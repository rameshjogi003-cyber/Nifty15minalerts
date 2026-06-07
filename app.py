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


# ─────────────────────────────────────────────────────────────────────────────
# CHANNEL STATUS HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def dc_icon(status):
    """Donchian Channel breakout icon."""
    if "BULL" in str(status):  return "🔵▲"
    if "BEAR" in str(status):  return "🔵▼"
    return "🔵–"


def kc_icon(status):
    """Keltner Channel position icon."""
    if "ABOVE" in str(status): return "🟦▲"
    if "BELOW" in str(status): return "🟦▼"
    return "🟦–"


def lr_icon(status):
    """Linear Regression slope icon."""
    if "UP" in str(status):    return "📐↗"
    if "DN" in str(status):    return "📐↘"
    return "📐–"


def squeeze_icon(status):
    """Squeeze state icon."""
    s = str(status)
    if "FIRE" in s or "🔥" in s: return "🔥"
    if "ON"   in s or "⚡" in s: return "⚡"
    return "🌀"


def sr_icon(status):
    """S/R box break icon."""
    if "RES BREAK" in str(status): return "📦▲"
    if "SUP BREAK" in str(status): return "📦▼"
    return "📦–"


def pdhl_icon(status):
    """Prior-day H/L break icon."""
    if "PDH" in str(status): return "📅▲"
    if "PDL" in str(status): return "📅▼"
    return "📅–"


# ─────────────────────────────────────────────────────────────────────────────
# v6 INTRADAY MESSAGE BUILDER
# ─────────────────────────────────────────────────────────────────────────────

