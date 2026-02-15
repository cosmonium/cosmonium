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

"""Tile and patch geometry generation.

This module provides functions for creating flat tiles and tessellation patches
used for terrain rendering and texture mapping. It supports adaptive tessellation,
UV coordinate transformation, and optional skirts for seamless patch connections.
"""

from typing import Optional

from panda3d.core import (
    Geom,
    GeomPatches,
    GeomVertexData,
    GeomVertexFormat,
    GeomVertexWriter,
    LPoint3d,
    NodePath,
)

from ...pstats import named_pstat
from .core import convert_xy, empty_geom, empty_node
from .tessellation import (
    TessellationInfo,
    make_adapted_square_primitives,
    make_adapted_square_primitives_skirt,
    make_primitives_skirt,
    make_square_primitives,
)


@named_pstat("geom")
def Tile(
    size: float,
    tessellation: TessellationInfo,
    inv_u: bool = False,
    inv_v: bool = False,
    swap_uv: bool = False,
    use_patch_adaptation: bool = True,
    use_patch_skirts: bool = True,
    skirt_size: float = 0.1,
    skirt_uv: float = 0.1,
) -> NodePath:
    """Create a flat rectangular tile with optional adaptive tessellation and skirts.

    Generates a tessellated rectangular tile in the XY plane at Z=0, with optional
    skirts extending beyond the edges. The tile can use adaptive tessellation to
    match different LOD levels along its edges, and UV coordinates can be transformed
    as needed.

    Args:
        size: Width and height of the square tile.
        tessellation: TessellationInfo object specifying inner and outer subdivision levels.
        inv_u: If True, invert U texture coordinates (1.0 - u).
        inv_v: If True, invert V texture coordinates (1.0 - v).
        swap_uv: If True, swap U and V texture coordinates.
        use_patch_adaptation: If True, use adaptive tessellation along edges.
        use_patch_skirts: If True, add skirts around tile edges to prevent gaps.
        skirt_size: Vertical offset for skirt vertices (negative Z displacement).
        skirt_uv: UV coordinate extension for skirt vertices beyond [0,1].

    Returns:
        NodePath containing the tile geometry with vertices, normals, tangents,
        binormals, and texture coordinates.

    Notes:
        - Tile vertices are positioned in the range [0, size] in X and Y.
        - Normal vectors point in the +Z direction (0, 0, 1).
        - Tangent vectors point in the +X direction (1, 0, 0).
        - Binormal vectors point in the +Y direction (0, 1, 0).
        - Skirts extend downward in -Z direction by skirt_size * size.
    """
    inner = tessellation.inner
    nb_vertices = inner + 1
    (path, node) = empty_node('uv')
    nb_points = nb_vertices * nb_vertices
    nb_primitives = inner * inner
    if use_patch_skirts:
        nb_points += nb_vertices * 4
        nb_primitives += inner * 4
    (gvw, gcw, gtw, gnw, gtanw, gbiw, prim, geom) = empty_geom('cube', nb_points, nb_primitives, tanbin=True)
    node.add_geom(geom)

    for i in range(0, nb_vertices):
        for j in range(0, nb_vertices):
            u = float(i) / inner
            v = float(j) / inner

            x = u
            y = v

            if inv_u:
                u = 1.0 - u
            if inv_v:
                v = 1.0 - v
            if swap_uv:
                gtw.add_data2(v, u)
            else:
                gtw.add_data2(u, v)
            gvw.add_data3(x * size, y * size, 0)
            gnw.add_data3(0, 0, 1.0)
            gtanw.add_data3(1, 0, 0)
            gbiw.add_data3(0, 1, 0)

    if use_patch_skirts:
        for a in range(0, 4):
            for b in range(0, nb_vertices):
                if a == 0:
                    x = 0.0
                    y = b / inner
                    u = -skirt_uv
                    v = y
                elif a == 1:
                    x = 1.0
                    y = b / inner
                    u = 1.0 + skirt_uv
                    v = y
                elif a == 2:
                    x = b / inner
                    y = 0.0
                    u = x
                    v = -skirt_uv
                elif a == 3:
                    x = b / inner
                    y = 1.0
                    u = x
                    v = 1.0 + skirt_uv

                if inv_u:
                    u = 1.0 - u
                if inv_v:
                    v = 1.0 - v
                if swap_uv:
                    gtw.add_data2(v, u)
                else:
                    gtw.add_data2(u, v)
                gvw.add_data3(x * size, y * size, -skirt_size * size)
                gnw.add_data3(0, 0, 1.0)
                gtanw.add_data3(1, 0, 0)
                gbiw.add_data3(0, 1, 0)

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


def TileBoundingPoints(size: float = 1.0, height: float = 1.0) -> list[LPoint3d]:
    """Calculate bounding points for a tile.

    Returns the minimum and maximum corner points of the bounding box
    that encompasses a tile with the given size and height variation.

    Args:
        size: Width and height of the square tile.
        height: Maximum height variation above/below the tile plane.

    Returns:
        List containing two LPoint3d objects:
            - First point: minimum corner at (0, 0, -height)
            - Second point: maximum corner at (size, size, height)
    """
    return [LPoint3d(0, 0, -height), LPoint3d(size, size, height)]


