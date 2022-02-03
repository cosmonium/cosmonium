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


from .base import ShaderProgram, StructuredShader
from .appearance import TextureAppearance
from .data_source.base import CompositeShaderDataSource
from .data_source.panda import PandaDataSource
from .instancing import NoInstanceControl
from .lighting.lambert import LambertPhongLightingModel
from .point_control import NoPointControl
from .scattering import AtmosphericScattering
from .tesselation import QuadTessellationVertexInput, TessellationControl
from .vertex_control.vertex_control import DefaultVertexControl
from .vertex_input import DirectVertexInput
from .. import settings

class TessellationVertexShader(ShaderProgram):
    def __init__(self):
        ShaderProgram.__init__(self, 'vertex')

    def create_inputs(self, code):
        code.append("in vec4 p3d_Vertex;")

    def create_body(self, code):
        code.append("gl_Position = p3d_Vertex;")

class VertexShader(ShaderProgram):
    def __init__(self,
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
                 scattering):
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
        self.scattering = scattering

    def create_layout(self, code):
        self.vertex_source.vertex_layout(code)

    def create_uniforms(self, code):
        code.append("uniform mat4 p3d_ProjectionMatrix;")
        code.append("uniform mat4 p3d_ModelMatrix;")
        if settings.use_double:
            code.append("uniform mat4 p3d_ModelMatrixInverseTranspose;")
        code.append("uniform mat4 p3d_ViewMatrix;")
        code.append("uniform mat4 p3d_ModelViewMatrix;")
        self.vertex_control.vertex_uniforms(code)
        self.point_control.vertex_uniforms(code)
        self.instance_control.vertex_uniforms(code)
        for shadow in self.shadows:
            shadow.vertex_uniforms(code)
        self.lighting_model.vertex_uniforms(code)
        self.scattering.vertex_uniforms(code)
        self.data_source.vertex_uniforms(code)
        self.appearance.vertex_uniforms(code)

    def create_inputs(self, code):
        self.vertex_source.vertex_inputs(code)
        for shadow in self.shadows:
            shadow.vertex_inputs(code)
        self.lighting_model.vertex_inputs(code)
        self.scattering.vertex_inputs(code)
        self.point_control.vertex_inputs(code)
        self.instance_control.vertex_inputs(code)
        self.data_source.vertex_inputs(code)
        self.appearance.vertex_inputs(code)
        if self.config.color_picking and self.config.vertex_oids:
            code.append("in vec4 oid;")

    def create_outputs(self, code):
        if self.config.fragment_uses_vertex:
            if self.config.model_vertex:
                code.append("out vec3 model_vertex;")
            if self.config.world_vertex:
                code.append("out vec3 world_vertex;")
        if self.config.fragment_uses_normal:
            if self.config.model_normal:
                code.append("out vec3 model_normal;")
            if self.config.world_normal:
                code.append("out vec3 world_normal;")
                if self.config.normals_use_centroid:
                    code.append("centroid out vec3 centroid_world_normal;")
        if self.config.fragment_uses_tangent:
            code.append("out vec3 binormal;")
            code.append("out vec3 tangent;")
        if self.config.relative_vector_to_obs:
            code.append("out vec3 relative_vector_to_obs;")
        for i in range(self.config.nb_textures_coord):
            code.append("out vec4 texcoord%i;" % i)
        if not self.config.use_model_texcoord:
            code.append("out vec4 texcoord0p;")
        self.vertex_control.vertex_outputs(code)
        self.point_control.vertex_outputs(code)
        for shadow in self.shadows:
            shadow.vertex_outputs(code)
        self.lighting_model.vertex_outputs(code)
        self.scattering.vertex_outputs(code)
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
        for shadow in self.shadows:
            shadow.vertex_extra(code)

    def create_body(self, code):
        code.append("vec4 model_vertex4;")
        if self.config.use_normal or self.config.vertex_control.use_normal:
            code.append("vec4 model_normal4;")
        if self.config.use_tangent:
            code.append("vec4 model_binormal4;")
            code.append("vec4 model_tangent4;")
        for i in range(self.config.nb_textures_coord):
            code.append("vec4 model_texcoord%i;" % i)
        if not self.config.use_model_texcoord:
            code.append("vec4 model_texcoord0p;")
        self.vertex_source.vertex_shader(code)
        if self.config.use_vertex:
            if self.config.world_vertex:
                code.append("vec4 world_vertex4;")
            if self.config.eye_vertex:
                code.append("vec4 eye_vertex4;")
            if not self.config.fragment_uses_vertex:
                if self.config.model_vertex:
                    code.append("vec3 model_vertex;")
                if self.config.world_vertex:
                    code.append("vec3 world_vertex;")
                if self.config.eye_vertex:
                    code.append("vec3 eye_vertex;")
        if self.config.use_normal and not self.config.fragment_uses_normal:
            if self.config.model_normal:
                code.append("vec3 model_normal;")
            if self.config.world_normal:
                code.append("vec3 world_normal;")
        if not self.config.fragment_uses_tangent:
            code.append("vec3 binormal;")
            code.append("vec3 tangent;")

        self.point_control.vertex_shader_decl(code)
        self.appearance.vertex_shader_decl(code)
        self.data_source.vertex_shader_decl(code)

        if self.vertex_control.has_vertex:
            self.vertex_control.update_vertex(code)
        if self.config.use_normal and self.vertex_control.has_normal:
            self.vertex_control.update_normal(code)
        if self.config.use_vertex and self.config.world_vertex and not (self.vertex_control.world_vertex or self.instance_control.world_vertex):
            code.append("world_vertex4 = p3d_ModelMatrix * model_vertex4;")
            if self.config.eye_vertex:
                code.append("eye_vertex4 = p3d_ViewMatrix * world_vertex4;")
        self.instance_control.update_vertex(code)
        if self.config.use_normal:
            self.instance_control.update_normal(code)
        if self.vertex_control.world_vertex or self.instance_control.world_vertex:
            code.append("gl_Position = p3d_ProjectionMatrix * (p3d_ViewMatrix * world_vertex4);")
        else:
            code.append("gl_Position = p3d_ProjectionMatrix * (p3d_ModelViewMatrix * model_vertex4);")
        if self.config.use_normal:
            if self.config.model_normal:
                code.append("model_normal = model_normal4.xyz;")
            if self.config.world_normal:
                if settings.use_double:
                    code.append("world_normal = vec3(normalize(p3d_ModelMatrixInverseTranspose * model_normal4));")
                else:
                    code.append("world_normal = vec3(normalize(p3d_ModelMatrix * model_normal4));")
                if self.config.fragment_uses_normal and self.config.normals_use_centroid:
                    code.append("centroid_world_normal = world_normal;")
        if self.config.use_tangent or self.config.fragment_uses_tangent:
            code.append("tangent = vec3(normalize(p3d_ModelMatrix * model_tangent4));")
            code.append("binormal = vec3(normalize(p3d_ModelMatrix * model_binormal4));")
        if self.config.relative_vector_to_obs:
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
        if self.config.use_vertex:
            if self.config.model_vertex:
                code.append("model_vertex = model_vertex4.xyz / model_vertex4.w;")
            if self.config.world_vertex:
                code.append("world_vertex = world_vertex4.xyz / world_vertex4.w;")
            if self.config.eye_vertex:
                code.append("eye_vertex = eye_vertex4.xyz / eye_vertex4.w;")
        for shadow in self.shadows:
            shadow.vertex_shader(code)
        self.point_control.vertex_shader(code)
        self.lighting_model.vertex_shader(code)
        self.scattering.vertex_shader(code)
        self.data_source.vertex_shader(code)
        self.appearance.vertex_shader(code)
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
    def __init__(self,
                 config,
                 data_source,
                 appearance,
                 shadows,
                 lighting_model,
                 scattering,
                 vertex_control,
                 point_control,
                 after_effects):
        ShaderProgram.__init__(self, 'fragment')
        self.config = config
        self.data_source = data_source
        self.appearance = appearance
        self.shadows = shadows
        self.lighting_model = lighting_model
        self.scattering = scattering
        self.vertex_control = vertex_control
        self.point_control = point_control
        self.after_effects = after_effects
        self.nb_outputs = 1

    def create_uniforms(self, code):
        self.appearance.fragment_uniforms(code)
        self.data_source.fragment_uniforms(code)
