#
#This file is part of Cosmonium.
#
#Copyright (C) 2018-2024 Laurent Deru.
#
#Cosmonium is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
#
#Cosmonium is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with Cosmonium.  If not, see <https://www.gnu.org/licenses/>.
#

from __future__ import annotations

from abc import ABC, abstractmethod
from math import sqrt, pi, sin, cos, asin, atan2, copysign
from panda3d.core import LVector3, LPoint3d, LVector3d

from .ellipse import DistancePointEllipse, PointToGeodetic
from .ellipsoid import DistancePointEllipsoid, TriaxialGeodeticToCartesian, PointToTriaxialGeodetic


class EllipsoidModelInterface(ABC):

    @abstractmethod
    def copy_extend(self, delta: float) -> EllipsoidModelInterface:
        """
        Create a copy of this model with all the axes increased by delta
        """
        raise NotImplementedError

    @abstractmethod
    def get_shape_axes(self) -> LVector3d:
        """
        Return the axes to be used to create the shape
        """
        raise NotImplementedError

    @abstractmethod
    def get_point_under(self, position: LPoint3d) -> LPoint3d:
        """
        Return the surface point closest to the given position.
        The position is expressed as cartesian body centered coordinates (ECEF)
        """
        ...

    @abstractmethod
    def get_radius_under(self, position: LPoint3d) -> float:
        """
        Return the distance from center of the ellipsoid to the surface point closest to the given position.
        The position is expressed as cartesian body centered coordinates (ECEF)
        """
        ...

    @abstractmethod
    def get_average_radius(self) -> float:
        """
        Returns the average radius of the ellipsoid
        """
        ...

    @abstractmethod
    def get_min_radius(self) -> float:
        """
        Return the minimum axis of the ellipsoid
        """
        ...

    @abstractmethod
    def get_max_radius(self) -> float:
        """
        Return the maximum axis of the ellipsoid
        """
        ...

    @abstractmethod
    def geodetic_to_cartesian(self, long: float, lat: float, h: float) -> LPoint3d:
        """
        Convert the geodetic coordinates into cartesian body centered coordinates (ECEF)
        """
        ...

    @abstractmethod
    def cartesian_to_geodetic(self, position: LPoint3d) -> tuple[float, float, float]:
        """
        Convert the cartesian body centered coordinates (ECEF) into geodetic coordinates
        """
        ...

    @abstractmethod
    def parametric_to_cartesian(self, x: float, y: float, h: float) -> LPoint3d:
        """
        Convert the parametric coordinates into cartesian body centered coordinates (ECEF)
        """
        ...

    @abstractmethod
    def cartesian_to_parametric(self, position: LPoint3d) -> tuple[float, float, float]:
        """
        Convert the cartesian body centered coordinates (ECEF) into parametric coordinates
        """
        ...

    @abstractmethod
    def get_tangent_plane_under(self, position: LPoint3d) -> tuple[LPoint3d, LPoint3d, LPoint3d]:
        """
        Returns the tangent, binormal and normal geodetic vectors (n-vector) related to the tangent plane
        of the closest point on the ellipsoid.
        """
        ...


class SphereModel(EllipsoidModelInterface):
    def __init__(self, radius):
        self.radius = radius

    def copy_extend(self, delta: float) -> SphereModel:
        return SphereModel(self.radius + delta)

    def get_shape_axes(self) -> LVector3d:
        return LVector3d(self.radius)

    def get_point_under(self, position: LPoint3d) -> LPoint3d:
        return position.normalized() * self.radius

    def get_radius_under(self, position: LPoint3d) -> float:
        return self.radius

    def get_average_radius(self) -> float:
        return self.radius

    def get_min_radius(self) -> float:
        return self.radius

    def get_max_radius(self) -> float:
        return self.radius

    def geodetic_to_cartesian(self, long: float, lat: float, h: float) -> LPoint3d:
        return LPoint3d(cos(lat) * cos(long), cos(lat) * sin(long), sin(lat)) * (self.radius + h)

    def cartesian_to_geodetic(self, position: LPoint3d) -> tuple[float, float, float]:
        distance = position.length()
        if distance > 0:
            theta = asin(position[2] / distance)
            if position[0] != 0.0:
                phi = atan2(position[1], position[0])
                #Offset phi by 180 deg with proper wrap around
                #phi = (phi + pi + pi) % (2 * pi) - pi
            else:
                phi = 0.0
        else:
            phi = 0.0
            theta = 0.0
        h = distance - self.radius
        return (phi, theta, h)

    def parametric_to_cartesian(self, x: float, y: float, h: float) -> LPoint3d:
        cos_s = cos(2 * pi * x + pi)
        sin_s = sin(2 * pi * x + pi)
        sin_r = sin(pi * y)
        cos_r = cos(pi * y)
        r = self.radius + h
        p = LVector3d(
            r * cos_s * sin_r,
            r * sin_s * sin_r,
            -r * cos_r)
        return p

    def cartesian_to_parametric(self, position: LPoint3d) -> tuple[float, float, float]:
        (phi, theta, h) = self.cartesian_to_geodetic(position)
        x = phi / pi / 2 + 0.5
        y = theta / pi + 0.5
        return (x, y, h)

    def get_tangent_plane_under(self, position: LPoint3d) -> tuple[LPoint3d, LPoint3d, LPoint3d]:
        (phi, theta, _h) = self.cartesian_to_geodetic(position)
        cos_s = cos(phi)
        sin_s = sin(phi)
        sin_r = sin(theta + pi / 2)
        cos_r = cos(theta + pi / 2)
        normal = LVector3d(
            cos_s * sin_r,
            sin_s * sin_r,
            -cos_r)
        normal.normalize()

        tangent = LVector3d(-sin_s, cos_s, 0)
        tangent.normalize()
        binormal = normal.cross(tangent)
        binormal.normalize()
        return (tangent, binormal, normal)


