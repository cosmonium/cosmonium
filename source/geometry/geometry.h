/*
 * This file is part of Cosmonium.
 *
 * Copyright (C) 2018-2026 Laurent Deru.
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

/**
 * @brief Stores tessellation configuration for adaptive mesh generation.
 *
 * TessellationInfo contains parameters for controlling the density and
 * adaptivity of mesh tessellation. It supports adaptive subdivision where
 * different edges of a patch can have different tessellation densities for
 * smooth LOD transitions.
 */
class TessellationInfo
{
PUBLISHED:
  /**
   * @brief Constructs tessellation configuration.
   *
   * @param inner Number of inner subdivisions (uniform tessellation density)
   * @param outer Four outer edge tessellation densities for adaptive LOD
   */
  TessellationInfo(unsigned int inner, LVecBase4i outer);

  unsigned int inner;  // Inner tessellation density (uniform)
  LVecBase4i outer;    // Outer edge tessellation densities (adaptive)
  LVecBase4i ratio;    // Computed tessellation ratios for edge transitions
};

/**
 * @brief Generates UV-mapped spherical patch geometry.
 *
 * UVPatchGenerator creates spherical surface patches using UV
 * (latitude/longitude) parameterization. These patches are used for
 * planetary surface rendering with LOD management. The generator
 * produces geometry with positions, normals, texture coordinates,
 * tangents, and binormals.
 *
 * Coordinate system:
 * - U (x): Longitude (0 to 1 maps to 0 to 360 degrees)
 * - V (y): Latitude (0 to 1 maps to 90N to 90S)
 */
class UVPatchGenerator
{
PUBLISHED:
  /**
   * @brief Constructs a UV patch generator.
   */
  UVPatchGenerator();

  /**
   * @brief Calculates the offset vector for a patch.
   *
   * The offset vector points from the origin to the center of the patch.
   *
   * @param axes Semi-axes of the ellipsoid (rx, ry, rz)
   * @param x0 Minimum U coordinate (longitude, 0-1 range)
   * @param y0 Minimum V coordinate (latitude, 0-1 range)
   * @param x1 Maximum U coordinate (longitude, 0-1 range)
   * @param y1 Maximum V coordinate (latitude, 0-1 range)
   * @return Offset vector from origin to patch center
   */
  LVector3d
  make_offset_vector(LVector3d axes, double x0, double y0, double x1, double y1);

  /**
   * @brief Calculates the normal vector at a point on a UV patch.
   *
   * @param axes Semi-axes of the ellipsoid (rx, ry, rz)
   * @param r Parametric coordinate in latitude direction (0-1 within patch)
   * @param s Parametric coordinate in longitude direction (0-1 within patch)
   * @param x0 Minimum U coordinate of patch (0-1)
   * @param y0 Minimum V coordinate of patch (0-1)
   * @param x1 Maximum U coordinate of patch (0-1)
   * @param y1 Maximum V coordinate of patch (0-1)
   * @return Normalized normal vector pointing outward from surface
   */
  LVector3d
  make_normal(LVector3d axes, double r, double s, double x0, double y0, double x1, double y1);

  /**
   * @brief Generates a UV patch mesh.
   *
   * Creates a rectangular patch on a spherical/ellipsoidal surface with
   * the specified tessellation density. The patch can be textured globally
   * (UV coordinates map to entire sphere) or locally (UV coordinates map
   * to patch only).
   *
   * @param axes Semi-axes of the ellipsoid (rx, ry, rz)
   * @param rings Number of latitude subdivisions
   * @param sectors Number of longitude subdivisions
   * @param x0 Minimum U coordinate (longitude, 0-1)
   * @param y0 Minimum V coordinate (latitude, 0-1)
   * @param x1 Maximum U coordinate (longitude, 0-1)
   * @param y1 Maximum V coordinate (latitude, 0-1)
   * @param global_texture If true, texture coordinates map to global sphere
   * @param inv_texture_u If true, invert U texture coordinates
   * @param inv_texture_v If true, invert V texture coordinates
   * @param offset Offset distance from surface
   * @param use_patch_skirts If true, generate edge skirts
   * @param skirt_size Size of edge skirts (as fraction of patch size)
   * @param skirt_uv UV offset for skirt texture coordinates
   * @return NodePath containing the generated patch geometry
   */
  NodePath
  make(LVector3d axes, unsigned int rings, unsigned int sectors,
      double x0, double y0, double x1, double y1,
      bool global_texture=false, bool inv_texture_u=false, bool inv_texture_v=false,
      double offset=0.0, bool use_patch_skirts=true, double skirt_size=0.001, double skirt_uv=0.001);
};

