#!/usr/bin/env python

# Author: Ryan Myers
# Models: Jeff Styers, Reagan Heller
#
# Last Updated: 2015-03-13
#
# This tutorial provides an example of creating a character
# and having it walk around on uneven terrain, as well
# as implementing a fully rotatable camera.

from __future__ import print_function

from panda3d.core import AmbientLight, DirectionalLight, LPoint3, LVector3, LRGBColor, LQuaternion, LColor
from panda3d.core import LPoint3d, LQuaterniond
from panda3d.core import PandaNode, NodePath
from panda3d.core import CollisionTraverser, CollisionNode, CollideMask
from panda3d.core import CollisionHandlerQueue, CollisionRay
from direct.actor.Actor import Actor

from cosmonium.procedural.shaders import HeightmapDataSource, TextureDictionaryDataSource
from cosmonium.procedural.shaders import DetailMap, DisplacementGeometryControl
from cosmonium.procedural.water import WaterNode
from cosmonium.appearances import ModelAppearance
from cosmonium.shaders import BasicShader, Fog, GeometryControl, ConstantTesselationControl
from cosmonium.shapes import MeshShape, InstanceShape
from cosmonium.surfaces import HeightmapSurface
from cosmonium.tiles import Tile, TiledShape, GpuPatchTerrainLayer, MeshTerrainLayer
from cosmonium.procedural.textures import PatchedGpuTextureSource
from cosmonium.procedural.terrain import TerrainObject
from cosmonium.procedural.populator import CpuTerrainPopulator, GpuTerrainPopulator, RandomObjectPlacer, MultiTerrainPopulator, TerrainObjectFactory
from cosmonium.procedural.heightmap import PatchedHeightmap
from cosmonium.procedural.shaderheightmap import ShaderHeightmapPatchFactory
from cosmonium.patchedshapes import VertexSizeMaxDistancePatchLodControl
from cosmonium.shadows import ShadowCaster
from cosmonium.parsers.yamlparser import YamlModuleParser
from cosmonium.parsers.noiseparser import NoiseYamlParser
from cosmonium.parsers.textureparser import TextureControlYamlParser, HeightColorControlYamlParser, TextureDictionaryYamlParser
from cosmonium import settings

from math import pow, pi, sqrt
import sys
from cosmonium.procedural.shadernoise import NoiseMap
from cosmonium.cosmonium import CosmoniumBase
from cosmonium.camera import CameraBase
from cosmonium.nav import NavBase
from cosmonium.astro.frame import AbsoluteReferenceFrame

class TreeAnimControl(GeometryControl):
    def get_id(self):
        return "tree"

    def vertex_uniforms(self, code):
        code.append("uniform float osg_FrameTime;")

    def update_vertex(self, code):
        code.append("    float isBark = step(0.251, model_texcoord0.y);")
        code.append("    float animation = sin(osg_FrameTime);")
        code.append("    animation *= sin(0.5 * osg_FrameTime);")
        code.append("    animation *= isBark;")
        code.append("    animation *= distance(model_vertex4.xy, vec2(0.0,0.0)) * 0.04;")
        code.append("    model_vertex4 = vec4(model_vertex4.xyz + animation, model_vertex4.w);")

class RockFactory(TerrainObjectFactory):
    def __init__(self, terrain):
        self.terrain = terrain

    def create_object(self):
        rock_shape = MeshShape('ralph-data/models/rock1', panda=True, scale=False)
        rock_appearance = ModelAppearance()
        if self.terrain.fog is not None:
            after_effects = [Fog(**self.terrain.fog)]
        else:
            after_effects = None
        rock_shader = BasicShader(after_effects=after_effects)
        rock = TerrainObject(shape=rock_shape, appearance=rock_appearance, shader=rock_shader)
        rock.set_parent(self.terrain)
        #bounds = self.rock.instance.getTightBounds()
        #offset = (bounds[1] - bounds[0]) / 2
        #offsets[count] = Vec4F(x, y, height - offset[2] * scale, scale)
        return rock

