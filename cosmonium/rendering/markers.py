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


from dataclasses import dataclass

from panda3d.core import LColor

from ..components.annotations.marker import ObjectMarker
from ..components.annotations.marker_shape import MarkerShape


@dataclass(slots=True)
class MarkerData:
    """Configuration for a single object marker.

    Attributes:
        color: RGBA color as an LColor.
        size: Marker radius in pixels.
        symbol: A MarkerShape enum value.
        label: Optional text label shown alongside the marker.
        occludable: When False the marker renders on top of all geometry.
    """

    color: LColor
    size: float
    symbol: MarkerShape
    label: str | None
    occludable: bool


class Markers:
    """Manages per-object markers, similar to how Labels manages object labels.

    Markers are placed individually on specific celestial objects and persist
    across visibility changes: the visual instance is created or destroyed as
    the object enters/leaves the visible set, but the marker configuration is
    retained until explicitly removed.
    """

    DEFAULT_COLOR = LColor(0.0, 1.0, 0.0, 0.9)
    DEFAULT_SIZE = 10.0
    DEFAULT_SYMBOL = MarkerShape.DIAMOND

    def __init__(self):
        # body -> MarkerData (persistent marker configuration)
        self.marker_data = {}
        # body -> ObjectMarker (active visual instance, only while body is visible)
        self.active_markers = {}
        # flat list of active ObjectMarker instances for update iteration
        self.markers = []

    def is_marked(self, body):
        """Return True if body has a marker configured.

        Args:
            body: The StellarObject to check.

        Returns:
            True if the body has a marker configured, False otherwise.
        """
        return body in self.marker_data

    def mark(self, body, color=None, size=None, symbol=None, label=None, occludable=False):
        """Set a marker on body, replacing any existing one.

        Args:
            body: The StellarObject to mark.
            color: RGBA color as an LColor (or 4-tuple). Defaults to green.
            size: Marker radius in pixels. Defaults to 10.
            symbol: A MarkerShape enum value. Defaults to DIAMOND.
            label: Optional text label shown alongside the marker symbol.
            occludable: When False the marker renders on top of all geometry.
        """
        if color is None:
            color = self.DEFAULT_COLOR
        if size is None:
            size = self.DEFAULT_SIZE
        if symbol is None:
            symbol = self.DEFAULT_SYMBOL
        if not isinstance(color, LColor):
            color = LColor(*color)

        # Replace any existing active instance so the new settings take effect immediately.
        if body in self.active_markers:
            self._destroy_instance(body)

        self.marker_data[body] = MarkerData(color, size, symbol, label, occludable)

        # If the body already has a scene_anchor (i.e. it is currently visible),
        # create the visual instance right away.
        if body.scene_anchor is not None and (body.anchor.visible or body.anchor.resolved):
            self._create_instance(body)

    def unmark(self, body):
        """Remove the marker from body.

        Args:
            body: The StellarObject to unmark.
        """
        self._destroy_instance(body)
        self.marker_data.pop(body, None)

    def unmark_all(self):
        """Remove all markers."""
        for body in list(self.active_markers.keys()):
            self._destroy_instance(body)
        self.marker_data.clear()

    def toggle_mark(self, body, color=None, size=None, symbol=None, label=None, occludable=True):
        """Toggle the marker on body: remove it if already marked, else add it.

        Args:
            body: The StellarObject to toggle.
            color: Marker color as an LColor (or 4-tuple). Defaults to green.
            size: Marker radius in pixels. Defaults to 10.
            symbol: A MarkerShape enum value. Defaults to DIAMOND.
            label: Optional text label shown alongside the marker symbol.
            occludable: When False the marker renders on top of all geometry.
        """
        if self.is_marked(body):
            self.unmark(body)
        else:
            self.mark(body, color=color, size=size, symbol=symbol, label=label, occludable=occludable)

    # ------------------------------------------------------------------
    # Visibility lifecycle hooks called from the main engine update loop.
    # ------------------------------------------------------------------

    def on_visible(self, body):
        """Called when body enters the visible set.

        Creates the marker visual instance if the body is configured to be marked.

        Args:
            body: The StellarObject that became visible.
        """
        if body in self.marker_data and body not in self.active_markers:
            self._create_instance(body)

    def on_invisible(self, body):
        """Called when body leaves the visible set.

        Destroys the active marker instance while retaining the marker configuration.

        Args:
            body: The StellarObject that became invisible.
        """
        self._destroy_instance(body)

    # ------------------------------------------------------------------
    # Per-frame update delegated to the active marker instances.
    # ------------------------------------------------------------------

    def update_obs(self, observer):
        """Update observer position for all active markers.

        Args:
            observer: The observer position.
        """
        for marker in self.markers:
            marker.update_obs(observer)

    def check_visibility(self, frustum, pixel_size):
        """Check visibility of all active markers.

        Args:
            frustum: The view frustum.
            pixel_size: Pixel size parameter.
        """
        for marker in self.markers:
            marker.check_visibility(frustum, pixel_size)

    def check_and_create_instance(self, scene_manager, camera_pos, camera_rot):
        """Check and create instances for all active markers.

        Args:
            scene_manager: The scene manager.
            camera_pos: Camera position.
            camera_rot: Camera rotation.
        """
        for marker in self.markers:
            marker.check_and_create_instance(scene_manager, camera_pos, camera_rot)

    def check_and_update_instance(self, scene_manager, camera_pos, camera_rot):
        """Check and update instances for all active markers.

        Args:
            scene_manager: The scene manager.
            camera_pos: Camera position.
            camera_rot: Camera rotation.
        """
        for marker in self.markers:
            marker.check_and_update_instance(scene_manager, camera_pos, camera_rot)

    # ------------------------------------------------------------------
    # Internal helpers.
    # ------------------------------------------------------------------

    def _create_instance(self, body):
        data = self.marker_data[body]
        marker = ObjectMarker(
            body.get_ascii_name() + '-marker',
            body,
            data.color,
            data.size,
            data.symbol,
            data.label,
            data.occludable,
        )
        marker.set_scene_anchor(body.scene_anchor)
        self.active_markers[body] = marker
        self.markers.append(marker)

    def _destroy_instance(self, body):
        marker = self.active_markers.pop(body, None)
        if marker is not None:
            self.markers.remove(marker)
            marker.remove_instance()
