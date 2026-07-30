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

"""Cube face patch generation for spherical mapping.

This module provides functions for creating spherical patches by mapping square
regions of a cube face onto a sphere. It includes two mapping methods:

1. Squared Distance Mapping: Maps cube faces to spheres using a squared distance
   formula that provides better area distribution than simple normalization.

2. Normalized Mapping: Maps cube faces to spheres using simple normalization,
   which is faster but has less uniform area distribution.

Both methods support adaptive tessellation, skirts, and various coordinate
transformations for creating seamless spherical surfaces.
"""

from math import sqrt
from typing import Optional

from panda3d.core import LPoint3d, LVector3d, NodePath

from ...pstats import named_pstat
from .core import empty_geom, empty_node
from .tessellation import (
    TessellationInfo,
    make_adapted_square_primitives,
    make_adapted_square_primitives_skirt,
    make_config,
    make_primitives_skirt,
    make_square_primitives,
)


def SquarePatch(
    height: float,
    inner: int,
    outer: Optional[list[int]],
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    offset: Optional[float] = None,
) -> NodePath:
    """Create a flat square patch on a cube face with adaptive tessellation.

    Generates a tessellated square patch positioned on a cube face at a fixed
    height. The patch can use adaptive tessellation along its edges to match
    neighboring patches of different resolutions.

    Args:
        height: Distance from origin to the cube face.
        inner: Number of subdivisions along each inner edge.
        outer: Optional list of 4 integers for outer edge subdivisions
            [right, front, left, back]. If None, all edges use inner value.
        x0: Starting X coordinate in [0,1] range.
        y0: Starting Y coordinate in [0,1] range.
        x1: Ending X coordinate in [0,1] range.
        y1: Ending Y coordinate in [0,1] range.
        offset: Z offset for positioning. If None, uses height value.

    Returns:
        NodePath containing the square patch geometry with vertices, normals,
        tangents, binormals, and texture coordinates.

    Notes:
        - Coordinates are mapped from [0,1] to [-1,1] range.
        - The patch is positioned in the XY plane at Z=height.
        - Normal vectors point in +Z direction (0, 0, 1).
        - Tangents point in +X direction (1, 0, 0) and binormals in +Y (0, 1, 0).
    """
    nb_vertices, inner, outer, ratio = make_config(inner, outer)

    path, node = empty_node('uv')
    gvw, gcw, gtw, gnw, gtanw, gbiw, prim, geom = empty_geom(
        'cube', nb_vertices * nb_vertices, inner * inner * 6, tanbin=True
    )
    node.add_geom(geom)

    dx = x1 - x0
    dy = y1 - y0

    if offset is None:
        offset = height

    for i in range(0, nb_vertices):
        for j in range(0, nb_vertices):
            x = x0 + i * dx / inner
            y = y0 + j * dy / inner

            x = 2.0 * x - 1.0
            y = 2.0 * y - 1.0

            u = float(i) / inner
            v = float(j) / inner

            gtw.add_data2(u, v)
            gvw.add_data3(x * height, y * height, height)
            gnw.add_data3(0, 0, 1.0)
            gtanw.add_data3(1, 0, 0)
            gbiw.add_data3(0, 1, 0)

    make_adapted_square_primitives(prim, inner, nb_vertices, ratio)
    prim.closePrimitive()
    geom.addPrimitive(prim)

    return path


