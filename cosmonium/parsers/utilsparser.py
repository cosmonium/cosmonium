# -*- coding: utf-8 -*-
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

from ..astro.frame import J2000EclipticReferenceFrame, J2000EquatorialReferenceFrame, EquatorialReferenceFrame
from ..astro.frame import CelestialReferenceFrame
from ..astro.frame import JupiterReferenceFrame, UranusReferenceFrame, PlutoReferenceFrame
from ..astro import units

from .yamlparser import YamlModuleParser

import re

hour_angle_regex= re.compile('^(\d+)\:(\d+)\'(\d+\.?\d*)\"$')
degree_angle_regex= re.compile(u'^([-+]?\d+)[d°](\d+)\'(\d+\.?\d*)\"$')

def hour_angle_decoder(text):
    if text is None: return None
    angle = None
    m = hour_angle_regex.search(text)
    if m is not None:
        hours = float(m.group(1))
        mins = float(m.group(2))
        secs = float(m.group(3))
        angle = units.hourMinSec(hours, mins, secs)
    return angle

def degree_angle_decoder(text):
    if text is None: return None
    angle = None
    m = degree_angle_regex.search(text)
    if m is not None:
        degrees = float(m.group(1))
        mins = float(m.group(2))
        secs = float(m.group(3))
        angle = units.degMinSec(degrees, mins, secs)
    return angle

class DistanceUnitsYamlParser(YamlModuleParser):
    translation = { 'km': units.Km,
                    'au': units.AU,
                    'ly': units.Ly,
                    'pc': units.Parsec,
                   }
    @classmethod
    def decode(self, data, default=None):
        if data is None:
            return default
        else:
            return DistanceUnitsYamlParser.translation.get(data.lower(), default)

class TimeUnitsYamlParser(YamlModuleParser):
    translation = { 'hour': units.Hour,
                    'day': units.Day,
                    'year': units.JYear,
                   }
    @classmethod
    def decode(self, data, default=None):
        if data is None:
            return default
        else:
            return TimeUnitsYamlParser.translation.get(data.lower(), default)

class AngleUnitsYamlParser(YamlModuleParser):
    translation = { 'deg': units.Deg,
                    'hour': units.HourAngle,
                    'rad': units.Rad
                   }
    @classmethod
    def decode(self, data, default=None):
        if data is None:
            return default
        else:
            return AngleUnitsYamlParser.translation.get(data.lower(), default)

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
    def decode(self, data):
        if data is None: return J2000EclipticReferenceFrame()
        (object_type, parameters) = self.get_type_and_data(data)
        object_type = object_type.lower()
        if object_type == 'j2000ecliptic':
            return J2000EclipticReferenceFrame()
        elif object_type == 'j2000equatorial':
            return J2000EquatorialReferenceFrame()
        elif object_type == 'equatorial':
            return self.decode_equatorial(data)
        elif object_type == 'mean-equatorial':
            return self.decode_mean_equatorial(data)
        elif object_type == 'iau:jupiter':
            return JupiterReferenceFrame()
        elif object_type == 'iau:uranus':
            return UranusReferenceFrame()
        elif object_type == 'iau:pluto':
            return PlutoReferenceFrame()
        else:
            print("Unknown reference frame", data)
            return None
