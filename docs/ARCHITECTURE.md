# Rowing Catch - Architecture & Development Rules

This document establishes the architectural layers and development rules for the rowing-catch project.

## 4-Layer Architecture

```
┌─────────────────────────────────────────────────────┐
│  Layer 4: UI/Pages (pages/)                         │
│  Orchestration & User Interaction                   │
└─────────────────────────────────────────────────────┘
                      ↓ imports
┌─────────────────────────────────────────────────────┐
│  Layer 3: Plot Renderers (rowing_catch/plots/)      │
│  Pure Visualization & Streamlit Integration         │
└─────────────────────────────────────────────────────┘
                      ↓ imports
┌─────────────────────────────────────────────────────┐
│  Layer 2: Plot Transforms (rowing_catch/plot_transforms/)
│  Plot Computation & Data Transformation             │
└─────────────────────────────────────────────────────┘
                      ↓ imports
┌─────────────────────────────────────────────────────┐
│  Layer 1: Core (rowing_catch/algo, scenario/)       │
│  Data Pipeline & Analysis Algorithms                │
└─────────────────────────────────────────────────────┘
```

## Layer Responsibilities

### Layer 1: Core (`rowing_catch/algo/`, `rowing_catch/scenario/`)
- **Purpose**: Data processing, analysis algorithms, synthetic data generation
- **Responsibilities**:
  - Data validation and transformation
  - Rowing mechanics calculations
  - Scenario generation (synthetic test data)
  - No dependencies on visualization or transforms
- **Main Modules**:
  - `algo/steps/` - Validation and analysis steps
  - `algo/analysis.py` - Core computation functions
  - `scenario/scenarios.py` - Synthetic data generation
  - `algo/constants.py`, `algo/helpers.py` - Utilities

### Layer 2: Plot Transforms (`rowing_catch/plot_transforms/`)
- **Purpose**: Convert core analysis results into plot-ready data structures
- **Responsibilities**:
  - Inherit from `PlotComponent` abstract base
  - Implement `compute()` method: `pd.DataFrame → dict[str, Any]`
  - Accept `avg_cycle`, `catch_idx`, `finish_idx`, optional `ghost_cycle` and `results`
  - Return normalized data dict with `data`, `metadata`, `coach_tip` keys
  - **Cannot** import from `plots/` or `pages/`
- **Pattern**:
  ```python
  class MyPlotComponent(PlotComponent):
      @property
      def name(self) -> str:
          return "Display Name"
      
      def compute(self, avg_cycle, catch_idx, finish_idx, ghost_cycle=None, results=None):
          # Transform avg_cycle into plot-ready data
          return {
              'data': {...},
              'metadata': {'title': '...', 'x_label': '...', 'y_label': '...'},
              'coach_tip': 'Advice for rower'
          }
  ```

### Layer 3: Plot Renderers (`rowing_catch/plots/`)
- **Purpose**: Render plot-ready data into matplotlib figures and Streamlit widgets
- **Responsibilities**:
  - Pure visualization (no computation logic)
  - Accept output from `plot_transforms/compute()` method
  - Use consistent theme from `plots/theme.py`
  - Use shared utilities from `plots/utils.py`
  - Display plots via `st.pyplot()` or `st.write()`
  - **Cannot** import from `pages/` or perform data computation
- **Pattern**:
  ```python
  def render_myplot(computed_data: dict[str, Any]):
      data = computed_data['data']
      metadata = computed_data['metadata']
      coach_tip = computed_data['coach_tip']
      
      fig, ax = setup_premium_plot(...)
      # Render data to matplotlib
      st.pyplot(fig)
      st.info(coach_tip)
  ```

### Layer 4: UI/Pages (`pages/`)
- **Purpose**: Page orchestration and user interaction
- **Responsibilities**:
  - Handle file uploads and user input
  - Coordinate data pipeline: `upload → algo → plot_transforms.compute() → renderer`
  - Manage page-specific UI flows
  - Should be minimal "glue" code, mostly calling layer 2 & 3
  - Can import from plot_transforms and plots but not vice versa