@named_pstat("geom")
def SquaredDistanceSquarePatch(
    axes: LVector3d,
    tessellation: TessellationInfo,
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    has_offset: bool = False,
    offset: Optional[float] = None,
    use_patch_adaptation: bool = True,
    use_patch_skirts: bool = True,
    skirt_size: float = 0.05,
    skirt_uv: float = 0.05,
    use_jacobian: bool = True,
) -> NodePath:
    """Create a spherical patch using squared distance cube-to-sphere mapping.

    Generates a tessellated patch on an ellipsoid surface by mapping a square
    region of a cube face using the squared distance formula. This mapping
    provides better area distribution than simple normalization, reducing
    distortion near the cube edges.

    The squared distance formula maps cube coordinates (x,y,z) to sphere
    coordinates using:
        x' = x * sqrt(1 - y^2/2 - z^2/2 + y^2z^2/3)
        y' = y * sqrt(1 - z^2/2 - x^2/2 + z^2x^2/3)
        z' = z * sqrt(1 - x^2/2 - y^2/2 + x^2y^2/3)

    Args:
        axes: LVector3d containing the ellipsoid semi-axes (radius_x, radius_y, radius_z).
        tessellation: TessellationInfo object specifying subdivision levels.
        x0: Starting X coordinate in [0,1] range.
        y0: Starting Y coordinate in [0,1] range.
        x1: Ending X coordinate in [0,1] range.
        y1: Ending Y coordinate in [0,1] range.
        has_offset: If True, apply an offset from the patch center.
        offset: Offset magnitude from patch center if has_offset is True.
        use_patch_adaptation: If True, use adaptive tessellation along edges.
        use_patch_skirts: If True, add skirts around patch edges.
        skirt_size: Size of edge skirts (as fraction of patch size).
        skirt_uv: UV coordinate extension for skirt vertices.
        use_jacobian: If True, store Jacobian data instead of computing tangent/binormal.

    Returns:
        NodePath containing the spherical patch geometry with vertices, normals,
        and either Jacobian data or tangent/binormal vectors.

    Notes:
        - Provides better area uniformity than normalized mapping.
        - Normal vectors are computed using ellipsoid geometry.
        - Skirts prevent gaps between adjacent patches.
        - Jacobian data can be used for shader-based tangent computation.
    """
    path, node = empty_node('uv')
    inner = tessellation.inner
    nb_vertices = inner + 1
    nb_points = nb_vertices * nb_vertices
    nb_primitives = inner * inner
    if use_patch_skirts:
        nb_points += nb_vertices * 4
        nb_primitives += inner * 4
    if use_jacobian:
        gvw, gcw, gtw, gnw, gtanw, gbiw, prim, geom, jacobian = empty_geom(
            'cube', nb_points, nb_primitives * 6, tanbin=False, jacobian=4
        )
    else:
        gvw, gcw, gtw, gnw, gtanw, gbiw, prim, geom = empty_geom('cube', nb_points, nb_primitives, tanbin=True)
    node.add_geom(geom)

    if has_offset:
        offset_vector = SquaredDistanceSquarePatchOffsetVector(axes, x0, y0, x1, y1) * offset

    dx = x1 - x0
    dy = y1 - y0

    normal_coefs = LVector3d(axes[1] * axes[2], axes[0] * axes[2], axes[0] * axes[1])

    def _make_point(u, v, point_axes):
        """Write a single squared-distance-mapped vertex."""
        x = x0 + u * dx
        y = y0 + v * dy
        x = 2.0 * x - 1.0
        y = 2.0 * y - 1.0
        z = 1.0
        x2 = x * x
        y2 = y * y
        z2 = z * z
        xp = x * sqrt(1.0 - y2 * 0.5 - z2 * 0.5 + y2 * z2 / 3.0)
        yp = y * sqrt(1.0 - z2 * 0.5 - x2 * 0.5 + z2 * x2 / 3.0)
        zp = z * sqrt(1.0 - x2 * 0.5 - y2 * 0.5 + x2 * y2 / 3.0)
        point = LPoint3d(xp, yp, zp)
        normal = LVector3d(point)
        gtw.add_data2(u, v)
        point.componentwise_mult(point_axes)
        if has_offset:
            point -= offset_vector
        gvw.add_data3d(point)
        normal.componentwise_mult(normal_coefs)
        normal.normalize()
        gnw.add_data3d(normal)
        if use_jacobian:
            jacobian.add_data4d(x, y, sqrt(0.5 - x * x / 6), sqrt(0.5 - y * y / 6))
        else:
            tangent = LVector3d(1.0, x * y * (z2 / 3.0 - 0.5), x * z * (y2 / 3.0 - 0.5))
            tangent.componentwise_mult(axes)
            tangent.normalize()
            binormal = normal.cross(tangent)
            binormal.normalize()
            gtanw.add_data3d(tangent)
            gbiw.add_data3d(binormal)

    for i in range(0, nb_vertices):
        for j in range(0, nb_vertices):
            _make_point(float(i) / inner, float(j) / inner, axes)

    if use_patch_skirts:
        reduced_axes = axes - LVector3d(max(dx, dy) * skirt_size)
        for a in range(0, 4):
            for b in range(0, nb_vertices):
                if a == 0:
                    i, j = 0, b
                elif a == 1:
                    i, j = inner, b
                elif a == 2:
                    i, j = b, 0
                else:
                    i, j = b, inner
                _make_point(float(i) / inner, float(j) / inner, reduced_axes)

    if use_patch_adaptation:
        make_adapted_square_primitives(prim, inner, nb_vertices, tessellation.ratio)
        if use_patch_skirts:
            make_adapted_square_primitives_skirt(prim, inner, nb_vertices, tessellation.ratio)
    else:
        make_square_primitives(prim, inner, nb_vertices)
        if use_patch_skirts:
            make_primitives_skirt(prim, inner, nb_vertices)
    prim.closePrimitive()
    geom.addPrimitive(prim)

    return path


