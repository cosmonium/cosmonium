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

"""Celestia Star Catalog (.stc) file parser.

Parses Celestia STC files and instantiates :class:`~Star` and
:class:`~Barycenter` objects, merging them with any stars that
were already loaded from the star catalog.
"""


import builtins
import io
import logging
from time import time

from ..astro import bayer, units
from ..astro.astro import app_to_abs_mag, calc_position
from ..astro.frame import J2000BarycentricEclipticReferenceFrame, J2000EclipticReferenceFrame
from ..astro.orbits import AbsoluteFixedPosition
from ..astro.rotations import UnknownRotation
from ..catalogs import objectsDB
from ..objects.star import Star
from ..objects.surface_factory import StarTexSurfaceFactory
from ..objects.systems import Barycenter
from . import config_parser
from .bodies import celestiaStarSurfaceFactory
from .celestia_utils import (
    instanciate_custom_orbit,
    instanciate_custom_rotation,
    instanciate_elliptical_orbit,
    instanciate_uniform_rotation,
)

logger = logging.getLogger('stc')


def names_list(name):
    return name.split(':')


def parse_names(item_name, item_alias):
    if isinstance(item_name, int):
        names = []
        if item_alias is not None:
            names = list(map(lambda x: bayer.canonize_name(x), names_list(item_alias)))
        if item_name != 0:
            names.append("HIP %d" % item_name)
    else:
        names = names_list(item_name)
    return names


def instanciate_star(universe, context, item_name, item_alias, item_data):
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
    has_barycenter = False
    surface_factory = None
    texture = None
    parent_name = item_data.get('OrbitBarycenter')
    if parent_name is not None:
        parent_name = str(parent_name)
        parent = objectsDB.get(bayer.canonize_name(parent_name))
        has_barycenter = True
        if parent is None:
            logger.warning("Could not find parent barycenter: %s", parent_name)
            return
        parent = parent.get_or_create_system()
    if parent is None:
        parent = universe
    if parent.is_system() and parent.primary is not None:
        parent_anchor = parent.primary.anchor
    else:
        parent_anchor = parent.anchor
    for key, value in item_data.items():
        if key == 'RA':
            ra = float(value) * units.Deg
        elif key == 'Dec':
            decl = float(value) * units.Deg
        elif key == 'Distance':
            distance = float(value) * units.Ly
        elif key == 'SpectralType':
            spectral_type = value
        elif key == 'Radius':
            radius = value
        elif key == 'SemiAxes':
            pass  # = value
        elif key == 'AppMag':
            app_magnitude = value
        elif key == 'AbsMag':
            abs_magnitude = value
        elif key == 'Temperature':
            temperature = value
        elif key == 'BoloCorrection':
            pass  # = value
        elif key == 'Texture':
            texture = value
        elif key == 'OrbitBarycenter':
            pass
        elif key == 'EllipticalOrbit':
            orbit = instanciate_elliptical_orbit(value, True)
        elif key == 'CustomOrbit':
            orbit = instanciate_custom_orbit(value, parent_anchor)
        elif key == 'UniformRotation':
            rotation = instanciate_uniform_rotation(value, parent_anchor, True)
        elif key == 'CustomRotation':
            rotation = instanciate_custom_rotation(value, parent_anchor)
        elif key == 'RotationPeriod':
            pass  # = value
        elif key == 'InfoURL':
            pass  # = value
        else:
            logger.warning("Key of Star '%s' not supported", key)
    if has_barycenter:
        parent_anchor.update(0, 0)
        frame = J2000EclipticReferenceFrame(parent_anchor)
    else:
        frame = J2000BarycentricEclipticReferenceFrame()
    if orbit is None:
        position = calc_position(ra, decl, distance)
        orbit = AbsoluteFixedPosition(absolute_reference_point=position, frame=frame)
    else:
        orbit.set_frame(frame)
    if distance is None:
        distance = orbit.get_absolute_reference_point_at(0).length()
    if app_magnitude is not None and distance is not None:
        if distance <= 0:
            logger.warning(
                "Star %s has non-positive distance %s (parent: %s)", names, distance, parent.anchor.body.get_name()
            )
            return None
        abs_magnitude = app_to_abs_mag(app_magnitude, distance)
    if texture is not None:
        surface_factory = StarTexSurfaceFactory(texture, context)
    else:
        surface_factory = celestiaStarSurfaceFactory
    # Check if a star with the primary name already exists (e.g. loaded from the star catalog).
    # If so, merge its names into the new star and replace it.
    existing_star = objectsDB.get(names[0]) if names else None
    if existing_star is not None:
        # Merge all names from the existing star, preserving new names first and deduplicating
        existing_names = existing_star.get_names().get_all_names() + existing_star.get_source_names()
        names_set = set(names)
        for n in existing_names:
            if n not in names_set:
                names.append(n)
                names_set.add(n)
        # Detach the existing star from its parent
        if existing_star.parent is not None:
            existing_star.parent.remove_child_fast(existing_star)
    star = Star(
        names,
        surface_factory=surface_factory,
        abs_magnitude=abs_magnitude,
        temperature=temperature,
        spectral_type=spectral_type,
        radius=radius,
        orbit=orbit,
        rotation=rotation,
    )
    parent.add_child_fast(star)
    if existing_star is not None:
        objectsDB.replace(existing_star, star)
    return star


