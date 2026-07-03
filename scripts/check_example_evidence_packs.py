#!/usr/bin/env python3
"""Validate public Jarvis protocol evidence packs."""

from __future__ import annotations

from pathlib import Path
import json
import sys
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
PACK_ROOT = ROOT / "docs" / "examples" / "evidence-packs"
PYTHON_PACKAGE_SRC = ROOT / "packages" / "python" / "src"
PROTOCOL_VERSION = "v0.1"
VALID_SOURCE_FIXTURES = {
    "docs/conformance/fixtures/valid/golden-path.json": "valid-golden-path-v01",
    "docs/conformance/fixtures/valid/takeover-path.json": "valid-takeover-path-v01",
}
MANIFEST_KEYS = {
    "pack_id",
    "protocol_version",
    "title",
    "description",
    "source_fixture",
    "source_contract_refs",
    "host_shape_ref",
    "pack_limits",
    "records",
    "evidence_manifests",
    "event_chains",
    "operation_headers",
}
RECORD_ENVELOPE_KEYS = {"object_type", "record", "context"}
EVIDENCE_MANIFEST_ENVELOPE_KEYS = {"evidence_manifest", "work_session"}
EVENT_CHAIN_ENVELOPE_KEYS = {"events"}

sys.path.insert(0, str(PYTHON_PACKAGE_SRC))

import jarvis_protocol  # noqa: E402


class EvidencePackError(Exception):
    """Raised when a public evidence pack violates its protocol contract."""


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise EvidencePackError(f"{rel(path)}: invalid JSON: {exc}") from exc


def assert_closed_object(path: Path, value: Any, allowed: set[str], label: str) -> None:
    if not isinstance(value, dict):
        raise EvidencePackError(f"{rel(path)}: {label} MUST be an object")
    extra = sorted(set(value) - allowed)
    if extra:
        raise EvidencePackError(f"{rel(path)}: {label} contains unsupported fields: {', '.join(extra)}")
    forbidden = jarvis_protocol.find_forbidden_host_private_field(value)
    if forbidden:
        raise EvidencePackError(f"{rel(path)}: {label} contains host-private field {forbidden}")


def resolve_local_path(pack_dir: Path, value: Any) -> Path:
    if not isinstance(value, str) or not value:
        raise EvidencePackError(f"{rel(pack_dir)}: path values MUST be nonempty strings")
    path = (pack_dir / value).resolve()
    if not path.is_relative_to(pack_dir.resolve()):
        raise EvidencePackError(f"{rel(pack_dir)}: pack paths MUST stay inside the pack")
    if not path.exists():
        raise EvidencePackError(f"{rel(path)}: referenced pack file does not exist")
    return path


def load_structured_ref(path: Path) -> Any:
    if path.suffix in {".yaml", ".yml"}:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    if path.suffix == ".json":
        return load_json(path)
    raise EvidencePackError(f"{rel(path)}: fragments are supported only for JSON and YAML refs")


def resolve_json_pointer(path: Path, document: Any, pointer: str) -> None:
    if not pointer.startswith("/"):
        raise EvidencePackError(f"{rel(path)}: source_contract_refs fragment MUST be a JSON Pointer")
    current = document
    for raw_part in pointer.strip("/").split("/"):
        part = raw_part.replace("~1", "/").replace("~0", "~")
        if isinstance(current, dict) and part in current:
            current = current[part]
            continue
        if isinstance(current, list) and part.isdigit() and int(part) < len(current):
            current = current[int(part)]
            continue
        raise EvidencePackError(f"{rel(path)}: source_contract_refs fragment does not resolve: #{pointer}")


def resolve_repo_ref(path: Path, value: Any) -> Path:
    if not isinstance(value, str) or not value:
        raise EvidencePackError(f"{rel(path)}: repository refs MUST be nonempty strings")
    local_ref, _, fragment = value.partition("#")
    if not local_ref:
        raise EvidencePackError(f"{rel(path)}: repository refs MUST include a local path")
    target = (ROOT / local_ref).resolve()
    if not target.is_relative_to(ROOT):
        raise EvidencePackError(f"{rel(path)}: repository refs MUST stay inside repo")
    if not target.exists():
        raise EvidencePackError(f"{rel(path)}: missing repository ref {value}")
    if fragment:
        resolve_json_pointer(target, load_structured_ref(target), fragment)
    return target


def resolve_fixture_ref(fixture: Any, ref: str) -> Any:
    current = fixture
    for part in ref.split("."):
        if isinstance(current, dict) and part in current:
            current = current[part]
            continue
        raise EvidencePackError(f"fixture ref {ref} does not resolve")
    return current


