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

/**
 * @file geometry.cpp
 * @brief Implementation of procedural geometry generators for planetary rendering.
 *
 * This file implements various patch generators for creating spherical and planar
 * geometry used in planetary-scale rendering systems. The generators support:
 *
 * - Multiple coordinate systems (UV spherical, QCS cube-mapped, improved QCS)
 * - Adaptive tessellation for seamless LOD transitions
 * - Edge skirts to prevent Z-fighting and cracks between LOD levels
 * - Vertex data generation with normals, tangents, and texture coordinates
 *
 * Key components:
 * - TessellationInfo: Configuration for adaptive mesh density
 * - UVPatchGenerator: Spherical patches using lat/lon parameterization
 * - QCSPatchGenerator: Cube-mapped sphere patches (standard projection)
 * - ImprovedQCSPatchGenerator: Cube-mapped patches with better area uniformity
 * - TilePatchGenerator: Flat planar tiles for heightfield terrain
 * - CubePatchGeneratorBase: Template methods for triangle primitive generation
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

// ============================================================================
// TessellationInfo Implementation
// ============================================================================

/**
 * @brief Constructs tessellation configuration and computes edge ratios.
 *
 * Calculates the tessellation ratios for each edge based on the difference
 * between inner and outer tessellation densities. These ratios are used to
 * create smooth transitions between patches with different LOD levels.
 */
TessellationInfo::TessellationInfo(unsigned int inner, LVecBase4i outer) :
        inner(inner),
        outer(outer)
{
    for (unsigned int i = 0; i < 4; ++i) {
        unsigned int x = outer[i];
        ratio[i] = inner >= x ? inner / x : 1;
    }
}

// ============================================================================
// UVPatchGenerator Implementation
// ============================================================================

UVPatchGenerator::UVPatchGenerator()
{
}

/**
 * @brief Computes offset vector to patch center using spherical coordinates.
 *
 * Converts UV coordinates (longitude/latitude) to 3D position on the ellipsoid
 * surface. The offset points from the origin to the geometric center of the patch.
 */
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

/**
 * @brief Computes surface normal at a point using spherical parameterization.
 *
 * Calculates the normal vector for an ellipsoid at the given UV coordinates.
 * The normal is computed from the gradient of the ellipsoid equation and
 * normalized to unit length.
 */
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

/**
 * @brief Generates a UV-mapped spherical patch with full vertex attributes.
 *
 * Creates a rectangular patch on an ellipsoid surface using latitude/longitude
 * parameterization. Generates vertex positions, normals, texture coordinates,
 * tangents, and binormals. The patch is subdivided into rings (latitude) and
 * sectors (longitude) for the desired tessellation density.
 */
