#!/usr/bin/env python
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

from direct.showbase.DirectObject import DirectObject
from panda3d.core import AmbientLight, DirectionalLight, LColor
from panda3d.core import LPoint3d, LQuaterniond, LVector3, LVector3d, LQuaternion, BitMask32, NodePath
from panda3d.bullet import BulletHeightfieldShape, BulletBoxShape, BulletRigidBodyNode, BulletCapsuleShape, ZUp

from cosmonium.foundation import BaseObject
from cosmonium.scenemanager import StaticSceneManager
from cosmonium.sceneworld import Worlds, CartesianWorld, FlatTerrainWorld
from cosmonium.lights import LightSources, SurrogateLight
from cosmonium.heightmapshaders import DisplacementVertexControl
from cosmonium.procedural.water import WaterNode
from cosmonium.appearances import ModelAppearance
from cosmonium.shaders import BasicShader, Fog, ConstantTessellationControl, ShaderShadowMap
from cosmonium.shapes import ActorShape, CompositeShapeObject, ShapeObject
from cosmonium.ships import ActorShip, NoShip
from cosmonium.surfaces import HeightmapFlatSurface
from cosmonium.tiles import Tile, TiledShape, GpuPatchTerrainLayer, MeshTerrainLayer
from cosmonium.patchedshapes import PatchFactory, PatchLayer, VertexSizeMaxDistanceLodControl
from cosmonium.shadows import ShadowMapDataSource, CustomShadowMapShadowCaster
from cosmonium.camera import CameraHolder, SurfaceFollowCameraController, EventsControllerBase
from cosmonium.nav import ControlNav
from cosmonium.parsers.heightmapsparser import HeightmapYamlParser
from cosmonium.controllers import ShipSurfaceBodyMover
from cosmonium.parsers.yamlparser import YamlModuleParser
from cosmonium.parsers.populatorsparser import PopulatorYamlParser
from cosmonium.parsers.appearancesparser import AppearanceYamlParser
from cosmonium.physics import Physics
from cosmonium.ui.splash import NoSplash
from cosmonium.utils import quaternion_from_euler
from cosmonium.cosmonium import CosmoniumBase
from cosmonium import settings

from cosmonium.astro import units

#TODO: Change of base unit should be done properly
units.m = 1.0
units.Km = 1000.0

from math import pow, pi, sqrt
import argparse

class TileFactory(PatchFactory):
    def __init__(self, heightmap, tile_density, size, has_water, water, has_physics, physics):
        self.heightmap = heightmap
        self.tile_density = tile_density
        self.size = size
        self.has_water = has_water
        self.water = water
        self.has_physics = has_physics
        self.physics = physics

    def get_patch_limits(self, patch):
        height_scale = self.heightmap.height_scale
        height_offset = self.heightmap.height_offset
        min_height = self.heightmap.min_height# * height_scale + height_offset
        max_height = self.heightmap.max_height# * height_scale + height_offset
        mean_height = (self.heightmap.min_height + self.heightmap.max_height) / 2.0# * height_scale + height_offset
        if patch is not None:
            patch_data = self.heightmap.get_patch_data(patch, recurse=True)
            if patch_data is not None:
                #TODO: This should be done inside the heightmap patch
                min_height = patch_data.min_height * height_scale + height_offset
                max_height = patch_data.max_height * height_scale + height_offset
                mean_height = patch_data.mean_height * height_scale + height_offset
            else:
                print("NO PATCH DATA !!!", patch.str_id())
        return (min_height, max_height, mean_height)

    def create_patch(self, parent, lod, face, x, y):
        (min_height, max_height, mean_height) = self.get_patch_limits(parent)
        patch = Tile(parent, lod, x, y, self.tile_density, self.size, min_height, max_height)
        #print("Create tile", patch.lod, patch.x, patch.y, patch.size, patch.scale, min_height, max_height, patch.flat_coord)
        if settings.hardware_tessellation:
            terrain_layer = GpuPatchTerrainLayer()
        else:
            terrain_layer = MeshTerrainLayer()
        patch.add_layer(terrain_layer)
        if self.has_water:
            patch.add_layer(WaterLayer(self.water))
        if self.has_physics:
            patch.add_layer(PhysicsLayer(self.physics))
        return patch

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

    def patch_done(self, patch):
        pass

    def update_instance(self, patch):
        pass

    def remove_instance(self):
        if self.water is not None:
            self.water.remove_instance()
            self.water = None