def assert_result(path: Path, result: Any) -> None:
    if result.valid:
        return
    first = result.errors[0] if result.errors else {}
    raise EvidencePackError(
        f"{rel(path)}: validation failed: "
        f"{first.get('error_id', 'unknown_error')} {first.get('field', '')}"
    )


def normalized_context(context: dict[str, Any]) -> dict[str, Any]:
    if "workSession" in context and "work_session" not in context:
        return {**context, "work_session": context["workSession"]}
    return context


def check_source_contract_refs(manifest_path: Path, refs: Any) -> None:
    if not isinstance(refs, list) or not refs:
        raise EvidencePackError(f"{rel(manifest_path)}: source_contract_refs MUST be nonempty")
    for ref in refs:
        resolve_repo_ref(manifest_path, ref)


def check_record_entry(
    manifest_path: Path,
    pack_dir: Path,
    fixture: dict[str, Any],
    entry: dict[str, Any],
) -> int:
    path = resolve_local_path(pack_dir, entry.get("path"))
    envelope = load_json(path)
    assert_closed_object(path, envelope, RECORD_ENVELOPE_KEYS, "record envelope")
    object_type = entry.get("object_type")
    source_ref = entry.get("source_ref")
    if envelope.get("object_type") != object_type:
        raise EvidencePackError(f"{rel(path)}: object_type mismatch")
    source_record = resolve_fixture_ref(fixture, source_ref)
    if envelope.get("record") != source_record:
        raise EvidencePackError(f"{rel(path)}: record does not match {source_ref}")
    context = envelope.get("context", {})
    if not isinstance(context, dict):
        raise EvidencePackError(f"{rel(path)}: context MUST be an object when present")
    expected_context_refs = entry.get("context_refs", {})
    if not isinstance(expected_context_refs, dict):
        raise EvidencePackError(f"{rel(manifest_path)}: context_refs MUST be an object")
    extra_context_keys = sorted(set(context) - set(expected_context_refs))
    if extra_context_keys:
        raise EvidencePackError(
            f"{rel(path)}: context contains keys without a context_ref: {', '.join(extra_context_keys)}"
        )
    for key, ref in expected_context_refs.items():
        expected = resolve_fixture_ref(fixture, ref)
        if context.get(key) != expected:
            raise EvidencePackError(f"{rel(path)}: context.{key} does not match {ref}")
    assert_result(
        path,
        jarvis_protocol.validate_protocol_record(
            object_type,
            envelope.get("record"),
            normalized_context(context),
        ),
    )
    return 1


def check_evidence_manifest_entry(
    pack_dir: Path,
    fixture: dict[str, Any],
    entry: dict[str, Any],
) -> int:
    path = resolve_local_path(pack_dir, entry.get("path"))
    envelope = load_json(path)
    assert_closed_object(
        path,
        envelope,
        EVIDENCE_MANIFEST_ENVELOPE_KEYS,
        "EvidenceManifest envelope",
    )
    manifest = envelope.get("evidence_manifest")
    work_session = envelope.get("work_session")
    manifest_ref = entry.get("source_ref")
    work_session_ref = entry.get("work_session_ref")
    if manifest != resolve_fixture_ref(fixture, manifest_ref):
        raise EvidencePackError(f"{rel(path)}: evidence_manifest does not match {manifest_ref}")
    if work_session != resolve_fixture_ref(fixture, work_session_ref):
        raise EvidencePackError(f"{rel(path)}: work_session does not match {work_session_ref}")
    assert_result(
        path,
        jarvis_protocol.validate_evidence_manifest(
            manifest,
            {"work_session": work_session},
        ),
    )
    return 1


def check_event_chain_entry(pack_dir: Path, fixture: dict[str, Any], entry: dict[str, Any]) -> int:
    path = resolve_local_path(pack_dir, entry.get("path"))
    envelope = load_json(path)
    assert_closed_object(path, envelope, EVENT_CHAIN_ENVELOPE_KEYS, "event chain envelope")
    source_refs = entry.get("source_refs")
    if not isinstance(source_refs, list) or not source_refs:
        raise EvidencePackError(f"{rel(path)}: event chain source_refs MUST be nonempty")
    expected_events = [resolve_fixture_ref(fixture, ref) for ref in source_refs]
    if envelope.get("events") != expected_events:
        raise EvidencePackError(f"{rel(path)}: events do not match source_refs")
    assert_result(path, jarvis_protocol.validate_event_hash_chain(envelope.get("events")))
    return 1


