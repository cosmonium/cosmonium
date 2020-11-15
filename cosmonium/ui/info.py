# -*- coding: utf-8 -*-
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

from ..bodies import StellarObject, StellarBody, Star
from ..dataattribution import dataAttributionDB
from ..surfaces import Surface
from ..astro.orbits import Orbit, FixedPosition, FixedOrbit, EllipticalOrbit, FuncOrbit
from ..astro.rotations import Rotation, UnknownRotation, UniformRotation, SynchronousRotation, FuncRotation
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
            print(_("Unknown object type"), body.__class__.__name__)
            result = None
        return result

def default_info(body):
    return ["Unknown", [(_('Unknown class'), body.__class__.__name__)]]

def orbit_info(orbit):
    return None

def fixed_orbit_info(orbit):
    texts = []
    texts.append([_("Right Ascension"), "%dh%dm%gs" % toHourMinSec(orbit.get_right_asc() * 180 / pi)])
    texts.append([_("Declination"), "%d°%d'%g\"" % toDegMinSec(orbit.get_declination() * 180 / pi)])
    return [_("Position"), texts]

def func_orbit_info(orbit):
    texts = []
    texts.append([_("Type"), orbit.__class__.__name__])
    return [_("Orbit"), texts]

def elliptic_orbit_info(orbit):
    texts = []
    sma = orbit.pericenter_distance / (1.0 - orbit.eccentricity)
    texts.append([_("Semi-major axis"), "%s" % toUnit(sma, units.lengths_scale)])
    texts.append([_("Period"), "%s" % toUnit(abs(orbit.period), units.times_scale)])
    texts.append([_("Eccentricity"), "%g" % (orbit.eccentricity)])
    texts.append([_("Inclination"), "%g°" % (orbit.inclination * 180 / pi)])
    texts.append([_("Ascending Node"), "%g°" % (orbit.ascending_node * 180 / pi)])
    texts.append([_("Argument of Periapsis"), "%g°" % (orbit.arg_of_periapsis * 180 / pi)])
    texts.append([_("Mean Anomaly"), "%g°" % (orbit.mean_anomaly * 180 / pi)])
    date = "%02d:%02d:%02d %d:%02d:%02d UTC" % time_to_values(orbit.epoch)
    texts.append([_("Epoch"), "%s" % date])
    return [_("Orbit"), texts]

def rotation_info(orbit):
    return None

def unknown_rotation_info(rotation):
    texts = [[_("Unknown rotation"), ""]]
    return [_("Rotation"), texts]

def uniform_rotation_info(rotation):
    texts = []
    #TODO: should give simulation time !
    (ra, de) = rotation.calc_axis_ra_de(0)
    if isinstance(rotation, SynchronousRotation):
        texts.append([_("Period"), _("Synchronous")])
    else:
        texts.append([_("Period"), toUnit(abs(rotation.period), units.times_scale)])
    texts.append([_("Right Ascension"), "%dh%dm%gs" % toHourMinSec(ra * 180 / pi)])
    texts.append([_("Declination"), "%d°%d'%g\"" % toDegMinSec(de * 180 / pi)])
    texts.append([_("Meridian"), "%g°" % (rotation.meridian_angle * 180 / pi)])
    date = "%02d:%02d:%02d %d:%02d:%02d UTC" % time_to_values(rotation.epoch)
    texts.append([_("Epoch"), "%s" % date])
    return [_("Rotation"), texts]

def func_rotation_info(orbit):
    texts = []
    texts.append([_("Type"), orbit.__class__.__name__])
    return [_("Rotation"), texts]

