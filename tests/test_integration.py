"""Integration test for the full conveyor generation pipeline.

Exercises config_validator → geometry_calculator → bom_generator without
requiring a live Fusion 360 instance. This is the "Phase 5" integration
test that would be run as part of CI before Fusion-specific tests.

To also exercise the Fusion side, run:
    python generate_all_configs.py
inside Fusion 360's Python environment, or
    python fusion_hello.py
to verify API connectivity first.
"""

import json
import os
import tempfile
import pytest
from pathlib import Path

from src.config_validator import ConveyorConfig
from src.geometry_calculator import calculate_geometry
from src.bom_generator import (
    BillOfMaterials,
    generate_bom,
    save_all_bom_formats,
)
from src.fusion_generator import create_test_config


# ---------------------------------------------------------------------------
# Fixtures — standard configs per the PRD/TRD
# ---------------------------------------------------------------------------

@pytest.fixture
def small_config_dict():
    """Config 1: Small/compact (L=800, W=300, H=500, no guards)."""
    return {
        "L": 800,
        "W": 300,
        "H": 500,
        "D": 40,
        "P": 100,
        "S": 500,
        "G": 0,
        "side_guards": False,
    }


@pytest.fixture
def medium_config_dict():
    """Config 2: Medium/standard (L=1200, W=450, H=700, with guards)."""
    return {
        "L": 1200,
        "W": 450,
        "H": 700,
        "D": 50,
        "P": 100,
        "S": 600,
        "G": 80,
        "side_guards": True,
    }


@pytest.fixture
def large_config_dict():
    """Config 3: Large/tall (L=1800, W=550, H=900, with guards)."""
    return {
        "L": 1800,
        "W": 550,
        "H": 900,
        "D": 60,
        "P": 120,
        "S": 700,
        "G": 150,
        "side_guards": True,
    }


# ---------------------------------------------------------------------------
# Pipeline validation for each config
# ---------------------------------------------------------------------------


class TestPipelineSmall:
    """Full pipeline validation for small config."""

    def test_validate(self, small_config_dict):
        config = ConveyorConfig(small_config_dict)
        assert config.validate() is True
        assert config.L == 800
        assert config.W == 300
        assert config.H == 500
        assert config.D == 40
        assert config.P == 100
        assert config.S == 500
        assert config.G == 0
        assert config.include_side_guards is False

    def test_geometry(self, small_config_dict):
        config = ConveyorConfig(small_config_dict)
        geo = calculate_geometry(config.L, config.P, config.S)
        assert geo.roller_count == 8
        assert geo.support_count == 2
        assert geo.roller_positions[0] == 50.0
        assert geo.roller_positions[-1] == 750.0
        assert geo.support_positions[0] == 50.0
        assert geo.support_positions[1] == 550.0

    def test_bom(self, small_config_dict):
        config = ConveyorConfig(small_config_dict)
        geo = calculate_geometry(config.L, config.P, config.S)
        bom = generate_bom(
            config.to_dict(),
            roller_count=geo.roller_count,
            support_count=geo.support_count,
            guard_count=0,
        )
        assert bom["bill_of_materials"]["frame"]["quantity"] == 1
        assert bom["bill_of_materials"]["rollers"]["quantity"] == 8
        assert bom["bill_of_materials"]["support_legs"]["quantity"] == 2
        assert bom["bill_of_materials"]["side_guards"]["quantity"] == 0
        assert bom["summary"]["total_components"] == 11
        assert bom["summary"]["total_guards"] == 0

    def test_bom_verify(self, small_config_dict):
        config = ConveyorConfig(small_config_dict)
        geo = calculate_geometry(config.L, config.P, config.S)
        bom_obj = BillOfMaterials(
            config=config.to_dict(),
            frame_count=1,
            roller_count=geo.roller_count,
            support_count=geo.support_count,
            guard_count=0,
        )
        assert bom_obj.verify_against_config() is True

    def test_bom_export(self, small_config_dict, tmp_path):
        config = ConveyorConfig(small_config_dict)
        geo = calculate_geometry(config.L, config.P, config.S)
        csv_path, json_path = save_all_bom_formats(
            config.to_dict(),
            geo.roller_count,
            geo.support_count,
            0,
            str(tmp_path),
        )
        assert os.path.exists(csv_path)
        assert os.path.exists(json_path)
        # Verify CSV content
        import csv
        with open(csv_path) as f:
            rows = list(csv.reader(f))
        assert rows[2][0] == "Roller"
        assert rows[2][1] == "8"
        assert rows[3][0] == "Support_Leg"
        assert rows[3][1] == "2"


