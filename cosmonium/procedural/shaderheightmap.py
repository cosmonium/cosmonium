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


from .shadernoise import NoiseShader, FloatTarget

from ..pipeline.target import ProcessTarget
from ..pipeline.stage import ProcessStage
from ..pipeline.factory import PipelineFactory
from ..pipeline.generator import GeneratorPool
from ..heightmap import TextureHeightmapBase, HeightmapPatch, PatchedHeightmapBase
from ..textures import TexCoord
from .. import settings

class HeightmapGenerationStage(ProcessStage):
    def __init__(self, coord, width, height, noise_source):
        ProcessStage.__init__(self, "heightmap")
        self.coord = coord
        self.size = (width, height)
        self.noise_source = noise_source

    def provides(self):
        return {'heightmap': 'color'}

    def create_shader(self):
        shader = NoiseShader(coord=self.coord, noise_source=self.noise_source, noise_target=FloatTarget())
        shader.create_and_register_shader(None, None)
        return shader

    def create(self, pipeline):
        target = ProcessTarget(self.name)
        target.set_one_shot(True)
        self.add_target(target)
        target.set_fixed_size(self.size)
        target.add_color_target((32, 0, 0, 0), srgb_colors=False, to_ram=True)
        target.create(pipeline)
        target.set_shader(self.create_shader())

class ShaderHeightmap(TextureHeightmapBase):
    tex_generators = {}

    def __init__(self, name, width, height, height_scale, noise, offset=None, scale=None, coord = TexCoord.Cylindrical, interpolator=None):
        TextureHeightmapBase.__init__(self, name, width, height, height_scale, 1.0, 1.0, interpolator)
        self.noise = noise
        self.offset = offset
        self.scale = scale
        self.coord = coord
        self.shader = None

    def set_noise(self, noise):
        self.noise = noise
        self.shader = None
        self.reset()

    def set_offset(self, offset):
        self.offset = offset
        if self.shader is not None:
            self.shader.offset = offset
        self.reset()

    def set_scale(self, scale):
        self.scale = scale
        if self.shader is not None:
            self.shader.scale = scale
        self.reset()

    def apply(self, shape):
        shape.instance.set_shader_input("heightmap_%s" % self.name, self.texture)

    async def load(self, tasks_tree, patch):
        result = await self.do_load(patch)
        data = result['heightmap']['heightmap']
        self.configure_data(data)

    def do_load(self, shape):
        if not self.tex_id in ShaderHeightmap.tex_generators:
            chain = PipelineFactory.instance().create_process_pipeline()
            stage = HeightmapGenerationStage(self.coord, self.width, self.height, self.noise)
            chain.add_stage(stage)
            chain.create()
            ShaderHeightmapPatch.tex_generators[self.tex_id] = chain
        tex_generator = ShaderHeightmap.tex_generators[self.tex_id]
        if self.shader is None:
            self.shader = NoiseShader(noise_source=self.noise,
                                      noise_target=FloatTarget(),
                                      coord = self.coord,
                                      offset = self.offset,
                                      scale = self.scale)
            self.shader.create_and_register_shader(None, None)
        return tex_generator.generate(self.shader, 0, self.texture)

class HeightmapPatchGenerator():
    def __init__(self, width, height, function, coord_scale):
        self.width = width
        self.height = height
        self.function = function
        self.coord_scale = coord_scale
        self.generator = None

    def create(self, coord):
        pool = GeneratorPool([])
        for i in range(settings.patch_pool_size):
            chain = PipelineFactory.instance().create_process_pipeline()
            stage = HeightmapGenerationStage(coord, self.width, self.height, self.function)
            chain.add_stage(stage)
            pool.add_chain(chain)
        pool.create()
        self.generator = pool

    def clear_all(self):
        if self.generator is not None:
            self.generator.remove()
            self.generator = None

    async def generate(self, tid, heightmap_patch):
        if self.generator is None:
            self.create(heightmap_patch.patch.coord)
        shader_data = {'heightmap': {'offset': (heightmap_patch.r_x0, heightmap_patch.r_y0, 0.0),
                                     'scale': (heightmap_patch.r_x1 - heightmap_patch.r_x0, heightmap_patch.r_y1 - heightmap_patch.r_y0, 1.0),
                                     'global_coord_scale': self.coord_scale,
                                     'face': heightmap_patch.patch.face
                                    }}
        #print("GEN HM", heightmap_patch.patch.str_id())
        result = await self.generator.generate(tid, shader_data)
        data = result['heightmap'].get('color')
        return data

class ShaderPatchedHeightmap(PatchedHeightmapBase):
    def __init__(self, name, data_source, size, min_height, max_height, height_scale, height_offset, overlap, interpolator=None, filter=None, max_lod=100):
        PatchedHeightmapBase.__init__(self, name, size, min_height, max_height, height_scale, height_offset, overlap, interpolator, filter, max_lod)
        self.data_source = data_source

    def do_create_patch_data(self, patch):
        return ShaderHeightmapPatch(self, patch, self.size, self.size, self.overlap)

    def clear_all(self):
        PatchedHeightmapBase.clear_all(self)
        self.data_source.clear_all()

class ShaderHeightmapPatch(HeightmapPatch):
    def apply(self, instance):
        if self.texture is None:
            # The heightmap is not available yet, use the parent heightmap instead
            self.calc_sub_patch()
        HeightmapPatch.apply(self, instance)

    async def load(self, tasks_tree, patch):
        data = await self.parent.data_source.generate("hm - " + patch.str_id(), self)
        self.configure_data(data)
