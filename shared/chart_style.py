"""House chart style ("V2 / Floated") for the matplotlib charts in this repo.

Import it instead of re-inlining rcParams/colours in the notebook or scripts.

    from shared import chart_style as cs

    cs.use()                                  # rcParams theme (fonts, palette, warm ground)
    fig, ax = cs.figure()                     # warm-white figure + axes
    ax.plot(d.index, d["y"], color=cs.PRIMARY)
    cs.floated_yaxis(ax, [0, 100, 200])       # floated value labels + sparse grid + halo
    cs.title(fig, "An insight headline in sentence case",
                  "Units; description of the indicator")
    cs.source(fig, "Source: FRED. Joshua Bailey")
    fig.savefig("chart.png")                  # warm ground preserved

Design summary
--------------
Charter serif headline over Helvetica Neue labels, on a warm-white ground.
Recessive frame: no top/right spines; the "Floated" finish puts value labels above
sparse, very light horizontal gridlines (each with a faint warm-white halo) and drops
the y-spine. Insight titles + a subtitle deck + a hairline rule; a source rule + left
credit at the foot. Prefer direct end-of-line labels and highlight-and-mute over legends.
The palette is validated colour-blind-safe on the warm ground.
"""
from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.transforms import Bbox

# --- Typography --------------------------------------------------------------
SERIF = "Charter"          # headline (falls back to Georgia/Times if absent)
SANS = "Helvetica Neue"    # labels, body, everything else

# --- Neutrals & ground -------------------------------------------------------
GROUND = "#FDFCFA"   # warm white — figure, axes and saved background
INK = "#241f1a"      # near-black warm ink (headlines, dark marks)
SUBTLE = "#6b6259"   # subtitle deck, tick labels, source
FAINT = "#95897b"    # very quiet labels
GRID = "#ece7df"     # context gridlines (small multiples)
GRIDL = "#f0eae0"    # the sparse floated gridlines (very light)
RULE = "#d2cabd"     # hairline rules (under title, above source)
AXIS = "#9b9184"     # soft warm grey for scatter axis lines
BASE = "#443d33"     # axis spines + zero/baseline reference lines (warm dark grey, not neutral)

# --- Palette (validated colour-blind-safe on the warm ground) ----------------
NAVY = "#1F5FA6"
SIENNA = "#CC5B2E"
TEAL = "#1F9AA4"
OCHRE = "#E0A020"
GREEN = "#3C9147"
PLUM = "#9C4F86"
MUTE = "#C3B8A8"     # de-emphasised / context series
MUTE2 = "#A79D8E"    # slightly darker neutral (reference marks)
SUMMARY = "#57503f"  # summary / total / aggregate lines (recessive warm dark grey, not pure black)

# Semantic roles and the ordered categorical ramp (assign in this order; never cycle).
PRIMARY, ACCENT, SUPPORT = NAVY, SIENNA, TEAL
CATEGORICAL = [NAVY, SIENNA, TEAL, OCHRE, GREEN, PLUM]

# Faint warm-white halo placed behind floated labels so they read over lines/fills.
HALO = dict(boxstyle="round,pad=0.14", facecolor=GROUND, edgecolor="none", alpha=0.72)

__all__ = [
    "use", "figure", "title", "source", "floated_yaxis", "scatter_axes",
    "highlight_mute", "spread", "direct_label", "legend", "annotate", "statbox",
    "check_overlaps", "HALO",
    "SERIF", "SANS", "GROUND", "INK", "SUBTLE", "FAINT", "GRID", "GRIDL", "RULE",
    "AXIS", "BASE", "NAVY", "SIENNA", "TEAL", "OCHRE", "GREEN", "PLUM", "MUTE", "MUTE2", "SUMMARY",
    "PRIMARY", "ACCENT", "SUPPORT", "CATEGORICAL",
    # deprecated aliases
    "set_economist_style", "add_footnote", "PALETTE",
]


