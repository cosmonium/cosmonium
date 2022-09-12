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


from direct.showbase.ShowBase import ShowBase
from panda3d.core import loadPrcFileData, loadPrcFile, Filename, WindowProperties, PandaSystem, PStatClient
from panda3d.core import Texture, CardMaker, CullBinManager
from panda3d.core import AmbientLight
from panda3d.core import LightRampAttrib, AntialiasAttrib
from panda3d.core import LColor, NodePath, PerspectiveLens
from panda3d.core import Camera

from direct.task.Task import Task

import logging
import gettext

from .parsers.configparser import configParser
from .foundation import BaseObject
from .scene.scenemanager import StaticSceneManager, DynamicSceneManager, RegionSceneManager, C_CameraHolder, remove_main_region
from .scene.sceneanchor import SceneAnchor, SceneAnchorCollection
from .scene.sceneworld import ObserverCenteredWorld, Worlds
from .labels import Labels
from .sprites import RoundDiskPointSprite, GaussianPointSprite, ExpPointSprite, MergeSprite
from .pointsset import PointsSetShapeObject, RegionsPointsSetShape, PassthroughPointsSetShape, EmissivePointsSetShape, HaloPointsSetShape
from .dircontext import defaultDirContext
from .opengl import OpenGLConfig
from .pipeline.scenepipeline import ScenePipeline
from .objects.universe import Universe
from .objects.stellarobject import StellarObject
from .objects.systems import StellarSystem, SimpleSystem
from .objects.stellarbody import StellarBody
from .objects.reflective import ReflectiveBody
from .engine.c_settings import c_settings
from .engine.anchors import StellarAnchor, CartesianAnchor
from .engine.traversers import UpdateTraverser, FindClosestSystemTraverser, FindLightSourceTraverser, FindShadowCastersTraverser
from .lights import SurrogateLight, LightSources
from .components.annotations.grid import Grid
from .astro.frame import BodyReferenceFrame
from .astro.frame import AbsoluteReferenceFrame, SynchroneReferenceFrame, OrbitReferenceFrame
#TODO: from .astro.frame import SurfaceReferenceFrame
from .celestia.cel_url import CelUrl
from .celestia import cel_parser, cel_engine

#Initialiser parsers
from .parsers import parsers

from .bodyclass import bodyClasses
from .autopilot import AutoPilot
from .controllers import ShipMover
from .camera import CameraHolder, CameraController, FixedCameraController, TrackCameraController, LookAroundCameraController, FollowCameraController
from .timecal import Time
from .events import EventsDispatcher
from .states import StatesProvider
from .debug import Debug
from .appstate import AppState
from .ui.gui import Gui
from .ui.mouse import Mouse
from .ui.splash import Splash, NoSplash
from .nav import FreeNav, WalkNav, ControlNav
from .controllers import BodyController, SurfaceBodyMover
from .ships import NoShip
from .astro import units
from .parsers.yamlparser import YamlModuleParser
from .fonts import fontsManager
from .pstats import pstat
from . import utils
from . import workers
from . import cache
from . import mesh
from . import settings
from . import pstats
from . import version

from math import pi
import subprocess
import platform
import sys
import os
from cosmonium.astro.units import J2000_Orientation, J200_EclipticOrientation

# Patch gettext classes
if sys.version_info < (3, 8):
    def pgettext(self, context, message):
        if self._fallback:
            return self._fallback.pgettext(context, message)
        return message
    gettext.NullTranslations.pgettext = pgettext
    gettext.GNUTranslations.CONTEXT = "%s\x04%s"
    def pgettext(self, context, message):
        ctxt_msg_id = self.CONTEXT % (context, message)
        missing = object()
        tmsg = self._catalog.get(ctxt_msg_id, missing)
        if tmsg is missing:
            if self._fallback:
                return self._fallback.pgettext(context, message)
            return message
        return tmsg
    gettext.GNUTranslations.pgettext = pgettext