- **Pattern**:
  ```python
  # Get plot transform from registry
  component = get_plot_component('trunk_angle')
  
  # Compute plot-ready data
  computed = component.compute(avg_cycle, catch_idx, finish_idx, ...)
  
  # Render to UI
  render_trunk_angle_with_stage_stickfigures(computed)
  ```

## Import Rules (Dependency Graph)

**Valid imports** (arrows point upward in dependency):

```
pages/                    ← imports from (plot_transforms, plots)
    ↑
rowing_catch/plots/       ← imports from (plot_transforms, algo)
    ↑
rowing_catch/plot_transforms/ ← imports from (algo, scenario)
    ↑
rowing_catch/algo/
rowing_catch/scenario/
```

**Forbidden imports**:
- ❌ `algo/` → anything above (no upward dependencies)
- ❌ `plot_transforms/` → `plots/` or `pages/`
- ❌ `plots/` → `pages/`
- ❌ `pages/` → nothing (terminal layer)
- ❌ Circular imports anywhere

**Rationale**: Lower layers should be reusable, testable independently, and not coupled to UI concerns.

## Adding a New Plot

### Step 1: Create Transform
File: `rowing_catch/plot_transforms/myplot.py`
```python
from typing import Any
import pandas as pd
from rowing_catch.plot_transforms.base import PlotComponent

class MyPlotComponent(PlotComponent):
    @property
    def name(self) -> str:
        return "My Plot"
    
    @property
    def description(self) -> str:
        return "Description of my plot"
    
    def compute(self, avg_cycle, catch_idx, finish_idx, ghost_cycle=None, results=None):
        # Your computation here
        return {
            'data': {...},
            'metadata': {'title': '', 'x_label': '', 'y_label': ''},
            'coach_tip': ''
        }
```

### Step 2: Create Renderer
File: `rowing_catch/plots/myplot.py`
```python
from typing import Any
import streamlit as st
from rowing_catch.plots.theme import COLOR_MAIN
from rowing_catch.plots.utils import setup_premium_plot

def render_myplot(computed_data: dict[str, Any]):
    data = computed_data['data']
    metadata = computed_data['metadata']
    coach_tip = computed_data['coach_tip']
    
    fig, ax = setup_premium_plot(...)
    # Render to matplotlib
    st.pyplot(fig)
    st.info(coach_tip)
```

### Step 3: Register Transform
Edit `rowing_catch/plot_transforms/registry.py`:
```python
from rowing_catch.plot_transforms.myplot import MyPlotComponent

_PLOT_COMPONENTS = {
    'myplot': MyPlotComponent(),
    # ... other plots
}
```

### Step 4: Export Renderer
Edit `rowing_catch/plots/__init__.py`:
```python
from rowing_catch.plots.myplot import render_myplot

__all__ = ['render_myplot', ...]
```

### Step 5: Use in Page
```python
from rowing_catch.plot_transforms import get_plot_component
from rowing_catch.plots.myplot import render_myplot

component = get_plot_component('myplot')
computed = component.compute(avg_cycle, catch_idx, finish_idx, ...)
render_myplot(computed)
```

## Code Quality Standards

### Type Checking (Mypy)
- All functions must have type annotations
- Use `pd.DataFrame | None` for optional DataFrames
- Use `dict[str, Any]` for flexible dictionaries
- Use `cast()` from typing for pandas scalar narrowing
- Run: `python -m mypy rowing_catch/`

### Linting (Ruff)
- No trailing whitespace in docstrings (W293)
- No unused variables (F841)
- Follow PEP 8 naming conventions
- Run: `ruff check .`

### Pre-Commit
- All checks must pass before committing
- Run: `pre-commit run --all-files`

