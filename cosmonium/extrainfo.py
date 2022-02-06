#
#This file is part of Cosmonium.
#
#Copyright (C) 2018-2022 Laurent Deru.
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


from .objects.systems import SimpleSystem

import re

from urllib import parse as urlquote

starts_with_digit = re.compile("^\d")

class ExtraInfo(object):
    def __init__(self):
        pass

    def get_url_for(self, body):
        return None

class WikipediaExtraInfo(object):
    url_prefix = "http://en.m.wikipedia.org/wiki/"

    def get_name(self):
        return "Wikipedia"

    def get_url_for(self, body):
        if isinstance(body, SimpleSystem):
            body = body.primary
        name = urlquote.quote(body.get_name())
        if body.body_class in ['planet']:
            return self.url_prefix + "%s_(planet)" % name
        if body.body_class in ['dwarfplanet']:
            if starts_with_digit.match(name):
                return self.url_prefix + "%s" % name
            else:
                return self.url_prefix + "%s_(dwarf_planet)" % name
        if body.body_class in ['moon', 'dwarfmoon']:
            return self.url_prefix + "%s_(moon)" % name
        if body.body_class in ['asteroid']:
            if starts_with_digit.match(name):
                return self.url_prefix + "%s" % name
            else:
                return self.url_prefix + "%s_(asteroid)" % name
        if body.body_class in ['comet', 'interstellar']:
            return self.url_prefix + "%s" % name
        return self.url_prefix + "%s" % name

class SimbadExtraInfo(object):
    url_prefix = "http://simbad.u-strasbg.fr/simbad/sim-id?NbIdent=1&Ident="

    def get_name(self):
        return "Simbad"

    def get_url_for(self, body):
        if isinstance(body, SimpleSystem):
            body = body.primary
        name = urlquote.quote(body.get_name())
        if body.body_class in ['star']:
            return self.url_prefix + name
        return None

class MpcExtraInfo(object):
    url_prefix = "https://www.minorplanetcenter.net/db_search/show_object?object_id="

    def get_name(self):
        return "Minor Planet Center"

    def get_url_for(self, body):
        if isinstance(body, SimpleSystem):
            body = body.primary
        name = body.get_name()
        if '/' in name:
            name = name.split('/')[0]
        name = urlquote.quote(name)
        if body.body_class in ['dwarfplanet', 'asteroid', 'comet', 'interstellar']:
            return self.url_prefix + name
        return None

extra_info = [WikipediaExtraInfo(),  SimbadExtraInfo(), MpcExtraInfo()]