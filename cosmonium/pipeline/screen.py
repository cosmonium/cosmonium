#
# This file is part of Cosmonium.
#
# Copyright (C) 2018-2023 Laurent Deru.
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

from panda3d.core import WindowProperties
from panda3d.core import load_prc_file_data

from .. import settings


class Screen:

    def __init__(self, base, srgb, multisamples, stereoscopic):
        self.base = base
        self.srgb = srgb
        self.multisamples = multisamples
        self.stereoscopic_framebuffer = stereoscopic

    def _create_main_window(self):
        props = WindowProperties.get_default()
        have_window = False
        try:
            self.base.open_default_window(props=props)
            have_window = True
        except Exception:
            pass
        # TODO: Obsolete workaround
        if have_window:
            self.base.bufferViewer.win = self.base.win
        return have_window

    def request(self):
        if self.srgb:
            load_prc_file_data("", "framebuffer-srgb true")
        if self.multisamples > 0:
            load_prc_file_data("", "framebuffer-multisample 1")
            load_prc_file_data("", "multisamples %d" % self.multisamples)
        if self.stereoscopic_framebuffer:
            load_prc_file_data("", "framebuffer-stereo #t")

        if self._create_main_window():
            return

        # Window could not be created, test what when wrong
        if self.stereoscopic_framebuffer:
            print("Failed to open a window, disabling stereoscopic framebuffer...")
            load_prc_file_data("", "framebuffer-stereo #f")
            self.stereoscopic_framebuffer = False
            if self._create_main_window():
                return

        if self.multisamples > 0:
            print("Failed to open a window, disabling multisampling...")
            load_prc_file_data("", "framebuffer-multisample #f")
            self.multisamples = 0
            if self._create_main_window():
                return

        # Can't create window even without multisampling
        if settings.use_gl_version is not None:
            print("Failed to open window with OpenGL Core; falling back to older OpenGL.")
            load_prc_file_data("", "gl-version")
            if self._create_main_window():
                return
        print("Could not open any window")
        sys.exit(1)
