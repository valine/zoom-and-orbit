# SPDX-License-Identifier: GPL-2.0-or-later
"""Test native selection and double-right-click focus in a disposable Blender UI."""
import json
import math
from pathlib import Path
import sys
import traceback

import addon_utils
import bmesh
import bpy
from bpy_extras.view3d_utils import location_3d_to_region_2d
from mathutils import Quaternion, Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'test-results'
OUT.mkdir(exist_ok=True)
LOG = OUT / 'focus.jsonl'
LOG.write_text('')
sys.path.insert(0, str(ROOT))
addon = addon_utils.enable('orbit_wheel_zoom', default_set=True)
assert Path(addon.__file__).resolve() == ROOT / 'orbit_wheel_zoom' / '__init__.py'
legacy = next(Path(p) / 'Blender_27x.py' for p in bpy.utils.preset_paths('keyconfig')
              if (Path(p) / 'Blender_27x.py').exists())
assert bpy.utils.keyconfig_set(str(legacy))
win = bpy.context.window
area = next(a for a in win.screen.areas if a.type == 'VIEW_3D')
region = next(r for r in area.regions if r.type == 'WINDOW')
space = area.spaces.active
rv = space.region_3d
prefs = bpy.context.preferences.addons['orbit_wheel_zoom'].preferences
bpy.context.preferences.view.smooth_view = 100
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)
mesh = bpy.data.meshes.new('Focus test mesh')
mesh.from_pydata([(1,-1,0),(3,-1,0),(3,1,0),(1,1,0),(5,-1,0),(5,1,0)],
                 [], [(0,1,2,3),(1,4,5,2)])
target = bpy.data.objects.new('Focus target', mesh)
bpy.context.collection.objects.link(target)
target.location = (2,1,0)
other_mesh = mesh.copy()
other = bpy.data.objects.new('Other selection', other_mesh)
bpy.context.collection.objects.link(other)
other.location = (-7,1,0)
curve_data = bpy.data.curves.new('Curve focus test', 'CURVE')
curve_data.dimensions = '3D'
spline = curve_data.splines.new('BEZIER')
spline.bezier_points.add(1)
for point, co in zip(spline.bezier_points, [(3,2,0),(5,2,0)]):
    point.co = co
    point.handle_left_type = point.handle_right_type = 'AUTO'
curve = bpy.data.objects.new('Curve control points', curve_data)
bpy.context.collection.objects.link(curve)
steps = []
current = {}
passed = []


def log(**data):
    with LOG.open('a') as stream:
        stream.write(json.dumps(data) + '\n')


