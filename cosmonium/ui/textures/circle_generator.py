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


from __future__ import annotations

from math import sqrt

from panda3d.core import LColor, PNMImage, Texture


class CircleTextureGenerator:
    """
    Generates circle textures for 9-slice/9-patch rendering.

    This generator creates textures with proper antialiasing using distance-based
    alpha calculations. The textures are designed to be used with 9-slice UV mapping
    where corners use portions of the circle.
    """

    def __init__(
        self,
        radius: int,
        border_width: int = 1,
        border_color: LColor | tuple[int, int, int, int] = (1, 1, 1, 1),
        inner_color: LColor | tuple[int, int, int, int] | None = None,
    ):
        """
        Initialize the circle texture generator.

        Args:
            radius: Radius of the circle in pixels (determines texture size)
            border_width: Width of the border/trait in pixels (for hollow circles).
                        Set to 0 for plain circle
            border_color: RGBA color or tuple for border
            inner_color: RGBA color or tuple for inner area of hollow circles (values 0-1).
                        If None, inner area is transparent. If provided, inner area uses this color.
        """
        self.radius = radius
        if not border_width:
            border_width = radius
        self.border_width = border_width
        self.border_color = LColor(border_color)
        self.inner_color = LColor(inner_color if inner_color is not None else (0, 0, 0, 0))
        self.outer_color = LColor(0)
        # Texture size is based on diameter plus one pixel padding for antialiasing
        self.texture_size = int(radius * 2 + 2)

    def _distance_from_center(self, x: int, y: int, center_x: float, center_y: float) -> float:
        """
        Calculate the distance from a point to the center of a cirle.

        Args:
            x, y: Point coordinates
            center_x, center_y: Circle center coordinates

        Returns:
            Distance
        """
        dx = x + 0.5 - center_x
        dy = y + 0.5 - center_y
        dist_from_center = sqrt(dx * dx + dy * dy)
        return dist_from_center

    def _smooth_step(self, edge0: float, edge1: float, x: float) -> float:
        """
        Smooth interpolation function for antialiasing.

        Args:
            edge0: Lower edge of interpolation range
            edge1: Upper edge of interpolation range
            x: Value to interpolate

        Returns:
            Interpolated value between 0 and 1
        """
        t = max(0.0, min(1.0, (x - edge0) / (edge1 - edge0)))
        return t * t * (3.0 - 2.0 * t)

    def generate_plain_circle(self) -> Texture:
        """
        Generate a filled circle texture with antialiasing.

        The circle is filled with border_color and has transparency on the outer side.
        Designed for solid rounded corners.

        Returns:
            Texture object
        """
        size = self.texture_size
        image = PNMImage(size, size, num_channels=4)

        center = size / 2.0
        radius = self.radius

        for y in range(size):
            for x in range(size):
                # Calculate distance to circle edge
                dist_from_center = self._distance_from_center(x, y, center, center)
                dist = dist_from_center - radius

                # Antialiasing: smooth transition over ~1 pixel
                # Negative distance = inside circle, positive = outside
                alpha = min(1.0 - self._smooth_step(-0.5, 0.5, dist), 1.0)

                final_color = self.border_color * alpha + self.outer_color * (1 - alpha)
                image.set_xel_a(x, y, *final_color)

        # Create and load texture
        texture = Texture()
        texture.load(image)
        texture.set_wrap_u(Texture.WM_clamp)
        texture.set_wrap_v(Texture.WM_clamp)
        return texture

    def generate_circle(self) -> Texture:
        """
        Generate a circle texture with antialiasing.

        The ring has border_color for the border. Outside the ring is transparent.
        Inside the ring uses inner_color (transparent by default, or custom color if specified).
        Designed for bordered rounded corners.

        Returns:
            Texture object
        """
        size = self.texture_size
        image = PNMImage(size, size, num_channels=4)

        center = size / 2.0
        outer_radius = self.radius
        center_radius = self.radius - self.border_width
        inner_radius = max(0, self.radius - self.border_width)  # Ensure inner_radius is non-negative

        for y in range(size):
            for x in range(size):
                # Calculate distance from center
                dist_from_center = self._distance_from_center(x, y, center, center)

                if inner_radius > 0:
                    # Blend between border color (ring) and inner color (center) or outer color (outside)
                    if dist_from_center > center_radius:
                        # Antialiasing: smooth transition over ~1 pixel
                        # Negative distance = inside outer circle, positive = outside
                        outer_dist = dist_from_center - outer_radius
                        outer_alpha = min(1.0 - self._smooth_step(-0.5, 0.5, outer_dist), 1.0)
                        final_color = self.border_color * outer_alpha + self.outer_color * (1 - outer_alpha)
                        image.set_xel_a(x, y, *final_color)
                    else:
                        # Antialiasing: smooth transition over ~1 pixel
                        # Negative distance = outside inner circle, positive = outside
                        inner_dist = inner_radius - dist_from_center
                        inner_alpha = min(1.0 - self._smooth_step(-0.5, 0.5, inner_dist), 1.0)
                        final_color = self.border_color * inner_alpha + self.inner_color * (1 - inner_alpha)
                        image.set_xel_a(x, y, *final_color)
                else:
                    # If inner_radius is 0, entire circle is the border
                    # Antialiasing: smooth transition over ~1 pixel
                    # Negative distance = inside circle, positive = outside
                    outer_dist = dist_from_center - outer_radius
                    outer_alpha = min(1.0 - self._smooth_step(-0.5, 0.5, outer_dist), 1.0)
                    final_color = self.border_color * outer_alpha + self.outer_color * (1 - outer_alpha)
                    image.set_xel_a(x, y, *final_color)

        # Create and load texture
        texture = Texture()
        texture.load(image)
        texture.set_wrap_u(Texture.WM_clamp)
        texture.set_wrap_v(Texture.WM_clamp)
        return texture