#         if self.config.has_bump_texture:
#             code.append("uniform float bump_height;")
        for shadow in self.shadows:
            shadow.fragment_uniforms(code)
        self.lighting_model.fragment_uniforms(code)
        self.scattering.fragment_uniforms(code)
        self.point_control.fragment_uniforms(code)
        for effect in self.after_effects:
            effect.fragment_uniforms(code)
        if self.config.color_picking and not self.config.vertex_oids:
            code.append("uniform vec4 color_picking;")
        if self.config.color_picking:
            code.append("layout (binding=0, rgba8) uniform writeonly image2D oid_store;")

    def create_inputs(self, code):
        if self.config.fragment_uses_vertex:
            if self.config.model_vertex:
                code.append("in vec3 model_vertex;")
            if self.config.world_vertex:
                code.append("in vec3 world_vertex;")
        if self.config.fragment_uses_normal:
            if self.config.model_normal:
                code.append("in vec3 model_normal;")
            if self.config.world_normal:
                code.append("in vec3 world_normal;")
                if self.config.normals_use_centroid:
                    code.append("centroid in vec3 centroid_world_normal;")
        if self.config.fragment_uses_tangent:
            code.append("in vec3 binormal;")
            code.append("in vec3 tangent;")
        if self.config.relative_vector_to_obs:
            code.append("in vec3 relative_vector_to_obs;")
        for i in range(self.config.nb_textures_coord):
            code.append("in vec4 texcoord%i;" % i)
        if not self.config.use_model_texcoord:
            code.append("in vec4 texcoord0p;")
        self.appearance.fragment_inputs(code)
        self.data_source.fragment_inputs(code)
        for shadow in self.shadows:
            shadow.fragment_inputs(code)
        self.lighting_model.fragment_inputs(code)
        self.scattering.fragment_inputs(code)
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
        self.scattering.fragment_extra(code)
        self.point_control.fragment_extra(code)
        for effect in self.after_effects:
            effect.fragment_extra(code)

    def create_body(self, code):
        if self.version < 130:
            code.append("vec4 frag_color[%d];" % self.nb_outputs)
        self.point_control.fragment_shader_decl(code)
        self.appearance.fragment_shader_decl(code)
        self.data_source.fragment_shader_decl(code)
        if self.config.relative_vector_to_obs:
            code.append("vec3 relative_vector_to_obs_norm = normalize(relative_vector_to_obs);")
