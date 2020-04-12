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
from __future__ import division

from panda3d.core import LColor, Texture

from .heightmapshaders import HeightmapDataSource
from . import settings

from math import floor

class TexInterpolator(object):
    def __init__(self):
        pass

    def get_single_value(self, peeker, x, y, clamp=True):
        x /= peeker.get_x_size()
        y /= peeker.get_y_size()
        if clamp:
            x = min(max(x, 0.0), 1.0)
            y = min(max(y, 0.0), 1.0)
        value = LColor()
        result = peeker.lookup(value, x, y)
        if not result:
            print("Invalid offsets", x, y)
            return 0.0
        if settings.encode_float:
            value = value[0] + value[1] / 255.0 + value[2] / 65025.0 + value[3] / 16581375.0
        else:
            value = value[0]
        return value

    def get_bilinear_value(self, peeker, x, y, clamp=True):
        x /= peeker.get_x_size()
        y /= peeker.get_y_size()
        if clamp:
            x = min(max(x, 0.0), 1.0)
            y = min(max(y, 0.0), 1.0)
        value = LColor()
        result = peeker.lookup_bilinear(value, x, y)
        if not result:
            print("Invalid offsets", x, y)
            return 0.0
        if settings.encode_float:
            value = value[0] + value[1] / 255.0 + value[2] / 65025.0 + value[3] / 16581375.0
        else:
            value = value[0]
        return value

    def get_value(self, peeker, x, y):
        return None

    def configure_texture(self, texture):
        pass

    def get_data_source_filtering(self):
        return None

class NearestInterpolator(TexInterpolator):
    def get_value(self, peeker, x, y):
        return self.get_single_value(peeker, x, y)

    def configure_texture(self, texture):
        texture.setMinfilter(Texture.FT_nearest)
        texture.setMagfilter(Texture.FT_nearest)

    def get_data_source_filtering(self):
        return HeightmapDataSource.F_none

class BilinearInterpolator(TexInterpolator):
    def get_value(self, peeker, x, y):
        return self.get_bilinear_value(peeker, x, y)

    def configure_texture(self, texture):
        texture.setMinfilter(Texture.FT_linear)
        texture.setMagfilter(Texture.FT_linear)

    def get_data_source_filtering(self):
        return HeightmapDataSource.F_none

class ImprovedBilinearInterpolator(TexInterpolator):
    def get_value(self, peeker, x, y):
        return self.get_bilinear_value(peeker, x, y)

    def configure_texture(self, texture):
        texture.setMinfilter(Texture.FT_nearest)
        texture.setMagfilter(Texture.FT_nearest)

    def get_data_source_filtering(self):
        return HeightmapDataSource.F_improved_bilinear

class QuinticInterpolator(TexInterpolator):
    def get_value(self, peeker, x, y):
        x += 0.5
        y += 0.5

        i_x = floor(x)
        i_y = floor(y)
        f_x = x - i_x
        f_y = y - i_y

        f_x = f_x*f_x*f_x*(f_x*(f_x*6.0-15.0)+10.0)
        f_y = f_y*f_y*f_y*(f_y*(f_y*6.0-15.0)+10.0)

        return self.get_bilinear_value(peeker, i_x + f_x - 0.5, i_y + f_y - 0.5)

    def configure_texture(self, texture):
        texture.setMinfilter(Texture.FT_linear)
        texture.setMagfilter(Texture.FT_linear)

    def get_data_source_filtering(self):
        return HeightmapDataSource.F_quintic

class BSplineInterpolator(TexInterpolator):
    def configure_texture(self, texture):
        texture.setMinfilter(Texture.FT_linear)
        texture.setMagfilter(Texture.FT_linear)

    def get_data_source_filtering(self):
        return HeightmapDataSource.F_bspline

    def cubic(self, alpha):
        alpha2 = alpha * alpha
        alpha3 = alpha2 * alpha
        w0 = 1./6. * (-alpha3 + 3.*alpha2 - 3.*alpha + 1.)
        w1 = 1./6. * (3.*alpha3 - 6.*alpha2 + 4.)
        w2 = 1./6. * (-3.*alpha3 + 3.*alpha2 + 3.*alpha + 1.)
        w3 = 1./6. * alpha3
        return (w0, w1, w2, w3)

    def get_value(self, peeker, x, y):
        tc_x = floor(x - 0.5) + 0.5
        tc_y = floor(y - 0.5) + 0.5

        alpha_x = x - tc_x
        alpha_y = y - tc_y
        cubic_x = self.cubic(alpha_x)
        cubic_y = self.cubic(alpha_y)
    
        s_x = cubic_x[0] + cubic_x[1]
        s_y = cubic_x[2] + cubic_x[3]
        s_z = cubic_y[0] + cubic_y[1]
        s_w = cubic_y[2] + cubic_y[3]
        offset_x = tc_x - 1 + (cubic_x[1]) / s_x
        offset_y = tc_x + 1 + (cubic_x[3]) / s_y
        offset_z = tc_y - 1 + (cubic_y[1]) / s_z
        offset_w = tc_y + 1 + (cubic_y[3]) / s_w

        sx = s_x / (s_x + s_y)
        sy = s_z / (s_z + s_w)

        p00 = self.get_bilinear_value(peeker, offset_x, offset_z)
        p01 = self.get_bilinear_value(peeker, offset_y, offset_z)
        p10 = self.get_bilinear_value(peeker, offset_x, offset_w)
        p11 = self.get_bilinear_value(peeker, offset_y, offset_w)

        def mix(x, y, a):
            return x * (1.0 - a) + y * a

        a = mix(p01, p00, sx)
        b = mix(p11, p10, sx)
        return mix(b, a, sy)
