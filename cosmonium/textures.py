
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


from panda3d.core import TextureStage, Texture, LColor, PNMImage

from .dircontext import defaultDirContext
from .utils import TransparencyBlend
from . import workers
from . import settings

import os


class TexCoord(object):
    Flat = 0
    Cylindrical = 1
    NormalizedCube = 2
    SqrtCube = 3


class TextureConfiguration:
    def __init__(self, *,
                 wrap_u=Texture.WM_repeat, wrap_v=Texture.WM_repeat, wrap_w=Texture.WM_repeat,
                 anisotropic_degree=0,
                 minfilter=Texture.FT_default, magfilter=Texture.FT_default,
                 border_color=LColor(0, 0, 0, 1),
                 format=None,
                 convert_to_srgb=False):
        self.wrap_u = wrap_u
        self.wrap_v = wrap_v
        self.wrap_w = wrap_w
        self.anisotropic_degree = anisotropic_degree
        self.minfilter = minfilter
        self.magfilter = magfilter
        self.border_color = border_color
        self.format = format
        self.convert_to_srgb = convert_to_srgb

    def create_2d(self, name, width, height):
        if self.format in (Texture.F_rgba32, Texture.F_rgb32, Texture.F_rg32, Texture.F_r32):
            c_type = Texture.T_float
        elif self.format in (Texture.F_rgba16, Texture.F_rgb16, Texture.F_rg16, Texture.F_r16):
            c_type = Texture.T_half_float
        else:
            c_type = Texture.T_byte
        texture = Texture(name)
        texture.setup_2d_texture(width, height, c_type, self.format)
        self.apply(texture)
        return texture

    def apply(self, texture):
        if self.format is not None:
            texture.set_format(self.format)
        texture.set_wrap_u(self.wrap_u)
        texture.set_wrap_v(self.wrap_v)
        texture.set_wrap_w(self.wrap_w)
        texture.set_anisotropic_degree(self.anisotropic_degree)
        texture.set_minfilter(self.minfilter)
        texture.set_magfilter(self.magfilter)
        texture.set_border_color(self.border_color)
        if self.convert_to_srgb:
            texture_format = texture.get_format()
            if texture_format == Texture.F_luminance:
                texture.set_format(Texture.F_sluminance)
            elif texture_format == Texture.F_luminance_alpha:
                texture.set_format(Texture.F_sluminance_alpha)
            elif texture_format == Texture.F_rgb:
                texture.set_format(Texture.F_srgb)
            elif texture_format == Texture.F_rgba:
                texture.set_format(Texture.F_srgb_alpha)


class TextureBase(object):
    default_texture = None

    def __init__(self):
        self.panda = True
        self.input_name = None

    def set_target(self, panda, input_name=None):
        self.panda = panda
        self.input_name = input_name

    def add_as_source(self, shape):
        pass

    def set_offset(self, offset):
        pass

    async def load(self, tasks_tree, patch):
        pass

    def apply(self, shape, instance):
        pass

    def apply_shader(self, instance, input_name, texture, texture_lod):
        instance.set_shader_input(input_name, texture)

    def clear(self, patch):
        pass

    def clear_all(self):
        pass

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

    def add_as_source(self, shape):
        pass

    def is_patched(self):
        return False

    def set_offset(self, offset):
        pass

    def texture_name(self, patch):
        return None

    def texture_filename(self, patch):
        return None

    async def load(self, tasks_tree, patch, texture_config=None):
        pass

    def clear(self, patch):
        pass

    def clear_all(self):
        pass

    def can_split(self, patch):
        return False

    def get_texture(self, patch):
        return (None, 0, 0)

    def get_recommended_shape(self):
        return None

