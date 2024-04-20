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


from .base import ShaderDataSource


class PandaShaderDataSource(ShaderDataSource):
    def __init__(self):
        ShaderDataSource.__init__(self)
        self.tex_transform = False
        self.texture_index = 0
        self.normal_map_index = 0
        self.bump_map_index = 0
        self.specular_map_index = 0
        self.emission_texture_index = 0
        self.nb_textures = 0
        self.has_surface_texture = False
        self.has_normal_texture = False
        self.has_bump_texture = False
        self.has_specular_texture = False
        self.has_specular_mask = False
        self.has_emission_texture = False
        self.has_transparency = False
        self.has_metalroughness_map_texture = False
        self.has_occlusion_map_texture = False
        self.has_occlusion_channel = False

    def get_id(self):
        config = ""
        if self.has_material:
            config += "m"
        if self.has_surface_texture:
            config += "u"
        if self.has_normal_texture:
            config += "n"
        if self.has_bump_texture:
            config += "b"
        if self.has_specular_texture:
            config += "s"
        if self.has_specular_mask:
            config += "p"
        if self.has_alpha_mask:
            config += "l"
        if self.has_emission_texture:
            config += "e"
        if self.has_transparency:
            config += "t"
        if self.tex_transform:
            config += "r"
        if self.has_metalroughness_map_texture:
            config += "g"
        if self.has_occlusion_map_texture:
            config += "o"
        if self.has_occlusion_channel:
            config += "c"
        return config

    def create_shader_configuration(self, appearance):
        self.tex_transform = appearance.tex_transform
        self.has_vertex_color = appearance.has_vertex_color
        self.has_attribute_color = appearance.has_attribute_color
        self.has_material = appearance.has_material
        self.has_specular = appearance.specularColor is not None
        self.texture_index = appearance.texture_index
        self.normal_map_index = appearance.normal_map_index
        self.bump_map_index = appearance.bump_map_index
        self.specular_map_index = appearance.specular_map_index
        self.emission_texture_index = appearance.emission_texture_index
        self.metalroughness_map_texture_index = appearance.metalroughness_map_texture_index
        self.occlusion_map_texture_index = appearance.occlusion_map_index
        self.nb_textures = appearance.nb_textures
        self.has_surface_texture = appearance.texture is not None
        self.has_normal_texture = appearance.normal_map is not None
        self.has_bump_texture = appearance.bump_map is not None
        self.has_specular_texture = appearance.specular_map is not None
        self.has_emission_texture = appearance.emission_texture
        self.has_metalroughness_map_texture = appearance.metalroughness_map is not None
        self.has_occlusion_map_texture = appearance.occlusion_map is not None
        self.has_specular_mask = appearance.has_specular_mask
        self.has_transparency = appearance.transparency
        self.has_alpha_mask = appearance.alpha_mask
        self.has_occlusion_channel = appearance.has_occlusion_channel

    def vertex_inputs(self, code):
        if self.has_vertex_color:
            code.append("in vec4 p3d_Color;")

    def vertex_outputs(self, code):
        if self.has_vertex_color:
            code.append("out vec4 vertex_color;")

    def vertex_shader(self, code):
        if self.has_vertex_color:
            code.append("vertex_color = p3d_Color;")

    def create_tex_coord(self, texture_id, texture_coord):
        code = []
        if self.shader.use_model_texcoord:
            if self.tex_transform:
                code.append("vec4 texcoord_tex%d = p3d_TextureMatrix[%d] * texcoord%d;" % (texture_id, texture_id, texture_coord))
            else:
                code.append("vec4 texcoord_tex%d = texcoord%d;" % (texture_id, texture_coord))
        else:
            #Using algo from http://vcg.isti.cnr.it/~tarini/no-seams/jgt_tarini.pdf (http://vcg.isti.cnr.it/~tarini/no-seams/)
            code.append("float du1 = fwidth(texcoord0.x);")
            code.append("float du2 = fwidth(texcoord0p.x);")
            code.append("vec4 texcoord_tex%d;" % (texture_id))
            #-0.001 is needed to avaoid noise artifacts
            code.append("if (du1 < du2 - 0.001) {")
            code.append("  texcoord_tex%d = texcoord%d;" % (texture_id, texture_coord))
            code.append("} else {")
            code.append("  texcoord_tex%d =  texcoord0p;" % (texture_id))
            code.append("}")
            if self.tex_transform:
                code.append("  texcoord_tex%d = p3d_TextureMatrix[%d] * texcoord_tex%d;" % (texture_id, texture_id, texture_id))
            code.append("texcoord_tex%d.xyz /= texcoord_tex%d.w;" % (texture_id, texture_id))
        return code

    def create_sample_texture(self, texture_id):
        code = []
        code.append("vec4 tex%i = texture(p3d_Texture%i, texcoord_tex%d.xy);" % (texture_id, texture_id, texture_id))
        return code

    def fragment_uniforms(self, code):
        for i in range(self.nb_textures):
            code.append("uniform sampler2D p3d_Texture%i;" % i)
        if self.nb_textures > 0:
            code.append("uniform mat4 p3d_TextureMatrix[%d];" % (self.nb_textures))
        code.append("uniform vec4 p3d_ColorScale;")
        if self.has_specular:
            code.append("uniform vec3 shape_specular_color;")
            code.append("uniform float shape_shininess;")
        if self.has_transparency:
            code.append("uniform float transparency_level;")
        if self.has_attribute_color:
            code.append("uniform vec4 p3d_Color;")
        if self.has_material:
            code.append("""uniform struct {
  vec4 ambient;
  vec4 diffuse;
  vec4 emission;
  vec3 specular;
  float shininess;

  vec4 baseColor;
  float roughness;
  float metallic;
  float refractiveIndex;
} p3d_Material;
""")

    def fragment_inputs(self, code):
        if self.has_vertex_color:
            code.append("in vec4 vertex_color;")

    def fragment_shader_decl(self, code):
        texture_coord = 0
        if self.has_surface_texture:
            code += self.create_tex_coord(self.texture_index, texture_coord)
        if self.has_normal_texture:
            code += self.create_tex_coord(self.normal_map_index, texture_coord)
        if self.has_bump_texture:
            code += self.create_tex_coord(self.bump_map_index, texture_coord)
        if self.has_specular_texture:
            code += self.create_tex_coord(self.specular_map_index, texture_coord)
        if self.has_emission_texture:
            code += self.create_tex_coord(self.emission_texture_index, texture_coord)
        if self.has_metalroughness_map_texture:
            code += self.create_tex_coord(self.metalroughness_map_texture_index, texture_coord)
        if self.has_occlusion_map_texture:
            code += self.create_tex_coord(self.occlusion_map_texture_index, texture_coord)

    def bump_sample(self, code):
        pass

    def has_source_for(self, source):
        if source == 'occlusion':
            return self.has_occlusion_map_texture or self.has_occlusion_channel
        return False

    def get_source_for(self, source, params=None, error=True):
        if source == 'surface':
            if self.has_attribute_color:
                #TODO: Should the texture be modulated ?
                return "p3d_Color * p3d_ColorScale"
            elif self.has_alpha_mask:
                return "vec4(1.0)"
            else:
                if self.has_surface_texture:
                    if self.has_transparency:
                        data = "tex%i" % self.texture_index
                    else:
                        data = "vec4(tex%i.rgb, 1.0)" % self.texture_index
                else:
                    data = "vec4(1.0)"
            if self.has_vertex_color:
                data = data + " * vertex_color"
            if self.has_material:
                data = data + " * p3d_Material.baseColor"
            data += " * p3d_ColorScale"
            return data
        if source == 'alpha':
            if self.has_transparency:
                if self.has_surface_texture:
                    data = "tex%i.a" % self.texture_index
                else:
                    data = "1.0"
            if self.has_vertex_color:
                data = data + " * vertex_color.a"
            if self.has_material:
                data = data + " * p3d_Material.baseColor.a"
            data += " * p3d_ColorScale.a"
            return data
        if source == 'normal':
            if self.has_normal_texture:
                return "(vec3(tex%i) * 2.0) - 1.0" % self.normal_map_index
            else:
                return "vec3(0, 0, 1.0)"
        if source == 'shininess':
                return "shape_shininess"
        if source == 'specular-color':
            if self.has_specular_texture:
                return "tex%i.rgb * shape_specular_color" % self.specular_map_index
            elif self.has_specular_mask:
                return "tex%i.aaa * shape_specular_color" % self.texture_index
            else:
                return "shape_specular_color"
        if source == 'emission':
            if self.has_emission_texture:
                data = "tex%i.rgb" % self.emission_texture_index
                if self.has_material:
                    data += " * p3d_Material.emission.rgb"
            elif self.has_material:
                data = "p3d_Material.emission.rgb"
            else:
                data = "vec3(0.0)"
            return data
        if source == 'metallic':
            if self.has_metalroughness_map_texture:
                data = "tex%i.b" % self.metalroughness_map_texture_index
            else:
                data = "1.0"
            if self.has_material:
                data = data + " * p3d_Material.metallic"
            return data
        if source == 'roughness':
            if self.has_metalroughness_map_texture:
                data = "tex%i.g" % self.metalroughness_map_texture_index
            else:
                data = "1.0"
            if self.has_material:
                data = data + " * p3d_Material.roughness"
            return data
        if source == 'occlusion':
            if self.has_occlusion_map_texture:
                return "tex%i.r" % self.occlusion_map_texture_index
            if self.has_occlusion_channel:
                return "tex%i.r" % self.metalroughness_map_texture_index
        if error: print("Unknown source '%s' requested" % source)
        return ''

    def fragment_shader(self, code):
        if self.has_surface_texture:
            code += self.create_sample_texture(self.texture_index)
        if self.has_normal_texture:
            code += self.create_sample_texture(self.normal_map_index)
        if self.has_specular_texture:
            code += self.create_sample_texture(self.specular_map_index)
        if self.has_emission_texture:
            code += self.create_sample_texture(self.emission_texture_index)
        if self.has_metalroughness_map_texture:
            code += self.create_sample_texture(self.metalroughness_map_texture_index)
        if self.has_occlusion_map_texture:
            code += self.create_sample_texture(self.occlusion_map_texture_index)
