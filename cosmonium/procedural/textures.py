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


from panda3d.core import Texture

from .shaders import DeferredDetailMapShader, TextureDictionaryDataSource
from .shadernoise import NoiseShader

from ..pipeline.target import ProcessTarget
from ..pipeline.stage import ProcessStage
from ..pipeline.factory import PipelineFactory
from ..pipeline.generator import GeneratorPool
from ..textures import TextureConfiguration, TextureSource
from .. import settings

class TextureGenerationStage(ProcessStage):
    def __init__(self, coord, width, height, noise_source, noise_target, alpha, srgb):
        ProcessStage.__init__(self, "texture")
        self.coord = coord
        self.size = (width, height)
        self.noise_source = noise_source
        self.noise_target = noise_target
        self.alpha = alpha
        self.srgb = srgb

    def provides(self):
        return {'texture': 'color'}

    def create_shader(self):
        shader = NoiseShader(coord=self.coord, noise_source=self.noise_source, noise_target=self.noise_target)
        shader.create_and_register_shader(None, None)
        return shader

    def create(self, pipeline):
        target = ProcessTarget(self.name)
        target.set_one_shot(True)
        self.add_target(target)
        target.set_fixed_size(self.size)
        if self.alpha:
            colors = (8, 8, 8, 8)
        else:
            colors = (8, 8, 8, 0)
        target.add_color_target(colors, srgb_colors=self.srgb, to_ram=False, config=None)
        target.create(pipeline)
        target.set_shader(self.create_shader())

    def configure_data(self, data, shape, patch):
        if patch is not None:
            data['shader'][self.name] = {'offset': (patch.x0, patch.y0, 0.0),
                                         'scale': (patch.x1 - patch.x0, patch.y1 - patch.y0, 1.0),
                                         'face': patch.face,
                                         'lod': patch.lod
                                         }
        else:
            data['shader'][self.name] = {'offset': (0.0, 0.0, 0.0),
                                         'scale': (1.0, 1.0, 1.0),
                                         'face': -1,
                                         'lod': 0
                                         }

class DetailTextureGenerationStage(ProcessStage):
    def __init__(self, width, height, heightmap, texture_control, texture_source):
        ProcessStage.__init__(self, "texture")
        self.size = (width, height)
        self.heightmap = heightmap
        self.texture_control = texture_control
        self.texture_source = texture_source

    def create_shader(self):
        shader = DeferredDetailMapShader(self.heightmap, self.texture_control, self.texture_source)
        shader.data_source.add_source(TextureDictionaryDataSource(self.texture_source))
        shader.data_source.add_source(self.heightmap.get_data_source(False))
        shader.create_and_register_shader(None, None)
        return shader

    def create(self, pipeline):
        target = ProcessTarget(self.name)
        target.set_one_shot(True)
        self.add_target(target)
        target.set_fixed_size(self.size)
        target.add_color_target((8, 8, 8, 0), srgb_colors=False, to_ram=False, config=None)
        target.create(pipeline)
        #TODO: Link is missing
        self.texture_control.create_shader_configuration(self.texture_source)
        target.set_shader(self.create_shader())

    def configure_data(self, data, shape, patch):
        data['shader'][self.name] = {'shape': shape,
                                     'patch': patch,
                                     'appearance': None,
                                     'lod': patch.lod
                                     }

class NoiseTextureGenerator():
    def __init__(self, size, noise, target, alpha=False, srgb=False):
        self.texture_size = size
        self.noise = noise
        self.target = target
        self.alpha = alpha
        self.srgb = srgb
        self.tex_generator = None

    def add_as_source(self, shape):
        pass

    def create(self, coord):
        self.tex_generator =  PipelineFactory.instance().create_process_pipeline()
        self.texture_stage = TextureGenerationStage(coord, self.texture_size, self.texture_size,
                                                    self.noise, self.target, alpha=self.alpha, srgb=self.srgb)
        self.tex_generator.add_stage(self.texture_stage)
        self.tex_generator.create()

    def clear_all(self):
        if self.tex_generator is not None:
            self.tex_generator.remove()
            self.tex_generator = None

    async def generate(self, tasks_tree, shape, patch, texture_config):
        if self.tex_generator is None:
            #TODO: This condition is needed for unpatched procedural ring, to be corrected
            self.create(patch.coord if patch else shape.coord)
        data = {'prepare': {'texture': {'color': texture_config}}, 'shader': {}}
        self.texture_stage.configure_data(data, shape, patch)
        #print("GEN", patch.str_id())
        result = await self.tex_generator.generate(tasks_tree, data)
        texture = result[self.texture_stage.name].get('color')
        return texture

