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

from ..objects.galaxies import (
    EllipticalGalaxyShape,
    FullRingGalaxyShape,
    FullSpiralGalaxyShape,
    Galaxy,
    GalaxyAppearance,
    IrregularGalaxyShape,
    LenticularGalaxyShape,
    SpiralGalaxyShape,
)
from ..sprites import ExpPointSprite, GaussianPointSprite, RoundDiskPointSprite
from .objectparser import ObjectYamlParser
from .orbitsparser import OrbitYamlParser
from .rotationsparser import RotationYamlParser
from .schemas.stellarobjects import GalaxyConfig
from .utilsparser import DistanceUnitsYamlParser, check_parent
from .yamlparser import YamlModuleParser


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
                return LenticularGalaxyShape(
                    nb_points_bulge,
                    nb_points_arms,
                    spread,
                    zspread,
                    point_size,
                    winding,
                    sersic_bulge,
                    sersic_disk,
                )
            elif shape == 'elliptical':
                factor = data.get('factor', 0)
                factor = 1.0 - factor / 10.0
                nb_points = data.get("nb-points", 1000)
                sersic = data.get("sersic", 4.0)
                spread = data.get("spread", 0.4)
                zspread = data.get("zspread", 0.2)
                point_size = data.get("size", 200)
                return EllipticalGalaxyShape(factor, nb_points, spread, zspread, point_size, sersic)
            elif shape == 'irregular':
                nb_points = data.get("nb-points", 1000)
                sersic = data.get("sersic", 4.0)
                spread = data.get("spread", 0.2)
                zspread = data.get("zspread", 0.1)
                point_size = data.get("size", 200)
                return IrregularGalaxyShape(nb_points, spread, zspread, point_size, sersic)
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
                    return SpiralGalaxyShape(
                        pitch,
                        nb_points_bulge,
                        nb_points_arms,
                        spread,
                        zspread,
                        sprite_size,
                        winding,
                        sersic_bulge,
                        sersic_disk,
                    )
                else:
                    N = data.get("N", 1.0)
                    B = data.get("B", 1.0)
                    ring = data.get("ring", False)
                    if ring:
                        return FullRingGalaxyShape(
                            N,
                            B,
                            nb_points_bulge,
                            nb_points_arms,
                            spread,
                            zspread,
                            sprite_size,
                            winding,
                            sersic_bulge,
                            sersic_disk,
                        )
                    else:
                        return FullSpiralGalaxyShape(
                            N,
                            B,
                            nb_points_bulge,
                            nb_points_arms,
                            spread,
                            zspread,
                            sprite_size,
                            winding,
                            sersic_bulge,
                            sersic_disk,
                        )
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
    def decode(self, data, parent=None):
        name = data.name
        translated_names, source_names = self.translate_names(name)
        parent_name = data.parent
        parent, explicit_parent = check_parent(name, parent, parent_name)
        if parent is None:
            return None
        body_class = data.body_class or 'galaxy'
        radius = data.radius
        radius_units = DistanceUnitsYamlParser.decode(data.radius_units)
        abs_magnitude = data.magnitude
        shape_type = data.classification
        orbit = OrbitYamlParser.decode(data.orbit, None, parent)
        rotation = RotationYamlParser.decode(data.rotation, None, parent)
        appearance = GalaxyAppearanceYamlParser.decode(data.appearance)
        shape = GalaxyShapeYamlParser.decode(data.shape, shape_type)
        galaxy = Galaxy(
            translated_names,
            source_names=source_names,
            body_class=body_class,
            shape_type=shape_type,
            shape=shape,
            appearance=appearance,
            abs_magnitude=abs_magnitude,
            radius=radius,
            radius_units=radius_units,
            orbit=orbit,
            rotation=rotation,
        )
        ObjectYamlParser.decode_objects_list(data.children, parent=galaxy)
        parent.add_child_fast(galaxy)
        return galaxy


def register_galaxy_parsers():
    ObjectYamlParser.register_object_parser('galaxy', GalaxyYamlParser(), model=GalaxyConfig)
