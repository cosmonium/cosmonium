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

from __future__ import print_function
from __future__ import absolute_import

from direct.showbase.ShowBase import ShowBase
from panda3d.core import loadPrcFileData, loadPrcFile, Filename, WindowProperties, PandaSystem, PStatClient
from panda3d.core import Texture, CardMaker
from panda3d.core import AmbientLight
from panda3d.core import LightRampAttrib, AntialiasAttrib
from panda3d.core import LColor, NodePath, PerspectiveLens, DepthTestAttrib
from panda3d.core import Camera

from direct.task.Task import Task

import logging
import gettext

from .parsers.configparser import configParser
from .foundation import BaseObject, CompositeObject
from .dircontext import defaultDirContext
from .opengl import request_opengl_config, check_opengl_config, create_main_window, check_and_create_rendering_buffers
from .renderers.renderer import Renderer
from .stellarobject import StellarObject
from .systems import StellarSystem, SimpleSystem
from .bodies import StellarBody, ReflectiveBody
from .anchors import AnchorBase
from .anchors import UpdateTraverser, FindClosestSystemTraverser, FindLightSourceTraverser, FindObjectsInVisibleResolvedSystemsTraverser, FindShadowCastersTraverser
from .universe import Universe
from .annotations import Grid
from .astro.frame import BodyReferenceFrame, SolBarycenter
from .astro.frame import J2000EquatorialReferenceFrame, J2000EclipticReferenceFrame
from .astro.frame import AbsoluteReferenceFrame, SynchroneReferenceFrame, RelativeReferenceFrame
from .astro.frame import SurfaceReferenceFrame
from .celestia.cel_url import CelUrl
from .celestia import cel_parser, cel_engine

#Initialiser parsers
from .parsers import parsers

from .bodyclass import bodyClasses
from .autopilot import AutoPilot
from .camera import CameraHolder, CameraController, FixedCameraController, TrackCameraController, LookAroundCameraController, FollowCameraController
from .timecal import Time
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
        self.keystrokes = {}
        self.gui = None #TODO: Temporary for keystroke below
        self.observer = None #TODO: For window_event below
        self.wireframe = False
        self.wireframe_filled = False
        self.trigger_check_settings = True
        self.request_fullscreen = False

        configParser.load()
        self.init_lang()
        self.print_info()
        self.panda_config()
        ShowBase.__init__(self, windowType='none')
        if not self.app_config.test_start:
            create_main_window(self)
            check_opengl_config(self)
            self.create_additional_display_regions()
            self.cam.node().set_camera_mask(BaseObject.DefaultCameraMask)
        else:
            self.buttonThrowers = [NodePath('dummy')]
            self.camera = NodePath('dummy')
            self.cam = self.camera.attach_new_node('dummy')
            self.camLens = PerspectiveLens()
            settings.shader_version = 130

        #TODO: should find a better way than patching classes...
        BaseObject.context = self
        YamlModuleParser.app = self
        BodyController.context = self

        self.setBackgroundColor(0, 0, 0, 1)
        self.disableMouse()
        self.render_textures = check_and_create_rendering_buffers(self)
        cache.init_cache()
        self.register_events()

        self.world = self.render.attachNewNode("world")
        self.annotation = self.render.attachNewNode("annotation")
        self.annotation.hide(BaseObject.AllCamerasMask)
        self.annotation.show(BaseObject.DefaultCameraMask)

        self.world.setShaderAuto()
        self.annotation.setShaderAuto()

        workers.asyncTextureLoader = workers.AsyncTextureLoader(self)
        workers.syncTextureLoader = workers.SyncTextureLoader()

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
        request_opengl_config(data)
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

    def keystroke_event(self, keyname):
        #TODO: Should be better isolated
        if self.gui is not None and self.gui.popup_menu: return
        callback_data = self.keystrokes.get(keyname, None)
        if callback_data is not None:
            (method, extraArgs) = callback_data
            method(*extraArgs)

    def accept(self, event, method, extraArgs=[], direct=False):
        if len(event) == 1 and not direct:
            self.keystrokes[event] = [method, extraArgs]
        else:
            ShowBase.accept(self, event, method, extraArgs=extraArgs)

    def ignore(self, event):
        if len(event) == 1:
            if event in self.keystrokes:
                del self.keystrokes[event]
        else:
            ShowBase.ignore(self, event)

    def register_events(self):
        if not self.app_config.test_start:
            self.buttonThrowers[0].node().setKeystrokeEvent('keystroke')
            self.accept(self.win.getWindowEvent(), self.window_event)
        self.accept('keystroke', self.keystroke_event)
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
            self.render.setShaderInput("near_plane_height", self.observer.height / self.observer.tan_fov2)
            self.render.setShaderInput("pixel_size", self.observer.pixel_size)
        if self.gui is not None:
            self.gui.update_size(width, height)
        if settings.color_picking and self.oid_texture is not None:
            self.oid_texture.clear()
            self.oid_texture.setup_2d_texture(width, height, Texture.T_unsigned_byte, Texture.F_rgba8)
            self.oid_texture.set_clear_color(LColor(0, 0, 0, 0))

    def connect_pstats(self):
        PStatClient.connect()

    def toggle_wireframe(self):
        self.world.clear_render_mode()
        if self.wireframe_filled:
            self.wireframe_filled = False
            self.wireframe = False
        self.wireframe = not self.wireframe
        if self.wireframe:
            self.world.set_render_mode_wireframe()

    def toggle_filled_wireframe(self):
        self.world.clear_render_mode()
        if self.wireframe:
            self.wireframe = False
            self.wireframe_filled = False
        self.wireframe_filled = not self.wireframe_filled
        if self.wireframe_filled:
            self.world.set_render_mode_filled_wireframe(settings.wireframe_fill_color)

    def save_screenshot(self, filename=None):
        if filename is None:
            filename = self.screenshot(namePrefix=settings.screenshot_path)
        else:
            self.screenshot(namePrefix=filename, defaultFilename=False)
        if filename is not None:
            print("Saving screenshot into", filename)
        else:
            print("Could not save filename")
            if self.gui is not None:
                self.gui.update_info("Could not save filename", duration=1.0, fade=1.0)

