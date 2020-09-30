# -*- coding: utf-8 -*-
#
#This file is part of Cosmonium.
#
#Copyright (C) 2018-2019 Laurent Deru.
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

from __future__ import print_function
from __future__ import absolute_import

from panda3d.core import LVector3, LVector2
from pandamenu.menu import DropDownMenu, PopupMenu

from ..bodies import Star, StellarBody
from ..systems import StellarSystem, SimpleSystem
from ..universe import Universe
from ..astro import units
from ..astro import bayer
from ..astro.units import toUnit
from ..fonts import fontsManager, Font
from ..catalogs import objectsDB
from ..bodyclass import bodyClasses
from ..appstate import AppState
from ..extrainfo import extra_info
from ..celestia.cel_url import CelUrl
from .. import utils
from .. import settings
#TODO: should only be used by Cosmonium main class
from ..parsers.configparser import configParser

from .hud import HUD
from .query import Query
from .editor import ParamEditor
from .textwindow import TextWindow
from .infopanel import InfoPanel
from .preferences import Preferences
from .clipboard import create_clipboard
from .browser import Browser
from .time import TimeEditor

about_text = """# Cosmonium

**Version**: V%s
Copyright 2018-2019 Laurent Deru


**Website**: http://github.com/cosmonium/cosmonium


This program is free software; you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation; either version 3 of the License, or (at your option) any later
version.


This program uses several third-party libraries which are subject to their own
licenses, see Third-Party.md for the complete list.
""" % settings.version

def menu_text(name, shortcut=None):
    if shortcut is not None:
        return name + '>' + shortcut
    else:
        return name

