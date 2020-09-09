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
from ..parameters import ParametersGroup, AutoUserParameter
from .. import settings

from .generator import GeneratorVertexShader

class NoiseSource(object):
    last_id = 0
    last_tmp = 0
    def __init__(self, name, prefix, ranges={}):
        NoiseSource.last_id += 1
        self.num_id = NoiseSource.last_id
        self.str_id = prefix + '_' + str(self.num_id)
        if name is None:
            name = self.str_id
        self.name = name
        self.ranges = ranges

    def get_id(self):
        return ''

    def get_name(self):
        return self.name

    def create_tmp(self, code, tmp_type='float'):
        NoiseSource.last_tmp += 1
        tmp = "tmp_" + str(self.last_tmp)
        code.append("    %s %s;" % (tmp_type, tmp))
        return tmp

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

    def get_user_parameters(self):
        return []

class BasicNoiseSource(NoiseSource):
    def __init__(self, noise, name, prefix, ranges={}):
        NoiseSource.__init__(self, name, prefix, ranges)
        self.noise = noise

    def noise_uniforms(self, code):
        self.noise.noise_uniforms(code)

    def noise_extra(self, program, code):
        self.noise.noise_extra(program, code)

    def noise_func(self, code):
        self.noise.noise_func(code)

    def update(self, instance):
        self.noise.update(instance)

    def get_user_parameters(self):
        return self.noise.get_user_parameters()

class NoiseConst(NoiseSource):
    def __init__(self, value, dynamic=False, name=None, ranges={}):
        NoiseSource.__init__(self, name, 'const', ranges)
        self.value = value
        self.dynamic = dynamic

    def get_id(self):
        if self.dynamic:
            return 'const'
        else:
            return '%g' % self.value

    def noise_uniforms(self, code):
        if self.dynamic:
            code.append("uniform float %s;" % self.str_id)

    def noise_value(self, code, value, point):
        if self.dynamic:
            code.append('        %s  = %s;' % (value, self.str_id))
        else:
            code.append('        %s  = %g;' % (value, self.value))

    def update(self, instance):
        if self.dynamic:
            instance.set_shader_input('%s' % self.str_id, self.value)

    def get_user_parameters(self):
        if not self.dynamic: return []
        group = ParametersGroup(self.name)
        group.add_parameters(AutoUserParameter('value', 'value', self, param_type=AutoUserParameter.TYPE_FLOAT, value_range=self.ranges.get('value')))
        return [group]

class NoiseCoord(NoiseSource):
    def __init__(self, coord, name=None):
        NoiseSource.__init__(self, name, 'coord')
        self.coord = coord

    def get_id(self):
        return '%s' % self.coord

    def noise_value(self, code, value, point):
        code.append('        %s  = %s.%s;' % (value, point, self.coord))

class GpuNoiseLibPerlin3D(NoiseSource):
    def __init__(self, name=None):
        NoiseSource.__init__(self, name, 'gnl-perlin3d')

    def get_id(self):
        return 'gnl-perlin3d'

    def noise_extra(self, program, code):
        program.include(code, 'gnl-FAST32_hash', defaultDirContext.find_shader("gpu-noise-lib/FAST32_hash.glsl"))
        program.include(code, 'gnl-Interpolation', defaultDirContext.find_shader("gpu-noise-lib/Interpolation.glsl"))
        program.include(code, 'gnl-Noise', defaultDirContext.find_shader("gpu-noise-lib/Perlin3D.glsl"))

    def noise_value(self, code, value, point):
        code.append('        %s  = Perlin3D(%s);' % (value, point))

class GpuNoiseLibCellular3D(NoiseSource):
    def __init__(self, name=None):
        NoiseSource.__init__(self, name, 'gnl-cell3d')

    def get_id(self):
        return 'gnl-cell3d'

    def noise_extra(self, program, code):
        program.include(code, 'gnl-FAST32_hash', defaultDirContext.find_shader("gpu-noise-lib/FAST32_hash.glsl"))
        program.include(code, 'gnl-Cellular', defaultDirContext.find_shader("gpu-noise-lib/Cellular.glsl"))

    def noise_value(self, code, value, point):
        code.append('        %s  = sqrt(Cellular3D(%s));' % (value, point))

class GpuNoiseLibPolkaDot3D(NoiseSource):
    def __init__(self, name=None):
        NoiseSource.__init__(self, name, 'gnl-polkadot3d')

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
    def __init__(self, name=None):
        NoiseSource.__init__(self, name, 'stegu-perlin3d')

    def get_id(self):
        return 'stegu-perlin3d'

    def noise_extra(self, program, code):
        program.include(code, 'stegu-common', defaultDirContext.find_shader("stegu/common.glsl"))
        program.include(code, 'stegu-snoise', defaultDirContext.find_shader("stegu/noise3D.glsl"))

    def noise_value(self, code, value, point):
        code.append('        %s  = snoise(%s);' % (value, point))

