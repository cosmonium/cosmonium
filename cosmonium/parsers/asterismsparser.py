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

from __future__ import absolute_import

from ..annotations import Asterism
from ..astro.orbits import FixedPosition
from ..catalogs import objectsDB

from .yamlparser import YamlModuleParser
from .objectparser import ObjectYamlParser

class AsterismYamlParser(YamlModuleParser):
    @classmethod
    def decode(cls, data, parent=None):
        name = data.get('name', "dummy")
        text_segments = data.get('segments', [])
        segments = []
        for text_segment in text_segments:
            segment = []
            for star_name in text_segment:
                star = objectsDB.get(star_name)
                if star is not None:
                    if star.parent.system is not None and not isinstance(star.anchor.orbit, FixedPosition):
                        star = star.parent
                    segment.append(star)
                else:
                    print("Could not find star", star_name)
            segments.append(segment)
        asterism = Asterism(name)
        asterism.set_segments_list(segments)
        if parent is not None:
            parent.add_component(asterism)
            return None
        else:
            return asterism

ObjectYamlParser.register_object_parser('asterism', AsterismYamlParser())