#         if self.config.has_bump_texture:
#             self.data_source.fragment_shader_distort_coord(code)
#             code.append("vec3 parallax_offset = relative_vector_to_obs_norm * (tex%i.rgb * 2.0 - 1.0) * bump_height;" % self.bump_map_index)
#             code.append("texcoord_tex%d.xyz -= parallax_offset;" % self.texture_index)
        if self.config.fragment_uses_normal:
            if self.config.model_normal:
                code.append("vec3 model_normal = normalize(model_normal);")
            if self.config.world_normal:
                if self.config.normals_use_centroid:
                    code.append("vec3 normal;")
                    code.append("if (abs(dot(world_normal, world_normal) - 1) > 0.01) {")
                    code.append("  normal = normalize(centroid_world_normal);")
                    code.append("} else {")
                    code.append("  normal = normalize(world_normal);")
                    code.append("}")
                else:
                    code.append("vec3 normal = normalize(world_normal);")
                if self.appearance.has_normal:
                    code.append("vec3 shape_normal = normal;")
        self.data_source.fragment_shader(code)
        self.appearance.fragment_shader(code)
        if self.config.fragment_uses_normal and self.appearance.has_normal:
            if self.appearance.normal_texture_tangent_space:
                code += [
                         "normal *= pixel_normal.z;",
                         "normal += tangent * pixel_normal.x;",
                         "normal += binormal * pixel_normal.y;",
                         "normal = normalize(normal);",
                         ]
            else:
                code.append("normal = pixel_normal;")
        if settings.shader_debug_fragment_shader == 'default':
            code.append("vec4 total_diffuse_color = vec4(0, 0, 0, 0);")
            code.append("vec3 total_emission_color = vec3(0, 0, 0);")
            code.append("float shadow = 1.0;")
            for shadow in self.shadows:
                shadow.fragment_shader(code)
            self.lighting_model.fragment_shader(code)
            self.scattering.fragment_shader(code)
            self.point_control.fragment_shader(code)
            code.append("vec4 total_color = total_diffuse_color + vec4(total_emission_color, 0.0);")
            for effect in self.after_effects:
                effect.fragment_shader(code)
        else:
            if settings.shader_debug_fragment_shader == 'diffuse':
                code.append("vec4 total_color = surface_color;")
            if settings.shader_debug_fragment_shader == 'normal':
                if self.config.fragment_uses_normal:
                    code.append("vec4 total_color = vec4((normal + vec3(1.0)) / 2.0, 1.0);")
                else:
                    code.append("vec4 total_color = vec4(1.0);")
            elif settings.shader_debug_fragment_shader == 'normalmap':
                if self.config.fragment_uses_normal and self.appearance.has_normal:
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
                    code.append("vec4 total_color = vec4(vec3(%s) * %s + 0.5, 1.0);" % (self.data_source.get_source_for("height_heightmap", "texcoord0.xy"),
                                                                                        self.data_source.get_source_for("range_heightmap")))
                else:
                    code.append("vec4 total_color = vec4(0.0, 0.0, 0.0, 1.0);")
        if settings.shader_debug_coord:
            code.append("float line_width = %g;" % settings.shader_debug_coord_line_width)
            code.append("total_color = mix(total_color, vec4(1, 0, 0, 1), clamp((line_width - texcoord0.x) / line_width, 0.0, 1.0));")
            code.append("total_color = mix(total_color, vec4(1, 0, 0, 1), clamp((texcoord0.x - 1.0 + line_width) / line_width, 0.0, 1.0));")
            code.append("total_color = mix(total_color, vec4(1, 0, 0, 1), clamp((line_width - texcoord0.y) / line_width, 0.0, 1.0));")
            code.append("total_color = mix(total_color, vec4(1, 0, 0, 1), clamp((texcoord0.y - 1.0 + line_width) / line_width, 0.0, 1.0));")
        code.append("frag_color[0] = clamp(total_color, 0.0, 1.0);")
        if self.version < 130:
            code.append("gl_FragColor = frag_color[0];")
        if self.config.color_picking:
            code.append("imageStore(oid_store, ivec2(gl_FragCoord.xy), color_picking);")

