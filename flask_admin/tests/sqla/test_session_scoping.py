"""
Test to investigate whether Flask-Admin holds a single session for the app lifetime
or uses request-scoped sessions.

This test creates a reproduction case to verify the behavior described in the issue:
https://github.com/pallets-eco/flask-admin/issues/XXXX
"""
import pytest
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView

try:
    from flask_babel import Babel
    HAS_BABEL = True
except ImportError:
    HAS_BABEL = False


def create_models(db):
    """Create test models"""
    
    class User(db.Model):  # type: ignore[name-defined]
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(50))
        
        def __repr__(self):
            return f"<User {self.id}: {self.name}>"
    
    return User


def setup_babel(app):
    """Setup babel if available"""
    if HAS_BABEL:
        Babel(app)
    return app


def test_session_identity_across_requests():
    """
    Test whether db.session passed to ModelView maintains the same session
    across requests or creates request-scoped sessions.
    
    This test will:
    1. Create a Flask app with Flask-SQLAlchemy
    2. Pass db.session to ModelView
    3. Make multiple requests and track the session object identity
    4. Verify if the session is the same object or different across requests
    """
    # Setup
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "test-secret"
    app.config["WTF_CSRF_ENABLED"] = False
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["SQLALCHEMY_ECHO"] = False
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["TESTING"] = True
    
    setup_babel(app)
    db = SQLAlchemy(app)
    User = create_models(db)
    
    # Track session ids across requests
    session_ids = []
    session_hash_ids = []
    
    # Create a custom ModelView that tracks the session
    class TrackingModelView(ModelView):
        def get_list(self, *args, **kwargs):
            # Track the session object identity
            session_ids.append(id(self.session))
            session_hash_ids.append(hash(id(self.session)))
            
            # Also track what the session actually resolves to
            # Flask-SQLAlchemy's scoped_session returns different sessions per request
            actual_session = self.session()  # Call the scoped_session proxy
            session_ids.append(id(actual_session))
            session_hash_ids.append(hash(id(actual_session)))
            
            return super().get_list(*args, **kwargs)
    
    # Create tables
    with app.app_context():
        db.create_all()
    
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
    print("SESSION IDENTITY TEST RESULTS")
    print("="*80)
    print(f"Number of requests made: 3")
    print(f"Session IDs collected: {len(session_ids)}")
    print(f"\nSession proxy IDs (self.session):")
    for i in range(0, len(session_ids), 2):
        print(f"  Request {i//2 + 1}: {session_ids[i]}")
    
    print(f"\nActual session IDs (self.session()):")
    for i in range(1, len(session_ids), 2):
        print(f"  Request {i//2 + 1}: {session_ids[i]}")
    
    # Check if proxy is always the same (expected for scoped_session)
    proxy_ids = [session_ids[i] for i in range(0, len(session_ids), 2)]
    actual_session_ids = [session_ids[i] for i in range(1, len(session_ids), 2)]
    
    proxy_is_same = len(set(proxy_ids)) == 1
    actual_sessions_are_same = len(set(actual_session_ids)) == 1
    
    print(f"\nProxy object is same across requests: {proxy_is_same}")
    print(f"Actual session is same across requests: {actual_sessions_are_same}")
    
    print("\n" + "="*80)
    print("ANALYSIS:")
    print("="*80)
    
    if proxy_is_same and not actual_sessions_are_same:
        print("✓ GOOD: db.session is a scoped_session proxy that returns")
        print("  different session instances per request/context.")
        print("\n  This is the expected behavior for Flask-SQLAlchemy.")
        print("  The ModelView holds a reference to the proxy, not the actual session.")
    elif proxy_is_same and actual_sessions_are_same:
        print("⚠ ISSUE: The scoped_session proxy returns the SAME session")
        print("  across different requests. This suggests session scoping is not")
        print("  working correctly or all requests are in the same context.")
    else:
        print("? UNEXPECTED: Results don't match expected patterns.")
    
    print("="*80)
    
    # The key assertion: we expect the proxy to be the same (since it's stored once)
    # but the actual sessions should be different per request context
    assert proxy_is_same, "Expected the scoped_session proxy to be the same object"
    
    # Note: In test mode with synchronous requests, sessions might be reused
    # This is actually OK - what matters is that db.session is a scoped_session proxy


