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


import pytest

from cosmonium.catalogs import CatalogIndex, NameIndex, GlobalObjectsDB
from cosmonium.engine.objectname import CatalogRegistry


class MockBody:
    """Mock object to simulate a celestial body for testing."""

    def __init__(self, names, source_names=None):
        self._names = names if isinstance(names, list) else [names]
        self._source_names = source_names if source_names else []
        self.oid = None
        self.oid_color = None

    def get_names(self):
        return self._names

    def get_source_names(self):
        return self._source_names

    def get_name_from_upper(self, upper_name):
        """Return the original name case from an uppercase version."""
        for name in self._names + self._source_names:
            if name.upper() == upper_name:
                return name
        return upper_name


class TestCatalogIndex:
    """Test the CatalogIndex class for efficient catalog lookups."""

    def test_add_and_get(self):
        """Test adding and retrieving catalog entries."""
        index = CatalogIndex("HIP")
        body1 = MockBody("HIP 32349")
        body2 = MockBody("HIP 1234")

        index.add("32349", body1)
        index.add("1234", body2)

        assert index.get("32349") == body1
        assert index.get("1234") == body2
        assert index.get("99999") is None

    def test_get_case_insensitive(self):
        """Test that get() is case-insensitive."""
        index = CatalogIndex("CDM")
        body = MockBody("CCDM J14396-6050C")
        index.add("J14396-6050C", body)

        assert index.get("J14396-6050C") == body
        assert index.get("j14396-6050C") == body
        assert index.get("j14396-6050c") == body

    def test_startswith_numeric(self):
        """Test startswith with numeric IDs."""
        index = CatalogIndex("HIP")
        body1 = MockBody("HIP 1234")
        body2 = MockBody("HIP 1235")
        body3 = MockBody("HIP 5678")
        body4 = MockBody("HIP 12350")

        index.add("1234", body1)
        index.add("1235", body2)
        index.add("5678", body3)
        index.add("12350", body4)

        results = index.startswith("123")
        assert len(results) == 3
        assert results[0][0] == "HIP 1234"
        assert results[1][0] == "HIP 1235"
        assert results[2][0] == "HIP 12350"

    def test_startswith_empty(self):
        """Test startswith with empty prefix returns first entries."""
        index = CatalogIndex("HIP")
        body1 = MockBody("HIP 1")
        body2 = MockBody("HIP 2")

        index.add("1", body1)
        index.add("2", body2)

        results = index.startswith("")
        assert len(results) == 2
        assert results[0][0] == "HIP 1"
        assert results[1][0] == "HIP 2"

    def test_startswith_max_results(self):
        """Test that startswith respects max_results limit."""
        index = CatalogIndex("HIP")
        for i in range(10):
            body = MockBody(f"HIP {i}")
            index.add(str(i), body)

        results = index.startswith("", max_results=2)
        assert len(results) == 2
        assert results[0][0] == "HIP 0"
        assert results[1][0] == "HIP 1"

    def test_sorted_order(self):
        """Test that results are sorted."""
        index = CatalogIndex("HIP")
        # Add in random order
        for id_str in ["100", "50", "1", "25", "200"]:
            body = MockBody(f"HIP {id_str}")
            index.add(id_str, body)

        results = index.startswith("")
        # NOTE: The IDs are still strings, so they will be sorted lexicographically, not numerically
        # ids = [int(r[0].split()[1]) for r in results]
        ids = [r[0].split()[1] for r in results]
        assert ids == sorted(ids)


