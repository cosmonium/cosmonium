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

"""Anchor classes for the 3D space simulation.

This module provides the Python implementation of anchor classes that represent
positions and orientations in the 3D space simulation. Anchors form a hierarchical
graph for celestial objects, handling coordinate transformations, visibility
determination, and observer-relative calculations.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from math import pi, sqrt
from typing import TYPE_CHECKING

from panda3d.core import LColor, LPoint3d, LQuaterniond, LVector3d

from ... import settings
from ...astro import units
from ...astro.astro import abs_mag_to_lum, abs_to_app_mag, app_to_abs_mag, lum_to_abs_mag
from ...astro.frame import AbsoluteReferenceFrame
from ...mathutil.quaternion import relative_rotation
from ..octree import OctreeNode
from .objectname import ObjectNames

if TYPE_CHECKING:
    from ...astro.frame import ReferenceFrame
    from ...astro.orbits import OrbitBase
    from ...astro.rotations import RotationBase
    from .traversers import AnchorTraverser


class AnchorBase(ABC):
    """Base class for all anchor types in the 3D space simulation.

    An anchor represents a position and orientation in the 3D space simulation.
    It handles visibility determination, observer-relative calculations, reference
    frame transformations and luminosity calculations for both intrinsic and reflected
    light, and hierarchical parent-child relationships.
    Anchors form the foundation of the graph for simulation and rendering.
    """

    def __init__(
        self,
        anchor_class: int,
        body: object,
        point_color: LColor | None = None,
        names: list[str] | str | None = None,
        source_names: list[str] | None = None,
        description: str = '',
    ) -> None:
        """Initialize the anchor.

        Args:
            anchor_class: Bitmask defining the anchor's classification.
            body: The celestial body associated with this anchor.
            point_color: Color for point rendering.
            names: Translated name(s) for this anchor. Can be a single name or a list of names.
            source_names: List of source (untranslated) names corresponding to the provided names.
            description: Optional description for this anchor.
        """
        self.content = anchor_class
        self.body = body
        self.parent = None
        self.rebuild_needed = False
        if point_color is None:
            point_color = LColor(1.0, 1.0, 1.0, 1.0)
        self.point_color = point_color
        # Name management
        self.object_names = ObjectNames()
        if names is None:
            self.object_names.add_name(ObjectNames.parse_name(''))
        elif isinstance(names, (list, tuple)):
            # Parse names and associate with source_names if provided
            source_list = source_names if source_names is not None else []
            for i, name in enumerate(names):
                parsed = ObjectNames.parse_name(name)
                # If there's a corresponding source name, use it as the original
                if i < len(source_list):
                    self.object_names.add_name(parsed, source_list[i])
                else:
                    self.object_names.add_name(parsed)
        else:
            # Single name
            self.object_names.add_name(ObjectNames.parse_name(names))

        self.description = description
        # Scene anchor (set by StellarObject or SceneWorld)
        self.scene_anchor = None
        # Flags
        self.visible = False
        self.visibility_override = False
        self.resolved = False
        self.update_id = -1
        self.update_frozen = False
        self.force_update = False
        # Cached values
        self._position = LPoint3d()
        self._global_position = LPoint3d()
        self._local_position = LPoint3d()
        self._orientation = LQuaterniond()
        self.bounding_radius = 0.0
        self._height_under = 0.0
        # Luminosity / radiance
        self._albedo = 0.5
        self._intrinsic_luminosity = 0.0
        self._reflected_luminosity = 0.0
        self._point_radiance = 0.0
        # Scene parameters
        self.rel_position = LPoint3d()
        self.distance_to_obs = 0
        self.vector_to_obs = LVector3d()
        self.visible_size = 0.0
        self.z_distance = 0.0
        # If this anchor is the primary body of a stellar system, this will point to the system anchor
        self.system: SystemAnchor | None = None

    def get_names(self) -> list[str]:
        """Get all translated names for this anchor.

        Returns:
            List of translated name strings.
        """
        return self.object_names.get_all_names()

    def set_names(self, names: list[str] | str | None) -> None:
        """Set the anchor's translated names.

        Args:
            names: Single name, list of names, or None.
        """
        # Rebuild object_names from scratch
        self.object_names = ObjectNames()
        if names is None:
            self.object_names.add_name(ObjectNames.parse_name(''))
        elif isinstance(names, (list, tuple)):
            for name in names:
                self.object_names.add_name(ObjectNames.parse_name(name))
        else:
            self.object_names.add_name(ObjectNames.parse_name(names))

    def get_source_names(self) -> list[str]:
        """Get the original (untranslated) names.

        Returns:
            List of source name strings.
        """
        return self.object_names.get_source_names()

    def _is_named(self, name_up: str) -> bool:
        """Check whether this anchor matches the given upper-case name.

        Args:
            name_up: An already-uppercased name string.

        Returns:
            True if any translated or source name matches.
        """
        for name in self.get_names():
            if name.upper() == name_up:
                return True
        for name in self.get_source_names():
            if name.upper() == name_up:
                return True
        return False

    def get_name(self) -> str:
        """Get the primary name for this anchor.

        Returns:
            The primary name string.
        """
        return self.object_names.get_name()

    def get_c_name(self) -> str:
        """Get the C-style identifier for this anchor.

        Returns:
            The C-name identifier.
        """
        return self.object_names.get_c_name()

    def get_description(self) -> str:
        """Get the description of this anchor.

        Returns:
            The anchor's description string.
        """
        return self.description

    def get_point_color(self) -> LColor:
        """Get the point color used for rendering.

        Returns:
            The point color.
        """
        return self.point_color

    def set_point_color(self, color: LColor) -> None:
        """Set the point color used for rendering.

        Args:
            color: The new point color.
        """
        self.point_color = color

    def get_albedo(self) -> float:
        """Get the albedo (reflectivity fraction).

        Returns:
            The albedo value.
        """
        return self._albedo

    def set_albedo(self, albedo: float) -> None:
        """Set the albedo.

        Args:
            albedo: The new albedo value.
        """
        self._albedo = albedo

    def get_intrinsic_luminosity(self) -> float:
        """Get the intrinsic (emitted) luminosity in Watts.

        Returns:
            The intrinsic luminosity.
        """
        return self._intrinsic_luminosity

    def set_intrinsic_luminosity(self, intrinsic_luminosity: float) -> None:
        """Set the intrinsic luminosity.

        Args:
            intrinsic_luminosity: The new intrinsic luminosity in Watts.
        """
        self._intrinsic_luminosity = intrinsic_luminosity

    def get_reflected_luminosity(self) -> float:
        """Get the reflected luminosity in Watts.

        Returns:
            The reflected luminosity.
        """
        return self._reflected_luminosity

    def get_cached_point_radiance(self) -> float:
        """Get the cached point radiance.

        Returns:
            The cached point radiance value.
        """
        return self._point_radiance

    def get_radiant_flux(self) -> float:
        """Get the total radiant flux (intrinsic + reflected) in Watts.

        Returns:
            The total radiant flux.
        """
        return self._intrinsic_luminosity + self._reflected_luminosity

    def get_point_radiance(self, distance: float) -> float:
        """Get the point radiance at a given distance.

        This method assumes the source is a point-like light source aligned
        with the normal of the receiver.

        Args:
            distance: The distance in kilometers.

        Returns:
            The radiance at the given distance.
        """
        return (self._intrinsic_luminosity + self._reflected_luminosity) / (4 * pi * distance * distance * 1000 * 1000)

    def get_cached_absolute_position(self) -> LPoint3d:
        """Get the cached absolute (global) position.

        Returns:
            The last computed absolute position.
        """
        return self._global_position

    def get_cached_local_position(self) -> LPoint3d:
        """Get the cached local position.

        Returns:
            The last computed local position.
        """
        return self._local_position

    def get_cached_absolute_orientation(self) -> LQuaterniond:
        """Get the cached absolute orientation.

        Returns:
            The last computed absolute orientation.
        """
        return self._orientation

    @abstractmethod
    def get_position_bounding_radius(self) -> float:
        """Get the bounding radius of the orbit/position trajectory.

        Returns:
            The position bounding radius.
        """

    @abstractmethod
    def get_absolute_reference_point(self) -> LPoint3d:
        """Get the absolute (global) reference point of this anchor.

        Returns:
            The absolute reference point.
        """

    @abstractmethod
    def get_absolute_position(self) -> LPoint3d:
        """Get the absolute position (reference point + local position).

        Returns:
            The absolute position.
        """

    @abstractmethod
    def get_local_position(self) -> LPoint3d:
        """Get the position relative to the reference point.

        Returns:
            The local position.
        """

    @abstractmethod
    def get_frame_position(self) -> LPoint3d:
        """Get the position expressed in the reference frame coordinates.

        Returns:
            The frame-relative position.
        """

    @abstractmethod
    def get_absolute_orientation(self) -> LQuaterniond:
        """Get the absolute orientation.

        Returns:
            The absolute orientation quaternion.
        """

    @abstractmethod
    def update_luminosity(self, star=None) -> None:
        """Update luminosity values based on a stellar light source.

        Args:
            star: The stellar anchor acting as the light source, or None.
        """

    def set_rebuild_needed(self) -> None:
        """Mark this anchor as needing rebuild and propagate to parent."""
        self.rebuild_needed = True
        if self.parent is not None:
            self.parent.set_rebuild_needed()

    @abstractmethod
    def rebuild(self) -> None:
        """Rebuild this anchor's internal state."""

    @abstractmethod
    def traverse(self, visitor: AnchorTraverser) -> None:
        """Accept a visitor for traversal.

        Args:
            visitor: The traverser object visiting this anchor.
        """

    @abstractmethod
    def is_stellar(self) -> bool:
        """Check if this anchor represents a stellar object.

        Returns:
            True if this is a stellar anchor.
        """

    @abstractmethod
    def has_orbit(self) -> bool:
        """Check if this anchor position is based on an orbit.

        Returns:
            True if this anchor has orbital motion.
        """

    @abstractmethod
    def has_rotation(self) -> bool:
        """Check if this anchor orientation is based on rotation.

        Returns:
            True if this anchor has rotational motion.
        """

    @abstractmethod
    def has_frame(self) -> bool:
        """Check if this anchor has a reference frame.

        Returns:
            True if this anchor has a reference frame.
        """

    def is_system(self) -> bool:
        """Return whether this anchor represents a stellar system.

        Returns:
            False for non-system anchors; overridden in SystemAnchor.
        """
        return False

    def get_bounding_radius(self) -> float:
        """Get the bounding radius of this anchor.

        Returns:
            The bounding radius (in kilometers).
        """
        return self.bounding_radius

    def set_bounding_radius(self, bounding_radius: float) -> None:
        """Set the bounding radius of this anchor.

        Args:
            bounding_radius: The new bounding radius in kilometers.
        """
        self.bounding_radius = bounding_radius

    def get_apparent_radius(self) -> float:
        """Get the apparent radius for rendering.

        Returns:
            The apparent radius, same as bounding radius by default.
        """
        return self.get_bounding_radius()

    def calc_absolute_relative_position_to(self, position: LPoint3d) -> LPoint3d:
        """Calculate the absolute position relative to a given point.

        Args:
            position: The reference point to calculate the relative position from.

        Returns:
            The absolute position relative to the given point.
        """
        return (self.get_absolute_reference_point() - position) + self.get_local_position()

    def calc_absolute_relative_position(self, anchor: AnchorBase) -> LPoint3d:
        """Calculate the relative position between this anchor and another.

        Args:
            anchor: The other anchor to calculate the relative position to.

        Returns:
            The position vector from this anchor to the other.
        """
        reference_point_delta = anchor.get_absolute_reference_point() - self.get_absolute_reference_point()
        local_delta = anchor.get_local_position() - self.get_local_position()
        delta = reference_point_delta + local_delta
        return delta

    def calc_local_distance_to(self, anchor: AnchorBase) -> tuple[LVector3d, float]:
        """Calculate the normalized direction and distance to another anchor.

        Args:
            anchor: The other anchor to calculate distance to.

        Returns:
            The normalized direction vector and distance as a tuple.
        """
        local_delta = anchor.get_local_position() - self.get_local_position()
        length = local_delta.length()
        return (local_delta / length, length)

    @abstractmethod
    def update(self, time: float, update_id: int) -> None:
        """Update the anchor's state for the current time.

        Args:
            time: The current simulation time.
            update_id: The unique identifier for this update pass.
        """

    @abstractmethod
    def update_observer(self, observer, update_id: int) -> None:
        """Update observer-relative position and visibility metrics.

        Args:
            observer: The observer/camera anchor.
            update_id: The unique identifier for this update pass.
        """

    @abstractmethod
    def update_state(self, observer, update_id: int) -> None:
        """Update the anchor's visibility and resolved state.

        Args:
            observer: The observer/camera anchor.
            update_id: The unique identifier for this update pass.
        """

    def update_all(self, time: float, observer, update_id: int) -> None:
        """Update all anchor states: time, observer, and visibility.

        Args:
            time: The current simulation time.
            observer: The observer/camera anchor.
            update_id: The unique identifier for this update pass.
        """
        self.update(time, update_id)
        self.update_observer(observer, update_id)
        self.update_state(observer, update_id)


