#This file is part of Cosmonium.
#
#Copyright (C) 2018-2022 Laurent Deru.
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


try:
    from cosmonium_engine import AnchorBase, UniverseAnchor, StellarAnchor, SystemAnchor, OctreeAnchor
    from cosmonium_engine import CartesianAnchor, CameraAnchor, OriginAnchor, FlatSurfaceAnchor, ObserverAnchor
    FixedStellarAnchor = StellarAnchor
    DynamicStellarAnchor = StellarAnchor
except ImportError as e:
    print("WARNING: Could not load Anchors C implementation, fallback on python implementation")
    print("\t", e)
    from .pyengine.anchors import AnchorBase, UniverseAnchor, StellarAnchor, FixedStellarAnchor, DynamicStellarAnchor, SystemAnchor, OctreeAnchor
    from .pyengine.anchors import CartesianAnchor, CameraAnchor, OriginAnchor, FlatSurfaceAnchor, ObserverAnchor
