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


from ..astro.frame import (
    BodyReferenceFrames,
    CelestialReferenceFrame,
    EquatorialReferenceFrame,
    J2000BarycentricEclipticReferenceFrame,
    J2000BarycentricEquatorialReferenceFrame,
    J2000EclipticReferenceFrame,
    J2000EquatorialReferenceFrame,
    SynchroneReferenceFrame,
)
from ..astro.framesdb import frames_db
from .objectparser import ObjectYamlParser
from .schemas.frame import (
    EquatorialFrameConfig,
    FixedFrameConfig,
    J2000BarycentricEclipticFrameConfig,
    J2000BarycentricEquatorialFrameConfig,
    J2000EclipticFrameConfig,
    J2000EquatorialFrameConfig,
    MeanEquatorialFrameConfig,
)
from .yamlparser import TypedYamlParser, YamlModuleParser


class J2000BarycentricEclipticFrameYamlParser(YamlModuleParser):
    @classmethod
    def decode(cls, data, parent=None):
        return J2000BarycentricEclipticReferenceFrame()


class J2000BarycentricEquatorialFrameYamlParser(YamlModuleParser):
    @classmethod
    def decode(cls, data, parent=None):
        return J2000BarycentricEquatorialReferenceFrame()


class J2000EclipticFrameYamlParser(YamlModuleParser):
    @classmethod
    def decode(cls, data, parent=None):
        body = data.center if data.center is not None else parent
        anchor = FrameYamlParser.find_center_anchor(body)
        return J2000EclipticReferenceFrame(anchor)


class J2000EquatorialFrameYamlParser(YamlModuleParser):
    @classmethod
    def decode(cls, data, parent=None):
        body = data.center if data.center is not None else parent
        anchor = FrameYamlParser.find_center_anchor(body)
        return J2000EquatorialReferenceFrame(anchor)


class EquatorialFrameYamlParser(YamlModuleParser):
    @classmethod
    def decode(cls, data, parent=None):
        body = data.center if data.center is not None else parent
        ra = data.ra
        de = data.de
        node = data.longitude
        anchor = FrameYamlParser.find_center_anchor(body)
        return CelestialReferenceFrame(anchor, right_ascension=ra, declination=de, longitude_at_node=node)


class MeanEquatorialFrameYamlParser(YamlModuleParser):
    @classmethod
    def decode(cls, data, parent=None):
        body = data.center if data.center is not None else parent
        anchor = FrameYamlParser.find_center_anchor(body)
        return EquatorialReferenceFrame(anchor)


class FixedFrameYamlParser(YamlModuleParser):
    @classmethod
    def decode(cls, data, parent=None):
        body = data.center if data.center is not None else parent
        anchor = FrameYamlParser.find_center_anchor(body)
        return SynchroneReferenceFrame(anchor)


class FrameYamlParser(TypedYamlParser):
    """Parser for frame types with validation."""

    @classmethod
    def find_center_anchor(cls, body):
        if body is not None and body.is_system() and body.primary is not None and not body.star_system:
            body = body.primary
        anchor = body.anchor if body is not None else None
        return anchor

    @classmethod
    def decode(cls, data, parent=None, default='j2000ecliptic'):
        if data is None:
            data = {'type': default}
        object_type, parameters = cls.get_type_and_data(data)
        object_type = object_type.lower()

        if object_type in cls.parsers:
            # Validate and decode using registered parser
            validated_parameters = cls.validate_and_decode(object_type, parameters)
            return cls.parsers[object_type].decode(validated_parameters, parent)
        else:
            # TODO: Reference name should be properly handled
            frame = frames_db.get(object_type)
            # TODO: this should not be done arbitrarily
            if parent is not None and isinstance(frame, BodyReferenceFrames):
                frame.set_anchor(parent.anchor)
            return frame


def register_frame_parsers():
    """Register frame type parsers with their models."""
    # Register frame types with FrameYamlParser
    FrameYamlParser.register_parser('j2000ecliptic', J2000EclipticFrameYamlParser, J2000EclipticFrameConfig)
    FrameYamlParser.register_parser('j2000equatorial', J2000EquatorialFrameYamlParser, J2000EquatorialFrameConfig)
    FrameYamlParser.register_parser(
        'j2000barycentricecliptic', J2000BarycentricEclipticFrameYamlParser, J2000BarycentricEclipticFrameConfig
    )
    FrameYamlParser.register_parser(
        'j2000barycentricequatorial', J2000BarycentricEquatorialFrameYamlParser, J2000BarycentricEquatorialFrameConfig
    )
    FrameYamlParser.register_parser('equatorial', EquatorialFrameYamlParser, EquatorialFrameConfig)
    FrameYamlParser.register_parser('mean-equatorial', MeanEquatorialFrameYamlParser, MeanEquatorialFrameConfig)
    FrameYamlParser.register_parser('fixed', FixedFrameYamlParser, FixedFrameConfig)

    # Register top-level object parser
    ObjectYamlParser.register_object_parser('frame', NamedFrameYamlParser())
    ObjectYamlParser.register_object_parser('equatorial', NamedFrameYamlParser())


class NamedFrameYamlParser(YamlModuleParser):
    @classmethod
    def decode(cls, data, parent=None):
        name = data.get('name')
        if name is None:
            return None
        frame = FrameYamlParser.decode(data, None)
        frames_db.register_frame(name, frame)
        return None
