#!/usr/bin/env python
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

# This demo is heavily based on the Ralph example of Panda3D
# Author: Ryan Myers
# Models: Jeff Styers, Reagan Heller
#


import sys
import os
# Disable stdout block buffering
sys.stdout.flush()
sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', buffering=1)

# Add lib/ directory to import path to be able to load the c++ libraries
sys.path.insert(1, 'lib')
# Add third-party/ directory to import path to be able to load the external libraries
sys.path.insert(0, 'third-party')
# CEFPanda and glTF modules aree not at top level
sys.path.insert(0, 'third-party/cefpanda')
sys.path.insert(0, 'third-party/gltf')

from panda3d.core import LPoint3d, LVector3d, LQuaterniond, LQuaternion, BitMask32, NodePath
from panda3d.bullet import BulletHeightfieldShape, BulletBoxShape, BulletRigidBodyNode, BulletCapsuleShape, ZUp

from cosmonium.foundation import BaseObject
from cosmonium.scene.flatuniverse import FlatUniverse
from cosmonium.scene.scenemanager import C_CameraHolder, StaticSceneManager, remove_main_region
from cosmonium.scene.sceneanchor import SceneAnchorCollection
from cosmonium.scene.sceneworld import CartesianWorld, SceneWorld
from cosmonium.engine.c_settings import c_settings
from cosmonium.procedural.water import WaterNode
from cosmonium.tiles import TerrainLayerFactoryInterface
from cosmonium.patchedshapes import PatchLayer
from cosmonium.shadows import CustomShadowMapShadowCaster, PSSMShadowMapShadowCaster
from cosmonium.camera import CameraHolder, SurfaceFollowCameraController, FixedCameraController, EventsControllerBase
from cosmonium.nav import ControlNav
from cosmonium.controllers.controllers import CartesianBodyMover, FlatSurfaceBodyMover
from cosmonium.parsers.actorobjectparser import ActorObjectYamlParser
from cosmonium.parsers.flatuniverseparser import FlatUniverseYamlParser
from cosmonium.parsers.yamlparser import YamlModuleParser
from cosmonium.physics import Physics
from cosmonium.ui.splash import NoSplash
from cosmonium.cosmonium import CosmoniumBase
from cosmonium import settings

from cosmonium.astro import units

#TODO: Change of base unit should be done properly
units.m = 1.0
units.Km = 1000.0

from math import pow, pi, sqrt
import argparse


class WaterLayer(PatchLayer):
    def __init__(self, config):
        self.config = config
        self.water = None

    def check_settings(self):
        if self.water is not None:
            if self.config.visible:
                self.water.create_instance()
            else:
                self.water.remove_instance()

    def create_instance(self, patch):
        scale = patch.scale * patch.size / self.config.scale
        self.water = WaterNode(patch.x0, patch.y0, patch.size, scale, patch)
        if self.config.visible:
            self.water.create_instance()

    def patch_done(self, patch, early):
        pass

    def update_instance(self, patch):
        pass

    def remove_instance(self):
        if self.water is not None:
            self.water.remove_instance()
            self.water = None


class WaterLayerFactory(TerrainLayerFactoryInterface):
    def __init__(self, water):
        self.water = water

    def create_layer(self, patch):
        return WaterLayer(self.water)


class PhysicsLayer(PatchLayer):
    def __init__(self, physics):
        self.physics = physics
        self.instance = None

    def patch_done(self, patch, early):
        if early:
            return
        terrain = patch.owner.owner.surface
        heightmap = terrain.heightmap
        heightmap_patch = heightmap.get_patch_data(patch, strict=True)
        terrain_scale = terrain.get_scale()
        patch_scale =  patch.get_scale()
        assert heightmap_patch.width == heightmap_patch.height
        assert patch_scale[0] == patch_scale[1]
        shape = BulletHeightfieldShape(heightmap_patch.texture, heightmap.max_height * terrain_scale[2], ZUp)
        shape.setUseDiamondSubdivision(True)
        self.instance = NodePath(BulletRigidBodyNode('Heightfield ' + patch.str_id()))
        self.instance.node().add_shape(shape)
        x = terrain_scale[0] * (patch.x0 + patch.x1) / 2.0
        y = terrain_scale[1] * (patch.y0 + patch.y1) / 2.0
        self.instance.set_pos(x, y, heightmap.max_height / 2 * terrain_scale[2])
        self.instance.set_scale(terrain_scale[0] * patch_scale[0] / (heightmap_patch.width - 1),
                                terrain_scale[1] * patch_scale[1] / (heightmap_patch.height - 1),
                                1)
        self.instance.setCollideMask(BitMask32.allOn())
        self.physics.add(self.instance)

    def remove_instance(self):
        if self.instance is None: return
        self.physics.remove(self.instance)
        self.instance.remove_node()
        self.instance = None


