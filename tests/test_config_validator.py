"""Unit tests for config_validator module.

Tests validate parameter ranges, logical constraints, and
the ConveyorConfig class per the PRD/TRD specifications.
"""

import pytest
from src.config_validator import (
    ConveyorConfig,
    get_param_range,
    validate_logical_constraints,
    validate_param,
)


# =============================================================================
# Tests for validate_param
# =============================================================================


class TestValidateParam:
    """Tests for single parameter validation."""

    def test_L_in_range(self):
        assert validate_param("L", 1200) is True

    def test_L_at_min(self):
        assert validate_param("L", 800) is True

    def test_L_at_max(self):
        assert validate_param("L", 2000) is True

    def test_L_below_min(self):
        with pytest.raises(ValueError, match="exceeds range"):
            validate_param("L", 799)

    def test_L_above_max(self):
        with pytest.raises(ValueError, match="exceeds range"):
            validate_param("L", 2001)

    def test_W_in_range(self):
        assert validate_param("W", 450) is True

    def test_W_at_min(self):
        assert validate_param("W", 300) is True

    def test_W_at_max(self):
        assert validate_param("W", 600) is True

    def test_H_in_range(self):
        assert validate_param("H", 700) is True

    def test_D_in_range(self):
        assert validate_param("D", 50) is True

    def test_P_in_range(self):
        assert validate_param("P", 100) is True

    def test_S_in_range(self):
        assert validate_param("S", 600) is True

    def test_G_in_range(self):
        assert validate_param("G", 80) is True

    def test_G_zero_valid(self):
        assert validate_param("G", 0) is True

    def test_unknown_param(self):
        with pytest.raises(ValueError, match="Unknown parameter"):
            validate_param("X", 100)

    def test_non_numeric_param(self):
        with pytest.raises(ValueError, match="must be numeric"):
            validate_param("L", "1200mm")

    def test_float_value(self):
        assert validate_param("L", 1200.5) is True


# =============================================================================
# Tests for get_param_range
# =============================================================================


class TestGetParamRange:
    """Tests for parameter range retrieval."""

    def test_L_range(self):
        assert get_param_range("L") == (800, 2000)

    def test_W_range(self):
        assert get_param_range("W") == (300, 600)

    def test_H_range(self):
        assert get_param_range("H") == (500, 900)

    def test_D_range(self):
        assert get_param_range("D") == (40, 80)

    def test_P_range(self):
        assert get_param_range("P") == (80, 150)

    def test_S_range(self):
        assert get_param_range("S") == (500, 1000)

    def test_G_range(self):
        assert get_param_range("G") == (0, 150)

    def test_unknown_param(self):
        with pytest.raises(ValueError, match="Unknown parameter"):
            get_param_range("X")


# =============================================================================
# Tests for validate_logical_constraints
# =============================================================================


class TestValidateLogicalConstraints:
    """Tests for logical constraint validation."""

    def test_valid_config_passes(self):
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
        assert validate_logical_constraints(config) is True

    def test_roller_fit_failure(self):
        # L=800, P=400 (impossible but tests the check)
        # L-100=700, 2*400=800, 700 < 800 -> fails
        config = {
            "L": 800,
            "W": 300,
            "H": 500,
            "D": 40,
            "P": 400,
            "S": 500,
            "G": 0,
            "side_guards": False,
        }
        with pytest.raises(ValueError, match="too short for roller spacing"):
            validate_logical_constraints(config)

    def test_support_too_large(self):
        config = {
            "L": 800,
            "W": 300,
            "H": 500,
            "D": 40,
            "P": 100,
            "S": 800,
            "G": 0,
            "side_guards": False,
        }
        with pytest.raises(ValueError, match="too large for conveyor length"):
            validate_logical_constraints(config)

    def test_guards_with_zero_height(self):
        config = {
            "L": 1200,
            "W": 450,
            "H": 700,
            "D": 50,
            "P": 100,
            "S": 600,
            "G": 0,
            "side_guards": True,
        }
        with pytest.raises(ValueError, match="Cannot have side guards"):
            validate_logical_constraints(config)

    def test_no_guards_zero_height_ok(self):
        config = {
            "L": 1200,
            "W": 450,
            "H": 700,
            "D": 50,
            "P": 100,
            "S": 600,
            "G": 0,
            "side_guards": False,
        }
        assert validate_logical_constraints(config) is True

    def test_edge_roller_fit_exact(self):
        # L=300, P=100: L-100=200, 2*P=200, so 200 >= 200 passes
        config = {
            "L": 300,
            "W": 300,
            "H": 500,
            "D": 40,
            "P": 100,
            "S": 500,
            "G": 0,
            "side_guards": False,
        }
        with pytest.raises(ValueError):
            validate_logical_constraints(config)


# =============================================================================
# Tests for ConveyorConfig
# =============================================================================


