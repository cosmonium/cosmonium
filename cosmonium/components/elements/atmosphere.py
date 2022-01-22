#
#This file is part of Cosmonium.
#
#Copyright (C) 2018-2022 Laurent Deru.
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


from panda3d.core import CullFaceAttrib
from panda3d.core import LQuaternion

from ...appearances import Appearance
from ...shapes import ShapeObject, SphereShape
from ...utils import TransparencyBlend
from ...shaders.scattering import AtmosphericScattering

from ... import settings


class Atmosphere(ShapeObject):
    def __init__(self, shape=None, appearance=None, shader=None):
        if shape is None:
            shape = SphereShape()
        if appearance is None:
            appearance = Appearance()
        ShapeObject.__init__(self, 'atmosphere', shape=shape, appearance=appearance, shader=shader, clickable=False)
        self.inside = None
        self.body = None
        self.body_radius = None
        self.radius = None
        self.ratio = None
        self.blend = TransparencyBlend.TB_None
        self.shape_objects = []
        self.attenuated_objects = []
        self.sources.add_source(self.create_data_source())

    def get_component_name(self):
        return _('Atmosphere')

    def configure_render_order(self):
        self.instance.set_bin("transparent", 0)

    def set_body(self, body):
        self.body = body

    def check_settings(self):
        if settings.show_atmospheres != self.shown:
            for shape_object in self.shape_objects:
                if self.shown:
                    self.remove_scattering_on(shape_object)
                else:
                    self.set_scattering_on(shape_object, extinction=False)
            for shape_object in self.attenuated_objects:
                if self.shown:
                    self.remove_scattering_on(shape_object)
                else:
                    self.set_scattering_on(shape_object, extinction=True)
        self.set_shown(settings.show_atmospheres)

    def set_scattering_on(self, shape_object, extinction):
        data_source = self.create_data_source()
        scattering = self.create_scattering_shader(atmosphere=False, displacement=not shape_object.is_flat(), extinction=extinction)
        shape_object.set_scattering(data_source, scattering)

    def remove_scattering_on(self, shape_object):
        shape_object.remove_scattering()

    def do_update_scattering(self, shape_object, atmosphere, extinction):
        pass

    def update_scattering(self):
        if not settings.show_atmospheres: return
        self.do_update_scattering(self, atmosphere=True, extinction=False)
        self.update_shader()
        for shape_object in self.shape_objects:
            self.do_update_scattering(shape_object, atmosphere=False, extinction=False)
            shape_object.update_shader()
        for shape_object in self.attenuated_objects:
            self.do_update_scattering(shape_object, atmosphere=False, extinction=True)
            shape_object.update_shader()

    def add_shape_object(self, shape_object):
        if shape_object in self.shape_objects: return
        print("Add scattering on", shape_object.get_name())
        self.shape_objects.append(shape_object)
        if shape_object in self.attenuated_objects:
            self.attenuated_objects.remove(shape_object)
        if self.shown:
            self.set_scattering_on(shape_object, extinction=False)

    def remove_shape_object(self, shape_object):
        if shape_object in self.shape_objects:
            print("Remove scattering on", shape_object.get_name())
            self.shape_objects.remove(shape_object)
            if self.shown:
                self.remove_scattering_on(shape_object)

    def add_attenuated_object(self, shape_object):
        if shape_object is self: return
        if shape_object in self.shape_objects: return
        if shape_object in self.attenuated_objects: return
        print("Apply extinction on", shape_object.owner.get_name(), ':', shape_object.get_name())
        self.attenuated_objects.append(shape_object)
        if self.shown:
            self.set_scattering_on(shape_object, extinction=True)

    def remove_attenuated_object(self, shape_object):
        if shape_object in self.attenuated_objects:
            self.attenuated_objects.remove(shape_object)
            if self.shown:
                self.remove_scattering_on(shape_object)

    def get_pixel_height(self):
        return self.body.anchor.visible_size * (self.ratio - 1.0)

    def check_visibility(self, frustum, pixel_size):
        ShapeObject.check_visibility(self, frustum, pixel_size)
        if self.get_pixel_height() < 1.0:
            self.visible = False

    async def create_instance(self, scene_anchor):
        #TODO: Find a better way to retrieve ellipticity
        scale = self.body.surface.get_scale() / self.body_radius
        self.set_scale(scale * self.radius)
        await ShapeObject.create_instance(self, scene_anchor)
        TransparencyBlend.apply(self.blend, self.instance)
        self.instance.setAttrib(CullFaceAttrib.make(CullFaceAttrib.MCullCounterClockwise))
        self.instance.set_depth_write(False)

    def update_shader_params(self):
        pass

    def update_obs(self, observer):
        ShapeObject.update_obs(self, observer)
        inside = self.body.anchor.distance_to_obs < self.radius
        if self.inside != inside:
            self.inside = inside
            self.update_shader_params()
            self.update_shader()
            self.update_scattering()
            if self.inside:
                print("Entering atmosphere")
                observer.has_scattering = True
                observer.scattering = self
                #TODO: To replace with a flag once update_id is merged in
                observer.apply_scattering = 5
            else:
                print("Leaving atmosphere")
                for shape_object in self.attenuated_objects:
                    self.remove_scattering_on(shape_object)
                    shape_object.update_shader()
                observer.has_scattering = False
                observer.scattering = None
                observer.apply_scattering = 0
                self.attenuated_objects = []
        elif observer.apply_scattering > 0:
            observer.apply_scattering -= 1

    def create_data_source(self):
        raise NotImplementedError()

    def create_scattering_shader(self, atmosphere, displacement, extinction):
        return AtmosphericScattering()

    def update_user_parameters(self):
        ShapeObject.update_user_parameters(self)
        self.update_scattering()

    def update_instance(self, scene_manager, camera_pos, camera_rot):
        ShapeObject.update_instance(self, scene_manager, camera_pos, camera_rot)
        if not self.instance_ready: return
        self.instance.set_quat(LQuaternion(*self.body.anchor.get_absolute_orientation()))

    def remove_instance(self):
        ShapeObject.remove_instance(self)
        self.inside = None
        for shape_object in self.attenuated_objects:
            self.remove_scattering_on(shape_object)
        self.attenuated_objects = []
        self.context.observer.has_scattering = False
        self.context.observer.scattering = None
        self.context.observer.apply_scattering = 0