def surface(surface):
    texts = []
    name = surface.get_name()
    if name is not None and name != '':
        texts.append([_("Name"), name])
    if surface.category is not None:
        texts.append([_("Category"), surface.category.name])
    if surface.resolution is not None:
        if isinstance(surface.resolution, int):
            texts.append([_("Resolution"), "%dK" % surface.resolution])
        else:
            texts.append([_("Resolution"), "%s" % surface.resolution])
    attributions = []
    if surface.attribution is not None:
        attributions.append((_('Surface'), surface.attribution))
    else:
        if surface.shape is not None and surface.shape.attribution is not None:
            attributions.append((_('Model'), surface.shape.attribution))
        if surface.appearance is not None:
            if surface.appearance.attribution is not None:
                attributions.append((_('Textures'), surface.appearance.attribution))
            elif surface.appearance.texture is not None and surface.appearance.texture.source.attribution is not None:
                attributions.append((_('Texture'), surface.appearance.texture.source.attribution))
    for (name, attribution) in attributions:
        if attribution is None: continue
        texts.append([name, None])
        if not isinstance(attribution, list):
            attribution = [attribution]
        for entry in attribution:
            data_attribution = dataAttributionDB.get_attribution(entry)
            if data_attribution is not None:
                texts.append([_("Source"), data_attribution.name])
                if data_attribution.copyright is not None:
                    texts.append([_("Copyright"), data_attribution.copyright])
                if data_attribution.license is not None:
                    texts.append([_("License"), data_attribution.license])
                if data_attribution.url is not None:
                    texts.append([_("URL"), data_attribution.url])
            else:
                texts.append([_("Source"), entry])
    if len(texts) != 0:
        return [_("Surface"), texts]
    else:
        return None

def stellar_object(body):
    texts = []
    general = []
    texts.append([_("General"), general])
    names = utils.join_names(bayer.decode_names(body.names))
    general.append([_("Names"), names])
    general.append([_("Category"), body.body_class])
    if body.description != '':
        general.append([_("Description"), body.description])
    texts.append(ObjectInfo.get_info_for(body.orbit))
    texts.append(ObjectInfo.get_info_for(body.rotation))
    return texts

def stellar_body(body):
    texts = []
    general = []
    texts.append([_("General"), general])
    names = utils.join_names(bayer.decode_names(body.names))
    general.append([_("Names"), names])
    general.append([_("Category"), body.body_class])
    if body.oblateness is None or body.oblateness == 0.0:
        radius = body.get_apparent_radius()
        general.append([_("Radius"), "%s (%s)" % (toUnit(radius, units.lengths_scale), toUnit(radius, units.diameter_scale))])
    else:
        radius = body.get_apparent_radius()
        polar_radius = radius * (1 - body.oblateness)
        general.append([_("Polar radius"), "%s (%s)" % (toUnit(polar_radius, units.lengths_scale), toUnit(polar_radius, units.diameter_scale))])
        general.append([_("Equatorial radius"), "%s (%s)" % (toUnit(radius, units.lengths_scale), toUnit(radius, units.diameter_scale))])
        general.append([_("Ellipticity"), "%g" % body.oblateness])
    general.append([_("Atmosphere"), _("Yes") if body.atmosphere is not None else _("No")])
    general.append([_("Clouds"), _("Yes") if body.clouds is not None else _("No")])
    general.append([_("Rings"), _("Yes") if body.ring is not None else _("No")])
    if body.description != '':
        general.append([_("Description"), body.description])
    if body.system is not None and isinstance(body.orbit, FixedOrbit):
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
    texts.append([_("General"), general])
    names = utils.join_names(bayer.decode_names(body.names))
    general.append([_("Names"), names])
    general.append([_("Category"), body.body_class])
    general.append([_("Radius"), "%s (%s)" % (toUnit(body.get_apparent_radius(), units.lengths_scale), toUnit(body.get_apparent_radius(), units.diameter_scale))])
    general.append([_("Spectral type"), body.spectral_type.get_text() if body.spectral_type is not None else _('Unknown')])
    general.append([_("Abs magnitude"), "%g" % body.get_abs_magnitude()])
    general.append([_("Luminosity"), "%g W (%gx Sun)" % (body.get_luminosity() * units.L0,  body.get_luminosity())])
    general.append([_("Temperature"), "%g K" % body.temperature if body.temperature is not None else _('Unknown')])
    if body.description != '':
        general.append([_("Description"), body.description])
    if body.system is not None and isinstance(body.orbit, FixedOrbit):
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
ObjectInfo.register(FuncOrbit, func_orbit_info)
ObjectInfo.register(EllipticalOrbit, elliptic_orbit_info)
ObjectInfo.register(Rotation, rotation_info)
ObjectInfo.register(UniformRotation, uniform_rotation_info)
ObjectInfo.register(SynchronousRotation, uniform_rotation_info)
ObjectInfo.register(UnknownRotation, unknown_rotation_info)
ObjectInfo.register(FuncRotation, func_rotation_info)
ObjectInfo.register(Surface, surface)
ObjectInfo.register(StellarObject, stellar_object)
ObjectInfo.register(StellarBody, stellar_body)
ObjectInfo.register(Star, star)
