#!/usr/bin/env python3
"""Validate the static Jarvis docs site links and local assets."""

import json
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
SITE_ROOT = ROOT / "demo"
OPENAPI_SOURCE = ROOT / "docs" / "openapi" / "jarvis-openapi.yaml"
OPENAPI_SITE_COPY = SITE_ROOT / "openapi" / "jarvis-openapi.yaml"
RAW_PREFIX = "/Flow-Research/jarvis/main/"
BLOB_PREFIX = "/Flow-Research/jarvis/blob/main/"
SOURCE_BASE = "https://github.com/Flow-Research/jarvis/blob/main/"
VOID_TAGS = {
    "area",
    "base",
    "br",
    "col",
    "embed",
    "hr",
    "img",
    "input",
    "link",
    "meta",
    "param",
    "source",
    "track",
    "wbr",
}
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
GUIDE_SOURCE_REFS = {
    SITE_ROOT / "guides" / "index.html": (
        "docs/examples/protocol-records.md",
        "docs/examples/existing-agent-compatibility.md",
        "docs/protocol/15-openapi-communication-binding.md",
    ),
    SITE_ROOT / "guides" / "implementer.html": (
        "docs/protocol/15-openapi-communication-binding.md",
        "docs/protocol/11-core-protocol-objects.md",
        "docs/conformance/checklist.md",
    ),
    SITE_ROOT / "guides" / "existing-agent.html": (
        "docs/examples/existing-agent-compatibility.md",
        "docs/examples/implementation-proof/native-coding-agent/README.md",
        "docs/protocol/16-positioning-adoption-lock.md",
    ),
    SITE_ROOT / "guides" / "request-review-takeover.html": (
        "docs/protocol/12-request-protocol.md",
        "docs/protocol/11-core-protocol-objects.md",
        "docs/conformance/failure-modes.md",
    ),
    SITE_ROOT / "guides" / "evidence-learning.html": (
        "docs/protocol/13-contribution-evidence-learning.md",
        "docs/examples/protocol-records.md",
        "docs/conformance/failure-modes.md",
    ),
    SITE_ROOT / "guides" / "extensions.html": (
        "docs/protocol/15-openapi-communication-binding.md",
        "docs/protocol/14-protocol-lock.md",
        "docs/protocol/11-core-protocol-objects.md",
    ),
    SITE_ROOT / "guides" / "protocol-errors.html": (
        "docs/protocol/15-openapi-communication-binding.md",
        "docs/conformance/failure-modes.md",
        "docs/openapi/jarvis-openapi.yaml",
    ),
    SITE_ROOT / "guides" / "examples.html": (
        "docs/examples/protocol-records.md",
        "docs/examples/evidence-packs/existing-agent-review/README.md",
        "docs/examples/evidence-packs/existing-agent-takeover/README.md",
        "docs/conformance/fixtures/valid/golden-path.json",
        "docs/conformance/fixtures/valid/takeover-path.json",
    ),
}
GUIDE_BOUNDARY_REQUIRED_TEXT = (
    "Hosts own",
    "runtime",
    "model routing",
    "tool execution",
    "auth",
    "storage",
    "UI",
    "billing",
    "scoring",
    "payment",
    "deployment",
    "host workflow",
)
GUIDE_INDEX_LINKS = (
    "./implementer.html",
    "./existing-agent.html",
    "./request-review-takeover.html",
    "./evidence-learning.html",
    "./extensions.html",
    "./protocol-errors.html",
    "./examples.html",
)


class SiteParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: set[str] = set()
        self.refs: list[tuple[str, str, str]] = []
        self.source_list_refs: list[tuple[str, str, str]] = []
        self.code_samples: list[str] = []
        self._source_list_depth = 0
        self._code_sample_depth = 0
        self._current_code_sample: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = {key: value for key, value in attrs if value is not None}
        classes = set(attr_map.get("class", "").split())
        in_source_list = self._source_list_depth > 0 or "source-list" in classes
        if in_source_list and tag not in VOID_TAGS:
            self._source_list_depth += 1
        if tag == "pre" and "code-sample" in classes and self._code_sample_depth == 0:
            self._code_sample_depth = 1
            self._current_code_sample = []
        elif self._code_sample_depth > 0 and tag not in VOID_TAGS:
            self._code_sample_depth += 1
        if "id" in attr_map:
            self.ids.add(attr_map["id"])
        for attr in ("href", "src"):
            if attr in attr_map:
                self.refs.append((tag, attr, attr_map[attr]))
                if in_source_list:
                    self.source_list_refs.append((tag, attr, attr_map[attr]))

    def handle_endtag(self, tag: str) -> None:
        if self._source_list_depth > 0:
            self._source_list_depth -= 1
        if self._code_sample_depth > 0:
            self._code_sample_depth -= 1
            if self._code_sample_depth == 0:
                self.code_samples.append("".join(self._current_code_sample).strip())
                self._current_code_sample = []

    def handle_data(self, data: str) -> None:
        if self._code_sample_depth > 0:
            self._current_code_sample.append(data)


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
        failures.append(f"{path.relative_to(ROOT)}: missing required site page")
        return ""
    return path.read_text(encoding="utf-8")


