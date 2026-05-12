# Parsers Unit Tests

This directory contains unit tests covering functionalities related to YAML parsing, configuration validation, and object loading for Cosmonium.

## Test Coverage

### 1. YAML Tests (`test_yaml.py`)

Tests for the loading and parsing infrastructure:

- **TestYamlLoader**: Tests YamlLoader I/O layer.

### 2. Object Parser Validation Tests (`test_object_parser_validation.py`)

Tests for ObjectYamlParser Pydantic validation integration:

- **TestObjectParserValidation**: Validates model registration, star and planet data validation, error handling, and fallback for unregistered types.

### 3. Schema Tests (`test_schemas.py`)

Tests for configuration schemas using Pydantic models:

- **TestOrbitSchemas**: Validates fixed and elliptic orbit configurations, including defaults.
- **TestRotationSchemas**: Tests uniform and fixed rotation configurations, including synchronous flags.
- **TestCelestialSchemas**: Covers star and planet configurations, with inline orbits, references, and nested surfaces.
- **TestSurfaceSchemas**: Validates appearance and surface configurations.
- **TestConfigBaseFeatures**: Tests to_dict() conversion and kebab-case aliases.
