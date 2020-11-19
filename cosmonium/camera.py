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
from direct.showbase.DirectObject import DirectObject
from direct.interval.LerpInterval import LerpFunc

from .astro.frame import AbsoluteReferenceFrame
from . import settings
from . import utils

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

class OrbitTargetHelper():
    def __init__(self, anchor):
        self.anchor = anchor
        self.orbit_center = None
        self.orbit_dir = None
        self.orbit_orientation = None
        self.orbit_zaxis = None
        self.orbit_xaxis = None
        self.start_x = None
        self.start_y = None
        self.orbit_speed_x = None
        self.orbit_speed_z = None

    def update(self):
        z_angle = -self.delta_x * self.orbit_speed_x
        x_angle = self.delta_y * self.orbit_speed_z
        z_rotation = LQuaterniond()
        z_rotation.set_from_axis_angle_rad(z_angle, self.orbit_zaxis)
        x_rotation = LQuaterniond()
        x_rotation.set_from_axis_angle_rad(x_angle, self.orbit_xaxis)
        combined = x_rotation * z_rotation
        delta = combined.xform(-self.orbit_dir)
        self.anchor.set_frame_pos(delta + self.orbit_center)
        self.anchor.set_frame_rot(self.orbit_orientation * combined)

    def update_mouse(self):
        if not base.mouseWatcherNode.hasMouse(): return
        mpos = base.mouseWatcherNode.getMouse()
        self.delta_x = mpos.get_x() - self.start_x
        self.delta_y = mpos.get_y() - self.start_y
        self.update()

    def start(self, target, orbit_speed_x, orbit_speed_z, orientation = None):
        self.delta_x = 0
        self.delta_y = 0
        self.orbit_speed_x = orbit_speed_x
        self.orbit_speed_z = orbit_speed_z
        center = target.get_rel_position_to(self.anchor._global_position)
        self.orbit_center = self.anchor.frame.get_rel_position(center)
        orbit_position = self.anchor.get_frame_pos()
        self.orbit_dir = self.orbit_center - orbit_position
        if orientation is None:
            self.orbit_orientation = self.anchor.get_frame_rot()
        else:
            self.orbit_orientation = orientation
        self.orbit_zaxis = self.orbit_orientation.xform(LVector3d.up())
        self.orbit_xaxis = self.orbit_orientation.xform(LVector3d.right())

    def start_mouse(self, target, orbit_speed_x, orbit_speed_z, orientation = None):
        if not base.mouseWatcherNode.hasMouse(): return
        mpos = base.mouseWatcherNode.getMouse()
        self.start_x = mpos.get_x()
        self.start_y = mpos.get_y()
        self.start(target, orbit_speed_x, orbit_speed_z, orientation)

class RotateAnchorHelper():
    def __init__(self, anchor):
        self.anchor = anchor
        self.drag_orientation = None
        self.drag_zaxis = None
        self.drag_xaxis = None
        self.start_x = None
        self.start_y = None
        self.orbit_speed_x = None
        self.orbit_speed_z = None

    def update(self):
        if not base.mouseWatcherNode.hasMouse(): return
        mpos = base.mouseWatcherNode.getMouse()
        delta_x = mpos.get_x() - self.start_x
        delta_y = mpos.get_y() - self.start_y
        z_angle = delta_x * self.orbit_speed_z
        x_angle = -delta_y * self.orbit_speed_x
        z_rotation = LQuaterniond()
        z_rotation.set_from_axis_angle_rad(z_angle, self.drag_zaxis)
        x_rotation = LQuaterniond()
        x_rotation.set_from_axis_angle_rad(x_angle, self.drag_xaxis)
        combined = x_rotation * z_rotation
        self.anchor.set_frame_rot(self.drag_orientation * combined)

    def start(self, orbit_speed_x, orbit_speed_z):
        if not base.mouseWatcherNode.hasMouse(): return
        mpos = base.mouseWatcherNode.getMouse()
        self.start_x = mpos.get_x()
        self.start_y = mpos.get_y()
        self.orbit_speed_x = orbit_speed_x
        self.orbit_speed_z = orbit_speed_z
        self.drag_orientation = self.anchor.get_frame_rot()
        self.drag_zaxis = self.drag_orientation.xform(LVector3d.up())
        self.drag_xaxis = self.drag_orientation.xform(LVector3d.right())

