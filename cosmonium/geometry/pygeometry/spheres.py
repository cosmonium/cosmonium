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

"""Sphere geometry generators.

This module provides various methods for generating spherical geometry,
including UV-mapped spheres, displacement-mapped spheres, icosahedral
spheres, and patched spheres.
"""

from math import asin, atan2, cos, pi, sin, sqrt

from panda3d.core import GlobPattern, LPoint2d, LPoint3d, LVector3d, NodePath, VBase3, Vec3
from panda3d.egg import EggData, EggPolygon, EggVertex, EggVertexPool, loadEggData

from .core import empty_geom, empty_node


def UVSphere(
    axes: LVector3d, rings: int = 5, sectors: int = 5, inv_texture_u: bool = False, inv_texture_v: bool = False
) -> NodePath:
    """Create a UV-mapped sphere geometry.

    Generates a spherical mesh using latitude/longitude parameterization
    (UV mapping). The sphere is tessellated into rings (latitude divisions)
    and sectors (longitude divisions). Supports ellipsoids with different
    semi-axes.

    Args:
        axes: Semi-axes of the ellipsoid (rx, ry, rz). For a sphere, use
            equal values (e.g., LVector3d(1, 1, 1)). For an ellipsoid, use
            different values.
        rings: Number of horizontal divisions (latitude lines). Must be >= 2.
            Includes poles. Default is 5.
        sectors: Number of vertical divisions (longitude lines). Must be >= 3.
            Default is 5.
        inv_texture_u: If True, invert U texture coordinates (horizontal flip).
            Default is False.
        inv_texture_v: If True, invert V texture coordinates (vertical flip).
            Default is False.

    Returns:
        NodePath containing the sphere geometry with vertex positions, normals,
        texture coordinates, tangents, and binormals.

    Notes:
        - The sphere has poles at (0, 0, +/-axes.z).
        - Texture coordinates range from (0, 0) to (1, 1).
        - Normals point outward from the sphere center.
        - Tangent vectors point in the longitude direction.
        - Binormal vectors point in the latitude direction.
        - Uses latitude-longitude parameterization.
    """
    (path, node) = empty_node('uv')
    (gvw, gcw, gtw, gnw, gtanw, gbiw, prim, geom) = empty_geom(
        'uv', rings * sectors, (rings - 1) * sectors, tanbin=True
    )
    node.add_geom(geom)

    R = 1.0 / (rings - 1)
    S = 1.0 / (sectors - 1)

    u = 1.0
    v = 1.0
    if inv_texture_v:
        v = 1.0 - v
    if inv_texture_u:
        u = 1.0 - u
    normal_coefs = LVector3d(axes[1] * axes[2], axes[0] * axes[2], axes[0] * axes[1])
    gtw.add_data2(u, v)
    gvw.add_data3(0, 0, axes[2])
    gnw.add_data3(0, 0, 1)
    gtanw.add_data3(0, 1, 0)
    gbiw.add_data3(1, 0, 0)
    for r in range(0, rings):
        for s in range(0, sectors):
            cos_s = cos(2 * pi * s * S + pi)
            sin_s = sin(2 * pi * s * S + pi)
            sin_r = sin(pi * r * R)
            cos_r = cos(pi * r * R)
            point = LVector3d(cos_s * sin_r, sin_s * sin_r, -cos_r)
            normal = LVector3d(point)
            if sin_r != 0:
                tangent = LVector3d(-axes[0] * point[1], axes[1] * point[0], 0)
            else:
                tangent = LVector3d(-axes[0], 0, 0)
            u = s * S
            v = r * R
            if inv_texture_v:
                v = 1.0 - v
            if inv_texture_u:
                u = 1.0 - u
            gtw.add_data2(u, v)
            point.componentwise_mult(axes)
            gvw.add_data3d(point)
            normal.componentwise_mult(normal_coefs)
            normal.normalize()
            gnw.add_data3d(normal)
            tangent.normalize()
            gtanw.add_data3d(tangent)
            binormal = normal.cross(tangent)
            binormal.normalize()
            gbiw.add_data3d(binormal)
    u = 0.0
    v = 0.0
    if inv_texture_v:
        v = 1.0 - v
    if inv_texture_u:
        u = 1.0 - u
    gtw.add_data2(u, v)
    gvw.add_data3(0, 0, -axes[2])
    gnw.add_data3(0, 0, -1)
    gtanw.add_data3(1, 0, 0)
    gbiw.add_data3(0, 1, 0)

    for r in range(0, rings - 1):
        for s in range(0, sectors):
            if r == 0:
                prim.add_vertices(r * sectors + (s + 1), (r + 1) * sectors + (s + 1), (r + 1) * sectors + s)
            elif r == rings - 1:
                prim.add_vertices(r * sectors + (s + 1), (r + 1) * sectors + (s + 1), (r + 1) * sectors + s)
            else:
                prim.add_vertices(r * sectors + s, r * sectors + (s + 1), (r + 1) * sectors + s)
                prim.add_vertices(r * sectors + (s + 1), (r + 1) * sectors + (s + 1), (r + 1) * sectors + s)
    prim.closePrimitive()
    geom.addPrimitive(prim)

    return path


