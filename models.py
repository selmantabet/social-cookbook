from app import db, login_manager
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import datetime
import json


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    hashed_password = db.Column(db.String(128), nullable=False)
    settings_json = db.Column(db.String(200), default="{}")
    food_profile = db.Column(db.String(200), default="{}")
    inventory = db.Column(db.String(100000), default="{}")
    recipes = db.relationship(
        'Recipe', backref='user', lazy=True, cascade="all, delete")
    comments = db.relationship(
        'Comment', backref='user', lazy=True, cascade="all, delete")
    votes = db.relationship(
        'Vote', backref='user', lazy=True, cascade="all, delete")
    bookmarks = db.relationship(
        'Bookmark', backref='user', lazy=True, cascade="all, delete")

    @property
    def password(self):
        raise AttributeError('Password is not readable.')

    @password.setter
    def password(self, password):
        self.hashed_password = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.hashed_password, password)


class Recipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    ingredients = db.Column(db.Text, nullable=False)
    instructions = db.Column(db.Text, nullable=False)
    allergies = db.Column(db.String(255), nullable=False)
    cuisines = db.Column(db.String(255), nullable=False)
    taste = db.Column(db.String(255), nullable=False)
    diet = db.Column(db.String(255), nullable=False)
    image_file = db.Column(db.String(40), nullable=False,
                           default='icon.jpeg')
    visibility = db.Column(db.String(40), nullable=False)
    rating = db.Column(db.String(255), nullable=False,
                       default=json.dumps({"upvotes": 0, "downvotes": 0}))
    comments = db.relationship(
        'Comment', backref='recipe', lazy=True, cascade="all, delete")
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    votes = db.relationship(
        'Vote', backref='recipe', lazy=True, cascade="all, delete")
    bookmarks = db.relationship(
        'Bookmark', backref='recipe', lazy=True, cascade="all, delete")


class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=False, default=datetime.now())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recipe_id = db.Column(db.Integer, db.ForeignKey(
        'recipe.id'), nullable=False)
    upvote = db.Column(db.Boolean, nullable=False)


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=False, default=datetime.now())
    content = db.Column(db.Text, nullable=False)
    recipe_id = db.Column(db.Integer, db.ForeignKey(
        'recipe.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


class Bookmark(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recipe_id = db.Column(db.Integer, db.ForeignKey(
        'recipe.id'), nullable=False)
