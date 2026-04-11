# Plot Annotation System — Architecture & Implementation Plan

> **Status**: Phase 2 Complete — Pilot running  
> **Date**: April 2026  
> **Scope**: Reusable annotation system for all plots in Rowing Catch

---

## 1. Executive Summary

**Recommended stack: pure matplotlib — no new interactive library.**

The app already renders everything via `setup_premium_plot()` (matplotlib), and a PDF-printable output is a hard requirement. Adding Plotly or Bokeh creates a parallel rendering stack with no clean home in the 4-layer architecture — two figure objects, two export paths, two styling systems. Matplotlib alone is entirely capable of delivering the required visual styles:

- **Segment backdrop**: Wide semi-transparent backing line behind the data trace (vector-safe, PDF-perfect)
- **Shaded band**: `ax.fill_between()` (used in FastF1, Strava dashboards)
- **Callout boxes**: `ax.annotate()` with `arrowprops` (standard matplotlib)
- **Reference labels**: `[P1]` text on plot + `matplotlib.table` legend beneath

The annotation system will be a new **Layer 2 module** (`plot_transformer/annotations.py`) of typed dataclasses produced by transformers and consumed by a shared renderer utility in `plot/utils.py`. Streamlit toggles live in the page layer and pass an `active_annotations: set[str]` filter down to renderers. PDF export works because all annotations are baked into the matplotlib `Figure` object.

---

## 2. Library Comparison

| Library | Interactive | PDF export | Glow/highlight | Streamlit | Maintenance | Verdict |
|---|---|---|---|---|---|---|
| **matplotlib (pure)** | ❌ static | ✅ native vector | ✅ segment backdrop | ✅ `st.pyplot()` | Active, stable | **✅ Use — primary** |
| **adjustText** | ❌ | ✅ (matplotlib) | N/A | ✅ transparent | Active | **✅ Use for dense labels** |
| **highlight_text** | ❌ | ✅ limited | ✅ rich spans | ✅ | Niche, active | ⚠️ Complex API, skip for now |
| **mplcursors** | ✅ hover | ❌ lost in PDF | ❌ | ✅ | Active | ❌ Skip — screen-only, no PDF |
| **Plotly + kaleido** | ✅ full | ⚠️ font drift | ✅ | ✅ `st.plotly_chart` | Active | ❌ Skip — PDF fragile, parallel stack |
| **Bokeh** | ✅ full | ❌ no native PDF | ❌ | ✅ `st.bokeh_chart` | Active | ❌ Skip — worst PDF story |

### Why not Plotly?

Plotly's `kaleido` PDF export has known font substitution and layout drift on complex multi-axis figures. For a coach who needs a reliable printed report, this is unacceptable. Plotly also requires a completely separate figure-building API — every existing renderer would need a full rewrite.

### Why not mplcursors?

`mplcursors` adds hover tooltips to `st.pyplot()` figures, but tooltips are JavaScript-based and do not survive PDF export. They also do not work in Streamlit's static figure rendering mode without workarounds.

---

## 3. Visual Techniques Catalog

### 3.1 Shaded Band (`ax.fill_between`)

**How it works:**
```python
ax.fill_between(x, y - tolerance, y + tolerance,
                color=ANNOTATION_COLOR_1, alpha=0.15, zorder=1)
```

**PDF fidelity:** ✅ Perfect — native matplotlib vector path fill.  
**Modern look rating:** ⭐⭐⭐⭐  
**B&W printing:** Use `hatch='\\\\'` as fallback pattern.  
**Best rowing use cases:**
- Catch/finish angle tolerance bands (`±5°` target zone)
- Power curve standard deviation envelope across cycles
- Recovery timing consistency zones
- Any "acceptable range" visualization

---

### 3.2 Segment Backdrop (Wide semi-transparent backing line)

**How it works** — plot a single wide, semi-transparent line behind the original data trace:
```python
def draw_segment_backdrop(ax, x, y, color, n_layers=4, base_linewidth=2.5):
    ax.plot(x, y, color=color, linewidth=base_linewidth * 5,
            alpha=0.25, solid_capstyle='round', zorder=4)
```

`n_layers` is kept in the signature for API compatibility but is unused — the effect is a single layer.

**PDF fidelity:** ✅ Fully vector — single semi-transparent path preserved exactly.  
**Modern look rating:** ⭐⭐⭐⭐ — Clean and legible on white axes; does not overpower the main trace.  
**B&W printing:** ✅ Works naturally — the wide light band is visible in grayscale.  
**Annotation colour rule:** The backdrop uses the annotation's own palette colour (amber, emerald, fuchsia, …), which is always distinct from the main data line colour (`COLOR_MAIN = #636EFA`). The palette no longer contains indigo (`#6366F1`) which was too close to `COLOR_MAIN`.  
**Best rowing use cases:**
- Highlight a specific stroke phase (drive segment) on the main line
- Mark the best/worst cycle on a cycle overlay plot
- Emphasize the "catch entry" or "finish moment" point

