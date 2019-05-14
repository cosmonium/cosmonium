from __future__ import print_function
from __future__ import absolute_import

from panda3d.core import ColorBlendAttrib, CullFaceAttrib, TransparencyAttrib
from panda3d.core import DepthOffsetAttrib
from .appearances import Appearance
from .shapes import ShapeObject, SphereShape, RingShape
from . import settings

class Ring(ShapeObject):
    def __init__(self, inner_radius, outer_radius, appearance=None, shader=None):
        ShapeObject.__init__(self, 'ring', appearance=appearance, shader=shader, clickable=True)
        self.inner_radius = inner_radius
        self.outer_radius = outer_radius
        self.set_shape(RingShape(inner_radius, outer_radius))

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
        self.alpha_mode = None

    def get_pixel_height(self):
        return self.parent.visible_size * (self.ratio - 1.0)

    def check_visibility(self, pixel_size):
        ShapeObject.check_visibility(self, pixel_size)
        if self.get_pixel_height() < 1.0:
            self.visible = False

    def create_instance(self):
        self.shape.set_radius(self.radius)
        ShapeObject.create_instance(self)
        self.instance.setTransparency(TransparencyAttrib.MAlpha)
        blendAttrib = ColorBlendAttrib.make(ColorBlendAttrib.MAdd, ColorBlendAttrib.OOne, self.alpha_mode)
        self.instance.setAttrib(blendAttrib)
        self.instance.setAttrib(CullFaceAttrib.make(CullFaceAttrib.MCullCounterClockwise))
        self.instance.set_depth_write(False)

        def create_scattering_shader(self, atmosphere, calc_in_fragment):
            return None

class NoAtmosphere(Atmosphere):
    def check_visibility(self, pixel_size):
        self.visible = False

    def create_scattering_shader(self, atmosphere, calc_in_fragment, normalize):
        return None

class Clouds(ShapeObject):
    def __init__(self, height, appearance, shader=None, shape=None):
        if shape is None:
            shape = SphereShape()
        ShapeObject.__init__(self, 'clouds', shape=shape, appearance=appearance, shader=shader, clickable=False)
        self.height = height
        self.inside = False
        if appearance is not None:
            #TODO: Disabled as it causes blinking
            pass#appearance.check_transparency()
        self.check_settings()
 
    def set_scale(self, scale):
        factor = 1.0 + self.height/self.parent.get_apparent_radius()
        self.shape.set_scale(scale * factor)

    def check_settings(self):
        self.set_shown(settings.show_clouds)

    def create_instance(self):
        ShapeObject.create_instance(self)
        #geomNode = self.parent.instance.find('**/+GeomNode')
        #self.instance.reparentTo(geomNode)
        #geomNode.setEffect(DecalEffect.make())
        if not settings.use_inverse_z:
            self.instance.setAttrib(DepthOffsetAttrib.make(int(self.height)))

    def update_instance(self, camera_pos, orientation):
        radius = self.parent.get_apparent_radius() + self.height
        inside = self.parent.distance_to_obs < radius
        if self.inside != inside:
            if inside:
                self.instance.setAttrib(CullFaceAttrib.make(CullFaceAttrib.MCullCounterClockwise))
            else:
                self.instance.setAttrib(CullFaceAttrib.make(CullFaceAttrib.MCullClockwise))
            self.inside = inside
        return ShapeObject.update_instance(self, camera_pos, orientation)
