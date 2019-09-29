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

from panda3d.core import LVector3, LMatrix3, LMatrix4

from ..shaders import StructuredShader, ShaderProgram, ShaderComponent
from ..dircontext import defaultDirContext
from ..textures import TexCoord
from .. import settings

class NoiseSource(object):
    def get_id(self):
        return ''

    def noise_uniforms(self, code):
        pass

    def noise_extra(self, program, code):
        pass

    def noise_func(self, code):
        pass

    def noise_value(self, code, value, point):
        pass

    def update(self, instance):
        pass

class NoiseConst(NoiseSource):
    def __init__(self, value):
        NoiseSource.__init__(self)
        self.value = value

    def get_id(self):
        return '%g' % self.value

    def noise_value(self, code, value, point):
        code.append('        %s  = %g;' % (value, self.value))

class GpuNoiseLibPerlin3D(NoiseSource):
    def get_id(self):
        return 'gnl-perlin3d'

    def noise_extra(self, program, code):
        program.include(code, 'gnl-FAST32_hash', defaultDirContext.find_shader("gpu-noise-lib/FAST32_hash.glsl"))
        program.include(code, 'gnl-Interpolation', defaultDirContext.find_shader("gpu-noise-lib/Interpolation.glsl"))
        program.include(code, 'gnl-Noise', defaultDirContext.find_shader("gpu-noise-lib/Perlin3D.glsl"))

    def noise_value(self, code, value, point):
        code.append('        %s  = Perlin3D(%s);' % (value, point))

class GpuNoiseLibCellular3D(NoiseSource):
    def get_id(self):
        return 'gnl-cell3d'

    def noise_extra(self, program, code):
        program.include(code, 'gnl-FAST32_hash', defaultDirContext.find_shader("gpu-noise-lib/FAST32_hash.glsl"))
        program.include(code, 'gnl-Cellular', defaultDirContext.find_shader("gpu-noise-lib/Cellular.glsl"))

    def noise_value(self, code, value, point):
        code.append('        %s  = sqrt(Cellular3D(%s));' % (value, point))

class GpuNoiseLibPolkaDot3D(NoiseSource):
    def __init__(self, min_radius, max_radius):
        NoiseSource.__init__(self)
        self.min_radius = min_radius
        self.max_radius = max_radius

    def get_id(self):
        return 'gnl-polkadot3d'

    def noise_extra(self, program, code):
        program.include(code, 'gnl-FAST32_hash', defaultDirContext.find_shader("gpu-noise-lib/FAST32_hash.glsl"))
        program.include(code, 'gnl-Falloff', defaultDirContext.find_shader("gpu-noise-lib/Falloff.glsl"))
        program.include(code, 'gnl-PolkaDot', defaultDirContext.find_shader("gpu-noise-lib/PolkaDot.glsl"))

    def noise_value(self, code, value, point):
        code.append('        %s  = PolkaDot3D(%s, %g, %g);' % (value, point, self.min_radius, self.max_radius))

class SteGuPerlin3D(NoiseSource):
    def get_id(self):
        return 'stegu-perlin3d'

    def noise_extra(self, program, code):
        program.include(code, 'stegu-common', defaultDirContext.find_shader("stegu/common.glsl"))
        program.include(code, 'stegu-snoise', defaultDirContext.find_shader("stegu/noise3D.glsl"))

    def noise_value(self, code, value, point):
        code.append('        %s  = snoise(%s);' % (value, point))

class SteGuCellular3D(NoiseSource):
    def __init__(self, fast):
        NoiseSource.__init__(self)
        self.fast = fast

    def get_id(self):
        if self.fast:
            return 'stegu-cellular3d-fast'
        else:
            return 'stegu-cellular3d'

    def noise_extra(self, program, code):
        program.include(code, 'stegu-common', defaultDirContext.find_shader("stegu/common.glsl"))
        if self.fast:
            program.include(code, 'stegu-cellular', defaultDirContext.find_shader("stegu/cellular2x2x2.glsl"))
        else:
            program.include(code, 'stegu-cellular', defaultDirContext.find_shader("stegu/cellular3D.glsl"))

    def noise_value(self, code, value, point):
        if self.fast:
            code.append('        %s = cellular2x2x2(%s).x;' % (value, point))
        else:
            code.append('        %s = cellular(%s).x;' % (value, point))

