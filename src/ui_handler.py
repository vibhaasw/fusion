"""User interface handler for conveyor configuration.

Handles loading configurations from JSON files, CLI arguments,
saving configurations, and displaying generation results.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional


def load_config_from_json(filepath: str) -> Dict[str, Any]:
    """Load configuration from JSON file.

    Args:
        filepath: Path to JSON config file.

    Returns:
        Configuration dictionary.

    Raises:
        FileNotFoundError: If file not found.
        json.JSONDecodeError: If invalid JSON.
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {filepath}")

    with open(path) as f:
        config = json.load(f)

    return config


def load_config_from_cli_args(args: argparse.Namespace) -> Dict[str, Any]:
    """Load configuration from command-line arguments.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Configuration dictionary.
    """
    config: Dict[str, Any] = {
        "L": float(args.length),
        "W": float(args.width),
        "H": float(args.height),
        "D": float(args.diameter),
        "P": float(args.roller_spacing),
        "S": float(args.support_spacing),
        "G": float(args.guard_height),
        "side_guards": args.side_guards,
    }
    return config


def save_config_to_json(
    config: Dict[str, Any], filepath: str
) -> None:
    """Save configuration to JSON file.

    Args:
        config: Configuration dictionary.
        filepath: Path to output JSON file.
    """
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w") as f:
        json.dump(config, f, indent=2)


def display_results(
    config: Dict[str, Any],
    roller_count: int,
    support_count: int,
    guard_count: int,
    output_files: list[str],
) -> None:
    """Display summary of generated assembly to user.

    Args:
        config: Configuration used.
        roller_count: Number of rollers generated.
        support_count: Number of support legs generated.
        guard_count: Number of side guards generated.
        output_files: List of generated file paths.
    """
    L = config.get("L", 0)
    W = config.get("W", 0)
    H = config.get("H", 0)
    D = config.get("D", 0)
    P = config.get("P", 0)
    S = config.get("S", 0)
    G = config.get("G", 0)
    guards = config.get("side_guards", False)

    total = 1 + roller_count + support_count + guard_count

    print("\n" + "=" * 60)
    print("  CONVEYOR CONFIGURATION GENERATED")
    print("=" * 60)
    print(f"  Conveyor Length:      {L} mm")
    print(f"  Conveyor Width:       {W} mm")
    print(f"  Frame Height:         {H} mm")
    print(f"  Roller Diameter:      {D} mm")
    print(f"  Roller Spacing:       {P} mm")
    print(f"  Support Spacing:      {S} mm")
    print(f"  Guard Height:         {G} mm")
    print(f"  Side Guards:          {'Yes' if guards else 'No'}")
    print("-" * 60)
    print(f"  Frame:                1")
    print(f"  Rollers:              {roller_count}")
    print(f"  Support Legs:         {support_count}")
    print(f"  Side Guards:          {guard_count}")
    print(f"  TOTAL COMPONENTS:     {total}")
    print("=" * 60)
    print("\n  Generated Files:")
    for f in output_files:
        print(f"    - {f}")
    print()


def display_error(error: Exception) -> None:
    """Display error message to user.

    Args:
        error: Exception to display.
    """
    print(f"\n  ERROR: {error}", file=sys.stderr)
    print()


def print_config_info(config: Dict[str, Any]) -> None:
    """Print configuration parameters in readable format.

    Args:
        config: Configuration dictionary.
    """
    print("\n  Configuration Parameters:")
    print(f"    L (Length):         {config.get('L', 'N/A')} mm")
    print(f"    W (Width):          {config.get('W', 'N/A')} mm")
    print(f"    H (Height):         {config.get('H', 'N/A')} mm")
    print(f"    D (Roller Dia):     {config.get('D', 'N/A')} mm")
    print(f"    P (Roller Spacing): {config.get('P', 'N/A')} mm")
    print(f"    S (Support Spacing):{config.get('S', 'N/A')} mm")
    print(f"    G (Guard Height):   {config.get('G', 'N/A')} mm")
    print(f"    side_guards:        {config.get('side_guards', 'N/A')}")
    print()


def main() -> int:
    """CLI entry point for conveyor generator.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    parser = argparse.ArgumentParser(
        description="Generate parametric roller conveyor assemblies for Fusion 360"
    )
    parser.add_argument(
        "--config",
        "-c",
        type=str,
        help="Path to JSON configuration file",
    )
    parser.add_argument("--length", "-L", type=float, default=1200)
    parser.add_argument("--width", "-W", type=float, default=450)
    parser.add_argument("--height", "-H", type=float, default=700)
    parser.add_argument("--diameter", "-D", type=float, default=50)
    parser.add_argument("--roller-spacing", "-P", type=float, default=100)
    parser.add_argument("--support-spacing", "-S", type=float, default=600)
    parser.add_argument("--guard-height", "-G", type=float, default=80)
    parser.add_argument(
        "--side-guards",
        action="store_true",
        default=False,
        help="Include side guard panels",
    )
    parser.add_argument(
        "--output-dir",
        "-o",
        type=str,
        default="outputs",
        help="Output directory for generated files",
    )
    parser.add_argument(
        "--save-config",
        "-s",
        type=str,
        help="Save configuration to JSON file",
    )

    args = parser.parse_args()

    try:
        if args.config:
            config = load_config_from_json(args.config)
        else:
            config = load_config_from_cli_args(args)

        if args.save_config:
            save_config_to_json(config, args.save_config)
            print(f"Configuration saved to: {args.save_config}")

        print_config_info(config)
        print("  (Fusion 360 required for actual assembly generation)")
        print()

        # NOTE: Actual Fusion generation requires Fusion API (adsk) which
        # runs inside Fusion 360's Python environment. This CLI validates
        # and previews the configuration; the fusion_generator module
        # is used from within Fusion's script environment.
        return 0

    except (FileNotFoundError, json.JSONDecodeError, ValueError) as e:
        display_error(e)
        return 1
    except Exception as e:
        display_error(e)
        return 1


if __name__ == "__main__":
    sys.exit(main())
