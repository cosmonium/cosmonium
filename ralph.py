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

from panda3d.core import AmbientLight, DirectionalLight, LPoint3, LVector3, LRGBColor, LQuaternion, LPoint3d,\
    LColor
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
from cosmonium.parsers.textureparser import TextureControlYamlParser, TextureDictionaryYamlParser
from cosmonium import settings

from math import pow, pi, sqrt
import sys
from cosmonium.procedural.shadernoise import NoiseMap
from cosmonium.cosmonium import CosmoniumBase
from cosmonium.camera import CameraBase

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
    def __init__(self, tile_density, size, has_water, water):
        self.tile_density = tile_density
        self.size = size
        self.has_water = has_water
        self.water = water

    def create_patch(self, parent, lod, x, y):
        patch = Tile(parent, lod, x, y, self.tile_density, self.size)
        #print("Create tile", lod, x, y, tile.size, tile.flat_coord)
        if settings.allow_tesselation:
            TerrainLayer = GpuPatchTerrainLayer
        else:
            TerrainLayer = MeshTerrainLayer
        patch.add_layer(TerrainLayer())
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
        noise_parser = NoiseYamlParser()
        heightmap = data.get('heightmap', None)
        biome = data.get('biome', None)
        control = data.get('control', None)
        appearance = data.get('appearance', None)
        water = data.get('water', None)
        fog = data.get('fog', None)
        if  heightmap is not None:
            heightmap = noise_parser.decode(heightmap)
        if biome is not None:
            biome = noise_parser.decode(biome)
        if control is not None:
            control_parser = TextureControlYamlParser()
            control = control_parser.decode(control)
        if appearance is not None:
            appearance_parser = TextureDictionaryYamlParser()
            appearance = appearance_parser.decode(appearance)
        if water is not None:
            level = water.get('level', 0)
            visible = water.get('visible', True)
            scale = 8.0 #* self.size / self.default_size
            water = WaterConfig(level, visible, scale)
        else:
            water = WaterConfig(0, False, 1.0)
        if fog is not None:
            fog_parameters = {}
            fog_parameters['fall_off'] = fog.get('falloff', 0.035)
            fog_parameters['density'] = fog.get('density', 20)
            fog_parameters['ground'] = fog.get('ground', -500)
        else:
            fog_parameters = None
        return (heightmap, biome, control, appearance, water, fog_parameters)

class RalphCamera(CameraBase):
    def set_camera_pos(self, position):
        base.cam.set_pos(*position)

    def get_camera_pos(self):
        return LPoint3d(*base.cam.get_pos())

class RalphSplash():
    def set_text(self, text):
        pass

