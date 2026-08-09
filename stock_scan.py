import os
import requests
import pandas as pd
import numpy as np
import yfinance as yf

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

WATCHLIST = [
    "1475.T",
    "0087.HK",
    "LAMR",
    "MPLX",
    "MU",
    "MRVL",
    "EIX",
    "PLTR",
    "BAC",
    "BRK-B",
    "COST",
    "DIS",
    "HD",
    "PG",
    "MC.PA",
    "META",
    "PSX",
    "TSLA",
    "SCHD",
    "VIG",
    "293.HK",
    "SPCX",
    "SMH",
    "0083.HK"
]
def rsi(series, period=14):
    delta = series.diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()

    rs = avg_gain / avg_loss

    return 100 - (100 / (1 + rs))

message_lines = []

for ticker in WATCHLIST:
    try:
        data = yf.download(
            ticker,
            period="1y",
            progress=False,
            auto_adjust=True
        )
         close = data["Close"]

        ma200 = close.rolling(200).mean().iloc[-1]
        price = close.iloc[-1]
        rsi14 = rsi(close).iloc[-1]

        if price > ma200:
            message_lines.append(
                f"{ticker}\n"
                f"Price: {price:.2f}\n"
                f"RSI: {rsi14:.1f}\n"
                f"Above 200DMA ✅\n"
            )


    except Exception as e:
        print(e)

message = "\n".join(message_lines)

if not message:
    message = "No stocks above 200DMA."

requests.post(
    f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
    json={
        "chat_id": CHAT_ID,
        "text": message
    }
)