class TreeFactory(TerrainObjectFactory):
    def __init__(self, terrain):
        self.terrain = terrain

    def create_object(self):
        tree_shape = MeshShape('ralph-data/models/trees/tree1', panda=True, scale=False)
        tree_appearance = ModelAppearance()
        if self.terrain.fog is not None:
            after_effects = [Fog(**self.terrain.fog)]
        else:
            after_effects = None
        tree_shader = BasicShader(geometry_control=TreeAnimControl(), after_effects=after_effects)
        tree = TerrainObject(shape=tree_shape, appearance = tree_appearance, shader=tree_shader)
        tree.set_parent(self.terrain)
        return tree

class TileFactory(object):
    def __init__(self, tile_density, size, height_scale, has_water, water):
        self.tile_density = tile_density
        self.size = size
        self.height_scale = height_scale
        self.has_water = has_water
        self.water = water

    def create_patch(self, parent, lod, x, y):
        patch = Tile(parent, lod, x, y, self.tile_density, self.size, self.height_scale)
        #print("Create tile", lod, x, y, tile.size, tile.flat_coord)
        if settings.allow_tesselation:
            terrain_layer = GpuPatchTerrainLayer()
        else:
            terrain_layer = MeshTerrainLayer()
        patch.add_layer(terrain_layer)
        if self.has_water:
            patch.add_layer(WaterLayer(self.water))
        return patch

class WaterLayer(object):
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
        self.water = WaterNode(-0.5, -0.5, 0.5, 0.5, self.config.level, self.config.scale, patch)
        if self.config.visible:
            self.water.create_instance()

    def update_instance(self, patch):
        pass

    def remove_instance(self):
        if self.water is not None:
            self.water.remove_instance()
            self.water = None

class WaterConfig():
    def __init__(self, level, visible, scale):
        self.level = level
        self.visible = visible
        self.scale = scale

class RalphConfigParser(YamlModuleParser):
    def decode(self, data):
        biome = data.get('biome', None)
        control = data.get('control', None)
        appearance = data.get('appearance', None)
        water = data.get('water', None)
        fog = data.get('fog', None)

        terrain = data.get('terrain', {})
        self.tile_size = terrain.get("tile-size", 1024)
        self.tile_density = terrain.get('tile-density', 64)
        self.max_vertex_size = terrain.get('max-vertex-size', 64)
        self.max_lod = terrain.get('max-lod', 10)
        self.max_distance = terrain.get('max-distance', 1.001 * 1024 * sqrt(2))
        self.heightmap_size = terrain.get('heightmap-size', 512)
        self.biome_size = terrain.get('biome-size', 128)
        #self.objects_density = int(25 * (1.0 * self.size / self.default_size) * (1.0 * self.size / self.default_size))
        self.objects_density = terrain.get('object-density', 250)

        heightmap = data.get('heightmap', {})
        self.height_scale = heightmap.get('scale', 1.0)
        scale_length = heightmap.get('scale-length', 1)
        scale_length = scale_length * self.tile_size
        noise = heightmap.get('noise')
        scale_noise = heightmap.get('scale-noise', True)
        median = heightmap.get('median', True)
        #filtering = self.decode_filtering(heightmap.get('filter', 'none'))
        if scale_noise:
            noise_scale = 1.0 / self.height_scale
        else:
            noise_scale = 1.0
        noise_parser = NoiseYamlParser(noise_scale, scale_length)
        self.heightmap = noise_parser.decode(noise)

        self.shadow_size = terrain.get('shadow-size', 16)
        self.shadow_box_length = terrain.get('shadow-depth', self.height_scale)

        if biome is not None:
            self.biome = noise_parser.decode(biome)
        else:
            self.biome = None

        if control is not None:
            control_type = control.get('type', 'textures')
            if control_type == 'textures':
                control_parser = TextureControlYamlParser()
                self.control = control_parser.decode(control)
            elif control_type == 'colormap':
                control_parser = HeightColorControlYamlParser()
                self.control = control_parser.decode(control, self.height_scale)
            else:
                print("Unknown control type '%'" % control_type)
                self.control = None
        else:
            self.control = None

        if appearance is not None:
            appearance_parser = TextureDictionaryYamlParser()
            self.appearance = appearance_parser.decode(appearance)
        else:
            self.appearance = None

        if water is not None:
            level = water.get('level', 0)
            visible = water.get('visible', False)
            scale = 8.0 #* self.size / self.default_size
            self.water = WaterConfig(level, visible, scale)
        else:
            self.water = WaterConfig(0, False, 1.0)
        if False and fog is not None:
            self.fog_parameters = {}
            self.fog_parameters['fall_off'] = fog.get('falloff', 0.035)
            self.fog_parameters['density'] = fog.get('density', 20)
            self.fog_parameters['ground'] = fog.get('ground', -500)
        else:
            self.fog_parameters = None