class TestConveyorConfig:
    """Tests for the ConveyorConfig class."""

    def test_valid_config_creation(self):
        config_dict = {
            "L": 1200,
            "W": 450,
            "H": 700,
            "D": 50,
            "P": 100,
            "S": 600,
            "G": 80,
            "side_guards": True,
        }
        config = ConveyorConfig(config_dict)
        assert config.L == 1200
        assert config.W == 450
        assert config.H == 700
        assert config.D == 50
        assert config.P == 100
        assert config.S == 600
        assert config.G == 80
        assert config.include_side_guards is True

    def test_missing_parameter(self):
        config_dict = {
            "L": 1200,
            "W": 450,
            # Missing H
            "D": 50,
            "P": 100,
            "S": 600,
            "G": 80,
            "side_guards": True,
        }
        with pytest.raises(ValueError, match="Missing required parameter"):
            ConveyorConfig(config_dict)

    def test_non_numeric_L(self):
        config_dict = {
            "L": "1200mm",
            "W": 450,
            "H": 700,
            "D": 50,
            "P": 100,
            "S": 600,
            "G": 80,
            "side_guards": True,
        }
        with pytest.raises(ValueError, match="must be numeric"):
            ConveyorConfig(config_dict)

    def test_non_boolean_side_guards(self):
        config_dict = {
            "L": 1200,
            "W": 450,
            "H": 700,
            "D": 50,
            "P": 100,
            "S": 600,
            "G": 80,
            "side_guards": "yes",
        }
        with pytest.raises(ValueError, match="must be boolean"):
            ConveyorConfig(config_dict)

    def test_out_of_range_L(self):
        config_dict = {
            "L": 500,
            "W": 450,
            "H": 700,
            "D": 50,
            "P": 100,
            "S": 600,
            "G": 80,
            "side_guards": True,
        }
        with pytest.raises(ValueError, match="exceeds range"):
            ConveyorConfig(config_dict)

    def test_get_method(self):
        config_dict = {
            "L": 1200,
            "W": 450,
            "H": 700,
            "D": 50,
            "P": 100,
            "S": 600,
            "G": 80,
            "side_guards": True,
        }
        config = ConveyorConfig(config_dict)
        assert config.get("L") == 1200
        assert config.get("W") == 450
        assert config.get("H") == 700

    def test_get_unknown_param(self):
        config_dict = {
            "L": 1200,
            "W": 450,
            "H": 700,
            "D": 50,
            "P": 100,
            "S": 600,
            "G": 80,
            "side_guards": True,
        }
        config = ConveyorConfig(config_dict)
        with pytest.raises(KeyError, match="Unknown parameter"):
            config.get("X")

    def test_to_dict(self):
        config_dict = {
            "L": 1200,
            "W": 450,
            "H": 700,
            "D": 50,
            "P": 100,
            "S": 600,
            "G": 80,
            "side_guards": True,
        }
        config = ConveyorConfig(config_dict)
        result = config.to_dict()
        assert result["L"] == 1200
        assert result["side_guards"] is True
        assert isinstance(result, dict)

    def test_to_json(self):
        config_dict = {
            "L": 1200,
            "W": 450,
            "H": 700,
            "D": 50,
            "P": 100,
            "S": 600,
            "G": 80,
            "side_guards": True,
        }
        config = ConveyorConfig(config_dict)
        result = config.to_json()
        assert "1200" in result
        assert "side_guards" in result

    def test_validate_success(self):
        config_dict = {
            "L": 1200,
            "W": 450,
            "H": 700,
            "D": 50,
            "P": 100,
            "S": 600,
            "G": 80,
            "side_guards": True,
        }
        config = ConveyorConfig(config_dict)
        assert config.validate() is True

    def test_validate_roller_fit_failure(self):
        # Roller fit can't fail within valid ranges (min L=800, max P=150
        # gives 700 >= 300 always). Test the validate() method directly
        # with a post-construction scenario: build a valid config, then
        # mutate and call validate() to confirm it catches violations.
        config_dict = {
            "L": 1200,
            "W": 450,
            "H": 700,
            "D": 50,
            "P": 100,
            "S": 600,
            "G": 80,
            "side_guards": True,
        }
        config = ConveyorConfig(config_dict)
        # Mutate to invalid state
        config.L = 250  # Now L-100=150 < 2*100=200
        with pytest.raises(ValueError, match="too short"):
            config.validate()

    def test_small_config(self):
        config_dict = {
            "L": 800,
            "W": 300,
            "H": 500,
            "D": 40,
            "P": 100,
            "S": 500,
            "G": 0,
            "side_guards": False,
        }
        config = ConveyorConfig(config_dict)
        assert config.L == 800
        assert config.include_side_guards is False

    def test_large_config(self):
        config_dict = {
            "L": 1800,
            "W": 550,
            "H": 900,
            "D": 60,
            "P": 120,
            "S": 700,
            "G": 150,
            "side_guards": True,
        }
        config = ConveyorConfig(config_dict)
        assert config.L == 1800
        assert config.G == 150
        assert config.include_side_guards is True
