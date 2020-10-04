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
from .foundation import BaseObject
from .dircontext import defaultDirContext
from .opengl import request_opengl_config, check_opengl_config, create_main_window, check_and_create_rendering_buffers
from .stellarobject import StellarObject
from .bodies import StellarBody, ReflectiveBody
from .systems import StellarSystem, SimpleSystem
from .universe import Universe
from .annotations import Grid
from .pointsset import PointsSet
from .sprites import RoundDiskPointSprite, GaussianPointSprite, ExpPointSprite, MergeSprite
from .astro.frame import J2000EquatorialReferenceFrame, J2000EclipticReferenceFrame
from .astro.frame import AbsoluteReferenceFrame, SynchroneReferenceFrame, RelativeReferenceFrame
from .astro.frame import SurfaceReferenceFrame
from .celestia.cel_url import CelUrl

#Initialiser parsers
from .parsers import parsers

from .bodyclass import bodyClasses
from .autopilot import AutoPilot
from .camera import CameraHolder, FixedCameraController, LookAroundCameraController, FollowCameraController
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

from math import pi
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

    def load_lang(self, domain, locale):
        return gettext.translation(domain, locale, fallback=True)

    def init_lang(self):
        self.translation = self.load_lang('cosmonium', 'locale')
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
                    if self.gui is not None: self.gui.update_info("Press <Alt-Enter> to leave fullscreen mode", 0.5, 2.0)
            else:
                if self.gui is not None: self.gui.update_info("Could not switch to fullscreen mode", 0.5, 2.0)
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
                self.gui.update_info("Could not save filename", 1.0, 1.0)

