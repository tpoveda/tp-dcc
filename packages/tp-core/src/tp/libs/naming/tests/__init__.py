"""Test suite for the tp.libs.naming library.

This package contains unit tests and integration tests for the naming library,
covering all major modules:

- test_config: Tests for the configuration module
- test_token: Tests for the token module
- test_rule: Tests for the rule module
- test_convention: Tests for the naming convention module
- test_preset: Tests for the preset and preset manager modules
- test_api: Integration tests for the API module
- test_validation: Tests for the validation module

To run all tests:
    pytest src/tp/libs/naming/tests/ -v

To run tests with coverage:
    pytest src/tp/libs/naming/tests/ -v --cov=tp.libs.naming --cov-report=html
"""

from __future__ import annotations

__author__ = "Tomi Poveda"
__maintainers__ = ["Tomi Poveda"]
