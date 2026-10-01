# SPDX-License-Identifier: GPL-2.0-or-later
"""Native orbit with wheel zoom, plus double-right-click selection focus."""

bl_info = {
    "name": "Orbit Wheel Zoom",
    "author": "Lukas",
    "version": (1, 1, 0),
    "blender": (5, 2, 0),
    "location": "3D View: Middle Mouse + wheel; double Right Mouse to focus",
    "description": "Wheel zoom during orbit and double-right-click to select and center",
    "category": "3D View",
}

import bpy
from bpy.props import BoolProperty, EnumProperty
from mathutils import Vector

_keymaps = []
_generation = None


class VIEW3D_OT_orbit_wheel_zoom(bpy.types.Operator):
    bl_idname = "view3d.orbit_wheel_zoom"
    bl_label = "Orbit with Wheel Zoom"
    bl_description = "Orbit normally; scroll while holding Middle Mouse to zoom"
    bl_options = {"INTERNAL"}

    @classmethod
    def poll(cls, context):
        return (context.area is not None and context.area.type == 'VIEW_3D'
                and context.region is not None and context.region.type == 'WINDOW'
                and bpy.ops.view3d.rotate.poll())

    def invoke(self, context, event):
        if event.type != 'MIDDLEMOUSE' or event.value != 'PRESS':
            return {'CANCELLED', 'PASS_THROUGH'}

        self._timer = None
        self._generation = _generation
        self._window_manager = context.window_manager
        before = {op.as_pointer() for op in context.window.modal_operators}
        result = bpy.ops.view3d.rotate('INVOKE_DEFAULT', use_cursor_init=True)
        if 'RUNNING_MODAL' not in result:
            return result

        native = next((op for op in context.window.modal_operators
                       if op.as_pointer() not in before), None)
        if native is None:
            # The native operation still owns the gesture if interception is unavailable.
            return {'FINISHED'}

        self._native_pointer = native.as_pointer()
        self._native_idname = native.bl_idname
        # Register AFTER native orbit: modal handlers are visited newest first.
        # Native orbit owns cursor grabbing; this wrapper must not grab it again.
        context.window_manager.modal_handler_add(self)
        self._timer = context.window_manager.event_timer_add(0.2, window=context.window)
        return {'RUNNING_MODAL'}

    def _cleanup(self):
        if self._timer is not None:
            try:
                self._window_manager.event_timer_remove(self._timer)
            except (ReferenceError, RuntimeError):
                pass
            self._timer = None

    def _finish(self):
        self._cleanup()
        # Native orbit must also receive its release/cancellation event.
        return {'FINISHED', 'PASS_THROUGH'}

    def modal(self, context, event):
        if self._generation is not _generation or context.window is None:
            return self._finish()

        native = next((op for op in context.window.modal_operators
                       if op.as_pointer() == self._native_pointer), None)
        if native is None or context.area is None or context.region is None:
            return self._finish()

        if ((event.type == 'MIDDLEMOUSE' and event.value == 'RELEASE')
                or (event.type == 'ESC' and event.value == 'PRESS')):
            return self._finish()

        # A customized modal keymap may switch the native operator to pan/drag-zoom.
        # Leave wheel handling to that operator until orbit resumes.
        if (native.bl_idname == self._native_idname
                and event.type in {'WHEELUPMOUSE', 'WHEELDOWNMOUSE'}
                and event.value == 'PRESS'):
            if bpy.ops.view3d.zoom.poll():
                delta = 1 if event.type == 'WHEELUPMOUSE' else -1
                if context.preferences.inputs.invert_zoom_wheel:
                    delta = -delta
                # Cursor-directed zoom changes the offset that native orbit caches.
                # Centre zoom preserves that state, including selection/depth pivots.
                bpy.ops.view3d.zoom('EXEC_DEFAULT', delta=delta, use_cursor_init=False)
            return {'RUNNING_MODAL'}

        # PASS_THROUGH alone keeps this handler alive AND reaches native orbit.
        # Combining it with RUNNING_MODAL stops subsequent modal handlers in Blender.
        return {'PASS_THROUGH'}

    def cancel(self, context):
        self._cleanup()


def _preferences(context):
    entry = context.preferences.addons.get(__name__)
    return entry.preferences if entry is not None else None


def _object_selection_center(context):
    """Use visible geometry bounds for objects, including evaluated modifiers."""
    depsgraph = context.evaluated_depsgraph_get()
    points = []
    for obj in context.selected_objects:
        if not obj.visible_get(view_layer=context.view_layer, viewport=context.space_data):
            continue
        evaluated = obj.evaluated_get(depsgraph)
        bounds = evaluated.bound_box
        if all(tuple(corner) == (-1.0, -1.0, -1.0) for corner in bounds):
            points.append(evaluated.matrix_world.translation)
        else:
            points.extend(evaluated.matrix_world @ Vector(corner) for corner in bounds)
    if not points:
        return None
    return Vector(tuple((min(p[i] for p in points) + max(p[i] for p in points)) * .5
                        for i in range(3)))


