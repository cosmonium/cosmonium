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

from __future__ import print_function
from __future__ import absolute_import

from direct.gui.DirectGui import DirectFrame, DGG
from direct.showbase.ShowBaseGlobal import aspect2d

class Layout(object):
    def __init__(self, width, height, parent=None, frameColor=(1, 1, 1, 1), frameSize=(0, 0.5, -0.5, 0)):
        self.width = width
        self.height = height
        if parent is None:
            parent = aspect2d
        self.parent = parent
        self.frame = DirectFrame(parent=parent, frameColor=frameColor, frameSize=frameSize, state=DGG.DISABLED)
        self.frame.setPos(0, 0, 0)
        self.children = [[None for y in range(self.height)] for x in range(self.width)]
        self.children_width = [[0.0 for y in range(self.height)] for x in range(self.width)]
        self.children_height = [[0.0 for y in range(self.height)] for x in range(self.width)]

    def set_child(self, x, y, child):
        if x >= self.width or y >= self.height: return
        child.reparent_to(self.frame)
        self.children[x][y] = child
        bounds = child.getBounds()
        if bounds is not None:
            width = bounds[1] - bounds[0]
            height = bounds[3] - bounds[2]
            self.children_width[x][y] = width
            self.children_height[x][y] = height
        else:
            self.children_width[x][y] = 0
            self.children_height[x][y] = 0

    def recalc_positions(self):
        max_widths = []
        for x in range(self.width):
            max_width = 0.0
            for y in range(self.height):
                max_width = max(max_width, self.children_width[x][y])
            max_widths.append(max_width)
        max_heights = []
        for y in range(self.height):
            max_height = 0.0
            for x in range(self.width):
                max_height = max(max_height, self.children_height[x][y])
            max_heights.append(max_height)
        pos_x = 0.0
        for x in range(self.width):
            pos_y = 0.0
            for y in range(self.height):
                pos_y -= max_heights[y]
                child = self.children[x][y]
                if child is not None:
                    child.setPos(pos_x, 0, pos_y)
            pos_x += max_widths[x]
        self.frame['frameSize']= [0, pos_x, 0, pos_y]

    def destroy(self):
        self.frame.destroy()

    def reparent_to(self, parent):
        self.frame.reparent_to(parent)
