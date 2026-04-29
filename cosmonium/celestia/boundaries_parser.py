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

"""Parser for Celestia constellation boundary data files.

Reads a whitespace-delimited boundary file and creates :class:`~Boundary`
objects for each constellation.
"""


import builtins
import logging
import re
import sys
from time import time

from ..astro.projection import InfinitePosition
from ..astro import units
from ..components.annotations.boundary import Boundary
from ..dircontext import defaultDirContext
from ..objects.universe import Universe

logger = logging.getLogger('boundaries')


def do_load(filepath, universe):
    start = time()
    logger.info("Loading %s", filepath)
    builtins.base.splash.set_text("Loading %s" % filepath)
    data = open(filepath)
    prev_const = None
    points = []
    for line in data.readlines():
        data = re.split(r'\s+', line.rstrip('\r\n').lstrip(' '))
        if len(data) == 4:
            (ra, decl, const, ignore) = data
            if const != prev_const and prev_const is not None:
                # print("Adding constellation", prev_const)
                boundary = Boundary(prev_const, points)
                universe.add_component(boundary)
                points = []
            prev_const = const
            position = InfinitePosition(float(ra) * units.HourAngle, declination=float(decl) * units.Deg)
            points.append(position)
        else:
            logger.warning("Malformed line: %s", data)
    end = time()
    logger.debug("Load time: %.3fs", end - start)


def load(filename, universe, context=defaultDirContext):
    filepath = context.find_data(filename)
    if filepath is not None:
        do_load(filepath, universe)
    else:
        logger.warning("File not found: %s", filename)


if __name__ == '__main__':
    if len(sys.argv) == 2:
        universe = Universe(None)
        load(sys.argv[1], universe)
