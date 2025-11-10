from random import choice
from random import randint

from faker import Faker
from models import Address
from models import Category
from models import Comment
from models import db
from models import Department
from models import Employee
from models import Order
from models import OrderItem
from models import OrderStatus
from models import Payment
from models import PaymentMethod
from models import Post
from models import Product
from models import Profile
from models import Project
from models import Role
from models import Tag
from models import User

fake = Faker()


def generate_fake_data(app):
    """Populate the database with a rich set of example data covering all models."""
    with app.app_context():
        db.create_all()
        db.create_all()
        # ----- Roles -----
        if Role.query.count() == 0:
            for name in ("admin", "editor", "user"):
                db.session.add(Role(name=name))
            db.session.commit()

        roles = Role.query.all()

        # ----- Categories -----
        while Category.query.count() < 5:
            db.session.add(
                Category(name=fake.unique.word(), description=fake.sentence())
            )
        db.session.commit()
        categories = Category.query.all()

        # ----- Tags -----
        while Tag.query.count() < 10:
            db.session.add(Tag(name=fake.unique.word()))
        db.session.commit()
        tags = Tag.query.all()

        # ----- Products -----
        while Product.query.count() < 20:
            db.session.add(
                Product(
                    name=fake.unique.word().title(),
                    description=fake.text(max_nb_chars=200),
                    price=round(
                        fake.pyfloat(
                            left_digits=3,
                            right_digits=2,
                            positive=True,
                            min_value=5,
                            max_value=200,
                        ),
                        2,
                    ),
                    stock=randint(0, 100),
                    data={
                        "color": fake.color_name(),
                        "size": choice(["S", "M", "L", "XL"]),
                    },
                )
            )
        db.session.commit()
        products = Product.query.all()

        # ----- Users -----
        while User.query.count() < 50:
            user = User(
                email=fake.unique.email(),
                name=fake.name(),
                age=randint(18, 65),
                active=choice([True, False]),
                preferences={"newsletter": choice([True, False])},
                balance=round(
                    fake.pyfloat(left_digits=3, right_digits=2, positive=True), 2
                ),
                last_login=fake.date_time_this_year(),
            )
            # assign 1-3 random roles
            user.roles.extend(
                fake.random_elements(elements=roles, length=randint(1, 3), unique=True)
            )
            db.session.add(user)
        db.session.commit()

        users = User.query.all()

        # ----- Addresses & Profiles -----
        for user in users:
            if not user.addresses:
                addr = Address(
                    street=fake.street_address(),
                    city=fake.city(),
                    state=fake.state(),
                    postal_code=fake.postcode(),
                    country=fake.country(),
                    is_primary=True,
                    user_id=user.id,
                )
                db.session.add(addr)
            if not user.profile:
                profile = Profile(bio=fake.sentence(), avatar=None, user_id=user.id)
                db.session.add(profile)
        db.session.commit()

        # ----- Posts -----
        while Post.query.count() < 100:
            author = choice(users)
            post = Post(
                author_id=author.id,
                category=choice(categories),
                title=fake.sentence(),
                body=fake.text(max_nb_chars=800),
            )
            post.tags = fake.random_elements(
                elements=tags, length=randint(1, 4), unique=True
            )
            db.session.add(post)
        db.session.commit()

        posts = Post.query.all()

        # ----- Comments -----
        while Comment.query.count() < 300:
            db.session.add(
                Comment(
                    post_id=choice(posts).id,
                    user_id=choice(users).id,
                    body=fake.sentence(),
                )
            )
        db.session.commit()

        # ----- Orders, Items, Payments -----
        while Order.query.count() < 200:
            user = choice(users)
            order = Order(
                user_id=user.id,
                status=choice(list(OrderStatus)),
                total_price=0,  # will update after adding items
            )
            db.session.add(order)
        db.session.commit()

        orders = Order.query.all()

        for order in orders:
            if not order.items:
                chosen_products = fake.random_elements(
                    elements=products, length=randint(1, 5), unique=True
                )
                total = 0
                for prod in chosen_products:
                    qty = randint(1, 3)
                    total += prod.price * qty
                    db.session.add(
                        OrderItem(
                            order_id=order.id,
                            product_id=prod.id,
                            quantity=qty,
                            price=prod.price,
                        )
                    )
                order.total_price = round(total, 2)
                db.session.add(
                    Payment(
                        order_id=order.id,
                        amount=order.total_price,
                        paid_at=fake.date_time_this_year(),
                        method=choice(list(PaymentMethod)),
                    )
                )
        db.session.commit()

        # ----- Departments -----
        while Department.query.count() < 5:
            db.session.add(
                Department(
                    name=fake.unique.company(),
                    budget=round(
                        fake.pyfloat(
                            left_digits=7,
                            right_digits=2,
                            positive=True,
                            min_value=10000,
                            max_value=1000000,
                        ),
                        2,
                    ),
                )
            )
        db.session.commit()
        departments = Department.query.all()

        # ----- Projects -----
        while Project.query.count() < 10:
            db.session.add(
                Project(
                    name=fake.unique.catch_phrase(),
                    deadline=fake.date_this_year(after_today=True),
                    description=fake.text(max_nb_chars=200),
                    budget=round(
                        fake.pyfloat(
                            left_digits=6,
                            right_digits=2,
                            positive=True,
                            min_value=5000,
                            max_value=500000,
                        ),
                        2,
                    ),
                )
            )
        db.session.commit()
        projects = Project.query.all()

        # ----- Employees -----
        while Employee.query.count() < 100:
            dept = choice(departments)
            emp = Employee(
                department_id=dept.id,
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                salary=round(
                    fake.pyfloat(
                        left_digits=6,
                        right_digits=2,
                        positive=True,
                        min_value=30000,
                        max_value=150000,
                    ),
                    2,
                ),
                hire_date=fake.date_between(start_date="-10y", end_date="today"),
                shift_start=fake.time_object(),
                is_full_time=choice([True, False]),
                rating=round(
                    fake.pyfloat(
                        left_digits=1,
                        right_digits=2,
                        positive=True,
                        min_value=1,
                        max_value=5,
                    ),
                    2,
                ),
            )
            db.session.add(emp)
        db.session.commit()

        employees = Employee.query.all()

        for emp in employees:
            if not emp.projects:
                emp.projects = fake.random_elements(
                    elements=projects, length=randint(1, 4), unique=True
                )
        db.session.commit()
