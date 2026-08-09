import os
import requests
import pandas as pd
import yfinance as yf

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

WATCHLIST = {
    "META": 45,
    "TSLA": 45,
    "PLTR": 45,
    "MU": 45,
    "MRVL": 45,

    "BAC": 35,
    "BRK-B": 35,
    "SCHD": 35,
    "VIG": 35,
    "MPLX": 35,
    "PSX": 35,
    "EIX": 35,

    "SMH": 40,
    "COST": 40,
    "HD": 40,
    "DIS": 40,
    "PG": 40
}


def rsi(series, period=14):
    delta = series.diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()

    rs = avg_gain / avg_loss

    return 100 - (100 / (1 + rs))


strong_buy = []
buy = []

for ticker, rsi_limit in WATCHLIST.items():

    try:
        data = yf.download(
            ticker,
            period="1y",
            progress=False,
            auto_adjust=True
        )

        if data.empty:
            continue

        close = data["Close"].squeeze()

        price = float(close.iloc[-1])

        ma200 = float(
            close.rolling(200).mean().iloc[-1]
        )

        rsi14 = float(
            rsi(close).iloc[-1]
        )

        high52 = float(close.max())

        discount = (
            (high52 - price)
            / high52
            * 100
        )

        if (
            price > ma200
            and rsi14 < 35
            and discount > 10
        ):

            strong_buy.append(
                f"{ticker} | RSI {rsi14:.1f} | {discount:.1f}% below high"
            )

        elif (
            price > ma200
            and rsi14 < rsi_limit
        ):

            buy.append(
                f"{ticker} | RSI {rsi14:.1f}"
            )

    except Exception as e:
        print(f"{ticker}: {e}")

message = "📈 Watchlist Scan\n\n"

if strong_buy:
    message += "🚨 STRONG BUY\n"
    message += "\n".join(strong_buy)
    message += "\n\n"

if buy:
    message += "✅ BUY\n"
    message += "\n".join(buy)
    message += "\n\n"

if not strong_buy and not buy:
    message += "No buy opportunities today."

requests.post(
    f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
    json={
        "chat_id": CHAT_ID,
        "text": message
    }
)
