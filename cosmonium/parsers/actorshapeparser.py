#
#This file is part of Cosmonium.
#
#Copyright (C) 2018-2023 Laurent Deru.
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


from panda3d.core import LVector3d, LQuaterniond

from ..shapes.actor import ActorShape

from .yamlparser import YamlModuleParser


class ActorShapeYamlParser(YamlModuleParser):

    @classmethod
    def decode(self, data):
        if isinstance(data, str):
            data = {'model': data}
        model = data.get('model')
        animations = data.get('animations', {})
        panda = data.get('panda', True)
        auto_scale_mesh = data.get('auto-scale', True)
        offset = data.get('offset', None)
        rotation_data = data.get('rotation', None)
        if not auto_scale_mesh:
            scale = data.get('scale', None)
        else:
            scale = None
        if offset is not None:
            offset = LVector3d(*offset)
        if isinstance(scale, (int, float)):
            scale = LVector3d(scale)
        elif isinstance(scale, list):
            scale = LVector3d(*scale)
        if rotation_data is not None:
            if len(rotation_data) == 3:
                rotation = LQuaterniond()
                rotation.set_hpr(LVector3d(*rotation_data))
            else:
                rotation = LQuaterniond(*rotation_data)
        else:
            rotation = None
        flatten = data.get('flatten', True)
        attribution = data.get('attribution', None)
        shape = ActorShape(
            model, animations, offset, rotation, scale, auto_scale_mesh, flatten, panda, attribution,
            context=YamlModuleParser.context)
        return shape, {}
