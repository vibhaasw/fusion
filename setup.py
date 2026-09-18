{
    "name": "fusion-conveyor-generator",
    "version": "1.0.0",
    "description": "Parametric Adjustable Roller Conveyor Configuration Generator for Autodesk Fusion 360",
    "author": "Fusion Hackathon Team",
    "packages": ["src"],
    "python_requires": ">=3.8",
    "install_requires": [
        'pywin32>=306; platform_system == "Windows"',
    ],
    "extras_require": {
        "test": ["pytest>=7.0"],
    },
    "entry_points": {
        "console_scripts": [
            "conveyor-generator=src.ui_handler:main",
        ],
    },
}