class CartesianAnchor(AnchorBase):
    """Anchor with Cartesian coordinate positioning in a reference frame.

    This anchor represents objects that use Cartesian coordinates within a
    reference frame (e.g., surface-bound objects, spacecraft).
    """

    def __init__(
        self,
        anchor_class: int,
        body: object,
        frame: ReferenceFrame,
        point_color: LColor | None = None,
        names: list[str] | str | None = None,
        source_names: list[str] | None = None,
        description: str = '',
    ) -> None:
        """Initialize the Cartesian anchor.

        Args:
            anchor_class: Bitmask defining the anchor's classification.
            body: The celestial body associated with this anchor.
            frame: The reference frame for coordinate transformations.
            point_color: Optional color for point rendering.
            names: Translated name(s) for this anchor. Can be a single name or a list of names.
            source_names: List of source (untranslated) names corresponding to the provided names.
            description: Optional description for this anchor.
        """
        AnchorBase.__init__(self, anchor_class, body, point_color, names, source_names, description)
        self.frame = frame
        self._frame_position = LPoint3d()
        self._frame_orientation = LQuaterniond()

    def is_stellar(self) -> bool:
        return False

    def has_orbit(self) -> bool:
        return False

    def has_rotation(self) -> bool:
        return False

    def has_frame(self) -> bool:
        return True

    def rebuild(self) -> None:
        pass

    def traverse(self, visitor) -> None:
        visitor.traverse_anchor(self)

    def do_update(self) -> None:
        """Update cached position and orientation from frame coordinates."""
        # TODO: _position should be global + local !
        self._position = self.get_local_position()
        self._local_position = self.get_local_position()
        self._orientation = self.get_absolute_orientation()

    def update(self, time: float, update_id: int) -> None:
        self.do_update()

    def update_observer(self, observer, update_id: int) -> None:
        """Update observer-relative position and visibility metrics."""
        if self.update_id == update_id:
            return
        reference_point_delta = self.get_absolute_reference_point() - observer.get_absolute_reference_point()
        local_delta = self.get_local_position() - observer.get_local_position()
        self.rel_position = reference_point_delta + local_delta
        self.distance_to_obs = self.rel_position.length()
        if self.distance_to_obs > 0.0:
            self.vector_to_obs = -self.rel_position / self.distance_to_obs
            self.visible_size = self.bounding_radius / (self.distance_to_obs * observer.pixel_size)
            coef = -self.vector_to_obs.dot(observer.camera_vector)
            self.z_distance = self.distance_to_obs * coef
        else:
            self.vector_to_obs = LVector3d()
            self.visible_size = 0.0
            self.z_distance = 0.0

    def update_state(self, observer, update_id: int) -> None:
        """Update the anchor's visibility and resolved state."""
        if self.distance_to_obs > self.bounding_radius:
            in_view = observer.rel_frustum.is_sphere_in(self.rel_position, self.bounding_radius)
            resolved = self.visible_size > settings.min_body_size
            visible = in_view  # and (visible_size > 1.0 or self._app_magnitude < settings.lowest_app_magnitude)
        else:
            # We are in the object
            resolved = True
            visible = True
        self.visible = visible
        self.resolved = resolved

    def copy(self, other: CartesianAnchor) -> None:
        """Copy state from another CartesianAnchor.

        Args:
            other: The anchor to copy from.
        """
        self.frame = other.get_frame()
        self._global_position = other.get_absolute_reference_point()
        self._frame_position = other.get_frame_position()
        self._frame_orientation = other.get_frame_orientation()

    def get_frame(self) -> ReferenceFrame:
        """Get the reference frame for this anchor.

        Returns:
            The reference frame object.
        """
        return self.frame

    def set_frame(self, frame: ReferenceFrame) -> None:
        """Set the reference frame for this anchor.

        Args:
            frame: The new reference frame.
        """
        # Get position and rotation in the absolute reference frame
        pos = self.get_local_position()
        rot = self.get_absolute_orientation()
        # Update reference frame
        self.frame = frame
        # Set back the position to calculate the position in the new reference frame
        self.set_local_position(pos)
        self.set_absolute_orientation(rot)

    def get_position_bounding_radius(self) -> float:
        """Get the bounding radius of the position trajectory."""
        return 0.0

    def update_luminosity(self, star=None) -> None:
        """Update luminosity values based on a stellar light source."""
        pass

    def set_absolute_reference_point(self, new_reference_point: LPoint3d) -> None:
        """Set the absolute reference point.

        Args:
            new_reference_point: The new absolute reference point.
        """
        if new_reference_point == self._global_position:
            return
        old_local = self.frame.get_local_position(self._frame_position)
        new_local = (self._global_position - new_reference_point) + old_local
        self._global_position = new_reference_point
        self._frame_position = self.frame.get_frame_position(new_local)
        self.do_update()

    def set_frame_position(self, position: LPoint3d) -> None:
        """Set the position in frame coordinates.

        Args:
            position: The new frame position.
        """
        self._frame_position = position

    def get_frame_position(self) -> LPoint3d:
        """Get the position in frame coordinates.

        Returns:
            The frame-relative position.
        """
        return self._frame_position

    def set_frame_orientation(self, rotation: LQuaterniond) -> None:
        """Set the orientation in frame coordinates.

        Args:
            rotation: The new frame-relative orientation.
        """
        self._frame_orientation = rotation

    def get_frame_orientation(self) -> LQuaterniond:
        """Get the orientation in frame coordinates.

        Returns:
            The frame-relative orientation.
        """
        return self._frame_orientation

    def get_local_position(self) -> LPoint3d:
        """Get the position relative to the reference point.

        Returns:
            The local position.
        """
        return self.frame.get_local_position(self._frame_position)

    def set_local_position(self, position: LPoint3d) -> None:
        """Set the position relative to the reference point.

        Args:
            position: The new local position.
        """
        self._frame_position = self.frame.get_frame_position(position)

    def get_absolute_reference_point(self) -> LPoint3d:
        """Get the absolute reference point.

        Returns:
            The absolute reference point for this anchor.
        """
        return self._global_position

    def get_absolute_position(self) -> LPoint3d:
        """Get the absolute position (reference point + local position).

        Returns:
            The absolute position.
        """
        return self._global_position + self.get_local_position()

    def set_absolute_position(self, position: LPoint3d) -> None:
        """Set the absolute position.

        Args:
            position: The new absolute position.
        """
        position -= self._global_position
        self._frame_position = self.frame.get_frame_position(position)

    def get_absolute_orientation(self) -> LQuaterniond:
        """Get the absolute orientation.

        Returns:
            The absolute orientation.
        """
        return self.frame.get_absolute_orientation(self._frame_orientation)

    def set_absolute_orientation(self, orientation: LQuaterniond) -> None:
        """Set the absolute orientation.

        Args:
            orientation: The new absolute orientation.
        """
        self._frame_orientation = self.frame.get_frame_orientation(orientation)

    def calc_absolute_position_of(self, frame_position: LPoint3d) -> LPoint3d:
        """Calculate the absolute position of a point given in frame coordinates.

        Args:
            frame_position: Position in frame coordinates.

        Returns:
            The absolute position.
        """
        return self._global_position + self.frame.get_local_position(frame_position)

    def calc_relative_position_to(self, position: LPoint3d) -> LPoint3d:
        """Calculate position relative to a reference point.

        Args:
            position: The reference point.

        Returns:
            The relative position.
        """
        return (self._global_position - position) + self.get_local_position()

    def calc_local_position_of_frame(self, frame_position: LPoint3d) -> LPoint3d:
        """Convert frame coordinates to local coordinates.

        Args:
            frame_position: Position in frame coordinates.

        Returns:
            The local position.
        """
        return self.frame.get_local_position(frame_position)

    def calc_frame_position_of_absolute(self, position: LPoint3d) -> LPoint3d:
        """Convert absolute position to frame coordinates.

        Args:
            position: Position in absolute coordinates.

        Returns:
            The frame-relative position.
        """
        return self.frame.get_frame_position(position - self._global_position)

    def calc_frame_position_of_local(self, position: LPoint3d) -> LPoint3d:
        """Convert local position to frame coordinates.

        Args:
            position: Position in local coordinates.

        Returns:
            The frame-relative position.
        """
        return self.frame.get_frame_position(position)

    def calc_frame_orientation_of(self, orientation: LQuaterniond) -> LQuaterniond:
        """Convert absolute orientation to frame-relative orientation.

        Args:
            orientation: Orientation in absolute coordinates.

        Returns:
            The frame-relative orientation.
        """
        return self.frame.get_frame_orientation(orientation)

    def calc_look_at2(self, target, rel=True, position=None):
        if not rel:
            if position is None:
                position = self.get_pos()
            direction = LVector3d(target - position)
        else:
            direction = LVector3d(target)
        direction.normalize()
        local_direction = self.get_absolute_orientation().conjugate().xform(direction)
        angle = LVector3d.forward().angleRad(local_direction)
        axis = LVector3d.forward().cross(local_direction)
        if axis.length() > 0.0:
            new_rot = relative_rotation(self.get_absolute_orientation(), axis, angle)
        #         new_rot=LQuaterniond()
        #         lookAt(new_rot, direction, LVector3d.up())
        else:
            new_rot = self.get_absolute_orientation()
        return new_rot, angle