def event(typ, value='NOTHING', *, shift=False):
    xy = current.get('xy', (region.width//2, region.height//2))
    win.event_simulate(type=typ, value=value, x=region.x+xy[0], y=region.y+xy[1], shift=shift)


def setup(name, mode='OBJECT', *, method='CENTER', enabled=True, miss=False, shifted=False):
    addon._keymaps[1][1].value = 'DOUBLE_CLICK'
    if bpy.context.object is not None and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    target.hide_set(mode == 'CURVE')
    other.hide_set(mode == 'CURVE')
    curve.hide_set(mode != 'CURVE')
    bpy.ops.object.select_all(action='DESELECT')
    active = curve if mode == 'CURVE' else target
    active.select_set(True)
    bpy.context.view_layer.objects.active = active
    if mode in {'VERT', 'EDGE', 'FACE'}:
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.context.tool_settings.mesh_select_mode = tuple(mode == m for m in ('VERT','EDGE','FACE'))
        bpy.ops.mesh.select_all(action='DESELECT')
    elif mode == 'CURVE':
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.curve.select_all(action='DESELECT')
    else:
        target.select_set(False)
        other.select_set(True)
        bpy.context.view_layer.objects.active = other
    rv.view_perspective = 'ORTHO'
    rv.view_rotation = Quaternion((1,0,0,0))
    rv.view_location = (0,0,0)
    rv.view_distance = 20
    space.shading.type = 'SOLID'
    space.overlay.show_overlays = True
    space.show_gizmo = False
    rv.update()
    prefs.double_right_click_focus = enabled
    prefs.double_click_focus_method = method
    bpy.context.scene.cursor.location = (8,9,3)
    bpy.context.scene.cursor.rotation_euler = (.2,.3,.4)
    points = {'OBJECT': (4,1,0), 'VERT': (3,0,0), 'EDGE': (4,0,0),
              'FACE': (4,1,0), 'CURVE': (3,2,0)}
    centers = dict(points, OBJECT=(5,1,0))
    current.clear()
    current.update(name=name, mode=mode, point=points[mode], center=centers[mode],
                   method=method, enabled=enabled, miss=miss, shifted=shifted,
                   cursor=[list(row) for row in bpy.context.scene.cursor.matrix])
    log(case=name)


def position():
    xy = location_3d_to_region_2d(region, rv, Vector(current['point']))
    assert xy is not None
    current['xy'] = (20, 20) if current['miss'] else tuple(round(x) for x in xy)
    event('MOUSEMOVE')


def single_checked():
    assert rv.view_location.length < 1e-5, list(rv.view_location)
    assert math.isclose(rv.view_distance, 20, rel_tol=1e-5)
    if current['mode'] == 'OBJECT' and not current['miss']:
        assert bpy.context.view_layer.objects.active == target
    # Blender's event_simulate API cannot produce double-clicks. Dispatch the
    # second press through the real operator/keymap; test physical double-click
    # recognition separately with focus_physical.py and an agent-seat mouse.
    addon._keymaps[1][1].value = 'PRESS'


def focused():
    addon._keymaps[1][1].value = 'DOUBLE_CLICK'
    center = Vector(current['center']) if current['enabled'] and not current['miss'] and not current['shifted'] else Vector((0,0,0))
    assert (rv.view_location-center).length < 1e-4, (list(rv.view_location),list(center))
    if current['method'] == 'CENTER':
        assert math.isclose(rv.view_distance, 20, rel_tol=1e-5), rv.view_distance
    else:
        assert not math.isclose(rv.view_distance, 20, rel_tol=1e-3), rv.view_distance
    cursor = bpy.context.scene.cursor.matrix
    assert all(abs(cursor[i][j]-current['cursor'][i][j]) < 1e-6 for i in range(4) for j in range(4))
    assert rv.view_rotation.rotation_difference(Quaternion((1,0,0,0))).angle < .001
    if current['enabled'] and not current['miss'] and not current['shifted']:
        mode = current['mode']
        if mode == 'OBJECT':
            assert bpy.context.selected_objects == [target], [o.name for o in bpy.context.selected_objects]
        elif mode in {'VERT','EDGE','FACE'}:
            bm = bmesh.from_edit_mesh(target.data)
            elements = {'VERT': bm.verts, 'EDGE': bm.edges, 'FACE': bm.faces}[mode]
            selected = [e for e in elements if e.select]
            assert len(selected) == 1, (mode, len(selected))
        elif mode == 'CURVE':
            # RNA reads the original curve; flush the edit-mode selection first.
            bpy.ops.object.mode_set(mode='OBJECT')
            assert sum(p.select_control_point for p in curve.data.splines[0].bezier_points) == 1
    passed.append(current['name'])
    log(passed=current['name'], center=list(rv.view_location), distance=rv.view_distance)


steps += [lambda: event('ESC','PRESS'), lambda: event('ESC','RELEASE'), lambda: None]
for name, mode, options in [
    ('object_geometry_center', 'OBJECT', {}),
    ('vertex', 'VERT', {}),
    ('edge', 'EDGE', {}),
    ('face', 'FACE', {}),
    ('curve_control_point', 'CURVE', {}),
    ('empty_space', 'OBJECT', {'miss': True}),
    ('disabled_feature', 'OBJECT', {'enabled': False}),
    ('shift_double_click', 'OBJECT', {'shifted': True}),
    ('frame_selected_option', 'OBJECT', {'method': 'FRAME'}),
]:
    steps += [lambda n=name,m=mode,o=options: setup(n,m,**o), position,
              lambda: event('RIGHTMOUSE','PRESS'), lambda: event('RIGHTMOUSE','RELEASE'),
              single_checked,
              lambda: event('RIGHTMOUSE','PRESS',shift=current['shifted']),
              lambda: event('RIGHTMOUSE','RELEASE',shift=current['shifted']),
              lambda: None, lambda: None, lambda: None, focused]


def tick():
    try:
        if steps:
            with bpy.context.temp_override(window=win,area=area,region=region):
                steps.pop(0)()
            return .15
        report = {'ok': True, 'passed': passed, 'blender': bpy.app.version_string}
    except Exception:
        addon._keymaps[1][1].value = 'DOUBLE_CLICK'
        report = {'ok': False, 'case': current.get('name'), 'error': traceback.format_exc(), 'passed': passed}
    log(**report)
    (OUT/'focus-summary.json').write_text(json.dumps(report,indent=2)+'\n')
    print('ORBIT_FOCUS_TEST',json.dumps(report),flush=True)
    return None


bpy.app.timers.register(tick, first_interval=3)
