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


from ..component import ShaderComponent, CompositeShaderComponent
from ..shadows.locallights import ShaderLocalShadows
from .scattering import NoScattering


class LightingModelBase(ShaderComponent):

    def set_scattering(self, scattering):
        raise NotImplementedError()


class BRDFInterface:

    def prepare_material(self, code):
        raise NotImplementedError()

    def light_contribution(self, code, result, light_direction, light_color):
        raise NotImplementedError()

    def ambient_contribution(self, code, result, ambient_diffuse):
        raise NotImplementedError()

    def cos_light_normal(self):
        raise NotImplementedError()


class EmissionModelInterface:
    def light_contribution(self, code, light_direction, light_color, cos_light_angle):
        raise NotImplementedError()

    def global_emission(self, code):
        raise NotImplementedError()


class NoEmission(ShaderComponent, EmissionModelInterface):

    def light_contribution(self, code, light_direction, light_color, cos_light_angle):
        pass

    def global_emission(self, code):
        pass


class EmissionMap(ShaderComponent, EmissionModelInterface):

    def light_contribution(self, code, light_direction, light_color, cos_light_angle):
        pass

    def global_emission(self, code):
        code.append("  total_emission_color.rgb += emission_color.rgb;")


class BacklitEmission(ShaderComponent, EmissionModelInterface):

    def fragment_uniforms(self, code):
        code.append("uniform float backlit;")

    def light_contribution(self, code, light_direction, light_color, cos_light_angle):
        code.append(f"if ({cos_light_angle} < 0.0) {{")
        code.append(f"  total_emission_color.rgb += surface_color.rgb * backlit * sqrt(-{cos_light_angle}) * global_shadow;")
        code.append("}")

    def global_emission(self, code):
        pass


class NightLightEmission(ShaderComponent, EmissionModelInterface):

    def fragment_uniforms(self, code):
        code.append("uniform float nightscale;")

    def light_contribution(self, code, light_direction, light_color, cos_light_angle):
        code.append(f"if ({cos_light_angle} < 0.0) {{")
        code.append(f"  float emission_coef = clamp(sqrt(-{cos_light_angle}), 0.0, 1.0) * nightscale;")
        code.append("  total_emission_color.rgb += emission_color.rgb * emission_coef;")
        code.append("}")

    def global_emission(self, code):
        pass


