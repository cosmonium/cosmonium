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

from cosmonium.catalogs import CatalogIndex, GlobalObjectsDB, NameIndex
from cosmonium.engine.objectname import CatalogRegistry, ObjectName, ObjectNames


class MockBody:
    """Mock object to simulate a celestial body for testing."""

    def __init__(self, names, source_names=None, reflective=False):
        raw_names = names if isinstance(names, list) else [names]
        extra_names = source_names if source_names else []
        self.oid = None
        self.oid_color = None
        self._object_names = ObjectNames()
        for name in raw_names + extra_names:
            self._object_names.add_name(ObjectNames.parse_name(name, reflective=reflective))

    def get_names(self):
        return self._object_names

    def get_source_names(self):
        return self._object_names.get_source_names()

    def get_name_from_upper(self, upper_name):
        """Return the original name case from an uppercase version."""
        for name in self._object_names.get_all_names() + self._object_names.get_source_names():
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
    def db(self, registry):
        """Create a fresh GlobalObjectsDB for each test (after registry is set up)."""
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
        assert db._catalog_indexes["HIP"].get("32349") == body1
        assert db.get("NGC 224") == body2
        assert db._catalog_indexes["NGC"].get("224") == body2
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


class TestAliasNameIndex:
    """Test the NameIndex class used as an alias index (unique=True)."""

    def test_add_and_get(self):
        """Test adding and retrieving alias entries."""
        index = NameIndex(unique=True)
        body = MockBody("1 Ceres", reflective=True)
        index.add("Ceres", body, display_name="1 Ceres")

        assert index.get("Ceres") == body
        assert index.get("CERES") == body  # Case-insensitive
        assert index.get("ceres") == body
        assert index.get("Vesta") is None

    def test_startswith(self):
        """Test startswith returns display_name, not alias."""
        index = NameIndex(unique=True)
        body1 = MockBody("1 Ceres", reflective=True)
        body2 = MockBody("4 Vesta", reflective=True)
        index.add("Ceres", body1, display_name="1 Ceres")
        index.add("Vesta", body2, display_name="4 Vesta")

        results = index.startswith("C")
        assert len(results) == 1
        assert results[0][0] == "1 Ceres"
        assert results[0][1] == body1

    def test_startswith_case_insensitive(self):
        """Test that startswith is case-insensitive."""
        index = NameIndex(unique=True)
        body = MockBody("1 Ceres", reflective=True)
        index.add("Ceres", body, display_name="1 Ceres")

        results = index.startswith("cer")
        assert len(results) == 1
        assert results[0][0] == "1 Ceres"

    def test_replace(self):
        """Test replacing a body in the alias index."""
        index = NameIndex(unique=True)
        body1 = MockBody("1 Ceres", reflective=True)
        body2 = MockBody("1 Ceres", reflective=True)
        index.add("Ceres", body1, display_name="1 Ceres")

        assert index.replace("Ceres", body2) is True
        assert index.get("Ceres") == body2

    def test_replace_nonexistent(self):
        """Test replacing a non-existent alias returns False."""
        index = NameIndex(unique=True)
        body = MockBody("1 Ceres", reflective=True)
        assert index.replace("Ceres", body) is False

    def test_unique_no_duplicate_keys(self):
        """Adding the same alias twice must not create a duplicate key."""
        index = NameIndex(unique=True)
        body1 = MockBody("1 Ceres", reflective=True)
        body2 = MockBody("1 Ceres", reflective=True)
        index.add("Ceres", body1, display_name="1 Ceres")
        index.add("Ceres", body2, display_name="1 Ceres")  # second add, same key

        # Only one entry in sorted_keys
        assert index._sorted_keys.count("CERES") == 1
        # Latest body wins
        assert index.get("Ceres") == body2

    def test_non_unique_allows_duplicate_keys(self):
        """Default NameIndex (unique=False) appends duplicate keys."""
        index = NameIndex()  # unique=False
        body1 = MockBody("Sirius")
        body2 = MockBody("Sirius")
        index.add("Sirius", body1)
        index.add("Sirius", body2)

        # Two entries in sorted_keys (duplicates allowed)
        assert index._sorted_keys.count("SIRIUS") == 2
        # get() returns the last-written body
        assert index.get("Sirius") == body2
        # startswith() returns two separate entries
        results = index.startswith("Sirius")
        assert len(results) == 2


