# tp-maya Tests

This directory contains tests for the tp-maya package, including unit tests and integration tests for the Maya metadata system.

## Test Types

### Unit Tests (`@pytest.mark.unit`)

Unit tests verify pure Python logic without requiring Maya. They can run with a standard Python interpreter and pytest.

**Important:** Only tests that don't import from `tp.libs.maya` modules can be true unit tests. Most of the meta package imports Maya modules transitively, so the majority of tests are integration tests.

```bash
# Run only unit tests (no Maya required)
pytest tests/ -m "not integration"
```

### Integration Tests (`@pytest.mark.integration`)

Integration tests require a Maya environment and must be run using `mayapy` (Maya's Python interpreter). They test actual Maya functionality including:

- Node creation and manipulation
- Attribute handling
- Scene graph connections
- Meta node hierarchies

## Running Tests

### Prerequisites

1. Maya must be installed
2. pytest must be installed in Maya's Python environment or accessible via PYTHONPATH

### Running with mayapy

The recommended way to run integration tests is using the provided test runner script:

```powershell
# Navigate to the tp-maya package directory
cd packages/tp-maya

# Run all tests
& "C:\Program Files\Autodesk\Maya2026\bin\mayapy.exe" scripts/run_maya_tests.py

# Run only integration tests
& "C:\Program Files\Autodesk\Maya2026\bin\mayapy.exe" scripts/run_maya_tests.py -m integration

# Run with verbose output
& "C:\Program Files\Autodesk\Maya2026\bin\mayapy.exe" scripts/run_maya_tests.py -v

# Run specific test file
& "C:\Program Files\Autodesk\Maya2026\bin\mayapy.exe" scripts/run_maya_tests.py tests/meta/test_meta_integration.py

# Run with coverage
& "C:\Program Files\Autodesk\Maya2026\bin\mayapy.exe" scripts/run_maya_tests.py --cov=tp.libs.maya.meta
```

Alternatively, you can run pytest directly with mayapy:

```powershell
& "C:\Program Files\Autodesk\Maya2026\bin\mayapy.exe" -m pytest tests/ -m integration
```

### Running Unit Tests Without Maya

Unit tests can be run with a standard Python environment:

```bash
# Run unit tests only
pytest tests/ -m "not integration"

# Or run specific unit test files
pytest tests/meta/test_registry_unit.py
```

## Test Fixtures

The `conftest.py` file provides several fixtures:

### `maya_session` (session-scoped)
Initializes Maya standalone at the start of the test session. Required for all integration tests.

### `new_scene` (function-scoped)
Creates a fresh Maya scene before each test and cleans up after. Depends on `maya_session`.

### `meta_registry_clean` (function-scoped)
Cleans the MetaRegistry before and after tests to ensure test isolation.

### `mock_maya_cmds`
Provides a mock `maya.cmds` module for unit testing without Maya.

## Test Organization

```
tests/
├── conftest.py              # Shared fixtures and pytest configuration
├── __init__.py
└── meta/
    ├── __init__.py
    ├── test_registry_unit.py      # Unit tests for MetaRegistry
    └── test_meta_integration.py   # Integration tests for metadata system
```

## Writing New Tests

### Unit Tests

```python
import pytest

@pytest.mark.unit
def test_example_unit():
    """Test that runs without Maya."""
    assert True
```

### Integration Tests

```python
import pytest

@pytest.mark.integration
def test_example_integration(new_scene):
    """Test that requires Maya."""
    from tp.libs.maya.meta.base import MetaBase
    
    meta = MetaBase(name="test")
    assert meta is not None
```

## Troubleshooting

### Maya not found
Ensure `mayapy` is in your PATH or use the full path to the Maya Python executable.

### Import errors
Make sure the tp-maya package and its dependencies are in Maya's PYTHONPATH.

### Test isolation issues
If tests are affecting each other, ensure you're using the `new_scene` and `meta_registry_clean` fixtures appropriately.