---

### 3.3 Highlighted Segment (Color + weight override)

**How it works:**
```python
# Slice the original series at the annotation range and re-plot
ax.plot(x[start:end], y[start:end],
        color=ANNOTATION_COLOR, linewidth=4,
        solid_capstyle='round', zorder=6)
```

**PDF fidelity:** ✅ Perfect.  
**Modern look rating:** ⭐⭐⭐ — Clear and accessible.  
**B&W printing:** ✅ Works naturally — color difference becomes weight difference.  
**Best rowing use cases:**
- "Shooting the slide" window on seat velocity
- Arm pull phase on handle velocity
- Any discrete phase highlight

---

### 3.4 Callout Box with Leader Line (`ax.annotate`)

**How it works:**
```python
ax.annotate(
    '[P1]',
    xy=(x_data, y_data),          # point on the data
    xytext=(x_offset, y_offset),  # where the box sits
    fontsize=8, fontweight='bold',
    color=ANNOTATION_LABEL_COLOR,
    arrowprops=dict(
        arrowstyle='-|>',
        color=ANNOTATION_LABEL_COLOR,
        lw=0.8,
        connectionstyle='arc3,rad=0.15',
    ),
    bbox=dict(
        boxstyle='round,pad=0.3',
        facecolor='white',
        edgecolor=ANNOTATION_LABEL_COLOR,
        linewidth=0.8,
        alpha=0.9,
    ),
    zorder=10,
)
```

**PDF fidelity:** ✅ Perfect.  
**Modern look rating:** ⭐⭐⭐⭐ — Standard in biomechanics papers and sports dashboards.  
**Clutter rule:** ≤ 3 callouts per plot. Beyond that, use `[Px]` labels with legend table.  
**Best rowing use cases:**
- Peak force annotation `[P1]`
- Catch detection event `[C1]`
- Notable deviation point `[W1]` (warning)

---

### 3.5 Vertical/Horizontal Phase Markers (`ax.axvspan`)

**How it works:**
```python
ax.axvspan(start_idx, end_idx,
           color=COLOR_CATCH, alpha=0.07,
           label='Drive Phase', zorder=0)
```

**PDF fidelity:** ✅ Perfect.  
**Modern look rating:** ⭐⭐⭐ — Already used in the codebase. Familiar convention.  
**Best rowing use cases:**
- Drive/recovery phase region (already partially implemented)
- "Ideal catch window" zone
- Transition point markers

---

### 3.6 Reference Label System `[P1]` → Legend Table

**On the plot** — compact, minimal:
```python
ax.text(x, y, '[P1]',
        fontsize=7, fontweight='bold',
        color=ANNOTATION_LABEL_COLOR,
        bbox=dict(boxstyle='round,pad=0.2',
                  facecolor='white',
                  edgecolor=ANNOTATION_LABEL_COLOR,
                  linewidth=0.7, alpha=0.95),
        zorder=10, ha='center', va='bottom')
```

**Legend table beneath** (baked into matplotlib figure, PDF-safe):
```python
# Added as a second axes below the main plot via gridspec
col_labels = ['Ref', 'Metric', 'Value']
table_data = [['P1', 'Peak Drive Force', '320 W'],
              ['P2', 'Catch Angle', '−31°']]
table = ax_legend.table(cellText=table_data, colLabels=col_labels,
                        loc='center', cellLoc='left')
table.auto_set_font_size(False)
table.set_fontsize(8)
ax_legend.axis('off')
```

**PDF fidelity:** ✅ The legend table is a matplotlib `Table` artist — fully vector in PDF.  
**Modern look rating:** ⭐⭐⭐⭐ — Common in biomechanics papers, keeps the plot uncluttered.

---

### 3.7 Recommended Combination

> **Use segment backdrop/highlight on segment + `[Px]` label at key point + legend table beneath.**

This is the optimal balance: the plot stays uncluttered, the legend provides full context, and everything is PDF-printable. Shaded bands are used for zones (drive/recovery). Callout boxes are reserved for ≤ 3 critical single points.

---

## 4. Recommended Architecture

### 4.1 New Module: `rowing_catch/plot_transformer/annotations.py`

Lives in **Layer 2** — no UI dependency, pure Python dataclasses.