class CosmoniumBase(ShowBase):
    def __init__(self):
        self.observer = None #TODO: For window_event below
        self.debug = Debug(self)
        self.wireframe = False
        self.wireframe_filled = False
        self.trigger_check_settings = True
        self.request_fullscreen = False
        self.common_state = NodePath("<state>")

        configParser.load()
        self.init_lang()
        self.print_info()
        self.panda_config()
        ShowBase.__init__(self, windowType='none')
        if not self.app_config.test_start:
            self.pipeline = ScenePipeline(engine=self.graphics_engine)
            self.pipeline.init()
            OpenGLConfig.check_opengl_config(self)
            #self.create_additional_display_regions()
            self.near_cam = None
        else:
            self.buttonThrowers = [NodePath('dummy')]
            self.camera = NodePath('dummy')
            self.cam = self.camera.attach_new_node(Camera('camera', PerspectiveLens()))
            self.camLens = self.cam.node().get_lens()
            settings.shader_version = 130

        #TODO: should find a better way than patching classes...
        BaseObject.context = self
        StellarObject.context = self
        YamlModuleParser.app = self
        BodyController.context = self

        self.setBackgroundColor(0, 0, 0, 1)
        self.disableMouse()
        cache.init_cache()
        self.register_events()

        self.common_state.setShaderAuto()

        workers.asyncTextureLoader = workers.AsyncTextureLoader(self)
        workers.syncTextureLoader = workers.SyncTextureLoader()

        # Front to back bin is added between opaque and transparent
        CullBinManager.get_global_ptr().add_bin("front_to_back", CullBinManager.BT_front_to_back, 25)

    def load_lang(self, domain, locale_path):
        languages = None
        for envar in ('LANGUAGE', 'LC_ALL', 'LC_MESSAGES', 'LANG'):
            val = os.environ.get(envar)
            if val:
                languages = val.split(':')
                break
        if languages is None:
            if sys.platform == 'darwin':
                #TODO: This is a workaround until either Panda3D provides the locale to use
                #or we switch to pyobjc.
                #This should be moved to its own module
                status, output = subprocess.getstatusoutput('defaults read -g AppleLocale')
                if status == 0:
                    languages = [output]
                else:
                    print("Could not retrieve default locale")
            elif sys.platform == 'win32':
                import ctypes
                import locale
                windll = ctypes.windll.kernel32
                language = locale.windows_locale[ windll.GetUserDefaultUILanguage() ]
                if language is not None:
                    languages = [language]
                else:
                    print("Could not retrieve default locale")

        print("Found languages", ', '.join(languages))
        return gettext.translation(domain, locale_path, languages=languages, fallback=True)

    def init_lang(self):
        self.translation = self.load_lang('cosmonium', defaultDirContext.find_file('main', 'locale'))
        self.translation.install()

    def panda_config(self):
        data = []
        OpenGLConfig.request_opengl_config(data)
        self.app_panda_config(data)
        data.append("text-encoding utf8")
        data.append("paste-emit-keystrokes #f")
        #TODO: Still needed ?
        data.append("bounds-type box")
        data.append("screenshot-extension {}".format(settings.screenshot_format))
        data.append("screenshot-filename %~p/{}".format(settings.screenshot_filename))
        if settings.win_fullscreen and settings.win_fs_width != 0 and settings.win_fs_height != 0:
            self.request_fullscreen = True
            data.append("fullscreen %d" % settings.win_fullscreen)
            data.append("win-size %d %d" % (settings.win_fs_width, settings.win_fs_height))
        else:
            data.append("win-size %d %d" % (settings.win_width, settings.win_height))
        data.append("lens-far-limit %g" % settings.lens_far_limit)
        data.append("transform-cache 0")
        data.append("state-cache 0")
        loadPrcFileData("", '\n'.join(data))
        if settings.prc_file is not None:
            config_file = settings.prc_file
            if not os.path.isabs(config_file):
                config_file = os.path.join(settings.config_dir, config_file)
            filename = Filename.from_os_specific(config_file)
            if filename.exists():
                print("Loading panda config", filename)
                loadPrcFile(filename)
            else:
                print("Panda config file", filename)

    def app_panda_config(self, data):
        pass

    def print_info(self):
        print("Cosmonium version: V" + version.version_str)
        print("Python version:", platform.python_version())
        print("Panda version: %s (%s) by %s (%s)" % (PandaSystem.getVersionString(),
                                                     PandaSystem.getGitCommit(),
                                                     PandaSystem.getDistributor(),
                                                     PandaSystem.getBuildDate()))
        print("Panda Systems:")
        for system in PandaSystem.get_global_ptr().get_systems():
            print("\t", system)
        print("Data type:", "double" if settings.use_double else 'float')

    def create_additional_display_regions(self):
        pass

    def register_events(self):
        if not self.app_config.test_start:
            self.accept(self.win.getWindowEvent(), self.window_event)
        self.accept('panic-deactivate-gsg', self.gsg_failure)

    def gsg_failure(self, event):
        print("Internal error detected, see output.log for more details")
        self.userExit()

    def get_fullscreen_sizes(self):
        info = self.pipe.getDisplayInformation()
        resolutions = []
        for idx in range(info.getTotalDisplayModes()):
            width = info.getDisplayModeWidth(idx)
            height = info.getDisplayModeHeight(idx)
            bits = info.getDisplayModeBitsPerPixel(idx)
            resolutions.append([width, height])
        resolutions.sort(key=lambda x: x[0], reverse=True)
        return resolutions

    def toggle_fullscreen(self):
        settings.win_fullscreen = not settings.win_fullscreen
        wp = WindowProperties(self.win.getProperties())
        wp.setFullscreen(settings.win_fullscreen)
        if settings.win_fullscreen:
            if settings.win_fs_width != 0 and settings.win_fs_height != 0:
                win_fs_width = settings.win_fs_width
                win_fs_height = settings.win_fs_height
            else:
                win_fs_width = base.pipe.getDisplayWidth()
                win_fs_height = base.pipe.getDisplayHeight()
            wp.setSize(win_fs_width, win_fs_height)
            # Defer config saving in case the switch fails
            self.request_fullscreen = True
        else:
            wp.setSize(settings.win_width, settings.win_height)
            configParser.save()
        self.win.requestProperties(wp)

    def window_event(self, window):
        if self.win is None: return
        if self.win.is_closed():
            self.userExit()
        wp = self.win.getProperties()
        width = wp.getXSize()
        height = wp.getYSize()
        if settings.win_fullscreen:
            # Only save config is the switch to FS is successful
            if wp.getFullscreen():
                if self.request_fullscreen or width != settings.win_fs_width or height != settings.win_fs_height:
                    settings.win_fs_width = width
                    settings.win_fs_height = height
                    configParser.save()
                if self.request_fullscreen:
                    if self.gui is not None: self.gui.update_info("Press <Alt-Enter> to leave fullscreen mode", duration=0.5, fade=2.0)
            else:
                if self.gui is not None: self.gui.update_info("Could not switch to fullscreen mode", duration=0.5, fade=2.0)
                settings.win_fullscreen = False
            self.request_fullscreen = False
        else:
            if width != settings.win_width or height != settings.win_height:
                settings.win_width = width
                settings.win_height = height
                configParser.save()
        if self.observer is not None:
            self.observer.set_film_size(width, height)
            self.common_state.setShaderInput("near_plane_height", self.observer.height / self.observer.tan_fov2)
            self.common_state.setShaderInput("pixel_size", self.observer.pixel_size)
        if self.pipeline is not None:
            self.pipeline.update_win_size(width, height)
        if self.gui is not None:
            self.gui.update_size(width, height)
        if settings.color_picking and self.oid_texture is not None:
            self.oid_texture.clear()
            self.oid_texture.setup_2d_texture(width, height, Texture.T_unsigned_byte, Texture.F_rgba8)
            self.oid_texture.set_clear_color(LColor(0, 0, 0, 0))

    def connect_pstats(self):
        PStatClient.connect()

    def toggle_wireframe(self):
        self.common_state.clear_render_mode()
        if self.wireframe_filled:
            self.wireframe_filled = False
            self.wireframe = False
        self.wireframe = not self.wireframe
        if self.wireframe:
            self.common_state.set_render_mode_wireframe()

    def toggle_filled_wireframe(self):
        self.common_state.clear_render_mode()
        if self.wireframe:
            self.wireframe = False
            self.wireframe_filled = False
        self.wireframe_filled = not self.wireframe_filled
        if self.wireframe_filled:
            self.common_state.set_render_mode_filled_wireframe(settings.wireframe_fill_color)

    def toggle_stereoscopic_framebuffer(self):
        settings.stereoscopic_framebuffer = not settings.stereoscopic_framebuffer
        if settings.stereoscopic_framebuffer:
            settings.red_blue_stereo = False
            settings.side_by_side_stereo = False
        configParser.save()

    def toggle_red_blue_stereo(self):
        settings.red_blue_stereo = not settings.red_blue_stereo
        if settings.red_blue_stereo:
            settings.stereoscopic_framebuffer = False
            settings.side_by_side_stereo = False
        configParser.save()

    def toggle_side_by_side_stereo(self):
        settings.side_by_side_stereo = not settings.side_by_side_stereo
        if settings.side_by_side_stereo:
            settings.red_blue_stereo = False
            settings.stereoscopic_framebuffer = False
        configParser.save()

    def toggle_swap_eyes(self):
        settings.stereo_swap_eyes = not settings.stereo_swap_eyes
        configParser.save()

    def save_screenshot(self, filename=None):
        if settings.screenshot_path is not None:
            filename = self.screenshot(namePrefix=settings.screenshot_path)
            if filename is not None:
                print("Saving screenshot into", filename)
            else:
                print("Could not save filename")
                if self.gui is not None:
                    self.gui.update_info("Could not save filename", duration=1.0, fade=1.0)
        else:
            self.gui.update_info(_("Screenshot not saved"), duration=0.5, fade=1.0)
            self.gui.show_select_screenshots()

    def set_screenshots_path(self, path):
        settings.screenshot_path = path
        self.save_settings()

