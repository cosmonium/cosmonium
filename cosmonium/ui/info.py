# -*- coding: utf-8 -*-
from __future__ import print_function
from __future__ import absolute_import

from ..bodies import StellarObject, StellarBody, Star
from ..bodyelements import NoAtmosphere
from ..dataattribution import dataAttributionDB
from ..surfaces import Surface
from ..astro.orbits import Orbit, FixedPosition, EllipticalOrbit
from ..astro.rotations import Rotation, UniformRotation
from ..astro.units import toUnit, time_to_values, toDegMinSec, toHourMinSec
from ..astro import bayer
from ..astro import units

from .. import utils

from math import pi

class ObjectInfo(object):
    infos = []
    infos_map = {}

    @classmethod
    def register(cls, info_class, info_method):
        cls.infos_map[info_class] = info_method
        cls.infos.insert(0, (info_class, info_method))

    @classmethod
    def get_info_for(cls, body):
        info_method = cls.infos_map.get(body.__class__, None)
        if info_method is None:
            for entry in cls.infos:
                (info_class, info_method) = entry
                if isinstance(body, info_class): break
        if info_method is not None:
            result = info_method(body)
        else:
            print("Unknown object type", body.__class__.__name__)
            result = None
        return result

def default_info(body):
    return ["Unknown", [('Unknown class', body.__class__.__name__)]]

def orbit_info(orbit):
    return None

def fixed_orbit_info(orbit):
    texts = []
    texts.append(["Right Ascension", "%dh%dm%gs" % toHourMinSec(orbit.get_right_asc() * 180 / pi)])
    texts.append(["Declination", "%d°%d'%g\"" % toDegMinSec(orbit.get_declination() * 180 / pi)])
    return ["Position", texts]

def elliptic_orbit_info(orbit):
    texts = []
    sma = orbit.pericenter_distance / (1.0 - orbit.eccentricity)
    texts.append(["Semi-major axis", "%s" % toUnit(sma, units.lengths_scale)])
    texts.append(["Period", "%s" % toUnit(abs(orbit.period), units.times_scale)])
    texts.append(["Eccentricity", "%g" % (orbit.eccentricity)])
    texts.append(["Inclination", "%g°" % (orbit.inclination * 180 / pi)])
    texts.append(["Ascending Node", "%g°" % (orbit.ascending_node * 180 / pi)])
    texts.append(["Argument of Periapsis", "%g°" % (orbit.arg_of_periapsis * 180 / pi)])
    texts.append(["Mean Anomaly", "%g°" % (orbit.mean_anomaly * 180 / pi)])
    date = "%02d:%02d:%02d %d:%02d:%02d UTC" % time_to_values(orbit.epoch)
    texts.append(["Epoch", "%s" % date])
    return ["Orbit", texts]

def rotation_info(orbit):
    return None

def circular_rotation_info(rotation):
    texts = []
    if rotation.sync:
        texts.append(["Period", "Synchronous"])
    else:
        texts.append(["Period", toUnit(abs(rotation.period), units.times_scale)])
    texts.append(["Inclination", "%g°" % (rotation.inclination * 180 / pi)])
    texts.append(["Ascending Node", "%g°" % (rotation.ascending_node * 180 / pi)])
    date = "%02d:%02d:%02d %d:%02d:%02d UTC" % time_to_values(rotation.epoch)
    texts.append(["Epoch", "%s" % date])
    return ["Rotation", texts]

def surface(surface):
    texts = []
    name = surface.get_name()
    if name is not None and name != '':
        texts.append(["Name", name])
    if surface.category is not None:
        texts.append(["Category", surface.category.name])
    if surface.resolution is not None:
        if isinstance(surface.resolution, int):
            texts.append(["Resolution", "%dK" % surface.resolution])
        else:
            texts.append(["Resolution", "%s" % surface.resolution])
    attributions = []
    if surface.attribution is not None:
        attributions.append(('Surface', surface.attribution))
    else:
        if surface.shape is not None and surface.shape.attribution is not None:
            attributions.append(('Model', surface.shape.attribution))
        if surface.appearance is not None:
            if surface.appearance.attribution is not None:
                attributions.append(('Textures', surface.appearance.attribution))
            elif surface.appearance.texture is not None and surface.appearance.texture.source.attribution is not None:
                attributions.append(('Texture', surface.appearance.texture.source.attribution))
    for (name, attribution) in attributions:
        if attribution is None: continue
        data_attribution = dataAttributionDB.get_attribution(attribution)
        texts.append([name, ''])
        if data_attribution is not None:
            texts.append(["Source", data_attribution.name])
            if data_attribution.copyright is not None:
                texts.append(["Copyright", data_attribution.copyright])
            if data_attribution.license is not None:
                texts.append(["License", data_attribution.license])
            if data_attribution.url is not None:
                texts.append(["URL", data_attribution.url])
        else:
            texts.append(["Source", attribution])
    if len(texts) != 0:
        return ["Surface", texts]
    else:
        return None

