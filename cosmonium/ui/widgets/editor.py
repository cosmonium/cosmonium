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


from panda3d.core import TextNode, NodePath, LVector3, LVector2
from direct.gui.DirectFrame import DirectFrame
from direct.gui import DirectGuiGlobals as DGG
from direct.gui.DirectLabel import DirectLabel
from direct.gui.DirectCheckButton import DirectCheckButton
from direct.gui.DirectGui import DirectEntry, DirectSlider
from directspinbox.DirectSpinBox import DirectSpinBox

from tabbedframe.TabbedFrame import TabbedFrame
from directguilayout.gui import Sizer
from directguilayout.gui import Widget as SizerWidget

from ...parameters import UserParameter
from ...utils import isclose
from ... import settings

from .tabbed_frame import TabbedFrameContainer
from .window import Window


class ParamEditor():
    def __init__(self, font_family, font_size = 14, owner=None):
        self.window = None
        self.layout = None
        self.last_pos = None
        self.font_size = font_size
        self.owner = owner
        self.scale = LVector2(settings.ui_scale, settings.ui_scale)
        self.text_scale = (self.font_size * settings.ui_scale, self.font_size * settings.ui_scale)
        border = round(self.font_size / 4.0)
        self.borders = (round(self.font_size), 0, border, border)
        self.width = settings.default_window_width
        self.height = settings.default_window_height

    def create_text_entry(self, frame, param):
        entry = DirectEntry(parent=frame,
                            initialText=str(param.get_param()),
                            numLines = 1,
                            width = 10,
                            command=self.do_update,
                            extraArgs=[None, param],
                            text_scale=self.font_size,
                            text_align=TextNode.A_left,
                            suppressKeys=1)
        widget = SizerWidget(entry)
        return widget

    def create_bool_entry(self, frame, param):
        btn = DirectCheckButton(parent=frame,
                                text="",
                                text_scale=self.text_scale,
                                text_align=TextNode.A_left,
                                boxPlacement="left",
                                #borderWidth=(2, 2),
                                indicator_text_scale=self.text_scale,
                                indicator_text='A',
                                indicator_text_pos=(0, 4),
                                indicator_borderWidth=(2, 2),
                                #boxBorder=1
                                pressEffect=False,
                                suppressKeys=1,
                                command=self.do_update,
                                extraArgs=[None, param],
                                )
        btn['indicatorValue'] = param.get_param()
        widget = SizerWidget(btn)
        return widget

    def create_slider_entry(self, frame, param, component=None):
        if component is not None:
            scaled_value = param.get_param_component(component, scale=True)
        else:
            scaled_value = param.get_param(scale=True)
        slider = DirectSlider(parent=frame,
                              scale=(self.font_size * 16, 1, self.font_size * 6),
                              value=scaled_value,
                              range=param.get_range(scale=True),
                              suppressKeys=1,
                              command=self.do_update_slider
                              )
        widget1 = SizerWidget(slider)
        widget2 = self.create_spin_entry(frame, param, slider, component)
        slider['extraArgs'] = [slider, widget2[0].dgui_obj, param, component]
        return widget1, widget2[0]

    def create_spin_entry(self, frame, param, slider=None, component=None):
        scale3 = LVector3(self.text_scale[0], 1.0, self.text_scale[1])
        value_range = param.get_range()
        value_type = param.get_type()
        if value_range is None:
            value_range=(value_type(float("-inf")), value_type(float("inf")))
        step_size = param.get_step()
        if step_size is None:
            step_size = 1
        if component is not None:
            value = param.get_param_component(component)
        else:
            value = param.get_param()
        entry = DirectSpinBox(parent=frame,
                              value=value,
                              valueType=value_type,
                              textFormat='{}',
                              minValue=value_range[0],
                              maxValue=value_range[1],
                              stepSize=step_size,
                              suppressKeys=1,
                              command=self.do_update,
                              extraArgs=[slider, param, component],
                              valueEntry_width = 10,
                              valueEntry_text_align=TextNode.A_left,
                              valueEntry_frameColor=settings.entry_background,
                              scale=scale3)
        widget = SizerWidget(entry)
        return widget, (0, 0)

    def add_parameter(self, frame, hsizer, param):
        label = DirectLabel(parent=frame,
                            text=param.name,
                            textMayChange=True,
                            text_scale=self.text_scale,
                            text_align=TextNode.A_left)
        widget = SizerWidget(label)
        hsizer.add(widget, borders=self.borders, alignments=("min", "center"))
        if param.param_type == UserParameter.TYPE_BOOL:
            widget = self.create_bool_entry(frame, param)
            hsizer.add(widget, alignments=("min", "center"), borders=self.borders)
            hsizer.add((0, 0))
        elif param.param_type == UserParameter.TYPE_STRING:
            widget = self.create_text_entry(frame, param)
            hsizer.add(widget, alignments=("min", "center"), borders=self.borders)
            hsizer.add((0, 0))
        elif param.param_type == UserParameter.TYPE_INT:
            if param.value_range is not None:
                widget1, widget2 = self.create_slider_entry(frame, param)
            else:
                widget1, widget2 = self.create_spin_entry(frame, param)
            hsizer.add(widget1, alignments=("min", "center"), borders=self.borders)
            hsizer.add(widget2, alignments=("min", "center"), borders=self.borders)
        elif param.param_type == UserParameter.TYPE_FLOAT:
            if param.value_range is not None:
                widget1, widget2 = self.create_slider_entry(frame, param)
            else:
                widget1, widget2 = self.create_spin_entry(frame, param)
            hsizer.add(widget1, alignments=("min", "center"), borders=self.borders)
            hsizer.add(widget2, alignments=("min", "center"), borders=self.borders)
        elif param.param_type == UserParameter.TYPE_VEC:
            borders = (0, 0, round(self.font_size / 4.0), round(self.font_size / 4.0))
            vsizer1 = Sizer("vertical", gaps=(0, round(self.font_size * .25)))
            vsizer2 = Sizer("vertical", gaps=(0, round(self.font_size * .25)))
            for component in range(param.nb_components):
                widget1, widget2 = self.create_slider_entry(frame, param, component)
                vsizer1.add(widget1, proportions=(0., 1.), alignments=("min", "center"), borders=borders)
                vsizer2.add(widget2, borders=borders)
            hsizer.add(vsizer1, proportions=(0., 1.), borders=self.borders)
            hsizer.add(vsizer2, borders=self.borders)
        else:
            print("Unknown entry type", param.param_type)

    def add_parameters(self, frame, sizer, parameters, hsizer=None):
        for param in parameters:
            if param is None: continue
            if param.is_group():
                if param.is_empty(): continue
                border = round(self.font_size / 4.0)
                borders = (round(self.font_size / 2), 0, border, border)
                if param.name is not None:
                    label = DirectLabel(parent=frame,
                                        text=param.name,
                                        textMayChange=True,
                                        text_scale=self.text_scale,
                                        text_align=TextNode.A_left)
                    widget = SizerWidget(label)
                    sizer.add(widget, borders=borders)
                hsizer = Sizer("horizontal", prim_limit=3, gaps=(0, round(self.font_size * .75)))
                sizer.add(hsizer, alignments=("min", "expand"), borders=self.borders)
                self.add_parameters(frame, sizer, param.parameters, hsizer)
            else:
                if not hsizer:
                    hsizer = Sizer("horizontal", prim_limit=3, gaps=(0, round(self.font_size * .75)))
                    sizer.add(hsizer, proportions=(1., 0.), borders=self.borders)
                self.add_parameter(frame, hsizer, param)

    def create_layout(self, group):
        scale3 = LVector3(self.text_scale[0], 1.0, self.text_scale[1])
        tabbed_frame = TabbedFrame(
            frameSize=(0, self.width * settings.ui_scale, -self.height * settings.ui_scale, 0),
            tab_frameSize = (0, 7, 0, 2),
            tab_scale=scale3,
            tab_text_align = TextNode.ALeft,
            tab_text_pos = (0.2, 0.6),
            tabUnselectedColor = settings.tab_background,
            tabSelectedColor = settings.panel_background,
            scroll_scrollBarWidth=self.font_size,
            scroll_verticalScroll_pageSize=self.font_size,
            )
        self.layout = TabbedFrameContainer(tabbed_frame)
        for section in group.parameters:
            sizer = Sizer("vertical")
            frame = DirectFrame(state=DGG.NORMAL, frameColor=settings.panel_background)
            self.add_parameters(frame, sizer, section.parameters)
            sizer.update((self.width * settings.ui_scale, self.height * settings.ui_scale))
            size = sizer.min_size
            frame['frameSize'] = (0, size[0], -size[1], 0)
            tabbed_frame.addPage(frame, section.name)
        self.button_background = DirectFrame(
            parent=tabbed_frame,
            state=DGG.NORMAL,
            frameColor=settings.panel_background,
            sortOrder=tabbed_frame['sortOrder'] - 1)
        self.button_background['frameSize'] = [0, self.width * settings.ui_scale, 0, self.layout.height_offset]
        title = "Editor - " + group.name
        self.window = Window(title, parent=pixel2d, scale=self.scale, child=self.layout, owner=self)
        self.window.register_scroller(self.layout.frame.viewingArea)

    def update_parameter(self, param):
        pass

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
