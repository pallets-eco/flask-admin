from collections import deque
from flask import Flask, render_template
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy_mptt.mixins import BaseNestedSets

# Create application
app = Flask(__name__)

# Create dummy secret key so we can use sessions
app.config["SECRET_KEY"] = "123456790"

# Create in-memory database
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///test.sqlite"
db = SQLAlchemy(app)

# Create models
class Node(db.Model, BaseNestedSets):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(64))

    def __str__(self):
        return self.name


# Administrative class
class NodeAdmin(ModelView):

    list_template = "admin/treelist.html"

    # Allow the AJAX endpoint to update only the parent relationship on each node
    column_editable_list = ["parent"]

    column_list = ["name", "parent_id"]
    form_excluded_columns = ["tree_id", "children", "left", "right", "level"]

    # Retrieve and render only the primary key from each parent key relationship since
    # that's all that is required to associate nodes on the client
    column_formatters = dict(parent=lambda _, __, m, ___: m.parent_id)

    # Pagination can cause partially-rendered (and therefore inconsistent) tree
    # rendering, so it is disabled here
    page_size = 0

    def __init__(self):
        super(NodeAdmin, self).__init__(Node, db.session, name="Nodes")

    def get_list(self, page, sort_column, sort_desc, search, filters,
                 execute=True, page_size=None):
        results = []
        sources = deque(Product.query.filter(Product.parent_id == None))
        while sources:
            product = sources.popleft()
            results.append(product)
            sources.extendleft(product.get_children())
        return len(results), results


# Simple page to list tree nodes
@app.route("/")
def index():
    nodes = Node.get_tree(session=db.session)
    return render_template("nodes.html", nodes=nodes)


if __name__ == "__main__":
    # Create admin
    admin = Admin(app, name="Example: Tree of Models")

    # Add views
    admin.add_view(NodeAdmin())

    # Create DB
    db.create_all()

    # Start app
    app.run(debug=True)
