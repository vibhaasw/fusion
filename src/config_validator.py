"""Configuration validator for conveyor parameters.

Validates and packages user input parameters against defined ranges
and logical constraints per the PRD/TRD specifications.
"""

from typing import Any

# Parameter ranges: (min, max) in mm
_PARAM_RANGES = {
    "L": (800, 2000),
    "W": (300, 600),
    "H": (500, 900),
    "D": (40, 80),
    "P": (80, 150),
    "S": (500, 1000),
    "G": (0, 150),
}

# Required parameter keys (including the boolean)
_REQUIRED_KEYS = {"L", "W", "H", "D", "P", "S", "G", "side_guards"}


class ConveyorConfig:
    """Validated conveyor configuration container.

    Attributes:
        L: Conveyor length (mm)
        W: Conveyor width (mm)
        H: Frame height (mm)
        D: Roller diameter (mm)
        P: Roller spacing (mm)
        S: Support leg spacing (mm)
        G: Side guard height (mm)
        include_side_guards: Whether to generate side guards
    """

    def __init__(self, config_dict: dict[str, Any]) -> None:
        """Initialize and validate configuration.

        Args:
            config_dict: Dictionary with keys L, W, H, D, P, S, G, side_guards.

        Raises:
            ValueError: If any parameter is invalid.
        """
        self._raw = dict(config_dict)
        self._validate_and_set()

    def _validate_and_set(self) -> None:
        """Run all validations and set attributes."""
        # Check required keys
        missing = _REQUIRED_KEYS - set(self._raw.keys())
        if missing:
            raise ValueError(
                f"Missing required parameter(s): {', '.join(sorted(missing))}"
            )

        # Type-check and range-check numeric params
        for param in ["L", "W", "H", "D", "P", "S", "G"]:
            value = self._raw[param]
            if not isinstance(value, (int, float)):
                raise ValueError(
                    f"Parameter {param} must be numeric, got {type(value).__name__}"
                )
            self._raw[param] = float(value)
            _check_range(param, self._raw[param])

        # Type-check boolean
        sg = self._raw["side_guards"]
        if not isinstance(sg, bool):
            raise ValueError(
                f"Parameter side_guards must be boolean, got {type(sg).__name__}"
            )

        # Logical constraints
        L = float(self._raw["L"])
        P = float(self._raw["P"])
        S = float(self._raw["S"])
        G = float(self._raw["G"])
        side_guards = self._raw["side_guards"]

        # Roller fit check: L - 100 >= 2 * P
        if L - 100 < 2 * P:
            raise ValueError(
                f"Conveyor length {L} too short for roller spacing {P}. "
                f"Need L >= {2 * P + 100}"
            )

        # Support placement check: S <= L - 100
        if S > L - 100:
            raise ValueError(
                f"Support spacing {S} too large for conveyor length {L}"
            )

        # Guard height logic
        if side_guards and G <= 0:
            raise ValueError(
                f"Cannot have side guards with height G = {G}. "
                f"Set G > 0 or side_guards = False"
            )

        # Set attributes
        self.L: float = L
        self.W: float = float(self._raw["W"])
        self.H: float = float(self._raw["H"])
        self.D: float = float(self._raw["D"])
        self.P: float = P
        self.S: float = S
        self.G: float = G
        self.include_side_guards: bool = side_guards

    def validate(self) -> bool:
        """Validate logical constraints between parameters.

        Range checks are performed at construction time.
        This method checks inter-parameter constraints only.

        Returns:
            True if valid (otherwise raises).

        Raises:
            ValueError: If logical constraints are violated.
        """
        if self.L - 100 < 2 * self.P:
            raise ValueError(
                f"Conveyor length {self.L} too short for roller spacing {self.P}. "
                f"Need L >= {2 * self.P + 100}"
            )
        if self.S > self.L - 100:
            raise ValueError(
                f"Support spacing {self.S} too large for conveyor length {self.L}"
            )
        if self.include_side_guards and self.G <= 0:
            raise ValueError(
                f"Cannot have side guards with height G = {self.G}. "
                f"Set G > 0 or side_guards = False"
            )
        return True

    def get(self, param_name: str) -> float:
        """Get parameter value by name.

        Args:
            param_name: One of L, W, H, D, P, S, G.

        Returns:
            The parameter value.

        Raises:
            KeyError: If param_name is not a numeric parameter.
        """
        if param_name not in _PARAM_RANGES:
            raise KeyError(f"Unknown parameter: {param_name}")
        return getattr(self, param_name)

    def to_dict(self) -> dict[str, Any]:
        """Export configuration to dictionary."""
        return {
            "L": self.L,
            "W": self.W,
            "H": self.H,
            "D": self.D,
            "P": self.P,
            "S": self.S,
            "G": self.G,
            "side_guards": self.include_side_guards,
        }

    def to_json(self) -> str:
        """Export configuration to JSON string."""
        import json

        return json.dumps(self.to_dict(), indent=2)


def validate_param(param_name: str, value: float) -> bool:
    """Validate a single parameter against its range.

    Args:
        param_name: Name of parameter (e.g., 'L', 'D', 'P').
        value: Value to validate.

    Returns:
        True if valid.

    Raises:
        ValueError: If out of range or type error.
    """
    if param_name not in _PARAM_RANGES:
        raise ValueError(f"Unknown parameter: {param_name}")

    if not isinstance(value, (int, float)):
        raise ValueError(
            f"Parameter {param_name} must be numeric, got {type(value).__name__}"
        )

    return _check_range(param_name, float(value))


def _check_range(param_name: str, value: float) -> bool:
    """Internal: check value against parameter range.

    Args:
        param_name: Parameter name.
        value: Value to check.

    Returns:
        True if within range.

    Raises:
        ValueError: If out of range.
    """
    lo, hi = _PARAM_RANGES[param_name]
    if value < lo or value > hi:
        raise ValueError(
            f"Parameter {param_name} value {value} exceeds range [{lo}, {hi}]"
        )
    return True


def get_param_range(param_name: str) -> tuple[float, float]:
    """Get allowed range for a parameter.

    Args:
        param_name: Name of parameter.

    Returns:
        Tuple of (min_value, max_value).

    Raises:
        ValueError: If unknown parameter.
    """
    if param_name not in _PARAM_RANGES:
        raise ValueError(f"Unknown parameter: {param_name}")
    return _PARAM_RANGES[param_name]


def validate_logical_constraints(config: dict[str, Any]) -> bool:
    """Validate logical constraints between parameters.

    Checks:
    - L - 100 >= 2 * P (room for rollers)
    - S <= L - 100 (supports fit)
    - If include_guards=True, G > 0

    Args:
        config: Dictionary with validated numeric values.

    Returns:
        True if constraints pass.

    Raises:
        ValueError: If constraints violated.
    """
    L = float(config["L"])
    P = float(config["P"])
    S = float(config["S"])
    G = float(config["G"])
    side_guards = bool(config["side_guards"])

    if L - 100 < 2 * P:
        raise ValueError(
            f"Conveyor length {L} too short for roller spacing {P}. "
            f"Need L >= {2 * P + 100}"
        )
    if S > L - 100:
        raise ValueError(
            f"Support spacing {S} too large for conveyor length {L}"
        )
    if side_guards and G <= 0:
        raise ValueError(
            f"Cannot have side guards with height G = {G}. "
            f"Set G > 0 or side_guards = False"
        )
    return True
