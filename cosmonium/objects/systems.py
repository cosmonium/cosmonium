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


from .stellarobject import StellarObject

from ..engine.anchors import SystemAnchor, OctreeAnchor


class ReferencePoint(StellarObject):
    virtual_object = True


class StellarSystem(StellarObject):
    anchor_class = SystemAnchor.System
    virtual_object = True
    support_offset_body_center = False

    def __init__(
        self,
        names,
        source_names,
        primary=None,
        star_system=False,
        orbit=None,
        rotation=None,
        frame=None,
        body_class=None,
        point_color=None,
        description='',
    ):
        StellarObject.__init__(self, names, source_names, orbit, rotation, frame, body_class, point_color, description)
        self.primary = None
        self.has_halo = False
        self.anchor.star_system = star_system
        self.set_primary(primary)

    def create_anchor(self, anchor_class, orbit, rotation, frame, point_color, names, source_names, description):
        return SystemAnchor(self, orbit, rotation, point_color, names, source_names, description)

    @property
    def star_system(self):
        return self.anchor.star_system

    @star_system.setter
    def star_system(self, value):
        self.anchor.star_system = value

    @property
    def children(self):
        """Delegated to the underlying SystemAnchor."""
        return [child.body for child in self.anchor.get_children()]

    def is_system(self):
        return True

    def get_or_create_system(self):
        return self

    def set_primary(self, primary):
        if self.primary is not None:
            self.anchor.set_primary(None)
            self.primary.set_system(None)
            self.primary = None
        if primary is not None:
            self.primary = primary
            self.anchor.set_primary(primary.anchor)
            self.body_class = primary.body_class
            self.anchor.point_color = primary.anchor.point_color

    def find_child_by_name(self, name):
        return self.anchor.find_child_by_name(name)

    def find_by_path(self, path, separator='/'):
        return self.anchor.find_by_path(path, separator)

    def find_nth_child(self, index):
        return self.anchor.find_nth_child(index)

    def add_child_fast(self, child):
        if child.parent is not None:
            # remove_child_fast handles both the body-level and anchor-level removal
            child.parent.remove_child_fast(child)
        self.anchor.add_child(child.anchor)
        child.set_parent(self)
        # TODO: This is a quick workaround until stars of a system are properly managed
        if child.is_emissive():
            self.has_halo = True

    def add_child_star_fast(self, child):
        self.add_child_fast(child)

    def add_child(self, child):
        self.add_child_fast(child)

    def remove_child_fast(self, child):
        child.set_parent(None)
        self.anchor.remove_child(child.anchor)
        if child is self.primary:
            self.primary = None

    def remove_child(self, child):
        self.remove_child_fast(child)

    def is_emissive(self):
        if self.primary is not None:
            return self.primary.is_emissive()
        return False

    def get_label_text(self):
        if self.primary is not None:
            return self.primary.get_label_text()
        return StellarObject.get_label_text(self)

    def get_components(self):
        if self.primary is not None:
            return self.primary.get_components()
        return []

    def start_shadows_update(self):
        if self.primary is not None:
            self.primary.start_shadows_update()

    def end_shadows_update(self):
        if self.primary is not None:
            self.primary.end_shadows_update()

    def add_shadow_target(self, target):
        if self.primary is not None:
            self.primary.add_shadow_target(target)

    def get_bounding_radius(self):
        return self.anchor.get_bounding_radius()


class OctreeSystem(StellarSystem):
    def __init__(
        self,
        names,
        source_names,
        orbit=None,
        rotation=None,
        frame=None,
        body_class=None,
        radius=None,
        point_color=None,
        description='',
    ):
        self.radius = radius
        StellarSystem.__init__(
            self,
            names,
            source_names,
            orbit=orbit,
            rotation=rotation,
            frame=frame,
            body_class=body_class,
            point_color=point_color,
            description=description,
        )

    def create_anchor(self, anchor_class, orbit, rotation, frame, point_color, names, sources_names, description):
        return OctreeAnchor(self, orbit, rotation, self.radius, point_color, names, sources_names, description)

    def dumpOctree(self):
        self.anchor.dump_octree()

    def log_octree(self):
        self.dump_octree = True

    def dumpOctreeStats(self):
        self.dump_octree_stats = not self.dump_octree_stats

    def rebuild(self):
        self.anchor.rebuild()

    def is_emissive(self):
        return True


class Barycenter(StellarSystem):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('body_class', 'star')
        StellarSystem.__init__(self, *args, **kwargs)
        self.has_halo = True

    def is_emissive(self):
        return True
