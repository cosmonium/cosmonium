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


from copy import copy


class ElementCategory:
    def __init__(self, name, priority):
        self.name = name
        self.priority = priority
        self.elements = {}


class ElementsDB(object):
    def __init__(self, name):
        self.name = name
        self.db_map = {}
        self.db_list = []

    def register_category(self, category_name, priority):
        if category_name in self.db_map:
            return
        category = ElementCategory(category_name, priority)
        self.db_map[category_name] = category
        self.db_list.append(category)
        self.db_list.sort(key=lambda x: x.priority, reverse=True)

    def register_alias(self, category_name, alias):
        category = self.db_map[category_name]
        self.db_map[alias] = category

    def register_element(self, category_name, element_name, element):
        category = self.db_map[category_name]
        category.elements[element_name] = element

    def get(self, name):
        element = None
        if ':' in name:
            (category_name, element_name) = name.split(':')
            if category_name in self.db_map:
                if element_name in self.db_map[category_name].elements:
                    element = self.db_map[category_name].elements[element_name]
                else:
                    print("DB", self.name, ':', "Element", name, "not found in category", category_name)
            else:
                print("DB", self.name, ':', "Category", category_name, "not found")
        else:
            element_name = name
        if element is None:
            for category in self.db_list:
                if element_name in category.elements:
                    element = category.elements[element_name]
                    break
        if element is not None:
            element = copy(element)
            element.frame = copy(element.frame)
        else:
            print("DB", self.name, ':', "Element", name, "not found")
        return element


orbit_elements_db = ElementsDB('orbits')
rotation_elements_db = ElementsDB('rotations')
