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

from ..astro import units
from ..catalogs import objectsDB

from .yamlparser import YamlModuleParser

import re

hour_angle_regex= re.compile('^(\d+)\:(\d+)\'(\d+\.?\d*)\"$')
degree_angle_regex= re.compile(u'^([-+]?\d+)[d°](\d+)\'(\d+\.?\d*)\"$')

def check_parent(name, parent, parent_name):
    explicit_parent = False
    if parent is not None:
        if parent_name is not None:
            print("Ignoring parent for %s" % name)
    else:
        if parent_name is not None:
            explicit_parent = True
            parent = objectsDB.get(parent_name)
            if parent is not None:
                parent = parent.get_or_create_system()
            else:
                print("ERROR: Parent '%s' of '%s' not found" % (parent_name, name))
    if parent is None:
        print("Object %s has no parent" % name)
    return (parent, explicit_parent)

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
    translation = { 'm': units.m,
                    'km': units.Km,
                    'au': units.AU,
                    'ly': units.Ly,
                    'pc': units.Parsec,
                    'kpc': units.KParsec,
                    'mpc': units.MParsec,
                    'gpc': units.GParsec,
                   }
    @classmethod
    def decode(self, data, default=None):
        if data is None:
            return default
        else:
            return DistanceUnitsYamlParser.translation.get(data.lower(), default)

class TimeUnitsYamlParser(YamlModuleParser):
    translation = { 'sec': units.Sec,
                    'min': units.Min,
                    'hour': units.Hour,
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

class AngleSpeedUnitsYamlParser(YamlModuleParser):
    translation = { 'deg/day': units.Deg_Per_Day
                   }
    @classmethod
    def decode(self, data, default=None):
        if data is None:
            return default
        else:
            return AngleSpeedUnitsYamlParser.translation.get(data.lower(), default)
