#
# This file is part of Cosmonium.
#
# Copyright (C) 2018-2025 Laurent Deru.
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


from .. import settings
from ..components.elements.clouds import Clouds
from ..patchedshapes.lodcontrol import TextureOrVertexSizeLodControl, VertexSizeLodControl
from ..shaders.rendering import RenderingShader
from .appearancesparser import AppearanceYamlParser
from .schemas.clouds import CloudsConfig
from .shapesparser import ShapeYamlParser
from .yamlparser import YamlModuleParser


class CloudsYamlParser(YamlModuleParser):
    @classmethod
    def decode(cls, data):
        if data is None:
            return None
        config = CloudsConfig.model_validate(data)
        height = float(config.height)
        shape, extra = ShapeYamlParser.decode(config.shape, use_skirt=False)
        appearance = AppearanceYamlParser.decode(config.appearance)
        if shape.patchable:
            if appearance.texture is None or appearance.texture.source.procedural:
                shape.set_lod_control(
                    VertexSizeLodControl(settings.patch_max_vertex_size, density=settings.patch_default_density)
                )
            else:
                shape.set_lod_control(
                    TextureOrVertexSizeLodControl(
                        settings.patch_max_vertex_size,
                        density=settings.patch_default_density,
                    )
                )
        lighting_model = None
        shader = RenderingShader(lighting_model=lighting_model)
        clouds = Clouds(height, appearance, shader, shape)
        return clouds
