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

from typing import Optional

"""
Object name registry and management.
This module provides the CatalogRegistry, ObjectName, and ObjectNames classes for managing
object names in the simulation.
"""


class CatalogRegistry:
    """Registry for astronomical catalogs with dynamic ID assignment."""

    instance: Optional[CatalogRegistry] = None  # Singleton instance

    def __init__(self):
        self._catalogs: dict[str, tuple[int, str]] = {}  # prefix -> (id, description)
        self._id_to_prefix: dict[int, str] = {}  # id -> prefix
        self._next_id: int = 1

    @classmethod
    def get_instance(cls) -> CatalogRegistry:
        """Get the singleton instance of CatalogRegistry."""
        if cls.instance is None:
            cls.instance = cls()
        return cls.instance

    def register_catalog(self, prefix: str, description: str = '') -> int:
        """
        Register a catalog with auto-assigned ID.

        Args:
            prefix: Catalog prefix (e.g., "HIP", "NGC")
            description: Optional description of the catalog

        Returns:
            The assigned catalog ID
        """
        if prefix in self._catalogs:
            return self._catalogs[prefix][0]  # Already registered

        catalog_id = self._next_id
        self._next_id += 1
        self._catalogs[prefix] = (catalog_id, description)
        self._id_to_prefix[catalog_id] = prefix
        return catalog_id

    def get_id(self, prefix: str) -> int:
        """Get the ID for a catalog prefix."""
        if prefix in self._catalogs:
            return self._catalogs[prefix][0]
        return 0  # Vernaclar

    def get_prefix(self, catalog_id: int) -> str:
        """Get the prefix for a catalog ID."""
        return self._id_to_prefix.get(catalog_id, '')

    def get_description(self, prefix: str) -> str:
        """Get the description for a catalog prefix."""
        if prefix in self._catalogs:
            return self._catalogs[prefix][1]
        return ''

    def has_catalog(self, prefix: str) -> bool:
        """Check if a catalog is registered."""
        return prefix in self._catalogs

    def get_all_prefixes(self) -> list[str]:
        """Get all registered catalog prefixes."""
        return list(self._catalogs.keys())

    def clear(self) -> None:
        """Clear all registered catalogs."""
        self._catalogs.clear()
        self._id_to_prefix.clear()
        self._next_id = 1


# SIMBAD Bayer greek abbreviations
BAYER_PREFIXES: set[str] = {
    'ALF',
    'BET',
    'GAM',
    'DEL',
    'EPS',
    'ZET',
    'ETA',
    'TET',
    'IOT',
    'KAP',
    'LAM',
    'MU.',
    'NU.',
    'KSI',
    'OMI',
    'PI.',
    'RHO',
    'SIG',
    'TAU',
    'UPS',
    'PHI',
    'KHI',
    'PSI',
    'OME',
    # Canonical aliases
    'ALP',
    'THE',
    'MU',
    'NU',
    'XI',
    'XI.',
    'PI',
    'CHI',
}

# 3-letter constellation abbreviations
CONSTELLATIONS: set[str] = {
    'Aql',
    'And',
    'Ara',
    'Lib',
    'Cet',
    'Ari',
    'Pyx',
    'Boo',
    'Cae',
    'Cha',
    'Cnc',
    'Cap',
    'Car',
    'Cas',
    'Cen',
    'Cep',
    'Com',
    'CVn',
    'Aur',
    'Col',
    'Cir',
    'Crv',
    'Crt',
    'CrA',
    'CrB',
    'Cru',
    'Cyg',
    'Del',
    'Dor',
    'Dra',
    'Sct',
    'Eri',
    'Sge',
    'For',
    'Gem',
    'Cam',
    'CMa',
    'UMa',
    'Gru',
    'Her',
    'Hor',
    'Hya',
    'Hyi',
    'Ind',
    'Lac',
    'Mon',
    'Lep',
    'Leo',
    'Lup',
    'Lyn',
    'Lyr',
    'Ant',
    'Mic',
    'Mus',
    'Oct',
    'Aps',
    'Oph',
    'Ori',
    'Pav',
    'Peg',
    'Pic',
    'Per',
    'Equ',
    'CMi',
    'LMi',
    'Vul',
    'UMi',
    'Phe',
    'PsA',
    'Vol',
    'Psc',
    'Pup',
    'Nor',
    'Ret',
    'Sgr',
    'Sco',
    'Scl',
    'Ser',
    'Sex',
    'Men',
    'Tau',
    'Tel',
    'Tuc',
    'Tri',
    'TrA',
    'Aqr',
    'Vir',
    'Vel',
}


