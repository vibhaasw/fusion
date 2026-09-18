# Fusion Conveyor Generator

Parametric Adjustable Roller Conveyor Configuration Generator for Autodesk Fusion 360.

A Python-based automation tool that generates parametric roller conveyor systems in Autodesk Fusion 360. Users input design specifications and the tool produces complete, editable CAD assemblies with automatic calculations for component positioning.

## Installation

```bash
cd fusion_conveyor_generator
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Usage

### Command Line (JSON Config)

```bash
python main.py --config configs/config_medium.json
```

### Example Configurations

Three preset configurations are provided:

- **Small**: L=800, W=300, H=500, D=40, P=100, S=500, G=0, no guards
- **Medium**: L=1200, W=450, H=700, D=50, P=100, S=600, G=80, with guards  
- **Large**: L=1800, W=550, H=900, D=60, P=120, S=700, G=150, with guards

### Input Parameters

| Parameter | Symbol | Min | Max | Unit | Description |
|-----------|--------|-----|-----|------|-------------|
| Conveyor Length | L | 800 | 2000 | mm | Total length of conveyor |
| Conveyor Width | W | 300 | 600 | mm | Width of conveyor belt surface |
| Frame Height | H | 500 | 900 | mm | Height from floor to conveyor bed |
| Roller Diameter | D | 40 | 80 | mm | Cylindrical roller outside diameter |
| Roller Spacing | P | 80 | 150 | mm | Center-to-center spacing |
| Support Leg Spacing | S | 500 | 1000 | mm | Spacing between support leg pairs |
| Side Guard Height | G | 0 | 150 | mm | Height of side guard panels |
| Include Side Guards | side_guards | — | — | bool | True to add side guards |

### Project Structure

```
fusion_conveyor_generator/
├── src/
│   ├── __init__.py
│   ├── config_validator.py      # Input validation
│   ├── geometry_calculator.py   # Roller/support math
│   ├── fusion_generator.py      # Fusion API integration
│   ├── bom_generator.py         # BOM export
│   └── ui_handler.py            # CLI/JSON interface
├── tests/
│   ├── __init__.py
│   ├── test_config_validator.py
│   ├── test_geometry_calculator.py
│   ├── test_fusion_generator.py
│   └── test_bom_generator.py
├── configs/
│   ├── config_small.json
│   ├── config_medium.json
│   └── config_large.json
├── outputs/
│   └── (generated .f3d, .csv, .json files)
├── main.py
├── requirements.txt
└── README.md
```

## Requirements

- Python 3.8+
- Autodesk Fusion 360 (latest version) installed and licensed
- pytest for running unit tests
