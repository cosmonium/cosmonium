# -*- coding: utf-8 -*-
#
#This file is part of Cosmonium.
#
#Copyright (C) 2018-2019 Laurent Deru.
#
#Cosmonium is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
#
#Cosmonium is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with Cosmonium.  If not, see <https://www.gnu.org/licenses/>.
#

from __future__ import print_function
from __future__ import absolute_import

from panda3d.core import TextProperties, TextPropertiesManager

from mistune import mistune
from ..fonts import fontsManager, Font

class MarkdownRenderer(mistune.Renderer):
    init = False
    def __init__(self, font_family):
        mistune.Renderer.__init__(self)
        self.font_normal = fontsManager.get_font(font_family, Font.STYLE_NORMAL)
        if self.font_normal is not None:
            self.font_normal = self.font_normal.load()
        self.font_bold = fontsManager.get_font(font_family, Font.STYLE_BOLD)
        if self.font_bold is not None:
            self.font_bold = self.font_bold.load()
        if self.font_bold is None:
            self.font_bold = self.font_normal
        self.font_italic = fontsManager.get_font(font_family, Font.STYLE_ITALIC)
        if self.font_italic is not None:
            self.font_italic = self.font_italic.load()
        if self.font_italic is None:
            self.font_italic = self.font_normal
        if not MarkdownRenderer.init:
            #TODO: names should be linked to instance and deleted when not needed
            tpMgr = TextPropertiesManager.getGlobalPtr()
            tp_normal = TextProperties()
            tp_normal.set_font(self.font_normal)
            tpMgr.setProperties("md_normal", tp_normal)
            tp_underscore = TextProperties()
            tp_underscore.set_underscore(True)
            tpMgr.setProperties("md_under", tp_underscore)
            tp_bold = TextProperties()
            tp_bold.set_font(self.font_bold)
            tpMgr.setProperties("md_bold", tp_bold)
            tp_italic = TextProperties()
            tp_italic.set_font(self.font_italic)
            tpMgr.setProperties("md_italic", tp_italic)
            for i in range(1, 7):
                header = TextProperties()
                header.set_text_scale(1.0 + (7 - i) / 10.0)
                tpMgr.setProperties("md_header%i" % i, header)
            MarkdownRenderer.init = True

    def placeholder(self):
        return ''

    def block_code(self, code, lang=None):
        return code

    def block_quote(self, text):
        return text

    def block_html(self, html):
        return html

    def header(self, text, level, raw=None):
        return '\1md_header%d\1%s\2\n\n' % (level, text)

    def hrule(self):
        return '-----\n'

    def list(self, body, ordered=True):
        return "%s\n" % body

    def list_item(self, text):
        return u"\u2022 %s\n" % text

    def paragraph(self, text):
        return '%s\n' % text.strip(' ')

    def table(self, header, body):
        return '%s\n%s\n' % (header, body)

    def table_row(self, content):
        return '%s\n' % content

    def table_cell(self, content, **flags):
        return '%s' % (content)

    def double_emphasis(self, text):
        return '\1md_bold\1%s\2' % text

    def emphasis(self, text):
        return '\1md_italic\1%s\2' % text

    def codespan(self, text):
        return '%s' % text

    def linebreak(self):
        return '\n'

    def strikethrough(self, text):
        return '%s' % text

    def text(self, text):
        return text

    def escape(self, text):
        return text

    def autolink(self, link, is_email=False):
        return '%s' % (link)

    def link(self, link, title, text):
        return '%s' % (text)

    def image(self, src, title, text):
        return '%s' % text

    def inline_html(self, html):
        return html

    def newline(self):
        """Rendering newline element."""
        return '\n'

    def footnote_ref(self, key, index):
        return "%s" % key

    def footnote_item(self, key, text):
        return text

    def footnotes(self, text):
        return text

def create_markdown_renderer(fonts):
    renderer = MarkdownRenderer(fonts)
    markdown = mistune.Markdown(renderer=renderer)
    return markdown
