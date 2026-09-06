import json
from .prompts import build_messages
from .providers.base import Provider


def get_variants(
    provider: Provider,
    model: str,
    text: str,
    instructions: str,
    n: int,
) -> list[str]:
    messages = build_messages(text, instructions, n)

    def _parse(raw: str) -> list[str]:
        raw = raw.strip()
        start = raw.find("[")
        end = raw.rfind("]") + 1
        if start == -1 or end == 0:
            raise ValueError("No JSON array in response")
        parsed = json.loads(raw[start:end])
        if len(parsed) != n:
            raise ValueError(f"Expected {n} variants, got {len(parsed)}")
        return parsed

    raw = provider.complete(messages, model)
    try:
        return _parse(raw)
    except (ValueError, json.JSONDecodeError):
        raw2 = provider.complete(messages, model)
        return _parse(raw2)