def SquaredDistanceSquarePatchPoint(
    axes: LVector3d,
    u: float,
    v: float,
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    offset: Optional[float] = None,
) -> LVector3d:
    """Calculate a point on a spherical patch using squared distance mapping.

    Computes the 3D position of a point on an ellipsoid surface by mapping
    the given UV coordinates through squared distance cube-to-sphere mapping.

    Args:
        axes: LVector3d containing the ellipsoid semi-axes (radius_x, radius_y, radius_z).
        u: U coordinate in [0,1] range within the patch.
        v: V coordinate in [0,1] range within the patch.
        x0: Starting X coordinate of the patch in [0,1] range.
        y0: Starting Y coordinate of the patch in [0,1] range.
        x1: Ending X coordinate of the patch in [0,1] range.
        y1: Ending Y coordinate of the patch in [0,1] range.
        offset: Optional offset magnitude from patch center.

    Returns:
        LVector3d representing the 3D point on the ellipsoid surface.
    """

    if offset is not None:
        offset_vector = SquaredDistanceSquarePatchOffsetVector(axes, x0, y0, x1, y1)

    dx = x1 - x0
    dy = y1 - y0

    x = x0 + u * dx
    y = y0 + v * dy

    x = 2.0 * x - 1.0
    y = 2.0 * y - 1.0
    z = 1.0

    x2 = x * x
    y2 = y * y
    z2 = z * z

    x *= sqrt(1.0 - y2 * 0.5 - z2 * 0.5 + y2 * z2 / 3.0)
    y *= sqrt(1.0 - z2 * 0.5 - x2 * 0.5 + z2 * x2 / 3.0)
    z *= sqrt(1.0 - x2 * 0.5 - y2 * 0.5 + x2 * y2 / 3.0)
    point = LVector3d(x, y, z)
    point.componentwise_mult(axes)

    if offset is not None:
        point -= offset_vector * offset

    return point


def SquaredDistanceSquarePatchNormal(
    axes: LVector3d,
    u: float,
    v: float,
    x0: float,
    y0: float,
    x1: float,
    y1: float,
) -> LVector3d:
    """Calculate the surface normal at a point on a squared distance patch.

    Computes the normalized surface normal at the given UV coordinates on
    an ellipsoid surface using squared distance cube-to-sphere mapping.

    Args:
        axes: LVector3d containing the ellipsoid semi-axes (radius_x, radius_y, radius_z).
        u: U coordinate in [0,1] range within the patch.
        v: V coordinate in [0,1] range within the patch.
        x0: Starting X coordinate of the patch in [0,1] range.
        y0: Starting Y coordinate of the patch in [0,1] range.
        x1: Ending X coordinate of the patch in [0,1] range.
        y1: Ending Y coordinate of the patch in [0,1] range.

    Returns:
        Normalized LVector3d representing the surface normal.
    """

    dx = x1 - x0
    dy = y1 - y0

    x = x0 + u * dx
    y = y0 + v * dy

    x = 2.0 * x - 1.0
    y = 2.0 * y - 1.0
    z = 1.0

    x2 = x * x
    y2 = y * y
    z2 = z * z

    x *= sqrt(1.0 - y2 * 0.5 - z2 * 0.5 + y2 * z2 / 3.0)
    y *= sqrt(1.0 - z2 * 0.5 - x2 * 0.5 + z2 * x2 / 3.0)
    z *= sqrt(1.0 - x2 * 0.5 - y2 * 0.5 + x2 * y2 / 3.0)
    normal = LVector3d(x, y, z)
    normal_coefs = LVector3d(axes[1] * axes[2], axes[0] * axes[2], axes[0] * axes[1])
    normal.componentwise_mult(normal_coefs)
    normal.normalize()

    return normal


