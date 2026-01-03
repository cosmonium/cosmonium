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


from panda3d.core import LVector3, LMatrix4, LQuaternion

from ..patchedshapes.patchedshapes import SquarePatchBase
from ..pipeline.shaders import GeneratorVertexShader
from ..shaders.base import StructuredShader, ShaderProgram
from ..shaders.component import ShaderComponent
from ..textures import TexCoord


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


class NoiseFragmentShader(ShaderProgram):
    def __init__(self, coord, noise_source, noise_target):
        ShaderProgram.__init__(self, 'fragment')
        self.coord = coord
        self.noise_source = noise_source
        self.noise_target = noise_target

    def create_uniforms(self, code):
        code.append("uniform vec2 reducedTextureSize;")
        code.append("uniform vec3 noiseOffset;")
        code.append("uniform vec3 noiseScale;")
        code.append("uniform float global_coord_scale;")
        code.append("uniform vec3 global_coord_offset;")
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
        self.noise_source.noise_extra(self, code)
        self.noise_source.noise_func(code)
        self.noise_target.fragment_extra(code)
        self.calc_noise_value(code)

    def calc_noise_value(self, code):
        code.append('float calc_noise_value(vec2 coord) {')
        code.append('vec3 position;')
        if self.coord == TexCoord.Cylindrical:
            code.append('float nx = 2 * pi * (noiseOffset.x + coord.x * noiseScale.x) + pi;')
            code.append('float ny = pi * (noiseOffset.y + coord.y * noiseScale.y);')
            code.append('float cnx = cos(nx);')
            code.append('float snx = sin(nx);')
            code.append('float cny = cos(ny);')
            code.append('float sny = sin(ny);')
            code.append('position.x = cnx * sny;')
            code.append('position.y = snx * sny;')
            code.append('position.z = -cny;')
        elif self.coord == TexCoord.NormalizedCube:
            code.append('vec3 p;')
            code.append('p.x = 2.0 * (noiseOffset.x + coord.x * noiseScale.x) - 1.0;')
            code.append('p.y = 2.0 * (noiseOffset.y + coord.y * noiseScale.y) - 1.0;')
            code.append('p.z = 1.0;')
            code.append('position = cube_rot * normalize(p);')
        elif self.coord == TexCoord.SqrtCube:
            code.append('vec3 p;')
            code.append('p.x = 2.0 * (noiseOffset.x + coord.x * noiseScale.x) - 1.0;')
            code.append('p.y = 2.0 * (noiseOffset.y + coord.y * noiseScale.y) - 1.0;')
            code.append('p.z = 1.0;')
            code.append('vec3 p2 = p * p;')
            code.append("position.x = p.x * sqrt(1.0 - p2.y * 0.5 - p2.z * 0.5 + p2.y * p2.z / 3.0);")
            code.append("position.y = p.y * sqrt(1.0 - p2.z * 0.5 - p2.x * 0.5 + p2.z * p2.x / 3.0);")
            code.append("position.z = p.z * sqrt(1.0 - p2.x * 0.5 - p2.y * 0.5 + p2.x * p2.y / 3.0);")
            code.append('position = cube_rot * position;')
        else:
            code.append('position.x = noiseOffset.x + coord.x * noiseScale.x;')
            code.append('position.y = noiseOffset.y + coord.y * noiseScale.y;')
            code.append('position.z = noiseOffset.z;')
        code.append('position = position * global_coord_scale + global_coord_offset;')
        code.append('float value;')
        self.noise_source.noise_value(code, 'value', 'position')
        code.append('return value * global_scale;')
        code.append('}')

    def create_body(self, code):
        if self.version < 130:
            code.append('vec4 frag_output;')
        code.append('vec2 coord = (gl_FragCoord.xy - vec2(0.5)) / reducedTextureSize;')
        code.append('float value = calc_noise_value(coord);')
        self.noise_target.apply_noise(code)
        if self.version < 130:
            code.append('gl_FragColor = frag_output;')


class NoiseShader(StructuredShader):
    coord_map = {
        TexCoord.Cylindrical: 'cyl',
        TexCoord.Flat: 'flat',
        TexCoord.NormalizedCube: 'cube',
        TexCoord.SqrtCube: 'sqrtcube',
    }

    def __init__(self, size, coord=TexCoord.Cylindrical, noise_source=None, noise_target=None):
        StructuredShader.__init__(self)
        self.reduced_size = (size[0] - 1, size[1] - 1)
        self.coord = coord
        self.noise_source = noise_source
        self.noise_target = noise_target
        self.vertex_shader = GeneratorVertexShader()
        self.fragment_shader = NoiseFragmentShader(self.coord, self.noise_source, self.noise_target)
        # self.texture = loader.loadTexture('permtexture.png')

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
        rotation = SquarePatchBase.rotations[face]
        rotation = LQuaternion(*rotation)
        mat = LMatrix4()
        rotation.extract_to_matrix(mat)
        return mat

    def update(
        self,
        instance,
        face=0,
        offset=LVector3(0, 0, 0),
        scale=LVector3(1, 1, 1),
        global_coord_scale=1.0,
        global_coord_offset=LVector3(0, 0, 0),
        global_scale=1.0,
        lod=None,
    ):
        instance.set_shader_input('reducedTextureSize', self.reduced_size)
        instance.set_shader_input('noiseOffset', offset)
        instance.set_shader_input('noiseScale', scale)
        instance.set_shader_input('global_coord_scale', global_coord_scale)
        instance.set_shader_input('global_coord_offset', global_coord_offset)
        instance.set_shader_input('global_scale', global_scale)
        # instance.set_shader_input('permTexture', self.texture)
        if self.coord == TexCoord.NormalizedCube or self.coord == TexCoord.SqrtCube:
            mat = self.get_rot_for_face(face)
            instance.set_shader_input('cube_rot', mat)
        self.noise_source.update(instance)


class NoiseTarget(ShaderComponent):
    pass


class FloatTarget(NoiseTarget):
    def get_id(self):
        return ''

    def apply_noise(self, code):
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