class SteGuCellularDiff3D(SteGuCellular3D):
    def get_id(self):
        return SteGuCellular3D.get_id(self) + '-diff'

    def noise_value(self, code, value, point):
        if self.fast:
            code.append('        vec2 F = cellular2x2x2(%s);' % (point))
        else:
            code.append('        vec2 F = cellular(%s);' % (point))
        code.append('        %s  = F.y - F.x;' % (value))

class QuilezPerlin3D(NoiseSource):
    def get_id(self):
        return 'quilez-gradientnoise3d'

    def noise_extra(self, program, code):
        program.include(code, 'quilez-noise', defaultDirContext.find_shader("quilez/GradientNoise3D.glsl"))

    def noise_value(self, code, value, point):
        code.append('        %s  = noise(%s);' % (value, point))

class TurbulenceNoise(NoiseSource):
    def __init__(self, noise):
        self.noise = noise

    def get_id(self):
        return 'turbulence-' + self.noise.get_id()

    def noise_uniforms(self, code):
        self.noise.noise_uniforms(code)

    def noise_extra(self, program, code):
        self.noise.noise_extra(program, code)

    def noise_func(self, code):
        self.noise.noise_func(code)

    def noise_value(self, code, value, point):
        code.append('        {')
        self.noise.noise_value(code, 'float tmp', point)
        code.append('        %s = abs(tmp);' % value)
        code.append('        }')

class AbsNoise(NoiseSource):
    def __init__(self, noise):
        self.noise = noise

    def get_id(self):
        return 'abs-' + self.noise.get_id()

    def noise_uniforms(self, code):
        self.noise.noise_uniforms(code)

    def noise_extra(self, program, code):
        self.noise.noise_extra(program, code)

    def noise_func(self, code):
        self.noise.noise_func(code)

    def noise_value(self, code, value, point):
        code.append('        {')
        self.noise.noise_value(code, 'float tmp', point)
        code.append('        %s = abs(tmp);' % value)
        code.append('        }')

class RidgedNoise(NoiseSource):
    def __init__(self, noise, offset=0.33, shift=True):
        self.noise = noise
        self.offset = offset
        self.shift = shift

    def get_id(self):
        return 'ridged-' + self.noise.get_id()

    def noise_uniforms(self, code):
        self.noise.noise_uniforms(code)

    def noise_extra(self, program, code):
        self.noise.noise_extra(program, code)

    def noise_func(self, code):
        self.noise.noise_func(code)

    def noise_value(self, code, value, point):
        code.append('        {')
        self.noise.noise_value(code, 'float tmp', point)
        if self.shift:
            code.append('        %s  = (1.0 - abs(tmp) - %g) * 2.0 - 1.0;' % (value, self.offset))
        else:
            code.append('        %s  = (1.0 - abs(tmp) - %g);' % (value, self.offset))
        code.append('        }')

class SquareNoise(NoiseSource):
    def __init__(self, noise):
        self.noise = noise

    def get_id(self):
        return 'square-' + self.noise.get_id()

    def noise_uniforms(self, code):
        self.noise.noise_uniforms(code)

    def noise_extra(self, program, code):
        self.noise.noise_extra(program, code)

    def noise_func(self, code):
        self.noise.noise_func(code)

    def noise_value(self, code, value, point):
        code.append('        {')
        self.noise.noise_value(code, 'float tmp', point)
        code.append('        %s = tmp * tmp;' % value)
        code.append('        }')

class CubeNoise(NoiseSource):
    def __init__(self, noise):
        self.noise = noise

    def get_id(self):
        return 'cube-' + self.noise.get_id()

    def noise_uniforms(self, code):
        self.noise.noise_uniforms(code)

    def noise_extra(self, program, code):
        self.noise.noise_extra(program, code)

    def noise_func(self, code):
        self.noise.noise_func(code)

    def noise_value(self, code, value, point):
        code.append('        {')
        self.noise.noise_value(code, 'float tmp', point)
        code.append('        %s = tmp * tmp * tmp;' % value)
        code.append('        }')

