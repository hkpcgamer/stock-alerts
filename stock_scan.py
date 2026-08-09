import os
import requests
import pandas as pd
import yfinance as yf
from datetime import datetime

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

WATCHLIST = {
    "1475.T": 40,
    "0087.HK": 40,
    "293.HK": 40,
    "LAMR": 40,
    "MPLX": 35,
    "MU": 45,
    "MRVL": 45,
    "EIX": 35,
    "PLTR": 45,
    "BAC": 35,
    "BRK-B": 35,
    "COST": 40,
    "DIS": 40,
    "HD": 40,
    "PG": 35,
    "MC.PA": 40,
    "META": 45,
    "PSX": 35,
    "TSLA": 45,
    "SCHD": 35,
    "VIG": 35,
    "SPCX": 40,
    "SMH": 40
}


def rsi(series, period=14):
    delta = series.diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()

    rs = avg_gain / avg_loss

    return 100 - (100 / (1 + rs))


today = datetime.utcnow().weekday()

strong_buy = []
buy = []
summary = []

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
        ma200 = float(close.rolling(200).mean().iloc[-1])
        rsi14 = float(rsi(close).iloc[-1])

        high52 = float(close.max())

        discount = ((high52 - price) / high52) * 100

        trend = "✅" if price > ma200 else "❌"

        summary.append(
            f"{ticker} | RSI {rsi14:.1f} | {discount:.0f}% off high | {trend}"
        )

        if (
            price > ma200
            and rsi14 < 35
            and discount > 10
        ):

            strong_buy.append(
                f"{ticker}\n"
                f"Price: {price:.2f}\n"
                f"RSI: {rsi14:.1f}\n"
                f"Discount from High: {discount:.1f}%"
            )

        elif (
            price > ma200
            and rsi14 < rsi_limit
        ):

            buy.append(
                f"{ticker}\n"
                f"Price: {price:.2f}\n"
                f"RSI: {rsi14:.1f}"
            )

    except Exception as e:
        print(f"{ticker}: {e}")

# Sunday summary
if today == 6:

    if summary:
        message = "📊 Weekly Watchlist Summary\n\n" + "\n".join(summary)
    else:
        message = "📊 Weekly Watchlist Summary\n\nNo data available."

# Weekday alerts
else:

    sections = ["📈 Watchlist Scan"]

    if strong_buy:
        sections.append(
            "🚨 STRONG BUY\n\n" + "\n\n".join(strong_buy)
        )

    if buy:
        sections.append(
            "✅ BUY\n\n" + "\n\n".join(buy)
        )

    if not strong_buy and not buy:
        sections.append("No buy opportunities today.")

    message = "\n\n".join(sections)

requests.post(
    f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
    json={
        "chat_id": CHAT_ID,
        "text": message
    }
)
