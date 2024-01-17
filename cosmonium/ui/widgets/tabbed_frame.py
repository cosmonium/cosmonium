#
#This file is part of Cosmonium.
#
#Copyright (C) 2018-2024 Laurent Deru.
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


from panda3d.core import LPoint3
from .direct_widget_container import DirectWidgetContainer


class TabbedFrameContainer(DirectWidgetContainer):

    def __init__(self, widget):
        super().__init__(widget)
        self.height_offset = self.frame['tab_frameSize'][3] * self.frame['tab_scale'][2]
        self.frame.set_pos(LPoint3(0, 0, -self.height_offset))

    def setPos(self, *args):
        if len(args) == 1:
            pos = args[0]
        else:
            pos = LPoint3(*args)
        self.frame.set_pos(LPoint3(pos[0], 0, pos[2] - self.height_offset))

    set_pos = setPos
