# SQLModel Tests

## ⚠️ **Development Test Collection Notice**

**WARNING**: This test collection was created during active development to ensure comprehensive coverage of SQLModel functionality. It currently contains over 700+ tests across 48+ test files, which is an overwhelming number for production use. 

**This extensive test suite was designed to:**
- Test every aspect of the SQLModel integration during development
- Ensure no functionality was missed during the initial implementation
- Provide detailed coverage for debugging and validation purposes

**Future Refactoring Required**: In a second development stage, these tests should be refactored into a smaller, more manageable set of comprehensive tests that maintain coverage while reducing complexity and execution time.

## Overview

This directory contains comprehensive tests for the SQLModel support in Flask-Admin, organized into focused test categories. Due to the differences between SQLModel (with global registry) and SQLAlchemy, tests are organized into separate focused files and directories to address SQLModel registry issues and provide better test isolation.

## Directory Structure

```
sqlmodel/
├── README.md
├── __init__.py
├── conftest.py                 # Test configuration and fixtures
├── debug_tests.py              # Development and troubleshooting tests
├── ajax/                       # AJAX functionality tests
│   ├── __init__.py
│   ├── test_ajax_extended.py
│   └── test_ajax_simple.py
├── fields/                     # Field handling and conversion tests
│   ├── __init__.py
│   ├── test_fields_comprehensive.py
│   ├── test_fields_focused.py
│   └── test_fields_simple.py
├── filters/                    # Query filtering tests
│   ├── __init__.py
│   ├── test_filters_coverage.py
│   └── test_filters_extended.py
├── form/                       # Form generation and conversion tests
│   ├── __init__.py
│   ├── test_constrained_pydantic_types.py
│   ├── test_extended_types_mixin_degradation.py
│   ├── test_extended_types_mixin_integration.py
│   ├── test_field_class_overrides_viewlevel.py
│   ├── test_form.py
│   ├── test_form_advanced_coverage.py
│   ├── test_form_coverage_gaps.py
│   ├── test_form_coverage_improvements.py
│   ├── test_form_rules.py
│   ├── test_inlineform.py
│   ├── test_property_computed_field_integration.py
│   └── test_special_pydantic_types.py
├── integration/                # Core integration and functionality tests
│   ├── __init__.py
│   ├── test_basic.py
│   ├── test_columns.py
│   ├── test_core.py
│   ├── test_multi_pk.py
│   ├── test_postgres.py
│   └── test_translation.py
├── templates/                  # Template test files
│   ├── another_macro.html
│   └── macro.html
├── tools/                      # Utility and tools tests
│   ├── __init__.py
│   ├── test_tools_comprehensive.py
│   ├── test_tools_coverage_gaps.py
│   ├── test_tools_coverage_improvements.py
│   └── test_tools_extended.py
├── typefmt/                    # Type formatting tests
│   ├── __init__.py
│   └── test_typefmt_coverage_improvements.py
├── validators/                 # Validation tests
│   ├── __init__.py
│   └── test_validators_comprehensive.py
├── view/                       # View functionality tests
│   ├── __init__.py
│   └── test_view_coverage_improvements.py
└── widgets/                    # Widget tests
    ├── __init__.py
    └── test_widgets.py
```

## Test Categories

### 🏗️ **Integration Tests** (`integration/`)
Core functionality and basic operations:
- `test_basic.py` - Basic CRUD operations and core functionality
- `test_columns.py` - Column handling and display
- `test_core.py` - Core SQLModelView functionality
- `test_multi_pk.py` - Multiple primary key support
- `test_postgres.py` - PostgreSQL specific functionality
- `test_translation.py` - Internationalization support

### 📝 **Form Tests** (`form/`)
Form generation and field conversion:
- `test_form.py` - Basic form generation
- `test_form_advanced_coverage.py` - Advanced form scenarios
- `test_form_rules.py` - Form rule handling
- `test_inlineform.py` - Inline form functionality
- `test_constrained_pydantic_types.py` - Pydantic type constraints
- `test_extended_types_mixin_*.py` - SQLAlchemy-utils integration
- `test_property_computed_field_integration.py` - Property/computed field support
- `test_field_class_overrides_viewlevel.py` - Custom field class overrides

### 🔧 **Tools Tests** (`tools/`)
Utility functions and model introspection:
- `test_tools_comprehensive.py` - Comprehensive tools functionality
- `test_tools_extended.py` - Extended tools features
- `test_tools_coverage_*.py` - Coverage improvement tests

### 🔍 **Filter Tests** (`filters/`)
Query filtering and search functionality:
- `test_filters_coverage.py` - Filter coverage tests
- `test_filters_extended.py` - Extended filter functionality

### 🏷️ **Field Tests** (`fields/`)
Custom field implementations:
- `test_fields_simple.py` - Basic field functionality
- `test_fields_focused.py` - Focused field tests
- `test_fields_comprehensive.py` - Comprehensive field coverage

### ⚡ **AJAX Tests** (`ajax/`)
Asynchronous functionality:
- `test_ajax_simple.py` - Basic AJAX functionality
- `test_ajax_extended.py` - Extended AJAX features

### 🎨 **UI Component Tests**
- `validators/` - Field validation tests
- `widgets/` - Custom widget tests
- `typefmt/` - Type formatting tests
- `view/` - View functionality tests

## Debug Tests

- `debug_tests.py` - Debug tests for development and troubleshooting
  - Filter group naming tests
  - Column list with relationships tests
  - Relationship field handling tests
  - Primary key detection tests
  - Field type detection tests
  - Dot notation filter naming tests
  - Filter joins setup tests

### Running Debug Tests

To run all debug tests:
```bash
python -m pytest flask_admin/tests/sqlmodel/debug_tests.py -v -s
```

To run a specific debug test:
```bash
python -m pytest flask_admin/tests/sqlmodel/debug_tests.py::test_filter_group_naming -v -s
```

The debug tests provide detailed output to help understand the behavior of various components and are useful for development and troubleshooting.

## Running Tests

To run all SQLModel tests:
```bash
python -m pytest flask_admin/tests/sqlmodel/ -v
```

To run a specific test file:
```bash
python -m pytest flask_admin/tests/sqlmodel/test_basic.py -v
```

## Notes

- Tests use SQLite by default
- PostgreSQL tests require a local PostgreSQL instance
- Some tests may require additional dependencies
- Debug tests provide verbose output for development use