class NoiseSourceScale(NoiseSource):
    def __init__(self, noise, value):
        NoiseSource.__init__(self)
        self.noise = noise
        self.value = value

    def get_id(self):
        return ('scale-%g-' % self.value) + self.noise.get_id()

    def noise_uniforms(self, code):
        self.noise.noise_uniforms(code)

    def noise_extra(self, program, code):
        self.noise.noise_extra(program, code)

    def noise_func(self, code):
        self.noise.noise_func(code)

    def noise_value(self, code, value, point):
        self.noise.noise_value(code, value, '%s * %g' % (point, self.value))

    def update(self, instance):
        self.noise.update(instance)

class NoiseOffset(NoiseSource):
    def __init__(self, noise, value):
        NoiseSource.__init__(self)
        self.noise = noise
        self.value = value

    def get_id(self):
        return ('offset-%g-' % self.value) + self.noise.get_id()

    def noise_uniforms(self, code):
        self.noise.noise_uniforms(code)

    def noise_extra(self, program, code):
        self.noise.noise_extra(program, code)

    def noise_func(self, code):
        self.noise.noise_func(code)

    def noise_value(self, code, value, point):
        self.noise.noise_value(code, value, '%s + %g' % (point, self.value))

    def update(self, instance):
        self.noise.update(instance)

class NoiseAdd(NoiseSource):
    fid = 0
    def __init__(self, noises):
        self.noises = noises
        NoiseAdd.fid += 1
        self.id = NoiseAdd.fid

    def get_id(self):
        return "add-" + '-'.join(map(lambda x: x.get_id(), self.noises))

    def noise_uniforms(self, code):
        for noise in self.noises:
            noise.noise_uniforms(code)

    def noise_extra(self, program, code):
        for noise in self.noises:
            noise.noise_extra(program, code)

    def noise_func(self, code):
        for noise in self.noises:
            noise.noise_func(code)
        code.append('float noise_add_%d(vec3 point)' % self.id)
        code.append('{')
        for (i, noise) in enumerate(self.noises):
            noise.noise_value(code, 'float value_%d' % i, 'point')
        add = ' + '.join(map(lambda i: 'value_%d' % i, range(len(self.noises))))
        code.append('  return %s;' % add)
        code.append('}')

    def noise_value(self, code, value, point):
        code.append('%s = noise_add_%d(%s);' % (value, self.id, point))

    def update(self, instance):
        for noise in self.noises:
            noise.update(instance)

class NoiseSub(NoiseSource):
    fid = 0
    def __init__(self, noise_a, noise_b):
        self.noise_a = noise_a
        self.noise_b = noise_b
        NoiseSub.fid += 1
        self.id = NoiseSub.fid

    def get_id(self):
        return self.noise_a.get_id() + "-sub-" + self.noise_b.get_id()

    def noise_uniforms(self, code):
        self.noise_a.noise_uniforms(code)
        self.noise_b.noise_uniforms(code)

    def noise_extra(self, program, code):
        self.noise_a.noise_extra(program, code)
        self.noise_b.noise_extra(program, code)

    def noise_func(self, code):
        self.noise_a.noise_func(code)
        self.noise_b.noise_func(code)
        code.append('float noise_sub_%d(vec3 point)' % self.id)
        code.append('{')
        code.append('  float value_a;')
        code.append('  float value_b;')
        self.noise_a.noise_value(code, 'value_a', 'point')
        self.noise_b.noise_value(code, 'value_b', 'point')
        code.append('  return value_a - value_b;')
        code.append('}')

    def noise_value(self, code, value, point):
        code.append('%s = noise_sub_%d(%s);' % (value, self.id, point))

    def update(self, instance):
        self.noise_a.update(instance)
        self.noise_b.update(instance)