class CameraAnchor(CartesianAnchor):
    """Specialized anchor to represent the observer/camera in the 3D space simulation."""

    def __init__(self, body: object, frame: ReferenceFrame) -> None:
        """Initialize the CameraAnchor.

        Args:
            body: The body associated with the camera (usually None or observer).
            frame: The reference frame for the camera.
        """
        CartesianAnchor.__init__(self, 0, body, frame, LColor(0))
        self.camera_vector = LVector3d()
        self.frustum = None
        self.rel_frustum = None
        self.pixel_size = 0.0

    def do_update(self) -> None:
        """Update camera vector from absolute orientation."""
        CartesianAnchor.do_update(self)
        self.camera_vector = self.get_absolute_orientation().xform(LVector3d.forward())


class OriginAnchor(CartesianAnchor):
    """Anchor positioned at the origin of the absolute reference frame.

    This anchor uses the absolute reference frame, making it suitable for
    objects that don't need frame transformations.
    """

    def __init__(
        self,
        anchor_class: int,
        body: object,
        names: list[str] | str | None = None,
        source_names: list[str] | None = None,
        description: str = '',
    ) -> None:
        """Initialize the OriginAnchor.

        Args:
            anchor_class: Bitmask defining the anchor's classification.
            body: The celestial body associated with this anchor.
            names: Translated name(s) for this anchor. Can be a single name or a list of names.
            source_names: List of source (untranslated) names corresponding to the provided names.
            description: Optional description for this anchor.
        """
        CartesianAnchor.__init__(
            self, anchor_class, body, AbsoluteReferenceFrame(), LColor(0), names, source_names, description
        )


