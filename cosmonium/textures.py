
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

from panda3d.core import TextureStage, Texture, LColor, PNMImage, CS_linear, CS_sRGB

from .dircontext import defaultDirContext
from .utils import TransparencyBlend, srgb_to_linear
from . import workers
from . import settings

import os

class TexCoord(object):
    Flat = 0
    Cylindrical = 1
    NormalizedCube = 2
    SqrtCube = 3

class TextureBase(object):
    default_texture = None

    def __init__(self):
        self.panda = True
        self.input_name = None

    def set_target(self, panda, input_name=None):
        self.panda = panda
        self.input_name = input_name


    def set_offset(self, offset):
        pass

    def load(self, patch, callback=None):
        pass

    def apply(self, shape):
        pass

    def apply_shader(self, shape, input_name, texture, texture_lod):
        shape.instance.set_shader_input(input_name, texture)

    def can_split(self, patch):
        return False

    def get_default_nb_components(self):
        return 4

    def get_default_max_val(self):
        return 255

    def get_default_color(self):
        return (1, 1, 1, 1)

    def create_default_image(self):
        image = PNMImage(1, 1, self.get_default_nb_components(), self.get_default_max_val())
        image.setXelA(0, 0, self.get_default_color())
        return image

    def create_default_texture(self):
        image = self.create_default_image()
        texture = Texture()
        texture.load(image)
        return (texture, 0, 0)

    def get_default_texture(self):
        if self.default_texture is None:
            self.default_texture = self.create_default_texture()
        return self.default_texture

    def clamp(self, texture):
        texture.setWrapU(Texture.WM_clamp)
        texture.setWrapV(Texture.WM_clamp)

    def vanish(self, texture):
        texture.setWrapU(Texture.WM_border_color)
        texture.setBorderColor(LColor(0, 0, 0, 0))

    def mipmap(self, texture):
        texture.setMinfilter(Texture.FT_linear_mipmap_linear)
        texture.setMagfilter(Texture.FT_linear_mipmap_linear)

    def mipmap_min(self, texture):
        texture.setMinfilter(Texture.FT_linear_mipmap_linear)
        texture.setMagfilter(Texture.FT_linear)

    def linear(self, texture):
        texture.setMinfilter(Texture.FT_linear)
        texture.setMagfilter(Texture.FT_linear)

    def debug_borders(self, texture):
        texture.setWrapU(Texture.WM_border_color)
        texture.setWrapV(Texture.WM_border_color)
        texture.setBorderColor(LColor(1, 0, 0, 1))

class TextureSource(object):
    cached = True
    procedural = False
    def __init__(self, attribution=None):
        self.loaded = False
        self.texture = None
        self.texture_size = 0
        self.attribution = attribution

    def is_patched(self):
        return False

    def set_offset(self, offset):
        pass

    def texture_name(self, patch):
        return None

    def texture_filename(self, patch):
        return None

    def load(self, patch, color_space=None, sync=False, callback=None, cb_args=()):
        pass

    def can_split(self, patch):
        return False

    def get_texture(self, patch):
        return (None, 0, 0)

    def get_recommended_shape(self):
        return None

class InvalidTextureSource(TextureSource):
    def load(self, patch, color_space=None, sync=False, callback=None, cb_args=()):
        callback(None, 0, 0, *cb_args)