class PhysicsLayerFactory(TerrainLayerFactoryInterface):
    def __init__(self, physics):
        self.physics = physics

    def create_layer(self, patch):
        return PhysicsLayer(self.physics)


class PhysicsBox():
    def __init__(self, model, physics, mass, limit):
        self.model = model
        self.physics = physics
        self.mass = mass
        self.limit = limit
        self.instance = None
        self.physics_instance = None

    def create_instance(self, observer):
        self.mesh = loader.loadModel(self.model)
        self.mesh.clearModelNodes()
        self.instance = NodePath("BoxHolder")
        self.mesh.reparent_to(self.instance)
        self.instance.reparent_to(render)

        bounds = self.instance.get_tight_bounds()
        half_size = (bounds[1] - bounds[0]) / 2.0
        shape = BulletBoxShape(half_size)

        self.physics_instance = NodePath(BulletRigidBodyNode('Box'))
        self.physics_instance.node().set_mass(self.mass)
        self.physics_instance.node().add_shape(shape)
        self.physics_instance.setCollideMask(BitMask32.allOn())
        #TODO: Replace with calc_absolute_...
        position = observer.get_local_position() + observer.get_absolute_orientation().xform(LPoint3d(0, 15, 5))
        self.physics_instance.set_pos(*position)
        self.physics.add(self.physics_instance)

    def remove_instance(self):
        if self.instance is not None:
            self.instance.remove_node()
            self.instance = None
            self.physics.remove(self.physics_instance)
            self.physics_instance = None

    def update(self, observer):
        if self.instance is None: return False
        local_position = LPoint3d(*self.physics_instance.get_pos())
        local_rotation = LQuaterniond(*self.physics_instance.get_quat())
        if settings.camera_at_origin:
            scene_rel_position = local_position - observer.get_local_position()
        else:
            scene_rel_position = local_position
        self.instance.set_pos(*scene_rel_position)
        self.instance.set_quat(LQuaternion(*local_rotation))
        if (local_position - observer.get_local_position()).length() > self.limit:
            print("Object is too far, removing it")
            self.remove_instance()
            return False
        else:
            return True

class WaterConfig():
    def __init__(self, level, visible, scale):
        self.level = level
        self.visible = visible
        self.scale = scale

class PhysicsConfig():
    def __init__(self, enable, gravity, model, mass, limit, debug):
        self.enable = enable
        self.gravity = gravity
        self.model = model
        self.mass = mass
        self.limit = limit
        self.debug = debug

class RalphConfigParser(YamlModuleParser):
    def __init__(self, worlds):
        YamlModuleParser.__init__(self)
        self.worlds = worlds

    def decode(self, data):
        water = data.get('water', None)
        physics = data.get('physics', {})

        parser = FlatUniverseYamlParser(self.worlds)
        parser.decode(data)
        terrain = data.get('terrain', {})
        self.tile_size = terrain.get("tile-size", 1024)

        self.shadow_size = terrain.get('shadow-size', 16)
        self.shadow_box_length = terrain.get('shadow-depth', self.tile_size)

        if water is not None:
            level = water.get('level', 0)
            visible = water.get('visible', False)
            scale = water.get('scale', 8.0)
            self.water = WaterConfig(level, visible, scale)
        else:
            self.water = WaterConfig(0, False, 1.0)

        has_physics = physics.get('enable', False)
        gravity = physics.get('gravity', 9.81)
        model = physics.get('model', None)
        mass = physics.get('mass', 20)
        limit = physics.get('limit', 100)
        enable_debug = physics.get('debug', False)
        self.physics = PhysicsConfig(has_physics, gravity, model, mass, limit, enable_debug)

        ralph = data.get('ralph', {})
        self.ralph_shape_object = ActorObjectYamlParser.decode(ralph)
        return True

