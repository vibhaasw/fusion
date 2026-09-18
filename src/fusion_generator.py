"""Fusion 360 CAD generation for conveyor assemblies.

Creates parametric roller conveyor assemblies using the Fusion 360 API.
This module is designed to run inside Fusion 360's Python environment.

For standalone testing and configuration preview, use the CLI in ui_handler.py.

============================================================================
INTERFACE CONTRACT
============================================================================
create_assembly() and all generation methods consume a configuration dict
with this exact shape (produced by config_validator.ConveyorConfig.to_dict()):

    {
        "L": 1200,              # float — Conveyor length (mm),   range [800, 2000]
        "W": 450,               # float — Conveyor width (mm),    range [300, 600]
        "H": 700,               # float — Frame height (mm),      range [500, 900]
        "D": 50,                # float — Roller diameter (mm),   range [40, 80]
        "P": 100,               # float — Roller spacing (mm),    range [80, 150]
        "S": 600,               # float — Support spacing (mm),   range [500, 1000]
        "G": 80,                # float — Guard height (mm),      range [0, 150]
        "side_guards": True     # bool  — Include side guards
    }

Do NOT add, remove, or rename keys without coordinating across the team.
Code that consumes this dict (fusion_generator.py, bom_generator.py,
ui_handler.py) will break silently if the shape changes.
============================================================================

Component naming conventions (per TRD Section 4.3):
  Frame        -> "Frame"
  Rollers      -> "Roller_1", "Roller_2", ..., "Roller_N"
  Support Legs -> "Leg_1", "Leg_2", ..., "Leg_M"
  Side Guards  -> "SideGuard_Left", "SideGuard_Right"
"""

from typing import Any, Dict, List, Optional

# Try to import Fusion API — will only succeed inside Fusion 360
try:
    import adsk.core
    import adsk.fusion
    import adsk.cam
    _HAS_FUSION = True
except ImportError:
    _HAS_FUSION = False

# Fixed dimensions (per TRD Section 5.3)
LEG_WIDTH = 40  # mm, fixed cross-section for support legs
GUARD_THICKNESS = 5  # mm, fixed thickness for side guards
MARGIN = 50  # mm from each conveyor end to first/last component


