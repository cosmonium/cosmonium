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

from panda3d.core import LVector3d, LQuaterniond
from . import settings
from .astro import units
from math import pi, exp
import sys

class NavBase(object):
    wheel_event_duration = 0.1

    def __init__(self):
        self.base = None
        self.observer = None
        self.keyMap = {}
        self.dragCenter = None
        self.dragDir = None
        self.dragOrientation = None
        self.dragZAxis = None
        self.dragXAxis = None
        self.wheel_event_time = 0.0
        self.wheel_direction = 0.0

    def init(self, base, camera, ui):
        self.base = base
        self.observer = camera
        self.ui = ui

    def setKey(self, key, state, *keys):
        self.keyMap[key] = state
        for key in keys:
            self.keyMap[key] = state

    def register_events(self, event_ctrl):
        pass

    def remove_events(self, event_ctrl):
        pass

    def register_wheel_events(self, event_ctrl):
        if settings.invert_wheel:
            event_ctrl.accept("wheel_up", self.wheel_event, [1])
            event_ctrl.accept("wheel_down", self.wheel_event, [-1])
        else:
            event_ctrl.accept("wheel_up", self.wheel_event, [-1])
            event_ctrl.accept("wheel_down", self.wheel_event, [1])

    def remove_wheel_events(self, event_ctrl):
        event_ctrl.ignore("wheel_up")
        event_ctrl.ignore("wheel_down")

    def wheel_event(self, direction):
        self.wheel_event_time = globalClock.getRealTime()
        self.wheel_direction = direction

    def stash_position(self):
        self.dragCenter = self.observer.get_position_of(self.dragCenter)

    def pop_position(self):
        self.dragCenter = self.observer.get_rel_position_of(self.dragCenter, local=False)

    def create_drag_params(self, target):
        center = target.get_rel_position_to(self.observer.camera_global_pos)
        self.dragCenter = self.observer.camera_frame.get_rel_position(center)
        dragPosition = self.observer.get_frame_camera_pos()
        self.dragDir = self.dragCenter - dragPosition
        self.dragOrientation = self.observer.get_frame_camera_rot()
        self.dragZAxis = self.dragOrientation.xform(LVector3d.up())
        self.dragXAxis = self.dragOrientation.xform(LVector3d.right())

    def do_drag(self, z_angle, x_angle, move=False, rotate=True):
        zRotation = LQuaterniond()
        zRotation.setFromAxisAngleRad(z_angle, self.dragZAxis)
        xRotation = LQuaterniond()
        xRotation.setFromAxisAngleRad(x_angle, self.dragXAxis)
        combined = xRotation * zRotation
        if move:
            delta = combined.xform(-self.dragDir)
            self.observer.set_frame_camera_pos(delta + self.dragCenter)
            self.observer.set_frame_camera_rot(self.dragOrientation * combined)
        else:
            self.observer.set_camera_rot(self.dragOrientation * combined)

    def update(self, dt):
        pass