NodePath
UVPatchGenerator::make(LVector3d axes, unsigned int rings, unsigned int sectors,
        double x0, double y0, double x1, double y1,
        bool global_texture, bool inv_texture_u, bool inv_texture_v,
        double offset, bool use_patch_adaptation, bool use_patch_skirts,
        double skirt_size, double skirt_uv, LVecBase4i outer)
{
    _geom_collector.start();

    unsigned int r_sectors = sectors + 1;
    unsigned int r_rings = rings + 1;

    // Compute outer tessellation ratios for edge adaptation
    LVecBase4i ratio;
    if (use_patch_adaptation) {
        for (unsigned int i = 0; i < 4; ++i) {
            unsigned int x = outer[i];
            ratio[i] = (x > 0 && rings >= x) ? rings / x : 1;
        }
    }

    unsigned int nb_data = r_rings * r_sectors;
    // Reserve space for primitive indices: each quad becomes 2 triangles with 3 indices each
    unsigned int nb_vertices = rings * sectors * 2 * 3;

    if (use_patch_skirts) {
        // Add vertices for 4 edges
        nb_data += 2 * r_rings + 2 * r_sectors;
        // Add indices for skirt: each segment becomes 2 triangles with 3 indices each
        nb_vertices += (2 * rings + 2 * sectors) * 2 * 3;
    }

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

    // Generate main patch vertices
    for (unsigned int r = 0; r < r_rings; ++r) {
        for (unsigned int s = 0; s < r_sectors; ++s) {
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
            LVector3d binormal = LVector3d(cos_s * cos_r, sin_s * cos_r, sin_r);
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
            binormal.componentwise_mult(axes);
            binormal.normalize();
            gbiw.add_data3d(binormal);
        }
    }

    // Generate skirt vertices if enabled
    if (use_patch_skirts) {
        // Reduce axes for skirt depth
        LVector3d reduced_axes = axes - LVector3d(std::max(dx, dy) * skirt_size);

        // Edge order: 0=left, 1=right, 2=bottom, 3=top
        for (unsigned int edge = 0; edge < 4; ++edge) {
            if (edge == 0) {  // Left edge (s=0, all r)
                for (unsigned int r = 0; r < r_rings; ++r) {
                    unsigned int s = 0;
                    double u_skirt = (!inv_texture_u) ? -skirt_uv : 1.0 + skirt_uv;
                    double v_skirt = double(r) / rings;
                    if (inv_texture_v) {
                        v_skirt = 1.0 - v_skirt;
                    }

                    double cos_s = cos(2 * M_PI * (x0 + s * dx / sectors) + M_PI);
                    double sin_s = sin(2 * M_PI * (x0 + s * dx / sectors) + M_PI);
                    double sin_r = sin(M_PI * (y0 + r * dy / rings));
                    double cos_r = cos(M_PI * (y0 + r * dy / rings));
                    LPoint3d point = LPoint3d(cos_s * sin_r, sin_s * sin_r, -cos_r);
                    LVector3d normal(point);
                    LVector3d tangent;
                    if (sin_r > 0) {
                        tangent = LVector3d(-axes[0] * point[1], axes[1] * point[0], 0);
                    } else {
                        tangent = LVector3d(-axes[0], 0, 0);
                    }
                    LVector3d binormal = LVector3d(cos_s * cos_r, sin_s * cos_r, sin_r);

                    if (!global_texture) {
                        gtw.add_data2(u_skirt, v_skirt);
                    } else {
                        gtw.add_data2((x0 + s * dx / sectors), (y0 + r * dy / rings));
                    }

                    point.componentwise_mult(reduced_axes);
                    if (offset != 0.0) {
                        point -= offset_vector;
                    }
                    gvw.add_data3d(point);
                    normal.componentwise_mult(normal_coefs);
                    normal.normalize();
                    gnw.add_data3d(normal);
                    tangent.normalize();
                    gtanw.add_data3d(tangent);
                    binormal.componentwise_mult(axes);
                    binormal.normalize();
                    gbiw.add_data3d(binormal);
                }
            } else if (edge == 1) {  // Right edge (s=sectors, all r)
                for (unsigned int r = 0; r < r_rings; ++r) {
                    unsigned int s = sectors;
                    double u_skirt = (!inv_texture_u) ? 1.0 + skirt_uv : -skirt_uv;
                    double v_skirt = double(r) / rings;
                    if (inv_texture_v) {
                        v_skirt = 1.0 - v_skirt;
                    }

                    double cos_s = cos(2 * M_PI * (x0 + s * dx / sectors) + M_PI);
                    double sin_s = sin(2 * M_PI * (x0 + s * dx / sectors) + M_PI);
                    double sin_r = sin(M_PI * (y0 + r * dy / rings));
                    double cos_r = cos(M_PI * (y0 + r * dy / rings));
                    LPoint3d point = LPoint3d(cos_s * sin_r, sin_s * sin_r, -cos_r);
                    LVector3d normal(point);
                    LVector3d tangent;
                    if (sin_r > 0) {
                        tangent = LVector3d(-axes[0] * point[1], axes[1] * point[0], 0);
                    } else {
                        tangent = LVector3d(-axes[0], 0, 0);
                    }
                    LVector3d binormal = LVector3d(cos_s * cos_r, sin_s * cos_r, sin_r);

                    if (!global_texture) {
                        gtw.add_data2(u_skirt, v_skirt);
                    } else {
                        gtw.add_data2((x0 + s * dx / sectors), (y0 + r * dy / rings));
                    }

                    point.componentwise_mult(reduced_axes);
                    if (offset != 0.0) {
                        point -= offset_vector;
                    }
                    gvw.add_data3d(point);
                    normal.componentwise_mult(normal_coefs);
                    normal.normalize();
                    gnw.add_data3d(normal);
                    tangent.normalize();
                    gtanw.add_data3d(tangent);
                    binormal.componentwise_mult(axes);
                    binormal.normalize();
                    gbiw.add_data3d(binormal);
                }
            } else if (edge == 2) {  // Bottom edge (r=0, all s)
                for (unsigned int s = 0; s < r_sectors; ++s) {
                    unsigned int r = 0;
                    double u_skirt = double(s) / sectors;
                    if (inv_texture_u) {
                        u_skirt = 1.0 - u_skirt;
                    }
                    double v_skirt = (!inv_texture_v) ? -skirt_uv : 1.0 + skirt_uv;

                    double cos_s = cos(2 * M_PI * (x0 + s * dx / sectors) + M_PI);
                    double sin_s = sin(2 * M_PI * (x0 + s * dx / sectors) + M_PI);
                    double sin_r = sin(M_PI * (y0 + r * dy / rings));
                    double cos_r = cos(M_PI * (y0 + r * dy / rings));
                    LPoint3d point = LPoint3d(cos_s * sin_r, sin_s * sin_r, -cos_r);
                    LVector3d normal(point);
                    LVector3d tangent;
                    if (sin_r > 0) {
                        tangent = LVector3d(-axes[0] * point[1], axes[1] * point[0], 0);
                    } else {
                        tangent = LVector3d(-axes[0], 0, 0);
                    }
                    LVector3d binormal = LVector3d(cos_s * cos_r, sin_s * cos_r, sin_r);

                    if (!global_texture) {
                        gtw.add_data2(u_skirt, v_skirt);
                    } else {
                        gtw.add_data2((x0 + s * dx / sectors), (y0 + r * dy / rings));
                    }

                    point.componentwise_mult(reduced_axes);
                    if (offset != 0.0) {
                        point -= offset_vector;
                    }
                    gvw.add_data3d(point);
                    normal.componentwise_mult(normal_coefs);
                    normal.normalize();
                    gnw.add_data3d(normal);
                    tangent.normalize();
                    gtanw.add_data3d(tangent);
                    binormal.componentwise_mult(axes);
                    binormal.normalize();
                    gbiw.add_data3d(binormal);
                }
            } else {  // edge == 3, Top edge (r=rings, all s)
                for (unsigned int s = 0; s < r_sectors; ++s) {
                    unsigned int r = rings;
                    double u_skirt = double(s) / sectors;
                    if (inv_texture_u) {
                        u_skirt = 1.0 - u_skirt;
                    }
                    double v_skirt = (!inv_texture_v) ? 1.0 + skirt_uv : -skirt_uv;

                    double cos_s = cos(2 * M_PI * (x0 + s * dx / sectors) + M_PI);
                    double sin_s = sin(2 * M_PI * (x0 + s * dx / sectors) + M_PI);
                    double sin_r = sin(M_PI * (y0 + r * dy / rings));
                    double cos_r = cos(M_PI * (y0 + r * dy / rings));
                    LPoint3d point = LPoint3d(cos_s * sin_r, sin_s * sin_r, -cos_r);
                    LVector3d normal(point);
                    LVector3d tangent;
                    if (sin_r > 0) {
                        tangent = LVector3d(-axes[0] * point[1], axes[1] * point[0], 0);
                    } else {
                        tangent = LVector3d(-axes[0], 0, 0);
                    }
                    LVector3d binormal = LVector3d(cos_s * cos_r, sin_s * cos_r, sin_r);

                    if (!global_texture) {
                        gtw.add_data2(u_skirt, v_skirt);
                    } else {
                        gtw.add_data2((x0 + s * dx / sectors), (y0 + r * dy / rings));
                    }

                    point.componentwise_mult(reduced_axes);
                    if (offset != 0.0) {
                        point -= offset_vector;
                    }
                    gvw.add_data3d(point);
                    normal.componentwise_mult(normal_coefs);
                    normal.normalize();
                    gnw.add_data3d(normal);
                    tangent.normalize();
                    gtanw.add_data3d(tangent);
                    binormal.componentwise_mult(axes);
                    binormal.normalize();
                    gbiw.add_data3d(binormal);
                }
            }
        }
    }

    // Generate main patch primitives
    if (use_patch_adaptation) {
        make_adapted_uv_primitives(prim, rings, sectors, r_rings, r_sectors, ratio);
    } else {
        for (unsigned int r = 0; r < r_rings - 1; ++r) {
            for (unsigned int s = 0; s < r_sectors - 1; ++s) {
                prim->add_vertices(r * r_sectors + s, r * r_sectors + (s + 1), (r + 1) * r_sectors + s);
                prim->add_vertices(r * r_sectors + (s + 1), (r + 1) * r_sectors + (s + 1), (r + 1) * r_sectors + s);
            }
        }
    }

    // Generate skirt primitives if enabled
    if (use_patch_skirts) {
        if (use_patch_adaptation) {
            make_adapted_uv_primitives_skirt(prim, rings, sectors, r_rings, r_sectors, ratio);
        } else {
            unsigned int base_idx = r_rings * r_sectors;

            // Left edge (s=0): Connect to skirt
            unsigned int skirt_start = base_idx;
            for (unsigned int r = 0; r < rings; ++r) {
                unsigned int v = r * r_sectors;
                unsigned int skirt = skirt_start + r;
                prim->add_vertices(v, v + r_sectors, skirt);
                prim->add_vertices(skirt, v + r_sectors, skirt + 1);
            }

            // Right edge (s=sectors): Connect to skirt
            skirt_start = base_idx + r_rings;
            for (unsigned int r = 0; r < rings; ++r) {
                unsigned int v = r * r_sectors + sectors;
                unsigned int skirt = skirt_start + r;
                prim->add_vertices(skirt, v, v + r_sectors);
                prim->add_vertices(v + r_sectors, skirt + 1, skirt);
            }

            // Bottom edge (r=0): Connect to skirt
            skirt_start = base_idx + 2 * r_rings;
            for (unsigned int s = 0; s < sectors; ++s) {
                unsigned int v = s;
                unsigned int skirt = skirt_start + s;
                prim->add_vertices(skirt, v, v + 1);
                prim->add_vertices(v + 1, skirt + 1, skirt);
            }

            // Top edge (r=rings): Connect to skirt
            skirt_start = base_idx + 2 * r_rings + r_sectors;
            for (unsigned int s = 0; s < sectors; ++s) {
                unsigned int v = rings * r_sectors + s;
                unsigned int skirt = skirt_start + s;
                prim->add_vertices(v, skirt, v + 1);
                prim->add_vertices(skirt, skirt + 1, v + 1);
            }
        }
    }

    prim->close_primitive();
    geom->add_primitive(prim);
    node->add_geom(geom);

    _geom_collector.stop();

    return NodePath(node);
}

