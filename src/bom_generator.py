"""Bill of Materials generator for conveyor assemblies.

Extracts component information from the assembly and exports
BOM in CSV and JSON formats per the TRD specifications.
"""

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


class BillOfMaterials:
    """Container for BOM information.

    Attributes:
        config: Original configuration dict.
        frame_count: Number of frame bodies (typically 1).
        roller_count: Number of roller bodies.
        support_count: Number of support leg bodies.
        guard_count: Number of side guard bodies (0 or 2).
    """

    def __init__(
        self,
        config: Dict[str, Any],
        frame_count: int = 1,
        roller_count: int = 0,
        support_count: int = 0,
        guard_count: int = 0,
    ) -> None:
        """Initialize BOM from component counts.

        Args:
            config: Configuration dictionary.
            frame_count: Number of frame components.
            roller_count: Number of roller components.
            support_count: Number of support leg components.
            guard_count: Number of side guard components.
        """
        self.config = config
        self.frame_count = frame_count
        self.roller_count = roller_count
        self.support_count = support_count
        self.guard_count = guard_count

    @property
    def total_components(self) -> int:
        """Total number of all components."""
        return (
            self.frame_count
            + self.roller_count
            + self.support_count
            + self.guard_count
        )

    def get_summary(self) -> Dict[str, Any]:
        """Get BOM as dictionary.

        Returns:
            Dictionary with configuration, BOM, and summary.
        """
        return {
            "generated_at": datetime.now(timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            ),
            "configuration": {
                "L": self.config.get("L", 0),
                "W": self.config.get("W", 0),
                "H": self.config.get("H", 0),
                "D": self.config.get("D", 0),
                "P": self.config.get("P", 0),
                "S": self.config.get("S", 0),
                "G": self.config.get("G", 0),
                "side_guards": self.config.get("side_guards", False),
            },
            "bill_of_materials": {
                "frame": {
                    "quantity": self.frame_count,
                    "description": "Structural frame",
                },
                "rollers": {
                    "quantity": self.roller_count,
                    "diameter_mm": self.config.get("D", 0),
                    "spacing_mm": self.config.get("P", 0),
                    "description": "Cylindrical rollers",
                },
                "support_legs": {
                    "quantity": self.support_count,
                    "height_mm": self.config.get("H", 0),
                    "spacing_mm": self.config.get("S", 0),
                    "description": "Vertical support legs",
                },
                "side_guards": {
                    "quantity": self.guard_count,
                    "height_mm": self.config.get("G", 0),
                    "description": "Optional side guards",
                },
            },
            "summary": {
                "total_components": self.total_components,
                "total_rollers": self.roller_count,
                "total_supports": self.support_count,
                "total_guards": self.guard_count,
            },
        }

    def export_csv(self, filepath: str) -> None:
        """Export BOM to CSV file.

        Args:
            filepath: Path to output CSV file.
        """
        summary = self.get_summary()
        config = summary["configuration"]
        bom = summary["bill_of_materials"]
        total = summary["summary"]["total_components"]

        with open(filepath, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "Component_Type",
                    "Quantity",
                    "Diameter_or_Height_mm",
                    "Notes",
                ]
            )
            writer.writerow(
                [
                    "Frame",
                    self.frame_count,
                    "-",
                    "Structural rectangular frame",
                ]
            )
            writer.writerow(
                [
                    "Roller",
                    self.roller_count,
                    config.get("D", 0),
                    f"Cylindrical rollers at {config.get('P', 0)}mm spacing",
                ]
            )
            writer.writerow(
                [
                    "Support_Leg",
                    self.support_count,
                    config.get("H", 0),
                    f"Vertical support legs at {config.get('S', 0)}mm spacing",
                ]
            )
            if self.guard_count > 0:
                writer.writerow(
                    [
                        "Side_Guard",
                        self.guard_count,
                        config.get("G", 0),
                        "Optional side guard panels",
                    ]
                )
            writer.writerow(
                [
                    "TOTAL",
                    total,
                    "-",
                    "Sum of all components",
                ]
            )

    def export_json(self, filepath: str) -> None:
        """Export BOM to JSON file.

        Args:
            filepath: Path to output JSON file.
        """
        summary = self.get_summary()
        with open(filepath, "w") as f:
            json.dump(summary, f, indent=2)

    def verify_against_config(self) -> bool:
        """Verify BOM matches expected counts from config.

        Returns:
            True if counts are consistent.
        """
        config = self.config
        L = config.get("L", 0)
        P = config.get("P", 0)
        S = config.get("S", 0)

        # Expected roller count
        available = L - 100
        expected_rollers = int(available / P) + 1 if P > 0 else 0

        # Expected support count
        expected_supports = int(available / S) + 1 if S > 0 else 0

        # Expected guards
        expected_guards = 2 if config.get("side_guards", False) else 0

        return (
            self.roller_count == expected_rollers
            and self.support_count == expected_supports
            and self.guard_count == expected_guards
            and self.frame_count == 1
        )