/**
 * @brief Base class for cube-mapped patch generators.
 *
 * CubePatchGeneratorBase provides template methods for generating
 * triangle primitives with adaptive tessellation and edge skirts.
 * These methods are used by derived classes (QCSPatchGenerator,
 * ImprovedQCSPatchGenerator, TilePatchGenerator) to create cube-mapped
 * patches for planetary rendering.
 *
 * The class supports:
 * - Uniform square tessellation
 * - Adaptive tessellation with different edge densities (for LOD transitions)
 * - Edge skirts (to hide cracks between LOD levels)
 */
class CubePatchGeneratorBase
{
protected:
  /**
   * @brief Generates adaptive triangle primitives for a square patch.
   *
   * Creates a triangulated mesh with potentially different tessellation
   * densities on each edge. This allows smooth transitions between patches
   * with different LOD levels.
   *
   * @tparam T Pointer type for primitive data (e.g., unsigned int*)
   * @param ptr Pointer to primitive data array
   * @param inner Inner tessellation density
   * @param nb_vertices Total number of vertices per edge
   * @param ratio Tessellation ratios for the four edges
   * @return Updated pointer after adding primitives
   */
  template <typename T>
  T *
  make_adapted_square_primitives(T *ptr,
      unsigned int inner, unsigned int nb_vertices, LVecBase4i ratio);

  /**
   * @brief Generates adaptive triangle primitives for edge skirts.
   *
   * Creates triangulated "skirts" along patch edges to hide cracks
   * between patches with different LOD levels. Skirts extend downward
   * from the patch edges.
   *
   * @tparam T Pointer type for primitive data
   * @param ptr Pointer to primitive data array
   * @param inner Inner tessellation density
   * @param nb_vertices Total number of vertices per edge
   * @param ratio Tessellation ratios for the four edges
   * @return Updated pointer after adding skirt primitives
   */
  template <typename T>
  T *
  make_adapted_square_primitives_skirt(T *ptr,
      unsigned int inner, unsigned int nb_vertices, LVecBase4i ratio);

  /**
   * @brief Generates uniform triangle primitives for a square patch.
   *
   * Creates a uniformly tessellated triangulated mesh (no edge adaptation).
   *
   * @tparam T Pointer type for primitive data
   * @param ptr Pointer to primitive data array
   * @param inner Inner tessellation density
   * @param nb_vertices Total number of vertices per edge
   * @return Updated pointer after adding primitives
   */
  template <typename T>
  T *
  make_primitives(T *ptr, unsigned int inner, unsigned int nb_vertices);

  /**
   * @brief Generates uniform triangle primitives for edge skirts.
   *
   * Creates skirts with uniform tessellation.
   *
   * @tparam T Pointer type for primitive data
   * @param ptr Pointer to primitive data array
   * @param inner Inner tessellation density
   * @param nb_vertices Total number of vertices per edge
   * @return Updated pointer after adding skirt primitives
   */
  template <typename T>
  T *
  make_primitives_skirt(T *ptr, unsigned int inner, unsigned int nb_vertices);

  /**
   * @brief Adds a triangle primitive.
   *
   * Helper method to add three vertex indices forming a triangle.
   *
   * @tparam T Pointer type for primitive data
   * @param ptr Pointer to primitive data array
   * @param a First vertex index
   * @param b Second vertex index
   * @param c Third vertex index
   * @return Updated pointer after adding triangle
   */
  template <typename T>
  inline T *
  add_vertices(T *ptr, unsigned int a, unsigned int b, unsigned int c);
};

