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
from __future__ import absolute_import

from panda3d.core import Shader, ShaderAttrib, LVector3d

from .utils import TransparencyBlend
from .cache import create_path_for
from .parameters import ParametersGroup
from . import settings

from math import asin
import hashlib
import os
import re

class ShaderBase(object):
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
        if force or self.shader is None:
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
        if not shape.instance_ready:
            print("shader update called on non ready shape instance")
        self.create_and_register_shader(shape, appearance)
        self.update_shader_shape(shape, appearance)
        if shape.patchable:
            for patch in shape.patches:
                if not shape.instance_ready:
                    print("shader update called on non ready patch instance")
                self.update_shader_patch(shape, patch, appearance)
        else:
            self.update_shader_patch(shape, shape, appearance)

    def update_patch(self, shape, patch, appearance):
        self.update_shader_patch(shape, patch, appearance)

    def get_user_parameters(self):
        return None

class AutoShader(ShaderBase):
    def set_instance_control(self, instance_control):
        print("AutoShader: set_instance_control not supported")

    def set_scattering(self, scattering):
        print("AutoShader: set_scattering not supported")

    def add_shadows(self, shadows):
        print("AutoShader: add_shadows not supported")

    def remove_shadows(self, shape, appearance, shadow):
        pass

    def clear_shadows(self, shape, appearance):
        pass

    def add_after_effect(self, after_effect):
        print("AutoShader: add_after_effect not supported")

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
        self.version = settings.shader_version
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
            if self.version >= 300 and settings.core_profile:
                code.append("#define texture2D texture")

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

    def use_legacy_in(self, code):
        new_code = []
        if self.shader_type == 'vertex':
            new_out = "attribute "
        else:
            new_out = "varying "
        regex = re.compile("^\s*in\s+")
        for line in code:
            new_line = regex.sub(new_out, line)
            new_code.append(new_line)
        return new_code

    def use_legacy_out(self, code):
        if self.shader_type != 'vertex':
            return code
        new_code = []
        regex = re.compile("^\s*out\s+")
        for line in code:
            new_line = regex.sub("varying ", line)
            new_code.append(new_line)
        return new_code

    def generate_shader(self, dump=None, shader_id=''):
        code = []
        self.clear_functions()
        self.create_shader_version(code)
        code.append("// Shader layout ")
        self.create_layout(code)
        code.append("// Shader uniforms ")
        self.create_uniforms(code)
        code.append("// Shader inputs")
        inputs = []
        self.create_inputs(inputs)
        if self.version < 130:
            inputs = self.use_legacy_in(inputs)
        code += inputs
        code.append("// Shader outputs")
        outputs = []
        self.create_outputs(outputs)
        if self.version < 130:
            outputs = self.use_legacy_out(outputs)
        code += outputs
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

    def get_user_parameters(self):
        return None

class StructuredShader(ShaderBase):
    def __init__(self):
        ShaderBase.__init__(self)
        self.vertex_shader = None
        self.tessellation_control_shader = None
        self.tessellation_eval_shader = None
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
        if self.tessellation_control_shader:
            tess_control = self.tessellation_control_shader.generate_shader(dump, shader_id)
        else:
            tess_control = ''
        if self.tessellation_eval_shader:
            tess_evaluation = self.tessellation_eval_shader.generate_shader(dump, shader_id)
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

    def get_user_parameters(self):
        params = []
        if self.vertex_shader:
            params += self.vertex_shader.get_user_parameters()
        if self.tessellation_control_shader:
            params += self.tessellation_control_shader.get_user_parameters()
        if self.tessellation_eval_shader:
            params += self.tessellation_eval_shader.get_user_parameters()
        if self.geometry_shader:
            params += self.geometry_shader.get_user_parameters()
        if self.fragment_shader:
            params += self.fragment_shader.get_user_parameters()
        return params

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
        code.append("vec4 final_color = texture2D(color_buffer, uv.xy);")
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
                 point_control,
                 after_effects):
        ShaderProgram.__init__(self, 'fragment')
        self.config = config
        self.data_source = data_source
        self.appearance = appearance
        self.shadows = shadows
        self.lighting_model = lighting_model
        self.scattering = scattering
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
                if self.config.fragment_uses_normal:
                    code.append("vec4 total_color = vec4((pixel_normal + vec3(1.0)) / 2.0, 1.0);")
                else:
                    code.append("vec4 total_color = vec4(1.0);")
            elif settings.shader_debug_fragment_shader == 'picking':
                if self.config.color_picking:
                    code.append("vec4 total_color = color_picking;")
                else:
                    code.append("vec4 total_color = vec4(1.0);")
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

