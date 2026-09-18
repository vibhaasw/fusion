# Technical Report
## Parametric Adjustable Roller Conveyor Configuration Generator

**Project:** Autodesk Fusion × Standards Industry Hackathon — Problem Statement A  
**Version:** 1.0  
**Date:** September 2026  
**Team:** Vibhaas W  
**Language:** Python 3.8+  
**Primary Tool:** Autodesk Fusion 360 SDK (Python API)

---

## 1. Executive Summary

### 1.1 Problem

Manual CAD modeling of roller conveyor systems is time-consuming, error-prone, and requires repeated manual adjustments when configurations change. Each new conveyor size means re-sketching, re-dimensioning, and re-positioning every component by hand.

### 1.2 Solution

A Python-based automation tool for Autodesk Fusion 360 that generates complete, parametric roller conveyor assemblies from 8 user-specified input parameters. Users provide a configuration (either via JSON file or CLI) and the tool produces:

- A complete Fusion 360 assembly (`.f3d`) with frame, rollers, support legs, and optional side guards
- A bill of materials in both CSV and JSON formats
- Fully parametric geometry — changing any parameter in Fusion's UI updates all dependent components automatically

### 1.3 Key Results

| Metric | Result |
|--------|--------|
| Configurations generated | 3 (small, medium, large) |
| Test coverage | 100+ unit tests, all passing |
| Parametric | Yes — all dimensions linked to Fusion Parameters |
| BOM formats | CSV + JSON |
| Code quality | PEP 8, full docstrings, type hints |

---

## 2. Parameter Specifications

The tool accepts exactly 8 parameters. All are required; no defaults are provided.

| Parameter | Symbol | Min | Max | Unit | Description |
|-----------|--------|-----|-----|------|-------------|
| Conveyor Length | L | 800 | 2000 | mm | Total length end-to-end |
| Conveyor Width | W | 300 | 600 | mm | Width of bed surface |
| Frame Height | H | 500 | 900 | mm | Floor to conveyor bed |
| Roller Diameter | D | 40 | 80 | mm | Roller outside diameter |
| Roller Spacing | P | 80 | 150 | mm | Center-to-center spacing |
| Support Leg Spacing | S | 500 | 1000 | mm | Spacing between support pairs |
| Side Guard Height | G | 0 | 150 | mm | Height of guard panels |
| Include Side Guards | side_guards | — | — | bool | True = 2 guards, False = none |

### 2.1 Validation Rules

**Range checks:** Each numeric parameter must fall within its min/max. Rejection: `"Parameter {name} value {value} exceeds range [{min}, {max}]"`.

**Logical constraints:**
1. **Roller fit:** `L - 100 ≥ 2 × P` (50mm margin on each end, room for ≥ 2 rollers)
2. **Support fit:** `S ≤ L - 100`
3. **Guard logic:** If `side_guards == True`, then `G > 0`; if `False`, `G` is ignored

---

## 3. Geometry Algorithms

### 3.1 Roller Positioning

```
margin = 50  (mm from each conveyor end to first/last roller)
available_length = L - 2 * margin
roller_count = floor(available_length / P) + 1

positions = []
for i in range(roller_count):
    position_x = margin + i * P
    positions.append(position_x)
```

**Example:** L=1200, P=100  
available = 1100, count = floor(1100/100)+1 = 12  
positions = [50, 150, 250, 350, 450, 550, 650, 750, 850, 950, 1050, 1150]

### 3.2 Support Leg Positioning

Identical algorithm using support spacing S instead of P.

```
support_count = floor((L - 100) / S) + 1
positions = [50 + i * S for i in range(support_count)]
```

**Example:** L=1200, S=600  
available = 1100, count = floor(1100/600)+1 = 2  
positions = [50, 650]

### 3.3 Parametric Linking Strategy

Each input parameter becomes a Fusion Parameter object. When creating sketch geometry, dimensions are linked to these parameters via expressions:

- Frame rectangle: sketch lines linked to `L` and `W` parameters
- Extrusion height: linked to `H` parameter
- Roller circle radius: `D/2` expression
- Roller extrusion: `W` parameter (along Y-axis)
- Support leg extrusion: `H` parameter
- Guard panel: `L` and `G` parameters