/**
 * @brief Generates cube-mapped spherical patches using Quadrilateralized Cubic Sphere (QCS) projection.
 *
 * QCSPatchGenerator creates patches on a sphere/ellipsoid using a cube-mapping approach
 * where each face of a cube is subdivided and projected onto the sphere. This provides
 * more uniform tessellation than UV mapping, avoiding pole singularities.
 *
 * The QCS projection maps each cube face directly to the sphere using the normalized
 * cube face coordinates. This is simpler than the improved version but can show slight
 * area distortion near the edges of cube faces.
 *
 * Features:
 * - Cube-face mapping with configurable face orientation
 * - Adaptive tessellation for LOD transitions
 * - Edge skirts to hide cracks between patches
 * - Support for layered rendering (atmosphere, clouds)
 * - Jacobian calculation for area-correct lighting
 */
class QCSPatchGenerator : public CubePatchGeneratorBase
{
PUBLISHED:
  /**
   * @brief Constructs a QCS patch generator.
   */
  QCSPatchGenerator();

  /**
   * @brief Calculates the offset vector for a cube-mapped patch.
   *
   * The offset vector points from the origin to the center of the patch
   * on the sphere surface.
   *
   * @param axes Semi-axes of the ellipsoid (rx, ry, rz)
   * @param x0 Minimum X coordinate on cube face (-1 to 1)
   * @param y0 Minimum Y coordinate on cube face (-1 to 1)
   * @param x1 Maximum X coordinate on cube face (-1 to 1)
   * @param y1 Maximum Y coordinate on cube face (-1 to 1)
   * @param x_inverted If true, invert X axis mapping
   * @param y_inverted If true, invert Y axis mapping
   * @param xy_swap If true, swap X and Y axes (for face rotation)
   * @return Offset vector from origin to patch center
   */
  LVector3d
  make_offset_vector(LVector3d axes,
      double x0, double y0, double x1, double y1,
      bool x_inverted=false, bool y_inverted=false, bool xy_swap=false);

  /**
   * @brief Calculates the normal vector at a point on a QCS patch.
   *
   * @param axes Semi-axes of the ellipsoid (rx, ry, rz)
   * @param u Parametric U coordinate within patch (0-1)
   * @param v Parametric V coordinate within patch (0-1)
   * @param x0 Minimum X coordinate on cube face (-1 to 1)
   * @param y0 Minimum Y coordinate on cube face (-1 to 1)
   * @param x1 Maximum X coordinate on cube face (-1 to 1)
   * @param y1 Maximum Y coordinate on cube face (-1 to 1)
   * @param x_inverted If true, invert X axis mapping
   * @param y_inverted If true, invert Y axis mapping
   * @param xy_swap If true, swap X and Y axes
   * @return Normalized normal vector pointing outward from surface
   */
  LVector3d
  make_normal(LVector3d axes,
          double u, double v, double x0, double y0, double x1, double y1,
          bool x_inverted=false, bool y_inverted=false, bool xy_swap=false);

  /**
   * @brief Generates a QCS patch mesh.
   *
   * Creates a cube-face patch projected onto a spherical/ellipsoidal surface
   * with adaptive tessellation and optional edge skirts. This is the primary
   * method for generating planetary surface geometry.
   *
   * @param axes Semi-axes of the ellipsoid (rx, ry, rz)
   * @param tessellation Tessellation configuration (inner/outer densities)
   * @param x0 Minimum X coordinate on cube face (-1 to 1)
   * @param y0 Minimum Y coordinate on cube face (-1 to 1)
   * @param x1 Maximum X coordinate on cube face (-1 to 1)
   * @param y1 Maximum Y coordinate on cube face (-1 to 1)
   * @param inv_u If true, invert U texture coordinates
   * @param inv_v If true, invert V texture coordinates
   * @param swap_uv If true, swap U and V texture coordinates
   * @param x_inverted If true, invert X axis mapping
   * @param y_inverted If true, invert Y axis mapping
   * @param xy_swap If true, swap X and Y axes (for face rotation)
   * @param has_offset If true, apply offset to geometry
   * @param offset Offset distance from surface
   * @param use_patch_adaptation If true, enable adaptive tessellation
   * @param use_patch_skirts If true, generate edge skirts
   * @param skirt_size Size of edge skirts (as fraction of patch size)
   * @param skirt_uv UV offset for skirt texture coordinates
   * @param use_jacobian If true, calculate Jacobian for area-correct lighting
   * @return NodePath containing the generated patch geometry
   */
  NodePath
  make(LVector3d axes, TessellationInfo tessellation,
      double x0, double y0, double x1, double y1,
      bool inv_u=false, bool inv_v=false, bool swap_uv=false,
      bool x_inverted=false, bool y_inverted=false, bool xy_swap=false,
      bool has_offset=false, double offset=0.0,
      bool use_patch_adaptation=true, bool use_patch_skirts=true,
      double skirt_size=0.001, double skirt_uv=0.001,
      bool use_jacobian=true);

private:
  inline void
  make_point(LVector3d axes,
      double u, double v, double x0, double y0, double x1, double y1,
      LVector3d normal_coefs,
      bool inv_u, bool inv_v, bool swap_uv,
      bool has_offset, LVector3d offset_vector,
      bool use_jacobian,
      GeomVertexWriter &gvw, GeomVertexWriter &gtw, GeomVertexWriter &gnw,
      GeomVertexWriter &gtanw, GeomVertexWriter &gbiw, GeomVertexWriter &gjacobianw);
};

