#
#This file is part of Cosmonium.
#
#Copyright (C) 2018-2023 Laurent Deru.
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


from .component import ShaderComponent
from ..utils import TransparencyBlend


class ShaderAppearance(ShaderComponent):

    def __init__(self):
        ShaderComponent.__init__(self)
        self.data = None
        self.has_surface = False
        self.has_emission = False
        self.has_occlusion = False
        self.has_normal = False
        self.normal_texture_tangent_space = False
        self.has_bump = False
        self.has_metalroughness = False
        self.has_specular = False
        self.has_transparency = False
        self.has_nightscale = False
        self.has_backlit = False

        self.has_vertex_color = False
        self.has_attribute_color = False
        self.has_material = False

        self.vertex_requires = set()
        self.fragment_requires = set()

    def fragment_shader_decl(self, code):
        if self.has_surface:
            code.append("vec4 surface_color;")
        if self.has_emission:
            code.append("vec3 emission_color;")
        if self.has_occlusion:
            code.append("float surface_occlusion;")
        if self.has_normal:
            code.append("vec3 pixel_normal;")
        if self.has_specular:
            code.append("float shininess;")
            code.append("vec3 specular_color;")
        if self.has_metalroughness:
            code.append("float metallic;")
            code.append("float perceptual_roughness;")


class TextureAppearance(ShaderAppearance):

    def get_id(self):
        config = ""
        if self.has_surface:
            config += "u"
        if self.has_emission:
            config += "e"
        if self.has_occlusion:
            config += "o"
        if self.has_normal:
            config += "n"
        if self.has_bump:
            config += "b"
        if self.has_specular:
            config += "s"
        if self.has_transparency:
            config += "t"
            if self.transparency_blend == TransparencyBlend.TB_None:
                config += "b"
        if self.has_metalroughness:
            config += 'mr'
        if self.has_nightscale:
            config += 'i'
        if self.has_backlit:
            config += 'a'
        return config

    def create_shader_configuration(self, appearance):
        #TODO: This should use the shader data source iso appearance!
        self.has_surface = True
        self.has_occlusion = self.data.has_source_for('occlusion')
        self.has_normal = appearance.normal_map is not None or self.data.has_source_for('normal')
        self.normal_texture_tangent_space = appearance.normal_map_tangent_space
        self.has_bump = appearance.bump_map is not None

        self.has_specular = appearance.specularColor is not None
        self.has_emission = appearance.emission_texture is not None

        self.has_metalroughness = appearance.metalroughness_map is not None
        self.has_transparency = appearance.transparency
        self.transparency_blend = appearance.transparency_blend

        self.has_nightscale = appearance.nightscale is not None
        self.has_backlit = appearance.backlit is not None

        if self.has_normal:
            self.fragment_requires.add('world_normal')
            if self.normal_texture_tangent_space:
                self.fragment_requires.add('tangent')
                if appearance.generate_binormal:
                    self.fragment_requires.add('generate_binormal')

    def fragment_shader(self, code):
        if self.has_surface:
            code.append("surface_color = %s;" % self.data.get_source_for('surface'))
        if self.has_emission:
            code.append("emission_color = %s;" % self.data.get_source_for('emission'))
        if self.has_transparency:
            #TODO: technically binary transparency is alpha strictly lower than .5
            code.append("if (surface_color.a <= transparency_level) discard;")
            if self.transparency_blend == TransparencyBlend.TB_None:
                code.append("surface_color.a = 1.0;")
        if self.has_normal:
            code.append("pixel_normal = %s;" % self.data.get_source_for('normal'))
        if self.has_specular:
            code.append("shininess = %s;" % self.data.get_source_for('shininess'))
            code.append("specular_color = %s;" % self.data.get_source_for('specular-color'))
        if self.has_occlusion:
            code.append("surface_occlusion = %s;" % self.data.get_source_for('occlusion'))
        if self.has_metalroughness:
            code.append("metallic = %s;" % self.data.get_source_for('metallic'))
            code.append("perceptual_roughness = %s;" % self.data.get_source_for('roughness'))
