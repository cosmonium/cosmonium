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


from panda3d.core import LColor, Texture, WindowProperties

from .. import settings
from ..parsers.configparser import configParser


class WindowManager:
    """Manages window events, fullscreen mode, and resolution changes."""

    def __init__(self, app):
        """
        Initialize the WindowManager.

        Args:
            app: The main application instance (CosmoniumBase or Cosmonium)
        """
        self.app = app
        self.request_fullscreen = False

    def get_fullscreen_sizes(self):
        """Get available fullscreen resolutions from the display."""
        info = self.app.pipe.getDisplayInformation()
        resolutions = []
        for idx in range(info.getTotalDisplayModes()):
            width = info.getDisplayModeWidth(idx)
            height = info.getDisplayModeHeight(idx)
            resolutions.append([width, height])
        resolutions.sort(key=lambda x: x[0], reverse=True)
        return resolutions

    def toggle_fullscreen(self) -> None:
        """
        Toggle fullscreen mode.
        """
        settings.win_fullscreen = not settings.win_fullscreen
        wp = WindowProperties(self.app.win.getProperties())
        wp.setFullscreen(settings.win_fullscreen)
        if settings.win_fullscreen:
            if settings.win_fs_width != 0 and settings.win_fs_height != 0:
                win_fs_width = settings.win_fs_width
                win_fs_height = settings.win_fs_height
            else:
                win_fs_width = self.app.pipe.getDisplayWidth()
                win_fs_height = self.app.pipe.getDisplayHeight()
            wp.setSize(win_fs_width, win_fs_height)
            # Defer config saving in case the switch fails
            self.request_fullscreen = True
        else:
            wp.setSize(settings.win_width, settings.win_height)
            configParser.save()
        self.app.win.requestProperties(wp)

    def window_event(self, window) -> None:
        """
        Handle window events such as resize and close.

        Args:
            window: The window that triggered the event
        """
        if self.app.win is None:
            return
        if self.app.win.is_closed():
            self.app.userExit()

        wp = self.app.win.getProperties()
        width = wp.getXSize()
        height = wp.getYSize()

        if settings.win_fullscreen:
            # Only save config if the switch to FS is successful
            if wp.getFullscreen():
                if self.request_fullscreen or width != settings.win_fs_width or height != settings.win_fs_height:
                    settings.win_fs_width = width
                    settings.win_fs_height = height
                    configParser.save()
                if self.request_fullscreen:
                    if self.app.gui is not None:
                        self.app.gui.update_info("Press <Alt-Enter> to leave fullscreen mode", duration=0.5, fade=2.0)
            else:
                if self.app.gui is not None:
                    self.app.gui.update_info("Could not switch to fullscreen mode", duration=0.5, fade=2.0)
                settings.win_fullscreen = False
            self.request_fullscreen = False
        else:
            if width != settings.win_width or height != settings.win_height:
                settings.win_width = width
                settings.win_height = height
                configParser.save()

        # Update app components
        if self.app.observer is not None:
            self.app.observer.set_film_size(width, height)

        if self.app.common_state is not None:
            self.app.common_state.setShaderInput(
                "near_plane_height", self.app.observer.height / self.app.observer.tan_fov2
            )
            self.app.common_state.setShaderInput("pixel_size", self.app.observer.pixel_size)
            self.app.common_state.setShaderInput("win_size", (width, height))

        if self.app.pipeline is not None:
            self.app.pipeline.update_win_size(width, height)

        if self.app.gui is not None:
            self.app.gui.update_size(width, height)

        if settings.color_picking and self.app.oid_texture is not None:
            self.app.oid_texture.clear()
            self.app.oid_texture.setup_2d_texture(width, height, Texture.T_unsigned_byte, Texture.F_rgba8)
            self.app.oid_texture.set_clear_color(LColor(0, 0, 0, 0))