# --- Theme -------------------------------------------------------------------
def use() -> None:
    """Apply the house rcParams theme so even ad-hoc ``plt.plot`` looks on-brand.

    Sets fonts, the categorical colour cycle, the warm-white ground (figure, axes
    and saved output), a recessive frame (no top/right spines) and quiet ticks.
    """
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": [SANS, "Helvetica", "Arial", "DejaVu Sans"],
        "font.serif": [SERIF, "Georgia", "Times New Roman", "DejaVu Serif"],
        "font.size": 11.5,
        "text.color": INK,
        "figure.facecolor": GROUND,
        "savefig.facecolor": GROUND,
        "axes.facecolor": GROUND,
        "axes.edgecolor": BASE,
        "axes.linewidth": 0.9,
        "axes.grid": False,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.prop_cycle": plt.cycler(color=CATEGORICAL),
        "axes.titlesize": 15.5,
        "axes.titleweight": "bold",
        "axes.labelcolor": SUBTLE,
        "axes.labelsize": 11.5,
        "grid.color": GRID,
        "grid.linewidth": 0.9,
        "xtick.color": SUBTLE,
        "ytick.color": SUBTLE,
        "xtick.labelsize": 10.5,
        "ytick.labelsize": 10.5,
        "figure.dpi": 100,
        "savefig.dpi": 160,
        "savefig.bbox": None,   # furniture uses figure-fraction coords; don't crop
    })


# --- Figure & furniture ------------------------------------------------------
def figure(w: float = 7.8, h: float = 5.4, rect=(0.075, 0.16, 0.80, 0.555)):
    """A warm-white figure with a single axes placed for a title block + source rule.

    ``rect`` leaves headroom at the top (title/deck/rule) and a foot for the source
    rule. Widen ``rect`` (e.g. 0.895) when there are no right-hand direct labels.
    """
    fig = plt.figure(figsize=(w, h), facecolor=GROUND)
    ax = fig.add_axes(rect)
    ax.set_facecolor(GROUND)
    return fig, ax


def title(fig, headline: str, deck: str, x: float = 0.075, x2: float = 0.965,
          y: float = 0.945, size: float = 15.5, deck_size: float = 11.5,
          rule_y: float = 0.85) -> None:
    """Insight headline (Charter, bold, sentence case) + grey subtitle deck + hairline rule.

    The deck carries the units / indicator description; keep units out of the headline.
    """
    fig.text(x, y, headline, ha="left", va="top", fontsize=size, fontweight="bold",
             family=SERIF, color=INK)
    fig.text(x, y - 0.058, deck, ha="left", va="top", fontsize=deck_size,
             family=SANS, color=SUBTLE)
    fig.add_artist(Line2D([x, x2], [rule_y, rule_y], transform=fig.transFigure,
                          color=RULE, lw=1.0))


def source(fig, text: str, x: float = 0.075, x2: float = 0.965, y: float = 0.03) -> None:
    """Foot-of-chart source rule + left-aligned credit (with a data note if present).

    Headline source only (no series codes), ending in "Joshua Bailey", e.g.
    "Source: FRED. Joshua Bailey" or "Sources: FRED; BLS. Joshua Bailey".
    Each line of ``text`` is re-wrapped to the figure width, so a long note can never
    run past the edge (which, under ``savefig bbox='tight'``, would blow out the image).
    The rule is placed above the *wrapped* block, so a multi-line note (a short method
    note above the credit) sits under its rule instead of running through it.
    """
    import textwrap
    size = 8
    wrap_w = max(48, int((x2 - x) * fig.get_size_inches()[0] * 13))
    text = "\n".join(textwrap.fill(seg, wrap_w) if seg.strip() else seg
                     for seg in text.split("\n"))
    line_h = size * 1.2 / 72 / fig.get_size_inches()[1]   # one line, in figure fractions
    rule_y = y + text.count("\n") * line_h + 0.028
    fig.add_artist(Line2D([x, x2], [rule_y, rule_y], transform=fig.transFigure,
                          color=RULE, lw=0.8))
    fig.text(x, y, text, ha="left", va="bottom", fontsize=size, color=SUBTLE, family=SANS)


