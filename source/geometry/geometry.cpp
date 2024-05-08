/*
 * This file is part of Cosmonium.
 *
 * Copyright (C) 2018-2024 Laurent Deru.
 *
 * Cosmonium is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * Cosmonium is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with Cosmonium.  If not, see <http://www.gnu.org/licenses/>.
 */

#include "geometry.h"
#include "geom.h"
#include "geomNode.h"
#include "geomTriangles.h"
#include "geomVertexWriter.h"
#include "nodePath.h"
#include "internalName.h"

#include <math.h>
#include <algorithm>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

static PStatCollector _geom_collector("Engine:geom");

TessellationInfo::TessellationInfo(unsigned int inner, LVecBase4i outer) :
        inner(inner),
        outer(outer)
{
    for (unsigned int i = 0; i < 4; ++i) {
        unsigned int x = outer[i];
        ratio[i] = inner >= x ? inner / x : 1;
    }
}

UVPatchGenerator::UVPatchGenerator()
{
}

LVector3d
UVPatchGenerator::make_offset_vector(LVector3d axes, double x0, double y0, double x1, double y1)
{
    double dx = x1 - x0;
    double dy = y1 - y0;
    double x = cos(2 * M_PI * (x0 + dx / 2) + M_PI) * sin(M_PI * (y0 + dy / 2));
    double y = sin(2 * M_PI * (x0 + dx / 2) + M_PI) * sin(M_PI * (y0 + dy / 2));
    double z = -cos(M_PI * (y0 + dy / 2));
    LVector3d vector = LVector3d(x, y, z);
    vector.componentwise_mult(axes);
    return vector;
}


LVector3d
UVPatchGenerator::make_normal(LVector3d axes, double r, double s, double x0, double y0, double x1, double y1)
{
    double dx = x1 - x0;
    double dy = y1 - y0;
    double cos_s = cos(2 * M_PI * (x0 + s * dx) + M_PI);
    double sin_s = sin(2 * M_PI * (x0 + s * dx) + M_PI);
    double sin_r = sin(M_PI * (y0 + r * dy));
    double cos_r = cos(M_PI * (y0 + r * dy));
    LVector3d normal = LVector3d(
            axes[1] * axes[2] * cos_s * sin_r,
            axes[0] * axes[2] * sin_s * sin_r,
            -axes[0] * axes[1] * cos_r);
    normal.normalize();
    return normal;
}

NodePath
UVPatchGenerator::make(LVector3d axes, unsigned int rings, unsigned int sectors,
        double x0, double y0, double x1, double y1,
        bool global_texture, bool inv_texture_u, bool inv_texture_v,
        double offset)
{
    _geom_collector.start();

    unsigned int r_sectors = sectors + 1;
    unsigned int r_rings = rings + 1;

    unsigned int nb_data = r_rings * r_sectors;
    unsigned int nb_vertices = rings * sectors;

    PT(GeomNode) node = new GeomNode("uv");

    PT(GeomVertexArrayFormat) array = new GeomVertexArrayFormat();
    array->add_column(InternalName::get_vertex(), 3, Geom::NT_float32, Geom::C_point);
    array->add_column(InternalName::get_texcoord(), 2, Geom::NT_float32, Geom::C_texcoord);
    array->add_column(InternalName::get_normal(), 3, Geom::NT_float32, Geom::C_vector);
    array->add_column(InternalName::get_tangent(), 3, Geom::NT_float32, Geom::C_vector);
    array->add_column(InternalName::get_binormal(), 3, Geom::NT_float32, Geom::C_vector);
    PT(GeomVertexFormat) source_format = new GeomVertexFormat();
    source_format->add_array(array);
    CPT(GeomVertexFormat) format = GeomVertexFormat::register_format(source_format);

    PT(GeomVertexData) gvd = new GeomVertexData("gvd", format, Geom::UH_static);
    if (nb_data != 0) {
        gvd->unclean_set_num_rows(nb_data);
    }
    PT(Geom) geom = new Geom(gvd);
    GeomVertexWriter gvw = GeomVertexWriter(gvd, InternalName::get_vertex());
    GeomVertexWriter gtw = GeomVertexWriter(gvd, InternalName::get_texcoord());
    GeomVertexWriter gnw = GeomVertexWriter(gvd, InternalName::get_normal());
    GeomVertexWriter gtanw = GeomVertexWriter(gvd, InternalName::get_tangent());
    GeomVertexWriter gbiw = GeomVertexWriter(gvd, InternalName::get_binormal());
    PT(GeomTriangles) prim = new GeomTriangles(Geom::UH_static);
    if (nb_vertices != 0) {
        prim->reserve_num_vertices(nb_vertices);
    }

    double dx = x1 - x0;
    double dy = y1 - y0;

    LVector3d offset_vector;
    if (offset != 0.0) {
      offset_vector = make_offset_vector(axes, x0, y0, x1, y1) * offset;
    }

    LVector3d normal_coefs = LVector3d(axes[1] * axes[2], axes[0] * axes[2], axes[0] * axes[1]);
    for (unsigned int r = 0; r < r_rings; ++r) {
        for (unsigned s = 0; s < r_sectors; ++s) {
            double cos_s = cos(2 * M_PI * (x0 + s * dx / sectors) + M_PI);
            double sin_s = sin(2 * M_PI * (x0 + s * dx / sectors) + M_PI);
            double sin_r = sin(M_PI * (y0 + r * dy / rings));
            double cos_r = cos(M_PI * (y0 + r * dy / rings));
            LPoint3d point = LPoint3d(
                cos_s * sin_r,
                sin_s * sin_r,
                -cos_r);
            LVector3d normal(point);
            LVector3d tangent;
            if (sin_r > 0) {
                tangent = LVector3d(-axes[0] * point[1], axes[1] * point[0], 0);
            } else {
                tangent = LVector3d(-axes[0], 0, 0);
            }
            if (global_texture) {
                gtw.add_data2((x0 + s * dx / sectors), (y0 + r * dy / rings));
            } else {
                double u = double(s) / sectors;
                double v = double(r) / rings;
                if (inv_texture_v) {
                    v = 1.0 - v;
                }
                if (inv_texture_u) {
                    u = 1.0 - u;
                }
                gtw.add_data2(u, v);
            }
            point.componentwise_mult(axes);
            if (offset != 0.0) {
              point -= offset_vector;
            }
            gvw.add_data3d(point);
            normal.componentwise_mult(normal_coefs);
            normal.normalize();
            gnw.add_data3d(normal);
            tangent.normalize();
            gtanw.add_data3d(tangent);
            LVector3d binormal = normal.cross(tangent);
            binormal.normalize();
            gbiw.add_data3d(binormal);
        }
    }

    for (unsigned int r = 0; r < r_rings - 1; ++r) {
        for (unsigned int s = 0; s < r_sectors - 1; ++s) {
            prim->add_vertices(r * r_sectors + s, r * r_sectors + (s + 1), (r + 1) * r_sectors + s);
            prim->add_vertices(r * r_sectors + (s + 1), (r + 1) * r_sectors + (s + 1), (r + 1) * r_sectors + s);
        }
    }
    prim->close_primitive();
    geom->add_primitive(prim);
    node->add_geom(geom);

    _geom_collector.stop();

    return NodePath(node);
}

