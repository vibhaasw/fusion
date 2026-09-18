"""Unit tests for the closed-loop verification module.

Tests the AssemblyVerification system — the "self-checking CAD" feature
that verifies generated geometry against the requested design parameters.
"""

import pytest
from src.verification import (
    AssemblyVerification,
    VerificationCheck,
    check_dimension,
    display_verification,
    verify_assembly,
    verify_configuration_match,
)


# =============================================================================
# Tests for check_dimension helper
# =============================================================================


class TestCheckDimension:
    """Tests for the dimension check helper."""

    def test_pass_within_tolerance(self):
        check = check_dimension("Test", 100.0, 100.005, tolerance=0.01)
        assert check.passed is True
        assert "PASS" in check.message

    def test_fail_outside_tolerance(self):
        check = check_dimension("Test", 100.0, 100.5, tolerance=0.01)
        assert check.passed is False
        assert "FAIL" in check.message
        assert "diff=0.500" in check.message

    def test_exact_match(self):
        check = check_dimension("Test", 100.0, 100.0)
        assert check.passed is True

    def test_custom_tolerance(self):
        check = check_dimension("Test", 100.0, 100.5, tolerance=1.0)
        assert check.passed is True


# =============================================================================
# Tests for verify_assembly — full pipeline checks
# =============================================================================


class TestVerifyAssemblyMediumConfig:
    """Verify a medium configuration assembly."""

    @pytest.fixture
    def medium_config(self):
        return {
            "L": 1200, "W": 450, "H": 700, "D": 50,
            "P": 100, "S": 600, "G": 80, "side_guards": True,
        }

    def test_all_checks_pass(self, medium_config):
        verification = verify_assembly(
            config=medium_config,
            actual_length=1200.0,
            actual_width=450.0,
            actual_height=700.0,
            actual_roller_diameter=50.0,
            actual_roller_count=12,
            actual_support_count=2,
            actual_guard_count=2,
        )
        assert verification.all_passed is True
        assert verification.passed_count == 7  # L, W, H, D, count, support_count, guards
        assert verification.failed_count == 0

    def test_verification_str(self, medium_config):
        verification = verify_assembly(
            config=medium_config,
            actual_length=1200.0,
            actual_width=450.0,
            actual_height=700.0,
            actual_roller_diameter=50.0,
            actual_roller_count=12,
            actual_support_count=2,
            actual_guard_count=2,
        )
        text = str(verification)
        assert "ASSEMBLY VERIFICATION REPORT" in text
        assert "✓ PASS" in text
        assert "All verification checks passed" in text

    def test_verification_dict(self, medium_config):
        verification = verify_assembly(
            config=medium_config,
            actual_length=1200.0,
            actual_width=450.0,
            actual_height=700.0,
            actual_roller_diameter=50.0,
            actual_roller_count=12,
            actual_support_count=2,
            actual_guard_count=2,
        )
        d = verification.to_dict()
        assert d["all_passed"] is True
        assert d["passed_count"] == 7
        assert d["failed_count"] == 0
        assert len(d["checks"]) == 7
        assert d["checks"][0]["check"] == "Conveyor Length (L)"
        assert d["checks"][0]["passed"] is True


class TestVerifyAssemblySmallConfig:
    """Verify a small configuration assembly (no guards)."""

    @pytest.fixture
    def small_config(self):
        return {
            "L": 800, "W": 300, "H": 500, "D": 40,
            "P": 100, "S": 500, "G": 0, "side_guards": False,
        }

    def test_all_checks_pass_no_guards(self, small_config):
        verification = verify_assembly(
            config=small_config,
            actual_length=800.0,
            actual_width=300.0,
            actual_height=500.0,
            actual_roller_diameter=40.0,
            actual_roller_count=8,
            actual_support_count=2,
            actual_guard_count=0,
        )
        assert verification.all_passed is True
        assert verification.passed_count == 7  # L, W, H, D, roller_count, support_count, guards

    def test_guard_check_fails_when_guards_missing(self, small_config):
        verification = verify_assembly(
            config=small_config,
            actual_length=800.0,
            actual_width=300.0,
            actual_height=500.0,
            actual_roller_diameter=40.0,
            actual_roller_count=8,
            actual_support_count=2,
            actual_guard_count=2,  # Wrong! Small config has no guards
        )
        assert verification.all_passed is False
        guard_check = [c for c in verification.checks if c.check_name == "Side Guards"][0]
        assert guard_check.passed is False