class InvalidTextureSource(TextureSource):
    async def load(self, tasks_tree, patch, texture_config=None):
        return (None, 0, 0)

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

    def load(self, tasks_tree, patch, texture_config=None):
        if self.source is None:
            self.create_source()
        return self.source.load(tasks_tree, patch, texture_config)

    def clear(self, patch):
        if self.source is None:
            self.create_source()
        self.source.clear(patch)

    def clear_all(self):
        if self.source is None:
            self.create_source()
        self.source.clear_all()

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

    async def load(self, tasks_tree, patch, texture_config=None):
        if not self.loaded:
            filename=self.context.find_texture(self.filename)
            if filename is not None:
                if settings.sync_texture_load:
                    texture = workers.syncTextureLoader.load_texture(filename)
                else:
                    texture = await workers.asyncTextureLoader.load_texture(filename, None)
                if texture is not None:
                    if texture_config is not None:
                        texture_config.apply(texture)
                    self.texture = texture
                    self.loaded = True
            else:
                print("File", self.filename, "not found")
        return (self.texture, 0, 0)

    def clear(self, patch):
        # A non-patched texture can not be cleared per patch
        pass

    def clear_all(self):
        self.texture = None
        self.loaded = False

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

    async def load(self, tasks_tree, patch):
        return (self.texture, 0, 0)

    def get_texture(self, shape):
        return (self.texture, 0, 0)

class WrapperTexture(TextureBase):
    def __init__(self, texture):
        self.texture = texture
        self.source = TextureSource()

class SimpleTexture(TextureBase):
    def __init__(self, source, srgb=False, offset=0):
        TextureBase.__init__(self)
        if source is not None and not isinstance(source, TextureSource):
            source = AutoTextureSource(source, attribution=None)
        self.srgb = srgb
        self.source = source
        self.offset = offset
        self.tex_matrix= True

    def add_as_source(self, shape):
        self.source.add_as_source(shape)

    def set_offset(self, offset):
        self.offset = offset

    def set_tex_matrix(self, tex_matrix):
        self.tex_matrix = tex_matrix

    def init_texture_stage(self, texture_stage, texture):
        pass

    def configure_instance(self, instance):
        pass

    def create_texture_config(self, shape):
        texture_config = TextureConfiguration()
        texture_config.convert_to_srgb = self.srgb
        if self.source.is_patched():
            texture_config.wrap_u = Texture.WM_clamp
            texture_config.wrap_v = Texture.WM_clamp
        if not self.source.is_patched():
            texture_config.minfilter = Texture.FT_linear_mipmap_linear
            texture_config.magfilter = Texture.FT_linear_mipmap_linear
        else:
            if shape.lod == 0:
                texture_config.minfilter = Texture.FT_linear_mipmap_linear
                texture_config.magfilter = Texture.FT_linear
            else:
                texture_config.minfilter = Texture.FT_linear
                texture_config.magfilter = Texture.FT_linear
        if shape.vanish_borders:
            texture_config.wrap_u = Texture.WM_border_color
            texture_config.border_color = LColor(0, 0, 0, 0)
        return texture_config

    async def load(self, tasks_tree, patch):
        if not self.source.loaded or not self.source.cached:
            if self.source.is_patched():
                self.source.set_offset(self.offset)
            texture_config = self.create_texture_config(patch)
            (texture, texture_size, texture_lod) = await self.source.load(tasks_tree, patch, texture_config=texture_config)

    def apply(self, shape, instance):
        (texture, texture_size, texture_lod) = self.source.get_texture(shape)
        #TODO: not really apply but we need a place to detected the alpha channel
        self.has_alpha_channel = texture.get_format() in (Texture.F_rgba, Texture.F_srgb_alpha, Texture.F_luminance_alpha, Texture.F_sluminance_alpha)
        if texture is None:
            #print("USE DEFAULT", shape.str_id())
            (texture, texture_size, texture_lod) = self.get_default_texture()
        if self.panda:
            self.apply_panda(shape, instance, texture, texture_lod)
        else:
            self.apply_shader(instance, self.input_name, texture, texture_lod)
        self.configure_instance(shape.instance)

    def apply_panda(self, shape, instance, texture, texture_lod):
        texture_stage = TextureStage(shape.str_id() + self.__class__.__name__)
        self.init_texture_stage(texture_stage, texture)
        if self.tex_matrix:
            shape.set_texture_to_lod(self, texture_stage, texture_lod, self.source.is_patched())
        instance.set_texture(texture_stage, texture, 1)

    def clear(self, patch):
        self.source.clear(patch)

    def clear_all(self):
        self.source.clear_all()

    def can_split(self, patch):
        return self.source.can_split(patch)

