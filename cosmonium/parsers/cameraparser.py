#
#This file is part of Cosmonium.
#
#Copyright (C) 2018-2024 Laurent Deru.
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


from panda3d.core import LVector3d

from ..camera import FixedCameraController, SurfaceFollowCameraController

from .yamlparser import TypedYamlParser, YamlModuleParser


class SurfaceFollowCameraControllerYamlParser(YamlModuleParser):

    @classmethod
    def decode(self, data):
        distance = data.get('distance', 5)
        max_ = data.get('max', 1.5)
        camera_controller = SurfaceFollowCameraController()
        camera_controller.set_camera_hints(distance=distance, max=max_)
        return camera_controller


class FixedCameraControllerYamlParser(YamlModuleParser):

    @classmethod
    def decode(self, data):
        camera_controller = FixedCameraController()
        if 'position' in data:
            position = LVector3d(*data.get('position'))
        else:
            position = LVector3d(0)
        camera_controller.set_camera_hints(position=position)
        return camera_controller


class CameraControllerYamlParser(TypedYamlParser):

    parsers = {}
    detect_trivial = True


CameraControllerYamlParser.register('surface-follow', SurfaceFollowCameraControllerYamlParser)
CameraControllerYamlParser.register('fixed', FixedCameraControllerYamlParser)
