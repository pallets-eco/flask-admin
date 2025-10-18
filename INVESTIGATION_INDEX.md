# Flask-Admin Session Scoping Investigation - Document Index

## Quick Links

### 🎯 Start Here
- **[FINAL_SUMMARY.md](FINAL_SUMMARY.md)** - Complete comparison of both libraries
- **[INVESTIGATION_GUIDE.md](INVESTIGATION_GUIDE.md)** - Quick start guide

### 📊 Main Findings

#### Flask-SQLAlchemy (✓ Compatible)
- **[SESSION_SCOPING_INVESTIGATION.md](SESSION_SCOPING_INVESTIGATION.md)** - Technical deep dive
- **[SUMMARY.md](SUMMARY.md)** - Executive summary
- **[session_scoping_diagram.txt](session_scoping_diagram.txt)** - Visual diagram

#### flask-sqlalchemy-lite (✗ Incompatible)
- **[FLASK_SQLALCHEMY_LITE_RESULTS.md](FLASK_SQLALCHEMY_LITE_RESULTS.md)** - Detailed findings + workarounds
- **[FLASK_SQLALCHEMY_LITE_INVESTIGATION.md](FLASK_SQLALCHEMY_LITE_INVESTIGATION.md)** - Investigation approach

### 🧪 Test Suites
- **[flask_admin/tests/sqla/test_session_scoping.py](flask_admin/tests/sqla/test_session_scoping.py)** - Flask-SQLAlchemy tests
- **[flask_admin/tests/sqla/test_session_scoping_lite.py](flask_admin/tests/sqla/test_session_scoping_lite.py)** - flask-sqlalchemy-lite tests

### 🔬 Reproduction Scripts
- **[reproduction_script.py](reproduction_script.py)** - Flask-SQLAlchemy demonstration
- **[test_lite_standalone.py](test_lite_standalone.py)** - Comparison demonstration

## Document Overview

### Executive Documents
These provide high-level summaries suitable for stakeholders:

| Document | Purpose | Audience |
|----------|---------|----------|
| FINAL_SUMMARY.md | Complete comparison | Everyone |
| SUMMARY.md | Flask-SQLAlchemy summary | Management/Stakeholders |
| INVESTIGATION_GUIDE.md | Quick reference | Developers |

### Technical Documentation
These provide detailed technical information:

| Document | Purpose | Detail Level |
|----------|---------|--------------|
| SESSION_SCOPING_INVESTIGATION.md | Flask-SQLAlchemy deep dive | High |
| FLASK_SQLALCHEMY_LITE_RESULTS.md | Lite findings + workarounds | High |
| FLASK_SQLALCHEMY_LITE_INVESTIGATION.md | Investigation methodology | Medium |
| session_scoping_diagram.txt | Visual explanation | Medium |

### Code Artifacts
Executable code for verification:

| File | Purpose | How to Run |
|------|---------|------------|
| reproduction_script.py | Flask-SQLAlchemy demo | `python reproduction_script.py` |
| test_lite_standalone.py | Comparison demo | `python test_lite_standalone.py` |
| test_session_scoping.py | Flask-SQLAlchemy tests | `pytest flask_admin/tests/sqla/test_session_scoping.py` |
| test_session_scoping_lite.py | Lite tests | `pytest flask_admin/tests/sqla/test_session_scoping_lite.py` |

## Investigation Results Summary

### Flask-SQLAlchemy ✓
**Status:** COMPATIBLE - Request-scoped sessions verified

**Key Points:**
- Uses `scoped_session` proxy
- Works with `ModelView(User, db.session)` pattern
- Different session per request
- Proper session isolation
- **RECOMMENDED for Flask-Admin**

**Evidence:**
- 3 tests created, all passing
- Reproduction script demonstrates correct behavior
- Session IDs show different instances per request

### flask-sqlalchemy-lite ✗
**Status:** INCOMPATIBLE - Requires workarounds

**Key Points:**
- Uses Flask `g` object for storage
- Requires app context to access `db.session`
- Standard `ModelView(User, db.session)` pattern FAILS
- Error: `RuntimeError: Working outside of application context`
- **Workarounds available** (see FLASK_SQLALCHEMY_LITE_RESULTS.md)

**Root Cause:**
`db.session` is a property that accesses Flask's `g` object, which requires an active application context. This context doesn't exist during ModelView initialization.

## How to Use This Documentation

### If You're Using Flask-SQLAlchemy
1. Read [SUMMARY.md](SUMMARY.md) for reassurance
2. Optionally read [SESSION_SCOPING_INVESTIGATION.md](SESSION_SCOPING_INVESTIGATION.md) for details
3. Run [reproduction_script.py](reproduction_script.py) to verify

### If You're Using flask-sqlalchemy-lite
1. **IMPORTANT:** Read [FLASK_SQLALCHEMY_LITE_RESULTS.md](FLASK_SQLALCHEMY_LITE_RESULTS.md)
2. Implement the LazySessionWrapper workaround
3. Consider switching to Flask-SQLAlchemy

### If You're Deciding Which to Use
1. Read [FINAL_SUMMARY.md](FINAL_SUMMARY.md) for complete comparison
2. **Recommendation:** Use Flask-SQLAlchemy with Flask-Admin

### If You Want to Verify the Findings
1. Clone the repository
2. Run `pytest flask_admin/tests/sqla/test_session_scoping.py -v`
3. Run `python reproduction_script.py`
4. Run `python test_lite_standalone.py`

## Original Issue Context

**Issue:** pallets-eco/flask-admin#2675  
**Question:** Does Flask-Admin hold a single session for the entire app lifetime?  
**Answer:** No, it uses request-scoped sessions (when using Flask-SQLAlchemy)

**Confusion Source:**
Users see that `ModelView` stores `db.session` once at initialization and worry it's the same session forever. However, `db.session` is a **proxy object** that returns different session instances per request.

## Key Takeaways

1. **Flask-SQLAlchemy:** ✓ Works correctly, request-scoped sessions
2. **flask-sqlalchemy-lite:** ✗ Not compatible without workarounds
3. **Original concern:** Unfounded for Flask-SQLAlchemy
4. **Recommendation:** Use Flask-SQLAlchemy with Flask-Admin

## Contributing to This Investigation

If you find issues or have additional test cases:
1. Check existing test files
2. Add new tests to appropriate test file
3. Update relevant documentation
4. Submit PR with findings

## Questions?

- **"Does Flask-Admin work with Flask-SQLAlchemy?"** → Yes! ✓
- **"Is it safe to use `ModelView(User, db.session)`?"** → Yes with Flask-SQLAlchemy ✓
- **"Does Flask-Admin work with flask-sqlalchemy-lite?"** → No, needs workarounds ✗
- **"Should I worry about app-lifetime sessions?"** → No with Flask-SQLAlchemy ✓
- **"Which library should I use?"** → Flask-SQLAlchemy ✓

---

**Investigation Complete:** October 18, 2025  
**Total Documents:** 11 files  
**Total Tests:** 6 test functions  
**Lines of Code:** 1000+ (tests + docs)  
**Status:** Comprehensive investigation completed ✓
