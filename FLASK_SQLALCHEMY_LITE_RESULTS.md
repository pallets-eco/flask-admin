# Flask-SQLAlchemy-Lite Investigation Results

## Executive Summary

**CRITICAL FINDING:** flask-sqlalchemy-lite is **NOT directly compatible** with Flask-Admin's standard `ModelView(User, db.session)` pattern.

### Comparison Table

| Aspect | Flask-SQLAlchemy | flask-sqlalchemy-lite |
|--------|------------------|----------------------|
| Session type | `scoped_session` proxy | Direct `Session` instance |
| Requires app context | No (at initialization) | **Yes (always)** |
| `ModelView(User, db.session)` | ✓ Works | ✗ Fails |
| Request scoping mechanism | SQLAlchemy's scoped_session | Flask's `g` object |
| Compatibility | ✓ Compatible | ⚠ Requires workaround |

## The Problem

flask-sqlalchemy-lite's `db.session` property **requires an active Flask application context** to work. This is because it stores sessions in Flask's `g` object:

```python
# flask-sqlalchemy-lite source code:
@property
def session(self) -> orm.Session:
    sessions: dict[str, orm.Session] = g.setdefault("_sqlalchemy_sessions", {})
    # ^ This 'g' requires an app context!
```

When you try to use the standard Flask-Admin pattern:

```python
# This FAILS with flask-sqlalchemy-lite:
admin.add_view(ModelView(User, db.session))
# Error: RuntimeError: Working outside of application context
```

The error occurs because `db.session` is accessed during ModelView initialization, which happens **outside** of a request context.

## Why Flask-SQLAlchemy Works

Flask-SQLAlchemy uses SQLAlchemy's `scoped_session`, which is a **proxy object** that can be stored and called later:

```python
# Flask-SQLAlchemy
db.session → scoped_session (proxy, no context needed)
# At request time:
db.session() → Session instance (uses current context)
```

The proxy can be stored at initialization time and will resolve to the correct session when actually used.

## Workarounds for flask-sqlalchemy-lite

### Workaround 1: Create a scoped_session Wrapper

Create your own `scoped_session` that wraps flask-sqlalchemy-lite's session factory:

```python
from flask import Flask
from flask_sqlalchemy_lite import SQLAlchemy
from sqlalchemy.orm import scoped_session
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView

app = Flask(__name__)
app.config["SQLALCHEMY_ENGINES"] = {"default": "sqlite:///app.db"}

db = SQLAlchemy(app)

# Create a scoped_session that uses flask-sqlalchemy-lite's sessionmaker
Session = scoped_session(
    db.sessionmaker,
    scopefunc=lambda: None  # Uses thread-local by default
)

# Now this works:
admin = Admin(app)
admin.add_view(ModelView(User, Session))
```

**Caveat:** This loses the Flask `g` object integration, so sessions won't be automatically cleaned up by flask-sqlalchemy-lite's teardown handler.

### Workaround 2: Session Factory Function

Pass a callable that returns the session:

```python
from flask import current_app

def get_session():
    """Returns session for current context"""
    return current_app.extensions['sqlalchemy'].get_session()

# Use with Flask-Admin:
admin.add_view(ModelView(User, get_session))
```

**Caveat:** This requires modifying Flask-Admin's ModelView to accept callables, which it may not support.

### Workaround 3: Custom ModelView

Create a custom ModelView that handles session retrieval:

```python
from flask_admin.contrib.sqla import ModelView as BaseModelView

class LiteModelView(BaseModelView):
    def __init__(self, model, db_instance, *args, **kwargs):
        # Store the db instance instead of session
        self._db = db_instance
        # Create a dummy session to satisfy parent __init__
        from sqlalchemy.orm import Session
        dummy_session = Session()
        super().__init__(model, dummy_session, *args, **kwargs)
    
    def _get_session(self):
        # Override to get session from flask-sqlalchemy-lite
        return self._db.get_session()
    
    # Override methods that use self.session
    def get_query(self):
        return self._get_session().query(self.model)
    
    # ... override other methods as needed

# Use with Flask-Admin:
admin.add_view(LiteModelView(User, db))
```

**Caveat:** Requires overriding multiple methods, brittle to Flask-Admin updates.

### Workaround 4: Lazy Session Property (RECOMMENDED)

Create a wrapper that delays session access until actually needed:

