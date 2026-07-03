from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from jarvis_protocol import validate_fixture


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = PACKAGE_ROOT / "fixtures/v0.1"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class FixtureValidationTests(unittest.TestCase):
    def test_valid_golden_path_fixture_is_accepted(self) -> None:
        fixture = read_json(FIXTURE_ROOT / "valid/golden-path.json")
        result = validate_fixture(fixture)
        self.assertTrue(result.valid, result.errors)

    def test_valid_takeover_path_fixture_is_accepted(self) -> None:
        fixture = read_json(FIXTURE_ROOT / "valid/takeover-path.json")
        result = validate_fixture(fixture)
        self.assertTrue(result.valid, result.errors)

    def test_takeover_path_fixture_requires_reconciliation_before_resume(self) -> None:
        fixture = read_json(FIXTURE_ROOT / "valid/takeover-path.json")
        fixture["records"]["takeovers"]["reconciliation_required"]["state"] = "resumed"
        result = validate_fixture(fixture)
        self.assertFalse(result.valid)
        self.assertEqual(result.errors[0]["error_id"], "invalid_transition")

    def test_golden_path_outcome_report_requires_terminal_work_session(self) -> None:
        fixture = read_json(FIXTURE_ROOT / "valid/golden-path.json")
        fixture["records"]["work_sessions"]["outcome_active"] = {
            **copy.deepcopy(fixture["records"]["work_sessions"]["active"]),
            "id": "ws-outcome-active",
        }
        fixture["records"]["outcome_reports"]["post_session"]["work_session_id"] = "ws-outcome-active"
        result = validate_fixture(fixture)
        self.assertFalse(result.valid)
        self.assertEqual(result.errors[0]["error_id"], "outcome_report_requires_terminal_source")

    def test_fixture_validation_binds_body_actor_fields_to_actor_header(self) -> None:
        fixture = read_json(FIXTURE_ROOT / "valid/golden-path.json")
        fixture["records"]["reviews"]["approve_source"]["reviewer_actor_id"] = "actor-agent-golden"
        result = validate_fixture(fixture)
        self.assertFalse(result.valid)
        self.assertEqual(result.errors[0]["error_id"], "actor_body_id_mismatch")

    def test_fixture_validation_enforces_work_session_genesis_headers(self) -> None:
        fixture = read_json(FIXTURE_ROOT / "valid/golden-path.json")
        operation = next(op for op in fixture["operations"] if op["operation_id"] == "createWorkSession")
        operation["headers"]["Jarvis-Expected-WorkSession-Revision"] = 1
        result = validate_fixture(fixture)
        self.assertFalse(result.valid)
        self.assertEqual(result.errors[0]["error_id"], "stale_work_session_revision")

    def test_fixture_validation_enforces_work_session_genesis_body(self) -> None:
        fixture = read_json(FIXTURE_ROOT / "valid/golden-path.json")
        fixture["records"]["work_sessions"]["genesis_request"]["revision"] = 1
        result = validate_fixture(fixture)
        self.assertFalse(result.valid)
        self.assertEqual(result.errors[0]["error_id"], "stale_work_session_revision")

    def test_fixture_validation_rejects_unrepresented_previous_hash(self) -> None:
        fixture = read_json(FIXTURE_ROOT / "valid/golden-path.json")
        operation = next(op for op in fixture["operations"] if op["operation_id"] == "recordReview")
        operation["headers"]["Jarvis-Expected-WorkSession-Revision"] = 999
        operation["headers"]["Jarvis-Previous-Event-Hash"] = "hash:unrepresented"
        result = validate_fixture(fixture)
        self.assertFalse(result.valid)
        self.assertEqual(result.errors[0]["error_id"], "invalid_previous_event_hash")

    def test_fixture_validation_rejects_operation_id_read_downgrade(self) -> None:
        fixture = read_json(FIXTURE_ROOT / "valid/golden-path.json")
        operation = next(op for op in fixture["operations"] if op["operation_id"] == "createRequest")
        operation["method"] = "GET"
        operation["path"] = "/work-sessions/ws-golden-001/export"
        operation["headers"] = {
            "Authorization": "HostAuth fixture",
            "Jarvis-Protocol-Version": "v0.1",
            "Jarvis-Actor-Id": operation["actor_id"],
        }
        result = validate_fixture(fixture)
        self.assertFalse(result.valid)
        self.assertEqual(result.errors[0]["error_id"], "invalid_export")
        self.assertEqual(result.errors[0]["field"], "method")

    def test_fixture_validation_rejects_operation_path_and_status_drift(self) -> None:
        path_fixture = read_json(FIXTURE_ROOT / "valid/golden-path.json")
        path_operation = next(op for op in path_fixture["operations"] if op["operation_id"] == "createRequest")
        path_operation["path"] = "/work-sessions/ws-golden-001/export"
        path_result = validate_fixture(path_fixture)
        self.assertFalse(path_result.valid)
        self.assertEqual(path_result.errors[0]["error_id"], "invalid_export")
        self.assertEqual(path_result.errors[0]["field"], "path")

        status_fixture = read_json(FIXTURE_ROOT / "valid/golden-path.json")
        status_operation = next(op for op in status_fixture["operations"] if op["operation_id"] == "createRequest")
        status_operation["expected_status"] = 418
        status_result = validate_fixture(status_fixture)
        self.assertFalse(status_result.valid)
        self.assertEqual(status_result.errors[0]["error_id"], "invalid_export")
        self.assertEqual(status_result.errors[0]["field"], "expected_status")

    def test_fixture_validation_rejects_accepted_agent_action_without_prior_policy_decision(self) -> None:
        fixture = read_json(FIXTURE_ROOT / "valid/golden-path.json")
        fixture["records"]["jarvis_events"]["evidence_captured"]["timestamp"] = "2026-06-16T10:03:00Z"
        result = validate_fixture(fixture)
        self.assertFalse(result.valid)
        self.assertEqual(result.errors[0]["error_id"], "missing_policy_decision")

    def test_fixture_validation_rejects_missing_inline_policy_decision_ref(self) -> None:
        fixture = read_json(FIXTURE_ROOT / "valid/golden-path.json")
        event = fixture["records"]["jarvis_events"]["evidence_captured"]
        event["timestamp"] = "2026-06-16T10:03:00Z"
        event["payload"]["policy_decision_ref"] = "policy-decision:missing"
        result = validate_fixture(fixture)
        self.assertFalse(result.valid)
        self.assertEqual(result.errors[0]["error_id"], "missing_policy_decision")

    def test_fixture_validation_rejects_wrong_fixture_protocol_version(self) -> None:
        fixture = read_json(FIXTURE_ROOT / "valid/golden-path.json")
        fixture["protocol_version"] = "v9"
        result = validate_fixture(fixture)
        self.assertFalse(result.valid)
        self.assertEqual(result.errors[0]["error_id"], "unsupported_protocol_version")

    def test_fixture_validation_rejects_host_private_cookie_fields(self) -> None:
        fixture = read_json(FIXTURE_ROOT / "valid/golden-path.json")
        fixture["records"]["evidence_manifests"]["portable_export"]["evidence_item_refs"][0]["cookie"] = "secret"
        result = validate_fixture(fixture)
        self.assertFalse(result.valid)
        self.assertEqual(result.errors[0]["error_id"], "forbidden_host_private_field")

    def test_fixture_validation_rejects_unknown_nested_evidence_item_fields(self) -> None:
        fixture = read_json(FIXTURE_ROOT / "valid/golden-path.json")
        fixture["records"]["evidence_manifests"]["portable_export"]["evidence_item_refs"][0][
            "unexpected_extra"
        ] = "host"
        result = validate_fixture(fixture)
        self.assertFalse(result.valid)
        self.assertEqual(result.errors[0]["error_id"], "invalid_export")

    def test_fixture_validation_allows_read_from_terminal_work_session(self) -> None:
        fixture = read_json(FIXTURE_ROOT / "valid/golden-path.json")
        fixture["records"]["work_sessions"] = {
            "completed": copy.deepcopy(fixture["records"]["work_sessions"]["completed"]),
            "genesis_request": copy.deepcopy(fixture["records"]["work_sessions"]["genesis_request"]),
            "active": copy.deepcopy(fixture["records"]["work_sessions"]["active"]),
        }
        fixture["operations"].insert(
            0,
            {
                "operation_id": "getWorkSession",
                "method": "GET",
                "path": "/work-sessions/ws-golden-001",
                "headers": {
                    "Authorization": "HostAuth fixture",
                    "Jarvis-Protocol-Version": "v0.1",
                    "Jarvis-Actor-Id": "actor-human-golden",
                },
                "actor_id": "actor-human-golden",
                "work_session_id": "ws-golden-001",
                "expected_status": 200,
            },
        )
        result = validate_fixture(fixture)
        self.assertTrue(result.valid, result.errors)

    def test_invalid_fixture_set_rejects_with_expected_error_id(self) -> None:
        for path in sorted((FIXTURE_ROOT / "invalid").glob("*.json")):
            with self.subTest(path=path.name):
                fixture = read_json(path)
                result = validate_fixture(fixture)
                self.assertFalse(result.valid, path.name)
                self.assertEqual(result.errors[0]["error_id"], fixture["expected_error_id"])


if __name__ == "__main__":
    unittest.main()
