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

"""High-level navigation commands for the autopilot.

Provides :class:`NavigationAutoPilot`, which exposes the destination-based
fly-to methods (go_to_front, go_to_object, go_to_surface, etc.).  All
methods ultimately delegate to :meth:`AutoPilotBase.move_and_rotate_to`.
"""

from __future__ import annotations

import logging
from math import pi
from typing import TYPE_CHECKING, Optional

from panda3d.core import LQuaterniond, LVector3d, lookAt

from .. import settings
from ..astro import units
from ..objects.systems import StellarSystem
from ..utils import isclose

if TYPE_CHECKING:
    from ..objects.stellarobject import StellarObject
    from .base import AutoPilotBase

logger = logging.getLogger('autopilot')


class NavigationAutoPilot:
    """Autopilot mode for high-level destination navigation.

    Holds a reference to an :class:`~cosmonium.autopilot.base.AutoPilotBase`
    instance whose animation primitives are used to execute the fly-to.

    Args:
        autopilot: The base autopilot that provides animation infrastructure.
    """

    def __init__(self, autopilot: AutoPilotBase) -> None:
        self.autopilot = autopilot

    # ------------------------------------------------------------------
    # Primitive: fly to position + direction
    # ------------------------------------------------------------------

    def go_to(
        self,
        target: StellarObject,
        duration: float,
        position,
        direction: LVector3d,
        up: Optional[LVector3d],
        start_rotation: float,
        end_rotation: float,
    ) -> None:
        """Fly to *position* facing *direction*, with an optional *up* hint.

        Builds the target orientation from *direction* and *up* using
        ``lookAt``.  If *up* is not provided the camera's current
        up vector is used.  The up vector is orthogonalised against
        *direction* via Gram-Schmidt before being passed to ``lookAt``.

        Args:
            target: The celestial object being navigated to (reserved for future
                use, e.g. keeping the object in view during the fly-to).
            duration: Animation duration in seconds.
            position: Target position in the local (anchor-relative) coordinate frame.
            direction: Unit vector pointing from the camera toward the target object.
            up: Preferred up vector for the camera.  Pass ``None`` to keep the
                current camera up direction.
            start_rotation: Rotation sub-range fraction (see :meth:`AutoPilotBase.move_and_rotate_to`).
            end_rotation: Rotation sub-range fraction (see :meth:`AutoPilotBase.move_and_rotate_to`).
        """
        if up is None:
            up = self.autopilot.camera_controller.get_local_orientation().xform(LVector3d.up())
        if isclose(abs(up.dot(direction)), 1.0):
            logger.warning("lookat vector identical to up vector")
        else:
            # Make the up vector orthogonal to direction (Gram-Schmidt) and
            # normalise so that lookAt receives a proper unit vector.
            up = (up - direction * up.dot(direction)).normalized()
        orientation = LQuaterniond()
        lookAt(orientation, direction, up)
        self.autopilot.move_and_rotate_to(
            position, orientation, duration=duration, start_rotation=start_rotation, end_rotation=end_rotation
        )

    # ------------------------------------------------------------------
    # Destination commands
    # ------------------------------------------------------------------

    def go_to_front(
        self,
        duration: Optional[float] = None,
        distance: Optional[float] = None,
        up: Optional[LVector3d] = None,
        star: bool = False,
        start_rotation: Optional[float] = None,
        end_rotation: Optional[float] = None,
    ) -> None:
        """Fly to the illuminated face of the selected object.

        The camera is positioned *distance* radii away from the object,
        looking from the direction of the primary light source.  For a
        star (or the primary of a system), the first registered light
        source is used; for a planet the system primary is used as the
        viewpoint.

        Args:
            duration: Animation duration. Defaults to ``settings.slow_move``.
            distance: Distance from the object surface in object radii. Defaults to
                ``settings.default_distance``.
            up: Preferred camera up vector. ``None`` keeps the current up.
            star: When ``True``, treat the selected object as a star and look from
                its own light source rather than from the system primary.
            start_rotation: Rotation timing fraction (see :meth:`AutoPilotBase.move_and_rotate_to`).
                Defaults to ``settings.goto_rotation_start``.
            end_rotation: Rotation timing fraction (see :meth:`AutoPilotBase.move_and_rotate_to`).
                Defaults to ``settings.goto_rotation_end``.
        """
        if not self.autopilot.ui.selected:
            return
        target = self.autopilot.ui.selected
        if duration is None:
            duration = settings.slow_move
        if distance is None:
            distance = settings.default_distance
        if start_rotation is None:
            start_rotation = settings.goto_rotation_start
        if end_rotation is None:
            end_rotation = settings.goto_rotation_end
        distance_unit = target.get_apparent_radius()
        if distance_unit == 0.0:
            distance_unit = target.get_bounding_radius()
        logger.debug("Go to front %s", target.get_name())
        self.autopilot.ui.follow_selected()
        center = target.anchor.calc_absolute_relative_position_to(
            self.autopilot.controller.get_absolute_reference_point()
        )
        # Determine the position from which we are viewing the object (i.e. where the light comes from).
        light_position = None
        if star:
            if target.lights is not None and len(target.lights.lights) > 0:
                light_position = target.lights.lights[0].source
        else:
            if (
                target.parent is not None
                and isinstance(target.parent, StellarSystem)
                and target.parent.primary is not None
            ):
                if target.parent.primary == target:
                    if target.lights is not None and len(target.lights.lights) > 0:
                        light_position = target.lights.lights[0].source
                else:
                    light_position = target.parent.primary
        if light_position is not None:
            logger.debug("Looking from %s", light_position.get_name())
            view_origin = light_position.anchor.calc_absolute_relative_position_to(
                self.autopilot.controller.get_absolute_reference_point()
            )
        else:
            view_origin = self.autopilot.controller.get_local_position()
        direction = center - view_origin
        direction.normalize()
        new_position = center - direction * distance * distance_unit
        self.go_to(target, duration, new_position, direction, up, start_rotation, end_rotation)

    def go_to_object(
        self,
        duration: Optional[float] = None,
        distance: Optional[float] = None,
        up: Optional[LVector3d] = None,
        start_rotation: Optional[float] = None,
        end_rotation: Optional[float] = None,
    ) -> None:
        """Fly toward the selected object from the current camera direction.

        The camera travels to a point *distance* radii in front of the
        object, keeping the current viewing direction.

        Args:
            duration: Animation duration.  Defaults to ``settings.slow_move``.
            distance: Distance from the object surface in object radii.  Defaults to
                ``settings.default_distance``.
            up: Preferred camera up vector.  ``None`` keeps the current up.
            start_rotation: Rotation timing fraction (see :meth:`AutoPilotBase.move_and_rotate_to`).
                Defaults to ``settings.goto_rotation_start``.
            end_rotation: Rotation timing fraction (see :meth:`AutoPilotBase.move_and_rotate_to`).
                Defaults to ``settings.goto_rotation_end``.
        """
        if not self.autopilot.ui.selected:
            return
        target = self.autopilot.ui.selected
        if duration is None:
            duration = settings.slow_move
        if distance is None:
            distance = settings.default_distance
        if start_rotation is None:
            start_rotation = settings.goto_rotation_start
        if end_rotation is None:
            end_rotation = settings.goto_rotation_end
        distance_unit = target.get_apparent_radius()
        if distance_unit == 0.0:
            distance_unit = target.get_bounding_radius()
        logger.debug("Go to %s", target.get_name())
        self.autopilot.ui.follow_selected()
        center = target.anchor.calc_absolute_relative_position_to(
            self.autopilot.controller.get_absolute_reference_point()
        )
        direction = center - self.autopilot.controller.get_local_position()
        direction.normalize()
        new_position = center - direction * distance * distance_unit
        self.go_to(target, duration, new_position, direction, up, start_rotation, end_rotation)

    def go_to_object_long_lat(
        self,
        longitude: float,
        latitude: float,
        duration: Optional[float] = None,
        distance: Optional[float] = None,
        up: Optional[LVector3d] = None,
        start_rotation: Optional[float] = None,
        end_rotation: Optional[float] = None,
    ) -> None:
        """Fly to a specific longitude/latitude on the selected object.

        The camera is placed *distance* radii above the geodetic position
        given by (*longitude*, *latitude*) on the object's surface,
        looking toward the object centre.

        Args:
            longitude: Target longitude in radians.
            latitude: Target latitude in radians.
            duration: Animation duration. Defaults to ``settings.slow_move``.
            distance: Distance from the surface in object radii. Defaults to
                ``settings.default_distance``.
            up: Preferred camera up vector. ``None`` keeps the current up.
            start_rotation: Rotation timing fraction (see :meth:`AutoPilotBase.move_and_rotate_to`).
                Defaults to ``settings.goto_longlat_rotation_start``.
            end_rotation: Rotation timing fraction (see :meth:`AutoPilotBase.move_and_rotate_to`).
                Defaults to ``settings.goto_longlat_rotation_end``.
        """
        if not self.autopilot.ui.selected:
            return
        target = self.autopilot.ui.selected
        if duration is None:
            duration = settings.slow_move
        if distance is None:
            distance = settings.default_distance
        if start_rotation is None:
            start_rotation = settings.goto_longlat_rotation_start
        if end_rotation is None:
            end_rotation = settings.goto_longlat_rotation_end
        distance_unit = target.get_apparent_radius()
        if distance_unit == 0.0:
            distance_unit = target.get_bounding_radius()
        logger.debug("Go to long-lat %s", target.get_name())
        self.autopilot.ui.follow_selected()
        center = target.anchor.calc_absolute_relative_position_to(
            self.autopilot.controller.get_absolute_reference_point()
        )
        # Compute the camera offset from the object centre in the object's
        # body-fixed frame, then rotate it into the world frame.
        offset = target.surface.geodetic_to_cartesian(longitude, latitude, (distance - 1) * distance_unit)
        offset = target.anchor._orientation.xform(offset)
        direction = -offset.normalized()
        self.go_to(target, duration, center + offset, direction, up, start_rotation, end_rotation)

    def go_to_surface(self, duration: Optional[float] = None, altitude: float = 2) -> None:
        """Fly the camera down to just above the surface below the current position.

        The camera is placed at the terrain height directly below its
        current position (as reported by ``get_height_under``), offset by
        *altitude* metres, and oriented to look toward the object centre.

        Args:
            duration: Animation duration.  Defaults to ``settings.slow_move``.
            altitude: The landing height in meters. Default to 2 meters above the surface.
        """
        if not self.autopilot.ui.selected:
            return
        target = self.autopilot.ui.selected
        if duration is None:
            duration = settings.slow_move
        logger.debug("Go to surface %s", target.get_name())
        self.autopilot.ui.sync_selected()
        center = target.anchor.calc_absolute_relative_position_to(
            self.autopilot.controller.get_absolute_reference_point()
        )
        direction = self.autopilot.controller.get_local_position() - center
        new_orientation = LQuaterniond()
        lookAt(new_orientation, direction)
        distance = target.get_height_under(self.autopilot.controller.get_local_position()) + altitude * units.m
        new_position = center + new_orientation.xform(LVector3d(0, distance, 0))
        self.autopilot.move_and_rotate_to(new_position, new_orientation, duration=duration)

    def go_pole(self, target: StellarObject, lat: float, duration: Optional[float], zoom: bool) -> None:
        """Fly to the pole at *lat* radians latitude on the given object.

        Args:
            target: The celestial object to fly to.
            lat: Target latitude in radians (``+pi/2`` = north, ``-pi/2`` = south).
            duration: Animation duration. ``None`` uses ``settings.slow_move``.
            zoom: When ``True``, use ``settings.default_distance``; otherwise
                preserve the current distance.
        """
        if zoom:
            distance = settings.default_distance
        else:
            distance_unit = target.get_apparent_radius()
            if distance_unit == 0.0:
                distance_unit = target.get_bounding_radius()
            distance = target.anchor.distance_to_obs / distance_unit
        self.go_to_object_long_lat(0, lat, duration, distance)

    def go_north(self, duration: Optional[float] = None, zoom: bool = False) -> None:
        """Fly to the north pole of the selected object.

        Args:
            duration: Animation duration.  Defaults to ``settings.slow_move``.
            zoom: When ``True``, use ``settings.default_distance`` rather than
                preserving the current distance.
        """
        if not self.autopilot.ui.selected:
            return
        target = self.autopilot.ui.selected
        lat = pi / 2
        if target.anchor.rotation.is_flipped():
            lat = -lat
        self.go_pole(target, lat, duration, zoom)

    def go_south(self, duration: Optional[float] = None, zoom: bool = False) -> None:
        """Fly to the south pole of the selected object.

        Args:
            duration: Animation duration.  Defaults to ``settings.slow_move``.
            zoom: When ``True``, use ``settings.default_distance`` rather than
                preserving the current distance.
        """
        if not self.autopilot.ui.selected:
            return
        target = self.autopilot.ui.selected
        lat = -pi / 2
        if target.anchor.rotation.is_flipped():
            lat = -lat
        self.go_pole(target, lat, duration, zoom)

    def go_meridian(self, duration: Optional[float] = None, zoom: bool = False) -> None:
        """Fly to the prime meridian (longitude=0, latitude=0) of the selected object.

        Args:
            duration: Animation duration.  Defaults to ``settings.slow_move``.
            zoom: When ``True``, use ``settings.default_distance`` rather than
                preserving the current distance.
        """
        if not self.autopilot.ui.selected:
            return
        target = self.autopilot.ui.selected
        if zoom:
            distance = settings.default_distance
        else:
            distance_unit = target.get_apparent_radius()
            if distance_unit == 0.0:
                distance_unit = target.get_bounding_radius()
            distance = target.anchor.distance_to_obs / distance_unit
        self.go_to_object_long_lat(0, 0, duration, distance)
