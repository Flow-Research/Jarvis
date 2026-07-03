"""Jarvis protocol helper package for v0.1 Protocol Alpha records."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
import re
from typing import Any

from .generated.openapi_types import *  # noqa: F403
from .generated.openapi_types import __all__ as OPENAPI_TYPE_NAMES
from .generated.schema_metadata import (
    OPENAPI_SCHEMA_NAMES,
    PROTOCOL_VERSION,
    SCHEMA_ALLOWED_FIELDS,
    SCHEMA_CLOSED_SCHEMAS,
    SCHEMA_ENUMS,
    SCHEMA_FIELD_CONSTS,
    SCHEMA_FIELD_ENUMS,
    SCHEMA_FORBIDDEN_FIELDS,
    SCHEMA_REQUIRED_FIELDS,
)


WORKSESSION_MUTATION_HEADERS = (
    "Authorization",
    "Jarvis-Protocol-Version",
    "Jarvis-Actor-Id",
    "Jarvis-Idempotency-Key",
    "Jarvis-Request-Timestamp",
    "Jarvis-Expected-WorkSession-Revision",
    "Jarvis-Previous-Event-Hash",
)

NON_WORKSESSION_MUTATION_HEADERS = (
    "Authorization",
    "Jarvis-Protocol-Version",
    "Jarvis-Actor-Id",
    "Jarvis-Idempotency-Key",
    "Jarvis-Request-Timestamp",
)

READ_HEADERS = (
    "Authorization",
    "Jarvis-Protocol-Version",
    "Jarvis-Actor-Id",
)

MUTATION_ONLY_HEADERS = (
    "Jarvis-Idempotency-Key",
    "Jarvis-Request-Timestamp",
    "Jarvis-Expected-WorkSession-Revision",
    "Jarvis-Previous-Event-Hash",
)

TERMINAL_WORK_SESSION_STATES = (
    "completed",
    "failed",
    "cancelled",
    "closed",
)

REVIEW_RESOLVED_REQUEST_STATUSES = (
    "approved",
    "denied",
    "narrowed",
    "answered",
    "needs_revision",
)

FORBIDDEN_EXPORT_KEY_TOKENS = (
    "password",
    "credential",
    "token",
    "secret",
    "private_key",
    "session_cookie",
    "cookie",
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
)

MISSING_HEADER_ERROR_IDS = {
    "Authorization": "unauthorized_actor",
    "Jarvis-Protocol-Version": "missing_protocol_version",
    "Jarvis-Actor-Id": "missing_actor",
    "Jarvis-Idempotency-Key": "missing_idempotency_key",
    "Jarvis-Request-Timestamp": "missing_request_timestamp",
    "Jarvis-Expected-WorkSession-Revision": "missing_expected_work_session_revision",
    "Jarvis-Previous-Event-Hash": "missing_previous_event_hash",
}

OBJECT_BY_OPERATION = {
    "registerWorker": "Worker",
    "registerActor": "Actor",
    "createWorkSession": "WorkSession",
    "appendJarvisEvent": "JarvisEvent",
    "recordPolicyDecision": "PolicyDecision",
    "createRequest": "Request",
    "recordReview": "Review",
    "recordTakeover": "Takeover",
    "recordContribution": "Contribution",
    "createLearningRecord": "LearningRecord",
    "createMemoryProposal": "MemoryProposal",
    "createSkillProposal": "SkillProposal",
    "submitOutcomeReport": "OutcomeReport",
    "exportEvidenceManifest": "EvidenceManifest",
}

OPERATION_BINDINGS_BY_ID = {
    "registerWorker": {"method": "PUT", "path": "/workers/{worker_id}", "statuses": {200, 400}},
    "registerActor": {"method": "PUT", "path": "/actors/{actor_id}", "statuses": {200, 400}},
    "createWorkSession": {"method": "POST", "path": "/work-sessions", "statuses": {201, 400}},
    "getWorkSession": {"method": "GET", "path": "/work-sessions/{work_session_id}", "statuses": {200, 400}},
    "appendJarvisEvent": {
        "method": "POST",
        "path": "/work-sessions/{work_session_id}/events",
        "statuses": {201, 400},
    },
    "recordPolicyDecision": {
        "method": "POST",
        "path": "/work-sessions/{work_session_id}/policy-decisions",
        "statuses": {201, 400},
    },
    "createRequest": {
        "method": "POST",
        "path": "/work-sessions/{work_session_id}/requests",
        "statuses": {201, 400},
    },
    "recordReview": {
        "method": "POST",
        "path": "/work-sessions/{work_session_id}/reviews",
        "statuses": {201, 400},
    },
    "recordTakeover": {
        "method": "POST",
        "path": "/work-sessions/{work_session_id}/takeovers",
        "statuses": {201, 400},
    },
    "recordContribution": {
        "method": "POST",
        "path": "/work-sessions/{work_session_id}/contributions",
        "statuses": {201, 400},
    },
    "createLearningRecord": {
        "method": "POST",
        "path": "/work-sessions/{work_session_id}/learning-records",
        "statuses": {201, 400},
    },
    "createMemoryProposal": {
        "method": "POST",
        "path": "/work-sessions/{work_session_id}/memory-proposals",
        "statuses": {201, 400},
    },
    "createSkillProposal": {
        "method": "POST",
        "path": "/work-sessions/{work_session_id}/skill-proposals",
        "statuses": {201, 400},
    },
    "exportEvidenceManifest": {
        "method": "GET",
        "path": "/work-sessions/{work_session_id}/export",
        "statuses": {200, 400},
    },
    "submitOutcomeReport": {"method": "POST", "path": "/outcome-reports", "statuses": {202, 400}},
}

ACTOR_BODY_FIELD_BY_OPERATION = {
    "createWorkSession": "created_by_actor_id",
    "appendJarvisEvent": "actor_id",
    "recordPolicyDecision": "actor_id",
    "createRequest": "requester_actor_id",
    "recordReview": "reviewer_actor_id",
    "recordTakeover": "controlling_actor_id",
    "createLearningRecord": "created_by_actor_id",
    "createMemoryProposal": "proposed_by_actor_id",
    "createSkillProposal": "proposed_by_actor_id",
    "submitOutcomeReport": "accepted_by_actor_id",
}

PROTOCOL_ERROR_IDS = set(SCHEMA_ENUMS.get("ProtocolErrorId", ()))


@dataclass(frozen=True)
class ValidationResult:
    """Protocol validation result."""

    valid: bool
    errors: list[dict[str, Any]]


class JarvisProtocolValidationError(ValueError):
    """Raised by callers that convert protocol validation errors into exceptions."""

    def __init__(self, error: Mapping[str, Any]) -> None:
        super().__init__(str(error.get("reason", "Jarvis protocol validation error")))
        self.error = dict(error)


def protocol_error(error_id: str, options: Mapping[str, Any] | None = None) -> dict[str, Any]:
    options = options or {}
    if error_id not in PROTOCOL_ERROR_IDS:
        return {
            "error_id": "invalid_export",
            "protocol_version": PROTOCOL_VERSION,
            "object_type": "ProtocolError",
            "field": "error_id",
            "reason": f"ProtocolErrorId MUST exist in the OpenAPI ProtocolErrorId enum: {error_id}",
            "remediation": "Use a Jarvis v0.1 ProtocolErrorId from the OpenAPI contract.",
            "trace_id": options.get("trace_id") or options.get("traceId") or "trace:jarvis-sdk",
        }
    return {
        "error_id": error_id,
        "protocol_version": PROTOCOL_VERSION,
        "object_type": options.get("object_type") or options.get("objectType") or "protocol",
        "field": options.get("field") or "",
        "reason": options.get("reason") or error_id,
        "remediation": options.get("remediation") or "Submit a Jarvis v0.1 compatible record.",
        "trace_id": options.get("trace_id") or options.get("traceId") or "trace:jarvis-sdk",
    }


def validation_result(errors: Sequence[Mapping[str, Any]]) -> ValidationResult:
    return ValidationResult(valid=len(errors) == 0, errors=[dict(error) for error in errors])


def _fail(error_id: str, options: Mapping[str, Any] | None = None) -> ValidationResult:
    return validation_result([protocol_error(error_id, options)])


def _pass() -> ValidationResult:
    return validation_result([])


def _is_plain_object(value: Any) -> bool:
    return isinstance(value, dict)


def _is_nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _timestamp(value: Any) -> datetime | None:
    if not _is_nonempty_string(value):
        return None
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", value):
        return None
    try:
        parsed = datetime.fromisoformat(value.removesuffix("Z") + "+00:00")
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(timezone.utc)


def _get_ref(root: Mapping[str, Any], ref: Any) -> Any:
    if not _is_nonempty_string(ref):
        return None
    current: Any = root
    for part in ref.split("."):
        if not isinstance(current, dict):
            return None
        current = current.get(part)
    return current


def _operation_body(fixture: Mapping[str, Any], operation: Mapping[str, Any] | None) -> Any:
    return _get_ref(fixture, operation.get("body_ref") if operation else None)


def _first_rejecting_operation(fixture: Mapping[str, Any]) -> Mapping[str, Any] | None:
    operations = fixture.get("operations")
    if not isinstance(operations, list):
        return None
    for operation in operations:
        if isinstance(operation, dict) and operation.get("expected_status", 0) >= 400:
            return operation
    return operations[0] if operations and isinstance(operations[0], dict) else None


def _all_records(records: Mapping[str, Any], group: str) -> list[dict[str, Any]]:
    values = records.get(group)
    if not isinstance(values, dict):
        return []
    return [value for value in values.values() if isinstance(value, dict)]


def _record_by_id(records: Mapping[str, Any], group: str, record_id: Any) -> dict[str, Any] | None:
    for record in _all_records(records, group):
        if record.get("id") == record_id:
            return record
    return None


def _ids_for(records: Mapping[str, Any], group: str) -> set[Any]:
    return {record.get("id") for record in _all_records(records, group)}


def _actor_by_id(records: Mapping[str, Any], actor_id: Any) -> dict[str, Any] | None:
    return _record_by_id(records, "actors", actor_id)


def _worker_for_actor(records: Mapping[str, Any], actor: Mapping[str, Any] | None) -> dict[str, Any] | None:
    return _record_by_id(records, "workers", actor.get("worker_id")) if actor else None


def _worker_grants(worker: Mapping[str, Any] | None) -> set[str]:
    scope = worker.get("authority_scope") if worker else None
    grants = scope.get("grants") if isinstance(scope, dict) else []
    return {grant for grant in grants if isinstance(grant, str)} if isinstance(grants, list) else set()


def _operation_method(operation: Mapping[str, Any] | None) -> Any:
    if operation:
        binding = OPERATION_BINDINGS_BY_ID.get(operation.get("operation_id"))
        return binding["method"] if binding else operation.get("method")
    return None


def _operation_path(operation: Mapping[str, Any] | None) -> str:
    if operation:
        binding = OPERATION_BINDINGS_BY_ID.get(operation.get("operation_id"))
        return binding["path"] if binding else operation.get("path", "")
    return ""


def _operation_path_matches_template(template: str, path: Any) -> bool:
    if not _is_nonempty_string(template) or not _is_nonempty_string(path):
        return False
    parts = []
    for segment in template.split("/"):
        if re.fullmatch(r"\{[^/]+\}", segment):
            parts.append(r"[^/]+")
        else:
            parts.append(re.escape(segment))
    return re.fullmatch("/".join(parts), path) is not None


def _operation_binding_error(operation: Mapping[str, Any] | None) -> dict[str, Any] | None:
    operation_id = operation.get("operation_id") if operation else None
    binding = OPERATION_BINDINGS_BY_ID.get(operation_id)
    if not binding:
        return protocol_error(
            "invalid_export",
            {
                "object_type": "FixtureOperation",
                "field": "operation_id",
                "reason": "Fixture operation_id MUST exist in the Jarvis OpenAPI binding.",
            },
        )
    if operation.get("method") != binding["method"]:
        return protocol_error(
            "invalid_export",
            {
                "object_type": "FixtureOperation",
                "field": "method",
                "reason": "Fixture operation method MUST match the Jarvis OpenAPI binding.",
            },
        )
    if not _operation_path_matches_template(binding["path"], operation.get("path")):
        return protocol_error(
            "invalid_export",
            {
                "object_type": "FixtureOperation",
                "field": "path",
                "reason": "Fixture operation path MUST match the Jarvis OpenAPI binding.",
            },
        )
    if operation.get("expected_status") not in binding["statuses"]:
        return protocol_error(
            "invalid_export",
            {
                "object_type": "FixtureOperation",
                "field": "expected_status",
                "reason": "Fixture operation expected_status MUST match the Jarvis OpenAPI binding.",
            },
        )
    return None


def _target_work_session_id(operation: Mapping[str, Any] | None, body: Mapping[str, Any] | None) -> Any:
    if operation and operation.get("work_session_id") is not None:
        return operation.get("work_session_id")
    if body and body.get("work_session_id") is not None:
        return body.get("work_session_id")
    return body.get("id") if body else None


def _request_id_from_target_ref(target_ref: Any) -> str | None:
    if _is_nonempty_string(target_ref) and target_ref.startswith("request:"):
        return target_ref.removeprefix("request:")
    return None


def _record_timestamp(record: Mapping[str, Any] | None) -> datetime | None:
    if not isinstance(record, dict):
        return None
    for field in ("created_at", "timestamp", "generated_at", "received_at"):
        parsed = _timestamp(record.get(field))
        if parsed is not None:
            return parsed
    return None


def _work_session_snapshot_for_operation(
    records: Mapping[str, Any],
    operation: Mapping[str, Any] | None,
    body: Mapping[str, Any] | None,
) -> dict[str, Any] | None:
    work_session_id = _target_work_session_id(operation, body)
    headers = operation.get("headers", {}) if operation else {}
    revision = headers.get("Jarvis-Expected-WorkSession-Revision") if isinstance(headers, dict) else None
    previous_hash = headers.get("Jarvis-Previous-Event-Hash") if isinstance(headers, dict) else None
    for snapshot in _all_records(records, "work_sessions"):
        if snapshot.get("id") != work_session_id:
            continue
        if revision is not None and snapshot.get("revision") != revision:
            continue
        if previous_hash is not None and snapshot.get("last_event_hash") != previous_hash:
            continue
        return snapshot
    return None


def _outcome_report_source_work_session(
    records: Mapping[str, Any],
    outcome_report: Mapping[str, Any] | None,
) -> dict[str, Any] | None:
    work_session_id = outcome_report.get("work_session_id") if outcome_report else None
    candidates = [
        snapshot
        for snapshot in _all_records(records, "work_sessions")
        if snapshot.get("id") == work_session_id
    ]
    for snapshot in candidates:
        if snapshot.get("status") in TERMINAL_WORK_SESSION_STATES:
            return snapshot
    return candidates[0] if candidates else None


def _evidence_manifest_source_work_session(
    fixture: Mapping[str, Any],
    evidence_manifest: Mapping[str, Any] | None,
    operation: Mapping[str, Any] | None,
) -> dict[str, Any] | None:
    records = fixture.get("records", {}) if isinstance(fixture.get("records"), dict) else {}
    expected_field = fixture.get("expected_error_field")
    if (
        fixture.get("expected_error_id") == "invalid_evidence_export_state"
        and _is_nonempty_string(expected_field)
        and expected_field.endswith(".status")
    ):
        referenced = _get_ref(fixture, expected_field.removesuffix(".status"))
        if isinstance(referenced, dict):
            return referenced
    work_session_id = evidence_manifest.get("work_session_id") if isinstance(evidence_manifest, dict) else None
    for snapshot in _all_records(records, "work_sessions"):
        if snapshot.get("id") == work_session_id and snapshot.get("status") in TERMINAL_WORK_SESSION_STATES:
            return snapshot
    operation_snapshot = _work_session_snapshot_for_operation(records, operation, evidence_manifest)
    if operation_snapshot:
        return operation_snapshot
    for snapshot in _all_records(records, "work_sessions"):
        if snapshot.get("id") == work_session_id:
            return snapshot
    return None


def _operation_body_binding_error(
    operation: Mapping[str, Any] | None,
    body: Mapping[str, Any] | None,
) -> dict[str, Any] | None:
    actor_body_field = ACTOR_BODY_FIELD_BY_OPERATION.get(operation.get("operation_id") if operation else None)
    if not actor_body_field or not isinstance(body, dict):
        return None
    headers = operation.get("headers", {}) if operation else {}
    header_actor_id = headers.get("Jarvis-Actor-Id") if isinstance(headers, dict) else None
    if body.get(actor_body_field) != header_actor_id:
        return protocol_error(
            "actor_body_id_mismatch",
            {
                "field": actor_body_field,
                "reason": f"{actor_body_field} MUST match Jarvis-Actor-Id.",
            },
        )
    return None


def _create_work_session_genesis_error(operation: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if not operation or operation.get("operation_id") != "createWorkSession":
        return None
    headers = operation.get("headers", {})
    revision = headers.get("Jarvis-Expected-WorkSession-Revision") if isinstance(headers, dict) else None
    previous_hash = headers.get("Jarvis-Previous-Event-Hash") if isinstance(headers, dict) else None
    if revision != 0:
        return protocol_error(
            "stale_work_session_revision",
            {
                "field": "headers.Jarvis-Expected-WorkSession-Revision",
                "reason": "createWorkSession MUST use WorkSession revision 0.",
            },
        )
    if previous_hash != "hash:protocol-genesis":
        return protocol_error(
            "invalid_previous_event_hash",
            {
                "field": "headers.Jarvis-Previous-Event-Hash",
                "reason": "createWorkSession MUST use hash:protocol-genesis as previous event hash.",
            },
        )
    return None


def _create_work_session_body_genesis_error(body: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(body, dict):
        return None
    if body.get("revision") != 0:
        return protocol_error(
            "stale_work_session_revision",
            {
                "field": "revision",
                "reason": "createWorkSession body MUST start at WorkSession revision 0.",
            },
        )
    if body.get("last_event_hash") != "hash:protocol-genesis":
        return protocol_error(
            "invalid_previous_event_hash",
            {
                "field": "last_event_hash",
                "reason": "createWorkSession body MUST start from hash:protocol-genesis.",
            },
        )
    return None


def _operation_state_error(
    records: Mapping[str, Any],
    operation: Mapping[str, Any] | None,
    body: Mapping[str, Any] | None,
) -> dict[str, Any] | None:
    if operation and operation.get("operation_id") == "createWorkSession":
        return _create_work_session_genesis_error(operation) or _create_work_session_body_genesis_error(body)
    path = _operation_path(operation)
    if not isinstance(path, str) or not path.startswith("/work-sessions"):
        return None
    headers = operation.get("headers", {}) if operation else {}
    if not isinstance(headers, dict):
        return None
    revision = headers.get("Jarvis-Expected-WorkSession-Revision")
    previous_hash = headers.get("Jarvis-Previous-Event-Hash")
    if revision is None or previous_hash is None:
        return None
    work_session_id = _target_work_session_id(operation, body)
    represented_states = [
        {
            "revision": state.get("revision"),
            "hash": state.get("last_event_hash"),
        }
        for state in _all_records(records, "work_sessions")
        if state.get("id") == work_session_id
    ]
    represented_states.extend(
        {
            "revision": event.get("sequence"),
            "hash": event.get("event_hash"),
        }
        for event in _all_records(records, "jarvis_events")
        if event.get("work_session_id") == work_session_id
    )
    if not represented_states:
        return None
    if any(state["revision"] == revision and state["hash"] == previous_hash for state in represented_states):
        return None
    if any(state["hash"] == previous_hash for state in represented_states):
        return protocol_error(
            "stale_work_session_revision",
            {
                "field": "headers.Jarvis-Expected-WorkSession-Revision",
                "reason": "Expected WorkSession revision does not match the represented previous hash state.",
            },
        )
    return protocol_error(
        "invalid_previous_event_hash",
        {
            "field": "headers.Jarvis-Previous-Event-Hash",
            "reason": "Previous event hash is not represented for the WorkSession.",
        },
    )


def _path_for_key(base_path: str, key: str) -> str:
    return f"{base_path}.{key}" if base_path else key


def _compact_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def find_forbidden_host_private_field(value: Any, base_path: str = "") -> str | None:
    if isinstance(value, list):
        for index, item in enumerate(value):
            found = find_forbidden_host_private_field(item, f"{base_path}[{index}]")
            if found:
                return found
        return None
    if not isinstance(value, dict):
        return None
    for key, child in value.items():
        normalized = str(key).lower()
        compact = _compact_key(str(key))
        if normalized in FORBIDDEN_EXPORT_KEY_TOKENS or any(
            token in normalized for token in FORBIDDEN_EXPORT_KEY_TOKENS
        ) or compact in {_compact_key(token) for token in FORBIDDEN_EXPORT_KEY_TOKENS} or any(
            _compact_key(token) in compact for token in FORBIDDEN_EXPORT_KEY_TOKENS
        ):
            return _path_for_key(base_path, str(key))
        found = find_forbidden_host_private_field(child, _path_for_key(base_path, str(key)))
        if found:
            return found
    return None


def _evidence_manifest_export_error(
    evidence_manifest: Mapping[str, Any] | None,
    work_session: Mapping[str, Any] | None,
) -> dict[str, Any] | None:
    forbidden = find_forbidden_host_private_field(evidence_manifest)
    if forbidden:
        return protocol_error(
            "forbidden_host_private_field",
            {
                "object_type": "EvidenceManifest",
                "field": forbidden,
                "reason": "EvidenceManifest MUST exclude host-private fields.",
            },
        )
    work_session_status = work_session.get("status") if isinstance(work_session, dict) else None
    if not work_session_status:
        return protocol_error(
            "invalid_evidence_export_state",
            {
                "object_type": "EvidenceManifest",
                "field": "work_session.status",
                "reason": "EvidenceManifest export requires a terminal WorkSession source.",
            },
        )
    if work_session_status and work_session_status not in TERMINAL_WORK_SESSION_STATES:
        return protocol_error(
            "invalid_evidence_export_state",
            {
                "object_type": "EvidenceManifest",
                "field": "work_session.status",
                "reason": "EvidenceManifest export requires a terminal WorkSession source.",
            },
        )
    if (
        not isinstance(work_session, dict)
        or not isinstance(evidence_manifest, dict)
        or work_session.get("id") != evidence_manifest.get("work_session_id")
    ):
        return protocol_error(
            "invalid_evidence_export_state",
            {
                "object_type": "EvidenceManifest",
                "field": "work_session_id",
                "reason": "EvidenceManifest source WorkSession id MUST match EvidenceManifest.work_session_id.",
            },
        )
    return None


def _prior_policy_decision_exists(
    records: Mapping[str, Any],
    actor_id: Any,
    work_session_id: Any,
    event_timestamp: datetime | None,
) -> bool:
    for decision in _all_records(records, "policy_decisions"):
        if decision.get("actor_id") != actor_id:
            continue
        if decision.get("work_session_id") != work_session_id:
            continue
        decision_timestamp = _record_timestamp(decision)
        if event_timestamp is not None and decision_timestamp is not None and decision_timestamp > event_timestamp:
            continue
        return True
    return False


def _accepted_operation_error(
    records: Mapping[str, Any],
    operation: Mapping[str, Any],
    body: Mapping[str, Any] | None,
) -> dict[str, Any] | None:
    if operation.get("operation_id") != "appendJarvisEvent" or not isinstance(body, dict):
        return None
    actor = _actor_by_id(records, body.get("actor_id"))
    if not actor or actor.get("type") != "agent":
        return None
    if body.get("type") == "policy_decision.recorded":
        return None
    has_prior_policy_decision = _prior_policy_decision_exists(
        records,
        body.get("actor_id"),
        body.get("work_session_id"),
        _record_timestamp(body),
    )
    if has_prior_policy_decision:
        return None
    return protocol_error(
        "missing_policy_decision",
        {
            "field": "records.jarvis_events",
            "reason": "AgentWorker action state requires a prior PolicyDecision.",
        },
    )


def validate_schema_record(object_type: str, record: Any) -> ValidationResult:
    if object_type not in OPENAPI_SCHEMA_NAMES:
        return _fail(
            "invalid_export",
            {
                "object_type": object_type,
                "field": "object_type",
                "reason": f"{object_type} MUST be defined by the OpenAPI schema.",
            },
        )
    if not isinstance(record, dict):
        return _fail(
            "invalid_export",
            {
                "object_type": object_type,
                "field": object_type,
                "reason": f"{object_type} MUST be an object.",
            },
        )
    for field in SCHEMA_REQUIRED_FIELDS.get(object_type, ()):
        if field not in record:
            return _fail(
                "invalid_export",
                {
                    "object_type": object_type,
                    "field": field,
                    "reason": f"{object_type}.{field} is required.",
                },
            )
    for field, expected in SCHEMA_FIELD_CONSTS.get(object_type, {}).items():
        if field in record and record[field] != expected:
            return _fail(
                "invalid_export",
                {
                    "object_type": object_type,
                    "field": field,
                    "reason": f"{object_type}.{field} MUST be {expected}.",
                },
            )
    for field, allowed_values in SCHEMA_FIELD_ENUMS.get(object_type, {}).items():
        if field in record and record[field] not in allowed_values:
            return _fail(
                "unknown_state",
                {
                    "object_type": object_type,
                    "field": field,
                    "reason": f"{object_type}.{field} MUST match the OpenAPI enum.",
                },
            )
    forbidden = set(SCHEMA_FORBIDDEN_FIELDS.get(object_type, ()))
    closed = object_type in set(SCHEMA_CLOSED_SCHEMAS)
    allowed = set(SCHEMA_ALLOWED_FIELDS.get(object_type, ()))
    for field in record:
        if field in forbidden:
            return _fail(
                "forbidden_host_private_field",
                {
                    "object_type": object_type,
                    "field": field,
                    "reason": f"{object_type}.{field} is forbidden in portable protocol records.",
                },
            )
        if closed and field not in allowed:
            return _fail(
                "invalid_export",
                {
                    "object_type": object_type,
                    "field": field,
                    "reason": f"{object_type}.{field} is not defined by the closed OpenAPI schema.",
                },
            )
    return _pass()


def validate_headers(headers: Any, options: Mapping[str, Any] | None = None) -> ValidationResult:
    options = options or {}
    if not isinstance(headers, dict):
        return _fail(
            "missing_protocol_version",
            {
                "field": "headers",
                "reason": "Jarvis operation headers MUST be an object.",
            },
        )
    required_headers = options.get("required_headers") or WORKSESSION_MUTATION_HEADERS
    for header in required_headers:
        if header not in headers:
            return _fail(
                MISSING_HEADER_ERROR_IDS.get(header, "invalid_export"),
                {
                    "field": f"headers.{header}",
                    "reason": f"{header} is required.",
                },
            )
    for header in ("Authorization", "Jarvis-Actor-Id", "Jarvis-Idempotency-Key"):
        if header in headers and not _is_nonempty_string(headers[header]):
            return _fail(
                MISSING_HEADER_ERROR_IDS.get(header, "missing_actor"),
                {
                    "field": f"headers.{header}",
                    "reason": f"{header} MUST be a nonempty string.",
                },
            )
    if headers.get("Jarvis-Protocol-Version") != PROTOCOL_VERSION:
        return _fail(
            "unsupported_protocol_version",
            {
                "field": "headers.Jarvis-Protocol-Version",
                "reason": "Jarvis-Protocol-Version MUST be v0.1.",
            },
        )
    request_timestamp = headers.get("Jarvis-Request-Timestamp")
    request_timestamp_present = "Jarvis-Request-Timestamp" in headers
    parsed_request_timestamp = _timestamp(request_timestamp)
    if (
        ("Jarvis-Request-Timestamp" in required_headers or request_timestamp_present)
        and parsed_request_timestamp is None
    ):
        return _fail(
            "missing_request_timestamp",
            {
                "field": "headers.Jarvis-Request-Timestamp",
                "reason": "Jarvis-Request-Timestamp MUST be an RFC3339 UTC timestamp.",
            },
        )
    now = options.get("now")
    if parsed_request_timestamp is not None and isinstance(now, datetime):
        now_utc = now.astimezone(timezone.utc) if now.tzinfo else now.replace(tzinfo=timezone.utc)
        delta_ms = (parsed_request_timestamp - now_utc).total_seconds() * 1000
        max_past_skew_ms = options.get("max_past_skew_ms") or options.get("max_skew_ms") or 300_000
        max_future_skew_ms = options.get("max_future_skew_ms") or 60_000
        if delta_ms < -max_past_skew_ms or delta_ms > max_future_skew_ms:
            return _fail(
                "stale_request_timestamp",
                {
                    "field": "headers.Jarvis-Request-Timestamp",
                    "reason": "Jarvis-Request-Timestamp is outside the accepted skew.",
                },
            )
    revision = headers.get("Jarvis-Expected-WorkSession-Revision")
    revision_present = "Jarvis-Expected-WorkSession-Revision" in headers
    if (
        ("Jarvis-Expected-WorkSession-Revision" in required_headers or revision_present)
        and (not _is_int(revision) or revision < 0)
    ):
        return _fail(
            "missing_expected_work_session_revision",
            {
                "field": "headers.Jarvis-Expected-WorkSession-Revision",
                "reason": "Jarvis-Expected-WorkSession-Revision MUST be a nonnegative integer.",
            },
        )
    previous_hash = headers.get("Jarvis-Previous-Event-Hash")
    previous_hash_present = "Jarvis-Previous-Event-Hash" in headers
    if (
        ("Jarvis-Previous-Event-Hash" in required_headers or previous_hash_present)
        and (
            not _is_nonempty_string(previous_hash)
            or not previous_hash.startswith("hash:")
        )
    ):
        return _fail(
            "invalid_previous_event_hash",
            {
                "field": "headers.Jarvis-Previous-Event-Hash",
                "reason": "Jarvis-Previous-Event-Hash MUST use the hash: prefix.",
            },
        )
    return _pass()


def validate_mutation_headers(headers: Any, options: Mapping[str, Any] | None = None) -> ValidationResult:
    options = dict(options or {})
    work_session_scoped = options.get("work_session_scoped", True)
    options["required_headers"] = (
        WORKSESSION_MUTATION_HEADERS
        if work_session_scoped
        else NON_WORKSESSION_MUTATION_HEADERS
    )
    return validate_headers(headers, options)


def validate_read_headers(headers: Any, options: Mapping[str, Any] | None = None) -> ValidationResult:
    options = dict(options or {})
    options["required_headers"] = READ_HEADERS
    result = validate_headers(headers, options)
    if not result.valid:
        return result
    forbidden_header = next((header for header in MUTATION_ONLY_HEADERS if header in headers), None)
    if forbidden_header:
        return _fail(
            "invalid_export",
            {
                "object_type": "headers",
                "field": f"headers.{forbidden_header}",
                "reason": "Read operations MUST NOT include mutation-only headers.",
            },
        )
    return result


def validate_operation_headers(
    operation: Mapping[str, Any] | None,
    options: Mapping[str, Any] | None = None,
) -> ValidationResult:
    options = dict(options or {})
    method = _operation_method(operation)
    path = _operation_path(operation)
    work_session_scoped = isinstance(path, str) and path.startswith("/work-sessions")
    header_result = (
        validate_read_headers(operation.get("headers") if operation else None, options)
        if method == "GET"
        else validate_mutation_headers(
            operation.get("headers") if operation else None,
            {
                **options,
                "work_session_scoped": work_session_scoped,
            },
        )
    )
    if not header_result.valid:
        return header_result
    headers = operation.get("headers", {}) if operation else {}
    if operation.get("actor_id") != headers.get("Jarvis-Actor-Id"):
        return _fail(
            "actor_body_id_mismatch",
            {
                "field": "headers.Jarvis-Actor-Id",
                "reason": "operation.actor_id MUST match Jarvis-Actor-Id.",
            },
        )
    genesis_error = _create_work_session_genesis_error(operation)
    return validation_result([genesis_error]) if genesis_error else _pass()


def validate_request(request: Any) -> ValidationResult:
    schema = validate_schema_record("Request", request)
    if not schema.valid:
        return schema
    if request.get("status") in {"pending", "acknowledged"}:
        for field in (
            "resolved_at",
            "resolved_by_review_id",
            "resolved_by_takeover_id",
            "closed_by_event_ref",
            "superseded_by_request_id",
        ):
            if field in request:
                return _fail(
                    "invalid_request_transition",
                    {
                        "object_type": "Request",
                        "field": field,
                        "reason": "Pending Request records MUST NOT include resolution fields.",
                    },
                )
    if request.get("status") in REVIEW_RESOLVED_REQUEST_STATUSES and not request.get("resolved_by_review_id"):
        return _fail(
            "missing_review_resolution",
            {
                "object_type": "Request",
                "field": "resolved_by_review_id",
                "reason": "Review-resolved Request states require resolved_by_review_id.",
            },
        )
    if request.get("status") == "takeover" and not request.get("resolved_by_takeover_id"):
        return _fail(
            "missing_takeover_resolution",
            {
                "object_type": "Request",
                "field": "resolved_by_takeover_id",
                "reason": "Takeover Request state requires resolved_by_takeover_id.",
            },
        )
    return _pass()


def validate_approval_scope(
    approval_scope: Any,
    options: Mapping[str, Any] | None = None,
) -> ValidationResult:
    options = options or {}
    schema = validate_schema_record("ApprovalScope", approval_scope)
    if not schema.valid:
        return _fail(
            "invalid_approval_scope",
            {
                "object_type": "ApprovalScope",
                "field": schema.errors[0].get("field"),
                "reason": schema.errors[0].get("reason"),
            },
        )
    request = options.get("request")
    review = options.get("review")
    expires_at = _timestamp(approval_scope.get("expires_at"))
    review_time = _record_timestamp(review if isinstance(review, dict) else None)
    valid = (
        _is_int(approval_scope.get("max_uses"))
        and approval_scope.get("max_uses") > 0
        and expires_at is not None
        and (not review or (review_time is not None and expires_at > review_time))
        and _is_nonempty_string(approval_scope.get("normalized_action_hash"))
        and approval_scope.get("normalized_action_hash", "").startswith("hash:")
        and isinstance(approval_scope.get("approved_action"), dict)
        and isinstance(approval_scope.get("allowed_scope"), dict)
        and isinstance(approval_scope.get("denied_scope"), dict)
        and (not request or approval_scope.get("request_id") == request.get("id"))
        and (not request or approval_scope.get("policy_decision_id") == request.get("policy_decision_id"))
        and (not request or approval_scope.get("applies_to_actor_id") == request.get("requester_actor_id"))
        and (not review or approval_scope.get("review_id") == review.get("id"))
        and (not review or approval_scope.get("applies_to_work_session_id") == review.get("work_session_id"))
    )
    return _pass() if valid else _fail(
        "invalid_approval_scope",
        {
            "object_type": "ApprovalScope",
            "field": "approval_scope",
            "reason": "ApprovalScope MUST be bounded, current, and tied to the Request and Review.",
        },
    )


def validate_review(review: Any, options: Mapping[str, Any] | None = None) -> ValidationResult:
    options = options or {}
    schema = validate_schema_record("Review", review)
    if not schema.valid:
        return schema
    if review.get("decision") in {"approve", "narrow"}:
        return validate_approval_scope(
            review.get("approval_scope"),
            {"request": options.get("request"), "review": review},
        )
    if review.get("decision") == "takeover" and not review.get("takeover_id"):
        return _fail(
            "missing_takeover_resolution",
            {
                "object_type": "Review",
                "field": "takeover_id",
                "reason": "Takeover Review decisions require takeover_id.",
            },
        )
    return _pass()


def validate_takeover(takeover: Any) -> ValidationResult:
    schema = validate_schema_record("Takeover", takeover)
    if not schema.valid:
        return schema
    if takeover.get("state") == "resumed" and (
        not isinstance(takeover.get("reconciliation_refs"), list)
        or not takeover.get("resumed_by_actor_id")
    ):
        return _fail(
            "missing_reconciliation_refs",
            {
                "object_type": "Takeover",
                "field": "reconciliation_refs",
                "reason": "Resumed Takeover records require reconciliation refs and resumed_by_actor_id.",
            },
        )
    return _pass()


def validate_contribution(contribution: Any) -> ValidationResult:
    schema = validate_schema_record("Contribution", contribution)
    if not schema.valid:
        return schema
    contributor_refs = contribution.get("contributor_refs")
    if not isinstance(contributor_refs, list) or len(contributor_refs) == 0:
        return _fail(
            "missing_contribution_actor",
            {
                "object_type": "Contribution",
                "field": "contributor_refs",
                "reason": "Contribution MUST identify contributors.",
            },
        )
    if contribution.get("contributor_type") == "shared" and len(contributor_refs) < 2:
        return _fail(
            "shared_contribution_without_individual_refs",
            {
                "object_type": "Contribution",
                "field": "contributor_refs",
                "reason": "Shared Contribution MUST preserve individual contributor refs.",
            },
        )
    return _pass()


def validate_evidence_manifest(
    evidence_manifest: Any,
    options: Mapping[str, Any] | None = None,
) -> ValidationResult:
    options = options or {}
    schema = validate_schema_record("EvidenceManifest", evidence_manifest)
    if not schema.valid:
        return schema
    export_error = _evidence_manifest_export_error(evidence_manifest, options.get("work_session"))
    if export_error:
        return validation_result([export_error])
    evidence_item_refs = evidence_manifest.get("evidence_item_refs")
    if isinstance(evidence_item_refs, list):
        for index, evidence_item_ref in enumerate(evidence_item_refs):
            item_result = validate_schema_record("EvidenceItemRef", evidence_item_ref)
            if not item_result.valid:
                error = item_result.errors[0]
                return validation_result([
                    protocol_error(
                        error["error_id"],
                        {
                            "object_type": "EvidenceItemRef",
                            "field": f"evidence_item_refs[{index}].{error.get('field', '')}",
                            "reason": error.get("reason"),
                        },
                    )
                ])
    return _pass()


def validate_learning_record(learning_record: Any) -> ValidationResult:
    return validate_schema_record("LearningRecord", learning_record)


def validate_memory_proposal(memory_proposal: Any) -> ValidationResult:
    schema = validate_schema_record("MemoryProposal", memory_proposal)
    if not schema.valid:
        return schema
    if memory_proposal.get("review_required") is not True or (
        memory_proposal.get("status") == "accepted" and not memory_proposal.get("review_refs")
    ):
        return _fail(
            "silent_memory_mutation",
            {
                "object_type": "MemoryProposal",
                "field": "review_required",
                "reason": "MemoryProposal cannot silently mutate durable memory.",
            },
        )
    return _pass()


def validate_skill_proposal(skill_proposal: Any) -> ValidationResult:
    schema = validate_schema_record("SkillProposal", skill_proposal)
    if not schema.valid:
        return schema
    if skill_proposal.get("status") == "accepted" and not skill_proposal.get("review_refs"):
        return _fail(
            "silent_skill_activation",
            {
                "object_type": "SkillProposal",
                "field": "review_refs",
                "reason": "SkillProposal cannot activate without review.",
            },
        )
    return _pass()


def validate_outcome_report(
    outcome_report: Any,
    options: Mapping[str, Any] | None = None,
) -> ValidationResult:
    options = options or {}
    schema = validate_schema_record("OutcomeReport", outcome_report)
    if not schema.valid:
        return schema
    learning_refs = outcome_report.get("learning_record_refs")
    if not isinstance(learning_refs, list) or len(learning_refs) == 0:
        return _fail(
            "outcome_report_without_learning_record",
            {
                "object_type": "OutcomeReport",
                "field": "learning_record_refs",
                "reason": "OutcomeReport MUST create or reference governed learning.",
            },
        )
    work_session = options.get("work_session")
    if (
        not isinstance(work_session, dict)
        or work_session.get("status") not in TERMINAL_WORK_SESSION_STATES
    ):
        return _fail(
            "outcome_report_requires_terminal_source",
            {
                "object_type": "OutcomeReport",
                "field": "work_session.status",
                "reason": "OutcomeReport source WorkSession MUST be terminal.",
            },
        )
    if work_session.get("id") != outcome_report.get("work_session_id"):
        return _fail(
            "outcome_report_requires_terminal_source",
            {
                "object_type": "OutcomeReport",
                "field": "work_session_id",
                "reason": "OutcomeReport source WorkSession id MUST match OutcomeReport.work_session_id.",
            },
        )
    return _pass()


def canonicalize_protocol_value(value: Any) -> str:
    return json.dumps(_sort_protocol_value(value), separators=(",", ":"), ensure_ascii=False)


def _sort_protocol_value(value: Any) -> Any:
    if isinstance(value, list):
        return [_sort_protocol_value(item) for item in value]
    if isinstance(value, dict):
        return {
            key: _sort_protocol_value(value[key])
            for key in sorted(value)
        }
    return value


def hash_protocol_value(value: Any) -> str:
    digest = sha256(canonicalize_protocol_value(value).encode("utf-8")).hexdigest()
    return f"hash:{digest}"


def validate_event_hash_chain(
    events: Any,
    options: Mapping[str, Any] | None = None,
) -> ValidationResult:
    options = options or {}
    if not isinstance(events, list) or len(events) == 0:
        return _fail(
            "missing_jarvis_event",
            {
                "object_type": "JarvisEvent",
                "field": "events",
                "reason": "Event hash-chain validation requires events.",
            },
        )
    seen_sequences: set[int] = set()
    seen_hashes: set[str] = set()
    for event in events:
        sequence = event.get("sequence") if isinstance(event, dict) else None
        if not isinstance(event, dict) or not _is_int(sequence) or sequence <= 0:
            return _fail(
                "invalid_export",
                {
                    "object_type": "JarvisEvent",
                    "field": "sequence",
                    "reason": "JarvisEvent.sequence MUST be a positive integer.",
                },
            )
        if sequence in seen_sequences:
            return _fail(
                "invalid_export",
                {
                    "object_type": "JarvisEvent",
                    "field": "sequence",
                    "reason": "JarvisEvent.sequence MUST be unique.",
                },
            )
        seen_sequences.add(sequence)
        event_hash = event.get("event_hash")
        if not _is_nonempty_string(event_hash) or not event_hash.startswith("hash:"):
            return _fail(
                "invalid_event_hash",
                {
                    "object_type": "JarvisEvent",
                    "field": "event_hash",
                    "reason": "JarvisEvent.event_hash MUST use the hash: prefix.",
                },
            )
        if event_hash in seen_hashes:
            return _fail(
                "invalid_event_hash",
                {
                    "object_type": "JarvisEvent",
                    "field": "event_hash",
                    "reason": "JarvisEvent.event_hash MUST be unique.",
                },
            )
        seen_hashes.add(event_hash)
    ordered = sorted(events, key=lambda event: event["sequence"])
    previous_hash = options.get("genesis_hash") or "hash:protocol-genesis"
    for event in ordered:
        if not isinstance(event, dict) or event.get("previous_hash") != previous_hash:
            return _fail(
                "invalid_previous_event_hash",
                {
                    "object_type": "JarvisEvent",
                    "field": "previous_hash",
                    "reason": "JarvisEvent.previous_hash MUST link to the previous event hash.",
                },
            )
        previous_hash = event["event_hash"]
    return _pass()


def validate_protocol_record(
    object_type: str,
    record: Any,
    options: Mapping[str, Any] | None = None,
) -> ValidationResult:
    options = options or {}
    if object_type in OPENAPI_SCHEMA_NAMES:
        forbidden = find_forbidden_host_private_field(record)
        if forbidden:
            return _fail(
                "forbidden_host_private_field",
                {
                    "object_type": object_type,
                    "field": forbidden,
                    "reason": "Protocol records MUST NOT expose host-private fields.",
                },
            )
    validators = {
        "Request": validate_request,
        "Takeover": validate_takeover,
        "Contribution": validate_contribution,
        "LearningRecord": validate_learning_record,
        "MemoryProposal": validate_memory_proposal,
        "SkillProposal": validate_skill_proposal,
    }
    if object_type == "Review":
        return validate_review(record, options)
    if object_type == "EvidenceManifest":
        return validate_evidence_manifest(record, options)
    if object_type == "OutcomeReport":
        return validate_outcome_report(record, options)
    validator = validators.get(object_type)
    return validator(record) if validator else validate_schema_record(object_type, record)


def _takeover_path_lifecycle_error(fixture: Mapping[str, Any]) -> dict[str, Any] | None:
    if fixture.get("fixture_id") != "valid-takeover-path-v01":
        return None
    request = _get_ref(fixture, "records.requests.takeover")
    human_active = _get_ref(fixture, "records.takeovers.human_active")
    reconciliation_required = _get_ref(
        fixture,
        "records.takeovers.reconciliation_required",
    )
    resumed = _get_ref(fixture, "records.takeovers.resumed")
    started_event = _get_ref(fixture, "records.jarvis_events.takeover_started")
    reconciliation_event = _get_ref(
        fixture,
        "records.jarvis_events.takeover_reconciliation_required",
    )
    resumed_event = _get_ref(fixture, "records.jarvis_events.takeover_resumed")
    takeovers = [human_active, reconciliation_required, resumed]
    if (
        not isinstance(request, dict)
        or request.get("status") != "takeover"
        or not _is_nonempty_string(request.get("resolved_by_takeover_id"))
        or not all(isinstance(takeover, dict) for takeover in takeovers)
    ):
        return protocol_error(
            "invalid_transition",
            {
                "field": "records.takeovers",
                "reason": "Takeover proof MUST include Request resolution and all Takeover lifecycle states.",
            },
        )
    expected_states = ["human_active", "reconciliation_required", "resumed"]
    for takeover, expected_state in zip(takeovers, expected_states, strict=True):
        affected_scope = takeover.get("affected_scope", {})
        if (
            takeover.get("id") != request.get("resolved_by_takeover_id")
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
            return protocol_error(
                "invalid_transition",
                {
                    "field": f"records.takeovers.{expected_state}",
                    "reason": "Takeover lifecycle states MUST bind the same Request, lock epoch, and affected scope.",
                },
            )
    if (
        not isinstance(resumed.get("reconciliation_refs"), list)
        or not resumed.get("reconciliation_refs")
        or not resumed.get("resumed_by_actor_id")
    ):
        return protocol_error(
            "missing_reconciliation_refs",
            {
                "field": "records.takeovers.resumed.reconciliation_refs",
                "reason": "Resumed Takeover records require reconciliation refs and resumed_by_actor_id.",
            },
        )
    if (
        not isinstance(started_event, dict)
        or not isinstance(reconciliation_event, dict)
        or not isinstance(resumed_event, dict)
        or not _is_int(started_event.get("sequence"))
        or not _is_int(reconciliation_event.get("sequence"))
        or not _is_int(resumed_event.get("sequence"))
        or not (
            started_event.get("sequence")
            < reconciliation_event.get("sequence")
            < resumed_event.get("sequence")
        )
        or reconciliation_event.get("previous_hash") != started_event.get("event_hash")
        or resumed_event.get("previous_hash") != reconciliation_event.get("event_hash")
    ):
        return protocol_error(
            "invalid_transition",
            {
                "field": "records.jarvis_events.takeover_reconciliation_required",
                "reason": "Takeover event chain MUST pass through reconciliation_required before resumed.",
            },
        )
    return None


def validate_fixture(fixture: Any) -> ValidationResult:
    if not isinstance(fixture, dict):
        return _fail("invalid_export", {"field": "fixture", "reason": "Fixture MUST be an object."})
    if fixture.get("protocol_version") != PROTOCOL_VERSION:
        return _fail(
            "unsupported_protocol_version",
            {
                "field": "protocol_version",
                "reason": "Fixture protocol_version MUST be v0.1.",
            },
        )
    operation = _first_rejecting_operation(fixture)
    error = _detect_fixture_error(fixture, operation)
    if fixture.get("kind") == "invalid":
        return validation_result([error]) if error else _fail(
            "invalid_export",
            {
                "field": fixture.get("expected_error_field", "fixture"),
                "reason": "Invalid fixture did not trigger a protocol rejection.",
            },
        )
    if error:
        return validation_result([error])
    takeover_lifecycle_error = _takeover_path_lifecycle_error(fixture)
    if takeover_lifecycle_error:
        return validation_result([takeover_lifecycle_error])
    operations = fixture.get("operations", [])
    for operation_item in operations if isinstance(operations, list) else []:
        if not isinstance(operation_item, dict):
            continue
        binding_shape_error = _operation_binding_error(operation_item)
        if binding_shape_error:
            return validation_result([binding_shape_error])
        header_result = validate_operation_headers(operation_item, {"skip_timestamp_skew": True})
        if not header_result.valid:
            return header_result
        body = _operation_body(fixture, operation_item)
        binding_error = _operation_body_binding_error(
            operation_item,
            body if isinstance(body, dict) else None,
        )
        if binding_error:
            return validation_result([binding_error])
        state_error = _operation_state_error(
            fixture.get("records", {}) if isinstance(fixture.get("records"), dict) else {},
            operation_item,
            body if isinstance(body, dict) else None,
        )
        if state_error:
            return validation_result([state_error])
        accepted_error = _accepted_operation_error(
            fixture.get("records", {}) if isinstance(fixture.get("records"), dict) else {},
            operation_item,
            body if isinstance(body, dict) else None,
        )
        if accepted_error:
            return validation_result([accepted_error])
        if operation_item.get("operation_id") == "exportEvidenceManifest":
            manifests = _all_records(fixture.get("records", {}), "evidence_manifests")
            manifest = manifests[0] if manifests else None
            manifest_result = validate_evidence_manifest(
                manifest,
                {"work_session": _evidence_manifest_source_work_session(fixture, manifest, operation_item)},
            )
            if not manifest_result.valid:
                return manifest_result
        object_type = OBJECT_BY_OPERATION.get(operation_item.get("operation_id"))
        if body and object_type:
            record_options = {}
            if operation_item.get("operation_id") == "submitOutcomeReport":
                record_options = {
                    "work_session": _outcome_report_source_work_session(
                        fixture.get("records", {}),
                        body if isinstance(body, dict) else None,
                    )
                }
            record_result = validate_protocol_record(object_type, body, record_options)
            if not record_result.valid:
                return record_result
    events = _all_records(fixture.get("records", {}), "jarvis_events")
    return validate_event_hash_chain(events) if events else _pass()


def _detect_fixture_error(
    fixture: Mapping[str, Any],
    operation: Mapping[str, Any] | None,
) -> dict[str, Any] | None:
    records = fixture.get("records", {}) if isinstance(fixture.get("records"), dict) else {}
    body = _operation_body(fixture, operation)
    if operation is not None:
        binding_shape_error = _operation_binding_error(operation)
        if binding_shape_error:
            return binding_shape_error
    header_result = validate_operation_headers(operation, {"skip_timestamp_skew": True})
    if not header_result.valid:
        return header_result.errors[0]
    headers = operation.get("headers", {}) if operation else {}
    binding_error = _operation_body_binding_error(operation, body if isinstance(body, dict) else None)
    if binding_error:
        return binding_error
    state_error = _operation_state_error(records, operation, body if isinstance(body, dict) else None)
    if state_error:
        return state_error
    body_time = _record_timestamp(body if isinstance(body, dict) else None)
    header_time = _timestamp(headers.get("Jarvis-Request-Timestamp")) if isinstance(headers, dict) else None
    if (
        fixture.get("expected_error_id") == "stale_request_timestamp"
        and body_time is not None
        and header_time is not None
        and (body_time - header_time).total_seconds() * 1000 >= 300_000
    ):
        return protocol_error(
            "stale_request_timestamp",
            {
                "field": "headers.Jarvis-Request-Timestamp",
                "reason": "Request timestamp is stale against the submitted protocol body.",
            },
        )

    work_session = _work_session_snapshot_for_operation(
        records,
        operation,
        body if isinstance(body, dict) else None,
    )

    if operation and operation.get("operation_id") == "createWorkSession" and isinstance(body, dict):
        if body.get("created_by_actor_id") != operation.get("actor_id"):
            return protocol_error(
                "unauthorized_actor",
                {
                    "field": "headers.Jarvis-Actor-Id",
                    "reason": "Actor cannot create a WorkSession for a different creator.",
                },
            )
        actor = _actor_by_id(records, operation.get("actor_id"))
        grants = _worker_grants(_worker_for_actor(records, actor))
        if "policy:own" not in grants:
            return protocol_error(
                "unauthorized_actor",
                {
                    "field": "headers.Jarvis-Actor-Id",
                    "reason": "Actor lacks authority to create a governed WorkSession.",
                },
            )

    if isinstance(body, dict) and body.get("policy_id") and body.get("policy_id") not in _ids_for(records, "policies"):
        return protocol_error(
            "missing_policy",
            {
                "field": "policy_id",
                "reason": "WorkSession references a Policy that is absent.",
            },
        )

    is_mutation_operation = _operation_method(operation) != "GET"
    if (
        is_mutation_operation
        and isinstance(work_session, dict)
        and work_session.get("status") in TERMINAL_WORK_SESSION_STATES
    ):
        return protocol_error(
            "sealed_work_session_mutation",
            {
                "field": "records.work_sessions.completed.status",
                "reason": "Sealed WorkSession records cannot be mutated.",
            },
        )

    active_takeover = next(
        (
            takeover
            for takeover in _all_records(records, "takeovers")
            if takeover.get("work_session_id") == _target_work_session_id(operation, body if isinstance(body, dict) else None)
            and takeover.get("state") == "human_active"
        ),
        None,
    )
    if (
        active_takeover
        and _actor_by_id(records, operation.get("actor_id") if operation else None) is not None
        and _actor_by_id(records, operation.get("actor_id") if operation else None).get("type") == "agent"
        and _is_int(operation.get("attempted_takeover_lock_epoch") if operation else None)
        and operation.get("attempted_takeover_lock_epoch") < active_takeover.get("lock_epoch")
    ):
        return protocol_error(
            "stale_takeover_epoch",
            {
                "field": "records.takeovers.active.lock_epoch",
                "reason": "AgentWorker continuation uses a stale takeover lock epoch.",
            },
        )

    if operation and operation.get("operation_id") == "appendJarvisEvent" and isinstance(body, dict):
        accepted_error = _accepted_operation_error(records, operation, body)
        if accepted_error:
            return accepted_error

    if operation and operation.get("operation_id") == "createRequest":
        request_result = validate_request(body)
        if not request_result.valid:
            return request_result.errors[0]

    if operation and operation.get("operation_id") == "recordReview" and isinstance(body, dict):
        request_id = _request_id_from_target_ref(body.get("target_ref"))
        review_result = validate_review(body, {"request": _record_by_id(records, "requests", request_id)})
        if not review_result.valid:
            return review_result.errors[0]

    if (
        operation
        and operation.get("operation_id") == "appendJarvisEvent"
        and isinstance(body, dict)
        and body.get("type") == "work_session.completed"
    ):
        pending = next(
            (
                request
                for request in _all_records(records, "requests")
                if request.get("work_session_id") == body.get("work_session_id")
                and request.get("status") == "pending"
            ),
            None,
        )
        if pending:
            return protocol_error(
                "request_unresolved",
                {
                    "field": "records.requests.pending.status",
                    "reason": "WorkSession cannot complete while a Request remains pending.",
                },
            )

    if operation and operation.get("operation_id") == "exportEvidenceManifest":
        manifests = _all_records(records, "evidence_manifests")
        manifest = manifests[0] if manifests else None
        export_error = _evidence_manifest_export_error(
            manifest,
            _evidence_manifest_source_work_session(fixture, manifest, operation) or work_session,
        )
        if export_error:
            return export_error

    if isinstance(body, dict) and body.get("type") == "evidence_manifest.mutated":
        return protocol_error(
            "sealed_evidence_mutation",
            {
                "field": "records.evidence_manifests.sealed",
                "reason": "Sealed EvidenceManifest records cannot be mutated.",
            },
        )

    if operation and operation.get("operation_id") == "createMemoryProposal":
        memory_result = validate_memory_proposal(body)
        if not memory_result.valid:
            return memory_result.errors[0]

    if operation and operation.get("operation_id") == "createSkillProposal":
        skill_result = validate_skill_proposal(body)
        if not skill_result.valid:
            return skill_result.errors[0]

    if operation and operation.get("operation_id") == "submitOutcomeReport":
        outcome_result = validate_outcome_report(
            body,
            {"work_session": _outcome_report_source_work_session(records, body if isinstance(body, dict) else None)},
        )
        if not outcome_result.valid:
            return outcome_result.errors[0]

    forbidden_field = find_forbidden_host_private_field(body)
    if forbidden_field:
        return protocol_error(
            "forbidden_host_private_field",
            {
                "field": forbidden_field,
                "reason": "Protocol records MUST NOT expose host-private fields.",
            },
        )
    return None


__all__ = list(OPENAPI_TYPE_NAMES)
__all__ += [
    "FORBIDDEN_EXPORT_KEY_TOKENS",
    "NON_WORKSESSION_MUTATION_HEADERS",
    "MUTATION_ONLY_HEADERS",
    "OPENAPI_SCHEMA_NAMES",
    "PROTOCOL_VERSION",
    "READ_HEADERS",
    "REVIEW_RESOLVED_REQUEST_STATUSES",
    "SCHEMA_ALLOWED_FIELDS",
    "SCHEMA_CLOSED_SCHEMAS",
    "SCHEMA_ENUMS",
    "SCHEMA_FIELD_CONSTS",
    "SCHEMA_FIELD_ENUMS",
    "SCHEMA_FORBIDDEN_FIELDS",
    "SCHEMA_REQUIRED_FIELDS",
    "TERMINAL_WORK_SESSION_STATES",
    "WORKSESSION_MUTATION_HEADERS",
    "JarvisProtocolValidationError",
    "ValidationResult",
    "canonicalize_protocol_value",
    "find_forbidden_host_private_field",
    "hash_protocol_value",
    "protocol_error",
    "validate_approval_scope",
    "validate_contribution",
    "validate_event_hash_chain",
    "validate_evidence_manifest",
    "validate_fixture",
    "validate_headers",
    "validate_learning_record",
    "validate_memory_proposal",
    "validate_mutation_headers",
    "validate_operation_headers",
    "validate_outcome_report",
    "validate_protocol_record",
    "validate_read_headers",
    "validate_request",
    "validate_review",
    "validate_schema_record",
    "validate_skill_proposal",
    "validate_takeover",
    "validation_result",
]
