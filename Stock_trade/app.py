from flask import Flask, render_template, redirect, request, url_for, session, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask import current_app
from flask_migrate import Migrate
from datetime import datetime
from forms import RegisterForm, LoginForm, CreateStockForm, BuyStockForm, SellStockForm, SetMarketHoursForm, SetMarketScheduleForm, DepositForm, WithdrawForm
from models import db, User, Stock, Trade, UserStock, LimitOrder, MarketHours, MarketSchedule
from sqlalchemy import func, or_
import random
import atexit
from apscheduler.schedulers.background import BackgroundScheduler

# Initialize the app and set some configuration values
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
app.config['SECRET_KEY'] = 'secret key'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database and login manager
db.init_app(app)
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)
migrate = Migrate(app, db)


admin_username = 'admin'
admin_password = 'password'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.template_filter()
def datetimeformat(value, format='%Y-%m-%d %H:%M:%S'):
    if value is None:
        return ''
    return value.strftime(format)


def is_market_open():
    current_time = datetime.now().time()
    current_day = datetime.now().strftime('%A')
    market_hours = MarketHours.query.first()
    market_schedule = MarketSchedule.query.filter(MarketSchedule.start_date <= datetime.now().date(), MarketSchedule.end_date >= datetime.now().date(), MarketSchedule.days_open.contains(current_day)).first()

    if market_hours and market_schedule:
        if market_hours.open_time <= current_time <= market_hours.close_time:
            return True
    return False



def update_stock_prices():
    with app.app_context():
        if not is_market_open():
            return

        stocks = Stock.query.all()
        for stock in stocks:
            stock.price = max(stock.price * random.uniform(0.98, 1.02), 0.01)
        db.session.commit()

scheduler = BackgroundScheduler()
scheduler.add_job(func=update_stock_prices, trigger="interval", seconds=60)
scheduler.start()

atexit.register(lambda: scheduler.shutdown())

@app.route("/")
def index():
    stocks = Stock.query.all()
    is_admin = current_user.is_authenticated and current_user.is_admin
    market_open = is_market_open()

    return render_template('index.html', stocks=stocks, is_admin=is_admin, is_market_open=market_open)



# Define the register route
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()

    if form.validate_on_submit():
        existing_user = User.query.filter_by(username=form.username.data).first()
        if existing_user is None:
            user = User(username=form.username.data, email=form.email.data, name=form.name.data)
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            flash('Your account has been created, please log in.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Username already exists, please use a different one.', 'danger')
    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        if form.username.data == admin_username and form.password.data == admin_password:
            admin_user = User.query.filter_by(username=admin_username).first()
            login_user(admin_user, remember=form.remember_me.data)
            return redirect(url_for('index'))

        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        return redirect(url_for('index'))
    return render_template('login.html', title='Sign In', form=form)



# Define the logout route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


# Define the create stock route
@app.route("/create_stock", methods=['GET', 'POST'])
@login_required
def create_stock():
    if not current_user.is_admin:
        flash('You must be an administrator to access this page.', 'danger')
        return redirect(url_for('index'))

    form = CreateStockForm()

    if form.validate_on_submit():
        existing_stock = Stock.query.filter_by(ticker=form.ticker.data).first()
        if existing_stock is None:
            stock = Stock(ticker=form.ticker.data, name=form.name.data, volume=form.volume.data, price=form.price.data)
            db.session.add(stock)
            db.session.commit()
            flash(f'Stock {form.name.data} ({form.ticker.data}) created successfully.', 'success')
            return redirect(url_for('index'))
        else:
            flash(f'Stock with ticker {form.ticker.data} already exists.', 'warning')

    return render_template('create_stock.html', title='Create Stock', form=form)