class FlatSurfaceAnchor(OriginAnchor):
    """Anchor for objects on flat surfaces."""

    def __init__(
        self,
        anchor_class: int,
        body: object,
        surface: object,
        names: list[str] | str | None = None,
        source_names: list[str] | None = None,
        description: str = '',
    ) -> None:
        """Initialize the FlatSurfaceAnchor.

        Args:
            anchor_class: Bitmask defining the anchor's classification.
            body: The celestial body associated with this anchor.
            surface: The surface object this anchor is attached to.
            names: Translated name(s) for this anchor. Can be a single name or a list of names.
            source_names: List of source (untranslated) names corresponding to the provided names.
            description: Optional description for this anchor.
        """
        OriginAnchor.__init__(self, anchor_class, body, names, source_names, description)
        self.surface = surface

    def set_surface(self, surface) -> None:
        """Set the surface for this anchor.

        Args:
            surface: The surface object to attach to.
        """
        self.surface = surface

    def update_observer(self, observer, update_id: int) -> None:
        """Update observer-relative position and visibility metrics."""
        if self.update_id == update_id:
            return
        self.vector_to_obs = LVector3d(observer.get_local_position())
        self.vector_to_obs.normalize()
        observer_local_position = observer.get_local_position()
        self.rel_position = self._local_position - observer_local_position
        self.distance_to_obs = self.rel_position.length()
        self.visible_size = 0.0
        self.z_distance = 0.0

    def update_state(self, observer, update_id: int) -> None:
        """Update the anchor's visibility and resolved state."""
        self.visible = True
        self.resolved = True


