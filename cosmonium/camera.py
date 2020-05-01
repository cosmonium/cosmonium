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

from panda3d.core import LPoint4, LPoint3d, LVector3d, LQuaternion, LQuaterniond, look_at

from . import settings

from math import sin, cos, acos, tan, atan, sqrt, pi

class CameraBase(object):
    def __init__(self, cam, lens):
        #Camera node
        self.cam = cam
        self.camLens = lens
        #Field of view (vertical)
        self.default_fov = None
        self.fov = None
        #Camera film size
        self.width = 0
        self.height = 0
        #Default focal (Fullscreen with default fov), used for the zoom factor
        self.default_focal = None
        #Current zoom factor
        self.zoom_factor = 1.0
        self.linked_cams = []

    def add_linked_cam(self, cam):
        self.linked_cams.append(cam)

    def init(self):
        self.realCamLens = self.camLens.make_copy()
        self.update_near_plane(settings.near_plane)
        print("Planes: ", self.camLens.getNear(), self.camLens.getFar())
        self.init_fov()

    def update_near_plane(self, near_plane):
        if settings.infinite_far_plane:
            far_plane = float('inf')
        else:
            far_plane = settings.far_plane
        if settings.use_inverse_z:
            self.camLens.setNearFar(settings.far_plane, near_plane)
        else:
            self.camLens.setNearFar(near_plane, far_plane)
        self.realCamLens.setNearFar(near_plane, far_plane)
        if settings.auto_infinite_plane:
            self.infinity = near_plane / settings.lens_far_limit / 1000
        else:
            self.infinity = settings.infinite_plane
        self.midPlane = self.infinity / settings.mid_plane_ratio
        render.setShaderInput("midPlane", self.midPlane)

    def init_fov(self):
        if base.pipe is not None:
            screen_width = base.pipe.getDisplayWidth()
            screen_height = base.pipe.getDisplayHeight()
        else:
            screen_width = 1
            screen_height = 1
        self.width = screen_width
        self.height = screen_height
        self.fov = settings.default_fov
        self.do_set_fov(settings.default_fov)
        self.default_fov = settings.default_fov
        self.default_focal = self.realCamLens.get_focal_length()
        self.set_film_size(self.width, self.height)

    def do_set_fov_lens(self, lens, hfov, vfov):
        lens.set_film_size(self.width, self.height)
        lens.set_fov(hfov, vfov)

    def do_set_fov(self, fov):
        hfov = 2 * atan(tan(fov * pi / 180 / 2) * self.width / self.height) * 180 / pi
        self.do_set_fov_lens(self.camLens, hfov, fov)
        self.do_set_fov_lens(self.realCamLens, hfov, fov)
        for cam in self.linked_cams:
            self.do_set_fov_lens(cam.node().get_lens(), hfov, fov)
        self.fov = fov

    def set_focal(self, new_focal):
        new_fov = atan(self.height / 2 / new_focal) * 2 / pi * 180
        self.set_fov(new_fov)

    def do_set_film_size_lens(self, lens, width, height):
        focal = lens.get_focal_length()
        lens.set_film_size(width, height)
        lens.set_focal_length(focal)

    def set_film_size(self, width, height):
        self.do_set_film_size_lens(self.camLens, width, height)
        self.do_set_film_size_lens(self.realCamLens, width, height)
        for cam in self.linked_cams:
            self.do_set_film_size_lens(cam.node().get_lens(), width, height)
        self.height = height
        self.width = width
        self.fov = self.realCamLens.getVfov()
        self.update_zoom_factor()
        self.calc_pixel_size()

    def update_zoom_factor(self):
        self.zoom_factor = self.realCamLens.get_focal_length() / self.default_focal

    def zoom(self, factor):
        zoom_factor = self.zoom_factor * factor
        new_focal = self.default_focal * zoom_factor
        self.set_focal(new_focal)

    def reset_zoom(self):
        self.set_focal(self.default_focal)

    def set_fov(self, new_fov):
        if new_fov >= settings.min_fov and new_fov <= settings.max_fov:
            print("Setting FoV to", new_fov)
            self.do_set_fov(new_fov)
            self.update_zoom_factor()
            self.calc_pixel_size()

    def get_fov(self):
        return self.fov

    def calc_pixel_size(self):
        self.height = self.height
        self.ratio = float(self.width) / self.height
        fov2 =  self.fov / 180 * pi / 2.0
        self.tan_fov2 = tan(fov2)
        self.sqr_tan_fov2 = self.tan_fov2 * self.tan_fov2
        self.inv_tan_fov2 = 1.0 / self.tan_fov2
        self.cos_fov2 = cos(fov2)
        self.sqr_cos_fov2 = self.cos_fov2 * self.cos_fov2
        self.inv_cos_fov2 = 1.0 / self.cos_fov2
        self.sin_fov2 = sin(fov2)
        self.sqr_sin_fov2 = self.sin_fov2 * self.sin_fov2
        self.inv_sin_fov2 = 1.0 / self.sin_fov2
        self.inv_cos_dfov = sqrt(1.0 + self.sqr_tan_fov2 + self.sqr_tan_fov2 * self.ratio * self.ratio)
        self.dfov = acos(1.0 / self.inv_cos_dfov)
        self.cos_dfov = 1.0 / self.inv_cos_dfov
        self.sqr_cos_dfov = self.cos_dfov * self.cos_dfov
        self.sqr_sin_dfov = 1.0 - self.sqr_cos_dfov
        self.sin_dfov = sqrt(self.sqr_sin_dfov)
        self.inv_sin_dfov = 1.0 / self.sin_dfov
        self.pixel_size = 2 * self.tan_fov2 / self.height

    def calc_pixel_size_of(self, distance, radius):
        return radius * self.inv_tan_fov2 / (distance + self.inv_tan_fov2) * self.height / 2

    def calc_exact_pixel_size_of(self, distance, radius):
        v=LPoint4(0.0, distance, radius, 1.0)
        w = self.realCamLens.getProjectionMat().xform(v)
        if w[3] == 0.0:
            return 0
        return w[1] / w[3] * self.height