# Define the buy_stock route
@app.route("/buy_stock/<int:stock_id>", methods=['GET', 'POST'])
@login_required
def buy_stock(stock_id):
    stock = Stock.query.get_or_404(stock_id)
    form = BuyStockForm()

    if form.validate_on_submit():
        if not is_market_open():
            flash('The market is currently closed. Trading is allowed only during market hours.', 'danger')
            return redirect(url_for('index'))

        if form.order_type.data == 'market':
            # Buy at market price
            if current_user.cash_balance < (form.volume.data * stock.price):
                flash('Insufficient funds to buy this stock.', 'danger')
            else:
                current_user.cash_balance -= form.volume.data * stock.price
                current_user.stocks.append(UserStock(stock=stock, volume=form.volume.data, purchase_price=stock.price))  
                db.session.commit()

                # Create a Trade object
                trade = Trade(user_id=current_user.id, stock_id=stock.id, trade_type='buy', volume=form.volume.data, trade_price=stock.price, total_value=form.volume.data * stock.price, trade_date=datetime.utcnow())
                db.session.add(trade)
                db.session.commit()

                flash(f'{form.volume.data} shares of {stock.name} purchased successfully at market price.', 'success')
                return redirect(url_for('index'))

        elif form.order_type.data == 'limit':
            # Buy with limit order
            if current_user.cash_balance < (form.volume.data * form.limit_price.data):
                flash('Insufficient funds to place this limit order.', 'danger')
            else:
                expiration_date = datetime.strptime(str(form.expiration_date.data), '%Y-%m-%d %H:%M:%S')

                limit_order = LimitOrder(stock=stock, volume=form.volume.data, limit_price=form.limit_price.data, expiration_date=expiration_date, user_id=current_user.id, order_type='buy')  # CHANGE: add user_id and order_type
                db.session.add(limit_order)
                db.session.commit()
                flash(f'{form.volume.data} shares of {stock.name} added to limit order at {form.limit_price.data} per share. Order expires on {expiration_date}.', 'success')
                return redirect(url_for('index'))

    return render_template('buy_stock.html', title='Buy Stock', form=form, stock=stock)





from datetime import datetime
# ... other imports

# ...

@app.route("/sell_stock/<int:stock_id>", methods=['GET', 'POST'])
@login_required
def sell_stock(stock_id):
    stock = Stock.query.get_or_404(stock_id)
    user_stock = UserStock.query.filter_by(user=current_user, stock=stock).first()
    form = SellStockForm()

    if form.validate_on_submit():
        if not is_market_open():
            flash('The market is currently closed. Trading is allowed only during market hours.', 'danger')
            return redirect(url_for('index'))

        if form.volume.data > user_stock.volume:
            flash('You do not own enough shares of this stock to sell.', 'danger')
            return redirect(url_for('sell_stock', stock_id=stock_id))

        if form.limit_price.data:
            limit_price = form.limit_price.data
            expiration_date = form.expiration_date.data

            limit_order = LimitOrder(user=current_user, stock=stock, volume=form.volume.data, limit_price=limit_price, expiration_date=expiration_date)
            db.session.add(limit_order)
            db.session.commit()
            flash(f'{form.volume.data} shares of {stock.name} placed for sale at limit price {limit_price} with expiration date {expiration_date}.', 'success')
            return redirect(url_for('index'))
        else:
            current_user.cash_balance += form.volume.data * stock.price
            user_stock.volume -= form.volume.data
            if user_stock.volume == 0:
                db.session.delete(user_stock)
            db.session.commit()

            # Create a transaction record for selling stocks
            transaction = Trade(user_id=current_user.id, stock_id=stock.id, trade_type='sell', volume=form.volume.data, trade_price=stock.price, total_value=form.volume.data * stock.price, trade_date=datetime.utcnow())
            db.session.add(transaction)
            db.session.commit()

            flash(f'{form.volume.data} shares of {stock.name} ({stock.ticker}) sold successfully at market price.', 'success')
            return redirect(url_for('index'))

    return render_template('sell_stock.html', title='Sell Stock', form=form, stock=stock, user_stock=user_stock)





