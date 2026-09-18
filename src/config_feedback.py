"""Configuration feedback — the "engineering assistant" layer.

Provides structured feedback after config validation:
- Validation status (what passed, what failed)
- Smart configuration suggestions (planned enhancement)
- Human-readable summary for UI/display

This is the "smart configuration feedback" feature from the
presentation guidance — makes the tool feel like an engineering
assistant, not just a button that creates CAD.
"""

from dataclasses import dataclass, field
from typing import Any


# ---------------------------------------------------------------------------
# Parameter metadata for user-facing display
# ---------------------------------------------------------------------------

PARAM_METADATA = {
    "L": {
        "name": "Conveyor Length",
        "unit": "mm",
        "description": "Total length of conveyor from end to end",
        "range": (800, 2000),
    },
    "W": {
        "name": "Conveyor Width",
        "unit": "mm",
        "description": "Width of conveyor belt surface",
        "range": (300, 600),
    },
    "H": {
        "name": "Frame Height",
        "unit": "mm",
        "description": "Height from floor to conveyor bed",
        "range": (500, 900),
    },
    "D": {
        "name": "Roller Diameter",
        "unit": "mm",
        "description": "Cylindrical roller outside diameter",
        "range": (40, 80),
    },
    "P": {
        "name": "Roller Spacing",
        "unit": "mm",
        "description": "Center-to-center spacing between rollers",
        "range": (80, 150),
    },
    "S": {
        "name": "Support Leg Spacing",
        "unit": "mm",
        "description": "Spacing between support leg pairs along length",
        "range": (500, 1000),
    },
    "G": {
        "name": "Side Guard Height",
        "unit": "mm",
        "description": "Height of optional side guard panels",
        "range": (0, 150),
    },
}


@dataclass
class ValidationResult:
    """Result of validating a single parameter.

    Attributes:
        param_name: Name of the parameter (e.g., 'L', 'D').
        value: The provided value.
        passed: True if the value is valid.
        message: Human-readable status or error message.
    """
    param_name: str
    value: float
    passed: bool
    message: str


