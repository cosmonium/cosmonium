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

from ..procedural.raymarching import SDFRayMarchingShader, BulgeRayMarchingShader, VolumetricDensityRayMarchingShader, VolumetricDensityEmissiveRayMarchingShader
from ..procedural.raymarching import SDFPointShape, SDFSphereShape
from .noiseparser import NoiseYamlParser
from .shadersparser import ShaderAppearanceYamlParser
from .yamlparser import YamlModuleParser

def create_point_sdf(parser, data, length_scale):
    name = data.get('name', None)
    position = data.get('position', [0, 0, 0])
    return SDFPointShape(position, dynamic=name is not None, name=name)

def create_sphere_sdf(parser, data, length_scale):
    name = data.get('name', None)
    position = data.get('position', [0, 0, 0])
    radius = data.get('radius', 1.0)
    return SDFSphereShape(position, radius, dynamic=name is not None, name=name)

NoiseYamlParser.register_noise_parser('point', create_point_sdf)
NoiseYamlParser.register_noise_parser('sphere', create_sphere_sdf)

class VolumetricDensityRayMarchingYamlParser(YamlModuleParser):
    @classmethod
    def decode(cls, data, appearance):
        noise_parser = NoiseYamlParser()
        density = noise_parser.decode(data.get('density'))
        absorption_factor = data.get('absorption-factor', 0.00001)
        absorption_coef = data.get('absorption-coef', [1, 1, 1])
        mie_coef = data.get('mie-coef', 0.1)
        phase_coef = data.get('phase-coef', 0)
        source_power = data.get('source-power', 10000.0)
        emission_power = data.get('emission-power', 0.0)
        emission_color = data.get('emission-color', [1, 1, 1])
        max_steps = data.get('max-steps', 16)
        hdr = data.get('hdr', False)
        exposure = data.get('exposure', 4.0)
        shader = VolumetricDensityRayMarchingShader(density)
        shader.absorption_factor = absorption_factor
        shader.absorption_coef = absorption_coef
        shader.mie_coef = mie_coef
        shader.phase_coef = phase_coef
        shader.source_power = source_power
        shader.emission_power = emission_power
        shader.emission_color = emission_color
        shader.max_steps = max_steps
        shader.hdr = hdr
        shader.exposure = exposure
        return shader

class VolumetricDensityEmissiveRayMarchingYamlParser(YamlModuleParser):
    @classmethod
    def decode(cls, data, appearance):
        noise_parser = NoiseYamlParser()
        density = noise_parser.decode(data.get('density'))
        emission_power = data.get('emission-power', 0.0)
        emission_color = data.get('emission-color', [1, 1, 1])
        max_steps = data.get('max-steps', 16)
        hdr = data.get('hdr', False)
        exposure = data.get('exposure', 4.0)
        shader = VolumetricDensityEmissiveRayMarchingShader(density)
        shader.emission_power = emission_power
        shader.emission_color = emission_color
        shader.max_steps = max_steps
        shader.hdr = hdr
        shader.exposure = exposure
        return shader

class BulgeRayMarchingYamlParser(YamlModuleParser):
    @classmethod
    def decode(cls, data, appearance):
        density_coef = data.get('density-coef', 10000.0)
        density_power = data.get('density-power', 2)
        hdr = data.get('hdr', False)
        exposure = data.get('exposure', 4.0)
        shader = BulgeRayMarchingShader()
        shader.density_coef = density_coef
        shader.density_power = density_power
        shader.hdr = hdr
        shader.exposure = exposure
        return shader

class SDFRayMarchingYamlParser(YamlModuleParser):
    @classmethod
    def decode(cls, data, appearance):
        sdf_parser = NoiseYamlParser()
        shape = sdf_parser.decode(data.get('shape', 'sphere'))
        hdr = data.get('hdr', False)
        exposure = data.get('exposure', 4.0)
        shader = SDFRayMarchingShader(shape)
        shader.hdr = hdr
        shader.exposure = exposure
        return shader

ShaderAppearanceYamlParser.register('raymarching:density', VolumetricDensityRayMarchingYamlParser)
ShaderAppearanceYamlParser.register('raymarching:emissive', VolumetricDensityEmissiveRayMarchingYamlParser)
ShaderAppearanceYamlParser.register('raymarching:bulge', BulgeRayMarchingYamlParser)
ShaderAppearanceYamlParser.register('raymarching:sdf', SDFRayMarchingYamlParser)
