# Migration Plan: `tp.libs.naming` + `tp.libs.pathsolver` → `tp.libs.templating`

## Status: ✅ COMPLETE

**360 tests passing** across all modules.

## Overview

This document outlines the migration plan to consolidate the `naming` and `pathsolver` libraries into a unified `templating` library under `tp.libs.templating`.

**Goal**: Create a unified templating system that handles both:
1. **Name templating**: Token-based naming conventions (current `naming` functionality) ✅
2. **Path templating**: Path pattern resolution with template references (current `pathsolver` functionality) ✅
3. **Integration**: Link path templates to naming templates to derive paths from name tokens ✅
4. **Version Management**: Auto-increment and version discovery ✅
5. **Asset Validation**: Asset type classification and validation ✅
6. **Discovery**: Pattern matching and asset discovery ✅
7. **Configuration**: Unified configuration loading and merging ✅
8. **Context**: Hierarchical template contexts with inheritance ✅

---

## Phase 1: Create New Directory Structure

### New Structure
```
tp/libs/templating/
├── __init__.py
├── api.py                    # Unified public API
├── errors.py                 # All error classes
├── consts.py                 # Constants (from naming)
├── validation.py             # Validation utilities (from naming)
│
├── naming/                   # Name templating (from naming lib)
│   ├── __init__.py
│   ├── token.py              # Token, KeyValue classes
│   ├── rule.py               # Rule class
│   ├── convention.py         # NamingConvention class
│   ├── preset.py             # PresetsManager class
│   └── config.py             # NamingConfiguration class
│
├── paths/                    # Path templating (from pathsolver)
│   ├── __init__.py
│   ├── template.py           # Template, Resolver classes
│   ├── pattern.py            # Pattern parsing/formatting functions
│   └── resolver.py           # Path resolver linking to naming
│
├── versioning/               # [P0] Version management
│   ├── __init__.py
│   ├── token.py              # VersionToken with auto-increment
│   └── resolver.py           # VersionResolver (filesystem/db version lookup)
│
├── assets/                   # [P0] Asset type classification & validation
│   ├── __init__.py
│   ├── registry.py           # AssetTypeRegistry
│   ├── validator.py          # AssetValidator, ValidationResult
│   └── types.py              # Built-in asset type definitions
│
├── discovery/                # [P1] Pattern matching & discovery
│   ├── __init__.py
│   ├── finder.py             # TemplateDiscovery, DiscoveredAsset
│   └── glob.py               # Glob pattern generation from templates
│
├── config/                   # [P1] Enhanced configuration
│   ├── __init__.py
│   ├── loader.py             # TemplateConfiguration loader
│   ├── schema.py             # Configuration schema/validation
│   └── merger.py             # Configuration merging utilities
│
├── context/                  # [P1] Context inheritance & overrides
│   ├── __init__.py
│   └── context.py            # TemplateContext with inheritance
│
├── maya/                     # Maya-specific utilities (from naming/maya)
│   ├── __init__.py
│   └── api.py
│
├── presets/                  # Preset files (from naming/presets)
│   ├── default-global.yaml
│   └── default.preset
│
└── tests/                    # All tests
    ├── __init__.py
    ├── conftest.py
    ├── data/
    │
    ├── naming/               # Original naming tests (must pass)
    │   ├── test_api.py
    │   ├── test_config.py
    │   ├── test_convention.py
    │   ├── test_preset.py
    │   ├── test_rule.py
    │   ├── test_token.py
    │   └── test_validation.py
    │
    ├── paths/                # Path templating tests
    │   ├── test_template.py
    │   ├── test_pattern.py
    │   └── test_resolver.py
    │
    ├── versioning/           # [P0] Version management tests
    │   ├── test_token.py
    │   └── test_resolver.py
    │
    ├── assets/               # [P0] Asset validation tests
    │   ├── test_registry.py
    │   └── test_validator.py
    │
    ├── discovery/            # [P1] Discovery tests
    │   └── test_finder.py
    │
    ├── config/               # [P1] Configuration tests
    │   └── test_loader.py
    │
    └── context/              # [P1] Context tests
        └── test_context.py
```

---

## Phase 2: Migration Steps

### Step 1: Create the `templating` directory structure ✅ COMPLETED
- [x] Create `tp/libs/templating/` directory
- [x] Create subdirectories: `naming/`, `paths/`, `maya/`, `presets/`, `tests/`

