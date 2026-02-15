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

"""UV patch geometry generators.

This module provides functions for generating spherical surface patches using
UV (latitude/longitude) parameterization.
"""

from math import cos, pi, sin

from panda3d.core import LPoint3d, LVector3d, NodePath

from ...pstats import named_pstat
from .core import empty_geom, empty_node


def UVPatchPoint(
    axes: LVector3d, r: float, s: float, x0: float, y0: float, x1: float, y1: float, offset: float = 0.0
) -> LPoint3d:
    """Calculate point on UV patch.

    Computes the 3D position of a point on a spherical UV patch given
    parametric coordinates (r, s) within the patch bounds.

    Args:
        axes: Semi-axes of the ellipsoid (rx, ry, rz).
        r: Parametric coordinate in latitude direction (0.0 to 1.0 within patch).
        s: Parametric coordinate in longitude direction (0.0 to 1.0 within patch).
        x0: Minimum longitude coordinate of patch (0.0 to 1.0 globally).
        y0: Minimum latitude coordinate of patch (0.0 to 1.0 globally).
        x1: Maximum longitude coordinate of patch (0.0 to 1.0 globally).
        y1: Maximum latitude coordinate of patch (0.0 to 1.0 globally).
        offset: Offset distance from surface center.
            Default is 0.0.

    Returns:
        3D point on the UV patch surface.

    Notes:
        - (r, s) = (0, 0) maps to patch corner (x0, y0).
        - (r, s) = (1, 1) maps to patch corner (x1, y1).
        - Uses spherical coordinates: longitude θ = 2π(x0 + s·Δx), latitude φ = π(y0 + r·Δy).
        - Point is offset inward if offset > 0.

    Example:
        >>> from panda3d.core import LVector3d
        >>> axes = LVector3d(1, 1, 1)
        >>> # Get center point of patch covering upper-right quadrant
        >>> point = UVPatchPoint(axes, 0.5, 0.5, 0.5, 0, 1.0, 0.5)
    """
    dx = x1 - x0
    dy = y1 - y0

    cos_s = cos(2 * pi * (x0 + s * dx) + pi)
    sin_s = sin(2 * pi * (x0 + s * dx) + pi)
    sin_r = sin(pi * (y0 + r * dy))
    cos_r = cos(pi * (y0 + r * dy))
    point = LPoint3d(cos_s * sin_r, sin_s * sin_r, -cos_r)
    point.componentwise_mult(axes)

    if offset != 0.0:
        offset_vector = UVPatchOffsetVector(axes, x0, y0, x1, y1)
        point -= offset_vector * offset

    return point


def UVPatchNormal(axes: LVector3d, r: float, s: float, x0: float, y0: float, x1: float, y1: float) -> LPoint3d:
    """Calculate normal on UV patch.

    Computes the outward-pointing unit normal vector at a point on a
    spherical UV patch.

    Args:
        axes: Semi-axes of the ellipsoid (rx, ry, rz).
        r: Parametric coordinate in latitude direction (0.0 to 1.0 within patch).
        s: Parametric coordinate in longitude direction (0.0 to 1.0 within patch).
        x0: Minimum longitude coordinate of patch (0.0 to 1.0 globally).
        y0: Minimum latitude coordinate of patch (0.0 to 1.0 globally).
        x1: Maximum longitude coordinate of patch (0.0 to 1.0 globally).
        y1: Maximum latitude coordinate of patch (0.0 to 1.0 globally).

    Returns:
        Normalized normal vector pointing outward from the ellipsoid surface.

    Notes:
        - For a sphere (equal axes), normal points radially outward.
        - For an ellipsoid, normal is perpendicular to the surface but not radial.
        - Normal is computed using the gradient of the ellipsoid equation.
    """
    dx = x1 - x0
    dy = y1 - y0

    cos_s = cos(2 * pi * (x0 + s * dx) + pi)
    sin_s = sin(2 * pi * (x0 + s * dx) + pi)
    sin_r = sin(pi * (y0 + r * dy))
    cos_r = cos(pi * (y0 + r * dy))
    normal = LPoint3d(axes[1] * axes[2] * cos_s * sin_r, axes[0] * axes[2] * sin_s * sin_r, -axes[0] * axes[1] * cos_r)
    normal.normalize()
    return normal


