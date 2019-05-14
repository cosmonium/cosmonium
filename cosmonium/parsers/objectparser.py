from __future__ import print_function
from __future__ import absolute_import

from ..bodies import StellarObject
from ..surfaces import surfaceCategoryDB, SurfaceCategory
from ..datasource import DataSource, dataSourceDB

from .yamlparser import YamlModuleParser

class ObjectYamlParser(YamlModuleParser):
    parsers = {}

    @classmethod
    def register_object_parser(cls, name, parser):
        cls.parsers[name] = parser

    @classmethod
    def decode_object(cls, object_type, parameters):
        result = None
        if object_type in cls.parsers:
            result = cls.parsers[object_type].decode(parameters)
        else:
            print("Unknown object type", object_type)
        return result

    @classmethod
    def decode_object_dict(cls, data):
        (object_type, parameters) = cls.get_type_and_data(data)
        return cls.decode_object(object_type, parameters)

    @classmethod
    def decode_objects_list(cls, data, merge_sub=False):
        objects = []
        for entry in data:
            parsed_data = cls.decode_object_dict(entry)
            if parsed_data is not None:
                if merge_sub and isinstance(parsed_data, list):
                    for sub in parsed_data:
                        if sub is not None:
                            objects.append(sub)
                else:
                    objects.append(parsed_data)
        return objects

    @classmethod
    def decode(cls, data):
        if isinstance(data, list):
            return cls.decode_objects_list(data, merge_sub=True)
        else:
            return cls.decode_object_dict(data)

class UniverseYamlParser(YamlModuleParser):
    def __init__(self, universe):
        YamlModuleParser.__init__(self)
        self.universe = universe

    def decode(self, data):
        children = ObjectYamlParser.decode(data)
        if not isinstance(children, list):
            children = [children]
        for child in children:
            if child is None:
                pass
            elif isinstance(child, StellarObject):
                self.universe.add_child_fast(child)
            else:
                self.universe.add_component(child)

class IncludeYamlParser(YamlModuleParser):
    def decode(self, data):
        if isinstance(data, str):
            filename = data
        else:
            filename = data.get('include')
        parser = ObjectYamlParser()
        body = parser.load_and_parse(filename)
        return body

class DataSourceYamlParser(YamlModuleParser):
    @classmethod
    def decode_source(self, data):
        name = data.get('name')
        copyright = data.get('copyright', None)
        license = data.get('license', None)
        url = data.get('url', None)
        source = DataSource(name, copyright, license, url)
        return source

    @classmethod
    def decode(self, data):
        for (source_id, source_data) in data.items():
            source = self.decode_source(source_data)
            dataSourceDB.add_source(source_id, source)
        return None

class SurfaceCategoryYamlParser(YamlModuleParser):
    @classmethod
    def decode(self, data):
        name = data.get('name')
        category = SurfaceCategory(name)
        surfaceCategoryDB.add(category)
        return None

ObjectYamlParser.register_object_parser('include', IncludeYamlParser())
ObjectYamlParser.register_object_parser('data-sources', DataSourceYamlParser())
ObjectYamlParser.register_object_parser('surface-category', SurfaceCategoryYamlParser())
