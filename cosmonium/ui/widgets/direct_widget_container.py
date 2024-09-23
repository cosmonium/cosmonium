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


class DirectWidgetContainer:
    def __init__(self, widget):
        self.frame = widget

    def destroy(self):
        self.frame.destroy()

    def frameSize(self):
        return self.frame['frameSize']

    def reparentTo(self, parent):
        self.frame.reparent_to(parent)

    def setPos(self, *args):
        self.frame.setPos(*args)

    frame_size = frameSize
    reparent_to = reparentTo
    set_pos = setPos