This ensures that changing any parameter in Fusion's UI automatically updates all dependent geometry — no manual re-dimensioning needed.

---

## 4. Implementation Details

### 4.1 Module Architecture

```
fusion-conveyor-generator/
├── src/
│   ├── config_validator.py      # Input validation & parameter packaging
│   ├── geometry_calculator.py   # Roller/support positioning math
│   ├── fusion_generator.py      # Fusion API integration (CAD generation)
│   ├── bom_generator.py         # BOM extraction & CSV/JSON export
│   └── ui_handler.py            # CLI interface (--config, --help)
├── tests/                        # 100+ unit tests
├── configs/                      # Small/medium/large JSON presets
├── outputs/                      # Generated .f3d + BOM files
├── main.py                       # CLI entry point
└── generate_all_configs.py      # Batch BOM generation script
```

### 4.2 Data Flow

```
User Input (JSON/CLI)
       ↓
config_validator.ConveyorConfig  — validates ranges + logical constraints
       ↓
geometry_calculator.calculate_geometry — computes counts & positions
       ↓
fusion_generator.create_assembly — creates Fusion document + all components
       ↓
bom_generator.save_all_bom_formats — exports CSV + JSON BOM
       ↓
Output Files (.f3d + bom_*.csv + bom_*.json)
```

### 4.3 Fusion Assembly Manager

`FusionAssemblyManager` (in `fusion_generator.py`) orchestrates all Fusion API operations:

| Method | Responsibility |
|--------|---------------|
| `create_document(name)` | Creates new Fusion design document |
| `create_parameters(config)` | Creates Fusion Parameter objects for L, W, H, D, P, S, G |
| `generate_frame(config)` | Skecthes rectangle (L×W) on XY plane, extrudes by H |
| `generate_rollers(positions, D, W)` | Creates cylinder at each position, extrudes along Y |
| `generate_supports(positions, H)` | Creates 40×40mm box at each position, extrudes by H |
| `generate_guards(L, G, W, include)` | Creates L×G×5mm panels at ±W/2 if enabled |
| `cleanup_stale_components(...)` | Deletes excess components when counts decrease |
| `save_document(filepath)` | Saves to .f3d |

### 4.4 Parametric Design Decisions

| Component | Parametric | Fixed |
|-----------|-----------|-------|
| Frame (L×W×H) | L, W, H | — |
| Rollers (cylinders) | D, W (length along Y) | Position (calculated) |
| Support legs (boxes) | H | 40×40 cross-section |
| Side guards (panels) | L, G | 5mm thickness |

All components use calculated positions, not hardcoded layouts. Roller and support counts are dynamically computed from L, P, S — not fixed at 8 or 12.

---

## 5. Validation & Testing

### 5.1 Unit Tests

| Module | Tests | Focus |
|--------|-------|-------|
| `config_validator` | 28 | Range boundaries, missing keys, type errors, logical constraints |
| `geometry_calculator` | 34 | Roller/support counts, positions, spacing, bounds, determinism |
| `bom_generator` | 18 | BOM structure, CSV/JSON export, verification against config |
| `fusion_generator` | 10 | Module import, constants, naming conventions, file naming, test config |
| `integration` | 12+ | Full pipeline for all 3 configs + differentiation checks |

**Total:** 100+ tests, all passing. No external Fusion runtime required for the validator, calculator, BOM, and integration tests.

### 5.2 Test Configs

| Config | L | W | H | D | P | S | G | Guards | Total Components |
|--------|---|---|---|---|---|---|---|--------|-----------------|
| Small | 800 | 300 | 500 | 40 | 100 | 500 | 0 | No | 11 |
| Medium | 1200 | 450 | 700 | 50 | 100 | 600 | 80 | Yes (2) | 17 |
| Large | 1800 | 550 | 900 | 60 | 120 | 700 | 150 | Yes (2) | 21 |

### 5.3 Integration Tests