class PhysicsLayer(PatchLayer):
    def __init__(self, physics):
        self.physics = physics
        self.instance = None

    def patch_done(self, patch):
        heightmap_patch = patch.owner.heightmap.get_patch_data(patch)
        shape = BulletHeightfieldShape(heightmap_patch.texture, patch.owner.heightmap.height_scale, ZUp)
        shape.setUseDiamondSubdivision(True)
        self.instance = NodePath(BulletRigidBodyNode('Heightfield'))
        self.instance.node().add_shape(shape)
        x = (patch.x0 + patch.x1) / 2.0
        y = (patch.y0 + patch.y1) / 2.0
        z = patch.owner.heightmap.height_scale / 2
        self.instance.set_pos(patch.scale * x, patch.scale * y , z)
        self.instance.set_scale(patch.scale / heightmap_patch.width, patch.scale / heightmap_patch.height, 1.0)
        self.instance.setCollideMask(BitMask32.allOn())
        self.physics.add(self.instance)

    def remove_instance(self):
        if self.instance is None: return
        self.physics.remove(self.instance)
        self.instance.remove_node()
        self.instance = None

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
    def decode(self, data):
        biome = data.get('biome', None)
        control = data.get('control', None)
        appearance = data.get('appearance', None)
        water = data.get('water', None)
        fog = data.get('fog', None)
        physics = data.get('physics', {})

        terrain = data.get('terrain', {})
        self.tile_size = terrain.get("tile-size", 1024)
        self.tile_density = terrain.get('tile-density', 64)
        self.max_vertex_size = terrain.get('max-vertex-size', 128)
        self.max_lod = terrain.get('max-lod', 10)
        self.max_distance = terrain.get('max-distance', 1.001 * 1024 * sqrt(2))
        #TODO: coord_scale should simply be tile_size
        self.coord_scale = self.tile_size / 16384

        self.heightmap = HeightmapYamlParser.decode(data.get('heightmap', {}), 'heightmap', patched=True, scale=self.tile_size, coord_scale=self.coord_scale)
        self.biome = HeightmapYamlParser.decode(data.get('biome', {}), 'biome', patched=True, scale=self.tile_size, coord_scale=self.coord_scale)

        self.shadow_size = terrain.get('shadow-size', 16)
        self.shadow_box_length = terrain.get('shadow-depth', self.tile_size)

        layers = data.get('layers', [])
        self.layers = []
        for layer in layers:
            self.layers.append(PopulatorYamlParser.decode(layer))

        self.appearance = AppearanceYamlParser.decode(appearance, self.heightmap, 1.0, patched_shape=True)
        self.appearance.texture_source.extend *= 1000

        if water is not None:
            level = water.get('level', 0)
            visible = water.get('visible', False)
            scale = water.get('scale', 8.0)
            self.water = WaterConfig(level, visible, scale)
        else:
            self.water = WaterConfig(0, False, 1.0)

        if fog is not None:
            self.fog_parameters = {}
            self.fog_parameters['fall_off'] = fog.get('falloff', 0.035)
            self.fog_parameters['density'] = fog.get('density', 20)
            self.fog_parameters['ground'] = fog.get('ground', -500)
        else:
            self.fog_parameters = None

        has_physics = physics.get('enable', False)
        gravity = physics.get('gravity', 9.81)
        model = physics.get('model', None)
        mass = physics.get('mass', 20)
        limit = physics.get('limit', 100)
        enable_debug = physics.get('debug', False)
        self.physics = PhysicsConfig(has_physics, gravity, model, mass, limit, enable_debug)

        return True

