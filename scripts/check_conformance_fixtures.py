#!/usr/bin/env python3
"""Validate Jarvis v0.1 conformance fixtures."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json
import re
import sys
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
OPENAPI_PATH = ROOT / "docs" / "openapi" / "jarvis-openapi.yaml"
FIXTURE_ROOT = ROOT / "docs" / "conformance" / "fixtures"
VALID_DIR = FIXTURE_ROOT / "valid"
INVALID_DIR = FIXTURE_ROOT / "invalid"

PROTOCOL_VERSION = "v0.1"
PROTOCOL_GENESIS_HASH = "hash:protocol-genesis"

FIXTURE_ID_RE = re.compile(r"^(valid|invalid)-[a-z0-9][a-z0-9-]*-v01$")

ALLOWED_HOST_SHAPE_REFS = {
    "command_line_host_boundary",
    "local_execution_host_boundary",
    "hosted_execution_host_boundary",
    "tool_use_protocol_boundary",
}

ASSERTION_CLASSES = {
    "header_gate",
    "actor_authority_gate",
    "event_chain_gate",
    "policy_decision_gate",
    "request_resolution_gate",
    "approval_scope_gate",
    "takeover_epoch_gate",
    "contribution_attribution_gate",
    "evidence_export_gate",
    "learning_governance_gate",
    "host_private_boundary_gate",
}

GOLDEN_PATH_REQUIRED_RECORD_GROUPS = {
    "actors",
    "agent_workers",
    "contributions",
    "evidence_manifests",
    "human_workers",
    "jarvis_events",
    "learning_records",
    "memory_proposals",
    "outcome_reports",
    "policies",
    "policy_decisions",
    "requests",
    "reviews",
    "skill_proposals",
    "work_sessions",
    "workers",
}

GOLDEN_PATH_REQUIRED_ASSERTION_CLASSES = {
    "header_gate",
    "actor_authority_gate",
    "event_chain_gate",
    "policy_decision_gate",
    "request_resolution_gate",
    "approval_scope_gate",
    "contribution_attribution_gate",
    "evidence_export_gate",
    "learning_governance_gate",
    "host_private_boundary_gate",
}

GLOBAL_REQUIRED_ASSERTION_CLASSES = ASSERTION_CLASSES

TERMINAL_WORK_SESSION_STATES = {
    "completed",
    "failed",
    "cancelled",
    "closed",
}

REVIEW_RESOLVED_REQUEST_STATUSES = {
    "approved",
    "denied",
    "narrowed",
    "answered",
    "needs_revision",
}

STALE_TIMESTAMP_MIN_SECONDS = 300

REQUIRED_INVALID_FIXTURES = {
    "forbidden-host-private-export-field.json": "forbidden_host_private_field",
    "invalid-approval-scope.json": "invalid_approval_scope",
    "invalid-evidence-export-state.json": "invalid_evidence_export_state",
    "invalid-previous-event-hash.json": "invalid_previous_event_hash",
    "missing-actor.json": "missing_actor",
    "missing-expected-work-session-revision.json": (
        "missing_expected_work_session_revision"
    ),
    "missing-idempotency-key.json": "missing_idempotency_key",
    "missing-policy-decision.json": "missing_policy_decision",
    "missing-policy.json": "missing_policy",
    "missing-previous-event-hash.json": "missing_previous_event_hash",
    "missing-protocol-version.json": "missing_protocol_version",
    "missing-request-timestamp.json": "missing_request_timestamp",
    "missing-review-resolution.json": "missing_review_resolution",
    "missing-takeover-resolution.json": "missing_takeover_resolution",
    "outcome-report-without-learning-record.json": (
        "outcome_report_without_learning_record"
    ),
    "outcome-report-requires-terminal-source.json": (
        "outcome_report_requires_terminal_source"
    ),
    "sealed-evidence-mutation.json": "sealed_evidence_mutation",
    "sealed-work-session-mutation.json": "sealed_work_session_mutation",
    "silent-memory-mutation.json": "silent_memory_mutation",
    "silent-skill-activation.json": "silent_skill_activation",
    "stale-request-timestamp.json": "stale_request_timestamp",
    "stale-takeover-continuation.json": "stale_takeover_epoch",
    "stale-work-session-revision.json": "stale_work_session_revision",
    "unauthorized-actor.json": "unauthorized_actor",
    "unresolved-request.json": "request_unresolved",
}

WORKSESSION_MUTATION_HEADERS = {
    "Authorization",
    "Jarvis-Protocol-Version",
    "Jarvis-Actor-Id",
    "Jarvis-Idempotency-Key",
    "Jarvis-Request-Timestamp",
    "Jarvis-Expected-WorkSession-Revision",
    "Jarvis-Previous-Event-Hash",
}

NON_WORKSESSION_MUTATION_HEADERS = {
    "Authorization",
    "Jarvis-Protocol-Version",
    "Jarvis-Actor-Id",
    "Jarvis-Idempotency-Key",
    "Jarvis-Request-Timestamp",
}

READ_HEADERS = {
    "Authorization",
    "Jarvis-Protocol-Version",
    "Jarvis-Actor-Id",
}

MUTATION_ONLY_HEADERS = {
    "Jarvis-Idempotency-Key",
    "Jarvis-Request-Timestamp",
    "Jarvis-Expected-WorkSession-Revision",
    "Jarvis-Previous-Event-Hash",
}

MISSING_HEADER_ERROR_IDS = {
    "missing_protocol_version": "Jarvis-Protocol-Version",
    "missing_actor": "Jarvis-Actor-Id",
    "missing_idempotency_key": "Jarvis-Idempotency-Key",
    "missing_request_timestamp": "Jarvis-Request-Timestamp",
    "missing_expected_work_session_revision": (
        "Jarvis-Expected-WorkSession-Revision"
    ),
    "missing_previous_event_hash": "Jarvis-Previous-Event-Hash",
}

FORBIDDEN_EXPORT_KEY_TOKENS = {
    "password",
    "credential",
    "token",
    "secret",
    "private_key",
    "session_cookie",
    "api_key",
    "access_key",
    "auth_header",
    "oauth",
    "database",
    "billing",
    "runtime",
    "container",
    "deployment",
    "model_api_key",
    "raw_prompt",
    "host_account",
    "ui_state",
    "private_score",
}


class FixtureError(Exception):
    """Raised when a fixture violates the conformance fixture contract."""


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def fail(message: str) -> int:
    print(message)
    return 1


def is_int(value: Any) -> bool:
    return type(value) is int


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise FixtureError(f"{rel(path)}: invalid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise FixtureError(f"{rel(path)}: fixture root MUST be an object")
    return data


def load_openapi() -> dict[str, Any]:
    data = yaml.safe_load(OPENAPI_PATH.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise FixtureError(f"{rel(OPENAPI_PATH)}: OpenAPI root MUST be an object")
    return data


def schema_enum(openapi: dict[str, Any], schema_name: str) -> set[str]:
    schema = openapi.get("components", {}).get("schemas", {}).get(schema_name, {})
    values = schema.get("enum", [])
    return set(values) if isinstance(values, list) else set()


def component_ref(openapi: dict[str, Any], ref: str) -> Any:
    if not ref.startswith("#/"):
        raise FixtureError(f"{rel(OPENAPI_PATH)}: unsupported OpenAPI ref {ref}")
    current: Any = openapi
    for part in ref[2:].split("/"):
        if not isinstance(current, dict) or part not in current:
            raise FixtureError(f"{rel(OPENAPI_PATH)}: missing OpenAPI ref {ref}")
        current = current[part]
    return current


def operation_parameter_names(openapi: dict[str, Any], operation: dict[str, Any]) -> set[str]:
    names: set[str] = set()
    for parameter in operation.get("parameters", []):
        if not isinstance(parameter, dict):
            continue
        if "$ref" in parameter:
            parameter = component_ref(openapi, parameter["$ref"])
        name = parameter.get("name")
        if isinstance(name, str):
            names.add(name)
    return names


def openapi_operations(openapi: dict[str, Any]) -> dict[str, dict[str, Any]]:
    operations: dict[str, dict[str, Any]] = {}
    paths = openapi.get("paths", {})
    if not isinstance(paths, dict):
        raise FixtureError(f"{rel(OPENAPI_PATH)}: paths MUST be an object")

    for path_template, path_item in paths.items():
        if not isinstance(path_item, dict):
            continue
        for method, operation in path_item.items():
            if method.lower() not in {"get", "post", "put", "patch", "delete"}:
                continue
            if not isinstance(operation, dict):
                continue
            operation_id = operation.get("operationId")
            if not isinstance(operation_id, str):
                continue
            if operation_id in operations:
                raise FixtureError(
                    f"{rel(OPENAPI_PATH)}: duplicate operationId {operation_id}"
                )
            responses = operation.get("responses", {})
            operations[operation_id] = {
                "method": method.upper(),
                "path_template": path_template,
                "parameters": operation_parameter_names(openapi, operation),
                "has_request_body": "requestBody" in operation,
                "statuses": set(responses) if isinstance(responses, dict) else set(),
                "actor_body_match": operation.get("x-jarvis-actor-body-id-match"),
            }
    return operations


def path_param_values(template: str, actual: str) -> dict[str, str] | None:
    pattern = "^" + re.escape(template) + "$"
    pattern = pattern.replace(r"\{worker_id\}", r"(?P<worker_id>[^/]+)")
    pattern = pattern.replace(r"\{actor_id\}", r"(?P<actor_id>[^/]+)")
    pattern = pattern.replace(
        r"\{work_session_id\}", r"(?P<work_session_id>[^/]+)"
    )
    match = re.match(pattern, actual)
    if match is None:
        return None
    return match.groupdict()


def get_ref(data: dict[str, Any], ref: str) -> Any:
    current: Any = data
    for part in ref.split("."):
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return None
    return current


def all_records(records: dict[str, Any], group_name: str) -> list[dict[str, Any]]:
    group = records.get(group_name, {})
    if not isinstance(group, dict):
        return []
    return [value for value in group.values() if isinstance(value, dict)]


def ids_for(records: dict[str, Any], group_name: str) -> set[str]:
    return {
        record["id"]
        for record in all_records(records, group_name)
        if isinstance(record.get("id"), str)
    }


def record_by_id(
    records: dict[str, Any], group_name: str, record_id: str | None
) -> dict[str, Any] | None:
    if record_id is None:
        return None
    for record in all_records(records, group_name):
        if record.get("id") == record_id:
            return record
    return None


def rejecting_operation(operation: dict[str, Any]) -> bool:
    status = operation.get("expected_status")
    return is_int(status) and status >= 400


def first_rejecting_operation(fixture: dict[str, Any]) -> dict[str, Any]:
    expected_error_id = fixture.get("expected_error_id")
    for operation in fixture.get("operations", []):
        if (
            isinstance(operation, dict)
            and rejecting_operation(operation)
            and operation.get("expected_error_id") == expected_error_id
        ):
            return operation
    return {}


def operation_body(fixture: dict[str, Any], operation: dict[str, Any]) -> Any:
    body_ref = operation.get("body_ref")
    if isinstance(body_ref, str):
        return get_ref(fixture, body_ref)
    return None


def actor_by_id(records: dict[str, Any], actor_id: str | None) -> dict[str, Any] | None:
    return record_by_id(records, "actors", actor_id)


def worker_for_actor(
    records: dict[str, Any], actor: dict[str, Any] | None
) -> dict[str, Any] | None:
    if actor is None:
        return None
    worker_id = actor.get("worker_id")
    if not isinstance(worker_id, str):
        return None
    return record_by_id(records, "workers", worker_id)


def worker_grants(worker: dict[str, Any] | None) -> set[str]:
    if worker is None:
        return set()
    authority_scope = worker.get("authority_scope", {})
    if not isinstance(authority_scope, dict):
        return set()
    grants = authority_scope.get("grants", [])
    if not isinstance(grants, list):
        return set()
    return {grant for grant in grants if isinstance(grant, str)}


def parse_utc_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        return None
    return parsed.replace(tzinfo=timezone.utc)


def timestamp_field(value: dict[str, Any]) -> datetime | None:
    for field_name in ("created_at", "updated_at", "timestamp", "received_at"):
        parsed = parse_utc_timestamp(value.get(field_name))
        if parsed is not None:
            return parsed
    return None


def request_id_from_target_ref(target_ref: Any) -> str | None:
    if isinstance(target_ref, str) and target_ref.startswith("request:"):
        return target_ref.removeprefix("request:")
    return None


def target_work_session_id(operation: dict[str, Any], body: Any) -> str | None:
    if isinstance(operation.get("work_session_id"), str):
        return operation["work_session_id"]
    if isinstance(body, dict) and isinstance(body.get("work_session_id"), str):
        return body["work_session_id"]
    return None


def work_session_snapshot_for_operation(
    records: dict[str, Any], operation: dict[str, Any], body: Any
) -> dict[str, Any] | None:
    work_session_id = target_work_session_id(operation, body)
    if work_session_id is None:
        return None
    revision = operation.get("headers", {}).get("Jarvis-Expected-WorkSession-Revision")
    previous_hash = operation.get("headers", {}).get("Jarvis-Previous-Event-Hash")
    for snapshot in all_records(records, "work_sessions"):
        if snapshot.get("id") != work_session_id:
            continue
        if is_int(revision) and previous_hash is not None:
            if (
                snapshot.get("revision") == revision
                and snapshot.get("last_event_hash") == previous_hash
            ):
                return snapshot
    return None


def resolved_state_ref(path: Path, fixture: dict[str, Any], state_ref: str) -> Any:
    value = get_ref(fixture, state_ref)
    if value is None:
        raise FixtureError(f"{rel(path)}: expected_error_field does not resolve")
    return value


def records_with_status(
    records: dict[str, Any], group_name: str, statuses: set[str]
) -> list[dict[str, Any]]:
    return [
        record
        for record in all_records(records, group_name)
        if record.get("status") in statuses
    ]


def ref_targets_protocol_state(ref: str) -> bool:
    return ref == "host_shape_ref" or ref == "operations" or ref.startswith(
        "records."
    )


def walk(value: Any, path: str = "") -> list[tuple[str, Any]]:
    items = [(path, value)]
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}" if path else key
            items.extend(walk(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            child_path = f"{path}[{index}]"
            items.extend(walk(child, child_path))
    return items


def is_forbidden_export_key(key: str) -> bool:
    normalized = key.lower().replace("-", "_")
    compact = re.sub(r"[^a-z0-9]", "", normalized)
    return any(
        token in normalized or token.replace("_", "") in compact
        for token in FORBIDDEN_EXPORT_KEY_TOKENS
    )


def fixture_files() -> list[tuple[Path, str]]:
    files: list[tuple[Path, str]] = []
    files.extend((path, "valid") for path in sorted(VALID_DIR.glob("*.json")))
    files.extend((path, "invalid") for path in sorted(INVALID_DIR.glob("*.json")))
    return files


def expected_headers_for_operation(
    operation_id: str, operation_info: dict[str, Any]
) -> tuple[set[str], set[str]]:
    parameters = operation_info["parameters"]
    if operation_id in {"registerWorker", "registerActor", "submitOutcomeReport"}:
        return NON_WORKSESSION_MUTATION_HEADERS, {
            "Jarvis-Expected-WorkSession-Revision",
            "Jarvis-Previous-Event-Hash",
        }
    if operation_info["method"] == "GET":
        return READ_HEADERS, MUTATION_ONLY_HEADERS
    if "Jarvis-Expected-WorkSession-Revision" in parameters:
        return WORKSESSION_MUTATION_HEADERS, set()
    return NON_WORKSESSION_MUTATION_HEADERS, {
        "Jarvis-Expected-WorkSession-Revision",
        "Jarvis-Previous-Event-Hash",
    }


def validate_source_ref(path: Path, openapi: dict[str, Any], source_ref: str) -> None:
    if source_ref.startswith("http://") or source_ref.startswith("https://"):
        return
    target, _, fragment = source_ref.partition("#")
    doc_path = ROOT / target
    if not doc_path.exists():
        raise FixtureError(f"{rel(path)}: source ref file missing: {source_ref}")
    if target == "docs/openapi/jarvis-openapi.yaml" and fragment:
        fragment_ref = "#" + fragment
        component_ref(openapi, fragment_ref)


def validate_host_shape(path: Path, fixture: dict[str, Any]) -> None:
    host_shape_ref = fixture.get("host_shape_ref")
    if host_shape_ref not in ALLOWED_HOST_SHAPE_REFS:
        raise FixtureError(f"{rel(path)}: host_shape_ref is not allowed")

    for item_path, value in walk(fixture.get("records", {}), "records"):
        if item_path.endswith(".host_shape_ref"):
            raise FixtureError(f"{rel(path)}: host_shape_ref appears inside records")
        if value == host_shape_ref:
            raise FixtureError(
                f"{rel(path)}: host_shape_ref value appears inside records at {item_path}"
            )

    for item_path, value in walk(fixture.get("operations", []), "operations"):
        if item_path.endswith(".host_shape_ref"):
            raise FixtureError(f"{rel(path)}: host_shape_ref appears inside operations")
        if value == host_shape_ref:
            raise FixtureError(
                f"{rel(path)}: host_shape_ref value appears inside operations at {item_path}"
            )


def validate_forbidden_export_fields(path: Path, fixture: dict[str, Any]) -> None:
    records = fixture.get("records", {})
    evidence_manifests = records.get("evidence_manifests", {})
    found: list[str] = []
    for item_path, value in walk(evidence_manifests, "records.evidence_manifests"):
        if isinstance(value, dict):
            for key in value:
                if is_forbidden_export_key(key):
                    found.append(f"{item_path}.{key}" if item_path else key)

    expected_error_id = fixture.get("expected_error_id")
    if expected_error_id == "forbidden_host_private_field":
        expected_field = fixture.get("expected_error_field")
        if expected_field not in found:
            raise FixtureError(
                f"{rel(path)}: forbidden_host_private_field fixture MUST expose "
                f"{expected_field}"
            )
        return

    if found:
        raise FixtureError(
            f"{rel(path)}: forbidden host-private export fields: "
            + ", ".join(sorted(found))
        )


def validate_fixture_envelope(path: Path, fixture: dict[str, Any], expected_kind: str) -> None:
    required = {
        "fixture_id",
        "protocol_version",
        "kind",
        "title",
        "description",
        "source_contract_refs",
        "host_shape_ref",
        "records",
        "operations",
        "assertions",
        "expected_result",
    }
    if expected_kind == "invalid":
        required.update({"expected_error_id", "expected_error_field"})

    missing = sorted(required - set(fixture))
    if missing:
        raise FixtureError(f"{rel(path)}: missing fixture fields: {', '.join(missing)}")

    fixture_id = fixture.get("fixture_id")
    if not isinstance(fixture_id, str) or not FIXTURE_ID_RE.match(fixture_id):
        raise FixtureError(f"{rel(path)}: fixture_id format is invalid")
    if not fixture_id.startswith(expected_kind + "-"):
        raise FixtureError(f"{rel(path)}: fixture_id kind prefix is invalid")
    if expected_kind == "valid" and path.name == "golden-path.json":
        if fixture_id != "valid-golden-path-v01":
            raise FixtureError(f"{rel(path)}: fixture_id MUST be valid-golden-path-v01")
    if expected_kind == "invalid":
        expected_id = f"invalid-{path.stem}-v01"
        if fixture_id != expected_id:
            raise FixtureError(f"{rel(path)}: fixture_id MUST be {expected_id}")

    if fixture.get("protocol_version") != PROTOCOL_VERSION:
        raise FixtureError(f"{rel(path)}: protocol_version MUST be {PROTOCOL_VERSION}")
    if fixture.get("kind") != expected_kind:
        raise FixtureError(f"{rel(path)}: kind MUST be {expected_kind}")
    expected_result = "pass" if expected_kind == "valid" else "reject"
    if fixture.get("expected_result") != expected_result:
        raise FixtureError(f"{rel(path)}: expected_result MUST be {expected_result}")

    if expected_kind == "valid":
        if "expected_error_id" in fixture or "expected_error_field" in fixture:
            raise FixtureError(f"{rel(path)}: valid fixture MUST NOT define error fields")
    else:
        expected_error_id = REQUIRED_INVALID_FIXTURES.get(path.name)
        if expected_error_id is None:
            raise FixtureError(f"{rel(path)}: invalid fixture is not required by Week 3")
        if fixture.get("expected_error_id") != expected_error_id:
            raise FixtureError(
                f"{rel(path)}: expected_error_id MUST be {expected_error_id}"
            )

    if not isinstance(fixture.get("records"), dict):
        raise FixtureError(f"{rel(path)}: records MUST be an object")
    if not isinstance(fixture.get("operations"), list) or not fixture["operations"]:
        raise FixtureError(f"{rel(path)}: operations MUST be a nonempty list")
    if not isinstance(fixture.get("assertions"), list) or not fixture["assertions"]:
        raise FixtureError(f"{rel(path)}: assertions MUST be a nonempty list")
    if not isinstance(fixture.get("source_contract_refs"), list) or not fixture[
        "source_contract_refs"
    ]:
        raise FixtureError(f"{rel(path)}: source_contract_refs MUST be nonempty")
    if expected_kind == "invalid":
        rejected_operations = [
            operation
            for operation in fixture["operations"]
            if isinstance(operation, dict)
            and rejecting_operation(operation)
            and operation.get("expected_error_id") == fixture.get("expected_error_id")
        ]
        if not rejected_operations:
            raise FixtureError(
                f"{rel(path)}: invalid fixture MUST include a rejecting operation"
            )


def validate_header_values(
    path: Path,
    operation_id: str,
    headers: dict[str, Any],
    expected_error_id: str | None,
) -> None:
    for header_name in (
        "Authorization",
        "Jarvis-Actor-Id",
        "Jarvis-Idempotency-Key",
    ):
        expected_missing_error = {
            "Jarvis-Actor-Id": "missing_actor",
            "Jarvis-Idempotency-Key": "missing_idempotency_key",
        }.get(header_name)
        if (
            header_name in headers
            and not (
                expected_missing_error is not None
                and expected_error_id == expected_missing_error
            )
        ):
            if not isinstance(headers[header_name], str) or not headers[header_name]:
                raise FixtureError(
                    f"{rel(path)}: {operation_id} {header_name} MUST be a nonempty string"
                )

    if (
        "Jarvis-Protocol-Version" in headers
        and expected_error_id != "missing_protocol_version"
        and headers["Jarvis-Protocol-Version"] != PROTOCOL_VERSION
    ):
        raise FixtureError(
            f"{rel(path)}: {operation_id} Jarvis-Protocol-Version MUST be "
            f"{PROTOCOL_VERSION}"
        )

    timestamp = headers.get("Jarvis-Request-Timestamp")
    if timestamp is not None and expected_error_id != "missing_request_timestamp":
        if not isinstance(timestamp, str) or not re.match(
            r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$", timestamp
        ):
            raise FixtureError(
                f"{rel(path)}: {operation_id} Jarvis-Request-Timestamp is invalid"
            )

    revision = headers.get("Jarvis-Expected-WorkSession-Revision")
    if revision is not None and expected_error_id != (
        "missing_expected_work_session_revision"
    ):
        if not is_int(revision) or revision < 0:
            raise FixtureError(
                f"{rel(path)}: {operation_id} "
                "Jarvis-Expected-WorkSession-Revision MUST be a nonnegative integer"
            )

    previous_hash = headers.get("Jarvis-Previous-Event-Hash")
    if previous_hash is not None and expected_error_id != "missing_previous_event_hash":
        if not isinstance(previous_hash, str) or not previous_hash.startswith("hash:"):
            raise FixtureError(
                f"{rel(path)}: {operation_id} Jarvis-Previous-Event-Hash is invalid"
            )


def validate_operation(
    path: Path,
    fixture: dict[str, Any],
    operation: dict[str, Any],
    operations: dict[str, dict[str, Any]],
) -> None:
    required = {"operation_id", "method", "path", "headers", "actor_id", "expected_status"}
    missing = sorted(required - set(operation))
    if missing:
        raise FixtureError(f"{rel(path)}: operation missing fields: {', '.join(missing)}")

    operation_id = operation.get("operation_id")
    if operation_id not in operations:
        raise FixtureError(f"{rel(path)}: unknown operation_id {operation_id}")
    operation_info = operations[operation_id]

    if not is_int(operation.get("expected_status")):
        raise FixtureError(f"{rel(path)}: {operation_id} expected_status MUST be integer")
    if operation.get("method") != operation_info["method"]:
        raise FixtureError(f"{rel(path)}: {operation_id} method does not match OpenAPI")
    path_values = path_param_values(operation_info["path_template"], operation.get("path", ""))
    if path_values is None:
        raise FixtureError(f"{rel(path)}: {operation_id} path does not match OpenAPI")

    expected_status = str(operation.get("expected_status"))
    if expected_status not in operation_info["statuses"]:
        raise FixtureError(f"{rel(path)}: {operation_id} expected_status is not in OpenAPI")

    headers = operation.get("headers")
    if not isinstance(headers, dict):
        raise FixtureError(f"{rel(path)}: {operation_id} headers MUST be an object")

    required_headers, forbidden_headers = expected_headers_for_operation(
        operation_id, operation_info
    )
    missing_headers = required_headers - set(headers)
    expected_error_id = fixture.get("expected_error_id")
    allowed_missing = MISSING_HEADER_ERROR_IDS.get(expected_error_id)
    if allowed_missing:
        if allowed_missing in headers:
            raise FixtureError(
                f"{rel(path)}: {operation_id} {expected_error_id} fixture MUST omit "
                f"{allowed_missing}"
            )
        missing_headers.discard(allowed_missing)
    if missing_headers:
        raise FixtureError(
            f"{rel(path)}: {operation_id} missing required headers: "
            + ", ".join(sorted(missing_headers))
        )
    present_forbidden = forbidden_headers & set(headers)
    if present_forbidden:
        raise FixtureError(
            f"{rel(path)}: {operation_id} includes forbidden headers: "
            + ", ".join(sorted(present_forbidden))
        )
    validate_header_values(path, operation_id, headers, expected_error_id)

    actor_header = headers.get("Jarvis-Actor-Id")
    if actor_header is not None and operation.get("actor_id") != actor_header:
        raise FixtureError(f"{rel(path)}: {operation_id} actor_id mismatches header")

    body: Any = None
    if operation_info["has_request_body"]:
        if "body_ref" not in operation:
            raise FixtureError(f"{rel(path)}: {operation_id} requires body_ref")
        body_ref = operation["body_ref"]
        if not isinstance(body_ref, str) or not body_ref.startswith("records."):
            raise FixtureError(f"{rel(path)}: {operation_id} body_ref MUST target records")
        body = get_ref(fixture, body_ref)
        if body is None:
            raise FixtureError(f"{rel(path)}: {operation_id} body_ref does not resolve")
        if not isinstance(body, dict):
            raise FixtureError(f"{rel(path)}: {operation_id} body_ref MUST resolve to object")
    elif "body_ref" in operation:
        raise FixtureError(f"{rel(path)}: {operation_id} MUST NOT define body_ref")

    if "worker_id" in path_values and isinstance(body, dict):
        if body.get("id") != path_values["worker_id"]:
            raise FixtureError(f"{rel(path)}: {operation_id} worker_id path mismatch")
    if "actor_id" in path_values and isinstance(body, dict):
        if body.get("id") != path_values["actor_id"]:
            raise FixtureError(f"{rel(path)}: {operation_id} actor_id path mismatch")
    if "work_session_id" in path_values:
        if operation.get("work_session_id") != path_values["work_session_id"]:
            raise FixtureError(
                f"{rel(path)}: {operation_id} work_session_id path mismatch"
            )
        if "body_ref" in operation and isinstance(body, dict):
            body_work_session_id = body.get("work_session_id")
            if body_work_session_id != path_values["work_session_id"]:
                raise FixtureError(
                    f"{rel(path)}: {operation_id} body work_session_id mismatch"
                )
    if operation_id == "createWorkSession" and isinstance(body, dict):
        if operation.get("work_session_id") != body.get("id"):
            raise FixtureError(
                f"{rel(path)}: createWorkSession work_session_id must match body id"
            )
    actor_body_match = operation_info.get("actor_body_match")
    if actor_body_match is not None and expected_error_id != "missing_actor":
        if not isinstance(actor_body_match, dict):
            raise FixtureError(
                f"{rel(OPENAPI_PATH)}: {operation_id} actor/body match MUST be an object"
            )
        body_field = actor_body_match.get("body_field")
        if not isinstance(body_field, str):
            raise FixtureError(
                f"{rel(OPENAPI_PATH)}: {operation_id} actor/body match missing body_field"
            )
        if not isinstance(body, dict) or body.get(body_field) != actor_header:
            raise FixtureError(
                f"{rel(path)}: {operation_id} body {body_field} mismatches Jarvis-Actor-Id"
            )

    validate_work_session_header_binding(
        path,
        fixture,
        operation,
        operation_info,
        path_values,
        body,
        expected_error_id,
    )

    if operation_info["path_template"].startswith("/work-sessions") and operation_id != (
        "createWorkSession"
    ):
        if "work_session_id" not in operation:
            raise FixtureError(f"{rel(path)}: {operation_id} requires work_session_id")

    if rejecting_operation(operation):
        if expected_error_id is None:
            raise FixtureError(
                f"{rel(path)}: {operation_id} rejecting operation requires expected_error_id"
            )
        if operation.get("expected_error_id") != expected_error_id:
            raise FixtureError(
                f"{rel(path)}: {operation_id} expected_error_id must match fixture"
            )
    elif "expected_error_id" in operation:
        raise FixtureError(f"{rel(path)}: successful {operation_id} has expected_error_id")

    event_ref = operation.get("expected_event_ref")
    if event_ref is not None:
        event_ids = {
            event.get("id")
            for event in fixture.get("records", {}).get("jarvis_events", {}).values()
            if isinstance(event, dict)
        }
        if event_ref not in event_ids:
            raise FixtureError(
                f"{rel(path)}: {operation_id} expected_event_ref does not resolve"
            )
        events = fixture.get("records", {}).get("jarvis_events", {}).values()
        produced = next(
            event
            for event in events
            if isinstance(event, dict) and event.get("id") == event_ref
        )
        operation_previous_hash = headers.get("Jarvis-Previous-Event-Hash")
        if (
            operation_previous_hash is not None
            and produced.get("previous_hash") != operation_previous_hash
        ):
            raise FixtureError(
                f"{rel(path)}: {operation_id} expected_event_ref previous_hash mismatch"
            )
        operation_work_session_id = operation.get("work_session_id")
        if (
            operation_work_session_id is not None
            and produced.get("work_session_id") != operation_work_session_id
        ):
            raise FixtureError(
                f"{rel(path)}: {operation_id} expected_event_ref work_session_id mismatch"
            )
        if operation_id == "createWorkSession" and produced.get("type") != (
            "work_session.created"
        ):
            raise FixtureError(
                f"{rel(path)}: createWorkSession expected_event_ref MUST be work_session.created"
            )
        expected_revision = headers.get("Jarvis-Expected-WorkSession-Revision")
        if isinstance(expected_revision, int) and produced.get("sequence") != (
            expected_revision + 1
        ):
            raise FixtureError(
                f"{rel(path)}: {operation_id} expected_event_ref sequence mismatch"
            )

    previous_hash = headers.get("Jarvis-Previous-Event-Hash")
    if previous_hash and expected_error_id != "invalid_previous_event_hash":
        event_hashes = represented_hash_set(fixture)
        if previous_hash not in event_hashes:
            raise FixtureError(
                f"{rel(path)}: {operation_id} previous event hash is not represented"
            )


def represented_work_session_states(
    fixture: dict[str, Any], work_session_id: str
) -> set[tuple[int, str]]:
    states: set[tuple[int, str]] = set()
    for snapshot in fixture.get("records", {}).get("work_sessions", {}).values():
        if (
            isinstance(snapshot, dict)
            and snapshot.get("id") == work_session_id
            and is_int(snapshot.get("revision"))
            and isinstance(snapshot.get("last_event_hash"), str)
        ):
            states.add((snapshot["revision"], snapshot["last_event_hash"]))
    for event in fixture.get("records", {}).get("jarvis_events", {}).values():
        if (
            isinstance(event, dict)
            and event.get("work_session_id") == work_session_id
            and is_int(event.get("sequence"))
            and isinstance(event.get("event_hash"), str)
        ):
            states.add((event["sequence"], event["event_hash"]))
    return states


def validate_work_session_header_binding(
    path: Path,
    fixture: dict[str, Any],
    operation: dict[str, Any],
    operation_info: dict[str, Any],
    path_values: dict[str, str],
    body: Any,
    expected_error_id: str | None,
) -> None:
    headers = operation["headers"]
    operation_id = operation["operation_id"]
    revision = headers.get("Jarvis-Expected-WorkSession-Revision")
    previous_hash = headers.get("Jarvis-Previous-Event-Hash")

    if operation_id == "createWorkSession":
        if expected_error_id != "missing_expected_work_session_revision" and revision != 0:
            raise FixtureError(
                f"{rel(path)}: createWorkSession revision MUST be protocol genesis revision"
            )
        if (
            expected_error_id != "missing_previous_event_hash"
            and previous_hash != PROTOCOL_GENESIS_HASH
        ):
            raise FixtureError(
                f"{rel(path)}: createWorkSession previous hash MUST be protocol genesis"
            )
        if isinstance(body, dict) and (
            body.get("revision") != 0
            or body.get("last_event_hash") != PROTOCOL_GENESIS_HASH
        ):
            raise FixtureError(
                f"{rel(path)}: createWorkSession body MUST represent genesis precondition"
            )
        return

    if operation_info["method"] == "GET" or not operation_info["path_template"].startswith(
        "/work-sessions"
    ):
        return

    work_session_id = path_values.get("work_session_id")
    if not work_session_id:
        return
    states = represented_work_session_states(fixture, work_session_id)
    if not states:
        raise FixtureError(
            f"{rel(path)}: {operation_id} has no WorkSession snapshot for "
            f"{work_session_id}"
        )

    if expected_error_id == "stale_work_session_revision":
        matching_hash_states = {
            state_revision
            for state_revision, state_hash in states
            if state_hash == previous_hash
        }
        if not matching_hash_states:
            raise FixtureError(
                f"{rel(path)}: stale_work_session_revision fixture MUST bind previous hash"
            )
        if revision in matching_hash_states:
            raise FixtureError(
                f"{rel(path)}: stale_work_session_revision fixture MUST use stale revision"
            )
        return

    if expected_error_id == "invalid_previous_event_hash":
        matching_revision_states = {
            state_hash for state_revision, state_hash in states if state_revision == revision
        }
        if not matching_revision_states:
            raise FixtureError(
                f"{rel(path)}: invalid_previous_event_hash fixture MUST bind revision"
            )
        if previous_hash in matching_revision_states:
            raise FixtureError(
                f"{rel(path)}: invalid_previous_event_hash fixture MUST use wrong hash"
            )
        return

    if expected_error_id == "missing_expected_work_session_revision":
        if not any(state_hash == previous_hash for _, state_hash in states):
            raise FixtureError(
                f"{rel(path)}: missing revision fixture MUST bind previous hash"
            )
        return

    if expected_error_id == "missing_previous_event_hash":
        if not any(state_revision == revision for state_revision, _ in states):
            raise FixtureError(
                f"{rel(path)}: missing previous hash fixture MUST bind revision"
            )
        return

    if revision is None or previous_hash is None:
        return

    if (revision, previous_hash) not in states:
        raise FixtureError(
            f"{rel(path)}: {operation_id} headers do not match WorkSession state"
        )


def validate_assertion(path: Path, fixture: dict[str, Any], assertion: dict[str, Any]) -> None:
    required = {"assertion_id", "class", "target_ref", "required_state", "expected_result"}
    missing = sorted(required - set(assertion))
    if missing:
        raise FixtureError(f"{rel(path)}: assertion missing fields: {', '.join(missing)}")
    if assertion.get("class") not in ASSERTION_CLASSES:
        raise FixtureError(f"{rel(path)}: assertion class is not allowed")
    if not ref_targets_protocol_state(assertion["target_ref"]):
        raise FixtureError(f"{rel(path)}: assertion target_ref must target protocol state")
    if get_ref(fixture, assertion["target_ref"]) is None:
        raise FixtureError(f"{rel(path)}: assertion target_ref does not resolve")

    expected_result = fixture.get("expected_result")
    if assertion.get("expected_result") != expected_result:
        raise FixtureError(f"{rel(path)}: assertion expected_result mismatch")

    if expected_result == "reject":
        if assertion.get("expected_error_id") != fixture.get("expected_error_id"):
            raise FixtureError(f"{rel(path)}: assertion expected_error_id mismatch")
    elif "expected_error_id" in assertion:
        raise FixtureError(f"{rel(path)}: passing assertion has expected_error_id")


def validate_golden_path_semantics(path: Path, fixture: dict[str, Any]) -> None:
    if path.name != "golden-path.json":
        return

    records = fixture.get("records", {})
    missing_record_groups = sorted(GOLDEN_PATH_REQUIRED_RECORD_GROUPS - set(records))
    if missing_record_groups:
        raise FixtureError(
            f"{rel(path)}: golden path missing record groups: "
            + ", ".join(missing_record_groups)
        )

    assertion_classes = {
        assertion.get("class")
        for assertion in fixture.get("assertions", [])
        if isinstance(assertion, dict)
    }
    missing_assertion_classes = sorted(
        GOLDEN_PATH_REQUIRED_ASSERTION_CLASSES - assertion_classes
    )
    if missing_assertion_classes:
        raise FixtureError(
            f"{rel(path)}: golden path missing assertion classes: "
            + ", ".join(missing_assertion_classes)
        )

    request = get_ref(fixture, "records.requests.approved")
    review = get_ref(fixture, "records.reviews.approve_source")
    policy_decision = get_ref(
        fixture, "records.policy_decisions.external_source_denied"
    )
    evidence_manifest = get_ref(fixture, "records.evidence_manifests.portable_export")
    learning_record = get_ref(fixture, "records.learning_records.pair")
    outcome_report = get_ref(fixture, "records.outcome_reports.post_session")
    memory_proposal = get_ref(fixture, "records.memory_proposals.source_policy_pattern")
    skill_proposal = get_ref(fixture, "records.skill_proposals.bounded_source_collection")
    contribution = get_ref(fixture, "records.contributions.shared_answer")

    if (
        not isinstance(policy_decision, dict)
        or not isinstance(request, dict)
        or policy_decision.get("request_id") != request.get("id")
        or request.get("policy_decision_id") != policy_decision.get("id")
        or policy_decision.get("work_session_id") != request.get("work_session_id")
        or policy_decision.get("actor_id") != request.get("requester_actor_id")
    ):
        raise FixtureError(f"{rel(path)}: golden PolicyDecision MUST create Request")

    if (
        not isinstance(review, dict)
        or request.get("resolved_by_review_id") != review.get("id")
        or review.get("target_ref") != f"request:{request.get('id')}"
        or review.get("work_session_id") != request.get("work_session_id")
    ):
        raise FixtureError(f"{rel(path)}: golden Request MUST resolve by Review")

    approval_scope = review.get("approval_scope") if isinstance(review, dict) else None
    approval_scope_expires_at = (
        parse_utc_timestamp(approval_scope.get("expires_at"))
        if isinstance(approval_scope, dict)
        else None
    )
    review_timestamp = timestamp_field(review) if isinstance(review, dict) else None
    if (
        not isinstance(approval_scope, dict)
        or approval_scope.get("request_id") != request.get("id")
        or approval_scope.get("review_id") != review.get("id")
        or approval_scope.get("policy_decision_id") != policy_decision.get("id")
        or approval_scope.get("applies_to_work_session_id") != request.get("work_session_id")
        or approval_scope.get("applies_to_actor_id") != request.get("requester_actor_id")
        or approval_scope.get("approved_action") != request.get("requested_action")
        or not is_int(approval_scope.get("max_uses"))
        or approval_scope.get("max_uses") <= 0
        or approval_scope_expires_at is None
        or review_timestamp is None
        or approval_scope_expires_at <= review_timestamp
        or not isinstance(approval_scope.get("normalized_action_hash"), str)
        or not approval_scope["normalized_action_hash"].startswith("hash:")
    ):
        raise FixtureError(f"{rel(path)}: golden Review MUST create ApprovalScope")

    worker_ids = ids_for(records, "workers")
    actor_ids = ids_for(records, "actors")
    if (
        not isinstance(contribution, dict)
        or contribution.get("contributor_type") != "shared"
        or not isinstance(contribution.get("contributor_refs"), list)
        or len(contribution["contributor_refs"]) < 2
    ):
        raise FixtureError(f"{rel(path)}: golden Contribution MUST be attributable")
    contributor_roles = {
        contributor.get("contribution_role")
        for contributor in contribution["contributor_refs"]
        if isinstance(contributor, dict)
    }
    if not {"human", "agent"} <= contributor_roles:
        raise FixtureError(f"{rel(path)}: golden Contribution MUST include human and agent")
    if contribution.get("work_session_id") != request.get("work_session_id"):
        raise FixtureError(f"{rel(path)}: golden Contribution MUST bind WorkSession")
    for contributor in contribution["contributor_refs"]:
        if not isinstance(contributor, dict):
            raise FixtureError(
                f"{rel(path)}: golden Contribution contributor refs MUST resolve"
            )
        contributor_worker = record_by_id(records, "workers", contributor.get("worker_id"))
        contributor_actor = record_by_id(records, "actors", contributor.get("actor_id"))
        if (
            contributor.get("contribution_role") not in {"human", "agent"}
            or contributor.get("worker_id") not in worker_ids
            or contributor.get("actor_id") not in actor_ids
            or not isinstance(contributor_worker, dict)
            or not isinstance(contributor_actor, dict)
            or contributor_worker.get("type") != contributor.get("contribution_role")
            or contributor_actor.get("type") != contributor.get("contribution_role")
            or contributor_actor.get("worker_id") != contributor_worker.get("id")
        ):
            raise FixtureError(
                f"{rel(path)}: golden Contribution contributor refs MUST resolve"
            )

    event_ids = ids_for(records, "jarvis_events")
    policy_decision_ids = ids_for(records, "policy_decisions")
    request_ids = ids_for(records, "requests")
    review_ids = ids_for(records, "reviews")
    contribution_ids = ids_for(records, "contributions")
    takeover_ids = ids_for(records, "takeovers")
    terminal_snapshots = [
        snapshot
        for snapshot in all_records(records, "work_sessions")
        if snapshot.get("id") == evidence_manifest.get("work_session_id")
        and snapshot.get("status") in TERMINAL_WORK_SESSION_STATES
    ] if isinstance(evidence_manifest, dict) else []

    if (
        not isinstance(evidence_manifest, dict)
        or evidence_manifest.get("generated_by_actor_id") not in actor_ids
        or evidence_manifest.get("work_session_id") != contribution.get("work_session_id")
        or not terminal_snapshots
        or evidence_manifest.get("event_chain_root")
        not in {snapshot.get("last_event_hash") for snapshot in terminal_snapshots}
        or not isinstance(evidence_manifest.get("evidence_item_refs"), list)
        or not evidence_manifest["evidence_item_refs"]
        or not isinstance(evidence_manifest.get("export_profile"), dict)
        or not evidence_manifest.get("artifact_refs")
        or not evidence_manifest.get("limitation_refs")
        or contribution.get("id") not in evidence_manifest.get("contribution_refs", [])
    ):
        raise FixtureError(f"{rel(path)}: golden EvidenceManifest MUST export evidence")
    for evidence_item in evidence_manifest["evidence_item_refs"]:
        if (
            not isinstance(evidence_item, dict)
            or evidence_item.get("work_session_id") != evidence_manifest.get("work_session_id")
            or evidence_item.get("captured_by_actor_id") not in actor_ids
            or not set(evidence_item.get("source_event_refs", [])) <= event_ids
        ):
            raise FixtureError(
                f"{rel(path)}: golden EvidenceManifest evidence items MUST bind events"
            )
    reference_sets = {
        "policy_decision_refs": policy_decision_ids,
        "request_refs": request_ids,
        "review_refs": review_ids,
        "takeover_refs": takeover_ids,
        "contribution_refs": contribution_ids,
    }
    for field_name, allowed_ids in reference_sets.items():
        refs = evidence_manifest.get(field_name, [])
        if not isinstance(refs, list) or not set(refs) <= allowed_ids:
            raise FixtureError(
                f"{rel(path)}: golden EvidenceManifest {field_name} MUST resolve"
            )

    if not isinstance(learning_record, dict) or learning_record.get("subject_type") not in {
        "human",
        "agent",
        "pair",
    }:
        raise FixtureError(f"{rel(path)}: golden LearningRecord subject_type is invalid")
    learning_id = learning_record.get("id")
    if (
        not set(learning_record.get("source_event_refs", [])) <= event_ids
        or not isinstance(memory_proposal, dict)
        or not isinstance(skill_proposal, dict)
        or learning_id not in memory_proposal.get("learning_record_refs", [])
        or learning_id not in skill_proposal.get("learning_record_refs", [])
        or not set(memory_proposal.get("source_event_refs", [])) <= event_ids
        or not set(skill_proposal.get("source_event_refs", [])) <= event_ids
    ):
        raise FixtureError(f"{rel(path)}: golden LearningRecord refs MUST resolve")

    if (
        not isinstance(outcome_report, dict)
        or learning_id not in outcome_report.get("learning_record_refs", [])
        or outcome_report.get("work_session_id") != learning_record.get("work_session_id")
        or outcome_report.get("accepted_by_actor_id") not in actor_ids
    ):
        raise FixtureError(f"{rel(path)}: golden OutcomeReport MUST reference learning")


def validate_takeover_path_semantics(path: Path, fixture: dict[str, Any]) -> None:
    if path.name != "takeover-path.json":
        return

    request = get_ref(fixture, "records.requests.takeover")
    human_active = get_ref(fixture, "records.takeovers.human_active")
    reconciliation_required = get_ref(
        fixture, "records.takeovers.reconciliation_required"
    )
    resumed = get_ref(fixture, "records.takeovers.resumed")
    started_event = get_ref(fixture, "records.jarvis_events.takeover_started")
    reconciliation_event = get_ref(
        fixture, "records.jarvis_events.takeover_reconciliation_required"
    )
    resumed_event = get_ref(fixture, "records.jarvis_events.takeover_resumed")

    if (
        not isinstance(request, dict)
        or request.get("status") != "takeover"
        or not isinstance(request.get("resolved_by_takeover_id"), str)
    ):
        raise FixtureError(
            f"{rel(path)}: takeover path Request MUST resolve by Takeover"
        )

    takeovers = [human_active, reconciliation_required, resumed]
    if not all(isinstance(takeover, dict) for takeover in takeovers):
        raise FixtureError(
            f"{rel(path)}: takeover path MUST include all Takeover lifecycle states"
        )

    takeover_id = request.get("resolved_by_takeover_id")
    expected_states = ["human_active", "reconciliation_required", "resumed"]
    for takeover, expected_state in zip(takeovers, expected_states, strict=True):
        affected_scope = takeover.get("affected_scope", {})
        if (
            takeover.get("id") != takeover_id
            or takeover.get("request_id") != request.get("id")
            or takeover.get("work_session_id") != request.get("work_session_id")
            or takeover.get("state") != expected_state
            or takeover.get("lock_epoch") != human_active.get("lock_epoch")
            or affected_scope.get("blocking_scope") != request.get("blocking_scope")
            or affected_scope.get("scope_ref")
            != request.get("requested_action", {}).get("scope_ref")
            or affected_scope.get("normalized_action_hash")
            != "hash:action-final-submission"
        ):
            raise FixtureError(
                f"{rel(path)}: takeover path {expected_state} state MUST bind Request and scope"
            )

    if (
        not isinstance(resumed.get("reconciliation_refs"), list)
        or not resumed.get("reconciliation_refs")
        or not resumed.get("resumed_by_actor_id")
    ):
        raise FixtureError(
            f"{rel(path)}: takeover path resumed state MUST include reconciliation refs"
        )

    events = [started_event, reconciliation_event, resumed_event]
    if not all(isinstance(event, dict) for event in events):
        raise FixtureError(
            f"{rel(path)}: takeover path MUST include Takeover lifecycle events"
        )
    if not (
        started_event.get("sequence")
        < reconciliation_event.get("sequence")
        < resumed_event.get("sequence")
    ):
        raise FixtureError(
            f"{rel(path)}: takeover path events MUST order reconciliation before resume"
        )
    if (
        reconciliation_event.get("previous_hash") != started_event.get("event_hash")
        or resumed_event.get("previous_hash") != reconciliation_event.get("event_hash")
    ):
        raise FixtureError(
            f"{rel(path)}: takeover path event hashes MUST chain through reconciliation"
        )


def validate_invalid_fixture_semantics(path: Path, fixture: dict[str, Any]) -> None:
    expected_error_id = fixture.get("expected_error_id")
    if not expected_error_id:
        return

    records = fixture.get("records", {})
    operation = first_rejecting_operation(fixture)
    body = operation_body(fixture, operation)

    if expected_error_id == "stale_request_timestamp":
        header_timestamp = parse_utc_timestamp(
            operation.get("headers", {}).get("Jarvis-Request-Timestamp")
        )
        body_timestamp = timestamp_field(body) if isinstance(body, dict) else None
        if (
            header_timestamp is None
            or body_timestamp is None
            or (body_timestamp - header_timestamp).total_seconds()
            < STALE_TIMESTAMP_MIN_SECONDS
        ):
            raise FixtureError(
                f"{rel(path)}: stale_request_timestamp fixture MUST use stale timestamp"
            )

    elif expected_error_id == "missing_policy":
        if not isinstance(body, dict):
            raise FixtureError(f"{rel(path)}: missing_policy fixture MUST submit WorkSession")
        policy_id = body.get("policy_id")
        if not isinstance(policy_id, str) or policy_id in ids_for(records, "policies"):
            raise FixtureError(
                f"{rel(path)}: missing_policy fixture MUST reference absent Policy"
            )

    elif expected_error_id == "missing_policy_decision":
        if not isinstance(body, dict):
            raise FixtureError(
                f"{rel(path)}: missing_policy_decision fixture MUST submit JarvisEvent"
            )
        actor = actor_by_id(records, body.get("actor_id"))
        payload = body.get("payload", {})
        has_policy_decision_ref = any(
            key in body or (isinstance(payload, dict) and key in payload)
            for key in ("policy_decision_id", "policy_decision_ref", "policy_decision_refs")
        )
        if actor is None or actor.get("type") != "agent" or has_policy_decision_ref:
            raise FixtureError(
                f"{rel(path)}: missing_policy_decision fixture MUST be AgentWorker "
                "state without PolicyDecision"
            )

    elif expected_error_id == "missing_review_resolution":
        if not isinstance(body, dict):
            raise FixtureError(
                f"{rel(path)}: missing_review_resolution fixture MUST submit Request"
            )
        if body.get("status") not in REVIEW_RESOLVED_REQUEST_STATUSES:
            raise FixtureError(
                f"{rel(path)}: missing_review_resolution fixture MUST use review-resolved status"
            )
        if body.get("resolved_at") is None:
            raise FixtureError(
                f"{rel(path)}: missing_review_resolution fixture MUST include resolved_at"
            )
        if body.get("resolved_by_review_id"):
            raise FixtureError(
                f"{rel(path)}: missing_review_resolution fixture MUST omit Review resolution"
            )

    elif expected_error_id == "missing_takeover_resolution":
        if not isinstance(body, dict):
            raise FixtureError(
                f"{rel(path)}: missing_takeover_resolution fixture MUST submit Request"
            )
        if body.get("status") != "takeover" or body.get("resolved_by_takeover_id"):
            raise FixtureError(
                f"{rel(path)}: missing_takeover_resolution fixture MUST omit Takeover resolution"
            )
        if body.get("resolved_at") is None:
            raise FixtureError(
                f"{rel(path)}: missing_takeover_resolution fixture MUST include resolved_at"
            )

    elif expected_error_id == "request_unresolved":
        work_session_id = target_work_session_id(operation, body)
        pending_requests = [
            request
            for request in records_with_status(records, "requests", {"pending"})
            if request.get("work_session_id") == work_session_id
        ]
        if not pending_requests or not isinstance(body, dict):
            raise FixtureError(
                f"{rel(path)}: request_unresolved fixture MUST keep Request pending"
            )
        if (
            body.get("type") != "work_session.completed"
            or body.get("work_session_id") != work_session_id
        ):
            raise FixtureError(
                f"{rel(path)}: request_unresolved fixture MUST attempt terminal completion"
            )

    elif expected_error_id == "invalid_approval_scope":
        if not isinstance(body, dict) or body.get("decision") not in {"approve", "narrow"}:
            raise FixtureError(
                f"{rel(path)}: invalid_approval_scope fixture MUST submit approve or narrow Review"
            )
        approval_scope = body.get("approval_scope")
        request_id = request_id_from_target_ref(body.get("target_ref"))
        request = record_by_id(records, "requests", request_id)
        if (
            not isinstance(request, dict)
            or request.get("work_session_id") != body.get("work_session_id")
        ):
            raise FixtureError(
                f"{rel(path)}: invalid_approval_scope fixture MUST target Request"
            )
        required = {
            "request_id",
            "review_id",
            "policy_decision_id",
            "normalized_action_hash",
            "approved_action",
            "allowed_scope",
            "denied_scope",
            "expires_at",
            "max_uses",
            "applies_to_work_session_id",
            "applies_to_actor_id",
        }
        if not isinstance(approval_scope, dict):
            return
        if not required <= set(approval_scope):
            return
        approval_scope_valid = (
            isinstance(request, dict)
            and approval_scope.get("request_id") == request.get("id")
            and approval_scope.get("review_id") == body.get("id")
            and approval_scope.get("policy_decision_id") == request.get("policy_decision_id")
            and approval_scope.get("applies_to_work_session_id")
            == body.get("work_session_id")
            and approval_scope.get("applies_to_actor_id") == request.get("requester_actor_id")
            and approval_scope.get("approved_action") == request.get("requested_action")
            and is_int(approval_scope.get("max_uses"))
            and approval_scope.get("max_uses") > 0
            and parse_utc_timestamp(approval_scope.get("expires_at")) is not None
            and timestamp_field(body) is not None
            and parse_utc_timestamp(approval_scope.get("expires_at")) > timestamp_field(body)
            and isinstance(approval_scope.get("normalized_action_hash"), str)
            and approval_scope["normalized_action_hash"].startswith("hash:")
            and isinstance(approval_scope.get("approved_action"), dict)
            and isinstance(approval_scope.get("allowed_scope"), dict)
            and isinstance(approval_scope.get("denied_scope"), dict)
        )
        if approval_scope_valid:
            raise FixtureError(
                f"{rel(path)}: invalid_approval_scope fixture MUST have invalid bounds"
            )

    elif expected_error_id == "stale_takeover_epoch":
        active_takeovers = [
            takeover
            for takeover in all_records(records, "takeovers")
            if takeover.get("state") == "human_active"
        ]
        actor = actor_by_id(records, operation.get("actor_id"))
        work_session_id = target_work_session_id(operation, body)
        active_takeover = next(
            (
                takeover
                for takeover in active_takeovers
                if takeover.get("work_session_id") == work_session_id
            ),
            None,
        )
        operation_snapshot = work_session_snapshot_for_operation(records, operation, body)
        attempted_lock_epoch = operation.get("attempted_takeover_lock_epoch")
        active_lock_epoch = active_takeover.get("lock_epoch") if active_takeover else None
        stale_epoch = (
            isinstance(body, dict)
            and active_takeover is not None
            and body.get("work_session_id") == active_takeover.get("work_session_id")
            and body.get("actor_id") == operation.get("actor_id")
            and is_int(attempted_lock_epoch)
            and is_int(active_lock_epoch)
            and attempted_lock_epoch >= 0
            and active_lock_epoch >= 0
            and attempted_lock_epoch < active_lock_epoch
        )
        if (
            active_takeover is None
            or actor is None
            or actor.get("type") != "agent"
            or operation_snapshot is None
            or operation_snapshot.get("last_event_hash")
            != operation.get("headers", {}).get("Jarvis-Previous-Event-Hash")
            or not stale_epoch
        ):
            raise FixtureError(
                f"{rel(path)}: stale_takeover_epoch fixture MUST show AgentWorker "
                "continuing during human_active Takeover"
            )

    elif expected_error_id == "invalid_evidence_export_state":
        error_field = fixture.get("expected_error_field")
        if not isinstance(error_field, str) or not error_field.endswith(".status"):
            raise FixtureError(
                f"{rel(path)}: invalid_evidence_export_state fixture MUST target status"
            )
        target_ref = error_field.removesuffix(".status")
        work_session = resolved_state_ref(path, fixture, target_ref)
        if (
            not isinstance(work_session, dict)
            or work_session.get("id") != operation.get("work_session_id")
            or work_session.get("status") in TERMINAL_WORK_SESSION_STATES
        ):
            raise FixtureError(
                f"{rel(path)}: invalid_evidence_export_state fixture MUST use non-terminal state"
            )

    elif expected_error_id == "sealed_work_session_mutation":
        operation_snapshot = work_session_snapshot_for_operation(records, operation, body)
        if (
            operation_snapshot is None
            or operation_snapshot.get("status") not in TERMINAL_WORK_SESSION_STATES
            or operation.get("method") == "GET"
            or not isinstance(body, dict)
            or body.get("work_session_id") != operation_snapshot.get("id")
        ):
            raise FixtureError(
                f"{rel(path)}: sealed_work_session_mutation fixture MUST mutate sealed WorkSession"
            )

    elif expected_error_id == "sealed_evidence_mutation":
        if not isinstance(body, dict) or body.get("type") != "evidence_manifest.mutated":
            raise FixtureError(
                f"{rel(path)}: sealed_evidence_mutation fixture MUST submit evidence mutation event"
            )
        if not all_records(records, "evidence_manifests"):
            raise FixtureError(
                f"{rel(path)}: sealed_evidence_mutation fixture MUST include EvidenceManifest"
            )
        evidence_manifest = next(iter(all_records(records, "evidence_manifests")), {})
        if evidence_manifest.get("work_session_id") != body.get("work_session_id"):
            raise FixtureError(
                f"{rel(path)}: sealed_evidence_mutation fixture MUST target sealed EvidenceManifest"
            )

    elif expected_error_id == "silent_memory_mutation":
        if not isinstance(body, dict):
            raise FixtureError(
                f"{rel(path)}: silent_memory_mutation fixture MUST submit MemoryProposal"
            )
        if body.get("review_required") is not False or body.get("status") != "accepted":
            raise FixtureError(
                f"{rel(path)}: silent_memory_mutation fixture MUST silently accept memory"
            )
        if not body.get("review_refs"):
            raise FixtureError(
                f"{rel(path)}: silent_memory_mutation fixture MUST isolate review_required"
            )

    elif expected_error_id == "silent_skill_activation":
        if not isinstance(body, dict):
            raise FixtureError(
                f"{rel(path)}: silent_skill_activation fixture MUST submit SkillProposal"
            )
        if body.get("status") != "accepted" or body.get("review_refs"):
            raise FixtureError(
                f"{rel(path)}: silent_skill_activation fixture MUST activate without review"
            )

    elif expected_error_id == "outcome_report_without_learning_record":
        if not isinstance(body, dict):
            raise FixtureError(
                f"{rel(path)}: outcome_report_without_learning_record fixture MUST submit OutcomeReport"
            )
        if body.get("learning_record_refs"):
            raise FixtureError(
                f"{rel(path)}: outcome_report_without_learning_record fixture MUST omit learning refs"
            )

    elif expected_error_id == "outcome_report_requires_terminal_source":
        if not isinstance(body, dict):
            raise FixtureError(
                f"{rel(path)}: outcome_report_requires_terminal_source fixture MUST submit OutcomeReport"
            )
        error_field = fixture.get("expected_error_field")
        if not isinstance(error_field, str) or not error_field.endswith(".status"):
            raise FixtureError(
                f"{rel(path)}: outcome_report_requires_terminal_source fixture MUST target status"
            )
        target_ref = error_field.removesuffix(".status")
        referenced_work_session = resolved_state_ref(path, fixture, target_ref)
        work_session_id = body.get("work_session_id")
        candidates = [
            state
            for state in all_records(records, "work_sessions")
            if state.get("id") == work_session_id
        ]
        if not candidates:
            raise FixtureError(
                f"{rel(path)}: outcome_report_requires_terminal_source fixture MUST include source WorkSession"
            )
        if referenced_work_session not in candidates:
            raise FixtureError(
                f"{rel(path)}: outcome_report_requires_terminal_source fixture expected_error_field MUST reference the source WorkSession"
            )
        if referenced_work_session.get("status") in TERMINAL_WORK_SESSION_STATES:
            raise FixtureError(
                f"{rel(path)}: outcome_report_requires_terminal_source fixture MUST target non-terminal status"
            )
        if any(state.get("status") in TERMINAL_WORK_SESSION_STATES for state in candidates):
            raise FixtureError(
                f"{rel(path)}: outcome_report_requires_terminal_source fixture MUST keep source WorkSession non-terminal"
            )
        if not body.get("learning_record_refs"):
            raise FixtureError(
                f"{rel(path)}: outcome_report_requires_terminal_source fixture MUST keep learning refs valid"
            )

    elif expected_error_id == "unauthorized_actor":
        if not isinstance(body, dict):
            raise FixtureError(
                f"{rel(path)}: unauthorized_actor fixture MUST submit protocol body"
            )
        actor_id = operation.get("actor_id")
        actor = actor_by_id(records, actor_id)
        worker = worker_for_actor(records, actor)
        grants = worker_grants(worker)
        if actor is None:
            raise FixtureError(
                f"{rel(path)}: unauthorized_actor fixture MUST use represented Actor"
            )
        if operation.get("operation_id") == "createWorkSession":
            if (
                actor_id == body.get("created_by_actor_id")
                and "policy:own" in grants
            ):
                raise FixtureError(
                    f"{rel(path)}: unauthorized_actor fixture MUST use Actor outside authority"
                )
        else:
            required_grants_by_operation = {
                "recordReview": "review:approve",
                "recordTakeover": "takeover:start",
                "appendJarvisEvent": "action:execute_after_policy",
            }
            required_grant = required_grants_by_operation.get(operation.get("operation_id"))
            if required_grant is not None and required_grant in grants:
                raise FixtureError(
                    f"{rel(path)}: unauthorized_actor fixture MUST use Actor outside authority"
                )


def validate_assertion_coverage(fixtures: list[dict[str, Any]]) -> None:
    covered = {
        assertion.get("class")
        for fixture in fixtures
        for assertion in fixture.get("assertions", [])
        if isinstance(assertion, dict)
    }
    missing = sorted(GLOBAL_REQUIRED_ASSERTION_CLASSES - covered)
    if missing:
        raise FixtureError(
            "docs/conformance/fixtures: missing assertion class coverage: "
            + ", ".join(missing)
        )


def represented_hash_set(fixture: dict[str, Any]) -> set[str]:
    hashes = {PROTOCOL_GENESIS_HASH}
    for event in fixture.get("records", {}).get("jarvis_events", {}).values():
        if isinstance(event, dict) and isinstance(event.get("event_hash"), str):
            hashes.add(event["event_hash"])
    for work_session in fixture.get("records", {}).get("work_sessions", {}).values():
        if isinstance(work_session, dict) and isinstance(
            work_session.get("last_event_hash"), str
        ):
            hashes.add(work_session["last_event_hash"])
    return hashes


def validate_event_chain(path: Path, fixture: dict[str, Any]) -> None:
    seen_hashes: set[str] = set()
    seen_sequences: set[int] = set()
    explicit_event_hashes = {
        event["event_hash"]
        for event in fixture.get("records", {}).get("jarvis_events", {}).values()
        if isinstance(event, dict) and isinstance(event.get("event_hash"), str)
    }
    snapshot_hashes = {
        work_session["last_event_hash"]
        for work_session in fixture.get("records", {}).get("work_sessions", {}).values()
        if isinstance(work_session, dict)
        and isinstance(work_session.get("last_event_hash"), str)
        and work_session["last_event_hash"] not in explicit_event_hashes
    }
    represented_predecessors = {PROTOCOL_GENESIS_HASH} | snapshot_hashes
    event_entries = fixture.get("records", {}).get("jarvis_events", {})
    ordered_events = sorted(
        event_entries.items(),
        key=lambda item: item[1].get("sequence", 0)
        if isinstance(item[1], dict)
        else 0,
    )
    explicit_sequence_by_hash = {
            event["event_hash"]: event["sequence"]
            for event in event_entries.values()
            if isinstance(event, dict)
            and isinstance(event.get("event_hash"), str)
            and is_int(event.get("sequence"))
    }
    for event_name, event in ordered_events:
        if not isinstance(event, dict):
            raise FixtureError(f"{rel(path)}: jarvis event {event_name} MUST be an object")
        sequence = event.get("sequence")
        if not is_int(sequence) or sequence <= 0:
            raise FixtureError(
                f"{rel(path)}: jarvis event {event_name} sequence MUST be positive integer"
            )
        if sequence in seen_sequences:
            raise FixtureError(f"{rel(path)}: duplicate jarvis event sequence {sequence}")
        seen_sequences.add(sequence)
        event_hash = event.get("event_hash")
        if not isinstance(event_hash, str):
            raise FixtureError(f"{rel(path)}: jarvis event {event_name} missing event_hash")
        canonicalization = event.get("canonicalization")
        if not isinstance(canonicalization, dict):
            raise FixtureError(
                f"{rel(path)}: jarvis event {event_name} missing canonicalization"
            )
        if (
            canonicalization.get("serialization") != "json-c14n"
            or canonicalization.get("hash_method") != "sha256"
        ):
            raise FixtureError(
                f"{rel(path)}: jarvis event {event_name} MUST use v0.1 canonicalization"
            )
        if event_hash in seen_hashes:
            raise FixtureError(f"{rel(path)}: duplicate event_hash {event_hash}")
        seen_hashes.add(event_hash)
        previous_hash = event.get("previous_hash")
        if previous_hash not in represented_predecessors:
            raise FixtureError(
                f"{rel(path)}: jarvis event {event_name} previous_hash is undefined"
            )
        previous_sequence = explicit_sequence_by_hash.get(previous_hash)
        if previous_sequence is not None and previous_sequence >= sequence:
            raise FixtureError(
                f"{rel(path)}: jarvis event {event_name} previous_hash points forward"
            )
        represented_predecessors.add(event_hash)


def validate_openapi_refs(path: Path, openapi: dict[str, Any], fixture: dict[str, Any]) -> None:
    for source_ref in fixture.get("source_contract_refs", []):
        if not isinstance(source_ref, str):
            raise FixtureError(f"{rel(path)}: source_contract_refs entries MUST be strings")
        validate_source_ref(path, openapi, source_ref)


def validate_fixture(
    path: Path,
    expected_kind: str,
    openapi: dict[str, Any],
    operations: dict[str, dict[str, Any]],
    protocol_error_ids: set[str],
) -> dict[str, Any]:
    fixture = load_json(path)
    validate_fixture_envelope(path, fixture, expected_kind)

    expected_error_id = fixture.get("expected_error_id")
    if expected_error_id and expected_error_id not in protocol_error_ids:
        raise FixtureError(f"{rel(path)}: expected_error_id missing from OpenAPI")

    validate_openapi_refs(path, openapi, fixture)
    validate_host_shape(path, fixture)
    validate_forbidden_export_fields(path, fixture)
    validate_event_chain(path, fixture)

    for operation in fixture["operations"]:
        if not isinstance(operation, dict):
            raise FixtureError(f"{rel(path)}: operation entries MUST be objects")
        validate_operation(path, fixture, operation, operations)

    for assertion in fixture["assertions"]:
        if not isinstance(assertion, dict):
            raise FixtureError(f"{rel(path)}: assertion entries MUST be objects")
        validate_assertion(path, fixture, assertion)

    validate_golden_path_semantics(path, fixture)
    validate_takeover_path_semantics(path, fixture)
    validate_invalid_fixture_semantics(path, fixture)
    return fixture


def validate_required_fixture_set() -> None:
    valid_files = {path.name for path in VALID_DIR.glob("*.json")}
    expected_valid_files = {"golden-path.json", "takeover-path.json"}
    if valid_files != expected_valid_files:
        missing = sorted(expected_valid_files - valid_files)
        extra = sorted(valid_files - expected_valid_files)
        message = []
        if missing:
            message.append("missing valid fixtures: " + ", ".join(missing))
        if extra:
            message.append("unexpected valid fixtures: " + ", ".join(extra))
        raise FixtureError(
            "docs/conformance/fixtures/valid: " + "; ".join(message)
        )

    invalid_files = {path.name for path in INVALID_DIR.glob("*.json")}
    expected_files = set(REQUIRED_INVALID_FIXTURES)
    missing = sorted(expected_files - invalid_files)
    extra = sorted(invalid_files - expected_files)
    if missing or extra:
        message = []
        if missing:
            message.append("missing invalid fixtures: " + ", ".join(missing))
        if extra:
            message.append("unexpected invalid fixtures: " + ", ".join(extra))
        raise FixtureError("; ".join(message))


def main() -> int:
    try:
        validate_required_fixture_set()
        openapi = load_openapi()
        operations = openapi_operations(openapi)
        protocol_error_ids = schema_enum(openapi, "ProtocolErrorId")

        loaded_fixtures: list[dict[str, Any]] = []
        for path, expected_kind in fixture_files():
            fixture = validate_fixture(
                path,
                expected_kind,
                openapi,
                operations,
                protocol_error_ids,
            )
            loaded_fixtures.append(fixture)
        validate_assertion_coverage(loaded_fixtures)
    except FixtureError as exc:
        return fail(str(exc))

    print("conformance fixtures ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
