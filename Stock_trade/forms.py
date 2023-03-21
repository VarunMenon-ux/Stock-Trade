from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, DecimalField, IntegerField, DateField, SelectField, TimeField
from wtforms.validators import InputRequired, Email, Length, EqualTo, NumberRange, Optional


class RegisterForm(FlaskForm):
    name = StringField('Full Name', validators=[InputRequired(), Length(min=3, max=50)])
    username = StringField('Username', validators=[InputRequired(), Length(min=3, max=20)])
    email = StringField('Email', validators=[InputRequired(), Email(message='Invalid email'), Length(max=50)])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=6, max=20)])
    confirm_password = PasswordField('Confirm Password', validators=[InputRequired(), EqualTo('password')])


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired(), Length(min=3, max=20)])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=6, max=20)])
    remember_me = BooleanField('Remember Me')


class CreateStockForm(FlaskForm):
    name = StringField('Company Name', validators=[InputRequired(), Length(min=3, max=100)])
    ticker = StringField('Stock Ticker', validators=[InputRequired(), Length(min=1, max=10)])
    volume = IntegerField('Volume', validators=[InputRequired(), NumberRange(min=1)])
    price = DecimalField('Initial Price', validators=[InputRequired(), NumberRange(min=0)])


class BuyStockForm(FlaskForm):
    volume = IntegerField('Volume', validators=[InputRequired(), NumberRange(min=1)])
    limit_price = DecimalField('Limit Order Price', validators=[Optional(), NumberRange(min=0)])
    expiration_date = DateField('Expiration Date', format='%Y-%m-%d', validators=[Optional()])
    order_type = SelectField('Order Type', choices=[('market', 'Market'), ('limit', 'Limit')], validators=[InputRequired()])


class SellStockForm(FlaskForm):
    volume = IntegerField('Volume', validators=[InputRequired(), NumberRange(min=1)])
    limit_price = DecimalField('Limit Order Price', validators=[Optional(), NumberRange(min=0)])
    expiration_date = DateField('Expiration Date', format='%Y-%m-%d', validators=[Optional()])
    order_type = SelectField('Order Type', choices=[('market', 'Market'), ('limit', 'Limit')], validators=[InputRequired()])


class SetMarketHoursForm(FlaskForm):
    open_time = TimeField('Opening Time', format='%H:%M', validators=[InputRequired()])
    close_time = TimeField('Closing Time', format='%H:%M', validators=[InputRequired()])


class SetMarketScheduleForm(FlaskForm):
    day = SelectField('Day of the Week', choices=[('', 'Choose a day'), ('Monday', 'Monday'), ('Tuesday', 'Tuesday'), ('Wednesday', 'Wednesday'), ('Thursday', 'Thursday'), ('Friday', 'Friday'), ('Saturday', 'Saturday'), ('Sunday', 'Sunday')], validators=[InputRequired()])
    start_date = DateField('Start Date', format='%Y-%m-%d', validators=[InputRequired()])
    end_date = DateField('End Date', format='%Y-%m-%d', validators=[InputRequired()])


class DepositForm(FlaskForm):
    amount = DecimalField('Amount', validators=[InputRequired(), NumberRange(min=0)])


class WithdrawForm(FlaskForm):
    amount = DecimalField('Amount', validators=[InputRequired(), NumberRange(min=0)])