class AutoTextureSource(TextureSource):
    factories = []
    def __init__(self, filename, attribution=None, context=defaultDirContext):
        TextureSource.__init__(self, attribution)
        self.filename = filename
        self.context = context
        self.source = None
        #TODO: override as these are accessed directly by external classes :(
        #should be transformed into methods
        self.cached = True

    @classmethod
    def register_source_factory(cls, factory, extensions, priority):
        #TODO: use struct iso tuple
        entry = (factory, extensions, priority)
        cls.factories.append(entry)
        cls.factories.sort(key=lambda x: x[2])

    def create_source(self):
        filename = self.filename
        if filename.endswith('.*'):
            filename = self.context.find_texture(filename)
            if filename is None:
                print("Could not find", self.filename)
                self.source = InvalidTextureSource()
                return
        base, extension = os.path.splitext(filename)
        if len(extension) > 0:
            extension = extension[1:]
        for entry in self.factories:
            if len(entry[1]) == 0 or extension in entry[1]:
                self.source = entry[0].create_source(self.filename, self.context)
                if self.source is not None:
                    self.cached = self.source.cached
                    self.texture_size = self.source.texture_size
                    return
        print("Could not find loader for", self.filename)
        self.source = InvalidTextureSource()

    def is_patched(self):
        if self.source is None:
            self.create_source()
        return self.source.is_patched()

    def texture_name(self, patch):
        return self.filename

    def texture_filename(self, patch):
        if self.source is None:
            self.create_source()
        return self.source.texture_filename(patch)

    def set_offset(self, offset):
        if self.source is None:
            self.create_source()
        self.source.set_offset(offset)

    def load(self, patch, color_space=None, sync=False, callback=None, cb_args=()):
        if self.source is None:
            self.create_source()
        return self.source.load(patch, color_space, sync, callback, cb_args)

    def can_split(self, patch):
        if self.source is None:
            self.create_source()
        return self.source.can_split(patch)

    def get_texture(self, patch):
        if self.source is None:
            self.create_source()
        return self.source.get_texture(patch)

    def get_recommended_shape(self):
        if self.source is None:
            self.create_source()
        return self.source.get_recommended_shape()

class TextureSourceFactory(object):
    def create_source(self, filename, context=defaultDirContext):
        return None

class TextureFileSource(TextureSource):
    cached = True
    def __init__(self, filename, attribution=None, context=defaultDirContext):
        TextureSource.__init__(self, attribution)
        self.filename = filename
        self.context = context
        self.loaded = False

    def texture_name(self, patch):
        return self.filename

    def texture_filename(self, patch):
        return self.context.find_texture(self.filename)

    def texture_loaded_cb(self, texture, callback, cb_args):
        self.texture = texture
        self.loaded = True
        if callback is not None:
            callback(self.texture, 0, 0, *cb_args)

    def load(self, patch, color_space=None, sync=False, callback=None, cb_args=()):
        if not self.loaded:
            filename=self.context.find_texture(self.filename)
            if filename is not None:
                if sync:
                    texture = workers.syncTextureLoader.load_texture(filename)
                    self.texture_loaded_cb(texture, callback, cb_args)
                else:
                    workers.asyncTextureLoader.load_texture(filename, None, self.texture_loaded_cb, (callback, cb_args))
            else:
                print("File", self.filename, "not found")
                self.texture_loaded_cb(None, callback, cb_args)
        else:
            if callback is not None:
                callback(self.texture, 0, 0, *cb_args)

    def get_texture(self, shape):
        return (self.texture, 0, 0)

class TextureFileSourceFactory(TextureSourceFactory):
    def create_source(self, filename, context=defaultDirContext):
        return TextureFileSource(filename, None, context)

#TODO: Should be done in cosmonium class
#Priority is set to a high value (ie low priority) as this is the fallback factory
AutoTextureSource.register_source_factory(TextureFileSourceFactory(), [], 9999)

class DirectTextureSource(TextureSource):
    cached = False
    def __init__(self, texture):
        TextureSource.__init__(self)
        self.loaded = True
        self.replace(texture)

    def replace(self, texture):
        self.texture = texture

    def load(self, patch, callback, cb_args):
        if callback is not None:
            callback(self.texture, 0, 0, *cb_args)

    def get_texture(self, shape):
        return (self.texture, 0, 0)

