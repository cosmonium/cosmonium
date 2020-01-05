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
from panda3d.core import DrawMask
from panda3d.core import AmbientLight
from panda3d.core import LightRampAttrib
from panda3d.core import LColor

from direct.task.Task import Task

import logging
from .parsers.configparser import configParser
from .foundation import BaseObject
from .dircontext import defaultDirContext
from .opengl import request_opengl_config, check_opengl_config, create_main_window, check_and_create_rendering_buffers
from .bodies import StellarBody, ReflectiveBody
from .systems import StellarSystem, SimpleSystem
from .universe import Universe
from .annotations import Grid
from .pointsset import PointsSet
from .sprites import RoundDiskPointSprite, GaussianPointSprite, ExpPointSprite, MergeSprite
from .astro.frame import J2000EquatorialReferenceFrame, J2000EclipticReferenceFrame
from .astro.frame import AbsoluteReferenceFrame, SynchroneReferenceFrame, RelativeReferenceFrame
from .celestia.cel_url import CelUrl

#import orbits and rotations elements to add them to the DB
from .astro.tables import uniform, vsop87, wgccre

from .bodyclass import bodyClasses
from .autopilot import AutoPilot
from .camera import Camera
from .timecal import Time
from .ui.gui import Gui
from .ui.mouse import Mouse
from .ui.splash import Splash
from .nav import FreeNav, WalkNav
from .astro import units
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
from cosmonium.bodies import StellarObject

