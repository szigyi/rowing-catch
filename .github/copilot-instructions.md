# Rowing Catch - Development Instructions for AI Agents

This is a streamlit app that lets you analyze your rowing data.

## Architecture Overview

This project follows a strict 4-layer architecture. **All code changes must respect these layers.**

### The 4 Layers (Bottom to Top)

1. **Layer 1: Core** (`rowing_catch/algo/`, `rowing_catch/scenario/`)
   - Pure data processing, no UI concerns
   - No dependencies on plots or pages

2. **Layer 2: Transforms** (`rowing_catch/plot_transformer/`)
   - Each plot = one transform class inheriting `PlotComponent`
   - Must implement `compute(avg_cycle, catch_idx, finish_idx, ...) → dict[str, Any]`
   - Returns: `{'data': {...}, 'metadata': {...}, 'coach_tip': '...'}`
   - **Cannot** import from `plot/` or `page/`

3. **Layer 3: Renderers** (`rowing_catch/plot/`)
   - Pure visualization functions: `render_myplot(computed_data)`
   - Use `setup_premium_plot()` from `plot/utils.py`
   - Use colors from `plot/theme.py`
   - **Cannot** compute or import from `page/`

4. **Layer 4: Pages** (`rowing_catch/page/`)
   - Minimal orchestration: `component.compute() → renderer.render()`
   - Can import from components and plots only

### Import Rule (Strict)

```
rowing_catch/page/           ← imports from (plot_transformer, plot)
    ↑
rowing_catch/plot/           ← imports from (plot_transformer, algo)
    ↑
rowing_catch/plot_transformer/ ← imports from (algo, scenario)
    ↑
rowing_catch/algo/, rowing_catch/scenario/ ← imports from each other only
```

**No circular imports. No upward dependencies.**

## File Naming Convention

All files follow a strict suffix convention that makes the layer immediately obvious from the filename:

| Layer      | Location                         | Suffix            | Example                      |
|------------|----------------------------------|-------------------|------------------------------|
| Transform  | `rowing_catch/plot_transformer/` | `_transformer.py` | `trunk_angle_transformer.py` |
| Renderer   | `rowing_catch/plot/`             | `_plot.py`        | `trunk_angle_plot.py`        |

**No exceptions.** `theme.py`, `utils.py`, `base.py`, and `registry.py` are infrastructure files and are exempt.

## Adding a New Plot - Checklist

When adding a new plot, follow this exact pattern:

1. ✅ Create `rowing_catch/plot_transformer/myplot_transformer.py` with `MyPlotComponent` class
2. ✅ Create `rowing_catch/plot/myplot_plot.py` with `render_myplot()` function
3. ✅ Export from `rowing_catch/plot_transformer/__init__.py`
4. ✅ Export from `rowing_catch/plot/__init__.py`
5. ✅ Import and use in page directly

**Do not deviate from this pattern.**

## Code Quality Gates

All code must pass:

- **Type Checking**: `python -m mypy rowing_catch/`
  - All functions need type annotations
  - Use `cast()` from typing for pandas scalar narrowing
  - Use `dict[str, Any]` for flexible dicts

- **Linting**: `ruff check .`
  - No trailing whitespace
  - No unused variables
  - PEP 8 compliance

- **Pre-Commit**: `pre-commit run --all-files`
  - Must pass all checks before committing

- **Tests**: `python -m pytest tests/ -v`
  - Keep existing tests passing

## Transform Pattern (Copy-Paste Template)

```python
"""MyPlot transform.

Transforms analysis results into data ready for rendering my plot.
"""
# File: rowing_catch/plot_transformer/myplot_transformer.py

from typing import Any

import pandas as pd

from rowing_catch.plot_transformer.base import PlotComponent


class MyPlotComponent(PlotComponent):
    """MyPlot visualization component."""

    @property
    def name(self) -> str:
        return "My Plot"

    @property
    def description(self) -> str:
        return "Description of what this plot shows"

    def compute(
            self,
            avg_cycle: pd.DataFrame,
            catch_idx: int,
            finish_idx: int,
            ghost_cycle: pd.DataFrame | None = None,
            results: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Compute plot-ready data.

        Args:
            avg_cycle: DataFrame with rowing stroke data
            catch_idx: Index of catch
            finish_idx: Index of finish
            ghost_cycle: Optional comparison DataFrame
            results: Optional full analysis results dict

        Returns:
            Dict with 'data', 'metadata', 'coach_tip' keys
        """
        # Your computation here
        data = {...}

        return {
            'data': data,
            'metadata': {
                'title': 'My Plot',
                'x_label': 'Stroke Index',
                'y_label': 'Units',
            },
            'coach_tip': 'Advice for the rower'
        }
```

