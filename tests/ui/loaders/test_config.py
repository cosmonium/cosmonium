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
Unit tests for UIConfigLoader's active skin variant selection.
"""

import os
import tempfile

import pytest
from panda3d.core import LColor

from cosmonium import settings
from cosmonium.ui.loaders.config import UIConfigLoader
from cosmonium.ui.loaders.init import init_widget_loaders


class MockGlobalVars:
    """Mock global variables for testing."""

    globals: dict = {}


class MockGUI:
    """Mock GUI class for testing."""

    global_vars = MockGlobalVars()


@pytest.fixture
def init_registry(scope='module'):
    init_widget_loaders()


def _write(path, content):
    with open(path, 'w') as f:
        f.write(content)


@pytest.fixture
def basic_ui_config():
    """A minimal ui.yaml with a base skin and two color-variable-only variants."""
    with tempfile.TemporaryDirectory() as ui_config_dir:
        _write(
            os.path.join(ui_config_dir, 'skin.yaml'),
            """
- variables:
    bg-base: "#000000"
- element: button
  background-color: var(bg-base)
""",
        )
        _write(
            os.path.join(ui_config_dir, 'dark.yaml'),
            """
label: Dark
variables:
  bg-base: "#000000"
""",
        )
        _write(
            os.path.join(ui_config_dir, 'light.yaml'),
            """
label: Light
variables:
  bg-base: "#ffffff"
""",
        )
        ui_config_file = os.path.join(ui_config_dir, 'ui.yaml')
        _write(
            ui_config_file,
            """
skin: skin.yaml
skin_variants:
  dark: dark.yaml
  light: light.yaml
default_skin_variant: dark
""",
        )
        yield ui_config_file


@pytest.fixture(autouse=True)
def restore_ui_skin_variant_setting():
    saved = settings.ui_skin_variant
    yield
    settings.ui_skin_variant = saved


class TestUIConfigLoaderSkinVariants:
    """Tests for the active skin variant selection in UIConfigLoader.load()."""

    def test_uses_the_configs_default_variant_when_no_setting_is_stored(self, init_registry, basic_ui_config):
        settings.ui_skin_variant = None
        gui = MockGUI()
        gui.skin_variant_override = None

        UIConfigLoader(gui).load(basic_ui_config)

        assert gui.active_skin_variant == 'dark'
        assert gui.skin.entries[0].background_color == LColor(0, 0, 0, 1)

    def test_a_stored_setting_overrides_the_configs_default(self, init_registry, basic_ui_config):
        settings.ui_skin_variant = 'light'
        gui = MockGUI()
        gui.skin_variant_override = None
        UIConfigLoader(gui).load(basic_ui_config)

        assert gui.active_skin_variant == 'light'
        assert gui.skin.entries[0].background_color == LColor(1, 1, 1, 1)

    def test_an_unknown_stored_variant_falls_back_to_the_configs_default(self, init_registry, basic_ui_config):
        settings.ui_skin_variant = 'nonexistent'
        gui = MockGUI()
        gui.skin_variant_override = None

        UIConfigLoader(gui).load(basic_ui_config)

        assert gui.active_skin_variant == 'dark'
        assert gui.skin.entries[0].background_color == LColor(0, 0, 0, 1)

    def test_available_variants_are_exposed_with_their_labels(self, init_registry, basic_ui_config):
        gui = MockGUI()
        gui.skin_variant_override = None

        UIConfigLoader(gui).load(basic_ui_config)

        assert {variant_id: variant.label for variant_id, variant in gui.skin_variants.items()} == {
            'dark': 'Dark',
            'light': 'Light',
        }

    def test_a_command_line_override_wins_over_the_stored_setting(self, init_registry, basic_ui_config):
        settings.ui_skin_variant = 'dark'
        gui = MockGUI()
        gui.skin_variant_override = 'light'

        UIConfigLoader(gui).load(basic_ui_config)

        assert gui.active_skin_variant == 'light'
        assert gui.skin.entries[0].background_color == LColor(1, 1, 1, 1)

    def test_an_unknown_command_line_override_falls_back_to_the_configs_default(self, init_registry, basic_ui_config):
        settings.ui_skin_variant = 'light'
        gui = MockGUI()
        gui.skin_variant_override = 'nonexistent'

        UIConfigLoader(gui).load(basic_ui_config)

        assert gui.active_skin_variant == 'dark'
        assert gui.skin.entries[0].background_color == LColor(0, 0, 0, 1)

    def test_no_command_line_override_falls_back_to_the_stored_setting(self, init_registry, basic_ui_config):
        settings.ui_skin_variant = 'light'
        gui = MockGUI()
        gui.skin_variant_override = None

        UIConfigLoader(gui).load(basic_ui_config)

        assert gui.active_skin_variant == 'light'
