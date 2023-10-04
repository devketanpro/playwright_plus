# Built-in imports
import logging
from asyncio.exceptions import CancelledError
from random import randint

# Public 3rd party packages imports
from playwright.sync_api import sync_playwright
from playwright.sync_api._generated import Locator, Page

# Private packages imports
# Local functions and relative imports
# Constants imports
# New constants
EXCLUDED_RESOURCES_TYPES = ["stylesheet", "image", "font", "svg"]

__all__ = [
    "check_for_loaded_marker",
    "open_new_page",
    "wait_after_execution",
    "with_page",
]


def create_block_resources(resources_to_block: list):
    def _block_resources(route):
        """
        See
        - https://playwright.dev/python/docs/api/class-request#request-resource-type
        - https://www.zenrows.com/blog/blocking-resources-in-playwright#blocking-resources

        """
        try:
            if route.request.resource_type in resources_to_block:
                route.abort()

            else:
                route.continue_()

        except CancelledError as err:
            logging.debug("block_resources was correctly canceled")

    return _block_resources


### WEB BROWSER AND PAGE OPENING


def _instantiate_browser_context_page(
    p,
    proxy_info: dict = None,
    headless: bool = True,
    accept_downloads: bool = True,
    block_resources: bool | list = True,
    cookies: list[dict] = None,
    browser_type: str = "chromium",
    **kwargs,
):
    """
    Create and configure a browser context along with a new page while excluding specific resource types.

    This function opens a browser, creates a browser context, and opens a new page with the specified settings.
    It allows for customization of browser behavior, proxy configuration, and resource blocking.

    Parameters:
    - p: A Playwright instance.
    - proxy_info: A dictionary containing proxy server information.
    - headless: Whether to run the browser in headless mode (default is True).
    - accept_downloads: Whether the browser should accept downloads (default is True).
    - block_resources: Whether to block specific resource types or provide a list of resource types to block (default is True).
    - cookies: A list of dictionaries containing cookies to set for the page (default is None).
    - browser_type: The type of browser to launch, either "chromium" or "firefox" (default is "chromium").
    - **kwargs: Additional keyword arguments for customization.

    Returns:
    - A tuple containing the browser, browser context, and a new page.
      - browser: The browser instance.
      - context: The browser context.
      - page: The new page created within the context.

    """

    # open chromium browser, using specified proxy
    browser = None
    logging.debug(
        f"[playwright_plus] open a browser : headless={headless}, proxy_info={proxy_info.get('server') if isinstance(proxy_info, dict) else None}"
    )
    match browser_type:
        case "chromium":
            browser = p.chromium.launch(headless=headless, proxy=proxy_info)
        case "firefox":
            browser = p.firefox.launch(headless=headless, proxy=proxy_info)

    # create the browser context
    logging.debug(
        f"[playwright_plus] open a browser context: accept_downloads={accept_downloads}, with {len(cookies) if cookies else 0} cookies set(s)"
    )
    if not browser:
        return None, None, None
    # The browser.new_context method is used to create a new browser context
    context = browser.new_context(accept_downloads=accept_downloads)

    # Add an initialization script to the context to modify the behavior of the navigator.webdriver property as False.
    context.add_init_script(
        """
            navigator.webdriver = false
            Object.defineProperty(navigator, 'webdriver', {
                get: () => false
            })
        """
    )

    # Add the cookies in the context
    if cookies:
        context.add_cookies(cookies)

    # open a web page
    logging.debug(
        f"[playwright_plus] open a new page: blocked resources={EXCLUDED_RESOURCES_TYPES if block_resources==True else block_resources}"
    )
    page = context.new_page()
    if block_resources:
        # If block resources is True then we are blocking some resources
        resources_to_block = (
            EXCLUDED_RESOURCES_TYPES if block_resources == True else block_resources
        )

        def _block_resources(route):
            try:
                if route.request.resource_type in resources_to_block:
                    route.abort()

                else:
                    route.continue_()

            except CancelledError as err:
                logging.debug("block_resources was correctly canceled")

        page.route("**/*", _block_resources)

    return browser, context, page


def open_new_page(
    proxy_info: dict = None,
    headless: bool = True,
    accept_downloads: bool = True,
    block_resources: bool | list = True,
    cookies: list[dict] = None,
    **kwargs,
):
    """
    Create and configure a new web page within a browser using Playwright.
    This function simplifies the process of creating a new web page by providing default configurations
    and options that can be customized.

    Parameters:
    - proxy_info (dict, optional): A dictionary containing proxy server information. Default is None.
    - headless (bool, optional): Whether to run the browser in headless mode (without a graphical user interface).
    Default is True.
    - accept_downloads (bool, optional): Whether the browser should accept downloads. Default is True.
    - block_resources (bool or list, optional): Control whether to block specific types of web resources during page loading.
    If True, block common resource types (["stylesheet", "image", "font", "svg"]).
    If a list is provided, block the specified resource types. Default is True.
    - cookies (list of dicts, optional): A list of dictionaries containing cookies to set for the new page. Default is None.
    - **kwargs: Additional keyword arguments for customization (not used within this function).

    Returns:
    A tuple containing:
    - browser: The browser instance.
    - context: The browser context.
    - page: The new web page created within the context.

    """
    p = sync_playwright().start()

    browser, context, page = _instantiate_browser_context_page(
        p,
        proxy_info=proxy_info,
        headless=headless,
        accept_downloads=accept_downloads,
        block_resources=block_resources,
        cookies=cookies,
    )

    return browser, context, page


