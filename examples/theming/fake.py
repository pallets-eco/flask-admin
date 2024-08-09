from faker import Faker
from models import User, Post, db
from random import choice, randint as rand

fake = Faker()


def generate_fake_data(app):
    with app.app_context():
        # get the count of users, if less than 10, then genereate fake users
        user_count = User.query.count()
        if user_count < 10:
            for i in range(10 - user_count):
                user = User(
                    email=fake.email(),
                    name=fake.name(),
                    age=rand(18, 45),
                    active=choice([True, False]),
                )   # type: ignore
                db.session.add(user)
            db.session.commit()

        # get list of user ids
        user_ids = [user.id for user in User.query.all()]
        # get the count of posts, if less than 30, then generate fake posts
        post_count = Post.query.count()
        if post_count < 30:
            for i in range(30 - post_count):
                post = Post(
                    author_id=choice(user_ids),
                    title=fake.sentence(),
                    body=fake.text(max_nb_chars=500)
                )   # type: ignore
                db.session.add(post)
            db.session.commit()
