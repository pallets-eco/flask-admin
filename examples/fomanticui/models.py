import enum

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import Date
from sqlalchemy import DateTime
from sqlalchemy import Enum
from sqlalchemy import Float
from sqlalchemy import ForeignKey
from sqlalchemy import func
from sqlalchemy import Integer
from sqlalchemy import JSON
from sqlalchemy import LargeBinary
from sqlalchemy import Numeric
from sqlalchemy import String
from sqlalchemy import Table
from sqlalchemy import Text
from sqlalchemy import Time
from sqlalchemy.orm import relationship

db = SQLAlchemy()

# ----- Association tables -----
user_roles = Table(
    "user_roles",
    db.Model.metadata,
    Column("user_id", Integer, ForeignKey("user.id"), primary_key=True),
    Column("role_id", Integer, ForeignKey("role.id"), primary_key=True),
)

posts_tags = Table(
    "posts_tags",
    db.Model.metadata,
    Column("post_id", Integer, ForeignKey("post.id"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tag.id"), primary_key=True),
)

# New association table for many-to-many relationship between employees and projects
employees_projects = Table(
    "employees_projects",
    db.Model.metadata,
    Column("employee_id", Integer, ForeignKey("employee.id"), primary_key=True),
    Column("project_id", Integer, ForeignKey("project.id"), primary_key=True),
)

# ----- Enumerations -----


class OrderStatus(enum.Enum):
    pending = "pending"
    paid = "paid"
    shipped = "shipped"
    completed = "completed"
    cancelled = "cancelled"


class PaymentMethod(enum.Enum):
    credit_card = "credit_card"
    paypal = "paypal"
    stripe = "stripe"


class User(db.Model):
    id = Column(Integer, primary_key=True)
    email = Column(String(120), unique=True)
    name = Column(String(64), nullable=False)
    age = Column(Integer, nullable=False)
    active = Column(Boolean, default=False)

    created_at = Column(DateTime, default=func.now())
    last_login = Column(DateTime)

    preferences = Column(JSON)
    balance = Column(Numeric(10, 2), default=0)

    # Relationships
    posts = relationship("Post", back_populates="author")
    addresses = relationship(
        "Address", back_populates="user", cascade="all, delete-orphan"
    )
    profile = relationship(
        "Profile", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    roles = relationship("Role", secondary=user_roles, back_populates="users")
    orders = relationship("Order", back_populates="user")

    def __repr__(self):
        return f"<User {self.id}>"


class Post(db.Model):
    id = Column(Integer, primary_key=True)
    author_id = Column(Integer, ForeignKey("user.id"))
    category_id = Column(Integer, ForeignKey("category.id"))

    title = Column(String(128), nullable=False)
    body = Column(Text)

    created_at = Column(DateTime, default=func.now())

    author = relationship("User", back_populates="posts")
    category = relationship("Category", back_populates="posts")
    tags = relationship("Tag", secondary=posts_tags, back_populates="posts")
    comments = relationship(
        "Comment", back_populates="post", cascade="all, delete-orphan"
    )
    attachments = relationship(
        "Attachment", back_populates="post", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Post {self.id}>"


# ----- Extra Models -----


class Role(db.Model):
    id = Column(Integer, primary_key=True)
    name = Column(String(32), unique=True, nullable=False)

    users = relationship("User", secondary=user_roles, back_populates="roles")

    def __repr__(self):
        return f"<Role {self.name}>"


class Address(db.Model):
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id"))
    street = Column(String(128))
    city = Column(String(64))
    state = Column(String(32))
    postal_code = Column(String(20))
    country = Column(String(64))
    is_primary = Column(Boolean, default=False)

    user = relationship("User", back_populates="addresses")

    def __repr__(self):
        return f"<Address {self.id}>"


class Profile(db.Model):
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id"), unique=True)
    bio = Column(Text)
    avatar = Column(LargeBinary)

    user = relationship("User", back_populates="profile")

    def __repr__(self):
        return f"<Profile {self.id}>"


class Category(db.Model):
    id = Column(Integer, primary_key=True)
    name = Column(String(64), unique=True, nullable=False)
    description = Column(Text)

    posts = relationship("Post", back_populates="category")

    def __repr__(self):
        return f"<Category {self.name}>"


class Tag(db.Model):
    id = Column(Integer, primary_key=True)
    name = Column(String(64), unique=True, nullable=False)

    posts = relationship("Post", secondary=posts_tags, back_populates="tags")

    def __repr__(self):
        return f"<Tag {self.name}>"


class Comment(db.Model):
    id = Column(Integer, primary_key=True)
    post_id = Column(Integer, ForeignKey("post.id"))
    user_id = Column(Integer, ForeignKey("user.id"))
    body = Column(Text)
    created_at = Column(DateTime, default=func.now())

    post = relationship("Post", back_populates="comments")
    user = relationship("User")

    def __repr__(self):
        return f"<Comment {self.id}>"


class Attachment(db.Model):
    id = Column(Integer, primary_key=True)
    post_id = Column(Integer, ForeignKey("post.id"))
    filename = Column(String(128))
    data = Column(LargeBinary)
    mimetype = Column(String(32))

    post = relationship("Post", back_populates="attachments")

    def __repr__(self):
        return f"<Attachment {self.id}>"


class Product(db.Model):
    id = Column(Integer, primary_key=True)
    name = Column(String(64), nullable=False)
    description = Column(Text)
    price = Column(Numeric(10, 2), nullable=False)
    stock = Column(Integer, default=0)
    data = Column(JSON)

    def __repr__(self):
        return f"<Product {self.name}>"


class Order(db.Model):
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id"))
    status = Column(Enum(OrderStatus), default=OrderStatus.pending)
    total_price = Column(Numeric(10, 2), default=0)
    created_at = Column(DateTime, default=func.now())

    user = relationship("User", back_populates="orders")
    items = relationship(
        "OrderItem", back_populates="order", cascade="all, delete-orphan"
    )
    payments = relationship(
        "Payment", back_populates="order", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Order {self.id}>"


class OrderItem(db.Model):
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("order.id"))
    product_id = Column(Integer, ForeignKey("product.id"))
    quantity = Column(Integer, default=1)
    price = Column(Numeric(10, 2), nullable=False)

    order = relationship("Order", back_populates="items")
    product = relationship("Product")

    def __repr__(self):
        return f"<OrderItem {self.id}>"


class Payment(db.Model):
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("order.id"))
    amount = Column(Numeric(10, 2), nullable=False)
    paid_at = Column(DateTime, default=func.now())
    method = Column(Enum(PaymentMethod))

    order = relationship("Order", back_populates="payments")

    def __repr__(self):
        return f"<Payment {self.id}>"


# ---------------- New models for more extensive
# type & relationship coverage ----------------
class Department(db.Model):
    id = Column(Integer, primary_key=True)
    name = Column(String(64), unique=True, nullable=False)
    budget = Column(Numeric(12, 2), default=0)
    created_at = Column(DateTime, default=func.now())

    employees = relationship("Employee", back_populates="department")

    def __repr__(self):
        return f"<Department {self.name}>"


class Project(db.Model):
    id = Column(Integer, primary_key=True)
    name = Column(String(128), unique=True, nullable=False)
    deadline = Column(Date)
    description = Column(Text)
    budget = Column(Numeric(12, 2))

    employees = relationship(
        "Employee", secondary=employees_projects, back_populates="projects"
    )

    def __repr__(self):
        return f"<Project {self.name}>"


class Employee(db.Model):
    id = Column(Integer, primary_key=True)
    department_id = Column(Integer, ForeignKey("department.id"))
    first_name = Column(String(64), nullable=False)
    last_name = Column(String(64), nullable=False)
    salary = Column(Numeric(10, 2))
    hire_date = Column(Date)
    shift_start = Column(Time)
    is_full_time = Column(Boolean, default=True)
    rating = Column(Float)

    department = relationship("Department", back_populates="employees")
    projects = relationship(
        "Project", secondary=employees_projects, back_populates="employees"
    )

    def __repr__(self):
        return f"<Employee {self.first_name} {self.last_name}>"


def db_init(app: Flask):
    with app.app_context():
        db.init_app(app)
        db.create_all()
