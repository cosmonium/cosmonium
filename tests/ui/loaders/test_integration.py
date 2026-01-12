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
import pytest
import tempfile

from panda3d.core import LColor

from cosmonium.ui.loaders.dock import DockLoader
from cosmonium.ui.loaders.hud import HUDLoader
from cosmonium.ui.loaders.init import init_widget_loaders
from cosmonium.ui.loaders.parsers import ParsersCollection
from cosmonium.ui.loaders.shortcuts import ShortcutsLoader
from cosmonium.ui.loaders.skin import SkinLoader
from cosmonium.ui.loaders.widgets import ButtonWidgetLoader, SpacerWidgetLoader, TextWidgetLoader, WidgetLoaderRegistry


@pytest.fixture
def init_registry(scope='module'):
    init_widget_loaders(WidgetLoaderRegistry.get_instance())


class TestShortcutsLoader:
    """Tests for ShortcutsLoader with actual config files."""

    def test_load_default_shortcuts(self):
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
            loader = ShortcutsLoader()
            shortcuts = loader.load(filepath)

            assert isinstance(shortcuts, list)
            assert len(shortcuts) == 2

            assert shortcuts == [('event-1', ['1']), ('event-2', ['2', 'control-2'])]
        finally:
            os.unlink(filepath)


class TestSkinLoader:
    """Tests for SkinLoader with actual config files."""

    def test_load_default_skin(self):
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
            loader = SkinLoader()
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

    def test_load_test_dock(self, init_registry):
        """Test loading test dock configuration."""

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yaml') as f:
            filepath = f.name
            f.write(
                """
dock:
   orientation: horizontal
   location: bottom
   widgets:
      - type: text
        text: "A"
"""
            )
        try:
            loader = DockLoader({})
            dock = loader.load(filepath)

            assert isinstance(dock, tuple)
            assert len(dock) == 3

            layout, orientation, location = dock
            assert orientation == 'horizontal'
            assert location == 'bottom'
            assert len(layout.widgets) == 1
        finally:
            os.unlink(filepath)


class TestHUDLoader:
    """Tests for HUDLoader with actual config files."""

    def test_load_default_hud(self):
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
            global_vars = {}
            loader = HUDLoader(global_vars)
            hud = loader.load(filepath)

            assert isinstance(hud, dict)
            assert len(hud) == 2

            entry = hud['top-left']
            # Check widgets structure
            assert isinstance(entry, list)
            assert len(entry) == 1
            assert entry[0].entries[0].template.expression.source == 'f"""my-text"""'
            entry = hud['top-right']
            # Check widgets structure
            assert isinstance(entry, list)
            assert len(entry) == 1
            assert entry[0].entries[0].template.expression.source == 'f"""my-other-text"""'
        finally:
            os.unlink(filepath)


class TestWidgetLoaders:
    """Tests for widget loaders."""

    def test_button_widget_loader(self):
        """Test ButtonWidgetLoader."""

        parsers = ParsersCollection()
        loader = ButtonWidgetLoader()

        # Test with text button
        data = {'text': 'Click me', 'event': 'test-event', 'size': 32}
        widget = loader.load(data, parsers, {})
        assert widget is not None
        assert widget.event == 'test-event'

    def test_text_widget_loader(self):
        """Test TextWidgetLoader."""

        parsers = ParsersCollection()
        loader = TextWidgetLoader()

        data = {'text': 'Hello World', 'align': 'left'}
        widget = loader.load(data, parsers, {})
        assert widget is not None

    def test_spacer_widget_loader(self):
        """Test SpacerWidgetLoader."""

        parsers = ParsersCollection()
        loader = SpacerWidgetLoader()

        data = {'size': [10, 10]}
        widget = loader.load(data, parsers, {})
        assert widget is not None

    def test_widget_registry(self):
        """Test WidgetLoaderRegistry."""

        registry = WidgetLoaderRegistry()
        init_widget_loaders(registry)

        # Test loading button
        button_data = {'type': 'button', 'text': 'Test', 'event': 'test'}
        button = registry.load(button_data, {})
        assert button is not None

        # Test loading text
        text_data = {'type': 'text', 'text': 'Test'}
        text = registry.load(text_data, {})
        assert text is not None

        # Test loading spacer
        spacer_data = {'type': 'spacer', 'size': [5, 5]}
        spacer = registry.load(spacer_data, {})
        assert spacer is not None

        # Test unknown type
        unknown_data = {'type': 'unknown'}
        unknown = registry.load(unknown_data, {})
        assert unknown is None
