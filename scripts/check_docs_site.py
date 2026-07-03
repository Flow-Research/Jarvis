#!/usr/bin/env python3
"""Validate the static Jarvis docs site links and local assets."""

from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse
import sys


ROOT = Path(__file__).resolve().parents[1]
SITE_ROOT = ROOT / "demo"
OPENAPI_SOURCE = ROOT / "docs" / "openapi" / "jarvis-openapi.yaml"
OPENAPI_SITE_COPY = SITE_ROOT / "openapi" / "jarvis-openapi.yaml"
RAW_PREFIX = "/Flow-Research/jarvis/main/"
BLOB_PREFIX = "/Flow-Research/jarvis/blob/main/"


class SiteParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: set[str] = set()
        self.refs: list[tuple[str, str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = {key: value for key, value in attrs if value is not None}
        if "id" in attr_map:
            self.ids.add(attr_map["id"])
        for attr in ("href", "src"):
            if attr in attr_map:
                self.refs.append((tag, attr, attr_map[attr]))


def clean_ref(value: str) -> str:
    return value.split("?", 1)[0].split("#", 1)[0]


def parse_html(path: Path) -> SiteParser:
    parser = SiteParser()
    parser.feed(path.read_text(encoding="utf-8"))
    return parser


def local_target(value: str, source: Path) -> Path:
    target = clean_ref(value)
    resolved = (source.parent / target).resolve()
    if resolved.is_dir():
        return resolved / "index.html"
    return resolved


def local_target_exists(value: str, source: Path) -> bool:
    target = clean_ref(value)
    if not target:
        return True
    resolved = local_target(value, source)
    return resolved.is_relative_to(SITE_ROOT) and resolved.exists()


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
    html_files = sorted(SITE_ROOT.rglob("*.html"))
    parsed = {path: parse_html(path) for path in html_files}
    failures: list[str] = []

    if not OPENAPI_SOURCE.exists():
        failures.append(f"{OPENAPI_SOURCE.relative_to(ROOT)}: missing OpenAPI source file")
    elif not OPENAPI_SITE_COPY.exists():
        failures.append(f"{OPENAPI_SITE_COPY.relative_to(ROOT)}: missing OpenAPI site snapshot")
    elif OPENAPI_SITE_COPY.read_bytes() != OPENAPI_SOURCE.read_bytes():
        failures.append(
            f"{OPENAPI_SITE_COPY.relative_to(ROOT)}: OpenAPI site snapshot differs from docs/openapi/jarvis-openapi.yaml"
        )

    for path, parser in parsed.items():
        for tag, attr, value in parser.refs:
            if value.startswith("#"):
                fragment = value[1:]
                if fragment and fragment not in parser.ids:
                    failures.append(f"{path.relative_to(ROOT)}: missing fragment target {value}")
                continue
            if tag == "iframe" and value.startswith("https://"):
                failures.append(f"{path.relative_to(ROOT)}: iframe src MUST be local: {value}")
                continue
            if path == SITE_ROOT / "openapi" / "index.html" and tag == "iframe":
                iframe_target = local_target(value, path)
                if iframe_target != OPENAPI_SITE_COPY:
                    failures.append(
                        f"{path.relative_to(ROOT)}: OpenAPI iframe MUST render {OPENAPI_SITE_COPY.relative_to(ROOT)}"
                    )
                continue
            if value.startswith("https://"):
                if not github_target_exists(value):
                    failures.append(f"{path.relative_to(ROOT)}: unsupported or broken external {attr}: {value}")
                continue
            if value.startswith("mailto:"):
                continue

            if not local_target_exists(value, path):
                failures.append(f"{path.relative_to(ROOT)}: broken local {attr}: {value}")
                continue

            parsed_ref = clean_ref(value)
            fragment = value.split("#", 1)[1] if "#" in value else ""
            target = local_target(parsed_ref, path) if parsed_ref else path
            if fragment and target.suffix == ".html":
                target_parser = parsed.get(target)
                if target_parser is None:
                    failures.append(f"{path.relative_to(ROOT)}: unparsed HTML target {value}")
                elif fragment not in target_parser.ids:
                    failures.append(f"{path.relative_to(ROOT)}: missing target fragment {value}")

    if failures:
        print("\n".join(failures))
        return 1

    print("docs site ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
