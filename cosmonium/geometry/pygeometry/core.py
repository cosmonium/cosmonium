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

"""Core geometry utility functions.

This module provides fundamental utility functions for creating and managing
Panda3D geometry primitives. These functions are used as building blocks by
higher-level geometry generators throughout the pygeometry package.
"""

from panda3d.core import (
    ColorAttrib,
    Geom,
    GeomNode,
    GeomPoints,
    GeomTriangles,
    GeomVertexArrayFormat,
    GeomVertexData,
    GeomVertexFormat,
    GeomVertexWriter,
    InternalName,
    NodePath,
)


def empty_node(name: str, color: bool = False) -> tuple[NodePath, GeomNode]:
    """Create an empty GeomNode with optional color attribute.

    Creates a new GeomNode wrapped in a NodePath, optionally configured
    to support per-vertex colors.

    Args:
        name: Name for the GeomNode.
        color: If True, enables per-vertex coloring by setting a vertex
            color attribute on the node. Default is False.

    Returns:
        A tuple containing:
            - NodePath: The NodePath wrapping the GeomNode.
            - GeomNode: The GeomNode itself.
    """
    node = GeomNode(name)
    path = NodePath(node)
    if color:
        path.setAttrib(ColorAttrib.makeVertex())
    return (path, node)


def empty_geom(
    prefix: str,
    nb_data: int,
    nb_vertices: int,
    points: bool = False,
    normal: bool = True,
    texture: bool = True,
    color: bool = False,
    tanbin: bool = False,
    jacobian: int = 0,
) -> tuple:
    """Create geometry with custom vertex format and writers.

    Creates a Geom object with a configurable vertex format and returns
    writers for populating vertex data. This is a low-level function used
    by geometry generators to efficiently create meshes.

    Args:
        prefix: Prefix for naming the geometry vertex data.
        nb_data: Number of vertex data rows to preallocate. Use 0 to
            skip preallocation.
        nb_vertices: Number of vertices to reserve in the primitive.
            Use 0 to skip reservation.
        points: If True, creates GeomPoints primitive. If False, creates
            GeomTriangles. Default is False.
        normal: If True, includes normal vectors in vertex format.
            Default is True.
        texture: If True, includes texture coordinates in vertex format.
            Default is True.
        color: If True, includes per-vertex colors in vertex format.
            Default is False.
        tanbin: If True, includes tangent and binormal vectors for
            normal mapping. Default is False.
        jacobian: Number of additional float parameters to store per vertex
            for custom data (e.g., Jacobian matrix components). Use 0 for
            none. Default is 0.

    Returns:
        A tuple containing vertex writers and geometry objects:
            - GeomVertexWriter: Vertex position writer.
            - GeomVertexWriter or None: Color writer (if color=True).
            - GeomVertexWriter or None: Texture coordinate writer (if texture=True).
            - GeomVertexWriter or None: Normal writer (if normal=True).
            - GeomVertexWriter or None: Tangent writer (if tanbin=True).
            - GeomVertexWriter or None: Binormal writer (if tanbin=True).
            - GeomPrimitive: The primitive (GeomPoints or GeomTriangles).
            - Geom: The geometry object.
            - GeomVertexWriter: Jacobian parameter writer (only if jacobian > 0).
    """
    array = GeomVertexArrayFormat()
    array.add_column(InternalName.get_vertex(), 3, Geom.NTFloat32, Geom.CPoint)
    if color:
        array.add_column(InternalName.get_color(), 4, Geom.NTFloat32, Geom.CColor)
    if texture:
        array.add_column(InternalName.get_texcoord(), 2, Geom.NTFloat32, Geom.CTexcoord)
    if normal:
        array.add_column(InternalName.get_normal(), 3, Geom.NTFloat32, Geom.CVector)
    if tanbin:
        array.add_column(InternalName.get_tangent(), 3, Geom.NTFloat32, Geom.CVector)
        array.add_column(InternalName.get_binormal(), 3, Geom.NTFloat32, Geom.CVector)
    if jacobian > 0:
        array.add_column(InternalName.make("jacobian_params"), jacobian, Geom.NTFloat32, Geom.COther)
    format = GeomVertexFormat()
    format.addArray(array)
    format = GeomVertexFormat.registerFormat(format)
    gvd = GeomVertexData('gvd', format, Geom.UHStatic)
    if nb_data != 0:
        gvd.unclean_set_num_rows(nb_data)
    geom = Geom(gvd)
    gvw = GeomVertexWriter(gvd, InternalName.get_vertex())
    if color:
        gcw = GeomVertexWriter(gvd, InternalName.get_color())
    else:
        gcw = None
    if texture:
        gtw = GeomVertexWriter(gvd, InternalName.get_texcoord())
    else:
        gtw = None
    if normal:
        gnw = GeomVertexWriter(gvd, InternalName.get_normal())
    else:
        gnw = None
    if tanbin:
        gtanw = GeomVertexWriter(gvd, InternalName.get_tangent())
        gbiw = GeomVertexWriter(gvd, InternalName.get_binormal())
    else:
        gtanw = None
        gbiw = None
    if jacobian > 0:
        gextra = GeomVertexWriter(gvd, InternalName.make("jacobian_params"))
    if points:
        prim = GeomPoints(Geom.UHStatic)
    else:
        prim = GeomTriangles(Geom.UHStatic)
    if nb_vertices != 0:
        prim.reserve_num_vertices(nb_vertices)
    if jacobian == 0:
        return (gvw, gcw, gtw, gnw, gtanw, gbiw, prim, geom)
    else:
        return (gvw, gcw, gtw, gnw, gtanw, gbiw, prim, geom, gextra)
