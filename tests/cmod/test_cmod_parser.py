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


"""
Unit tests for CMOD parser.

This module contains comprehensive tests for both binary and ASCII CMOD format parsing,
including materials, vertices, and all primitive types (triangles, lines, points).
"""

import os
import struct
import tempfile

import pytest

from cosmonium.cmod.cmod_parser import CMODParser


class TestCMODParserBinary:
    """Tests for binary CMOD format parsing."""

    def create_binary_cmod(self, filepath, include_material=True, include_mesh=True):
        """Helper to create a binary CMOD file for testing."""
        with open(filepath, 'wb') as f:
            # Write magic header
            f.write(b'#celmodel_binary')

            if include_material:
                # Material
                f.write(struct.pack('<H', 1001))  # TOKEN_MATERIAL
                f.write(struct.pack('<H', 1003))  # TOKEN_DIFFUSE
                f.write(struct.pack('<H', 7))  # CMOD_Color data type
                f.write(struct.pack('<fff', 0.8, 0.8, 0.8))
                f.write(struct.pack('<H', 1004))  # TOKEN_SPECULAR
                f.write(struct.pack('<H', 7))  # CMOD_Color data type
                f.write(struct.pack('<fff', 0.2, 0.2, 0.2))
                f.write(struct.pack('<H', 1005))  # TOKEN_SPECPOWER
                f.write(struct.pack('<H', 1))  # CMOD_Float1 data type
                f.write(struct.pack('<f', 32.0))
                f.write(struct.pack('<H', 1002))  # TOKEN_END_MATERIAL

            if include_mesh:
                # Mesh
                f.write(struct.pack('<H', 1009))  # TOKEN_MESH
                f.write(struct.pack('<H', 1011))  # TOKEN_VERTEXDESC
                f.write(struct.pack('<HH', 0, 2))  # POSITION, FORMAT_FLOAT3
                f.write(struct.pack('<HH', 3, 2))  # NORMAL, FORMAT_FLOAT3
                f.write(struct.pack('<H', 1012))  # TOKEN_END_VERTEXDESC
                f.write(struct.pack('<H', 1013))  # TOKEN_VERTICES
                f.write(struct.pack('<I', 3))  # 3 vertices

                # Vertices
                for x, y in [(0, 0), (1, 0), (0.5, 1)]:
                    f.write(struct.pack('<fff', x, y, 0.0))  # Position
                    f.write(struct.pack('<fff', 0.0, 0.0, 1.0))  # Normal

                # Triangle
                f.write(struct.pack('<H', 0))  # PRIM_TRILIST
                f.write(struct.pack('<I', 0))  # Material 0
                f.write(struct.pack('<I', 3))  # 3 indices
                f.write(struct.pack('<III', 0, 1, 2))

                f.write(struct.pack('<H', 1010))  # TOKEN_END_MESH

    def test_parse_binary_magic_header(self):
        """Test binary CMOD magic header recognition."""
        parser = CMODParser()
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.cmod') as f:
            f.write(b'#celmodel_binary')
            filepath = f.name

        try:
            # Should not raise an error
            result = parser.parse(filepath)
            assert result is not None
            assert 'materials' in result
            assert 'meshes' in result
        finally:
            os.unlink(filepath)

    def test_parse_binary_material(self):
        """Test parsing binary material definitions."""
        parser = CMODParser()
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.cmod') as f:
            filepath = f.name

        try:
            self.create_binary_cmod(filepath, include_material=True, include_mesh=False)
            result = parser.parse(filepath)

            assert len(result['materials']) == 1
            material = result['materials'][0]

            assert 'diffuse' in material
            assert len(material['diffuse']) == 3
            assert material['diffuse'][0] == pytest.approx(0.8, rel=1e-5)

            assert 'specular' in material
            assert material['specular'][0] == pytest.approx(0.2, rel=1e-5)

            assert 'specpower' in material
            assert material['specpower'] == pytest.approx(32.0, rel=1e-5)
        finally:
            os.unlink(filepath)

    def test_parse_binary_mesh_vertices(self):
        """Test parsing binary mesh vertices."""
        parser = CMODParser()
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.cmod') as f:
            filepath = f.name

        try:
            self.create_binary_cmod(filepath, include_material=False, include_mesh=True)
            result = parser.parse(filepath)

            assert len(result['meshes']) == 1
            mesh = result['meshes'][0]

            assert 'vertices' in mesh
            assert len(mesh['vertices']) == 3

            # Check first vertex
            vertex = mesh['vertices'][0]
            assert 'position' in vertex
            assert vertex['position'] == pytest.approx((0.0, 0.0, 0.0))
            assert 'normal' in vertex
            assert vertex['normal'] == pytest.approx((0.0, 0.0, 1.0))
        finally:
            os.unlink(filepath)

    def test_parse_binary_mesh_primitives(self):
        """Test parsing binary mesh primitives."""
        parser = CMODParser()
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.cmod') as f:
            filepath = f.name

        try:
            self.create_binary_cmod(filepath, include_material=False, include_mesh=True)
            result = parser.parse(filepath)

            mesh = result['meshes'][0]
            assert 'groups' in mesh
            assert len(mesh['groups']) == 1

            group = mesh['groups'][0]
            assert group['type'] == 0  # PRIM_TRILIST
            assert group['material'] == 0
            assert group['indices'] == [0, 1, 2]
        finally:
            os.unlink(filepath)

    def test_parse_binary_with_texture(self):
        """Test parsing binary material with texture."""
        parser = CMODParser()
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.cmod') as f:
            # Write complete CMOD with texture
            f.write(b'#celmodel_binary')
            f.write(struct.pack('<H', 1001))  # TOKEN_MATERIAL
            f.write(struct.pack('<H', 1003))  # TOKEN_DIFFUSE
            f.write(struct.pack('<H', 7))  # CMOD_Color data type
            f.write(struct.pack('<fff', 1.0, 1.0, 1.0))
            f.write(struct.pack('<H', 1007))  # TOKEN_TEXTURE
            f.write(struct.pack('<H', 0))  # Texture semantic (uint16, no data type)
            f.write(struct.pack('<H', 5))  # CMOD_String data type for path
            tex_path = b'test.png'
            f.write(struct.pack('<H', len(tex_path)))  # String length (uint16)
            f.write(tex_path)
            f.write(struct.pack('<H', 1002))  # TOKEN_END_MATERIAL
            filepath = f.name

        try:
            result = parser.parse(filepath)
            assert len(result['materials']) == 1
            material = result['materials'][0]

            assert 'textures' in material
            assert len(material['textures']) == 1
            assert material['textures'][0]['path'] == 'test.png'
            assert material['textures'][0]['type'] == 0
        finally:
            os.unlink(filepath)

    def test_invalid_magic_header(self):
        """Test that invalid magic header raises error."""
        parser = CMODParser()
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.cmod') as f:
            f.write(b'invalid_header_data')
            filepath = f.name

        try:
            with pytest.raises(ValueError, match="Invalid CMOD file"):
                parser.parse(filepath)
        finally:
            os.unlink(filepath)


