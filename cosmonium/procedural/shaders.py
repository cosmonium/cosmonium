#
#This file is part of Cosmonium.
#
#Copyright (C) 2018-2022 Laurent Deru.
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


from ..shaders.base import StructuredShader, ShaderProgram
from ..shaders.appearance import ShaderAppearance
from ..shaders.data_source.base import ShaderDataSource, CompositeShaderDataSource
from ..pipeline.shaders import GeneratorVertexShader


class TextureDictionaryShaderDataSource(ShaderDataSource):
    def __init__(self, dictionary):
        ShaderDataSource.__init__(self)
        self.dictionary = dictionary
        self.tiling = dictionary.tiling

    def get_id(self):
        return 'dict' + str(id(self)) + self.tiling.get_id()

    def set_shader(self, shader):
        ShaderDataSource.set_shader(self, shader)
        self.tiling.set_shader(shader)

    def fragment_uniforms(self, code):
        ShaderDataSource.fragment_uniforms(self, code)
        self.tiling.uniforms(code)
        if self.dictionary.texture_array:
            for texture in self.dictionary.texture_arrays.values():
                code.append("uniform sampler2DArray %s;" % texture.input_name)
        else:
            for (name, entry) in self.dictionary.blocks.items():
                for texture in entry.textures:
                    code.append("uniform sampler2D tex_%s_%s;" % (name, texture.category))
        code.append("uniform vec2 detail_factor;")

    def fragment_extra(self, code):
        ShaderDataSource.fragment_extra(self, code)
        self.tiling.extra(code)

    def get_source_for(self, source, param, error=True):
        for (block_id, entry) in self.dictionary.blocks.items():
            for texture in entry.textures:
                if source == '{}_{}'.format(block_id, texture.category):
                    position = "{} * detail_factor".format(param)
                    if self.dictionary.texture_array:
                        tex_id = self.dictionary.get_tex_id_for(block_id, texture.category)
                        dict_name = 'array_%s' % texture.category
                        texture_sample = self.tiling.sample_array('tex_{}'.format(dict_name), position, tex_id)
                        #TODO: There should not be a link like that
                        if self.shader.appearance.resolved:
                            if texture.category == 'normal':
                                return "(%s.xyz * 2 - 1)" % (texture_sample)
                            else:
                                return "%s.xyz" % (texture_sample)
                        else:
                            if texture.category == 'normal':
                                return "(textureLod(tex_%s, vec3(%s, %d), 1000).xyz * 2 - 1)" % (dict_name, position, tex_id)
                            else:
                                return "textureLod(tex_%s, vec3(%s, %d), 1000).xyz" % (dict_name, position, tex_id)
                    else:
                        texture_sample = self.tiling.sample('tex_{}_{}'.format(dict_name, texture.category), position)
                        if texture.category == 'normal':
                            return "(%s.xyz * 2 - 1)" % (texture_sample)
                        else:
                            return "%s.xyz" % (texture_sample)
        for (name, index) in self.dictionary.blocks_index.items():
            if source == name + '_index':
                return (index, self.dictionary.nb_blocks)
        if error: print("Unknown source '%s' requested" % source)
        return ''

class ProceduralMap(ShaderAppearance):
    use_vertex = True
    world_vertex = True
    model_vertex = True

    def __init__(self, textures_control, heightmap, create_normals=False):
        ShaderAppearance.__init__(self)
        self.textures_control = textures_control
        self.heightmap = heightmap
        self.has_surface_texture = True
        self.has_normal_texture = create_normals
        self.normal_texture_tangent_space = True
        #self.textures_control.set_heightmap(self.heightmap)
        self.has_attribute_color = False
        self.has_vertex_color = False
        self.has_material = False

    def get_id(self):
        config = "pm"
        if self.has_normal_texture:
            config += '-n'
        return config

    def fragment_shader(self, code):
        code.append('vec3 surface_normal = %s;' % self.shader.data_source.get_source_for('normal_%s' % self.heightmap.name, 'texcoord0.xy'))
        code.append("float height = %s;" % self.shader.data_source.get_source_for('height_%s' % self.heightmap.name, 'texcoord0.xy'))
        code.append('vec2 uv = texcoord0.xy;')
        code.append('float angle = surface_normal.z;')
        if True:
            #self.textures_control.color_func_call(code)
            #code.append("surface_color = vec4(%s_color, 1.0);" % self.textures_control.name)
            code.append("surface_color = vec4(height, height, height, 1.0);")
        else:
            code += ['surface_color = vec4(surface_normal, 1.0);']
        if self.has_normal_texture:
            code += ['pixel_normal = surface_normal;']