class RoamingRalphDemo(CosmoniumBase):

    def get_local_position(self):
        return base.cam.get_pos()

    def create_terrain_appearance(self):
        self.terrain_appearance.set_shadow(self.shadow_caster)

    def create_terrain_heightmap(self):
        self.heightmap = PatchedHeightmap('heightmap',
                                          self.noise_size,
                                          self.height_scale,
                                          self.size,
                                          self.size,
                                          True,
                                          ShaderHeightmapPatchFactory(self.noise))

    def create_terrain_biome(self):
        self.biome = PatchedHeightmap('biome',
                                      self.biome_size,
                                      1.0,
                                      self.size,
                                      self.size,
                                      False,
                                      ShaderHeightmapPatchFactory(self.biome_noise))

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
        appearance = DetailMap(self.terrain_control, self.heightmap, create_normals=True)
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
        self.tile_factory = TileFactory(self.tile_density, self.size, self.has_water, self.water)
        self.terrain_shape = TiledShape(self.tile_factory, self.size, self.max_lod, lod_control=VertexSizeMaxDistancePatchLodControl(self.max_distance, self.max_vertex_size))
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
                               self.size,
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
        self.skybox.setScale(1.5* self.size)
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
        return int(self.objects_density / scale + 1.0)

    def create_populator(self):
        if settings.allow_instancing:
            TerrainPopulator = GpuTerrainPopulator
        else:
            TerrainPopulator = CpuTerrainPopulator
        self.rock_collection = TerrainPopulator(RockFactory(self), self.objects_density_for_patch, self.objects_density, RandomObjectPlacer(self))
        self.tree_collection = TerrainPopulator(TreeFactory(self), self.objects_density_for_patch, self.objects_density, RandomObjectPlacer(self))
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

    def __init__(self):
        CosmoniumBase.__init__(self)

        self.config_file = 'ralph-data/ralph.yaml'
        self.splash = RalphSplash()

        config = RalphConfigParser()
        (self.noise, self.biome_noise, self.terrain_control, self.terrain_appearance, self.water, self.fog) = config.load_and_parse(self.config_file)

        self.tile_density = 64
        self.default_size = 128
        self.max_vertex_size = 64
        self.max_lod = 10

        self.size = 128 * 8
        self.max_distance = 1.001 * self.size * sqrt(2)
        self.noise_size = 512
        self.biome_size = 128
        self.noise_scale = 0.5 * self.size / self.default_size
        self.objects_density = int(25 * (1.0 * self.size / self.default_size) * (1.0 * self.size / self.default_size))
        self.objects_density = 250
        self.height_scale = 100 * 5.0
        self.has_water = True
        self.fullscreen = False
        self.shadow_caster = None
        self.light_angle = None
        self.light_dir = LVector3.up()
        self.vector_to_star = self.light_dir
        self.light_quat = LQuaternion()
        self.light_color = (1.0, 1.0, 1.0, 1.0)
        self.directionalLight = None
        self.shadow_size = self.default_size / 8
        self.shadow_box_length = self.height_scale

        self.observer = RalphCamera(self.cam, self.camLens)
        self.observer.init()

        self.distance_to_obs = float('inf')
        self.height_under = 0.0
        self.scene_position = LVector3()
        self.scene_scale_factor = 1
        self.scene_orientation = LQuaternion()

        #Size of an edge seen from 4 units above
        self.edge_apparent_size = (1.0 * self.size / self.tile_density) / (4.0 * self.observer.pixel_size)
        print("Apparent size:", self.edge_apparent_size)

        self.win.setClearColor((135.0/255, 206.0/255, 235.0/255, 1))

        # This is used to store which keys are currently pressed.
        self.keyMap = {
            "left": 0, "right": 0, "forward": 0, "backward": 0,
            "cam-left": 0, "cam-right": 0, "cam-up": 0, "cam-down": 0,
            "sun-left": 0, "sun-right": 0,
            "turbo": 0}

        # Set up the environment
        #
        # Create some lighting
        self.vector_to_obs = base.cam.get_pos()
        self.vector_to_obs.normalize()
        if True:
            self.shadow_caster = ShadowCaster(1024)
            self.shadow_caster.create()
            self.shadow_caster.set_lens(self.shadow_size, -self.shadow_box_length / 2.0, self.shadow_box_length / 2.0, -self.light_dir)
            self.shadow_caster.set_pos(self.light_dir * self.shadow_box_length / 2.0)
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

        # Accept the control keys for movement and rotation

        self.accept("escape", sys.exit)
        self.accept("control-q", sys.exit)
        self.accept("arrow_left", self.setKey, ["left", True])
        self.accept("arrow_right", self.setKey, ["right", True])
        self.accept("arrow_up", self.setKey, ["forward", True])
        self.accept("arrow_down", self.setKey, ["backward", True])
        self.accept("shift", self.setKey, ["turbo", True])
        self.accept("a", self.setKey, ["cam-left", True], direct=True)
        self.accept("s", self.setKey, ["cam-right", True], direct=True)
        self.accept("u", self.setKey, ["cam-up", True], direct=True)
        self.accept("u-up", self.setKey, ["cam-up", False])
        self.accept("d", self.setKey, ["cam-down", True], direct=True)
        self.accept("d-up", self.setKey, ["cam-down", False])
        self.accept("o", self.setKey, ["sun-left", True], direct=True)
        self.accept("o-up", self.setKey, ["sun-left", False])
        self.accept("p", self.setKey, ["sun-right", True], direct=True)
        self.accept("p-up", self.setKey, ["sun-right", False])
        self.accept("arrow_left-up", self.setKey, ["left", False])
        self.accept("arrow_right-up", self.setKey, ["right", False])
        self.accept("arrow_up-up", self.setKey, ["forward", False])
        self.accept("arrow_down-up", self.setKey, ["backward", False])
        self.accept("shift-up", self.setKey, ["turbo", False])
        self.accept("a-up", self.setKey, ["cam-left", False])
        self.accept("s-up", self.setKey, ["cam-right", False])
        self.accept("w", self.toggle_water)
        self.accept("h", self.print_debug)
        self.accept("f2", self.connect_pstats)
        self.accept("f3", self.toggle_filled_wireframe)
        self.accept("shift-f3", self.toggle_wireframe)
        self.accept("f5", self.bufferViewer.toggleEnable)
        self.accept("f8", self.terrain_shape.dump_tree)
        self.accept("f10", self.save_screenshot)
        self.accept('alt-enter', self.toggle_fullscreen)

        taskMgr.add(self.move, "moveTask")

        # Game state variables
        self.isMoving = False

        # Set up the camera
        self.cam.setPos(self.ralph.getX(), self.ralph.getY() + 10, 2)
        self.camera_height = 2.0
        render.set_shader_input("camera", self.cam.get_pos())

        self.cTrav = CollisionTraverser()

        self.ralphGroundRay = CollisionRay()
        self.ralphGroundRay.setOrigin(0, 0, 9)
        self.ralphGroundRay.setDirection(0, 0, -1)
        self.ralphGroundCol = CollisionNode('ralphRay')
        self.ralphGroundCol.addSolid(self.ralphGroundRay)
        self.ralphGroundCol.setFromCollideMask(CollideMask.bit(0))
        self.ralphGroundCol.setIntoCollideMask(CollideMask.allOff())
        self.ralphGroundColNp = self.ralph.attachNewNode(self.ralphGroundCol)
        self.ralphGroundHandler = CollisionHandlerQueue()
        self.cTrav.addCollider(self.ralphGroundColNp, self.ralphGroundHandler)

        # Uncomment this line to see the collision rays
        #self.ralphGroundColNp.show()

        # Uncomment this line to show a visual representation of the
        # collisions occuring
        #self.cTrav.showCollisions(render)

        #self.terrain_shape.test_lod(LPoint3d(*self.ralph.getPos()), self.distance_to_obs, self.pixel_size, self.terrain_appearance)
        #self.terrain_shape.update_lod(LPoint3d(*self.ralph.getPos()), self.distance_to_obs, self.pixel_size, self.terrain_appearance)
        #self.terrain.shape_updated()
        self.terrain.update_instance(LPoint3d(*self.ralph.getPos()), None)

    # Records the state of the arrow keys
    def setKey(self, key, value):
        self.keyMap[key] = value

    # Accepts arrow keys to move either the player or the menu cursor,
    # Also deals with grid checking and collision detection
    def move(self, task):

        # Get the time that elapsed since last frame.  We multiply this with
        # the desired speed in order to find out with which distance to move
        # in order to achieve that desired speed.
        dt = globalClock.getDt()

        # If the camera-left key is pressed, move camera left.
        # If the camera-right key is pressed, move camera right.

        if self.keyMap["cam-left"]:
            self.cam.setX(self.cam, -20 * dt)
        if self.keyMap["cam-right"]:
            self.cam.setX(self.cam, +20 * dt)
        if self.keyMap["cam-up"]:
            self.camera_height *= (1 + 2 * dt)
        if self.keyMap["cam-down"]:
            self.camera_height *= (1 - 2 * dt)
        if self.camera_height < 1.0:
            self.camera_height = 1.0

        if self.keyMap["sun-left"]:
            self.set_light_angle(self.light_angle + 30 * dt)
        if self.keyMap["sun-right"]:
            self.set_light_angle(self.light_angle - 30 * dt)

        # save ralph's initial position so that we can restore it,
        # in case he falls off the map or runs into something.

        startpos = self.ralph.getPos()

        # If a move-key is pressed, move ralph in the specified direction.

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

        #self.limit_pos(self.ralph)

        # If ralph is moving, loop the run animation.
        # If he is standing still, stop the animation.

        if self.keyMap["forward"] or self.keyMap["backward"] or self.keyMap["left"] or self.keyMap["right"]:
            if self.isMoving is False:
                self.ralph.loop("run")
                self.isMoving = True
        else:
            if self.isMoving:
                self.ralph.stop()
                self.ralph.pose("walk", 5)
                self.isMoving = False

        # If the camera is too far from ralph, move it closer.
        # If the camera is too close to ralph, move it farther.

        camvec = self.ralph.getPos() - self.cam.getPos()
        camvec.setZ(0)
        camdist = camvec.length()
        camvec.normalize()
        if camdist > 10.0:
            self.cam.setPos(self.cam.getPos() + camvec * (camdist - 10))
            camdist = 10.0
        if camdist < 5.0:
            self.cam.setPos(self.cam.getPos() - camvec * (5 - camdist))
            camdist = 5.0

        # Normally, we would have to call traverse() to check for collisions.
        # However, the class ShowBase that we inherit from has a task to do
        # this for us, if we assign a CollisionTraverser to self.cTrav.
        self.cTrav.traverse(render)

        if False:
            # Adjust ralph's Z coordinate.  If ralph's ray hit anything, put
            # him back where he was last frame.

            entries = list(self.ralphGroundHandler.getEntries())
            entries.sort(key=lambda x: x.getSurfacePoint(render).getZ())

            if len(entries) > 0:
                self.ralph.setPos(startpos)
        ralph_height = self.get_height(self.ralph.getPos())
        self.ralph.setZ(ralph_height)

        # Keep the camera at one foot above the terrain,
        # or two feet above ralph, whichever is greater.

        camera_height = self.get_height(self.cam.getPos()) + 1.0
        if camera_height < ralph_height + self.camera_height:
            self.cam.setZ(ralph_height + self.camera_height)
        else:
            self.cam.setZ(camera_height)
        #self.limit_pos(self.camera)

        # The camera should look in ralph's direction,
        # but it should also try to stay horizontal, so look at
        # a floater which hovers above ralph's head.
        self.cam.lookAt(self.floater)

        #self.shadow_caster.set_pos(self.ralph.get_pos())
        self.shadow_caster.set_pos(self.ralph.get_pos() - camvec * camdist + camvec * self.shadow_size / 2)

        render.set_shader_input("camera", self.cam.get_pos())
        self.vector_to_obs = base.cam.get_pos()
        self.vector_to_obs.normalize()

        if self.isMoving:
            #self.terrain_shape.test_lod(LPoint3d(*self.ralph.getPos()), self.distance_to_obs, self.pixel_size, self.terrain_appearance)
            pass#self.terrain_shape.update_lod(LPoint3d(*self.ralph.getPos()), self.distance_to_obs, self.pixel_size, self.terrain_appearance)

        self.object_collection.update_instance()
        self.terrain.update_instance(LPoint3d(*self.ralph.getPos()), None)
        return task.cont

    def print_debug(self):
        print("Height:", self.get_height(self.ralph.getPos()), self.terrain.get_height(self.ralph.getPos()))
        print("Ralph:", self.ralph.get_pos())
        print("Camera:", base.cam.get_pos())
demo = RoamingRalphDemo()
demo.run()
