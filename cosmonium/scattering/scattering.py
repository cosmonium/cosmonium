#
# This file is part of Cosmonium.
#
# Copyright (C) 2018-2024 Laurent Deru.
#
# Cosmonium is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Cosmonium is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Cosmonium.  If not, see <https://www.gnu.org/licenses/>.
#


from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional

from .. import settings
from ..parameters import ParametersGroup

if TYPE_CHECKING:
    from ..entities.entity import Entity


class ScatteringBase(ABC):

    def __init__(self):
        self.atmospheres: set[Entity] = set()
        self.entities: list[Entity] = []
        self.attenuated_objects: list[Entity] = []
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
        for entity in self.entities:
            atmosphere = entity in self.atmospheres
            self.set_scattering_on(entity, atmosphere=atmosphere, extinction=False)
        for entity in self.attenuated_objects:
            self.set_scattering_on(entity, atmosphere=False, extinction=True)

    def disable_scattering(self) -> None:
        for entity in self.entities:
            self.remove_scattering_on(entity)
        for entity in self.attenuated_objects:
            self.remove_scattering_on(entity)

    def set_scattering_on(self, entity: Entity, atmosphere: bool, extinction: bool) -> None:
        data_source = self.create_data_source(atmosphere)
        scattering_shader = self.create_scattering_shader(
            atmosphere=atmosphere, displacement=not entity.is_flat(), extinction=extinction
        )
        entity.set_scattering(data_source, scattering_shader)

    def remove_scattering_on(self, entity: Entity) -> None:
        entity.remove_scattering()

    def update_scattering(self) -> None:
        if not settings.show_atmospheres:
            return
        for entity in self.entities:
            atmosphere = entity in self.atmospheres
            self.do_update_scattering(entity, atmosphere=atmosphere, extinction=False)
            entity.update_shader()
        for entity in self.attenuated_objects:
            self.do_update_scattering(entity, atmosphere=False, extinction=True)
            entity.update_shader()

    def add_shape_object(self, entity: Entity, atmosphere: bool = False) -> None:
        if entity in self.entities:
            return
        print("Add scattering on", entity.get_name())
        self.entities.append(entity)
        if entity in self.attenuated_objects:
            self.attenuated_objects.remove(entity)
        if atmosphere:
            self.atmospheres.add(entity)
        self.set_scattering_on(entity, atmosphere=atmosphere, extinction=False)

    def remove_shape_object(self, entity: Entity) -> None:
        if entity in self.entities:
            print("Remove scattering on", entity.get_name())
            self.entities.remove(entity)
            self.remove_scattering_on(entity)
            try:
                del self.atmospheres[entity]
            except KeyError:
                pass

    def add_attenuated_object(self, entity: Entity) -> None:
        if entity is self or entity in self.entities or entity in self.attenuated_objects:
            return
        print("Apply extinction on", entity.owner.get_name(), ':', entity.get_name())
        self.attenuated_objects.append(entity)
        self.set_scattering_on(entity, atmosphere=False, extinction=True)

    def remove_attenuated_object(self, entity: Entity) -> None:
        if entity in self.attenuated_objects:
            self.attenuated_objects.remove(entity)
            self.remove_scattering_on(entity)

    def remove_all_attenuated_objects(self) -> None:
        for entity in self.attenuated_objects:
            self.remove_scattering_on(entity)
            entity.update_shader()
        self.attenuated_objects = []

    @abstractmethod
    def do_update_scattering(self, entity: Entity, atmosphere: bool, extinction: bool) -> None:
        raise NotImplementedError()

    @abstractmethod
    def create_scattering_shader(self, atmosphere: bool, displacement: bool, extinction: bool) -> None:
        raise NotImplementedError()

    @abstractmethod
    def create_data_source(self, atmosphere: bool) -> None:
        raise NotImplementedError()

    def update_user_parameters(self):
        self.update_scattering()

    def get_user_parameters(self):
        return ParametersGroup("Scattering")

    def update(self, time, dt):
        pass
