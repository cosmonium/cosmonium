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


from math import pi
from panda3d.core import LPoint3d

from ..astro.astro import calc_orientation
from ..astro.elementsdb import orbit_elements_db
from ..astro.frame import AbsoluteReferenceFrame, BodyReferenceFrames, J2000EclipticReferenceFrame
from ..astro.orbits import AbsoluteFixedPosition, LocalFixedPosition, EllipticalOrbit
from ..astro import units

from .framesparser import FrameYamlParser
from .objectparser import ObjectYamlParser
from .utilsparser import DistanceUnitsYamlParser, TimeUnitsYamlParser, AngleUnitsYamlParser, AngleSpeedUnitsYamlParser
from .yamlparser import YamlModuleParser


class EllipticOrbitYamlParser(YamlModuleParser):
    @classmethod
    def decode(self, data, frame=None, parent=None):
        semi_major_axis = data.get('semi-major-axis', None)
        semi_major_axis_units = DistanceUnitsYamlParser.decode(data.get('semi-major-axis-units', 'AU'))
        pericenter_distance = data.get('pericenter-distance', None)
        pericenter_distance_units = DistanceUnitsYamlParser.decode(data.get('pericenter-distance-units', 'AU'))
        period = data.get('period', None)
        period_units = TimeUnitsYamlParser.decode(data.get('period-units', 'Year'))
        mean_motion = data.get('mean-motion', None)
        mean_motion_units = AngleSpeedUnitsYamlParser.decode(data.get('mean-motion-units', 'deg/day'))
        eccentricity = data.get('eccentricity', 0.0)
        inclination = data.get('inclination', 0.0)
        ascending_node = data.get('ascending-node', 0.0)
        arg_of_periapsis = data.get('arg-of-periapsis', None)
        long_of_pericenter = data.get('long-of-pericenter', None)
        mean_anomaly = data.get('mean-anomaly', None)
        time_of_perihelion = data.get('time-of-perihelion', None)
        mean_longitude = data.get('mean-longitude', 0.0)
        epoch = data.get('epoch', units.J2000)
        if data.get('frame') is not None or frame is None:
            frame = FrameYamlParser.decode(data.get('frame', 'J2000Ecliptic'), parent)

        if pericenter_distance is None:
            if semi_major_axis is None:
                # TODO: raise error
                pericenter_distance = 1
            else:
                pericenter_distance = semi_major_axis * semi_major_axis_units * (1.0 - eccentricity)
        else:
            pericenter_distance = pericenter_distance * pericenter_distance_units

        if period is None:
            if mean_motion is None:
                # TODO: raise error
                period = 1.0
            else:
                period = 2 * pi / (mean_motion * mean_motion_units)
        else:
            period = period * period_units

        if arg_of_periapsis is None:
            if long_of_pericenter is None:
                arg_of_periapsis = 0.0
            else:
                arg_of_periapsis = (long_of_pericenter - ascending_node) % 360.0
        if mean_anomaly is None:
            if mean_longitude is None:
                mean_anomaly = (epoch - time_of_perihelion) * (2 * pi / period) * 180 / pi
            else:
                mean_anomaly = (mean_longitude - (arg_of_periapsis + ascending_node)) % 360

        return EllipticalOrbit(
            frame,
            epoch,
            2 * pi / period,
            mean_anomaly * units.Deg,
            pericenter_distance,
            eccentricity,
            arg_of_periapsis * units.Deg,
            inclination * units.Deg,
            ascending_node * units.Deg,
        )


class FixedPositionYamlParser(YamlModuleParser):
    @classmethod
    def decode(self, data, frame=None, parent=None):
        position = data.get('position', None)
        if position is None:
            ra = data.get('ra', 0.0)
            ra_units = AngleUnitsYamlParser.decode(data.get('ra-units', 'Deg'))
            decl = data.get('de', 0.0)
            decl_units = AngleUnitsYamlParser.decode(data.get('de-units', 'Deg'))
            distance = data.get('distance', 0.0)
            distance_units = DistanceUnitsYamlParser.decode(data.get('distance-units', 'pc'))
            frame = AbsoluteReferenceFrame()
            global_pos = True
            orientation = calc_orientation(ra * ra_units, decl * decl_units) * units.J2000_Orientation
            position = orientation.xform(LPoint3d(0, 0, distance * distance_units))
            frame = AbsoluteReferenceFrame()  # TDODO: This should be J2000BarycentricEclipticReferenceFrame
        else:
            position = LPoint3d(*position)
            global_pos = data.get("global", True)
            if data.get('frame') is not None or frame is None:
                frame = FrameYamlParser.decode(data.get('frame', 'J2000Ecliptic'), parent)
        if global_pos:
            return AbsoluteFixedPosition(absolute_reference_point=position, frame=frame)
        else:
            return LocalFixedPosition(frame_position=position, frame=frame)


class GlobalPositionYamlParser(YamlModuleParser):
    @classmethod
    def decode(self, data, frame=None, parent=None):
        position = LPoint3d(*data.get('position', [0, 0, 0]))
        position_units = DistanceUnitsYamlParser.decode(data.get('position-units', 'pc'))
        if data.get('frame') is not None or frame is None:
            frame = FrameYamlParser.decode(data.get('frame', 'J2000Ecliptic'), parent)
        return AbsoluteFixedPosition(absolute_reference_point=position * position_units, frame=frame)


class OrbitYamlParser(YamlModuleParser):
    @classmethod
    def decode(cls, data, frame=None, parent=None):
        if data is None:
            data = {'type': 'fixed', 'position': (0, 0, 0), 'global': False}
        (object_type, parameters) = cls.get_type_and_data(data)
        if object_type == 'elliptic':
            orbit = EllipticOrbitYamlParser.decode(parameters, frame, parent)
        elif object_type == 'fixed':
            orbit = FixedPositionYamlParser.decode(parameters, frame, parent)
        elif object_type == 'global':
            orbit = GlobalPositionYamlParser.decode(parameters, frame, parent)
        else:
            orbit = orbit_elements_db.get(data)
            if orbit is None:
                # TODO: An error should be raised instead !
                orbit = AbsoluteFixedPosition(frame=J2000EclipticReferenceFrame())
            # TODO: this should not be done arbitrarily
            if isinstance(orbit.frame, BodyReferenceFrames) and orbit.frame.anchor is None:
                orbit.frame.set_anchor(parent.anchor)
        return orbit


class OrbitCategoryYamlParser(YamlModuleParser):
    @classmethod
    def decode(self, data, parent=None):
        name = data.get('name')
        priority = data.get('priority')
        orbit_elements_db.register_category(name, priority)
        return None


class NamedOrbitYamlParser(YamlModuleParser):
    @classmethod
    def decode(self, data, parent=None):
        name = data.get('name')
        category = data.get('category')
        if name is None or category is None:
            return None
        orbit = OrbitYamlParser.decode(data)
        orbit_elements_db.register_element(category, name, orbit)
        return None


def register_orbit_parsers():
    ObjectYamlParser.register_object_parser('orbit', NamedOrbitYamlParser())
    ObjectYamlParser.register_object_parser('orbit-category', OrbitCategoryYamlParser())
