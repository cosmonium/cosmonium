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


from panda3d.core import LQuaternion, LQuaterniond
from panda3d.core import LPoint3d, LVector3d
from panda3d.core import NodePath, ModelPool

from ..dircontext import defaultDirContext
from ..mesh import load_model, load_panda_model
from ..parameters import ParametersGroup, AutoUserParameter, UserParameter
#TODO: There shouldn't be a dependency towards astro
from ..astro import units

from .base import Shape


class MeshShape(Shape):
    deferred_instance = True
    def __init__(self, model, offset=None, rotation=None, scale=None, auto_scale_mesh=True, flatten=True, panda=False, attribution=None, context=defaultDirContext):
        Shape.__init__(self)
        self.model = model
        self.attribution = attribution
        self.context = context
        if offset is None:
            offset = LPoint3d()
        self.offset = offset
        if rotation is None:
            rotation = LQuaterniond()
        if scale is None:
            scale = LVector3d(1, 1, 1)
        self.scale_factor = scale
        self.rotation = rotation
        self.auto_scale_mesh = auto_scale_mesh
        self.flatten = flatten
        self.panda = panda
        self.mesh = None
        if auto_scale_mesh and self.scale_factor is not None:
            self.radius = max(*self.scale_factor)
        else:
            self.radius = 0.0

    def update_shape(self):
        self.mesh.set_pos(*self.offset)
        self.mesh.set_quat(LQuaternion(*self.rotation))
        self.mesh.set_scale(*self.scale_factor)

    def get_rotation(self):
        return self.rotation.get_hpr()

    def set_rotation(self, rotation):
        self.rotation.set_hpr(rotation)

    def get_user_parameters(self):
        group = ParametersGroup("Mesh")
        group.add_parameter(AutoUserParameter('Offset', 'offset', self, AutoUserParameter.TYPE_VEC, [-10, 10], nb_components=3))
        group.add_parameter( UserParameter('Rotation', self.set_rotation, self.get_rotation, AutoUserParameter.TYPE_VEC, [-180, 180], nb_components=3))
        if not self.auto_scale_mesh:
            group.add_parameter(AutoUserParameter('Scale', 'scale', self, AutoUserParameter.TYPE_VEC, [0.001, 10], nb_components=3))
        return group

    def is_spherical(self):
        return False

    def load(self):
        if self.panda:
            return load_panda_model(self.model)
        else:
            return load_model(self.model, self.context)

    async def create_instance(self):
        self.instance = NodePath('mesh-holder')
        mesh = await self.load()
        if mesh is None: return None
        #The shape has been removed from the view while the mesh was loaded
        if self.instance is None: return
        self.mesh = mesh
        if self.auto_scale_mesh:
            (l, r) = mesh.getTightBounds()
            major = max(r - l) / 2
            scale_factor = 1.0 / major
            self.scale_factor *= scale_factor
        else:
            self.scale_factor *= units.m
            self.radius = max(*self.scale_factor)
        if self.flatten:
            self.mesh.flattenStrong()
        self.update_shape()
        self.apply_owner()
        self.mesh.reparent_to(self.instance)
        return self.instance

    def remove_instance(self):
        Shape.remove_instance(self)
        if self.mesh is not None:
            ModelPool.release_model(self.mesh.node())
            self.mesh = None
