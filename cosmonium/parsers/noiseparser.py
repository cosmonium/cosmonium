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

from ..procedural.shadernoise import NoiseConst, NoiseMap, PositionMap
from ..astro import units

from .yamlparser import YamlParser
from .utilsparser import DistanceUnitsYamlParser

class NoiseYamlParser(YamlParser):
    parsers = {}

    def __init__(self, length_scale=1.0):
        self.length_scale = length_scale

    @classmethod
    def register_noise_parser(cls, name, parser):
        cls.parsers[name] = parser

    def add_pos_map(self, noise, data):
        if not isinstance(data, dict): return noise
        scale = data.get('pos-scale', None)
        offset = data.get('pos-offset', None)
        if scale is None and offset is None:
            return noise
        if scale is None: scale = 1.0
        if offset is None: offset = 0.0
        offset /= self.length_scale
        return PositionMap(noise, offset, scale)

    def add_noise_map(self, noise, data):
        if not isinstance(data, dict): return noise
        min_value = data.get('min', None)
        max_value = data.get('max', None)
        if min_value is None and max_value is None:
            scale = data.get('scale', None)
            offset = data.get('offset', None)
            if scale is None and offset is None:
                return noise
            if scale is None:
                scale = 1.0
            if offset is None:
                offset = 0.0
            min_value = -scale + offset
            max_value = scale + offset
        else:
            if min_value is None:
                min_value = -1.0
            if max_value is None:
                max_value = 1.0
        return NoiseMap(noise, min_value, max_value)

    def decode_noise(self, func, parameters):
        result = None
        if func in self.parsers:
            result = self.parsers[func](self, parameters, self.length_scale)
        else:
            print("Unknown noise function", func)
        if result is not None:
            result = self.add_noise_map(self.add_pos_map(result, parameters), parameters)
        return result

    def decode_noise_dict(self, data):
        if isinstance(data, (float, int)):
            return NoiseConst(data)
        (func, parameters) = self.get_type_and_data(data)
        return self.decode_noise(func, parameters)

    def decode_noise_list(self, data):
        noises = []
        for noise in data:
            noises.append(self.decode_noise_dict(noise))
        return noises

    def decode(self, data):
        aliases = data.get('aliases', {})
        for (alias, func) in aliases.items():
            parser = self.parsers.get(func, None)
            if parser is not None:
                self.register_noise_parser(alias, parser)
            else:
                print("Function", func, "unknown")
        noise = data.get('noise')
        return self.decode_noise_dict(noise)

from ..procedural.shadernoise import NoiseClamp, NoiseMin, NoiseMax, NegNoise
from ..procedural.shadernoise import NoiseAdd, NoiseSub, NoiseMul, NoisePow, NoiseExp, NoiseThreshold
from ..procedural.shadernoise import RidgedNoise, AbsNoise, FbmNoise, SquareNoise, CubeNoise
from ..procedural.shadernoise import NoiseWarp, Noise1D, NoiseCoord, SpiralNoise, NoiseRotate
from ..procedural.shadernoise import GpuNoiseLibPerlin3D, GpuNoiseLibCellular3D, GpuNoiseLibPolkaDot3D
from ..procedural.shadernoise import SteGuPerlin3D, SteGuCellular3D, SteGuCellularDiff3D
from ..procedural.shadernoise import QuilezPerlin3D, QuilezGradientNoise3D
from ..procedural.shadernoise import SinCosNoise

def create_add_noise(parser, data, length_scale):
    if not isinstance(data, dict):
        data = {'terms': data}
    name = data.get('name', None)
    noises = parser.decode_noise_list(data.get('terms'))
    return NoiseAdd(noises, name=name)

def create_sub_noise(parser, data, length_scale):
    if not isinstance(data, dict):
        data = {'terms': data}
    name = data.get('name', None)
    a = parser.decode_noise_dict(data.get('terms')[0])
    b = parser.decode_noise_dict(data.get('terms')[1])
    return NoiseSub(a, b, name=name)

def create_mul_noise(parser, data, length_scale):
    if not isinstance(data, dict):
        data = {'factors': data}
    name = data.get('name', None)
    noises = parser.decode_noise_list(data.get('factors'))
    return NoiseMul(noises, name=name)

def create_pow_noise(parser, data, length_scale):
    if not isinstance(data, dict):
        data = {'base': data[0],
                'power': data[1]}
    name = data.get('name', None)
    base = parser.decode_noise_dict(data.get('base'))
    power = parser.decode_noise_dict(data.get('power'))
    return NoisePow(base, power, name=name)

def create_exp_noise(parser, data, length_scale):
    if not isinstance(data, dict):
        data = { 'power': data }
    name = data.get('name', None)
    power = parser.decode_noise_dict(data.get('power'))
    return NoiseExp(power, name=name)

