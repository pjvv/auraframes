"""Tests for pagination utilities."""
import pytest

from auraframes.exceptions import NetworkError
from auraframes.utils.pagination import paginate


class TestPaginate:
    """Tests for paginate function."""

    @pytest.mark.asyncio
    async def test_single_page(self):
        """Should handle single page response."""
        async def fetch_fn(*args, **kwargs):
            return [1, 2, 3], None

        result = await paginate(fetch_fn)
        assert result == [1, 2, 3]

    @pytest.mark.asyncio
    async def test_multiple_pages(self):
        """Should handle multiple pages."""
        call_count = 0

        async def fetch_fn(*args, cursor=None, **kwargs):
            nonlocal call_count
            call_count += 1
            if cursor is None:
                return [1, 2], "page2"
            elif cursor == "page2":
                return [3, 4], "page3"
            else:
                return [5], None

        result = await paginate(fetch_fn, delay=0.01)
        assert result == [1, 2, 3, 4, 5]
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_empty_first_page(self):
        """Should handle empty first page."""
        async def fetch_fn(*args, **kwargs):
            return [], None

        result = await paginate(fetch_fn)
        assert result == []

    @pytest.mark.asyncio
    async def test_passes_args(self):
        """Should pass positional arguments to fetch function."""
        received_args = []

        async def fetch_fn(arg1, arg2, **kwargs):
            received_args.append((arg1, arg2))
            return ["item"], None

        result = await paginate(fetch_fn, "first", "second")
        assert result == ["item"]
        assert received_args == [("first", "second")]

    @pytest.mark.asyncio
    async def test_passes_kwargs(self):
        """Should pass keyword arguments to fetch function."""
        received_kwargs = []

        async def fetch_fn(*args, **kwargs):
            received_kwargs.append(kwargs)
            return ["item"], None

        result = await paginate(fetch_fn, limit=100, extra="value")
        assert result == ["item"]
        assert "limit" in received_kwargs[0]
        assert received_kwargs[0]["extra"] == "value"

    @pytest.mark.asyncio
    async def test_progress_callback(self):
        """Should call progress callback after each page."""
        progress_calls = []

        async def fetch_fn(*args, cursor=None, **kwargs):
            if cursor is None:
                return [1, 2], "page2"
            return [3], None

        def on_progress(count):
            progress_calls.append(count)

        result = await paginate(fetch_fn, delay=0.01, progress_callback=on_progress)
        assert result == [1, 2, 3]
        assert progress_calls == [2, 3]

    @pytest.mark.asyncio
    async def test_retries_on_network_error(self):
        """Should retry on network errors."""
        call_count = 0

        async def fetch_fn(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise NetworkError("Connection failed")
            return [1, 2, 3], None

        result = await paginate(fetch_fn, max_retries=3)
        assert result == [1, 2, 3]
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_raises_after_max_retries(self):
        """Should raise after max retries exhausted."""
        async def always_fail(*args, **kwargs):
            raise NetworkError("Connection failed")

        with pytest.raises(NetworkError):
            await paginate(always_fail, max_retries=2)

    @pytest.mark.asyncio
    async def test_generic_types(self):
        """Should work with different item types."""
        async def fetch_dicts(*args, cursor=None, **kwargs):
            if cursor is None:
                return [{"id": 1}], "page2"
            return [{"id": 2}], None

        result = await paginate(fetch_dicts, delay=0.01)
        assert result == [{"id": 1}, {"id": 2}]
