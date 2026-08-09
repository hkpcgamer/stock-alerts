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
watch = []

summary_strong = []
summary_watch = []
summary_healthy = []
summary_extended = []

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

        discount = (
            (high52 - price)
            / high52
            * 100
        )

        above200 = price > ma200

        # STRONG BUY
        if (
            above200
            and rsi14 < 35
            and discount > 10
        ):

            explanation = (
                "Reason:\n"
                "• Above 200DMA ✅\n"
                "• RSI below 35 ✅\n"
                "• More than 10% below 52-week high ✅\n\n"
                "Interpretation:\n"
                "Oversold stock in a long-term uptrend."
            )

            strong_buy.append(
                f"🚨 {ticker}\n"
                f"Price: {price:.2f}\n"
                f"RSI: {rsi14:.1f}\n"
                f"Discount: {discount:.1f}%\n\n"
                f"{explanation}"
            )

            summary_strong.append(
                f"{ticker} (RSI {rsi14:.1f})"
            )

        # BUY
        elif (
            above200
            and rsi14 < rsi_limit
        ):

            explanation = (
                "Reason:\n"
                "• Above 200DMA ✅\n"
                "• RSI below threshold ✅\n\n"
                "Interpretation:\n"
                "Healthy uptrend experiencing a pullback."
            )

            buy.append(
                f"✅ {ticker}\n"
                f"Price: {price:.2f}\n"
                f"RSI: {rsi14:.1f}\n\n"
                f"{explanation}"
            )

        # WATCH
        elif (
            not above200
            and rsi14 < 40
        ):

            explanation = (
                "Reason:\n"
                "• Oversold ✅\n"
                "• Below 200DMA ❌\n\n"
                "Interpretation:\n"
                "Potential opportunity if trend improves."
            )

            watch.append(
                f"👀 {ticker}\n"
                f"Price: {price:.2f}\n"
                f"RSI: {rsi14:.1f}\n"
                f"Discount: {discount:.1f}%\n\n"
                f"{explanation}"
            )

            summary_watch.append(
                f"{ticker} (RSI {rsi14:.1f})"
            )

        # Weekly summary categorisation
        if rsi14 > 70:
            summary_extended.append(
                f"{ticker} (RSI {rsi14:.1f})"
            )

        elif above200 and 40 <= rsi14 <= 70:
            summary_healthy.append(
                f"{ticker} (RSI {rsi14:.1f})"
            )

    except Exception as e:
        print(f"{ticker}: {e}")

# Sunday Summary
if today == 6:

    sections = ["📊 Weekly Watchlist Review"]

    if summary_strong:
        sections.append(
            "🚨 STRONG BUY\n" +
            "\n".join(summary_strong)
        )

    if summary_watch:
        sections.append(
            "👀 WATCH\n" +
            "\n".join(summary_watch)
        )

    if summary_healthy:
        sections.append(
            "✅ HEALTHY TREND\n" +
            "\n".join(summary_healthy)
        )

    if summary_extended:
        sections.append(
            "⚠️ EXTENDED\n" +
            "\n".join(summary_extended)
        )

    message = "\n\n".join(sections)

# Weekday Scans
else:

    sections = ["📈 Watchlist Scan"]

    if strong_buy:
        sections.append(
            "🚨 STRONG BUY\n\n" +
            "\n\n".join(strong_buy)
        )

    if buy:
        sections.append(
            "✅ BUY\n\n" +
            "\n\n".join(buy)
        )

    if watch:
        sections.append(
            "👀 WATCH\n\n" +
            "\n\n".join(watch)
        )

    if not strong_buy and not buy and not watch:
        sections.append(
            "No buy opportunities today."
        )

    message = "\n\n".join(sections)

requests.post(
    f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
    json={
        "chat_id": CHAT_ID,
        "text": message
    }
)