def floated_yaxis(ax, ticks, xleft: float = 0.008, fmt=None,
                  baseline: bool = False, halo: bool = True) -> None:
    """The V2 "Floated" y-axis: value labels above sparse, very light gridlines, no spine.

    Pass a SPARSE tick list (3-5 values). Each label gets a warm-white halo so it reads
    over a line or fill. Set ``baseline=True`` for a thin bottom rule on time series that
    have no zero line of their own.
    """
    fmt = fmt or (lambda v: f"{v:g}")
    ax.tick_params(length=0)
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.set_yticks(ticks)
    ax.set_yticklabels([])
    for v in ticks:
        ax.axhline(v, color=GRIDL, lw=0.9, zorder=0)
        ax.text(xleft, v, fmt(v), transform=ax.get_yaxis_transform(), va="bottom",
                ha="left", fontsize=9.8, color=SUBTLE, family=SANS, zorder=5,
                bbox=HALO if halo else None)
    if baseline:
        ax.spines["bottom"].set_visible(True)
        ax.spines["bottom"].set_color(BASE)
        ax.spines["bottom"].set_linewidth(0.9)


def scatter_axes(ax, grid: bool = True) -> None:
    """L-shaped soft-grey axis lines for scatters — the ONE type that keeps axis lines.

    Adds visible left+bottom spines in soft warm grey and a light grid to locate points.
    Set axis titles separately (``ax.set_xlabel``/``set_ylabel``); on a scatter x and y
    are not self-evident, so both usually earn a label.
    """
    ax.tick_params(length=0)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_visible(True)
        ax.spines[s].set_color(AXIS)
        ax.spines[s].set_linewidth(0.9)
    if grid:
        ax.grid(True, color=GRIDL, lw=0.9, zorder=0)


# --- Idiom helpers -----------------------------------------------------------
def highlight_mute(highlight):
    """Return ``color_of(name)`` mapping highlighted series to colours, others to MUTE.

    ``highlight`` is either a list of names (assigned CATEGORICAL in order) or a dict
    ``{name: colour}``. Use for dense multi-series charts: colour the 2-3 that matter,
    grey the rest.
    """
    if isinstance(highlight, dict):
        cmap = dict(highlight)
    else:
        cmap = {name: CATEGORICAL[i % len(CATEGORICAL)] for i, name in enumerate(highlight)}
    return lambda name: cmap.get(name, MUTE)


def spread(values, gap):
    """Nudge label y-positions so none are closer than ``gap`` (simple one pass, top-down)."""
    values = np.asarray(values, dtype=float)
    order = np.argsort(values)[::-1]
    adj = values.copy()
    for i in range(1, len(order)):
        hi, lo = order[i - 1], order[i]
        if adj[hi] - adj[lo] < gap:
            adj[lo] = adj[hi] - gap
    return adj


def direct_label(ax, x, y, text, color, *, pad: int = 8, bold: bool = True,
                 size: float = 9.0, **kw):
    """Place a direct label to the right of a point (e.g. the end of a line).

    Direct labels are the *preferred* way to identify series — reach for a legend only
    when lines are too clustered to label individually.
    """
    ax.annotate(text, xy=(x, y), xytext=(pad, 0), textcoords="offset points",
                va="center", ha="left", fontsize=size, color=color,
                fontweight="bold" if bold else "normal", family=SANS,
                annotation_clip=False, **kw)


def _cap_first(s: str) -> str:
    return s[:1].upper() + s[1:] if s else s


def _fit_ncol(labels, fig_w_in):
    """Largest column count whose widest row still fits the figure width (in chars)."""
    widths = [len(l) + 7 for l in labels]            # ~label + handle + gap
    target = max(30, fig_w_in * 10.5)
    for ncol in range(len(labels), 0, -1):
        rows = [sum(widths[r:r + ncol]) for r in range(0, len(widths), ncol)]
        if max(rows) <= target or ncol == 1:
            return ncol
    return 1