class SpheroidModel(EllipsoidModelInterface):
    def __init__(self, radius, ellipticity):
        self.radius = radius
        self.ellipticity = ellipticity

    def copy_extend(self, delta: float) -> SpheroidModel:
        return SpheroidModel(self.radius + delta, self.ellipticity)

    def get_shape_axes(self) -> LVector3d:
        return LVector3d(1.0, 1.0, 1.0 - self.ellipticity) * self.radius

    def get_point_under(self, position: LPoint3d) -> LPoint3d:
        if position[0] != 0.0:
            phi = atan2(position[1], position[0])
        else:
            phi = 0.0
        y0 = sqrt(position[0] * position[0] + position[1] * position[1]) / self.radius
        y1 = position[2] / self.radius
        x0, x1, _distance = DistancePointEllipse(1.0, 1.0 - self.ellipticity, y0, y1)
        return LPoint3d(
            copysign(x0 * cos(phi) * self.radius, position[0]),
            copysign(x0 * sin(phi) * self.radius, position[1]),
            x1 * self.radius)

    def get_radius_under(self, position: LPoint3d) -> float:
        y0 = sqrt(position[0] * position[0] + position[1] * position[1]) / self.radius
        y1 = position[2] / self.radius
        x0, x1, _distance = DistancePointEllipse(1.0, 1.0 - self.ellipticity, y0, y1)
        r = self.radius * sqrt(x0 * x0 + x1 * x1)
        return r

    def get_average_radius(self) -> float:
        return self.radius

    def get_min_radius(self) -> float:
        return self.radius * (1.0 - self.ellipticity)

    def get_max_radius(self) -> float:
        return self.radius

    def geodetic_to_cartesian(self, long: float, lat: float, h: float) -> LPoint3d:
        ba = 1 - self.ellipticity
        e2 = 1 - ba * ba
        sin_lat = sin(lat)
        N = self.radius / sqrt(1 - e2 * sin_lat * sin_lat)
        pos = LPoint3d(
            (N + h) * cos(lat) * cos(long), (N + h) * cos(lat) * sin(long), ((1 - e2) * N + h) * sin_lat)
        return pos

    def cartesian_to_geodetic(self, position: LPoint3d) -> tuple[float, float, float]:
        y0 = sqrt(position[0] * position[0] + position[1] * position[1]) / self.radius
        y1 = position[2] / self.radius
        if position[0] != 0.0:
            phi = atan2(position[1], position[0])
        else:
            phi = 0.0
        (theta, h) = PointToGeodetic(1.0, 1.0 - self.ellipticity, y0, y1)
        return (phi, theta, h * self.radius)

    def parametric_to_cartesian(self, x: float, y: float, h: float) -> LPoint3d:
        cos_s = cos(2 * pi * x + pi)
        sin_s = sin(2 * pi * x + pi)
        sin_r = sin(pi * y)
        cos_r = cos(pi * y)
        p = LVector3d(
            (self.radius + h) * cos_s * sin_r,
            (self.radius + h) * sin_s * sin_r,
            -(self.radius * (1.0 - self.ellipticity) + h) * cos_r)
        return p

    def cartesian_to_parametric(self, position: LPoint3d) -> tuple[float, float, float]:
        scaled_position = LPoint3d(
            position[0],
            position[1],
            position[2] / (1.0 - self.ellipticity)
            )
        distance = scaled_position.length()
        if distance > 0:
            theta = asin(scaled_position[2] / distance)
            if scaled_position[0] != 0.0:
                phi = atan2(scaled_position[1], scaled_position[0])
                #Offset phi by 180 deg with proper wrap around
                #phi = (phi + pi + pi) % (2 * pi) - pi
            else:
                phi = 0.0
        else:
            phi = 0.0
            theta = 0.0
        x = phi / pi / 2 + 0.5
        y = theta / pi + 0.5
        h = distance - self.radius
        return (x, y, h)

    def get_tangent_plane_under(self, position: LPoint3d) -> tuple[LPoint3d, LPoint3d, LPoint3d]:
        (phi, theta, _h) = self.cartesian_to_geodetic(position)
        cos_s = cos(phi)
        sin_s = sin(phi)
        sin_r = sin(theta + pi / 2)
        cos_r = cos(theta + pi / 2)
        normal = LVector3d(
            cos_s * sin_r,
            sin_s * sin_r,
            -cos_r)
        normal.normalize()

        tangent = LVector3d(-sin_s, cos_s, 0)
        tangent.normalize()
        binormal = normal.cross(tangent)
        binormal.normalize()
        return (tangent, binormal, normal)


