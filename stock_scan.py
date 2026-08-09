import os
import requests
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

weekly_details = []

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

        ma50 = float(close.rolling(50).mean().iloc[-1])
        ma200 = float(close.rolling(200).mean().iloc[-1])

        rsi14 = float(rsi(close).iloc[-1])

        high52 = float(close.max())

        discount = ((high52 - price) / high52) * 100

        above50 = price > ma50
        above200 = price > ma200

        status50 = "✅" if above50 else "❌"
        status200 = "✅" if above200 else "❌"

        # Score out of 10

        score = 0

        # Trend (4 points)
        if above200:
            score += 2

        if above50:
            score += 2

        # RSI (3 points)
        if rsi14 < 30:
            score += 3
        elif rsi14 < 35:
            score += 2
        elif rsi14 < 45:
            score += 1

        # Discount from high (3 points)
        if discount > 30:
            score += 3
        elif discount > 20:
            score += 2
        elif discount > 10:
            score += 1

        weekly_details.append(
            f"{ticker}\n"
            f"Score: {score}/10\n"
            f"RSI: {rsi14:.1f}\n"
            f"50DMA: {status50}\n"
            f"200DMA: {status200}\n"
            f"{discount:.0f}% below high\n"
        )

        # STRONG BUY

        if (
            above200
            and rsi14 < 35
            and discount > 10
        ):

            strong_buy.append(
                f"🚨 {ticker}\n\n"
                f"Score: {score}/10\n"
                f"Price: {price:.2f}\n"
                f"RSI: {rsi14:.1f}\n"
                f"50DMA: {status50}\n"
                f"200DMA: {status200}\n"
                f"Discount: {discount:.1f}%\n\n"
                f"Interpretation:\n"
                f"• Oversold (RSI below 35)\n"
                f"• Long-term trend intact\n"
                f"• Trading well below recent highs\n"
                f"• Potential accumulation opportunity"
            )

        # BUY

        elif (
            above200
            and rsi14 < rsi_limit
        ):

            buy.append(
                f"✅ {ticker}\n\n"
                f"Score: {score}/10\n"
                f"Price: {price:.2f}\n"
                f"RSI: {rsi14:.1f}\n"
                f"50DMA: {status50}\n"
                f"200DMA: {status200}\n\n"
                f"Interpretation:\n"
                f"• Pullback within an uptrend\n"
                f"• Momentum remains healthy\n"
                f"• Worth monitoring for entry"
            )

        # WATCH

        elif (
            not above200
            and rsi14 < 40
        ):

            watch.append(
                f"👀 {ticker}\n\n"
                f"Score: {score}/10\n"
                f"Price: {price:.2f}\n"
                f"RSI: {rsi14:.1f}\n"
                f"50DMA: {status50}\n"
                f"200DMA: {status200}\n"
                f"Discount: {discount:.1f}%\n\n"
                f"Interpretation:\n"
                f"• Oversold\n"
                f"• Long-term trend not yet confirmed\n"
                f"• Watch for move back above 200DMA"
            )

    except Exception as e:
        print(f"{ticker}: {e}")

# Sunday summary

if today == 6:

    message = "📊 Weekly Watchlist Review\n\n"
    message += "\n".join(weekly_details)

# Weekday scans

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
