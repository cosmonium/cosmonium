#
# This file is part of Cosmonium.
#
# Copyright (C) 2018-2026 Laurent Deru.
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


from ..component import ShaderComponent


class GeometryControl(ShaderComponent):
    """Base class for geometry control components.

    This is ShaderComponent provides the geometry-specific shader code
    to be injected into a GeometryShader.

    Subclasses should override the geometry_* methods to provide their
    specific geometry shader contributions.
    """

    def geometry_layout(self, code):
        pass

    def geometry_uniforms(self, code):
        pass

    def geometry_inputs(self, code):
        pass

    def geometry_outputs(self, code):
        pass

    def geometry_extra(self, code):
        pass

    def geometry_shader(self, code):
        pass
