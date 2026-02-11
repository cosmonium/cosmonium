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


"""
Tests for the loading and parsing infrastructure.

Tests the YAML related classes:
1. YamlLoader - YAML I/O
3. YamlParser - Object instantiation
"""

import io

from cosmonium.parsers.yamlloader import YamlLoader
from cosmonium.parsers.yamlparser import YamlParser


class TestYamlLoader:
    """Test YamlLoader I/O layer."""

    def test_parse_simple_yaml(self):
        """Test parsing YAML text to dictionary."""
        yaml_text = """
        name: Test
        value: 42
        nested:
          key: value
        """
        data = YamlLoader.parse(yaml_text)

        assert data is not None
        assert data['name'] == 'Test'
        assert data['value'] == 42
        assert data['nested']['key'] == 'value'

    def test_parse_invalid_yaml(self):
        """Test parsing invalid YAML returns None."""
        yaml_text = """
        invalid: [unclosed
        """
        data = YamlLoader.parse(yaml_text)
        assert data is None

    def test_store_and_parse_roundtrip(self):
        """Test storing and parsing round-trip."""
        original = {'name': 'Test', 'value': 42, 'list': [1, 2, 3]}

        # Store to string
        stream = io.StringIO()
        YamlLoader.store(original, stream)

        # Parse back
        stream.seek(0)
        result = YamlLoader.parse(stream)

        assert result == original


class TestYamlParser:
    """Test YamlParser layer (deprecated))."""

    def test_decode_passthrough(self):
        """Test basic YamlParser decode."""
        parser = YamlParser()
        data = {'key': 'value'}

        result = parser.decode(data)
        assert result == data

    def test_backward_compatible_wrappers(self):
        """Test backward compatibility wrappers delegate to YamlLoader."""
        parser = YamlParser()

        # Test parse wrapper
        yaml_text = "key: value"
        result = parser.parse(yaml_text)
        assert result == {'key': 'value'}

        # Test store wrapper
        stream = io.StringIO()
        parser.store({'test': 123}, stream)
        stream.seek(0)
        assert stream.read() == "test: 123\n"
