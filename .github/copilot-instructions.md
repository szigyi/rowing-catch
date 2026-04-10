# Rowing Catch - Development Instructions for AI Agents

This is a streamlit app that lets you analyze your rowing data.

## Architecture Overview

This project follows a strict 4-layer architecture. **All code changes must respect these layers.**

### The 4 Layers (Bottom to Top)

1. **Layer 1: Core** (`rowing_catch/algo/`, `rowing_catch/scenario/`)
   - Pure data processing, no UI concerns
   - No dependencies on plots or pages

2. **Layer 2: Transforms** (`rowing_catch/plot_transforms/`)
   - Each plot = one transform class inheriting `PlotComponent`
   - Must implement `compute(avg_cycle, catch_idx, finish_idx, ...) → dict[str, Any]`
   - Returns: `{'data': {...}, 'metadata': {...}, 'coach_tip': '...'}`
   - **Cannot** import from `plots/` or `pages/`

3. **Layer 3: Renderers** (`rowing_catch/plots/`)
   - Pure visualization functions: `render_myplot(computed_data)`
   - Use `setup_premium_plot()` from `plots/utils.py`
   - Use colors from `plots/theme.py`
   - **Cannot** compute or import from `pages/`

4. **Layer 4: Pages** (`pages/`)
   - Minimal orchestration: `component.compute() → renderer.render()`
   - Can import from components and plots only

### Import Rule (Strict)

```
pages/           ← imports from (plot_transforms, plots)
    ↑
plots/           ← imports from (plot_transforms, algo)
    ↑
plot_transforms/ ← imports from (algo, scenario)
    ↑
algo/, scenario/ ← imports from each other only
```

**No circular imports. No upward dependencies.**

## File Naming Convention

All files follow a strict suffix convention that makes the layer immediately obvious from the filename:

| Layer | Location | Suffix | Example |
|---|---|---|---|
| Transform | `rowing_catch/plot_transforms/` | `_transformer.py` | `trunk_angle_transformer.py` |
| Renderer | `rowing_catch/plots/` | `_plot.py` | `trunk_angle_plot.py` |

**No exceptions.** `theme.py`, `utils.py`, `base.py`, and `registry.py` are infrastructure files and are exempt.

## Adding a New Plot - Checklist

When adding a new plot, follow this exact pattern:

1. ✅ Create `rowing_catch/plot_transforms/myplot_transformer.py` with `MyPlotComponent` class
2. ✅ Create `rowing_catch/plots/myplot_plot.py` with `render_myplot()` function
3. ✅ Export from `rowing_catch/plot_transforms/__init__.py`
4. ✅ Export from `rowing_catch/plots/__init__.py`
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
# File: rowing_catch/plot_transforms/myplot_transformer.py

from typing import Any

import pandas as pd

from rowing_catch.plot_transforms.base import PlotComponent


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
# File: rowing_catch/plots/myplot_plot.py

from typing import Any

import streamlit as st

from rowing_catch.plots.theme import COLOR_MAIN
from rowing_catch.plots.utils import setup_premium_plot


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

## Common Mistakes (DO NOT DO)

- ❌ Import `plots/` in `plot_transforms/` → Violates layer dependency
- ❌ Import `pages/` anywhere → Violates layering
- ❌ Mix computation and rendering → Breaks separation of concerns
- ❌ Add coach_tip directly in renderer → Belongs in transform
- ❌ Hardcode colors → Use `plots/theme.py`
- ❌ Skip type annotations → mypy will fail
- ❌ Use `float(value)` on pandas scalars without `cast()` → mypy error

## Testing

### Rules

- **All pure functions must have tests.** If a function takes inputs and returns outputs with no side effects, it must be covered by `pytest` tests.
- **Keep business logic out of UI code.** Calculations, data transformations, and coaching logic must live in `algo/`, `scenario/`, or `plot_transforms/` — never inline in a page or renderer. This makes them independently testable.
- **Renderers are not tested directly.** Streamlit/matplotlib rendering is UI — test the `compute()` output instead.

### What to test

| Layer | What to test |
|---|---|
| `algo/` | All helper functions, signal processing, index detection |
| `scenario/` | Scenario logic, data loading, transformations |
| `plot_transforms/` | `compute()` output shape, values, coach tips |
| `plots/` | Not tested directly (rendering) |
| `pages/` | Not tested directly (UI orchestration) |

### Test structure

Place tests under `tests/` mirroring the source layout:

```
tests/
    algo/
        test_helpers.py
        test_analysis.py
    scenario/
        test_*.py
    plot_transforms/
        test_trunk_angle.py
        test_kinetic_chain.py
        ...
```

### Example: extracting logic for testability

**❌ Bad — logic buried in page, untestable:**
```python
# pages/1_Trunk_Angle.py
drive_angle = avg_cycle['trunk_angle'].iloc[catch_idx] - avg_cycle['trunk_angle'].iloc[finish_idx]
st.metric("Drive angle", f"{drive_angle:.1f}°")
```

**✅ Good — logic in transform, tested separately:**
```python
# rowing_catch/plot_transforms/trunk_angle.py
def compute_drive_angle(avg_cycle: pd.DataFrame, catch_idx: int, finish_idx: int) -> float:
    return float(avg_cycle['trunk_angle'].iloc[catch_idx] - avg_cycle['trunk_angle'].iloc[finish_idx])

# tests/plot_transforms/test_trunk_angle.py
def test_compute_drive_angle():
    df = pd.DataFrame({'trunk_angle': [30.0, 20.0, 10.0]})
    assert compute_drive_angle(df, catch_idx=0, finish_idx=2) == 20.0
```

## Before Committing

Always run:

```bash
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
- Transform base class: [rowing_catch/plot_transforms/base.py](rowing_catch/plot_transforms/base.py)
- Theme colors: [rowing_catch/plots/theme.py](rowing_catch/plots/theme.py)
- Plot utilities: [rowing_catch/plots/utils.py](rowing_catch/plots/utils.py)

## Key Insight

The point of this architecture is to make adding new plots **trivial and reusable**:

- Add a plot? → Create component + renderer, export from `__init__.py`
- Reuse a plot? → Import `MyPlotComponent` and `render_myplot()` directly in any page
- Test a plot? → Test component independently from UI
- Change styling? → Update `theme.py` once, all plots update
- Modify computation? → Update component, renderer stays the same
- Update rendering? → Update renderer, computation stays the same

**Separation of concerns = easy maintenance.**
