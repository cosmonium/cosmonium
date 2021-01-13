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
from panda3d.core import WindowProperties, FrameBufferProperties, GraphicsPipe
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

class RenderTarget(object):
    def __init__(self):
        self.root = None
        self.quad = None
        self.buffer = None
        self.width = None
        self.height = None
        self.mode = None

    def format_to_props(self, texture_format):
        fbprops = FrameBufferProperties()
        fbprops.set_srgb_color(False)
        if texture_format == Texture.F_rgb:
            fbprops.set_float_color(False)
            fbprops.set_rgba_bits(8, 8, 8, 0)
        elif texture_format == Texture.F_rgba:
            fbprops.set_float_color(False)
            fbprops.set_rgba_bits(8, 8, 8, 8)
        elif texture_format == Texture.F_r32:
            fbprops.set_float_color(True)
            fbprops.set_rgba_bits(32, 0, 0, 0)
        elif texture_format == Texture.F_rgb32:
            fbprops.set_float_color(True)
            fbprops.set_rgba_bits(32, 32, 32, 0)
        elif texture_format == Texture.F_rgba32:
            fbprops.set_float_color(True)
            fbprops.set_rgba_bits(32, 32, 32, 32)
        return fbprops

    def make_buffer(self, width, height, texture_format, to_ram):
        self.width = width
        self.height = height
        self.to_ram = to_ram
        self.root = NodePath("root")
        winprops = WindowProperties()
        winprops.setSize(width, height)
        fbprops = self.format_to_props(texture_format)
        win = base.win
        self.buffer=base.graphics_engine.make_output(
            win.get_pipe(), "generatorBuffer", -1,
            fbprops, winprops, GraphicsPipe.BF_refuse_window | GraphicsPipe.BF_resizeable,
            win.get_gsg(), win)
        self.buffer.set_active(False)

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

        print("Created offscreen buffer, size: %dx%d" % (width, height), "format:", Texture.formatFormat(texture_format))

    def set_shader(self, shader):
        self.shader = shader
        self.quad.set_shader(shader.shader)

    def remove(self):
        if self.buffer is not None:
            self.buffer.set_active(False)
            base.graphicsEngine.remove_window(self.buffer)
            self.buffer = None

    def prepare(self, shader_data, texture):
        self.buffer.set_one_shot(True)
        self.buffer.set_active(True)
        #TODO: face should be in shader
        self.shader.update(self.quad, **shader_data)
        self.buffer.clear_render_textures()
        if self.to_ram:
            mode = GraphicsOutput.RTM_copy_ram
        else:
            mode = GraphicsOutput.RTM_bind_or_copy
        self.buffer.add_render_texture(texture, mode)

class RenderStage():
    def __init__(self,name, size):
        self.name = name
        self.size = size
        self.target = None

    def get_size(self):
        return self.size

    def create(self):
        raise NotImplementedError()

    def prepare(self, shader_data, texture):
        self.target.prepare(shader_data, texture)

class GeneratorChain():
    def __init__(self):
        self.stages = []
        self.busy = False
        self.queue = []
        taskMgr.add(self.check_generation, 'tex_generation', sort = -10000)

    def add_stage(self, stage):
        self.stages.append(stage)

    def create(self):
        for stage in self.stages:
            stage.create()

    def callback(self, stage_info):
        (shader_data, texture, callback, cb_args) = stage_info
        if texture.has_ram_image():
            if callback is not None:
                #print(texture)
                #print(self.buffer.get_fb_properties(), self.buffer.get_texture())
                callback(texture, *cb_args)
        else:
            print("Texture has no RAM image")

    def check_generation(self, task):
        if len(self.queue) > 0:
            stage_info = self.queue.pop(0)
            self.callback(stage_info)
            if len(self.queue) > 0:
                self.schedule_next()
            else:
                self.busy = False
        return Task.cont

    def schedule_next(self):
        (shader_data, texture, callback, cb_args) = self.queue[0]
        for stage in self.stages:
            stage.prepare(shader_data.get(stage.name, {}), texture)

    def schedule(self, item):
        self.queue.append(item)
        if not self.busy:
            self.schedule_next()
            self.busy = True

    def generate(self, shader_data, texture, callback=None, cb_args=()):
        #print("ADD")
        self.schedule((shader_data, texture, callback, cb_args))

class GeneratorPool(object):
    def __init__(self, number):
        self.number = number
        self.generators = []
        for _ in range(number):
            self.generators.append(GeneratorChain())

    def make_buffer(self, width, height, texture_format):
        for generator in self.generators:
            generator.make_buffer(width, height, texture_format)

    def generate(self, shader, face, texture, callback=None, cb_args=()):
        lowest = self.generators[0]
        for generator in self.generators[1:]:
            if len(generator.queue) < len(lowest.queue):
                lowest = generator
        lowest.generate(shader, face, texture, callback, cb_args)