class NoiseMul(NoiseSource):
    fid = 0
    def __init__(self, noises):
        self.noises = noises
        NoiseMul.fid += 1
        self.id = NoiseMul.fid

    def get_id(self):
        return "mul-" + '-'.join(map(lambda x: x.get_id(), self.noises))

    def noise_uniforms(self, code):
        for noise in self.noises:
            noise.noise_uniforms(code)

    def noise_extra(self, program, code):
        for noise in self.noises:
            noise.noise_extra(program, code)

    def noise_func(self, code):
        for noise in self.noises:
            noise.noise_func(code)
        code.append('float noise_mul_%d(vec3 point)' % self.id)
        code.append('{')
        for (i, noise) in enumerate(self.noises):
            noise.noise_value(code, 'float value_%d' % i, 'point')
        mul = ' * '.join(map(lambda i: 'value_%d' % i, range(len(self.noises))))
        code.append('  return %s;' % mul)
        code.append('}')

    def noise_value(self, code, value, point):
        code.append('%s = noise_mul_%d(%s);' % (value, self.id, point))

    def update(self, instance):
        for noise in self.noises:
            noise.update(instance)

class NoisePow(NoiseSource):
    fid = 0
    def __init__(self, noise_a, noise_b):
        self.noise_a = noise_a
        self.noise_b = noise_b
        NoisePow.fid += 1
        self.id = NoisePow.fid

    def get_id(self):
        return self.noise_a.get_id() + "-pow-" + self.noise_b.get_id()

    def noise_uniforms(self, code):
        self.noise_a.noise_uniforms(code)
        self.noise_b.noise_uniforms(code)

    def noise_extra(self, program, code):
        self.noise_a.noise_extra(program, code)
        self.noise_b.noise_extra(program, code)

    def noise_func(self, code):
        self.noise_a.noise_func(code)
        self.noise_b.noise_func(code)
        code.append('float noise_pow_%d(vec3 point)' % self.id)
        code.append('{')
        code.append('  float value_a;')
        code.append('  float value_b;')
        self.noise_a.noise_value(code, 'value_a', 'point')
        self.noise_b.noise_value(code, 'value_b', 'point')
        code.append('  return pow(value_a, value_b);')
        code.append('}')

    def noise_value(self, code, value, point):
        code.append('%s = noise_pow_%d(%s);' % (value, self.id, point))

    def update(self, instance):
        self.noise_a.update(instance)
        self.noise_b.update(instance)

class NoiseThreshold(NoiseSource):
    fid = 0
    def __init__(self, noise_a, noise_b):
        self.noise_a = noise_a
        self.noise_b = noise_b
        NoiseThreshold.fid += 1
        self.id = NoiseThreshold.fid

    def get_id(self):
        return self.noise_a.get_id() + "-threshold-" + self.noise_b.get_id()

    def noise_uniforms(self, code):
        self.noise_a.noise_uniforms(code)
        self.noise_b.noise_uniforms(code)

    def noise_extra(self, program, code):
        self.noise_a.noise_extra(program, code)
        self.noise_b.noise_extra(program, code)

    def noise_func(self, code):
        self.noise_a.noise_func(code)
        self.noise_b.noise_func(code)
        code.append('float noise_threshold_%d(vec3 point)' % self.id)
        code.append('{')
        code.append('  float value_a;')
        code.append('  float value_b;')
        self.noise_a.noise_value(code, 'value_a', 'point')
        self.noise_b.noise_value(code, 'value_b', 'point')
        code.append('  return max((value_a - value_b), 0.0);')
        code.append('}')

    def noise_value(self, code, value, point):
        code.append('%s = noise_threshold_%d(%s);' % (value, self.id, point))

    def update(self, instance):
        self.noise_a.update(instance)
        self.noise_b.update(instance)

class NoiseClamp(NoiseSource):
    fid = 0
    def __init__(self, noise, min_value, max_value):
        NoiseSource.__init__(self)
        self.noise = noise
        self.min_value = min_value
        self.max_value = max_value
        NoiseClamp.fid += 1
        self.id = NoiseClamp.fid

    def get_id(self):
        return ('clamp-%g-%g-' % (self.min_value, self.max_value)) + self.noise.get_id()

    def noise_uniforms(self, code):
        self.noise.noise_uniforms(code)

    def noise_extra(self, program, code):
        self.noise.noise_extra(program, code)

    def noise_func(self, code):
        self.noise.noise_func(code)
        code.append('float noise_clamp_%d(vec3 point)' % self.id)
        code.append('{')
        code.append('  float value;')
        self.noise.noise_value(code, 'value', 'point')
        code.append('  return clamp(value, %g, %g);' % (self.min_value, self.max_value))
        code.append('}')

    def noise_value(self, code, value, point):
        code.append('%s = noise_clamp_%d(%s);' % (value, self.id, point))

    def update(self, instance):
        self.noise.update(instance)