class ObjectName:
    """Represents a single object name with type information."""

    # Name type constants
    NT_vernacular = 0
    NT_bayer = 1
    NT_flamsteed = 2
    NT_catalog = 3
    NT_variable_star = 4
    NT_custom = 5
    NT_minor_planet = 6

    def __init__(self, value: str, name_type: int, catalog_id: int = 0, translatable: bool = True) -> None:
        self.value = value
        self.type = name_type
        self.catalog_id = catalog_id
        self.translatable = translatable

    @classmethod
    def make_vernacular(cls, name: str) -> ObjectName:
        """Create a vernacular (common) name."""
        return ObjectName(name, cls.NT_vernacular, 0, True)

    @classmethod
    def make_flamsteed(cls, name: str) -> ObjectName:
        """Create a Flamsteed designation name."""
        return ObjectName(name, cls.NT_flamsteed, 0, False)

    @classmethod
    def make_bayer(cls, name: str) -> ObjectName:
        """Create a Bayer designation name."""
        return ObjectName(name, cls.NT_bayer, 0, False)

    @classmethod
    def make_catalog(cls, catalog_id: int, value: str) -> ObjectName:
        """Create a catalog name."""
        return ObjectName(value, cls.NT_catalog, catalog_id, False)

    @classmethod
    def make_minor_planet(cls, name: str) -> ObjectName:
        """Create a minor planet / asteroid designation name."""
        return ObjectName(name, cls.NT_minor_planet, 0, True)

    def get_full_name(self) -> str:
        """Get the full name, reconstructing catalog names if needed."""
        if self.type == self.NT_catalog and self.catalog_id > 0:
            prefix = CatalogRegistry.get_instance().get_prefix(self.catalog_id)
            if prefix:
                return f"{prefix} {self.value}"
        return self.value

    def __repr__(self) -> str:
        return (
            f"ObjectName(value='{self.value}', type={self.type}, "
            f"catalog_id={self.catalog_id}, translatable={self.translatable})"
        )


