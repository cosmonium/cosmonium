#
#This file is part of Cosmonium.
#
#Copyright (C) 2018-2024 Laurent Deru.
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


from panda3d.core import TextNode, LVector2
from direct.gui import DirectGuiGlobals as DGG
from direct.gui.DirectScrolledFrame import DirectScrolledFrame
from direct.gui.DirectLabel import DirectLabel
from directguilayout.gui import Sizer
from directguilayout.gui import Widget as SizerWidget

from ... import settings
from ...fonts import fontsManager, Font

from ..object_info import ObjectInfo
from ..widgets.window import Window
from ..widgets.direct_widget_container import DirectWidgetContainer


class InfoWindow():
    def __init__(self, scale, font_family, font_size = 14, owner=None):
        self.window = None
        self.layout = None
        self.last_pos = None
        self.font_size = font_size
        self.scale = LVector2(settings.ui_scale, settings.ui_scale)
        self.text_scale = (self.font_size * settings.ui_scale, self.font_size * settings.ui_scale)
        self.title_scale = (self.font_size * settings.ui_scale * 1.2, self.font_size * settings.ui_scale * 1.2)
        self.borders = (self.font_size / 4.0, 0, self.font_size / 4.0, self.font_size / 4.0)
        self.owner = owner
        self.font_normal = fontsManager.get_font(font_family, Font.STYLE_NORMAL)
        if self.font_normal is not None:
            self.font_normal = self.font_normal.load()
        self.font_bold = fontsManager.get_font(font_family, Font.STYLE_BOLD)
        if self.font_bold is not None:
            self.font_bold = self.font_bold.load()
        if self.font_bold is None:
            self.font_bold = self.font_normal
        self.width = settings.default_window_width / 2
        self.height = settings.default_window_height

    def create_layout(self, body):
        sizer = Sizer("vertical")
        hsizer = Sizer("horizontal", prim_limit=2, gaps=(round(self.font_size * .5), round(self.font_size * .5)))
        sizer.add(hsizer, alignments=("min", "expand"), borders=self.borders)
        self.layout = DirectWidgetContainer(DirectScrolledFrame(state=DGG.NORMAL,
                                                                frameColor=(0.33, 0.33, 0.33, .66),
                                                                scrollBarWidth=self.font_size,
                                                                horizontalScroll_relief=DGG.FLAT,
                                                                verticalScroll_relief=DGG.FLAT))
        self.layout.frame.setPos(0, 0, 0)
        self.make_entries(self.layout.frame.getCanvas(), hsizer, body)
        sizer.update((self.width, self.height))
        self.layout.frame['frameSize'] = (0, self.width * settings.ui_scale, -self.height * settings.ui_scale, 0)
        size = sizer.min_size
        self.layout.frame['canvasSize'] = (0, size[0], -size[1], 0)
        title = "Body information"
        self.window = Window(title, parent=pixel2d, scale=self.scale, child=self.layout, owner=self)
        self.window.register_scroller(self.layout.frame)

    def make_title_entry(self, frame, title):
        title_label = DirectLabel(parent=frame,
                                  text=title,
                                  text_align=TextNode.ALeft,
                                  text_scale=self.title_scale,
                                  text_font=self.font_bold,
                                  frameColor=(0, 0, 0, 0))
        return title_label

    def make_text_entry(self, frame, text):
        label = DirectLabel(parent=frame,
                            text=text,
                            text_align=TextNode.ALeft,
                            text_scale=self.text_scale,
                            text_font=self.font_normal,
                            frameColor=(0, 0, 0, 0))
        return label

    def make_entries(self, frame, hsizer, body):
        borders = (0, 0, 0, 0)
        info = ObjectInfo.get_info_for(body)
        for entry in info:
            if entry is None: continue
            if len(entry) != 2:
                print("Invalid entry", entry)
                continue
            (title, value) = entry
            if title is None:
                pass
            elif value is None:
                title_label = self.make_title_entry(frame, title)
                title_widget = SizerWidget(title_label)
                hsizer.add(title_widget, borders=borders, alignments=("min", "left"))
                hsizer.add((0, 0))
            else:
                if isinstance(value, str):
                    title_label = self.make_text_entry(frame, title)
                    title_widget = SizerWidget(title_label)
                    value_label = self.make_text_entry(frame, value)
                    value_widget = SizerWidget(value_label, borders)
                    hsizer.add(title_widget, borders=borders, alignments=("min", "left"))
                    hsizer.add(value_widget, borders=borders, alignments=("min", "left"))
                else:
                    title_label = self.make_title_entry(frame, title)
                    title_widget = SizerWidget(title_label)
                    hsizer.add(title_widget, borders=borders, alignments=("min", "left"))
                    hsizer.add((0, 0))
                    for entry in value:
                        if len(entry) != 2:
                            print("Invalid entry for", title, entry)
                            continue
                        (title, value) = entry
                        title_label = self.make_text_entry(frame, title)
                        title_widget = SizerWidget(title_label)
                        value_label = self.make_text_entry(frame, value)
                        value_widget = SizerWidget(value_label)
                        hsizer.add(title_widget, borders=borders, alignments=("min", "left"))
                        hsizer.add(value_widget, borders=borders, alignments=("min", "left"))

    def show(self, body):
        if self.shown():
            print("Info panel already shown")
            return
        self.create_layout(body)
        if self.last_pos is None:
            self.last_pos = (100, 0, -100)
        self.window.setPos(self.last_pos)
        self.window.update()

    def hide(self):
        if self.window is not None:
            self.last_pos = self.window.getPos()
            self.window.destroy()
            self.window = None
            self.layout = None

    def shown(self):
        return self.window is not None

    def window_closed(self, window):
        if window is self.window:
            self.last_pos = self.window.getPos()
            self.window = None
            self.layout = None
            if self.owner is not None:
                self.owner.window_closed(self)
