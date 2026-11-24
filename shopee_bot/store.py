import json

from . import config


def load_seen() -> set[str]:
    if config.STATE_FILE.exists():
        return set(json.loads(config.STATE_FILE.read_text()))
    return set()


def save_seen(seen: set[str]):
    config.STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    config.STATE_FILE.write_text(json.dumps(sorted(seen), ensure_ascii=False))
