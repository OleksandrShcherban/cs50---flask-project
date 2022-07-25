import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
uri = os.getenv("DATABASE_URL")
if uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://")
db = SQL(uri)

# Make sure API key is set
# if not os.environ.get("API_KEY"):
#     raise RuntimeError("API_KEY not set")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    cash = db.execute("SELECT cash FROM users WHERE id = (?)",
                      session["user_id"])[0]['cash']
    portfolio = db.execute(
        "SELECT symbol, price, SUM(shares) AS sum FROM operations WHERE user_id = (?) GROUP BY symbol, price", session["user_id"])
    names = {}
    for record in portfolio:
        names[record['symbol']] = lookup(record['symbol'])['name']
    return render_template("portfolio.html", portfolio=portfolio, cash=cash, names=names)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "POST":
        symbol = request.form.get("symbol")
        if symbol == "":
            return apology("Ticker symbol is empty")
        symbol = lookup(symbol)
        if symbol == None:
            return apology("No such symbol exists")
        if request.form.get("shares").isdigit() != True or request.form.get("shares") == "0":
            return apology("Shares must be positive non-fractured value")
        shares = int(request.form.get("shares"))
        price = symbol['price']
        symbol = symbol['symbol']
        cash = db.execute("SELECT cash FROM users WHERE id = (?)",
                          session["user_id"])[0]['cash']
        if shares * price > cash:
            return apology("You have no enough cash")
        db.execute("INSERT INTO operations (symbol, shares, price, user_id) VALUES (?, ?, ?, ?)",
                   symbol, shares, price, session["user_id"])
        cash -= shares * price
        db.execute("UPDATE users SET cash = (?) WHERE id = (?)",
                   cash, session["user_id"])
        flash('You bought ' + str(shares) + ' shares of ' + symbol)
        return redirect("/")

    else:
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    history = db.execute(
        "SELECT symbol, shares, price, datetime FROM operations WHERE user_id = (?)", session["user_id"])
    return render_template("history.html", history=history)


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
        rows = db.execute("SELECT * FROM users WHERE username = ?",
                          request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        flash('Hello, ' + request.form.get("username"))
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
    flash('Hope to see you back soon')
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    if request.method == "POST":
        symbol = request.form.get("symbol")
        if symbol == "":
            return apology("Ticker symbol is empty")
        symbol = lookup(symbol)
        if symbol == None:
            return apology("No such symbol exists")
        return render_template("quoted.html", symbol=symbol)

    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        if username == "":
            return apology("Username field is empty")
        username_check = db.execute(
            "SELECT username FROM users WHERE username = (?) LIMIT 1", username)
        if len(username_check) > 0:
            return apology("Username already exist")
        if password == "":
            return apology("Password field is empty")
        if password != confirmation:
            return apology("Password confirmation doesn't match")
        hash = generate_password_hash(password)
        session["user_id"] = db.execute(
            "INSERT INTO users (username, hash) VALUES (?, ?)", username, hash)
        flash(username + ', your registration completed')
        return redirect("/")

    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    if request.method == "POST":
        symbol = request.form.get("symbol")
        if symbol == "":
            return apology("Ticker symbol is empty")
        symbol = lookup(symbol)
        if symbol == None:
            return apology("No such symbol exists")
        if request.form.get("shares").isdigit() != True or request.form.get("shares") == "0":
            return apology("Shares must be positive non-fractured value")
        shares = int(request.form.get("shares"))
        price = symbol['price']
        symbol = symbol['symbol']
        cash = db.execute("SELECT cash FROM users WHERE id = (?)",
                          session["user_id"])[0]['cash']
        available = db.execute("SELECT SUM(shares) AS sum FROM operations WHERE user_id = (?) AND symbol = (?)",
                               session["user_id"], symbol)[0]['sum']
        if shares > available:
            return apology("You have no enough shares")
        db.execute("INSERT INTO operations (symbol, shares, price, user_id) VALUES (?, ?, ?, ?)",
                   symbol, -shares, price, session["user_id"])
        cash += shares * price
        db.execute("UPDATE users SET cash = (?) WHERE id = (?)",
                   cash, session["user_id"])
        flash('You sold ' + str(shares) + ' shares of ' + symbol)
        return redirect("/")

    else:
        symbols = db.execute(
            "SELECT DISTINCT symbol FROM operations WHERE user_id = (?)", session["user_id"])
        return render_template("sell.html", symbols=symbols)


@app.route("/change", methods=["GET", "POST"])
def change():
    """Change password"""
    if request.method == "POST":

        username = request.form.get("username")
        old = request.form.get("old")
        new = request.form.get("new")
        confirmation = request.form.get("confirmation")
        if username == "":
            return apology("Username field is empty")
        username_check = db.execute(
            "SELECT username FROM users WHERE id = (?)", session["user_id"])
        if username != username_check[0]['username']:
            return apology("You may change password only for user currently logged in")
        password_check = db.execute(
            "SELECT hash FROM users WHERE id = (?)", session["user_id"])
        if not check_password_hash(password_check[0]['hash'], old):
            return apology("Wrong old password")
        if new == "":
            return apology("New password field is empty")
        if new == old:
            return apology("New and old passwords are the same")
        if new != confirmation:
            return apology("Password confirmation doesn't match")
        hash = generate_password_hash(new)
        db.execute("UPDATE users SET hash = (?) WHERE id = (?)",
                   hash, session["user_id"])
        flash(username + ', your password changed')
        return redirect("/")

    else:
        return render_template("change.html")


@app.route("/q", methods=["POST"])
@login_required
def q():
    """Check stock quote."""
    if request.method == "POST":
        symbol = request.get_data()
        symbol = lookup(symbol)
        if symbol != None:
            return "<h1>" + symbol["symbol"] + ' => ' + symbol["name"] + "</h1><br>"
        else:
            return "No such symbol"
