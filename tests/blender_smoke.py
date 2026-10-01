# SPDX-License-Identifier: GPL-2.0-or-later
"""UI integration tests; run with Blender --factory-startup --enable-event-simulate."""
import json
import math
from pathlib import Path
import sys
import traceback

import bpy
from mathutils import Quaternion, Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'test-results'
OUT.mkdir(exist_ok=True)
LOG = OUT / 'smoke.jsonl'
LOG.write_text('')
sys.path.insert(0, str(ROOT))
import orbit_wheel_zoom as addon


def log(**data):
    with LOG.open('a') as stream:
        stream.write(json.dumps(data) + '\n')


legacy = next(Path(p) / 'Blender_27x.py' for p in bpy.utils.preset_paths('keyconfig')
              if (Path(p) / 'Blender_27x.py').exists())
assert bpy.utils.keyconfig_set(str(legacy))
addon.register()
win = bpy.context.window
area = next(a for a in win.screen.areas if a.type == 'VIEW_3D')
region = next(r for r in area.regions if r.type == 'WINDOW')
space = area.spaces.active
rv = space.region_3d
inputs = bpy.context.preferences.inputs
initial_rotation = Quaternion((0.88, 0.28, 0.12, 0.35)).normalized()
bpy.data.objects['Cube'].location = (3, 0, 0)
steps = []
current = {}
passed = []


def snapshot():
    return {'distance': rv.view_distance, 'location': list(rv.view_location),
            'rotation': list(rv.view_rotation),
            'operators': [op.bl_idname for op in win.modal_operators]}


def event(typ, value='NOTHING', dx=0, dy=0, **mods):
    win.event_simulate(type=typ, value=value,
                       x=region.x + int(region.width * .62) + dx,
                       y=region.y + int(region.height * .55) + dy, **mods)


def setup(name, *, selected=False, method='TURNTABLE', perspective='PERSP',
          inverted=False, cursor=False, native=False, end='MIDDLEMOUSE',
          depth=False, camera=False):
    current.clear()
    current.update(name=name, native=native, inverted=inverted, end=end, camera=camera)
    addon._keymaps[0][1].active = not native
    inputs.use_rotate_around_active = selected
    inputs.use_mouse_depth_navigate = depth
    inputs.use_zoom_to_mouse = cursor
    inputs.invert_zoom_wheel = inverted
    inputs.view_rotate_method = method
    space.lock_camera = camera
    rv.view_perspective = 'CAMERA' if camera else perspective
    rv.view_distance = 10
    rv.view_location = (0, 0, 0)
    rv.view_rotation = initial_rotation.copy()
    current['initial'] = snapshot()
    event('MOUSEMOVE')
    log(case=name, keyconfig=bpy.context.window_manager.keyconfigs.active.name)


def orbit_started():
    s = snapshot()
    assert Quaternion(s['rotation']).rotation_difference(initial_rotation).angle > .001, s
    has_wrapper = 'VIEW3D_OT_orbit_wheel_zoom' in s['operators']
    assert has_wrapper != current['native'], s
    current['before'] = s


def zoomed():
    s = snapshot()
    factor = 1 if current['native'] else (1.2 if current['inverted'] else 1 / 1.2)
    assert math.isclose(s['distance'], current['before']['distance'] * factor, rel_tol=2e-5), s
    assert (Vector(s['location']) - Vector(current['before']['location'])).length < 1e-5, s
    current['zoomed'] = s


def continued():
    s = snapshot()
    assert math.isclose(s['distance'], current['zoomed']['distance'], rel_tol=2e-5), s
    assert Quaternion(s['rotation']).rotation_difference(
        Quaternion(current['zoomed']['rotation'])).angle > .0001, s
    assert (Vector(s['location']) - Vector(current['zoomed']['location'])).length < .1, s


def zoom_reversed():
    assert math.isclose(rv.view_distance, current['before']['distance'], rel_tol=2e-5), snapshot()


def finish_gesture():
    key = current['end']
    event(key, 'RELEASE' if key == 'MIDDLEMOUSE' else 'PRESS', dx=36, dy=20)


