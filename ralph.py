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

from __future__ import print_function

import sys
import os
# Disable stdout block buffering
sys.stdout.flush()
sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', buffering=1)

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
from cosmonium.heightmapshaders import HeightmapDataSource, DisplacementVertexControl
from cosmonium.procedural.appearances import ProceduralAppearance
from cosmonium.procedural.water import WaterNode
from cosmonium.appearances import ModelAppearance
from cosmonium.shaders import BasicShader, Fog, ConstantTessellationControl, ShaderShadowMap
from cosmonium.shapes import ActorShape, CompositeShapeObject, ShapeObject
from cosmonium.ships import ActorShip
from cosmonium.surfaces import HeightmapFlatSurface
from cosmonium.tiles import Tile, TiledShape, GpuPatchTerrainLayer, MeshTerrainLayer
from cosmonium.procedural.shaderheightmap import ShaderPatchedHeightmap, HeightmapPatchGenerator
from cosmonium.patchedshapes import PatchFactory, PatchLayer, VertexSizeMaxDistancePatchLodControl
from cosmonium.shadows import ShadowMap
from cosmonium.camera import CameraHolder, SurfaceFollowCameraController, EventsControllerBase
from cosmonium.nav import ControlNav
from cosmonium.parsers.heightmapsparser import InterpolatorYamlParser
from cosmonium.controllers import ShipSurfaceBodyMover
from cosmonium.astro.frame import CartesianSurfaceReferenceFrame
from cosmonium.parsers.yamlparser import YamlModuleParser
from cosmonium.parsers.noiseparser import NoiseYamlParser
from cosmonium.parsers.populatorsparser import PopulatorYamlParser
from cosmonium.parsers.textureparser import TextureDictionaryYamlParser
from cosmonium.parsers.texturecontrolparser import TextureControlYamlParser, HeightColorControlYamlParser
from cosmonium.physics import Physics
from cosmonium.ui.splash import NoSplash
from cosmonium.utils import quaternion_from_euler
from cosmonium.cosmonium import CosmoniumBase
from cosmonium import settings

from math import pow, pi, sqrt
import argparse

class TileFactory(PatchFactory):
    def __init__(self, heightmap, tile_density, size, height_scale, has_water, water, has_physics, physics):
        self.heightmap = heightmap
        self.tile_density = tile_density
        self.size = size
        self.height_scale = height_scale
        self.has_water = has_water
        self.water = water
        self.has_physics = has_physics
        self.physics = physics

    def create_patch(self, parent, lod, x, y):
        #print("CREATE PATCH", x, y)
        min_height = -self.height_scale / self.size
        max_height = self.height_scale / self.size
        if parent is not None:
            heightmap_patch = self.heightmap.get_patch_data(parent)
            if heightmap_patch is not None:
                min_height = heightmap_patch.min_height / self.size
                max_height = heightmap_patch.max_height / self.size
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
        position = observer._local_position + observer._orientation.xform(LPoint3d(0, 15, 5))
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
            scene_rel_position = local_position - observer._local_position
        else:
            scene_rel_position = local_position
        self.instance.set_pos(*scene_rel_position)
        self.instance.set_quat(LQuaternion(*local_rotation))
        if (local_position - observer._local_position).length() > self.limit:
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
        self.heightmap_size = terrain.get('heightmap-size', 512)
        self.biome_size = terrain.get('biome-size', 128)

        heightmap = data.get('heightmap', {})
        raw_height_scale = heightmap.get('max-height', 1.0)
        height_scale_units = heightmap.get('max-height-units', 1.0)
        scale_length = heightmap.get('scale-length', 2.0)
        noise = heightmap.get('noise')
        self.height_scale = raw_height_scale * height_scale_units
        self.noise_scale = raw_height_scale
        #filtering = self.decode_filtering(heightmap.get('filter', 'none'))
        noise_parser = NoiseYamlParser(scale_length)
        heightmap_function = noise_parser.decode(noise)
        self.heightmap_data_source = HeightmapPatchGenerator(self.heightmap_size, self.heightmap_size, heightmap_function, self.tile_size)
        self.shadow_size = terrain.get('shadow-size', 16)
        self.shadow_box_length = terrain.get('shadow-depth', self.height_scale)
        self.interpolator = InterpolatorYamlParser.decode(heightmap.get('interpolator'))
        self.filter = InterpolatorYamlParser.decode(heightmap.get('filter'))
        self.heightmap_max_lod = heightmap.get('max-lod', 100)

        layers = data.get('layers', [])
        self.layers = []
        for layer in layers:
            self.layers.append(PopulatorYamlParser.decode(layer))

        if biome is not None:
            biome_function = noise_parser.decode(biome)
            self.biome_data_source = HeightmapPatchGenerator(self.biome_size, self.biome_size, biome_function, self.tile_size)
        else:
            self.biome_data_source = None

        if appearance is not None:
            appearance_parser = TextureDictionaryYamlParser()
            self.appearance = appearance_parser.decode(appearance)
            self.appearance.extend *= 1000
        else:
            self.appearance = None

        if control is not None:
            control_parser = TextureControlYamlParser()
            self.control = control_parser.decode(control, self.appearance, 1.0)
        else:
            self.control = None

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
        base.camera.show(BaseObject.DefaultCameraMask | BaseObject.WaterCameraMask)
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

