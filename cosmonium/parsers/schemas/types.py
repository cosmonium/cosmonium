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
Custom Pydantic field types.

This module provides:

* Type annotations that validate and automatically convert list inputs into the
  appropriate Panda3D math types (LVector3d, LPoint3d, LColor).
* Type annotations for numeric values with associated units, which accept either a
    bare numeric value (using a per-field default unit) or an explicit [value, unit_str]
    pair.  Validation converts both forms into a ValueWithUnits named-tuple whose
    .scaled_value property returns the value expressed in Cosmonium's internal base
    unit for the relevant dimension (km for distances, days for time, radians for
    angles).
"""

from __future__ import annotations

from typing import Any, NamedTuple, Sequence

from panda3d.core import LColor, LPoint3d, LVector3d
from pydantic import GetCoreSchemaHandler
from pydantic_core import core_schema

from ...astro import units

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


# ===========================================================================
# Value-with-units field types
# ===========================================================================
#
# These types allow schema fields to accept either a bare numeric value
# (which uses a per-field default unit) or an explicit ``[value, unit_str]``
# pair.  Validation converts both forms into a ``ValueWithUnits`` named-tuple
# whose ``.scaled_value`` property returns the value expressed in Cosmonium's
# internal base unit for the relevant dimension (km for distances, days for
# time, radians for angles).
#
# Usage in schema classes::
#
#     from .types import DistanceAUField, TimeYearField, AngleDegField
#
#     class MyConfig(ConfigBase):
#         semi_major_axis: Optional[DistanceAUField] = Field(None)
#         period: Optional[TimeYearField] = Field(None)
#         inclination: AngleDegField = Field(0.0)
#
# Parsers then access the already-scaled value::
#
#     if data.semi_major_axis is not None:
#         sma_km = data.semi_major_axis.scaled_value
#
# Serialization: ``model_dump()`` always returns ``[value, unit_str]`` so
# configs can be round-tripped through YAML without losing unit information.
#

_DISTANCE_UNITS: dict[str, float] = {
    'm': units.m,
    'km': units.Km,
    'au': units.AU,
    'ly': units.Ly,
    'pc': units.Parsec,
    'kpc': units.KParsec,
    'mpc': units.MParsec,
    'gpc': units.GParsec,
}

_TIME_UNITS: dict[str, float] = {
    'sec': units.Sec,
    'min': units.Min,
    'hour': units.Hour,
    'day': units.Day,
    'year': units.JYear,
}

_ANGLE_UNITS: dict[str, float] = {
    'deg': units.Deg,
    'hour': units.HourAngle,
    'rad': units.Rad,
}

_ANGLE_SPEED_UNITS: dict[str, float] = {
    'deg/day': units.Deg / units.Day,
}


# ---------------------------------------------------------------------------
# ValueWithUnits — the canonical storage type for all unit fields
# ---------------------------------------------------------------------------


class ValueWithUnits(NamedTuple):
    """A numeric value paired with its unit string and precomputed scale factor.

    ``scaled_value`` returns ``value * scale``, i.e. the value expressed in
    internal base unit for the relevant dimension.

    Examples::

        v = ValueWithUnits(1.0, 'au', 149597870.7)
        v.scaled_value  # => 149597870.7 km

        v = ValueWithUnits(23.5, 'deg', pi/180)
        v.scaled_value  # => 0.410... radians
    """

    value: float
    unit: str
    scale: float

    @property
    def scaled_value(self) -> float:
        """Return ``value * scale`` (value in the internal base unit)."""
        return self.value * self.scale


# ---------------------------------------------------------------------------
# Factory function for unit field types
# ---------------------------------------------------------------------------


def _make_unit_field_type(type_name: str, units_table: dict[str, float], default_unit: str) -> type:
    """Return a new Pydantic-compatible type class for a value-with-unit field.

    The returned class:
    * accepts a bare ``float``/``int`` (uses *default_unit*)
    * accepts a ``[value, unit_str]`` two-element list or tuple
    * accepts an existing :class:`ValueWithUnits` (pass-through)
    * rejects any other input with a descriptive ``ValueError``
    * serializes back to ``[value, unit_str]`` for YAML round-tripping
    """
    _default = default_unit.lower()
    assert _default in units_table, f"default_unit {default_unit!r} not in {type_name} units table"
    _default_scale = units_table[_default]

    def _validate(value: Any) -> ValueWithUnits:
        if isinstance(value, ValueWithUnits):
            if value.unit not in units_table:
                valid = ', '.join(sorted(units_table.keys()))
                raise ValueError(f"Incompatible unit {value.unit!r} for {type_name}; valid: {valid}")
            return value
        if isinstance(value, (int, float)):
            return ValueWithUnits(float(value), _default, _default_scale)
        if isinstance(value, (list, tuple)) and len(value) == 2:
            raw_v, raw_u = value
            try:
                v = float(raw_v)
            except (TypeError, ValueError) as exc:
                raise ValueError(f"Value must be numeric, got {raw_v!r}") from exc
            u = str(raw_u).lower()
            scale = units_table.get(u)
            if scale is None:
                valid = ', '.join(sorted(units_table.keys()))
                raise ValueError(f"Unknown unit {raw_u!r} for {type_name}; valid: {valid}")
            return ValueWithUnits(v, u, scale)
        raise ValueError(f"Expected a number or [number, unit_str] for {type_name}, got {type(value).__name__!r}")

    def _serialize(value: Any) -> Any:
        if isinstance(value, ValueWithUnits):
            return [value.value, value.unit]
        return value

    def _get_schema(cls: Any, source_type: Any, handler: GetCoreSchemaHandler) -> core_schema.CoreSchema:
        return core_schema.no_info_plain_validator_function(
            _validate,
            serialization=core_schema.plain_serializer_function_ser_schema(_serialize, info_arg=False),
        )

    return type(type_name, (), {'__get_pydantic_core_schema__': classmethod(_get_schema)})


# ---------------------------------------------------------------------------
# Public unit field type aliases
# ---------------------------------------------------------------------------

# --- Distance ---

DistanceMField = _make_unit_field_type('DistanceMField', _DISTANCE_UNITS, 'm')

DistanceKmField = _make_unit_field_type('DistanceKmField', _DISTANCE_UNITS, 'km')

DistanceAUField = _make_unit_field_type('DistanceAUField', _DISTANCE_UNITS, 'au')

DistanceLyField = _make_unit_field_type('DistanceLyField', _DISTANCE_UNITS, 'ly')

DistancePcField = _make_unit_field_type('DistancePcField', _DISTANCE_UNITS, 'pc')

# --- Time ---

TimeDayField = _make_unit_field_type('TimeDayField', _TIME_UNITS, 'day')

TimeYearField = _make_unit_field_type('TimeYearField', _TIME_UNITS, 'year')

# --- Angle ---

AngleDegField = _make_unit_field_type('AngleDegField', _ANGLE_UNITS, 'deg')

AngleHourField = _make_unit_field_type('AngleHourField', _ANGLE_UNITS, 'hour')

# --- Angular speed ---

AngleSpeedDegPerDayField = _make_unit_field_type('AngleSpeedDegPerDayField', _ANGLE_SPEED_UNITS, 'deg/day')
