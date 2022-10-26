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


from panda3d.core import AsyncFuture
from direct.task import Task

from ..pipeline.pipeline import ProcessPipeline


class GeneratorChain(ProcessPipeline):
    def __init__(self, win=None, engine=None):
        ProcessPipeline.__init__(self, win, engine)
        self.busy = False
        self.queue = []
        taskMgr.add(self.check_generation, 'tex_generation', sort = -10000)

    def check_generation(self, task):
        if len(self.queue) > 0:
            (tid, shader_data, future, controller) = self.queue.pop(0)
            if not future.cancelled():
                future.set_result(self.gather())
            else:
                #print("Dropping result", tid)
                pass
            self.schedule_next()
        return Task.cont

    def schedule_next(self):
        while len(self.queue) > 0:
            (tid, shader_data, future, controller) = self.queue[0]
            if not future.cancelled():
                #print("TRIGGER", tid)
                if controller is not None:
                    if controller.is_waiting():
                        self.trigger(shader_data)
                        break
                    else:
                        # Even though no one is waiting for this data,
                        # we have to set a result on the synchronization future
                        future.set_result(None)
                else:
                    self.trigger(shader_data)
                    break
            #print("Remove cancelled job", tid)
            self.queue.pop(0)
        else:
            self.busy = False

    def schedule(self, tid, shader_data, future, controller):
        self.queue.append((tid, shader_data, future, controller))
        if not self.busy:
            self.schedule_next()
            self.busy = True

    def generate(self, tid, shader_data, controller=None):
        future = AsyncFuture()
        self.schedule(tid, shader_data, future, controller)
        return future

class GeneratorPool(object):
    def __init__(self, chains):
        self.chains = chains

    def add_chain(self, chain):
        self.chains.append(chain)

    def create(self):
        for chain in self.chains:
            chain.create()

    def remove(self):
        for chain in self.chains:
            chain.remove()

    def generate(self, tid, shader_data, controller=None):
        lowest = self.chains[0]
        for chain in self.chains[1:]:
            if len(chain.queue) < len(lowest.queue):
                lowest = chain
        return lowest.generate(tid, shader_data, controller)
