# Orbit Wheel Zoom

A Blender 5.2 add-on that lets you scroll to zoom while holding the middle mouse
button to orbit. It wraps Blender's native orbit operator, retaining native
turntable/trackball rotation, selection pivots, cursor wrapping, and cancellation.

## Use

Hold **Middle Mouse** and move to orbit. While still holding it, scroll to zoom.
Release Middle Mouse to finish, or press Escape/right-click to cancel using your
normal orbit bindings. Wheel direction follows Blender's **Invert Wheel Zoom
Direction** preference.

Zoom during this gesture uses the **view centre**, even if Zoom to Mouse Position
is enabled. This avoids an offset jump when combining cursor zoom with Blender's
cached orbit pivot. Wheel zoom outside the gesture keeps Blender's normal behavior.

The add-on binds unmodified Middle Mouse in the 3D View. Shift+Middle Mouse pan,
Ctrl+Middle Mouse zoom, the SpaceMouse, and other editors keep their native bindings.
It supports the Blender and Blender 2.7x presets. It does not add wheel zoom inside
other modal tools (for example navigation during a transform), or replace Alt+mouse
navigation in the Industry Compatible preset.

## Install

1. Run `python3 scripts/package.py` to build `dist/orbit_wheel_zoom-1.0.0.zip`.
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

## Development and validation

The implementation is in `orbit_wheel_zoom/__init__.py`. No external Python
dependencies or Blender rebuild are required. Blender 5.2+ is required because
the wrapper tracks the native operation through `Window.modal_operators`.

The UI integration tests run in a disposable Blender window with factory settings:

```sh
blender --factory-startup --enable-event-simulate --python tests/blender_smoke.py
```

The test script installs the legacy Blender 2.7x keymap in that temporary process,
loads the repository's add-on, simulates gestures, and writes results under
`test-results/`. It does not save preferences or scene files. The window stays open
for inspection. Run it on a separate desktop when Blender is already in use.

After installation, verify startup loading with:

```sh
blender --enable-event-simulate --python tests/installed_smoke.py
```

Validated in Blender 5.2.1 LTS with the Blender 2.7x keymap: native baseline,
turntable, both wheel directions, inverted wheel direction, trackball with a
selection pivot, orthographic view, zoom-to-cursor preference with a selection
pivot, automatic depth preference, Escape/right-click cancellation, locked-camera
movement, Shift/Ctrl navigation, and disabling during an active gesture. A fresh
process also verified the installed copy and saved enablement. Camera animation
autokey/undo combinations and additional Blender versions have not been validated.

## License

GPL-2.0-or-later. See `LICENSE`.
