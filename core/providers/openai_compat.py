import httpx
from .base import Provider


class OpenAICompatProvider(Provider):
    def __init__(self, base_url: str, api_key: str, timeout: int = 60):
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._timeout = timeout

    def complete(self, messages: list[dict], model: str) -> str:
        if not self._api_key:
            raise ValueError("No API key set — open Settings and add your key.")
        resp = httpx.post(
            f"{self._base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self._api_key}"},
            json={"model": model, "messages": messages},
            timeout=self._timeout,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