class CameraHolder(CameraBase):
    #TODO: this should inherit from the Anchor base class
    def __init__(self, cam, lens):
        CameraBase.__init__(self, cam, lens)
        self.frame = AbsoluteReferenceFrame()
        self._global_position = LPoint3d()
        self.camera_global_pos = self._global_position
        self._position = LPoint3d()
        self._local_position = LPoint3d()
        self._orientation = LQuaterniond()
        self.camera_vector = LVector3d()
        self._frame_position = LPoint3d()
        self._frame_rotation = LQuaterniond()
        self.has_scattering = False
        self.scattering = None
        self.apply_scattering = 0
        self.update_shader_needed = False

    def set_scattering(self, scattering):
        self.scattering = scattering
        self.update_shader_needed = True

    def set_frame(self, frame):
        #Get position and rotation in the absolute reference frame
        pos = self.get_pos()
        rot = self.get_rot()
        #Update reference frame
        self.frame = frame
        #Set back the position to calculate the position in the new reference frame
        self.set_pos(pos)
        self.set_rot(rot)

    def change_global(self, new_global_pos):
        if self._global_position == new_global_pos: return
        old_local = self.frame.get_local_position(self._frame_position)
        new_local = (self._global_position - new_global_pos) + old_local
        self._global_position = new_global_pos
        self.camera_global_pos = self._global_position
        self._frame_position = self.frame.get_rel_position(new_local)

    def get_position(self):
        return self._global_position + self._local_position

    def set_frame_pos(self, position):
        self._frame_position = position

    def get_frame_pos(self):
        return self._frame_position

    def set_frame_rot(self, rotation):
        self._frame_rotation = rotation

    def get_frame_rot(self):
        return self._frame_rotation

    def set_pos(self, position, local=True):
        if not local:
            position -= self._global_position
        self._frame_position = self.frame.get_rel_position(position)

    def get_pos(self):
        return self.frame.get_local_position(self._frame_position)

    def set_rot(self, orientation):
        self._frame_rotation = self.frame.get_rel_orientation(orientation)

    def get_rot(self):
        return self.frame.get_abs_orientation(self._frame_rotation)

    #TODO: Absolete API to be replaced by the above Anchor API
    def get_camera_pos(self):
        return self._local_position

    def get_camera_rot(self):
        return self._orientation

    def get_camera_vector(self):
        return self.camera_vector

    def update(self):
        #TODO: _position should be global + local !
        self._position = self.get_pos()
        self._local_position = self.get_pos()
        self._orientation = self.get_rot()
        self.camera_vector = self._orientation.xform(LVector3d.forward())
        if not settings.camera_at_origin:
            self.cam.setPos(*self.get_camera_pos())
        self.cam.setQuat(LQuaternion(*self.get_camera_rot()))

class EventsControllerBase(DirectObject):
    wheel_event_duration = 0.1

    def __init__(self):
        self.keymap = {}

    def set_key(self, key, state, *keys):
        self.keymap[key] = state
        for key in keys:
            self.keymap[key] = state

    def register_events(self):
        pass

    def remove_events(self):
        self.ignore_all()

