#!/usr/bin/env python3
"""Validate the Jarvis existing-agent implementation proof."""

from __future__ import annotations

from pathlib import Path
from datetime import datetime
import json
import re
import sys
from typing import Any

import yaml

from generate_implementation_proof import LANGGRAPH_TRACE_PATH, PROOF_PATH, ROOT, build_proof


PYTHON_PACKAGE_SRC = ROOT / "packages" / "python" / "src"
PROTOCOL_VERSION = "v0.1"
REQUIRED_HELPERS = {
    "create_operation_envelope",
    "create_work_session_mutation_headers",
    "create_non_work_session_mutation_headers",
    "create_read_headers",
    "create_next_jarvis_event",
    "create_evidence_manifest",
    "validate_protocol_record",
    "validate_operation_headers",
    "validate_event_hash_chain",
    "validate_evidence_manifest",
    "validate_fixture",
}
TOP_LEVEL_KEYS = {
    "proof_id",
    "fixture_id",
    "protocol_version",
    "kind",
    "expected_result",
    "title",
    "description",
    "issue_ref",
    "host_shape_ref",
    "native_agent_boundary",
    "sdk_helper_trace",
    "source_contract_refs",
    "records",
    "operations",
    "assertions",
    "pack_limits",
}
REQUIRED_RECORD_GROUPS = {
    "workers",
    "actors",
    "human_workers",
    "agent_workers",
    "policies",
    "work_sessions",
    "jarvis_events",
    "policy_decisions",
    "requests",
    "reviews",
    "contributions",
    "evidence_manifests",
    "learning_records",
    "memory_proposals",
    "skill_proposals",
    "outcome_reports",
}
OBJECT_TYPES_BY_GROUP = {
    "workers": "Worker",
    "actors": "Actor",
    "human_workers": "HumanWorker",
    "agent_workers": "AgentWorker",
    "policies": "Policy",
    "work_sessions": "WorkSession",
    "jarvis_events": "JarvisEvent",
    "policy_decisions": "PolicyDecision",
    "requests": "Request",
    "reviews": "Review",
    "contributions": "Contribution",
    "learning_records": "LearningRecord",
    "memory_proposals": "MemoryProposal",
    "skill_proposals": "SkillProposal",
    "outcome_reports": "OutcomeReport",
}
FORBIDDEN_LIMIT_FLAGS = {
    "certifies_implementation",
    "claims_production_adoption",
    "defines_host_execution",
    "defines_runtime_behavior",
    "defines_agent_runtime",
    "defines_host_ui",
    "defines_storage",
    "defines_auth",
    "defines_model_calls",
    "defines_tool_execution",
    "defines_billing",
    "defines_scoring",
    "defines_payment",
    "defines_deployment",
    "defines_monitoring",
    "defines_host_integration",
    "defines_host_workflow",
    "defines_adapter_code",
    "defines_wrapper_code",
}
REQUIRED_OPERATION_SPINE = [
    ("registerWorker", "records.workers.human", None, "actor-proof-registrar"),
    ("registerWorker", "records.workers.agent", None, "actor-proof-registrar"),
    ("registerActor", "records.actors.human", None, "actor-proof-registrar"),
    ("registerActor", "records.actors.agent", None, "actor-proof-registrar"),
    ("createWorkSession", "records.work_sessions.genesis_request", "ws-native-coding-agent-proof", "actor-human-proof"),
    ("recordPolicyDecision", "records.policy_decisions.external_source_denied", "ws-native-coding-agent-proof", "actor-agent-proof"),
    ("createRequest", "records.requests.pending", "ws-native-coding-agent-proof", "actor-agent-proof"),
    ("recordReview", "records.reviews.approve_source", "ws-native-coding-agent-proof", "actor-human-proof"),
    ("recordPolicyDecision", "records.policy_decisions.external_source_allowed", "ws-native-coding-agent-proof", "actor-agent-proof"),
    ("appendJarvisEvent", "records.jarvis_events.evidence_captured", "ws-native-coding-agent-proof", "actor-agent-proof"),
    ("appendJarvisEvent", "records.jarvis_events.framework_trace_captured", "ws-native-coding-agent-proof", "actor-agent-proof"),
    ("recordContribution", "records.contributions.shared_answer", "ws-native-coding-agent-proof", "actor-human-proof"),
    ("createLearningRecord", "records.learning_records.pair", "ws-native-coding-agent-proof", "actor-human-proof"),
    ("createMemoryProposal", "records.memory_proposals.source_policy_pattern", "ws-native-coding-agent-proof", "actor-human-proof"),
    ("createSkillProposal", "records.skill_proposals.bounded_source_collection", "ws-native-coding-agent-proof", "actor-human-proof"),
    ("appendJarvisEvent", "records.jarvis_events.worksession_completed", "ws-native-coding-agent-proof", "actor-human-proof"),
    ("exportEvidenceManifest", None, "ws-native-coding-agent-proof", "actor-human-proof"),
    ("submitOutcomeReport", "records.outcome_reports.post_session", None, "actor-human-proof"),
]
EVENT_HASH_EXCLUDED_FIELDS = {"event_hash", "actor_signature", "signing_key_ref"}

