from __future__ import print_function
from __future__ import absolute_import

from panda3d.core import Point3, TextNode
from direct.gui.DirectGui import DirectFrame, DGG
from direct.gui.OnscreenText import OnscreenText, Plain
from direct.showbase.ShowBaseGlobal import aspect2d

class Window():
    texture = None
    def __init__(self, title, scale, parent=None, child=None, transparent=False, owner=None):
        self.scale = scale
        self.owner = owner
        self.last_pos = None
        self.title_text = title
        self.title_color = (1, 1, 1, 1)
        self.title_pad = tuple(self.scale * 2)
        if parent is None:
            parent = aspect2d
        self.parent = parent
        if transparent:
            frameColor = (0, 0, 0, 0)
        else:
            frameColor = (0, 0, 0, 1)
        self.pad = 0
#         if Window.texture is None:
#             Window.texture = loader.loadTexture('textures/futureui1.png')
#         image_scale = (scale[0] * Window.texture.get_x_size(), 1, scale[1] * Window.texture.get_y_size())
        self.frame = DirectFrame(parent=parent, state=DGG.NORMAL, frameColor=frameColor)#, image=self.texture, image_scale=image_scale)
        self.title_frame = DirectFrame(parent=self.frame, state=DGG.NORMAL, frameColor=(.5, .5, .5, 1))
        self.title = OnscreenText(text=self.title_text,
                                  style=Plain,
                                  fg=self.title_color,
                                  scale=tuple(self.scale * 14),
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
                                  scale=tuple(self.scale * 14),
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
            frame_size = self.child.frame['frameSize']
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

    def getPos(self):
        return self.frame.getPos()

    def setPos(self, pos):
        self.frame.setPos(pos)
