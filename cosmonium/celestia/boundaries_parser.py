from __future__ import print_function
from __future__ import absolute_import

from ..universe import Universe
from ..annotations import Boundary
from ..astro.orbits import InfinitePosition
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
            position = InfinitePosition(right_asc=float(ra), right_asc_unit=units.HourAngle, declination=float(decl))
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
