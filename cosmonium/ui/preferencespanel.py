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

from panda3d.core import TextNode, NodePath, LVector3, LVector2
from direct.gui.DirectFrame import DirectFrame
from direct.gui import DirectGuiGlobals
from direct.gui.DirectLabel import DirectLabel
from direct.gui.DirectCheckButton import DirectCheckButton

from tabbedframe.TabbedFrame import TabbedFrame
from directguilayout.gui import Sizer
from directguilayout.gui import Widget as SizerWidget
from .widgets import DirectWidgetContainer
from .window import Window

import sys
if sys.version_info[0] >= 3:
    from collections.abc import Iterable
else:
    from collections import Iterable

class PreferencesPanel():
    def __init__(self, font_family, font_size = 14, owner=None):
        self.window = None
        self.layout = None
        self.last_pos = None
        self.font_size = font_size
        self.owner = owner
        self.scale = LVector2(1, 1)

    def create_layout(self):
        scale3 = LVector3(self.scale[0], 1.0, self.scale[1])
        buttonSize = self.font_size * 2
        self.layout = DirectWidgetContainer(TabbedFrame(frameSize=(0, 800, -600, 0),
                                                        tab_frameSize = (0, 7, 0, 2),
                                                        tab_scale=scale3 * self.font_size,
                                                        tab_text_align = TextNode.ALeft,
                                                        tab_text_pos = (0.2, 0.6),
                                                        tabSelectedColor = (0.7, 0.7, 0.7, 1)))
        self.layout.frame.setPos(0, 0, -buttonSize)
        borders = (self.font_size, 0, self.font_size / 2.0, self.font_size / 2.0)
        borders_tab = (self.font_size * 2, 0, self.font_size / 2.0, self.font_size / 2.0)
        for (tab_name, entries) in self.preferences:
            sizer = Sizer("vertical")
            frame = DirectFrame(state=DirectGuiGlobals.NORMAL, frameColor=(1, 0, 0, 1))
            has_titles = False
            for entry in entries:
                if isinstance(entry, str):
                    label = DirectLabel(parent=frame,
                                        text=entry,
                                        textMayChange=True,
                                        text_scale=self.font_size,
                                        text_align=TextNode.A_left)
                    widget = SizerWidget(label)
                    sizer.add(widget, expand=True, borders=borders)
                    has_titles = True
                elif isinstance(entry, Iterable):
                    text, value, func = entry[:3]
                    args = entry[3:]
                    btn = DirectCheckButton(parent=frame,
                                            text=text,
                                            text_scale=self.font_size,
                                            text_align=TextNode.A_left,
                                            boxPlacement="left",
                                            #borderWidth=(2, 2),
                                            indicator_text_scale=self.font_size,
                                            indicator_text='A',
                                            indicator_text_pos=(0, 4),
                                            indicator_borderWidth=(2, 2),
                                            #boxBorder=1
                                            pressEffect=False,
                                            command=self.toggle_option,
                                            extraArgs=[func, args]
                                            )
                    btn['indicatorValue'] = value
                    widget = SizerWidget(btn)
                    sizer.add(widget, expand=True, borders=borders_tab if has_titles else borders)
                elif entry == 0:
                    sizer.add((0, self.font_size))
                else:
                    print("Unknown entry type", entry)
            sizer.update((800, 600))
            self.layout.frame.addPage(frame, tab_name)
        title = "Preferences"
        self.window = Window(title, parent=pixel2d, scale=self.scale, child=self.layout, owner=self)

    def toggle_option(self, btn, func, args):
        if func is not None: func(*args)

    def show(self):
        if self.shown():
            print("Preferences already shown")
            return
        self.create_layout()
        if self.last_pos is None:
            self.last_pos = (0, 0, -100)
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
