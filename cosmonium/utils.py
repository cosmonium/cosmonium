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

from panda3d.core import LQuaterniond, LVector3d, LColor
from panda3d.core import ColorBlendAttrib, TransparencyAttrib

from . import settings
from .astro import units

def join_names(names):
    return ' / '.join(names)

def quaternion_from_euler(h, p, r):
    rotation = LQuaterniond()
    rotation.set_hpr((h, p, r))
    return rotation

def relative_rotation(rotation, axis, angle):
    axis.normalize()
    rel_axis = rotation.xform(axis)
    delta_quat = LQuaterniond()
    try:
        delta_quat.setFromAxisAngleRad(angle, rel_axis)
    except AssertionError:
        print("invalid axis", axis, axis.length(), rel_axis, rel_axis.length())
    return rotation * delta_quat

def mag_to_scale(magnitude):
    if magnitude > settings.lowest_app_magnitude:
        return 0.0
    if magnitude < settings.max_app_magnitude:
        return 1.0
    return settings.min_mag_scale + (1 - settings.min_mag_scale) * (settings.lowest_app_magnitude - magnitude) / (settings.lowest_app_magnitude - settings.max_app_magnitude)

def mag_to_scale_nolimit(magnitude):
    if magnitude > settings.lowest_app_magnitude:
        return 0.0
    if magnitude < settings.max_app_magnitude:
        return 1.0
    return (settings.lowest_app_magnitude - magnitude) / (settings.lowest_app_magnitude - settings.max_app_magnitude)

def LQuaternionromAxisAngle(axis, angle, angle_units=units.Rad):
    if isinstance(axis, list):
        axis = LVector3d(*axis)
    axis.normalize()
    rot = LQuaterniond()
    rot.setFromAxisAngleRad(angle * angle_units, axis)
    return rot

def isclose(a, b, rel_tol=1e-09, abs_tol=0.0):
    return abs(a-b) <= max(rel_tol * max(abs(a), abs(b)), abs_tol)

class TransparencyBlend:
    TB_None = 0
    TB_Alpha = 1
    TB_PremultipliedAlpha = 2
    TB_Additive = 3
    TB_AlphaAdditive = 4
    TB_Saturate = 5

    @staticmethod
    def apply(blend, instance):
        blendAttrib = None
        translucid = False
        if blend == TransparencyBlend.TB_None:
            pass
        elif blend == TransparencyBlend.TB_Alpha:
            blendAttrib = ColorBlendAttrib.make(ColorBlendAttrib.MAdd,
                                                ColorBlendAttrib.O_incoming_alpha, ColorBlendAttrib.O_one_minus_incoming_alpha,
                                                ColorBlendAttrib.M_add,
                                                ColorBlendAttrib.O_one, ColorBlendAttrib.O_one_minus_incoming_alpha)
            translucid = True
        elif blend == TransparencyBlend.TB_PremultipliedAlpha:
            blendAttrib = ColorBlendAttrib.make(ColorBlendAttrib.MAdd,
                                                ColorBlendAttrib.O_one, ColorBlendAttrib.O_one_minus_incoming_alpha,
                                                ColorBlendAttrib.M_add,
                                                ColorBlendAttrib.O_one, ColorBlendAttrib.O_one_minus_incoming_alpha)
            translucid = True
        elif blend == TransparencyBlend.TB_Additive:
            blendAttrib = ColorBlendAttrib.make(ColorBlendAttrib.MAdd,
                                                ColorBlendAttrib.O_one, ColorBlendAttrib.O_one,
                                                ColorBlendAttrib.M_add,
                                                ColorBlendAttrib.O_one, ColorBlendAttrib.O_one)
            translucid = False
        elif blend == TransparencyBlend.TB_AlphaAdditive:
            blendAttrib = ColorBlendAttrib.make(ColorBlendAttrib.MAdd,
                                                ColorBlendAttrib.O_one, ColorBlendAttrib.O_incoming_alpha,
                                                ColorBlendAttrib.M_add,
                                                ColorBlendAttrib.O_one, ColorBlendAttrib.O_incoming_alpha)
            translucid = True
        elif blend == TransparencyBlend.TB_Saturate:
            blendAttrib = ColorBlendAttrib.make(ColorBlendAttrib.MAdd,
                                                ColorBlendAttrib.O_one_minus_fbuffer_color, ColorBlendAttrib.O_one,
                                                ColorBlendAttrib.M_add,
                                                ColorBlendAttrib.O_one, ColorBlendAttrib.O_one)
            translucid = True
        else:
            print("Unknown blend mode", blend)
        if blendAttrib is not None:
            instance.setAttrib(blendAttrib)
        if translucid:
            instance.set_bin('transparent', 0)

def srgb_to_linear_channel(color):
    return pow(((color + 0.055) / 1.055), 2.4) if color > 0.0404482362771082 else color / 12.92

def  linear_to_srgb_channel(value):
    return 1.055 * pow(value, 0.41666) - 0.055 if(value > 0.0031308) else 12.92 * value

def srgb_to_linear(color):
    if settings.srgb:
        return LColor(srgb_to_linear_channel(color[0]),
                      srgb_to_linear_channel(color[1]),
                      srgb_to_linear_channel(color[2]),
                      color[3])
    else:
        return color

def linear_to_srgb(color):
    if settings.srgb:
        return LColor(linear_to_srgb_channel(color[0]),
                      linear_to_srgb_channel(color[1]),
                      linear_to_srgb_channel(color[2]),
                      color[3])
    else:
        return color

def int_to_color(value):
    r = value & 0xFF
    g = (value >> 8) & 0xFF
    b = (value >> 16) & 0xFF
    #a = (value >> 24) & 0xFF
    return LColor(r / 255.0, g / 255.0, b / 255.0, 1.0)

def color_to_int(color):
    value = round(color[0] * 255)
    value += round(color[1] * 255) << 8
    value += round(color[2] * 255) << 16
    #value += round(color[3] * 255) << 24
    return value