class ShadingLightingModel(CompositeShaderComponent):

    def __init__(self, brdf: ShaderComponent):
        CompositeShaderComponent.__init__(self)
        self.brdf = brdf
        self.scattering = NoScattering()
        self.emission = NoEmission()
        self.local_shadows = ShaderLocalShadows()
        self.add_component(brdf)
        self.add_component(self.scattering)
        self.add_component(self.emission)
        self.add_component(self.local_shadows)
        self._appearance = None

    @property
    def appearance(self):
        return self._appearance

    @appearance.setter
    def appearance(self, appearance):
        self._appearance = appearance
        for component in self.components:
            component.appearance = appearance

    def set_scattering(self, scattering):
        self.remove_component(self.scattering)
        self.scattering = scattering
        self.add_component(self.scattering)

    def create_shader_configuration(self, appearance):
        CompositeShaderComponent.create_shader_configuration(self, appearance)
        self.remove_component(self.emission)
        if self.appearance.has_emission:
            if self.appearance.has_nightscale:
                self.emission = NightLightEmission()
            else:
                self.emission = EmissionMap()
        elif self.appearance.has_backlit:
            self.emission = BacklitEmission()
        else:
            self.emission = NoEmission()
        self.add_component(self.emission)

    def vertex_uniforms(self, code):
        CompositeShaderComponent.vertex_uniforms(self, code)
        code.append("""
uniform struct p3d_LightSourceParameters {
    vec4 position;
    vec4 diffuse;
    vec4 specular;
    vec3 attenuation;
    vec3 spotDirection;
    float spotCosCutoff;
    sampler2DShadow shadowMap;
    mat4 shadowViewMatrix;
} p3d_LightSource[8];
""")

    def fragment_uniforms(self, code):
        CompositeShaderComponent.fragment_uniforms(self, code)
        code.append("""
uniform struct p3d_LightSourceParameters {
    vec4 position;
    vec4 diffuse;
    vec4 specular;
    vec3 attenuation;
    vec3 spotDirection;
    float spotCosCutoff;
    sampler2DShadow shadowMap;
    mat4 shadowViewMatrix;
} p3d_LightSource[8];

uniform struct p3d_LightModelParameters {
    vec4 ambient;
} p3d_LightModel;

""")
        code.append("const float LIGHT_CUTOFF = 0.001;")
        code.append("const float SPOTSMOOTH = 0.001;")
        code.append("uniform float ambient_coef;")
        code.append("uniform vec3 ambient_color;")

    def vertex_shader(self, code):
        CompositeShaderComponent.vertex_shader(self, code)
        code.append("for (int i = 0; i < p3d_LightSource.length(); ++i) {")
        self.local_shadows.prepare_shadow_for(code, "i")
        code.append("}")
        global_lights = self.shader.data_source.get_source_for('global_lights')
        code.append("for (int i = 0; i < 1; ++i) {")
        for shadow in self.shader.shadows:
            shadow.prepare_shadow_for(code, "i", global_lights + "direction", global_lights + "eye_direction")
        self.scattering.prepare_scattering_for(code, global_lights + "eye_direction", global_lights + "color")
        code.append("}")

    def fragment_shader(self, code):
        CompositeShaderComponent.fragment_shader(self, code)
        self.brdf.prepare_material(code)
        code.append("for (int i = 0; i < p3d_LightSource.length(); ++i) {")
        code.append("    vec3 lightcol = p3d_LightSource[i].diffuse.rgb;")
        code.append("    if (dot(lightcol, lightcol) < LIGHT_CUTOFF) {")
        code.append("        continue;")
        code.append("    }")
        code.append("    float shadow = 1.0;")
        code.append("    vec3 light_position = p3d_LightSource[i].position.xyz - eye_vertex * p3d_LightSource[i].position.w;")
        code.append("    vec3 light_direction = normalize(light_position);")
        code.append("    float light_distance = length(light_position);")
        code.append("    vec3 attenuation_params = p3d_LightSource[i].attenuation;")
        code.append("    float attenuation_factor = 1.0 / (attenuation_params.x + attenuation_params.y * light_distance + attenuation_params.z * light_distance * light_distance);")
        code.append("    shadow *= attenuation_factor;")
        code.append("    float spot_cos = dot(normalize(p3d_LightSource[i].spotDirection), -light_direction);")
        code.append("    float spot_cutoff = p3d_LightSource[i].spotCosCutoff;")
        code.append("    float shadow_spot = smoothstep(spot_cutoff - SPOTSMOOTH, spot_cutoff + SPOTSMOOTH, spot_cos);")
        code.append("    shadow *= shadow_spot;")
        self.local_shadows.shadow_for(code, "i")
        code.append("    vec3 contribution = vec3(0);")
        self.brdf.light_contribution(code, "contribution", "light_direction", "p3d_LightSource[i].diffuse")
        code.append("    total_diffuse_color.rgb += contribution * shadow;")
        code.append("}")
        global_lights = self.shader.data_source.get_source_for('global_lights')
        code.append("  vec3 transmittance;")
        self.scattering.calc_transmittance(code)
        code.append("for (int i = 0; i < 1; ++i) {")
        code.append("    vec3 incoming_light_color;")
        code.append("    vec3 in_scatter;")
        code.append("    vec3 ambient_diffuse;")
        code.append("    float global_shadow = 1.0;")
        code.append("    float local_shadow = 1.0;")
        for shadow in self.shader.shadows:
            shadow.shadow_for(code, "i", global_lights + "direction", global_lights + "eye_direction")
        self.scattering.incoming_light_for(code, global_lights + "eye_direction", global_lights + "color")
        code.append("    vec3 direct_contribution;")
        self.brdf.light_contribution(code, "direct_contribution", global_lights + "eye_direction", "incoming_light_color")
        code.append("    vec3 indirect_contribution;")
        self.brdf.ambient_contribution(code, "indirect_contribution", "ambient_diffuse")
        code.append("    total_diffuse_color.rgb += ((direct_contribution * local_shadow + indirect_contribution ) * transmittance + in_scatter) * global_shadow;")
        self.emission.light_contribution(code, global_lights + "direction", global_lights + "eye_direction", self.brdf.cos_light_normal())
        code.append("}")
        code.append("vec3 ambient = surface_color.rgb * (ambient_color * ambient_coef + p3d_LightModel.ambient.rgb);")
        if self.appearance.has_occlusion:
            code.append("ambient *= surface_occlusion;")
        code.append("total_diffuse_color.rgb += ambient;")
        code.append("total_diffuse_color.a = surface_color.a;")
        self.emission.global_emission(code)


class AtmosphereLightingModel(CompositeShaderComponent):

    def __init__(self):
        CompositeShaderComponent.__init__(self)
        self.scattering = NoScattering()
        self.add_component(self.scattering)
        self._appearance = None

    @property
    def appearance(self):
        return self._appearance

    @appearance.setter
    def appearance(self, appearance):
        self._appearance = appearance
        for component in self.components:
            component.appearance = appearance

    def set_scattering(self, scattering):
        self.remove_component(self.scattering)
        self.scattering = scattering
        self.add_component(self.scattering)

    def vertex_shader(self, code):
        CompositeShaderComponent.vertex_shader(self, code)
        global_lights = self.shader.data_source.get_source_for('global_lights')
        code.append("for (int i = 0; i < 1; ++i) {")
        self.scattering.prepare_scattering_for(code, global_lights + "eye_direction", global_lights + "color")
        code.append("}")

    def fragment_shader(self, code):
        CompositeShaderComponent.fragment_shader(self, code)
        global_lights = self.shader.data_source.get_source_for('global_lights')
        code.append("for (int i = 0; i < 1; ++i) {")
        code.append("    vec3 incoming_light_color;")
        code.append("    vec3 in_scatter;")
        code.append("    vec3 transmittance;")
        self.scattering.incoming_light_for(code, global_lights + "eye_direction", global_lights + "color")
        code.append("    total_diffuse_color.rgb += in_scatter;")
        code.append("}")
        code.append("total_diffuse_color.a = surface_color.a;")
