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


from panda3d.core import load_prc_file_data
from panda3d.core import DepthTestAttrib, Texture
from panda3d.core import WindowProperties, FrameBufferProperties, GraphicsOutput
from direct.filter.FilterManager import FilterManager

from .shaders import PostProcessShader
from . import settings

import sys
import os

def request_opengl_config(data):
    sync_video_value = int(settings.sync_video)
    data.append("sync-video %d" % sync_video_value)
    os.environ['__GL_SYNC_TO_VBLANK'] = str(sync_video_value)
    os.environ['vblank_mode'] = str(sync_video_value)

    if settings.use_gl_version is not None:
        data.append("gl-version %s" % settings.use_gl_version)
        settings.core_profile = True
    elif sys.platform == "darwin" and settings.use_core_profile_mac:
        data.append("gl-version 3 2")
        settings.core_profile = True
    if settings.use_srgb and settings.use_hardware_srgb:
        data.append("framebuffer-srgb true")
    if settings.use_inverse_z:
        data.append("gl-depth-zero-to-one true")
    if settings.force_power_of_two_textures:
        data.append("textures-power-2 down")
    else:
        data.append("textures-power-2 none")
    if settings.use_hardware_sprites:
        data.append("hardware-point-sprites #t")
    if settings.stereoscopic_framebuffer:
        data.append("framebuffer-stereo #t")
    elif settings.red_blue_stereo:
        data.append("red-blue-stereo #t")
    elif settings.side_by_side_stereo:
        data.append("side-by-side-stereo #t")
    if settings.stereo_swap_eyes:
        data.append("swap-eyes #t")
    data.append("gl-coordinate-system default")
    data.append("gl-check-errors #t")
    if settings.dump_panda_shaders:
        data.append("dump-generated-shaders #t")
    data.append("driver-generate-mipmaps #t")
    data.append("gl-immutable-texture-storage true")
    data.append("state-cache #f")
    data.append("filled-wireframe-apply-shader #t")

    render_scene_to_buffer = False
    if settings.use_srgb and not settings.use_hardware_srgb:
        render_scene_to_buffer = True

    if settings.use_hdr:
        render_scene_to_buffer = True

    if settings.use_inverse_z:
        render_scene_to_buffer = True

    if not render_scene_to_buffer and settings.multisamples > 0:
        settings.framebuffer_multisampling = True
        load_prc_file_data("", "framebuffer-multisample 1")
        load_prc_file_data("", "multisamples %d" % settings.multisamples)

def _create_main_window(base):
    props = WindowProperties.get_default()
    have_window = False
    try:
        base.open_default_window(props=props)
        have_window = True
    except Exception:
        pass
    if have_window:
        base.bufferViewer.win = base.win
    return have_window

def create_main_window(base):
    if _create_main_window(base):
        return
    #We could not open the window, try to fallback to a supported configuration
    if settings.stereoscopic_framebuffer:
        print("Failed to open a window, disabling stereoscopic framebuffer...")
        load_prc_file_data("", "framebuffer-stereo #f")
        settings.stereoscopic_framebuffer = False
        if _create_main_window(base):
            return
    if settings.framebuffer_multisampling:
        print("Failed to open a window, disabling multisampling...")
        load_prc_file_data("", "framebuffer-multisample #f")
        settings.disable_multisampling = True
        settings.framebuffer_multisampling = False
        if _create_main_window(base):
            return
    #Can't create window even without multisampling
    if settings.use_gl_version is not None:
        print("Failed to open window with OpenGL Core; falling back to older OpenGL.")
        load_prc_file_data("", "gl-version")
        if _create_main_window(base):
            return
    print("Could not open any window")
    sys.exit(1)

def check_glsl_version(glsl_version):
    settings.shader_version = glsl_version

def test_floating_point_buffer(base, rgba_bits):
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

def test_aux_buffer(base):
    props = FrameBufferProperties()
    props.set_aux_rgba(1)
    buffer = base.win.make_texture_buffer("testBuffer", 256, 256, to_ram=False, fbp=props)
    if buffer is not None:
        supported = True
        buffer.set_active(False)
        base.graphicsEngine.removeWindow(buffer)
    else:
        supported = False
    return supported


def check_floating_point_buffer(base):
    if settings.use_floating_point_buffer:
        settings.floating_point_buffer = True
        if not test_floating_point_buffer(base, (32, 0, 0, 0)):
            print("One component floating point buffer not supported")
            settings.floating_point_buffer = False
        elif not test_floating_point_buffer(base, (32, 32, 32, 32)):
            print("Three components floating point buffer not supported")
            settings.floating_point_buffer = False
    else:
        settings.floating_point_buffer = False

    if settings.floating_point_buffer:
        print("Using floating point buffer")

    if not settings.encode_float and not settings.floating_point_buffer:
        settings.encode_float = True

def check_srgb_buffer(base):
    if settings.use_srgb:
        if not settings.use_hardware_srgb:
            settings.srgb_buffer = False
        elif not base.win.getFbProperties().get_srgb_color():
            print("Could not enable sRGB on main framebuffer")
            settings.srgb_buffer = False
        else:
            settings.srgb_buffer = True

