from __future__ import print_function
from __future__ import absolute_import

from panda3d.core import Shader, ShaderAttrib

from .cache import create_path_for
from . import settings

import hashlib
import os

class ShaderBase(object):
    dynamic_shader = False
    shaders_cache = {}

    def __init__(self):
        self.shader = None

    def get_shader_id(self):
        return None

    def define_shader(self, shape, appearance):
        pass

    def find_shader(self, shader_id):
        if shader_id in self.shaders_cache:
            return self.shaders_cache[shader_id]
        return None

    def create_shader(self):
        pass

    def create_and_register_shader(self, shape, appearance, force=False):
        if force or self.shader is None or self.dynamic_shader:
            self.define_shader(shape, appearance)
            shader_id = self.get_shader_id()
            self.shader = self.find_shader(shader_id)
        if self.shader is None:
            self.shader = self.create_shader()
            shader_id = self.get_shader_id()
            self.shaders_cache[shader_id] = self.shader
        if self.shader is not None and shape is not None:
            shape.instance.setShader(self.shader)

    def apply(self, shape, appearance):
        if shape is None or shape.instance is None: return
        self.create_and_register_shader(shape, appearance, force=True)
        self.update_shader_shape_static(shape, appearance)
        if shape.patchable:
            for patch in shape.patches:
                self.update_shader_patch_static(shape, patch, appearance)
        else:
            self.update_shader_patch_static(shape, shape, appearance)

    def apply_patch(self, shape, patch, appearance):
        self.update_shader_patch_static(shape, patch, appearance)

    def update_shader_shape_static(self, shape, appearance):
        pass

    def update_shader_shape(self, shape, appearance):
        pass

    def update_shader_patch_static(self, shape, patch, appearance):
        pass

    def update_shader_patch(self, shape, patch, appearance):
        pass

    def update(self, shape, appearance):
        self.create_and_register_shader(shape, appearance)
        self.update_shader_shape(shape, appearance)
        if shape.patchable:
            for patch in shape.patches:
                self.update_shader_patch(shape, patch, appearance)
        else:
            self.update_shader_patch(shape, shape, appearance)

    def update_patch(self, shape, patch, appearance):
        self.update_shader_patch(shape, patch, appearance)

class AutoShader(ShaderBase):
    def apply(self, shape, appearance):
        pass

    def update(self, shape, appearance):
        pass

class FileShader(ShaderBase):
    def __init__(self, vertex='', fragment='', tess_control='', tess_evaluation=''):
        ShaderBase.__init__(self)
        self.vertex = vertex
        self.tess_control = tess_control
        self.tess_evaluation = tess_evaluation
        self.geometry = ''
        self.fragment = fragment

    def get_shader_id(self):
        return self.vertex + '-' + self.tess_control + '-' + self.tess_evaluation + '-' + self.fragment

    def create_shader(self):
        print("Loading shader", self.get_shader_id())
        return Shader.load(Shader.SL_GLSL,
                           vertex=self.vertex,
                           tess_control=self.tess_control,
                           tess_evaluation=self.tess_evaluation,
                           geometry=self.geometry,
                           fragment=self.fragment)

class ShaderProgram(object):
    def __init__(self, shader_type):
        self.shader_type = shader_type
        self.version = settings.shader_min_version
        self.functions = {}

    def clear_functions(self):
        self.functions = {}

    def add_function(self, code, name, func):
        if not name in self.functions:
            func(code)
            self.functions[name] = True

    def include(self, code, name, filename):
        if not name in self.functions:
            data = open(filename)
            code += data.readlines()
            self.functions[name] = True

    def pi(self, code):
        code.append("const float pi  = 3.14159265358;")

    def to_srgb(self, code):
        #See https://www.khronos.org/registry/OpenGL/extensions/EXT/EXT_framebuffer_sRGB.txt
        code.append('''
float to_srgb(float value) {
    if(value < 0.0031308) {
        return 12.92 * value;
    } else {
        return 1.055 * pow(value, 0.41666) - 0.055;
    }
}''')

    def encode_rgba(self, code):
        code.append('''
vec4 EncodeFloatRGBA( float v ) {
  //vec4 enc = vec4(1.0, 255.0, 65025.0, 16581375.0) * v;
  vec4 enc = vec4(1.0, 255.0, 65535.0, 16777215.0) * v;
  enc = fract(enc);
  enc -= enc.yzww * vec4(1.0/255.0, 1.0/255.0, 1.0/255.0, 0.0);
  return enc;
}''')

    def add_encode_rgba(self, code):
        self.add_function(code, 'EncodeFloatRGBA', self.encode_rgba)

    def decode_rgba(self, code):
        code.append('''
float DecodeFloatRGBA( vec4 rgba ) {
  //return dot( rgba, vec4(1.0, 1/255.0, 1/65025.0, 1/16581375.0) );
  return dot( rgba, vec4(1.0, 1/255.0, 1/65535.0, 1/16777215.0) );
}''')

    def add_decode_rgba(self, code):
        self.add_function(code, 'DecodeFloatRGBA', self.decode_rgba)

    def create_shader_version(self, code):
        if self.version is not None:
            code.append("#version %d" % self.version)

    def create_layout(self, code):
        pass

    def create_uniforms(self, code):
        pass

    def create_inputs(self, code):
        pass

    def create_outputs(self, code):
        pass

    def create_extra(self, code):
        self.add_function(code, 'pi', self.pi)

    def create_body(self, code):
        pass

    def generate_shader(self, dump=None, shader_id=''):
        code = []
        self.clear_functions()
        self.create_shader_version(code)
        code.append("// Shader layout ")
        self.create_layout(code)
        code.append("// Shader uniforms ")
        self.create_uniforms(code)
        code.append("// Shader inputs")
        self.create_inputs(code)
        code.append("// Shader outputs")
        self.create_outputs(code)
        self.create_extra(code)
        code.append("void main() {")
        self.create_body(code)
        code.append("}")
        shader = '\n'.join(code)
        if dump is not None:
            shaders_path = create_path_for('shaders')
            with open(os.path.join(shaders_path, "%s.%s.glsl" % (dump, self.shader_type)), "w") as shader_file:
                shader_file.write(shader)
        return shader

class StructuredShader(ShaderBase):
    def __init__(self):
        ShaderBase.__init__(self)
        self.version = None
        self.vertex_shader = None
        self.tesselation_control_shader = None
        self.tesselation_eval_shader = None
        self.geometry_shader = None
        self.fragment_shader = None

    def create_shader(self):
        shader_id = self.get_shader_id()
        if settings.dump_shaders:
            dump = hashlib.md5(shader_id.encode()).hexdigest()
            print("Creating shader %s (%s)" %(shader_id, dump))
        else:
            dump = None
            print("Creating shader", shader_id)

        if self.vertex_shader:
            vertex = self.vertex_shader.generate_shader(dump, shader_id)
        else:
            vertex = ''
        if self.tesselation_control_shader:
            tess_control = self.tesselation_control_shader.generate_shader(dump, shader_id)
        else:
            tess_control = ''
        if self.tesselation_eval_shader:
            tess_evaluation = self.tesselation_eval_shader.generate_shader(dump, shader_id)
        else:
            tess_evaluation = ''
        if self.geometry_shader:
            geometry = self.geometry_shader.generate_shader(dump, shader_id)
        else:
            geometry = ''
        if self.fragment_shader:
            fragment = self.fragment_shader.generate_shader(dump, shader_id)
        else:
            fragment = ''
        return Shader.make(Shader.SL_GLSL,
                           vertex=vertex,
                           tess_control=tess_control,
                           tess_evaluation=tess_evaluation,
                           geometry=geometry,
                           fragment=fragment)

