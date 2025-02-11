import pandas as pd
from tradingview_screener import Query, col

res = (
    Query()
    .select(
        'name',
        'volume',
        'market_cap_calc',
        'Perf.YTD',
        'Perf.W',
        'Perf.1M',
        'Perf.3M',
        'Perf.6M',
        'Perf.Y',
        'Perf.All',
        'change',
        'Value.Traded'
    )
    .where(
        col('volume') > 500_000,
        col('market_cap_calc') < 100_000_000,
        col('Perf.YTD') > 30
    )
    .order_by('volume', ascending=False)
    .limit(250)
    .set_markets('crypto')
    .get_scanner_data()
)

df = pd.DataFrame(res)
print(df)  # Prints the DataFrame in console


json_file = "tradingview_data.json"
# Writes JSON to file as an array of dicts
df.to_json(json_file, orient="records", indent=2)
with open(json_file, "r", encoding="utf-8") as f:
    lines = f.readlines()

# 2. Remove lines 2–6 (1-based indexing)
#    - lines[0] is line 1
#    - lines[1] through lines[5] correspond to lines 2–6
#    So, keep lines[:1] (the first line) and then lines[6:] (line 7 onward).
lines_to_keep = lines[:1] + lines[6:]

# 3. Remove the last 2 lines
#    - lines_to_keep[:-2] drops the final two lines
lines_to_keep = lines_to_keep[:-2]

# 4. Overwrite the file with the remaining lines
with open(json_file, "w", encoding="utf-8") as f:
    f.writelines(lines_to_keep)
    context.log(lines_to_keep)