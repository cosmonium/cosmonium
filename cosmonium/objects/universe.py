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


from panda3d.core import LPoint3d, LQuaterniond

from ..astro.frame import AbsoluteReferenceFrame
from ..astro.orbits import AbsoluteFixedPosition
from ..astro.rotations import FixedRotation
from ..catalogs import objectsDB
from ..engine.anchors import UniverseAnchor

from .systems import OctreeSystem


class Universe(OctreeSystem):
    def __init__(self, radius):
        OctreeSystem.__init__(
            self,
            ['Universe'],
            [],
            orbit=AbsoluteFixedPosition(absolute_reference_point=LPoint3d(), frame=AbsoluteReferenceFrame()),
            rotation=FixedRotation(LQuaterniond(), frame=AbsoluteReferenceFrame()),
            radius=radius,
            description='Universe',
        )

    def create_anchor(self, anchor_class, orbit, rotation, frame, point_color, names, sources_names, description):
        return UniverseAnchor(self, orbit, rotation, self.radius, point_color, names, sources_names, description)

    def find_by_path(self, path, separator='/'):
        # TODO: Should probably moved outsidde Of Universe class
        if not isinstance(path, str):
            return self.anchor.find_by_path(path, separator)
        elif path.startswith(separator):
            path = path[len(separator):]
            return self.anchor.find_by_path(path, separator)
        else:
            parts = path.split(separator)
            root = objectsDB.get(parts[0])
            if root is not None:
                if len(parts) > 1:
                    return root.find_by_path(parts[1:], separator)
                else:
                    return root.anchor
            else:
                return None