class TestNameIndex:
    """Test the NameIndex class for efficient name lookups."""

    def test_add_and_get(self):
        """Test adding and retrieving name entries."""
        index = NameIndex()
        body1 = MockBody("Sirius")
        body2 = MockBody("Betelgeuse")

        index.add("Sirius", body1)
        index.add("Betelgeuse", body2)

        assert index.get("Sirius") == body1
        assert index.get("Betelgeuse") == body2
        assert index.get("Rigel") is None

    def test_get_case_insensitive(self):
        """Test that get() is case-insensitive."""
        index = NameIndex()
        body = MockBody("Sirius")
        index.add("Sirius", body)

        assert index.get("sirius") == body
        assert index.get("SIRIUS") == body
        assert index.get("SiRiUs") == body

    def test_get_search(self):
        """Test that get() properly search names."""
        index = NameIndex()
        names = ["Alpha", "Beta", "Gamma", "Delta", "Epsilon", "Zeta"]
        bodies = [MockBody(name) for name in names]

        for name, body in zip(names, bodies):
            index.add(name, body)

        # Test retrieval
        assert index.get("Beta") == bodies[1]
        assert index.get("Zeta") == bodies[5]
        assert index.get("Alpha") == bodies[0]

    def test_startswith(self):
        """Test startswith with various prefixes."""
        index = NameIndex()
        names = ["Sirius", "Sigma", "Sol", "Betelgeuse", "Beta"]
        bodies = [MockBody(name) for name in names]

        for name, body in zip(names, bodies):
            index.add(name, body)

        results = index.startswith("S")
        result_names = [r[0] for r in results]
        assert len(results) == 3
        assert result_names == ["Sigma", "Sirius", "Sol"]  # Should be in alphabetical order

    def test_startswith_case_insensitive(self):
        """Test that startswith is case-insensitive."""
        index = NameIndex()
        body = MockBody("Sirius")
        index.add("Sirius", body)

        results = index.startswith("sir")
        assert len(results) == 1
        assert results[0][0] == "Sirius"

    def test_startswith_max_results(self):
        """Test that startswith respects max_results limit."""
        index = NameIndex()
        for i in range(100):
            body = MockBody(f"Star{i}")
            index.add(f"Star{i}", body)

        results = index.startswith("Star", max_results=2)
        assert len(results) == 2
        assert results[0][0] == "Star0"
        assert results[1][0] == "Star1"

    def test_sorted_order(self):
        """Test that results are in alphabetical order."""
        index = NameIndex()
        names = ["Zeta", "Alpha", "Beta", "Gamma"]
        for name in names:
            body = MockBody(name)
            index.add(name, body)

        results = index.startswith("")
        assert len(results) == 4
        assert results[0][0] == "Alpha"
        assert results[1][0] == "Beta"
        assert results[2][0] == "Gamma"
        assert results[3][0] == "Zeta"

        # Test with a prefix that matches all
        for name in names:
            body = MockBody(name + "Star")
            index.add(name + "Star", body)

        results = index.startswith("A")
        assert len(results) == 2
        assert results[0][0] == "Alpha"
        assert results[1][0] == "AlphaStar"


class TestGlobalObjectsDB:
    """Test the GlobalObjectsDB class for global object lookups."""

    @pytest.fixture
    def registry(self):
        """Create a fresh CatalogRegistry."""
        registry = CatalogRegistry.get_instance()
        registry.clear()  # Clear any existing catalogs
        registry.register_catalog("HIP", "Hipparcos Catalog")
        registry.register_catalog("NGC", "New General Catalog")
        return registry

    @pytest.fixture
    def db(self):
        """Create a fresh GlobalObjectsDB for each test."""
        return GlobalObjectsDB()

    def test_add_and_get(self, db, registry):
        """Test adding and retrieving objects."""
        body = MockBody("Sirius", ["HIP 32349"])
        db.add(body)

        assert db.get("Sirius") == body
        assert db.get("HIP 32349") == body
        assert db.get("sirius") == body  # Case-insensitive

    def test_get_non_existent(self, db):
        """Test getting a non-existent object returns None."""
        assert db.get("NonExistent") is None

    def test_catalog_routing(self, db, registry):
        """Test that catalog names are routed to catalog indexes and names to name index."""
        body1 = MockBody("HIP 32349")
        body2 = MockBody("NGC 224")
        body3 = MockBody("Sirius")

        db.add(body1)
        db.add(body2)
        db.add(body3)

        assert db.get("HIP 32349") == body1
        assert db.catalog_indexes["HIP"].get("32349") == body1
        assert db.get("NGC 224") == body2
        assert db.catalog_indexes["NGC"].get("224") == body2
        assert db.get("Sirius") == body3
        assert db.name_index.get("Sirius") == body3

    def test_startswith_catalog(self, db, registry):
        """Test startswith with catalog queries."""
        for i in range(10):
            body = MockBody(f"HIP {i}")
            db.add(body)

        results = db.startswith("HIP 1")
        assert len(results) > 0
        # Should find HIP 1
        result_names = [r[0] for r in results]
        assert "HIP 1" in result_names

    def test_startswith_name(self, db):
        """Test startswith with regular names."""
        body1 = MockBody("Sirius")
        body2 = MockBody("Sigma")
        body3 = MockBody("Betelgeuse")

        db.add(body1)
        db.add(body2)
        db.add(body3)

        results = db.startswith("S")
        result_names = [r[0] for r in results]
        assert len(result_names) >= 2
        assert "Sirius" in result_names
        assert "Sigma" in result_names

    def test_startswith_max_results(self, db):
        """Test that startswith respects max_results."""
        for i in range(100):
            body = MockBody(f"Star{i}")
            db.add(body)

        results = db.startswith("Star", max_results=10)
        assert len(results) <= 10

    @pytest.mark.skip(reason="Remove method not fully implemented yet")
    def test_remove(self, db):
        """Test removing an object."""
        body = MockBody("Sirius")
        db.add(body)

        assert db.get("Sirius") == body
        db.remove(body)
        assert db.get("Sirius") is None

    def test_oid_assignment(self, db):
        """Test that OIDs are assigned correctly."""
        body1 = MockBody("Star1")
        body2 = MockBody("Star2")

        db.add(body1)
        db.add(body2)

        assert body1.oid == 0
        assert body2.oid == 1
        assert db.get_oid(0) == body1
        assert db.get_oid(1) == body2
