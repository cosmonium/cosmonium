#
#This file is part of Cosmonium.
#
#Copyright (C) 2018-2022 Laurent Deru.
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


from panda3d.core import TextNode, LVector3, LVector2
from direct.gui.DirectFrame import DirectFrame
from direct.gui import DirectGuiGlobals as DGG
from direct.gui.DirectLabel import DirectLabel
from direct.gui.DirectButton import DirectButton
from directspinbox.DirectSpinBox import DirectSpinBox

from tabbedframe.TabbedFrame import TabbedFrame
from directguilayout.gui import Sizer
from directguilayout.gui import Widget as SizerWidget

from ... import settings

from ..widgets.direct_widget_container import DirectWidgetContainer
from ..widgets.window import Window


class TimeEditor():
    def __init__(self, time, font_family, font_size = 14, owner=None):
        self.time = time
        self.window = None
        self.layout = None
        self.last_pos = None
        self.font_size = font_size
        self.owner = owner
        self.scale = LVector2(settings.ui_scale, settings.ui_scale)
        self.text_scale = (self.font_size * settings.ui_scale, self.font_size * settings.ui_scale)
        self.borders = (self.font_size, 0, self.font_size / 4.0, self.font_size / 4.0)
        self.width = settings.default_window_width
        self.height = settings.default_window_height
        self.day_entry = None
        self.month_entry = None
        self.year_entry = None
        self.hour_entry = None
        self.min_entry = None
        self.sec_entry = None

    def create_label(self, frame, text):
        label = DirectLabel(parent=frame,
                            text=text,
                            textMayChange=True,
                            text_scale=self.text_scale,
                            text_align=TextNode.A_left)
        return label

    def create_spin_entry(self, frame, value, value_range, width):
        scale3 = LVector3(self.text_scale[0], 1.0, self.text_scale[1])
        entry = DirectSpinBox(parent=frame,
                              value=value,
                              valueType=int,
                              textFormat='{}',
                              minValue=value_range[0],
                              maxValue=value_range[1],
                              stepSize=1,
                              suppressKeys=1,
                              valueEntry_width = width,
                              valueEntry_text_align=TextNode.A_left,
                              valueEntry_frameColor=settings.entry_background,
                              scale=scale3)
        return entry

    def add_entry(self, frame, hsizer, text, value, value_range, width):
        vsizer = Sizer("vertical")
        label = self.create_label(frame, text)
        vsizer.add(SizerWidget(label), borders=self.borders, alignments=("min", "center"))
        entry = self.create_spin_entry(frame, value, value_range, width)
        vsizer.add(SizerWidget(entry), alignments=("min", "expand"), borders=self.borders)
        hsizer.add(vsizer, alignments=("min", "center"), borders=self.borders)
        return entry

    def add_time(self, frame, sizer):
        hsizer = Sizer("horizontal")
        self.hour_entry = self.add_entry(frame, hsizer, _("Hour"), 0, (0, 23), 2)
        self.min_entry = self.add_entry(frame, hsizer, _("Min"), 0, (0, 59), 2)
        self.sec_entry = self.add_entry(frame, hsizer, _("Sec"), 0, (0, 59), 2)
        sizer.add(hsizer, alignments=("min", "expand"), borders=self.borders)

    def add_date(self, frame, sizer):
        hsizer = Sizer("horizontal")
        self.day_entry = self.add_entry(frame, hsizer, _("Day"), 1, (1, 31), 2)
        self.month_entry = self.add_entry(frame, hsizer, _("Month"), 1, (1, 12), 2)
        self.year_entry = self.add_entry(frame, hsizer, _("Year"), 0, (-1000000, 1000000), 4)
        sizer.add(hsizer, alignments=("min", "expand"), borders=self.borders)

    def set_current_time(self):
        (years, months, days, hours, mins, secs) = self.time.time_to_values()
        self.year_entry.setValue(years)
        self.month_entry.setValue(months)
        self.day_entry.setValue(days)
        self.hour_entry.setValue(hours)
        self.min_entry.setValue(mins)
        self.sec_entry.setValue(secs)

    def create_layout(self):
        frame = DirectFrame(state=DGG.NORMAL, frameColor=settings.panel_background)
        self.layout = DirectWidgetContainer(frame)
        self.layout.frame.setPos(0, 0, 0)
        sizer = Sizer("vertical")
        self.add_time(frame, sizer)
        self.add_date(frame, sizer)
        self.set_current_time()
        hsizer = Sizer("horizontal")
        ok = DirectButton(parent=frame,
                          text=_("OK"),
                          text_scale=self.text_scale,
                          command = self.ok)
        hsizer.add(SizerWidget(ok), alignments=("min", "center"), borders=self.borders)
        current = DirectButton(parent=frame,
                               text=_("Set current time"),
                               text_scale=self.text_scale,
                               command = self.set_current_time)
        hsizer.add(SizerWidget(current), alignments=("min", "center"), borders=self.borders)
        cancel = DirectButton(parent=frame,
                              text=_("Cancel"),
                              text_scale=self.text_scale,
                              command = self.cancel)
        hsizer.add(SizerWidget(cancel), alignments=("min", "center"), borders=self.borders)
        sizer.add(hsizer, borders=self.borders)
        sizer.update((self.width, self.height))
        size = sizer.min_size
        frame['frameSize'] = (0, size[0], -size[1], 0)
        self.window = Window(_("Set time"), parent=pixel2d, scale=self.scale, child=self.layout, owner=self)

    def ok(self):
        years = self.year_entry.getValue()
        months = self.month_entry.getValue()
        days = self.day_entry.getValue()
        hours = self.hour_entry.getValue()
        mins = self.min_entry.getValue()
        secs = self.sec_entry.getValue()

        self.time.set_time(years, months, days, hours, mins, secs)
        self.hide()

    def cancel(self):
        self.hide()

    def show(self):
        if self.shown():
            print("Time Editor already shown")
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
