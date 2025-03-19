#
# This file is part of Cosmonium.
#
# Copyright (C) 2018-2025 Laurent Deru.
#
# Cosmonium is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Cosmonium is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Cosmonium.  If not, see <https://www.gnu.org/licenses/>.
#


from ..component import CompositeShaderComponent, ShaderComponent


class ShaderDataSource(ShaderComponent):
    def has_source_for(self, source):
        return False

    def get_source_for(self, source, params=None, error=True):
        if error:
            print("Unknown source '%s' requested" % source)
        return ''


class CompositeShaderDataSource(CompositeShaderComponent):
    def __init__(self, sources=None):
        CompositeShaderComponent.__init__(self)
        if sources is not None:
            if isinstance(sources, list):
                for source in sources:
                    self.add_component(source)
            else:
                self.add_component(sources)

    def add_source(self, source):
        self.add_component(source)

    def remove_source(self, source_id):
        self.components = list(filter(lambda source: not source.has_source_for(source_id), self.components))

    def has_source_for(self, source_id):
        for source in self.components:
            if source.has_source_for(source_id):
                return True
        return False

    def get_source_for(self, source_id, params=None, error=True):
        for source in self.components:
            value = source.get_source_for(source_id, params, False)
            if value != '':
                return value
        if error:
            print("Unknown source '%s' requested" % source_id)
        return ''