def build_intraday_message(d):
    ticker    = d.get("ticker",    "UNKNOWN")
    cur       = currency_for(ticker)
    close_p   = d.get("close",    "N/A")
    action    = d.get("action",   "N/A")
    direction = d.get("direction","N/A")
    intensity = d.get("intensity","N/A")

    # ── ORB ──────────────────────────────────────────────────────────────────
    orb   = d.get("orb",     "N/A")
    orb_h = d.get("orbhigh", "N/A")
    orb_l = d.get("orblow",  "N/A")

    # ── EXISTING INDICATORS ──────────────────────────────────────────────────
    vwap     = d.get("vwap",     "N/A")
    vwap_pos = d.get("vwap_pos", "N/A")
    adx      = d.get("adx",     "N/A")
    adx_rising = d.get("adx_rising", "N/A")
    chop     = d.get("chop",    "N/A")
    rsi      = d.get("rsi",     "N/A")
    score    = d.get("score",   "N/A")
    atr      = d.get("atr",     "N/A")
    lots     = d.get("lots",    "N/A")
    sl       = d.get("sl",      "N/A")

    # EMA — escape < > for Telegram HTML
    ema9_v  = d.get("ema9",  "N/A")
    ema24_v = d.get("ema24", "N/A")
    ema39_v = d.get("ema39", "N/A")

    # ── TRAIL / STOP ─────────────────────────────────────────────────────────
    trail_hit    = d.get("trail_hit",   "NO")
    trail_peak   = d.get("trail_peak",  "N/A")
    stop_dist    = d.get("stop_dist",   "N/A")
    vol_factor   = d.get("volatility_factor", "N/A")
    atr_ratio    = d.get("atr_ratio",   "N/A")
    stop_line    = d.get("stop_line",   "N/A")
    breakeven    = d.get("breakeven",   "N/A")
    stop_reason  = d.get("stop_reason","N/A")
    trail_locked = d.get("trail_dist_locked",  "N/A")
    trail_current= d.get("trail_dist_current", "N/A")
    trail_floor  = d.get("trail_min_floor",    "N/A")
    prem_risk    = d.get("riskperlot",  "N/A")   # kept for risk display
    chop_factor  = d.get("chop_factor", "N/A")

    # ── NEW v6: CHANNEL FIELDS ────────────────────────────────────────────────
    dc_status = d.get("dc_status", "N/A")
    dc_upper  = d.get("dc_upper",  "N/A")
    dc_lower  = d.get("dc_lower",  "N/A")

    kc_status = d.get("kc_status", "N/A")
    kc_upper  = d.get("kc_upper",  "N/A")
    kc_lower  = d.get("kc_lower",  "N/A")

    lr_status = d.get("lr_status", "N/A")
    lr_slope  = d.get("lr_slope",  "N/A")
    lr_upper  = d.get("lr_upper",  "N/A")
    lr_lower  = d.get("lr_lower",  "N/A")

    squeeze   = d.get("squeeze",   "N/A")

    # ── NEW v6: BOX / RANGE FIELDS ────────────────────────────────────────────
    sr_status = d.get("sr_status",   "N/A")
    pdh       = d.get("pdh",         "N/A")
    pdl       = d.get("pdl",         "N/A")
    pdhl_status = d.get("pdhl_status","N/A")

    # ─────────────────────────────────────────────────────────────────────────
    ist = pytz.timezone("Asia/Kolkata")
    now = datetime.now(ist).strftime("%H:%M IST, %d %b %Y")

    # ── ACTION icon ───────────────────────────────────────────────────────────
    action_icons = {
        "BUY CE": "🟢", "BUY CALL": "🟢",
        "BUY PE": "🔴", "BUY PUT":  "🔴",
        "NO ENTRY — FLAT":   "⚪", "NO ENTRY — CHOPPY": "⚠️",
        "NO ENTRY — SPIKE":  "⚡", "WAIT":              "⚪",
        "WAIT — OR FORMING": "🟡", "TIME OVER — EXIT":  "🔔",
        "TRAIL SL — EXIT":   "🛑", "MARKET CLOSED":     "🔒",
    }
    icon     = action_icons.get(action, "⚪")
    orb_icon = "🚀" if orb == "BULL BREAK" else "💥" if orb == "BEAR BREAK" else "📦"

    # ── ADX display ───────────────────────────────────────────────────────────
    adx_str = f"{adx} {'▲' if adx_rising == 'YES' else '▼' if adx_rising == 'NO' else ''}".strip()

    # ── Chop label ────────────────────────────────────────────────────────────
    try:
        cv = float(chop)
        chop_label = "TRENDING" if cv < 38.2 else "CHOPPY" if cv > 61.8 else "MIXED"
    except (ValueError, TypeError):
        chop_label = ""
    chop_disp = f"{chop} ({chop_label})" if chop_label else f"{chop}"

    # ── VWAP display ──────────────────────────────────────────────────────────
    vwap_display = f"{vwap} ({vwap_pos})" if is_active(vwap_pos) else f"{vwap}"

    # ── EMA stack ranking ────────────────────────────────────────────────────
    ema_labels = [
        ("CMP", float(close_p) if close_p != "N/A" else 0),
        ("E9",  float(ema9_v)  if ema9_v  != "N/A" else 0),
        ("E24", float(ema24_v) if ema24_v != "N/A" else 0),
        ("E39", float(ema39_v) if ema39_v != "N/A" else 0),
    ]
    ema_sorted = sorted(ema_labels, key=lambda x: x[1], reverse=True)
    ema_rank   = " ﹥ ".join(f"{lbl}:{val:.1f}" for lbl, val in ema_sorted)
    # Derive EMA trend from sorted order
    vals = [v for _, v in ema_sorted]
    cmp_idx = next((i for i, (l, _) in enumerate(ema_sorted) if l == "CMP"), -1)
    e9_idx  = next((i for i, (l, _) in enumerate(ema_sorted) if l == "E9"),  -1)
    e24_idx = next((i for i, (l, _) in enumerate(ema_sorted) if l == "E24"), -1)
    e39_idx = next((i for i, (l, _) in enumerate(ema_sorted) if l == "E39"), -1)
    if e9_idx < e24_idx < e39_idx:
        ema_trend = "BULL STACK"; ema_icon = "🟢"
    elif e9_idx > e24_idx > e39_idx:
        ema_trend = "BEAR STACK"; ema_icon = "🔴"
    else:
        ema_trend = "MIXED";      ema_icon = "🟡"

    # ── Trail / stop block ───────────────────────────────────────────────────
    if str(trail_hit).startswith("YES"):
        why = f" ({stop_reason})" if is_active(stop_reason) else ""
        trail_block = f"🛑 <b>STOP HIT{why} — EXIT ALL LOTS NOW</b>\n"
    elif is_active(stop_line) and is_active(trail_peak):
        be   = " 🔒BE" if str(breakeven).upper() == "ARMED" else ""
        vf   = f" vol×{vol_factor}" if is_active(vol_factor) else ""
        cf   = f" chop×{chop_factor}" if is_active(chop_factor) else ""
        dist = stop_dist if is_active(stop_dist) else trail_locked
        risk = f" | ≈{cur}{prem_risk}/lot" if is_active(prem_risk) else ""
        trail_block = (
            f"📍 Stop @ <b>{stop_line}</b>{be}  (dist {dist} pts{vf}{cf})\n"
            f"   peak {trail_peak}{risk}\n"
        )
    elif is_active(trail_current):
        floor = f" (floor {trail_floor})" if is_active(trail_floor) else ""
        trail_block = f"📐 Stop (idle): {trail_current} pts{floor}\n"
    else:
        trail_block = ""

    # ── NEW v6: Channel block ─────────────────────────────────────────────────
    # Donchian
    dc_range = ""
    if is_active(dc_upper) and is_active(dc_lower):
        dc_range = f"  [{cur}{dc_lower} – {cur}{dc_upper}]"
    dc_line = f"{dc_icon(dc_status)} DC  : <b>{dc_status}</b>{dc_range}\n"

    # Keltner
    kc_range = ""
    if is_active(kc_upper) and is_active(kc_lower):
        kc_range = f"  [{cur}{kc_lower} – {cur}{kc_upper}]"
    kc_line = f"{kc_icon(kc_status)} KC  : <b>{kc_status}</b>{kc_range}\n"

    # Linear Regression
    lr_slope_str = f"  slope {lr_slope}" if is_active(lr_slope) else ""
    lr_range = ""
    if is_active(lr_upper) and is_active(lr_lower):
        lr_range = f"  [{cur}{lr_lower} – {cur}{lr_upper}]"
    lr_line = f"{lr_icon(lr_status)} LR  : <b>{lr_status}</b>{lr_slope_str}{lr_range}\n"

    # Squeeze
    sqz_line = f"{squeeze_icon(squeeze)} SQZ : <b>{squeeze}</b>\n"

    channel_block = (
        f"━━━━━\n"
        f"📡 <b>CHANNELS</b>\n"
        f"{dc_line}"
        f"{kc_line}"
        f"{lr_line}"
        f"{sqz_line}"
    )

    # ── NEW v6: Box / Range block ─────────────────────────────────────────────
    pdhl_range = ""
    if is_active(pdh) and is_active(pdl):
        pdhl_range = f"  H:{cur}{pdh}  L:{cur}{pdl}"
    sr_line   = f"{sr_icon(sr_status)} S/R  : <b>{sr_status}</b>\n"
    pdhl_line = f"{pdhl_icon(pdhl_status)} PDH/L: <b>{pdhl_status}</b>{pdhl_range}\n"

    box_block = (
        f"━━━━━\n"
        f"📦 <b>BOX / RANGE</b>\n"
        f"{sr_line}"
        f"{pdhl_line}"
    )

    # ── ASSEMBLE ─────────────────────────────────────────────────────────────
    return (
        f"⚡ <b>{ticker} INTRADAY v6</b>  |  {now}\n"
        f"━━━━━\n"
        f"💰 Close     : <b>{cur}{close_p}</b>\n"
        f"{orb_icon} ORB       : <b>{orb}</b>\n"
        f"   H: {orb_h}  |  L: {orb_l}\n"
        f"━━━━━\n"
        f"🧭 Direction : <b>{direction}</b>\n"
        f"⚡ Intensity  : <b>{intensity}</b>\n"
        f"{icon} Action    : <b>{action}</b>\n"
        f"   Score: {score}\n"
        f"━━━━━\n"
        f"VWAP : {vwap_display}\n"
        f"ADX  : {adx_str}\n"
        f"RSI  : {rsi}\n"
        f"Chop : {chop_disp}\n"
        f"ATR  : {atr}\n"
        f"{ema_icon} EMA  : {ema_trend}\n"
        f"   {ema_rank}\n"
        f"{channel_block}"
        f"{box_block}"
        f"━━━━━\n"
        f"{trail_block}"
     
    )


