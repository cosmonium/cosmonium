# Test Structure

- `test_noisepythonparser.py` - Unit tests for noise Python parser
  - `TestBasicFunctionality` - Test basic parsing functionality
  - `TestBinaryOperators` - Test binary operators
  - `TestUnaryOperators` - Test unary operators
  - `TestFunctionCalls` - Test function calls
  - `TestSafety` - Test non supported syntax and safety features
  - `TestEquivalence` - Test equivalence between YAML and Python syntax
  - `TestIntegrationWithYamlParser` - Test integration with the YAML parser
  - `TestEdgeCases` - Test edge and corner cases
- `test_shadernoise.py` - Unit tests for shader noise (requires GPU with compute shaders support
  - `TestSimpleSources` - Test simple source of noise data
  - `TestArithmetic` - Test arithmetic operations
  - `TestMathFunctions` - Test basic math functions
