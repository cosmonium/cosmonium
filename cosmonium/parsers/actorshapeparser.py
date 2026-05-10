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


from panda3d.core import LQuaterniond, LVector3d

from ..shapes.actor import ActorShape
from .schemas.actor import ActorShapeConfig
from .yamlparser import YamlModuleParser


class ActorShapeYamlParser(YamlModuleParser):

    @classmethod
    def decode(cls, data):
        if isinstance(data, str):
            data = {'model': data}
        config = ActorShapeConfig.model_validate(data)
        auto_scale_mesh = config.auto_scale
        scale = None if auto_scale_mesh else config.scale
        offset = config.offset if config.offset is not None else LVector3d()
        if isinstance(scale, (int, float)):
            scale = LVector3d(scale)
        elif isinstance(scale, list):
            scale = LVector3d(*scale)
        rotation_data = config.rotation
        if rotation_data is not None:
            if len(rotation_data) == 3:
                rotation = LQuaterniond()
                rotation.set_hpr(LVector3d(*rotation_data))
            else:
                rotation = LQuaterniond(*rotation_data)
        else:
            rotation = None
        shape = ActorShape(
            config.model,
            config.animations,
            offset,
            rotation,
            scale,
            auto_scale_mesh,
            config.auto_center,
            config.flatten,
            config.panda,
            context=YamlModuleParser.context,
        )
        if config.attribution:
            shape.set_attribution(config.attribution)
        return shape, {}
