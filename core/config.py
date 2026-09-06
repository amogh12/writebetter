import json
import keyring
import sys
from pathlib import Path

def _config_path() -> Path:
    if getattr(sys, "frozen", False):
        # Running as PyInstaller bundle — keep config next to the exe
        return Path(sys.executable).parent / "config.json"
    return Path(__file__).parent.parent / "config.json"

_CONFIG_PATH = _config_path()


def load_config() -> dict:
    with open(_CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)


def save_config(cfg: dict) -> None:
    with open(_CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)


def get_api_key(key_ref: str) -> str:
    return keyring.get_password("writebetter", key_ref) or ""


def set_api_key(key_ref: str, key: str) -> None:
    keyring.set_password("writebetter", key_ref, key)


def get_active_provider_cfg(cfg: dict) -> dict | None:
    active = cfg.get("active_provider")
    for p in cfg.get("providers", []):
        if p["id"] == active:
            return p
    return None


def make_provider(provider_cfg: dict):
    from core.providers.openai_compat import OpenAICompatProvider
    from core.providers.anthropic import AnthropicProvider

    key_ref = provider_cfg.get("key_ref", "")
    api_key = get_api_key(key_ref)
    base_url = provider_cfg["base_url"]
    timeout = int(provider_cfg.get("timeout", 60))

    if provider_cfg["type"] == "anthropic":
        return AnthropicProvider(base_url, api_key, timeout=timeout)
    return OpenAICompatProvider(base_url, api_key, timeout=timeout)
