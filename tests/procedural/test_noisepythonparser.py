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


import pytest

from cosmonium.parsers.noisepythonparser import NoisePythonParser
from cosmonium.parsers.noiseparser import NoiseYamlParser
from cosmonium.procedural.shadernoise import (
    NoiseConst,
    NoiseCoord,
    NoiseAdd,
    NoiseSub,
    NoiseMul,
    NoiseDiv,
    NoisePow,
    NegNoise,
    AbsNoise,
    GpuNoiseLibPerlin3D,
    FbmNoise,
    RidgedNoise,
)


class TestBasicFunctionality:
    """Test basic parsing functionality."""

    def test_numeric_constant(self):
        """Test parsing numeric constants."""
        parser = NoisePythonParser()
        noise = parser.compile("42")
        assert isinstance(noise, NoiseConst)
        assert noise.value == 42

    def test_float_constant(self):
        """Test parsing float constants."""
        parser = NoisePythonParser()
        noise = parser.compile("3.14")
        assert isinstance(noise, NoiseConst)
        assert noise.value == 3.14

    def test_coordinate_x(self):
        """Test parsing x coordinate."""
        parser = NoisePythonParser()
        noise = parser.compile("x")
        assert isinstance(noise, NoiseCoord)
        assert noise.coord == 'x'

    def test_coordinate_y(self):
        """Test parsing y coordinate."""
        parser = NoisePythonParser()
        noise = parser.compile("y")
        assert isinstance(noise, NoiseCoord)
        assert noise.coord == 'y'

    def test_coordinate_z(self):
        """Test parsing z coordinate."""
        parser = NoisePythonParser()
        noise = parser.compile("z")
        assert isinstance(noise, NoiseCoord)
        assert noise.coord == 'z'


class TestBinaryOperators:
    """Test binary operators."""

    def test_addition(self):
        """Test addition operator."""
        parser = NoisePythonParser()
        noise = parser.compile("x + 10")
        assert isinstance(noise, NoiseAdd)
        assert len(noise.noises) == 2
        assert isinstance(noise.noises[0], NoiseCoord)
        assert noise.noises[0].coord == 'x'
        assert isinstance(noise.noises[1], NoiseConst)
        assert noise.noises[1].value == 10

    def test_subtraction(self):
        """Test subtraction operator."""
        parser = NoisePythonParser()
        noise = parser.compile("x - 5")
        assert isinstance(noise, NoiseSub)
        assert isinstance(noise.noise_a, NoiseCoord)
        assert noise.noise_a.coord == 'x'
        assert isinstance(noise.noise_b, NoiseConst)
        assert noise.noise_b.value == 5

    def test_multiplication(self):
        """Test multiplication operator."""
        parser = NoisePythonParser()
        noise = parser.compile("y * 2")
        assert isinstance(noise, NoiseMul)
        assert len(noise.noises) == 2
        assert isinstance(noise.noises[0], NoiseCoord)
        assert noise.noises[0].coord == 'y'
        assert isinstance(noise.noises[1], NoiseConst)
        assert noise.noises[1].value == 2

    def test_power(self):
        """Test power operator."""
        parser = NoisePythonParser()
        noise = parser.compile("x ** 2")
        assert isinstance(noise, NoisePow)
        assert isinstance(noise.noise_a, NoiseCoord)
        assert noise.noise_a.coord == 'x'
        assert isinstance(noise.noise_b, NoiseConst)
        assert noise.noise_b.value == 2

    def test_division(self):
        """Test division operator."""
        parser = NoisePythonParser()
        noise = parser.compile("x / 2")
        assert isinstance(noise, NoiseDiv)
        assert isinstance(noise.noise_a, NoiseCoord)
        assert noise.noise_a.coord == 'x'
        assert isinstance(noise.noise_b, NoiseConst)
        assert noise.noise_b.value == 2

    def test_complex_expression(self):
        """Test complex expression with multiple operators."""
        parser = NoisePythonParser()
        noise = parser.compile("x + y * 2")
        assert isinstance(noise, NoiseAdd)
        assert len(noise.noises) == 2
        # x + (y * 2) due to operator precedence
        assert isinstance(noise.noises[0], NoiseCoord)
        assert noise.noises[0].coord == 'x'
        assert isinstance(noise.noises[1], NoiseMul)
        mul = noise.noises[1]
        assert len(mul.noises) == 2
        assert isinstance(mul.noises[0], NoiseCoord)
        assert mul.noises[0].coord == 'y'
        assert isinstance(mul.noises[1], NoiseConst)
        assert mul.noises[1].value == 2