class TestCMODParserASCII:
    """Tests for ASCII CMOD format parsing."""

    def create_ascii_cmod(self, filepath, primitives='trilist'):
        """Helper to create an ASCII CMOD file for testing."""
        with open(filepath, 'w') as f:
            f.write("#celmodel_ascii\n\n")

            # Material
            f.write("material\n")
            f.write("diffuse 0.8 0.8 0.8\n")
            f.write("specular 0.2 0.2 0.2\n")
            f.write("specpower 32.0\n")
            f.write("end_material\n\n")

            # Mesh
            f.write("mesh\n")
            f.write("vertexdesc\n")
            f.write("position f3\n")
            f.write("normal f3\n")
            f.write("end_vertexdesc\n")
            f.write("vertices 3\n")
            f.write("0.0 0.0 0.0  0.0 0.0 1.0\n")
            f.write("1.0 0.0 0.0  0.0 0.0 1.0\n")
            f.write("0.5 1.0 0.0  0.0 0.0 1.0\n")

            if primitives == 'trilist':
                f.write("trilist 0 3\n")
                f.write("0 1 2\n")
            elif primitives == 'linelist':
                f.write("linelist 0 2\n")
                f.write("0 1\n")
            elif primitives == 'points':
                f.write("points 0 1\n")
                f.write("0\n")

            f.write("end_mesh\n")

    def test_parse_ascii_magic_header(self):
        """Test ASCII CMOD magic header recognition."""
        parser = CMODParser()
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.cmod') as f:
            f.write("#celmodel_ascii\n")
            filepath = f.name

        try:
            result = parser.parse(filepath)
            assert result is not None
            assert 'materials' in result
            assert 'meshes' in result
        finally:
            os.unlink(filepath)

    def test_parse_ascii_material(self):
        """Test parsing ASCII material definitions."""
        parser = CMODParser()
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.cmod') as f:
            filepath = f.name

        try:
            self.create_ascii_cmod(filepath)
            result = parser.parse(filepath)

            assert len(result['materials']) == 1
            material = result['materials'][0]

            assert material['diffuse'] == pytest.approx((0.8, 0.8, 0.8))
            assert material['specular'] == pytest.approx((0.2, 0.2, 0.2))
            assert material['specpower'] == pytest.approx(32.0)
        finally:
            os.unlink(filepath)

    def test_parse_ascii_vertices(self):
        """Test parsing ASCII vertices."""
        parser = CMODParser()
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.cmod') as f:
            filepath = f.name

        try:
            self.create_ascii_cmod(filepath)
            result = parser.parse(filepath)

            mesh = result['meshes'][0]
            assert len(mesh['vertices']) == 3

            vertex = mesh['vertices'][0]
            assert vertex['position'] == pytest.approx((0.0, 0.0, 0.0))
            assert vertex['normal'] == pytest.approx((0.0, 0.0, 1.0))
        finally:
            os.unlink(filepath)

    def test_parse_ascii_trilist(self):
        """Test parsing ASCII triangle list primitive."""
        parser = CMODParser()
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.cmod') as f:
            filepath = f.name

        try:
            self.create_ascii_cmod(filepath, primitives='trilist')
            result = parser.parse(filepath)

            group = result['meshes'][0]['groups'][0]
            assert group['type'] == 0  # PRIM_TRILIST
            assert group['indices'] == [0, 1, 2]
        finally:
            os.unlink(filepath)

    def test_parse_ascii_linelist(self):
        """Test parsing ASCII line list primitive."""
        parser = CMODParser()
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.cmod') as f:
            filepath = f.name

        try:
            self.create_ascii_cmod(filepath, primitives='linelist')
            result = parser.parse(filepath)

            group = result['meshes'][0]['groups'][0]
            assert group['type'] == 3  # PRIM_LINELIST
            assert group['indices'] == [0, 1]
        finally:
            os.unlink(filepath)

    def test_parse_ascii_points(self):
        """Test parsing ASCII points primitive."""
        parser = CMODParser()
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.cmod') as f:
            filepath = f.name

        try:
            self.create_ascii_cmod(filepath, primitives='points')
            result = parser.parse(filepath)

            group = result['meshes'][0]['groups'][0]
            assert group['type'] == 5  # PRIM_POINTS
            assert group['indices'] == [0]
        finally:
            os.unlink(filepath)

    def test_parse_ascii_with_texture(self):
        """Test parsing ASCII material with texture."""
        parser = CMODParser()
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.cmod') as f:
            f.write("#celmodel_ascii\n\n")
            f.write("material\n")
            f.write("diffuse 1.0 1.0 1.0\n")
            f.write("texture0 \"test_texture.png\"\n")
            f.write("end_material\n")
            filepath = f.name

        try:
            result = parser.parse(filepath)
            material = result['materials'][0]

            assert len(material['textures']) == 1
            assert material['textures'][0]['path'] == 'test_texture.png'
        finally:
            os.unlink(filepath)

    def test_parse_ascii_with_comments(self):
        """Test parsing ASCII with comments."""
        parser = CMODParser()
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.cmod') as f:
            f.write("#celmodel_ascii\n")
            f.write("# This is a comment\n")
            f.write("material\n")
            f.write("# Another comment\n")
            f.write("diffuse 0.5 0.5 0.5\n")
            f.write("end_material\n")
            filepath = f.name

        try:
            result = parser.parse(filepath)
            assert len(result['materials']) == 1
            assert result['materials'][0]['diffuse'] == pytest.approx((0.5, 0.5, 0.5))
        finally:
            os.unlink(filepath)


