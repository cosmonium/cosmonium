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


from ..components.annotations.boundary import Boundary
from ..astro.projection import InfinitePosition
from ..astro import units
from ..dircontext import defaultDirContext

import re

def create_line(points, prev_ra, prev_decl, ra, decl):
    if prev_ra is not None:
        delta_ra = ra - prev_ra
        if delta_ra <= -180:
            delta_ra += 360
        if delta_ra >= 180:
            delta_ra -= 360
        count_ra = int(abs(delta_ra)) + 1
        delta_decl = decl - prev_decl
        count_decl = int(abs(delta_decl)) + 1
        count = max(count_ra, count_decl)
        ra_incr = delta_ra / count
        decl_incr = delta_decl / count
        for i in range(count):
            position = InfinitePosition((prev_ra + i * ra_incr) * units.Deg, (prev_decl + i * decl_incr) * units.Deg)
            points.append(position)
    position = InfinitePosition(ra * units.Deg, decl * units.Deg)
    points.append(position)

def do_load(filepath):
    boundaries = {}
    data = open(filepath)
    prev_const = None
    points = []
    prev_ra = None
    prev_decl = None
    first_ra = None
    first_decl = None
    for line in data.readlines():
        line = line.rstrip(' \r\n').lstrip(' ')
        data = re.split('\|', line)
        if len(data) == 3:
            (ra, decl, const) = data
            if const != prev_const and prev_const is not None:
                #print("Adding constellation", prev_const, const)
                create_line(points, prev_ra, prev_decl, first_ra, first_decl)
                boundary = Boundary(prev_const, points)
                boundaries[prev_const] = boundary
                points = []
                prev_ra = None
                prev_decl = None
            prev_const = const
            (hours, mins, secs) = ra.split(' ')
            ra = units.hourMinSec(float(hours), float(mins), float(secs))
            decl = float(decl)
            if prev_ra is None:
                first_ra = ra
                first_decl = decl
            create_line(points, prev_ra, prev_decl, ra, decl)
            prev_ra = ra
            prev_decl = decl
        elif line != '':
            print("Malformed line", data)
    create_line(points, prev_ra, prev_decl, first_ra, first_decl)
    boundary = Boundary(const, points)
    boundaries[const] = boundary
    return boundaries

def load(filename, context=defaultDirContext):
    filepath = context.find_data(filename)
    if filepath is not None:
        return do_load(filepath)
    else:
        print("File not found", filename)
        return None