class ObserverAnchor(CartesianAnchor):
    """Anchor that follows the observer position.

    This anchor is used for objects that should remain at the observer's
    position.
    """

    def __init__(
        self,
        anchor_class: int,
        body: object,
        names: list[str] | str | None = None,
        source_names: list[str] | None = None,
        description: str = '',
    ) -> None:
        """Initialize the ObserverAnchor.

        Args:
            anchor_class: Bitmask defining the anchor's classification.
            body: The celestial body associated with this anchor.
            names: Translated name(s) for this anchor. Can be a single name or a list of names.
            source_names: List of source (untranslated) names corresponding to the provided names.
            description: Optional description for this anchor.
        """
        CartesianAnchor.__init__(
            self, anchor_class, body, AbsoluteReferenceFrame(), LColor(0), names, source_names, description
        )

    def update(self, time: float, update_id: int) -> None:
        # Do nothing
        pass

    def update_observer(self, observer, update_id: int) -> None:
        """Update observer-relative position and visibility metrics."""
        if self.update_id == update_id:
            return
        self.copy(observer)
        self.distance_to_obs = 0.0
        self.vector_to_obs = LVector3d()
        self.visible_size = 0.0
        self.z_distance = 0.0

    def update_state(self, observer, update_id: int) -> None:
        """Update the anchor's visibility and resolved state."""
        self.visible = True
        self.resolved = True