def SquaredDistanceSquarePatchOffsetVector(
    axes: LVector3d,
    x0: float,
    y0: float,
    x1: float,
    y1: float,
) -> LVector3d:
    """Calculate the offset vector for the center of a squared distance patch.

    Computes the position of the patch center, which is used as an offset
    reference point when creating patches with offsets.

    Args:
        axes: LVector3d containing the ellipsoid semi-axes.
        x0: Starting X coordinate of the patch in [0,1] range.
        y0: Starting Y coordinate of the patch in [0,1] range.
        x1: Ending X coordinate of the patch in [0,1] range.
        y1: Ending Y coordinate of the patch in [0,1] range.

    Returns:
        LVector3d representing the patch center position.
    """

    return SquaredDistanceSquarePatchPoint(axes, 0.5, 0.5, x0, y0, x1, y1, None)


def SquaredDistanceSquarePatchBoundingPoints(
    axes: LVector3d,
    min_height: float,
    max_height: float,
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    offset: Optional[float] = None,
) -> list[LPoint3d]:
    """Calculate bounding points for a squared distance patch with height variation.

    Computes a set of points that define the bounding volume of a spherical
    patch, accounting for minimum and maximum height variations. The points
    are sampled at the corners, edge midpoints, and center of the patch.

    Args:
        axes: LVector3d containing the ellipsoid semi-axes.
        min_height: Minimum height variation (can be negative for valleys).
        max_height: Maximum height variation (for peaks).
        x0: Starting X coordinate of the patch in [0,1] range.
        y0: Starting Y coordinate of the patch in [0,1] range.
        x1: Ending X coordinate of the patch in [0,1] range.
        y1: Ending Y coordinate of the patch in [0,1] range.
        offset: Optional offset magnitude from patch center.

    Returns:
        List of LPoint3d objects representing the bounding volume corners.

    Notes:
        - Samples 9 points per height level (corners, edge midpoints, center).
        - If min_height == max_height, only one height level is sampled.
        - Height is applied along the surface normal direction.
        - Offset is applied to all points if specified.
    """
    points = []
    if min_height != max_height:
        heights = (min_height, max_height)
    else:
        heights = (min_height,)
    if offset is not None:
        offset_vector = SquaredDistanceSquarePatchOffsetVector(axes, x0, y0, x1, y1) * offset
    for height in heights:
        for i in (0.0, 0.5, 1.0):
            for j in (0.0, 0.5, 1.0):
                point = SquaredDistanceSquarePatchPoint(axes, i, j, x0, y0, x1, y1, None)
                if height != 0:
                    normal = SquaredDistanceSquarePatchNormal(axes, i, j, x0, y0, x1, y1)
                    point += normal * height
                if offset is not None:
                    point -= offset_vector
                points.append(point)
    return points


