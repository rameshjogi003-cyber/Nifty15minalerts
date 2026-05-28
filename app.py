from flask import Flask, request, jsonify
import requests
from datetime import datetime
import pytz
import os

app = Flask(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
CHAT_ID   = os.environ.get("CHAT_ID",   "")


def send_telegram(text):
    if not BOT_TOKEN or not CHAT_ID:
        print("ERROR: BOT_TOKEN or CHAT_ID not set.")
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    response = requests.post(url, json={
        "chat_id":    CHAT_ID,
        "text":       text,
        "parse_mode": "HTML"
    })
    print(f"Telegram: {response.status_code} — {response.text}")


# ── NIFTY MESSAGE ────────────────────────────────────────
def build_nifty_message(d):
    market    = d.get("market",    "N/A")
    direction = d.get("direction", "N/A")
    intensity = d.get("intensity", "N/A")
    action    = d.get("action",    "N/A")
    adx       = d.get("adx",       "N/A")
    chop      = d.get("chop",      "N/A")
    atr       = d.get("atr",       "N/A")
    lots      = d.get("lots",      "N/A")
    prevclose = d.get("prevclose", "N/A")

    ist = pytz.timezone("Asia/Kolkata")
    now = datetime.now(ist).strftime("%H:%M IST, %d %b %Y")

    icons = {"BUY CE": "🟢", "BUY PE": "🔴", "NO ENTRY": "🟡", "WAIT": "⚪"}
    icon  = icons.get(action, "⚪")
    regime_icons = {"TRENDING": "✅", "CHOPPY": "⚠️", "NEUTRAL": "➖"}
    regime_icon  = regime_icons.get(market, "")

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


# ── WTI CRUDE MESSAGE ────────────────────────────────────
def build_crude_message(d):
    close_p   = d.get("close",     "N/A")
    change    = d.get("change",    "N/A")
    changepct = d.get("changepct", "N/A")
    market    = d.get("market",    "N/A")
    direction = d.get("direction", "N/A")
    intensity = d.get("intensity", "N/A")
    action    = d.get("action",    "N/A")
    adx       = d.get("adx",       "N/A")
    chop      = d.get("chop",      "N/A")
    atr       = d.get("atr",       "N/A")
    lots      = d.get("lots",      "N/A")
    rpl       = d.get("riskperlot","N/A")
    sl        = d.get("sl",        "N/A")
    prevclose = d.get("prevclose", "N/A")

    ist = pytz.timezone("Asia/Kolkata")
    now = datetime.now(ist).strftime("%H:%M IST, %d %b %Y")

    icons = {"BUY CALL": "🟢", "BUY PUT": "🔴", "NO ENTRY": "🟡", "WAIT": "⚪"}
    icon  = icons.get(action, "⚪")
    regime_icons = {"TRENDING": "✅", "CHOPPY": "⚠️", "NEUTRAL": "➖"}
    regime_icon  = regime_icons.get(market, "")
    chg_icon = "📈" if not str(change).startswith("-") else "📉"

    return (
        f"🛢 <b>WTI CRUDE 15M Signal</b>  |  {now}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"💰 Close     : <b>${close_p}</b>\n"
        f"{chg_icon} Change    : <b>{change} ({changepct}%)</b>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"{regime_icon} Market    : <b>{market}</b>\n"
        f"🧭 Direction : <b>{direction}</b>\n"
        f"⚡ Intensity  : <b>{intensity}</b>\n"
        f"{icon} Action    : <b>{action}</b>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"ADX  : {adx}  |  Chop : {chop}\n"
        f"ATR  : ${atr}  |  Lots : {lots}\n"
        f"Risk/lot : ${rpl}  |  SL : ${sl}\n"
        f"Prev close : {prevclose}\n"
        f"━━━━━━━━━━━━━━━"
    )


# ── ROUTES ───────────────────────────────────────────────
@app.route("/")
def health():
    return "Nifty + WTI alert server running ✅", 200


@app.route("/webhook", methods=["POST"])
def webhook_nifty():
    try:
        data = request.get_json(force=True)
        print(f"Nifty payload: {data}")
        send_telegram(build_nifty_message(data))
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/webhook/crude", methods=["POST"])
def webhook_crude():
    try:
        data = request.get_json(force=True)
        print(f"WTI payload: {data}")
        send_telegram(build_crude_message(data))
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/test", methods=["GET"])
def test_nifty():
    sample = {
        "market": "TRENDING", "direction": "BULLISH", "intensity": "STRONG",
        "action": "BUY CE", "adx": "28.4", "chop": "41.2",
        "atr": "118", "lots": "1", "prevclose": "ABOVE"
    }
    send_telegram(build_nifty_message(sample))
    return jsonify({"status": "nifty test sent"}), 200


@app.route("/test/crude", methods=["GET"])
def test_crude():
    sample = {
        "close": "78.42", "change": "+0.38", "changepct": "+0.49",
        "market": "TRENDING", "direction": "BULLISH", "intensity": "STRONG",
        "action": "BUY CALL", "adx": "29.1", "chop": "40.8",
        "atr": "0.54", "lots": "1", "riskperlot": "37.80",
        "sl": "700", "prevclose": "ABOVE"
    }
    send_telegram(build_crude_message(sample))
    return jsonify({"status": "crude test sent"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
