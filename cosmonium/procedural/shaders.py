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


from ..shaders import ShaderDataSource, ShaderAppearance, StructuredShader, ShaderProgram, CompositeShaderDataSource
from .generator import GeneratorVertexShader

class TextureTiling:
    def __init__(self):
        self.shader = None

    def set_shader(self, shader):
        self.shader = shader

    def uniforms(self, code):
        pass

    def extra(self, code):
        pass

    def tile_texture(self, texture, coord):
        pass

    def tile_texture_array(self, texture, coord, page):
        pass

class SimpleTextureTiling(TextureTiling):
    def tile_texture(self, texture, coord):
        return 'texture2D({}, {})'.format(texture, coord)

    def tile_texture_array(self, texture, coord, page):
        return 'texture2D({}, vec3({}, {}))'.format(texture, coord, page)

class HashTextureTiling(TextureTiling):
    def hash4(self, code):
        code.append('''
vec4 hash4( vec2 p ) { return fract(sin(vec4( 1.0+dot(p,vec2(37.0,17.0)),
                                              2.0+dot(p,vec2(11.0,47.0)),
                                              3.0+dot(p,vec2(41.0,29.0)),
                                              4.0+dot(p,vec2(23.0,31.0))))*103.0); }
''')

    def hash_texture_tiling(self, code):
        code.append(
'''vec4 hash_texture_tiling(sampler2D samp, in vec2 uv)
{
    vec2 iuv = floor(uv.xy);
    vec2 fuv = fract(uv.xy);

    // generate per-tile transform
    vec4 ofa = hash4(iuv + vec2(0.0, 0.0));
    vec4 ofb = hash4(iuv + vec2(1.0, 0.0));
    vec4 ofc = hash4(iuv + vec2(0.0, 1.0));
    vec4 ofd = hash4(iuv + vec2(1.0, 1.0));

    vec2 ddx = dFdx(uv.xy);
    vec2 ddy = dFdy(uv.xy);

    // transform per-tile uvs
    ofa.zw = sign(ofa.zw - 0.5);
    ofb.zw = sign(ofb.zw - 0.5);
    ofc.zw = sign(ofc.zw - 0.5);
    ofd.zw = sign(ofd.zw - 0.5);

    // uv's, and derivarives (for correct mipmapping)
    vec2 uva = uv.xy*ofa.zw + ofa.xy; vec2 ddxa = ddx*ofa.zw; vec2 ddya = ddy*ofa.zw;
    vec2 uvb = uv.xy*ofb.zw + ofb.xy; vec2 ddxb = ddx*ofb.zw; vec2 ddyb = ddy*ofb.zw;
    vec2 uvc = uv.xy*ofc.zw + ofc.xy; vec2 ddxc = ddx*ofc.zw; vec2 ddyc = ddy*ofc.zw;
    vec2 uvd = uv.xy*ofd.zw + ofd.xy; vec2 ddxd = ddx*ofd.zw; vec2 ddyd = ddy*ofd.zw;

    // fetch and blend
    vec2 b = smoothstep(0.25, 0.75, fuv);
    return mix( mix(textureGrad(samp, uva, ddxa, ddya),
                    textureGrad(samp, uvb, ddxb, ddyb), b.x),
                mix(textureGrad(samp, uvc, ddxc, ddyc),
                    textureGrad(samp, uvd, ddxd, ddyd), b.x), b.y);
}
''')

    def hash_texture_array_tiling(self, code):
        code.append(
'''vec4 hash_texture_array_tiling(sampler2DArray samp, in vec3 uv)
{
    vec2 iuv = floor(uv.xy);
    vec2 fuv = fract(uv.xy);

    // generate per-tile transform
    vec4 ofa = hash4(iuv + vec2(0.0, 0.0));
    vec4 ofb = hash4(iuv + vec2(1.0, 0.0));
    vec4 ofc = hash4(iuv + vec2(0.0, 1.0));
    vec4 ofd = hash4(iuv + vec2(1.0, 1.0));

    vec2 ddx = dFdx(uv.xy);
    vec2 ddy = dFdy(uv.xy);

    // transform per-tile uvs
    ofa.zw = sign(ofa.zw - 0.5);
    ofb.zw = sign(ofb.zw - 0.5);
    ofc.zw = sign(ofc.zw - 0.5);
    ofd.zw = sign(ofd.zw - 0.5);

    // uv's, and derivarives (for correct mipmapping)
    vec2 uva = uv.xy*ofa.zw + ofa.xy; vec2 ddxa = ddx*ofa.zw; vec2 ddya = ddy*ofa.zw;
    vec2 uvb = uv.xy*ofb.zw + ofb.xy; vec2 ddxb = ddx*ofb.zw; vec2 ddyb = ddy*ofb.zw;
    vec2 uvc = uv.xy*ofc.zw + ofc.xy; vec2 ddxc = ddx*ofc.zw; vec2 ddyc = ddy*ofc.zw;
    vec2 uvd = uv.xy*ofd.zw + ofd.xy; vec2 ddxd = ddx*ofd.zw; vec2 ddyd = ddy*ofd.zw;

    // fetch and blend
    vec2 b = smoothstep(0.25, 0.75, fuv);
    return mix( mix(textureGrad(samp, vec3(uva, uv.z), ddxa, ddya),
                    textureGrad(samp, vec3(uvb, uv.z), ddxb, ddyb), b.x),
                mix(textureGrad(samp, vec3(uvc, uv.z), ddxc, ddyc),
                    textureGrad(samp, vec3(uvd, uv.z), ddxd, ddyd), b.x), b.y);
}
''')

    def extra(self, code):
        self.shader.fragment_shader.add_function(code, 'hash4', self.hash4)
        self.shader.fragment_shader.add_function(code, 'hash_texture_tiling', self.hash_texture_tiling)
        self.shader.fragment_shader.add_function(code, 'hash_texture_array_tiling', self.hash_texture_array_tiling)

    def tile_texture(self, texture, coord):
        return 'hash_texture_tiling({}, {})'.format(texture, coord)

    def tile_texture_array(self, texture, coord, page):
        return 'hash_texture_array_tiling({}, vec3({}, {}))'.format(texture, coord, page)

class TextureDictionaryDataSource(ShaderDataSource):
    def __init__(self, dictionary, shader=None):
        ShaderDataSource.__init__(self, shader)
        self.dictionary = dictionary
        self.tiling = dictionary.tiling

    def get_id(self):
        return 'dict' + str(id(self))

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
                        texture_sample = self.tiling.tile_texture_array('tex_{}'.format(dict_name), position, tex_id)
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
                        texture_sample = self.tiling.tile_texture('tex_{}_{}'.format(dict_name, texture.category), position)
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

    def __init__(self, textures_control, heightmap, create_normals=False, shader=None):
        ShaderAppearance.__init__(self, shader)
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

    def __init__(self, textures_control, heightmap, create_normals=True, shader=None):
        ShaderAppearance.__init__(self, shader)
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

    def update_shader_shape_static(self, shape, appearance):
        ShaderAppearance.update_shader_shape_static(self, shape, appearance)
        self.textures_control.update_shader_shape_static(shape, appearance)

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
    # Workaround class to have a shader appearance for the TextureDictionaryDataSource
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
        shape.get_data_source().apply_patch_data(patch, instance)
        #instance.set_shader_input("flat_coord", patch.flat_coord)
        self.texture_source.apply(shape, instance)
        self.heightmap.apply_patch_data(patch, instance)