```python
@dataclass
class PointAnnotation:
    label: str            # Short ref: '[P1]'
    description: str      # Full text shown in legend Description column
    x: float
    y: float
    style: Literal['callout', 'label'] = 'label'
    color: str | None = None
    axis_id: str = 'main'
    coach_tip: str = ''   # Short coaching cue for legend Coach Tip column. '' → blank.


@dataclass
class SegmentAnnotation:
    label: str
    description: str
    x_start: float
    x_end: float
    x: list[float] = field(default_factory=list)
    y: list[float] = field(default_factory=list)
    style: Literal['highlight', 'glow', 'highlight+glow'] = 'glow'
    color: str | None = None
    axis_id: str = 'main'
    coach_tip: str = ''   # Short coaching cue. '' → blank.


@dataclass
class BandAnnotation:
    label: str
    description: str
    y_low: float
    y_high: float
    display_name: str | None = None
    x_start: float | None = None
    x_end: float | None = None
    color: str | None = None
    axis_id: str = 'main'
    coach_tip: str = ''   # Short coaching cue. '' → blank.


@dataclass
class PhaseAnnotation:
    label: str
    description: str
    x_start: float
    x_end: float
    color: str | None = None
    axis_id: str = 'main'
    coach_tip: str = ''   # Short coaching cue. '' → blank.
```

#### Coach Tip — first-class generic feature

`coach_tip` is a **standard field on every annotation type**, not a trunk-angle-specific feature. Rules:

- **All** annotation types carry it, defaulting to `''` (empty string = blank cell in the legend)
- The field is **always computed in the transformer** — never in the renderer
- Tips must be **short** (≤ 12 words): a callout sentence, not a paragraph
- Tips are **data-driven**: the transformer calculates them from the actual measured values vs. ideal zones, producing scenario-specific text (e.g. "Rock over more — 7.0° short" vs. "Catch lean within ideal range ✓")
- The Coach Tip column in the legend table is **only shown when at least one active annotation has a non-empty tip** — the column disappears automatically for unannotated plots
- Zone/reference bands (`BandAnnotation`, `PhaseAnnotation`) typically have **empty tips** — the visual zone communicates the target; no coaching sentence is needed. Point and segment annotations typically carry tips.

#### Coach Tip pattern in transformers

```python
# In any _compute_*_annotations() function:

def _my_metric_coach_tip(value: float, ideal_zone: tuple[float, float]) -> str:
    """Return a coaching cue for [metric name].

    To add a new scenario, insert an if branch here and return a string.
    """
    z_low, z_high = ideal_zone
    if value > z_high:
        deficit = abs(value - z_high)
        return f'[Action] — {deficit:.1f}° short of ideal'
    if value < z_low:
        excess = abs(value - z_low)
        return f'[Action] — {excess:.1f}° past ideal'
    return '[Metric] within ideal range ✓'

# Then pass it to the annotation constructor:
PointAnnotation(
    label='[P1]',
    description=f'Peak Force: {value:.0f} W',
    x=..., y=...,
    coach_tip=_my_metric_coach_tip(value, IDEAL_ZONE),
)
```

### 4.2 Extended `compute()` Output Contract

The `PlotComponent.compute()` return dict gains a new key:

```python
{
    'data':        {...},
    'metadata':    {...},
    'coach_tip':   str,                    # plot-level tip shown in st.info()
    'annotations': list[AnnotationEntry],  # [] if none; each entry may carry its own coach_tip
    'annotation_defs': list[AnnotationDefinition],  # for pre-compute toggles (Phase 5)
}
```

**Two levels of coaching tips:**

| Level | Where | Purpose |
|---|---|---|
| Plot-level `coach_tip` | `compute()` return dict | One-sentence summary for the whole plot. Shown via `st.info()` below the figure. |
| Annotation-level `ann.coach_tip` | Each `AnnotationEntry` field | Specific cue for that annotation's data point/segment/zone. Shown in the legend table's Coach Tip column. |

**Backward compatible:** All existing renderers use `.get('annotations', [])` so they continue to work unchanged.

### 4.3 Utility Functions in `rowing_catch/plot/utils.py`

```python
def apply_annotations(
    ax: matplotlib.axes.Axes,
    annotations: Sequence[AnnotationEntry],
    active_labels: set[str] | None = None,
    axis_id: str = 'main',
    color_overrides: dict[str, str] | None = None,
) -> list[tuple[str, str, str]]:
    """Apply visible annotations to an axes.

    Returns:
        List of (label, description, coach_tip) 3-tuples for the visible
        annotations. Pass this to render_annotation_legend_on_figure().
    """


def render_annotation_legend_on_figure(
    fig: matplotlib.figure.Figure,
    ax_legend: matplotlib.axes.Axes,
    legend_items: list[tuple[str, str, str]],   # (label, description, coach_tip)
    colors: list[str] | None = None,
    font_size: int = 8,
) -> None:
    """Render a 3-column legend table (Ref | Description | Coach Tip) in ax_legend.

    The Coach Tip column is omitted entirely when all tips are empty,
    keeping the table compact for unannotated plots.
    """


def draw_segment_backdrop(
    ax: matplotlib.axes.Axes,
    x: list[float],
    y: list[float],
    color: str,
    n_layers: int = 4,
    base_linewidth: float = 2.5,
) -> None:
    """Draw a wide semi-transparent backing line behind the original data line."""
```

### 4.4 Toggle Wiring — Page Layer Pattern

