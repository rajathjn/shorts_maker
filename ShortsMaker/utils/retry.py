import functools
import logging
import time

from .notify_discord import notify_discord


def retry(max_retries: int, delay: int, notify: bool = False):
    """
    A decorator that retries a function execution a specified number of times with a delay between retries.

    Args:
        max_retries: The number of times to retry the function.
        delay: The delay in seconds between each retry attempt.

    Returns:
        The decorated function with retry logic.

    Raises:
        Exception: If the function fails after the specified number of retries.

    Example:
        @retry(max_retries=3, delay=2)
        def my_function():
            # Function implementation
            pass
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = logging.getLogger(func.__name__)
            start_time = time.perf_counter()
            logger.info(f"Using retry decorator with {max_retries} max_retries and {delay}s delay")
            logger.info(f"Begin function {func.__name__}")
            err = "Before running"
            for attempt in range(max_retries):
                try:
                    value = func(*args, **kwargs)
                    logger.info(f"Returned: {value}")
                    logger.info(
                        f"Completed function {func.__name__} in {round(time.perf_counter() - start_time, 2)}s after {attempt + 1} max_retries"
                    )
                    return value
                except Exception as e:
                    logger.error(f"Exception: {e}")
                    logger.error(f"Retrying function {func.__name__} after {delay}s")
                    err = str(e)
                    time.sleep(delay)
            if notify:
                notify_discord(
                    f"{func.__name__} Failed after {max_retries} max_retries.\nException: {err}"
                )
            logging.exception(f"Failed after {max_retries} max_retries")

        return wrapper

    return decorator