def check_header_entry(pack_dir: Path, fixture: dict[str, Any], entry: dict[str, Any]) -> int:
    path = resolve_local_path(pack_dir, entry.get("path"))
    operation = load_json(path)
    source_index = entry.get("source_operation_index")
    operations = fixture.get("operations", [])
    if not isinstance(source_index, int) or source_index < 0 or source_index >= len(operations):
        raise EvidencePackError(f"{rel(path)}: source_operation_index is invalid")
    source_operation = operations[source_index]
    if operation != source_operation:
        raise EvidencePackError(f"{rel(path)}: operation envelope does not match source operation")
    assert_result(
        path,
        jarvis_protocol.validate_operation_headers(
            operation,
            {"skip_timestamp_skew": True},
        ),
    )
    return 1


def check_manifest(manifest_path: Path) -> int:
    pack_dir = manifest_path.parent
    manifest = load_json(manifest_path)
    assert_closed_object(manifest_path, manifest, MANIFEST_KEYS, "manifest")
    if manifest.get("protocol_version") != PROTOCOL_VERSION:
        raise EvidencePackError(f"{rel(manifest_path)}: protocol_version MUST be {PROTOCOL_VERSION}")
    source_fixture_ref = manifest.get("source_fixture")
    expected_fixture_id = VALID_SOURCE_FIXTURES.get(source_fixture_ref)
    if expected_fixture_id is None:
        raise EvidencePackError(
            f"{rel(manifest_path)}: source_fixture MUST reference a valid v0.1 proof fixture"
        )
    source_fixture_path = resolve_repo_ref(manifest_path, source_fixture_ref)
    fixture = load_json(source_fixture_path)
    if (
        fixture.get("fixture_id") != expected_fixture_id
        or fixture.get("protocol_version") != PROTOCOL_VERSION
        or fixture.get("kind") != "valid"
    ):
        raise EvidencePackError(
            f"{rel(manifest_path)}: source_fixture MUST be the canonical valid v0.1 fixture"
        )
    check_source_contract_refs(manifest_path, manifest.get("source_contract_refs"))
    host_shape_ref = manifest.get("host_shape_ref")
    if not isinstance(host_shape_ref, str) or host_shape_ref != fixture.get("host_shape_ref"):
        raise EvidencePackError(f"{rel(manifest_path)}: host_shape_ref MUST match source fixture metadata")
    for section in ("records", "evidence_manifests", "event_chains", "operation_headers"):
        if not isinstance(manifest.get(section), list) or not manifest[section]:
            raise EvidencePackError(f"{rel(manifest_path)}: {section} MUST be a nonempty list")

    checked = 0
    for entry in manifest.get("records", []):
        if not isinstance(entry, dict):
            raise EvidencePackError(f"{rel(manifest_path)}: record entries MUST be objects")
        checked += check_record_entry(manifest_path, pack_dir, fixture, entry)
    for entry in manifest.get("evidence_manifests", []):
        if not isinstance(entry, dict):
            raise EvidencePackError(f"{rel(manifest_path)}: EvidenceManifest entries MUST be objects")
        checked += check_evidence_manifest_entry(pack_dir, fixture, entry)
    for entry in manifest.get("event_chains", []):
        if not isinstance(entry, dict):
            raise EvidencePackError(f"{rel(manifest_path)}: event chain entries MUST be objects")
        checked += check_event_chain_entry(pack_dir, fixture, entry)
    for entry in manifest.get("operation_headers", []):
        if not isinstance(entry, dict):
            raise EvidencePackError(f"{rel(manifest_path)}: header entries MUST be objects")
        checked += check_header_entry(pack_dir, fixture, entry)
    header_indexes = [entry.get("source_operation_index") for entry in manifest["operation_headers"]]
    if sorted(header_indexes) != list(range(len(fixture.get("operations", [])))):
        raise EvidencePackError(
            f"{rel(manifest_path)}: operation_headers MUST cover every source fixture operation"
        )
    if checked == 0:
        raise EvidencePackError(f"{rel(manifest_path)}: evidence pack MUST validate at least one entry")
    return checked


def main() -> int:
    if not PACK_ROOT.exists():
        print("docs/examples/evidence-packs is missing")
        return 1
    manifests = sorted(PACK_ROOT.glob("*/manifest.json"))
    if not manifests:
        print("docs/examples/evidence-packs contains no manifest.json files")
        return 1
    checked = 0
    try:
        for manifest_path in manifests:
            checked += check_manifest(manifest_path)
    except EvidencePackError as exc:
        print(exc)
        return 1
    print(f"Validated {len(manifests)} example evidence pack(s), {checked} entries.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
