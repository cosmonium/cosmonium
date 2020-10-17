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

from panda3d.core import Point3, TextNode, PGSliderBar
from direct.showbase.DirectObject import DirectObject
from direct.gui.DirectGui import DirectFrame, DGG
from direct.gui.DirectSlider import DirectSlider
from direct.gui.DirectScrollBar import DirectScrollBar
from direct.gui.OnscreenText import OnscreenText, Plain
from direct.showbase.ShowBaseGlobal import aspect2d

from .. import settings

class Window():
    texture = None
    def __init__(self, title_text, scale, parent=None, child=None, transparent=False, owner=None):
        self.title_text = title_text
        self.scale = scale
        self.title_size = settings.window_title_size
        self.owner = owner
        self.child = None
        self.last_pos = None
        self.title_color = (1, 1, 1, 1)
        self.title_pad = tuple(self.scale * 2)
        if parent is None:
            parent = aspect2d
        self.parent = parent
        if transparent:
            frameColor = (0, 0, 0, 0)
        else:
            frameColor = (0.5, 0.5, 0.5, 1)
        self.pad = 0
        self.event_handler = DirectObject()
        self.button_thrower = base.buttonThrowers[0].node()
        self.event_handler.accept("wheel_up-up", self.mouse_wheel_event, extraArgs = [-1])
        self.event_handler.accept("wheel_down-up", self.mouse_wheel_event, extraArgs = [1])
        self.scrollers = []

#         if Window.texture is None:
#             Window.texture = loader.loadTexture('textures/futureui1.png')
#         image_scale = (scale[0] * Window.texture.get_x_size(), 1, scale[1] * Window.texture.get_y_size())
        self.frame = DirectFrame(parent=parent, state=DGG.NORMAL, frameColor=frameColor)#, image=self.texture, image_scale=image_scale)
        self.title_frame = DirectFrame(parent=self.frame, state=DGG.NORMAL, frameColor=(.5, .5, .5, 1))
        self.title = OnscreenText(text=self.title_text,
                                  style=Plain,
                                  fg=self.title_color,
                                  scale=tuple(self.scale * self.title_size),
                                  parent=self.title_frame,
                                  pos=(0, 0),
                                  align=TextNode.ALeft,
                                  font=None,
                                  mayChange=True)
        bounds = self.title.getTightBounds()
        self.title_frame['frameSize'] = [0, bounds[1][0] - bounds[0][0] + self.title_pad[0] * 2,
                                         0, bounds[1][2] - bounds[0][2] + self.title_pad[1] * 2]
        self.title.setPos( -bounds[0][0] + self.title_pad[0],  -bounds[0][2] + self.title_pad[1])
        self.close_frame = DirectFrame(parent=self.frame, state=DGG.NORMAL, frameColor=(.5, .5, .5, 1))
        self.close = OnscreenText(text='X',
                                  style=Plain,
                                  fg=self.title_color,
                                  scale=tuple(self.scale * self.title_size),
                                  parent=self.close_frame,
                                  pos=(0, 0),
                                  align=TextNode.ACenter,
                                  font=None,
                                  mayChange=True)
        bounds = self.close.getTightBounds()
        self.close_frame['frameSize'] = [0, bounds[1][0] - bounds[0][0] + self.title_pad[0] * 2,
                                         self.title_frame['frameSize'][2], self.title_frame['frameSize'][3]]
        self.close.setPos( -bounds[0][0] + self.title_pad[0],  -bounds[0][2] + self.title_pad[1])
        self.frame.setPos(0, 0, 0)
        self.title_frame.bind(DGG.B1PRESS, self.start_drag)
        self.title_frame.bind(DGG.B1RELEASE, self.stop_drag)
        self.close_frame.bind(DGG.B1PRESS, self.close_window)
        self.set_child(child)

    def set_child(self, child):
        if child is not None:
            self.child = child
            child.reparent_to(self.frame)
            self.update()

    def update(self):
        if self.child is not None:
            frame_size = list(self.child.frame['frameSize'])
            if frame_size is not None:
                frame_size[0] -= self.pad
                frame_size[1] += self.pad
                frame_size[2] += self.pad
                frame_size[3] -= self.pad
            self.frame['frameSize'] = frame_size
        if self.frame['frameSize'] is not None:
            width = self.frame['frameSize'][1] - self.frame['frameSize'][0]
            title_size = self.title_frame['frameSize']
            title_size[0] = 0
            title_size[1] = width
            self.title_frame['frameSize'] = title_size
            self.close_frame.setPos(width - self.close_frame['frameSize'][1], 0, 0)

    def register_scroller(self, scroller):
        self.scrollers.append(scroller)

    def mouse_wheel_event(self, dir):
        # If the user is scrolling a scroll-bar, don't try to scroll the scrolled-frame too.
        region = base.mouseWatcherNode.getOverRegion()
        if region is not None:
            widget = base.render2d.find("**/*{0}".format(region.name))
            if widget.is_empty() or isinstance(widget.node(), PGSliderBar) or isinstance(widget.getParent().node(), PGSliderBar):
                return

        # Get the mouse-position
        if not base.mouseWatcherNode.hasMouse():
            return
        mouse_pos = base.mouseWatcherNode.getMouse()

        found_scroller = None
        # Determine whether any of the scrolled-frames are under the mouse-pointer
        for scroller in self.scrollers:
            bounds = scroller['frameSize']
            pos = scroller.get_relative_point(base.render2d, Point3(mouse_pos.get_x() ,0, mouse_pos.get_y()))
            if pos.x > bounds[0] and pos.x < bounds[1] and \
                pos.z > bounds[2] and pos.z < bounds[3]:
                found_scroller = scroller
                break

        if found_scroller is not None:
            if not found_scroller.verticalScroll.isHidden():
                self.do_mouse_scroll(found_scroller.verticalScroll, dir, None)
            else:
                self.do_mouse_scroll(found_scroller.horizontalScroll, dir, None)

    def do_mouse_scroll(self, obj, dir, data):
        if isinstance(obj, DirectSlider) or isinstance(obj, DirectScrollBar):
            obj.setValue(obj.getValue() + dir * obj["pageSize"] * 0.1)

    def start_drag(self, event):
        if base.mouseWatcherNode.has_mouse():
            mpos = base.mouseWatcherNode.get_mouse()
            self.drag_start = self.frame.parent.get_relative_point(render2d, Point3(mpos.get_x() ,0, mpos.get_y())) - self.frame.getPos()
            taskMgr.add(self.drag, "drag", -1)

    def drag(self, task):
        if base.mouseWatcherNode.has_mouse():
            mpos = base.mouseWatcherNode.get_mouse()
            current_pos = self.frame.parent.get_relative_point(render2d, Point3(mpos.get_x() ,0, mpos.get_y()))
            self.frame.set_pos(current_pos - self.drag_start)
        return task.again

    def close_window(self, event=None):
        if self.owner is not None:
            self.owner.window_closed(self)
        self.destroy()

    def stop_drag(self, event):
        taskMgr.remove("drag")
        self.last_pos = self.frame.getPos()

    def destroy(self):
        if self.frame is not None:
            self.frame.destroy()
        self.frame = None
        self.scrollers = []
        self.event_handler.ignore_all()

    def getPos(self):
        return self.frame.getPos()

    def setPos(self, pos):
        self.frame.setPos(pos)
