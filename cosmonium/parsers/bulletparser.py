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


from panda3d.bullet import BulletCapsuleShape, Z_up


from .yamlparser import TypedYamlParser, YamlModuleParser


class BulletCapsuleShapeYamlParser(YamlModuleParser):

    @classmethod
    def decode(self, data):
        width = data.get('width', .5)
        height = data.get('height', 1.8)
        shape = BulletCapsuleShape(width, height - 2 * width, Z_up)
        return shape


class BulletPhysicsShapeYamlParser(TypedYamlParser):

    parsers = {}
    detect_trivial = True

BulletPhysicsShapeYamlParser.register('capsule', BulletCapsuleShapeYamlParser)
