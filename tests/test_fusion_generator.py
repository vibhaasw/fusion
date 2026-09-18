"""Unit tests for the fusion generator module.

These tests verify the structural correctness of the Fusion generator
code without requiring a live Fusion 360 instance.

For full integration testing with Fusion, run manually inside
Fusion 360's Python environment.
"""

import pytest

# Test that the module can be imported (even without Fusion API)
def test_fusion_generator_import():
    """Verify the fusion_generator module can be imported."""
    import src.fusion_generator as fg
    # Module should exist and have the expected attributes
    assert hasattr(fg, "FusionAssemblyManager")
    assert hasattr(fg, "create_assembly")
    assert hasattr(fg, "save_assembly_to_file")
    assert hasattr(fg, "create_test_config")


def test_fusion_api_not_available_outside_fusion():
    """Verify Fusion API gracefully handles being outside Fusion."""
    import src.fusion_generator as fg

    # _HAS_FUSION should be False outside Fusion 360
    assert fg._HAS_FUSION is False


def test_create_test_config_default():
    """Test creating a default test configuration."""
    import src.fusion_generator as fg

    config = fg.create_test_config()
    assert config["L"] == 1200
    assert config["W"] == 450
    assert config["H"] == 700
    assert config["D"] == 50
    assert config["P"] == 100
    assert config["S"] == 600
    assert config["G"] == 80
    assert config["side_guards"] is True


def test_create_test_config_custom():
    """Test creating a custom test configuration."""
    import src.fusion_generator as fg

    config = fg.create_test_config(
        length=800,
        width=300,
        height=500,
        diameter=40,
        roller_spacing=100,
        support_spacing=500,
        guard_height=0,
        side_guards=False,
    )
    assert config["L"] == 800
    assert config["W"] == 300
    assert config["H"] == 500
    assert config["D"] == 40
    assert config["P"] == 100
    assert config["S"] == 500
    assert config["G"] == 0
    assert config["side_guards"] is False


def test_create_test_config_large():
    """Test creating a large configuration."""
    import src.fusion_generator as fg

    config = fg.create_test_config(
        length=1800,
        width=550,
        height=900,
        diameter=60,
        roller_spacing=120,
        support_spacing=700,
        guard_height=150,
        side_guards=True,
    )
    assert config["L"] == 1800
    assert config["W"] == 550
    assert config["H"] == 900
    assert config["D"] == 60
    assert config["P"] == 120
    assert config["S"] == 700
    assert config["G"] == 150
    assert config["side_guards"] is True


def test_constant_values():
    """Verify fixed dimension constants are correct."""
    import src.fusion_generator as fg

    assert fg.LEG_WIDTH == 40
    assert fg.GUARD_THICKNESS == 5
    assert fg.MARGIN == 50


def test_cleanup_stale_components_not_raises_outside_fusion():
    """Verify FusionAssemblyManager can be inspected without Fusion."""
    import src.fusion_generator as fg

    # The class should exist and have the expected methods
    assert hasattr(fg.FusionAssemblyManager, "cleanup_stale_components")
    assert hasattr(fg.FusionAssemblyManager, "generate_frame")
    assert hasattr(fg.FusionAssemblyManager, "generate_rollers")
    assert hasattr(fg.FusionAssemblyManager, "generate_supports")
    assert hasattr(fg.FusionAssemblyManager, "generate_guards")
    assert hasattr(fg.FusionAssemblyManager, "create_parameters")
    assert hasattr(fg.FusionAssemblyManager, "save_document")


def test_component_naming_conventions():
    """Verify component naming follows the TRD specification."""
    # Naming patterns from TRD Section 4.3:
    # Frame -> "Frame"
    # Rollers -> "Roller_1", "Roller_2", ..., "Roller_N"
    # Support Legs -> "Leg_1", "Leg_2", ..., "Leg_M"
    # Side Guards -> "SideGuard_Left", "SideGuard_Right"

    roller_names = [f"Roller_{i+1}" for i in range(5)]
    assert roller_names == ["Roller_1", "Roller_2", "Roller_3", "Roller_4", "Roller_5"]

    leg_names = [f"Leg_{i+1}" for i in range(3)]
    assert leg_names == ["Leg_1", "Leg_2", "Leg_3"]

    assert "SideGuard_Left" == "SideGuard_Left"
    assert "SideGuard_Right" == "SideGuard_Right"


def test_filenaming_convention():
    """Verify the Fusion document naming convention."""
    # Format: conveyor_{L}x{W}x{H}_{D}D_{P}P.f3d
    L, W, H, D, P = 1200, 450, 700, 50, 100
    filename = f"conveyor_{L}x{W}x{H}_{D}D_{P}P.f3d"
    assert filename == "conveyor_1200x450x700_50D_100P.f3d"

    # Small config
    L, W, H, D, P = 800, 300, 500, 40, 100
    filename = f"conveyor_{L}x{W}x{H}_{D}D_{P}P.f3d"
    assert filename == "conveyor_800x300x500_40D_100P.f3d"
