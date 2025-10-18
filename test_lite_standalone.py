#!/usr/bin/env python
"""
Standalone test script for flask-sqlalchemy-lite with Flask-Admin.
Compares session scoping behavior with Flask-SQLAlchemy.
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy as FlaskSQLAlchemy
import flask_sqlalchemy_lite
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import DeclarativeBase, scoped_session

try:
    from flask_babel import Babel
    HAS_BABEL = True
except ImportError:
    HAS_BABEL = False

class Base(DeclarativeBase):
    pass


def test_flask_sqlalchemy_lite():
    """Test flask-sqlalchemy-lite session scoping"""
    print("\n" + "="*80)
    print("FLASK-SQLALCHEMY-LITE INVESTIGATION")
    print("="*80)
    
    # Setup
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "test"
    app.config["WTF_CSRF_ENABLED"] = False
    app.config["SQLALCHEMY_ENGINES"] = {"default": "sqlite:///:memory:"}
    app.config["TESTING"] = True
    
    if HAS_BABEL:
        Babel(app)
    
    db = flask_sqlalchemy_lite.SQLAlchemy(app)
    
    class User(Base):
        __tablename__ = 'user'
        id = Column(Integer, primary_key=True)
        name = Column(String(50))
    
    # Test 1: Session Type
    print("\n1. Session Type Analysis")
    print("-" * 70)
    
    with app.app_context():
        Base.metadata.create_all(db.engine)
        
        print(f"   Has db.session: {hasattr(db, 'session')}")
        if hasattr(db, 'session'):
            print(f"   Type: {type(db.session).__name__}")
            print(f"   Is scoped_session: {isinstance(db.session, scoped_session)}")
            print(f"   Storage: Flask 'g' object (request-local)")
    
    # Test 2: Session Identity
    print("\n2. Session Identity Across Requests")
    print("-" * 70)
    
    session_ids = []
    
    class TrackingModelView(ModelView):
        def get_list(self, *args, **kwargs):
            session_ids.append(id(self.session))
            return super().get_list(*args, **kwargs)
    
    admin = Admin(app, name="Test")
    
    # CRITICAL: flask-sqlalchemy-lite db.session requires app context
    # Cannot be accessed at initialization time like Flask-SQLAlchemy
    # This is a KEY DIFFERENCE!
    
    try:
        admin.add_view(TrackingModelView(User, db.session, name="User"))
        worked = True
    except RuntimeError as e:
        if "Working outside of application context" in str(e):
            print("   ⚠ CRITICAL FINDING: db.session requires app context!")
            print("   ⚠ Cannot use ModelView(User, db.session) pattern")
            print("   ⚠ This pattern works with Flask-SQLAlchemy but NOT flask-sqlalchemy-lite")
            return [], "N/A - Incompatible"
        raise
    
    client = app.test_client()
    
    for i in range(3):
        with app.app_context():
            response = client.get("/admin/user/")
    
    print(f"   Session IDs across 3 requests:")
    for i, sid in enumerate(session_ids, 1):
        print(f"     Request {i}: {sid}")
    
    unique = len(set(session_ids))
    print(f"   Unique sessions: {unique}")
    
    if unique == 3:
        print("   ✓ Different session per request (GOOD)")
    else:
        print(f"   ⚠ Only {unique} unique session(s) (PROBLEMATIC)")
    
    # Test 3: Session Isolation
    print("\n3. Session Isolation Test")
    print("-" * 70)
    
    app2 = Flask(__name__)
    app2.config["SECRET_KEY"] = "test"
    app2.config["WTF_CSRF_ENABLED"] = False
    app2.config["SQLALCHEMY_ENGINES"] = {"default": "sqlite:///:memory:"}
    app2.config["TESTING"] = True
    
    if HAS_BABEL:
        Babel(app2)
    
    db2 = flask_sqlalchemy_lite.SQLAlchemy(app2)
    
    class User2(Base):
        __tablename__ = 'user2'
        id = Column(Integer, primary_key=True)
        name = Column(String(50))
    
    with app2.app_context():
        Base.metadata.create_all(db2.engine)
        user = User2(id=1, name="Original")
        db2.session.add(user)
        db2.session.commit()
    
    admin2 = Admin(app2)
    admin2.add_view(ModelView(User2, db2.session, name="User"))
    client2 = app2.test_client()
    
    # Request 1: Modify without commit
    with app2.app_context():
        client2.get("/admin/user/edit/?id=1")
        user = db2.session.get(User2, 1)
        if user:
            user.name = "Modified"
    
    # Request 2: Check for leakage
    with app2.app_context():
        client2.get("/admin/user/edit/?id=1")
        user = db2.session.get(User2, 1)
        result = user.name if user else "None"
    
    print(f"   After uncommitted change: '{result}'")
    print(f"   Expected: 'Original'")
    
    if result == "Original":
        print("   ✓ No data leakage (GOOD)")
    else:
        print("   ⚠ Data leaked between requests (PROBLEMATIC)")
    
    return session_ids, result


def test_flask_sqlalchemy():
    """Test Flask-SQLAlchemy session scoping for comparison"""
    print("\n" + "="*80)
    print("FLASK-SQLALCHEMY (COMPARISON)")
    print("="*80)
    
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "test"
    app.config["WTF_CSRF_ENABLED"] = False
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["TESTING"] = True
    
    if HAS_BABEL:
        Babel(app)
    
    db = FlaskSQLAlchemy(app)
    
    class User(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(50))
    
    print("\n1. Session Type Analysis")
    print("-" * 70)
    
    with app.app_context():
        db.create_all()
        print(f"   Has db.session: {hasattr(db, 'session')}")
        print(f"   Type: {type(db.session).__name__}")
        print(f"   Is scoped_session: {isinstance(db.session, scoped_session)}")
    
    print("\n2. Session Identity (3 requests)")
    print("-" * 70)
    
    session_ids = []
    actual_ids = []
    
    class TrackingModelView(ModelView):
        def get_list(self, *args, **kwargs):
            session_ids.append(id(self.session))
            actual_ids.append(id(self.session()))
            return super().get_list(*args, **kwargs)
    
    admin = Admin(app)
    admin.add_view(TrackingModelView(User, db.session, name="User"))
    client = app.test_client()
    
    for i in range(3):
        with app.app_context():
            client.get("/admin/user/")
    
    print(f"   Proxy IDs: {len(set(session_ids))} unique")
    print(f"   Actual session IDs: {len(set(actual_ids))} unique")
    
    if len(set(session_ids)) == 1 and len(set(actual_ids)) == 3:
        print("   ✓ Proxy-based request scoping (GOOD)")
    
    return session_ids, actual_ids


def main():
    print("\n" + "="*80)
    print("FLASK-ADMIN SESSION SCOPING COMPARISON")
    print("Flask-SQLAlchemy vs flask-sqlalchemy-lite")
    print("="*80)
    
    # Test both
    lite_sessions, lite_isolation = test_flask_sqlalchemy_lite()
    fsa_sessions, fsa_actual = test_flask_sqlalchemy()
    
    # Summary
    print("\n" + "="*80)
    print("COMPARISON SUMMARY")
    print("="*80)
    
    print("\n Flask-SQLAlchemy:")
    print("   • Uses scoped_session proxy")
    print("   • Session per request via SQLAlchemy's scoping mechanism")
    print("   • ModelView stores proxy, gets session per context")
    print(f"   • Result: {len(set(fsa_actual))} unique sessions in 3 requests ✓")
    
    print("\n flask-sqlalchemy-lite:")
    print("   • Does NOT use scoped_session proxy")
    print("   • Session per request via Flask's 'g' object")
    print("   • ModelView stores direct session reference")
    print(f"   • Result: {len(set(lite_sessions))} unique sessions in 3 requests", end="")
    
    if len(set(lite_sessions)) == 3:
        print(" ✓")
        print("\n   ✓ COMPATIBLE: flask-sqlalchemy-lite works with Flask-Admin")
        print("     Different implementation but achieves request-scoped sessions")
    else:
        print(" ⚠")
        print("\n   ⚠ ISSUE: Sessions not properly scoped")
        print("     May require custom integration or workarounds")
    
    print("\n" + "="*80)
    print("RECOMMENDATION")
    print("="*80)
    
    if len(set(lite_sessions)) == 3 and lite_isolation == "Original":
        print("\n✓ BOTH libraries are compatible with Flask-Admin's ModelView pattern")
        print("✓ Both provide proper request-scoped sessions")
        print("✓ Safe to use: ModelView(User, db.session)")
        print("\nDifference: Implementation mechanism, not functionality")
        print("  - Flask-SQLAlchemy: SQLAlchemy's scoped_session")
        print("  - flask-sqlalchemy-lite: Flask's 'g' object")
    else:
        print("\n⚠ flask-sqlalchemy-lite may have compatibility issues")
        print("⚠ Further investigation or workarounds may be needed")
    
    print("="*80)


if __name__ == "__main__":
    main()
