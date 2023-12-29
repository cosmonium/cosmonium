#
#This file is part of Cosmonium.
#
#Copyright (C) 2018-2023 Laurent Deru.
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


from dataclasses import dataclass
from direct.showbase.ShowBaseGlobal import globalClock
from direct.task.TaskManagerGlobal import taskMgr
import math
from panda3d.core import CollisionTraverser, CollisionHandlerPusher, CollisionHandlerQueue
from panda3d.core import CollisionNode, CollisionCapsule, CollisionRay
from panda3d.core import BitMask32, LPoint3
from typing import Any

from .base import PhysicsBase, PhysicsController


@dataclass
class PhysicNode:
    controller: Any = None
    entity: Any = None
    instance: Any = None
    handler: Any = None


class CollisionPhysics(PhysicsBase):

    collision = True
    physics = False
    support_heightmap = False

    collision_bit = 1

    def __init__(self):
        self.traverser = CollisionTraverser()
        self.pusher = CollisionHandlerPusher()
        self.queue = CollisionHandlerQueue()
        self.gravity = 9.81
        self.nodes = []
        self.task = taskMgr.add(self.height_task, 'height')
        self.fall = 1

    def height_task(self, task):
        for node in self.nodes:
            highest_z = -math.inf
            for i in range(node.handler.get_num_entries()):
                entry = node.handler.get_entry(i)
                z = entry.get_surface_point(node.entity.scene_anchor.instance).get_z()
                if z > highest_z:
                    highest_z = z
            if highest_z != -math.inf:
                node.instance.set_z(node.instance.get_z() + self.fall * globalClock.getDt())
                self.fall -= 9.81 * globalClock.getDt()
                if highest_z > node.instance.get_z():
                    self.fall = 0
                    if False and self.player.jump:
                        self.fall = 4
                    node.instance.set_z(highest_z)
        return task.cont

    def enable(self):
        pass

    def set_gravity(self, gravity):
        self.gravity = gravity

    def disable(self):
        pass

    def add_object(self, entity, physics_instance):
        physics_instance.set_collide_mask(BitMask32.bit(self.collision_bit))

    def add_objects(self, entity, physics_instances):
        for physics_instance in physics_instances:
            physics_instance.set_collide_mask(BitMask32.bit(self.collision_bit))

    def add_controller(self, entity, instance, physics_node):
        node = PhysicNode(entity=entity, instance=instance)
        physics_node.set_from_collide_mask(BitMask32.bit(self.collision_bit))
        self.nodes.append(node)
        solid = instance.attach_new_node(physics_node)

        self.traverser.add_collider(solid, self.pusher)
        self.pusher.add_collider(solid, instance)
        #self.traverser.add_collider(solid, self.queue)

        ray = CollisionRay()
        #ray.set_origin(0, 0, entity.height / 2)
        ray.set_origin(0, 0, 1)
        ray.set_direction(0, 0, -1)
        ray_node = CollisionNode('playerRay')
        ray_node.add_solid(ray)
        ray_node.set_from_collide_mask(BitMask32.bit(self.collision_bit))
        ray_node.set_into_collide_mask(BitMask32.all_off())
        solid = instance.attach_new_node(ray_node)
        node.handler = CollisionHandlerQueue()
        self.traverser.add_collider(solid, node.handler)

        instance.setCollideMask(BitMask32.all_off())
        entity.set_controller(ReactBodyController(entity.anchor, entity.scene_anchor, entity.mover))
        # self.traverser.show_collisions(render)
        return instance

    def remove_object(self, entity, physics_instance):
        pass

    def remove_controller(self, entity, physics_instance):
        pass

    def update(self, time, dt):
        self.traverser.traverse(render)
        for entry in self.queue.entries:
            print(entry)

    def ls(self):
        pass

    def create_capsule_shape_for(self, model):
        bounds = model.get_tight_bounds()
        dims = bounds[1] - bounds[0]
        width = max(dims[0], dims[1]) / 2.0
        height = dims[2]
        physics_shape = CollisionCapsule(0, 0, height * 0.1, 0, 0, height, width)
        return physics_shape

    def create_controller_for(self, physics_shape):
        physics_node = CollisionNode('cn')
        physics_node.add_solid(physics_shape)
        return physics_node

    def build_from_geom(self, instance, dynamic=True, compress=False):
        return [instance]

    def set_mass(self, physics_instance, mass):
        pass


class ReactBodyController(PhysicsController):
    def __init__(self, anchor, scene_anchor, mover):
        PhysicsController.__init__(self, anchor)
        self.scene_anchor = scene_anchor
        self.mover = mover

    def create_mover(self):
        pass

    def update(self, time, dt):
        if self.anchor.body.ship_object.instance is not None:
            scene_position = self.anchor.body.ship_object.instance.get_pos()
            self.anchor.body.ship_object.instance.set_pos(LPoint3())
            position = self.anchor.get_local_position() + scene_position
            self.mover.set_local_position(position)
            self.mover.update()