@app.route('/deposit', methods=['GET', 'POST'])
@login_required
def deposit():
    form = DepositForm()
    if form.validate_on_submit():
        current_user.cash_balance += float(form.amount.data)
        deposit_trade = Trade(user_id=current_user.id, trade_type='deposit', total_value=form.amount.data, trade_date=datetime.utcnow())
        db.session.add(deposit_trade)
        
        db.session.commit()
        flash('Deposit successful.', 'success')
        return redirect(url_for('index'))
    return render_template('deposit.html', title='Deposit', form=form)

@app.route('/withdraw', methods=['GET', 'POST'])
@login_required
def withdraw():
    form = WithdrawForm()
    if form.validate_on_submit():
        if current_user.cash_balance < form.amount.data:
            flash('Insufficient funds to make this withdrawal.', 'danger')
        else:
            current_user.cash_balance -= float(form.amount.data) 
            withdraw_trade = Trade(user_id=current_user.id, trade_type='withdrawal', total_value=form.amount.data, trade_date=datetime.utcnow())
            db.session.add(withdraw_trade)
            
            db.session.commit()
            flash(f'Successfully withdrew ${form.amount.data:.2f} from your account.', 'success')
            return redirect(url_for('index'))

    return render_template('withdraw.html', form=form)




@app.route('/portfolio')
@login_required
def portfolio():
    stocks = current_user.stocks.all()
    total_invested = 0
    portfolio_data = {}

    for stock in stocks:
        total_invested += stock.volume * stock.purchase_price
        portfolio_data[stock.stock_id] = stock.volume

    return render_template('portfolio.html', portfolio=portfolio_data, stocks=stocks, cash=current_user.cash_balance, total_invested=total_invested)




@app.route('/transactions')
@login_required
def transactions():
    user_stocks = UserStock.query.filter_by(user_id=current_user.id).all()
    trades = Trade.query.filter_by(user_id=current_user.id).all()
    return render_template('transactions.html', user_stocks=user_stocks, trades=trades)


@app.route('/set_market_hours', methods=['GET', 'POST'])
@login_required
def set_market_hours():
    if not current_user.is_admin:
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('index'))

    form = SetMarketHoursForm()
    if form.validate_on_submit():
        market_schedule = MarketHours.query.first()
        if market_schedule is None:
            market_schedule = MarketHours()

        market_schedule.open_time = form.open_time.data
        market_schedule.close_time = form.close_time.data
        db.session.add(market_schedule)
        db.session.commit()
        flash('Market hours have been updated.', 'success')
        return redirect(url_for('index'))

    return render_template('set_market_hours.html', form=form)

    

@app.route('/set_market_schedule', methods=['GET', 'POST'])
@login_required
def set_market_schedule():
    if not current_user.is_admin:
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('index'))

    form = SetMarketScheduleForm()
    if form.validate_on_submit():
        market_schedule = MarketSchedule.query.filter_by(days_open=form.day.data).first()
        if not market_schedule:
            market_schedule = MarketSchedule(days_open=form.day.data)
            db.session.add(market_schedule)
        market_schedule.start_date = form.start_date.data
        market_schedule.end_date = form.end_date.data
        db.session.commit()
        flash('Market schedule has been updated.', 'success')
        return redirect(url_for('index'))
    return render_template('set_market_schedule.html', form=form)


# Define the cancel order route
@app.route("/cancel_order/<int:trade_id>")
@login_required
def cancel_order(trade_id):
    trade = Trade.query.get_or_404(trade_id)
    user_stock = UserStock.query.filter_by(user=current_user, stock=trade.stock).first()

    if trade.user_id != current_user.id:
        flash('You cannot cancel an order that does not belong to you.', 'danger')
    elif trade.executed:
        flash('You cannot cancel an order that has already been executed.', 'danger')
    else:
        db.session.delete(trade)
        if trade.order_type == 'buy':
            user_stock.volume -= trade.volume
            current_user.cash_balance += trade.volume * trade.price
        else:
            user_stock.volume += trade.volume
        db.session.commit()
        flash('Order cancelled successfully.', 'success')

    return redirect(url_for('portfolio'))


if __name__ == '__main__':
    manager.run()
