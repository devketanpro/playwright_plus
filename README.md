# playwright_plus
This repository contains a collection of Python functions and decorators for web scraping and automation using Playwright, a powerful tool for browser automation. These functions simplify common tasks and provide customization options for various web automation scenarios. This is the Custom augmented version of the python playwright library.
## Table of Contents
- [Introduction](#introduction)
- [Getting Started](#getting-started)
- [Function List](#function-list)
  - [Json Error Detector](#json-error-detector)
  - [Json Parse Result](#json-parse-result)
  - [Captcha Solver Function](#captcha-solver-function)
  - [Intercept Json Playwright](#intercept-json-playwright)
  - [Handle Response](#handle-response)
  - [Request Json Playwright](#request-json-playwright)
  - [Instantiate Browser Context Page](#instantiate-browser-context-page)
  - [Open New Page](#open-new-page)
  - [With Page](#with-page)
  - [Get page arguments](#get-page-arg)
  - [Wait after execution](#wait-after-execution)
  - [Check for loaded marker](#check-for-loaded-marker)
- [How to Test](#how-to-test)

## Introduction

Playwright is a versatile tool for automating web interactions, including web scraping, form filling, and UI testing. However, it can require complex setup and handling of various aspects of web automation. This repository aims to simplify web automation tasks using Playwright by providing a collection of Python functions and decorators.

## Getting Started

To use these functions in your Python project, follow these steps:

1. Install Playwright and Playwright-Python:
   ```bash
   pip install -r requirements.txt
   
## Function list
### Json Error Detector
#### func_name: json_detect_error
* A simple error detection function for JSON responses.

### Json Parse Result
#### func_name: json_parse_result
* A simple JSON parsing function to extract relevant data from a JSON response.

### Captcha Solver Function
#### func_name: captcha_solver_function
* Attempt to solve a captcha image.

### Intercept Json Playwright
#### func_name: intercept_json_playwright
* Intercept JSON data from a web page using Playwright.

### Handle Response
#### func_name: handle_response
* Handle intercepted HTTP responses.

### Request Json Playwright
#### func_name: request_json_playwright
* Send an HTTP request to a JSON URL using Playwright and return the JSON response.

### Instantiate Browser Context and Page
#### func_name: _instantiate_browser_context_page
* Create and configure a browser context along with a new page while excluding specific resource types.

### Open New Page
#### func_name: open_new_page
*   Create and configure a new web page within a browser using Playwright.
    This function simplifies the process of creating a new web page by providing default configurations
    and options that can be customized.

### With Page
#### func_name: with_page
*   A decorator function that adds a new page obtained from the `_instantiate_browser_context_page` function
    as a keyword argument to the decorated function.

### Get page arguments
#### func_name: _get_page_arg
*   Retrieve a 'Page' object from function arguments or keyword arguments.
    This utility function is used to extract a 'Page' object from the arguments or keyword arguments
    of a decorated function. It is typically used within decorators in web automation or testing scripts.

### Wait after execution
#### func_name: wait_after_execution
*   Decorator that introduces a pause after the execution of a decorated function.
    This decorator is used to add a waiting period after the execution of a function.
    It can be helpful in web automation and testing scenarios where you need to
    control the timing of actions on a web page.

### Check for loaded marker
#### func_name: check_for_loaded_marker
*   Decorator that checks for the presence and visibility of an HTML element (marker) on a web page.
    This decorator is used to ensure that a specific HTML element (marker) is present and visible on a web page
    before and after executing a decorated function. It is typically used in web automation or testing scripts.

## How to Test
 ```bash
 1. cd playwright_plus
 2. python test_intercept_json_playwright.py
