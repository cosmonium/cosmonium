#
#This file is part of Cosmonium.
#
#Copyright (C) 2018-2021 Laurent Deru.
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


from copy import copy


class FramesDB(object):
    def __init__(self):
        self.frames = {}

    def register_frame(self, frame_name, frame):
        self.frames[frame_name] = frame

    def get(self, name):
        if name in self.frames:
            return copy(self.frames[name])
        else:
            print("DB frames:", "Frame", name, "not found")

frames_db = FramesDB()