@dataclass
class ConfigurationFeedback:
    """Structured feedback from configuration validation.

    Provides more than a simple pass/fail — gives the user
    a clear picture of what was checked and what the result is.

    Attributes:
        config_dict: The original configuration dictionary.
        parameter_results: List of per-parameter validation results.
        overall_passed: True if all parameters and constraints pass.
        constraint_results: List of logical constraint check results.
        summary_message: Overall human-readable summary.
        suggestions: List of smart suggestions (empty if none).
    """

    config_dict: dict[str, Any]
    parameter_results: list[ValidationResult] = field(default_factory=list)
    overall_passed: bool = False
    constraint_results: list[dict[str, Any]] = field(default_factory=list)
    summary_message: str = ""
    suggestions: list[str] = field(default_factory=list)

    def __str__(self) -> str:
        """Human-readable feedback summary."""
        lines = []
        lines.append("=" * 50)
        lines.append("  CONFIGURATION STATUS")
        lines.append("=" * 50)

        if self.overall_passed:
            lines.append("")
            lines.append("  ✓ Parameters valid")
            lines.append("  ✓ Roller layout feasible")
            lines.append("  ✓ Support layout generated")
            if self.config_dict.get("side_guards", False):
                lines.append("  ✓ Guard configuration valid")
            lines.append("")
            lines.append("  Configuration ready for generation")
        else:
            lines.append("")
            lines.append("  ✗ Configuration has issues:")
            for result in self.parameter_results:
                if not result.passed:
                    lines.append(f"    ✗ {result.message}")
            for constraint in self.constraint_results:
                if not constraint.get("passed", True):
                    lines.append(f"    ✗ {constraint['message']}")
            lines.append("")

        if self.suggestions:
            lines.append("  Suggestions:")
            for s in self.suggestions:
                lines.append(f"    → {s}")
            lines.append("")

        lines.append("=" * 50)
        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        """Export feedback as a dictionary (for UI or JSON display)."""
        return {
            "overall_passed": self.overall_passed,
            "summary_message": self.summary_message,
            "parameter_results": [
                {
                    "param": r.param_name,
                    "value": r.value,
                    "passed": r.passed,
                    "message": r.message,
                }
                for r in self.parameter_results
            ],
            "constraint_results": self.constraint_results,
            "suggestions": self.suggestions,
        }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def get_configuration_feedback(config_dict: dict[str, Any]) -> ConfigurationFeedback:
    """Generate structured feedback for a configuration dictionary.

    Runs all validations and returns a ConfigurationFeedback object
    with per-parameter results, constraint checks, and any smart
    suggestions.

    Args:
        config_dict: Dictionary with keys L, W, H, D, P, S, G, side_guards.

    Returns:
        ConfigurationFeedback with full validation status.
    """
    from src.config_validator import (
        ConveyorConfig,
        get_param_range,
        validate_logical_constraints,
    )

    feedback = ConfigurationFeedback(config_dict=config_dict)

    # 1. Per-parameter validation
    numeric_params = ["L", "W", "H", "D", "P", "S", "G"]
    for param in numeric_params:
        value = config_dict.get(param)
        try:
            # This will raise ValueError if out of range
            from src.config_validator import validate_param

            validate_param(param, value)
            lo, hi = get_param_range(param)
            metadata = PARAM_METADATA.get(param, {})
            desc = metadata.get("description", "")
            feedback.parameter_results.append(
                ValidationResult(
                    param_name=param,
                    value=float(value),
                    passed=True,
                    message=f"{metadata.get('name', param)} = {value} mm  (range [{lo}, {hi}]) ✓",
                )
            )
        except ValueError as e:
            feedback.parameter_results.append(
                ValidationResult(
                    param_name=param,
                    value=float(value) if isinstance(value, (int, float)) else 0.0,
                    passed=False,
                    message=str(e),
                )
            )

    # 2. Boolean parameter
    sg = config_dict.get("side_guards")
    if not isinstance(sg, bool):
        feedback.parameter_results.append(
            ValidationResult(
                param_name="side_guards",
                value=0.0,
                passed=False,
                message=f"side_guards must be boolean, got {type(sg).__name__}",
            )
        )
    else:
        feedback.parameter_results.append(
            ValidationResult(
                param_name="side_guards",
                value=1.0 if sg else 0.0,
                passed=True,
                message=f"Side guards: {'Enabled' if sg else 'Disabled'} ✓",
            )
        )

    # 3. Logical constraints
    constraints = [
        {
            "name": "Roller fit",
            "check": lambda: config_dict["L"] - 100 >= 2 * config_dict["P"],
            "message": "Roller spacing fits within conveyor length",
            "fail_message": "Conveyor too short for selected roller spacing",
        },
        {
            "name": "Support fit",
            "check": lambda: config_dict["S"] <= config_dict["L"] - 100,
            "message": "Support spacing fits within conveyor length",
            "fail_message": "Support spacing too large for conveyor length",
        },
    ]

    if config_dict.get("side_guards", False):
        constraints.append(
            {
                "name": "Guard height",
                "check": lambda: config_dict["G"] > 0,
                "message": "Guard height is valid (G > 0)",
                "fail_message": "Guard height must be > 0 when guards enabled",
            }
        )

    for constraint in constraints:
        try:
            passed = constraint["check"]()
            feedback.constraint_results.append(
                {
                    "name": constraint["name"],
                    "passed": passed,
                    "message": constraint["message"] if passed else constraint["fail_message"],
                }
            )
            if not passed:
                feedback.parameter_results.append(
                    ValidationResult(
                        param_name=constraint["name"].lower().replace(" ", "_"),
                        value=0.0,
                        passed=False,
                        message=constraint["fail_message"],
                    )
                )
        except (KeyError, TypeError, ValueError) as e:
            feedback.constraint_results.append(
                {
                    "name": constraint["name"],
                    "passed": False,
                    "message": f"Constraint check failed: {e}",
                }
            )

    # 4. Determine overall pass/fail
    all_passed = all(r.passed for r in feedback.parameter_results) and all(
        c.get("passed", True) for c in feedback.constraint_results
    )
    feedback.overall_passed = all_passed

    if all_passed:
        feedback.summary_message = "Configuration valid and ready for generation."
    else:
        failed = [r for r in feedback.parameter_results if not r.passed]
        feedback.summary_message = f"Configuration has {len(failed)} issue(s)."

    # 5. Smart suggestions (planned enhancement — currently basic)
    feedback.suggestions = _generate_suggestions(config_dict, feedback)

    return feedback