def page_hrefs(parsed: dict[Path, SiteParser], path: Path) -> set[str]:
    parser = parsed.get(path)
    if parser is None:
        return set()
    return {
        clean_ref(value)
        for _tag, attr, value in parser.refs
        if attr == "href"
    }


def has_field_path(record: object, path: tuple[str, ...]) -> bool:
    current = record
    for part in path:
        if not isinstance(current, dict) or part not in current:
            return False
        current = current[part]
    return current is not None


def validate_examples_json_samples(
    path: Path,
    parser: SiteParser | None,
    failures: list[str],
) -> None:
    if parser is None:
        failures.append(f"{path.relative_to(ROOT)}: missing parsed examples page")
        return

    parsed_samples = []
    for index, sample in enumerate(parser.code_samples, start=1):
        try:
            parsed_samples.append(json.loads(sample))
        except json.JSONDecodeError as exc:
            failures.append(
                f"{path.relative_to(ROOT)}: code sample {index} is not valid JSON: {exc.msg}"
            )

    by_object_type = {
        sample.get("object_type"): sample
        for sample in parsed_samples
        if isinstance(sample, dict) and isinstance(sample.get("object_type"), str)
    }
    evidence_samples = [
        sample for sample in parsed_samples
        if isinstance(sample, dict) and isinstance(sample.get("evidence_manifest"), dict)
    ]

    required_object_paths = {
        "WorkSession": (
            ("record", "id"),
            ("record", "protocol_version"),
            ("record", "created_by_actor_id"),
            ("record", "human_worker_id"),
            ("record", "agent_worker_id"),
            ("record", "policy_id"),
            ("record", "status"),
            ("record", "revision"),
            ("record", "last_event_hash"),
            ("record", "created_at"),
            ("record", "updated_at"),
        ),
        "PolicyDecision": (
            ("record", "id"),
            ("record", "work_session_id"),
            ("record", "actor_id"),
            ("record", "policy_id"),
            ("record", "requested_action"),
            ("record", "normalized_action_hash"),
            ("record", "risk_class"),
            ("record", "result"),
            ("record", "created_at"),
            ("record", "request_id"),
        ),
        "Request": (
            ("record", "id"),
            ("record", "protocol_version"),
            ("record", "work_session_id"),
            ("record", "requester_actor_id"),
            ("record", "requester_worker_id"),
            ("record", "target_human_worker_id"),
            ("record", "policy_decision_id"),
            ("record", "type"),
            ("record", "status"),
            ("record", "blocking_scope"),
            ("record", "reason_code"),
            ("record", "reason_summary"),
            ("record", "requested_action"),
            ("record", "requested_outcome"),
            ("record", "risk_class"),
            ("record", "human_decision_needed"),
            ("record", "options"),
            ("record", "default_if_no_response"),
            ("record", "created_at"),
            ("record", "expires_at"),
            ("record", "resolved_at"),
            ("record", "resolved_by_review_id"),
        ),
        "Review": (
            ("record", "id"),
            ("record", "work_session_id"),
            ("record", "reviewer_actor_id"),
            ("record", "reviewer_worker_id"),
            ("record", "target_ref"),
            ("record", "decision"),
            ("record", "created_at"),
            ("record", "approval_scope"),
            ("record", "approval_scope", "request_id"),
            ("record", "approval_scope", "review_id"),
            ("record", "approval_scope", "request_revision"),
            ("record", "approval_scope", "request_event_hash"),
            ("record", "approval_scope", "normalized_action_hash"),
            ("record", "approval_scope", "approved_action"),
            ("record", "approval_scope", "allowed_scope"),
            ("record", "approval_scope", "denied_scope"),
            ("record", "approval_scope", "expires_at"),
            ("record", "approval_scope", "max_uses"),
            ("record", "approval_scope", "applies_to_work_session_id"),
            ("record", "approval_scope", "applies_to_actor_id"),
        ),
        "Takeover": (
            ("record", "id"),
            ("record", "work_session_id"),
            ("record", "requested_by_actor_id"),
            ("record", "controlling_actor_id"),
            ("record", "request_id"),
            ("record", "affected_scope"),
            ("record", "affected_scope", "artifact_refs"),
            ("record", "reason"),
            ("record", "lock_epoch"),
            ("record", "state"),
            ("record", "created_at"),
            ("record", "resumed_by_actor_id"),
            ("record", "reconciliation_refs"),
            ("record", "resolved_at"),
        ),
        "Contribution": (
            ("record", "id"),
            ("record", "work_session_id"),
            ("record", "contributor_refs"),
            ("record", "contributor_type"),
            ("record", "contribution_type"),
            ("record", "event_refs"),
            ("record", "created_at"),
        ),
        "OutcomeReport": (
            ("record", "id"),
            ("record", "work_session_id"),
            ("record", "source_ref"),
            ("record", "reporter_ref"),
            ("record", "accepted_by_actor_id"),
            ("record", "outcome"),
            ("record", "learning_record_refs"),
            ("record", "received_at"),
        ),
        "LearningRecord": (
            ("record", "id"),
            ("record", "work_session_id"),
            ("record", "created_by_actor_id"),
            ("record", "subject_type"),
            ("record", "subject_ref"),
            ("record", "lesson_type"),
            ("record", "source_event_refs"),
            ("record", "review_state"),
            ("record", "scope"),
            ("record", "created_at"),
        ),
    }

    for object_type, required_paths in required_object_paths.items():
        sample = by_object_type.get(object_type)
        if sample is None:
            failures.append(f"{path.relative_to(ROOT)}: missing JSON sample for {object_type}")
            continue
        for field_path in required_paths:
            if not has_field_path(sample, field_path):
                joined = ".".join(field_path)
                failures.append(f"{path.relative_to(ROOT)}: {object_type} sample missing {joined}")

    if not evidence_samples:
        failures.append(f"{path.relative_to(ROOT)}: missing EvidenceManifest JSON sample")
        return
    evidence_sample = evidence_samples[0]
    for field_path in (
        ("evidence_manifest", "id"),
        ("evidence_manifest", "work_session_id"),
        ("evidence_manifest", "generated_by_actor_id"),
        ("evidence_manifest", "objective"),
        ("evidence_manifest", "event_chain_root"),
        ("evidence_manifest", "evidence_item_refs"),
        ("evidence_manifest", "policy_decision_refs"),
        ("evidence_manifest", "request_refs"),
        ("evidence_manifest", "review_refs"),
        ("evidence_manifest", "takeover_refs"),
        ("evidence_manifest", "contribution_refs"),
        ("evidence_manifest", "export_profile"),
        ("evidence_manifest", "generated_at"),
    ):
        if not has_field_path(evidence_sample, field_path):
            joined = ".".join(field_path)
            failures.append(f"{path.relative_to(ROOT)}: EvidenceManifest sample missing {joined}")


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

    for page_group, source_ref_map in (
        ("conformance", CONFORMANCE_SOURCE_REFS),
        ("guide", GUIDE_SOURCE_REFS),
    ):
        for path, source_refs in source_ref_map.items():
            if not path.exists():
                failures.append(f"{path.relative_to(ROOT)}: missing {page_group} site page")
                continue
            page_text = path.read_text(encoding="utf-8")
            page_parser = parsed[path]
            if not any(
                tag == "a" and attr == "href" and value == "#main-content"
                for tag, attr, value in page_parser.refs
            ):
                failures.append(f"{path.relative_to(ROOT)}: missing skip link")
            if "main-content" not in page_parser.ids:
                failures.append(f"{path.relative_to(ROOT)}: missing main content target")
            if page_group == "guide":
                for required_boundary_text in GUIDE_BOUNDARY_REQUIRED_TEXT:
                    if required_boundary_text not in page_text:
                        failures.append(
                            f"{path.relative_to(ROOT)}: missing guide boundary text {required_boundary_text}"
                        )
            page_refs = {clean_ref(value) for _tag, _attr, value in page_parser.source_list_refs}
            for source_ref in source_refs:
                source_path = ROOT / source_ref
                if not source_path.exists():
                    failures.append(f"{source_ref}: missing {page_group} source contract")
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

    required_site_text(SITE_ROOT / "index.html", failures)
    home_hrefs = page_hrefs(parsed, SITE_ROOT / "index.html")
    for guide_link in (
        "./guides/",
        "./guides/implementer.html",
        "./guides/existing-agent.html",
        "./guides/request-review-takeover.html",
        "./guides/evidence-learning.html",
        "./guides/extensions.html",
        "./guides/protocol-errors.html",
        "./guides/examples.html",
    ):
        if guide_link not in home_hrefs:
            failures.append(f"demo/index.html: missing guide link {guide_link}")

    guide_index = required_site_text(SITE_ROOT / "guides" / "index.html", failures)
    guide_index_hrefs = page_hrefs(parsed, SITE_ROOT / "guides" / "index.html")
    for guide_link in GUIDE_INDEX_LINKS:
        if guide_link not in guide_index_hrefs:
            failures.append(f"demo/guides/index.html: missing guide index link {guide_link}")
    for required_text in (
        "Implementer guide",
        "Existing-agent compatibility",
        "Request, Review, Takeover",
        "Evidence and Learning",
        "Extensions",
        "Protocol errors",
        "Protocol examples",
    ):
        if required_text not in guide_index:
            failures.append(f"demo/guides/index.html: missing {required_text}")

    implementer_page = required_site_text(SITE_ROOT / "guides" / "implementer.html", failures)
    for required_text in (
        "Must store",
        "Must emit",
        "Must validate",
        "Must reject",
        "Jarvis-Expected-WorkSession-Revision",
        "Jarvis-Previous-Event-Hash",
        "PolicyDecision before an AgentWorker action",
        "Hosts own UI, auth, storage, runtime behavior, model routing, tool execution",
    ):
        if required_text not in implementer_page:
            failures.append(f"demo/guides/implementer.html: missing {required_text}")

    existing_agent_guide = required_site_text(SITE_ROOT / "guides" / "existing-agent.html", failures)
    for required_text in (
        "Existing agents keep native execution",
        "Jarvis does not replace the agent",
        "Worker and Actor refs",
        "PolicyDecision before every AgentWorker action",
        "Jarvis-compatible does not mean Jarvis-certified",
    ):
        if required_text not in existing_agent_guide:
            failures.append(f"demo/guides/existing-agent.html: missing {required_text}")

    control_guide = required_site_text(SITE_ROOT / "guides" / "request-review-takeover.html", failures)
    for required_text in (
        "Request is a structured scoped deferral",
        "ApprovalScope",
        "lock_epoch",
        "missing mutating headers",
        "stale AgentWorker continuation",
        "Request created with blocking_scope",
    ):
        if required_text not in control_guide:
            failures.append(f"demo/guides/request-review-takeover.html: missing {required_text}")

    evidence_guide = required_site_text(SITE_ROOT / "guides" / "evidence-learning.html", failures)
    for required_text in (
        "Contribution",
        "EvidenceManifest",
        "LearningRecord",
        "MemoryProposal",
        "SkillProposal",
        "OutcomeReport",
        "OutcomeReport whose source WorkSession is not terminal",
    ):
        if required_text not in evidence_guide:
            failures.append(f"demo/guides/evidence-learning.html: missing {required_text}")

    extension_guide = required_site_text(SITE_ROOT / "guides" / "extensions.html", failures)
    for required_text in (
        "Extensions MUST use a namespace",
        "Extensions MUST NOT override core Jarvis fields",
        "unsupported_capability",
        "invalid_extension_namespace",
        "extension_core_field_override",
    ):
        if required_text not in extension_guide:
            failures.append(f"demo/guides/extensions.html: missing {required_text}")

    errors_guide = required_site_text(SITE_ROOT / "guides" / "protocol-errors.html", failures)
    for required_text in (
        "error_id",
        "protocol_version",
        "object_type",
        "field",
        "reason",
        "remediation",
        "trace_id",
        "outcome_report_requires_terminal_source",
        "Do not include host-private response fields",
    ):
        if required_text not in errors_guide:
            failures.append(f"demo/guides/protocol-errors.html: missing {required_text}")

    examples_guide = required_site_text(SITE_ROOT / "guides" / "examples.html", failures)
    for required_text in (
        "Minimal WorkSession record flow",
        "PolicyDecision before AgentWorker action",
        "Scoped Request and Review resolution",
        "Takeover and reconciliation",
        "Contribution and EvidenceManifest export",
        "OutcomeReport to LearningRecord",
        '"object_type": "WorkSession"',
        '"object_type": "PolicyDecision"',
        '"object_type": "Request"',
        '"object_type": "Review"',
        '"object_type": "Takeover"',
        '"object_type": "Contribution"',
        '"evidence_manifest"',
        '"object_type": "OutcomeReport"',
        '"object_type": "LearningRecord"',
        '"work_session_id"',
        '"policy_decision_id"',
        '"resolved_by_review_id"',
        '"lock_epoch"',
        '"learning_record_refs"',
    ):
        if required_text not in examples_guide:
            failures.append(f"demo/guides/examples.html: missing {required_text}")
    validate_examples_json_samples(
        SITE_ROOT / "guides" / "examples.html",
        parsed.get(SITE_ROOT / "guides" / "examples.html"),
        failures,
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
