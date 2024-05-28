#
#This file is part of Cosmonium.
#
#Copyright (C) 2018-2024 Laurent Deru.
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


from panda3d.core import TextNode, LVector2

from ..objects.star import Star
from ..astro import units
from ..astro import bayer
from ..astro.units import toUnit
from .. import utils
from .. import settings

from .dock.dock import Dock
from .hud.fadetextline import FadeTextLine
from .hud.textblock import TextBlock
from .hud.textline import TextLine
from .skin import UIElement

class Huds():
    def __init__(self, gui, dock, skin):
        self.owner = gui
        self.skin = skin
        offset = LVector2()
        self.element = UIElement(None, class_='hud', id_='hud')
        self.title = TextLine('title', base.p2dTopLeft, offset, TextNode.ALeft, LVector2(0, 1), owner=self)
        title_height = self.title.get_height()
        self.topLeft = TextBlock('topLeft', base.p2dTopLeft, LVector2(0, title_height), TextNode.ALeft, True, 10, owner=self)
        self.bottomLeft = TextBlock('bottomLeft', base.p2dBottomLeft, offset, TextNode.ALeft, False, 5, owner=self)
        self.topRight = TextBlock('topRight', base.p2dTopRight, offset, TextNode.ARight, True, 5, owner=self)
        self.bottomRight = TextBlock('bottomRight', base.p2dBottomRight, offset, TextNode.ARight, False, 5, owner=self)
        #TODO: Info should be moved out of HUD
        self.info = FadeTextLine('info', base.p2dBottomLeft, offset, TextNode.ALeft, LVector2(0, -3), owner=self)
        # TODO: Temporary broken way to instanciate a dock
        if dock is not None:
            layout, orientation, location = dock
            self.bottom_dock = Dock(gui, base.pixel2d, orientation, location, layout, LVector2(1, 1), offset, skin)
        else:
            self.bottom_dock = None
        self.shown = True
        self.last_fps = globalClock.getRealTime()

    def hide(self):
        self.title.hide()
        self.topLeft.hide()
        self.bottomLeft.hide()
        self.topRight.hide()
        self.bottomRight.hide()
        self.shown = False

    def show(self):
        self.title.show()
        self.topLeft.show()
        self.bottomLeft.show()
        self.topRight.show()
        self.bottomRight.show()
        self.shown = True

    def set_scale(self, scale):
        self.title.set_scale(scale)
        self.topLeft.set_scale(scale)
        self.bottomLeft.set_scale(scale)
        self.topRight.set_scale(scale)
        self.bottomRight.set_scale(scale)
        self.info.set_scale(scale)

    def set_y_offset(self, y_offset):
        self.title.set_offset((0, -y_offset))
        title_height = self.title.get_height()
        self.topLeft.set_offset((0, y_offset + title_height))
        self.topRight.set_offset((0, y_offset))

    def update(self, cosmonium, camera, mouse, nav, autopilot, time):
        selected = cosmonium.selected
        track = cosmonium.track
        follow = cosmonium.follow
        sync = cosmonium.sync
        (years, months, days, hours, mins, secs) = time.time_to_values()
        date="%02d:%02d:%02d %2d:%02d:%02d UTC" % (years, months, days, hours, mins, secs)
        if selected is not None:
            names = utils.join_names(bayer.decode_names(selected.get_names()))
            self.title.set_text(names)
            radius = selected.get_apparent_radius()
            if selected.virtual_object or selected.anchor.distance_to_obs > 10 * radius:
                self.topLeft.set(0, _("Distance: ")  + toUnit(selected.anchor.distance_to_obs, units.lengths_scale))
            else:
                if selected.surface is not None and not selected.surface.is_flat():
                    alt_under = selected.get_alt_under(camera.get_local_position())
                    surface_point = selected.get_point_under(camera.get_local_position())
                    (tangent, binormal, normal) = selected.get_tangent_plane_under(camera.get_local_position())
                    direction = camera.get_local_position() - surface_point
                    distance = direction.dot(normal)
                    altitude = distance + alt_under
                    self.topLeft.set(0, _("Altitude: ") + toUnit(altitude, units.lengths_scale) + " (" + _("Ground: ")  + toUnit(distance, units.lengths_scale) + ")")
                else:
                    altitude = selected.anchor.distance_to_obs - radius
                    self.topLeft.set(0, _("Altitude: ")  + toUnit(altitude, units.lengths_scale))
            if not selected.virtual_object and selected.anchor.is_stellar():
                self.topLeft.set(1, _("Radius: ") + "%s (%s)" % (toUnit(radius, units.lengths_scale), toUnit(radius, units.diameter_scale, 'x')))
                self.topLeft.set(2, _("Abs (app) magnitude: ") + "%g (%g)" % (selected.get_abs_magnitude(), selected.get_app_magnitude()))
                if selected.is_emissive():
                    self.topLeft.set(3, _("Luminosity: ") + "%g" % (selected.anchor._intrinsic_luminosity / units.L0) + _("x Sun"))
                    if isinstance(selected, Star):
                        self.topLeft.set(4, _("Spectral type: ") + selected.spectral_type.get_text())
                        self.topLeft.set(5, _("Temperature: ") + "%d" % selected.temperature + " K")
                    else:
                        self.topLeft.set(4, "")
                        self.topLeft.set(5, "")
                else:
                    self.topLeft.set(3, _("Phase: ") + "%g°" % ((1 - selected.get_phase()) * 180))
                    self.topLeft.set(4, "")
                    self.topLeft.set(5, "")
            else:
                if selected.anchor.is_stellar():
                    self.topLeft.set(1, _("Abs (app) magnitude: ") + "%g (%g)" % (selected.get_abs_magnitude(), selected.get_app_magnitude()))
                else:
                    self.topLeft.set(1, "")
                self.topLeft.set(2, "")
                self.topLeft.set(3, "")
                self.topLeft.set(4, "")
                self.topLeft.set(5, "")
        else:
            self.title.set_text("")
            self.topLeft.set(0, "")
            self.topLeft.set(1, "")
            self.topLeft.set(2, "")
            self.topLeft.set(3, "")
            self.topLeft.set(4, "")
            self.topLeft.set(5, "")
            self.topLeft.set(6, "")
        self.bottomLeft.set(0, toUnit(nav.speed, units.speeds_scale))
        if settings.mouse_over and mouse.over is not None:
            names = utils.join_names(bayer.decode_names(mouse.over.names))
            self.bottomLeft.set(1, names)
        else:
            self.bottomLeft.set(1, "")
        current_time = globalClock.getRealTime()
        if current_time - self.last_fps >= 1.0:
            if settings.display_render_info == 'fps':
                fps = globalClock.getAverageFrameRate()
                self.topRight.set(0, "%.1f fps" % fps)
            elif settings.display_render_info == 'ms':
                fps = globalClock.getDt() * 1000
                self.topRight.set(0, "%.1f ms" % fps)
            else:
                self.topRight.set(0, "")
            self.last_fps = current_time
        if autopilot.current_interval is not None:
            self.bottomRight.set(4, _("Travelling (%d)") % (autopilot.current_interval.getDuration() - autopilot.current_interval.getT()))
        else:
            self.bottomRight.set(4, "")
        if track is not None:
            self.bottomRight.set(3, _("Track %s") % track.get_name())
        else:
            self.bottomRight.set(3, "")
        if cosmonium.fly:
            self.bottomRight.set(2, _("Fly over %s") % selected.get_name())
        elif follow is not None:
            self.bottomRight.set(2, _("Follow %s") % follow.get_name())
        elif sync is not None:
            self.bottomRight.set(2, _("Sync orbit %s") % sync.get_name())
        else:
            self.bottomRight.set(2, "")
        if time.running:
            self.bottomRight.set(0, "%s (%.0fx)" % (date, time.multiplier))
        else:
            self.bottomRight.set(0, _("%s (Paused)") % (date))
        self.bottomRight.set(1, "FoV: %d° %d' %g\" (%gx)" % (units.toDegMinSec(camera.lens.get_vfov()) + (camera.zoom_factor, )))
        if self.bottom_dock is not None:
            self.bottom_dock.update()

    def update_size(self):
        if self.bottom_dock is not None:
            self.bottom_dock.update_size()