## Renderer Pattern (Copy-Paste Template)

```python
"""MyPlot renderer.

Renders plot-ready data as matplotlib figure and Streamlit widgets.
"""
# File: rowing_catch/plot/myplot_plot.py

from typing import Any

import streamlit as st

from rowing_catch.plot.theme import COLOR_MAIN
from rowing_catch.plot.utils import setup_premium_plot


def render_myplot(computed_data: dict[str, Any]):
    """Render myplot from computed data.

    Args:
        computed_data: Output from MyPlotComponent.compute()
    """
    data = computed_data['data']
    metadata = computed_data['metadata']
    coach_tip = computed_data['coach_tip']

    fig, ax = setup_premium_plot(
        title=metadata['title'],
        x_label=metadata['x_label'],
        y_label=metadata['y_label'],
    )

    # Render to matplotlib
    ax.plot(data['x'], data['y'], color=COLOR_MAIN, linewidth=2.5)

    st.pyplot(fig)
    st.info(coach_tip)
```

## Coaching Tips Pattern

When a plot component produces annotation-level coaching tips that carry **conditional logic** (e.g. green/yellow/red thresholds), extract that logic into a dedicated `tip/` sub-package inside the transformer package. This mirrors the pattern used by `plot_transformer/trunk/tip/`.

### Structure

```
rowing_catch/plot_transformer/<domain>/
    __init__.py
    <domain>_transformer.py       ← imports from tip/
    tip/
        __init__.py               ← re-exports all public tip functions
        <domain>_tips.py          ← pure tip functions only
```

### Tip Function Contract

Each tip function must:
- Be a **pure function** (no side effects, no imports from `plot/` or `page/`)
- Accept only plain Python scalars (`float`, `tuple[float, float]`, `list[float]`, …)
- Return **`tuple[str, bool]`** — `(cue_text, is_ideal)`
  - `is_ideal=True` → rower is within the ideal range (renders green in the UI)
  - `is_ideal=False` → improvement needed (renders red/yellow in the UI)
- Declare **named threshold constants** at module level (not magic numbers inline)
- Be covered by `pytest` tests in `tests/plot_transformer/`

### Tip Function Template

```python
# File: rowing_catch/plot_transformer/<domain>/tip/<domain>_tips.py

MY_THRESHOLD: float = 3.0  # units — below = ideal


def my_metric_coach_tip(value: float) -> tuple[str, bool]:
    """Return coaching cue and ideal-flag for <metric>.

    Args:
        value: Measured <metric> value.

    Returns:
        Tuple of (coaching cue string, is_ideal bool)
    """
    if value <= MY_THRESHOLD:
        return f'<metric> is {value:.1f} — within ideal range ✓', True
    return f'<metric> is {value:.1f} — exceeds threshold ({MY_THRESHOLD}). <Action>.', False
```

### Wiring tip functions into annotations

In the transformer, import tip functions from the `tip/` sub-package and pass both the cue and the flag to the annotation:

```python
from rowing_catch.plot_transformer.<domain>.tip import my_metric_coach_tip

tip_text, tip_ideal = my_metric_coach_tip(value)
annotations.append(
    PointAnnotation(
        label='[P1]',
        description='...',
        x=x, y=y,
        coach_tip=tip_text,
        coach_tip_is_ideal=tip_ideal,   # ← drives green/red cell in the UI
    )
)
```

### Rules

- ❌ Never inline threshold logic directly in `compute()` — it can't be tested in isolation
- ❌ Never hardcode threshold numbers as magic values — use named module-level constants
- ✅ Keep tip functions in `tip/<domain>_tips.py`, exported via `tip/__init__.py`
- ✅ Test every tip function in `tests/plot_transformer/`