def UVPatchOffsetVector(axes: LVector3d, x0: float, y0: float, x1: float, y1: float) -> LVector3d:
    """Calculate offset vector for UV patch.

    Computes the vector from the origin to the center of a UV patch.

    Args:
        axes: Semi-axes of the ellipsoid (rx, ry, rz).
        x0: Minimum longitude coordinate of patch (0.0 to 1.0).
        y0: Minimum latitude coordinate of patch (0.0 to 1.0).
        x1: Maximum longitude coordinate of patch (0.0 to 1.0).
        y1: Maximum latitude coordinate of patch (0.0 to 1.0).

    Returns:
        Vector from origin to patch center on the ellipsoid surface.

    Notes:
        - Patch center is at ((x0+x1)/2, (y0+y1)/2) in UV space.
    """
    dx = x1 - x0
    dy = y1 - y0
    v = LVector3d(
        cos(2 * pi * (x0 + dx / 2) + pi) * sin(pi * (y0 + dy / 2)),
        sin(2 * pi * (x0 + dx / 2) + pi) * sin(pi * (y0 + dy / 2)),
        -cos(pi * (y0 + dy / 2)),
    )
    v.componentwise_mult(axes)
    return v


@named_pstat("geom")
def UVPatch(
    axes: LVector3d,
    rings: int,
    sectors: int,
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    global_texture: bool = False,
    inv_texture_u: bool = False,
    inv_texture_v: bool = False,
    offset: float = 0.0,
    use_patch_skirts=True,
    skirt_size=0.001,
    skirt_uv=0.001,
) -> NodePath:
    """Create UV-mapped spherical patch.

    Generates a rectangular patch on a spherical surface using UV
    (latitude/longitude) parameterization.

    Args:
        axes: Semi-axes of the ellipsoid (rx, ry, rz).
        rings: Number of subdivisions in latitude direction.
        sectors: Number of subdivisions in longitude direction.
        x0: Minimum longitude coordinate (0.0 to 1.0, where 0=0° and 1=360°).
        y0: Minimum latitude coordinate (0.0 to 1.0, where 0=90°N and 1=90°S).
        x1: Maximum longitude coordinate (0.0 to 1.0).
        y1: Maximum latitude coordinate (0.0 to 1.0).
        global_texture: If True, texture coordinates map to global sphere (0-1).
            If False, texture coordinates map to patch only (0-1 within patch).
            Default is False.
        inv_texture_u: If True, invert U texture coordinates. Default is False.
        inv_texture_v: If True, invert V texture coordinates. Default is False.
        offset: Offset distance from surface.
            Default is 0.0.
        use_patch_skirts: If True, generate skirts along patch edges to hide gaps.
            Default is True.
        skirt_size: Depth of skirts as a fraction of patch size. Default is 0.001.
        skirt_uv: UV offset for skirt texture coordinates. Default is 0.001.

    Returns:
        NodePath containing the patch geometry with positions, normals,
        texture coordinates, tangents, and binormals.

    Notes:
        - Geometry has (rings+1) × (sectors+1) vertices.
        - Creates rings × sectors quads (2 triangles each).
        - Tangents point in longitude direction.
        - Binormals point in latitude direction.
    """
    r_sectors = sectors + 1
    r_rings = rings + 1

    nb_data = r_rings * r_sectors
    # Reserve space for primitive indices: each quad becomes 2 triangles with 3 indices each
    nb_vertices = rings * sectors * 2 * 3
    if use_patch_skirts:
        # Add vertices for 4 edges
        nb_data += 2 * r_rings + 2 * r_sectors
        # Add indices for skirt: each segment becomes 2 triangles with 3 indices each
        nb_vertices += (2 * rings + 2 * sectors) * 6

    (path, node) = empty_node('uv')
    (gvw, gcw, gtw, gnw, gtanw, gbiw, prim, geom) = empty_geom('uv', nb_data, nb_vertices, tanbin=True)

    dx = x1 - x0
    dy = y1 - y0

    if offset != 0.0:
        offset_vector = UVPatchOffsetVector(axes, x0, y0, x1, y1) * offset

    normal_coefs = LVector3d(axes[1] * axes[2], axes[0] * axes[2], axes[0] * axes[1])

    # Generate main patch vertices
    for r in range(0, r_rings):
        for s in range(0, r_sectors):
            cos_s = cos(2 * pi * (x0 + s * dx / sectors) + pi)
            sin_s = sin(2 * pi * (x0 + s * dx / sectors) + pi)
            sin_r = sin(pi * (y0 + r * dy / rings))
            cos_r = cos(pi * (y0 + r * dy / rings))
            point = LVector3d(cos_s * sin_r, sin_s * sin_r, -cos_r)
            normal = LVector3d(point)
            if sin_r != 0:
                tangent = LVector3d(-axes[0] * point[1], axes[1] * point[0], 0)
            else:
                tangent = LVector3d(-axes[0], 0, 0)
            binormal = LVector3d(cos_s * cos_r, sin_s * cos_r, sin_r)
            if global_texture:
                gtw.add_data2((x0 + s * dx / sectors), (y0 + r * dy / rings))
            else:
                u = s / sectors
                v = r / rings
                if inv_texture_v:
                    v = 1.0 - v
                if inv_texture_u:
                    u = 1.0 - u
                gtw.add_data2(u, v)
            point.componentwise_mult(axes)
            if offset != 0.0:
                point -= offset_vector
            gvw.add_data3d(point)
            normal.componentwise_mult(normal_coefs)
            normal.normalize()
            gnw.add_data3d(normal)
            tangent.normalize()
            gtanw.add_data3d(tangent)
            binormal.componentwise_mult(axes)
            binormal.normalize()
            gbiw.add_data3d(binormal)

    # Generate skirt vertices if enabled
    if use_patch_skirts:
        # Reduce axes for skirt depth
        reduced_axes = axes - LVector3d(skirt_size)

        # Edge order: 0=left, 1=right, 2=bottom, 3=top
        for edge in range(0, 4):
            if edge == 0:  # Left edge (s=0, all r)
                for r in range(0, r_rings):
                    s = 0
                    u_skirt = -skirt_uv if not inv_texture_u else 1.0 + skirt_uv
                    v_skirt = r / rings
                    if inv_texture_v:
                        v_skirt = 1.0 - v_skirt

                    cos_s = cos(2 * pi * (x0 + s * dx / sectors) + pi)
                    sin_s = sin(2 * pi * (x0 + s * dx / sectors) + pi)
                    sin_r = sin(pi * (y0 + r * dy / rings))
                    cos_r = cos(pi * (y0 + r * dy / rings))
                    point = LVector3d(cos_s * sin_r, sin_s * sin_r, -cos_r)
                    normal = LVector3d(point)
                    if sin_r != 0:
                        tangent = LVector3d(-axes[0] * point[1], axes[1] * point[0], 0)
                    else:
                        tangent = LVector3d(-axes[0], 0, 0)
                    binormal = LVector3d(cos_s * cos_r, sin_s * cos_r, sin_r)

                    if not global_texture:
                        gtw.add_data2(u_skirt, v_skirt)
                    else:
                        gtw.add_data2((x0 + s * dx / sectors), (y0 + r * dy / rings))

                    point.componentwise_mult(reduced_axes)
                    if offset != 0.0:
                        point -= offset_vector
                    gvw.add_data3d(point)
                    normal.componentwise_mult(normal_coefs)
                    normal.normalize()
                    gnw.add_data3d(normal)
                    tangent.normalize()
                    gtanw.add_data3d(tangent)
                    binormal.componentwise_mult(axes)
                    binormal.normalize()
                    gbiw.add_data3d(binormal)

            elif edge == 1:  # Right edge (s=sectors, all r)
                for r in range(0, r_rings):
                    s = sectors
                    u_skirt = 1.0 + skirt_uv if not inv_texture_u else -skirt_uv
                    v_skirt = r / rings
                    if inv_texture_v:
                        v_skirt = 1.0 - v_skirt

                    cos_s = cos(2 * pi * (x0 + s * dx / sectors) + pi)
                    sin_s = sin(2 * pi * (x0 + s * dx / sectors) + pi)
                    sin_r = sin(pi * (y0 + r * dy / rings))
                    cos_r = cos(pi * (y0 + r * dy / rings))
                    point = LVector3d(cos_s * sin_r, sin_s * sin_r, -cos_r)
                    normal = LVector3d(point)
                    if sin_r != 0:
                        tangent = LVector3d(-axes[0] * point[1], axes[1] * point[0], 0)
                    else:
                        tangent = LVector3d(-axes[0], 0, 0)
                    binormal = LVector3d(cos_s * cos_r, sin_s * cos_r, sin_r)

                    if not global_texture:
                        gtw.add_data2(u_skirt, v_skirt)
                    else:
                        gtw.add_data2((x0 + s * dx / sectors), (y0 + r * dy / rings))

                    point.componentwise_mult(reduced_axes)
                    if offset != 0.0:
                        point -= offset_vector
                    gvw.add_data3d(point)
                    normal.componentwise_mult(normal_coefs)
                    normal.normalize()
                    gnw.add_data3d(normal)
                    tangent.normalize()
                    gtanw.add_data3d(tangent)
                    binormal.componentwise_mult(axes)
                    binormal.normalize()
                    gbiw.add_data3d(binormal)

            elif edge == 2:  # Bottom edge (r=0, all s)
                for s in range(0, r_sectors):
                    r = 0
                    u_skirt = s / sectors
                    if inv_texture_u:
                        u_skirt = 1.0 - u_skirt
                    v_skirt = -skirt_uv if not inv_texture_v else 1.0 + skirt_uv

                    cos_s = cos(2 * pi * (x0 + s * dx / sectors) + pi)
                    sin_s = sin(2 * pi * (x0 + s * dx / sectors) + pi)
                    sin_r = sin(pi * (y0 + r * dy / rings))
                    cos_r = cos(pi * (y0 + r * dy / rings))
                    point = LVector3d(cos_s * sin_r, sin_s * sin_r, -cos_r)
                    normal = LVector3d(point)
                    if sin_r != 0:
                        tangent = LVector3d(-axes[0] * point[1], axes[1] * point[0], 0)
                    else:
                        tangent = LVector3d(-axes[0], 0, 0)
                    binormal = LVector3d(cos_s * cos_r, sin_s * cos_r, sin_r)

                    if not global_texture:
                        gtw.add_data2(u_skirt, v_skirt)
                    else:
                        gtw.add_data2((x0 + s * dx / sectors), (y0 + r * dy / rings))

                    point.componentwise_mult(reduced_axes)
                    if offset != 0.0:
                        point -= offset_vector
                    gvw.add_data3d(point)
                    normal.componentwise_mult(normal_coefs)
                    normal.normalize()
                    gnw.add_data3d(normal)
                    tangent.normalize()
                    gtanw.add_data3d(tangent)
                    binormal.componentwise_mult(axes)
                    binormal.normalize()
                    gbiw.add_data3d(binormal)

            else:  # edge == 3, Top edge (r=rings, all s)
                for s in range(0, r_sectors):
                    r = rings
                    u_skirt = s / sectors
                    if inv_texture_u:
                        u_skirt = 1.0 - u_skirt
                    v_skirt = 1.0 + skirt_uv if not inv_texture_v else -skirt_uv

                    cos_s = cos(2 * pi * (x0 + s * dx / sectors) + pi)
                    sin_s = sin(2 * pi * (x0 + s * dx / sectors) + pi)
                    sin_r = sin(pi * (y0 + r * dy / rings))
                    cos_r = cos(pi * (y0 + r * dy / rings))
                    point = LVector3d(cos_s * sin_r, sin_s * sin_r, -cos_r)
                    normal = LVector3d(point)
                    if sin_r != 0:
                        tangent = LVector3d(-axes[0] * point[1], axes[1] * point[0], 0)
                    else:
                        tangent = LVector3d(-axes[0], 0, 0)
                    binormal = LVector3d(cos_s * cos_r, sin_s * cos_r, sin_r)

                    if not global_texture:
                        gtw.add_data2(u_skirt, v_skirt)
                    else:
                        gtw.add_data2((x0 + s * dx / sectors), (y0 + r * dy / rings))

                    point.componentwise_mult(reduced_axes)
                    if offset != 0.0:
                        point -= offset_vector
                    gvw.add_data3d(point)
                    normal.componentwise_mult(normal_coefs)
                    normal.normalize()
                    gnw.add_data3d(normal)
                    tangent.normalize()
                    gtanw.add_data3d(tangent)
                    binormal.componentwise_mult(axes)
                    binormal.normalize()
                    gbiw.add_data3d(binormal)

    # Generate main patch primitives
    for r in range(0, r_rings - 1):
        for s in range(0, r_sectors - 1):
            prim.add_vertices(r * r_sectors + s, r * r_sectors + (s + 1), (r + 1) * r_sectors + s)
            prim.add_vertices(r * r_sectors + (s + 1), (r + 1) * r_sectors + (s + 1), (r + 1) * r_sectors + s)

    # Generate skirt primitives if enabled
    if use_patch_skirts:
        make_uv_primitives_skirt(prim, rings, sectors, r_rings, r_sectors)

    prim.closePrimitive()
    geom.addPrimitive(prim)
    node.add_geom(geom)
    return path


