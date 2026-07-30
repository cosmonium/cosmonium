# -*- coding: utf-8 -*-
#
# This file is part of Cosmonium.
#
# Copyright (C) 2018-2025 Laurent Deru.
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

from typing import Any, Dict, Optional

import mistune
from mistune.core import BaseRenderer, BlockState
from panda3d.core import TextProperties, TextPropertiesManager

from ..fonts import Font, fontsManager


class DirectMarkdownRenderer(BaseRenderer):

    init = False

    def __init__(self, font_family):
        BaseRenderer.__init__(self)
        font_normal = fontsManager.get_font(font_family, Font.STYLE_NORMAL)
        if font_normal is not None:
            font_normal = font_normal.load()
        font_bold = fontsManager.get_font(font_family, Font.STYLE_BOLD)
        if font_bold is not None:
            font_bold = font_bold.load()
        if font_bold is None:
            font_bold = font_normal
        font_italic = fontsManager.get_font(font_family, Font.STYLE_ITALIC)
        if font_italic is not None:
            font_italic = font_italic.load()
        if font_italic is None:
            font_italic = font_normal
        self.init_text_properties(font_normal, font_bold, font_italic)

    @classmethod
    def init_text_properties(cls, font_normal, font_bold, font_italic):
        if cls.init:
            return
        # TODO: names should be linked to instance and deleted when not needed
        tpMgr = TextPropertiesManager.getGlobalPtr()
        tp_normal = TextProperties()
        tp_normal.set_font(font_normal)
        tpMgr.setProperties("md_normal", tp_normal)
        tp_underscore = TextProperties()
        tp_underscore.set_underscore(True)
        tpMgr.setProperties("md_under", tp_underscore)
        tp_bold = TextProperties()
        tp_bold.set_font(font_bold)
        tpMgr.setProperties("md_bold", tp_bold)
        tp_italic = TextProperties()
        tp_italic.set_font(font_italic)
        tpMgr.setProperties("md_italic", tp_italic)
        for i in range(1, 7):
            header = TextProperties()
            header.set_text_scale(1.0 + (7 - i) / 10.0)
            tpMgr.setProperties("md_header%i" % i, header)
        cls.init = True

    def render_token(self, token: Dict[str, Any], state: BlockState) -> str:
        # backward compitable with v2
        func = self._get_method(token["type"])
        attrs = token.get("attrs")

        if "raw" in token:
            text = token["raw"]
        elif "children" in token:
            text = self.render_tokens(token["children"], state)
        else:
            if attrs:
                return func(**attrs)
            else:
                return func()
        if attrs:
            return func(text, **attrs)
        else:
            return func(text)

    # inline level

    def text(self, text: str) -> str:
        return text

    def link(self, text: str, url: str, title: Optional[str] = None) -> str:
        return text

    def image(self, text: str, url: str, title: Optional[str] = None) -> str:
        return text

    def emphasis(self, text: str) -> str:
        return '\1md_italic\1%s\2' % text

    def strong(self, text: str) -> str:
        return '\1md_bold\1%s\2' % text

    def codespan(self, text: str) -> str:
        return '\1md_italic\1%s\2' % text

    def linebreak(self) -> str:
        return '\n'

    def softbreak(self) -> str:
        return ' '

    def inline_html(self, html: str) -> str:
        return html

    # block level

    def paragraph(self, text: str) -> str:
        return '%s\n' % text.strip(' ')

    def heading(self, text: str, level: int, **attrs: Any) -> str:
        return '\1md_header%d\1%s\2\n\n' % (level, text)

    def blank_line(self) -> str:
        return '\n'

    def thematic_break(self) -> str:
        return '-----\n'

    def block_text(self, text: str) -> str:
        return text

    def block_code(self, code: str, info: Optional[str] = None) -> str:
        return '\1md_italic\1%s\2' % code

    def block_quote(self, text: str) -> str:
        return '\1md_italic\1%s\2' % text

    def block_html(self, html: str) -> str:
        return html

    def block_error(self, html: str) -> str:
        return '\1md_bold\1%s\2' % html

    def list(self, text: str, ordered: bool, **attrs: Any) -> str:
        return "%s\n" % text

    def list_item(self, text: str) -> str:
        return u"\u2022 %s\n" % text

    # provided by strikethrough plugin

    def strikethrough(self, text: str) -> str:
        return '%s' % text

    # provided by mark plugin

    def mark(self, text: str) -> str:
        return text

    # provide by table plugin

    def table(self, text: str) -> str:
        return '%s\n' % (text)

    def table_head(self, text: str) -> str:
        return '%s\n' % (text)

    def table_body(self, text: str) -> str:
        return '%s\n' % (text)

    def table_row(self, text: str) -> str:
        return '%s\n' % text

    def table_cell(self, text, align=None, head=False):
        return '%s' % (text)

    # provided by footnotes plugin

    def footnote_ref(self, key: str, index: int) -> str:
        return "%s" % key

    def footnote_item(self, text: str, key: str, index: int) -> str:
        return text

    def footnotes(self, text: str) -> str:
        return text


def create_markdown_renderer(fonts):
    renderer = DirectMarkdownRenderer(fonts)
    markdown = mistune.create_markdown(renderer=renderer)
    return markdown
