#
# This file is part of Cosmonium.
#
# Copyright (C) 2018-2024 Laurent Deru.
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

from .. import settings
from .appearance import TextureAppearance
from .base import ShaderProgram, StructuredShader
from .component import ShaderComponent
from .data_source.base import CompositeShaderDataSource
from .data_source.panda import PandaShaderDataSource
from .instancing import NoInstanceControl
from .lighting.base import ShadingLightingModel
from .lighting.lambert import LambertPhongLightingModel
from .point_control import NoPointControl
from .tessellation import QuadTessellationVertexInput, TessellationControl
from .vertex_control.vertex_control import DefaultVertexControl
from .vertex_input import DirectVertexInput


class TessellationVertexShader(ShaderProgram):

    def __init__(self):
        ShaderProgram.__init__(self, 'vertex')

    def create_inputs(self, code):
        code.append("in vec4 p3d_Vertex;")

    def create_body(self, code):
        code.append("gl_Position = p3d_Vertex;")


class VertexShader(ShaderProgram):

    def __init__(
        self,
        config,
        shader_type,
        vertex_source,
        data_source,
        appearance,
        vertex_control,
        point_control,
        instance_control,
        shadows,
        lighting_model,
    ):
        ShaderProgram.__init__(self, shader_type)
        self.config = config
        self.vertex_source = vertex_source
        self.data_source = data_source
        self.appearance = appearance
        self.vertex_control = vertex_control
        self.point_control = point_control
        self.instance_control = instance_control
        self.shadows = shadows
        self.lighting_model = lighting_model

    def create_layout(self, code):
        self.vertex_source.vertex_layout(code)

    def create_uniforms(self, code):
        code.append("uniform mat4 p3d_ProjectionMatrix;")
        code.append("uniform mat4 p3d_ModelMatrix;")
        code.append("uniform mat4 p3d_ModelMatrixInverseTranspose;")
        code.append("uniform mat4 p3d_ViewMatrix;")
        code.append("uniform mat4 p3d_ModelViewMatrix;")
        if 'eye_normal' in self.config.fragment_requires:
            code.append("uniform mat3 p3d_NormalMatrix;")
        code.append("uniform vec2 win_size;")
        code.append("uniform vec2 target_size;")
        self.vertex_control.vertex_uniforms(code)
        self.point_control.vertex_uniforms(code)
        self.instance_control.vertex_uniforms(code)
        for shadow in self.shadows:
            shadow.vertex_uniforms(code)
        self.lighting_model.vertex_uniforms(code)
        self.data_source.vertex_uniforms(code)
        self.appearance.vertex_uniforms(code)

    def create_inputs(self, code):
        self.vertex_source.vertex_inputs(code)
        for shadow in self.shadows:
            shadow.vertex_inputs(code)
        self.lighting_model.vertex_inputs(code)
        self.point_control.vertex_inputs(code)
        self.instance_control.vertex_inputs(code)
        self.data_source.vertex_inputs(code)
        self.appearance.vertex_inputs(code)
        if self.config.color_picking and self.config.vertex_oids:
            code.append("in vec4 oid;")

    def create_outputs(self, code):
        if 'model_vertex' in self.config.fragment_requires:
            code.append("out vec3 v_model_vertex;")
        if 'world_vertex' in self.config.fragment_requires:
            code.append("out vec3 v_world_vertex;")
        if 'eye_vertex' in self.config.fragment_requires:
            code.append("out vec3 v_eye_vertex;")
        if 'model_normal' in self.config.fragment_requires:
            code.append("out vec3 v_model_normal;")
        if 'world_normal' in self.config.fragment_requires:
            code.append("out vec3 v_world_normal;")
        if 'centroid_world_normal' in self.config.fragment_requires:
            code.append("centroid out vec3 v_centroid_world_normal;")
        if 'eye_normal' in self.config.fragment_requires:
            code.append("out vec3 v_eye_normal;")
        if 'tangent' in self.config.fragment_requires:
            code.append("out vec3 v_binormal;")
            code.append("out vec3 v_tangent;")
        if 'relative_vector_to_obs' in self.config.fragment_requires:
            code.append("out vec3 v_relative_vector_to_obs;")
        for i in range(self.config.nb_textures_coord):
            code.append("out vec4 texcoord%i;" % i)
        if not self.config.use_model_texcoord:
            code.append("out vec4 texcoord0p;")
        self.vertex_control.vertex_outputs(code)
        self.point_control.vertex_outputs(code)
        for shadow in self.shadows:
            shadow.vertex_outputs(code)
        self.lighting_model.vertex_outputs(code)
        self.data_source.vertex_outputs(code)
        self.appearance.vertex_outputs(code)
        if self.config.color_picking and self.config.vertex_oids:
            code.append("out vec4 color_picking;")

    def create_extra(self, code):
        ShaderProgram.create_extra(self, code)
        self.data_source.vertex_extra(code)
        self.vertex_source.vertex_extra(code)
        self.vertex_control.vertex_extra(code)
        self.point_control.vertex_extra(code)
        self.lighting_model.vertex_extra(code)
        for shadow in self.shadows:
            shadow.vertex_extra(code)

    def create_body(self, code):
        code.append("vec4 model_vertex4;")
        if 'model_normal' in self.config.vertex_requires:
            code.append("vec4 model_normal4;")
        if 'tangent' in self.config.vertex_requires:
            code.append("vec4 model_binormal4;")
            code.append("vec4 model_tangent4;")
        for i in range(self.config.nb_textures_coord):
            code.append("vec4 model_texcoord%i;" % i)
        if not self.config.use_model_texcoord:
            code.append("vec4 model_texcoord0p;")
        self.vertex_source.vertex_shader(code)
        code.append("vec3 model_vertex;")
        if 'world_vertex' in self.config.vertex_requires:
            code.append("vec4 world_vertex4;")
            code.append("vec3 world_vertex;")
        if 'eye_vertex' in self.config.vertex_requires:
            code.append("vec4 eye_vertex4;")
            code.append("vec3 eye_vertex;")
        if 'model_normal' in self.config.vertex_requires:
            code.append("vec3 model_normal;")
        if 'world_normal' in self.config.vertex_requires:
            code.append("vec3 world_normal;")
        if 'eye_normal' in self.config.vertex_requires:
            code.append("vec3 eye_normal;")
        if 'tangent' in self.config.vertex_requires:
            code.append("vec3 binormal;")
            code.append("vec3 tangent;")

        self.point_control.vertex_shader_decl(code)
        self.appearance.vertex_shader_decl(code)
        self.data_source.vertex_shader_decl(code)

        if 'model_vertex' in self.vertex_control.vertex_provides:
            self.vertex_control.update_vertex(code)
        if 'model_normal' in self.config.vertex_requires and 'model_normal' in self.vertex_control.vertex_provides:
            self.vertex_control.update_normal(code)
        if 'world_vertex' in self.config.vertex_requires and not (
            'world_vertex' in self.vertex_control.vertex_provides
            or 'world_vertex' in self.instance_control.vertex_provides
        ):
            code.append("world_vertex4 = p3d_ModelMatrix * model_vertex4;")
        self.instance_control.update_vertex(code)
        if 'eye_vertex' in self.config.vertex_requires:
            code.append("eye_vertex4 = p3d_ViewMatrix * world_vertex4;")
        if 'model_normal' in self.config.vertex_requires or 'world_normal' in self.config.vertex_requires:
            self.instance_control.update_normal(code)
        if (
            'world_vertex' in self.vertex_control.vertex_provides
            or 'world_vertex' in self.instance_control.vertex_provides
        ):
            code.append("gl_Position = p3d_ProjectionMatrix * (p3d_ViewMatrix * world_vertex4);")
        else:
            code.append("gl_Position = p3d_ProjectionMatrix * (p3d_ModelViewMatrix * model_vertex4);")
        if 'model_normal' in self.config.vertex_requires:
            code.append("model_normal = model_normal4.xyz;")
        if 'world_normal' in self.config.vertex_requires:
            code.append("world_normal = normalize((p3d_ModelMatrixInverseTranspose * model_normal4).xyz);")
        if 'eye_normal' in self.config.vertex_requires:
            code.append("eye_normal = normalize(p3d_NormalMatrix * model_normal4.xyz);")
        if 'tangent' in self.config.vertex_requires:
            code.append("tangent = vec3(normalize(p3d_ModelMatrix * model_tangent4));")
            code.append("binormal = vec3(normalize(p3d_ModelMatrix * model_binormal4));")
        if 'relative_vector_to_obs' in self.config.vertex_requires:
            code.append("vec3 vector_to_obs = -vertex.xyz / vertex.w;")
            code.append("vec3 relative_vector_to_obs_tmp;")
            code.append("relative_vector_to_obs_tmp.x = dot(p3d_Tangent, vector_to_obs);")
            code.append("relative_vector_to_obs_tmp.y = dot(p3d_Binormal, vector_to_obs);")
            code.append("relative_vector_to_obs_tmp.z = dot(normal, vector_to_obs);")
            code.append("relative_vector_to_obs = normalize(relative_vector_to_obs_tmp);")
        for i in range(self.config.nb_textures_coord):
            code.append("texcoord%i = model_texcoord%i;" % (i, i))
        if not self.config.use_model_texcoord:
            code.append("texcoord0p = model_texcoord0p;")
        if 'model_vertex' in self.config.vertex_requires:
            code.append("model_vertex = model_vertex4.xyz / model_vertex4.w;")
        if 'world_vertex' in self.config.vertex_requires:
            code.append("world_vertex = world_vertex4.xyz / world_vertex4.w;")
        if 'eye_vertex' in self.config.vertex_requires:
            code.append("eye_vertex = eye_vertex4.xyz / eye_vertex4.w;")
        for shadow in self.shadows:
            shadow.vertex_shader(code)
        self.point_control.vertex_shader(code)
        self.lighting_model.vertex_shader(code)
        self.data_source.vertex_shader(code)
        self.appearance.vertex_shader(code)
        if 'model_vertex' in self.config.fragment_requires:
            code.append("v_model_vertex = model_vertex;")
        if 'world_vertex' in self.config.fragment_requires:
            code.append("v_world_vertex = world_vertex;")
        if 'eye_vertex' in self.config.fragment_requires:
            code.append("v_eye_vertex = eye_vertex;")
        if 'model_normal' in self.config.fragment_requires:
            code.append("v_model_normal = model_normal;")
        if 'world_normal' in self.config.fragment_requires:
            code.append("v_world_normal = world_normal;")
        if 'centroid_world_normal' in self.config.fragment_requires:
            code.append("v_centroid_world_normal = world_normal;")
        if 'eye_normal' in self.config.fragment_requires:
            code.append("v_eye_normal = eye_normal;")
        if 'tangent' in self.config.fragment_requires:
            code.append("v_tangent = mat3(p3d_ViewMatrix) * tangent;")
            code.append("v_binormal = mat3(p3d_ViewMatrix) * binormal;")
        if 'relative_vector_to_obs' in self.config.fragment_requires:
            code.append("v_relative_vector_to_obs = relative_vector_to_obs;")
        if self.config.color_picking and self.config.vertex_oids:
            code.append("color_picking = oid;")


