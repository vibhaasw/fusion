"""Unit tests for BOM generator module.

Tests BOM generation, CSV/JSON export, and verification
against configuration per the TRD specifications.
"""

import csv
import json
import os
import tempfile
import pytest
from src.bom_generator import (
    BillOfMaterials,
    export_bom_csv,
    export_bom_json,
    generate_bom,
    save_all_bom_formats,
)


# =============================================================================
# Tests for generate_bom
# =============================================================================


class TestGenerateBOM:
    """Tests for BOM generation from configuration."""

    def test_medium_config_bom(self):
        config = {
            "L": 1200,
            "W": 450,
            "H": 700,
            "D": 50,
            "P": 100,
            "S": 600,
            "G": 80,
            "side_guards": True,
        }
        bom = generate_bom(config, roller_count=12, support_count=2, guard_count=2)
        assert bom["bill_of_materials"]["frame"]["quantity"] == 1
        assert bom["bill_of_materials"]["rollers"]["quantity"] == 12
        assert bom["bill_of_materials"]["support_legs"]["quantity"] == 2
        assert bom["bill_of_materials"]["side_guards"]["quantity"] == 2
        assert bom["summary"]["total_components"] == 17

    def test_small_config_bom_no_guards(self):
        config = {
            "L": 800,
            "W": 300,
            "H": 500,
            "D": 40,
            "P": 100,
            "S": 500,
            "G": 0,
            "side_guards": False,
        }
        bom = generate_bom(config, roller_count=8, support_count=2, guard_count=0)
        assert bom["bill_of_materials"]["side_guards"]["quantity"] == 0
        assert bom["summary"]["total_guards"] == 0
        assert bom["summary"]["total_components"] == 11

    def test_bom_contains_timestamp(self):
        config = {
            "L": 1200,
            "W": 450,
            "H": 700,
            "D": 50,
            "P": 100,
            "S": 600,
            "G": 80,
            "side_guards": True,
        }
        bom = generate_bom(config, roller_count=12, support_count=2, guard_count=2)
        assert "generated_at" in bom
        assert "configuration" in bom
        assert "bill_of_materials" in bom
        assert "summary" in bom

    def test_bom_configuration_matches_input(self):
        config = {
            "L": 1500,
            "W": 500,
            "H": 800,
            "D": 60,
            "P": 110,
            "S": 800,
            "G": 100,
            "side_guards": True,
        }
        bom = generate_bom(config, roller_count=13, support_count=2, guard_count=2)
        assert bom["configuration"]["L"] == 1500
        assert bom["configuration"]["W"] == 500
        assert bom["configuration"]["H"] == 800


# =============================================================================
# Tests for BillOfMaterials class
# =============================================================================


class TestBillOfMaterials:
    """Tests for the BillOfMaterials container class."""

    def test_creation_with_counts(self):
        bom = BillOfMaterials(
            config={"L": 1200, "W": 450, "H": 700, "D": 50, "P": 100, "S": 600, "G": 80, "side_guards": True},
            frame_count=1,
            roller_count=12,
            support_count=2,
            guard_count=2,
        )
        assert bom.frame_count == 1
        assert bom.roller_count == 12
        assert bom.support_count == 2
        assert bom.guard_count == 2

    def test_total_components_property(self):
        bom = BillOfMaterials(
            config={},
            frame_count=1,
            roller_count=12,
            support_count=2,
            guard_count=2,
        )
        assert bom.total_components == 17

    def test_total_components_no_guards(self):
        bom = BillOfMaterials(
            config={},
            frame_count=1,
            roller_count=8,
            support_count=2,
            guard_count=0,
        )
        assert bom.total_components == 11

    def test_verify_against_config_success(self):
        config = {
            "L": 1200,
            "W": 450,
            "H": 700,
            "D": 50,
            "P": 100,
            "S": 600,
            "G": 80,
            "side_guards": True,
        }
        bom = BillOfMaterials(
            config=config,
            frame_count=1,
            roller_count=12,
            support_count=2,
            guard_count=2,
        )
        assert bom.verify_against_config() is True

    def test_verify_against_config_wrong_roller_count(self):
        config = {
            "L": 1200,
            "W": 450,
            "H": 700,
            "D": 50,
            "P": 100,
            "S": 600,
            "G": 80,
            "side_guards": True,
        }
        bom = BillOfMaterials(
            config=config,
            frame_count=1,
            roller_count=10,  # Wrong: should be 12
            support_count=2,
            guard_count=2,
        )
        assert bom.verify_against_config() is False

    def test_verify_against_config_wrong_guard_count(self):
        config = {
            "L": 1200,
            "W": 450,
            "H": 700,
            "D": 50,
            "P": 100,
            "S": 600,
            "G": 80,
            "side_guards": True,
        }
        bom = BillOfMaterials(
            config=config,
            frame_count=1,
            roller_count=12,
            support_count=2,
            guard_count=0,  # Wrong: should be 2
        )
        assert bom.verify_against_config() is False

    def test_export_csv(self, tmp_path):
        bom = BillOfMaterials(
            config={
                "L": 1200, "W": 450, "H": 700, "D": 50,
                "P": 100, "S": 600, "G": 80, "side_guards": True,
            },
            frame_count=1,
            roller_count=12,
            support_count=2,
            guard_count=2,
        )
        csv_path = str(tmp_path / "test_bom.csv")
        bom.export_csv(csv_path)

        assert os.path.exists(csv_path)
        with open(csv_path) as f:
            reader = csv.reader(f)
            rows = list(reader)

        assert rows[0] == ["Component_Type", "Quantity", "Diameter_or_Height_mm", "Notes"]
        assert rows[1][0] == "Frame"
        assert rows[1][1] == "1"
        assert rows[2][0] == "Roller"
        assert rows[2][1] == "12"
        assert rows[3][0] == "Support_Leg"
        assert rows[3][1] == "2"
        assert rows[4][0] == "Side_Guard"
        assert rows[4][1] == "2"
        assert rows[5][0] == "TOTAL"
        assert rows[5][1] == "17"

    def test_export_json(self, tmp_path):
        bom = BillOfMaterials(
            config={
                "L": 1200, "W": 450, "H": 700, "D": 50,
                "P": 100, "S": 600, "G": 80, "side_guards": True,
            },
            frame_count=1,
            roller_count=12,
            support_count=2,
            guard_count=2,
        )
        json_path = str(tmp_path / "test_bom.json")
        bom.export_json(json_path)

        assert os.path.exists(json_path)
        with open(json_path) as f:
            data = json.load(f)

        assert data["bill_of_materials"]["frame"]["quantity"] == 1
        assert data["bill_of_materials"]["rollers"]["quantity"] == 12
        assert data["summary"]["total_components"] == 17

    def test_export_json_contains_config(self, tmp_path):
        config = {
            "L": 1200, "W": 450, "H": 700, "D": 50,
            "P": 100, "S": 600, "G": 80, "side_guards": True,
        }
        bom = BillOfMaterials(
            config=config,
            frame_count=1,
            roller_count=12,
            support_count=2,
            guard_count=2,
        )
        json_path = str(tmp_path / "test_bom.json")
        bom.export_json(json_path)

        with open(json_path) as f:
            data = json.load(f)

        assert data["configuration"]["L"] == 1200
        assert data["configuration"]["side_guards"] is True


