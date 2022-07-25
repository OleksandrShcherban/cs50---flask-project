import os
import requests
import urllib.parse
import time

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


def lookup(symbol):
    """Look up quote for symbol."""

    # Contact API
    try:
        # pk_ae98cd1be43345d7b1be7e51ccafefad
        # api_key = os.environ.get("API_KEY")
        api_key = "pk_ae98cd1be43345d7b1be7e51ccafefad"
        url = f"https://cloud.iexapis.com/stable/stock/{urllib.parse.quote_plus(symbol)}/quote?token={api_key}"
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException:
        return None

    # Parse response
    try:
        quote = response.json()
        return {
            "name": quote["companyName"],
            "price": float(quote["latestPrice"]),
            "symbol": quote["symbol"]
        }
    except (KeyError, TypeError, ValueError):
        return None


def usd(value):
    """Format value as USD."""
    return f"${value:,.2f}"

def timeformat(value):
    print("==============================")
    t = (2009, 2, 17, 17, 3, 38, 1, 48, 0)
    t = time.mktime(t)
    print("t = " + t)
    print("value = " + value)
    print (time.strftime("%b %d %Y %H:%M:%S", (t)))
    print (time.strftime("%b %d %Y %H:%M:%S", (value)))
    print (time.strftime("%b %d %Y %H:%M:%S", time.gmtime(t)))
    print (time.strftime("%b %d %Y %H:%M:%S", time.gmtime(value)))
    return time.strftime("%b %d %Y %H:%M:%S", time.gmtime(t))
    # time.strftime('%A, %Y-%m-%d %H:%M:%S', value)