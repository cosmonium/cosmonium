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


from direct.showbase.ShowBaseGlobal import globalClock
from math import pi, exp
from panda3d.core import LVector3, LVector3d, LPoint3d, LQuaterniond
import sys

from . import settings
from .astro import units


class NavigationController:
    def __init__(self):
        self.base = None
        self.camera = None
        self.camera_controller = None
        self.controller = None

    def init(self, base, camera, camera_controller, controller):
        self.base = base
        self.camera = camera
        self.camera_controller = camera_controller
        self.controller = controller

    def set_target(self, target):
        pass

    def get_name(self):
        return ''

    def get_id(self):
        return ''

    def require_target(self):
        return False

    def require_controller(self):
        return False

    def register_events(self, event_ctrl):
        # TODO: Should inherit from DirectObject and use own event handler
        pass

    def remove_events(self, event_ctrl):
        pass

    def set_controller(self, controller):
        self.controller = controller

    def set_camera_controller(self, camera_controller):
        self.camera_controller = camera_controller

    def stash_position(self):
        pass

    def pop_position(self):
        pass

    def update(self, time, dt):
        pass


class InteractiveNavigationController(NavigationController):
    wheel_event_duration = 0.1

    def __init__(self):
        NavigationController.__init__(self)
        self.keyMap = {}
        self.orbit_center = LPoint3d()
        self.orbit_start = None
        self.orbit_orientation = None
        self.wheel_event_time = 0.0
        self.wheel_direction = 0.0

    def get_name(self):
        return 'Free navigation'

    def setKey(self, key, state, *keys):
        self.keyMap[key] = state
        for key in keys:
            self.keyMap[key] = state

    def register_wheel_events(self, event_ctrl):
        event_ctrl.accept("wheel_up", self.wheel_event, [1])
        event_ctrl.accept("wheel_down", self.wheel_event, [-1])

    def remove_wheel_events(self, event_ctrl):
        event_ctrl.ignore("wheel_up")
        event_ctrl.ignore("wheel_down")

    def wheel_event(self, direction):
        if settings.invert_wheel:
            direction = -direction
        self.wheel_event_time = globalClock.get_real_time()
        self.wheel_direction = direction

    def stash_position(self):
        self.orbit_center = self.controller.anchor.calc_absolute_position_of(self.orbit_center)

    def pop_position(self):
        self.orbit_center = self.controller.anchor.calc_frame_position_of_absolute(self.orbit_center)

    def create_orbit_params(self, target, surface=False):
        # Orbiting around a body involve both the object and the camera controller
        # The orbit position is set on the object while the camera orientation is set on the camera controller
        # The position must be done in the object frame otherwise the orbit point will drift away
        center = target.anchor.calc_absolute_relative_position_to(self.controller.get_absolute_reference_point())
        if surface:
            # Set the orbit center at the surface of the body
            center += target.anchor.vector_to_obs * target.anchor._height_under
        self.orbit_center = self.controller.anchor.calc_frame_position_of_local(center)
        self.orbit_start = self.controller.get_frame_position() - self.orbit_center
        if self.controller.orbit_rot_camera:
            self.orbit_orientation = self.camera_controller.get_local_orientation()
        else:
            self.orbit_orientation = self.controller.get_frame_orientation()

    def do_orbit(self, z_angle, x_angle):
        z_rotation = LQuaterniond()
        x_rotation = LQuaterniond()
        try:
            orbit_z_axis = self.orbit_orientation.xform(LVector3d.up())
            orbit_x_axis = self.orbit_orientation.xform(LVector3d.right())
            z_rotation.set_from_axis_angle_rad(z_angle, orbit_z_axis)
            x_rotation.set_from_axis_angle_rad(x_angle, orbit_x_axis)
        except AssertionError as e:
            print("Wrong orbit axis :", e)
        combined = x_rotation * z_rotation
        new_rot = self.orbit_orientation * combined
        if self.controller.orbit_rot_camera:
            self.camera_controller.set_local_orientation(new_rot)
        else:
            self.controller.set_frame_orientation(new_rot)
        try:
            if self.controller.orbit_rot_camera:
                orbit_orientation = self.controller.anchor.calc_frame_orientation_of(self.orbit_orientation)
            else:
                orbit_orientation = self.orbit_orientation
            orbit_z_axis = orbit_orientation.xform(LVector3d.up())
            orbit_x_axis = orbit_orientation.xform(LVector3d.right())
            z_rotation.set_from_axis_angle_rad(z_angle, orbit_z_axis)
            x_rotation.set_from_axis_angle_rad(x_angle, orbit_x_axis)
        except AssertionError as e:
            print("Wrong orbit axis :", e)
        combined = x_rotation * z_rotation
        delta = combined.xform(self.orbit_start)
        self.controller.set_frame_position(delta + self.orbit_center)