class SteGuCellular3D(NoiseSource):
    def __init__(self, fast, name=None, prefix='stegu-cellular3d'):
        NoiseSource.__init__(self, name, prefix)
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
    def __init__(self, fast, name=None):
        SteGuCellular3D.__init__(self, fast, name, 'stegu-cellular3d-diff')

    def get_id(self):
        return SteGuCellular3D.get_id(self) + '-diff'

    def noise_value(self, code, value, point):
        if self.fast:
            code.append('        vec2 F = cellular2x2x2(%s);' % (point))
        else:
            code.append('        vec2 F = cellular(%s);' % (point))
        code.append('        %s  = F.y - F.x;' % (value))

class QuilezPerlin3D(NoiseSource):
    def __init__(self, name=None):
        NoiseSource.__init__(self, name, 'quilez-perlin3d')

    def get_id(self):
        return 'quilez-perlin3d'

    def noise_extra(self, program, code):
        program.include(code, 'quilez-noise', defaultDirContext.find_shader("quilez/GradientNoise3D.glsl"))

    def noise_value(self, code, value, point):
        code.append('        %s  = noise(%s);' % (value, point))

class QuilezGradientNoise3D(NoiseSource):
    def __init__(self, name=None):
        NoiseSource.__init__(self, name, 'quilez-gradientnoise3d')

    def get_id(self):
        return 'quilez-gradientnoise3d'

    def noise_extra(self, program, code):
        program.include(code, 'quilez-noise', defaultDirContext.find_shader("quilez/GradientNoise.glsl"))

    def noise_value(self, code, value, point):
        code.append('        %s  = noise(%s);' % (value, point))

class SinCosNoise(NoiseSource):
    def __init__(self, name=None):
        NoiseSource.__init__(self, name, 'sincos')

    def get_id(self):
        return 'sincos'

    def noise_value(self, code, value, point):
        code.append('        {')
        code.append('        vec3 tmp_sincos = %s;' % point)
        code.append('        %s = sin(tmp_sincos.y) + cos(tmp_sincos.x);' % value)
        code.append('        }')

class AbsNoise(BasicNoiseSource):
    def __init__(self, noise, name=None):
        BasicNoiseSource.__init__(self, noise, name, 'abs')

    def get_id(self):
        return 'abs-' + self.noise.get_id()

    def noise_value(self, code, value, point):
        tmp = self.create_tmp(code)
        self.noise.noise_value(code, tmp, point)
        code.append('          %s = abs(%s);' % (value, tmp))

class NegNoise(BasicNoiseSource):
    def __init__(self, noise, name=None):
        BasicNoiseSource.__init__(self, noise, name, 'neg')

    def get_id(self):
        return 'neg-' + self.noise.get_id()

    def noise_value(self, code, value, point):
        tmp = self.create_tmp(code)
        self.noise.noise_value(code, tmp, point)
        code.append('          %s = -(%s);' % (value, tmp))

class RidgedNoise(BasicNoiseSource):
    def __init__(self, noise, offset=0.33, shift=True, name=None):
        BasicNoiseSource.__init__(self, noise, name, 'ridged')
        self.offset = offset
        self.shift = shift

    def get_id(self):
        return 'ridged-' + self.noise.get_id()

    def noise_value(self, code, value, point):
        code.append('        {')
        code.append('          float tmp_ridged;')
        self.noise.noise_value(code, 'tmp_ridged', point)
        if self.shift:
            code.append('        %s  = (1.0 - abs(tmp_ridged) - %g) * 2.0 - 1.0;' % (value, self.offset))
        else:
            code.append('        %s  = (1.0 - abs(tmp_ridged) - %g);' % (value, self.offset))
        code.append('        }')

class SquareNoise(BasicNoiseSource):
    def __init__(self, noise, name=None):
        BasicNoiseSource.__init__(self, noise, name, 'square')

    def get_id(self):
        return 'square-' + self.noise.get_id()

    def noise_value(self, code, value, point):
        code.append('        {')
        code.append('          float tmp_square;')
        self.noise.noise_value(code, 'tmp_square', point)
        code.append('        %s = tmp_square * tmp_square;' % value)
        code.append('        }')

