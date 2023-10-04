#
#This file is part of Cosmonium.
#
#Copyright (C) 2018-2023 Laurent Deru.
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


from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional, TYPE_CHECKING

from .. import settings

if TYPE_CHECKING:
    from ..shapes.shape_object import ShapeObject


class ScatteringBase(ABC):

    def __init__(self):
        self.atmospheres: set[ShapeObject] = set()
        self.shape_objects: list[ShapeObject] = []
        self.attenuated_objects: list[ShapeObject] = []
        self.inside: Optional[bool] = None
        self.body = None
        self.light = None

    def clear(self) -> None:
        self.remove_all_attenuated_objects()

    def set_body(self, body):
        self.body = body

    def set_light(self, light):
        self.light = light

    def set_inside(self, inside: bool) -> None:
        self.inside = inside
        self.update_scattering()

    def enable_scattering(self) -> None:
        for shape_object in self.shape_objects:
            atmosphere = shape_object in self.atmospheres
            self.set_scattering_on(shape_object, atmosphere=atmosphere, extinction=False)
        for shape_object in self.attenuated_objects:
            self.set_scattering_on(shape_object, atmosphere=False, extinction=True)

    def disable_scattering(self) -> None:
        for shape_object in self.shape_objects:
            self.remove_scattering_on(shape_object)
        for shape_object in self.attenuated_objects:
            self.remove_scattering_on(shape_object)

    def set_scattering_on(self, shape_object: ShapeObject, atmosphere: bool, extinction: bool) -> None:
        data_source = self.create_data_source(atmosphere)
        scattering_shader = self.create_scattering_shader(
            atmosphere=atmosphere, displacement=not shape_object.is_flat(), extinction=extinction)
        shape_object.set_scattering(data_source, scattering_shader)

    def remove_scattering_on(self, shape_object: ShapeObject) -> None:
        shape_object.remove_scattering()

    def update_scattering(self) -> None:
        if not settings.show_atmospheres:
            return
        for shape_object in self.shape_objects:
            atmosphere = shape_object in self.atmospheres
            self.do_update_scattering(shape_object, atmosphere=atmosphere, extinction=False)
            shape_object.update_shader()
        for shape_object in self.attenuated_objects:
            self.do_update_scattering(shape_object, atmosphere=False, extinction=True)
            shape_object.update_shader()

    def add_shape_object(self, shape_object: ShapeObject, atmosphere: bool = False) -> None:
        if shape_object in self.shape_objects:
            return
        print("Add scattering on", shape_object.get_name())
        self.shape_objects.append(shape_object)
        if shape_object in self.attenuated_objects:
            self.attenuated_objects.remove(shape_object)
        if atmosphere:
            self.atmospheres.add(shape_object)
        self.set_scattering_on(shape_object, atmosphere=atmosphere, extinction=False)

    def remove_shape_object(self, shape_object: ShapeObject) -> None:
        if shape_object in self.shape_objects:
            print("Remove scattering on", shape_object.get_name())
            self.shape_objects.remove(shape_object)
            self.remove_scattering_on(shape_object)
            try:
                del self.atmospheres[shape_object]
            except KeyError:
                pass

    def add_attenuated_object(self, shape_object: ShapeObject) -> None:
        if shape_object is self or shape_object in self.shape_objects or shape_object in self.attenuated_objects:
            return
        print("Apply extinction on", shape_object.owner.get_name(), ':', shape_object.get_name())
        self.attenuated_objects.append(shape_object)
        self.set_scattering_on(shape_object, atmosphere=False, extinction=True)

    def remove_attenuated_object(self, shape_object: ShapeObject) -> None:
        if shape_object in self.attenuated_objects:
            self.attenuated_objects.remove(shape_object)
            self.remove_scattering_on(shape_object)

    def remove_all_attenuated_objects(self) -> None:
        for shape_object in self.attenuated_objects:
            self.remove_scattering_on(shape_object)
            shape_object.update_shader()
        self.attenuated_objects = []

    @abstractmethod
    def do_update_scattering(
            self, shape_object: ShapeObject, atmosphere: bool, extinction: bool) -> None:
        raise NotImplementedError()

    @abstractmethod
    def create_scattering_shader(self, atmosphere: bool, displacement: bool, extinction: bool) -> None:
        raise NotImplementedError()

    @abstractmethod
    def create_data_source(self, atmosphere: bool) -> None:
        raise NotImplementedError()

    def update(self, time, dt):
        pass