def legend(ax, *, above: bool = True, ncol=None, y: float = 1.02, loc: str = "best",
           size: float = 8.5, **kw):
    """House legend. Default: a horizontal legend ABOVE the plot that WRAPS to fit width.

    Never sit a legend in the upper-left of a floated-axis chart — it collides with the
    floated value labels. ``above=True`` (default) picks the column count from the label
    widths so the row never runs past the figure edge, records the row count on the axes
    (so the title auto-reserves headroom), then places it just above the axes.
    ``above=False`` places a normal in-plot legend at ``loc`` — pass an explicitly clear
    corner. First word of each entry is capitalised.
    """
    import math
    handles, labels = ax.get_legend_handles_labels()
    if not handles:
        return None
    labels = [_cap_first(l) for l in labels]
    opts = dict(frameon=False, fontsize=size, handlelength=1.5, handletextpad=0.6,
                columnspacing=1.5, borderaxespad=0.0)
    opts.update(kw)
    if above:
        if ncol is None:
            ncol = _fit_ncol(labels, ax.figure.get_size_inches()[0])
        rows = math.ceil(len(labels) / ncol)
        ax._house_legend_rows = rows                       # noqa: SLF001 (title reads this)
        ax.figure.subplots_adjust(top=0.82 - (rows - 1) * 0.045)
        return ax.legend(handles, labels, loc="lower left", bbox_to_anchor=(0, y),
                         ncol=ncol, **opts)
    return ax.legend(handles, labels, loc=loc, ncol=ncol or 1, **opts)


_STAT_CORNERS = {
    "lower left": (0.02, 0.03, "left", "bottom"),
    "lower right": (0.985, 0.03, "right", "bottom"),
    "upper left": (0.02, 0.975, "left", "top"),
    "upper right": (0.985, 0.975, "right", "top"),
}


def statbox(ax, lines, *, loc: str = "lower left", size: float = 7.6,
            tint: str = "#F3EDE3"):
    """Standard tidy panel for a few key stats / diagnostics inside a chart.

    A borderless soft warm-tint card (no grey-outlined "bubble"), sans text in the ink
    token, placed in a corner. ``lines`` is a list of short strings (or one string).
    """
    x, y, ha, va = _STAT_CORNERS.get(loc, _STAT_CORNERS["lower left"])
    text = lines if isinstance(lines, str) else "\n".join(lines)
    # ``ha`` hangs the card off its corner; the lines INSIDE it always read left-aligned
    # (a right-aligned, ragged-left block is unreadable for anything but a column of digits).
    return ax.text(x, y, text, transform=ax.transAxes, ha=ha, va=va, ma="left",
                   fontsize=size, family=SANS, color=INK, linespacing=1.4, zorder=8,
                   bbox=dict(boxstyle="round,pad=0.5", facecolor=tint, edgecolor="none",
                             alpha=0.94))


def box_anchor(ax, box, fx: float = 0.5, pad: float = 0.015):
    """Where a callout arrow should leave a ``statbox``: a point on its bottom edge.

    Returns axes-fraction coords ``fx`` of the way across the rendered card (0=left,
    1=right), ``pad`` below it. Measure the card rather than guessing at coordinates —
    an arrow whose tail floats in mid-plot instead of touching its label is worse than
    no arrow at all.
    """
    fig = ax.figure
    fig.canvas.draw()                              # the card has no extent until drawn
    renderer = fig.canvas.get_renderer()
    patch = box.get_bbox_patch()
    bb = (patch or box).get_window_extent(renderer)
    inv = ax.transAxes.inverted()
    (x0, y0) = inv.transform((bb.x0, bb.y0))
    (x1, _y1) = inv.transform((bb.x1, bb.y1))
    return (x0 + fx * (x1 - x0), y0 - pad)


