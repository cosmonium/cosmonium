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
from .schemas.galaxies import (
    EllipticalGalaxyShapeConfig,
    GalaxyAppearanceConfig,
    GalaxyConfig,
    IrregularGalaxyShapeConfig,
    LenticularGalaxyShapeConfig,
    SpiralGalaxyShapeConfig,
)
from .utilsparser import check_parent
from .yamlparser import YamlModuleParser


class GalaxyAppearanceYamlParser(YamlModuleParser):
    @classmethod
    def decode_appearance(cls, data):
        config = GalaxyAppearanceConfig.model_validate(data)
        sprite = config.sprite
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
        return GalaxyAppearance(sprite, config.color_scale)

    @classmethod
    def decode(cls, data):
        if data is None:
            return GalaxyAppearance()
        else:
            return cls.decode_appearance(data)


class GalaxyShapeYamlParser(YamlModuleParser):
    @classmethod
    def decode_shape(cls, data):
        shape_type_name = data.get('shape') if isinstance(data, dict) else data.shape
        if shape_type_name == 'lenticular':
            config = LenticularGalaxyShapeConfig.model_validate(data)
            winding = config.winding * pi / 180
            return LenticularGalaxyShape(
                config.nb_points_bulge,
                config.nb_points_arms,
                config.spread,
                config.zspread,
                config.size,
                winding,
                config.sersic_bulge,
                config.sersic,
            )
        elif shape_type_name == 'elliptical':
            config = EllipticalGalaxyShapeConfig.model_validate(data)
            factor = 1.0 - config.factor / 10.0
            return EllipticalGalaxyShape(
                factor, config.nb_points, config.spread, config.zspread, config.size, config.sersic
            )
        elif shape_type_name == 'irregular':
            config = IrregularGalaxyShapeConfig.model_validate(data)
            return IrregularGalaxyShape(config.nb_points, config.spread, config.zspread, config.size, config.sersic)
        elif shape_type_name == 'spiral':
            config = SpiralGalaxyShapeConfig.model_validate(data)
            winding = config.winding * pi / 180
            spread = config.spread
            if spread is None:
                spread = config.pitch / 5.0 if config.pitch is not None else 0.1
            if config.pitch is not None:
                return SpiralGalaxyShape(
                    config.pitch,
                    config.nb_points_bulge,
                    config.nb_points_arms,
                    spread,
                    config.zspread,
                    config.size,
                    winding,
                    config.sersic_bulge,
                    config.sersic,
                )
            else:
                if config.ring:
                    return FullRingGalaxyShape(
                        config.N,
                        config.B,
                        config.nb_points_bulge,
                        config.nb_points_arms,
                        spread,
                        config.zspread,
                        config.size,
                        winding,
                        config.sersic_bulge,
                        config.sersic,
                    )
                else:
                    return FullSpiralGalaxyShape(
                        config.N,
                        config.B,
                        config.nb_points_bulge,
                        config.nb_points_arms,
                        spread,
                        config.zspread,
                        config.size,
                        winding,
                        config.sersic_bulge,
                        config.sersic,
                    )
        else:
            print("Unknown shape '%s'", shape_type_name)
            return None

    @classmethod
    def vancouleur_to_pitch(cls, stage):
        return (2.69 * stage + 16.22) / 180 * pi

    @classmethod
    def decode_shape_type(cls, data, shape_type):
        # Normalize data to a dict (or empty dict) once at the start
        if data is None or not isinstance(data, dict):
            data = {}
        else:
            data = dict(data)
        if shape_type.startswith('S0'):
            data['shape'] = 'lenticular'
            return cls.decode_shape(data)
        elif shape_type.startswith('E'):
            data['shape'] = 'elliptical'
            return cls.decode_shape(data)
        elif shape_type.startswith('Irr'):
            data['shape'] = 'irregular'
            return cls.decode_shape(data)
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
            return cls.decode_shape(data)
        return None

    @classmethod
    def decode(cls, data, shape_type):
        if data is None or (isinstance(data, dict) and data.get('shape') is None):
            return cls.decode_shape_type(data, shape_type)
        else:
            return cls.decode_shape(data)


class GalaxyYamlParser(YamlModuleParser):
    def decode(self, data, parent=None):
        name = data.name
        parent_name = data.parent
        parent, explicit_parent = check_parent(name, parent, parent_name)
        if parent is None:
            return None
        body_class = data.body_class or 'galaxy'
        radius = data.radius.scaled_value if data.radius is not None else None
        shape_type = data.classification
        orbit = OrbitYamlParser.decode(data.orbit, None, parent)
        rotation = RotationYamlParser.decode(data.rotation, None, parent)
        appearance = GalaxyAppearanceYamlParser.decode(data.appearance)
        shape = GalaxyShapeYamlParser.decode(data.shape, shape_type)
        galaxy = Galaxy(
            name,
            body_class=body_class,
            shape_type=shape_type,
            shape=shape,
            appearance=appearance,
            abs_magnitude=data.magnitude,
            radius=radius,
            orbit=orbit,
            rotation=rotation,
        )
        self.translate_object_names(galaxy.anchor)
        ObjectYamlParser.decode_objects_list(data.children, parent=galaxy)
        parent.add_child_fast(galaxy)
        return galaxy


def register_galaxy_parsers():
    ObjectYamlParser.register_object_parser('galaxy', GalaxyYamlParser(), model=GalaxyConfig)
