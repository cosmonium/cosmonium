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

from panda3d.core import CullFaceAttrib
from panda3d.core import DepthOffsetAttrib

from .appearances import Appearance
from .shapes import ShapeObject, SphereShape, RingShape
from .surfaces import FlatSurface
from .utils import TransparencyBlend
from .shaders import AtmosphericScattering
from .shadows import RingShadowCaster
from .parameters import AutoUserParameter

from . import settings

class Ring(ShapeObject):
    def __init__(self, inner_radius, outer_radius, appearance=None, shader=None):
        ShapeObject.__init__(self, 'ring', appearance=appearance, shader=shader, clickable=True)
        self.inner_radius = inner_radius
        self.outer_radius = outer_radius
        self.set_shape(RingShape(inner_radius, outer_radius))
        self.shadow_caster = RingShadowCaster(self)
        self.shape.vanish_borders = True

    def get_component_name(self):
        return 'Ring'

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

    def get_component_name(self):
        return 'Atmosphere'

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

    def update_scattering(self):
        if not settings.show_atmospheres: return
        for shape_object in self.shape_objects:
            self.do_update_scattering(shape_object)
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

    def update_user_parameters(self):
        ShapeObject.update_user_parameters(self)
        self.update_scattering()

class Clouds(FlatSurface):
    def __init__(self, height, appearance, shader=None, shape=None):
        if shape is None:
            shape = SphereShape()
        FlatSurface.__init__(self, 'clouds', shape=shape, appearance=appearance, shader=shader, clickable=False)
        self.height = height
        self.scale_base = None
        self.inside = None
        if appearance is not None:
            #TODO: Disabled as it causes blinking
            pass#appearance.check_transparency()
 
    def get_component_name(self):
        return 'Clouds'

    def set_scale(self, scale):
        self.scale_base = scale
        factor = 1.0 + self.height/self.parent.get_apparent_radius()
        self.shape.set_scale(scale * factor)

    def check_settings(self):
        self.set_shown(settings.show_clouds)

    def update_instance(self, camera_pos, camera_rot):
        radius = self.parent.get_apparent_radius() + self.height
        inside = self.parent.distance_to_obs < radius
        if self.inside != inside:
            if inside:
                self.instance.setAttrib(CullFaceAttrib.make(CullFaceAttrib.MCullCounterClockwise))
                if not settings.use_inverse_z:
                    self.instance.setAttrib(DepthOffsetAttrib.make(0))
                if self.appearance.transparency:
                    self.instance.set_depth_write(True)
            else:
                self.instance.setAttrib(CullFaceAttrib.make(CullFaceAttrib.MCullClockwise))
                if not settings.use_inverse_z:
                    self.instance.setAttrib(DepthOffsetAttrib.make(1))
                if self.appearance.transparency:
                    self.instance.set_depth_write(False)
            self.inside = inside
        return FlatSurface.update_instance(self, camera_pos, camera_rot)

    def remove_instance(self):
        FlatSurface.remove_instance(self)
        self.inside = None

    def set_height(self, height):
        self.height = height

    def get_height(self):
        return self.height

    def get_user_parameters(self):
        group = ShapeObject.get_user_parameters(self)
        group.add_parameter(AutoUserParameter('Height', 'height', self, AutoUserParameter.TYPE_FLOAT, [0, self.parent.get_apparent_radius() * 0.01]))
        return group

    def update_user_parameters(self):
        ShapeObject.update_user_parameters(self)
        self.set_scale(self.scale_base)
