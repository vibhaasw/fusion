# Fusion Conveyor Generator

Parametric Adjustable Roller Conveyor Configuration Generator for Autodesk Fusion 360.

A Python-based automation tool that generates parametric roller conveyor systems in Autodesk Fusion 360. Users input design specifications and the tool produces complete, editable CAD assemblies with automatic calculations for component positioning.

## Table of Contents

1. [Project Overview](#project-overview)
2. [Requirements](#requirements)
3. [Installation](#installation)
4. [Usage](#usage)
5. [Output](#output)
6. [Testing](#testing)
7. [Architecture](#architecture)
8. [Parameters Reference](#parameters-reference)
9. [Troubleshooting](#troubleshooting)
10. [Future Improvements](#future-improvements)

---

## Project Overview

### Problem Statement

Manual CAD modeling of roller conveyor systems is time-consuming, error-prone, and requires repeated manual adjustments for different configurations.

### Solution

A Python-based Fusion 360 automation tool that generates complete, parametric roller conveyor assemblies from 8 user-specified input parameters. Users provide a configuration (JSON file or CLI) and the tool produces:

- A complete Fusion 360 assembly (`.f3d`) with frame, rollers, support legs, and optional side guards
- A bill of materials in both CSV and JSON formats
- Fully parametric geometry — changing any parameter in Fusion's UI updates all dependent components automatically

### Key Features

- **8 input parameters** with range validation and logical constraints
- **3 preset configurations**: small (800mm), medium (1200mm), large (1800mm)
- **Dynamic component counts**: rollers and supports calculated from L, P, S — not hardcoded
- **Parametric modeling**: all dimensions linked to Fusion Parameters
- **BOM export**: CSV and JSON formats with component counts, diameters, and notes
- **119 unit tests**: config validator, geometry calculator, BOM generator, integration

### Deliverables

| Deliverable | Status |
|-------------|--------|
| Fusion API tool | ✓ (`fusion_generator.py`) |
| 3 parametric assemblies | ✓ (11, 17, 21 components) |
| BOM CSV + JSON | ✓ (all 3 configs) |
| Technical report | ✓ (`TECHNICAL_REPORT.md`) |
| Demo script | ✓ (`DEMO_SCRIPT.md`) |
| 119 unit tests | ✓ (all passing) |

---

## Requirements

- **Python 3.8+** (3.13 used in development)
- **Autodesk Fusion 360** (latest version) — required for `.f3d` assembly generation
- **pytest 7.0+** — for running unit tests

### Python Dependencies

```
pywin32>=306  # Windows only (Fusion API on Windows)
pytest>=7.0   # Testing
```

Note: The Fusion 360 API (`adsk.*` modules) is only available inside Fusion 360's embedded Python environment. The tool's non-Fusion modules (`config_validator.py`, `geometry_calculator.py`, `bom_generator.py`) use only Python stdlib.

---

## Installation

```bash
# Clone or navigate to the project
cd fusion_conveyor_generator

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Verify installation
python -m pytest tests/ -q
# Expected: 119 passed
```

### Fusion 360 Setup (for `.f3d` generation)

1. Install Autodesk Fusion 360
2. Fusion includes its own Python environment with `adsk.*` modules
3. To run scripts inside Fusion:
   - Open Fusion 360
   - Go to **Scripts & Add-ins**
   - Create a new script pointing to `generate_all_configs.py` or `fusion_hello.py`
   - Or paste Python code into Fusion's Python console

---

## Usage

### Command Line (JSON Config)

Preview a configuration without Fusion:

```bash
python main.py --config configs/config_medium.json
```

This validates the config, calculates geometry, and displays a summary. No `.f3d` file is created (Fusion required for that).

### Command Line (Direct Arguments)

```bash
python main.py -L 1200 -W 450 -H 700 -D 50 -P 100 -S 600 -G 80 --side-guards
```

### Batch BOM Generation (No Fusion Required)

Generate BOMs for all three standard configs:

```bash
python generate_all_configs.py
```

Output: CSV + JSON BOM files in `outputs/` for small, medium, and large configs.

### Fusion Assembly Generation (Requires Fusion 360)

**Option A — Batch generation (all 3 configs):**

1. Open Fusion 360
2. Run: `python generate_all_configs.py` (inside Fusion's Python environment)
3. Output: `outputs/conveyor_*.f3d` + BOM files

**Option B — Single config via Python console:**

```python
import sys
sys.path.append(r"path/to/fusion_conveyor_generator/src")
from fusion_generator import create_assembly, create_test_config
import adsk.core

app = adsk.core.Application.get()
config = create_test_config(
    length=1200, width=450, height=700,
    diameter=50, roller_spacing=100,
    support_spacing=600, guard_height=80,
    side_guards=True
)
doc = create_assembly(config, app)
print(f"Created: {doc.name}")
```

**Option C — Hello World test (verify API connectivity):**

```bash
# Run inside Fusion 360
python fusion_hello.py
# Creates /tmp/test_fusion_hello.f3d with a 10mm cube
```

### Saving Configurations

```bash
# Save current CLI config to JSON
python main.py -L 1000 -W 400 -H 600 -D 45 -P 90 -S 550 -G 50 --side-guards \
    -s my_config.json

# Later, reuse it
python main.py --config my_config.json
```

---

## Output

### Generated Files

| File | Description |
|------|-------------|
| `outputs/conveyor_{L}x{W}x{H}_{D}D_{P}P.f3d` | Fusion 360 assembly (requires Fusion) |
| `outputs/bom_conveyor_{L}x{W}x{H}_{D}D_{P}P.csv` | Bill of materials (CSV) |
| `outputs/bom_conveyor_{L}x{W}x{H}_{D}D_{P}P.json` | Bill of materials (JSON) |

### Example BOM (CSV)

```
Component_Type,Quantity,Diameter_or_Height_mm,Notes
Frame,1,—,Structural rectangular frame
Roller,12,50,Cylindrical rollers at 100mm spacing
Support_Leg,2,700,Vertical support legs at 600mm spacing
Side_Guard,2,80,Optional side guard panels
TOTAL,17,—,Sum of all components
```

### Example BOM (JSON)

```json
{
  "generated_at": "2026-09-18T11:05:00Z",
  "configuration": {
    "L": 1200, "W": 450, "H": 700,
    "D": 50, "P": 100, "S": 600, "G": 80,
    "side_guards": true
  },
  "bill_of_materials": {
    "frame": {"quantity": 1, "description": "Structural frame"},
    "rollers": {"quantity": 12, "diameter_mm": 50, "spacing_mm": 100},
    "support_legs": {"quantity": 2, "height_mm": 700, "spacing_mm": 600},
    "side_guards": {"quantity": 2, "height_mm": 80}
  },
  "summary": {
    "total_components": 17,
    "total_rollers": 12,
    "total_supports": 2,
    "total_guards": 2
  }
}
```

---

## Testing

### Run All Tests

```bash
python -m pytest tests/ -v
```

Expected: **119 passed**, 0 failures.

### Test Breakdown

| Test File | Tests | Purpose |
|-----------|-------|---------|
| `test_config_validator.py` | 28 | Range validation, logical constraints, ConveyorConfig class |
| `test_geometry_calculator.py` | 34 | Roller/support counts, positions, spacing, determinism |
| `test_bom_generator.py` | 18 | BOM structure, CSV/JSON export, verification |
| `test_fusion_generator.py` | 10 | Module structure, constants, naming conventions |
| `test_integration.py` | 12+ | Full pipeline across all 3 configs + differentiation |

### Run Specific Test Module

```bash
python -m pytest tests/test_geometry_calculator.py -v
python -m pytest tests/test_integration.py -v
```

### Coverage

Current coverage exceeds 85% across all modules. Run with:

```bash
python -m pytest tests/ --cov=src --cov-report=term-missing
```

---

## Architecture

### Module Structure

```
fusion_conveyor_generator/
├── src/
│   ├── __init__.py
│   ├── config_validator.py      # INPUT VALIDATION
│   │   ├── ConveyorConfig (class)
│   │   ├── validate_param()
│   │   ├── get_param_range()
│   │   └── validate_logical_constraints()
│   │
│   ├── geometry_calculator.py   # GEOMETRY CALCULATIONS
│   │   ├── calculate_roller_count()
│   │   ├── calculate_roller_positions()
│   │   ├── calculate_support_count()
│   │   ├── calculate_support_positions()
│   │   └── CalculatedGeometry (class)
│   │
│   ├── fusion_generator.py      # FUSION CAD GENERATION
│   │   ├── FusionAssemblyManager (class)
│   │   ├── create_assembly()
│   │   ├── create_parameters()
│   │   ├── generate_frame()
│   │   ├── generate_rollers()
│   │   ├── generate_supports()
│   │   ├── generate_guards()
│   │   └── cleanup_stale_components()
│   │
│   ├── bom_generator.py         # BILL OF MATERIALS
│   │   ├── BillOfMaterials (class)
│   │   ├── generate_bom()
│   │   ├── export_bom_csv()
│   │   ├── export_bom_json()
│   │   └── save_all_bom_formats()
│   │
│   └── ui_handler.py            # USER INTERFACE
│       ├── load_config_from_json()
│       ├── load_config_from_cli_args()
│       ├── save_config_to_json()
│       ├── display_results()
│       └── main() (CLI entry point)
│
├── tests/
│   ├── test_config_validator.py
│   ├── test_geometry_calculator.py
│   ├── test_bom_generator.py
│   ├── test_fusion_generator.py
│   └── test_integration.py
│
├── configs/
│   ├── config_small.json
│   ├── config_medium.json
│   └── config_large.json
│
├── outputs/
│   ├── .gitkeep
│   ├── bom_conveyor_*.csv       # Generated BOMs
│   └── bom_conveyor_*.json      # Generated BOMs
│
├── main.py                      # CLI entry point
├── generate_all_configs.py      # Batch BOM generation
├── fusion_hello.py              # Fusion API hello world
├── TECHNICAL_REPORT.md          # Technical documentation
├── DEMO_SCRIPT.md               # Live demo script
├── SUBMISSION_NOTES.txt         # Submission checklist
├── requirements.txt
├── setup.py
└── README.md
```

### Data Flow

```
User Input (JSON/CLI)
       ↓
[VALIDATE] — config_validator.ConveyorConfig
       ↓
[CALCULATE] — geometry_calculator.calculate_geometry
       ↓
[GENERATE FUSION ASSEMBLY] — fusion_generator.create_assembly (requires Fusion)
       ↓
[SAVE & EXPORT] — bom_generator.save_all_bom_formats
       ↓
Output Files (.f3d + bom_*.csv + bom_*.json)
```

### Interface Contract

`create_assembly()` in `fusion_generator.py` consumes a configuration dict with this exact shape (produced by `ConveyorConfig.to_dict()`):

```python
{
    "L": 1200,              # float — Conveyor length (mm),   range [800, 2000]
    "W": 450,               # float — Conveyor width (mm),    range [300, 600]
    "H": 700,               # float — Frame height (mm),      range [500, 900]
    "D": 50,                # float — Roller diameter (mm),   range [40, 80]
    "P": 100,               # float — Roller spacing (mm),    range [80, 150]
    "S": 600,               # float — Support spacing (mm),   range [500, 1000]
    "G": 80,                # float — Guard height (mm),      range [0, 150]
    "side_guards": True     # bool  — Include side guards
}
```

**Do NOT add, remove, or rename keys without coordinating across the team.** Code consuming this dict will break silently if the shape changes.

---

## Parameters Reference

All 8 parameters are required. No defaults.

| Parameter | Symbol | Min | Max | Unit | Description |
|-----------|--------|-----|-----|------|-------------|
| Conveyor Length | L | 800 | 2000 | mm | Total length of conveyor from end to end |
| Conveyor Width | W | 300 | 600 | mm | Width of conveyor belt surface |
| Frame Height | H | 500 | 900 | mm | Height from floor to conveyor bed |
| Roller Diameter | D | 40 | 80 | mm | Cylindrical roller outside diameter |
| Roller Spacing | P | 80 | 150 | mm | Center-to-center spacing between rollers |
| Support Leg Spacing | S | 500 | 1000 | mm | Spacing between support leg pairs along length |
| Side Guard Height | G | 0 | 150 | mm | Height of optional side guard panels |
| Include Side Guards | side_guards | — | — | bool | True to add side guards, False to omit |

### Validation Rules

1. **Range checks:** Each numeric parameter must fall within its min/max
2. **Roller fit:** `L - 100 ≥ 2 × P` (50mm margin on each end, room for at least 2 rollers)
3. **Support fit:** `S ≤ L - 100`
4. **Guard logic:** If `side_guards == True`, then `G > 0`; if `False`, `G` is ignored

### Preset Configurations

| Config | L | W | H | D | P | S | G | Guards | Rollers | Supports | Total |
|--------|---|---|---|---|---|---|---|--------|---------|----------|-------|
| Small | 800 | 300 | 500 | 40 | 100 | 500 | 0 | No | 8 | 2 | 11 |
| Medium | 1200 | 450 | 700 | 50 | 100 | 600 | 80 | Yes | 12 | 2 | 17 |
| Large | 1800 | 550 | 900 | 60 | 120 | 700 | 150 | Yes | 15 | 3 | 21 |

---

## Troubleshooting

### "Not running inside Fusion 360"

This message appears when running `fusion_generator.py` or `fusion_hello.py` from a standard Python interpreter. The `adsk.*` modules only exist inside Fusion 360's embedded Python.

**Fix:** Run the script inside Fusion 360 (Scripts & Add-ins, or Python console).

### "Config file not found"

```bash
python main.py --config configs/config_medium.json
# Check: does the file exist at that path?
ls configs/config_medium.json
```

### "Parameter X value Y exceeds range [min, max]"

The input value is outside the allowed range. Check the Parameters Reference table for valid ranges.

### "Conveyor length L too short for roller spacing P"

The conveyor is too short to fit at least 2 rollers with the given spacing.

**Fix:** Either decrease P (roller spacing) or increase L (conveyor length). Minimum L = `2 × P + 100`.

### "Support spacing S too large for conveyor length L"

Support legs won't fit with the given spacing.

**Fix:** Decrease S or increase L. Must have `S ≤ L - 100`.

### "Cannot have side guards with height G = 0"

`side_guards` is True but `G` is 0 or negative.

**Fix:** Set `G > 0` or set `side_guards = False`.

### Tests failing

```bash
# Run with verbose output to see which tests fail
python -m pytest tests/ -v --tb=long

# Run a single test module
python -m pytest tests/test_config_validator.py -v
```

### Fusion .f3d not generated

The `.f3d` generation requires Fusion 360. The CLI and BOM generation work standalone. To generate assemblies:

1. Open Fusion 360
2. Run `python generate_all_configs.py` inside Fusion's Python environment
3. Or use Fusion's Scripts & Add-ins to run `fusion_generator.py`

---

## Future Improvements

- **Revolute joints** for roller rotation (allow rollers to spin in Fusion)
- **Material selection** and mass properties
- **Multiple conveyor segments** in a single assembly
- **STEP/IGES export** for interoperability with other CAD tools
- **Structural analysis** hooks (FEA readiness)
- **Motion simulation** for conveyor speed and throughput
- **Web UI** for configuration input (Flask/FastAPI frontend)
- **Configuration versioning** and saved configuration library

---

## License

This project was created for the Autodesk Fusion × Standards Industry Hackathon.
