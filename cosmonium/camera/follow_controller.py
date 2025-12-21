#
# This file is part of Cosmonium.
#
# Copyright (C) 2018-2025 Laurent Deru.
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


from math import pi
from panda3d.core import LVector3d, LQuaterniond, look_at

from .base import BaseCameraController, OrbitTargetHelper
from .. import settings


class FollowCameraController(BaseCameraController):
    camera_mode = BaseCameraController.FOLLOW

    def __init__(self):
        BaseCameraController.__init__(self)
        self.distance = 5.0
        self.max_distance = 2.0

    def get_name(self):
        return _('Follow camera')

    def get_id(self):
        return "follow"

    def set_camera_hints(self, **kwargs):
        self.distance = kwargs.get('distance', self.distance)
        self.max_distance = kwargs.get('max', self.max_distance)

    def update(self, time, dt):
        min_distance = self.reference_anchor.get_apparent_radius() * self.distance
        max_distance = self.reference_anchor.get_apparent_radius() * self.distance * self.max_distance

        self.camera.update()
        camera_position = self.camera.get_local_position()
        vector_to_reference = self.reference_anchor.get_local_position() - camera_position
        distance = vector_to_reference.length()
        vector_to_reference.normalize()
        if min_distance > 0 and distance == 0:
            vector_to_reference = self.reference_anchor.get_absolute_orientation().xform(-LVector3d.forward())
            distance = 1.0
        if distance > max_distance:
            camera_position = camera_position + vector_to_reference * (distance - max_distance)
        if distance < min_distance:
            camera_position = camera_position - vector_to_reference * (min_distance - distance)

        vector_to_reference = self.reference_anchor.get_local_position() - camera_position
        vector_to_reference.normalize()
        camera_orientation = LQuaterniond()
        look_at(
            camera_orientation,
            vector_to_reference,
            self.reference_anchor.get_absolute_orientation().xform(LVector3d.up()),
        )

        self.camera.change_global(self.reference_anchor.get_absolute_reference_point())
        self.camera.set_local_position(camera_position)
        self.camera.set_absolute_orientation(camera_orientation)
        self.camera.update()


