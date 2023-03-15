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


from panda3d.core import Texture, LColor

from .patcheddata import PatchData, PatchedData
from .shapedata import TextureShapeDataBase
from .shaders.data_source.heightmap import HeightmapShaderDataSource
from .textures import TexCoord, AutoTextureSource, TextureBase, HeightMapTexture
from .textures import TextureConfiguration
from .interpolators import HardwareInterpolator
from .filters import BilinearFilter
from .dircontext import defaultDirContext

import traceback
import numpy

#TODO: HeightmapPatch has common code with Heightmap and TextureHeightmapBase, this should be refactored
#TODO: Texture data should be refactored like appearance to be fully independent from the source

class HeightmapPatch(PatchData):
    def __init__(self, parent, patch, width, height, overlap):
        PatchData.__init__(self, parent, patch, width, height, overlap)
        self.texture_peeker = None
        self.min_height = None
        self.max_height = None
        self.mean_height = None

    def copy_from(self, parent_data):
        PatchData.copy_from(self, parent_data)
        self.texture_peeker = parent_data.texture_peeker
        self.min_height = parent_data.min_height
        self.max_height = parent_data.max_height
        self.mean_height = parent_data.mean_height

    def set_height(self, x, y, height):
        pass

    def get_height(self, x, y, shape_patch=None):
        if self.texture_peeker is None:
            print("No peeker", self.patch.str_id(), self.patch.instance_ready)
            traceback.print_stack()
            return 0.0
        if shape_patch is not None and self.patch is not shape_patch:
            texture_offset, texture_scale = self.calc_scale_and_offset(shape_patch)
        else:
            texture_offset = self.texture_offset
            texture_scale = self.texture_scale
        new_x = x * texture_scale[0] + texture_offset[0] * self.width
        new_y = y * texture_scale[1] + texture_offset[1] * self.height
        new_x = min(new_x, self.width - 1)
        new_y = min(new_y, self.height - 1)
        height = self.parent.filter.get_value(self.texture_peeker, new_x, new_y)
        #TODO: This should be done in PatchedHeightmap.get_height()
        return height * self.parent.height_scale + self.parent.height_offset

    def get_height_uv(self, u, v, shape_patch=None):
        return self.get_height(u * self.width, v * self.height, shape_patch)

    def apply(self, instance):
        name = self.parent.name
        instance.set_shader_input('heightmap_%s' % name, self.texture)
        #TODO: replace this by a vec3
        instance.set_shader_input("heightmap_%s_height_scale" % name, self.parent.get_height_scale(self.patch))
        instance.set_shader_input("heightmap_%s_u_scale" % name, self.parent.get_u_scale(self.patch))
        instance.set_shader_input("heightmap_%s_v_scale" % name, self.parent.get_v_scale(self.patch))
        instance.set_shader_input("heightmap_%s_offset" % name, self.texture_offset)
        instance.set_shader_input("heightmap_%s_scale" % name, self.texture_scale)

    def clear(self, instance):
        PatchData.clear(self, instance)
        self.texture_peeker = None

    def collect_shader_data(self, data):
        # Data is set as RGBA, but stored as BGRA
        data += [self.parent.get_v_scale(self.patch),
                 self.parent.get_u_scale(self.patch),
                 self.parent.get_height_scale(self.patch),
                 0.0,
                 self.texture_scale[0],
                 self.texture_offset[1],
                 self.texture_offset[0],
                 self.texture_scale[1]]

    def create_texture_config(self):
        texture_config = TextureConfiguration(wrap_u=Texture.WMClamp,
                                              wrap_v=Texture.WMClamp)
        self.parent.filter.update_texture_config(texture_config)
        return texture_config

    def retrieve_texture_data(self):
        self.texture_peeker = self.texture.peek()
#       if self.texture_peeker is None:
#           print("NOT READY !!!")
        data = self.texture.getRamImage()
        #TODO: should be completed and refactored
        signed = False
        component_type = self.texture.getComponentType()
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
        np_buffer = numpy.frombuffer(data, buffer_type)
        np_buffer.shape = (self.texture.getYSize(), self.texture.getXSize(), self.texture.getNumComponents())
        self.min_height = np_buffer.min() / scale
        self.max_height = np_buffer.max() / scale
        self.mean_height = np_buffer.mean() / scale

    def make_default_data(self):
        texture = Texture()
        texture.setup_2d_texture(1, 1, Texture.T_float, Texture.F_r32)
        texture.set_clear_color(LColor(0, 0, 0, 0))
        texture.make_ram_image()
        return texture

class TextureHeightmapPatch(HeightmapPatch):
    def __init__(self, data_source, parent, patch, width, height, overlap):
        HeightmapPatch.__init__(self, parent, patch, width, height, overlap)
        self.data_source = data_source

    def apply(self, instance):
        self.data_source.apply(self.patch, instance, "heightmap_%s" % self.parent.name)
        HeightmapPatch.apply(self, instance)

    async def do_load(self, tasks_tree, patch):
        texture_config = self.create_texture_config()
        await self.data_source.load(tasks_tree, patch, texture_config)
        (texture_data, texture_size, texture_lod) = self.data_source.source.get_texture(patch, strict=True)
        if texture_data is not None:
            self.configure_data(texture_data)

    def clear(self, instance):
        HeightmapPatch.clear(self, instance)
        self.data_source.clear(self.patch, instance)


