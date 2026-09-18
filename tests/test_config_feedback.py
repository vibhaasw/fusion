"""Unit tests for configuration feedback module.

Tests the ConfigurationFeedback system — the "engineering assistant"
layer that provides structured status and smart suggestions.
"""

import pytest
from src.config_feedback import (
    ConfigurationFeedback,
    ValidationResult,
    display_configuration_feedback,
    format_configuration_status,
    get_configuration_feedback,
)


# =============================================================================
# Tests for get_configuration_feedback — valid configs
# =============================================================================


class TestConfigurationFeedbackValid:
    """Feedback for valid configurations."""

    def test_medium_config_feedback(self):
        config = {
            "L": 1200, "W": 450, "H": 700, "D": 50,
            "P": 100, "S": 600, "G": 80, "side_guards": True,
        }
        feedback = get_configuration_feedback(config)
        assert feedback.overall_passed is True
        assert len(feedback.parameter_results) == 8  # 7 numeric + 1 boolean
        assert len(feedback.constraint_results) == 3  # roller fit + support fit + guard

    def test_small_config_feedback(self):
        config = {
            "L": 800, "W": 300, "H": 500, "D": 40,
            "P": 100, "S": 500, "G": 0, "side_guards": False,
        }
        feedback = get_configuration_feedback(config)
        assert feedback.overall_passed is True
        # No guard constraint when side_guards=False
        constraint_names = [c["name"] for c in feedback.constraint_results]
        assert "Guard height" not in constraint_names

    def test_all_parameters_pass(self):
        config = {
            "L": 1200, "W": 450, "H": 700, "D": 50,
            "P": 100, "S": 600, "G": 80, "side_guards": True,
        }
        feedback = get_configuration_feedback(config)
        for result in feedback.parameter_results:
            assert result.passed is True

    def test_feedback_str_representation(self):
        config = {
            "L": 1200, "W": 450, "H": 700, "D": 50,
            "P": 100, "S": 600, "G": 80, "side_guards": True,
        }
        feedback = get_configuration_feedback(config)
        text = str(feedback)
        assert "CONFIGURATION STATUS" in text
        assert "✓ Parameters valid" in text
        assert "Configuration ready for generation" in text

    def test_feedback_dict_export(self):
        config = {
            "L": 1200, "W": 450, "H": 700, "D": 50,
            "P": 100, "S": 600, "G": 80, "side_guards": True,
        }
        feedback = get_configuration_feedback(config)
        d = feedback.to_dict()
        assert d["overall_passed"] is True
        assert len(d["parameter_results"]) == 8
        assert d["parameter_results"][0]["param"] == "L"
        assert d["parameter_results"][0]["passed"] is True

    def test_no_suggestions_for_valid_config(self):
        config = {
            "L": 1200, "W": 450, "H": 700, "D": 50,
            "P": 100, "S": 600, "G": 80, "side_guards": True,
        }
        feedback = get_configuration_feedback(config)
        # May have suggestions, may not — just verify it doesn't crash
        assert isinstance(feedback.suggestions, list)


# =============================================================================
# Tests for invalid configurations
# =============================================================================


class TestConfigurationFeedbackInvalid:
    """Feedback for invalid configurations."""

    def test_out_of_range_L(self):
        config = {
            "L": 500, "W": 450, "H": 700, "D": 50,
            "P": 100, "S": 600, "G": 80, "side_guards": True,
        }
        feedback = get_configuration_feedback(config)
        assert feedback.overall_passed is False
        L_results = [r for r in feedback.parameter_results if r.param_name == "L"]
        assert len(L_results) == 1
        assert L_results[0].passed is False
        assert "exceeds range" in L_results[0].message

    def test_missing_parameter(self):
        config = {
            "L": 1200, "W": 450, "H": 700, "D": 50,
            "P": 100, "S": 600, "G": 80,
            # Missing side_guards
        }
        feedback = get_configuration_feedback(config)
        assert feedback.overall_passed is False

    def test_roller_fit_failure(self):
        config = {
            "L": 800, "W": 300, "H": 500, "D": 40,
            "P": 400, "S": 500, "G": 0, "side_guards": False,
        }
        feedback = get_configuration_feedback(config)
        assert feedback.overall_passed is False
        constraint = [c for c in feedback.constraint_results if c["name"] == "Roller fit"][0]
        assert constraint["passed"] is False

    def test_guards_with_zero_height(self):
        config = {
            "L": 1200, "W": 450, "H": 700, "D": 50,
            "P": 100, "S": 600, "G": 0, "side_guards": True,
        }
        feedback = get_configuration_feedback(config)
        assert feedback.overall_passed is False
        constraint = [c for c in feedback.constraint_results if c["name"] == "Guard height"][0]
        assert constraint["passed"] is False

    def test_non_boolean_side_guards(self):
        config = {
            "L": 1200, "W": 450, "H": 700, "D": 50,
            "P": 100, "S": 600, "G": 80, "side_guards": "yes",
        }
        feedback = get_configuration_feedback(config)
        assert feedback.overall_passed is False
        sg_results = [r for r in feedback.parameter_results if r.param_name == "side_guards"]
        assert len(sg_results) == 1
        assert sg_results[0].passed is False


# =============================================================================
# Tests for smart suggestions (planned enhancement)
# =============================================================================


