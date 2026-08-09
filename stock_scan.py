import os
import requests
import pandas as pd
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
    "VIG"
]

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

        if price > ma200:
            message_lines.append(
                f"{ticker}: Above 200DMA ✅"
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
