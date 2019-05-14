# -*- coding: utf-8 -*-
from __future__ import print_function
from __future__ import absolute_import

from ..annotations import Asterism
from ..astro.orbits import FixedPosition
from ..catalogs import objectsDB

from .yamlparser import YamlModuleParser
from .objectparser import ObjectYamlParser

class AsterismYamlParser(YamlModuleParser):
    @classmethod
    def decode(cls, data):
        name = data.get('name', "dummy")
        text_segments = data.get('segments', [])
        segments = []
        for text_segment in text_segments:
            segment = []
            for star_name in text_segment:
                star = objectsDB.get(star_name)
                if star is not None:
                    if not isinstance(star.orbit, FixedPosition):
                        star = star.parent
                    segment.append(star)
                else:
                    print("Could not find star", star_name)
            segments.append(segment)
        asterism = Asterism(name)
        asterism.set_segments_list(segments)
        return asterism

ObjectYamlParser.register_object_parser('asterism', AsterismYamlParser())