// ============================================================================
// UVPatchGenerator Adaptive Primitive Helpers
// ============================================================================

/**
 * @brief Generates adaptive triangle primitives for a UV patch grid.
 *
 * Creates triangles for a UV (latitude/longitude) spherical patch with
 * adaptive tessellation along the edges to match neighbouring patches with
 * different LOD levels.
 *
 * ratio ordering: [left (s=0), bottom (r=0), right (s=sectors), top (r=rings)].
 */
void
UVPatchGenerator::make_adapted_uv_primitives(GeomTriangles *prim,
        unsigned int rings, unsigned int sectors,
        unsigned int r_rings, unsigned int r_sectors,
        LVecBase4i ratio)
{
    for (unsigned int r = 0; r < rings; ++r) {
        for (unsigned int s = 0; s < sectors; ++s) {
            unsigned int v = r_sectors * r + s;
            if (r == 0) {
                unsigned int i = 1;  // bottom: merges s
                if (s == 0) {
                    // Bottom-left corner
                    unsigned int j = 0;  // left
                    if (ratio[i] == 1 && ratio[j] == 1) {
                        prim->add_vertices(v, v + 1, v + r_sectors);
                        prim->add_vertices(v + 1, v + r_sectors + 1, v + r_sectors);
                    } else {
                        prim->add_vertices(v, v + r_sectors + 1, v + r_sectors * ratio[j]);
                        prim->add_vertices(v, v + ratio[i], v + r_sectors + 1);
                    }
                } else if (s == sectors - 1) {
                    // Bottom-right corner
                    unsigned int j = 2;  // right
                    if (ratio[i] == 1) {
                        prim->add_vertices(v, v + 1, v + r_sectors);
                    }
                    if (ratio[j] == 1) {
                        prim->add_vertices(v + 1, v + r_sectors + 1, v + r_sectors);
                    }
                } else {
                    // Bottom edge, not corner
                    unsigned int vp = r * r_sectors + (s / ratio[i]) * ratio[i];
                    if ((s % ratio[i]) == 0) {
                        prim->add_vertices(v, v + ratio[i], v + r_sectors);
                    }
                    prim->add_vertices(vp + ratio[i], v + r_sectors + 1, v + r_sectors);
                }
            } else if (r == rings - 1) {
                unsigned int i = 3;  // top: merges s
                if (s == 0) {
                    // Top-left corner
                    unsigned int j = 0;  // left
                    if (ratio[j] == 1) {
                        prim->add_vertices(v, v + 1, v + r_sectors);
                    }
                    if (ratio[i] == 1) {
                        prim->add_vertices(v + 1, v + r_sectors + 1, v + r_sectors);
                    }
                } else if (s == sectors - 1) {
                    // Top-right corner
                    unsigned int j = 2;  // right
                    if (ratio[i] == 1 && ratio[j] == 1) {
                        prim->add_vertices(v, v + 1, v + r_sectors);
                        prim->add_vertices(v + 1, v + r_sectors + 1, v + r_sectors);
                    } else {
                        unsigned int vpx = r_sectors * (r / ratio[j]) * ratio[j] + s;
                        prim->add_vertices(vpx + 1, v + r_sectors + 1, v);
                        unsigned int vpy = r * r_sectors + (s / ratio[i]) * ratio[i];
                        prim->add_vertices(v, v + r_sectors + 1, vpy + r_sectors);
                    }
                } else {
                    // Top edge, not corner
                    unsigned int vp = r * r_sectors + (s / ratio[i]) * ratio[i];
                    prim->add_vertices(v, v + 1, vp + r_sectors);
                    if (((s + 1) % ratio[i]) == 0) {
                        prim->add_vertices(v + 1, v + r_sectors + 1, vp + r_sectors);
                    }
                }
            } else if (s == 0) {
                // Left edge: merges r
                unsigned int i = 0;
                unsigned int vp = r_sectors * (r / ratio[i]) * ratio[i] + s;
                prim->add_vertices(v + 1, v + r_sectors + 1, vp + r_sectors * ratio[i]);
                if ((r % ratio[i]) == 0) {
                    prim->add_vertices(v, v + 1, vp + r_sectors * ratio[i]);
                }
            } else if (s == sectors - 1) {
                // Right edge: merges r
                unsigned int i = 2;
                unsigned int vp = r_sectors * (r / ratio[i]) * ratio[i] + s;
                prim->add_vertices(v, vp + 1, v + r_sectors);
                if (((r + 1) % ratio[i]) == 0) {
                    prim->add_vertices(vp + 1, v + r_sectors + 1, v + r_sectors);
                }
            } else {
                prim->add_vertices(v, v + 1, v + r_sectors);
                prim->add_vertices(v + 1, v + r_sectors + 1, v + r_sectors);
            }
        }
    }
}