class FusionAssemblyManager:
    """Manages Fusion 360 document, components, and parametric relationships.

    Attributes:
        app: Fusion application instance.
        document: Fusion document.
        parameters: Dict of created Fusion parameter objects.
    """

    def __init__(self, app: "adsk.core.Application") -> None:
        """Initialize with Fusion app instance.

        Args:
            app: Fusion application instance.

        Raises:
            RuntimeError: If not running inside Fusion 360.
        """
        if not _HAS_FUSION:
            raise RuntimeError(
                "Fusion API not available. This module must run inside Fusion 360."
            )
        self.app = app
        self.document: Optional["adsk.fusion.Document"] = None
        self.parameters: Dict[str, "adsk.fusion.Parameter"] = {}

    def create_document(self, name: str) -> "adsk.fusion.Document":
        """Create a new Fusion document.

        Args:
            name: Document name.

        Returns:
            The created Fusion document.
        """
        self.document = self.app.documents.add(adsk.fusion.DocumentTypes.DesignDocumentType)
        self.document.name = name
        return self.document

    def create_parameters(self, config: Dict[str, Any]) -> Dict[str, "adsk.fusion.Parameter"]:
        """Create Fusion parameters from configuration.

        Args:
            config: Validated configuration dictionary.

        Returns:
            Dict mapping parameter names to Fusion Parameter objects.
        """
        design = self.document.product
        parameters = design.parameters

        param_defs = {
            "L": (config["L"], "mm", "Conveyor length"),
            "W": (config["W"], "mm", "Conveyor width"),
            "H": (config["H"], "mm", "Frame height"),
            "D": (config["D"], "mm", "Roller diameter"),
            "P": (config["P"], "mm", "Roller spacing"),
            "S": (config["S"], "mm", "Support leg spacing"),
            "G": (config["G"], "mm", "Side guard height"),
        }

        for name, (value, unit, description) in param_defs.items():
            param = parameters.add(
                name,
                adsk.core.DistanceValue.create(value, unit),
                description,
            )
            self.parameters[name] = param

        return self.parameters

    def _get_param_value(self, name: str) -> float:
        """Get a parameter's numeric value.

        Args:
            name: Parameter name.

        Returns:
            Parameter value in mm.
        """
        if name in self.parameters:
            return self.parameters[name].expression
        # Fallback: return from config if parameter not created
        return 0.0

    def generate_frame(self, config: Dict[str, Any]) -> "adsk.fusion.BRepBody":
        """Generate the frame body (rectangular box L x W x H).

        Args:
            config: Configuration dictionary.

        Returns:
            The created frame body.
        """
        design = self.document.product
        root_comp = design.rootComponent

        # Get parameter values
        L = config["L"]
        W = config["W"]
        H = config["H"]

        # Create sketch on XY plane (Z=0)
        sketches = root_comp.sketches
        xy_plane = root_comp.xYConstructionPlane
        sketch = sketches.add(xy_plane)

        # Draw rectangle from (0,0) to (L, W)
        lines = sketch.sketchCurves.sketchLines
        lines.addByCenter(
            adsk.core.Point3D.create(0, 0, 0),
            adsk.core.Point3D.create(L, 0, 0),
        )
        lines.addByCenter(
            adsk.core.Point3D.create(L, 0, 0),
            adsk.core.Point3D.create(L, W, 0),
        )
        lines.addByCenter(
            adsk.core.Point3D.create(L, W, 0),
            adsk.core.Point3D.create(0, W, 0),
        )
        lines.addByCenter(
            adsk.core.Point3D.create(0, W, 0),
            adsk.core.Point3D.create(0, 0, 0),
        )

        # Extrude upward by height H
        extrudes = root_comp.features.extrudeFeatures
        profs = sketch.profiles
        ext_input = extrudes.createInput(
            profs, adsk.fusion.ExtrudeFeatureInput.createNewBodyFeatureType
        )
        ext_input.setDistanceExtent(False, adsk.core.ValueInput.createByReal(H))
        ext_input.targetBody = adsk.fusion.ExtrudeFeatureTargetBody.wholeBody
        extrusion = extrudes.add(ext_input)

        # Rename body to "Frame"
        frame_body = extrusion.bodies.item(0)
        frame_body.name = "Frame"

        # Apply parametric expressions to dimensions
        # Note: In actual Fusion API, we'd link sketch dimensions to parameters
        # via expressions. Here we create the geometry with the correct dimensions.

        return frame_body

    def generate_rollers(
        self,
        positions: List[float],
        diameter: float,
        width: float,
    ) -> List["adsk.fusion.BRepBody"]:
        """Generate roller array (cylindrical bodies).

        Each roller is a cylinder of diameter D, length W (along Y-axis),
        positioned at the calculated X-axis positions.

        Args:
            positions: List of X-axis positions.
            diameter: Roller diameter D (mm).
            width: Conveyor width W (mm).

        Returns:
            List of created roller bodies.
        """
        design = self.document.product
        root_comp = design.rootComponent
        rollers: List["adsk.fusion.BRepBody"] = []

        extrudes = root_comp.features.extrudeFeatures

        for i, pos_x in enumerate(positions):
            # Create sketch on XZ plane at (pos_x, 0, H/2)
            sketches = root_comp.sketches
            xz_plane = root_comp.xZConstructionPlane

            # We need to offset the sketch to the correct X position
            # Create a temporary construction plane at the roller position
            sketch = sketches.add(xz_plane)

            # Draw circle with radius D/2 centered at (0, 0) in sketch plane
            # The sketch origin maps to (pos_x, 0, H/2) in world space
            # We use a point offset in the sketch
            center_point = adsk.core.Point3D.create(0, 0, 0)
            radius = diameter / 2.0
            circle = sketch.sketchCurves.sketchCircles.addByCenter(
                center_point, adsk.core.ValueInput.createByReal(radius)
            )

            # Extrude along Y-axis by width W
            profs = sketch.profiles
            ext_input = extrudes.createInput(
                profs, adsk.fusion.ExtrudeFeatureInput.createNewBodyFeatureType
            )
            ext_input.setDistanceExtent(
                False, adsk.core.ValueInput.createByReal(width)
            )
            ext_input.targetBody = adsk.fusion.ExtrudeFeatureTargetBody.wholeBody
            extrusion = extrudes.add(ext_input)

            roller_body = extrusion.bodies.item(0)
            roller_body.name = f"Roller_{i + 1}"

            # Translate body to position_x along X-axis
            # The extrusion was centered at origin; move it to pos_x
            transform = adsk.core.Matrix3D.create()
            transform.translation = adsk.core.Vector3D.create(pos_x, 0, 0)
            move_feats = root_comp.features.moveFeatures
            move_input = move_feats.createInput(roller_body, transform)
            move_feats.add(move_input)

            rollers.append(roller_body)

        return rollers

    def generate_supports(
        self,
        positions: List[float],
        height: float,
    ) -> List["adsk.fusion.BRepBody"]:
        """Generate support leg array (vertical rectangular boxes).

        Each support is a 40x40mm cross-section box, height H,
        positioned at calculated X-axis positions.

        Args:
            positions: List of X-axis positions.
            height: Frame height H (mm).

        Returns:
            List of created support leg bodies.
        """
        design = self.document.product
        root_comp = design.rootComponent
        supports: List["adsk.fusion.BRepBody"] = []

        extrudes = root_comp.features.extrudeFeatures
        half_width = LEG_WIDTH / 2.0  # 20mm

        for i, pos_x in enumerate(positions):
            # Create sketch on XY plane at (pos_x, 0, 0)
            sketches = root_comp.sketches
            xy_plane = root_comp.xYConstructionPlane
            sketch = sketches.add(xy_plane)

            # Draw square: (-20, -20) to (20, 20) centered at origin
            # Then translate to pos_x
            lines = sketch.sketchCurves.sketchLines
            p1 = adsk.core.Point3D.create(-half_width, -half_width, 0)
            p2 = adsk.core.Point3D.create(half_width, -half_width, 0)
            p3 = adsk.core.Point3D.create(half_width, half_width, 0)
            p4 = adsk.core.Point3D.create(-half_width, half_width, 0)

            lines.addByCenter(p1, p2)
            lines.addByCenter(p2, p3)
            lines.addByCenter(p3, p4)
            lines.addByCenter(p4, p1)

            # Extrude upward by height H
            profs = sketch.profiles
            ext_input = extrudes.createInput(
                profs, adsk.fusion.ExtrudeFeatureInput.createNewBodyFeatureType
            )
            ext_input.setDistanceExtent(
                False, adsk.core.ValueInput.createByReal(height)
            )
            ext_input.targetBody = adsk.fusion.ExtrudeFeatureTargetBody.wholeBody
            extrusion = extrudes.add(ext_input)

            support_body = extrusion.bodies.item(0)
            support_body.name = f"Leg_{i + 1}"

            # Translate to position_x along X-axis
            transform = adsk.core.Matrix3D.create()
            transform.translation = adsk.core.Vector3D.create(pos_x, 0, 0)
            move_feats = root_comp.features.moveFeatures
            move_input = move_feats.createInput(support_body, transform)
            move_feats.add(move_input)

            supports.append(support_body)

        return supports

    def generate_guards(
        self,
        length: float,
        height: float,
        width: float,
        include_guards: bool,
    ) -> List["adsk.fusion.BRepBody"]:
        """Generate side guard panels (if applicable).

        Each guard is L x G x 5mm panel.
        Left guard at Y = -W/2, right at Y = +W/2.

        Args:
            length: Conveyor length L (mm).
            height: Guard height G (mm).
            width: Conveyor width W (mm).
            include_guards: Whether to generate guards.

        Returns:
            List of created guard bodies (empty if not included).
        """
        if not include_guards:
            return []

        design = self.document.product
        root_comp = design.rootComponent
        guards: List["adsk.fusion.BRepBody"] = []

        extrudes = root_comp.features.extrudeFeatures
        half_width = width / 2.0

        for side_idx, y_position in enumerate([-half_width, half_width]):
            # Create sketch on XZ plane at (0, y_position, 0)
            sketches = root_comp.sketches
            xz_plane = root_comp.xZConstructionPlane

            # Create a construction plane at the guard's Y position
            # For simplicity, sketch on XZ plane and translate
            sketch = sketches.add(xz_plane)

            # Draw rectangle: (0,0) to (L, G)
            lines = sketch.sketchCurves.sketchLines
            p1 = adsk.core.Point3D.create(0, 0, 0)
            p2 = adsk.core.Point3D.create(length, 0, 0)
            p3 = adsk.core.Point3D.create(length, height, 0)
            p4 = adsk.core.Point3D.create(0, height, 0)

            lines.addByCenter(p1, p2)
            lines.addByCenter(p2, p3)
            lines.addByCenter(p3, p4)
            lines.addByCenter(p4, p1)

            # Extrude along Y-axis by 5mm (guard thickness)
            profs = sketch.profiles
            ext_input = extrudes.createInput(
                profs, adsk.fusion.ExtrudeFeatureInput.createNewBodyFeatureType
            )
            ext_input.setDistanceExtent(
                False, adsk.core.ValueInput.createByReal(GUARD_THICKNESS)
            )
            ext_input.targetBody = adsk.fusion.ExtrudeFeatureTargetBody.wholeBody

            # Extrude direction: along Y axis
            ext_input. extrusionDirection = adsk.core.Vector3D.create(0, 1, 0)
            extrusion = extrudes.add(ext_input)

            guard_body = extrusion.bodies.item(0)
            guard_name = "SideGuard_Left" if side_idx == 0 else "SideGuard_Right"
            guard_body.name = guard_name

            # Translate to Y position
            transform = adsk.core.Matrix3D.create()
            transform.translation = adsk.core.Vector3D.create(0, y_position, 0)
            move_feats = root_comp.features.moveFeatures
            move_input = move_feats.createInput(guard_body, transform)
            move_feats.add(move_input)

            guards.append(guard_body)

        return guards

    def cleanup_stale_components(
        self,
        expected_roller_count: int,
        expected_support_count: int,
        expected_guard_count: int,
    ) -> None:
        """Remove old components when counts decrease.

        Deletes highest-numbered components first to keep
        lowest-numbered components consistent.

        Args:
            expected_roller_count: Expected number of rollers.
            expected_support_count: Expected number of support legs.
            expected_guard_count: Expected number of side guards.
        """
        design = self.document.product
        root_comp = design.rootComponent

        # Clean up rollers
        self._cleanup_pattern(root_comp, "Roller_", expected_roller_count)

        # Clean up support legs
        self._cleanup_pattern(root_comp, "Leg_", expected_support_count)

        # Clean up side guards
        self._cleanup_pattern(root_comp, "SideGuard_", expected_guard_count)

    def _cleanup_pattern(
        self,
        root_comp: "adsk.fusion.Component",
        prefix: str,
        expected_count: int,
    ) -> None:
        """Remove bodies matching a name pattern if count exceeds expected.

        Args:
            root_comp: Root component.
            prefix: Name prefix to match (e.g., "Roller_").
            expected_count: Expected number of components.
        """
        bodies = root_comp.bodies
        to_delete = []

        for i in range(bodies.count):
            body = bodies.item(i)
            if body.name.startswith(prefix):
                to_delete.append(body)

        # Sort by name to delete highest-numbered first
        to_delete.sort(key=lambda b: b.name, reverse=True)

        if len(to_delete) > expected_count:
            delete_feats = root_comp.features.deleteFeatures
            for body in to_delete[expected_count:]:
                delete_feats.add(body)

    def save_document(self, filepath: str) -> None:
        """Save document to .f3d file.

        Args:
            filepath: Full path to save location.
        """
        if self.document:
            self.document.saveAs(filepath, adsk.core.Promise())

    def close_document(self) -> None:
        """Close the current document."""
        if self.document:
            self.app.documents.close(self.document)


