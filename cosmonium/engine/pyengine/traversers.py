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

"""Visitor pattern traversers for the anchor hierarchy.

This module provides traverser classes that implement the visitor pattern for
traversing and processing the anchor graph. Traversers are used for tasks
such as updating object states, collecting visible objects, finding nearby systems,
and identifying light sources and shadow casters.
"""

from __future__ import annotations

from math import asin, pi
from typing import TYPE_CHECKING

from ..anchors import StellarAnchor

if TYPE_CHECKING:
    from panda3d.core import LPoint3d

    from .anchors import AnchorBase, CameraAnchor, SystemAnchor
    from .octree import OctreeNode


class AnchorTraverser:
    """Base visitor class for traversing the anchor hierarchy.

    This abstract base class defines the interface for traverser objects that
    visit nodes in the anchor graph. Subclasses implement specific
    traversal behaviors for different purposes.
    """

    def traverse_anchor(self, anchor: AnchorBase) -> None:
        """Visit a single anchor node.

        Args:
            anchor: The anchor to visit.
        """
        pass

    def enter_system(self, anchor: SystemAnchor) -> bool:
        """Determine whether to enter and traverse a system anchor's children.

        Args:
            anchor: The system anchor being evaluated.

        Returns:
            True if the system's children should be traversed.
        """
        return False

    def traverse_system(self, anchor: SystemAnchor) -> None:
        """Visit all children of a system anchor.

        Args:
            anchor: The system anchor whose children should be visited.
        """
        pass

    def enter_octree_node(self, node: OctreeNode) -> bool:
        """Determine whether to enter and traverse an octree node's children.

        Args:
            node: The octree node being evaluated.

        Returns:
            True if the node's children should be traversed.
        """
        return False

    def traverse_octree_node(self, node: OctreeNode) -> None:
        """Visit the leaves of an octree node.

        Args:
            node: The octree node whose leaves should be visited.
        """
        pass


class UpdateTraverser(AnchorTraverser):
    """Traverser for updating anchor states and collecting visible objects.

    This traverser updates the state of all anchors based on the current time
    and observer position, and collects a list of visible objects for rendering.
    """

    def __init__(self, time: float, observer: CameraAnchor, lowest_radiance: float, update_id: int) -> None:
        """Initialize the UpdateTraverser.

        Args:
            time: The current simulation time.
            observer: The camera/observer anchor.
            lowest_radiance: The minimum radiance threshold for visibility.
            update_id: A unique identifier for this update pass.
        """
        self.time = time
        self.observer = observer
        self.lowest_radiance = lowest_radiance
        self.update_id = update_id
        self.visibles = []

    def get_collected(self) -> list[AnchorBase]:
        """Get the list of visible anchors collected during traversal.

        Returns:
            The list of anchors that are visible.
        """
        return self.visibles

    def traverse_anchor(self, anchor: AnchorBase) -> None:
        # if anchor.update_id == self.update_id: return
        anchor.update_all(self.time, self.observer, self.update_id)
        anchor.update_id = self.update_id
        if anchor.visible or anchor.visibility_override:
            self.visibles.append(anchor)

    def enter_system(self, anchor: SystemAnchor) -> bool:
        self.traverse_anchor(anchor)
        return ((anchor.visible or anchor.visibility_override) and anchor.resolved) or anchor.force_update

    def traverse_system(self, anchor: SystemAnchor) -> None:
        for child in anchor.children:
            child.traverse(self)

    def enter_octree_node(self, octree_node: OctreeNode) -> bool:
        # TODO: Octree root must be separate from octree node. Use enter_system ?
        frustum = self.observer.frustum
        distance = (octree_node.center - frustum.get_position()).length() - octree_node.radius
        if distance <= 0.0:
            return True
        point_radiance = octree_node.max_luminosity / (4 * pi * distance * distance * 1000 * 1000)
        if point_radiance < self.lowest_radiance:
            return False
        return frustum.is_sphere_in(octree_node.center, octree_node.radius)

    def traverse_octree_node(self, octree_node: OctreeNode) -> None:
        frustum = self.observer.frustum
        frustum_position = frustum.get_position()
        distance = (octree_node.center - frustum_position).length() - octree_node.radius
        if distance > 0.0:
            lowest_luminosity = 4 * pi * distance * 1000 * 1000 * self.lowest_radiance
        else:
            lowest_luminosity = 0.0
        for leaf in octree_node.leaves:
            traverse = False
            if leaf._intrinsic_luminosity > lowest_luminosity:
                distance = (leaf._global_position - frustum_position).length()
                if distance > leaf.bounding_radius:
                    point_radiance = leaf._intrinsic_luminosity / (4 * pi * distance * distance * 1000 * 1000)
                    if point_radiance > self.lowest_radiance:
                        traverse = frustum.is_sphere_in(leaf._global_position, leaf.bounding_radius)
                else:
                    # We are inside the leaf object
                    traverse = True
            if traverse:
                leaf.traverse(self)


