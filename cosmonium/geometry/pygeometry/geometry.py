#
# This file is part of Cosmonium.
#
# Copyright (C) 2018-2022 Laurent Deru.
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

from math import sin, cos, pi, atan2, sqrt, asin

from panda3d.core import Geom, GeomNode, GeomPatches, GeomPoints, GeomVertexData, GeomVertexArrayFormat, InternalName
from panda3d.core import LVector3d, GlobPattern, BoundingBox, LPoint3
from panda3d.core import GeomVertexFormat, GeomTriangles, GeomVertexWriter, ColorAttrib
from panda3d.core import NodePath, VBase3, Vec3, LPoint3d, LPoint2d
from panda3d.egg import EggData, EggVertexPool, EggVertex, EggPolygon, loadEggData

from ...pstats import named_pstat


def empty_node(prefix, color=False):
    path = NodePath(prefix + '_path')
    node = GeomNode(prefix + '_node')
    path.attachNewNode(node)
    if color:
        path.setAttrib(ColorAttrib.makeVertex())
    return (path, node)


def empty_geom(prefix, nb_data, nb_vertices, points=False, normal=True, texture=True, color=False, tanbin=False):
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
    if points:
        prim = GeomPoints(Geom.UHStatic)
    else:
        prim = GeomTriangles(Geom.UHStatic)
    if nb_vertices != 0:
        prim.reserve_num_vertices(nb_vertices)
    return (gvw, gcw, gtw, gnw, gtanw, gbiw, prim, geom)


def BoundingBoxGeom(box):
    (path, node) = empty_node('bb')
    (gvw, gcw, gtw, gnw, gtanw, gbiw, prim, geom) = empty_geom(
        'bb', 8, 12, normal=False, texture=False, tanbin=False)
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


def CubeGeom():
    (path, node) = empty_node('cube')
    (gvw, gcw, gtw, gnw, gtanw, gbiw, prim, geom) = empty_geom(
        'cube', 8, 12, normal=False, texture=False, tanbin=False)
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


def UVSphere(radius=1, rings=5, sectors=5, inv_texture_u=False, inv_texture_v=False):
    (path, node) = empty_node('uv')
    (gvw, gcw, gtw, gnw, gtanw, gbiw, prim, geom) = empty_geom(
        'uv', rings * sectors, (rings - 1) * sectors, tanbin=True)
    node.add_geom(geom)

    R = 1. / (rings - 1)
    S = 1. / (sectors - 1)

    u = 1.0
    v = 1.0
    if inv_texture_v:
        v = 1.0 - v
    if inv_texture_u:
        u = 1.0 - u
    gtw.add_data2(u, v)
    gvw.add_data3(0, 0, radius)
    gnw.add_data3(0, 0, 1)
    gtanw.add_data3(0, 1, 0)
    gbiw.add_data3(1, 0, 0)
    for r in range(0, rings):
        for s in range(0, sectors):
            cos_s = cos(2 * pi * s * S + pi)
            sin_s = sin(2 * pi * s * S + pi)
            sin_r = sin(pi * r * R)
            cos_r = cos(pi * r * R)
            x = cos_s * sin_r
            y = sin_s * sin_r
            z = -cos_r
            u = s * S
            v = r * R
            if inv_texture_v:
                v = 1.0 - v
            if inv_texture_u:
                u = 1.0 - u
            gtw.add_data2(u, v)
            gvw.add_data3(x * radius, y * radius, z * radius)
            gnw.add_data3(x, y, z)
            # Derivation wrt s and normalization (sin_r is dropped)
            gtanw.add_data3(-sin_s, cos_s, 0)  # -y, x, 0
            # Derivation wrt r
            binormal = LVector3d(cos_s * cos_r, sin_s * cos_r, sin_r)
            binormal.normalize()
            gbiw.add_data3d(binormal)
    u = 0.0
    v = 0.0
    if inv_texture_v:
        v = 1.0 - v
    if inv_texture_u:
        u = 1.0 - u
    gtw.add_data2(u, v)
    gvw.add_data3(0, 0, -radius)
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


