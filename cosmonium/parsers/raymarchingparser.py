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


from ..procedural.raymarching import (
    BulgeRayMarchingAppearance,
    SDFPointShape,
    SDFRayMarchingAppearance,
    SDFSphereShape,
    VolumetricDensityEmissiveRayMarchingAppearance,
    VolumetricDensityRayMarchingAppearance,
)
from .appearancesparser import AppearanceYamlParser
from .noiseparser import NoiseYamlParser
from .schemas.raymarching import (
    BulgeRayMarchingConfig,
    SDFPointShapeConfig,
    SDFRayMarchingConfig,
    SDFSphereShapeConfig,
    VolumetricDensityEmissiveRayMarchingConfig,
    VolumetricDensityRayMarchingConfig,
)
from .yamlparser import YamlModuleParser


def create_point_sdf(parser, data, length_scale):
    config = SDFPointShapeConfig.model_validate(data)
    return SDFPointShape(config.position, dynamic=config.name is not None, name=config.name)


def create_sphere_sdf(parser, data, length_scale):
    config = SDFSphereShapeConfig.model_validate(data)
    ranges = {'radius': config.radius_range}
    return SDFSphereShape(
        config.position, config.radius, dynamic=config.name is not None, name=config.name, ranges=ranges
    )


NoiseYamlParser.register_noise_parser('point', create_point_sdf)
NoiseYamlParser.register_noise_parser('sphere', create_sphere_sdf)


class VolumetricDensityRayMarchingYamlParser(YamlModuleParser):
    @classmethod
    def decode(cls, data, heightmap, radius, patched_shape):
        config = VolumetricDensityRayMarchingConfig.model_validate(data)
        noise_parser = NoiseYamlParser()
        density = noise_parser.decode(config.density)
        appearance = VolumetricDensityRayMarchingAppearance(
            density,
            config.absorption_factor,
            config.absorption_coef,
            config.mie_coef,
            config.phase_coef,
            config.source_color,
            config.source_power,
            config.emission_color,
            config.emission_power,
            config.max_steps,
            config.hdr,
            config.exposure,
        )
        return appearance


class VolumetricDensityEmissiveRayMarchingYamlParser(YamlModuleParser):
    @classmethod
    def decode(cls, data, heightmap, radius, patched_shape):
        config = VolumetricDensityEmissiveRayMarchingConfig.model_validate(data)
        noise_parser = NoiseYamlParser()
        density = noise_parser.decode(config.density)
        appearance = VolumetricDensityEmissiveRayMarchingAppearance(
            density, config.emission_color, config.emission_power, config.max_steps, config.hdr, config.exposure
        )
        return appearance


class BulgeRayMarchingYamlParser(YamlModuleParser):
    @classmethod
    def decode(cls, data, heightmap, radius, patched_shape):
        config = BulgeRayMarchingConfig.model_validate(data)
        appearance = BulgeRayMarchingAppearance(
            config.effective_intensity,
            config.effective_radius,
            config.emissive_color,
            config.emissive_scale,
            config.max_steps,
            config.hdr,
            config.exposure,
        )
        return appearance


class SDFRayMarchingYamlParser(YamlModuleParser):
    @classmethod
    def decode(cls, data, heightmap, radius, patched_shape):
        config = SDFRayMarchingConfig.model_validate(data)
        sdf_parser = NoiseYamlParser()
        shape = sdf_parser.decode(config.shape)
        appearance = SDFRayMarchingAppearance(shape, config.max_steps, config.hdr, config.exposure)
        return appearance


def register_raymarching_parsers():
    AppearanceYamlParser.register('raymarching:density', VolumetricDensityRayMarchingYamlParser)
    AppearanceYamlParser.register('raymarching:emissive', VolumetricDensityEmissiveRayMarchingYamlParser)
    AppearanceYamlParser.register('raymarching:bulge', BulgeRayMarchingYamlParser)
    AppearanceYamlParser.register('raymarching:sdf', SDFRayMarchingYamlParser)
