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


from ..astro.orbits import FixedPosition
from ..catalogs import objectsDB
from ..components.annotations.asterism import Asterism
from .objectparser import ObjectYamlParser
from .schemas.annotations import AsterismConfig
from .yamlparser import YamlModuleParser


class AsterismYamlParser(YamlModuleParser):
    @classmethod
    def decode(cls, data, parent=None):
        segments = []
        for text_segment in data.segments:
            segment = []
            for star_name in text_segment:
                star = objectsDB.get_body(star_name)
                if star is not None:
                    if star.parent.anchor.has_system() and not isinstance(star.anchor.orbit, FixedPosition):
                        star = star.parent
                    segment.append(star.anchor)
                else:
                    print("Could not find star", star_name)
            segments.append(segment)
        asterism = Asterism(data.name)
        asterism.set_segments_list(segments)
        if parent is not None:
            parent.add_component(asterism)
            return None
        else:
            return asterism


def register_asterism_parsers():
    ObjectYamlParser.register_object_parser('asterism', AsterismYamlParser(), model=AsterismConfig)