class SimpleTexture(TextureBase):
    def __init__(self, source, srgb=False, offset=0):
        TextureBase.__init__(self)
        if source is not None and not isinstance(source, TextureSource):
            source = AutoTextureSource(source, attribution=None)
        self.srgb = srgb
        self.source = source
        self.offset = offset
        self.tex_matrix= True

    def set_offset(self, offset):
        self.offset = offset

    def set_tex_matrix(self, tex_matrix):
        self.tex_matrix = tex_matrix

    def init_texture_stage(self, texture_stage, texture):
        pass

    def configure_instance(self, instance):
        pass

    def convert_texture(self, texture):
        pass

    def texture_loaded_cb(self, texture, texture_size, texture_lod, callback, cb_args):
        if texture is not None:
            self.convert_texture(texture)
        if callback is not None:
            callback(self, *cb_args)

    def load(self, patch, callback=None, cb_args=None):
        if not self.source.loaded or not self.source.cached:
            if self.srgb:
                color_space=CS_sRGB
            else:
                color_space=CS_linear
            if self.source.is_patched():
                self.source.set_offset(self.offset)
            self.source.load(patch, color_space=color_space, callback=self.texture_loaded_cb, cb_args=(callback, cb_args))
        else:
            if callback is not None:
                callback(self, *cb_args)

    def apply(self, shape):
        (texture, texture_size, texture_lod) = self.source.get_texture(shape)
        if texture is None:
            (texture, texture_size, texture_lod) = self.get_default_texture()
        if self.source.is_patched():
            self.clamp(texture)
        if not self.source.is_patched():
            self.mipmap(texture)
        else:
            if shape.lod == 0:
                self.mipmap_min(texture)
            else:
                self.linear(texture)
        if shape.vanish_borders:
            self.vanish(texture)
        if self.panda:
            self.apply_panda(shape, texture, texture_lod)
        else:
            self.apply_shader(shape, self.input_name, texture, texture_lod)
        self.configure_instance(shape.instance)

    def apply_panda(self, shape, texture, texture_lod):
        texture_stage = TextureStage(shape.str_id() + self.__class__.__name__)
        self.init_texture_stage(texture_stage, texture)
        if self.tex_matrix:
            shape.set_texture_to_lod(self, texture_stage, texture_lod, self.source.is_patched())
            if shape.swap_uv:
                shape.instance.setTexRotate(texture_stage, -90)
            scale = shape.instance.getTexScale(texture_stage)
            offset = shape.instance.getTexOffset(texture_stage)
            if shape.swap_uv:
                if shape.inv_v:
                    scale.x = -scale.x
                else:
                    offset.y += 1.0
                if not shape.inv_u:
                    scale.y = -scale.y
                    offset.x += 1.0
            else:
                if shape.inv_v:
                    scale.y = -scale.y
                    offset.y += 1.0
                if shape.inv_u:
                    scale.x = -scale.x
                    offset.x += 1.0
            shape.instance.setTexScale(texture_stage, scale)
            shape.instance.setTexOffset(texture_stage, offset)
        shape.instance.setTexture(texture_stage, texture, 1)

    def can_split(self, patch):
        return self.source.can_split(patch)

class DataTexture(TextureBase):
    def __init__(self, source):
        TextureBase.__init__(self)
        if source is not None and not isinstance(source, TextureSource):
            source = AutoTextureSource(source, attribution=None)
        self.source = source

    def texture_loaded_cb(self, texture, texture_size, texture_lod, callback, cb_args):
        if callback is not None:
            callback(self, *cb_args)

    def load(self, patch, callback=None, cb_args=None):
        if not self.source.loaded or not self.source.cached:
            self.source.load(patch, callback=self.texture_loaded_cb, cb_args=(callback, cb_args))
        else:
            if callback is not None:
                callback(self, *cb_args)

    def apply(self, shape, input_name):
        (texture, texture_size, texture_lod) = self.source.get_texture(shape)
        if texture is None:
            (texture, texture_size, texture_lod) = self.get_default_texture()
        if texture is not None:
            if self.source.is_patched():
                self.clamp(texture)
            shape.instance.set_shader_input(input_name, texture)

    def can_split(self, patch):
        return self.source.can_split(patch)