class TestUnaryOperators:
    """Test unary operators."""

    def test_unary_minus_constant(self):
        """Test parsing negative constants."""
        parser = NoisePythonParser()
        noise = parser.compile("-10.5")
        assert isinstance(noise, NoiseConst)
        assert noise.value == -10.5

    def test_unary_minus_noise(self):
        """Test parsing negative noise."""
        parser = NoisePythonParser()
        noise = parser.compile("-x")
        assert isinstance(noise, NegNoise)
        assert isinstance(noise.noise, NoiseCoord)
        assert noise.noise.coord == 'x'

    def test_unary_plus(self):
        """Test unary plus operator (no-op)."""
        parser = NoisePythonParser()
        noise = parser.compile("+x")
        assert isinstance(noise, NoiseCoord)
        assert noise.coord == 'x'


class TestFunctionCalls:
    """Test function calls."""

    def test_simple_function_call(self):
        """Test simple function call without arguments."""
        parser = NoisePythonParser()
        noise = parser.compile("perlin()")
        assert isinstance(noise, GpuNoiseLibPerlin3D)

    def test_function_with_positional_arg(self):
        """Test function call with positional argument."""
        parser = NoisePythonParser()
        noise = parser.compile("abs(x)")
        assert isinstance(noise, AbsNoise)
        assert isinstance(noise.noise, NoiseCoord)
        assert noise.noise.coord == 'x'

    def test_function_with_keyword_args(self):
        """Test function call with keyword arguments."""
        parser = NoisePythonParser()
        noise = parser.compile("fbm(noise=perlin(), octaves=8)")
        assert isinstance(noise, FbmNoise)
        assert isinstance(noise.noise, GpuNoiseLibPerlin3D)
        assert noise.octaves == 8

    def test_nested_function_calls(self):
        """Test nested function calls."""
        parser = NoisePythonParser()
        noise = parser.compile("ridged(perlin())")
        assert isinstance(noise, RidgedNoise)
        assert isinstance(noise.noise, GpuNoiseLibPerlin3D)

    def test_complex_nested_expression(self):
        """Test complex nested expression."""
        parser = NoisePythonParser()
        noise = parser.compile("fbm(ridged(perlin()), octaves=8) + 10.0")
        assert isinstance(noise, NoiseAdd)
        assert len(noise.noises) == 2
        assert isinstance(noise.noises[0], FbmNoise)
        assert noise.noises[0].octaves == 8
        assert isinstance(noise.noises[0].noise, RidgedNoise)
        assert isinstance(noise.noises[0].noise.noise, GpuNoiseLibPerlin3D)
        assert isinstance(noise.noises[1], NoiseConst)
        assert noise.noises[1].value == 10


class TestSafety:
    """Test non supported syntax and safety features."""

    def test_unknown_function(self):
        """Test that unknown functions raise an error."""
        parser = NoisePythonParser()
        with pytest.raises(ValueError, match="Unknown noise function: unknown_func"):
            parser.compile("unknown_func()")

    def test_reject_imports(self):
        """Test that import statements are rejected."""
        parser = NoisePythonParser()
        with pytest.raises(ValueError, match="Unknown noise function: __import__"):
            parser.compile("__import__('os')")

    def test_reject_attribute_access(self):
        """Test that attribute access is rejected."""
        parser = NoisePythonParser()
        with pytest.raises(ValueError, match="Unsupported expression type"):
            parser.compile("x.__class__")

    def test_reject_method_calls(self):
        """Test that method calls are rejected."""
        parser = NoisePythonParser()
        with pytest.raises(ValueError, match="Only simple function calls are supported"):
            parser.compile("perlin().noise_value()")

    def test_invalid_syntax(self):
        """Test that invalid Python syntax raises an error."""
        parser = NoisePythonParser()
        with pytest.raises(ValueError, match="Invalid Python syntax"):
            parser.compile("x + + +")

    def test_unknown_variable(self):
        """Test that unknown variables raise an error."""
        parser = NoisePythonParser()
        with pytest.raises(ValueError, match="Unknown name: unknown_var"):
            parser.compile("unknown_var")


