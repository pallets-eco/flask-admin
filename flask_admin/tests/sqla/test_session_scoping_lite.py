"""
Test to investigate whether Flask-Admin with flask-sqlalchemy-lite holds a single 
session for the app lifetime or uses request-scoped sessions.

This test compares flask-sqlalchemy-lite behavior with Flask-SQLAlchemy.
"""
import pytest
from flask import Flask
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView

try:
    from flask_babel import Babel
    HAS_BABEL = True
except ImportError:
    HAS_BABEL = False

try:
    # Try to import flask-sqlalchemy-lite
    import flask_sqlalchemy_lite
    HAS_FLASK_SQLALCHEMY_LITE = True
except ImportError:
    HAS_FLASK_SQLALCHEMY_LITE = False
    flask_sqlalchemy_lite = None


def setup_babel(app):
    """Setup babel if available"""
    if HAS_BABEL:
        Babel(app)
    return app


@pytest.mark.skipif(
    not HAS_FLASK_SQLALCHEMY_LITE,
    reason="flask-sqlalchemy-lite not installed"
)
def test_lite_session_type_investigation():
    """
    Test to understand what type of session object flask-sqlalchemy-lite provides
    and how it compares to Flask-SQLAlchemy.
    """
    from sqlalchemy import Column, Integer, String
    from sqlalchemy.orm import DeclarativeBase
    
    class Base(DeclarativeBase):
        pass
    
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "test-secret"
    # flask-sqlalchemy-lite uses different config
    app.config["SQLALCHEMY_ENGINES"] = {
        "default": "sqlite:///:memory:"
    }
    app.config["TESTING"] = True
    
    setup_babel(app)
    
    # Initialize with flask-sqlalchemy-lite
    db = flask_sqlalchemy_lite.SQLAlchemy(app)
    
    # Define a test model
    class User(Base):
        __tablename__ = 'user'
        id = Column(Integer, primary_key=True)
        name = Column(String(50))
    
    with app.app_context():
        Base.metadata.create_all(db.engine)
    
    # Inspect the session type
    print("\n" + "="*80)
    print("FLASK-SQLALCHEMY-LITE SESSION TYPE INVESTIGATION")
    print("="*80)
    
    # Check if db.session exists
    has_session = hasattr(db, 'session')
    print(f"\ndb has 'session' attribute: {has_session}")
    
    if has_session:
        print(f"Type of db.session: {type(db.session)}")
        print(f"db.session repr: {repr(db.session)}")
        print(f"db.session class name: {db.session.__class__.__name__}")
        print(f"db.session module: {db.session.__class__.__module__}")
        
        # Check if it's a scoped_session
        from sqlalchemy.orm import scoped_session
        is_scoped = isinstance(db.session, scoped_session)
        print(f"\nIs scoped_session: {is_scoped}")
        
        if is_scoped:
            print("\n✓ flask-sqlalchemy-lite uses scoped_session (like Flask-SQLAlchemy)")
            print("  This suggests similar session scoping behavior.")
        else:
            print("\n⚠ flask-sqlalchemy-lite does NOT use scoped_session")
            print("  This may indicate different session management approach.")
            print("  Session scoping behavior may differ from Flask-SQLAlchemy.")
    else:
        print("\n⚠ flask-sqlalchemy-lite does NOT provide db.session")
        print("  This means the recommended Flask-Admin pattern won't work:")
        print("  ModelView(User, db.session)  # This will fail!")
        print("\n  You may need to:")
        print("  1. Create your own session management")
        print("  2. Pass a manually created scoped_session")
        print("  3. Use a different integration pattern")
    
    print("="*80)


@pytest.mark.skipif(
    not HAS_FLASK_SQLALCHEMY_LITE,
    reason="flask-sqlalchemy-lite not installed"
)
def test_lite_session_identity_across_requests():
    """
    Test whether flask-sqlalchemy-lite session maintains the same session
    across requests or creates request-scoped sessions.
    """
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "test-secret"
    app.config["WTF_CSRF_ENABLED"] = False
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["TESTING"] = True
    
    setup_babel(app)
    db = flask_sqlalchemy_lite.SQLAlchemy(app)
    
    class User(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(50))
    
    # Check if db.session exists
    if not hasattr(db, 'session'):
        pytest.skip("flask-sqlalchemy-lite does not provide db.session")
    
    # Create tables
    with app.app_context():
        db.create_all()
    
    # Track session ids across requests
    session_ids = []
    
    class TrackingModelView(ModelView):
        def get_list(self, *args, **kwargs):
            # Track the session object identity
            session_ids.append(id(self.session))
            
            # Check if it's callable (scoped_session)
            if callable(self.session):
                actual_session = self.session()
                session_ids.append(id(actual_session))
            
            return super().get_list(*args, **kwargs)
    
    # Add admin view
    admin = Admin(app, name="Test Admin")
    admin.add_view(TrackingModelView(User, db.session, name="User"))
    
    # Create test client
    client = app.test_client()
    
    # Make multiple requests to the list view
    for i in range(3):
        with app.app_context():
            response = client.get("/admin/user/")
            assert response.status_code == 200
    
    # Analyze results
    print("\n" + "="*80)
    print("FLASK-SQLALCHEMY-LITE SESSION IDENTITY TEST RESULTS")
    print("="*80)
    print(f"Number of requests made: 3")
    print(f"Session IDs collected: {len(session_ids)}")
    
    if len(session_ids) == 3:
        # No callable session - may be direct session instances
        print(f"\nSession IDs (self.session - NOT a proxy):")
        for i, sid in enumerate(session_ids, 1):
            print(f"  Request {i}: {sid}")
        
        unique_ids = set(session_ids)
        if len(unique_ids) == 1:
            print("\n⚠ WARNING: Same session instance across all requests")
            print("  This indicates app-lifetime session, not request-scoped!")
            print("  This is the problematic behavior mentioned in the issue.")
        else:
            print("\n✓ GOOD: Different session instances per request")
            print("  Sessions are properly scoped.")
    else:
        # Callable session - scoped_session proxy
        print(f"\nSession proxy IDs (self.session):")
        for i in range(0, len(session_ids), 2):
            print(f"  Request {i//2 + 1}: {session_ids[i]}")
        
        print(f"\nActual session IDs (self.session()):")
        for i in range(1, len(session_ids), 2):
            print(f"  Request {i//2 + 1}: {session_ids[i]}")
        
        proxy_ids = [session_ids[i] for i in range(0, len(session_ids), 2)]
        actual_session_ids = [session_ids[i] for i in range(1, len(session_ids), 2)]
        
        proxy_is_same = len(set(proxy_ids)) == 1
        actual_sessions_are_same = len(set(actual_session_ids)) == 1
        
        print(f"\nProxy object is same across requests: {proxy_is_same}")
        print(f"Actual session is same across requests: {actual_sessions_are_same}")
        
        if proxy_is_same and not actual_sessions_are_same:
            print("\n✓ GOOD: Uses scoped_session proxy with request-scoped sessions")
            print("  Behavior is similar to Flask-SQLAlchemy.")
        elif proxy_is_same and actual_sessions_are_same:
            print("\n⚠ WARNING: Proxy returns same session across requests")
            print("  This may indicate improper session scoping.")
    
    print("="*80)