void
CubePatchGeneratorBase::make_primitives(PT(GeomTriangles) prim, unsigned int inner, unsigned int nb_vertices)
{
    for (unsigned int x = 0; x < inner; ++x) {
        for (unsigned int y = 0; y < inner; ++y) {
            unsigned int v = nb_vertices * x + y;
            prim->add_vertices(v, v + nb_vertices, v + 1);
            prim->add_vertices(v + 1, v + nb_vertices, v + nb_vertices + 1);
        }
    }
}

void
CubePatchGeneratorBase::make_adapted_square_primitives(PT(GeomTriangles) prim,
        unsigned int inner, unsigned int nb_vertices, LVecBase4i ratio)
{
    for (unsigned int x = 0; x < inner; ++x) {
        for (unsigned int y = 0; y < inner; ++y) {
            unsigned int v = nb_vertices * x + y;
            if (x == 0) {
                unsigned int i = 0;
                if (y == 0) {
                    unsigned int j = 1;
                    if (ratio[i] == 1 && ratio[j] == 1) {
                        prim->add_vertices(v, v + nb_vertices, v + 1);
                        prim->add_vertices(v + 1, v + nb_vertices, v + nb_vertices + 1);
                    } else {
                        prim->add_vertices(v, v + nb_vertices * ratio[j], v + nb_vertices + 1);
                        prim->add_vertices(v, v + nb_vertices + 1, v + ratio[i]);
                    }
                } else if (y == inner - 1) {
                    unsigned int j = 3;
                    if (ratio[i] == 1) {
                        prim->add_vertices(v, v + nb_vertices, v + 1);
                    }
                    prim->add_vertices(v + 1, v + nb_vertices * ratio[j], v + nb_vertices * ratio[j] + 1);
                } else {
                    unsigned int vp = nb_vertices * x + int(y / ratio[i]) * ratio[i];
                    if ((y % ratio[i]) == 0) {
                        prim->add_vertices(v, v + nb_vertices, v + ratio[i]);
                    }
                    prim->add_vertices(vp + ratio[i], v + nb_vertices, v + nb_vertices + 1);
                }
            } else if (x == inner - 1) {
                unsigned int i = 2;
                if (y == 0) {
                    unsigned int j = 1;
                    if (ratio[j] == 1) {
                        prim->add_vertices(v, v + nb_vertices, v + 1);
                    }
                    prim->add_vertices(v + ratio[i], v + nb_vertices, v + nb_vertices + ratio[i]);
                } else if (y == inner - 1) {
                    unsigned int j = 3;
                    if (ratio[i] == 1 && ratio[j] == 1) {
                        prim->add_vertices(v, v + nb_vertices, v + 1);
                        prim->add_vertices(v + 1, v + nb_vertices, v + nb_vertices + 1);
                    } else {
                        unsigned int vpx = nb_vertices * (x / ratio[j]) * ratio[j] + y;
                        prim->add_vertices(vpx + 1, v, v + nb_vertices + 1);
                        unsigned int vpy = nb_vertices * x + ((y / ratio[i]) * ratio[i]);
                        prim->add_vertices(v, vpy + nb_vertices, v + nb_vertices + 1);
                    }
                } else {
                    unsigned int vp = nb_vertices * x + ((y / ratio[i]) * ratio[i]);
                    prim->add_vertices(v, vp + nb_vertices, v + 1);
                    if (((y + 1) % ratio[i]) == 0) {
                        prim->add_vertices(v + 1, vp + nb_vertices, v + nb_vertices + 1);
                    }
                }
            } else if (y == 0) {
                unsigned int i = 1;
                unsigned int vp = nb_vertices * (x / ratio[i]) * ratio[i] + y;
                prim->add_vertices(v + 1, vp + nb_vertices * ratio[i], v + nb_vertices + 1);
                if ((x % ratio[i]) == 0) {
                    prim->add_vertices(v, v + nb_vertices * ratio[i], v + 1);
                }
            } else if (y == inner - 1) {
                unsigned int i = 3;
                unsigned int vp = nb_vertices * (x / ratio[i]) * ratio[i] + y;
                prim->add_vertices(v, v + nb_vertices, vp + 1);
                if (((x + 1) % ratio[i]) == 0) {
                    prim->add_vertices(vp + 1, v + nb_vertices, v + nb_vertices + 1);
                }
            } else {
                prim->add_vertices(v, v + nb_vertices, v + 1);
                prim->add_vertices(v + 1, v + nb_vertices, v + nb_vertices + 1);
            }
        }
    }
}

