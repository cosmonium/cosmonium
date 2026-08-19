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

import bisect
from typing import TYPE_CHECKING, Optional

from .engine.objectname import CatalogRegistry, ObjectName
from .utils import int_to_color

if TYPE_CHECKING:
    from .engine.pyengine.anchors import AnchorBase
    from .objects.stellarobject import StellarObject


class CatalogIndex:
    """Index for catalog entries with efficient prefix search."""

    def __init__(self, catalog_prefix: str) -> None:
        self.catalog_prefix: str = catalog_prefix
        self._sorted_keys: list[str] = []  # Sorted list of upper-cased catalog IDs for prefix search
        self._id_to_anchor: dict[str, AnchorBase] = {}  # Dict for exact lookup and replacement
        self._dirty: bool = False

    def add(self, catalog_id: str, anchor: AnchorBase) -> None:
        """Add a catalog entry."""
        upper_id = catalog_id.upper()
        self._sorted_keys.append(upper_id)
        self._id_to_anchor[upper_id] = anchor
        self._dirty = True

    def replace(self, catalog_id: str, new_anchor: AnchorBase) -> None:
        """Replace the anchor associated with a catalog ID.

        The sorted keys list is not modified; only the lookup dict is updated.

        Args:
            catalog_id: The catalog ID whose anchor should be replaced.
            new_anchor: The new anchor to associate with the catalog ID.
        """
        upper_id = catalog_id.upper()
        if upper_id in self._id_to_anchor:
            self._id_to_anchor[upper_id] = new_anchor

    def _ensure_sorted(self) -> None:
        """Sort the keys list if needed."""
        if self._dirty:
            self._sorted_keys.sort()
            self._dirty = False

    def get(self, catalog_id: str) -> Optional[AnchorBase]:
        """Get an anchor by exact catalog ID."""
        return self._id_to_anchor.get(catalog_id.upper())

    def startswith(self, id_prefix: str, max_results: int = 50) -> list[tuple[str, AnchorBase]]:
        """
        Find catalog entries where the ID starts with the given prefix.
        Uses bisect for efficient binary search.
        """
        self._ensure_sorted()

        if not id_prefix:
            # Return first N entries
            return [
                (f"{self.catalog_prefix} {key}", self._id_to_anchor[key]) for key in self._sorted_keys[:max_results]
            ]

        upper_prefix = id_prefix.upper()

        # Use bisect to find the leftmost position where upper_key >= upper_prefix
        idx = bisect.bisect_left(self._sorted_keys, upper_prefix)

        result = []
        while idx < len(self._sorted_keys) and len(result) < max_results:
            upper_str_id = self._sorted_keys[idx]
            if upper_str_id.startswith(upper_prefix):
                result.append((f"{self.catalog_prefix} {upper_str_id}", self._id_to_anchor[upper_str_id]))
                idx += 1
            else:
                break

        return result


class NameIndex:
    """Index for name entries with efficient sorted search.

    Args:
        unique: When True, adding a name that already exists in the index will
            update the stored entry without adding a duplicate key to the sorted
            list.
            When False (the default), duplicate keys are allowed.
    """

    def __init__(self, unique: bool = False) -> None:
        self._sorted_keys: list[str] = []  # Sorted list of upper-cased names for prefix search
        self._name_to_entry: dict[str, tuple[str, AnchorBase]] = {}  # upper_name -> (display_name, anchor)
        self._dirty: bool = False
        self._unique: bool = unique

    def add(self, name: str, anchor: AnchorBase, display_name: Optional[str] = None) -> None:
        """Add a name entry.

        Args:
            name: The lookup key (case-insensitive).
            anchor: The anchor to associate with this name.
            display_name: The name returned by :meth:`startswith`.  When
                omitted, *name* itself is used as the display name.  This is
                useful when the search key differs from the canonical name you
                want to show to the user (e.g. an alias "Ceres" whose
                display name is the full designation "1 Ceres").

        When *unique* is ``True`` and the key already exists, the sorted-keys
        list is not modified but the dictionary entry is silently overwritten.
        """
        upper_name = name.upper()
        stored_name = display_name if display_name is not None else name
        if self._unique:
            if upper_name not in self._name_to_entry:
                self._sorted_keys.append(upper_name)
                self._dirty = True
        else:
            self._sorted_keys.append(upper_name)
            self._dirty = True
        self._name_to_entry[upper_name] = (stored_name, anchor)

    def replace(self, name: str, new_anchor: AnchorBase) -> bool:
        """Replace the anchor associated with a name.

        The sorted keys list is not modified; only the lookup dict is updated.

        Args:
            name: The name whose anchor should be replaced.
            new_anchor: The new anchor to associate with the name.

        Returns:
            True if the name was found and replaced, False otherwise.
        """
        upper_name = name.upper()
        if upper_name in self._name_to_entry:
            original_name = self._name_to_entry[upper_name][0]
            self._name_to_entry[upper_name] = (original_name, new_anchor)
            return True
        return False

    def _ensure_sorted(self) -> None:
        """Sort the keys list if needed."""
        if self._dirty:
            self._sorted_keys.sort()
            self._dirty = False

    def get(self, name: str) -> Optional[AnchorBase]:
        """Get an anchor by exact name (case-insensitive)."""
        entry = self._name_to_entry.get(name.upper())
        return entry[1] if entry is not None else None

    def startswith(self, text: str, max_results: int = 50) -> list[tuple[str, AnchorBase]]:
        """Find names starting with the given text using binary search."""
        self._ensure_sorted()

        if not text:
            # Return first N entries
            return [
                (self._name_to_entry[key][0], self._name_to_entry[key][1]) for key in self._sorted_keys[:max_results]
            ]

        upper_text = text.upper()

        # Binary search for first matching entry
        idx = bisect.bisect_left(self._sorted_keys, upper_text)

        result = []
        while idx < len(self._sorted_keys) and len(result) < max_results:
            upper_name = self._sorted_keys[idx]
            if upper_name.startswith(upper_text):
                entry = self._name_to_entry[upper_name]
                result.append((entry[0], entry[1]))
                idx += 1
            else:
                break

        return result


