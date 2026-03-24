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

"""Marker geometry building functions.

This module provides functions for constructing marker geometries in various
shapes that can be rendered in the annotation pass.
"""

from math import cos, pi, sin

from panda3d.core import Geom, GeomLines, GeomNode, GeomTriangles, GeomVertexData, GeomVertexFormat, GeomVertexWriter

from ..components.annotations.marker_shape import MarkerShape


def _write_points(vwriter, points):
    """Write a list of (x, y, z) tuples to vertex data and return the base index.

    Args:
        vwriter: Vertex writer object.
        points: List of (x, y, z) tuples.

    Returns:
        The base index of the first written vertex.
    """
    base = vwriter.getWriteRow()
    for p in points:
        vwriter.addData3f(*p)
    return base


def _add_loop(vwriter, prim, points):
    """Add a closed loop of line segments.

    Args:
        vwriter: Vertex writer object.
        prim: Geometry primitive object.
        points: List of (x, y, z) tuples defining the loop.
    """
    base = _write_points(vwriter, points)
    n = len(points)
    for i in range(n):
        prim.addVertex(base + i)
        prim.addVertex(base + (i + 1) % n)
    prim.closePrimitive()


def _add_segments(vwriter, prim, segments):
    """Add a list of disjoint line segments, each given as (start, end) point tuples.

    Args:
        vwriter: Vertex writer object.
        prim: Geometry primitive object.
        segments: List of ((start_x, start_y, start_z), (end_x, end_y, end_z)) tuples.
    """
    for a, b in segments:
        base = _write_points(vwriter, [a, b])
        prim.addVertex(base)
        prim.addVertex(base + 1)
        prim.closePrimitive()


def _add_fan(vwriter, prim, center, rim_points):
    """Add a filled triangle fan from center to a closed rim.

    Args:
        vwriter: Vertex writer object.
        prim: Geometry primitive object.
        center: Center point as (x, y, z) tuple.
        rim_points: List of (x, y, z) tuples defining the rim.
    """
    base = _write_points(vwriter, [center] + list(rim_points))
    n = len(rim_points)
    for i in range(n):
        prim.addVertex(base)
        prim.addVertex(base + 1 + i)
        prim.addVertex(base + 1 + (i + 1) % n)
    prim.closePrimitive()


def build_marker_geom(name, shape):
    """Return a GeomNode containing the marker shape at unit scale in the XZ plane.

    The geometry occupies the XZ plane (Y=0). X is horizontal right, Z is vertical up.
    The caller should scale the NodePath to achieve the desired screen-space size.

    Args:
        name: Name of the geometry node.
        shape: One of the MarkerShape enum values.

    Returns:
        A GeomNode containing the marker geometry.
    """
    fmt = GeomVertexFormat.getV3()
    vdata = GeomVertexData(name + '-vdata', fmt, Geom.UHStatic)
    vwriter = GeomVertexWriter(vdata, 'vertex')

    filled = shape in (MarkerShape.DISK, MarkerShape.FILLEDSQUARE)
    if filled:
        prim = GeomTriangles(Geom.UHStatic)
    else:
        prim = GeomLines(Geom.UHStatic)

    if shape == MarkerShape.DIAMOND:
        _add_loop(vwriter, prim, [(0, 0, 1), (1, 0, 0), (0, 0, -1), (-1, 0, 0)])

    elif shape == MarkerShape.PLUS:
        _add_segments(
            vwriter,
            prim,
            [
                ((-1, 0, 0), (1, 0, 0)),
                ((0, 0, -1), (0, 0, 1)),
            ],
        )

    elif shape == MarkerShape.SQUARE:
        _add_loop(vwriter, prim, [(-1, 0, -1), (1, 0, -1), (1, 0, 1), (-1, 0, 1)])

    elif shape == MarkerShape.TRIANGLE:
        _add_loop(vwriter, prim, [(0, 0, 1), (-1, 0, -1), (1, 0, -1)])

    elif shape == MarkerShape.X:
        _add_segments(
            vwriter,
            prim,
            [
                ((-1, 0, -1), (1, 0, 1)),
                ((-1, 0, 1), (1, 0, -1)),
            ],
        )

    elif shape == MarkerShape.FILLEDSQUARE:
        _add_fan(vwriter, prim, (0, 0, 0), [(-1, 0, -1), (1, 0, -1), (1, 0, 1), (-1, 0, 1)])

    elif shape == MarkerShape.LEFTARROW:
        _add_segments(
            vwriter,
            prim,
            [
                ((-1, 0, 0), (0, 0, 0)),
                ((-1, 0, 0), (-0.5, 0, 0.5)),
                ((-1, 0, 0), (-0.5, 0, -0.5)),
            ],
        )

    elif shape == MarkerShape.RIGHTARROW:
        _add_segments(
            vwriter,
            prim,
            [
                ((1, 0, 0), (0, 0, 0)),
                ((1, 0, 0), (0.5, 0, 0.5)),
                ((1, 0, 0), (0.5, 0, -0.5)),
            ],
        )

    elif shape == MarkerShape.UPARROW:
        _add_segments(
            vwriter,
            prim,
            [
                ((0, 0, 1), (0, 0, 0)),
                ((0, 0, 1), (-0.5, 0, 0.5)),
                ((0, 0, 1), (0.5, 0, 0.5)),
            ],
        )

    elif shape == MarkerShape.DOWNARROW:
        _add_segments(
            vwriter,
            prim,
            [
                ((0, 0, -1), (0, 0, 0)),
                ((0, 0, -1), (-0.5, 0, -0.5)),
                ((0, 0, -1), (0.5, 0, -0.5)),
            ],
        )

    elif shape == MarkerShape.CIRCLE:
        n = 32
        rim = [(cos(2 * pi * i / n), 0, sin(2 * pi * i / n)) for i in range(n)]
        _add_loop(vwriter, prim, rim)

    elif shape == MarkerShape.DISK:
        n = 32
        rim = [(cos(2 * pi * i / n), 0, sin(2 * pi * i / n)) for i in range(n)]
        _add_fan(vwriter, prim, (0, 0, 0), rim)

    geom = Geom(vdata)
    geom.addPrimitive(prim)
    node = GeomNode(name)
    node.addGeom(geom)
    return node
