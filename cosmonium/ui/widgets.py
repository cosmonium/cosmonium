from __future__ import print_function
from __future__ import absolute_import

from panda3d.core import TextNode
from direct.gui.OnscreenText import OnscreenText
from direct.gui.DirectGui import DGG
from direct.gui.DirectScrolledFrame import DirectScrolledFrame

class ScrollText():
    def __init__(self, text='', align=TextNode.ALeft, scale=(1, 1), font=None, font_size=12, parent=None, frameColor=(0.33, 0.33, 0.33, .66)):
        if parent is None:
            parent = aspect2d
        self.parent = parent
        self.frame = DirectScrolledFrame(parent=parent, frameColor=frameColor, state=DGG.DISABLED,
                                         relief=DGG.FLAT,
                                         scrollBarWidth=scale[0] * font_size,
                                         horizontalScroll_relief=DGG.FLAT,
                                         verticalScroll_relief=DGG.FLAT,
                                         )
        self.text = OnscreenText(parent=self.frame.getCanvas(),
                                 text=text,
                                 align=align,
                                 scale=tuple(scale * font_size),
                                 font=font)
        bounds = self.text.getTightBounds()
        self.frame['canvasSize'] = [0, bounds[1][0] - bounds[0][0], -bounds[1][2] + bounds[0][2], 0]
        self.frame['frameSize'] = [0, 0.5, -0.5, 0]
        self.text.setPos(-bounds[0][0], -bounds[1][2])
        self.frame.setPos(0, 0, 0)

    def destroy(self):
        self.frame.destroy()

    def reparent_to(self, parent):
        self.frame.reparent_to(parent)
