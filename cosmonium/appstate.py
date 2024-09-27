#
# This file is part of Cosmonium.
#
# Copyright (C) 2018-2024 Laurent Deru.
#
# Cosmonium is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Cosmonium is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Cosmonium.  If not, see <https://www.gnu.org/licenses/>.
#


from panda3d.core import LPoint3d, LQuaterniond

from .bodyclass import bodyClasses
from . import settings


class AppState(object):
    def __init__(self):
        self.reset()

    def reset(self):
        self.selected = None
        self.follow = None
        self.sync = None
        self.track = None
        self.fly = False

        self.multiplier = None
        self.time_full = None
        self.running = None

        self.global_position = None
        self.absolute = False
        self.position = None
        self.orientation = None

        self.fov = None

        self.render = None
        self.labels = None

    def save_state(self, cosmonium):
        self.selected = cosmonium.selected
        self.follow = cosmonium.follow
        self.sync = cosmonium.sync
        self.track = cosmonium.track

        self.multiplier = cosmonium.time.multiplier
        self.time_full = cosmonium.time.time_full
        self.running = cosmonium.time.running

        # TODO: This work only for FixedCameraController
        cosmonium.camera_controller.prepare_movement()
        self.global_position = cosmonium.ship.anchor.get_absolute_reference_point()
        self.position = cosmonium.ship.anchor.get_frame_position()
        self.orientation = cosmonium.ship.anchor.get_frame_orientation()
        self.absolute = False

        self.fov = cosmonium.observer.get_fov()

        self.render = {}
        self.render['orbits'] = settings.show_orbits
        self.render['clouds'] = settings.show_clouds
        self.render['atmospheres'] = settings.show_atmospheres
        self.render['asterisms'] = settings.show_asterisms
        self.render['boundaries'] = settings.show_boundaries
        self.render['equatorialgrid'] = cosmonium.equatorial_grid.shown
        self.render['eclipticgrid'] = cosmonium.ecliptic_grid.shown

        self.labels = {}
        for name, body_class in bodyClasses.classes.items():
            self.render[name] = body_class.show
            self.labels[name] = body_class.show_label

    def apply_state(self, cosmonium):
        cosmonium.reset_nav()

        cosmonium.time.multiplier = self.multiplier
        cosmonium.time.time_full = self.time_full
        cosmonium.time.running = self.running

        if self.selected is not None:
            cosmonium.select_body(self.selected)
        if self.follow is not None:
            cosmonium.follow_body(self.follow)
        if self.sync is not None:
            cosmonium.sync_body(self.sync)
        if self.track is not None:
            cosmonium.track_body(self.track)

        # Update the universe with the new time reference and selection
        cosmonium.main_update_task(None)

        if self.global_position is not None:
            cosmonium.ship.anchor.set_absolute_reference_point(self.global_position)
        else:
            if self.sync is not None:
                cosmonium.ship.anchor.set_absolute_reference_point(self.sync.anchor.get_absolute_reference_point())
            elif self.follow:
                cosmonium.ship.anchor.set_absolute_reference_point(self.follow.anchor.get_absolute_reference_point())
            else:
                cosmonium.ship.anchor.set_absolute_reference_point(LPoint3d())
        if self.absolute:
            cosmonium.ship.anchor.set_local_position(self.position)
            cosmonium.ship.anchor.set_absolute_orientation(self.orientation)
        else:
            cosmonium.ship.anchor.set_frame_position(self.position)
            cosmonium.ship.anchor.set_frame_orientation(self.orientation)
        cosmonium.observer.anchor.set_frame_orientation(LQuaterniond())

        cosmonium.observer.set_fov(self.fov)

        if self.render is not None:
            settings.show_orbits = self.render['orbits']
            settings.show_clouds = self.render['clouds']
            settings.show_asterisms = self.render['asterisms']
            settings.show_boundaries = self.render['boundaries']
            cosmonium.set_grid_equatorial(self.render['equatorialgrid'])
            cosmonium.set_grid_ecliptic(self.render['eclipticgrid'])
            for name, body_class in bodyClasses.classes.items():
                show = self.render.get(name, None)
                if show is not None:
                    body_class.show = show

        if self.labels is not None:
            for name, body_class in bodyClasses.classes.items():
                body_class.show_label = self.labels.get(name, False)

        cosmonium.update_settings()

        # Update again to detect the new nearest system
        cosmonium.nearest_system = None
        cosmonium.main_update_task(None)
        # We have to do it twice as the current code does not add the extra object to the
        # list of octree leaves to check
        cosmonium.main_update_task(None)