class StellarAnchor(AnchorBase):
    """Anchor for celestial bodies with orbital mechanics.

    This anchor represents celestial bodies that have orbital and rotational
    dynamics. It includes support for luminosity calculations, both intrinsic
    (for stars) and reflected (for planets/moons).
    """

    Emissive: int = 1
    Reflective: int = 2
    System: int = 4
    OctreeAnchor: int = 8

    def __init__(
        self,
        anchor_class: int,
        body: object,
        orbit: OrbitBase,
        rotation: RotationBase,
        point_color: LColor,
        names: list[str] | str | None = None,
        source_names: list[str] | None = None,
        description: str = '',
    ) -> None:
        """Initialize the StellarAnchor.

        Args:
            anchor_class: Bitmask defining the anchor's classification.
            body: The celestial body associated with this anchor.
            orbit: The orbital component defining the body's motion.
            rotation: The rotational component defining the body's orientation.
            point_color: Color for point rendering.
            names: Translated name(s) for this anchor. Can be a single name or a list of names.
            source_names: List of source (untranslated) names corresponding to the provided names.
            description: Optional description for this anchor.
        """
        AnchorBase.__init__(self, anchor_class, body, point_color, names, source_names, description)
        self.orbit = orbit
        self.rotation = rotation
        self._equatorial = LQuaterniond.ident_quat()

    def get_or_create_system(self) -> SystemAnchor:
        """Return the system this anchor is primary of, creating it lazily if needed.

        If this anchor has no stellar system yet, a new SystemAnchor wrapping this
        body is created, the current orbit is transferred to the system, and a
        LocalFixedPosition orbit is set on this body so that it is placed at the
        origin of the new system.

        Returns:
            The system anchor (a SystemAnchor instance).
        """
        if self.system is None:
            # Lazy imports to avoid circular dependencies
            from ...astro.frame import OrbitReferenceFrame, J2000BarycentricEclipticReferenceFrame
            from ...astro.orbits import LocalFixedPosition
            from ...astro.rotations import FixedRotation

            system_orbit = self.orbit
            system_rotation = FixedRotation(LQuaterniond(), J2000BarycentricEclipticReferenceFrame())
            # TODO: The system name should be translated correctly
            system = SystemAnchor(None, system_orbit, system_rotation, LColor(0), [self.get_name() + " System"])
            system.set_primary(self)
            if self.parent is not None:
                self.parent.add_child_fast(system)
            orbit = LocalFixedPosition(frame=OrbitReferenceFrame(system), frame_position=LPoint3d())
            self.set_orbit(orbit)
            system.add_child_fast(self)
        return self.system

    def is_stellar(self) -> bool:
        return True

    def has_orbit(self) -> bool:
        return True

    def has_rotation(self) -> bool:
        return True

    def has_frame(self) -> bool:
        return False

    def rebuild(self) -> None:
        pass

    def traverse(self, visitor) -> None:
        visitor.traverse_anchor(self)

    def get_orbit(self) -> OrbitBase:
        """Get the orbital component of this anchor.

        Returns:
            The orbit object.
        """
        return self.orbit

    def set_orbit(self, orbit: OrbitBase) -> None:
        """Set the orbital component of this anchor.

        Args:
            orbit: The new orbit object.
        """
        self.orbit = orbit

    def get_rotation(self) -> RotationBase:
        """Get the rotational component of this anchor.

        Returns:
            The rotation object.
        """
        return self.rotation

    def set_rotation(self, rotation: RotationBase) -> None:
        """Set the rotational component of this anchor.

        Args:
            rotation: The new rotation object.
        """
        self.rotation = rotation

    def has_system(self) -> bool:
        """Check if this anchor has a stellar system.

        Returns:
            True if this anchor is the primary body of a stellar system.
        """
        return self.system is not None

    def get_system(self) -> SystemAnchor | None:
        """Get the stellar system this anchor is the primary body of.

        Returns:
            The SystemAnchor this anchor is the primary body of, or None if it has no system.
        """
        return self.system

    def set_system(self, system: SystemAnchor) -> None:
        """Set the stellar system this anchor is the primary body of.

        Most system consists of a primary body (e.g., a star or planet) and one or more secondary bodies
        (e.g., planets, moons) that orbit it.
        This method is used to assign this anchor as the primary body of a stellar system.
        Args:
            system: The SystemAnchor to set as the system of this anchor.
        """
        self.system = system

    def update_observer(self, observer, update_id: int) -> None:
        """Update observer-relative position and visibility metrics."""
        if self.update_id == update_id:
            return
        reference_point_delta = self._global_position - observer.get_absolute_reference_point()
        local_delta = self._local_position - observer.get_local_position()
        self.rel_position = reference_point_delta + local_delta
        self.distance_to_obs = self.rel_position.length()
        if self.distance_to_obs > 0.0:
            self.vector_to_obs = -self.rel_position / self.distance_to_obs
            self.visible_size = self.bounding_radius / (self.distance_to_obs * observer.pixel_size)
            coef = -self.vector_to_obs.dot(observer.camera_vector)
            self.z_distance = self.distance_to_obs * coef
        else:
            self.vector_to_obs = LVector3d()
            self.visible_size = 0.0
            self.z_distance = 0.0

    def update_state(self, observer, update_id: int) -> None:
        """Update the anchor's visibility and resolved state."""
        if self.distance_to_obs > self.bounding_radius:
            in_view = observer.rel_frustum.is_sphere_in(self.rel_position, self.bounding_radius)
            resolved = self.visible_size > settings.min_body_size
            visible = in_view
        else:
            # We are in the object
            resolved = True
            visible = True
        self.visible = visible
        self.resolved = resolved

    def get_position_bounding_radius(self) -> float:
        return self.orbit.get_bounding_radius()

    def get_absolute_reference_point(self) -> LPoint3d:
        return self._global_position

    def get_absolute_position(self) -> LPoint3d:
        return self._position

    def get_frame_position(self) -> LPoint3d:
        return self.orbit.get_frame().get_frame_position(self._local_position)

    def get_local_position(self) -> LPoint3d:
        return self._local_position

    def get_absolute_orientation(self) -> LQuaterniond:
        return self._orientation

    def get_equatorial_rotation(self) -> LQuaterniond:
        """Get the equatorial orientation of the body.

        Returns:
            The equatorial rotation quaternion.
        """
        return self._equatorial

    def get_sync_rotation(self) -> LQuaterniond:
        """Get the synchronous rotation (same as absolute orientation).

        Returns:
            The synchronous rotation quaternion.
        """
        return self._orientation

    def get_absolute_magnitude(self) -> float:
        return lum_to_abs_mag(self.get_radiant_flux() / units.L0)

    def get_apparent_magnitude(self) -> float:
        return abs_to_app_mag(self.get_absolute_magnitude(), self.distance_to_obs)

    def update(self, time: float, update_id: int) -> None:
        if self.update_id == update_id:
            return
        self._orientation = self.rotation.get_absolute_rotation_at(time)
        self._equatorial = self.rotation.get_equatorial_orientation_at(time)
        self._local_position = self.orbit.get_local_position_at(time)
        self._global_position = self.orbit.get_absolute_reference_point_at(time)
        self._position = self._global_position + self._local_position

    def get_reflected_luminosity(self, star: StellarAnchor) -> float:
        """Compute the reflected luminosity from a stellar light source.

        Args:
            star: The stellar anchor acting as the light source.

        Returns:
            The reflected luminosity in Watts.
        """
        vector_to_star = self.calc_absolute_relative_position(star)
        distance_to_star = vector_to_star.length()
        vector_to_star /= distance_to_star
        if distance_to_star > 0.0:
            irradiance = star.get_point_radiance(distance_to_star)
            surface = pi * self.bounding_radius * self.bounding_radius * 1000 * 1000  # Units are in km
            received_power = irradiance * surface
            reflected_power = received_power * self._albedo
            phase_angle = self.vector_to_obs.dot(vector_to_star)
            fraction = (1.0 + phase_angle) / 2.0
            return reflected_power * fraction
        else:
            return 0.0

    def update_luminosity(self, star=None):
        if self.content & self.Reflective != 0:
            if star is not None:
                self._reflected_luminosity = self.get_reflected_luminosity(star)
            else:
                self._reflected_luminosity = 0.0
        else:
            self._reflected_luminosity = 0.0
        if self.distance_to_obs > 0:
            self._point_radiance = self.get_point_radiance(self.distance_to_obs)
        else:
            self._point_radiance = 0.0


