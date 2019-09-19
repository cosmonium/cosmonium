from __future__ import print_function
from __future__ import absolute_import

from panda3d.core import Texture, LColor, LVector2

from .heightmap import Heightmap, HeightmapPatch, HeightmapPatchFactory
from .generator import TexGenerator, GeneratorPool
from .shadernoise import NoiseShader, FloatTarget
from ..textures import TexCoord
from .. import settings

import traceback
import numpy
import sys

class ShaderHeightmap(Heightmap):
    tex_generators = {}

    def __init__(self, name, width, height, height_scale, median, noise, offset=None, scale=None, coord = TexCoord.Cylindrical, interpolator=None):
        Heightmap.__init__(self, name, width, height, height_scale, 1.0, 1.0, median, interpolator)
        self.noise = noise
        self.offset = offset
        self.scale = scale
        self.coord = coord
        self.shader = None
        self.texture = None
        self.texture_offset = LVector2()
        self.texture_scale = LVector2(1, 1)
        self.tex_id = str(width) + ':' + str(height)

    def reset(self):
        self.texture = None

    def set_noise(self, noise):
        self.noise = noise
        self.shader = None
        self.texture = None

    def set_offset(self, offset):
        self.offset = offset
        if self.shader is not None:
            self.shader.offset = offset
        self.texture = None

    def set_scale(self, scale):
        self.scale = scale
        if self.shader is not None:
            self.shader.scale = scale
        self.texture = None

    def get_heightmap(self, patch):
        return self

    def get_texture_offset(self, patch):
        return self.texture_offset

    def get_texture_scale(self, patch):
        return self.texture_scale

    def get_height(self, x, y):
        if self.texture_peeker is None:
            print("No peeker")
            traceback.print_stack()
            return 0.0
        new_x = x * self.texture_scale[0] + self.texture_offset[0] * self.width
        new_y = ((self.height - 1) - y) * self.texture_scale[1] + self.texture_offset[1] * self.height
        new_x = min(new_x, self.width - 1)
        new_y = min(new_y, self.height - 1)
        height = self.interpolator.get_value(self.texture_peeker, new_x, new_y)
        return height * self.height_scale# + self.offset

    def heightmap_ready_cb(self, texture, callback, cb_args):
        self.heightmap_ready = True
        #print("READY")
        self.texture_peeker = self.texture.peek()
#         if self.texture_peeker is None:
#             print("NOT READY !!!")
        if callback is not None:
            callback(self, *cb_args)

    def create_heightmap(self, patch, callback=None, cb_args=()):
        if self.texture is None:
            self.texture = Texture()
            self.texture.set_wrap_u(Texture.WMClamp)
            self.texture.set_wrap_v(Texture.WMClamp)
            self.interpolator.configure_texture(self.texture)
            self._make_heightmap(callback, cb_args)
        else:
            if callback is not None:
                callback(self, *cb_args)

    def _make_heightmap(self, callback, cb_args):
        if not self.tex_id in ShaderHeightmap.tex_generators:
            ShaderHeightmap.tex_generators[self.tex_id] = TexGenerator()
            if settings.encode_float:
                texture_format = Texture.F_rgba
            else:
                texture_format = Texture.F_r32
            ShaderHeightmap.tex_generators[self.tex_id].make_buffer(self.width, self.height, texture_format)
        tex_generator = ShaderHeightmap.tex_generators[self.tex_id]
        if self.shader is None:
            self.shader = NoiseShader(noise_source=self.noise,
                                      noise_target=FloatTarget(),
                                      coord = self.coord,
                                      offset = self.offset,
                                      scale = self.scale)
            self.shader.global_frequency = self.global_frequency
            self.shader.global_scale = self.global_scale
            self.shader.create_and_register_shader(None, None)
        tex_generator.generate(self.shader, 0, self.texture, self.heightmap_ready_cb, (callback, cb_args))

class ShaderHeightmapPatchFactory(HeightmapPatchFactory):
    def __init__(self, noise):
        HeightmapPatchFactory.__init__(self)
        self.noise = noise

    def create_patch(self, *args, **kwargs):
        return ShaderHeightmapPatch.create_from_patch(self.noise, *args, **kwargs)