def create_assembly(
    config: Dict[str, Any],
    app: "adsk.core.Application",
) -> "adsk.fusion.Document":
    """High-level function to generate a complete conveyor assembly.

    Process:
    1. Create Fusion document
    2. Create parameters
    3. Generate frame, rollers, supports, guards
    4. Return document

    Args:
        config: Validated configuration dictionary.
        app: Fusion application instance.

    Returns:
        Fusion document with complete assembly.
    """
    manager = FusionAssemblyManager(app)

    # Create document
    filename = (
        f"conveyor_{config['L']}x{config['W']}x{config['H']}_"
        f"{config['D']}D_{config['P']}P"
    )
    document = manager.create_document(filename)

    # Create parameters
    manager.create_parameters(config)

    # Calculate geometry
    from src.geometry_calculator import calculate_geometry

    geo = calculate_geometry(
        config["L"], config["P"], config["S"]
    )

    # Generate frame
    manager.generate_frame(config)

    # Generate rollers
    manager.generate_rollers(
        geo.roller_positions,
        config["D"],
        config["W"],
    )

    # Generate support legs
    manager.generate_supports(
        geo.support_positions,
        config["H"],
    )

    # Generate side guards (if applicable)
    if config["side_guards"]:
        manager.generate_guards(
            config["L"],
            config["G"],
            config["W"],
            True,
        )

    # Cleanup stale components (if re-generating)
    manager.cleanup_stale_components(
        geo.roller_count,
        geo.support_count,
        2 if config["side_guards"] else 0,
    )

    return document


