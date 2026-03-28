#
# This file is part of Cosmonium.
#
# Copyright (C) 2018-2026 Laurent Deru.
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

from ..astro import units
from ..astro.astro import calc_orientation
from ..astro.elementsdb import orbit_elements_db
from ..astro.frame import AbsoluteReferenceFrame, BodyReferenceFrames, J2000EclipticReferenceFrame
from ..astro.orbits import AbsoluteFixedPosition, EllipticalOrbit, LocalFixedPosition
from .framesparser import FrameYamlParser
from .objectparser import ObjectYamlParser
from .schemas.orbit import EllipticOrbitConfig, FixedOrbitConfig, GlobalPositionConfig
from .utilsparser import AngleSpeedUnitsYamlParser, AngleUnitsYamlParser, DistanceUnitsYamlParser, TimeUnitsYamlParser
from .yamlparser import TypedYamlParser, YamlModuleParser


class EllipticOrbitYamlParser(YamlModuleParser):
    @classmethod
    def decode(cls, data, frame=None, parent=None):
        semi_major_axis = data.semi_major_axis
        semi_major_axis_units = DistanceUnitsYamlParser.decode(data.semi_major_axis_units)
        pericenter_distance = data.pericenter_distance
        pericenter_distance_units = DistanceUnitsYamlParser.decode(data.pericenter_distance_units)
        period = data.period
        period_units = TimeUnitsYamlParser.decode(data.period_units)
        mean_motion = data.mean_motion
        mean_motion_units = AngleSpeedUnitsYamlParser.decode(data.mean_motion_units)
        eccentricity = data.eccentricity
        inclination = data.inclination
        ascending_node = data.ascending_node
        arg_of_periapsis = data.arg_of_periapsis
        long_of_pericenter = data.long_of_pericenter
        mean_anomaly = data.mean_anomaly
        time_of_perihelion = data.time_of_perihelion
        mean_longitude = data.mean_longitude
        epoch = data.epoch if data.epoch is not None else units.J2000
        if data.frame is not None or frame is None:
            frame = FrameYamlParser.decode(data.frame if data.frame else 'j2000ecliptic', parent)

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
    def decode(cls, data, frame=None, parent=None):
        position = data.position
        if position is None:
            ra = data.ra
            ra_units = AngleUnitsYamlParser.decode(data.ra_units)
            decl = data.de
            decl_units = AngleUnitsYamlParser.decode(data.de_units)
            distance = data.distance
            distance_units = DistanceUnitsYamlParser.decode(data.distance_units)
            frame = AbsoluteReferenceFrame()
            global_pos = True
            orientation = calc_orientation(ra * ra_units, decl * decl_units) * units.J2000_Orientation
            position = orientation.xform(LPoint3d(0, 0, distance * distance_units))
            frame = AbsoluteReferenceFrame()  # TODO: This should be J2000BarycentricEclipticReferenceFrame
        else:
            position = data.position
            global_pos = data.global_
            if data.frame is not None or frame is None:
                frame = FrameYamlParser.decode(data.frame if data.frame else 'j2000ecliptic', parent)
        if global_pos:
            return AbsoluteFixedPosition(absolute_reference_point=position, frame=frame)
        else:
            return LocalFixedPosition(frame_position=position, frame=frame)


class GlobalPositionYamlParser(YamlModuleParser):
    @classmethod
    def decode(cls, data, frame=None, parent=None):
        position = data.position
        position_units = DistanceUnitsYamlParser.decode(data.position_units)
        if data.frame is not None or frame is None:
            frame = FrameYamlParser.decode(data.frame if data.frame else 'j2000ecliptic', parent)
        return AbsoluteFixedPosition(absolute_reference_point=position * position_units, frame=frame)


class OrbitYamlParser(TypedYamlParser):
    """Parser for orbit types with validation."""

    @classmethod
    def decode(cls, data, frame=None, parent=None):
        if data is None:
            data = {'type': 'fixed', 'position': (0, 0, 0), 'global': False}
        object_type, parameters = cls.get_type_and_data(data)

        if object_type in cls.parsers:
            # Validate and decode using registered parser
            validated_parameters = cls.validate_and_decode(object_type, parameters)
            orbit = cls.parsers[object_type].decode(validated_parameters, frame, parent)
        else:
            orbit = orbit_elements_db.get(data)
            if orbit is None:
                print("Unknown orbit reference", data)
                # TODO: An error should be raised instead !
                orbit = AbsoluteFixedPosition(absolute_reference_point=LPoint3d(), frame=J2000EclipticReferenceFrame())
            # TODO: this should not be done arbitrarily
            if isinstance(orbit.frame, BodyReferenceFrames) and orbit.frame.anchor is None:
                orbit.frame.set_anchor(parent.anchor)
        return orbit


class OrbitCategoryYamlParser(YamlModuleParser):
    @classmethod
    def decode(cls, data, parent=None):
        name = data.get('name')
        priority = data.get('priority')
        orbit_elements_db.register_category(name, priority)
        return None


class NamedOrbitYamlParser(YamlModuleParser):
    @classmethod
    def decode(cls, data, parent=None):
        name = data.get('name')
        category = data.get('category')
        if name is None or category is None:
            return None
        orbit = OrbitYamlParser.decode(data)
        orbit_elements_db.register_element(category, name, orbit)
        return None


def register_orbit_parsers():
    """Register orbit type parsers with their models."""
    # Register orbit types with OrbitYamlParser
    OrbitYamlParser.register_parser('elliptic', EllipticOrbitYamlParser, EllipticOrbitConfig)
    OrbitYamlParser.register_parser('fixed', FixedPositionYamlParser, FixedOrbitConfig)
    OrbitYamlParser.register_parser('global', GlobalPositionYamlParser, GlobalPositionConfig)

    # Register top-level object parsers
    ObjectYamlParser.register_object_parser('orbit', NamedOrbitYamlParser())
    ObjectYamlParser.register_object_parser('elliptic', NamedOrbitYamlParser())
    ObjectYamlParser.register_object_parser('fixed', NamedOrbitYamlParser())
    ObjectYamlParser.register_object_parser('global', NamedOrbitYamlParser())
    ObjectYamlParser.register_object_parser('orbit-category', OrbitCategoryYamlParser())