class DataTexture(TextureBase):
    def __init__(self, source):
        TextureBase.__init__(self)
        if source is not None and not isinstance(source, TextureSource):
            source = AutoTextureSource(source, attribution=None)
        self.source = source

    async def load(self, tasks_tree, patch, texture_config):
        if not self.source.loaded or not self.source.cached:
            await self.source.load(tasks_tree, patch, texture_config=texture_config)

    def apply(self, shape, instance, input_name):
        (texture, texture_size, texture_lod) = self.source.get_texture(shape)
        if texture is None:
            (texture, texture_size, texture_lod) = self.get_default_texture()
        if texture is not None:
            instance.set_shader_input(input_name, texture)

    def clear(self, patch, instance):
        self.source.clear(patch)

    def clear_all(self):
        self.source.clear_all()

    def can_split(self, patch):
        return self.source.can_split(patch)

class VisibleTexture(SimpleTexture):
    def __init__(self, source, tint=None, srgb=None):
        if srgb is None:
            srgb = settings.use_srgb
        SimpleTexture.__init__(self, source, srgb=srgb)
        self.tint_color = tint
        self.transparent = False
        self.has_alpha_channel = False
        self.has_specular_mask = False

    def init_texture_stage(self, texture_stage, texture):
        if self.tint_color is not None:
            if settings.disable_tint: return
            texture_stage.setColor(self.tint_color)
            texture_stage.setCombineRgb(TextureStage.CMModulate,
                                        TextureStage.CSTexture, TextureStage.COSrcColor,
                                        TextureStage.CSConstant, TextureStage.COSrcColor)

    def apply(self, shape, instance):
        SimpleTexture.apply(self, shape, instance)
        if self.source.is_patched() and settings.debug_vt:
            self.debug_borders()


class SurfaceTexture(VisibleTexture):
    category = 'albedo'
    def __init__(self, source, tint=None, srgb=None):
        VisibleTexture.__init__(self, source, tint, srgb=srgb)
        self.check_transparency = False
        self.transparent = False

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
        if not settings.use_srgb:
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

    def create_texture_config(self, shape):
        texture_config = TextureConfiguration(minfilter = Texture.FT_linear_mipmap_linear,
                                              magfilter = Texture.FT_linear_mipmap_linear,
                                              convert_to_srgb = self.srgb)
        return texture_config

    async def load(self, tasks_tree, patch):
        if self.texture is None:
            texture_config = self.create_texture_config(patch)
            if settings.sync_texture_load:
                texture = workers.syncTextureLoader.load_texture_array(self.textures)
            else:
                texture = await workers.asyncTextureLoader.load_texture_array(self.textures)
            if texture is not None:
                self.texture = texture
                texture_config.apply(texture)

    def apply(self, shape, instance):
        self.apply_shader(instance, self.input_name, self.texture, None)

    def clear(self, patch):
        # A non-patched texture can not be cleared per patch
        pass

    def clear_all(self):
        self.texture = None

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

    def find_parent_texture_for(self, patch):
        parent_patch = patch.parent
        while parent_patch is not None and parent_patch.str_id() not in self.map_patch:
            parent_patch = parent_patch.parent
        if parent_patch is not None:
            return self.map_patch[parent_patch.str_id()]

    async def load(self, tasks_tree, patch, texture_config=None):
        texture_info = None
        if not patch.str_id() in self.map_patch:
            tex_name = self.texture_name(patch)
            filename = self.context.find_texture(tex_name)
            alpha_tex_name = self.alpha_texture_name(patch)
            alpha_filename = self.context.find_texture(alpha_tex_name)
            if filename is not None:
                if settings.sync_texture_load:
                    texture = workers.syncTextureLoader.load_texture(filename, alpha_filename)
                else:
                    texture = await workers.asyncTextureLoader.load_texture(filename, alpha_filename)
                if texture is not None:
                    if texture_config is not None:
                        texture_config.apply(texture)
                    texture_info = (texture, self.texture_size, patch.lod)
                    self.map_patch[patch.str_id()] = texture_info
            else:
                print("File", tex_name, "not found")
            if texture_info is None:
                texture_info = self.find_parent_texture_for(patch)
        else:
            texture_info = self.map_patch[patch.str_id()]
        return texture_info

    def clear(self, patch):
        try:
            del self.map_patch[patch.str_id()]
        except KeyError:
            pass

    def clear_all(self):
        self.map_patch = {}

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
