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


from panda3d.core import LQuaterniond, LVector3d

from ..astro.elementsdb import rotation_elements_db
from ..astro.rotations import FixedRotation, UnknownRotation, UniformRotation, SynchronousRotation
from ..astro.frame import BodyReferenceFrame
from ..astro.astro import calc_orientation, calc_orientation_from_incl_an
from ..astro import units
from .. import utils

from .yamlparser import YamlModuleParser
from .objectparser import ObjectYamlParser
from .utilsparser import TimeUnitsYamlParser, AngleUnitsYamlParser
from .framesparser import FrameYamlParser

from math import pi

class OrientationYamlParser(YamlModuleParser):
    @classmethod
    def decode(cls, data, flipped):
        inclination = data.get('inclination', 0.0)
        inclination_units = AngleUnitsYamlParser.decode(data.get('inclination-units', 'Deg'))
        ascending_node = data.get('ascending-node', 0.0)
        ascending_node_units = AngleUnitsYamlParser.decode(data.get('ascending-node-units', 'Deg'))
        right_ascension = data.get('ra', None)
        right_ascension_units = AngleUnitsYamlParser.decode(data.get('ra-units', 'Deg'))
        declination = data.get('de', 0.0)
        declination_units = AngleUnitsYamlParser.decode(data.get('de-units', 'Deg'))
        if right_ascension is not None:
            orientation = calc_orientation(right_ascension * right_ascension_units,
                                           declination * declination_units,
                                           flipped)
        else:
            orientation = calc_orientation_from_incl_an(inclination * inclination_units,
                                                        ascending_node * ascending_node_units,
                                                        flipped)
        return orientation

class UniformYamlParser(YamlModuleParser):
    @classmethod
    def decode(self, data, frame, parent):
        synchronous = data.get('synchronous', False)
        period = data.get('period', None)
        period_units = TimeUnitsYamlParser.decode(data.get('period-units', 'Year'))
        meridian_angle = data.get('meridian', 0.0)
        meridian_units = AngleUnitsYamlParser.decode(data.get('meridian-units', 'Deg'))
        epoch = data.get('epoch', units.J2000)
        if data.get('frame') is not None or frame is None:
            if data.get('ra') is not None:
                default_frame = 'J2000Equatorial'
            else:
                default_frame = 'J2000Ecliptic'
            frame = FrameYamlParser.decode(data.get('frame', default_frame), parent)
        flipped = period is not None and period < 0
        orientation = OrientationYamlParser.decode(data, flipped)
        if synchronous:
            rotation = SynchronousRotation(orientation, meridian_angle * meridian_units, epoch, frame)
            if parent is not None:
                if parent.system is not None:
                    rotation.set_parent_body(parent.system.anchor)
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
    def decode(self, data, frame, parent):
        if 'angle' in data:
            angle = float(data['angle'])
            axis = data.get("axis", LVector3d.up())
            orientation = utils.LQuaternionromAxisAngle(axis, angle, units.Deg)
        elif 'ra' in data:
            orientation = OrientationYamlParser.decode(data, False)
        else:
            orientation = LQuaterniond()
        if data.get('frame') is not None or frame is None:
            frame = FrameYamlParser.decode(data.get('frame', 'J2000Equatorial'), parent)
        rotation = FixedRotation(orientation, frame)
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
                #TODO: An error should be raised instead
                rotation = UnknownRotation()
            #TODO: this should not be done arbitrarily
            if isinstance(rotation.frame, BodyReferenceFrame) and rotation.frame.anchor is None:
                rotation.frame.set_anchor(parent.anchor)
            if isinstance(rotation, SynchronousRotation) and rotation.parent_body is None:
                if parent.system is not None:
                    rotation.set_parent_body(parent.system.anchor)
                else:
                    rotation.set_parent_body(parent.anchor)
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
