from __future__ import print_function
from __future__ import absolute_import

from panda3d.core import  Material, TextureStage, Texture, GeomNode
from panda3d.core import TransparencyAttrib

from .textures import TextureBase, SurfaceTexture, TransparentTexture, NightTexture, NormalMapTexture, SpecularMapTexture, BumpMapTexture
from .textures import AutoTextureSource
from .utils import TransparencyBlend
from .dircontext import defaultDirContext

from . import settings

class AppearanceBase:
    def __init__(self):
        self.tex_transform = False
        self.nb_textures = 0
        self.texture_index = 0
        self.normal_map_index = 0
        self.bump_map_index = 0
        self.specular_map_index = 0
        self.night_texture_index = 0
        self.texture = None
        self.normal_map = None
        self.bump_map = None
        self.specular_map = None
        self.night_texture = None
        self.has_specular_mask = False
        self.normal_map_tangent_space = False
        self.specularColor = None
        self.transparency = False
        self.transparency_level = 0.0
        self.transparency_blend = TransparencyBlend.TB_None
        self.has_vertex_color = False
        self.has_attribute_color = False
        self.has_material = False
        self.shadow = None
        self.roughness = 0.0
        self.backlit = 0.0
        self.attribution = None

    def bake(self):
        pass

    def apply_textures(self, patch):
        pass

    def apply_patch(self, patch, owner):
        pass

    def apply(self, shape, owner):
        pass

    def update_lod(self, nodepath, apparent_radius, distance_to_obs, pixel_size):
        pass

