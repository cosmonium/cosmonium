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


from abc import ABC, abstractmethod

from ..controllers.controllers import BodyController


class PhysicsBase(ABC):

    @abstractmethod
    def enable(self):
        raise NotImplementedError()

    @abstractmethod
    def set_gravity(self, gravity):
        raise NotImplementedError()

    @abstractmethod
    def disable(self):
        raise NotImplementedError()

    @abstractmethod
    def add_object(self, entity, physics_instance):
        raise NotImplementedError()

    @abstractmethod
    def add_objects(self, entity, physics_instances):
        raise NotImplementedError()

    @abstractmethod
    def add_controller(self, entity, instance, physics_node):
        raise NotImplementedError()

    @abstractmethod
    def remove_object(self, entity, physics_instance):
        raise NotImplementedError()

    @abstractmethod
    def remove_controller(self, entity, physics_instance):
        raise NotImplementedError()

    @abstractmethod
    def update(self, time, dt):
        raise NotImplementedError()

    @abstractmethod
    def ls(self):
        raise NotImplementedError()

    @abstractmethod
    def create_capsule_shape_for(self, model):
        raise NotImplementedError()

    @abstractmethod
    def create_controller_for(self, physics_shape):
        raise NotImplementedError()

    @abstractmethod
    def build_from_geom(self, instance):
        raise NotImplementedError()

    @abstractmethod
    def set_mass(self, physics_instance, mass):
        raise NotImplementedError()


class PhysicsController(BodyController):
    pass