void
CubePatchGeneratorBase::make_adapted_square_primitives_skirt(PT(GeomTriangles) prim,
        unsigned int inner, unsigned int nb_vertices, LVecBase4i ratio)
{
    for (unsigned int a = 0; a < 4; ++a) {
        unsigned int start = nb_vertices * nb_vertices + a * nb_vertices;
        for (unsigned int b = 0; b < inner; ++b) {
            unsigned int skirt = start + b;
            unsigned int i, x, y;
            if (a == 0) {
                i = 0;
                x = 0;
                y = b;
            } else if (a == 1) {
                i = 2;
                x = inner - 1;
                y = b;
            } else if (a == 2) {
                i = 1;
                x = b;
                y = 0;
            } else if (a == 3) {
                i = 3;
                x = b;
                y = inner - 1;
            }
            unsigned v = nb_vertices * x + y;
            if (a == 0) {
                if ((y % ratio[i]) == 0) {
                    prim->add_vertices(v, v + ratio[i], skirt);
                    prim->add_vertices(skirt, v + ratio[i], skirt + ratio[i]);
                }
            } else if (a == 1) {
                if ((y % ratio[i]) == 0) {
                    prim->add_vertices(v + nb_vertices, skirt, v + nb_vertices + ratio[i]);
                    prim->add_vertices(v + nb_vertices + ratio[i], skirt, skirt + ratio[i]);
                }
            } else if (a == 2) {
                if ((x % ratio[i]) == 0) {
                    prim->add_vertices(v, skirt, v + nb_vertices * ratio[i]);
                    prim->add_vertices(v + nb_vertices * ratio[i], skirt, skirt + ratio[i]);
                }
            } else if (a == 3) {
                if ((x % ratio[i]) == 0) {
                    prim->add_vertices(skirt + ratio[i], v + 1, v + nb_vertices * ratio[i] + 1);
                    prim->add_vertices(skirt, v + 1, skirt + ratio[i]);
                }
            }
        }
    }
}

void
CubePatchGeneratorBase::make_primitives_skirt(PT(GeomTriangles) prim,
        unsigned int inner, unsigned int nb_vertices)
{
    for (unsigned int a = 0; a < 4; ++a) {
        unsigned int start = nb_vertices * nb_vertices + a * nb_vertices;
        for (unsigned int b = 0; b < inner; ++b) {
            unsigned int skirt = start + b;
            unsigned int i, x, y;
            if (a == 0) {
                x = 0;
                y = b;
            } else if (a == 1) {
                x = inner - 1;
                y = b;
            } else if (a == 2) {
                x = b;
                y = 0;
            } else if (a == 3) {
                x = b;
                y = inner - 1;
            }
            unsigned int v = nb_vertices * x + y;
            if (a == 0) {
                prim->add_vertices(v, v + 1, skirt);
                prim->add_vertices(skirt, v + 1, skirt + 1);
            } else if (a == 1) {
                prim->add_vertices(v + nb_vertices, skirt, v + nb_vertices + 1);
                prim->add_vertices(v + nb_vertices + 1, skirt, skirt + 1);
            } else if (a == 2) {
                prim->add_vertices(v, skirt, v + nb_vertices);
                prim->add_vertices(v + nb_vertices, skirt, skirt + 1);
            } else if (a == 3) {
                prim->add_vertices(skirt + 1, v + 1, v + nb_vertices + 1);
                prim->add_vertices(skirt, v + 1, skirt + 1);
            }
        }
    }
}

QCSPatchGenerator::QCSPatchGenerator()
{
}

