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

from ..galaxies import LenticularGalaxyShape, EllipticalGalaxyShape, IrregularGalaxyShape, SpiralGalaxyShape, FullSpiralGalaxyShape, FullRingGalaxyShape
from ..sprites import GaussianPointSprite, ExpPointSprite, RoundDiskPointSprite
from ..galaxies import Galaxy, GalaxyAppearance

from .utilsparser import DistanceUnitsYamlParser
from .orbitsparser import OrbitYamlParser
from .rotationsparser import RotationYamlParser
from .objectparser import ObjectYamlParser
from .yamlparser import YamlModuleParser

from math import pi

class GalaxyAppearanceYamlParser(YamlModuleParser):
    @classmethod
    def decode_appearance(cls, data):
        sprite = data.get('sprite', 'exp')
        if sprite is not None:
            if sprite == 'gaussian':
                sprite = GaussianPointSprite()
            elif sprite == 'exp':
                sprite = ExpPointSprite()
            elif sprite == 'round':
                sprite = RoundDiskPointSprite()
            else:
                print("Unknown sprite '%s'", sprite)
                sprite = None
        color_scale = data.get('scale', 5.0)
        return GalaxyAppearance(sprite, color_scale)

    @classmethod
    def decode(cls, data):
        if data is None:
            return GalaxyAppearance()
        else:
            return cls.decode_appearance(data)

class GalaxyShapeYamlParser(YamlModuleParser):
    @classmethod
    def decode_shape(cls, data):
        shape = data.get('shape')
        radius = 1.0
        if shape is not None:
            if shape == 'lenticular':
                nb_points_bulge = data.get("nb-points-bulge", 200)
                nb_points_arms = data.get("nb-points-arms", 1000)
                sersic_bulge = data.get("sersic-bulge", 4.0)
                sersic_disk = data.get("sersic", 1.0)
                winding = data.get("winding", 360) * pi / 180
                spread = data.get("spread", 0.4)
                zspread = data.get("zspread", 0.1)
                point_size = data.get("size", 200)
                return LenticularGalaxyShape(radius, None, nb_points_bulge, nb_points_arms, spread, zspread, point_size, winding, sersic_bulge, sersic_disk)
            elif shape == 'elliptical':
                factor = data.get('factor', 0)
                factor = 1.0 - factor / 10.0
                nb_points = data.get("nb-points", 1000)
                sersic = data.get("sersic", 4.0)
                spread = data.get("spread", 0.4)
                zspread = data.get("zspread", 0.2)
                point_size = data.get("size", 200)
                return EllipticalGalaxyShape(factor, radius, None, nb_points, spread, zspread, point_size, sersic)
            elif shape == 'irregular':
                nb_points = data.get("nb-points", 1000)
                sersic = data.get("sersic", 4.0)
                spread = data.get("spread", 0.2)
                zspread = data.get("zspread", 0.1)
                point_size = data.get("size", 200)
                return IrregularGalaxyShape(radius, None, nb_points, spread, zspread, point_size, sersic)
            elif shape == "spiral":
                pitch = data.get('pitch')
                if pitch is not None:
                    default_spread = pitch / 5.0
                else:
                    default_spread = 0.1
                nb_points_bulge = data.get("nb-points-bulge", 400)
                nb_points_arms = data.get("nb-points-arms", 1000)
                sersic_bulge = data.get("sersic-bulge", 4.0)
                sersic_disk = data.get("sersic", 1.0)
                winding = data.get("winding", 360) * pi / 180
                spread = data.get("spread", default_spread)
                zspread = data.get("zspread", 0.02)
                sprite_size = data.get("size", 200)
                if pitch is not None:
                    return SpiralGalaxyShape(pitch, radius, None, nb_points_bulge, nb_points_arms, spread, zspread, sprite_size, winding, sersic_bulge, sersic_disk)
                else:
                    N = data.get("N", 1.0)
                    B = data.get("B", 1.0)
                    ring = data.get("ring", False)
                    if ring:
                        return FullRingGalaxyShape(N, B, radius, None, nb_points_bulge, nb_points_arms, spread, zspread, sprite_size, winding, sersic_bulge, sersic_disk)
                    else:
                        return FullSpiralGalaxyShape(N, B, radius, None, nb_points_bulge, nb_points_arms, spread, zspread, sprite_size, winding, sersic_bulge, sersic_disk)
            else:
                print("Unknown shape '%s'", shape)
                shape = None
        return shape

    @classmethod
    def vancouleur_to_pitch(self, stage):
        return (2.69 * stage + 16.22) / 180 * pi

    @classmethod
    def decode_shape_type(cls, data, shape_type):
        if shape_type.startswith('S0'):
            data['shape'] = 'lenticular'
            return cls.decode(data, shape_type)
        elif shape_type.startswith('E'):
            data['shape'] = 'elliptical'
            return cls.decode(data, shape_type)
        elif shape_type.startswith('Irr'):
            data['shape'] = 'irregular'
            return cls.decode(data, shape_type)
        elif shape_type.startswith('S'):
            data['shape'] = 'spiral'
            if shape_type.endswith('bc'):
                stage = 4
            elif shape_type.endswith('ab'):
                stage = 2
            elif shape_type.endswith('a'):
                stage = 1
            elif shape_type.endswith('b'):
                stage = 3
            elif shape_type.endswith('c'):
                stage = 5
            else:
                stage = 0.5
            pitch = cls.vancouleur_to_pitch(stage)
            data['pitch'] = pitch
            return cls.decode(data, shape_type)

    @classmethod
    def decode(cls, data, shape_type):
        if data is None or data.get('shape') is None:
            return cls.decode_shape_type(data, shape_type)
        else:
            return cls.decode_shape(data)

class GalaxyYamlParser(YamlModuleParser):
    def decode(self, data):
        name = data.get('name')
        body_class = data.get('body-class', 'galaxy')
        radius = float(data.get('radius'))
        radius_units = DistanceUnitsYamlParser.decode(data.get('radius-units', 'Ly'))
        abs_magnitude = data.get('magnitude')
        shape_type = data.get('type')
        orbit = OrbitYamlParser.decode(data.get('orbit'))
        rotation = RotationYamlParser.decode(data.get('rotation'))
        appearance = GalaxyAppearanceYamlParser.decode(data)
        shape = GalaxyShapeYamlParser.decode(data, shape_type)
        galaxy = Galaxy(name,
                    body_class=body_class,
                    shape_type=shape_type,
                    shape=shape,
                    appearance=appearance,
                    abs_magnitude=abs_magnitude,
                    radius=radius,
                    radius_units=radius_units,
                    orbit=orbit,
                    rotation=rotation)
        return galaxy

ObjectYamlParser.register_object_parser('galaxy', GalaxyYamlParser())
