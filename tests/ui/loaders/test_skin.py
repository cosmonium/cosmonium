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
Unit tests for the skin loader.
"""

import pytest
from pydantic import ValidationError

from cosmonium.ui.config.models import SkinVariablesConfig
from cosmonium.ui.loaders.skin import resolve_variables


class TestResolveVariables:
    """Tests for skin variables resolution."""

    def test_whole_value_reference_preserves_type(self):
        variables = {'spacing': 8}
        assert resolve_variables('var(spacing)', variables) == 8

    def test_whole_value_reference_to_a_list_preserves_the_list(self):
        variables = {'accent': [1.0, 0.5, 0.25, 1.0]}
        assert resolve_variables('var(accent)', variables) == [1.0, 0.5, 0.25, 1.0]

    def test_reference_embedded_in_a_larger_string_is_stringified(self):
        variables = {'spacing': '8px'}
        assert resolve_variables('var(spacing) 0px', variables) == '8px 0px'

    def test_multiple_references_in_one_string(self):
        variables = {'a': '1px', 'b': '2px'}
        assert resolve_variables('var(a) var(b) var(a) var(b)', variables) == '1px 2px 1px 2px'

    def test_non_string_scalars_pass_through_unchanged(self):
        assert resolve_variables(42, {}) == 42
        assert resolve_variables(None, {}) is None

    def test_recurses_into_lists_and_dicts(self):
        variables = {'x': 'resolved'}
        assert resolve_variables(['var(x)', 'literal'], variables) == ['resolved', 'literal']
        assert resolve_variables({'key': 'var(x)'}, variables) == {'key': 'resolved'}

    def test_undefined_variable_is_reported_and_left_as_is(self, caplog):
        result = resolve_variables('var(missing)', {}, context='test-context')
        assert result == 'var(missing)'
        assert "Undefined skin variable 'var(missing)'" in caplog.text
        assert 'test-context' in caplog.text

    def test_string_without_any_reference_is_unchanged(self):
        assert resolve_variables('#FF0000', {}) == '#FF0000'


class TestSkinVariablesConfig:
    """Tests for the SkinVariablesConfig model that validates `variables:` blocks."""

    def test_a_variables_block_validates(self):
        config = SkinVariablesConfig(variables={'primary-color': '#3388FF', 'spacing': '8px'})

        assert config.variables == {'primary-color': '#3388FF', 'spacing': '8px'}

    def test_a_non_dict_variables_block_is_rejected(self):
        with pytest.raises(ValidationError):
            SkinVariablesConfig(variables='not-a-dict')

    def test_extra_keys_alongside_variables_are_rejected(self):
        with pytest.raises(ValidationError):
            SkinVariablesConfig(variables={'a': 1}, element='button')
