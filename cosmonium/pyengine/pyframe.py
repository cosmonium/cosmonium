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


from panda3d.core import LPoint3d, LVector3d, LQuaterniond, look_at
from ..astro.astro import calc_orientation
from ..astro import units
from math import pi
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

class ReferenceFrame(object):

    def get_center(self):
        raise NotImplementedError()

    def get_orientation(self):
        raise NotImplementedError()

    def get_absolute_reference_point(self):
        raise NotImplementedError()

    def get_absolute_position(self, frame_position):
        return self.get_absolute_reference_point() + self.get_local_position(frame_position)

    def get_local_position(self, frame_position):
        return self.get_center() + self.get_orientation().xform(frame_position)

    def get_frame_position(self, local_position):
        return self.get_orientation().conjugate().xform(local_position - self.get_center())

    def get_absolute_orientation(self, frame_orientation):
        return frame_orientation * self.get_orientation()

    def get_frame_orientation(self, absolute_orientation):
        return absolute_orientation * self.get_orientation().conjugate()

    def __str__(self):
        raise NotImplementedError()

class J2000BarycentricEclipticReferenceFrame(ReferenceFrame):
    def get_center(self):
        return LPoint3d()

    def get_orientation(self):
        return LQuaterniond()

    def get_absolute_reference_point(self):
        return LPoint3d()

    def get_local_position(self, frame_position):
        return frame_position

    def get_frame_position(self, local_position):
        return local_position

    def get_absolute_orientation(self, frame_orientation):
        return frame_orientation

    def get_frame_orientation(self, absolute_orientation):
        return absolute_orientation

    def __str__(self):
        return 'J2000BarycentricEclipticReferenceFrame'

class J2000BarycentricEquatorialReferenceFrame(ReferenceFrame):
    def get_center(self):
        return LPoint3d()

    def get_orientation(self):
        return units.J2000_Orientation

    def get_absolute_reference_point(self):
        return LPoint3d()

    def get_local_position(self, frame_position):
        return units.J2000_Orientation.xform(frame_position)

    def get_frame_position(self, local_position):
        return units.J2000_Orientation.conjugate().xform(local_position)

    def get_absolute_orientation(self, frame_orientation):
        return frame_orientation * units.J2000_Orientation

    def get_frame_orientation(self, absolute_orientation):
        return absolute_orientation * units.J2000_Orientation.conjugate()

    def __str__(self):
        return 'J2000BarycentricEquatorialReferenceFrame'

class AnchorReferenceFrame(ReferenceFrame):
    def __init__(self, anchor = None):
        self.anchor = anchor

    def set_anchor(self, anchor):
        self.anchor = anchor

    def get_center(self):
        return self.anchor.get_local_position()

    def get_absolute_reference_point(self):
        return self.anchor.get_absolute_reference_point()

    def __str__(self):
        return self.__class__.__name__ + '(' + self.anchor.body.get_name() + ')'

class J2000EclipticReferenceFrame(AnchorReferenceFrame):
    orientation = LQuaterniond()
    def get_orientation(self):
        return self.orientation

class J2000EquatorialReferenceFrame(AnchorReferenceFrame):
    orientation = LQuaterniond()
    orientation.setFromAxisAngleRad(-units.J2000_Obliquity / 180.0 * pi, LVector3d.unitX())
    def get_orientation(self):
        return self.orientation

class J2000BarycentricEquatorialReferenceFrame(J2000EquatorialReferenceFrame):
    def __init__(self):
        J2000EquatorialReferenceFrame.__init__(self, SolBarycenter())

class RelativeReferenceFrame(ReferenceFrame):
    def __init__(self, parent_frame, position, orientation):
        ReferenceFrame.__init__(self)
        self.parent_frame = parent_frame
        self.frame_position = position
        self.frame_orientation = orientation

    def get_center(self):
        return self.parent_frame.get_local_position(self.frame_position)

    def get_orientation(self):
        return self.parent_frame.get_absolute_orientation(self.frame_orientation)

    def get_absolute_reference_point(self):
        return self.parent_frame.get_absolute_reference_point()

    def __str__(self):
        return self.__class__.__name__ + '(' + str(self.parent_frame) + ')'