class Cosmonium(CosmoniumBase):
    FREE_NAV = 0
    WALK_NAV = 1
    CONTROL_NAV = 2

    def __init__(self):
        CosmoniumBase.__init__(self)

        mesh.init_mesh_loader()
        fontsManager.register_fonts(defaultDirContext.find_font('dejavu'))

        self.update_id = 0
        self.patch = None
        self.selected = None
        self.follow = None
        self.sync = None
        self.track = None
        self.extra = []
        self.fly = False
        self.nav_controllers = []
        self.nav = None
        self.gui = None
        self.old_visibles = []
        self.visibles = []
        self.becoming_visibles = []
        self.no_longer_visibles = []
        self.old_resolved = []
        self.resolved = []
        self.becoming_resolved = []
        self.no_longer_resolved = []
        self.global_light_sources = []
        self.orbits = []
        self.shadow_casters = []
        self.nearest_system = None
        self.nearest_body = None
        self.hdr = 0
        self.observer = None
        self.time = Time()
        self.current_sequence = None
        self.autopilot = None
        self.globalAmbient = None
        self.oid_texture = None
        self.camera_controllers = []
        self.camera_controller = None
        self.body_controllers = []
        self.ships = []
        self.ship = None

        if self.app_config.test_start:
            self.near_cam = None

        self.worlds = Worlds()
        self.universe = Universe(self)
        self.background = ObserverCenteredWorld("background", background=True)
        self.worlds.add_world(self.background)
        self.labels = Labels()

        if settings.color_picking:
            self.oid_texture = Texture()
            self.oid_texture.setup_2d_texture(settings.win_width, settings.win_height, Texture.T_unsigned_byte, Texture.F_rgba8)
            self.oid_texture.set_clear_color(LColor(0, 0, 0, 0))
            self.common_state.set_shader_input("oid_store", self.oid_texture)
        else:
            self.oid_texture = None
        self.observer = CameraHolder()
        self.autopilot = AutoPilot(self)
        self.mouse = Mouse(self, self.oid_texture)
        if self.near_cam is not None:
            self.observer.add_linked_cam(self.near_cam)

        self.add_camera_controller(FixedCameraController())
        self.add_camera_controller(TrackCameraController())
        self.add_camera_controller(LookAroundCameraController())
        self.add_camera_controller(FollowCameraController())
        self.observer.init()
        if C_CameraHolder is not None:
            self.c_camera_holder = C_CameraHolder(self.observer.anchor, self.observer.camera_np, self.observer.lens)
        else:
            self.c_camera_holder = self.observer

        self.add_nav_controller(FreeNav())
        self.add_nav_controller(WalkNav())
        self.add_nav_controller(ControlNav())

        ship = NoShip()
        self.add_ship(ship)

        self.splash = Splash() if not self.app_config.test_start else NoSplash()

        if not settings.sync_data_load:
            self.async_start = workers.AsyncMethod("async_start", self, self.load_task, self.configure_scene)
        else:
            self.load_task()
            self.configure_scene()

    def load_task(self):
        self.init_universe()

        self.load_universe()

        self.splash.set_text("Building tree...")
        print("Building tree")
        self.universe.rebuild()
        #self.universe.octree.print_summary()
        #self.universe.octree.print_stats()

        self.home = self.universe.find_by_path(self.app_config.default_home)
        if self.home is None:
            print("Could not find home object", self.app_config.default_home)
        self.splash.set_text("Done")

    def configure_scene(self):
        #Force frame update to render the last status of the splash screen
        base.graphicsEngine.renderFrame()
        self.splash.close()

        #TODO: Temporarily until state registration is split up between each class
        self.states_provider = StatesProvider(self, self.time, self.observer, self.autopilot, self.gui, self.debug)

        if self.gui is None:
            self.gui = Gui(self.app_config.ui, self, self.time, self.observer, self.mouse, self.autopilot)
            self.mouse.set_ui(self.gui)

        #TODO: Temporarily until event registration is split up between each class
        self.events_dispatcher = EventsDispatcher(self, self.time, self.observer, self.autopilot, self.gui, self.debug)

        # Use the first of each controllers as default
        self.set_nav(self.nav_controllers[0])
        self.set_ship(self.ships[0])
        self.set_camera_controller(self.camera_controllers[0])

        self.nav.register_events(self)
        self.gui.register_events(self)

        self.scene_manager = None
        if not self.app_config.test_start:
            print("Using scene manager '{}'".format(settings.scene_manager))
            if settings.scene_manager == 'static':
                self.scene_manager = StaticSceneManager(self.render)
            elif settings.scene_manager == 'dynamic':
                self.scene_manager = DynamicSceneManager(self.render)
            elif settings.scene_manager == 'region':
                self.scene_manager = RegionSceneManager()
            else:
                print("ERROR: Unknown scene manager {}".format(settings.scene_manager))
            remove_main_region(self.cam)
            self.scene_manager.scale = settings.scale
            self.scene_manager.init_camera(self.c_camera_holder, self.cam)
            self.scene_manager.set_camera_mask(BaseObject.DefaultCameraFlag | BaseObject.AnnotationCameraFlag)
            self.pipeline.create()
            self.pipeline.set_scene_manager(self.scene_manager)
        else:
            self.scene_manager = DynamicSceneManager(self.render)
            self.scene_manager.init_camera(self.c_camera_holder, self.cam)

        if settings.render_sprite_points:
            if settings.point_scale_dpi_aware and not self.app_config.test_start:
                screen_point_scale = self.pipe.display_zoom
            else:
                screen_point_scale = settings.custom_point_scale
            self.point_sprite = GaussianPointSprite(size=16, fwhm=8)
            self.halos_sprite = ExpPointSprite(size=256, max_value=0.6)
            if self.scene_manager.has_regions():
                points_shape = RegionsPointsSetShape(EmissivePointsSetShape, has_size=True, has_oid=True, screen_scale=screen_point_scale)
            else:
                points_shape = PassthroughPointsSetShape(EmissivePointsSetShape(has_size=True, has_oid=True, screen_scale=screen_point_scale))
            self.pointset = PointsSetShapeObject(points_shape, use_sprites=True, sprite=self.point_sprite)
            if self.scene_manager.has_regions():
                points_shape = RegionsPointsSetShape(HaloPointsSetShape, has_size=True, has_oid=True, screen_scale=screen_point_scale)
            else:
                points_shape = PassthroughPointsSetShape(HaloPointsSetShape(has_size=True, has_oid=True, screen_scale=screen_point_scale))
            self.haloset = PointsSetShapeObject(points_shape, use_sprites=True, sprite=self.halos_sprite, background=settings.halo_depth)
            self.pointset.configure(self.scene_manager)
            self.haloset.configure(self.scene_manager)

        self.common_state.setAntialias(AntialiasAttrib.MMultisample)
        self.setFrameRateMeter(False)

        self.set_ambient(settings.global_ambient)

        self.equatorial_grid = Grid("Equatorial", J2000_Orientation, LColor(0.28,  0.28,  0.38, 1))
        self.background.add_component(self.equatorial_grid)
        self.equatorial_grid.set_shown(settings.show_equatorial_grid)

        self.ecliptic_grid = Grid("Ecliptic", J200_EclipticOrientation, LColor(0.28,  0.28,  0.38, 1))
        self.background.add_component(self.ecliptic_grid)
        self.ecliptic_grid.set_shown(settings.show_ecliptic_grid)

        self.time.set_current_date()

        for controller in self.body_controllers:
            controller.init()

        #self.universe.first_update()
        self.camera_controller.update(self.time.time_full, 0)
        #self.universe.first_update_obs(self.observer)
        self.window_event(None)

        taskMgr.add(self.time_task, "time-task", sort=10)

        self.time_task(None)
        self.start_universe()
        if self.app_config.test_start:
            #TODO: this is where the tests should be inserted
            print("Tests done.")
            self.userExit()

    def app_panda_config(self, data):
        icon = defaultDirContext.find_texture('cosmonium.ico')
        data.append("icon-filename %s" % icon)
        data.append("window-title Cosmonium")

    def add_controller(self, controller):
        self.body_controllers.append(controller)

    def create_additional_display_regions(self):
        self.near_dr = self.win.make_display_region()
        self.near_dr.set_sort(1)
        self.near_dr.set_clear_depth_active(True)
        near_cam_node = Camera('nearcam')
        self.near_cam = self.camera.attach_new_node(near_cam_node)
        self.near_dr.setCamera(self.near_cam)
        self.near_cam.node().set_camera_mask(BaseObject.NearCameraFlag)
        self.near_cam.node().get_lens().set_near_far(units.m /self.scene_manager.scale, float('inf'))

    def add_camera_controller(self, camera_controller):
        self.camera_controllers.append(camera_controller)

    def get_camera_controller(self, camera_id):
        for camera_controller in self.camera_controllers:
            if camera_id == camera_controller.get_id():
                return camera_controller
        return None

    def set_camera_controller(self, camera_controller):
        if camera_controller.require_target():
            if self.track is None:
                self.track = self.selected
            if self.track is None:
                return
        if self.camera_controller is not None:
            position = self.camera_controller.get_local_position()
            rotation = self.camera_controller.get_local_orientation()
            self.camera_controller.deactivate()
        else:
            position = None
            rotation = None
        self.camera_controller = camera_controller
        if camera_controller.require_target():
            self.camera_controller.set_target(self.track)
        self.camera_controller.activate(self.observer, self.ship.anchor)
        if position is not None and rotation is not None:
            self.camera_controller.set_local_position(position)
            self.camera_controller.set_local_orientation(rotation)
        if self.ship is not None:
            self.camera_controller.set_camera_hints(**self.ship.get_camera_hints())
        self.nav.set_camera_controller(camera_controller)
        self.autopilot.set_camera_controller(self.camera_controller)
        print("Switching camera to", self.camera_controller.get_name())

    def set_default_camera_controller(self):
        for camera_controller in self.camera_controllers:
            if self.ship.supports_camera_mode(camera_controller.camera_mode):
                self.set_camera_controller(camera_controller)
                break
        else:
            print("ERROR: No camera controller supported by this ship")

    def add_ship(self, ship):
        self.ships.append(ship)

    def get_ship(self, name):
        name = name.lower()
        for ship in self.ships:
            if name == ship.get_name().lower():
                return ship
        return None

    def set_ship(self, ship):
        if self.ship is not None:
            self.worlds.remove_world(self.ship)
            self.autopilot.set_controller(None)
            self.nav.set_controller(None)
            self.camera_controller.set_reference_anchor(None)
        old_ship = self.ship
        self.ship = ship
        if self.ship is not None:
            self.worlds.add_world(self.ship)
            self.autopilot.set_controller(ShipMover(self.ship.anchor))
            self.nav.set_controller(ShipMover(self.ship.anchor))
            if old_ship is not None:
                self.ship.anchor.copy(old_ship.anchor)
            if self.camera_controller is not None:
                if self.ship.supports_camera_mode(self.camera_controller.camera_mode):
                    self.camera_controller.set_reference_anchor(self.ship.anchor)
                    self.camera_controller.set_camera_hints(**self.ship.get_camera_hints())
                else:
                    #Current camera controller is not supported by the ship, switch to the first one supported
                    for camera_controller in self.camera_controllers:
                        if self.ship.supports_camera_mode(camera_controller.camera_mode):
                            #Apply the current camera controller to be able to switch
                            self.camera_controller.set_reference_anchor(self.ship.anchor)
                            self.set_camera_controller(camera_controller)
                            break
                    else:
                        print("ERROR: No camera controller supported by this ship")

    def add_nav_controller(self, nav_controller):
        self.nav_controllers.append(nav_controller)

    def get_nav_controller(self, nav_id):
        for nav in self.nav_controllers:
            if nav_id == nav.get_id():
                return nav
        return None

    def set_nav(self, nav, target=None, controller=None):
        if nav.require_target() and target is None:
            return
        if nav.require_controller() and controller is None:
            return
        if controller is None and self.ship is not None:
            controller = ShipMover(self.ship.anchor)
        if self.nav is not None:
            self.nav.remove_events(self)
        self.nav = nav
        if self.nav is not None:
            self.nav.init(self, self.observer, self.camera_controller, controller)
            self.nav.register_events(self)
            if nav.require_target():
                self.nav.set_target(target)
            if nav.require_controller():
                nav.set_controller(controller)
            self.gui.set_nav(nav)
            print("Switching navigation controller to", self.nav.get_name())

    def toggle_fly_mode(self):
        if not self.fly:
            if self.selected is not None:
                print("Fly mode")
                self.fly = True
                self.follow = None
                self.sync = None
                self.set_nav(self.nav_controllers[self.WALK_NAV], target=self.selected)
        else:
            print("Free mode")
            self.fly = False
            self.set_nav(self.nav_controllers[self.FREE_NAV])

    def toggle_hdr(self):
        self.hdr += 1
        if self.hdr > 3: self.hdr = 0
        print("HDR:", self.hdr)
        if self.hdr == 0:
            self.common_state.clearAttrib(LightRampAttrib.getClassType())
        elif self.hdr == 1:
            self.common_state.setAttrib(LightRampAttrib.makeHdr0())
        elif self.hdr == 2:
            self.common_state.setAttrib(LightRampAttrib.makeHdr1())
        elif self.hdr == 3:
            self.common_state.setAttrib(LightRampAttrib.makeHdr2())

    def save_screenshot_no_annotation(self):
        if settings.screenshot_path is not None:
            state = self.gui.hide_with_state()
            self.scene_manager.set_camera_mask(BaseObject.DefaultCameraFlag)
            base.graphicsEngine.renderFrame()
            filename = self.screenshot(namePrefix=settings.screenshot_path)
            self.gui.show_with_state(state)
            self.scene_manager.set_camera_mask(BaseObject.DefaultCameraFlag | BaseObject.AnnotationCameraFlag)
            if filename is not None:
                print("Saving screenshot without annotation into", filename)
            else:
                print("Could not save filename")
        else:
            self.gui.update_info(_("Screenshot not saved"), duration=0.5, fade=1.0)
            self.gui.show_select_screenshots()

    def select_body(self, body):
        if self.selected == body:
            return
        if self.selected is not None:
            print("Deselect", self.selected.get_name())
            self.selected.set_selected(False)
        if body is not None:
            print("Select", body.get_name())
            self.update_extra(body)
            body.set_selected(True)
        self.selected = body
        if self.fly:
            #Disable fly mode when changing body
            self.toggle_fly_mode()

    def select_home(self):
        self.select_body(self.home)

    def reset_nav(self):
        print("Reset nav")
        self.follow = None
        self.ship.anchor.set_frame(AbsoluteReferenceFrame())
        self.observer.set_frame(AbsoluteReferenceFrame())
        self.sync = None
        if self.fly:
            #Disable fly mode when changing body
            self.toggle_fly_mode()
        if self.track is not None:
            self.track = None
            self.set_default_camera_controller()
        self.autopilot.reset()

    def center_on_object(self, target=None, duration=None, cmd=True, proportional=True):
        if target is None and self.selected is not None:
            target = self.selected
        self.camera_controller.center_on_object(target, duration, cmd, proportional)

    def run_script(self, sequence):
        if self.current_sequence is not None:
            self.current_sequence.pause()
        self.current_sequence = sequence
        if self.current_sequence is not None:
            self.current_sequence.start()
        return self.current_sequence is not None

    def load_and_run_script(self, script_path):
        script = cel_parser.load(script_path)
        running = self.run_script(cel_engine.build_sequence(self, script))
        return running

    def reset_script(self):
        if self.current_sequence is not None:
            self.current_sequence.pause()
            self.current_sequence = None

    def load_cel_url(self, url):
        print("Loading", url)
        state = None
        cel_url = CelUrl()
        if cel_url.parse(url):
            state = cel_url.convert_to_state(self)
        if state is not None:
            state.apply_state(self)
        else:
            print("Invalid cel://")
            self.gui.update_info("Invalid URL...")

    def save_celurl(self):
        state = AppState()
        state.save_state(self)
        cel_url = CelUrl()
        cel_url.store_state(self, state)
        url = cel_url.encode()
        self.gui.clipboard.copy_to(url)
        print(url)

    def load_celurl(self):
        url = self.gui.clipboard.copy_from()
        if url is None or url == '': return
        print(url)
        state = None
        cel_url = CelUrl()
        if cel_url.parse(url):
            state = cel_url.convert_to_state(self)
        if state is not None:
            state.apply_state(self)
        else:
            print("Invalid URL: '%s'" % url)
            self.gui.update_info(_("Invalid URL..."))

    def reset_all(self):
        self.gui.update_info("Cancel", duration=0.5, fade=1.0)
        self.reset_nav()
        self.reset_script()

    def update_settings(self):
        self.trigger_check_settings = True
        self.save_settings()

    def save_settings(self):
        configParser.save()

    def set_limit_magnitude(self, mag):
        settings.lowest_app_magnitude = min(16.0, max(0.0, mag))
        print("Magnitude limit:  %.1f" % settings.lowest_app_magnitude)
        self.gui.update_info(_("Magnitude limit:  %.1f") % settings.lowest_app_magnitude, duration=0.5, fade=1.0)
        self.save_settings()

    def incr_limit_magnitude(self, incr):
        self.set_limit_magnitude(settings.lowest_app_magnitude + incr)

    def toggle_orbits(self):
        settings.show_orbits = not settings.show_orbits
        self.update_settings()
            
    def toggle_clouds(self):
        settings.show_clouds = not settings.show_clouds
        self.update_settings()
            
    def toggle_atmosphere(self):
        settings.show_atmospheres = not settings.show_atmospheres
        self.update_settings()

    def toggle_rotation_axis(self):
        settings.show_rotation_axis = not settings.show_rotation_axis
        self.update_settings()

    def toggle_reference_axis(self):
        settings.show_reference_axis = not settings.show_reference_axis
        self.update_settings()

    def set_grid_equatorial(self, status):
        settings.show_equatorial_grid = status
        self.equatorial_grid.set_shown(status)
        configParser.save()

    def toggle_grid_equatorial(self):
        self.set_grid_equatorial(not settings.show_equatorial_grid)

    def set_grid_ecliptic(self, status):
        settings.show_ecliptic_grid = status
        self.ecliptic_grid.set_shown(status)
        configParser.save()

    def toggle_grid_ecliptic(self):
        self.set_grid_ecliptic(not settings.show_ecliptic_grid)

    def toggle_asterisms(self):
        settings.show_asterisms = not settings.show_asterisms
        self.update_settings()

    def toggle_boundaries(self):
        settings.show_boundaries = not settings.show_boundaries
        self.update_settings()

    def toggle_body_class(self, body_class):
        bodyClasses.toggle_show(body_class)
        self.update_settings()

    def show_label(self, body_class):
        bodyClasses.show_label(body_class)
        self.update_settings()

    def hide_label(self, body_class):
        bodyClasses.hide_label(body_class)
        self.update_settings()

    def toggle_label(self, body_class):
        bodyClasses.toggle_show_label(body_class)
        self.update_settings()

    def show_orbit(self, body_class):
        print("Show orbit", body_class)
        bodyClasses.show_orbit(body_class)
        self.update_settings()

    def hide_orbit(self, body_class):
        print("Show orbit", body_class)
        bodyClasses.hide_orbit(body_class)
        self.update_settings()

    def toggle_orbit(self, body_class):
        print("Toggle orbit", body_class)
        bodyClasses.toggle_show_orbit(body_class)
        self.update_settings()

    def select_planet(self, name):
        order = int(name)
        to_select = None
        if self.nearest_system is not None:
            if isinstance(self.nearest_system, SimpleSystem):
                if order > 0:
                    to_select = self.nearest_system.find_nth_child(order)
                else:
                    to_select = self.nearest_system
            elif isinstance(self.nearest_system, StellarSystem):
                if order > 0:
                    order-= 1
                    to_select = self.nearest_system.find_nth_child(order)
                else:
                    to_select = self.nearest_system
            else:
                if order == 0:
                    to_select = self.nearest_system
        if to_select is not None:
            if isinstance(to_select, SimpleSystem):
                to_select = to_select.primary
            self.select_body(to_select)

    def go_home(self):
        self.select_body(self.home)

    def set_ambient(self, ambient):
        settings.global_ambient = clamp(ambient, 0.0, 1.0)
        if self.globalAmbient is not None:
            self.common_state.clearLight(self.globalAmbientPath)
            self.globalAmbientPath.removeNode()
        self.globalAmbient=AmbientLight('globalAmbient')
        if settings.use_srgb:
            corrected_ambient = pow(settings.global_ambient, 2.2)
        else:
            corrected_ambient = settings.global_ambient
        settings.corrected_global_ambient = corrected_ambient
        print("Ambient light level:  %.2f" % settings.global_ambient)
        self.gui.update_info("Ambient light level:  %.2f" % settings.global_ambient, duration=0.5, fade=1.0)
        self.globalAmbient.setColor((corrected_ambient, corrected_ambient, corrected_ambient, 1))
        self.globalAmbientPath = self.common_state.attachNewNode(self.globalAmbient)
        self.common_state.setLight(self.globalAmbientPath)
        self.common_state.set_shader_input("global_ambient", settings.corrected_global_ambient)
        configParser.save()

    def incr_ambient(self, ambient_incr):
        self.set_ambient(settings.global_ambient + ambient_incr)

    def follow_selected(self):
        self.follow_body(self.selected)

    def follow_body(self, body):
        self.follow = body
        self.sync = None
        if self.follow is not None:
            print("Follow", self.follow.get_name())
            self.ship.anchor.set_frame(OrbitReferenceFrame(body.anchor))
            self.update_extra(self.follow)
            self.observer.set_frame(OrbitReferenceFrame(body.anchor))
        else:
            self.ship.anchor.set_frame(AbsoluteReferenceFrame())
            self.observer.set_frame(AbsoluteReferenceFrame())
        if self.fly:
            #Disable fly mode when changing body
            self.toggle_fly_mode()

    def sync_selected(self):
        self.sync_body(self.selected)

    def sync_body(self, body):
        self.sync = body
        self.follow = None
        if self.sync is not None:
            print("Sync", self.sync.get_name())
            self.ship.anchor.set_frame(SynchroneReferenceFrame(body.anchor))
            self.update_extra(self.sync)
            self.observer.set_frame(SynchroneReferenceFrame(body.anchor))
        else:
            self.ship.anchor.set_frame(AbsoluteReferenceFrame())
            self.observer.set_frame(AbsoluteReferenceFrame())
        if self.fly:
            #Disable fly mode when changing body
            self.toggle_fly_mode()

    def track_selected(self):
        self.track_body(self.selected)

    def track_body(self, body):
        if body is not None:
            for camera_controller in self.camera_controllers:
                if camera_controller.camera_mode == CameraController.TRACK:
                    print("Track", body.get_name())
                    self.track = body
                    self.set_camera_controller(camera_controller)
                    break
            else:
                print("ERROR: Can not find track camera")
        else:
            self.track = None
            self.set_default_camera_controller()

    def toggle_track_selected(self):
        if self.track is not None:
            self.track_body(None)
        elif self.selected is not None:
            self.track_body(self.selected)

    def control_selected(self):
        if self.selected is None: return
        if not isinstance(self.selected.orbit.frame, SurfaceReferenceFrame) or not isinstance(self.selected.rotation.frame, SurfaceReferenceFrame):
            print("Can not take control")
            return
        mover = SurfaceBodyMover(self.selected)
        print("Take control")
        self.fly = True
        self.follow = None
        self.sync = None
        self.set_nav(self.nav_controllers[self.CONTROL_NAV], controller=mover)

    def set_surface(self, body, surface_name):
        if body is None:
            body = self.selected
        if body is not None:
            surface = body.find_surface(surface_name)
            if surface is not None:
                body.set_surface(surface)
            else:
                print("ERROR: surface '{}' not found".format(surface_name))

    def update_c_settings(self):
        if c_settings is not None:
            c_settings.min_body_size = settings.min_body_size
            c_settings.min_point_size = settings.min_point_size
            c_settings.min_mag_scale = settings.min_mag_scale
            c_settings.mag_pixel_scale = settings.mag_pixel_scale
            c_settings.lowest_app_magnitude = settings.lowest_app_magnitude
            c_settings.max_app_magnitude = settings.max_app_magnitude
            c_settings.smallest_glare_mag = c_settings.smallest_glare_mag
        if self.c_camera_holder is not None:
            self.c_camera_holder.cos_fov2 = self.observer.cos_fov2

    def update_worlds(self, time, dt):
        self.worlds.update_anchor(time, self.update_id)
        self.worlds.update_anchor_obs(self.observer.anchor, self.update_id)
        self.worlds.update(time, dt)

    @pstat
    def update_universe(self, time, dt):
        traverser = UpdateTraverser(time, self.observer.anchor, settings.lowest_app_magnitude, self.update_id)
        self.universe.anchor.traverse(traverser)
        self.visibles = list(traverser.get_collected())
        self.visibles.sort(key=lambda v: v.z_distance)
        self.controllers_to_update = []
        for controller in self.body_controllers:
            if controller.should_update(time, dt):
                controller.update(time, dt)
                self.controllers_to_update.append(controller)
        #TODO: Should be done in update_extra
        #if self.selected is not None:
        #    self.selected.calc_height_under(self.observer.get_local_position())
        for controller in self.controllers_to_update:
            controller.update_obs(self.observer.anchor)
        for controller in self.controllers_to_update:
            controller.check_visibility(self.observer.anchor.frustum, self.observer.anchor.pixel_size)

    @pstat
    def find_global_light_sources(self):
        position = self.observer.get_local_position()
        traverser = FindLightSourceTraverser(-10, self.observer.get_absolute_position())
        self.universe.anchor.traverse(traverser)
        self.global_light_sources = traverser.get_collected()
        #print("LIGHTS", list(map(lambda x: x.body.get_name(), self.global_light_sources)))

    def _add_extra(self, to_add):
        if to_add is None: return
        #TODO: this should not be done
        if not isinstance(to_add, StellarAnchor): return
        #TODO: There should be a mechanism to retrieve them
        if isinstance(to_add.orbit.frame, BodyReferenceFrame):
            self._add_extra(to_add.orbit.frame.anchor)
        if isinstance(to_add.rotation.frame, BodyReferenceFrame):
            self._add_extra(to_add.rotation.frame.anchor)
        if not to_add in self.extra:
            self.extra.append(to_add)

    def update_extra(self, *args):
        self.extra = []
        #TODO: temporary
        for body in args:
            if body is None: continue
            self._add_extra(body.anchor)
        for anchor in self.extra:
            anchor.update(self.time.time_full, self.update_id)

    def update_extra_observer(self):
        for anchor in self.extra:
            anchor.update_observer(self.observer.anchor, self.update_id)
            anchor.update_id = self.update_id

    @pstat
    def update_magnitudes(self):
        if len(self.global_light_sources) > 0:
            star = self.global_light_sources[0]
        else:
            star = None
        for visible_object in self.visibles:
            visible_object.update_app_magnitude(star)
        for anchor in self.extra:
            #TODO: This will not work for objects in an another system
            anchor.update_app_magnitude(star)

    @pstat
    def update_states(self):
        visibles = []
        resolved = []
        self.visible_scene_anchors = SceneAnchorCollection()
        self.resolved_scene_anchors = SceneAnchorCollection()
        for anchor in self.visibles:
            visible = anchor.resolved or anchor._app_magnitude < settings.lowest_app_magnitude
            if visible:
                visibles.append(anchor)
                self.visible_scene_anchors.add_scene_anchor(anchor.body.scene_anchor)
                if not anchor.was_visible:
                    self.becoming_visibles.append(anchor)
                if anchor.resolved:
                    resolved.append(anchor)
                    self.resolved_scene_anchors.add_scene_anchor(anchor.body.scene_anchor)
            else:
                if anchor.was_visible:
                    self.no_longer_visibles.append(anchor)
            anchor.visible = visible
        for world in self.worlds.worlds:
            resolved.append(world.anchor)
            self.resolved_scene_anchors.add_scene_anchor(world.scene_anchor)
        for anchor in self.old_visibles:
            if not anchor in self.visibles:
                self.no_longer_visibles.append(anchor)
                anchor.was_visible = anchor.visible
                anchor.visible = False
        self.visibles = visibles
        self.resolved = resolved
        for anchor in resolved:
            if not anchor.was_resolved:
                self.becoming_resolved.append(anchor)
        for anchor in self.old_resolved:
            if not anchor in self.resolved:
                self.no_longer_resolved.append(anchor)

    @pstat
    def find_local_lights(self):
        if len(self.global_light_sources) > 0:
            star = self.global_light_sources[0]
        else:
            star = None
        if star is None: return
        for anchor in self.resolved:
            if anchor.content & StellarAnchor.System != 0: continue
            if anchor.content & StellarAnchor.Reflective == 0: continue
            body = anchor.body
            if body.lights is None:
                lights = LightSources()
                body.set_lights(lights)
            light = body.lights.get_light_for(star.body)
            if light is None:
                light = SurrogateLight(star.body, body)
                body.lights.add_light(light)
            light.update_light()

    @pstat
    def find_shadows(self):
        self.shadow_casters = []
        if self.nearest_system is None or not self.nearest_system.anchor.resolved: return
        if len(self.global_light_sources) == 0: return
        reflectives = []
        for anchor in self.resolved:
            if anchor.content & StellarAnchor.System != 0: continue
            if anchor.content & StellarAnchor.Reflective == 0: continue
            anchor.body.start_shadows_update()
            reflectives.append(anchor)

        for light_source in self.global_light_sources:
            for reflective in reflectives:
                surrogate_light = reflective.body.lights.get_light_for(light_source.body)
                if surrogate_light is None: continue
                reflective.body.self_shadows_update(surrogate_light)
                #print("TEST", reflective.body.get_name())
                traverser = FindShadowCastersTraverser(reflective, -surrogate_light.light_direction, surrogate_light.light_distance, light_source.get_bounding_radius())
                self.nearest_system.anchor.traverse(traverser)
                #print("SHADOWS", list(map(lambda x: x.body.get_name(), traverser.anchors)))
                for occluder in traverser.get_collected():
                    if not occluder in self.shadow_casters:
                        self.shadow_casters.append(occluder)
                    occluder.body.add_shadow_target(surrogate_light, reflective.body)

        for reflective in reflectives:
            reflective.body.end_shadows_update()

    @pstat
    def check_scattering(self):
        for anchor in self.resolved:
            #TODO: We need to test the type of the parent anchor
            if anchor.parent is None or anchor.parent.content == ~0: continue
            if not anchor.body.allow_scattering: continue
            primary = anchor.parent.body.primary
            if primary is None: continue
            #TODO: We should not do an explicit test like this here
            if primary.anchor.content & StellarAnchor.System != 0: continue
            if primary.atmosphere is not None and primary.init_components and (anchor.get_local_position() - primary.anchor.get_local_position()).length() < primary.atmosphere.radius:
                primary.atmosphere.add_shape_object(anchor.body.surface)

    @pstat
    def update_height_under(self):
        for anchor in self.resolved:
            anchor._height_under = anchor.body.get_height_under(self.observer.get_local_position())

    @pstat
    def update_scene_anchors(self):
        scene_manager = self.scene_manager
        for newly_visible in self.becoming_visibles:
            newly_visible.body.scene_anchor.create_instance(scene_manager)
        for visible in self.visibles:
            visible.body.scene_anchor.update(scene_manager)
        for old_visible in self.no_longer_visibles:
            old_visible.body.scene_anchor.remove_instance()

    @pstat
    def update_instances(self):
        scene_manager = self.scene_manager

        camera_pos = self.observer.get_local_position()
        camera_rot = self.observer.get_absolute_orientation()
        frustum = self.observer.anchor.rel_frustum
        pixel_size = self.observer.anchor.pixel_size
        for occluder in self.shadow_casters:
        #    occluder.update_scene(self.c_observer)
            occluder.body.scene_anchor.update(scene_manager)
        for newly_visible in self.becoming_visibles:
            #print("NEW VISIBLE", newly_visible.body.get_name())
            self.labels.add_label(newly_visible.body)
            if newly_visible.resolved:
                newly_visible.body.on_resolved(scene_manager)
        for newly_resolved in self.becoming_resolved:
            #print("NEW RESOLVED", newly_resolved.body.get_name())
            newly_resolved.body.on_resolved(scene_manager)
        for old_resolved in self.no_longer_resolved:
            #print("OLD RESOLVED", old_resolved.body.get_name())
            old_resolved.body.on_point(scene_manager)
        for old_visible in self.no_longer_visibles:
            #print("OLD VISIBLE", old_visible.body.get_name())
            self.labels.remove_label(old_visible.body)
            if old_visible.resolved:
                old_visible.body.on_point(self.scene_manager)
        for resolved in self.resolved:
            body = resolved.body
            #TODO: this will update the body's components
            body.update_obs(self.observer)
            body.check_visibility(frustum, pixel_size)
            body.check_and_update_instance(scene_manager, camera_pos, camera_rot)
        self.worlds.update_scene_anchor(scene_manager)
        for controller in self.controllers_to_update:
            controller.check_and_update_instance(camera_pos, camera_rot)

    @pstat
    def update_gui(self):
        self.gui.update_status()

    @pstat
    def update_points(self):
        if settings.render_sprite_points:
            self.pointset.reset()
            self.haloset.reset()
            self.pointset.add_objects(self.scene_manager, self.visible_scene_anchors)
            self.haloset.add_objects(self.scene_manager, self.visible_scene_anchors)
            self.pointset.update()
            self.haloset.update()

    @pstat
    def update_labels(self):
        camera_pos = self.observer.get_local_position()
        camera_rot = self.observer.get_absolute_orientation()
        frustum = self.observer.anchor.rel_frustum
        pixel_size = self.observer.anchor.pixel_size
        self.labels.update_obs(self.observer)
        self.labels.check_visibility(frustum, pixel_size)
        self.labels.check_and_update_instance(self.scene_manager, camera_pos, camera_rot)

    @pstat
    def find_nearest_system(self):
        #First iter over the visible object to have a first closest system
        distance = float('inf')
        closest_visible_system = None
        for visible in self.visibles:
            #TODO: The test to see if the object is a root system is a bit crude...
            if visible.distance_to_obs < distance and visible.parent.content == ~0:
                closest_visible_system = visible
                distance = visible.distance_to_obs
        #Use that system to boostrap the tree traversal
        traverser = FindClosestSystemTraverser(self.observer.anchor, closest_visible_system, distance)
        self.universe.anchor.traverse(traverser)
        closest_system = traverser.closest_system.body if traverser.closest_system is not None else None
        closest_visible_system = closest_visible_system.body if closest_visible_system is not None else None
        return (closest_system, closest_visible_system)

    def update_nearest_system(self, nearest_system, nearest_visible_system):
        if nearest_system != self.nearest_system:
            if nearest_system is not None:
                print("New nearest system:", nearest_system.get_name())
                self.autopilot.stash_position()
                self.nav.stash_position()
                self.ship.anchor.set_absolute_reference_point(nearest_system.anchor.get_absolute_reference_point())
                self.camera_controller.update(self.time.time_full, 0)
                self.observer.change_global(nearest_system.anchor.get_absolute_reference_point())
                self.autopilot.pop_position()
                self.nav.pop_position()
            else:
                print("No more near system")
            self.nearest_system = nearest_system

        nearest_body = None
        distance = float('inf')
        for visible in self.visibles:
            body_distance =  visible.distance_to_obs - visible._height_under
            if body_distance < distance:
                nearest_body = visible.body
                distance = body_distance
        if nearest_body is not None:
            if self.nearest_body != nearest_body:
                self.nearest_body = nearest_body
                print("New nearest visible object:", nearest_body.get_name())
        else:
            distance = None
        return distance

    def time_task(self, task):
        # Reset all states
        self.update_id += 1
        self.to_update_extra = []
        self.old_visibles = self.visibles
        self.visibles = []
        self.becoming_visibles = []
        self.no_longer_visibles = []
        self.old_resolved = self.resolved
        self.resolved = []
        self.becoming_resolved = []
        self.no_longer_resolved = []
        self.update_c_settings()

        #Update time and camera
        if task is not None:
            dt = globalClock.getDt()
        else:
            dt = 0

        self.gui.update()
        self.time.update_time(dt)
        self.update_extra(self.selected, self.follow, self.sync, self.track)
        self.nav.update(self.time.time_full, dt)
        self.camera_controller.update(self.time.time_full, dt)
        self.update_extra_observer()

        update = pstats.levelpstat('update', 'Bodies')
        obs = pstats.levelpstat('obs', 'Bodies')
        visibility = pstats.levelpstat('visibility', 'Bodies')
        instance = pstats.levelpstat('instance', 'Bodies')
        StellarObject.nb_update = 0
        StellarObject.nb_obs = 0
        StellarObject.nb_visibility = 0
        StellarObject.nb_instance = 0

        self.update_universe(self.time.time_full, dt)
        self.update_worlds(self.time.time_full, dt)

        nearest_system, nearest_visible_system = self.find_nearest_system()
        #TODO: anchors should be distance sorted
        distance = self.update_nearest_system(nearest_system, nearest_visible_system)
        self.scene_manager.update_scene_and_camera(distance, self.c_camera_holder)

        self.find_global_light_sources()
        self.update_magnitudes()
        self.update_states()
        self.update_scene_anchors()
        self.find_local_lights()
        self.check_scattering()
        self.update_height_under()

        if self.trigger_check_settings:
            for visible in self.visibles:
                visible.body.check_settings()
            self.worlds.check_settings()
            self.labels.check_settings()
            #TODO: This should be done by a container object
            self.ecliptic_grid.check_settings()
            self.equatorial_grid.check_settings()
            self.trigger_check_settings = False

        self.find_shadows()
        self.update_instances()
        self.scene_manager.build_scene(self.common_state, self.c_camera_holder, self.visible_scene_anchors, self.resolved_scene_anchors)
        self.update_points()
        self.update_labels()
        self.update_gui()

        update.set_level(StellarObject.nb_update)
        obs.set_level(StellarObject.nb_obs)
        visibility.set_level(StellarObject.nb_visibility)
        instance.set_level(StellarObject.nb_instance)

        if settings.color_picking:
            self.oid_texture.clear_image()

        return Task.cont

    def print_debug(self):
        print("Global:")
        print("\tscale", self.scene_manager.scale)
        print("\tPlanes", self.observer.lens.get_near(), self.observer.lens.get_far())
        print("\tFoV", self.observer.lens.get_fov())
        print("Camera:")
        print("\tGlobal position", self.observer.get_absolute_reference_point())
        print("\tLocal position", self.observer.get_local_position())
        print("\tRotation", self.observer.get_absolute_orientation())
        print("\tCamera vector", self.observer.anchor.camera_vector)
        print("\tFrame position", self.observer.get_frame_position(), "rotation", self.observer.get_frame_orientation())
        if self.selected:
            print("Selected:", utils.join_names(self.selected.names))
            print("\tType:", self.selected.__class__.__name__)
            print("\tDistance:", self.selected.anchor.distance_to_obs / units.Km, 'Km')
            print("\tRadius", self.selected.get_apparent_radius(), "Km", "Extend:", self.selected.get_bounding_radius(), "Km", "Visible:", self.selected.anchor.visible, self.selected.anchor.visible_size, "px")
            print("\tApp magnitude:", self.selected.get_app_magnitude(), '(', self.selected.get_abs_magnitude(), ')')
            if isinstance(self.selected, StellarBody):
                print("\tPhase:", self.selected.get_phase())
            print("\tGlobal position", self.selected.anchor.get_absolute_reference_point())
            print("\tLocal position", self.selected.anchor.get_local_position(), '(Frame:', self.selected.anchor.orbit.get_frame_position_at(self.time.time_full), ')')
            print("\tOrientation", self.selected.anchor.get_absolute_orientation())
            print("\tVector to obs", self.selected.anchor.vector_to_obs)
            print("\tVisible:", self.selected.anchor.visible, "Resolved:", self.selected.anchor.resolved, '(', self.selected.anchor.visible_size, ') Override:', self.selected.anchor.visibility_override)
            print("\tUpdate frozen:", self.selected.anchor.update_frozen)
            print("\tOrbit:", self.selected.anchor.orbit.__class__.__name__, self.selected.anchor.orbit.frame)
            print("\tRotation:", self.selected.anchor.rotation.__class__.__name__, self.selected.anchor.rotation.frame)
            if self.selected.label is not None:
                print("\tLabel visible:", self.selected.label.visible)
            if isinstance(self.selected, ReflectiveBody) and self.selected.surface is not None:
                print("\tRing shadow:", self.selected.surface.shadows.ring_shadow is not None)
                #print("\tSphere shadow:", [x.body.get_friendly_name() for x in self.selected.surface.shadows.sphere_shadows.occluders])
            if isinstance(self.selected, StellarBody):
                if self.selected.scene_anchor.scene_scale_factor is not None:
                    print("Scene")
                    print("\tPosition", self.selected.scene_anchor.scene_position, '(Offset:', self.selected.scene_anchor.world_body_center_offset, ')')
                    print("\tScale", self.selected.scene_anchor.scene_scale_factor)
                    print("\tZ distance", self.selected.anchor.z_distance)
                if self.selected.surface is not None and self.selected.surface.instance is not None:
                    print("Instance")
                    print("\tPosition", self.selected.surface.instance.get_pos())
                    print("\tDistance", self.selected.surface.instance.get_pos().length())
                    print("\tScale", self.selected.surface.get_scale() * self.selected.scene_anchor.scene_scale_factor)
                    print("\tInstance Ready:", self.selected.surface.instance_ready)
                    if self.selected.atmosphere is not None:
                        pass#print("\tAtm size", self.selected.atmosphere.get_pixel_height())
                    if self.selected.surface.shape.patchable:
                        print("Patches:", len(self.selected.surface.shape.patches))
                else:
                    print("\tPoint")
                projection = self.selected.cartesian_to_spherical(self.observer.get_local_position())
                xy = self.selected.spherical_to_xy(projection)
                print("\tLongLat:", projection[0] * 180 / pi, projection[1] * 180 / pi, projection[2], "XY:", xy[0], xy[1])
                height = self.selected.anchor._height_under
                print("\tHeight:", height, "Delta:", height - self.selected.get_apparent_radius(), "Alt:", (self.selected.anchor.distance_to_obs - height))
                if self.selected.surface is not None and self.selected.surface.shape.patchable:
                    x = projection[0] / pi / 2 + 0.5
                    y = 1.0 - (projection[1] / pi + 0.5)
                    coord = self.selected.surface .global_to_shape_coord(x, y)
                    patch = self.selected.surface.shape.find_patch_at(coord)
                    if patch is not None:
                        print("\tID:", patch.str_id())
                        print("\tLOD:", patch.lod)
                        print("\tView:", patch.quadtree_node.patch_in_view)
                        print("\tLength:", patch.quadtree_node.length, "App:", patch.quadtree_node.apparent_size)
                        print("\tCoord:", coord, "Distance:", patch.quadtree_node.distance)
                        print("\tflat:", patch.flat_coord)
                        if patch.instance is not None:
                            print("\tPosition:", patch.instance.get_pos(), patch.instance.get_pos(render))
                            print("\tDistance:", patch.instance.get_pos(render).length())
                            print("\tScale:", patch.instance.get_scale())
                            if patch.quadtree_node.offset is not None:
                                print("\tOffset:", patch.quadtree_node.offset, patch.quadtree_node.offset * self.selected.get_apparent_radius())
            else:
                if self.selected.scene_anchor.scene_scale_factor is not None:
                    print("Scene:")
                    print("\tPosition:", self.selected.scene_anchor.scene_position)
                    print("\tOrientation:", self.selected.scene_anchor.scene_orientation)
                    print("\tScale:", self.selected.scene_anchor.scene_scale_factor)

    def init_universe(self):
        pass

    def load_universe(self):
        pass

    def start_universe(self):
        pass