def UVPatchBoundingPoints(
    axes: LVector3d,
    min_height: float,
    max_height: float,
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    offset: float = 0.0,
) -> list[LPoint3d]:
    """Calculate bounding points for UV patch.

    Computes a set of points that define the bounding volume of a UV patch,
    accounting for minimum and maximum terrain heights. Used for frustum
    culling and LOD calculations.

    Args:
        axes: Semi-axes of the ellipsoid (rx, ry, rz).
        min_height: Minimum terrain height (can be negative for valleys).
        max_height: Maximum terrain height (elevation above ellipsoid).
        x0: Minimum longitude coordinate of patch (0.0 to 1.0).
        y0: Minimum latitude coordinate of patch (0.0 to 1.0).
        x1: Maximum longitude coordinate of patch (0.0 to 1.0).
        y1: Maximum latitude coordinate of patch (0.0 to 1.0).
        offset: Offset distance from surface. Default is 0.0.

    Returns:
        List of 3D points defining the patch bounding volume. If min_height
        equals max_height, returns 9 points. Otherwise, returns 18 points
        (9 at min height, 9 at max height).

    Notes:
        - Samples patch at 9 locations: corners (0,0), (0.5,0), (1,0), (0,0.5),
          (0.5,0.5), (1,0.5), (0,1), (0.5,1), (1,1).
        - Heights are applied along surface normals.
        - Used to construct bounding boxes or spheres for culling.
    """
    points = []
    if min_height != max_height:
        heights = (min_height, max_height)
    else:
        heights = (min_height,)
    if offset != 0.0:
        offset_vector = UVPatchOffsetVector(axes, x0, y0, x1, y1) * offset
    for height in heights:
        for i in (0.0, 0.5, 1.0):
            for j in (0.0, 0.5, 1.0):
                point = UVPatchPoint(axes, i, j, x0, y0, x1, y1)
                if height != 0:
                    normal = UVPatchNormal(axes, i, j, x0, y0, x1, y1)
                    point += normal * height
                if offset != 0.0:
                    point -= offset_vector
                points.append(point)
    return points


