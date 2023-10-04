import unittest

from web_intercept import (json_detect_error, json_parse_result,
                           request_json_playwright)


class TestPlaywrightPlus(unittest.TestCase):
    def test_intercept_json_playwright(self):
        """
        Test intercepting JSON data from a website with specified parameters.

        Parameters:
        - timeout: Set a timeout of 9000 milliseconds.
        - json_url: Specify the website URL.
        - json_url_subpart: Subpart of the URL for JSON data.
        - json_detect_error: Function to detect errors in the JSON response.
        - json_parse_result: Function to extract records from the 'data' key.
        """
        result = request_json_playwright(
            timeout=9000,
            json_url="https://blog.teclado.com/",
            json_url_subpart="/api/content/tiers/",
            json_detect_error=json_detect_error,
            json_parse_result=json_parse_result,
        )
        self.assertIsNotNone(result)
        tiers = result.get("tiers")
        meta = result.get("meta")

        # Additional assertions to check the JSON data
        self.assertIsNotNone(tiers)
        self.assertIsNotNone(meta)
        self.assertIn("pagination", meta)
        pagination = meta["pagination"]
        self.assertIsNotNone(pagination)
        self.assertIn("total", pagination)
        total = pagination["total"]

        # Check if the number of tiers matches the 'total' value in pagination
        self.assertEqual(len(tiers), total)

        # Check if the 'active' attribute of the first tier is True
        self.assertTrue(tiers[0].get("active"))

    def test_intercept_json_playwright_with_empty_response(self):
        """
        Test when the JSON response is empty.

        Parameters:
        - timeout: Set a timeout of 9000 milliseconds.
        - json_url: Specify the website URL.
        - json_url_subpart: Subpart of the URL for JSON data.
        - json_detect_error: Function to detect errors in the JSON response.
        - json_parse_result: Function to extract records from the 'data' key.
        """
        result = request_json_playwright(
            timeout=9000,
            json_url="https://blog.teclado.com/",
            json_url_subpart="/api/members/",
            json_detect_error=json_detect_error,
            json_parse_result=json_parse_result,
        )

        self.assertIsNotNone(result)

        # Additional assertion to check if the result is an empty dictionary
        self.assertEqual(result, {})

    def test_intercept_json_playwright_with_invalid_json(self):
        """
        Test when the JSON response is invalid.

        Parameters:
        - json_url: Specify the website URL.
        - json_url_subpart: Subpart of the URL for JSON data.
        - json_detect_error: Function to detect errors in the JSON response.
        - json_parse_result: Function to extract records from the 'data' key.
        """
        result = request_json_playwright(
            json_url="https://blog.teclado.com/",
            json_url_subpart="send/event",
            json_detect_error=json_detect_error,
            json_parse_result=json_parse_result,
        )

        self.assertIsNotNone(result)

        # Additional assertion to check the error message and structure of the result
        self.assertIn("error", result)
        self.assertIn("error_message", result)
        self.assertIn("data", result)
        self.assertEqual(result["error"], "PlaywrightInterceptError")
        self.assertIn("Expecting value", result["error_message"])


if __name__ == "__main__":
    unittest.main()