class NoiseMap(NoiseSource):
    fid = 0
    def __init__(self, noise, min_value=0.0, max_value=1.0, src_min_value=-1.0, src_max_value=1.0):
        self.noise = noise
        self.min_value = min_value
        self.max_value = max_value
        self.src_min_value = src_min_value
        self.src_max_value = src_max_value
        self.range = self.max_value - self.min_value
        self.src_range = self.src_max_value - self.src_min_value
        self.range_factor = self.range / self.src_range
        NoiseMap.fid += 1
        self.id = NoiseMap.fid

    def get_id(self):
        return 'map-%g-%g-' % (self.min_value, self.max_value) + self.noise.get_id()

    def noise_uniforms(self, code):
        self.noise.noise_uniforms(code)

    def noise_extra(self, program, code):
        self.noise.noise_extra(program, code)

    def noise_func(self, code):
        self.noise.noise_func(code)
        code.append('float noise_map_%d(vec3 point)' % self.id)
        code.append('{')
        code.append('  float value;')
        self.noise.noise_value(code, 'value', 'point')
        code.append('  return clamp((value - %g) * %g + %g, %f, %f);' % (self.src_min_value, self.range_factor, self.min_value, self.min_value, self.max_value))
        code.append('}')

    def noise_value(self, code, value, point):
        code.append('%s = noise_map_%d(%s);' % (value, self.id, point))

    def update(self, instance):
        self.noise.update(instance)

class Noise1D(NoiseSource):
    fid = 0
    def __init__(self, noise, axis):
        NoiseSource.__init__(self)
        self.noise = noise
        self.axis = axis
        Noise1D.fid += 1
        self.id = Noise1D.fid

    def get_id(self):
        return ('axis-%s-' % (self.axis)) + self.noise.get_id()

    def noise_uniforms(self, code):
        self.noise.noise_uniforms(code)

    def noise_extra(self, program, code):
        self.noise.noise_extra(program, code)

    def noise_func(self, code):
        self.noise.noise_func(code)
        code.append('float noise_axis_%d(vec3 point)' % self.id)
        code.append('{')
        code.append('  float value;')
        code.append('  vec3 point_1d = vec3(0);')
        code.append('  point_1d.%s = point.%s;' % (self.axis, self.axis))
        self.noise.noise_value(code, 'value', 'point_1d')
        code.append('  return value;')
        code.append('}')

    def noise_value(self, code, value, point):
        code.append('%s = noise_axis_%d(%s);' % (value, self.id, point))

    def update(self, instance):
        self.noise.update(instance)