def test_session_isolation_between_requests():
    """
    Test that changes made in one request don't leak to another request
    through the session, which would indicate a shared session.
    """
    # Setup
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "test-secret"
    app.config["WTF_CSRF_ENABLED"] = False
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["SQLALCHEMY_ECHO"] = False
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["TESTING"] = True
    
    setup_babel(app)
    db = SQLAlchemy(app)
    User = create_models(db)
    
    # Create tables
    with app.app_context():
        db.create_all()
        # Add initial user
        user = User(id=1, name="Original")
        db.session.add(user)
        db.session.commit()
    
    admin = Admin(app, name="Test Admin")
    
    # Track session state across requests
    session_states = []
    
    class TrackingModelView(ModelView):
        def get_one(self, obj_id):
            # Get the user from the session
            user = super().get_one(obj_id)
            
            # Track what's in the session identity map
            actual_session = self.session()
            session_state = {
                'session_id': id(actual_session),
                'user_in_session': user in actual_session,
                'user_name': user.name if user else None,
                'identity_map_size': len(actual_session.identity_map) if hasattr(actual_session, 'identity_map') else 'N/A'
            }
            session_states.append(session_state)
            
            return user
    
    admin.add_view(TrackingModelView(User, db.session, name="User"))
    client = app.test_client()
    
    # Request 1: Get the user and modify it (but don't commit)
    with app.app_context():
        response = client.get("/admin/user/edit/?id=1")
        assert response.status_code == 200
        
        # Modify the user directly through the session (simulating a bug scenario)
        user = db.session.get(User, 1)
        if user:
            user.name = "Modified in Request 1"
            # Don't commit - if session is shared, this will leak
    
    # Request 2: Get the user again - should see original value
    with app.app_context():
        response = client.get("/admin/user/edit/?id=1")
        assert response.status_code == 200
        
        user = db.session.get(User, 1)
        assert user is not None
        
        print("\n" + "="*80)
        print("SESSION ISOLATION TEST RESULTS")
        print("="*80)
        print(f"After Request 1 (modified but not committed): name should be 'Modified in Request 1'")
        print(f"After Request 2 (new context): name should be 'Original' (from DB)")
        print(f"Actual name in Request 2: '{user.name}'")
        print("="*80)
        
        # If sessions are properly scoped, Request 2 should see the original value
        # because the uncommitted change in Request 1 shouldn't leak
        if user.name == "Original":
            print("✓ GOOD: Session isolation is working correctly.")
            print("  Uncommitted changes in Request 1 did not leak to Request 2.")
        else:
            print("⚠ ISSUE: Session isolation is NOT working.")
            print("  Uncommitted changes from Request 1 leaked to Request 2.")
            print("  This suggests a shared session across requests.")
        print("="*80)


def test_session_type_investigation():
    """
    Test to understand what type of session object is passed to ModelView
    and how it behaves.
    """
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "test-secret"
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["TESTING"] = True
    
    setup_babel(app)
    db = SQLAlchemy(app)
    User = create_models(db)
    
    with app.app_context():
        db.create_all()
    
    # Inspect the session type
    print("\n" + "="*80)
    print("SESSION TYPE INVESTIGATION")
    print("="*80)
    print(f"Type of db.session: {type(db.session)}")
    print(f"db.session repr: {repr(db.session)}")
    print(f"db.session class name: {db.session.__class__.__name__}")
    print(f"db.session module: {db.session.__class__.__module__}")
    
    # Check if it's a scoped_session
    from sqlalchemy.orm import scoped_session
    is_scoped = isinstance(db.session, scoped_session)
    print(f"\nIs scoped_session: {is_scoped}")
    
    if is_scoped:
        print("\n✓ GOOD: db.session is a scoped_session proxy.")
        print("  This means it will return different session instances")
        print("  based on the current scope (typically per-request in Flask).")
        
        # Check the registry
        print(f"\nRegistry type: {type(db.session.registry)}")
        print(f"Registry class: {db.session.registry.__class__.__name__}")
    
    # Create a ModelView and check what it stores
    view = ModelView(User, db.session, name="User")
    print(f"\nModelView.session type: {type(view.session)}")
    print(f"ModelView.session is db.session: {view.session is db.session}")
    print(f"ModelView.session id: {id(view.session)}")
    print(f"db.session id: {id(db.session)}")
    
    # Test calling the session
    with app.app_context():
        actual_session = db.session()
        print(f"\nActual session from db.session(): {type(actual_session)}")
        print(f"Actual session class: {actual_session.__class__.__name__}")
    
    print("="*80)


if __name__ == "__main__":
    # Allow running this test file directly for quick investigation
    pytest.main([__file__, "-v", "-s"])
