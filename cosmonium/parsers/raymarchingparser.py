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


from ..procedural.raymarching import SDFRayMarchingAppearance, BulgeRayMarchingAppearance
from ..procedural.raymarching import VolumetricDensityRayMarchingAppearance
from ..procedural.raymarching import VolumetricDensityEmissiveRayMarchingAppearance
from ..procedural.raymarching import SDFPointShape, SDFSphereShape

from .appearancesparser import AppearanceYamlParser
from .noiseparser import NoiseYamlParser
from .yamlparser import YamlModuleParser


def create_point_sdf(parser, data, length_scale):
    name = data.get('name', None)
    position = data.get('position', [0, 0, 0])
    return SDFPointShape(position, dynamic=name is not None, name=name)


def create_sphere_sdf(parser, data, length_scale):
    name = data.get('name', None)
    position = data.get('position', [0, 0, 0])
    radius = data.get('radius', 1.0)
    radius_range = data.get('radius-range', [0.0, 1.0])
    ranges = {'radius': radius_range}
    return SDFSphereShape(position, radius, dynamic=name is not None, name=name, ranges=ranges)


NoiseYamlParser.register_noise_parser('point', create_point_sdf)
NoiseYamlParser.register_noise_parser('sphere', create_sphere_sdf)


class VolumetricDensityRayMarchingYamlParser(YamlModuleParser):
    @classmethod
    def decode(cls, data, heightmap, radius, patched_shape):
        noise_parser = NoiseYamlParser()
        density = noise_parser.decode(data.get('density'))
        absorption_factor = data.get('absorption-factor', 0.00001)
        absorption_coef = data.get('absorption-coef', [1, 1, 1])
        mie_coef = data.get('mie-coef', 0.1)
        phase_coef = data.get('phase-coef', 0)
        source_color = data.get('source-color', [1, 1, 1])
        source_power = data.get('source-power', 10000.0)
        emission_power = data.get('emission-power', 0.0)
        emission_color = data.get('emission-color', [1, 1, 1])
        max_steps = data.get('max-steps', 16)
        hdr = data.get('hdr', False)
        exposure = data.get('exposure', 4.0)
        appearance = VolumetricDensityRayMarchingAppearance(
            density,
            absorption_factor,
            absorption_coef,
            mie_coef,
            phase_coef,
            source_color,
            source_power,
            emission_color,
            emission_power,
            max_steps,
            hdr,
            exposure,
        )
        return appearance


class VolumetricDensityEmissiveRayMarchingYamlParser(YamlModuleParser):
    @classmethod
    def decode(cls, data, heightmap, radius, patched_shape):
        noise_parser = NoiseYamlParser()
        density = noise_parser.decode(data.get('density'))
        emission_power = data.get('emission-power', 0.0)
        emission_color = data.get('emission-color', [1, 1, 1])
        max_steps = data.get('max-steps', 16)
        hdr = data.get('hdr', False)
        exposure = data.get('exposure', 4.0)
        appearance = VolumetricDensityEmissiveRayMarchingAppearance(
            density, emission_color, emission_power, max_steps, hdr, exposure
        )
        return appearance


class BulgeRayMarchingYamlParser(YamlModuleParser):
    @classmethod
    def decode(cls, data, heightmap, radius, patched_shape):
        density_coef = data.get('density-coef', 10000.0)
        density_power = data.get('density-power', 2)
        max_steps = data.get('max-steps', 16)
        hdr = data.get('hdr', False)
        exposure = data.get('exposure', 4.0)
        appearance = BulgeRayMarchingAppearance(
            effective_intensity, effective_radius, emissive_color, emissive_scale, max_steps, hdr, exposure
        )
        return appearance


class SDFRayMarchingYamlParser(YamlModuleParser):
    @classmethod
    def decode(cls, data, heightmap, radius, patched_shape):
        sdf_parser = NoiseYamlParser()
        shape = sdf_parser.decode(data.get('shape', 'sphere'))
        max_steps = data.get('max-steps', 16)
        hdr = data.get('hdr', False)
        exposure = data.get('exposure', 4.0)
        appearance = SDFRayMarchingAppearance(shape, max_steps, hdr, exposure)
        return appearance


AppearanceYamlParser.register('raymarching:density', VolumetricDensityRayMarchingYamlParser)
AppearanceYamlParser.register('raymarching:emissive', VolumetricDensityEmissiveRayMarchingYamlParser)
AppearanceYamlParser.register('raymarching:bulge', BulgeRayMarchingYamlParser)
AppearanceYamlParser.register('raymarching:sdf', SDFRayMarchingYamlParser)
