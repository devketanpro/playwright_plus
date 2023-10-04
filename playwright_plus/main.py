import os

from dotenv import load_dotenv
from web_intercept import (json_detect_error, json_parse_result,
                           request_json_playwright)

# Load environment variables from .env file
load_dotenv()


if __name__ == "__main__":
    PAGE_URL = os.getenv("PAGE_URL")
    JSON_URL_SUBPART = os.getenv("JSON_URL_SUBPART")
    result = request_json_playwright(
        timeout=9000,
        json_url=PAGE_URL,
        json_url_subpart=JSON_URL_SUBPART,
        json_detect_error=json_detect_error,
        json_parse_result=json_parse_result,
    )
    print(
        f"Successfully scraped data from the website at {PAGE_URL} and fetched the API data located at the subpart: {JSON_URL_SUBPART} and the data is :\n"
    )
    print(result)
