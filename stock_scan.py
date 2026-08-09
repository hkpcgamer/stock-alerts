import os
import requests
import pandas as pd
import yfinance as yf

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

WATCHLIST = [
    "META",
    "BAC",
    "BRK-B",
    "SCHD",
    "VIG",
    "TSLA",
    "SMH"
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

        if data.empty:
            message_lines.append(f"{ticker}: No data")
            continue

        close = data["Close"].squeeze()

        price = float(close.iloc[-1])
        ma200 = float(close.rolling(200).mean().iloc[-1])

        if price > ma200:
            status = "✅ Above 200DMA"
        else:
            status = "❌ Below 200DMA"

        message_lines.append(
            f"{ticker}\n"
            f"Price: {price:.2f}\n"
            f"200DMA: {ma200:.2f}\n"
            f"{status}\n"
        )

    except Exception as e:
        message_lines.append(
            f"{ticker}: ERROR {str(e)}"
        )

message = "\n".join(message_lines)

requests.post(
    f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
    json={
        "chat_id": CHAT_ID,
        "text": message
    }
)