def with_page(**kwargs):
    """
    A decorator function that adds a new page obtained from the `_instantiate_browser_context_page` function
    as a keyword argument to the decorated function.

    Parameters:
    - func: The function to be decorated.

    Returns:
    - The decorated function with an additional 'page' keyword argument.
    """

    def decorator(func):
        def func_wrapper(*func_args, **func_kwargs):
            __doc__ = """This is just a decorator function is used to add the new page that we are getting from `_instantiate_browser_context_page` function in the function kwargs"""

            # by default, accept_downloads=True, headless=True, block_resources=True, no proxy, no cookies
            default = {
                "accept_downloads": True,
                "headless": True,
                "block_resources": True,
                "proxy_info": None,
            }
            for k, v in default.items():
                if k not in kwargs:
                    kwargs[k] = v

            # overwrite the decorator kwargs if the ones specified by the wrapped function
            kwargs.update(func_kwargs)

            # open browser, context and page with the conditions specified in the kwargs dictionary
            with sync_playwright() as p:
                browser, context, page = _instantiate_browser_context_page(p, **kwargs)

                # add the new page to thfunc_kwargse wrapped function kwargs
                func_kwargs["page"] = page

                # execute the function with the open page
                output = func(*func_args, **func_kwargs)

                # close the page and browser
                page.close()
                browser.close()

            return output

        return func_wrapper

    return decorator


### WEB SURFING
def _get_page_arg(func_args: list, func_kwargs: dict, func_name: str) -> Page:
    """
    Retrieve a 'Page' object from function arguments or keyword arguments.
    This utility function is used to extract a 'Page' object from the arguments or keyword arguments
    of a decorated function. It is typically used within decorators in web automation or testing scripts.

    Parameters:
    - func_args (list): A list of positional arguments passed to the decorated function.
    - func_kwargs (dict): A dictionary of keyword arguments passed to the decorated function.
    - func_name (str): The name of the decorated function, used in error messages.

    Returns:
    - A 'Page' object if found in the arguments or keyword arguments.
    """
    page = None
    if func_kwargs:
        page = func_kwargs.get("page")
    if (not page) and func_args:
        page = func_args[0]
    if not isinstance(page, Page):
        raise Exception(
            f"One of the decorator expects the function `{func_name}` to have a page as first arg or as kwarg."
        )
    return page


def wait_after_execution(wait_ms: int = 2000, randomized: bool = True):
    """
    Decorator that introduces a pause after the execution of a decorated function.
    This decorator is used to add a waiting period after the execution of a function.
    It can be helpful in web automation and testing scenarios where you need to
    control the timing of actions on a web page.

    Parameters:
    - wait_ms (int, optional): The duration in milliseconds to wait after the function execution.
      Default is 2000 milliseconds (2 seconds).

    - randomized (bool, optional): Whether to introduce randomization to the waiting time.
      If True, the actual waiting time will vary within a 15% range around 'wait_ms.'
      If False, the waiting time will be exactly 'wait_ms.' Default is True.
    """

    def decorator(func):
        def func_wrapper(*func_args, **func_kwargs):
            # get the page object. Check the kwargs first, then the first args
            page = _get_page_arg(func_args, func_kwargs, func.__name__)

            # execute the function
            output = func(*func_args, **func_kwargs)

            # wait for the given time before moving to the next command
            nonlocal wait_ms
            # the wait_ms value can be overwritten if it is specified as a kwarg in the wrapped function
            if func_kwargs and ("wait_ms" in func_kwargs):
                wait_ms = func_kwargs.get("wait_ms")

            if randomized:
                # take a random number in the 15% range around the input time in millisecond
                min = int(wait_ms * 0.85 + 0.5)
                max = int(wait_ms * 1.15 + 0.5)
                wait_ms = randint(min, max)
            # wait for the given time before moving to the next command
            page.wait_for_timeout(wait_ms)

            return output

        return func_wrapper

    return decorator


def check_for_loaded_marker(
    marker: str | Locator = None,
    marker_strict: bool = False,
    load_message: str = None,
    timeout: int = 10000,
):
    """
    Decorator that checks for the presence and visibility of an HTML element (marker) on a web page.
    This decorator is used to ensure that a specific HTML element (marker) is present and visible on a web page
    before and after executing a decorated function. It is typically used in web automation or testing scripts.

    Parameters:
    - marker (str or Locator, optional): The marker can be either a string selector or a Playwright Locator object
      representing the HTML element to check. Default is None.
    - marker_strict (bool, optional): A boolean flag indicating whether the marker selector should be used as-is (True)
      or if a dot (.) should be added before it (False). Default is False.
    - load_message (str, optional): An optional custom message to log when the marker is considered loaded.
      If not provided, a default message is used. Default is None.
    - timeout (int, optional): The maximum time in milliseconds to wait for the marker to become visible on the page.
      Default is 10000 milliseconds (10 seconds).

    Returns:
    - The decorated function with the added marker checking behavior.
    """

    def decorator(func):
        def func_wrapper(*func_args, **func_kwargs):
            # get the page object. Check the kwargs first, then the first args
            page = _get_page_arg(func_args, func_kwargs, func.__name__)

            # execute the function
            output = func(*func_args, **func_kwargs)

            # build the marker locator if needed
            nonlocal marker
            if isinstance(marker, str):
                # add a dot before the marker if it misses it
                if not (marker_strict) and not (marker.startswith(".")):
                    marker = "." + marker
                # make the marker a playwright Locator
                marker = page.locator(marker)
                # wait for the marker to be visible
                marker.wait_for(timeout=timeout)
                logging.debug(
                    load_message
                    if load_message
                    else "[playwright_plus] loaded marker visible."
                )

            return output

        return func_wrapper

    return decorator