class Cosmonium(CosmoniumBase):
    def __init__(self):
        CosmoniumBase.__init__(self)

        mesh.init_mesh_loader()
        fontsManager.register_fonts(defaultDirContext.find_font('dejavu'))

        self.over = None
        self.patch = None
        self.selected = None
        self.follow = None
        self.sync = None
        self.track = None
        self.fly = False
        self.nav = None
        self.gui = None
        self.last_visibles = []
        self.visibles = []
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
        self.controllers = []
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
        self.add_camera_controller(LookAroundCameraController())
        self.add_camera_controller(FollowCameraController())
        self.observer.init()

        if self.nav is None:
            self.nav = FreeNav()
        ship = NoShip()
        self.set_camera_controller(self.camera_controllers[0])
        self.add_ship(ship)
        self.set_ship(ship)

        self.splash = Splash() if not self.app_config.test_start else NoSplash()

        if not settings.debug_sync_load:
            self.async_start = workers.AsyncMethod("async_start", self, self.load_task, self.configure_scene)
        else:
            self.load_task()
            self.configure_scene()

    def load_task(self):
        self.init_universe()

        self.load_universe()

        self.universe.recalc_recursive()

        self.splash.set_text("Building octree...")
        self.universe.create_octree()
        #self.universe.octree.print_summary()
        #self.universe.octree.print_stats()

        self.sun = self.universe.find_by_path('Sol')
        if not self.sun:
            print("Could not find Sun")
        self.splash.set_text("Done")

    def configure_scene(self):
        #Force frame update to render the last status of the splash screen
        base.graphicsEngine.renderFrame()
        self.splash.close()
        if self.gui is None:
            self.gui = Gui(self, self.time, self.observer, self.mouse, self.nav, self.autopilot)
        self.set_nav(self.nav)

        self.nav.register_events(self)
        self.gui.register_events(self)

        self.pointset = PointsSet(use_sprites=True, sprite=GaussianPointSprite(size=16, fwhm=8))
        if settings.render_sprite_points:
            self.pointset.instance.reparentTo(self.world)

        self.haloset = PointsSet(use_sprites=True, sprite=ExpPointSprite(size=256, max_value=0.6), background=settings.halo_depth)
        if settings.render_sprite_points:
            self.haloset.instance.reparentTo(self.world)

        render.setAntialias(AntialiasAttrib.MMultisample)
        self.setFrameRateMeter(False)
        self.render.set_attrib(DepthTestAttrib.make(DepthTestAttrib.M_less_equal))

        self.set_ambient(settings.global_ambient)

        self.equatorial_grid = Grid("Equatorial", J2000EquatorialReferenceFrame.orientation, LColor(0.28,  0.28,  0.38, 1))
        self.equatorial_grid.set_shown(settings.show_equatorial_grid)

        self.ecliptic_grid = Grid("Ecliptic", J2000EclipticReferenceFrame.orientation, LColor(0.28,  0.28,  0.38, 1))
        self.ecliptic_grid.set_shown(settings.show_ecliptic_grid)

        self.time.set_current_date()

        for controller in self.controllers:
            controller.init()

        self.universe.first_update()
        self.camera_controller.update(self.time.time_full, 0)
        self.universe.first_update_obs(self.observer)
        self.window_event(None)
        self.time_task(None)

        taskMgr.add(self.time_task, "time-task")

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
        self.controllers.append(controller)

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

    def set_camera_controller(self, camera_controller):
        if self.camera_controller is not None:
            self.camera_controller.deactivate()
        self.camera_controller = camera_controller
        self.camera_controller.activate(self.observer, self.ship)
        if self.ship is not None:
            self.camera_controller.set_camera_hints(**self.ship.get_camera_hints())
        print("Switching camera to", self.camera_controller.get_name())

    def add_ship(self, ship):
        self.ships.append(ship)

    def set_ship(self, ship):
        if self.ship is not None:
            self.universe.remove_component(self.ship)
            self.autopilot.set_ship(None)
            self.nav.set_ship(None)
            self.camera_controller.set_reference_point(None)
        old_ship = self.ship
        self.ship = ship
        if self.ship is not None:
            self.universe.add_component(self.ship)
            self.autopilot.set_ship(self.ship)
            self.nav.set_ship(self.ship)
            if old_ship is not None:
                self.ship.copy(old_ship)
            if self.ship.supports_camera_mode(self.camera_controller.camera_mode):
                self.camera_controller.set_reference_point(self.ship)
                self.camera_controller.set_camera_hints(**self.ship.get_camera_hints())
            else:
                #Current camera controller is not supported by the ship, switch to the first one supported
                for camera_controller in self.camera_controllers:
                    if self.ship.supports_camera_mode(camera_controller.camera_mode):
                        self.set_camera_controller(camera_controller)
                        break
                else:
                    print("ERROR: No camera controller supported by this ship")

    def set_nav(self, nav):
        if self.nav is not None:
            self.nav.remove_events(self)
        self.nav = nav
        if self.nav is not None:
            self.nav.init(self, self.observer, self.ship, self.gui)
            self.nav.register_events(self)

    def toggle_fly_mode(self):
        if not self.fly:
            if self.selected is not None:
                print("Fly mode")
                self.fly = True
                self.follow = None
                self.sync = None
                self.set_nav(WalkNav(self.selected))
        else:
            print("Free mode")
            self.fly = False
            self.set_nav(FreeNav())

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
            body.set_selected(True)
        self.selected = body
        if self.fly:
            #Disable fly mode when changing body
            self.toggle_fly_mode()

    def select_home(self):
        self.select_body(self.sun)

    def reset_nav(self):
        print("Reset nav")
        self.follow = None
        self.ship.set_frame(AbsoluteReferenceFrame())
        self.observer.set_frame(AbsoluteReferenceFrame())
        self.sync = None
        if self.fly:
            #Disable fly mode when changing body
            self.toggle_fly_mode()
        self.track = None
        self.autopilot.reset()

    def run_script(self, sequence):
        if self.current_sequence is not None:
            self.current_sequence.pause()
        self.current_sequence = sequence
        if self.current_sequence is not None:
            self.current_sequence.start()
        return self.current_sequence is not None

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
        self.gui.update_info("Cancel", 0.5, 1.0)
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
        self.gui.update_info(_("Magnitude limit:  %.1f") % settings.lowest_app_magnitude, 0.5, 1.0)
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
    
    def toggle_grid_equatorial(self):
        settings.show_equatorial_grid = not settings.show_equatorial_grid
        self.equatorial_grid.set_shown(settings.show_equatorial_grid)
        configParser.save()

    def toggle_grid_ecliptic(self):
        settings.show_ecliptic_grid = not settings.show_ecliptic_grid
        self.ecliptic_grid.set_shown(settings.show_ecliptic_grid)
        configParser.save()

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
        self.select_body(self.sun)

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
        self.gui.update_info("Ambient light level:  %.2f" % settings.global_ambient, 0.5, 1.0)
        self.globalAmbient.setColor((corrected_ambient, corrected_ambient, corrected_ambient, 1))
        self.globalAmbientPath = self.world.attachNewNode(self.globalAmbient)
        self.world.setLight(self.globalAmbientPath)
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
            self.ship.set_frame(RelativeReferenceFrame(body, body.orbit.frame))
            self.observer.set_frame(RelativeReferenceFrame(body, body.orbit.frame))
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
        self.track = body
        if self.track is not None:
            print("Track", body.get_name())

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
        self.set_nav(ControlNav(mover))

    def reset_visibles(self):
        self.visibles = []

    def add_visible(self, body):
        self.visibles.append(body)

    def print_visibles(self):
        if self.last_visibles != self.visibles:
            print("Visible bodies", len(self.visibles), ':', ', '.join(map(lambda x: x.get_name(), self.visibles)))
        self.last_visibles = self.visibles

    @pstat
    def update_octree(self):
        self.universe.build_octree_cells_list(settings.lowest_app_magnitude)
        self.universe.add_extra_to_list(self.selected, self.follow, self.sync, self.track)

    @pstat
    def update_universe(self, time, dt):
        self.universe.update(time, dt)
        self.controllers_to_update = []
        for controller in self.controllers:
            if controller.should_update(time, dt):
                controller.update(time, dt)
                self.controllers_to_update.append(controller)

    @pstat
    def update_obs(self):
        self.universe.update_obs(self.observer)
        for controller in self.controllers_to_update:
            controller.update_obs(self.observer)

    @pstat
    def update_visibility(self):
        self.reset_visibles()
        self.universe.check_visibility(self.observer.pixel_size)
        for controller in self.controllers_to_update:
            controller.check_visibility(self.observer.pixel_size)
        self.print_visibles()

    @pstat
    def update_instances(self):
        self.pointset.reset()
        self.haloset.reset()
        self.universe.check_and_update_instance(self.observer.get_camera_pos(), self.observer.get_camera_rot(), self.pointset)
        for controller in self.controllers_to_update:
            controller.check_and_update_instance(self.observer.get_camera_pos(), self.observer.get_camera_rot(), self.pointset)
        self.pointset.update()
        self.haloset.update()
        self.gui.update_status()

    def time_task(self, task):
        dt = globalClock.getDt()

        self.time.update_time(dt)
        self.nav.update(dt)

        self.update_octree()
        update = pstats.levelpstat('update', 'Bodies')
        obs = pstats.levelpstat('obs', 'Bodies')
        visibility = pstats.levelpstat('visibility', 'Bodies')
        instance = pstats.levelpstat('instance', 'Bodies')
        StellarObject.nb_update = 0
        StellarObject.nb_obs = 0
        StellarObject.nb_visibility = 0
        StellarObject.nb_instance = 0

        if self.trigger_check_settings:
            self.universe.check_settings()
            self.trigger_check_settings = False

        self.update_universe(self.time.time_full, self.time.dt)
        self.camera_controller.update(self.time.time_full, self.time.dt)
        self.update_obs()

        if self.track != None:
            self.autopilot.center_on_object(self.track, duration=0, cmd=False)
            self.ship.update(self.time.time_full, 0)
            self.camera_controller.update(self.time.time_full, 0)

        if self.universe.nearest_system != self.nearest_system:
            if self.universe.nearest_system is not None:
                print("New nearest system:", self.universe.nearest_system.get_name())
                self.autopilot.stash_position()
                self.nav.stash_position()
                self.ship.change_global(self.universe.nearest_system.get_global_position())
                self.camera_controller.update(self.time.time_full, 0)
                self.autopilot.pop_position()
                self.nav.pop_position()
            else:
                print("No more near system")
            if self.nearest_system is not None:
                pass#self.nearest_system.remove_instance()
                #self.nearest_system.update_obs(self.observer.get_camera_pos())
                #self.universe.to_update.append(self.nearest_system)
            self.nearest_system = self.universe.nearest_system

        if self.nearest_system is not None:
            if isinstance(self.nearest_system, StellarSystem):
                (distance, body) = self.nearest_system.find_closest()
            else:
                body = self.nearest_system
            if body is not None:
                height = body.get_height_under(self.observer.get_camera_pos())
                distance = body.distance_to_obs - height
            if body is not None and self.nearest_body != body:
                self.nearest_body = body
                print("New nearest object:", body.get_name())
        else:
            body = None
        if settings.auto_scale:
            if body is None:
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
        self.update_visibility()
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
            print("\tDistance:", self.selected.distance_to_obs / units.Km, 'Km')
            print("\tRadius", self.selected.get_apparent_radius(), "Km", "Extend:", self.selected.get_extend(), "Km", "Visible:", self.selected.visible, self.selected.visible_size, "px")
            print("\tApp magnitude:", self.selected.get_app_magnitude(), '(', self.selected.get_abs_magnitude(), ')')
            if isinstance(self.selected, StellarBody):
                print("\tPhase:", self.selected.get_phase())
            print("\tGlobal position", self.selected.get_global_position())
            print("\tLocal position", self.selected.get_local_position(), '(Frame:', self.selected.orbit.get_frame_position_at(self.time.time_full), ')')
            print("\tRotation", self.selected.get_abs_rotation())
            print("\tOrientation", self.selected._orientation)
            print("\tVector to obs", self.selected.vector_to_obs)
            print("\tVector to star", self.selected.vector_to_star, "Distance:", self.selected.distance_to_star)
            print("\tVisible:", self.selected.visible, "Resolved:", self.selected.resolved, '(', self.selected.visible_size, ')', "In view:", self.selected.in_view)
            print("\tUpdate frozen:", self.selected.update_frozen)
            print("\tOrbit:", self.selected.orbit.__class__.__name__, self.selected.orbit.frame)
            if self.selected.label is not None:
                print("\tLabel visible:", self.selected.label.visible)
            if isinstance(self.selected, ReflectiveBody) and self.selected.surface is not None:
                print("\tRing shadow:", self.selected.surface.shadows.ring_shadow is not None)
                print("\tSphere shadow:", [x.body.get_friendly_name() for x in self.selected.surface.shadows.sphere_shadows.occluders])
            if isinstance(self.selected, StellarBody):
                if self.selected.scene_scale_factor is not None:
                    print("Scene")
                    print("\tPosition", self.selected.scene_position, '(Offset:', self.selected.world_body_center_offset, ') distance:', self.selected.scene_distance)
                    print("\tOrientation", self.selected.scene_orientation)
                    print("\tScale", self.selected.scene_scale_factor, '(', self.selected.get_scale() * self.selected.scene_scale_factor, ')')
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
                height = self.selected.get_height_under(self.observer.get_camera_pos())
                print("\tHeight:", height, "Delta:", height - self.selected.get_apparent_radius(), "Alt:", (self.selected.distance_to_obs - height))
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
                if self.selected.scene_scale_factor is not None:
                    print("Scene:")
                    print("\tPosition:", self.selected.scene_position, self.selected.scene_distance)
                    print("\tOrientation:", self.selected.scene_orientation)
                    print("\tScale:", self.selected.scene_scale_factor)

    def init_universe(self):
        pass

    def load_universe(self):
        pass

    def start_universe(self):
        pass
