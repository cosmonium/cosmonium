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
import bisect
from typing import Any, Optional

from .engine.objectname import CatalogRegistry
from .utils import int_to_color


class CatalogIndex:
    """Index for catalog entries with efficient prefix search."""

    def __init__(self, catalog_prefix: str) -> None:
        self.catalog_prefix: str = catalog_prefix
        self._sorted_ids: list[tuple[str, Any]] = []  # Sorted list of (catalog_id, body) tuples
        self._id_to_body: dict[str, Any] = {}  # Dict for exact lookup
        self._dirty: bool = False

    def add(self, catalog_id: str, body: Any) -> None:
        """Add a catalog entry."""
        upper_id = catalog_id.upper()
        self._sorted_ids.append((upper_id, body))
        self._id_to_body[upper_id] = body
        self._dirty = True

    def _ensure_sorted(self) -> None:
        """Sort the list if needed."""
        if self._dirty:
            self._sorted_ids.sort(key=lambda x: x[0])
            self._dirty = False

    def get(self, catalog_id: str) -> Optional[Any]:
        """Get a body by exact catalog ID."""
        return self._id_to_body.get(catalog_id.upper())

    def startswith(self, id_prefix: str, max_results: int = 50) -> list[tuple[str, Any]]:
        """
        Find catalog entries where the ID starts with the given prefix.
        Uses bisect for efficient binary search.
        """
        self._ensure_sorted()

        if not id_prefix:
            # Return first N entries
            return [(f"{self.catalog_prefix} {entry[0]}", entry[1]) for entry in self._sorted_ids[:max_results]]

        upper_prefix = id_prefix.upper()

        # Use bisect to find the leftmost position where upper_str_id >= upper_prefix
        idx = bisect.bisect_left(self._sorted_ids, upper_prefix, key=lambda x: x[0])

        result = []
        while idx < len(self._sorted_ids) and len(result) < max_results:
            upper_str_id, body = self._sorted_ids[idx]
            if upper_str_id.startswith(upper_prefix):
                result.append((f"{self.catalog_prefix} {upper_str_id}", body))
                idx += 1
            else:
                break

        return result


class NameIndex:
    """Index for name entries with efficient sorted search."""

    def __init__(self) -> None:
        self._entries: list[tuple[str, str, Any]] = []  # List of (UPPER_NAME, original_name, body) tuples
        self._dirty: bool = False

    def add(self, name: str, body: Any) -> None:
        """Add a name entry."""
        upper_name = name.upper()
        self._entries.append((upper_name, name, body))
        self._dirty = True

    def _ensure_sorted(self) -> None:
        """Sort the list if needed."""
        if self._dirty:
            self._entries.sort(key=lambda x: x[0])
            self._dirty = False

    def get(self, name: str) -> Optional[Any]:
        """Get a body by exact name (case-insensitive) using binary search."""
        self._ensure_sorted()
        upper_name = name.upper()

        # Use binary search to find exact match
        idx = bisect.bisect_left(self._entries, (upper_name, '', None))

        # Check if we found an exact match
        if idx < len(self._entries) and self._entries[idx][0] == upper_name:
            return self._entries[idx][2]  # Return the body

        return None

    def startswith(self, text: str, max_results: int = 50) -> list[tuple[str, Any]]:
        """Find names starting with the given text using binary search."""
        self._ensure_sorted()

        if not text:
            # Return first N entries
            return [(entry[1], entry[2]) for entry in self._entries[:max_results]]

        upper_text = text.upper()

        # Binary search for first matching entry
        idx = bisect.bisect_left(self._entries, (upper_text, '', None))

        result = []
        while idx < len(self._entries) and len(result) < max_results:
            entry_upper, entry_name, body = self._entries[idx]
            if entry_upper.startswith(upper_text):
                result.append((entry_name, body))
                idx += 1
            else:
                break

        return result


