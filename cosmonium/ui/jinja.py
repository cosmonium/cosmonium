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


from abc import ABC, abstractmethod
import builtins
from direct.showbase.ShowBaseGlobal import globalClock
import jinja2

from ..astro import bayer, units
from ..bodyclass import bodyClasses
from ..objects.star import Star
from .. import settings
from .. import utils


class ObjectProvider(ABC):

    @abstractmethod
    def _object(self): ...

    @property
    def abs_magnitude(self):
        return self._object.get_abs_magnitude()

    @property
    def app_magnitude(self):
        return self._object.get_app_magnitude()

    @property
    def apparent_radius(self):
        return self._object.get_apparent_radius()

    @property
    def distance_to_obs(self):
        return self._object.anchor.distance_to_obs

    @property
    def friendly_name(self):
        return self._object.get_friendly_name()

    @property
    def ground_distance(self):
        camera_position = builtins.base.observer.get_local_position()
        surface_point = self._object.get_point_under(camera_position)
        (tangent, binormal, normal) = self._object.get_tangent_plane_under(camera_position)
        direction = camera_position - surface_point
        distance = direction.dot(normal)
        return distance

    @property
    def altitude(self):
        if self._object.surface is not None and not self._object.surface.is_flat():
            camera_position = builtins.base.observer.get_local_position()
            alt_under = self._object.get_alt_under(camera_position)
            altitude = self.ground_distance + alt_under
        else:
            altitude = self._object.anchor.distance_to_obs - self._object.get_apparent_radius()
        return altitude

    @property
    def has_not_flat_surface(self):
        return self._object.surface is not None and not self._object.surface.is_flat()

    @property
    def intrinsic_luminosity(self):
        return self._object.anchor._intrinsic_luminosity

    @property
    def is_emissive(self):
        return self._object.is_emissive()

    @property
    def is_star(self):
        return isinstance(self._object, Star)

    @property
    def is_stellar(self):
        return self._object.anchor.is_stellar()

    @property
    def is_virtual_object(self):
        return self._object.virtual_object

    @property
    def list_of_names(self):
        return utils.join_names(bayer.decode_names(self._object.get_names()))

    @property
    def phase(self):
        return (1 - self._object.get_phase()) * 180

    @property
    def spectral_type(self):
        return self._object.spectral_type.get_text()

    @property
    def temperature(self):
        return self._object.temperature


class AutopilotProvider:
    def __init__(self, engine):
        self.engine = engine

    @property
    def running(self):
        return self.engine.autopilot.current_interval is not None

    @property
    def time_to_destination(self):
        return self.engine.autopilot.current_interval.duration - self.engine.autopilot.current_interval.t


class BodiesProvider:

    def is_shown(self, body_class):
        return bodyClasses.get_show(body_class)


class CameraProvider:
    def __init__(self, engine):
        self.engine = engine

    @property
    def vfov(self):
        return self.engine.observer.lens.get_vfov()

    @property
    def zoom(self):
        return self.engine.observer.zoom_factor


class ClockProvider:

    def __init__(self):
        self.last_average_frame_time = -1
        self.last_average_frame = None
        self.last_frame_duration_time = -1
        self.last_frame_duration = None

    @property
    def average_frame_rate(self):
        current_time = globalClock.get_real_time()
        if current_time - self.last_average_frame_time >= 1.0:
            self.last_average_frame_time = current_time
            self.last_average_frame = globalClock.get_average_frame_rate()
        return self.last_average_frame

    @property
    def frame_duration(self):
        current_time = globalClock.get_real_time()
        if current_time - self.last_frame_duration_time >= 1.0:
            self.last_frame_duration_time = current_time
            self.last_frame_duration = globalClock.get_dt()
        return self.last_frame_duration


class EngineProvider:
    def __init__(self, engine):
        self.engine = engine

    @property
    def fly(self):
        return self.engine.fly

    @property
    def follow(self):
        return self.engine.follow

    @property
    def selected(self):
        return self.engine.selected

    @property
    def ship(self):
        return self.engine.ship

    @property
    def sync(self):
        return self.engine.sync

    @property
    def track(self):
        return self.engine.track


class GuiProvider:
    def __init__(self, gui):
        self.gui = gui

    @property
    def menubar_shown(self):
        return self.gui.menubar_shown


class LabelsProvider:

    def is_shown(self, body_class):
        return bodyClasses.get_show_label(body_class)


class NavProvider:
    def __init__(self, engine):
        self.engine = engine

    @property
    def speed(self):
        return self.engine.nav.speed


class OrbitsProvider:

    def is_shown(self, body_class):
        return bodyClasses.get_show_orbit(body_class)


class ScalesProvider:

    def length(self, value):
        return units.toUnit(value, units.lengths_scale)

    def radius(self, value, extra=""):
        return units.toUnit(value, units.diameter_scale, extra)

    def speed(self, value):
        return units.toUnit(value, units.speeds_scale)

    def degrees(self, value):
        return "%d° %d' %g\"" % units.toDegMinSec(value)


class SelectedProvider(ObjectProvider):

    def __init__(self, engine):
        self.engine = engine

    @property
    def _object(self):
        if self.engine.selected is not None:
            return self.engine.selected
        else:
            raise jinja2.exceptions.UndefinedError()


class UnitsProvider:

    @property
    def L0(self):
        return units.L0


class SettingsProvider:

    def __getattr__(self, attr):
        return getattr(settings, attr)


class TimeProvider:
    def __init__(self, engine):
        self.engine = engine

    @property
    def date(self):
        return "%02d:%02d:%02d %2d:%02d:%02d UTC" % self.engine.time.time_to_values()

    @property
    def multiplier(self):
        return self.engine.time.multiplier

    @property
    def is_running(self):
        return self.engine.time.running


class JinjaEnv:
    def __init__(self, engine, gui):
        self.env = jinja2.Environment()
        self.env.globals = {
            'autopilot': AutopilotProvider(engine),
            'bodies': BodiesProvider(),
            'camera': CameraProvider(engine),
            'clock': ClockProvider(),
            'engine': EngineProvider(engine),
            'gui': GuiProvider(gui),
            'labels': LabelsProvider(),
            'nav': NavProvider(engine),
            'orbits': OrbitsProvider(),
            'scales': ScalesProvider(),
            'selected': SelectedProvider(engine),
            'settings': SettingsProvider(),
            'time': TimeProvider(engine),
            'units': UnitsProvider(),
        }

    def compile_expression(self, source: str):
        try:
            return self.env.compile_expression(source, undefined_to_none=False)
        except jinja2.exceptions.TemplateError:
            print(f"Error while compiling '{source}'")
            raise

    def create_template(self, source: str):
        try:
            return self.env.from_string(source)
        except jinja2.exceptions.TemplateError:
            print(f"Error while compiling '{source}'")
            raise
