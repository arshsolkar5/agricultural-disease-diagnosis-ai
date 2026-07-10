import asyncio
import json
import time
from typing import Any, Dict, List, Optional, Type, TypeVar

import httpx
from pydantic import BaseModel

from app.config import settings
from app.utils.exceptions import (
    OpenRouterAuthenticationException,
    OpenRouterException,
    OpenRouterResponseException,
    OpenRouterTimeoutException,
)
from app.utils.logger import get_logger

logger = get_logger("llm.openrouter")

T = TypeVar("T", bound=BaseModel)


class RateLimiter:
    """Simple token bucket rate limiter for OpenRouter API."""

    _instance: Optional["RateLimiter"] = None
    _lock: asyncio.Lock = asyncio.Lock()

    def __new__(cls, requests_per_minute: int = 8):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.requests_per_minute = requests_per_minute
            cls._instance.tokens = requests_per_minute
            cls._instance.last_update = time.time()
            cls._instance._instance_lock = asyncio.Lock()
        return cls._instance

    async def acquire(self) -> None:
        async with self._instance_lock:
            now = time.time()
            elapsed = now - self.last_update
            self.tokens = min(self.requests_per_minute, self.tokens + elapsed * (self.requests_per_minute / 60.0))
            self.last_update = now

            if self.tokens < 1:
                wait_time = (1 - self.tokens) * (60.0 / self.requests_per_minute)
                logger.info("rate_limit_wait", wait_seconds=round(wait_time, 2))
                await asyncio.sleep(wait_time)
                self.tokens = 1
            else:
                self.tokens -= 1


