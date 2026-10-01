#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Build an installable legacy Blender add-on ZIP using only the standard library."""
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

root = Path(__file__).resolve().parents[1]
destination = root / 'dist' / 'orbit_wheel_zoom-1.1.0.zip'
destination.parent.mkdir(exist_ok=True)
with ZipFile(destination, 'w', ZIP_DEFLATED) as archive:
    archive.write(root / 'orbit_wheel_zoom' / '__init__.py', 'orbit_wheel_zoom/__init__.py')
    archive.write(root / 'LICENSE', 'orbit_wheel_zoom/LICENSE')
    archive.write(root / 'README.md', 'orbit_wheel_zoom/README.md')
print(destination)
