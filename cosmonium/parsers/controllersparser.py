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

from ..catalogs import objectsDB
from ..plugins import moduleLoader

from .yamlparser import YamlModuleParser
from .objectparser import ObjectYamlParser

class ControllerYamlParser(YamlModuleParser):
    @classmethod
    def decode(self, data):
        name = data.get('name')
        filename = data.get('file')
        module_path = self.context.find_module(filename)
        module = moduleLoader.load_module(module_path)
        controller = module.ControllerClass
        return controller

class StandaloneControllerYamlParser(YamlModuleParser):
    @classmethod
    def decode(self, data):
        name = data.get('name', None)
        body_name = data.get('body')
        body = objectsDB.get(body_name)
        if body is None:
            print("ERROR: Parent '%s' of controller '%s' not found" % (body_name, name))
            return None
        controller_class = ControllerYamlParser.decode(data)
        controller = controller_class(body)
        self.app.add_controller(controller)
        return None

ObjectYamlParser.register_object_parser('controller', StandaloneControllerYamlParser())