class BasicShader(StructuredShader):
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
        data_source = MultiDataSource(data_source)
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
        self.fragment_uses_tangent = False
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

    def add_shadows(self, shadow):
        self.shadows.append(shadow)
        shadow.shader = self
        shadow.appearance = self.appearance
        #As the list is referenced by the vertex and fragment shader no need to apply to fragment too...

    def remove_shadows(self, shape, appearance, shadow):
        if shadow in self.shadows:
            if shape.instance_ready:
                shadow.clear(shape, appearance)
            self.shadows.remove(shadow)
            shadow.shader = None
            shadow.appearance = None
        else:
            print("SHADOW NOT FOUND")
        #As the list is referenced by the vertex and fragment shader no need to apply to fragment too...

    def clear_shadows(self, shape, appearance):
        while self.shadows:
            shadow = self.shadows.pop()
            if shape.instance_ready:
                shadow.clear(shape, appearance)
            shadow.shader = None
        #As the list is referenced by the vertex and fragment shader no need to apply to fragment too...

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

    def update_shader_shape_static(self, shape, appearance):
        if self.color_picking and not self.vertex_oids:
            shape.instance.set_shader_input("color_picking", shape.get_oid_color())
        self.appearance.update_shader_shape_static(shape, appearance)
        self.tessellation_control.update_shader_shape_static(shape, appearance)
        for shadow in self.shadows:
            shadow.update_shader_shape_static(shape, appearance)
        self.lighting_model.update_shader_shape_static(shape, appearance)
        self.scattering.update_shader_shape_static(shape, appearance)
        self.vertex_control.update_shader_shape_static(shape, appearance)
        self.point_control.update_shader_shape_static(shape, appearance)
        self.instance_control.update_shader_shape_static(shape, appearance)
        self.data_source.update_shader_shape_static(shape, appearance)
        for effect in self.after_effects:
            effect.update_shader_shape_static(shape, appearance)
#         if self.has_bump_texture:
#             shape.instance.setShaderInput("bump_height", appearance.bump_height / settings.scale)

    def update_shader_shape(self, shape, appearance):
        self.appearance.update_shader_shape(shape, appearance)
        self.tessellation_control.update_shader_shape(shape, appearance)
        for shadow in self.shadows:
            shadow.update_shader_shape(shape, appearance)
        self.lighting_model.update_shader_shape(shape, appearance)
        self.scattering.update_shader_shape(shape, appearance)
        self.vertex_control.update_shader_shape(shape, appearance)
        self.point_control.update_shader_shape(shape, appearance)
        self.data_source.update_shader_shape(shape, appearance)
        for effect in self.after_effects:
            effect.update_shader_shape(shape, appearance)

    def update_shader_patch_static(self, shape, patch, appearance):
        self.appearance.update_shader_patch_static(shape, patch, appearance)
        self.tessellation_control.update_shader_patch_static(shape, patch, appearance)
        for shadow in self.shadows:
            shadow.update_shader_shape_static(shape, appearance)
        self.lighting_model.update_shader_patch_static(shape, patch, appearance)
        self.scattering.update_shader_patch_static(shape, patch, appearance)
        self.vertex_control.update_shader_patch_static(shape, patch, appearance)
        self.data_source.update_shader_patch_static(shape, patch, appearance)
        for effect in self.after_effects:
            effect.update_shader_patch_static(shape, patch, appearance)

    def update_shader_patch(self, shape, patch, appearance):
        self.appearance.update_shader_patch(shape, patch, appearance)
        self.tessellation_control.update_shader_patch(shape, patch, appearance)
        self.lighting_model.update_shader_patch(shape, patch, appearance)
        self.scattering.update_shader_patch(shape, patch, appearance)
        self.vertex_control.update_shader_patch(shape, patch, appearance)
        self.data_source.update_shader_patch(shape, patch, appearance)
        for effect in self.after_effects:
            effect.update_shader_patch(shape, patch, appearance)

    def get_user_parameters(self):
        group = ParametersGroup()
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

class ShaderComponent(object):
    use_vertex = False
    use_vertex_frag = False
    model_vertex = False
    world_vertex = False
    use_normal = False
    model_normal = False
    world_normal = False
    use_tangent = False

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

    def get_user_parameters(self):
        return None

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

    def clear(self, shape, appearance):
        pass

