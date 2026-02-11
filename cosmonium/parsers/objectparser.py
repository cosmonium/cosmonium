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


from ..components.elements.surface_categories import SurfaceCategory, surfaceCategoryDB
from ..dataattribution import DataAttribution, dataAttributionDB
from .schemas.base import IncludeConfig
from .schemas.misc import AttributionConfig
from .schemas.stellarobjects import UniverseConfig
from .schemas.surface import SurfaceCategoryConfig
from .yamlparser import TypedYamlParser, YamlModuleParser


class ObjectYamlParser(TypedYamlParser):
    """Parser for top-level objects with type-based dispatch."""


class UniverseYamlParser(YamlModuleParser):
    def __init__(self, universe=None):
        YamlModuleParser.__init__(self)
        self.universe = universe

    def set_universe(self, universe):
        self.universe = universe

    def decode(self, data, parent=None):
        ObjectYamlParser.decode_objects_list(data.children, parent=self.universe)


class IncludeYamlParser(YamlModuleParser):
    def decode(self, data, **extra):
        if isinstance(data, str):
            filename = data
        else:
            filename = data.include

        parser = ObjectYamlParser()
        body = parser.load_and_parse(filename, **extra)
        return body


class DataAttributionYamlParser(YamlModuleParser):
    @classmethod
    def decode(cls, data, attribution_id=None):
        if attribution_id is None:
            attribution_id = data.id
        name = data.name
        copyright = data.copyright
        license = data.license
        url = data.url
        attribution = DataAttribution(name, copyright, license, url)
        dataAttributionDB.add_attribution(attribution_id, attribution)
        return None


class DataAttributionsListYamlParser(YamlModuleParser):
    @classmethod
    def decode(cls, data, parent=None):
        # data is a dict of attribution_id -> attribution data
        # This parser doesn't validate individual attributions, just passes them through
        attributions = data.get('attributions', {})
        for attribution_id, attribution_data in attributions.items():
            validated_attribution = AttributionConfig.model_validate(attribution_data)
            DataAttributionYamlParser.decode(validated_attribution, attribution_id)
        return None


class SurfaceCategoryYamlParser(YamlModuleParser):
    @classmethod
    def decode(cls, data):
        category = SurfaceCategory(data.name)
        surfaceCategoryDB.add(category)
        return None


universeYamlParser = UniverseYamlParser()


def register_object_parsers():
    ObjectYamlParser.register_object_parser('universe', universeYamlParser, UniverseConfig)
    ObjectYamlParser.register_object_parser('include', IncludeYamlParser(), IncludeConfig)
    ObjectYamlParser.register_object_parser('attributions', DataAttributionsListYamlParser())
    ObjectYamlParser.register_object_parser('attribution', DataAttributionYamlParser(), model=AttributionConfig)
    ObjectYamlParser.register_object_parser(
        'surface-category', SurfaceCategoryYamlParser(), model=SurfaceCategoryConfig
    )
