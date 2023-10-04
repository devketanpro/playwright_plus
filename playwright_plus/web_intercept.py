# Built-in imports
import logging
import time
from asyncio.exceptions import CancelledError
from copy import deepcopy

# Private packages imports
from browser_surf import with_page
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from utils import catch_timeout_error
# Public 3rd party packages imports
from playwright.sync_api._generated import Locator, Page

# Local functions and relative imports
# Constants imports
# New constants

### This file contains function to scrape a web page by simulating a browser surfing


def set_json_to_page(page, buffer):
    if not buffer.get("error"):
        page.target_json = buffer
    else:
        page.target_json = {
            "error": "PlaywrightInterceptError",
            "error_message": buffer["error"],
            "data": {},
        }


def json_detect_error(result):
    """
    A simple error detection function for JSON responses.
    Parameters:
        - result (dict): The JSON response result to be checked for errors.
    Returns:
        - is_error (bool): True if an error is detected, False otherwise.
        - result (dict): The original or modified JSON response result.
    """
    if "error" in result and result["error"]:
        return True, result
    else:
        return False, result


def json_parse_result(result):
    """
    A simple JSON parsing function to extract relevant data from a JSON response.

    Parameters:
        - result (dict): The JSON response result to be parsed.

    Returns:
        - parsed_data (dict): The parsed data extracted from the JSON response.
    """
    return result.get("data", {})  # Extract the "data" field from the JSON response


def captcha_solver_function(page):
    """
    Attempt to solve a captcha image.

    Parameters:
        - page: The Selenium WebDriver object representing the web page where the captcha is located.
    Returns:
        - A tuple containing two values:
                 - A boolean indicating whether a refresh is needed (True) or not (False).
                 - The extracted captcha text if it's successfully solved; None if it's not solved.

    This function attempts to solve a captcha image using simple criteria.
    It's a complex logic to solve the captcha, and in the future, a more
    sophisticated implementation may be necessary because it can be a time-consuming task.

    I am currently returning a placeholder/testing value.

    Note: We can use built-in Python libraries like scrapy, or other external libraries for solving the captcha.
    """
    return False, None


def construct_handle_response(page: Page, json_url_subpart: str):
    def handle_response(response):
        try:
            if json_url_subpart in response.url:
                try:
                    buffer = response.json()
                except Exception as jde:
                    buffer = {"error": f"exception when trying to intercept:{str(jde)}"}

                set_json_to_page(page, buffer)

        except CancelledError:
            logging.debug("handle_response was correctly canceled")

    return handle_response