class ShaderHeightmapPatch(HeightmapPatch):
    tex_generators = {}
    cachable = False
    def __init__(self, noise, parent,
                 x0, y0, x1, y1,
                 width, height,
                 scale=1.0,
                 coord=TexCoord.Cylindrical, face=0, border=1):
        HeightmapPatch.__init__(self, parent, x0, y0, x1, y1,
                              width, height,
                              scale,
                              coord, face, border)
        self.shader = None
        self.texture = None
        self.texture_peeker = None
        self.noise = noise
        self.tex_generator = None
        self.callback = None
        self.cloned = False
        self.texture_offset = LVector2()
        self.texture_scale = LVector2(1, 1)
        self.min_height = None
        self.max_height = None
        self.mean_height = None

    def copy_from(self, heightmap_patch):
        self.cloned = True
        self.lod = heightmap_patch.lod
        self.texture = heightmap_patch.texture
        self.texture_peeker = heightmap_patch.texture_peeker
        self.heightmap_ready = heightmap_patch.heightmap_ready

    def get_height(self, x, y):
        if self.texture_peeker is None:
            print("No peeker", self.patch.str_id(), self.patch.instance_ready)
            traceback.print_stack()
            return 0.0
        new_x = x * self.texture_scale[0] + self.texture_offset[0] * self.width
        new_y = ((self.height - 1) - y) * self.texture_scale[1] + self.texture_offset[1] * self.height
        new_x = min(new_x, self.width - 1)
        new_y = min(new_y, self.height - 1)
        height = self.parent.interpolator.get_value(self.texture_peeker, new_x, new_y)
        #TODO: This should be done in PatchedHeightmap.get_height()
        return height * self.parent.height_scale# + self.parent.offset

    def generate(self, callback, cb_args=()):
        if self.texture is None:
            self.texture = Texture()
            self.texture.set_wrap_u(Texture.WMClamp)
            self.texture.set_wrap_v(Texture.WMClamp)
            self.parent.interpolator.configure_texture(self.texture)
            self._make_heightmap(callback, cb_args)
        else:
            if callback is not None:
                callback(self, *cb_args)

    def heightmap_ready_cb(self, texture, callback, cb_args):
        #print("READY", self.patch.str_id())
        self.texture_peeker = self.texture.peek()
#         if self.texture_peeker is None:
#             print("NOT READY !!!")
        self.heightmap_ready = True
        data = self.texture.getRamImage()
        if sys.version_info[0] < 3:
            buf = data.getData()
            np_buffer = numpy.fromstring(buf, dtype=numpy.float32)
        else:
            np_buffer = numpy.frombuffer(data, numpy.float32)
        np_buffer.shape = (self.texture.getYSize(), self.texture.getXSize(), self.texture.getNumComponents())
        self.min_height = np_buffer.min()
        self.max_height = np_buffer.max()
        self.mean_height = np_buffer.mean()
        if callback is not None:
            callback(self, *cb_args)

    def _make_heightmap(self, callback, cb_args):
        if not self.width in ShaderHeightmapPatch.tex_generators:
            ShaderHeightmapPatch.tex_generators[self.width] = GeneratorPool(settings.patch_pool_size)
            if settings.encode_float:
                texture_format = Texture.F_rgba
            else:
                texture_format = Texture.F_r32
            ShaderHeightmapPatch.tex_generators[self.width].make_buffer(self.width, self.height, texture_format)
        tex_generator = ShaderHeightmapPatch.tex_generators[self.width]
        if self.shader is None:
            self.shader = NoiseShader(coord=self.coord,
                                      noise_source=self.noise,
                                      noise_target=FloatTarget(),
                                      offset=(self.x0, self.y0, 0.0),
                                      scale=(self.lod_scale_x, self.lod_scale_y, 1.0))
            self.shader.global_frequency = self.parent.global_frequency
            self.shader.global_scale = self.parent.global_scale
            self.shader.create_and_register_shader(None, None)
        tex_generator.generate(self.shader, self.face, self.texture, self.heightmap_ready_cb, (callback, cb_args))
