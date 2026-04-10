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


"""Tests for appearance configuration schemas."""

from cosmonium.parsers.schemas.appearance import DeferredProceduralAppearanceConfig, ProceduralAppearanceConfig


class TestProceduralAppearanceConfig:
    """Tests for ProceduralAppearanceConfig schema validation."""

    def test_minimal_config(self):
        """Test minimal procedural appearance config."""
        config = ProceduralAppearanceConfig.model_validate({})
        assert config.type == "procedural"
        assert config.control is None
        assert config.textures is None

    def test_with_control_and_textures(self):
        """Test procedural config with control and textures."""
        data = {
            "control": {"type": "heightmap"},
            "textures": {"grass": "grass.jpg", "rock": "rock.jpg"},
        }
        config = ProceduralAppearanceConfig.model_validate(data)
        assert config.control == {"type": "heightmap"}
        assert config.textures == {"grass": "grass.jpg", "rock": "rock.jpg"}


class TestDeferredProceduralAppearanceConfig:
    """Tests for DeferredProceduralAppearanceConfig schema validation."""

    def test_minimal_config(self):
        """Test minimal deferred procedural appearance config."""
        config = DeferredProceduralAppearanceConfig.model_validate({})
        assert config.type == "deferred-procedural"
        assert config.size == 256

    def test_with_fields(self):
        """Test deferred procedural with all fields."""
        data = {
            "size": 1024,
            "control": {"type": "heightmap"},
            "textures": {"sand": "sand.jpg"},
        }
        config = DeferredProceduralAppearanceConfig.model_validate(data)
        assert config.size == 1024
        assert config.control == {"type": "heightmap"}
        assert config.textures == {"sand": "sand.jpg"}