class DetailMapTextureGenerator():
    def __init__(self, size, heightmap, texture_control, texture_source):
        self.texture_size = size
        self.heightmap = heightmap
        self.texture_control = texture_control
        self.texture_source = texture_source
        self.tex_generator = None
        self.texture_stage = None

    def add_as_source(self, shape):
        shape.add_source(self.texture_source)

    def create(self):
        self.tex_generator = GeneratorPool([])
        for i in range(settings.patch_pool_size):
            chain = PipelineFactory.instance().create_process_pipeline()
            self.texture_stage = DetailTextureGenerationStage(self.texture_size, self.texture_size, self.heightmap, self.texture_control, self.texture_source)
            chain.add_stage(self.texture_stage)
            self.tex_generator.add_chain(chain)
        self.tex_generator.create()

    def clear_all(self):
        if self.tex_generator is not None:
            self.tex_generator.remove()
            self.tex_generator = None

    async def generate(self, tasks_tree, shape, patch, texture_config):
        if self.tex_generator is None:
            self.create()
        if not self.texture_source.loaded:
            await self.texture_source.task
        data = {'prepare': {'texture': {'color': texture_config}}, 'shader': {}}
        for source_name in self.texture_control.get_sources_names():
            if source_name in tasks_tree.named_tasks:
                await tasks_tree.named_tasks[source_name]
        self.texture_stage.configure_data(data, shape, patch)
        #print(globalClock.get_frame_count(), "*** GEN TEX", patch.str_id())
        result = await self.tex_generator.generate("tex - " + patch.str_id(), data)
        texture = result[self.texture_stage.name].get('color')
        texture.set_name("tex - " + patch.str_id())
        #print(globalClock.get_frame_count(), "*** DONE TEX", patch.str_id())
        return texture

class ProceduralVirtualTextureSource(TextureSource):
    cached = True
    procedural = True
    def __init__(self, tex_generator, size):
        TextureSource.__init__(self)
        self.texture_size = size
        self.tex_generator = tex_generator

    async def load(self, tasks_tree, shape, texture_config):
        if self.texture is None:
            self.texture = await self.tex_generator.generate(tasks_tree, shape, None, texture_config)
        return (self.texture, self.texture_size, 0)

    def get_texture(self, shape, strict=False):
        return (self.texture, self.texture_size, 0)

    def clear_all(self):
        self.texture = None
        self.tex_generator.clear_all()

class PatchedProceduralVirtualTextureSource(TextureSource):
    cached = False
    def __init__(self, tex_generator, size):
        TextureSource.__init__(self)
        self.texture_size = size
        self.map_patch = {}
        self.tex_generator = tex_generator
        self.procedural = True

    def add_as_source(self, shape):
        self.tex_generator.add_as_source(shape)

    def is_patched(self):
        return True

    def child_texture_name(self, patch):
        return None

    def texture_name(self, patch):
        return None

    def can_split(self, patch):
        return True

    async def load(self, tasks_tree, patch, texture_config):
        #print("LOAD TEX", patch.str_id())
        texture_info = None
        if not patch.str_id() in self.map_patch:
            texture = await self.tex_generator.generate(tasks_tree, patch.owner, patch, texture_config)
            #print("READY TEX", patch.str_id())
            texture_info = (texture, self.texture_size, patch.lod)
            self.map_patch[patch.str_id()] = texture_info
        else:
            texture_info = self.map_patch[patch.str_id()]
        return texture_info

    def clear_patch(self, patch):
        try:
            del self.map_patch[patch.str_id()]
        except KeyError:
            pass

    def clear_all(self):
        self.map_patch = {}
        self.tex_generator.clear_all()

    def get_texture(self, patch, strict=False):
        if patch.str_id() in self.map_patch:
            return self.map_patch[patch.str_id()]
        elif not strict:
            parent_patch = patch.parent
            while parent_patch is not None and parent_patch.str_id() not in self.map_patch:
                parent_patch = parent_patch.parent
            if parent_patch is not None:
                #print(globalClock.getFrameCount(), "USE PARENT", patch.str_id(), parent_patch.str_id())
                return self.map_patch[parent_patch.str_id()]
            else:
                #print(globalClock.getFrameCount(), "NONE")
                return (None, self.texture_size, patch.lod)
        else:
            return (None, self.texture_size, patch.lod)