def annotate(ax, text, xy, xytext, *, color=None, rad: float = 0.2, size: float = 8.5,
             ha: str = "left", va: str = "center", **kw):
    """House callout: a curved, tidy arrow whose head stops short of its target.

    Text is Helvetica Neue in the ink token (matching the legend), first word capitalised.
    ``xytext`` is an (dx, dy) offset in points from ``xy``; ``rad`` sets the arc curvature
    (sign flips the bend). The arrowhead is shrunk back from the target so it never runs
    right up to the mark it points at.
    """
    return ax.annotate(_cap_first(text), xy=xy, xytext=xytext,
                       textcoords="offset points", fontsize=size, color=color or INK,
                       family=SANS, ha=ha, va=va,
                       arrowprops=dict(arrowstyle="-|>", color=MUTE2, lw=0.9,
                                       shrinkA=3, shrinkB=9, mutation_scale=11,
                                       connectionstyle=f"arc3,rad={rad}"),
                       **kw)


def check_overlaps(fig, name: str = "", *, min_px: float = 4.0):
    """Print a warning for any chart furniture that collides — run it before every save.

    Checks the axis labels, the legend, the figure-level texts (headline/deck/source)
    and the hairline rules against each other in rendered pixels, and flags an axis label
    that spills above its own plot (into the title/rule). Not exhaustive — it ignores
    in-plot annotations and tick labels, which legitimately sit near data — but it catches
    the recurring furniture collisions mechanically instead of by eye. Never ship a chart
    that prints an ``[OVERLAP]``. Returns the list of warnings.
    """
    try:
        fig.canvas.draw()
        r = fig.canvas.get_renderer()
    except Exception:  # pragma: no cover - headless safety
        return []

    def bb(artist):
        try:
            b = artist.get_window_extent(r)
            return b if (b.width > 1 and b.height > 1) else None
        except Exception:
            return None

    warns, labelled = set(), []
    for ax in fig.axes:
        try:
            axbb = ax.get_window_extent(r)
        except Exception:
            axbb = None
        for tag, art in (("y-label", ax.yaxis.label), ("x-label", ax.xaxis.label)):
            if not art.get_text().strip() or not (b := bb(art)):
                continue
            labelled.append((tag, b))
            if axbb is not None and b.y1 > axbb.y1 + min_px:
                warns.add(f"{tag} extends above the plot (into the title/rule)")
        leg = ax.get_legend()
        if leg and (b := bb(leg)):
            labelled.append(("legend", b))
    for t in fig.texts:
        if t.get_text().strip() and (b := bb(t)):
            labelled.append((f"text '{t.get_text()[:22]}…'", b))

    rules = []
    for art in fig.artists:  # hairline rules (wide, ~0 tall)
        if isinstance(art, Line2D):
            try:
                b = art.get_window_extent(r)
            except Exception:
                continue
            if b.width > 5:
                rules.append(Bbox([[b.x0, b.y0 - 3], [b.x1, b.y1 + 3]]))

    def clash(a, c, min_h=min_px):
        i = Bbox.intersection(a, c)
        return i is not None and i.width > min_px and i.height > min_h

    for i, (na, ba) in enumerate(labelled):
        for rb in rules:
            if clash(ba, rb, min_h=0.5):
                warns.add(f"{na} crosses a rule")
        for nb, bc in labelled[i + 1:]:
            if clash(ba, bc):
                warns.add(f"{na} overlaps {nb}")
    for w in sorted(warns):
        print(f"  [OVERLAP] {name}: {w}")
    return list(warns)


# --- Deprecated aliases (old Economist-serif API; now render in the new style) ----
_use, _source = use, source


def set_economist_style(*_a, **_k) -> None:  # pragma: no cover - back-compat shim
    """Deprecated. Kept so old notebooks import cleanly; applies the current house style."""
    _use()


def add_footnote(fig, note=None, source="Source: Joshua Bailey", wrap=None) -> None:  # noqa: A002
    """Deprecated. Kept for old notebooks; renders as the current source rule + credit."""
    text = f"Note. {note}  {source}" if note else source
    _source(fig, text)


# Old constant names kept as aliases (mapped to the new palette) so old notebooks
# import cleanly and re-render in the current single design language.
PALETTE = CATEGORICAL
ECON_RED = ACCENT
ECON_NAVY = PRIMARY
LIGHT_BLUE = SUPPORT
GREY = MUTE2
SAND = OCHRE
DARK_RED = SIENNA
# GREEN already defined above (new green); old code using it gets the current green.
