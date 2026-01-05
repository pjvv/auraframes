"""Tests for the HTTP client."""
import pytest
import respx
from httpx import Response

from auraframes.client import Client, AURA_API_BASE_URL, AURA_API_VERSION


BASE_URL = f'{AURA_API_BASE_URL}/{AURA_API_VERSION}'


class TestClient:
    """Tests for the Client class."""

    @respx.mock
    def test_client_initializes_with_httpx_client(self):
        """Client should initialize with an httpx client."""
        client = Client()
        assert client.http2_client is not None

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_request_constructs_correct_url(self):
        """GET requests should construct the correct URL."""
        route = respx.get(f'{BASE_URL}/frames.json').mock(
            return_value=Response(200, json={'data': 'test'})
        )

        client = Client()
        await client.get('/frames.json')

        assert route.called
        assert route.call_count == 1

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_request_returns_json(self):
        """GET requests should return parsed JSON."""
        respx.get(f'{BASE_URL}/frames.json').mock(
            return_value=Response(200, json={'frames': [{'id': '123'}]})
        )

        client = Client()
        result = await client.get('/frames.json')

        assert result == {'frames': [{'id': '123'}]}

    @pytest.mark.asyncio
    @respx.mock
    async def test_post_request_sends_data(self):
        """POST requests should send data correctly."""
        route = respx.post(f'{BASE_URL}/login.json').mock(
            return_value=Response(200, json={'result': 'ok'})
        )

        client = Client()
        result = await client.post('/login.json', data={'user': {'email': 'test@test.com'}})

        assert route.called
        assert result == {'result': 'ok'}
        # Verify the request body
        request = route.calls.last.request
        assert b'test@test.com' in request.content

    @pytest.mark.asyncio
    @respx.mock
    async def test_add_default_headers(self):
        """Client should allow adding default headers."""
        route = respx.get(f'{BASE_URL}/test.json').mock(
            return_value=Response(200, json={'data': 'test'})
        )

        client = Client()
        client.add_default_headers({
            'x-token-auth': 'test-token',
            'x-user-id': 'user-123'
        })
        await client.get('/test.json')

        # Verify headers were sent
        request = route.calls.last.request
        assert request.headers['x-token-auth'] == 'test-token'
        assert request.headers['x-user-id'] == 'user-123'

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_with_query_params(self):
        """GET requests should include query parameters."""
        route = respx.get(f'{BASE_URL}/assets.json').mock(
            return_value=Response(200, json={'data': 'test'})
        )

        client = Client()
        await client.get('/assets.json', query_params={'frame_id': 'frame-123', 'limit': 100})

        # Verify query params were sent
        request = route.calls.last.request
        assert 'frame_id=frame-123' in str(request.url)
        assert 'limit=100' in str(request.url)


class TestClientErrorHandling:
    """Tests for client error handling."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_non_json_response_raises_exception(self):
        """Non-JSON responses should raise an exception."""
        respx.post(f'{BASE_URL}/test.json').mock(
            return_value=Response(200, text='Not JSON content')
        )

        client = Client()

        with pytest.raises(Exception) as exc_info:
            await client.post('/test.json', data={})

        assert 'Non-JSON response' in str(exc_info.value)
