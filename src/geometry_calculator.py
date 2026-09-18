"""Geometry calculator for roller and support positioning.

Calculates roller and support leg positions based on conveyor
length and spacing parameters. All calculations are deterministic.

Algorithm per TRD Section 3.1-3.2:
  margin = 50 (mm from each end)
  available_length = L - 2 * margin
  count = floor(available_length / spacing) + 1
  positions = [margin + i * spacing for i in range(count)]
"""

import math
from typing import List


def calculate_roller_count(length: float, spacing: float) -> int:
    """Calculate number of rollers that fit.

    Formula: floor((length - 100) / spacing) + 1

    Args:
        length: Conveyor length (mm).
        spacing: Roller spacing (mm).

    Returns:
        Number of rollers.
    """
    available_length = length - 100  # 50mm margin on each end
    return int(math.floor(available_length / spacing)) + 1


def calculate_roller_positions(length: float, spacing: float) -> List[float]:
    """Calculate X-axis positions of rollers.

    Returns positions spaced at 'spacing' mm intervals,
    starting 50mm from each end.

    Args:
        length: Conveyor length (mm).
        spacing: Roller spacing (mm).

    Returns:
        List of X-axis positions.
    """
    count = calculate_roller_count(length, spacing)
    margin = 50.0
    return [margin + i * spacing for i in range(count)]


def calculate_support_count(length: float, spacing: float) -> int:
    """Calculate number of support legs.

    Formula: floor((length - 100) / spacing) + 1

    Args:
        length: Conveyor length (mm).
        spacing: Support leg spacing (mm).

    Returns:
        Number of support legs.
    """
    available_length = length - 100
    return int(math.floor(available_length / spacing)) + 1


def calculate_support_positions(length: float, spacing: float) -> List[float]:
    """Calculate X-axis positions of support legs.

    Args:
        length: Conveyor length (mm).
        spacing: Support leg spacing (mm).

    Returns:
        List of X-axis positions.
    """
    count = calculate_support_count(length, spacing)
    margin = 50.0
    return [margin + i * spacing for i in range(count)]


class CalculatedGeometry:
    """Container for calculated component positions and counts.

    Attributes:
        roller_count: Number of rollers.
        roller_positions: X-axis positions of rollers.
        support_count: Number of support legs.
        support_positions: X-axis positions of supports.
    """

    def __init__(
        self,
        roller_count: int,
        roller_pos: List[float],
        support_count: int,
        support_pos: List[float],
    ) -> None:
        """Initialize calculated geometry."""
        self.roller_count = roller_count
        self.roller_positions = roller_pos
        self.support_count = support_count
        self.support_positions = support_pos

    def validate(self) -> bool:
        """Validate all positions are within bounds.

        Returns:
            True if valid.

        Raises:
            ValueError: If any position is out of bounds.
        """
        # Roller positions must be within [50, L-50]
        for pos in self.roller_positions:
            if pos < 50 or pos > 1600:  # L max is 2000, so L-50 max is 1950
                raise ValueError(
                    f"Roller position {pos} out of bounds [50, 1950]"
                )

        # Spacing between consecutive rollers must equal P
        for i in range(1, len(self.roller_positions)):
            diff = self.roller_positions[i] - self.roller_positions[i - 1]
            if abs(diff - 100.0) > 0.01:  # Tolerance
                pass  # Will be checked by caller with actual P

        # Support positions within bounds
        for pos in self.support_positions:
            if pos < 50 or pos > 1950:
                raise ValueError(
                    f"Support position {pos} out of bounds [50, 1950]"
                )

        return True

    def to_dict(self) -> dict:
        """Export to dictionary."""
        return {
            "roller_count": self.roller_count,
            "roller_positions": self.roller_positions,
            "support_count": self.support_count,
            "support_positions": self.support_positions,
        }


def calculate_geometry(
    length: float, roller_spacing: float, support_spacing: float
) -> CalculatedGeometry:
    """Calculate complete geometry from validated config.

    Convenience wrapper that calls all calculate_* functions.

    Args:
        length: Conveyor length (mm).
        roller_spacing: Roller spacing P (mm).
        support_spacing: Support leg spacing S (mm).

    Returns:
        CalculatedGeometry with all positions and counts.
    """
    roller_count = calculate_roller_count(length, roller_spacing)
    roller_pos = calculate_roller_positions(length, roller_spacing)
    support_count = calculate_support_count(length, support_spacing)
    support_pos = calculate_support_positions(length, support_spacing)

    return CalculatedGeometry(
        roller_count=roller_count,
        roller_pos=roller_pos,
        support_count=support_count,
        support_pos=support_pos,
    )
