import logging
from collections import deque
from typing import Any, Literal

import httpx
from httpx import Response, Timeout
from loguru import logger

from auraframes.exceptions import APIError, NetworkError

# Suppress verbose httpx debug logging
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

AURA_API_BASE_URL = 'https://api.pushd.com'
AURA_API_VERSION = 'v5'
USER_AGENT = 'Aura/4.7.790 (Android 30; Client)'

SENSITIVE_HEADERS = {'x-token-auth', 'authorization', 'cookie', 'set-cookie'}
SENSITIVE_KEYS = {'password', 'token', 'auth_token', 'secret'}

HttpMethod = Literal['GET', 'POST', 'PUT', 'DELETE']


def _sanitize_for_logging(data: dict | None, sensitive_keys: set[str] | None = None) -> dict[str, Any] | None:
    """Remove sensitive data from dict before logging."""
    if data is None:
        return None
    sensitive_keys = sensitive_keys or SENSITIVE_KEYS
    result: dict[str, Any] = {}
    for key, value in data.items():
        if key.lower() in sensitive_keys:
            result[key] = '[REDACTED]'
        elif isinstance(value, dict):
            result[key] = _sanitize_for_logging(value, sensitive_keys)
        else:
            result[key] = value
    return result


def _sanitize_headers(headers: dict | None) -> dict | None:
    """Remove sensitive headers before logging."""
    if headers is None:
        return None
    return {k: '[REDACTED]' if k.lower() in SENSITIVE_HEADERS else v for k, v in headers.items()}


def _handle_response_error(response: Response) -> None:
    """Check response status and raise appropriate exception."""
    if response.status_code >= 400:
        try:
            error_body = response.json()
            error_msg = error_body.get('error', response.text)
        except Exception:
            error_msg = response.text
        raise APIError(f"HTTP {response.status_code}: {error_msg}")


class Client:

    def __init__(self, history_len: int = 30) -> None:
        self.http2_client = httpx.AsyncClient(
            http2=True,
            base_url=f'{AURA_API_BASE_URL}/{AURA_API_VERSION}',
            headers={
                'accept-language': 'en-US',
                'cache-control': 'no-cache',
                'user-agent': USER_AGENT,
                'content-type': 'application/json; charset=utf-8',
            },
            timeout=Timeout(timeout=20.0)
        )
        self.history: deque[Response] = deque(maxlen=history_len)

    async def __aenter__(self) -> "Client":
        return self

    async def __aexit__(self, exc_type: type | None, exc_val: BaseException | None, exc_tb: Any) -> None:
        await self.close()

    async def close(self) -> None:
        await self.http2_client.aclose()

    async def _request(
        self,
        method: HttpMethod,
        url: str,
        data: dict[str, Any] | None = None,
        query_params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | Timeout | None = None
    ) -> dict[str, Any]:
        """
        Make an HTTP request with common error handling and logging.

        :param method: HTTP method (GET, POST, PUT, DELETE)
        :param url: Request URL
        :param data: JSON body data (for POST/PUT)
        :param query_params: Query parameters
        :param headers: Additional headers
        :param timeout: Optional per-request timeout (seconds or Timeout object)
        :return: JSON response body
        :raises NetworkError: On connection/timeout errors
        :raises APIError: On HTTP errors or non-JSON responses
        """
        # Filter out None values from query params
        if query_params:
            query_params = {k: v for k, v in query_params.items() if v is not None}

        # Log request with sanitized data
        logger.debug(
            f'{method} request to {url}',
            data=_sanitize_for_logging(data) if data else None,
            query_params=query_params,
            headers=_sanitize_headers(headers)
        )

        # Make the request
        try:
            request_kwargs: dict[str, Any] = {
                'url': url,
                'params': query_params,
                'headers': headers,
            }
            if method in ('POST', 'PUT'):
                request_kwargs['json'] = data
            if timeout is not None:
                request_kwargs['timeout'] = timeout

            response = await self.http2_client.request(method, **request_kwargs)
        except httpx.TimeoutException as e:
            raise NetworkError(f"Request timed out: {e}")
        except httpx.RequestError as e:
            raise NetworkError(f"Network error: {e}")

        # Track response history
        self.history.append(response)

        # Check for HTTP errors
        _handle_response_error(response)

        # Parse JSON response
        try:
            json_body = response.json()
            logger.debug(f'Response ({response.status_code}), body: {json_body}')
        except Exception:
            logger.debug(f'Response ({response.status_code}), body: {response.text}')
            raise APIError(f'Non-JSON response ({response.status_code}): {response.text}')

        # Handle cookies
        self._set_cookies(response)

        return json_body

    async def get(
        self,
        url: str,
        query_params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | Timeout | None = None
    ) -> dict[str, Any]:
        return await self._request('GET', url, query_params=query_params, headers=headers, timeout=timeout)

    async def post(
        self,
        url: str,
        data: dict[str, Any] | None = None,
        query_params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | Timeout | None = None
    ) -> dict[str, Any]:
        return await self._request('POST', url, data=data, query_params=query_params, headers=headers, timeout=timeout)

    async def put(
        self,
        url: str,
        data: dict[str, Any] | None = None,
        query_params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | Timeout | None = None
    ) -> dict[str, Any]:
        return await self._request('PUT', url, data=data, query_params=query_params, headers=headers, timeout=timeout)

    async def delete(
        self,
        url: str,
        query_params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | Timeout | None = None
    ) -> dict[str, Any]:
        return await self._request('DELETE', url, query_params=query_params, headers=headers, timeout=timeout)

    def add_default_headers(self, headers: dict) -> None:
        self.http2_client.headers.update(headers)

    def _set_cookies(self, response: httpx.Response) -> None:
        if len(response.cookies):
            logger.debug(f'Response Cookies: {response.cookies}')

        for cookie_name, cookie_data in response.cookies.items():
            self.http2_client.cookies.set(cookie_name, cookie_data)
