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
Integration tests for DirectMarkdownRenderer.

This module contains integration tests that verify DirectMarkdownRenderer
properly implements all required methods from Mistune's BaseRenderer and
correctly renders markdown text.
"""

from unittest.mock import Mock, patch

import pytest

from cosmonium.ui.markdown import DirectMarkdownRenderer, create_markdown_renderer


@pytest.fixture
def mock_text_properties():
    """Mock init_text_properties to avoid Panda3D text property registration."""
    with patch.object(DirectMarkdownRenderer, 'init_text_properties'):
        yield


@pytest.fixture
def mock_fonts(mock_text_properties):
    """Mock font loading to avoid Panda3D dependencies."""
    with patch('cosmonium.ui.markdown.fontsManager') as mock_font_manager:
        mock_font = Mock()
        mock_font.load.return_value = mock_font
        mock_font_manager.get_font.return_value = mock_font
        yield mock_font_manager


class TestMarkdownIntegration:
    """Test integration with Mistune markdown parser."""

    @pytest.fixture
    def markdown(self, mock_fonts):
        """Create a markdown instance with DirectMarkdownRenderer."""
        return create_markdown_renderer("test-font")

    def test_create_markdown_renderer_returns_markdown_instance(self, mock_fonts):
        """Test that create_markdown_renderer returns a Mistune instance."""
        markdown = create_markdown_renderer("test-font")
        assert markdown is not None
        assert hasattr(markdown, 'parse')

    def test_render_plain_text(self, markdown):
        """Test rendering plain text."""
        result = markdown("Hello World")
        assert result == "Hello World\n"

    def test_render_emphasis(self, markdown):
        """Test rendering emphasized (italic) text."""
        result = markdown("This is *italic* text")
        assert result == "This is \1md_italic\1italic\2 text\n"

    def test_render_strong(self, markdown):
        """Test rendering strong (bold) text."""
        result = markdown("This is **bold** text")
        assert result == "This is \1md_bold\1bold\2 text\n"

    def test_render_heading_level_1(self, markdown):
        """Test rendering heading level 1."""
        result = markdown("# Heading 1")
        assert result == "\1md_header1\1Heading 1\2\n\n"

    def test_render_heading_level_2(self, markdown):
        """Test rendering heading level 2."""
        result = markdown("## Heading 2")
        assert result == "\1md_header2\1Heading 2\2\n\n"

    def test_render_heading_level_3(self, markdown):
        """Test rendering heading level 3."""
        result = markdown("### Heading 3")
        assert result == "\1md_header3\1Heading 3\2\n\n"

    def test_render_paragraph(self, markdown):
        """Test rendering paragraphs."""
        result = markdown("This is a paragraph.\n\nThis is another paragraph.")
        assert result == "This is a paragraph.\n\nThis is another paragraph.\n"

    def test_render_code_inline(self, markdown):
        """Test rendering inline code."""
        result = markdown("Use `code` for inline code")
        assert result == "Use \1md_italic\1code\2 for inline code\n"

    def test_render_code_block(self, markdown):
        """Test rendering code blocks."""
        code_block = "```python\ndef hello():\n    return \"world\"\n```"
        result = markdown(code_block)
        assert result == '\1md_italic\1def hello():\n    return "world"\n\2'

    def test_render_unordered_list(self, markdown):
        """Test rendering unordered lists."""
        list_text = "- Item 1\n- Item 2\n- Item 3"
        result = markdown(list_text)
        assert result == "\u2022 Item 1\n\u2022 Item 2\n\u2022 Item 3\n\n"

    def test_render_ordered_list(self, markdown):
        """Test rendering ordered lists."""
        list_text = "1. First\n2. Second\n3. Third"
        result = markdown(list_text)
        assert result == "\u2022 First\n\u2022 Second\n\u2022 Third\n\n"

    def test_render_blockquote(self, markdown):
        """Test rendering blockquotes."""
        result = markdown("> This is a quote")
        assert result == "\1md_italic\1This is a quote\n\2"

    def test_render_link(self, markdown):
        """Test rendering links."""
        result = markdown("[Click here](https://example.com)")
        assert result == "Click here\n"

    def test_render_thematic_break(self, markdown):
        """Test rendering thematic breaks (horizontal rules)."""
        result = markdown("---")
        assert result == "-----\n"

    def test_render_combined_formatting(self, markdown):
        """Test rendering text with combined formatting."""
        text = "This has **bold**, *italic*, and `code` formatting."
        result = markdown(text)
        assert result == "This has \1md_bold\1bold\2, \1md_italic\1italic\2, and \1md_italic\1code\2 formatting.\n"

    def test_render_nested_emphasis(self, markdown):
        """Test rendering nested emphasis."""
        text = "This is ***bold and italic*** text"
        result = markdown(text)
        assert result == "This is \1md_italic\1\1md_bold\1bold and italic\2\2 text\n"

    def test_render_multiple_paragraphs(self, markdown):
        """Test rendering multiple paragraphs."""
        text = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."
        result = markdown(text)
        assert result == "First paragraph.\n\nSecond paragraph.\n\nThird paragraph.\n"

    def test_render_heading_with_emphasis(self, markdown):
        """Test rendering heading with emphasis."""
        text = "# Heading with *italic* and **bold**"
        result = markdown(text)
        assert result == "\1md_header1\1Heading with \1md_italic\1italic\2 and \1md_bold\1bold\2\2\n\n"

    def test_render_list_with_emphasis(self, markdown):
        """Test rendering list with emphasis."""
        text = "- Item with **bold**\n- Item with *italic*"
        result = markdown(text)
        assert result == "\u2022 Item with \1md_bold\1bold\2\n\u2022 Item with \1md_italic\1italic\2\n\n"

    def test_render_empty_string(self, markdown):
        """Test rendering empty string."""
        result = markdown("")
        assert result == "\n"

    def test_render_only_whitespace(self, markdown):
        """Test rendering only whitespace."""
        result = markdown("   ")
        assert result == "\n"