class CubeNoise(BasicNoiseSource):
    def __init__(self, noise, name=None):
        BasicNoiseSource.__init__(self, noise, name, 'cube')

    def get_id(self):
        return 'cube-' + self.noise.get_id()

    def noise_value(self, code, value, point):
        code.append('        {')
        code.append('          float tmp_cube;')
        self.noise.noise_value(code, 'tmp_cube', point)
        code.append('        %s = tmp_cube * tmp_cube * tmp_cube;' % value)
        code.append('        }')

class PositionMap(BasicNoiseSource):
    def __init__(self, noise, offset=0.0, scale=1.0, dynamic=True, name=None):
        BasicNoiseSource.__init__(self, noise, name, 'pos')
        self.offset = offset
        self.scale = scale
        self.dynamic = dynamic

    def get_id(self):
        if self.dynamic:
            return ('pos-%d-' % self.num_id) + self.noise.get_id()
        else:
            return ('pos-%g-%g-' % (self.offset, self.scale)) + self.noise.get_id()

    def noise_uniforms(self, code):
        BasicNoiseSource.noise_uniforms(self, code)
        if self.dynamic:
            code.append("uniform vec2 %s_params;" % self.str_id)

    def noise_value(self, code, value, point):
        if self.dynamic:
            self.noise.noise_value(code, value, '(%s * %s_params.x + %s_params.y)' % (point, self.str_id, self.str_id))
        else:
            self.noise.noise_value(code, value, '(%s * %g + %g)' % (point, self.scale, self.offset))

    def update(self, instance):
        BasicNoiseSource.update(self, instance)
        if self.dynamic:
            instance.set_shader_input('%s_params' % self.str_id, (self.scale, self.offset))

    def get_user_parameters(self):
        parameters = BasicNoiseSource.get_user_parameters(self)
        if isinstance(parameters, ParametersGroup):
            group = parameters
        else:
            group = ParametersGroup(self.noise.name)
            group.add_parameters(parameters)
        group.add_parameters(AutoUserParameter('Scale', 'scale', self, param_type=AutoUserParameter.TYPE_FLOAT),
                             AutoUserParameter('Offset', 'offset', self, param_type=AutoUserParameter.TYPE_FLOAT))
        return [group]

class NoiseAdd(NoiseSource):
    def __init__(self, noises, name=None):
        NoiseSource.__init__(self, name, 'add')
        self.noises = noises

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
        code.append('float noise_add_%d(vec3 point)' % self.num_id)
        code.append('{')
        for (i, noise) in enumerate(self.noises):
            noise.noise_value(code, 'float value_%d' % i, 'point')
        add = ' + '.join(map(lambda i: 'value_%d' % i, range(len(self.noises))))
        code.append('  return %s;' % add)
        code.append('}')

    def noise_value(self, code, value, point):
        code.append('%s = noise_add_%d(%s);' % (value, self.num_id, point))

    def update(self, instance):
        for noise in self.noises:
            noise.update(instance)

    def get_user_parameters(self):
        parameters = []
        for noise in self.noises:
            parameters += noise.get_user_parameters()
        return parameters

class NoiseSub(NoiseSource):
    def __init__(self, noise_a, noise_b, name=None):
        NoiseSource.__init__(self, name, 'sub')
        self.noise_a = noise_a
        self.noise_b = noise_b

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
        code.append('float noise_sub_%d(vec3 point)' % self.num_id)
        code.append('{')
        code.append('  float value_a;')
        code.append('  float value_b;')
        self.noise_a.noise_value(code, 'value_a', 'point')
        self.noise_b.noise_value(code, 'value_b', 'point')
        code.append('  return value_a - value_b;')
        code.append('}')

    def noise_value(self, code, value, point):
        code.append('%s = noise_sub_%d(%s);' % (value, self.num_id, point))

    def update(self, instance):
        self.noise_a.update(instance)
        self.noise_b.update(instance)

    def get_user_parameters(self):
        return self.noise_a.get_user_parameters() + self.noise_b.get_user_parameters()

class NoiseMul(NoiseSource):
    def __init__(self, noises, name=None):
        NoiseSource.__init__(self, name, 'mul')
        self.noises = noises

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
        code.append('float noise_mul_%d(vec3 point)' % self.num_id)
        code.append('{')
        for (i, noise) in enumerate(self.noises):
            noise.noise_value(code, 'float value_%d' % i, 'point')
        mul = ' * '.join(map(lambda i: 'value_%d' % i, range(len(self.noises))))
        code.append('  return %s;' % mul)
        code.append('}')

    def noise_value(self, code, value, point):
        code.append('%s = noise_mul_%d(%s);' % (value, self.num_id, point))

    def update(self, instance):
        for noise in self.noises:
            noise.update(instance)

    def get_user_parameters(self):
        parameters = []
        for noise in self.noises:
            parameters += noise.get_user_parameters()
        return parameters