/**
 * @brief Generates cube-mapped spherical patches using improved QCS projection.
 *
 * ImprovedQCSPatchGenerator creates patches using an improved Quadrilateralized
 * Cubic Sphere projection that provides better area uniformity than the standard
 * QCS mapping. The improvement comes from using a modified mapping function
 * that reduces area distortion across the cube face.
 *
 * The improved projection uses the formula:
 * x' = x * sqrt(1 - y^2/2 - z^2/2 + y^2z^2/3)
 * y' = y * sqrt(1 - z^2/2 - x^2/2 + z^2x^2/3)
 * z' = z * sqrt(1 - x^2/2 - y^2/2 + x^2y^2/3)
 *
 * This results in more uniform tessellation density across the sphere surface
 * compared to simple normalization used in standard QCS.
 *
 * This is the recommended generator for high-quality planetary rendering where
 * uniform mesh density is important for consistent LOD behavior and lighting.
 *
 * Features:
 * - Improved equal-area cube-face mapping
 * - Adaptive tessellation for LOD transitions
 * - Edge skirts to hide cracks between patches
 * - Support for layered rendering
 * - Jacobian calculation for accurate lighting
 */
class ImprovedQCSPatchGenerator : public CubePatchGeneratorBase
{
PUBLISHED:
  /**
   * @brief Constructs an improved QCS patch generator.
   */
  ImprovedQCSPatchGenerator();

  /**
   * @brief Calculates the offset vector for an improved QCS patch.
   *
   * Computes the offset vector using the improved tangent-based mapping.
   *
   * @param axes Semi-axes of the ellipsoid (rx, ry, rz)
   * @param x0 Minimum X coordinate on cube face (-1 to 1)
   * @param y0 Minimum Y coordinate on cube face (-1 to 1)
   * @param x1 Maximum X coordinate on cube face (-1 to 1)
   * @param y1 Maximum Y coordinate on cube face (-1 to 1)
   * @param x_inverted If true, invert X axis mapping
   * @param y_inverted If true, invert Y axis mapping
   * @param xy_swap If true, swap X and Y axes (for face rotation)
   * @return Offset vector from origin to patch center
   */
  LVector3d
  make_offset_vector(LVector3d axes,
      double x0, double y0, double x1, double y1,
      bool x_inverted=false, bool y_inverted=false, bool xy_swap=false);

  /**
   * @brief Calculates the normal vector at a point on an improved QCS patch.
   *
   * @param axes Semi-axes of the ellipsoid (rx, ry, rz)
   * @param u Parametric U coordinate within patch (0-1)
   * @param v Parametric V coordinate within patch (0-1)
   * @param x0 Minimum X coordinate on cube face (-1 to 1)
   * @param y0 Minimum Y coordinate on cube face (-1 to 1)
   * @param x1 Maximum X coordinate on cube face (-1 to 1)
   * @param y1 Maximum Y coordinate on cube face (-1 to 1)
   * @param x_inverted If true, invert X axis mapping
   * @param y_inverted If true, invert Y axis mapping
   * @param xy_swap If true, swap X and Y axes
   * @return Normalized normal vector pointing outward from surface
   */
  LVector3d
  make_normal(LVector3d axes,
          double u, double v, double x0, double y0, double x1, double y1,
          bool x_inverted=false, bool y_inverted=false, bool xy_swap=false);