def save_assembly_to_file(
    document: "adsk.fusion.Document",
    output_dir: str,
    config: Dict[str, Any],
) -> str:
    """Save generated assembly to .f3d file.

    Filename: conveyor_{L}x{W}x{H}_{D}D_{P}P.f3d

    Args:
        document: Fusion document.
        output_dir: Directory to save to.
        config: Configuration (for naming).

    Returns:
        Full filepath to saved file.
    """
    from pathlib import Path

    L = config["L"]
    W = config["W"]
    H = config["H"]
    D = config["D"]
    P = config["P"]

    filename = f"conveyor_{L}x{W}x{H}_{D}D_{P}P.f3d"
    filepath = str(Path(output_dir) / filename)

    document.saveAs(filepath, adsk.core.Promise())
    return filepath


# Standalone test helper — creates a mock config for testing
# without requiring Fusion API
def create_test_config(
    length: float = 1200,
    width: float = 450,
    height: float = 700,
    diameter: float = 50,
    roller_spacing: float = 100,
    support_spacing: float = 600,
    guard_height: float = 80,
    side_guards: bool = True,
) -> Dict[str, Any]:
    """Create a test configuration dictionary.

    Args:
        length: Conveyor length (mm).
        width: Conveyor width (mm).
        height: Frame height (mm).
        diameter: Roller diameter (mm).
        roller_spacing: Roller spacing (mm).
        support_spacing: Support leg spacing (mm).
        guard_height: Guard height (mm).
        side_guards: Include side guards.

    Returns:
        Configuration dictionary.
    """
    return {
        "L": length,
        "W": width,
        "H": height,
        "D": diameter,
        "P": roller_spacing,
        "S": support_spacing,
        "G": guard_height,
        "side_guards": side_guards,
    }


