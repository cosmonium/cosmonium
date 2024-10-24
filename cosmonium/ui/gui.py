# -*- coding: utf-8 -*-
#
# This file is part of Cosmonium.
#
# Copyright (C) 2018-2024 Laurent Deru.
#
# Cosmonium is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Cosmonium is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Cosmonium.  If not, see <https://www.gnu.org/licenses/>.
#

import os
from panda3d.core import LVector2

from ..fonts import fontsManager, Font
from ..catalogs import objectsDB
from .. import settings
from .. import version

# TODO: should only be used by Cosmonium main class
from ..parsers.configparser import configParser

from .jinja import JinjaEnv
from .loader import UIConfigLoader
from .shortcuts import Shortcuts
from .huds import Huds
from .hud.query import Query
from .clipboard import create_clipboard
from .windows.browser import Browser
from .windows.filewindow import FileWindow
from .windows.info import InfoWindow
from .windows.objecteditor import ObjectEditorWindow
from .windows.preferences import Preferences
from .windows.textwindow import TextWindow
from .windows.time import TimeEditor
from .menubuilder import MenuBuilder
from .menubar import Menubar
from .popup import Popup


about_text = (
    """# Cosmonium

**Version**: V%s
Copyright 2018-2024 Laurent Deru


**Website**: http://github.com/cosmonium/cosmonium


This program is free software; you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation; either version 3 of the License, or (at your option) any later
version.


This program uses several third-party libraries which are subject to their own
licenses, see Third-Party.md for the complete list.
"""
    % version.version_str
)


