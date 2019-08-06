from __future__ import print_function
from __future__ import absolute_import

from ..annotations import Boundary
from ..astro.orbits import InfinitePosition
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
            position = InfinitePosition(right_asc=prev_ra + i * ra_incr, declination=prev_decl + i * decl_incr)
            points.append(position)
    position = InfinitePosition(right_asc=ra, declination=decl)
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