class RaphSkyBox(DirectObject):
    def __init__(self):
        self.skybox = None
        self.sun_color = None
        self.skybox_color = None
        self.light_angle = None
        self.light_dir = LVector3d.up()
        self.light_quat = LQuaternion()
        self.light_color = (1.0, 1.0, 1.0, 1.0)
        self.fog = None

    def init(self, config):
        skynode = base.camera.attachNewNode('skybox')
        base.camera.hide(BaseObject.AllCamerasMask)
        base.camera.show(BaseObject.DefaultCameraFlag | BaseObject.WaterCameraFlag)
        self.skybox = loader.loadModel('ralph-data/models/rgbCube')
        self.skybox.reparentTo(skynode)

        self.skybox.setTextureOff(1)
        self.skybox.setShaderOff(1)
        self.skybox.setTwoSided(True)
        # make big enough to cover whole terrain, else there'll be problems with the water reflections
        self.skybox.setScale(1.5 * config.tile_size)
        self.skybox.setBin('background', 1)
        self.skybox.setDepthWrite(False)
        self.skybox.setDepthTest(False)
        self.skybox.setLightOff(1)
        self.skybox.setShaderOff(1)
        self.skybox.setFogOff(1)

        #self.skybox.setColor(.55, .65, .95, 1.0)
        self.skybox_color = LColor(pow(0.5, 1/2.2), pow(0.6, 1/2.2), pow(0.7, 1/2.2), 1.0)
        self.sun_color = LColor(pow(1.0, 1/2.2), pow(0.9, 1/2.2), pow(0.7, 1/2.2), 1.0)
        self.skybox.setColor(self.skybox_color)

    def set_fog(self, fog):
        self.fog = fog
        self.set_light_angle(self.light_angle)

    def set_light_angle(self, angle):
        self.light_angle = angle
        self.light_quat.setFromAxisAngleRad(angle * pi / 180, LVector3.forward())
        self.light_dir = self.light_quat.xform(-LVector3.up())
        cosA = self.light_dir.dot(-LVector3.up())
        if cosA >= 0:
            coef = sqrt(cosA)
            self.light_color = (1, coef, coef, 1)
            new_sky_color = self.skybox_color * cosA
            new_sky_color[3] = 1.0
            self.skybox.setColor(new_sky_color)
            if self.fog is not None:
                self.fog.fog_color = self.skybox_color * cosA
                self.fog.sun_color = self.sun_color * cosA
        else:
            self.light_color = (0, 0, 0, 1)
            self.skybox.setColor(self.light_color)
            if self.fog is not None:
                self.fog.fog_color = self.skybox_color * 0
                self.fog.sun_color = self.sun_color * 0

class RalphWord(CartesianWorld):
    def __init__(self, name, ship_object, radius, enable_physics):
        CartesianWorld.__init__(self, name)
        self.add_component(ship_object)
        self.ship_object = ship_object
        self.current_state = None
        self.physics_instance = None
        self.enable_physics = enable_physics

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
        if self.enable_physics and self.physics_instance is None:
            bounds = self.instance.get_tight_bounds()
            dims = bounds[1] - bounds[0]
            width = max(dims[0], dims[1]) / 2.0
            height = dims[2]
            self.physics_instance = NodePath(BulletRigidBodyNode("Ralph"))
            shape = BulletCapsuleShape(width, height - 2 * width, ZUp)
            self.physics_instance.node().addShape(shape)
            self.physics_instance.node().setMass(1.0)
            self.physics_instance.node().setKinematic(True)
            base.physics.add(self.physics_instance)

    def update(self, time, dt):
        CartesianWorld.update(self, time, dt)
        if self.physics_instance is not None:
            offset = LPoint3d(0, 0, 0.8)
            self.physics_instance.set_pos(*(self._local_position + offset))
            self.physics_instance.set_quat(LQuaternion(*self._orientation))

    def get_apparent_radius(self):
        return 1.5

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
        self.accept("shift-f8", self.engine.terrain_shape.dump_tree)
        self.accept("shift-control-f8", self.engine.terrain_shape.dump_patches)
        self.accept('control-f8', self.toggle_split_merge_debug)
        self.accept('shift-f9', self.toggle_bb)
        self.accept('control-f9', self.toggle_frustum)
        self.accept("f10", self.engine.save_screenshot)
        self.accept("shift-f11", self.engine.scene_manager.ls)
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

    def toggle_bb(self):
        settings.debug_lod_show_bb = not settings.debug_lod_show_bb
        self.engine.trigger_check_settings = True

    def toggle_frustum(self):
        settings.debug_lod_frustum = not settings.debug_lod_frustum
        self.engine.trigger_check_settings = True

    def update(self, time, dt):
        if self.keymap.get("sun-left"):
            self.sun.set_light_angle(self.sun.light_angle + 30 * dt)
            self.engine.update_shader()
        if self.keymap.get("sun-right"):
            self.sun.set_light_angle(self.sun.light_angle - 30 * dt)
            self.engine.update_shader()