class DetailMap(ShaderAppearance):
    use_vertex = True
    world_vertex = True
    model_vertex = True

    def __init__(self, textures_control, heightmap, create_normals=True):
        ShaderAppearance.__init__(self)
        self.textures_control = textures_control
        self.heightmap = heightmap
        self.create_normals = create_normals
        self.normal_texture_tangent_space = True
        self.resolved = False

    def create_shader_configuration(self, appearance):
        self.textures_control.create_shader_configuration(appearance.texture_source)
        self.has_surface = 'albedo' in appearance.texture_source.texture_categories
        self.has_normal = self.create_normals
        self.has_detail_normal = 'normal' in appearance.texture_source.texture_categories
        self.has_occlusion = 'occlusion' in appearance.texture_source.texture_categories

    def get_id(self):
        name = "dm"
        config = ""
        if self.has_surface:
            config += "u"
        if self.has_occlusion:
            config += "o"
        if self.has_normal:
            config += "n"
        if self.has_detail_normal:
            config += "d"
        if self.resolved:
            config += 'r'
        if config != "":
            return name + '-' + config
        else:
            return name

    def set_shader(self, shader):
        ShaderAppearance.set_shader(self, shader)
        self.textures_control.set_shader(shader)

    def set_resolved(self, resolved):
        self.resolved = resolved

    def vertex_uniforms(self, code):
        code.append("uniform vec4 flat_coord;")

    def vertex_outputs(self, code):
        code.append("out vec2 flat_position;")

    def vertex_shader(self, code):
        code.append("flat_position.x = flat_coord.x + flat_coord.z * texcoord0.x;")
        code.append("flat_position.y = flat_coord.y + flat_coord.w * (1.0 - texcoord0.y);")

    def fragment_uniforms(self, code):
        ShaderAppearance.fragment_uniforms(self, code)
        self.textures_control.fragment_uniforms(code)

    def fragment_inputs(self, code):
        code.append("in vec2 flat_position;")

    def fragment_extra(self, code):
        self.textures_control.fragment_extra(code)

    def fragment_shader_decl(self, code):
        ShaderAppearance.fragment_shader_decl(self, code)
        code.append('vec2 position = flat_position;')

    def fragment_shader(self, code):
        code.append('vec3 surface_normal = %s;' % self.shader.data_source.get_source_for('normal_%s' % self.heightmap.name, 'texcoord0.xy'))
        code.append("float height = %s;" % self.shader.data_source.get_source_for('height_%s' % self.heightmap.name, 'texcoord0.xy'))
        code.append('vec2 uv = texcoord0.xy;')
        code.append('float angle = surface_normal.z;')
        self.textures_control.color_func_call(code)
        if self.has_surface:
            self.textures_control.get_value(code, 'albedo')
            code.append("surface_color = %s_albedo;" % self.textures_control.name)
        if self.has_normal:
            if self.has_detail_normal:
                self.textures_control.get_value(code, 'normal')
                code.append("vec3 n1 = surface_normal + vec3(0, 0, 1);")
                code.append("vec3 n2 = %s_normal.xyz * vec3(-1, -1, 1);" % self.textures_control.name)
                code.append("pixel_normal = n1 * dot(n1, n2) / n1.z - n2;")
            else:
                code.append("pixel_normal = surface_normal;")
        if self.has_occlusion:
            self.textures_control.get_value(code, 'occlusion')
            code.append("surface_occlusion = %s_occlusion.x;" % self.textures_control.name)

class DeferredDetailMapFragmentShader(ShaderProgram):
    def __init__(self, data_source, textures_control, heightmap):
        ShaderProgram.__init__(self, 'fragment')
        self.data_source = data_source
        self.textures_control = textures_control
        self.heightmap = heightmap

    def set_shader(self, shader):
        self.shader = shader
        self.textures_control.set_shader(self)
        #self.heightmap.set_shader(self)

    def create_uniforms(self, code):
        self.data_source.fragment_uniforms(code)
        self.textures_control.fragment_uniforms(code)
        code.append("uniform vec4 flat_coord;")

    def create_inputs(self, code):
        self.data_source.fragment_inputs(code)
        code.append("in vec2 texcoord;")

    def create_outputs(self, code):
        if self.version >= 130:
            code.append("out vec4 frag_output;")

    def create_extra(self, code):
        self.data_source.fragment_extra(code)
        self.textures_control.fragment_extra(code)

    def create_body(self, code):
        self.data_source.fragment_shader_decl(code)
        if self.version < 130:
            code.append('vec4 frag_output;')
        self.data_source.fragment_shader(code)
        code.append("vec2 flat_position;")
        code.append("vec2 texcoord0 = texcoord.xy;")
        code.append("flat_position.x = flat_coord.x + flat_coord.z * texcoord.x;")
        code.append("flat_position.y = flat_coord.y + flat_coord.w * (1.0 - texcoord.y);")
        code.append('vec2 position = flat_position;')
        code.append('vec3 surface_normal = %s;' % self.shader.data_source.get_source_for('normal_%s' % self.heightmap.name, 'texcoord.xy'))
        code.append("float height = %s;" % self.shader.data_source.get_source_for('height_%s' % self.heightmap.name, 'texcoord.xy'))
        code.append('vec2 uv = texcoord.xy;')
        code.append('float angle = surface_normal.z;')
        self.textures_control.color_func_call(code)
        if True or self.has_surface:
            self.textures_control.get_value(code, 'albedo')
            code.append("frag_output = %s_albedo;" % self.textures_control.name)
        if self.version < 130:
            code.append('gl_FragColor = frag_output;')

class FakeAppearance:
    # Workaround class to have a shader appearance for the TextureDictionaryShaderDataSource
    def __init__(self):
        self.resolved = True

class DeferredDetailMapShader(StructuredShader):
    def __init__(self, heightmap, textures_control, texture_source):
        StructuredShader.__init__(self)
        self.heightmap = heightmap
        self.texture_source = texture_source
        self.appearance = FakeAppearance()
        self.data_source = CompositeShaderDataSource()
        self.data_source.set_shader(self)
        self.vertex_shader = GeneratorVertexShader()
        self.fragment_shader = DeferredDetailMapFragmentShader(self.data_source, textures_control, heightmap)
        self.fragment_shader.set_shader(self)

    def get_shader_id(self):
        name = 'detailmap'
        return name

    def update(self, instance, shape, patch, appearance, lod):
        shape.get_data_source().apply(shape, instance)
        shape.get_patch_data_source().apply(patch, instance)
        #instance.set_shader_input("flat_coord", patch.flat_coord)
        self.texture_source.apply(shape, instance)
        self.heightmap.apply(patch, instance)
