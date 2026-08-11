# Finance Strip API

Tiny API that returns **Nifty, Sensex, Gold, and Silver** in one clean JSON response,
for use in the CGL Focus new-tab extension. Data via Yahoo Finance. HTTPS + CORS enabled.

## What it returns

`GET /` →

```json
{
  "success": true,
  "nifty":  { "value": 24500.1, "change_pct": 0.42 },
  "sensex": { "value": 80200.5, "change_pct": 0.38 },
  "gold":   { "value": 74500,   "unit": "INR/10g", "change_pct": -0.15 },
  "silver": { "value": 92000,   "unit": "INR/kg",  "change_pct": 0.22 },
  "usdinr": 83.2
}
```

Gold/silver are international spot (futures) converted to INR via live USD-INR.
Note: these are *international* metal prices in INR, not IBJA retail rates — close, but
a jeweller's rate includes GST + making charges.

## Deploy to Vercel (2 minutes, free)

1. Put this folder in a GitHub repo (or upload it).
2. Go to vercel.com → Add New → Project → import that repo.
3. Framework preset: **Other**. Leave everything default. Click **Deploy**.
4. When it finishes you get a URL like `https://your-project.vercel.app`.
5. Open that URL in a browser — you should see the JSON above.
6. Paste that URL into the extension: Settings → General → Finance strip → API URL.

No API key, no config. Vercel runs `api/index.py` as a Python serverless function.

## Notes

- Markets are closed on weekends/holidays — Yahoo returns the last close then.
- Yahoo is an unofficial source; if it ever changes, this may need an update.
- The extension caches results (a few minutes), so it won't hammer the endpoint.
