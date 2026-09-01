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


"""Read-only queries over the stellar object tree.

These are pure functions of the object graph (no engine/UI dependency),
so they can be reused by any caller that needs to know "what orbits this
body" - menus, HUD widgets, scripting, etc. - without depending on how
that caller obtains or acts on the result.
"""

from .systems import StellarSystem
from .universe import Universe


def get_ancestors(body):
    """Return the ancestor chain of `body`, from the outermost system down
    to (but not including) `body` itself, in root-to-leaf order.

    For an ancestor system with its own primary body (e.g. a planet's own
    moon system), the primary is returned in place of the system itself -
    same convention as get_orbiting_bodies.

    Args:
        body: A StellarObject, or None.

    Returns:
        List of StellarObject, possibly empty, root-first.
    """
    ancestors = []
    parent = body.parent if body is not None else None
    while parent is not None and not isinstance(parent, Universe):
        if isinstance(parent, StellarSystem) and parent.primary is not None:
            if parent.primary != body:
                ancestors.append(parent.primary)
        else:
            ancestors.append(parent)
        parent = parent.parent
    ancestors.reverse()
    return ancestors


def get_orbiting_bodies(body):
    """Return the bodies orbiting in the same system as `body`, sorted by orbit radius.

    `body` itself is excluded from the result. For child systems with a
    primary body (e.g. a planet's own moon system), the primary is
    returned in place of the system itself, matching how such systems are
    presented elsewhere (selection, labels, ...).

    Args:
        body: A StellarObject, or None.

    Returns:
        List of StellarObject, possibly empty.
    """
    if isinstance(body, StellarSystem):
        system = body
    elif body is not None and body.anchor.has_system():
        system = body.anchor.get_system().body
    else:
        system = None
    if system is None:
        return []

    children = [child for child in system.children if child != body]
    if not children:
        return []
    children.sort(key=lambda child: child.anchor.orbit.get_bounding_radius() if child.anchor.has_orbit() else 0)

    result = []
    for child in children:
        if isinstance(child, StellarSystem) and child.primary is not None:
            result.append(child.primary)
        else:
            result.append(child)
    return result
