from http.server import BaseHTTPRequestHandler
import json
import urllib.request
import urllib.error
import urllib.parse

# Yahoo Finance symbols:
#   ^NSEI  = Nifty 50
#   ^BSESN = Sensex
#   GC=F   = Gold futures (USD/oz)
#   SI=F   = Silver futures (USD/oz)
#   INR=X  = USD to INR
SYMBOLS = {
    "nifty": "^NSEI",
    "sensex": "^BSESN",
    "gold": "GOLDBEES.NS",
    "silver": "SILVERBEES.NS",
    "usdinr": "USDINR=X",
}


# The v8 chart endpoint does NOT require a crumb/cookie, unlike v7/quote.
CHART_BASE = "https://query1.finance.yahoo.com/v8/finance/chart/"


def fetch_symbol(sym):
    # 5d/1d gives a short series of daily closes; use last two for true 1-day change
    url = CHART_BASE + urllib.parse.quote(sym) + "?range=5d&interval=1d"
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode())
    result = data["chart"]["result"][0]
    meta = result.get("meta", {})
    price = meta.get("regularMarketPrice")

    # Build the close series, dropping nulls (holidays/gaps)
    closes = []
    try:
        raw = result["indicators"]["quote"][0]["close"]
        closes = [c for c in raw if c is not None]
    except Exception:
        closes = []

    prev = None
    if price is not None and closes:
        # if the last close equals the live price, the prior day is closes[-2]
        if abs(closes[-1] - price) < 1e-6 and len(closes) >= 2:
            prev = closes[-2]
        else:
            prev = closes[-1]
    if prev is None:
        prev = meta.get("previousClose") or meta.get("chartPreviousClose")
    if price is None:
        price = closes[-1] if closes else None

    change_pct = None
    if price is not None and prev:
        change_pct = round((price - prev) / prev * 100, 2)
    return price, change_pct


def build_payload():
    vals = {}
    for key, sym in SYMBOLS.items():
        try:
            vals[key] = fetch_symbol(sym)
        except Exception:
            vals[key] = (None, None)

    return {
        "success": True,
        "nifty": {"value": vals["nifty"][0], "change_pct": vals["nifty"][1]},
        "sensex": {"value": vals["sensex"][0], "change_pct": vals["sensex"][1]},
        "gold": {"value": vals["gold"][0], "unit": "GoldBeES", "change_pct": vals["gold"][1]},
        "silver": {"value": vals["silver"][0], "unit": "SilverBeES", "change_pct": vals["silver"][1]},
        "usdinr": {"value": vals["usdinr"][0], "change_pct": vals["usdinr"][1]},
    }


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            payload = build_payload()
            status = 200
        except Exception as e:
            payload = {"success": False, "error": str(e)}
            status = 502
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "public, max-age=300")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.end_headers()
