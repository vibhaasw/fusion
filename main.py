#!/usr/bin/env python3
"""Entry point for the Fusion Conveyor Generator.

Usage:
    python main.py --config configs/config_medium.json
    python main.py -L 1200 -W 450 -H 700 -D 50 -P 100 -S 600 -G 80 --side-guards
    python main.py --config configs/config_small.json --save-config my_config.json

Note: Actual Fusion 360 assembly generation requires running this tool
inside Fusion 360's Python environment (via Fusion's script/run dialog).
This CLI validates configurations and previews parameters.
For full generation, use the Fusion API directly from within Fusion 360.
"""

import sys

from src.ui_handler import main

if __name__ == "__main__":
    sys.exit(main())
