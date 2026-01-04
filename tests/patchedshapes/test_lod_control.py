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


from unittest.mock import Mock

from cosmonium.patchedshapes.lodcontrol import (
    LodControl,
    TextureLodControl,
    TextureOrVertexSizeLodControl,
    VertexSizeLodControl,
    VertexSizeMaxDistanceLodControl,
)


def create_mock_patch(lod=0, density=32, visible=True):
    """Create a mock patch object for testing."""
    mock = Mock(spec_set=['lod', 'density', 'visible', 'children'])
    mock.lod = lod
    mock.density = density
    mock.visible = visible
    mock.children = []
    return mock


def create_mock_appearance(texture_size=256):
    """Create a mock appearance with texture."""
    appearance = Mock(spec_set=['texture'])
    if texture_size > 0:
        texture = Mock(spec_set=['source'])
        texture_source = Mock(spec_set=['texture_size'])
        texture_source.texture_size = texture_size
        texture.source = texture_source
        appearance.texture = texture
    else:
        appearance.texture = None
    return appearance


class TestLodControl:
    """Test suite for base LodControl class."""

    def test_initialization(self):
        """Test LodControl initialization."""
        lod_control = LodControl(density=64, max_lod=10)

        assert lod_control.density == 64
        assert lod_control.max_lod == 10

    def test_get_density_for(self):
        """Test getting density for a given LOD."""
        lod_control = LodControl(density=32)

        assert lod_control.get_density_for(0) == 32
        assert lod_control.get_density_for(5) == 32

    def test_should_split_always_false(self):
        """Test that base class never splits."""
        lod_control = LodControl()
        patch = create_mock_patch(lod=0)

        assert lod_control.should_split(patch, 100, 10) is False

    def test_should_merge_always_false(self):
        """Test that base class never merges."""
        lod_control = LodControl()
        patch = create_mock_patch(lod=5)

        assert lod_control.should_merge(patch, 100, 10) is False

    def test_should_instanciate_visible_leaf(self):
        """Test instantiation for visible leaf patches."""
        lod_control = LodControl()
        patch = create_mock_patch(visible=True)

        assert lod_control.should_instanciate(patch, 100, 10) is True

    def test_should_instanciate_invisible(self):
        """Test that invisible patches should not be instantiated."""
        lod_control = LodControl()
        patch = create_mock_patch(visible=False)

        assert lod_control.should_instanciate(patch, 100, 10) is False

    def test_should_instanciate_with_children(self):
        """Test that patches with children should not be instantiated."""
        lod_control = LodControl()
        patch = create_mock_patch(visible=True)
        patch.children = [create_mock_patch(), create_mock_patch()]

        assert lod_control.should_instanciate(patch, 100, 10) is False

    def test_should_remove_invisible(self):
        """Test that invisible patches should be removed."""
        lod_control = LodControl()
        patch = create_mock_patch(visible=False)

        assert lod_control.should_remove(patch, 100, 10) is True

    def test_should_remove_visible(self):
        """Test that visible patches should not be removed."""
        lod_control = LodControl()
        patch = create_mock_patch(visible=True)

        assert lod_control.should_remove(patch, 100, 10) is False


class TestTextureLodControl:
    """Test suite for TextureLodControl class."""

    def test_initialization(self):
        """Test TextureLodControl initialization."""
        lod_control = TextureLodControl(density=64, max_lod=12)

        assert lod_control.density == 64
        assert lod_control.max_lod == 12
        assert lod_control.texture_size == 0

    def test_set_appearance_with_texture(self):
        """Test setting appearance with texture."""
        lod_control = TextureLodControl(density=32)
        appearance = create_mock_appearance(texture_size=512)

        lod_control.set_appearance(appearance)

        assert lod_control.texture_size == 512

    def test_set_appearance_without_texture(self):
        """Test setting appearance without texture."""
        lod_control = TextureLodControl(density=32)
        appearance = create_mock_appearance(texture_size=0)

        lod_control.set_appearance(appearance)

        assert lod_control.texture_size == 0

    def test_set_texture_size(self):
        """Test directly setting texture size."""
        lod_control = TextureLodControl(density=32)

        lod_control.set_texture_size(1024)

        assert lod_control.texture_size == 1024

    def test_should_split_when_patch_larger_than_texture(self):
        """Test splitting when apparent patch size is larger than texture."""
        lod_control = TextureLodControl(density=32, max_lod=10)
        lod_control.set_texture_size(256)
        patch = create_mock_patch(lod=3)

        # Apparent size is 300, texture is 256, and 300 > 256 * 1.1 = 281.6
        assert lod_control.should_split(patch, 300, 100) is True

    def test_should_not_split_when_patch_similar_to_texture(self):
        """Test not splitting when apparent patch size is similar to texture."""
        lod_control = TextureLodControl(density=32, max_lod=10)
        lod_control.set_texture_size(256)
        patch = create_mock_patch(lod=3)

        # Apparent size is 260, texture is 256, and 260 < 256 * 1.1 = 281.6
        assert lod_control.should_split(patch, 260, 100) is False

    def test_should_not_split_at_max_lod(self):
        """Test that splitting doesn't occur at max LOD."""
        lod_control = TextureLodControl(density=32, max_lod=5)
        lod_control.set_texture_size(256)
        patch = create_mock_patch(lod=5)

        assert lod_control.should_split(patch, 1000, 100) is False

    def test_should_not_split_without_texture(self):
        """Test that splitting doesn't occur without texture."""
        lod_control = TextureLodControl(density=32, max_lod=10)
        lod_control.set_texture_size(0)
        patch = create_mock_patch(lod=3)

        assert lod_control.should_split(patch, 1000, 100) is False

    def test_should_merge_when_patch_smaller_than_texture(self):
        """Test merging when apparent patch size is smaller than texture."""
        lod_control = TextureLodControl(density=32)
        lod_control.set_texture_size(256)
        patch = create_mock_patch(lod=5)

        # Apparent size is 200, texture is 256, and 200 < 256 / 1.1 = 232.7
        assert lod_control.should_merge(patch, 200, 100) is True

    def test_should_not_merge_when_patch_similar_to_texture(self):
        """Test not merging when apparent patch size is similar to texture."""
        lod_control = TextureLodControl(density=32)
        lod_control.set_texture_size(256)
        patch = create_mock_patch(lod=5)

        # Apparent size is 240, texture is 256, and 240 > 256 / 1.1 = 232.7
        assert lod_control.should_merge(patch, 240, 100) is False


