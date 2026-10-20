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


"""Read-only queries over the anchor tree.

These are pure functions of the anchor graph (no engine/UI dependency),
so they can be reused by any caller that needs to know "what orbits this
body" - menus, HUD widgets, scripting, etc. - without depending on how
that caller obtains or acts on the result.
"""

from ..engine.anchors import UniverseAnchor


def get_ancestors(anchor):
    """Return the ancestor chain of `anchor`, from the outermost system down
    to (but not including) `anchor` itself, in root-to-leaf order.

    For an ancestor system with its own primary body (e.g. a planet's own
    moon system), the primary is returned in place of the system itself -
    same convention as get_orbiting_bodies.

    Args:
        anchor: The anchor of an object, or None.

    Returns:
        List of anchors, possibly empty, root-first.
    """
    ancestors = []
    parent = anchor.parent if anchor is not None else None
    while parent is not None and not isinstance(parent, UniverseAnchor):
        if parent.primary is not None:
            if parent.primary != anchor:
                ancestors.append(parent.primary)
        else:
            ancestors.append(parent)
        parent = parent.parent
    ancestors.reverse()
    return ancestors


def get_orbiting_bodies(anchor):
    """Return the objects orbiting in the same system as `anchor`, sorted by orbit radius.

    `anchor` itself is excluded from the result. For child systems with a
    primary body (e.g. a planet's own moon system), the primary is
    returned in place of the system itself, matching how such systems are
    presented elsewhere (selection, labels, ...).

    Args:
        anchor: The anchor of an object, or None.

    Returns:
        List of anchors, possibly empty.
    """
    if anchor is None:
        return []
    if anchor.is_system():
        system = anchor
    elif anchor.has_system():
        system = anchor.get_system()
    else:
        return []

    children = [child for child in system.get_children() if child != anchor]
    children.sort(key=lambda child: child.orbit.get_bounding_radius() if child.has_orbit() else 0)

    result = []
    for child in children:
        if child.is_system() and child.primary is not None:
            result.append(child.primary)
        else:
            result.append(child)
    return result
