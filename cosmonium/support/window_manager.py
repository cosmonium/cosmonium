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


import sys

from panda3d.core import LColor, Texture, WindowProperties

from .. import settings
from ..parsers.configparser import configParser

# Minimum size of a window that must be on the desktop to be reachable by the user
MIN_VISIBLE = 64


def is_window_reachable(x, y, width, height, desktop_width, desktop_height):
    """Check that a window is visible enough for the user to be able to move it"""
    return (
        x + width >= MIN_VISIBLE and x <= desktop_width - MIN_VISIBLE and y >= 0 and y <= desktop_height - MIN_VISIBLE
    )


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
        # Position of the window when switching to fullscreen
        self.windowed_origin = None

    def get_desktop_size(self) -> tuple:
        """Get the size of the desktop"""
        return self.app.pipe.getDisplayWidth(), self.app.pipe.getDisplayHeight()

    def scale_default_size(self) -> None:
        """
        Scale the default window size with the display zoom.

        The default size is expressed in logical pixels, so it is only scaled when it comes from the defaults.
        A size saved in the configuration is in physical pixels and is used as is.
        """
        if settings.win_size_configured or settings.win_fullscreen or not settings.ui_scale_dpi_aware:
            return
        zoom = self.app.pipe.display_zoom
        if zoom == 1.0:
            return
        width = int(settings.win_width * zoom)
        height = int(settings.win_height * zoom)
        # Do not create a window larger than the screen
        screen_width = self.app.pipe.getDisplayWidth()
        screen_height = self.app.pipe.getDisplayHeight()
        if screen_width > 0 and screen_height > 0:
            width = min(width, screen_width)
            height = min(height, screen_height)
        settings.win_width = width
        settings.win_height = height
        wp = WindowProperties(self.app.win.getProperties())
        wp.setSize(*self.get_windowed_size())
        self.app.win.requestProperties(wp)

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

    def save_windowed_origin(self) -> None:
        """Remember the position of the window to restore it when leaving fullscreen"""
        wp = self.app.win.getProperties()
        if wp.hasOrigin() and not wp.getFullscreen():
            self.windowed_origin = (wp.getXOrigin(), wp.getYOrigin())

    def get_windowed_size(self) -> tuple:
        """Get the size of the window when leaving fullscreen, limited to the desktop size"""
        desktop_width, desktop_height = self.get_desktop_size()
        return min(settings.win_width, desktop_width), min(settings.win_height, desktop_height)

    def get_windowed_origin(self) -> tuple:
        """
        Get the position of the window when leaving fullscreen.

        The position saved when entering fullscreen is used, unless the desktop layout changed in the meantime and
        it is not reachable anymore. Otherwise the window is centered on the desktop.
        """
        width, height = self.get_windowed_size()
        desktop_width, desktop_height = self.get_desktop_size()
        if self.windowed_origin is not None:
            x, y = self.windowed_origin
            # The desktop size is only known for the primary monitor on Windows and macOS, the position of the
            # window can be valid on another monitor. There the system keeps the windows reachable.
            if not sys.platform.startswith('linux') or is_window_reachable(
                x, y, width, height, desktop_width, desktop_height
            ):
                return x, y
        return max(0, (desktop_width - width) // 2), max(0, (desktop_height - height) // 2)

    def toggle_fullscreen(self) -> None:
        """
        Toggle fullscreen mode.
        """
        if not settings.win_fullscreen:
            self.save_windowed_origin()
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
            wp.setSize(*self.get_windowed_size())
            wp.setOrigin(*self.get_windowed_origin())
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
        elif not wp.getFullscreen():
            # The window may still be fullscreen when leaving fullscreen, the size is then not the windowed size
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