class TessellationShader(ShaderProgram):

    def __init__(self, config, tessellation_control):
        ShaderProgram.__init__(self, 'control')
        self.config = config
        self.tessellation_control = tessellation_control

    def create_layout(self, code):
        self.tessellation_control.vertex_layout(code)

    def create_uniforms(self, code):
        self.tessellation_control.vertex_uniforms(code)

    def create_inputs(self, code):
        self.tessellation_control.vertex_inputs(code)

    def create_outputs(self, code):
        self.tessellation_control.vertex_outputs(code)

    def create_extra(self, code):
        code.append("#define id gl_InvocationID")
        self.tessellation_control.vertex_extra(code)

    def create_body(self, code):
        code.append("if (id == 0) {")
        self.tessellation_control.vertex_shader(code)
        code.append("}")
        code.append("gl_out[id].gl_Position = gl_in[id].gl_Position;")


class FragmentShader(ShaderProgram):

    def __init__(
        self, config, data_source, appearance, shadows, lighting_model, vertex_control, point_control, after_effects
    ):
        ShaderProgram.__init__(self, 'fragment')
        self.config = config
        self.data_source = data_source
        self.appearance = appearance
        self.shadows = shadows
        self.lighting_model = lighting_model
        self.vertex_control = vertex_control
        self.point_control = point_control
        self.after_effects = after_effects
        self.nb_outputs = 1

    def create_uniforms(self, code):
        code.append("uniform vec2 win_size;")
        code.append("uniform vec2 target_size;")
        self.appearance.fragment_uniforms(code)
        self.data_source.fragment_uniforms(code)
        #         if self.config.has_bump_texture:
        #             code.append("uniform float bump_height;")
        for shadow in self.shadows:
            shadow.fragment_uniforms(code)
        self.lighting_model.fragment_uniforms(code)
        self.point_control.fragment_uniforms(code)
        for effect in self.after_effects:
            effect.fragment_uniforms(code)
        if self.config.color_picking and not self.config.vertex_oids:
            code.append("uniform vec4 color_picking;")
        if self.config.color_picking:
            code.append("layout (binding=0, rgba8) uniform writeonly image2D oid_store;")

    def create_inputs(self, code):
        if 'model_vertex' in self.config.fragment_requires:
            code.append("in vec3 v_model_vertex;")
        if 'world_vertex' in self.config.fragment_requires:
            code.append("in vec3 v_world_vertex;")
        if 'eye_vertex' in self.config.fragment_requires:
            code.append("in vec3 v_eye_vertex;")
        if 'model_normal' in self.config.fragment_requires:
            code.append("in vec3 v_model_normal;")
        if 'world_normal' in self.config.fragment_requires:
            code.append("in vec3 v_world_normal;")
        if 'centroid_world_normal' in self.config.fragment_requires:
            code.append("centroid in vec3 v_centroid_world_normal;")
        if 'eye_normal' in self.config.fragment_requires:
            code.append("in vec3 v_eye_normal;")
        if 'tangent' in self.config.fragment_requires:
            code.append("in vec3 v_tangent;")
            code.append("in vec3 v_binormal;")
        if 'relative_vector_to_obs' in self.config.fragment_requires:
            code.append("in vec3 v_relative_vector_to_obs;")
        for i in range(self.config.nb_textures_coord):
            code.append("in vec4 texcoord%i;" % i)
        if not self.config.use_model_texcoord:
            code.append("in vec4 texcoord0p;")
        self.appearance.fragment_inputs(code)
        self.data_source.fragment_inputs(code)
        for shadow in self.shadows:
            shadow.fragment_inputs(code)
        self.lighting_model.fragment_inputs(code)
        self.vertex_control.fragment_inputs(code)
        self.point_control.fragment_inputs(code)
        if self.config.color_picking and self.config.vertex_oids:
            code.append("in vec4 color_picking;")

    def create_outputs(self, code):
        if self.version >= 130:
            code.append("out vec4 frag_color[%d];" % self.nb_outputs)

    def create_extra(self, code):
        ShaderProgram.create_extra(self, code)
        self.data_source.fragment_extra(code)
        self.appearance.fragment_extra(code)
        for shadow in self.shadows:
            shadow.fragment_extra(code)
        self.lighting_model.fragment_extra(code)
        self.point_control.fragment_extra(code)
        for effect in self.after_effects:
            effect.fragment_extra(code)

    def create_body(self, code):
        if self.version < 130:
            code.append("vec4 frag_color[%d];" % self.nb_outputs)
        if 'model_vertex' in self.config.fragment_requires:
            code.append("vec3 model_vertex = v_model_vertex;")
        if 'world_vertex' in self.config.fragment_requires:
            code.append("vec3 world_vertex = v_world_vertex;")
        if 'eye_vertex' in self.config.fragment_requires:
            code.append("vec3 eye_vertex = v_eye_vertex;")
        if 'model_normal' in self.config.fragment_requires:
            code.append("vec3 model_normal = normalize(v_model_normal);")
        if 'world_normal' in self.config.fragment_requires:
            if 'centroid_world_normal' in self.config.fragment_requires:
                code.append("vec3 world_normal;")
                code.append("if (abs(dot(v_world_normal, v_world_normal) - 1) > 0.01) {")
                code.append("  world_normal = normalize(v_centroid_world_normal);")
                code.append("} else {")
                code.append("  world_normal = normalize(v_world_normal);")
                code.append("}")
            else:
                code.append("vec3 world_normal = normalize(v_world_normal);")
            code.append("vec3 normal = world_normal;")
        if 'eye_normal' in self.config.fragment_requires:
            code.append("vec3 eye_normal = normalize(v_eye_normal);")
            if self.appearance.has_normal:
                code.append("vec3 shape_eye_normal = eye_normal;")
        if 'tangent' in self.config.fragment_requires:
            code.append("vec3 tangent = normalize(v_tangent);")
            code.append("vec3 binormal = normalize(v_binormal);")

        self.point_control.fragment_shader_decl(code)
        self.appearance.fragment_shader_decl(code)
        self.data_source.fragment_shader_decl(code)
        if 'relative_vector_to_obs_norm' in self.config.fragment_requires:
            code.append("vec3 relative_vector_to_obs_norm = normalize(v_relative_vector_to_obs);")
        #  if self.config.has_bump_texture:
        #       self.data_source.fragment_shader_distort_coord(code)
        #       code.append(
        #           "vec3 parallax_offset = "
        #           "relative_vector_to_obs_norm * (tex%i.rgb * 2.0 - 1.0) * bump_height;" % self.bump_map_index)
        #       code.append("texcoord_tex%d.xyz -= parallax_offset;" % self.texture_index)
        self.data_source.fragment_shader(code)
        self.appearance.fragment_shader(code)
        if 'eye_normal' in self.config.fragment_requires and self.appearance.has_normal:
            if self.appearance.normal_texture_tangent_space:
                code += [
                    "eye_normal *= pixel_normal.z;",
                    "eye_normal += tangent * pixel_normal.x;",
                    "eye_normal += binormal * pixel_normal.y;",
                    "eye_normal = normalize(eye_normal);",
                ]
            else:
                code.append("eye_normal = pixel_normal;")
        if settings.shader_debug_fragment_shader == 'default':
            code.append("vec4 total_diffuse_color = vec4(0, 0, 0, 0);")
            code.append("vec3 total_emission_color = vec3(0, 0, 0);")
            self.lighting_model.fragment_shader(code)
            self.point_control.fragment_shader(code)
            code.append("vec4 total_color = total_diffuse_color + vec4(total_emission_color, 0.0);")
            for effect in self.after_effects:
                effect.fragment_shader(code)
        else:
            if settings.shader_debug_fragment_shader == 'diffuse':
                code.append("vec4 total_color = surface_color;")
            if settings.shader_debug_fragment_shader == 'normal':
                if 'eye_normal' in self.config.fragment_requires:
                    code.append("vec4 total_color = vec4((eye_normal + vec3(1.0)) / 2.0, 1.0);")
                else:
                    code.append("vec4 total_color = vec4(1.0);")
            elif settings.shader_debug_fragment_shader == 'normalmap':
                if 'eye_normal' in self.config.fragment_requires and self.appearance.has_normal:
                    code.append("vec4 total_color = vec4((pixel_normal + vec3(1.0)) / 2.0, 1.0);")
                else:
                    code.append("vec4 total_color = vec4(1.0);")
            elif settings.shader_debug_fragment_shader == 'picking':
                if self.config.color_picking:
                    code.append("vec4 total_color = color_picking;")
                else:
                    code.append("vec4 total_color = vec4(1.0);")
            elif settings.shader_debug_fragment_shader == 'shadows':
                code.append("float shadow = 1.0;")
                for shadow in self.shadows:
                    shadow.fragment_shader(code)
                code.append("vec4 total_color = vec4(1.0, shadow, shadow, 1.0);")
            elif settings.shader_debug_fragment_shader == 'heightmap':
                if self.data_source.has_source_for("height"):
                    code.append(
                        "vec4 total_color = vec4(vec3(%s) * %s + 0.5, 1.0);"
                        % (
                            self.data_source.get_source_for("height_heightmap", "texcoord0.xy"),
                            self.data_source.get_source_for("range_heightmap"),
                        )
                    )
                else:
                    code.append("vec4 total_color = vec4(0.0, 0.0, 0.0, 1.0);")
        if settings.shader_debug_coord:
            code.append("float line_width = %g;" % settings.shader_debug_coord_line_width)
            code.append(
                "total_color = "
                "mix(total_color, vec4(1, 0, 0, 1), clamp((line_width - texcoord0.x) / line_width, 0.0, 1.0));"
            )
            code.append(
                "total_color = "
                "mix(total_color, vec4(1, 0, 0, 1), clamp((texcoord0.x - 1.0 + line_width) / line_width, 0.0, 1.0));"
            )
            code.append(
                "total_color = "
                "mix(total_color, vec4(1, 0, 0, 1), clamp((line_width - texcoord0.y) / line_width, 0.0, 1.0));"
            )
            code.append(
                "total_color = "
                "mix(total_color, vec4(1, 0, 0, 1), clamp((texcoord0.y - 1.0 + line_width) / line_width, 0.0, 1.0));"
            )
        if settings.use_pbr:
            code.append("frag_color[0] = total_color;")
        else:
            code.append("frag_color[0] = clamp(total_color, 0.0, 1.0);")
        if self.version < 130:
            code.append("gl_FragColor = frag_color[0];")
        if self.config.color_picking:
            code.append("imageStore(oid_store, ivec2(gl_FragCoord.xy), color_picking);")


