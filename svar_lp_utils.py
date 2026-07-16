"""Estimation helpers for the energy -> supercore passthrough model.

Primary tool: an observed-shock state-dependent local-projection estimator in the
Ramey-Zubairy (2018) tradition, using Kanzig's published oil-supply-news shock as
an observed exogenous regressor (no first stage -> avoids the LP-IV
state-dependence pitfall). HAC inference is lag-augmented and valid for LPs
(Montiel-Olea & Plagborg-Moller 2021); a wild bootstrap is provided as a cross-check.

"""

from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm


# ----------------------------------------------------------------------------
# Transition / regime weighting
# ----------------------------------------------------------------------------
def logistic_transition(z: pd.Series, gamma: float) -> pd.Series:
    """Logistic transition weight F(z) in (0,1); standardised z, F rises with z.

    gamma controls smoothness; large gamma -> near hard threshold at z = mean.
    """
    zc = (z - z.mean()) / z.std()
    return pd.Series(1.0 / (1.0 + np.exp(-gamma * zc)), index=z.index, name="F")


def hard_threshold(z: pd.Series, thresh: float) -> pd.Series:
    """Indicator F(z)=1{z >= thresh} (regime weight for the 'high' state)."""
    return (z >= thresh).astype(float).rename("F")


# ----------------------------------------------------------------------------
# Local projections
# ----------------------------------------------------------------------------
def _build_controls(df: pd.DataFrame, y: str, shock: str, state_raw: str,
                    n_lags: int, covid: bool) -> pd.DataFrame:
    """Lag-augmented control block: lags of shock, lags of d(y), state level, trend, COVID."""
    X = pd.DataFrame(index=df.index)
    for L in range(1, n_lags + 1):
        X[f"shock_l{L}"] = df[shock].shift(L)        # lag augmentation (MOPM 2021)
        X[f"dy_l{L}"] = df[y].diff().shift(L)        # lagged dependent growth
    if state_raw is not None:
        X["state_l1"] = df[state_raw].shift(1)
    X["trend"] = np.arange(len(df), dtype=float)
    if covid:
        X["covid"] = ((df.index >= "2020-03-01") & (df.index <= "2020-12-01")).astype(float)
    return X


def linear_lp(df: pd.DataFrame, y: str, shock: str, horizons, *,
              state_raw: str | None = None, n_lags: int = 12, covid: bool = True) -> pd.DataFrame:
    """Linear (no-state) LP. y is a log-level x100 series; returns cumulative level IRF.

    LHS at horizon h: y_{t+h} - y_{t-1}. Coefficient on shock_t = IRF(h).
    HAC (Newey-West, bandwidth h+1) inference.
    """
    ctrl = _build_controls(df, y, shock, state_raw, n_lags, covid)
    base = pd.concat([pd.Series(1.0, index=df.index, name="const"),
                      df[shock].rename("shock"), ctrl], axis=1)
    out = []
    for h in horizons:
        lhs = (df[y].shift(-h) - df[y].shift(1)).rename("lhs")
        d = pd.concat([lhs, base], axis=1).dropna()
        if len(d) < base.shape[1] + 10:
            out.append({"h": h, "n": len(d)})
            continue
        res = sm.OLS(d["lhs"], d.drop(columns="lhs")).fit(
            cov_type="HAC", cov_kwds={"maxlags": h + 1})
        out.append({"h": h, "beta": res.params["shock"], "se": res.bse["shock"],
                    "n": int(res.nobs)})
    return pd.DataFrame(out)


def state_dependent_lp(df: pd.DataFrame, y: str, shock: str, F: pd.Series, horizons, *,
                       state_raw: str | None = None, n_lags: int = 12,
                       covid: bool = True) -> pd.DataFrame:
    """Ramey-Zubairy observed-shock state-dependent LP (all regressors regime-interacted).

    F is the transition weight in [0,1] for the 'high'/hot regime (use F(z_{t-1})).
    Returns, per horizon: betaH, betaL (cumulative level IRFs by regime), HAC SEs,
    the difference and the Wald p-value for H0: betaH = betaL, and n.
    """
    ctrl = _build_controls(df, y, shock, state_raw, n_lags, covid)
    regs = pd.concat([pd.Series(1.0, index=df.index, name="const"),
                      df[shock].rename("shock"), ctrl], axis=1)
    Fser = F.reindex(df.index)
    out = []
    for h in horizons:
        lhs = (df[y].shift(-h) - df[y].shift(1)).rename("lhs")
        XH = regs.mul(Fser, axis=0).add_suffix("_H")
        XL = regs.mul(1.0 - Fser, axis=0).add_suffix("_L")
        d = pd.concat([lhs, XH, XL], axis=1).dropna()
        if len(d) < (XH.shape[1] + XL.shape[1]) + 10:
            out.append({"h": h, "n": len(d)})
            continue
        res = sm.OLS(d["lhs"], d.drop(columns="lhs")).fit(
            cov_type="HAC", cov_kwds={"maxlags": h + 1})
        tt = res.t_test("shock_H - shock_L = 0")
        out.append({"h": h, "betaH": res.params["shock_H"], "seH": res.bse["shock_H"],
                    "betaL": res.params["shock_L"], "seL": res.bse["shock_L"],
                    "diff": float(res.params["shock_H"] - res.params["shock_L"]),
                    "wald_p": float(np.ravel(tt.pvalue)[0]), "n": int(res.nobs)})
    return pd.DataFrame(out)