def make_uv_primitives_skirt(prim, rings: int, sectors: int, r_rings: int, r_sectors: int) -> None:
    """
    Generate skirt primitives for UV patch.
    Skirt vertices are stored after main vertices in this order:
    - Left edge (r_rings vertices)
    - Right edge (r_rings vertices)
    - Bottom edge (r_sectors vertices)
    - Top edge (r_sectors vertices)

    Args:
        prim: GeomPrimitive to which skirt indices will be added.
        rings: Number of rings in the main patch.
        sectors: Number of sectors in the main patch.
        r_rings: Number of vertices per ring (sectors + 1).
        r_sectors: Number of vertices per sector (rings + 1).
    """
    base_idx = r_rings * r_sectors  # First skirt vertex index

    # Left edge (s=0): Connect to skirt
    skirt_start = base_idx
    for r in range(0, rings):
        v = r * r_sectors  # Main vertex at s=0, r
        skirt = skirt_start + r
        prim.add_vertices(v, v + r_sectors, skirt)
        prim.add_vertices(skirt, v + r_sectors, skirt + 1)

    # Right edge (s=sectors): Connect to skirt
    skirt_start = base_idx + r_rings
    for r in range(0, rings):
        v = r * r_sectors + sectors  # Main vertex at s=sectors, r
        skirt = skirt_start + r
        prim.add_vertices(skirt, v, v + r_sectors)
        prim.add_vertices(v + r_sectors, skirt + 1, skirt)

    # Bottom edge (r=0): Connect to skirt
    skirt_start = base_idx + 2 * r_rings
    for s in range(0, sectors):
        v = s  # Main vertex at r=0, s
        skirt = skirt_start + s
        prim.add_vertices(skirt, v, v + 1)
        prim.add_vertices(v + 1, skirt + 1, skirt)

    # Top edge (r=rings): Connect to skirt
    skirt_start = base_idx + 2 * r_rings + r_sectors
    for s in range(0, sectors):
        v = rings * r_sectors + s  # Main vertex at r=rings, s
        skirt = skirt_start + s
        prim.add_vertices(v, skirt, v + 1)
        prim.add_vertices(skirt, skirt + 1, v + 1)
