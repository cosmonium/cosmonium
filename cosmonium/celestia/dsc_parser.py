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


from panda3d.core import LVector3d

from ..objects.universe import Universe
from ..objects.galaxies import Galaxy
from ..celestia import config_parser
from ..astro.astro import calc_position
from ..astro.orbits import AbsoluteFixedPosition
from ..astro.rotations import FixedRotation
from ..astro.frame import J2000EquatorialReferenceFrame, AbsoluteReferenceFrame
from ..astro import units
from ..dircontext import defaultDirContext
from .. import utils

import sys
import io

def names_list(name):
    return name.split(':')

def instanciate_body(universe, item_type, item_name, item_data):
    ra=None
    decl=None
    distance=None
    type=None
    radius=None
    axis=None
    angle=None
    abs_magnitude=None
    app_magnitude=None
    orbit=None
    axis = LVector3d.up()
    angle = 0.0
    names = names_list(item_name)
    for (key, value) in item_data.items():
        if key == 'RA':
            ra = float(value) * units.HourAngle
        elif key == 'Dec':
            decl = float(value) * units.Deg
        elif key == 'Distance':
            distance = float(value) * units.Ly
        elif key == 'Type':
            type = value
        elif key == 'Radius':
            radius = value
        elif key == 'Axis':
            axis = LVector3d(*value)
        elif key == 'Angle':
            angle = value
        elif key == 'AbsMag':
            abs_magnitude = value
        elif key == 'AppMag':
            app_magnitude = value
        elif key == 'InfoURL':
            pass # = value
        else:
            print("Key of", item_type, key, "not supported")
    position = calc_position(ra, decl, distance)
    frame = AbsoluteReferenceFrame() #TDODO: This should be J2000BarycentricEclipticReferenceFrame
    orbit = AbsoluteFixedPosition(absolute_reference_point=position, frame=frame)
    rot = utils.LQuaternionromAxisAngle(axis, angle, units.Deg)
    rotation = FixedRotation(rot, J2000EquatorialReferenceFrame())
    if app_magnitude != None and distance != None:
        abs_magnitude = units.app_to_abs_mag(app_magnitude, distance)
    dso = Galaxy(names,
                abs_magnitude=abs_magnitude,
                radius=radius,
                orbit=orbit,
                rotation=rotation)
    return dso

def instanciate_item(universe, disposition, item_type, item_name, item_parent, item_alias, item_data):
    if disposition != 'Add':
        print("Disposition", disposition, "not supported")
        return
    if item_parent:
        print("Parent", item_parent, "not supported")        
    if item_type == 'Galaxy':
        body = instanciate_body(universe, item_type, item_name, item_data)
        universe.add_child_fast(body)
    else:
        print("Type", item_type, "not supported")
        return

def instanciate(items_list, universe):
    for item in items_list:
        instanciate_item(universe, *item)

def parse_file(filename, universe, context=defaultDirContext):
    filepath = context.find_data(filename)
    if filepath is not None:
        print("Loading", filepath)
        base.splash.set_text("Loading %s" % filepath)
        data = io.open(filepath, encoding='latin-1').read()
        items = config_parser.parse(data)
        if items is not None:
            instanciate(items, universe)
    else:
        print("File not found", filename)

def load(dsc, universe, context=defaultDirContext):
    if isinstance(dsc, list):
        for dsc in dsc:
            parse_file(dsc, universe, context)
    else:
        parse_file(dsc, universe, context)

if __name__ == '__main__':
    universe=Universe(None)
    if len(sys.argv) == 2:
        parse_file(sys.argv[1], universe)
