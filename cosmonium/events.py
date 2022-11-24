# -*- coding: utf-8 -*-
#
#This file is part of Cosmonium.
#
#Copyright (C) 2018-2021 Laurent Deru.
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

from direct.showbase.DirectObject import DirectObject

class EventsDispatcher(DirectObject):
    def __init__(self, engine, time, camera, autopilot, gui, debug):
        DirectObject.__init__(self)
        self.engine = engine
        self.time = time
        self.camera = camera
        self.autopilot = autopilot
        self.gui = gui
        self.debug = debug
        self.accept('exit', self.engine.userExit)
        self.accept('gui-search-object', self.gui.open_find_object)
        self.accept('escape-dispatch', self.gui.escape)
        self.accept('cancel', self.engine.reset_all)
        self.accept('toggle-fullscreen', self.engine.toggle_fullscreen)
        self.accept('zoom-in', self.camera.zoom, [1.05])
        self.accept('zoom-out', self.camera.zoom, [1.0/1.05])
        self.accept('reset-zoom', self.camera.reset_zoom)
        self.accept('gui-toggle-menubar', self.gui.toggle_menu)
        self.accept('gui-show-menubar', self.gui.show_menu)
        self.accept('gui-show-preferences', self.gui.show_preferences)
        self.accept('gui-show-editor', self.gui.show_editor)
        self.accept('gui-show-time-editor', self.gui.show_time_editor)

        self.accept('gui-show-info', self.gui.show_info)
        self.accept('gui-show-help', self.gui.show_help)
        self.accept('gui-show-select-screenshots', self.gui.show_select_screenshots)
        self.accept('debug-connect-pstats', self.engine.connect_pstats)
        self.accept('debug-toggle-filled-wireframe', self.engine.toggle_filled_wireframe)
        self.accept('debug-toggle-wireframe', self.engine.toggle_wireframe)
        self.accept('toggle-hdr', self.engine.toggle_hdr)
        self.accept('debug-toggle-buffer-viewer', self.debug.toggle_buffer_viewer)
        self.accept('debug-dump-octree-stats', self.engine.universe.dumpOctreeStats)
        self.accept('debug-dump-octree', self.engine.universe.dumpOctree)
        self.accept('debug-freeze-lod', self.debug.toggle_lod_freeze)
        self.accept('debug-dump-objects-stats', self.debug.dump_object_stats)
        self.accept('debug-dump-objects-info', self.debug.dump_object_info)
        self.accept('debug-toggle-split-merge-log', self.debug.toggle_split_merge_debug)
        self.accept('debug-toggle-shader-debug-coord', self.debug.toggle_shader_debug_coord)
        self.accept('debug-toggle-bounding-boxes', self.debug.toggle_bb)
        self.accept('debug-toggle-lod-frustum', self.debug.toggle_frustum)
        self.accept('debug-toggle-shadows-frustum', self.debug.toggle_shadow_frustum)
        self.accept('save-screenshot', self.engine.save_screenshot)
        self.accept('save-screenshot-no-gui', self.engine.save_screenshot_no_annotation)
        self.accept('debug-scene-ls', self.debug.list_scene)
        self.accept('debug-scene-explore', self.debug.open_scene_explorer)
        self.accept('debug-scene-analyze', self.debug.analyse_scene)
        self.accept('debug-print-tasks', self.debug.print_tasks)
        self.accept('debug-shader-fragment-mode', self.debug.set_shader_fragment_debug)
        for shader_debug_mode in ['default', 'diffuse', 'heightmap', 'normal', 'normalmap', 'picking', 'shadows']:
            self.accept('debug-shader-fragment-mode-' + shader_debug_mode, self.debug.set_shader_fragment_debug, [shader_debug_mode])
        self.accept('debug-toggle-shader-raymarching-canvas', self.debug.toggle_shader_debug_raymarching_canvas)
        self.accept('debug-toggle-shader-debug-raymarching_slice', self.debug.toggle_shader_debug_raymarching_slice)

        self.accept('goto-front', self.autopilot.go_to_front, [None, None, None, False])
        self.accept('goto-illuminated-front', self.autopilot.go_to_front, [None, None, None, True])
        self.accept('goto-selected', self.autopilot.go_to_object)
        self.accept('center-selected', self.engine.center_on_object)
        self.accept('debug-toggle-jump', self.debug.toggle_jump)

        self.accept('goto-north', self.autopilot.go_north)
        self.accept('goto-south', self.autopilot.go_south)
        self.accept('goto-meridian', self.autopilot.go_meridian)

        self.accept('align-ecliptic', self.autopilot.align_on_ecliptic)
        self.accept('align-equatorial', self.autopilot.align_on_equatorial)

        self.accept('goto-surface', self.autopilot.go_to_surface)

        self.accept('select-home', self.engine.go_home)

        self.accept('save-cel-url', self.engine.save_celurl)
        self.accept('load-cel-url', self.engine.load_celurl)
        self.accept('open-script', self.gui.show_open_script)

        self.accept('set-j2000-date', self.time.set_J2000_date)
        self.accept('set-current-date', self.time.set_current_date)
        self.accept('accelerate-time-10', self.time.accelerate_time, [10.0])
        self.accept('accelerate-time-2', self.time.accelerate_time, [2.0])
        self.accept('slow-time-10', self.time.slow_time, [10.0])
        self.accept('slow-time-2', self.time.slow_time, [2.0])
        self.accept('invert-time', self.time.invert_time)
        self.accept('toggle-freeze-time', self.time.toggle_freeze_time)
        self.accept('set-real-time', self.time.set_real_time)

        self.accept('follow-selected', self.engine.follow_selected)
        self.accept('sync-selected', self.engine.sync_selected)
        self.accept('track-selected', self.engine.toggle_track_selected)
        self.accept('control-selected', self.engine.control_selected)

        self.accept('decrease-ambient', self.engine.incr_ambient, [-0.05])
        self.accept('increase-ambient', self.engine.incr_ambient, [+0.05])

        self.accept('decrease-limit-magnitude', self.engine.incr_limit_magnitude, [-0.1])
        self.accept('increase-limit-magnitude', self.engine.incr_limit_magnitude, [+0.1])
        self.accept('decrease-exposure', self.engine.incr_exposure, [-0.1])
        self.accept('increase-exposure', self.engine.incr_exposure, [+0.1])

        #Render
        self.accept('toggle-atmosphere', self.engine.toggle_atmosphere)
        self.accept('toggle-rotation-axis', self.engine.toggle_rotation_axis)
        self.accept('toggle-reference-axis', self.engine.toggle_reference_axis)
        self.accept('toggle-constellations-boundaries', self.engine.toggle_boundaries)
        #self.accept('toggle-shadows', self.toggle_shadows)
        self.accept('toggle-clouds', self.engine.toggle_clouds)
        #self.accept('toggle-nightsides', self.engine.toggle_nightsides)
        self.accept('toggle-orbits', self.engine.toggle_orbits)
        #self.accept('toggle-comet-tails', self.engine.toggle_comet_tails)
        self.accept('toggle-body-class-galaxy', self.engine.toggle_body_class, ['galaxy'])
        #self.accept('toggle-globular', self.engine.toggle_globulars)
        self.accept('toggle-equatorial-grid', self.engine.toggle_grid_equatorial)
        self.accept('toggle-ecliptic-grid', self.engine.toggle_grid_ecliptic)
        self.accept('toggle-asterisms', self.engine.toggle_asterisms)
        #self.accept('toggle-nebulae', self.engine.toggle_nebulae)

        #Orbits
        self.accept('toggle-orbit-star', self.engine.toggle_orbit, ['star'])
        self.accept('toggle-orbit-planet', self.engine.toggle_orbit, ['planet'])
        self.accept('toggle-orbit-dwarfplanet', self.engine.toggle_orbit, ['dwarfplanet'])
        self.accept('toggle-orbit-moon', self.engine.toggle_orbit, ['moon'])
        self.accept('toggle-orbit-minormoon', self.engine.toggle_orbit, ['minormoon'])
        self.accept('toggle-orbit-comet', self.engine.toggle_orbit, ['comet'])
        self.accept('toggle-orbit-asteroid', self.engine.toggle_orbit, ['asteroid'])
        self.accept('toggle-orbit-spacecraft', self.engine.toggle_orbit, ['spacecraft'])

        #Labels
        self.accept('toggle-label-galaxy', self.engine.toggle_label, ['galaxy'])
        self.accept('toggle-label-globular', self.engine.toggle_label, ['globular'])
        self.accept('toggle-label-star', self.engine.toggle_label, ['star'])
        self.accept('toggle-label-planet', self.engine.toggle_label, ['planet'])
        self.accept('toggle-label-dwarfplanet', self.engine.toggle_label, ['dwarfplanet'])
        self.accept('toggle-label-moon', self.engine.toggle_label, ['moon'])
        self.accept('toggle-label-minormoon', self.engine.toggle_label, ['minormoon'])
        self.accept('toggle-label-lostmoon', self.engine.toggle_label, ['lostmoon'])
        self.accept('toggle-label-comet', self.engine.toggle_label, ['comet'])
        self.accept('toggle-label-asteroid', self.engine.toggle_label, ['asteroid'])
        self.accept('toggle-label-interstellar', self.engine.toggle_label, ['interstellar'])
        self.accept('toggle-label-spacecraft', self.engine.toggle_label, ['spacecraft'])
        self.accept('toggle-label-constellation', self.engine.toggle_label, ['constellation'])
        self.accept('toggle-label-location', self.engine.toggle_label, ['location'])

        self.accept('toggle-hud', self.gui.toggle_hud)

        for i in range(0, 10):
            self.accept("select-object-{}".format(i), self.engine.select_planet, [i])

        self.accept('debug-print-info', self.debug.print_info)
        self.accept('toggle-fly-mode', self.engine.toggle_fly_mode)

        self.accept('toggle-stereoscopic-framebuffer', self.engine.toggle_stereoscopic_framebuffer)
        self.accept('toggle-red_blue-stereo', self.engine.toggle_red_blue_stereo)
        self.accept('toggle-side-by_side-stereo', self.engine.toggle_side_by_side_stereo)
        self.accept('toggle-swap-eyes', self.engine.toggle_swap_eyes)

        for display_render_info in ['fps', 'ms', 'none']:
            self.accept('set-display-render-info-' + display_render_info, self.gui.set_display_render_info, [display_render_info])

