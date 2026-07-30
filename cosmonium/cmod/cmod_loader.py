#
# This file is part of Cosmonium.
#
# Copyright (C) 2018-2025 Laurent Deru.
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


from __future__ import annotations

import builtins
import os

from panda3d.core import (
    ColorBlendAttrib,
    CS_default,
    CS_yup_right,
    Filename,
    Geom,
    GeomLines,
    GeomLinestrips,
    GeomNode,
    GeomPoints,
    GeomTriangles,
    GeomTristrips,
    GeomVertexData,
    GeomVertexFormat,
    GeomVertexWriter,
    LMatrix4,
    Material,
    MaterialAttrib,
    ModelRoot,
    RenderState,
    Texture,
    TextureAttrib,
    TextureStage,
    TransparencyAttrib,
)

from .cmod_parser import CMODParser


class CmodLoader:
    """Direct loader for CMOD files that bypasses EGG generation."""

    name = 'Celestia Model'
    extensions = ['cmod']
    supports_compressed = False

    def load_file(self, path, options, record=None):
        """Load a CMOD file directly into Panda3D scene graph."""
        if isinstance(path, Filename):
            filepath = path.to_os_specific()
        else:
            filepath = str(path)

        try:
            # Parse CMOD file
            parser = CMODParser()
            model_data = parser.parse(filepath)

            # Create root node
            root = ModelRoot('cmod')

            # CMOD are Y-Up and Panda3D is using Z-Up by default
            self.csxform = LMatrix4.convert_mat(CS_yup_right, CS_default)

            # Get base directory for relative texture paths
            base_dir = os.path.dirname(filepath)

            # Build materials (returns list of tuples: (material, textures, blend_mode))
            materials = []
            for mat_data in model_data.get('materials', []):
                material_info = self._create_material(mat_data, base_dir)
                materials.append(material_info)

            # Build meshes
            for mesh_idx, mesh_data in enumerate(model_data.get('meshes', [])):
                geom_node = self._create_geom_node(mesh_data, materials, mesh_idx)
                if geom_node:
                    root.add_child(geom_node)

            return root

        except Exception as e:
            print(f"Failed to load CMOD file '{filepath}': {e}")
            import traceback

            traceback.print_exc()
            return None

    def _create_material(self, mat_data: dict, base_dir: str) -> tuple[Material, tuple[int, Texture], int]:
        """Create a Panda3D Material from CMOD material data.

        Returns a tuple of (material, textures, blend_mode) where:
        - material: Panda3D Material object
        - textures: list of (texture_semantic, Texture object) tuples
        - blend_mode: integer blend mode value (0=opaque, 1=additive, 2=premultiplied alpha)
        """
        material = Material()

        # Set diffuse color
        diffuse = mat_data.get('diffuse', (1.0, 1.0, 1.0))
        opacity = mat_data.get('opacity', 1.0)
        material.set_diffuse((diffuse[0], diffuse[1], diffuse[2], opacity))

        # Set specular color
        specular = mat_data.get('specular', (0.0, 0.0, 0.0))
        material.set_specular((specular[0], specular[1], specular[2], 1.0))

        # Set shininess
        specpower = mat_data.get('specpower', 1.0)
        shininess = min(128.0, specpower)
        material.set_shininess(shininess)

        # Set emissive color
        emissive = mat_data.get('emissive', (0.0, 0.0, 0.0))
        material.set_emission((emissive[0], emissive[1], emissive[2], 1.0))

        # Load textures
        textures = []
        loader = builtins.base.loader
        for tex_data in mat_data.get('textures', []):
            tex_path = tex_data.get('path', '')
            tex_type = tex_data.get('type', 0)  # texture semantic (0=diffuse, etc.)

            if tex_path:
                # Try to resolve texture path relative to model directory
                full_path = os.path.join(base_dir, tex_path)

                if os.path.exists(full_path):
                    try:
                        texture = loader.loadTexture(Filename.from_os_specific(full_path))
                        if texture:
                            textures.append((tex_type, texture))
                    except Exception as e:
                        print(f"Warning: Failed to load texture '{tex_path}': {e}")
                else:
                    # Try as celestia hierarchy
                    for res in ('hires', 'medres', 'lores'):
                        full_path = os.path.join(base_dir, '../textures', res, tex_path)
                        if os.path.exists(full_path):
                            try:
                                texture = loader.loadTexture(Filename.from_os_specific(full_path))
                                if texture:
                                    textures.append((tex_type, texture))
                                    break
                            except Exception as e:
                                print(f"Warning: Failed to load texture '{tex_path}': {e}")
                    else:
                        print(f"Warning: Failed to find texture '{tex_path}'")

        # Get blend mode
        blend_mode = mat_data.get('blend', 0)

        return (material, textures, blend_mode)

    def _create_geom_node(self, mesh_data: dict, materials: list[Material], mesh_idx: int) -> GeomNode:
        """Create a GeomNode from CMOD mesh data."""
        vertices = mesh_data.get('vertices', [])
        if not vertices:
            return None

        vertex_desc = mesh_data.get('vertex_desc', [])
        groups = mesh_data.get('groups', [])

        # Create GeomNode
        geom_node = GeomNode(f"mesh_{mesh_idx}")

        # Determine vertex format based on attributes
        has_normal = any(attr['semantic'] == CMODParser.NORMAL for attr in vertex_desc)
        has_texcoord = any(attr['semantic'] == CMODParser.TEXCOORD0 for attr in vertex_desc)

        # Use appropriate format
        if has_texcoord and has_normal:
            format = GeomVertexFormat.get_v3n3t2()
        elif has_normal:
            format = GeomVertexFormat.get_v3n3()
        elif has_texcoord:
            format = GeomVertexFormat.get_v3t2()
        else:
            format = GeomVertexFormat.get_v3()

        # Create vertex data
        vdata = GeomVertexData(f"vertices_{mesh_idx}", format, Geom.UH_static)
        vdata.set_num_rows(len(vertices))

        # Writers for vertex attributes
        vertex_writer = GeomVertexWriter(vdata, 'vertex')
        normal_writer = GeomVertexWriter(vdata, 'normal') if has_normal else None
        texcoord_writer = GeomVertexWriter(vdata, 'texcoord') if has_texcoord else None

        # Write vertex data
        for vertex in vertices:
            pos = vertex.get('position', (0.0, 0.0, 0.0))
            vertex_writer.add_data3(pos[0], pos[1], pos[2])

            if normal_writer:
                normal = vertex.get('normal', (0.0, 0.0, 1.0))
                normal_writer.add_data3(normal[0], normal[1], normal[2])

            if texcoord_writer:
                texcoord = vertex.get('texcoord0', (0.0, 0.0))
                texcoord_writer.add_data2(texcoord[0], texcoord[1])

        # Create primitives for each group
        for group in groups:
            prim_type = group.get('type', CMODParser.PRIM_TRILIST)
            indices = group.get('indices', [])
            mat_index = group.get('material', 0)

            if prim_type == CMODParser.PRIM_TRILIST:
                prim = GeomTriangles(Geom.UH_static)
                for i in range(0, len(indices), 3):
                    if i + 2 < len(indices):
                        prim.add_vertices(indices[i], indices[i + 1], indices[i + 2])

            elif prim_type == CMODParser.PRIM_TRISTRIP:
                prim = GeomTristrips(Geom.UH_static)
                for idx in indices:
                    prim.add_vertex(idx)
                prim.close_primitive()

            elif prim_type == CMODParser.PRIM_TRIFAN:
                # Convert triangle fan to triangle list
                prim = GeomTriangles(Geom.UH_static)
                if len(indices) >= 3:
                    first = indices[0]
                    for i in range(1, len(indices) - 1):
                        prim.add_vertices(first, indices[i], indices[i + 1])

            elif prim_type == CMODParser.PRIM_LINELIST:
                # Line list: every 2 indices form a line
                prim = GeomLines(Geom.UH_static)
                for i in range(0, len(indices), 2):
                    if i + 1 < len(indices):
                        prim.add_vertices(indices[i], indices[i + 1])

            elif prim_type == CMODParser.PRIM_LINESTRIP:
                # Line strip: consecutive vertices form a strip
                prim = GeomLinestrips(Geom.UH_static)
                for idx in indices:
                    prim.add_vertex(idx)
                prim.close_primitive()

            elif prim_type == CMODParser.PRIM_POINTS:
                # Points: each index is a point
                prim = GeomPoints(Geom.UH_static)
                for idx in indices:
                    prim.add_vertex(idx)

            else:
                # Unsupported primitive type, skip
                prim = None

            if prim is None:
                continue

            # Create geom and add to node
            geom = Geom(vdata)
            geom.add_primitive(prim)
            geom_index = geom_node.get_num_geoms()
            geom.transform_vertices(self.csxform)
            geom_node.add_geom(geom)

            # Apply material if available
            if mat_index < len(materials) and materials[mat_index] is not None:
                material, textures, blend_mode = materials[mat_index]

                # Start with material attribute
                attribs = [MaterialAttrib.make(material)]

                # Apply textures
                if textures:
                    tex_attrib = TextureAttrib.make()
                    for tex_type, texture in textures:
                        texstage = TextureStage(str(tex_type))
                        if tex_type == CMODParser.TEXTURE_DIFFUSE:
                            texstage.set_mode(TextureStage.M_modulate)
                        elif tex_type == CMODParser.TEXTURE_NORMAL:
                            texstage.set_mode(TextureStage.M_normal)
                        elif tex_type == CMODParser.TEXTURE_SPECULAR:
                            texstage.set_mode(TextureStage.M_gloss)
                        elif tex_type == CMODParser.TEXTURE_EMISSIVE:
                            texstage.set_mode(TextureStage.M_glow)
                        else:
                            print(f"WARNING, unknown texture type {tex_type}")
                            continue
                        tex_attrib = tex_attrib.add_on_stage(texstage, texture)
                    attribs.append(tex_attrib)

                # Apply blend mode (transparency)
                # CMOD blend modes: 0=opaque, 1=additive, 2=premultiplied alpha
                if blend_mode == 1:
                    # Additive blending
                    attribs.append(TransparencyAttrib.make(TransparencyAttrib.M_alpha))
                    attribs.append(
                        ColorBlendAttrib.make(
                            ColorBlendAttrib.M_add, ColorBlendAttrib.O_incoming_alpha, ColorBlendAttrib.O_one
                        )
                    )
                elif blend_mode == 2:
                    # Premultiplied alpha
                    attribs.append(TransparencyAttrib.make(TransparencyAttrib.M_premultiplied_alpha))
                elif blend_mode != 0:
                    # Any other non-zero blend mode, use standard alpha
                    attribs.append(TransparencyAttrib.make(TransparencyAttrib.M_alpha))

                # Create render state with all attributes
                render_state = RenderState.make(*attribs)
                geom_node.set_geom_state(geom_index, render_state)

        return geom_node
