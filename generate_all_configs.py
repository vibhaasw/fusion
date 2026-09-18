#!/usr/bin/env python3
"""Generate BOMs for all three standard conveyor configurations.

Runs the full pipeline (validate → calculate → BOM) without requiring
Fusion 360. Produces CSV + JSON BOM files for each config in the outputs/
directory. Fusion .f3d generation requires running inside Fusion.

Usage:
    python generate_all_configs.py

For Fusion assembly generation:
    1. Run fusion_hello.py first to verify API connectivity
    2. Then run this script inside Fusion's Python environment
       (Fusion adds src/ to sys.path automatically when used as a script)
"""

import os
import sys
from pathlib import Path

# Ensure src/ is on the path for direct imports
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from config_validator import ConveyorConfig
from geometry_calculator import calculate_geometry
from bom_generator import save_all_bom_formats


# ---------------------------------------------------------------------------
# Standard configurations (per PRD/TRD Section 7.1)
# ---------------------------------------------------------------------------

CONFIGS = {
    "small": {
        "L": 800,
        "W": 300,
        "H": 500,
        "D": 40,
        "P": 100,
        "S": 500,
        "G": 0,
        "side_guards": False,
    },
    "medium": {
        "L": 1200,
        "W": 450,
        "H": 700,
        "D": 50,
        "P": 100,
        "S": 600,
        "G": 80,
        "side_guards": True,
    },
    "large": {
        "L": 1800,
        "W": 550,
        "H": 900,
        "D": 60,
        "P": 120,
        "S": 700,
        "G": 150,
        "side_guards": True,
    },
}


def generate_config(name: str, config_dict: dict) -> dict:
    """Validate, calculate, and generate BOM for one configuration.

    Args:
        name: Config name (small/medium/large).
        config_dict: Raw parameter dictionary.

    Returns:
        Dictionary with results summary.
    """
    print(f"\n{'=' * 60}")
    print(f"  Generating: {name.upper()} configuration")
    print(f"{'=' * 60}")

    # 1. Validate
    print("  Step 1: Validating parameters...")
    config = ConveyorConfig(config_dict)
    config.validate()
    print(f"    L={config.L}, W={config.W}, H={config.H}")
    print(f"    D={config.D}, P={config.P}, S={config.S}, G={config.G}")
    print(f"    Side guards: {'Yes' if config.include_side_guards else 'No'}")

    # 2. Calculate geometry
    print("  Step 2: Calculating geometry...")
    geo = calculate_geometry(config.L, config.P, config.S)
    print(f"    Rollers: {geo.roller_count} "
          f"(positions: {geo.roller_positions[:3]}...{geo.roller_positions[-3:]})")
    print(f"    Supports: {geo.support_count} "
          f"(positions: {geo.support_positions})")
    guard_count = 2 if config.include_side_guards else 0
    print(f"    Guards: {guard_count}")

    # 3. Generate BOM
    print("  Step 3: Generating BOM...")
    output_dir = Path(__file__).resolve().parent / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)

    csv_path, json_path = save_all_bom_formats(
        config.to_dict(),
        geo.roller_count,
        geo.support_count,
        guard_count,
        str(output_dir),
    )
    print(f"    CSV:  {csv_path}")
    print(f"    JSON: {json_path}")

    total = 1 + geo.roller_count + geo.support_count + guard_count

    return {
        "name": name,
        "config": config.to_dict(),
        "roller_count": geo.roller_count,
        "support_count": geo.support_count,
        "guard_count": guard_count,
        "total_components": total,
        "bom_csv": str(csv_path),
        "bom_json": str(json_path),
        "fusion_f3d": None,  # Set when running inside Fusion
    }


def main() -> int:
    """Generate all three configs and print a summary report."""
    print("=" * 60)
    print("  Fusion Conveyor Generator")
    print("  All-Configurations BOM Generator")
    print("=" * 60)

    results = []
    for name, config_dict in CONFIGS.items():
        try:
            result = generate_config(name, config_dict)
            results.append(result)
        except Exception as e:
            print(f"  ERROR generating {name}: {e}")
            import traceback
            traceback.print_exc()
            results.append({"name": name, "error": str(e)})

    # Summary table
    print(f"\n{'=' * 60}")
    print(f"  GENERATION SUMMARY")
    print(f"{'=' * 60}")
    print(f"  {'Config':<10} {'L':<6} {'W':<6} {'H':<6} "
          f"{'#Roller':<8} {'#Support':<9} {'#Guard':<7} {'Total':<6}")
    print(f"  {'-'*10} {'-'*6} {'-'*6} {'-'*6} "
          f"{'-'*8} {'-'*9} {'-'*7} {'-'*6}")

    for r in results:
        if "error" in r:
            print(f"  {r['name']:<10} FAILED: {r['error']}")
            continue
        c = r["config"]
        print(f"  {r['name']:<10} {c['L']:<6} {c['W']:<6} {c['H']:<6} "
              f"{r['roller_count']:<8} {r['support_count']:<9} "
              f"{r['guard_count']:<7} {r['total_components']:<6}")

    print(f"\n  All BOM files saved to: {Path(__file__).resolve().parent / 'outputs'}")

    if not any("fusion_f3d" in r and r.get("fusion_f3d") for r in results):
        print("\n  NOTE: .f3d Fusion files require running inside Fusion 360.")
        print("  To generate assemblies:")
        print("    1. Open Fusion 360")
        print("    2. Run: python generate_all_configs.py (inside Fusion)")
        print("    OR use the Fusion Scripts & Add-ins dialog")

    print(f"\n{'=' * 60}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