class CameraController(EventsControllerBase):
    camera_type = None
    FIXED = 'fixed'
    TRACK = 'track'
    LOOK_AROUND = 'look-around'
    FOLLOW = 'follow'

    def __init__(self):
        EventsControllerBase.__init__(self)
        self.camera = None
        self.reference_point = None
        self.current_interval = None

    def get_name(self):
        return ''

    def get_id(self):
        return ''

    def require_target(self):
        return False

    def set_camera_hints(self, **kwargs):
        pass

    def activate(self, camera, reference_point):
        self.camera = camera
        self.set_reference_point(reference_point)
        self.register_events()

    def deactivate(self):
        self.remove_events()
        self.camera = None
        self.reference_point = None

    def prepare_movement(self):
        pass

    def get_position(self):
        return None

    def set_position(self, position):
        pass

    def get_rotation(self):
        return None

    def set_rotation(self, rotation):
        pass

    def set_abs_rotation(self, rotation):
        rotation = rotation * self.reference_point._orientation.conjugate()
        self.set_rotation(rotation)

    def get_abs_rotation(self):
        rotation = self.get_rotation() * self.reference_point._orientation
        return rotation

    def set_reference_point(self, reference_point):
        self.reference_point = reference_point

    def calc_look_at(self, position, target):
        abs_rotation = self.get_abs_rotation()
        direction = LVector3d(target - position)
        direction.normalize()
        local_direction = abs_rotation.conjugate().xform(direction)
        angle = LVector3d.forward().angleRad(local_direction)
        axis = LVector3d.forward().cross(local_direction)
        if axis.length() > 0.0:
            new_rot = utils.relative_rotation(abs_rotation, axis, angle)
        else:
            new_rot = abs_rotation
        return new_rot, angle

    def do_rot(self, step, origin, delta):
        rotation = origin + delta * step
        rotation.normalize()
        #TODO: should be relative to ship orientation
        self.set_abs_rotation(rotation)
        if step == 1.0:
            self.current_interval = None

    def lookat(self, target, duration = 2.0, proportional=True):
        abs_rotation = self.get_abs_rotation()
        new_rotation, angle = self.calc_look_at(self.reference_point.get_pos(), target)
        if settings.debug_jump: duration = 0
        if duration == 0:
            self.set_abs_rotation(new_rotation)
        else:
            if proportional:
                duration = duration * angle / pi
            if self.current_interval != None:
                self.current_interval.pause()
            self.current_interval = LerpFunc(self.do_rot,
                fromData=0,
                toData=1,
                duration=duration,
                blendType='easeInOut',
                extraArgs=[abs_rotation, new_rotation - abs_rotation],
                name=None)
            self.current_interval.start()

    def center_on_object(self, target, duration=None, cmd=True, proportional=True):
        if duration is None:
            duration = settings.fast_move
        if target is None: return
        if cmd: print("Center on", target.get_name())
        center = target.get_rel_position_to(self.reference_point._global_position)
        self.lookat(center, duration=duration, proportional=proportional)

    def update(self, time, dt):
        pass

class FixedCameraController(CameraController):
    camera_mode = CameraController.FIXED
    STATE_DEFAULT = 'default'
    STATE_MOUSE_DRAG = 'mouse-drag'

    def __init__(self):
        CameraController.__init__(self)
        self.state = self.STATE_DEFAULT
        self.rotation = LQuaterniond()
        self.is_looking_back = False
        self.reference_pos = None
        self.distance = 5.0
        self.reference_rot = LQuaterniond()

    def get_name(self):
        return _('Fixed camera')

    def get_id(self):
        return "fixed"

    def set_camera_hints(self, **kwargs):
        self.reference_pos = kwargs.get('position',  None)
        self.distance = kwargs.get('distance',  self.distance)

    def register_events(self):
        self.accept('*', self.look_back)
        self.accept("mouse1", self.mouse_click_event)
        self.accept("mouse1-up", self.mouse_release_event)

    def mouse_click_event(self):
        if not self.state == self.STATE_DEFAULT: return
        self.mouse_control = RotateAnchorHelper(self.camera)
        orbit_speed_z = self.camera.realCamLens.getHfov() / 180 * pi / 2
        orbit_speed_x = self.camera.realCamLens.getVfov() / 180 * pi / 2
        self.mouse_control.start(orbit_speed_x, orbit_speed_z)
        self.state = self.STATE_MOUSE_DRAG

    def mouse_release_event(self):
        if self.state == self.STATE_MOUSE_DRAG:
            self.mouse_control = None
            self.state = self.STATE_DEFAULT

    def get_rotation(self):
        return self.rotation

    def set_rotation(self, rotation):
        if rotation is not None:
            self.rotation = rotation

    def prepare_movement(self):
        rotation = self.rotation * self.reference_point._orientation
        self.reference_point.set_rot(rotation)
        self.rotation = LQuaterniond()

    def look_back(self):
        self.rotation = LQuaterniond()
        if not self.is_looking_back:
            self.rotation.setFromAxisAngleRad(pi, LVector3d.up())
        self.is_looking_back = not self.is_looking_back

    def update(self, time, dt):
        reference_pos = self.reference_pos
        if reference_pos is None:
            reference_pos = -LVector3d().forward() * self.reference_point.get_apparent_radius() * self.distance
        local_position = self.reference_point._local_position + self.reference_point._orientation.xform(reference_pos)
        self.camera.change_global(self.reference_point._global_position)
        self.camera.set_pos(local_position)
        if self.state == self.STATE_DEFAULT:
            rotation = self.rotation * self.reference_point._orientation
            self.camera.set_rot(rotation)
        elif self.state == self.STATE_MOUSE_DRAG:
            self.mouse_control.update()
            self.rotation = self.camera.get_rot() * self.reference_point._orientation.conjugate()
        else:
            print("Unknown state", self.state)
        self.camera.update()

