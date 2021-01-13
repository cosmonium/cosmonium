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

from panda3d.core import NodePath, Camera, OrthographicLens, CardMaker, GraphicsOutput, Texture
from panda3d.core import FrameBufferProperties
from direct.task import Task

from ..shaders import ShaderProgram

class GeneratorVertexShader(ShaderProgram):
    def __init__(self):
        ShaderProgram.__init__(self, 'vertex')

    def create_uniforms(self, code):
        code.append("uniform mat4 p3d_ModelViewProjectionMatrix;")

    def create_inputs(self, code):
        code.append("in vec2 p3d_MultiTexCoord0;")
        code.append("in vec4 p3d_Vertex;")

    def create_outputs(self, code):
        code.append("out vec2 texcoord;")

    def create_body(self, code):
        code.append("gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;")
        code.append("texcoord = p3d_MultiTexCoord0;")

class TexGenerator(object):
    def __init__(self):
        self.root = None
        self.quad = None
        self.buffer = None
        self.busy = False
        self.first = True
        self.queue = []
        self.processed = []

    def make_buffer(self, width, height, texture_format):
        self.width = width
        self.height = height
        self.root = NodePath("root")
        props = FrameBufferProperties()
        props.set_srgb_color(False)
        if texture_format == Texture.F_rgb:
            props.set_float_color(False)
            props.set_rgba_bits(8, 8, 8, 0)
        elif texture_format == Texture.F_rgba:
            props.set_float_color(False)
            props.set_rgba_bits(8, 8, 8, 8)
        elif texture_format == Texture.F_r32:
            props.set_float_color(True)
            props.set_rgba_bits(32, 0, 0, 0)
        elif texture_format == Texture.F_rgb32:
            props.set_float_color(True)
            props.set_rgba_bits(32, 32, 32, 0)
        elif texture_format == Texture.F_rgba32:
            props.set_float_color(True)
            props.set_rgba_bits(32, 32, 32, 32)
        self.buffer = base.win.make_texture_buffer("generatorBuffer", width, height, to_ram=True, fbp=props)
        #print(self.buffer.get_fb_properties(), self.buffer.get_texture())

        #Create the camera for the buffer
        cam = Camera("generator-cam")
        lens = OrthographicLens()
        lens.set_film_size(2, 2)
        lens.set_near_far(0, 0)
        lens.setNearFar(-1000, 1000)
        cam.set_lens(lens)
        cam_np = self.root.attach_new_node(cam)

        #Create the plane with the texture
        cm = CardMaker("plane")
        cm.set_frame_fullscreen_quad()
        self.quad = self.root.attach_new_node(cm.generate())
        self.quad.set_depth_test(False)
        self.quad.set_depth_write(False)

        #Create the display region and attach the camera
        dr = self.buffer.make_display_region((0, 1, 0, 1))
        dr.disable_clears()
        dr.set_camera(cam_np)
        dr.set_scissor_enabled(False)

        taskMgr.add(self.check_generation, 'check_generation', sort = -10000)
        taskMgr.add(self.callback, 'callback', sort = -9999)
        print("Created offscreen buffer, size: %dx%d" % (width, height), "format:", Texture.formatFormat(texture_format))

    def remove(self):
        if self.buffer is not None:
            self.buffer.set_active(False)
            base.graphicsEngine.remove_window(self.buffer)
            self.buffer = None

    def callback(self, task):
        if len(self.processed) > 0:
            (shader, face, texture, callback, cb_args) = self.processed[0]
            if texture.has_ram_image():
                if callback is not None:
                    #print(texture)
                    #print(self.buffer.get_fb_properties(), self.buffer.get_texture())
                    callback(texture, *cb_args)
                self.processed.pop(0)
        return Task.cont

    def check_generation(self, task):
        if self.buffer is None:
            return Task.cont
        if self.first and len(self.queue) > 0:
            (shader, face, texture, callback, cb_args) = self.queue[0]
            if not texture.has_ram_image():
                #print("FIRST")
                self.buffer.setOneShot(True)
            else:
                self.first = False
            return Task.cont
        if len(self.queue) > 0:
            self.processed.append(self.queue.pop(0))
            if len(self.queue) > 0:
                self.schedule_next()
            else:
                self.busy = False
        return Task.cont

    def prepare(self, shader, face, texture):
        self.buffer.set_one_shot(True)
        self.quad.set_shader(shader.shader)
        #TODO: face should be in shader
        shader.update(self.root, face=face)
        self.buffer.clear_render_textures()
        self.buffer.add_render_texture(texture, GraphicsOutput.RTM_copy_ram)

    def schedule_next(self):
        (shader, face, texture, callback, cb_args) = self.queue[0]
        self.prepare(shader, face, texture)

    def schedule(self, item):
        self.queue.append(item)
        if not self.busy:
            #print("SCHEDULE")
            (shader, face, texture, callback, cb_args) = item
            self.prepare(shader, face, texture)
            self.busy = True

    def generate(self, shader, face, texture, callback=None, cb_args=()):
        #print("ADD")
        self.schedule((shader, face, texture, callback, cb_args))

class GeneratorPool(object):
    def __init__(self, number):
        self.number = number
        self.generators = []
        for _ in range(number):
            self.generators.append(TexGenerator())

    def make_buffer(self, width, height, texture_format):
        for generator in self.generators:
            generator.make_buffer(width, height, texture_format)

    def generate(self, shader, face, texture, callback=None, cb_args=()):
        lowest = self.generators[0]
        for generator in self.generators[1:]:
            if len(generator.queue) < len(lowest.queue):
                lowest = generator
        lowest.generate(shader, face, texture, callback, cb_args)