sys.path.insert(0, str(PYTHON_PACKAGE_SRC))

import jarvis_protocol  # noqa: E402


OPENAPI_SCHEMAS = yaml.safe_load(
    (ROOT / "docs" / "openapi" / "jarvis-openapi.yaml").read_text(encoding="utf-8")
)["components"]["schemas"]


class ImplementationProofError(Exception):
    """Raised when the implementation proof violates the protocol contract."""


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ImplementationProofError(f"{rel(path)}: invalid JSON: {exc}") from exc


def load_structured_ref(path: Path) -> Any:
    if path.suffix in {".yaml", ".yml"}:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    if path.suffix == ".json":
        return load_json(path)
    return path.read_text(encoding="utf-8")


def resolve_json_pointer(path: Path, document: Any, pointer: str) -> None:
    if not pointer.startswith("/"):
        raise ImplementationProofError(f"{rel(path)}: JSON pointer fragment MUST start with /")
    current = document
    for raw_part in pointer.strip("/").split("/"):
        part = raw_part.replace("~1", "/").replace("~0", "~")
        if isinstance(current, dict) and part in current:
            current = current[part]
            continue
        if isinstance(current, list) and part.isdigit() and int(part) < len(current):
            current = current[int(part)]
            continue
        raise ImplementationProofError(f"{rel(path)}: JSON pointer does not resolve: #{pointer}")


def resolve_repo_ref(value: Any) -> None:
    if not isinstance(value, str) or not value:
        raise ImplementationProofError("source_contract_refs entries MUST be nonempty strings")
    local_ref, _, fragment = value.partition("#")
    target = (ROOT / local_ref).resolve()
    if not target.is_relative_to(ROOT) or not target.exists():
        raise ImplementationProofError(f"source_contract_refs entry does not resolve: {value}")
    if fragment:
        resolve_json_pointer(target, load_structured_ref(target), fragment)


def schema_ref_name(ref: str) -> str:
    prefix = "#/components/schemas/"
    if not ref.startswith(prefix):
        raise ImplementationProofError(f"unsupported OpenAPI ref: {ref}")
    return ref.removeprefix(prefix)


