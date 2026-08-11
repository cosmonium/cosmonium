# -*- coding: utf-8 -*-
#
# This file is part of Cosmonium.
#
# Copyright (C) 2018-2026 Laurent Deru.
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

from .. import settings
from ..catalogs import objectsDB

# TODO: should only be used by Cosmonium main class
from ..parsers.configparser import configParser
from .clipboard import create_clipboard
from .hud.query import Query
from .loaders.config import UIConfigLoader
from .loaders.init import init_widget_loaders
from .loaders.widgets import WidgetLoaderRegistry
from .managers.anchor_layout_manager import AnchorLayout
from .managers.overlay_manager import OverlayManager
from .managers.theme_manager import ThemeManager
from .managers.window_manager import WindowManager
from .menus.menubar import Menubar
from .menus.menubuilder import MenuBuilder
from .menus.popup import Popup
from .shortcuts import Shortcuts
from .templates.providers import GlobalVars
from .windows.browser import Browser


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

        self.anchor = cosmonium.pixel2d
        self.anchors = AnchorLayout(cosmonium)

        self.update_size(self.screen_width, self.screen_height)
        self.skin = None
        self.clipboard = create_clipboard()
        self.shortcuts = Shortcuts(self.base, self.base.messenger, self)

        self.global_vars = GlobalVars(self.base, self)

        init_widget_loaders(WidgetLoaderRegistry.get_instance())
        self.load(config_file)
        self.translation = self.cosmonium.lang_manager.load_lang("ui", self.locale)

        self.shortcuts.set_shortcuts(self.shortcuts_config)

        # Initialize managers
        self.window_manager = WindowManager(self)
        self.window_manager.register_instance(self.window_manager)
        self.theme_manager = ThemeManager(self, self.skin)

        # Initialize overlay manager (replaces Huds)
        self.hud = OverlayManager(self, self.hud_config, self.dock_config)

        # Initialize query object
        self.query = Query('query', self.cosmonium.p2dBottomLeft, 0, settings.query_delay, parent=self)

        self.browser = Browser(parent=self)

        self.menu_builder = MenuBuilder(
            self.translation, self.messenger, self.shortcuts, self.cosmonium, self.mouse, self.browser
        )
        self.menu_builder.add_named_menus(self.named_menus)

        self.menubar_shown = False
        if self.menubar_config is not None:
            self.menubar = Menubar(self.menu_builder.create_menubar(self.menubar_config), self.scale, parent=self)
            self.menubar.create()
        else:
            self.menubar = None

        self.popup_menu_config = self.menu_builder.create_menu(self.popup_config) if self.popup_config else None
        self.popup_menu_shown = False

        if settings.show_hud:
            self.show_hud()
        else:
            self.hide_hud()
        if self.menubar is not None:
            if settings.show_menubar:
                self.show_menu()
            else:
                self.hide_menu()

    def get_ui(self):
        return self

    def load(self, ui_config_file):
        """Load UI configuration and apply directly to GUI."""
        loader = UIConfigLoader(self)
        loader.load(ui_config_file)

    def set_nav(self, nav):
        self.nav = nav

    def calc_scale(self):
        self.scale = LVector2(1 / self.screen_width * 2.0, 1 / self.screen_height * 2.0)

    def register_events(self, event_ctrl):
        pass

    def window_closed(self, window):
        self.window_manager.window_closed(window)

    def update(self):
        self.clipboard.update()

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
        self.query.create()

    def update_status(self):
        self.hud.update(self.global_vars.globals)

    def update_info(self, text, pos=(1, -3), color=(1, 1, 1, 1), anchor=None, duration=3.0, fade=1.0):
        self.hud.info.set(text=text, pos=pos, color=color, anchor=anchor, duration=duration, fade=fade)

    def update_size(self, width, height):
        if not self.anchors.update(width, height, self.screen_width, self.screen_height):
            return
        self.width = width
        self.height = height

        if self.hud is not None:
            self.hud.update_size()

    def get_limits(self):
        if self.menubar_shown and self.menubar is not None:
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
        hud_shown, menubar_shown = state
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
        if self.menubar is None:
            return
        self.menubar.show()
        self.menubar_shown = True
        limits = self.get_limits()
        self.hud.set_y_offset(-limits[2])
        for window in self.window_manager.open_windows:
            window.set_limits(limits)

    def hide_menu(self):
        if self.menubar is None:
            return
        self.menubar.hide()
        self.menubar_shown = False
        self.hud.set_y_offset(0)
        limits = self.get_limits()
        for window in self.window_manager.open_windows:
            window.set_limits(limits)

    def toggle_menu(self):
        if self.menubar is None:
            return
        if self.menubar_shown:
            self.hide_menu()
        else:
            self.show_menu()
        settings.show_menubar = self.menubar_shown
        self.cosmonium.save_settings()

    def show_context_menu(self):
        over = self.mouse.get_over()
        if over is None and self.menubar_shown:
            return
        popup_menu = Popup(self.cosmonium, self.scale, self.popup_menu_config, over, self, self.popup_done)
        popup_menu.create()
        self.popup_menu_shown = True