/**
 * @brief Generates adaptive triangle primitives for UV patch edge skirts.
 *
 * Creates triangles connecting the UV patch edges to surrounding skirt
 * vertices. Adapts per-edge tessellation to match the outer levels.
 *
 * Skirt vertices start at index (r_rings * r_sectors) in the order:
 * [left (r_rings), right (r_rings), bottom (r_sectors), top (r_sectors)].
 */
void
UVPatchGenerator::make_adapted_uv_primitives_skirt(GeomTriangles *prim,
        unsigned int rings, unsigned int sectors,
        unsigned int r_rings, unsigned int r_sectors,
        LVecBase4i ratio)
{
    unsigned int base_idx = r_rings * r_sectors;

    // Left edge (s=0): adapts along r
    unsigned int skirt_start = base_idx;
    for (unsigned int r = 0; r < rings; ++r) {
        unsigned int v = r * r_sectors;
        unsigned int skirt = skirt_start + r;
        if ((r % ratio[0]) == 0) {
            prim->add_vertices(v, v + r_sectors * ratio[0], skirt);
            prim->add_vertices(skirt, v + r_sectors * ratio[0], skirt + ratio[0]);
        }
    }

    // Right edge (s=sectors): adapts along r
    skirt_start = base_idx + r_rings;
    for (unsigned int r = 0; r < rings; ++r) {
        unsigned int v = r * r_sectors + sectors;
        unsigned int skirt = skirt_start + r;
        if ((r % ratio[2]) == 0) {
            prim->add_vertices(skirt, v, v + r_sectors * ratio[2]);
            prim->add_vertices(v + r_sectors * ratio[2], skirt + ratio[2], skirt);
        }
    }

    // Bottom edge (r=0): adapts along s
    skirt_start = base_idx + 2 * r_rings;
    for (unsigned int s = 0; s < sectors; ++s) {
        unsigned int v = s;
        unsigned int skirt = skirt_start + s;
        if ((s % ratio[1]) == 0) {
            prim->add_vertices(skirt, v, v + ratio[1]);
            prim->add_vertices(v + ratio[1], skirt + ratio[1], skirt);
        }
    }

    // Top edge (r=rings): adapts along s
    skirt_start = base_idx + 2 * r_rings + r_sectors;
    for (unsigned int s = 0; s < sectors; ++s) {
        unsigned int v = rings * r_sectors + s;
        unsigned int skirt = skirt_start + s;
        if ((s % ratio[3]) == 0) {
            prim->add_vertices(v, skirt, v + ratio[3]);
            prim->add_vertices(skirt, skirt + ratio[3], v + ratio[3]);
        }
    }
}