class NodePathHolder(object):
    def __init__(self, instance):
        self.instance = instance

    def get_rel_position_to(self, position):
        return LPoint3d(*self.instance.get_pos(render))

class RalphCamera(CameraBase):
    def __init__(self, cam, lens):
        CameraBase.__init__(self, cam, lens)
        self.camera_global_pos = LPoint3d()
        self.camera_frame = AbsoluteReferenceFrame()

    def get_frame_camera_pos(self):
        return LPoint3d(*base.cam.get_pos())

    def set_frame_camera_pos(self, position):
        base.cam.set_pos(*position)

    def get_frame_camera_rot(self):
        return LQuaterniond(*base.cam.get_quat())

    def set_frame_camera_rot(self, rot):
        base.cam.set_quat(LQuaternion(*rot))

    def set_camera_pos(self, position):
        base.cam.set_pos(*position)

    def get_camera_pos(self):
        return LPoint3d(*base.cam.get_pos())

    def set_camera_rot(self, rot):
        base.cam.set_quat(LQuaternion(*rot))

    def get_camera_rot(self):
        return LQuaterniond(*base.cam.get_quat())

class FollowCam(object):
    def __init__(self, terrain, cam, target, floater):
        self.terrain = terrain
        self.cam = cam
        self.target = target
        self.floater = floater
        self.height = 2.0
        self.min_height = 1.0
        self.max_dist = 10.0
        self.min_dist = 5.0
        self.cam.setPos(self.target.getX(), self.target.getY() + self.max_dist, self.height)

    def set_limits(self, min_dist, max_dist):
        self.min_dist = min_dist
        self.max_dist = max_dist

    def set_height(self, height):
        self.height = max(height, self.min_height)

    def scale_height(self, scale):
        self.height = max(self.min_height, self.height * scale)

    def update(self):
        vec = self.target.getPos() - self.cam.getPos()
        vec.setZ(0)
        dist = vec.length()
        vec.normalize()
        if dist > self.max_dist:
            self.cam.setPos(self.cam.getPos() + vec * (dist - self.max_dist))
            dist = self.max_dist
        if dist < self.min_dist:
            self.cam.setPos(self.cam.getPos() - vec * (self.min_dist - dist))
            dist = self.min_dist

        # Keep the camera at min_height above the terrain,
        # or camera_height above target, whichever is greater.
        terrain_height = self.terrain.get_height(self.cam.getPos())
        target_height = self.target.get_z()
        if terrain_height + self.min_height < target_height + self.height:
            new_camera_height = target_height + self.height
        else:
            new_camera_height = terrain_height + self.min_height
        self.cam.setZ(new_camera_height)

        # The camera should look in ralph's direction,
        # but it should also try to stay horizontal, so look at
        # a floater which hovers above ralph's head.
        self.cam.lookAt(self.floater)