class FbmNoise(NoiseSource):
    fid = 0
    def __init__(self, noise, octaves=8, frequency=1.0, lacunarity=2.0, geometric=True, h=0.25, gain=0.5):
        NoiseSource.__init__(self)
        FbmNoise.fid += 1
        self.id = FbmNoise.fid
        self.name = 'fbm_%d' % self.id
        self.noise = noise
        self.octaves = octaves
        self.frequency = frequency
        self.lacunarity = lacunarity
        self.geometric = geometric
        self.h = h
        self.gain = gain

    def get_id(self):
        if self.geometric:
            geom = '-g'
        else:
            geom = ''
        return self.name + geom + '-' + self.noise.get_id()

    def noise_uniforms(self, code):
        self.noise.noise_uniforms(code)
        code += ["uniform float %s_octaves;" % self.name,
                 "uniform float %s_frequency;" % self.name,
                 "uniform float %s_lacunarity;" % self.name,
                 "uniform float %s_amplitude;" % self.name
                 ]
        if self.geometric:
            code.append("uniform float %s_gain;" % self.name)
        else:
            code.append("uniform float %s_h;" % self.name)

    def noise_extra(self, program, code):
        self.noise.noise_extra(program, code)

    def noise_func(self, code):
        self.noise.noise_func(code)
        code.append('float Fbm_%s(vec3 point)' % self.name)
        code.append('{')
        code.append("float frequency = %s_frequency;" % self.name)
        if self.geometric:
            code.append("float gain = %s_gain;" % self.name)
        else:
            code.append("float gain = pow(%s_lacunarity, -%s_h);" % (self.name, self.name))
        code.append('    float result = 0.0;')
        code.append('    float amplitude = 1.0;')
        code.append('    float max_value = 0.0;')
        code.append('    for (int i = 0; i < %s_octaves; ++i)' % self.name)
        code.append('    {')
        code.append('        float value;')
        self.noise.noise_value(code, 'value', 'point * frequency')
        code.append('        result += value * amplitude;')
        code.append('        max_value += amplitude;')
        code.append('        amplitude *= gain;')
        code.append('        frequency *= %s_lacunarity;' % self.name)
        code.append('    }')
        code.append('    return result / max_value;')
        code.append('}')

    def noise_value(self, code, value, point):
        code.append('%s = Fbm_%s(%s);' % (value, self.name, point))

    def set(self, key, value):
        if key == 'noiseOctaves':
            self.octaves = value
        elif key == 'noiseFrequency':
            self.frequency = value
        elif key == 'noiseLacunarity':
            self.lacunarity = value
        elif key == 'noiseAmplitude':
            self.amplitude = value
        elif key == 'noiseGain':
            self.gain = value
        elif key == 'noiseH':
            self.h = value
        else:
            print("Unknown parameter", key)

    def update(self, instance):
        self.noise.update(instance)
        instance.set_shader_input('%s_octaves' % self.name, self.octaves)
        instance.set_shader_input('%s_frequency' % self.name, self.frequency)
        instance.set_shader_input('%s_lacunarity' % self.name, self.lacunarity)
        if self.geometric:
            instance.set_shader_input('%s_gain' % self.name, self.gain)
        else:
            instance.set_shader_input('%s_h' % self.name, self.h)

class NoiseWarp(NoiseSource):
    fid = 0
    def __init__(self, noise_main, noise_warp, scale=4.0):
        self.noise_main = noise_main
        self.noise_warp = noise_warp
        self.scale = scale
        NoiseWarp.fid += 1
        self.id = NoiseWarp.fid

    def get_id(self):
        return self.noise_main.get_id() + "-warp-" + self.noise_warp.get_id()

    def noise_uniforms(self, code):
        self.noise_main.noise_uniforms(code)
        self.noise_warp.noise_uniforms(code)

    def noise_extra(self, program, code):
        self.noise_main.noise_extra(program, code)
        self.noise_warp.noise_extra(program, code)

    def noise_func(self, code):
        self.noise_main.noise_func(code)
        self.noise_warp.noise_func(code)
        code.append('float noise_warp_%d(vec3 point)' % self.id)
        code.append('{')
        code.append('  vec3 warped_point;')
        code.append('  float value;')
        self.noise_warp.noise_value(code, 'warped_point.x', 'point')
        self.noise_warp.noise_value(code, 'warped_point.y', 'point + vec3(1, 2, 3)')
        self.noise_warp.noise_value(code, 'warped_point.z', 'point + vec3(4, 3, 2)')
        self.noise_main.noise_value(code, 'value', 'point + %g * warped_point' % self.scale)
        code.append('  return value;')
        code.append('}')

    def noise_value(self, code, value, point):
        code.append('%s = noise_warp_%d(%s);' % (value, self.id, point))

    def update(self, instance):
        self.noise_main.update(instance)
        self.noise_warp.update(instance)

class NoiseVertexShader(ShaderProgram):
    def __init__(self):
        ShaderProgram.__init__(self, 'vertex')

    def create_uniforms(self, code):
        code.append("uniform mat4 p3d_ModelViewProjectionMatrix;")

    def create_inputs(self, code):
        code.append("in vec2 p3d_MultiTexCoord0;")
        code.append("in vec4 p3d_Vertex;")

    def create_outputs(self, code):
        code.append("out vec2 texcoord;")

    def create_body(self, code):
        code.append("gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;")
        code.append("texcoord = p3d_MultiTexCoord0;")

