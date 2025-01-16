import streamlit as st
import pandas as pd
from tradingview_screener import Query, col

def run_query(min_volume, max_market_cap, min_perf_ytd):
    """
    Execute the TradingView Screener query with dynamically supplied parameters.
    """
    query = (
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
    )
    return query.get_scanner_data()


def main():
    """
    Main Streamlit app function.
    """
    st.title("TradingView Screener: Crypto")

    # --- Approach 1: Using Streamlit's built-in widgets ---
    st.header("Filter Parameters")

    min_volume = st.number_input("Minimum Volume", value=500000, step=10000)
    max_market_cap = st.number_input("Max Market Cap", value=100000000, step=1000000)
    min_perf_ytd = st.number_input("Min Perf YTD (%)", value=30, step=1)

    if st.button("Run Query"):
        data = run_query(min_volume, max_market_cap, min_perf_ytd)
        df = pd.DataFrame(data)

        # Display as a table
        st.write("### Results")
        st.dataframe(df)

        # Display the JSON output
        st.write("### JSON Output")
        st.json(df.to_dict(orient="records"))

        # Optionally allow users to download the JSON
        json_string = df.to_json(orient="records", indent=2)
        st.download_button(
            label="Download JSON",
            data=json_string,
            file_name="tradingview_data.json",
            mime="application/json"
        )

    # --- Approach 2: Using URL Query Params (optional) ---
    # If you want to allow passing params via URL, e.g.:
    #   ?min_volume=1000000&max_market_cap=50000000&min_perf_ytd=25
    st.write("---")
    st.header("Alternatively: Load from Query Parameters")

    # Read query params
    query_params = st.experimental_get_query_params()
    # Provide defaults if they are not present
    q_min_volume = int(query_params.get("min_volume", [500000])[0])
    q_max_market_cap = int(query_params.get("max_market_cap", [100000000])[0])
    q_min_perf_ytd = int(query_params.get("min_perf_ytd", [30])[0])

    st.write(f"URL param `min_volume`: **{q_min_volume}**")
    st.write(f"URL param `max_market_cap`: **{q_max_market_cap}**")
    st.write(f"URL param `min_perf_ytd`: **{q_min_perf_ytd}**")

    if st.button("Run Query from URL Params"):
        data = run_query(q_min_volume, q_max_market_cap, q_min_perf_ytd)
        df = pd.DataFrame(data)

        st.write("### Results (From URL Params)")
        st.dataframe(df)

        st.write("### JSON Output")
        st.json(df.to_dict(orient="records"))


if __name__ == "__main__":
    main()
