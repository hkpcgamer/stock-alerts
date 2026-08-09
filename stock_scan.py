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


def classify(score):
    if score >= 90:
        return "🏆 Exceptional Setup"
    elif score >= 75:
        return "🚨 Strong Opportunity"
    elif score >= 60:
        return "✅ Attractive"
    elif score >= 40:
        return "👀 Watch Closely"
    elif score >= 20:
        return "⚪ Neutral"
    else:
        return "❌ Weak Setup"


# Function to compute trend state

def trend_state(above50, above200):
    if above50 and above200:
        return "✅ Strong Uptrend"
    elif (not above50) and above200:
        return "⚠️ Pullback in Uptrend"
    elif above50 and (not above200):
        return "🔄 Recovery Attempt"
    else:
        return "❌ Downtrend"


today = datetime.utcnow().weekday()

strong_buy = []
buy = []
watch = []

weekly_details = []
rankings = []

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
        trend = trend_state(above50, above200)

        # Technical Opportunity Score (100)
        score = 0

        # Trend (55 points)
        if above200:
            score += 40

        if above50:
            score += 15

        # RSI (25 points)
        if rsi14 < 30:
            score += 25
        elif rsi14 < 35:
            score += 20
        elif rsi14 < 40:
            score += 15
        elif rsi14 < 45:
            score += 10
        elif rsi14 < 50:
            score += 5

        # Discount from high (20 points)
        if discount > 40:
            score += 20
        elif discount > 30:
            score += 15
        elif discount > 20:
            score += 10
        elif discount > 10:
            score += 5

        # Overbought penalty
        if rsi14 > 80:
            score -= 20
        elif rsi14 > 75:
            score -= 15
        elif rsi14 > 70:
            score -= 10

        classification = classify(score)

        rankings.append((score, ticker, classification))

        weekly_details.append(
            (
                score,
                f"{ticker}
"
                f"Score: {score}/100
"
                f"Classification: {classification}
"
                f"Trend: {trend}
"
                f"RSI: {rsi14:.1f}
"
                f"50DMA: {status50}
"
                f"200DMA: {status200}
"
                f"{discount:.0f}% below high
"
            )
        )

        # STRONG BUY
        if (
            above200
            and rsi14 < 35
            and discount > 10
        ):
            strong_buy.append(
                f"🚨 {ticker}

"
                f"Score: {score}/100
"
                f"Classification: {classification}
"
                f"Trend: {trend}

"
                f"Price: {price:.2f}
"
                f"RSI: {rsi14:.1f}
"
                f"50DMA: {status50}
"
                f"200DMA: {status200}
"
                f"Discount: {discount:.1f}%

"
                f"Interpretation:
"
                f"• Oversold (RSI below 35)
"
                f"• Long-term trend intact
"
                f"• Trading below recent highs
"
                f"• Potential accumulation opportunity"
            )

        # BUY
        elif (
            above200
            and rsi14 < rsi_limit
        ):
            buy.append(
                f"✅ {ticker}

"
                f"Score: {score}/100
"
                f"Classification: {classification}
"
                f"Trend: {trend}

"
                f"Price: {price:.2f}
"
                f"RSI: {rsi14:.1f}
"
                f"50DMA: {status50}
"
                f"200DMA: {status200}

"
                f"Interpretation:
"
                f"• Pullback within an uptrend
"
                f"• Momentum remains healthy
"
                f"• Worth monitoring for entry"
            )

        # WATCH
        elif (
            not above200
            and rsi14 < 40
        ):
            watch.append(
                f"👀 {ticker}

"
                f"Score: {score}/100
"
                f"Classification: {classification}
"
                f"Trend: {trend}

"
                f"Price: {price:.2f}
"
                f"RSI: {rsi14:.1f}
"
                f"50DMA: {status50}
"
                f"200DMA: {status200}
"
                f"Discount: {discount:.1f}%

"
                f"Interpretation:
"
                f"• Oversold
"
                f"• Long-term trend not yet confirmed
"
                f"• Watch for move back above 200DMA"
            )

    except Exception as e:
        print(f"{ticker}: {e}")

rankings.sort(key=lambda x: x[0], reverse=True)

top5 = rankings[:5]

# Sunday Review
if today == 6:
    weekly_details.sort(key=lambda x: x[0], reverse=True)
    message = "📊 Weekly Watchlist Review

"
    message += "🏆 TOP TECHNICAL OPPORTUNITIES

"
    for rank, item in enumerate(top5, start=1):
        message += (
            f"{rank}. {item[1]} — "
            f"{item[0]}/100 "
            f"({item[2]})
"
        )
    message += "

"
    for _, detail in weekly_details:
        message += detail + "
"
# Weekday Scan
else:
    leaderboard = ["🏆 TOP TECHNICAL OPPORTUNITIES"]
    for rank, item in enumerate(top5, start=1):
        leaderboard.append(
            f"{rank}. {item[1]} — "
            f"{item[0]}/100 "
            f"({item[2]})"
        )
    sections = [
        "📈 Watchlist Scan",
        "
".join(leaderboard)
    ]
    if strong_buy:
        sections.append(
            "🚨 STRONG BUY

" +
            "

".join(strong_buy)
        )
    if buy:
        sections.append(
            "✅ BUY

" +
            "

".join(buy)
        )
    if watch:
        sections.append(
            "👀 WATCH

" +
            "

".join(watch)
        )
    if not strong_buy and not buy and not watch:
        sections.append(
            "No buy opportunities today."
        )
    message = "

".join(sections)

requests.post(
    f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
    json={
        "chat_id": CHAT_ID,
        "text": message
    }
)