class NoisePow(NoiseSource):
    def __init__(self, noise_a, noise_b, name=None):
        NoiseSource.__init__(self, name, 'mul')
        self.noise_a = noise_a
        self.noise_b = noise_b

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
        code.append('float noise_pow_%d(vec3 point)' % self.num_id)
        code.append('{')
        code.append('  float value_a;')
        code.append('  float value_b;')
        self.noise_a.noise_value(code, 'value_a', 'point')
        self.noise_b.noise_value(code, 'value_b', 'point')
        code.append('  return pow(value_a, value_b);')
        code.append('}')

    def noise_value(self, code, value, point):
        code.append('%s = noise_pow_%d(%s);' % (value, self.num_id, point))

    def update(self, instance):
        self.noise_a.update(instance)
        self.noise_b.update(instance)

    def get_user_parameters(self):
        return self.noise_a.get_user_parameters() + self.noise_b.get_user_parameters()

class NoiseExp(BasicNoiseSource):
    def __init__(self, noise, name=None):
        BasicNoiseSource.__init__(self, noise, name, 'exp')

    def get_id(self):
        return 'exp-' + self.noise.get_id()

    def noise_value(self, code, value, point):
        tmp = self.create_tmp(code)
        self.noise.noise_value(code, tmp, point)
        code.append('      %s = exp(%s);' % (value, tmp))

class NoiseThreshold(NoiseSource):
    def __init__(self, noise_a, noise_b, name=None):
        NoiseSource.__init__(self, name, 'threshold')
        self.noise_a = noise_a
        self.noise_b = noise_b

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
        code.append('float noise_threshold_%d(vec3 point)' % self.num_id)
        code.append('{')
        code.append('  float value_a;')
        code.append('  float value_b;')
        self.noise_a.noise_value(code, 'value_a', 'point')
        self.noise_b.noise_value(code, 'value_b', 'point')
        code.append('  return max((value_a - value_b), 0.0);')
        code.append('}')

    def noise_value(self, code, value, point):
        code.append('%s = noise_threshold_%d(%s);' % (value, self.num_id, point))

    def update(self, instance):
        self.noise_a.update(instance)
        self.noise_b.update(instance)

    def get_user_parameters(self):
        return self.noise_a.get_user_parameters() + self.noise_b.get_user_parameters()

class NoiseClamp(NoiseSource):
    def __init__(self, noise, min_value, max_value, dynamic=False, name=None, ranges={}):
        NoiseSource.__init__(self, name, 'clamp', ranges)
        self.noise = noise
        self.min_value = min_value
        self.max_value = max_value
        self.dynamic = dynamic

    def get_id(self):
        if self.dynamic:
            return 'clamp-' + self.noise.get_id()
        else:
            return ('clamp-%g-%g-' % (self.min_value, self.max_value)) + self.noise.get_id()

    def noise_uniforms(self, code):
        self.noise.noise_uniforms(code)
        if self.dynamic:
            code.append("uniform float %s_min;" % self.str_id)
            code.append("uniform float %s_max;" % self.str_id)

    def noise_extra(self, program, code):
        self.noise.noise_extra(program, code)

    def noise_func(self, code):
        self.noise.noise_func(code)
        code.append('float noise_clamp_%d(vec3 point)' % self.num_id)
        code.append('{')
        code.append('  float value;')
        self.noise.noise_value(code, 'value', 'point')
        if self.dynamic:
            code.append('  return clamp(value, %s_min, %s_max);' % (self.str_id, self.str_id))
        else:
            code.append('  return clamp(value, %g, %g);' % (self.min_value, self.max_value))
        code.append('}')

    def noise_value(self, code, value, point):
        code.append('%s = noise_clamp_%d(%s);' % (value, self.num_id, point))

    def update(self, instance):
        self.noise.update(instance)
        if self.dynamic:
            instance.set_shader_input('%s_min' % self.str_id, self.min_value)
            instance.set_shader_input('%s_max' % self.str_id, self.max_value)

    def get_user_parameters(self):
        if not self.dynamic: return []
        group = ParametersGroup(self.name)
        group.add_parameters(AutoUserParameter('Min', 'min_value', self, param_type=AutoUserParameter.TYPE_FLOAT, value_range=self.ranges.get('min')))
        group.add_parameters(AutoUserParameter('Max', 'max_value', self, param_type=AutoUserParameter.TYPE_FLOAT, value_range=self.ranges.get('max')))
        return [group]

