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


"""Tests for configuration schemas."""

from cosmonium.parsers.schemas.appearance import TexturesAppearanceConfig
from cosmonium.parsers.schemas.orbit import EllipticOrbitConfig, FixedOrbitConfig
from cosmonium.parsers.schemas.rotation import FixedRotationConfig, UniformRotationConfig
from cosmonium.parsers.schemas.stellarobjects import ReflectiveBodyConfig, StarConfig
from cosmonium.parsers.schemas.surface import SurfaceConfig


class TestOrbitSchemas:
    """Test orbit configuration schemas."""

    def test_fixed_orbit_valid(self):
        """Test valid fixed orbit configuration."""
        data = {
            "type": "fixed",
            "position": [0, 0, 0],
        }
        config = FixedOrbitConfig.model_validate(data)
        assert config.type == "fixed"
        assert config.position == [0, 0, 0]

    def test_elliptic_orbit_valid(self):
        """Test valid elliptic orbit configuration."""
        data = {
            "type": "elliptic",
            "semi-major-axis": 1.0,
            "eccentricity": 0.0167,
            "period": 365.25,
        }
        config = EllipticOrbitConfig.model_validate(data)
        assert config.type == "elliptic"
        assert config.semi_major_axis == 1.0
        assert config.eccentricity == 0.0167
        assert config.period == 365.25

    def test_elliptic_orbit_defaults(self):
        """Test default values for elliptic orbit."""
        data = {"type": "elliptic"}
        config = EllipticOrbitConfig.model_validate(data)
        assert config.eccentricity == 0.0
        assert config.inclination == 0.0
        assert config.ascending_node == 0.0


class TestRotationSchemas:
    """Test rotation configuration schemas."""

    def test_uniform_rotation_valid(self):
        """Test valid uniform rotation configuration."""
        data = {
            "type": "uniform",
            "period": 24.0,
            "inclination": 23.5,
        }
        config = UniformRotationConfig.model_validate(data)
        assert config.type == "uniform"
        assert config.period == 24.0
        assert config.inclination == 23.5

    def test_fixed_rotation_valid(self):
        """Test valid fixed rotation configuration."""
        data = {
            "type": "fixed",
            "angle": 90.0,
            "axis": [0, 1, 0],
        }
        config = FixedRotationConfig.model_validate(data)
        assert config.type == "fixed"
        assert config.angle == 90.0
        assert config.axis == [0, 1, 0]

    def test_uniform_rotation_synchronous(self):
        """Test synchronous rotation flag."""
        data = {
            "type": "uniform",
            "synchronous": True,
        }
        config = UniformRotationConfig.model_validate(data)
        assert config.synchronous is True


class TestCelestialSchemas:
    """Test celestial body configuration schemas."""

    def test_star_config_minimal(self):
        """Test minimal star configuration."""
        data = {
            "type": "star",
            "name": "Sun",
        }
        config = StarConfig.model_validate(data)
        assert config.type == "star"
        assert config.name == "Sun"

    def test_star_config_full(self):
        """Test full star configuration."""
        data = {
            "type": "star",
            "name": ["Sun", "Sol"],
            "radius": 696000,
            "temperature": 5778,
            "magnitude": 4.83,
            "spectral-type": "G2V",
        }
        config = StarConfig.model_validate(data)
        assert config.name == ["Sun", "Sol"]
        assert config.radius == 696000
        assert config.temperature == 5778
        assert config.spectral_type == "G2V"

    def test_planet_config_minimal(self):
        """Test minimal planet configuration."""
        data = {
            "type": "planet",
            "name": "Earth",
        }
        config = ReflectiveBodyConfig.model_validate(data)
        assert config.type == "planet"
        assert config.name == "Earth"
        assert config.albedo == 0.5

    def test_planet_config_with_inline_orbit(self):
        """Test planet with inline orbit configuration."""
        data = {
            "type": "planet",
            "name": "Mars",
            "orbit": {
                "type": "elliptic",
                "semi-major-axis": 1.524,
                "eccentricity": 0.0934,
            },
        }
        config = ReflectiveBodyConfig.model_validate(data)
        assert config.name == "Mars"
        # The orbit should be parsed as a dict
        assert config.orbit == {
            "type": "elliptic",
            "semi-major-axis": 1.524,
            "eccentricity": 0.0934,
        }

    def test_planet_config_with_orbit_reference(self):
        """Test planet with named reference orbit."""
        data = {
            "type": "planet",
            "name": "Mars",
            "orbit": "mars-orbit",
        }
        config = ReflectiveBodyConfig.model_validate(data)

        # The orbit should be kept as a string
        # The actual resolution happens in a later phase
        assert config.orbit == "mars-orbit"

    def test_planet_config_nested_surfaces(self):
        """Test planet with nested surface configurations."""
        data = {
            "type": "planet",
            "name": "Mars",
            "surfaces": [
                {
                    "category": "visible",
                    "appearance": {"texture": "mars.jpg"},
                }
            ],
        }
        config = ReflectiveBodyConfig.model_validate(data)
        assert config.surfaces is not None
        assert len(config.surfaces) == 1


class TestSurfaceSchemas:
    """Test surface configuration schemas."""

    def test_appearance_config(self):
        """Test appearance configuration."""
        data = {
            "texture": "earth.jpg",
            "tint": [1, 0.5, 0.5],
            "transparency": True,
        }
        config = TexturesAppearanceConfig.model_validate(data)
        assert config.texture == "earth.jpg"
        assert config.tint == [1, 0.5, 0.5]
        assert config.transparency is True

    def test_surface_config_minimal(self):
        """Test minimal surface configuration."""
        data = {
            "category": "visible",
        }
        config = SurfaceConfig.model_validate(data)
        assert config.category == "visible"

    def test_surface_config_with_nested(self):
        """Test surface with nested appearance."""
        data = {
            "category": "visible",
            "appearance": {
                "texture": "mars.jpg",
                "albedo": 0.25,
            },
        }
        config = SurfaceConfig.model_validate(data)
        assert config.category == "visible"
        assert config.appearance is not None


class TestConfigBaseFeatures:
    """Test ConfigBase features like to_dict()."""

    def test_to_dict_conversion(self):
        """Test converting config back to dict."""
        data = {
            "type": "star",
            "name": "Sun",
            "temperature": 5778,
        }
        config = StarConfig.model_validate(data)
        result = config.to_dict()

        assert isinstance(result, dict)
        assert result["type"] == "star"
        assert result["name"] == "Sun"
        assert result["temperature"] == 5778

    def test_to_dict_kebab_case_aliases(self):
        """Test that to_dict() uses kebab-case aliases."""
        data = {
            "type": "reflective",
            "name": "Mars",
            "body-class": "planet",
        }
        config = ReflectiveBodyConfig.model_validate(data)
        result = config.to_dict()

        # Should use the alias
        assert "body-class" in result
