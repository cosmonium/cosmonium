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

from panda3d.core import PNMImage, Texture

from math import pi
from cosmonium import cache
import os
from cosmonium.textures import TextureSource

class TerrainPatch:
    cachable = True
    def __init__(self, x0, y0, x1, y1,
                 width, height,
                 scale = 1.0,
                 cylindrical_map=True, cube_map=False, face=-1, border=1):
        self.x0 = x0
        self.y0 = y0
        self.x1 = x1
        self.y1 = y1
        self.scale = scale
        self.width = width
        self.height = height
        self.cylindrical_map = cylindrical_map
        self.cube_map = cube_map
        self.face = face
        self.border = border
        self.r_width = self.width + self.border * 2
        self.r_height = self.height + self.border * 2
        self.r_x0 = self.x0 - float(self.border)/self.width * (self.x1 - self.x0)
        self.r_x1 = self.x1 + float(self.border)/self.width * (self.x1 - self.x0)
        self.r_y0 = self.y0 - float(self.border)/self.height * (self.y1 - self.y0)
        self.r_y1 = self.y1 + float(self.border)/self.height * (self.y1 - self.y0)
        self.dx = self.r_x1 - self.r_x0
        self.dy = self.r_y1 - self.r_y0
        self.lod = None

    @classmethod
    def create_from_patch(cls, noise,
                          x, y, lod, density,
                          cylindrical_map=True, cube_map=False, face=-1):
        r_div = 1 << lod
        if cylindrical_map:
            s_div = 2 << lod
        else:
            s_div = 1 << lod
        x0 = float(x) / s_div
        y0 = float(y) / r_div
        x1 = float(x + 1) / s_div
        y1 = float(y + 1) / r_div
        patch = cls(noise,
                    x0, y0, x1, y1,
                    width=density, height=density,
                    scale=1.0,
                    cylindrical_map=cylindrical_map, cube_map=cube_map, face=face, border=1)
        patch.lod = lod
        patch.lod_scale_x = 1.0 / s_div
        patch.lod_scale_y = 1.0 / r_div
        patch.density = density
        patch.x = x
        patch.y = y
        return patch

class CachedTerrainPatch(TerrainPatch):
    def __init__(self, id, patch):
        self.id = id
        self.patch = patch
        if patch.lod is not None:
            self.path = "%d" % patch.lod
            self.name = "%d-%d-%d" % (patch.density, patch.x, patch.y)
        else:
            self.path = ''
            self.name = str(self.patch.width) + "-" + str(self.patch.height) + '-' + str(self.patch.x0) + '-' + str(self.patch.y0) + '-' + str(self.patch.x1) + '-'+ str(self.patch.y1)
        if patch.face != -1:
            self.name += '-%d' % patch.face

    def get_terrain_file_name(self, category=None):
        if category is not None:
            category = '-' + category
        else:
            category = ''
        path = cache.create_path_for(self.id, self.path)
        return os.path.join(path, self.name + category + ".png")

    def load_terrain_map(self):
        image = PNMImage()
        if image.read(self.get_terrain_file_name()):
            for y in range(self.patch.r_height):
                for x in range(self.patch.r_width):
                    self.patch.set_height(x, y, image.getGray(x, y))
            return True
        else:
            return False
    
    def store_terrain_map(self):
        image = self.make_terrain_heightmap()
        image.write(self.get_terrain_file_name())

    def make_terrain_heightmap(self):
        return self.patch.make_terrain_heightmap()

    def make_terrain_map(self):
        if self.load_terrain_map():
            return
        self.patch.make_terrain_map()
        self.store_terrain_map()

    def refine_terrain_map(self, factor=2):
        if self.load_terrain_map():
            return
        self.patch.refine_terrain_map(factor)
        self.store_terrain_map()
        
    def load_image(self, category, grayscale=False):
        image = PNMImage()
        if image.read(self.get_terrain_file_name(category)):
            if grayscale:
                image.makeGrayscale()
            return image
        else:
            return None
    
    def store_image(self, image, category):
        image.write(self.get_terrain_file_name(category))

    def make_terrain_normal(self, x_scale, y_scale):
        p = self.load_image('norm')
        if p: return p
        p = self.patch.make_terrain_normal(x_scale, y_scale)
        self.store_image(p, 'norm')
        return p
    
    def make_terrain_specular(self):
        p = self.load_image('spec', grayscale=True)
        if p: return p
        p = self.patch.make_terrain_specular()
        self.store_image(p, 'spec')
        return p
    
    def make_terrain_texture(self):
        p = self.load_image('tex')
        if p: return p
        p = self.patch.make_terrain_texture()
        self.store_image(p, 'tex')
        return p


class TerrainNormalMap(TextureSource):
    cached = True
    def __init__(self, terrain, radius, height_scale):
        TextureSource.__init__(self)
        self.terrain = terrain
        self.loaded = False
        self.texture = None
        perimeter = 2.0 * pi * radius
        self.x_scale = (terrain.width / perimeter) * height_scale
        self.y_scale = (terrain.height / perimeter) * height_scale

    def load(self, patch, grayscale=False):
        if not self.loaded:
            image = self.terrain.make_terrain_normal(self.x_scale, self.y_scale)
            self.texture = Texture()
            self.texture.load(image)
            self.loaded = True
        return (self.texture, 0, 0)
