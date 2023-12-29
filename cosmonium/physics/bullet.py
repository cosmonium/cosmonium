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


from panda3d.bullet import BulletWorld, BulletDebugNode, BulletRigidBodyNode,\
    BulletTriangleMesh, BulletTriangleMeshShape, BulletCapsuleShape, ZUp,\
    BulletCharacterControllerNode
from panda3d.core import LQuaterniond, LVector3d, NodePath, LVector3, BitMask32

from .base import PhysicsBase


class BulletPhysics(PhysicsBase):

    collision = True
    physics = True
    support_heightmap = True

    def __init__(self, enable_debug):
        self.enable_debug = enable_debug
        self.physics_world = None
        self.render_world = None
        self.debug = None
        self.gravity = 9.81

    def enable(self):
        self.physics_world = BulletWorld()
        self.render_world = NodePath('physics-root')
        if self.enable_debug:
            self.debug = render.attach_new_node(BulletDebugNode('Debug'))
            self.debug.show()
            #self.debug.node().showNormals(True)
            self.physics_world.set_debug_node(self.debug.node())

    def set_gravity(self, gravity):
        self.gravity = self.gravity
        self.physics_world.set_gravity(*LVector3d(0, 0, -gravity))

    def disable(self):
        self.physics_world = None
        self.render_world.remove_node()
        self.render_world = None
        if self.debug is not None:
            self.debug.remove_node()
            self.debug = None

    def add_object(self, entity, physics_instance):
        physics_instance.set_collide_mask(BitMask32.all_on())
        self.physics_world.attach_rigid_body(physics_instance.node())
        physics_instance.reparent_to(self.render_world)

    def add_objects(self, entity, physics_instances):
        for physics_instance in physics_instances:
            physics_instance.set_collide_mask(BitMask32.all_on())
            self.physics_world.attach_rigid_body(physics_instance.node())
            physics_instance.reparent_to(self.render_world)

    def add_controller(self, entity, instance, physics_node):
        physics_instance = NodePath(physics_node)
        #physics_instance.set_z(1)
        physics_node.set_gravity(self.gravity)
        self.physics_world.attach_character(physics_node)
        physics_instance.reparent_to(self.render_world)
        physics_instance.set_collide_mask(BitMask32.all_on())
        physics_instance.set_transform(instance.get_transform())
        physics_instance.set_pos(entity.anchor.get_local_position())
        return physics_instance

    def remove_object(self, entity, physics_instance):
        self.physics_world.remove_rigid_body(physics_instance.node())

    def remove_controller(self, entity, physics_instance):
        self.physics_world.remove_character(physics_instance.node())

    def update(self, time, dt):
        if self.physics_world is None:
            return
        self.physics_world.do_physics(dt)

    def ls(self):
        self.render_world.ls()

    def create_capsule_shape_for(self, model):
        bounds = model.get_tight_bounds()
        dims = bounds[1] - bounds[0]
        width = max(dims[0], dims[1]) / 2.0
        height = dims[2]
        physics_shape = BulletCapsuleShape(width, height - 2 * width, ZUp)
        return physics_shape

    def create_controller_for(self, physics_shape):
        return BulletCharacterControllerNode(physics_shape, 0.1, 'Player')

    def build_from_geom(self, model, dynamic=True, compress=False):
        physics_nodepaths = []
        for nodepath in model.findAllMatches('**/+GeomNode'):
            node = BulletRigidBodyNode(nodepath.name)
            mesh = BulletTriangleMesh()
            mesh.addGeom(nodepath.node().get_geom(0))
            shape = BulletTriangleMeshShape(mesh, dynamic=dynamic, compress=compress)
            node.add_shape(shape)
            physics_nodepath = NodePath(node)
            physics_nodepath.set_transform(nodepath.get_transform(model))
            physics_nodepaths.append(physics_nodepath)
        return physics_nodepaths

    def set_mass(self, physics_instance, mass):
        physics_instance.node().set_mass(mass)


class KineticMover:

    kinetic_mover = True
    position_mover = False

    def __init__(self, entity):
        self.entity = entity

    def activate(self):
        pass

    def set_state(self, state):
        self.entity.set_state(state)

    def update(self):
        pass


class BulletMover(KineticMover):

    def feedback(self):
        if self.entity.physics_node is not None:
            bounds = self.entity.ship_object.instance.get_tight_bounds()
            dims = bounds[1] - bounds[0]
            # width = max(dims[0], dims[1]) / 2.0
            height = dims[2]
            offset = LVector3(0, 0, -height / 2)
            self.entity.anchor.set_frame_position(self.entity.physics_instance.get_pos() + offset)

    def set_local_position(self, position):
        if self.entity.physics_node is not None:
            self.entity.physics_node.set_pos(position)
        else:
            self.entity.anchor.set_frame_position(position)

    def set_speed_relative(self, speed):
        if self.entity.physics_node is not None:
            rotation = self.entity.anchor.get_frame_orientation()
            self.entity.physics_node.set_linear_movement(rotation.xform(speed), True)

    def turn_relative(self, step):
        rotation = self.entity.anchor.get_frame_orientation()
        delta = LQuaterniond()
        delta.set_from_axis_angle_rad(step, LVector3d.up())
        new_rotation = delta * rotation
        self.entity.anchor.set_frame_orientation(new_rotation)
