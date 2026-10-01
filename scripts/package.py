#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Build a small installable Blender add-on ZIP using only the standard library."""
import ast
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory
from zipfile import ZIP_DEFLATED, ZipFile


def main():
    root = Path(__file__).resolve().parents[1]
    module = root / 'orbit_wheel_zoom' / '__init__.py'
    tree = ast.parse(module.read_text())
    info = next(ast.literal_eval(node.value) for node in tree.body
                if isinstance(node, ast.Assign)
                and any(isinstance(target, ast.Name) and target.id == 'bl_info'
                        for target in node.targets))
    version = '.'.join(map(str, info['version']))
    minimum = '.'.join(map(str, info['blender']))
    destination = root / 'dist'
    destination.mkdir(exist_ok=True)
    instructions = (
        f"{info['name']} {version}\nBlender {minimum} or newer\n\n"
        '1. Leave the downloaded ZIP zipped.\n'
        '2. In Blender: Edit > Preferences > Add-ons > menu > Install from Disk.\n'
        '3. Select the ZIP and enable Zoom and Orbit if it is not already checked.\n'
        '   Save Preferences if preference auto-save is off.\n\n'
        'Hold Middle Mouse and move to orbit; scroll while holding it to zoom.\n'
        'Double-right-click to select and center. Options are in Preferences.\n\n'
        'Documentation, source, and updates:\n'
        'https://github.com/valine/zoom-and-orbit\n'
    )
    with TemporaryDirectory(prefix='package-', dir=destination) as temporary:
        package = Path(temporary) / 'zoom-and-orbit.zip'
        with ZipFile(package, 'w', ZIP_DEFLATED) as archive:
            archive.write(module, 'orbit_wheel_zoom/__init__.py')
            archive.write(root / 'LICENSE', 'orbit_wheel_zoom/LICENSE')
            archive.writestr('orbit_wheel_zoom/INSTALL.txt', instructions)
        versioned = destination / f'orbit_wheel_zoom-{version}.zip'
        shutil.copyfile(package, versioned)
        package.replace(destination / 'zoom-and-orbit.zip')
    for path in (versioned, destination / 'zoom-and-orbit.zip'):
        print(f'{path}: {path.stat().st_size:,} bytes')


if __name__ == '__main__':
    main()