@named_pstat("geom")
def NormalizedSquarePatch(
    axes: LVector3d,
    tessellation: TessellationInfo,
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    has_offset: bool = False,
    offset: Optional[float] = None,
    use_patch_adaptation: bool = True,
    use_patch_skirts: bool = True,
    skirt_size: float = 0.05,
    skirt_uv: float = 0.05,
    use_jacobian: bool = True,
) -> NodePath:
    """Create a spherical patch using normalized cube-to-sphere mapping.

    Generates a tessellated patch on an ellipsoid surface by mapping a square
    region of a cube face using simple normalization. This is faster than
    squared distance mapping but produces less uniform area distribution.

    The normalized mapping simply normalizes the cube coordinates:
        point = normalize(x, y, z)

    Args:
        axes: LVector3d containing the ellipsoid semi-axes (radius_x, radius_y, radius_z).
        tessellation: TessellationInfo object specifying subdivision levels.
        x0: Starting X coordinate in [0,1] range.
        y0: Starting Y coordinate in [0,1] range.
        x1: Ending X coordinate in [0,1] range.
        y1: Ending Y coordinate in [0,1] range.
        has_offset: If True, apply an offset from the patch center.
        offset: Offset magnitude from patch center if has_offset is True.
        use_patch_adaptation: If True, use adaptive tessellation along edges.
        use_patch_skirts: If True, add skirts around patch edges.
        skirt_size: Size of edge skirts (as fraction of patch size).
        skirt_uv: UV coordinate extension for skirt vertices.
        use_jacobian: If True, store Jacobian data instead of computing tangent/binormal.

    Returns:
        NodePath containing the spherical patch geometry with vertices, normals,
        and either Jacobian data or tangent/binormal vectors.

    Notes:
        - Simpler and faster than squared distance mapping.
        - Results in less uniform area distribution (more distortion near edges).
        - Normal vectors are computed using ellipsoid geometry.
        - Skirts prevent gaps between adjacent patches.
        - Jacobian data can be used for shader-based tangent computation.
    """
    path, node = empty_node('uv')
    inner = tessellation.inner
    nb_vertices = inner + 1
    nb_points = nb_vertices * nb_vertices
    nb_primitives = inner * inner
    if use_patch_skirts:
        nb_points += nb_vertices * 4
        nb_primitives += inner * 4
    if use_jacobian:
        gvw, gcw, gtw, gnw, gtanw, gbiw, prim, geom, jacobian = empty_geom(
            'cube', nb_points, nb_primitives * 6, tanbin=False, jacobian=3
        )
    else:
        gvw, gcw, gtw, gnw, gtanw, gbiw, prim, geom = empty_geom('cube', nb_points, nb_primitives, tanbin=True)
    node.add_geom(geom)

    if has_offset:
        offset_vector = NormalizedSquarePatchOffsetVector(axes, x0, y0, x1, y1) * offset

    dx = x1 - x0
    dy = y1 - y0

    normal_coefs = LVector3d(axes[1] * axes[2], axes[0] * axes[2], axes[0] * axes[1])

    def _make_point(u, v, point_axes):
        """Write a single normalized-mapped vertex."""
        x = x0 + u * dx
        y = y0 + v * dy
        x = 2.0 * x - 1.0
        y = 2.0 * y - 1.0
        point = LVector3d(x, y, 1.0)
        point.normalize()
        normal = LVector3d(point)
        gtw.add_data2(u, v)
        point.componentwise_mult(point_axes)
        if has_offset:
            point -= offset_vector
        gvw.add_data3d(point)
        normal.componentwise_mult(normal_coefs)
        normal.normalize()
        gnw.add_data3d(normal)
        if use_jacobian:
            jacobian.add_data3d(x, y, 1 / (x * x + y * y + 1))
        else:
            tangent = LVector3d(1.0 + y * y, -x * y, -x)
            binormal = LVector3d(-x * y, 1.0 + x * x, -y)
            tangent.componentwise_mult(axes)
            tangent.normalize()
            binormal.componentwise_mult(axes)
            binormal.normalize()
            gtanw.add_data3d(tangent)
            gbiw.add_data3d(binormal)

    for i in range(0, nb_vertices):
        for j in range(0, nb_vertices):
            _make_point(float(i) / inner, float(j) / inner, axes)

    if use_patch_skirts:
        reduced_axes = axes - LVector3d(max(dx, dy) * skirt_size)
        for a in range(0, 4):
            for b in range(0, nb_vertices):
                if a == 0:
                    i, j = 0, b
                elif a == 1:
                    i, j = inner, b
                elif a == 2:
                    i, j = b, 0
                else:
                    i, j = b, inner
                _make_point(float(i) / inner, float(j) / inner, reduced_axes)

    if use_patch_adaptation:
        make_adapted_square_primitives(prim, inner, nb_vertices, tessellation.ratio)
        if use_patch_skirts:
            make_adapted_square_primitives_skirt(prim, inner, nb_vertices, tessellation.ratio)
    else:
        make_square_primitives(prim, inner, nb_vertices)
        if use_patch_skirts:
            make_primitives_skirt(prim, inner, nb_vertices)
    prim.closePrimitive()
    geom.addPrimitive(prim)

    return path


def NormalizedSquarePatchPoint(
    axes: LVector3d,
    u: float,
    v: float,
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    offset: Optional[float] = None,
) -> LVector3d:
    """Calculate a point on a spherical patch using normalized mapping.

    Computes the 3D position of a point on an ellipsoid surface by mapping
    the given UV coordinates through simple normalization.

    Args:
        axes: LVector3d containing the ellipsoid semi-axes (radius_x, radius_y, radius_z).
        u: U coordinate in [0,1] range within the patch.
        v: V coordinate in [0,1] range within the patch.
        x0: Starting X coordinate of the patch in [0,1] range.
        y0: Starting Y coordinate of the patch in [0,1] range.
        x1: Ending X coordinate of the patch in [0,1] range.
        y1: Ending Y coordinate of the patch in [0,1] range.
        offset: Optional offset magnitude from patch center.

    Returns:
        LVector3d representing the 3D point on the ellipsoid surface.
    """
    dx = x1 - x0
    dy = y1 - y0
    x = x0 + u * dx
    y = y0 + v * dy
    vec = LVector3d(2.0 * x - 1.0, 2.0 * y - 1.0, 1.0)
    vec.normalize()
    vec.componentwise_mult(axes)

    if offset is not None:
        offset_vector = NormalizedSquarePatchOffsetVector(axes, x0, y0, x1, y1)
        vec -= offset_vector * offset

    return vec


