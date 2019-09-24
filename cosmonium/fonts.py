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

from panda3d.core import Filename

import os

class Font(object):
    STYLE_UNKNOWN = 0x01
    STYLE_NORMAL =  0x02
    STYLE_BOLD =    0x04
    STYLE_ITALIC =  0x08

    def __init__(self, family, style, filename):
        self.family = family
        self.style = style
        self.filename = filename
        self.font = None

    def load(self):
        if self.font is None:
            self.font = loader.loadFont(Filename.from_os_specific(self.filename).get_fullpath())
        return self.font

class FontsManager(object):
    def __init__(self):
        self.families = {}

    def register_font(self, filename):
        basename = os.path.basename(filename)
        base, extension = os.path.splitext(basename)
        if '-' in base:
            (family, stylename) = base.split('-')
            style = 0
            if stylename.find("Regular") >= 0:
                stylename = stylename.replace("Regular", "")
                style |= Font.STYLE_NORMAL
            if stylename.find("Book") >= 0:
                stylename = stylename.replace("Book", "")
                style |= Font.STYLE_NORMAL
            if stylename.find("Bold") >= 0:
                stylename = stylename.replace("Bold", "")
                style |= Font.STYLE_BOLD
            if stylename.find("Italic") >= 0:
                stylename = stylename.replace("Italic", "")
                style |= Font.STYLE_ITALIC
            if stylename.find("Oblique") >= 0:
                stylename = stylename.replace("Oblique", "")
                style |= Font.STYLE_ITALIC
            if stylename != "":
                style |= Font.STYLE_UNKNOWN
        else:
            family = base
            style = Font.STYLE_NORMAL
        entry = self.families.setdefault(family, [])
        #print("Adding font '%s' style %x" % (family, style))
        entry.append(Font(family, style, filename))

    def register_fonts(self, path):
        for entry in os.listdir(path):
            if entry.endswith('.ttf'):
                self.register_font(os.path.join(path, entry))

    def get_font(self, family, style):
        entry = self.families.get(family, None)
        if entry:
            for font in entry:
                if (font.style & style) == style:
                    return font
            print("Requested style not found for '%s" % family)
        else:
            print("Font family '%s' unknown" % family)
        return None

fontsManager = FontsManager()