class RalphShip(ActorShip):
    def __init__(self, name, ship_object, radius, enable_physics):
        ActorShip.__init__(self, name, ship_object, radius)
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

    def check_and_update_instance(self, camera_pos, camera_rot, pointset):
        ActorShip.check_and_update_instance(self, camera_pos, camera_rot, pointset)
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
        ActorShip.update(self, time, dt)
        if self.physics_instance is not None:
            offset = LPoint3d(0, 0, 0.8)
            self.physics_instance.set_pos(*(self._local_position + offset))
            self.physics_instance.set_quat(LQuaternion(*self._orientation))

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
        self.accept('control-f8', self.toggle_split_merge_debug)
        self.accept('shift-f9', self.toggle_bb)
        self.accept('control-f9', self.toggle_frustum)
        self.accept("f10", self.engine.save_screenshot)
        self.accept("f11", render.ls)
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

class RalphAppConfig:
    def __init__(self):
        self.test_start = False

class RoamingRalphDemo(CosmoniumBase):
    def create_terrain_appearance(self):
        self.terrain_appearance = ProceduralAppearance(self.ralph_config.control, self.ralph_config.appearance, self.heightmap)

    def create_terrain_heightmap(self):
        self.heightmap = ShaderPatchedHeightmap('heightmap',
                                          self.ralph_config.heightmap_data_source,
                                          self.ralph_config.heightmap_size,
                                          -1, 1,
                                          1.0 / self.ralph_config.tile_size, 0.0,
                                          1.0, 1.0,
                                          0,
                                          self.ralph_config.interpolator,
                                          max_lod=self.ralph_config.heightmap_max_lod)

    def create_terrain_biome(self):
        self.biome = ShaderPatchedHeightmap('biome',
                                      self.ralph_config.biome_data_source,
                                      self.ralph_config.biome_size,
                                      -1, 1,
                                      1.0 , 0,
                                      1.0, 1.0,
                                      0,
                                      self.ralph_config.interpolator)

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
        data_source = [HeightmapDataSource(self.heightmap),
                       HeightmapDataSource(self.biome, normals=False),
                       self.terrain_appearance.get_data_source()]
        if settings.hardware_tessellation:
            tessellation_control = ConstantTessellationControl()
        else:
            tessellation_control = None
        self.terrain_shader = BasicShader(appearance=self.terrain_appearance.get_shader_appearance(),
                                          tessellation_control=tessellation_control,
                                          vertex_control=DisplacementVertexControl(self.heightmap),
                                          data_source=data_source)
        self.terrain_shader.add_shadows(ShaderShadowMap('caster', None, self.shadow_caster, use_bias=False))

    def create_tile(self, x, y):
        self.terrain_shape.add_root_patch(x, y)

    def create_terrain(self):
        self.create_terrain_heightmap()
        self.create_terrain_biome()
        self.tile_factory = TileFactory(self.heightmap,
                                        self.ralph_config.tile_density, self.ralph_config.tile_size,
                                        self.ralph_config.height_scale,
                                        self.has_water, self.water,
                                        self.ralph_config.physics.enable, self.physics)
        self.terrain_shape = TiledShape(self.tile_factory,
                                        self.ralph_config.tile_size,
                                        VertexSizeMaxDistancePatchLodControl(self.ralph_config.max_distance / self.ralph_config.tile_size,
                                                                             self.ralph_config.max_vertex_size,
                                                                             density=settings.patch_constant_density,
                                                                             max_lod=self.ralph_config.max_lod))
        self.create_terrain_appearance()
        self.create_terrain_shader()
        self.terrain_object = HeightmapFlatSurface(
                               'surface',
                               0, self.ralph_config.tile_size,
                               self.terrain_shape,
                               self.heightmap,
                               self.biome,
                               self.terrain_appearance,
                               self.terrain_shader,
                               clickable=False,
                               follow_mesh=True)
        self.terrain = CompositeShapeObject()
        self.terrain.add_component(self.terrain_object)
        self.terrain_object.set_parent(self)
        self.terrain.set_owner(self)
        self.terrain.set_parent(self)

    async def create_instance(self):
        await self.terrain.create_instance()
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

    def get_height_under(self, position):
        return self.get_height(position)

    #Used by populator
    def get_height_patch(self, patch, u, v):
        height = self.terrain_object.get_height_patch(patch, u, v)
        if self.has_water and self.water.visible and height < self.water.level:
            height = self.water.level
        return height

    def get_normals_under(self, position):
        return self.terrain_object.get_normals_at(position[0], position[1])

    def get_lonlatvert_under(self, position):
        return self.terrain_object.get_lonlatvert_at(position[0], position[1])

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
        self.ralph.update_shader()

    def get_apparent_radius(self):
        return 0

    def get_min_radius(self):
        return 0

    def get_max_radius(self):
        return 0

    def get_name(self):
        return "terrain"

    def is_emissive(self):
        return False

    def get_local_position(self):
        return LPoint3d()

    def get_sync_rotation(self):
        return LQuaterniond()

    def __init__(self, args):
        self.app_config = RalphAppConfig()
        CosmoniumBase.__init__(self)

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

        self.cam.node().set_camera_mask(BaseObject.DefaultCameraMask | BaseObject.NearCameraMask)
        self.observer = CameraHolder(self.camera, self.camLens)
        self.observer.init()

        self.distance_to_obs = 2.0 #Can not be 0 !
        self._height_under = 0.0
        self.scene_position = LVector3d()
        self.scene_scale_factor = 1
        self.scene_rel_position = LVector3d()
        self.scene_orientation = LQuaternion()
        self.model_body_center_offset = LVector3d()
        self.world_body_center_offset = LVector3d()
        self._local_position = LPoint3d()
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
        self.vector_to_star = -self.skybox.light_dir

        self.vector_to_obs = base.camera.get_pos()
        self.vector_to_obs.normalize()
        if True:
            self.shadow_caster = ShadowMap(1024)
            self.shadow_caster.create()
            self.shadow_caster.set_lens(self.ralph_config.shadow_size, -self.ralph_config.shadow_box_length / 2.0, self.ralph_config.shadow_box_length / 2.0, -self.vector_to_star)
            self.shadow_caster.set_pos(self.vector_to_star * self.ralph_config.shadow_box_length / 2.0)
            self.shadow_caster.snap_cam = True
        else:
            self.shadow_caster = None

        self.ambientLight = AmbientLight("ambientLight")
        self.ambientLight.setColor((settings.global_ambient, settings.global_ambient, settings.global_ambient, 1))
        render.setLight(render.attachNewNode(self.ambientLight))

        base.setFrameRateMeter(True)

        taskMgr.add(self.init())

    async def init(self):
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

        await self.create_instance()
        self.create_tile(0, 0)

        # Create the main character, Ralph

        self.ralph_shape = ActorShape("ralph-data/models/ralph",
                                      {"run": "ralph-data/models/ralph-run",
                                       "walk": "ralph-data/models/ralph-walk"},
                                      auto_scale_mesh=False,
                                      rotation=quaternion_from_euler(180, 0, 0),
                                      scale=(0.2, 0.2, 0.2))
        self.ralph_appearance = ModelAppearance(vertex_color=True, material=False)
        self.ralph_shader = BasicShader()
        self.ralph_shader.add_shadows(ShaderShadowMap('caster', None, self.shadow_caster, use_bias=True))

        self.ralph_shape_object = ShapeObject('ralph', self.ralph_shape, self.ralph_appearance, self.ralph_shader, clickable=False)
        await self.ralph_shape_object.create_instance()
        self.ralph = RalphShip('ralph', self.ralph_shape_object, 1.5, self.ralph_config.physics.enable)
        frame = CartesianSurfaceReferenceFrame(self, LPoint3d())
        self.ralph.set_frame(frame)
        self.ralph.create_own_shadow_caster = False

        self.camera_controller = SurfaceFollowCameraController()
        #self.camera_controller = FixedCameraController()
        self.camera_controller.activate(self.observer, self.ralph)
        self.camera_controller.set_body(self)
        self.camera_controller.set_camera_hints(distance=5, max=1.5)

        self.controller = RalphControl(self.skybox, self)
        self.controller.register_events()

        self.mover = ShipSurfaceBodyMover(self.ralph)
        self.mover.activate()
        self.nav = ControlNav()
        self.nav.set_controller(self.mover)
        self.nav.register_events(self)
        self.nav.speed = 25
        self.nav.rot_step_per_sec = 2

        #TEMPORARY
        self.ralph.update(0, 0)
        self.camera_controller.update(0, 0)
        self.mover.update()
        self.ralph.update_obs(self.observer)
        self.ralph.check_visibility(self.observer.pixel_size)
        self.ralph.check_and_update_instance(self.observer.get_camera_pos(), self.observer.get_camera_rot(), None)
        self.ralph.create_light()
        if self.ralph_config.physics.enable:
            for physic_object in self.physic_objects:
                physic_object.update(self.observer)

        # Set up the camera
        self.distance_to_obs = self.camera.get_z() - self.get_height(self.camera.getPos())
        render.set_shader_input("camera", self.camera.get_pos())

        self.terrain.update_instance(self.observer.get_camera_pos(), None)

        taskMgr.add(self.move, "moveTask")

    def move(self, task):
        dt = globalClock.getDt()

        if self.trigger_check_settings:
            self.terrain.check_settings()
            self.trigger_check_settings = False

        self.nav.update(0, dt)
        self.ralph.update(0, dt)
        self.terrain.update(0, dt)
        self.camera_controller.update(0, dt)
        self.controller.update(0, dt)
        self.mover.update()

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
        self.vector_to_star = -self.skybox.light_dir
        if self.shadow_caster is not None:
            self.shadow_caster.set_direction(-self.vector_to_star)
        if False and self.directionalLight is not None:
            self.directionalLight.setDirection(-self.vector_to_star)

        if self.shadow_caster is not None:
            vec = self.ralph_shape.instance.getPos() - self.camera.getPos()
            vec.set_z(0)
            dist = vec.length()
            vec.normalize()
            self.shadow_caster.set_pos(self.ralph_shape.instance.get_pos() - vec * dist + vec * self.ralph_config.shadow_size / 2)

        render.set_shader_input("camera", self.camera.get_pos())
        self.vector_to_obs = self.camera.get_pos()
        self.vector_to_obs.normalize()
        self.distance_to_obs = self.observer._local_position.get_z()# - self.get_height(self.observer._local_position)
        self._local_position = LPoint3d()
        self._height_under = self.get_height_under(self.observer._local_position)
        self.rel_position = self._local_position - self.observer._local_position
        self.scene_rel_position = self.rel_position
        if settings.camera_at_origin:
            self.scene_position = self.scene_rel_position
        else:
            self.scene_position = LPoint3d()

        self.ralph.update_obs(self.observer)
        self.terrain.update_obs(self.observer)
        self.ralph.check_visibility(self.observer.pixel_size)
        self.ralph.check_and_update_instance(self.observer.get_camera_pos(), self.observer.get_camera_rot(), None)
        self.terrain.update_instance(self.observer.get_camera_pos(), None)

        return task.cont

    def print_debug(self):
        print("Height:", self.get_height(self.ralph._local_position),
              self.terrain_object.get_height_at(self.ralph._local_position[0], self.ralph._local_position[1]))
        print("Ralph:", self.ralph._local_position, self.ralph._frame_position, self.ralph._frame_rotation.get_hpr(), self.ralph._orientation.get_hpr())
        print("Camera:", self.observer._local_position, self.observer._orientation.get_hpr(), self.distance_to_obs)

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
