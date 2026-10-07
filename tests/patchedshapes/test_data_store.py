#
# This file is part of Cosmonium.
#
# Copyright (C) 2018-2026 Laurent Deru.
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


import builtins
import struct
from array import array
from types import SimpleNamespace
from unittest.mock import Mock, create_autospec

import pytest
from panda3d.core import GeomEnums, GraphicsEngine, ShaderBuffer

from cosmonium.entities.data_store import PatchDataStoreManager
from cosmonium.entities.patcheddata import PatchedData
from cosmonium.opengl import OpenGLConfig
from cosmonium.shaders.instancing import OffsetScaleInstanceControl

from ..glsl import run_glsl_test

# Values of the two vec4 stored for each entry, in shader order
ENTRY_DATA = [1.0, 2.0, 3.0, 0.0, 4.0, 5.0, 6.0, 7.0]


def create_data_source(values=ENTRY_DATA):
    """Create a mock data source providing the given values for each patch."""
    data_source = create_autospec(PatchedData, instance=True, spec_set=True)
    data_source.get_nb_shader_data.return_value = len(values)

    def collect_shader_data(data, patch):
        data += values

    data_source.collect_shader_data.side_effect = collect_shader_data
    return data_source


def create_mock_patch(entry_id=None):
    """Create a mock patch with only an entry id."""
    patch = Mock(spec_set=['entry_id'])
    patch.entry_id = entry_id
    return patch


def create_manager(monkeypatch, use_shader_buffer, values=ENTRY_DATA, max_elem=8):
    monkeypatch.setattr(OpenGLConfig, 'shader_buffer', use_shader_buffer)
    manager = PatchDataStoreManager(max_elem)
    manager.parameters.add_data_source(create_data_source(values))
    manager.init()
    return manager


def data_store_preamble(manager):
    shader_data_source = manager.parameters.get_shader_data_source()
    code = []
    shader_data_source.uniforms(code)
    shader_data_source.fetch_data_store(code)
    return '\n'.join(code)


DATA_STORE_TEST = """
vec4 first = fetch_data_store(0);
vec4 second = fetch_data_store(1);
assert(first == vec4(1.0, 2.0, 3.0, 0.0));
assert(second == vec4(4.0, 5.0, 6.0, 7.0));
"""


class TestPatchParametersDataStore:
    """Test the layout of the patch parameters data store."""

    def test_stride_is_rounded_to_vec4(self, monkeypatch):
        """Each entry uses a whole number of vec4."""
        manager = create_manager(monkeypatch, False, values=[1.0] * 5)
        assert manager.parameters.stride == 2
        assert manager.parameters.texture_data.get_x_size() == 8 * 2

    def test_texture_layout(self, monkeypatch):
        """Data is stored in the texture with the R and B components swapped."""
        manager = create_manager(monkeypatch, False)
        manager.update_patch(create_mock_patch(entry_id=3))
        image = manager.parameters.texture_data.get_ram_image()
        values = struct.unpack('f' * 8, bytes(image)[3 * 32 : 4 * 32])
        assert list(values) == [3.0, 2.0, 1.0, 0.0, 6.0, 5.0, 4.0, 7.0]

    def test_shader_buffer_update(self, monkeypatch):
        """Data is written in the shader buffer at the patch entry."""
        engine = Mock(spec_set=['update_shader_buffer_data'])
        gsg = object()
        monkeypatch.setattr(builtins, 'base', SimpleNamespace(graphics_engine=engine, win=Mock(gsg=gsg)), raising=False)
        manager = create_manager(monkeypatch, True)
        manager.update_patch(create_mock_patch(entry_id=3))
        engine.update_shader_buffer_data.assert_called_once()
        buffer, called_gsg, data, offset = engine.update_shader_buffer_data.call_args.args
        assert buffer is manager.parameters.shader_buffer
        assert called_gsg is gsg
        assert offset == 3 * 32
        assert list(struct.unpack('f' * 8, data)) == ENTRY_DATA

    def test_shader_id(self, monkeypatch):
        """Shader id depends on the storage kind."""
        texture_manager = create_manager(monkeypatch, False)
        buffer_manager = create_manager(monkeypatch, True)
        texture_id = texture_manager.parameters.get_shader_data_source().get_id()
        buffer_id = buffer_manager.parameters.get_shader_data_source().get_id()
        assert texture_id != buffer_id

    def test_texture_fetch(self, gsg, monkeypatch):
        """Data stored in the texture is retrieved by the shader."""
        manager = create_manager(monkeypatch, False)
        manager.update_patch(create_mock_patch(entry_id=3))
        inputs = {'data_store': manager.parameters.texture_data, 'entry_id': 3}
        run_glsl_test(gsg, DATA_STORE_TEST, data_store_preamble(manager), inputs, version=430)

    def test_shader_buffer_fetch(self, gsg, monkeypatch):
        """Data stored in the shader buffer is retrieved by the shader."""
        if not hasattr(GraphicsEngine, 'update_shader_buffer_data'):
            pytest.skip("shader buffer update not supported")
        monkeypatch.setattr(
            builtins, 'base', SimpleNamespace(graphics_engine=gsg.get_engine(), win=Mock(gsg=gsg)), raising=False
        )
        manager = create_manager(monkeypatch, True)
        manager.update_patch(create_mock_patch(entry_id=3))
        inputs = {'DataStoreBuffer': manager.parameters.shader_buffer, 'entry_id': 3}
        run_glsl_test(gsg, DATA_STORE_TEST, data_store_preamble(manager), inputs, version=430)


class TestOffsetScaleInstanceControl:
    """Test the instances offset table storage."""

    def test_storage_selection(self, monkeypatch):
        """Shader buffer is preferred when available."""
        monkeypatch.setattr(OpenGLConfig, 'shader_buffer', True)
        assert OffsetScaleInstanceControl(16).storage == 'ssbo'
        monkeypatch.setattr(OpenGLConfig, 'shader_buffer', False)
        assert OffsetScaleInstanceControl(16).storage == 'tex'

    def test_shader_buffer_fetch(self, gsg, monkeypatch):
        """Offsets stored in the shader buffer are retrieved by the shader."""
        monkeypatch.setattr(OpenGLConfig, 'shader_buffer', True)
        instance_control = OffsetScaleInstanceControl(16)
        code = []
        instance_control.vertex_uniforms(code)
        offsets = [(0.0, 1.0, 2.0, 3.0), (4.0, 5.0, 6.0, 7.0)]
        data = array('f', [value for offset in offsets for value in offset]).tobytes()
        buffer = ShaderBuffer('instances_offset', data, GeomEnums.UH_static)
        body = "assert(instances_offset[1] == vec4(4.0, 5.0, 6.0, 7.0));"
        run_glsl_test(gsg, body, '\n'.join(code), {'InstancesOffsetBuffer': buffer}, version=430)
