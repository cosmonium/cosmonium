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


from panda3d.core import LVector2

from ..bodies import Star
from ..astro import units
from ..astro import bayer
from ..astro.units import toUnit
from ..fonts import fontsManager, Font
from ..catalogs import objectsDB
from .. import utils
from .. import settings
from .. import version
#TODO: should only be used by Cosmonium main class
from ..parsers.configparser import configParser

from .shortcuts import Shortcuts
from .hud import HUD
from .query import Query
from .objecteditor import ObjectEditorWindow
from .textwindow import TextWindow
from .filewindow import FileWindow
from .infopanel import InfoPanel
from .preferences import Preferences
from .clipboard import create_clipboard
from .browser import Browser
from .time import TimeEditor
from .menubar import Menubar
from .popup import Popup

import os

about_text = """# Cosmonium

**Version**: V%s
Copyright 2018-2020 Laurent Deru


**Website**: http://github.com/cosmonium/cosmonium


This program is free software; you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation; either version 3 of the License, or (at your option) any later
version.


This program uses several third-party libraries which are subject to their own
licenses, see Third-Party.md for the complete list.
""" % version.version_str

class Gui(object):
    def __init__(self, cosmonium, time, camera, mouse, autopilot):
        self.cosmonium = cosmonium
        self.time = time
        self.camera = camera
        self.mouse = mouse
        self.nav = None
        self.autopilot = autopilot
        self.messenger = self.cosmonium.messenger
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
        self.shortcuts = Shortcuts(base, base.messenger, self)
        self.hud = HUD(self.scale, self.font)
        self.query = Query(self.scale, self.font, settings.query_color, settings.query_text_size, settings.query_suggestion_text_size, settings.query_delay)
        self.last_fps = globalClock.getRealTime()
        self.width = 0
        self.height = 0
        self.update_size(self.screen_width, self.screen_height)
        self.opened_windows = []
        self.editor = ObjectEditorWindow(font_family=settings.markdown_font, font_size=settings.ui_font_size, owner=self)
        self.time_editor = TimeEditor(self.time, font_family=settings.markdown_font, font_size=settings.ui_font_size, owner=self)
        self.info = InfoPanel(self.scale, settings.markdown_font, font_size=settings.ui_font_size, owner=self)
        self.preferences = Preferences(self.cosmonium, settings.markdown_font, font_size=settings.ui_font_size, owner=self)
        self.help = TextWindow('Help', self.scale, settings.markdown_font, font_size=settings.ui_font_size, owner=self)
        self.help.load('control.md')
        self.license = TextWindow('License', self.scale, settings.markdown_font, font_size=settings.ui_font_size, owner=self)
        self.license.load('COPYING.md')
        self.about = TextWindow('About', self.scale, settings.markdown_font, font_size=settings.ui_font_size, owner=self)
        self.about.set_text(about_text)
        self.filewindow = FileWindow('Select', self.scale, settings.markdown_font, font_size=settings.ui_font_size, owner=self)
        self.browser = Browser(self.scale, owner=self)
        self.menubar = Menubar(self.messenger, self.shortcuts, self.cosmonium)
        self.menubar.create(self.font, self.scale)
        self.popup_menu = Popup(self, self.messenger, self.cosmonium, self.browser)
        self.popup_menu_shown = False
        if settings.show_hud:
            self.show_hud()
        else:
            self.hide_hud()
        if settings.show_menubar:
            self.show_menu()
        else:
            self.hide_menu()

    def set_nav(self, nav):
        self.nav = nav

    def calc_scale(self):
        self.scale = LVector2(settings.ui_scale[0] / self.screen_width * 2.0,  settings.ui_scale[1] / self.screen_height * 2.0)

    def register_events(self, event_ctrl):
        pass

    def window_closed(self, window):
        if window in self.opened_windows:
            self.opened_windows.remove(window)

    def update(self):
        self.clipboard.update()

    def escape(self):
        if len(self.opened_windows) != 0:
            window = self.opened_windows.pop()
            window.hide()
        else:
            self.cosmonium.reset_all()

    def left_click(self):
        body = self.mouse.get_over()
        if body != None and self.cosmonium.selected == body:
            self.cosmonium.center_on_object(body)
            return
        self.cosmonium.select_body(body)

    def right_click(self):
        over = self.mouse.get_over()
        if over is None and self.menubar_shown:
            return False
        self.popup_menu.create(self.font, self.scale, over, self.popup_done)
        self.popup_menu_shown = True

    def popup_done(self):
        self.popup_menu_shown = False

    def set_render_fps(self):
        settings.display_fps = True
        settings.display_ms = False
        configParser.save()

    def set_render_ms(self):
        settings.display_fps = False
        settings.display_ms = True
        configParser.save()

    def set_render_none(self):
        settings.display_fps = False
        settings.display_ms = False
        configParser.save()

    def load_cel_script(self, path):
        settings.last_script_path = os.path.dirname(path)
        self.cosmonium.save_settings()
        self.cosmonium.load_and_run_script(path)

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
        selected = self.cosmonium.selected
        track = self.cosmonium.track
        follow = self.cosmonium.follow
        sync = self.cosmonium.sync
        (years, months, days, hours, mins, secs) = self.time.time_to_values()
        date="%02d:%02d:%02d %2d:%02d:%02d UTC" % (years, months, days, hours, mins, secs)
        if selected is not None:
            names = utils.join_names(bayer.decode_names(selected.get_names()))
            self.hud.title.set_text(names)
            radius = selected.get_apparent_radius()
            if selected.virtual_object or selected.anchor.distance_to_obs > 10 * radius:
                self.hud.topLeft.set(0, _("Distance: ")  + toUnit(selected.anchor.distance_to_obs, units.lengths_scale))
            else:
                if selected.surface is not None and not selected.surface.is_flat():
                    distance = selected.anchor.distance_to_obs - selected.anchor._height_under
                    altitude = selected.anchor.distance_to_obs - radius
                    self.hud.topLeft.set(0, _("Altitude: ") + toUnit(altitude, units.lengths_scale) + " (" + _("Ground: ")  + toUnit(distance, units.lengths_scale) + ")")
                else:
                    altitude = selected.anchor.distance_to_obs - radius
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
            self.hud.title.set_text("")
            self.hud.topLeft.set(0, "")
            self.hud.topLeft.set(1, "")
            self.hud.topLeft.set(2, "")
            self.hud.topLeft.set(3, "")
            self.hud.topLeft.set(4, "")
            self.hud.topLeft.set(5, "")
            self.hud.topLeft.set(6, "")
        self.hud.bottomLeft.set(0, toUnit(self.nav.speed, units.speeds_scale))
        if settings.mouse_over and self.mouse.over is not None:
            names = utils.join_names(bayer.decode_names(self.mouse.over.names))
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
        self.hud.bottomRight.set(1, "FoV: %d° %d' %g\" (%gx)" % (units.toDegMinSec(self.camera.lens.get_vfov()) + (self.camera.zoom_factor, )))

    def update_info(self, text, pos=(1, -3), color=(1, 1, 1, 1), anchor=None, duration=3.0, fade=1.0):
        self.hud.info.set(text=text, pos=pos, color=color, anchor=anchor, duration=duration, fade=fade)

    def update_scale(self):
        self.hud.set_scale()

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
        self.menubar.show()
        self.menubar_shown = True
        self.hud.set_y_offset(self.menubar.get_height())

    def hide_menu(self):
        self.menubar.hide()
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

    def show_select_screenshots(self):
        if self.filewindow.shown():
            self.filewindow.hide()
        self.filewindow.show(settings.screenshot_path, self.cosmonium.set_screenshots_path, show_files=False)
        if not self.filewindow in self.opened_windows:
            self.opened_windows.append(self.filewindow)

    def show_open_script(self):
        if self.filewindow.shown():
            self.filewindow.hide()
        self.filewindow.show(settings.last_script_path, self.load_cel_script, extensions=['.cel', '.CEL'])
        if not self.filewindow in self.opened_windows:
            self.opened_windows.append(self.filewindow)