class FreeNav(InteractiveNavigationController):
    distance_speed = 2.0
    rotation_speed = 2 * pi / 3
    rotation_damping = 2.0

    def __init__(self):
        InteractiveNavigationController.__init__(self)
        self.speed = 0.0
        self.rot_speed = LVector3d()
        self.mouse_orbit = False
        self.keyboardTrack = False
        self.startX = None
        self.startY = None
        self.orbit_coef = 0.0
        self.orbit_x = 0.0
        self.orbit_z = 0.0

    def get_name(self):
        return 'Free navigation'

    def get_id(self):
        return 'free'

    def register_events(self, event_ctrl):
        self.keyMap = {
            "left": 0,
            "right": 0,
            "up": 0,
            "down": 0,
            "home": 0,
            "end": 0,
            "control-left": 0,
            "control-right": 0,
            "shift-left": 0,
            "shift-right": 0,
            "shift-up": 0,
            "shift-down": 0,
            "a": 0,
            "z": 0,
        }
        event_ctrl.accept("arrow_up", self.setKey, ['up', 1])
        event_ctrl.accept("arrow_up-up", self.setKey, ['up', 0, 'shift-up'])
        event_ctrl.accept("arrow_down", self.setKey, ['down', 1])
        event_ctrl.accept("arrow_down-up", self.setKey, ['down', 0, 'shift-down'])
        event_ctrl.accept("shift-arrow_up", self.setKey, ['shift-up', 1])
        event_ctrl.accept("shift-arrow_down", self.setKey, ['shift-down', 1])
        event_ctrl.accept("arrow_left", self.setKey, ['left', 1])
        event_ctrl.accept("arrow_left-up", self.setKey, ['left', 0, 'shift-left', 'control-left'])
        event_ctrl.accept("arrow_right", self.setKey, ['right', 1])
        event_ctrl.accept("arrow_right-up", self.setKey, ['right', 0, 'shift-right', 'control-right'])
        event_ctrl.accept("shift-arrow_left", self.setKey, ['shift-left', 1])
        event_ctrl.accept("shift-arrow_right", self.setKey, ['shift-right', 1])
        if sys.platform != "darwin":
            event_ctrl.accept("control-arrow_left", self.setKey, ['control-left', 1])
            event_ctrl.accept("control-arrow_right", self.setKey, ['control-right', 1])
        else:
            event_ctrl.accept("alt-arrow_left", self.setKey, ['control-left', 1])
            event_ctrl.accept("alt-arrow_right", self.setKey, ['control-right', 1])
        event_ctrl.accept("home", self.setKey, ['home', 1])
        event_ctrl.accept("home-up", self.setKey, ['home', 0])
        event_ctrl.accept("end", self.setKey, ['end', 1])
        event_ctrl.accept("end-up", self.setKey, ['end', 0])
        event_ctrl.accept("a", self.setKey, ['a', 1])
        event_ctrl.accept("a-up", self.setKey, ['a', 0])
        event_ctrl.accept("z", self.setKey, ['z', 1])
        event_ctrl.accept("z-up", self.setKey, ['z', 0])
        event_ctrl.accept("q", self.switchDirection)
        event_ctrl.accept("s", self.stop)
        event_ctrl.accept("x", self.align_camera)

        event_ctrl.accept("mouse3", self.on_orbit_click, [False])
        event_ctrl.accept("shift-mouse3", self.on_orbit_click, [True])
        event_ctrl.accept("mouse3-up", self.on_orbit_release)

        self.register_wheel_events(event_ctrl)

    def remove_events(self, event_ctrl):
        event_ctrl.ignore("arrow_up")
        event_ctrl.ignore("arrow_up-up")
        event_ctrl.ignore("arrow_down")
        event_ctrl.ignore("arrow_down-up")
        event_ctrl.ignore("shift-arrow_up")
        event_ctrl.ignore("shift-arrow_down")
        event_ctrl.ignore("arrow_left")
        event_ctrl.ignore("arrow_left-up")
        event_ctrl.ignore("arrow_right")
        event_ctrl.ignore("arrow_right-up")
        event_ctrl.ignore("shift-arrow_left")
        event_ctrl.ignore("shift-arrow_right")
        if sys.platform != "darwin":
            event_ctrl.ignore("control-arrow_left")
            event_ctrl.ignore("control-arrow_right")
        else:
            event_ctrl.ignore("alt-arrow_left")
            event_ctrl.ignore("alt-arrow_right")
        event_ctrl.ignore("home")
        event_ctrl.ignore("home-up")
        event_ctrl.ignore("end")
        event_ctrl.ignore("end-up")
        event_ctrl.ignore("a")
        event_ctrl.ignore("a-up")
        event_ctrl.ignore("z")
        event_ctrl.ignore("z-up")
        event_ctrl.ignore("q")
        event_ctrl.ignore("s")

        event_ctrl.ignore("mouse3")
        event_ctrl.ignore("shift-mouse3")
        event_ctrl.ignore("mouse3-up")

        self.remove_wheel_events(event_ctrl)

    def select_target(self):
        if self.base.follow is not None:
            target = self.base.follow
        elif self.base.sync is not None:
            target = self.base.sync
        elif self.base.selected is not None:
            target = self.base.selected
        else:
            target = None
        return target

    def switchDirection(self):
        self.speed = -self.speed

    def stop(self):
        self.speed = 0

    def align_camera(self):
        self.camera_controller.prepare_movement()

    def on_orbit_click(self, orbit_surface):
        if not self.base.mouseWatcherNode.hasMouse():
            return
        mpos = self.base.mouseWatcherNode.getMouse()
        self.start_x = mpos.get_x()
        self.start_y = mpos.get_y()
        target = self.select_target()
        if target is not None:
            self.mouse_orbit = True
            if orbit_surface:
                # When orbiting a point on the surface, the orbit speed should be constant
                self.orbit_angle_x = pi / 3
                self.orbit_angle_y = pi / 3
            else:
                # Adapt the orbit speed so that orbiting is still manageable when close to the body
                arc_length = pi * target.get_apparent_radius()
                apparent_size = arc_length / (
                    (target.anchor.distance_to_obs - target.anchor._height_under) * self.camera.pixel_size
                )
                if apparent_size != 0.0:
                    self.orbit_angle_x = min(pi, pi / 2 / apparent_size * self.camera.height)
                    self.orbit_angle_y = min(pi, pi / 2 / apparent_size * self.camera.width)
                else:
                    # Body has no defined surface, use constant orbit speed
                    self.orbit_angle_x = pi
                    self.orbit_angle_y = pi
            self.create_orbit_params(target, orbit_surface)

    def on_orbit_release(self):
        self.mouse_orbit = False

    def update(self, time, dt):
        rot_x = 0.0
        rot_y = 0.0
        rot_z = 0.0
        distance = 0.0
        if self.mouse_orbit and self.base.mouseWatcherNode.hasMouse():
            mpos = self.base.mouseWatcherNode.getMouse()
            delta_x = mpos.get_x() - self.start_x
            delta_y = mpos.get_y() - self.start_y
            z_angle = -delta_x * self.orbit_angle_x
            x_angle = delta_y * self.orbit_angle_y
            self.do_orbit(z_angle, x_angle)

        if settings.celestia_nav:
            if self.keyMap['up']:
                rot_x = -1
            if self.keyMap['down']:
                rot_x = 1
            if self.keyMap['left']:
                rot_y = -1
            if self.keyMap['right']:
                rot_y = 1
        else:
            if self.keyMap['up']:
                rot_x = 1
            if self.keyMap['down']:
                rot_x = -1
            if self.keyMap['left']:
                rot_y = 1
            if self.keyMap['right']:
                rot_y = -1
        if self.keyMap['control-left']:
            rot_z = 1
        if self.keyMap['control-right']:
            rot_z = -1

        if self.keyMap['home']:
            distance = 1
        if self.keyMap['end']:
            distance = -1

        if self.wheel_event_time + self.wheel_event_duration > globalClock.get_real_time():
            distance = self.wheel_direction

        if not self.keyboardTrack and (
            self.keyMap['shift-left']
            or self.keyMap['shift-right']
            or self.keyMap['shift-up']
            or self.keyMap['shift-down']
        ):
            target = self.select_target()
            if target is not None:
                self.keyboardTrack = True
                arc_length = pi * target.get_apparent_radius()
                apparent_size = arc_length / (target.anchor.distance_to_obs - target.anchor._height_under)
                if apparent_size != 0:
                    self.orbit_coef = min(pi, pi / 2 / apparent_size)
                else:
                    self.orbit_coef = pi
                self.orbit_x = 0.0
                self.orbit_z = 0.0
                self.create_orbit_params(target)

        if self.keyboardTrack:
            if not (
                self.keyMap['shift-left']
                or self.keyMap['shift-right']
                or self.keyMap['shift-up']
                or self.keyMap['shift-down']
            ):
                self.keyboardTrack = False

            if self.keyMap['shift-left']:
                self.orbit_z += self.orbit_coef * dt
                self.do_orbit(self.orbit_z, self.orbit_x)

            if self.keyMap['shift-right']:
                self.orbit_z -= self.orbit_coef * dt
                self.do_orbit(self.orbit_z, self.orbit_x)

            if self.keyMap['shift-up']:
                self.orbit_x += self.orbit_coef * dt
                self.do_orbit(self.orbit_z, self.orbit_x)

            if self.keyMap['shift-down']:
                self.orbit_x -= self.orbit_coef * dt
                self.do_orbit(self.orbit_z, self.orbit_x)

        if self.keyMap['a'] or self.keyMap['z'] or rot_x != 0 or rot_y != 0 or rot_z != 0:
            self.camera_controller.prepare_movement()

        if self.keyMap['a']:
            if self.speed == 0:
                self.speed = 0.1
            else:
                self.speed *= exp(dt * 3)

        if self.keyMap['z']:
            if self.speed < 1e-5:
                self.speed = 0
            else:
                self.speed /= exp(dt * 3)
        y = self.speed * dt
        self.controller.step_relative(y)

        if settings.damped_nav:
            self.rot_speed *= exp(-dt * self.rotation_damping)
            self.rot_speed += LVector3d(rot_x, rot_y, rot_z) * self.rotation_speed * dt
        else:
            self.rot_speed = LVector3d(rot_x, rot_y, rot_z) * self.rotation_speed
        self.turn(LVector3d.right(), self.rot_speed.x * dt)
        self.turn(LVector3d.forward(), self.rot_speed.y * dt)
        self.turn(LVector3d.up(), self.rot_speed.z * dt)
        self.change_altitude(distance * self.distance_speed * dt)

    def turn(self, axis, angle):
        rot = LQuaterniond()
        rot.setFromAxisAngleRad(angle, axis)
        self.controller.step_turn(rot)

    def change_altitude(self, rate):
        if rate == 0.0:
            return
        target = self.select_target()
        if target is None:
            return
        local_position = self.controller.anchor.calc_absolute_relative_position_to(
            target.anchor.get_absolute_reference_point()
        )
        (tangent, binormal, normal) = target.get_tangent_plane_under(local_position)
        surface_point = target.get_point_under(local_position)
        direction = local_position - surface_point
        altitude = direction.dot(normal)
        if altitude > 0:
            if rate < 0 or altitude >= settings.min_altitude:
                self.controller.delta_local(-normal * altitude * rate)
        else:
            self.controller.set_local_position(surface_point + settings.min_altitude * normal)


