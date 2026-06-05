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


# ════════════════════════════════════════════════════════════════
#  INTRADAY OPTIONS MESSAGE  (Pine Script v2 — /webhook/intraday)
#  Handles Nifty 5M signals with ORB, VWAP, Score, Trail SL
# ════════════════════════════════════════════════════════════════
def build_intraday_message(d):
    # TradingView Settings to change per instrument:
    #   Nifty:      Entry Start=9:30  Exit By=14:15  Session End=15:30
    #   Crude/Gold: Entry Start=9:30  Exit By=23:00  Session End=23:30
    ticker     = d.get("ticker",      "NIFTY")
    close_p    = d.get("close",       "N/A")
    action     = d.get("action",      "N/A")
    direction  = d.get("direction",   "N/A")
    intensity  = d.get("intensity",   "N/A")

    # ORB fields — now always populated in v2
    orb        = d.get("orb",         "N/A")
    orb_h      = d.get("orbhigh",     "N/A")
    orb_l      = d.get("orblow",      "N/A")

    # VWAP fields — vwap_pos is NEW in v2
    vwap       = d.get("vwap",        "N/A")
    vwap_pos   = d.get("vwap_pos",    "N/A")

    # ADX — adx_rising is NEW in v2
    adx        = d.get("adx",         "N/A")
    adx_rising = d.get("adx_rising",  "N/A")

    # Chop — NEW in v2 (was always N/A before)
    chop       = d.get("chop",        "N/A")

    # RSI and Score — now always populated in v2
    rsi        = d.get("rsi",         "N/A")
    score      = d.get("score",       "N/A")

    # Position sizing
    lots       = d.get("lots",        "N/A")
    rpl        = d.get("riskperlot",  "N/A")
    sl         = d.get("sl",          "N/A")

    # Trail SL — NEW in v2
    trail_dist = d.get("trail_dist",  "N/A")
    trail_peak = d.get("trail_peak",  "N/A")
    trail_hit  = d.get("trail_hit",   "NO")

    ist = pytz.timezone("Asia/Kolkata")
    now = datetime.now(ist).strftime("%H:%M IST, %d %b %Y")

    # ── Action icon ───────────────────────
    action_icons = {
        "BUY CE":               "🟢",
        "BUY PE":               "🔴",
        "NO ENTRY — FLAT":      "⚪",
        "NO ENTRY — CHOPPY":    "⚠️",
        "NO ENTRY — SPIKE":     "⚡",
        "WAIT":                 "⚪",
        "WAIT — OR FORMING":    "🟡",
        "TIME OVER — EXIT":     "🔔",
        "TRAIL SL — EXIT":      "🛑",
        "MARKET CLOSED":        "🔒"
    }
    icon = action_icons.get(action, "⚪")

    # ── ORB icon ──────────────────────────
    orb_icon = "🚀" if orb == "BULL BREAK" else "💥" if orb == "BEAR BREAK" else "📦"

    # ── ADX display with rising arrow ──────
    adx_str = f"{adx} {'▲' if adx_rising == 'YES' else '▼' if adx_rising == 'NO' else ''}"

    # ── Chop regime label ────────────────
    try:
        chop_val = float(chop)
        chop_label = "TRENDING" if chop_val < 38.2 else "CHOPPY" if chop_val > 61.8 else "MIXED"
    except (ValueError, TypeError):
        chop_label = "N/A"

    # ── VWAP position display ────────────────
    vwap_display = f"{vwap} ({vwap_pos})" if vwap_pos not in ("N/A", "") else vwap

    # ── Trail SL block (only shown when a trade is active) ─────────
    # trail_peak = "NA" means no active trade (Pine sends "NA" string when inactive)
    trail_block = ""
    if trail_hit == "YES — EXIT NOW":
        trail_block = f"🛑 TRAIL SL HIT — EXIT NOW\n"
    elif trail_peak not in ("N/A", "NA", "", None) and trail_dist not in ("N/A", "NA", "", None):
        trail_block = f"📍 Trail SL : {trail_dist} pts from peak {trail_peak}\n"

    return (
        f"⚡ <b>{ticker} INTRADAY</b>  |  {now}\n"
        f"━━━━━\n"
        f"💰 Close     : <b>₹{close_p}</b>\n"
        f"{orb_icon} ORB       : <b>{orb}</b>\n"
        f"   H: {orb_h}  |  L: {orb_l}\n"
        f"━━━━\n"
        f"🧭 Direction : <b>{direction}</b>\n"
        f"⚡ Intensity  : <b>{intensity}</b>\n"
        f"{icon} Action    : <b>{action}</b>\n"
        f"━━━━━\n"
        f"VWAP : {vwap_display}  \n"
         f"ADX : {adx_str}\n"
        f"RSI  : {rsi} \n"
         f"Score : {score}\n"
        f"Chop : {chop} ({chop_label})\n"
            )