class FakeLightSource:
    light_color = LColor(1, 1, 1, 1)

class SimpleShadowCaster(CustomShadowMapShadowCaster):
    def update(self):
        pass

class RalphAppConfig:
    def __init__(self):
        self.test_start = False

class RoamingRalphDemo(CosmoniumBase):
    def create_terrain_shader(self):
#         control4 = HeightColorMap('colormap',
#                 [
#                  ColormapLayer(0.00, top=LRGBColor(0, 0.1, 0.24)),
#                  ColormapLayer(0.40, top=LRGBColor(0, 0.1, 0.24)),
#                  ColormapLayer(0.49, top=LRGBColor(0, 0.6, 0.6)),
#                  ColormapLayer(0.50, bottom=LRGBColor(0.9, 0.8, 0.6), top=LRGBColor(0.5, 0.4, 0.3)),
#                  ColormapLayer(0.80, top=LRGBColor(0.2, 0.3, 0.1)),
#                  ColormapLayer(0.90, top=LRGBColor(0.7, 0.6, 0.4)),
#                  ColormapLayer(1.00, bottom=LRGBColor(1, 1, 1), top=LRGBColor(1, 1, 1)),
#                 ])
        data_source = []
        if self.terrain_shape.data_store is not None:
            data_source.append(self.terrain_shape.data_store.get_shader_data_source())
        data_source.append(self.ralph_config.heightmap.get_data_source(self.terrain_shape.data_store is not None))
        data_source.append(self.ralph_config.biome.get_data_source(self.terrain_shape.data_store is not None))
        data_source.append(self.ralph_config.appearance.get_data_source())
        if settings.hardware_tessellation:
            tessellation_control = ConstantTessellationControl()
        else:
            tessellation_control = None
        self.terrain_shader = BasicShader(appearance=self.ralph_config.appearance.get_shader_appearance(),
                                          tessellation_control=tessellation_control,
                                          vertex_control=DisplacementVertexControl(self.ralph_config.heightmap),
                                          data_source=data_source)
        if self.shadows:
            self.terrain_shader.add_shadows(ShaderShadowMap('shadows', use_bias=False))

    def create_tile(self, x, y):
        self.terrain_shape.add_root_patch(x, y)

    def create_terrain(self):
        self.tile_factory = TileFactory(self.ralph_config.heightmap,
                                        self.ralph_config.tile_density, self.ralph_config.tile_size,
                                        self.has_water, self.water,
                                        self.ralph_config.physics.enable, self.physics)
        self.terrain_shape = TiledShape(self.tile_factory,
                                        self.ralph_config.tile_size,
                                        VertexSizeMaxDistanceLodControl(self.ralph_config.max_distance / self.ralph_config.tile_size,
                                                                        self.ralph_config.max_vertex_size,
                                                                        density=settings.patch_constant_density,
                                                                        max_lod=self.ralph_config.max_lod))
        self.create_terrain_shader()
        self.terrain_object = HeightmapFlatSurface(
                               'surface',
                               0, self.ralph_config.tile_size,
                               self.terrain_shape,
                               self.ralph_config.heightmap,
                               self.ralph_config.biome,
                               self.ralph_config.appearance,
                               self.terrain_shader,
                               clickable=False)
        self.terrain_object.set_body(self)
        self.terrain = CompositeShapeObject()
        self.terrain.add_component(self.terrain_object)

    async def create_instance(self):
        await self.terrain.create_instance(self.terrain_world.scene_anchor)
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
        box.create_instance(self.ralph)
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
        height = self.terrain_object.get_height_at(position[0], position[1])
        if self.has_water and self.water.visible and height < self.water.level:
            height = self.water.level
        return height

    #Used by populator
    def get_height_patch(self, patch, u, v):
        height = self.terrain_object.get_height_patch(patch, u, v)
        if self.has_water and self.water.visible and height < self.water.level:
            height = self.water.level
        return height

    def set_ambient(self, ambient):
        settings.global_ambient = clamp(ambient, 0.0, 1.0)
        if settings.srgb:
            corrected_ambient = pow(settings.global_ambient, 2.2)
        else:
            corrected_ambient = settings.global_ambient
        settings.corrected_global_ambient = corrected_ambient
        render.set_shader_input("global_ambient", settings.corrected_global_ambient)
        print("Ambient light level:  %.2f" % settings.global_ambient)

    def incr_ambient(self, ambient_incr):
        self.set_ambient(settings.global_ambient + ambient_incr)

    def update_shader(self):
        self.terrain.update_shader()
        self.ralph_shape_object.update_shader()

    #TODO: Needed by patchedshapes.py update_lod()
    def get_min_radius(self):
        return 0

    def __init__(self, args):
        self.app_config = RalphAppConfig()
        CosmoniumBase.__init__(self)

        self.update_id = 0
        settings.color_picking = False
        settings.scale = 1.0
        settings.use_depth_scaling = False
        self.gui = None

        if args.config is not None:
            self.config_file = args.config
        else:
            self.config_file = 'ralph-data/ralph.yaml'
        self.splash = NoSplash()
        self.ralph_config = RalphConfigParser()
        if self.ralph_config.load_and_parse(self.config_file) is None:
            sys.exit(1)

        self.has_water = True
        self.water = self.ralph_config.water

        if self.ralph_config.physics.enable:
            self.physics = Physics(self.ralph_config.physics.debug)
            self.physics.enable()
            self.physics.set_gravity(self.ralph_config.physics.gravity)
        else:
            self.physics = None
        self.physic_objects = []

        self.fullscreen = False
        self.shadow_caster = None
        self.set_ambient(0.3)
        self.shadows = True

        self.cam.node().set_camera_mask(BaseObject.DefaultCameraFlag | BaseObject.NearCameraFlag)
        self.observer = CameraHolder()
        self.observer.init()
        self.scene_manager = StaticSceneManager()
        self.scene_manager.init_camera(self.observer, self.cam)
        self.scene_manager.scale = 1.0
        self.worlds = Worlds()

        self.model_body_center_offset = LVector3d()
        self.light_color = LColor(1, 1, 1, 1)
        self.context = self
        self.oid_color = 0
        self.oid_texture = None
        #Needed for create_light to work
        self.nearest_system = self
        self.star = self
        self.primary = None
        self.size = self.ralph_config.tile_size #TODO: Needed by populator

        self.skybox = RaphSkyBox()
        self.skybox.init(self.ralph_config)
        self.skybox.set_light_angle(45)

        self.ambientLight = AmbientLight("ambientLight")
        self.ambientLight.setColor((settings.global_ambient, settings.global_ambient, settings.global_ambient, 1))
        render.setLight(render.attachNewNode(self.ambientLight))

        base.setFrameRateMeter(True)

        taskMgr.add(self.init())

    async def init(self):
        self.lights = LightSources()
        self.light = SurrogateLight(FakeLightSource(), None)
        self.light.light_direction = LVector3d(1, 0, 0)
        self.lights.add_light(self.light)

        self.create_terrain()
        for component in self.ralph_config.layers:
            self.terrain.add_component(component)
            self.terrain_shape.add_linked_object(component)

        if self.ralph_config.fog_parameters is not None:
            self.fog = Fog(**self.ralph_config.fog_parameters)
            self.terrain.add_after_effect(self.fog)
            self.skybox.set_fog(self.fog)
        else:
            self.fog = None
        self.surface = self.terrain_object
        self.terrain_world = FlatTerrainWorld("terrain")
        self.terrain_world.on_visible(self.scene_manager)
        self.terrain_world.set_terrain(self.terrain_object)
        self.terrain_object.set_body(self.terrain_world)
        self.terrain_world.add_component(self.terrain)
        self.terrain_world.surface = self
        self.terrain_world.context = self
        self.terrain_world.model_body_center_offset = 0.0
        self.worlds.add_world(self.terrain_world)

        if self.shadows:
            self.shadow_caster = SimpleShadowCaster(self.light, self.terrain_world)
            #self.shadow_caster = ShadowMap(1024)
            self.shadow_caster.create()
            self.shadow_caster.shadow_map.set_lens(self.ralph_config.shadow_size, -self.ralph_config.shadow_box_length / 2.0, self.ralph_config.shadow_box_length / 2.0, self.skybox.light_dir)
            self.shadow_caster.shadow_map.snap_cam = True
        else:
            self.shadow_caster = None

        if self.shadows:
            shadows_data_source = ShadowMapDataSource('shadows', self.shadow_caster, use_bias=False, calculate_shadow_coef=False)
            self.terrain_object.sources.add_source(shadows_data_source)
        self.terrain_object.sources.add_source(self.lights)

        await self.create_instance()
        self.create_tile(0, 0)

        # Create the main character, Ralph

        self.ralph_shape = ActorShape("ralph-data/models/ralph",
                                      {"run": "ralph-data/models/ralph-run",
                                       "walk": "ralph-data/models/ralph-walk"},
                                      auto_scale_mesh=False,
                                      rotation=quaternion_from_euler(180, 0, 0),
                                      scale=LVector3d(0.2, 0.2, 0.2))
        self.ralph_appearance = ModelAppearance(vertex_color=True, material=False)
        self.ralph_shader = BasicShader()
        if self.shadows:
            self.ralph_shader.add_shadows(ShaderShadowMap('shadows', use_bias=True))

        self.ralph_shape_object = ShapeObject('ralph', self.ralph_shape, self.ralph_appearance, self.ralph_shader, clickable=False)
        self.ralph_world = RalphWord('ralph', self.ralph_shape_object, 1.5, self.ralph_config.physics.enable)
        self.ralph_world.on_visible(self.scene_manager)
        #self.ralph_world.add_component(self.ralph_shape_object)
        self.worlds.add_world(self.ralph_world)
        self.ralph_world.anchor.set_bounding_radius(1.5)
        self.ralph_shape_object.body = self.ralph_world
        self.ralph_shape_object.set_owner(self.ralph_world)
        if self.shadows:
            shadows_data_source = ShadowMapDataSource('shadows', self.shadow_caster, use_bias=True, calculate_shadow_coef=False)
            self.ralph_shape_object.sources.add_source(shadows_data_source)
        self.ralph_shape_object.sources.add_source(self.lights)
        await self.ralph_shape_object.create_instance(self.ralph_world.scene_anchor)
        #self.ralph = RalphShip('ralph', self.ralph_shape_object, 1.5, self.ralph_config.physics.enable)
        #self.ralph.create_own_shadow_caster = False

        self.camera_controller = SurfaceFollowCameraController()
        #self.camera_controller = FixedCameraController()
        self.camera_controller.activate(self.observer, self.ralph_world.anchor)
        self.camera_controller.set_body(self.terrain_world)
        self.camera_controller.set_camera_hints(distance=5, max=1.5)

        self.controller = RalphControl(self.skybox, self)
        self.controller.register_events()

        self.mover = ShipSurfaceBodyMover(self.ralph_world.anchor, self.terrain_world)
        self.mover.activate()
        self.nav = ControlNav()
        self.nav.set_controller(self.mover)
        self.nav.register_events(self)
        self.nav.speed = 25
        self.nav.rot_step_per_sec = 2

        self.worlds.update_anchor(0, 0)
        self.camera_controller.update(0, 0)
        self.mover.update()
        self.worlds.update_anchor_obs(self.observer.anchor, 0)
        self.worlds.update(0, 0)
        self.worlds.update_obs(self.observer.anchor)
        self.worlds.check_visibility(self.observer.anchor.frustum, self.observer.anchor.pixel_size)
        self.worlds.check_and_update_instance(self.scene_manager, self.observer.anchor.get_local_position(), self.observer.anchor.get_absolute_orientation())
        #self.ralph.create_light()
        if self.ralph_config.physics.enable:
            for physic_object in self.physic_objects:
                physic_object.update(self.observer)

        # Set up the camera
        render.set_shader_input("camera", self.camera.get_pos())

        self.terrain.update_instance(self.scene_manager, self.observer.get_local_position(), None)

        taskMgr.add(self.move, "moveTask")

    def move(self, task):
        dt = globalClock.getDt()
        self.update_id += 1

        if self.trigger_check_settings:
            self.terrain.check_settings()
            self.trigger_check_settings = False

        self.worlds.update_anchor(0, self.update_id)
        self.nav.update(0, dt)
        self.controller.update(0, dt)
        self.mover.update()
        self.camera_controller.update(0, dt)
        self.worlds.update_anchor_obs(self.observer.anchor, self.update_id)

        if self.ralph_config.physics.enable:
            to_remove = []
            self.physics.update(0, dt)
            for physic_object in self.physic_objects:
                keep = physic_object.update(self.observer)
                if not keep:
                    to_remove.append(physic_object)
            for physic_object in to_remove:
                self.physic_objects.remove(physic_object)

        #TODO: Proper light management should be added
        self.light_color = self.skybox.light_color
        self.light.light_direction = self.skybox.light_dir
        if False and self.directionalLight is not None:
            self.directionalLight.setDirection(self.skybox.light_dir)

        if self.shadow_caster is not None:
            vec = self.ralph_world.anchor.get_local_position() - self.observer.anchor.get_local_position()
            vec.set_z(0)
            dist = vec.length()
            vec.normalize()
            #TODO: Should use the directional light to set the pos
            self.shadow_caster.shadow_map.set_direction(self.skybox.light_dir)
            self.shadow_caster.shadow_map.set_pos(self.ralph_world.anchor.get_local_position() - vec * dist + vec * self.ralph_config.shadow_size / 2)

        render.set_shader_input("camera", self.camera.get_pos())

        self.worlds.update(0, dt)
        self.worlds.update_obs(self.observer.anchor)
        self.worlds.check_visibility(self.observer.anchor.frustum, self.observer.anchor.pixel_size)
        for world  in self.worlds.worlds:
            world.anchor._height_under = world.get_height_under(self.observer.anchor.get_local_position())
            world.scene_anchor.update(self.scene_manager)

        self.scene_manager.update_scene_and_camera(0, self.observer)

        self.worlds.check_and_update_instance(self.scene_manager, self.observer.anchor.get_local_position(), self.observer.anchor.get_absolute_orientation())

        self.scene_manager.build_scene(self.common_state, self.win, self.observer, [], [])

        return task.cont

    def print_debug(self):
        print("Height:", self.get_height(self.ralph_world.anchor.get_local_position()),
              self.terrain_object.get_height_at(self.ralph_world.anchor.get_local_position()[0], self.ralph_world.anchor.get_local_position()[1]))
        print("Ralph:", self.ralph_world.anchor.get_local_position(), self.ralph_world.anchor.get_frame_position(), self.ralph_world.anchor.get_frame_orientation().get_hpr(), self.ralph_world.anchor.get_absolute_orientation().get_hpr())
        print("Camera:", self.observer.get_local_position(), self.observer.get_absolute_orientation().get_hpr())

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