class WalkNav(InteractiveNavigationController):
    rot_step_per_sec = pi / 4
    speed = 10 * units.m
    distance_speed = 2.0

    def __init__(self):
        InteractiveNavigationController.__init__(self)
        self.speed_factor = 1.0

    def get_name(self):
        return 'Fly'

    def get_id(self):
        return 'walk'

    def require_target(self):
        return True

    def set_target(self, target):
        self.body = target

    def register_events(self, event_ctrl):
        self.keyMap = {
            "left": 0,
            "right": 0,
            "up": 0,
            "down": 0,
            "home": 0,
            "end": 0,
            "shift-left": 0,
            "shift-right": 0,
            "shift-up": 0,
            "shift-down": 0,
            "control-left": 0,
            "control-right": 0,
        }
        event_ctrl.accept("arrow_up", self.setKey, ['up', 1])
        event_ctrl.accept("arrow_up-up", self.setKey, ['up', 0, 'shift-up'])
        event_ctrl.accept("arrow_down", self.setKey, ['down', 1])
        event_ctrl.accept("arrow_down-up", self.setKey, ['down', 0, 'shift-down'])
        event_ctrl.accept("arrow_left", self.setKey, ['left', 1])
        event_ctrl.accept("arrow_left-up", self.setKey, ['left', 0, 'shift-left', 'control-left'])
        event_ctrl.accept("arrow_right", self.setKey, ['right', 1])
        event_ctrl.accept("arrow_right-up", self.setKey, ['right', 0, 'shift-right', 'control-right'])
        event_ctrl.accept("shift-arrow_up", self.setKey, ['shift-up', 1])
        event_ctrl.accept("shift-arrow_down", self.setKey, ['shift-down', 1])
        event_ctrl.accept("shift-arrow_left", self.setKey, ['shift-left', 1])
        event_ctrl.accept("shift-arrow_right", self.setKey, ['shift-right', 1])
        if sys.platform != "darwin":
            event_ctrl.accept("control-arrow_left", self.setKey, ['control-left', 1])
            event_ctrl.accept("control-arrow_right", self.setKey, ['control-right', 1])
        else:
            event_ctrl.accept("alt-arrow_left", self.setKey, ['control-left', 1])
            event_ctrl.accept("alt-arrow_right", self.setKey, ['control-right', 1])
        event_ctrl.accept("home", self.setKey, ['home', 1])
        event_ctrl.accept("home-up", self.setKey, ['home', 0])
        event_ctrl.accept("end", self.setKey, ['end', 1])
        event_ctrl.accept("end-up", self.setKey, ['end', 0])

        self.register_wheel_events(event_ctrl)

        event_ctrl.accept("a", self.fast)
        event_ctrl.accept("a-up", self.slow)

    def remove_events(self, event_ctrl):
        event_ctrl.ignore("arrow_up")
        event_ctrl.ignore("arrow_up-up")
        event_ctrl.ignore("arrow_down")
        event_ctrl.ignore("arrow_down-up")
        event_ctrl.ignore("arrow_left")
        event_ctrl.ignore("arrow_left-up")
        event_ctrl.ignore("arrow_right")
        event_ctrl.ignore("arrow_right-up")
        event_ctrl.ignore("shift-arrow_up")
        event_ctrl.ignore("shift-arrow_down")
        event_ctrl.ignore("shift-arrow_left")
        event_ctrl.ignore("shift-arrow_right")
        if sys.platform != "darwin":
            event_ctrl.ignore("control-arrow_left")
            event_ctrl.ignore("control-arrow_right")
        else:
            event_ctrl.ignore("alt-arrow_left")
            event_ctrl.ignore("alt-arrow_right")
        event_ctrl.ignore("home")
        event_ctrl.ignore("home-up")

        self.remove_wheel_events(event_ctrl)

        event_ctrl.ignore("a")
        event_ctrl.ignore("a-up")

    def fast(self):
        self.speed_factor = 10.0

    def slow(self):
        self.speed_factor = 1.0

    def update(self, time, dt):
        if self.keyMap['up']:
            self.step(self.speed * self.speed_factor * dt)

        if self.keyMap['down']:
            self.step(-self.speed * self.speed_factor * dt)

        if self.keyMap['left']:
            self.turn(LVector3d.up(), self.rot_step_per_sec * dt)

        if self.keyMap['right']:
            self.turn(LVector3d.up(), -self.rot_step_per_sec * dt)

        if self.keyMap['shift-up']:
            self.turn(LVector3d.right(), self.rot_step_per_sec * dt)

        if self.keyMap['shift-down']:
            self.turn(LVector3d.right(), -self.rot_step_per_sec * dt)

        if self.keyMap['shift-left']:
            self.turn(LVector3d.up(), self.rot_step_per_sec * dt)

        if self.keyMap['shift-right']:
            self.turn(LVector3d.up(), -self.rot_step_per_sec * dt)

        if self.keyMap['control-left']:
            self.turn(LVector3d.forward(), self.rot_step_per_sec * dt)

        if self.keyMap['control-right']:
            self.turn(LVector3d.forward(), -self.rot_step_per_sec * dt)

        if self.keyMap['home']:
            self.change_altitude(self.distance_speed * dt)

        if self.keyMap['end']:
            self.change_altitude(-self.distance_speed * dt)

        if self.wheel_event_time + self.wheel_event_duration > globalClock.get_real_time():
            distance = self.wheel_direction
            self.change_altitude(distance * self.distance_speed * dt)

    def step(self, distance):
        object_position = self.controller.get_local_position()
        (_lon, _lat, normal) = self.body.get_tangent_plane_under(object_position)
        surface_point = self.body.get_point_under(self.controller.get_local_position())
        direction = self.controller.get_local_position() - surface_point
        altitude = direction.dot(normal)
        direction = self.controller.get_absolute_orientation().xform(LVector3d.forward())
        projected = direction - normal * direction.dot(normal)
        projected.normalize()
        new_position = self.body.get_point_under(object_position + projected * distance)
        (_lon, _lat, normal) = self.body.get_tangent_plane_under(new_position)
        self.controller.set_local_position(new_position + normal * altitude)

    def change_altitude(self, rate):
        if rate == 0.0:
            return
        (tangent, binormal, normal) = self.body.get_tangent_plane_under(self.controller.get_local_position())
        surface_point = self.body.get_point_under(self.controller.get_local_position())
        direction = self.controller.get_local_position() - surface_point
        altitude = direction.dot(normal)
        if altitude > 0:
            if rate < 0 or altitude >= settings.min_altitude:
                self.controller.delta_local(-normal * altitude * rate)
        else:
            self.controller.set_local_position(surface_point + settings.min_altitude * normal)

    def turn(self, axis, angle):
        rot = LQuaterniond()
        rot.setFromAxisAngleRad(angle, axis)
        self.controller.step_turn(rot)


