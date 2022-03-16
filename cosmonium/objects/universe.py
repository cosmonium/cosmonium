#
#This file is part of Cosmonium.
#
#Copyright (C) 2018-2022 Laurent Deru.
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


from panda3d.core import LPoint3d, LQuaterniond

from ..astro.orbits import AbsoluteFixedPosition
from ..astro.rotations import FixedRotation
from ..astro.frame import AbsoluteReferenceFrame
from ..engine.anchors import UniverseAnchor

from .systems import OctreeSystem

class Universe(OctreeSystem):
    def __init__(self, context):
        OctreeSystem.__init__(self, ['Universe'], [],
                              orbit=AbsoluteFixedPosition(absolute_reference_point=LPoint3d(),
                                                          frame=AbsoluteReferenceFrame()),
                              rotation=FixedRotation(LQuaterniond(), frame=AbsoluteReferenceFrame()),
                              description='Universe')
        self.visible = True

    def create_anchor(self, anchor_class, orbit, rotation, point_color):
        return UniverseAnchor(self, orbit, rotation, point_color)

    def get_fullname(self, separator='/'):
        return ''