class NoiseMin(NoiseSource):
    def __init__(self, noise_a, noise_b, name=None):
        NoiseSource.__init__(self, name, 'min')
        self.noise_a = noise_a
        self.noise_b = noise_b

    def get_id(self):
        return self.noise_a.get_id() + "-min-" + self.noise_b.get_id()

    def noise_uniforms(self, code):
        self.noise_a.noise_uniforms(code)
        self.noise_b.noise_uniforms(code)

    def noise_extra(self, program, code):
        self.noise_a.noise_extra(program, code)
        self.noise_b.noise_extra(program, code)

    def noise_func(self, code):
        self.noise_a.noise_func(code)
        self.noise_b.noise_func(code)
        code.append('float noise_min_%d(vec3 point)' % self.num_id)
        code.append('{')
        code.append('  float value_a;')
        code.append('  float value_b;')
        self.noise_a.noise_value(code, 'value_a', 'point')
        self.noise_b.noise_value(code, 'value_b', 'point')
        code.append('  return min(value_a, value_b);')
        code.append('}')

    def noise_value(self, code, value, point):
        code.append('%s = noise_min_%d(%s);' % (value, self.num_id, point))

    def update(self, instance):
        self.noise_a.update(instance)
        self.noise_b.update(instance)

    def get_user_parameters(self):
        return self.noise_a.get_user_parameters() + self.noise_b.get_user_parameters()

class NoiseMax(NoiseSource):
    def __init__(self, noise_a, noise_b, name=None):
        NoiseSource.__init__(self, name, 'max')
        self.noise_a = noise_a
        self.noise_b = noise_b

    def get_id(self):
        return self.noise_a.get_id() + "-max-" + self.noise_b.get_id()

    def noise_uniforms(self, code):
        self.noise_a.noise_uniforms(code)
        self.noise_b.noise_uniforms(code)

    def noise_extra(self, program, code):
        self.noise_a.noise_extra(program, code)
        self.noise_b.noise_extra(program, code)

    def noise_func(self, code):
        self.noise_a.noise_func(code)
        self.noise_b.noise_func(code)
        code.append('float noise_max_%d(vec3 point)' % self.num_id)
        code.append('{')
        code.append('  float value_a;')
        code.append('  float value_b;')
        self.noise_a.noise_value(code, 'value_a', 'point')
        self.noise_b.noise_value(code, 'value_b', 'point')
        code.append('  return max(value_a, value_b);')
        code.append('}')

    def noise_value(self, code, value, point):
        code.append('%s = noise_max_%d(%s);' % (value, self.num_id, point))

    def update(self, instance):
        self.noise_a.update(instance)
        self.noise_b.update(instance)

    def get_user_parameters(self):
        return self.noise_a.get_user_parameters() + self.noise_b.get_user_parameters()

class NoiseMap(BasicNoiseSource):
    def __init__(self, noise, min_value=0.0, max_value=1.0, src_min_value=-1.0, src_max_value=1.0, name=None):
        BasicNoiseSource.__init__(self, noise, name, 'map')
        self.min_value = min_value
        self.max_value = max_value
        self.src_min_value = src_min_value
        self.src_max_value = src_max_value
        self.range = self.max_value - self.min_value
        self.src_range = self.src_max_value - self.src_min_value
        self.range_factor = self.range / self.src_range

    def get_id(self):
        return 'map-%g-%g-' % (self.min_value, self.max_value) + self.noise.get_id()

    def noise_func(self, code):
        self.noise.noise_func(code)
        code.append('float noise_map_%d(vec3 point)' % self.num_id)
        code.append('{')
        code.append('  float value;')
        self.noise.noise_value(code, 'value', 'point')
        code.append('  return clamp((value - %g) * %g + %g, %f, %f);' % (self.src_min_value, self.range_factor, self.min_value, self.min_value, self.max_value))
        code.append('}')

    def noise_value(self, code, value, point):
        code.append('%s = noise_map_%d(%s);' % (value, self.num_id, point))

class Noise1D(BasicNoiseSource):
    def __init__(self, noise, axis, name=None):
        BasicNoiseSource.__init__(self, noise, name, 'axis')
        self.axis = axis

    def get_id(self):
        return ('axis-%s-' % (self.axis)) + self.noise.get_id()

    def noise_func(self, code):
        BasicNoiseSource.noise_func(self, code)
        code.append('float noise_axis_%d(vec3 point)' % self.num_id)
        code.append('{')
        code.append('  float value;')
        code.append('  vec3 point_1d = vec3(0);')
        code.append('  point_1d.%s = point.%s;' % (self.axis, self.axis))
        self.noise.noise_value(code, 'value', 'point_1d')
        code.append('  return value;')
        code.append('}')

    def noise_value(self, code, value, point):
        code.append('%s = noise_axis_%d(%s);' % (value, self.num_id, point))

