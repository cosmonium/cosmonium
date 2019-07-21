from __future__ import print_function
from __future__ import absolute_import

from panda3d.core import LPoint3d, LVector3d, LQuaterniond, LQuaternion

from .astro.frame import AbsoluteReferenceFrame
from .settings import near_plane
from . import settings
from . import utils

from math import sin, cos, acos, tan, atan, sqrt, pi, log

class CameraBase(object):
    def __init__(self, cam, lens):
        #Camera node
        self.cam = cam
        self.camLens = lens
        #Field of view (vertical)
        self.fov = None
        #Camera film size
        self.width = 0
        self.height = 0
        #Focal configuration
        self.default_focal = None
        self.focal = None
        self.min_focal = None
        #Current zoom factor
        self.zoom_factor = 1.0

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
        screen_width = base.pipe.getDisplayWidth()
        screen_height = base.pipe.getDisplayHeight()
        self.width = screen_width
        self.height = screen_height
        self.fov = settings.default_fov
        self.min_focal = screen_height / tan(settings.max_fov * pi / 180 / 2.0) / 2.0
        self.max_focal = screen_height / tan(settings.min_fov * pi / 180 / 2.0) / 2.0
        self.calc_fov()
        self.set_film_size(self.width, self.height)

    def calc_fov(self):
        hfov = 2 * atan(tan(self.fov * pi / 180 / 2) * self.width / self.height) * 180 / pi
        self.camLens.set_film_size(self.width, self.height)
        self.camLens.set_fov(hfov, self.fov)
        self.realCamLens.set_film_size(self.width, self.height)
        self.realCamLens.set_fov(hfov, self.fov)
        self.focal = self.camLens.get_focal_length()
        self.default_focal = self.focal

    def set_focal(self, new_focal):
        if new_focal >= self.min_focal and new_focal <= self.max_focal:
            self.camLens.set_focal_length(new_focal)
            self.realCamLens.set_focal_length(new_focal)
            self.focal = new_focal
            self.calc_pixel_size()

    def set_film_size(self, width, height):
        self.camLens.setFilmSize(width, height)
        self.camLens.set_focal_length(self.focal)
        self.realCamLens.setFilmSize(width, height)
        self.realCamLens.set_focal_length(self.focal)
        self.height = height
        self.width = width
        self.calc_pixel_size()

    def zoom(self, factor):
        zoom_factor = self.zoom_factor * factor
        new_focal = self.default_focal * zoom_factor
        if new_focal >= self.min_focal and new_focal <= self.max_focal:
            self.zoom_factor = zoom_factor
            self.set_focal(new_focal)

    def set_fov(self, new_fov):
        if new_fov >= settings.min_fov and new_fov <= settings.max_fov:
            print("Setting FoV to", new_fov)
            self.fov = new_fov
            self.calc_fov()
            self.set_focal(self.default_focal * self.zoom_factor)

    def calc_pixel_size(self):
        self.height = self.height
        self.ratio = float(self.width) / self.height
        fov2 = self.realCamLens.getVfov() / 180 * pi / 2.0
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

class Camera(CameraBase):
    def __init__(self, cam, lens):
        CameraBase.__init__(self, cam, lens)
        #Global position of the camera, i.e. the center of the current system
        self.camera_global_pos = LPoint3d()
        #Local position of the camera within the system in the current camera reference frame
        #Initialize not at zero to avoid null vector when starting to move
        self.camera_pos = LPoint3d(0, -1, 0)
        #Camera orientation in the current camera reference frame
        self.camera_rot = LQuaterniond()
        #Camera reference frame
        self.camera_frame = AbsoluteReferenceFrame()
        #Direction of sight of the camera
        self.camera_vector = LVector3d.forward()

    def set_camera_frame(self, frame):
        #Get position and rotation in the absolute reference frame
        pos = self.get_camera_pos()
        rot = self.get_camera_rot()
        #Update reference frame
        self.camera_frame = frame
        #Set back the camera position to calculate the position in the new reference frame
        self.set_camera_pos(pos)
        self.set_camera_rot(rot)

    def change_global(self, new_global_pos):
        old_local = self.camera_frame.get_local_position(self.camera_pos)
        new_local = (self.camera_global_pos - new_global_pos) + old_local
        self.camera_global_pos = new_global_pos
        self.camera_pos = self.camera_frame.get_rel_position(new_local)

    def get_position(self):
        return self.camera_global_pos + self.camera_frame.get_local_position(self.camera_pos)

    def get_position_of(self, rel_position):
        return self.camera_global_pos + self.camera_frame.get_local_position(rel_position)

    def set_rel_camera_pos(self, position):
        self.camera_pos = position

    def get_rel_camera_pos(self):
        return self.camera_pos

    def set_rel_camera_rot(self, orientation):
        self.camera_rot = orientation

    def get_rel_camera_rot(self):
        return self.camera_rot

    def get_rel_position_of(self, position, local=True):
        if not local:
            position -= self.camera_global_pos
        return self.camera_frame.get_rel_position(position)

    def get_rel_rotation_of(self, orientation):
        return self.camera_frame.get_rel_orientation(orientation)

    def set_camera_pos(self, position, local=True, local_ref=None):
        if local:
            if local_ref is not None:
                position -= (self.camera_global_pos - local_ref)
        else:
            position -= self.camera_global_pos
        self.camera_pos = self.camera_frame.get_rel_position(position)

    def get_camera_pos(self):
        return self.camera_frame.get_local_position(self.camera_pos)
    
    def set_camera_rot(self, orientation):
        self.camera_rot = self.camera_frame.get_rel_orientation(orientation)

    def get_camera_rot(self):
        return self.camera_frame.get_abs_orientation(self.camera_rot)

    def get_camera_vector(self):
        return self.get_camera_rot().xform(LVector3d.forward())

    def update_camera(self):
        #Don't update camera position as everything is relative to camera
        self.camera_vector = self.get_camera_vector()
        self.cam.setQuat(LQuaternion(*self.get_camera_rot()))
        self._position = self.get_camera_pos()
        
    def camera_look_back(self):
        new_rot=utils.relative_rotation(self.get_camera_rot(), LVector3d.up(), pi)
        self.set_camera_rot(new_rot)

    def step_camera(self, delta, absolute=True):
        if absolute:
            self.set_camera_pos(self.get_camera_pos() + delta)
        else:
            self.camera_pos += delta

    def turn_camera(self, orientation, absolute=True):
        if absolute:
            self.set_camera_rot(orientation)
        else:
            self.camera_rot = orientation

    def step_turn_camera(self, delta, absolute=True):
        if absolute:
            self.set_camera_rot(delta * self.get_camera_rot())
        else:
            self.camera_rot = delta * self.camera_rot

    def calc_look_at(self, target, rel=True, position=None):
        if not rel:
            if position is None:
                position = self.get_camera_pos()
            direction = LVector3d(target - position)
        else:
            direction = LVector3d(target)
        direction.normalize()
        local_direction = self.get_camera_rot().conjugate().xform(direction)
        angle=LVector3d.forward().angleRad(local_direction)
        axis=LVector3d.forward().cross(local_direction)
        if axis.length() > 0.0:
            new_rot = utils.relative_rotation(self.get_camera_rot(), axis, angle)
#         new_rot=LQuaterniond()
#         lookAt(new_rot, direction, LVector3d.up())
        else:
            new_rot = self.get_camera_rot()
        return new_rot, angle
