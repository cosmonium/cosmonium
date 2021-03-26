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

from panda3d.core import OmniBoundingVolume, BoundingBox
from panda3d.core import LPoint3d, LVector3, LVector3d, LVector4
from panda3d.core import NodePath

from .patchedshapes import PatchBase, PatchedShapeBase, BoundingBoxShape
from .textures import TexCoord
from . import geometry
from . import settings

from math import sqrt

class Tile(PatchBase):
    coord = TexCoord.Flat

    def __init__(self, parent, lod, x, y, density, scale, min_height, max_height):
        PatchBase.__init__(self, parent, lod, density)
        self.x = x
        self.y = y
        self.face = -1
        self.scale = scale
        self.size = 1.0 / (1 << lod)
        self.half_size = self.size / 2.0

        self.x0 = x
        self.y0 = y
        self.x1 = x + self.size
        self.y1 = y + self.size
        self.centre = LPoint3d(x + self.half_size, y + self.half_size, 0.0)
        self.flat_coord = LVector4(self.x0 * scale,
                                    self.y1 * scale,
                                    (self.x1 - self.x0) * scale,
                                    (self.y0 - self.y1) * scale)
        self.bounds = geometry.PatchAABB(self.x0, self.y0, 1.0, min_height, max_height)
        self.layers = []
        self.bounds_shape = BoundingBoxShape(self.bounds)

    def str_id(self):
        return "%d - %g %g" % (self.lod, self.x / self.size, self.y / self.size)

    def add_layer(self, layer):
        self.layers.append(layer)

    def check_settings(self):
        PatchBase.check_settings(self)
        for layer in self.layers:
            layer.check_settings()
        for child in self.children:
            child.check_settings()

    def get_patch_length(self):
        return self.scale * self.size

    def check_visibility(self, worker, local, model_camera_pos, model_camera_vector, altitude, pixel_size):
        if self.in_patch(*local):
            self.distance = altitude
            within_patch = True
        else:
            dx = max(self.x0 - model_camera_pos[0], 0, model_camera_pos[0] - self.x1) * self.scale
            dy = max(self.y0 - model_camera_pos[1], 0, model_camera_pos[1] - self.y1) * self.scale
            self.distance = sqrt(dx*dx + dy*dy + altitude * altitude)
            within_patch = False
        self.patch_in_view = worker.is_patch_in_view(self)
        self.visible = within_patch or self.patch_in_view
        #print(self.str_id(), within_patch, self.patch_in_view, altitude, self.distance)
        self.apparent_size = self.get_patch_length() / (self.distance * pixel_size)

    def create_geometry_instance(self):
        for layer in self.layers:
            layer.create_instance(self)

    def patch_done(self):
        PatchBase.patch_done(self)
        for layer in self.layers:
            layer.patch_done(self)

    def update_instance(self, parent):
        PatchBase.update_instance(self, parent)
        if self.instance is None: return
        #print("Update", self.str_id())
        for layer in self.layers:
            layer.update_instance(self)

    def remove_geometry_instance(self):
        for layer in self.layers:
            layer.remove_instance()

    def coord_to_uv(self, coord):
        (x, y) = coord
        return (x - self.x0) / self.size, (y - self.y0) / self.size

    def get_xy_for(self, u, v):
        return u * self.size + self.x0, v * self.size + self.y0

    def get_scale(self):
        return LVector3(self.size, self.size, 1.0)

    def get_normals_at(self, coord):
        vectors = (LVector3d.up(), LVector3d.forward(), LVector3d.left())
        return vectors

    def get_lonlatvert_at(self, coord):
        vectors = (LVector3d.right(), LVector3d.forward(), LVector3d.up())
        return vectors

class TerrainLayer(object):
    def __init__(self):
        self.instance = None

    def check_settings(self):
        pass

    def create_instance(self, patch):
        pass

    def patch_done(self, patch):
        pass

    def update_instance(self, patch):
        pass

    def remove_instance(self):
        if self.instance is not None:
            self.instance.removeNode()
            self.instance = None

class GpuPatchTerrainLayer(TerrainLayer):
    template = None

    def create_instance(self, patch):
        if self.template is None:
            GpuPatchTerrainLayer.template = geometry.Patch(1.0)
        self.instance = NodePath('tile')
        self.template.instanceTo(self.instance)
        self.instance.reparent_to(patch.instance)
        self.instance.set_pos(patch.x0, patch.y0, 0.0)
        self.instance.set_scale(*patch.get_scale())

