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

from math import pi

import pytest
from panda3d.core import LColor, LPoint3d, LVector3d

from cosmonium.parsers.schemas.appearance import TexturesAppearanceConfig
from cosmonium.parsers.schemas.orbit import EllipticOrbitConfig, FixedOrbitConfig
from cosmonium.parsers.schemas.rotation import FixedRotationConfig, UniformRotationConfig
from cosmonium.parsers.schemas.stellarobjects import ReflectiveBodyConfig, StarConfig, StellarRingsConfig
from cosmonium.parsers.schemas.surface import SurfaceConfig
from cosmonium.parsers.schemas.types import ValueWithUnits


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
        assert config.position == LPoint3d(0, 0, 0)

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
        assert isinstance(config.semi_major_axis, ValueWithUnits)
        assert config.semi_major_axis.value == 1.0
        assert config.semi_major_axis.unit == 'au'
        assert config.eccentricity == 0.0167
        assert isinstance(config.period, ValueWithUnits)
        assert config.period.value == 365.25
        assert config.period.unit == 'year'

    def test_elliptic_orbit_explicit_units(self):
        """Test elliptic orbit with explicit unit strings."""
        data = {
            "type": "elliptic",
            "semi-major-axis": [150000000, "km"],
            "period": [365.25, "day"],
        }
        config = EllipticOrbitConfig.model_validate(data)
        assert config.semi_major_axis.value == 150000000.0
        assert config.semi_major_axis.unit == 'km'
        assert config.period.value == 365.25
        assert config.period.unit == 'day'

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
        assert isinstance(config.period, ValueWithUnits)
        assert config.period.value == 24.0
        assert config.period.unit == 'year'
        assert isinstance(config.inclination, ValueWithUnits)
        assert config.inclination.value == 23.5
        assert config.inclination.unit == 'deg'

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
        assert config.axis == LVector3d(0, 1, 0)

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
        # radius is now a ValueWithUnits (default unit: km)
        assert isinstance(config.radius, ValueWithUnits)
        assert config.radius.value == 696000.0
        assert config.radius.unit == 'km'
        assert config.radius.scaled_value == 696000.0
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
        assert config.tint == LColor(1.0, 0.5, 0.5, 1.0)
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


class TestPandaFieldTypes:
    """Test custom Pydantic field types for Panda3D math objects."""

    # ------------------------------------------------------------------
    # Vector3Field
    # ------------------------------------------------------------------

    def test_lvector3d_from_list(self):
        """3-element list is accepted and stores 3 floats."""
        config = FixedRotationConfig.model_validate({"type": "fixed", "axis": [0.0, 1.0, 0.0]})
        assert config.axis == LVector3d(0.0, 1.0, 0.0)

    def test_lvector3d_from_int_list(self):
        """Integer elements are coerced to float."""
        config = FixedRotationConfig.model_validate({"type": "fixed", "axis": [1, 0, 0]})
        assert config.axis == LVector3d(1.0, 0.0, 0.0)

    def test_lvector3d_wrong_length_raises(self):
        """A list with the wrong number of elements must raise a validation error."""
        with pytest.raises(Exception):
            FixedRotationConfig.model_validate({"type": "fixed", "axis": [0, 1]})

    def test_lvector3d_non_numeric_raises(self):
        """Non-numeric elements must raise a validation error."""
        with pytest.raises(Exception):
            FixedRotationConfig.model_validate({"type": "fixed", "axis": ["a", "b", "c"]})

    def test_lvector3d_none_preserved(self):
        """Optional field with None input stays None."""
        config = FixedRotationConfig.model_validate({"type": "fixed"})
        assert config.axis is None

    def test_lvector3d_serializes_to_list(self):
        """model_dump() must return a plain list so configs can be round-tripped."""
        config = FixedRotationConfig.model_validate({"type": "fixed", "axis": [0, 0, 1]})
        result = config.model_dump()
        assert isinstance(result["axis"], list)
        assert result["axis"] == [0.0, 0.0, 1.0]

    # ------------------------------------------------------------------
    # Point3Field (via FixedOrbitConfig)
    # ------------------------------------------------------------------

    def test_lpoint3d_from_list(self):
        """3-element list is accepted for a point field."""
        config = FixedOrbitConfig.model_validate({"type": "fixed", "position": [1, 2, 3]})
        assert config.position == LPoint3d(1.0, 2.0, 3.0)

    def test_lpoint3d_wrong_length_raises(self):
        with pytest.raises(Exception):
            FixedOrbitConfig.model_validate({"type": "fixed", "position": [1, 2]})

    # ------------------------------------------------------------------
    # ColorField (via TexturesAppearanceConfig)
    # ------------------------------------------------------------------

    def test_lcolor_3_components_gets_alpha(self):
        """A 3-element RGB list gets alpha=1.0 appended."""
        config = TexturesAppearanceConfig.model_validate({"tint": [0.5, 0.3, 0.1]})
        assert config.tint == LColor(0.5, 0.3, 0.1, 1.0)

    def test_lcolor_4_components_preserved(self):
        """A 4-element RGBA list is stored as-is."""
        config = TexturesAppearanceConfig.model_validate({"tint": [0.5, 0.3, 0.1, 0.8]})
        assert config.tint == LColor(0.5, 0.3, 0.1, 0.8)

    def test_lcolor_wrong_length_raises(self):
        """1 or 2-element inputs are rejected."""
        with pytest.raises(Exception):
            TexturesAppearanceConfig.model_validate({"tint": [1.0, 0.5]})

    def test_lcolor_5_components_raises(self):
        """5-element input is rejected."""
        with pytest.raises(Exception):
            TexturesAppearanceConfig.model_validate({"tint": [1.0, 0.5, 0.2, 1.0, 0.5]})

    def test_lcolor_serializes_to_list(self):
        """model_dump() must return a plain 4-element list."""
        config = TexturesAppearanceConfig.model_validate({"tint": [1, 0, 0]})
        result = config.model_dump()
        assert isinstance(result["tint"], list)
        assert result["tint"] == [1.0, 0.0, 0.0, 1.0]