def state_sign_lp(df: pd.DataFrame, y: str, shock: str, F: pd.Series, horizons, *,
                  state_raw: str | None = None, n_lags: int = 12, covid: bool = True) -> pd.DataFrame:
    """State-dependent LP isolating the PRICE-RAISING (negative-supply) shock.

    The impact terms are (regime x price-raising) and (regime x price-falling); the
    price-falling part is carried as a separate regime-interacted control, so betaH/betaL
    read as the hot/slack cumulative response to a price-RAISING (positive Kanzig) oil
    shock. Drop-in replacement for state_dependent_lp (same columns: betaH, seH, betaL,
    seL, diff, wald_p, n). Lag-augmented HAC inference (Newey-West, bandwidth h+1).
    """
    s = df[shock]
    spos, sneg = s.clip(lower=0), s.clip(upper=0)
    ctrl = _build_controls(df, y, shock, state_raw, n_lags, covid)
    base = pd.concat([pd.Series(1.0, index=df.index, name="const"),
                      spos.rename("sp"), sneg.rename("sn"), ctrl], axis=1)
    Fser = F.reindex(df.index)
    out = []
    for h in horizons:
        lhs = (df[y].shift(-h) - df[y].shift(1)).rename("lhs")
        XH = base.mul(Fser, axis=0).add_suffix("_H")
        XL = base.mul(1.0 - Fser, axis=0).add_suffix("_L")
        d = pd.concat([lhs, XH, XL], axis=1).dropna()
        if len(d) < (XH.shape[1] + XL.shape[1]) + 10:
            out.append({"h": h, "n": len(d)})
            continue
        res = sm.OLS(d["lhs"], d.drop(columns="lhs")).fit(
            cov_type="HAC", cov_kwds={"maxlags": h + 1})
        tt = res.t_test("sp_H - sp_L = 0")
        out.append({"h": h, "betaH": res.params["sp_H"], "seH": res.bse["sp_H"],
                    "betaL": res.params["sp_L"], "seL": res.bse["sp_L"],
                    "diff": float(res.params["sp_H"] - res.params["sp_L"]),
                    "wald_p": float(np.ravel(tt.pvalue)[0]), "n": int(res.nobs)})
    return pd.DataFrame(out)


def linear_pos_lp(df: pd.DataFrame, y: str, shock: str, horizons, *,
                  state_raw: str | None = None, n_lags: int = 12, covid: bool = True) -> pd.DataFrame:
    """Linear (no-state) LP on the PRICE-RAISING part of the shock; price-falling carried
    as a control. Drop-in for linear_lp's no-state IRF (returns h, beta, se, n)."""
    s = df[shock]
    spos, sneg = s.clip(lower=0), s.clip(upper=0)
    ctrl = _build_controls(df, y, shock, state_raw, n_lags, covid)
    base = pd.concat([pd.Series(1.0, index=df.index, name="const"),
                      spos.rename("sp"), sneg.rename("sn"), ctrl], axis=1)
    out = []
    for h in horizons:
        lhs = (df[y].shift(-h) - df[y].shift(1)).rename("lhs")
        d = pd.concat([lhs, base], axis=1).dropna()
        if len(d) < base.shape[1] + 10:
            out.append({"h": h, "n": len(d)})
            continue
        res = sm.OLS(d["lhs"], d.drop(columns="lhs")).fit(
            cov_type="HAC", cov_kwds={"maxlags": h + 1})
        out.append({"h": h, "beta": res.params["sp"], "se": res.bse["sp"], "n": int(res.nobs)})
    return pd.DataFrame(out)


