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
    # range=1d gives meta.chartPreviousClose = the prior trading day's close,
    # which is exactly the "Previous Close" shown on quote pages.
    url = CHART_BASE + urllib.parse.quote(sym) + "?range=1d&interval=1d"
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
    prev = meta.get("chartPreviousClose") or meta.get("previousClose")
    if price is None:
        # fall back to last close in the series
        try:
            closes = [c for c in result["indicators"]["quote"][0]["close"] if c is not None]
            price = closes[-1] if closes else None
        except Exception:
            pass
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