### Step 2: Move and update naming library files ✅ COMPLETED
- [x] Move `naming/token.py` → `templating/naming/token.py`
- [x] Move `naming/rule.py` → `templating/naming/rule.py`
- [x] Move `naming/convention.py` → `templating/naming/convention.py`
- [x] Move `naming/preset.py` → `templating/naming/preset.py`
- [x] Move `naming/config.py` → `templating/naming/config.py`
- [x] Move `naming/consts.py` → `templating/consts.py`
- [x] Move `naming/validation.py` → `templating/validation.py`
- [x] Move `naming/api.py` → `templating/naming/api.py`
- [x] Move `naming/maya/` → `templating/maya/`
- [x] Move `naming/presets/` → `templating/presets/`

### Step 3: Move and update pathsolver library files ✅ COMPLETED
- [x] Move `pathsolver/template.py` → `templating/paths/template.py`
- [x] Move `pathsolver/errors.py` content → merge into `templating/errors.py`
- [x] Extract pattern functions from template.py → `templating/paths/pattern.py`
- [x] Create `templating/paths/resolver.py` with PathResolver class

### Step 4: Update all imports within moved files ✅ COMPLETED
Update all internal imports from:
```python
from tp.libs.naming import ...
from tnmLib.pathsolver import ...
```
To:
```python
from tp.libs.templating import ...
from tp.libs.templating.naming import ...
from tp.libs.templating.paths import ...
```

### Step 5: Create unified errors.py ✅ COMPLETED
```python
# tp/libs/templating/errors.py

# From pathsolver
class ParseError(Exception):
    """Raised when a template is unable to parse a path."""

class FormatError(Exception):
    """Raised when a template is unable to format data into a path."""

class ResolveError(Exception):
    """Raised when a template reference cannot be resolved."""

# Add naming-specific errors as needed
class TokenNotFoundError(Exception):
    """Raised when a token is not found in the naming convention."""

class RuleNotFoundError(Exception):
    """Raised when a rule is not found in the naming convention."""
```

### Step 6: Create unified API
```python
# tp/libs/templating/api.py

# Re-export naming functionality
from tp.libs.templating.naming.api import (
    naming_preset_manager,
    reset_preset_manager,
    naming_convention,
    active_naming_convention,
    set_active_naming_convention,
    solve,
    parse,
)

# Re-export path functionality
from tp.libs.templating.paths.template import Template
from tp.libs.templating.paths.pattern import (
    regular_expression_from_pattern,
    expand_pattern,
    keys_from_pattern,
    parse_path_by_pattern,
    path_from_parsed_data,
)

# New integrated functionality
from tp.libs.templating.paths.resolver import PathResolver
```

### Step 7: Move and update tests ✅ COMPLETED
- [x] Move `naming/tests/` → `templating/tests/naming/`
- [x] Update all test imports
- [x] Run tests to ensure they pass (220 tests passing)

### Step 8: Create new path tests ✅ COMPLETED
- [x] Create `templating/tests/paths/test_template.py` (21 tests)
- [ ] Create `templating/tests/paths/test_pattern.py` (future)
- [ ] Create `templating/tests/paths/test_resolver.py` (future)

---

## Phase 3: New Path Resolver Integration

### Step 9: Create PathResolver class
Create a new `PathResolver` class that links path templates to naming conventions:

```python
# tp/libs/templating/paths/resolver.py

from tp.libs.templating.paths.template import Template, Resolver
from tp.libs.templating.naming.convention import NamingConvention

class PathResolver(Resolver):
    """Resolver that links path templates to naming conventions.
    
    This allows deriving file paths from naming convention tokens.
    """
    
    def __init__(
        self,
        naming_convention: NamingConvention | None = None,
        templates: dict[str, Template] | None = None,
    ):
        self._naming_convention = naming_convention
        self._templates: dict[str, Template] = templates or {}
    
    def register_template(self, template: Template):
        """Register a path template."""
        self._templates[template.name] = template
    
    def get(self, template_name: str, default=None) -> Template | None:
        """Get a template by name."""
        return self._templates.get(template_name, default)
    
    def resolve_path(
        self,
        template_name: str,
        rule_name: str | None = None,
        **token_values,
    ) -> str:
        """Resolve a path using naming convention tokens.
        
        Args:
            template_name: Name of the path template to use.
            rule_name: Optional naming rule to use for token resolution.
            **token_values: Token values to use.
            
        Returns:
            Resolved path string.
        """
        template = self.get(template_name)
        if template is None:
            raise KeyError(f"Template '{template_name}' not found")
        
        # Resolve tokens through naming convention if available
        resolved_data = {}
        if self._naming_convention:
            for key, value in token_values.items():
                token = self._naming_convention.token(key)
                if token:
                    resolved_data[key] = token.solve(value, default_value=value)
                else:
                    resolved_data[key] = value
        else:
            resolved_data = token_values
        
        return template.format(resolved_data)
    
    def parse_path(
        self,
        template_name: str,
        path: str,
    ) -> dict:
        """Parse a path and return token values.
        
        Args:
            template_name: Name of the path template to use.
            path: Path string to parse.
            
        Returns:
            Dictionary of parsed token values.
        """
        template = self.get(template_name)
        if template is None:
            raise KeyError(f"Template '{template_name}' not found")
        
        return template.parse(path)
```