def linearity_ftest(df: pd.DataFrame, y: str, shock: str, F: pd.Series, h: int, *,
                    state_raw: str | None = None, n_lags: int = 12,
                    covid: bool = True) -> dict:
    """Joint F-test that the regime split adds nothing at horizon h (all _H vs _L equal).

    Compares the regime-interacted model to the restriction that every high-regime
    coefficient equals its low-regime counterpart (i.e. the linear LP). Non-robust
    F (homoskedastic) as a specification screen; HAC Wald on the shock term is the
    headline test in state_dependent_lp.
    """
    ctrl = _build_controls(df, y, shock, state_raw, n_lags, covid)
    regs = pd.concat([pd.Series(1.0, index=df.index, name="const"),
                      df[shock].rename("shock"), ctrl], axis=1)
    Fser = F.reindex(df.index)
    lhs = (df[y].shift(-h) - df[y].shift(1)).rename("lhs")
    XH = regs.mul(Fser, axis=0).add_suffix("_H")
    XL = regs.mul(1.0 - Fser, axis=0).add_suffix("_L")
    d = pd.concat([lhs, XH, XL], axis=1).dropna()
    res = sm.OLS(d["lhs"], d.drop(columns="lhs")).fit()
    names = [c for c in regs.columns]
    restr = [f"{n}_H - {n}_L = 0" for n in names]
    ft = res.f_test(restr)
    return {"h": h, "F": float(np.ravel(ft.fvalue)[0]), "p": float(np.ravel(ft.pvalue)[0]),
            "df_num": len(names), "n": int(res.nobs)}


def wild_bootstrap_sdlp(df: pd.DataFrame, y: str, shock: str, F: pd.Series, horizons, *,
                        state_raw: str | None = None, n_lags: int = 12, covid: bool = True,
                        n_boot: int = 500, seed: int = 42) -> dict:
    """Wild (Rademacher) bootstrap bands for state-dependent LP betaH/betaL per horizon.

    Residual-resampling wild bootstrap at each horizon, deterministic (seed=42), used only
    as a cross-check on the HAC bands. Note it draws i.i.d. multipliers, so it ignores the
    MA serial correlation that overlapping LP horizons induce in the residuals and tends to
    understate uncertainty; HAC (Newey-West, lag-augmented) is the headline inference.
    Returns dict of arrays keyed h -> {betaH:(lo,hi), betaL:(lo,hi)} at 68/90%.
    """
    rng = np.random.default_rng(seed)
    ctrl = _build_controls(df, y, shock, state_raw, n_lags, covid)
    regs = pd.concat([pd.Series(1.0, index=df.index, name="const"),
                      df[shock].rename("shock"), ctrl], axis=1)
    Fser = F.reindex(df.index)
    bands = {}
    for h in horizons:
        lhs = (df[y].shift(-h) - df[y].shift(1)).rename("lhs")
        XH = regs.mul(Fser, axis=0).add_suffix("_H")
        XL = regs.mul(1.0 - Fser, axis=0).add_suffix("_L")
        d = pd.concat([lhs, XH, XL], axis=1).dropna()
        if len(d) < (XH.shape[1] + XL.shape[1]) + 10:
            continue
        X = d.drop(columns="lhs").to_numpy()
        yv = d["lhs"].to_numpy()
        XtXinv = np.linalg.pinv(X.T @ X)
        beta = XtXinv @ (X.T @ yv)
        resid = yv - X @ beta
        cols = list(d.drop(columns="lhs").columns)
        iH, iL = cols.index("shock_H"), cols.index("shock_L")
        bH = np.empty(n_boot); bL = np.empty(n_boot)
        for b in range(n_boot):
            e = resid * rng.choice([-1.0, 1.0], size=len(resid))
            yb = X @ beta + e
            bb = XtXinv @ (X.T @ yb)
            bH[b] = bb[iH]; bL[b] = bb[iL]
        bands[h] = {
            "betaH": (np.percentile(bH, [5, 16, 84, 95])),
            "betaL": (np.percentile(bL, [5, 16, 84, 95])),
        }
    return bands