class TestCMODParserVertexFormats:
    """Tests for different vertex attribute formats."""

    def test_parse_vertex_with_texcoords(self):
        """Test parsing vertices with texture coordinates."""
        parser = CMODParser()
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.cmod') as f:
            f.write(b'#celmodel_binary')
            f.write(struct.pack('<H', 1009))  # TOKEN_MESH
            f.write(struct.pack('<H', 1011))  # TOKEN_VERTEXDESC
            f.write(struct.pack('<HH', 0, 2))  # POSITION, FORMAT_FLOAT3
            f.write(struct.pack('<HH', 3, 2))  # NORMAL, FORMAT_FLOAT3
            f.write(struct.pack('<HH', 5, 1))  # TEXCOORD0, FORMAT_FLOAT2
            f.write(struct.pack('<H', 1012))  # TOKEN_END_VERTEXDESC
            f.write(struct.pack('<H', 1013))  # TOKEN_VERTICES
            f.write(struct.pack('<I', 1))  # 1 vertex
            f.write(struct.pack('<fff', 0.0, 0.0, 0.0))  # Position
            f.write(struct.pack('<fff', 0.0, 0.0, 1.0))  # Normal
            f.write(struct.pack('<ff', 0.5, 0.5))  # UV
            f.write(struct.pack('<H', 1010))  # TOKEN_END_MESH
            filepath = f.name

        try:
            result = parser.parse(filepath)
            vertex = result['meshes'][0]['vertices'][0]

            assert 'texcoord0' in vertex
            assert vertex['texcoord0'] == pytest.approx((0.5, 0.5))
        finally:
            os.unlink(filepath)

    def test_parse_vertex_with_color(self):
        """Test parsing vertices with color."""
        parser = CMODParser()
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.cmod') as f:
            f.write(b'#celmodel_binary')
            f.write(struct.pack('<H', 1009))  # TOKEN_MESH
            f.write(struct.pack('<H', 1011))  # TOKEN_VERTEXDESC
            f.write(struct.pack('<HH', 0, 2))  # POSITION, FORMAT_FLOAT3
            f.write(struct.pack('<HH', 1, 3))  # COLOR0, FORMAT_FLOAT4
            f.write(struct.pack('<H', 1012))  # TOKEN_END_VERTEXDESC
            f.write(struct.pack('<H', 1013))  # TOKEN_VERTICES
            f.write(struct.pack('<I', 1))  # 1 vertex
            f.write(struct.pack('<fff', 0.0, 0.0, 0.0))  # Position
            f.write(struct.pack('<ffff', 1.0, 0.0, 0.0, 1.0))  # Color (red)
            f.write(struct.pack('<H', 1010))  # TOKEN_END_MESH
            filepath = f.name

        try:
            result = parser.parse(filepath)
            vertex = result['meshes'][0]['vertices'][0]

            assert 'color0' in vertex
            assert vertex['color0'] == pytest.approx((1.0, 0.0, 0.0, 1.0))
        finally:
            os.unlink(filepath)


