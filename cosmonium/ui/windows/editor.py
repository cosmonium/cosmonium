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
from direct.gui.DirectCheckButton import DirectCheckButton
from direct.gui.DirectFrame import DirectFrame
from direct.gui.DirectGui import DirectEntry, DirectSlider
from direct.gui.DirectLabel import DirectLabel
from directguilayout.gui import Sizer
from directguilayout.gui import Widget as SizerWidget
from directspinbox.DirectSpinBox import DirectSpinBox, WHEELDOWN, WHEELUP
from panda3d.core import TextNode
from tabbedframe.TabbedFrame import TabbedFrame

from ...parameters import UserParameter
from ...utils import isclose
from ... import settings
from ..skin import UIElement
from ..widgets.tabbed_frame import TabbedFrameContainer
from ..widgets.window import Window
from .uiwindow import UIWindow


class ParamEditor(UIWindow):

    def __init__(self, owner=None):
        UIWindow.__init__(self, owner)
        self.width = settings.default_window_width
        self.height = settings.default_window_height

    def make_entries(self):
        pass

    def update_parameter(self, param):
        pass

    def create_text_entry(self, frame, param):
        entry_element = UIElement('entry', parent=self.element)
        entry = DirectEntry(
            parent=frame,
            initialText=str(param.get_param()),
            numLines=1,
            width=10,
            command=self.do_update,
            extraArgs=[None, param],
            text_align=TextNode.A_left,
            suppressKeys=1,
            **self.skin.get_style(entry_element),
        )
        widget = SizerWidget(entry)
        return widget

    def create_bool_entry(self, frame, param):
        check_button_element = UIElement('check-button', parent=self.element)
        btn = DirectCheckButton(
            parent=frame,
            text_align=TextNode.A_left,
            boxPlacement="left",
            # borderWidth=(2, 2),
            indicator_text='A',
            indicator_text_pos=(0, 4),
            indicator_borderWidth=(2, 2),
            # boxBorder=1
            pressEffect=False,
            suppressKeys=1,
            command=self.do_update,
            extraArgs=[None, param],
            **self.skin.get_style(check_button_element),
        )
        btn['indicatorValue'] = param.get_param()
        widget = SizerWidget(btn)
        return widget

    def create_slider_entry(self, frame, param, component=None):
        slider_element = UIElement('slider', parent=self.element)
        if component is not None:
            scaled_value = param.get_param_component(component, scale=True)
        else:
            scaled_value = param.get_param(scale=True)
        slider = DirectSlider(
            parent=frame,
            value=scaled_value,
            range=param.get_range(scale=True),
            suppressKeys=1,
            command=self.do_update_slider,
            **self.skin.get_style(slider_element),
        )
        widget1 = SizerWidget(slider)
        widget2 = self.create_spin_entry(frame, param, slider, component)
        slider['extraArgs'] = [slider, widget2[0].dgui_obj, param, component]
        return widget1, widget2[0]

    def create_spin_entry(self, frame, param, slider=None, component=None):
        spin_box_element = UIElement('spin-box', parent=self.element)
        value_range = param.get_range()
        value_type = param.get_type()
        if value_range is None:
            value_range = (value_type(float("-inf")), value_type(float("inf")))
        step_size = param.get_step()
        if step_size is None:
            step_size = 1
        if component is not None:
            value = param.get_param_component(component)
        else:
            value = param.get_param()
        entry = DirectSpinBox(
            parent=frame,
            value=value,
            valueType=value_type,
            textFormat='{}',
            minValue=value_range[0],
            maxValue=value_range[1],
            stepSize=step_size,
            suppressKeys=1,
            command=self.do_update,
            extraArgs=[slider, param, component],
            valueEntry_width=10,
            valueEntry_text_align=TextNode.A_left,
            **self.skin.get_style(spin_box_element),
        )
        entry.valueEntry.unbind(WHEELUP)
        entry.valueEntry.unbind(WHEELDOWN)
        widget = SizerWidget(entry)
        return widget, (0, 0)

    def add_parameter(self, frame, hsizer, param):
        hsizer_element = UIElement('sizer', class_='editor-entry-sizer', parent=self.element)
        label_element = UIElement('label', parent=self.element, class_='editor-entry-label')
        label = DirectLabel(
            parent=frame,
            text=param.name,
            textMayChange=True,
            text_align=TextNode.A_left,
            **self.skin.get_style(label_element),
        )
        widget = SizerWidget(label)
        hsizer.add(widget, alignments=("min", "center"), **self.skin.get_style(hsizer_element, usage='cell'))
        if param.param_type == UserParameter.TYPE_BOOL:
            widget = self.create_bool_entry(frame, param)
            hsizer.add(widget, alignments=("min", "center"), **self.skin.get_style(hsizer_element, usage='cell'))
            hsizer.add((0, 0))
        elif param.param_type == UserParameter.TYPE_STRING:
            widget = self.create_text_entry(frame, param)
            hsizer.add(widget, alignments=("min", "center"), **self.skin.get_style(hsizer_element, usage='cell'))
            hsizer.add((0, 0))
        elif param.param_type == UserParameter.TYPE_INT:
            if param.value_range is not None:
                widget1, widget2 = self.create_slider_entry(frame, param)
            else:
                widget1, widget2 = self.create_spin_entry(frame, param)
            hsizer.add(widget1, alignments=("min", "center"), **self.skin.get_style(hsizer_element, usage='cell'))
            hsizer.add(widget2, alignments=("min", "center"), **self.skin.get_style(hsizer_element, usage='cell'))
        elif param.param_type == UserParameter.TYPE_FLOAT:
            if param.value_range is not None:
                widget1, widget2 = self.create_slider_entry(frame, param)
            else:
                widget1, widget2 = self.create_spin_entry(frame, param)
            hsizer.add(widget1, alignments=("min", "center"), **self.skin.get_style(hsizer_element, usage='cell'))
            hsizer.add(widget2, alignments=("min", "center"), **self.skin.get_style(hsizer_element, usage='cell'))
        elif param.param_type == UserParameter.TYPE_VEC:
            vector_element = UIElement('sizer', parent=self.element, class_='editor-entry-vector')
            vsizer1 = Sizer("vertical", **self.skin.get_style(vector_element))
            vsizer2 = Sizer("vertical", **self.skin.get_style(vector_element))
            for component in range(param.nb_components):
                widget1, widget2 = self.create_slider_entry(frame, param, component)
                vsizer1.add(
                    widget1,
                    proportions=(0.0, 1.0),
                    alignments=("min", "center"),
                    **self.skin.get_style(vector_element, usage='cell'),
                )
                vsizer2.add(widget2, **self.skin.get_style(vector_element, usage='cell'))
            hsizer.add(vsizer1, proportions=(0.0, 1.0), **self.skin.get_style(hsizer_element, usage='cell'))
            hsizer.add(vsizer2, **self.skin.get_style(hsizer_element, usage='cell'))
        else:
            print("Unknown entry type", param.param_type)

    def add_parameters(self, frame, sizer, parameters, hsizer=None):
        hsizer_element = UIElement('sizer', class_='editor-entry-sizer', parent=self.element)
        label_element = UIElement('label', parent=self.element, class_='editor-section-label')
        for param in parameters:
            if param is None:
                continue
            if param.is_group():
                if param.is_empty():
                    continue
                if param.name is not None:
                    label = DirectLabel(
                        parent=frame,
                        text=param.name,
                        textMayChange=True,
                        text_align=TextNode.A_left,
                        **self.skin.get_style(label_element),
                    )
                    widget = SizerWidget(label)
                    sizer.add(widget, **self.skin.get_style(label_element, dgui='sizer', usage='cell'))
                hsizer = Sizer("horizontal", prim_limit=3, **self.skin.get_style(hsizer_element))
                sizer.add(hsizer, alignments=("min", "expand"), **self.skin.get_style(hsizer_element, usage='cell'))
                self.add_parameters(frame, sizer, param.parameters, hsizer)
            else:
                if not hsizer:
                    hsizer = Sizer("horizontal", prim_limit=3, **self.skin.get_style(hsizer_element))
                    sizer.add(hsizer, proportions=(1.0, 0.0), **self.skin.get_style(hsizer_element, usage='cell'))
                self.add_parameter(frame, hsizer, param)

    def create_layout(self, *args, **kwargs):
        group = self.make_entries(*args, **kwargs)
        tabbed_frame_element = UIElement('tabbed-frame', class_='editor')
        tabbed_frame = TabbedFrame(
            frameSize=(0, self.width * settings.ui_scale, -self.height * settings.ui_scale, 0),
            **self.skin.get_style(tabbed_frame_element),
            tab_frameSize=(0, 7, 0, 2),
            tab_text_align=TextNode.ALeft,
            tab_text_pos=(0.2, 0.6),
        )
        self.layout = TabbedFrameContainer(tabbed_frame)
        for section in group.parameters:
            self.element = UIElement('frame', parent=tabbed_frame_element, class_='editor-canvas')
            sizer = Sizer("vertical")
            frame = DirectFrame(state=DGG.NORMAL, **self.skin.get_style(self.element))
            self.add_parameters(frame, sizer, section.parameters)
            sizer.update((self.width * settings.ui_scale, self.height * settings.ui_scale))
            size = sizer.min_size
            frame['frameSize'] = (0, size[0], -size[1], 0)
            tabbed_frame.addPage(frame, section.name)
        self.button_background = DirectFrame(
            parent=tabbed_frame,
            state=DGG.NORMAL,
            **self.skin.get_style(self.element),
            sortOrder=tabbed_frame['sortOrder'] - 1,
        )
        self.element = None
        self.button_background['frameSize'] = [0, self.width * settings.ui_scale, 0, self.layout.height_offset]
        title = "Editor - " + group.name
        self.window = Window(title, parent=pixel2d, scale=self.scale, child=self.layout, owner=self)
        self.window.register_scroller(self.layout.frame.viewingArea)

    def do_update(self, value, slider, param, component=None):
        value = param.convert_to_type(value)
        if component is None:
            param.set_param(value)
            if slider is not None:
                new_value = param.get_param(scale=True)
                if not isclose(slider['value'], new_value, rel_tol=1e-6):
                    slider['value'] = new_value
        else:
            param.set_param_component(component, value)
            if slider is not None:
                new_value = param.get_param_component(component, scale=True)
                if not isclose(slider['value'], new_value, rel_tol=1e-6):
                    slider['value'] = new_value
        self.update_parameter(param)

    def do_update_slider(self, slider, entry, param, component=None):
        value = slider['value']
        value = param.convert_to_type(value)
        if component is None:
            param.set_param(value, scale=True)
            if entry is not None:
                new_value = param.get_param()
                if not isclose(entry.getValue(), new_value, rel_tol=1e-6):
                    entry.setValue(new_value)
        else:
            param.set_param_component(component, value, scale=True)
            if entry is not None:
                new_value = param.get_param_component(component)
                if not isclose(entry.getValue(), new_value, rel_tol=1e-6):
                    entry.setValue(new_value)
        self.update_parameter(param)
