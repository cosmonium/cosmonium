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

from panda3d.core import LVector2, Texture, LColor

from .patchedshapes import PatchLodControl
from .textures import TexCoord, AutoTextureSource, TextureBase, HeightMapTexture
from .interpolators import HardwareInterpolator
from .filters import BilinearFilter
from .dircontext import defaultDirContext

import traceback
import numpy
import sys

#TODO: HeightmapPatch has common code with Heightmap and TextureHeightmapBase, this should be refactored
#TODO: Texture data should be refactored like appearance to be fully independent from the source

class HeightmapPatch:
    cachable = True
    def __init__(self, parent,
                 x0, y0, x1, y1,
                 width, height,
                 scale = 1.0,
                 coord=TexCoord.Cylindrical, face=-1, overlap=0):
        self.parent = parent
        self.x0 = x0
        self.y0 = y0
        self.x1 = x1
        self.y1 = y1
        self.scale = scale
        self.width = width
        self.height = height
        self.coord = coord
        self.face = face
        self.overlap = overlap
        self.r_width = self.width - self.overlap * 2
        self.r_height = self.height - self.overlap * 2
        self.r_x0 = self.x0 - overlap / self.r_width * (self.x1 - self.x0)
        self.r_x1 = self.x1 + overlap / self.r_width * (self.x1 - self.x0)
        self.r_y0 = self.y0 - overlap / self.r_height * (self.y1 - self.y0)
        self.r_y1 = self.y1 + overlap / self.r_height * (self.y1 - self.y0)
        self.lod = None
        self.patch = None
        self.heightmap_ready = False
        self.texture = None
        self.texture_peeker = None
        self.callback = None
        self.cloned = False
        self.texture_offset = LVector2((self.overlap + 0.5) / self.width, (self.overlap + 0.5) / self.height)
        self.texture_scale = LVector2((self.width - self.overlap * 2 - 1) / self.width, (self.height - self.overlap * 2 - 1) / self.height)
        self.min_height = None
        self.max_height = None
        self.mean_height = None

    @classmethod
    def create_from_patch(cls, noise, parent,
                          x, y, scale, lod, density,
                          coord=TexCoord.Cylindrical, face=-1, overlap=0):
        #TODO: Should be move to Patch/Tile
        if coord == TexCoord.Cylindrical:
            r_div = 1 << lod
            s_div = 2 << lod
            x0 = float(x) / s_div
            y0 = float(y) / r_div
            x1 = float(x + 1) / s_div
            y1 = float(y + 1) / r_div
        elif coord == TexCoord.NormalizedCube or coord == TexCoord.SqrtCube:
            div = 1 << lod
            r_div = div
            s_div = div
            x0 = float(x) / div
            y0 = float(y) / div
            x1 = float(x + 1) / div
            y1 = float(y + 1) / div
        else:
            div = 1 << lod
            r_div = div
            s_div = div
            size = 1.0 / (1 << lod)
            x0 = (x) * scale
            y0 = (y) * scale
            x1 = (x + size) * scale
            y1 = (y + size) * scale
        patch = cls(noise, parent,
                    x0, y0, x1, y1,
                    width=density, height=density,
                    scale=scale,
                    coord=coord, face=face, overlap=overlap)
        patch.patch_lod = lod
        patch.lod = lod
        patch.density = density
        patch.x = x
        patch.y = y
        return patch

    def copy_from(self, heightmap_patch):
        self.cloned = True
        self.lod = heightmap_patch.lod
        self.texture = heightmap_patch.texture
        self.texture_peeker = heightmap_patch.texture_peeker
        self.heightmap_ready = heightmap_patch.heightmap_ready
        self.min_height = heightmap_patch.min_height
        self.max_height = heightmap_patch.max_height
        self.mean_height = heightmap_patch.mean_height

    def calc_sub_patch(self):
        self.copy_from(self.parent_heightmap)
        delta = self.patch.lod - self.lod
        scale = 1 << delta
        if self.patch.coord != TexCoord.Flat:
            x_tex = (self.x // scale) * scale
            y_tex = (self.y // scale) * scale
            x_delta = (self.x - x_tex) / scale
            y_delta = (self.y - y_tex) / scale
        else:
            x_tex = int(self.x * scale) / scale
            y_tex = int(self.y * scale) / scale
            x_delta = self.x - x_tex
            y_delta = self.y - y_tex
        r_scale_x = (self.width - self.overlap * 2 - 1) / self.width
        r_scale_y = (self.height - self.overlap * 2 - 1) / self.height
        self.texture_offset = LVector2((self.overlap + 0.5) / self.width + x_delta * r_scale_x, (self.overlap + 0.5) / self.height + y_delta * r_scale_y)
        self.texture_scale = LVector2(r_scale_x / scale, r_scale_y / scale)

    def is_ready(self):
        return self.heightmap_ready

    def set_height(self, x, y, height):
        pass

    def get_height(self, x, y):
        if self.texture_peeker is None:
            print("No peeker", self.patch.str_id(), self.patch.instance_ready)
            traceback.print_stack()
            return 0.0
        new_x = x * self.texture_scale[0] + self.texture_offset[0] * self.width
        new_y = y * self.texture_scale[1] + self.texture_offset[1] * self.height
        new_x = min(new_x, self.width - 1)
        new_y = min(new_y, self.height - 1)
        height = self.parent.filter.get_value(self.texture_peeker, new_x, new_y)
        #TODO: This should be done in PatchedHeightmap.get_height()
        return height * self.parent.height_scale + self.parent.height_offset

    def get_height_uv(self, u, v):
        return self.get_height(u * self.width, v * self.height)

    def load(self, patch, callback, cb_args=()):
        if self.texture is None:
            self.texture = Texture()
            self.texture.set_wrap_u(Texture.WMClamp)
            self.texture.set_wrap_v(Texture.WMClamp)
            self.parent.filter.configure_texture(self.texture)
            self.do_load(patch, callback, cb_args)
        else:
            if callback is not None:
                callback(self, *cb_args)

    def heightmap_ready_cb(self, texture, callback, cb_args):
        if texture is not None:
            self.texture = texture
            #print("READY", self.patch.str_id(), texture, self.texture)
            self.texture_peeker = texture.peek()
#           if self.texture_peeker is None:
#               print("NOT READY !!!")
            self.heightmap_ready = True
            data = self.texture.getRamImage()
            #TODO: should be completed and refactored
            signed = False
            component_type = texture.getComponentType()
            if component_type == Texture.T_float:
                buffer_type = numpy.float32
                scale = 1.0
            elif component_type == Texture.T_unsigned_byte:
                if signed:
                    buffer_type = numpy.int8
                    scale = 128.0
                else:
                    buffer_type = numpy.uint8
                    scale = 255.0
            elif component_type == Texture.T_unsigned_short:
                if signed:
                    buffer_type = numpy.int16
                    scale = 32768.0
                else:
                    buffer_type = numpy.uint16
                    scale = 65535.0
            if sys.version_info[0] < 3:
                buf = data.getData()
                np_buffer = numpy.fromstring(buf, dtype=buffer_type)
            else:
                np_buffer = numpy.frombuffer(data, buffer_type)
            np_buffer.shape = (self.texture.getYSize(), self.texture.getXSize(), self.texture.getNumComponents())
            self.min_height = np_buffer.min() / scale
            self.max_height = np_buffer.max() / scale
            self.mean_height = np_buffer.mean() / scale
        else:
            if self.parent_heightmap is not None:
                self.calc_sub_patch()
            else:
                print("Make default texture for heightmap")
                texture = Texture()
                texture.setup_2d_texture(1, 1, Texture.T_float, Texture.F_r32)
                texture.set_clear_color(LColor(0, 0, 0, 0))
                texture.make_ram_image()
                self.heightmap_ready_cb(texture, None, None)
        if callback is not None:
            callback(self, *cb_args)

    def do_load(self, patch, callback, cb_args):
        pass

class TextureHeightmapPatch(HeightmapPatch):
    def __init__(self, data_source, parent, x0, y0, x1, y1, width, height, scale, coord, face, overlap):
        HeightmapPatch.__init__(self, parent, x0, y0, x1, y1, width, height, scale, coord, face, overlap)
        self.data_source = data_source

    def apply(self, patch):
        self.data_source.apply(patch, "heightmap_%s" % self.parent.name)

    def texture_loaded_cb(self, texture, patch, callback, cb_args):
        (texture_data, texture_size, texture_lod) = self.data_source.source.get_texture(patch, strict=True)
        self.heightmap_ready_cb(texture_data, callback, cb_args)

    def do_load(self, patch, callback, cb_args):
        self.data_source.load(patch, self.texture_loaded_cb, (patch, callback, cb_args))

class HeightmapPatchFactory(object):
    def create_patch(self, *args, **kwargs):
        return None

class TextureHeightmapPatchFactory(HeightmapPatchFactory):
    def __init__(self, data_source):
        HeightmapPatchFactory.__init__(self)
        self.data_source = data_source

    def create_patch(self, *args, **kwargs):
        return TextureHeightmapPatch.create_from_patch(self.data_source, *args, **kwargs)

class Heightmap(object):
    def __init__(self, name, width, height, min_height, max_height, height_scale, height_offset, u_scale, v_scale, interpolator=None, filter=None):
        self.name = name
        self.width = width
        self.height = height
        self.min_height = min_height
        self.max_height = max_height
        self.height_scale = height_scale
        self.height_offset = height_offset
        self.u_scale = float(u_scale) / width
        self.v_scale = float(v_scale) / height
        if interpolator is None:
            interpolator = HardwareInterpolator()
        self.interpolator = interpolator
        if filter is None:
            filter = BilinearFilter()
        self.filter = filter
        self.heightmap_ready = False

    def set_size(self, width, height):
        u_scale = self.u_scale * self.width
        v_scale = self.v_scale * self.height
        self.width = width
        self.height = height
        self.u_scale = u_scale / self.width
        self.v_scale = v_scale / self.height

    def set_height_scale(self, height_scale):
        self.height_scale = height_scale

    def get_height_scale(self, patch):
        return self.height_scale

    def set_u_scale(self, scale):
        self.u_scale = scale / self.width

    def set_v_scale(self, scale):
        self.v_scale = scale / self.height

    def get_u_scale(self, patch):
        return self.u_scale

    def get_v_scale(self, patch):
        return self.v_scale

    def is_ready(self):
        return self.heightmap_ready

    def set_height(self, x, y, height):
        pass

    def get_height(self, x, y):
        return None

    def get_height_uv(self, u, v):
        return self.get_height(u * self.width, v * self.height)

    def get_heightmap(self, patch):
        return self

    def create_heightmap(self, patch, callback=None, cb_args=()):
        return None

class TextureHeightmapBase(Heightmap):
    def __init__(self, name, width, height, min_height, max_height, height_scale, height_offset, u_scale, v_scale, interpolator, filter):
        Heightmap.__init__(self, name, width, height, min_height, max_height, height_scale, height_offset, u_scale, v_scale, interpolator, filter)
        self.texture = None
        self.texture_offset = LVector2()
        self.texture_scale = LVector2(1, 1)
        self.tex_id = str(width) + ':' + str(height)

    def reset(self):
        self.texture = None

    def get_texture_offset(self, patch):
        return self.texture_offset

    def get_texture_scale(self, patch):
        return self.texture_scale

        return self.heightmap_ready

    def set_height(self, x, y, height):
        pass

    def get_height(self, x, y):
        if self.texture_peeker is None:
            print("No peeker")
            traceback.print_stack()
            return 0.0
        new_x = x * self.texture_scale[0] + self.texture_offset[0] * self.width
        new_y = y * self.texture_scale[1] + self.texture_offset[1] * self.height
        new_x = min(new_x, self.width - 1)
        new_y = min(new_y, self.height - 1)
        height = self.filter.get_value(self.texture_peeker, new_x, new_y)
        return height * self.height_scale + self.height_offset

    def create_heightmap(self, shape, callback=None, cb_args=()):
        return self.load(shape, callback, cb_args)

    def load(self, shape, callback, cb_args=()):
        if self.texture is None:
            self.texture = Texture()
            self.texture.set_wrap_u(Texture.WMClamp)
            self.texture.set_wrap_v(Texture.WMClamp)
            self.filter.configure_texture(self.texture)
            self.do_load(shape, self.heightmap_ready_cb, (callback, cb_args))
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

    def do_load(self, shape, callback, cb_args):
        pass

class TextureHeightmap(TextureHeightmapBase):
    def __init__(self, name, width, height, min_height, max_height, height_scale, height_offset, data_source, offset=None, scale=None, coord = TexCoord.Cylindrical, interpolator=None, filter=None):
        TextureHeightmapBase.__init__(self, name, width, height, min_height, max_height, height_scale,  height_offset, 1.0, 1.0, interpolator, filter)
        self.data_source = data_source

    def set_data_source(self, data_source, context=defaultDirContext):
        if data_source is not None and not isinstance(data_source, TextureBase):
            data_source = HeightMapTexture(AutoTextureSource(data_source, None, context))
        self.data_source = data_source

    def do_load(self, shape, callback, cb_args):
        self.data_source.load(shape, self.heightmap_ready_cb, (callback, cb_args))

class PatchedHeightmap(Heightmap):
    def __init__(self, name, size, min_height, max_height, height_scale, height_offset, u_scale, v_scale, overlap, patch_factory, interpolator=None, filter=None, max_lod=100):
        Heightmap.__init__(self, name, size, size, min_height, max_height, height_scale, height_offset, u_scale, v_scale, interpolator, filter)
        self.size = size
        self.overlap = overlap
        self.patch_factory = patch_factory
        self.max_lod = max_lod
        self.normal_scale_lod = True
        self.map_patch = {}

    def get_u_scale(self, patch):
        if self.normal_scale_lod:
            factor = 1 << patch.lod
            return self.u_scale / factor
        else:
            return self.u_scale

    def get_v_scale(self, patch):
        if self.normal_scale_lod:
            factor = 1 << patch.lod
            return self.v_scale / factor
        else:
            return self.v_scale

    def get_texture_offset(self, patch):
        return self.map_patch[patch.str_id()].texture_offset

    def get_texture_scale(self, patch):
        return self.map_patch[patch.str_id()].texture_scale

    def get_heightmap(self, patch):
        return self.map_patch.get(patch.str_id(), None)

    def create_heightmap(self, patch, callback=None, cb_args=()):
        if not patch.str_id() in self.map_patch:
            #TODO: Should be done by inheritance
            if patch.coord == TexCoord.Cylindrical:
                x = patch.sector
                y = patch.ring
                face = -1
            elif patch.coord == TexCoord.Flat:
                x = patch.x
                y = patch.y
                face = -1
            else:
                x = patch.x
                y = patch.y
                face = patch.face
            #TODO: Should be done with a factory
            heightmap = self.patch_factory.create_patch(parent=self, x=x, y=y, scale=patch.scale, lod=patch.lod, density=self.size,
                                                       coord=patch.coord, face=face, overlap=self.overlap)
            self.map_patch[patch.str_id()] = heightmap
            #TODO: Should be linked properly
            heightmap.patch = patch
            if patch.parent is not None:
                heightmap.parent_heightmap = self.map_patch[patch.parent.str_id()]
            else:
                heightmap.parent_heightmap = None
            if patch.lod > self.max_lod and patch.parent is not None:
                #print("CLONE", patch.str_id())
                heightmap.calc_sub_patch()
                #print(patch.str_id(), ':', parent_heightmap.lod, heightmap.texture_offset, heightmap.texture_scale)
                if callback is not None:
                    callback(heightmap, *cb_args)
            else:
                #print("GEN", patch.str_id())
                heightmap.load(patch, callback, cb_args)
        else:
            #print("CACHE", patch.str_id())
            heightmap = self.map_patch[patch.str_id()]
            if heightmap.is_ready() and callback is not None:
                callback(heightmap, *cb_args)
            else:
                print("PATCH NOT READY?", heightmap.heightmap_ready, callback)

    def apply(self, patch):
        heightmap = self.map_patch[patch.str_id()]
        heightmap.apply(patch)

class StackedHeightmapPatch(HeightmapPatch):
    def __init__(self, patches, *args, **kwargs):
        HeightmapPatch.__init__(self, *args, **kwargs)
        self.patches = patches
        self.callback = None
        self.count = None

    def is_ready(self):
        if self.count is None or self.count != len(self.patches):
            return False
        for patch in self.patches:
            if not patch.is_ready():
                return False
        return True

    def get_height(self, x, y):
        height = 0.0
        for patch in self.patches:
            height += patch.get_height(x, y)
        return height

    def sub_callback(self, patch):
        self.count += 1
        if self.count == len(self.patches):
            self.callback(self.patch)

    def load(self, callback):
        if self.count != None: return
        self.count = 0
        self.callback = callback
        for patch in self.patches:
            patch.load(self.sub_callback)

class StackedHeightmapPatchFactory(HeightmapPatchFactory):
    def __init__(self, heightmaps):
        HeightmapPatchFactory.__init__(self)
        self.heightmaps = heightmaps

    def create_patch(self, *args, **kwargs):
        patches = []
        for heightmap in self.heightmaps:
            kwargs['parent'] = heightmap
            patches.append(heightmap.patch_factory.create_patch(*args, **kwargs))
        return StackedHeightmapPatch.create_from_patch(patches, *args, **kwargs)

class StackedPatchedHeightmap(PatchedHeightmap):
    def __init__(self, name, size, height_scale, u_scale, v_scale, heightmaps, callback=None):
        PatchedHeightmap.__init__(self, name, size, height_scale, u_scale, v_scale, StackedHeightmapPatchFactory(heightmaps), callback)
        self.heightmaps = heightmaps

class TerrainPatchLodControl(PatchLodControl):
    def __init__(self, heightmap, factor = 1.0, max_lod=100):
        self.heightmap = heightmap
        self.max_lod = max_lod
        self.patch_size = heightmap.size * factor

    def should_split(self, patch, apparent_patch_size, distance):
        if apparent_patch_size > self.patch_size * 1.01 and patch.lod < self.max_lod:
            print(patch.str_id(), apparent_patch_size, self.patch_size, patch.distance, patch.average_height)
        return apparent_patch_size > self.patch_size * 1.01 and patch.lod < self.max_lod

    def should_merge(self, patch, apparent_patch_size, distance):
        return apparent_patch_size < self.patch_size / 1.99

class HeightmapRegistry():
    def __init__(self):
        self.db_map = {}

    def register(self, name, heightmap):
        self.db_map[name] = heightmap

    def get(self, name):
        return self.db_map.get(name, None)

heightmapRegistry = HeightmapRegistry()
