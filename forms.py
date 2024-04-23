from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
from flask_wtf.file import FileAllowed
from wtforms import StringField, PasswordField, SubmitField, IntegerField
from wtforms.validators import DataRequired, EqualTo, ValidationError, Regexp
from models import User
from helpers import images
# This file check method was based on https://stackoverflow.com/a/67172432/11690953


def FileSizeLimit(max_size_in_mb):
    max_bytes = max_size_in_mb*1024*1024  # Convert MB to bytes

    def file_length_check(form, field):
        if field.data is None:
            return
        if len(field.data.read()) > max_bytes:
            raise ValidationError(
                f"File size must be less than {max_size_in_mb}MB")
        field.data.seek(0)
    return file_length_check


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


class RecipeForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    ingredients = StringField('Ingredients', validators=[DataRequired()])
    instructions = StringField('Instructions', validators=[DataRequired()])
    submit = SubmitField('Submit')


class PantryForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    quantity = IntegerField('Quantity', validators=[DataRequired()])
    submit = SubmitField('Submit')


class SearchForm(FlaskForm):
    ingredients = StringField('Ingredients', validators=[DataRequired()])
    submit = SubmitField('Search')


class SettingsForm(FlaskForm):
    avatar = FileField('Upload Avatar', validators=[
                       FileRequired(), FileSizeLimit(max_size_in_mb=2), FileAllowed(images, 'Image files only!')], default=None)
    submit = SubmitField('Save')
