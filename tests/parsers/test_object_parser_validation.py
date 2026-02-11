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


"""Tests for ObjectYamlParser Pydantic validation integration."""

import pytest

from cosmonium.parsers.objectparser import ObjectYamlParser
from cosmonium.parsers.schemas.stellarobjects import ReflectiveBodyConfig, StarConfig


class TestObjectParserValidation:
    """Test ObjectYamlParser validation integration."""

    def test_models_dict_exists(self):
        """Test that ObjectYamlParser has models dict."""
        assert hasattr(ObjectYamlParser, 'models')
        assert isinstance(ObjectYamlParser.models, dict)

    def test_model_registration(self):
        """Test that models can be registered."""
        # Manually register for testing
        ObjectYamlParser.models['test-star'] = StarConfig
        assert 'test-star' in ObjectYamlParser.models
        assert ObjectYamlParser.models['test-star'] == StarConfig

    def test_validate_star(self):
        """Test validation of star data."""
        ObjectYamlParser.models['star'] = StarConfig

        star_data = {'type': 'star', 'name': 'TestStar', 'radius': 696000, 'temperature': 5778}

        validated = ObjectYamlParser.validate_and_decode('star', star_data)
        assert isinstance(validated, StarConfig)
        assert validated.name == 'TestStar'
        assert validated.radius == 696000
        assert validated.temperature == 5778

    def test_validate_planet(self):
        """Test validation of planet data."""
        ObjectYamlParser.models['planet'] = ReflectiveBodyConfig

        planet_data = {'type': 'planet', 'name': 'Mars', 'radius': 3396, 'albedo': 0.25}

        validated = ObjectYamlParser.validate_and_decode('planet', planet_data)
        assert isinstance(validated, ReflectiveBodyConfig)
        assert validated.name == 'Mars'
        assert validated.radius == 3396
        assert validated.albedo == 0.25

    def test_validation_error_fallback(self):
        """Test that validation errors raise ValueErrors."""
        ObjectYamlParser.models['star'] = StarConfig

        invalid_data = {
            'type': 'star',
            'name': 123,  # Should be string
        }
        with pytest.raises(ValueError):
            ObjectYamlParser.validate_and_decode('star', invalid_data)

    def test_unregistered_type_returns_dict(self):
        """Test that unregistered types return raw dict."""
        unknown_data = {'key': 'value'}
        result = ObjectYamlParser.validate_and_decode('unknown-type', unknown_data)
        assert result == unknown_data
