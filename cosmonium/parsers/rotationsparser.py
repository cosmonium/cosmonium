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

from panda3d.core import LQuaterniond, LVector3d

from ..astro.elementsdb import rotation_elements_db
from ..astro.rotations import EquatorialReferenceAxis, FixedRotation, UnknownRotation, create_uniform_rotation
from ..astro.frame import BodyReferenceFrame
from ..astro import units
from .. import utils

from .yamlparser import YamlModuleParser
from .objectparser import ObjectYamlParser
from .utilsparser import TimeUnitsYamlParser, AngleUnitsYamlParser
from .framesparser import FrameYamlParser

class UniformYamlParser(YamlModuleParser):
    @classmethod
    def decode(self, data, frame, parent):
        synchronous = data.get('synchronous', False)
        period = data.get('period', None)
        period_units = TimeUnitsYamlParser.decode(data.get('period-units', 'Year'))
        inclination = data.get('inclination', 0.0)
        inclination_units = AngleUnitsYamlParser.decode(data.get('inclination-units', 'Deg'))
        ascending_node = data.get('ascending-node', 0.0)
        ascending_node_units = AngleUnitsYamlParser.decode(data.get('ascending-node-units', 'Deg'))
        right_ascension = data.get('ra', None)
        ra_units = AngleUnitsYamlParser.decode(data.get('ra-units', 'Deg'))
        declination = data.get('de', 0.0)
        decl_units = AngleUnitsYamlParser.decode(data.get('de-units', 'Deg'))
        meridian_angle = data.get('meridian', 0.0)
        meridian_units = AngleUnitsYamlParser.decode(data.get('meridian-units', 'Deg'))
        epoch = data.get('epoch', units.J2000)
        if data.get('frame') is not None or frame is None:
            frame = FrameYamlParser.decode(data.get('frame', 'J2000Ecliptic'), parent)
        return create_uniform_rotation(period,
                                period_units,
                                synchronous,
                                inclination,
                                inclination_units,
                                ascending_node,
                                ascending_node_units,
                                right_ascension,
                                ra_units,
                                declination,
                                decl_units,
                                meridian_angle,
                                meridian_units,
                                epoch,
                                frame)

class FixedRotationYamlParser(YamlModuleParser):
    @classmethod
    def decode(self, data, frame, parent):
        if 'angle' in data:
            angle = float(data['angle'])
            axis = data.get("axis", LVector3d.up())
            rot = utils.LQuaternionromAxisAngle(axis, angle, units.Deg)
        elif 'ra' in data:
            right_ascension = data.get('ra', None)
            ra_units = AngleUnitsYamlParser.decode(data.get('ra-units', 'Deg'))
            declination = data.get('de', 0.0)
            decl_units = AngleUnitsYamlParser.decode(data.get('de-units', 'Deg'))
            rot = EquatorialReferenceAxis(right_ascension * ra_units, declination * decl_units, False)
        else:
            rot = LQuaterniond()
        if data.get('frame') is not None or frame is None:
            frame = FrameYamlParser.decode(data.get('frame', 'J2000Equatorial'), parent)
        rotation = FixedRotation(rot, frame)
        return rotation

class RotationYamlParser(YamlModuleParser):
    @classmethod
    def decode(cls, data, frame=None, parent=None):
        if data is None: return UnknownRotation()
        (object_type, parameters) = cls.get_type_and_data(data)
        if object_type == 'uniform':
            rotation = UniformYamlParser.decode(parameters, frame, parent)
        elif object_type == 'fixed':
            rotation = FixedRotationYamlParser.decode(parameters, frame, parent)
        else:
            rotation = rotation_elements_db.get(data)
            if rotation is None:
                rotation = UnknownRotation()
            #TODO: this should not be done arbitrarily
            if isinstance(rotation.frame, BodyReferenceFrame) and rotation.frame.anchor is None:
                rotation.frame.set_anchor(parent.anchor)
        return rotation

class NamedRotationYamlParser(YamlModuleParser):
    @classmethod
    def decode(self, data, parent=None):
        name = data.get('name')
        category = data.get('category')
        if name is None or category is None: return None
        rotation = RotationYamlParser.decode(data)
        rotation_elements_db.register_element(category, name, rotation)
        return None

ObjectYamlParser.register_object_parser('rotation', NamedRotationYamlParser())