def check_aux_buffer(base):
    if settings.use_aux_buffer:
        settings.aux_buffer = True
        if not test_aux_buffer(base):
            print("Auxiliary buffer not supported")
            settings.aux_buffer = False
    else:
        settings.aux_buffer = False

    if settings.aux_buffer:
        print("Using aux buffer")

def check_opengl_config(base):
    gsg = base.win.gsg
    glsl_version = gsg.getDriverShaderVersionMajor() * 100 + gsg.getDriverShaderVersionMinor()
    settings.buffer_texture = gsg.supports_buffer_texture
    settings.srgb_texture = gsg.supports_texture_srgb
    settings.non_power_of_two_textures = not settings.force_power_of_two_textures and gsg.supports_tex_non_pow2
    settings.hardware_tessellation = settings.use_hardware_tessellation and gsg.supports_tessellation_shaders
    settings.hardware_instancing = settings.use_hardware_instancing and gsg.supports_geometry_instancing
    settings.texture_array = settings.use_texture_array and gsg.supports_2d_texture_array
    check_floating_point_buffer(base)
    check_srgb_buffer(base)
    check_glsl_version(glsl_version)

    if settings.use_srgb and settings.srgb_texture:
        settings.srgb = True

    if settings.srgb and not settings.srgb_buffer and settings.buffer_texture and settings.non_power_of_two_textures:
        settings.render_scene_to_buffer = True
        settings.software_srgb = True

    if settings.use_hdr and settings.buffer_texture and settings.floating_point_buffer and settings.non_power_of_two_textures:
        settings.render_scene_to_buffer = True
        settings.hdr = True

    if settings.use_inverse_z and settings.buffer_texture and settings.non_power_of_two_textures:
        settings.render_scene_to_buffer = True

    if settings.use_color_picking and settings.non_power_of_two_textures and glsl_version >= 420:
        settings.color_picking = True

    print("Hardware Vendor:", gsg.driver_vendor)
    print("Driver Renderer: %s (%s)" % (gsg.driver_renderer, gsg.driver_version))
    print("Shader version: %d" % glsl_version)
    print("Hardware sRGB:", settings.srgb_buffer)
    print("sRGB textures:", settings.srgb_texture)
    print("Hardware instancing:", settings.hardware_instancing)
    print("Hardware tessellation:", settings.hardware_tessellation)
    print("Inverse-Z buffer:", settings.use_inverse_z)
    print("HDR:", settings.hdr)
    print("sRGB:", settings.srgb)
    print("Render to buffer:", settings.buffer_texture)
    print("Floating point buffer:", settings.floating_point_buffer)
    print("Texture array:", settings.texture_array)
    print("Color picking", settings.color_picking)

def check_and_create_rendering_buffers(showbase):
    if not settings.render_scene_to_buffer:
        return

    if not settings.buffer_texture:
        print("Render to buffer not supported")
        return

    print("Render scene to buffer")

    buffer_multisamples = 0
    if settings.render_scene_to_buffer and not settings.disable_multisampling and settings.use_multisampling and settings.multisamples > 0:
        buffer_multisamples = settings.multisamples

    manager = FilterManager(showbase.win, showbase.cam)
    color_buffer = Texture()
    depth_buffer = None
    aux_buffer = None
    if settings.use_inverse_z:
        render.set_attrib(DepthTestAttrib.make(DepthTestAttrib.M_greater))
        depth_buffer = Texture()
        showbase.win.set_clear_depth(0)
        float_depth = True
        depth_bits = 24
    else:
        float_depth = False
        depth_bits = 1
    if False:
        float_depth = False
        depth_bits = 1
        depth_buffer = Texture()
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
    if settings.aux_buffer:
        aux_buffer = Texture()
    textures = {'color': color_buffer, 'depth': depth_buffer, 'aux0': aux_buffer}
    fbprops = FrameBufferProperties()
    fbprops.setFloatColor(float_colors)
    fbprops.setRgbaBits(*rgba_bits)
    fbprops.setSrgbColor(settings.srgb_buffer)
    fbprops.setDepthBits(depth_bits)
    fbprops.setFloatDepth(float_depth)
    if not settings.framebuffer_multisampling:
        fbprops.setMultisamples(buffer_multisamples)
    final_quad = manager.render_scene_into(textures=textures, fbprops=fbprops)
    final_quad.clear_color()
    if aux_buffer is not None:
        manager.buffers[-1].setClearValue(GraphicsOutput.RTPAuxRgba0, (0.0, 0.0, 0.0, 0.0))
    final_quad_shader = PostProcessShader(gamma_correction=settings.software_srgb, hdr=settings.use_hdr).create_shader()
    final_quad.set_shader(final_quad_shader)
    final_quad.set_shader_input("color_buffer", color_buffer)
    final_quad.set_shader_input("exposure", 2)
    return textures
