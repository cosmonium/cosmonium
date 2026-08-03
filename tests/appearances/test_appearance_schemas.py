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

from panda3d.core import LColor

from cosmonium.parsers.schemas.appearance import ModelAppearanceConfig, TexturesAppearanceConfig


class TestTexturesAppearanceConfig:
    """Tests for TexturesAppearanceConfig schema validation."""

    def test_minimal_config(self):
        """Test that a minimal config with no fields is valid."""
        config = TexturesAppearanceConfig.model_validate({})
        assert config.type == "textures"
        assert config.texture is None
        assert config.transparency is False
        assert config.transparency is False
        assert config.transparency_level == 0.0
        assert config.transparency_blend is None
        assert config.nightscale == 0.02
        assert config.shininess == 1.0
        assert config.bump_height == 0.0
        assert config.roughness == 0.0
        assert config.backlit is None
        assert config.normal_bias is None
        assert config.slope_bias is None
        assert config.depth_bias is None

    def test_full_config(self):
        """Test a fully populated configuration."""
        data = {
            "type": "textures",
            "texture": "earth.jpg",
            "tint": [1.0, 0.5, 0.5, 1.0],
            "transparency": True,
            "transparency-level": 0.5,
            "transparency-blend": "alpha",
            "night-texture": "earth-night.jpg",
            "emission-texture": None,
            "nightscale": 0.05,
            "normalmap": "earth-normal.png",
            "specular-color": [0.5, 0.5, 0.5],
            "shininess": 20.0,
            "specularmap": "earth-specular.png",
            "bumpmap": "earth-bump.png",
            "bump-height": 5.0,
            "diffuse-color": [0.8, 0.8, 0.8, 1.0],
            "emission-color": [1.0, 1.0, 1.0, 1.0],
            "roughness": 0.3,
            "backlit": 0.1,
            "attribution": "NASA",
            "normal-bias": 0.3,
            "slope-bias": 0.4,
            "depth-bias": 0.05,
        }
        config = TexturesAppearanceConfig.model_validate(data)
        assert config.type == "textures"
        assert config.texture == "earth.jpg"
        assert config.tint == LColor(1.0, 0.5, 0.5, 1.0)
        assert config.transparency is True
        assert config.transparency_level == 0.5
        assert config.transparency_blend == "alpha"
        assert config.night_texture == "earth-night.jpg"
        assert config.emission_texture is None
        assert config.nightscale == 0.05
        assert config.normalmap == "earth-normal.png"
        assert config.specular_color == LColor(0.5, 0.5, 0.5, 1.0)
        assert config.shininess == 20.0
        assert config.specularmap == "earth-specular.png"
        assert config.bumpmap == "earth-bump.png"
        assert config.bump_height == 5.0
        assert config.diffuse_color == LColor(0.8, 0.8, 0.8, 1.0)
        assert config.emission_color == LColor(1.0, 1.0, 1.0, 1.0)
        assert config.roughness == 0.3
        assert config.backlit == 0.1
        assert config.attribution == "NASA"
        assert config.normal_bias == 0.3
        assert config.slope_bias == 0.4
        assert config.depth_bias == 0.05

    def test_texture_accepts_string(self):
        """Test that texture field accepts a string path."""
        config = TexturesAppearanceConfig.model_validate({"texture": "mars.jpg"})
        assert config.texture == "mars.jpg"

    def test_texture_accepts_dict(self):
        """Test that texture field accepts a dict configuration."""
        config = TexturesAppearanceConfig.model_validate({"texture": {"file": "mars.jpg", "format": "rgb"}})
        assert config.texture == {"file": "mars.jpg", "format": "rgb"}

    def test_tint_with_three_components(self):
        """Test that tint accepts 3-component color."""
        config = TexturesAppearanceConfig.model_validate({"tint": [1.0, 0.5, 0.3]})
        assert config.tint == LColor(1.0, 0.5, 0.3, 1.0)

    def test_tint_with_four_components(self):
        """Test that tint accepts 4-component color."""
        config = TexturesAppearanceConfig.model_validate({"tint": [1.0, 0.5, 0.3, 0.8]})
        assert config.tint == LColor(1.0, 0.5, 0.3, 0.8)

    def test_shadow_bias_parameters(self):
        """Test shadow bias parameters."""
        data = {
            "normal-bias": 0.3,
            "slope-bias": 0.7,
            "depth-bias": 0.15,
        }
        config = TexturesAppearanceConfig.model_validate(data)
        assert config.normal_bias == 0.3
        assert config.slope_bias == 0.7
        assert config.depth_bias == 0.15


class TestModelAppearanceConfig:
    """Tests for ModelAppearanceConfig schema validation."""

    def test_minimal_config(self):
        """Test minimal model appearance config."""
        config = ModelAppearanceConfig.model_validate({})
        assert config.type == "model"
        assert config.material is True
        assert config.vertex_color is True
        assert config.occlusion_channel is False

    def test_full_config(self):
        """Test fully specified model config."""
        data = {
            "material": False,
            "vertex-color": False,
            "occlusion-channel": True,
            "normal-bias": 0.2,
            "slope-bias": 0.3,
            "depth-bias": 0.05,
        }
        config = ModelAppearanceConfig.model_validate(data)
        assert config.material is False
        assert config.vertex_color is False
        assert config.occlusion_channel is True
        assert config.normal_bias == 0.2
