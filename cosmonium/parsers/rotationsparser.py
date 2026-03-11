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

from panda3d.core import LQuaterniond, LVector3d

from ..astro import units
from ..astro.astro import calc_orientation, calc_orientation_from_incl_an
from ..astro.elementsdb import rotation_elements_db
from ..astro.frame import BodyReferenceFrames
from ..astro.rotations import FixedRotation, SynchronousRotation, UniformRotation, UnknownRotation
from ..mathutil.quaternion import quaternion_from_axis_angle
from .framesparser import FrameYamlParser
from .objectparser import ObjectYamlParser
from .schemas.rotation import FixedRotationConfig, UniformRotationConfig
from .utilsparser import AngleUnitsYamlParser, TimeUnitsYamlParser
from .yamlparser import TypedYamlParser, YamlModuleParser


class OrientationYamlParser(YamlModuleParser):
    @classmethod
    def decode(cls, data, flipped):
        inclination = data.inclination if data.inclination is not None else 0.0
        inclination_units = AngleUnitsYamlParser.decode(data.inclination_units)
        ascending_node = data.ascending_node if data.ascending_node is not None else 0.0
        ascending_node_units = AngleUnitsYamlParser.decode(data.ascending_node_units)
        right_ascension = data.ra
        right_ascension_units = AngleUnitsYamlParser.decode(data.ra_units)
        declination = data.de if data.de is not None else 0.0
        declination_units = AngleUnitsYamlParser.decode(data.de_units)
        if right_ascension is not None:
            orientation = calc_orientation(
                right_ascension * right_ascension_units, declination * declination_units, flipped
            )
        else:
            orientation = calc_orientation_from_incl_an(
                inclination * inclination_units, ascending_node * ascending_node_units, flipped
            )
        return orientation


class UniformYamlParser(YamlModuleParser):
    @classmethod
    def decode(cls, data, frame, parent):
        synchronous = data.synchronous if data.synchronous is not None else False
        period = data.period
        period_units = TimeUnitsYamlParser.decode(data.period_units)
        meridian_angle = data.meridian if data.meridian is not None else 0.0
        meridian_units = AngleUnitsYamlParser.decode(data.meridian_units)
        epoch = data.epoch if data.epoch is not None else units.J2000
        if data.frame is not None or frame is None:
            if data.ra is not None:
                default_frame = 'j2000equatorial'
            else:
                default_frame = 'j2000ecliptic'
            frame = FrameYamlParser.decode(data.frame if data.frame else default_frame, parent)
        flipped = period is not None and period < 0
        orientation = OrientationYamlParser.decode(data, flipped)
        if synchronous:
            rotation = SynchronousRotation(orientation, meridian_angle * meridian_units, epoch, frame)
            if parent is not None:
                if parent.anchor.has_system():
                    rotation.set_parent_body(parent.anchor.get_system())
                else:
                    rotation.set_parent_body(parent.anchor)
        else:
            if period is None:
                print("WARNING: Missing period")
                period = 1
            mean_motion = 2 * pi / (period * period_units)
            rotation = UniformRotation(orientation, mean_motion, meridian_angle * meridian_units, epoch, frame)
        return rotation


class FixedRotationYamlParser(YamlModuleParser):
    @classmethod
    def decode(cls, data, frame, parent):
        if data.angle is not None:
            angle = float(data.angle)
            axis = data.axis if data.axis is not None else LVector3d.up()
            orientation = quaternion_from_axis_angle(axis, angle, units.Deg)
        elif data.ra is not None:
            orientation = OrientationYamlParser.decode(data, False)
        else:
            orientation = LQuaterniond()
        if data.frame is not None or frame is None:
            frame = FrameYamlParser.decode(data.frame if data.frame else 'j2000equatorial', parent)
        rotation = FixedRotation(orientation, frame)
        return rotation


class RotationYamlParser(TypedYamlParser):
    """Parser for rotation types with validation."""

    @classmethod
    def decode(cls, data, frame=None, parent=None, default=None):
        if data is None:
            if default is not None:
                data = {'type': default}
            else:
                return UnknownRotation()
        object_type, parameters = cls.get_type_and_data(data)

        if object_type in cls.parsers:
            # Validate and decode using registered parser
            validated = cls.validate_and_decode(object_type, parameters)
            rotation = cls.parsers[object_type].decode(validated, frame, parent)
        else:
            rotation = rotation_elements_db.get(data)
            if rotation is None:
                # TODO: An error should be raised instead
                rotation = UnknownRotation()
            # TODO: this should not be done arbitrarily
            if isinstance(rotation.frame, BodyReferenceFrames) and rotation.frame.anchor is None:
                rotation.frame.set_anchor(parent.anchor)
            if isinstance(rotation, SynchronousRotation) and rotation.parent_body is None:
                if parent.anchor.has_system():
                    rotation.set_parent_body(parent.anchor.get_system())
                else:
                    rotation.set_parent_body(parent.anchor)
        return rotation


class NamedRotationYamlParser(YamlModuleParser):
    @classmethod
    def decode(cls, data, parent=None):
        name = data.get('name')
        category = data.get('category')
        if name is None or category is None:
            return None
        rotation = RotationYamlParser.decode(data)
        rotation_elements_db.register_element(category, name, rotation)
        return None


def register_rotation_parsers():
    """Register rotation type parsers with their models."""
    # Register rotation types with RotationYamlParser
    RotationYamlParser.register_parser('uniform', UniformYamlParser, UniformRotationConfig)
    RotationYamlParser.register_parser('fixed', FixedRotationYamlParser, FixedRotationConfig)

    # Register top-level object parser
    ObjectYamlParser.register_object_parser('rotation', NamedRotationYamlParser())
    ObjectYamlParser.register_object_parser('uniform', NamedRotationYamlParser())
    ObjectYamlParser.register_object_parser('fixed', NamedRotationYamlParser())
