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


from ..universe import Universe
from ..annotations import Boundary
from ..astro.projection import InfinitePosition
from ..astro import units
from ..dircontext import defaultDirContext

import sys
import re
import struct
from time import time

def do_load(filepath, universe):
    start = time()
    print("Loading", filepath)
    base.splash.set_text("Loading %s" % filepath)
    data = open(filepath)
    prev_const = None
    points = []
    for line in data.readlines():
        data = re.split(' +', line.rstrip('\r\n').lstrip((' ')))
        if len(data) == 4:
            (ra, decl, const, ignore) = data
            if const != prev_const and prev_const is not None:
                #print("Adding constellation", prev_const)
                boundary = Boundary(prev_const, points)
                universe.add_component(boundary)
                points = []
            prev_const = const
            position = InfinitePosition(float(ra) * units.HourAngle, declination=float(decl) * units.Deg)
            points.append(position)
        else:
            print("Malformed line", data)
    end = time()
    print("Load time:", end - start)

def load(filename, universe, context=defaultDirContext):
    filepath = context.find_data(filename)
    if filepath is not None:
        do_load(filepath, universe)
    else:
        print("File not found", filename)

if __name__ == '__main__':
    if len(sys.argv) == 2:
        universe=Universe(None)
        struct = load(sys.argv[1], universe)