def _generate_suggestions(
    config_dict: dict[str, Any], feedback: ConfigurationFeedback
) -> list[str]:
    """Generate smart configuration suggestions.

    Planned enhancement — currently provides basic, helpful suggestions
    based on the configuration values. Future versions could include
    optimization suggestions (e.g., 'adjust spacing to reduce end margins').

    Args:
        config_dict: The configuration dictionary.
        feedback: The validation feedback (for context).

    Returns:
        List of suggestion strings (empty if none applicable).
    """
    suggestions = []

    # Only suggest if config is valid
    if not feedback.overall_passed:
        return suggestions

    L = float(config_dict.get("L", 0))
    P = float(config_dict.get("P", 0))
    S = float(config_dict.get("S", 0))

    if L <= 0 or P <= 0 or S <= 0:
        return suggestions

    # Suggestion 1: Roller end margin balance
    margin = 50.0
    available_length = L - 2 * margin
    roller_count = int(available_length / P) + 1
    used_length = (roller_count - 1) * P
    end_margin_total = L - used_length - 2 * margin

    # If there's significant unused space at the ends, suggest
    if end_margin_total > P * 0.5 and roller_count > 2:
        # Space left after all rollers and margins
        suggestions.append(
            f"Roller spacing {P}mm leaves ~{end_margin_total:.0f}mm extra at ends. "
            f"Consider P={P + 10}mm for tighter layout."
        )

    # Suggestion 2: Support density
    available_support_length = L - 2 * margin
    support_count = int(available_support_length / S) + 1
    if support_count < 2 and L > 1000:
        suggestions.append(
            f"Only {support_count} support{'s' if support_count != 1 else ''} for "
            f"a {L}mm conveyor. Consider S={min(S - 100, 500)}mm for more support."
        )

    # Suggestion 3: Guard height relative to frame
    G = float(config_dict.get("G", 0))
    H = float(config_dict.get("H", 0))
    if config_dict.get("side_guards", False) and G > 0 and H > 0:
        guard_ratio = G / H if H > 0 else 0
        if guard_ratio > 0.3:
            suggestions.append(
                f"Guard height {G}mm is {guard_ratio*100:.0f}% of frame height {H}mm. "
                f"High guards may interfere with material flow."
            )
        elif guard_ratio < 0.05 and G > 0:
            suggestions.append(
                f"Guard height {G}mm is very low relative to frame height {H}mm. "
                f"Consider G={max(G + 20, 50)}mm for effective guarding."
            )

    # Suggestion 4: Diameter to spacing ratio
    D = float(config_dict.get("D", 0))
    if D > 0 and P > 0:
        ratio = D / P
        if ratio > 0.6:
            suggestions.append(
                f"Roller diameter {D}mm is {ratio*100:.0f}% of spacing {P}mm. "
                f"Large rollers relative to spacing — check clearance."
            )

    return suggestions


def display_configuration_feedback(feedback: ConfigurationFeedback) -> None:
    """Print configuration feedback to stdout.

    Args:
        feedback: ConfigurationFeedback to display.
    """
    print(str(feedback))


def format_configuration_status(config_dict: dict[str, Any]) -> str:
    """One-line configuration status for display.

    Args:
        config_dict: Configuration dictionary.

    Returns:
        Formatted status string.
    """
    from src.config_validator import ConveyorConfig

    try:
        config = ConveyorConfig(config_dict)
        config.validate()
        L = config.L
        W = config.W
        H = config.H
        D = config.D
        P = config.P
        S = config.S
        G = config.G
        guards = "Yes" if config.include_side_guards else "No"

        from src.geometry_calculator import calculate_geometry

        geo = calculate_geometry(L, P, S)
        guard_count = 2 if config.include_side_guards else 0
        total = 1 + geo.roller_count + geo.support_count + guard_count

        return (
            f"✓ Valid configuration: {L}×{W}×{H}mm, "
            f"D={D}mm, P={P}mm, S={S}mm, G={G}mm, "
            f"guards={'Yes' if config.include_side_guards else 'No'} → "
            f"{geo.roller_count} rollers, {geo.support_count} supports, "
            f"{guard_count} guards, {total} total components"
        )
    except ValueError as e:
        return f"✗ Invalid configuration: {e}"
