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

"""Ring geometry generation for planetary rings.

Rings are generated as flat, textured annular (donut-shaped) meshes.
"""

from math import cos, pi, sin

from panda3d.core import Geom, GeomTriangles, GeomVertexData, GeomVertexFormat, GeomVertexWriter

from ...pstats import named_pstat


@named_pstat("geom")
def RingFaceGeometry(up: float, inner_radius: float, outer_radius: float, nbOfPoints: int) -> Geom:
    """Create geometry for a planetary ring face.

    Generates a flat annular (ring-shaped) mesh in the XY plane, suitable for
    rendering planetary rings. The ring is divided into radial segments and
    includes vertices, normals, colors, and texture coordinates.

    The ring is constructed as a series of quad strips, each subdivided into
    two triangles. The texture coordinates are set so that the outer edge
    maps to u=1 and the inner edge maps to u=0, with v varying around the
    ring circumference.

    Args:
        up: Direction of the ring normal. Use +1 for upward-facing (CCW winding)
            or -1 for downward-facing (CW winding). This affects triangle
            winding order and normal direction.
        inner_radius: Inner radius of the ring (size of the hole).
        outer_radius: Outer radius of the ring (size of the outer edge).
        nbOfPoints: Number of radial segments around the ring. Higher values
            produce smoother rings but increase vertex count.

    Returns:
        Geom object containing the ring geometry with vertices, normals,
        colors (white), and texture coordinates.

    Notes:
        - The ring lies in the XY plane at Z=0.
        - Vertices are generated in pairs (outer, inner) for each segment.
        - Normal vectors point in the +Z or -Z direction based on 'up'.
        - Colors are set to white (1, 1, 1, 1) for all vertices.
        - Texture U coordinate: 0=inner edge, 1=outer edge.
        - Texture V coordinate: varies from 0 to 1 around the ring.
        - Total vertices: nbOfPoints * 2
        - Total triangles: nbOfPoints * 2 (including closure)
    """
    format = GeomVertexFormat.getV3n3cpt2()
    vdata = GeomVertexData('ring', format, Geom.UHStatic)
    vdata.unclean_set_num_rows(nbOfPoints)
    vertex = GeomVertexWriter(vdata, 'vertex')
    normal = GeomVertexWriter(vdata, 'normal')
    color = GeomVertexWriter(vdata, 'color')
    texcoord = GeomVertexWriter(vdata, 'texcoord')
    for i in range(nbOfPoints):
        angle = 2 * pi / nbOfPoints * i
        x = cos(angle)
        y = sin(angle)
        vertex.add_data3(outer_radius * x, outer_radius * y, 0)
        normal.add_data3(0, 0, up)
        color.add_data4(1, 1, 1, 1)
        texcoord.add_data2(1, 0)
        vertex.add_data3(inner_radius * x, inner_radius * y, 0)
        normal.add_data3(0, 0, up)
        color.add_data4(1, 1, 1, 1)
        texcoord.add_data2(0, 0)
    triangles = GeomTriangles(Geom.UHStatic)
    triangles.reserve_num_vertices(nbOfPoints - 1)
    for i in range(nbOfPoints - 1):
        if up < 0:
            triangles.addVertex(i * 2 + 0)
            triangles.addVertex(i * 2 + 1)
            triangles.addVertex(i * 2 + 2)
            triangles.closePrimitive()
            triangles.addVertex(i * 2 + 2)
            triangles.addVertex(i * 2 + 1)
            triangles.addVertex(i * 2 + 3)
            triangles.closePrimitive()
        else:
            triangles.addVertex(i * 2 + 2)
            triangles.addVertex(i * 2 + 1)
            triangles.addVertex(i * 2 + 0)
            triangles.closePrimitive()
            triangles.addVertex(i * 2 + 3)
            triangles.addVertex(i * 2 + 1)
            triangles.addVertex(i * 2 + 2)
            triangles.closePrimitive()
    if up < 0:
        triangles.addVertex((nbOfPoints - 1) * 2 + 0)
        triangles.addVertex((nbOfPoints - 1) * 2 + 1)
        triangles.addVertex(0)
        triangles.closePrimitive()
        triangles.addVertex(0)
        triangles.addVertex((nbOfPoints - 1) * 2 + 1)
        triangles.addVertex(1)
        triangles.closePrimitive()
    else:
        triangles.addVertex(0)
        triangles.addVertex((nbOfPoints - 1) * 2 + 1)
        triangles.addVertex((nbOfPoints - 1) * 2 + 0)
        triangles.closePrimitive()
        triangles.addVertex(1)
        triangles.addVertex((nbOfPoints - 1) * 2 + 1)
        triangles.addVertex(0)
        triangles.closePrimitive()
    geom = Geom(vdata)
    geom.addPrimitive(triangles)
    return geom