class CosmoniumBase(ShowBase):
    def __init__(self):
        self.keystrokes = {}
        self.gui = None #TODO: Temporary for keystroke below
        self.observer = None #TODO: For window_event below
        self.wireframe = False
        self.wireframe_filled = False
        self.trigger_check_settings = True

        self.print_info()
        self.panda_config()
        ShowBase.__init__(self, windowType='none')
        create_main_window(self)
        check_opengl_config(self)

        BaseObject.context = self

        self.setBackgroundColor(0, 0, 0, 1)
        self.disableMouse()
        check_and_create_rendering_buffers(self)
        cache.init_cache()
        self.register_events()

        self.world = self.render.attachNewNode("world")
        self.annotation = self.render.attachNewNode("annotation")
        self.annotation_shader = self.annotation.attachNewNode("annotation_shader")
        self.annotation.node().adjust_draw_mask(DrawMask(0), DrawMask(1), DrawMask(0))
        self.annotation_shader.node().adjust_draw_mask(DrawMask(0), DrawMask(1), DrawMask(0))

        self.world.setShaderAuto()
        self.annotation_shader.setShaderAuto()

        workers.asyncTextureLoader = workers.AsyncTextureLoader(self)
        workers.syncTextureLoader = workers.SyncTextureLoader()

    def panda_config(self):
        data = []
        request_opengl_config(data)
        self.app_panda_config(data)
        data.append("text-encoding utf8")
        data.append("paste-emit-keystrokes #f")
        #TODO: Still needed ?
        data.append("bounds-type box")
        data.append("screenshot-extension png")
        data.append("screenshot-filename %~p-%Y-%m-%d-%H-%M-%S-%~f.%~e")
        data.append("fullscreen %d" % settings.win_fullscreen)
        if settings.win_fullscreen:
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
        print("Panda version: %s (%s)" % (PandaSystem.getVersionString(), PandaSystem.getGitCommit()))
        print("Data type:", "double" if settings.use_double else 'float')

    def exit(self):
        sys.exit(0)

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
        self.buttonThrowers[0].node().setKeystrokeEvent('keystroke')
        self.accept('keystroke', self.keystroke_event)
        self.accept(self.win.getWindowEvent(), self.window_event)
        self.accept('panic-deactivate-gsg', self.gsg_failure)

    def gsg_failure(self, event):
        print("Internal error detected, see output.log for more details")
        sys.exit(1)

    def get_fullscreen_sizes(self):
        screen_width = base.pipe.getDisplayWidth()
        screen_height = base.pipe.getDisplayHeight()
        return (screen_width, screen_height)

    def toggle_fullscreen(self):
        settings.win_fullscreen = not settings.win_fullscreen
        wp = WindowProperties(self.win.getProperties())
        wp.setFullscreen(settings.win_fullscreen)
        if settings.win_fullscreen:
            resolutions = self.get_fullscreen_sizes()
            wp.setSize(*resolutions)
        else:
            wp.setSize(settings.win_width, settings.win_height)
        self.win.requestProperties(wp)
        configParser.save()

    def window_event(self, window):
        if self.win.is_closed():
            sys.exit(0)
        width = self.win.getProperties().getXSize()
        height = self.win.getProperties().getYSize()
        if width != settings.win_width or height != settings.win_height:
            if settings.win_fullscreen:
                settings.win_fs_width = width
                settings.win_fs_height = height
            else:
                settings.win_width = width
                settings.win_height = height
            configParser.save()
        if self.observer is not None:
            self.observer.set_film_size(width, height)
            self.render.setShaderInput("near_plane_height", self.observer.height / self.observer.tan_fov2)
        if self.gui is not None:
            self.gui.update_size(width, height)

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

    def save_screenshot(self):
        filename = self.screenshot()
        if filename is not None:
            print("Saving screenshot into", filename)
        else:
            print("Could not save filename")

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

        self.universe = Universe(self)

        self.splash = Splash()
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
        self.observer = Camera(self.cam, self.camLens)
        self.autopilot = AutoPilot(self.observer, self)
        self.mouse = Mouse(self)
        if self.nav is None:
            self.nav = FreeNav()
        if self.gui is None:
            self.gui = Gui(self, self.time, self.observer, self.mouse, self.nav, self.autopilot)
        self.set_nav(self.nav)

        self.nav.register_events(self)
        self.gui.register_events(self)

        self.observer.init()

        self.pointset = PointsSet(use_sprites=True, sprite=GaussianPointSprite(size=16))
        if settings.render_sprite_points:
            self.pointset.instance.reparentTo(self.world)
        
        self.haloset = PointsSet(use_sprites=True, sprite=ExpPointSprite(size=256, max_value=0.6), background=settings.halo_depth)
        if settings.render_sprite_points:
            self.haloset.instance.reparentTo(self.world)
        
        #render.setAntialias(AntialiasAttrib.MAuto)#MMultisample)
        self.setFrameRateMeter(False)
        
        self.set_ambient(settings.global_ambient)
        
        self.equatorial_grid = Grid("Equatorial", J2000EquatorialReferenceFrame.orientation, LColor(0.28,  0.28,  0.38, 1))
        self.equatorial_grid.set_shown(settings.show_equatorial_grid)

        self.ecliptic_grid = Grid("Ecliptic", J2000EclipticReferenceFrame.orientation, LColor(0.28,  0.28,  0.38, 1))
        self.ecliptic_grid.set_shown(settings.show_ecliptic_grid)

        self.time.set_current_date()
        self.universe.first_update()
        self.universe.first_update_obs(self.observer)
        self.window_event(None)
        self.time_task(None)

        taskMgr.add(self.time_task, "time-task")

        self.start_universe()

    def app_panda_config(self, data):
        icon = defaultDirContext.find_texture('cosmonium.ico')
        data.append("icon-filename %s" % icon)
        data.append("window-title Cosmonium")

    def set_nav(self, nav):
        if self.nav is not None:
            self.nav.remove_events(self)
        self.nav = nav
        if self.nav is not None:
            self.nav.init(self, self.observer, self.gui)
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
        self.gui.hide()
        self.annotation.hide()
        self.annotation_shader.hide()
        base.graphicsEngine.renderFrame()
        filename = self.screenshot()
        self.gui.show()
        self.annotation.show()
        self.annotation_shader.show()
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
        self.observer.set_camera_frame(AbsoluteReferenceFrame())
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
            self.observer.set_camera_frame(RelativeReferenceFrame(body, body.orbit.frame))
        else:
            self.observer.set_camera_frame(AbsoluteReferenceFrame())
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
            self.observer.set_camera_frame(SynchroneReferenceFrame(body))
        else:
            self.observer.set_camera_frame(AbsoluteReferenceFrame())
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
        self.universe.add_extra_to_list(self.selected, self.track)

    @pstat
    def update_universe(self):
        self.universe.update(self.time.time_full)

    @pstat
    def update_obs(self):
        self.universe.update_obs(self.observer)
        if self.selected is not None:
            self.selected.calc_height_under(self.observer.get_camera_pos())
    @pstat
    def update_visibility(self):
        self.reset_visibles()
        self.universe.check_visibility(self.observer.pixel_size)
        self.print_visibles()

    @pstat
    def update_instances(self):
        self.pointset.reset()
        self.haloset.reset()
        self.universe.check_and_update_instance(self.observer.get_camera_pos(), self.observer.get_camera_rot(), self.pointset)
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

        self.update_universe()
        self.observer.update_camera()
        self.update_obs()

        if self.track != None:
            self.autopilot.center_on_object(self.track, duration=0, cmd=False)
            self.observer.update_camera()

        if self.universe.nearest_system != self.nearest_system:
            if self.universe.nearest_system is not None:
                print("New nearest system:", self.universe.nearest_system.get_name())
                self.autopilot.stash_position()
                self.nav.stash_position()
                self.observer.change_global(self.universe.nearest_system.get_global_position())
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

        return Task.cont

    def print_debug(self):
        print("Global:")
        print("\tscale", settings.scale)
        print("\tPlanes", self.camLens.getNear(), self.camLens.getFar())
        print("Camera:")
        print("\tGlobal position", self.observer.camera_global_pos)
        print("\tLocal position", self.observer.get_camera_pos(), '(', self.observer.camera_pos, ')')
        print("\tRotation", self.observer.get_camera_rot(), '(', self.observer.camera_rot, ')')
        if self.selected:
            print("Selected:", utils.join_names(self.selected.names))
            print("\tType:", self.selected.__class__.__name__)
            print("\tDistance:", self.selected.distance_to_obs / units.Km, 'Km')
            print("\tRadius", self.selected.get_apparent_radius(), "Km", "Extend:", self.selected.get_extend(), "Km", "Visible:", self.selected.visible, self.selected.visible_size, "px")
            print("\tApp magnitude:", self.selected.get_app_magnitude(), '(', self.selected.get_abs_magnitude(), ')')
            if isinstance(self.selected, StellarBody):
                print("\tPhase:", self.selected.get_phase())
            print("\tGlobal position", self.selected.get_global_position())
            print("\tLocal position", self.selected.get_local_position())
            print("\tRotation", self.selected.get_abs_rotation())
            print("\tOrientation", self.selected._orientation)
            print("\tVector to obs", self.selected.vector_to_obs)
            print("\tVector to star", self.selected.vector_to_star, "Distance:", self.selected.distance_to_star)
            print("\tVisible:", self.selected.visible, "Resolved:", self.selected.resolved, '(', self.selected.visible_size, ')', "In view:", self.selected.in_view)
            print("\tUpdate frozen:", self.selected.update_frozen)
            if self.selected.label is not None:
                print("\tLabel visible:", self.selected.label.visible)
            if isinstance(self.selected, ReflectiveBody) and self.selected.surface is not None:
                print("\tRing shadow:", self.selected.surface.shadows.ring_shadow is not None)
                print("\tSphere shadow:", [x.body.get_friendly_name() for x in self.selected.surface.shadows.sphere_shadows.occluders])
            if isinstance(self.selected, StellarBody):
                if self.selected.scene_scale_factor is not None:
                    print("Scene")
                    print("\tPosition", self.selected.scene_position, '(', self.selected.world_body_center_offset, ')', self.selected.scene_distance)
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
                print("\tProjection:", projection[0] * 180 / pi, projection[1] * 180 / pi, projection[2])
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
