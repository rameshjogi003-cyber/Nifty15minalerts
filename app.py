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


INDIAN_TOKENS = ("NIFTY", "BANKNIFTY", "FINNIFTY", "SENSEX", "BANKEX",
                 "MCX", "CRUDEOIL", "GOLD", "GOLDM", "SILVER", "SILVERM",
                 "NSE", "BSE", "NATURALGAS", "COPPER", "ZINC")


def currency_for(ticker):
    return "₹" if any(tok in ticker.upper() for tok in INDIAN_TOKENS) else "$"


def is_active(value):
    return value not in ("N/A", "NA", "", None)


def build_intraday_message(d):
    ticker     = d.get("ticker",      "UNKNOWN")
    cur        = currency_for(ticker)
    close_p    = d.get("close",       "N/A")
    action     = d.get("action",      "N/A")
    direction  = d.get("direction",   "N/A")
    intensity  = d.get("intensity",   "N/A")

    orb        = d.get("orb",         "N/A")
    orb_h      = d.get("orbhigh",     "N/A")
    orb_l      = d.get("orblow",      "N/A")

    vwap       = d.get("vwap",        "N/A")
    vwap_pos   = d.get("vwap_pos",    "N/A")

    adx        = d.get("adx",         "N/A")
    adx_rising = d.get("adx_rising",  "N/A")
    chop       = d.get("chop",        "N/A")
    rsi        = d.get("rsi",         "N/A")
    score      = d.get("score",       "N/A")

    lots       = d.get("lots",        "N/A")
    rpl        = d.get("riskperlot",  "N/A")
    sl         = d.get("sl",          "N/A")
    atr        = d.get("atr",         "N/A")

    trail_locked  = d.get("trail_dist_locked",  "N/A")
    trail_current = d.get("trail_dist_current", "N/A")
    trail_floor   = d.get("trail_min_floor",    "N/A")
    trail_peak    = d.get("trail_peak",         "N/A")
    vol_factor    = d.get("volatility_factor",  "N/A")
    atr_ratio     = d.get("atr_ratio",          "N/A")
    trail_hit     = d.get("trail_hit",          "NO")
    stop_line     = d.get("stop_line",          "N/A")
    stop_dist     = d.get("stop_dist",          "N/A")
    breakeven     = d.get("breakeven",          "N/A")
    stop_reason   = d.get("stop_reason",        "N/A")
    prem_risk     = d.get("prem_risk_per_lot",  "N/A")
    chop_factor   = d.get("chop_factor",        "N/A")

    # EMA fields — replace < and > with unicode lookalikes to avoid Telegram HTML parse errors
    ema_rel  = d.get("ema_rel", "N/A").replace("<", "﹤").replace(">", "﹥")
    ema9_v   = d.get("ema9",    "N/A")
    ema24_v  = d.get("ema24",   "N/A")
    ema39_v  = d.get("ema39",   "N/A")

    ist = pytz.timezone("Asia/Kolkata")
    now = datetime.now(ist).strftime("%H:%M IST, %d %b %Y")

    action_icons = {
        "BUY CE": "🟢", "BUY CALL": "🟢",
        "BUY PE": "🔴", "BUY PUT": "🔴",
        "NO ENTRY — FLAT": "⚪", "NO ENTRY — CHOPPY": "⚠️",
        "NO ENTRY — SPIKE": "⚡", "WAIT": "⚪",
        "WAIT — OR FORMING": "🟡", "TIME OVER — EXIT": "🔔",
        "TRAIL SL — EXIT": "🛑", "MARKET CLOSED": "🔒",
    }
    icon = action_icons.get(action, "⚪")

    orb_icon = "🚀" if orb == "BULL BREAK" else "💥" if orb == "BEAR BREAK" else "📦"

    adx_str = f"{adx} {'▲' if adx_rising == 'YES' else '▼' if adx_rising == 'NO' else ''}".strip()

    try:
        cv = float(chop)
        chop_label = "TRENDING" if cv < 38.2 else "CHOPPY" if cv > 61.8 else "MIXED"
    except (ValueError, TypeError):
        chop_label = ""
    chop_disp = f"{chop} ({chop_label})" if chop_label else f"{chop}"

    vwap_display = f"{vwap} ({vwap_pos})" if is_active(vwap_pos) else f"{vwap}"

    # Emoji based on already-escaped ema_rel (uses ﹥ ﹤ now)
    ema_icon = ("🟢" if "CMP﹥E9﹥E24﹥E39" == ema_rel
                else "🔴" if "CMP﹤E9﹤E24﹤E39" == ema_rel
                else "🟠" if ema_rel.startswith("CMP﹥")
                else "🟡")

    if str(trail_hit).startswith("YES"):
        why = f" ({stop_reason})" if is_active(stop_reason) else ""
        trail_block = f"🛑 <b>STOP HIT{why} — EXIT ALL LOTS NOW</b>\n"
    elif is_active(stop_line) and is_active(trail_peak):
        be = " 🔒BE" if str(breakeven).upper() == "ARMED" else ""
        vf = f" vol×{vol_factor}" if is_active(vol_factor) else ""
        cf = f" chop×{chop_factor}" if is_active(chop_factor) else ""
        dist = f"{stop_dist}" if is_active(stop_dist) else trail_locked
        risk = f" | ≈{cur}{prem_risk}/lot" if is_active(prem_risk) else ""
        trail_block = (f"📍 Stop @ <b>{stop_line}</b>{be}  (dist {dist} pts{vf}{cf})\n"
                       f"   peak {trail_peak}{risk}\n")
    elif is_active(trail_current):
        floor = f" (floor {trail_floor})" if is_active(trail_floor) else ""
        trail_block = f"📐 Stop (idle): {trail_current} pts{floor}\n"
    else:
        trail_block = ""

    return (
        f"⚡ <b>{ticker} INTRADAY</b>  |  {now}\n"
        f"━━━━━\n"
        f"💰 Close     : <b>{cur}{close_p}</b>\n"
        f"{orb_icon} ORB       : <b>{orb}</b>\n"
        f"   H: {orb_h}  |  L: {orb_l}\n"
        f"━━━━\n"
        f"🧭 Direction : <b>{direction}</b>\n"
        f"⚡ Intensity  : <b>{intensity}</b>\n"
        f"{icon} Action    : <b>{action}</b>\n"
        f"━━━━━\n"
        f"VWAP : {vwap_display}\n"
        f"ADX  : {adx_str}\n"
        f"RSI  : {rsi}\n"
        f"Score: {score}\n"
        f"Chop : {chop_disp}\n"
        f"ATR  : {atr}\n"
        f"{ema_icon} EMA  : {ema_rel}\n"
        f"   E9:{ema9_v} | E24:{ema24_v} | E39:{ema39_v}\n"
        f"━━━━━\n"
        f"{trail_block}"
        f"📦 Lots : {lots}  |  Risk/lot : {cur}{rpl}\n"
        f"🛡 SL   : {cur}{sl}\n"
        f"━━━━━"
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
        "ticker": "NIFTY", "close": "23335.85",
        "action": "TRAIL SL — EXIT", "direction": "BEARISH",
        "intensity": "MODERATE", "orb": "BEAR BREAK",
        "orbhigh": "23495.1", "orblow": "23300.1",
        "vwap": "23390.2", "vwap_pos": "BELOW",
        "adx": "30.3", "adx_rising": "NO", "chop": "59.0",
        "rsi": "44.1", "score": "1B/4Be", "lots": "2",
        "riskperlot": "4550", "sl": "6000", "atr": "28.4",
        "atr_ratio": "1.15", "volatility_factor": "1.09",
        "trail_dist_locked": "42", "trail_dist_current": "38.5",
        "trail_min_floor": "30", "trail_peak": "23300",
        "trail_hit": "YES — EXIT",
        "ema_rel": "CMP<E9<E24<E39",
        "ema9": "23350.1", "ema24": "23400.5", "ema39": "23450.2",
    }
    send_telegram(build_intraday_message(sample))
    return jsonify({"status": "intraday test sent"}), 200