class TestTextureOrVertexSizeLodControl:
    """Test suite for TextureOrVertexSizeLodControl class."""

    def test_initialization(self):
        """Test TextureOrVertexSizeLodControl initialization."""
        lod_control = TextureOrVertexSizeLodControl(max_vertex_size=2.0, density=64, max_lod=12)

        assert lod_control.max_vertex_size == 2.0
        assert lod_control.density == 64
        assert lod_control.max_lod == 12

    def test_get_density_for_with_texture(self):
        """Test getting density based on texture size."""
        lod_control = TextureOrVertexSizeLodControl(max_vertex_size=2.0, density=64)
        lod_control.set_texture_size(512)

        # density = texture_size / max_vertex_size = 512 / 2.0 = 256
        assert lod_control.get_density_for(0) == 256

    def test_get_density_for_without_texture(self):
        """Test getting density without texture."""
        lod_control = TextureOrVertexSizeLodControl(max_vertex_size=2.0, density=64)

        assert lod_control.get_density_for(0) == 64

    def test_should_split_by_texture(self):
        """Test splitting based on texture size."""
        lod_control = TextureOrVertexSizeLodControl(max_vertex_size=2.0, density=64, max_lod=10)
        lod_control.set_texture_size(256)
        patch = create_mock_patch(lod=3, density=128)

        # With texture, use texture-based split logic
        # Apparent size is 300, texture is 256, and 300 > 256 * 1.1 = 281.6
        assert lod_control.should_split(patch, 300, 100) is True

    def test_should_split_by_vertex_size(self):
        """Test splitting based on vertex size when no texture."""
        lod_control = TextureOrVertexSizeLodControl(max_vertex_size=2.0, density=64, max_lod=10)
        patch = create_mock_patch(lod=3, density=64)

        # Without texture, use vertex-based split logic
        # Apparent vertex size = 200 / 64 = 3.125 > 2.0
        assert lod_control.should_split(patch, 200, 100) is True

    def test_should_not_split_by_vertex_size(self):
        """Test not splitting when vertex size is appropriate."""
        lod_control = TextureOrVertexSizeLodControl(max_vertex_size=2.0, density=64, max_lod=10)
        patch = create_mock_patch(lod=3, density=64)

        # Apparent vertex size = 100 / 64 = 1.56 < 2.0
        assert lod_control.should_split(patch, 100, 100) is False

    def test_should_merge_by_texture(self):
        """Test merging based on texture size."""
        lod_control = TextureOrVertexSizeLodControl(max_vertex_size=2.0, density=64)
        lod_control.set_texture_size(256)
        patch = create_mock_patch(lod=5, density=128)

        # With texture, use texture-based merge logic
        # Apparent size is 200, texture is 256, and 200 < 256 / 1.1 = 232.7
        assert lod_control.should_merge(patch, 200, 100) is True

    def test_should_merge_by_vertex_size(self):
        """Test merging based on vertex size when no texture."""
        lod_control = TextureOrVertexSizeLodControl(max_vertex_size=2.0, density=64)
        patch = create_mock_patch(lod=5, density=64)

        # Without texture, use vertex-based merge logic
        # Apparent vertex size = 100 / 64 = 1.56 < 2.0 / 1.1 = 1.82
        assert lod_control.should_merge(patch, 100, 100) is True

    def test_should_not_merge_by_vertex_size(self):
        """Test not merging when vertex size is too large."""
        lod_control = TextureOrVertexSizeLodControl(max_vertex_size=2.0, density=64)
        patch = create_mock_patch(lod=5, density=64)

        # Apparent vertex size = 120 / 64 = 1.875 > 2.0 / 1.1 = 1.82
        assert lod_control.should_merge(patch, 120, 100) is False