class HeightmapBase():
    def __init__(self, width, height, min_height, max_height, height_scale, height_offset, interpolator=None, filter=None):
        self.width = width
        self.height = height
        self.min_height = min_height
        self.max_height = max_height
        self.height_scale = height_scale
        self.height_offset = height_offset
        self.u_scale = 1.0 / width
        self.v_scale = 1.0 / height
        if interpolator is None:
            interpolator = HardwareInterpolator()
        self.interpolator = interpolator
        if filter is None:
            filter = BilinearFilter(self.interpolator)
        self.filter = filter

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

    def set_height(self, x, y, height):
        pass

    def get_height(self, x, y):
        return None

    def get_height_uv(self, u, v):
        return self.get_height(u * self.width, v * self.height)

class TextureHeightmapBase(HeightmapBase, TextureShapeDataBase):
    def __init__(self, name, width, height, min_height, max_height, height_scale, height_offset, interpolator, filter):
        HeightmapBase.__init__(self, width, height, min_height, max_height, height_scale, height_offset, interpolator, filter)
        TextureShapeDataBase.__init__(self, name, width, height)
        self.texture_peeker = None

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

    def configure_texture(self, texture):
        texture.set_wrap_u(Texture.WMClamp)
        texture.set_wrap_v(Texture.WMClamp)
        self.filter.configure_texture(texture)
        self.texture_peeker = self.texture.peek()
        data = self.texture.getRamImage()
        np_buffer = numpy.frombuffer(data, numpy.float32)
        np_buffer.shape = (self.texture.getYSize(), self.texture.getXSize(), self.texture.getNumComponents())
        self.min_height = np_buffer.min()
        self.max_height = np_buffer.max()
        self.mean_height = np_buffer.mean()


class TextureHeightmap(TextureHeightmapBase):
    def __init__(self, name, width, height, min_height, max_height, height_scale, height_offset, data_source, offset=None, scale=None, coord = TexCoord.Cylindrical, interpolator=None, filter=None):
        TextureHeightmapBase.__init__(self, name, width, height, min_height, max_height, height_scale,  height_offset, interpolator, filter)
        self.data_source = data_source

    def set_data_source(self, data_source, context=defaultDirContext):
        if data_source is not None and not isinstance(data_source, TextureBase):
            data_source = HeightMapTexture(AutoTextureSource(data_source, None, context))
        self.data_source = data_source

    async def load(self, shape):
        await self.data_source.load(shape)
        (texture_data, texture_size, texture_lod) = self.data_source.source.get_texture(strict=True)
        self.configure_data(texture_data)


class PatchedHeightmapBase(HeightmapBase, PatchedData):
    def __init__(self, name, size, min_height, max_height, height_scale, height_offset, overlap, interpolator=None, filter=None, max_lod=100):
        HeightmapBase.__init__(self, size, size, min_height, max_height, height_scale, height_offset, interpolator, filter)
        PatchedData.__init__(self, name, size, overlap, max_lod)
        self.normal_scale_lod = True

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

    def get_data_source(self, data_store):
        return HeightmapShaderDataSource(self, data_store)

    def get_nb_shader_data(self):
        return 8

class TexturePatchedHeightmap(PatchedHeightmapBase):
    def __init__(self, name, data_source, size, min_height, max_height, height_scale, height_offset, overlap, interpolator=None, filter=None, max_lod=100):
        PatchedHeightmapBase.__init__(self, name, size, min_height, max_height, height_scale, height_offset, overlap, interpolator, filter, max_lod)
        self.data_source = data_source

    def use(self, count=1):
        PatchedHeightmapBase.use(self, count)
        self.data_source.use(count)

    def release(self, count=1):
        PatchedHeightmapBase.use(self, count)
        self.data_source.release(count)

    def do_create_patch_data(self, patch):
        return TextureHeightmapPatch(self.data_source, self, patch, self.size, self.size, self.overlap)

    def clear(self, patch, instance):
        PatchedHeightmapBase.clear(self, patch, instance)
        self.data_source.clear(patch, instance)


class StackedHeightmapPatch(HeightmapPatch):
    def __init__(self, patches, parent, patch, width, height, overlap):
        HeightmapPatch.__init__(self, parent, patch, width, height, overlap)
        self.patches = patches

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

    def load(self):
        if self.count != None: return
        for patch in self.patches:
            patch.load()


class StackedPatchedHeightmap(PatchedHeightmapBase):
    def __init__(self, name, size, height_scale, heightmaps):
        PatchedHeightmapBase.__init__(self, name, size, height_scale)
        self.heightmaps = heightmaps

    def do_create_patch_data(self, patch):
        patches = []
        for heightmap in self.heightmaps:
            patches.append(heightmap.do_create_patch_data(self, patch, self.size, self.size, self.overlap))
        return StackedHeightmapPatch(patches, self, patch, self.size, self.size, self.overlap)


class HeightmapRegistry():
    def __init__(self):
        self.db_map = {}

    def register(self, name, heightmap):
        self.db_map[name] = heightmap

    def get(self, name):
        return self.db_map.get(name, None)

heightmapRegistry = HeightmapRegistry()
