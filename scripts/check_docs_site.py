#!/usr/bin/env python3
"""Validate the static Jarvis docs site links and local assets."""

from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse
import sys


ROOT = Path(__file__).resolve().parents[1]
SITE_ROOT = ROOT / "demo"
INDEX = SITE_ROOT / "index.html"
RAW_PREFIX = "/Flow-Research/jarvis/main/"
BLOB_PREFIX = "/Flow-Research/jarvis/blob/main/"


class SiteParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: set[str] = set()
        self.refs: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = {key: value for key, value in attrs if value is not None}
        if "id" in attr_map:
            self.ids.add(attr_map["id"])
        for attr in ("href", "src"):
            if attr in attr_map:
                self.refs.append((attr, attr_map[attr]))


def clean_ref(value: str) -> str:
    return value.split("?", 1)[0].split("#", 1)[0]


def local_target_exists(value: str) -> bool:
    target = clean_ref(value)
    if not target:
        return True
    return (SITE_ROOT / target).resolve().is_relative_to(SITE_ROOT) and (SITE_ROOT / target).resolve().exists()


def github_target_exists(value: str) -> bool:
    parsed = urlparse(value)
    if parsed.netloc == "github.com" and parsed.path == "/Flow-Research/jarvis":
        return True
    if parsed.netloc == "github.com" and parsed.path.startswith(BLOB_PREFIX):
        target = parsed.path.removeprefix(BLOB_PREFIX)
        return (ROOT / target).exists()
    if parsed.netloc == "raw.githubusercontent.com" and parsed.path.startswith(RAW_PREFIX):
        target = parsed.path.removeprefix(RAW_PREFIX)
        return (ROOT / target).exists()
    return False


def main() -> int:
    parser = SiteParser()
    parser.feed(INDEX.read_text(encoding="utf-8"))
    failures: list[str] = []

    for attr, value in parser.refs:
        if value.startswith("#"):
            fragment = value[1:]
            if fragment and fragment not in parser.ids:
                failures.append(f"{INDEX.relative_to(ROOT)}: missing fragment target {value}")
            continue
        if value.startswith("./"):
            if not local_target_exists(value):
                failures.append(f"{INDEX.relative_to(ROOT)}: broken local {attr}: {value}")
            continue
        if value.startswith("https://"):
            if not github_target_exists(value):
                failures.append(f"{INDEX.relative_to(ROOT)}: unsupported or broken external {attr}: {value}")
            continue
        if value.startswith("mailto:"):
            continue
        failures.append(f"{INDEX.relative_to(ROOT)}: unsupported {attr}: {value}")

    if failures:
        print("\n".join(failures))
        return 1

    print("docs site ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
