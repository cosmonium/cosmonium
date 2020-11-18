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

from panda3d.core import LQuaterniond, LQuaternion, LVector3d, LPoint3d, NodePath
from panda3d.core import lookAt

from direct.interval.LerpInterval import LerpFunc, LerpQuatInterval
from direct.interval.MetaInterval import Parallel, Sequence
from direct.interval.FunctionInterval import Wait

from .astro.frame import J2000EclipticReferenceFrame, J2000EquatorialReferenceFrame
from .astro.frame import SynchroneReferenceFrame
from .astro import units
from .utils import isclose
from .systems import SimpleSystem
from . import settings

from math import acos, pi, exp, log

class AutoPilot(object):
    def __init__(self, ui):
        self.ui = ui
        self.ship = None
        self.camera_controller =None
        self.current_interval = None
        self.timed_interval = None
        self.last_interval_time = None
        self.fake = None
        self.start_pos = LPoint3d()
        self.end_pos = LPoint3d()

    def set_ship(self, ship):
        self.ship = ship

    def set_camera_controller(self, camera_controller):
        self.camera_controller = camera_controller

    def reset(self):
        if self.current_interval != None:
            self.current_interval.pause()
            self.current_interval = None
        if self.timed_interval != None:
            self.timed_interval.pause()
            self.timed_interval = None

    def stash_position(self):
        self.start_pos = self.ship.get_position_of(self.start_pos)
        self.end_pos = self.ship.get_position_of(self.end_pos)

    def pop_position(self):
        self.start_pos = self.ship.get_rel_position_of(self.start_pos, local=False)
        self.end_pos = self.ship.get_rel_position_of(self.end_pos, local=False)

    def do_move(self, step):
        position = self.end_pos * step + self.start_pos * (1.0 - step)
        self.ship.set_frame_pos(position)
        if step == 1.0:
            self.current_interval = None

    def move_to(self, new_pos, absolute=True, duration=0, ease=True):
        if settings.debug_jump: duration = 0
        if duration == 0:
            if absolute:
                self.ship.set_pos(new_pos)
            else:
                self.ship.set_frame_pos(new_pos)
        else:
            if self.current_interval != None:
                self.current_interval.pause()
            if absolute:
                self.start_pos = self.ship.get_frame_pos()
                self.end_pos = self.ship.get_rel_position_of(new_pos)
            if ease:
                blend_type = 'easeInOut'
            else:
                blend_type = 'noBlend'
            self.current_interval = LerpFunc(self.do_move,
                fromData=0,
                toData=1,
                duration=duration,
                blendType=blend_type,
                name=None)
            self.current_interval.start()

    def do_update_func(self, step, func, extra):
        delta = globalClock.getRealTime() - self.last_interval_time
        self.last_interval_time = globalClock.getRealTime()
        if self.current_interval is None:
            func(delta, *extra)
        if step == 1.0:
            self.timed_interval = None

    def update_func(self, func, duration=0, extra=()):
        if settings.debug_jump: duration = 0
        if duration == 0:
            func(duration, *extra)
        else:
            if self.timed_interval != None:
                self.timed_interval.pause()
            self.last_interval_time = globalClock.getRealTime()
            self.timed_interval = LerpFunc(self.do_update_func,
                fromData=0,
                toData=1,
                duration=duration,
                extraArgs=[func, extra],
                name=None)
            self.timed_interval.start()

    def do_move_and_rot(self, step):
        rot = LQuaterniond(*self.fake.getQuat())
        rot.normalize()
        self.ship.set_frame_rot(rot)
        position = self.end_pos * step + self.start_pos * (1.0 - step)
        self.ship.set_frame_pos(position)
        if step == 1.0:
            self.current_interval = None

    def move_and_rotate_to(self, new_pos, new_rot, absolute=True, duration=0, start_rotation=0.0, end_rotation=0.5):
        if settings.debug_jump: duration = 0
        self.camera_controller.prepare_movement()
        if duration == 0:
            if absolute:
                self.ship.set_pos(new_pos)
                self.ship.set_rot(new_rot)
            else:
                self.ship.set_frame_pos(new_pos)
                self.ship.set_frame_rot(new_rot)
        else:
            if self.current_interval != None:
                self.current_interval.pause()
            self.fake = NodePath('fake')
            if absolute:
                self.start_pos = self.ship.get_frame_pos()
                self.end_pos = self.ship.get_rel_position_of(new_pos)
                start_rot = self.ship.get_frame_rot()
                end_rot = self.ship.get_rel_rotation_of(new_rot)
            else:
                self.start_pos = self.ship.get_frame_pos()
                self.end_pos = new_pos
                start_rot = self.ship.get_frame_rot()
                end_rot = new_rot
            self.fake.set_quat(LQuaternion(*start_rot))
            nodepath_lerp = Sequence()
            rotation_duration = duration * (end_rotation - start_rotation)
            nodepath_lerp.append(Wait(duration * start_rotation))
            nodepath_lerp.append(LerpQuatInterval(self.fake,
                                             duration=rotation_duration,
                                             blendType='easeInOut',
                                             quat = LQuaternion(*end_rot),
                                             ))
            func_lerp = LerpFunc(self.do_move_and_rot,
                                 fromData=0,
                                 toData=1,
                                 duration=duration,
                                 blendType='easeInOut',
                                 name=None)
            parallel = Parallel(nodepath_lerp, func_lerp)
            self.current_interval = parallel
            self.current_interval.start()

    def go_to(self, target, duration, position, direction, up, start_rotation, end_rotation):
        if up is None:
            up = LVector3d.up()
        frame = SynchroneReferenceFrame(target)
        up = frame.get_orientation().xform(up)
        if isclose(abs(up.dot(direction)), 1.0):
            print("Warning: lookat vector identical to up vector")
        else:
            # Make the up vector orthogonal to the direction using Gram-Schmidt
            up = up - direction * up.dot(direction)
        orientation = LQuaterniond()
        lookAt(orientation, direction, up)
        self.move_and_rotate_to(position, orientation, duration=duration)

    def go_to_front(self, duration = None, distance=None, up=None, star=False, start_rotation=0.0, end_rotation=0.5):
        if not self.ui.selected: return
        target = self.ui.selected
        if duration is None:
            duration = settings.slow_move
        if distance is None:
            distance = settings.default_distance
        distance_unit = target.get_apparent_radius()
        if distance_unit == 0.0:
            distance_unit = target.get_extend()
        print("Go to front", target.get_name())
        self.ui.follow_selected()
        center = target.get_rel_position_to(self.ship._global_position)
        position = None
        if star:
            position = target.star
        else:
            if target.parent is not None and isinstance(target.parent, SimpleSystem):
                if target.parent.primary == target:
                    if target.star is not target:
                        position = target.star
                else:
                    position = target.parent.primary
        if position is not None:
            print("Looking from", position.get_name())
            position = position.get_rel_position_to(self.ship._global_position)
        else:
            position = self.ship.get_pos()
        direction = center - position
        direction.normalize()
        new_position = center - direction * distance * distance_unit
        self.go_to(target, duration, new_position, direction, up, start_rotation, end_rotation)

    def go_to_object(self, duration = None, distance=None, up=None, start_rotation=0.0, end_rotation=0.5):
        if not self.ui.selected: return
        target = self.ui.selected
        if duration is None:
            duration = settings.slow_move
        if distance is None:
            distance = settings.default_distance
        distance_unit = target.get_apparent_radius()
        if distance_unit == 0.0:
            distance_unit = target.get_extend()
        print("Go to", target.get_name())
        self.ui.follow_selected()
        center = target.get_rel_position_to(self.ship._global_position)
        direction = center - self.ship.get_pos()
        direction.normalize()
        new_position = center - direction * distance * distance_unit
        self.go_to(target, duration, new_position, direction, up, start_rotation, end_rotation)

    def go_to_object_long_lat(self, longitude, latitude, duration = None, distance=None, up=None, start_rotation=0.0, end_rotation=0.5):
        if not self.ui.selected: return
        target = self.ui.selected
        if duration is None:
            duration = settings.slow_move
        if distance is None:
            distance = settings.default_distance
        distance_unit = target.get_apparent_radius()
        if distance_unit == 0.0:
            distance_unit = target.get_extend()
        print("Go to long-lat", target.get_name())
        self.ui.follow_selected()
        center = target.get_rel_position_to(self.ship._global_position)
        new_position = (longitude, latitude, distance * distance_unit)
        new_position = target.spherical_to_cartesian(new_position)
        direction = center - new_position
        direction.normalize()
        self.go_to(target, duration, new_position, direction, up, start_rotation, end_rotation)

    def go_to_surface(self, duration = None, height=1.001):
        if not self.ui.selected: return
        target = self.ui.selected
        if duration is None:
            duration = settings.slow_move
        print("Go to surface", target.get_name())
        self.ui.sync_selected()
        center = target.get_rel_position_to(self.ship._global_position)
        direction = self.ship.get_pos() - center
        new_orientation = LQuaterniond()
        lookAt(new_orientation, direction)
        height = target.get_height_under(self.ship.get_pos()) + 10 * units.m
        new_position = center + new_orientation.xform(LVector3d(0, height, 0))
        self.move_and_rotate_to(new_position, new_orientation, duration=duration)

    def go_pole(self, target, lat, duration, zoom):
        if not self.ui.selected: return
        target = self.ui.selected
        if zoom:
            distance = settings.default_distance
        else:
            distance_unit = target.get_apparent_radius()
            if distance_unit == 0.0:
                distance_unit = target.get_extend()
            distance = target.distance_to_obs / distance_unit
        self.go_to_object_long_lat(0, lat, duration, distance)

    def go_north(self, duration=None, zoom=False):
        if not self.ui.selected: return
        target = self.ui.selected
        lat = pi / 2
        if target.rotation.is_flipped():
            lat = -lat
        self.go_pole(target, lat, duration, zoom)

    def go_south(self, duration=None, zoom=False):
        if not self.ui.selected: return
        target = self.ui.selected
        lat = -pi / 2
        if target.rotation.is_flipped():
            lat = -lat
        self.go_pole(target, lat, duration, zoom)

    def go_meridian(self, duration=None, zoom=False):
        if not self.ui.selected: return
        target = self.ui.selected
        if zoom:
            distance = settings.default_distance
        else:
            distance_unit = target.get_apparent_radius()
            if distance_unit == 0.0:
                distance_unit = target.get_extend()
            distance = target.distance_to_obs / distance_unit
        self.go_to_object_long_lat(0, 0, duration, distance)

    def align_on_ecliptic(self, duration=None):
        if duration is None:
            duration = settings.fast_move
        ecliptic_normal = self.ship._frame_rotation.conjugate().xform(J2000EclipticReferenceFrame.orientation.xform(LVector3d.up()))
        angle = acos(ecliptic_normal.dot(LVector3d.right()))
        direction = ecliptic_normal.cross(LVector3d.right()).dot(LVector3d.forward())
        if direction < 0:
            angle = 2 * pi - angle
        rot=LQuaterniond()
        rot.setFromAxisAngleRad(pi / 2 - angle, LVector3d.forward())
        self.ship.step_turn(rot, absolute=False)
        #self.move_and_rotate_to(position, orientation, duration=duration)

    def align_on_equatorial(self, duration=None):
        if duration is None:
            duration = settings.fast_move
        ecliptic_normal = self.ship._frame_rotation.conjugate().xform(J2000EquatorialReferenceFrame.orientation.xform(LVector3d.up()))
        angle = acos(ecliptic_normal.dot(LVector3d.right()))
        direction = ecliptic_normal.cross(LVector3d.right()).dot(LVector3d.forward())
        if direction < 0:
            angle = 2 * pi - angle
        rot=LQuaterniond()
        rot.setFromAxisAngleRad(pi / 2 - angle, LVector3d.forward())
        self.ship.step_turn(rot, absolute=False)

    def do_change_distance(self, delta, rate):
        target = self.ui.selected
        center = target.get_rel_position_to(self.ship._global_position)
        min_distance = target.get_apparent_radius()
        natural_distance = 4.0 * min_distance
        relative_pos = self.ship.get_pos() - center

        if target.distance_to_obs < min_distance:
            min_distance = target.distance_to_obs * 0.5

        if target.distance_to_obs >= min_distance and natural_distance != 0:
            r = (target.distance_to_obs - min_distance) / natural_distance
            new_distance = min_distance + natural_distance * exp(log(r) + rate * delta)
            new_pos = relative_pos * (new_distance / target.distance_to_obs)
            self.ship.set_pos(center + new_pos)

    def change_distance(self, rate, duration=None):
        print("Change distance")
        if duration is None:
            duration = settings.fast_move
        self.update_func(self.do_change_distance, duration, [rate])

    def do_orbit(self, delta, axis, rate):
        target = self.ui.selected
        center = target.get_rel_position_to(self.ship._global_position)
        center = self.ship.get_rel_position_of(center)
        relative_pos = self.ship.get_frame_pos() - center
        rot=LQuaterniond()
        rot.setFromAxisAngleRad(rate * delta, axis)
        rot2 = self.ship._frame_rotation.conjugate() * rot * self.ship._frame_rotation
        rot2.normalize()
        distance = relative_pos.length()
        relative_pos.normalize()
        new_pos = rot2.xform(relative_pos) * distance
        self.ship.set_frame_pos(new_pos + center)
        self.ship.turn(self.ship._frame_rotation * rot2, absolute=False)

    def orbit(self, axis, rate, duration=None):
        print("Orbit")
        if duration is None:
            duration = settings.slow_move
        self.update_func(self.do_orbit, duration, [axis, rate])

    def do_rotate(self, delta, axis, rate):
        rot=LQuaterniond()
        rot.setFromAxisAngleRad(rate * delta, axis)
        self.ship.step_turn(rot, absolute=False)

    def rotate(self, axis, rate, duration=None):
        print("Rotate")
        if duration is None:
            duration = settings.slow_move
        self.update_func(self.do_rotate, duration, [axis, rate])