class Gui(object):

    def __init__(self, config_file, cosmonium, time, camera, mouse, autopilot):
        self.base = cosmonium
        self.cosmonium = cosmonium
        self.time = time
        self.camera = camera
        self.mouse = mouse
        self.nav = None
        self.autopilot = autopilot
        self.messenger = self.cosmonium.messenger
        self.over = None
        self.hud = None
        if self.base.pipe is not None:
            self.screen_width = self.base.pipe.getDisplayWidth()
            self.screen_height = self.base.pipe.getDisplayHeight()
        else:
            self.screen_width = 1
            self.screen_height = 1
        if settings.ui_scale_dpi_aware and not self.cosmonium.app_config.test_start:
            settings.ui_scale = cosmonium.pipe.display_zoom
        else:
            settings.ui_scale = settings.custom_ui_scale
        self.calc_scale()
        self.width = 0
        self.height = 0

        self.root = cosmonium.pixel2d
        self.cosmonium.p2dTopCenter = cosmonium.pixel2d.attach_new_node('p2dTopCenter')
        self.cosmonium.p2dBottomCenter = cosmonium.pixel2d.attach_new_node('p2dBottomCenter')
        self.cosmonium.p2dLeftCenter = cosmonium.pixel2d.attach_new_node('p2dLeftCenter')
        self.cosmonium.p2dRightCenter = cosmonium.pixel2d.attach_new_node('p2dRightCenter')

        self.cosmonium.p2dTopLeft = cosmonium.pixel2d.attach_new_node('p2dTopLeft')
        self.cosmonium.p2dTopRight = cosmonium.pixel2d.attach_new_node('p2dTopRight')
        self.cosmonium.p2dBottomLeft = cosmonium.pixel2d.attach_new_node('p2dBottomLeft')
        self.cosmonium.p2dBottomRight = cosmonium.pixel2d.attach_new_node('p2dBottomRight')

        self.update_size(self.screen_width, self.screen_height)
        font = fontsManager.get_font(settings.hud_font, Font.STYLE_NORMAL)
        if font is not None:
            self.font = font.load()
        else:
            self.font = None
        self.clipboard = create_clipboard()
        self.shortcuts = Shortcuts(self.base, self.base.messenger, self)

        self.env = JinjaEnv(self.base, self)

        ui_config = self.load(config_file)
        self.skin = ui_config.skin
        self.translation = self.cosmonium.load_lang("ui", ui_config.locale)

        self.shortcuts.set_shortcuts(ui_config.shortcuts)

        self.hud = Huds(self, ui_config.hud, ui_config.dock, self.env, self.skin)
        self.query = Query('query', self.cosmonium.p2dBottomLeft, 0, settings.query_delay, owner=self)
        self.opened_windows = []
        self.browser = Browser(owner=self)
        self.editor = ObjectEditorWindow(owner=self)
        self.time_editor = TimeEditor(self.time, owner=self)
        self.info = InfoWindow(owner=self)
        self.preferences = Preferences(self.cosmonium, owner=self)
        self.help = TextWindow('Help', owner=self)
        self.help.load('control.md')
        self.license = TextWindow('License', owner=self)
        self.license.load('COPYING.md')
        self.about = TextWindow('About', owner=self)
        self.about.set_text(about_text)
        self.filewindow = FileWindow('Select', owner=self)

        self.menu_builder = MenuBuilder(
            self.translation, self.messenger, self.shortcuts, self.cosmonium, self.mouse, self.browser
        )
        self.menu_builder.add_named_menus(ui_config.named_menus)
        self.menubar = Menubar(self.menu_builder.create_menubar(ui_config.menubar), owner=self)
        self.menubar.create(self.scale)
        self.popup_menu = Popup(self.cosmonium, self.menu_builder.create_menu(ui_config.popup), owner=self)
        self.popup_menu_shown = False

        if settings.show_hud:
            self.show_hud()
        else:
            self.hide_hud()
        if settings.show_menubar:
            self.show_menu()
        else:
            self.hide_menu()

    def get_ui(self):
        return self

    def load(self, ui_config_file):
        loader = UIConfigLoader(self.env)
        return loader.load(ui_config_file)

    def set_nav(self, nav):
        self.nav = nav

    def calc_scale(self):
        self.scale = LVector2(
            settings.ui_scale / self.screen_width * 2.0, settings.ui_scale / self.screen_height * 2.0
        )

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
        if body is not None and self.cosmonium.selected == body:
            self.cosmonium.center_on_object(body)
            return
        self.cosmonium.select_body(body)

    def right_click(self):
        self.over = self.mouse.get_over()
        if self.over is None and self.menubar_shown:
            return False
        self.popup_menu.create(self.scale, self.over, self.popup_done)
        self.popup_menu_shown = True
        self.over = None

    def popup_done(self):
        self.popup_menu_shown = False

    def set_display_render_info(self, mode):
        settings.display_render_info = mode
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
        self.hud.update(self.cosmonium, self.camera, self.mouse, self.nav, self.autopilot, self.time)

    def update_info(self, text, pos=(1, -3), color=(1, 1, 1, 1), anchor=None, duration=3.0, fade=1.0):
        self.hud.info.set(text=text, pos=pos, color=color, anchor=anchor, duration=duration, fade=fade)

    def update_scale(self):
        self.hud.set_scale()

    def update_size(self, width, height):
        if self.width == width and self.height == height:
            return
        self.width = width
        self.height = height
        # TODO: This is an ugly hack, should use the proper anchors or define new ones
        # Update aspect2d scale and anchors
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
        self.cosmonium.p2dTopCenter.setPos(self.width / 2, 0, 0)
        self.cosmonium.p2dBottomCenter.setPos(self.width / 2, 0, -self.height)
        self.cosmonium.p2dLeftCenter.setPos(0, 0, -self.height / 2)
        self.cosmonium.p2dRightCenter.setPos(self.width, 0, -self.height / 2)

        self.cosmonium.p2dTopLeft.setPos(0, 0, 0)
        self.cosmonium.p2dTopRight.setPos(self.width - 1, 0, 0)
        self.cosmonium.p2dBottomLeft.setPos(0, 0, -self.height + 1)
        self.cosmonium.p2dBottomRight.setPos(self.width - 1, 0, -self.height + 1)

        if self.hud is not None:
            self.hud.update_size()

    def get_limits(self):
        if self.menubar_shown:
            y_offset = self.menubar.get_height() / self.scale[1]
        else:
            y_offset = 0
        return (0, self.width, -y_offset, -self.height)

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
        (hud_shown, menubar_shown) = state
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
        limits = self.get_limits()
        self.hud.set_y_offset(-limits[2])
        for window in self.opened_windows:
            window.set_limits(limits)

    def hide_menu(self):
        self.menubar.hide()
        self.menubar_shown = False
        self.hud.set_y_offset(0)
        limits = self.get_limits()
        for window in self.opened_windows:
            window.set_limits(limits)

    def toggle_menu(self):
        if self.menubar_shown:
            self.hide_menu()
        else:
            self.show_menu()
        settings.show_menubar = self.menubar_shown
        self.cosmonium.save_settings()

    def show_help(self):
        self.help.show()
        if self.help not in self.opened_windows:
            self.opened_windows.append(self.help)

    def show_license(self):
        self.license.show()
        if self.license not in self.opened_windows:
            self.opened_windows.append(self.license)

    def show_about(self):
        self.about.show()
        if self.about not in self.opened_windows:
            self.opened_windows.append(self.about)

    def show_time_editor(self):
        self.time_editor.show()
        if self.time_editor not in self.opened_windows:
            self.opened_windows.append(self.time_editor)

    def show_info(self):
        if self.cosmonium.selected is not None:
            if self.info.shown():
                self.info.hide()
            self.info.show(self.cosmonium.selected)
            if self.info not in self.opened_windows:
                self.opened_windows.append(self.info)

    def show_editor(self):
        if self.cosmonium.selected is not None:
            if self.editor.shown():
                self.editor.hide()
            self.editor.show(self.cosmonium.selected)
            if self.editor not in self.opened_windows:
                self.opened_windows.append(self.editor)

    def show_ship_editor(self):
        if self.cosmonium.ship is not None:
            if self.editor.shown():
                self.editor.hide()
            self.editor.show(self.cosmonium.ship)
            if self.editor not in self.opened_windows:
                self.opened_windows.append(self.editor)

    def show_preferences(self):
        self.preferences.show()
        if self.preferences not in self.opened_windows:
            self.opened_windows.append(self.preferences)

    def show_select_screenshots(self):
        if self.filewindow.shown():
            self.filewindow.hide()
        self.filewindow.show(settings.screenshot_path, self.cosmonium.set_screenshots_path, show_files=False)
        if self.filewindow not in self.opened_windows:
            self.opened_windows.append(self.filewindow)

    def show_open_script(self):
        if self.filewindow.shown():
            self.filewindow.hide()
        self.filewindow.show(settings.last_script_path, self.load_cel_script, extensions=['.cel', '.CEL'])
        if self.filewindow not in self.opened_windows:
            self.opened_windows.append(self.filewindow)
