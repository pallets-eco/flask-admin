from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime, Boolean, func
from sqlalchemy.orm import relationship
from flask_sqlalchemy import SQLAlchemy
from flask import Flask

db = SQLAlchemy()


class User(db.Model):
    id = Column(Integer, primary_key=True)
    email = Column(String(120), unique=True)
    name = Column(String(64), nullable=False)
    age = Column(Integer, nullable=False)
    active = Column(Boolean, default=False)

    created_at = Column(DateTime, default=func.now())

    posts = relationship('Post', back_populates='author')
    
    def __repr__(self):
        return f'<User {self.id}>'



class Post(db.Model):
    id = Column(Integer, primary_key=True)
    author_id = Column(Integer, ForeignKey('user.id'))
    title = Column(String(64), nullable=False)
    body = Column(Text)

    created_at = Column(DateTime, default=func.now())

    author = relationship('User', back_populates='posts')
    
    def __repr__(self):
        return f'<Post {self.id}>'



def db_init(app : Flask):
    with app.app_context():
        db.init_app(app)
        db.create_all()