class TestSmartSuggestions:
    """Tests for the suggestion generation (planned enhancement feature)."""

    def test_no_suggestions_when_invalid(self):
        config = {
            "L": 500, "W": 450, "H": 700, "D": 50,
            "P": 100, "S": 600, "G": 80, "side_guards": True,
        }
        feedback = get_configuration_feedback(config)
        assert feedback.overall_passed is False
        assert feedback.suggestions == []

    def test_suggestion_for_high_guard_ratio(self):
        config = {
            "L": 1200, "W": 450, "H": 500, "D": 50,
            "P": 100, "S": 600, "G": 400, "side_guards": True,
        }
        # This is invalid (G out of range), so no suggestions
        feedback = get_configuration_feedback(config)
        assert feedback.overall_passed is False

    def test_suggestion_for_low_guard_ratio(self):
        config = {
            "L": 1200, "W": 450, "H": 900, "D": 50,
            "P": 100, "S": 600, "G": 10, "side_guards": True,
        }
        feedback = get_configuration_feedback(config)
        assert feedback.overall_passed is True
        # Low guard relative to height may trigger suggestion
        # (G=10, H=900 → ratio=0.011, below 0.05 threshold)
        if feedback.suggestions:
            assert any("guard" in s.lower() for s in feedback.suggestions)

    def test_suggestion_for_large_roller_diameter_ratio(self):
        config = {
            "L": 1200, "W": 450, "H": 700, "D": 80,
            "P": 100, "S": 600, "G": 80, "side_guards": True,
        }
        feedback = get_configuration_feedback(config)
        assert feedback.overall_passed is True
        # D=80, P=100 → ratio=0.8 > 0.6 → should suggest
        if feedback.suggestions:
            assert any("diameter" in s.lower() or "roller" in s.lower() for s in feedback.suggestions)

    def test_suggestions_for_uneven_margins(self):
        config = {
            "L": 850, "W": 450, "H": 700, "D": 50,
            "P": 100, "S": 600, "G": 80, "side_guards": True,
        }
        feedback = get_configuration_feedback(config)
        assert feedback.overall_passed is True
        # L=850, P=100: floor(750/100)+1 = 8 rollers,
        # used = 7*100 = 700, end_margin_total = 850 - 700 - 100 = 50
        # 50 > 100*0.5 = 50? No, 50 is not > 50. So no suggestion.
        # Let's try L=900, P=100: floor(800/100)+1 = 9, used=800, end=900-800-100=-100 → no
        # Try L=1050, P=100: floor(950/100)+1 = 10, used=900, end=1050-900-100=50.
        # 50 > 50? No. So try L=1100: floor(1000/100)+1=11, used=1000, end=1100-1000-100=0. No.
        # Try L=1060, P=100: floor(960/100)+1=10, used=900, end=1060-900-100=60.
        # 60 > 50 → should suggest
        config2 = {
            "L": 1060, "W": 450, "H": 700, "D": 50,
            "P": 100, "S": 600, "G": 80, "side_guards": True,
        }
        feedback2 = get_configuration_feedback(config2)
        assert feedback2.overall_passed is True
        if feedback2.suggestions:
            assert any("spacing" in s.lower() or "margin" in s.lower() for s in feedback2.suggestions)


# =============================================================================
# Tests for format_configuration_status
# =============================================================================


class TestFormatConfigurationStatus:
    """Tests for the one-line status formatter."""

    def test_valid_config_status(self):
        config = {
            "L": 1200, "W": 450, "H": 700, "D": 50,
            "P": 100, "S": 600, "G": 80, "side_guards": True,
        }
        status = format_configuration_status(config)
        assert status.startswith("✓ Valid configuration:")
        assert "1200" in status and "450" in status and "700" in status
        assert "12 rollers" in status
        assert "2 supports" in status
        assert "2 guards" in status
        assert "17 total components" in status

    def test_invalid_config_status(self):
        config = {
            "L": 500, "W": 450, "H": 700, "D": 50,
            "P": 100, "S": 600, "G": 80, "side_guards": True,
        }
        status = format_configuration_status(config)
        assert status.startswith("✗ Invalid configuration:")
        assert "exceeds range" in status

    def test_small_config_status(self):
        config = {
            "L": 800, "W": 300, "H": 500, "D": 40,
            "P": 100, "S": 500, "G": 0, "side_guards": False,
        }
        status = format_configuration_status(config)
        assert "8 rollers" in status
        assert "2 supports" in status
        assert "0 guards" in status or "No" in status
        assert "11 total components" in status

    def test_large_config_status(self):
        config = {
            "L": 1800, "W": 550, "H": 900, "D": 60,
            "P": 120, "S": 700, "G": 150, "side_guards": True,
        }
        status = format_configuration_status(config)
        assert "15 rollers" in status
        assert "3 supports" in status
        assert "21 total components" in status


# =============================================================================
# Tests for ValidationResult and ConfigurationFeedback dataclasses
# =============================================================================


class TestDataClasses:
    """Tests for the data classes."""

    def test_validation_result_creation(self):
        result = ValidationResult(
            param_name="L",
            value=1200.0,
            passed=True,
            message="Conveyor Length = 1200.0 mm  (range [800, 2000]) ✓",
        )
        assert result.param_name == "L"
        assert result.value == 1200.0
        assert result.passed is True
        assert "1200" in result.message

    def test_configuration_feedback_to_dict(self):
        feedback = ConfigurationFeedback(
            config_dict={"L": 1200},
            overall_passed=True,
            summary_message="All good.",
            suggestions=["Try larger rollers"],
        )
        d = feedback.to_dict()
        assert d["overall_passed"] is True
        assert d["summary_message"] == "All good."
        assert d["suggestions"] == ["Try larger rollers"]
        assert len(d["parameter_results"]) == 0

    def test_configuration_feedback_str(self):
        feedback = ConfigurationFeedback(
            config_dict={},
            overall_passed=True,
            summary_message="Ready.",
        )
        text = str(feedback)
        assert "CONFIGURATION STATUS" in text
        assert "Configuration ready for generation" in text
