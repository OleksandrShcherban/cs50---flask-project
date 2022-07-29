import os
import requests

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookupStock, lookupForex, lookupWeather, lookupNews, usd

app = Flask(__name__)

app.config["TEMPLATES_AUTO_RELOAD"] = True

app.jinja_env.filters["usd"] = usd

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

db = SQL("sqlite:///database.db")


@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    credit = db.execute("SELECT credit FROM users WHERE id = (?)", session["user_id"])[0]['credit']
    stocks = db.execute("SELECT symbol, id FROM stocks WHERE user_id = (?) ORDER BY symbol", session["user_id"])
    pairs = db.execute("SELECT pair, id FROM forex WHERE user_id = (?) ORDER BY pair", session["user_id"])
    weathers = db.execute("SELECT city, id FROM weather WHERE user_id = (?) ORDER BY city", session["user_id"])
    categories = db.execute("SELECT category, id FROM news WHERE user_id = (?) ORDER BY category", session["user_id"])
    names = {}
    prices = {}
    descriptions = {}
    temps = {}
    clouds = {}
    winds = {}
    gusts = {}
    titles = {}
    news = {}
    urls = {}
    times = {}
    rates = {}
    for record in stocks:
        lookup = lookupStock(record['symbol'])
        names[record['symbol']] = lookup['name']
        prices[record['symbol']] = lookup['price']
    for record in pairs:
        lookup = lookupForex(record['pair'])
        if lookup != None: rates[record['pair']] = lookup['rate']
        else: rates[record['pair']] = "API provider doesn't allow so many requests in a minute. Try refreshing page after one minute"
    for record in weathers:
        lookup = lookupWeather(record['city'])
        descriptions[record['city']] = lookup['description']
        temps[record['city']] = lookup['temp']
        clouds[record['city']] = lookup['clouds']
        winds[record['city']] = lookup['wind']
        gusts[record['city']] = lookup['gust']
    for record in categories:
        lookup = lookupNews(record['category'])
        titles[record['category']] = lookup['title']
        news[record['category']] = lookup['description']
        urls[record['category']] = lookup['url']
        times[record['category']] = lookup['time'].split('T')[0] + ' ' + lookup['time'].split('T')[1][:5]
    flash("Please use the appropriate menu selections to setup your infopage")
    return render_template("infopage.html", stocks=stocks, names=names, prices=prices, pairs=pairs, rates=rates, weathers=weathers, descriptions=descriptions, temps=temps, clouds=clouds, winds=winds, gusts=gusts, categories=categories, titles=titles, news=news, urls=urls, times=times, credit=credit)

@app.route("/register", methods=["GET", "POST"])
def register():
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

@app.route("/login", methods=["GET", "POST"])
def login():
    session.clear()
    if request.method == "POST":
        if not request.form.get("username"):
            return apology("must provide username", 403)
        elif not request.form.get("password"):
            return apology("must provide password", 403)
        rows = db.execute("SELECT * FROM users WHERE username = ?",
                          request.form.get("username"))
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)
        session["user_id"] = rows[0]["id"]
        flash('Hello, ' + request.form.get("username"))
        return redirect("/")
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash('Hope to see you back soon')
    return redirect("/")

@app.route("/stocks", methods=["GET", "POST"])
@login_required
def stocks():
    if request.method == "POST":
        symbol = request.form.get("symbol")
        credit = db.execute(
            "SELECT credit FROM users WHERE id = (?)", session["user_id"])[0]['credit']
        if symbol == "":
            return apology("Symbol is empty")
        symbol = lookupStock(symbol)
        if symbol == None:
            return apology("No such symbol exists")
        symbol = symbol['symbol']
        if credit == 0:
            return apology("You have zero credit for lines")
        credit -= 1
        db.execute("INSERT INTO stocks (symbol, user_id) VALUES (?, ?)",
                   symbol, session["user_id"])
        db.execute("UPDATE users SET credit = (?) WHERE id = (?)",
                   credit, session["user_id"])
        flash('You added ' + symbol + ' to your INFOpage')
        return redirect("/")
    else:
        credit = db.execute(
            "SELECT credit FROM users WHERE id = (?)", session["user_id"])[0]['credit']
        return render_template("stocks.html", credit=credit)


@app.route("/delStock", methods=["POST"])
@login_required
def delStock():
    if request.method == "POST":
        id = request.form.get("id")
        credit = db.execute(
            "SELECT credit FROM users WHERE id = (?)", session["user_id"])[0]['credit']
        db.execute("DELETE FROM stocks WHERE id = (?) LIMIT 1", id)
        credit += 1
        db.execute("UPDATE users SET credit = (?) WHERE id = (?)",
                   credit, session["user_id"])
        flash('INFO-line deleted')
        return redirect("/")