def stellar_object(body):
    texts = []
    general = []
    texts.append(["General", general])
    names = utils.join_names(bayer.decode_names(body.names))
    general.append(["Names", names])
    general.append(["Category", body.body_class])
    if body.description != '':
        general.append(["Description", body.description])
    texts.append(ObjectInfo.get_info_for(body.orbit))
    texts.append(ObjectInfo.get_info_for(body.rotation))
    return texts

def stellar_body(body):
    texts = []
    general = []
    texts.append(["General", general])
    names = utils.join_names(bayer.decode_names(body.names))
    general.append(["Names", names])
    general.append(["Category", body.body_class])
    if body.oblateness is None or body.oblateness == 0.0:
        radius = body.get_apparent_radius()
        general.append(["Radius", "%s (%s)" % (toUnit(radius, units.lengths_scale), toUnit(radius, units.diameter_scale))])
    else:
        radius = body.get_apparent_radius()
        polar_radius = radius * (1 - body.oblateness)
        general.append(["Polar radius", "%s (%s)" % (toUnit(polar_radius, units.lengths_scale), toUnit(polar_radius, units.diameter_scale))])
        general.append(["Equatorial radius", "%s (%s)" % (toUnit(radius, units.lengths_scale), toUnit(radius, units.diameter_scale))])
        general.append(["Ellipticity", "%g" % body.oblateness])
    general.append(["Atmosphere", "Yes" if not isinstance(body.atmosphere, NoAtmosphere) else "No"])
    general.append(["Clouds", "Yes" if body.clouds is not None else "No"])
    general.append(["Rings", "Yes" if body.ring is not None else "No"])
    if body.description != '':
        general.append(["Description", body.description])
    if body.system is not None:
        texts.append(ObjectInfo.get_info_for(body.system.orbit))
    else:
        texts.append(ObjectInfo.get_info_for(body.orbit))
    texts.append(ObjectInfo.get_info_for(body.rotation))
    if body.surface is not None:
        texts.append(ObjectInfo.get_info_for(body.surface))
    return texts

def star(body):
    texts = []
    general = []
    texts.append(["General", general])
    names = utils.join_names(bayer.decode_names(body.names))
    general.append(["Names", names])
    general.append(["Category", body.body_class])
    general.append(["Radius", "%s (%s)" % (toUnit(body.get_apparent_radius(), units.lengths_scale), toUnit(body.get_apparent_radius(), units.diameter_scale))])
    general.append(["Spectral type", body.spectral_type.get_text() if body.spectral_type is not None else 'Unknown'])
    general.append(["Abs magnitude", "%g" % body.get_abs_magnitude()])
    general.append(["Luminosity", "%g W (%gx Sun)" % (body.get_luminosity() * units.L0,  body.get_luminosity())])
    general.append(["Temperature", "%g K" % body.temperature if body.temperature is not None else 'Unknown'])
    if body.description != '':
        general.append(["Description", body.description])
    if body.system is not None:
        texts.append(ObjectInfo.get_info_for(body.system.orbit))
    else:
        texts.append(ObjectInfo.get_info_for(body.orbit))
    texts.append(ObjectInfo.get_info_for(body.rotation))
    if body.surface is not None:
        texts.append(ObjectInfo.get_info_for(body.surface))
    return texts

ObjectInfo.register(object, default_info)
ObjectInfo.register(Orbit, orbit_info)
ObjectInfo.register(FixedPosition, fixed_orbit_info)
ObjectInfo.register(EllipticalOrbit, elliptic_orbit_info)
ObjectInfo.register(Rotation, rotation_info)
ObjectInfo.register(UniformRotation, circular_rotation_info)
ObjectInfo.register(Surface, surface)
ObjectInfo.register(StellarObject, stellar_object)
ObjectInfo.register(StellarBody, stellar_body)
ObjectInfo.register(Star, star)
