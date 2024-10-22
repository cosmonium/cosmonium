#
# This file is part of Cosmonium.
#
# Copyright (C) 2018-2024 Laurent Deru.
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

from direct.gui import DirectGuiGlobals as DGG
from direct.gui.DirectLabel import DirectLabel
from direct.gui.DirectScrolledFrame import DirectScrolledFrame
from directguilayout.gui import Sizer
from directguilayout.gui import Widget as SizerWidget
from panda3d.core import TextNode

from ... import settings
from ..object_info import ObjectInfo
from ..skin import UIElement
from ..widgets.direct_widget_container import DirectWidgetContainer
from ..widgets.window import Window
from .uiwindow import UIWindow


class InfoWindow(UIWindow):

    def __init__(self, owner=None):
        UIWindow.__init__(self, owner)
        self.element = UIElement('window', id_='info-window')
        self.font_size = self.skin.get(self.element).font_size(None, False, None)
        self.width = settings.default_window_width / 2
        self.height = settings.default_window_height

    def create_layout(self, body):
        self.element = UIElement('scrolled-frame', class_='info')
        vsizer_element = UIElement('sizer', class_='vertical-sizer', parent=self.element)
        sizer = Sizer("vertical", **self.skin.get_style(vsizer_element))
        hsizer_element = UIElement('sizer', class_='entry-sizer', parent=self.element)
        hsizer = Sizer("horizontal", prim_limit=2, **self.skin.get_style(hsizer_element))
        sizer.add(hsizer, alignments=("min", "expand"), **self.skin.get_style(hsizer_element, usage='cell'))
        self.layout = DirectWidgetContainer(
            DirectScrolledFrame(
                state=DGG.NORMAL,
                horizontalScroll_relief=DGG.FLAT,
                verticalScroll_relief=DGG.FLAT,
                **self.skin.get_style(self.element)
            )
        )
        self.layout.frame.setPos(0, 0, 0)
        self.make_entries(self.layout.frame.getCanvas(), hsizer, body)
        sizer.update((self.width, self.height))
        self.layout.frame['frameSize'] = (0, self.width * settings.ui_scale, -self.height * settings.ui_scale, 0)
        size = sizer.min_size
        self.layout.frame['canvasSize'] = (0, size[0], -size[1], 0)
        title = "Body information"
        self.window = Window(title, parent=self.owner.root, scale=self.scale, child=self.layout, owner=self)
        self.window.register_scroller(self.layout.frame)

    def make_title_entry(self, frame, title):
        label_element = UIElement('label', parent=self.element, class_='info-section-label')
        title_label = DirectLabel(
            parent=frame, text=title, text_align=TextNode.ALeft, **self.skin.get_style(label_element)
        )
        return title_label

    def make_text_entry(self, frame, text):
        label_element = UIElement('label', parent=self.element, class_='info-entry-label')
        label = DirectLabel(parent=frame, text=text, text_align=TextNode.ALeft, **self.skin.get_style(label_element))
        return label

    def make_entries(self, frame, hsizer, body):
        borders = (0, 0, 0, 0)
        info = ObjectInfo.get_info_for(body)
        for entry in info:
            if entry is None:
                continue
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
