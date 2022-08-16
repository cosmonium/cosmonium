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


from ..astro import bayer
from ..astro import units
from ..astro.orbits import AbsoluteFixedPosition, EllipticalOrbit
from ..astro.rotations import UnknownRotation, UniformRotation, SynchronousRotation
from ..astro.frame import BodyReferenceFrame, J2000EclipticReferenceFrame, J2000EquatorialReferenceFrame
from ..astro.astro import calc_orientation_from_incl_an
from ..astro.elementsdb import orbit_elements_db, rotation_elements_db

from math import pi

def names_list(name):
    return name.split(':')

def body_path(parent):
    path = list(map(lambda x: bayer.canonize_name(x), parent.split('/')))
    return path


def instanciate_custom_orbit(data, parent_anchor):
    if '-' in data:
        (category, name) = data.split('-')
        element_name = category + ':' + name
    else:
        element_name = "celestia:" + data
    orbit = orbit_elements_db.get(element_name)
    if orbit is None:
        #TODO: An error should be raised instead !
        orbit = AbsoluteFixedPosition(frame = J2000EclipticReferenceFrame())
    #TODO: this should not be done arbitrarily
    if isinstance(orbit.frame, BodyReferenceFrame) and orbit.frame.anchor is None:
        orbit.frame.set_anchor(parent_anchor)
    return orbit

def instanciate_elliptical_orbit(data, global_coord):
    semi_major_axis = None
    if global_coord:
        semi_major_axis_units = units.AU
        pericenter_distance_units = units.AU
        period_units = units.JYear
    else:
        semi_major_axis_units = units.Km
        pericenter_distance_units = units.Km
        period_units = units.Day
    pericenter_distance = None
    period = None
    eccentricity = 0.0
    inclination = 0
    ascending_node = 0.0
    arg_of_periapsis = None
    long_of_pericenter = None
    mean_anomaly = None
    mean_longitude = 0.0
    epoch = units.J2000

    for (key, value) in data.items():
        if key == 'SemiMajorAxis':
            semi_major_axis = value
        elif key == '':
            pericenter_distance = value
        elif key == 'Period':
            period = value
        elif key == 'Epoch':
            pass #= value
        elif key == 'Eccentricity':
            eccentricity = value
        elif key == 'Inclination':
            inclination = value
        elif key == 'AscendingNode':
            ascending_node = value
        elif key == 'ArgOfPericenter':
            arg_of_periapsis = value
        elif key == 'LongOfPericenter':
            long_of_pericenter = value
        elif key == 'MeanAnomaly':
            mean_anomaly = value
        elif key == 'MeanLongitude':
            mean_longitude = value
        else:
            print("Key of EllipticalOrbit", key, "not supported")
    if pericenter_distance is None:
        if semi_major_axis is None:
            #TODO: raise error
            pericenter_distance = 1
        else:
            pericenter_distance = semi_major_axis  * semi_major_axis_units * (1.0 - eccentricity)
    else:
        pericenter_distance = pericenter_distance * pericenter_distance_units

    if period is None:
        #TODO: raise error
        period = 1.0
    period = period * period_units

    if arg_of_periapsis is None:
        if long_of_pericenter is None:
            arg_of_periapsis = 0.0
        else:
            arg_of_periapsis = (long_of_pericenter - ascending_node) % 360.0
    if mean_anomaly is None:
        mean_anomaly = (mean_longitude - (arg_of_periapsis + ascending_node)) % 360

    #TODO: The real frame should be given in parameter
    frame = J2000EquatorialReferenceFrame()
    return EllipticalOrbit(frame,
                           epoch,
                           2 * pi / period,
                           mean_anomaly * units.Deg,
                           pericenter_distance,
                           eccentricity,
                           arg_of_periapsis * units.Deg,
                           inclination * units.Deg,
                           ascending_node * units.Deg
                           )

def instanciate_frame(universe, data, parent_anchor, global_coord):
    frame_center = parent_anchor
    if data is not None:
        for (key, value) in data.items():
            if key == 'Center':
                #print("Looking for center", value)
                if '/' in value:
                    global_coord = False
                else:
                    global_coord = True
                path = body_path(value)
                frame_center = universe.find_by_path(path)
                if frame_center is not None:
                    frame_center = frame_center.anchor
                else:
                    print("Frame center '", value, "'not found")
            else:
                print("Frame", key, "not supported")
    return frame_center, global_coord

def instanciate_reference_frame(universe, data, parent_anchor, global_coord):
    frame_type = J2000EclipticReferenceFrame
    frame_center = None
    for (key, value) in data.items():
        if key == 'EquatorJ2000':
            frame_type = J2000EquatorialReferenceFrame
            frame_center, global_coord = instanciate_frame(universe, value, parent_anchor, global_coord)
        elif key == 'EclipticJ2000':
            frame_type = J2000EclipticReferenceFrame
            frame_center, global_coord = instanciate_frame(universe, value, parent_anchor, global_coord)
        else:
            print("Reference frame type", key, "not supported")
#     if frame_center:
#         print("Found center", frame_center.get_name())
    return frame_type(frame_center), global_coord

def instanciate_custom_rotation(data, parent_anchor):
    if '-' in data:
        (category, name) = data.split('-')
        if name == 'p03lp':
            category, name = name, category
        element_name = category + ':' + name
    else:
        element_name = "celestia:" + data
    rotation = rotation_elements_db.get(element_name)
    if rotation is None:
        rotation = UnknownRotation()
    #TODO: this should not be done arbitrarily
    if isinstance(rotation.frame, BodyReferenceFrame) and rotation.frame.anchor is None:
        rotation.frame.set_anchor(parent_anchor)
    return rotation


def instanciate_uniform_rotation(data, parent_anchor, global_coord):
    period = None
    sync = True
    if global_coord:
        period_units = units.Hour
    else:
        period_units = units.Day
    inclination = 0.0
    ascending_node = 0.0
    meridian_angle = 0.0
    epoch  = units.J2000

    for (key, value) in data.items():
        if key == 'Period':
            period = value
            sync=False
        elif key == 'Epoch':
            epoch = epoch
        elif key == 'Inclination':
            inclination = value
        elif key == 'AscendingNode':
            ascending_node = value
        elif key == 'MeridianAngle':
            meridian_angle = value
        else:
            print("Key of UniformRotation", key, "not supported")
    flipped = period is not None and period < 0
    orientation = calc_orientation_from_incl_an(inclination * units.Deg,
                                                ascending_node * units.Deg,
                                                flipped)
    frame = J2000EquatorialReferenceFrame()
    if sync:
        rotation = SynchronousRotation(orientation, meridian_angle * units.Deg, epoch, frame)
        rotation.set_parent_body(parent_anchor)
    else:
        mean_motion = 2 * pi / (period * period_units)
        rotation = UniformRotation(orientation, mean_motion, meridian_angle * units.Deg, epoch, frame)
    return rotation


def instanciate_precessing_rotation(data):
    return UnknownRotation()