LVector3d
QCSPatchGenerator::make_offset_vector(LVector3d axes,
    double x0, double y0, double x1, double y1,
    bool x_inverted, bool y_inverted, bool xy_swap)
{
  if (x_inverted) {
      double tmp = 1 - x0;
      x0 = 1 - x1;
      x1 = tmp;
  }
  if (y_inverted) {
      double tmp = 1 - y0;
      y0 = 1 - y1;
      y1 = tmp;
  }
  if (xy_swap) {
      std::swap(x0, y0);
      std::swap(x1, y1);
  }

  double dx = x1 - x0;
  double dy = y1 - y0;

  LVector3d offset_vector;
  double x = x0 + 0.5 * dx;
  double y = y0 + 0.5 * dy;
  offset_vector = LVector3d(2.0 * x - 1.0, 2.0 * y - 1.0, 1.0);
  offset_vector.normalize();
  offset_vector.componentwise_mult(axes);

  return offset_vector;
}

LVector3d
QCSPatchGenerator::make_normal(LVector3d axes,
        double u, double v, double x0, double y0, double x1, double y1,
        bool x_inverted, bool y_inverted, bool xy_swap)
{
  if (x_inverted) {
      double tmp = 1 - x0;
      x0 = 1 - x1;
      x1 = tmp;
  }
  if (y_inverted) {
      double tmp = 1 - y0;
      y0 = 1 - y1;
      y1 = tmp;
  }
  if (xy_swap) {
      std::swap(x0, y0);
      std::swap(x1, y1);
  }

  double dx = x1 - x0;
  double dy = y1 - y0;

  double x = x0 + u * dx;
  double y = y0 + v * dy;
  x = 2.0 * x - 1.0;
  y = 2.0 * y - 1.0;
  LVector3d normal(x, y, 1.0);
  normal.normalize();
  LVector3d normal_coefs = LVector3d(axes[1] * axes[2], axes[0] * axes[2], axes[0] * axes[1]);
  normal.componentwise_mult(normal_coefs);
  normal.normalize();

  return normal;
}

void
QCSPatchGenerator::make_point(LVector3d axes,
        double u, double v, double x0, double y0, double dx, double dy,
        LVector3d normal_coefs,
        bool inv_u, bool inv_v, bool swap_uv,
        bool has_offset, LVector3d offset_vector,
        GeomVertexWriter &gvw, GeomVertexWriter &gtw, GeomVertexWriter &gnw, GeomVertexWriter &gtanw,
        GeomVertexWriter &gbiw)
{
    double x = x0 + u * dx;
    double y = y0 + v * dy;
    x = 2.0 * x - 1.0;
    y = 2.0 * y - 1.0;
    LVector3d point(x, y, 1.0);
    point.normalize();
    LVector3d normal = point;
    LVector3d tangent(1.0 + y * y, -x * y, -x);

    if (inv_u) {
        u = 1.0 - u;
    }
    if (inv_v) {
        v = 1.0 - v;
    }
    if (swap_uv) {
        std::swap(u, v);
    }
    gtw.add_data2(u, v);

    point.componentwise_mult(axes);
    if (has_offset) {
        point -= offset_vector;
    }
    gvw.add_data3d(point);
    normal.componentwise_mult(normal_coefs);
    normal.normalize();
    gnw.add_data3d(normal);
    tangent.componentwise_mult(axes);
    tangent.normalize();
    LVector3d binormal = normal.cross(tangent);
    binormal.normalize();
    if (inv_u)
        tangent = -tangent;
    if (inv_v)
        binormal = -binormal;
    if (swap_uv) {
        std::swap(tangent, binormal);
    }
    gtanw.add_data3d(tangent);
    gbiw.add_data3d(binormal);
}