@with_page(headless=True)
@catch_timeout_error()
def intercept_json_playwright(
    page_url: str,
    json_url_subpart: str,
    page: Page = None,
    json_detect_error: callable = None,
    json_parse_result: callable = None,
    captcha_solver_function: callable = None,
    max_refresh: int = 1,
    timeout: int = 4000,
    goto_timeout=30000,
    **kwargs,
) -> dict:
    """
    Intercept JSON data from a web page using Playwright.

    Parameters:
    - page_url (str): The URL of the web page to navigate to.
    - json_url_subpart (str): A subpart of the URL to identify JSON requests.
    - page (Page, optional): The Playwright Page object. If not provided, it will be obtained from the decorator.
    - json_detect_error (callable, optional): A callable function to detect errors in the intercepted JSON response.
    - json_parse_result (callable, optional): A callable function to parse and process the intercepted JSON data.
    - captcha_solver_function (callable, optional): A callable function to solve captchas if encountered.
    - max_refresh (int, optional): The maximum number of page refresh attempts.
    - timeout (int, optional): The total timeout duration in milliseconds.
    - goto_timeout (int, optional): The timeout for the page.goto method in milliseconds.
    - response (Response, optional): The Playwright Response object representing the intercepted JSON response.
    - **kwargs: Additional keyword arguments for configuring the Playwright Page.

    Returns:
    - dict: A dictionary containing the intercepted JSON data or error information.
    """

    logging.debug("This version of playwright_intercept is deprecated")
    time_spent = 0
    nb_refresh = 0
    captcha_to_solve = False
    result = {}
    is_error = False

    # set up the page to intercept the wanted call
    target_json = {}

    def handle_response(response):
        """
        Handle intercepted HTTP responses.

        Parameters:
            - response: The intercepted HTTP response object.
        Returns:
            - A dictionary containing the intercepted data or an error message.

        This function is designed to handle intercepted HTTP responses in the context of the `intercept_json_playwright`
        function. It checks if the response URL contains the specified `json_url_subpart` and attempts to extract JSON data
        from the response. If successful, it populates the `target_json` dictionary with the extracted data. If an error
        occurs during JSON parsing, it populates the `target_json` dictionary with an error message.

        If the response itself contains an error message, it is also included in the `target_json` dictionary.
        """
        if json_url_subpart in response.url:
            try:
                buffer = response.json()
            except Exception as jde:
                buffer = {"error": f"exception when trying to intercept:{str(jde)}"}

            if not buffer.get("error"):
                target_json["data"] = buffer

            else:
                target_json["data"] = {
                    "error": "PlaywrightInterceptError",
                    "error_message": buffer["error"],
                    "data": {},
                }

    page.on("response", handle_response)

    # call the onsite page
    s = time.time()
    try:
        page.goto(page_url, timeout=goto_timeout)
    except:
        # This should be return error since we can't do anything without our page
        pass
    duration = time.time() - s
    time_spent += int(duration * 1000)

    # wait for the valid json to be intercepted
    while (time_spent <= timeout) and (nb_refresh < max_refresh):
        s = time.perf_counter()

        # get the data that has been intercepted
        target_json = target_json.get("data", {})
        logging.debug(
            f"time_spent : {time_spent}. target_json keys: {target_json.keys()}"
        )

        # Create a result object from the intercepted data
        result = {"error": None, "error_message": None, "data": deepcopy(target_json)}

        # if the proper function was provided, scan the result for error
        is_error = False
        if callable(json_detect_error):
            is_error, result = json_detect_error(result)

        # two known cases of error are possible
        ## no json was yet intercepted >> note the error, wait for the next loop iteration
        if not target_json:
            result = {
                "error": "PlaywrightInterceptError",
                "error_message": "An empty json was collected after calling the hidden API.",
                "data": {},
            }

        ## A captcha was raised > raise a flag for a captcha to be solved
        elif result.get("error") == "CaptchaRaisedError":
            captcha_to_solve = True

        ## Other scenario (no error, or unknown new error)
        else:
            break

        # if a captcha flag was raised, try to solve it
        if captcha_to_solve and callable(captcha_solver_function):
            ask_for_refresh, captcha_solved = captcha_solver_function(page)
            if captcha_solved:
                # reset the json and wait for next interception
                captcha_to_solve = False
                target_json = {}
                result = {}

            if ask_for_refresh:
                try:
                    logging.debug("refresh")
                    nb_refresh += 1
                    ask_for_refresh = False
                    page.goto(page_url, timeout=3000)
                except:
                    pass

        # if this loop iteration was too short, wait more time (total duration must be at least 500ms)
        duration = time.perf_counter() - s
        if duration * 1000 < 500:
            remaining_sleep_time = 500 - int(duration * 1000)
            page.wait_for_timeout(remaining_sleep_time)

        # update the time_spent
        duration = time.perf_counter() - s
        time_spent += duration * 1000

    # if the proper function was provided, parse the intercepted json
    if (not is_error) and json_parse_result:
        result = json_parse_result(result)

    return result


