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


from ..plugins import moduleLoader

from .objectparser import ObjectYamlParser
from .yamlparser import YamlModuleParser


class AddonYamlParser(YamlModuleParser):
    @classmethod
    def decode(self, data, parent=None):
        if isinstance(data, str):
            data = {'file': data}
        # name = data.get('name', None)
        filename = data.get('file')
        module_path = self.context.find_module(filename)
        if module_path is not None:
            module = moduleLoader.load_module(module_path)
            plugin = module.CosmoniumPlugin()
            plugin.init(self.app)
        else:
            print("ERROR: Could not find '{}'".format(filename))
        return None


def register_plugin_parsers():
    ObjectYamlParser.register_object_parser('plugin', AddonYamlParser())
