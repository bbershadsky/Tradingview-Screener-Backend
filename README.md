## Tradingview Screener - get the best value assets using a serverless Python function on Appwrite

[LIVE DEMO](https://fbtv-3.vercel.app/)

# Setting up Appwrite Backend

Create a storage bucket and copy its ID to an `.env` file

```bash
appwrite login
? Enter your email 
? Enter your password ********************
✓ Success: Successfully signed in as b.boriz@gmail.com
♥ Hint: Next you can create or link to your project using 'appwrite init project'
```

## Deployment

Make sure your `appwrite.json` is set up correctly and you are logged into your server.

`appwrite push functions`

Add your .env vars to Appwrite Console Settings and redeploy

Test it and take note of the URL, use this as the webhook for the frontend function

Example with url params: http://cloud.appwrite.io/v1/PROJECT?volume=100000&market_cap_calc=100000000&perf_ytd=30


## ⚙️ Configuration

| Setting           | Value                             |
| ----------------- | --------------------------------- |
| Runtime           | Python (3.12)                      |
| Entrypoint        | `src/main.py`                     |
| Build Commands    | `pip install -r requirements.txt` |
| Permissions       | `any`                             |
| Timeout (Seconds) | 15                                |

## Other utilities

`functions/costco_price` - Costco Online price scraper for Elk built with Appwrite BaaS POC built using bs4 and regex
`generate_json.py` - alpha version