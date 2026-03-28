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


"""
Custom Pydantic field types for Panda3D math objects.

This module provides type annotations that validate and automatically convert
list inputs into the appropriate Panda3D math types (LVector3d, LPoint3d, LColor).
"""

from __future__ import annotations

from typing import Any, Sequence

from panda3d.core import LColor, LPoint3d, LVector3d
from pydantic import GetCoreSchemaHandler
from pydantic_core import core_schema


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _to_float_list(value: Any, expected_lengths: tuple[int, ...]) -> list[float]:
    """Validate that *value* is a numeric sequence with an acceptable length.

    Returns a list of Python floats so that callers can safely pass them to
    Panda3D constructors.

    Raises ``ValueError`` on any mismatch.
    """
    if isinstance(value, (int, float)):
        # Scalar broadcasts into a vector of uniform components (matching Panda3D's
        # single-argument constructor convention) - only legal for single-element
        # expected lengths or when a uniform vector is acceptable.
        return [float(value)] * expected_lengths[0]
    if not isinstance(value, (list, tuple, Sequence)) or isinstance(value, (str, bytes)):
        raise ValueError(f"Expected a sequence of numbers, got {type(value).__name__!r}")
    n = len(value)
    if n not in expected_lengths:
        lengths_str = " or ".join(str(length) for length in expected_lengths)
        raise ValueError(f"Expected {lengths_str} components, got {n}")
    try:
        return [float(x) for x in value]
    except (TypeError, ValueError) as exc:
        raise ValueError(f"All components must be numeric: {exc}") from exc


# ---------------------------------------------------------------------------
# _VecType — reusable base class for n-component field types
# ---------------------------------------------------------------------------


class _VecType:
    """Pydantic custom type base for a n-component float vector/point.

    Subclasses must override ``_panda_type`` (the Panda3D class to
    instantiate), and ``_n_components`` (the number of components of the vector).
    """

    _panda_type: Any = None
    _n_components: int = 0

    @classmethod
    def _validate(cls, value: Any) -> Any:
        if isinstance(value, cls._panda_type):
            return value
        floats = _to_float_list(value, (cls._n_components,))
        return cls._panda_type(*floats)

    @classmethod
    def _serialize(cls, value: Any) -> list[float]:
        if isinstance(value, (list, tuple)):
            return [float(x) for x in value]
        # Panda3D vector - iterate to extract components
        try:
            return [float(x) for x in value]
        except Exception:
            return list(value)

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler: GetCoreSchemaHandler) -> core_schema.CoreSchema:
        return core_schema.no_info_plain_validator_function(
            cls._validate,
            serialization=core_schema.plain_serializer_function_ser_schema(
                cls._serialize,
                info_arg=False,
            ),
        )


# ---------------------------------------------------------------------------
# Concrete 3-component types
# ---------------------------------------------------------------------------


class Vector3Field(_VecType):
    _panda_type = LVector3d
    _n_components = 3


class Point3Field(_VecType):
    _panda_type = LPoint3d
    _n_components = 3


# ---------------------------------------------------------------------------
# LColorType — 3 or 4 component RGBA color
# ---------------------------------------------------------------------------


class ColorField(_VecType):
    """Pydantic custom type for an RGBA color.

    Accepts either 3 components ``[r, g, b]`` (alpha defaults to 1.0) or
    4 components ``[r, g, b, a]``.  Always serializes back to a 4-element list.
    """

    @classmethod
    def _validate(cls, value: Any) -> Any:
        if isinstance(value, LColor):
            return value
        floats = _to_float_list(value, (3, 4))
        if len(floats) == 3:
            floats.append(1.0)
        return LColor(*floats)
