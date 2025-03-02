import functools
import time

from .logging_config import get_logger
from .notify_discord import notify_discord


def retry(max_retries: int, delay: int, notify: bool = False):
    """
    A retry decorator function that allows retrying a function based on the specified
    number of retries, delay between retries, and an option to send a notification upon
    failure. It logs all execution details, including successful executions, exceptions,
    and retry attempts.

    Args:
        max_retries (int): The maximum number of times the function should be retried
            in case of an exception.
        delay (int): The time in seconds to wait before retrying the function after
            a failure.
        notify (bool): Whether to send a notification if the function fails after
            reaching the maximum number of retries. Default is False.

    Returns:
        Callable: A decorator function that applies the retry logic to the decorated
            function.

    Raises:
        Exception: If all retries are exhausted and the function still fails, the
            exception from the last attempt will be raised.

    Example:
    @retry(max_retries=3, delay=2)
    def my_function():
        # Function implementation
        pass
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger(__name__)
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
                    logger.exception(f"Exception: {e}")
                    logger.warning(f"Retrying function {func.__name__} after {delay}s")
                    err = str(e)
                    time.sleep(delay)
            if notify:
                notify_discord(
                    f"{func.__name__} Failed after {max_retries} max_retries.\nException: {err}"
                )
            logger.exception(f"Failed after {max_retries} max_retries")

        return wrapper

    return decorator
