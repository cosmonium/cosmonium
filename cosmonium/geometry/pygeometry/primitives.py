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

"""Basic geometric primitives.

This module provides functions for creating simple 3D geometric primitives
such as bounding boxes and cubes.
"""

from panda3d.core import GeomVertexRewriter, InternalName, NodePath

from .core import empty_geom, empty_node


def BoundingBoxGeom(box) -> NodePath:
    """Create bounding box geometry from a BoundingBox object.

    Generates a triangulated mesh representation of a bounding box.
    The box is represented as 6 faces (12 triangles) using the 8
    corner points.

    Args:
        box: A Panda3D BoundingBox or similar object that provides
            a get_point(i) method for accessing the 8 corner points.

    Returns:
        NodePath containing the bounding box geometry without normals
        or texture coordinates.

    Notes:
        - The geometry has 8 vertices (one per corner).
        - Uses 12 triangles (2 per face) to form a closed box.
        - No normals or texture coordinates are generated.
        - Vertex order follows Panda3D's BoundingBox convention.
    """
    path, node = empty_node('bb')
    gvw, gcw, gtw, gnw, gtanw, gbiw, prim, geom = empty_geom('bb', 8, 12, normal=False, texture=False, tanbin=False)
    node.add_geom(geom)
    for i in range(8):
        gvw.set_data3(box.get_point(i))

    prim.add_vertices(0, 4, 5)
    prim.add_vertices(0, 5, 1)
    prim.add_vertices(4, 6, 7)
    prim.add_vertices(4, 7, 5)
    prim.add_vertices(6, 2, 3)
    prim.add_vertices(6, 3, 7)
    prim.add_vertices(2, 0, 1)
    prim.add_vertices(2, 1, 3)
    prim.add_vertices(1, 5, 7)
    prim.add_vertices(1, 7, 3)
    prim.add_vertices(2, 6, 4)
    prim.add_vertices(2, 4, 0)

    geom.add_primitive(prim)
    return path


def BoundingBoxGeomUpdate(path: NodePath, box) -> None:
    """Update existing bounding box geometry with new box dimensions.

    Modifies the vertex positions of an existing bounding box geometry
    in-place. This is more efficient than recreating the geometry when
    only the box dimensions change.

    Args:
        path: NodePath containing the bounding box geometry to update.
            Must have been created with BoundingBoxGeom().
        box: A Panda3D BoundingBox or similar object that provides
            a get_point(i) method for accessing the 8 corner points.

    Notes:
        - This is an in-place update; no new geometry is created.
    """
    geom = path.node().modify_geom(0)
    vdata = geom.modify_vertex_data()
    gvw = GeomVertexRewriter(vdata, InternalName.get_vertex())
    for i in range(8):
        gvw.set_data3(box.get_point(i))


def CubeGeom() -> NodePath:
    """Create unit cube geometry.

    Generates a cube centered at the origin with vertices at (+/-1, +/-1, +/-1).
    The cube is triangulated with 6 faces (12 triangles).

    Returns:
        NodePath containing the cube geometry without normals or
        texture coordinates.

    Notes:
        - Cube extends from (-1, -1, -1) to (1, 1, 1).
        - Uses 8 vertices (one per corner).
        - Uses 12 triangles (2 per face).
        - No normals or texture coordinates are generated.
    """
    path, node = empty_node('cube')
    gvw, gcw, gtw, gnw, gtanw, gbiw, prim, geom = empty_geom('cube', 8, 12, normal=False, texture=False, tanbin=False)
    node.add_geom(geom)
    gvw.add_data3(-1, -1, -1)
    gvw.add_data3(-1, -1, 1)
    gvw.add_data3(-1, 1, -1)
    gvw.add_data3(-1, 1, 1)
    gvw.add_data3(1, -1, -1)
    gvw.add_data3(1, -1, 1)
    gvw.add_data3(1, 1, -1)
    gvw.add_data3(1, 1, 1)

    prim.add_vertices(0, 4, 5)
    prim.add_vertices(0, 5, 1)
    prim.add_vertices(4, 6, 7)
    prim.add_vertices(4, 7, 5)
    prim.add_vertices(6, 2, 3)
    prim.add_vertices(6, 3, 7)
    prim.add_vertices(2, 0, 1)
    prim.add_vertices(2, 1, 3)
    prim.add_vertices(1, 5, 7)
    prim.add_vertices(1, 7, 3)
    prim.add_vertices(2, 6, 4)
    prim.add_vertices(2, 4, 0)

    geom.add_primitive(prim)
    return path