class Appearance(AppearanceBase):
    JOB_TEXTURE_LOAD = 0x0001
    def __init__(self,
                 emissionColor=None,
                 diffuseColor=None,
                 ambientColor=None,
                 specularColor=None,
                 shininess=1.0,
                 transparency=False,
                 transparency_level=0.0,
                 transparency_blend=TransparencyBlend.TB_Alpha,
                 texture=None,
                 normalMap=None,
                 specularMap=None,
                 bumpMap=None,
                 bump_height = 10.0,
                 night_texture=None,
                 tint=None,
                 srgb=None):
        AppearanceBase.__init__(self)
        self.emissionColor = emissionColor
        self.diffuseColor = diffuseColor
        self.ambientColor = ambientColor
        self.specularColor = specularColor
        self.shininess = shininess
        if srgb is None:
            srgb = settings.use_srgb
        self.srgb = srgb
        if texture is not None:
            self.set_texture(texture, tint, transparency, transparency_level, transparency_blend)
        if night_texture is not None:
            self.set_night_texture(night_texture, tint)
        self.set_normal_map(normalMap)
        self.set_specular_map(specularMap)
        self.set_bump_map(bumpMap, bump_height)
        self.shadow = None
        self.normal_map_tangent_space = True
        self.nb_textures = 0
        self.nb_textures_coord = 0
        self.texture_index = 0
        self.normal_map_index = 0
        self.bump_map_index = 0
        self.specular_map_index = 0
        self.night_texture_index = 0
        self.has_specular_mask = False
        self.tex_transform = True
        self.has_vertex_color = False
        self.has_attribute_color = False
        self.has_material = True

    def set_roughness(self, roughness):
        self.roughness = roughness

    def set_backlit(self, backlit):
        self.backlit = backlit

    def check_specular_mask(self):
        if self.texture is not None and self.specularColor is not None:
            self.texture.check_specular_mask = True

    def check_transparency(self):
        if self.texture is not None:
            self.texture.check_transparency = True

    def set_shadow(self, shadow):
        self.shadow = shadow

    def bake(self):
        self.material=Material()
        if self.emissionColor != None:
            self.material.setEmission(self.emissionColor)
        if self.diffuseColor != None:
            self.material.setDiffuse(self.diffuseColor)
        if self.ambientColor != None:
            self.material.setAmbient(self.ambientColor)
        if self.specularColor != None:
            self.material.setSpecular(self.specularColor)
        if self.shininess != None:
            self.material.setShininess(self.shininess)
        self.check_specular_mask()
        self.calc_indexes()

    def set_texture(self, texture, tint=None, transparency=False, transparency_level=0.0, transparency_blend=TransparencyBlend.TB_Alpha, offset=0, context=defaultDirContext):
        if texture is not None and not isinstance(texture, TextureBase):
            if transparency:
                texture = TransparentTexture(AutoTextureSource(texture, None, context), tint, level=transparency_level, blend=transparency_blend, srgb=self.srgb)
            else:
                texture = SurfaceTexture(AutoTextureSource(texture, None, context), tint, srgb=self.srgb)
        self.texture = texture
        self.transparency = transparency
        self.transparency_level = transparency_level
        self.transparency_blend = transparency_blend
        self.tint = tint
        texture.set_offset(offset)

    def set_night_texture(self, night_texture, tint=None, context=defaultDirContext):
        if night_texture is not None and not isinstance(night_texture, TextureBase):
            night_texture = NightTexture(AutoTextureSource(night_texture, None, context), tint, srgb=self.srgb)
        self.night_texture = night_texture

    def set_normal_map(self, normal_map, context=defaultDirContext):
        if normal_map is not None and not isinstance(normal_map, TextureBase):
            normal_map = NormalMapTexture(AutoTextureSource(normal_map, None, context))
        self.normal_map = normal_map

    def set_specular_map(self, specular_map, context=defaultDirContext):
        if specular_map is not None and not isinstance(specular_map, TextureBase):
            specular_map = SpecularMapTexture(AutoTextureSource(specular_map, None, context))
        self.specular_map = specular_map

    def set_bump_map(self, bump_map, bump_height, context=defaultDirContext):
        if bump_map is not None and not isinstance(bump_map, TextureBase):
            bump_map = BumpMapTexture(AutoTextureSource(bump_map, None, context))
        self.bump_map = bump_map
        self.bump_height = bump_height

    def calc_indexes(self):
        self.nb_textures = 0
        self.nb_textures_coord = 0
        if self.texture is not None:
            self.texture_index = self.nb_textures
            self.nb_textures += 1
        if self.normal_map is not None:
            self.normal_map_index = self.nb_textures
            self.nb_textures += 1
        if self.bump_map is not None:
            self.bump_map_index = self.nb_textures
            self.nb_textures += 1
        if self.specularColor is not None and self.specular_map is not None:
            self.specular_map_index = self.nb_textures
            self.nb_textures += 1
        if self.night_texture is not None:
            self.night_texture_index = self.nb_textures
            self.nb_textures += 1
        if self.nb_textures > 0:
            self.nb_textures_coord = 1

    def texture_loaded_cb(self, texture, patch, owner):
        shape = owner.shape
        if self.texture is not None and self.texture.check_specular_mask:
            self.has_specular_mask = self.texture.has_specular_mask
            self.texture.check_specular_mask = False
        if shape.patchable:
            #print("CB", patch.str_id(), '-', patch.jobs_pending)
            owner.jobs_done_cb(patch)
        else:
            #print("CB", shape, '-', shape.jobs_pending)
            owner.jobs_done_cb(None)

    def load_textures(self, shape, owner):
        if self.texture:
            self.texture.load(shape, self.texture_loaded_cb, (shape, owner))
        if self.normal_map:
            self.normal_map.load(shape, self.texture_loaded_cb, (shape, owner))
        if self.bump_map:
            self.bump_map.load(shape, self.texture_loaded_cb, (shape, owner))
        if self.specular_map:
            self.specular_map.load(shape, self.texture_loaded_cb, (shape, owner))
        if self.night_texture:
            self.night_texture.load(shape, self.texture_loaded_cb, (shape, owner))

    def apply_textures(self, patch):
        patch.instance.clearTexture()
        if self.texture:
            self.has_specular_mask = self.texture.has_specular_mask
            self.texture.apply(patch)
        if self.normal_map:
            self.normal_map.apply(patch)
        if self.bump_map:
            self.bump_map.apply(patch)
        if self.specularColor is not None and self.specular_map is not None:
            self.specular_map.apply(patch)
        if self.night_texture:
            self.night_texture.apply(patch)

    def apply_patch(self, patch, owner):
        if (patch.jobs & Appearance.JOB_TEXTURE_LOAD) == 0:
            #print("APPLY", patch.str_id())
            if self.nb_textures > 0:
                patch.jobs |= Appearance.JOB_TEXTURE_LOAD
                patch.jobs_pending += self.nb_textures
                self.load_textures(patch, owner)

    def apply(self, shape, owner):
        #Override any material present on the shape (use ModelAppearance to keep it)
        shape.instance.setMaterial(self.material, 1)
        if shape.patchable: return
        if (shape.jobs & Appearance.JOB_TEXTURE_LOAD) == 0:
            #print("APPLY", shape, self.nb_textures)
            if self.nb_textures > 0:
                shape.jobs |= Appearance.JOB_TEXTURE_LOAD
                shape.jobs_pending += self.nb_textures
                self.load_textures(shape, owner)

