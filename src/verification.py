"""Closed-loop verification for generated conveyor assemblies.

The system doesn't stop at generation — it verifies the generated
geometry against the requested design parameters.

This implements the "self-checking CAD" and "closed-loop"
differentiators from the presentation guidance:
  - Generated length → PASS/FAIL
  - Generated width → PASS/FAIL
  - Roller diameter → PASS/FAIL
  - Roller spacing → PASS/FAIL
  - Roller count → PASS/FAIL
  - Support spacing → PASS/FAIL
  - Guard selection → PASS/FAIL

All checks are deterministic and reference the original config.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class VerificationCheck:
    """Result of a single verification check.

    Attributes:
        check_name: Human-readable name of the check.
        expected: The expected value (from config).
        actual: The actual value (from generated geometry).
        passed: True if expected matches actual within tolerance.
        tolerance_mm: Allowed deviation in mm (default 0.01).
        message: Human-readable result message.
    """
    check_name: str
    expected: float
    actual: float
    passed: bool = False
    tolerance_mm: float = 0.01
    message: str = ""


@dataclass
class AssemblyVerification:
    """Complete verification report for a generated assembly.

    Attributes:
        config: The original configuration dict.
        checks: List of all verification checks.
        all_passed: True if every check passes.
        passed_count: Number of checks that passed.
        failed_count: Number of checks that failed.
        summary_message: Overall human-readable summary.
    """

    config: dict[str, Any]
    checks: list[VerificationCheck] = field(default_factory=list)
    all_passed: bool = False
    passed_count: int = 0
    failed_count: int = 0
    summary_message: str = ""

    def __str__(self) -> str:
        """Human-readable verification report."""
        lines = []
        lines.append("=" * 55)
        lines.append("  ASSEMBLY VERIFICATION REPORT")
        lines.append("=" * 55)
        lines.append("")
        lines.append(f"  Configuration: {self.config.get('L', '?')}×{self.config.get('W', '?')}×{self.config.get('H', '?')} mm")
        lines.append("")

        for check in self.checks:
            status = "✓ PASS" if check.passed else "✗ FAIL"
            lines.append(f"  {status}  {check.check_name}")
            if not check.passed:
                lines.append(f"         Expected: {check.expected}, Actual: {check.actual}")

        lines.append("")
        lines.append("-" * 55)
        lines.append(f"  Total: {self.passed_count} passed, {self.failed_count} failed")
        lines.append("")

        if self.all_passed:
            lines.append("  ✓ All verification checks passed.")
            lines.append("  The generated geometry matches the requested design.")
        else:
            lines.append(f"  ✗ {self.failed_count} check(s) failed.")
            lines.append("  Generated geometry does NOT match the requested design.")

        lines.append("=" * 55)
        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        """Export verification as a dictionary."""
        return {
            "config": self.config,
            "all_passed": self.all_passed,
            "passed_count": self.passed_count,
            "failed_count": self.failed_count,
            "summary_message": self.summary_message,
            "checks": [
                {
                    "check": c.check_name,
                    "expected": c.expected,
                    "actual": c.actual,
                    "passed": c.passed,
                    "tolerance_mm": c.tolerance_mm,
                    "message": c.message,
                }
                for c in self.checks
            ],
        }


# ---------------------------------------------------------------------------
# Tolerance for floating-point comparisons
# ---------------------------------------------------------------------------

TOLERANCE = 0.01  # mm — dimensions must match within this


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------


def check_dimension(
    check_name: str,
    expected: float,
    actual: float,
    tolerance: float = TOLERANCE,
) -> VerificationCheck:
    """Create a dimension check result.

    Args:
        check_name: Name of the check.
        expected: Expected value from config.
        actual: Actual value from geometry.
        tolerance: Allowed deviation in mm.

    Returns:
        VerificationCheck with pass/fail determined.
    """
    passed = abs(expected - actual) <= tolerance
    return VerificationCheck(
        check_name=check_name,
        expected=expected,
        actual=actual,
        passed=passed,
        tolerance_mm=tolerance,
        message=(
            f"PASS: {check_name} = {actual} mm (expected {expected} mm)"
            if passed
            else f"FAIL: {check_name} = {actual} mm (expected {expected} mm, diff={abs(expected - actual):.3f} mm)"
        ),
    )


def verify_assembly(
    config: dict[str, Any],
    actual_length: float,
    actual_width: float,
    actual_height: float,
    actual_roller_diameter: float,
    actual_roller_count: int,
    actual_support_count: int,
    actual_guard_count: int,
    roller_spacing_actual: float | None = None,
    support_spacing_actual: float | None = None,
) -> AssemblyVerification:
    """Verify a generated assembly against the requested configuration.

    Runs all checks and returns a complete AssemblyVerification report.

    Args:
        config: Original configuration dict.
        actual_length: Measured conveyor length from geometry.
        actual_width: Measured conveyor width from geometry.
        actual_height: Measured frame height from geometry.
        actual_roller_diameter: Measured roller diameter.
        actual_roller_count: Number of rollers in the assembly.
        actual_support_count: Number of support legs in the assembly.
        actual_guard_count: Number of side guards in the assembly.
        roller_spacing_actual: Measured spacing between rollers (if available).
        support_spacing_actual: Measured spacing between supports (if available).

    Returns:
        AssemblyVerification with all checks.
    """
    checks: list[VerificationCheck] = []

    # 1. Frame dimensions
    checks.append(
        check_dimension("Conveyor Length (L)", config["L"], actual_length)
    )
    checks.append(
        check_dimension("Conveyor Width (W)", config["W"], actual_width)
    )
    checks.append(
        check_dimension("Frame Height (H)", config["H"], actual_height)
    )

    # 2. Roller diameter
    checks.append(
        check_dimension("Roller Diameter (D)", config["D"], actual_roller_diameter)
    )

    # 3. Roller count
    available_length = config["L"] - 100
    expected_roller_count = int(available_length / config["P"]) + 1
    count_check = VerificationCheck(
        check_name="Roller Count",
        expected=float(expected_roller_count),
        actual=float(actual_roller_count),
        passed=(actual_roller_count == expected_roller_count),
        message=(
            f"PASS: {actual_roller_count} rollers (expected {expected_roller_count})"
            if actual_roller_count == expected_roller_count
            else f"FAIL: {actual_roller_count} rollers (expected {expected_roller_count})"
        ),
    )
    checks.append(count_check)

    # 4. Roller spacing (if measurable)
    if roller_spacing_actual is not None:
        checks.append(
            check_dimension(
                "Roller Spacing (P)", config["P"], roller_spacing_actual
            )
        )

    # 5. Support count
    expected_support_count = int(available_length / config["S"]) + 1
    support_check = VerificationCheck(
        check_name="Support Leg Count",
        expected=float(expected_support_count),
        actual=float(actual_support_count),
        passed=(actual_support_count == expected_support_count),
        message=(
            f"PASS: {actual_support_count} supports (expected {expected_support_count})"
            if actual_support_count == expected_support_count
            else f"FAIL: {actual_support_count} supports (expected {expected_support_count})"
        ),
    )
    checks.append(support_check)

    # 6. Support spacing (if measurable)
    if support_spacing_actual is not None:
        checks.append(
            check_dimension(
                "Support Spacing (S)", config["S"], support_spacing_actual
            )
        )

    # 7. Guard selection
    expected_guards = 2 if config.get("side_guards", False) else 0
    guard_check = VerificationCheck(
        check_name="Side Guards",
        expected=float(expected_guards),
        actual=float(actual_guard_count),
        passed=(actual_guard_count == expected_guards),
        message=(
            f"PASS: {actual_guard_count} guards (expected {expected_guards})"
            if actual_guard_count == expected_guards
            else f"FAIL: {actual_guard_count} guards (expected {expected_guards})"
        ),
    )
    checks.append(guard_check)

    # Compute summary
    passed = sum(1 for c in checks if c.passed)
    failed = len(checks) - passed

    return AssemblyVerification(
        config=config,
        checks=checks,
        all_passed=(failed == 0),
        passed_count=passed,
        failed_count=failed,
        summary_message=(
            f"All {len(checks)} verification checks passed."
            if failed == 0
            else f"{failed} of {len(checks)} checks failed."
        ),
    )


def display_verification(verification: AssemblyVerification) -> None:
    """Print verification report to stdout.

    Args:
        verification: AssemblyVerification to display.
    """
    print(str(verification))


def verify_configuration_match(
    config: dict[str, Any],
    generated_roller_count: int,
    generated_support_count: int,
    generated_guard_count: int,
) -> bool:
    """Quick check: do generated counts match the config?

    Lightweight version of full verification — just checks counts.
    Useful as a pre-flight check before full verification.

    Args:
        config: Original configuration dict.
        generated_roller_count: Number of rollers generated.
        generated_support_count: Number of supports generated.
        generated_guard_count: Number of guards generated.

    Returns:
        True if all counts match expected values.
    """
    available = config["L"] - 100
    expected_rollers = int(available / config["P"]) + 1
    expected_supports = int(available / config["S"]) + 1
    expected_guards = 2 if config.get("side_guards", False) else 0

    return (
        generated_roller_count == expected_rollers
        and generated_support_count == expected_supports
        and generated_guard_count == expected_guards
    )