class MeshTerrainLayer(TerrainLayer):
    template = {}
    def create_instance(self, patch):
        tile_id = str(patch.tessellation_inner_level) + '-' + '-'.join(map(str, patch.tessellation_outer_level))
        #print(tile_id)
        if tile_id not in self.template:
            self.template[tile_id] = geometry.Tile(size=1.0, inner=patch.tessellation_inner_level, outer=patch.tessellation_outer_level)
        template = self.template[tile_id]
        self.instance = NodePath('tile')
        template.instanceTo(self.instance)
        self.instance.reparent_to(patch.instance)
        self.instance.set_pos(patch.x0, patch.y0, 0.0)
        self.instance.set_scale(*patch.get_scale())

    def update_instance(self, patch):
        self.remove_instance()
        self.create_instance(patch)

class TiledShape(PatchedShapeBase):
    def __init__(self, factory, scale, lod_control):
        PatchedShapeBase.__init__(self, None, lod_control)
        self.factory = factory
        self.scale = scale

    def global_to_shape_coord(self, x, y):
        return (x / self.scale, y / self.scale)

    def find_patch_at(self, coord):
        (x, y) = coord
        for patch in self.root_patches:
            result = self._find_patch_at(patch, x, y)
            if result is not None:
                return result
        return None

    def find_root_patch(self, x, y):
        for patch in self.root_patches:
            if patch.x == x and patch.y == y:
                return patch
        return None

    def add_root_patch(self, x, y):
        patch = self.find_root_patch(x, y)
        if patch is None:
            patch = self.factory.create_patch(None, 0, x, y)
            patch.owner = self
            self.root_patches.append(patch)
            for linked_object in self.linked_objects:
                linked_object.create_root_patch(patch)
                north = self.find_root_patch(patch.x, patch.y + 1)
                if north is not None:
                    neighbours = north.collect_side_neighbours(PatchBase.SOUTH)
                    for neighbour in neighbours:
                        patch.add_neighbour(PatchBase.NORTH, neighbour)
                        neighbour.add_neighbour(PatchBase.SOUTH, patch)
                east = self.find_root_patch(patch.x + 1, patch.y)
                if east is not None:
                    neighbours = east.collect_side_neighbours(PatchBase.WEST)
                    for neighbour in neighbours:
                        patch.add_neighbour(PatchBase.EAST, neighbour)
                        neighbour.add_neighbour(PatchBase.WEST, patch)
                south = self.find_root_patch(patch.x, patch.y - 1)
                if south is not None:
                    neighbours = south.collect_side_neighbours(PatchBase.NORTH)
                    for neighbour in neighbours:
                        patch.add_neighbour(PatchBase.SOUTH, neighbour)
                        neighbour.add_neighbour(PatchBase.NORTH, patch)
                west = self.find_root_patch(patch.x - 1, patch.y)
                if west is not None:
                    neighbours = west.collect_side_neighbours(PatchBase.EAST)
                    for neighbour in neighbours:
                        patch.add_neighbour(PatchBase.WEST, neighbour)
                        neighbour.add_neighbour(PatchBase.EAST, patch)
        return patch

    def split_patch(self, patch):
        self.factory.split_patch(patch)

    def merge_patch(self, patch):
        self.factory.merge_patch(patch)

    def add_root_patches(self, patch, update):
        #print("Create root patches", patch.centre, self.scale)
        self.add_root_patch(patch.x - 1, patch.y - 1)
        self.add_root_patch(patch.x, patch.y - 1)
        self.add_root_patch(patch.x + 1, patch.y - 1)
        self.add_root_patch(patch.x - 1, patch.y)
        self.add_root_patch(patch.x + 1, patch.y)
        self.add_root_patch(patch.x - 1, patch.y + 1)
        self.add_root_patch(patch.x, patch.y + 1)
        self.add_root_patch(patch.x + 1, patch.y + 1)
        patch.calc_outer_tessellation_level(update)

    def xform_cam_to_model(self, camera_pos):
        model_camera_pos = camera_pos / self.scale
        (x, y) = model_camera_pos[0], model_camera_pos[1]
        return (model_camera_pos, None, (x, y))

    def is_bb_in_view(self, bb, patch_normal, patch_offset):
        lens_bounds = self.lens_bounds.make_copy()
        lens_bounds.xform(render.get_mat(self.instance))
        intersect = lens_bounds.contains(bb)
        return (intersect & BoundingBox.IF_some) != 0

    def is_patch_in_view(self, patch):
        return self.is_bb_in_view(patch.bounds, None, None)

    def get_scale(self):
        return LVector3(self.scale, self.scale, 1.0)
