from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, EqualTo, ValidationError, Regexp
from models import User


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Regexp(
        '^[a-z]{6,8}$', message='Your username should be between 6 and 8 characters long, and can only contain lowercase letters.')])
    password = PasswordField('Password', validators=[
        DataRequired(),
        EqualTo('confirm_password', message='Passwords do not match. Try again'),
        Regexp(
            '.{6,}$', message='Your password needs to be at least 6 characters long.'),
        Regexp(
            '(?=.*[a-z])', message='Your password needs to contain at least one lowercase letter.'),
        Regexp(
            '(?=.*[A-Z])', message='Your password needs to contain at least one uppercase letter.'),
        Regexp(
            '(?=.*[0-9])', message='Your password needs to contain at least one number.'),
        Regexp('(?=.*[!@#\$%\^&\*])',
               message='Your password needs to contain at least one special character.')
    ])
    confirm_password = PasswordField(
        'Confirm Password', validators=[DataRequired()])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError(
                'Username already exist. Please choose a different one.')


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

    def verify_credential(self, username, password):
        user = User.query.filter_by(username=username.data).first()
        if not (user is not None and user.verify_password(password)):
            raise ValidationError(
                'Invalid username or password. Please try again.')


class RecipeForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    ingredients = StringField('Ingredients', validators=[DataRequired()])
    instructions = StringField('Instructions', validators=[DataRequired()])
    submit = SubmitField('Submit')


class SearchForm(FlaskForm):
    ingredients = StringField('Ingredients', validators=[DataRequired()])
    submit = SubmitField('Search')
