# Engine Unit Tests

This directory contains unit tests covering functionalities related to the engine of Cosmonium.

## Test Coverage

### 1. Object Name Tests (`test_objectname.py`)

Tests for the object naming and catalog system:

- **TestCatalogRegistry**: Tests catalog registration, auto-assigned IDs, prefix and ID retrieval, and catalog existence checks.
- **TestObjectNameParsing**: Tests parsing of various name types including vernacular names, catalog entries (HIP, HD, etc.), Bayer designations, Flamsteed designations, and empty names.
- **TestObjectNames**: Tests ObjectNames collection management including adding/retrieving names, friendly names, C names, source names, catalog-specific names, and catalog entry checks.
- **TestFactoryMethods**: Tests factory methods for creating vernacular, Bayer, and catalog name objects.

### 2. Catalog Tests (`test_catalogs.py`)

Tests for the catalog indexing and global object database system:

- **TestCatalogIndex**: Tests the `CatalogIndex` class, including adding/retrieving entries, case-insensitive lookups, prefix-based searches using bisect, handling empty prefixes, max results limits, and sorted order of results.
- **TestNameIndex**: Tests the `NameIndex` class, including adding/retrieving names, case-insensitive searches, prefix matching, max results enforcement, and alphabetical sorting of results.
- **TestGlobalObjectsDB**: Tests the `GlobalObjectsDB` class, including adding objects, routing names to appropriate indexes (catalog vs. general), prefix searches across catalogs and names, OID assignment, and retrieval by OID.