import os
import pandas as pd
import datetime
from dotenv import load_dotenv
from tradingview_screener import Query, col
from appwrite.client import Client
from appwrite.services.storage import Storage
from appwrite.exception import AppwriteException
from appwrite.input_file import InputFile

# Load environment variables from .env file
load_dotenv()

def main(context):
    client = (
        Client()
        .set_endpoint(os.environ["APPWRITE_FUNCTION_API_ENDPOINT"])
        .set_project(os.environ["APPWRITE_FUNCTION_PROJECT_ID"])
        .set_key(os.environ["APPWRITE_API_KEY"])
    )
    storage = Storage(client)
    
    # Extract query parameters with default values
    # (Assuming context.req.query is how to retrieve query parameters in your environment)
    volume_threshold = int(context.req.query.get('volume', 500000))
    market_cap_calc_threshold = int(context.req.query.get('market_cap_calc', 100000000))
    perf_ytd_threshold = int(context.req.query.get('perf_ytd', 25))

    # Capture current UTC time as ISO string
    date_modified = datetime.datetime.utcnow().isoformat()

    try:
        # 1) Get Data
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
                col('volume') > volume_threshold,
                col('market_cap_calc') < market_cap_calc_threshold,
                col('Perf.YTD') > perf_ytd_threshold
            )
            .order_by('volume', ascending=False)
            .limit(250)
            .set_markets('crypto')
            .get_scanner_data()
        )

        df = pd.DataFrame(res)
        context.log(df)  # Debug log of the DataFrame

        # 2) Convert DataFrame to JSON file & manipulate lines
        json_file = "tradingview_data.json"
        df.to_json(json_file, orient="records", indent=2)

        with open(json_file, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # Remove lines 2–6
        lines_to_keep = lines[:1] + lines[6:]
        # Remove the last 2 lines
        lines_to_keep = lines_to_keep[:-2]

        # Overwrite the file with the remaining lines
        with open(json_file, "w", encoding="utf-8") as f:
            f.writelines(lines_to_keep)

        # 3) Attempt to upload the JSON file to Appwrite storage
        bucket_id = os.environ["APPWRITE_BUCKET_ID"]
        file_id = "unique()"  # or any custom ID
        try:
            # Instead of passing the open file handle, create an InputFile
            file_input = InputFile.from_path(json_file)
            response = storage.create_file(
                bucket_id=bucket_id,
                file_id=file_id,
                file=file_input  # Pass the file object as InputFile
            )

            # Generate File URL
            uploaded_file_id = response["$id"]
            file_url = (
                f"{os.getenv('APPWRITE_FUNCTION_API_ENDPOINT')}/storage/buckets/"
                f"{bucket_id}/files/{uploaded_file_id}/view"
                f"?project={os.getenv('APPWRITE_FUNCTION_PROJECT_ID')}"
            )

            # Return file URL with date_modified if successful
            context.log(f"File uploaded successfully: {file_url}")
            return context.res.json({
                "file_url": file_url,
                "date_modified": date_modified
            })

        except AppwriteException as err:
            # If file upload fails, return the lines_to_keep as JSON response
            # so your function doesn't crash with HTTP 500
            context.error(f"File Upload Failed: {repr(err)}")
            json_str = "".join(lines_to_keep)

            # If the truncated lines aren’t guaranteed to form valid JSON,
            # consider safer ways to re-build valid JSON instead.
            return context.res.json({
                "error": "File upload failed",
                "content": json_str,
                "date_modified": date_modified
            })

    except AppwriteException as err:
        context.error("Could not : " + repr(err))

    finally:
        # Cleanup the JSON file if it exists
        if os.path.exists(json_file):
            os.remove(json_file)

    # Default return if nothing above returns
    return context.res.json({
        "motto": "Build like a team of hundreds_",
        "learn": "https://appwrite.io/docs",
        "connect": "https://appwrite.io/discord",
        "getInspired": "https://builtwith.appwrite.io",
        "date_modified": date_modified
    })