class TrackCameraController(CameraController):
    camera_mode = CameraController.TRACK

    def __init__(self):
        CameraController.__init__(self)
        self.target = None
        self.reference_pos = None
        self.distance = 5.0
        self.rotation = LQuaterniond()

    def get_name(self):
        return _('Track camera')

    def get_id(self):
        return "track"

    def require_target(self):
        return True

    def set_target(self, target):
        self.target = target

    def set_camera_hints(self, **kwargs):
        self.reference_pos = kwargs.get('position',  None)
        self.distance = kwargs.get('distance',  self.distance)

    def get_rotation(self):
        return self.rotation

    def set_rotation(self, rotation):
        if rotation is not None:
            self.rotation = rotation

    def update(self, time, dt):
        reference_pos = self.reference_pos
        if reference_pos is None:
            reference_pos = -LVector3d().forward() * self.reference_point.get_apparent_radius() * self.distance
        self.center_on_object(self.target, duration=0, cmd=False)

        local_position = self.reference_point._local_position + self.reference_point._orientation.xform(reference_pos)
        rotation = self.rotation * self.reference_point._orientation
        self.camera.change_global(self.reference_point._global_position)
        self.camera.set_pos(local_position)
        self.camera.set_rot(rotation)
        self.camera.update()

class LookAroundCameraController(CameraController):
    camera_mode = CameraController.LOOK_AROUND
    def __init__(self):
        CameraController.__init__(self)
        self.rotation = LQuaterniond()
        self.reference_pos = LPoint3d()
        self.reference_rot = LQuaterniond()

    def get_name(self):
        return _('Look around camera')

    def get_id(self):
        return "look-around"

    def set_camera_hints(self, **kwargs):
        self.reference_pos = kwargs.get('position',  self.reference_pos)
        self.reference_rot = kwargs.get('rotation', self.reference_rot)

    def update(self, time, dt):
        if base.mouseWatcherNode.hasMouse():
            mpos = base.mouseWatcherNode.getMouse()
            x_angle = mpos.get_y() * pi / 2
            z_angle = mpos.get_x() * pi / 2
            x_rotation = LQuaterniond()
            x_rotation.setFromAxisAngleRad(x_angle, LVector3d.right())
            z_rotation = LQuaterniond()
            z_rotation.setFromAxisAngleRad(-z_angle, LVector3d.up())
            self.rotation = x_rotation * z_rotation

        local_position = self.reference_point._local_position + self.reference_point._orientation.xform(self.reference_pos)
        orientation = self.reference_rot * self.rotation * self.reference_point._orientation
        self.camera.change_global(self.reference_point._global_position)
        self.camera.set_pos(local_position)
        self.camera.set_rot(orientation)
        self.camera.update()

class FollowCameraController(CameraController):
    camera_mode = CameraController.FOLLOW
    def __init__(self):
        CameraController.__init__(self)
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
        min_distance = self.reference_point.get_apparent_radius() * self.distance
        max_distance = self.reference_point.get_apparent_radius() * self.distance * self.max_distance

        self.camera.update()
        camera_position = self.camera._local_position
        vector_to_reference = self.reference_point._local_position - camera_position
        distance = vector_to_reference.length()
        vector_to_reference.normalize()
        if min_distance > 0 and distance == 0:
            vector_to_reference = self.reference_point._orientation.xform(-LVector3d.forward())
            distance = 1.0
        if distance > max_distance:
            camera_position = camera_position + vector_to_reference * (distance - max_distance)
        if distance < min_distance:
            camera_position = camera_position - vector_to_reference * (min_distance - distance)

        vector_to_reference = self.reference_point._local_position - camera_position
        vector_to_reference.normalize()
        camera_orientation = LQuaterniond()
        look_at(camera_orientation, vector_to_reference, self.reference_point._orientation.xform(LVector3d.up()))

        self.camera.change_global(self.reference_point._global_position)
        self.camera.set_pos(camera_position)
        self.camera.set_rot(camera_orientation)
        self.camera.update()

