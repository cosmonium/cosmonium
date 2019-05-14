# -*- coding: utf-8 -*-
from __future__ import print_function
from __future__ import absolute_import

from ..annotations import Constellation
from ..astro.orbits import InfinitePosition
from ..astro import units

from .yamlparser import YamlModuleParser
from .objectparser import ObjectYamlParser
from .utilsparser import hour_angle_decoder, degree_angle_decoder
from . import boundaries_parser

import re

class ConstellationYamlParser(YamlModuleParser):
    @classmethod
    def decode(cls, data):
        constellation = None
        name = data.get('name')
        genitive = data.get('genitive')
        abbr = data.get('abbreviation')
        ra = hour_angle_decoder(data.get('ra'))
        if ra is None:
            print("Invalid ra : '%s'" % data.get('ra'))
            ra = 0
        decl = degree_angle_decoder(data.get('de'))
        if decl is None:
            print("Invalid de : '%s'" % data.get('de'))
            decl = 0
        center = InfinitePosition(right_asc=ra, declination=decl)
        boundaries = 'boundaries/%s.txt' % abbr.lower()
        boundaries = boundaries_parser.load(boundaries, cls.context)
        if boundaries is not None:
            constellation = Constellation(name, center, list(boundaries.values())[0])
        return constellation

ObjectYamlParser.register_object_parser('constellation', ConstellationYamlParser())