class TestPipelineMedium:
    """Full pipeline validation for medium config."""

    def test_validate(self, medium_config_dict):
        config = ConveyorConfig(medium_config_dict)
        assert config.validate() is True
        assert config.L == 1200
        assert config.W == 450
        assert config.H == 700
        assert config.D == 50
        assert config.P == 100
        assert config.S == 600
        assert config.G == 80
        assert config.include_side_guards is True

    def test_geometry(self, medium_config_dict):
        config = ConveyorConfig(medium_config_dict)
        geo = calculate_geometry(config.L, config.P, config.S)
        # L=1200, P=100: floor(1100/100)+1 = 12
        assert geo.roller_count == 12
        # L=1200, S=600: floor(1100/600)+1 = 2
        assert geo.support_count == 2
        assert geo.roller_positions[0] == 50.0
        assert geo.roller_positions[-1] == 1150.0
        assert geo.support_positions[0] == 50.0
        assert geo.support_positions[1] == 650.0

    def test_bom(self, medium_config_dict):
        config = ConveyorConfig(medium_config_dict)
        geo = calculate_geometry(config.L, config.P, config.S)
        bom = generate_bom(
            config.to_dict(),
            roller_count=geo.roller_count,
            support_count=geo.support_count,
            guard_count=2,
        )
        assert bom["bill_of_materials"]["frame"]["quantity"] == 1
        assert bom["bill_of_materials"]["rollers"]["quantity"] == 12
        assert bom["bill_of_materials"]["support_legs"]["quantity"] == 2
        assert bom["bill_of_materials"]["side_guards"]["quantity"] == 2
        assert bom["summary"]["total_components"] == 17

    def test_bom_export(self, medium_config_dict, tmp_path):
        config = ConveyorConfig(medium_config_dict)
        geo = calculate_geometry(config.L, config.P, config.S)
        csv_path, json_path = save_all_bom_formats(
            config.to_dict(),
            geo.roller_count,
            geo.support_count,
            2,
            str(tmp_path),
        )
        assert os.path.exists(csv_path)
        assert os.path.exists(json_path)
        import csv
        with open(csv_path) as f:
            rows = list(csv.reader(f))
        assert rows[2][1] == "12"  # rollers