def DisplacementUVSphere(
    radius: float,
    heightmap,
    scale: float,
    rings: int = 5,
    sectors: int = 5,
    inv_texture_u: bool = False,
    inv_texture_v: bool = True,
) -> NodePath:
    """Create sphere with height-mapped displacement.

    Generates a spherical mesh where vertex positions are displaced by a
    heightmap.
    Uses Panda3D's Egg format for automatic normal calculation.

    Args:
        radius: Base radius of the sphere before displacement.
        heightmap: Heightmap object that provides a get_height_uv(u, v) method
            returning height values at UV coordinates.
        scale: Multiplier for heightmap values. Final vertex radius is
            radius + heightmap_value * scale.
        rings: Number of horizontal divisions (latitude lines). Default is 5.
        sectors: Number of vertical divisions (longitude lines). Default is 5.
        inv_texture_u: If True, invert U texture coordinates. Default is False.
        inv_texture_v: If True, invert V texture coordinates. Default is True.

    Returns:
        NodePath containing the displaced sphere geometry with automatically
        computed normals, tangents, and binormals.

    Notes:
        - Vertex positions: (x, y, z) * (radius + heightmap(u, v) * scale).
        - Normals are recomputed at 45° threshold after displacement.
        - Tangent and binormal vectors are automatically calculated.
        - Uses Egg data format internally for advanced processing.
        - Geometry is flattened after creation for performance.
    """
    data = EggData()
    pool = EggVertexPool('pool')
    vertices = []
    data.addChild(pool)
    R = 1.0 / (rings)
    S = 1.0 / (sectors)
    for r in range(0, rings + 1):
        for s in range(0, sectors + 1):
            cos_s = cos(2 * pi * s * S + pi)
            sin_s = sin(2 * pi * s * S + pi)
            sin_r = sin(pi * r * R)
            cos_r = cos(pi * r * R)
            x = cos_s * sin_r
            y = sin_s * sin_r
            z = cos_r
            vertex = EggVertex()
            u = s * S
            v = r * R
            height = radius + heightmap.get_height_uv(u, v) * scale
            vertex.setPos(LPoint3d(x * height, y * height, z * height))
            if inv_texture_v:
                v = 1.0 - v
            if inv_texture_u:
                u = 1.0 - u
            vertex.setUv(LPoint2d(u, v))
            pool.addVertex(vertex)
            vertices.append(vertex)

    index = 0
    for r in range(0, rings):
        for s in range(0, sectors):
            poly = EggPolygon()
            data.addChild(poly)
            poly.addVertex(vertices[index + sectors + 1])
            poly.addVertex(vertices[index])
            poly.addVertex(vertices[index + sectors])

            poly = EggPolygon()
            data.addChild(poly)
            poly.addVertex(vertices[index + sectors + 1])
            poly.addVertex(vertices[index + 1])
            poly.addVertex(vertices[index])
            index += 1
    data.removeUnusedVertices(True)
    data.recomputeVertexNormals(45)
    data.recomputeTangentBinormal(GlobPattern(""))
    node = loadEggData(data)
    path = NodePath(node)
    path.flattenStrong()
    return path


