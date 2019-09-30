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

from panda3d.core import NodePath, OrthographicLens, CardMaker, GraphicsOutput, Texture
from panda3d.core import FrameBufferProperties, GraphicsPipe, WindowProperties
from direct.task import Task

from .. import settings

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
        self.buffer.setOneShot(True)
        #the camera for the buffer
        cam = base.makeCamera(win=self.buffer)
        cam.reparent_to(self.root)
        cam.set_pos(width / 2, height / 2, 100)
        cam.set_p(-90)
        lens = OrthographicLens()
        lens.set_film_size(width, height)
        cam.node().set_lens(lens)          
        #plane with the texture
        cm = CardMaker("plane")
        cm.set_frame(0, width, 0, height)
        x_margin = 1.0 / width / 2.0
        y_margin = 1.0 / height / 2.0
        cm.set_uv_range((-x_margin, -y_margin), (1 + x_margin, 1 + y_margin))
        self.quad = self.root.attach_new_node(cm.generate())
        self.quad.look_at(0, 0, -1)
        taskMgr.add(self.check_generation, 'check_generation', sort = -10000)
        taskMgr.add(self.callback, 'callback', sort = -9999)
        print("Created offscreen buffer, size: %dx%d" % (width, height), "format:", Texture.formatFormat(texture_format))

    def remove(self):
        if self.buffer is not None:
            self.buffer.set_active(False)
            base.graphicsEngine.removeWindow(self.buffer)
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
        self.buffer.setOneShot(True)
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
        if texture.has_ram_image():
            print("Texture already has data")
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