class FreeNav(NavBase):
    rot_step_per_sec = pi/2
    incr_speed_rot_step_per_sec = 0.7
    decr_speed_rot_step_per_sec = incr_speed_rot_step_per_sec * 2.0
    distance_speed = 2.0

    def __init__(self):
        NavBase.__init__(self)
        self.speed = 0.0
        self.mouseSelectClick = False
        self.mouseTrackClick = False
        self.keyboardTrack = False
        self.startX = None
        self.startY = None
        self.drag_coef = 0.0
        self.drag_x = 0.0
        self.drag_z = 0.0
        self.dragCenter = LVector3d()
        self.current_rot_x_speed = 0.0
        self.current_rot_y_speed = 0.0
        self.current_rot_z_speed = 0.0

    def register_events(self, event_ctrl):
        self.keyMap = {"left": 0, "right": 0,
                       "up": 0, "down": 0,
                       "home": 0, "end": 0,
                       "control-left": 0, "control-right": 0,
                       "shift-left": 0, "shift-right": 0,
                       "shift-up": 0, "shift-down": 0,
                       "a": 0, "z": 0}
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

        event_ctrl.accept("mouse1", self.OnSelectClick )
        event_ctrl.accept("mouse1-up", self.OnSelectRelease )
        event_ctrl.accept("mouse3", self.OnTrackClick )
        event_ctrl.accept("mouse3-up", self.OnTrackRelease )

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

        event_ctrl.ignore("mouse1")
        event_ctrl.ignore("mouse1-up")
        event_ctrl.ignore("mouse3")
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

    def OnSelectClick(self):
        if self.base.mouseWatcherNode.hasMouse():
            self.mouseSelectClick = True
            mpos = self.base.mouseWatcherNode.getMouse()
            self.startX = mpos.getX()
            self.startY = mpos.getY()
            self.dragCenter = self.observer.get_camera_pos()
            self.dragOrientation = self.observer.get_camera_rot()
            self.dragZAxis = self.dragOrientation.xform(LVector3d.up())
            self.dragXAxis = self.dragOrientation.xform(LVector3d.right())

    def OnSelectRelease(self):
        if self.base.mouseWatcherNode.hasMouse():
            mpos = self.base.mouseWatcherNode.getMouse()
            if self.startX == mpos.getX() and self.startY == mpos.getY():
                self.ui.left_click()
        self.mouseSelectClick = False

    def OnTrackClick(self):
        if not self.base.mouseWatcherNode.hasMouse(): return
        mpos = self.base.mouseWatcherNode.getMouse()
        self.startX = mpos.getX()
        self.startY = mpos.getY()
        target = self.select_target()
        if target is not None:
            self.mouseTrackClick = True
            arc_length = pi * target.get_apparent_radius()
            apparent_size = arc_length / ((target.distance_to_obs - target.height_under) * self.observer.pixel_size)
            if apparent_size != 0.0:
                self.dragAngleX = min(pi, pi / 2 / apparent_size * self.observer.height)
                self.dragAngleY = min(pi, pi / 2 / apparent_size * self.observer.width)
            else:
                self.dragAngleX = pi
                self.dragAngleY = pi
            self.create_drag_params(target)

    def OnTrackRelease(self):
        if self.base.mouseWatcherNode.hasMouse():
            mpos = self.base.mouseWatcherNode.getMouse()
            if self.startX == mpos.getX() and self.startY == mpos.getY():
                self.ui.right_click()
        self.mouseTrackClick = False

    def update(self, dt):
        rot_x = 0.0
        rot_y = 0.0
        rot_z = 0.0
        distance = 0.0
        if self.mouseTrackClick and self.base.mouseWatcherNode.hasMouse():
            mpos = self.base.mouseWatcherNode.getMouse()
            deltaX = mpos.getX() - self.startX
            deltaY = mpos.getY() - self.startY
            z_angle = -deltaX * self.dragAngleX
            x_angle = deltaY * self.dragAngleY
            self.do_drag(z_angle, x_angle, True)

        if self.mouseSelectClick and self.base.mouseWatcherNode.hasMouse():
            mpos = self.base.mouseWatcherNode.getMouse()
            deltaX = mpos.getX() - self.startX
            deltaY = mpos.getY() - self.startY
            z_angle = deltaX * self.observer.realCamLens.getHfov() / 180 * pi / 2
            x_angle = -deltaY * self.observer.realCamLens.getVfov() / 180 * pi / 2
            self.do_drag(z_angle, x_angle)

        if settings.celestia_nav:
            if self.keyMap['up']:
                rot_x = -1
            if self.keyMap['down']:
                rot_x = 1
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

        if self.wheel_event_time + self.wheel_event_duration > globalClock.getRealTime():
            distance = self.wheel_direction

        if not self.keyboardTrack and (self.keyMap['shift-left'] or self.keyMap['shift-right'] or self.keyMap['shift-up'] or self.keyMap['shift-down']):
            target = self.select_target()
            if target is not None:
                self.keyboardTrack = True
                arc_length = pi * target.get_apparent_radius()
                apparent_size = arc_length / (target.distance_to_obs - target.height_under)
                if apparent_size != 0:
                    self.drag_coef = min(pi, pi / 2 / apparent_size)
                else:
                    self.drag_coef = pi
                self.drag_x = 0.0
                self.drag_z = 0.0
                self.create_drag_params(target)

        if self.keyboardTrack:
            if not (self.keyMap['shift-left'] or self.keyMap['shift-right'] or self.keyMap['shift-up'] or self.keyMap['shift-down']):
                self.keyboardTrack = False

            if self.keyMap['shift-left']:
                self.drag_z += self.drag_coef * dt
                self.do_drag(self.drag_z, self.drag_x, True)

            if self.keyMap['shift-right']:
                self.drag_z -= self.drag_coef * dt
                self.do_drag(self.drag_z, self.drag_x, True)

            if self.keyMap['shift-up']:
                self.drag_x += self.drag_coef * dt
                self.do_drag(self.drag_z, self.drag_x, True)

            if self.keyMap['shift-down']:
                self.drag_x -= self.drag_coef * dt
                self.do_drag(self.drag_z, self.drag_x, True)

        if self.keyMap['a']:
            if self.speed == 0:
                self.speed = 0.1
            else:
                self.speed *= exp(dt*3)

        if self.keyMap['z']:
            if self.speed < 1e-5:
                self.speed = 0
            else:
                self.speed /= exp(dt*3)
        y = self.speed * dt
        self.stepRelative(0, y, 0)

        if settings.damped_nav:
            #TODO: Refactor this wall of code...
            if rot_x > 0:
                self.current_rot_x_speed += self.incr_speed_rot_step_per_sec * dt
                self.current_rot_x_speed = min(self.current_rot_x_speed, self.rot_step_per_sec)
            elif rot_x < 0:
                self.current_rot_x_speed -= self.incr_speed_rot_step_per_sec * dt
                self.current_rot_x_speed = max(self.current_rot_x_speed, -self.rot_step_per_sec)
            elif self.current_rot_x_speed > 0.0:
                self.current_rot_x_speed -= self.decr_speed_rot_step_per_sec * dt
                self.current_rot_x_speed = max(0.0, self.current_rot_x_speed)
            elif self.current_rot_x_speed < 0.0:
                self.current_rot_x_speed += self.decr_speed_rot_step_per_sec * dt
                self.current_rot_x_speed = min(0.0, self.current_rot_x_speed)
            if rot_y > 0:
                self.current_rot_y_speed += self.incr_speed_rot_step_per_sec * dt
                self.current_rot_y_speed = min(self.current_rot_y_speed, self.rot_step_per_sec)
            elif rot_y < 0:
                self.current_rot_y_speed -= self.incr_speed_rot_step_per_sec * dt
                self.current_rot_y_speed = max(self.current_rot_y_speed, -self.rot_step_per_sec)
            elif self.current_rot_y_speed > 0.0:
                self.current_rot_y_speed -= self.decr_speed_rot_step_per_sec * dt
                self.current_rot_y_speed = max(0.0, self.current_rot_y_speed)
            elif self.current_rot_y_speed < 0.0:
                self.current_rot_y_speed += self.decr_speed_rot_step_per_sec * dt
                self.current_rot_y_speed = min(0.0, self.current_rot_y_speed)
            if rot_z > 0:
                self.current_rot_z_speed += self.incr_speed_rot_step_per_sec * dt
                self.current_rot_z_speed = min(self.current_rot_z_speed, self.rot_step_per_sec)
            elif rot_z < 0:
                self.current_rot_z_speed -= self.incr_speed_rot_step_per_sec * dt
                self.current_rot_z_speed = max(self.current_rot_z_speed, -self.rot_step_per_sec)
            elif self.current_rot_z_speed > 0.0:
                self.current_rot_z_speed -= self.decr_speed_rot_step_per_sec * dt
                self.current_rot_z_speed = max(0.0, self.current_rot_z_speed)
            elif self.current_rot_z_speed < 0.0:
                self.current_rot_z_speed += self.decr_speed_rot_step_per_sec * dt
                self.current_rot_z_speed = min(0.0, self.current_rot_z_speed)
        else:
            self.current_rot_x_speed = rot_x * self.rot_step_per_sec
            self.current_rot_y_speed = rot_y * self.rot_step_per_sec
            self.current_rot_z_speed = rot_z * self.rot_step_per_sec
        self.turn( LVector3d.right(), self.current_rot_x_speed * dt)
        self.turn( LVector3d.forward(), self.current_rot_y_speed * dt)
        self.turn( LVector3d.up(), self.current_rot_z_speed * dt)
        self.change_altitude(distance * self.distance_speed * dt)

    def turn(self, axis, angle):
        rot=LQuaterniond()
        rot.setFromAxisAngleRad(angle, axis)
        self.observer.step_turn_camera(rot, absolute=False)

    def stepRelative(self, x = 0, y = 0, z = 0):
        direction=LVector3d(x,y,z)
        delta = self.observer.get_frame_camera_rot().xform(direction)
        self.observer.step_camera(delta, absolute=False)

    def change_altitude(self, rate):
        if rate == 0.0: return
        target = self.select_target()
        if target is None: return
        direction=(target.get_rel_position_to(self.observer.camera_global_pos) - self.observer.get_camera_pos())
        height = target.get_height_under(self.observer.get_camera_pos())
        altitude = direction.length() - height
        #print(direction.length(), height, altitude)
        if altitude < settings.min_altitude:
            altitude = altitude - settings.min_altitude
            rate = 1.0
        direction.normalize()
        self.observer.step_camera(direction*altitude*rate, absolute=True)