```python
# rowing_catch/page/development.py

computed = component.compute(avg_cycle, catch_idx, finish_idx)
annotations = computed.get('annotations', [])

# Render toggles below the plot header
if annotations:
    with st.expander("🔍 Annotations", expanded=False):
        # Master toggle — show/hide all annotations with one click
        show_all = st.checkbox('Show all annotations', value=True, key=f'ann_{component.name}_show_all')
        st.divider()
        if show_all:
            # Individual toggles — only active when master is on
            active = {
                ann.label
                for ann in annotations
                if st.checkbox(
                    f"{ann.label} — {ann.description}",
                    value=True,
                    key=f"ann_{component.name}_{ann.label}",
                )
            }
        else:
            # Render individual checkboxes as disabled for discoverability
            for ann in annotations:
                st.checkbox(
                    f"{ann.label} — {ann.description}",
                    value=False,
                    key=f"ann_{component.name}_{ann.label}",
                    disabled=True,
                )
            active = set()  # hide all
else:
    active = set()

# Render with active filter
render_trunk_angle(computed, active_annotations=active)
```

**Master toggle behaviour:**
- **On** (default): individual checkboxes are live — each annotation can be toggled independently.
- **Off**: all individual checkboxes are rendered as disabled (so the user can still see what annotations exist) and `active_annotations=set()` is passed → all annotations hidden.
- Passing `set()` (empty set) hides all annotations. Passing `None` shows all (backward-compatible default).

### 4.5 Renderer Signature Extension

Each renderer gains one optional parameter:

```python
def render_trunk_angle(
    computed_data: dict[str, Any],
    active_annotations: set[str] | None = None,  # NEW
    return_fig: bool = False,                    # NEW — for PDF export
) -> matplotlib.figure.Figure | None:
```

**`active_annotations=None`** means "show all" → backward compatible.  
**`return_fig=True`** skips `st.pyplot(fig)` and returns the `Figure` → used by PDF export.

### 4.6 PDF Export Module

New file: `rowing_catch/export/pdf_export.py`

```python
from matplotlib.backends.backend_pdf import PdfPages

def export_plots_to_pdf(
    plot_specs: list[dict[str, Any]],  # list of {component, computed, active_annotations}
    output_path: str,
) -> None:
    """Export a list of rendered plots to a single PDF file.

    Each plot is rendered with return_fig=True and saved to the PDF.
    Annotations are baked in based on active_annotations filter.
    """
    with PdfPages(output_path) as pdf:
        for spec in plot_specs:
            fig = spec['renderer'](
                spec['computed'],
                active_annotations=spec.get('active_annotations'),
                return_fig=True,
            )
            if fig:
                pdf.savefig(fig, bbox_inches='tight')
                plt.close(fig)
```

A "📄 Download PDF" button in the page layer calls this and returns the bytes via `st.download_button`.

### 4.7 `AnnotationDefinition` for Pre-Compute Toggles (Optional Phase 2)

Add to `PlotComponent` base class:

```python
@property
def annotation_definitions(self) -> list[AnnotationDefinition]:
    """Declare annotation types this component can produce.
    Used to render toggles BEFORE calling compute() — important for
    expensive computations that should be skipped if toggled off.
    Override in subclasses to enable pre-compute toggle UI.
    """
    return []
```

This is optional and can be added in Phase 2 when computation becomes expensive enough to matter.

---

## 5. Package/Module Layout

```
rowing_catch/
├── plot_transformer/
│   ├── annotations.py          # NEW — AnnotationEntry dataclasses + palette
│   ├── base.py                 # Updated — documents 'annotations' key in compute()
│   ├── trunk/
│   │   └── trunk_angle_transformer.py   # First to get annotations
│   └── ...
├── plot/
│   ├── utils.py                # Updated — apply_annotations(), render_annotation_legend(), draw_segment_backdrop()
│   ├── theme.py                # Updated — ANNOTATION_COLORS palette
│   └── trunk/
│       └── trunk_angle_plot.py # First renderer to use apply_annotations()
└── export/
    └── __init__.py             # NEW package
    └── pdf_export.py           # NEW — PdfPages export utility
tests/
└── plot_transformer/
    └── test_annotations.py     # NEW — test dataclass construction + auto color assignment
```

---

## 6. Annotation Color Assignment

Auto-assign colors from the palette so transformers don't need to hardcode:

```python
def assign_annotation_colors(
    annotations: list[AnnotationEntry],
    palette: list[str] = ANNOTATION_COLORS,
) -> list[AnnotationEntry]:
    """Assign palette colors to annotations that have color=None."""
    color_iter = iter(palette)
    result = []
    for ann in annotations:
        if ann.color is None:
            ann = dataclasses.replace(ann, color=next(color_iter, '#888888'))
        result.append(ann)
    return result
```

This is called inside `apply_annotations()` so transformers never need to import from `plot/`.

---

## 7. Implementation Roadmap

