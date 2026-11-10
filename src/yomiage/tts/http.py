"""HTTP で呼び出す TTS エンジンの共通処理。"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

import aiohttp

from .base import TTSError

T = TypeVar("T")

_TIMEOUT = aiohttp.ClientTimeout(total=60)


def _describe(error: Exception) -> str:
    # ClientResponseError の repr は要求ヘッダーを含むため、認証情報がログに出ないよう使わない
    if isinstance(error, aiohttp.ClientResponseError):
        return f"HTTP {error.status}"
    return type(error).__name__


async def _request(
    session: aiohttp.ClientSession,
    method: str,
    url: str,
    read: Callable[[aiohttp.ClientResponse], Awaitable[T]],
    **kwargs: Any,
) -> T:
    try:
        async with session.request(method, url, timeout=_TIMEOUT, **kwargs) as response:
            response.raise_for_status()
            return await read(response)
    except (aiohttp.ClientError, asyncio.TimeoutError, ValueError) as error:
        raise TTSError(f"{method} {url} に失敗しました: {_describe(error)}") from error


async def request_json(session: aiohttp.ClientSession, method: str, url: str, **kwargs: Any) -> Any:
    return await _request(session, method, url, lambda res: res.json(content_type=None), **kwargs)


async def request_bytes(session: aiohttp.ClientSession, method: str, url: str, **kwargs: Any) -> bytes:
    return await _request(session, method, url, lambda res: res.read(), **kwargs)
