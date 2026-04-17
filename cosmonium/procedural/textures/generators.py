#
# This file is part of Cosmonium.
#
# Copyright (C) 2018-2026 Laurent Deru.
#
# Cosmonium is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Cosmonium is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Cosmonium.  If not, see <https://www.gnu.org/licenses/>.
#

"""Procedural texture generators.

:class:`NoiseTextureGenerator` wraps a :class:`~.stages.TextureGenerationStage`
inside a single process pipeline to produce noise-based textures.
:class:`DetailMapTextureGenerator` maintains a pool of pipelines, each
containing a :class:`~.stages.DetailTextureGenerationStage`, for parallel
per-patch detail-map generation.
"""

import logging

from direct.showbase.ShowBaseGlobal import globalClock
from direct.task.Task import shield

from ... import settings
from ...pipeline.factory import PipelineFactory
from ...pipeline.generator import GeneratorPool
from .stages import DetailTextureGenerationStage, TextureGenerationStage

logger = logging.getLogger("textures")


class NoiseTextureGenerator:
    """Generator that produces procedural textures from noise functions.

    Wraps a ``TextureGenerationStage`` inside a single process pipeline.
    The pipeline is created lazily on the first call to ``generate`` and
    reused for subsequent calls.
    """

    def __init__(self, size, noise, target, alpha=False, srgb=False):
        """Initialize the noise texture generator.

        Args:
            size: Square texture size in pixels (width and height).
            noise: Noise source definition for the shader.
            target: Noise target definition for the shader.
            alpha: Whether the output texture includes an alpha channel.
            srgb: Whether the output texture uses sRGB color space.
        """
        self.texture_size = size
        self.noise = noise
        self.target = target
        self.alpha = alpha
        self.srgb = srgb
        self.tex_generator = None

    def add_as_source(self, shape):
        pass

    def create(self, coord):
        """Create the process pipeline with a texture generation stage.

        Args:
            coord: Coordinate system used for noise evaluation.
        """
        self.tex_generator = PipelineFactory.instance().create_process_pipeline()
        self.texture_stage = TextureGenerationStage(
            coord,
            self.texture_size,
            self.texture_size,
            self.noise,
            self.target,
            alpha=self.alpha,
            srgb=self.srgb,
        )
        self.tex_generator.add_stage(self.texture_stage)
        self.tex_generator.create()

    def clear_all(self):
        """Remove and release the process pipeline and its resources."""
        if self.tex_generator is not None:
            self.tex_generator.remove()
            self.tex_generator = None

    async def generate(self, tasks_tree, shape, patch, texture_config):
        """Generate a procedural texture asynchronously.

        Creates the pipeline on first invocation if it does not yet exist.

        Args:
            tasks_tree: Task tree for managing asynchronous dependencies.
            shape: The shape object that owns the texture.
            patch: The patch to generate for, or None for the whole surface.
            texture_config: Configuration for the output color texture.

        Returns:
            The generated texture.
        """
        if self.tex_generator is None:
            # TODO: This condition is needed for unpatched procedural ring, to be corrected
            self.create(patch.coord if patch else shape.coord)
        data = {'prepare': {'texture': {'color': texture_config}}, 'shader': {}}
        self.texture_stage.configure_data(data, shape, patch)
        if settings.debug_tex_loading:
            logger.debug(f"Generating texture for {patch.str_id()}")
        result = await self.tex_generator.generate(tasks_tree, data)
        texture = result[self.texture_stage.name].get('color')
        return texture


class DetailMapTextureGenerator:
    """Generator that produces detail map textures from heightmap data.

    Maintains a ``GeneratorPool`` of process pipelines, each containing a
    ``DetailTextureGenerationStage``, to allow parallel generation of detail
    maps for multiple patches. The pool is created lazily on first use.
    """

    def __init__(self, size, heightmap, texture_control, texture_source):
        """Initialize the detail map texture generator.

        Args:
            size: Square texture size in pixels (width and height).
            heightmap: Heightmap data source for terrain sampling.
            texture_control: Controls detail texture selection and blending.
            texture_source: Source providing the detail texture dictionary.
        """
        self.texture_size = size
        self.heightmap = heightmap
        self.texture_control = texture_control
        self.texture_source = texture_source
        self.tex_generator = None
        self.texture_stage = None

    def add_as_source(self, shape):
        """Register the texture source on the given shape.

        Args:
            shape: The shape to add the texture source to.
        """
        shape.add_source(self.texture_source)

    def create(self):
        """Create the generator pool with multiple process pipelines.

        The pool size is determined by ``settings.patch_pool_size``.
        """
        self.tex_generator = GeneratorPool([])
        for i in range(settings.patch_pool_size):
            chain = PipelineFactory.instance().create_process_pipeline()
            self.texture_stage = DetailTextureGenerationStage(
                self.texture_size,
                self.texture_size,
                self.heightmap,
                self.texture_control,
                self.texture_source,
            )
            chain.add_stage(self.texture_stage)
            self.tex_generator.add_chain(chain)
        self.tex_generator.create()

    def clear_all(self):
        """Remove and release the generator pool and its resources."""
        if self.tex_generator is not None:
            self.tex_generator.remove()
            self.tex_generator = None

    async def generate(self, tasks_tree, shape, patch, texture_config):
        """Generate a detail map texture asynchronously.

        Creates the generator pool on first invocation. Waits for the
        texture source to finish loading and for any dependent heightmap
        sources before rendering.

        Args:
            tasks_tree: Task tree for managing asynchronous dependencies.
            shape: The shape object that owns the texture.
            patch: The patch to generate the detail map for.
            texture_config: Configuration for the output color texture.

        Returns:
            The generated texture.
        """
        if self.tex_generator is None:
            self.create()
        if not self.texture_source.loaded:
            await shield(self.texture_source.task)
        data = {'prepare': {'texture': {'color': texture_config}}, 'shader': {}}
        for source_name in self.texture_control.get_sources_names():
            if source_name in tasks_tree.named_tasks:
                await tasks_tree.named_tasks[source_name]
        self.texture_stage.configure_data(data, shape, patch)
        if settings.debug_tex_loading:
            logger.debug(f"{globalClock.get_frame_count()} Generating detail map texture for {patch.str_id()}")
        result = await self.tex_generator.generate("tex - " + patch.str_id(), data)
        texture = result[self.texture_stage.name].get('color')
        texture.set_name("tex - " + patch.str_id())
        if settings.debug_tex_loading:
            logger.debug(f"{globalClock.get_frame_count()} Detail map texture generated for {patch.str_id()}")
        return texture
