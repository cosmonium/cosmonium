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

"""Octree spatial partitioning data structure.

This module provides the OctreeNode class for efficient spatial organization
and queries of celestial objects.
"""

from __future__ import annotations

from math import sqrt
from typing import TYPE_CHECKING

from panda3d.core import LPoint3d

if TYPE_CHECKING:
    from .anchors import StellarAnchor
    from .traversers import AnchorTraverser


class OctreeNode:
    """Spatial partitioning data structure for efficient queries.

    An octree node recursively subdivides 3D space into eight octants, enabling
    efficient spatial queries for large numbers of celestial objects.
    Each node can contain leaves (stellar objects) and up to eight child octree nodes.
    """

    OctreeSystem: int = 8

    max_level: int = 200
    max_leaves: int = 75
    nb_cells: int = 0
    nb_leaves: int = 0
    child_factor: float = 0.25

    def __init__(
        self,
        level: int,
        parent: OctreeNode | None,
        center: LPoint3d,
        width: float,
        threshold: float,
        index: int = -1,
    ) -> None:
        """Initialize an OctreeNode with the given parameters.

        Args:
            level: The depth level of this node in the octree (0 for root).
            parent: The parent OctreeNode, or None for the root node.
            center: The center point of this octree node's volume.
            width: The width of this octree node's cubic volume.
            threshold: The luminosity threshold for determining object placement.
            index: The index of this node within its parent (0-7), or -1 for root.
        """
        self.level = level
        self.parent = parent
        self.width = width
        self.radius = self.width / 2.0 * sqrt(3)
        self.center = center
        self.threshold = threshold
        self.index = index
        self.has_children = False
        self.children = [None, None, None, None, None, None, None, None]
        self.leaves = []
        self.max_luminosity = 0.0
        self.rebuild_needed = False
        # TODO: Right now an octree contains anything
        self.content = ~0
        OctreeNode.nb_cells += 1

    def get_num_children(self) -> int:
        """Get the number of non-None child nodes.

        Returns:
            The count of child nodes that have been created.
        """
        nb_children = 0
        for child in self.children:
            if child is not None:
                nb_children += 1
        return nb_children

    def get_num_leaves(self) -> int:
        """Get the number of leaf objects in this node.

        Returns:
            The count of stellar objects directly contained in this node.
        """
        return len(self.leaves)

    def set_rebuild_needed(self) -> None:
        """Mark this node and all ancestors as needing rebuild.

        This propagates the rebuild flag up the tree to ensure the entire
        hierarchy is updated when needed.
        """
        self.rebuild_needed = True
        if self.parent is not None:
            self.parent.set_rebuild_needed()

    def rebuild(self) -> None:
        """Rebuild this node and all children that need rebuilding.

        This recursively rebuilds all child nodes and leaves that have been
        marked as needing rebuild.
        """
        for leaf in self.leaves:
            if (leaf.content & self.OctreeSystem) != 0:
                leaf.rebuild()
        for child in self.children:
            if child is not None and child.rebuild_needed:
                child.rebuild()
        self.rebuild_needed = False

    def traverse(self, traverser: AnchorTraverser) -> None:
        """Traverse this node and its children using the visitor pattern.

        Args:
            traverser: The traverser object that visits each node.
        """
        traverser.traverse_octree_node(self)
        for child in self.children:
            if child is not None and traverser.enter_octree_node(child):
                child.traverse(traverser)

    def add(self, leaf: StellarAnchor) -> None:
        """Add a stellar object as a leaf to the octree.

        Args:
            leaf: The stellar anchor to add to the octree.
        """
        self._add(leaf, leaf._global_position, leaf._intrinsic_luminosity)

    def get_child(self, index: int) -> OctreeNode | None:
        """Get a child node by its index.

        Args:
            index: The index of the child (0-7).

        Returns:
            The child node, or None if no child exists at that index.
        """
        return self.children[index]

    def get_leaf(self, index: int) -> StellarAnchor:
        """Get a leaf object by its index.

        Args:
            index: The index of the leaf in the leaves list.

        Returns:
            The stellar anchor at that index.
        """
        return self.leaves[index]

    def get_leaves(self) -> list[StellarAnchor]:
        """Get all leaf objects in this node.

        Returns:
            The list of stellar anchors contained in this node.
        """
        return self.leaves

    def _add_in_child(self, obj: StellarAnchor, position: LPoint3d, luminosity: float) -> None:
        index = 0
        if position.x >= self.center.x:
            index |= 1
        if position.y >= self.center.y:
            index |= 2
        if position.z >= self.center.z:
            index |= 4
        if self.children[index] is None:
            child_offset = self.width / 4.0
            child_center = LPoint3d(self.center)
            if (index & 1) != 0:
                child_center.x += child_offset
            else:
                child_center.x -= child_offset
            if (index & 2) != 0:
                child_center.y += child_offset
            else:
                child_center.y -= child_offset
            if (index & 4) != 0:
                child_center.z += child_offset
            else:
                child_center.z -= child_offset
            child = OctreeNode(
                self.level + 1, self, child_center, self.width / 2.0, self.threshold * self.child_factor, index
            )
            self.children[index] = child
        self.children[index]._add(obj, position, luminosity)

    def _add(self, obj: StellarAnchor, position: LPoint3d, luminosity: float) -> None:
        self.nb_leaves += 1
        if luminosity > self.max_luminosity:
            self.max_luminosity = luminosity
        if not self.has_children or luminosity > self.threshold:
            self.leaves.append(obj)
        else:
            self._add_in_child(obj, position, luminosity)
        if self.level < self.max_level and len(self.leaves) >= self.max_leaves and not self.has_children:
            self._split()

    def _split(self) -> None:
        new_leaves = []
        center = self.center
        for leaf in self.leaves:
            position = leaf._global_position
            if leaf._intrinsic_luminosity > self.threshold or (center - position).length() < leaf.bounding_radius:
                new_leaves.append(leaf)
            else:
                self._add_in_child(leaf, position, leaf._intrinsic_luminosity)
        self.leaves = new_leaves
        self.has_children = True

    def dump_octree_summary(self) -> None:
        """Print a summary of the octree structure to stdout."""
        if len(self.leaves) > 0:
            print(' ' * self.level, self.level, self.index, self.width, self.threshold, len(self.leaves), self.center)
        for i in range(8):
            if self.children[i] is not None:
                self.children[i].dump_octree_summary()

    def dump_octree(self) -> None:
        """Print detailed octree information including leaf names to stdout."""
        if len(self.leaves) > 0:
            print('  ' * self.level, self.level, self.index, self.width, self.threshold, self.center, self.has_children)
            print(
                '  ' * self.level,
                '->',
                self.max_luminosity,
                ":",
                ', '.join(map(lambda x: x.body.get_name(), self.leaves)),
            )
        for i in range(8):
            if self.children[i] is not None:
                self.children[i].dump_octree()

    def print_stats(self) -> None:
        """Print octree statistics including cell and leaf counts."""
        print("Nb cells:", self.nb_cells)
        print("Nb leaves:", self.nb_leaves)
