import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached


@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""

    # Query the information where sum of shares > 0
    portfolio = db.execute(
        "SELECT symbol, SUM(shares) as sum FROM transactions WHERE user_id = :user_id GROUP BY symbol Having sum > 0", user_id=session["user_id"])

    # Get the user's current cash
    rows = db.execute("SELECT cash FROM users WHERE id = :user_id", user_id=session["user_id"])
    available_cash = rows[0]["cash"]
    total_asset = available_cash
    statistics = []

    # Record the information for each symbol
    for i in portfolio:
        quote = lookup(i["symbol"])
        temp = {
            'symbol': quote["symbol"],
            'name': quote["name"],
            'shares': i["sum"],
            'price': usd(quote['price']),
            'total': i["sum"]*quote["price"]
        }
        total_asset += temp['total']
        temp['total'] = usd(temp['total'])
        statistics.append(temp)

    return render_template("index.html", statistics=statistics, available_cash=usd(available_cash), total_asset=usd(total_asset))


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "POST":
        quote = lookup(request.form.get("symbol"))
        if not quote:
            return apology("Invalid stock symbol")

        # Check if shares was a integer
        try:
            shares = int(request.form.get("shares"))
        except:
            return apology("shares must be a integer", 400)

        # Check if # of shares requested positive
        if shares <= 0:
            return apology("can't buy less than or 0 shares", 400)

        # check if  the user's cash is enough
        rows = db.execute("SELECT cash FROM users WHERE id = :id", id=session["user_id"])
        totalPrice = quote["price"] * shares
        if rows[0]["cash"] < totalPrice:
            return apology("Not enough money")

        # Update the transaction database
        db.execute(
            "INSERT INTO transactions (symbol, company, shares, price, user_id, cost) VALUES(:symbol, :company, :shares, :price, :user_id, :cost)",
            symbol=quote["symbol"], company=quote["name"], shares=shares, price=quote["price"], user_id=session["user_id"], cost=totalPrice)

        # Update the user database
        db.execute("Update users set cash = cash - :totalPrice Where id = :user_id",
                   totalPrice=totalPrice, user_id=session["user_id"])
        flash('Bought!')
        return redirect("/")
    else:
        return render_template("buy.html")


@app.route("/check", methods=["GET"])
def check():
    """Return true if username available, else false, in JSON format"""
    rows = db.execute(
        "SELECT * FROM users WHERE username = :username", username=request.args.get("username"))
    if len(rows) == 0:
        return jsonify(True)
    else:
        return jsonify(False)


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    transactions = db.execute(
        "SELECT symbol, shares, price, timestamp FROM transactions WHERE user_id = :user_id", user_id=session["user_id"])
    return render_template("history.html", transactions=transactions)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = :username", username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""

    # Ensure proper symbol
    if request.method == 'POST':
        stock = lookup(request.form.get("symbol"))
        if not stock:
            return apology("Invalid stock")
        return render_template("quoted.html", stock=stock)
    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == 'POST':

        # Make sure fileds aren't left blank
        if not request.form.get("username") or not request.form.get("password"):
            return apology(" Miss username or password")

        # Make sure password matches
        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("password not match")

        # hash password and insert user information into database (protect against SQL injection attacks)
        passwordHash = generate_password_hash(request.form.get("password"), method='pbkdf2:sha256', salt_length=8)

        # Check if the username already exist
        result = db.execute(
            "Insert Into users (username, hash) VALUES(:username, :hash)", username=request.form.get("username"), hash=passwordHash)
        if not result:
            return apology("Username already exists")

        # Remember the user if he registered succussfully
        session["user_id"] = result
        return redirect("/")
    return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""

    # Check if we have enough shares
    if request.method == 'POST':
        quote = lookup(request.form.get("symbol"))
        shares = int(request.form.get("shares"))
        available_shares = db.execute("SELECT SUM(shares) as total_shares FROM transactions WHERE user_id = :user_id and symbol = :symbol GROUP BY symbol",
                                      user_id=session["user_id"], symbol=quote["symbol"])
        if shares > available_shares[0]["total_shares"]:
            return apology("not enough shares")

        # Update users and transaction tables
        totalPrice = quote["price"]*shares
        db.execute(
            "INSERT INTO transactions (symbol, company, shares, price, user_id, cost) VALUES(:symbol, :company, :shares, :price, :user_id, :cost)",
            symbol=quote["symbol"], company=quote["name"], shares=-shares, price=quote["price"], user_id=session["user_id"], cost=totalPrice)

        db.execute("Update users set cash = cash + :totalPrice Where id = :user_id",
                   totalPrice=totalPrice, user_id=session["user_id"])
        flash("Sold!")
        return redirect("/")
    portfolio = db.execute("SELECT symbol, SUM(shares) as total_shares FROM transactions WHERE user_id = :user_id GROUP BY symbol HAVING total_shares > 0",
                           user_id=session["user_id"])
    return render_template("sell.html", portfolio=portfolio)


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