def continuous_interaction_lp(df: pd.DataFrame, y: str, shock: str, state: str, horizons, *,
                              quad: bool = True, n_lags: int = 12,
                              covid: bool = True) -> pd.DataFrame:
    """Continuous-interaction LP (Najjar-Shapiro style), optionally quadratic in the state.

    y_{t+h} - y_{t-1} = b0*s_t + b1*(s_t*z_{t-1}) [+ b2*(s_t*z^2_{t-1})] + controls + e

    z is the state column standardised over its sample and LAGGED one month inside this
    function (predetermined). State main effects (z_{t-1}, z^2_{t-1}) are included via the
    control block. Returns per horizon: b0/b1/(b2) with HAC SEs, p-values for b1=0, b2=0
    and the joint b1=b2=0 Wald (any state dependence), plus n.
    """
    zs = df[state].dropna()
    z = ((zs - zs.mean()) / zs.std()).reindex(df.index).shift(1)   # standardised, lagged
    ctrl = _build_controls(df, y, shock, state, n_lags, covid)     # has state_l1 (raw level)
    ctrl["state2_l1"] = z ** 2                                     # quadratic main effect
    terms = {"const": pd.Series(1.0, index=df.index),
             "shock": df[shock], "shock_x_z": df[shock] * z}
    if quad:
        terms["shock_x_z2"] = df[shock] * z ** 2
    base = pd.concat([pd.DataFrame(terms), ctrl], axis=1)
    out = []
    for h in horizons:
        lhs = (df[y].shift(-h) - df[y].shift(1)).rename("lhs")
        d = pd.concat([lhs, base], axis=1).dropna()
        if len(d) < base.shape[1] + 10:
            out.append({"h": h, "n": len(d)})
            continue
        res = sm.OLS(d["lhs"], d.drop(columns="lhs")).fit(
            cov_type="HAC", cov_kwds={"maxlags": h + 1})
        row = {"h": h, "b0": res.params["shock"], "se0": res.bse["shock"],
               "b1": res.params["shock_x_z"], "se1": res.bse["shock_x_z"],
               "p_b1": res.pvalues["shock_x_z"], "n": int(res.nobs)}
        if quad:
            row.update({"b2": res.params["shock_x_z2"], "se2": res.bse["shock_x_z2"],
                        "p_b2": res.pvalues["shock_x_z2"]})
            jt = res.wald_test("(shock_x_z = 0), (shock_x_z2 = 0)", scalar=True)
            row["p_joint"] = float(jt.pvalue)
        else:
            row["p_joint"] = row["p_b1"]
        # implied beta(z) curve with delta-method HAC bands
        zgrid = np.arange(-1.5, 2.01, 0.25)
        names = ["shock", "shock_x_z"] + (["shock_x_z2"] if quad else [])
        V = res.cov_params().loc[names, names].to_numpy()
        bvec = res.params[names].to_numpy()
        for zg in zgrid:
            g = np.array([1.0, zg] + ([zg ** 2] if quad else []))
            row[f"beta_at_{zg:+.2f}"] = float(g @ bvec)
            row[f"se_at_{zg:+.2f}"] = float(np.sqrt(g @ V @ g))
        out.append(row)
    return pd.DataFrame(out)


def asymmetry_lp(df: pd.DataFrame, y: str, shock: str, horizons, *,
                 state: str | None = None, size: bool = True, n_lags: int = 12,
                 covid: bool = True) -> pd.DataFrame:
    """Sign-split and size-dependent LP, with an optional tightness horse-race.

    Regressors: s+ = max(s,0), s- = min(s,0); if size, s*|s| (CLM size-dependence);
    if state given, also s*z_{t-1} (standardised) so size and state compete directly.
    Returns per horizon: coefficients/SEs, Wald p for s+ = s- (sign symmetry), p-values
    on the size and state terms, and n.
    """
    sp = df[shock].clip(lower=0).rename("shock_pos")
    sn = df[shock].clip(upper=0).rename("shock_neg")
    terms = {"const": pd.Series(1.0, index=df.index), "shock_pos": sp, "shock_neg": sn}
    if size:
        terms["shock_x_abs"] = df[shock] * df[shock].abs()
    if state is not None:
        zs = df[state].dropna()
        z = ((zs - zs.mean()) / zs.std()).reindex(df.index).shift(1)
        terms["shock_x_z"] = df[shock] * z
    ctrl = _build_controls(df, y, shock, state, n_lags, covid)
    base = pd.concat([pd.DataFrame(terms), ctrl], axis=1)
    out = []
    for h in horizons:
        lhs = (df[y].shift(-h) - df[y].shift(1)).rename("lhs")
        d = pd.concat([lhs, base], axis=1).dropna()
        if len(d) < base.shape[1] + 10:
            out.append({"h": h, "n": len(d)})
            continue
        res = sm.OLS(d["lhs"], d.drop(columns="lhs")).fit(
            cov_type="HAC", cov_kwds={"maxlags": h + 1})
        tt = res.t_test("shock_pos - shock_neg = 0")
        row = {"h": h, "b_pos": res.params["shock_pos"], "se_pos": res.bse["shock_pos"],
               "b_neg": res.params["shock_neg"], "se_neg": res.bse["shock_neg"],
               "p_sign_sym": float(np.ravel(tt.pvalue)[0]), "n": int(res.nobs)}
        if size:
            row.update({"b_size": res.params["shock_x_abs"],
                        "p_size": res.pvalues["shock_x_abs"]})
        if state is not None:
            row.update({"b_state": res.params["shock_x_z"],
                        "p_state": res.pvalues["shock_x_z"]})
        out.append(row)
    return pd.DataFrame(out)
