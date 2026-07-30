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


from typing import Any, Dict, List, TextIO


class EggWriter:
    """Writer for Panda3D EGG file format."""

    def __init__(self):
        self.indent_level = 0
        self.indent_str = "  "

    def write(self, filepath: str, model_data: Dict[str, Any]):
        """Write model data to an EGG file."""
        with open(filepath, 'w') as f:
            self._write_header(f)
            self._write_materials(f, model_data.get('materials', []))
            self._write_meshes(f, model_data)

    def _write_header(self, f: TextIO):
        """Write EGG file header."""
        f.write('<CoordinateSystem> { Z-up }\n\n')

    def _indent(self) -> str:
        """Get current indentation string."""
        return self.indent_str * self.indent_level

    def _write_materials(self, f: TextIO, materials: List[Dict[str, Any]]):
        """Write material definitions."""
        for i, mat in enumerate(materials):
            self._write_material(f, mat, i)

    def _write_material(self, f: TextIO, material: Dict[str, Any], index: int):
        """Write a single material."""
        mat_name = f"material_{index}"

        f.write(f'<Material> {mat_name} {{\n')
        self.indent_level += 1

        # Write diffuse color
        diffuse = material.get('diffuse', (1.0, 1.0, 1.0))
        f.write(f'{self._indent()}<Scalar> diffr {{ {diffuse[0]} }}\n')
        f.write(f'{self._indent()}<Scalar> diffg {{ {diffuse[1]} }}\n')
        f.write(f'{self._indent()}<Scalar> diffb {{ {diffuse[2]} }}\n')

        # Write diffuse alpha (opacity)
        opacity = material.get('opacity', 1.0)
        f.write(f'{self._indent()}<Scalar> diffa {{ {opacity} }}\n')

        # Write specular color
        specular = material.get('specular', (0.0, 0.0, 0.0))
        f.write(f'{self._indent()}<Scalar> specr {{ {specular[0]} }}\n')
        f.write(f'{self._indent()}<Scalar> specg {{ {specular[1]} }}\n')
        f.write(f'{self._indent()}<Scalar> specb {{ {specular[2]} }}\n')

        # Write specular power (shininess)
        specpower = material.get('specpower', 1.0)
        # EGG uses shininess in range 0-128, CMOD uses different scale
        # We clamp to 128.0 to stay within EGG's valid range
        shininess = min(128.0, specpower)
        f.write(f'{self._indent()}<Scalar> shininess {{ {shininess} }}\n')

        # Write emissive color
        emissive = material.get('emissive', (0.0, 0.0, 0.0))
        if emissive != (0.0, 0.0, 0.0):
            f.write(f'{self._indent()}<Scalar> emitr {{ {emissive[0]} }}\n')
            f.write(f'{self._indent()}<Scalar> emitg {{ {emissive[1]} }}\n')
            f.write(f'{self._indent()}<Scalar> emitb {{ {emissive[2]} }}\n')

        self.indent_level -= 1
        f.write('}\n\n')

        # Write textures
        textures = material.get('textures', [])
        for tex in textures:
            self._write_texture(f, tex, mat_name, index)

    def _write_texture(self, f: TextIO, texture: Dict[str, Any], mat_name: str, mat_index: int):
        """Write texture definition."""
        tex_path = texture.get('path', '')
        if not tex_path:
            return

        tex_name = f"texture_{mat_index}"

        f.write(f'<Texture> {tex_name} {{\n')
        self.indent_level += 1

        f.write(f'{self._indent()}"{tex_path}"\n')
        f.write(f'{self._indent()}<Scalar> envtype {{ modulate }}\n')
        f.write(f'{self._indent()}<Scalar> minfilter {{ linear_mipmap_linear }}\n')
        f.write(f'{self._indent()}<Scalar> magfilter {{ linear }}\n')
        f.write(f'{self._indent()}<Scalar> wrap {{ repeat }}\n')

        self.indent_level -= 1
        f.write('}\n\n')

    def _write_meshes(self, f: TextIO, model_data: Dict[str, Any]):
        """Write all meshes."""
        meshes = model_data.get('meshes', [])
        materials = model_data.get('materials', [])

        for mesh_idx, mesh in enumerate(meshes):
            self._write_mesh(f, mesh, mesh_idx, materials)

    def _write_mesh(self, f: TextIO, mesh: Dict[str, Any], mesh_idx: int, materials: List[Dict[str, Any]]):
        """Write a single mesh."""
        group_name = f"mesh_{mesh_idx}"

        f.write(f'<Group> {group_name} {{\n')
        self.indent_level += 1

        # Write vertex pool
        self._write_vertex_pool(f, mesh, mesh_idx)

        # Write polygon groups
        self._write_polygon_groups(f, mesh, mesh_idx, materials)

        self.indent_level -= 1
        f.write('}\n\n')

    def _write_vertex_pool(self, f: TextIO, mesh: Dict[str, Any], mesh_idx: int):
        """Write vertex pool."""
        pool_name = f"vpool_{mesh_idx}"
        vertices = mesh.get('vertices', [])

        f.write(f'{self._indent()}<VertexPool> {pool_name} {{\n')
        self.indent_level += 1

        for i, vertex in enumerate(vertices):
            self._write_vertex(f, vertex, i)

        self.indent_level -= 1
        f.write(f'{self._indent()}}}\n\n')

    def _write_vertex(self, f: TextIO, vertex: Dict[str, Any], index: int):
        """Write a single vertex."""
        f.write(f'{self._indent()}<Vertex> {index} {{\n')
        self.indent_level += 1

        # Write position
        pos = vertex.get('position', (0.0, 0.0, 0.0))
        f.write(f'{self._indent()}{pos[0]} {pos[1]} {pos[2]}\n')

        # Write normal if available
        normal = vertex.get('normal')
        if normal:
            f.write(f'{self._indent()}<Normal> {{ {normal[0]} {normal[1]} {normal[2]} }}\n')

        # Write UV coordinates if available
        texcoord = vertex.get('texcoord0')
        if texcoord:
            f.write(f'{self._indent()}<UV> {{ {texcoord[0]} {texcoord[1]} }}\n')

        # Write color if available
        color = vertex.get('color0')
        if color:
            if len(color) == 4:
                f.write(f'{self._indent()}<RGBA> {{ {color[0]} {color[1]} {color[2]} {color[3]} }}\n')
            else:
                f.write(f'{self._indent()}<RGBA> {{ {color[0]} {color[1]} {color[2]} 1.0 }}\n')

        self.indent_level -= 1
        f.write(f'{self._indent()}}}\n')

    def _write_polygon_groups(self, f: TextIO, mesh: Dict[str, Any], mesh_idx: int, materials: List[Dict[str, Any]]):
        """Write polygon groups."""
        groups = mesh.get('groups', [])
        pool_name = f"vpool_{mesh_idx}"

        for group_idx, group in enumerate(groups):
            self._write_polygon_group(f, group, group_idx, pool_name, materials)

    def _write_polygon_group(
        self, f: TextIO, group: Dict[str, Any], group_idx: int, pool_name: str, materials: List[Dict[str, Any]]
    ):
        """Write a single polygon group."""
        from .cmod_parser import CMODParser

        prim_type = group.get('type', CMODParser.PRIM_TRILIST)
        mat_index = group.get('material', 0)
        indices = group.get('indices', [])

        f.write(f'{self._indent()}<Group> {{\n')
        self.indent_level += 1

        # Apply material reference if available
        attributes = []
        if mat_index < len(materials):
            mat_name = f"material_{mat_index}"
            attributes.append(f'<MRef> {{ {mat_name} }}')

            # Write texture reference if material has texture
            textures = materials[mat_index].get('textures', [])
            if textures:
                tex_name = f"texture_{mat_index}"
                attributes.append(f'<TRef> {{ {tex_name} }}')

        # Convert primitives to polygons/lines/points
        if prim_type == CMODParser.PRIM_TRILIST:
            # Triangle list: every 3 indices form a triangle
            for i in range(0, len(indices), 3):
                if i + 2 < len(indices):
                    self._write_polygon(f, pool_name, indices[i : i + 3], attributes)

        elif prim_type == CMODParser.PRIM_TRISTRIP:
            # Triangle strip: vertices form a strip
            for i in range(len(indices) - 2):
                if i % 2 == 0:
                    # Even triangle: normal order
                    tri = [indices[i], indices[i + 1], indices[i + 2]]
                else:
                    # Odd triangle: reverse order to maintain winding
                    tri = [indices[i], indices[i + 2], indices[i + 1]]
                self._write_polygon(f, pool_name, tri)

        elif prim_type == CMODParser.PRIM_TRIFAN:
            # Triangle fan: first vertex is shared by all triangles
            if len(indices) >= 3:
                first = indices[0]
                for i in range(1, len(indices) - 1):
                    tri = [first, indices[i], indices[i + 1]]
                    self._write_polygon(f, pool_name, tri, attributes)

        elif prim_type == CMODParser.PRIM_LINELIST:
            # Line list: every 2 indices form a line
            for i in range(0, len(indices), 2):
                if i + 1 < len(indices):
                    self._write_line(f, pool_name, [indices[i], indices[i + 1]], attributes)

        elif prim_type == CMODParser.PRIM_LINESTRIP:
            # Line strip: consecutive vertices form lines
            for i in range(len(indices) - 1):
                self._write_line(f, pool_name, [indices[i], indices[i + 1]], attributes)

        elif prim_type == CMODParser.PRIM_POINTS:
            # Points: each index is a point
            for idx in indices:
                self._write_point(f, pool_name, idx, attributes)

        self.indent_level -= 1
        f.write(f'{self._indent()}}}\n')

    def _write_polygon(self, f: TextIO, pool_name: str, indices: List[int], attributes: List[str]):
        """Write a single polygon."""
        f.write(f'{self._indent()}<Polygon> {{\n')
        self.indent_level += 1

        for attr in attributes:
            f.write(f'{self._indent()}{attr}\n')

        for idx in indices:
            f.write(f'{self._indent()}<VertexRef> {{ {idx} <Ref> {{ {pool_name} }} }}\n')

        self.indent_level -= 1
        f.write(f'{self._indent()}}}\n')

    def _write_line(self, f: TextIO, pool_name: str, indices: List[int], attributes: List[str]):
        """Write a single line."""
        f.write(f'{self._indent()}<Line> {{\n')
        self.indent_level += 1

        for attr in attributes:
            f.write(f'{self._indent()}{attr}\n')

        for idx in indices:
            f.write(f'{self._indent()}<VertexRef> {{ {idx} <Ref> {{ {pool_name} }} }}\n')

        self.indent_level -= 1
        f.write(f'{self._indent()}}}\n')

    def _write_point(self, f: TextIO, pool_name: str, index: int, attributes: List[str]):
        """Write a single point."""
        f.write(f'{self._indent()}<Point> {{\n')
        self.indent_level += 1

        for attr in attributes:
            f.write(f'{self._indent()}{attr}\n')

            f.write(f'{self._indent()}<VertexRef> {{ {index} <Ref> {{ {pool_name} }} }}\n')

        self.indent_level -= 1
        f.write(f'{self._indent()}}}\n')
