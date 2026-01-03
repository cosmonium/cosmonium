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


from __future__ import annotations

import math

from panda3d.core import LPoint3

from cosmonium.procedural.primitives.arithmetic import NegNoise, NoiseAdd, NoiseDiv, NoiseMul, NoisePow, NoiseSub
from cosmonium.procedural.primitives.math import AbsNoise, NoiseClamp, NoiseExp, NoiseMax, NoiseMin
from cosmonium.procedural.shadernoise import NoiseSource
from cosmonium.procedural.sources.simple import NoiseCoord, NoiseConst

from ..glsl import run_glsl_test


def run_noise_test(gsg, noise: NoiseSource, inputs: dict, tests: list[str]):
    """"""
    preamble_code = []
    noise.noise_uniforms(preamble_code)
    for name, value in inputs.items():
        input_type = None
        if isinstance(value, LPoint3):
            input_type = 'vec3'
        elif isinstance(value, float):
            input_type = 'float'
        if input_type:
            uniform = f"uniform {input_type} {name};"
            if uniform not in preamble_code:
                preamble_code.append(uniform)
    noise.noise_extra(None, preamble_code)
    noise.noise_func(preamble_code)
    body_code = ["float value = 0;"]
    noise.noise_value(body_code, 'value', 'point')
    body_code += tests
    run_glsl_test(gsg, '\n'.join(body_code), '\n'.join(preamble_code), inputs)


class TestSimpleSources:
    """Test simple source of noise data."""

    def test_coord(self, gsg):
        """Test coordinate noise source."""
        inputs = {'point': LPoint3(1, 2, 3)}
        noise = NoiseCoord("x")
        tests = ['assert(value == 1);']
        run_noise_test(gsg, noise, inputs, tests)

        inputs = {'point': LPoint3(1, 2, 3)}
        noise = NoiseCoord("y")
        tests = ['assert(value == 2);']
        run_noise_test(gsg, noise, inputs, tests)

        inputs = {'point': LPoint3(1, 2, 3)}
        noise = NoiseCoord("z")
        tests = ['assert(value == 3);']
        run_noise_test(gsg, noise, inputs, tests)

    def test_const(self, gsg):
        """Test constant value noise source."""
        noise = NoiseConst(123.456)
        tests = ['assert(value == 123.456);']
        run_noise_test(gsg, noise, {}, tests)

    def test_const_dynamic(self, gsg):
        """Test updatable constant value noise source."""
        noise = NoiseConst(0, dynamic=True)
        inputs = {noise.str_id: 456.789}
        tests = ['assert(value == 456.789);']
        run_noise_test(gsg, noise, inputs, tests)


class TestArithmetic:
    """Test arithmetic operations."""

    def test_neg(self, gsg):
        """Test negation operator."""
        noise = NegNoise(NoiseConst(-1))
        tests = ['assert(value == 1);']
        run_noise_test(gsg, noise, {}, tests)

        noise = NegNoise(NoiseConst(2))
        tests = ['assert(value == -2);']
        run_noise_test(gsg, noise, {}, tests)

    def test_add(self, gsg):
        """Test addition operator."""
        inputs = {'point': LPoint3(1, 2, 3)}
        noise = NoiseAdd([NoiseCoord('x')])
        tests = ['assert(value == 1);']
        run_noise_test(gsg, noise, inputs, tests)

        noise = NoiseAdd([NoiseCoord('x'), NoiseCoord('y'), NoiseCoord('z')])
        tests = ['assert(value == 6);']
        run_noise_test(gsg, noise, inputs, tests)

    def test_sub(self, gsg):
        """Test subtraction operator."""
        inputs = {'point': LPoint3(1, 2, 3)}
        noise = NoiseSub(NoiseCoord('x'), NoiseCoord('y'))
        tests = ['assert(value == -1);']
        run_noise_test(gsg, noise, inputs, tests)

    def test_mul(self, gsg):
        """Test multiplication operator."""
        inputs = {'point': LPoint3(-1, 2, 3)}
        noise = NoiseMul([NoiseCoord('x')])
        tests = ['assert(value == -1);']
        run_noise_test(gsg, noise, inputs, tests)

        noise = NoiseMul([NoiseCoord('x'), NoiseCoord('y'), NoiseCoord('z')])
        tests = ['assert(value == -6);']
        run_noise_test(gsg, noise, inputs, tests)

    def test_div(self, gsg):
        """Test division operator."""
        inputs = {'point': LPoint3(1, 2, 3)}
        noise = NoiseDiv(NoiseCoord('z'), NoiseCoord('y'))
        tests = ['assert(value == 1.5);']
        run_noise_test(gsg, noise, inputs, tests)

    def test_pow(self, gsg):
        """Test power/exponentiation operator."""
        inputs = {'point': LPoint3(0.5, 2, 9)}
        noise = NoisePow(NoiseCoord('z'), NoiseCoord('y'))
        tests = ['assert(value == 81);']
        run_noise_test(gsg, noise, inputs, tests)

        noise = NoisePow(NoiseCoord('z'), NoiseCoord('x'))
        tests = ['assert(value == 3);']
        run_noise_test(gsg, noise, inputs, tests)


