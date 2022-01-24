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


from direct.actor.Actor import Actor

from .mesh import MeshShape
from ..dircontext import defaultDirContext

class ActorShape(MeshShape):
    def __init__(self, model, animations, offset=None, rotation=None, scale=None, auto_scale_mesh=True, flatten=True, attribution=None, context=defaultDirContext):
        MeshShape.__init__(self, model, offset, rotation, scale, auto_scale_mesh, flatten, True, attribution, context)
        self.animations = animations

    async def load(self):
        return Actor(self.model, self.animations)

    def stop(self, animName=None, partName=None):
        if self.mesh is not None:
            self.mesh.stop(animName, partName)

    def play(self, animName, partName=None, fromFrame=None, toFrame=None):
        if self.mesh is not None:
            self.mesh.play(animName, partName, fromFrame, toFrame)

    def loop(self, animName, restart=1, partName=None, fromFrame=None, toFrame=None):
        if self.mesh is not None:
            self.mesh.loop(animName, restart, partName, fromFrame, toFrame)

    def pingpong(self, animName, restart=1, partName=None, fromFrame=None, toFrame=None):
        if self.mesh is not None:
            self.mesh.pingpong(animName, restart, partName, fromFrame, toFrame)

    def pose(self, animName, frame, partName=None, lodName=None):
        if self.mesh is not None:
            self.mesh.pose(animName, frame, partName, lodName)
