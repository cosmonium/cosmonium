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


from panda3d.core import CollisionCapsule


from .yamlparser import TypedYamlParser, YamlModuleParser


class CollisionCapsuleShapeYamlParser(YamlModuleParser):

    @classmethod
    def decode(self, data):
        width = data.get('width', .5)
        height = data.get('height', 1.8)
        shape = CollisionCapsule(0, 0, height * 0.1, 0, 0, height, width)
        return shape


class CollisionShapeYamlParser(TypedYamlParser):

    parsers = {}
    detect_trivial = True

CollisionShapeYamlParser.register('capsule', CollisionCapsuleShapeYamlParser)
