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


from .pipeline import ProcessPipeline
from .generator import GeneratorChain

class PipelineFactory:
    _instance = None

    def __init__(self):
        self.win = base.win
        self.graphics_engine = base.graphics_engine

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = PipelineFactory()
        return cls._instance

    def create_simple_pipeline(self):
        return ProcessPipeline(self.win, self.graphics_engine)

    def create_process_pipeline(self):
        return GeneratorChain(self.win, self.graphics_engine)
