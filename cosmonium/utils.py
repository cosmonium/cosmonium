# -*- coding: utf-8 -*-
from __future__ import print_function
from __future__ import absolute_import

from panda3d.core import LQuaterniond, LVector3d
from panda3d.core import ColorBlendAttrib, TransparencyAttrib

from . import settings
from .astro import units

def join_names(names):
    return ' / '.join(names)

def relative_rotation(rotation, axis, angle):
    axis.normalize()
    rel_axis = rotation.xform(axis)
    delta_quat = LQuaterniond()
    try:
        delta_quat.setFromAxisAngleRad(angle, rel_axis)
    except Exception as e:
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
        if blend == TransparencyBlend.TB_Alpha:
            blendAttrib = ColorBlendAttrib.make(ColorBlendAttrib.MAdd,
                                                ColorBlendAttrib.O_incoming_alpha, ColorBlendAttrib.O_one_minus_incoming_alpha,
                                                ColorBlendAttrib.M_add,
                                                ColorBlendAttrib.O_one, ColorBlendAttrib.O_one)
            translucid = True
        elif blend == TransparencyBlend.TB_PremultipliedAlpha:
            blendAttrib = ColorBlendAttrib.make(ColorBlendAttrib.MAdd,
                                                ColorBlendAttrib.O_one, ColorBlendAttrib.O_one_minus_incoming_alpha,
                                                ColorBlendAttrib.M_add,
                                                ColorBlendAttrib.O_one, ColorBlendAttrib.O_one)
            translucid = True
        elif blend == TransparencyBlend.TB_Additive:
            blendAttrib = ColorBlendAttrib.make(ColorBlendAttrib.MAdd,
                                                ColorBlendAttrib.O_one, ColorBlendAttrib.O_one,
                                                ColorBlendAttrib.M_add,
                                                ColorBlendAttrib.O_one, ColorBlendAttrib.O_one)
            translucid = True
        elif blend == TransparencyBlend.TB_AlphaAdditive:
            blendAttrib = ColorBlendAttrib.make(ColorBlendAttrib.MAdd,
                                                ColorBlendAttrib.O_one, ColorBlendAttrib.O_incoming_alpha,
                                                ColorBlendAttrib.M_add,
                                                ColorBlendAttrib.O_one, ColorBlendAttrib.O_one)
            translucid = True
        elif blend == TransparencyBlend.TB_Saturare:
            blendAttrib = ColorBlendAttrib.make(ColorBlendAttrib.MAdd,
                                                ColorBlendAttrib.O_one_minus_fbuffer_color, ColorBlendAttrib.O_one,
                                                ColorBlendAttrib.M_add,
                                                ColorBlendAttrib.O_one, ColorBlendAttrib.O_one)
            translucid = True
        if blendAttrib is not None:
            instance.setAttrib(blendAttrib)
        if translucid:
            instance.setTransparency(TransparencyAttrib.MAlpha)
