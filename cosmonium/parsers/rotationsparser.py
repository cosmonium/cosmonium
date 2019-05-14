from __future__ import print_function
from __future__ import absolute_import

from panda3d.core import LQuaterniond, LVector3d

from ..astro.elementsdb import rotation_elements_db
from ..astro.rotations import FixedRotation, UniformRotation
from ..astro import units
from .. import utils

from .yamlparser import YamlModuleParser
from .objectparser import ObjectYamlParser
from .utilsparser import TimeUnitsYamlParser, AngleUnitsYamlParser
from .utilsparser import FrameYamlParser

class UniformYamlParser(YamlModuleParser):
    @classmethod
    def decode(self, data):
        synchronous = data.get('synchronous', False)
        period = data.get('period', None)
        period_units = TimeUnitsYamlParser.decode(data.get('period-units', 'Year'))
        radial_speed = data.get('radial-speed', None)
        inclination = data.get('inclination', 0.0)
        ascending_node = data.get('ascending-node', 0.0)
        right_ascension = data.get('ra', None)
        ra_units = AngleUnitsYamlParser.decode(data.get('ra-units', 'Deg'))
        declination = data.get('de', 0.0)
        decl_units = AngleUnitsYamlParser.decode(data.get('de-units', 'Deg'))
        meridian_angle = data.get('meridian', 0.0)
        epoch = data.get('epoch', units.J2000)
        frame = FrameYamlParser.decode(data.get('frame', 'J2000Ecliptic'))
        return UniformRotation(radial_speed,
                                period,
                                period_units,
                                synchronous,
                                inclination,
                                ascending_node,
                                right_ascension,
                                ra_units,
                                declination,
                                decl_units,
                                meridian_angle,
                                epoch,
                                frame)

class FixedRotationYamlParser(YamlModuleParser):
    @classmethod
    def decode(self, data):
        if 'angle' in data:
            angle = float(data['angle'])
            axis = data.get("axis", LVector3d.up())
            rot = utils.LQuaternionromAxisAngle(axis, angle, units.Deg)
        else:
            rot = LQuaterniond()
        rotation = FixedRotation(rot)
        return rotation

class RotationYamlParser(YamlModuleParser):
    @classmethod
    def decode(cls, data):
        if data is None: return FixedRotation()
        (object_type, parameters) = cls.get_type_and_data(data)
        if object_type == 'uniform':
            rotation = UniformYamlParser.decode(parameters)
        elif object_type == 'fixed':
            rotation = FixedRotationYamlParser.decode(parameters)
        else:
            rotation = rotation_elements_db.get(data)
        return rotation

class NamedRotationYamlParser(YamlModuleParser):
    @classmethod
    def decode(self, data):
        name = data.get('name')
        category = data.get('category')
        if name is None or category is None: return None
        rotation = RotationYamlParser.decode(data)
        rotation_elements_db.register_element(category, name, rotation)
        return None

ObjectYamlParser.register_object_parser('rotation', NamedRotationYamlParser())
