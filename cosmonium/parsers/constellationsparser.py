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

from ..annotations import Constellation
from ..astro.orbits import InfinitePosition
from ..astro import units

from .yamlparser import YamlModuleParser
from .objectparser import ObjectYamlParser
from .utilsparser import hour_angle_decoder, degree_angle_decoder
from . import boundariesparser

import re

class ConstellationYamlParser(YamlModuleParser):
    @classmethod
    def decode(cls, data, parent=None):
        constellation = None
        name = cls.translate_name(data.get('name'), context='constellation')
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
        boundaries = boundariesparser.load(boundaries, cls.context)
        if boundaries is not None:
            constellation = Constellation(name, center, list(boundaries.values())[0])
        if parent is not None:
            parent.add_component(constellation)
            return None
        else:
            return constellation

ObjectYamlParser.register_object_parser('constellation', ConstellationYamlParser())
