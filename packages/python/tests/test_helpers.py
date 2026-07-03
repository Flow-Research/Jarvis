from __future__ import annotations

from datetime import datetime, timezone
import unittest

from jarvis_protocol import (
    canonicalize_protocol_value,
    create_evidence_manifest,
    create_jarvis_event,
    create_next_jarvis_event,
    create_operation_envelope,
    create_operation_path,
    create_read_headers,
    create_work_session_mutation_headers,
    find_forbidden_host_private_field,
    get_operation_binding,
    hash_protocol_value,
    JarvisProtocolValidationError,
    protocol_error,
    validate_approval_scope,
    validate_evidence_manifest,
    validate_event_hash_chain,
    validate_mutation_headers,
    validate_operation_headers,
    validate_outcome_report,
    validate_protocol_record,
    validate_read_headers,
)

AUTHORIZATION = "HostAuth test"


class HelperValidationTests(unittest.TestCase):
    def test_mutation_headers_enforce_work_session_zero_trust_headers(self) -> None:
        missing = validate_mutation_headers(
            {
                "Authorization": "HostAuth test",
                "Jarvis-Protocol-Version": "v0.1",
                "Jarvis-Actor-Id": "actor-test",
                "Jarvis-Idempotency-Key": "idem-test",
                "Jarvis-Request-Timestamp": "2026-06-16T10:00:00Z",
            }
        )
        self.assertFalse(missing.valid)
        self.assertEqual(missing.errors[0]["error_id"], "missing_expected_work_session_revision")

        accepted = validate_mutation_headers(
            {
                "Authorization": "HostAuth test",
                "Jarvis-Protocol-Version": "v0.1",
                "Jarvis-Actor-Id": "actor-test",
                "Jarvis-Idempotency-Key": "idem-test",
                "Jarvis-Request-Timestamp": "2026-06-16T10:00:00Z",
                "Jarvis-Expected-WorkSession-Revision": 0,
                "Jarvis-Previous-Event-Hash": "hash:protocol-genesis",
            },
            {"now": datetime(2026, 6, 16, 10, 0, 0, tzinfo=timezone.utc)},
        )
        self.assertTrue(accepted.valid, accepted.errors)

    def test_header_helpers_create_valid_read_and_work_session_mutation_headers(self) -> None:
        read_headers = create_read_headers(
            actor_id="actor-human-test",
            authorization=AUTHORIZATION,
        )
        self.assertEqual(
            read_headers,
            {
                "Authorization": AUTHORIZATION,
                "Jarvis-Protocol-Version": "v0.1",
                "Jarvis-Actor-Id": "actor-human-test",
            },
        )
        self.assertTrue(validate_read_headers(read_headers).valid)

        mutation_headers = create_work_session_mutation_headers(
            actor_id="actor-human-test",
            authorization=AUTHORIZATION,
            idempotency_key="idem-test",
            request_timestamp="2026-06-16T10:00:00Z",
            expected_work_session_revision=0,
            previous_event_hash="hash:protocol-genesis",
        )
        self.assertTrue(validate_mutation_headers(mutation_headers).valid)

    def test_operation_helper_binds_openapi_method_path_status_headers_and_actor(self) -> None:
        self.assertEqual(
            get_operation_binding("exportEvidenceManifest"),
            {
                "method": "GET",
                "path": "/work-sessions/{work_session_id}/export",
                "statuses": [200, 400],
            },
        )
        self.assertEqual(
            create_operation_path("exportEvidenceManifest", {"work_session_id": "ws-test"}),
            "/work-sessions/ws-test/export",
        )
        operation = create_operation_envelope(
            operation_id="exportEvidenceManifest",
            actor_id="actor-human-test",
            authorization=AUTHORIZATION,
            work_session_id="ws-test",
        )
        self.assertEqual(
            operation,
            {
                "operation_id": "exportEvidenceManifest",
                "method": "GET",
                "path": "/work-sessions/ws-test/export",
                "headers": {
                    "Authorization": AUTHORIZATION,
                    "Jarvis-Protocol-Version": "v0.1",
                    "Jarvis-Actor-Id": "actor-human-test",
                },
                "actor_id": "actor-human-test",
                "expected_status": 200,
                "work_session_id": "ws-test",
            },
        )
        self.assertTrue(validate_operation_headers(operation).valid)

    def test_event_and_evidence_manifest_helpers_build_valid_protocol_records(self) -> None:
        created = create_next_jarvis_event(
            id="event-created",
            event_type="work_session.created",
            work_session_id="ws-test",
            actor_id="actor-human-test",
            timestamp="2026-06-16T10:00:00Z",
            payload={
                "object_type": "work_session",
                "object_id": "ws-test",
                "action": "created",
            },
        )
        completed = create_next_jarvis_event(
            events=[created],
            id="event-completed",
            event_type="work_session.completed",
            work_session_id="ws-test",
            actor_id="actor-human-test",
            timestamp="2026-06-16T10:10:00Z",
            payload={
                "object_type": "work_session",
                "object_id": "ws-test",
                "action": "completed",
            },
        )
        self.assertEqual(created["sequence"], 1)
        self.assertEqual(completed["sequence"], 2)
        self.assertEqual(completed["previous_hash"], created["event_hash"])
        self.assertTrue(validate_event_hash_chain([created, completed]).valid)

        work_session = {
            "id": "ws-test",
            "objective": "Prove helper-created protocol records.",
            "status": "completed",
            "last_event_hash": completed["event_hash"],
        }
        manifest = create_evidence_manifest(
            id="evidence-test",
            work_session=work_session,
            events=[created, completed],
            generated_by_actor_id="actor-human-test",
            generated_at="2026-06-16T10:11:00Z",
            evidence_item_refs=[
                {
                    "id": "evidence-item-test",
                    "work_session_id": "ws-test",
                    "source_event_refs": ["event-completed"],
                    "captured_by_actor_id": "actor-human-test",
                    "evidence_type": "artifact",
                    "artifact_ref": "artifact:test",
                    "content_hash": "hash:content",
                    "trust_label": "verified",
                    "redaction_state": "none",
                    "captured_at": "2026-06-16T10:10:00Z",
                    "limitation_refs": [],
                }
            ],
        )
        self.assertEqual(manifest["event_chain_root"], completed["event_hash"])
        self.assertTrue(validate_evidence_manifest(manifest, {"work_session": work_session}).valid)

    def test_event_helper_computes_hash_before_optional_signature_metadata(self) -> None:
        base = {
            "id": "event-signed",
            "sequence": 1,
            "event_type": "work_session.created",
            "work_session_id": "ws-test",
            "actor_id": "actor-human-test",
            "timestamp": "2026-06-16T10:00:00Z",
            "payload": {
                "object_type": "work_session",
                "object_id": "ws-test",
                "action": "created",
            },
        }
        unsigned = create_jarvis_event(**base)
        signed = create_jarvis_event(
            **base,
            actor_signature="signature:test",
            signing_key_ref="signing-key:test",
        )
        self.assertEqual(signed["event_hash"], unsigned["event_hash"])
        self.assertEqual(signed["actor_signature"], "signature:test")

    def test_event_helper_rejects_mismatched_caller_supplied_event_hash(self) -> None:
        with self.assertRaises(JarvisProtocolValidationError) as context:
            create_jarvis_event(
                id="event-bad-hash",
                sequence=1,
                event_type="work_session.created",
                work_session_id="ws-test",
                actor_id="actor-human-test",
                timestamp="2026-06-16T10:00:00Z",
                payload={
                    "object_type": "work_session",
                    "object_id": "ws-test",
                    "action": "created",
                },
                event_hash="hash:not-the-canonical-event",
            )
        self.assertEqual(context.exception.error["error_id"], "invalid_event_hash")

    def test_next_event_helper_rejects_cross_work_session_event_linkage(self) -> None:
        other = create_next_jarvis_event(
            id="event-other",
            event_type="work_session.created",
            work_session_id="ws-other",
            actor_id="actor-human-test",
            timestamp="2026-06-16T10:00:00Z",
            payload={
                "object_type": "work_session",
                "object_id": "ws-other",
                "action": "created",
            },
        )
        with self.assertRaises(JarvisProtocolValidationError) as context:
            create_next_jarvis_event(
                events=[other],
                id="event-wrong-link",
                event_type="work_session.completed",
                work_session_id="ws-test",
                actor_id="actor-human-test",
                timestamp="2026-06-16T10:10:00Z",
                payload={
                    "object_type": "work_session",
                    "object_id": "ws-test",
                    "action": "completed",
                },
            )
        self.assertEqual(context.exception.error["error_id"], "invalid_export")

    def test_operation_helper_rejects_concrete_path_work_session_mismatch(self) -> None:
        with self.assertRaises(JarvisProtocolValidationError) as context:
            create_operation_envelope(
                operation_id="appendJarvisEvent",
                actor_id="actor-human-test",
                authorization=AUTHORIZATION,
                path="/work-sessions/ws-other/events",
                work_session_id="ws-test",
                idempotency_key="idem-test",
                request_timestamp="2026-06-16T10:00:00Z",
                expected_work_session_revision=0,
                previous_event_hash="hash:protocol-genesis",
                body_ref="records.jarvis_events.created",
            )
        self.assertEqual(context.exception.error["error_id"], "path_body_id_mismatch")

    def test_evidence_manifest_helper_rejects_empty_refs_and_root_drift(self) -> None:
        event = create_next_jarvis_event(
            id="event-root",
            event_type="work_session.completed",
            work_session_id="ws-test",
            actor_id="actor-human-test",
            timestamp="2026-06-16T10:10:00Z",
            payload={
                "object_type": "work_session",
                "object_id": "ws-test",
                "action": "completed",
            },
        )
        work_session = {
            "id": "ws-test",
            "objective": "Reject malformed manifest helpers.",
            "status": "completed",
            "last_event_hash": event["event_hash"],
        }
        with self.assertRaises(JarvisProtocolValidationError) as empty_context:
            create_evidence_manifest(
                id="evidence-empty",
                work_session=work_session,
                events=[event],
                generated_by_actor_id="actor-human-test",
                generated_at="2026-06-16T10:11:00Z",
            )
        self.assertEqual(empty_context.exception.error["error_id"], "invalid_export")

        with self.assertRaises(JarvisProtocolValidationError) as drift_context:
            create_evidence_manifest(
                id="evidence-root-drift",
                work_session=work_session,
                events=[event],
                event_chain_root="hash:wrong-root",
                generated_by_actor_id="actor-human-test",
                generated_at="2026-06-16T10:11:00Z",
                evidence_item_refs=[
                    {
                        "id": "evidence-item-test",
                        "work_session_id": "ws-test",
                        "source_event_refs": ["event-root"],
                        "captured_by_actor_id": "actor-human-test",
                        "evidence_type": "artifact",
                        "artifact_ref": "artifact:test",
                        "content_hash": "hash:content",
                        "trust_label": "verified",
                        "redaction_state": "none",
                        "captured_at": "2026-06-16T10:10:00Z",
                        "limitation_refs": [],
                    }
                ],
            )
        self.assertEqual(drift_context.exception.error["error_id"], "invalid_evidence_export_state")

    def test_non_work_session_mutation_headers_do_not_require_revision_hash(self) -> None:
        result = validate_mutation_headers(
            {
                "Authorization": "HostAuth test",
                "Jarvis-Protocol-Version": "v0.1",
                "Jarvis-Actor-Id": "actor-test",
                "Jarvis-Idempotency-Key": "idem-test",
                "Jarvis-Request-Timestamp": "2026-06-16T10:00:00Z",
            },
            {
                "work_session_scoped": False,
                "now": datetime(2026, 6, 16, 10, 0, 0, tzinfo=timezone.utc),
            },
        )
        self.assertTrue(result.valid, result.errors)

    def test_non_work_session_mutations_allow_extra_work_session_headers_without_requiring_them(self) -> None:
        result = validate_mutation_headers(
            {
                "Authorization": "HostAuth test",
                "Jarvis-Protocol-Version": "v0.1",
                "Jarvis-Actor-Id": "actor-test",
                "Jarvis-Idempotency-Key": "idem-test",
                "Jarvis-Request-Timestamp": "2026-06-16T10:00:00Z",
                "Jarvis-Expected-WorkSession-Revision": 0,
                "Jarvis-Previous-Event-Hash": "hash:protocol-genesis",
            },
            {
                "work_session_scoped": False,
                "now": datetime(2026, 6, 16, 10, 0, 0, tzinfo=timezone.utc),
            },
        )
        self.assertTrue(result.valid, result.errors)

    def test_required_identity_and_replay_headers_reject_empty_values(self) -> None:
        result = validate_mutation_headers(
            {
                "Authorization": " ",
                "Jarvis-Protocol-Version": "v0.1",
                "Jarvis-Actor-Id": "actor-test",
                "Jarvis-Idempotency-Key": "idem-test",
                "Jarvis-Request-Timestamp": "2026-06-16T10:00:00Z",
                "Jarvis-Expected-WorkSession-Revision": 0,
                "Jarvis-Previous-Event-Hash": "hash:protocol-genesis",
            },
            {"now": datetime(2026, 6, 16, 10, 0, 0, tzinfo=timezone.utc)},
        )
        self.assertFalse(result.valid)
        self.assertEqual(result.errors[0]["field"], "headers.Authorization")

    def test_required_mutation_headers_reject_null_values(self) -> None:
        base_headers = {
            "Authorization": "HostAuth test",
            "Jarvis-Protocol-Version": "v0.1",
            "Jarvis-Actor-Id": "actor-test",
            "Jarvis-Idempotency-Key": "idem-test",
            "Jarvis-Request-Timestamp": "2026-06-16T10:00:00Z",
            "Jarvis-Expected-WorkSession-Revision": 0,
            "Jarvis-Previous-Event-Hash": "hash:protocol-genesis",
        }
        cases = [
            ("Jarvis-Request-Timestamp", "missing_request_timestamp"),
            ("Jarvis-Expected-WorkSession-Revision", "missing_expected_work_session_revision"),
            ("Jarvis-Previous-Event-Hash", "invalid_previous_event_hash"),
        ]
        for header, error_id in cases:
            headers = dict(base_headers)
            headers[header] = None
            result = validate_mutation_headers(headers)
            self.assertFalse(result.valid, header)
            self.assertEqual(result.errors[0]["error_id"], error_id)

    def test_approval_scope_requires_review_timestamp_when_review_context_exists(self) -> None:
        approval_scope = {
            "id": "approval-test",
            "request_id": "request-test",
            "review_id": "review-test",
            "policy_decision_id": "policy-decision-test",
            "request_revision": 3,
            "request_event_hash": "hash:request",
            "approved_action": {"action": "fetch", "target": "registry.npmjs.org"},
            "allowed_scope": {"scope_ref": "scope:allow"},
            "denied_scope": {"scope_ref": "scope:deny"},
            "expires_at": "2026-06-16T10:30:00Z",
            "max_uses": 3,
            "applies_to_work_session_id": "ws-test",
            "applies_to_actor_id": "actor-agent-test",
            "normalized_action_hash": "hash:approval-test",
        }
        result = validate_approval_scope(
            approval_scope,
            {
                "request": {
                    "id": "request-test",
                    "policy_decision_id": "policy-decision-test",
                    "requester_actor_id": "actor-agent-test",
                },
                "review": {
                    "id": "review-test",
                    "work_session_id": "ws-test",
                },
            },
        )
        self.assertFalse(result.valid)
        self.assertEqual(result.errors[0]["error_id"], "invalid_approval_scope")

    def test_timestamp_skew_rejects_future_requests_beyond_one_minute(self) -> None:
        result = validate_mutation_headers(
            {
                "Authorization": "HostAuth test",
                "Jarvis-Protocol-Version": "v0.1",
                "Jarvis-Actor-Id": "actor-test",
                "Jarvis-Idempotency-Key": "idem-test",
                "Jarvis-Request-Timestamp": "2026-06-16T10:04:00Z",
                "Jarvis-Expected-WorkSession-Revision": 0,
                "Jarvis-Previous-Event-Hash": "hash:protocol-genesis",
            },
            {"now": datetime(2026, 6, 16, 10, 0, 0, tzinfo=timezone.utc)},
        )
        self.assertFalse(result.valid)
        self.assertEqual(result.errors[0]["error_id"], "stale_request_timestamp")

    def test_timestamp_skew_requires_explicit_now_for_parity(self) -> None:
        result = validate_mutation_headers(
            {
                "Authorization": "HostAuth test",
                "Jarvis-Protocol-Version": "v0.1",
                "Jarvis-Actor-Id": "actor-test",
                "Jarvis-Idempotency-Key": "idem-test",
                "Jarvis-Request-Timestamp": "2026-06-16T10:04:00Z",
                "Jarvis-Expected-WorkSession-Revision": 0,
                "Jarvis-Previous-Event-Hash": "hash:protocol-genesis",
            }
        )
        self.assertTrue(result.valid, result.errors)

    def test_previous_hash_header_requires_protocol_hash_prefix(self) -> None:
        result = validate_mutation_headers(
            {
                "Authorization": "HostAuth test",
                "Jarvis-Protocol-Version": "v0.1",
                "Jarvis-Actor-Id": "actor-test",
                "Jarvis-Idempotency-Key": "idem-test",
                "Jarvis-Request-Timestamp": "2026-06-16T10:00:00Z",
                "Jarvis-Expected-WorkSession-Revision": 0,
                "Jarvis-Previous-Event-Hash": "not-a-protocol-hash",
            },
            {"now": datetime(2026, 6, 16, 10, 0, 0, tzinfo=timezone.utc)},
        )
        self.assertFalse(result.valid)
        self.assertEqual(result.errors[0]["error_id"], "invalid_previous_event_hash")

    def test_read_operations_bind_actor_to_header(self) -> None:
        result = validate_operation_headers(
            {
                "operation_id": "exportEvidenceManifest",
                "method": "GET",
                "path": "/work-sessions/ws-test/export",
                "actor_id": "actor-body",
                "expected_status": 200,
                "headers": {
                    "Authorization": "HostAuth test",
                    "Jarvis-Protocol-Version": "v0.1",
                    "Jarvis-Actor-Id": "actor-header",
                },
            }
        )
        self.assertFalse(result.valid)
        self.assertEqual(result.errors[0]["error_id"], "actor_body_id_mismatch")

    def test_read_headers_reject_mutation_only_requirements(self) -> None:
        result = validate_read_headers(
            {
                "Authorization": "HostAuth test",
                "Jarvis-Protocol-Version": "v0.1",
                "Jarvis-Actor-Id": "actor-test",
            }
        )
        self.assertTrue(result.valid, result.errors)

        extra_headers = validate_read_headers(
            {
                "Authorization": "HostAuth test",
                "Jarvis-Protocol-Version": "v0.1",
                "Jarvis-Actor-Id": "actor-test",
                "Jarvis-Idempotency-Key": "idem-test",
            }
        )
        self.assertFalse(extra_headers.valid)
        self.assertEqual(extra_headers.errors[0]["error_id"], "invalid_export")

    def test_outcome_report_requires_terminal_work_session_source(self) -> None:
        report = {
            "id": "outcome-test",
            "work_session_id": "ws-test",
            "source_ref": "source:ws-test",
            "reporter_ref": "reporter:test",
            "accepted_by_actor_id": "actor-human-test",
            "outcome": "accepted",
            "learning_record_refs": ["learning-test"],
            "received_at": "2026-06-16T10:00:00Z",
        }
        missing_source = validate_outcome_report(report)
        self.assertFalse(missing_source.valid)
        self.assertEqual(missing_source.errors[0]["error_id"], "outcome_report_requires_terminal_source")

        active_source = validate_outcome_report(report, {"work_session": {"id": "ws-test", "status": "active"}})
        self.assertFalse(active_source.valid)
        self.assertEqual(active_source.errors[0]["error_id"], "outcome_report_requires_terminal_source")

        completed_source = validate_outcome_report(
            report,
            {"work_session": {"id": "ws-test", "status": "completed"}},
        )
        self.assertTrue(completed_source.valid, completed_source.errors)

        wrong_source = validate_outcome_report(
            report,
            {"work_session": {"id": "ws-other", "status": "completed"}},
        )
        self.assertFalse(wrong_source.valid)
        self.assertEqual(wrong_source.errors[0]["error_id"], "outcome_report_requires_terminal_source")

    def test_evidence_manifest_requires_terminal_work_session_source(self) -> None:
        manifest = {
            "id": "evidence-test",
            "work_session_id": "ws-test",
            "generated_by_actor_id": "actor-human-test",
            "objective": "test",
            "event_chain_root": "hash:root",
            "evidence_item_refs": [
                {
                    "id": "evidence-item-test",
                    "work_session_id": "ws-test",
                    "source_event_refs": ["event-test"],
                    "captured_by_actor_id": "actor-agent-test",
                    "evidence_type": "artifact",
                    "artifact_ref": "artifact:test",
                    "content_hash": "hash:content",
                    "trust_label": "verified",
                    "redaction_state": "none",
                    "captured_at": "2026-06-16T10:00:00Z",
                    "limitation_refs": [],
                },
            ],
            "policy_decision_refs": [],
            "request_refs": [],
            "review_refs": [],
            "takeover_refs": [],
            "contribution_refs": [],
            "export_profile": {
                "profile": "portable",
            },
            "generated_at": "2026-06-16T10:00:00Z",
        }
        missing_source = validate_evidence_manifest(manifest)
        self.assertFalse(missing_source.valid)
        self.assertEqual(missing_source.errors[0]["error_id"], "invalid_evidence_export_state")

        active_source = validate_evidence_manifest(manifest, {"work_session": {"id": "ws-test", "status": "active"}})
        self.assertFalse(active_source.valid)
        self.assertEqual(active_source.errors[0]["error_id"], "invalid_evidence_export_state")

        completed_source = validate_evidence_manifest(
            manifest,
            {"work_session": {"id": "ws-test", "status": "completed"}},
        )
        self.assertTrue(completed_source.valid, completed_source.errors)

        wrong_source = validate_evidence_manifest(
            manifest,
            {"work_session": {"id": "ws-other", "status": "completed"}},
        )
        self.assertFalse(wrong_source.valid)
        self.assertEqual(wrong_source.errors[0]["error_id"], "invalid_evidence_export_state")
        self.assertEqual(wrong_source.errors[0]["field"], "work_session_id")

        root_drift = validate_evidence_manifest(
            {**manifest, "event_chain_root": "hash:wrong-root"},
            {
                "work_session": {
                    "id": "ws-test",
                    "status": "completed",
                    "last_event_hash": "hash:root",
                }
            },
        )
        self.assertFalse(root_drift.valid)
        self.assertEqual(root_drift.errors[0]["error_id"], "invalid_evidence_export_state")
        self.assertEqual(root_drift.errors[0]["field"], "event_chain_root")

    def test_protocol_error_helper_emits_openapi_error_envelope(self) -> None:
        error = protocol_error(
            "missing_actor",
            {
                "object_type": "headers",
                "field": "Jarvis-Actor-Id",
                "reason": "actor missing",
                "remediation": "send actor header",
                "trace_id": "trace:test",
            },
        )
        self.assertEqual(
            error,
            {
                "error_id": "missing_actor",
                "protocol_version": "v0.1",
                "object_type": "headers",
                "field": "Jarvis-Actor-Id",
                "reason": "actor missing",
                "remediation": "send actor header",
                "trace_id": "trace:test",
            },
        )

    def test_protocol_error_helper_rejects_ids_outside_openapi_enum(self) -> None:
        error = protocol_error("not_in_openapi")
        self.assertEqual(error["error_id"], "invalid_export")
        self.assertEqual(error["field"], "error_id")

    def test_closed_schema_validation_rejects_unknown_protocol_fields(self) -> None:
        result = validate_protocol_record(
            "OutcomeReport",
            {
                "id": "outcome-test",
                "work_session_id": "ws-test",
                "source_ref": "source:ws-test",
                "reporter_ref": "reporter:test",
                "accepted_by_actor_id": "actor-human-test",
                "outcome": "accepted",
                "learning_record_refs": ["learning-test"],
                "received_at": "2026-06-16T10:00:00Z",
                "unexpected_host_field": "host-only",
            },
        )
        self.assertFalse(result.valid)
        self.assertEqual(result.errors[0]["error_id"], "invalid_export")

    def test_schema_validation_rejects_invalid_protocol_version_and_enum(self) -> None:
        bad_version = validate_protocol_record(
            "WorkSession",
            {
                "id": "ws-test",
                "protocol_version": "v9",
                "objective": "test",
                "human_worker_id": "worker-human",
                "agent_worker_id": "worker-agent",
                "policy_id": "policy-test",
                "created_by_actor_id": "actor-human",
                "status": "active",
                "context_manifest": [],
                "event_log_ref": "events:test",
                "contribution_ledger_ref": "contributions:test",
                "evidence_manifest_ref": "evidence:test",
                "learning_record_refs": [],
                "created_at": "2026-06-16T10:00:00Z",
                "updated_at": "2026-06-16T10:00:00Z",
                "revision": 0,
                "last_event_hash": "hash:protocol-genesis",
            },
        )
        self.assertFalse(bad_version.valid)
        self.assertEqual(bad_version.errors[0]["error_id"], "invalid_export")

        bad_status = validate_protocol_record(
            "WorkSession",
            {
                "id": "ws-test",
                "protocol_version": "v0.1",
                "objective": "test",
                "human_worker_id": "worker-human",
                "agent_worker_id": "worker-agent",
                "policy_id": "policy-test",
                "created_by_actor_id": "actor-human",
                "status": "not_a_state",
                "context_manifest": [],
                "event_log_ref": "events:test",
                "contribution_ledger_ref": "contributions:test",
                "evidence_manifest_ref": "evidence:test",
                "learning_record_refs": [],
                "created_at": "2026-06-16T10:00:00Z",
                "updated_at": "2026-06-16T10:00:00Z",
                "revision": 0,
                "last_event_hash": "hash:protocol-genesis",
            },
        )
        self.assertFalse(bad_status.valid)
        self.assertEqual(bad_status.errors[0]["error_id"], "unknown_state")

    def test_generic_schema_validation_rejects_non_object_records_as_invalid_export(self) -> None:
        result = validate_protocol_record("Request", None)
        self.assertFalse(result.valid)
        self.assertEqual(result.errors[0]["error_id"], "invalid_export")

    def test_generic_schema_validation_rejects_unknown_object_type(self) -> None:
        result = validate_protocol_record("TypoObject", {})
        self.assertFalse(result.valid)
        self.assertEqual(result.errors[0]["error_id"], "invalid_export")
        self.assertEqual(result.errors[0]["field"], "object_type")

    def test_protocol_record_validation_rejects_nested_host_private_fields(self) -> None:
        result = validate_protocol_record(
            "JarvisEvent",
            {
                "id": "event-test",
                "sequence": 1,
                "type": "work_session.created",
                "work_session_id": "ws-test",
                "actor_id": "actor-test",
                "timestamp": "2026-06-16T10:00:00Z",
                "payload": {
                    "object_type": "work_session",
                    "object_id": "ws-test",
                    "action": "created",
                    "raw_runtime_state": "host-only",
                },
                "previous_hash": "hash:protocol-genesis",
                "event_hash": "hash:event-test",
                "canonicalization": {
                    "serialization": "json-c14n",
                    "hash_method": "sha256",
                    "profile_ref": "canonicalization:v0.1",
                },
            },
        )
        self.assertFalse(result.valid)
        self.assertEqual(result.errors[0]["error_id"], "forbidden_host_private_field")
        self.assertEqual(result.errors[0]["field"], "payload.raw_runtime_state")

    def test_canonicalization_and_hashing_are_stable_across_key_order(self) -> None:
        left = {"b": 2, "a": {"y": True, "x": "yes"}}
        right = {"a": {"x": "yes", "y": True}, "b": 2}
        self.assertEqual(canonicalize_protocol_value(left), canonicalize_protocol_value(right))
        self.assertEqual(hash_protocol_value(left), hash_protocol_value(right))

    def test_event_hash_chain_helper_rejects_broken_previous_hashes(self) -> None:
        valid = validate_event_hash_chain(
            [
                {"sequence": 1, "previous_hash": "hash:protocol-genesis", "event_hash": "hash:first"},
                {"sequence": 2, "previous_hash": "hash:first", "event_hash": "hash:second"},
            ]
        )
        self.assertTrue(valid.valid, valid.errors)

        invalid = validate_event_hash_chain(
            [
                {"sequence": 1, "previous_hash": "hash:protocol-genesis", "event_hash": "hash:first"},
                {"sequence": 2, "previous_hash": "hash:wrong", "event_hash": "hash:second"},
            ]
        )
        self.assertFalse(invalid.valid)
        self.assertEqual(invalid.errors[0]["error_id"], "invalid_previous_event_hash")

    def test_event_hash_chain_rejects_missing_event_hash(self) -> None:
        result = validate_event_hash_chain(
            [
                {"sequence": 1, "previous_hash": "hash:protocol-genesis"},
            ]
        )
        self.assertFalse(result.valid)
        self.assertEqual(result.errors[0]["error_id"], "invalid_event_hash")
        self.assertEqual(result.errors[0]["field"], "event_hash")

    def test_event_hash_chain_rejects_malformed_sequence(self) -> None:
        result = validate_event_hash_chain(
            [
                {
                    "sequence": "1",
                    "previous_hash": "hash:protocol-genesis",
                    "event_hash": "hash:first",
                },
            ]
        )
        self.assertFalse(result.valid)
        self.assertEqual(result.errors[0]["error_id"], "invalid_export")
        self.assertEqual(result.errors[0]["field"], "sequence")

    def test_event_hash_chain_rejects_nonpositive_or_duplicate_sequence(self) -> None:
        nonpositive = validate_event_hash_chain(
            [
                {
                    "sequence": 0,
                    "previous_hash": "hash:protocol-genesis",
                    "event_hash": "hash:first",
                },
            ]
        )
        self.assertFalse(nonpositive.valid)
        self.assertEqual(nonpositive.errors[0]["error_id"], "invalid_export")
        self.assertEqual(nonpositive.errors[0]["field"], "sequence")

        duplicate = validate_event_hash_chain(
            [
                {"sequence": 1, "previous_hash": "hash:protocol-genesis", "event_hash": "hash:first"},
                {"sequence": 1, "previous_hash": "hash:first", "event_hash": "hash:second"},
            ]
        )
        self.assertFalse(duplicate.valid)
        self.assertEqual(duplicate.errors[0]["error_id"], "invalid_export")
        self.assertEqual(duplicate.errors[0]["field"], "sequence")

    def test_event_hash_chain_rejects_duplicate_event_hash(self) -> None:
        result = validate_event_hash_chain(
            [
                {"sequence": 1, "previous_hash": "hash:protocol-genesis", "event_hash": "hash:same"},
                {"sequence": 2, "previous_hash": "hash:same", "event_hash": "hash:same"},
            ]
        )
        self.assertFalse(result.valid)
        self.assertEqual(result.errors[0]["error_id"], "invalid_event_hash")
        self.assertEqual(result.errors[0]["field"], "event_hash")

    def test_host_private_field_scanner_returns_forbidden_path(self) -> None:
        self.assertEqual(
            find_forbidden_host_private_field({"export_profile": {}, "session_cookie": "secret"}),
            "session_cookie",
        )
        self.assertEqual(
            find_forbidden_host_private_field({"export_profile": {}, "private-key": "secret"}),
            "private-key",
        )
        self.assertEqual(
            find_forbidden_host_private_field({"export_profile": {}, "rawPrompt": "secret"}),
            "rawPrompt",
        )


if __name__ == "__main__":
    unittest.main()