class Gui(object):
    def __init__(self, cosmonium, time, camera, mouse, nav, autopilot):
        self.cosmonium = cosmonium
        self.time = time
        self.camera = camera
        self.mouse = mouse
        self.nav = nav
        self.autopilot = autopilot
        if base.pipe is not None:
            self.screen_width = base.pipe.getDisplayWidth()
            self.screen_height = base.pipe.getDisplayHeight()
        else:
            self.screen_width = 1
            self.screen_height = 1
        self.calc_scale()
        font = fontsManager.get_font(settings.hud_font, Font.STYLE_NORMAL)
        if font is not None:
            self.font = font.load()
        else:
            self.font = None
        self.clipboard = create_clipboard()
        self.hud = HUD(self.scale, self.font)
        self.query = Query(self.scale, self.font, settings.query_color, settings.query_text_size, settings.query_suggestion_text_size, settings.query_delay)
        self.last_fps = globalClock.getRealTime()
        self.width = 0
        self.height = 0
        self.update_size(self.screen_width, self.screen_height)
        self.popup_menu = None
        self.opened_windows = []
        self.editor = ParamEditor(font_family=settings.markdown_font, font_size=settings.ui_font_size, owner=self)
        self.time_editor = TimeEditor(self.time, font_family=settings.markdown_font, font_size=settings.ui_font_size, owner=self)
        self.info = InfoPanel(self.scale, settings.markdown_font, owner=self)
        self.preferences = Preferences(self.cosmonium, settings.markdown_font, owner=self)
        self.help = TextWindow('Help', self.scale, settings.markdown_font, owner=self)
        self.help.load('control.md')
        self.license = TextWindow('License', self.scale, settings.markdown_font, owner=self)
        self.license.load('COPYING.md')
        self.about = TextWindow('About', self.scale, settings.markdown_font, owner=self)
        self.about.set_text(about_text)
        self.create_menubar()
        self.browser = Browser(self.scale, owner=self)
        if settings.show_hud:
            self.show_hud()
        else:
            self.hide_hud()
        if settings.show_menubar:
            self.show_menu()
        else:
            self.hide_menu()

    def calc_scale(self):
        self.scale = LVector2(settings.ui_scale[0] / self.screen_width * 2.0,  settings.ui_scale[1] / self.screen_height * 2.0)

    def register_events(self, event_ctrl):
        event_ctrl.accept('control-q', self.cosmonium.userExit)
        event_ctrl.accept('enter', self.open_find_object)
        event_ctrl.accept('escape', self.escape)
        event_ctrl.accept('alt-enter', self.cosmonium.toggle_fullscreen)
        event_ctrl.accept(',', self.camera.zoom, [1.05])
        event_ctrl.accept('shift-,-repeat', self.camera.zoom, [1.05])
        event_ctrl.accept('.', self.camera.zoom, [1.0/1.05])
        event_ctrl.accept('shift-.-repeat', self.camera.zoom, [1.0/1.05])
        event_ctrl.accept('control-r', self.camera.reset_zoom)
        event_ctrl.accept('control-m', self.toggle_menu)
        event_ctrl.accept('control-p', self.show_preferences)
        event_ctrl.accept('control-e', self.show_editor)

        event_ctrl.accept('f1', self.show_info)
        event_ctrl.accept('shift-f1', self.show_help)
        event_ctrl.accept('f2', self.cosmonium.connect_pstats)
        event_ctrl.accept('f3', self.cosmonium.toggle_filled_wireframe)
        event_ctrl.accept('shift-f3', self.cosmonium.toggle_wireframe)
        event_ctrl.accept('f4', self.cosmonium.toggle_hdr)
        event_ctrl.accept("f5", base.bufferViewer.toggleEnable)
        event_ctrl.accept('f7', self.cosmonium.universe.dumpOctreeStats)
        event_ctrl.accept('shift-f7', self.cosmonium.universe.dumpOctree)
        event_ctrl.accept('f8', self.toggle_lod_freeze)
        event_ctrl.accept('shift-f8', self.dump_object_info)
        event_ctrl.accept('shift-control-f8', self.dump_object_info_2)
        event_ctrl.accept('control-f8', self.toggle_split_merge_debug)
        event_ctrl.accept('f9', self.toggle_shader_debug_coord)
        event_ctrl.accept('shift-f9', self.toggle_bb)
        event_ctrl.accept('control-f9', self.toggle_frustum)
        event_ctrl.accept('shift-control-f9', self.toggle_shadow_frustum)
        event_ctrl.accept('f10', self.cosmonium.save_screenshot)
        event_ctrl.accept('shift-f10', self.cosmonium.save_screenshot_no_annotation)
        event_ctrl.accept('f11', render.ls)
        event_ctrl.accept('shift-f11', render.explore)
        event_ctrl.accept('f12', render.analyze)

        event_ctrl.accept('f', self.cosmonium.follow_selected)
        event_ctrl.accept('y', self.cosmonium.sync_selected)
        event_ctrl.accept('t', self.cosmonium.toggle_track_selected)
        event_ctrl.accept('control-t', self.cosmonium.control_selected)

        event_ctrl.accept('d', self.autopilot.go_to_front, [None, None, None, False])
        event_ctrl.accept('shift-d', self.autopilot.go_to_front, [None, None, None, True])
        event_ctrl.accept('g', self.autopilot.go_to_object)
        event_ctrl.accept('c', self.autopilot.center_on_object)
        event_ctrl.accept('control-j', self.toggle_jump)

        event_ctrl.accept('shift-n', self.autopilot.go_north)
        event_ctrl.accept('shift-s', self.autopilot.go_south)
        event_ctrl.accept('shift-r', self.autopilot.go_meridian)

        event_ctrl.accept('shift-t', self.autopilot.go_system_top)
        event_ctrl.accept('shift-f', self.autopilot.go_system_front)
        event_ctrl.accept('shift-i', self.autopilot.go_system_side)

        event_ctrl.accept('shift-e', self.autopilot.align_on_ecliptic)
        event_ctrl.accept('shift-q', self.autopilot.align_on_equatorial)
        event_ctrl.accept('#', self.autopilot.change_distance, [-0.1])

        event_ctrl.accept('control-g', self.autopilot.go_to_surface)

        event_ctrl.accept('h', self.cosmonium.go_home)

        event_ctrl.accept('control-c', self.save_celurl)
        event_ctrl.accept('control-v', self.load_celurl)

        event_ctrl.accept('shift-j', self.time.set_J2000_date)
        event_ctrl.accept('!', self.time.set_current_date)
        event_ctrl.accept('l', self.time.accelerate_time, [10.0])
        event_ctrl.accept('shift-l', self.time.accelerate_time, [2.0])
        event_ctrl.accept('k', self.time.slow_time, [10.0])
        event_ctrl.accept('shift-k', self.time.slow_time, [2.0])
        event_ctrl.accept('j', self.time.invert_time)
        event_ctrl.accept('space', self.time.toggle_freeze_time)
        event_ctrl.accept('\\', self.time.set_real_time)

        event_ctrl.accept('{', self.cosmonium.incr_ambient, [-0.05])
        event_ctrl.accept('}', self.cosmonium.incr_ambient, [+0.05])

        #Render
        event_ctrl.accept('control-a', self.cosmonium.toggle_atmosphere)
        event_ctrl.accept('shift-a', self.cosmonium.toggle_rotation_axis)
        event_ctrl.accept('shift-control-r', self.cosmonium.toggle_reference_axis)
        event_ctrl.accept('control-b', self.cosmonium.toggle_boundaries)
        #event_ctrl.accept('control-e', self.toggle_shadows)
        event_ctrl.accept('i', self.cosmonium.toggle_clouds)
        #event_ctrl.accept('control-l', self.cosmonium.toggle_nightsides)
        event_ctrl.accept('o', self.cosmonium.toggle_orbits)
        #event_ctrl.accept('control-t', self.cosmonium.toggle_comet_tails)
        event_ctrl.accept('u', self.cosmonium.toggle_body_class, ['galaxy'])
        #event_ctrl.accept('shift-u', self.cosmonium.toggle_globulars)
        event_ctrl.accept(';', self.cosmonium.toggle_grid_equatorial)
        event_ctrl.accept(':', self.cosmonium.toggle_grid_ecliptic)
        event_ctrl.accept('/', self.cosmonium.toggle_asterisms)
        #event_ctrl.accept('^', self.cosmonium.toggle_nebulae)

        #Orbits
        event_ctrl.accept('shift-control-b', self.cosmonium.toggle_orbit, ['star'])
        event_ctrl.accept('shift-control-p', self.cosmonium.toggle_orbit, ['planet'])
        event_ctrl.accept('shift-control-d', self.cosmonium.toggle_orbit, ['dwarfplanet'])
        event_ctrl.accept('shift-control-m', self.cosmonium.toggle_orbit, ['moon'])
        event_ctrl.accept('shift-control-o', self.cosmonium.toggle_orbit, ['minormoon'])
        event_ctrl.accept('shift-control-c', self.cosmonium.toggle_orbit, ['comet'])
        event_ctrl.accept('shift-control-a', self.cosmonium.toggle_orbit, ['asteroid'])
        event_ctrl.accept('shift-control-s', self.cosmonium.toggle_orbit, ['spacecraft'])

        #Labels
        event_ctrl.accept('e', self.cosmonium.toggle_label, ['galaxy'])
        #event_ctrl.accept('shift-e', self.toggle_label, ['globular'])
        event_ctrl.accept('b', self.cosmonium.toggle_label, ['star'])
        event_ctrl.accept('p', self.cosmonium.toggle_label, ['planet'])
        event_ctrl.accept('shift-p', self.cosmonium.toggle_label, ['dwarfplanet'])
        event_ctrl.accept('m', self.cosmonium.toggle_label, ['moon'])
        event_ctrl.accept('shift-m', self.cosmonium.toggle_label, ['minormoon'])
        event_ctrl.accept('shift-w', self.cosmonium.toggle_label, ['comet'])
        event_ctrl.accept('w', self.cosmonium.toggle_label, ['asteroid'])
        event_ctrl.accept('n', self.cosmonium.toggle_label, ['spacecraft'])
        event_ctrl.accept('=', self.cosmonium.toggle_label, ['constellation'])
        #event_ctrl.accept('&', self.toggle_label, ['location'])

        event_ctrl.accept('v', self.toggle_hud)

        for i in range(0, 10):
            event_ctrl.accept("%d" % i, self.cosmonium.select_planet, [i])

        event_ctrl.accept('shift-h', self.cosmonium.print_debug)
        event_ctrl.accept('shift-y', self.cosmonium.toggle_fly_mode)

    def window_closed(self, window):
        if window in self.opened_windows:
            self.opened_windows.remove(window)

    def escape(self):
        if len(self.opened_windows) != 0:
            window = self.opened_windows.pop()
            window.hide()
        else:
            self.cosmonium.reset_all()

    def left_click(self):
        body = self.mouse.get_over()
        if body != None and self.cosmonium.selected == body:
            self.autopilot.center_on_object(body)
            return
        self.cosmonium.select_body(body)

    def right_click(self):
        self.popup_menu = self.create_popup_menu(self.mouse.get_over())

    def save_celurl(self):
        state = AppState()
        state.save_state(self.cosmonium)
        cel_url = CelUrl()
        cel_url.store_state(self.cosmonium, state)
        url = cel_url.encode()
        self.clipboard.copy_to(url)
        print(url)

    def load_celurl(self):
        url = self.clipboard.copy_from()
        if url is None or url == '': return
        print(url)
        state = None
        cel_url = CelUrl()
        if cel_url.parse(url):
            state = cel_url.convert_to_state(self.cosmonium)
        if state is not None:
            state.apply_state(self.cosmonium)
        else:
            print("Invalid URL: '%s'" % url)
            self.update_info(_("Invalid URL..."))

    def toggle_jump(self):
        settings.debug_jump = not settings.debug_jump
        if settings.debug_jump:
            self.update_info(_("Instant move"))
        else:
            self.update_info(_("Normal move"))

    def toggle_lod_freeze(self):
        settings.debug_lod_freeze = not settings.debug_lod_freeze
        if settings.debug_lod_freeze:
            self.update_info(_("Freeze LOD"))
        else:
            self.update_info(_("Unfreeze LOD"))

    def toggle_bb(self):
        settings.debug_lod_show_bb = not settings.debug_lod_show_bb
        self.cosmonium.trigger_check_settings = True

    def toggle_frustum(self):
        settings.debug_lod_frustum = not settings.debug_lod_frustum
        self.cosmonium.trigger_check_settings = True

    def toggle_shadow_frustum(self):
        settings.debug_shadow_frustum = not settings.debug_shadow_frustum
        self.cosmonium.trigger_check_settings = True

    def dump_object_info(self):
        selected = self.cosmonium.selected
        if selected is None: return
        if not isinstance(selected, StellarBody): return
        if selected.surface is not None:
            shape = selected.surface.shape
            if shape.patchable:
                print("Surface")
                shape.dump_tree()
        if selected.clouds is not None:
            shape = selected.clouds.shape
            if shape.patchable:
                print("Clouds")
                shape.dump_tree()

    def dump_object_info_2(self):
        selected = self.cosmonium.selected
        if selected is None: return
        if not isinstance(selected, StellarBody): return
        if selected.surface is not None:
            shape = selected.surface.shape
            if shape.patchable:
                print("Surface")
                shape.dump_patches()
        if selected.clouds is not None:
            shape = selected.clouds.shape
            if shape.patchable:
                print("Clouds")
                shape.dump_patches()

    def toggle_split_merge_debug(self):
        settings.debug_lod_split_merge = not settings.debug_lod_split_merge

    def toggle_stereoscopic_framebuffer(self):
        settings.stereoscopic_framebuffer = not settings.stereoscopic_framebuffer
        if settings.stereoscopic_framebuffer:
            settings.red_blue_stereo = False
            settings.side_by_side_stereo = False
        configParser.save()

    def toggle_red_blue_stereo(self):
        settings.red_blue_stereo = not settings.red_blue_stereo
        if settings.red_blue_stereo:
            settings.stereoscopic_framebuffer = False
            settings.side_by_side_stereo = False
        configParser.save()

    def toggle_side_by_side_stereo(self):
        settings.side_by_side_stereo = not settings.side_by_side_stereo
        if settings.side_by_side_stereo:
            settings.red_blue_stereo = False
            settings.stereoscopic_framebuffer = False
        configParser.save()

    def toggle_swap_eyes(self):
        settings.stereo_swap_eyes = not settings.stereo_swap_eyes
        configParser.save()

    def set_render_fps(self):
        settings.display_fps = True
        settings.display_ms = False

    def set_render_ms(self):
        settings.display_fps = False
        settings.display_ms = True

    def set_render_none(self):
        settings.display_fps = False
        settings.display_ms = False

    def set_shader_fragment_debug(self, mode):
        settings.shader_debug_fragment_shader = mode
        self.cosmonium.trigger_check_settings = True

    def toggle_shader_debug_coord(self):
        settings.shader_debug_coord = not settings.shader_debug_coord
        self.cosmonium.trigger_check_settings = True

    def toggle_shader_debug_raymarching_canvas(self):
        settings.shader_debug_raymarching_canvas = not settings.shader_debug_raymarching_canvas
        self.cosmonium.trigger_check_settings = True

    def toggle_shader_debug_raymarching_slice(self):
        settings.shader_debug_raymarching_slice = not settings.shader_debug_raymarching_slice
        self.cosmonium.trigger_check_settings = True

    def create_main_menu_items(self):
        return (
                (menu_text(_('_Find object'), 'Enter'), 0, self.open_find_object),
                0,
                (menu_text(_('_Save URL'), 'Control-C'), 0, self.save_celurl),
                (menu_text(_('_Load URL'), 'Control-V'), 0, self.load_celurl),
                0,
                (menu_text(_('Go to _home'), 'H'), 0, self.cosmonium.go_home),
                0,
                (menu_text(_('_Preferences')), 0, self.show_preferences),
                0,
                (menu_text(_('_Quit'), 'Control-Q'), 0, self.cosmonium.userExit),
                )

    def create_time_menu_items(self):
        return (
                (menu_text(_('_Increase rate 10x'), 'L'), 0, self.time.accelerate_time, 10.0),
                (menu_text(_('I_ncrease rate 2x'), 'Shift-L'), 0, self.time.accelerate_time, 2.0),
                (menu_text(_('_Decrease rate 10x'), 'K'), 0, self.time.slow_time, 10.0),
                (menu_text(_('D_ecrease rate 2x'), 'Shift-K'), 0, self.time.slow_time, 2.0),
                (menu_text(_('_Reverse time'), 'J'), 0, self.time.invert_time),
                (menu_text(_('_Freeze time'), 'Space'), 0, self.time.toggle_freeze_time),
                (menu_text(_('_Set real time'), '\\'), 0, self.time.set_real_time),
                0,
                (menu_text(_('Set _time...')), 0, self.time_editor.show),
                (menu_text(_('Set _current time'), '!'), 0, self.time.set_current_date),
                (menu_text(_('Set _J2000 epoch'), 'Shift-J'), 0, self.time.set_J2000_date),
                )

    def create_select_menu_items(self):
        has_selected = self.cosmonium.selected is not None
        orbiting_bodies = self.create_orbiting_bodies_menu_items(self.cosmonium.selected)
        orbits = self.create_orbits_menu_items(self.cosmonium.selected)
        return (
            (menu_text(_('_Info'), 'F1'), 0, self.show_info if has_selected else 0),
            (menu_text(_('_Edit'), 'Control-E'), 0, self.show_editor if has_selected else 0),
            0,
            (menu_text(_('_Go to'), 'G'), 0, self.autopilot.go_to_object if has_selected else 0),
            (menu_text(_('Go to f_ront'), 'D'), 0, self.autopilot.go_to_front if has_selected else 0),
            (menu_text(_('Go to _surface'), 'Control-G'), 0, self.autopilot.go_to_surface if has_selected else 0),
            0,
            (menu_text(_('_Follow'), 'F'), 0, self.cosmonium.follow_selected if has_selected else 0),
            (menu_text(_('S_ync'), 'Y'), 0, self.cosmonium.sync_selected if has_selected else 0),
            0,
            (menu_text(_('_Reset navigation'), 'Escape'), 0, self.escape if has_selected else 0),
            0,
            (menu_text(_("Orbiting bodies")), 0, orbiting_bodies),
            (menu_text(_("Orbits")), 0, orbits),
        )

    def create_camera_menu_items(self):
        has_selected = self.cosmonium.selected is not None
        controllers = []
        for controller in self.cosmonium.camera_controllers:
            controllers.append((controller.get_name(),
                                self.cosmonium.camera_controller is controller,
                                self.cosmonium.set_camera_controller if self.cosmonium.ship.supports_camera_mode(controller.camera_mode) else 0,
                                controller))
        ships = []
        for ship in self.cosmonium.ships:
            ships.append((ship.get_name(), self.cosmonium.ship is ship, self.cosmonium.set_ship, ship))

        return (
                (menu_text(_('_Mode')), 0, controllers),
                0,
                (menu_text(_('_Center on'), 'C'), 0, self.autopilot.center_on_object if has_selected else 0),
                #('Look _back'), '*'), 0, self.camera.camera_look_back),
                (menu_text(_('_Track'), 'Y'), 0, self.cosmonium.track_selected if has_selected else 0),
                0,
                (menu_text(_('Zoom _in'), '.'), 0, self.camera.zoom, 1.05),
                (menu_text(_('Zoom _out'), ','), 0, self.camera.zoom, 1.0/1.05),
                (menu_text(_('_Reset Zoom'), 'Control-R'), 0, self.camera.reset_zoom),
                0,
                (menu_text(_('_Select ship')), 0, ships if len(self.cosmonium.ships) > 1 else 0),
                (menu_text(_('_Edit ship')), 0, self.show_ship_editor if self.cosmonium.ship.editable else 0),
                )

    def create_render_menu_items(self):
        labels = (
                  (menu_text(_('_Galaxies'), 'E'), bodyClasses.get_show_label('galaxy'), self.cosmonium.toggle_label, 'galaxy'),
                  #(menu_text(_('Globular'), 'Shift-E'), self.toggle_label, 'globular'),
                  (menu_text(_('_Stars'), 'B'), bodyClasses.get_show_label('star'), self.cosmonium.toggle_label, 'star'),
                  (menu_text(_('_Planets'), 'P'), bodyClasses.get_show_label('planet'), self.cosmonium.toggle_label, 'planet'),
                  (menu_text(_('_Dwarf planets'), 'Shift-P'), bodyClasses.get_show_label('dwarfplanet'), self.cosmonium.toggle_label, 'dwarfplanet'),
                  (menu_text(_('_Moons'), 'M'), bodyClasses.get_show_label('moon'), self.cosmonium.toggle_label, 'moon'),
                  (menu_text(_('M_inor Moons'), 'Shift-M'), bodyClasses.get_show_label('minormoon'), self.cosmonium.toggle_label, 'minormoon'),
                  (menu_text(_('L_ost Moons')), bodyClasses.get_show_label('lostmoon'), self.cosmonium.toggle_label, 'lostmoon'),
                  (menu_text(_('C_omets'), 'Shift-W'), bodyClasses.get_show_label('comet'), self.cosmonium.toggle_label, 'comet'),
                  (menu_text(_('_Asteroids'), 'W'), bodyClasses.get_show_label('asteroid'), self.cosmonium.toggle_label, 'asteroid'),
                  (menu_text(_('I_nterstellars')), bodyClasses.get_show_label('interstellar'), self.cosmonium.toggle_label, 'interstellar'),
                  (menu_text(_('S_pacecrafts'), 'N'), bodyClasses.get_show_label('spacecraft'), self.cosmonium.toggle_label, 'spacecraft'),
                  (menu_text(_('_Constellations'), '='), bodyClasses.get_show_label('constellation'), self.cosmonium.toggle_label, 'constellation'),
                  #(menu_text(_('Locations'), '&'), self.toggle_label, 'location'),
                  )

        orbits = (
                  (menu_text(_('All _orbits'), 'O'), settings.show_orbits, self.cosmonium.toggle_orbits),
                  0,
                  (menu_text(_('_Stars'), 'Shift-Control-B'), bodyClasses.get_show_orbit('star'), self.cosmonium.toggle_orbit, 'star'),
                  (menu_text(_('_Planets'), 'Shift-Control-P'), bodyClasses.get_show_orbit('planet'), self.cosmonium.toggle_orbit, 'planet'),
                  (menu_text(_('_Dwarf planets'), 'Shift-Control-D'), bodyClasses.get_show_orbit('dwarfplanet'), self.cosmonium.toggle_orbit, 'dwarfplanet'),
                  (menu_text(_('_Moons'), 'Shift-control-M'), bodyClasses.get_show_orbit('moon'), self.cosmonium.toggle_orbit, 'moon'),
                  (menu_text(_('M_inor moons'), 'Shift-Control-O'), bodyClasses.get_show_orbit('minormoon'), self.cosmonium.toggle_orbit, 'minormoon'),
                  (menu_text(_('L_ost moons')), bodyClasses.get_show_orbit('lostmoon'), self.cosmonium.toggle_orbit, 'lostmoon'),
                  (menu_text(_('_Comets'), 'Shift-Control-C'), bodyClasses.get_show_orbit('comet'), self.cosmonium.toggle_orbit, 'comet'),
                  (menu_text(_('_Asteroids'), 'Shift-Control-A'), bodyClasses.get_show_orbit('asteroid'), self.cosmonium.toggle_orbit, 'asteroid'),
                  (menu_text(_('I_nterstellars')), bodyClasses.get_show_orbit('interstellar'), self.cosmonium.toggle_orbit, 'interstellar'),
                  (menu_text(_('S_pacecrafts'), 'Shift-Control-S'), bodyClasses.get_show_orbit('spacecraft'), self.cosmonium.toggle_orbit, 'spacecraft'),
                  )

        bodies = (
                  (menu_text(_('_Galaxies'), 'U'), bodyClasses.get_show('galaxy'), self.cosmonium.toggle_body_class, 'galaxy'),
                  #(menu_text(_('shift-u'), self.cosmonium.toggle_globulars)
                  #(menu_text(_('^'), self.cosmonium.toggle_nebulae)
                  )

        options = (
                   (menu_text(_('_Atmospheres'), 'Control-A'), settings.show_atmospheres, self.cosmonium.toggle_atmosphere),
                   (menu_text(_('_Clouds'), 'I'), settings.show_clouds, self.cosmonium.toggle_clouds),
                   #(menu_text(_('control-e'), self.toggle_shadows)
                   #(menu_text(_('control-l)', self.cosmonium.toggle_nightsides)
                   #(menu_text(_('control-t'), self.cosmonium.toggle_comet_tails)
                   )

        guides = (
                   (menu_text(_('_Boundaries'), 'Control-B'), settings.show_boundaries, self.cosmonium.toggle_boundaries),
                   (menu_text(_('_Asterisms'), '/'), settings.show_asterisms, self.cosmonium.toggle_asterisms),
                   )

        grids = (
                 (menu_text(_('_Equatorial'), ';'), settings.show_equatorial_grid, self.cosmonium.toggle_grid_equatorial),
                 (menu_text(_('E_cliptic'), ':'), settings.show_ecliptic_grid, self.cosmonium.toggle_grid_ecliptic),
                 )

        stereo = (
                    (menu_text(_('Hardware support')), settings.stereoscopic_framebuffer, self.toggle_stereoscopic_framebuffer),
                    (menu_text(_('Red-Blue')), settings.red_blue_stereo, self.toggle_red_blue_stereo),
                    (menu_text(_('Side by side')), settings.side_by_side_stereo, self.toggle_side_by_side_stereo),
                    (menu_text(_('Swap eyes')), settings.stereo_swap_eyes, self.toggle_swap_eyes),
                    )

        advanced = (
                    (menu_text(_('_Decrease ambient'), '{'), 0, self.cosmonium.incr_ambient, -0.05),
                    (menu_text(_('_Increase ambient'), '}'), 0, self.cosmonium.incr_ambient, +0.05),
                    0,
                    (menu_text(_('_Rotation axis'), 'Shift-A'), settings.show_rotation_axis, self.cosmonium.toggle_rotation_axis),
                    (menu_text(_('Reference _frame'), 'Shift-Control-R'), settings.show_reference_axis, self.cosmonium.toggle_reference_axis),
                    )

        return (
            (menu_text(_('_Labels')), 0, labels),
            (menu_text(_('_Orbits')), 0, orbits),
            (menu_text(_('_Bodies')), 0, bodies),
            (menu_text(_('O_ptions')), 0, options),
            (menu_text(_('_Grids')), 0, grids),
            (menu_text(_('G_uides')), 0, guides),
            (menu_text(_('_3D')), 0, stereo),
            (menu_text(_('_Advanced')), 0, advanced),
        )

    def create_window_menu_items(self):
        return (
                (menu_text(_('Toggle _fullscreen'), 'Alt-Enter'), 0, self.cosmonium.toggle_fullscreen),
                (menu_text(_('Toggle _menubar'), 'Control-M'), 0, self.toggle_menu),
                (menu_text(_('Toggle _HUD'), 'V'), 0, self.toggle_hud),
                0,
                (menu_text(_('Save _screenshot'), 'F10'), 0, self.cosmonium.save_screenshot),
                (menu_text(_('Save screenshot _without UI'), 'Shift-F10'), 0, self.cosmonium.save_screenshot_no_annotation),
                )

    def create_debug_menu_items(self):
        fps = (
                (menu_text(_('Frame per second')), settings.display_fps, self.set_render_fps),
                (menu_text(_('Render time')), settings.display_ms, self.set_render_ms),
                (menu_text(_("None")), not (settings.display_fps or settings.display_ms), self.set_render_none),
                )
        shaders = (
                (menu_text(_('Default')), settings.shader_debug_fragment_shader == 'default', self.set_shader_fragment_debug, 'default'),
                (menu_text(_('Diffuse')), settings.shader_debug_fragment_shader == 'diffuse', self.set_shader_fragment_debug, 'diffuse'),
                (menu_text(_('Normals')), settings.shader_debug_fragment_shader == 'normal', self.set_shader_fragment_debug, 'normal'),
                (menu_text(_('Normal map')), settings.shader_debug_fragment_shader == 'normalmap', self.set_shader_fragment_debug, 'normalmap'),
                (menu_text(_('Shadows')), settings.shader_debug_fragment_shader == 'shadows', self.set_shader_fragment_debug, 'shadows'),
                (menu_text(_('Color picking')), settings.shader_debug_fragment_shader == 'picking', self.set_shader_fragment_debug, 'picking'),
                (menu_text(_('Ray hit')), settings.shader_debug_raymarching_canvas, self.toggle_shader_debug_raymarching_canvas),
                (menu_text(_('Show slice')), settings.shader_debug_raymarching_slice, self.toggle_shader_debug_raymarching_slice),
                )
        return (
                (menu_text(_('Toggle filled wireframe'), 'F3'), 0, self.cosmonium.toggle_filled_wireframe),
                (menu_text(_('Toggle wireframe'), 'Shift-F3'), 0, self.cosmonium.toggle_wireframe),
                (menu_text(_("Show render buffers"), "F5"), 0, base.bufferViewer.toggleEnable),
                (menu_text(_('Show shadow frustum'), 'Shift-Control-F9'), settings.debug_shadow_frustum, self.toggle_shadow_frustum),
                0,
                (menu_text(_('Shaders')), 0, shaders),
                (menu_text(_('Instant movement'), 'Control-J'), settings.debug_jump, self.toggle_jump),
                (menu_text(_('Connect pstats'), 'F2'), 0, self.cosmonium.connect_pstats),
                (menu_text(_('Render info')), 0, fps),
                0,
                (menu_text(_('Freeze LOD'), 'F8'), settings.debug_lod_freeze, self.toggle_lod_freeze),
                (menu_text(_('Dump LOD tree'), 'Shift-F8'), 0, self.dump_object_info),
                (menu_text(_('Dump LOD flat tree'), 'Shift-Control-F8'), 0, self.dump_object_info_2),
                (menu_text(_('Log LOD events'), 'Control-F8'), settings.debug_lod_split_merge, self.toggle_split_merge_debug),
                (menu_text(_('Show boundaries'), 'F9'), settings.shader_debug_coord, self.toggle_shader_debug_coord),
                (menu_text(_('Show LOD bounding boxes'), 'Shift-F9'), settings.debug_lod_show_bb, self.toggle_bb),
                (menu_text(_('Show LOD culling frustum'), 'Control-F9'), settings.debug_lod_frustum, self.toggle_frustum),
                0,
                (menu_text(_('Show octree stats'), 'F7'), 0, self.cosmonium.universe.dumpOctreeStats),
                (menu_text(_('Dump octree'), 'Shift-F7'), 0, self.cosmonium.universe.dumpOctree),
                )

    def create_help_menu_items(self):
        return (
       (menu_text(_('User _guide'), 'Shift-F1'), 0, self.show_help),
       0, # separator
       (menu_text(_('_Credits')), 0, 0),
       (menu_text(_('_License')), 0, self.show_license),
       0, # separator
       (menu_text(_('_About')), 0, self.show_about),
       )

    def create_menubar(self):
        scale = self.scale
        scale = LVector3(scale[0], 1.0, scale[1])
        scale[0] *= settings.menu_text_size
        scale[2] *= settings.menu_text_size
        self.menubar = DropDownMenu(
            items=((_('_Cosmonium'), self.create_main_menu_items),
                   (_('_Select'), self.create_select_menu_items),
                   (_('_Time'), self.create_time_menu_items),
                   (_('Camera'), self.create_camera_menu_items),
                   (_('_Render'), self.create_render_menu_items),
                   (_('_Window'), self.create_window_menu_items),
                   (_('_Debug'), self.create_debug_menu_items),
                   (_('_Help'), self.create_help_menu_items),),
            font=self.font,
            sidePad=.75,
            align=DropDownMenu.ALeft,
            baselineOffset=-.35,
            scale=scale, itemHeight=1.2, leftPad=.2,
            separatorHeight=.3,
            underscoreThickness=1,
            BGColor=(.9,.9,.9,.9),
            BGBorderColor=(.3,.3,.3,1),
            separatorColor=(0,0,0,1),
            frameColorHover=(.3,.3,.3,1),
            frameColorPress=(.3,.3,.3,.1),
            textColorReady=(0,0,0,1),
            textColorHover=(.7,.7,.7,1),
            textColorPress=(0,0,0,1),
            textColorDisabled=(.3,.3,.3,1))
        self.menubar_shown = True

    def popup_done(self):
        self.popup_menu = False

    def create_orbiting_bodies_menu_items(self, body):
        subitems = []
        if isinstance(body, StellarSystem):
            system = body
        elif body is not None and body.system is not None and not isinstance(body.system, Universe):
            system = body.system
        else:
            system = None
        if system is not None:
            children = []
            for child in system.children:
                if child != body:
                    children.append(child)
            if len(children) > 0:
                children.sort(key=lambda x: x.orbit.get_apparent_radius())
                subitems = []
                for child in children:
                    if isinstance(child, SimpleSystem):
                        subitems.append([child.primary.get_friendly_name(), 0, self.cosmonium.select_body, child.primary])
                    else:
                        subitems.append([child.get_friendly_name(), 0, self.cosmonium.select_body, child])
        return subitems

    def create_orbits_menu_items(self, body):
        subitems = []
        if body is not None:
            parent = body.parent
            while parent is not None and not isinstance(parent, Universe):
                if isinstance(parent, SimpleSystem):
                    if parent.primary != body:
                        subitems.append([parent.primary.get_friendly_name(), 0, self.cosmonium.select_body, parent.primary])
                else:
                    subitems.append([parent.get_friendly_name(), 0, self.cosmonium.select_body, parent])
                parent = parent.parent
        return subitems

    def create_popup_menu(self, over):
        if over is None and self.menubar_shown:
            return False
        items = []
        if over is not None:
            self.cosmonium.select_body(over)
            items.append((over.get_friendly_name(), 0, self.cosmonium.autopilot.center_on_object))
            items.append(0)
            items.append([_('_Info'), 0, self.show_info])
            items.append([_('_Goto'), 0, self.autopilot.go_to_object])
            items.append([_('_Follow'), 0, self.cosmonium.follow_selected])
            items.append([_('S_ync'), 0, self.cosmonium.sync_selected])
            if isinstance(over, StellarBody) and len(over.surfaces) > 1:
                subitems = []
                for surface in over.surfaces:
                    name = surface.get_name()
                    if surface.category is not None:
                        if name != '':
                            name += " (%s)" % surface.category.name
                        else:
                            name = "%s" % surface.category.name
                    if surface.resolution is not None:
                        if isinstance(surface.resolution, int):
                            name += " (%dK)" % surface.resolution
                        else:
                            name += " (%s)" % surface.resolution
                    if surface is over.surface:
                        subitems.append([name, 0, None, None])
                    else:
                        subitems.append([name, 0, over.set_surface, surface])
                items.append([_("Surfaces"), 0, subitems])
            subitems = self.create_orbiting_bodies_menu_items(over)
            if len(subitems) > 0:
                items.append([_("Orbiting bodies"), 0, subitems])
            subitems = self.create_orbits_menu_items(over)
            if len(subitems) > 0:
                items.append([_("Orbits"), 0, subitems])
        items.append([_('_Edit'), 0, self.show_editor])
        subitems = []
        for info in extra_info:
            name = info.get_name()
            url = info.get_url_for(over)
            if url is not None:
                subitems.append([name, 0, self.browser.load, url])
        if len(subitems) > 0:
            items.append([_("More info"), 0, subitems])
        if not self.menubar_shown:
            if over is not None:
                items.append(0)
            items.append([_('Show _menubar'), 0, self.show_menu])
        scale = self.hud.scale
        scale = LVector3(scale[0], 1.0, scale[1])
        scale[0] *= settings.menu_text_size
        scale[2] *= settings.menu_text_size
        PopupMenu(items=items,
                  font=self.font,
                  baselineOffset=-.35,
                  scale=scale, itemHeight=1.2, leftPad=.2,
                  separatorHeight=.3,
                  underscoreThickness=1,
                  BGColor=(.9,.9,.9,.9),
                  BGBorderColor=(.3,.3,.3,1),
                  separatorColor=(0,0,0,1),
                  frameColorHover=(.3,.3,.3,1),
                  frameColorPress=(.3,.3,.3,.1),
                  textColorReady=(0,0,0,1),
                  textColorHover=(.7,.7,.7,1),
                  textColorPress=(0,0,0,1),
                  textColorDisabled=(.3,.3,.3,1),
                  onDestroy=self.popup_done
                  )
        return True

    def select_object(self, body):
        self.cosmonium.select_body(body)

    def get_object(self, name):
        result = objectsDB.get(name)
        return result

    def list_objects(self, prefix):
        result = objectsDB.startswith(prefix)
        result.sort(key=lambda x: x[0])
        return result

    def open_find_object(self):
        self.query.open_query(self)

    def update_status(self):
        over = self.cosmonium.over
        selected = self.cosmonium.selected
        track = self.cosmonium.track
        follow = self.cosmonium.follow
        sync = self.cosmonium.sync
        (years, months, days, hours, mins, secs) = self.time.time_to_values()
        date="%02d:%02d:%02d %2d:%02d:%02d UTC" % (years, months, days, hours, mins, secs)
        if selected is not None:
            names = utils.join_names(bayer.decode_names(selected.get_names()))
            self.hud.title.set(names)
            radius = selected.get_apparent_radius()
            if selected.virtual_object or selected.distance_to_obs > 10 * radius:
                self.hud.topLeft.set(0, _("Distance: ")  + toUnit(selected.distance_to_obs, units.lengths_scale))
            else:
                if selected.surface is not None and not selected.surface.is_flat():
                    distance = selected.distance_to_obs - selected.height_under
                    altitude = selected.distance_to_obs - radius
                    self.hud.topLeft.set(0, _("Altitude: ") + toUnit(altitude, units.lengths_scale) + " (" + _("Ground: ")  + toUnit(distance, units.lengths_scale) + ")")
                else:
                    altitude = selected.distance_to_obs - radius
                    self.hud.topLeft.set(0, _("Altitude: ")  + toUnit(altitude, units.lengths_scale))
            if not selected.virtual_object:
                self.hud.topLeft.set(1, _("Radius: ") + "%s (%s)" % (toUnit(radius, units.lengths_scale), toUnit(radius, units.diameter_scale, 'x')))
                self.hud.topLeft.set(2, _("Abs (app) magnitude: ") + "%g (%g)" % (selected.get_abs_magnitude(), selected.get_app_magnitude()))
                if selected.is_emissive():
                    self.hud.topLeft.set(3, _("Luminosity: ") + "%g" % (selected.get_luminosity()) + _("x Sun"))
                    if isinstance(selected, Star):
                        self.hud.topLeft.set(4, _("Spectral type: ") + selected.spectral_type.get_text())
                        self.hud.topLeft.set(5, _("Temperature: ") + "%d" % selected.temperature + " K")
                    else:
                        self.hud.topLeft.set(4, "")
                        self.hud.topLeft.set(5, "")
                else:
                    self.hud.topLeft.set(3, _("Phase: ") + "%g°" % ((1 - selected.get_phase()) * 180))
                    self.hud.topLeft.set(4, "")
                    self.hud.topLeft.set(5, "")
            else:
                self.hud.topLeft.set(1, _("Abs (app) magnitude: ") + "%g (%g)" % (selected.get_abs_magnitude(), selected.get_app_magnitude()))
                self.hud.topLeft.set(2, "")
                self.hud.topLeft.set(3, "")
                self.hud.topLeft.set(4, "")
                self.hud.topLeft.set(5, "")
        else:
            self.hud.title.set("")
            self.hud.topLeft.set(0, "")
            self.hud.topLeft.set(1, "")
            self.hud.topLeft.set(2, "")
            self.hud.topLeft.set(3, "")
            self.hud.topLeft.set(4, "")
            self.hud.topLeft.set(5, "")
            self.hud.topLeft.set(6, "")
        self.hud.bottomLeft.set(0, toUnit(self.nav.speed, units.speeds_scale))
        if over:
            names = utils.join_names(bayer.decode_names(over.names))
            self.hud.bottomLeft.set(1, names)
        else:
            self.hud.bottomLeft.set(1, "")
        current_time = globalClock.getRealTime()
        if current_time - self.last_fps >= 1.0:
            if settings.display_fps:
                fps = globalClock.getAverageFrameRate()
                self.hud.topRight.set(0, "%.1f fps" % fps)
            elif settings.display_ms:
                fps = globalClock.getDt() * 1000
                self.hud.topRight.set(0, "%.1f ms" % fps)
            else:
                self.hud.topRight.set(0, "")
            self.last_fps = current_time
        if self.autopilot.current_interval is not None:
            self.hud.bottomRight.set(4, _("Travelling (%d)") % (self.autopilot.current_interval.getDuration() - self.autopilot.current_interval.getT()))
        else:
            self.hud.bottomRight.set(4, "")
        if track is not None:
            self.hud.bottomRight.set(3, _("Track %s") % track.get_name())
        else:
            self.hud.bottomRight.set(3, "")
        if self.cosmonium.fly:
            self.hud.bottomRight.set(2, _("Fly over %s") % selected.get_name())
        elif follow is not None:
            self.hud.bottomRight.set(2, _("Follow %s") % follow.get_name())
        elif sync is not None:
            self.hud.bottomRight.set(2, _("Sync orbit %s") % sync.get_name())
        else:
            self.hud.bottomRight.set(2, "")
        if self.time.running:
            self.hud.bottomRight.set(0, "%s (%.0fx)" % (date, self.time.multiplier))
        else:
            self.hud.bottomRight.set(0, _("%s (Paused)") % (date))
        #self.hud.bottomRight.set(1, "FOV: %.0f°/%.0f°" % (self.cosmonium.realCamLens.getHfov(), self.cosmonium.realCamLens.getVfov()))
        self.hud.bottomRight.set(1, "FoV: %d° %d' %g\" (%gx)" % (units.toDegMinSec(self.camera.realCamLens.getVfov()) + (self.camera.zoom_factor, )))

    def update_info(self, text, duration=3.0, fade=1.0):
        self.hud.info.set(text, duration, fade)

    def update_scale(self):
        self.hud.update_scale()

    def update_size(self, width, height):
        if self.width == width and self.height == height:
            return
        self.width = width
        self.height = height
        #TODO: This is an ugly hack, should use the proper anchors or define new ones
        #Update aspect2d scale and anchors
        arx = 1.0 * self.screen_width / self.width
        ary = 1.0 * self.screen_height / self.height
        self.cosmonium.aspect2d.setScale(arx, 1.0, ary)
        self.cosmonium.a2dTop = 1.0 / ary
        self.cosmonium.a2dBottom = -1.0 / ary
        self.cosmonium.a2dLeft = -1.0 / arx
        self.cosmonium.a2dRight = 1.0 / arx
        self.cosmonium.a2dTopCenter.setPos(0, 0, self.cosmonium.a2dTop)
        self.cosmonium.a2dBottomCenter.setPos(0, 0, self.cosmonium.a2dBottom)
        self.cosmonium.a2dLeftCenter.setPos(self.cosmonium.a2dLeft, 0, 0)
        self.cosmonium.a2dRightCenter.setPos(self.cosmonium.a2dRight, 0, 0)

        self.cosmonium.a2dTopLeft.setPos(self.cosmonium.a2dLeft, 0, self.cosmonium.a2dTop)
        self.cosmonium.a2dTopRight.setPos(self.cosmonium.a2dRight, 0, self.cosmonium.a2dTop)
        self.cosmonium.a2dBottomLeft.setPos(self.cosmonium.a2dLeft, 0, self.cosmonium.a2dBottom)
        self.cosmonium.a2dBottomRight.setPos(self.cosmonium.a2dRight, 0, self.cosmonium.a2dBottom)
        self.cosmonium.pixel2d.setScale(2.0 / width, 1.0, 2.0 / height)

    def hide(self):
        self.hud.hide()
        self.hide_menu()

    def show(self):
        self.hud.show()
        self.show_menu()

    def hide_with_state(self):
        state = (self.hud.shown, self.menubar_shown)
        self.hide()
        return state

    def show_with_state(self, state):
        (hud_shown, menubar_shown) =state
        if hud_shown:
            self.hud.show()
        if menubar_shown:
            self.show_menu()

    def show_hud(self):
        self.hud.show()

    def hide_hud(self):
        self.hud.hide()

    def toggle_hud(self):
        if self.hud.shown:
            self.hud.hide()
        else:
            self.hud.show()
        settings.show_hud = self.hud.shown
        self.cosmonium.save_settings()

    def show_menu(self):
        self.menubar.menu.show()
        self.menubar_shown = True
        self.hud.set_y_offset(self.menubar.height)

    def hide_menu(self):
        self.menubar.menu.hide()
        self.menubar_shown = False
        self.hud.set_y_offset(0)

    def toggle_menu(self):
        if self.menubar_shown:
            self.hide_menu()
        else:
            self.show_menu()
        settings.show_menubar = self.menubar_shown
        self.cosmonium.save_settings()

    def show_help(self):
        self.help.show()
        if not self.help in self.opened_windows:
            self.opened_windows.append(self.help)

    def show_license(self):
        self.license.show()
        if not self.license in self.opened_windows:
            self.opened_windows.append(self.license)

    def show_about(self):
        self.about.show()
        if not self.about in self.opened_windows:
            self.opened_windows.append(self.about)

    def show_info(self):
        if self.cosmonium.selected is not None:
            if self.info.shown():
                self.info.hide()
            self.info.show(self.cosmonium.selected)
            if not self.info in self.opened_windows:
                self.opened_windows.append(self.info)

    def show_editor(self):
        if self.cosmonium.selected is not None:
            if self.editor.shown():
                self.editor.hide()
            self.editor.show(self.cosmonium.selected)
            if not self.editor in self.opened_windows:
                self.opened_windows.append(self.editor)

    def show_ship_editor(self):
        if self.cosmonium.ship is not None:
            if self.editor.shown():
                self.editor.hide()
            self.editor.show(self.cosmonium.ship)
            if not self.editor in self.opened_windows:
                self.opened_windows.append(self.editor)

    def show_preferences(self):
        self.preferences.show()
        if not self.preferences in self.opened_windows:
            self.opened_windows.append(self.preferences)
