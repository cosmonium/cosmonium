from __future__ import print_function
from __future__ import absolute_import

from panda3d.core import TextNode, LColor, LVector3, WindowProperties, Texture, TransparencyAttrib

from direct.gui.DirectFrame import DirectFrame
from direct.gui.DirectLabel import DirectLabel
from direct.gui.OnscreenImage import OnscreenImage

from .. import settings

class Splash:
    def __init__(self):
        props = WindowProperties(base.win.getProperties())
        screen_width = props.getXSize()
        screen_height = props.getYSize()
        self.ratio = float(screen_width) / float(screen_height)
        self.text_scale = 0.03
        self.text_offset = self.text_scale / 4
        self.text_height = self.text_scale + self.text_offset
        self.image_scale = 0.3
        self.bg_texture = loader.loadTexture("textures/splash-background.jpg")
        if settings.use_srgb:
            self.bg_texture.set_format(Texture.F_srgb)
        self.bg_texture.setWrapU(Texture.WM_clamp)
        self.bg_texture.setWrapV(Texture.WM_clamp)
        self.bg_texture_ratio = float(self.bg_texture.get_x_size()) / self.bg_texture.get_y_size()
        self.texture = loader.loadTexture("textures/cosmonium-name-tp.png")
        self.texture_ratio = float(self.texture.get_x_size()) / self.texture.get_y_size()
        if self.ratio >= 1.0:
            sx = self.ratio
            sy = self.ratio / self.bg_texture_ratio
        else:
            sx = 1.0 / self.ratio
            sy = 1.0 / (self.ratio * self.bg_texture_ratio)
        self.bg_image = OnscreenImage(self.bg_texture,
                                   color=(1, 1, 1, 1),
                                   pos=(0, 0, 0),
                                   scale=(sx, 1, sy),
                                   parent=base.aspect2d)
        self.image = OnscreenImage(self.texture,
                                   color=(1, 1, 1, 1),
                                   scale=(self.image_scale * self.texture_ratio, 1, self.image_scale),
                                   parent=base.aspect2d)
        self.image.setTransparency(TransparencyAttrib.MAlpha)
        self.text = DirectLabel(text="",
                                text_align=TextNode.ACenter,
                                text_scale=self.text_scale,
                                #text_font=self.font_normal,
                                text_fg=(0.5, 0.5, 0.5, 1),
                                text_bg=(0, 0, 0, 0),
                                text_pos=(0, -self.image_scale - self.text_height))
                                #frameSize = (-0.75, 0.75, self.text_height, 0))
        self.text.reparent_to(base.aspect2d)

    def set_text(self, text):
        self.text.setText(text)
    def close(self):
        self.text.destroy()
        self.image.destroy()
        self.bg_image.destroy()