def create_threshold_noise(parser, data, length_scale):
    if not isinstance(data, dict):
        data = {'a': data[0],
                'b': data[1]}
    name = data.get('name', None)
    a = parser.decode_noise_dict(data.get('a'))
    b = parser.decode_noise_dict(data.get('b'))
    return NoiseThreshold(a, b, name=name)

def create_clamp_noise(parser, data, length_scale):
    name = data.get('name', None)
    noise = parser.decode_noise_dict(data.get('noise'))
    min_value = data.get('min', 0.0)
    max_value = data.get('max', 1.0)
    data['min'] = None
    data['max'] = None
    return NoiseClamp(noise, min_value, max_value, name=name)

def create_min_noise(parser, data, length_scale):
    if not isinstance(data, dict):
        data = {'a': data[0],
                'b': data[1]}
    name = data.get('name', None)
    a = parser.decode_noise_dict(data.get('a'))
    b = parser.decode_noise_dict(data.get('b'))
    return NoiseMin(a, b, name=name)

def create_max_noise(parser, data, length_scale):
    if not isinstance(data, dict):
        data = {'a': data[0],
                'b': data[1]}
    name = data.get('name', None)
    a = parser.decode_noise_dict(data.get('a'))
    b = parser.decode_noise_dict(data.get('b'))
    return NoiseMax(a, b, name=name)

def create_const_noise(parser, data, length_scale):
    name = data.get('name', None)
    value = data.get('value')
    return NoiseConst(value, dynamic=name is not None, name=name)

def create_x_noise(parser, data, length_scale):
    if not isinstance(data, dict):
        data = {}
    name = data.get('name', None)
    return NoiseCoord('x', name=name)

def create_y_noise(parser, data, length_scale):
    if not isinstance(data, dict):
        data = {}
    name = data.get('name', None)
    return NoiseCoord('y', name=name)

def create_z_noise(parser, data, length_scale):
    if not isinstance(data, dict):
        data = {}
    name = data.get('name', None)
    return NoiseCoord('z', name=name)

def create_gpunoise_perlin_noise(parser, data, length_scale):
    if not isinstance(data, dict):
        data = {}
    name = data.get('name', None)
    return GpuNoiseLibPerlin3D(name)

def create_gpunoise_cellular_noise(parser, data, length_scale):
    if not isinstance(data, dict):
        data = {}
    name = data.get('name', None)
    return GpuNoiseLibCellular3D(name)

def create_gpunoise_polkadot_noise(parser, data, length_scale):
    name = data.get('name', None)
    min_value = data.get('min', 0.0)
    max_value = data.get('max', 1.0)
    data['min'] = None
    data['max'] = None
    return GpuNoiseLibPolkaDot3D(min_value, max_value, name=name)

def create_stegu_perlin_noise(parser, data, length_scale):
    if not isinstance(data, dict):
        data = {}
    name = data.get('name', None)
    return SteGuPerlin3D(name)

def create_stegu_cellular_noise(parser, data, length_scale):
    name = data.get('name', None)
    fast = data.get('fast', None)
    return SteGuCellular3D(fast, name=name)

def create_stegu_cellulardiff_noise(parser, data, length_scale):
    name = data.get('name', None)
    fast = data.get('fast', None)
    return SteGuCellularDiff3D(fast, name=name)

def create_iq_perlin_noise(parser, data, length_scale):
    if not isinstance(data, dict):
        data = {}
    name = data.get('name', None)
    return QuilezPerlin3D(name)

def create_iq_gradient_noise(parser, data, length_scale):
    if not isinstance(data, dict):
        data = {}
    name = data.get('name', None)
    return QuilezGradientNoise3D(name)

def create_sincos_noise(parser, data, length_scale):
    if not isinstance(data, dict):
        data = {}
    name = data.get('name', None)
    return SinCosNoise(name)

def create_ridged_noise(parser, data, length_scale):
    if isinstance(data, str):
        data = {'noise': data}
    name = data.get('name', None)
    noise = parser.decode_noise_dict(data.get('noise'))
    shift = data.get('shift', True)
    return RidgedNoise(noise, shift=shift, name=name)

def create_abs_noise(parser, data, length_scale):
    if not isinstance(data, dict):
        data = {'noise': data}
    name = data.get('name', None)
    noise = parser.decode_noise_dict(data.get('noise'))
    return AbsNoise(noise, name=name)

def create_neg_noise(parser, data, length_scale):
    if not isinstance(data, dict):
        data = {'noise': data}
    name = data.get('name', None)
    noise = parser.decode_noise_dict(data.get('noise'))
    return NegNoise(noise, name=name)

def create_square_noise(parser, data, length_scale):
    if not isinstance(data, dict):
        data = {'noise': data}
    name = data.get('name', None)
    noise = parser.decode_noise_dict(data.get('noise'))
    return SquareNoise(noise, name=name)

def create_cube_noise(parser, data, length_scale):
    if not isinstance(data, dict):
        data = {'noise': data}
    name = data.get('name', None)
    noise = parser.decode_noise_dict(data.get('noise'))
    return CubeNoise(noise, name=name)

