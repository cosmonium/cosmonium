from __future__ import print_function
from __future__ import absolute_import

from panda3d.core import CullFaceAttrib
from panda3d.core import DepthOffsetAttrib

from .appearances import Appearance
from .shapes import ShapeObject, SphereShape, RingShape
from .surfaces import FlatSurface
from .utils import TransparencyBlend
from .shaders import AtmosphericScattering
from .shadows import RingShadowCaster

from . import settings

class Ring(ShapeObject):
    def __init__(self, inner_radius, outer_radius, appearance=None, shader=None):
        ShapeObject.__init__(self, 'ring', appearance=appearance, shader=shader, clickable=True)
        self.inner_radius = inner_radius
        self.outer_radius = outer_radius
        self.set_shape(RingShape(inner_radius, outer_radius))
        self.shadow_caster = RingShadowCaster(self)

class Atmosphere(ShapeObject):
    def __init__(self, shape=None, appearance=None, shader=None):
        if shape is None:
            shape = SphereShape()
        if appearance is None:
            appearance = Appearance()
        ShapeObject.__init__(self, 'atmosphere', shape=shape, appearance=appearance, shader=shader, clickable=False)
        self.planet_radius = 0
        self.radius = 0
        self.ratio = 0
        self.blend = TransparencyBlend.TB_None
        self.shape_objects = []
        self.check_settings()

    def check_settings(self):
        if settings.show_atmospheres != self.shown:
            for shape_object in self.shape_objects:
                if self.shown:
                    self.remove_scattering_on(shape_object)
                else:
                    self.set_scattering_on(shape_object)
        self.set_shown(settings.show_atmospheres)

    def set_scattering_on(self, shape_object):
        if shape_object.shader is not None:
            scattering = self.create_scattering_shader(atmosphere=False)
            shape_object.shader.set_scattering(scattering)
            shape_object.update_shader()

    def remove_scattering_on(self, shape_object):
        if shape_object.shader is not None:
            shape_object.shader.set_scattering(AtmosphericScattering())
            shape_object.update_shader()

    def add_shape_object(self, shape_object):
        self.shape_objects.append(shape_object)
        if self.shown:
            self.set_scattering_on(shape_object)

    def remove_shape_object(self, shape_object):
        if shape_object in self.shape_objects:
            self.shape_objects.remove(shape_object)
            if self.shown:
                self.remove_scattering_on(shape_object)

    def get_pixel_height(self):
        return self.parent.visible_size * (self.ratio - 1.0)

    def check_visibility(self, pixel_size):
        ShapeObject.check_visibility(self, pixel_size)
        if self.get_pixel_height() < 1.0:
            self.visible = False

    def create_instance(self):
        self.shape.set_radius(self.radius)
        ShapeObject.create_instance(self)
        TransparencyBlend.apply(self.blend, self.instance)
        self.instance.setAttrib(CullFaceAttrib.make(CullFaceAttrib.MCullCounterClockwise))
        self.instance.set_depth_write(False)

    def create_scattering_shader(self, atmosphere):
        return AtmosphericScattering()

class NoAtmosphere(Atmosphere):
    def check_visibility(self, pixel_size):
        self.visible = False

class Clouds(FlatSurface):
    def __init__(self, height, appearance, shader=None, shape=None):
        if shape is None:
            shape = SphereShape()
        FlatSurface.__init__(self, 'clouds', shape=shape, appearance=appearance, shader=shader, clickable=False)
        self.height = height
        self.inside = None
        if appearance is not None:
            #TODO: Disabled as it causes blinking
            pass#appearance.check_transparency()
        self.check_settings()
 
    def set_scale(self, scale):
        factor = 1.0 + self.height/self.parent.get_apparent_radius()
        self.shape.set_scale(scale * factor)

    def check_settings(self):
        self.set_shown(settings.show_clouds)

    def update_instance(self, camera_pos, orientation):
        radius = self.parent.get_apparent_radius() + self.height
        inside = self.parent.distance_to_obs < radius
        if self.inside != inside:
            if inside:
                self.instance.setAttrib(CullFaceAttrib.make(CullFaceAttrib.MCullCounterClockwise))
                if not settings.use_inverse_z:
                    self.instance.setAttrib(DepthOffsetAttrib.make(0))
                self.instance.set_depth_write(True)
            else:
                self.instance.setAttrib(CullFaceAttrib.make(CullFaceAttrib.MCullClockwise))
                if not settings.use_inverse_z:
                    self.instance.setAttrib(DepthOffsetAttrib.make(1))
                self.instance.set_depth_write(False)
            self.inside = inside
        return ShapeObject.update_instance(self, camera_pos, orientation)