class TestValueWithUnitsTypes:
    """Test value-with-units Pydantic field types (distance, angle, time)."""

    # ------------------------------------------------------------------
    # ValueWithUnits basics
    # ------------------------------------------------------------------

    def test_value_with_units_namedtuple(self):
        """ValueWithUnits stores value, unit, scale and computes scaled_value."""
        v = ValueWithUnits(90.0, 'deg', pi / 180.0)
        assert v.value == 90.0
        assert v.unit == 'deg'
        assert abs(v.scaled_value - pi / 2) < 1e-10

    # ------------------------------------------------------------------
    # DistanceAUField
    # ------------------------------------------------------------------

    def test_distance_bare_float_uses_default_unit(self):
        """Bare float uses the default unit (AU for DistanceAUField)."""
        config = EllipticOrbitConfig.model_validate({"type": "elliptic", "semi-major-axis": 1.0})
        v = config.semi_major_axis
        assert isinstance(v, ValueWithUnits)
        assert v.value == 1.0
        assert v.unit == 'au'
        # scaled_value should be ~149 597 870.7 km
        assert abs(v.scaled_value - 149597870.7) < 0.1

    def test_distance_explicit_km(self):
        """Explicit [value, 'km'] pair."""
        config = EllipticOrbitConfig.model_validate({"type": "elliptic", "semi-major-axis": [149597870.7, "km"]})
        v = config.semi_major_axis
        assert v.unit == 'km'
        assert abs(v.scaled_value - 149597870.7) < 0.1

    def test_distance_none_optional(self):
        """Optional distance field returns None when not provided."""
        config = EllipticOrbitConfig.model_validate({"type": "elliptic"})
        assert config.semi_major_axis is None

    def test_distance_invalid_unit_raises(self):
        """Unknown unit string raises a validation error."""
        with pytest.raises(Exception):
            EllipticOrbitConfig.model_validate({"type": "elliptic", "semi-major-axis": [1.0, "furlongs"]})

    def test_distance_serializes_to_list(self):
        """model_dump() returns [value, unit_str]."""
        config = EllipticOrbitConfig.model_validate({"type": "elliptic", "semi-major-axis": 1.0})
        result = config.model_dump()
        assert result["semi_major_axis"] == [1.0, 'au']

    # ------------------------------------------------------------------
    # DistanceMField (heightmap defaults)
    # ------------------------------------------------------------------

    def test_distance_m_default_unit(self):
        """DistanceMField uses metres as default unit."""
        from cosmonium.parsers.schemas.heightmap import HeightmapConfig

        config = HeightmapConfig.model_validate({"height_scale": 1000.0})
        v = config.height_scale
        assert v.unit == 'm'
        # 1000 m → 1.0 km
        assert abs(v.scaled_value - 1.0) < 1e-10

    def test_distance_m_explicit_km(self):
        """DistanceMField accepts explicit km unit."""
        from cosmonium.parsers.schemas.heightmap import HeightmapConfig

        config = HeightmapConfig.model_validate({"height_scale": [1.0, "km"]})
        v = config.height_scale
        assert v.unit == 'km'
        assert v.scaled_value == 1.0

    # ------------------------------------------------------------------
    # TimeYearField
    # ------------------------------------------------------------------

    def test_time_bare_float_uses_year(self):
        """Bare float uses year as default unit."""
        config = EllipticOrbitConfig.model_validate({"type": "elliptic", "period": 1.0})
        v = config.period
        assert v.unit == 'year'
        # 1 Julian year = 365.25 days
        assert abs(v.scaled_value - 365.25) < 1e-9

    def test_time_explicit_day(self):
        """Explicit [value, 'day'] pair."""
        config = EllipticOrbitConfig.model_validate({"type": "elliptic", "period": [365.25, "day"]})
        v = config.period
        assert v.unit == 'day'
        assert v.scaled_value == 365.25

    def test_time_explicit_sec(self):
        """Explicit [value, 'sec'] pair."""
        config = EllipticOrbitConfig.model_validate({"type": "elliptic", "period": [86400.0, "sec"]})
        v = config.period
        assert v.unit == 'sec'
        assert abs(v.scaled_value - 1.0) < 1e-6  # 86400 s = 1 day

    # ------------------------------------------------------------------
    # AngleDegField
    # ------------------------------------------------------------------

    def test_angle_bare_float_uses_deg(self):
        """Bare float uses degrees as default unit."""
        config = UniformRotationConfig.model_validate({"type": "uniform", "inclination": 90.0})
        v = config.inclination
        assert v.unit == 'deg'
        assert abs(v.scaled_value - pi / 2) < 1e-10

    def test_angle_explicit_rad(self):
        """Explicit [value, 'rad'] pair."""
        config = UniformRotationConfig.model_validate({"type": "uniform", "inclination": [1.5707963, "rad"]})
        v = config.inclination
        assert v.unit == 'rad'
        assert abs(v.scaled_value - 1.5707963) < 1e-7

    def test_angle_default_zero(self):
        """Default 0.0 inclination becomes ValueWithUnits(0, 'deg', ...)."""
        config = UniformRotationConfig.model_validate({"type": "uniform"})
        v = config.inclination
        assert isinstance(v, ValueWithUnits)
        assert v.value == 0.0
        assert v.scaled_value == 0.0

    def test_angle_invalid_unit_raises(self):
        """Unknown angle unit raises a validation error."""
        with pytest.raises(Exception):
            UniformRotationConfig.model_validate({"type": "uniform", "inclination": [45.0, "gradians"]})

    # ------------------------------------------------------------------
    # AngleSpeedDegPerDayField
    # ------------------------------------------------------------------

    def test_angle_speed_default_unit(self):
        """AngleSpeedDegPerDayField defaults to deg/day."""
        config = EllipticOrbitConfig.model_validate({"type": "elliptic", "mean-motion": 0.9856})
        v = config.mean_motion
        assert v.unit == 'deg/day'
        assert v.value == 0.9856

    # ------------------------------------------------------------------
    # Serialization round-trip
    # ------------------------------------------------------------------

    def test_unit_field_serializes_to_list(self):
        """All unit fields serialize to [value, unit_str] lists."""
        config = EllipticOrbitConfig.model_validate(
            {
                "type": "elliptic",
                "semi-major-axis": 1.0,
                "period": [365.25, "day"],
            }
        )
        result = config.model_dump()
        assert result["semi_major_axis"] == [1.0, 'au']
        assert result["period"] == [365.25, 'day']


