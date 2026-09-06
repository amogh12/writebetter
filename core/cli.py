"""Smoke test: uv run python -m core.cli "text to rewrite" """
import sys
from core.config import load_config, get_active_provider_cfg, make_provider
from core.variants import get_variants


def main() -> None:
    text = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Hello this is test sentence with bad grammar."
    cfg = load_config()
    provider_cfg = get_active_provider_cfg(cfg)
    if not provider_cfg:
        print("ERROR: No active provider in config.json", file=sys.stderr)
        sys.exit(1)

    print(f"Provider: {provider_cfg['id']}  Model: {provider_cfg['model']}")
    provider = make_provider(provider_cfg)
    variants = get_variants(
        provider,
        provider_cfg["model"],
        text,
        cfg.get("default_instructions", ""),
        cfg.get("num_variants", 3),
    )
    for i, v in enumerate(variants, 1):
        print(f"\n[{i}] {v}")


if __name__ == "__main__":
    main()