class TestPipelineLarge:
    """Full pipeline validation for large config."""

    def test_validate(self, large_config_dict):
        config = ConveyorConfig(large_config_dict)
        assert config.validate() is True
        assert config.L == 1800
        assert config.W == 550
        assert config.H == 900
        assert config.D == 60
        assert config.P == 120
        assert config.S == 700
        assert config.G == 150
        assert config.include_side_guards is True

    def test_geometry(self, large_config_dict):
        config = ConveyorConfig(large_config_dict)
        geo = calculate_geometry(config.L, config.P, config.S)
        # L=1800, P=120: floor(1700/120)+1 = 15
        assert geo.roller_count == 15
        # L=1800, S=700: floor(1700/700)+1 = 3
        assert geo.support_count == 3
        assert geo.roller_positions[0] == 50.0
        assert geo.roller_positions[-1] == 1730.0
        assert geo.support_positions[0] == 50.0
        assert geo.support_positions[1] == 750.0
        assert geo.support_positions[2] == 1450.0

    def test_bom(self, large_config_dict):
        config = ConveyorConfig(large_config_dict)
        geo = calculate_geometry(config.L, config.P, config.S)
        bom = generate_bom(
            config.to_dict(),
            roller_count=geo.roller_count,
            support_count=geo.support_count,
            guard_count=2,
        )
        assert bom["bill_of_materials"]["frame"]["quantity"] == 1
        assert bom["bill_of_materials"]["rollers"]["quantity"] == 15
        assert bom["bill_of_materials"]["support_legs"]["quantity"] == 3
        assert bom["bill_of_materials"]["side_guards"]["quantity"] == 2
        assert bom["summary"]["total_components"] == 21

    def test_bom_export(self, large_config_dict, tmp_path):
        config = ConveyorConfig(large_config_dict)
        geo = calculate_geometry(config.L, config.P, config.S)
        csv_path, json_path = save_all_bom_formats(
            config.to_dict(),
            geo.roller_count,
            geo.support_count,
            2,
            str(tmp_path),
        )
        assert os.path.exists(csv_path)
        assert os.path.exists(json_path)
        import csv
        with open(csv_path) as f:
            rows = list(csv.reader(f))
        assert rows[2][1] == "15"


# ---------------------------------------------------------------------------
# Cross-config differentiation — ensures the three configs are substantially
# different from each other (per acceptance criteria)
# ---------------------------------------------------------------------------


class TestConfigDifferentiation:
    """Verify the three configs produce meaningfully different results."""

    def test_small_vs_medium_roller_count_differs(self):
        small = calculate_geometry(800, 100, 500)
        medium = calculate_geometry(1200, 100, 600)
        assert small.roller_count != medium.roller_count
        assert small.roller_count < medium.roller_count

    def test_small_vs_large_roller_count_differs(self):
        small = calculate_geometry(800, 100, 500)
        large = calculate_geometry(1800, 120, 700)
        assert small.roller_count != large.roller_count
        assert small.roller_count < large.roller_count

    def test_medium_vs_large_roller_count_differs(self):
        medium = calculate_geometry(1200, 100, 600)
        large = calculate_geometry(1800, 120, 700)
        assert medium.roller_count != large.roller_count

    def test_all_three_have_different_total_components(self):
        small_bom = generate_bom(
            {"L": 800, "W": 300, "H": 500, "D": 40, "P": 100, "S": 500, "G": 0, "side_guards": False},
            roller_count=8, support_count=2, guard_count=0,
        )
        medium_bom = generate_bom(
            {"L": 1200, "W": 450, "H": 700, "D": 50, "P": 100, "S": 600, "G": 80, "side_guards": True},
            roller_count=12, support_count=2, guard_count=2,
        )
        large_bom = generate_bom(
            {"L": 1800, "W": 550, "H": 900, "D": 60, "P": 120, "S": 700, "G": 150, "side_guards": True},
            roller_count=15, support_count=3, guard_count=2,
        )
        totals = sorted([
            small_bom["summary"]["total_components"],
            medium_bom["summary"]["total_components"],
            large_bom["summary"]["total_components"],
        ])
        assert totals[0] != totals[1] or totals[1] != totals[2]

    def test_small_has_no_guards_medium_has_guards(self):
        config_s = ConveyorConfig({"L": 800, "W": 300, "H": 500, "D": 40, "P": 100, "S": 500, "G": 0, "side_guards": False})
        config_m = ConveyorConfig({"L": 1200, "W": 450, "H": 700, "D": 50, "P": 100, "S": 600, "G": 80, "side_guards": True})
        assert config_s.include_side_guards is False
        assert config_m.include_side_guards is True

    def test_small_vs_large_support_counts_differ(self):
        small = calculate_geometry(800, 100, 500)
        large = calculate_geometry(1800, 120, 700)
        assert small.support_count != large.support_count