### Phase 1 — Foundation (Week 1)

1. **Create `rowing_catch/plot_transformer/annotations.py`** with all dataclasses + palette + `assign_annotation_colors()`.
2. **Update `rowing_catch/plot/theme.py`** — add `ANNOTATION_COLORS` list.
3. **Update `rowing_catch/plot/utils.py`** — add `apply_annotations()`, `render_annotation_legend()`, `draw_segment_backdrop()`.
4. **Update `base.py`** docstring to document the `annotations` and `annotation_defs` keys.
5. **Tests**: `tests/plot_transformer/test_annotations.py` — test dataclass construction, color assignment, label uniqueness.

### Phase 2 — First Pilot Plot (Week 2)

6. **Update `TrunkAngleComponent.compute()`** — add 2–3 `PointAnnotation` entries: catch angle deviation, finish angle deviation, peak lean.
7. **Update `render_trunk_angle()`** — accept `active_annotations`, call `apply_annotations()`, render legend table.
8. **Update `page/development.py`** — add toggle expander for trunk angle annotations.
9. **Visual QA** — run the app, verify segment backdrop on light background, verify PDF screenshot quality.

### Phase 3 — Rollout (Weeks 3–4)

> ⚠️ **Coaching content review required before each transformer.** Agree on the coaching scenarios, thresholds, and exact wording with the developer before writing any `_*_coach_tip()` function. Do not implement tips speculatively.

10. Migrate each transformer to add domain-specific annotations. Priority order:
    - `KineticChainComponent` — segment highlights per body segment
    - `VelocityProfileComponent` — peak velocity point, deceleration segment
    - `PowerAccumulationComponent` — peak power point, drive phase band
    - `RecoverySlideControlComponent` — consistency band
    - Remaining transformers

### Phase 4 — PDF Export (Week 5)

11. **Create `rowing_catch/export/` package** with `pdf_export.py`.
12. **Add `return_fig` parameter** to all renderers.
13. **Wire "Download PDF" button** in the report page.
14. **Test PDF output** — verify annotations are baked in, legend table renders correctly.

### Phase 5 — Pre-Compute Toggles (Phase 2, optional)

15. Add `annotation_definitions` to `PlotComponent` base class.
16. Update page layer to render toggles before `compute()`.
17. Add `@st.cache_data` to expensive `compute()` calls.

---

## 8. Pilot Learnings & Updated Gotchas (Phase 2 Post-Mortem)

These are concrete issues discovered during implementation of the pilot on `TrunkAngleComponent` / `render_trunk_angle_with_stage_stickfigures`. Update future rollout plans accordingly.

---

### 8.1 ✅ RESOLVED — Legend Table Overlaps Multi-Axis Plot Bottom

**What the plan said:** Place the annotation legend as `fig.text()` entries in the bottom margin of the figure using `fig.transFigure` coordinates.

**What actually happened (attempt 1):** The trunk angle plot has two subplots (`ax_top` at height ratio 3, `ax_bot` at height ratio 2). `ax_bot` occupies the bottom ~35% of the figure canvas in figure-coordinate space — exactly where `fig.text()` at `y=0.02–0.18` tried to place the legend. The text overlaid directly on the stick figures.

**Intermediate fix (rejected):** `render_annotation_legend()` was briefly changed to a Streamlit widget (`st.markdown()` below `st.pyplot()`). This avoided the overlap but moved the legend *outside* the matplotlib figure — not on the diagram, not PDF-safe, and not what was wanted.

**Final resolution:** The figure layout was switched from `plt.subplots()` to a **3-row `GridSpec`**:

```
┌─────────────────────────────┐  height ratio: 3
│  ax_top  (trunk angle trace)│
├─────────────────────────────┤  height ratio: 2
│  ax_bot  (stick figures)    │
├─────────────────────────────┤  height ratio: 0.35 × n_active_annotations
│  ax_legend (table)          │
└─────────────────────────────┘
```

- `ax_legend` is sized dynamically (0.35 units per annotation row); collapses to `0.001` when empty
- `render_annotation_legend_on_figure(fig, ax_legend, legend_items, colors)` draws a styled `matplotlib.table` filling the full `ax_legend` axes via `bbox=(0.0, 0.0, 1.0, 1.0)`
- Table has a light header, colored bold ref labels matching each annotation's palette color, and subtle `#E8E8E8` borders
- Fully baked into the `Figure` — works for both Streamlit display and PDF export

**Rule for rollout:** For multi-axis plots with a stick figure or detail panel at the bottom, use a 3-row `GridSpec` with an explicit `ax_legend` row. Size it with `height_ratio = 0.35 × n_active_annotations`. Pass `ax_legend` to `render_annotation_legend_on_figure()`. Never use `fig.text()` or `fig.add_axes()` to place the legend — both conflict with `constrained_layout`.

---

### 8.2 ✅ RESOLVED — Band Text Placed Outside Visible Plot Area