class FbmNoise(BasicNoiseSource):
    def __init__(self, noise, octaves=8, frequency=1.0, lacunarity=2.0, geometric=True, h=0.25, gain=0.5, name=None, ranges={}):
        BasicNoiseSource.__init__(self, noise, name, 'fbm', ranges)
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
        return self.str_id + geom + '-' + self.noise.get_id()

    def noise_uniforms(self, code):
        BasicNoiseSource.noise_uniforms(self, code)
        code += ["uniform float %s_octaves;" % self.str_id,
                 "uniform float %s_frequency;" % self.str_id,
                 "uniform float %s_lacunarity;" % self.str_id,
                 "uniform float %s_amplitude;" % self.str_id
                 ]
        if self.geometric:
            code.append("uniform float %s_gain;" % self.str_id)
        else:
            code.append("uniform float %s_h;" % self.str_id)

    def noise_func(self, code):
        self.noise.noise_func(code)
        code.append('float Fbm_%s(vec3 point)' % self.str_id)
        code.append('{')
        code.append("float frequency = %s_frequency;" % self.str_id)
        if self.geometric:
            code.append("float gain = %s_gain;" % self.str_id)
        else:
            code.append("float gain = pow(%s_lacunarity, -%s_h);" % (self.str_id, self.str_id))
        code.append('    float result = 0.0;')
        code.append('    float amplitude = 1.0;')
        code.append('    float max_value = 0.0;')
        code.append('    for (int i = 0; i < %s_octaves; ++i)' % self.str_id)
        code.append('    {')
        code.append('        float value;')
        self.noise.noise_value(code, 'value', 'point * frequency')
        code.append('        result += value * amplitude;')
        code.append('        max_value += amplitude;')
        code.append('        amplitude *= gain;')
        code.append('        frequency *= %s_lacunarity;' % self.str_id)
        code.append('    }')
        code.append('    return result / max_value;')
        code.append('}')

    def noise_value(self, code, value, point):
        code.append('%s = Fbm_%s(%s);' % (value, self.str_id, point))

    def update(self, instance):
        self.noise.update(instance)
        instance.set_shader_input('%s_octaves' % self.str_id, self.octaves)
        instance.set_shader_input('%s_frequency' % self.str_id, self.frequency)
        instance.set_shader_input('%s_lacunarity' % self.str_id, self.lacunarity)
        if self.geometric:
            instance.set_shader_input('%s_gain' % self.str_id, self.gain)
        else:
            instance.set_shader_input('%s_h' % self.str_id, self.h)

    def get_user_parameters(self):
        group = ParametersGroup(self.name,
                                AutoUserParameter('Octaves', 'octaves', self, AutoUserParameter.TYPE_INT, value_range=self.ranges.get('octaves')),
                                AutoUserParameter('Frequency', 'frequency', self, AutoUserParameter.TYPE_FLOAT, value_range=self.ranges.get('frequency')),
                                AutoUserParameter('Lacunarity', 'lacunarity', self, AutoUserParameter.TYPE_FLOAT, value_range=self.ranges.get('lacunarity')),
                                AutoUserParameter('Gain', 'gain', self, AutoUserParameter.TYPE_FLOAT, value_range=self.ranges.get('gain')),
                                )
        group.add_parameters(self.noise.get_user_parameters())
        return [group]