class VisibleTexture(SimpleTexture):
    def __init__(self, source, tint=None, srgb=None):
        if srgb is None:
            srgb = settings.srgb
        SimpleTexture.__init__(self, source, srgb=srgb)
        self.tint_color = tint
        self.check_specular_mask = False
        self.has_specular_mask = False
        self.transparent = False

    def init_texture_stage(self, texture_stage, texture):
        if self.tint_color is not None:
            if settings.disable_tint: return
            texture_stage.setColor(srgb_to_linear(self.tint_color))
            texture_stage.setCombineRgb(TextureStage.CMModulate,
                                        TextureStage.CSTexture, TextureStage.COSrcColor,
                                        TextureStage.CSConstant, TextureStage.COSrcColor)

    def apply(self, shape):
        SimpleTexture.apply(self, shape)
        if self.source.is_patched() and settings.debug_vt:
            self.debug_borders()

    def convert_texture(self, texture):
        if self.srgb:
            tex_format = texture.getFormat()
            if tex_format == Texture.F_rgb:
                texture.set_format(Texture.F_srgb)
            elif tex_format == Texture.F_rgba:
                texture.set_format(Texture.F_srgb_alpha)

class SurfaceTexture(VisibleTexture):
    category = 'albedo'
    def __init__(self, source, tint=None, srgb=None):
        VisibleTexture.__init__(self, source, tint, srgb=srgb)
        self.check_transparency = False
        self.transparent = False

    def texture_has_transparency(self, texture):
        texture_format = texture.get_format()
        return texture_format in (Texture.F_rgba, Texture.F_srgb_alpha, Texture.F_luminance_alpha, Texture.F_sluminance_alpha)

    def texture_loaded_cb(self, texture, texture_size, texture_lod, callback, cb_args):
        if self.check_specular_mask and self.texture_has_transparency(texture):
            self.has_specular_mask = True
        VisibleTexture.texture_loaded_cb(self, texture, texture_size, texture_lod, callback, cb_args)

    def init_texture_stage(self, texture_stage, texture):
        VisibleTexture.init_texture_stage(self, texture_stage, texture)
        if self.has_specular_mask:
            texture_stage.setMode(TextureStage.MModulateGloss)
        if self.check_transparency and self.texture_has_transparency(texture):
            self.transparent = True

    def get_default_color(self):
        return (1, 1, 1, 1)

class EmissionTexture(SurfaceTexture):
    def get_default_color(self):
        return (0, 0, 0, 1)

class TransparentTexture(VisibleTexture):
    category = 'albedo'
    def __init__(self, source, tint=None, level=0.0, blend=TransparencyBlend.TB_Alpha, srgb=None):
        VisibleTexture.__init__(self, source, tint, srgb)
        self.level = level
        self.transparent = True
        self.blend = blend

    def configure_instance(self, instance):
        TransparencyBlend.apply(self.blend, instance)

    def get_default_color(self):
        return (1, 1, 1, 0)

class NormalMapTexture(SimpleTexture):
    category = 'normal'
    def init_texture_stage(self, texture_stage, texture):
        texture_stage.setMode(TextureStage.MNormal)

    def get_default_color(self):
        return (.5, .5, 1, 1)

class SpecularMapTexture(SimpleTexture):
    category = 'specular'
    def init_texture_stage(self, texture_stage, texture):
        texture_stage.setMode(TextureStage.MGloss)

    def get_default_color(self):
        return (1, 1, 1, 1)

class OcclusionMapTexture(SimpleTexture):
    category = 'occlusion'
    def get_default_color(self):
        return (1, 1, 1, 1)

class BumpMapTexture(SimpleTexture):
    category = 'bump'
    def init_texture_stage(self, texture_stage, texture):
        texture_stage.setMode(TextureStage.MHeight)

    def get_default_color(self):
        return (0, 0, 0, 0)

