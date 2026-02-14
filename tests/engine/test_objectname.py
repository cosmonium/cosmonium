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

from cosmonium.engine.objectname import CatalogRegistry, ObjectName, ObjectNames


@pytest.fixture(scope="module")
def registry():
    """Fixture to provide a fresh CatalogRegistry instance for tests."""
    # Clear the registry before each test
    registry = CatalogRegistry.get_instance()
    registry.clear()
    catalogs = [
        ('HIP', 'Hipparcos Catalogue'),
        ('HD', 'Henry Draper Catalogue'),
        ('HR', 'Harvard Revised Photometry Catalogue'),
        ('SAO', 'Smithsonian Astrophysical Observatory Star Catalog'),
        ('TYC', 'Tycho Catalogue'),
        ('BD', 'Bonner Durchmusterung'),
        ('CD', 'Cordoba Durchmusterung'),
        ('NGC', 'New General Catalogue'),
        ('IC', 'Index Catalogue'),
        ('M', 'Messier Catalogue'),
        ('GJ', 'Gliese-Jahreiss Catalogue'),
        ('GL', 'Gliese Catalogue'),
        ('LHS', 'Luyten Half-Second Catalogue'),
        ('PGC', 'Principal Galaxies Catalogue'),
        ('UGC', 'Uppsala General Catalogue of Galaxies'),
        ('WDS', 'Washington Double Star Catalog'),
        ('CCDM', 'Catalogue of Components of Double and Multiple Stars'),
        ('ADS', 'Aitken Double Star Catalog'),
    ]
    for prefix, description in catalogs:
        registry.register_catalog(prefix, description)
    return registry


class TestCatalogRegistry:
    """Test the CatalogRegistry class."""

    def test_registry_instance(self, registry):
        """Test that we can get the registry instance."""
        assert len(registry.get_all_prefixes()) > 0

    def test_auto_assigned_ids(self, registry):
        """Test that IDs are auto-assigned in order."""
        # First few catalogs should have sequential IDs starting from 1
        hip_id = registry.get_id('HIP')
        hd_id = registry.get_id('HD')
        hr_id = registry.get_id('HR')
        assert hip_id == 1
        assert hd_id == 2
        assert hr_id == 3

    def test_get_prefix(self, registry):
        """Test getting prefix from ID."""
        assert registry.get_prefix(1) == 'HIP'
        assert registry.get_prefix(2) == 'HD'

    def test_has_catalog(self, registry):
        """Test checking if catalog exists."""
        assert registry.has_catalog('HIP')
        assert registry.has_catalog('NGC')
        assert not registry.has_catalog('NOTEXIST')


class TestObjectNameParsing:
    """Test name parsing functionality."""

    def test_parse_vernacular_name(self, registry):
        """Test parsing common vernacular names."""
        name = ObjectNames.parse_name("Sirius")
        assert name.type == ObjectName.NT_vernacular
        assert name.translatable
        assert name.value == "Sirius"
        assert name.get_full_name() == "Sirius"

    def test_parse_catalog_hip(self, registry):
        """Test parsing HIP catalog names."""
        name = ObjectNames.parse_name("HIP 32349")
        assert name.type == ObjectName.NT_catalog
        assert name.translatable is False
        assert name.catalog_id == registry.get_id('HIP')
        assert name.value == "32349"
        assert name.get_full_name() == "HIP 32349"

    def test_parse_catalog_hd(self, registry):
        """Test parsing HD catalog names."""
        name = ObjectNames.parse_name("HD 48915")
        assert name.type == ObjectName.NT_catalog
        assert name.translatable is False
        assert name.catalog_id == registry.get_id('HD')
        assert name.value == "48915"

    def test_parse_bayer_designation(self, registry):
        """Test parsing Bayer designations."""
        name = ObjectNames.parse_name("ALF CMa")
        assert name.type == ObjectName.NT_bayer
        assert name.translatable is False
        assert name.value == "ALF CMa"

    def test_parse_bayer_with_number(self, registry):
        """Test parsing Bayer designations with numbers."""
        name = ObjectNames.parse_name("BET2 Ori")
        assert name.type == ObjectName.NT_bayer
        assert name.translatable is False

    def test_parse_flamsteed(self, registry):
        """Test parsing Flamsteed designations."""
        name = ObjectNames.parse_name("51 Peg")
        assert name.type == ObjectName.NT_flamsteed
        assert name.translatable is False
        assert name.value == "51 Peg"

    def test_parse_empty_name(self, registry):
        """Test parsing empty name."""
        name = ObjectNames.parse_name("")
        assert name.type == ObjectName.NT_vernacular
        assert name.translatable