class TestMathFunctions:
    """Test basic math functions."""

    def test_abs(self, gsg):
        """Test abs() function."""
        noise = AbsNoise(NoiseConst(-1))
        tests = ['assert(value == 1);']
        run_noise_test(gsg, noise, {}, tests)

        noise = AbsNoise(NoiseConst(2))
        tests = ['assert(value == 2);']
        run_noise_test(gsg, noise, {}, tests)

    def test_exp(self, gsg):
        """Test exp() function."""
        inputs = {'point': LPoint3(0, 1, 2)}
        noise = NoiseExp(NoiseCoord('x'))
        tests = ['assert(value == 1);']
        run_noise_test(gsg, noise, inputs, tests)

        noise = NoiseExp(NoiseCoord('z'))
        tests = [f'assert(abs(value - {math.e * math.e}) < 1e-6);']
        run_noise_test(gsg, noise, inputs, tests)

    def test_max(self, gsg):
        """Test max() function."""
        inputs = {'point': LPoint3(0, 1, 2)}
        noise = NoiseMax(NoiseCoord('x'), NoiseConst(1.5))
        tests = ['assert(value == 1.5);']
        run_noise_test(gsg, noise, inputs, tests)

        noise = NoiseMax(NoiseCoord('z'), NoiseConst(1.5))
        tests = ['assert(value == 2);']
        run_noise_test(gsg, noise, inputs, tests)

    def test_min(self, gsg):
        """Test min() function."""
        inputs = {'point': LPoint3(0, 1, 2)}
        noise = NoiseMin(NoiseCoord('x'), NoiseConst(1.5))
        tests = ['assert(value == 0);']
        run_noise_test(gsg, noise, inputs, tests)

        noise = NoiseMin(NoiseCoord('z'), NoiseConst(1.5))
        tests = ['assert(value == 1.5);']
        run_noise_test(gsg, noise, inputs, tests)

    def test_clamp(self, gsg):
        """Test clamp() function with constant bounds."""
        inputs = {'point': LPoint3(0, 2, 4)}
        noise = NoiseClamp(NoiseCoord('x'), 1, 3)
        tests = ['assert(value == 1);']
        run_noise_test(gsg, noise, inputs, tests)

        noise = NoiseClamp(NoiseCoord('y'), 1, 3)
        tests = ['assert(value == 2);']
        run_noise_test(gsg, noise, inputs, tests)

        noise = NoiseClamp(NoiseCoord('z'), 1, 3)
        tests = ['assert(value == 3);']
        run_noise_test(gsg, noise, inputs, tests)

    def test_clamp_dynamic(self, gsg):
        """Test clamp() function with synamic bounds."""
        noise = NoiseClamp(NoiseCoord('x'), 0, 0, dynamic=True)
        inputs = {'point': LPoint3(0, 2, 4), noise.str_id + '_min': 1.0, noise.str_id + '_max': 3.0}
        tests = ['assert(value == 1);']
        run_noise_test(gsg, noise, inputs, tests)

        noise = NoiseClamp(NoiseCoord('y'), 0, 0, dynamic=True)
        inputs = {'point': LPoint3(0, 2, 4), noise.str_id + '_min': 1.0, noise.str_id + '_max': 3.0}
        tests = ['assert(value == 2);']
        run_noise_test(gsg, noise, inputs, tests)

        noise = NoiseClamp(NoiseCoord('z'), 0, 0, dynamic=True)
        inputs = {'point': LPoint3(0, 2, 4), noise.str_id + '_min': 1.0, noise.str_id + '_max': 3.0}
        tests = ['assert(value == 3);']
        run_noise_test(gsg, noise, inputs, tests)
