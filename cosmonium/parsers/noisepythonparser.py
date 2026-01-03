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
Python Expression Parser for Noise Functions

This module provides an alternative way to define noise functions using Python syntax
instead of hierarchical YAML. The parser is completely safe - it never executes user
code, only parses Python expressions into noise object hierarchies by delegating to
the YAML parser for actual noise creation.

Example Usage:
    parser = NoisePythonParser()
    noise = parser.compile("fbm(ridged(perlin()), octaves=8) + 10.0")

Supported Syntax:
    - Binary operators: +, -, *, /, //, **, etc.
    - Unary operators: -, +, ~
    - Function calls: perlin(), fbm(noise=perlin(), octaves=8)
    - Numeric literals: 42, 3.14, -1.5
    - Coordinate names: x, y, z
"""

import ast

from ..procedural.primitives.arithmetic import NegNoise, NoiseAdd, NoiseSub, NoiseMul, NoiseDiv, NoisePow
from ..procedural.sources.simple import NoiseConst, NoiseCoord

# Import all the create_*() functions from noiseparser
from .noiseparser import (
    create_add_noise,
    create_sub_noise,
    create_mul_noise,
    create_div_noise,
    create_pow_noise,
    create_exp_noise,
    create_min_noise,
    create_max_noise,
    create_threshold_noise,
    create_clamp_noise,
    create_x_noise,
    create_y_noise,
    create_z_noise,
    create_gpunoise_perlin_noise,
    create_gpunoise_cellular_noise,
    create_gpunoise_polkadot_noise,
    create_stegu_perlin_noise,
    create_stegu_cellular_noise,
    create_stegu_cellulardiff_noise,
    create_iq_perlin_noise,
    create_iq_gradient_noise,
    create_sincos_noise,
    create_ridged_noise,
    create_abs_noise,
    create_neg_noise,
    create_square_noise,
    create_cube_noise,
    create_fbm_noise,
    create_spiral_noise,
    create_warp_noise,
    create_rotate_noise,
    create_1d_noise,
    create_const_noise,
    create_position_map,
    create_noise_map,
)


class NoisePythonParser:
    """
    AST-based parser for converting Python expressions into Noise objects.

    This parser provides an easy way to define noise functions using Python syntax.
    It parses AST nodes and delegates to the YAML parser creation functions,
    ensuring all preprocessing and validation is consistent.
    """

    # Class-level registries for functions and operators
    # Maps Python function name to create_*() function from noiseparser
    _noise_functions = {}
    _binary_operators = {}
    _unary_operators = {}

    @classmethod
    def register_noise_function(cls, name, create_func):
        """
        Register a noise function that can be called from Python syntax.

        Args:
            name: Function name as it appears in Python code (e.g., 'perlin')
            create_func: The create_*() function from noiseparser.py

        Example:
            from cosmonium.parsers.noiseparser import create_gpunoise_perlin_noise
            NoisePythonParser.register_noise_function('perlin', create_gpunoise_perlin_noise)
            # Users can now write: perlin()
        """
        cls._noise_functions[name] = create_func

    @classmethod
    def register_binary_operator(cls, operator_type, factory_func):
        """
        Register a binary operator handler.

        Args:
            operator_type: AST operator type (e.g., ast.Add, ast.Sub)
            factory_func: Callable that takes (left, right) and returns a Noise object

        Example:
            NoisePythonParser.register_binary_operator(ast.Add, lambda l, r: NoiseAdd([l, r]))
            # Users can now write: noise_a + noise_b
        """
        cls._binary_operators[operator_type] = factory_func

    @classmethod
    def register_unary_operator(cls, operator_type, factory_func):
        """
        Register a unary operator handler.

        Args:
            operator_type: AST operator type (e.g., ast.USub, ast.UAdd)
            factory_func: Callable that takes (operand) and returns a Noise object

        Example:
            NoisePythonParser.register_unary_operator(ast.USub, lambda op: NegNoise(op))
            # Users can now write: -noise
        """
        cls._unary_operators[operator_type] = factory_func

    def __init__(self, yaml_parser=None):
        """
        Initialize the parser.

        Args:
            yaml_parser: NoiseYamlParser instance to use for noise creation.
                        If None, a new instance will be created.
        """
        # Import here to avoid circular dependency
        if yaml_parser is None:
            from .noiseparser import NoiseYamlParser

            yaml_parser = NoiseYamlParser()
        self._yaml_parser = yaml_parser

    def compile(self, code_string):
        """
        Parse a Python expression string and return a Noise object.

        Args:
            code_string: Python expression as a string

        Returns:
            Noise object hierarchy

        Raises:
            ValueError: If the expression is invalid or uses unsupported features
            SyntaxError: If the Python syntax is invalid

        """
        try:
            # Parse the code into an AST
            tree = ast.parse(code_string, mode="eval")
            # Visit the expression node
            return self._visit(tree.body)
        except SyntaxError as e:
            raise ValueError(f"Invalid Python syntax: {e}")

    def _visit(self, node):
        """
        Visit an AST node and return the corresponding Noise object.

        This is the main dispatch method that handles different node types.
        """
        # Dispatch to the appropriate handler based on node type
        if isinstance(node, ast.BinOp):
            return self._visit_binop(node)
        elif isinstance(node, ast.UnaryOp):
            return self._visit_unaryop(node)
        elif isinstance(node, ast.Call):
            return self._visit_call(node)
        elif isinstance(node, ast.Constant):
            return self._visit_constant(node)
        elif isinstance(node, ast.Name):
            return self._visit_name(node)
        else:
            raise ValueError(
                f"Unsupported expression type: {type(node).__name__}. "
                "Only arithmetic operations, function calls, and literals are allowed."
            )

    def _visit_binop(self, node):
        """Handle binary operations (e.g., a + b, a * b)."""
        left = self._visit(node.left)
        right = self._visit(node.right)

        op_type = type(node.op)
        if op_type not in self._binary_operators:
            raise ValueError(
                f"Unsupported binary operator: {op_type.__name__}. "
                f"Supported operators: {list(self._binary_operators.keys())}"
            )

        factory = self._binary_operators[op_type]
        return factory(left, right)

    def _visit_unaryop(self, node):
        """Handle unary operations (e.g., -x, +x)."""
        operand = self._visit(node.operand)

        op_type = type(node.op)
        if op_type not in self._unary_operators:
            raise ValueError(
                f"Unsupported unary operator: {op_type.__name__}. "
                f"Supported operators: {list(self._unary_operators.keys())}"
            )

        factory = self._unary_operators[op_type]
        return factory(operand)

    def _visit_call(self, node):
        """Handle function calls (e.g., perlin(), fbm(noise=perlin(), octaves=8))."""
        # Get function name
        if not isinstance(node.func, ast.Name):
            raise ValueError(
                "Only simple function calls are supported (e.g., perlin()). "
                "Method calls and attribute access are not allowed."
            )

        func_name = node.func.id

        if func_name not in self._noise_functions:
            raise ValueError(
                f"Unknown noise function: {func_name}. " f"Available functions: {sorted(self._noise_functions.keys())}"
            )

        # Get the create_*() function
        create_func = self._noise_functions[func_name]

        # Build parameters dict for the create function
        params = {}

        # Parse positional arguments
        # For most functions, the first positional arg is 'noise'
        if len(node.args) > 0:
            # Visit each positional arg to get a Noise object
            for i, arg in enumerate(node.args):
                visited_arg = self._visit(arg)
                # Use 'noise' for first arg if it's a Noise object, otherwise use positional index
                if i == 0:
                    params["noise"] = visited_arg
                else:
                    # Additional positional args (rare case)
                    params[f"arg{i}"] = visited_arg

        # Parse keyword arguments
        for keyword in node.keywords:
            # Convert Python-style parameter names (underscores) to YAML-style (hyphens)
            param_name = keyword.arg.replace("_", "-")

            # Visit the value to get a Noise object or keep primitive values
            value = keyword.value
            if isinstance(value, ast.Constant):
                # For constants, extract the actual value
                params[param_name] = value.value
            elif isinstance(value, ast.UnaryOp) and isinstance(value.op, ast.USub):
                # Handle negative constants (e.g., min=-0.5)
                if isinstance(value.operand, ast.Constant):
                    params[param_name] = -value.operand.value
                else:
                    # If it's not a simple negative constant, visit it
                    params[param_name] = self._visit(value)
            elif isinstance(value, (ast.Name, ast.BinOp, ast.UnaryOp, ast.Call)):
                # For expressions, visit them to get Noise objects
                params[param_name] = self._visit(value)
            else:
                raise ValueError(f"Unsupported keyword argument type for {keyword.arg}: {type(value).__name__}")

        # Call the create_*() function directly
        try:
            # The create functions expect (parser, data, length_scale)
            # The data can be a string, dict, or list depending on the function
            # We pass our params dict as the data
            return create_func(self._yaml_parser, params, self._yaml_parser.length_scale)
        except Exception as e:
            raise ValueError(
                f"Error calling {func_name}() via create function: {e}. "
                "Check that you're passing the correct arguments."
            )

    def _visit_constant(self, node):
        """Handle constant values (numbers, strings, etc.)."""
        if isinstance(node.value, (int, float)):
            return NoiseConst(node.value)
        else:
            raise ValueError(
                f"Unsupported constant type: {type(node.value).__name__}. Only numeric constants are allowed."
            )

    def _visit_name(self, node):
        """Handle variable names (e.g., x, y, z)."""
        name = node.id

        # Check if it's a coordinate
        if name in ("x", "y", "z"):
            return NoiseCoord(name)

        raise ValueError(
            f"Unknown name: {name}. " "Only coordinate names (x, y, z) or registered functions are allowed."
        )


# ============================================================================
# Register Binary Operators
# ============================================================================

NoisePythonParser.register_binary_operator(ast.Add, lambda left, right: NoiseAdd([left, right]))
NoisePythonParser.register_binary_operator(ast.Sub, lambda left, right: NoiseSub(left, right))
NoisePythonParser.register_binary_operator(ast.Mult, lambda left, right: NoiseMul([left, right]))
NoisePythonParser.register_binary_operator(ast.Div, lambda left, right: NoiseDiv(left, right))
NoisePythonParser.register_binary_operator(ast.Pow, lambda left, right: NoisePow(left, right))


# ============================================================================
# Register Unary Operators
# ============================================================================


def create_unary_neg_noise(op):
    """Special create function for unary negation"""
    if isinstance(op, NoiseConst):
        # If we are negating a constant, we directly negate the value
        op.value = -op.value
        return op
    else:
        return NegNoise(op)


NoisePythonParser.register_unary_operator(ast.USub, create_unary_neg_noise)
NoisePythonParser.register_unary_operator(ast.UAdd, lambda op: op)  # Unary + is a no-op


# ============================================================================
# Register Noise Functions
# ============================================================================

# Arithmetic operations
NoisePythonParser.register_noise_function("add", create_add_noise)
NoisePythonParser.register_noise_function("sub", create_sub_noise)
NoisePythonParser.register_noise_function("mul", create_mul_noise)
NoisePythonParser.register_noise_function("div", create_div_noise)
NoisePythonParser.register_noise_function("pow", create_pow_noise)
NoisePythonParser.register_noise_function("exp", create_exp_noise)

# Comparison/clamping operations
NoisePythonParser.register_noise_function("min", create_min_noise)
NoisePythonParser.register_noise_function("max", create_max_noise)
NoisePythonParser.register_noise_function("threshold", create_threshold_noise)
NoisePythonParser.register_noise_function("clamp", create_clamp_noise)

# Coordinate functions
NoisePythonParser.register_noise_function("x", create_x_noise)
NoisePythonParser.register_noise_function("y", create_y_noise)
NoisePythonParser.register_noise_function("z", create_z_noise)

# Basic noise generators - GpuNoiseLib variants (use shorthand names)
NoisePythonParser.register_noise_function("perlin", create_gpunoise_perlin_noise)
NoisePythonParser.register_noise_function("cellular", create_gpunoise_cellular_noise)
NoisePythonParser.register_noise_function("polkadot", create_gpunoise_polkadot_noise)

# GpuNoiseLib prefixed variants (explicit names)
NoisePythonParser.register_noise_function("gpunoise_perlin", create_gpunoise_perlin_noise)
NoisePythonParser.register_noise_function("gpunoise_cellular", create_gpunoise_cellular_noise)
NoisePythonParser.register_noise_function("gpunoise_polkadot", create_gpunoise_polkadot_noise)

# SteGu noise variants
NoisePythonParser.register_noise_function("stegu_perlin", create_stegu_perlin_noise)
NoisePythonParser.register_noise_function("stegu_cellular", create_stegu_cellular_noise)
NoisePythonParser.register_noise_function("stegu_cellulardiff", create_stegu_cellulardiff_noise)

# IQ (Inigo Quilez) noise variants
NoisePythonParser.register_noise_function("iq_perlin", create_iq_perlin_noise)
NoisePythonParser.register_noise_function("iq_gradient", create_iq_gradient_noise)

# Other noise generators
NoisePythonParser.register_noise_function("sincos", create_sincos_noise)

# Transform functions
NoisePythonParser.register_noise_function("ridged", create_ridged_noise)
NoisePythonParser.register_noise_function("abs", create_abs_noise)
NoisePythonParser.register_noise_function("turbulence", create_abs_noise)  # alias for abs
NoisePythonParser.register_noise_function("neg", create_neg_noise)
NoisePythonParser.register_noise_function("square", create_square_noise)
NoisePythonParser.register_noise_function("cube", create_cube_noise)

# Compound noise functions
NoisePythonParser.register_noise_function("fbm", create_fbm_noise)
NoisePythonParser.register_noise_function("spiral", create_spiral_noise)
NoisePythonParser.register_noise_function("warp", create_warp_noise)
NoisePythonParser.register_noise_function("rot", create_rotate_noise)

# 1D noise projection
NoisePythonParser.register_noise_function("noise1d", create_1d_noise)

# Constants
NoisePythonParser.register_noise_function("const", create_const_noise)

# Position and output mapping
NoisePythonParser.register_noise_function("pos_map", create_position_map)
NoisePythonParser.register_noise_function("noise_map", create_noise_map)
