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

"""Tessellation configuration and primitive generation.

This module provides utilities for configuring tessellation levels and generating
triangle primitives for square patches with optional adaptive subdivision. It supports
creating uniform grids as well as adaptive tessellation that varies along patch edges
to match neighboring patches of different resolutions.
"""

from typing import Optional


class TessellationInfo:
    """Store tessellation configuration for adaptive patch subdivision.

    This class encapsulates the tessellation parameters needed for creating
    adaptive square patches that can match different tessellation levels along
    their edges to seamlessly connect with neighboring patches.

    Attributes:
        inner: Number of subdivisions along each inner edge of the patch.
        outer: List of subdivisions for the four outer edges [right, front, left, back].
        ratio: Subdivision ratio between inner and each outer edge for adaptation.
    """

    def __init__(self, inner: int, outer: list[int]):
        """Initialize tessellation configuration.

        Args:
            inner: Number of subdivisions for the inner patch (along both axes).
            outer: List of 4 integers specifying subdivisions for outer edges
                in order: [right, front, left, back]. Each value determines
                how the patch edge should subdivide to match neighbors.
        """
        self.inner = inner
        self.outer = outer
        self.ratio = [inner // x if inner >= x else 1 for x in outer]


def make_config(inner: int, outer: Optional[list[int]]) -> tuple[int, int, list[int], list[int]]:
    """Create tessellation configuration parameters.

    Generates the configuration needed for tessellation, including the number
    of vertices and adaptation ratios between inner and outer edge subdivisions.

    Args:
        inner: Number of subdivisions along each inner edge.
        outer: Optional list of 4 integers for outer edge subdivisions
            [right, front, left, back]. If None, all edges use inner value.

    Returns:
        A tuple containing:
            - nb_vertices: Number of vertices along each axis (inner + 1)
            - inner: Number of inner subdivisions (unchanged)
            - outer: List of outer subdivisions (created if None)
            - ratio: List of adaptation ratios for each outer edge
    """
    nb_vertices = inner + 1
    if outer is None:
        outer = [inner, inner, inner, inner]
    ratio = [inner // x if inner >= x else 1 for x in outer]
    return (nb_vertices, inner, outer, ratio)


def make_square_primitives(prim, inner: int, nb_vertices: int) -> None:
    """Generate uniform triangles for a square grid.

    Creates a uniform grid of triangles by subdividing a square patch into
    inner*inner quads, each split into two triangles. This is used when
    no adaptive tessellation is needed.

    Args:
        prim: GeomTriangles primitive to add vertices to.
        inner: Number of subdivisions along each edge.
        nb_vertices: Number of vertices along each axis (inner + 1).

    Notes:
        - Generates 2 triangles per quad (inner * inner * 2 triangles total).
        - Vertices are indexed in row-major order.
        - Each quad is split diagonally from lower-left to upper-right.
    """
    for x in range(0, inner):
        for y in range(0, inner):
            v = nb_vertices * x + y
            prim.add_vertices(v, v + nb_vertices, v + 1)
            prim.add_vertices(v + 1, v + nb_vertices, v + nb_vertices + 1)


def make_adapted_square_primitives(prim, inner: int, nb_vertices: int, ratio: list[int]) -> None:
    """Generate adaptive triangles for a square grid with edge subdivision.

    Creates triangles for a square patch with adaptive tessellation along the
    edges. The patch adapts its edge triangulation to match neighboring patches
    with different tessellation levels, preventing cracks and T-junctions.

    The adaptation occurs along the four edges (right=0, front=1, left=2, back=3),
    where vertices may be merged based on the ratio between inner and outer
    tessellation levels.

    Args:
        prim: GeomTriangles primitive to add vertices to.
        inner: Number of subdivisions along each inner edge.
        nb_vertices: Number of vertices along each axis (inner + 1).
        ratio: List of 4 integers specifying subdivision ratios for each edge
            [right, front, left, back]. A ratio of 2 means the edge subdivides
            half as many times as the interior.

    Notes:
        - Edge vertices are selectively merged based on ratio values.
        - Corner vertices require special handling to maintain consistency.
        - Interior triangles (not touching edges) use standard subdivision.
        - Ensures crack-free transitions between LOD levels.
    """
    #                   0 1 2
    #                  =================
    # 0                ||/|/|/|
    # nb_vertices      ||/|/|
    # nb_vertices * 2  ||/|
    #
    for x in range(0, inner):
        for y in range(0, inner):
            v = nb_vertices * x + y
            if x == 0:
                # Right of Ralph
                i = 0
                if y == 0:
                    # ====
                    # ||/|
                    j = 1
                    if ratio[i] == 1 and ratio[j] == 1:
                        prim.add_vertices(v, v + nb_vertices, v + 1)
                        prim.add_vertices(v + 1, v + nb_vertices, v + nb_vertices + 1)
                    else:
                        prim.add_vertices(v, v + nb_vertices * ratio[j], v + nb_vertices + 1)
                        prim.add_vertices(v, v + nb_vertices + 1, v + ratio[i])
                elif y == inner - 1:
                    #
                    #  ||/|
                    #  ====
                    j = 3
                    if ratio[i] == 1:
                        prim.add_vertices(v, v + nb_vertices, v + 1)
                    prim.add_vertices(v + 1, v + nb_vertices * ratio[j], v + nb_vertices * ratio[j] + 1)
                else:
                    vp = nb_vertices * x + (y // ratio[i]) * ratio[i]
                    if (y % ratio[i]) == 0:
                        prim.add_vertices(v, v + nb_vertices, v + ratio[i])
                    prim.add_vertices(vp + ratio[i], v + nb_vertices, v + nb_vertices + 1)
            elif x == inner - 1:
                # Left of Ralph
                i = 2
                if y == 0:
                    # ====
                    # |/||
                    j = 1
                    if ratio[j] == 1:
                        prim.add_vertices(v, v + nb_vertices, v + 1)
                    prim.add_vertices(v + ratio[i], v + nb_vertices, v + nb_vertices + ratio[i])
                elif y == inner - 1:
                    j = 3
                    if ratio[i] == 1 and ratio[j] == 1:
                        prim.add_vertices(v, v + nb_vertices, v + 1)
                        prim.add_vertices(v + 1, v + nb_vertices, v + nb_vertices + 1)
                    else:
                        vpx = nb_vertices * (x // ratio[j]) * ratio[j] + y
                        prim.add_vertices(vpx + 1, v, v + nb_vertices + 1)
                        vpy = nb_vertices * x + ((y // ratio[i]) * ratio[i])
                        prim.add_vertices(v, vpy + nb_vertices, v + nb_vertices + 1)
                else:
                    vp = nb_vertices * x + ((y // ratio[i]) * ratio[i])
                    prim.add_vertices(v, vp + nb_vertices, v + 1)
                    if ((y + 1) % ratio[i]) == 0:
                        prim.add_vertices(v + 1, vp + nb_vertices, v + nb_vertices + 1)
            elif y == 0:
                # Front of Ralph
                i = 1
                vp = nb_vertices * (x // ratio[i]) * ratio[i] + y
                prim.add_vertices(v + 1, vp + nb_vertices * ratio[i], v + nb_vertices + 1)
                if (x % ratio[i]) == 0:
                    prim.add_vertices(v, v + nb_vertices * ratio[i], v + 1)
            elif y == inner - 1:
                # Back of Ralph
                i = 3
                vp = nb_vertices * (x // ratio[i]) * ratio[i] + y
                prim.add_vertices(v, v + nb_vertices, vp + 1)
                if ((x + 1) % ratio[i]) == 0:
                    prim.add_vertices(vp + 1, v + nb_vertices, v + nb_vertices + 1)
            else:
                prim.add_vertices(v, v + nb_vertices, v + 1)
                prim.add_vertices(v + 1, v + nb_vertices, v + nb_vertices + 1)


def make_adapted_square_primitives_skirt(prim, inner: int, nb_vertices: int, ratio: list[int]) -> None:
    """Generate adaptive triangles for patch edge skirts.

    Creates triangles connecting the patch edges to surrounding skirt vertices.
    Skirts extend beyond the patch boundaries to prevent gaps between patches
    due to floating-point precision or LOD transitions. The skirt triangulation
    adapts to match the edge subdivision ratios.

    Skirt vertices are stored after the main patch vertices in the order:
    [right_skirt, left_skirt, front_skirt, back_skirt], with nb_vertices
    vertices per skirt edge.

    Args:
        prim: GeomTriangles primitive to add vertices to.
        inner: Number of subdivisions along each inner edge.
        nb_vertices: Number of vertices along each axis (inner + 1).
        ratio: List of 4 integers specifying subdivision ratios for each edge
            [right, front, left, back].

    Notes:
        - Skirt vertices start at index (nb_vertices * nb_vertices).
        - Adapts triangulation based on ratio to maintain consistency.
        - Each edge generates two triangles per subdivision.
    """
    for a in range(0, 4):
        start = nb_vertices * nb_vertices + a * nb_vertices
        for b in range(0, inner):
            skirt = start + b
            if a == 0:
                i = 0
                x = 0
                y = b
            elif a == 1:
                i = 2
                x = inner - 1
                y = b
            elif a == 2:
                i = 1
                x = b
                y = 0
            elif a == 3:
                i = 3
                x = b
                y = inner - 1
            v = nb_vertices * x + y
            if a == 0:
                if (y % ratio[i]) == 0:
                    prim.add_vertices(v, v + ratio[i], skirt)
                    prim.add_vertices(skirt, v + ratio[i], skirt + ratio[i])
            elif a == 1:
                if (y % ratio[i]) == 0:
                    prim.add_vertices(v + nb_vertices, skirt, v + nb_vertices + ratio[i])
                    prim.add_vertices(v + nb_vertices + ratio[i], skirt, skirt + ratio[i])
            elif a == 2:
                if (x % ratio[i]) == 0:
                    prim.add_vertices(v, skirt, v + nb_vertices * ratio[i])
                    prim.add_vertices(v + nb_vertices * ratio[i], skirt, skirt + ratio[i])
            elif a == 3:
                if (x % ratio[i]) == 0:
                    prim.add_vertices(skirt + ratio[i], v + 1, v + nb_vertices * ratio[i] + 1)
                    prim.add_vertices(skirt, v + 1, skirt + ratio[i])


def make_adapted_uv_primitives(prim, rings: int, sectors: int, r_rings: int, r_sectors: int, ratio: list[int]) -> None:
    """Generate adaptive triangles for a UV patch grid with edge subdivision.

    Creates triangles for a UV (latitude/longitude) spherical patch with
    adaptive tessellation along the edges. The patch adapts its edge
    triangulation to match neighbouring patches with different tessellation
    levels, preventing cracks and T-junctions.

    The adaptation occurs along the four edges, where vertices may be merged
    based on the ratio between inner and outer tessellation levels.

    Args:
        prim: GeomTriangles primitive to add vertices to.
        rings: Number of subdivisions in latitude direction.
        sectors: Number of subdivisions in longitude direction.
        r_rings: Number of vertices along the rings axis (rings + 1).
        r_sectors: Number of vertices along the sectors axis (sectors + 1).
        ratio: List of 4 integers specifying subdivision ratios for each edge
            [left, bottom, right, top].

    Notes:
        - Uses UV winding convention: (v, v+1, v+r_sectors) for interior cells.
        - Corner vertices require special handling to maintain consistency.
    """
    for r in range(0, rings):
        for s in range(0, sectors):
            v = r_sectors * r + s
            if r == 0:
                # Bottom edge
                i = 1  # bottom ratio, merges s
                if s == 0:
                    # Bottom-left corner
                    j = 0  # left ratio, merges r
                    if ratio[i] == 1 and ratio[j] == 1:
                        prim.add_vertices(v, v + 1, v + r_sectors)
                        prim.add_vertices(v + 1, v + r_sectors + 1, v + r_sectors)
                    else:
                        prim.add_vertices(v, v + r_sectors + 1, v + r_sectors * ratio[j])
                        prim.add_vertices(v, v + ratio[i], v + r_sectors + 1)
                elif s == sectors - 1:
                    # Bottom-right corner
                    j = 2  # right ratio, merges r
                    if ratio[i] == 1:
                        prim.add_vertices(v, v + 1, v + r_sectors)
                    prim.add_vertices(v + 1, v + r_sectors * ratio[j] + 1, v + r_sectors * ratio[j])
                else:
                    # Bottom edge, not corner
                    vp = r * r_sectors + (s // ratio[i]) * ratio[i]
                    if (s % ratio[i]) == 0:
                        prim.add_vertices(v, v + ratio[i], v + r_sectors)
                    prim.add_vertices(vp + ratio[i], v + r_sectors + 1, v + r_sectors)
            elif r == rings - 1:
                # Top edge
                i = 3  # top ratio, merges s
                if s == 0:
                    # Top-left corner
                    j = 0  # left ratio, merges r
                    if ratio[j] == 1:
                        prim.add_vertices(v, v + 1, v + r_sectors)
                    prim.add_vertices(v + ratio[i], v + r_sectors + ratio[i], v + r_sectors)
                elif s == sectors - 1:
                    # Top-right corner
                    j = 2  # right ratio, merges r
                    if ratio[i] == 1 and ratio[j] == 1:
                        prim.add_vertices(v, v + 1, v + r_sectors)
                        prim.add_vertices(v + 1, v + r_sectors + 1, v + r_sectors)
                    else:
                        vpx = r_sectors * (r // ratio[j]) * ratio[j] + s
                        prim.add_vertices(vpx + 1, v + r_sectors + 1, v)
                        vpy = r * r_sectors + ((s // ratio[i]) * ratio[i])
                        prim.add_vertices(v, v + r_sectors + 1, vpy + r_sectors)
                else:
                    # Top edge, not corner
                    vp = r * r_sectors + ((s // ratio[i]) * ratio[i])
                    prim.add_vertices(v, v + 1, vp + r_sectors)
                    if ((s + 1) % ratio[i]) == 0:
                        prim.add_vertices(v + 1, v + r_sectors + 1, vp + r_sectors)
            elif s == 0:
                # Left edge
                i = 0  # left ratio, merges r
                vp = r_sectors * (r // ratio[i]) * ratio[i] + s
                prim.add_vertices(v + 1, v + r_sectors + 1, vp + r_sectors * ratio[i])
                if (r % ratio[i]) == 0:
                    prim.add_vertices(v, v + 1, vp + r_sectors * ratio[i])
            elif s == sectors - 1:
                # Right edge
                i = 2  # right ratio, merges r
                vp = r_sectors * (r // ratio[i]) * ratio[i] + s
                prim.add_vertices(v, vp + 1, v + r_sectors)
                if ((r + 1) % ratio[i]) == 0:
                    prim.add_vertices(vp + 1, v + r_sectors + 1, v + r_sectors)
            else:
                prim.add_vertices(v, v + 1, v + r_sectors)
                prim.add_vertices(v + 1, v + r_sectors + 1, v + r_sectors)


def make_adapted_uv_primitives_skirt(
    prim, rings: int, sectors: int, r_rings: int, r_sectors: int, ratio: list[int]
) -> None:
    """Generate adaptive triangles for UV patch edge skirts.

    Creates triangles connecting the UV patch edges to surrounding skirt
    vertices. Skirts extend beyond the patch boundaries to prevent gaps
    between patches due to floating-point precision or LOD transitions. The
    skirt triangulation adapts to match the edge subdivision ratios.

    Skirt vertices are stored after the main patch vertices in the order:
    [left_skirt(r_rings), right_skirt(r_rings), bottom_skirt(r_sectors),
    top_skirt(r_sectors)].

    Args:
        prim: GeomTriangles primitive to add vertices to.
        rings: Number of subdivisions in latitude direction.
        sectors: Number of subdivisions in longitude direction.
        r_rings: Number of vertices along the rings axis (rings + 1).
        r_sectors: Number of vertices along the sectors axis (sectors + 1).
        ratio: List of 4 integers specifying subdivision ratios for each edge
            [left, bottom, right, top].

    Notes:
        - Skirt vertices start at index (r_rings * r_sectors).
        - Adapts triangulation based on ratio to maintain consistency.
        - Only generates triangles at ratio-boundary positions for adapted edges.
    """
    base_idx = r_rings * r_sectors

    # Left edge (s=0), varies along r
    skirt_start = base_idx
    for r in range(0, rings):
        v = r * r_sectors
        skirt = skirt_start + r
        if (r % ratio[0]) == 0:
            prim.add_vertices(v, v + r_sectors * ratio[0], skirt)
            prim.add_vertices(skirt, v + r_sectors * ratio[0], skirt + ratio[0])

    # Right edge (s=sectors), varies along r
    skirt_start = base_idx + r_rings
    for r in range(0, rings):
        v = r * r_sectors + sectors
        skirt = skirt_start + r
        if (r % ratio[2]) == 0:
            prim.add_vertices(skirt, v, v + r_sectors * ratio[2])
            prim.add_vertices(v + r_sectors * ratio[2], skirt + ratio[2], skirt)

    # Bottom edge (r=0), varies along s
    skirt_start = base_idx + 2 * r_rings
    for s in range(0, sectors):
        v = s
        skirt = skirt_start + s
        if (s % ratio[1]) == 0:
            prim.add_vertices(skirt, v, v + ratio[1])
            prim.add_vertices(v + ratio[1], skirt + ratio[1], skirt)

    # Top edge (r=rings), varies along s
    skirt_start = base_idx + 2 * r_rings + r_sectors
    for s in range(0, sectors):
        v = rings * r_sectors + s
        skirt = skirt_start + s
        if (s % ratio[3]) == 0:
            prim.add_vertices(v, skirt, v + ratio[3])
            prim.add_vertices(skirt, skirt + ratio[3], v + ratio[3])


def make_primitives_skirt(prim, inner: int, nb_vertices: int) -> None:
    """Generate uniform triangles for patch edge skirts.

    Creates triangles connecting the patch edges to surrounding skirt vertices
    using uniform subdivision (no adaptation). Skirts prevent visual gaps between
    patches by extending slightly beyond the patch boundaries.

    Skirt vertices are stored after the main patch vertices in the order:
    [right_skirt, left_skirt, front_skirt, back_skirt], with nb_vertices
    vertices per skirt edge.

    Args:
        prim: GeomTriangles primitive to add vertices to.
        inner: Number of subdivisions along each inner edge.
        nb_vertices: Number of vertices along each axis (inner + 1).

    Notes:
        - Skirt vertices start at index (nb_vertices * nb_vertices).
        - Each edge segment generates two triangles.
        - Used when uniform tessellation is applied (no adaptation needed).
    """
    for a in range(0, 4):
        start = nb_vertices * nb_vertices + a * nb_vertices
        for b in range(0, inner):
            skirt = start + b
            if a == 0:
                x = 0
                y = b
            elif a == 1:
                x = inner - 1
                y = b
            elif a == 2:
                x = b
                y = 0
            elif a == 3:
                x = b
                y = inner - 1
            v = nb_vertices * x + y
            if a == 0:
                prim.add_vertices(v, v + 1, skirt)
                prim.add_vertices(skirt, v + 1, skirt + 1)
            elif a == 1:
                prim.add_vertices(v + nb_vertices, skirt, v + nb_vertices + 1)
                prim.add_vertices(v + nb_vertices + 1, skirt, skirt + 1)
            elif a == 2:
                prim.add_vertices(v, skirt, v + nb_vertices)
                prim.add_vertices(v + nb_vertices, skirt, skirt + 1)
            elif a == 3:
                prim.add_vertices(skirt + 1, v + 1, v + nb_vertices + 1)
                prim.add_vertices(skirt, v + 1, skirt + 1)
