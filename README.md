# Orbit Wheel Zoom
### Zoom and orbit in one fluid mouse gesture


Hold the middle mouse button down to orbit and scroll to zoom at the same time. Your mouse can still register scroll events even when the middle mouse button is held down. This addon takes advantage of that fact, and allows you you to orbit and zoom at the same time.

![Scrolling to zoom while continuously orbiting Suzanne in Blender](docs/media/orbit-wheel-zoom.gif)

Scroll zoom during continuous middle-mouse orbit. [Watch the full-resolution video](docs/media/orbit-wheel-zoom.mp4).

## Use

Hold **Middle Mouse** and move to orbit. While still holding it, scroll to zoom.

**Double-right-click** an object, vertex, edge, face, or curve control point to
select it and center the view.

In Preferences → Add-ons → **Orbit Wheel Zoom**, choose **Frame Selected** instead
of **Center Only** if you want double-right-click to also zoom to fit. The feature
can also be disabled there. It is intended for right-click-select keymaps, including
your Blender 2.7x preset. Single clicks and Shift/Ctrl/Alt selection shortcuts retain
their regular bindings. It operates in Object, Pose, and applicable Edit modes;
paint/sculpt strokes and text editing are excluded.

The add-on binds unmodified Middle Mouse in the 3D View. Shift+Middle Mouse pan,
Ctrl+Middle Mouse zoom, the SpaceMouse, and other editors keep their native bindings.
It supports the Blender and Blender 2.7x presets. 

## Install

1. Run `python3 scripts/package.py` to build `dist/orbit_wheel_zoom-1.1.0.zip`.
2. In Blender's Preferences → Add-ons, use the menu's **Install from Disk** command.
3. Select the ZIP, then enable **Orbit Wheel Zoom** and save preferences if auto-save
   is disabled.

Disable the add-on in Preferences to restore normal MMB behavior. No existing
keymap entries are removed or rewritten.

For a scripted local install, run `blender -b --factory-startup --python
scripts/install.py` after packaging. This backs up `userpref.blend`, reads your
existing preferences, installs and enables the add-on, and saves preferences.
Restart any already-open Blender instance to load it. The installer records the
installation path and backup location in `test-results/installation.json`.


## License

GPL-2.0-or-later. See `LICENSE`.