class SurfaceFollowCameraController(BaseCameraController):
    camera_mode = BaseCameraController.FOLLOW
    STATE_DEFAULT = 'default'
    STATE_ORBIT_MOUSE = 'orbit-mouse'
    STATE_ORBIT_KEYBOARD = 'orbit-keyboard'

    def __init__(self, orbit_body=True, change_distance=True):
        BaseCameraController.__init__(self)
        self.orbit_body = orbit_body
        self.change_distance = change_distance
        self.terrain = None
        self.height = 2.0
        self.min_height = 1.0
        self.reference_min_distance = 1.0
        self.min_distance = 1.0
        self.max_distance = 1.0
        self.mouse_control = None
        self.state = self.STATE_DEFAULT
        self.distance = 5.0
        self.max_distance = 2.0
        self.reference_distance = self.min_distance

    def get_name(self):
        return _('Follow camera')

    def get_id(self):
        return "surface-follow"

    def set_camera_hints(self, **kwargs):
        self.distance = kwargs.get('distance', self.distance)
        self.max_distance = kwargs.get('max', self.max_distance)
        self.reference_distance = self.distance

    def register_events(self):
        if self.orbit_body:
            self.accept("mouse1", self.mouse_click_event)
            self.accept("mouse1-up", self.mouse_release_event)
            self.accept("shift-arrow_left", self.set_key, ['shift-left', 1])
            self.accept("shift-arrow_right", self.set_key, ['shift-right', 1])
            self.accept("arrow_left-up", self.set_key, ['shift-left', 0])
            self.accept("arrow_right-up", self.set_key, ['shift-right', 0])
            self.accept("shift-arrow_up", self.set_key, ['shift-up', 1])
            self.accept("shift-arrow_down", self.set_key, ['shift-down', 1])
            self.accept("arrow_up-up", self.set_key, ['shift-up', 0])
            self.accept("arrow_down-up", self.set_key, ['shift-down', 0])
        if self.change_distance:
            if settings.invert_wheel:
                self.accept("wheel_up", self.do_change_distance, [0.1])
                self.accept("wheel_down", self.do_change_distance, [-0.1])
            else:
                self.accept("wheel_up", self.do_change_distance, [-0.1])
                self.accept("wheel_down", self.do_change_distance, [0.1])

    def set_terrain(self, terrain):
        self.terrain = terrain

    def calc_projected_orientation(self):
        projected_vector_to_reference = self.reference_anchor.get_local_position() - self.camera.get_local_position()
        projected_vector_to_reference[2] = 0.0
        projected_vector_to_reference.normalize()
        orientation = LQuaterniond()
        look_at(
            orientation,
            projected_vector_to_reference,
            self.reference_anchor.get_absolute_orientation().xform(LVector3d.up()),
        )
        return orientation

    def mouse_click_event(self):
        if not self.state == self.STATE_DEFAULT:
            return
        orientation = self.calc_projected_orientation()
        self.mouse_control = OrbitTargetHelper(self.base, self.camera.anchor)
        self.mouse_control.start_mouse(self.reference_anchor, pi, pi, orientation)
        self.state = self.STATE_ORBIT_MOUSE

    def mouse_release_event(self):
        if self.state == self.STATE_ORBIT_MOUSE:
            self.mouse_control = None
            self.state = self.STATE_DEFAULT

    def do_change_distance(self, step):
        vector_to_reference = self.reference_anchor.get_local_position() - self.camera.get_local_position()
        distance = vector_to_reference.length()
        vector_to_reference.normalize()
        new_distance = max(self.reference_min_distance, distance * (1.0 + step))
        new_position = self.reference_anchor.get_local_position() - vector_to_reference * new_distance
        self.camera.set_local_position(new_position)
        self.camera.update()
        self.update_limits()

    def update_limits(self):
        camera_position = self.camera.get_local_position()
        vector_to_reference = self.reference_anchor.get_local_position() - camera_position
        self.height = max(self.min_height, camera_position[2] - self.reference_anchor.get_local_position()[2])
        vector_to_reference[2] = 0.0
        distance = vector_to_reference.length()
        self.distance = max(self.reference_min_distance, distance / self.reference_anchor.get_apparent_radius())

    def update_lookat(self):
        camera_position = self.camera.get_local_position()
        vector_to_reference = self.reference_anchor.get_local_position() - camera_position
        vector_to_reference.normalize()
        camera_orientation = LQuaterniond()
        look_at(
            camera_orientation,
            vector_to_reference,
            self.reference_anchor.get_absolute_orientation().xform(LVector3d.up()),
        )
        self.camera.set_absolute_orientation(camera_orientation)

    def update(self, time, dt):
        if self.state == self.STATE_DEFAULT:
            if (
                self.keymap.get('shift-left')
                or self.keymap.get('shift-right')
                or self.keymap.get('shift-up')
                or self.keymap.get('shift-down')
            ):
                orientation = self.calc_projected_orientation()
                self.mouse_control = OrbitTargetHelper(self.base, self.camera.anchor)
                self.mouse_control.start(self.reference_anchor, pi, pi, orientation)
                self.state = self.STATE_ORBIT_KEYBOARD
        if self.state == self.STATE_ORBIT_MOUSE:
            self.mouse_control.update_mouse()
            self.camera.update()
            self.update_lookat()
            self.camera.update()
            self.update_limits()
        elif self.state == self.STATE_ORBIT_KEYBOARD:
            key_pressed = False
            if self.keymap.get('shift-left'):
                key_pressed = True
                self.mouse_control.delta_x += dt
            if self.keymap.get('shift-right'):
                key_pressed = True
                self.mouse_control.delta_x -= dt
            if self.keymap.get('shift-up'):
                key_pressed = True
                self.mouse_control.delta_y += dt
            if self.keymap.get('shift-down'):
                key_pressed = True
                self.mouse_control.delta_y -= dt
            self.mouse_control.update()
            self.camera.update()
            self.update_lookat()
            self.camera.update()
            self.update_limits()
            if not key_pressed:
                self.state = self.STATE_DEFAULT
        elif self.state == self.STATE_DEFAULT:
            min_distance = self.reference_anchor.get_apparent_radius() * self.distance
            max_distance = self.reference_anchor.get_apparent_radius() * self.distance * self.max_distance
            camera_position = self.camera.get_local_position()
            projected_vector_to_reference = self.reference_anchor.get_local_position() - camera_position
            projected_vector_to_reference[2] = 0.0
            distance = projected_vector_to_reference.length()
            projected_vector_to_reference.normalize()
            if min_distance > 0 and distance == 0:
                projected_vector_to_reference = self.reference_anchor.get_absolute_orientation().xform(
                    LVector3d.forward()
                )
                distance = 1.0
            if distance > max_distance:
                camera_position = camera_position + projected_vector_to_reference * (distance - max_distance)
            if distance < min_distance:
                camera_position = camera_position - projected_vector_to_reference * (min_distance - distance)

            surface_height = self.terrain.anchor._height_under
            target_height = self.reference_anchor.get_local_position()[2]
            # print(self.height, self.min_height, surface_height, target_height)
            if surface_height + self.min_height < target_height + self.height:
                new_camera_height = target_height + self.height
            else:
                new_camera_height = surface_height + self.min_height
            camera_position[2] = new_camera_height
            vector_to_reference = self.reference_anchor.get_local_position() - camera_position
            vector_to_reference.normalize()
            camera_orientation = LQuaterniond()
            look_at(
                camera_orientation,
                vector_to_reference,
                self.reference_anchor.get_absolute_orientation().xform(LVector3d.up()),
            )

            self.camera.change_global(self.reference_anchor.get_absolute_reference_point())
            self.camera.set_local_position(camera_position)
            self.camera.set_absolute_orientation(camera_orientation)
            self.camera.update()
        else:
            print("Unknown state", self.state)