class FindClosestSystemTraverser(AnchorTraverser):
    """Traverser for finding the nearest stellar system to the observer.

    This traverser searches the anchor hierarchy to find the closest stellar
    system to the observer's current position.
    """

    def __init__(self, observer: CameraAnchor, system: AnchorBase, distance: float) -> None:
        """Initialize the FindClosestSystemTraverser.

        Args:
            observer: The camera/observer anchor.
            system: The initial closest system candidate.
            distance: The initial search distance.
        """
        self.observer = observer
        self._global_position = observer._global_position
        self.closest_system = system
        self.distance = distance

    def enter_system(self, anchor: SystemAnchor) -> bool:
        # We only enter octree systems
        return (anchor.content & StellarAnchor.OctreeAnchor) != 0

    def enter_octree_node(self, octree_node: OctreeNode) -> bool:
        # TODO: Check node content ?
        distance = (octree_node.center - self._global_position).length() - octree_node.radius
        return distance <= self.distance

    def traverse_octree_node(self, octree_node: OctreeNode) -> None:
        global_position = self.observer._global_position
        local_position = self.observer._local_position
        for leaf in octree_node.leaves:
            global_delta = leaf._global_position - global_position
            local_delta = leaf._local_position - local_position
            distance = (global_delta + local_delta).length()
            if (leaf.content & StellarAnchor.OctreeAnchor) != 0:
                if distance - leaf.bounding_radius < self.distance:
                    leaf.traverse(self)
            else:
                if distance < self.distance:
                    self.distance = distance
                    self.closest_system = leaf


class FindLightSourceTraverser(AnchorTraverser):
    """Traverser for discovering light sources affecting a region.

    This traverser identifies all emissive objects (stars) that contribute
    significant lighting to a given position in space.
    """

    def __init__(self, lowest_radiance: float, position: LPoint3d) -> None:
        """Initialize the FindLightSourceTraverser.

        Args:
            lowest_radiance: The minimum radiance threshold for light sources to be considered.
            position: The target position for which to find affecting light sources.
        """
        self.lowest_radiance = lowest_radiance
        self.position = position
        self.anchors = []

    def get_collected(self) -> list[AnchorBase]:
        """Get the list of light source anchors collected during traversal.

        Returns:
            The list of emissive anchors that affect the target position.
        """
        return self.anchors

    def traverse_anchor(self, anchor: AnchorBase) -> None:
        self.anchors.append(anchor)

    def enter_system(self, anchor: SystemAnchor) -> bool:
        # TODO: Is global position accurate enough ?
        global_delta = anchor._global_position - self.position
        if anchor.content & StellarAnchor.Emissive != 0:
            distance = (global_delta).length()
            if distance > anchor.bounding_radius:
                point_radiance = anchor._intrinsic_luminosity / (4 * pi * distance * distance * 1000 * 1000)
                return point_radiance > self.lowest_radiance
            else:
                # We are inside the system
                return True
        else:
            return False

    def traverse_system(self, anchor: SystemAnchor) -> None:
        for child in anchor.children:
            if child.content & StellarAnchor.Emissive == 0:
                continue
            # TODO: Is global position accurate enough ?
            global_delta = child._global_position - self.position
            distance = (global_delta).length()
            if distance > 0:
                point_radiance = child._intrinsic_luminosity / (4 * pi * distance * distance * 1000 * 1000)
                if point_radiance > self.lowest_radiance:
                    child.traverse(self)
            else:
                child.traverse(self)

    def enter_octree_node(self, octree_node: OctreeNode) -> bool:
        # TODO: Check node content ?
        distance = (octree_node.center - self.position).length() - octree_node.radius
        if distance <= 0.0:
            return True
        point_radiance = octree_node.max_luminosity / (4 * pi * distance * distance * 1000 * 1000)
        if point_radiance < self.lowest_radiance:
            return False
        return True

    def traverse_octree_node(self, octree_node: OctreeNode) -> None:
        distance = (octree_node.center - self.position).length() - octree_node.radius
        if distance > 0.0:
            lowest_luminosity = 4 * pi * distance * 1000 * 1000 * self.lowest_radiance
        else:
            lowest_luminosity = 0.0
        for leaf in octree_node.leaves:
            if leaf._intrinsic_luminosity > lowest_luminosity:
                distance = (leaf._global_position - self.position).length()
                if distance > leaf.bounding_radius:
                    point_radiance = leaf._intrinsic_luminosity / (4 * pi * distance * distance * 1000 * 1000)
                    if point_radiance > self.lowest_radiance:
                        leaf.traverse(self)
                else:
                    # We are inside the leaf object
                    leaf.traverse(self)