class TestObjectNames:
    """Test ObjectNames collection management."""

    def test_add_and_get_names(self, registry):
        """Test adding and retrieving names."""
        names = ObjectNames()
        names.add_name(ObjectNames.parse_name("Sirius"))
        names.add_name(ObjectNames.parse_name("HIP 32349"))

        assert names.get_num_names() == 2
        all_names = names.get_all_names()
        assert "Sirius" in all_names
        assert "HIP 32349" in all_names

    def test_get_friendly_name(self, registry):
        """Test getting the friendly name."""
        names = ObjectNames()
        names.add_name(ObjectNames.parse_name("Sirius"))
        names.add_name(ObjectNames.parse_name("HIP 32349"))
        names.add_name(ObjectNames.parse_name("ALF CMa"))

        # Should return first vernacular name
        assert names.get_friendly_name() == "Sirius"

    def test_get_c_name(self, registry):
        """Test getting the C name (first name untranslated)."""
        # Test with translated name
        names = ObjectNames()
        names.add_name(ObjectNames.parse_name("Sirio"), "Sirius")
        # Should return the original untranslated name
        assert names.get_c_name() == "Sirius"

        # Test without translation
        names2 = ObjectNames()
        names2.add_name(ObjectNames.parse_name("Alpha Centauri"))
        # Should return the name itself
        assert names2.get_c_name() == "Alpha Centauri"

        # Test with catalog name (no translation)
        names3 = ObjectNames()
        names3.add_name(ObjectNames.parse_name("HIP 32349"))
        # Should return the value without prefix
        assert names3.get_c_name() == "HIP 32349"

    def test_get_source_names(self, registry):
        """Test getting source names."""
        names = ObjectNames()
        names.add_name(ObjectNames.parse_name("Translated Name"), "Original Name")
        names.add_name(ObjectNames.parse_name("HIP 32349"))

        source_names = names.get_source_names()
        assert "Original Name" in source_names
        assert "HIP 32349" in source_names

    def test_get_catalog_names(self, registry):
        """Test getting names from specific catalog."""
        names = ObjectNames()
        names.add_name(ObjectNames.parse_name("HIP 32349"))
        names.add_name(ObjectNames.parse_name("HD 48915"))
        names.add_name(ObjectNames.parse_name("HR 2491"))

        hip_names = names.get_catalog_names(registry.get_id('HIP'))
        assert len(hip_names) == 1
        assert "HIP 32349" in hip_names

    def test_has_catalog_entry(self, registry):
        """Test checking for catalog entries."""
        names = ObjectNames()
        names.add_name(ObjectNames.parse_name("HIP 32349"))

        assert names.has_catalog_entry(registry.get_id('HIP'))
        assert not names.has_catalog_entry(registry.get_id('HD'))

    def test_get_catalog_id(self, registry):
        """Test getting catalog ID."""
        names = ObjectNames()
        names.add_name(ObjectNames.parse_name("HIP 32349"))

        catalog_id = names.get_catalog_id(registry.get_id('HIP'))
        assert catalog_id == "32349"


class TestFactoryMethods:
    """Test ObjectName factory methods."""

    def test_make_vernacular(self, registry):
        """Test making a vernacular name."""
        name = ObjectName.make_vernacular("Test Name")
        assert name.type == ObjectName.NT_vernacular
        assert name.translatable is True
        assert name.value == "Test Name"

    def test_make_bayer(self, registry):
        """Test making a Bayer designation."""
        name = ObjectName.make_bayer("ALF CMa")
        assert name.type == ObjectName.NT_bayer
        assert name.translatable is False

    def test_make_catalog(self, registry):
        """Test making a catalog name."""
        name = ObjectName.make_catalog(registry.get_id('HIP'), "32349")
        assert name.type == ObjectName.NT_catalog
        assert name.translatable is False
        assert name.catalog_id == registry.get_id('HIP')
        assert name.get_full_name() == "HIP 32349"