def NormalizedSquarePatchNormal(
    axes: LVector3d,
    u: float,
    v: float,
    x0: float,
    y0: float,
    x1: float,
    y1: float,
) -> LVector3d:
    """Calculate the surface normal at a point on a normalized patch.

    Computes the normalized surface normal at the given UV coordinates on
    an ellipsoid surface using simple normalization mapping.

    Args:
        axes: LVector3d containing the ellipsoid semi-axes (radius_x, radius_y, radius_z).
        u: U coordinate in [0,1] range within the patch.
        v: V coordinate in [0,1] range within the patch.
        x0: Starting X coordinate of the patch in [0,1] range.
        y0: Starting Y coordinate of the patch in [0,1] range.
        x1: Ending X coordinate of the patch in [0,1] range.
        y1: Ending Y coordinate of the patch in [0,1] range.

    Returns:
        Normalized LVector3d representing the surface normal.
    """
    dx = x1 - x0
    dy = y1 - y0
    x = x0 + u * dx
    y = y0 + v * dy
    normal = LVector3d(2.0 * x - 1.0, 2.0 * y - 1.0, 1.0)
    normal.normalize()
    normal_coefs = LVector3d(axes[1] * axes[2], axes[0] * axes[2], axes[0] * axes[1])
    normal.componentwise_mult(normal_coefs)
    normal.normalize()

    return normal


def NormalizedSquarePatchOffsetVector(
    axes: LVector3d,
    x0: float,
    y0: float,
    x1: float,
    y1: float,
) -> LVector3d:
    """Calculate the offset vector for the center of a normalized patch.

    Computes the position of the patch center, which is used as an offset
    reference point when creating patches with offsets.

    Args:
        axes: LVector3d containing the ellipsoid semi-axes.
        x0: Starting X coordinate of the patch in [0,1] range.
        y0: Starting Y coordinate of the patch in [0,1] range.
        x1: Ending X coordinate of the patch in [0,1] range.
        y1: Ending Y coordinate of the patch in [0,1] range.

    Returns:
        LVector3d representing the patch center position.
    """
    return NormalizedSquarePatchPoint(axes, 0.5, 0.5, x0, y0, x1, y1, None)


def NormalizedSquarePatchBoundingPoints(
    axes: LVector3d,
    min_height: float,
    max_height: float,
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    offset: Optional[float] = None,
) -> list[LPoint3d]:
    """Calculate bounding points for a normalized patch with height variation.

    Computes a set of points that define the bounding volume of a spherical
    patch, accounting for minimum and maximum height variations. The points
    are sampled at the corners, edge midpoints, and center of the patch.

    Args:
        axes: LVector3d containing the ellipsoid semi-axes.
        min_height: Minimum height variation (can be negative for valleys).
        max_height: Maximum height variation (for peaks).
        x0: Starting X coordinate of the patch in [0,1] range.
        y0: Starting Y coordinate of the patch in [0,1] range.
        x1: Ending X coordinate of the patch in [0,1] range.
        y1: Ending Y coordinate of the patch in [0,1] range.
        offset: Optional offset magnitude from patch center.

    Returns:
        List of LPoint3d objects representing the bounding volume corners.

    Notes:
        - Samples 9 points per height level (corners, edge midpoints, center).
        - If min_height == max_height, only one height level is sampled.
        - Height is applied along the surface normal direction.
        - Offset is applied to all points if specified.
    """
    points = []
    if min_height != max_height:
        heights = (min_height, max_height)
    else:
        heights = (min_height,)
    if offset is not None:
        offset_vector = NormalizedSquarePatchOffsetVector(axes, x0, y0, x1, y1) * offset
    for height in heights:
        for i in (0.0, 0.5, 1.0):
            for j in (0.0, 0.5, 1.0):
                point = NormalizedSquarePatchPoint(axes, i, j, x0, y0, x1, y1, None)
                if height != 0:
                    normal = NormalizedSquarePatchNormal(axes, i, j, x0, y0, x1, y1)
                    point += normal * height
                if offset is not None:
                    point -= offset_vector
                points.append(point)
    return points
