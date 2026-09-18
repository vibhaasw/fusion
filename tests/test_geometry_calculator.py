"""Unit tests for geometry_calculator module.

Tests roller and support positioning calculations per the
TRD specifications. All calculations must be deterministic.
"""

import pytest
from src.geometry_calculator import (
    calculate_geometry,
    calculate_roller_count,
    calculate_roller_positions,
    calculate_support_count,
    calculate_support_positions,
    CalculatedGeometry,
)


# =============================================================================
# Tests for calculate_roller_count
# =============================================================================


class TestCalculateRollerCount:
    """Tests for roller count calculation."""

    def test_medium_config(self):
        # L=1200, P=100: floor(1100/100)+1 = 11+1 = 12
        assert calculate_roller_count(1200, 100) == 12

    def test_small_config(self):
        # L=800, P=100: floor(700/100)+1 = 7+1 = 8
        assert calculate_roller_count(800, 100) == 8

    def test_large_config(self):
        # L=1800, P=120: floor(1700/120)+1 = 14+1 = 15
        assert calculate_roller_count(1800, 120) == 15

    def test_min_length_max_spacing(self):
        # L=800, P=150: floor(700/150)+1 = 4+1 = 5
        assert calculate_roller_count(800, 150) == 5

    def test_max_length_min_spacing(self):
        # L=2000, P=80: floor(1900/80)+1 = 23+1 = 24
        assert calculate_roller_count(2000, 80) == 24

    def test_exact_division(self):
        # L=1100, P=100: floor(1000/100)+1 = 10+1 = 11
        assert calculate_roller_count(1100, 100) == 11

    def test_non_exact_division(self):
        # L=1200, P=130: floor(1100/130)+1 = 8+1 = 9
        assert calculate_roller_count(1200, 130) == 9

    def test_L_1000_P_80(self):
        # L=1000, P=80: floor(900/80)+1 = 11+1 = 12
        assert calculate_roller_count(1000, 80) == 12


# =============================================================================
# Tests for calculate_roller_positions
# =============================================================================


class TestCalculateRollerPositions:
    """Tests for roller position calculation."""

    def test_medium_config_positions(self):
        # L=1200, P=100: positions = [50, 150, 250, ..., 1150]
        positions = calculate_roller_positions(1200, 100)
        assert len(positions) == 12
        assert positions[0] == 50.0
        assert positions[-1] == 1150.0
        # Check spacing
        for i in range(1, len(positions)):
            assert positions[i] - positions[i - 1] == 100.0

    def test_small_config_positions(self):
        # L=800, P=100: positions = [50, 150, ..., 750]
        positions = calculate_roller_positions(800, 100)
        assert len(positions) == 8
        assert positions[0] == 50.0
        assert positions[-1] == 750.0

    def test_positions_within_bounds(self):
        # All positions must be within [50, L-50]
        positions = calculate_roller_positions(1200, 100)
        for pos in positions:
            assert pos >= 50.0
            assert pos <= 1150.0  # L - 50

    def test_single_roller_minimum(self):
        # L=200, P=80 (would fail validation but calc still works)
        # floor(100/80)+1 = 1+1 = 2
        positions = calculate_roller_positions(200, 80)
        assert len(positions) == 2
        assert positions[0] == 50.0

    def test_positions_increasing(self):
        positions = calculate_roller_positions(1500, 100)
        for i in range(1, len(positions)):
            assert positions[i] > positions[i - 1]

    def test_large_config_positions(self):
        # L=1800, P=120: [50, 170, 290, ..., 1730]
        positions = calculate_roller_positions(1800, 120)
        assert len(positions) == 15
        assert positions[0] == 50.0
        assert positions[-1] == 1730.0


# =============================================================================
# Tests for calculate_support_count
# =============================================================================


class TestCalculateSupportCount:
    """Tests for support leg count calculation."""

    def test_medium_config(self):
        # L=1200, S=600: floor(1100/600)+1 = 1+1 = 2
        assert calculate_support_count(1200, 600) == 2

    def test_small_config(self):
        # L=800, S=500: floor(700/500)+1 = 1+1 = 2
        assert calculate_support_count(800, 500) == 2

    def test_large_config(self):
        # L=1800, S=700: floor(1700/700)+1 = 2+1 = 3
        assert calculate_support_count(1800, 700) == 3

    def test_dense_supports(self):
        # L=1200, S=500: floor(1100/500)+1 = 2+1 = 3
        assert calculate_support_count(1200, 500) == 3

    def test_sparse_supports(self):
        # L=2000, S=1000: floor(1900/1000)+1 = 1+1 = 2
        assert calculate_support_count(2000, 1000) == 2


