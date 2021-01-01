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

from panda3d.core import LPoint3d, LQuaterniond

from .astro.orbits import FixedOrbit
from .astro.rotations import FixedRotation
from .astro.frame import AbsoluteReferenceFrame

from .systems import OctreeSystem
from .anchors import UniverseAnchor

class Universe(OctreeSystem):
    def __init__(self, context):
        OctreeSystem.__init__(self, ['Universe'], [],
                              orbit=FixedOrbit(frame=AbsoluteReferenceFrame()),
                              rotation=FixedRotation(LQuaterniond(), frame=AbsoluteReferenceFrame()),
                              description='Universe')
        self.visible = True

    def create_anchor(self, anchor_class, orbit, rotation, point_color):
        return UniverseAnchor(anchor_class, self, orbit, rotation, point_color)

    def get_fullname(self, separator='/'):
        return ''

    def get_distance(self, time):
        return 0

    def get_global_position(self):
        return LPoint3d()
    
    def get_abs_rotation(self):
        return self._orientation

    def update_and_update_observer(self, time, observer, frustum, camera_global_position, camera_local_position, pixel_size):
        self.anchor.update_and_update_observer_children(time, observer, frustum, camera_global_position, camera_local_position, pixel_size)
