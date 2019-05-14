from __future__ import print_function
from __future__ import absolute_import

from panda3d.core import loadPrcFileData
from panda3d.core import DepthTestAttrib, Texture, Shader
from panda3d.core import FrameBufferProperties

from .shaders import PostProcessShader
from .support.FilterManager import FilterManager
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
        manager = FilterManager(showbase.win, showbase.cam)
        color_buffer = Texture()
        if settings.use_inverse_z:
            render.set_attrib(DepthTestAttrib.make(DepthTestAttrib.M_greater))
            depth_buffer = Texture()
            showbase.win.set_clear_depth(0)
            depthtex = depth_buffer
            floatdepth = True
            depthbits = 24
        else:
            depthtex = None
            floatdepth = False
            depthbits = 1
        if settings.render_scene_to_float:
            if settings.floating_point_buffer:
                rgbabits = (32, 32, 32, 32)
                floatcolor = True
            else:
                print("Floating point buffer not available, sRBG conversion will show artifacts")
                rgbabits = (1, 1, 1, 1)
                floatcolor = False
        else:
            rgbabits = (1, 1, 1, 1)
            floatcolor = False
        srgb_buffer = settings.use_srgb and settings.use_hardware_srgb
        final_quad = manager.render_scene_into(colortex=color_buffer, rgbabits=rgbabits, floatcolor=floatcolor, srgb=srgb_buffer,
                                               depthtex=depthtex, depthbits=depthbits, floatdepth=floatdepth,
                                               multisamples=buffer_multisamples)
        final_quad_shader = PostProcessShader(gamma_correction=final_stage_srgb, hdr=settings.use_hdr).create_shader()
        final_quad.set_shader(final_quad_shader)
        final_quad.set_shader_input("color_buffer", color_buffer)
        final_quad.set_shader_input("exposure", 2)
