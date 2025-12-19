from random import choices
from wsgiref.validate import validator
import phonenumbers
from flask_wtf import FlaskForm
from wtforms import (StringField, IntegerField, TextAreaField, EmailField, PasswordField, SelectField, SelectMultipleField, BooleanField, HiddenField, ValidationError, widgets)
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms.validators import InputRequired, DataRequired, EqualTo, Length, Optional, Email, Regexp
from sqlalchemy import desc

from app.models.user import AppUser


class SignUpForm(FlaskForm):
    """Sign up Form"""
    username = StringField(
        'Username', validators=[
            DataRequired(),
            Length(3, 20, message="Please provide a valid name"),
            Regexp(
                "^[A-Za-z][A-Za-z0-9_.]*$",
                0,
                "Usernames must have only letters, " "numbers, dots or underscores",
            )
        ]
    )
    email = EmailField(
        'Email address', validators=[DataRequired(), Email(), Length(1, 64)]
    )
    firstname = StringField(
        'First Name', validators=[
            DataRequired(),
            Length(3, 50, message="Please provide a valid name"),
            Regexp(
                "^[A-Za-z][A-Za-z0-9_.]*$",
                0,
                "Please Make sure you typed your name correctly",
            )
        ]
    )
    lastname = StringField(
        'Last Name', validators=[
            DataRequired(),
            Length(3, 50, message="Please provide a valid name"),
            Regexp(
                "^[A-Za-z][A-Za-z0-9_.]*$",
                0,
                "Please Make sure you typed your name correctly",
            )
        ]
    )
    
    password = PasswordField(
        'Password', validators=[
            DataRequired(),
            Length(4, 72),
            EqualTo('confirmPasswd', message='Passwords Must Match!')
        ]
    )
    confirmPasswd = PasswordField(
        'Confirm Password', validators=[
            DataRequired(),
            Length(4, 72),
            EqualTo('password', message='Passwords Must Match!')
        ]
    )
    
    def validate_email(self, email):
        if AppUser.query.filter_by(email=email.data).first():
            raise ValidationError("Email already registered!")

    def validate_username(self, username):
        if AppUser.query.filter_by(username=username.data).first():
            raise ValidationError("Username already taken!")


class LoginForm(FlaskForm):
    """form for user to login"""
    email_username = StringField(
        'Email or Phone', validators=[DataRequired(), Length(1, 64)]
    )
    pwd = PasswordField(
        'Password', validators=[
            DataRequired(), Length(min=4, max=72)
        ]
    )