// ============================================================================
// CubePatchGeneratorBase Implementation
// ============================================================================

/**
 * @brief Adds a triangle to the primitive array.
 *
 * Helper template method to write three vertex indices forming a triangle.
 * Used by all primitive generation methods.
 */
template <typename T>
T *
CubePatchGeneratorBase::add_vertices(T *ptr, unsigned int a, unsigned int b, unsigned int c) {
    *ptr++ = a;
    *ptr++ = b;
    *ptr++ = c;
    return ptr;
}

/**
 * @brief Generates uniform triangle primitives for a square patch.
 *
 * Creates a regular grid of triangles with uniform tessellation. Each quad
 * in the grid is split into two triangles. This is used when no adaptive
 * tessellation is wanted.
 */
template <typename T>
T *
CubePatchGeneratorBase::make_primitives(T *ptr, unsigned int inner, unsigned int nb_vertices)
{
    for (unsigned int x = 0; x < inner; ++x) {
        for (unsigned int y = 0; y < inner; ++y) {
            unsigned int v = nb_vertices * x + y;
            ptr = add_vertices(ptr, v, v + nb_vertices, v + 1);
            ptr = add_vertices(ptr, v + 1, v + nb_vertices, v + nb_vertices + 1);
        }
    }
    return ptr;
}

/**
 * @brief Generates adaptive triangle primitives for a square patch.
 *
 * Creates triangulated mesh with potentially different tessellation densities
 * on each edge. The algorithm:
 * 1. Generates inner uniform grid
 * 2. Creates transition zones along edges with different densities
 * 3. Fills corners with adaptive triangulation
 *
 * This allows seamless transitions between patches with different LOD levels
 * without T-junctions or cracks.
 */
template <typename T>
T *
CubePatchGeneratorBase::make_adapted_square_primitives(T *ptr,
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
                        ptr = add_vertices(ptr, v, v + nb_vertices, v + 1);
                        ptr = add_vertices(ptr, v + 1, v + nb_vertices, v + nb_vertices + 1);
                    } else {
                        ptr = add_vertices(ptr, v, v + nb_vertices * ratio[j], v + nb_vertices + 1);
                        ptr = add_vertices(ptr, v, v + nb_vertices + 1, v + ratio[i]);
                    }
                } else if (y == inner - 1) {
                    unsigned int j = 3;
                    if (ratio[i] == 1) {
                        ptr = add_vertices(ptr, v, v + nb_vertices, v + 1);
                    }
                    if (ratio[j] == 1) {
                        ptr = add_vertices(ptr, v + 1, v + nb_vertices, v + nb_vertices + 1);
                    }
                } else {
                    unsigned int vp = nb_vertices * x + int(y / ratio[i]) * ratio[i];
                    if ((y % ratio[i]) == 0) {
                        ptr = add_vertices(ptr, v, v + nb_vertices, v + ratio[i]);
                    }
                    ptr = add_vertices(ptr, vp + ratio[i], v + nb_vertices, v + nb_vertices + 1);
                }
            } else if (x == inner - 1) {
                unsigned int i = 2;
                if (y == 0) {
                    unsigned int j = 1;
                    if (ratio[j] == 1) {
                        ptr = add_vertices(ptr, v, v + nb_vertices, v + 1);
                    }
                    if (ratio[i] == 1) {
                        ptr = add_vertices(ptr, v + 1, v + nb_vertices, v + nb_vertices + 1);
                    }
                } else if (y == inner - 1) {
                    unsigned int j = 3;
                    if (ratio[i] == 1 && ratio[j] == 1) {
                        ptr = add_vertices(ptr, v, v + nb_vertices, v + 1);
                        ptr = add_vertices(ptr, v + 1, v + nb_vertices, v + nb_vertices + 1);
                    } else {
                        unsigned int vpx = nb_vertices * (x / ratio[j]) * ratio[j] + y;
                        ptr = add_vertices(ptr, vpx + 1, v, v + nb_vertices + 1);
                        unsigned int vpy = nb_vertices * x + ((y / ratio[i]) * ratio[i]);
                        ptr = add_vertices(ptr, v, vpy + nb_vertices, v + nb_vertices + 1);
                    }
                } else {
                    unsigned int vp = nb_vertices * x + ((y / ratio[i]) * ratio[i]);
                    ptr = add_vertices(ptr, v, vp + nb_vertices, v + 1);
                    if (((y + 1) % ratio[i]) == 0) {
                        ptr = add_vertices(ptr, v + 1, vp + nb_vertices, v + nb_vertices + 1);
                    }
                }
            } else if (y == 0) {
                unsigned int i = 1;
                unsigned int vp = nb_vertices * (x / ratio[i]) * ratio[i] + y;
                ptr = add_vertices(ptr, v + 1, vp + nb_vertices * ratio[i], v + nb_vertices + 1);
                if ((x % ratio[i]) == 0) {
                    ptr = add_vertices(ptr, v, v + nb_vertices * ratio[i], v + 1);
                }
            } else if (y == inner - 1) {
                unsigned int i = 3;
                unsigned int vp = nb_vertices * (x / ratio[i]) * ratio[i] + y;
                ptr = add_vertices(ptr, v, v + nb_vertices, vp + 1);
                if (((x + 1) % ratio[i]) == 0) {
                    ptr = add_vertices(ptr, vp + 1, v + nb_vertices, v + nb_vertices + 1);
                }
            } else {
                ptr = add_vertices(ptr, v, v + nb_vertices, v + 1);
                ptr = add_vertices(ptr, v + 1, v + nb_vertices, v + nb_vertices + 1);
            }
        }
    }
    return ptr;
}