class NoiseFragmentShader(ShaderProgram):
    def __init__(self, coord, noise_source, noise_target):
        ShaderProgram.__init__(self, 'fragment')
        self.coord = coord
        self.noise_source = noise_source
        self.noise_target = noise_target

    def create_uniforms(self, code):
        code.append("uniform vec3 noiseOffset;")
        code.append("uniform vec3 noiseScale;")
        code.append("uniform float global_frequency;")
        code.append("uniform vec3 global_offset;")
        code.append("uniform float global_scale;")
        if self.coord == TexCoord.NormalizedCube or self.coord == TexCoord.SqrtCube:
            code.append("uniform mat3 cube_rot;")
        self.noise_source.noise_uniforms(code)
        self.noise_target.fragment_uniforms(code)

    def create_inputs(self, code):
        code.append("in vec2 texcoord;")

    def create_outputs(self, code):
        if self.version >= 130:
            code.append("out vec4 frag_output;")

    def create_extra(self, code):
        self.pi(code)
        if settings.encode_float:
            self.add_encode_rgba(code)
        self.noise_source.noise_extra(self, code)
        self.noise_source.noise_func(code)
        self.noise_target.fragment_extra(code)
        self.calc_noise_value(code)

    def calc_noise_value(self, code):
        code.append('float calc_noise_value(vec2 coord) {')
        code.append('vec3 position;')
        if self.coord == TexCoord.Cylindrical:
            code.append('float nx = 2 * pi * (noiseOffset.x + coord.x * noiseScale.x);')
            code.append('float ny = pi * (noiseOffset.y + (1.0 - coord.y) * noiseScale.y);')
            code.append('float cnx = cos(nx);')
            code.append('float snx = sin(nx);')
            code.append('float cny = cos(ny);')
            code.append('float sny = sin(ny);')
            code.append('position.x = cnx * sny;')
            code.append('position.y = snx * sny;')
            code.append('position.z = cny;')
        elif self.coord == TexCoord.NormalizedCube:
            code.append('vec3 p;')
            code.append('p.x = 2.0 * (noiseOffset.x + coord.x * noiseScale.x) - 1.0;')
            code.append('p.y = 2.0 * (noiseOffset.y + (1.0 - coord.y) * noiseScale.y) - 1.0;')
            code.append('p.z = 1.0;')
            code.append('position = normalize(cube_rot * p);')
        elif self.coord == TexCoord.SqrtCube:
            code.append('vec3 p;')
            code.append('p.x = 2.0 * (noiseOffset.x + coord.x * noiseScale.x) - 1.0;')
            code.append('p.y = 2.0 * (noiseOffset.y + (1.0 - coord.y) * noiseScale.y) - 1.0;')
            code.append('p.z = 1.0;')
            code.append('p = cube_rot * p;')
            code.append('vec3 p2 = p * p;')
            code.append("position.x = p.x * sqrt(1.0 - p2.y * 0.5 - p2.z * 0.5 + p2.y * p2.z / 3.0);")
            code.append("position.y = p.y * sqrt(1.0 - p2.z * 0.5 - p2.x * 0.5 + p2.z * p2.x / 3.0);")
            code.append("position.z = p.z * sqrt(1.0 - p2.x * 0.5 - p2.y * 0.5 + p2.x * p2.y / 3.0);")
        else:
            code.append('position.x = noiseOffset.x + coord.x * noiseScale.x;')
            code.append('position.y = noiseOffset.y + (1.0 - coord.y) * noiseScale.y;')
            code.append('position.z = noiseOffset.z;')
        code.append('position = position * global_frequency + global_offset;')
        code.append('float value;')
        self.noise_source.noise_value(code, 'value', 'position')
        code.append('return value * global_scale;')
        code.append('}')

    def create_body(self, code):
        if self.version < 130:
            code.append('vec4 frag_output;')
        code.append('float value = calc_noise_value(texcoord.xy);')
        self.noise_target.apply_noise(code)
        if self.version < 130:
            code.append('gl_FragColor = frag_output;')

