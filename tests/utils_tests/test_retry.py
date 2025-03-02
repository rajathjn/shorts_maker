from unittest.mock import Mock, patch

from ShortsMaker.utils.retry import retry


def test_retry_preserves_function_docstring():
    @retry(max_retries=3, delay=0)
    def mock_func():
        """This is a test function."""
        pass

    assert mock_func.__doc__ == "This is a test function."


@patch("ShortsMaker.utils.retry.logger")
def test_retry_logs_function_name(mock_logger):
    # Test that function name is correctly logged
    mock_func = Mock(return_value="success")
    mock_func.__name__ = "test_func"
    decorated = retry(max_retries=1, delay=0)(mock_func)

    decorated()

    mock_logger.info.assert_any_call("Begin function test_func")


@patch("ShortsMaker.utils.retry.logger")
def test_retry_logs_return_value(mock_logger):
    # Test that return value is correctly logged
    mock_func = Mock(return_value="test_value")
    mock_func.__name__ = "test_func"
    decorated = retry(max_retries=1, delay=0)(mock_func)

    decorated()

    mock_logger.info.assert_any_call("Returned: test_value")


@patch("ShortsMaker.utils.retry.logger")
def test_retry_logs_execution_time(mock_logger):
    # Test that execution time is logged
    mock_func = Mock(return_value="success")
    mock_func.__name__ = "test_func"
    decorated = retry(max_retries=1, delay=0)(mock_func)

    decorated()

    # Check that completion log contains function name and execution time
    completion_log_call = mock_logger.info.call_args_list[-1]
    assert "Completed function test_func in" in str(completion_log_call)
    assert "s after 1 max_retries" in str(completion_log_call)


@patch("ShortsMaker.utils.retry.logger")
def test_retry_logs_max_retries_and_delay(mock_logger):
    # Test that retry parameters are logged
    mock_func = Mock(return_value="success")
    mock_func.__name__ = "test_func"
    decorated = retry(max_retries=5, delay=10)(mock_func)

    decorated()

    mock_logger.info.assert_any_call("Using retry decorator with 5 max_retries and 10s delay")


@patch("ShortsMaker.utils.retry.logger")
def test_retry_logs_attempts(mock_logger):
    mock_func = Mock(side_effect=[Exception("error"), "success"])
    mock_func.__name__ = "test_func"
    decorated = retry(max_retries=2, delay=0)(mock_func)

    decorated()

    assert mock_logger.info.call_count >= 2
    assert mock_logger.warning.call_count == 1
    assert mock_logger.exception.call_count == 1


def test_retry_successful_second_attempt():
    mock_func = Mock(side_effect=[Exception("error"), "success"])
    mock_func.__name__ = "test_func"
    decorated = retry(max_retries=3, delay=0)(mock_func)

    result = decorated()

    assert result == "success"
    assert mock_func.call_count == 2


def test_retry_all_attempts_failed():
    mock_func = Mock(side_effect=Exception("error"))
    mock_func.__name__ = "test_func"
    decorated = retry(max_retries=3, delay=0)(mock_func)

    result = decorated()

    assert result is None
    assert mock_func.call_count == 3


@patch("ShortsMaker.utils.retry.notify_discord")
def test_retry_with_notify(mock_notify):
    mock_func = Mock(side_effect=Exception("error"))
    mock_func.__name__ = "test_func"
    decorated = retry(max_retries=2, delay=0, notify=True)(mock_func)

    decorated()

    mock_notify.assert_called_once_with("test_func Failed after 2 max_retries.\nException: error")


@patch("time.sleep")
def test_retry_respects_delay(mock_sleep):
    mock_func = Mock(side_effect=[Exception("error"), "success"])
    mock_func.__name__ = "test_func"
    delay = 5
    decorated = retry(max_retries=3, delay=delay)(mock_func)

    decorated()

    mock_sleep.assert_called_once_with(delay)


def test_retry_preserves_function_args():
    mock_func = Mock(return_value="success")
    mock_func.__name__ = "test_func"
    decorated = retry(max_retries=3, delay=0)(mock_func)

    decorated(1, key="value")

    mock_func.assert_called_once_with(1, key="value")
