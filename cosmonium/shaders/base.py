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


from panda3d.core import Shader

from ..opengl import OpenGLConfig
from ..cache import create_path_for
from .. import settings

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

    def create(self, shape, appearance, force=True):
        self.create_and_register_shader(shape, appearance, force)

    def apply(self, instance):
        if instance is None: return
        if self.shader is not None:
            instance.set_shader(self.shader)
        else:
            print("ERROR: Applying a non created shader")

class AutoShader(ShaderBase):
    def set_instance_control(self, instance_control):
        print("AutoShader: set_instance_control not supported")

    def set_scattering(self, scattering):
        print("AutoShader: set_scattering not supported")

    def add_shadows(self, shadows):
        print("AutoShader: add_shadows not supported")

    def remove_shadows(self, shape, appearance, shadow):
        pass

    def remove_all_shadows(self, shape, appearance):
        pass

    def add_after_effect(self, after_effect):
        print("AutoShader: add_after_effect not supported")

    def apply(self, shape, appearance):
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
        self.file_id: str = None

    def get_shader_id(self):
        return ''

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

    def create_shader_version(self, code):
        if self.version is not None:
            if self.version < 300:
                code.append(f"#version {self.version}")
            else:
                profile = 'core' if OpenGLConfig.core_profile else 'compatibility'
                code.append(f"#version {self.version} {profile}")
            if OpenGLConfig.core_profile:
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
            self.file_id = os.path.join(shaders_path, "%s.%s.glsl" % (dump, self.shader_type))
            with open(self.file_id, "w") as shader_file:
                shader_file.write(shader)
        else:
            self.file_id = shader_id
        return shader

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
            shaders_path = create_path_for('shaders')
            print(f"Creating shader {shader_id} ({shaders_path}/{dump})")
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
        shader = Shader.make(Shader.SL_GLSL,
                             vertex=vertex,
                             tess_control=tess_control,
                             tess_evaluation=tess_evaluation,
                             geometry=geometry,
                             fragment=fragment)
        shader.set_filename(-1, f"{shaders_path}/{dump}")
        if vertex:
            shader.set_filename(Shader.ST_vertex, self.vertex_shader.file_id)
        if tess_control:
            shader.set_filename(Shader.ST_tess_control, self.tessellation_control_shader.file_id)
        if tess_evaluation:
            shader.set_filename(Shader.ST_tess_evaluation, self.tessellation_eval_shader.file_id)
        if geometry:
            shader.set_filename(Shader.ST_geometry, self.geometry_shader.file_id)
        if fragment:
            shader.set_filename(Shader.ST_fragment, self.fragment_shader.file_id)
        return shader
