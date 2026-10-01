# SPDX-License-Identifier: GPL-2.0-or-later
"""Verify a fresh Blender process loads the installed add-on and saved keymap.

Run WITHOUT --factory-startup: blender --enable-event-simulate --python tests/installed_smoke.py
This never saves preferences or a scene.
"""
import json
import math
from pathlib import Path
import traceback

import addon_utils
import bpy
import orbit_wheel_zoom

root = Path(__file__).resolve().parents[1]
out = root / 'test-results' / 'installed-smoke.json'
out.parent.mkdir(exist_ok=True)
win = bpy.context.window
area = max((a for a in win.screen.areas if a.type == 'VIEW_3D'), key=lambda a: a.width * a.height)
region = next(r for r in area.regions if r.type == 'WINDOW')
rv = area.spaces.active.region_3d
report = {'module': orbit_wheel_zoom.__file__,
          'version': list(orbit_wheel_zoom.bl_info['version']),
          'enabled': addon_utils.check('orbit_wheel_zoom'),
          'keyconfig': bpy.context.window_manager.keyconfigs.active.name,
          'blender': bpy.app.version_string}
start = {}


def event(typ, value='NOTHING', dx=0):
    win.event_simulate(type=typ, value=value,
                       x=region.x + region.width // 2 + dx,
                       y=region.y + region.height // 2)


def loaded():
    assert report['enabled'] == (True, True), report
    assert Path(report['module']).resolve() != root / 'orbit_wheel_zoom' / '__init__.py', report
    assert len(orbit_wheel_zoom._keymaps) == 2
    assert report['version'] == [1, 1, 0]
    report['focus_method'] = bpy.context.preferences.addons['orbit_wheel_zoom'].preferences.double_click_focus_method


def active():
    names = [op.bl_idname for op in win.modal_operators]
    assert 'VIEW3D_OT_orbit_wheel_zoom' in names and 'VIEW3D_OT_rotate' in names, names
    start['distance'] = rv.view_distance
    start['rotation'] = rv.view_rotation.copy()


def zoomed():
    factor = 1.2 if bpy.context.preferences.inputs.invert_zoom_wheel else 1 / 1.2
    assert math.isclose(rv.view_distance, start['distance'] * factor, rel_tol=2e-5)
    report.update(distance_before=start['distance'], distance_after=rv.view_distance)


def continued():
    assert rv.view_rotation.rotation_difference(start['rotation']).angle > .001


def finished():
    names = [op.bl_idname for op in win.modal_operators]
    assert not any(n in names for n in ('VIEW3D_OT_rotate', 'VIEW3D_OT_orbit_wheel_zoom')), names


steps = [loaded, lambda: event('ESC', 'PRESS'), lambda: event('ESC', 'RELEASE'),
         lambda: event('MOUSEMOVE'), lambda: event('MIDDLEMOUSE', 'PRESS'),
         lambda: event('MOUSEMOVE', dx=20), active,
         lambda: event('WHEELUPMOUSE', 'PRESS', dx=20), zoomed,
         lambda: event('MOUSEMOVE', dx=30), continued,
         lambda: event('MIDDLEMOUSE', 'RELEASE', dx=30), lambda: None, finished]


def tick():
    try:
        if steps:
            steps.pop(0)()
            return .15
        report['ok'] = True
    except Exception:
        report.update(ok=False, error=traceback.format_exc())
    out.write_text(json.dumps(report, indent=2) + '\n')
    print('ORBIT_WHEEL_INSTALLED_TEST', json.dumps(report), flush=True)
    return None


bpy.app.timers.register(tick, first_interval=3)
