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
import tempfile

import pytest
from panda3d.core import LColor
from pydantic import BaseModel, Field

from cosmonium.parsers.validator import ConfigValidator
from cosmonium.ui.config.models import ButtonWidgetConfig, OptionMenuWidgetConfig, SpacerWidgetConfig, TextWidgetConfig
from cosmonium.ui.dock.dock import Dock
from cosmonium.ui.hud.dynamictextblock import DynamicTextBlock
from cosmonium.ui.loaders.dock import DockLoader
from cosmonium.ui.loaders.hud import HUDLoader
from cosmonium.ui.loaders.init import init_widget_loaders
from cosmonium.ui.loaders.shortcuts import ShortcutsLoader
from cosmonium.ui.loaders.skin import SkinLoader
from cosmonium.ui.loaders.widgets import (
    ButtonWidgetLoader,
    OptionMenuWidgetLoader,
    SpacerWidgetLoader,
    TextWidgetLoader,
    WidgetYamlParser,
)


class MockGlobalVars:
    """Mock global variables for testing."""

    globals: dict = {}


class MockGUI:
    """Mock GUI class for testing."""

    global_vars = MockGlobalVars()


@pytest.fixture
def init_registry(scope='module'):
    init_widget_loaders()


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
            f.write("""
event-1: 1
event-2: [2, control-2]
""")
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
            f.write("""
-
  background-color: "#330100"
- element: menu
  text-color: [0, 0, 0, 1]
""")
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

    def test_load_skin_with_variables(self, validator):
        """Test that `variables:` blocks are substituted into referencing entries."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yaml') as f:
            filepath = f.name
            f.write("""
- variables:
    primary-color: "#3388FF"
    spacing: 8px
- element: button
  background-color: var(primary-color)
  padding: var(spacing)
- element: label
  padding: "var(spacing) 0px"
""")
        try:
            loader = SkinLoader(None, validator)
            skin = loader.load(filepath)

            # The variables block itself doesn't produce a skin entry.
            assert len(skin.entries) == 2

            button = skin.entries[0]
            assert button.background_color == LColor(0x33 / 255, 0x88 / 255, 0xFF / 255, 1.0)
            assert button.padding[0](None, None) == 8.0  # left, from the "var(spacing)" shorthand

            label = skin.entries[1]
            assert label.padding[0](None, None) == 0.0  # left, from "var(spacing) 0px"
            assert label.padding[3](None, None) == 8.0  # top
        finally:
            os.unlink(filepath)

    def test_load_skin_with_undefined_variable(self, validator, caplog):
        """Test that an undefined variable reference is reported and left unresolved."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yaml') as f:
            filepath = f.name
            f.write("""
- element: entry
  background-color: var(does-not-exist)
""")
        try:
            loader = SkinLoader(None, validator)
            skin = loader.load(filepath)

            assert len(skin.entries) == 1
            assert skin.entries[0].background_color is None
            assert "Undefined skin variable 'var(does-not-exist)'" in caplog.text
        finally:
            os.unlink(filepath)

    def test_load_skin_with_root_font_size_and_rem(self, validator):
        """Test that a `root` pseudo-element entry changes how `rem` lengths resolve."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yaml') as f:
            filepath = f.name
            f.write("""
- element: root
  font-size: 20px
- element: button
  font-size: 1.5rem
""")
        try:
            loader = SkinLoader(None, validator)
            skin = loader.load(filepath)

            assert skin.root_font_size == 20.0
            # The root entry doesn't produce a skin entry either.
            assert len(skin.entries) == 1
            button = skin.entries[0]
            assert button.font_size(None, skin) == 30.0  # 1.5 * 20px
        finally:
            os.unlink(filepath)


class TestDockLoader:
    """Tests for DockLoader with actual config files."""

    def test_load_test_dock(self, gui, init_registry, validator):
        """Test loading test dock configuration."""

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yaml') as f:
            filepath = f.name
            f.write("""
dock:
 - orientation: horizontal
   anchor    : bottom
   widgets:
      - type: text
        text: "A"
""")
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

    def test_load_dock_with_user_class_and_id(self, gui, init_registry, validator):
        """A dock and its widgets can carry a user-supplied class/id on top of the hardcoded ones."""

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yaml') as f:
            filepath = f.name
            f.write("""
dock:
 - id: main-dock
   class: transparent
   orientation: horizontal
   anchor    : bottom
   widgets:
      - type: button
        text: "A"
        class: [primary, danger]
        id: my-button
""")
        try:
            loader = DockLoader(gui, validator)
            docks = loader.load(filepath)

            dock = docks[0]
            assert dock.id_ == 'main-dock'
            # The user class merges with the hardcoded structural 'dock' class, it does not replace it.
            assert dock.layout.element.class_ == frozenset({'dock', 'transparent'})

            button = dock.layout.widgets[0]
            assert button.id_ == 'my-button'
            assert button.class_ == ['primary', 'danger']
        finally:
            os.unlink(filepath)


class TestHUDLoader:
    """Tests for HUDLoader with actual config files."""

    def test_load_default_hud(self, validator):
        """Test loading default HUD configuration."""

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yaml') as f:
            filepath = f.name
            f.write("""
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
""")
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

    def test_load_hud_with_user_class(self, validator):
        """A HUD widget can carry a user-supplied class, used to skin its text lines."""

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yaml') as f:
            filepath = f.name
            f.write("""
hud:
  - anchor: top-left
    id: title
    class: debug-hud
    type: text-list
    entries:
      - text: my-text
