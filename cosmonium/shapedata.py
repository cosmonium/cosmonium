#
#This file is part of Cosmonium.
#
#Copyright (C) 2018-2021 Laurent Deru.
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

from panda3d.core import LVector2

from .textures import TextureBase
from .dircontext import defaultDirContext

class ShapeData:
    def __init__(self, name):
        self.name = name
        self.data_ready = False

    def is_ready(self):
        return self.data_ready

    def get_data(self):
        return self

    def create_data(self):
        return None

    async def load(self):
        pass

    def clear(self):
        pass

class TextureShapeDataBase(ShapeData):
    def __init__(self, name, width, height):
        ShapeData.__init__(self, name)
        self.width = width
        self.height = height
        self.texture = None
        self.texture_offset = LVector2()
        self.texture_scale = LVector2(1, 1)
        self.tex_id = str(width) + ':' + str(height)

    def set_size(self, width, height):
        self.width = width
        self.height = height

    def reset(self):
        self.texture = None

    def get_texture_offset(self):
        return self.texture_offset

    def get_texture_scale(self):
        return self.texture_scale

    def configure_texture(self, texture):
        pass

    def make_default_data(self):
        return None

    def configure_data(self, texture):
        if texture is not None:
            self.texture = texture
            self.configure_texture(texture)
            self.data_ready = True
        else:
            print("Make default data")
            self.configure_data(self.make_default_data())

    def clear(self):
        self.texture = None
        self.data_ready = False

class TextureShapeData(TextureShapeDataBase):
    def __init__(self, name, width, height, data_source):
        TextureShapeDataBase.__init__(self, name, width, height)
        self.data_source = data_source

    def create_auto_texture(self, data_source, context):
        return None

    def set_data_source(self, data_source, context=defaultDirContext):
        if data_source is not None and not isinstance(data_source, TextureBase):
            data_source = self.create_auto_texture(data_source, context)
        self.data_source = data_source

    async def load(self, shape):
        await self.data_source.load(shape)
        (texture_data, texture_size, texture_lod) = self.data_source.source.get_texture(strict=True)
        self.configure_data(texture_data)

    def clear(self):
        TextureShapeDataBase.clear(self)
        self.data_source.clear()