The `test_integration.py` module validates the full pipeline for each config:
1. Config validation passes
2. Geometry calculation produces correct counts and positions
3. BOM generation produces correct component counts
4. BOM export to CSV and JSON succeeds with correct content
5. The three configs are substantially different from each other (different roller counts, support counts, guard presence)

---

## 6. Results

### 6.1 Configuration 1: Small / Compact

| Parameter | Value |
|-----------|-------|
| L | 800 mm |
| W | 300 mm |
| H | 500 mm |
| D | 40 mm |
| P | 100 mm |
| S | 500 mm |
| G | 0 mm |
| Side guards | No |

**Component counts:**
- Frame: 1
- Rollers: 8 (positions: 50, 150, 250, 350, 450, 550, 650, 750)
- Support legs: 2 (positions: 50, 550)
- Side guards: 0
- **Total: 11**

### 6.2 Configuration 2: Medium / Standard

| Parameter | Value |
|-----------|-------|
| L | 1200 mm |
| W | 450 mm |
| H | 700 mm |
| D | 50 mm |
| P | 100 mm |
| S | 600 mm |
| G | 80 mm |
| Side guards | Yes |

**Component counts:**
- Frame: 1
- Rollers: 12 (positions: 50 to 1150, 100mm spacing)
- Support legs: 2 (positions: 50, 650)
- Side guards: 2 (Left at Y=-225, Right at Y=+225)
- **Total: 17**

### 6.3 Configuration 3: Large / Tall

| Parameter | Value |
|-----------|-------|
| L | 1800 mm |
| W | 550 mm |
| H | 900 mm |
| D | 60 mm |
| P | 120 mm |
| S | 700 mm |
| G | 150 mm |
| Side guards | Yes |

**Component counts:**
- Frame: 1
- Rollers: 15 (positions: 50 to 1730, 120mm spacing)
- Support legs: 3 (positions: 50, 750, 1450)
- Side guards: 2 (Left at Y=-275, Right at Y=+275)
- **Total: 21**

---

## 7. Assumptions & Limitations

### 7.1 Design Assumptions

- **Margin = 50mm:** 50mm from each conveyor end to the first/last roller and support. This is a design choice balancing structural stability with space efficiency.
- **Support leg cross-section = 40×40mm:** Fixed for simplicity. Not parametric.
- **Guard thickness = 5mm:** Fixed. Not parametric.
- **Rollers run parallel to conveyor width (Y-axis):** Standard industrial roller conveyor orientation.
- **All components are solid bodies:** No thin-walled frame or shell features.

### 7.2 Limitations

- **Fusion API required for assembly generation:** The `fusion_generator.py` module must run inside Fusion 360's Python environment. The CLI and BOM generation work standalone.
- **No material assignment:** Components are created as generic solid bodies; material selection is left to the user in Fusion.
- **No joint creation in current implementation:** Roller shafts would benefit from revolute joints for rotation. This is identified as a Phase 3 feature that can be added.
- **No CAM or manufacturing outputs:** Tool creates geometry only, no toolpaths or drawings.
- **Single conveyor configuration per document:** Each .f3d contains one conveyor assembly.
- **No cloud or collaboration features:** Documents are local .f3d files.

### 7.3 Future Improvements

- Add revolute joints for roller rotation
- Add material selection and mass properties
- Support multiple conveyor segments in one assembly
- Export to STEP/IGES for interoperability
- Add structural analysis hooks (FEA readiness)
- Add motion simulation for conveyor speed and throughput
- Web UI for configuration input

---

## 8. Conclusion

The Parametric Adjustable Roller Conveyor Configuration Generator successfully meets all hackathon requirements:

1. ✓ Generates 3 substantially different conveyor configurations
2. ✓ All models are fully parametric — no hard-coded geometry
3. ✓ Fusion API is the primary tool
4. ✓ Complete, well-tested Python source code
5. ✓ BOMs exported in both CSV and JSON formats
6. ✓ Technical documentation complete

The tool eliminates manual CAD modeling effort for conveyor design. A manufacturing engineer can specify any valid configuration in seconds and receive a complete, parametric Fusion assembly ready for further design work.

**Code repository:** `https://github.com/vibhaasw/fusion`
