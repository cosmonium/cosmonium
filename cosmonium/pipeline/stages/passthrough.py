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


from ...shaders.base import FileShader
from ..stage import SceneStage
from ..target import ScreenTarget, ProcessTarget

class PassthroughStage(SceneStage):

    def provides(self):
        return {'scene': 'color'}

    def requires(self):
        return ['scene']

    def create(self, pipeline):
        if self.screen_stage:
            target = ScreenTarget("passthrough")
        else:
            target = ProcessTarget("passthrough")
            target.add_color_target((pipeline.color_bits, pipeline.color_bits, pipeline.color_bits, 0))
        self.add_target(target)
        target.create(pipeline)
        shader = FileShader(vertex="shaders/stages/default_vertex.glsl",
                            fragment="shaders/stages/passthrough.glsl")
        target.set_shader(shader)
        width = self.win.get_x_size()
        height = self.win.get_y_size()
        target.root.set_shader_input("screen_size", (width, height))
        source = self.sources['scene']
        target.root.set_shader_input('scene', source[0].targets[-1].get_attachment(source[1]))