class CustomShaderComponent(ShaderComponent):
    def __init__(self, component_id):
        self.component_id = component_id
        self.has_vertex = False
        self.has_normal = False
        self.use_vertex = False
        self.use_vertex_frag = False
        self.model_vertex = False
        self.world_vertex = False
        self.use_normal = False
        self.model_normal = False
        self.world_normal = False
        self.use_tangent = False
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
        self.has_surface = False
        self.has_emission = False
        self.has_occlusion = False
        self.has_normal = False
        self.normal_texture_tangent_space = False
        self.has_bump = False
        self.has_gloss = False
        self.has_specular = False
        self.has_transparency = False
        self.has_nightscale = False
        self.has_backlit = False

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
        if self.has_gloss:
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
        if self.has_gloss:
            config += 'g'
        if self.has_nightscale:
            config += 'i'
        if self.has_backlit:
            config += 'a'
        return config

    def create_shader_configuration(self, appearance):
        #TODO: This should use the shader data source iso appearance!
        self.has_surface = True
        self.has_occlusion = False
        self.has_normal = appearance.normal_map is not None or self.data.has_source_for('normal')
        self.normal_texture_tangent_space = appearance.normal_map_tangent_space
        self.has_bump = appearance.bump_map is not None

        self.has_specular = appearance.specularColor is not None
        self.has_emission = appearance.emission_texture is not None

        self.has_gloss = appearance.gloss_map is not None
        self.has_transparency = appearance.transparency
        self.transparency_blend = appearance.transparency_blend

        self.has_nightscale = appearance.nightscale is not None
        self.has_backlit = appearance.backlit is not None

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
        if self.has_gloss:
            code.append("metallic = %s;" % self.data.get_source_for('metallic'))
            code.append("perceptual_roughness = %s;" % self.data.get_source_for('roughness'))

class VertexInput(ShaderComponent):
    def __init__(self, config):
        ShaderComponent.__init__(self)
        self.config = config

class DirectVertexInput(VertexInput):
    def vertex_inputs(self, code):
        code.append("in vec4 p3d_Vertex;")
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

class QuadTessellationVertexInput(VertexInput):
    def __init__(self, invert_v=True, shader=None):
        VertexInput.__init__(self, shader)
        self.invert_v = invert_v

    def vertex_layout(self, code):
        code.append("layout(quads, equal_spacing, ccw) in;")
        if self.config.vertex_shader.version < 400:
            code.append("#extension GL_ARB_tessellation_shader : enable")

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

class TessellationControl(ShaderComponent):
    pass

class ConstantTessellationControl(TessellationControl):
    def __init__(self, invert_v=True, shader=None):
        TessellationControl.__init__(self, shader)
        #invert_v is not used in TessellationControl but in QuadTessellationVertexInput
        #It is configured here as this is the user class
        self.invert_v = invert_v

    def get_id(self):
        return "ctess"

    def vertex_layout(self, code):
        code.append("layout(vertices = 4) out;")
        if self.shader.vertex_shader.version < 400:
            code.append("#extension GL_ARB_tessellation_shader : enable")

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
        patch.instance.set_shader_input('TessLevelInner', patch.tessellation_inner_level)
        patch.instance.set_shader_input('TessLevelOuter', *patch.tessellation_outer_level)

class VertexControl(ShaderComponent):
    use_double = False
    has_vertex = True
    has_normal = False
    def update_vertex(self, code):
        pass

    def update_normal(self, code):
        pass

class DefaultVertexControl(VertexControl):
    has_vertex = False

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
    has_normal = True

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
    has_normal = True

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
    has_normal = True

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

class PointControl(ShaderComponent):
    def fragment_shader_decl(self, code):
        for i in range(self.shader.nb_textures_coord):
            code.append("vec4 texcoord%i = vec4(gl_PointCoord, 0, 0);" % i)

    def update_shader_shape_static(self, shape, appearance):
        #TODO: This should definitively not be here
        attrib = shape.instance.getAttrib(ShaderAttrib)
        attrib2 = attrib.setFlag(ShaderAttrib.F_shader_point_size, True)
        shape.instance.setAttrib(attrib2)

class NoPointControl(ShaderComponent):
    pass

class StaticSizePointControl(PointControl):
    def get_id(self):
        return "pt-sta"

    def vertex_inputs(self, code):
        code.append("in float size;")

    def vertex_shader(self, code):
        code.append("gl_PointSize = size;")

class DistanceSizePointControl(PointControl):
    def get_id(self):
        return "pt-dist"

    def vertex_uniforms(self, code):
        code.append("uniform float near_plane_height;")

    def vertex_inputs(self, code):
        code.append("in float size;")

    def vertex_shader(self, code):
        code.append("gl_PointSize = (size * near_plane_height) / gl_Position.w;")

class InstanceControl(ShaderComponent):
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
    def has_source_for(self, source):
        return False

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

    def has_source_for(self, source_id):
        for source in self.sources:
            if source.has_source_for(source_id):
                return True
        return False

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

