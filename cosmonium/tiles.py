from __future__ import print_function
from __future__ import absolute_import

from panda3d.core import OmniBoundingVolume, BoundingBox
from panda3d.core import LPoint3d, LVector3, LVector4
from panda3d.core import NodePath

from .patchedshapes import PatchBase, PatchedShapeBase
from .textures import TexCoord
from . import geometry
from . import settings

from math import sqrt

class Tile(PatchBase):
    coord = TexCoord.Flat

    def __init__(self, parent, lod, x, y, density, scale, height_scale):
        PatchBase.__init__(self, parent, lod, density)
        self.x = x
        self.y = y
        self.scale = scale
        self.height_scale = height_scale
        self.size = 1.0 / (1 << lod)
        self.half_size = self.size / 2.0

        self.x0 = x - self.half_size
        self.y0 = y - self.half_size
        self.x1 = x + self.half_size
        self.y1 = y + self.half_size
        self.centre = LPoint3d(x, y, 0.0)
        self.flat_coord = LVector4(self.x0 * scale,
                                    self.y0 * scale,
                                    (self.x1 - self.x0) * scale,
                                    (self.y1 - self.y0) * scale)
        self.local_bounds = geometry.PatchAABB(0.5, self.height_scale)
        self.layers = []
        self.create_holder_instance()
        self.bounds = self.local_bounds.make_copy()
        self.bounds.xform(self.holder.getNetTransform().getMat())

    def str_id(self):
        if self.x != 0:
            x = 1.0 / self.x
        else:
            x = 0
        if self.y != 0:
            y = 1.0 / self.y
        else:
            y = 0
        return "%d - %g %g" % (self.lod, x, y)

    def add_layer(self, layer):
        self.layers.append(layer)

    def check_settings(self):
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
        self.in_cone = True
        self.visible = within_patch or (self.patch_in_view and self.in_cone)
        #print(self.str_id(), within_patch, self.patch_in_view, altitude, self.distance)
        self.apparent_size = self.get_patch_length() / (self.distance * pixel_size)

    def create_holder_instance(self):
        self.holder = NodePath('tile')
        self.holder.set_pos(*self.centre)
        self.holder.set_scale(*self.get_scale())
        if settings.debug_lod_bb:
            self.holder.node().setBounds(self.local_bounds)
        else:
            self.holder.node().setBounds(OmniBoundingVolume())
        self.holder.node().setFinal(1)

    def create_instance(self):
        self.instance = self.holder
        self.apply_owner()
        for layer in self.layers:
            layer.create_instance(self)
        return self.instance

    def update_instance(self, shape):
        if self.instance is None: return
        #print("Update", self.str_id())
        for layer in self.layers:
            layer.update_instance(self)

    def remove_holder_instance(self):
        if self.holder is not None:
            self.holder.removeNode()
            self.holder = None

    def remove_instance(self):
        for layer in self.layers:
            layer.remove_instance()
        self.instance = None
        self.instance_ready = False

    def coord_to_uv(self, coord):
        (x, y) = coord
        return (x - self.x0) / self.size, 1 - (y - self.y0) / self.size

    def get_xy_for(self, u, v):
        return u * self.size + self.x0, (1 - v) * self.size + self.y0

    def get_scale(self):
        return LVector3(self.size, self.size, 1.0)

class TerrainLayer(object):
    def __init__(self):
        self.instance = None

    def check_settings(self):
        pass

    def create_instance(self, patch):
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
            GpuPatchTerrainLayer.template = geometry.Patch(0.5)
        self.instance = NodePath('tile')
        self.template.instanceTo(self.instance)
        self.instance.reparent_to(patch.instance)

class MeshTerrainLayer(TerrainLayer):
    template = {}
    def create_instance(self, patch):
        tile_id = str(patch.tesselation_inner_level) + '-' + '-'.join(map(str, patch.tesselation_outer_level))
        #print(tile_id)
        if tile_id not in self.template:
            self.template[tile_id] = geometry.Tile(size=0.5, inner=patch.tesselation_inner_level, outer=patch.tesselation_outer_level)
        template = self.template[tile_id]
        self.instance = NodePath('tile')
        template.instanceTo(self.instance)
        self.instance.reparent_to(patch.instance)

    def update_instance(self, patch):
        self.remove_instance()
        self.create_instance(patch)

class TiledShape(PatchedShapeBase):
    def __init__(self, factory, scale, lod_control):
        PatchedShapeBase.__init__(self, lod_control)
        self.factory = factory
        self.scale = scale

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
            self.root_patches.append(patch)
            for linked_object in self.linked_objects:
                linked_object.create_root_patch(patch)
        return patch

    def split_patch(self, patch):
        self.factory.split_patch(patch)

    def merge_patch(self, patch):
        self.factory.merge_patch(patch)

    def add_root_patches(self, patch, update):
        #print("Create root patches", patch.centre, self.scale)
        self.add_root_patch(patch.x - 1, patch.y - 1)
        if self.find_root_patch(patch.x, patch.y - 1) is None:
            south = self.add_root_patch(patch.x, patch.y - 1)
            patch.set_neighbours(PatchBase.SOUTH, [south])
            south.set_neighbours(PatchBase.NORTH, [patch])
        self.add_root_patch(patch.x + 1, patch.y - 1)
        if self.find_root_patch(patch.x - 1, patch.y) is None:
            west = self.add_root_patch(patch.x - 1, patch.y)
            patch.set_neighbours(PatchBase.WEST, [west])
            west.set_neighbours(PatchBase.EAST, [patch])
        if self.find_root_patch(patch.x + 1, patch.y) is None:
            east = self.add_root_patch(patch.x + 1, patch.y)
            patch.set_neighbours(PatchBase.EAST, [east])
            east.set_neighbours(PatchBase.WEST, [patch])
        self.add_root_patch(patch.x - 1, patch.y + 1)
        if self.find_root_patch(patch.x, patch.y + 1) is None:
            north = self.add_root_patch(patch.x, patch.y + 1)
            patch.set_neighbours(PatchBase.NORTH, [north])
            north.set_neighbours(PatchBase.SOUTH, [patch])
        self.add_root_patch(patch.x + 1, patch.y + 1)
        patch.calc_outer_tesselation_level(update)

    def xform_cam_to_model(self, camera_pos):
        model_camera_pos = camera_pos / self.scale
        (x, y) = model_camera_pos[0], model_camera_pos[1]
        return (model_camera_pos, None, (x, y))

    def is_bb_in_view(self, bb, patch_normal, patch_offset):
        obj_bounds = bb.make_copy()
        obj_bounds.xform(self.instance.getMat(render))
        intersect = self.lens_bounds.contains(obj_bounds)
        return (intersect & BoundingBox.IF_some) != 0

    def is_patch_in_view(self, patch):
        if patch.holder is None: return False
        return self.is_bb_in_view(patch.bounds, None, None)

    def get_scale(self):
        return LVector3(self.scale, self.scale, 1.0)
