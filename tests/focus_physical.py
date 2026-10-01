# SPDX-License-Identifier: GPL-2.0-or-later
"""Check actual double-right-click recognition on a disposable agent desktop.

Run without --enable-event-simulate. Right-double-click the coordinates written to
test-results/focus-physical-ready.json (window-local, top-left origin), first for an
object, then for a face. Results appear in focus-physical.json. No preferences save.
"""
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
sys.path.insert(0,str(ROOT))
addon = addon_utils.enable('orbit_wheel_zoom',default_set=True)
legacy = next(Path(p)/'Blender_27x.py' for p in bpy.utils.preset_paths('keyconfig')
              if (Path(p)/'Blender_27x.py').exists())
bpy.utils.keyconfig_set(str(legacy))
bpy.context.preferences.view.show_splash = False
win = bpy.context.window
area = next(a for a in win.screen.areas if a.type=='VIEW_3D')
region = next(r for r in area.regions if r.type=='WINDOW')
rv = area.spaces.active.region_3d
cube = bpy.data.objects['Cube']
cube.location=(3,1,0)
stage='object'
passed=[]


def reset_view():
    rv.view_perspective='ORTHO'
    rv.view_rotation=Quaternion((1,0,0,0))
    rv.view_location=(0,0,0)
    rv.view_distance=20
    area.spaces.active.show_gizmo=False
    bpy.context.scene.cursor.location=(9,8,7)


with bpy.context.temp_override(window=win,area=area,region=region):
    bpy.ops.object.select_all(action='DESELECT')
reset_view()


def ready():
    target=Vector((3,1,1 if stage=='face' else 0))
    xy=location_3d_to_region_2d(region,rv,target)
    (OUT/'focus-physical-ready.json').write_text(json.dumps({
        'stage':stage,'x':round(region.x+xy.x),'y':round(win.height-region.y-xy.y),
        'target':list(target),'window_size':[win.width,win.height]})+'\n')
    return None


def watch():
    global stage
    try:
        target=Vector((3,1,1 if stage=='face' else 0))
        if (rv.view_location-target).length > 1e-4:
            return .2
        with bpy.context.temp_override(window=win,area=area,region=region):
            assert math.isclose(rv.view_distance,20,rel_tol=1e-5)
            assert (bpy.context.scene.cursor.location-Vector((9,8,7))).length < 1e-6
            assert bpy.context.active_object == cube
            if stage=='face':
                selected=[f for f in bmesh.from_edit_mesh(cube.data).faces if f.select]
                assert len(selected)==1 and selected[0].normal.z > .99
            passed.append(stage)
            if stage=='object':
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.context.tool_settings.mesh_select_mode=(False,False,True)
                bpy.ops.mesh.select_all(action='DESELECT')
                stage='face'
                reset_view()
                bpy.app.timers.register(ready,first_interval=.5)
                return .2
        report={'ok':True,'passed':passed,'method':'actual agent-seat double-right-clicks'}
    except Exception:
        report={'ok':False,'passed':passed,'error':traceback.format_exc()}
    (OUT/'focus-physical.json').write_text(json.dumps(report,indent=2)+'\n')
    print('FOCUS_PHYSICAL_TEST',json.dumps(report),flush=True)
    return None


bpy.app.timers.register(ready,first_interval=3)
bpy.app.timers.register(watch,first_interval=3.5)