class PandaDataSource(DataSource):
    def __init__(self, shader=None):
        DataSource.__init__(self, shader)
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
        self.has_gloss_map_texture = False

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
        if self.tex_transform:
            config += "r"
        if self.has_gloss_map_texture:
            config += "g"
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
        self.gloss_map_texture_index = appearance.gloss_map_texture_index
        self.nb_textures = appearance.nb_textures
        self.has_surface_texture = appearance.texture is not None
        self.has_normal_texture = appearance.normal_map is not None
        self.has_bump_texture = appearance.bump_map is not None
        self.has_specular_texture = appearance.specular_map is not None
        self.has_specular_mask = appearance.has_specular_mask
        self.has_emission_texture = appearance.emission_texture
        self.has_gloss_map_texture = appearance.gloss_map is not None
        self.has_transparency = appearance.transparency
        self.has_alpha_mask = appearance.alpha_mask

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
        code.append("vec4 tex%i = texture2D(p3d_Texture%i, texcoord_tex%d.xy);" % (texture_id, texture_id, texture_id))
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
        if self.has_gloss_map_texture:
            code += self.create_tex_coord(self.gloss_map_texture_index, texture_coord)

    def bump_sample(self, code):
        pass

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
                return "tex%i.a" % self.texture_index
            else:
                return "1.0"
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
            if self.has_gloss_map_texture:
                data = "tex%i.b" % self.gloss_map_texture_index
            else:
                data = "1.0"
            if self.has_material:
                data = data + " * p3d_Material.metallic"
            return data
        if source == 'roughness':
            if self.has_gloss_map_texture:
                data = "tex%i.g" % self.gloss_map_texture_index
            else:
                data = "1.0"
            if self.has_material:
                data = data + " * p3d_Material.roughness"
            return data
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
        if self.has_gloss_map_texture:
            code += self.create_sample_texture(self.gloss_map_texture_index)

    def update_shader_shape_static(self, shape, appearance):
        if self.has_specular:
            shape.instance.setShaderInput("shape_specular_color", appearance.specularColor)
            shape.instance.setShaderInput("shape_shininess", appearance.shininess)
        if self.has_transparency:
            shape.instance.setShaderInput("transparency_level", appearance.transparency_level)

class ShaderShadow(ShaderComponent):
    pass

class ShaderShadowMap(ShaderShadow):
    use_vertex = True
    model_vertex = True
    use_normal = True
    model_normal = True

    def __init__(self, name, caster_body, caster, shader=None):
        ShaderShadow.__init__(self, shader)
        self.name = name
        self.caster_body = caster_body
        self.caster = caster

    def get_id(self):
        return 'sm-' + self.name

    def vertex_uniforms(self, code):
        code.append("uniform mat4 trans_model_to_clip_of_%sLightSource;" % self.name)
        code.append("uniform float %s_shadow_bias;" % self.name)

    def vertex_outputs(self, code):
        code.append("out vec4 %s_lightcoord;" % self.name)

    def vertex_shader(self, code):
        code.append("vec4 %s_lightclip = trans_model_to_clip_of_%sLightSource * (model_vertex4 + model_normal4 * %s_shadow_bias);" % (self.name, self.name, self.name))
        code.append("%s_lightcoord = %s_lightclip * vec4(0.5, 0.5, 0.5, 1.0) + %s_lightclip.w * vec4(0.5, 0.5, 0.5, 0.0);" % (self.name, self.name, self.name))

    def fragment_uniforms(self, code):
        code.append("uniform sampler2DShadow %s_depthmap;" % self.name)
        code.append("uniform float %s_shadow_coef;" % self.name)

    def fragment_inputs(self, code):
        code.append("in vec4 %s_lightcoord;" % self.name)

    def fragment_shader(self, code):
        if self.shader.fragment_shader.version < 130:
            code.append("shadow *= 1.0 - (1.0 - shadow2D(%s_depthmap, %s_lightcoord.xyz).x) * %s_shadow_coef;" % (self.name, self.name, self.name))
        else:
            code.append("shadow *= 1.0 - (1.0 - texture(%s_depthmap, %s_lightcoord.xyz)) * %s_shadow_coef;" % (self.name, self.name, self.name))

    def update_shader_shape_static(self, shape, appearance):
        shape.instance.setShaderInput('%s_shadow_bias' % self.name, self.caster.bias)
        shape.instance.setShaderInput('%s_depthmap' % self.name, self.caster.depthmap)
        shape.instance.setShaderInput("%sLightSource" % self.name, self.caster.cam)
        if self.caster_body is None:
            shape.instance.setShaderInput('%s_shadow_coef' % self.name, 1.0)

    def update_shader_shape(self, shape, appearance):
        if self.caster_body is None: return
        caster = self.caster_body
        body = shape.owner
        self_radius = caster.get_apparent_radius()
        body_radius = body.get_apparent_radius()
        position = caster._local_position
        body_position = body._local_position
        pa = body_position - position
        distance = abs(pa.length() - body_radius)
        if distance != 0:
            self_ar = self_radius / distance
            star_ar = caster.star.get_apparent_radius() / ((caster.star._local_position - body_position).length() - body_radius)
            ar_ratio = star_ar / self_ar
        else:
            ar_ratio = 0.0
        shape.instance.setShaderInput('%s_shadow_coef' % self.name, 1.0 - ar_ratio * ar_ratio)

    def clear(self, shape, appearance):
        shape.instance.clearShaderInput('%s_depthmap' % self.name)
        shape.instance.clearShaderInput("%sLightSource" % self.name)

