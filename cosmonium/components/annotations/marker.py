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


from panda3d.core import LPoint3d, LVector3, LVector3d, NodePath, OmniBoundingVolume

from ...foundation import VisibleObject
from ...utils import srgb_to_linear
from ...geometry.marker import build_marker_geom
from ... import settings


class ObjectMarker(VisibleObject):
    """A visual marker placed on a specific celestial object.

    The marker is rendered in the annotation pass as a screen-space geometric
    symbol (diamond, circle, square, etc.) centered on the object, maintaining
    a constant pixel size regardless of distance.  An optional text label can
    accompany the symbol (Not implemented yet).
    """

    default_shown = True
    ignore_light = True
    default_camera_mask = VisibleObject.AnnotationCameraFlag

    def __init__(self, name, marker_source, color, size, symbol, label, occludable):
        """
        Initialize the marker with the given configuration.

        Args:
            name: Unique name for this marker.
            marker_source: The StellarObject (or compatible object) being marked.
            color: RGBA marker color as an LColor (in sRGB space, will be converted to linear).
            size: Nominal marker radius in pixels.
            symbol: One of the MarkerShape enum values.
            label: Optional text to display alongside the marker symbol.
            occludable: When False the marker is drawn on top of all geometry (depth test disabled).
        """
        VisibleObject.__init__(self, name)
        self.marker_source = marker_source
        self.color = color
        self.size = size
        self.symbol = symbol
        self.label_text = label
        self.occludable = occludable
        # The NodePath instance of the marker geometry
        self.marker_instance = None
        # Dummy node used for orientation
        self.look_at = None

    def create_instance(self):
        geom_node = build_marker_geom(self.marker_source.get_ascii_name() + '-marker', self.symbol)

        self.marker_instance = NodePath(geom_node)
        self.marker_instance.setRenderModeThickness(2)
        self.marker_instance.setColor(srgb_to_linear(self.color))
        self.marker_instance.set_depth_write(True)
        if not self.occludable:
            self.marker_instance.set_depth_test(False)

        self.instance = NodePath('marker-holder')
        self.marker_instance.reparentTo(self.instance)
        self.instance.reparentTo(self.scene_anchor.unshifted_instance)
        self.instance_ready = True
        self.instance.node().setBounds(OmniBoundingVolume())
        self.instance.node().setFinal(True)
        self.instance.set_light_off(1)
        self.instance.hide(self.AllCamerasMask)
        self.instance.show(self.default_camera_mask)

        self.look_at = self.instance.attachNewNode("dummy")

    def check_visibility(self, frustum, pixel_size):
        self.visible = self.marker_source.anchor.visible or self.marker_source.anchor.resolved

    def update_instance(self, scene_manager, camera_pos, camera_rot):
        body = self.marker_source
        offset = body.get_bounding_radius()
        position = -camera_rot.xform(LPoint3d(0, offset, 0))
        z_coef = -body.anchor.vector_to_obs.dot(body.context.observer.anchor.camera_vector)
        z_distance = (body.anchor.distance_to_obs - offset) * z_coef
        self.instance.set_pos(*position)
        scale = abs(self.context.observer.pixel_size * self.size * z_distance * settings.ui_scale)
        if scale < 1e-7:
            scale = 1e-7
        self.look_at.set_pos(LVector3(*(camera_rot.xform(LVector3d.forward()))))
        self.marker_instance.look_at(self.look_at, LVector3(), LVector3(*(camera_rot.xform(LVector3d.up()))))
        self.instance.set_scale(scale)
