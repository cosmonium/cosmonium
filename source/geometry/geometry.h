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

#ifndef GEOMETRY_H
#define GEOMETRY_H

#include "pandabase.h"
#include "luse.h"

#include "nodePath.h"

class GeomVertexWriter;

class TesselationInfo
{
PUBLISHED:
  TesselationInfo(unsigned int inner, LVecBase4i outer);

  unsigned int inner;
  LVecBase4i outer;
  LVecBase4i ratio;
};

class UVPatchGenerator
{
PUBLISHED:
  UVPatchGenerator();

  LVector3d
  make_normal(double x0, double y0, double x1, double y1);

  NodePath
  make(double radius, unsigned int rings, unsigned int sectors,
      double x0, double y0, double x1, double y1,
      bool global_texture=false, bool inv_texture_u=false, bool inv_texture_v=false,
      bool has_offset=false, double offset=0.0);
};

class CubePatchGeneratorBase
{
protected:
  void
  make_adapted_square_primitives(PT(GeomTriangles) prim,
      unsigned int inner, unsigned int nb_vertices, LVecBase4i ratio);

  void
  make_adapted_square_primitives_skirt(PT(GeomTriangles) prim,
      unsigned int inner, unsigned int nb_vertices, LVecBase4i ratio);

  void
  make_primitives(PT(GeomTriangles) prim, unsigned int inner, unsigned int nb_vertices);

  void
  make_primitives_skirt(PT(GeomTriangles) prim, unsigned int inner, unsigned int nb_vertices);
};

class QCSPatchGenerator : public CubePatchGeneratorBase
{
PUBLISHED:
  QCSPatchGenerator();

  NodePath
  make(double radius, TesselationInfo tesselation,
      double x0, double y0, double x1, double y1,
      bool inv_u=false, bool inv_v=false, bool swap_uv=false,
      bool x_inverted=false, bool y_inverted=false, bool xy_swap=false,
      bool has_offset=false, double offset=0.0,
      bool use_patch_adaptation=true, bool use_patch_skirts=true,
      double skirt_size=0.001, double skirt_uv=0.001);

private:
  inline void
  make_point(double radius, unsigned int inner, LVector3d patch_normal,
      unsigned int i, unsigned int j, double x0, double y0, double x1, double y1,
      bool inv_u, bool inv_v, bool swap_uv,
      bool has_offset, double offset,
      GeomVertexWriter &gvw, GeomVertexWriter &gtw, GeomVertexWriter &gnw,
      GeomVertexWriter &gtanw, GeomVertexWriter &gbiw);
};

class ImprovedQCSPatchGenerator : public CubePatchGeneratorBase
{
PUBLISHED:
  ImprovedQCSPatchGenerator();

  NodePath
  make(double radius, TesselationInfo tesselation,
      double x0, double y0, double x1, double y1,
      bool inv_u=false, bool inv_v=false, bool swap_uv=false,
      bool x_inverted=false, bool y_inverted=false, bool xy_swap=false,
      bool has_offset=false, double offset=0.0,
      bool use_patch_adaptation=true, bool use_patch_skirts=true,
      double skirt_size=0.001, double skirt_uv=0.001);

private:
  inline void
  make_point(double radius, unsigned int inner, LVector3d patch_normal,
      unsigned int i, unsigned int j, double x0, double y0, double x1, double y1,
      bool inv_u, bool inv_v, bool swap_uv,
      bool has_offset, double offset,
      GeomVertexWriter &gvw, GeomVertexWriter &gtw, GeomVertexWriter &gnw,
      GeomVertexWriter &gtanw, GeomVertexWriter &gbiw);
};

class TilePatchGenerator :  public CubePatchGeneratorBase
{
PUBLISHED:
  TilePatchGenerator();

  NodePath
  make(double size, TesselationInfo tesselation,
      bool inv_u=false, bool inv_v=false, bool swap_uv=false,
      bool use_patch_adaptation=true, bool use_patch_skirts=true,
      double skirt_size=0.1, double skirt_uv=0.1);

private:
  inline void
  make_point(double size,
      double u, double v,
      double x, double y, double z,
      bool inv_u, bool inv_v, bool swap_uv,
      GeomVertexWriter &gvw, GeomVertexWriter &gtw, GeomVertexWriter &gnw,
      GeomVertexWriter &gtanw, GeomVertexWriter &gbiw);
};

#endif // GEOMETRY_H