NodePath
QCSPatchGenerator::make(LVector3d axes, TessellationInfo tessellation,
        double x0, double y0, double x1, double y1,
        bool inv_u, bool inv_v, bool swap_uv,
        bool x_inverted, bool y_inverted, bool xy_swap,
        bool has_offset, double offset,
        bool use_patch_adaptation, bool use_patch_skirts,
        double skirt_size, double skirt_uv)
{
    _geom_collector.start();

    unsigned int nb_vertices = tessellation.inner + 1;

    unsigned int nb_prims = tessellation.inner * tessellation.inner;
    unsigned int nb_points = nb_vertices * nb_vertices;

    if (use_patch_skirts) {
        nb_points += nb_vertices * 4;
        nb_prims += tessellation.inner * 4;
    }

    PT(GeomNode) node = new GeomNode("qcs");

    PT(GeomVertexArrayFormat) array = new GeomVertexArrayFormat();
    array->add_column(InternalName::get_vertex(), 3, Geom::NT_float32, Geom::C_point);
    array->add_column(InternalName::get_texcoord(), 2, Geom::NT_float32, Geom::C_texcoord);
    array->add_column(InternalName::get_normal(), 3, Geom::NT_float32, Geom::C_vector);
    array->add_column(InternalName::get_tangent(), 3, Geom::NT_float32, Geom::C_vector);
    array->add_column(InternalName::get_binormal(), 3, Geom::NT_float32, Geom::C_vector);
    PT(GeomVertexFormat) source_format = new GeomVertexFormat();
    source_format->add_array(array);
    CPT(GeomVertexFormat) format = GeomVertexFormat::register_format(source_format);

    PT(GeomVertexData) gvd = new GeomVertexData("gvd", format, Geom::UH_static);
    if (nb_points != 0) {
        gvd->unclean_set_num_rows(nb_points);
    }
    PT(Geom) geom = new Geom(gvd);
    GeomVertexWriter gvw = GeomVertexWriter(gvd, InternalName::get_vertex());
    GeomVertexWriter gtw = GeomVertexWriter(gvd, InternalName::get_texcoord());
    GeomVertexWriter gnw = GeomVertexWriter(gvd, InternalName::get_normal());
    GeomVertexWriter gtanw = GeomVertexWriter(gvd, InternalName::get_tangent());
    GeomVertexWriter gbiw = GeomVertexWriter(gvd, InternalName::get_binormal());
    PT(GeomTriangles) prim = new GeomTriangles(Geom::UH_static);
    if (nb_prims != 0) {
        prim->reserve_num_vertices(nb_prims);
    }

    LVector3d offset_vector;
    if (has_offset) {
        offset_vector = make_offset_vector(axes, x0, y0, x1, y1, x_inverted, y_inverted, xy_swap) * offset;
    }

    if (x_inverted) {
        double tmp = 1 - x0;
        x0 = 1 - x1;
        x1 = tmp;
    }
    if (y_inverted) {
        double tmp = 1 - y0;
        y0 = 1 - y1;
        y1 = tmp;
    }
    if (xy_swap) {
        std::swap(x0, y0);
        std::swap(x1, y1);
    }

    double dx = x1 - x0;
    double dy = y1 - y0;

    LVector3d normal_coefs = LVector3d(axes[1] * axes[2], axes[0] * axes[2], axes[0] * axes[1]);
    for (unsigned int i = 0; i < nb_vertices; ++i) {
        for (unsigned int j = 0; j < nb_vertices; ++j) {
            make_point(axes,
                    double(i) / tessellation.inner, double(j) / tessellation.inner,
                    x0, y0, dx, dy,
                    normal_coefs,
                    inv_u, inv_v, swap_uv,
                    has_offset, offset_vector,
                    gvw, gtw, gnw, gtanw, gbiw);
        }
    }

    if (use_patch_skirts) {
      LVector3d reduced_axes = axes - LVector3d(std::max(dx, dy) * skirt_size);
        for (unsigned int a = 0; a < 4; ++a) {
            for (unsigned int b = 0; b < nb_vertices; ++b) {
                unsigned int i, j;
                if (a == 0) {
                    i = 0;
                    j = b;
                } else if (a == 1) {
                    i = tessellation.inner;
                    j = b;
                } else if (a == 2) {
                    i = b;
                    j = 0;
                } else if (a == 3) {
                    i = b;
                    j = tessellation.inner;
                }
                make_point(reduced_axes,
                        double(i) / tessellation.inner, double(j) / tessellation.inner,
                        x0, y0, dx, dy,
                        normal_coefs,
                        inv_u, inv_v, swap_uv,
                        has_offset, offset_vector,
                        gvw, gtw, gnw, gtanw, gbiw);
            }
        }
    }

    if (use_patch_adaptation) {
        make_adapted_square_primitives(prim, tessellation.inner, nb_vertices, tessellation.ratio);
        if (use_patch_skirts) {
            make_adapted_square_primitives_skirt(prim, tessellation.inner, nb_vertices, tessellation.ratio);
        }
    } else {
        make_primitives(prim, tessellation.inner, nb_vertices);
        if (use_patch_skirts) {
            make_primitives_skirt(prim, tessellation.inner, nb_vertices);
        }
    }

    prim->close_primitive();
    geom->add_primitive(prim);
    node->add_geom(geom);

    _geom_collector.stop();

    return NodePath(node);
}

ImprovedQCSPatchGenerator::ImprovedQCSPatchGenerator()
{
}
LVector3d
ImprovedQCSPatchGenerator::make_offset_vector(LVector3d axes,
    double x0, double y0, double x1, double y1,
    bool x_inverted, bool y_inverted, bool xy_swap)
{
    if (x_inverted) {
        double tmp = 1 - x0;
        x0 = 1 - x1;
        x1 = tmp;
    }
    if (y_inverted) {
        double tmp = 1 - y0;
        y0 = 1 - y1;
        y1 = tmp;
    }
    if (xy_swap) {
        std::swap(x0, y0);
        std::swap(x1, y1);
    }

    double dx = x1 - x0;
    double dy = y1 - y0;

    double x = x0 + 0.5 * dx;
    double y = y0 + 0.5 * dy;
    double z = 1.0;

    x = 2.0 * x - 1.0;
    y = 2.0 * y - 1.0;

    double x2 = x * x;
    double y2 = y * y;
    double z2 = z * z;

    x *= sqrt(1.0 - y2 * 0.5 - z2 * 0.5 + y2 * z2 / 3.0);
    y *= sqrt(1.0 - z2 * 0.5 - x2 * 0.5 + z2 * x2 / 3.0);
    z *= sqrt(1.0 - x2 * 0.5 - y2 * 0.5 + x2 * y2 / 3.0);
    LVector3d offset_vector = LVector3d(x, y, z);
    offset_vector.componentwise_mult(axes);
    return offset_vector;
}