class SpiralNoise(BasicNoiseSource):
    def __init__(self, noise, octaves=8, frequency=1.0, lacunarity=2.0, gain=0.5, nudge=0.5, name=None, ranges={}):
        BasicNoiseSource.__init__(self, noise, name, 'spiral', ranges)
        self.octaves = octaves
        self.frequency = frequency
        self.lacunarity = lacunarity
        self.gain = gain
        self.nudge = nudge

    def get_id(self):
        return self.str_id + '-' + self.noise.get_id()

    def noise_uniforms(self, code):
        self.noise.noise_uniforms(code)
        code += ["uniform float %s_octaves;" % self.str_id,
                 "uniform float %s_frequency;" % self.str_id,
                 "uniform float %s_lacunarity;" % self.str_id,
                 "uniform float %s_amplitude;" % self.str_id,
                 "uniform float %s_gain;" % self.str_id,
                 "uniform float %s_nudge;" % self.str_id,
                 ]

    def noise_func(self, code):
        self.noise.noise_func(code)
        code.append('float Spiral_%s(vec3 point)' % self.str_id)
        code.append('{')
        code.append("    float nudge = %s_nudge;" % self.str_id)
        code.append("    float normalizer = 1.0 / sqrt(1.0 + nudge*nudge);")
        code.append("    float frequency = %s_frequency;" % self.str_id)
        code.append("    float lacunarity = %s_lacunarity;" % self.str_id)
        code.append("    float gain = %s_gain;" % self.str_id)
        code.append('    float result = 0.0;')
        code.append('    float amplitude = 1.0;')
        code.append('    float max_value = 0.0;')
        code.append('    for (int i = 0; i < %s_octaves; ++i)' % self.str_id)
        code.append('    {')
        code.append('        float value;')
        self.noise.noise_value(code, 'value', 'point * frequency')
        code.append('        result += value * amplitude;')
        code.append('        max_value += amplitude;')
        code.append('        amplitude *= gain;')
        code.append('        frequency *= lacunarity;')
        code.append('        point.xy += vec2(point.y, -point.x) * nudge;')
        code.append('        point.xy *= normalizer;')
        code.append('        point.xz += vec2(point.z, -point.x) * nudge;')
        code.append('        point.xz *= normalizer;')
        code.append('    }')
        code.append('    return result / max_value;')
        code.append('}')

    def noise_value(self, code, value, point):
        code.append('%s = Spiral_%s(%s);' % (value, self.str_id, point))

    def update(self, instance):
        self.noise.update(instance)
        instance.set_shader_input('%s_octaves' % self.str_id, self.octaves)
        instance.set_shader_input('%s_frequency' % self.str_id, self.frequency)
        instance.set_shader_input('%s_lacunarity' % self.str_id, self.lacunarity)
        instance.set_shader_input('%s_gain' % self.str_id, self.gain)
        instance.set_shader_input('%s_nudge' % self.str_id, self.nudge)

    def get_user_parameters(self):
        group = ParametersGroup(self.name,
                                AutoUserParameter('Octaves', 'octaves', self, AutoUserParameter.TYPE_INT, value_range=self.ranges.get('octaves')),
                                AutoUserParameter('Frequency', 'frequency', self, AutoUserParameter.TYPE_FLOAT, value_range=self.ranges.get('frequency')),
                                AutoUserParameter('Lacunarity', 'lacunarity', self, AutoUserParameter.TYPE_FLOAT, value_range=self.ranges.get('lacunarity')),
                                AutoUserParameter('Gain', 'gain', self, AutoUserParameter.TYPE_FLOAT, value_range=self.ranges.get('gain')),
                                AutoUserParameter('Nudge', 'nudge', self, AutoUserParameter.TYPE_FLOAT, value_range=self.ranges.get('nudge')),
                  )
        group.add_parameters(self.noise.get_user_parameters())
        return [group]

class NoiseWarp(NoiseSource):
    def __init__(self, noise_main, noise_warp, scale=4.0, name=None, ranges={}):
        NoiseSource.__init__(self, name, 'warp', ranges)
        self.noise_main = noise_main
        self.noise_warp = noise_warp
        self.scale = scale

    def get_id(self):
        return self.noise_main.get_id() + "-warp-" + self.noise_warp.get_id()

    def noise_uniforms(self, code):
        self.noise_main.noise_uniforms(code)
        self.noise_warp.noise_uniforms(code)
        code += ["uniform float %s_scale;" % self.str_id]

    def noise_extra(self, program, code):
        self.noise_main.noise_extra(program, code)
        self.noise_warp.noise_extra(program, code)

    def noise_func(self, code):
        self.noise_main.noise_func(code)
        self.noise_warp.noise_func(code)
        code.append('float noise_warp_%d(vec3 point)' % self.num_id)
        code.append('{')
        code.append('  vec3 warped_point;')
        code.append('  float value;')
        self.noise_warp.noise_value(code, 'warped_point.x', 'point')
        self.noise_warp.noise_value(code, 'warped_point.y', 'point + vec3(1, 2, 3)')
        self.noise_warp.noise_value(code, 'warped_point.z', 'point + vec3(4, 3, 2)')
        self.noise_main.noise_value(code, 'value', 'point + %s_scale * warped_point' % self.str_id)
        code.append('  return value;')
        code.append('}')

    def noise_value(self, code, value, point):
        code.append('%s = noise_warp_%d(%s);' % (value, self.num_id, point))

    def update(self, instance):
        self.noise_main.update(instance)
        self.noise_warp.update(instance)
        instance.set_shader_input('%s_scale' % self.str_id, self.scale)

    def get_user_parameters(self):
        group = ParametersGroup(self.name,
                                AutoUserParameter('scale', 'scale', self, AutoUserParameter.TYPE_FLOAT, value_range=self.ranges.get('scale')),
                                )
        group.add_parameters(self.noise_main.get_user_parameters())
        group.add_parameters(self.noise_wrap.get_user_parameters())
        return [group]

