#
# This file is part of Cosmonium.
#
# Copyright (C) 2018-2026 Laurent Deru.
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


from ..objects.systems import Barycenter, StellarSystem
from .objectparser import ObjectYamlParser
from .orbitsparser import OrbitYamlParser
from .rotationsparser import RotationYamlParser
from .schemas.stellarobjects import SystemConfig
from .utilsparser import check_parent
from .yamlparser import YamlModuleParser


class SystemYamlParser(YamlModuleParser):
    def decode(self, data, parent=None):
        name = data.name
        parent_name = data.parent
        star_system = data.star_system
        parent, explicit_parent = check_parent(name, parent, parent_name)
        if parent is None:
            return None
        orbit = OrbitYamlParser.decode(data.orbit, None, parent)
        rotation = RotationYamlParser.decode(data.rotation, None, parent)
        system = StellarSystem(name, star_system=star_system, orbit=orbit, rotation=rotation)
        self.translate_object_names(system.anchor)
        children_data = data.children if data.children else []
        ObjectYamlParser.decode_objects_list(children_data, parent=system)
        if system.children:
            system.set_primary(system.children[0])
        parent.add_child_fast(system)
        return system


class BarycenterYamlParser(YamlModuleParser):
    def decode(self, data, parent=None):
        name = data.name
        parent_name = data.parent
        parent, explicit_parent = check_parent(name, parent, parent_name)
        if parent is None:
            return None
        orbit = OrbitYamlParser.decode(data.orbit, None, parent)
        rotation = RotationYamlParser.decode(data.rotation, None, parent)
        system = Barycenter(name, orbit=orbit, rotation=rotation)
        self.translate_object_names(system.anchor)
        children_data = data.children if data.children else []
        ObjectYamlParser.decode_objects_list(children_data, parent=system)
        parent.add_child_fast(system)
        return system


def register_system_parsers():
    ObjectYamlParser.register_object_parser('system', SystemYamlParser(), model=SystemConfig)
    ObjectYamlParser.register_object_parser('barycenter', BarycenterYamlParser(), model=SystemConfig)