def DisplacementUVSphere(radius, heightmap, scale, rings=5, sectors=5, inv_texture_u=False, inv_texture_v=True):
    data = EggData()
    pool = EggVertexPool('pool')
    vertices = []
    data.addChild(pool)
    R = 1. / (rings)
    S = 1. / (sectors)
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


def UVPatchPoint(axes, r, s, x0, y0, x1, y1, offset=0.0):
    dx = x1 - x0
    dy = y1 - y0

    cos_s = cos(2 * pi * (x0 + s * dx) + pi)
    sin_s = sin(2 * pi * (x0 + s * dx) + pi)
    sin_r = sin(pi * (y0 + r * dy))
    cos_r = cos(pi * (y0 + r * dy))
    point = LPoint3d(
        cos_s * sin_r,
        sin_s * sin_r,
        -cos_r)
    point.componentwise_mult(axes)

    if offset != 0.0:
        offset_vector = UVPatchOffsetVector(axes, x0, y0, x1, y1)
        point -= offset_vector * offset

    return point


def UVPatchNormal(axes, r, s, x0, y0, x1, y1):
    dx = x1 - x0
    dy = y1 - y0

    cos_s = cos(2 * pi * (x0 + s * dx) + pi)
    sin_s = sin(2 * pi * (x0 + s * dx) + pi)
    sin_r = sin(pi * (y0 + r * dy))
    cos_r = cos(pi * (y0 + r * dy))
    normal = LPoint3d(
        axes[1] * axes[2] * cos_s * sin_r,
        axes[0] * axes[2] * sin_s * sin_r,
        -axes[0] * axes[1] * cos_r)
    normal.normalize()
    return normal


def UVPatchOffsetVector(axes, x0, y0, x1, y1):
    dx = x1 - x0
    dy = y1 - y0
    v = LVector3d(
        cos(2 * pi * (x0 + dx / 2) + pi) * sin(pi * (y0 + dy / 2)),
        sin(2 * pi * (x0 + dx / 2) + pi) * sin(pi * (y0 + dy / 2)),
        -cos(pi * (y0 + dy / 2)))
    v.componentwise_mult(axes)
    return v


@named_pstat("geom")
def UVPatch(axes, rings, sectors, x0, y0, x1, y1,
            global_texture=False, inv_texture_u=False, inv_texture_v=False, offset=0.0):
    r_sectors = sectors + 1
    r_rings = rings + 1

    (path, node) = empty_node('uv')
    (gvw, gcw, gtw, gnw, gtanw, gbiw, prim, geom) = empty_geom(
        'uv', (r_rings * r_sectors), rings * sectors, tanbin=True)

    dx = x1 - x0
    dy = y1 - y0

    if offset != 0.0:
        offset_vector = UVPatchOffsetVector(axes, x0, y0, x1, y1) * offset

    normal_coefs = LVector3d(axes[1] * axes[2], axes[0] * axes[2], axes[0] * axes[1])
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
            binormal = normal.cross(tangent)
            binormal.normalize()
            gbiw.add_data3d(binormal)

    for r in range(0, r_rings - 1):
        for s in range(0, r_sectors - 1):
            # if y0 == 0 and r == 0:
            #     #prim.add_vertices((r+1) * r_sectors + (s+1), (r+1) * r_sectors + s, r * r_sectors + (s+1))
            # elif y1 == rings and r == r_rings - 1:
            #     #prim.add_vertices((r+1) * r_sectors + (s+1), (r+1) * r_sectors + s, r * r_sectors + (s+1))
            # else:
            # if y0 >= 0.5:
            prim.add_vertices(r * r_sectors + s, r * r_sectors + (s + 1), (r + 1) * r_sectors + s)
            prim.add_vertices(r * r_sectors + (s + 1), (r + 1) * r_sectors + (s + 1), (r + 1) * r_sectors + s)
            # else:
            #     prim.add_vertices((r + 1) * r_sectors + s, r * r_sectors + (s+1), r * r_sectors + s)
            #     prim.add_vertices(r * r_sectors + (s+1), (r+1) * r_sectors + s, (r + 1) * r_sectors + (s+1))
    prim.closePrimitive()
    geom.addPrimitive(prim)
    node.add_geom(geom)
    return path