class CelestialReferenceFrame(AnchorReferenceFrame):
    """
    Reference frame build using the North pole axis (ra, decl) and the
    longitude at the node, where the perpendicular plane intersect the
    equatorial plane.
    """
    def __init__(self, body = None,
                 right_ascension=0.0, right_ascension_unit=units.Deg,
                 declination=0.0, declination_unit=units.Deg,
                 longitude_at_node=0.0, longitude_at_nod_units=units.Deg):
        AnchorReferenceFrame.__init__(self, body)
        self.right_asc = right_ascension * right_ascension_unit
        self.declination = declination * declination_unit
        self.longitude_at_node = longitude_at_node * longitude_at_nod_units

        longitude_quad = LQuaterniond()
        longitude_quad.setFromAxisAngleRad(self.longitude_at_node, LVector3d.unitZ())
        self.orientation = longitude_quad * calc_orientation(self.right_asc, self.declination, False) * J2000EquatorialReferenceFrame.orientation

    def get_orientation(self):
        return self.orientation

j2000GalacticReferenceFrame = CelestialReferenceFrame(right_ascension=units.J2000_GalacticNorthRightAscension,
                                                      declination=units.J2000_GalacticNorthDeclination,
                                                      longitude_at_node=units.J2000_GalacticNode
                                                      )

class OrbitReferenceFrame(AnchorReferenceFrame):
    def get_orientation(self):
        rot = self.anchor.orbit.frame.get_orientation()
        return rot

class EquatorialReferenceFrame(AnchorReferenceFrame):
    def get_orientation(self):
        rot = self.anchor.get_equatorial_rotation()
        return rot

class SynchroneReferenceFrame(AnchorReferenceFrame):
    def get_orientation(self):
        rot = self.anchor.get_sync_rotation()
        return rot

class SurfaceReferenceFrame(AnchorReferenceFrame):
    def __init__(self, body, long, lat):
        AnchorReferenceFrame.__init__(self, body)
        self.long = long
        self.lat = lat

    def get_center(self):
        return self.body.get_local_position() + self.body.get_sync_rotation().xform(self.get_center_parent_frame())

    def get_orientation(self):
        return self.get_orientation_parent_frame() * self.body.get_sync_rotation()

    #TODO: workaround until proper hierarchical frames are implemented
    def get_center_parent_frame(self):
        position = self.body.spherical_to_frame_cartesian((self.long, self.lat, self.body.get_apparent_radius()))
        return position

    def get_position_parent_frame(self, relative_pos):
        return self.get_center_parent_frame() + self.get_orientation_parent_frame().xform(relative_pos)

    def get_orientation_parent_frame(self):
        (x, y, _) = self.body.spherical_to_xy((self.long, self.lat, None))
        (normal, tangent, binormal) = self.body.get_normals_under_xy(x, y)
        rotation = LQuaterniond()
        look_at(rotation, binormal, normal)
        return rotation

class CartesianSurfaceReferenceFrame(AnchorReferenceFrame):
    def __init__(self, body, position):
        AnchorReferenceFrame.__init__(self, body)
        self.position = position

    def get_center(self):
        return self.body.get_local_position() + self.body.get_sync_rotation().xform(self.get_center_parent_frame())

    def get_orientation(self):
        return self.get_orientation_parent_frame() * self.body.get_sync_rotation()

    #TODO: workaround until proper hierarchical frames are implemented
    def get_center_parent_frame(self):
        position = LPoint3d(self.position[0], self.position[1], 0)
        return position

    def get_position_parent_frame(self, relative_pos):
        return self.get_center_parent_frame() + self.get_orientation_parent_frame().xform(relative_pos)

    def get_orientation_parent_frame(self):
        (lon, lat, vert) = self.body.get_lonlatvert_under(self.position)
        rotation = LQuaterniond()
        look_at(rotation, lon, vert)
        return rotation

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