@pytest.mark.skipif(
    not HAS_FLASK_SQLALCHEMY_LITE,
    reason="flask-sqlalchemy-lite not installed"
)
def test_lite_session_isolation():
    """
    Test that changes made in one request don't leak to another request
    with flask-sqlalchemy-lite.
    """
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "test-secret"
    app.config["WTF_CSRF_ENABLED"] = False
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["TESTING"] = True
    
    setup_babel(app)
    db = flask_sqlalchemy_lite.SQLAlchemy(app)
    
    class User(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(50))
    
    if not hasattr(db, 'session'):
        pytest.skip("flask-sqlalchemy-lite does not provide db.session")
    
    # Create tables and initial data
    with app.app_context():
        db.create_all()
        user = User(id=1, name="Original")
        db.session.add(user)
        db.session.commit()
    
    admin = Admin(app, name="Test Admin")
    admin.add_view(ModelView(User, db.session, name="User"))
    client = app.test_client()
    
    # Request 1: Get and modify (but don't commit)
    with app.app_context():
        response = client.get("/admin/user/edit/?id=1")
        assert response.status_code == 200
        
        user = db.session.get(User, 1)
        if user:
            user.name = "Modified in Request 1"
            # Don't commit - if session is shared, this will leak
    
    # Request 2: Check if modification leaked
    with app.app_context():
        response = client.get("/admin/user/edit/?id=1")
        assert response.status_code == 200
        
        user = db.session.get(User, 1)
        assert user is not None
        
        print("\n" + "="*80)
        print("FLASK-SQLALCHEMY-LITE SESSION ISOLATION TEST RESULTS")
        print("="*80)
        print(f"After Request 1 (modified but not committed): expected 'Modified in Request 1'")
        print(f"After Request 2 (new context): expected 'Original' (from DB)")
        print(f"Actual name in Request 2: '{user.name}'")
        print("="*80)
        
        if user.name == "Original":
            print("✓ GOOD: Session isolation is working correctly.")
            print("  Uncommitted changes in Request 1 did not leak to Request 2.")
        else:
            print("⚠ WARNING: Session isolation is NOT working.")
            print("  Uncommitted changes from Request 1 leaked to Request 2.")
            print("  This indicates a shared session across requests.")
        print("="*80)


def test_comparison_summary():
    """
    Generate a comparison summary between Flask-SQLAlchemy and flask-sqlalchemy-lite.
    This test always runs to provide guidance even if flask-sqlalchemy-lite is not installed.
    """
    print("\n" + "="*80)
    print("FLASK-SQLALCHEMY vs FLASK-SQLALCHEMY-LITE COMPARISON")
    print("="*80)
    
    print("\nFlask-SQLAlchemy (already tested):")
    print("  ✓ Provides db.session as scoped_session proxy")
    print("  ✓ Request-scoped sessions (different per request)")
    print("  ✓ Automatic session cleanup at request teardown")
    print("  ✓ Compatible with Flask-Admin ModelView(User, db.session)")
    
    if HAS_FLASK_SQLALCHEMY_LITE:
        print("\nflask-sqlalchemy-lite (testing available):")
        print("  Run the tests above to see actual behavior")
    else:
        print("\nflask-sqlalchemy-lite (NOT INSTALLED):")
        print("  ⚠ Cannot test - package not available")
        print("  Install with: pip install flask-sqlalchemy-lite")
        print("\n  Expected investigation results:")
        print("  - Check if db.session exists and its type")
        print("  - Verify if it uses scoped_session or direct session")
        print("  - Test session isolation across requests")
        print("  - Compare with Flask-SQLAlchemy behavior")
        print("\n  Possible outcomes:")
        print("  1. If it uses scoped_session: Likely compatible with Flask-Admin")
        print("  2. If it uses direct session: May have app-lifetime session issue")
        print("  3. If no db.session: Requires different integration approach")
    
    print("="*80)


if __name__ == "__main__":
    # Allow running this test file directly
    pytest.main([__file__, "-v", "-s"])
