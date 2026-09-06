import httpx
from .base import Provider


class AnthropicProvider(Provider):
    def __init__(self, base_url: str, api_key: str, timeout: int = 60):
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._timeout = timeout

    def complete(self, messages: list[dict], model: str) -> str:
        system: str | None = None
        msgs = []
        for m in messages:
            if m["role"] == "system":
                system = m["content"]
            else:
                msgs.append(m)

        body: dict = {"model": model, "max_tokens": 4096, "messages": msgs}
        if system:
            body["system"] = system

        resp = httpx.post(
            f"{self._base_url}/v1/messages",
            headers={
                "x-api-key": self._api_key,
                "anthropic-version": "2023-06-01",
            },
            json=body,
            timeout=self._timeout,
        )
        resp.raise_for_status()
        return resp.json()["content"][0]["text"]