class ObjectNames:
    """Manages a collection of object names."""

    def __init__(self) -> None:
        self._names: list[ObjectName] = []
        self._originals: list[str] = []  # Parallel list, sparse (only for translated entries)

    def add_name(self, name: ObjectName, original: Optional[str] = None) -> None:
        """Add a name to the collection."""
        self._names.append(name)
        self._originals.append(original if original else '')

    def get_num_names(self) -> int:
        """Get the number of names."""
        return len(self._names)

    def get_name_entry(self, index: int) -> ObjectName:
        """Get the ObjectName entry at the given index."""
        return self._names[index]

    def get_c_name(self) -> str:
        """Get the first name untranslated (original before translation)."""
        # Return the original untranslated name from _originals[0] if available
        if self._originals and self._originals[0]:
            return self._originals[0]
        # Otherwise return the first name's full name
        return self._names[0].get_full_name() if self._names else ''

    def get_name(self) -> str:
        """Get the primary name."""
        return self._names[0].get_full_name() if self._names else ''

    def get_all_names(self) -> list[str]:
        """Get all names as a list of strings."""
        return [name.get_full_name() for name in self._names]

    def get_source_names(self) -> list[str]:
        """Get source names (non-translatable names and originals of translated ones)."""
        result = []
        for i, name in enumerate(self._names):
            if not name.translatable:
                result.append(name.get_full_name())
            elif i < len(self._originals) and self._originals[i]:
                result.append(self._originals[i])
        return result

    def get_catalog_names(self, catalog_id: int) -> list[str]:
        """Get all names from a specific catalog."""
        result = []
        for name in self._names:
            if name.type == ObjectName.NT_catalog and name.catalog_id == catalog_id:
                result.append(name.get_full_name())
        return result

    def has_catalog_entry(self, catalog_id: int) -> bool:
        """Check if there's an entry from the specified catalog."""
        for name in self._names:
            if name.type == ObjectName.NT_catalog and name.catalog_id == catalog_id:
                return True
        return False

    def get_catalog_id(self, catalog_id: int) -> str:
        """Get the ID value from the specified catalog."""
        for name in self._names:
            if name.type == ObjectName.NT_catalog and name.catalog_id == catalog_id:
                return name.value
        return ''

    def set_translated(self, index: int, translated: str) -> None:
        """Set a translated value for a name, storing the original."""
        if index >= len(self._names):
            return  # Index out of bounds

        # Ensure _originals is sized properly
        if index >= len(self._originals):
            # Extend the list efficiently
            self._originals.extend([''] * (index - len(self._originals) + 1))

        # Store original if not already stored
        if not self._originals[index]:
            self._originals[index] = self._names[index].value
        self._names[index].value = translated

    @classmethod
    def parse_name(cls, name: str, reflective: bool = False) -> ObjectName:
        """
        Parse a name string and auto-detect its type.

        Args:
            name: The name string to parse.
            reflective: When True the body is a reflective body.
                When True, the minor-planet designation pattern is tested and Flamsteed
                pattern is ignored.
                When False, Flamsteed pattern is tested and the minor-planet designation
                pattern is ignored.

        Returns an ObjectName with appropriate type, catalog_id, and translatable flag.
        """
        if not name:
            return ObjectName.make_vernacular(name)

        # Check for catalog prefix (e.g., "HIP 32349")
        space_pos = name.find(' ')
        if space_pos > 0:
            prefix = name[:space_pos]
            upper_prefix = prefix.upper()

            # Check for known catalog
            catalog_id = CatalogRegistry.get_instance().get_id(upper_prefix)
            if catalog_id:
                value = name[space_pos + 1 :]
                return ObjectName.make_catalog(catalog_id, value)

            # Check for Bayer designation (e.g., "ALF CMa", "BET2 Ori")
            # Extract just the greek letters (may have numbers attached)
            bayer_prefix = ''
            for i, c in enumerate(upper_prefix):
                if c.isdigit():
                    bayer_prefix = upper_prefix[:i]
                    break
            else:
                bayer_prefix = upper_prefix

            if bayer_prefix in BAYER_PREFIXES:
                rest = name[space_pos + 1 :]

                # May have optional number followed by constellation
                rest_space = rest.find(' ')
                if rest_space >= 0:
                    maybe_constellation = rest[rest_space + 1 :]
                    if maybe_constellation in CONSTELLATIONS:
                        return ObjectName.make_bayer(name)
                else:
                    # Just prefix + constellation
                    if rest in CONSTELLATIONS:
                        return ObjectName.make_bayer(name)

            # "NUMBER Word" patterns: Flamsteed (stars) vs minor-planet (reflective bodies)
            if prefix.isdigit():
                rest = name[space_pos + 1 :]
                if rest.isalpha():
                    if reflective:
                        # Reflective bodies (minor planets, asteroids): any alphabetic name
                        # after the number is a minor-planet designation.
                        return ObjectName.make_minor_planet(name)
                    else:
                        # Stars / stellar systems: a 2-4 letter word is a constellation
                        # abbreviation → Flamsteed designation.
                        if 2 <= len(rest) <= 4:
                            return ObjectName.make_flamsteed(name)

        # Default to vernacular name (translatable)
        return ObjectName.make_vernacular(name)
