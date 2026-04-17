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

"""Procedural texture generation framework using GPU shader pipelines.

This module provides pipeline stages and generators for creating textures
procedurally via noise-based shaders and detail map composition. It supports
both single-shot texture generation for non-patched bodies and per-patch
level-of-detail generation for patched terrain surfaces. Textures are
rendered off-screen using process pipelines.
"""

import logging
from direct.showbase.ShowBaseGlobal import globalClock
from direct.task.Task import shield

from .shaders import DeferredDetailMapShader, TextureDictionaryShaderDataSource
from .shadernoise import NoiseShader

from ..pipeline.target import ProcessTarget
from ..pipeline.stage import ProcessStage
from ..pipeline.factory import PipelineFactory
from ..pipeline.generator import GeneratorPool
from ..textures import TextureSource
from .. import settings


logger = logging.getLogger("textures")


class TextureGenerationStage(ProcessStage):
    """Pipeline stage that generates a texture from a noise shader.

    Renders a noise function into an off-screen color target to produce a
    procedural texture. Supports configurable coordinate systems, alpha
    channels, and sRGB output. Patch offset and scale are passed as shader
    uniforms so the same stage can render any patch region.
    """

    def __init__(self, coord, width, height, noise_source, noise_target, alpha, srgb):
        """Initialize the texture generation stage.

        Args:
            coord: Coordinate system used for noise evaluation.
            width: Width of the output texture in pixels.
            height: Height of the output texture in pixels.
            noise_source: Noise source definition for the shader.
            noise_target: Noise target definition for the shader.
            alpha: Whether the output texture includes an alpha channel.
            srgb: Whether the output texture uses sRGB color space.
        """
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
        """Create and register the noise shader for this stage.

        Returns:
            NoiseShader: The compiled noise shader instance.
        """
        shader = NoiseShader(
            self.size,
            coord=self.coord,
            noise_source=self.noise_source,
            noise_target=self.noise_target,
        )
        shader.create_and_register_shader(None, None)
        return shader

    def create(self, pipeline):
        """Create the render target and configure the shader for this stage.

        Args:
            pipeline: The process pipeline that owns this stage.
        """
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
        """Configure shader data with patch offset, scale, face, and LOD.

        Args:
            data: Mutable data dictionary passed through the pipeline.
            shape: The shape object that owns the texture.
            patch: The patch to generate for, or None for the whole surface.
        """
        if patch is not None:
            data['shader'][self.name] = {
                'offset': (patch.x0, patch.y0, 0.0),
                'scale': (patch.x1 - patch.x0, patch.y1 - patch.y0, 1.0),
                'face': patch.face,
                'lod': patch.lod,
            }
        else:
            data['shader'][self.name] = {
                'offset': (0.0, 0.0, 0.0),
                'scale': (1.0, 1.0, 1.0),
                'face': -1,
                'lod': 0,
            }


class DetailTextureGenerationStage(ProcessStage):
    """Pipeline stage that generates a detail map from a heightmap.

    Composites multiple detail textures based on terrain height and slope
    information using a deferred detail map shader. The texture control
    and texture source define which detail textures are blended together.
    """

    def __init__(self, width, height, heightmap, texture_control, texture_source):
        """Initialize the detail texture generation stage.

        Args:
            width: Width of the output texture in pixels.
            height: Height of the output texture in pixels.
            heightmap: Heightmap data source for terrain sampling.
            texture_control: Controls detail texture selection and blending.
            texture_source: Source providing the detail texture dictionary.
        """
        ProcessStage.__init__(self, "texture")
        self.size = (width, height)
        self.heightmap = heightmap
        self.texture_control = texture_control
        self.texture_source = texture_source

    def create_shader(self):
        """Create and register the deferred detail map shader.

        Returns:
            DeferredDetailMapShader: The compiled detail map shader instance.
        """
        shader = DeferredDetailMapShader(self.heightmap, self.texture_control, self.texture_source)
        shader.data_source.add_source(TextureDictionaryShaderDataSource(self.texture_source))
        shader.data_source.add_source(self.heightmap.get_data_source(False))
        shader.create_and_register_shader(None, None)
        return shader

    def create(self, pipeline):
        """Create the render target and configure the detail map shader.

        Args:
            pipeline: The process pipeline that owns this stage.
        """
        target = ProcessTarget(self.name)
        target.set_one_shot(True)
        self.add_target(target)
        target.set_fixed_size(self.size)
        target.add_color_target((8, 8, 8, 0), srgb_colors=False, to_ram=False, config=None)
        target.create(pipeline)
        # TODO: Link is missing
        self.texture_control.create_shader_configuration(self.texture_source)
        target.set_shader(self.create_shader())

    def configure_data(self, data, shape, patch):
        """Configure shader data with shape, patch, and LOD information.

        Args:
            data: Mutable data dictionary passed through the pipeline.
            shape: The shape object that owns the texture.
            patch: The patch to generate the detail map for.
        """
        data['shader'][self.name] = {
            'shape': shape,
            'patch': patch,
            'appearance': None,
            'lod': patch.lod,
        }


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


