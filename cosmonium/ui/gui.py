# -*- coding: utf-8 -*-
from __future__ import print_function
from __future__ import absolute_import

from panda3d.core import LVector3, LVector2

from ..bodies import Star, StellarBody
from ..systems import SimpleSystem
from ..universe import Universe
from ..astro import units
from ..astro import bayer
from ..astro.units import toUnit
from ..dircontext import defaultDirContext
from ..fonts import fontsManager, Font
from ..catalogs import objectsDB
from .. import utils
from .. import settings

from .hud import HUD
from .query import Query
from .Menu import PopupMenu
from .help import HelpPanel
from .infopanel import InfoPanel

class Gui(object):
    def __init__(self, cosmonium, time, camera, mouse, nav, autopilot):
        self.cosmonium = cosmonium
        self.time = time
        self.camera = camera
        self.mouse = mouse
        self.nav = nav
        self.autopilot = autopilot
        self.calc_scale()
        font = fontsManager.get_font(settings.hud_font, Font.STYLE_NORMAL)
        if font is not None:
            self.font = font.load()
        else:
            self.font = None
        self.hud = HUD(self.scale, self.font)
        self.query = Query(self.scale, self.font)
        self.last_fps = globalClock.getRealTime()
        self.screen_width = base.pipe.getDisplayWidth()
        self.screen_height = base.pipe.getDisplayHeight()
        self.width = 0
        self.height = 0
        self.update_size(self.screen_width, self.screen_height)
        self.popup_menu = None
        self.info = InfoPanel(self.scale, settings.markdown_font)
        self.help = HelpPanel(self.scale, settings.markdown_font)

    def calc_scale(self):
        screen_width = base.pipe.getDisplayWidth()
        screen_height = base.pipe.getDisplayHeight()
        self.scale = LVector2(1.0 / screen_width * 2.0, 1.0 / screen_height * 2.0)

    def register_events(self, event_ctrl):
        event_ctrl.accept('control-q', self.cosmonium.exit)
        event_ctrl.accept('enter', self.open_find_object)
        event_ctrl.accept('escape', self.escape)
        event_ctrl.accept('alt-enter', self.cosmonium.toggle_fullscreen)
        event_ctrl.accept('z', self.camera.zoom, [1.05])
        event_ctrl.accept('shift-z', self.camera.zoom, [1.0/1.05])
        event_ctrl.accept('shift-z-repeat', self.camera.zoom, [1.0/1.05])

        event_ctrl.accept('f1', self.toggle_info)
        event_ctrl.accept('shift-f1', self.toggle_help)
        event_ctrl.accept('f2', self.cosmonium.connect_pstats)
        event_ctrl.accept('f3', self.cosmonium.toggle_filled_wireframe)
        event_ctrl.accept('shift-f3', self.cosmonium.toggle_wireframe)
        event_ctrl.accept('f4', self.cosmonium.toggle_hdr)
        event_ctrl.accept("f5", base.bufferViewer.toggleEnable)
        event_ctrl.accept('f7', self.cosmonium.universe.dumpOctreeStats)
        event_ctrl.accept('shift-f7', self.cosmonium.universe.dumpOctree)
        event_ctrl.accept('f8', self.toggle_lod_freeze)
        event_ctrl.accept('shift-f8', self.dump_object_info)
        event_ctrl.accept('shift-control-f8', self.dump_object_info_2)
        event_ctrl.accept('control-f8', self.toggle_split_merge_debug)
        event_ctrl.accept('control-f9', self.toggle_bb)
        #event_ctrl.accept('f8', self.cosmonium.universe.dumpOctree)
        #event_ctrl.accept('f9', self.cosmonium.universe.addPlanes)
        event_ctrl.accept('f10', self.cosmonium.save_screenshot)
        event_ctrl.accept('shift-f10', self.cosmonium.save_screenshot_no_annotation)
        event_ctrl.accept('f11', render.explore)
        event_ctrl.accept('f12', render.analyze)
        
        event_ctrl.accept('f', self.cosmonium.follow_selected)
        event_ctrl.accept('y', self.cosmonium.sync_selected)
        event_ctrl.accept('t', self.cosmonium.toggle_track_selected)
        
        event_ctrl.accept('d', self.autopilot.go_to_front, [None, None, None, False])
        event_ctrl.accept('shift-d', self.autopilot.go_to_front, [None, None, None, True])
        event_ctrl.accept('g', self.autopilot.go_to_object)
        event_ctrl.accept('c', self.autopilot.center_on_object)
        event_ctrl.accept('control-j', self.autopilot.toggle_jump)
        event_ctrl.accept('*', self.camera.camera_look_back)

        event_ctrl.accept('shift-n', self.autopilot.go_north)
        event_ctrl.accept('shift-s', self.autopilot.go_south)
        event_ctrl.accept('shift-r', self.autopilot.go_meridian)

        event_ctrl.accept('shift-t', self.autopilot.go_system_top)
        event_ctrl.accept('shift-f', self.autopilot.go_system_front)
        event_ctrl.accept('shift-i', self.autopilot.go_system_side)

        event_ctrl.accept('shift-e', self.autopilot.align_on_ecliptic)
        event_ctrl.accept('shift-q', self.autopilot.align_on_equatorial)
        event_ctrl.accept('#', self.autopilot.change_distance, [-0.1])

        event_ctrl.accept('control-g', self.autopilot.go_to_surface)

        event_ctrl.accept('h', self.cosmonium.go_home)

        event_ctrl.accept('shift-j', self.time.set_J2000_date)
        event_ctrl.accept('!', self.time.set_current_date)
        event_ctrl.accept('l', self.time.accelerate_time, [2.0])
        event_ctrl.accept('shift-l', self.time.accelerate_time, [10.0])
        event_ctrl.accept('k', self.time.slow_time, [2.0])
        event_ctrl.accept('shift-k', self.time.slow_time, [10.0])
        event_ctrl.accept('j', self.time.invert_time)
        event_ctrl.accept('space', self.time.toggle_freeze_time)
        event_ctrl.accept('\\', self.time.set_real_time)

        event_ctrl.accept('{', self.cosmonium.incr_ambient, [-0.05])
        event_ctrl.accept('}', self.cosmonium.incr_ambient, [+0.05])

        #Render
        event_ctrl.accept('control-a', self.cosmonium.toggle_atmosphere)
        event_ctrl.accept('shift-a', self.cosmonium.toggle_rotation_axis)
        event_ctrl.accept('shift-control-r', self.cosmonium.toggle_reference_axis)
        event_ctrl.accept('control-b', self.cosmonium.toggle_boundaries)
        #event_ctrl.accept('control-e', self.toggle_shadows)
        event_ctrl.accept('i', self.cosmonium.toggle_clouds)
        #event_ctrl.accept('control-l', self.cosmonium.toggle_nightsides)
        event_ctrl.accept('o', self.cosmonium.toggle_orbits)
        #event_ctrl.accept('control-t', self.cosmonium.toggle_comet_tails)
        event_ctrl.accept('u', self.cosmonium.toggle_body_class, ['galaxy'])
        #event_ctrl.accept('shift-u', self.cosmonium.toggle_globulars)
        event_ctrl.accept(';', self.cosmonium.toggle_grid_equatorial)
        event_ctrl.accept(':', self.cosmonium.toggle_grid_ecliptic)
        event_ctrl.accept('/', self.cosmonium.toggle_asterisms)
        #event_ctrl.accept('^', self.cosmonium.toggle_nebulae)

        #Orbits
        event_ctrl.accept('shift-control-b', self.cosmonium.toggle_orbit, ['star'])
        event_ctrl.accept('shift-control-p', self.cosmonium.toggle_orbit, ['planet'])
        event_ctrl.accept('shift-control-d', self.cosmonium.toggle_orbit, ['dwarfplanet'])
        event_ctrl.accept('shift-control-m', self.cosmonium.toggle_orbit, ['moon'])
        event_ctrl.accept('shift-control-o', self.cosmonium.toggle_orbit, ['minormoon'])
        event_ctrl.accept('shift-control-c', self.cosmonium.toggle_orbit, ['comet'])
        event_ctrl.accept('shift-control-a', self.cosmonium.toggle_orbit, ['asteroid'])
        event_ctrl.accept('shift-control-s', self.cosmonium.toggle_orbit, ['spacecraft'])

        #Labels
        event_ctrl.accept('e', self.cosmonium.toggle_label, ['galaxy'])
        #event_ctrl.accept('shift-e', self.toggle_label, ['globular'])
        event_ctrl.accept('b', self.cosmonium.toggle_label, ['star'])
        event_ctrl.accept('p', self.cosmonium.toggle_label, ['planet'])
        event_ctrl.accept('shift-p', self.cosmonium.toggle_label, ['dwarfplanet'])
        event_ctrl.accept('m', self.cosmonium.toggle_label, ['moon'])
        event_ctrl.accept('shift-m', self.cosmonium.toggle_label, ['minormoon'])
        event_ctrl.accept('shift-w', self.cosmonium.toggle_label, ['comet'])
        event_ctrl.accept('w', self.cosmonium.toggle_label, ['asteroid'])
        event_ctrl.accept('n', self.cosmonium.toggle_label, ['spacecraft'])
        event_ctrl.accept('=', self.cosmonium.toggle_label, ['constellation'])
        #event_ctrl.accept('&', self.toggle_label, ['location'])

        event_ctrl.accept('v', self.hud.toggle_shown)

        for i in range(0, 10):
            event_ctrl.accept("%d" % i, self.cosmonium.select_planet, [i])

        event_ctrl.accept('shift-h', self.cosmonium.print_debug)
        event_ctrl.accept('shift-y', self.cosmonium.toggle_fly_mode)

    def escape(self):
        if self.info.shown():
            self.hide_info()
        elif self.help.shown():
            self.hide_help()
        else:
            self.cosmonium.reset_all()

    def left_click(self):
        body = self.mouse.get_over()
        if body != None and self.cosmonium.selected == body:
            self.autopilot.center_on_object(body)
            return
        self.cosmonium.select_body(body)

    def right_click(self):
        self.popup_menu = self.create_popup_menu(self.mouse.get_over())

    def toggle_lod_freeze(self):
        settings.debug_lod_freeze = not settings.debug_lod_freeze

    def toggle_bb(self):
        settings.debug_lod_show_bb = not settings.debug_lod_show_bb
        self.cosmonium.trigger_check_settings = True

    def dump_object_info(self):
        if self.cosmonium.selected is None: return
        if self.cosmonium.selected.surface is not None:
            shape = self.cosmonium.selected.surface.shape
            if shape.patchable:
                shape.dump_tree()

    def dump_object_info_2(self):
        if self.cosmonium.selected is None: return
        if self.cosmonium.selected.surface is not None:
            shape = self.cosmonium.selected.surface.shape
            if shape.patchable:
                shape.dump_patches()

    def toggle_split_merge_debug(self):
        settings.debug_lod_split_merge = not settings.debug_lod_split_merge

    def popup_done(self):
        self.popup_menu = False

    def create_popup_menu(self, over):
        if over is None:
            return False
        self.cosmonium.select_body(over)
        items = []
        items.append((over.get_friendly_name(), 0, self.cosmonium.autopilot.center_on_object))
        items.append(0)
        items.append(['_Info', 0, self.show_info])
        items.append(['_Goto', 0, self.autopilot.go_to_object])
        items.append(['_Follow', 0, self.cosmonium.follow_selected])
        items.append(['S_ync', 0, self.cosmonium.sync_selected])
        if isinstance(over, StellarBody) and len(over.surfaces) > 1:
            subitems = []
            for surface in over.surfaces:
                name = surface.get_name()
                if surface.category is not None:
                    if name != '':
                        name += " (%s)" % surface.category.name
                    else:
                        name = "%s" % surface.category.name
                if surface.resolution is not None:
                    if isinstance(surface.resolution, int):
                        name += " (%dK)" % surface.resolution
                    else:
                        name += " (%s)" % surface.resolution
                if surface is over.surface:
                    subitems.append([name, 0, None, None])
                else:
                    subitems.append([name, 0, over.set_surface, surface])
            items.append(["Surfaces", 0, subitems])
        if over.system is not None and not isinstance(over.system, Universe):
            subitems = []
            for child in over.system.children:
                if child != over:
                    if isinstance(child, SimpleSystem):
                        subitems.append([child.primary.get_friendly_name(), 0, self.cosmonium.select_body, child.primary])
                    else:
                        subitems.append([child.get_friendly_name(), 0, self.cosmonium.select_body, child])
            if len(subitems) > 0:
                items.append(["Orbiting bodies", 0, subitems])
        subitems = []
        parent = over.parent
        while parent is not None and not isinstance(parent, Universe):
            if isinstance(parent, SimpleSystem):
                if parent.primary != over:
                    subitems.append([parent.primary.get_friendly_name(), 0, self.cosmonium.select_body, parent.primary])
            else:
                subitems.append([parent.get_friendly_name(), 0, self.cosmonium.select_body, parent])
            parent = parent.parent
        if len(subitems) > 0:
            items.append(["Orbits", 0, subitems])
        scale = self.hud.scale
        scale = LVector3(scale[0], 1.0, scale[1])
        scale[0] *= settings.menu_text_size
        scale[2] *= settings.menu_text_size
        PopupMenu(items=items,
                  baselineOffset=-.35,
                  scale=scale, itemHeight=1.2, leftPad=.2,
                  separatorHeight=.3,
                  underscoreThickness=1,
                  BGColor=(.9,.9,.9,.9),
                  BGBorderColor=(.3,.3,.3,1),
                  separatorColor=(0,0,0,1),
                  frameColorHover=(.3,.3,.3,1),
                  frameColorPress=(.3,.3,.3,.1),
                  textColorReady=(0,0,0,1),
                  textColorHover=(.7,.7,.7,1),
                  textColorPress=(0,0,0,1),
                  textColorDisabled=(.3,.3,.3,1),
                  onDestroy=self.popup_done
                  )
        return True

    def select_object(self, body):
        self.cosmonium.select_body(body)

    def list_objects(self, prefix):
        result = objectsDB.startswith(prefix)
        text_result = []
        for entry in result:
            text_result.append((entry.get_name_startswith(prefix), entry))
        text_result.sort(key=lambda x: x[0])
        return text_result

    def open_find_object(self):
        self.query.open_query(self)

    def update_status(self):
        over = self.cosmonium.over
        selected = self.cosmonium.selected
        track = self.cosmonium.track
        follow = self.cosmonium.follow
        sync = self.cosmonium.sync
        (day, month, year, hour, min, sec) = self.time.time_to_values()
        date="%02d:%02d:%02d %2d:%02d:%02d UTC" % (day, month, year, hour, min, sec)
        if selected is not None:
            names = utils.join_names(bayer.decode_names(selected.names))
            self.hud.title.set(names)
            radius = selected.get_apparent_radius()
            if selected.distance_to_obs > 10 * radius:
                self.hud.topLeft.set(0, "Distance: " + toUnit(selected.distance_to_obs, units.lengths_scale))
            else:
                distance = selected.distance_to_obs - selected.height_under
                altitude = selected.distance_to_obs - radius
                self.hud.topLeft.set(0, "Altitude: " + toUnit(altitude, units.lengths_scale) + " (Ground: " + toUnit(distance, units.lengths_scale)+")")
            if not selected.virtual_object:
                self.hud.topLeft.set(1, "Radius: %s (%s)" % (toUnit(radius, units.lengths_scale), toUnit(radius, units.diameter_scale, 'x')))
                self.hud.topLeft.set(2, "Abs (app) magnitude: %g (%g)" % (selected.get_abs_magnitude(), selected.get_app_magnitude()))
                if selected.is_emissive():
                    self.hud.topLeft.set(3, "Luminosity: %gx Sun" % (selected.get_luminosity()))
                    if isinstance(selected, Star):
                        self.hud.topLeft.set(4, "Spectral type: " + selected.spectral_type.get_text())
                        self.hud.topLeft.set(5, "Temperature: %d K" % selected.temperature)
                    else:
                        self.hud.topLeft.set(4, "")
                        self.hud.topLeft.set(5, "")
                else:
                    self.hud.topLeft.set(3, "Phase: %g°" % ((1 - selected.get_phase()) * 180))
                    self.hud.topLeft.set(4, "")
                    self.hud.topLeft.set(5, "")
            else:
                self.hud.topLeft.set(1, "Abs (app) magnitude: %g (%g)" % (selected.get_abs_magnitude(), selected.get_app_magnitude()))
                self.hud.topLeft.set(2, "")
                self.hud.topLeft.set(3, "")
                self.hud.topLeft.set(4, "")
                self.hud.topLeft.set(5, "")
        else:
            self.hud.title.set("")
            self.hud.topLeft.set(0, "")
            self.hud.topLeft.set(1, "")
            self.hud.topLeft.set(2, "")
            self.hud.topLeft.set(3, "")
            self.hud.topLeft.set(4, "")
            self.hud.topLeft.set(5, "")
            self.hud.topLeft.set(6, "")
        self.hud.bottomLeft.set(0, toUnit(self.nav.speed, units.speeds_scale))
        if over:
            names = utils.join_names(bayer.decode_names(over.names))
            self.hud.bottomLeft.set(1, names)
        else:
            self.hud.bottomLeft.set(1, "")
        current_time = globalClock.getRealTime()
        if current_time - self.last_fps >= 1.0:
            fps = globalClock.getAverageFrameRate()
            self.hud.topRight.set(0, "%.1f" % fps)
            self.last_fps = current_time
        if self.autopilot.current_interval is not None:
            self.hud.bottomRight.set(4, "Traveling (%d)" % (self.autopilot.current_interval.getDuration() - self.autopilot.current_interval.getT()))
        else:
            self.hud.bottomRight.set(4, "")
        if track is not None:
            self.hud.bottomRight.set(3, "Track %s" % track.get_name())
        else:
            self.hud.bottomRight.set(3, "")
        if self.cosmonium.fly:
            self.hud.bottomRight.set(2, "Fly over %s" % selected.get_name())
        elif follow is not None:
            self.hud.bottomRight.set(2, "Follow %s" % follow.get_name())
        elif sync is not None:
            self.hud.bottomRight.set(2, "Sync orbit %s" % sync.get_name())
        else:
            self.hud.bottomRight.set(2, "")
        if self.time.running:
            self.hud.bottomRight.set(0, "%s (%.0fx)" % (date, self.time.multiplier))
        else:
            self.hud.bottomRight.set(0, "%s (Paused)" % (date))
        #self.hud.bottomRight.set(1, "FOV: %.0f°/%.0f°" % (self.cosmonium.realCamLens.getHfov(), self.cosmonium.realCamLens.getVfov()))
        self.hud.bottomRight.set(1, "FoV: %d° %d' %g\" (%gx)" % (units.toDegMinSec(self.camera.realCamLens.getVfov()) + (self.camera.zoom_factor, )))

    def update_info(self, text, duration=3.0, fade=1.0):
        self.hud.info.set(text, duration, fade)

    def update_scale(self):
        self.hud.update_scale()

    def update_size(self, width, height):
        if self.width == width and self.height == height:
            return
        self.width = width
        self.height = height
        #TODO: This is an ugly hack, should use the proper anchors or define new ones
        #Update aspect2d scale and anchors
        arx = 1.0 * self.screen_width / self.width
        ary = 1.0 * self.screen_height / self.height
        self.cosmonium.aspect2d.setScale(arx, 1.0, ary)
        self.cosmonium.a2dTop = 1.0 / ary
        self.cosmonium.a2dBottom = -1.0 / ary
        self.cosmonium.a2dLeft = -1.0 / arx
        self.cosmonium.a2dRight = 1.0 / arx
        self.cosmonium.a2dTopCenter.setPos(0, 0, self.cosmonium.a2dTop)
        self.cosmonium.a2dBottomCenter.setPos(0, 0, self.cosmonium.a2dBottom)
        self.cosmonium.a2dLeftCenter.setPos(self.cosmonium.a2dLeft, 0, 0)
        self.cosmonium.a2dRightCenter.setPos(self.cosmonium.a2dRight, 0, 0)

        self.cosmonium.a2dTopLeft.setPos(self.cosmonium.a2dLeft, 0, self.cosmonium.a2dTop)
        self.cosmonium.a2dTopRight.setPos(self.cosmonium.a2dRight, 0, self.cosmonium.a2dTop)
        self.cosmonium.a2dBottomLeft.setPos(self.cosmonium.a2dLeft, 0, self.cosmonium.a2dBottom)
        self.cosmonium.a2dBottomRight.setPos(self.cosmonium.a2dRight, 0, self.cosmonium.a2dBottom)

    def hide(self):
        self.hud.hide()

    def show(self):
        self.hud.show()

    def show_help(self):
        self.help.show()

    def hide_help(self):
        self.help.hide()

    def show_info(self):
        if self.cosmonium.selected is not None:
            if self.info.shown():
                self.hide_info()
            self.info.show(self.cosmonium.selected)

    def hide_info(self):
        self.info.hide()

    def toggle_info(self):
        if not self.info.shown():
            self.show_info()
        else:
            self.hide_info()

    def toggle_help(self):
        if not self.help.shown():
            self.show_help()
        else:
            self.hide_help()