**What the plan said:** `BandAnnotation` with `x_start=None`/`x_end=None` uses `ax.get_xlim()` at draw time to span full width.

**What actually happened:** `ax_top` shares its x-axis with `ax_bot` via `sharex=True`. `ax_bot` has an explicit `set_xlim(x_min - 5, x_max + 5)` padding call, which propagates to `ax_top`. When `apply_annotations()` called `ax.get_xlim()` to resolve the band width, it got the padded range. The "Ideal Catch Range" / "Ideal Finish Range" display texts were then placed at 80–97% of `x_max + 5` — well outside the visible data area.

**Resolution:** `BandAnnotation` gained explicit `x_start` and `x_end` fields pinned to the actual data range (`x_min`, `x_max`) in the transformer. These are now passed via `_compute_trunk_annotations(x_min=..., x_max=...)`. The renderer no longer needs to know about this.

**Rule for rollout:** Always set explicit `x_start`/`x_end` on `BandAnnotation` when the axes uses shared x or has padding in `set_xlim()`. Never rely on `ax.get_xlim()` for text placement in shared-axis plots.

---

### 8.3 ✅ RESOLVED — `BandAnnotation` Needed a `display_name` Field

**What the plan said:** `BandAnnotation` has `label` (reference like `[A4]`) and `description` (legend table text).

**What actually happened:** The existing plot showed "Ideal Catch" / "Ideal Finish" text directly on the zones. Moving these zones to annotations meant losing that in-plot text. Two fields were not enough: `label` is the reference badge, `description` is the legend table row — but neither is suitable for rendering as a concise human-readable label inside the band on the plot.

**Resolution:** Added `display_name: str | None = None` to `BandAnnotation`. This is the short text rendered inside the shaded area (e.g. `'Ideal Catch Range'`). Defaults to `None` → no in-plot text. The `_draw_band_annotation()` helper renders it centered at 80% of the band's x width.

**Rule for rollout:** Any `BandAnnotation` that replaces a previously hard-coded zone label should set `display_name` to preserve the on-plot text.

---

### 8.4 NEW GOTCHA — `ax.get_xlim()` / `ax.get_ylim()` in `apply_annotations()` Reflect State at Call Time

**Confirmed during pilot:** `_draw_point_annotation()` uses `ax.get_ylim()` to compute a vertical offset for badge placement. This offset is computed relative to the axes limits *at the time `apply_annotations()` is called* — which is after the main data is plotted but before `ax.legend()` or `ax.set_ylim()` calls that follow it.

In the trunk angle renderer, `apply_annotations()` is called after `ax_top.legend()`, so the ylim is stable. But in renderers where the ylim changes *after* `apply_annotations()` (e.g. due to a later `ax.set_ylim()` or `ax.autoscale()`), badge offsets will be wrong.

**Rule for rollout:** Always call `apply_annotations()` as the **last operation on an axes before `st.pyplot()`**, after all data, legends, and axis limits are set. If `set_ylim()` is called after annotation, the offset calculations will be stale.

---

### 8.5 NEW GOTCHA — `BandAnnotation` with `x_start=None` Falls Back to Padded `xlim`

Already documented in 8.2 above, but worth restating as a general rule:

**Never use `x_start=None` on a `BandAnnotation` in any plot that calls `set_xlim()` with padding** (e.g. `set_xlim(x_min - 5, x_max + 5)`). The `_draw_band_annotation()` helper resolves `None` via `ax.get_xlim()`, which includes the padding. This makes the band span into the padded region and pushes `display_name` text out of the visible area.

---

### 8.6 ✅ RESOLVED — `render_annotation_legend_on_figure()` Under `constrained_layout`

**Previous risk:** The original implementation of `render_annotation_legend_on_figure()` used `fig.add_axes()` with coordinates derived from `ax_ref.get_position()`. Under `constrained_layout=True`, axes positions are not final until the figure is drawn, making this coordinate calculation unreliable — the table could overlap other content.

**Resolution:** The function signature was updated to accept a **pre-allocated `ax_legend` axes** (the third `GridSpec` row) instead of `ax_ref`. It no longer calls `fig.add_axes()` or reads any position. The caller (the renderer) is responsible for creating the `GridSpec` with the right height ratios before the function is called. This completely sidesteps the `constrained_layout` conflict.

**Updated signature:**
```python
def render_annotation_legend_on_figure(
    fig: matplotlib.figure.Figure,   # kept for API symmetry, not used internally
    ax_legend: matplotlib.axes.Axes, # the pre-allocated legend row axes
    legend_items: list[tuple[str, str]],
    colors: list[str] | None = None,
    font_size: int = 8,
) -> None:
```

**Rule for rollout:** Always pre-allocate `ax_legend` in the renderer's `GridSpec`. Do not call `fig.add_axes()` inside `render_annotation_legend_on_figure()`.

---