class ControlNav(InteractiveNavigationController):
    rot_step_per_sec = pi / 4
    speed = 10 * units.m
    distance_speed = 2.0

    def __init__(self):
        InteractiveNavigationController.__init__(self)
        self.controller = None
        self.speed_factor = 1.0

    def get_name(self):
        return 'Control body'

    def get_id(self):
        return 'control'

    def require_controller(self):
        return True

    def set_controller(self, controller):
        self.controller = controller

    def register_events(self, event_ctrl):
        self.keyMap = {
            "left": 0,
            "right": 0,
            "up": 0,
            "down": 0,
            "home": 0,
            "end": 0,
        }
        event_ctrl.accept("arrow_up", self.setKey, ['up', 1])
        event_ctrl.accept("arrow_up-up", self.setKey, ['up', 0])
        event_ctrl.accept("arrow_down", self.setKey, ['down', 1])
        event_ctrl.accept("arrow_down-up", self.setKey, ['down', 0])
        event_ctrl.accept("arrow_left", self.setKey, ['left', 1])
        event_ctrl.accept("arrow_left-up", self.setKey, ['left', 0])
        event_ctrl.accept("arrow_right", self.setKey, ['right', 1])
        event_ctrl.accept("arrow_right-up", self.setKey, ['right', 0])
        event_ctrl.accept("home", self.setKey, ['home', 1])
        event_ctrl.accept("home-up", self.setKey, ['home', 0])
        event_ctrl.accept("end", self.setKey, ['end', 1])
        event_ctrl.accept("end-up", self.setKey, ['end', 0])

        self.register_wheel_events(event_ctrl)

        event_ctrl.accept("a", self.fast)
        event_ctrl.accept("a-up", self.slow)

    def remove_events(self, event_ctrl):
        event_ctrl.ignore("arrow_up")
        event_ctrl.ignore("arrow_up-up")
        event_ctrl.ignore("arrow_down")
        event_ctrl.ignore("arrow_down-up")
        event_ctrl.ignore("arrow_left")
        event_ctrl.ignore("arrow_left-up")
        event_ctrl.ignore("arrow_right")
        event_ctrl.ignore("arrow_right-up")
        event_ctrl.ignore("home")
        event_ctrl.ignore("home-up")

        self.remove_wheel_events(event_ctrl)

        event_ctrl.ignore("a")
        event_ctrl.ignore("a-up")

    def fast(self):
        self.speed_factor = 10.0

    def slow(self):
        self.speed_factor = 1.0

    def update(self, time, dt):
        is_moving = False
        if self.keyMap['up']:
            self.step(self.speed * self.speed_factor * dt)
            is_moving = True

        if self.keyMap['down']:
            self.step(-self.speed * self.speed_factor * dt)
            is_moving = True

        if self.keyMap['left']:
            self.turn(self.rot_step_per_sec * dt)

        if self.keyMap['right']:
            self.turn(-self.rot_step_per_sec * dt)

        if self.keyMap['home']:
            self.change_altitude(self.distance_speed * dt)

        if self.keyMap['end']:
            self.change_altitude(-self.distance_speed * dt)

        if self.wheel_event_time + self.wheel_event_duration > globalClock.get_real_time():
            distance = self.wheel_direction
            self.change_altitude(distance * self.distance_speed * dt)

        if is_moving:
            self.controller.set_state('moving')
        else:
            self.controller.set_state('idle')

    def step(self, distance):
        self.controller.step_relative(distance)

    def change_altitude(self, rate):
        if rate == 0.0:
            return

    def turn(self, angle):
        self.controller.turn_relative(angle)