@app.route("/webhook/debug", methods=["POST"])
def webhook_debug():
    data = request.get_json(force=True)
    print(f"RAW PAYLOAD: {data}")
    send_telegram(f"<b>DEBUG PAYLOAD:</b>\n<code>{str(data)}</code>")
    return jsonify({"status": "ok"}), 200


def build_message(d):
    ticker    = d.get("ticker",    "UNKNOWN")
    cur       = currency_for(ticker)
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
    prevclose = d.get("prevclose", "N/A")

    ist = pytz.timezone("Asia/Kolkata")
    now = datetime.now(ist).strftime("%H:%M IST, %d %b %Y")

    action_icons = {
        "BUY CE": "🟢", "BUY PE": "🔴",
        "BUY CALL": "🟢", "BUY PUT": "🔴",
        "NO ENTRY": "🟡", "WAIT": "⚪",
    }
    icon = action_icons.get(action, "⚪")
    regime_icon = {"TRENDING": "✅", "CHOPPY": "⚠️", "NEUTRAL": "➖"}.get(market, "")
    chg_icon = "📈" if not str(change).startswith("-") else "📉"

    return (
        f"📊 <b>{ticker}  Signal</b>  |  {now}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"💰 Close     : <b>{cur}{close_p}</b>\n"
        f"{chg_icon} Change    : <b>{change} ({changepct}%)</b>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"{regime_icon} Market    : <b>{market}</b>\n"
        f"🧭 Direction : <b>{direction}</b>\n"
        f"⚡ Intensity  : <b>{intensity}</b>\n"
        f"{icon} Action    : <b>{action}</b>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"ADX  : {adx}\n"
        f"Chop : {chop}\n"
        f"ATR  : {atr}\n"
        f"Prev close : {prevclose}\n"
        f"━━━━━━━━━━━━━━━"
    )


@app.route("/webhook", methods=["POST"])
def webhook_nifty():
    try:
        send_telegram(build_message(request.get_json(force=True)))
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/webhook/crude", methods=["POST"])
def webhook_crude():
    try:
        send_telegram(build_message(request.get_json(force=True)))
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/test", methods=["GET"])
def test_nifty():
    sample = {
        "ticker": "NIFTY", "close": "24385.50", "change": "+120", "changepct": "+0.49",
        "market": "TRENDING", "direction": "BULLISH", "intensity": "STRONG",
        "action": "BUY CE", "adx": "28.4", "chop": "31.2",
        "atr": "118", "prevclose": "ABOVE",
    }
    send_telegram(build_message(sample))
    return jsonify({"status": "test sent"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
