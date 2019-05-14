from __future__ import print_function
from __future__ import absolute_import

from copy import deepcopy

class ElementCategory():
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
        category = ElementCategory(category_name, priority)
        self.db_map[category_name] = category
        self.db_list.append(category)
        self.db_list.sort(key=lambda x: x.priority, reverse=True)

    def register_element(self, category_name, element_name, element):
        category = self.db_map[category_name]
        category.elements[element_name] = element

    def get(self, name):
        if ':' in name:
            (category_name, element_name) = name.split(':')
            if category_name in self.db_map:
                if element_name in self.db_map[category_name].elements:
                    return deepcopy(self.db_map[category_name].elements[element_name])
                else:
                    print("DB", self.name, ':', "Element", name, "not found in category", category_name)
            else:
                print("DB", self.name, ':', "Category", category_name, "not found")
        else:
            element_name = name
        for category in self.db_list:
            if element_name in category.elements:
                return deepcopy(category.elements[element_name])
        print("DB", self.name, ':', "Element", name, "not found")
            
orbit_elements_db = ElementsDB('orbits')
rotation_elements_db = ElementsDB('rotations')
