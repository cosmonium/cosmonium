#
#This file is part of Cosmonium.
#
#Copyright (C) 2018-2021 Laurent Deru.
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

from copy import copy

# Coordinate System
# Panda3D Coordinate system : Z-Up Right-handed
#    x : right
#    y : forward (into screen)
#    z : up
# Mapped onto J2000.0 Ecliptic frame
#    x : vernal equinox
#    y : 
#    z : North Pole
#
# Celestia and SpaceEngine are Y-Up Right-handed
#    Panda3d = Cel/SE
#      x    =    x
#      y    =    z
#      z    =   -y

try:
    from cosmonium_engine import AnchorReferenceFrame, J2000EclipticReferenceFrame, J2000EquatorialReferenceFrame, CelestialReferenceFrame, EquatorialReferenceFrame, SynchroneReferenceFrame, RelativeReferenceFrame
    from cosmonium_engine import J2000BarycentricEclipticReferenceFrame, J2000BarycentricEquatorialReferenceFrame
    SurfaceReferenceFrame = AnchorReferenceFrame
except ImportError as e:
    print("WARNING: Could not load frames C implementation, fallback on python implementation")
    print("\t", e)
    from ..pyengine.pyframe import AnchorReferenceFrame, J2000EclipticReferenceFrame, J2000EquatorialReferenceFrame, CelestialReferenceFrame, EquatorialReferenceFrame, SynchroneReferenceFrame, RelativeReferenceFrame
    from ..pyengine.pyframe import J2000BarycentricEclipticReferenceFrame, J2000BarycentricEquatorialReferenceFrame
    from ..pyengine.pyframe import SurfaceReferenceFrame

BodyReferenceFrame = AnchorReferenceFrame
AbsoluteReferenceFrame = J2000BarycentricEclipticReferenceFrame

class FramesDB(object):
    def __init__(self):
        self.frames = {}

    def register_frame(self, frame_name, frame):
        self.frames[frame_name] = frame

    def get(self, name):
        if name in self.frames:
            return copy(self.frames[name])
        else:
            print("DB frames:", "Frame", name, "not found")

frames_db = FramesDB()
