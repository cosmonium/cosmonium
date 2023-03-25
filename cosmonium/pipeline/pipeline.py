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


class Pipeline:
    def __init__(self, win=None, engine=None):
        self.stages = {}
        self.ordered_stages = []
        self.win = win
        self.graphics_engine = engine
        self.base_sort = None
        self.win_size = (0, 0)
        self.update_slots_requested = False
        if self.win is not None:
            self.reset_slots()

    def set_win(self, win):
        assert len(self.ordered_stages) == 0
        self.win = win
        self.reset_slots()

    def reset_slots(self):
        self.base_sort = self.win.get_sort() - 100

    def request_slot(self):
        self.base_sort += 1
        return self.base_sort

    def add_stage(self, stage):
        self.stages[stage.name] = stage
        self.ordered_stages.append(stage)
        stage.init(self.win, self.graphics_engine, self)
        stage.update_win_size(self.win_size)
        for request in stage.requires():
            for previous_stage in reversed(self.ordered_stages[:-1]):
                if request in previous_stage.provides():
                    print("Add source", request, "from", previous_stage.name, "for", stage.name)
                    stage.add_source(request, previous_stage)
                    break
            else:
                print(f'Missing required stage {request}')
        return stage

    def get_stage(self, stage_name):
        return self.stages[stage_name]

    def create(self):
        for stage in self.stages.values():
            stage.create(self)

    def remove(self):
        for stage in self.stages.values():
            stage.remove()

    def request_slots_update(self):
        self.update_slots_requested = True

    def update_slots(self):
        self.reset_slots()
        for stage in self.ordered_stages:
            stage.update_slots()

    def update_win_size(self, width, height):
        self.size = (width, height)
        for stage in self.stages.values():
            stage.update_win_size(self.size)
        if self.update_slots_requested:
            self.update_slots()
            self.update_slots_requested = False


class ProcessPipeline(Pipeline):
    def trigger(self, data):
        for stage in self.ordered_stages:
            stage.prepare(data.get('prepare', {}).get(stage.name, {}))
            stage.update_shader_data(data.get('shader', {}).get(stage.name, {}))
            stage.trigger()

    def gather(self):
        result = {}
        for stage in self.ordered_stages:
            stage.gather(result)
        return result