### Testing
- Add tests in `tests/algo/` for core algorithms
- Add transform tests if needed
- Test-driven development encouraged
- Run: `python -m pytest tests/ -v`

## File Organization

```
rowing_catch/
├── algo/              ← Core algorithms (Layer 1)
│   ├── steps/         ← Data validation & transformation
│   ├── analysis.py    ← Main computation functions
│   ├── constants.py   ← Magic numbers & thresholds
│   └── helpers.py     ← Utility functions
├── scenario/          ← Synthetic data (Layer 1)
│   └── scenarios.py   ← Scenario generators
├── plot_transforms/   ← Plot computation (Layer 2)
│   ├── base.py        ← Abstract PlotComponent class
│   ├── registry.py    ← Transform discovery
│   ├── velocity.py    ← VelocityCoordinationComponent
│   ├── trajectory.py  ← HandleTrajectoryComponent
│   ├── rhythm.py      ← ConsistencyRhythmComponent
│   ├── trunk_angle.py ← TrunkAngleComponent
│   └── __init__.py    ← Public exports
├── plots/             ← Visualization renderers (Layer 3)
│   ├── theme.py       ← Color & style constants
│   ├── utils.py       ← setup_premium_plot(), helpers
│   ├── velocity.py    ← render_velocity_coordination()
│   ├── trajectory.py  ← render_handle_trajectory()
│   ├── rhythm.py      ← render_consistency_rhythm()
│   ├── trunk_angle.py ← render_trunk_angle_with_stage_stickfigures()
│   └── __init__.py    ← Public exports
└── ui/                ← Deprecated (keep if needed for backward compat)
    ├── annotations.py
    ├── components.py  ← Old; use rowing_catch/plot_transforms instead
    └── utils.py
```

## Naming Conventions

### Transforms
- Class name: `{Feature}Component` (e.g., `VelocityCoordinationComponent`)
- File name: `snake_case` matching feature (e.g., `velocity.py`)
- Method: `compute()` always

### Renderers
- Function name: `render_{feature}()` (e.g., `render_velocity_coordination()`)
- File name: `snake_case` matching feature (e.g., `velocity.py`)
- Accept parameter: `computed_data: dict[str, Any]`

### Pages
- File name: `{number}_{Feature}.py` (e.g., `1_Trunk_Angle.py`)
- Keep logic minimal, delegate to transforms and renderers

## Performance & Scalability

- **Lazy Loading**: Plots computed only when transform instantiated
- **Registry Pattern**: Fast lookup of available plots via `get_plot_component()`
- **Data Reuse**: Same computed dict can be rendered multiple times (ghost lines, comparisons)
- **Caching**: Leverage Streamlit's `@st.cache_data` for expensive computations

## Documentation

- Each transform must have a `description` property explaining what it visualizes
- Each renderer should document what keys it expects in `computed_data['data']`
- Use docstrings (Google style) with Args and Returns sections
- Keep README.md synchronized with architecture changes

## Migration Path

Old pattern (do not use):
```python
# ❌ Old: Computation + rendering mixed
plot_trunk_angle_with_stage_stickfigures(avg_cycle, catch_idx, finish_idx, results)
```

New pattern (use this):
```python
# ✅ New: Separated layers
component = get_plot_component('trunk_angle')
computed = component.compute(avg_cycle, catch_idx, finish_idx, results=results)
render_trunk_angle_with_stage_stickfigures(computed)
```

## Violations & Maintenance

- **Code Review Checklist**:
  - Does new plot follow transform/renderer pattern?
  - Are imports consistent with dependency rules?
  - Do all functions have type annotations?
  - Do new transforms have meaningful coach_tip?
  - Is new code tested?

- **Refactoring Signals**:
  - If `rowing_catch/ui/` functions are still used → migrate to transforms/plots
  - If transforms exceed 200 lines → split into smaller transforms
  - If pages exceed 50 lines → extract orchestration to helper functions