class RenderingShader(StructuredShader):
    def __init__(self,
                 appearance=None,
                 shadows=None,
                 lighting_model=None,
                 scattering=None,
                 tessellation_control=None,
                 vertex_control=None,
                 point_control=None,
                 instance_control=None,
                 data_source=None,
                 after_effects=None,
                 use_model_texcoord=True,
                 vertex_oids=False):
        StructuredShader.__init__(self)
        if appearance is None:
            appearance = TextureAppearance()
        appearance.set_shader(self)
        if shadows is None:
            shadows = []
        if lighting_model is None:
            lighting_model = LambertPhongLightingModel()
        if scattering is None:
            scattering = AtmosphericScattering()
        lighting_model.set_shader(self)
        if vertex_control is None:
            vertex_control = DefaultVertexControl()
        if point_control is None:
            point_control = NoPointControl()
        if instance_control is None:
            instance_control = NoInstanceControl()
        if tessellation_control is not None:
            vertex_source = QuadTessellationVertexInput(tessellation_control.invert_v, self)
        else:
            vertex_source = DirectVertexInput(self)
        if data_source is None:
            data_source = PandaDataSource(self)
        data_source = CompositeShaderDataSource(data_source)
        if after_effects is None:
            after_effects = []
        self.appearance = appearance
        self.appearance.shader = self
        self.shadows = shadows
        for shadow in self.shadows:
            shadow.shader = self
            shadow.appearance  = appearance
        self.lighting_model = lighting_model
        self.lighting_model.shader = self
        self.scattering = scattering
        self.scattering.shader = self
        self.vertex_control = vertex_control
        self.vertex_control.shader = self
        self.point_control = point_control
        self.point_control.shader = self
        self.instance_control = instance_control
        self.instance_control.shader = self
        self.data_source = data_source
        self.data_source.set_shader(self)
        self.after_effects = after_effects
        self.appearance.data = self.data_source
        self.lighting_model.appearance = self.appearance
        self.vertex_oids = vertex_oids
        if tessellation_control is not None:
            self.tessellation_control = tessellation_control
            self.tessellation_control.shader = self
            self.vertex_shader = TessellationVertexShader()
            self.tessellation_control_shader = TessellationShader(self, tessellation_control)
            self.tessellation_eval_shader = VertexShader(self,
                                                        shader_type='eval',
                                                        vertex_source=vertex_source,
                                                        data_source=self.data_source,
                                                        appearance=self.appearance,
                                                        vertex_control=self.vertex_control,
                                                        point_control=self.point_control,
                                                        instance_control=self.instance_control,
                                                        shadows=self.shadows,
                                                        lighting_model=self.lighting_model,
                                                        scattering=self.scattering)
        else:
            self.tessellation_control = TessellationControl()
            self.tessellation_eval_shader = None
            self.vertex_shader = VertexShader(self,
                                              shader_type='vertex',
                                              vertex_source=vertex_source,
                                              data_source=self.data_source,
                                              appearance=self.appearance,
                                              vertex_control=self.vertex_control,
                                              point_control=self.point_control,
                                              instance_control=self.instance_control,
                                              shadows=self.shadows,
                                              lighting_model=self.lighting_model,
                                              scattering=self.scattering)
        self.fragment_shader = FragmentShader(self,
                                              data_source=self.data_source,
                                              appearance=self.appearance,
                                              shadows=self.shadows,
                                              lighting_model=self.lighting_model,
                                              scattering=self.scattering,
                                              vertex_control=vertex_control,
                                              point_control=self.point_control,
                                              after_effects=self.after_effects)

        self.nb_textures_coord = 0

        self.use_vertex = False
        self.model_vertex = False
        self.world_vertex = False
        self.eye_vertex = False
        self.fragment_uses_vertex = False
        self.relative_vector_to_obs = False
        self.use_normal = False
        self.model_normal = False
        self.world_normal = False
        self.fragment_uses_normal = False
        self.use_tangent = False
        self.generate_binormal = False
        self.fragment_uses_tangent = False
        self.normals_use_centroid = False
        self.use_model_texcoord = use_model_texcoord
        self.color_picking = settings.color_picking

    def set_instance_control(self, instance_control):
        self.instance_control = instance_control
        #TODO: wrong if there is tessellation
        self.vertex_shader.instance_control = instance_control

    def set_scattering(self, scattering):
        self.scattering = scattering
        self.scattering.shader = self
        if self.tessellation_eval_shader is None:
            self.vertex_shader.scattering = scattering
        else:
            self.tessellation_eval_shader.scattering = scattering
        self.fragment_shader.scattering = scattering

    def remove_scattering(self):
        self.set_scattering(AtmosphericScattering())

    def add_shadows(self, shadow):
        self.shadows.append(shadow)
        shadow.shader = self
        shadow.appearance = self.appearance
        #As the list is referenced by the vertex and fragment shader no need to apply to fragment too...

    def remove_shadows(self, shape, appearance, shadow):
        if shadow in self.shadows:
            self.shadows.remove(shadow)
            shadow.shader = None
            shadow.appearance = None
        else:
            print("SHADOW NOT FOUND")
        #As the list is referenced by the vertex and fragment shader no need to apply to fragment too...

    def remove_all_shadows(self, shape, appearance):
        while self.shadows:
            shadow = self.shadows.pop()
            shadow.shader = None
        #As the list is referenced by the vertex and fragment shader no need to apply to fragment too...

    def add_after_effect(self, after_effect):
        self.after_effects.append(after_effect)
        #As the list is referenced by the fragment shader no need to apply to fragment too...

    def create_shader_configuration(self, appearance):
        self.nb_textures_coord = 1

        self.normals_use_centroid = settings.use_multisampling and settings.multisamples > 0 and settings.shader_normals_use_centroid
        self.data_source.create_shader_configuration(appearance)

        self.appearance.create_shader_configuration(appearance)

