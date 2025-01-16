from flask import Flask, request, jsonify
import pandas as pd
import json

# tradingview_screener library
from tradingview_screener import Query, col

app = Flask(__name__)

@app.route("/tradingview", methods=["POST"])
def tradingview_data():
    """
    A Flask endpoint that:
      1. Receives POST parameters to filter the query.
      2. Runs the TradingView screener with those parameters.
      3. Converts results to JSON (multi-line).
      4. Removes lines 2–6 and the last 2 lines (1-based indexing).
      5. Returns the cleaned JSON object.
    """
    # Get POST data; if not provided, use defaults
    data = request.get_json(silent=True) or {}
    min_volume = data.get("min_volume", 500000)
    max_market_cap = data.get("max_market_cap", 100000000)
    min_perf_ytd = data.get("min_perf_ytd", 30)

    # 1. Run the TradingView query
    res = (
        Query()
        .select(
            "name",
            "volume",
            "market_cap_calc",
            "Perf.YTD",
            "Perf.W",
            "Perf.1M",
            "Perf.3M",
            "Perf.6M",
            "Perf.Y",
            "Perf.All",
            "change",
            "Value.Traded"
        )
        .where(
            col("volume") > min_volume,
            col("market_cap_calc") < max_market_cap,
            col("Perf.YTD") > min_perf_ytd
        )
        .order_by("volume", ascending=False)
        .limit(100)
        .set_markets("crypto")
        .get_scanner_data()
    )

    df = pd.DataFrame(res)

    # 2. Convert to multi-line JSON string
    json_str = df.to_json(orient="records", indent=2)
    lines = json_str.splitlines()

    # 3. Remove lines 2–6 (1-based indexing: lines[1] through lines[5])
    #    keep lines[:1] (line 1) and then lines[6:] (line 7 onward)
    lines_to_keep = lines[:1] + lines[6:]

    # 4. Remove the last 2 lines
    lines_to_keep = lines_to_keep[:-2]

    # Join the remaining lines back together
    cleaned_json_str = "\n".join(lines_to_keep)

    # 5. Convert cleaned string back to a Python object (so we return valid JSON)
    #    - if the removal breaks JSON validity, you’ll need to adjust which lines to remove.
    cleaned_obj = json.loads(cleaned_json_str)

    # 6. Return as raw JSON
    return jsonify(cleaned_obj)

if __name__ == "__main__":
    # For local testing:
    app.run(host="0.0.0.0", port=8000, debug=True)