class WalkNav(NavBase):
    rot_step_per_sec = pi/4
    speed = 10  * units.m
    distance_speed = 2.0

    def __init__(self, body):
        NavBase.__init__(self)
        self.body = body
        self.speed_factor = 1.0

    def register_events(self, event_ctrl):
        self.keyMap = {"left": 0, "right": 0,
                       "up": 0, "down": 0,
                       "home": 0, "end": 0,
                       "shift-left": 0, "shift-right": 0,
                       "shift-up": 0, "shift-down": 0,
                       "control-left": 0, "control-right": 0,
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

    def update(self, dt):
        if self.keyMap['up']:
            self.step(self.speed * self.speed_factor * dt)

        if self.keyMap['down']:
            self.step(-self.speed * self.speed_factor * dt)

        if self.keyMap['left']:
            self.turn( LVector3d.up(), self.rot_step_per_sec * dt)

        if self.keyMap['right']:
            self.turn( LVector3d.up(), -self.rot_step_per_sec * dt)

        if self.keyMap['shift-up']:
            self.turn( LVector3d.right(), self.rot_step_per_sec * dt)

        if self.keyMap['shift-down']:
            self.turn( LVector3d.right(), -self.rot_step_per_sec * dt)

        if self.keyMap['shift-left']:
            self.turn( LVector3d.up(), self.rot_step_per_sec * dt)

        if self.keyMap['shift-right']:
            self.turn( LVector3d.up(), -self.rot_step_per_sec * dt)

        if self.keyMap['control-left']:
            self.turn( LVector3d.forward(), self.rot_step_per_sec * dt)

        if self.keyMap['control-right']:
            self.turn( LVector3d.forward(), -self.rot_step_per_sec * dt)

        if self.keyMap['home']:
            self.change_altitude(self.distance_speed * dt)

        if self.keyMap['end']:
            self.change_altitude(-self.distance_speed * dt)

        if self.wheel_event_time + self.wheel_event_duration > globalClock.getRealTime():
            distance = self.wheel_direction
            self.change_altitude(distance * self.distance_speed * dt)

    def step(self, distance):
        arc_to_angle = 1.0 / (self.body.get_apparent_radius())
        camera_pos = self.observer.get_camera_pos()
        (normal, tangent, binormal) = self.body.get_normals_under(camera_pos)
        direction = self.observer.get_camera_rot().xform(LVector3d(0, distance, 0))
        projected = direction - normal * direction.dot(normal)
        position = self.body.cartesian_to_spherical(self.observer.get_camera_pos())
        delta_x = tangent.dot(projected) * arc_to_angle
        delta_y = binormal.dot(projected) * arc_to_angle
        new_position = [position[0] + delta_x, position[1] + delta_y, position[2]]
        altitude = position[2] - self.body.height_under
        (x, y, distance) = self.body.spherical_to_longlat(new_position)
        new_height = self.body.surface.get_height_at(x, y, strict = True)
        if new_height is not None:
            new_position[2] = new_height + altitude
        else:
            print("Patch not found for", x, y, '->', new_position[2])
        new_position = self.body.spherical_to_cartesian(new_position)
        self.observer.set_camera_pos(new_position)
        target_pos = new_position + direction * 10 * units.m
        target_pos = self.body.cartesian_to_spherical(target_pos)
        (x, y, distance) = self.body.spherical_to_longlat(target_pos)
        target_height = self.body.surface.get_height_at(x, y, strict = True)
        if target_height is not None:
            target_pos = (target_pos[0], target_pos[1], target_height + altitude)
        else:
            print("Patch not found for", x, y, '->', target_pos[2])
        target_pos = self.body.spherical_to_cartesian(target_pos)
        rot, angle = self.observer.calc_look_at(target_pos, rel=False)
        #self.observer.set_camera_rot(rot)
        #print(angle)

    def change_altitude(self, rate):
        if rate == 0.0: return
        direction=(self.body.get_rel_position_to(self.observer.camera_global_pos) - self.observer.get_camera_pos())
        height = self.body.get_height_under(self.observer.get_camera_pos())
        altitude = direction.length() - height
        #print(direction.length(), height, altitude)
        if altitude < settings.min_altitude:
            altitude = altitude - settings.min_altitude
            rate = 1.0
        direction.normalize()
        self.observer.step_camera(direction*altitude*rate, absolute=True)

    def turn(self, axis, angle):
        rot=LQuaterniond()
        rot.setFromAxisAngleRad(angle, axis)
        self.observer.step_turn_camera(rot, absolute=False)