class RalphWord(CartesianWorld):
    def __init__(self, name, ship_object, radius, enable_physics):
        CartesianWorld.__init__(self, name)
        self.add_component(ship_object)
        self.ship_object = ship_object
        self.current_state = None
        self.physics_instance = None
        self.enable_physics = enable_physics
        self.anchor.set_bounding_radius(radius)

    def set_state(self, new_state):
        if self.current_state == new_state: return
        if new_state == 'moving':
            self.ship_object.shape.loop("run")
        if new_state == 'idle':
            self.ship_object.shape.stop()
            self.ship_object.shape.pose("walk", 5)
        self.current_state = new_state

    def check_and_update_instance(self, scene_manager, camera_pos, camera_rot):
        CartesianWorld.check_and_update_instance(self, scene_manager, camera_pos, camera_rot)
        if self.ship_object.instance is not None and self.enable_physics and self.physics_instance is None:
            bounds = self.ship_object.instance.get_tight_bounds()
            dims = bounds[1] - bounds[0]
            width = max(dims[0], dims[1]) / 2.0
            height = dims[2]
            self.physics_instance = NodePath(BulletRigidBodyNode("Ralph"))
            shape = BulletCapsuleShape(width, height - 2 * width, ZUp)
            self.physics_instance.node().addShape(shape)
            self.physics_instance.node().setMass(60.0)
            self.physics_instance.node().setKinematic(True)
            base.physics.add(self.physics_instance)

    def update(self, time, dt):
        CartesianWorld.update(self, time, dt)
        if self.physics_instance is not None:
            offset = LPoint3d(0, 0, 0.8)
            self.physics_instance.set_pos(*(self.anchor.get_local_position() + offset))
            self.physics_instance.set_quat(LQuaternion(*self.anchor.get_absolute_orientation()))

class RalphControl(EventsControllerBase):
    def __init__(self, sun, engine):
        EventsControllerBase.__init__(self)
        self.sun = sun
        self.engine = engine

    def register_events(self):
        self.accept("escape", sys.exit)
        self.accept("control-q", sys.exit)
        self.accept("w", self.engine.toggle_water)
        self.accept("h", self.engine.print_debug)
        self.accept("f2", self.engine.connect_pstats)
        self.accept("f3", self.engine.toggle_filled_wireframe)
        self.accept("shift-f3", self.engine.toggle_wireframe)
        self.accept("f5", self.engine.bufferViewer.toggleEnable)
        self.accept('f8', self.toggle_lod_freeze)
        if self.engine.terrain_shape is not None:
            self.accept("shift-f8", self.engine.terrain_shape.dump_tree)
            self.accept("shift-control-f8", self.engine.terrain_shape.dump_patches)
        self.accept('control-f8', self.toggle_split_merge_debug)
        self.accept('f9', self.toggle_shader_debug_coord)
        self.accept('shift-f9', self.toggle_bb)
        self.accept('control-f9', self.toggle_frustum)
        self.accept("f10", self.engine.save_screenshot)
        self.accept("shift-f11", self.debug_ls)
        self.accept('alt-enter', self.engine.toggle_fullscreen)
        self.accept('{', self.engine.incr_ambient, [-0.05])
        self.accept('}', self.engine.incr_ambient, [+0.05])
        self.accept('space', self.engine.spawn_box)

        self.accept("o", self.set_key, ["sun-left", True])#, direct=True)
        self.accept("o-up", self.set_key, ["sun-left", False])
        self.accept("p", self.set_key, ["sun-right", True])#, direct=True)
        self.accept("p-up", self.set_key, ["sun-right", False])

    def toggle_lod_freeze(self):
        settings.debug_lod_freeze = not settings.debug_lod_freeze

    def toggle_split_merge_debug(self):
        settings.debug_lod_split_merge = not settings.debug_lod_split_merge

    def toggle_shader_debug_coord(self):
        settings.shader_debug_coord = not settings.shader_debug_coord
        self.engine.trigger_check_settings = True

    def toggle_bb(self):
        settings.debug_lod_show_bb = not settings.debug_lod_show_bb
        self.engine.trigger_check_settings = True

    def toggle_frustum(self):
        settings.debug_lod_frustum = not settings.debug_lod_frustum
        self.engine.trigger_check_settings = True

    def debug_ls(self):
        self.engine.scene_manager.ls()
        if self.engine.physics is not None:
            self.engine.physics.ls()

    def update(self, time, dt):
        if self.keymap.get("sun-left"):
            self.sun.set_light_angle(self.sun.light_angle + 30 * dt)
        if self.keymap.get("sun-right"):
            self.sun.set_light_angle(self.sun.light_angle - 30 * dt)

    def get_point_radiance(self, distance):
        return 1 / pi