class FindShadowCastersTraverser(AnchorTraverser):
    """Traverser for identifying objects that cast shadows.

    This traverser finds all objects that can cast a shadow on a target body
    from a given light source, taking into account the angular sizes and
    positions of all objects.
    """

    def __init__(self, target: AnchorBase, light_position: LPoint3d, light_source_radius: float) -> None:
        """Initialize the FindShadowCastersTraverser.

        Args:
            target: The anchor representing the target body that may receive shadows.
            light_position: The position of the light source casting shadows.
            light_source_radius: The radius of the light source, used to calculate angular size.
        """
        self.target = target
        self.body_position = target._local_position
        self.body_bounding_radius = target.bounding_radius
        self.vector_to_light_source = light_position - self.body_position
        self.distance_to_light_source = self.vector_to_light_source.length()
        self.vector_to_light_source /= self.distance_to_light_source
        self.light_source_angular_radius = asin(
            light_source_radius / (self.distance_to_light_source - self.body_bounding_radius)
        )
        self.anchors = []
        self.parent_systems = []
        parent = target.parent
        while parent is not None and parent.content != ~0:
            self.parent_systems.append(parent)
            parent = parent.parent

    def get_collected(self) -> list[AnchorBase]:
        """Get the list of shadow caster anchors collected during traversal.

        Returns:
            The list of anchors that cast shadows on the target.
        """
        return self.anchors

    def check_cast_shadow(self, occluder: AnchorBase) -> bool:
        """Check if an occluder casts a shadow on the target.

        Args:
            occluder: The potential shadow-casting anchor.

        Returns:
            True if the occluder casts a shadow on the target.
        """
        cast_shadow = False
        occluder_position = occluder._local_position
        occluder_bounding_radius = occluder.bounding_radius
        relative_position = occluder_position - self.body_position
        t = self.vector_to_light_source.dot(relative_position)
        # print(occluder.body.get_name(), t)
        if t >= 0 and t <= self.distance_to_light_source:
            distance = relative_position.length() - self.body_bounding_radius
            occluder_angular_radius = (
                asin(occluder_bounding_radius / distance) if occluder_bounding_radius < distance else pi / 2
            )
            ar_ratio = occluder_angular_radius / self.light_source_angular_radius
            # print(occluder.body.get_name(), "D", distance, "AR", occluder_angular_radius, "R", ar_ratio)
            # TODO: No longer valid if we are using HDR
            # If the shadow coef is smaller than the min change in pixel color
            # the umbra will have no visible impact
            if ar_ratio * ar_ratio > 1.0 / 255:
                distance_to_projection = (relative_position - self.vector_to_light_source * t).length()
                penumbra_radius = (1 + ar_ratio) * occluder_bounding_radius
                # TODO: Should check also the visible size of the penumbra
                if distance_to_projection < penumbra_radius + self.body_bounding_radius:
                    # print(occluder.body.get_name(), "casts shadows on", self.target.body.get_name())
                    cast_shadow = True
        return cast_shadow

    def traverse_anchor(self, anchor: AnchorBase) -> None:
        if anchor != self.target and anchor.content & StellarAnchor.Reflective != 0 and self.check_cast_shadow(anchor):
            self.anchors.append(anchor)

    def enter_system(self, anchor: SystemAnchor) -> bool:
        enter = anchor in self.parent_systems or (
            anchor.content & StellarAnchor.Reflective != 0 and self.check_cast_shadow(anchor)
        )
        # TODO: We should trigger update here if needed (using update_id) instead of deferring update to next frame
        anchor.force_update = enter
        return enter

    def traverse_system(self, anchor: SystemAnchor) -> None:
        for child in anchor.children:
            child.traverse(self)