@with_page(headless=True)
def intercept_json_playwright_old(
    page_url: str,
    json_url_subpart: str,
    page: Page = None,
    json_detect_error: callable = None,
    json_parse_result: callable = None,
    wait_seconds: int = 4,
    **kwargs,
) -> dict:
    target_json = {}
    is_error = False
    result = {}

    def handle_response(response):
        try:
            if json_url_subpart in response.url:
                try:
                    buffer = response.json()
                except Exception as jde:
                    buffer = {"error": f"exception when trying to intercept:{str(jde)}"}

                if not buffer.get("error"):
                    target_json["data"] = buffer
                else:
                    target_json["data"] = {
                        "error": "PlaywrightInterceptError",
                        "error_message": buffer["error"],
                        "data": {},
                    }
        except CancelledError:
            logging.debug("handle_response was correctly canceled")

    page.on("response", handle_response)

    try:
        page.goto(page_url)
    except PlaywrightTimeoutError as err:
        return {
            "error": "PlaywrightTimeoutError",
            "error_message": str(err),
            "data": {},
        }
    except Exception as err:
        return {"error": "PlaywrightGotoError", "error_message": str(err), "data": {}}

    for _ in range(wait_seconds * 2):
        page.wait_for_timeout(500)
        target_json = target_json.get("data", {})

        logging.debug(f"target_json keys: {target_json.keys()}")
        if not target_json:
            result = {
                "error": "PlaywrightInterceptError",
                "error_message": "An empty json was collected after calling the hidden API.",
                "data": {},
            }
        else:
            result = {"error": None, "error_message": None, "data": target_json}
            break

    if json_detect_error:
        is_error, result = json_detect_error(result)

    if (not is_error) and json_parse_result:
        result = json_parse_result(result)

    return result


@with_page(headless=True)
def intercept_json_playwright_multiple(
    page_url: str,
    json_url_subpart: str,
    page=None,
    json_detect_error: callable = None,
    json_parse_result: callable = None,
    wait_seconds: int = 4,
    expect_more: int = 0,
    **kwargs,
) -> dict:
    """
    WARNING this is a dev environement.
    In a future version this will be merged with the other equivalent methods
    This particular variety needs to be able to recieve a wrong API cal and
    wait for a second one.
    """
    target_json = {}

    def handle_response(response):
        try:
            if json_url_subpart in response.url:
                try:
                    buffer = response.json()
                except Exception as jde:
                    buffer = {"error": f"exception when trying to intercept:{str(jde)}"}

                if not buffer.get("error"):
                    target_json["data"] = buffer
                else:
                    target_json["data"] = {
                        "error": "PlaywrightInterceptError",
                        "error_message": buffer["error"],
                        "data": {},
                    }
        except CancelledError:
            logging.debug("handle_response was correctly canceled")

    page.on("response", handle_response)
    try:
        page.goto(page_url)
    except PlaywrightTimeoutError as err:
        pass
    except Exception as err:
        return {"error": "PlaywrightGotoError", "error_message": str(err), "data": {}}

    # Check if error
    is_error = True
    result = {
        "error": "PlaywrightInterceptError",
        "error_message": "An empty json was collected after calling the hidden API.",
        "data": {},
    }

    for _ in range(wait_seconds * 2):
        page.wait_for_timeout(500)
        target_json = target_json.get("data", {})

        logging.debug(f"target_json keys: {target_json.keys()}")
        if target_json:
            result = {"error": None, "error_message": None, "data": target_json}

            # Check if the result is correct
            if json_detect_error:
                is_error, result = json_detect_error(result)

            if not is_error or expect_more == 0:
                # If we find a correct one or we have recived too many errors
                # We break
                break
            else:
                # If it is an error but we expect more
                # we reduce the total expected
                expect_more -= 1

    if (not is_error) and json_parse_result:
        result = json_parse_result(result)

    return result


def request_json_playwright(
    json_url: str,
    json_url_subpart: str ,
    json_detect_error: callable = None,
    json_parse_result: callable = None,
    **kwargs,
) -> dict:
    """
    Send an HTTP request to a JSON URL using Playwright and return the JSON response.

    Parameters:
        - json_url (str): The URL of the JSON resource to request.
        - json_url_subpart (str): The Sub part of the URL of the JSON resource to request.
        - json_detect_error (callable, optional): A custom error detection function that takes the response text
          as input and returns True if an error is detected, or False otherwise. Defaults to None.
        - json_parse_result (callable, optional): A custom JSON parsing function that takes the response text
          as input and returns the parsed JSON object. Defaults to None.
        - **kwargs: Additional keyword arguments to be passed to `intercept_json_playwright`.
    Returns:
        dict: A dictionary representing the parsed JSON response.
    """

    result = intercept_json_playwright(
        page_url=json_url,
        json_url_subpart=json_url_subpart,
        json_detect_error=json_detect_error,
        json_parse_result=json_parse_result,
        **kwargs,
    )

    return result
