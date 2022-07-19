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


from panda3d.core import LVector3, LVector3d

from ...foundation import ObjectLabel
from ... import settings


class BackgroundLabel(ObjectLabel):
    color_picking = False

    def create_instance(self):
        ObjectLabel.create_instance(self)
        self.instance.setBin('background', self.label_source.background_level)
        infinity = self.context.scene_manager.infinity
        if self.label_source is not None:
            self.rel_position = self.label_source.project(0, self.context.observer.get_absolute_position(), infinity)
        else:
            self.rel_position = None
        if self.rel_position != None:
            self.instance.set_pos(*self.rel_position)

    def check_visibility(self, frustum, pixel_size):
        ObjectLabel.check_visibility(self, frustum, pixel_size)
        if self.visible and self.instance is not None:
            self.visible = frustum.is_sphere_in(self.rel_position, 0)

    def update_instance(self, scene_manager, camera_pos, orientation):
        self.look_at.set_pos(LVector3(*(orientation.xform(LVector3d.forward()))))
        if self.rel_position != None:
            distance = self.rel_position.length()
            vector = self.rel_position / distance
            z_coef = vector.dot(self.context.observer.anchor.camera_vector)
            z_distance = distance * z_coef
            scale = abs(self.context.observer.pixel_size * self.label_source.get_label_size() * z_distance * settings.ui_scale)
        else:
            scale = 0.0
        if scale < 1e-7:
            print("Label too far", self.get_name())
            scale = 1e-7
        self.instance.set_scale(scale)
        self.label_instance.look_at(self.look_at, LVector3(), LVector3(*(orientation.xform(LVector3d.up()))))

