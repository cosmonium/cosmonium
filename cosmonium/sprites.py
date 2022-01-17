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


from panda3d.core import PNMImage
from panda3d.core import Texture, TexGenAttrib, TransparencyAttrib, TextureStage

from .utils import linear_to_srgb_channel
from . import settings

from math import pi, log, exp, sqrt

class PointObject(object):
    def apply(self, instance):
        pass

class SimplePoint(PointObject):
    def __init__(self, point_size=1):
        self.point_size = point_size

    def apply(self, instance):
        instance.setRenderModeThickness(self.point_size)

class TexturePointSprite(PointObject):
    def __init__(self, filename):
        self.filename = file
        self.texture = None

    def apply(self, instance):
        if self.texture is None:
            self.texture = loader.loadTexture(self.filename)
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
        if settings.use_srgb:
            texture_format = self.texture.get_format()
            if texture_format == Texture.F_luminance:
                self.texture.set_format(Texture.F_sluminance)
            elif texture_format == Texture.F_luminance_alpha:
                self.texture.set_format(Texture.F_sluminance_alpha)
            elif texture_format == Texture.F_rgb:
                self.texture.set_format(Texture.F_srgb)
            elif texture_format == Texture.F_rgba:
                self.texture.set_format(Texture.F_srgb_alpha)
        instance.setTexGen(TextureStage.getDefault(), TexGenAttrib.MPointSprite)
        instance.setTransparency(TransparencyAttrib.MAlpha, 1)
        instance.setTexture(TextureStage('ts'), self.texture, 1)

class RoundDiskPointSprite(GenPointSprite):
    def __init__(self, size=64, max_value=1.0):
        GenPointSprite.__init__(self, size)
        self.max_value = max_value

    def generate(self):
        srgb = settings.use_srgb
        p = PNMImage(self.size, self.size, num_channels=2)
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
                va = r * self.max_value
                if srgb:
                    vc = linear_to_srgb_channel(va)
                else:
                    vc = va
                p.set_xel_a(x, y, vc, vc, vc, va)
        return p

class GaussianPointSprite(GenPointSprite):
    def __init__(self, size=64, fwhm=None, max_value=1.0):
        GenPointSprite.__init__(self, size)
        if fwhm is None:
            fwhm = self.size / 3.0
        self.fwhm = fwhm
        self.max_value = max_value

    def generate(self):
        srgb = settings.use_srgb
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
                va = value * self.max_value
                if srgb:
                    vc = linear_to_srgb_channel(va)
                else:
                    vc = va
                p.set_xel_a(x, y, vc, vc, vc, va)
        return p

class ExpPointSprite(GenPointSprite):
    # Factor must be 1/256 squared as the value at the border is factor^0.5
    def __init__(self, size=64, factor=1.0/(256*256), max_value=1.0):
        GenPointSprite.__init__(self, size)
        self.factor = factor
        self.max_value = max_value

    def get_min_size(self):
        return self.size

    def generate(self):
        srgb = settings.use_srgb
        p = PNMImage(self.size, self.size, num_channels=2)
        for y in range(self.size):
            ry = (y - self.half_size + 0.5) / self.size
            for x in range(self.size):
                rx = (x - self.half_size + 0.5) / self.size
                dist = sqrt(rx*rx + ry*ry)
                value = min(1.0, pow(self.factor, dist))
                va = value * self.max_value
                if srgb:
                    vc = linear_to_srgb_channel(va)
                else:
                    vc = va
                p.set_xel_a(x, y, vc, vc, vc, va)
        return p

class MergeSprite(GenPointSprite):
    def __init__(self, size, top, bottom):
        GenPointSprite.__init__(self, size)
        self.top = top
        self.bottom = bottom

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