class TestSurfaceAndBodyDistanceFields:
    """Tests for distance unit fields in surface, body, and ring schemas."""

    # ------------------------------------------------------------------
    # StellarBodyConfig / StarConfig
    # ------------------------------------------------------------------

    def test_star_radius_bare_float_km(self):
        """Star radius bare float uses km as default unit."""
        config = StarConfig.model_validate({"type": "star", "name": "Sun", "radius": 696000})
        assert isinstance(config.radius, ValueWithUnits)
        assert config.radius.value == 696000.0
        assert config.radius.unit == 'km'
        assert config.radius.scaled_value == 696000.0

    def test_star_radius_explicit_au(self):
        """Star radius accepts explicit AU unit."""
        config = StarConfig.model_validate({"type": "star", "name": "Sun", "radius": [0.00465, "au"]})
        assert config.radius.unit == 'au'
        # 0.00465 au × 149597870.7 km/au ≈ 695629 km
        assert abs(config.radius.scaled_value - 0.00465 * 149597870.7) < 1.0

    def test_planet_diameter_converts_to_km(self):
        """Planet diameter bare float is in km, scaled_value / 2 gives radius."""
        config = ReflectiveBodyConfig.model_validate({"type": "planet", "name": "Earth", "diameter": 12742})
        assert isinstance(config.diameter, ValueWithUnits)
        assert config.diameter.value == 12742.0
        assert config.diameter.unit == 'km'
        assert config.diameter.scaled_value == 12742.0

    def test_planet_radius_none(self):
        """Radius is optional and defaults to None."""
        config = ReflectiveBodyConfig.model_validate({"type": "planet", "name": "Earth"})
        assert config.radius is None

    def test_planet_radius_invalid_unit_raises(self):
        """Unknown unit string raises a validation error."""
        with pytest.raises(Exception):
            ReflectiveBodyConfig.model_validate({"type": "planet", "name": "X", "radius": [6371, "miles"]})

    def test_planet_radius_serializes_to_list(self):
        """Planet radius serializes to [value, unit_str]."""
        config = ReflectiveBodyConfig.model_validate({"type": "planet", "name": "Earth", "radius": 6371})
        result = config.model_dump()
        assert result["radius"] == [6371.0, 'km']

    # ------------------------------------------------------------------
    # SurfaceConfig
    # ------------------------------------------------------------------

    def test_surface_radius_bare_float_km(self):
        """Surface radius bare float uses km as default unit."""
        config = SurfaceConfig.model_validate({"radius": 6371})
        assert isinstance(config.radius, ValueWithUnits)
        assert config.radius.unit == 'km'
        assert config.radius.scaled_value == 6371.0

    def test_surface_diameter_field(self):
        """Surface supports diameter field with unit."""
        config = SurfaceConfig.model_validate({"diameter": [12742, "km"]})
        assert config.diameter.value == 12742.0
        assert config.diameter.scaled_value == 12742.0

    def test_surface_ellipticity_field(self):
        """Surface ellipticity replaces old oblateness field."""
        config = SurfaceConfig.model_validate({"radius": 6378, "ellipticity": 0.0034})
        assert config.ellipticity == 0.0034

    def test_surface_axes_field(self):
        """Surface axes (ellipsoid semi-axes) accepted as 3-element list."""
        config = SurfaceConfig.model_validate({"axes": [6378, 6378, 6357]})
        assert list(config.axes) == [6378.0, 6378.0, 6357.0]

    def test_surface_radius_none(self):
        """Surface radius defaults to None."""
        config = SurfaceConfig.model_validate({})
        assert config.radius is None

    # ------------------------------------------------------------------
    # StellarRingsConfig
    # ------------------------------------------------------------------

    def test_rings_inner_outer_bare_float(self):
        """Ring inner/outer radii bare floats use km as default unit."""
        config = StellarRingsConfig.model_validate({
            "type": "rings",
            "name": "Saturn-rings",
            "inner-radius": 74500,
            "outer-radius": 140200,
        })
        assert isinstance(config.inner_radius, ValueWithUnits)
        assert config.inner_radius.unit == 'km'
        assert config.inner_radius.scaled_value == 74500.0
        assert config.outer_radius.scaled_value == 140200.0

    def test_rings_inner_outer_explicit_au(self):
        """Ring inner/outer radii accept explicit AU unit."""
        config = StellarRingsConfig.model_validate({
            "type": "rings",
            "name": "Saturn-rings",
            "inner-radius": [0.000498, "au"],
            "outer-radius": [0.000937, "au"],
        })
        assert config.inner_radius.unit == 'au'
        assert abs(config.inner_radius.scaled_value - 0.000498 * 149597870.7) < 1.0

    def test_rings_serializes_to_list(self):
        """Ring radii serialize to [value, unit_str]."""
        config = StellarRingsConfig.model_validate({
            "type": "rings",
            "name": "X",
            "inner-radius": 74500,
            "outer-radius": 140200,
        })
        result = config.model_dump()
        assert result["inner_radius"] == [74500.0, 'km']
        assert result["outer_radius"] == [140200.0, 'km']