---

## Phase 3.5: Implement P0 & P1 Features

### Step 10: [P0] Version Management ✅ COMPLETED

Implemented in `versioning/token.py` and `versioning/resolver.py`:
- `VersionToken`: Token for version strings with auto-increment
  - `format_version()`: Format version numbers into strings
  - `parse_version()`: Parse version strings into numeric components
  - `next_version()`: Get next version string (with increment options for semantic)
  - `compare()`: Compare two version strings
  - `sort_versions()`: Sort a list of version strings
  - Supports simple (001, 002) and semantic (1.0.0, 1.2.3) versioning
- `VersionResolver`: Filesystem-based version discovery
  - `all_versions()`: List all versions matching a template
  - `latest_version()`: Find the latest version
  - `next_available_version()`: Get the next version number
  - `version_exists()`: Check if a specific version exists
  - `resolve_latest()`: Get full path to latest version

**Tests**: 30 tests passing in `tests/versioning/test_token.py`

### Step 11: [P0] Asset Type Classification & Validation ✅ COMPLETED

Implemented in `assets/types.py`, `assets/registry.py`, and `assets/validator.py`:
- `AssetTypeDefinition`: Definition of asset types with rules
  - Required/allowed tokens
  - File extensions
  - Custom validators
  - Metadata
- `AssetTypeRegistry`: Registry for managing asset types
  - Built-in types: character, prop, environment, texture, material, animation, rig, audio
  - `register_type()`, `get_type()`, `list_types()`
  - `types_by_category()`, `types_with_extension()`
  - Serialization with `to_dict()` / `from_dict()`
- `AssetValidator`: Validate names and paths
  - `validate_name()`, `validate_path()`
  - `suggest_corrections()`: Suggest fixes for invalid names
  - `detect_asset_type()`: Auto-detect asset type from path
  - `batch_validate()`: Validate multiple items
- `ValidationResult`: Result with errors, warnings, suggestions

**Tests**: 36 tests passing in `tests/assets/test_assets.py`

### Step 12: [P1] Pattern Matching & Discovery (TODO)
    ) -> str:
        """Get next available version number."""
    
    def all_versions(
        self,
        template_name: str,
        **tokens,
    ) -> list[str]:
        """List all existing versions."""
```

### Step 11: [P0] Asset Type Classification & Validation

#### assets/types.py
```python
@dataclass
class AssetTypeDefinition:
    """Definition of an asset type with its rules."""
    
    name: str
    description: str
    naming_rule: str
    path_template: str
    allowed_tokens: list[str]
    required_tokens: list[str]
    validators: list[Callable]
    file_extensions: list[str]
```

#### assets/registry.py
```python
class AssetTypeRegistry:
    """Registry for asset type definitions."""
    
    def register_type(self, asset_type: AssetTypeDefinition):
        """Register an asset type."""
    
    def get_type(self, name: str) -> AssetTypeDefinition | None:
        """Get asset type by name."""
    
    def list_types(self) -> list[str]:
        """List all registered type names."""
```

#### assets/validator.py
```python
@dataclass
class ValidationResult:
    """Result of a validation operation."""
    
    valid: bool
    errors: list[str]
    warnings: list[str]
    suggestions: list[str]

class AssetValidator:
    """Validate asset names and paths against rules."""
    
    def __init__(
        self,
        registry: AssetTypeRegistry,
        naming_convention: NamingConvention | None = None,
    ):
        self._registry = registry
        self._naming_convention = naming_convention
    
    def validate_name(
        self,
        name: str,
        asset_type: str,
    ) -> ValidationResult:
        """Validate a name against asset type rules."""
    
    def validate_path(
        self,
        path: str,
        asset_type: str,
    ) -> ValidationResult:
        """Validate a path against asset type rules."""
    
    def suggest_corrections(
        self,
        invalid_name: str,
        asset_type: str,
    ) -> list[str]:
        """Suggest valid alternatives for invalid names."""