/**
 * @brief Generates adaptive skirt primitives for edge crack prevention.
 *
 * Creates vertical "skirt" geometry along patch edges that extends downward
 * to hide cracks and Z-fighting between patches with different LOD levels.
 * The skirts follow the same adaptive tessellation pattern as the main patch
 * to ensure proper connection with edge vertices.
 */
template <typename T>
T *
CubePatchGeneratorBase::make_adapted_square_primitives_skirt(T *ptr,
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
            unsigned int v = nb_vertices * x + y;
            if (a == 0) {
                if ((y % ratio[i]) == 0) {
                    ptr = add_vertices(ptr, v, v + ratio[i], skirt);
                    ptr = add_vertices(ptr, skirt, v + ratio[i], skirt + ratio[i]);
                }
            } else if (a == 1) {
                if ((y % ratio[i]) == 0) {
                    ptr = add_vertices(ptr, v + nb_vertices, skirt, v + nb_vertices + ratio[i]);
                    ptr = add_vertices(ptr, v + nb_vertices + ratio[i], skirt, skirt + ratio[i]);
                }
            } else if (a == 2) {
                if ((x % ratio[i]) == 0) {
                    ptr = add_vertices(ptr, v, skirt, v + nb_vertices * ratio[i]);
                    ptr = add_vertices(ptr, v + nb_vertices * ratio[i], skirt, skirt + ratio[i]);
                }
            } else if (a == 3) {
                if ((x % ratio[i]) == 0) {
                    ptr = add_vertices(ptr, skirt + ratio[i], v + 1, v + nb_vertices * ratio[i] + 1);
                    ptr = add_vertices(ptr, skirt, v + 1, skirt + ratio[i]);
                }
            }
        }
    }
    return ptr;
}

/**
 * @brief Generates uniform skirt primitives.
 *
 * Creates edge skirts with uniform tessellation (no adaptation). Used when
 * adaptive tessellation is disabled.
 */
template <typename T>
T *
CubePatchGeneratorBase::make_primitives_skirt(T *ptr,
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
                ptr = add_vertices(ptr, v, v + 1, skirt);
                ptr = add_vertices(ptr, skirt, v + 1, skirt + 1);
            } else if (a == 1) {
                ptr = add_vertices(ptr, v + nb_vertices, skirt, v + nb_vertices + 1);
                ptr = add_vertices(ptr, v + nb_vertices + 1, skirt, skirt + 1);
            } else if (a == 2) {
                ptr = add_vertices(ptr, v, skirt, v + nb_vertices);
                ptr = add_vertices(ptr, v + nb_vertices, skirt, skirt + 1);
            } else if (a == 3) {
                ptr = add_vertices(ptr, skirt + 1, v + 1, v + nb_vertices + 1);
                ptr = add_vertices(ptr, skirt, v + 1, skirt + 1);
            }
        }
    }
    return ptr;
}

// ============================================================================
// QCSPatchGenerator Implementation
// ============================================================================

QCSPatchGenerator::QCSPatchGenerator()
{
}

/**
 * @brief Computes offset vector using standard QCS cube-to-sphere mapping.
 *
 * Maps cube face coordinates to sphere surface using direct normalization.
 * Handles axis inversions and swapping for different cube face orientations.
 */
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