def instanciate_barycenter(universe, context, item_name, item_alias, item_data):
    names = parse_names(item_name, item_alias)
    ra = None
    decl = None
    distance = None
    orbit = None
    rotation = UnknownRotation()
    parent = None
    has_barycenter = False
    parent_name = item_data.get('OrbitBarycenter')
    if parent_name is not None:
        parent_name = str(parent_name)
        parent = objectsDB.get(bayer.canonize_name(parent_name))
        has_barycenter = True
        if parent is None:
            logger.warning("Could not find parent barycenter: %s", parent_name)
            return
        parent = parent.get_or_create_system()
    if parent is None:
        parent = universe
    if parent.is_system() and parent.primary is not None:
        parent_anchor = parent.primary.anchor
    else:
        parent_anchor = parent.anchor
    for key, value in item_data.items():
        if key == 'RA':
            ra = float(value) * units.Deg
        elif key == 'Dec':
            decl = float(value) * units.Deg
        elif key == 'Distance':
            distance = float(value) * units.Ly
        elif key == 'OrbitBarycenter':
            pass
        elif key == 'EllipticalOrbit':
            orbit = instanciate_elliptical_orbit(value, True)
        elif key == 'CustomOrbit':
            orbit = instanciate_custom_orbit(value, parent_anchor)
        elif key == 'InfoURL':
            pass  # = value
        else:
            logger.warning("Key of Barycenter '%s' not supported", key)
    # Check if a star with the primary name already exists (e.g. loaded from the star catalog).
    # If so, merge its names into the new star and replace it.
    existing_star = objectsDB.get(names[0]) if names else None
    if existing_star is not None:
        # print("Replacing star", names, "with barycenter")
        # Merge all names from the existing star, preserving new names first and deduplicating
        existing_names = existing_star.get_names().get_all_names() + existing_star.get_source_names()
        names_set = set(names)
        for n in existing_names:
            if n not in names_set:
                names.append(n)
                names_set.add(n)
        # Detach the existing star from its parent
        if existing_star.parent is not None:
            existing_star.parent.remove_child_fast(existing_star)
    if has_barycenter:
        parent_anchor.update(0, 0)
        frame = J2000EclipticReferenceFrame(parent_anchor)
    else:
        frame = J2000BarycentricEclipticReferenceFrame()
    if orbit is None:
        position = calc_position(ra, decl, distance)
        orbit = AbsoluteFixedPosition(absolute_reference_point=position, frame=frame)
    else:
        orbit.set_frame(frame)
    barycenter = Barycenter(names, orbit=orbit, rotation=rotation)
    parent.add_child_fast(barycenter)
    if existing_star is not None:
        objectsDB.replace(existing_star, barycenter)
    return barycenter


def instanciate_item(universe, context, disposition, item_type, item_name, item_parent, item_alias, item_data):
    if disposition != 'Add':
        logger.warning("Disposition '%s' not supported", disposition)
        return
    if item_type == 'Body':
        instanciate_star(universe, context, item_name, item_alias, item_data)
    elif item_type == 'Barycenter':
        instanciate_barycenter(universe, context, item_name, item_alias, item_data)
    else:
        logger.warning("Type '%s' not supported", item_type)
        return


def instanciate(items_list, universe, context):
    for item in items_list:
        instanciate_item(universe, context, *item)


def parse_file(filename, universe, context):
    filepath = context.find_data(filename)
    if filepath is not None:
        start = time()
        logger.info("Loading %s", filepath)
        builtins.base.splash.set_text("Loading %s" % filepath)
        data = io.open(filepath, encoding='latin-1').read()
        items = config_parser.parse(data)
        if items is not None:
            instanciate(items, universe, context)
        end = time()
        logger.debug("Load time: %.3fs", end - start)
    else:
        logger.warning("File not found: %s", filename)


def load(stc, universe, context):
    if isinstance(stc, list):
        for stc in stc:
            parse_file(stc, universe, context)
    else:
        parse_file(stc, universe, context)