def json_type_name(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return type(value).__name__


def type_matches(expected: Any, value: Any) -> bool:
    expected_types = expected if isinstance(expected, list) else [expected]
    for expected_type in expected_types:
        if expected_type == "object" and isinstance(value, dict):
            return True
        if expected_type == "array" and isinstance(value, list):
            return True
        if expected_type == "string" and isinstance(value, str):
            return True
        if expected_type == "integer" and isinstance(value, int) and not isinstance(value, bool):
            return True
        if expected_type == "number" and isinstance(value, (int, float)) and not isinstance(value, bool):
            return True
        if expected_type == "boolean" and isinstance(value, bool):
            return True
        if expected_type == "null" and value is None:
            return True
    return False


def schema_errors(schema: dict[str, Any], value: Any, field: str) -> list[str]:
    if "$ref" in schema:
        return schema_errors(OPENAPI_SCHEMAS[schema_ref_name(schema["$ref"])], value, field)
    errors: list[str] = []
    for subschema in schema.get("allOf", []):
        errors.extend(schema_errors(subschema, value, field))
    any_of = schema.get("anyOf")
    if isinstance(any_of, list) and any_of:
        if not any(not schema_errors(subschema, value, field) for subschema in any_of):
            errors.append(f"{field} MUST match at least one allowed schema")
    not_schema = schema.get("not")
    if isinstance(not_schema, dict) and not schema_errors(not_schema, value, field):
        errors.append(f"{field} MUST NOT match forbidden schema")
    if "const" in schema and value != schema["const"]:
        errors.append(f"{field} MUST equal {schema['const']!r}")
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{field} MUST match the OpenAPI enum")
    if "type" in schema and not type_matches(schema["type"], value):
        errors.append(f"{field} MUST be {schema['type']}, got {json_type_name(value)}")
        return errors
    if isinstance(value, str):
        if "minLength" in schema and len(value) < schema["minLength"]:
            errors.append(f"{field} MUST NOT be empty")
        if "pattern" in schema and re.search(schema["pattern"], value) is None:
            errors.append(f"{field} MUST match OpenAPI pattern")
        if schema.get("format") == "date-time":
            try:
                datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                errors.append(f"{field} MUST be a valid date-time")
    if isinstance(value, list):
        if "minItems" in schema and len(value) < schema["minItems"]:
            errors.append(f"{field} MUST contain at least {schema['minItems']} item(s)")
        if schema.get("uniqueItems"):
            seen = set()
            for item in value:
                encoded = json.dumps(item, sort_keys=True, separators=(",", ":"))
                if encoded in seen:
                    errors.append(f"{field} items MUST be unique")
                    break
                seen.add(encoded)
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, item in enumerate(value):
                errors.extend(schema_errors(item_schema, item, f"{field}[{index}]"))
    if isinstance(value, dict):
        properties = schema.get("properties", {})
        required = schema.get("required", [])
        for required_field in required:
            if required_field not in value or value[required_field] is None:
                errors.append(f"{field}.{required_field} is required")
        additional = schema.get("additionalProperties", True)
        for key, child in value.items():
            if key in properties:
                errors.extend(schema_errors(properties[key], child, f"{field}.{key}"))
            elif additional is False:
                errors.append(f"{field}.{key} is not defined by the OpenAPI schema")
            elif isinstance(additional, dict):
                errors.extend(schema_errors(additional, child, f"{field}.{key}"))
    return errors


def validate_openapi_schema(schema_name: str, value: Any, field: str) -> None:
    errors = schema_errors(OPENAPI_SCHEMAS[schema_name], value, field)
    if errors:
        raise ImplementationProofError(errors[0])


def all_records(records: dict[str, Any], group: str) -> list[dict[str, Any]]:
    values = records.get(group)
    if not isinstance(values, dict):
        raise ImplementationProofError(f"records.{group} MUST be an object")
    return [value for value in values.values() if isinstance(value, dict)]


def record_by_id(records: dict[str, Any], group: str, record_id: Any) -> dict[str, Any] | None:
    for record in all_records(records, group):
        if record.get("id") == record_id:
            return record
    return None


def assert_result(label: str, result: Any) -> None:
    if result.valid:
        return
    first = result.errors[0] if result.errors else {}
    raise ImplementationProofError(
        f"{label}: {first.get('error_id', 'unknown_error')} {first.get('field', '')}"
    )


def operation_body(proof: dict[str, Any], operation: dict[str, Any]) -> Any:
    body_ref = operation.get("body_ref")
    if not isinstance(body_ref, str):
        return None
    current: Any = proof
    for part in body_ref.split("."):
        if not isinstance(current, dict) or part not in current:
            raise ImplementationProofError(f"operation body_ref does not resolve: {body_ref}")
        current = current[part]
    return current


def event_by_id(proof: dict[str, Any], event_id: str) -> dict[str, Any]:
    for event in all_records(proof["records"], "jarvis_events"):
        if event.get("id") == event_id:
            return event
    raise ImplementationProofError(f"JarvisEvent {event_id} is missing")


def terminal_work_session(proof: dict[str, Any]) -> dict[str, Any]:
    sessions = all_records(proof["records"], "work_sessions")
    for session in sessions:
        if session.get("status") == "completed":
            return session
    raise ImplementationProofError("proof MUST include a terminal WorkSession")


def validate_operation_spine(proof: dict[str, Any]) -> None:
    operations = proof.get("operations")
    if not isinstance(operations, list) or len(operations) != len(REQUIRED_OPERATION_SPINE):
        raise ImplementationProofError("operations MUST contain the complete required proof spine")
    for index, (operation_id, body_ref, work_session_id, actor_id) in enumerate(REQUIRED_OPERATION_SPINE):
        operation = operations[index]
        if not isinstance(operation, dict):
            raise ImplementationProofError(f"operations[{index}] MUST be an object")
        expected = {
            "operation_id": operation_id,
            "body_ref": body_ref,
            "work_session_id": work_session_id,
            "actor_id": actor_id,
        }
        for field, expected_value in expected.items():
            if expected_value is None:
                if field in operation:
                    raise ImplementationProofError(f"operations[{index}].{field} MUST be absent")
            elif operation.get(field) != expected_value:
                raise ImplementationProofError(
                    f"operations[{index}].{field} MUST be {expected_value}"
                )
    event_sequence_by_body_ref = {
        "records.jarvis_events.evidence_captured": "event-evidence-captured",
        "records.jarvis_events.framework_trace_captured": "event-framework-trace-captured",
        "records.jarvis_events.worksession_completed": "event-worksession-completed",
    }
    for operation in operations:
        event_id = event_sequence_by_body_ref.get(operation.get("body_ref"))
        if event_id and operation_body(proof, operation).get("id") != event_id:
            raise ImplementationProofError(f"{operation.get('body_ref')} MUST bind the expected JarvisEvent")


def validate_event_hashes(proof: dict[str, Any]) -> None:
    for event in all_records(proof["records"], "jarvis_events"):
        hash_input = {
            key: value
            for key, value in event.items()
            if key not in EVENT_HASH_EXCLUDED_FIELDS
        }
        expected_hash = jarvis_protocol.hash_protocol_value(hash_input)
        if event.get("event_hash") != expected_hash:
            raise ImplementationProofError(f"JarvisEvent {event.get('id')} event_hash MUST match canonical event body hash")


def validate_request_resolution(proof: dict[str, Any]) -> None:
    records = proof["records"]
    request = next(
        (
            item
            for item in all_records(records, "requests")
            if item.get("id") == "req-native-agent-source" and item.get("status") == "approved"
        ),
        None,
    )
    review = record_by_id(records, "reviews", "review-native-agent-source-approval")
    if not request or request.get("status") != "approved":
        raise ImplementationProofError("proof MUST include the final approved Request snapshot")
    if not review or review.get("target_ref") != f"request:{request['id']}":
        raise ImplementationProofError("Review MUST target the resolved Request")
    if request.get("resolved_by_review_id") != review.get("id"):
        raise ImplementationProofError("Request MUST resolve through the HumanWorker Review")
    approval_scope = review.get("approval_scope")
    if not isinstance(approval_scope, dict) or approval_scope.get("request_id") != request.get("id"):
        raise ImplementationProofError("ApprovalScope MUST bind to the resolved Request")
    if approval_scope.get("request_event_hash") != event_by_id(proof, "event-request-created").get("event_hash"):
        raise ImplementationProofError("ApprovalScope MUST bind to the Request JarvisEvent hash")


def validate_terminal_exports(proof: dict[str, Any]) -> None:
    terminal = terminal_work_session(proof)
    operations = proof["operations"]
    completed_index = next(
        index
        for index, operation in enumerate(operations)
        if operation.get("body_ref") == "records.jarvis_events.worksession_completed"
    )
    export_index = next(
        index
        for index, operation in enumerate(operations)
        if operation.get("operation_id") == "exportEvidenceManifest"
    )
    outcome_index = next(
        index
        for index, operation in enumerate(operations)
        if operation.get("operation_id") == "submitOutcomeReport"
    )
    if not completed_index < export_index < outcome_index:
        raise ImplementationProofError("EvidenceManifest export and OutcomeReport MUST occur after WorkSession completion")
    export_operation = operations[export_index]
    if export_operation.get("work_session_id") != terminal.get("id"):
        raise ImplementationProofError("EvidenceManifest export operation MUST target the terminal WorkSession")
    manifest = proof["records"]["evidence_manifests"]["portable_export"]
    outcome = proof["records"]["outcome_reports"]["post_session"]
    if manifest.get("work_session_id") != terminal.get("id"):
        raise ImplementationProofError("EvidenceManifest MUST reference the terminal WorkSession")
    if outcome.get("work_session_id") != terminal.get("id"):
        raise ImplementationProofError("OutcomeReport MUST reference the terminal WorkSession")


def validate_actor_authority(proof: dict[str, Any]) -> None:
    records = proof["records"]
    create_operation = proof["operations"][4]
    creator_actor = record_by_id(records, "actors", create_operation.get("actor_id"))
    if not creator_actor:
        raise ImplementationProofError("createWorkSession Actor MUST be represented")
    creator_worker = record_by_id(records, "workers", creator_actor.get("worker_id"))
    grants = creator_worker.get("authority_scope", {}).get("grants", []) if creator_worker else []
    if "policy:own" not in grants:
        raise ImplementationProofError("createWorkSession Actor MUST belong to a worker with policy:own authority")
    for event in all_records(records, "jarvis_events"):
        actor = record_by_id(records, "actors", event.get("actor_id"))
        allowed = actor.get("event_authority", {}).get("allowed_event_types", []) if actor else []
        if event.get("type") not in allowed:
            raise ImplementationProofError(f"Actor {event.get('actor_id')} lacks authority for {event.get('type')}")


def validate_native_framework_trace(proof: dict[str, Any]) -> None:
    if not LANGGRAPH_TRACE_PATH.exists():
        raise ImplementationProofError(f"{rel(LANGGRAPH_TRACE_PATH)} is missing")
    trace = load_json(LANGGRAPH_TRACE_PATH)
    if not isinstance(trace, dict):
        raise ImplementationProofError(f"{rel(LANGGRAPH_TRACE_PATH)} MUST be an object")
    native_boundary = proof.get("native_agent_boundary")
    if not isinstance(native_boundary, dict):
        raise ImplementationProofError("native_agent_boundary MUST be an object")
    if native_boundary.get("framework_trace_ref") != rel(LANGGRAPH_TRACE_PATH):
        raise ImplementationProofError("native_agent_boundary.framework_trace_ref MUST point to the native framework trace")
    expected_hash = jarvis_protocol.hash_protocol_value(trace)
    if native_boundary.get("framework_trace_hash") != expected_hash:
        raise ImplementationProofError("native_agent_boundary.framework_trace_hash MUST match the native framework trace")
    framework = trace.get("framework")
    if not isinstance(framework, dict):
        raise ImplementationProofError("native framework trace MUST identify the framework")
    for field in ("name", "package", "package_version", "api"):
        if not isinstance(framework.get(field), str) or not framework[field]:
            raise ImplementationProofError(f"native framework trace framework.{field} MUST be present")
    mapping = trace.get("jarvis_mapping")
    if not isinstance(mapping, dict):
        raise ImplementationProofError("native framework trace MUST map native execution to Jarvis records")
    expected_mapping = {
        "work_session_id": terminal_work_session(proof).get("id"),
        "policy_decision_id": "pd-native-agent-source-denied",
        "request_id": "req-native-agent-source",
        "review_id": "review-native-agent-source-approval",
        "contribution_id": "contribution-native-agent-shared-answer",
        "evidence_manifest_id": "evidence-manifest-native-agent-proof",
        "learning_record_id": "learning-native-agent-pair",
        "memory_proposal_id": "memory-proposal-native-agent",
        "skill_proposal_id": "skill-proposal-native-agent",
        "outcome_report_id": "outcome-report-native-agent",
    }
    for key, expected_value in expected_mapping.items():
        if mapping.get(key) != expected_value:
            raise ImplementationProofError(f"native framework trace {key} MUST match Jarvis proof records")
    manifest = proof["records"]["evidence_manifests"]["portable_export"]
    evidence_items = manifest.get("evidence_item_refs", [])
    trace_evidence = next(
        (
            item
            for item in evidence_items
            if isinstance(item, dict) and item.get("id") == "evidence-langgraph-stategraph-trace"
        ),
        None,
    )
    if not trace_evidence:
        raise ImplementationProofError("EvidenceManifest MUST include native framework trace evidence")
    if trace_evidence.get("content_hash") != expected_hash:
        raise ImplementationProofError("native framework trace evidence content_hash MUST match trace hash")
    source_event_refs = trace_evidence.get("source_event_refs")
    if source_event_refs != ["event-framework-trace-captured"]:
        raise ImplementationProofError("native framework trace evidence MUST reference the trace-capture event")
    trace_event = event_by_id(proof, "event-framework-trace-captured")
    if trace_event.get("payload", {}).get("object_id") != trace_evidence.get("id"):
        raise ImplementationProofError("trace-capture JarvisEvent MUST identify the trace evidence item")
    boundary = trace.get("boundary")
    if not isinstance(boundary, dict) or boundary.get("jarvis_scope") != "protocol_records_only":
        raise ImplementationProofError("native framework trace boundary MUST keep Jarvis limited to protocol records")
    if boundary.get("native_execution_preserved") is not True:
        raise ImplementationProofError("native framework trace boundary MUST preserve native execution")
    if boundary.get("adapter_or_wrapper_added") is not False:
        raise ImplementationProofError("native framework trace MUST NOT add adapter or wrapper behavior")


def validate_proof(proof: dict[str, Any]) -> int:
    if set(proof) != TOP_LEVEL_KEYS:
        extra = sorted(set(proof) - TOP_LEVEL_KEYS)
        missing = sorted(TOP_LEVEL_KEYS - set(proof))
        raise ImplementationProofError(f"top-level proof keys mismatch; extra={extra}; missing={missing}")
    if proof.get("protocol_version") != PROTOCOL_VERSION:
        raise ImplementationProofError(f"protocol_version MUST be {PROTOCOL_VERSION}")
    if proof.get("kind") != "valid" or proof.get("expected_result") != "accept":
        raise ImplementationProofError("implementation proof MUST be a valid accepted proof")
    records = proof.get("records")
    if not isinstance(records, dict) or set(records) != REQUIRED_RECORD_GROUPS:
        raise ImplementationProofError("records MUST contain the full Jarvis proof object spine")
    trace = proof.get("sdk_helper_trace")
    if not isinstance(trace, list) or not REQUIRED_HELPERS <= set(trace):
        raise ImplementationProofError("sdk_helper_trace MUST name every required SDK helper")
    limits = proof.get("pack_limits")
    if not isinstance(limits, dict) or any(limits.get(flag) is not False for flag in FORBIDDEN_LIMIT_FLAGS):
        raise ImplementationProofError(
            "pack_limits MUST reject certification, adoption, host, runtime, UI, storage, auth, model, tool, billing, scoring, payment, deployment, monitoring, integration, workflow, adapter, and wrapper claims"
        )
    native_boundary = proof.get("native_agent_boundary")
    if not isinstance(native_boundary, dict) or native_boundary.get("jarvis_scope") != "protocol_records_only":
        raise ImplementationProofError("native_agent_boundary MUST keep Jarvis limited to protocol records")
    if native_boundary.get("native_execution_preserved") is not True:
        raise ImplementationProofError("native_agent_boundary MUST preserve native execution")
    source_refs = proof.get("source_contract_refs")
    if not isinstance(source_refs, list) or not source_refs:
        raise ImplementationProofError("source_contract_refs MUST be nonempty")
    for ref in source_refs:
        resolve_repo_ref(ref)

    checked = 0
    validate_operation_spine(proof)
    checked += 1
    for group, object_type in OBJECT_TYPES_BY_GROUP.items():
        for record in all_records(records, group):
            validate_openapi_schema(object_type, record, f"records.{group}.{record.get('id', 'record')}")
            options = {}
            if object_type == "OutcomeReport":
                options = {"work_session": terminal_work_session(proof)}
            assert_result(
                f"records.{group}.{record.get('id', 'record')}",
                jarvis_protocol.validate_protocol_record(object_type, record, options),
            )
            checked += 1

    events = all_records(records, "jarvis_events")
    validate_event_hashes(proof)
    checked += 1
    assert_result("event hash chain", jarvis_protocol.validate_event_hash_chain(events))
    checked += 1
    validate_request_resolution(proof)
    checked += 1
    validate_terminal_exports(proof)
    checked += 1
    validate_actor_authority(proof)
    checked += 1
    validate_native_framework_trace(proof)
    checked += 1

    evidence_manifest = records["evidence_manifests"]["portable_export"]
    assert_result(
        "EvidenceManifest export",
        jarvis_protocol.validate_evidence_manifest(
            evidence_manifest,
            {"work_session": terminal_work_session(proof)},
        ),
    )
    checked += 1

    operations = proof.get("operations")
    if not isinstance(operations, list) or not operations:
        raise ImplementationProofError("operations MUST be a nonempty list")
    for operation in operations:
        if not isinstance(operation, dict):
            raise ImplementationProofError("operation entries MUST be objects")
        assert_result(
            f"operation.{operation.get('operation_id', 'unknown')}",
            jarvis_protocol.validate_operation_headers(
                operation,
                {"skip_timestamp_skew": True},
            ),
        )
        body = operation_body(proof, operation)
        object_type = jarvis_protocol.OBJECT_BY_OPERATION.get(operation.get("operation_id"))
        if body is not None and object_type:
            options = {}
            if object_type == "OutcomeReport":
                options = {"work_session": terminal_work_session(proof)}
            assert_result(
                f"operation body.{operation.get('operation_id')}",
                jarvis_protocol.validate_protocol_record(object_type, body, options),
            )
        checked += 1

    assert_result("SDK fixture validator", jarvis_protocol.validate_fixture(proof))
    checked += 1
    return checked


def main() -> int:
    if not PROOF_PATH.exists():
        print(f"{rel(PROOF_PATH)} is missing")
        return 1
    expected = build_proof()
    actual = load_json(PROOF_PATH)
    if actual != expected:
        print(f"{rel(PROOF_PATH)} is stale; run python3 scripts/generate_implementation_proof.py")
        return 1
    try:
        checked = validate_proof(actual)
    except ImplementationProofError as exc:
        print(exc)
        return 1
    print(f"implementation proof ok ({checked} checks)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
