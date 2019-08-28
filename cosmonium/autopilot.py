from __future__ import print_function
from __future__ import absolute_import

from panda3d.core import LQuaterniond, LQuaternion, LVector3d, LPoint3d, NodePath
from panda3d.core import lookAt

from direct.interval.LerpInterval import LerpFunc, LerpQuatInterval
from direct.interval.MetaInterval import Parallel

from .astro.frame import J2000EclipticReferenceFrame, J2000EquatorialReferenceFrame
from .astro.frame import CelestiaBodyFixedReferenceFrame
from .astro import units
from .utils import isclose
from .systems import SimpleSystem
from . import settings

from math import acos, pi, exp, log

class AutoPilot(object):
    def __init__(self, camera, ui):
        self.camera = camera
        self.ui = ui
        self.current_interval = None
        self.fake = None
        self.start_pos = LPoint3d()
        self.end_pos = LPoint3d()

    def reset(self):
        if self.current_interval != None:
            self.current_interval.pause()
            self.current_interval = None

    def stash_position(self):
        self.start_pos = self.camera.get_position_of(self.start_pos)
        self.end_pos = self.camera.get_position_of(self.end_pos)

    def pop_position(self):
        self.start_pos = self.camera.get_rel_position_of(self.start_pos, local=False)
        self.end_pos = self.camera.get_rel_position_of(self.end_pos, local=False)

    def do_camera_rot(self, step, origin, delta):
        #TODO: this is wrong, it should be replaced by do_camera_move_and_rot()
        rot = origin + delta * step
        rot.normalize()
        self.camera.set_camera_rot(rot)
        if step == 1.0:
            self.current_interval = None

    def camera_lookat(self, position, rel=False, duration = 2.0, proportional=True):
        new_rot, angle=self.camera.calc_look_at(position, rel)
        if settings.debug_jump: duration = 0
        if duration == 0:
            self.camera.set_camera_rot(new_rot)
        else:
            if proportional:
                duration=duration*angle/pi
            if self.current_interval != None:
                self.current_interval.pause()
            self.current_interval = LerpFunc(self.do_camera_rot,
                fromData=0,
                toData=1,
                duration=duration,
                blendType='easeInOut',
                extraArgs=[self.camera.get_camera_rot(), new_rot - self.camera.get_camera_rot()],
                name=None)
            self.current_interval.start()

    def do_camera_move(self, step):
        position = self.end_pos * step + self.start_pos * (1.0 - step)
        self.camera.set_frame_camera_pos(position)
        if step == 1.0:
            self.current_interval = None

    def move_camera_to(self, new_pos, absolute=True, duration=0, ease=True):
        if settings.debug_jump: duration = 0
        if duration == 0:
            if absolute:
                self.camera.set_camera_pos(new_pos)
            else:
                self.camera.set_frame_camera_pos(new_pos)
        else:
            if self.current_interval != None:
                self.current_interval.pause()
            if absolute:
                self.start_pos = self.camera.get_frame_camera_pos()
                self.end_pos = self.camera.get_rel_position_of(new_pos)
            if ease:
                blend_type = 'easeInOut'
            else:
                blend_type = 'noBlend'
            self.current_interval = LerpFunc(self.do_camera_move,
                fromData=0,
                toData=1,
                duration=duration,
                blendType=blend_type,
                name=None)
            self.current_interval.start()

    def do_update_camera_func(self, step, func, extra):
        delta = globalClock.getRealTime() - self.last_interval_time
        self.last_interval_time = globalClock.getRealTime()
        func(delta, *extra)
        if step == 1.0:
            self.current_interval = None

    def update_camera_func(self, func, duration=0, extra=()):
        if settings.debug_jump: duration = 0
        if duration == 0:
            func(duration, *extra)
        else:
            if self.current_interval != None:
                self.current_interval.pause()
            self.last_interval_time = globalClock.getRealTime()
            self.current_interval = LerpFunc(self.do_update_camera_func,
                fromData=0,
                toData=1,
                duration=duration,
                extraArgs=[func, extra],
                name=None)
            self.current_interval.start()

    def do_camera_move_and_rot(self, step):
        rot = LQuaterniond(*self.fake.getQuat())
        rot.normalize()
        self.camera.set_camera_rot(rot)
        position = self.end_pos * step + self.start_pos * (1.0 - step)
        self.camera.set_frame_camera_pos(position)
        if step == 1.0:
            self.current_interval = None

    def move_and_rotate_camera_to(self, new_pos, new_rot, absolute=True, duration=0):
        if settings.debug_jump: duration = 0
        if duration == 0:
            if absolute:
                self.camera.set_camera_pos(new_pos)
                self.camera.set_camera_rot(new_rot)
            else:
                self.camera.set_frame_camera_pos(new_pos)
                self.camera.set_frame_camera_rot(new_rot)
        else:
            if self.current_interval != None:
                self.current_interval.pause()
            self.fake = NodePath('fake')
            if absolute:
                self.start_pos = self.camera.get_frame_camera_pos()
                self.end_pos = self.camera.get_rel_position_of(new_pos)
                #TODO
                #new_rot = self.camera.get_rel_rotation_of(new_pos)
            nodepath_lerp = LerpQuatInterval(self.fake,
                                             duration=duration,
                                             blendType='easeInOut',
                                             quat = LQuaternion(*new_rot),
                                             startQuat = LQuaternion(*self.camera.get_camera_rot())
                                             )
            func_lerp = LerpFunc(self.do_camera_move_and_rot,
                                 fromData=0,
                                 toData=1,
                                 duration=duration,
                                 blendType='easeInOut',
                                 name=None)
            parallel = Parallel(nodepath_lerp, func_lerp)
            self.current_interval = parallel
            self.current_interval.start()

    def center_on_object(self, target=None, duration=None, cmd=True, proportional=True):
        if duration is None:
            duration = settings.fast_move
        if target is None and self.ui.selected:
            target=self.ui.selected
        if target is None: return
        if cmd: print("Center on", target.get_name())
        center = target.get_rel_position_to(self.camera.camera_global_pos)
        self.camera_lookat(center, rel=False, duration=duration, proportional=proportional)

    def go_system_top(self):
        if self.ui.nearest_system is not None:
            distance = self.ui.nearest_system.get_extend()
        else:
            distance = units.AU * 4
        self.camera.set_camera_pos(LPoint3d(0, 0, distance))
        self.camera_lookat(LPoint3d(0, 0, 0))

    def go_system_front(self):
        if self.ui.nearest_system is not None:
            distance = self.ui.nearest_system.get_extend()
        else:
            distance = units.AU * 4
        self.camera.set_camera_pos(LPoint3d(0, distance, 0))
        self.camera_lookat(LPoint3d(0, 0, 0))

    def go_system_side(self):
        if self.ui.nearest_system is not None:
            distance = self.ui.nearest_system.get_extend()
        else:
            distance = units.AU * 4
        self.camera.set_camera_pos(LPoint3d(distance, 0, 0))
        self.camera_lookat(LPoint3d(0, 0, 0))

    def go_to(self, target, duration, position, direction, up):
        if up is None:
            up = LVector3d.up()
        frame = CelestiaBodyFixedReferenceFrame(target)
        up = frame.get_orientation().xform(up)
        if isclose(abs(up.dot(direction)), 1.0):
            print("Warning: lookat vector identical to up vector")
        orientation = LQuaterniond()
        lookAt(orientation, direction, up)
        self.move_and_rotate_camera_to(position, orientation, duration=duration)

    def go_to_front(self, duration = None, distance=None, up=None, star=False):
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
        center = target.get_rel_position_to(self.camera.camera_global_pos)
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
            position = position.get_rel_position_to(self.camera.camera_global_pos)
        else:
            position = self.camera.get_camera_pos()
        direction = center - position
        direction.normalize()
        new_position = center - direction * distance * distance_unit
        self.go_to(target, duration, new_position, direction, up)

    def go_to_object(self, duration = None, distance=None, up=None):
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
        center = target.get_rel_position_to(self.camera.camera_global_pos)
        direction = center - self.camera.get_camera_pos()
        direction.normalize()
        new_position = center - direction * distance * distance_unit
        self.go_to(target, duration, new_position, direction, up)

    def go_to_object_long_lat(self, longitude, latitude, duration = None, distance=None, up=None):
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
        center = target.get_rel_position_to(self.camera.camera_global_pos)
        new_position = (longitude, latitude, distance * distance_unit)
        new_position = target.spherical_to_cartesian(new_position)
        direction = center - new_position
        direction.normalize()
        self.go_to(target, duration, new_position, direction, up)

    def go_to_surface(self, duration = None, height=1.001):
        if not self.ui.selected: return
        target = self.ui.selected
        if duration is None:
            duration = settings.slow_move
        print("Go to surface", target.get_name())
        self.ui.sync_selected()
        center = target.get_rel_position_to(self.camera.camera_global_pos)
        direction = self.camera.get_camera_pos() - center
        new_orientation = LQuaterniond()
        lookAt(new_orientation, direction)
        height = target.get_height_under(self.camera.get_camera_pos()) + 10 * units.m
        new_position = center + new_orientation.xform(LVector3d(0, height, 0))
        self.move_and_rotate_camera_to(new_position, new_orientation, duration=duration)

    def go_north(self, duration=None, zoom=False):
        if not self.ui.selected: return
        target = self.ui.selected
        if zoom:
            distance = settings.default_distance
        else:
            distance_unit = target.get_apparent_radius()
            if distance_unit == 0.0:
                distance_unit = target.get_extend()
            distance = target.distance_to_obs / distance_unit
        self.go_to_object_long_lat(0, pi / 2, duration, distance)

    def go_south(self, duration=None, zoom=False):
        if not self.ui.selected: return
        target = self.ui.selected
        if zoom:
            distance = settings.default_distance
        else:
            distance_unit = target.get_apparent_radius()
            if distance_unit == 0.0:
                distance_unit = target.get_extend()
            distance = target.distance_to_obs / distance_unit
        self.go_to_object_long_lat(0, -pi / 2, duration, distance)

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

    #TODO: Move to future camera class
    def align_on_ecliptic(self, duration=None):
        if duration is None:
            duration = settings.fast_move
        ecliptic_normal = self.camera.camera_rot.conjugate().xform(J2000EclipticReferenceFrame.orientation.xform(LVector3d.up()))
        angle = acos(ecliptic_normal.dot(LVector3d.right()))
        direction = ecliptic_normal.cross(LVector3d.right()).dot(LVector3d.forward())
        if direction < 0:
            angle = 2 * pi - angle
        rot=LQuaterniond()
        rot.setFromAxisAngleRad(pi / 2 - angle, LVector3d.forward())
        self.camera.step_turn_camera(rot, absolute=False)
        #self.move_and_rotate_camera_to(position, orientation, duration=duration)

    #TODO: Move to future camera class
    def align_on_equatorial(self, duration=None):
        if duration is None:
            duration = settings.fast_move
        ecliptic_normal = self.camera.camera_rot.conjugate().xform(J2000EquatorialReferenceFrame.orientation.xform(LVector3d.up()))
        angle = acos(ecliptic_normal.dot(LVector3d.right()))
        direction = ecliptic_normal.cross(LVector3d.right()).dot(LVector3d.forward())
        if direction < 0:
            angle = 2 * pi - angle
        rot=LQuaterniond()
        rot.setFromAxisAngleRad(pi / 2 - angle, LVector3d.forward())
        self.camera.step_turn_camera(rot, absolute=False)
        #self.move_and_rotate_camera_to(position, orientation, duration=duration)

    def do_change_distance(self, delta, rate):
        target = self.ui.selected
        center = target.get_rel_position_to(self.camera.camera_global_pos)
        min_distance = target.get_apparent_radius()
        natural_distance = 4.0 * min_distance
        relative_pos = self.camera.get_camera_pos() - center

        if target.distance_to_obs < min_distance:
            min_distance = target.distance_to_obs * 0.5

        if target.distance_to_obs >= min_distance and natural_distance != 0:
            r = (target.distance_to_obs - min_distance) / natural_distance
            new_distance = min_distance + natural_distance * exp(log(r) + rate * delta)
            new_pos = relative_pos * (new_distance / target.distance_to_obs)
            self.camera.set_camera_pos(center + new_pos)

    def change_distance(self, rate, duration=None):
        print("Change distance")
        if duration is None:
            duration = settings.fast_move
        self.update_camera_func(self.do_change_distance, duration, [rate])

    def do_orbit(self, delta, axis, rate):
        target = self.ui.selected
        center = target.get_rel_position_to(self.camera.camera_global_pos)
        center = self.camera.get_rel_position_of(center)
        relative_pos = self.camera.get_frame_camera_pos() - center
        rot=LQuaterniond()
        rot.setFromAxisAngleRad(rate * delta, axis)
        rot2 = self.camera.camera_rot.conjugate() * rot * self.camera.camera_rot
        rot2.normalize()
        new_pos = rot2.conjugate().xform(relative_pos)
        self.camera.set_frame_camera_pos(new_pos + center)
        self.camera.turn_camera(self.camera.camera_rot * rot2, absolute=False)

    def orbit(self, axis, rate, duration=None):
        print("Orbit")
        if duration is None:
            duration = settings.slow_move
        self.update_camera_func(self.do_orbit, duration, [axis, rate])

    def do_rotate(self, delta, axis, rate):
        rot=LQuaterniond()
        rot.setFromAxisAngleRad(rate * delta, axis)
        self.camera.step_turn_camera(rot, absolute=False)

    def rotate(self, axis, rate, duration=None):
        print("Rotate")
        if duration is None:
            duration = settings.slow_move
        self.update_camera_func(self.do_rotate, duration, [axis, rate])