def finished():
    s = snapshot()
    assert not any(name in s['operators'] for name in
                   ('VIEW3D_OT_rotate', 'VIEW3D_OT_orbit_wheel_zoom')), s
    if current['end'] in {'ESC', 'RIGHTMOUSE'}:
        assert math.isclose(s['distance'], current['initial']['distance'], rel_tol=2e-5), s
        assert (Vector(s['location']) - Vector(current['initial']['location'])).length < 1e-5, s
        assert Quaternion(s['rotation']).rotation_difference(initial_rotation).angle < .001, s
        event('MIDDLEMOUSE', 'RELEASE', dx=36, dy=20)
    current['finished'] = s


def idle_checked():
    s = snapshot()
    assert Quaternion(s['rotation']).rotation_difference(
        Quaternion(current['finished']['rotation'])).angle < .001, s
    passed.append(current['name'])
    log(passed=current['name'], before=current['before'], zoomed=current['zoomed'], after=s)


cases = [
    ('native_baseline', {'native': True}),
    ('turntable', {}),
    ('inverted_wheel', {'inverted': True}),
    ('selected_trackball', {'selected': True, 'method': 'TRACKBALL'}),
    ('selected_orthographic', {'selected': True, 'perspective': 'ORTHO'}),
    ('cursor_preference_with_selection', {'selected': True, 'cursor': True}),
    ('auto_depth', {'depth': True}),
    ('escape_cancels_both', {'selected': True, 'end': 'ESC'}),
    ('right_click_cancels_both', {'selected': True, 'end': 'RIGHTMOUSE'}),
    ('locked_camera', {'camera': True}),
]
# Dismiss Blender's startup splash before the first measured gesture.
steps += [lambda: event('ESC', 'PRESS'), lambda: event('ESC', 'RELEASE'), lambda: None]
for name, options in cases:
    steps += [lambda n=name, o=options: setup(n, **o),
              lambda: event('MIDDLEMOUSE', 'PRESS'),
              lambda: event('MOUSEMOVE', dx=35, dy=20), orbit_started,
              lambda: event('WHEELUPMOUSE', 'PRESS', dx=35, dy=20), zoomed,
              lambda: event('WHEELDOWNMOUSE', 'PRESS', dx=35, dy=20), zoom_reversed,
              lambda: event('WHEELUPMOUSE', 'PRESS', dx=35, dy=20), zoomed,
              lambda: event('MOUSEMOVE', dx=36, dy=20), continued,
              finish_gesture, lambda: None, lambda: None, finished,
              lambda: event('MOUSEMOVE', dx=60, dy=20), idle_checked]


def modifier_start(shift=False, ctrl=False):
    setup('modifier_navigation')
    event('MIDDLEMOUSE', 'PRESS', shift=shift, ctrl=ctrl)


def modifier_checked(expected):
    names = snapshot()['operators']
    assert expected in names and 'VIEW3D_OT_orbit_wheel_zoom' not in names, names
    event('MIDDLEMOUSE', 'RELEASE')
    passed.append(expected)
    log(passed=expected)


steps += [lambda: modifier_start(shift=True),
          lambda: modifier_checked('VIEW3D_OT_move'), lambda: None,
          lambda: modifier_start(ctrl=True),
          lambda: modifier_checked('VIEW3D_OT_zoom'), lambda: None]


def unregister_active():
    assert 'VIEW3D_OT_orbit_wheel_zoom' in snapshot()['operators']
    addon.unregister()


def unregister_checked():
    names = snapshot()['operators']
    assert not any(name in names for name in ('VIEW3D_OT_orbit_wheel_zoom', 'VIEW3D_OT_rotate')), names
    assert not addon._keymaps
    addon.register()
    assert len(addon._keymaps) == 2
    passed.append('disable_during_orbit_and_reenable')
    log(passed=passed[-1])


steps += [lambda: setup('unregister'), lambda: event('MIDDLEMOUSE', 'PRESS'),
          unregister_active, lambda: event('MIDDLEMOUSE', 'RELEASE'),
          lambda: None, unregister_checked]


def tick():
    try:
        if steps:
            steps.pop(0)()
            return .12
        report = {'ok': True, 'passed': passed, 'blender': bpy.app.version_string}
    except Exception:
        report = {'ok': False, 'case': current.get('name'), 'state': snapshot(),
                  'error': traceback.format_exc(), 'passed': passed}
    log(**report)
    (OUT / 'summary.json').write_text(json.dumps(report, indent=2) + '\n')
    print('ORBIT_WHEEL_TEST_RESULT', json.dumps(report), flush=True)
    return None


bpy.app.timers.register(tick, first_interval=3)
