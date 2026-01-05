"""Tests for retry utilities."""
import pytest

from auraframes.exceptions import NetworkError
from auraframes.utils.retry import with_retry, retry


class TestWithRetry:
    """Tests for with_retry function."""

    @pytest.mark.asyncio
    async def test_success_no_retry(self):
        """Successful function should return without retry."""
        call_count = 0

        async def success_fn():
            nonlocal call_count
            call_count += 1
            return "success"

        result = await with_retry(success_fn, max_retries=3)
        assert result == "success"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_retry_on_network_error(self):
        """NetworkError should trigger retry."""
        call_count = 0

        async def fail_then_succeed():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise NetworkError("Connection failed")
            return "success"

        result = await with_retry(fail_then_succeed, max_retries=3, initial_delay=0.01)
        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_retry_exhausted(self):
        """Should raise after max retries exhausted."""
        call_count = 0

        async def always_fail():
            nonlocal call_count
            call_count += 1
            raise NetworkError("Connection failed")

        with pytest.raises(NetworkError, match="Connection failed"):
            await with_retry(always_fail, max_retries=2, initial_delay=0.01)
        assert call_count == 3  # Initial + 2 retries

    @pytest.mark.asyncio
    async def test_retry_on_connection_error(self):
        """ConnectionError should trigger retry."""
        call_count = 0

        async def fail_then_succeed():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("Connection refused")
            return "success"

        result = await with_retry(fail_then_succeed, max_retries=3, initial_delay=0.01)
        assert result == "success"
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_retry_on_timeout_error(self):
        """TimeoutError should trigger retry."""
        call_count = 0

        async def fail_then_succeed():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise TimeoutError("Request timed out")
            return "success"

        result = await with_retry(fail_then_succeed, max_retries=3, initial_delay=0.01)
        assert result == "success"
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_no_retry_on_other_exceptions(self):
        """Non-retry exceptions should not trigger retry."""
        call_count = 0

        async def value_error():
            nonlocal call_count
            call_count += 1
            raise ValueError("Invalid value")

        with pytest.raises(ValueError, match="Invalid value"):
            await with_retry(value_error, max_retries=3, initial_delay=0.01)
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_custom_retry_exceptions(self):
        """Custom retry exceptions should be respected."""
        call_count = 0

        async def fail_then_succeed():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Custom error")
            return "success"

        result = await with_retry(
            fail_then_succeed,
            max_retries=3,
            initial_delay=0.01,
            retry_exceptions=(ValueError,)
        )
        assert result == "success"
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_passes_args_and_kwargs(self):
        """Arguments should be passed to function."""
        async def add(a, b, c=0):
            return a + b + c

        result = await with_retry(add, 1, 2, c=3, max_retries=1)
        assert result == 6


class TestRetryDecorator:
    """Tests for retry decorator."""

    @pytest.mark.asyncio
    async def test_decorator_success(self):
        """Decorated function should work normally on success."""
        @retry(max_retries=3, initial_delay=0.01)
        async def success_fn():
            return "success"

        result = await success_fn()
        assert result == "success"

    @pytest.mark.asyncio
    async def test_decorator_retry_on_error(self):
        """Decorated function should retry on error."""
        call_count = 0

        @retry(max_retries=3, initial_delay=0.01)
        async def fail_then_succeed():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise NetworkError("Connection failed")
            return "success"

        result = await fail_then_succeed()
        assert result == "success"
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_decorator_preserves_function_name(self):
        """Decorated function should preserve original name."""
        @retry(max_retries=3)
        async def my_function():
            return "result"

        assert my_function.__name__ == "my_function"

    @pytest.mark.asyncio
    async def test_decorator_with_custom_exceptions(self):
        """Decorator should support custom exceptions."""
        call_count = 0

        @retry(max_retries=3, initial_delay=0.01, retry_exceptions=(KeyError,))
        async def fail_then_succeed():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise KeyError("Missing key")
            return "success"

        result = await fail_then_succeed()
        assert result == "success"
        assert call_count == 2