class GlobalObjectsDB:
    def __init__(self) -> None:
        self.oids: list[Optional[AnchorBase]] = []

        # Catalog indexes for known catalogs
        registry = CatalogRegistry.get_instance()
        self._catalog_indexes: dict[str, CatalogIndex] = {}
        self._catalog_indexes_by_id: dict[int, CatalogIndex] = {}
        for catalog_prefix in registry.get_all_prefixes():
            catalog_index = CatalogIndex(catalog_prefix)
            self._catalog_indexes[catalog_prefix] = catalog_index
            catalog_id = registry.get_id(catalog_prefix)
            self._catalog_indexes_by_id[catalog_id] = catalog_index

        # General name index for non-catalog names
        self.name_index: NameIndex = NameIndex()

        # Alias name index
        self.alias_name_index: NameIndex = NameIndex(unique=True)

    def _sync_minor_planet_aliases(self, anchor: AnchorBase) -> None:
        """Add or update word-part aliases for any NT_minor_planet names in anchor."""
        object_names = anchor.get_names()
        for i in range(object_names.get_num_names()):
            name_entry = object_names.get_name_entry(i)
            if name_entry.type == ObjectName.NT_minor_planet:
                full_name = name_entry.get_full_name()
                space_pos = full_name.find(' ')
                if space_pos > 0:
                    alias = full_name[space_pos + 1 :]
                    if not self.alias_name_index.replace(alias, anchor):
                        self.alias_name_index.add(alias, anchor, display_name=full_name)

    def add(self, anchor: AnchorBase) -> None:
        anchor.oid = len(self.oids)
        anchor.oid_color = int_to_color(anchor.oid)
        self.oids.append(anchor)

        # Route names to appropriate indexes
        object_names = anchor.get_names()
        for i in range(object_names.get_num_names()):
            name_entry = object_names.get_name_entry(i)
            if name_entry.type == ObjectName.NT_catalog:
                catalog_index = self._catalog_indexes_by_id.get(name_entry.catalog_id)
                if catalog_index is not None:
                    catalog_index.add(name_entry.value, anchor)
                    continue
            self.name_index.add(name_entry.get_full_name(), anchor)

        # Also index pre-translation originals so they remain searchable.
        # get_source_names() returns both non-translatable full names (already handled
        # above via ObjectName entries) and originals of translated names. Only the
        # latter differ from get_all_names(),
        current_names = set(object_names.get_all_names())
        for source_name in anchor.get_source_names():
            if source_name not in current_names:
                self.name_index.add(source_name, anchor)

        # Add aliases for minor planet names
        self._sync_minor_planet_aliases(anchor)

    def add_name_for(self, anchor: AnchorBase, name: str, object_name: ObjectName) -> None:
        # Route name to appropriate index
        if object_name.type == ObjectName.NT_catalog:
            catalog_index = self._catalog_indexes_by_id.get(object_name.catalog_id)
            if catalog_index is not None:
                catalog_index.add(object_name.value, anchor)

        # Always add to general name index (the translated form must be searchable).
        self.name_index.add(name, anchor)

        # If it's a minor planet name, also add or update the alias index so that
        # the translated word-part (e.g. "Cérès" from "1 Cérès") is searchable.
        if object_name.type == ObjectName.NT_minor_planet:
            alias_space = name.find(' ')
            if alias_space > 0:
                alias = name[alias_space + 1 :]
                if not self.alias_name_index.replace(alias, anchor):
                    self.alias_name_index.add(alias, anchor, display_name=name)

    def get(self, name: str) -> Optional[AnchorBase]:
        """Get anchor by exact name using indexes (O(log N) lookup)."""
        if not name:
            return None

        # Check if it's a catalog name (PREFIX + space + ID)
        space_pos = name.find(' ')
        if space_pos > 0:
            prefix = name[:space_pos].upper()
            if prefix in self._catalog_indexes:
                catalog_id = name[space_pos + 1 :]
                return self._catalog_indexes[prefix].get(catalog_id)

        # Search in the primary name index first
        result = self.name_index.get(name)
        if result is not None:
            return result

        # Fall back to the alias index
        # This ensures aliases never hide objects with the same primary name
        return self.alias_name_index.get(name)

    def get_body(self, name: str) -> Optional[StellarObject]:
        """Get the StellarObject of the anchor registered under the given name.
        Returns None if no anchor is found for the given name.
        """
        anchor = self.get(name)
        return anchor.body if anchor is not None else None

    def get_oid(self, oid: int) -> Optional[AnchorBase]:
        """Get the anchor registered under the given oid."""
        if oid < len(self.oids):
            return self.oids[oid]
        else:
            return None

    def get_oid_body(self, oid: int) -> Optional[StellarObject]:
        """Get the StellarObject of the anchor registered under the given oid.
        Returns None if no anchor is found for the given oid.
        """
        anchor = self.get_oid(oid)
        return anchor.body if anchor is not None else None

    def remove(self, anchor: AnchorBase) -> None:
        """
        Remove an anchor from the database.
        Note: This marks the anchor as removed but doesn't actually delete from indexes
        to avoid complexity of index maintenance. The OID slot is set to None.
        """
        self.oids[anchor.oid] = None

    def replace(self, old_anchor: AnchorBase, new_anchor: AnchorBase) -> None:
        """
        Replace old_anchor with new_anchor in all indexes.
        All names that pointed to old_anchor will now point to new_anchor.
        new_anchor must already have all the desired names set before calling this.
        """
        self.oids[old_anchor.oid] = None  # Clear old anchor reference

        # Update indexes
        object_names = new_anchor.get_names()
        for i in range(object_names.get_num_names()):
            name_entry = object_names.get_name_entry(i)
            if name_entry.type == ObjectName.NT_catalog:
                catalog_index = self._catalog_indexes_by_id.get(name_entry.catalog_id)
                if catalog_index is not None:
                    upper_id = name_entry.value.upper()
                    if upper_id in catalog_index._id_to_anchor:
                        catalog_index.replace(name_entry.value, new_anchor)
                    else:
                        catalog_index.add(name_entry.value, new_anchor)
                    continue
            full_name = name_entry.get_full_name()
            if not self.name_index.replace(full_name, new_anchor):
                self.name_index.add(full_name, new_anchor)

        # Update pre-translation originals (same filter logic as add()).
        current_names = set(object_names.get_all_names())
        for source_name in new_anchor.get_source_names():
            if source_name not in current_names:
                if not self.name_index.replace(source_name, new_anchor):
                    self.name_index.add(source_name, new_anchor)

        # Update alias index for minor planet names
        self._sync_minor_planet_aliases(new_anchor)

    def startswith(self, text: str, max_results: int = 50) -> list[tuple[str, AnchorBase]]:
        """
        Find objects whose names start with the given text.
        Uses catalog-aware search for better performance.
        """
        if not text:
            return []

        text = text.strip()
        upper_text = text.upper()
        result = []

        # Check if it's a catalog query (e.g., "HIP 32")
        space_pos = text.find(' ')
        if space_pos > 0:
            prefix = text[:space_pos].upper()
            if prefix in self._catalog_indexes:
                # It's a catalog query with ID prefix
                id_prefix = text[space_pos + 1 :]
                return self._catalog_indexes[prefix].startswith(id_prefix, max_results)

        # Check if the text itself is a catalog prefix (e.g., "HIP")
        if upper_text in self._catalog_indexes:
            # Return first entries from that catalog
            result.extend(self._catalog_indexes[upper_text].startswith('', max_results))
            if len(result) >= max_results:
                return result[:max_results]

        # Check for partial catalog prefix match (e.g., "HI" matches "HIP")
        for catalog_prefix in self._catalog_indexes:
            if catalog_prefix.startswith(upper_text):
                # Add some results from this catalog
                # Use a small fraction of max_results to allow results from multiple matching catalogs
                catalog_sample_size = max_results // 3
                catalog_results = self._catalog_indexes[catalog_prefix].startswith('', catalog_sample_size)
                result.extend(catalog_results)
                if len(result) >= max_results:
                    return result[:max_results]

        # Search in general name index
        name_results = self.name_index.startswith(text, max_results - len(result))
        result.extend(name_results)

        # Search in alias name index
        alias_results = self.alias_name_index.startswith(text, max_results - len(result))
        result.extend(alias_results)

        # Sort and deduplicate by anchor identity, then limit results
        seen_anchors: set[int] = set()
        deduped = []
        for name, anchor in result:
            anchor_id = id(anchor)
            if anchor_id not in seen_anchors:
                seen_anchors.add(anchor_id)
                deduped.append((name, anchor))
        deduped.sort(key=lambda x: x[0].upper())
        return deduped[:max_results]


objectsDB = GlobalObjectsDB()