def halfSphereAABB(mean_height, positive, offset=0.0):
    if positive:
        min_points = LPoint3(-1, 0 - offset, -1)
        max_points = LPoint3(1, 1 - offset, 1)
    else:
        min_points = LPoint3(-1, offset - 1, -1)
        max_points = LPoint3(1, offset, 1)
    return BoundingBox(min_points, max_points)


def UVPatchAABB(axes, min_height, max_height, x0, y0, x1, y1, offset=0.0):
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
    x_min = min(p.get_x() for p in points)
    x_max = max(p.get_x() for p in points)
    y_min = min(p.get_y() for p in points)
    y_max = max(p.get_y() for p in points)
    z_min = min(p.get_z() for p in points)
    z_max = max(p.get_z() for p in points)
    box = BoundingBox(LPoint3(x_min, y_min, z_min), LPoint3(x_max, y_max, z_max))
    return box


def UVPatchedSphere(radius=1, rings=8, sectors=16, lod=2):
    # LOD = 1 : Two half sphere
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


def IcoSphere(radius=1, subdivisions=1):
    (path, node) = empty_node('ico')
    (gvw, gcw, gtw, gnw, gtanw, gbiw, prim, geom) = empty_geom('ico', 0, 0, tanbin=True)
    node.add_geom(geom)

    verts = []

    phi = .5 * (1. + sqrt(5.))
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
        0, 1, 2,
        0, 3, 1,
        0, 4, 5,
        1, 7, 6,
        1, 6, 2,
        1, 3, 7,
        0, 2, 4,
        0, 5, 3,
        2, 6, 8,
        2, 8, 4,
        3, 5, 9,
        3, 9, 7,
        11, 6, 7,
        10, 5, 4,
        10, 4, 8,
        10, 9, 5,
        11, 8, 6,
        11, 7, 9,
        10, 8, 11,
        10, 11, 9
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