class ShaderSphereShadow(ShaderShadow):
    use_vertex = True
    use_vertex_frag = True
    world_vertex = True
    model_vertex = True
    max_occluders = 4
    far_sun = True

    def __init__(self, shader=None):
        ShaderShadow.__init__(self, shader)
        #Currently only target having the same orientation as the caster are supported
        #i.e. rings
        self.oblate_occluder = False

    def get_id(self):
        name = "ss"
        if self.oblate_occluder:
            name += "o"
        return name

    def fragment_uniforms(self, code):
        if self.far_sun:
            code.append("uniform vec3 vector_to_star;")
            code.append("uniform float star_dist_radius_ratio;")
            code.append("uniform float star_ar;")
        else:
            code.append("uniform vec3 star_center;")
            code.append("uniform float star_radius;")
        code.append("uniform vec3 occluder_centers[%d];" % self.max_occluders)
        code.append("uniform float occluder_radii[%d];" % self.max_occluders)
        if self.oblate_occluder:
            code.append("uniform vec3 occluder_transform[%d];" % self.max_occluders)
        code.append("uniform int nb_of_occluders;")

    def fragment_shader(self, code):
        if self.far_sun:
            code.append("float aa = star_dist_radius_ratio * star_dist_radius_ratio;")
        code.append("for (int i = 0; i < nb_of_occluders; i++) {")
        if self.far_sun:
            if self.oblate_occluder:
                code.append("  vec3 vector_to_star_local = normalize(vec3(occluder_transform[i].x * vector_to_star.x, occluder_transform[i].y * vector_to_star.y, occluder_transform[i].z * vector_to_star.z));")
            else:
                code.append("  vec3 vector_to_star_local = vector_to_star;")
        else:
            code.append("  vec3 star_local = star_center - world_vertex;")
            if self.oblate_occluder:
                code.append("  star_local = vec3(occluder_transform[i].x * star_local.x, occluder_transform[i].y * star_local.y, occluder_transform[i].z * star_local.z);")
            code.append("  float aa = dot(star_local, star_local);")
        code.append("  vec3 occluder_local = occluder_centers[i] - world_vertex;")
        if self.oblate_occluder:
            code.append("  occluder_local = vec3(occluder_transform[i].x * occluder_local.x, occluder_transform[i].y * occluder_local.y, occluder_transform[i].z * occluder_local.z);")
        code.append("  float occluder_radius = occluder_radii[i];")
        code.append("  float bb = dot(occluder_local, occluder_local);")
        if self.far_sun:
            code.append("  float ab = dot(vector_to_star_local, occluder_local) * star_dist_radius_ratio;")
        else:
            code.append("  float ab = dot(star_local, occluder_local);")
        code.append("  if (ab > 0) { //Apply shadow only if the occluder is between the target and the star")
        if self.far_sun:
            code.append("    float s = ab*ab + bb + occluder_radius*occluder_radius*aa - aa*bb;")
            code.append("    float t = 2.0*ab*occluder_radius;")
        else:
            code.append("    float s = ab*ab + star_radius*star_radius*bb + occluder_radius*occluder_radius*aa - aa*bb;")
            code.append("    float t = 2.0*ab*star_radius*occluder_radius;")
        code.append("    if ((s + t) < 0.0) {");
        code.append("      //No overlap")
        code.append("    } else if ((s - t) < 0.0) {");
        code.append("      //Partial overlap, use angular radius to calculate actual occlusion")
        if not self.far_sun:
            code.append("      float star_ar = asin(star_radius / length(star_local));")
        code.append("      float occluder_ar = asin(occluder_radius / length(occluder_local));")
        #acos(dot) has precision issues and shows artefacts in the penumbra
        #We use asin(cross()) instead to diminish the artifacts (though smoothstep below is also needed)
        if self.far_sun:
            #code.append("      float separation = acos(clamp(dot(vector_to_star, normalize(occluder_local)), 0, 1));")
            code.append("      float separation = asin(clamp(length(cross(vector_to_star, normalize(occluder_local))), 0, 1));")
        else:
            #code.append("      float separation = acos(clamp(dot(normalize(star_local), normalize(occluder_local)), 0, 1));")
            code.append("      float separation = asin(clamp(length(cross(normalize(star_local), normalize(occluder_local))), 0, 1));")
        code.append("      if (separation <= star_ar - occluder_ar) {")
        code.append("        //Occluder fully inside star, attenuation is the ratio of the visible surfaces");
        code.append("        float surface_ratio = clamp((occluder_ar * occluder_ar) / (star_ar * star_ar), 0, 1);");
        code.append("        shadow *= 1.0 - surface_ratio;");
        code.append("      } else {");
        code.append("        //Occluder partially occluding star, use linear approximation");
        code.append("        float surface_ratio = clamp((occluder_ar * occluder_ar) / (star_ar * star_ar), 0, 1);");
        code.append("        float ar_diff = abs(star_ar - occluder_ar);");
        #TODO: Smoothstep is added here to hide precision artifacts in the penumbra
        #It causes the penumbra to appear darker than it should
        #code.append("        shadow *= surface_ratio * (separation - ar_diff) / (star_ar + occluder_ar - ar_diff);")
        code.append("        shadow *= surface_ratio * smoothstep(0, 1, (separation - ar_diff) / (star_ar + occluder_ar - ar_diff));")
        code.append("      }");
        code.append("    } else {");
        code.append("      shadow = 0.0; //Full overlap")
        code.append("    }")
        code.append("  } else {")
        code.append("    //Not in shadow");
        code.append("  }")
        code.append("}")

    def update_shader_shape(self, shape, appearance):
        #TODO: This is quite ugly....
        star = shape.owner.star
        observer = shape.owner.context.observer._position
        scale = shape.owner.scene_scale_factor
        if self.far_sun:
            shape.instance.setShaderInput('vector_to_star', shape.owner.vector_to_star)
            shape.instance.setShaderInput('star_dist_radius_ratio', shape.owner.distance_to_star / star.get_apparent_radius())
            shape.instance.setShaderInput('star_ar', asin(star.get_apparent_radius() / shape.owner.distance_to_star))
        else:
            star_center = (star._local_position - observer) * scale
            star_radius = star.get_apparent_radius() * scale
            shape.instance.setShaderInput('star_center', star_center)
            shape.instance.setShaderInput('star_radius', star_radius)
        centers = []
        radii = []
        tf = []
        for shadow_caster in shape.parent.shadows.sphere_shadows.occluders:
            centers.append((shadow_caster.body._local_position - observer) * scale)
            radius = shadow_caster.body.get_apparent_radius()
            radii.append(radius * scale)
            if self.oblate_occluder:
                vs = shadow_caster.body.get_scale()
                tf.append((radius/vs[0], radius/vs[1], radius/vs[2]))
        nb_of_occluders = len(shape.parent.shadows.sphere_shadows.occluders)
        shape.instance.setShaderInput('occluder_centers', centers)
        shape.instance.setShaderInput('occluder_radii', radii)
        if self.oblate_occluder:
            shape.instance.setShaderInput('occluder_transform', tf)
        shape.instance.setShaderInput("nb_of_occluders", nb_of_occluders)