class OpenRouterClient:
    """Thin, centralized OpenRouter client with retries and structured output support."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout_seconds: Optional[float] = None,
        max_retries: Optional[int] = None,
        retry_backoff_seconds: Optional[float] = None,
        site_url: Optional[str] = None,
        app_name: Optional[str] = None,
        rate_limit_rpm: Optional[int] = None,
    ) -> None:
        self.api_key = api_key if api_key is not None else settings.openrouter_api_key
        self.base_url = (base_url or settings.openrouter_base_url).rstrip("/")
        self.model = model or settings.openrouter_model
        self.timeout_seconds = timeout_seconds or settings.openrouter_timeout_seconds
        self.max_retries = max_retries or settings.openrouter_max_retries
        self.retry_backoff_seconds = retry_backoff_seconds or settings.openrouter_retry_backoff_seconds
        self.site_url = site_url or settings.openrouter_site_url
        self.app_name = app_name or settings.openrouter_app_name
        self.rate_limiter = RateLimiter(rate_limit_rpm or getattr(settings, 'openrouter_rate_limit_rpm', 8))

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    def _headers(self) -> Dict[str, str]:
        headers = {
            "Content-Type": "application/json",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        if self.site_url:
            headers["HTTP-Referer"] = self.site_url
        if self.app_name:
            headers["X-OpenRouter-Title"] = self.app_name
        return headers

    def _build_response_format(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "type": "json_schema",
            "json_schema": {
                "name": schema.get("title", "structured_response"),
                "schema": schema,
                "strict": True,
            },
        }

    async def _post(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not self.api_key:
            raise OpenRouterAuthenticationException("OPENROUTER_API_KEY is not configured")

        await self.rate_limiter.acquire()

        url = f"{self.base_url}/chat/completions"
        timeout = httpx.Timeout(self.timeout_seconds)

        last_error: Optional[Exception] = None
        for attempt in range(1, self.max_retries + 1):
            started_at = asyncio.get_running_loop().time()
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.post(url, headers=self._headers(), json=payload)

                latency_ms = (asyncio.get_running_loop().time() - started_at) * 1000
                logger.info(
                    "openrouter_response",
                    model=payload.get("model", self.model),
                    status_code=response.status_code,
                    latency_ms=round(latency_ms, 2),
                    attempt=attempt,
                )

                if response.status_code == 401 or response.status_code == 403:
                    raise OpenRouterAuthenticationException(
                        f"OpenRouter authentication failed with status {response.status_code}"
                    )

                if response.status_code in {408, 429, 500, 502, 503, 504}:
                    message = response.text.strip() or f"HTTP {response.status_code}"
                    last_error = OpenRouterException(message)
                    # For rate limits (429), fail fast to allow fallback
                    if response.status_code == 429:
                        raise last_error
                    if attempt < self.max_retries:
                        await asyncio.sleep(self.retry_backoff_seconds * (2 ** (attempt - 1)))
                        continue
                    raise last_error

                if 400 <= response.status_code < 500:
                    raise OpenRouterResponseException(
                        response.text.strip() or f"OpenRouter request failed with status {response.status_code}"
                    )

                data = response.json()
                return data
            except (httpx.TimeoutException, httpx.TransportError) as exc:
                last_error = OpenRouterTimeoutException(str(exc))
                logger.warning("openrouter_transport_retry", attempt=attempt, error=str(exc))
                if attempt < self.max_retries:
                    await asyncio.sleep(self.retry_backoff_seconds * (2 ** (attempt - 1)))
                    continue
                raise last_error
            except OpenRouterAuthenticationException:
                raise
            except Exception as exc:
                last_error = OpenRouterResponseException(str(exc))
                logger.warning("openrouter_request_retry", attempt=attempt, error=str(exc))
                if attempt < self.max_retries:
                    await asyncio.sleep(self.retry_backoff_seconds * (2 ** (attempt - 1)))
                    continue
                raise last_error

        if last_error:
            raise last_error
        raise OpenRouterException("Unknown OpenRouter failure")

    def _extract_message_content(self, response: Dict[str, Any]) -> str:
        choices = response.get("choices") or []
        if not choices:
            raise OpenRouterResponseException("OpenRouter response did not include choices")

        message = choices[0].get("message") or {}
        content = message.get("content")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts: List[str] = []
            for item in content:
                if isinstance(item, dict):
                    if "text" in item:
                        parts.append(str(item["text"]))
                    elif "content" in item:
                        parts.append(str(item["content"]))
                else:
                    parts.append(str(item))
            return "\n".join(parts)
        if content is None:
            return ""
        return str(content)

    def _extract_json_payload(self, text: str) -> Dict[str, Any]:
        stripped = text.strip()
        if not stripped:
            raise OpenRouterResponseException("OpenRouter returned an empty response")

        candidates = [stripped]
        if "```" in stripped:
            parts = stripped.split("```")
            for part in parts:
                candidate = part.strip()
                if candidate.startswith("json"):
                    candidate = candidate[4:].strip()
                if candidate.startswith("{") and candidate.endswith("}"):
                    candidates.append(candidate)

        if "{" in stripped and "}" in stripped:
            start = stripped.find("{")
            end = stripped.rfind("}")
            if start != -1 and end != -1 and end > start:
                candidates.append(stripped[start : end + 1])

        for candidate in candidates:
            try:
                parsed = json.loads(candidate)
                if isinstance(parsed, dict):
                    return parsed
            except json.JSONDecodeError:
                continue

        # If all candidates fail, try to fix common JSON issues
        logger.warning("json_parse_failed_candidates", text_preview=stripped[:200])
        
        # Try to fix trailing commas
        try:
            import re
            fixed = re.sub(r',\s*([}\]])', r'\1', stripped)
            parsed = json.loads(fixed)
            if isinstance(parsed, dict):
                logger.info("json_parse_fixed_trailing_commas")
                return parsed
        except (json.JSONDecodeError, ImportError):
            pass

        raise OpenRouterResponseException("Failed to parse OpenRouter JSON response")

    async def chat_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        schema_model: Type[T],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        reasoning_effort: Optional[str] = None,
        model: Optional[str] = None,
    ) -> T:
        """Execute a structured OpenRouter chat call and validate it with Pydantic."""

        schema = schema_model.model_json_schema()
        payload: Dict[str, Any] = {
            "model": model or self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
            "response_format": self._build_response_format(schema),
            "structured_outputs": True,
            "temperature": temperature if temperature is not None else settings.openrouter_temperature,
            "max_tokens": max_tokens if max_tokens is not None else settings.openrouter_max_tokens,
            "reasoning": {
                "effort": reasoning_effort or settings.openrouter_reasoning_effort,
                "exclude": False,
            },
        }

        try:
            response = await self._post(payload)
        except OpenRouterException:
            # Fallback to JSON mode for models that do not honor json_schema strictly.
            payload["response_format"] = {"type": "json_object"}
            payload["structured_outputs"] = False
            response = await self._post(payload)

        content = self._extract_message_content(response)
        payload_dict = self._extract_json_payload(content)
        return schema_model.model_validate(payload_dict)


_CLIENT: Optional[OpenRouterClient] = None


def get_openrouter_client() -> OpenRouterClient:
    global _CLIENT
    if _CLIENT is None:
        _CLIENT = OpenRouterClient()
    return _CLIENT


async def explain_with_openrouter(
    *,
    system_prompt: str,
    user_prompt: str,
    schema_model: Type[T],
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None,
    reasoning_effort: Optional[str] = None,
    model: Optional[str] = None,
) -> T:
    """Convenience wrapper used by agents."""

    return await get_openrouter_client().chat_structured(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        schema_model=schema_model,
        max_tokens=max_tokens,
        temperature=temperature,
        reasoning_effort=reasoning_effort,
        model=model,
    )