class CameraHolder(CameraBase):
    def __init__(self, cam, lens):
        CameraBase.__init__(self, cam, lens)
        self.camera_global_pos = LPoint3d()
        self._position = LPoint3d()
        self._local_position = LPoint3d()
        self._orientation = LQuaterniond()
        self.camera_vector = LVector3d()

        #These two variables should only be used by the camera controller
        self._frame_position = LPoint3d()
        self._frame_rotation = LQuaterniond()

    def get_position(self):
        return self.camera_global_pos + self._local_position

    def get_camera_pos(self):
        return self._local_position

    def get_camera_rot(self):
        return self._orientation

    def get_camera_vector(self):
        return self.camera_vector

    def update_camera(self, global_position, position, orientation):
        self.camera_global_pos = global_position
        self._position = position
        self._local_position = position
        self._orientation = orientation
        self.camera_vector = self._orientation.xform(LVector3d.forward())
        #Don't update camera position as everything is relative to camera
        self.cam.setQuat(LQuaternion(*self.get_camera_rot()))

class CameraController():
    camera_type = None
    FIXED = 'fixed'
    LOOK_AROUND = 'look-around'
    FOLLOW = 'follow'
    def __init__(self):
        self.camera = None
        self.reference_point = None
        self.event_ctrl = None

    def get_name(self):
        return ''

    def activate(self, camera, reference_point, event_ctrl):
        self.camera = camera
        self.reference_point = reference_point
        self.event_ctrl = event_ctrl
        self.register_events()

    def deactivate(self):
        self.remove_events()
        self.camera = None
        self.reference_point = None
        self.event_ctrl = None

    def set_reference_point(self, reference_point):
        self.reference_point = reference_point

    def register_events(self):
        pass

    def remove_events(self):
        pass

    def update_camera(self):
        pass