### 8.10 NEW GOTCHA — `Sequence` Import Must Come from `collections.abc`, Not `typing`

Python 3.9+ deprecates `typing.Sequence` in favour of `collections.abc.Sequence`. ruff rule `UP035` flags `from typing import Sequence` as a fixable error. All `Sequence` uses in this codebase must use:

```python
from collections.abc import Sequence
```

Not:

```python
from typing import Sequence  # ❌ ruff UP035
```

---

### 8.11 ✅ RESOLVED — Coach Tip is a Generic First-Class Feature on All Annotation Types

**What was attempted:** Coach tips were first considered a trunk-angle-specific feature, with per-annotation tips only added to `PointAnnotation`.

**Final design:** `coach_tip: str = ''` is a **standard field on every annotation dataclass** — `PointAnnotation`, `SegmentAnnotation`, `BandAnnotation`, `PhaseAnnotation`. It is part of the core data contract, not a bolt-on.

**How it works end-to-end:**
1. The transformer computes the tip from measured data and ideal zones via a pure function (e.g. `_catch_lean_coach_tip(value, zone) -> str`)
2. The tip is set on the annotation at construction time: `coach_tip=_catch_lean_coach_tip(...)`
3. `apply_annotations()` returns `list[tuple[str, str, str]]` — `(label, description, coach_tip)` — carrying the tip to the renderer
4. `render_annotation_legend_on_figure()` renders a **Ref | Description | Coach Tip** table. The Coach Tip column is **only shown when at least one active annotation has a non-empty tip** — it collapses automatically.

**Conventions:**
- `coach_tip = ''` (empty) → blank cell, no column shown if all are empty
- Zone/reference bands (`BandAnnotation`, `PhaseAnnotation`) typically leave `coach_tip = ''` — the visual zone communicates the target
- Point and segment annotations typically carry a tip
- Tips are ≤ 12 words: specific, actionable, include the measured gap when relevant
- Tips use `→`, `✓`, `—` characters (Unicode escapes in source: `\u2192`, `\u2713`, `\u2014`)
- **Each coaching tip must be reviewed with the developer before implementation.** Scenarios, thresholds, and wording carry biomechanical meaning. Never implement tips speculatively.

**Rule for rollout:** When migrating a transformer in Phase 3, add a `_my_metric_coach_tip(value, zone) -> str` pure function with clearly commented scenario branches. Test each branch independently.

> ⚠️ **Coaching content review required.** Before implementing any new `_*_coach_tip()` function, discuss the intended scenarios, thresholds, and wording with the developer. Rowing coaching cues carry biomechanical meaning — incorrect thresholds or misleading phrasing can give a rower bad advice. Do not implement coaching tips speculatively. Agree on scenarios first, then code.

---

## 9. Open Questions / Risks (Updated)

### 9.1 ✅ RESOLVED — Segment Backdrop on Light Background
Changed from multi-layer neon glow to a single wide semi-transparent backing line (`draw_segment_backdrop`): `linewidth = base_linewidth * 5`, `alpha = 0.25`, `zorder = 4` (behind the main line). Works cleanly on white axes — clearly visible without washing out the data trace. The annotation palette colour is always distinct from `COLOR_MAIN` (indigo `#6366F1` was removed from the palette for being too close to `#636EFA`).

### 9.1b ✅ RESOLVED — Type-Prefixed Reference Labels (`[P]`, `[S]`, `[Z]`, `[R]`)

Changed from generic sequential `[A1]–[A6]` to type-prefixed labels that encode the visual geometry:

| Prefix | Type | Visual |
|--------|------|--------|
| `[P1]`, `[P2]` | `PointAnnotation` | ● callout dot + arrow |
| `[S1]`, `[S2]` | `SegmentAnnotation` | ━━ wide backdrop line |
| `[Z1]`, `[Z2]` | `BandAnnotation` | ░░ shaded horizontal band |
| `[R1]` | `PhaseAnnotation` | ▓▓ vertical shaded region |

Trunk angle plot labels after rename:
```
[P1] Catch Lean: −31° (ideal −35°–−25°, +4°)
[P2] Finish Lean: +28° (ideal +25°–+35°, −3°)
[S1] Drive phase: −31° → +28° (59° range)
[Z1] Ideal Catch Zone: −35° to −25°
[Z2] Ideal Finish Zone: +25° to +35°
[S2] Recovery: +28° → −31° (59° rock-over)
```

Counters are **per-plot** — each plot starts at `[P1]`, `[S1]`, `[Z1]` independently.

**Rule for rollout:** Always use the type-prefix scheme. `[A_]` labels are retired.

### 9.2 ✅ RESOLVED — Multi-Axis Plots
`axis_id: str` field on each `AnnotationEntry` is working. The trunk angle pilot uses `axis_id='top'` for all 5 annotations. `ax_bot` (stick figures) receives no annotations. `apply_annotations()` takes an `axis_id` parameter and filters accordingly.