class KineticNav(InteractiveNavigationController):
    rot_step_per_sec = pi / 4
    speed = 10 * units.m
    distance_speed = 2.0

    def __init__(self):
        InteractiveNavigationController.__init__(self)
        self.controller = None
        self.speed_factor = 1.0

    def get_name(self):
        return 'Kinetic control'

    def get_id(self):
        return 'kinetic'

    def require_controller(self):
        return True

    def set_controller(self, controller):
        self.controller = controller

    def register_events(self, event_ctrl):
        self.keyMap = {"left": 0, "right": 0, "up": 0, "down": 0, "home": 0, "end": 0, "jump": 0}
        event_ctrl.accept("arrow_up", self.setKey, ['up', 1])
        event_ctrl.accept("arrow_up-up", self.setKey, ['up', 0])
        event_ctrl.accept("arrow_down", self.setKey, ['down', 1])
        event_ctrl.accept("arrow_down-up", self.setKey, ['down', 0])
        event_ctrl.accept("arrow_left", self.setKey, ['left', 1])
        event_ctrl.accept("arrow_left-up", self.setKey, ['left', 0])
        event_ctrl.accept("arrow_right", self.setKey, ['right', 1])
        event_ctrl.accept("arrow_right-up", self.setKey, ['right', 0])
        event_ctrl.accept(" ", self.setKey, ['jump', 1])
        event_ctrl.accept(" -up", self.setKey, ['jump', 0])

    def remove_events(self, event_ctrl):
        event_ctrl.ignore("arrow_up")
        event_ctrl.ignore("arrow_up-up")
        event_ctrl.ignore("arrow_down")
        event_ctrl.ignore("arrow_down-up")
        event_ctrl.ignore("arrow_left")
        event_ctrl.ignore("arrow_left-up")
        event_ctrl.ignore("arrow_right")
        event_ctrl.ignore("arrow_right-up")
        event_ctrl.ignore(" ")
        event_ctrl.ignore(" -up")

    def update(self, time, dt):
        is_moving = False
        speed = LVector3(0, 0, 0)
        y = self.keyMap['up'] - self.keyMap['down']
        if y:
            speed.set_y(y * self.speed * self.speed_factor)
            is_moving = True

        if self.keyMap['left']:
            self.turn(self.rot_step_per_sec * dt)

        if self.keyMap['right']:
            self.turn(-self.rot_step_per_sec * dt)

        self.set_speed_relative(speed)

        if is_moving:
            self.controller.set_state('moving')
        else:
            self.controller.set_state('idle')

    def set_speed_relative(self, speed):
        self.controller.set_speed_relative(speed)

    def turn(self, angle):
        self.controller.turn_relative(angle)