/**
 * @brief Computes surface normal using standard QCS mapping.
 *
 * Calculates normal vector for an ellipsoid at the given cube face coordinates.
 * The normal is derived from the gradient of the ellipsoid equation.
 */
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
        bool use_jacobian,
        GeomVertexWriter &gvw, GeomVertexWriter &gtw, GeomVertexWriter &gnw, GeomVertexWriter &gtanw,
        GeomVertexWriter &gbiw, GeomVertexWriter &gjacobianw)
{
    double x = x0 + u * dx;
    double y = y0 + v * dy;
    x = 2.0 * x - 1.0;
    y = 2.0 * y - 1.0;
    LVector3d point(x, y, 1.0);
    point.normalize();
    LVector3d normal = point;

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
    if (use_jacobian) {
        gjacobianw.add_data3d(x, y, 1 / (x * x + y * y + 1));
    } else {
        LVector3d tangent(1.0 + y * y, -x * y, -x);
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
}

/**
 * @brief Generates a complete QCS patch with adaptive tessellation.
 *
 * Main method that creates the full patch geometry including:
 * - Vertex positions mapped from cube face to sphere
 * - Surface normals for lighting
 * - Texture coordinates
 * - Tangent space vectors for normal mapping
 * - Optional Jacobian data for area-correct rendering
 * - Optional edge skirts for crack prevention
 *
 * The method handles axis transformations for different cube face orientations
 * and supports adaptive tessellation for seamless LOD transitions.
 */
NodePath
QCSPatchGenerator::make(LVector3d axes, TessellationInfo tessellation,
        double x0, double y0, double x1, double y1,
        bool inv_u, bool inv_v, bool swap_uv,
        bool x_inverted, bool y_inverted, bool xy_swap,
        bool has_offset, double offset,
        bool use_patch_adaptation, bool use_patch_skirts,
        double skirt_size, double skirt_uv,
        bool use_jacobian)
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
    if (use_jacobian) {
        array->add_column(InternalName::make("jacobian_params"), 3, Geom::NT_float32, Geom::C_other);
    } else {
        array->add_column(InternalName::get_tangent(), 3, Geom::NT_float32, Geom::C_vector);
        array->add_column(InternalName::get_binormal(), 3, Geom::NT_float32, Geom::C_vector);
    }
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
    GeomVertexWriter gjacobianw;
    GeomVertexWriter gtanw;
    GeomVertexWriter gbiw;
    if (use_jacobian) {
        gjacobianw = GeomVertexWriter(gvd, InternalName::make("jacobian_params"));
    } else {
        gtanw = GeomVertexWriter(gvd, InternalName::get_tangent());
        gbiw = GeomVertexWriter(gvd, InternalName::get_binormal());
    }
    PT(GeomTriangles) prim = new GeomTriangles(Geom::UH_static);

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
                    use_jacobian,
                    gvw, gtw, gnw, gtanw, gbiw,
                    gjacobianw);
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
                        use_jacobian,
                        gvw, gtw, gnw, gtanw, gbiw,
                        gjacobianw);
            }
        }
    }

    auto handle = prim->modify_vertices_handle(Thread::get_current_thread());
    handle->set_num_rows(nb_prims * 6);
    uint16_t *ptr = (uint16_t *)handle->get_write_pointer();
    if (use_patch_adaptation) {
        ptr = make_adapted_square_primitives(ptr, tessellation.inner, nb_vertices, tessellation.ratio);
        if (use_patch_skirts) {
            ptr = make_adapted_square_primitives_skirt(ptr, tessellation.inner, nb_vertices, tessellation.ratio);
        }
    } else {
        ptr = make_primitives(ptr, tessellation.inner, nb_vertices);
        if (use_patch_skirts) {
            ptr = make_primitives_skirt(ptr, tessellation.inner, nb_vertices);
        }
    }

    prim->close_primitive();
    geom->add_primitive(prim);
    node->add_geom(geom);

    _geom_collector.stop();

    return NodePath(node);
}

// ============================================================================
// ImprovedQCSPatchGenerator Implementation
// ============================================================================

ImprovedQCSPatchGenerator::ImprovedQCSPatchGenerator()
{
}

/**
 * @brief Computes offset vector using improved equal-area QCS mapping.
 *
 * Uses a modified cube-to-sphere projection that provides better area uniformity
 * than standard QCS. The mapping uses the formula:
 * x' = x * sqrt(1 - y^2/2 - z^2/2 + y^2z^2/3)
 * y' = y * sqrt(1 - z^2/2 - x^2/2 + z^2x^2/3)
 * z' = z * sqrt(1 - x^2/2 - y^2/2 + x^2y^2/3)
 *
 * This results in more uniform triangle sizes across the sphere surface compared
 * to the simple normalization used in standard QCS.
 */
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

/**
 * @brief Computes surface normal using improved equal-area QCS mapping.
 *
 * Calculates normal vector using the improved projection formula for better
 * area uniformity. The normal computation accounts for the modified mapping
 * to ensure correct lighting.
 */
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

/**
 * @brief Generates a single vertex with all attributes for improved QCS patch.
 *
 * Helper method that computes and writes all vertex attributes using the
 * improved equal-area mapping. Ensures consistent vertex generation across
 * the patch with proper tangent space calculation.
 */