class PassThroughVertexShader(ShaderProgram):
    def __init__(self, config):
        ShaderProgram.__init__(self, 'vertex')
        self.config = config

    def create_uniforms(self, code):
        code.append("uniform mat4x4 p3d_ModelViewProjectionMatrix;")

    def create_inputs(self, code):
        code.append("in vec4 p3d_Vertex;")

    def create_outputs(self, code):
        code.append("out vec4 uv;")

    def create_body(self, code):
        code.append("gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;")
        code.append("uv = gl_Position * 0.5 + 0.5;")

class PassThroughFragmentShader(ShaderProgram):
    def __init__(self, config):
        ShaderProgram.__init__(self, 'fragment')
        self.config = config

    def create_uniforms(self, code):
        code.append("uniform sampler2D color_buffer;")
        if self.config.hdr:
            code.append("uniform float exposure;")

    def create_inputs(self, code):
        code.append("in vec4 uv;")

    def create_outputs(self, code):
        code.append("out vec4 color;")

    def create_extra(self, code):
        self.add_function(code, 'to_srgb', self.to_srgb)

    def create_body(self, code):
        code.append("vec4 final_color = texture(color_buffer, uv.xy);")
        if self.config.hdr:
            code.append("final_color = 1.0 - exp(final_color * -exposure);")
        if self.config.gamma_correction:
            #code.append("color = vec4(pow(final_color.xyz, vec3(1.0/2.2)), final_color.a);")
            code.append("color = vec4(to_srgb(final_color.x), to_srgb(final_color.y), to_srgb(final_color.z), final_color.a);")
        else:
            code.append("color = final_color;")

class PostProcessShader(StructuredShader):
    def __init__(self, gamma_correction=False, hdr=False):
        StructuredShader.__init__(self)
        self.vertex_shader = PassThroughVertexShader(self)
        self.fragment_shader = PassThroughFragmentShader(self)
        self.gamma_correction = gamma_correction
        self.hdr = hdr

    def get_shader_id(self):
        return "postprocess"

class TesselationVertexShader(ShaderProgram):
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
                 instance_control,
                 lighting_model,
                 scattering):
        ShaderProgram.__init__(self, shader_type)
        if shader_type == 'eval' or vertex_control.use_double:
            self.version = max(410, self.version)
        self.version = max(instance_control.version, self.version)
        self.config = config
        self.vertex_source = vertex_source
        self.data_source = data_source
        self.appearance = appearance
        self.vertex_control = vertex_control
        self.instance_control = instance_control
        self.lighting_model = lighting_model
        self.scattering = scattering

    def create_layout(self, code):
        self.vertex_source.vertex_layout(code)

    def create_uniforms(self, code):
        code.append("uniform mat4 p3d_ProjectionMatrix;")
        code.append("uniform mat4 p3d_ModelMatrix;")
        code.append("uniform mat4 p3d_ViewMatrix;")
        code.append("uniform mat4 p3d_ModelViewMatrix;")
        if self.config.use_shadow:
            code.append("uniform mat4 trans_model_to_clip_of_sunLight;")
            code.append("uniform float shadow_bias;")
        if self.config.point_shader:
            code.append("uniform float near_plane_height;")
            if self.config.scale_point_static:
                code.append("uniform float size_scale;")
        self.vertex_control.vertex_uniforms(code)
        self.instance_control.vertex_uniforms(code)
        self.lighting_model.vertex_uniforms(code)
        self.scattering.vertex_uniforms(code)
        self.data_source.vertex_uniforms(code)
        self.appearance.vertex_uniforms(code)

    def create_inputs(self, code):
        self.vertex_source.vertex_inputs(code)
        self.lighting_model.vertex_inputs(code)
        self.scattering.vertex_inputs(code)
        self.instance_control.vertex_inputs(code)
        self.data_source.vertex_inputs(code)
        self.appearance.vertex_inputs(code)

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
        if self.config.fragment_uses_tangent:
            code.append("out vec3 binormal;")
            code.append("out vec3 tangent;")
        if self.config.relative_vector_to_obs:
            code.append("out vec3 relative_vector_to_obs;")
        for i in range(self.config.nb_textures_coord):
            code.append("out vec4 texcoord%i;" % i)
        if not self.config.use_model_texcoord:
            code.append("out vec4 texcoord0p;")
        if self.config.use_shadow:
            code.append("out vec4 lightcoord;")
        self.vertex_control.vertex_outputs(code)
        self.lighting_model.vertex_outputs(code)
        self.scattering.vertex_outputs(code)
        self.data_source.vertex_outputs(code)
        self.appearance.vertex_outputs(code)

    def create_extra(self, code):
        ShaderProgram.create_extra(self, code)
        self.data_source.vertex_extra(code)
        self.vertex_source.vertex_extra(code)
        self.vertex_control.vertex_extra(code)

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
        self.vertex_control.update_vertex(code)
        if self.config.use_normal:
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
                code.append("world_normal = vec3(normalize(p3d_ModelMatrix * model_normal4));")
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
        if self.config.use_shadow:
            code.append("vec4 lightclip = trans_model_to_clip_of_sunLight * (model_vertex4 + model_normal4 * shadow_bias);")
            code.append("lightcoord = lightclip * vec4(0.5, 0.5, 0.5, 1.0) + lightclip.w * vec4(0.5, 0.5, 0.5, 0.0);")
        if self.config.use_vertex:
            if self.config.model_vertex:
                code.append("model_vertex = model_vertex4.xyz / model_vertex4.w;")
            if self.config.world_vertex:
                code.append("world_vertex = world_vertex4.xyz / world_vertex4.w;")
            if self.config.eye_vertex:
                code.append("eye_vertex = eye_vertex4.xyz / eye_vertex4.w;")
        if self.config.point_shader:
            if self.config.scale_point:
                code.append("gl_PointSize = (size * near_plane_height) / gl_Position.w;")
            elif self.config.scale_point_static:
                code.append("gl_PointSize = size * size_scale;")
            else:
                code.append("gl_PointSize = size;")
        self.lighting_model.vertex_shader(code)
        self.scattering.vertex_shader(code)
        self.data_source.vertex_shader(code)
        self.appearance.vertex_shader(code)

class TesselationShader(ShaderProgram):
    def __init__(self, config, tesselation_control):
        ShaderProgram.__init__(self, 'control')
        self.version = 410
        self.config = config
        self.tesselation_control = tesselation_control

    def create_layout(self, code):
        self.tesselation_control.vertex_layout(code)

    def create_uniforms(self, code):
        self.tesselation_control.vertex_uniforms(code)

    def create_inputs(self, code):
        self.tesselation_control.vertex_inputs(code)

    def create_outputs(self, code):
        self.tesselation_control.vertex_outputs(code)

    def create_extra(self, code):
        code.append("#define id gl_InvocationID")
        self.tesselation_control.vertex_extra(code)

    def create_body(self, code):
        code.append("if (id == 0) {")
        self.tesselation_control.vertex_shader(code)
        code.append("}")
        code.append("gl_out[id].gl_Position = gl_in[id].gl_Position;")

class FragmentShader(ShaderProgram):
    def __init__(self, config, data_source, appearance, lighting_model, scattering, after_effects):
        ShaderProgram.__init__(self, 'fragment')
        self.config = config
        self.data_source = data_source
        self.appearance = appearance
        self.lighting_model = lighting_model
        self.scattering = scattering
        self.after_effects = after_effects

    def create_uniforms(self, code):
        self.appearance.fragment_uniforms(code)
        self.data_source.fragment_uniforms(code)