# =============================================================================
# Tests for export helper functions
# =============================================================================


class TestExportHelpers:
    """Tests for standalone export functions."""

    def test_export_bom_csv(self, tmp_path):
        bom = {
            "bill_of_materials": {
                "frame": {"quantity": 1},
                "rollers": {"quantity": 12},
                "support_legs": {"quantity": 2},
                "side_guards": {"quantity": 2},
            }
        }
        config = {
            "L": 1200, "W": 450, "H": 700, "D": 50,
            "P": 100, "S": 600, "G": 80, "side_guards": True,
        }
        csv_path = str(tmp_path / "helper_bom.csv")
        export_bom_csv(bom, config, csv_path)

        assert os.path.exists(csv_path)
        with open(csv_path) as f:
            rows = list(csv.reader(f))
        assert rows[2][1] == "12"  # Roller quantity

    def test_export_bom_json(self, tmp_path):
        bom = {
            "bill_of_materials": {
                "frame": {"quantity": 1},
                "rollers": {"quantity": 12},
                "support_legs": {"quantity": 2},
                "side_guards": {"quantity": 2},
            },
            "configuration": {
                "L": 1200, "W": 450, "H": 700,
                "D": 50, "P": 100, "S": 600, "G": 80,
                "side_guards": True,
            }
        }
        config = {
            "L": 1200, "W": 450, "H": 700, "D": 50,
            "P": 100, "S": 600, "G": 80, "side_guards": True,
        }
        json_path = str(tmp_path / "helper_bom.json")
        export_bom_json(bom, config, json_path)

        assert os.path.exists(json_path)
        with open(json_path) as f:
            data = json.load(f)
        assert data["bill_of_materials"]["rollers"]["quantity"] == 12


# =============================================================================
# Tests for save_all_bom_formats
# =============================================================================


class TestSaveAllBOMFormats:
    """Tests for saving BOM in both formats."""

    def test_save_both_formats(self, tmp_path):
        config = {
            "L": 1200, "W": 450, "H": 700, "D": 50,
            "P": 100, "S": 600, "G": 80, "side_guards": True,
        }
        csv_path, json_path = save_all_bom_formats(
            config, roller_count=12, support_count=2, guard_count=2,
            output_dir=str(tmp_path),
        )

        assert os.path.exists(csv_path)
        assert os.path.exists(json_path)
        assert csv_path.endswith(".csv")
        assert json_path.endswith(".json")
        assert "conveyor_1200x450x700" in csv_path
        assert "conveyor_1200x450x700" in json_path

    def test_files_contain_correct_data(self, tmp_path):
        config = {
            "L": 800, "W": 300, "H": 500, "D": 40,
            "P": 100, "S": 500, "G": 0, "side_guards": False,
        }
        csv_path, json_path = save_all_bom_formats(
            config, roller_count=8, support_count=2, guard_count=0,
            output_dir=str(tmp_path),
        )

        # Check CSV
        with open(csv_path) as f:
            rows = list(csv.reader(f))
        assert rows[2][1] == "8"  # 8 rollers
        # For small config (no guards): header, Frame, Roller, Support_Leg, TOTAL
        assert rows[4][1] == "11"  # Total 11

        # Check JSON
        with open(json_path) as f:
            data = json.load(f)
        assert data["bill_of_materials"]["rollers"]["quantity"] == 8
        assert data["bill_of_materials"]["side_guards"]["quantity"] == 0
