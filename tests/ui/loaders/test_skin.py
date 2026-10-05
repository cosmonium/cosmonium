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

import os
import tempfile

import pytest
from panda3d.core import LColor
from pydantic import ValidationError

from cosmonium.parsers.validator import ConfigValidator
from cosmonium.ui.config.models import SkinRootConfig, SkinVariablesConfig, SkinVariantConfig
from cosmonium.ui.loaders.skin import SkinLoader, resolve_variables
from cosmonium.ui.skin import UISkin


@pytest.fixture
def yaml_file():
    """Write YAML content to a temporary file and return its path, cleaning up afterwards."""
    paths = []

    def _write(content):
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yaml') as f:
            f.write(content)
            paths.append(f.name)
        return f.name

    yield _write

    for path in paths:
        os.unlink(path)


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


class TestRootFontSize:
    """Tests for SkinLoader.resolve_root_font_size() and UISkin default root font size."""

    def test_default_matches_declared_constant(self):
        skin = UISkin()

        assert skin.root_font_size == UISkin.DEFAULT_ROOT_FONT_SIZE

    def test_plain_number_is_accepted(self):
        root_config = SkinRootConfig(element='root', **{'font-size': 20})

        root_font_size = SkinLoader.resolve_root_font_size(root_config)

        assert root_font_size == 20.0

    def test_px_string_is_accepted(self):
        root_config = SkinRootConfig(element='root', **{'font-size': '18px'})

        root_font_size = SkinLoader.resolve_root_font_size(root_config)

        assert root_font_size == 18.0

    def test_no_font_size_returns_none(self):
        root_config = SkinRootConfig(element='root')

        root_font_size = SkinLoader.resolve_root_font_size(root_config)

        assert root_font_size is None

    def test_em_or_rem_value_is_rejected(self, caplog):
        root_config = SkinRootConfig(element='root', **{'font-size': '1.5em'})

        root_font_size = SkinLoader.resolve_root_font_size(root_config, context='test-context')

        assert root_font_size is None
        assert "Invalid root font-size" in caplog.text
        assert 'test-context' in caplog.text


class TestSkinVariantConfig:
    """Tests for the SkinVariantConfig model that validates a skin variant file."""

    def test_a_variant_validates(self):
        config = SkinVariantConfig(label='Light', variables={'bg-base': '#ffffff'})

        assert config.label == 'Light'
        assert config.variables == {'bg-base': '#ffffff'}

    def test_label_is_optional(self):
        config = SkinVariantConfig(variables={'bg-base': '#ffffff'})

        assert config.label is None

    def test_variables_default_to_empty(self):
        config = SkinVariantConfig()

        assert config.variables == {}

    def test_extra_keys_are_rejected(self):
        with pytest.raises(ValidationError):
            SkinVariantConfig(variables={'bg-base': '#ffffff'}, element='button')


class TestSkinLoaderVariants:
    """Tests for SkinLoader.load_variant() and SkinLoader.load() with a variant applied."""

    def test_load_variant_returns_label_and_variables(self, yaml_file):
        variant_file = yaml_file("""
label: Light
variables:
  bg-base: "#ffffff"
""")
        loader = SkinLoader(None, ConfigValidator())

        variant = loader.load_variant(variant_file)

        assert variant.label == 'Light'
        assert variant.variables == {'bg-base': '#ffffff'}

    def test_variant_overrides_the_base_skins_variables(self, yaml_file):
        skin_file = yaml_file("""
- variables:
    bg-base: "#000000"
- element: button
  background-color: var(bg-base)
""")
        variant_file = yaml_file("""
label: Light
variables:
  bg-base: "#ffffff"
""")
        loader = SkinLoader(None, ConfigValidator())

        skin = loader.load(skin_file, variant_filepath=variant_file)

        assert skin.entries[0].background_color == LColor(1, 1, 1, 1)

    def test_variant_only_overrides_variables_it_declares(self, yaml_file):
        skin_file = yaml_file("""
- variables:
    bg-base: "#000000"
    accent: "#3388ff"
- element: button
  background-color: var(bg-base)
  border-color: var(accent)
""")
        variant_file = yaml_file("""
variables:
  bg-base: "#ffffff"
""")
        loader = SkinLoader(None, ConfigValidator())

        skin = loader.load(skin_file, variant_filepath=variant_file)

        assert skin.entries[0].background_color == LColor(1, 1, 1, 1)
        assert skin.entries[0].border_color == LColor(0x33 / 255, 0x88 / 255, 1, 1)

    def test_no_variant_keeps_the_base_skins_own_variables(self, yaml_file):
        skin_file = yaml_file("""
- variables:
    bg-base: "#000000"
- element: button
  background-color: var(bg-base)
""")
        loader = SkinLoader(None, ConfigValidator())

        skin = loader.load(skin_file)

        assert skin.entries[0].background_color == LColor(0, 0, 0, 1)