class SystemAnchor(StellarAnchor):
    """Anchor for stellar systems containing multiple bodies.

    This anchor serves as a container for multiple celestial bodies that form
    a system (e.g., a planet with moons, a binary star system). It manages
    the hierarchical relationships, aggregate properties like bounding radius
    and combined luminosity, and child lookup by name or index.
    """

    def __init__(
        self,
        body: object,
        orbit: OrbitBase,
        rotation: RotationBase,
        point_color: LColor,
        names: list[str] | str | None = None,
        source_names: list[str] | None = None,
        description: str = '',
    ) -> None:
        """Initialize the SystemAnchor.

        Args:
            body: The system body associated with this anchor.
            orbit: The orbital component of the system.
            rotation: The rotational component of the system.
            point_color: Color for point rendering.
            names: Translated name(s) for this anchor. Can be a single name or a list of names.
            source_names: List of source (untranslated) names corresponding to the provided names.
            description: Optional description for this anchor.
        """
        StellarAnchor.__init__(self, self.System, body, orbit, rotation, point_color, names, source_names, description)
        self.primary = None
        self.star_system = False
        self.children: list[StellarAnchor] = []
        self.children_map: dict[str, StellarAnchor] = {}

    def get_or_create_system(self) -> SystemAnchor:
        """Return the system this anchor is primary of, creating it lazily if needed.

        A SystemAnchor is already a stellar system, so no creation is needed.

        Returns:
            This anchor.
        """
        return self

    def is_system(self) -> bool:
        """Return True — this anchor represents a stellar system."""
        return True

    def set_primary(self, primary: StellarAnchor | None) -> None:
        """Set the primary body of the system.

        Args:
            primary: The primary stellar anchor (e.g., the star).
        """
        self.primary = primary
        if primary is not None:
            primary.set_system(self)

    def add_child(self, child: AnchorBase) -> None:
        """Add a child anchor to the system and register its names.

        Args:
            child: The child anchor to add.
        """
        self.children.append(child)
        for name in child.get_names():
            self.children_map[name.upper()] = child
        child.parent = self
        if not self.rebuild_needed:
            self.set_rebuild_needed()

    def remove_child(self, child: AnchorBase) -> None:
        """Remove a child anchor from the system and unregister its names.

        Args:
            child: The child anchor to remove.
        """
        try:
            self.children.remove(child)
        except ValueError:
            pass
        else:
            child.parent = None
            for name in child.get_names():
                del self.children_map[name.upper()]
        if not self.rebuild_needed:
            self.set_rebuild_needed()

    def get_children(self) -> list[AnchorBase]:
        """Get the list of child anchors in this system.

        Returns:
            A list of child AnchorBase objects.
        """
        return self.children

    def find_child_by_name(self, name: str) -> AnchorBase | None:
        """Find a direct child body by name.

        Checks the fast children_map first, then falls back to a linear scan to find
        simple system referenced by their primary body name.

        Args:
            name: The (possibly mixed-case) name to search for.

        Returns:
            The anchor of the matching body, or None.
        """
        name_up = name.upper()
        child_anchor = self.children_map.get(name_up)
        if child_anchor is not None:
            return child_anchor
        for child_anchor in self.children:
            # SimpleSystem-like: child is a system with a primary whose name matches
            if (
                child_anchor.is_system()
                and child_anchor.primary is not None
                and child_anchor.primary._is_named(name_up)
            ):
                return child_anchor.primary
        return None

    def find_by_path(
        self,
        path: list[str] | str,
        separator: str = '/',
    ) -> AnchorBase | None:
        """Resolve a slash-separated path into a body relative to this system.

        Args:
            path: A path string (e.g. ``"Earth/Moon"``) or a list of name
                components that has already been split.
            separator: Character used to split a string *path*.

        Returns:
            The resolved anchor of the body, or None.
        """
        if not isinstance(path, list):
            path = path.split(separator)
        if not path:
            return None
        name = path[0]
        child = self.find_child_by_name(name)
        if child is None:
            return None
        if len(path) == 1:
            return child
        # Recurse: go through child (system) or child's containing system anchor
        sub_path = path[1:]
        if child.is_system():
            return child.find_by_path(sub_path, separator)
        elif child.system is not None:
            return child.system.find_by_path(sub_path, separator)
        return None

    def find_nth_child(self, index: int) -> AnchorBase | None:
        """Return the body of the *index*-th child (0-based).

        Args:
            index: Zero-based child index.

        Returns:
            The anchor of the child body, or None when out of range.
        """
        if index < len(self.children):
            return self.children[index].body
        return None

    def rebuild(self) -> None:
        """Rebuild the system's bounding radius and content flags."""
        self.content = self.System
        bounding_radius = 0
        for child in self.children:
            if child.rebuild_needed:
                child.rebuild()
            self.content |= child.content
            farthest_distance = child.get_position_bounding_radius() + child.get_bounding_radius()
            if farthest_distance > bounding_radius:
                bounding_radius = farthest_distance
        self.bounding_radius = bounding_radius
        if self.primary is None:
            luminosity = 0.0
            for child in self.children:
                if child.content & self.Emissive != 0:
                    luminosity += child._intrinsic_luminosity
            self._intrinsic_luminosity = luminosity
        else:
            self._intrinsic_luminosity = self.primary._intrinsic_luminosity
        self.rebuild_needed = False

    def traverse(self, visitor) -> None:
        """Accept a visitor for traversal."""
        if visitor.enter_system(self):
            visitor.traverse_system(self)

    def update_luminosity(self, star=None) -> None:
        """Update the system's luminosity based on a light source."""
        if self.primary is not None:
            self.primary.update_luminosity(star)
            self._intrinsic_luminosity = self.primary._intrinsic_luminosity
            self._reflected_luminosity = self.primary._reflected_luminosity
            self._point_radiance = self.primary._point_radiance
        else:
            StellarAnchor.update_luminosity(self, star)


