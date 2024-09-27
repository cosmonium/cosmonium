#
# This file is part of Cosmonium.
#
# Copyright (C) 2018-2024 Laurent Deru.
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

from functools import wraps
from panda3d.core import PStatCollector


custom_collectors = {}


def named_pstat(name):
    def pstat(func):
        collectorName = "%s:%s" % ('Engine', name)
        if collectorName not in custom_collectors.keys():
            custom_collectors[collectorName] = PStatCollector(collectorName)
        pstat = custom_collectors[collectorName]

        @wraps(func)
        def doPstat(*args, **kargs):
            pstat.start()
            returned = func(*args, **kargs)
            pstat.stop()
            return returned

        return doPstat

    return pstat


def pstat(func):
    return named_pstat(func.__name__)(func)


def levelpstat(name, category='Engine'):
    collectorName = category + ':' + name
    if collectorName not in custom_collectors.keys():
        custom_collectors[collectorName] = PStatCollector(collectorName)
    pstat = custom_collectors[collectorName]
    return pstat
