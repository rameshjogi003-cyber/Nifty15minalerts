from flask import Flask, request, jsonify
import requests
from datetime import datetime
import pytz
import os

app = Flask(__name__)

# ── CONFIG via Environment Variables ────────────────────
# Set these in Render dashboard → Environment section
# Never hardcode tokens in the file
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
CHAT_ID   = os.environ.get("CHAT_ID",   "")
# ────────────────────────────────────────────────────────


def send_telegram(text):
    """Send a formatted HTML message to Telegram."""
    if not BOT_TOKEN or not CHAT_ID:
        print("ERROR: BOT_TOKEN or CHAT_ID not set in environment variables.")
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    response = requests.post(url, json={
        "chat_id":    CHAT_ID,
        "text":       text,
        "parse_mode": "HTML"
    })
    print(f"Telegram response: {response.status_code} — {response.text}")


def build_message(d):
    """Build the formatted Telegram message from TradingView webhook payload."""
    market    = d.get("market",    "N/A")
    direction = d.get("direction", "N/A")
    intensity = d.get("intensity", "N/A")
    action    = d.get("action",    "N/A")
    adx       = d.get("adx",       "N/A")
    chop      = d.get("chop",      "N/A")
    atr       = d.get("atr",       "N/A")
    lots      = d.get("lots",      "N/A")
    prevclose = d.get("prevclose", "N/A")

    # IST timestamp
    ist = pytz.timezone("Asia/Kolkata")
    now = datetime.now(ist).strftime("%H:%M IST, %d %b %Y")

    # Action icon
    icons = {
        "BUY CE":   "🟢",
        "BUY PE":   "🔴",
        "NO ENTRY": "🟡",
        "WAIT":     "⚪",
    }
    icon = icons.get(action, "⚪")

    # Regime icon
    regime_icons = {
        "TRENDING": "✅",
        "CHOPPY":   "⚠️",
        "NEUTRAL":  "➖",
    }
    regime_icon = regime_icons.get(market, "")

    return (
        f"📊 <b>NIFTY 15M Signal</b>  |  {now}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"{regime_icon} Market    : <b>{market}</b>\n"
        f"🧭 Direction : <b>{direction}</b>\n"
        f"⚡ Intensity  : <b>{intensity}</b>\n"
        f"{icon} Action    : <b>{action}</b>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"ADX  : {adx}  |  Chop : {chop}\n"
        f"ATR  : {atr} pts  |  Lots : {lots}\n"
        f"Prev close : {prevclose}\n"
        f"━━━━━━━━━━━━━━━"
    )


@app.route("/webhook", methods=["POST"])
def webhook():
    """Receive TradingView webhook and forward to Telegram."""
    try:
        data = request.get_json(force=True)
        print(f"Received payload: {data}")
        msg = build_message(data)
        send_telegram(msg)
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 400


@app.route("/")
def health():
    """Health check — Render pings this to keep service alive."""
    return "Nifty alert server is running ✅", 200


@app.route("/test", methods=["GET"])
def test():
    """
    Manual test endpoint.
    Visit https://your-app.onrender.com/test in browser
    to send a sample message to your Telegram.
    """
    sample = {
        "market":    "TRENDING",
        "direction": "BULLISH",
        "intensity": "STRONG",
        "action":    "BUY CE",
        "adx":       "28.4",
        "chop":      "41.2",
        "atr":       "118",
        "lots":      "1",
        "prevclose": "ABOVE"
    }
    msg = build_message(sample)
    send_telegram(msg)
    return jsonify({"status": "test message sent", "message": msg}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
