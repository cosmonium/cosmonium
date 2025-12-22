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


from panda3d.core import CardMaker, NodePath, OmniBoundingVolume

from ..shapes.base import Shape


class BillboardShape(Shape):
    """
    A shape that displays a billboard.
    The actual image displayed by the billboard is set by the associated appeareance object
    """

    def __init__(self):
        """
        Initialize the billboard shape.
        """
        Shape.__init__(self)
        self.card_instance = None

    async def create_instance(self):
        """Create the billboard geometry."""
        self.instance = NodePath("billboard")

        # Create a card for the billboard
        card_maker = CardMaker("billboard-card")
        card_maker.set_frame(-1, 1, -1, 1)
        node = card_maker.generate()
        self.card_instance = self.instance.attach_new_node(node)

        # Make it always face the camera
        self.card_instance.setBillboardPointWorld()

        # Set bounds
        self.instance.node().setBounds(OmniBoundingVolume())
        self.instance.node().setFinal(True)

        return self.instance

    def remove_instance(self) -> None:
        """
        Remove the billboard instance.
        """
        Shape.remove_instance(self)
        self.card_instance = None

    def set_axes(self, axes):
        # Useless method for billboard
        pass