class NoiseRotate(NoiseSource):
    def __init__(self, noise_main, noise_angle, axis, name=None):
        NoiseSource.__init__(self, name, 'rot' + axis)
        self.noise_main = noise_main
        self.noise_angle = noise_angle
        self.axis = axis

    def get_id(self):
        return self.noise_main.get_id() + "-rot" + self.axis + "-" + self.noise_angle.get_id()

    def noise_uniforms(self, code):
        self.noise_main.noise_uniforms(code)
        self.noise_angle.noise_uniforms(code)

    def noise_extra(self, program, code):
        self.noise_main.noise_extra(program, code)
        self.noise_angle.noise_extra(program, code)

    def noise_func(self, code):
        self.noise_main.noise_func(code)
        self.noise_angle.noise_func(code)
        code.append('float noise_rot%s_%d(vec3 point)' % (self.axis, self.num_id))
        code.append('{')
        code.append('  float value;')
        code.append('  float theta;')
        self.noise_angle.noise_value(code, 'theta', 'point')
        code.append('  float cos_theta = cos(theta);')
        code.append('  float sin_theta = sin(theta);')
        if self.axis == 'x':
            code.append('  mat3 rot = mat3(1.0, 0.0,       0.0,')
            code.append('                  0.0, cos_theta, -sin_theta,')
            code.append('                  0.0, sin_theta, cos_theta);')
        elif self.axis == 'y':
            code.append('  mat3 rot = mat3(cos_theta,  0.0, sin_theta,')
            code.append('                  0.0,        1.0, 0.0,')
            code.append('                  -sin_theta, 0.0, cos_theta);')
        else:
            code.append('  mat3 rot = mat3(cos_theta, -sin_theta, 0.0,')
            code.append('                  sin_theta, cos_theta,  0.0,')
            code.append('                  0.0,       0.0,        1.0);')
        self.noise_main.noise_value(code, 'value', 'rot * point')
        code.append('  return value;')
        code.append('}')

    def noise_value(self, code, value, point):
        code.append('%s = noise_rot%s_%d(%s);' % (value, self.axis, self.num_id, point))

    def update(self, instance):
        self.noise_main.update(instance)
        self.noise_angle.update(instance)

    def get_user_parameters(self):
        group = ParametersGroup(self.name)
        group.add_parameters(self.noise_main.get_user_parameters())
        group.add_parameters(self.noise_angle.get_user_parameters())
        return [group]

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
            code.append('float ny = pi * (noiseOffset.y + coord.y * noiseScale.y);')
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
            code.append('p.y = 2.0 * (noiseOffset.y + coord.y * noiseScale.y) - 1.0;')
            code.append('p.z = 1.0;')
            code.append('position = normalize(cube_rot * p);')
        elif self.coord == TexCoord.SqrtCube:
            code.append('vec3 p;')
            code.append('p.x = 2.0 * (noiseOffset.x + coord.x * noiseScale.x) - 1.0;')
            code.append('p.y = 2.0 * (noiseOffset.y + coord.y * noiseScale.y) - 1.0;')
            code.append('p.z = 1.0;')
            code.append('p = cube_rot * p;')
            code.append('vec3 p2 = p * p;')
            code.append("position.x = p.x * sqrt(1.0 - p2.y * 0.5 - p2.z * 0.5 + p2.y * p2.z / 3.0);")
            code.append("position.y = p.y * sqrt(1.0 - p2.z * 0.5 - p2.x * 0.5 + p2.z * p2.x / 3.0);")
            code.append("position.z = p.z * sqrt(1.0 - p2.x * 0.5 - p2.y * 0.5 + p2.x * p2.y / 3.0);")
        else:
            code.append('position.x = noiseOffset.x + coord.x * noiseScale.x;')
            code.append('position.y = noiseOffset.y + coord.y * noiseScale.y;')
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
        self.vertex_shader = GeneratorVertexShader()
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

class AlphaTarget(NoiseTarget):
    def get_id(self):
        return 'alpha'

    def apply_noise(self, code):
        code.append('frag_output = vec4(1.0, 1.0, 1.0, value);')