def generate_bom(
    config: Dict[str, Any],
    roller_count: int,
    support_count: int,
    guard_count: int = 0,
) -> Dict[str, Any]:
    """Generate BOM dictionary from configuration.

    Args:
        config: Configuration dictionary.
        roller_count: Number of rollers.
        support_count: Number of support legs.
        guard_count: Number of side guards (0 or 2).

    Returns:
        BOM dictionary with component counts.
    """
    bom = BillOfMaterials(
        config=config,
        frame_count=1,
        roller_count=roller_count,
        support_count=support_count,
        guard_count=guard_count,
    )
    return bom.get_summary()


def export_bom_csv(
    bom: Dict[str, Any],
    config: Dict[str, Any],
    filepath: str,
) -> None:
    """Export BOM to CSV format.

    Args:
        bom: BOM dictionary from generate_bom().
        config: Configuration dictionary.
        filepath: Path to output CSV file.
    """
    bom_obj = BillOfMaterials(
        config=config,
        frame_count=bom["bill_of_materials"]["frame"]["quantity"],
        roller_count=bom["bill_of_materials"]["rollers"]["quantity"],
        support_count=bom["bill_of_materials"]["support_legs"]["quantity"],
        guard_count=bom["bill_of_materials"]["side_guards"]["quantity"],
    )
    bom_obj.export_csv(filepath)


def export_bom_json(
    bom: Dict[str, Any],
    config: Dict[str, Any],
    filepath: str,
) -> None:
    """Export BOM to JSON format.

    Args:
        bom: BOM dictionary from generate_bom().
        config: Configuration dictionary.
        filepath: Path to output JSON file.
    """
    bom_obj = BillOfMaterials(
        config=config,
        frame_count=bom["bill_of_materials"]["frame"]["quantity"],
        roller_count=bom["bill_of_materials"]["rollers"]["quantity"],
        support_count=bom["bill_of_materials"]["support_legs"]["quantity"],
        guard_count=bom["bill_of_materials"]["side_guards"]["quantity"],
    )
    bom_obj.export_json(filepath)


def save_all_bom_formats(
    config: Dict[str, Any],
    roller_count: int,
    support_count: int,
    guard_count: int,
    output_dir: str,
) -> tuple:
    """Generate and save BOM in both CSV and JSON formats.

    Args:
        config: Configuration dictionary.
        roller_count: Number of rollers.
        support_count: Number of support legs.
        guard_count: Number of side guards.
        output_dir: Directory to save BOM files.

    Returns:
        Tuple of (csv_path, json_path).
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Build config name for filenames
    L = config.get("L", 0)
    W = config.get("W", 0)
    H = config.get("H", 0)
    D = config.get("D", 0)
    P = config.get("P", 0)

    config_name = f"conveyor_{L}x{W}x{H}_{D}D_{P}P"
    csv_path = str(output_path / f"bom_{config_name}.csv")
    json_path = str(output_path / f"bom_{config_name}.json")

    # Generate BOM summary
    bom = generate_bom(config, roller_count, support_count, guard_count)

    # Export both formats
    export_bom_csv(bom, config, csv_path)
    export_bom_json(bom, config, json_path)

    return (csv_path, json_path)