# ─────────────────────────────────────────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────────────────────────────────────────

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
    """Full v6 test with channel + box fields."""
    sample = {
        # base
        "ticker": "NIFTY", "close": "23335.85",
        "action": "BUY CALL", "direction": "BULLISH",
        "intensity": "STRONG", "score": "11B/3Be/16",
        # ORB
        "orb": "BULL BREAK", "orbhigh": "23495.1", "orblow": "23300.1",
        # indicators
        "vwap": "23290.2", "vwap_pos": "ABOVE",
        "adx": "32.1", "adx_rising": "YES", "chop": "39.0",
        "rsi": "61.4", "atr": "28.4",
        "ema9": "23350.1", "ema24": "23300.5", "ema39": "23260.2",
        # trail
        "trail_hit": "NO", "trail_peak": "23400",
        "stop_line": "23315", "stop_dist": "85",
        "trail_dist_locked": "85", "trail_dist_current": "80.2",
        "trail_min_floor": "30", "volatility_factor": "1.12",
        "atr_ratio": "1.18", "breakeven": "ARMED",
        "stop_reason": "TRAIL_ACTIVE", "riskperlot": "4550",
        "chop_factor": "0.88", "sl": "6000",
        "lots": "3",
        # NEW v6: channels
        "dc_status": "BULL BREAK ▲", "dc_upper": "23510", "dc_lower": "23100",
        "kc_status": "ABOVE UPPER",  "kc_upper": "23480", "kc_lower": "23180",
        "lr_status": "SLOPE UP ↗",   "lr_slope": "4.25",
        "lr_upper":  "23520",        "lr_lower": "23200",
        "squeeze":   "🔥 FIRED!",
        # NEW v6: boxes
        "sr_status":   "RES BREAK ▲",
        "pdh": "23490", "pdl": "23180", "pdhl_status": "ABOVE PDH ▲",
    }
    send_telegram(build_intraday_message(sample))
    return jsonify({"status": "intraday v6 test sent"}), 200


@app.route("/webhook/debug", methods=["POST"])
def webhook_debug():
    data = request.get_json(force=True)
    print(f"RAW PAYLOAD: {data}")
    send_telegram(f"<b>DEBUG PAYLOAD:</b>\n<code>{str(data)}</code>")
    return jsonify({"status": "ok"}), 200


# ─────────────────────────────────────────────────────────────────────────────
# LEGACY ROUTES (unchanged)
# ─────────────────────────────────────────────────────────────────────────────

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
    icon        = action_icons.get(action, "⚪")
    regime_icon = {"TRENDING": "✅", "CHOPPY": "⚠️", "NEUTRAL": "➖"}.get(market, "")
    chg_icon    = "📈" if not str(change).startswith("-") else "📉"

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