def _center_selection(context):
    # Reuse native element-centre calculation and smooth navigation. The cursor is
    # only a synchronous carrier for the target; it is restored before any redraw.
    cursor = context.scene.cursor
    saved_location = cursor.location.copy()
    try:
        if context.mode == 'OBJECT':
            center = _object_selection_center(context)
            if center is None:
                return False
            cursor.location = center
        elif 'FINISHED' not in bpy.ops.view3d.snap_cursor_to_selected('EXEC_DEFAULT'):
            return False
        if context.region_data.view_perspective == 'CAMERA' and not context.space_data.lock_camera:
            # As with Frame Selected, leave an unlocked camera to navigate the view.
            bpy.ops.view3d.view_camera('EXEC_DEFAULT')
        return 'FINISHED' in bpy.ops.view3d.view_center_cursor('INVOKE_DEFAULT')
    finally:
        cursor.location = saved_location


class VIEW3D_OT_orbit_wheel_select_and_center(bpy.types.Operator):
    bl_idname = "view3d.orbit_wheel_select_and_center"
    bl_label = "Select and Center"
    bl_description = "Select the item under the mouse and center the view on it"
    bl_options = {'UNDO', 'INTERNAL'}

    @classmethod
    def poll(cls, context):
        prefs = _preferences(context)
        return (context.area is not None and context.area.type == 'VIEW_3D'
                and context.region is not None and context.region.type == 'WINDOW'
                and context.region_data is not None
                and (prefs is None or prefs.double_right_click_focus)
                and (context.mode in {'OBJECT', 'POSE'}
                     or (context.mode.startswith('EDIT_') and context.mode != 'EDIT_TEXT'))
                and bpy.ops.view3d.select.poll()
                and bpy.ops.view3d.view_center_cursor.poll())

    def invoke(self, context, event):
        # FINISHED means a hit even when the clicked item was already selected.
        # A miss must not refocus the previous selection, or pan into empty space.
        selected = bpy.ops.view3d.select(
            'EXEC_DEFAULT', location=(event.mouse_region_x, event.mouse_region_y),
            extend=False, deselect=False, toggle=False, deselect_all=False,
            select_passthrough=False)
        if 'FINISHED' not in selected:
            return {'CANCELLED'}
        prefs = _preferences(context)
        if prefs is not None and prefs.double_click_focus_method == 'FRAME':
            if bpy.ops.view3d.view_selected.poll():
                bpy.ops.view3d.view_selected('INVOKE_DEFAULT', use_all_regions=False)
        else:
            _center_selection(context)
        return {'FINISHED'}


class OrbitWheelZoomPreferences(bpy.types.AddonPreferences):
    bl_idname = __name__

    double_right_click_focus: BoolProperty(
        name="Double Right Click to Focus", default=True,
        description="Select and center objects or editable elements with a double right click")
    double_click_focus_method: EnumProperty(
        name="Focus Behavior", default='CENTER',
        items=(('CENTER', "Center Only", "Center the selection while keeping the current zoom"),
               ('FRAME', "Frame Selected", "Center and zoom to fit the selection")))

    def draw(self, context):
        layout = self.layout
        layout.label(text="Hold Middle Mouse to orbit, then scroll to zoom.")
        layout.label(text="Zoom during orbit uses the view centre.")
        layout.label(text="Wheel direction follows Blender's navigation preferences.")
        layout.separator()
        layout.prop(self, "double_right_click_focus")
        row = layout.row()
        row.enabled = self.double_right_click_focus
        row.prop(self, "double_click_focus_method")


_classes = (VIEW3D_OT_orbit_wheel_zoom, VIEW3D_OT_orbit_wheel_select_and_center,
            OrbitWheelZoomPreferences)


def register():
    global _generation
    _generation = object()
    for cls in _classes:
        bpy.utils.register_class(cls)
    keyconfig = bpy.context.window_manager.keyconfigs.addon
    if keyconfig is not None:
        keymap = keyconfig.keymaps.new(name='3D View', space_type='VIEW_3D')
        item = keymap.keymap_items.new(VIEW3D_OT_orbit_wheel_zoom.bl_idname,
                                     'MIDDLEMOUSE', 'PRESS')
        _keymaps.append((keymap, item))
        item = keymap.keymap_items.new(VIEW3D_OT_orbit_wheel_select_and_center.bl_idname,
                                     'RIGHTMOUSE', 'DOUBLE_CLICK')
        _keymaps.append((keymap, item))


def unregister():
    global _generation
    _generation = None
    for keymap, item in _keymaps:
        keymap.keymap_items.remove(item)
    _keymaps.clear()
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
