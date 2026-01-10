# tp-tools-metahuman Tests

This directory contains tests for the tp-tools-metahuman package, including unit tests and integration tests for the MetaHuman body rig meta system.

## Test Types

### Unit Tests (`@pytest.mark.unit`)

Unit tests verify pure Python logic without requiring Maya. They can run with a standard Python interpreter and pytest.

**Important:** Only tests that don't import from Maya-dependent modules can be true unit tests. The `meta/constants.py` module is pure Python and can be tested without Maya.

```bash
# Run only unit tests (no Maya required)
pytest tests/ -m unit
```

### Integration Tests (`@pytest.mark.integration`)

Integration tests require a Maya environment and must be run using `mayapy` (Maya's Python interpreter). They test actual Maya functionality including:

- MetaNode creation and manipulation
- Attribute handling
- Meta layer hierarchies
- Rig metanode management

## Running Tests

### Prerequisites

1. Maya must be installed
2. The maya2026 virtual environment must be set up (see `dev/scripts/venv_setup.py`)
3. pytest must be installed in the maya2026 environment

### Running with mayapy

The recommended way to run integration tests is using the provided test runner script:

```powershell
# Navigate to the tp-tools-metahuman package directory
cd packages/tp-tools-metahuman

# Run all tests
& "C:\Program Files\Autodesk\Maya2026\bin\mayapy.exe" scripts/run_maya_tests.py

# Run only integration tests
& "C:\Program Files\Autodesk\Maya2026\bin\mayapy.exe" scripts/run_maya_tests.py -m integration

# Run with verbose output
& "C:\Program Files\Autodesk\Maya2026\bin\mayapy.exe" scripts/run_maya_tests.py -v

# Run specific test file
& "C:\Program Files\Autodesk\Maya2026\bin\mayapy.exe" scripts/run_maya_tests.py tests/meta/test_rig_integration.py

# Run with coverage
& "C:\Program Files\Autodesk\Maya2026\bin\mayapy.exe" scripts/run_maya_tests.py --cov=tp.tools.metahuman
```

### Running Unit Tests Without Maya

Unit tests can be run with a standard Python environment:

```bash
# Run unit tests only
pytest tests/ -m unit

# Or run specific unit test files
pytest tests/meta/test_constants.py -m unit
```

## Test Fixtures

The `conftest.py` file provides several fixtures:

### `maya_session` (session-scoped)
Initializes Maya standalone at the start of the test session. Required for all integration tests.

### `new_scene` (function-scoped)
Creates a fresh Maya scene before each test and cleans up after. Depends on `maya_session`.

### `mock_maya`
Provides mock Maya modules for unit testing without Maya.

## Test Organization

```
tests/
├── conftest.py              # Shared fixtures and pytest configuration
├── __init__.py
└── meta/
    ├── __init__.py
    ├── test_constants.py           # Unit tests for constants module
    ├── test_rig_integration.py     # Integration tests for MetaMetaHumanRig
    └── test_layer_integration.py   # Integration tests for MetaHumanLayer
```

## Writing New Tests

### Unit Tests

```python
import pytest

@pytest.mark.unit
def test_example_unit():
    """Test that runs without Maya."""
    # Import constants directly to avoid Maya dependencies
    from tp.tools.metahuman.rig.meta import constants
    assert constants.METAHUMAN_RIG_TYPE == "metaHumanRig"
```

### Integration Tests

```python
import pytest

@pytest.mark.integration
def test_example_integration(new_scene):
    """Test that requires Maya."""
    from tp.tools.metahuman.rig.meta.rig import MetaMetaHumanRig
    
    meta_rig = MetaMetaHumanRig(name="test_rig_meta")
    assert meta_rig.exists()
```

## Troubleshooting

### Maya not found
Ensure `mayapy` is in your PATH or use the full path to the Maya Python executable.

### Import errors
Make sure the tp-tools-metahuman package and its dependencies are installed in the maya2026 environment. The test runner script automatically sets up the environment.

### Test isolation issues
If tests are affecting each other, ensure you're using the `new_scene` fixture which creates a fresh scene before each test.

### TP Framework not initialized
The test runner script automatically initializes the TP framework via `tp.bootstrap.init()`. If you're running tests manually, you may need to initialize it first.

