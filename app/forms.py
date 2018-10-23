from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, \
    TextAreaField, SelectField, IntegerField, DecimalField, RadioField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, \
    Length, Required, NumberRange
from app.models import User
from datetime import datetime, timedelta
from models import Dog, Service

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')


class ResetPasswordRequestForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')


class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Request Password Reset')


class EditProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    address = TextAreaField('Address', validators=[Length(min=0, max=140)])
    submit = SubmitField('Submit')

    def __init__(self, original_username, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=self.username.data).first()
            if user is not None:
                raise ValidationError('Please use a different username.')


class AppointmentForm(FlaskForm):
    date = SelectField('Select Date', validators=[DataRequired()])
    time = SelectField('Select timeslot', validators=[Required()], choices=[('0','09:00-10:30'),
        ('1','10:30-12:00'), ('2','12:00-13:30'),
        ('3','13:30-15:00'), ('4','15:00-16:30')])
    dog = SelectField('Select a dog', validators=[Required()], coerce=int)
    service = SelectField('Select a service', validators=[Required()], coerce=int)
    comment = TextAreaField('Any comment', validators=[Length(min=0, max=140)])
    submit = SubmitField('Submit')

    def __init__(self, datenow, user_id, *args, **kwargs):
        super(AppointmentForm, self).__init__(*args, **kwargs)
        self.datenow = datenow
        self.user_id = user_id
        self.date.choices = [((self.datenow+timedelta(days=i)).strftime("%Y-%m-%d"),self.datenow+timedelta(days=i)) 
        for i in range(8)]
        self.dog.choices = [(dog.id, dog.name) for dog in
        Dog.query.filter_by(user_id=self.user_id).all()]
        self.service.choices = [(s.id, s.name) for s in
        Service.query.filter_by(expired=False).all()]


class CreateDogForm(FlaskForm):
    name = StringField('Dog name', validators=[DataRequired()])
    dog_type = StringField('Dog breed', validators=[DataRequired()])
    age = IntegerField('Age', validators=[NumberRange(min=0, max=30)])
    length = DecimalField('Length', validators=[NumberRange(min=0,max=10)])
    gender = RadioField('Gender', choices=[('Male', 'Male'), ('Female', 'Female')], validators=[DataRequired()])
    comment = TextAreaField('Any comment', validators=[Length(min=0, max=140)])
    submit = SubmitField('Submit')

class EditDogForm(FlaskForm):
    name = StringField('Dog name', validators=[DataRequired()])
    dog_type = StringField('Dog breed', validators=[DataRequired()])
    age = IntegerField('Age', validators=[NumberRange(min=0, max=30)])
    length = DecimalField('Length', validators=[NumberRange(min=0,max=10)])
    gender = RadioField('Gender', choices=[('m', 'Male'), ('f', 'Female')], validators=[DataRequired()])
    comment = TextAreaField('Any comment', validators=[Length(min=0, max=140)])
    submit = SubmitField('Submit')

class EditServiceForm(FlaskForm):
    name = StringField('Service Name', validators=[DataRequired()])
    price = DecimalField('Price', validators=[NumberRange(min=0,max=1000)])
    submit = SubmitField('Submit')

class CreateServiceForm(FlaskForm):
    name = StringField('Service Name', validators=[DataRequired()])
    price = DecimalField('Price', validators=[NumberRange(min=0,max=1000)])
    submit = SubmitField('Submit')

class RescheduleApp(FlaskForm):
    date = SelectField('Select Date', validators=[DataRequired()])
    time = SelectField('Select timeslot', validators=[Required()], choices=[('1','09:00-10:30'),
        ('2','10:30-12:00'), ('3','12:00-13:30'),
        ('4','13:30-15:00'), ('5','15:00-16:30')])
    submit = SubmitField('Submit')

    def __init__(self, datenow, user_id, *args, **kwargs):
        super(RescheduleApp, self).__init__(*args, **kwargs)
        self.datenow = datenow
        self.user_id = user_id
        self.date.choices = [((self.datenow+timedelta(days=i)).strftime("%Y-%m-%d"),self.datenow+timedelta(days=i)) 
        for i in range(8)]