class Cosmonium(CosmoniumBase):
    FREE_NAV = 0
    WALK_NAV = 1
    CONTROL_NAV = 2

    def __init__(self):
        CosmoniumBase.__init__(self)

        mesh.init_mesh_loader()
        fontsManager.register_fonts(defaultDirContext.find_font('dejavu'))

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
        self.visibles = []
        self.light_sources = []
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

        self.universe = Universe(self)

        if settings.color_picking:
            self.oid_texture = Texture()
            self.oid_texture.setup_2d_texture(settings.win_width, settings.win_height, Texture.T_unsigned_byte, Texture.F_rgba8)
            self.oid_texture.set_clear_color(LColor(0, 0, 0, 0))
            self.render.set_shader_input("oid_store", self.oid_texture)
        else:
            self.oid_texture = None
        self.observer = CameraHolder(self.camera, self.camLens)
        self.autopilot = AutoPilot(self)
        self.mouse = Mouse(self, self.oid_texture)
        if self.near_cam is not None:
            self.observer.add_linked_cam(self.near_cam)

        self.add_camera_controller(FixedCameraController())
        self.add_camera_controller(TrackCameraController())
        self.add_camera_controller(LookAroundCameraController())
        self.add_camera_controller(FollowCameraController())
        self.observer.init()

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

        self.universe.recalc_recursive()

        self.splash.set_text("Building tree...")
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
        if self.gui is None:
            self.gui = Gui(self, self.time, self.observer, self.mouse, self.autopilot)
            self.mouse.set_ui(self.gui)

        # Use the first of each controllers as default
        self.set_nav(self.nav_controllers[0])
        self.set_ship(self.ships[0])
        self.set_camera_controller(self.camera_controllers[0])

        self.nav.register_events(self)
        self.gui.register_events(self)

        self.renderer = Renderer(self)
        
        render.setAntialias(AntialiasAttrib.MMultisample)
        self.setFrameRateMeter(False)
        self.render.set_attrib(DepthTestAttrib.make(DepthTestAttrib.M_less_equal))

        self.set_ambient(settings.global_ambient)

        self.equatorial_grid = Grid("Equatorial", J2000EquatorialReferenceFrame.orientation, LColor(0.28,  0.28,  0.38, 1))
        self.equatorial_grid.set_shown(settings.show_equatorial_grid)

        self.ecliptic_grid = Grid("Ecliptic", J2000EclipticReferenceFrame.orientation, LColor(0.28,  0.28,  0.38, 1))
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
        self.near_cam.node().set_camera_mask(BaseObject.NearCameraMask)
        self.near_cam.node().get_lens().set_near_far(units.m /settings.scale, float('inf'))

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
            position = self.camera_controller.get_pos()
            rotation = self.camera_controller.get_rot()
            self.camera_controller.deactivate()
        else:
            position = None
            rotation = None
        self.camera_controller = camera_controller
        if camera_controller.require_target():
            self.camera_controller.set_target(self.track)
        self.camera_controller.activate(self.observer, self.ship)
        if position is not None and rotation is not None:
            self.camera_controller.set_pos(position)
            self.camera_controller.set_rot(rotation)
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
            self.universe.remove_component(self.ship)
            self.autopilot.set_ship(None)
            self.nav.set_ship(None)
            self.camera_controller.set_reference_point(None)
        old_ship = self.ship
        self.ship = ship
        if self.ship is not None:
            self.autopilot.set_ship(self.ship)
            self.nav.set_ship(self.ship)
            if old_ship is not None:
                self.ship.copy(old_ship)
            if self.camera_controller is not None:
                if self.ship.supports_camera_mode(self.camera_controller.camera_mode):
                    self.camera_controller.set_reference_point(self.ship)
                    self.camera_controller.set_camera_hints(**self.ship.get_camera_hints())
                else:
                    #Current camera controller is not supported by the ship, switch to the first one supported
                    for camera_controller in self.camera_controllers:
                        if self.ship.supports_camera_mode(camera_controller.camera_mode):
                            #Apply the current camera controller to be able to switch
                            self.camera_controller.set_reference_point(self.ship)
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
        if self.nav is not None:
            self.nav.remove_events(self)
        self.nav = nav
        if self.nav is not None:
            self.nav.init(self, self.observer, self.camera_controller, self.ship)
            self.nav.register_events(self)
            if nav.require_target():
                self.nav.set_target(target)
            if nav.require_controller():
                self.nav.set_controller(controller)
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
            self.world.clearAttrib(LightRampAttrib.getClassType())
        elif self.hdr == 1:
            self.world.setAttrib(LightRampAttrib.makeHdr0())
        elif self.hdr == 2:
            self.world.setAttrib(LightRampAttrib.makeHdr1())
        elif self.hdr == 3:
            self.world.setAttrib(LightRampAttrib.makeHdr2())

    def save_screenshot_no_annotation(self):
        state = self.gui.hide_with_state()
        self.annotation.hide()
        base.graphicsEngine.renderFrame()
        filename = self.screenshot(namePrefix=settings.screenshot_path)
        self.gui.show_with_state(state)
        self.annotation.show()
        if filename is not None:
            print("Saving screenshot without annotation into", filename)
        else:
            print("Could not save filename")

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
        self.ship.set_frame(AbsoluteReferenceFrame())
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
            self.world.clearLight(self.globalAmbientPath)
            self.globalAmbientPath.removeNode()
        self.globalAmbient=AmbientLight('globalAmbient')
        if settings.srgb:
            corrected_ambient = pow(settings.global_ambient, 2.2)
        else:
            corrected_ambient = settings.global_ambient
        settings.corrected_global_ambient = corrected_ambient
        print("Ambient light level:  %.2f" % settings.global_ambient)
        self.gui.update_info("Ambient light level:  %.2f" % settings.global_ambient, duration=0.5, fade=1.0)
        self.globalAmbient.setColor((corrected_ambient, corrected_ambient, corrected_ambient, 1))
        self.globalAmbientPath = self.world.attachNewNode(self.globalAmbient)
        self.world.setLight(self.globalAmbientPath)
        self.render.set_shader_input("global_ambient", settings.corrected_global_ambient)
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
            self.ship.set_frame(RelativeReferenceFrame(body, body.anchor.orbit.frame))
            self.update_extra(self.follow)
            self.observer.set_frame(RelativeReferenceFrame(body, body.anchor.orbit.frame))
        else:
            self.ship.set_frame(AbsoluteReferenceFrame())
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
            self.ship.set_frame(SynchroneReferenceFrame(body))
            self.update_extra(self.sync)
            self.observer.set_frame(SynchroneReferenceFrame(body))
        else:
            self.ship.set_frame(AbsoluteReferenceFrame())
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

    @pstat
    def update_universe(self, time, dt):
        frustum = self.observer.rel_frustum
        pixel_size = self.observer.pixel_size
        traverser = UpdateTraverser(time, self.observer, settings.lowest_app_magnitude)
        self.universe.anchor.traverse(traverser)
        self.visibles = traverser.visibles
        #TODO: Temporary hack until the constellations, asterisms, .. are moved into a proper container
        CompositeObject.update(self.universe, time, dt)
        CompositeObject.update_obs(self.universe, self.observer)
        CompositeObject.check_visibility(self.universe, frustum, pixel_size)
        self.controllers_to_update = []
        for controller in self.body_controllers:
            if controller.should_update(time, dt):
                controller.update(time, dt)
                self.controllers_to_update.append(controller)
        #TODO: Should be done in update_extra
        #if self.selected is not None:
        #    self.selected.calc_height_under(self.observer.get_camera_pos())
        for controller in self.controllers_to_update:
            controller.update_obs(self.observer)
        for controller in self.controllers_to_update:
            controller.check_visibility(frustum, pixel_size)

    def find_light_sources(self):
        position = self.observer._global_position + self.observer._local_position
        traverser = FindLightSourceTraverser(-10, position)
        self.universe.anchor.traverse(traverser)
        self.light_sources = traverser.anchors
        #print("LIGHTS", list(map(lambda x: x.body.get_name(), traverser.anchors)))

    def update_ship(self, time, dt):
        frustum = self.observer.rel_frustum
        pixel_size = self.observer.pixel_size
        self.ship.update(time, dt)
        self.ship.update_obs(self.observer)
        self.ship.check_visibility(frustum, pixel_size)

    def _add_extra(self, to_add):
        if to_add is None: return
        if isinstance(to_add, SolBarycenter): return
        if to_add is self.universe: return
        self._add_extra(to_add.parent)
        #TODO: There should be a mechanism to retrieve them
        if isinstance(to_add.anchor.orbit.frame, BodyReferenceFrame):
            self._add_extra(to_add.anchor.orbit.frame.body)
        if isinstance(to_add.anchor.rotation.frame, BodyReferenceFrame):
            self._add_extra(to_add.anchor.rotation.frame.body)
        if not to_add in self.extra:
            self.extra.append(to_add)

    def update_extra(self, *args):
        self.extra = []
        for body in args:
            self._add_extra(body)
        for body in self.extra:
            body.anchor.update(self.time.time_full)

    def update_extra_observer(self):
        for body in self.extra:
            body.anchor.update_observer(self.observer)

    def update_magnitudes(self):
        if len(self.light_sources) > 0:
            star = self.light_sources[0]
        else:
            star = None
        for visible_object in self.visibles:
            visible_object.update_app_magnitude(star)

    def find_orbits(self):
        #TODO: This is a bit crappy, this whole method should be moved in the renderer
        top_systems = []
        for visible in self.visibles:
            #TODO: The test to see if the object is a root system is a bit crude...
            if visible.resolved and visible.content & AnchorBase.System != 0 and visible.parent.content == ~1:
                top_systems.append(visible)
        traverser = FindObjectsInVisibleResolvedSystemsTraverser()
        for system in top_systems:
            system.traverse(traverser)
        self.orbits = list(map(lambda anchor: anchor.body, traverser.anchors))

    def update_orbits(self):
        self.renderer.add_orbits(self.orbits)

    def find_shadows(self):
        self.shadow_casters = []
        if self.nearest_system is None or not self.nearest_system.anchor.resolved: return
        for visible_object in self.visibles:
            if not visible_object.resolved: continue
            if visible_object.content & AnchorBase.System != 0: continue
            if visible_object.content & AnchorBase.Reflective == 0: continue
            visible_object.body.start_shadows_update()
            #print("TEST", visible_object.body.get_name())
            traverser = FindShadowCastersTraverser(visible_object, visible_object.vector_to_star, visible_object.distance_to_star, visible_object.star.get_apparent_radius())
            self.nearest_system.anchor.traverse(traverser)
            #print("SHADOWS", list(map(lambda x: x.body.get_name(), traverser.anchors)))
            for occluder in traverser.anchors:
                if not occluder in self.shadow_casters:
                    self.shadow_casters.append(occluder)
                occluder.body.add_shadow_target(visible_object.body)
            visible_object.body.end_shadows_update()

    def check_scattering(self):
        for visible_object in self.visibles:
            if not visible_object.resolved: continue
            primary = visible_object.parent.body.primary
            if primary is None: continue
            if primary.atmosphere is not None and primary.init_components and (visible_object._local_position - primary.anchor._local_position).length() < primary.atmosphere.radius:
                primary.atmosphere.add_shape_object(visible_object.body.surface)

    def update_height_under(self):
        for visible_object in self.visibles:
            if not visible_object.resolved: continue
            visible_object._height_under = visible_object.body.get_height_under(self.observer._local_position)

    @pstat
    def update_instances(self):
        #TODO: Temporary hack until the constellations, asterisms, .. are moved into a proper container
        CompositeObject.check_and_update_instance(self.universe, self.observer.get_camera_pos(), self.observer.get_camera_rot())
        for occluder in self.shadow_casters:
            occluder.update_scene()
        for visible in self.visibles:
            visible.update_scene()
            self.renderer.add_object(visible.body)
        self.renderer.render(self.observer)
        self.ship.check_and_update_instance(self.observer.get_camera_pos(), self.observer.get_camera_rot())
        for controller in self.controllers_to_update:
            controller.check_and_update_instance(self.observer.get_camera_pos(), self.observer.get_camera_rot())
        self.gui.update_status()

    def find_nearest_system(self):
        #First iter over the visible object to have a first closest system
        distance = float('inf')
        closest_system = None
        for visible in self.visibles:
            #TODO: The test to see if the object is a root system is a bit crude...
            if visible.distance_to_obs < distance and visible.parent.content == ~1:
                closest_system = visible.body
                distance = visible.distance_to_obs
        #Use that system to boostrap the tree traversal
        traverser = FindClosestSystemTraverser(self.observer, closest_system, distance)
        self.universe.anchor.traverse(traverser)
        return (traverser.closest_system, closest_system)

    def update_nearest_system(self, nearest_system, nearest_visible_system):
        if nearest_system != self.nearest_system:
            if nearest_system is not None:
                print("New nearest system:", nearest_system.get_name())
                self.autopilot.stash_position()
                self.nav.stash_position()
                self.ship.change_global(nearest_system.get_global_position())
                self.camera_controller.update(self.time.time_full, 0)
                self.observer.change_global(nearest_system.get_global_position())
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
        if nearest_body is not None and self.nearest_body != nearest_body:
            self.nearest_body = nearest_body
            print("New nearest visible object:", nearest_body.get_name())
        if settings.auto_scale:
            if nearest_body is None:
                settings.scale = settings.max_scale
            elif distance is None:
                settings.scale = settings.max_scale
            elif distance <= 0:
                settings.scale = settings.min_scale
            elif distance < settings.max_scale * 10:
                settings.scale = max(distance / 10, settings.min_scale)
            else:
                settings.scale = settings.max_scale
            if settings.set_frustum:
                #near_plane = min(distance / settings.scale / 2.0, settings.near_plane)
                if settings.scale < 1.0:
                    near_plane = settings.scale
                else:
                    near_plane = settings.near_plane
                self.observer.update_near_plane(near_plane)

    def time_task(self, task):
        # Reset all states
        self.to_update_extra = []
        self.renderer.reset()

        #Update time and camera
        if task is not None:
            dt = globalClock.getDt()
        else:
            dt = 0

        self.gui.update()
        self.time.update_time(dt)
        self.update_extra(self.selected, self.follow, self.sync, self.track)
        self.nav.update(self.time.time_full, dt)
        self.update_ship(self.time.time_full, dt)
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
        self.find_light_sources()
        self.update_magnitudes()
        self.find_orbits()
        self.check_scattering()
        self.update_height_under()

        nearest_system, nearest_visible_system = self.find_nearest_system()
        self.update_nearest_system(nearest_system, nearest_visible_system)

        if self.trigger_check_settings:
            for visible in self.visibles:
                visible.body.check_settings()
            for orbit in self.orbits:
                orbit.check_settings()
            #TODO: Temporary hack until the constellations, asterisms, .. are moved into a proper container
            CompositeObject.check_settings(self.universe)
            #TODO: This should be done by a container object
            self.ecliptic_grid.check_settings()
            self.equatorial_grid.check_settings()
            self.trigger_check_settings = False

        self.update_orbits()
        self.find_shadows()
        self.update_instances()

        update.set_level(StellarObject.nb_update)
        obs.set_level(StellarObject.nb_obs)
        visibility.set_level(StellarObject.nb_visibility)
        instance.set_level(StellarObject.nb_instance)

        if settings.color_picking:
            self.oid_texture.clear_image()

        return Task.cont

    def print_debug(self):
        print("Global:")
        print("\tscale", settings.scale)
        print("\tPlanes", self.camLens.get_near(), self.camLens.get_far())
        print("\tFoV", self.camLens.get_fov())
        print("Camera:")
        print("\tGlobal position", self.observer.camera_global_pos)
        print("\tLocal position", self.observer.get_camera_pos())
        print("\tRotation", self.observer.get_camera_rot())
        print("\tFrame position", self.observer._frame_position, "rotation", self.observer._frame_rotation)
        if self.selected:
            print("Selected:", utils.join_names(self.selected.names))
            print("\tType:", self.selected.__class__.__name__)
            print("\tDistance:", self.selected.anchor.distance_to_obs / units.Km, 'Km')
            print("\tRadius", self.selected.get_apparent_radius(), "Km", "Extend:", self.selected.get_extend(), "Km", "Visible:", self.selected.anchor.visible, self.selected.anchor.visible_size, "px")
            print("\tApp magnitude:", self.selected.get_app_magnitude(), '(', self.selected.get_abs_magnitude(), ')')
            if isinstance(self.selected, StellarBody):
                print("\tPhase:", self.selected.get_phase())
            print("\tGlobal position", self.selected.get_global_position())
            print("\tLocal position", self.selected.get_local_position(), '(Frame:', self.selected.anchor.orbit.get_frame_position_at(self.time.time_full), ')')
            print("\tRotation", self.selected.get_abs_rotation())
            print("\tOrientation", self.selected.anchor._orientation)
            print("\tVector to obs", self.selected.anchor.vector_to_obs)
            print("\tVector to star", self.selected.anchor.vector_to_star, "Distance:", self.selected.anchor.distance_to_star)
            print("\tVisible:", self.selected.anchor.visible, "Resolved:", self.selected.anchor.resolved, '(', self.selected.anchor.visible_size, ')')
            print("\tUpdate frozen:", self.selected.anchor.update_frozen)
            print("\tOrbit:", self.selected.anchor.orbit.__class__.__name__, self.selected.anchor.orbit.frame)
            if self.selected.label is not None:
                print("\tLabel visible:", self.selected.label.visible)
            if isinstance(self.selected, ReflectiveBody) and self.selected.surface is not None:
                print("\tRing shadow:", self.selected.surface.shadows.ring_shadow is not None)
                print("\tSphere shadow:", [x.body.get_friendly_name() for x in self.selected.surface.shadows.sphere_shadows.occluders])
            if isinstance(self.selected, StellarBody):
                if self.selected.anchor.scene_scale_factor is not None:
                    print("Scene")
                    print("\tPosition", self.selected.anchor.scene_position, '(Offset:', self.selected.world_body_center_offset, ') distance:', self.selected.anchor.scene_distance)
                    print("\tOrientation", self.selected.anchor.scene_orientation)
                    print("\tScale", self.selected.anchor.scene_scale_factor, '(', self.selected.surface.get_scale() * self.selected.anchor.scene_scale_factor, ')')
                if self.selected.surface is not None and self.selected.surface.instance is not None:
                    print("Instance")
                    print("\tPosition", self.selected.surface.instance.get_pos())
                    print("\tDistance", self.selected.surface.instance.get_pos().length())
                    print("\tInstance Ready:", self.selected.surface.instance_ready)
                    if self.selected.atmosphere is not None:
                        pass#print("\tAtm size", self.selected.atmosphere.get_pixel_height())
                    if self.selected.surface.shape.patchable:
                        print("Patches:", len(self.selected.surface.shape.patches))
                else:
                    print("\tPoint")
                projection = self.selected.cartesian_to_spherical(self.observer.get_camera_pos())
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
                        print("\tView:", patch.patch_in_view)
                        print("\tLength:", patch.get_patch_length(), "App:", patch.apparent_size)
                        print("\tCoord:", coord, "Distance:", patch.distance)
                        print("\tMean:", patch.mean_radius)
                        print("\tflat:", patch.flat_coord)
                        if patch.instance is not None:
                            print("\tPosition:", patch.instance.get_pos(), patch.instance.get_pos(self.world))
                            print("\tDistance:", patch.instance.get_pos(self.world).length())
                            print("\tScale:", patch.instance.get_scale())
                            if patch.offset is not None:
                                print("\tOffset:", patch.offset, patch.offset * self.selected.get_apparent_radius())
            else:
                if self.selected.anchor.scene_scale_factor is not None:
                    print("Scene:")
                    print("\tPosition:", self.selected.anchor.scene_position, self.selected.anchor.scene_distance)
                    print("\tOrientation:", self.selected.anchor.scene_orientation)
                    print("\tScale:", self.selected.anchor.scene_scale_factor)

    def init_universe(self):
        pass

    def load_universe(self):
        pass

    def start_universe(self):
        pass
