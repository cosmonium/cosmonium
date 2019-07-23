from __future__ import print_function
from __future__ import absolute_import

from panda3d.core import OmniBoundingVolume
from panda3d.core import LPoint3d, LVector3, LVector4
from panda3d.core import NodePath

from .patchedshapes import PatchBase, PatchedShapeBase
from .textures import TexCoord
from . import geometry

from math import sqrt

class Tile(PatchBase):
    coord = TexCoord.Flat

    def __init__(self, parent, lod, x, y, density, scale):
        PatchBase.__init__(self, parent, lod, density)
        self.x = x
        self.y = y
        self.scale = scale
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
        self.layers = []

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
            self.distance = sqrt(104)
        else:
            self.distance = (self.centre - model_camera_pos).length()
            dx = max(self.x0 - model_camera_pos[0], 0, model_camera_pos[0] - self.x1)
            dy = max(self.y0 - model_camera_pos[1], 0, model_camera_pos[1] - self.y1)
            self.distance = sqrt(dx*dx + dy*dy) * self.scale + sqrt(104)
        self.visible = True
        self.patch_in_view = True
        self.in_cone = True
        self.apparent_size = self.get_patch_length() / (self.distance * pixel_size)

    def create_instance(self):
        self.instance = NodePath('tile')
        self.instance.set_pos(*self.centre)
        self.instance.set_scale(*self.get_scale())
        self.apply_owner()
        for layer in self.layers:
            layer.create_instance(self)
        return self.instance

    def update_instance(self):
        if self.instance is None: return
        #print("Update", self.str_id())
        for layer in self.layers:
            layer.update_instance(self)

    def remove_instance(self):
        if self.instance:
            self.instance.removeNode()
            self.instance = None
            self.instance_ready = False
        for layer in self.layers:
            layer.remove_instance()

    def coord_to_uv(self, coord):
        (x, y) = coord
        return (x - self.x0) / self.size, 1 - (y - self.y0) / self.size

    def get_xy_for(self, u, v):
        return u * self.size + self.x0, (1 - v) * self.size + self.y0

    def get_scale(self):
        return LVector3(self.size, self.size, 1.0)

class GpuPatchTerrainLayer(object):
    template = None
    def check_settings(self):
        pass

    def create_instance(self, patch):
        if self.template is None:
            GpuPatchTerrainLayer.template = geometry.Patch(0.5)
        self.instance = NodePath('tile')
        bounds = OmniBoundingVolume()
        self.instance.node().setBounds(bounds)
        self.instance.node().setFinal(1)
        self.template.instanceTo(self.instance)
        self.instance.reparent_to(patch.instance)

    def update_instance(self, patch):
        pass

    def remove_instance(self):
        if self.instance is not None:
            self.instance.removeNode()
            self.instance = None

class MeshTerrainLayer(object):
    template = None
    def __init__(self):
        self.density = 16

    def check_settings(self):
        pass

    def create_instance(self, patch):
        if self.template is None:
            MeshTerrainLayer.template = geometry.Tile(size=0.5, split=self.density + 1)
        self.instance = NodePath('tile')
        self.template.instanceTo(self.instance)
        self.instance.reparent_to(patch.instance)

    def update_instance(self, patch):
        pass

    def remove_instance(self):
        if self.instance is not None:
            self.instance.removeNode()
            self.instance = None

class TiledShape(PatchedShapeBase):
    def __init__(self, factory, scale, lod_control):
        PatchedShapeBase.__init__(self, lod_control)
        self.factory = factory
        self.scale = scale
        self.populator = None

    def set_populator(self, populator):
        self.populator = populator

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
        return patch

    def split_patch(self, patch):
        lod = patch.lod + 1
        delta = patch.half_size / 2.0
        x = patch.x
        y = patch.y
        self.factory.create_patch(patch, lod, x - delta, y - delta)
        self.factory.create_patch(patch, lod, x + delta, y - delta)
        self.factory.create_patch(patch, lod, x + delta, y + delta)
        self.factory.create_patch(patch, lod, x - delta, y + delta)

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

    def create_patch_instance_delayed(self, patch):
        PatchedShapeBase.create_patch_instance_delayed(self, patch)
        if self.populator is not None and (self.populator.lod_aware or patch.lod == 0):
            self.populator.create_instance_patch(patch)

    def remove_patch_instance(self, patch, split=False):
        if patch.instance is not None:
            if self.populator is not None and (self.populator.lod_aware or (not split and patch.lod == 0)):
                self.populator.remove_instance_patch(patch)
        PatchedShapeBase.remove_patch_instance(self, patch)

    def xform_cam_to_model(self, camera_pos):
        model_camera_pos = camera_pos / self.scale
        (x, y) = model_camera_pos[0], model_camera_pos[1]
        return (model_camera_pos, None, (x, y))

    def are_children_visibles(self, patch):
        return True

    def get_scale(self):
        return LVector3(self.scale, self.scale, 1.0)