class SimpleShadowCaster(CustomShadowMapShadowCaster):
    def update(self):
        pass

class RalphAppConfig:
    def __init__(self):
        self.test_start = False

class RoamingRalphDemo(CosmoniumBase):
    def create_tile(self, x, y):
        self.terrain_shape.add_root_patch(x, y)

    def create_terrain(self):
        self.terrain_world = self.worlds.terrain
        if self.terrain_world is not None:
            self.terrain_surface = self.terrain_world.surface
            self.terrain_shape = self.terrain_surface.shape
            if self.has_water:
                self.terrain_shape.factory.add_layer_factory(WaterLayerFactory(self.water))
            if self.physics is not None and self.physics.support_heightmap:
                self.terrain_shape.factory.add_layer_factory(PhysicsLayerFactory(self.physics))
        else:
            self.terrain_shape = None

    async def create_instance(self):
        #TODO: Should do init correctly
        WaterNode.z = self.water.level
        WaterNode.observer = self.observer
        if self.has_water:
            WaterNode.create_cam()

    def spawn_box(self):
        if not self.ralph_config.physics.enable: return
        if self.ralph_config.physics.model is None: return
        box = PhysicsBox(self.ralph_config.physics.model,
                         self.physics,
                         self.ralph_config.physics.mass,
                         self.ralph_config.physics.limit)
        box.create_instance(self.ralph_world.anchor)
        self.physic_objects.append(box)

    def toggle_water(self):
        if not self.has_water: return
        self.water.visible = not self.water.visible
        if self.water.visible:
            WaterNode.create_cam()
        else:
            WaterNode.remove_cam()
        self.terrain_shape.check_settings()

    def get_height(self, position):
        height = self.terrain_surface.get_height_under(position)
        if self.has_water and self.water.visible and height < self.water.level:
            height = self.water.level
        return height

    #Used by populator
    def get_height_patch(self, patch, u, v):
        height = self.terrain_surface.get_height_patch(patch, u, v)
        if self.has_water and self.water.visible and height < self.water.level:
            height = self.water.level
        return height

    def set_ambient(self, ambient):
        settings.global_ambient = clamp(ambient, 0.0, 1.0)
        if settings.use_srgb:
            corrected_ambient = pow(settings.global_ambient, 2.2)
        else:
            corrected_ambient = settings.global_ambient
        settings.corrected_global_ambient = corrected_ambient
        render.set_shader_input("global_ambient", settings.corrected_global_ambient)
        print("Ambient light level:  %.2f" % settings.global_ambient)

    def incr_ambient(self, ambient_incr):
        self.set_ambient(settings.global_ambient + ambient_incr)

    #TODO: Needed by patchedshapes.py update_lod()
    def get_min_radius(self):
        return 0

    def __init__(self, args):
        self.app_config = RalphAppConfig()
        CosmoniumBase.__init__(self)
        SceneWorld.context = self

        self.update_id = 0
        settings.color_picking = False
        settings.scale = 1.0
        settings.use_depth_scaling = False
        settings.infinite_far_plane = False
        self.gui = None

        self.worlds = FlatUniverse()

        if args.config is not None:
            self.config_file = args.config
        else:
            self.config_file = 'ralph-data/ralph.yaml'
        self.splash = NoSplash()
        self.ralph_config = RalphConfigParser(self.worlds)
        if self.ralph_config.load_and_parse(self.config_file) is None:
            sys.exit(1)

        self.has_water = True
        self.water = self.ralph_config.water

        if self.ralph_config.physics.enable:
            self.physics = Physics(self.ralph_config.physics.debug)
            self.physics.enable()
            self.physics.set_gravity(self.ralph_config.physics.gravity)
            if self.ralph_config.physics.debug:
                print("Disabling camera at origin")
                settings.camera_at_origin = False
        else:
            self.physics = None
        self.physic_objects = []

        self.fullscreen = False
        self.shadow_caster = None
        self.set_ambient(settings.global_ambient)
        self.shadows = True
        self.pssm_shadows = True
        self.init_c_settings()

        self.cam.node().set_camera_mask(BaseObject.DefaultCameraFlag | BaseObject.NearCameraFlag)
        self.observer = CameraHolder()
        self.observer.init()
        if C_CameraHolder is not None:
            self.c_camera_holder = C_CameraHolder(self.observer.anchor, self.observer.camera_np, self.observer.lens)
        else:
            self.c_camera_holder = self.observer
        self.update_c_settings()
        self.scene_manager = StaticSceneManager(base.render)
        self.scene_manager.init_camera(self.c_camera_holder, self.cam)
        remove_main_region(self.cam)
        self.scene_manager.scale = 1.0
        self.pipeline.create()
        self.pipeline.set_scene_manager(self.scene_manager)

        self.context = self
        self.oid_color = 0
        self.oid_texture = None

        base.setFrameRateMeter(True)

        taskMgr.add(self.init())

    def init_c_settings(self):
        if c_settings is not None:
            c_settings.offset_body_center = settings.offset_body_center
            c_settings.camera_at_origin = settings.camera_at_origin
            c_settings.use_depth_scaling = settings.use_depth_scaling
            c_settings.use_inv_scaling = settings.use_inv_scaling
            c_settings.use_log_scaling = settings.use_log_scaling
            c_settings.inverse_z = settings.use_inverse_z
            c_settings.default_near_plane = settings.near_plane
            c_settings.infinite_far_plane = settings.infinite_far_plane
            c_settings.default_far_plane = settings.far_plane
            c_settings.infinite_plane = settings.infinite_plane
            c_settings.auto_infinite_plane = settings.auto_infinite_plane
            c_settings.lens_far_limit = settings.lens_far_limit

    def update_c_settings(self):
        if self.c_camera_holder is not None:
            self.c_camera_holder.cos_fov2 = self.observer.cos_fov2

    async def init(self):
        self.create_terrain()

        await self.create_instance()
        if self.terrain_world is not None:
            self.create_tile(0, 0)

        # Create the main character, Ralph

        self.ralph_shape_object = self.ralph_config.ralph_shape_object
        self.ralph_world = RalphWord('ralph', self.ralph_shape_object, 1.5, self.ralph_config.physics.enable)
        self.worlds.add_world(self.ralph_world)
        self.worlds.add_special(self.ralph_world)

        if self.shadows:
            if self.pssm_shadows:
                self.worlds.set_global_shadows(PSSMShadowMapShadowCaster(self.worlds.lights.lights[0], self.ralph_world))
            else:
                self.shadow_caster = SimpleShadowCaster(self.light, self.terrain_world)
                self.shadow_caster.create()
                self.shadow_caster.shadow_map.set_lens(self.ralph_config.shadow_size, -self.ralph_config.shadow_box_length / 2.0, self.ralph_config.shadow_box_length / 2.0, self.skybox.light_dir)
                self.shadow_caster.shadow_map.snap_cam = True
        else:
            self.shadow_caster = None

        if self.terrain_world:
            self.camera_controller = SurfaceFollowCameraController()
            self.camera_controller.set_body(self.terrain_world)
            self.camera_controller.set_camera_hints(distance=5, max=1.5)
        else:
            self.camera_controller = FixedCameraController()
            self.camera_controller.set_camera_hints(position=LVector3d(0, -2, 1))
        self.camera_controller.activate(self.observer, self.ralph_world.anchor)

        self.controller = RalphControl(self.worlds.lights.lights[0], self)
        self.controller.register_events()

        if self.terrain_world:
            self.mover = FlatSurfaceBodyMover(self.ralph_world.anchor, self.terrain_world)
        else:
            self.mover = CartesianBodyMover(self.ralph_world.anchor)
        self.mover.activate()
        self.nav = ControlNav()
        self.nav.set_controller(self.mover)
        self.nav.register_events(self)
        self.nav.speed = 25
        self.nav.rot_step_per_sec = 2

        self.worlds.init()

        taskMgr.add(self.main_update_task, "main-update-task", sort=settings.main_update_task_sort)
        taskMgr.add(self.update_instances_task, "instances-task", sort=settings.instances_update_task_sort)

    def main_update_task(self, task):
        dt = globalClock.getDt()
        self.update_id += 1

        self.pipeline.process_last_frame(dt)

        if self.trigger_check_settings:
            self.worlds.check_settings()
            self.trigger_check_settings = False

        self.worlds.start_update()
        self.worlds.update_specials(0, self.update_id)
        self.nav.update(0, dt)
        self.controller.update(0, dt)
        self.mover.update()
        self.camera_controller.update(0, dt)
        self.worlds.update_specials_observer(self.observer, self.update_id)

        self.worlds.update(0, dt, self.update_id, self.observer)
        self.worlds.update_height_under(self.observer)

        if self.ralph_config.physics.enable:
            to_remove = []
            self.physics.update(0, dt)
            for physic_object in self.physic_objects:
                keep = physic_object.update(self.observer)
                if not keep:
                    to_remove.append(physic_object)
            for physic_object in to_remove:
                self.physic_objects.remove(physic_object)

        if self.shadow_caster is not None:
            if self.pssm_shadows:
                pass #self.shadow_caster.update(self.scene_manager)
            else:
                vec = self.ralph_world.anchor.get_local_position() - self.observer.anchor.get_local_position()
                vec.set_z(0)
                dist = vec.length()
                vec.normalize()
                #TODO: Should use the directional light to set the pos
                self.shadow_caster.shadow_map.set_direction(self.skybox.light_dir)
                self.shadow_caster.shadow_map.set_pos(self.ralph_world.anchor.get_local_position() - vec * dist + vec * self.ralph_config.shadow_size / 2)

        self.scene_manager.update_scene_and_camera(0, self.c_camera_holder)

        self.worlds.update_states()
        self.worlds.update_scene_anchors(self.scene_manager)
        #self.worlds.check_scattering()


        self.worlds.find_shadows()
        self.worlds.update_instances_state(self.scene_manager)
        self.worlds.update_lod(self.observer)

        return task.cont

    def update_instances_task(self, task):
        self.worlds.update_instances(self.scene_manager, self.observer)
        self.scene_manager.build_scene(self.common_state, self.c_camera_holder, self.worlds.visible_scene_anchors, self.worlds.resolved_scene_anchors)

        return task.cont

    def print_debug(self):
        if self.terrain_world is not None:
            print("Height:", self.get_height(self.ralph_world.anchor.get_local_position()),
                  self.terrain_surface.get_height_under(self.ralph_world.anchor.get_local_position()))
        print("Ralph:", self.ralph_world.anchor.get_local_position(), self.ralph_world.anchor.get_frame_position(), self.ralph_world.anchor.get_frame_orientation().get_hpr(), self.ralph_world.anchor.get_absolute_orientation().get_hpr())
        print("Camera:", self.observer.get_local_position(), self.observer.get_absolute_orientation().get_hpr())
        position = self.ralph_world.anchor.get_local_position()
        coord = self.ralph_shape_object.shape.global_to_shape_coord(position[0], position[1])
        patch = self.ralph_shape_object.shape.find_patch_at(coord)
        if patch is not None:
            print("Ralph patch:", patch.str_id())
        position = self.observer.anchor.get_local_position()
        coord = self.ralph_shape_object.shape.global_to_shape_coord(position[0], position[1])
        patch = self.ralph_shape_object.shape.find_patch_at(coord)
        if patch is not None:
            print("Camera patch:", patch.str_id())

parser = argparse.ArgumentParser()
parser.add_argument("--config",
                    help="Path to the file with the configuration",
                    default=None)
if sys.platform == "darwin":
    #Ignore -psn_<app_id> from MacOS
    parser.add_argument('-p', help=argparse.SUPPRESS)
args = parser.parse_args()

demo = RoamingRalphDemo(args)
demo.run()
