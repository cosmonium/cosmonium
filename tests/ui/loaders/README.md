# User Interface Loaders Unit Tests

This directory contains unit tests covering functionalities related to the loaders module of the user interface of Cosmonium.

## Test Coverage

### 1. Parsers Tests (`test_parsers.py`)

This module contains comprehensive tests for all parser utilities used in UI configuration loading.

- **TestColorParser**: Tests for ColorParser.
- **TestLengthParser**: Tests for LengthParser.
- **TestAlignmentParser**: Tests for AlignmentParser.
- **TestBorderParser**: Tests for BorderParser.
- **TestGapParser**: Tests for GapParser.
- **TestTextAlignmentParser**: Tests for TextAlignmentParser.
- **TestParsersCollection**: Tests for ParsersCollection.


### 2. Integration Tests (`test_integration.py`)

This module contains integration tests that verify the loaders work with configuration files.

- **TestShortcutsLoader**: Tests for ShortcutsLoader with actual config files.
- **TestSkinLoader**: Tests for SkinLoader with actual config files.
- **TestDockLoader**: Tests for DockLoader with actual config files.
- **TestHUDLoader**:  Tests for HUDLoader with actual config files.
- **TestWidgetLoaders**: Tests for widget loaders.