LVector3d
ImprovedQCSPatchGenerator::make_normal(LVector3d axes,
        double u, double v, double x0, double y0, double x1, double y1,
        bool x_inverted, bool y_inverted, bool xy_swap)
{
    if (x_inverted) {
        double tmp = 1 - x0;
        x0 = 1 - x1;
        x1 = tmp;
    }
    if (y_inverted) {
        double tmp = 1 - y0;
        y0 = 1 - y1;
        y1 = tmp;
    }
    if (xy_swap) {
        std::swap(x0, y0);
        std::swap(x1, y1);
    }

    double dx = x1 - x0;
    double dy = y1 - y0;

    double x = x0 + u * dx;
    double y = y0 + v * dy;
    double z = 1.0;
    x = 2.0 * x - 1.0;
    y = 2.0 * y - 1.0;
    double x2 = x * x;
    double y2 = y * y;
    double z2 = z * z;
    double xp = x * sqrt(1.0 - y2 * 0.5 - z2 * 0.5 + y2 * z2 / 3.0);
    double yp = y * sqrt(1.0 - z2 * 0.5 - x2 * 0.5 + z2 * x2 / 3.0);
    double zp = z * sqrt(1.0 - x2 * 0.5 - y2 * 0.5 + x2 * y2 / 3.0);

    LVector3d normal_coefs = LVector3d(axes[1] * axes[2], axes[0] * axes[2], axes[0] * axes[1]);
    LPoint3d normal = LPoint3d(xp, yp, zp);
    normal.componentwise_mult(normal_coefs);
    normal.normalize();
    return normal;
}

void
ImprovedQCSPatchGenerator::make_point(LVector3d axes,
        double u, double v,
        double x0, double y0, double dx, double dy,
        LVector3d normal_coefs,
        bool inv_u, bool inv_v, bool swap_uv,
        bool has_offset, LVector3d offset_vector,
        GeomVertexWriter &gvw, GeomVertexWriter &gtw, GeomVertexWriter &gnw, GeomVertexWriter &gtanw,
        GeomVertexWriter &gbiw)
{
    double x = x0 + u * dx;
    double y = y0 + v * dy;
    double z = 1.0;
    x = 2.0 * x - 1.0;
    y = 2.0 * y - 1.0;
    double x2 = x * x;
    double y2 = y * y;
    double z2 = z * z;
    double xp = x * sqrt(1.0 - y2 * 0.5 - z2 * 0.5 + y2 * z2 / 3.0);
    double yp = y * sqrt(1.0 - z2 * 0.5 - x2 * 0.5 + z2 * x2 / 3.0);
    double zp = z * sqrt(1.0 - x2 * 0.5 - y2 * 0.5 + x2 * y2 / 3.0);

    LPoint3d point = LPoint3d(xp, yp, zp);
    LVector3d normal = point;
    LVector3d tangent(1.0, x * y * (z2 / 3.0 - 0.5), x * z * (y2 / 3.0 - 0.5));

    if (inv_u) {
        u = 1.0 - u;
    }
    if (inv_v) {
        v = 1.0 - v;
    }
    if (swap_uv) {
        std::swap(u, v);
    }
    gtw.add_data2(u, v);
    point.componentwise_mult(axes);
    if (has_offset) {
      point -= offset_vector;
    }
    gvw.add_data3(point);
    normal.componentwise_mult(normal_coefs);
    normal.normalize();
    gnw.add_data3d(normal);
    tangent.componentwise_mult(axes);
    tangent.normalize();
    LVector3d binormal = normal.cross(tangent);
    binormal.normalize();
    if (inv_u)
        tangent = -tangent;
    if (inv_v)
        binormal = -binormal;
    if (swap_uv) {
        std::swap(tangent, binormal);
    }
    gtanw.add_data3d(tangent);
    gbiw.add_data3d(binormal);
}

