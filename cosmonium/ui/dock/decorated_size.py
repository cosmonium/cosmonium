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

from __future__ import annotations

from direct.gui import DirectGuiGlobals as DGG
from direct.gui.DirectFrame import DirectFrame
from directguilayout.gui import Sizer

from ...geometry.geometry import FrameGeom
from .base import FrameColorTexture


class DecoratedSizer(Sizer):

    def __init__(self, border, image, geom, *args, **kwargs):
        Sizer.__init__(self, *args, **kwargs)
        self.frame = None
        self.border = border
        self.image = image
        self.geom = geom
        self.border_color = None

    def create(self, parent, skin):
        borders_parameters = skin.get_dgui_parameters_for('borders')
        self.colors = FrameColorTexture(**borders_parameters)
        frame_parameters = skin.get_dgui_parameters_for('frame')
        self.frame = DirectFrame(
            **frame_parameters,
            parent=parent,
            state=DGG.NORMAL,
            )
        self.border_color = skin.border_color

    def update_frame(self):
        size = self.get_size()
        self.frame['frameSize'] = (0, size[0], -size[1], 0)
        geom = FrameGeom(size, self.border, texture=False)
        geom.set_color(*self.border_color)
        self.frame['geom'] = geom

    def set_pos(self, pos):
        Sizer.set_pos(self, pos)
        x, y = pos
        self.frame.set_pos(x, 0, -y)

    def update(self, size=None):
        Sizer.update(self, size=size)
        self.update_frame()