class RalphNav(NavBase):
    def __init__(self, ralph, target, cam, observer, sun, follow):
        NavBase.__init__(self)
        self.ralph = ralph
        self.target = target
        self.cam = cam
        self.observer = observer
        self.sun = sun
        self.follow = follow
        self.isMoving = False
        self.mouseSelectClick = False

    def register_events(self, event_ctrl):
        self.keyMap = {
            "left": 0, "right": 0, "forward": 0, "backward": 0,
            "cam-left": 0, "cam-right": 0, "cam-up": 0, "cam-down": 0,
            "sun-left": 0, "sun-right": 0,
            "turbo": 0}
        event_ctrl.accept("arrow_left", self.setKey, ["left", True])
        event_ctrl.accept("arrow_right", self.setKey, ["right", True])
        event_ctrl.accept("arrow_up", self.setKey, ["forward", True])
        event_ctrl.accept("arrow_down", self.setKey, ["backward", True])
        event_ctrl.accept("shift", self.setKey, ["turbo", True])
        event_ctrl.accept("a", self.setKey, ["cam-left", True], direct=True)
        event_ctrl.accept("s", self.setKey, ["cam-right", True], direct=True)
        event_ctrl.accept("u", self.setKey, ["cam-up", True], direct=True)
        event_ctrl.accept("u-up", self.setKey, ["cam-up", False])
        event_ctrl.accept("d", self.setKey, ["cam-down", True], direct=True)
        event_ctrl.accept("d-up", self.setKey, ["cam-down", False])
        event_ctrl.accept("o", self.setKey, ["sun-left", True], direct=True)
        event_ctrl.accept("o-up", self.setKey, ["sun-left", False])
        event_ctrl.accept("p", self.setKey, ["sun-right", True], direct=True)
        event_ctrl.accept("p-up", self.setKey, ["sun-right", False])
        event_ctrl.accept("arrow_left-up", self.setKey, ["left", False])
        event_ctrl.accept("arrow_right-up", self.setKey, ["right", False])
        event_ctrl.accept("arrow_up-up", self.setKey, ["forward", False])
        event_ctrl.accept("arrow_down-up", self.setKey, ["backward", False])
        event_ctrl.accept("shift-up", self.setKey, ["turbo", False])
        event_ctrl.accept("a-up", self.setKey, ["cam-left", False])
        event_ctrl.accept("s-up", self.setKey, ["cam-right", False])

        event_ctrl.accept("mouse1", self.OnSelectClick )
        event_ctrl.accept("mouse1-up", self.OnSelectRelease )

        if settings.invert_wheel:
            event_ctrl.accept("wheel_up", self.change_distance, [0.1])
            event_ctrl.accept("wheel_down", self.change_distance, [-0.1])
        else:
            event_ctrl.accept("wheel_up", self.change_distance, [-0.1])
            event_ctrl.accept("wheel_down", self.change_distance, [0.1])

    def remove_events(self, event_ctrl):
        NavBase.remove_events(self, event_ctrl)

    def OnSelectClick(self):
        if base.mouseWatcherNode.hasMouse():
            self.mouseSelectClick = True
            mpos = base.mouseWatcherNode.getMouse()
            self.startX = mpos.getX()
            self.startY = mpos.getY()
            self.dragAngleX = pi
            self.dragAngleY = pi
            self.create_drag_params(self.target)

    def OnSelectRelease(self):
        if base.mouseWatcherNode.hasMouse():
            mpos = base.mouseWatcherNode.getMouse()
            if self.startX == mpos.getX() and self.startY == mpos.getY():
                pass
        self.mouseSelectClick = False

    def change_distance(self, step):
        camvec = self.ralph.getPos() - self.cam.getPos()
        camdist = camvec.length()
        camvec.normalize()
        new_dist = max(5.0, camdist * (1.0 + step))
        self.follow.set_limits(new_dist / 2.0, new_dist)
        self.cam.set_pos(self.ralph.getPos() - camvec * new_dist)

    def update(self, dt):
        if self.mouseSelectClick and base.mouseWatcherNode.hasMouse():
            mpos = base.mouseWatcherNode.getMouse()
            deltaX = mpos.getX() - self.startX
            deltaY = mpos.getY() - self.startY
            z_angle = -deltaX * self.dragAngleX
            x_angle = deltaY * self.dragAngleY
            self.do_drag(z_angle, x_angle, move=True, rotate=False)
            self.follow.set_height(self.cam.get_z() - self.ralph.get_z())
            return True

        if self.keyMap["cam-left"]:
            self.cam.setX(self.cam, -20 * dt)
        if self.keyMap["cam-right"]:
            self.cam.setX(self.cam, +20 * dt)
        if self.keyMap["cam-up"]:
            self.follow.scale_height(1 + 2 * dt)
        if self.keyMap["cam-down"]:
            self.follow.scale_height(1 - 2 * dt)

        if self.keyMap["sun-left"]:
            self.sun.set_light_angle(self.sun.light_angle + 30 * dt)
        if self.keyMap["sun-right"]:
            self.sun.set_light_angle(self.sun.light_angle - 30 * dt)

        delta = 25
        if self.keyMap["turbo"]:
            delta *= 10
        if self.keyMap["left"]:
            self.ralph.setH(self.ralph.getH() + 300 * dt)
        if self.keyMap["right"]:
            self.ralph.setH(self.ralph.getH() - 300 * dt)
        if self.keyMap["forward"]:
            self.ralph.setY(self.ralph, -delta * dt)
        if self.keyMap["backward"]:
            self.ralph.setY(self.ralph, delta * dt)

        if self.keyMap["forward"] or self.keyMap["backward"] or self.keyMap["left"] or self.keyMap["right"]:
            if self.isMoving is False:
                self.ralph.loop("run")
                self.isMoving = True
        else:
            if self.isMoving:
                self.ralph.stop()
                self.ralph.pose("walk", 5)
                self.isMoving = False
        return False

