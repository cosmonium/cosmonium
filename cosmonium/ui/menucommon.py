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

from ..extrainfo import extra_info
from ..objects.stellarbody import StellarBody
from ..objects.systems import StellarSystem, SimpleSystem
from ..objects.universe import Universe


def create_orbiting_bodies_menu(engine, body):
    subitems = []
    if isinstance(body, StellarSystem):
        system = body
    elif body is not None and body.system is not None and not isinstance(body.system, Universe):
        system = body.system
    else:
        system = None
    if system is not None:
        children = []
        for child in system.children:
            if child != body:
                children.append(child)
        if len(children) > 0:
            children.sort(key=lambda x: x.anchor.orbit.get_bounding_radius() if x.anchor.has_orbit() else 0)
            subitems = []
            for child in children:
                if isinstance(child, SimpleSystem):
                    subitems.append([child.primary.get_friendly_name(), 0, engine.select_body, child.primary])
                else:
                    subitems.append([child.get_friendly_name(), 0, engine.select_body, child])
    return subitems


def create_orbits_menu(engine, body):
    subitems = []
    if body is not None:
        parent = body.parent
        while parent is not None and not isinstance(parent, Universe):
            if isinstance(parent, SimpleSystem):
                if parent.primary != body:
                    subitems.append([parent.primary.get_friendly_name(), 0, engine.select_body, parent.primary])
            else:
                subitems.append([parent.get_friendly_name(), 0, engine.select_body, parent])
            parent = parent.parent
    return subitems


def create_select_camera_controller_menu(engine):
    subitems = []
    for controller in engine.camera_controllers:
        activable = engine.ship.supports_camera_mode(controller.camera_mode) and (
            not controller.require_target() or engine.selected is not None
        )
        subitems.append(
            (
                controller.get_name(),
                engine.camera_controller is controller,
                engine.set_camera_controller if activable else 0,
                controller,
            )
        )
    return subitems


def create_select_ship_menu(engine):
    subitems = []
    for ship in engine.ships:
        subitems.append((ship.get_name(), engine.ship is ship, engine.set_ship, ship))
    return subitems


def create_surfaces_menu(body):
    subitems = []
    if isinstance(body, StellarBody) and len(body.surfaces) > 1:
        for surface in body.surfaces:
            name = surface.get_name()
            if surface.category is not None:
                if name is not None:
                    name += " (%s)" % surface.category.name
                else:
                    name = "%s" % surface.category.name
            if surface.resolution is not None:
                if isinstance(surface.resolution, int):
                    name += " (%dK)" % surface.resolution
                else:
                    name += " (%s)" % surface.resolution
            if surface is body.surface:
                subitems.append([name, 0, None, None])
            else:
                subitems.append([name, 0, body.set_surface, surface])
    return subitems


def create_extra_info_menu(browser, body):
    subitems = []
    for info in extra_info:
        name = info.get_name()
        url = info.get_url_for(body)
        if url is not None:
            subitems.append([name, 0, browser.load, url])
    return subitems