class TestVerifyAssemblyLargeConfig:
    """Verify a large configuration assembly."""

    @pytest.fixture
    def large_config(self):
        return {
            "L": 1800, "W": 550, "H": 900, "D": 60,
            "P": 120, "S": 700, "G": 150, "side_guards": True,
        }

    def test_all_checks_pass(self, large_config):
        verification = verify_assembly(
            config=large_config,
            actual_length=1800.0,
            actual_width=550.0,
            actual_height=900.0,
            actual_roller_diameter=60.0,
            actual_roller_count=15,
            actual_support_count=3,
            actual_guard_count=2,
        )
        assert verification.all_passed is True

    def test_wrong_roller_count(self, large_config):
        verification = verify_assembly(
            config=large_config,
            actual_length=1800.0,
            actual_width=550.0,
            actual_height=900.0,
            actual_roller_diameter=60.0,
            actual_roller_count=14,  # Wrong! Should be 15
            actual_support_count=3,
            actual_guard_count=2,
        )
        assert verification.all_passed is False
        roller_check = [c for c in verification.checks if c.check_name == "Roller Count"][0]
        assert roller_check.passed is False

    def test_wrong_dimensions(self, large_config):
        verification = verify_assembly(
            config=large_config,
            actual_length=1700.0,  # Wrong!
            actual_width=550.0,
            actual_height=900.0,
            actual_roller_diameter=60.0,
            actual_roller_count=15,
            actual_support_count=3,
            actual_guard_count=2,
        )
        assert verification.all_passed is False
        length_check = [c for c in verification.checks if c.check_name == "Conveyor Length (L)"][0]
        assert length_check.passed is False


class TestVerifyAssemblyWithSpacingChecks:
    """Verify when roller/support spacing is measurable."""

    def test_roller_spacing_check(self):
        config = {
            "L": 1200, "W": 450, "H": 700, "D": 50,
            "P": 100, "S": 600, "G": 80, "side_guards": True,
        }
        verification = verify_assembly(
            config=config,
            actual_length=1200.0,
            actual_width=450.0,
            actual_height=700.0,
            actual_roller_diameter=50.0,
            actual_roller_count=12,
            actual_support_count=2,
            actual_guard_count=2,
            roller_spacing_actual=100.0,
        )
        spacing_check = [c for c in verification.checks if c.check_name == "Roller Spacing (P)"][0]
        assert spacing_check.passed is True

    def test_roller_spacing_check_fails(self):
        config = {
            "L": 1200, "W": 450, "H": 700, "D": 50,
            "P": 100, "S": 600, "G": 80, "side_guards": True,
        }
        verification = verify_assembly(
            config=config,
            actual_length=1200.0,
            actual_width=450.0,
            actual_height=700.0,
            actual_roller_diameter=50.0,
            actual_roller_count=12,
            actual_support_count=2,
            actual_guard_count=2,
            roller_spacing_actual=95.0,  # Wrong!
        )
        spacing_check = [c for c in verification.checks if c.check_name == "Roller Spacing (P)"][0]
        assert spacing_check.passed is False


# =============================================================================
# Tests for verify_configuration_match (lightweight check)
# =============================================================================


class TestVerifyConfigurationMatch:
    """Tests for the lightweight count-matching check."""

    def test_match_medium(self):
        config = {
            "L": 1200, "W": 450, "H": 700, "D": 50,
            "P": 100, "S": 600, "G": 80, "side_guards": True,
        }
        assert verify_configuration_match(config, 12, 2, 2) is True

    def test_mismatch_roller_count(self):
        config = {
            "L": 1200, "W": 450, "H": 700, "D": 50,
            "P": 100, "S": 600, "G": 80, "side_guards": True,
        }
        assert verify_configuration_match(config, 11, 2, 2) is False

    def test_mismatch_support_count(self):
        config = {
            "L": 1200, "W": 450, "H": 700, "D": 50,
            "P": 100, "S": 600, "G": 80, "side_guards": True,
        }
        assert verify_configuration_match(config, 12, 3, 2) is False

    def test_mismatch_guard_count(self):
        config = {
            "L": 1200, "W": 450, "H": 700, "D": 50,
            "P": 100, "S": 600, "G": 80, "side_guards": True,
        }
        assert verify_configuration_match(config, 12, 2, 0) is False

    def test_small_config_no_guards(self):
        config = {
            "L": 800, "W": 300, "H": 500, "D": 40,
            "P": 100, "S": 500, "G": 0, "side_guards": False,
        }
        assert verify_configuration_match(config, 8, 2, 0) is True
        assert verify_configuration_match(config, 8, 2, 2) is False

    def test_large_config(self):
        config = {
            "L": 1800, "W": 550, "H": 900, "D": 60,
            "P": 120, "S": 700, "G": 150, "side_guards": True,
        }
        assert verify_configuration_match(config, 15, 3, 2) is True
