from __future__ import print_function
from __future__ import absolute_import

from panda3d.core import WindowProperties, FrameBufferProperties, GraphicsPipe, GraphicsOutput, Texture, OrthographicLens, PandaNode, NodePath
from panda3d.core import LVector3, ColorWriteAttrib, LColor, CullFaceAttrib

from . import settings

class ShadowCaster(object):
    def __init__(self, size):
        self.size = size
        self.buffer = None
        self.depthmap = None
        self.cam = None
        self.shadow_caster = None
        self.bias = 0.

    def create(self):
        winprops = WindowProperties.size(self.size, self.size)
        props = FrameBufferProperties()
        props.setRgbColor(0)
        props.setAlphaBits(0)
        props.setDepthBits(1)
        self.buffer = base.graphicsEngine.makeOutput(
            base.pipe, "shadowsBuffer", -2,
            props, winprops,
            GraphicsPipe.BFRefuseWindow,
            base.win.getGsg(), base.win)

        if not self.buffer:
            print("Video driver cannot create an offscreen buffer.")
            return
        self.depthmap = Texture()
        self.buffer.addRenderTexture(self.depthmap, GraphicsOutput.RTMBindOrCopy,
                                 GraphicsOutput.RTPDepthStencil)

        self.depthmap.setMinfilter(Texture.FTShadow)
        self.depthmap.setMagfilter(Texture.FTShadow)
        self.depthmap.setBorderColor(LColor(1, 1, 1, 1))
        self.depthmap.setWrapU(Texture.WMBorderColor)
        self.depthmap.setWrapV(Texture.WMBorderColor)

        self.cam = base.makeCamera(self.buffer, lens=OrthographicLens())
        self.cam.reparent_to(render)
        self.node = self.cam.node()
        lci = NodePath(PandaNode("Light Camera Initializer"))
        lci.set_attrib(ColorWriteAttrib.make(ColorWriteAttrib.M_none), 1000)
        lci.set_attrib(CullFaceAttrib.make(CullFaceAttrib.MCullCounterClockwise), 1000)
        self.node.setInitialState(lci.getState())
        self.node.setScene(render)
        if settings.debug_shadow_frustum:
            self.node.showFrustum()

    def set_lens(self, size, near, far, direction):
        lens = self.node.get_lens()
        lens.set_film_size(size)
        lens.setNear(near)
        lens.setFar(far)
        lens.set_view_vector(direction, LVector3.up())
 
    def get_lens(self):
        return self.node.get_lens()

    def set_direction(self, direction):
        lens = self.node.get_lens()
        lens.set_view_vector(direction, LVector3.up())

    def get_pos(self):
        return self.cam.get_pos()

    def set_pos(self, position):
        self.cam.set_pos(position)

    def remove(self):
        self.node = None
        self.cam.remove_node()
        self.cam = None
        self.depthmap = None
        self.buffer.set_active(False)
        base.graphicsEngine.removeWindow(self.buffer)
        self.buffer = None