void
ImprovedQCSPatchGenerator::make_point(LVector3d axes,
        double u, double v,
        double x0, double y0, double dx, double dy,
        LVector3d normal_coefs,
        bool inv_u, bool inv_v, bool swap_uv,
        bool has_offset, LVector3d offset_vector,
        bool use_jacobian,
        GeomVertexWriter &gvw, GeomVertexWriter &gtw, GeomVertexWriter &gnw, GeomVertexWriter &gtanw,
        GeomVertexWriter &gbiw, GeomVertexWriter &gjacobianw)
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
    if (use_jacobian) {
        gjacobianw.add_data4d(x, y, sqrt(0.5 - x * x / 6), sqrt(0.5 - y * y / 6));;
    } else {
        LVector3d tangent(1.0, x * y * (z2 / 3.0 - 0.5), x * z * (y2 / 3.0 - 0.5));
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
}

/**
 * @brief Generates a complete improved QCS patch with adaptive tessellation.
 *
 * Main method for creating improved QCS patches. Uses the equal-area mapping
 * for better mesh uniformity. Supports all the same features as standard QCS
 * (adaptive tessellation, skirts, layering) but with improved triangle size
 * distribution across the sphere.
 */
NodePath
ImprovedQCSPatchGenerator::make(LVector3d axes, TessellationInfo tessellation,
        double x0, double y0, double x1, double y1,
        bool inv_u, bool inv_v, bool swap_uv,
        bool x_inverted, bool y_inverted, bool xy_swap,
        bool has_offset, double offset,
        bool use_patch_adaptation, bool use_patch_skirts,
        double skirt_size, double skirt_uv,
        bool use_jacobian)
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
    if (use_jacobian) {
        array->add_column(InternalName::make("jacobian_params"), 4, Geom::NT_float32, Geom::C_other);
    } else {
        array->add_column(InternalName::get_tangent(), 3, Geom::NT_float32, Geom::C_vector);
        array->add_column(InternalName::get_binormal(), 3, Geom::NT_float32, Geom::C_vector);
    }
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
    GeomVertexWriter gjacobianw;
    GeomVertexWriter gtanw;
    GeomVertexWriter gbiw;
    if (use_jacobian) {
        gjacobianw = GeomVertexWriter(gvd, InternalName::make("jacobian_params"));
    } else {
        gtanw = GeomVertexWriter(gvd, InternalName::get_tangent());
        gbiw = GeomVertexWriter(gvd, InternalName::get_binormal());
    }
    PT(GeomTriangles) prim = new GeomTriangles(Geom::UH_static);

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
                    use_jacobian,
                    gvw, gtw, gnw, gtanw, gbiw, gjacobianw);
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
                        use_jacobian,
                        gvw, gtw, gnw, gtanw, gbiw, gjacobianw);
            }
        }
    }

    auto handle = prim->modify_vertices_handle(Thread::get_current_thread());
    handle->set_num_rows(nb_prims * 6);
    uint16_t *ptr = (uint16_t *)handle->get_write_pointer();
    if (use_patch_adaptation) {
        ptr = make_adapted_square_primitives(ptr, tessellation.inner, nb_vertices, tessellation.ratio);
        if (use_patch_skirts) {
            ptr = make_adapted_square_primitives_skirt(ptr, tessellation.inner, nb_vertices, tessellation.ratio);
        }
    } else {
        ptr = make_primitives(ptr, tessellation.inner, nb_vertices);
        if (use_patch_skirts) {
            ptr = make_primitives_skirt(ptr, tessellation.inner, nb_vertices);
        }
    }

    prim->close_primitive();
    geom->add_primitive(prim);
    node->add_geom(geom);

    _geom_collector.stop();

    return NodePath(node);
}

// ============================================================================
// TilePatchGenerator Implementation
// ============================================================================

TilePatchGenerator::TilePatchGenerator()
{
}

/**
 * @brief Generates a single vertex for a flat tile patch.
 *
 * Helper method that creates vertex attributes for planar geometry. The tile
 * lies in the XY plane with a constant upward normal. Tangent and binormal
 * vectors align with the X and Y axes respectively.
 */
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

/**
 * @brief Generates a complete flat tile patch with adaptive tessellation.
 *
 * Creates a rectangular planar tile suitable for heightfield terrain. The tile
 * is centered at the origin and lies in the XY plane. Vertices can be displaced
 * in Z by vertex shaders or heightfield data.
 *
 * Features adaptive tessellation and edge skirts.
 */
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

    auto handle = prim->modify_vertices_handle(Thread::get_current_thread());
    handle->set_num_rows(nb_prims * 6);
    uint16_t *ptr = (uint16_t *)handle->get_write_pointer();
    if (use_patch_adaptation) {
        ptr = make_adapted_square_primitives(ptr, tessellation.inner, nb_vertices, tessellation.ratio);
        if (use_patch_skirts) {
            ptr = make_adapted_square_primitives_skirt(ptr, tessellation.inner, nb_vertices, tessellation.ratio);
        }
    } else {
        ptr = make_primitives(ptr, tessellation.inner, nb_vertices);
        if (use_patch_skirts) {
            ptr = make_primitives_skirt(ptr, tessellation.inner, nb_vertices);
        }
    }

    prim->close_primitive();
    geom->add_primitive(prim);
    node->add_geom(geom);

    _geom_collector.stop();

    return NodePath(node);
}