class EllipsoidModel(EllipsoidModelInterface):
    def __init__(self, axes: LVector3d):
        self.axes = axes
        self.radius: float = max(axes)

    def copy_extend(self, delta: float) -> SphereModel:
        return EllipsoidModel(self.axes + LVector3d(delta))

    def get_shape_axes(self) -> LVector3d:
        return self.axes

    def get_point_under(self, position: LPoint3d) -> LPoint3d:
        x0, x1, x2, _distance = DistancePointEllipsoid(
            *(self.axes / self.radius),
            abs(position[0] / self.radius),
            abs(position[1] / self.radius),
            abs(position[2] / self.radius),
            )
        return LPoint3d(
            copysign(x0 * self.radius, position[0]),
            copysign(x1 * self.radius, position[1]),
            copysign(x2 * self.radius, position[2]))

    def get_radius_under(self, position: LPoint3d) -> float:
        x0, x1, x2, _distance = DistancePointEllipsoid(
            *(self.axes / self.radius),
            abs(position[0] / self.radius),
            abs(position[1] / self.radius),
            abs(position[2] / self.radius),
            )
        r = self.radius * sqrt(x0 * x0 + x1 * x1 + x2 * x2)
        return r

    def get_average_radius(self) -> float:
        return self.radius

    def get_min_radius(self) -> float:
        return min(self.axes)

    def get_max_radius(self) -> float:
        return max(self.axes)

    def geodetic_to_cartesian(self, long: float, lat: float, h: float) -> LPoint3d:
        return TriaxialGeodeticToCartesian(self.axes, long, lat, h)

    def cartesian_to_geodetic(self, position: LPoint3d) -> tuple[float, float, float]:
        (phi, theta, h) = PointToTriaxialGeodetic(
            *(self.axes / self.radius),
            position[0] / self.radius,
            position[1] / self.radius,
            position[2] / self.radius,)
        return (phi, theta, h * self.radius)

    def parametric_to_cartesian(self, x: float, y: float, h: float) -> LPoint3d:
        cos_s = cos(2 * pi * x + pi)
        sin_s = sin(2 * pi * x + pi)
        sin_r = sin(pi * y)
        cos_r = cos(pi * y)
        p = LVector3d(
            (self.axes[0] + h) * cos_s * sin_r,
            (self.axes[1] + h) * sin_s * sin_r,
            -(self.axes[2] + h) * cos_r)
        return p

    def cartesian_to_parametric(self, position: LPoint3d) -> tuple[float, float, float]:
        scaled_position = LPoint3d(
            position[0] / self.axes[0],
            position[1] / self.axes[1],
            position[2] / self.axes[2]
            )
        distance = scaled_position.length()
        if distance > 0:
            theta = asin(scaled_position[2] / distance)
            if scaled_position[0] != 0.0:
                phi = atan2(scaled_position[1], scaled_position[0])
                #Offset phi by 180 deg with proper wrap around
                #phi = (phi + pi + pi) % (2 * pi) - pi
            else:
                phi = 0.0
        else:
            phi = 0.0
            theta = 0.0
        x = phi / pi / 2 + 0.5
        y = theta / pi + 0.5
        h = distance - self.radius
        return (x, y, h)

    def get_tangent_plane_under(self, position: LPoint3d) -> tuple[LPoint3d, LPoint3d, LPoint3d]:
        (phi, theta, _h) = self.cartesian_to_geodetic(position)
        cos_s = cos(phi)
        sin_s = sin(phi)
        sin_r = sin(theta + pi / 2)
        cos_r = cos(theta + pi / 2)
        normal = LVector3d(
            cos_s * sin_r,
            sin_s * sin_r,
            -cos_r)
        normal.normalize()

        tangent = LVector3d(-sin_s, cos_s, 0)
        tangent.normalize()
        binormal = normal.cross(tangent)
        binormal.normalize()
        return (tangent, binormal, normal)
