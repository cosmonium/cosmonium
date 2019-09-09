from __future__ import print_function

from panda3d.core import LVector2

from ..patchedshapes import PatchLodControl
from ..textures import TexCoord

from math import floor, ceil

class HeightmapPatch:
    cachable = True
    def __init__(self, parent,
                 x0, y0, x1, y1,
                 width, height,
                 scale = 1.0,
                 coord=TexCoord.Cylindrical, face=-1, border=1):
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
        self.patch = None
        self.heightmap_ready = False

    @classmethod
    def create_from_patch(cls, noise, parent,
                          x, y, scale, lod, density,
                          coord=TexCoord.Cylindrical, face=-1):
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
            half_size = size / 2.0
            x0 = (x - half_size) * scale
            y0 = (y - half_size) * scale
            x1 = (x + half_size) * scale
            y1 = (y + half_size) * scale
        patch = cls(noise, parent,
                    x0, y0, x1, y1,
                    width=density, height=density,
                    scale=scale,
                    coord=coord, face=face, border=1)
        patch.patch_lod = lod
        patch.lod = lod
        patch.lod_scale_x = scale / s_div
        patch.lod_scale_y = scale / r_div
        patch.density = density
        patch.x = x
        patch.y = y
        return patch

    def is_ready(self):
        return self.heightmap_ready

    def set_height(self, x, y, height):
        pass

    def get_height(self, x, y):
        return None

    def get_average_height_uv(self, u, v):
        x = u * (self.width - 1)
        y = v * (self.height - 1)
        x0 = int(floor(x))
        y0 = int(floor(y))
        x1 = int(ceil(x))
        y1 = int(ceil(y))
        dx = x - x0
        dy = y - y0
        h_00 = self.get_height(x0, y0)
        h_01 = self.get_height(x0, y1)
        h_10 = self.get_height(x1, y0)
        h_11 = self.get_height(x1, y1)
        return h_00 + (h_10 - h_00) * dx + (h_01 - h_00) * dy + (h_00 + h_11 - h_01 - h_10) * dx * dy

    def get_height_uv(self, u, v):
        return self.get_height(int(u * (self.width - 1)), int(v * (self.height - 1)))

    def generate(self):
        pass

    def copy_from(self, heightmap_patch):
        pass

class HeightmapPatchFactory(object):
    def create_patch(self, *args, **kwargs):
        return None

class Heightmap(object):
    tex_generators = {}

    def __init__(self, name, width, height, height_scale, u_scale, v_scale, median):
        self.name = name
        self.width = width
        self.height = height
        self.height_scale = height_scale
        self.u_scale = float(u_scale) / width
        self.v_scale = float(v_scale) / height
        self.median = median
        if median:
            self.offset = -0.5 * self.height_scale
        else:
            self.offset = 0.0
        self.global_frequency = 1.0
        self.global_scale = 1.0 / self.height_scale
        self.heightmap_ready = False

    def set_height_scale(self, height_scale):
        self.height_scale = height_scale
        if self.median:
            self.offset = -0.5 * self.height_scale
        else:
            self.offset = 0.0

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

    def get_average_height_uv(self, u, v):
        x = u * (self.width - 1)
        y = v * (self.height - 1)
        x0 = int(floor(x))
        y0 = int(floor(y))
        x1 = int(ceil(x))
        y1 = int(ceil(y))
        dx = x - x0
        dy = y - y0
        h_00 = self.get_height(x0, y0)
        h_01 = self.get_height(x0, y1)
        h_10 = self.get_height(x1, y0)
        h_11 = self.get_height(x1, y1)
        return h_00 + (h_10 - h_00) * dx + (h_01 - h_00) * dy + (h_00 + h_11 - h_01 - h_10) * dx * dy

    def get_height_uv(self, u, v):
        return self.get_height(int(u * (self.width - 1)), int(v * (self.height - 1)))

    def get_heightmap(self):
        return None

    def create_heightmap(self, patch, callback=None, cb_args=()):
        return None

class PatchedHeightmap(Heightmap):
    def __init__(self, name, size, height_scale, u_scale, v_scale, median, patch_factory, max_lod=100):
        Heightmap.__init__(self, name, size, size, height_scale, u_scale, v_scale, median)
        self.size = size
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
                                                       coord=patch.coord, face=face)
            self.map_patch[patch.str_id()] = heightmap
            #TODO: Should be linked properly
            heightmap.patch = patch
            if patch.lod > self.max_lod and patch.parent is not None:
                #print("CLONE", patch.str_id())
                parent_heightmap = self.map_patch[patch.parent.str_id()]
                heightmap.copy_from(parent_heightmap)
                delta = patch.lod - heightmap.lod
                scale = 1 << delta
                x_tex = int(x / scale) * scale
                y_tex = int(y / scale) * scale
                x_delta = float(x - x_tex) / scale
                y_delta = float(y - y_tex) / scale
                #Y orientation is the opposite of the texture v axis
                y_delta = 1.0 - y_delta - 1.0 / scale
                if y_delta == 1.0: y_delta = 0.0
                heightmap.texture_offset = LVector2(x_delta, y_delta)
                heightmap.texture_scale = LVector2(1.0 / scale, 1.0 / scale)
                #print(patch.str_id(), ':', parent_heightmap.lod, heightmap.texture_offset, heightmap.texture_scale)
                if callback is not None:
                    callback(heightmap, *cb_args)
            else:
                #print("GEN", patch.str_id())
                heightmap.generate(callback, cb_args)
        else:
            #print("CACHE", patch.str_id())
            heightmap = self.map_patch[patch.str_id()]
            if heightmap.is_ready() and callback is not None:
                callback(heightmap, *cb_args)
            else:
                pass#print("PATCH NOT READY?", heightmap.heightmap_ready, callback)

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

    def generate(self, callback):
        if self.count != None: return
        self.count = 0
        self.callback = callback
        for patch in self.patches:
            patch.generate(self.sub_callback)

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
