import os
import requests
import urllib.parse

from flask import redirect, render_template, request, session
from functools import wraps


def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code


def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def lookupStock(symbol):
    try:
        # api_key = os.environ.get("API_KEY")
        api_key = "pk_ae98cd1be43345d7b1be7e51ccafefad"
        url = f"https://cloud.iexapis.com/stable/stock/{urllib.parse.quote_plus(symbol)}/quote?token={api_key}"
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException:
        return None

    try:
        quote = response.json()
        return {
            "name": quote["companyName"],
            "price": float(quote["latestPrice"]),
            "symbol": quote["symbol"]
        }
    except (KeyError, TypeError, ValueError):
        return None


def lookupForex(pair):
    try:
        url = f"https://api.polygon.io/v2/aggs/ticker/C:{pair}/prev?adjusted=true&apiKey=Xxp5786uyvAhyP_WbFpZ_7ncFzIiAd1b"
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException:
        return None
    try:
        quote = response.json()
        if (quote["resultsCount"] != 0):
            return {"rate": quote["results"][0]["c"]}
        else: return "0"
    except (KeyError, TypeError, ValueError):
        return None

def lookupWeather(city):
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid=890af9ff7986d6f9b72c5fe1cee18186"
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException:
        return None

    try:
        quote = response.json()
        try:
            return {
            "city": quote["name"],
            "description": quote["weather"][0]["description"],
            "temp": round(quote["main"]["temp"] - 273.15, 1),
            "clouds": quote["clouds"]["all"],
            "wind": quote["wind"]["speed"],
            "gust": quote["wind"]["gust"]}
        except (KeyError, TypeError, ValueError):
            return {
                "city": quote["name"],
                "description": quote["weather"][0]["description"],
                "temp": round((quote["main"]["temp"] - 273.15)*10)/10,
                "clouds": quote["clouds"]["all"],
                "wind": quote["wind"]["speed"],
                "gust": quote["wind"]["speed"]}
    except (KeyError, TypeError, ValueError):
        return None


def lookupNews(category):
    try:
        url = f"https://newsapi.org/v2/top-headlines?category={category}&language=en&pageSize=1&apiKey=4bd17288a3294a9bb2fb4fed940bfc78"
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException:
        return None
    try:
        quote = response.json()
        return {
            "title": quote["articles"][0]["title"],
            "description": quote["articles"][0]["description"],
            "url": quote["articles"][0]["url"],
            "time": quote["articles"][0]["publishedAt"]}
    except (KeyError, TypeError, ValueError):
        return None

def usd(value):
    """Format value as USD."""
    return f"${value:,.2f}"
