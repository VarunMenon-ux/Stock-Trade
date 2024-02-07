from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    name = db.Column(db.String(120))
    password_hash = db.Column(db.String(128))
    cash_balance = db.Column(db.Float, default=10000.0)
    stocks = db.relationship('UserStock', backref='user', lazy='dynamic')
    limit_orders = db.relationship('LimitOrder', backref='user', lazy='dynamic')
    trades = db.relationship('Trade', backref='user', lazy='dynamic')
    is_admin = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Stock(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    volume = db.Column(db.Integer)
    price = db.Column(db.Float)
    prev_price = db.Column(db.Float, default=0.0)
    users = db.relationship('UserStock', backref='stock', lazy='dynamic')
    limit_orders = db.relationship('LimitOrder', backref='stock', lazy='dynamic')
    trades = db.relationship('Trade', backref='stock', lazy='dynamic')
    high = db.Column(db.Float, default=0.0)
    low = db.Column(db.Float, default=0.0)


class UserStock(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    stock_id = db.Column(db.Integer, db.ForeignKey('stock.id'))
    volume = db.Column(db.Integer)
    purchase_price = db.Column(db.Float)


class LimitOrder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    stock_id = db.Column(db.Integer, db.ForeignKey('stock.id'))
    volume = db.Column(db.Integer)
    limit_price = db.Column(db.Float)
    expiration_date = db.Column(db.DateTime)
    order_type = db.Column(db.String(10))


class Trade(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    stock_id = db.Column(db.Integer, db.ForeignKey('stock.id'))
    volume = db.Column(db.Integer)
    trade_price = db.Column(db.Float)
    trade_date = db.Column(db.DateTime)
    trade_type = db.Column(db.String(10)) # 'buy' or 'sell'
    total_value = db.Column(db.Float)


class MarketHours(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    open_time = db.Column(db.Time)
    close_time = db.Column(db.Time)

class MarketSchedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    days_open = db.Column(db.String(100)) # Comma-separated days when the market is open