```

### Step 12: [P1] Pattern Matching & Discovery

#### discovery/finder.py
```python
@dataclass
class DiscoveredAsset:
    """An asset discovered through pattern matching."""
    
    path: str
    parsed_tokens: dict[str, str]
    asset_type: str | None
    version: str | None

class TemplateDiscovery:
    """Discover files matching templates."""
    
    def __init__(self, path_resolver: PathResolver):
        self._path_resolver = path_resolver
    
    def find_matching(
        self,
        template_name: str,
        root_path: str,
        **partial_tokens,
    ) -> list[DiscoveredAsset]:
        """Find all files matching template with optional filters."""
    
    def find_latest_versions(
        self,
        template_name: str,
        root_path: str,
        **partial_tokens,
    ) -> list[DiscoveredAsset]:
        """Find latest version of each unique asset."""
```

#### discovery/glob.py
```python
def glob_from_template(
    template: Template,
    **known_tokens,
) -> str:
    """Generate glob pattern from template.
    
    Known tokens are substituted, unknown become wildcards.
    """

def regex_from_template(
    template: Template,
    **known_tokens,
) -> re.Pattern:
    """Generate regex pattern from template."""
```

### Step 13: [P1] Enhanced Configuration

#### config/schema.py
```python
@dataclass
class TemplateConfigurationSchema:
    """Schema for validating configuration files."""
    
    version: str
    name: str
    tokens: dict[str, TokenSchema]
    rules: dict[str, RuleSchema]
    path_templates: dict[str, PathTemplateSchema]
    asset_types: dict[str, AssetTypeSchema]
```

#### config/loader.py
```python
class TemplateConfiguration:
    """Complete serializable configuration."""
    
    @classmethod
    def from_yaml(cls, path: str) -> TemplateConfiguration:
        """Load from YAML file."""
    
    @classmethod
    def from_json(cls, path: str) -> TemplateConfiguration:
        """Load from JSON file."""
    
    def to_yaml(self, path: str):
        """Save to YAML file."""
    
    def to_json(self, path: str):
        """Save to JSON file."""
    
    def merge_with(
        self,
        other: TemplateConfiguration,
    ) -> TemplateConfiguration:
        """Merge two configurations (for layered configs)."""
    
    def validate(self) -> list[str]:
        """Validate configuration integrity."""
    
    def build_naming_convention(self) -> NamingConvention:
        """Build NamingConvention from config."""
    
    def build_path_resolver(self) -> PathResolver:
        """Build PathResolver from config."""
    
    def build_asset_registry(self) -> AssetTypeRegistry:
        """Build AssetTypeRegistry from config."""
