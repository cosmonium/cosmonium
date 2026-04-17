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

"""Process pipeline stages for procedural texture generation.

:class:`TextureGenerationStage` renders a noise function into an off-screen
color target to produce a procedural texture.
:class:`DetailTextureGenerationStage` composites multiple detail textures
based on terrain height and slope information.
"""

from ...pipeline.stage import ProcessStage
from ...pipeline.target import ProcessTarget
from ..shadernoise import NoiseShader
from ..shaders import DeferredDetailMapShader, TextureDictionaryShaderDataSource


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
