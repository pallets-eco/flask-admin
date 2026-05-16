import datetime
import random

from sqlmodel import Session
from sqlmodel import SQLModel
from sqlmodel import select

from admin import engine
from admin.models import AVAILABLE_USER_TYPES
from admin.models import Post
from admin.models import Tag
from admin.models import Tree
from admin.models import User


def build_sample_db() -> None:
    """Populate a small db with some example entries."""

    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        if session.exec(select(User)).first() is not None:
            return

    first_names = [
        "Harry",
        "Amelia",
        "Oliver",
        "Jack",
        "Isabella",
        "Charlie",
        "Sophie",
        "Mia",
        "Jacob",
        "Thomas",
        "Emily",
        "Lily",
        "Ava",
        "Isla",
        "Alfie",
        "Olivia",
        "Jessica",
        "Riley",
        "William",
        "James",
        "Geoffrey",
        "Lisa",
        "Benjamin",
        "Stacey",
        "Lucy",
    ]
    last_names = [
        "Brown",
        "Brown",
        "Patel",
        "Jones",
        "Williams",
        "Johnson",
        "Taylor",
        "Thomas",
        "Roberts",
        "Khan",
        "Clarke",
        "Clarke",
        "Clarke",
        "James",
        "Phillips",
        "Wilson",
        "Ali",
        "Mason",
        "Mitchell",
        "Rose",
        "Davis",
        "Davies",
        "Rodriguez",
        "Cox",
        "Alexander",
    ]
    countries = [
        ("ZA", "South Africa", 27, "ZAR", "Africa/Johannesburg"),
        ("BF", "Burkina Faso", 226, "XOF", "Africa/Ouagadougou"),
        ("US", "United States of America", 1, "USD", "America/New_York"),
        ("BR", "Brazil", 55, "BRL", "America/Sao_Paulo"),
        ("TZ", "Tanzania", 255, "TZS", "Africa/Dar_es_Salaam"),
        ("DE", "Germany", 49, "EUR", "Europe/Berlin"),
        ("CN", "China", 86, "CNY", "Asia/Shanghai"),
    ]

    sample_text = [
        {
            "title": "de Finibus Bonorum et Malorum - Part I",
            "content": (
                "Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do "
                "eiusmod tempor incididunt ut labore et dolore magna aliqua."
            ),
        },
        {
            "title": "de Finibus Bonorum et Malorum - Part II",
            "content": (
                "Sed ut perspiciatis unde omnis iste natus error sit voluptatem "
                "accusantium doloremque laudantium, totam rem aperiam."
            ),
        },
        {
            "title": "de Finibus Bonorum et Malorum - Part III",
            "content": (
                "At vero eos et accusamus et iusto odio dignissimos ducimus qui "
                "blanditiis praesentium voluptatum deleniti atque corrupti quos dolores."
            ),
        },
    ]

    with Session(engine) as session:
        users: list[User] = []
        for first_name, last_name in zip(first_names, last_names):
            country = random.choice(countries)
            user = User(
                type=random.choice(AVAILABLE_USER_TYPES)[0],
                first_name=first_name,
                last_name=last_name,
                email=f"{first_name.lower()}@example.com",
                website="https://www.example.com",
                ip_address="127.0.0.1",
                currency=country[3],
                timezone=country[4],
                dialling_code=country[2],
                local_phone_number="0" + "".join(random.choices("123456789", k=9)),
            )
            users.append(user)
            session.add(user)

        tags: list[Tag] = []
        for tag_name in [
            "YELLOW",
            "WHITE",
            "BLUE",
            "GREEN",
            "RED",
            "BLACK",
            "BROWN",
            "PURPLE",
            "ORANGE",
        ]:
            tag = Tag(name=tag_name)
            tags.append(tag)
            session.add(tag)

        session.flush()

        for user in users:
            entry = random.choice(sample_text)
            post = Post(
                user_id=user.id,
                title=f"{user.first_name}'s opinion on {entry['title']}",
                text=entry["content"],
                background_color=random.choice(["#cccccc", "red", "lightblue", "#0f0"]),
                date=(
                    datetime.date.today()
                    - datetime.timedelta(days=int(1000 * random.random()))
                ),
            )
            post.tags = random.sample(tags, 2)
            session.add(post)

        trunk = Tree(name="Trunk")
        session.add(trunk)
        session.flush()

        for i in range(5):
            branch = Tree(name=f"Branch {i + 1}", parent_id=trunk.id)
            session.add(branch)
            session.flush()
            for j in range(5):
                leaf = Tree(name=f"Leaf {j + 1}", parent_id=branch.id)
                session.add(leaf)

        session.commit()
