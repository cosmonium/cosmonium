#
#This file is part of Cosmonium.
#
#Copyright (C) 2018-2019 Laurent Deru.
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

from __future__ import print_function
from __future__ import absolute_import

class LabelsRenderer(object):
    def __init__(self, context):
        self.context = context
        self.labels = []
        self.old_labels = []

    def reset(self):
        self.old_labels = self.labels
        self.labels = []

    def update(self, observer):
        camera_pos = observer.get_camera_pos()
        camera_rot = observer.get_camera_rot()
        frustum = observer.rel_frustum
        pixel_size = observer.pixel_size
        for body in self.labels:
            if body.label is None:
                body.create_label()
                body.label.check_settings()
            body.label.check_visibility(frustum, pixel_size)
            body.label.check_and_update_instance(camera_pos, camera_rot)
        for body in self.old_labels:
            if body not in self.labels and body.label is not None:
                body.label.remove_instance()
                body.label = None

    def add_label(self, body):
        self.labels.append(body)