class OctreeAnchor(SystemAnchor):
    """SystemAnchor integrated with octree spatial partitioning.

    This anchor combines a stellar system with an octree data structure for
    efficient spatial queries. It's typically used for large collections of
    objects like star fields or asteroid belts.
    """

    def __init__(
        self,
        body: object,
        orbit: OrbitBase,
        rotation: RotationBase,
        radius: float,
        point_color: LColor,
        names: list[str] | str | None = None,
        source_names: list[str] | None = None,
        description: str = '',
    ) -> None:
        """Initialize the OctreeAnchor.

        Args:
            body: The celestial body associated with this anchor.
            orbit: The orbital component.
            rotation: The rotational component.
            radius: The radius of the octree volume.
            point_color: Color for point rendering.
            names: Translated name(s) for this anchor. Can be a single name or a list of names.
            source_names: List of source (untranslated) names corresponding to the provided names.
            description: Optional description for this anchor.
        """
        SystemAnchor.__init__(self, body, orbit, rotation, point_color, names, source_names, description)
        self.bounding_radius = radius
        # TODO: Should be configurable
        abs_magnitude = app_to_abs_mag(6.0, radius * sqrt(3))
        luminosity = abs_mag_to_lum(abs_magnitude) * units.L0
        # TODO: position should be extracted from orbit
        self.octree = OctreeNode(
            0, self, LPoint3d(10 * units.Ly, 10 * units.Ly, 10 * units.Ly), radius * 2, luminosity
        )
        self.octree.parent = self
        # TODO: Should be done during rebuild
        self._intrinsic_luminosity = luminosity
        # TODO: Right now an octree contains anything
        self.content = ~0
        self.recreate_octree = True

    def rebuild(self) -> None:
        """Rebuild the octree structure and nested content."""
        if self.recreate_octree:
            self.create_octree()
            self.recreate_octree = False
        if self.octree.rebuild_needed:
            self.octree.rebuild()
        self.rebuild_needed = False

    def traverse(self, visitor) -> None:
        """Accept a visitor for traversal."""
        if visitor.enter_system(self):
            self.octree.traverse(visitor)

    def create_octree(self) -> None:
        """Create and populate the octree structure with child objects."""
        for child in self.children:
            child.update(0, 0)
            child.rebuild()
            self.octree.add(child)

    def dump_octree(self) -> None:
        """Print octree structure for debugging."""
        self.octree.dump_octree()


class UniverseAnchor(OctreeAnchor):
    """Root anchor representing the entire universe.

    This is the top-level anchor in the graph hierarchy, encompassing
    all stellar systems and objects. It's always visible and resolved.
    """

    def __init__(
        self,
        body: object,
        orbit: OrbitBase,
        rotation: RotationBase,
        radius: float,
        point_color: LColor,
        names: list[str] | str | None = None,
        source_names: list[str] | None = None,
        description: str = '',
    ) -> None:
        """Initialize the UniverseAnchor.

        Args:
            body: The celestial body associated with this anchor.
            orbit: The orbital component (typically static for the universe).
            rotation: The rotational component (typically static for the universe).
            radius: The radius of the universe volume.
            point_color: Color for point rendering.
            names: Translated name(s) for this anchor. Can be a single name or a list of names.
            source_names: List of source (untranslated) names corresponding to the provided names.
            description: Optional description for this anchor.
        """
        OctreeAnchor.__init__(self, body, orbit, rotation, radius, point_color, names, source_names, description)
        self.visible = True
        self.resolved = True

    def traverse(self, visitor: object) -> None:
        """Accept a visitor for traversal.

        Args:
            visitor: The traverser object visiting this anchor.
        """
        self.octree.traverse(visitor)
