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
SOURCE_BASE = "https://github.com/Flow-Research/jarvis/blob/main/"
CONFORMANCE_SOURCE_REFS = {
    SITE_ROOT / "conformance" / "index.html": (
        "docs/conformance/README.md",
        "docs/conformance/checklist.md",
        "docs/conformance/fixtures/README.md",
    ),
    SITE_ROOT / "conformance" / "golden-path.html": (
        "docs/conformance/golden-path.md",
        "docs/conformance/fixtures/valid/golden-path.json",
        "docs/conformance/fixtures/invalid/stale-takeover-continuation.json",
    ),
    SITE_ROOT / "conformance" / "failure-modes.html": (
        "docs/conformance/failure-modes.md",
        "docs/conformance/fixtures/README.md",
    ),
    SITE_ROOT / "conformance" / "fixtures.html": (
        "docs/conformance/fixtures/README.md",
        "scripts/check_conformance_fixtures.py",
    ),
    SITE_ROOT / "conformance" / "compatibility-claim.html": (
        "docs/conformance/checklist.md",
        "docs/releases/v0.1.0.md",
    ),
    SITE_ROOT / "conformance" / "existing-agent-compatibility.html": (
        "docs/examples/existing-agent-compatibility.md",
        "docs/conformance/existing-agent-proof-plan.md",
    ),
    SITE_ROOT / "conformance" / "compatible-host-mapping.html": (
        "docs/examples/compatible-host-mapping.md",
        "docs/conformance/compatibility-mapping.md",
    ),
}


class SiteParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: set[str] = set()
        self.refs: list[tuple[str, str, str]] = []
        self.source_list_refs: list[tuple[str, str, str]] = []
        self._source_list_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = {key: value for key, value in attrs if value is not None}
        classes = set(attr_map.get("class", "").split())
        if "source-list" in classes:
            self._source_list_depth = 1
        elif self._source_list_depth > 0:
            self._source_list_depth += 1
        if "id" in attr_map:
            self.ids.add(attr_map["id"])
        for attr in ("href", "src"):
            if attr in attr_map:
                self.refs.append((tag, attr, attr_map[attr]))
                if self._source_list_depth > 0:
                    self.source_list_refs.append((tag, attr, attr_map[attr]))

    def handle_endtag(self, tag: str) -> None:
        if self._source_list_depth > 0:
            self._source_list_depth -= 1


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


def required_site_text(path: Path, failures: list[str]) -> str:
    if not path.exists():
        failures.append(f"{path.relative_to(ROOT)}: missing conformance site page")
        return ""
    return path.read_text(encoding="utf-8")


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

    for path, source_refs in CONFORMANCE_SOURCE_REFS.items():
        if not path.exists():
            failures.append(f"{path.relative_to(ROOT)}: missing conformance site page")
            continue
        page_text = path.read_text(encoding="utf-8")
        if 'class="skip-link" href="#main-content"' not in page_text:
            failures.append(f"{path.relative_to(ROOT)}: missing skip link")
        if 'id="main-content"' not in page_text:
            failures.append(f"{path.relative_to(ROOT)}: missing main content target")
        page_refs = {clean_ref(value) for _tag, _attr, value in parsed[path].source_list_refs}
        for source_ref in source_refs:
            source_path = ROOT / source_ref
            if not source_path.exists():
                failures.append(f"{source_ref}: missing conformance source contract")
                continue
            source_url = f"{SOURCE_BASE}{source_ref}"
            if source_url not in page_refs:
                failures.append(f"{path.relative_to(ROOT)}: missing source contract link {source_ref}")

    conformance_index = required_site_text(SITE_ROOT / "conformance" / "index.html", failures)
    for required_text in ("Fixture-backed proof", "Checklist-only proof"):
        if required_text not in conformance_index:
            failures.append(f"demo/conformance/index.html: missing {required_text}")

    claim_page = required_site_text(SITE_ROOT / "conformance" / "compatibility-claim.html", failures)
    for claim_field in (
        "Implementation:",
        "Protocol compatibility:",
        "Conformance surface:",
        "Verification date:",
        "Verifier:",
        "Evidence:",
    ):
        if claim_field not in claim_page:
            failures.append(f"demo/conformance/compatibility-claim.html: missing claim field {claim_field}")
    for rejected_claim in (
        "Certified Jarvis implementation",
        "Official Jarvis host",
        "Production adoption proven by Jarvis",
        "Foundation governance approval",
    ):
        if rejected_claim not in claim_page:
            failures.append(f"demo/conformance/compatibility-claim.html: missing rejected claim {rejected_claim}")
    for required_text in (
        "fixture or checklist basis",
        "self-attested",
        "Actor/body binding",
        "Protocol error envelope",
        "Forbidden host-private export rejection",
    ):
        if required_text not in claim_page:
            failures.append(f"demo/conformance/compatibility-claim.html: missing {required_text}")

    golden_path_page = required_site_text(SITE_ROOT / "conformance" / "golden-path.html", failures)
    for required_text in (
        'Every actor-bearing mutation body matches <code>Jarvis-Actor-Id</code>',
        "Stale Takeover rejection is covered by the stale Takeover fixture",
    ):
        if required_text not in golden_path_page:
            failures.append(f"demo/conformance/golden-path.html: missing {required_text}")

    failure_modes_page = required_site_text(SITE_ROOT / "conformance" / "failure-modes.html", failures)
    for required_text in (
        "Fixture-backed rejection ids",
        "Checklist-only protocol error ids",
        "Public conformance reports MUST NOT claim fixture coverage",
        "Required error envelope",
        "Protocol error responses MUST exclude host-private fields",
    ):
        if required_text not in failure_modes_page:
            failures.append(f"demo/conformance/failure-modes.html: missing {required_text}")

    existing_agent_page = required_site_text(SITE_ROOT / "conformance" / "existing-agent-compatibility.html", failures)
    for required_text in (
        "Existing agents keep native execution",
        "Hosts own native agent runtime",
        "Jarvis does not replace the agent",
    ):
        if required_text not in existing_agent_page:
            failures.append(f"demo/conformance/existing-agent-compatibility.html: missing {required_text}")

    fixtures_page = required_site_text(SITE_ROOT / "conformance" / "fixtures.html", failures)
    fixtures_parser = parsed.get(SITE_ROOT / "conformance" / "fixtures.html")
    fixture_refs = {
        clean_ref(value)
        for _tag, _attr, value in (fixtures_parser.refs if fixtures_parser else [])
    }
    for fixture_path in sorted((ROOT / "docs" / "conformance" / "fixtures").rglob("*.json")):
        fixture_name = fixture_path.name
        if fixture_name not in fixtures_page:
            failures.append(f"demo/conformance/fixtures.html: missing fixture {fixture_name}")
        fixture_ref = fixture_path.relative_to(ROOT).as_posix()
        fixture_url = f"{SOURCE_BASE}{fixture_ref}"
        if fixture_url not in fixture_refs:
            failures.append(f"demo/conformance/fixtures.html: missing fixture link {fixture_ref}")
    for required_text in (
        "Valid fixtures omit",
        "Invalid fixtures include one primary",
    ):
        if required_text not in fixtures_page:
            failures.append(f"demo/conformance/fixtures.html: missing {required_text}")

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