### Real Example

See `rowing_catch/plot_transformer/trunk/tip/trunk_angle_tips.py` (trunk) and
`rowing_catch/plot_transformer/rhythm/tip/rhythm_consistency_tips.py` (rhythm) as reference implementations.

## Common Mistakes (DO NOT DO)

- ❌ Import `plot/` in `plot_transformer/` → Violates layer dependency
- ❌ Import `page/` anywhere → Violates layering
- ❌ Mix computation and rendering → Breaks separation of concerns
- ❌ Add coach_tip directly in renderer → Belongs in transform
- ❌ Hardcode colors → Use `plot/theme.py`
- ❌ Skip type annotations → mypy will fail
- ❌ Use `float(value)` on pandas scalars without `cast()` → mypy error

## Testing

### Rules

- **All pure functions must have tests.** If a function takes inputs and returns outputs with no side effects, it must be covered by `pytest` tests.
- **Keep business logic out of UI code.** Calculations, data transformations, and coaching logic must live in `algo/`, `scenario/`, or `plot_transformer/` — never inline in a page or renderer. This makes them independently testable.
- **Renderers are not tested directly.** Streamlit/matplotlib rendering is UI — test the `compute()` output instead.

### What to test

| Layer | What to test |
|---|---|
| `algo/` | All helper functions, signal processing, index detection |
| `scenario/` | Scenario logic, data loading, transformations |
| `plot_transformer/` | `compute()` output shape, values, coach tips |
| `plot/` | Not tested directly (rendering) |
| `page/` | Not tested directly (UI orchestration) |

### Test structure

Place tests under `tests/` mirroring the source layout:

```
tests/
    algo/
        test_helpers.py
        test_analysis.py
    scenario/
        test_*.py
    plot_transformer/
        test_trunk_angle.py
        test_kinetic_chain.py
        ...
```

### Example: extracting logic for testability

**❌ Bad — logic buried in page, untestable:**
```python
# rowing_catch/page/development.py
drive_angle = avg_cycle['trunk_angle'].iloc[catch_idx] - avg_cycle['trunk_angle'].iloc[finish_idx]
st.metric("Drive angle", f"{drive_angle:.1f}°")
```

**✅ Good — logic in transform, tested separately:**
```python
# rowing_catch/plot_transformer/trunk/trunk_angle_transformer.py
def compute_drive_angle(avg_cycle: pd.DataFrame, catch_idx: int, finish_idx: int) -> float:
    return float(avg_cycle['trunk_angle'].iloc[catch_idx] - avg_cycle['trunk_angle'].iloc[finish_idx])

# tests/plot_transformer/test_trunk_angle.py
def test_compute_drive_angle():
    df = pd.DataFrame({'trunk_angle': [30.0, 20.0, 10.0]})
    assert compute_drive_angle(df, catch_idx=0, finish_idx=2) == 20.0
```

## Before Committing

Always run:

```bash
# Activate virtual env
source .venv/bin/activate

# Type checking
python -m mypy rowing_catch/

# Linting
ruff check .

# Full pre-commit
pre-commit run --all-files

# Tests
python -m pytest tests/ -v
```

**If all pass, you're good to commit.**

## Reference Documentation

- Full architecture details: See [ARCHITECTURE.md](docs/ARCHITECTURE.md)
- Transform base class: [rowing_catch/plot_transformer/base.py](rowing_catch/plot_transformer/base.py)
- Theme colors: [rowing_catch/plot/theme.py](rowing_catch/plot/theme.py)
- Plot utilities: [rowing_catch/plot/utils.py](rowing_catch/plot/utils.py)

## Key Insight

The point of this architecture is to make adding new plots **trivial and reusable**:

- Add a plot? → Create component + renderer, export from `__init__.py`
- Reuse a plot? → Import `MyPlotComponent` and `render_myplot()` directly in any page
- Test a plot? → Test component independently from UI
- Change styling? → Update `theme.py` once, all plots update
- Modify computation? → Update component, renderer stays the same
- Update rendering? → Update renderer, computation stays the same

**Separation of concerns = easy maintenance.**