""")
        try:
            loader = HUDLoader(None, validator)
            hud = loader.load(filepath)

            assert hud[0].class_ == 'debug-hud'
        finally:
            os.unlink(filepath)


class TestWidgetLoaders:
    """Tests for widget loaders."""

    def test_button_widget_loader(self, validator):
        """Test ButtonWidgetLoader."""

        loader = ButtonWidgetLoader()

        # Test with text button
        data = {'type': 'button', 'text': 'Click me', 'event': 'test-event'}
        config = validator.validate_dict(data, ButtonWidgetConfig)
        widget = loader.decode(config, global_vars={})
        assert widget is not None
        assert widget.event == 'test-event'
        assert widget.is_icon is False

        # Test with icon button
        data = {'type': 'button', 'code': 'f001', 'event': 'test-event'}
        config = validator.validate_dict(data, ButtonWidgetConfig)
        widget = loader.decode(config, global_vars={})
        assert widget.is_icon is True

        # Test with a user-supplied class and id
        data = {'type': 'button', 'text': 'Click me', 'event': 'test-event', 'class': 'primary', 'id': 'my-button'}
        config = validator.validate_dict(data, ButtonWidgetConfig)
        widget = loader.decode(config, global_vars={})
        assert widget.class_ == 'primary'
        assert widget.id_ == 'my-button'

        # Test with an enabled expression
        class Settings:
            can_click = True

        global_vars = {'settings': Settings()}
        data = {'type': 'button', 'text': 'Click me', 'event': 'test-event', 'enabled': 'settings.can_click'}
        config = validator.validate_dict(data, ButtonWidgetConfig)
        widget = loader.decode(config, global_vars=global_vars)
        assert widget.enabled_condition.execute(global_vars) is True
        # Check that enabled condition does read the variable
        Settings.can_click = False
        assert widget.enabled_condition.execute(global_vars) is False

    def test_option_menu_widget_loader(self, validator):
        """Test OptionMenuWidgetLoader."""

        loader = OptionMenuWidgetLoader()

        data = {'type': 'option-menu', 'items': ['Low', 'Medium', 'High'], 'event': 'set-quality'}
        config = validator.validate_dict(data, OptionMenuWidgetConfig)
        widget = loader.decode(config, global_vars={})
        assert widget is not None
        assert widget.items == ['Low', 'Medium', 'High']
        assert widget.event == 'set-quality'
        assert widget.selected is None

        # Test with a user-supplied class, id and a 'selected' expression reflecting live app state
        class Settings:
            quality = 'Medium'

        global_vars = {'settings': Settings()}
        data = {
            'type': 'option-menu',
            'items': ['Low', 'Medium', 'High'],
            'event': 'set-quality',
            'selected': 'settings.quality',
            'class': 'primary',
            'id': 'my-option-menu',
        }
        config = validator.validate_dict(data, OptionMenuWidgetConfig)
        widget = loader.decode(config, global_vars=global_vars)
        assert widget.selected() == 'Medium'
        assert widget.class_ == 'primary'
        assert widget.id_ == 'my-option-menu'

        # The expression is re-evaluated on each call, reflecting the live value at read time
        Settings.quality = 'High'
        assert widget.selected() == 'High'

        # Test with an enabled expression
        Settings.can_click = True
        global_vars['settings'] = Settings()
        data = {
            'type': 'option-menu',
            'items': ['Low', 'Medium', 'High'],
            'event': 'set-quality',
            'enabled': 'settings.can_click',
        }
        config = validator.validate_dict(data, OptionMenuWidgetConfig)
        widget = loader.decode(config, global_vars=global_vars)
        assert widget.enabled_condition.execute(global_vars) is True
        # Check that enabled condition does read the variable
        Settings.can_click = False
        assert widget.enabled_condition.execute(global_vars) is False

    def test_spacer_widget_loader(self, validator):
        """Test SpacerWidgetLoader."""

        loader = SpacerWidgetLoader()

        data = {'type': 'spacer', 'size': [10, 10]}
        config = validator.validate_dict(data, SpacerWidgetConfig)
        widget = loader.decode(config, global_vars={})
        assert widget is not None

    def test_text_widget_loader(self, validator):
        """Test TextWidgetLoader."""

        loader = TextWidgetLoader()

        data = {'type': 'text', 'text': 'Hello World', 'align': 'left'}
        config = validator.validate_dict(data, TextWidgetConfig)
        widget = loader.decode(config, global_vars={})
        assert widget is not None

    def test_widget_yaml_parser(self, validator, init_registry):
        """Test WidgetYamlParser dispatch."""

        # Test loading button
        button_data = {'type': 'button', 'text': 'Test', 'event': 'test'}
        button_config = validator.validate_dict(button_data, ButtonWidgetConfig)
        button = WidgetYamlParser.decode_object(button_config, global_vars={})
        assert button is not None

        # Test loading text
        text_data = {'type': 'text', 'text': 'Test'}
        text_config = validator.validate_dict(text_data, TextWidgetConfig)
        text = WidgetYamlParser.decode_object(text_config, global_vars={})
        assert text is not None

        # Test loading spacer
        spacer_data = {'type': 'spacer', 'size': [5, 5]}
        space_config = validator.validate_dict(spacer_data, SpacerWidgetConfig)
        spacer = WidgetYamlParser.decode_object(space_config, global_vars={})
        assert spacer is not None

        # Test loading option-menu
        option_menu_data = {'type': 'option-menu', 'items': ['A', 'B'], 'event': 'test'}
        option_menu_config = validator.validate_dict(option_menu_data, OptionMenuWidgetConfig)
        option_menu = WidgetYamlParser.decode_object(option_menu_config, global_vars={})
        assert option_menu is not None

        # Test unknown type
        class UnknownConfig(BaseModel):
            type: str = Field()

        assert WidgetYamlParser.decode_object(UnknownConfig(type='unknown'), global_vars={}) is None