class TestCMODParserPrimitiveTypes:
    """Tests for all primitive types."""

    def create_mesh_with_primitive(self, filepath, prim_type, indices):
        """Helper to create a mesh with specific primitive type."""
        with open(filepath, 'wb') as f:
            f.write(b'#celmodel_binary')
            f.write(struct.pack('<H', 1009))  # TOKEN_MESH
            f.write(struct.pack('<H', 1011))  # TOKEN_VERTEXDESC
            f.write(struct.pack('<HH', 0, 2))  # POSITION, FORMAT_FLOAT3
            f.write(struct.pack('<H', 1012))  # TOKEN_END_VERTEXDESC
            f.write(struct.pack('<H', 1013))  # TOKEN_VERTICES
            f.write(struct.pack('<I', len(indices)))
            for _ in indices:
                f.write(struct.pack('<fff', 0.0, 0.0, 0.0))
            f.write(struct.pack('<H', prim_type))
            f.write(struct.pack('<I', 0))  # Material 0
            f.write(struct.pack('<I', len(indices)))
            for idx in indices:
                f.write(struct.pack('<I', idx))
            f.write(struct.pack('<H', 1010))  # TOKEN_END_MESH

    def test_parse_tristrip(self):
        """Test parsing triangle strip primitive."""
        parser = CMODParser()
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.cmod') as f:
            filepath = f.name

        try:
            self.create_mesh_with_primitive(filepath, 1, [0, 1, 2, 3])  # PRIM_TRISTRIP
            result = parser.parse(filepath)

            group = result['meshes'][0]['groups'][0]
            assert group['type'] == 1  # PRIM_TRISTRIP
            assert group['indices'] == [0, 1, 2, 3]
        finally:
            os.unlink(filepath)

    def test_parse_trifan(self):
        """Test parsing triangle fan primitive."""
        parser = CMODParser()
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.cmod') as f:
            filepath = f.name

        try:
            self.create_mesh_with_primitive(filepath, 2, [0, 1, 2, 3])  # PRIM_TRIFAN
            result = parser.parse(filepath)

            group = result['meshes'][0]['groups'][0]
            assert group['type'] == 2  # PRIM_TRIFAN
            assert group['indices'] == [0, 1, 2, 3]
        finally:
            os.unlink(filepath)

    def test_parse_linestrip(self):
        """Test parsing line strip primitive."""
        parser = CMODParser()
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.cmod') as f:
            filepath = f.name

        try:
            self.create_mesh_with_primitive(filepath, 4, [0, 1, 2])  # PRIM_LINESTRIP
            result = parser.parse(filepath)

            group = result['meshes'][0]['groups'][0]
            assert group['type'] == 4  # PRIM_LINESTRIP
            assert group['indices'] == [0, 1, 2]
        finally:
            os.unlink(filepath)


