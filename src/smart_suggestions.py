"""Smart configuration suggestions engine.

Provides intelligent feedback on conveyor configurations — detects
potential issues and suggests improvements. This is the "engineering
assistant" differentiator from the presentation.

Suggested enhancements:
- Uneven end margin warning
- Support density assessment  
- Guard height vs frame height ratio
- Roller diameter to spacing ratio
- Optimal spacing suggestions
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class ConfigSuggestion:
    """A single smart suggestion for a configuration.

    Attributes:
        category: Category of the suggestion (e.g., 'spacing', 'guards').
        suggestion: The suggestion text.
        suggestion_type: Type of suggestion ('warning', 'info', 'optimization').
        affected_params: List of parameter names this suggestion affects.
    """
    category: str
    suggestion: str
    suggestion_type: str = "info"  # 'warning', 'info', 'optimization'
    affected_params: list[str] = None


def generate_smart_suggestions(config: dict[str, Any]) -> list[ConfigSuggestion]:
    """Generate smart suggestions for a conveyor configuration.

    Analyzes the configuration and provides intelligent feedback
    beyond simple validation — detecting potential issues and
    suggesting improvements.

    Args:
        config: Validated configuration dictionary.

    Returns:
        List of ConfigSuggestion objects.
    """
    suggestions: list[ConfigSuggestion] = []

    L = config.get("L", 0)
    W = config.get("W", 0)
    H = config.get("H", 0)
    D = config.get("D", 0)
    P = config.get("P", 0)
    S = config.get("S", 0)
    G = config.get("G", 0)
    include_guards = config.get("side_guards", False)

    if L <= 0 or P <= 0:
        return suggestions

    # 1. End margin analysis
    _analyze_end_margins(L, P, suggestions)

    # 2. Support leg density check
    _analyze_support_density(L, S, suggestions)

    # 3. Guard height assessment
    if include_guards and G > 0 and H > 0:
        _analyze_guard_height(G, H, suggestions)

    # 4. Roller diameter to spacing ratio
    if D > 0 and P > 0:
        _analyze_roller_spacing_ratio(D, P, suggestions)

    # 5. Width-to-length aspect ratio
    if L > 0 and W > 0:
        _analyze_aspect_ratio(L, W, suggestions)

    # 6. Configuration complexity assessment
    _assess_complexity(L, W, H, include_guards, suggestions)

    return suggestions


def _analyze_end_margins(L: float, P: float, suggestions: list[ConfigSuggestion]) -> None:
    """Analyze end margins and suggest optimal roller spacing.

    The margin from the last roller to the conveyor end should be
    close to the standard 50mm margin for balanced design.
    """

    margin = 50.0  # mm
    last_roller_pos = margin + int((L - 2 * margin) / P) * P
    end_gap = L - last_roller_pos

    if end_gap > P * 0.5:
        suggestions.append(
            ConfigSuggestion(
                category="spacing",
                suggestion=(
                    f"Roller spacing {P}mm creates uneven end margin "
                    f"({end_gap:.0f}mm). Consider adjusting to {P + 10}mm "
                    f"for more balanced layout."
                ),
                suggestion_type="optimization",
                affected_params=["P"],
            )
        )
    elif end_gap < -P * 0.3:
        suggestions.append(
            ConfigSuggestion(
                category="spacing",
                suggestion=(
                    f"Roller spacing {P}mm causes rollers to extend beyond "
                    f"conveyor end. Check configuration."
                ),
                suggestion_type="warning",
                affected_params=["P", "L"],
            )
        )


def _analyze_support_density(L: float, S: float, suggestions: list[ConfigSuggestion]) -> None:
    """Analyze support leg density and suggest improvements.

    Too few supports for a long conveyor may indicate instability.
    """

    margin = 50.0
    available = L - 2 * margin
    if available <= 0 or S <= 0:
        return

    support_count = int(available / S) + 1
    supports_per_meter = support_count / (L / 1000.0)

    if supports_per_meter < 3.0 and L > 1000:
        suggestions.append(
            ConfigSuggestion(
                category="supports",
                suggestion=(
                    f"Only {support_count} support{'s' if support_count != 1 else ''} "
                    f"for a {L}mm conveyor ({supports_per_meter:.1f} supports/m). "
                    f"Consider reducing spacing to {max(S - 200, 500)}mm for better stability."
                ),
                suggestion_type="warning",
                affected_params=["S"],
            )
        )
    elif supports_per_meter > 8.0:
        suggestions.append(
            ConfigSuggestion(
                category="supports",
                suggestion=(
                    f"High support density: {support_count} supports on {L}mm conveyor "
                    f"({supports_per_meter:.1f} supports/m). Consider increasing spacing "
                    f"to {min(S + 100, 1000)}mm to reduce component count."
                ),
                suggestion_type="info",
                affected_params=["S"],
            )
        )


def _analyze_guard_height(G: float, H: float, suggestions: list[ConfigSuggestion]) -> None:
    """Analyze guard height relative to frame height.

    Very high guards may interfere with material flow.
    Very low guards may not provide effective protection.
    """

    if G <= 0 or H <= 0:
        return

    ratio = G / H

    if ratio > 0.35:
        suggestions.append(
            ConfigSuggestion(
                category="guards",
                suggestion=(
                    f"Guard height {G}mm is {ratio*100:.0f}% of frame height {H}mm. "
                    f"High guards may interfere with material flow. "
                    f"Consider G={int(H * 0.3)}mm for better clearance."
                ),
                suggestion_type="warning",
                affected_params=["G"],
            )
        )
    elif ratio < 0.08 and G > 0:
        suggestions.append(
            ConfigSuggestion(
                category="guards",
                suggestion=(
                    f"Guard height {G}mm is very low ({ratio*100:.0f}% of frame height "
                    f"{H}mm). May not provide effective edge protection. "
                    f"Consider G={max(G + 30, 50)}mm."
                ),
                suggestion_type="info",
                affected_params=["G"],
            )
        )


def _analyze_roller_spacing_ratio(D: float, P: float, suggestions: list[ConfigSuggestion]) -> None:
    """Analyze roller diameter relative to spacing.

    Large rollers relative to spacing may cause material guidance issues.
    """

    if D <= 0 or P <= 0:
        return

    ratio = D / P

    if ratio > 0.6:
        suggestions.append(
            ConfigSuggestion(
                category="rollers",
                suggestion=(
                    f"Roller diameter {D}mm is {ratio*100:.0f}% of spacing {P}mm. "
                    f"Large rollers relative to spacing — check material guidance "
                    f"clearance. Consider P={D + 30}mm or smaller rollers."
                ),
                suggestion_type="warning",
                affected_params=["D", "P"],
            )
        )
    elif ratio < 0.2 and D > 0:
        suggestions.append(
            ConfigSuggestion(
                category="rollers",
                suggestion=(
                    f"Roller diameter {D}mm is small relative to spacing {P}mm "
                    f"({ratio*100:.0f}%). Small rollers may not support heavy loads. "
                    f"Consider D={max(D + 10, 50)}mm for better load capacity."
                ),
                suggestion_type="info",
                affected_params=["D"],
            )
        )


def _analyze_aspect_ratio(L: float, W: float, suggestions: list[ConfigSuggestion]) -> None:
    """Analyze conveyor length-to-width aspect ratio.

    Very long, narrow conveyors or very short, wide ones may have
    different design considerations.
    """

    if L <= 0 or W <= 0:
        return

    ratio = L / W

    if ratio > 5.0:
        suggestions.append(
            ConfigSuggestion(
                category="geometry",
                suggestion=(
                    f"Conveyor is very long relative to width "
                    f"({L}mm × {W}mm = {ratio:.1f}:1 ratio). "
                    f"Consider additional intermediate support for stability."
                ),
                suggestion_type="info",
                affected_params=["S"],
            )
        )
    elif ratio < 1.5:
        suggestions.append(
            ConfigSuggestion(
                category="geometry",
                suggestion=(
                    f"Conveyor is nearly square ({L}mm × {W}mm = {ratio:.1f}:1 ratio). "
                    f"Short conveyors may not need side guards. "
                    f"Consider setting side_guards=False to simplify."
                ),
                suggestion_type="info",
                affected_params=["side_guards"],
            )
        )


def _assess_complexity(
    L: float, W: float, H: float, include_guards: bool, suggestions: list[ConfigSuggestion]
) -> None:
    """Assess overall configuration complexity.

    Provides a high-level assessment of the configuration.
    """

    if L >= 1500 and W >= 500 and H >= 800 and include_guards:
        suggestions.append(
            ConfigSuggestion(
                category="complexity",
                suggestion=(
                    f"Large, complex configuration: {L}×{W}×{H}mm with guards. "
                    f"This is a substantial assembly with many components. "
                    f"Verify all dimensions before generating."
                ),
                suggestion_type="info",
                affected_params=["L", "W", "H"],
            )
        )
    elif L <= 900 and W <= 400 and H <= 600 and not include_guards:
        suggestions.append(
            ConfigSuggestion(
                category="complexity",
                suggestion=(
                    f"Simple, compact configuration: {L}×{W}×{H}mm without guards. "
                    f"Good choice for low-capacity applications. "
                    f"Consider upgrading to medium size for more versatility."
                ),
                suggestion_type="info",
                affected_params=["L", "W", "H"],
            )
        )