class ShaderRingShadow(ShaderShadow):
    use_vertex = True
    use_vertex_frag = True
    world_vertex = True
    model_vertex = True
    def get_id(self):
        return 'rs'

    def fragment_uniforms(self, code):
        code.append("uniform sampler2D shadow_ring_tex;")
        code.append("uniform vec3 ring_normal;")
        code.append("uniform float ring_inner_radius;")
        code.append("uniform float ring_outer_radius;")
        code.append("uniform vec3 body_center;")

    def fragment_shader(self, code):
        #Simple line-plane intersection:
        #line is surface of the planet to the center of the light source
        #plane is the plane of the rings system
        code.append("vec3 new_pos = world_vertex - body_center;")
        code.append("float ring_intersection_param = -dot(new_pos, ring_normal.xyz) / dot(light_dir, ring_normal.xyz);")
        code.append("if (ring_intersection_param > 0.0) {")
        code.append("  vec3 ring_intersection = new_pos + light_dir * ring_intersection_param;")
        code.append('  float ring_shadow_local = (length(ring_intersection) - ring_inner_radius) / (ring_outer_radius - ring_inner_radius);')
        code.append("  shadow *= 1.0 - texture2D(shadow_ring_tex, vec2(ring_shadow_local, 0.0)).a;")
        code.append("} else {")
        code.append("  //Not in shadow")
        code.append("}")

    #TODO: Should be in static
    def update_shader_shape(self, shape, appearance):
        #TODO: This is quite ugly....
        ring = shape.parent.shadows.ring_shadow.ring
        (texture, texture_size, texture_lod) = ring.appearance.texture.source.get_texture(ring.shape)
        if texture is not None:
            shape.instance.setShaderInput('shadow_ring_tex',texture)
        normal = shape.owner.scene_orientation.xform(LVector3d.up())
        shape.instance.setShaderInput('ring_normal', normal)
        shape.instance.setShaderInput('ring_inner_radius', ring.inner_radius * shape.owner.scene_scale_factor)
        shape.instance.setShaderInput('ring_outer_radius', ring.outer_radius * shape.owner.scene_scale_factor)
        if shape.owner.support_offset_body_center and settings.offset_body_center:
            body_center = shape.owner.scene_position + shape.owner.projected_world_body_center_offset
        else:
            body_center = shape.owner.scene_position
        shape.instance.setShaderInput('body_center', body_center)