#         if self.config.has_bump_texture:
#             code.append("uniform float bump_height;")
        if self.config.use_shadow:
            code.append("uniform sampler2DShadow depthmap;")
        self.lighting_model.fragment_uniforms(code)
        self.scattering.fragment_uniforms(code)
        for effect in self.after_effects:
            effect.fragment_uniforms(code)

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
        if self.config.fragment_uses_tangent:
            code.append("in vec3 binormal;")
            code.append("in vec3 tangent;")
        if self.config.relative_vector_to_obs:
            code.append("in vec3 relative_vector_to_obs;")
        if not self.config.point_shader:
            for i in range(self.config.nb_textures_coord):
                code.append("in vec4 texcoord%i;" % i)
        if not self.config.use_model_texcoord:
            code.append("in vec4 texcoord0p;")
        self.appearance.fragment_inputs(code)
        self.data_source.fragment_inputs(code)
        if self.config.use_shadow:
            code.append("in vec4 lightcoord;")
        self.lighting_model.fragment_inputs(code)
        self.scattering.fragment_inputs(code)

    def create_outputs(self, code):
        code.append("out vec4 frag_color;")

    def create_extra(self, code):
        ShaderProgram.create_extra(self, code)
        self.data_source.fragment_extra(code)
        self.appearance.fragment_extra(code)
        self.lighting_model.fragment_extra(code)
        self.scattering.fragment_extra(code)
        for effect in self.after_effects:
            effect.fragment_extra(code)

    def create_body(self, code):
        if self.config.point_shader:
            for i in range(self.config.nb_textures_coord):
                code.append("vec4 texcoord%i = vec4(gl_PointCoord, 0, 0);" % i)
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
                code.append("vec3 normal = normalize(world_normal);")
        self.data_source.fragment_shader(code)
        self.appearance.fragment_shader(code)
        if self.config.fragment_uses_normal and self.appearance.has_normal_texture:
            if self.appearance.normal_texture_tangent_space:
                code += [
                         "normal *= pixel_normal.z;",
                         "normal += tangent * pixel_normal.x;",
                         "normal += binormal * pixel_normal.y;",
                         "normal = normalize(normal);",
                         ]
            else:
                code.append("normal = pixel_normal;")
        if self.config.use_shadow:
            code.append("float shadow = texture(depthmap, lightcoord.xyz);")
        else:
            code.append("float shadow = 1.0;")
        code.append("vec4 total_diffuse_color = vec4(0, 0, 0, 0);")
        code.append("vec4 total_emission_color = vec4(0, 0, 0, 0);")
        self.lighting_model.fragment_shader(code)
        self.scattering.fragment_shader(code)
        code.append("vec4 total_color = total_diffuse_color + total_emission_color;")
        for effect in self.after_effects:
            effect.fragment_shader(code)
        code.append("frag_color = clamp(total_color, 0.0, 1.0);")

