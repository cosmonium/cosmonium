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


from ..astro import units
from ..astro.projection import InfinitePosition
from ..components.annotations.constellation import Constellation
from . import boundariesparser
from .objectparser import ObjectYamlParser
from .schemas.annotations import ConstellationConfig
from .utilsparser import degree_angle_decoder, hour_angle_decoder
from .yamlparser import YamlModuleParser


class ConstellationYamlParser(YamlModuleParser):
    @classmethod
    def decode(cls, data, parent=None):
        constellation = None
        name = cls.translate_name(data.name, context='constellation')
        # genitive = data.genitive
        abbr = data.abbreviation
        ra = hour_angle_decoder(data.ra)
        if ra is None:
            print("Invalid ra : '%s'" % data.ra)
            ra = 0
        decl = degree_angle_decoder(data.de)
        if decl is None:
            print("Invalid de : '%s'" % data.de)
            decl = 0
        center = InfinitePosition(ra * units.Deg, decl * units.Deg)
        boundaries = 'boundaries/%s.txt' % abbr.lower()
        boundaries = boundariesparser.load(boundaries, cls.context)
        if boundaries is not None:
            constellation = Constellation(name, center, list(boundaries.values())[0])
        if parent is not None:
            parent.add_component(constellation)
            return None
        else:
            return constellation


def register_constellation_parsers():
    ObjectYamlParser.register_object_parser('constellation', ConstellationYamlParser(), model=ConstellationConfig)
