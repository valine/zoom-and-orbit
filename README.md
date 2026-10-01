# Zoom and Orbit
### Zoom and orbit in one fluid mouse gesture


Hold the middle mouse button to orbit, then scroll while still holding it to zoom.
Zoom and Orbit adds this gesture to Blender's native orbit controls. It also
includes optional double-right-click selection and centering.

**[Download Zoom and Orbit (.zip)](https://github.com/valine/zoom-and-orbit/releases/latest/download/zoom-and-orbit.zip)**

Free and open source · Blender 5.2+ · Tested in Blender 5.2.1

![Scrolling to zoom while continuously orbiting Suzanne in Blender](docs/media/orbit-wheel-zoom.gif)

Scroll zoom during continuous middle-mouse orbit.
[Video demo](docs/media/orbit-wheel-zoom-social.mp4) ·
[Original HDR demo, cropped to Blender](docs/media/orbit-wheel-zoom.mp4)

## Install

1. **[Download the add-on ZIP](https://github.com/valine/zoom-and-orbit/releases/latest/download/zoom-and-orbit.zip)** and leave it zipped.
2. In Blender, open **Edit → Preferences → Add-ons**. Open the menu in the
   upper-right corner and choose **Install from Disk**. Select the downloaded ZIP.
3. Enable **Zoom and Orbit** if it is not already checked. You're ready to orbit
   and scroll. If preference auto-save is off, click **Save Preferences**.

For future updates, download the same ZIP and install it again. Disable the
add-on in Preferences to restore normal MMB behavior.

## Use

Hold **Middle Mouse** and move to orbit. While still holding it, scroll to zoom.

**Double-right-click** an object, vertex, edge, face, or curve control point to
select it and center the view.

In Preferences → Add-ons → **Zoom and Orbit**, choose **Frame Selected** instead
of **Center Only** if you want double-right-click to also zoom to fit. The feature
can also be disabled there. It is intended for right-click-select keymaps, including
the Blender 2.7x preset. Single clicks and Shift/Ctrl/Alt selection shortcuts retain
their regular bindings. It operates in Object, Pose, and applicable Edit modes;
paint/sculpt strokes and text editing are excluded.

The add-on binds unmodified Middle Mouse in the 3D View. Shift+Middle Mouse pan,
Ctrl+Middle Mouse zoom, the SpaceMouse, and other editors keep their native bindings.
It supports the Blender and Blender 2.7x presets. 

Zoom during orbit uses the view center and follows Blender's wheel-direction
preference. No existing keymap entries are removed or rewritten.

## Development

To build the installable ZIP from source, run `python3 scripts/package.py`.
The builder writes a versioned ZIP and `dist/zoom-and-orbit.zip`, the filename used
for the direct release download. Demo media and development tools are excluded
from the installation package.

For a scripted local install, run `blender -b --factory-startup --python
scripts/install.py` after packaging. This backs up `userpref.blend`, reads your
existing preferences, installs and enables the add-on, and saves preferences.
Restart any already-open Blender instance to load it. The installer records the
installation path and backup location in `test-results/installation.json`.

To regenerate the cropped HDR video, annotated GIF, and SDR social video, run
`python3 scripts/render_demo.py /path/to/original.mp4` with FFmpeg (including
zscale, libsvtav1, and libx264) and Pycairo installed. The default crop and 400-nit
tone mapping match the supplied recording. The mouse indicator illustrates the
gesture; it is not a recording of individual input events.


## License

GPL-2.0-or-later. See `LICENSE`.
