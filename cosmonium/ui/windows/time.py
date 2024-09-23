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
from direct.gui.DirectButton import DirectButton
from direct.gui.DirectFrame import DirectFrame
from direct.gui.DirectLabel import DirectLabel
from directguilayout.gui import Sizer
from directguilayout.gui import Widget as SizerWidget
from directspinbox.DirectSpinBox import DirectSpinBox
from panda3d.core import TextNode

from ... import settings
from ..skin import UIElement
from ..widgets.direct_widget_container import DirectWidgetContainer
from ..widgets.window import Window
from .uiwindow import UIWindow


class TimeEditor(UIWindow):

    def __init__(self, time, owner=None):
        UIWindow.__init__(self, owner)
        self.time = time
        self.element = UIElement('window', id_='time-window')
        self.font_size = self.skin.get(self.element).font_size(None, False, None)
        self.borders = (self.font_size / 4.0, self.font_size / 4.0, self.font_size / 4.0, self.font_size / 4.0)
        self.width = settings.default_window_width
        self.height = settings.default_window_height
        self.day_entry = None
        self.month_entry = None
        self.year_entry = None
        self.hour_entry = None
        self.min_entry = None
        self.sec_entry = None

    def create_label(self, frame, text):
        label_element = UIElement('label', parent=self.element, class_='time-label')
        label = DirectLabel(
            parent=frame,
            text=text,
            textMayChange=True,
            text_align=TextNode.A_left,
            **self.skin.get_style(label_element)
        )
        return label

    def create_spin_entry(self, frame, value, value_range, width):
        spin_element = UIElement('spin-box', parent=self.element, class_='time-spin-box')
        entry = DirectSpinBox(
            parent=frame,
            value=value,
            valueType=int,
            textFormat='{}',
            minValue=value_range[0],
            maxValue=value_range[1],
            stepSize=1,
            suppressKeys=1,
            valueEntry_width=width,
            valueEntry_text_align=TextNode.A_left,
            **self.skin.get_style(spin_element)
        )
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
        self.element = UIElement('frame', class_='time-editor')
        frame = DirectFrame(state=DGG.NORMAL, **self.skin.get_style(self.element))
        self.layout = DirectWidgetContainer(frame)
        self.layout.frame.setPos(0, 0, 0)
        sizer = Sizer("vertical")
        self.add_time(frame, sizer)
        self.add_date(frame, sizer)
        self.set_current_time()
        hsizer = Sizer("horizontal")
        ok_button_element = UIElement('button', class_='ok-button')
        ok = DirectButton(parent=frame, text=_("OK"), command=self.ok, **self.skin.get_style(ok_button_element))
        hsizer.add(SizerWidget(ok), alignments=("min", "center"), borders=self.borders)
        current_time_button_element = UIElement('button', class_='current-time-button')
        current = DirectButton(
            parent=frame,
            text=_("Set current time"),
            command=self.set_current_time,
            **self.skin.get_style(current_time_button_element)
        )
        hsizer.add(SizerWidget(current), alignments=("min", "center"), borders=self.borders)
        cancel_button_element = UIElement('button', class_='cancel-button')
        cancel = DirectButton(
            parent=frame, text=_("Cancel"), command=self.cancel, **self.skin.get_style(cancel_button_element)
        )
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
