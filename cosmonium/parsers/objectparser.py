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


from ..components.elements.surfaces import surfaceCategoryDB, SurfaceCategory
from ..dataattribution import DataAttribution, dataAttributionDB

from .yamlparser import YamlModuleParser

class ObjectYamlParser(YamlModuleParser):
    parsers = {}

    @classmethod
    def register_object_parser(cls, name, parser):
        cls.parsers[name] = parser

    @classmethod
    def decode_object(cls, object_type, parameters, parent=None):
        result = None
        if object_type in cls.parsers:
            if parent is not None:
                result = cls.parsers[object_type].decode(parameters, parent)
            else:
                result = cls.parsers[object_type].decode(parameters)
        else:
            print("Unknown object type", object_type)
        return result

    @classmethod
    def decode_object_dict(cls, data, parent=None):
        (object_type, parameters) = cls.get_type_and_data(data)
        if parent is not None:
            return cls.decode_object(object_type, parameters, parent)
        else:
            return cls.decode_object(object_type, parameters)

    @classmethod
    def decode_objects_list(cls, data, parent=None, merge_sub=False):
        objects = []
        for entry in data:
            parsed_data = cls.decode_object_dict(entry, parent)
            if parsed_data is not None:
                if merge_sub and isinstance(parsed_data, list):
                    for sub in parsed_data:
                        if sub is not None:
                            objects.append(sub)
                else:
                    objects.append(parsed_data)
        return objects

    @classmethod
    def decode(cls, data, parent=None):
        if isinstance(data, list):
            return cls.decode_objects_list(data, parent, merge_sub=True)
        else:
            return cls.decode_object_dict(data, parent)

class UniverseYamlParser(YamlModuleParser):
    def __init__(self, universe=None):
        YamlModuleParser.__init__(self)
        self.universe = universe

    def set_universe(self, universe):
        self.universe = universe

    def decode(self, data, parent=None):
        children = ObjectYamlParser.decode(data.get('children', []), self.universe)

class IncludeYamlParser(YamlModuleParser):
    def decode(self, data, parent=None):
        if isinstance(data, str):
            filename = data
        else:
            filename = data.get('include')
        parser = ObjectYamlParser()
        body = parser.load_and_parse(filename, parent)
        return body

class DataAttributionYamlParser(YamlModuleParser):
    @classmethod
    def decode(self, data, attribution_id=None):
        if attribution_id is None:
            attribution_id = data.get('id')
        name = data.get('name')
        copyright = data.get('copyright', None)
        license = data.get('license', None)
        url = data.get('url', None)
        attribution = DataAttribution(name, copyright, license, url)
        dataAttributionDB.add_attribution(attribution_id, attribution)
        return None

class DataAttributionsListYamlParser(YamlModuleParser):
    @classmethod
    def decode(self, data, parent=None):
        for (attribution_id, attribution_data) in data.items():
            DataAttributionYamlParser.decode(attribution_data, attribution_id)
        return None

class SurfaceCategoryYamlParser(YamlModuleParser):
    @classmethod
    def decode(self, data):
        name = data.get('name')
        category = SurfaceCategory(name)
        surfaceCategoryDB.add(category)
        return None

universeYamlParser = UniverseYamlParser()
ObjectYamlParser.register_object_parser('universe', universeYamlParser)
ObjectYamlParser.register_object_parser('include', IncludeYamlParser())
ObjectYamlParser.register_object_parser('attributions', DataAttributionsListYamlParser())
ObjectYamlParser.register_object_parser('attribution', DataAttributionYamlParser())
ObjectYamlParser.register_object_parser('surface-category', SurfaceCategoryYamlParser())
