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


from panda3d.core import LPoint3d, LVector3d, LVector3, LColor, LPoint3

from ...foundation import ObjectLabel
from ... import settings


class StellarBodyLabel(ObjectLabel):
    def create_instance(self):
        ObjectLabel.create_instance(self)
        if settings.color_picking and self.label_source.oid_color is not None:
            self.instance.set_shader_input("color_picking", self.label_source.oid_color)

    def check_visibility(self, frustum, pixel_size):
        if hasattr(self.label_source, "primary") and self.label_source.anchor.resolved:
            self.visible = False
            return
        if self.label_source.system is not None:
            body = self.label_source.system
        else:
            body = self.label_source
        if self.label_source.anchor.visible and self.label_source.anchor.resolved:
            self.visible = True
            self.fade = 1.0
        else:
            if body.anchor.distance_to_obs > 0.0:
                size = body.anchor.get_position_bounding_radius() / (body.anchor.distance_to_obs * pixel_size)
                self.visible = size > settings.label_fade
                self.fade = min(1.0, max(0.0, (size - settings.orbit_fade) / settings.orbit_fade))
        self.fade = clamp(self.fade, 0.0, 1.0)

    def update_instance(self, scene_manager, camera_pos, camera_rot):
        body = self.label_source
        if body.is_emissive() and (not body.anchor.resolved or body.background):
            self.instance.set_pos(LPoint3())
            scale = abs(self.context.observer.pixel_size * body.get_label_size() * body.anchor.z_distance)
        else:
            offset = body.get_bounding_radius()
            position = - camera_rot.xform(LPoint3d(0, offset, 0))
            z_coef = -body.anchor.vector_to_obs.dot(body.context.observer.anchor.camera_vector)
            z_distance = (body.anchor.distance_to_obs - offset) * z_coef
            self.instance.set_pos(*position)
            scale = abs(self.context.observer.pixel_size * body.get_label_size() * z_distance)
        self.look_at.set_pos(LVector3(*(camera_rot.xform(LVector3d.forward()))))
        self.label_instance.look_at(self.look_at, LVector3(), LVector3(*(camera_rot.xform(LVector3d.up()))))
        self.instance.set_color_scale(LColor(self.fade, self.fade, self.fade, 1.0))
        if scale < 1e-7:
            print("Label too far", self.get_name(), scale)
            scale = 1e-7
        self.instance.set_scale(scale)


class FixedOrbitLabel(StellarBodyLabel):
    def check_visibility(self, frustum, pixel_size):
        #TODO: Should be refactored !
        if hasattr(self.label_source, "primary") and self.label_source.anchor.resolved and (self.label_source.primary is None or (self.label_source.primary.label is not None and self.label_source.primary.label.visible)):
            self.visible = False
            return
        self.visible = self.label_source.anchor._app_magnitude < settings.label_lowest_app_magnitude
        self.fade = 0.2 + (settings.label_lowest_app_magnitude - self.label_source.anchor._app_magnitude) / (settings.label_lowest_app_magnitude - settings.max_app_magnitude)
        self.fade = clamp(self.fade, 0.0, 1.0)