def UVPatchedSphere(radius: float = 1, rings: int = 8, sectors: int = 16, lod: int = 2) -> NodePath:
    """Create sphere from patches with LOD.

    Generates a sphere by subdividing it into multiple UV patches.

    Args:
        radius: Radius of the sphere. Default is 1.
        rings: Number of rings (latitude divisions) for each patch.
            Default is 8.
        sectors: Number of sectors (longitude divisions) for each patch.
            Default is 16.
        lod: Level of detail - determines patch subdivision. LOD=1 creates
            two hemispheres, LOD=2 creates 4*4 patches, etc. Formula:
            - ring_divisions = 2^lod
            - sector_divisions = 2^(lod+1)
            Default is 2.

    Returns:
        NodePath containing all patches as children.

    Notes:
        - Total patches = 2^lod × 2^(lod+1) = 2^(2*lod+1).
        - LOD 1: 4 patches (2 rings × 2 sectors).
        - LOD 2: 16 patches (4 rings × 4 sectors).
        - LOD 3: 64 patches (8 rings × 8 sectors).
    """
    # Import here to avoid circular dependency
    from .patches import UVPatch

    path = NodePath('uv')
    r_div = 1 << lod
    s_div = 2 << lod
    for sector in range(s_div):
        for ring in range(r_div):
            x0 = int(sector * sectors / s_div)
            y0 = int(ring * rings / r_div)
            x1 = int((sector + 1) * sectors / s_div)
            y1 = int((ring + 1) * rings / r_div)
            subpath = UVPatch(radius, rings, sectors, x0, y0, x1, y1)
            subpath.reparentTo(path)
    return path


