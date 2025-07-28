"""
Flask-Admin SQLModel support module.

This module provides SQLModel integration for Flask-Admin, enabling
administrative interfaces for SQLModel models with full compatibility
to Flask-Admin's existing features.

Development supported by Claude (Anthropic) - AI-assisted implementation
of SQLModel compatibility layer for Flask-Admin v2.x series.
"""

from ._types import T_MODEL_FIELD_LIST  # noqa: F401

# Export common types for external use
from ._types import T_SQLMODEL  # noqa: F401
from ._types import T_SQLMODEL_FIELD_ARGS  # noqa: F401
from ._types import T_SQLMODEL_PK_VALUE  # noqa: F401
from ._types import T_SQLMODEL_QUERY  # noqa: F401
from ._types import T_SQLMODEL_SESSION_TYPE  # noqa: F401
from .view import SQLModelView  # noqa: F401