class TesselationInfo():

    def __init__(self, inner, outer):
        self.inner = inner
        self.outer = outer
        self.ratio = [inner // x if inner >= x else 1 for x in outer]


def make_config(inner, outer):
    nb_vertices = inner + 1
    if outer is None:
        outer = [inner, inner, inner, inner]
    ratio = [inner // x if inner >= x else 1 for x in outer]
    return (nb_vertices, inner, outer, ratio)


def make_square_primitives(prim, inner, nb_vertices):
    for x in range(0, inner):
        for y in range(0, inner):
            v = nb_vertices * x + y
            prim.add_vertices(v, v + nb_vertices, v + 1)
            prim.add_vertices(v + 1, v + nb_vertices, v + nb_vertices + 1)


def make_adapted_square_primitives(prim, inner, nb_vertices, ratio):
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


def make_adapted_square_primitives_skirt(prim, inner, nb_vertices, ratio):
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


def make_primitives_skirt(prim, inner, nb_vertices):
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


@named_pstat("geom")
def Tile(size, tesselation,
         inv_u=False, inv_v=False, swap_uv=False,
         use_patch_adaptation=True,
         use_patch_skirts=True,
         skirt_size=0.1, skirt_uv=0.1):
    inner = tesselation.inner
    nb_vertices = inner + 1
    (path, node) = empty_node('uv')
    nb_points = nb_vertices * nb_vertices
    nb_primitives = inner * inner
    if use_patch_skirts:
        nb_points += nb_vertices * 4
        nb_primitives += inner * 4
    (gvw, gcw, gtw, gnw, gtanw, gbiw, prim, geom) = empty_geom(
        'cube', nb_points, nb_primitives, tanbin=True)
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
        make_adapted_square_primitives(prim, inner, nb_vertices, tesselation.ratio)
        if use_patch_skirts:
            make_adapted_square_primitives_skirt(prim, inner, nb_vertices, tesselation.ratio)
    else:
        make_square_primitives(prim, inner, nb_vertices)
        if use_patch_skirts:
            make_primitives_skirt(prim, inner, nb_vertices)
    prim.closePrimitive()
    geom.addPrimitive(prim)

    return path


def TileAABB(size=1.0, height=1.0):
    return BoundingBox(LPoint3(0, 0, -height), LPoint3(size, size, height))


def Patch(size=1.0):
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


def PatchAABB(x=0.0, y=0.0, size=1.0, scale=1.0, min_height=-1.0, max_height=1.0):
    return BoundingBox(LPoint3(x * scale, y * scale, min_height),
                       LPoint3((x + size) * scale, (y + size) * scale, max_height))


def convert_xy(x0, y0, x1, y1, x_inverted=False, y_inverted=False, xy_swap=False):
    if x_inverted:
        x0, x1 = 1 - x1, 1 - x0
    if y_inverted:
        y0, y1 = 1 - y1, 1 - y0
    if xy_swap:
        x0, y0 = y0, x0
        x1, y1 = y1, x1

    dx = float(x1 - x0)
    dy = float(y1 - y0)

    return (x0, y0, x1, y1, dx, dy)


def QuadPatch(x0, y0, x1, y1,
              x_inverted=False, y_inverted=False, xy_swap=False, offset=None):

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


@named_pstat("geom")
def SquarePatch(height, inner, outer,
                x0, y0, x1, y1,
                inv_u=False, inv_v=False, swap_uv=False,
                x_inverted=False, y_inverted=False, xy_swap=False, offset=None):
    (nb_vertices, inner, outer, ratio) = make_config(inner, outer)

    (path, node) = empty_node('uv')
    (gvw, gcw, gtw, gnw, gtanw, gbiw, prim, geom) = empty_geom(
        'cube', nb_vertices * nb_vertices, inner * inner, tanbin=True)
    node.add_geom(geom)

    (x0, y0, x1, y1, dx, dy) = convert_xy(x0, y0, x1, y1, x_inverted, y_inverted, xy_swap)

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

            if inv_u:
                u = 1.0 - u
            if inv_v:
                v = 1.0 - v
            if swap_uv:
                gtw.add_data2(v, u)
            else:
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
        axes, tesselation,
        x0, y0, x1, y1,
        inv_u=False, inv_v=False, swap_uv=False,
        x_inverted=False, y_inverted=False, xy_swap=False, has_offset=False, offset=None,
        use_patch_adaptation=True,
        use_patch_skirts=True,
        skirt_size=0.001, skirt_uv=0.001):
    (path, node) = empty_node('uv')
    inner = tesselation.inner
    nb_vertices = inner + 1
    nb_points = nb_vertices * nb_vertices
    nb_primitives = inner * inner
    if use_patch_skirts:
        nb_points += nb_vertices * 4
        nb_primitives += inner * 4
    (gvw, gcw, gtw, gnw, gtanw, gbiw, prim, geom) = empty_geom(
        'cube', nb_points, nb_primitives, tanbin=True)
    node.add_geom(geom)

    if offset is not None:
        offset_vector = SquaredDistanceSquarePatchOffsetVector(
            axes, x0, y0, x1, y1, x_inverted, y_inverted, xy_swap) * offset

    (x0, y0, x1, y1, dx, dy) = convert_xy(x0, y0, x1, y1, x_inverted, y_inverted, xy_swap)

    normal_coefs = LVector3d(axes[1] * axes[2], axes[0] * axes[2], axes[0] * axes[1])
    for i in range(0, nb_vertices):
        for j in range(0, nb_vertices):
            u = float(i) / inner
            v = float(j) / inner
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
            tangent = LVector3d(1.0, x * y * (z2 / 3.0 - 0.5), x * z * (y2 / 3.0 - 0.5))
            if inv_u:
                u = 1.0 - u
            if inv_v:
                v = 1.0 - v
            if swap_uv:
                u, v = v, u
            gtw.add_data2(u, v)
            point.componentwise_mult(axes)
            if offset is not None:
                point -= offset_vector
            gvw.add_data3(point)
            normal.componentwise_mult(normal_coefs)
            normal.normalize()
            gnw.add_data3(normal)
            tangent.componentwise_mult(axes)
            tangent.normalize()
            binormal = normal.cross(tangent)
            binormal.normalize()
            if inv_u:
                tangent = -tangent
            if inv_v:
                binormal = -binormal
            if swap_uv:
                tangent, binormal = binormal, tangent
            gtanw.add_data3d(tangent)
            gbiw.add_data3d(binormal)

    if use_patch_skirts:
        reduced_axes = axes - LVector3d(max(dx, dy) * skirt_size)
        for a in range(0, 4):
            for b in range(0, nb_vertices):
                if a == 0:
                    i = 0
                    j = b
                elif a == 1:
                    i = inner
                    j = b
                elif a == 2:
                    i = b
                    j = 0
                elif a == 3:
                    i = b
                    j = inner
                u = float(i) / inner
                v = float(j) / inner
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
                tangent = LVector3d(1.0, x * y * (z2 / 3.0 - 0.5), x * z * (y2 / 3.0 - 0.5))
                if inv_u:
                    u = 1.0 - u
                if inv_v:
                    v = 1.0 - v
                if swap_uv:
                    u, v = v, u
                gtw.add_data2(u, v)
                point.componentwise_mult(reduced_axes)
                if offset is not None:
                    point -= offset_vector
                gvw.add_data3(point)
                normal.componentwise_mult(normal_coefs)
                normal.normalize()
                gnw.add_data3(normal)
                tangent.componentwise_mult(axes)
                tangent.normalize()
                binormal = normal.cross(tangent)
                binormal.normalize()
                if inv_u:
                    tangent = -tangent
                if inv_v:
                    binormal = -binormal
                if swap_uv:
                    tangent, binormal = binormal, tangent
                gtanw.add_data3d(tangent)
                gbiw.add_data3d(binormal)

    if use_patch_adaptation:
        make_adapted_square_primitives(prim, inner, nb_vertices, tesselation.ratio)
        if use_patch_skirts:
            make_adapted_square_primitives_skirt(prim, inner, nb_vertices, tesselation.ratio)
    else:
        make_square_primitives(prim, inner, nb_vertices)
        if use_patch_skirts:
            make_primitives_skirt(prim, inner, nb_vertices)
    prim.closePrimitive()
    geom.addPrimitive(prim)

    return path


def SquaredDistanceSquarePatchPoint(axes,
                                    u, v,
                                    x0, y0, x1, y1,
                                    offset=None,
                                    x_inverted=False, y_inverted=False, xy_swap=False):

    if offset is not None:
        offset_vector = SquaredDistanceSquarePatchOffsetVector(axes, x0, y0, x1, y1, x_inverted, y_inverted, xy_swap)

    (x0, y0, x1, y1, dx, dy) = convert_xy(x0, y0, x1, y1, x_inverted, y_inverted, xy_swap)

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


def SquaredDistanceSquarePatchNormal(axes,
                                     u, v,
                                     x0, y0, x1, y1,
                                     x_inverted=False, y_inverted=False, xy_swap=False):

    (x0, y0, x1, y1, dx, dy) = convert_xy(x0, y0, x1, y1, x_inverted, y_inverted, xy_swap)

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


def SquaredDistanceSquarePatchOffsetVector(axes, x0, y0, x1, y1,
                                           x_inverted=False, y_inverted=False, xy_swap=False):

    return SquaredDistanceSquarePatchPoint(axes, 0.5, 0.5, x0, y0, x1, y1, None, x_inverted, y_inverted, xy_swap)


def SquaredDistanceSquarePatchAABB(axes, min_height, max_height,
                                   x0, y0, x1, y1, offset=None,
                                   x_inverted=False, y_inverted=False, xy_swap=False):
    points = []
    if min_height != max_height:
        heights = (min_height, max_height)
    else:
        heights = (min_height,)
    if offset is not None:
        offset_vector = SquaredDistanceSquarePatchOffsetVector(
            axes, x0, y0, x1, y1, x_inverted, y_inverted, xy_swap) * offset
    for height in heights:
        for i in (0.0, 0.5, 1.0):
            for j in (0.0, 0.5, 1.0):
                point = SquaredDistanceSquarePatchPoint(
                    axes, i, j, x0, y0, x1, y1, None, x_inverted, y_inverted, xy_swap)
                if height != 0:
                    normal = SquaredDistanceSquarePatchNormal(
                        axes, i, j, x0, y0, x1, y1, x_inverted, y_inverted, xy_swap)
                    point += normal * height
                if offset is not None:
                    point -= offset_vector
                points.append(point)
    x_min = min(p.get_x() for p in points)
    x_max = max(p.get_x() for p in points)
    y_min = min(p.get_y() for p in points)
    y_max = max(p.get_y() for p in points)
    z_min = min(p.get_z() for p in points)
    z_max = max(p.get_z() for p in points)
    box = BoundingBox(LPoint3(x_min, y_min, z_min), LPoint3(x_max, y_max, z_max))
    return box


@named_pstat("geom")
def NormalizedSquarePatch(axes, tesselation,
                          x0, y0, x1, y1,
                          inv_u=False, inv_v=False, swap_uv=False,
                          x_inverted=False, y_inverted=False, xy_swap=False, has_offset=False, offset=None,
                          use_patch_adaptation=True,
                          use_patch_skirts=True,
                          skirt_size=0.001, skirt_uv=0.001):
    (path, node) = empty_node('uv')
    #use_patch_skirts = False
    inner = tesselation.inner
    nb_vertices = inner + 1
    nb_points = nb_vertices * nb_vertices
    nb_primitives = inner * inner
    if use_patch_skirts:
        nb_points += nb_vertices * 4
        nb_primitives += inner * 4
    (gvw, gcw, gtw, gnw, gtanw, gbiw, prim, geom) = empty_geom('cube', nb_points, nb_primitives, tanbin=True)
    node.add_geom(geom)

    if has_offset:
        offset_vector = NormalizedSquarePatchOffsetVector(
            axes, x0, y0, x1, y1, x_inverted, y_inverted, xy_swap) * offset

    (x0, y0, x1, y1, dx, dy) = convert_xy(x0, y0, x1, y1, x_inverted, y_inverted, xy_swap)

    normal_coefs = LVector3d(axes[1] * axes[2], axes[0] * axes[2], axes[0] * axes[1])
    for i in range(0, nb_vertices):
        for j in range(0, nb_vertices):
            x = x0 + i * dx / inner
            y = y0 + j * dy / inner
            x = 2.0 * x - 1.0
            y = 2.0 * y - 1.0
            point = LVector3d(x, y, 1.0)
            point.normalize()
            normal = LVector3d(point)
            tangent = LVector3d(1.0 + y * y, -x * y, -x)
            u = float(i) / inner
            v = float(j) / inner
            if inv_u:
                u = 1.0 - u
            if inv_v:
                v = 1.0 - v
            if swap_uv:
                u, v = v, u
            gtw.add_data2(u, v)
            point.componentwise_mult(axes)
            if offset is not None:
                point -= offset_vector
            gvw.add_data3d(point)
            normal.componentwise_mult(normal_coefs)
            normal.normalize()
            gnw.add_data3d(normal)
            tangent.componentwise_mult(axes)
            tangent.normalize()
            binormal = normal.cross(tangent)
            binormal.normalize()
            if inv_u:
                tangent = -tangent
            if inv_v:
                binormal = -binormal
            if swap_uv:
                tangent, binormal = binormal, tangent
            gtanw.add_data3d(tangent)
            gbiw.add_data3d(binormal)

    if use_patch_skirts:
        reduced_axes = axes - LVector3d(max(dx, dy) * skirt_size)
        for a in range(0, 4):
            for b in range(0, nb_vertices):
                if a == 0:
                    i = 0
                    j = b
                elif a == 1:
                    i = inner
                    j = b
                elif a == 2:
                    i = b
                    j = 0
                elif a == 3:
                    i = b
                    j = inner
                x = x0 + i * dx / inner
                y = y0 + j * dy / inner
                x = 2.0 * x - 1.0
                y = 2.0 * y - 1.0
                point = LVector3d(x, y, 1.0)
                point.normalize()
                normal = LVector3d(point)
                tangent = LVector3d(1.0 + y * y, -x * y, -x)
                u = float(i) / inner
                v = float(j) / inner
                if inv_u:
                    u = 1.0 - u
                if inv_v:
                    v = 1.0 - v
                if swap_uv:
                    u, v = v, u
                gtw.add_data2(u, v)
                point.componentwise_mult(reduced_axes)
                if offset is not None:
                    point -= offset_vector
                gvw.add_data3d(point)
                normal.componentwise_mult(normal_coefs)
                normal.normalize()
                gnw.add_data3d(normal)
                tangent.componentwise_mult(axes)
                tangent.normalize()
                binormal = tangent.cross(normal)
                binormal.normalize()
                if inv_u:
                    tangent = -tangent
                if inv_v:
                    binormal = -binormal
                if swap_uv:
                    tangent, binormal = binormal, tangent
                gtanw.add_data3d(tangent)
                gbiw.add_data3d(binormal)

    if use_patch_adaptation:
        make_adapted_square_primitives(prim, inner, nb_vertices, tesselation.ratio)
        if use_patch_skirts:
            make_adapted_square_primitives_skirt(prim, inner, nb_vertices, tesselation.ratio)
    else:
        make_square_primitives(prim, inner, nb_vertices)
        if use_patch_skirts:
            make_primitives_skirt(prim, inner, nb_vertices)
    prim.closePrimitive()
    geom.addPrimitive(prim)

    return path


def NormalizedSquarePatchPoint(axes,
                               u, v,
                               x0, y0, x1, y1,
                               offset=None,
                               x_inverted=False, y_inverted=False, xy_swap=False):
    (x0, y0, x1, y1, dx, dy) = convert_xy(x0, y0, x1, y1, x_inverted, y_inverted, xy_swap)

    x = x0 + u * dx
    y = y0 + v * dy
    vec = LVector3d(2.0 * x - 1.0, 2.0 * y - 1.0, 1.0)
    vec.normalize()
    vec.componentwise_mult(axes)

    if offset is not None:
        offset_vector = NormalizedSquarePatchOffsetVector(axes, x0, y0, x1, y1, x_inverted, y_inverted, xy_swap)
        vec -= offset_vector * offset

    return vec


def NormalizedSquarePatchNormal(axes,
                                u, v,
                                x0, y0, x1, y1,
                                x_inverted=False, y_inverted=False, xy_swap=False):
    (x0, y0, x1, y1, dx, dy) = convert_xy(x0, y0, x1, y1, x_inverted, y_inverted, xy_swap)

    x = x0 + u * dx
    y = y0 + v * dy
    normal = LVector3d(2.0 * x - 1.0, 2.0 * y - 1.0, 1.0)
    normal.normalize()
    normal_coefs = LVector3d(axes[1] * axes[2], axes[0] * axes[2], axes[0] * axes[1])
    normal.componentwise_mult(normal_coefs)
    normal.normalize()

    return normal


def NormalizedSquarePatchOffsetVector(axes, x0, y0, x1, y1,
                                      x_inverted=False, y_inverted=False, xy_swap=False):
    return NormalizedSquarePatchPoint(axes, 0.5, 0.5, x0, y0, x1, y1, None, x_inverted, y_inverted, xy_swap)


def NormalizedSquarePatchAABB(axes, min_height, max_height,
                              x0, y0, x1, y1, offset=None,
                              x_inverted=False, y_inverted=False, xy_swap=False):
    points = []
    if min_height != max_height:
        heights = (min_height, max_height)
    else:
        heights = (min_height,)
    if offset is not None:
        offset_vector = NormalizedSquarePatchOffsetVector(
            axes, x0, y0, x1, y1, x_inverted, y_inverted, xy_swap) * offset
    for height in heights:
        for i in (0.0, 0.5, 1.0):
            for j in (0.0, 0.5, 1.0):
                point = NormalizedSquarePatchPoint(
                    axes, i, j, x0, y0, x1, y1, None, x_inverted, y_inverted, xy_swap)
                if height != 0:
                    normal = NormalizedSquarePatchNormal(
                        axes, i, j, x0, y0, x1, y1, x_inverted, y_inverted, xy_swap)
                    point += normal * height
                if offset is not None:
                    point -= offset_vector
                points.append(point)
    x_min = min(p.get_x() for p in points)
    x_max = max(p.get_x() for p in points)
    y_min = min(p.get_y() for p in points)
    y_max = max(p.get_y() for p in points)
    z_min = min(p.get_z() for p in points)
    z_max = max(p.get_z() for p in points)
    box = BoundingBox(LPoint3(x_min, y_min, z_min), LPoint3(x_max, y_max, z_max))
    return box


@named_pstat("geom")
def RingFaceGeometry(up, inner_radius, outer_radius, nbOfPoints):
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
