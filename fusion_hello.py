#!/usr/bin/env python3
"""Fusion 360 API Hello World — minimal connectivity test.

Verifies that the Autodesk Fusion 360 SDK is accessible and demonstrates
basic document/sketch/extrude operations.

Run this INSIDE Fusion 360's Python environment:
  - Via Scripts & Add-ins → create new script pointing to this file
  - Or paste into Fusion's Python console after adding src/ to sys.path

This script is NOT meant to run from a standard Python interpreter —
the adsk.* modules only exist inside Fusion 360.
"""

import sys

# ---------------------------------------------------------------------------
# Fusion API import — only succeeds inside Fusion 360
# ---------------------------------------------------------------------------
try:
    import adsk.core
    import adsk.fusion
    _HAS_FUSION = True
except ImportError:
    _HAS_FUSION = False


def run_hello_world() -> None:
    """Create a 10mm cube in a new Fusion document and save it.

    Steps:
    1. Get Fusion application instance
    2. Create new design document
    3. Sketch a 10x10 rectangle on XY plane
    4. Extrude 10mm upward
    5. Save to /tmp/test_fusion_hello.f3d
    """

    if not _HAS_FUSION:
        print("ERROR: Not running inside Fusion 360.")
        print("The adsk.* modules are only available in Fusion's Python environment.")
        print()
        print("To run this script:")
        print("  1. Open Fusion 360")
        print("  2. Go to Scripts & Add-ins")
        print("  3. Create a new script and point it to this file")
        print("  4. Or paste the code into Fusion's Python console")
        sys.exit(1)

    # 1. Get the Fusion application
    app = adsk.core.Application.get()
    print("Connected to Fusion 360.")

    # 2. Create a new design document
    doc = app.documents.add(adsk.fusion.DocumentTypes.DesignDocumentType)
    print(f"Created new document: {doc.name}")

    # 3. Access the root component and create a sketch on XY plane
    design = doc.product
    root = design.rootComponent

    sketches = root.sketches
    xy_plane = root.xYConstructionPlane
    sketch = sketches.add(xy_plane)

    # Draw a 10x10 rectangle
    lines = sketch.sketchCurves.sketchLines
    d = 10.0  # mm
    lines.addByCenter(
        adsk.core.Point3D.create(0, 0, 0),
        adsk.core.Point3D.create(d, 0, 0),
    )
    lines.addByCenter(
        adsk.core.Point3D.create(d, 0, 0),
        adsk.core.Point3D.create(d, d, 0),
    )
    lines.addByCenter(
        adsk.core.Point3D.create(d, d, 0),
        adsk.core.Point3D.create(0, d, 0),
    )
    lines.addByCenter(
        adsk.core.Point3D.create(0, d, 0),
        adsk.core.Point3D.create(0, 0, 0),
    )
    print("Sketch: 10mm x 10mm rectangle on XY plane.")

    # 4. Extrude the profile 10mm upward
    extrudes = root.features.extrudeFeatures
    ext_input = extrudes.createInput(
        sketch.profiles,
        adsk.fusion.ExtrudeFeatureInput.createNewBodyFeatureType,
    )
    ext_input.setDistanceExtent(
        False, adsk.core.ValueInput.createByReal(d)
    )
    ext_input.targetBody = adsk.fusion.ExtrudeFeatureTargetBody.wholeBody
    extrusion = extrudes.add(ext_input)
    print("Extruded 10mm — cube created.")

    # 5. Save the document
    save_path = "/tmp/test_fusion_hello.f3d"
    doc.saveAs(save_path, adsk.core.Promise())
    print(f"Document saved to: {save_path}")

    # 6. Summary
    body_count = root.bodies.count
    print()
    print("=" * 50)
    print("  Fusion Hello World — Complete")
    print("=" * 50)
    print(f"  Bodies in document: {body_count}")
    print(f"  Saved to: {save_path}")
    print("  Open this file in Fusion 360 to verify.")
    print("=" * 50)


if __name__ == "__main__":
    try:
        run_hello_world()
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