# =============================================================================
# Tests for calculate_support_positions
# =============================================================================


class TestCalculateSupportPositions:
    """Tests for support leg position calculation."""

    def test_medium_config_positions(self):
        # L=1200, S=600: positions = [50, 650]
        positions = calculate_support_positions(1200, 600)
        assert len(positions) == 2
        assert positions[0] == 50.0
        assert positions[1] == 650.0

    def test_large_config_positions(self):
        # L=1800, S=700: positions = [50, 750, 1450]
        positions = calculate_support_positions(1800, 700)
        assert len(positions) == 3
        assert positions[0] == 50.0
        assert positions[1] == 750.0
        assert positions[2] == 1450.0

    def test_positions_within_bounds(self):
        positions = calculate_support_positions(1200, 600)
        for pos in positions:
            assert pos >= 50.0
            assert pos <= 1150.0

    def test_small_config_positions(self):
        # L=800, S=500: positions = [50, 550]
        positions = calculate_support_positions(800, 500)
        assert len(positions) == 2
        assert positions[0] == 50.0
        assert positions[1] == 550.0


# =============================================================================
# Tests for CalculatedGeometry
# =============================================================================


class TestCalculatedGeometry:
    """Tests for the CalculatedGeometry container class."""

    def test_creation(self):
        geo = CalculatedGeometry(
            roller_count=12,
            roller_pos=[50, 150, 250],
            support_count=2,
            support_pos=[50, 650],
        )
        assert geo.roller_count == 12
        assert geo.roller_positions == [50, 150, 250]
        assert geo.support_count == 2
        assert geo.support_positions == [50, 650]

    def test_validate_success(self):
        geo = CalculatedGeometry(
            roller_count=12,
            roller_pos=[50, 150, 250, 350, 450, 550, 650, 750, 850, 950, 1050, 1150],
            support_count=2,
            support_pos=[50, 650],
        )
        assert geo.validate() is True

    def test_to_dict(self):
        geo = CalculatedGeometry(
            roller_count=5,
            roller_pos=[50, 150, 250, 350, 450],
            support_count=2,
            support_pos=[50, 550],
        )
        result = geo.to_dict()
        assert result["roller_count"] == 5
        assert result["roller_positions"] == [50, 150, 250, 350, 450]
        assert result["support_count"] == 2


# =============================================================================
# Tests for calculate_geometry (full pipeline)
# =============================================================================


class TestCalculateGeometry:
    """Tests for the full geometry calculation pipeline."""

    def test_medium_configuration(self):
        geo = calculate_geometry(1200, 100, 600)
        assert geo.roller_count == 12
        assert geo.support_count == 2
        assert len(geo.roller_positions) == 12
        assert len(geo.support_positions) == 2
        assert geo.roller_positions[0] == 50.0
        assert geo.roller_positions[-1] == 1150.0
        assert geo.support_positions[0] == 50.0
        assert geo.support_positions[1] == 650.0

    def test_small_configuration(self):
        geo = calculate_geometry(800, 100, 500)
        assert geo.roller_count == 8
        assert geo.support_count == 2
        assert geo.roller_positions[0] == 50.0
        assert geo.roller_positions[-1] == 750.0

    def test_large_configuration(self):
        geo = calculate_geometry(1800, 120, 700)
        assert geo.roller_count == 15
        assert geo.support_count == 3
        assert geo.roller_positions[0] == 50.0
        assert geo.roller_positions[-1] == 1730.0
        assert geo.support_positions[2] == 1450.0

    def test_deterministic(self):
        # Same inputs always produce same outputs
        geo1 = calculate_geometry(1200, 100, 600)
        geo2 = calculate_geometry(1200, 100, 600)
        assert geo1.roller_count == geo2.roller_count
        assert geo1.roller_positions == geo2.roller_positions
        assert geo1.support_count == geo2.support_count
        assert geo1.support_positions == geo2.support_positions
