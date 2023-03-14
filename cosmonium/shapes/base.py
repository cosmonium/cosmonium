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


from panda3d.core import GeomNode
from panda3d.core import LVecBase3, LVector3
from panda3d.core import BitMask32
from panda3d.core import CollisionSphere, CollisionNode

from .. import settings

#TODO: Should inherit from VisibleObject !
class Shape:
    patchable = False
    use_collision_solid = False
    deferred_instance = False

    def __init__(self):
        self.instance = None
        self.collision_solid = None
        self.scale = LVector3(1.0, 1.0, 1.0)
        self.radius = 1.0
        self.owner = None
        self.instance_ready = False
        self.task = None
        self.clickable = False
        self.attribution = None
        #TODO: Used to fix ring textures
        self.vanish_borders = False

    def get_name(self):
        return 'shape ' + self.owner.get_name()

    def get_user_parameters(self):
        return None

    def check_settings(self):
        pass

    def get_data_source(self):
        return None

    def task_done(self, task):
        self.task = None

    def shape_done(self):
        pass

    def is_spherical(self):
        return True

    def update_shape(self):
        pass

    async def create_instance(self):
        return None

    def update_instance(self, scene_manager, camera_pos, camera_rot):
        pass

    def remove_instance(self):
        if self.instance is not None:
            self.instance.detach_node()
            self.instance = None
        self.instance_ready = False
        if self.task is not None:
            #print("KILL TASK", self.str_id())
            self.task.cancel()
            self.task = None

    def create_collision_solid(self, radius=1.0):
        cs = CollisionSphere(0, 0, 0, radius)
        self.collision_solid = self.instance.attachNewNode(CollisionNode('cnode'))
        self.collision_solid.node().addSolid(cs)
        #self.collision_solid.show()

    def show(self):
        if self.instance:
            self.instance.show()

    def hide(self):
        if self.instance:
            self.instance.hide()

    def str_id(self):
        return 'shape'

    def set_owner(self, owner):
        self.owner = owner
        self.apply_owner()

    def apply_owner(self):
        if self.instance is not None:
            if self.use_collision_solid and self.collision_solid is not None:
                self.collision_solid.setPythonTag('owner', self.owner)
            self.instance.setPythonTag('owner', self.owner)

    def update_lod(self, camera_pos, distance_to_obs, pixel_size, appearance):
        return [], []

    def set_texture_to_lod(self, texture, texture_stage, texture_lod, patched):
        pass

    def set_scale(self, scale):
        self.radius = max(scale)
        self.scale = scale

    def set_radius(self, radius):
        self.radius = radius
        self.scale = LVector3(radius, radius, radius)

    def get_scale(self):
        return self.scale

    def global_to_shape_coord(self, x, y):
        return (x, y)

    def coord_to_uv(self, coord):
        return coord

    def find_patch_at(self, coord):
        return self

    def set_clickable(self, clickable):
        self.clickable = clickable
        if self.use_collision_solid and self.collision_solid is not None:
            if clickable:
                self.collision_solid.node().setIntoCollideMask(CollisionNode.getDefaultCollideMask())
            else:
                self.collision_solid.node().setIntoCollideMask(BitMask32.all_off())
            #The instance itself is not clickable
            self.instance.setCollideMask(BitMask32.all_off())
        else:
            if clickable:
                self.instance.setCollideMask(GeomNode.getDefaultCollideMask())
            else:
                self.instance.setCollideMask(BitMask32.all_off())


class InstanceShape(Shape):
    deferred_instance = True
    def __init__(self, instance):
        Shape.__init__(self)
        self.instance = instance
        bounds = self.instance.getTightBounds()
        if bounds is not None:
            (l, r) = bounds
            self.radius = max(r - l) / 2
        else:
            self.radius = 0

    async def create_instance(self):
        self.apply_owner()
        self.parent.apply_instance(self.instance)
        self.instance_ready = True
        return self.instance

    def get_apparent_radius(self):
        return self.radius

    def get_scale(self):
        return LVecBase3(1.0, 1.0, 1.0)
