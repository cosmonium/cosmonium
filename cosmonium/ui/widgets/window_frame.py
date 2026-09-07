#
# This file is part of Cosmonium.
#
# Copyright (C) 2018-2026 Laurent Deru.
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


import builtins

from direct.gui.DirectGui import DGG, DirectFrame
from direct.gui.DirectScrollBar import DirectScrollBar
from direct.gui.DirectSlider import DirectSlider
from direct.gui.OnscreenText import OnscreenText, Plain
from direct.showbase.DirectObject import DirectObject
from panda3d.core import PGSliderBar, Point3, TextNode, TransparencyAttrib

from ...geometry.geometry import FrameGeom
from ..dock.decorated_sizer import COS_45
from ..skin import UIElement
from ..textures.circle_generator import CircleTextureGenerator
from .draggable import DraggableWidgetMixin


class WindowFrame(DraggableWidgetMixin):

    def __init__(self, title_text, scale, parent=None, child=None):
        DraggableWidgetMixin.__init__(self)
        self.title_text = title_text
        self.scale = scale
        self.parent = parent
        self.child = None
        self.title_color = (1, 1, 1, 1)
        self.title_pad = tuple(self.scale * 2)
        self.base = builtins.base

        if parent is not None:
            self.skin = parent.skin
        else:
            self.skin = None

        self.anchor = parent.anchor
        # Border/rounded-corner geometry, resolved from the skin here and recreated by
        # update() whenever the window's size changes.
        border_element = UIElement('borders', class_='border')
        border_style = self.skin.get(border_element)
        self.border_width = border_style.get_length('border_width', border_element, self.skin, default=1.0)
        self.border_color = border_style.border_color
        self.background_color = border_style.background_color
        self.corner_radius = border_style.get_length('border_radius', border_element, self.skin)
        self.corner_texture = None
        self.border = (self.border_width, self.border_width)
        # The title bar, close button and content are inset from the frame innern edges.
        # A plain rectangular border only needs to clear its own width, but a rounded one
        # needs more to avoid being overridden by the window title or close button.
        if self.corner_radius:
            self.content_inset = self.corner_radius - (self.corner_radius - self.border_width) * COS_45
        else:
            self.content_inset = self.border_width
        self.event_handler = DirectObject()
        self.button_thrower = self.base.buttonThrowers[0].node()
        self.event_handler.accept("wheel_up-up", self.mouse_wheel_event, extraArgs=[-1])
        self.event_handler.accept("wheel_down-up", self.mouse_wheel_event, extraArgs=[1])
        self.scrollers = []

        self.frame = DirectFrame(parent=parent.anchor, state=DGG.NORMAL)
        if self.border_width > 0 and self.border_color is not None:
            # For frame with rounded corners, the decorator frame is used to draw the border and background.
            # For frames without rounded corners, the frame itself is used to draw the border and background.
            fill = (0, 0, 0, 0) if self.corner_radius else (self.background_color or (0, 0, 0, 0))
            self.decorator_frame = DirectFrame(parent=self.frame, frameColor=fill)
        else:
            self.decorator_frame = None
        title_frame_element = UIElement('frame', class_='title-frame')
        self.title_frame = DirectFrame(parent=self.frame, state=DGG.NORMAL, **self.skin.get_style(title_frame_element))
        self.title_frame.set_pos(self.content_inset, 0, -self.content_inset)
        title_element = UIElement('onscreen-text', class_='title-text')
        self.title = OnscreenText(
            text=self.title_text,
            style=Plain,
            parent=self.title_frame,
            pos=(0, 0),
            align=TextNode.ALeft,
            mayChange=True,
            **self.skin.get_style(title_element),
        )
        bounds = self.title.get_tight_bounds()
        size = bounds[1] - bounds[0]
        bottom_left = bounds[0]
        self.title_frame['frameSize'] = [0, size[0] + self.title_pad[0] * 2, -size[2] - self.title_pad[1] * 2, 0]
        self.title.setTextPos(-bottom_left[0] + self.title_pad[0], -size[2] - bottom_left[2] - self.title_pad[1])
        close_frame_element = UIElement('frame', class_='close-frame')
        self.close_frame = DirectFrame(parent=self.frame, state=DGG.NORMAL, **self.skin.get_style(close_frame_element))
        close_element = UIElement('onscreen-text', class_='close-text')
        self.close = OnscreenText(
            text='X',
            style=Plain,
            parent=self.close_frame,
            pos=(0, 0),
            align=TextNode.ACenter,
            mayChange=True,
            **self.skin.get_style(close_element),
        )
        bounds = self.close.get_tight_bounds()
        size = bounds[1] - bounds[0]
        bottom_left = bounds[0]
        self.close_frame['frameSize'] = [
            0,
            size[0] + self.title_pad[0] * 2,
            self.title_frame['frameSize'][2],
            self.title_frame['frameSize'][3],
        ]
        self.close.setTextPos(-bottom_left[0] + self.title_pad[0], -size[2] - bottom_left[2] - self.title_pad[1])
        self.frame.set_pos(0, 0, 0)
        self.instance = self.frame
        self.setup_dragging(self.title_frame)
        if self.decorator_frame is not None:
            self.setup_dragging(self.decorator_frame)
        self.close_frame.bind(DGG.B1PRESS, self.close_window)
        self.set_child(child)

    def get_ui(self):
        return self.parent.get_ui()

    def set_child(self, child):
        if child is not None:
            self.child = child
            child.reparent_to(self.frame)
            self.update()

    def update(self):
        if self.child is None:
            return
        title_frame_size = self.title_frame['frameSize']
        title_height = title_frame_size[3] - title_frame_size[2]
        self.child.set_pos(self.content_inset, 0, -title_height - self.content_inset)
        frame_size = self.child.frame_size()
        width = frame_size[1] - frame_size[0]
        height = frame_size[3] - frame_size[2]
        title_size = self.title_frame['frameSize']
        title_size[1] = width
        self.title_frame['frameSize'] = title_size
        self.close_frame.set_pos(self.content_inset + width - self.close_frame['frameSize'][1], 0, -self.content_inset)
        if self.decorator_frame is not None:
            extended_width = width + self.content_inset * 2
            extended_height = height + title_height + self.content_inset * 2
            size = (extended_width, extended_height)
            if self.corner_radius:
                if self.corner_texture is None:
                    generator = CircleTextureGenerator(
                        radius=self.corner_radius,
                        border_width=self.border_width,
                        border_color=self.border_color,
                        inner_color=self.background_color,
                    )
                    self.corner_texture = generator.generate_circle()
                geom = FrameGeom(size, (self.corner_radius, self.corner_radius), texture=True, fill=True)
                geom.set_texture(self.corner_texture)
                geom.set_transparency(TransparencyAttrib.M_alpha)
            else:
                geom = FrameGeom(size, self.border, outer=False, texture=False)
                geom.set_color(*self.border_color)
            self.decorator_frame['geom'] = geom
            self.decorator_frame['frameSize'] = [0, extended_width, 0, -extended_height]

    def set_limits(self, limits):
        pos = self.frame.get_pos()
        new_pos = (min(max(pos[0], limits[0]), limits[1]), 0, max(min(pos[2], limits[2]), limits[3]))
        self.frame.set_pos(new_pos)
        self.set_drag_limits(limits)

    def register_scroller(self, scroller):
        self.scrollers.append(scroller)

    def mouse_wheel_event(self, dir):
        # If the user is scrolling a scroll-bar, don't try to scroll the scrolled-frame too.
        region = self.base.mouseWatcherNode.getOverRegion()
        if region is not None:
            widget = self.base.render2d.find("**/*{0}".format(region.name))
            if (
                widget.is_empty()
                or isinstance(widget.node(), PGSliderBar)
                or isinstance(widget.getParent().node(), PGSliderBar)
            ):
                return

        # Get the mouse-position
        if not self.base.mouseWatcherNode.hasMouse():
            return
        mouse_pos = self.base.mouseWatcherNode.getMouse()

        found_scroller = None
        # Determine whether any of the scrolled-frames are under the mouse-pointer
        for scroller in self.scrollers:
            bounds = scroller['frameSize']
            pos = scroller.get_relative_point(self.base.render2d, Point3(mouse_pos.get_x(), 0, mouse_pos.get_y()))
            if pos.x > bounds[0] and pos.x < bounds[1] and pos.z > bounds[2] and pos.z < bounds[3]:
                found_scroller = scroller
                break

        if found_scroller is not None:
            if not found_scroller.verticalScroll.isHidden():
                self.do_mouse_scroll(found_scroller.verticalScroll, dir, None)
            elif not found_scroller.horizontalScroll.isHidden():
                self.do_mouse_scroll(found_scroller.horizontalScroll, dir, None)

    def do_mouse_scroll(self, obj, dir, data):
        if isinstance(obj, DirectSlider) or isinstance(obj, DirectScrollBar):
            obj.setValue(obj.getValue() + dir * obj["pageSize"])

    def close_window(self, event=None):
        if self.parent is not None:
            self.parent.window_closed()

    def destroy(self):
        self.cleanup_drag()
        if self.frame is not None:
            self.frame.destroy()
        self.frame = None
        self.scrollers = []
        self.event_handler.ignore_all()

    def getPos(self):
        return self.frame.get_pos()

    def setPos(self, pos):
        self.frame.set_pos(pos)
