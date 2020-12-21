/*
 * This file is part of Cosmonium.
 *
 * Copyright (C) 2018-2020 Laurent Deru.
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

TesselationInfo::TesselationInfo(unsigned int inner, LVecBase4i outer) :
  inner(inner),
  outer(outer)
{
  for (unsigned int i = 0; i < 4; ++i) {
    int x = outer[i];
    ratio[i] = inner >= x ? inner / x  : 1;
  }
}

UVPatchGenerator::UVPatchGenerator()
{
}

LVector3d
UVPatchGenerator::make_normal(double x0, double y0, double x1, double y1)
{
    double dx = x1 - x0;
    double dy = y1 - y0;
    double x = cos(2*M_PI * (x0 + dx / 2) + M_PI) * sin(M_PI * (y0 + dy / 2));
    double y = sin(2*M_PI * (x0 + dx / 2) + M_PI) * sin(M_PI * (y0 + dy / 2));
    double z = -cos(M_PI * (y0 + dy / 2));
    return LVector3d(x, y, z);
}

NodePath
UVPatchGenerator::make(double radius, unsigned int rings, unsigned int sectors,
      double x0, double y0, double x1, double y1,
      bool global_texture, bool inv_texture_u, bool inv_texture_v,
      bool has_offset, double offset)
{
    int r_sectors = sectors + 1;
    int r_rings = rings + 1;

    int nb_data = r_rings * r_sectors;
    int nb_vertices = rings * sectors;

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

    LVector3d normal;
    if (has_offset) {
        normal = make_normal(x0, y0, x1, y1);
    }

    for (unsigned int r = 0; r < r_rings; ++r) {
        for (unsigned s = 0; s < r_sectors; ++s) {
            double cos_s = cos(2*M_PI * (x0 + s * dx / sectors) + M_PI);
            double sin_s = sin(2*M_PI * (x0 + s * dx / sectors) + M_PI);
            double sin_r = sin(M_PI * (y0 + r * dy / rings));
            double cos_r = cos(M_PI * (y0 + r * dy / rings));
            double x = cos_s * sin_r;
            double y = sin_s * sin_r;
            double z = -cos_r;
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
            if (has_offset) {
                gvw.add_data3(x * radius - normal[0] * offset,
                              y * radius - normal[1] * offset,
                              z * radius - normal[2] * offset);
            } else {
                gvw.add_data3(x * radius, y * radius, z * radius);
            }
            gnw.add_data3(x, y, z);
            // Derivation wrt s and normalization (sin_r is dropped)
            gtanw.add_data3(-sin_s, cos_s, 0); // -y, x, 0
            // Derivation wrt r
            LVector3d binormal(cos_s * cos_r, sin_s * cos_r, sin_r);
            binormal.normalize();
            gbiw.add_data3d(binormal);
        }
    }

    for (unsigned int r = 0; r < r_rings - 1; ++r) {
        for (unsigned int s = 0; s < r_sectors - 1; ++s) {
            prim->add_vertices(r * r_sectors + s, r * r_sectors + (s+1), (r+1) * r_sectors + s);
            prim->add_vertices(r * r_sectors + (s+1), (r+1) * r_sectors + (s+1), (r+1) * r_sectors + s);
        }
    }
    prim->close_primitive();
    geom->add_primitive(prim);
    node->add_geom(geom);
    return NodePath(node);
}

void
CubePatchGeneratorBase::make_primitives(PT(GeomTriangles) prim, unsigned int inner, unsigned int nb_vertices)
{
    for (unsigned int x = 0; x < inner; ++x) {
        for (unsigned int y = 0; y < inner; ++y) {
            unsigned int v = nb_vertices * y + x;
            prim->add_vertices(v, v + nb_vertices, v + 1);
            prim->add_vertices(v + 1, v + nb_vertices, v + nb_vertices + 1);
        }
    }
}

void
CubePatchGeneratorBase::make_adapted_square_primitives(PT(GeomTriangles) prim,
    unsigned int inner, unsigned int nb_vertices, LVecBase4i ratio)
{
  unsigned int i, v, vp;
  for (unsigned int x = 0; x < inner; ++x) {
      for (unsigned int y = 0; y < inner; ++y) {
          if (x == 0) {
              if (y == 0) {
                  i = 0;
                  v = nb_vertices * y + x;
                  vp = nb_vertices * y + (x / ratio[i]) * ratio[i];
                  if ((x % ratio[i]) == 0) {
                      prim->add_vertices(v, v + nb_vertices + ratio[i], v + ratio[i]);
                  }
                  prim->add_vertices(vp, v + nb_vertices, v + nb_vertices + 1);
                  i = 1;
                  v = nb_vertices * y + x;
                  vp = nb_vertices * (y / ratio[i]) * ratio[i] + x;
                  if ((y % ratio[i]) == 0) {
                      prim->add_vertices(v, v + nb_vertices * ratio[i], v + 1);
                  }
                  prim->add_vertices(v + 1, vp + nb_vertices * ratio[i], v + nb_vertices + 1);
              } else if (y == inner - 1) {
                  i = 1;
                  v = nb_vertices * y + x;
                  if ((y % ratio[i]) == 0) {
                      prim->add_vertices(v, v + nb_vertices * ratio[i], v + 1);
                  }
                  i = 2;
                  v = nb_vertices * y + x;
                  vp = nb_vertices * y + (x / ratio[i]) * ratio[i];
                  prim->add_vertices(vp + ratio[i], v + nb_vertices, v + nb_vertices + ratio[i]);
              } else {
                  i = 1;
                  v = nb_vertices * y + x;
                  vp = nb_vertices * (y / ratio[i]) * ratio[i] + x;
                  if ((y % ratio[i]) == 0) {
                      prim->add_vertices(v, v + nb_vertices * ratio[i], v + 1);
                  }
                  prim->add_vertices(v + 1, vp + nb_vertices * ratio[i], v + nb_vertices + 1);
              }
          } else if (x == inner - 1) {
              if (y == 0) {
                  i = 0;
                  v = nb_vertices * y + x;
                  vp = nb_vertices * y + (x / ratio[i]) * ratio[i];
                  if ((x % ratio[i]) == 0) {
                      prim->add_vertices(v, v + nb_vertices + ratio[i], v + ratio[i]);
                  }
                  prim->add_vertices(vp, v + nb_vertices, v + nb_vertices + 1);
                  i = 3;
                  v = nb_vertices * y + x;
                  vp = nb_vertices * ((y / ratio[i]) * ratio[i]) + x;
                  prim->add_vertices(v, v + nb_vertices, vp + 1);
                  if ((y % ratio[i]) == 0) {
                      prim->add_vertices(v + 1, v + nb_vertices * ratio[i], v + nb_vertices * ratio[i] + 1);
                  }
              } else if (y == inner - 1) {
                  i = 2;
                  v = nb_vertices * y + x;
                  vp = nb_vertices * y + (x / ratio[i]) * ratio[i];
                  prim->add_vertices(v, vp + nb_vertices, v + 1);
                  if ((x % ratio[i]) == 0) {
                      prim->add_vertices(vp + ratio[i], v + nb_vertices, v + nb_vertices + ratio[i]);
                  }
                  i = 3;
                  v = nb_vertices * y + x;
                  vp = nb_vertices * ((y / ratio[i]) * ratio[i]) + x;
                  prim->add_vertices(v, v + nb_vertices, vp + 1);
                  if ((y % ratio[i]) == 0) {
                      prim->add_vertices(v + 1, v + nb_vertices * ratio[i], v + nb_vertices * ratio[i] + 1);
                  }
              } else {
                  i = 3;
                  v = nb_vertices * y + x;
                  vp = nb_vertices * ((y / ratio[i]) * ratio[i]) + x;
                  prim->add_vertices(v, v + nb_vertices, vp + 1);
                  if ((y % ratio[i]) == 0) {
                      prim->add_vertices(v + 1, v + nb_vertices * ratio[i], v + nb_vertices * ratio[i] + 1);
                  }
              }
          } else if (y == 0) {
              i = 0;
              v = nb_vertices * y + x;
              vp = nb_vertices * y + (x / ratio[i]) * ratio[i];
              if ((x % ratio[i]) == 0) {
                  prim->add_vertices(v, v + nb_vertices + ratio[i], v + ratio[i]);
              }
              prim->add_vertices(vp, v + nb_vertices, v + nb_vertices + 1);
          } else if (y == inner - 1) {
              i = 2;
              v = nb_vertices * y + x;
              vp = nb_vertices * y + (x / ratio[i]) * ratio[i];
              prim->add_vertices(v, vp + nb_vertices, v + 1);
              if ((x % ratio[i]) == 0) {
                  prim->add_vertices(vp + ratio[i], v + nb_vertices, v + nb_vertices + ratio[i]);
              }
          } else {
              v = nb_vertices * y + x;
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
                i = 1;
                x = 0;
                y = b;
            } else if (a == 1) {
                i = 3;
                x = inner - 1;
                y = b;
            } else if (a == 2) {
                i = 0;
                x = b;
                y = 0;
            } else if (a == 3) {
                i = 2;
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

void
QCSPatchGenerator::make_point(double radius, unsigned int inner, LVector3d patch_normal,
    unsigned int i, unsigned int j, double x0, double y0, double dx, double dy,
    bool inv_u, bool inv_v, bool swap_uv,
    bool has_offset, double offset,
    GeomVertexWriter &gvw, GeomVertexWriter &gtw, GeomVertexWriter &gnw, GeomVertexWriter &gtanw, GeomVertexWriter &gbiw)
{
  double x = x0 + i * dx / inner;
  double y = y0 + j * dy / inner;
  x = 2.0 * x - 1.0;
  y = 2.0 * y - 1.0;
  LVector3d vec(x, y, 1.0);
  vec.normalize();
  LVector3d nvec = vec;

  double u = double(i) / inner;
  double v = double(j) / inner;
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
  vec = vec * radius;
  if (has_offset) {
      vec = vec - patch_normal * offset;
  }
  gvw.add_data3d(vec);
  gnw.add_data3d(nvec);
  LVector3d tan(1.0 + y*y, -x*y, -x);
  tan.normalize();
  LVector3d bin(x * y, 1.0 + x*x, -y);
  bin.normalize();
  if (inv_u) tan = -tan;
  if (inv_v) bin = -bin;
  if (swap_uv) {
    std::swap(tan, bin);
  }
  gtanw.add_data3d(tan);
  gbiw.add_data3d(bin);
}

NodePath
QCSPatchGenerator::make(double radius, TesselationInfo tesselation,
    double x0, double y0, double x1, double y1,
    bool inv_u, bool inv_v, bool swap_uv,
    bool x_inverted, bool y_inverted, bool xy_swap,
    bool has_offset, double offset,
    bool use_patch_adaptation, bool use_patch_skirts)
{
  unsigned int nb_vertices = tesselation.inner + 1;

  unsigned int nb_prims = tesselation.inner * tesselation.inner;
  unsigned int nb_points = nb_vertices * nb_vertices;

  if (use_patch_skirts) {
      nb_points += nb_vertices * 4;
      nb_prims += tesselation.inner * 4;
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

  LVector3d normal;
  if (has_offset) {
      double x = x0 + 0.5 * dx;
      double y = y0 + 0.5 * dy;
      normal = LVector3d(2.0 * x - 1.0, 2.0 * y - 1.0, 1.0);
      normal.normalize();
  }

  for (unsigned int i = 0; i < nb_vertices; ++i) {
      for (unsigned int j = 0; j < nb_vertices; ++j) {
        make_point(radius, tesselation.inner, normal,
            i, j, x0, y0, dx, dy,
            inv_u, inv_v, swap_uv,
            has_offset, offset,
            gvw, gtw, gnw, gtanw, gbiw);
      }
  }

  if (use_patch_skirts) {
      if (!has_offset) {
          has_offset = true;
          offset = 0;
      }
      offset = offset + sqrt(dx * dx + dy * dy) / tesselation.inner;
      for (unsigned int a = 0; a < 4; ++a) {
          for (unsigned int b = 0; b < nb_vertices; ++b) {
              unsigned int i, j;
              if (a == 0) {
                  i = 0;
                  j = b;
              } else if (a == 1) {
                  i = tesselation.inner;
                  j = b;
              } else if (a == 2) {
                  i = b;
                  j = 0;
              } else if (a == 3) {
                  i = b;
                  j = tesselation.inner;
              }
              make_point(radius, tesselation.inner, normal,
                  i, j, x0, y0, dx, dy,
                  inv_u, inv_v, swap_uv,
                  has_offset, offset,
                  gvw, gtw, gnw, gtanw, gbiw);
            }
        }
  }

  if (use_patch_adaptation) {
    make_adapted_square_primitives(prim, tesselation.inner, nb_vertices, tesselation.ratio);
    if (use_patch_skirts) {
      make_adapted_square_primitives_skirt(prim, tesselation.inner, nb_vertices, tesselation.ratio);
    }
  } else {
    make_primitives(prim, tesselation.inner, nb_vertices);
    if (use_patch_skirts) {
      make_primitives_skirt(prim, tesselation.inner, nb_vertices);
    }
  }

  prim->close_primitive();
  geom->add_primitive(prim);
  node->add_geom(geom);
  return NodePath(node);
}

ImprovedQCSPatchGenerator::ImprovedQCSPatchGenerator()
{
}

void
ImprovedQCSPatchGenerator::make_point(double radius, unsigned int inner, LVector3d patch_normal,
    unsigned int i, unsigned int j, double x0, double y0, double dx, double dy,
    bool inv_u, bool inv_v, bool swap_uv,
    bool has_offset, double offset,
    GeomVertexWriter &gvw, GeomVertexWriter &gtw, GeomVertexWriter &gnw, GeomVertexWriter &gtanw, GeomVertexWriter &gbiw)
{
  double x = x0 + i * dx / inner;
  double y = y0 + j * dy / inner;
  double z = 1.0;
  x = 2.0 * x - 1.0;
  y = 2.0 * y - 1.0;
  double x2 = x * x;
  double y2 = y * y;
  double z2 = z * z;
  double xp = x * sqrt(1.0 - y2 * 0.5 - z2 * 0.5 + y2 * z2 / 3.0);
  double yp = y * sqrt(1.0 - z2 * 0.5 - x2 * 0.5 + z2 * x2 / 3.0);
  double zp = z * sqrt(1.0 - x2 * 0.5 - y2 * 0.5 + x2 * y2 / 3.0);

  double u = double(i) / inner;
  double v = double(j) / inner;
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
  if (has_offset) {
    gvw.add_data3(xp * radius - patch_normal[0] * offset,
                  yp * radius - patch_normal[1] * offset,
                  zp * radius - patch_normal[2] * offset);
  } else {
    gvw.add_data3(xp * radius, yp * radius, zp * radius);
  }
  gnw.add_data3(xp, yp, zp);
  LVector3d tan(1.0, x * y * (z2 / 3.0 - 0.5), x * z * (y2 / 3.0 - 0.5));
  tan.normalize();
  LVector3d bin(x * y * (z2 / 3.0 - 0.5), 1.0, y * z * (x2 / 3.0 - 0.5));
  bin.normalize();
  if (inv_u) tan = -tan;
  if (inv_v) bin = -bin;
  if (swap_uv) {
    std::swap(tan, bin);
  }
  gtanw.add_data3d(tan);
  gbiw.add_data3d(bin);
}

NodePath
ImprovedQCSPatchGenerator::make(double radius, TesselationInfo tesselation,
    double x0, double y0, double x1, double y1,
    bool inv_u, bool inv_v, bool swap_uv,
    bool x_inverted, bool y_inverted, bool xy_swap,
    bool has_offset, double offset,
    bool use_patch_adaptation, bool use_patch_skirts)
{
  unsigned int nb_vertices = tesselation.inner + 1;

  unsigned int nb_prims = tesselation.inner * tesselation.inner;
  unsigned int nb_points = nb_vertices * nb_vertices;

  if (use_patch_skirts) {
      nb_points += nb_vertices * 4;
      nb_prims += tesselation.inner * 4;
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

  LVector3d normal;
  if (has_offset) {
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
    normal = LVector3d(x, y, z);
    normal.normalize();
  }

  for (unsigned int i = 0; i < nb_vertices; ++i) {
      for (unsigned int j = 0; j < nb_vertices; ++j) {
        make_point(radius, tesselation.inner, normal,
            i, j, x0, y0, dx, dy,
            inv_u, inv_v, swap_uv,
            has_offset, offset,
            gvw, gtw, gnw, gtanw, gbiw);
      }
  }

  if (use_patch_skirts) {
      if (!has_offset) {
          has_offset = true;
          offset = 0;
      }
      offset = offset + sqrt(dx * dx + dy * dy) / tesselation.inner;
      for (unsigned int a = 0; a < 4; ++a) {
          for (unsigned int b = 0; b < nb_vertices; ++b) {
              unsigned int i, j;
              if (a == 0) {
                  i = 0;
                  j = b;
              } else if (a == 1) {
                  i = tesselation.inner;
                  j = b;
              } else if (a == 2) {
                  i = b;
                  j = 0;
              } else if (a == 3) {
                  i = b;
                  j = tesselation.inner;
              }
              make_point(radius, tesselation.inner, normal,
                  i, j, x0, y0, dx, dy,
                  inv_u, inv_v, swap_uv,
                  has_offset, offset,
                  gvw, gtw, gnw, gtanw, gbiw);
            }
        }
  }

  if (use_patch_adaptation) {
    make_adapted_square_primitives(prim, tesselation.inner, nb_vertices, tesselation.ratio);
    if (use_patch_skirts) {
      make_adapted_square_primitives_skirt(prim, tesselation.inner, nb_vertices, tesselation.ratio);
    }
  } else {
    make_primitives(prim, tesselation.inner, nb_vertices);
    if (use_patch_skirts) {
      make_primitives_skirt(prim, tesselation.inner, nb_vertices);
    }
  }

  prim->close_primitive();
  geom->add_primitive(prim);
  node->add_geom(geom);
  return NodePath(node);
}
