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

from panda3d.core import LPoint3d, LVector3, LVector3d, LVector4, LMatrix4
from panda3d.core import NodePath

from .patchedshapes import CullingFrustum, QuadTreeNode, PatchBase, PatchedShapeBase, BoundingBoxShape, PatchLayer
from .textures import TexCoord
from . import geometry
from . import settings


class Tile(PatchBase):
    coord = TexCoord.Flat

    def __init__(self, parent, lod, x, y, density, surface_scale, min_height, max_height):
        PatchBase.__init__(self, parent, lod, density, surface_scale)
        self.x = x
        self.y = y
        self.face = -1
        self.size = 1.0 / (1 << lod)
        self.half_size = self.size / 2.0

        self.x0 = x
        self.y0 = y
        self.x1 = x + self.size
        self.y1 = y + self.size
        self.flat_coord = LVector4(self.x0 * surface_scale,
                                    self.y1 * surface_scale,
                                    (self.x1 - self.x0) * surface_scale,
                                    (self.y0 - self.y1) * surface_scale)
        self.create_quadtree_node(min_height, max_height)
        self.bounds_shape = BoundingBoxShape(self.quadtree_node.bounds)

    def create_quadtree_node(self, min_height, max_height):
        centre = LPoint3d(self.x0 + self.half_size, self.y0 + self.half_size, 0.0)
        normal = LVector3d.up()
        bounds = geometry.PatchAABB(self.x0, self.y0, self.size, 1.0, min_height, max_height)
        self.quadtree_node = QuadTreeNode(self, self.lod, self.density, centre, self.size, normal, 0.0, bounds)

    def str_id(self):
        return "%d - %g %g" % (self.lod, self.x / self.size, self.y / self.size)

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

class GpuPatchTerrainLayer(PatchLayer):
    template = None

    def create_instance(self, patch):
        if self.template is None:
            GpuPatchTerrainLayer.template = geometry.Patch(1.0)
        self.instance = NodePath('tile')
        self.template.instanceTo(self.instance)
        self.instance.reparent_to(patch.instance)
        self.instance.set_pos(patch.x0, patch.y0, 0.0)
        self.instance.set_scale(*patch.get_scale())

class MeshTerrainLayer(PatchLayer):
    template = {}
    def create_instance(self, patch):
        tile_id = str(patch.size) + '-' + str(patch.tessellation_inner_level) + '-' + '-'.join(map(str, patch.tessellation_outer_level))
        #print(tile_id)
        if tile_id not in self.template:
            self.template[tile_id] = geometry.Tile(1.0,
                                                   geometry.TesselationInfo(patch.tessellation_inner_level, patch.tessellation_outer_level),
                                                   use_patch_adaptation=settings.use_patch_adaptation, use_patch_skirts=settings.use_patch_skirts,
                                                   skirt_size=patch.size / 33, skirt_uv=1 / 33)
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
        PatchedShapeBase.__init__(self, factory, None, lod_control)
        self.heightscale = scale

    def create_culling_frustum(self):
        transform_mat = LMatrix4()
        transform_mat.invert_from(self.instance.getNetTransform().getMat())
        self.culling_frustum = CullingFrustum(self.owner, self.owner.context.observer, transform_mat)

    def global_to_shape_coord(self, x, y):
        return (x / self.heightscale, y / self.heightscale)

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
            patch = self.create_patch(None, 0, -1, x, y)
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

    def split_patch(self, parent):
        lod = parent.lod + 1
        delta = parent.half_size
        x = parent.x
        y = parent.y
        self.create_patch(parent, lod, -1, x, y)
        self.create_patch(parent, lod, -1, x + delta, y)
        self.create_patch(parent, lod, -1, x + delta, y + delta)
        self.create_patch(parent, lod, -1, x, y + delta)

    def merge_patch(self, patch):
        pass

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
        model_camera_pos = camera_pos / self.heightscale
        (x, y) = model_camera_pos[0], model_camera_pos[1]
        return (model_camera_pos, None, (x, y))

    def get_scale(self):
        return LVector3(self.heightscale, self.heightscale, self.heightscale)
