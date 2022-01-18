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


class Pipeline:
    def __init__(self, win=None, engine=None):
        self.stages = {}
        self.ordered_stages = []
        self.win = win
        self.graphics_engine = engine
        if self.win is not None:
            self.base_sort = self.win.get_sort() - 100
        self.win_size = (0, 0)

    def set_win(self, win):
        self.win = win
        self.base_sort = self.win.get_sort() - 100
        for stage in self.stages.values():
            stage.set_win(win)

    def request_slot(self):
        self.base_sort += 1
        return self.base_sort

    def add_stage(self, stage):
        self.stages[stage.name] = stage
        self.ordered_stages.append(stage)
        stage.set_win(self.win)
        stage.set_engine(self.graphics_engine)
        stage.update_win_size(self.win_size)
        for request in stage.requires():
            for prev in reversed(self.ordered_stages[:-1]):
                if request in stage.provides():
                    stage.add_source(request, prev, stage.provides()[request])
                    break
            else:
                print('Missing required stage {request}')

    def get_stage(self, stage_name):
        return self.stages[stage_name]

    def create(self):
        for stage in self.stages.values():
            stage.create(self)

    def remove(self):
        for stage in self.stages.values():
            stage.remove()

    def update_win_size(self, width, height):
        self.size = (width, height)
        for stage in self.stages.values():
            stage.update_win_size(self.size)


class ProcessPipeline(Pipeline):
    def trigger(self, shader_data):
        for stage in self.ordered_stages:
            stage.prepare()
            stage.update_shader_data(shader_data.get(stage.name, {}))
            stage.trigger()

    def gather(self):
        result = {}
        for stage in self.ordered_stages:
            stage.gather(result)
        return result