#         if self.has_bump_texture:
#             self.fragment_uses_vertex = True
#             self.use_normal = True
#             self.use_tangent = True
#             self.relative_vector_to_obs = True

        if self.appearance.use_vertex:
            self.use_vertex = True
            if self.appearance.model_vertex:
                self.model_vertex = True
            if  self.appearance.world_vertex:
                self.world_vertex = True
            self.fragment_uses_vertex = True

        for effect in self.after_effects:
            if effect.use_vertex:
                self.use_vertex = True
                if effect.model_vertex:
                    self.model_vertex = True
                if  effect.world_vertex:
                    self.world_vertex = True
                self.fragment_uses_vertex = True

        if self.vertex_control.use_vertex:
            self.use_vertex = True
            if self.vertex_control.model_vertex:
                self.model_vertex = True
            if self.vertex_control.world_vertex:
                self.world_vertex = True
        if self.vertex_control.use_normal:
            self.use_normal = True
        if self.vertex_control.use_tangent:
            self.use_tangent = True

        if self.point_control.use_vertex:
            self.use_vertex = True
            if self.point_control.model_vertex:
                self.model_vertex = True
            if self.point_control.world_vertex:
                self.world_vertex = True

        if self.instance_control.use_vertex:
            self.use_vertex = True
            if self.instance_control.model_vertex:
                self.model_vertex = True
            if self.instance_control.world_vertex:
                self.world_vertex = True

        if self.lighting_model.use_vertex:
            self.use_vertex = True
            if self.lighting_model.model_vertex:
                self.model_vertex = True
            if self.lighting_model.world_vertex:
                self.world_vertex = True
            if self.lighting_model.use_vertex_frag:
                self.fragment_uses_vertex = True

        if self.lighting_model.use_normal:
            self.use_normal = True
            self.model_normal = self.lighting_model.model_normal
            self.world_normal = self.lighting_model.world_normal
            self.fragment_uses_normal = True

        if self.lighting_model.use_tangent:
            self.use_tangent = True
            self.fragment_uses_tangent = True

        if self.lighting_model.use_normal and self.appearance.has_normal and self.appearance.normal_texture_tangent_space:
            self.use_tangent = True
            self.fragment_uses_tangent = True

        if self.scattering.use_vertex:
            self.use_vertex = True
            if self.scattering.model_vertex:
                self.model_vertex = True
            if self.scattering.world_vertex:
                self.world_vertex = True
            if self.scattering.use_vertex_frag:
                self.fragment_uses_vertex = True

        for shadow in self.shadows:
            if shadow.use_vertex:
                self.use_vertex = True
                if shadow.model_vertex:
                    self.model_vertex = True
                if shadow.world_vertex:
                    self.world_vertex = True
                if shadow.use_vertex_frag:
                    self.fragment_uses_vertex = True

            if shadow.use_normal:
                self.use_normal = True
                if shadow.model_normal:
                    self.model_normal = True
                if shadow.world_normal:
                    self.world_normal = True

        #TODO: Should be done in data source
        if self.use_tangent:
            self.generate_binormal = appearance.generate_binormal

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
        sc_id = self.scattering.get_id()
        if sc_id:
            name += "-" + sc_id
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
        self.scattering.define_shader(shape, appearance)

    def get_user_parameters(self):
        group = StructuredShader.get_user_parameters(self)
        group.add_parameter(self.lighting_model.get_user_parameters())
        group.add_parameter(self.appearance.get_user_parameters())
        group.add_parameter(self.scattering.get_user_parameters())
        group.add_parameter(self.vertex_control.get_user_parameters())
        group.add_parameter(self.point_control.get_user_parameters())
        group.add_parameter(self.instance_control.get_user_parameters())
        group.add_parameter(self.data_source.get_user_parameters())
        for after_effect in self.after_effects:
            group.add_parameter(after_effect.get_user_parameters())
        group.add_parameter(self.tessellation_control.get_user_parameters())
        return group