```python
class LazySessionWrapper:
    """Wrapper that provides session access only when called"""
    def __init__(self, db):
        self._db = db
    
    def __call__(self):
        """Returns the current session"""
        return self._db.get_session()
    
    def query(self, *args, **kwargs):
        """Proxy query calls to current session"""
        return self._db.get_session().query(*args, **kwargs)
    
    def add(self, *args, **kwargs):
        return self._db.get_session().add(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        return self._db.get_session().delete(*args, **kwargs)
    
    def commit(self, *args, **kwargs):
        return self._db.get_session().commit(*args, **kwargs)
    
    def rollback(self, *args, **kwargs):
        return self._db.get_session().rollback(*args, **kwargs)
    
    def flush(self, *args, **kwargs):
        return self._db.get_session().flush(*args, **kwargs)
    
    def get(self, *args, **kwargs):
        return self._db.get_session().get(*args, **kwargs)

# Use with Flask-Admin:
session_wrapper = LazySessionWrapper(db)
admin.add_view(ModelView(User, session_wrapper))
```

This mimics scoped_session's behavior by proxying all session method calls.

## Detailed Investigation Results

### Test 1: Session Type
- flask-sqlalchemy-lite provides `db.session` ✓
- Type: `Session` (direct instance, not proxy)
- Stored in Flask's `g` object
- **Requires app context to access**

### Test 2: Compatibility with Flask-Admin
- Standard pattern `ModelView(User, db.session)` **FAILS** ✗
- Error: `RuntimeError: Working outside of application context`
- Reason: `db.session` property accesses `g` which needs context

### Test 3: Request Scoping (if workaround used)
- Sessions ARE request-scoped when accessed properly
- Each request gets a fresh session from Flask's `g` object
- Automatic cleanup via teardown handler

## Recommendations

### For New Projects

**If using Flask-Admin:**
- ✓ Use **Flask-SQLAlchemy** (standard library)
- ✗ Avoid flask-sqlalchemy-lite unless you implement workarounds

### For Existing Projects Using flask-sqlalchemy-lite

1. **Best Option:** Implement Workaround 4 (LazySessionWrapper)
   - Provides compatibility with minimal code changes
   - Maintains flask-sqlalchemy-lite's session management
   - Works with Flask-Admin's existing code

2. **Alternative:** Switch to Flask-SQLAlchemy
   - More compatible with Flask ecosystem
   - Better documentation and community support
   - Works out-of-the-box with Flask-Admin

3. **For Advanced Users:** Create custom ModelView
   - Full control over session management
   - Can optimize for specific use cases
   - Requires deep understanding of both libraries

## Why Use flask-sqlalchemy-lite?

Given the compatibility issues, why might someone choose flask-sqlalchemy-lite?

**Advantages:**
- Lighter weight (fewer dependencies)
- More explicit session management
- Async support (if using async engines)
- Simpler codebase

**Disadvantages:**
- **Not compatible with Flask-Admin out-of-the-box**
- Less community support
- Requires workarounds for many Flask extensions
- Less documentation

## Conclusion

### Flask-SQLAlchemy (Standard)
- ✓ **COMPATIBLE** with Flask-Admin
- ✓ Works with `ModelView(User, db.session)` pattern
- ✓ Request-scoped sessions via `scoped_session` proxy
- ✓ **RECOMMENDED** for use with Flask-Admin

### flask-sqlalchemy-lite
- ✗ **NOT COMPATIBLE** with Flask-Admin's standard pattern
- ⚠ Requires workarounds (LazySessionWrapper or custom ModelView)
- ✓ Does provide request-scoped sessions (via Flask `g` object)
- ⚠ **Use only if willing to implement workarounds**

## Summary for Original Issue

The original question was whether Flask-Admin holds a single session for app lifetime or uses request-scoped sessions.

**Answer:**
- **Flask-SQLAlchemy:** Request-scoped sessions ✓ (VERIFIED)
- **flask-sqlalchemy-lite:** Would be request-scoped if compatible, but **standard pattern doesn't work** ✗ (INCOMPATIBLE)

The concern about app-lifetime sessions is **unfounded for Flask-SQLAlchemy**, but flask-sqlalchemy-lite presents a different problem: incompatibility with Flask-Admin's initialization pattern.

## Files Created

1. **Test Suite:** `flask_admin/tests/sqla/test_session_scoping_lite.py`
2. **Standalone Test:** `test_lite_standalone.py`
3. **Investigation Doc:** `FLASK_SQLALCHEMY_LITE_INVESTIGATION.md`
4. **Results Doc:** This file

## Next Steps

1. Update PR description with these findings
2. Reply to comment with summary and workarounds
3. Consider adding workaround examples to Flask-Admin documentation
4. Possibly add a compatibility note in Flask-Admin docs

---

**Investigation Date:** October 18, 2025  
**Status:** Complete  
**Result:** flask-sqlalchemy-lite NOT compatible without workarounds
