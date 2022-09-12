#
#This file is part of Cosmonium.
#
#Copyright (C) 2018-2022 Laurent Deru.
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


from panda3d.core import FrameBufferProperties

from . import settings

import sys
import os


class OpenGLConfig:
    glsl_version = None
    core_profile = False
    floating_point_buffer = False
    srgb_framebuffer = False
    buffer_texture = False
    srgb_texture = False
    non_power_of_two_textures = False
    hardware_tessellation = False
    hardware_instancing = False
    texture_array = False

    @classmethod
    def request_opengl_config(cls, data):
        sync_video_value = int(settings.sync_video)
        data.append("sync-video %d" % sync_video_value)
        os.environ['__GL_SYNC_TO_VBLANK'] = str(sync_video_value)
        os.environ['vblank_mode'] = str(sync_video_value)

        if settings.use_gl_version is not None:
            data.append("gl-version %s" % settings.use_gl_version)
            cls.core_profile = True
        elif sys.platform == "darwin" and settings.use_core_profile_mac:
            data.append("gl-version 3 2")
            cls.core_profile = True
        if settings.use_inverse_z:
            data.append("gl-depth-zero-to-one true")
        if settings.force_power_of_two_textures:
            data.append("textures-power-2 down")
        else:
            data.append("textures-power-2 none")
        if settings.use_hardware_sprites:
            data.append("hardware-point-sprites #t")
        else:
            data.append("hardware-point-sprites #f")
        if settings.red_blue_stereo:
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

    @classmethod
    def check_glsl_version(cls, glsl_version):
        settings.shader_version = glsl_version

    @classmethod
    def test_floating_point_buffer(cls, base, rgba_bits):
        props = FrameBufferProperties()
        props.set_srgb_color(False)
        props.set_float_color(True)
        props.set_rgba_bits(*rgba_bits)
        buffer = base.win.make_texture_buffer("testBuffer", 256, 256, to_ram=True, fbp=props)
        if buffer is not None:
            supported = True
            buffer.set_active(False)
            base.graphicsEngine.remove_window(buffer)
        else:
            supported = False
        return supported

    @classmethod
    def test_aux_buffer(cls, base):
        props = FrameBufferProperties()
        props.set_aux_rgba(1)
        buffer = base.win.make_texture_buffer("testBuffer", 256, 256, to_ram=False, fbp=props)
        if buffer is not None:
            supported = True
            buffer.set_active(False)
            base.graphicsEngine.remove_window(buffer)
        else:
            supported = False
        return supported

    @classmethod
    def check_floating_point_buffer(cls, base):
        if settings.use_floating_point_buffer:
            cls.floating_point_buffer = True
            if not cls.test_floating_point_buffer(base, (32, 0, 0, 0)):
                print("One component floating point buffer not supported")
                cls.floating_point_buffer = False
            elif not cls.test_floating_point_buffer(base, (32, 32, 32, 32)):
                print("Four components floating point buffer not supported")
                cls.floating_point_buffer = False
        else:
            cls.floating_point_buffer = False

    @classmethod
    def check_aux_buffer(cls, base):
        if settings.use_aux_buffer:
            cls.aux_buffer = True
            if not cls.test_aux_buffer(base):
                print("Auxiliary buffer not supported")
                cls.aux_buffer = False
        else:
            cls.aux_buffer = False

    @classmethod
    def check_opengl_config(cls, base):
        gsg = base.win.gsg
        cls.glsl_version = gsg.getDriverShaderVersionMajor() * 100 + gsg.getDriverShaderVersionMinor()
        cls.buffer_texture = gsg.supports_buffer_texture
        cls.srgb_texture = settings.use_srgb and gsg.supports_texture_srgb
        cls.non_power_of_two_textures = not settings.force_power_of_two_textures and gsg.supports_tex_non_pow2
        cls.hardware_tessellation = settings.use_hardware_tessellation and gsg.supports_tessellation_shaders
        cls.hardware_instancing = settings.use_hardware_instancing and gsg.supports_geometry_instancing
        cls.texture_array = settings.use_texture_array and gsg.supports_2d_texture_array
        cls.inverse_z = settings.use_inverse_z
        cls.check_floating_point_buffer(base)
        cls.check_glsl_version(cls.glsl_version)

        if settings.use_color_picking and cls.non_power_of_two_textures and cls.glsl_version >= 420:
            settings.color_picking = True

        print("Hardware Vendor:", gsg.driver_vendor)
        print("Driver Renderer: %s (%s)" % (gsg.driver_renderer, gsg.driver_version))
        print("Shader version: %d" % cls.glsl_version)
        print("sRGB framebuffer:", cls.srgb_framebuffer)
        print("sRGB textures:", cls.srgb_texture)
        print("Hardware instancing:", cls.hardware_instancing)
        print("Hardware tessellation:", cls.hardware_tessellation)
        print("Inverse-Z buffer:", settings.use_inverse_z)
        print("Render to buffer:", cls.buffer_texture)
        print("Floating point buffer:", cls.floating_point_buffer)
        print("Texture array:", cls.texture_array)
