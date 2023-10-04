from playwright._impl._api_types import TimeoutError as PlaywrightTimeoutError


def catch_TimeoutError(
    exception_class: Exception = Exception,
    message: str = None,
):
    def decorator(func):
        def func_wrapper(*args, **kwargs):
            try:
                output = func(*args, **kwargs)
                return output

            except PlaywrightTimeoutError as te:
                # instantiate the exception to raise.
                exception = exception_class(message)
                # customize the error message
                exception.message = f"[{func.__name__}] {exception.message}:\n{str(te)}"
                # raise the exception
                raise exception

        return func_wrapper

    return decorator
