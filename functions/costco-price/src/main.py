import requests
from bs4 import BeautifulSoup
import sqlite3
import re
import logging
import time
import urllib3
import http.client as http_client
import traceback

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Optionally enable HTTP debugging if needed
# http_client.HTTPConnection.debuglevel = 1

# URL of the product page
URL = 'https://www.costco.ca/northfork-meats-elk-ground-meat-454-g-1-lb-x-10-pack.product.100571433.html'

def main(context):
    """
    Appwrite Cloud Function entry point.

    context.res => The response object.
    context.log => Function to log messages.
    """

    context.log("Starting Appwrite function...")

    # Prepare default response object
    context.res = {
        "statusCode": 200,
        "json": {}
    }

    # We’ll store messages or final results here:
    response_data = {
        "message": "",
        "price": None,
        "product_id": None
    }

    # 1. Fetch the webpage
    html_content = None
    try:
        context.log(f"Attempting to fetch the page: {URL}")
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.google.com",
            "Accept-Encoding": "gzip, deflate, br"
        }
        response = requests.get(URL, headers=headers, timeout=10, verify=False)
        response.raise_for_status()
        html_content = response.text
        context.log("Successfully fetched page content.")
    except requests.exceptions.Timeout as te:
        error_msg = f"Timeout error while fetching the page: {te}"
        context.log(error_msg)
        response_data["message"] = error_msg
        context.res["statusCode"] = 504  # Gateway Timeout
    except Exception as e:
        error_msg = f"Error fetching the page: {e}"
        context.log(error_msg)
        context.log(traceback.format_exc())
        response_data["message"] = error_msg
        context.res["statusCode"] = 500

    # If we couldn't fetch the page, return early
    if not html_content:
        context.log("No HTML content received; returning early.")
        context.res["json"] = response_data
        return context.res

    # 2. Parse the page with BeautifulSoup
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        context.log("Successfully parsed HTML content with BeautifulSoup.")
    except Exception as e:
        error_msg = f"Error parsing HTML content: {e}"
        context.log(error_msg)
        context.log(traceback.format_exc())
        response_data["message"] = error_msg
        context.res["statusCode"] = 500
        context.res["json"] = response_data
        return context.res

    # 3. Extract adobeProductData from scripts
    adobe_data_script = None
    try:
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string and 'var adobeProductData =' in script.string:
                adobe_data_script = script.string
                break
        
        if not adobe_data_script:
            raise ValueError("Could not find the adobeProductData script.")
        context.log("Found the adobeProductData script.")
    except Exception as e:
        error_msg = f"Error locating the adobeProductData script: {e}"
        context.log(error_msg)
        context.log(traceback.format_exc())
        response_data["message"] = error_msg
        context.res["statusCode"] = 500
        context.res["json"] = response_data
        return context.res

    # 4. Extract price and SKU with regex
    current_price = None
    product_id = None
    try:
        price_match = re.search(r'priceTotal:\s*initialize\(([^)]+)\)', adobe_data_script)
        if price_match:
            price_str = price_match.group(1).strip('\'"')
            current_price = float(price_str)
            context.log(f"Extracted price: {current_price}")
        else:
            raise ValueError("Could not extract priceTotal.")

        sku_match = re.search(r'SKU:\s*initialize\(([^)]+)\)', adobe_data_script)
        if sku_match:
            product_id = sku_match.group(1).strip('\'"')
            context.log(f"Extracted SKU: {product_id}")
        else:
            raise ValueError("Could not extract SKU.")
    except Exception as e:
        error_msg = f"Error parsing adobeProductData: {e}"
        context.log(error_msg)
        context.log(traceback.format_exc())
        response_data["message"] = error_msg
        context.res["statusCode"] = 500
        context.res["json"] = response_data
        return context.res

    # Update the response data with extracted info
    response_data["price"] = current_price
    response_data["product_id"] = product_id

    # 5. Compare prices using sqlite database
    try:
        conn = sqlite3.connect('prices.db')
        cursor = conn.cursor()
        context.log("Connected to SQLite database successfully.")

        # Create table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS product_prices (
                product_id TEXT PRIMARY KEY,
                price REAL,
                timestamp INTEGER
            )
        ''')
        conn.commit()
        context.log("Checked/Created the product_prices table.")

        # Get previous price
        cursor.execute('SELECT price FROM product_prices WHERE product_id = ?', (product_id,))
        row = cursor.fetchone()

        if row:
            previous_price = row[0]
            context.log(f"Previous price for product {product_id} is {previous_price}")
            if current_price < previous_price:
                response_data["message"] = "The product is on sale!"
            elif current_price == previous_price:
                response_data["message"] = "The price has not changed."
            else:
                response_data["message"] = "The price has increased."
        else:
            response_data["message"] = "No previous price data to compare."

        # Update database with the current price
        current_timestamp = int(time.time())
        cursor.execute('''
            INSERT OR REPLACE INTO product_prices (product_id, price, timestamp)
            VALUES (?, ?, ?)
        ''', (product_id, current_price, current_timestamp))
        conn.commit()
        context.log("Database updated with the current price.")

        conn.close()
        context.log("Closed SQLite connection.")
    except Exception as e:
        error_msg = f"Error comparing/updating prices in database: {e}"
        context.log(error_msg)
        context.log(traceback.format_exc())
        response_data["message"] = error_msg
        context.res["statusCode"] = 500
        context.res["json"] = response_data
        return context.res

    # Everything succeeded
    context.log("Function completed successfully.")
    context.res["json"] = response_data
    return context.res