@app.route("/forex", methods=["GET", "POST"])
@login_required
def forex():
    if request.method == "POST":
        pair = request.form.get("from") + request.form.get("to")
        credit = db.execute("SELECT credit FROM users WHERE id = (?)", session["user_id"])[0]['credit']
        forex = lookupForex(pair)
        if forex == None:
            return apology("To many forex requests... Try after 1 minute please")
        if forex == "0":
            return apology("No such pair exists... Try another combination")
        if credit == 0:
            return apology("You have zero credit for lines")
        credit -= 1
        count = db.execute("SELECT COUNT(id) AS count FROM forex WHERE user_id = (?)", session["user_id"])
        print(count[0]['count'])
        if count[0]['count'] >= 3:
            return apology("Sorry, displaying of 3 pairs already. Cannot add due to specific restrictions of Forex API provider")
        db.execute("INSERT INTO forex (pair, user_id) VALUES (?, ?)", pair, session["user_id"])
        db.execute("UPDATE users SET credit = (?) WHERE id = (?)", credit, session["user_id"])
        flash('You added ' + pair + ' pair to your INFOpage')
        return redirect("/")
    else:
        credit = db.execute("SELECT credit FROM users WHERE id = (?)", session["user_id"])[0]['credit']
        return render_template("forex.html", credit=credit)


@app.route("/delForex", methods=["POST"])
@login_required
def delForex():
    if request.method == "POST":
        id = request.form.get("id")
        credit = db.execute("SELECT credit FROM users WHERE id = (?)", session["user_id"])[0]['credit']
        db.execute("DELETE FROM forex WHERE id = (?) LIMIT 1", id)
        credit += 1
        db.execute("UPDATE users SET credit = (?) WHERE id = (?)", credit, session["user_id"])
        flash('Exchange-rate pair deleted')
        return redirect("/")

@app.route("/weather", methods=["GET", "POST"])
@login_required
def weather():
    if request.method == "POST":
        ccc = lookupNews("health")
        city = request.form.get("city")
        credit = db.execute(
            "SELECT credit FROM users WHERE id = (?)", session["user_id"])[0]['credit']
        if city == "":
            return apology("City is empty")
        weather = lookupWeather(city)
        if weather == None:
            return apology("No such city found")
        city = weather["city"]
        if credit == 0:
            return apology("You have zero credit for lines")
        credit -= 1
        db.execute("INSERT INTO weather (city, user_id) VALUES (?, ?)",
                   city, session["user_id"])
        db.execute("UPDATE users SET credit = (?) WHERE id = (?)",
                   credit, session["user_id"])
        flash('You added ' + city + ' to your INFOpage')
        return redirect("/")
    else:
        credit = db.execute(
            "SELECT credit FROM users WHERE id = (?)", session["user_id"])[0]['credit']
        return render_template("weather.html", credit=credit)

@app.route("/delWeather", methods=["POST"])
@login_required
def delWeather():
    if request.method == "POST":
        id = request.form.get("id")
        credit = db.execute(
            "SELECT credit FROM users WHERE id = (?)", session["user_id"])[0]['credit']
        db.execute("DELETE FROM weather WHERE id = (?) LIMIT 1", id)
        credit += 1
        db.execute("UPDATE users SET credit = (?) WHERE id = (?)",
                   credit, session["user_id"])
        flash('INFO-line deleted')
        return redirect("/")

@app.route("/news", methods=["GET", "POST"])
@login_required
def news():
    if request.method == "POST":
        category = request.form.get("category")
        credit = db.execute("SELECT credit FROM users WHERE id = (?)", session["user_id"])[0]['credit']
        news = lookupNews(category)
        if news == None:
            return apology("No such news at the moment")
        if credit == 0:
            return apology("You have zero credit for lines")
        credit -= 1
        db.execute("INSERT INTO news (category, user_id) VALUES (?, ?)", category, session["user_id"])
        db.execute("UPDATE users SET credit = (?) WHERE id = (?)", credit, session["user_id"])
        flash('You added ' + category + ' category of news')
        return redirect("/")
    else:
        credit = db.execute("SELECT credit FROM users WHERE id = (?)", session["user_id"])[0]['credit']
        return render_template("news.html", credit=credit)

@app.route("/delNews", methods=["POST"])
@login_required
def delNews():
    if request.method == "POST":
        id = request.form.get("id")
        credit = db.execute("SELECT credit FROM users WHERE id = (?)", session["user_id"])[0]['credit']
        db.execute("DELETE FROM news WHERE id = (?) LIMIT 1", id)
        credit += 1
        db.execute("UPDATE users SET credit = (?) WHERE id = (?)", credit, session["user_id"])
        flash('News line deleted')
        return redirect("/")


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


# @app.route("/stockq", methods=["POST"])
# @login_required
# def stockq():
#     if request.method == "POST":
#         symbol = request.get_data()
#         symbol = lookup(symbol)
#         response = [2]
#         response[0] = symbol["symbol"]
#         response[1] = symbol["name"]
#         if symbol != None:
#             return response
#         else:
#             return {'1' : "No such symbol"}