class TestMinorPlanetAliases:
    """Test minor planet alias search in GlobalObjectsDB."""

    @pytest.fixture
    def registry(self):
        """Create a fresh CatalogRegistry."""
        registry = CatalogRegistry.get_instance()
        registry.clear()
        registry.register_catalog("HIP", "Hipparcos Catalog")
        return registry

    @pytest.fixture
    def db(self):
        """Create a fresh GlobalObjectsDB for each test."""
        return GlobalObjectsDB()

    def test_get_by_full_name(self, db, registry):
        """Minor planet can be found by its full name."""
        ceres = MockBody("1 Ceres", reflective=True)
        db.add(ceres)
        assert db.get("1 Ceres") == ceres

    def test_get_by_alias(self, db, registry):
        """Minor planet can be found by its word-part alias."""
        ceres = MockBody("1 Ceres", reflective=True)
        db.add(ceres)
        assert db.get("Ceres") == ceres
        assert db.get("ceres") == ceres  # Case-insensitive

    def test_alias_does_not_hide_primary_name(self, db, registry):
        """When a primary-named object shares a name with a minor planet alias,
        the primary name wins in exact-match search."""
        moon_europa = MockBody("Europa")
        asteroid_europa = MockBody("52 Europa", reflective=True)

        db.add(moon_europa)
        db.add(asteroid_europa)

        # Exact search for "Europa" must return the moon, not the asteroid
        assert db.get("Europa") == moon_europa
        # Full name still finds the asteroid
        assert db.get("52 Europa") == asteroid_europa

    def test_startswith_by_alias_prefix(self, db, registry):
        """Prefix search finds a minor planet via its alias."""
        ceres = MockBody("1 Ceres", reflective=True)
        db.add(ceres)

        results = db.startswith("Cere")
        result_names = [r[0] for r in results]
        assert "1 Ceres" in result_names

    def test_startswith_includes_both_moon_and_asteroid(self, db, registry):
        """Prefix search returns both the moon and the asteroid when
        the search text matches both."""
        moon_europa = MockBody("Europa")
        asteroid_europa = MockBody("52 Europa", reflective=True)

        db.add(moon_europa)
        db.add(asteroid_europa)

        results = db.startswith("Europa")
        result_names = [r[0] for r in results]
        assert "Europa" in result_names
        assert "52 Europa" in result_names

    def test_startswith_alias_deduplication(self, db, registry):
        """A minor planet found by both its full name prefix and alias
        should appear only once in the results."""
        ceres = MockBody("1 Ceres", reflective=True)
        db.add(ceres)

        # "1 " won't match alias "Ceres", so no duplicate here
        results_alias = db.startswith("Cere")
        bodies = [r[1] for r in results_alias]
        assert bodies.count(ceres) == 1

    def test_no_alias_for_non_minor_planet(self, db, registry):
        """Regular vernacular names do not produce aliases."""
        star = MockBody("Sirius")
        db.add(star)

        # There should be no alias entry
        assert db.alias_name_index.get("Sirius") is None
        assert db.get("Sirius") == star

    def test_multiple_minor_planets(self, db, registry):
        """Multiple minor planets can each be found by their alias."""
        ceres = MockBody("1 Ceres", reflective=True)
        vesta = MockBody("4 Vesta", reflective=True)
        pallas = MockBody("2 Pallas", reflective=True)

        db.add(ceres)
        db.add(vesta)
        db.add(pallas)

        assert db.get("Ceres") == ceres
        assert db.get("Vesta") == vesta
        assert db.get("Pallas") == pallas

    def test_startswith_multiple_aliases(self, db, registry):
        """Prefix search finds multiple minor planets sharing a prefix."""
        ceres = MockBody("1 Ceres", reflective=True)
        cerberus = MockBody("1865 Cerberus", reflective=True)
        db.add(ceres)
        db.add(cerberus)

        results = db.startswith("Cer")
        result_names = [r[0] for r in results]
        assert "1 Ceres" in result_names
        assert "1865 Cerberus" in result_names

    def test_add_name_for_minor_planet_registers_alias(self, db, registry):
        """add_name_for() with an NT_minor_planet ObjectName must add the translated
        word-part alias so that the body can be found by the translated alias."""
        ceres = MockBody("1 Ceres", reflective=True)
        object_name_entry = ObjectName.make_minor_planet("1 Ceres")
        db.add(ceres)

        translated_name = "1 Cérès"
        db.add_name_for(ceres, translated_name, object_name_entry)

        # The translated full name must be retrievable directly
        assert db.get("1 Cérès") == ceres
        # The translated alias (word-part after the number) must be registered
        assert db.alias_name_index.get("Cérès") == ceres
        assert db.get("Cérès") == ceres
        # Prefix search via translated alias must also work
        results = db.startswith("Cérè")
        result_names = [r[0] for r in results]
        assert "1 Cérès" in result_names

    def test_add_name_for_non_minor_planet_no_alias(self, db, registry):
        """add_name_for() with a non-minor-planet one must not add anything to
        the alias index."""
        star = MockBody("Sirius")
        object_name_entry = ObjectName.make_vernacular("Sirius")
        db.add(star)

        db.add_name_for(star, "Sirios", object_name_entry)

        assert db.alias_name_index.get("Sirios") is None
        assert db.get("Sirios") == star
