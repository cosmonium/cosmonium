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

from ..universe import Universe
from ..systems import Barycenter
from ..catalogs import objectsDB
from ..astro.orbits import FixedPosition
from ..astro.rotations import UnknownRotation
from ..astro.frame import j2000BarycentricEquatorialReferenceFrame
from ..astro.astro import app_to_abs_mag
from ..astro import bayer
from ..astro import units
from ..bodies import Star, StarTexSurfaceFactory
from ..dircontext import defaultDirContext

from .celestia_utils import instanciate_elliptical_orbit, instanciate_custom_orbit, \
    instanciate_uniform_rotation, instanciate_custom_rotation
from .bodies import celestiaStarSurfaceFactory
from . import config_parser

from time import time
import sys
import io

def names_list(name):
    return name.split(':')

def parse_names(item_name, item_alias):
    if isinstance(item_name, int):
        names=[]
        if item_alias != None:
            names = list(map(lambda x: bayer.canonize_name(x), names_list(item_alias)))
        if item_name != 0:
            names.append("HIP %d" % item_name)
    else:
        names = names_list(item_name)
    return names

def instanciate_star(universe, item_name, item_alias, item_data):
    names = parse_names(item_name, item_alias)
    ra = None
    decl = None
    distance = None
    spectral_type = None
    radius = None
    abs_magnitude = None
    app_magnitude = None
    temperature = None
    orbit = None
    rotation = UnknownRotation()
    parent = None
    surface_factory = None
    texture = None
    parent_name = item_data.get('OrbitBarycenter')
    if parent_name is not None:
        parent = objectsDB.get(bayer.canonize_name(parent_name))
        if parent is None:
            print("Could not find parent", parent)
    if parent is None:
        parent = universe
    for (key, value) in item_data.items():
        if key == 'RA':
            ra = value
        elif key == 'Dec':
            decl = value
        elif key == 'Distance':
            distance = value
        elif key == 'SpectralType':
            spectral_type = value
        elif key == 'Radius':
            radius = value
        elif key == 'SemiAxes':
            pass # = value
        elif key == 'AppMag':
            app_magnitude = value
        elif key == 'AbsMag':
            abs_magnitude = value
        elif key == 'Temperature':
            temperature = value
        elif key == 'BoloCorrection':
            pass # = value
        elif key == 'Texture':
            texture = value
        elif key == 'OrbitBarycenter':
            pass
        elif key == 'EllipticalOrbit':
            orbit = instanciate_elliptical_orbit(value, True)
        elif key == 'CustomOrbit':
            orbit = instanciate_custom_orbit(value, parent)
        elif key == 'UniformRotation':
            rotation = instanciate_uniform_rotation(value, True)
        elif key == 'CustomRotation':
            rotation = instanciate_custom_rotation(value, parent)
        elif key == 'RotationPeriod':
            pass # = value
        else:
            print("Key of Star", key, "not supported")
    if orbit is None:
        orbit = FixedPosition(right_asc=ra, declination=decl, distance=distance, distance_unit=units.Ly)
    orbit.set_frame(j2000BarycentricEquatorialReferenceFrame)
    if distance is not None:
        distance *= units.Ly
    elif parent is not None:
        distance = parent.get_global_position().length()
    if app_magnitude != None and distance != None:
        abs_magnitude = app_to_abs_mag(app_magnitude, distance)
    if texture is not None:
        surface_factory=StarTexSurfaceFactory(texture)
    else:
        surface_factory=celestiaStarSurfaceFactory
    star = Star(names, source_names=[],
                surface_factory=surface_factory,
                abs_magnitude=abs_magnitude,
                temperature=temperature,
                spectral_type=spectral_type,
                radius=radius,
                orbit=orbit,
                rotation=rotation)
    parent.add_child_star_fast(star)
    return star

def instanciate_barycenter(universe, item_name, item_alias, item_data):
    names = parse_names(item_name, item_alias)
    ra = None
    decl = None
    distance = None
    orbit = None
    rotation = UnknownRotation()
    parent = None
    parent_name = item_data.get('OrbitBarycenter')
    if parent_name is not None:
        parent = objectsDB.get(bayer.canonize_name(parent_name))
        if parent is None:
            print("Could not find parent", parent)
    if parent is None:
        parent = universe
    for (key, value) in item_data.items():
        if key == 'RA':
            ra = value
        elif key == 'Dec':
            decl = value
        elif key == 'Distance':
            distance = value
        elif key == 'OrbitBarycenter':
            pass
        elif key == 'EllipticalOrbit':
            orbit = instanciate_elliptical_orbit(value, True)
        elif key == 'CustomOrbit':
            orbit = instanciate_custom_orbit(value, parent)
        else:
            print("Key of Barycenter", key, "not supported")
    existing_star = objectsDB.get(names[-1])
    if existing_star:
        #print("Replacing star", names, "with barycenter")
        objectsDB.remove(existing_star)
        if existing_star.parent is not None:
            existing_star.parent.remove_child_fast(existing_star)
    if orbit is None:
        orbit = FixedPosition(right_asc=ra, declination=decl, distance=distance, distance_unit=units.Ly)
    orbit.set_frame(j2000BarycentricEquatorialReferenceFrame)
    barycenter = Barycenter(names, source_names=[], orbit=orbit, rotation=rotation)
    parent.add_child_star_fast(barycenter)
    return barycenter

def instanciate_item(universe, disposition, item_type, item_name, item_parent, item_alias, item_data):
    if disposition != 'Add':
        print("Disposition", disposition, "not supported")
        return
    if item_type == 'Body':
        instanciate_star(universe, item_name, item_alias, item_data)
    elif item_type == 'Barycenter':
        instanciate_barycenter(universe, item_name, item_alias, item_data)
    else:
        print("Type", item_type, "not supported")
        return

def instanciate(items_list, universe):
    for item in items_list:
        instanciate_item(universe, *item)

def parse_file(filename, universe, context=defaultDirContext):
    filepath = context.find_data(filename)
    if filepath is not None:
        start = time()
        print("Loading", filepath)
        base.splash.set_text("Loading %s" % filepath)
        data = io.open(filepath, encoding='latin-1').read()
        items = config_parser.parse(data)
        if items is not None:
            instanciate(items, universe)
        end = time()
        print("Load time:", end - start)
    else:
        print("File not found", filename)

def load(stc, universe):
    if isinstance(stc, list):
        for stc in stc:
            parse_file(stc, universe)
    else:
        parse_file(stc, universe)

if __name__ == '__main__':
    universe=Universe()
    if len(sys.argv) == 2:
        parse_file(sys.argv[1], universe)
