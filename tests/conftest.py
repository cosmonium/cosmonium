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


"""
Pytest configuration file for Cosmonium tests.

This file provides global fixtures for testing.
"""

import os
import sys

import pytest


# Add lib/ directory to import path to be able to load the c++ libraries
# Temporarily disabled as some tests fails with C++ library
# sys.path.insert(1, os.path.join(os.path.dirname(__file__),'../lib'))

# Add third-party/ directory to import path to be able to load the external libraries
sys.path.insert(1, os.path.join(os.path.dirname(__file__), '../third-party'))

# ============================================================================
# Fixtures copied from Panda3D test infrastructure to perform GLSL tests
# ============================================================================


@pytest.fixture(scope='session')
def graphics_pipe():
    from panda3d.core import GraphicsPipeSelection

    pipe = GraphicsPipeSelection.get_global_ptr().make_default_pipe()

    if pipe is None or not pipe.is_valid():
        pytest.skip("GraphicsPipe is invalid")

    yield pipe


@pytest.fixture(scope='session')
def graphics_engine():
    from panda3d.core import GraphicsEngine

    engine = GraphicsEngine.get_global_ptr()
    yield engine

    # This causes GraphicsEngine to also terminate the render threads.
    engine.remove_all_windows()


@pytest.fixture(scope='module')
def gsg(graphics_pipe, graphics_engine):
    "Returns a windowless GSG that can be used for offscreen rendering."
    from panda3d.core import GraphicsPipe, FrameBufferProperties, WindowProperties

    fbprops = FrameBufferProperties()
    fbprops.force_hardware = True

    buffer = graphics_engine.make_output(
        graphics_pipe, 'buffer', 0, fbprops, WindowProperties.size(32, 32), GraphicsPipe.BF_refuse_window
    )
    graphics_engine.open_windows()

    if buffer is None:
        pytest.skip("GraphicsPipe cannot make offscreen buffers")

    yield buffer.gsg

    if buffer is not None:
        graphics_engine.remove_window(buffer)