class FixedCameraController(CameraController):
    camera_mode = CameraController.FIXED
    def __init__(self):
        CameraController.__init__(self)
        self.rotation = LQuaterniond()
        self.is_looking_back = False

    def get_name(self):
        return 'Fixed camera'

    def register_events(self):
        self.event_ctrl.accept('*', self.look_back)

    def remove_events(self):
        self.event_ctrl.ignore('*')

    def look_back(self):
        self.rotation = LQuaterniond()
        if not self.is_looking_back:
            self.rotation.setFromAxisAngleRad(pi, LVector3d.up())
        self.is_looking_back = not self.is_looking_back

    def update_camera(self):
        (reference_distance, reference_pos, reference_rot) = self.reference_point.get_camera_hints()

        global_position = self.reference_point._global_position

        local_position = self.reference_point._local_position + self.reference_point._orientation.xform(reference_pos)
        orientation = reference_rot * self.rotation * self.reference_point._orientation
        self.camera.update_camera(global_position, local_position, orientation)

class LookAroundCameraController(CameraController):
    camera_mode = CameraController.LOOK_AROUND
    def __init__(self):
        CameraController.__init__(self)
        self.rotation = LQuaterniond()

    def get_name(self):
        return 'Look around camera'

    def update_camera(self):
        (reference_distance, reference_pos, reference_rot) = self.reference_point.get_camera_hints()

        if self.event_ctrl.mouseWatcherNode.hasMouse():
            mpos = self.event_ctrl.mouseWatcherNode.getMouse()
            x_angle = mpos.get_y() * pi / 2
            z_angle = mpos.get_x() * pi / 2
            x_rotation = LQuaterniond()
            x_rotation.setFromAxisAngleRad(x_angle, LVector3d.right())
            z_rotation = LQuaterniond()
            z_rotation.setFromAxisAngleRad(-z_angle, LVector3d.up())
            self.rotation = x_rotation * z_rotation

        global_position = self.reference_point._global_position

        local_position = self.reference_point._local_position + self.reference_point._orientation.xform(reference_pos)
        orientation = reference_rot * self.rotation * self.reference_point._orientation
        self.camera.update_camera(global_position, local_position, orientation)

class FollowCameraController(CameraController):
    camera_mode = CameraController.FOLLOW
    def get_name(self):
        return 'Follow camera'

    def update_camera(self):
        (reference_distance, reference_pos, reference_rot) = self.reference_point.get_camera_hints()
        min_distance = reference_distance / 2.0
        max_distance = reference_distance * 2.0

        camera_frame_position = self.camera._frame_position
        vector_to_reference = self.reference_point._frame_position - camera_frame_position
        distance = vector_to_reference.length()
        vector_to_reference.normalize()
        if min_distance > 0 and distance == 0:
            vector_to_reference = self.reference_point._frame_rotation.xform(-LVector3d.forward())
            distance = 1.0
        if distance > max_distance:
            camera_frame_position = camera_frame_position + vector_to_reference * (distance - max_distance)
        if distance < min_distance:
            camera_frame_position = camera_frame_position - vector_to_reference * (min_distance - distance)

        camera_frame_orientation = LQuaterniond()
        look_at(camera_frame_orientation, vector_to_reference, self.reference_point._frame_rotation.xform(LVector3d.up()))

        camera_global_position = self.reference_point._global_position
        camera_local_position = self.reference_point.frame.get_local_position(camera_frame_position)
        camera_local_orientation = self.reference_point.frame.get_abs_orientation(camera_frame_orientation)
        self.camera.update_camera(camera_global_position, camera_local_position, camera_local_orientation)
        self.camera._frame_position = camera_frame_position
        self.camera._frame_rotation = camera_frame_orientation