def IcoSphere(radius: float = 1, subdivisions: int = 1) -> NodePath:
    """Create icosahedral sphere with subdivision.

    Generates a sphere by recursively subdividing an icosahedron (20-sided
    polyhedron). This method produces more uniform triangle distribution
    compared to UV mapping, avoiding pole singularities.

    Args:
        radius: Radius of the sphere. Default is 1.
        subdivisions: Number of subdivision iterations. Each subdivision
            quadruples the triangle count:
            - 0 subdivisions: 20 triangles (base icosahedron).
            - 1 subdivision: 80 triangles.
            - 2 subdivisions: 320 triangles.
            - 3 subdivisions: 1,280 triangles.
            - N subdivisions: 20 × 4^N triangles.
            Default is 1.

    Returns:
        NodePath containing the icosphere geometry with positions, normals,
        texture coordinates, tangents, and binormals.

    Notes:
        - Texture coordinates are calculated spherically using atan2 and asin.
        - Seam handling: Duplicates vertices at texture wrap boundary (u=0/1).
        - More uniform triangle distribution than UV spheres.
        - No singularities at poles.
        - Higher vertex count for equivalent tessellation density.
        - Tangent/binormal generation is included for normal mapping.
    """
    (path, node) = empty_node('ico')
    (gvw, gcw, gtw, gnw, gtanw, gbiw, prim, geom) = empty_geom('ico', 0, 0, tanbin=True)
    node.add_geom(geom)

    verts = []

    phi = 0.5 * (1.0 + sqrt(5.0))
    invnorm = 1 / sqrt(phi * phi + 1)

    verts.append(Vec3(-1, phi, 0) * invnorm)  # 0
    verts.append(Vec3(1, phi, 0) * invnorm)  # 1
    verts.append(Vec3(0, 1, -phi) * invnorm)  # 2
    verts.append(Vec3(0, 1, phi) * invnorm)  # 3
    verts.append(Vec3(-phi, 0, -1) * invnorm)  # 4
    verts.append(Vec3(-phi, 0, 1) * invnorm)  # 5
    verts.append(Vec3(phi, 0, -1) * invnorm)  # 6
    verts.append(Vec3(phi, 0, 1) * invnorm)  # 7
    verts.append(Vec3(0, -1, -phi) * invnorm)  # 8
    verts.append(Vec3(0, -1, phi) * invnorm)  # 9
    verts.append(Vec3(-1, -phi, 0) * invnorm)  # 10
    verts.append(Vec3(1, -phi, 0) * invnorm)  # 11

    faces = [
        0,
        1,
        2,
        0,
        3,
        1,
        0,
        4,
        5,
        1,
        7,
        6,
        1,
        6,
        2,
        1,
        3,
        7,
        0,
        2,
        4,
        0,
        5,
        3,
        2,
        6,
        8,
        2,
        8,
        4,
        3,
        5,
        9,
        3,
        9,
        7,
        11,
        6,
        7,
        10,
        5,
        4,
        10,
        4,
        8,
        10,
        9,
        5,
        11,
        8,
        6,
        11,
        7,
        9,
        10,
        8,
        11,
        10,
        11,
        9,
    ]

    size = 60

    # Step 2 : tessellate
    for subdivision in range(0, subdivisions):
        size *= 4
        newFaces = []
        for i in range(0, int(size / 12)):
            i1 = faces[i * 3]
            i2 = faces[i * 3 + 1]
            i3 = faces[i * 3 + 2]
            i12 = len(verts)
            i23 = i12 + 1
            i13 = i12 + 2
            v1 = verts[i1]
            v2 = verts[i2]
            v3 = verts[i3]
            # make 1 vertice at the center of each edge and project it onto the sphere
            vt = v1 + v2
            vt.normalize()
            verts.append(vt)
            vt = v2 + v3
            vt.normalize()
            verts.append(vt)
            vt = v1 + v3
            vt.normalize()
            verts.append(vt)
            # now recreate indices
            newFaces.append(i1)
            newFaces.append(i12)
            newFaces.append(i13)
            newFaces.append(i2)
            newFaces.append(i23)
            newFaces.append(i12)
            newFaces.append(i3)
            newFaces.append(i13)
            newFaces.append(i23)
            newFaces.append(i12)
            newFaces.append(i23)
            newFaces.append(i13)
        faces = newFaces

    vertices = []
    texs = []
    norms = []
    for i in range(0, len(verts)):
        vert = verts[i]
        vertices.append(VBase3(vert * radius))
        norms.append(vert)
        # Calculate texture coords
        u = -((atan2(vert.x, vert.y)) / pi) / 2.0 + 0.5
        v = asin(vert.z) / pi + 0.5
        texs.append([u, v])
    indices = len(vertices)
    for i in range(0, int(len(faces) / 3)):
        i1 = faces[i * 3]
        i2 = faces[i * 3 + 1]
        i3 = faces[i * 3 + 2]
        u1 = texs[i2][0] - texs[i1][0]
        v1 = texs[i2][1] - texs[i1][1]
        u2 = texs[i3][0] - texs[i2][0]
        v2 = texs[i3][1] - texs[i2][1]
        if (u1 * v2 - u2 * v1) < 0:
            if texs[i1][0] < 0.5:
                vertices.append(vertices[i1])
                norms.append(norms[i1])
                texs.append([texs[i1][0] + 1.0, texs[i1][1]])
                i1 = indices
                indices += 1
            if texs[i2][0] < 0.5:
                vertices.append(vertices[i2])
                norms.append(norms[i2])
                texs.append([texs[i2][0] + 1.0, texs[i2][1]])
                i2 = indices
                indices += 1
            if texs[i3][0] < 0.5:
                vertices.append(vertices[i3])
                norms.append(norms[i3])
                texs.append([texs[i3][0] + 1.0, texs[i3][1]])
                i3 = indices
                indices += 1
        faces[i * 3] = i1
        faces[i * 3 + 1] = i2
        faces[i * 3 + 2] = i3
    for i in range(0, len(vertices)):
        gvw.add_data3(vertices[i])
        gnw.add_data3(norms[i])
        gtw.add_data2(*texs[i])
    for i in range(0, int(len(faces) / 3)):
        i1 = faces[i * 3]
        i2 = faces[i * 3 + 1]
        i3 = faces[i * 3 + 2]
        prim.add_vertices(i1, i2, i3)

    prim.closePrimitive()
    geom.addPrimitive(prim)

    return path
