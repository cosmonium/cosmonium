from __future__ import print_function
from __future__ import absolute_import

from panda3d.core import PNMImage
from panda3d.core import Texture, TexGenAttrib, TransparencyAttrib, TextureStage
from math import pi, log, exp, sqrt

class PointObject(object):
    def apply(self, instance):
        pass

    def get_min_size(self):
        return 1

class SimplePoint(PointObject):
    def __init__(self, point_size=1):
        self.point_size = point_size

    def get_min_size(self):
        return self.point_size

    def apply(self, instance):
        instance.setRenderModeThickness(self.point_size)

class TexturePointSprite(PointObject):
    def __init__(self, file, min_size=5, max_size=15):
        self.file = file
        self.min_size = min_size
        self.max_size = max_size
        self.texture = None

    def get_min_size(self):
        return self.min_size

    def apply(self, instance):
        if self.texture is None:
            self.texture = loader.loadTexture(self.file)
        instance.setTexGen(TextureStage.getDefault(), TexGenAttrib.MPointSprite)
        instance.setTransparency(TransparencyAttrib.MAlpha)
        instance.setTexture(self.texture, 1)

class GenPointSprite(PointObject):
    def __init__(self, size=64):
        self.size = size
        self.half_size = size / 2.0
        self.texture = None
        self.image = None

    def generate(self):
        return None

    def apply(self, instance):
        if self.texture is None:
            if self.image is None:
                self.image = self.generate()
            self.texture = Texture()
            self.texture.load(self.image)
        instance.setTexGen(TextureStage.getDefault(), TexGenAttrib.MPointSprite)
        instance.setTransparency(TransparencyAttrib.MAlpha, 1)
        instance.setTexture(TextureStage('ts'), self.texture, 1)

class RoundDiskPointSprite(GenPointSprite):
    def __init__(self, size=64, max_value=1.0):
        GenPointSprite.__init__(self, size)
        self.max_value = max_value

    def get_min_size(self):
        return 2

    def generate(self):
        p = PNMImage(self.size, self.size, num_channels=2, maxval=65535)
        for y in range(self.size):
            ry = (y - self.half_size + 0.5) / (self.half_size - 1)
            for x in range(self.size):
                rx = (x - self.half_size + 0.5) / (self.half_size - 1)
                r = sqrt(rx*rx + ry*ry)
                if r > 1.0:
                    r = 0.0
                elif r > 0.5:
                    r = 2 * (1 - r)
                else:
                    r = 1.0
                r *= self.max_value
                p.set_xel_a(x, y, r, r, r, r)
        return p

class GaussianPointSprite(GenPointSprite):
    def __init__(self, size=64, fwhm=None, max_value=1.0):
        GenPointSprite.__init__(self, size)
        if fwhm is None:
            fwhm = self.size / 3.0
        self.fwhm = fwhm
        self.max_value = max_value

    def get_min_size(self):
        return 4

    def generate(self):
        p = PNMImage(self.size, self.size, num_channels=2)
        sigma = self.fwhm / (2 * sqrt(2 * log(2)))
        inv_sig2 = 1.0 / (2 * sigma * sigma)
        inv_factor = 1.0 / (sigma * sqrt(2.0 * pi))
        for y in range(self.size):
            ry = y - self.half_size + 0.5
            for x in range(self.size):
                rx = x - self.half_size + 0.5
                dist2 = rx*rx + ry*ry
                value = min(1.0, exp(- dist2 * inv_sig2) * inv_factor * self.fwhm)
                v = value * self.max_value
                p.set_xel_a(x, y, v, v, v, v)
        return p

class ExpPointSprite(GenPointSprite):
    def __init__(self, size=64, factor=1.0/(256*256*256), max_value=1.0):
        GenPointSprite.__init__(self, size)
        self.factor = factor
        self.max_value = max_value

    def get_min_size(self):
        return self.size

    def generate(self):
        p = PNMImage(self.size, self.size, num_channels=2)
        for y in range(self.size):
            ry = (y - self.half_size + 0.5) / self.size
            for x in range(self.size):
                rx = (x - self.half_size + 0.5) / self.size
                dist = sqrt(rx*rx + ry*ry)
                value = min(1.0, pow(self.factor, dist))
                v = value * self.max_value
                p.set_xel_a(x, y, v, v, v, v)
        return p

class MergeSprite(GenPointSprite):
    def __init__(self, size, top, bottom):
        GenPointSprite.__init__(self, size)
        self.top = top
        self.bottom = bottom

    def get_min_size(self):
        return self.top.get_min_size()

    def generate(self):
        pt = self.top.generate()
        pb = self.bottom.generate()
        p = PNMImage(self.size, self.size, num_channels=2)
        for y in range(self.size):
            yt = y - self.size / 2 + self.top.size / 2
            yb = y - self.size / 2 + self.bottom.size / 2
            for x in range(self.size):
                xt = x - self.size / 2 + self.top.size / 2
                xb = x - self.size / 2 + self.bottom.size / 2
                if xt < 0 or xt >= self.top.size or yt < 0 or yt >= self.top.size:
                    c = pb.get_xel_a(xb, yb)
                elif xb < 0 or xb >= self.bottom.size or yb < 0 or yb >= self.bottom.size:
                    c = pt.get_xel_a(xt, yt)
                else:
                    ct = pt.get_xel_a(xt, yt)
                    cb = pb.get_xel_a(xb, yb)
                    c = ct + cb * (1 - ct[3])
                    c[3] = ct[3] + cb[3] * (1 - ct[3])
                p.set_xel_a(x, y, c)
        return p