# =============================================================================
# RUNNABLE DEMO — Run from inside Fusion 360's Python environment
# =============================================================================
# To use: open Fusion 360, go to Scripts & Add-ins, create a new script,
# paste this file's path, or run from the command line inside Fusion's
# Python interpreter:
#
#     "C:\Program Files\Autodesk\Fusion 360\Fusion 360.exe" --python run.py
#
# Or paste into Fusion's Python console:
#     import sys; sys.path.append(r"path\to\fusion_conveyor_generator\src")
#     from fusion_generator import create_assembly, create_test_config
#     import adsk.core
#     app = adsk.core.Application.get()
#     config = create_test_config(length=1200, width=450, height=700,
#                                 diameter=50, roller_spacing=100,
#                                 support_spacing=600, guard_height=80,
#                                 side_guards=True)
#     doc = create_assembly(config, app)
#
# The config dict has this shape (see INTERFACE CONTRACT above):
#     {"L":1200, "W":450, "H":700, "D":50, "P":100, "S":600, "G":80, "side_guards":True}
# =============================================================================

if __name__ == "__main__":
    import sys
    import os

    print("=" * 60)
    print("  Fusion Conveyor Generator — Demo")
    print("=" * 60)

    if not _HAS_FUSION:
        print()
        print("  NOTE: Not running inside Fusion 360.")
        print("  This module requires the Fusion 360 API (adsk.*).")
        print()
        print("  To run the demo:")
        print("    1. Open Fusion 360")
        print("    2. Go to Scripts & Add-ins")
        print("    3. Create a new script pointing to this file")
        print("    4. Or run from Fusion's Python console")
        print()
        print("  For configuration preview without Fusion, use:")
        print("    python main.py --config configs/config_medium.json")
        print()

        # Still show what the config would look like
        demo_config = create_test_config()
        print("  Demo configuration (would be passed to Fusion):")
        for key, value in demo_config.items():
            print(f"    {key}: {value}")
        print()

        # Show what geometry would be generated
        # When running inside Fusion with src/ on sys.path, import directly.
        # When running from project root, use the package path.
        try:
            from geometry_calculator import calculate_geometry
        except ImportError:
            from src.geometry_calculator import calculate_geometry

        geo = calculate_geometry(
            demo_config["L"], demo_config["P"], demo_config["S"]
        )
        print(f"  Rollers:   {geo.roller_count} at positions {geo.roller_positions}")
        print(f"  Supports:  {geo.support_count} at positions {geo.support_positions}")
        guard_count = 2 if demo_config["side_guards"] else 0
        print(f"  Guards:    {guard_count}")
        print(f"  Total:     {1 + geo.roller_count + geo.support_count + guard_count}")
        print()
        sys.exit(0)

    # Running inside Fusion 360 — generate the assembly
    try:
        app = adsk.core.Application.get()
    except Exception as e:
        print(f"  ERROR: Could not get Fusion application: {e}")
        sys.exit(1)

    # Use a medium configuration by default
    config = create_test_config()
    print(f"\n  Generating conveyor: {config['L']}x{config['W']}x{config['H']} mm")
    print(f"  Rollers: {config['D']}mm diameter, {config['P']}mm spacing")
    print(f"  Supports: {config['S']}mm spacing")
    print(f"  Guards: {'Yes' if config['side_guards'] else 'No'} (height={config['G']}mm)")

    try:
        document = create_assembly(config, app)
        print(f"\n  Assembly created successfully!")
        print(f"  Document: {document.name}")
        print(f"  Components: {len(document.rootComponent.bodies)} bodies")
        print()
    except Exception as e:
        print(f"\n  ERROR during assembly generation: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

