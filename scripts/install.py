# SPDX-License-Identifier: GPL-2.0-or-later
"""Install the packaged add-on and enable it in the current user's saved preferences.

Run with: blender -b --factory-startup --python scripts/install.py
"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil

import addon_utils
import bpy

ROOT = Path(__file__).resolve().parents[1]
ZIP = ROOT / 'dist' / 'orbit_wheel_zoom-1.1.0.zip'
MODULE = 'orbit_wheel_zoom'
assert bpy.app.version >= (5, 2, 0), 'Blender 5.2 or newer is required'
assert ZIP.is_file(), 'Run python3 scripts/package.py first'
preferences_file = Path(bpy.utils.user_resource('CONFIG', path='userpref.blend'))
backup = None
if preferences_file.exists():
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    backup = preferences_file.with_name(preferences_file.name + '.before-orbit-wheel-' + stamp)
    shutil.copy2(preferences_file, backup)
    assert 'FINISHED' in bpy.ops.wm.read_userpref()


def preferences_snapshot():
    inputs = bpy.context.preferences.inputs
    return {
        'keyconfig': bpy.context.preferences.keymap.active_keyconfig,
        'inputs': {p.identifier: getattr(inputs, p.identifier)
                   for p in inputs.bl_rna.properties
                   if p.type in {'BOOLEAN', 'INT', 'FLOAT', 'STRING', 'ENUM'}},
        'addons': sorted(a.module for a in bpy.context.preferences.addons if a.module != MODULE),
    }


before = preferences_snapshot()
assert 'FINISHED' in bpy.ops.preferences.addon_install(filepath=str(ZIP), overwrite=True)
module = addon_utils.enable(MODULE, default_set=True, persistent=True)
assert module is not None and addon_utils.check(MODULE) == (True, True)
assert preferences_snapshot() == before, 'Unexpected change to existing input/keymap/add-on settings'
installed = Path(module.__file__).resolve()
expected = ROOT / MODULE / '__init__.py'
assert installed.read_bytes() == expected.read_bytes(), 'Installed code differs from the repository'
assert 'FINISHED' in bpy.ops.wm.save_userpref()
report = {
    'installed': str(installed),
    'enabled': True,
    'preferences': str(preferences_file),
    'preferences_backup': str(backup) if backup else None,
    'keyconfig': before['keyconfig'],
    'sha256': hashlib.sha256(installed.read_bytes()).hexdigest(),
    'blender': bpy.app.version_string,
}
result_dir = ROOT / 'test-results'
result_dir.mkdir(exist_ok=True)
(result_dir / 'installation.json').write_text(json.dumps(report, indent=2) + '\n')
print('ORBIT_WHEEL_INSTALLED', json.dumps(report), flush=True)
