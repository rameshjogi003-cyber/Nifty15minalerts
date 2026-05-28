# Nifty 15M Telegram Alert Server

Receives TradingView webhooks and forwards formatted Nifty signals to Telegram.

## Files

| File | Purpose |
|------|---------|
| `app.py` | Flask webhook server |
| `requirements.txt` | Python dependencies |

## Deploy on Render (free)

1. Fork or upload this repo to GitHub
2. Go to [render.com](https://render.com) → New → Web Service
3. Connect your GitHub repo
4. Fill in these settings:

| Field | Value |
|-------|-------|
| Runtime | Python 3 |
| Build command | `pip install -r requirements.txt` |
| Start command | `gunicorn app:app` |
| Instance type | Free |
| Region | Singapore |

5. Under **Environment Variables** add:
   - `BOT_TOKEN` → your Telegram bot token from @BotFather
   - `CHAT_ID`   → your Telegram chat ID

## Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | Health check |
| `/webhook` | POST | Receives TradingView alert |
| `/test` | GET | Sends a sample message to Telegram |

## Getting your Telegram credentials

**Bot token:**
1. Open Telegram → search `@BotFather`
2. Send `/newbot` and follow prompts
3. Copy the token provided

**Chat ID:**
1. Send any message to your new bot
2. Open: `https://api.telegram.org/botYOUR_TOKEN/getUpdates`
3. Find `"chat":{"id":XXXXXXX}` — that number is your Chat ID

## TradingView Alert Setup

After deploying, your webhook URL is:
```
https://your-app-name.onrender.com/webhook
```

In TradingView:
- Alerts → Create Alert
- Condition: select the Nifty indicator
- Trigger: **Once Per Bar Close**
- Notifications: enable Webhook URL → paste your URL
- Leave Message field blank (Pine Script sends the JSON)

## Telegram Message Format

```
📊 NIFTY 15M Signal  |  10:15 IST, 28 May 2026
━━━━━━━━━━━━━━━
✅ Market    : TRENDING
🧭 Direction : BULLISH
⚡ Intensity  : STRONG
🟢 Action    : BUY CE
━━━━━━━━━━━━━━━
ADX  : 28.4  |  Chop : 41.2
ATR  : 118 pts  |  Lots : 1
Prev close : ABOVE
━━━━━━━━━━━━━━━
```