class ProceduralVirtualTextureSource(TextureSource):
    """Texture source that generates a single procedural texture.

    Produces one texture for the entire surface on first load and caches the
    result. Suitable for non-patched bodies where a single texture covers
    the whole object.
    """

    cached = True
    procedural = True

    def __init__(self, tex_generator, size):
        """Initialize the procedural virtual texture source.

        Args:
            tex_generator: Generator used to produce the procedural texture.
            size: Square texture size in pixels (width and height).
        """
        TextureSource.__init__(self)
        self.texture_size = size
        self.tex_generator = tex_generator

    async def load(self, tasks_tree, shape, texture_config):
        """Load the procedural texture, generating it if not yet cached.

        Args:
            tasks_tree: Task tree for managing asynchronous dependencies.
            shape: The shape object that owns the texture.
            texture_config: Configuration for the output color texture.

        Returns:
            tuple: (texture, texture_size, lod) where lod is always 0.
        """
        if self.texture is None:
            self.texture = await self.tex_generator.generate(tasks_tree, shape, None, texture_config)
        return (self.texture, self.texture_size, 0)

    def get_texture(self, shape, strict=False):
        """Return the cached texture tuple.

        Args:
            shape: The shape requesting the texture.
            strict: Unused; present for interface compatibility.

        Returns:
            tuple: (texture, texture_size, lod) where lod is always 0.
        """
        return (self.texture, self.texture_size, 0)

    def clear_all(self):
        """Release the cached texture and the underlying generator."""
        self.texture = None
        self.tex_generator.clear_all()


class PatchedProceduralVirtualTextureSource(TextureSource):
    """Patched texture source that generates a procedural texture per patch.

    Maintains a cache of generated textures keyed by patch ID. Each patch
    gets its own texture at the appropriate level of detail. When a patch
    texture is not yet available, the nearest ancestor texture is returned
    as a fallback.
    """

    cached = False

    def __init__(self, tex_generator, size):
        """Initialize the patched procedural virtual texture source.

        Args:
            tex_generator: Generator used to produce per-patch textures.
            size: Square texture size in pixels (width and height).
        """
        TextureSource.__init__(self)
        self.texture_size = size
        self.map_patch = {}
        self.tex_generator = tex_generator
        self.procedural = True

    def add_as_source(self, shape):
        """Register the generator's texture source on the given shape.

        Args:
            shape: The shape to add the texture source to.
        """
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
        """Load or generate the texture for a specific patch.

        Returns a cached result if the patch has already been generated,
        otherwise triggers generation and caches the result.

        Args:
            tasks_tree: Task tree for managing asynchronous dependencies.
            patch: The patch to generate the texture for.
            texture_config: Configuration for the output color texture.

        Returns:
            tuple: (texture, texture_size, lod) for the requested patch.
        """
        if settings.debug_tex_loading:
            logger.debug(f"{globalClock.get_frame_count()} Loading texture for {patch.str_id()}")
        texture_info = None
        if not patch.str_id() in self.map_patch:
            texture = await self.tex_generator.generate(tasks_tree, patch.owner, patch, texture_config)
            if settings.debug_tex_loading:
                logger.debug(f"{globalClock.get_frame_count()} Texture ready for {patch.str_id()}")
            texture_info = (texture, self.texture_size, patch.lod)
            self.map_patch[patch.str_id()] = texture_info
        else:
            texture_info = self.map_patch[patch.str_id()]
        return texture_info

    def clear(self, patch):
        """Remove the cached texture for a specific patch.

        Args:
            patch: The patch whose cached texture should be removed.
        """
        try:
            del self.map_patch[patch.str_id()]
        except KeyError:
            pass

    def clear_all(self):
        """Release all cached patch textures and the underlying generator."""
        self.map_patch = {}
        self.tex_generator.clear_all()

    def get_texture(self, patch, strict=False):
        """Retrieve the texture for a patch, with optional ancestor fallback.

        Args:
            patch: The patch to retrieve the texture for.
            strict: If True, return None when the exact patch texture is
                missing. If False, walk up the parent chain to find the
                nearest available ancestor texture.

        Returns:
            tuple: (texture, texture_size, lod) for the patch or its nearest
                ancestor, or (None, texture_size, lod) if unavailable.
        """
        if patch.str_id() in self.map_patch:
            return self.map_patch[patch.str_id()]
        elif not strict:
            parent_patch = patch.parent
            while parent_patch is not None and parent_patch.str_id() not in self.map_patch:
                parent_patch = parent_patch.parent
            if parent_patch is not None:
                if settings.debug_tex_loading:
                    logger.debug(
                        f"{globalClock.get_frame_count()} Using parent texture for {patch.str_id()},"
                        f" parent: {parent_patch.str_id()}"
                    )
                return self.map_patch[parent_patch.str_id()]
            else:
                if settings.debug_tex_loading:
                    logger.debug(f"{globalClock.get_frame_count()} No texture found for {patch.str_id()}")
                return (None, self.texture_size, patch.lod)
        else:
            return (None, self.texture_size, patch.lod)
