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
from panda3d.core import NodePath, TextNode

from .base import FrameColorTexture


class DecoratedSizer(Sizer):

    def __init__(self, border, image, geom, border_color, *args, **kwargs):
        Sizer.__init__(self, *args, **kwargs)
        self.frame = None
        self.border = border
        self.image = image
        self.geom = geom
        self.border_color = border_color

    def create(self, parent, skin):
        borders_parameters = skin.get_dgui_parameters_for('default', 'borders')
        self.colors = FrameColorTexture(**borders_parameters)
        frame_parameters = skin.get_dgui_parameters_for('default', 'frame')
        self.frame = DirectFrame(
            **frame_parameters,
            parent=parent,
            state=DGG.NORMAL,
            )
        self.bg_frame = DirectFrame(
            **frame_parameters,
            parent=self.frame,
            state=DGG.NORMAL,
            )

    def update_frame(self):
        size = self.get_size()
        self.frame['frameSize'] = (0, size[0] + 1, -size[1] - 1, 0)
        self.bg_frame['frameSize'] = (0, size[0] - self.border[0] * 2 + 1, -size[1] + self.border[1] * 2 - 1, 0)
        self.bg_frame.set_pos(self.border[0], 0, -self.border[1])
        decorator = TextNode('bg')
        decorator.set_text(" ")
        decorator.set_card_actual(*self.frame['frameSize'])
        decorator.set_card_border(self.border[0] * 2, 1 / 3)
        decorator.set_card_texture(self.colors.texture)
        self.frame['geom'] = NodePath(decorator.generate())

    def set_pos(self, pos):
        Sizer.set_pos(self, pos)
        x, y = pos
        self.frame.set_pos(x, 0, -y)

    def update(self, size=None):
        Sizer.update(self, size=size)
        self.update_frame()
