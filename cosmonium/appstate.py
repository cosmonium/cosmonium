from __future__ import print_function
from __future__ import absolute_import

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

        self.absolute = False
        self.global_position = None
        self.local_position = None
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

        self.global_position = cosmonium.observer.camera_global_pos
        self.local_position = cosmonium.observer.get_frame_camera_pos()
        self.orientation = cosmonium.observer.get_frame_camera_rot()
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
        if self.selected is not None:
            cosmonium.select_body(self.selected)
        if self.follow is not None:
            cosmonium.follow_body(self.follow)
        if self.sync is not None:
            cosmonium.sync_body(self.sync)
        if self.track is not None:
            cosmonium.track_body(self.track)

        cosmonium.time.multiplier = self.multiplier
        cosmonium.time.time_full = self.time_full
        cosmonium.time.running = self.running

        cosmonium.observer.camera_global_pos = self.global_position
        if self.absolute:
            cosmonium.observer.set_camera_pos(self.local_position)
            cosmonium.observer.set_camera_rot(self.orientation)
        else:
            cosmonium.observer.set_frame_camera_pos(self.local_position)
            cosmonium.observer.set_frame_camera_rot(self.orientation)
        #update_camera() will be performed next frame

        cosmonium.observer.set_fov(self.fov)

        if self.render is not None:
            settings.show_orbits = self.render['orbits']
            settings.show_clouds = self.render['clouds']
            settings.show_asterisms = self.render['asterisms']
            settings.show_boundaries = self.render['boundaries']
            cosmonium.equatorial_grid.set_shown(self.render['equatorialgrid'])
            cosmonium.ecliptic_grid.set_shown(self.render['eclipticgrid'])
            for name, body_class in bodyClasses.classes.items():
                show = self.render.get(name, None)
                if show is not None:
                    body_class.show = show

        if self.labels is not None:
            for name, body_class in bodyClasses.classes.items():
                body_class.show_label = self.labels.get(name, False)

        cosmonium.update_settings()