  /**
   * @brief Generates an improved QCS patch mesh.
   *
   * Creates a cube-face patch using the improved tangent-based projection
   * for better area uniformity. Supports adaptive tessellation and edge skirts.
   *
   * @param axes Semi-axes of the ellipsoid (rx, ry, rz)
   * @param tessellation Tessellation configuration (inner/outer densities)
   * @param x0 Minimum X coordinate on cube face (-1 to 1)
   * @param y0 Minimum Y coordinate on cube face (-1 to 1)
   * @param x1 Maximum X coordinate on cube face (-1 to 1)
   * @param y1 Maximum Y coordinate on cube face (-1 to 1)
   * @param inv_u If true, invert U texture coordinates
   * @param inv_v If true, invert V texture coordinates
   * @param swap_uv If true, swap U and V texture coordinates
   * @param x_inverted If true, invert X axis mapping
   * @param y_inverted If true, invert Y axis mapping
   * @param xy_swap If true, swap X and Y axes (for face rotation)
   * @param has_offset If true, apply offset to geometry
   * @param offset Offset distance from surface
   * @param use_patch_adaptation If true, enable adaptive tessellation
   * @param use_patch_skirts If true, generate edge skirts
   * @param skirt_size Size of edge skirts (as fraction of patch size)
   * @param skirt_uv UV offset for skirt texture coordinates
   * @param use_jacobian If true, calculate Jacobian for area-correct lighting
   * @return NodePath containing the generated patch geometry
   */
  NodePath
  make(LVector3d axes, TessellationInfo tessellation,
      double x0, double y0, double x1, double y1,
      bool inv_u=false, bool inv_v=false, bool swap_uv=false,
      bool x_inverted=false, bool y_inverted=false, bool xy_swap=false,
      bool has_offset=false, double offset=0.0,
      bool use_patch_adaptation=true, bool use_patch_skirts=true,
      double skirt_size=0.001, double skirt_uv=0.001,
      bool use_jacobian=true);

private:
  inline void
  make_point(LVector3d axes,
      double u, double v, double x0, double y0, double x1, double y1,
      LVector3d normal_coefs,
      bool inv_u, bool inv_v, bool swap_uv,
      bool has_offset, LVector3d offset_vector,
      bool use_jacobian,
      GeomVertexWriter &gvw, GeomVertexWriter &gtw, GeomVertexWriter &gnw,
      GeomVertexWriter &gtanw, GeomVertexWriter &gbiw, GeomVertexWriter &gjacobianw);
};

/**
 * @brief Generates flat planar tile patches for heightfield terrain.
 *
 * TilePatchGenerator creates rectangular flat tiles used for terrain rendering
 * with height displacement. Unlike the spherical patch generators, this creates
 * planar geometry intended for height-mapping or for rendering local terrain
 * patches where surface curvature can be ignored.
 *
 * The generated tiles are flat XY planes that can be displaced in the Z direction
 * by vertex shaders or heightfield data. This is useful for:
 * - Large-scale terrain rendering where local patches appear flat
 * - Height-mapped terrain systems
 * - Terrain chunks in non-planetary environments
 *
 * Features:
 * - Flat planar geometry with configurable size
 * - Adaptive tessellation for LOD transitions between tiles
 * - Edge skirts to hide cracks between LOD levels
 * - Texture coordinate mapping suitable for heightfield sampling
 */
class TilePatchGenerator :  public CubePatchGeneratorBase
{
PUBLISHED:
  /**
   * @brief Constructs a tile patch generator.
   */
  TilePatchGenerator();

  /**
   * @brief Generates a flat tile patch mesh.
   *
   * Creates a rectangular planar tile centered at the origin with configurable
   * tessellation density. The tile lies in the XY plane and can be textured
   * for heightfield displacement.
   *
   * @param size Size of the tile (width and height in world units)
   * @param tessellation Tessellation configuration (inner/outer densities)
   * @param inv_u If true, invert U texture coordinates
   * @param inv_v If true, invert V texture coordinates
   * @param swap_uv If true, swap U and V texture coordinates
   * @param use_patch_adaptation If true, enable adaptive tessellation
   * @param use_patch_skirts If true, generate edge skirts
   * @param skirt_size Size of edge skirts (in world units)
   * @param skirt_uv UV offset for skirt texture coordinates
   * @return NodePath containing the generated tile geometry
   */
  NodePath
  make(double size, TessellationInfo tessellation,
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