NodePath
ImprovedQCSPatchGenerator::make(LVector3d axes, TessellationInfo tessellation,
        double x0, double y0, double x1, double y1,
        bool inv_u, bool inv_v, bool swap_uv,
        bool x_inverted, bool y_inverted, bool xy_swap,
        bool has_offset, double offset,
        bool use_patch_adaptation, bool use_patch_skirts,
        double skirt_size, double skirt_uv)
{
    _geom_collector.start();

    unsigned int nb_vertices = tessellation.inner + 1;

    unsigned int nb_prims = tessellation.inner * tessellation.inner;
    unsigned int nb_points = nb_vertices * nb_vertices;

    if (use_patch_skirts) {
        nb_points += nb_vertices * 4;
        nb_prims += tessellation.inner * 4;
    }

    PT(GeomNode) node = new GeomNode("qcs");

    PT(GeomVertexArrayFormat) array = new GeomVertexArrayFormat();
    array->add_column(InternalName::get_vertex(), 3, Geom::NT_float32, Geom::C_point);
    array->add_column(InternalName::get_texcoord(), 2, Geom::NT_float32, Geom::C_texcoord);
    array->add_column(InternalName::get_normal(), 3, Geom::NT_float32, Geom::C_vector);
    array->add_column(InternalName::get_tangent(), 3, Geom::NT_float32, Geom::C_vector);
    array->add_column(InternalName::get_binormal(), 3, Geom::NT_float32, Geom::C_vector);
    PT(GeomVertexFormat) source_format = new GeomVertexFormat();
    source_format->add_array(array);
    CPT(GeomVertexFormat) format = GeomVertexFormat::register_format(source_format);

    PT(GeomVertexData) gvd = new GeomVertexData("gvd", format, Geom::UH_static);
    if (nb_points != 0) {
        gvd->unclean_set_num_rows(nb_points);
    }
    PT(Geom) geom = new Geom(gvd);
    GeomVertexWriter gvw = GeomVertexWriter(gvd, InternalName::get_vertex());
    GeomVertexWriter gtw = GeomVertexWriter(gvd, InternalName::get_texcoord());
    GeomVertexWriter gnw = GeomVertexWriter(gvd, InternalName::get_normal());
    GeomVertexWriter gtanw = GeomVertexWriter(gvd, InternalName::get_tangent());
    GeomVertexWriter gbiw = GeomVertexWriter(gvd, InternalName::get_binormal());
    PT(GeomTriangles) prim = new GeomTriangles(Geom::UH_static);
    if (nb_prims != 0) {
        prim->reserve_num_vertices(nb_prims);
    }

    LVector3d offset_vector;
    if (has_offset) {
        offset_vector = make_offset_vector(axes, x0, y0, x1, y1, x_inverted, y_inverted, xy_swap) * offset;
    }

    if (x_inverted) {
        double tmp = 1 - x0;
        x0 = 1 - x1;
        x1 = tmp;
    }
    if (y_inverted) {
        double tmp = 1 - y0;
        y0 = 1 - y1;
        y1 = tmp;
    }
    if (xy_swap) {
        std::swap(x0, y0);
        std::swap(x1, y1);
    }

    double dx = x1 - x0;
    double dy = y1 - y0;

    LVector3d normal_coefs = LVector3d(axes[1] * axes[2], axes[0] * axes[2], axes[0] * axes[1]);
    for (unsigned int i = 0; i < nb_vertices; ++i) {
        for (unsigned int j = 0; j < nb_vertices; ++j) {
            make_point(axes,
                    double(i) / tessellation.inner, double(j) / tessellation.inner,
                    x0, y0, dx, dy,
                    normal_coefs,
                    inv_u, inv_v, swap_uv,
                    has_offset, offset_vector,
                    gvw, gtw, gnw, gtanw, gbiw);
        }
    }

    if (use_patch_skirts) {
        LVector3d reduced_axes = axes - LVector3d(std::max(dx, dy) * skirt_size);
        LVector3d reduced_normal_coefs = LVector3d(
                reduced_axes[1] * reduced_axes[2],
                reduced_axes[0] * reduced_axes[2],
                reduced_axes[0] * reduced_axes[1]);
        for (unsigned int a = 0; a < 4; ++a) {
            for (unsigned int b = 0; b < nb_vertices; ++b) {
                unsigned int i, j;
                if (a == 0) {
                    i = 0;
                    j = b;
                } else if (a == 1) {
                    i = tessellation.inner;
                    j = b;
                } else if (a == 2) {
                    i = b;
                    j = 0;
                } else if (a == 3) {
                    i = b;
                    j = tessellation.inner;
                }
                make_point(reduced_axes,
                        double(i) / tessellation.inner, double(j) / tessellation.inner,
                        x0, y0, dx, dy,
                        reduced_normal_coefs,
                        inv_u, inv_v, swap_uv,
                        has_offset, offset_vector,
                        gvw, gtw, gnw, gtanw, gbiw);
            }
        }
    }

    if (use_patch_adaptation) {
        make_adapted_square_primitives(prim, tessellation.inner, nb_vertices, tessellation.ratio);
        if (use_patch_skirts) {
            make_adapted_square_primitives_skirt(prim, tessellation.inner, nb_vertices, tessellation.ratio);
        }
    } else {
        make_primitives(prim, tessellation.inner, nb_vertices);
        if (use_patch_skirts) {
            make_primitives_skirt(prim, tessellation.inner, nb_vertices);
        }
    }

    prim->close_primitive();
    geom->add_primitive(prim);
    node->add_geom(geom);

    _geom_collector.stop();

    return NodePath(node);
}

TilePatchGenerator::TilePatchGenerator()
{
}

