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

from panda3d.core import loadPrcFileData
from panda3d.core import DepthTestAttrib, Texture, Shader
from panda3d.core import FrameBufferProperties
from direct.filter.FilterManager import FilterManager

from .shaders import PostProcessShader
from . import settings

import sys

def request_opengl_config(data):
    if settings.use_inverse_z:
        settings.shader_min_version = max(410, settings.shader_min_version)
        settings.render_scene_to_buffer = True
        settings.power_of_two_textures = False
    if settings.allow_tesselation:
        settings.shader_min_version = max(410, settings.shader_min_version)
    if settings.allow_instancing:
        settings.shader_min_version = max(140, settings.shader_min_version)
    settings.shader_min_version = max(130, settings.shader_min_version)
    if sys.platform == "darwin":
        #MacOS does not support GLSL version 130
        settings.shader_min_version = max(150, settings.shader_min_version)
    if settings.use_hdr:
        settings.render_scene_to_buffer = True
        settings.power_of_two_textures = False
        settings.render_scene_to_float = True
    data.append("gl-version 3 2")
    if settings.use_srgb:
        if settings.use_hardware_srgb:
            data.append("framebuffer-srgb true")
    if settings.use_inverse_z:
        data.append("gl-depth-zero-to-one true")
    if not settings.power_of_two_textures:
        data.append("textures-power-2 none")
    data.append("hardware-point-sprites #t")
    data.append("text-encoding utf8")
    data.append("gl-coordinate-system default")
    data.append("gl-check-errors #t")
    if settings.dump_panda_shaders:
        data.append("dump-generated-shaders #t")
    if settings.multisamples > 0 and not settings.render_scene_to_buffer:
        data.append("framebuffer-multisample 1")
        data.append("multisamples %d" % settings.multisamples)
    data.append("driver-generate-mipmaps #t")
    #TODO: Still needed ?
    data.append("bounds-type box")

def check_opengl_config(gsg):
    #TODO: Test if the requested configuration above is supported by the generated GSG
    print("Hardware Vendor:", gsg.driver_vendor)
    print("Driver Renderer: %s (%s)" % (gsg.driver_renderer, gsg.driver_version))
    print("Shader version: %d.%d" % (gsg.getDriverShaderVersionMajor(), gsg.getDriverShaderVersionMinor()))
    print("Hardware sRGB:", settings.use_hardware_srgb)
    print("Hardware instancing:", settings.allow_instancing)
    print("Hardware tesselation:", settings.allow_tesselation)
    print("Inverse-Z buffer:", settings.use_inverse_z)
    print("HDR:", settings.use_hdr)

def test_floating_point_buffer(rgba_bits):
        props = FrameBufferProperties()
        props.set_srgb_color(False)
        props.set_float_color(True)
        props.set_rgba_bits(*rgba_bits)
        buffer = base.win.make_texture_buffer("testBuffer", 256, 256, to_ram=True, fbp=props)
        if buffer is not None:
            supported = True
            buffer.set_active(False)
            base.graphicsEngine.removeWindow(buffer)
        else:
            supported = False
        return supported

def check_and_create_rendering_buffers(showbase):
    if settings.allow_floating_point_buffer:
        settings.floating_point_buffer = True
        if not test_floating_point_buffer((32, 0, 0, 0)):
            print("One component floating point buffer not supported")
            settings.floating_point_buffer = False
        if not test_floating_point_buffer((32, 32, 32, 32)):
            print("Three components floating point buffer not supported")
            settings.floating_point_buffer = False
    else:
        settings.floating_point_buffer = False

    if settings.floating_point_buffer:
        print("Using floating point buffer")

    if not settings.encode_float and not settings.floating_point_buffer:
        settings.encode_float = True

    if settings.use_srgb and settings.use_hardware_srgb and not showbase.win.getFbProperties().get_srgb_color():
        print("Could not enable sRGB on main framebuffer")
        settings.use_hardware_srgb = False

    final_stage_srgb = False
    if settings.use_srgb and not settings.use_hardware_srgb:
        settings.render_scene_to_buffer = True
        settings.render_scene_to_float = True
        final_stage_srgb = True

    buffer_multisamples = 0
    if settings.render_scene_to_buffer and settings.multisamples > 0:
        buffer_multisamples = settings.multisamples

    if settings.render_scene_to_buffer:
        print("Render scene to buffer")
        manager = FilterManager(showbase.win, showbase.cam)
        color_buffer = Texture()
        if settings.use_inverse_z:
            render.set_attrib(DepthTestAttrib.make(DepthTestAttrib.M_greater))
            depth_buffer = Texture()
            showbase.win.set_clear_depth(0)
            float_depth = True
            depth_bits = 24
        else:
            depth_buffer = None
            float_depth = False
            depth_bits = 1
        if settings.render_scene_to_float:
            if settings.floating_point_buffer:
                rgba_bits = (32, 32, 32, 32)
                float_colors = True
            else:
                print("Floating point buffer not available, sRBG conversion will show artifacts")
                rgba_bits = (1, 1, 1, 1)
                float_colors = False
        else:
            rgba_bits = (1, 1, 1, 1)
            float_colors = False
        srgb_buffer = settings.use_srgb and settings.use_hardware_srgb
        textures = {'color': color_buffer, 'depth': depth_buffer}
        fbprops = FrameBufferProperties()
        fbprops.setFloatColor(float_colors)
        fbprops.setRgbaBits(*rgba_bits)
        fbprops.setSrgbColor(srgb_buffer)
        fbprops.setDepthBits(depth_bits)
        fbprops.setFloatDepth(float_depth)
        fbprops.setMultisamples(buffer_multisamples)
        final_quad = manager.render_scene_into(textures=textures, fbprops=fbprops)
        final_quad_shader = PostProcessShader(gamma_correction=final_stage_srgb, hdr=settings.use_hdr).create_shader()
        final_quad.set_shader(final_quad_shader)
        final_quad.set_shader_input("color_buffer", color_buffer)
        final_quad.set_shader_input("exposure", 2)
