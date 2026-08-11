import os
import requests
import yfinance as yf
from datetime import datetime

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
FINNHUB_API_KEY = os.environ.get("FINNHUB_API_KEY")

WATCHLIST = {
    "0087.HK": 40,
    "0293.HK": 40,
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
    "TSLA": 45,
    "VIG": 35,
    "SPCX": 40,
    "SMH": 40,
    "IAU": 40,
    "ARKG": 45, 
    "ICLN": 40, 
    "IGF": 40, 
    "VGIT": 35, 
    "XLE": 35, 
    "XLU": 35

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


def get_news(ticker):

    try:

        from datetime import date, timedelta

        today = date.today()
        start = today - timedelta(days=30)

        url = (
            f"https://finnhub.io/api/v1/company-news"
            f"?symbol={ticker}"
            f"&from={start}"
            f"&to={today}"
            f"&token={FINNHUB_API_KEY}"
        )

        response = requests.get(
            url,
            timeout=10
        )

        articles = response.json()

        headlines = []

        for article in articles[:4]:

            headline = article.get(
                "headline"
            )

            if headline:
                headlines.append(
                    headline
                )

        return headlines

    except Exception:

        return []


from datetime import datetime, UTC

def trend_state(above50, above200):

    if above50 and above200:
        return "✅ Strong Uptrend"

    elif (not above50) and above200:
        return "⚠️ Pullback in Uptrend"

    elif above50 and (not above200):
        return "🔄 Recovery Attempt"

    else:
        return "❌ Downtrend"


today = datetime.now(UTC).weekday()

strong_buy = []
buy = []
watch = []

weekly_details = []
rankings = []
events = []
daily_details = []

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

        ma50_yesterday = float(
            close.rolling(50).mean().iloc[-2]
        )

        ma200_yesterday = float(
            close.rolling(200).mean().iloc[-2]
        )

        golden_cross = (
            ma50_yesterday <= ma200_yesterday
            and ma50 > ma200
        )

        death_cross = (
            ma50_yesterday >= ma200_yesterday
            and ma50 < ma200
        )

        
        # Strict Cup & Handle Detection

        window = close.tail(252)  # ~12 months

        left_side = window.iloc[:126]
        right_side = window.iloc[126:]

        left_peak = float(left_side.max())
        bottom = float(window.min())
        right_peak = float(right_side.max())

        cup_depth = (
            (left_peak - bottom)
            / left_peak
        )

        near_old_high = (
            abs(right_peak - left_peak)
            / left_peak
            < 0.05
        )

        handle_low = float(
            close.tail(20).min()
        )

        handle_depth = (
            (right_peak - handle_low)
            / right_peak
        )

        cup_handle = (
            0.10 < cup_depth < 0.35
            and near_old_high
            and handle_depth < 0.15
            and price > ma50
            and price > ma200
        )

        high52 = float(close.max())

        discount = ((high52 - price) / high52) * 100

        above50 = price > ma50
        above200 = price > ma200

        status50 = "✅" if above50 else "❌"
        status200 = "✅" if above200 else "❌"

        trend = trend_state(
            above50,
            above200
        )

        trend = trend_state(
            above50,
            above200
        )

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

        # Prevent negative scores

        score = max(score, 0)

        classification = classify(score)

        if golden_cross:
            events.append(
                f"✅ GOLDEN CROSS\n{ticker}"
            )

        if death_cross:
            events.append(
                f"❌ DEATH CROSS\n{ticker}"
            )

        if cup_handle:
            events.append( 
                f"🔄 CUP & HANDLE\n" 
                f"{ticker}\n" 
                f"Cup Depth: {cup_depth:.0%}" 
            )
            
        rankings.append(
            (score, ticker, classification)
        )


        daily_details.append(
            (
                score,
                f"{ticker}\n"
                f"Score: {score}/100\n"
                f"Classification: {classification}\n"
                f"RSI: {rsi14:.1f}\n"
                f"50DMA: {status50}\n"
                f"200DMA: {status200}\n"
                f"{discount:.0f}% below high\n"
            )
        )
        weekly_details.append(
            (
                score,
                f"{ticker}\n"
                f"Score: {score}/100\n"
                f"Classification: {classification}\n"
                f"RSI: {rsi14:.1f}\n"
                f"50DMA: {status50}\n"
                f"200DMA: {status200}\n"
                f"{discount:.0f}% below high\n"
            )
        )

        # STRONG BUY

        if (
            above200
            and rsi14 < 35
            and discount > 10
        ):

            news_section = ""

            if FINNHUB_API_KEY:

                news_list = get_news(ticker)

                if news_list:

                    news_section = "\n\n📰 Recent News\n"

                    for headline in news_list:
                        news_section += f"• {headline}\n"

            strong_buy.append(
                f"🚨 {ticker}\n\n"
                f"Score: {score}/100\n"
                f"Classification: {classification}\n"
                f"Trend: {trend}\n\n"
                f"Price: {price:.2f}\n"
                f"RSI: {rsi14:.1f}\n"
                f"50DMA: {status50}\n"
                f"200DMA: {status200}\n"
                f"Discount: {discount:.1f}%\n\n"
                f"Technical Thesis:\n"
                f"• Oversold (RSI below 35)\n"
                f"• Long-term trend intact\n"
                f"• Trading below recent highs\n"
                f"• Potential accumulation opportunity"
                f"{news_section}"
            )

        # BUY

        elif (
            above200
            and rsi14 < rsi_limit
        ):

            buy.append(
                f"✅ {ticker}\n\n"
                f"Score: {score}/100\n"
                f"Classification: {classification}\n\n"
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
                f"Score: {score}/100\n"
                f"Classification: {classification}\n\n"
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

rankings.sort(
    key=lambda x: x[0],
    reverse=True
)
print("DEBUG rankings:", len(rankings))
print("DEBUG daily_details:", len(daily_details))

top5 = rankings[:5]

# Sunday Review

if today == 6:

    weekly_details.sort(
        key=lambda x: x[0],
        reverse=True
    )

    message = "📊 Weekly Watchlist Review\n\n"

    if events:
        message += (
            "🔔 TECHNICAL EVENTS\n\n"
            + "\n\n".join(events)
            + "\n\n"
        )

    message += "🏆 TOP TECHNICAL OPPORTUNITIES\n\n"

    for rank, item in enumerate(top5, start=1):
        message += (
            f"{rank}. {item[1]} — "
            f"{item[0]}/100 "
            f"({item[2]})\n"
        )

    message += "\n\n"

    for _, detail in weekly_details:
        message += detail + "\n"

# Weekday Scan

else:

    leaderboard = ["🏆 TOP TECHNICAL OPPORTUNITIES"]

    for rank, item in enumerate(top5, start=1):
        leaderboard.append(
            f"{rank}. {item[1]} — "
            f"{item[0]}/100 "
            f"({item[2]})"
        )

    daily_details.sort(
    key=lambda x: x[0],
    reverse=True
)

    sections = ["📈 Watchlist Scan"]

    
    if events: 
        sections.append( 
            "🔔 TECHNICAL EVENTS\n\n" + 
            "\n\n".join(events) 
        )
        
    sections.append( 
        "\n".join(leaderboard) 
    )

    all_stocks = ["📊 FULL WATCHLIST"]

    for _, detail in daily_details:
        all_stocks.append(detail)

    sections.append(
        "\n".join(all_stocks)
    )
    
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

response =  MAX_LEN = 3500 
            if len(message) <= MAX_LEN: 
                
                response = requests.post( 
                    f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                    json={
                        "chat_id": CHAT_ID,
                        "text": message
                    }
                )
                print("Telegram status:", response.status_code) 
                print("Telegram response:", response.text) 
            else: 
                part1 = message[:MAX_LEN]
                part2 = message[MAX_LEN:]
                
                response1 = requests.post(
                    f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", 
                    json={
                        "chat_id": CHAT_ID, 
                        "text": part1
                    }
                ) 
                
                response2 = requests.post(
                    f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                    json={ 
                        "chat_id": CHAT_ID,
                        "text": part2 } 
                ) 
                print("Telegram status 1:", response1.status_code) 
                print("Telegram status 2:", response2.status_code)

print("Telegram status:", response.status_code)
print("Telegram response:", response.text)

def trend_state(above50, above200):
    if above50 and above200:
        return "✅ Strong Uptrend"
    elif (not above50) and above200:
        return "⚠️ Pullback in Uptrend"
    elif above50 and (not above200):
        return "🔄 Recovery Attempt"
    else:
        return "❌ Downtrend"
if rsi14 > 80:
    score -= 20
elif rsi14 > 75:
    score -= 15
elif rsi14 > 70:
    score -= 10
news_section = ""

try:
    stock = yf.Ticker(ticker)

    news = stock.news[:4]

    if news:

        news_section = "\n\n📰 Recent News\n"

        for article in news:

            title = article.get("title", "No title")

            news_section += f"• {title}\n"

except Exception:
    pass