class RenderingShader(StructuredShader):

    def __init__(
        self,
        appearance=None,
        shadows=None,
        lighting_model=None,
        tessellation_control=None,
        vertex_control=None,
        point_control=None,
        instance_control=None,
        data_source=None,
        after_effects=None,
        use_model_texcoord=True,
        vertex_oids=False,
    ):
        StructuredShader.__init__(self)
        if appearance is None:
            appearance = TextureAppearance()
        appearance.set_shader(self)
        if shadows is None:
            shadows = []
        if lighting_model is None:
            lighting_model = ShadingLightingModel(LambertPhongLightingModel())
        lighting_model.set_shader(self)
        if vertex_control is None:
            vertex_control = DefaultVertexControl()
        if point_control is None:
            point_control = NoPointControl()
        if instance_control is None:
            instance_control = NoInstanceControl()
        if tessellation_control is not None:
            vertex_source = QuadTessellationVertexInput(tessellation_control.invert_v)
        else:
            vertex_source = DirectVertexInput()
        vertex_source.set_shader(self)
        if data_source is None:
            data_source = PandaShaderDataSource()
        data_source = CompositeShaderDataSource(data_source)
        if after_effects is None:
            after_effects = []
        self.appearance = appearance
        self.appearance.set_shader(self)
        self.shadows = shadows
        for shadow in self.shadows:
            shadow.set_shader(self)
            shadow.appearance = appearance
        self.lighting_model = lighting_model
        self.lighting_model.set_shader(self)
        self.vertex_control = vertex_control
        self.vertex_control.set_shader(self)
        self.point_control = point_control
        self.point_control.set_shader(self)
        self.instance_control = instance_control
        self.instance_control.set_shader(self)
        self.data_source = data_source
        self.data_source.set_shader(self)
        self.after_effects = after_effects
        self.appearance.data = self.data_source
        self.lighting_model.appearance = self.appearance
        self.vertex_oids = vertex_oids
        if tessellation_control is not None:
            self.tessellation_control = tessellation_control
            self.tessellation_control.set_shader(self)
            self.vertex_shader = TessellationVertexShader()
            self.tessellation_control_shader = TessellationShader(self, tessellation_control)
            self.tessellation_eval_shader = VertexShader(
                self,
                shader_type='eval',
                vertex_source=vertex_source,
                data_source=self.data_source,
                appearance=self.appearance,
                vertex_control=self.vertex_control,
                point_control=self.point_control,
                instance_control=self.instance_control,
                shadows=self.shadows,
                lighting_model=self.lighting_model,
            )
        else:
            self.tessellation_control = TessellationControl()
            self.tessellation_eval_shader = None
            self.vertex_shader = VertexShader(
                self,
                shader_type='vertex',
                vertex_source=vertex_source,
                data_source=self.data_source,
                appearance=self.appearance,
                vertex_control=self.vertex_control,
                point_control=self.point_control,
                instance_control=self.instance_control,
                shadows=self.shadows,
                lighting_model=self.lighting_model,
            )
        self.fragment_shader = FragmentShader(
            self,
            data_source=self.data_source,
            appearance=self.appearance,
            shadows=self.shadows,
            lighting_model=self.lighting_model,
            vertex_control=vertex_control,
            point_control=self.point_control,
            after_effects=self.after_effects,
        )

        self.nb_textures_coord = 0

        self.use_model_texcoord = use_model_texcoord
        self.color_picking = settings.color_picking

    def set_instance_control(self, instance_control):
        self.instance_control = instance_control
        # TODO: wrong if there is tessellation
        self.vertex_shader.instance_control = instance_control

    def add_shadows(self, shadow):
        self.shadows.append(shadow)
        shadow.shader = self
        shadow.appearance = self.appearance
        # As the list is referenced by the vertex and fragment shader no need to apply to fragment too...

    def remove_shadows(self, shape, appearance, shadow):
        if shadow in self.shadows:
            self.shadows.remove(shadow)
            shadow.shader = None
            shadow.appearance = None
        else:
            print("SHADOW NOT FOUND")
        # As the list is referenced by the vertex and fragment shader no need to apply to fragment too...

    def remove_all_shadows(self, shape, appearance):
        while self.shadows:
            shadow = self.shadows.pop()
            shadow.shader = None
        # As the list is referenced by the vertex and fragment shader no need to apply to fragment too...

    def add_after_effect(self, after_effect):
        self.after_effects.append(after_effect)
        # As the list is referenced by the fragment shader no need to apply to fragment too...

    def remove_after_effect(self, after_effect):
        self.after_effects.remove(after_effect)
        # As the list is referenced by the fragment shader no need to apply to fragment too...

    def create_shader_configuration(self, appearance):
        self.vertex_requires = set()
        self.vertex_provides = set()
        self.fragment_requires = set()
        self.fragment_provides = set()

        self.nb_textures_coord = 1

        self.data_source.create_shader_configuration(appearance)
        self.appearance.create_shader_configuration(appearance)
        self.lighting_model.create_shader_configuration(appearance)

        #         if self.has_bump_texture:
        #             self.fragment_uses_vertex = True
        #             self.use_normal = True
        #             self.use_tangent = True
        #             self.relative_vector_to_obs = True

        component: ShaderComponent
        components = (
            self.appearance,
            *self.after_effects,
            self.vertex_control,
            self.point_control,
            self.instance_control,
            self.lighting_model,
            *self.shadows,
        )
        for component in components:
            self.vertex_requires.update(component.vertex_requires)
            self.vertex_provides.update(component.vertex_provides)

        component: ShaderComponent
        for component in (self.appearance, *self.after_effects, self.lighting_model, *self.shadows):
            self.fragment_requires.update(component.fragment_requires)
            self.fragment_provides.update(component.fragment_provides)

        for fragment_required in self.fragment_requires:
            if fragment_required not in self.fragment_provides:
                self.vertex_requires.add(fragment_required)

        if 'eye_vertex' in self.vertex_requires:
            self.vertex_requires.add('world_vertex')
        if 'world_normal' in self.fragment_requires:
            if settings.use_multisampling and settings.multisamples > 0 and settings.shader_normals_use_centroid:
                self.fragment_requires.add('centroid_world_normal')
        if 'world_normal' in self.vertex_requires:
            self.vertex_requires.add('model_normal')
        if 'eye_normal' in self.vertex_requires:
            self.vertex_requires.add('model_normal')

    def get_shader_id(self):
        if settings.shader_debug_fragment_shader == 'default':
            name = "basic"
        else:
            name = "debug-" + settings.shader_debug_fragment_shader
        if settings.shader_debug_coord:
            name += "-debug-coord"
        ap_id = self.appearance.get_id()
        if ap_id:
            name += "-" + ap_id
        for shadow in self.shadows:
            shadow_id = shadow.get_id()
            if shadow_id:
                name += "-" + shadow_id
        lm_id = self.lighting_model.get_id()
        if lm_id:
            name += "-" + lm_id
        vc_id = self.vertex_control.get_id()
        if vc_id:
            name += "-" + vc_id
        pc_id = self.point_control.get_id()
        if pc_id:
            name += "-" + pc_id
        ic_id = self.instance_control.get_id()
        if ic_id:
            name += "-" + ic_id
        ds_id = self.data_source.get_id()
        if ds_id:
            name += ds_id
        config = ''
        if not self.use_model_texcoord:
            config += 'g'
        if config:
            name += '-' + config
        tc_id = self.tessellation_control.get_id()
        if tc_id:
            name += '-' + tc_id
        if not self.color_picking:
            name += "-ncp"
        return name

    def define_shader(self, shape, appearance):
        self.create_shader_configuration(appearance)
        # TODO: self.scattering.define_shader(shape, appearance)

    def get_user_parameters(self):
        group = StructuredShader.get_user_parameters(self)
        group.add_parameter(self.lighting_model.get_user_parameters())
        group.add_parameter(self.appearance.get_user_parameters())
        group.add_parameter(self.vertex_control.get_user_parameters())
        group.add_parameter(self.point_control.get_user_parameters())
        group.add_parameter(self.instance_control.get_user_parameters())
        group.add_parameter(self.data_source.get_user_parameters())
        for after_effect in self.after_effects:
            group.add_parameter(after_effect.get_user_parameters())
        group.add_parameter(self.tessellation_control.get_user_parameters())
        return group
