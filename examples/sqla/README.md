# Flask-Admin SQLAlchemy Example with Audit Log System

A comprehensive example demonstrating Flask-Admin's SQLAlchemy integration, enhanced with a complete **Audit Log System** that automatically tracks all database changes.

> **Note:** This is a fork of the official [Flask-Admin](https://github.com/flask-admin/flask-admin) repository with additional audit logging functionality.

---

## Table of Contents

- [Introduction](#introduction)
- [Audit Log Feature](#audit-log-feature)
- [How It Works](#how-it-works)
- [Database Schema](#database-schema)
- [Admin Interface](#admin-interface)
- [Getting Started](#getting-started)
- [Testing the Audit Log](#testing-the-audit-log)
- [Technologies Used](#technologies-used)
- [Credits](#credits)

---

## Introduction

This project extends the standard Flask-Admin SQLAlchemy example with a powerful audit logging system. It demonstrates how to:

- Build administrative interfaces with Flask-Admin
- Use SQLAlchemy ORM with various field types
- Implement automatic change tracking using SQLAlchemy event listeners
- Create read-only admin views for audit trails

The audit log feature is essential for applications that require:

- **Compliance** - Meet regulatory requirements (GDPR, HIPAA, SOX)
- **Security** - Track who changed what and when
- **Debugging** - Understand how data evolved over time
- **Accountability** - Maintain a complete history of all modifications

---

## Audit Log Feature

The Audit Log System automatically captures all Create, Update, and Delete operations on the following models:

| Model | Description |
|-------|-------------|
| **User** | User accounts with contact details, preferences |
| **Post** | Blog posts with tags and metadata |
| **Tag** | Categorization tags for posts |
| **Tree** | Hierarchical tree structure with parent-child relationships |

### What Gets Logged

| Action | Old Values | New Values |
|--------|------------|------------|
| **CREATE** | - | All field values of the new record |
| **UPDATE** | Previous values of changed fields | New values of changed fields |
| **DELETE** | All field values before deletion | - |

---

## How It Works

### SQLAlchemy Event Listeners Architecture

The audit system leverages SQLAlchemy's powerful event system to intercept database operations without modifying existing code. Three event listeners are registered for each audited model:

```
┌─────────────────────────────────────────────────────────────┐
│                    SQLAlchemy ORM                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   Model.save()  ──────►  after_insert  ──────►  AuditLog   │
│                                                  (CREATE)   │
│                                                             │
│   Model.update() ─────►  after_update  ──────►  AuditLog   │
│                                                  (UPDATE)   │
│                                                             │
│   Model.delete() ─────►  after_delete  ──────►  AuditLog   │
│                                                  (DELETE)   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Event Listeners Explained

#### 1. `after_insert` Listener
Triggered after a new record is inserted into the database.

```python
@event.listens_for(Model, "after_insert")
def _after_insert_listener(mapper, connection, target):
    # Captures all field values of the newly created record
    # Stores them as JSON in the 'new_values' column
```

#### 2. `after_update` Listener
Triggered after an existing record is modified.

```python
@event.listens_for(Model, "after_update")
def _after_update_listener(mapper, connection, target):
    # Uses SQLAlchemy's history API to detect changed fields
    # Captures both old and new values for changed fields only
```

#### 3. `after_delete` Listener
Triggered after a record is deleted from the database.

```python
@event.listens_for(Model, "after_delete")
def _after_delete_listener(mapper, connection, target):
    # Captures all field values before deletion
    # Stores them as JSON in the 'old_values' column
```

### Key Implementation Details

- **Automatic Registration**: Event listeners are registered at module load time for all audited models
- **JSON Serialization**: Complex types (UUID, datetime, enum) are automatically serialized to JSON-compatible formats
- **Change Detection**: For updates, only modified fields are logged using SQLAlchemy's `get_history()` function
- **Self-Protection**: The AuditLog model itself is excluded from auditing to prevent infinite loops

---

## Database Schema

### AuditLog Table

| Column | Type | Description |
|--------|------|-------------|
| `id` | Integer | Primary key, auto-incremented |
| `action` | Enum | Action type: `CREATE`, `UPDATE`, or `DELETE` |
| `model_name` | String(100) | Name of the affected model (e.g., "User", "Post") |
| `record_id` | String(100) | Primary key of the affected record (supports UUID) |
| `old_values` | Text | JSON string of previous values (for UPDATE/DELETE) |
| `new_values` | Text | JSON string of new values (for CREATE/UPDATE) |
| `timestamp` | DateTime | UTC timestamp when the action occurred |

### Example Log Entries

**CREATE Example:**
```json
{
  "action": "CREATE",
  "model_name": "Tag",
  "record_id": "5",
  "old_values": null,
  "new_values": "{\"id\": 5, \"name\": \"PYTHON\"}",
  "timestamp": "2024-01-15T10:30:00"
}
```

**UPDATE Example:**
```json
{
  "action": "UPDATE",
  "model_name": "Post",
  "record_id": "12",
  "old_values": "{\"title\": \"Old Title\"}",
  "new_values": "{\"title\": \"New Title\"}",
  "timestamp": "2024-01-15T11:45:00"
}
```

**DELETE Example:**
```json
{
  "action": "DELETE",
  "model_name": "User",
  "record_id": "abc-123-uuid",
  "old_values": "{\"first_name\": \"John\", \"last_name\": \"Doe\", ...}",
  "new_values": null,
  "timestamp": "2024-01-15T14:20:00"
}
```

---

## Admin Interface

### Audit Log View Features

The Audit Log admin view is designed for **read-only access** to maintain data integrity:

| Feature | Description |
|---------|-------------|
| **Read-Only** | Cannot create, edit, or delete audit entries |
| **Sortable** | Default sort by timestamp (newest first) |
| **Filterable** | Filter by action type, model name, record ID, timestamp |
| **Searchable** | Search by model name or record ID |
| **Detail View** | View full JSON of old/new values |

### Available Filters

- **Action** - Filter by CREATE, UPDATE, or DELETE
- **Model Name** - Filter by specific model (User, Post, Tag, Tree)
- **Record ID** - Find all changes to a specific record
- **Timestamp** - Filter by date range

### Custom Theme

The admin interface features a modern, professional design with:

- Dark gradient background
- Purple/pink gradient navigation bar
- Styled cards, buttons, and tables
- Responsive layout for mobile devices
- Matching landing page with language selection

---

## Getting Started

### Prerequisites

- Python 3.10 or higher
- Git

### Step 1: Clone the Repository

```bash
git clone https://github.com/Neha-1216/flask-admin.git
cd flask-admin/examples/sqla
```

### Step 2: Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -e "../../[sqlalchemy-with-utils,export,translation]"
```

This installs Flask-Admin with all required extras:
- `sqlalchemy-with-utils` - SQLAlchemy support with utility types
- `export` - CSV/Excel export functionality
- `translation` - Multi-language support

### Step 4: Run the Application

```bash
python main.py
```

The application will:
1. Create a SQLite database (`admin/db.sqlite`)
2. Populate it with sample data (25 users, 25 posts, 9 tags, 31 tree nodes)
3. Start the development server

### Step 5: Access the Admin Panel

1. Open your browser and go to: **http://127.0.0.1:5000**
2. Select your preferred language
3. You'll be redirected to the Flask-Admin dashboard

### Navigation

| URL | Description |
|-----|-------------|
| `http://127.0.0.1:5000` | Language selection page |
| `http://127.0.0.1:5000/admin/` | Admin dashboard |
| `http://127.0.0.1:5000/admin/user/` | User management |
| `http://127.0.0.1:5000/admin/post/` | Post management |
| `http://127.0.0.1:5000/admin/tag/` | Tag management |
| `http://127.0.0.1:5000/admin/auditlog/` | Audit log viewer |

---

## Testing the Audit Log

Follow these steps to verify the audit logging functionality:

### Test 1: CREATE Action

1. Navigate to **Tag** in the admin menu
2. Click the **Create** button
3. Enter a name (e.g., "TEST_TAG") and save
4. Go to **Other → Audit Log**
5. Verify a new entry with:
   - Action: `CREATE`
   - Model Name: `Tag`
   - New Values: Contains the tag data

### Test 2: UPDATE Action

1. Navigate to **Tag**
2. Click the edit icon next to your test tag
3. Change the name to "UPDATED_TAG" and save
4. Go to **Other → Audit Log**
5. Verify a new entry with:
   - Action: `UPDATE`
   - Old Values: `{"name": "TEST_TAG"}`
   - New Values: `{"name": "UPDATED_TAG"}`

### Test 3: DELETE Action

1. Navigate to **Tag**
2. Select the checkbox next to your test tag
3. Choose "Delete" from the "With selected" dropdown
4. Confirm the deletion
5. Go to **Other → Audit Log**
6. Verify a new entry with:
   - Action: `DELETE`
   - Old Values: Contains all tag data before deletion

### Test 4: Using Filters

1. In the Audit Log view, click **Add Filter**
2. Select **Action** → **equals** → **CREATE**
3. Apply the filter to see only creation events
4. Try filtering by **Model Name** to see changes for specific tables

---

## Technologies Used

| Technology | Purpose |
|------------|---------|
| **Python 3.10+** | Programming language |
| **Flask** | Web framework |
| **Flask-Admin** | Admin interface generator |
| **SQLAlchemy** | ORM for database operations |
| **Flask-SQLAlchemy** | Flask integration for SQLAlchemy |
| **SQLAlchemy-Utils** | Additional column types (UUID, Email, URL, etc.) |
| **Flask-Babel** | Internationalization support |
| **SQLite** | Database (for demo purposes) |
| **Bootstrap 4** | Frontend styling |
| **WTForms** | Form handling and validation |

---

## Project Structure

```
examples/sqla/
├── admin/
│   ├── __init__.py          # Flask app and database setup
│   ├── models.py             # SQLAlchemy models + AuditLog + event listeners
│   ├── main.py               # Admin views and routes
│   ├── data.py               # Sample data generation
│   ├── static/
│   │   ├── css/
│   │   │   └── custom-theme.css  # Custom admin theme
│   │   └── favicon.ico
│   └── templates/
│       └── admin/
│           ├── master.html   # Custom master template
│           └── index.html    # Custom dashboard
├── main.py                   # Application entry point
├── pyproject.toml            # Project dependencies
├── README.md                 # This file
└── venv/                     # Virtual environment (not in repo)
```

---

## Credits

- **Original Repository:** [flask-admin/flask-admin](https://github.com/flask-admin/flask-admin)
- **Flask-Admin Documentation:** [flask-admin.readthedocs.io](https://flask-admin.readthedocs.io/)
- **SQLAlchemy Events:** [SQLAlchemy Event System](https://docs.sqlalchemy.org/en/14/core/event.html)

---

## License

This project is licensed under the same terms as Flask-Admin. See the [LICENSE](../../LICENSE) file in the root directory for details.