def Patch(size: float = 1.0) -> NodePath:
    """Create a simple quad patch for tessellation shaders.

    Generates a single quad patch primitive suitable for use with tessellation
    shaders. The patch consists of 4 control points forming a square in the
    XY plane at Z=0.

    Args:
        size: Width and height of the square patch.

    Returns:
        NodePath containing a GeomPatches primitive with 4 control points.

    Notes:
        - The patch has 4 vertices arranged as a quad.
        - Vertices are ordered: (0,0), (size,0), (size,size), (0,size).
        - This is intended for hardware tessellation, not direct rendering.
        - No normals or texture coordinates are included.
    """
    (path, node) = empty_node('patch')
    form = GeomVertexFormat.getV3()
    vdata = GeomVertexData("vertices", form, Geom.UHStatic)

    vertexWriter = GeomVertexWriter(vdata, "vertex")
    vertexWriter.add_data3(0, 0, 0)
    vertexWriter.add_data3(size, 0, 0)
    vertexWriter.add_data3(size, size, 0)
    vertexWriter.add_data3(0, size, 0)
    patches = GeomPatches(4, Geom.UHStatic)

    patches.addConsecutiveVertices(0, 4)  # South, west, north, east
    patches.closePrimitive()

    gm = Geom(vdata)
    gm.addPrimitive(patches)

    node.addGeom(gm)
    return path


def PatchBoundingPoints(
    x: float = 0.0,
    y: float = 0.0,
    size: float = 1.0,
    scale: float = 1.0,
    min_height: float = -1.0,
    max_height: float = 1.0,
) -> list[LPoint3d]:
    """Calculate bounding points for a patch with height variation.

    Returns the minimum and maximum corner points of the bounding box
    that encompasses a patch at a given position with specified size
    and height range.

    Args:
        x: X coordinate of the patch origin.
        y: Y coordinate of the patch origin.
        size: Width and height of the square patch.
        scale: Scaling factor applied to X and Y coordinates.
        min_height: Minimum Z coordinate (bottom of bounding box).
        max_height: Maximum Z coordinate (top of bounding box).

    Returns:
        List containing two LPoint3d objects:
            - First point: minimum corner at (x*scale, y*scale, min_height)
            - Second point: maximum corner at ((x+size)*scale, (y+size)*scale, max_height)
    """
    return [LPoint3d(x * scale, y * scale, min_height), LPoint3d((x + size) * scale, (y + size) * scale, max_height)]


def QuadPatch(
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    x_inverted: bool = False,
    y_inverted: bool = False,
    xy_swap: bool = False,
    offset: Optional[float] = None,
) -> NodePath:
    """Create a quad patch for tessellation with transformed coordinates.

    Generates a single quad patch primitive with transformed coordinates
    suitable for creating cube face patches. The coordinates are mapped
    from [0,1] range to [-1,1] range and can be inverted or swapped.

    Args:
        x0: Starting X coordinate in [0,1] range.
        y0: Starting Y coordinate in [0,1] range.
        x1: Ending X coordinate in [0,1] range.
        y1: Ending Y coordinate in [0,1] range.
        x_inverted: If True, invert X coordinates before mapping.
        y_inverted: If True, invert Y coordinates before mapping.
        xy_swap: If True, swap X and Y coordinates before mapping.
        offset: Z offset for the patch. If None, defaults to 1.0.

    Returns:
        NodePath containing a GeomPatches primitive with 4 control points.

    Notes:
        - Input coordinates are in [0,1] range and mapped to [-1,1].
        - Vertices are ordered for tessellation: (x0,y0), (x1,y0), (x1,y1), (x0,y1).
        - Used primarily for cube face patch generation.
    """

    (x0, y0, x1, y1, dx, dy) = convert_xy(x0, y0, x1, y1, x_inverted, y_inverted, xy_swap)

    if offset is None:
        offset = 1.0

    (path, node) = empty_node('patch')
    form = GeomVertexFormat.getV3()
    vdata = GeomVertexData("vertices", form, Geom.UHStatic)

    vertexWriter = GeomVertexWriter(vdata, "vertex")
    x0 = 2.0 * x0 - 1.0
    x1 = 2.0 * x1 - 1.0
    y0 = 2.0 * y0 - 1.0
    y1 = 2.0 * y1 - 1.0
    vertexWriter.add_data3(x0, y0, offset)
    vertexWriter.add_data3(x1, y0, offset)
    vertexWriter.add_data3(x1, y1, offset)
    vertexWriter.add_data3(x0, y1, offset)
    patches = GeomPatches(4, Geom.UHStatic)

    patches.addConsecutiveVertices(0, 4)  # South, west, north, east
    patches.closePrimitive()

    gm = Geom(vdata)
    gm.addPrimitive(patches)

    node.addGeom(gm)
    return path
