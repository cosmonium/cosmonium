#
#This file is part of Cosmonium.
#
#Copyright (C) 2018-2022 Laurent Deru.
#
#Cosmonium is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
#
#Cosmonium is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with Cosmonium.  If not, see <https://www.gnu.org/licenses/>.
#

from functools import partial
from . import settings
from .bodyclass import bodyClasses


class StatesProvider():
    def __init__(self, engine, time, camera, autopilot, gui, debug):
        self.states = {
            'debug-jump': lambda: settings.debug_jump,
            'debug-lod-freeze': lambda: settings.debug_lod_freeze,
            'debug-lod-frustum': lambda: settings.debug_lod_frustum,
            'debug-lod-show-bb': lambda: settings.debug_lod_show_bb,
            'debug-lod-split-merge': lambda: settings.debug_lod_split_merge,
            'debug-shadow-frustum': lambda: settings.debug_shadow_frustum,
            'has-object-selected': lambda: engine.selected is not None,
            'shader-debug-coord': lambda: settings.shader_debug_coord,
            'shader-debug-raymarching-canvas': lambda: settings.shader_debug_raymarching_canvas,
            'shader-debug-raymarching-slice': lambda: settings.shader_debug_raymarching_slice,
            'ship-editable': lambda: engine.ship.editable,
            'show-asterisms': lambda: settings.show_asterisms,
            'show-atmospheres': lambda: settings.show_atmospheres,
            'show-boundaries': lambda: settings.show_boundaries,
            'show-clouds': lambda: settings.show_clouds,
            'show-ecliptic-grid': lambda: settings.show_ecliptic_grid,
            'show-equatorial-grid': lambda: settings.show_equatorial_grid,
            'show-orbits': lambda: settings.show_orbits,
            'show-rotation-axis': lambda: settings.show_rotation_axis,
            'show-reference-axis': lambda: settings.show_reference_axis,
            'stereoscopic-framebuffer': lambda: settings.stereoscopic_framebuffer,
            'red-blue-stereo': lambda: settings.red_blue_stereo,
            'side-by-side-stereo': lambda: settings.side_by_side_stereo,
            'stereo-swap-eyes': lambda: settings.stereo_swap_eyes,
            }
        for display_render_info in ['fps', 'ms', 'none']:
            self.states['display-render-info-' + display_render_info] = lambda mode=display_render_info: settings.display_render_info == mode

        for class_name in bodyClasses.classes.keys():
            self.states[class_name + '-shown'] = partial(bodyClasses.get_show, class_name)
        for class_name in bodyClasses.classes.keys():
            self.states['label-' + class_name + '-shown'] = partial(bodyClasses.get_show_label, class_name)
        for class_name in bodyClasses.classes.keys():
            self.states['orbit-' + class_name + '-shown'] = partial(bodyClasses.get_show_orbit, class_name)

        for shader_debug_mode in ['default', 'diffuse', 'heightmap', 'normal', 'normalmap', 'picking', 'shadows']:
            self.states['debug-shader-fragment-mode-' + shader_debug_mode] = lambda mode=shader_debug_mode: settings.shader_debug_fragment_shader == mode

    def get_state(self, state_name):
        state_evaluator = self.states.get(state_name)
        if state_evaluator:
            state = state_evaluator()
        else:
            print(f"ERROR: Unknown state {state_name}")
            state = None
        return state