class BasicShader(StructuredShader):
    def __init__(self, appearance=None,
                 lighting_model=None,
                 scattering=None,
                 tesselation_control=None,
                 vertex_control=None,
                 instance_control=None,
                 data_source=None,
                 after_effects=None,
                 use_model_texcoord=True,
                 point_shader=False,
                 scale_point=False,
                 scale_point_static=False):
        StructuredShader.__init__(self)
        if appearance is None:
            appearance = TextureAppearance()
        appearance.set_shader(self)
        if lighting_model is None:
            lighting_model = LambertPhongLightingModel()
        if scattering is None:
            scattering = AtmosphericScattering()
        lighting_model.set_shader(self)
        if vertex_control is None:
            vertex_control = DefaultVertexControl()
        if instance_control is None:
            instance_control = NoInstanceControl()
        if tesselation_control is not None:
            vertex_source = QuadTesselationVertexInput(tesselation_control.invert_v, self)
        else:
            vertex_source = DirectVertexInput(self)
        if data_source is None:
            data_source = PandaTextureDataSource(self)
        data_source = MultiDataSource(data_source)
        if after_effects is None:
            after_effects = []
        self.appearance = appearance
        self.appearance.shader = self
        self.lighting_model = lighting_model
        self.lighting_model.shader = self
        self.scattering = scattering
        self.scattering.shader = self
        self.vertex_control = vertex_control
        self.vertex_control.shader = self
        self.instance_control = instance_control
        self.instance_control.shader = self
        self.data_source = data_source
        self.data_source.set_shader(self)
        self.after_effects = after_effects
        self.dynamic_shader = scattering.dynamic_shader
        self.appearance.data = self.data_source
        self.lighting_model.appearance = self.appearance
        if tesselation_control is not None:
            self.tesselation_control = tesselation_control
            self.vertex_shader = TesselationVertexShader()
            self.tesselation_control_shader = TesselationShader(self, tesselation_control)
            self.tesselation_eval_shader = VertexShader(self,
                                                        shader_type='eval',
                                                        vertex_source=vertex_source,
                                                        data_source=self.data_source,
                                                        appearance=self.appearance,
                                                        vertex_control=self.vertex_control,
                                                        instance_control=self.instance_control,
                                                        lighting_model=self.lighting_model,
                                                        scattering=self.scattering)
        else:
            self.tesselation_control = TesselationControl()
            self.vertex_shader = VertexShader(self,
                                              shader_type='vertex',
                                              vertex_source=vertex_source,
                                              data_source=self.data_source,
                                              appearance=self.appearance,
                                              vertex_control=self.vertex_control,
                                              instance_control=self.instance_control,
                                              lighting_model=self.lighting_model,
                                              scattering=self.scattering)
        self.fragment_shader = FragmentShader(self,
                                              data_source=self.data_source,
                                              appearance=self.appearance,
                                              lighting_model=self.lighting_model,
                                              scattering=self.scattering,
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
        self.fragment_uses_tangent = False
        self.use_shadow = False
        self.use_model_texcoord = use_model_texcoord
        #TODO: Should be moved to a Point Shader
        self.point_shader = point_shader
        self.scale_point = scale_point
        self.scale_point_static = scale_point_static
        self.size_scale = 1.0

    def set_instance_control(self, instance_control):
        self.instance_control = instance_control
        self.vertex_shader.instance_control = instance_control
        self.vertex_shader.version = max(self.vertex_shader.version, instance_control.version)

    def add_after_effect(self, after_effect):
        self.after_effects.append(after_effect)
        #As the list is referenced by the fragment shader no need to apply to fragment too...

    def create_shader_configuration(self, appearance):
        self.nb_textures_coord = 1

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

        if self.lighting_model.use_normal and self.appearance.has_normal_texture and self.appearance.normal_texture_tangent_space:
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

        if appearance.shadow is not None:
            self.use_shadow = True
            self.use_normal = True
            self.model_normal = True
        else:
            self.use_shadow = False

        if self.point_shader:
            pass
            #self.use_vertex = True
            #self.eye_vertex = True

    def get_shader_id(self):
        if self.point_shader:
            name = "point"
        else:
            name = "basic"
        if self.point_shader:
            if self.scale_point:
                name += "-s"
        ap_id = self.appearance.get_id()
        if ap_id:
            name += "-" + ap_id
        lm_id = self.lighting_model.get_id()
        if lm_id:
            name += "-" + lm_id
        sc_id = self.scattering.get_id()
        if sc_id:
            name += "-" + sc_id
        gc_id = self.vertex_control.get_id()
        if gc_id:
            name += "-" + gc_id
        ic_id = self.instance_control.get_id()
        if ic_id:
            name += "-" + ic_id
        ds_id = self.data_source.get_id()
        if ds_id:
            name += ds_id
        config = ''
        if self.use_shadow:
            config += 'h'
        if not self.use_model_texcoord:
            config += 'g'
        if config:
            name += '-' + config
        tc_id = self.tesselation_control.get_id()
        if tc_id:
            name += '-' + tc_id
        return name

    def define_shader(self, shape, appearance):
        self.create_shader_configuration(appearance)
        self.scattering.define_shader(shape, appearance)

    def update_shader_shape_static(self, shape, appearance):
        self.appearance.update_shader_shape_static(shape, appearance)
        self.tesselation_control.update_shader_shape_static(shape, appearance)
        self.lighting_model.update_shader_shape_static(shape, appearance)
        self.scattering.update_shader_shape_static(shape, appearance)
        self.vertex_control.update_shader_shape_static(shape, appearance)
        self.instance_control.update_shader_shape_static(shape, appearance)
        self.data_source.update_shader_shape_static(shape, appearance)
        for effect in self.after_effects:
            effect.update_shader_shape_static(shape, appearance)
#         if self.has_bump_texture:
#             shape.instance.setShaderInput("bump_height", appearance.bump_height / settings.scale)
        if self.use_shadow:
            shape.instance.setShaderInput('shadow_bias', appearance.shadow.bias)
            shape.instance.setShaderInput('depthmap', appearance.shadow.depthmap)
            shape.instance.setShaderInput("sunLight", appearance.shadow.cam)
        else:
            shape.instance.clearShaderInput('depthmap')
            shape.instance.clearShaderInput("sunLight")
        if self.point_shader:
            attrib = shape.instance.getAttrib(ShaderAttrib)
            attrib2 = attrib.setFlag(ShaderAttrib.F_shader_point_size, True)
            shape.instance.setAttrib(attrib2)

    def set_size_scale(self, size_scale):
        self.size_scale = size_scale

    def update_shader_shape(self, shape, appearance):
        self.appearance.update_shader_shape(shape, appearance)
        self.tesselation_control.update_shader_shape(shape, appearance)
        self.lighting_model.update_shader_shape(shape, appearance)
        self.scattering.update_shader_shape(shape, appearance)
        self.vertex_control.update_shader_shape(shape, appearance)
        self.data_source.update_shader_shape(shape, appearance)
        for effect in self.after_effects:
            effect.update_shader_shape(shape, appearance)
        if self.point_shader and self.scale_point_static:
            shape.instance.setShaderInput("size_scale", self.size_scale)

    def update_shader_patch_static(self, shape, patch, appearance):
        self.appearance.update_shader_patch_static(shape, patch, appearance)
        self.tesselation_control.update_shader_patch_static(shape, patch, appearance)
        self.lighting_model.update_shader_patch_static(shape, patch, appearance)
        self.scattering.update_shader_patch_static(shape, patch, appearance)
        self.vertex_control.update_shader_patch_static(shape, patch, appearance)
        self.data_source.update_shader_patch_static(shape, patch, appearance)
        for effect in self.after_effects:
            effect.update_shader_patch_static(shape, patch, appearance)

    def update_shader_patch(self, shape, patch, appearance):
        self.appearance.update_shader_patch(shape, patch, appearance)
        self.tesselation_control.update_shader_patch(shape, patch, appearance)
        self.lighting_model.update_shader_patch(shape, patch, appearance)
        self.scattering.update_shader_patch(shape, patch, appearance)
        self.vertex_control.update_shader_patch(shape, patch, appearance)
        self.data_source.update_shader_patch(shape, patch, appearance)
        for effect in self.after_effects:
            effect.update_shader_patch(shape, patch, appearance)

class ShaderComponent(object):
    use_vertex = False
    use_vertex_frag = False
    model_vertex = False
    world_vertex = False
    use_normal = False
    model_normal = False
    world_normal = False
    use_tangent = False
    dynamic_shader = False

    def __init__(self, shader=None):
        self.shader = shader

    def set_shader(self, shader):
        self.shader = shader

    def get_id(self):
        return ""

    def create_shader_configuration(self, appearance):
        pass

    def define_shader(self, shape, appearance):
        pass

    def vertex_layout(self, code):
        pass

    def vertex_uniforms(self, code):
        pass

    def vertex_inputs(self, code):
        pass

    def vertex_outputs(self, code):
        pass

    def vertex_extra(self, code):
        pass

    def vertex_shader(self, code):
        pass

    def fragment_uniforms(self, code):
        pass

    def fragment_inputs(self, code):
        pass

    def fragment_extra(self, code):
        pass

    def fragment_shader_decl(self, code):
        pass

    def fragment_shader_distort_coord(self, code):
        pass

    def fragment_shader(self, code):
        pass

    def update_shader_shape_static(self, shape, appearance):
        pass

    def update_shader_shape(self, shape, appearance):
        pass

    def update_shader_patch_static(self, shape, patch, appearance):
        pass

    def update_shader_patch(self, shape, patch, appearance):
        pass

class CustomShaderComponent(ShaderComponent):
    def __init__(self, component_id):
        self.component_id = component_id
        self.use_vertex = False
        self.use_vertex_frag = False
        self.model_vertex = False
        self.world_vertex = False
        self.use_normal = False
        self.model_normal = False
        self.world_normal = False
        self.use_tangent = False
        self.dynamic_shader = False
        self.use_double = False

        self.vertex_uniforms_data = []
        self.vertex_inputs_data = []
        self.vertex_outputs_data = []
        self.vertex_extra_data = []
        self.update_vertex_data = []
        self.update_normal_data = []
        self.vertex_shader_data = []
        self.fragment_uniforms_data = []
        self.fragment_inputs_data = []
        self.fragment_extra_data = []
        self.fragment_shader_decl_data = []
        self.fragment_shader_distort_coord_data = []
        self.fragment_shader_data = []

    def get_id(self):
        return self.component_id

    def vertex_uniforms(self, code):
        code += self.vertex_uniforms_data

    def vertex_inputs(self, code):
        code += self.vertex_inputs_data

    def vertex_outputs(self, code):
        code += self.vertex_outputs_data

    def vertex_extra(self, code):
        code += self.vertex_extra_data

    def update_vertex(self, code):
        code += self.update_vertex_data

    def update_normal(self, code):
        code += self.update_normal_data

    def vertex_shader(self, code):
        code += self.vertex_shader_data

    def fragment_uniforms(self, code):
        code += self.fragment_uniforms_data

    def fragment_inputs(self, code):
        code += self.fragment_inputs_data

    def fragment_extra(self, code):
        code += self.fragment_extra_data

    def fragment_shader_decl(self, code):
        code += self.fragment_shader_decl_data

    def fragment_shader_distort_coord(self, code):
        code += self.fragment_shader_distort_coord_data

    def fragment_shader(self, code):
        code += self.fragment_shader_data

class ShaderAppearance(ShaderComponent):
    def __init__(self, shader=None):
        ShaderComponent.__init__(self, shader)
        self.data = None
        self.has_surface_texture = False
        self.has_normal_texture = False
        self.normal_texture_tangent_space = False
        self.has_bump_texture = False

        self.has_specular = False
        self.has_specular_texture = False
        self.has_night_texture = False

        self.has_transparency = False

    def fragment_shader_decl(self, code):
        code.append("vec4 surface_color;")
        code.append("vec3 pixel_normal;")
        code.append("vec3 specular_factor;")
        code.append("vec3 night_color;")

    def fragment_uniforms(self, code):
        code.append("uniform vec4 p3d_ColorScale;")

class TextureAppearance(ShaderAppearance):
    def get_id(self):
        config = ""
        if self.has_surface_texture:
            config += "u"
        if self.has_normal_texture:
            config += "n"
        if self.has_bump_texture:
            config += "b"
        if self.has_specular:
            config += "s"
        if self.has_specular_texture:
            config += "S"
        if self.has_night_texture:
            config += "i"
        if self.has_transparency:
            config += "t"
        if self.has_vertex_color:
            config += 'v'
        if self.has_attribute_color:
            config += 'a'
        if self.has_material:
            config += 'm'
        return config

    def create_shader_configuration(self, appearance):
        self.has_surface_texture = appearance.texture is not None
        self.has_normal_texture = appearance.normal_map is not None
        self.normal_texture_tangent_space = appearance.normal_map_tangent_space
        self.has_bump_texture = appearance.bump_map is not None

        self.has_specular = appearance.specularColor is not None
        self.has_specular_texture = appearance.specular_map is not None or appearance.has_specular_mask
        self.has_night_texture = appearance.night_texture is not None

        self.has_transparency = appearance.transparency
        #TODO: should be in ShaderAppearance
        self.has_vertex_color = appearance.has_vertex_color
        self.has_attribute_color = appearance.has_attribute_color
        self.has_material = appearance.has_material

    def vertex_inputs(self, code):
        if self.has_vertex_color:
            code.append("in vec4 p3d_Color;")

    def vertex_outputs(self, code):
        if self.has_vertex_color:
            code.append("out vec4 vertex_color;")

    def vertex_shader(self, code):
        if self.has_vertex_color:
            code.append("vertex_color = p3d_Color;")

    def fragment_uniforms(self, code):
        ShaderAppearance.fragment_uniforms(self, code)
        if self.has_specular:
            code.append("uniform vec4 specular_color;")
            code.append("uniform float shininess;")
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

    def fragment_shader(self, code):
        if self.has_surface_texture:
            code.append("surface_color = %s;" % self.data.get_source_for('surface'))
        elif self.has_material:
            code.append("surface_color = p3d_Material.diffuse;")
        else:
            code.append("surface_color = vec4(1.0, 1.0, 1.0, 1.0);")
        if self.has_transparency:
            #TODO: technically binary transparency is alpha strictly lower than .5
            code.append("if (surface_color.a <= transparency_level) discard;")
        if self.has_normal_texture:
            code.append("pixel_normal = %s;" % self.data.get_source_for('normal'))
        if self.has_specular_texture:
            code.append("specular_factor = %s;" % self.data.get_source_for('specular'))
        else:
            code.append("specular_factor = vec3(1.0, 1.0, 1.0);")
        if self.has_night_texture:
            code.append("night_color = %s;" % self.data.get_source_for('night'))

    def update_shader_shape_static(self, shape, appearance):
        if self.has_specular:
            shape.instance.setShaderInput("specular_color", appearance.specularColor)
            shape.instance.setShaderInput("shininess", appearance.shininess)
        if self.has_transparency:
            shape.instance.setShaderInput("transparency_level", appearance.transparency_level)

class VertexInput(ShaderComponent):
    def __init__(self, config):
        ShaderComponent.__init__(self)
        self.config = config

class DirectVertexInput(VertexInput):
    def vertex_inputs(self, code):
        code.append("in vec4 p3d_Vertex;")
        if self.config.point_shader:
            code.append("in float size;")
        if self.config.use_normal or self.config.vertex_control.use_normal:
            code.append("in vec3 p3d_Normal;")
        if self.config.use_tangent:
            code.append("in vec3 p3d_Binormal;")
            code.append("in vec3 p3d_Tangent;")
        for i in range(self.config.nb_textures_coord):
            code.append("in vec4 p3d_MultiTexCoord%i;" % i)

    def vertex_shader(self, code):
        code.append("model_vertex4 = p3d_Vertex;")
        if self.config.use_normal or self.config.vertex_control.use_normal:
            code.append("model_normal4 = vec4(p3d_Normal, 0.0);")
        if self.config.use_tangent:
            code.append("model_binormal4 = vec4(p3d_Binormal, 0.0);")
            code.append("model_tangent4 = vec4(p3d_Tangent, 0.0);")
        if self.config.use_model_texcoord:
            for i in range(self.config.nb_textures_coord):
                code.append("model_texcoord%i = p3d_MultiTexCoord%i;" % (i, i))
        else:
            #TODO: Should be done here ?
            code.append("vec3 tmp = model_vertex4.xyz / model_vertex4.w;")
            code.append("float tmp_len = length(tmp);")
            code.append("float u = atan(tmp.y, tmp.x) / pi / 2 + 0.5;")
            code.append("float v = asin(tmp.z / tmp_len) / pi + 0.5;")
            code.append("model_texcoord0 = vec4(fract(u), v, 0, 1);")
            code.append("model_texcoord0p = vec4(fract(u + 0.5) - 0.5, v, 0, 1);")

class QuadTesselationVertexInput(VertexInput):
    def __init__(self, invert_v=True, shader=None):
        VertexInput.__init__(self, shader)
        self.invert_v = invert_v

    def vertex_layout(self, code):
        code.append("layout(quads, equal_spacing, ccw) in;")

    def interpolate(self, code):
        code += ['''
vec4 interpolate(in vec4 v0, in vec4 v1, in vec4 v2, in vec4 v3)
{
    vec4 a = mix(v0, v1, gl_TessCoord.x);
    vec4 b = mix(v3, v2, gl_TessCoord.x);
    return mix(a, b, gl_TessCoord.y);
}
''']

    def vertex_extra(self, code):
        self.interpolate(code)

    def vertex_shader(self, code):
        code += ['''
            model_vertex4 = interpolate(
                              gl_in[0].gl_Position,
                              gl_in[1].gl_Position,
                              gl_in[2].gl_Position,
                              gl_in[3].gl_Position);
''']
        #TODO: Retrieve normals from tesselator
        if self.config.use_normal or self.config.vertex_control.use_normal:
            code.append("model_normal4 = vec4(0.0, 0.0, 1.0, 0.0);")
        if self.config.use_tangent:
            code.append("model_binormal4 = vec4(1.0, 0.0, 0.0, 0.0);")
            code.append("model_tangent4 = vec4(0.0, 1.0, 0.0, 0.0);")
        for i in range(self.config.nb_textures_coord):
            if self.invert_v:
                code.append("model_texcoord%i = vec4(gl_TessCoord.x, 1.0 - gl_TessCoord.y, 0.0, 0.0);" % (i))
            else:
                code.append("model_texcoord%i = vec4(gl_TessCoord.x, gl_TessCoord.y, 0.0, 0.0);" % (i))

class TesselationControl(ShaderComponent):
    pass

class ConstantTesselationControl(TesselationControl):
    def __init__(self, invert_v=True, shader=None):
        TesselationControl.__init__(self, shader)
        #invert_v is not used in TesselationControl but in QuadTesselationVertexInput
        #It is configured here as this is the user class
        self.invert_v = invert_v

    def get_id(self):
        return "ctess"

    def vertex_layout(self, code):
        code.append("layout(vertices = 4) out;")

    def vertex_uniforms(self, code):
        code.append("uniform float TessLevelInner;")
        code.append("uniform vec4 TessLevelOuter;")

    def vertex_shader(self, code):
        code += ['''
        gl_TessLevelOuter[0] = TessLevelOuter[0];
        gl_TessLevelOuter[1] = TessLevelOuter[1];
        gl_TessLevelOuter[2] = TessLevelOuter[2];
        gl_TessLevelOuter[3] = TessLevelOuter[3];

        gl_TessLevelInner[0] = TessLevelInner;
        gl_TessLevelInner[1] = TessLevelInner;
''']

    def update_shader_patch(self, shape, patch, appearance):
        patch.instance.set_shader_input('TessLevelInner', patch.tesselation_inner_level)
        patch.instance.set_shader_input('TessLevelOuter', *patch.tesselation_outer_level)

class VertexControl(ShaderComponent):
    use_double = False
    def update_vertex(self, code):
        pass

    def update_normal(self, code):
        pass

class DefaultVertexControl(VertexControl):
    pass

class LargeObjectVertexControl(VertexControl):
    use_vertex = True
    world_vertex = True

    def get_id(self):
        return "lo"

    def vertex_uniforms(self, code):
        code.append("uniform float midPlane;")

    def update_vertex(self, code):
        code.append("world_vertex4 = p3d_ModelMatrix * model_vertex4;")
        code.append("float distance_to_obs = length(vec3(world_vertex4));")
        code.append("if (distance_to_obs > midPlane) {")
        code.append("  vec3 vector_to_point = world_vertex4.xyz / distance_to_obs;")
        code.append("  vec3 not_scaled = vector_to_point * midPlane;")
        code.append("  float scaled_distance = midPlane * (1.0 - midPlane/distance_to_obs);")
        code.append("  vec3 scaled = vector_to_point * scaled_distance;")
        code.append("  world_vertex4.xyz = not_scaled + scaled;")
        code.append("}")

class NormalizedCubeVertexControl(VertexControl):
    use_vertex = True

    def get_id(self):
        return "normcube"

    def vertex_uniforms(self, code):
        code.append("uniform vec3 patch_offset;")

    def update_vertex(self, code):
        code.append("model_vertex4 = vec4(normalize(model_vertex4.xyz), model_vertex4.w);")
        code.append("vec4 source_vertex4 = model_vertex4;")
        code.append("model_vertex4.xyz -= patch_offset;")

    def update_normal(self, code):
        code.append("model_normal4 = vec4(source_vertex4.xyz, 0.0);")
        if self.shader.use_tangent:
            code.append("model_tangent4 = vec4(source_vertex4.z, source_vertex4.y, -source_vertex4.x, 0.0);")
            code.append("model_binormal4 = vec4(source_vertex4.x, source_vertex4.z, -source_vertex4.y, 0.0);")

    def update_shader_patch_static(self, shape, patch, appearance):
        patch.instance.set_shader_input('patch_offset', patch.source_normal * patch.offset)

class SquaredDistanceCubeVertexControl(VertexControl):
    use_vertex = True

    def get_id(self):
        return "sqrtcube"

    def vertex_uniforms(self, code):
        code.append("uniform vec3 patch_offset;")

    def update_vertex(self, code):
        code.append("float x2 = model_vertex4.x * model_vertex4.x;")
        code.append("float y2 = model_vertex4.y * model_vertex4.y;")
        code.append("float z2 = model_vertex4.z * model_vertex4.z;")
        code.append("model_vertex4.x *= sqrt(1.0 - y2 * 0.5 - z2 * 0.5 + y2 * z2 / 3.0);")
        code.append("model_vertex4.y *= sqrt(1.0 - z2 * 0.5 - x2 * 0.5 + z2 * x2 / 3.0);")
        code.append("model_vertex4.z *= sqrt(1.0 - x2 * 0.5 - y2 * 0.5 + x2 * y2 / 3.0);")
        code.append("vec4 source_vertex4 = model_vertex4;")
        code.append("model_vertex4.xyz -= patch_offset;")

    def update_normal(self, code):
        code.append("model_normal4 = vec4(source_vertex4.xyz, 0.0);")
        if self.shader.use_tangent:
            code.append("model_tangent4 = vec4(source_vertex4.z, source_vertex4.y, -source_vertex4.x, 0.0);")
            code.append("model_binormal4 = vec4(source_vertex4.x, source_vertex4.z, -source_vertex4.y, 0.0);")

    def update_shader_patch_static(self, shape, patch, appearance):
        patch.instance.set_shader_input('patch_offset', patch.source_normal * patch.offset)

class DoubleSquaredDistanceCubeVertexControl(VertexControl):
    use_double = True
    use_vertex = True

    def get_id(self):
        return "sqrtcubedouble"

    def vertex_uniforms(self, code):
        code.append("uniform vec3 patch_offset;")

    def update_vertex(self, code):
        code.append("dvec4 double_model_vertex4 = dvec4(model_vertex4) + dvec4(0, 0, 1, 0);")
        code.append("double x2 = double_model_vertex4.x * double_model_vertex4.x;")
        code.append("double y2 = double_model_vertex4.y * double_model_vertex4.y;")
        code.append("double z2 = double_model_vertex4.z * double_model_vertex4.z;")

        code.append("double_model_vertex4.x *= sqrt(1.0 - y2 * 0.5 - z2 * 0.5 + y2 * z2 / 3.0);")
        code.append("double_model_vertex4.y *= sqrt(1.0 - z2 * 0.5 - x2 * 0.5 + z2 * x2 / 3.0);")
        code.append("double_model_vertex4.z *= sqrt(1.0 - x2 * 0.5 - y2 * 0.5 + x2 * y2 / 3.0);")
        code.append("double_model_vertex4.xyz -= dvec3(patch_offset);")
        code.append("model_vertex4 = vec4(double_model_vertex4);")

    def update_normal(self, code):
        code.append("model_normal4 = vec4(model_vertex4.xyz, 0.0);")

    def update_shader_patch_static(self, shape, patch, appearance):
        patch.instance.set_shader_input('patch_offset', patch.source_normal * patch.offset)

class InstanceControl(ShaderComponent):
    version = 0
    def __init__(self, max_instances):
        ShaderComponent.__init__(self)
        self.max_instances = max_instances

    def update_vertex(self, code):
        pass

    def update_normal(self, code):
        pass

class NoInstanceControl(InstanceControl):
    def __init__(self):
        InstanceControl.__init__(self, 0)

class OffsetScaleInstanceControl(InstanceControl):
    version = 140
    use_vertex = True
    world_vertex = True
    def get_id(self):
        return "offset%d" % self.max_instances

    def vertex_uniforms(self, code):
        if settings.instancing_use_tex:
            code.append("uniform samplerBuffer instances_offset;")
        else:
            code.append("uniform vec4 instances_offset[%d];" % self.max_instances)

    def update_vertex(self, code):
        if settings.instancing_use_tex:
            code.append("vec4 offset_data = texelFetch(instances_offset, gl_InstanceID);")
        else:
            code.append("vec4 offset_data = instances_offset[gl_InstanceID];")
        code.append("world_vertex4 = p3d_ModelMatrix * vec4(model_vertex4.xyz * offset_data.w, model_vertex4.w);")
        code.append("world_vertex4 = world_vertex4 + vec4(offset_data.xyz, 0.0);")

    def update_shader_shape_static(self, shape, appearance):
        if appearance.offsets is not None:
            shape.instance.set_shader_input('instances_offset', appearance.offsets)

class DataSource(ShaderComponent):
    def get_source_for(self, source, params=None, error=True):
        if error: print("Unknown source '%s' requested" % source)
        return ''

class MultiDataSource(DataSource):
    def __init__(self, sources=None, shader=None):
        DataSource.__init__(self, shader)
        if sources is None:
            self.sources = []
        elif isinstance(sources, list):
            self.sources = sources
        else:
            self.sources = [sources]

    def set_shader(self, shader):
        self.shader = shader
        for source in self.sources:
            source.set_shader(shader)

    def get_id(self):
        str_id = ""
        for source in self.sources:
            src_id = source.get_id()
            if src_id:
                str_id += '-'
                str_id += src_id
        return str_id

    def create_shader_configuration(self, appearance):
        for source in self.sources:
            source.create_shader_configuration(appearance)

    def get_source_for(self, source_id, params=None, error=True):
        for source in self.sources:
            value = source.get_source_for(source_id, params, False)
            if value != '':
                return value
        if error: print("Unknown source '%s' requested" % source_id)
        return ''

    def vertex_layout(self, code):
        for source in self.sources:
            source.vertex_layout(code)

    def vertex_uniforms(self, code):
        for source in self.sources:
            source.vertex_uniforms(code)

    def vertex_inputs(self, code):
        for source in self.sources:
            source.vertex_inputs(code)

    def vertex_outputs(self, code):
        for source in self.sources:
            source.vertex_outputs(code)

    def vertex_extra(self, code):
        for source in self.sources:
            source.vertex_extra(code)

    def vertex_shader(self, code):
        for source in self.sources:
            source.vertex_shader(code)

    def fragment_uniforms(self, code):
        for source in self.sources:
            source.fragment_uniforms(code)

    def fragment_inputs(self, code):
        for source in self.sources:
            source.fragment_inputs(code)

    def fragment_extra(self, code):
        for source in self.sources:
            source.fragment_extra(code)

    def fragment_shader_decl(self, code):
        for source in self.sources:
            source.fragment_shader_decl(code)

    def fragment_shader_distort_coord(self, code):
        for source in self.sources:
            source.fragment_shader_distort_coord(code)

    def fragment_shader(self, code):
        for source in self.sources:
            source.fragment_shader(code)

    def update_shader_shape_static(self, shape, appearance):
        for source in self.sources:
            source.update_shader_shape_static(shape, appearance)

    def update_shader_shape(self, shape, appearance):
        for source in self.sources:
            source.update_shader_shape(shape, appearance)

    def update_shader_patch_static(self, shape, patch, appearance):
        for source in self.sources:
            source.update_shader_patch_static(shape, patch, appearance)

    def update_shader_patch(self, shape, patch, appearance):
        for source in self.sources:
            source.update_shader_patch(shape, patch, appearance)

class PandaTextureDataSource(DataSource):
    def __init__(self, shader=None):
        DataSource.__init__(self, shader)
        self.tex_transform = False
        self.texture_index = 0
        self.normal_map_index = 0
        self.bump_map_index = 0
        self.specular_map_index = 0
        self.night_texture_index = 0
        self.nb_textures = 0
        self.has_surface_texture = False
        self.has_normal_texture = False
        self.has_bump_texture = False
        self.has_specular_texture = False
        self.has_specular_mask = False
        self.has_night_texture = False
        self.has_transparency = False

    def get_id(self):
        config = ""
        if self.has_surface_texture:
            config += "u"
        if self.has_normal_texture:
            config += "n"
        if self.has_bump_texture:
            config += "b"
        if self.has_specular_texture:
            config += "s"
        if self.has_specular_mask:
            config += "m"
        if self.has_night_texture:
            config += "i"
        if self.tex_transform:
            config += "r"
        return config

    def create_shader_configuration(self, appearance):
        self.tex_transform = appearance.tex_transform
        self.texture_index = appearance.texture_index
        self.normal_map_index = appearance.normal_map_index
        self.bump_map_index = appearance.bump_map_index
        self.specular_map_index = appearance.specular_map_index
        self.night_texture_index = appearance.night_texture_index
        self.nb_textures = appearance.nb_textures
        self.has_surface_texture = appearance.texture is not None
        self.has_normal_texture = appearance.normal_map is not None
        self.has_bump_texture = appearance.bump_map is not None
        self.has_specular_texture = appearance.specular_map is not None
        self.has_specular_mask = appearance.has_specular_mask
        self.has_night_texture = appearance.night_texture
        self.has_transparency = appearance.transparency

    def create_tex_coord(self, texture_id, texture_coord):
        code = []
        if self.shader.use_model_texcoord:
            if self.tex_transform:
                code.append("vec4 texcoord_tex%d = texmat_%d * texcoord%d;" % (texture_id, texture_id, texture_coord))
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
                code.append("  texcoord_tex%d = texmat_%d * texcoord_tex%d;" % (texture_id, texture_id, texture_id))
            code.append("texcoord_tex%d.xyz /= texcoord_tex%d.w;" % (texture_id, texture_id))
        return code

    def create_sample_texture(self, texture_id):
        code = []
        code.append("vec4 tex%i = texture(p3d_Texture%i, texcoord_tex%d.xy);" % (texture_id, texture_id, texture_id))
        return code

    def fragment_uniforms(self, code):
        for i in range(self.nb_textures):
            code.append("uniform sampler2D p3d_Texture%i;" % i)
            if self.tex_transform:
                code.append("uniform mat4 texmat_%i;" % i)
        if self.has_night_texture:
            code.append("uniform float nightscale;")

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
        if self.has_night_texture:
            code += self.create_tex_coord(self.night_texture_index, texture_coord)

    def bump_sample(self, code):
        pass

    def get_source_for(self, source, params=None, error=True):
        if source == 'surface':
            if self.has_transparency:
                return "tex%i" % self.texture_index
            else:
                return "vec4(tex%i.rgb, 1.0)" % self.texture_index
        if source == 'normal':
            return "(vec3(tex%i) * 2.0) - 1.0" % self.normal_map_index
        if source == 'specular':
            if self.has_specular_texture:
                return "tex%i.rgb" % self.specular_map_index
            elif self.has_specular_mask:
                return "tex%i.aaa" % self.texture_index
        if source == 'night':
            return "tex%i.rgb * nightscale" % self.night_texture_index
        if error: print("Unknown source '%s' requested" % source)
        return ''

    def fragment_shader(self, code):
        if self.has_surface_texture:
            code += self.create_sample_texture(self.texture_index)
        if self.has_normal_texture:
            code += self.create_sample_texture(self.normal_map_index)
        if self.has_specular_texture:
            code += self.create_sample_texture(self.specular_map_index)
        if self.has_night_texture:
            code += self.create_sample_texture(self.night_texture_index)

    def update_shader_patch_static(self, shape, patch, appearance):
        if self.tex_transform:
            #print("TEXMAT APPLY", patch.str_id())
            for stage in patch.instance.findAllTextureStages():
                if 'Normal' in stage.getName():
                    patch.instance.setShaderInput("texmat_%d" % self.normal_map_index, patch.instance.getTexTransform(stage).getMat())
                elif 'Bump' in stage.getName():
                    patch.instance.setShaderInput("texmat_%d" % self.bump_map_index, patch.instance.getTexTransform(stage).getMat())
                elif 'Surface' in stage.getName() or 'Transparent' in stage.getName() or 'Ring' in stage.getName() or 'default' in stage.getName():
                    patch.instance.setShaderInput("texmat_%d" % self.texture_index, patch.instance.getTexTransform(stage).getMat())
                elif 'Specular' in stage.getName():
                    patch.instance.setShaderInput("texmat_%d" % self.specular_map_index, patch.instance.getTexTransform(stage).getMat())
                elif 'Night' in stage.getName():
                    patch.instance.setShaderInput("texmat_%d" % self.night_texture_index, patch.instance.getTexTransform(stage).getMat())
                else:
                    print("Unknown stage", stage)

    def update_shader_shape_static(self, shape, appearance):
        if self.has_night_texture:
            shape.instance.setShaderInput("nightscale", 0.02)

class LightingModel(ShaderComponent):
    pass

class FlatLightingModel(LightingModel):
    def get_id(self):
        return "flat"

    def fragment_shader(self, code):
        if self.appearance.has_attribute_color:
            code.append("total_emission_color = p3d_Color;")
        elif self.appearance.has_vertex_color:
            code.append("total_emission_color = vertex_color;")
        elif self.appearance.has_material:
            code.append("total_emission_color = p3d_Material.emission;")
        else:
            code.append("total_emission_color = vec4(1, 1, 1, 1);")
        code.append("total_emission_color *= surface_color * p3d_ColorScale;")

class LambertPhongLightingModel(LightingModel):
    use_normal = True
    world_normal = True
    use_tangent = False

    def get_id(self):
        return "lambert"
 
    def fragment_uniforms(self, code):
        code.append("uniform float ambient_coef;")
        code.append("uniform vec3 light_dir;")
        code.append("uniform vec4 ambient_color;")
        code.append("uniform vec4 light_color;")
        if self.appearance.has_specular:
            code.append("uniform vec3 half_vec;")

    def fragment_shader(self, code):
        #TODO: should be done only using .rgb (or vec3) and apply alpha channel in the end
        if self.appearance.has_specular:
            code.append("float spec_angle = clamp(dot(normal, half_vec), 0.0, 1.0);")
            code.append("vec4 specular = light_color * pow(spec_angle, shininess);")
        code.append("vec4 ambient = ambient_color * ambient_coef;")
        code.append("float diffuse_angle = dot(normal, light_dir);")
        code.append("float diffuse_coef = clamp(diffuse_angle, 0.0, 1.0);")
        code.append("vec4 diffuse = light_color * shadow * diffuse_coef;")
        code.append("vec4 total_light = clamp((diffuse + (1.0 - diffuse_coef) * ambient), 0.0, 1.0);")
        code.append("total_light.a = 1.0;")
        code.append("total_diffuse_color = surface_color * total_light;")
        if self.appearance.has_material:
            code.append("total_diffuse_color *= p3d_Material.diffuse;")
        if self.appearance.has_specular:
            code.append("total_diffuse_color.rgb += specular.rgb * specular_factor.rgb * specular_color.rgb * shadow;")
        if self.appearance.has_night_texture:
            code.append("if (diffuse_angle < 0.0) {")
            code.append("  float emission_coef = clamp(sqrt(-diffuse_angle), 0.0, 1.0);")
            code.append("  total_emission_color.rgb = night_color.rgb * emission_coef;")
            code.append("}")

    def update_shader_shape(self, shape, appearance):
        light_dir = shape.owner.vector_to_star
        light_color = shape.owner.light_color
        shape.instance.setShaderInput("light_dir", *light_dir)
        shape.instance.setShaderInput("light_color", light_color)
        shape.instance.setShaderInput("ambient_coef", settings.corrected_global_ambient)
        shape.instance.setShaderInput("ambient_color", (1, 1, 1, 1))
        if self.appearance.has_specular:
            half_vec = shape.owner.vector_to_star + shape.owner.vector_to_obs
            half_vec.normalize()
            shape.instance.setShaderInput("half_vec", *half_vec)

class LunarLambertLightingModel(LightingModel):
    use_normal = True
    use_vertex = True
    use_vertex_frag = True
    world_vertex = True
    world_normal = True
    use_tangent = False

    def get_id(self):
        return "lunar"

    def fragment_uniforms(self, code):
        code.append("uniform float ambient_coef;")
        code.append("uniform vec3 light_dir;")
        code.append("uniform vec4 ambient_color;")
        code.append("uniform vec4 light_color;")

    def fragment_shader(self, code):
        code.append("vec4 ambient = ambient_color * ambient_coef;")
        code.append("float light_angle = dot(normal, light_dir);")
        code.append("vec4 diffuse = vec4(0.0, 0.0, 0.0, 1.0);")
        code.append("float diffuse_coef = 0.0;")
        code.append("if (light_angle > 0.0) {")
        code.append("  float view_angle = dot(normal, normalize(-world_vertex));")
        code.append("  diffuse_coef = clamp(light_angle / (max(view_angle, 0.001) + light_angle), 0.0, 1.0);")
        code.append("  diffuse = light_color * shadow * diffuse_coef;")
        code.append("}")
        code.append("vec4 total_light = clamp((diffuse + (1.0 - diffuse_coef) * ambient), 0.0, 1.0);")
        code.append("total_light.a = 1.0;")
        code.append("total_diffuse_color = surface_color * total_light;")
        if self.appearance.has_night_texture:
            code.append("if (light_angle < 0.0) {")
            code.append("  total_emission_color.rgb = night_color.rgb * clamp(sqrt(-light_angle), 0.0, 1.0);")
            code.append("}")

    def update_shader_shape(self, shape, appearance):
        light_dir = shape.owner.vector_to_star
        light_color = shape.owner.light_color
        shape.instance.setShaderInput("light_dir", *light_dir)
        shape.instance.setShaderInput("light_color", light_color)
        shape.instance.setShaderInput("ambient_coef", settings.corrected_global_ambient)
        shape.instance.setShaderInput("ambient_color", (1, 1, 1, 1))

class AtmosphericScattering(ShaderComponent):
    pass

class Fog(ShaderComponent):
    use_vertex = True
    world_vertex = True

    def __init__(self, fall_off, density, ground):
        ShaderComponent.__init__(self)
        self.fog_fall_off = fall_off
        self.fog_density = density
        self.fog_ground = ground

    def get_id(self):
        return "fog"

    def fragment_uniforms(self, code):
        code.append("uniform vec3 camera;")
        code.append("uniform float fogFallOff;")
        code.append("uniform float fogDensity;")
        code.append("uniform float fogGround;")

    def applyFog(self, code):
        code.append('''
vec3 applyFog(in vec3  pixelColor, in vec3 position)
{
    float cam_distance = abs(distance(camera, position));
    vec3 cam_to_point = normalize(position - camera);
    //float fogAmount = 1.0 - exp(-cam_distance * fogFallOff);
    float fogAmount = fogDensity / fogFallOff * exp(-(camera.z - fogGround) * fogFallOff) * (1.0 - exp(-cam_distance * cam_to_point.z * fogFallOff )) / cam_to_point.z;
    //float fogAmount = fogDensity / fogFallOff * (exp(-(camera.z - fogGround) * fogFallOff) - exp(-(camera.z - fogGround + cam_distance * cam_to_point.z) * fogFallOff )) / cam_to_point.z;
    float sunAmount = max( dot( cam_to_point, light_dir ), 0.0 );
    vec3 fogColor = vec3(0.5, 0.6, 0.7);
    vec3 sunColor = vec3(1.0, 0.9, 0.7);
    vec3  mixColor = mix( fogColor, sunColor, pow(sunAmount, 8.0));
    return mix(pixelColor, mixColor, clamp(fogAmount, 0, 1));
}
''')

    def fragment_extra(self, code):
        self.applyFog(code)

    def fragment_shader(self, code):
        code.append('    total_color.xyz = applyFog(total_color.xyz, world_vertex);')

    def update_shader_shape_static(self, shape, appearance):
        shape.instance.set_shader_input("fogFallOff", self.fog_fall_off)
        shape.instance.set_shader_input("fogDensity", self.fog_density)
        shape.instance.set_shader_input("fogGround", self.fog_ground)