class TestVertexSizeLodControl:
    """Test suite for VertexSizeLodControl class."""

    def test_initialization(self):
        """Test VertexSizeLodControl initialization."""
        lod_control = VertexSizeLodControl(max_vertex_size=3.0, density=32, max_lod=15)

        assert lod_control.max_vertex_size == 3.0
        assert lod_control.density == 32
        assert lod_control.max_lod == 15

    def test_should_split_large_vertex_size(self):
        """Test splitting when vertex size is too large."""
        lod_control = VertexSizeLodControl(max_vertex_size=2.0, density=64, max_lod=10)
        patch = create_mock_patch(lod=3, density=64)

        # Apparent vertex size = 200 / 64 = 3.125 > 2.0 * 1.1 = 2.2
        assert lod_control.should_split(patch, 200, 100) is True

    def test_should_not_split_appropriate_vertex_size(self):
        """Test not splitting when vertex size is appropriate."""
        lod_control = VertexSizeLodControl(max_vertex_size=2.0, density=64, max_lod=10)
        patch = create_mock_patch(lod=3, density=64)

        # Apparent vertex size = 120 / 64 = 1.875 < 2.0 * 1.1 = 2.2
        assert lod_control.should_split(patch, 120, 100) is False

    def test_should_not_split_at_max_lod(self):
        """Test that splitting doesn't occur at max LOD."""
        lod_control = VertexSizeLodControl(max_vertex_size=2.0, density=64, max_lod=5)
        patch = create_mock_patch(lod=5, density=64)

        assert lod_control.should_split(patch, 1000, 100) is False

    def test_should_merge_small_vertex_size(self):
        """Test merging when vertex size is small."""
        lod_control = VertexSizeLodControl(max_vertex_size=2.0, density=64)
        patch = create_mock_patch(lod=5, density=64)

        # Apparent vertex size = 100 / 64 = 1.56 < 2.0 / 1.1 = 1.82
        assert lod_control.should_merge(patch, 100, 100) is True

    def test_should_not_merge_appropriate_vertex_size(self):
        """Test not merging when vertex size is appropriate."""
        lod_control = VertexSizeLodControl(max_vertex_size=2.0, density=64)
        patch = create_mock_patch(lod=5, density=64)

        # Apparent vertex size = 120 / 64 = 1.875 > 2.0 / 1.1 = 1.82
        assert lod_control.should_merge(patch, 120, 100) is False


class TestVertexSizeMaxDistanceLodControl:
    """Test suite for VertexSizeMaxDistanceLodControl class."""

    def test_initialization(self):
        """Test VertexSizeMaxDistanceLodControl initialization."""
        lod_control = VertexSizeMaxDistanceLodControl(max_distance=1000.0, max_vertex_size=2.5, density=32, max_lod=10)

        assert lod_control.max_distance == 1000.0
        assert lod_control.max_vertex_size == 2.5
        assert lod_control.density == 32
        assert lod_control.max_lod == 10

    def test_should_instanciate_within_distance(self):
        """Test instantiation when within max distance."""
        lod_control = VertexSizeMaxDistanceLodControl(max_distance=1000.0, max_vertex_size=2.0, density=32)
        patch = create_mock_patch(visible=True)

        assert lod_control.should_instanciate(patch, 100, 500) is True

    def test_should_not_instanciate_beyond_distance(self):
        """Test not instantiating when beyond max distance."""
        lod_control = VertexSizeMaxDistanceLodControl(max_distance=1000.0, max_vertex_size=2.0, density=32)
        patch = create_mock_patch(visible=True)

        assert lod_control.should_instanciate(patch, 100, 1500) is False

    def test_should_not_instanciate_invisible(self):
        """Test not instantiating invisible patches regardless of distance."""
        lod_control = VertexSizeMaxDistanceLodControl(max_distance=1000.0, max_vertex_size=2.0, density=32)
        patch = create_mock_patch(visible=False)

        assert lod_control.should_instanciate(patch, 100, 500) is False

    def test_inherits_vertex_size_split_behavior(self):
        """Test that it inherits split behavior from VertexSizeLodControl."""
        lod_control = VertexSizeMaxDistanceLodControl(max_distance=1000.0, max_vertex_size=2.0, density=64, max_lod=10)
        patch = create_mock_patch(lod=3, density=64)

        # Should behave like VertexSizeLodControl for split
        # Apparent vertex size = 200 / 64 = 3.125 > 2.0 * 1.1 = 2.2
        assert lod_control.should_split(patch, 200, 100) is True

    def test_inherits_vertex_size_merge_behavior(self):
        """Test that it inherits merge behavior from VertexSizeLodControl."""
        lod_control = VertexSizeMaxDistanceLodControl(max_distance=1000.0, max_vertex_size=2.0, density=64)
        patch = create_mock_patch(lod=5, density=64)

        # Should behave like VertexSizeLodControl for merge
        # Apparent vertex size = 100 / 64 = 1.56 < 2.0 / 1.1 = 1.82
        assert lod_control.should_merge(patch, 100, 100) is True