class TestEquivalence:
    """Test equivalence between YAML and Python syntax."""

    def test_simple_multiplication_equivalence(self):
        """Test that Python and YAML produce equivalent structures."""
        python_parser = NoisePythonParser()
        yaml_parser = NoiseYamlParser()

        # Python: y * 2000
        python_noise = python_parser.compile("y * 2000")

        # YAML: {mul: [y, 2000]}
        yaml_noise = yaml_parser.decode({"func": {"mul": {"factors": ["y", 2000]}}})

        # Both should be NoiseMul
        assert isinstance(python_noise, NoiseMul)
        assert isinstance(yaml_noise, NoiseMul)

        # Both should have 2 factors
        assert len(python_noise.noises) == 2
        assert len(yaml_noise.noises) == 2

        # First factor should be NoiseCoord('y')
        assert isinstance(python_noise.noises[0], NoiseCoord)
        assert isinstance(yaml_noise.noises[0], NoiseCoord)
        assert python_noise.noises[0].coord == 'y'
        assert yaml_noise.noises[0].coord == 'y'

        # Second factor should be NoiseConst(2000)
        assert isinstance(python_noise.noises[1], NoiseConst)
        assert isinstance(yaml_noise.noises[1], NoiseConst)
        assert python_noise.noises[1].value == 2000
        assert yaml_noise.noises[1].value == 2000

    def test_addition_equivalence(self):
        """Test addition equivalence."""
        python_parser = NoisePythonParser()
        yaml_parser = NoiseYamlParser()

        # Python: x + 10
        python_noise = python_parser.compile("x + 10")

        # YAML: {add: [x, 10]}
        yaml_noise = yaml_parser.decode({"func": {"add": {"terms": ["x", 10]}}})

        # Both should be NoiseAdd
        assert isinstance(python_noise, NoiseAdd)
        assert isinstance(yaml_noise, NoiseAdd)

        # Both should have 2 terms
        assert len(python_noise.noises) == 2
        assert len(yaml_noise.noises) == 2

        # First factor should be NoiseCoord('y')
        assert isinstance(python_noise.noises[0], NoiseCoord)
        assert isinstance(yaml_noise.noises[0], NoiseCoord)
        assert python_noise.noises[0].coord == 'x'
        assert yaml_noise.noises[0].coord == 'x'

        # Second factor should be NoiseConst(2000)
        assert isinstance(python_noise.noises[1], NoiseConst)
        assert isinstance(yaml_noise.noises[1], NoiseConst)
        assert python_noise.noises[1].value == 10
        assert yaml_noise.noises[1].value == 10

    def test_fbm_equivalence(self):
        """Test FBM noise equivalence."""
        python_parser = NoisePythonParser()
        yaml_parser = NoiseYamlParser()

        # Python: fbm(perlin(), octaves=8)
        python_noise = python_parser.compile("fbm(perlin(), octaves=8)")

        # YAML: {fbm: {noise: perlin, octaves: 8}}
        yaml_noise = yaml_parser.decode({"func": {"fbm": {"noise": "gpunoise:perlin", "octaves": 8}}})

        # Both should be FbmNoise
        assert isinstance(python_noise, FbmNoise)
        assert isinstance(yaml_noise, FbmNoise)
        assert python_noise.octaves == 8
        assert yaml_noise.octaves == 8


class TestIntegrationWithYamlParser:
    """Test integration with the YAML parser."""

    def test_python_key_in_yaml(self):
        """Test that the python: key works in YAML parser."""
        yaml_parser = NoiseYamlParser()
        noise = yaml_parser.decode({"python": "x + 10"})
        assert isinstance(noise, NoiseAdd)
        assert len(noise.noises) == 2
        assert isinstance(noise.noises[0], NoiseCoord)
        assert noise.noises[0].coord == 'x'
        assert isinstance(noise.noises[1], NoiseConst)
        assert noise.noises[1].value == 10

    def test_complex_python_expression_in_yaml(self):
        """Test complex Python expression via YAML parser."""
        yaml_parser = NoiseYamlParser()
        noise = yaml_parser.decode({"python": "fbm(ridged(perlin()), octaves=8) + 10.0"})
        assert isinstance(noise, NoiseAdd)
        assert len(noise.noises) == 2
        assert isinstance(noise.noises[0], FbmNoise)
        assert isinstance(noise.noises[1], NoiseConst)
        assert noise.noises[1].value == 10


class TestEdgeCases:
    """Test edge and corner cases."""

    def test_parentheses(self):
        """Test that parentheses work correctly."""
        parser = NoisePythonParser()
        noise = parser.compile("(x + y) * 2")
        assert isinstance(noise, NoiseMul)
        assert len(noise.noises) == 2
        assert isinstance(noise.noises[0], NoiseAdd)
        add = noise.noises[0]
        assert len(add.noises) == 2
        assert isinstance(add.noises[0], NoiseCoord)
        assert add.noises[0].coord == 'x'
        assert isinstance(add.noises[1], NoiseCoord)
        assert add.noises[1].coord == 'y'
        assert isinstance(noise.noises[1], NoiseConst)
        assert noise.noises[1].value == 2

    def test_multiple_additions(self):
        """Test multiple additions."""
        parser = NoisePythonParser()
        noise = parser.compile("x + y + z")
        # This creates nested additions: (x + y) + z
        assert isinstance(noise, NoiseAdd)

    def test_multiline_expression(self):
        """Test multiline expression."""
        parser = NoisePythonParser()
        code = """fbm(
            ridged(perlin()),
            octaves=8
        ) + 10.0"""
        noise = parser.compile(code)
        assert isinstance(noise, NoiseAdd)
        assert isinstance(noise.noises[0], FbmNoise)

    def test_whitespace_handling(self):
        """Test that whitespace is handled correctly."""
        parser = NoisePythonParser()
        noise1 = parser.compile("x+y")
        noise2 = parser.compile("x + y")
        noise3 = parser.compile("x  +  y")
        # All should produce the same structure
        assert isinstance(noise1, NoiseAdd)
        assert isinstance(noise2, NoiseAdd)
        assert isinstance(noise3, NoiseAdd)