class ModelAppearance(AppearanceBase):
    def __init__(self, srgb=None, vertex_color=False, attribute_color=False):
        AppearanceBase.__init__(self)
        self.shadow = None
        self.specularColor = None
        self.tex_transform = False
        if srgb is None:
            srgb = settings.use_srgb
        self.srgb = srgb
        #TODO: Should be inferred from model
        self.has_vertex_color = vertex_color
        self.has_attribute_color = attribute_color
        self.has_material = False
        self.offsets = None
        #TODO: This should be factored out...
        self.normal_map_tangent_space = True
        self.nb_textures = 0
        self.nb_textures_coord = 0
        self.texture = None
        self.texture_index = 0
        self.normal_map = None
        self.normal_map_index = 0
        self.bump_map = None
        self.bump_map_index = 0
        self.specular_map = None
        self.specular_map_index = 0
        self.night_texture = None
        self.night_texture_index = 0
        self.has_specular_mask = False
        self.transparency = False
        self.transparency_blend = TransparencyBlend.TB_None

    def set_shadow(self, shadow):
        self.shadow = shadow

    def scan_model(self, instance):
        stages = instance.findAllTextureStages()
        stages.sort()
        #TODO: We assume all the geom have the same texture stage (which is obviously wrong)
        #Should be done like transparency for all the geoms and create a shader per geom...
        has_surface = False
        has_normal = False
        for stage in stages:
            tex = instance.find_texture(stage)
            if tex:
                mode = stage.get_mode()
                if mode in (TextureStage.M_modulate, TextureStage.M_modulate_glow, TextureStage.M_modulate_gloss):
                    if not has_surface:
                        self.texture = tex
                        self.texture_index = self.nb_textures
                        self.has_specular_mask = mode == TextureStage.M_modulate_gloss
                        if self.srgb:
                            tex_format = self.texture.getFormat()
                            if tex_format == Texture.F_rgb:
                                self.texture.set_format(Texture.F_srgb)
                            elif tex_format == Texture.F_rgba:
                                self.texture.set_format(Texture.F_srgb_alpha)
                        self.nb_textures += 1
                        has_surface = True
                elif mode in (TextureStage.M_normal, TextureStage.M_normal_height, TextureStage.M_normal_gloss):
                    if not has_normal:
                        self.normal_map = tex
                        self.normal_map_index = self.nb_textures
                        self.nb_textures += 1
                        has_normal = True
                else:
                    print("Unsupported mode %d" % mode)
        transparency_mode = TransparencyAttrib.M_none
        for np in instance.find_all_matches('**'):
            if np.has_transparency():
                if transparency_mode != TransparencyAttrib.M_none:
                    print("Overriding transparency config")
                transparency_mode = np.get_transparency()
            node = np.node()
            attrib = node.get_attrib(TransparencyAttrib)
            if attrib is not None:
                transparency_mode = attrib.get_mode()
            if isinstance(node, GeomNode):
                for state in node.get_geom_states():
                    attrib = state.get_attrib(TransparencyAttrib)
                    if attrib is not None:
                        transparency_mode = attrib.get_mode()
        if transparency_mode == TransparencyAttrib.M_none:
            self.transparency = False
            self.transparency_blend = TransparencyBlend.TB_None
        elif transparency_mode == TransparencyAttrib.M_alpha:
            self.transparency = True
            self.transparency_level = 0.0
            self.transparency_blend = TransparencyBlend.TB_Alpha
        elif transparency_mode == TransparencyAttrib.M_premultiplied_alpha:
            self.transparency = True
            self.transparency_level = 0.0
            self.transparency_blend = TransparencyBlend.TB_PremultipliedAlpha
        elif transparency_mode == TransparencyAttrib.M_binary:
            self.transparency = True
            self.transparency_level = 0.5
            self.transparency_blend = TransparencyBlend.TB_None
        else:
            print("Unsupported transparency mode", transparency_mode)
            #Activate transparency anyway
            self.transparency = True
            self.transparency_level = 0.0
            self.transparency_blend = TransparencyBlend.TB_Alpha
        self.nb_textures_coord = 1

    def apply(self, shape, owner):
        self.scan_model(shape.instance)
