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

from panda3d.core import LPoint3d, LVector3d, LQuaterniond, look_at
from . import units
from math import pi

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

class ReferenceFrame(object):
    def get_center(self):
        raise Exception
    def get_orientation(self):
        raise Exception
    def get_local_position(self, relative_pos):
        return self.get_center() + self.get_orientation().xform(relative_pos)
    def get_rel_position(self, absolute_pos):
        return self.get_orientation().conjugate().xform(absolute_pos - self.get_center()) 
    def get_abs_orientation(self, relative_orien):
        return relative_orien * self.get_orientation()
    def get_rel_orientation(self, absolute_orien):
        return absolute_orien * self.get_orientation().conjugate()
    def set_parent_body(self, body):
        raise Exception

class AbsoluteReferenceFrame(ReferenceFrame):
    null_center = LPoint3d(0, 0, 0)
    null_orientation = LQuaterniond()
    def get_center(self):
        return self.null_center
    def get_orientation(self):
        return self.null_orientation
    def get_local_position(self, relative_pos):
        return relative_pos
    def get_rel_position(self, absolute_pos):
        return absolute_pos
    def get_abs_orientation(self, relative_orien):
        return relative_orien
    def get_rel_orientation(self, absolute_orien):
        return absolute_orien

class BodyReferenceFrame(ReferenceFrame):
    def __init__(self, body = None):
        self.body = body
        self.explicit_body = body is not None

    def set_parent_body(self, body):
        if not self.explicit_body:
            self.body = body

    def get_center(self):
        return self.body.get_local_position()

class J2000EclipticReferenceFrame(BodyReferenceFrame):
    orientation = LQuaterniond()
    def get_orientation(self):
        return self.orientation

class J2000EquatorialReferenceFrame(BodyReferenceFrame):
    orientation = LQuaterniond()
    orientation.setFromAxisAngleRad(-units.J2000_Obliquity / 180.0 * pi, LVector3d.unitX())
    def get_orientation(self):
        return self.orientation

class RelativeReferenceFrame(BodyReferenceFrame):
    def __init__(self, body = None, parent_frame = None):
        BodyReferenceFrame.__init__(self, body)
        self.parent_frame = parent_frame

    def get_orientation(self):
        return self.parent_frame.get_orientation()

class CelestialReferenceFrame(RelativeReferenceFrame):
    """
    Reference frame build using the North pole axis (ra, decl) and the
    longitude at the node, where the perpendicular plane intersect the
    equatorial plane.
    """
    def __init__(self, body = None,
                 right_asc=0.0, right_asc_unit=units.Deg,
                 declination=0.0, declination_unit=units.Deg,
                 longitude_at_node=0.0, longitude_at_nod_units=units.Deg):
        RelativeReferenceFrame.__init__(self, body)
        self.right_asc = right_asc * right_asc_unit
        self.declination = declination * declination_unit
        self.longitude_at_node = longitude_at_node * longitude_at_nod_units
        right_asc_quat=LQuaterniond()
        right_asc_quat.setFromAxisAngleRad(self.right_asc + pi / 2, LVector3d.unitZ())
        declination_quat = LQuaterniond()
        declination_quat.setFromAxisAngleRad(-self.declination + pi / 2, LVector3d.unitX())
        longitude_quad = LQuaterniond()
        longitude_quad.setFromAxisAngleRad(-self.longitude_at_node + pi / 2, LVector3d.unitZ())
        self.orientation = longitude_quad * declination_quat * right_asc_quat * J2000EquatorialReferenceFrame.orientation

    def get_orientation(self):
        return self.orientation

j2000GalacticReferenceFrame = CelestialReferenceFrame(right_asc=units.J2000_GalacticNorthRightAscension,
                                                      declination=units.J2000_GalacticNorthDeclination,
                                                      longitude_at_node=units.J2000_GalacticNode
                                                      )

class EquatorialReferenceFrame(RelativeReferenceFrame):
    def get_orientation(self):
        rot = self.body.get_equatorial_rotation()
        return rot

class SynchroneReferenceFrame(RelativeReferenceFrame):
    def get_orientation(self):
        rot = self.body.get_sync_rotation()
        return rot

class SurfaceReferenceFrame(RelativeReferenceFrame):
    def __init__(self, long, lat):
        RelativeReferenceFrame.__init__(self)
        self.long = long
        self.lat = lat

    def set_parent_body(self, body):
        self.body = body
        if self.body.primary is not None:
            self.body = self.body.primary

    def get_center(self):
        return self.body.get_local_position() + self.body.get_sync_rotation().xform(self.get_center_parent_frame())

    def get_orientation(self):
        return self.get_orientation_parent_frame() * self.body.get_sync_rotation()

    #TODO: workaround until proper hierarchical frames are implemented
    def get_center_parent_frame(self):
        (x, y, _) = self.body.spherical_to_xy((self.long, self.lat, None))
        distance = self.body.get_height_under_xy(x, y)
        position = self.body.spherical_to_frame_cartesian((self.long, self.lat, distance))
        return position

    def get_position_parent_frame(self, relative_pos):
        return self.get_center_parent_frame() + self.get_orientation_parent_frame().xform(relative_pos)

    def get_orientation_parent_frame(self):
        (x, y, _) = self.body.spherical_to_xy((self.long, self.lat, None))
        (normal, tangent, binormal) = self.body.get_normals_under_xy(x, y)
        rotation = LQuaterniond()
        look_at(rotation, binormal, normal)
        return rotation

class FramesDB(object):
    def __init__(self):
        self.frames = {}

    def register_frame(self, frame_name, frame):
        self.frames[frame_name] = frame

    def get(self, name):
        if name in self.frames:
            return self.frames[name]
        else:
            print("DB frames:", "Frame", name, "not found")

frames_db = FramesDB()