class TestCMODParserEdgeCases:
    """Tests for edge cases and error handling."""

    def test_parse_empty_file(self):
        """Test parsing an empty file."""
        parser = CMODParser()
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.cmod') as f:
            filepath = f.name

        try:
            with pytest.raises(ValueError):
                parser.parse(filepath)
        finally:
            os.unlink(filepath)

    def test_parse_minimal_valid_file(self):
        """Test parsing a minimal but valid CMOD file."""
        parser = CMODParser()
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.cmod') as f:
            f.write(b'#celmodel_binary')
            filepath = f.name

        try:
            result = parser.parse(filepath)
            assert result['materials'] == []
            assert result['meshes'] == []
        finally:
            os.unlink(filepath)

    def test_parse_multiple_materials(self):
        """Test parsing file with multiple materials."""
        parser = CMODParser()
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.cmod') as f:
            f.write(b'#celmodel_binary')
            # Material 1
            f.write(struct.pack('<H', 1001))  # TOKEN_MATERIAL
            f.write(struct.pack('<H', 1003))  # TOKEN_DIFFUSE
            f.write(struct.pack('<H', 7))  # CMOD_Color data type
            f.write(struct.pack('<fff', 1.0, 0.0, 0.0))  # Red
            f.write(struct.pack('<H', 1002))  # TOKEN_END_MATERIAL
            # Material 2
            f.write(struct.pack('<H', 1001))  # TOKEN_MATERIAL
            f.write(struct.pack('<H', 1003))  # TOKEN_DIFFUSE
            f.write(struct.pack('<H', 7))  # CMOD_Color data type
            f.write(struct.pack('<fff', 0.0, 1.0, 0.0))  # Green
            f.write(struct.pack('<H', 1002))  # TOKEN_END_MATERIAL
            filepath = f.name

        try:
            result = parser.parse(filepath)
            assert len(result['materials']) == 2
            assert result['materials'][0]['diffuse'] == pytest.approx((1.0, 0.0, 0.0))
            assert result['materials'][1]['diffuse'] == pytest.approx((0.0, 1.0, 0.0))
        finally:
            os.unlink(filepath)

    def test_parse_multiple_meshes(self):
        """Test parsing file with multiple meshes."""
        parser = CMODParser()
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.cmod') as f:
            f.write(b'#celmodel_binary')
            # Mesh 1
            f.write(struct.pack('<H', 1009))  # TOKEN_MESH
            f.write(struct.pack('<H', 1011))  # TOKEN_VERTEXDESC
            f.write(struct.pack('<HH', 0, 2))  # POSITION, FORMAT_FLOAT3
            f.write(struct.pack('<H', 1012))  # TOKEN_END_VERTEXDESC
            f.write(struct.pack('<H', 1013))  # TOKEN_VERTICES
            f.write(struct.pack('<I', 1))
            f.write(struct.pack('<fff', 0.0, 0.0, 0.0))
            f.write(struct.pack('<H', 1010))  # TOKEN_END_MESH
            # Mesh 2
            f.write(struct.pack('<H', 1009))  # TOKEN_MESH
            f.write(struct.pack('<H', 1011))  # TOKEN_VERTEXDESC
            f.write(struct.pack('<HH', 0, 2))  # POSITION, FORMAT_FLOAT3
            f.write(struct.pack('<H', 1012))  # TOKEN_END_VERTEXDESC
            f.write(struct.pack('<H', 1013))  # TOKEN_VERTICES
            f.write(struct.pack('<I', 1))
            f.write(struct.pack('<fff', 1.0, 1.0, 1.0))
            f.write(struct.pack('<H', 1010))  # TOKEN_END_MESH
            filepath = f.name

        try:
            result = parser.parse(filepath)
            assert len(result['meshes']) == 2
            assert result['meshes'][0]['vertices'][0]['position'] == pytest.approx((0.0, 0.0, 0.0))
            assert result['meshes'][1]['vertices'][0]['position'] == pytest.approx((1.0, 1.0, 1.0))
        finally:
            os.unlink(filepath)

    def test_parse_unknown_token_raises_exception(self):
        """Test that unknown tokens cause parser to bail out with exception."""
        parser = CMODParser()
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.cmod') as f:
            f.write(b'#celmodel_binary')
            f.write(struct.pack('<H', 1001))  # TOKEN_MATERIAL
            f.write(struct.pack('<H', 9999))  # Unknown token
            f.write(struct.pack('<H', 7))  # CMOD_Color data type
            f.write(struct.pack('<fff', 0.5, 0.5, 0.5))  # Data
            f.write(struct.pack('<H', 1002))  # TOKEN_END_MATERIAL
            filepath = f.name

        try:
            with pytest.raises(ValueError, match="Unknown material token: 9999"):
                parser.parse(filepath)
        finally:
            os.unlink(filepath)

    def test_parse_wrong_data_type_raises_exception(self):
        """Test that wrong data types cause parser to bail out with exception."""
        parser = CMODParser()
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.cmod') as f:
            f.write(b'#celmodel_binary')
            f.write(struct.pack('<H', 1001))  # TOKEN_MATERIAL
            f.write(struct.pack('<H', 1003))  # TOKEN_DIFFUSE
            f.write(struct.pack('<H', 1))  # CMOD_Float1 (wrong! should be CMOD_Color)
            f.write(struct.pack('<f', 0.5))  # Single float
            f.write(struct.pack('<H', 1002))  # TOKEN_END_MATERIAL
            filepath = f.name

        try:
            with pytest.raises(ValueError, match="Expected data type .* but got"):
                parser.parse(filepath)
        finally:
            os.unlink(filepath)