@app.route("/webhook/intraday", methods=["POST"])
def webhook_intraday():
    try:
        data = request.get_json(force=True)
        print(f"Intraday payload: {data}")
        send_telegram(build_intraday_message(data))
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        print(f"Intraday error: {e}")
        return jsonify({"error": str(e)}), 400


@app.route("/test/intraday", methods=["GET"])
def test_intraday():
    sample = {
        "ticker":      "NIFTY",
        "close":       "24385.50",
        "action":      "BUY CE",
        "direction":   "BULLISH",
        "intensity":   "STRONG",
        "orb":         "BULL BREAK",
        "orbhigh":     "24350.0",
        "orblow":      "24280.0",
        "vwap":        "24310.5",
        "vwap_pos":    "ABOVE",
        "adx":         "28.4",
        "adx_rising":  "YES",
        "chop":        "31.2",
        "rsi":         "62.3",
        "score":       "7B/2Be",
        "lots":        "2",
        "riskperlot":  "4550",
        "sl":          "6000",
        "trail_dist":  "20",
        "trail_peak":  "24390",
        "trail_hit":   "NO"
    }
    send_telegram(build_intraday_message(sample))
    return jsonify({"status": "intraday test sent"}), 200


# ════════════════════════════════════════════════════════════════
#  GENERIC SIGNAL MESSAGE  (Crude Oil, Gold, Silver — old scripts)
#  /webhook  and  /webhook/crude
# ════════════════════════════════════════════════════════════════
def build_message(d):
    ticker    = d.get("ticker",    "UNKNOWN")
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

    is_indian = any(x in ticker.upper() for x in
                    ["NIFTY", "BANKNIFTY", "MCX", "CRUDEOIL", "GOLD", "SILVER", "NSE", "BSE"])
    currency  = "₹" if is_indian else "$"

    action_icons = {
        "BUY CE": "🟢", "BUY PE": "🔴",
        "BUY CALL": "🟢", "BUY PUT": "🔴",
        "NO ENTRY": "🟡", "WAIT": "⚪"
    }
    icon = action_icons.get(action, "⚪")

    regime_icons = {"TRENDING": "✅", "CHOPPY": "⚠️", "NEUTRAL": "➖"}
    regime_icon  = regime_icons.get(market, "")

    chg_icon = "📈" if not str(change).startswith("-") else "📉"

    return (
        f"📊 <b>{ticker}  Signal</b>  |  {now}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"💰 Close     : <b>{currency}{close_p}</b>\n"
        f"{chg_icon} Change    : <b>{change} ({changepct}%)</b>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"{regime_icon} Market    : <b>{market}</b>\n"
        f"🧭 Direction : <b>{direction}</b>\n"
        f"⚡ Intensity  : <b>{intensity}</b>\n"
        f"{icon} Action    : <b>{action}</b>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"ADX  : {adx} \n"
        f"Chop : {chop}\n"
        f"ATR  : {atr} \n"
        f"Prev close : {prevclose}\n"
        f"━━━━━━━━━━━━━━━"
    )


@app.route("/webhook", methods=["POST"])
def webhook_nifty():
    try:
        data = request.get_json(force=True)
        send_telegram(build_message(data))
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/webhook/crude", methods=["POST"])
def webhook_crude():
    try:
        data = request.get_json(force=True)
        send_telegram(build_message(data))
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/test", methods=["GET"])
def test_nifty():
    sample = {
        "ticker": "NIFTY", "close": "24385.50",
        "market": "TRENDING", "direction": "BULLISH", "intensity": "STRONG",
        "action": "BUY CE", "adx": "28.4", "chop": "31.2",
        "atr": "118", "lots": "1", "prevclose": "ABOVE"
    }
    send_telegram(build_message(sample))
    return jsonify({"status": "test sent"}), 200


@app.route("/test/crude", methods=["GET"])
def test_crude():
    sample = {
        "ticker": "CRUDEOIL1!", "close": "8675", "change": "+124", "changepct": "+1.45",
        "market": "TRENDING", "direction": "BULLISH", "intensity": "STRONG",
        "action": "BUY CALL", "adx": "29.1", "chop": "31.2",
        "atr": "65", "lots": "1", "riskperlot": "4550",
        "sl": "6000", "prevclose": "ABOVE"
    }
    send_telegram(build_message(sample))
    return jsonify({"status": "crude test sent"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