class ShaderSphereSelfShadow(ShaderShadow):
    #TODO: Until proper self-shadowing is added, the effect of the normal map
    #is damped by this factor when the angle between the normal and the light
    #is negative (angle > 90deg)
    fake_self_shadow = 0.05

    def get_id(self):
        return 'sss' if self.appearance.has_normal else ''

    def fragment_shader(self, code):
        if self.appearance.has_normal:
            code.append("float terminator_coef = dot(shape_normal, light_dir);")
            code.append("shadow *= smoothstep(0.0, 1.0, (%f + terminator_coef) * %f);" % (self.fake_self_shadow, 1.0 / self.fake_self_shadow))

class LightingModel(ShaderComponent):
    def apply_emission(self, code, angle):
        back_test = self.appearance.has_backlit or (self.appearance.has_emission and self.appearance.has_nightscale)
        if back_test:
            code.append("if (%s < 0.0) {" % angle)
        if self.appearance.has_emission and self.appearance.has_nightscale:
            code.append("  float emission_coef = clamp(sqrt(-%s), 0.0, 1.0);" % angle)
            code.append("  total_emission_color.rgb += emission_color.rgb * emission_coef;")
        if self.appearance.has_backlit:
            code.append("  total_emission_color.rgb += surface_color.rgb * backlit * sqrt(-%s);" % angle)
        if back_test:
            code.append("}")
        if self.appearance.has_emission and not self.appearance.has_nightscale:
            code.append("  total_emission_color.rgb += emission_color.rgb;")

    def update_shader_shape(self, shape, appearance):
        if self.appearance.has_backlit:
            shape.instance.setShaderInput("backlit", appearance.backlit)
        if self.appearance.has_nightscale:
            shape.instance.setShaderInput("nightscale", appearance.nightscale)

class FlatLightingModel(LightingModel):
    def get_id(self):
        return "flat"

    def fragment_shader(self, code):
        if self.appearance.has_surface:
            code.append("total_diffuse_color = surface_color;")
        if self.appearance.has_emission:
            code.append("total_emission_color = emission_color;")
        if self.appearance.has_transparency:
            #TODO: This should not be here!
            code.append("float alpha =  %s;" % self.shader.data_source.get_source_for('alpha'))
            code.append("total_diffuse_color.a *= alpha;")

class LambertPhongLightingModel(LightingModel):
    use_vertex = True
    world_vertex = True
    use_vertex_frag = True
    use_normal = True
    world_normal = True

    def get_id(self):
        return "lambert"
 
    def fragment_uniforms(self, code):
        code.append("uniform float ambient_coef;")
        code.append("uniform float backlit;")
        code.append("uniform vec3 light_dir;")
        code.append("uniform vec4 ambient_color;")
        code.append("uniform vec4 light_color;")

    def fragment_shader(self, code):
        #TODO: should be done only using .rgb (or vec3) and apply alpha channel in the end
        if self.appearance.has_specular:
            code.append("vec3 obs_dir = normalize(-world_vertex);")
            code.append("vec3 half_vec = normalize(light_dir + obs_dir);")
            code.append("float spec_angle = clamp(dot(normal, half_vec), 0.0, 1.0);")
            code.append("vec4 specular = light_color * pow(spec_angle, shininess);")
        code.append("vec4 ambient = ambient_color * ambient_coef;")
        if self.appearance.has_occlusion:
            code.append("ambient *= surface_occlusion;")
        code.append("float diffuse_angle = 0.0;")
        code.append("diffuse_angle = dot(normal, light_dir);")
        code.append("float diffuse_coef = clamp(diffuse_angle, 0.0, 1.0) * shadow;")
        code.append("vec4 total_light = clamp((diffuse_coef + (1.0 - diffuse_coef) * ambient), 0.0, 1.0);")
        code.append("total_light.a = 1.0;")
        code.append("total_diffuse_color = surface_color * total_light;")
        if self.appearance.has_specular:
            code.append("total_diffuse_color.rgb += specular.rgb * specular_color.rgb * shadow;")
        self.apply_emission(code, 'diffuse_angle')

    def update_shader_shape(self, shape, appearance):
        LightingModel.update_shader_shape(self, shape, appearance)
        light_dir = shape.owner.vector_to_star
        light_color = shape.owner.light_color
        shape.instance.setShaderInput("light_dir", *light_dir)
        shape.instance.setShaderInput("light_color", light_color)
        shape.instance.setShaderInput("ambient_coef", settings.corrected_global_ambient)
        shape.instance.setShaderInput("ambient_color", (1, 1, 1, 1))

