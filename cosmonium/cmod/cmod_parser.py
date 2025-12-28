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

import struct
from typing import Any, BinaryIO


class CMODParser:
    """Parser for Celestia CMOD (Celestia Model) binary format."""

    # CMOD binary format constants
    CMOD_MAGIC = b'#celmodel_binary'
    CMOD_ASCII_MAGIC = b'#celmodel_ascii'

    # Token types
    TOKEN_MATERIAL = 1001
    TOKEN_END_MATERIAL = 1002
    TOKEN_DIFFUSE = 1003
    TOKEN_SPECULAR = 1004
    TOKEN_SPECPOWER = 1005
    TOKEN_OPACITY = 1006
    TOKEN_TEXTURE = 1007
    TOKEN_MESH = 1009
    TOKEN_END_MESH = 1010
    TOKEN_VERTEXDESC = 1011
    TOKEN_END_VERTEXDESC = 1012
    TOKEN_VERTICES = 1013
    TOKEN_EMISSIVE = 1014
    TOKEN_BLEND = 1015

    # Data types for token values
    CMOD_Float1 = 1
    CMOD_Float2 = 2
    CMOD_Float3 = 3
    CMOD_Float4 = 4
    CMOD_String = 5
    CMOD_Uint32 = 6
    CMOD_Color = 7

    # Vertex attribute semantic types
    POSITION = 0
    COLOR0 = 1
    COLOR1 = 2
    NORMAL = 3
    TANGENT = 4
    TEXCOORD0 = 5
    TEXCOORD1 = 6
    TEXCOORD2 = 7
    TEXCOORD3 = 8
    POINTSIZE = 9

    # Vertex attribute format types
    FORMAT_FLOAT1 = 0
    FORMAT_FLOAT2 = 1
    FORMAT_FLOAT3 = 2
    FORMAT_FLOAT4 = 3
    FORMAT_UBYTE4 = 4

    # Primitive types
    PRIM_TRILIST = 0
    PRIM_TRISTRIP = 1
    PRIM_TRIFAN = 2
    PRIM_LINELIST = 3
    PRIM_LINESTRIP = 4
    PRIM_POINTS = 5

    # Texture semantic
    TEXTURE_DIFFUSE = 0
    TEXTURE_NORMAL = 1
    TEXTURE_SPECULAR = 2
    TEXTURE_EMISSIVE = 3

    def __init__(self):
        self.materials = []
        self.meshes = []

    def parse(self, filepath: str) -> dict[str, Any]:
        """Parse a CMOD file and return the model data."""
        with open(filepath, 'rb') as f:
            # Read magic header (16 bytes for binary, variable for ASCII)
            magic = f.read(16)

            if magic == self.CMOD_MAGIC:
                return self._parse_binary(f)
            elif magic.startswith(self.CMOD_ASCII_MAGIC):
                # Need to reopen in text mode for ASCII parsing
                pass
            else:
                raise ValueError("Invalid CMOD file: unrecognized magic header")

        # Reopen for ASCII parsing
        with open(filepath, 'r', encoding='utf-8') as ft:
            return self._parse_ascii(ft)

    def _parse_binary(self, f: BinaryIO) -> dict[str, Any]:
        """Parse binary CMOD format."""
        # Reset state
        self.materials = []
        self.meshes = []

        while True:
            token = self._read_token(f)
            if token is None:
                break
            if token == self.TOKEN_MATERIAL:
                material = self._parse_material(f)
                self.materials.append(material)
            elif token == self.TOKEN_MESH:
                mesh = self._parse_mesh(f)
                self.meshes.append(mesh)
            else:
                # Unknown token at top level - bail out
                raise ValueError(f"Unknown top-level CMOD token: {token}. Parser cannot continue.")

        return {'materials': self.materials, 'meshes': self.meshes}

    def _read_token(self, f: BinaryIO) -> int:
        """Read a 16-bit token from the file."""
        data = f.read(2)
        if len(data) < 2:
            return None
        return struct.unpack('<H', data)[0]

    def _read_data_type(self, f: BinaryIO) -> int:
        """Read a 16-bit data type from the file."""
        data = f.read(2)
        if len(data) < 2:
            return None
        return struct.unpack('<H', data)[0]

    def _read_4_bytes_raw(self, f: BinaryIO) -> int:
        """Read four 8-bit unsigned integer (without data type)."""
        return struct.unpack('<BBBB', f.read(4))

    def _read_uint16_raw(self, f: BinaryIO) -> int:
        """Read a 32-bit unsigned integer (without data type)."""
        return struct.unpack('<H', f.read(2))[0]

    def _read_uint32_raw(self, f: BinaryIO) -> int:
        """Read a 32-bit unsigned integer (without data type)."""
        return struct.unpack('<I', f.read(4))[0]

    def _read_float_raw(self, f: BinaryIO) -> float:
        """Read a 32-bit float (without data type)."""
        return struct.unpack('<f', f.read(4))[0]

    def _read_2_float_raw(self, f: BinaryIO) -> float:
        """Read two 32-bit floats (without data type)."""
        return struct.unpack('<ff', f.read(8))

    def _read_3_float_raw(self, f: BinaryIO) -> float:
        """Read three 32-bit floats (without data type)."""
        return struct.unpack('<fff', f.read(12))

    def _read_4_float_raw(self, f: BinaryIO) -> float:
        """Read four 32-bit floats (without data type)."""
        return struct.unpack('<ffff', f.read(16))

    def _read_uint32(self, f: BinaryIO) -> int:
        """Read a 32-bit unsigned integer with data type validation."""
        data_type = self._read_data_type(f)
        if data_type != self.CMOD_Uint32:
            raise ValueError(f"Expected data type {self.CMOD_Uint32} but got {data_type}")
        return self._read_uint32_raw(f)

    def _read_float(self, f: BinaryIO) -> float:
        """Read a 32-bit float with data type validation."""
        data_type = self._read_data_type(f)
        if data_type != self.CMOD_Float1:
            raise ValueError(f"Expected data type {self.CMOD_Float1} but got {data_type}")
        return self._read_float_raw(f)

    def _read_string(self, f: BinaryIO) -> str:
        """Read a length-prefixed string with data type validation."""
        data_type = self._read_data_type(f)
        if data_type != self.CMOD_String:
            raise ValueError(f"Expected data type {self.CMOD_String} but got {data_type}")
        # Read string length as uint16
        length = struct.unpack('<H', f.read(2))[0]
        if length == 0:
            return ""
        data = f.read(length)
        try:
            return data.decode('utf-8')
        except UnicodeDecodeError:
            # If UTF-8 fails, try latin-1
            return data.decode('latin-1')

    def _read_color(self, f: BinaryIO) -> tuple[float, float, float]:
        """Read an RGB color (3 floats)."""
        data_type = self._read_data_type(f)
        if data_type not in (self.CMOD_Color, self.CMOD_Float3):
            raise ValueError(f"Expected data type {self.CMOD_Color} or {self.CMOD_Float3} but got {data_type}")
        (r, g, b) = self._read_3_float_raw(f)
        return (r, g, b)

    def _parse_material(self, f: BinaryIO) -> dict[str, Any]:
        """Parse a material definition."""
        material = {
            'diffuse': (1.0, 1.0, 1.0),
            'specular': (0.0, 0.0, 0.0),
            'emissive': (0.0, 0.0, 0.0),
            'specpower': 1.0,
            'opacity': 1.0,
            'blend': 0,
            'textures': [],
        }

        while True:
            token = self._read_token(f)
            if token == self.TOKEN_END_MATERIAL:
                break
            elif token == self.TOKEN_DIFFUSE:
                material['diffuse'] = self._read_color(f)
            elif token == self.TOKEN_SPECULAR:
                material['specular'] = self._read_color(f)
            elif token == self.TOKEN_EMISSIVE:
                material['emissive'] = self._read_color(f)
            elif token == self.TOKEN_SPECPOWER:
                material['specpower'] = self._read_float(f)
            elif token == self.TOKEN_OPACITY:
                material['opacity'] = self._read_float(f)
            elif token == self.TOKEN_BLEND:
                material['blend'] = self._read_uint32(f)
            elif token == self.TOKEN_TEXTURE:
                # Texture semantic is a raw uint16 (no data type prefix)
                tex_semantic = self._read_uint16_raw(f)
                # Then the path string has CMOD_String data type prefix
                tex_path = self._read_string(f)
                material['textures'].append({'type': tex_semantic, 'path': tex_path})
            else:
                # Unknown token in material - bail out
                raise ValueError(f"Unknown material token: {token}. Parser cannot continue.")

        return material

    def _parse_mesh(self, f: BinaryIO) -> dict[str, Any]:
        """Parse a mesh definition."""
        mesh = {'vertex_desc': [], 'vertices': [], 'groups': []}

        while True:
            token = self._read_token(f)

            if token == self.TOKEN_END_MESH:
                break
            elif token == self.TOKEN_VERTEXDESC:
                mesh['vertex_desc'] = self._parse_vertex_desc(f)
            elif token == self.TOKEN_VERTICES:
                vertex_count = self._read_uint32_raw(f)
                mesh['vertices'] = self._parse_vertices(f, mesh['vertex_desc'], vertex_count)
            elif token >= self.PRIM_TRILIST and token <= self.PRIM_POINTS:
                # Primitive group token
                group = self._parse_primitive_group(f, token)
                mesh['groups'].append(group)
            else:
                # Unknown token in mesh, bail out
                raise ValueError(f"Unknown mesh token: {token}. Parser cannot continue.")

        return mesh

    def _parse_vertex_desc(self, f: BinaryIO) -> list[dict[str, Any]]:
        """Parse vertex descriptor (attributes).

        Reads attribute definitions until TOKEN_END_VERTEXDESC is encountered.
        Each attribute is: semantic (uint16) + format (uint16).
        """
        attributes = []

        while True:
            token = self._read_token(f)

            if token == self.TOKEN_END_VERTEXDESC:
                break

            # Token is actually the semantic
            semantic = token
            # Read format
            fmt = self._read_uint16_raw(f)

            attributes.append({'semantic': semantic, 'format': fmt})

        return attributes

    def _parse_vertices(self, f: BinaryIO, vertex_desc: list[dict[str, Any]], count: int) -> list[dict[str, Any]]:
        """Parse vertex data."""
        vertices = []

        for _ in range(count):
            vertex = {}

            for attr in vertex_desc:
                semantic = attr['semantic']
                fmt = attr['format']

                # Read data based on format
                if fmt == self.FORMAT_FLOAT1:
                    data = (self._read_float_raw(f),)
                elif fmt == self.FORMAT_FLOAT2:
                    data = self._read_2_float_raw(f)
                elif fmt == self.FORMAT_FLOAT3:
                    data = self._read_3_float_raw(f)
                elif fmt == self.FORMAT_FLOAT4:
                    data = self._read_4_float_raw(f)
                elif fmt == self.FORMAT_UBYTE4:
                    bytes_data = self._read_4_bytes_raw(f)
                    # Normalize to 0-1 range
                    data = tuple(b / 255.0 for b in bytes_data)
                else:
                    data = None

                # Store with semantic name
                vertex[self._semantic_name(semantic)] = data

            vertices.append(vertex)

        return vertices

    def _parse_primitive_group(self, f: BinaryIO, prim_type: int) -> dict[str, Any]:
        """Parse a primitive group (triangles, lines, etc.)."""
        material_index = self._read_uint32_raw(f)
        index_count = self._read_uint32_raw(f)

        indices = []
        for _ in range(index_count):
            indices.append(self._read_uint32_raw(f))

        return {'type': prim_type, 'material': material_index, 'indices': indices}

    def _semantic_name(self, semantic: int) -> str:
        """Convert semantic ID to string name."""
        names = {
            self.POSITION: 'position',
            self.COLOR0: 'color0',
            self.COLOR1: 'color1',
            self.NORMAL: 'normal',
            self.TANGENT: 'tangent',
            self.TEXCOORD0: 'texcoord0',
            self.TEXCOORD1: 'texcoord1',
            self.TEXCOORD2: 'texcoord2',
            self.TEXCOORD3: 'texcoord3',
            self.POINTSIZE: 'pointsize',
        }
        return names.get(semantic, f'unknown_{semantic}')

    def _parse_ascii(self, f) -> dict[str, Any]:
        """Parse ASCII CMOD format."""
        # Reset state
        self.materials = []
        self.meshes = []

        # Read header line
        header = f.readline().strip()
        if not header.startswith('#celmodel_ascii'):
            raise ValueError("Invalid ASCII CMOD header")

        # Parse using simple text parsing
        while True:
            line = f.readline()
            if not line:
                break

            line = line.strip()
            if not line or line.startswith('#'):
                continue

            if line == 'material':
                material = self._parse_ascii_material(f)
                self.materials.append(material)
            elif line == 'mesh':
                mesh = self._parse_ascii_mesh(f)
                self.meshes.append(mesh)

        return {'materials': self.materials, 'meshes': self.meshes}

    def _parse_ascii_material(self, f) -> dict[str, Any]:
        """Parse ASCII material definition."""
        material = {
            'diffuse': (1.0, 1.0, 1.0),
            'specular': (0.0, 0.0, 0.0),
            'emissive': (0.0, 0.0, 0.0),
            'specpower': 1.0,
            'opacity': 1.0,
            'blend': 0,
            'textures': [],
        }

        while True:
            line = f.readline()
            if not line:
                break

            line = line.strip()
            if not line or line.startswith('#'):
                continue

            if line == 'end_material':
                break

            parts = line.split()
            if not parts:
                continue

            keyword = parts[0]
            if keyword == 'diffuse':
                material['diffuse'] = tuple(float(x) for x in parts[1:4])
            elif keyword == 'specular':
                material['specular'] = tuple(float(x) for x in parts[1:4])
            elif keyword == 'emissive':
                material['emissive'] = tuple(float(x) for x in parts[1:4])
            elif keyword == 'specpower':
                material['specpower'] = float(parts[1])
            elif keyword == 'opacity':
                material['opacity'] = float(parts[1])
            elif keyword == 'blend':
                material['blend'] = int(parts[1])
            elif keyword == 'texture0':
                # texture0 "path/to/texture.png"
                tex_path = ' '.join(parts[1:]).strip('"')
                material['textures'].append({'type': 0, 'path': tex_path})

        return material

    def _parse_ascii_mesh(self, f) -> dict[str, Any]:
        """Parse ASCII mesh definition."""
        mesh = {'vertex_desc': [], 'vertices': [], 'groups': []}

        while True:
            line = f.readline()
            if not line:
                break

            line = line.strip()
            if not line or line.startswith('#'):
                continue

            if line == 'end_mesh':
                break

            parts = line.split()
            if not parts:
                continue

            keyword = parts[0]
            if keyword == 'vertexdesc':
                mesh['vertex_desc'] = self._parse_ascii_vertexdesc(f)
            elif keyword == 'vertices':
                vertex_count = int(parts[1])
                mesh['vertices'] = self._parse_ascii_vertices(f, mesh['vertex_desc'], vertex_count)
            elif keyword in ('trilist', 'tristrip', 'trifan', 'linelist', 'linestrip', 'points'):
                group = self._parse_ascii_primitive_group(f, keyword, parts)
                mesh['groups'].append(group)

        return mesh

    def _parse_ascii_vertexdesc(self, f) -> list[dict[str, Any]]:
        """Parse ASCII vertex descriptor."""
        attributes = []

        while True:
            line = f.readline()
            if not line:
                break

            line = line.strip()
            if not line or line.startswith('#'):
                continue

            if line == 'end_vertexdesc':
                break

            parts = line.split()
            if len(parts) >= 2:
                # Format: semantic format
                semantic_name = parts[0].lower()
                format_name = parts[1].lower()

                # Map semantic names to IDs
                semantic_map = {
                    'position': self.POSITION,
                    'normal': self.NORMAL,
                    'color0': self.COLOR0,
                    'color1': self.COLOR1,
                    'tangent': self.TANGENT,
                    'texcoord0': self.TEXCOORD0,
                    'texcoord1': self.TEXCOORD1,
                    'texcoord2': self.TEXCOORD2,
                    'texcoord3': self.TEXCOORD3,
                    'pointsize': self.POINTSIZE,
                }

                # Map format names to IDs
                format_map = {
                    'f1': self.FORMAT_FLOAT1,
                    'f2': self.FORMAT_FLOAT2,
                    'f3': self.FORMAT_FLOAT3,
                    'f4': self.FORMAT_FLOAT4,
                    'ub4': self.FORMAT_UBYTE4,
                }

                semantic = semantic_map.get(semantic_name, 0)
                fmt = format_map.get(format_name, self.FORMAT_FLOAT3)

                attributes.append({'semantic': semantic, 'format': fmt})

        return attributes

    def _parse_ascii_vertices(self, f, vertex_desc: list[dict[str, Any]], count: int) -> list[dict[str, Any]]:
        """Parse ASCII vertex data."""
        vertices = []

        for _ in range(count):
            line = f.readline()
            if not line:
                break

            parts = line.strip().split()
            if not parts:
                continue

            vertex = {}
            idx = 0

            for attr in vertex_desc:
                semantic = attr['semantic']
                fmt = attr['format']

                # Read data based on format with bounds checking
                try:
                    if fmt == self.FORMAT_FLOAT1:
                        if idx >= len(parts):
                            break
                        data = (float(parts[idx]),)
                        idx += 1
                    elif fmt == self.FORMAT_FLOAT2:
                        if idx + 1 >= len(parts):
                            break
                        data = (float(parts[idx]), float(parts[idx + 1]))
                        idx += 2
                    elif fmt == self.FORMAT_FLOAT3:
                        if idx + 2 >= len(parts):
                            break
                        data = (float(parts[idx]), float(parts[idx + 1]), float(parts[idx + 2]))
                        idx += 3
                    elif fmt == self.FORMAT_FLOAT4:
                        if idx + 3 >= len(parts):
                            break
                        data = (float(parts[idx]), float(parts[idx + 1]), float(parts[idx + 2]), float(parts[idx + 3]))
                        idx += 4
                    elif fmt == self.FORMAT_UBYTE4:
                        if idx + 3 >= len(parts):
                            break
                        # In ASCII, ubyte4 is usually represented as floats
                        data = (float(parts[idx]), float(parts[idx + 1]), float(parts[idx + 2]), float(parts[idx + 3]))
                        idx += 4
                    else:
                        data = None

                    vertex[self._semantic_name(semantic)] = data
                except (ValueError, IndexError):
                    # Skip malformed vertex data
                    break

            vertices.append(vertex)

        return vertices

    def _parse_ascii_primitive_group(self, f, prim_type_name: str, parts: list[str]) -> dict[str, Any]:
        """Parse ASCII primitive group."""
        # Map primitive type names to IDs
        prim_type_map = {
            'trilist': self.PRIM_TRILIST,
            'tristrip': self.PRIM_TRISTRIP,
            'trifan': self.PRIM_TRIFAN,
            'linelist': self.PRIM_LINELIST,
            'linestrip': self.PRIM_LINESTRIP,
            'points': self.PRIM_POINTS,
        }

        prim_type = prim_type_map.get(prim_type_name, self.PRIM_TRILIST)

        # Format: primtype material_index index_count
        # Validate we have enough parameters
        if len(parts) < 3:
            print(f"Warning: Malformed primitive group line, expected 3 parts, got {len(parts)}")
            return {'type': prim_type, 'material': 0, 'indices': []}

        material_index = int(parts[1])
        index_count = int(parts[2])

        # Read indices
        indices = []
        remaining = index_count

        while remaining > 0:
            line = f.readline()
            if not line:
                break

            parts = line.strip().split()
            for part in parts:
                if remaining > 0:
                    indices.append(int(part))
                    remaining -= 1

        return {'type': prim_type, 'material': material_index, 'indices': indices}
