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
from panda3d.core import AsyncFuture
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
        self.resizable = False

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
        buffer_options = GraphicsPipe.BF_refuse_window
        if self.resizable:
            buffer_options |= GraphicsPipe.BF_resizeable
        self.buffer = base.graphics_engine.make_output(win.get_pipe(), "generatorBuffer", -1,
            fbprops, winprops,  buffer_options, win.get_gsg(), win)
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
        #TODO: This should either be done inside the passthrough vertex shader
        # Or in the heightmap sampler.
        x_margin = 1.0 / width / 2.0
        y_margin = 1.0 / height / 2.0
        cm.set_uv_range((-x_margin, -y_margin), (1 + x_margin, 1 + y_margin))
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
        self.clear()
        if self.buffer is not None:
            self.buffer.set_active(False)
            base.graphicsEngine.remove_window(self.buffer)
            self.buffer = None

    def prepare(self, textures, shader_data):
        self.buffer.clear_render_textures()
        self.shader.update(self.quad, **shader_data)
        if self.to_ram:
            mode = GraphicsOutput.RTM_copy_ram
        else:
            mode = GraphicsOutput.RTM_bind_or_copy
        for texture_config in textures.values():
            if not isinstance(texture_config, (list, tuple)):
                texture = texture_config
                render_target = GraphicsOutput.RTP_color
            else:
                texture, render_target = texture_config
            self.buffer.add_render_texture(texture, mode, render_target)
        self.buffer.set_one_shot(True)
        self.buffer.set_active(True)

    def update(self, shader_data):
        self.shader.update(self.quad, **shader_data)
        self.buffer.set_one_shot(True)

    def clear(self):
        #TODO: Should the buffer be deactivated too ?
        self.buffer.clear_render_textures()

class RenderStage():
    sources = []
    def __init__(self,name, size):
        self.name = name
        self.size = size
        self.sources_map = {}
        self.target = None
        self.textures = None

    def get_size(self):
        return self.size

    def has_output(self, output_name):
        return False

    def get_output(self, output_name):
        return None

    def add_source(self, source_name, stage):
        self.sources_map[source_name] = stage

    def create(self):
        raise NotImplementedError()

    def create_textures(self):
        raise NotImplementedError()

    def prepare(self, shader_data):
        self.textures = self.create_textures(shader_data)
        self.target.prepare(self.textures, shader_data)

    def update(self, shader_data):
        self.target.update(shader_data)

    def gather(self, result):
        data = {}
        for name, texture_config in self.textures.items():
            if isinstance(texture_config, (list, tuple)):
                data[name] = texture_config[0]
            else:
                data[name] = texture_config
        result[self.name] = data

    def clear(self):
        self.target.clear()
        self.textures = None

    def remove(self):
        self.target.remove()

class GeneratorChain():
    def __init__(self):
        self.stages = []
        self.busy = False
        self.queue = []
        taskMgr.add(self.check_generation, 'tex_generation', sort = -10000)

    def add_stage(self, stage):
        for source in stage.sources:
            for parent in reversed(self.stages):
                output = parent.get_output(source)
                if output is not None:
                    stage.add_source(source, parent)
                    break
            else:
                print("ERROR: Source {} not found".format(source))
        self.stages.append(stage)

    def create(self):
        for stage in self.stages:
            stage.create()

    def prepare(self, shader_data):
        for stage in self.stages:
            stage.prepare(shader_data.get(stage.name, {}))

    def update(self, shader_data):
        for stage in self.stages:
            stage.update(shader_data.get(stage.name, {}))

    def gather_results(self):
        result = {}
        for stage in self.stages:
            stage.gather(result)
        return result

    def clear(self):
        for stage in self.stages:
            stage.clear()

    def remove(self):
        for stage in self.stages:
            stage.remove()

    def check_generation(self, task):
        if len(self.queue) > 0:
            (shader_data, future) = self.queue.pop(0)
            future.set_result(self.gather_results())
            if len(self.queue) > 0:
                self.schedule_next()
            else:
                self.busy = False
                #self.clear()
        return Task.cont

    def schedule_next(self):
        (shader_data, future) = self.queue[0]
        self.prepare(shader_data)

    def schedule(self, shader_data, future):
        self.queue.append((shader_data, future))
        if not self.busy:
            self.schedule_next()
            self.busy = True

    def generate(self, shader_data):
        future = AsyncFuture()
        self.schedule(shader_data, future)
        return future

class GeneratorPool(object):
    def __init__(self, chains):
        self.chains = chains

    def add_chain(self, chain):
        self.chains.append(chain)

    def create(self):
        for chain in self.chains:
            chain.create()

    def remove(self):
        for chain in self.chains:
            chain.remove()

    def generate(self, shader_data):
        lowest = self.chains[0]
        for chain in self.chains[1:]:
            if len(chain.queue) < len(lowest.queue):
                lowest = chain
        return lowest.generate(shader_data)
