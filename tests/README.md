# Cosmonium Unit Tests

This directory contains unit tests for the Cosmonium project.


## Running the Tests

### Prerequisites

Tests require Panda3D to be installed. Install the test dependencies:
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### Running All Tests

From the repository root directory:
```bash
pytest tests/
```


## Test Structure

Each test file follows this structure:
- **Mock Classes**: Lightweight objects that simulate the behavior of complex dependencies
- **Test Classes**: Organized by the class being tested
- **Test Methods**: Individual test cases with descriptive names


## Notes

- These tests should work with both C++ and Python implementation of the engine
- Tests should use **unittest.mock with create_autospec()** and **spec_set=True** to create proper mocks with type safety
- Tests should use Panda3D instead of mocks
- Tests must to be **fast** and **deterministic** for reliable CI/CD integration


## Contributing

When adding new tests:
1. Follow the existing naming conventions (`test_*.py` for files, `Test*`for classes, and `test_*` for methods)
2. Use descriptive test names that explain what is being tested
3. Include docstrings explaining the test's purpose
4. Except for Panda3D, mock external dependencies to keep tests fast and isolated
5. Group related tests into test classes