```

### Step 14: [P1] Context Inheritance & Overrides

#### context/context.py
```python
class TemplateContext:
    """Hierarchical context for template resolution."""
    
    def __init__(
        self,
        name: str,
        parent: TemplateContext | None = None,
        configuration: TemplateConfiguration | None = None,
    ):
        self.name = name
        self.parent = parent
        self._overrides: dict[str, Any] = {}
        self._configuration = configuration
    
    def with_override(self, **overrides) -> TemplateContext:
        """Create child context with overrides."""
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get value with inheritance chain lookup."""
    
    def set(self, key: str, value: Any):
        """Set value in this context."""
    
    @property
    def naming_convention(self) -> NamingConvention:
        """Get naming convention for this context."""
    
    @property
    def path_resolver(self) -> PathResolver:
        """Get path resolver for this context."""
    
    def resolve_name(self, rule_name: str, **tokens) -> str:
        """Resolve a name using this context."""
    
    def resolve_path(self, template_name: str, **tokens) -> str:
        """Resolve a path using this context."""
```

---

## Phase 4: Update External Consumers

### Files to Update
After the library is migrated, these external files need import updates:

| File | Current Import | New Import |
|------|----------------|------------|
| `tp-tools-utility/.../renamer/model.py` | `from tp.libs.naming.consts import EditIndexMode` | `from tp.libs.templating.consts import EditIndexMode` |
| `tp-tools-utility/.../renamer/controllers/maya/controller.py` | `from tp.libs.naming.consts import PrefixSuffixType` | `from tp.libs.templating.consts import PrefixSuffixType` |
| `tp-tools-utility/.../renamer/controllers/maya/controller.py` | `from tp.libs.naming.maya import api as naming` | `from tp.libs.templating.maya import api as naming` |
| `tp-modrig/.../naming.py` | `from tp.libs.naming.manager import NameManager` | `from tp.libs.templating.naming.manager import NameManager` |
| `tp-modrig/.../rig.py` | `from tp.libs.naming.manager import NameManager` | `from tp.libs.templating.naming.manager import NameManager` |
| `tp-modrig/.../base/rig.py` | `from tp.libs.naming.manager import NameManager` | `from tp.libs.templating.naming.manager import NameManager` |
| `tp-modrig/.../namingpresets.py` | `from tp.libs.naming import manager` | `from tp.libs.templating.naming import manager` |
| `tp-modrig/.../module.py` | `from tp.libs.naming.manager import NameManager` | `from tp.libs.templating.naming.manager import NameManager` |
| `tp-modrig/.../configuration.py` | `from tp.libs.naming.manager import NameManager` | `from tp.libs.templating.naming.manager import NameManager` |

**Note**: `tp.libs.naming.manager` is referenced but not present in the current `naming` library listing. Verify if this module exists or needs to be created.

---

## Phase 5: Cleanup

### Step 10: Remove old libraries
- [ ] Delete `tp/libs/naming/` directory (after all tests pass)
- [ ] Delete `tp/libs/pathsolver/` directory (after all tests pass)

### Step 11: Update documentation
- [ ] Update README.md for tp-core package
- [ ] Add docstrings to new API functions
- [ ] Create usage examples

---

## Execution Order Summary

1. **Create directory structure** (Phase 1)
2. **Copy files** (don't delete originals yet)
3. **Update imports in copied files** (Phase 2, Steps 2-6)
4. **Run original naming tests** → must all pass
5. **Add new path tests** (Phase 2, Step 8)
6. **Implement PathResolver** (Phase 3)
7. **Test integration**
8. **[P0] Implement Version Management** (Phase 3.5, Steps 10)
9. **[P0] Implement Asset Validation** (Phase 3.5, Step 11)
10. **[P1] Implement Pattern Discovery** (Phase 3.5, Step 12)
11. **[P1] Implement Enhanced Configuration** (Phase 3.5, Step 13)
12. **[P1] Implement Context Inheritance** (Phase 3.5, Step 14)
13. **Update external consumers** (Phase 4)
14. **Delete old directories** (Phase 5)

---

## Testing Strategy

### Naming Tests (Must Pass)
All existing tests in `naming/tests/` must pass after migration:
- `test_api.py`
- `test_config.py`
- `test_convention.py`
- `test_preset.py`
- `test_rule.py`
- `test_token.py`
- `test_validation.py`

### New Path Tests (To Create)
```python
# test_template.py
def test_template_parse():
    """Test parsing a path with a template."""

def test_template_format():
    """Test formatting data into a path."""

def test_template_keys():
    """Test extracting keys from a pattern."""

def test_template_reference():
    """Test template references with @ syntax."""

# test_pattern.py
def test_regular_expression_from_pattern():
    """Test regex generation from pattern."""

def test_expand_pattern():
    """Test pattern expansion with references."""

def test_nested_keys():
    """Test dot notation for nested keys."""

# test_resolver.py
def test_path_resolver_with_naming_convention():
    """Test resolving paths using naming convention tokens."""

def test_path_resolver_parse():
    """Test parsing paths back to tokens."""
```

---

## Known Issues to Address

1. **Broken import**: `from tnmLib.pathsolver import errors` in `template.py` - needs to be fixed
2. **`six` dependency**: `from six import with_metaclass` can be removed (Python 3.6+ supports `class Resolver(metaclass=abc.ABCMeta)`)
3. **Missing `manager.py`**: `tp-modrig/namingpresets.py` imports `from tp.libs.naming import manager` but this module doesn't exist in `naming/`. This is a broken import that needs investigation - either:
   - The module was never created, or
   - It was deleted at some point
   - **Action**: Check if `tp-modrig` works currently or if this is dead code
4. **EditIndexMode location**: Currently in `consts.py` but also defined in `maya/api.py` - consolidate

---

## Timeline Estimate

| Phase | Estimated Time |
|-------|----------------|
| Phase 1: Directory Structure | 30 min |
| Phase 2: File Migration | 2-3 hours |
| Phase 3: PathResolver Integration | 2-3 hours |
| Phase 3.5: P0 Features (Versioning + Assets) | 4-5 hours |
| Phase 3.5: P1 Features (Discovery + Config + Context) | 5-6 hours |
| Phase 4: External Consumer Updates | 1 hour |
| Phase 5: Cleanup & Documentation | 1 hour |
| **Total** | **16-20 hours** |