### 9.3 OPEN — Streamlit Rerun Cost
Every `st.checkbox` toggle triggers a full Streamlit rerun including `component.compute()`. Currently acceptable for the trunk angle component (fast computation). Will become an issue if compute involves signal processing or large datasets. Mitigation: `@st.cache_data` on compute calls. Pre-compute toggle API (Phase 5) is the long-term solution.

### 9.4 ✅ RESOLVED — `return_fig` Return Type
Implemented as `-> matplotlib.figure.Figure | None`. Renderers return `fig` when `return_fig=True`, else call `st.pyplot(fig)` and return `None`. mypy is satisfied.

### 9.5 OPEN — `adjustText` for Dense Labels
Not yet needed — trunk angle has only 5 annotations, none overlapping. Will evaluate when plots with denser annotations (e.g. kinetic chain with per-segment labels) are migrated in Phase 3.

### 9.6 ✅ RESOLVED — `render_annotation_legend_on_figure()` Under `constrained_layout`
See gotcha 8.9 above. Resolved by redesigning the function to accept a pre-allocated `ax_legend` axes from the `GridSpec` instead of using `fig.add_axes()`. PDF export path is now consistent with the Streamlit display path.

---

## 10. Reference: Existing Annotation Patterns in the Codebase

The codebase already uses several annotation-like patterns. The new system should standardize and extend them:

| Existing pattern | File | New system equivalent |
|---|---|---|
| `ax.axvspan(catch_idx, ...)` | Multiple renderers | `PhaseAnnotation` |
| `ax.axhline(ideal_value, ...)` | Trunk angle renderer | `BandAnnotation` (y_low=y_high) |
| `ax.annotate(text, xy=...)` | Ad-hoc in some renderers | `PointAnnotation` with `style='callout'` |
| `ax.text(x, y, label)` | Ad-hoc | `PointAnnotation` with `style='label'` |
| `ax.fill_between(x, y1, y2)` | Recovery slide control | `BandAnnotation` |

The goal is to replace all ad-hoc annotations with the typed system so they become togglable and PDF-consistent.

---

## 11. Key Design Decisions Summary (Updated)

| Decision | Planned | Actual (post-pilot) |
|---|---|---|
| Primary library | matplotlib only | ✅ matplotlib only |
| Annotation home | `plot_transformer/annotations.py` (Layer 2) | ✅ Implemented as planned |
| Toggle mechanism | `set[str]` passed from page → renderer | ✅ Implemented as planned |
| Color assignment | Auto from palette in `apply_annotations()` | ✅ Auto for new annotations; **explicit module-level constants for semantic replacements** |
| Legend table | matplotlib `Table` artist on a sub-axes | ✅ **Implemented as planned** — `render_annotation_legend_on_figure(fig, ax_legend, ...)` draws a styled `matplotlib.table` inside a dedicated `GridSpec` row (`ax_legend`). Fully in-figure, PDF-safe. `render_annotation_legend()` (Streamlit fallback) kept for future simpler plots. |
| PDF export | `matplotlib.backends.backend_pdf.PdfPages` | 🔜 Phase 4 — not yet implemented |
| Highlight style default | `glow` on dark segments | ✅ **Changed**: replaced neon glow (layered alpha) with `draw_segment_backdrop` — single wide semi-transparent line (`linewidth × 5`, `alpha=0.25`, `zorder=4`) behind the main trace. Cleaner on white axes. |
| `BandAnnotation` | `label` + `description` only | ⚠️ **Extended**: added `display_name` field for in-plot text |
| `BandAnnotation` x bounds | `None` → resolves via `ax.get_xlim()` | ⚠️ **Changed**: always set explicit `x_start`/`x_end` in shared-axis plots |
| Figure layout (multi-axis) | `plt.subplots()` with 2 rows | ⚠️ **Changed**: 3-row `GridSpec` with dynamic `ax_legend` row sized as `0.35 × n_active_annotations`; collapses to `0.001` when no annotations active |
| `coach_tip` on annotations | Not in original plan | ✅ **Added**: `coach_tip: str = ''` on **all four** annotation types. Generic, data-driven, computed in transformer via pure `_*_coach_tip()` functions. Legend shows **Ref \| Description \| Coach Tip**; column collapses when all empty. |
| Annotation reference labels | `[A1]`–`[An]` sequential | ✅ **Changed**: type-prefixed — `[P_]` points, `[S_]` segments, `[Z_]` zones, `[R_]` regions. Counters reset per plot. Trunk angle: `[P1]`, `[P2]`, `[S1]`, `[Z1]`, `[Z2]`, `[S2]`. |
| `apply_annotations()` return type | `list[tuple[str, str]]` | ⚠️ **Changed**: `list[tuple[str, str, str]]` — `(label, description, coach_tip)` |
| `Sequence` import | `typing.Sequence` | ⚠️ **Changed**: must use `collections.abc.Sequence` (ruff UP035) |

