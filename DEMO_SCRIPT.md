# Demo Script — Fusion Conveyor Generator

Duration target: 5-7 minutes. Show each major feature with live interaction where possible.

=============================================================================
PREPARATION
=============================================================================
1. Open Fusion 360
2. Open terminal / Scripts & Add-ins
3. Have these ready:
   - configs/config_small.json
   - configs/config_medium.json
   - configs/config_large.json
   - generate_all_configs.py (run inside Fusion to produce .f3d files)
   - TESTED .f3d files in outputs/ (pre-generate if demo time is tight)

=============================================================================
SEGMENT 1: INTRODUCTION (30 seconds)
=============================================================================
Show: Project README or terminal
Say: "This tool automates parametric roller conveyor design in Fusion 360.
      You specify 8 parameters — length, width, height, roller diameter,
      spacing, support spacing, guard height, and whether guards are included —
      and the tool generates a complete, editable CAD assembly."

=============================================================================
SEGMENT 2: CONFIGURATION INPUT (1 minute)
=============================================================================
Show: config_medium.json in a text editor or via CLI

Option A — CLI:
  python main.py --config configs/config_medium.json

Option B — Python console in Fusion:
  import sys; sys.path.append(r"path/to/src")
  from config_validator import ConveyorConfig
  from geometry_calculator import calculate_geometry
  config = ConveyorConfig({"L":1200,"W":450,"H":700,"D":50,"P":100,"S":600,"G":80,"side_guards":True})
  geo = calculate_geometry(config.L, config.P, config.S)
  print(f"Rollers: {geo.roller_count}, Supports: {geo.support_count}")

Point out:
  - 8 parameters, all required
  - Clear min/max ranges (L: 800-2000mm, D: 40-80mm, etc.)
  - Validation happens before Fusion generation

=============================================================================
SEGMENT 3: GENERATE ASSEMBLY (1-2 minutes)
=============================================================================
Show: Fusion 360 with the generated assembly open

If pre-generated .f3d files exist:
  - Open outputs/conveyor_1200x450x700_50D_100P.f3d

If generating live:
  - Run generate_all_configs.py inside Fusion
  - Watch the assembly appear

Point out in the Fusion Model Tree:
  - Frame (1 body)
  - Roller_1 through Roller_N (cylindrical bodies)
  - Leg_1 through Leg_M (vertical boxes)
  - SideGuard_Left, SideGuard_Right (panels, if guards enabled)
  - Parameters folder — shows L, W, H, D, P, S, G as Fusion Parameters

=============================================================================
SEGMENT 4: PARAMETRIC UPDATE DEMO (1.5 minutes) — KEY MOMENT
=============================================================================
This is the most important part — demonstrate that changing a parameter
updates all geometry automatically.

Action 1: Change L from 1200 to 1400
  - In Fusion UI: Change Parameters → L: 1200 → 1400
  - Observe: Frame extends, roller count may increase, support positions update
  - Say: "The frame grows, rollers reposition, supports stay valid — all parametric."

Action 2: Change P from 100 to 120
  - Change Parameters → P: 100 → 120
  - Observe: Roller count decreases, positions update
  - Say: "Fewer rollers, wider spacing — calculated automatically."

Action 3: Change H from 700 to 800
  - Change Parameters → H: 700 → 800
  - Observe: Frame and support legs grow taller
  - Say: "Frame and legs both update. No manual re-dimensioning."

Action 4: Toggle side_guards from True to False
  - Change Parameters → G: 80 → 0 (or disable guards)
  - Observe: Guards disappear from assembly
  - Say: "Optional features can be toggled off parametrically."

=============================================================================
SEGMENT 5: BOM DEMONSTRATION (30 seconds)
=============================================================================
Show: outputs/ directory with CSV and JSON files

  - conveyor_1200x450x700_50D_100P_bom.csv
  - conveyor_1200x450x700_50D_100P_bom.json

Open the CSV in a text editor or spreadsheet:
  Component_Type, Quantity, Diameter_or_Height_mm, Notes
  Frame, 1, —, Structural rectangular frame
  Roller, 12, 50, Cylindrical rollers at 100mm spacing
  Support_Leg, 2, 700, Vertical support legs at 600mm spacing
  Side_Guard, 2, 80, Optional side guard panels
  TOTAL, 17, —, Sum of all components

Say: "BOM is automatically generated — component counts, diameters, heights,
      all derived from the configuration. Available in CSV and JSON."

=============================================================================
SEGMENT 6: THREE CONFIGURATIONS SIDE BY SIDE (30 seconds)
=============================================================================
Show: Brief comparison of all three configs

  Small:  800×300×500, D=40, P=100, S=500, no guards → 11 components
  Medium: 1200×450×700, D=50, P=100, S=600, guards → 17 components
  Large:  1800×550×900, D=60, P=120, S=700, guards → 21 components

Say: "Three substantially different configurations, generated from changed
      parameters only. Each one is fully parametric."

=============================================================================
SEGMENT 7: CLOSE (15 seconds)
=============================================================================
Say: "The tool eliminates manual conveyor CAD work. Specify parameters,
      get a complete parametric assembly with BOM. Open source, ready for
      extension with joints, materials, and manufacturing outputs."

=============================================================================
BACKUP PLAN
=============================================================================
If Fusion isn't available during demo:
- Show the generated .f3d files' file sizes and timestamps as proof
- Run the CLI: python main.py --config configs/config_medium.json
- Show test results: python -m pytest tests/ -v --tb=short
- Show the geometry calculator output for each config
- Show the BOM files
- Walk through the technical report's results section
