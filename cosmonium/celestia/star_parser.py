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


import builtins
import io
from panda3d.core import LVector3d
import re
import struct
import sys
from time import time

from ..astro.astro import calc_position
from ..astro.spectraltype import spectralTypeStringDecoder, spectralTypeIntDecoder
from ..astro.orbits import AbsoluteFixedPosition
from ..astro.rotations import UnknownRotation
from ..astro.frame import J2000BarycentricEclipticReferenceFrame, AbsoluteReferenceFrame
from ..astro.astro import app_to_abs_mag
from ..astro import bayer
from ..astro import units
from ..dircontext import defaultDirContext
from ..objects.star import Star
from ..objects.universe import Universe

from .bodies import celestiaStarSurfaceFactory


def parse_line(line, names, universe):
    data = re.split(' +', line.rstrip('\r\n'))
    if len(data) == 6:
        (catNo, ra, decl, distance, app_magnitude, spectral_type) = data
        catNo = int(catNo)
        if catNo in names:
            name = names[catNo]
        else:
            name = "HIP %d" % catNo
        position = calc_position(float(ra) * units.Deg, float(decl) * units.Deg, distance * units.Ly)
        frame = AbsoluteReferenceFrame()  # TDODO: This should be J2000BarycentricEclipticReferenceFrame
        orbit = AbsoluteFixedPosition(absolute_reference_point=position, frame=frame)
        abs_magnitude = app_to_abs_mag(float(app_magnitude), float(distance) * units.KmPerLy)
        star = Star(
            name,
            source_names=[],
            radius=None,
            surface_factory=celestiaStarSurfaceFactory,
            spectral_type=spectralTypeStringDecoder.decode(spectral_type),
            abs_magnitude=abs_magnitude,
            orbit=orbit,
            rotation=UnknownRotation(),
        )
        universe.add_child_fast(star)
    else:
        print("Malformed line", data)


def do_load_text(filepath, names, universe):
    start = time()
    print("Loading", filepath)
    builtins.base.splash.set_text("Loading %s" % filepath)
    data = open(filepath)
    data.readline()
    for line in data.readlines():
        parse_line(line, names, universe)
    end = time()
    print("Load time:", end - start)


def load_text(filename, names, universe, context=defaultDirContext):
    filepath = context.find_data(filename)
    if filepath is not None:
        return do_load_text(filepath, names, universe)
    else:
        print("File not found", filename)
        return {}


def do_load_bin(filepath, names, universe):
    start = time()
    print("Loading", filepath)
    builtins.base.splash.set_text("Loading %s" % filepath)
    data = open(filepath, 'rb')
    field = data.read(8 + 2 + 4)
    header, version, count = struct.unpack("<8shi", field)
    if not header == b"CELSTARS":
        print("Invalid header", header)
        return
    if not version == 0x0100:
        print("Invalid version", version)
        return
    print("Found", count, "stars")
    fmt = "<ifffhh"
    size = struct.calcsize(fmt)
    for i in range(count):
        fields = data.read(size)
        catNo, x, y, z, abs_magnitude, spectral_type = struct.unpack(fmt, fields)
        if catNo in names:
            name = names[catNo]
        else:
            name = "HIP %d" % catNo
        position = LVector3d(x * units.Ly, -z * units.Ly, y * units.Ly)
        orbit = AbsoluteFixedPosition(
            absolute_reference_point=position, frame=J2000BarycentricEclipticReferenceFrame()
        )
        star = Star(
            name,
            source_names=[],
            surface_factory=celestiaStarSurfaceFactory,
            spectral_type=spectralTypeIntDecoder.decode(spectral_type),
            abs_magnitude=abs_magnitude / 256.0,
            orbit=orbit,
            rotation=UnknownRotation(),
        )
        universe.add_child_fast(star)
    end = time()
    print("Load time:", end - start)


def load_bin(filename, names, universe, context=defaultDirContext):
    filepath = context.find_data(filename)
    if filepath is not None:
        return do_load_bin(filepath, names, universe)
    else:
        print("File not found", filename)
        return {}


def parse_line_name(line):
    data = re.split(':', line.rstrip('\r\n'))
    catNo = int(data[0])
    names = data[1:]
    names.append("HIP %d" % catNo)
    return (catNo, names)


def do_load_names(filepath):
    start = time()
    print("Loading", filepath)
    builtins.base.splash.set_text("Loading %s" % filepath)
    names = {}
    data = io.open(filepath, encoding='latin-1')
    for line in data.readlines():
        catNo, aliases = parse_line_name(line)
        names[catNo] = list(map(lambda x: bayer.canonize_name(x), aliases))
    end = time()
    print("Load time:", end - start)
    return names


def load_names(filename, context=defaultDirContext):
    filepath = context.find_data(filename)
    if filepath is not None:
        return do_load_names(filepath)
    else:
        print("File not found", filename)
        return {}


if __name__ == '__main__':
    if len(sys.argv) == 2:
        universe = Universe(None)
        if sys.argv[1].endswith('.txt'):
            load_text(sys.argv[1], universe)
        else:
            load_bin(sys.argv[1], universe)