void
TilePatchGenerator::make_point(double size,
        double u, double v,
        double x, double y, double z,
        bool inv_u, bool inv_v, bool swap_uv,
        GeomVertexWriter &gvw, GeomVertexWriter &gtw, GeomVertexWriter &gnw,
        GeomVertexWriter &gtanw, GeomVertexWriter &gbiw)
{
    if (inv_u) {
        u = 1.0 - u;
    }
    if (inv_v) {
        v = 1.0 - v;
    }
    if (swap_uv) {
        std::swap(u, v);
    }
    gtw.add_data2(u, v);
    gvw.add_data3(x * size, y * size, z * size);

    gnw.add_data3(0, 0, 1.0);
    LVector3d tan(1, 0, 0);
    LVector3d bin(0, 1, 0);
    if (inv_u)
        tan = -tan;
    if (inv_v)
        bin = -bin;
    if (swap_uv) {
        std::swap(tan, bin);
    }
    gtanw.add_data3d(tan);
    gbiw.add_data3d(bin);
}

NodePath
TilePatchGenerator::make(double size, TessellationInfo tessellation,
        bool inv_u, bool inv_v, bool swap_uv,
        bool use_patch_adaptation, bool use_patch_skirts,
        double skirt_size, double skirt_uv)
{
    _geom_collector.start();

    unsigned int nb_vertices = tessellation.inner + 1;

    unsigned int nb_prims = tessellation.inner * tessellation.inner;
    unsigned int nb_points = nb_vertices * nb_vertices;

    if (use_patch_skirts) {
        nb_points += nb_vertices * 4;
        nb_prims += tessellation.inner * 4;
    }

    PT(GeomNode) node = new GeomNode("qcs");

    PT(GeomVertexArrayFormat) array = new GeomVertexArrayFormat();
    array->add_column(InternalName::get_vertex(), 3, Geom::NT_float32, Geom::C_point);
    array->add_column(InternalName::get_texcoord(), 2, Geom::NT_float32, Geom::C_texcoord);
    array->add_column(InternalName::get_normal(), 3, Geom::NT_float32, Geom::C_vector);
    array->add_column(InternalName::get_tangent(), 3, Geom::NT_float32, Geom::C_vector);
    array->add_column(InternalName::get_binormal(), 3, Geom::NT_float32, Geom::C_vector);
    PT(GeomVertexFormat) source_format = new GeomVertexFormat();
    source_format->add_array(array);
    CPT(GeomVertexFormat) format = GeomVertexFormat::register_format(source_format);

    PT(GeomVertexData) gvd = new GeomVertexData("gvd", format, Geom::UH_static);
    if (nb_points != 0) {
        gvd->unclean_set_num_rows(nb_points);
    }
    PT(Geom) geom = new Geom(gvd);
    GeomVertexWriter gvw = GeomVertexWriter(gvd, InternalName::get_vertex());
    GeomVertexWriter gtw = GeomVertexWriter(gvd, InternalName::get_texcoord());
    GeomVertexWriter gnw = GeomVertexWriter(gvd, InternalName::get_normal());
    GeomVertexWriter gtanw = GeomVertexWriter(gvd, InternalName::get_tangent());
    GeomVertexWriter gbiw = GeomVertexWriter(gvd, InternalName::get_binormal());
    PT(GeomTriangles) prim = new GeomTriangles(Geom::UH_static);
    if (nb_prims != 0) {
        prim->reserve_num_vertices(nb_prims);
    }

    for (unsigned int i = 0; i < nb_vertices; ++i) {
        double u = float(i) / tessellation.inner;
        for (unsigned int j = 0; j < nb_vertices; ++j) {
            double v = float(j) / tessellation.inner;
            make_point(size,
                    u, v,
                    u, v, 0,
                    inv_u, inv_v, swap_uv,
                    gvw, gtw, gnw, gtanw, gbiw);
        }
    }

    if (use_patch_skirts) {
        for (unsigned int a = 0; a < 4; ++a) {
            for (unsigned int b = 0; b < nb_vertices; ++b) {
                double x, y;
                double u, v;
                if (a == 0) {
                    x = 0.0;
                    y = float(b) / tessellation.inner;
                    u = -skirt_uv;
                    v = y;
                } else if (a == 1) {
                    x = 1.0;
                    y = float(b) / tessellation.inner;
                    u = 1.0 + skirt_uv;
                    v = y;
                } else if (a == 2) {
                    x = float(b) / tessellation.inner;
                    y = 0.0;
                    u = x;
                    v = -skirt_uv;
                } else if (a == 3) {
                    x = float(b) / tessellation.inner;
                    y = 1.0;
                    u = x;
                    v = 1.0 + skirt_uv;
                }
                make_point(size,
                        u, v,
                        x, y, -skirt_size,
                        inv_u, inv_v, swap_uv,
                        gvw, gtw, gnw, gtanw, gbiw);
            }
        }
    }

    if (use_patch_adaptation) {
        make_adapted_square_primitives(prim, tessellation.inner, nb_vertices, tessellation.ratio);
        if (use_patch_skirts) {
            make_adapted_square_primitives_skirt(prim, tessellation.inner, nb_vertices, tessellation.ratio);
        }
    } else {
        make_primitives(prim, tessellation.inner, nb_vertices);
        if (use_patch_skirts) {
            make_primitives_skirt(prim, tessellation.inner, nb_vertices);
        }
    }

    prim->close_primitive();
    geom->add_primitive(prim);
    node->add_geom(geom);

    _geom_collector.stop();

    return NodePath(node);
}