class TextureArray(TextureBase):
    def __init__(self, textures=None, srgb=False):
        TextureBase.__init__(self)
        if textures is None:
            textures = []
        self.textures = textures
        if not settings.srgb:
            srgb = False
        self.srgb = srgb
        for (i, texture) in enumerate(textures):
            #TODO: should be done properly with an accessor or a map in this class
            texture.array_id = i
        self.texture = None
        self.texture_size = 0
        self.texture_lod = 0

    def add_texture(self, texture):
        self.textures.append(texture)
        #TODO: should be done properly with an accessor or a map in this class
        texture.array_id = len(self.textures) - 1

    def set_target(self, panda, input_name=None):
        self.panda = panda
        self.input_name = input_name

    def convert_texture(self, texture):
        if self.srgb:
            tex_format = texture.getFormat()
            if tex_format == Texture.F_rgb:
                texture.set_format(Texture.F_srgb)
            elif tex_format == Texture.F_rgba:
                texture.set_format(Texture.F_srgb_alpha)

    #TODO: This code is from TextureSource, a TextureArraySource should be created
    def texture_loaded_cb(self, texture, callback, cb_args):
        if texture is not None:
            self.convert_texture(texture)
        self.texture = texture
        if callback is not None:
            callback(self, *cb_args)

    def load(self, patch, callback=None, cb_args=None):
        if self.texture is None:
            sync = False
            if sync:
                texture = workers.syncTextureLoader.load_texture_array(self.textures)
                self.texture_loaded_cb(texture, callback, cb_args)
            else:
                workers.asyncTextureLoader.load_texture_array(self.textures, self.texture_loaded_cb, (callback, cb_args))
        else:
            if callback is not None:
                callback(self, *cb_args)

    def apply(self, shape):
        self.mipmap(self.texture)
        self.apply_shader(shape, self.input_name, self.texture, None)

    def can_split(self, patch):
        return False

class HeightMapTexture(DataTexture):
    category = 'heightmap'

    def get_default_nb_components(self):
        return 1

    def get_default_color(self):
        return (0, 0, 0, 0)

class VirtualTextureSource(TextureSource):
    cached = False
    def __init__(self, root, ext, size, attribution=None, context=defaultDirContext):
        TextureSource.__init__(self, attribution)
        self.map_patch = {}
        self.root = root
        self.ext = ext
        self.texture_size = size
        self.context = context

    def is_patched(self):
        return True

    def child_texture_name(self, patch):
        return None

    def texture_name(self, patch):
        return None

    def alpha_texture_name(self, patch):
        return None

    def can_split(self, patch):
        tex_name = self.child_texture_name(patch)
        exists = os.path.isfile(tex_name)
        return exists

    def texture_loaded_cb(self, texture, patch, callback, cb_args):
        if texture is not None:
            self.map_patch[patch.str_id()] = (texture, self.texture_size, patch.lod)
            if callback is not None:
                callback(texture, self.texture_size, patch.lod, *cb_args)
        else:
            parent_patch = patch.parent
            while parent_patch is not None and parent_patch.str_id() not in self.map_patch:
                parent_patch = parent_patch.parent
            if parent_patch is not None:
                if callback is not None:
                    callback(*(self.map_patch[parent_patch.str_id()] + cb_args))
            else:
                if callback is not None:
                    callback(None, self.texture_size, patch.lod, *cb_args)

    def load(self, patch, color_space=None, sync=False, callback=None, cb_args=()):
        if not patch.str_id() in self.map_patch:
            tex_name = self.texture_name(patch)
            filename = self.context.find_texture(tex_name)
            alpha_tex_name = self.alpha_texture_name(patch)
            alpha_filename = self.context.find_texture(alpha_tex_name)
            if filename is not None:
                if sync:
                    texture = workers.syncTextureLoader.load_texture(filename, alpha_filename)
                    self.texture_loaded_cb(texture, patch, callback, cb_args)
                else:
                    workers.asyncTextureLoader.load_texture(filename, alpha_filename, self.texture_loaded_cb, (patch, callback, cb_args))
            else:
                print("File", tex_name, "not found")
                self.texture_loaded_cb(None, patch, callback, cb_args)
        else:
            callback(*(self.map_patch[patch.str_id()] + cb_args))

    def get_texture(self, patch, strict=False):
        if patch.str_id() in self.map_patch:
            return self.map_patch[patch.str_id()]
        elif not strict:
            parent_patch = patch.parent
            while parent_patch is not None and parent_patch.str_id() not in self.map_patch:
                parent_patch = parent_patch.parent
            if parent_patch is not None:
                return self.map_patch[parent_patch.str_id()]
            else:
                return (None, self.texture_size, patch.lod)
        else:
            return (None, self.texture_size, patch.lod)
