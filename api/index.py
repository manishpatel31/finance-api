from http.server import BaseHTTPRequestHandler
import json
import urllib.request
import urllib.error
import urllib.parse

# Yahoo Finance quote endpoint. Symbols:
#   ^NSEI  = Nifty 50
#   ^BSESN = Sensex
#   GC=F   = Gold futures (USD/oz)
#   SI=F   = Silver futures (USD/oz)
#   USDINR=X = USD to INR (to convert metals to INR)
SYMBOLS = ["^NSEI", "^BSESN", "GC=F", "SI=F", "USDINR=X"]

YF_URL = "https://query1.finance.yahoo.com/v7/finance/quote?symbols=" + ",".join(
    urllib.parse.quote(s) for s in SYMBOLS
)

# grams per troy ounce (to show gold/silver per gram in INR)
GRAMS_PER_OZ = 31.1035


def fetch_yahoo():
    req = urllib.request.Request(
        YF_URL,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode())


def build_payload():
    raw = fetch_yahoo()
    quotes = {}
    for q in raw.get("quoteResponse", {}).get("result", []):
        quotes[q.get("symbol")] = q

    def price(sym):
        q = quotes.get(sym, {})
        return q.get("regularMarketPrice")

    def change_pct(sym):
        q = quotes.get(sym, {})
        return q.get("regularMarketChangePercent")

    usdinr = price("USDINR=X") or 0

    gold_oz_usd = price("GC=F")
    silver_oz_usd = price("SI=F")
    # convert to INR per 10 grams (common Indian quote unit)
    gold_10g_inr = None
    silver_kg_inr = None
    if gold_oz_usd and usdinr:
        gold_10g_inr = round(gold_oz_usd / GRAMS_PER_OZ * usdinr * 10, 0)
    if silver_oz_usd and usdinr:
        silver_kg_inr = round(silver_oz_usd / GRAMS_PER_OZ * usdinr * 1000, 0)

    return {
        "success": True,
        "nifty": {"value": price("^NSEI"), "change_pct": change_pct("^NSEI")},
        "sensex": {"value": price("^BSESN"), "change_pct": change_pct("^BSESN")},
        "gold": {
            "value": gold_10g_inr, "unit": "INR/10g",
            "change_pct": change_pct("GC=F"),
        },
        "silver": {
            "value": silver_kg_inr, "unit": "INR/kg",
            "change_pct": change_pct("SI=F"),
        },
        "usdinr": usdinr,
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
        # CORS so the browser extension can read it
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "public, max-age=300")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.end_headers()
