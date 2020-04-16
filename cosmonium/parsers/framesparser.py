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

from ..astro.frame import J2000EclipticReferenceFrame, J2000EquatorialReferenceFrame, EquatorialReferenceFrame, SynchroneReferenceFrame
from ..astro.frame import SurfaceReferenceFrame, CelestialReferenceFrame
from ..astro.frame import frames_db

from .yamlparser import YamlModuleParser
from .objectparser import ObjectYamlParser
from .utilsparser import AngleUnitsYamlParser

class FrameYamlParser(YamlModuleParser):
    @classmethod
    def decode_equatorial(cls, data):
        ra = data.get("ra", 0.0)
        de = data.get("de", 0.0)
        node = data.get("longitude", 0.0)
        return CelestialReferenceFrame(right_asc=ra, declination=de, longitude_at_node=node)

    @classmethod
    def decode_mean_equatorial(cls, data):
        return EquatorialReferenceFrame()

    @classmethod
    def decode_surface_frame(self, data):
        long = data.get('long', 0.0)
        long_units = AngleUnitsYamlParser.decode(data.get('long-units', 'Deg'))
        lat = data.get('lat', 0.0)
        lat_units = AngleUnitsYamlParser.decode(data.get('lat-units', 'Deg'))
        return SurfaceReferenceFrame(long * long_units, lat * lat_units)

    @classmethod
    def decode(self, data):
        if data is None: return J2000EclipticReferenceFrame()
        (object_type, parameters) = self.get_type_and_data(data)
        object_type = object_type.lower()
        if object_type == 'j2000ecliptic':
            return J2000EclipticReferenceFrame()
        elif object_type == 'j2000equatorial':
            return J2000EquatorialReferenceFrame()
        elif object_type == 'fixed':
            return SynchroneReferenceFrame()
        elif object_type == 'surface':
            return self.decode_surface_frame(data)
        elif object_type == 'equatorial':
            return self.decode_equatorial(data)
        elif object_type == 'mean-equatorial':
            return self.decode_mean_equatorial(data)
        else:
            return frames_db.get(data)

class NamedFrameYamlParser(YamlModuleParser):
    @classmethod
    def decode(self, data):
        name = data.get('name')
        if name is None: return None
        frame = FrameYamlParser.decode(data)
        frames_db.register_frame(name, frame)
        return None

ObjectYamlParser.register_object_parser('frame', NamedFrameYamlParser())
