from __future__ import print_function
from __future__ import absolute_import

from ..astro import bayer
from ..astro import units
from ..astro.orbits import EllipticalOrbit
from ..astro.rotations import FixedRotation, UniformRotation
from ..astro.frame import J2000EclipticReferenceFrame, J2000EquatorialReferenceFrame
from ..astro.elementsdb import orbit_elements_db, rotation_elements_db

def names_list(name):
    return name.split(':')

def body_path(parent):
    path = list(map(lambda x: bayer.canonize_name(x), parent.split('/')))
    return path


def instanciate_custom_orbit(data):
    if '-' in data:
        (category, name) = data.split('-')
        element_name = category + ':' + name
    else:
        element_name = "celestia:" + data
    return orbit_elements_db.get(element_name)

def instanciate_elliptical_orbit(data, global_coord):
    semi_major_axis=None
    if global_coord:
        semi_major_axis_units=units.AU
        pericenter_distance_units=units.AU
        period_units=units.JYear
    else:
        semi_major_axis_units=units.Km
        pericenter_distance_units=units.Km        
        period_units=units.Day
    pericenter_distance=None
    radial_speed=None
    period=None
    eccentricity=0.0
    inclination=0
    ascending_node=0.0
    arg_of_periapsis=None
    long_of_pericenter=None
    mean_anomaly=None
    mean_longitude=0.0
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
    return EllipticalOrbit(semi_major_axis=semi_major_axis,
        semi_major_axis_units=semi_major_axis_units,
        pericenter_distance=pericenter_distance,
        pericenter_distance_units=pericenter_distance_units,
        radial_speed=radial_speed,
        period=period,
        period_units=period_units,
        eccentricity=eccentricity,
        inclination=inclination,
        ascending_node=ascending_node,
        arg_of_periapsis=arg_of_periapsis,
        long_of_pericenter=long_of_pericenter,
        mean_anomaly=mean_anomaly,
        mean_longitude=mean_longitude)

def instanciate_frame(universe, data, global_coord):
    frame_center = None
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
                if frame_center is None:
                    print("Frame center '", value, "'not found")
            else:
                print("Frame", key, "not supported")
    return frame_center, global_coord

def instanciate_reference_frame(universe, data, global_coord):
    frame_type = J2000EclipticReferenceFrame
    frame_center = None
    for (key, value) in data.items():
        if key == 'EquatorJ2000':
            frame_type = J2000EquatorialReferenceFrame
            frame_center, global_coord = instanciate_frame(universe, value, global_coord)
        elif key == 'EclipticJ2000':
            frame_type = J2000EclipticReferenceFrame
            frame_center, global_coord = instanciate_frame(universe, value, global_coord)
        else:
            print("Reference frame type", key, "not supported")
#     if frame_center:
#         print("Found center", frame_center.get_name())
    return frame_type(frame_center), global_coord

def instanciate_custom_rotation(data):
    if '-' in data:
        (category, name) = data.split('-')
        if name == 'p03lp':
            category, name = name, category
        element_name = category + ':' + name
    else:
        element_name = "celestia:" + data
    return rotation_elements_db.get(element_name)

def instanciate_uniform_rotation(data, global_coord):
    radial_speed=None
    period=None
    sync=True
    if global_coord:
        period_units=units.Hour
    else:
        period_units=units.Day
    inclination=0.0
    ascending_node=0.0
    meridian_angle=0.0
    for (key, value) in data.items():
        if key == 'Period':
            period = value
            sync=False
        elif key == 'Epoch':
            pass #= value
        elif key == 'Inclination':
            inclination = value
        elif key == 'AscendingNode':
            ascending_node = value
        elif key == 'MeridianAngle':
            meridian_angle = value
        else:
            print("Key of UniformRotation", key, "not supported")
    return UniformRotation(radial_speed=radial_speed,
                              period=period,
                              sync=sync,
                              period_units=period_units,
                              inclination=inclination,
                              ascending_node=ascending_node,
                              meridian_angle=meridian_angle)

def instanciate_precessing_rotation(data):
    return FixedRotation()