class SurfaceFollowCameraController(CameraController):
    camera_mode = CameraController.FOLLOW
    STATE_DEFAULT = 'default'
    STATE_ORBIT_MOUSE = 'orbit-mouse'
    STATE_ORBIT_KEYBOARD = 'orbit-keyboard'

    def __init__(self, orbit_body=True, change_distance=True):
        CameraController.__init__(self)
        self.orbit_body = orbit_body
        self.change_distance = change_distance
        self.body = None
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

    def set_body(self, body):
        self.body = body

    def calc_projected_orientation(self):
        projected_vector_to_reference = self.reference_point._local_position - self.camera._local_position
        projected_vector_to_reference[2] = 0.0
        projected_vector_to_reference.normalize()
        orientation = LQuaterniond()
        look_at(orientation, projected_vector_to_reference, self.reference_point._orientation.xform(LVector3d.up()))
        return orientation

    def mouse_click_event(self):
        if not self.state == self.STATE_DEFAULT: return
        orientation = self.calc_projected_orientation()
        self.mouse_control = OrbitTargetHelper(self.camera)
        self.mouse_control.start_mouse(self.reference_point, pi, pi, orientation)
        self.state = self.STATE_ORBIT_MOUSE

    def mouse_release_event(self):
        if self.state == self.STATE_ORBIT_MOUSE:
            self.mouse_control = None
            self.state = self.STATE_DEFAULT

    def do_change_distance(self, step):
        vector_to_reference = self.reference_point._local_position - self.camera._local_position
        distance = vector_to_reference.length()
        vector_to_reference.normalize()
        new_distance = max(self.reference_min_distance, distance * (1.0 + step))
        new_position = self.reference_point._local_position - vector_to_reference * new_distance
        self.distance = new_distance / self.reference_point.get_apparent_radius()
        surface_height = self.body.get_height_under(new_position)
        self.height = new_position[2] - surface_height
        self.camera.set_pos(new_position)
        self.camera.update()

    def update_limits(self):
        surface_height = self.body.get_height_under(self.camera._local_position)
        vector_to_reference = self.reference_point._local_position - self.camera._local_position
        self.height = self.camera._local_position[2] - surface_height
        vector_to_reference[2] = 0.0
        distance = vector_to_reference.length()
        self.distance = max(self.reference_min_distance, distance / self.reference_point.get_apparent_radius())

    def update_lookat(self):
        camera_position = self.camera._local_position
        vector_to_reference = self.reference_point._local_position - camera_position
        vector_to_reference.normalize()
        camera_orientation = LQuaterniond()
        look_at(camera_orientation, vector_to_reference, self.reference_point._orientation.xform(LVector3d.up()))
        self.camera.set_rot(camera_orientation)

    def update(self, time, dt):
        if self.state == self.STATE_DEFAULT:
            if self.keymap.get('shift-left') or self.keymap.get('shift-right') or self.keymap.get('shift-up') or self.keymap.get('shift-down'):
                orientation = self.calc_projected_orientation()
                self.mouse_control = OrbitTargetHelper(self.camera)
                self.mouse_control.start(self.reference_point, pi, pi, orientation)
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
            min_distance = self.reference_point.get_apparent_radius() * self.distance
            max_distance = self.reference_point.get_apparent_radius() * self.distance * self.max_distance
            camera_position = self.camera._local_position
            projected_vector_to_reference = self.reference_point._local_position - camera_position
            projected_vector_to_reference[2] = 0.0
            distance = projected_vector_to_reference.length()
            projected_vector_to_reference.normalize()
            if min_distance > 0 and distance == 0:
                projected_vector_to_reference = self.reference_point._orientation.xform(LVector3d.forward())
                distance = 1.0
            if distance > max_distance:
                camera_position = camera_position + projected_vector_to_reference * (distance - max_distance)
            if distance < min_distance:
                camera_position = camera_position - projected_vector_to_reference * (min_distance - distance)

            surface_height = self.body.get_height_under(self.camera._local_position)
            target_height = self.reference_point._local_position[2]
            #print(self.height, self.min_height, surface_height, target_height)
            if surface_height + self.min_height < target_height + self.height:
                new_camera_height = target_height + self.height
            else:
                new_camera_height = surface_height + self.min_height
            camera_position[2] = new_camera_height
            vector_to_reference = self.reference_point._local_position - camera_position
            vector_to_reference.normalize()
            camera_orientation = LQuaterniond()
            look_at(camera_orientation, vector_to_reference, self.reference_point._orientation.xform(LVector3d.up()))

            self.camera.change_global(self.reference_point._global_position)
            self.camera.set_pos(camera_position)
            self.camera.set_rot(camera_orientation)
            self.camera.update()
        else:
            print("Unknown state", self.state)
