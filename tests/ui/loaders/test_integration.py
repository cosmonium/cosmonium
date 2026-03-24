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
Integration tests for UI configuration loaders.

This module contains integration tests that verify the loaders work
with configuration files.
"""

import os
from pydantic import BaseModel, Field
import pytest
import tempfile

from panda3d.core import LColor

from cosmonium.ui.config.models import ButtonWidgetConfig, TextWidgetConfig, SpacerWidgetConfig
from cosmonium.ui.config.validator import ConfigValidator
from cosmonium.ui.dock.dock import Dock
from cosmonium.ui.hud.dynamictextblock import DynamicTextBlock

from cosmonium.ui.loaders.dock import DockLoader
from cosmonium.ui.loaders.hud import HUDLoader
from cosmonium.ui.loaders.init import init_widget_loaders
from cosmonium.ui.loaders.parsers import ParsersCollection
from cosmonium.ui.loaders.shortcuts import ShortcutsLoader
from cosmonium.ui.loaders.skin import SkinLoader
from cosmonium.ui.loaders.widgets import ButtonWidgetLoader, SpacerWidgetLoader, TextWidgetLoader, WidgetLoaderRegistry


class MockGlobalVars:
    """Mock global variables for testing."""
    globals: dict = {}


class MockGUI:
    """Mock GUI class for testing."""
    global_vars = MockGlobalVars()


@pytest.fixture
def init_registry(scope='module'):
    init_widget_loaders(WidgetLoaderRegistry.get_instance())


@pytest.fixture
def gui():
    return MockGUI()


@pytest.fixture
def validator():
    return ConfigValidator()


class TestShortcutsLoader:
    """Tests for ShortcutsLoader with actual config files."""

    def test_load_default_shortcuts(self, validator):
        """Test loading default shortcuts configuration."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yaml') as f:
            filepath = f.name
            f.write(
                """
event-1: 1
event-2: [2, control-2]
"""
            )
        try:
            loader = ShortcutsLoader(None, validator)
            shortcuts = loader.load(filepath)

            assert isinstance(shortcuts, list)
            assert len(shortcuts) == 2

            assert shortcuts == [('event-1', ['1']), ('event-2', ['2', 'control-2'])]
        finally:
            os.unlink(filepath)


class TestSkinLoader:
    """Tests for SkinLoader with actual config files."""

    def test_load_default_skin(self, validator):
        """Test loading default skin configuration."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yaml') as f:
            filepath = f.name
            f.write(
                """
-
  background-color: "#330100"
- element: menu
  text-color: [0, 0, 0, 1]
"""
            )
        try:
            loader = SkinLoader(None, validator)
            skin = loader.load(filepath)

            assert skin is not None
            assert hasattr(skin, 'entries')
            assert len(skin.entries) == 2

            # Check that entries have expected attributes
            entry = skin.entries[0]
            assert entry.selector is None
            assert entry.background_color == LColor(51 / 255, 1 / 255, 0, 1)
            entry = skin.entries[1]
            assert entry.selector is None
            assert entry.text_color == LColor(0, 0, 0, 1)
        finally:
            os.unlink(filepath)


class TestDockLoader:
    """Tests for DockLoader with actual config files."""

    def test_load_test_dock(self, gui, init_registry, validator):
        """Test loading test dock configuration."""

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yaml') as f:
            filepath = f.name
            f.write(
                """
dock:
 - orientation: horizontal
   anchor    : bottom
   widgets:
      - type: text
        text: "A"
"""
            )
        try:
            loader = DockLoader(gui, validator)
            docks = loader.load(filepath)

            assert isinstance(docks, list)
            assert len(docks) == 1

            dock = docks[0]
            assert isinstance(dock, Dock)
            assert dock.direction == 'horizontal'
            assert dock.location == 'bottom'
            assert len(dock.layout.widgets) == 1
        finally:
            os.unlink(filepath)


class TestHUDLoader:
    """Tests for HUDLoader with actual config files."""

    def test_load_default_hud(self, validator):
        """Test loading default HUD configuration."""

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yaml') as f:
            filepath = f.name
            f.write(
                """
hud:
  - anchor: top-left
    id: title
    type: text-list
    entries:
      - text: my-text

  - anchor: top-right
    id: right
    type: text-list
    entries:
      - text: my-other-text
"""
            )
        try:
            loader = HUDLoader(None, validator)
            hud = loader.load(filepath)

            assert isinstance(hud, list)
            assert len(hud) == 2

            entry = hud[0]
            # Check widgets structure
            assert entry.location == 'top-left'
            assert isinstance(entry, DynamicTextBlock)
            assert len(entry.entries) == 1
            assert entry.entries[0].template.expression.source == 'f"""my-text"""'
            entry = hud[1]
            # Check widgets structure
            assert entry.location == 'top-right'
            assert isinstance(entry, DynamicTextBlock)
            assert len(entry.entries) == 1
            assert entry.entries[0].template.expression.source == 'f"""my-other-text"""'
        finally:
            os.unlink(filepath)


class TestWidgetLoaders:
    """Tests for widget loaders."""

    def test_button_widget_loader(self, validator):
        """Test ButtonWidgetLoader."""

        parsers = ParsersCollection()
        loader = ButtonWidgetLoader()

        # Test with text button
        data = {'type': 'button', 'text': 'Click me', 'event': 'test-event', 'size': 32}
        config = validator.validate_dict(data, ButtonWidgetConfig)
        widget = loader.load(config, parsers, {})
        assert widget is not None
        assert widget.event == 'test-event'

    def test_text_widget_loader(self, validator):
        """Test TextWidgetLoader."""

        parsers = ParsersCollection()
        loader = TextWidgetLoader()

        data = {'type': 'text', 'text': 'Hello World', 'align': 'left'}
        config = validator.validate_dict(data, TextWidgetConfig)
        widget = loader.load(config, parsers, {})
        assert widget is not None

    def test_spacer_widget_loader(self, validator):
        """Test SpacerWidgetLoader."""

        parsers = ParsersCollection()
        loader = SpacerWidgetLoader()

        data = {'type': 'spacer', 'size': [10, 10]}
        config = validator.validate_dict(data, SpacerWidgetConfig)
        widget = loader.load(config, parsers, {})
        assert widget is not None

    def test_widget_registry(self, validator):
        """Test WidgetLoaderRegistry."""

        registry = WidgetLoaderRegistry()
        init_widget_loaders(registry)

        # Test loading button
        button_data = {'type': 'button', 'text': 'Test', 'event': 'test'}
        button_config = validator.validate_dict(button_data, ButtonWidgetConfig)
        button = registry.load(button_config, {})
        assert button is not None

        # Test loading text
        text_data = {'type': 'text', 'text': 'Test'}
        text_config = validator.validate_dict(text_data, TextWidgetConfig)
        text = registry.load(text_config, {})
        assert text is not None

        # Test loading spacer
        spacer_data = {'type': 'spacer', 'size': [5, 5]}
        space_config = validator.validate_dict(spacer_data, SpacerWidgetConfig)
        spacer = registry.load(space_config, {})
        assert spacer is not None

        # Test unknown type
        class UnknownConfig(BaseModel):
            type: str = Field()

        with pytest.raises(NotImplementedError):
            registry.load(UnknownConfig(type='unknown'), {})
