# Built-in imports
from copy import deepcopy
import logging
import time

# Public 3rd party packages imports
from playwright.sync_api._generated import Page, Locator

# Private packages imports
from playwright_plus import with_page
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from asyncio.exceptions import CancelledError

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
    logging.debug("This version of playwright_intercept is deprecated")
    time_spent = 0
    nb_refresh = 0
    captcha_to_solve = False

    # set up the page to intercept the wanted call
    target_json = {}

    def handle_response(response):
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
    json_detect_error: callable = None,
    json_parse_result: callable = None,
    **kwargs,
) -> dict:
    result = intercept_json_playwright(
        page_url=json_url,
        json_url_subpart=json_url,
        json_detect_error=json_detect_error,
        json_parse_result=json_parse_result,
        **kwargs,
    )

    return result
