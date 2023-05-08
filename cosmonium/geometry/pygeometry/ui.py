#
# This file is part of Cosmonium.
#
# Copyright (C) 2018-2023 Laurent Deru.
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

from panda3d.core import CullFaceAttrib, LVector2

from .geometry import empty_geom, empty_node


def FrameGeom(frame_size, border_size=(1, 1), texture=False):
    (path, node) = empty_node('frame')
    (gvw, gcw, gtw, gnw, gtanw, gbiw, prim, geom) = empty_geom(
        'frame', 8 * 4, 8 * 2, normal=False, texture=texture, tanbin=False)
    node.add_geom(geom)

    frame_size = LVector2(*frame_size)
    border_size = LVector2(*border_size)

    # Top left corner
    gvw.add_data3(0, 0, 0)
    gvw.add_data3(border_size[0], 0, 0)
    gvw.add_data3(border_size[0], 0, -border_size[1])
    gvw.add_data3(0, 0, -border_size[1])

    # Top frame
    gvw.add_data3(border_size[0], 0, 0)
    gvw.add_data3(frame_size[0] - border_size[0], 0, 0)
    gvw.add_data3(frame_size[0] - border_size[0], 0, -border_size[1])
    gvw.add_data3(border_size[0], 0, -border_size[1])

    # Top right corner
    gvw.add_data3(frame_size[0] - border_size[0], 0, 0)
    gvw.add_data3(frame_size[0], 0, 0)
    gvw.add_data3(frame_size[0], 0, -border_size[1])
    gvw.add_data3(frame_size[0] - border_size[0], 0, -border_size[1])

    # left frame
    gvw.add_data3(0, 0, -border_size[1])
    gvw.add_data3(border_size[0], 0, -border_size[1])
    gvw.add_data3(border_size[0], 0, -frame_size[1] + border_size[1])
    gvw.add_data3(0, 0, -frame_size[1] + border_size[1])

    # bottom left corner
    gvw.add_data3(0, 0, -frame_size[1] + border_size[1])
    gvw.add_data3(border_size[0], 0, -frame_size[1] + border_size[1])
    gvw.add_data3(border_size[0], 0, -frame_size[1])
    gvw.add_data3(0, 0, -frame_size[1])

    # Right frame
    gvw.add_data3(frame_size[0] - border_size[0], 0, -border_size[1])
    gvw.add_data3(frame_size[0], 0, -border_size[1])
    gvw.add_data3(frame_size[0], 0, -frame_size[1] + border_size[1])
    gvw.add_data3(frame_size[0] - border_size[0], 0, -frame_size[1] + border_size[1])

    # bottom right corner
    gvw.add_data3(frame_size[0] - border_size[0], 0, -frame_size[1] + border_size[1])
    gvw.add_data3(frame_size[0], 0, -frame_size[1] + border_size[1])
    gvw.add_data3(frame_size[0], 0, -frame_size[1])
    gvw.add_data3(frame_size[0] - border_size[0], 0, -frame_size[1])

    # bottom left corner
    gvw.add_data3(border_size[0], 0, -frame_size[1] + border_size[1])
    gvw.add_data3(frame_size[0] - border_size[0], 0, -frame_size[1] + border_size[1])
    gvw.add_data3(frame_size[0] - border_size[0], 0, -frame_size[1])
    gvw.add_data3(border_size[0], 0, -frame_size[1])

    for i in range(8):
        offset = i * 4
        prim.add_vertices(offset + 0, offset + 3, offset + 1)
        prim.add_vertices(offset + 1, offset + 3, offset + 2)

    geom.add_primitive(prim)
    path.set_attrib(CullFaceAttrib.make(CullFaceAttrib.M_cull_none))
    return path
