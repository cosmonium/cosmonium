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
from direct.gui.DirectGui import DirectEntry, DirectSlider

from tabbedframe.TabbedFrame import TabbedFrame
from directguilayout.gui import Sizer
from directguilayout.gui import Widget as SizerWidget

from ..parameters import UserParameter

from .widgets import DirectWidgetContainer
from .window import Window


class ParamEditor():
    def __init__(self, font_family, font_size = 14, owner=None):
        self.window = None
        self.layout = None
        self.last_pos = None
        self.font_size = font_size
        self.owner = owner
        self.scale = LVector2(1, 1)
        self.body = None

    def add_parameter(self, frame, sizer, param):
        borders = (self.font_size, 0, self.font_size / 4.0, self.font_size / 4.0)
        if param.param_type == UserParameter.TYPE_BOOL:
            hsizer = Sizer("horizontal")
            label = DirectLabel(parent=frame,
                                text=param.name,
                                textMayChange=True,
                                text_scale=self.font_size,
                                text_align=TextNode.A_left)
            widget = SizerWidget(label)
            hsizer.add(widget, expand=True, borders=borders)
            btn = DirectCheckButton(parent=frame,
                                    text="",
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
                                    command=self.do_update,
                                    extraArgs=[None, param],
                                    )
            btn['indicatorValue'] = param.get_param()
            widget = SizerWidget(btn)
            hsizer.add(widget, expand=True, borders=borders)
            sizer.add(hsizer, expand=True, borders=borders)
        elif param.param_type == UserParameter.TYPE_STRING or param.value_range is None:
            hsizer = Sizer("horizontal")
            label = DirectLabel(parent=frame,
                                text=param.name,
                                textMayChange=True,
                                text_scale=self.font_size,
                                text_align=TextNode.A_left)
            widget = SizerWidget(label)
            hsizer.add(widget, expand=True, borders=borders)
            entry = DirectEntry(parent=frame,
                                initialText=str(param.get_param()),
                                numLines = 1,
                                width = 16,
                                command=self.do_update,
                                extraArgs=[None, param],
                                text_scale=self.font_size,
                                text_align=TextNode.A_left,
                                suppressKeys=1)
            widget = SizerWidget(entry)
            hsizer.add(widget, expand=True, borders=borders)
            sizer.add(hsizer, expand=True, borders=borders)
        elif param.param_type in (UserParameter.TYPE_INT, UserParameter.TYPE_FLOAT):
            hsizer = Sizer("horizontal")
            label = DirectLabel(parent=frame,
                                text=param.name,
                                textMayChange=True,
                                text_scale=self.font_size,
                                text_align=TextNode.A_left)
            widget = SizerWidget(label)
            hsizer.add(widget, expand=True, borders=borders)
            slider = DirectSlider(parent=frame,
                                  scale=(self.font_size * 16, 1, self.font_size * 2),
                                  value=param.get_param(scale=True),
                                  range=param.get_range(scale=True),
                                  command=self.do_update_slider)
            widget = SizerWidget(slider)
            hsizer.add(widget, expand=True, borders=borders)
            entry = DirectEntry(parent=frame,
                                initialText=str(param.get_param()),
                                numLines = 1,
                                width = 16,
                                command=self.do_update,
                                extraArgs=[slider, param],
                                text_scale=self.font_size,
                                text_align=TextNode.A_left,
                                suppressKeys=1)
            widget = SizerWidget(entry)
            hsizer.add(widget, expand=True, borders=borders)
            slider['extraArgs'] = [slider, entry, param]
            sizer.add(hsizer, expand=True, borders=borders)
        elif param.param_type == UserParameter.TYPE_VEC:
            hsizer = Sizer("horizontal")
            label = DirectLabel(parent=frame,
                                text=param.name,
                                textMayChange=True,
                                text_scale=self.font_size,
                                text_align=TextNode.A_left)
            widget = SizerWidget(label)
            hsizer.add(widget, borders=borders, alignment="center_v")
            vsizer = Sizer("vertical")
            for component in range(param.nb_components):
                hsizer2 = Sizer("horizontal")
                slider = DirectSlider(parent=frame,
                                      scale=(self.font_size * 16, 1, self.font_size * 2),
                                      value=param.get_param_component(component, scale=True),
                                      range=param.get_range(scale=True),
                                      command=self.do_update_slider
                                      )
                widget = SizerWidget(slider)
                hsizer2.add(widget, expand=True, borders=borders)
                entry = DirectEntry(parent=frame,
                                    initialText=str(param.get_param_component(component)),
                                    numLines = 1,
                                    width = 16,
                                    command=self.do_update,
                                    extraArgs=[slider, param, component],
                                    text_scale=self.font_size,
                                    text_align=TextNode.A_left,
                                    suppressKeys=1)
                widget = SizerWidget(entry)
                hsizer2.add(widget, expand=True, borders=borders)
                slider['extraArgs'] = [slider, entry, param, component]
                vsizer.add(hsizer2, expand=True, borders=borders)
            hsizer.add(vsizer, borders=borders, alignment="center_v")
            sizer.add(hsizer, expand=True, borders=borders)
        else:
            print("Unknown entry type", param.param_type)

    def add_parameters(self, frame, sizer, parameters):
        for param in parameters:
            if param is None: continue
            if param.is_group():
                borders = (self.font_size / 2, 0, self.font_size / 4.0, self.font_size / 4.0)
                if param.name is not None:
                    label = DirectLabel(parent=frame,
                                        text=param.name,
                                        textMayChange=True,
                                        text_scale=self.font_size,
                                        text_align=TextNode.A_left)
                    widget = SizerWidget(label)
                    sizer.add(widget, expand=True, borders=borders)
                self.add_parameters(frame, sizer, param.parameters)
            else:
                self.add_parameter(frame, sizer, param)

    def create_layout(self, parameters):
        scale3 = LVector3(self.scale[0], 1.0, self.scale[1])
        buttonSize = self.font_size * 2
        self.layout = DirectWidgetContainer(TabbedFrame(frameSize=(0, 800, -600, 0),
                                                        tab_frameSize = (0, 7, 0, 2),
                                                        tab_scale=scale3 * self.font_size,
                                                        tab_text_align = TextNode.ALeft,
                                                        tab_text_pos = (0.2, 0.6),
                                                        tabSelectedColor = (0.7, 0.7, 0.7, 1)))
        self.layout.frame.setPos(0, 0, -buttonSize)
        for group in parameters.parameters:
            sizer = Sizer("vertical")
            frame = DirectFrame(state=DirectGuiGlobals.NORMAL, frameColor=(1, 0, 0, 1))
            self.add_parameters(frame, sizer, group.parameters)
            sizer.update((800, 600))
            self.layout.frame.addPage(frame, group.name)
        title = "Editor"
        self.window = Window(title, parent=pixel2d, scale=self.scale, child=self.layout, owner=self)

    def do_update(self, value, slider, param, component=None):
        print("Update", param.name, value)
        value = param.convert_to_type(value)
        if component is None:
            param.set_param(value)
            if slider is not None:
                slider['value'] = param.get_param(scale=True)
        else:
            param.set_param_component(component, value)
            if slider is not None:
                slider['value'] = param.get_param_component(component, scale=True)
        self.body.update_user_parameters()

    def do_update_slider(self, slider, entry, param, component=None):
        value = slider['value']
        value = param.convert_to_type(value)
        if component is None:
            param.set_param(value, scale=True)
            if entry is not None:
                entry.enterText(str(param.get_param()))
        else:
            param.set_param_component(component, value, scale=True)
            if entry is not None:
                entry.enterText(str(param.get_param_component(component)))
        self.body.update_user_parameters()

    def show(self, body):
        if self.shown():
            print("Editor already shown")
            return
        self.body = body
        self.create_layout(body.get_user_parameters())
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