def create_1d_noise(parser, data, length_scale):
    name = data.get('name', None)
    noise = parser.decode_noise_dict(data.get('noise'))
    axis = data.get('axis', "z")
    return Noise1D(noise, axis, name=name)

def create_fbm_noise(parser, data, length_scale):
    name = data.get('name', None)
    noise = parser.decode_noise_dict(data.get('noise'))
    octaves = data.get('octaves', 8)
    frequency = data.get('frequency', None)
    if frequency is None:
        length = data.get('length', length_scale)
        length_units = DistanceUnitsYamlParser.decode(data.get('length-units'), units.Km)
        if length is not None:
            length *= length_units
            frequency = length_scale / (length * 4)
        else:
            frequency = 1.0
    lacunarity = data.get('lacunarity', 2.0)
    geometric = data.get('geometric', True)
    h = data.get('h', 0.25)
    gain = data.get('gain', 0.5)

    return FbmNoise(noise, octaves, frequency, lacunarity, geometric, h, gain, name=name)

def create_spiral_noise(parser, data, length_scale):
    name = data.get('name', None)
    noise = parser.decode_noise_dict(data.get('noise'))
    octaves = data.get('octaves', 8)
    frequency = data.get('frequency', 1.0)
    lacunarity = data.get('lacunarity', 2.0)
    gain = data.get('gain', 0.5)
    nudge = data.get('nudge', 0.5)

    return SpiralNoise(noise, octaves, frequency, lacunarity, gain, nudge, name=name)

def create_warp_noise(parser, data, length_scale):
    name = data.get('name', None)
    main = parser.decode_noise_dict(data.get('noise'))
    warp = parser.decode_noise_dict(data.get('warp'))
    scale = float(data.get('strength', 4.0))
    return NoiseWarp(main, warp, scale, name=name)

def create_rotate_noise(parser, data, length_scale):
    name = data.get('name', None)
    main = parser.decode_noise_dict(data.get('noise'))
    angle = parser.decode_noise_dict(data.get('angle'))
    axis = data.get('axis', 'x')
    return NoiseRotate(main, angle, axis, name=name)

NoiseYamlParser.register_noise_parser('add', create_add_noise)
NoiseYamlParser.register_noise_parser('sub', create_sub_noise)
NoiseYamlParser.register_noise_parser('mul', create_mul_noise)
NoiseYamlParser.register_noise_parser('pow', create_pow_noise)
NoiseYamlParser.register_noise_parser('exp', create_exp_noise)
NoiseYamlParser.register_noise_parser('threshold', create_threshold_noise)
NoiseYamlParser.register_noise_parser('clamp', create_clamp_noise)
NoiseYamlParser.register_noise_parser('min', create_min_noise)
NoiseYamlParser.register_noise_parser('max', create_max_noise)
NoiseYamlParser.register_noise_parser('abs', create_abs_noise)
NoiseYamlParser.register_noise_parser('neg', create_neg_noise)
NoiseYamlParser.register_noise_parser('1d', create_1d_noise)
NoiseYamlParser.register_noise_parser('square', create_square_noise)
NoiseYamlParser.register_noise_parser('cube', create_cube_noise)

NoiseYamlParser.register_noise_parser('ridged', create_ridged_noise)
NoiseYamlParser.register_noise_parser('turbulence', create_abs_noise)
NoiseYamlParser.register_noise_parser('fbm', create_fbm_noise)
NoiseYamlParser.register_noise_parser('spiral', create_spiral_noise)
NoiseYamlParser.register_noise_parser('warp', create_warp_noise)
NoiseYamlParser.register_noise_parser('rot', create_rotate_noise)

NoiseYamlParser.register_noise_parser('const', create_const_noise)
NoiseYamlParser.register_noise_parser('x', create_x_noise)
NoiseYamlParser.register_noise_parser('y', create_y_noise)
NoiseYamlParser.register_noise_parser('z', create_z_noise)
NoiseYamlParser.register_noise_parser('gpunoise:perlin', create_gpunoise_perlin_noise)
NoiseYamlParser.register_noise_parser('gpunoise:cellular', create_gpunoise_cellular_noise)
NoiseYamlParser.register_noise_parser('gpunoise:polkadot', create_gpunoise_polkadot_noise)
NoiseYamlParser.register_noise_parser('stegu:perlin', create_stegu_perlin_noise)
NoiseYamlParser.register_noise_parser('stegu:cellular', create_stegu_cellular_noise)
NoiseYamlParser.register_noise_parser('stegu:cellulardiff', create_stegu_cellulardiff_noise)
NoiseYamlParser.register_noise_parser('iq:perlin', create_iq_perlin_noise)
NoiseYamlParser.register_noise_parser('iq:gradient', create_iq_gradient_noise)
NoiseYamlParser.register_noise_parser('sincos', create_sincos_noise)