class OrenNayarPhongLightingModel(LightingModel):
    use_vertex = True
    world_vertex = True
    use_vertex_frag = True
    use_normal = True
    world_normal = True

    def get_id(self):
        return "oren-nayar"

    def fragment_uniforms(self, code):
        code.append("uniform float ambient_coef;")
        code.append("uniform vec3 light_dir;")
        code.append("uniform vec4 ambient_color;")
        code.append("uniform vec4 light_color;")
        code.append("uniform float backlit;")
        code.append("uniform float roughness_squared;")

    def fragment_shader(self, code):
        code.append("vec3 obs_dir = normalize(-world_vertex);")
        if self.appearance.has_specular:
            code.append("vec3 half_vec = normalize(light_dir + obs_dir);")
            code.append("float spec_angle = clamp(dot(normal, half_vec), 0.0, 1.0);")
            code.append("vec4 specular = light_color * pow(spec_angle, shininess);")
        code.append("vec4 ambient = ambient_color * ambient_coef;")
        code.append("float v_dot_n = dot(obs_dir, normal);")
        code.append("float l_dot_n = dot(light_dir, normal);")
        code.append("float theta_r = acos(v_dot_n);")
        code.append("float theta_i = acos(l_dot_n);")
        code.append("float alpha = max(theta_r, theta_i);")
        code.append("float beta = min(theta_r, theta_i);")
        code.append("float delta = dot(normalize(obs_dir - normal * v_dot_n), normalize(light_dir - normal * l_dot_n));")
        code.append("float a = 1.0 - 0.5 * roughness_squared / (roughness_squared + 0.33);")
        code.append("float b = 0.45 * roughness_squared / (roughness_squared + 0.09);")
        code.append("float c = sin(alpha) * tan(beta);")
        code.append("float diffuse_coef = max(0.0, l_dot_n) * (a + b * max(0.0, delta) * c);")
        code.append("vec4 diffuse = light_color * shadow * diffuse_coef;")
        code.append("vec4 total_light = clamp((diffuse + (1.0 - diffuse_coef) * ambient), 0.0, 1.0);")
        code.append("total_light.a = 1.0;")
        code.append("total_diffuse_color = surface_color * total_light;")
        if self.appearance.has_specular:
            code.append("total_diffuse_color.rgb += specular.rgb * specular_factor.rgb * specular_color.rgb * shadow;")
        self.apply_emission(code, 'l_dot_n')

    def update_shader_shape(self, shape, appearance):
        LightingModel.update_shader_shape(self, shape, appearance)
        light_dir = shape.owner.vector_to_star
        light_color = shape.owner.light_color
        shape.instance.setShaderInput("light_dir", *light_dir)
        shape.instance.setShaderInput("light_color", light_color)
        shape.instance.setShaderInput("ambient_coef", settings.corrected_global_ambient)
        shape.instance.setShaderInput("ambient_color", (1, 1, 1, 1))
        shape.instance.setShaderInput("roughness_squared", appearance.roughness * appearance.roughness)

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
        self.fog_color = (0.5, 0.6, 0.7, 1.0)
        self.sun_color = (1.0, 0.9, 0.7, 1.0)

    def get_id(self):
        return "fog"

    def fragment_uniforms(self, code):
        code.append("uniform vec3 camera;")
        code.append("uniform float fogFallOff;")
        code.append("uniform float fogDensity;")
        code.append("uniform float fogGround;")
        code.append("uniform vec4 fogColor;")
        code.append("uniform vec4 sunColor;")

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
    vec3  mixColor = mix( fogColor.xyz, sunColor.xyz, pow(sunAmount, 8.0));
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
        shape.instance.set_shader_input("fogColor", self.fog_color)
        shape.instance.set_shader_input("sunColor", self.sun_color)