class GlobalObjectsDB:
    def __init__(self) -> None:
        self.oids: list[Optional[Any]] = []

        # Catalog indexes for known catalogs
        registry = CatalogRegistry.get_instance()
        self.catalog_indexes: dict[str, CatalogIndex] = {}
        for catalog_prefix in registry.get_all_prefixes():
            self.catalog_indexes[catalog_prefix] = CatalogIndex(catalog_prefix)

        # General name index for non-catalog names
        self.name_index: NameIndex = NameIndex()

    def add(self, body: Any) -> None:
        body.oid = len(self.oids)
        body.oid_color = int_to_color(body.oid)
        self.oids.append(body)

        # Route names to appropriate indexes
        all_names = set(body.get_names() + body.get_source_names())
        for name in all_names:
            # Check if it's a catalog name (PREFIX + space + ID)
            space_pos = name.find(' ')
            if space_pos > 0:
                prefix = name[:space_pos].upper()
                if prefix in self.catalog_indexes:
                    catalog_id = name[space_pos + 1 :]
                    self.catalog_indexes[prefix].add(catalog_id, body)
                    continue

            # Add to general name index
            self.name_index.add(name, body)

    def get(self, name: str) -> Optional[Any]:
        """Get body by exact name using indexes (O(log N) lookup)."""
        if not name:
            return None

        # Check if it's a catalog name (PREFIX + space + ID)
        space_pos = name.find(' ')
        if space_pos > 0:
            prefix = name[:space_pos].upper()
            if prefix in self.catalog_indexes:
                catalog_id = name[space_pos + 1 :]
                return self.catalog_indexes[prefix].get(catalog_id)

        # Otherwise search in the name index
        return self.name_index.get(name)

    def get_oid(self, oid: int) -> Optional[Any]:
        if oid < len(self.oids):
            return self.oids[oid]
        else:
            return None

    def remove(self, body: Any) -> None:
        """
        Remove a body from the database.
        Note: This marks the body as removed but doesn't actually delete from indexes
        to avoid complexity of index maintenance. The OID slot is set to None.
        """
        self.oids[body.oid] = None

    def replace(self, old_body: Any, new_body: Any) -> None:
        """
        Replace old_body with new_body in all indexes.
        All names that pointed to old_body will now point to new_body.
        new_body must already have all the desired names set before calling this.
        """
        self.oids[old_body.oid] = None  # Clear old body reference

        # Update catalog indexes: replace old_body with new_body for all names
        all_names = set(new_body.get_names() + new_body.get_source_names())
        for name in all_names:
            space_pos = name.find(' ')
            if space_pos > 0:
                prefix = name[:space_pos].upper()
                if prefix in self.catalog_indexes:
                    catalog_id = name[space_pos + 1 :]
                    catalog_index = self.catalog_indexes[prefix]
                    upper_id = catalog_id.upper()
                    if upper_id in catalog_index._id_to_body:
                        # Update the dict entry
                        catalog_index._id_to_body[upper_id] = new_body
                        # Update the sorted list entry
                        for i, (eid, _) in enumerate(catalog_index._sorted_ids):
                            if eid == upper_id:
                                catalog_index._sorted_ids[i] = (eid, new_body)
                                break
                    else:
                        catalog_index.add(catalog_id, new_body)
                    continue

            # Update the name index
            name_index = self.name_index
            upper_name = name.upper()
            found = False
            for i, (ename, _, _) in enumerate(name_index._entries):
                if ename == upper_name:
                    name_index._entries[i] = (ename, name_index._entries[i][1], new_body)
                    found = True
                    break
            if not found:
                name_index.add(name, new_body)

    def startswith(self, text: str, max_results: int = 50) -> list[tuple[str, Any]]:
        """
        Find objects whose names start with the given text.
        Uses catalog-aware search for better performance.
        """
        if not text:
            return []

        text = text.strip()
        upper_text = text.upper()
        result = []

        # Check if it's a catalog query (e.g., "HIP 32", "HIP ", "HI")
        space_pos = text.find(' ')
        if space_pos > 0:
            prefix = text[:space_pos].upper()
            if prefix in self.catalog_indexes:
                # It's a catalog query with ID prefix
                id_prefix = text[space_pos + 1 :]
                return self.catalog_indexes[prefix].startswith(id_prefix, max_results)

        # Check if the text itself is a catalog prefix (e.g., "HIP")
        if upper_text in self.catalog_indexes:
            # Return first entries from that catalog
            result.extend(self.catalog_indexes[upper_text].startswith('', max_results))
            if len(result) >= max_results:
                return result[:max_results]

        # Check for partial catalog prefix match (e.g., "HI" matches "HIP")
        for catalog_prefix in self.catalog_indexes:
            if catalog_prefix.startswith(upper_text):
                # Add some results from this catalog
                # Use a small fraction of max_results to allow results from multiple matching catalogs
                catalog_sample_size = max_results // 3
                catalog_results = self.catalog_indexes[catalog_prefix].startswith('', catalog_sample_size)
                result.extend(catalog_results)
                if len(result) >= max_results:
                    return result[:max_results]

        # Search in general name index
        name_results = self.name_index.startswith(text, max_results - len(result))
        result.extend(name_results)

        # Sort and limit results
        result.sort(key=lambda x: x[0].upper())
        return result[:max_results]


objectsDB = GlobalObjectsDB()