class RalphSplash():
    def set_text(self, text):
        pass

class RoamingRalphDemo(CosmoniumBase):

    def get_local_position(self):
        return base.cam.get_pos()

    def create_terrain_appearance(self):
        self.terrain_appearance = self.ralph_config.appearance
        self.terrain_appearance.set_shadow(self.shadow_caster)

    def create_terrain_heightmap(self):
        self.heightmap = PatchedHeightmap('heightmap',
                                          self.ralph_config.heightmap_size,
                                          self.ralph_config.height_scale,
                                          self.ralph_config.tile_size,
                                          self.ralph_config.tile_size,
                                          True,
                                          ShaderHeightmapPatchFactory(self.ralph_config.heightmap))

    def create_terrain_biome(self):
        self.biome = PatchedHeightmap('biome',
                                      self.ralph_config.biome_size,
                                      1.0,
                                      self.ralph_config.tile_size,
                                      self.ralph_config.tile_size,
                                      False,
                                      ShaderHeightmapPatchFactory(self.ralph_config.biome))

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
        appearance = DetailMap(self.ralph_config.control, self.heightmap, create_normals=True)
        data_source = [HeightmapDataSource(self.heightmap, PatchedGpuTextureSource, filtering=HeightmapDataSource.F_none),
                       HeightmapDataSource(self.biome, PatchedGpuTextureSource, filtering=HeightmapDataSource.F_none),
                       TextureDictionaryDataSource(self.terrain_appearance, TextureDictionaryDataSource.F_hash)]
        if settings.allow_tesselation:
            tesselation_control = ConstantTesselationControl(invert_v=False)
        else:
            tesselation_control = None
        if self.fog is not None:
            after_effects = [Fog(**self.fog)]
        else:
            after_effects = None
        self.terrain_shader = BasicShader(appearance=appearance,
                                          tesselation_control=tesselation_control,
                                          geometry_control=DisplacementGeometryControl(self.heightmap),
                                          data_source=data_source,
                                          after_effects=after_effects)

    def create_tile(self, x, y):
        self.terrain_shape.add_root_patch(x, y)

    def create_terrain(self):
        self.tile_factory = TileFactory(self.ralph_config.tile_density, self.ralph_config.tile_size, self.ralph_config.height_scale, self.has_water, self.water)
        self.terrain_shape = TiledShape(self.tile_factory,
                                        self.ralph_config.tile_size,
                                        VertexSizeMaxDistancePatchLodControl(self.ralph_config.max_distance,
                                                                             self.ralph_config.max_vertex_size,
                                                                             max_lod=self.ralph_config.max_lod))
        self.create_terrain_heightmap()
        self.create_terrain_biome()
        self.create_terrain_appearance()
        self.create_terrain_shader()
        self.terrain = HeightmapSurface(
                               'surface',
                               0,
                               self.terrain_shape,
                               self.heightmap,
                               self.biome,
                               self.terrain_appearance,
                               self.terrain_shader,
                               self.ralph_config.tile_size,
                               clickable=False,
                               average=True)
        self.terrain.set_parent(self)
        self.terrain.create_instance()
        if self.has_water:
            WaterNode.create_cam()

    def toggle_water(self):
        if not self.has_water: return
        self.water.visible = not self.water.visible
        if self.water.visible:
            WaterNode.create_cam()
        else:
            WaterNode.remove_cam()
        self.terrain_shape.check_settings()

    def get_height(self, position):
        height = self.terrain.get_height(position)
        if self.has_water and self.water.visible and height < self.water.level:
            height = self.water.level
        return height

    #Used by populator
    def get_height_patch(self, patch, u, v):
        height = self.terrain.get_height_patch(patch, u, v)
        if self.has_water and self.water.visible and height < self.water.level:
            height = self.water.level
        return height

    def skybox_init(self):
        skynode = base.cam.attachNewNode('skybox')
        self.skybox = loader.loadModel('ralph-data/models/rgbCube')
        self.skybox.reparentTo(skynode)

        self.skybox.setTextureOff(1)
        self.skybox.setShaderOff(1)
        self.skybox.setTwoSided(True)
        # make big enough to cover whole terrain, else there'll be problems with the water reflections
        self.skybox.setScale(1.5 * self.ralph_config.tile_size)
        self.skybox.setBin('background', 1)
        self.skybox.setDepthWrite(False)
        self.skybox.setDepthTest(False)
        self.skybox.setLightOff(1)
        self.skybox.setShaderOff(1)
        self.skybox.setFogOff(1)

        #self.skybox.setColor(.55, .65, .95, 1.0)
        self.skybox_color = LColor(pow(0.5, 1/2.2), pow(0.6, 1/2.2), pow(0.7, 1/2.2), 1.0)
        self.skybox.setColor(self.skybox_color)

    def objects_density_for_patch(self, patch):
        scale = 1 << patch.lod
        return int(self.ralph_config.objects_density / scale + 1.0)

    def create_populator(self):
        if settings.allow_instancing:
            TerrainPopulator = GpuTerrainPopulator
        else:
            TerrainPopulator = CpuTerrainPopulator
        self.rock_collection = TerrainPopulator(RockFactory(self), self.objects_density_for_patch, self.ralph_config.objects_density, RandomObjectPlacer(self))
        self.tree_collection = TerrainPopulator(TreeFactory(self), self.objects_density_for_patch, self.ralph_config.objects_density, RandomObjectPlacer(self))
        self.object_collection = MultiTerrainPopulator()
        self.object_collection.add_populator(self.rock_collection)
        self.object_collection.add_populator(self.tree_collection)

    def set_light_angle(self, angle):
        self.light_angle = angle
        self.light_quat.setFromAxisAngleRad(angle * pi / 180, LVector3.forward())
        self.light_dir = self.light_quat.xform(LVector3.up())
        cosA = self.light_dir.dot(LVector3.up())
        self.vector_to_star = self.light_dir
        if self.shadow_caster is not None:
            self.shadow_caster.set_direction(-self.light_dir)
        if self.directionalLight is not None:
            self.directionalLight.setDirection(-self.light_dir)
        if cosA >= 0:
            coef = sqrt(cosA)
            self.light_color = (1, coef, coef, 1)
            self.directionalLight.setColor(self.light_color)
            self.skybox.setColor(self.skybox_color * cosA)
        else:
            self.light_color = (1, 0, 0, 1)
            self.directionalLight.setColor(self.light_color)
            self.skybox.setColor(self.skybox_color * 0)
        self.update()

    def update(self):
        self.object_collection.update_instance()
        self.terrain.update_instance(None, None)

    def apply_instance(self, instance):
        pass

    def create_instance_delayed(self):
        pass

    def get_apparent_radius(self):
        return 0

    def get_name(self):
        return "terrain"

    def is_emissive(self):
        return False

    def toggle_lod_freeze(self):
        settings.debug_lod_freeze = not settings.debug_lod_freeze

    def toggle_split_merge_debug(self):
        settings.debug_lod_split_merge = not settings.debug_lod_split_merge

    def __init__(self):
        CosmoniumBase.__init__(self)

        self.config_file = 'ralph-data/ralph.yaml'
        self.splash = RalphSplash()
        self.ralph_config = RalphConfigParser()
        self.ralph_config.load_and_parse(self.config_file)
        self.water = self.ralph_config.water
        self.fog = self.ralph_config.fog_parameters

        self.has_water = True
        self.fullscreen = False
        self.shadow_caster = None
        self.light_angle = None
        self.light_dir = LVector3.up()
        self.vector_to_star = self.light_dir
        self.light_quat = LQuaternion()
        self.light_color = (1.0, 1.0, 1.0, 1.0)
        self.directionalLight = None

        self.observer = RalphCamera(self.cam, self.camLens)
        self.observer.init()

        self.distance_to_obs = 0.0
        self.height_under = 0.0
        self.scene_position = LVector3()
        self.scene_scale_factor = 1
        self.scene_rel_position = LVector3()
        self.scene_orientation = LQuaternion()
        self.context = self
        self.size = self.ralph_config.tile_size #TODO: Needed by populator

        #Size of an edge seen from 4 units above
        self.edge_apparent_size = (1.0 * self.ralph_config.tile_size / self.ralph_config.tile_density) / (4.0 * self.observer.pixel_size)
        print("Apparent size:", self.edge_apparent_size)

        self.win.setClearColor((135.0/255, 206.0/255, 235.0/255, 1))


        # Set up the environment
        #
        # Create some lighting
        self.vector_to_obs = base.cam.get_pos()
        self.vector_to_obs.normalize()
        if True:
            self.shadow_caster = ShadowCaster(1024)
            self.shadow_caster.create()
            self.shadow_caster.set_lens(self.ralph_config.shadow_size, -self.ralph_config.shadow_box_length / 2.0, self.ralph_config.shadow_box_length / 2.0, -self.light_dir)
            self.shadow_caster.set_pos(self.light_dir * self.ralph_config.shadow_box_length / 2.0)
            self.shadow_caster.bias = 0.1
        else:
            self.shadow_caster = None

        self.ambientLight = AmbientLight("ambientLight")
        self.ambientLight.setColor((settings.global_ambient, settings.global_ambient, settings.global_ambient, 1))
        self.directionalLight = DirectionalLight("directionalLight")
        self.directionalLight.setDirection(-self.light_dir)
        self.directionalLight.setColor(self.light_color)
        self.directionalLight.setSpecularColor(self.light_color)
        render.setLight(render.attachNewNode(self.ambientLight))
        render.setLight(render.attachNewNode(self.directionalLight))

        render.setShaderAuto()
        base.setFrameRateMeter(True)

        self.create_terrain()
        self.create_populator()
        self.terrain_shape.set_populator(self.object_collection)
        self.create_tile(0, 0)
        self.skybox_init()

        self.set_light_angle(45)

        # Create the main character, Ralph

        ralphStartPos = LPoint3()
        self.ralph = Actor("ralph-data/models/ralph",
                           {"run": "ralph-data/models/ralph-run",
                            "walk": "ralph-data/models/ralph-walk"})
        self.ralph.reparentTo(render)
        self.ralph.setScale(.2)
        self.ralph.setPos(ralphStartPos + (0, 0, 0.5))
        self.ralph_shape = InstanceShape(self.ralph)
        self.ralph_shape.parent = self
        self.ralph_shape.set_owner(self)
        self.ralph_shape.create_instance()
        self.ralph_appearance = ModelAppearance(self.ralph)
        self.ralph_appearance.set_shadow(self.shadow_caster)
        self.ralph_shader = BasicShader()
        self.ralph_appearance.bake()
        self.ralph_appearance.apply(self.ralph_shape, self.ralph_shader)
        self.ralph_shader.apply(self.ralph_shape, self.ralph_appearance)
        self.ralph_shader.update(self.ralph_shape, self.ralph_appearance)

        # Create a floater object, which floats 2 units above ralph.  We
        # use this as a target for the camera to look at.

        self.floater = NodePath(PandaNode("floater"))
        self.floater.reparentTo(self.ralph)
        self.floater.setZ(2.0)

        self.ralph_body = NodePathHolder(self.ralph)
        self.ralph_floater = NodePathHolder(self.floater)

        self.follow_cam = FollowCam(self, self.cam, self.ralph, self.floater)

        self.nav = RalphNav(self.ralph, self.ralph_floater, self.cam, self.observer, self, self.follow_cam)
        self.nav.register_events(self)

        self.accept("escape", sys.exit)
        self.accept("control-q", sys.exit)
        self.accept("w", self.toggle_water)
        self.accept("h", self.print_debug)
        self.accept("f2", self.connect_pstats)
        self.accept("f3", self.toggle_filled_wireframe)
        self.accept("shift-f3", self.toggle_wireframe)
        self.accept("f5", self.bufferViewer.toggleEnable)
        self.accept('f8', self.toggle_lod_freeze)
        self.accept("shift-f8", self.terrain_shape.dump_tree)
        self.accept('control-f8', self.toggle_split_merge_debug)
        self.accept("f10", self.save_screenshot)
        self.accept('alt-enter', self.toggle_fullscreen)

        taskMgr.add(self.move, "moveTask")

        # Set up the camera
        self.follow_cam.update()
        self.distance_to_obs = self.cam.get_z() - self.get_height(self.cam.getPos())
        render.set_shader_input("camera", self.cam.get_pos())

        self.terrain.update_instance(LPoint3d(*self.cam.getPos()), None)

    def move(self, task):
        dt = globalClock.getDt()

        control = self.nav.update(dt)

        ralph_height = self.get_height(self.ralph.getPos())
        self.ralph.setZ(ralph_height)

        if not control:
            self.follow_cam.update()
        else:
            #TODO: Should have a FreeCam class for mouse orbit and this in update()
            self.cam.lookAt(self.floater)

        if self.shadow_caster is not None:
            vec = self.ralph.getPos() - self.cam.getPos()
            vec.set_z(0)
            dist = vec.length()
            vec.normalize()
            self.shadow_caster.set_pos(self.ralph.get_pos() - vec * dist + vec * self.ralph_config.shadow_size / 2)

        render.set_shader_input("camera", self.cam.get_pos())
        self.vector_to_obs = base.cam.get_pos()
        self.vector_to_obs.normalize()
        self.distance_to_obs = self.cam.get_z() - self.get_height(self.cam.getPos())
        self.scene_rel_position = -base.cam.get_pos()

        self.object_collection.update_instance()
        self.terrain.update_instance(LPoint3d(*self.cam.getPos()), None)
        return task.cont

    def print_debug(self):
        print("Height:", self.get_height(self.ralph.getPos()), self.terrain.get_height(self.ralph.getPos()))
        print("Ralph:", self.ralph.get_pos())
        print("Camera:", base.cam.get_pos(), self.follow_cam.height, self.distance_to_obs)
demo = RoamingRalphDemo()
demo.run()