class NoiseShader(StructuredShader):
    coord_map = {TexCoord.Cylindrical: 'cyl',
                 TexCoord.Flat: 'flat',
                 TexCoord.NormalizedCube: 'cube',
                 TexCoord.SqrtCube: 'sqrtcube'}
    def __init__(self, coord = TexCoord.Cylindrical, noise_source=None, noise_target=None, offset=None, scale=None):
        StructuredShader.__init__(self)
        self.coord = coord
        self.noise_source = noise_source
        self.noise_target = noise_target
        if offset is None:
            offset = LVector3(0, 0, 0)
        self.offset = offset
        if scale is None:
            scale = LVector3(1, 1, 1)
        self.scale = scale
        self.global_frequency = 1.0
        self.global_offset = LVector3(0, 0, 0)
        self.global_scale = 1.0
        self.vertex_shader = NoiseVertexShader()
        self.fragment_shader = NoiseFragmentShader(self.coord, self.noise_source, self.noise_target)
        #self.texture = loader.loadTexture('permtexture.png')

    def get_shader_id(self):
        name = 'noise'
        config = ""
        config += self.coord_map[self.coord]
        if config:
            name += '-' + config
        noise = self.noise_source.get_id()
        if noise != '':
            name += '-' + noise
        target = self.noise_target.get_id()
        if target != '':
            name += '-' + target
        return name

    def get_rot_for_face(self, face):
        if face == 0:
            return LMatrix3(0.0, 0.0, 1.0,
                            0.0, 1.0, 0.0,
                            -1.0, 0.0, 0.0)
        elif face == 1:
            return LMatrix3(0.0, 0.0, -1.0,
                            0.0, 1.0, 0.0,
                            1.0, 0.0, 0.0)
        elif face == 2:
            return LMatrix3(1.0, 0.0, 0.0,
                            0.0, 0.0, -1.0,
                            0.0, 1.0, 0.0)
        elif face == 3:
            return LMatrix3(1.0, 0.0, 0.0,
                            0.0, 0.0, 1.0,
                            0.0, -1.0, 0.0)
        elif face == 4:
            return LMatrix3(-1.0, 0.0, 0.0,
                            0.0, -1.0, 0.0,
                            0.0, 0.0, 1.0)
        elif face == 5:
            return LMatrix3(-1.0, 0.0, 0.0,
                            0.0, 1.0, 0.0,
                            0.0, 0.0, -1.0)
        else:
            return LMatrix3(1.0, 0.0, 0.0,
                            0.0, 1.0, 0.0,
                            0.0, 0.0, 1.0)

    def update(self, instance, face):
        instance.set_shader_input('noiseOffset', self.offset)
        instance.set_shader_input('noiseScale', self.scale)
        instance.set_shader_input('global_frequency', self.global_frequency)
        instance.set_shader_input('global_offset', self.global_offset)
        instance.set_shader_input('global_scale', self.global_scale)
        #instance.set_shader_input('permTexture', self.texture)
        if self.coord == TexCoord.NormalizedCube or self.coord == TexCoord.SqrtCube:
            mat = self.get_rot_for_face(face)
            mat.transpose_in_place()
            instance.set_shader_input('cube_rot', LMatrix4(mat))
        self.noise_source.update(instance)

class NoiseTarget(ShaderComponent):
    pass

class FloatTarget(NoiseTarget):
    def get_id(self):
        if settings.encode_float:
            return 'enc'
        else:
            return ''

    def fragment_extra(self, code):
        if settings.encode_float:
            self.add_encode_rgba(code)

    def apply_noise(self, code):
        if settings.encode_float:
            code.append('frag_output = EncodeFloatRGBA(value);')
        else:
            code.append('frag_output = vec4(value, 0, 0, 0);')

class GrayTarget(NoiseTarget):
    def get_id(self):
        return 'gray'

    def apply_noise(self, code):
        code.append('frag_output = vec4(value, value, value, 1.0);')
