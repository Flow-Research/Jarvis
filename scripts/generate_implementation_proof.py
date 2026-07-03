#!/usr/bin/env python3
"""Generate the Jarvis existing-agent implementation proof."""

from __future__ import annotations

from pathlib import Path
import json
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PYTHON_PACKAGE_SRC = ROOT / "packages" / "python" / "src"
PROOF_PATH = (
    ROOT
    / "docs"
    / "examples"
    / "implementation-proof"
    / "native-coding-agent"
    / "proof.json"
)
AUTHORIZATION = "HostAuth proof"
PROTOCOL_VERSION = "v0.1"
WORK_SESSION_ID = "ws-native-coding-agent-proof"
HUMAN_WORKER_ID = "worker-human-proof"
AGENT_WORKER_ID = "worker-agent-proof"
HUMAN_ACTOR_ID = "actor-human-proof"
AGENT_ACTOR_ID = "actor-agent-proof"
REGISTRAR_ACTOR_ID = "actor-proof-registrar"
POLICY_ID = "policy-proof-bounded"

sys.path.insert(0, str(PYTHON_PACKAGE_SRC))

import jarvis_protocol  # noqa: E402


def requested_action() -> dict[str, str]:
    return {
        "action": "fetch_external_source",
        "target_ref": "source:existing-agent-reference",
        "scope_ref": "scope:external-source",
    }


def action_hash() -> str:
    return jarvis_protocol.hash_protocol_value(requested_action())


def worker_records() -> dict[str, dict[str, Any]]:
    return {
        "human": {
            "id": HUMAN_WORKER_ID,
            "type": "human",
            "role": "responsible reviewer",
            "authority_scope": {
                "grants": ["policy:own", "review:approve", "takeover:start"],
            },
            "accountability_scope": {
                "accountable_for": ["objective", "policy", "final_review"],
            },
            "display_name": "HumanWorker Proof",
            "capabilities": [
                {
                    "ref": "capability:review",
                    "capability_type": "human_judgment",
                    "required": True,
                },
            ],
        },
        "agent": {
            "id": AGENT_WORKER_ID,
            "type": "agent",
            "role": "bounded coding agent",
            "authority_scope": {
                "grants": [
                    "action:propose",
                    "action:execute_after_policy",
                    "evidence:capture",
                ],
            },
            "accountability_scope": {
                "accountable_for": [
                    "policy_checked_execution",
                    "evidence_capture",
                ],
            },
            "display_name": "Native Coding Agent Proof",
            "capabilities": [
                {
                    "ref": "capability:code_review_summary",
                    "capability_type": "coding",
                    "required": True,
                },
            ],
        },
    }


def actor_records() -> dict[str, dict[str, Any]]:
    return {
        "human": {
            "id": HUMAN_ACTOR_ID,
            "worker_id": HUMAN_WORKER_ID,
            "type": "human",
            "event_authority": {
                "can_append_events": True,
                "allowed_event_types": [
                    "work_session.created",
                    "review.recorded",
                    "contribution.recorded",
                    "learning.recorded",
                    "memory_proposal.created",
                    "skill_proposal.created",
                    "work_session.completed",
                ],
            },
            "contribution_scope": {
                "contribution_roles": ["human", "shared"],
            },
            "created_at": "2026-07-03T09:00:00Z",
            "valid_from": "2026-07-03T09:00:00Z",
        },
        "agent": {
            "id": AGENT_ACTOR_ID,
            "worker_id": AGENT_WORKER_ID,
            "type": "agent",
            "event_authority": {
                "can_append_events": True,
                "allowed_event_types": [
                    "policy_decision.recorded",
                    "request.created",
                    "evidence.captured",
                    "contribution.recorded",
                ],
            },
            "contribution_scope": {
                "contribution_roles": ["agent", "shared"],
            },
            "created_at": "2026-07-03T09:00:00Z",
            "valid_from": "2026-07-03T09:00:00Z",
        },
    }


def participant_records() -> tuple[dict[str, Any], dict[str, Any]]:
    human_worker = {
        "worker_id": HUMAN_WORKER_ID,
        "actor_id": HUMAN_ACTOR_ID,
        "role": "policy owner and reviewer",
        "policy_authority": {"grants": ["policy:own", "policy:narrow"]},
        "review_authority": {
            "grants": [
                "review:approve",
                "review:narrow",
                "review:deny",
                "takeover:start",
            ],
        },
        "profile_ref": "profile:human-proof",
        "domain_context_refs": ["context:coding-task-brief"],
        "preferences": {"review.default_detail": "evidence_first"},
        "boundaries": ["external source access requires review"],
        "known_patterns": [
            "ask for bounded approval before external source collection",
        ],
    }
    agent_worker = {
        "worker_id": AGENT_WORKER_ID,
        "actor_id": AGENT_ACTOR_ID,
        "agent_ref": "agent:native-coding-agent",
        "role": "bounded coding and research agent",
        "capability_refs": [
            {
                "ref": "capability:code_review_summary",
                "capability_type": "coding",
                "required": True,
            },
        ],
        "autonomy_level": "bounded_execute",
        "operating_constraints": [
            "record PolicyDecision before action affects WorkSession state",
            "create Request when Policy denies action",
            "capture evidence during work",
        ],
        "tool_access_profile": "tool-profile:policy-bounded",
        "memory_access_profile": "memory-profile:read-only",
    }
    return human_worker, agent_worker


def policy_record() -> dict[str, Any]:
    return {
        "id": POLICY_ID,
        "owner_worker_id": HUMAN_WORKER_ID,
        "created_by_actor_id": HUMAN_ACTOR_ID,
        "autonomy_level": "bounded_execute",
        "allowed_actions": [
            {
                "action": "inspect_local_context",
                "scope_ref": "scope:local-worksession",
                "grant_refs": ["grant:local-context-read"],
            },
        ],
        "denied_actions": [
            {
                "action": "fetch_external_source",
                "scope_ref": "scope:external-source",
            },
        ],
        "review_required_actions": [
            {
                "action": "submit_final_artifact",
                "scope_ref": "scope:final-submission",
            },
        ],
        "risk_classes": ["low", "medium", "high"],
        "escalation_rules": [
            {
                "trigger": "external_source_access",
                "risk_class": "medium",
                "required_action": "create_request",
                "reviewer_ref": HUMAN_WORKER_ID,
                "reason": "HumanWorker review gates external source collection.",
            },
        ],
        "created_at": "2026-07-03T09:00:00Z",
        "tool_grants": ["grant:local-context-read"],
        "memory_grants": ["grant:read-confirmed-memory"],
        "request_limits": {
            "max_pending_requests": 3,
            "max_repeated_denials": 1,
            "default_expiry_seconds": 1800,
        },
    }


def base_work_session(*, revision: int, last_event_hash: str, status: str, updated_at: str) -> dict[str, Any]:
    record = {
        "id": WORK_SESSION_ID,
        "protocol_version": PROTOCOL_VERSION,
        "created_by_actor_id": HUMAN_ACTOR_ID,
        "objective": "Show an existing coding agent participating through Jarvis protocol records.",
        "human_worker_id": HUMAN_WORKER_ID,
        "agent_worker_id": AGENT_WORKER_ID,
        "policy_id": POLICY_ID,
        "status": status,
        "revision": revision,
        "last_event_hash": last_event_hash,
        "event_log_ref": f"event-log:{WORK_SESSION_ID}",
        "created_at": "2026-07-03T09:01:00Z",
        "updated_at": updated_at,
        "source_ref": "source:native-coding-agent-proof",
        "context_manifest_ref": "context:coding-task-brief",
        "contribution_ledger_ref": f"ledger:{WORK_SESSION_ID}",
    }
    if status == "completed":
        record["evidence_manifest_ref"] = "evidence-manifest-native-agent-proof"
        record["learning_record_refs"] = ["learning-native-agent-pair"]
    return record


def build_events() -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    event_specs = [
        (
            "event-worksession-created",
            "work_session.created",
            "work_session",
            "created",
            WORK_SESSION_ID,
            HUMAN_ACTOR_ID,
            "2026-07-03T09:01:00Z",
            "WorkSession created with HumanWorker, AgentWorker, objective, and Policy.",
        ),
        (
            "event-policy-denied",
            "policy_decision.recorded",
            "policy_decision",
            "recorded",
            "pd-native-agent-source-denied",
            AGENT_ACTOR_ID,
            "2026-07-03T09:04:00Z",
            "PolicyDecision denied external source collection and required Request.",
        ),
        (
            "event-request-created",
            "request.created",
            "request",
            "created",
            "req-native-agent-source",
            AGENT_ACTOR_ID,
            "2026-07-03T09:05:00Z",
            "AgentWorker created scoped Request for HumanWorker review.",
        ),
        (
            "event-review-approved",
            "review.recorded",
            "review",
            "recorded",
            "review-native-agent-source-approval",
            HUMAN_ACTOR_ID,
            "2026-07-03T09:08:00Z",
            "HumanWorker approved bounded external source collection.",
        ),
        (
            "event-policy-allowed",
            "policy_decision.recorded",
            "policy_decision",
            "recorded",
            "pd-native-agent-source-approved",
            AGENT_ACTOR_ID,
            "2026-07-03T09:08:30Z",
            "PolicyDecision allowed the action inside ApprovalScope.",
        ),
        (
            "event-evidence-captured",
            "evidence.captured",
            "evidence_manifest",
            "evidence_item_captured",
            "evidence-source-summary",
            AGENT_ACTOR_ID,
            "2026-07-03T09:12:00Z",
            "AgentWorker captured evidence for the reviewed answer.",
        ),
        (
            "event-contribution-recorded",
            "contribution.recorded",
            "contribution",
            "recorded",
            "contribution-native-agent-shared-answer",
            HUMAN_ACTOR_ID,
            "2026-07-03T09:16:00Z",
            "Shared contribution recorded for HumanWorker and AgentWorker.",
        ),
        (
            "event-learning-recorded",
            "learning.recorded",
            "learning_record",
            "recorded",
            "learning-native-agent-pair",
            HUMAN_ACTOR_ID,
            "2026-07-03T09:18:00Z",
            "Pair learning recorded from Request and Review resolution.",
        ),
        (
            "event-memory-proposal-created",
            "memory_proposal.created",
            "memory_proposal",
            "created",
            "memory-proposal-native-agent",
            HUMAN_ACTOR_ID,
            "2026-07-03T09:19:00Z",
            "MemoryProposal created for future bounded-source work.",
        ),
        (
            "event-skill-proposal-created",
            "skill_proposal.created",
            "skill_proposal",
            "created",
            "skill-proposal-native-agent",
            HUMAN_ACTOR_ID,
            "2026-07-03T09:20:00Z",
            "SkillProposal created for future bounded-source work.",
        ),
        (
            "event-worksession-completed",
            "work_session.completed",
            "work_session",
            "completed",
            WORK_SESSION_ID,
            HUMAN_ACTOR_ID,
            "2026-07-03T09:25:00Z",
            "WorkSession completed with evidence and governed learning.",
        ),
    ]
    for event_id, event_type, object_type, action, object_id, actor_id, timestamp, summary in event_specs:
        events.append(
            jarvis_protocol.create_next_jarvis_event(
                events=events,
                id=event_id,
                event_type=event_type,
                work_session_id=WORK_SESSION_ID,
                actor_id=actor_id,
                timestamp=timestamp,
                payload={
                    "object_type": object_type,
                    "object_id": object_id,
                    "action": action,
                    "summary": summary,
                },
            )
        )
    return events


def build_collaboration_records(events: list[dict[str, Any]]) -> dict[str, Any]:
    denied_policy_decision = {
        "id": "pd-native-agent-source-denied",
        "work_session_id": WORK_SESSION_ID,
        "actor_id": AGENT_ACTOR_ID,
        "policy_id": POLICY_ID,
        "requested_action": requested_action(),
        "normalized_action_hash": action_hash(),
        "risk_class": "medium",
        "result": "deny",
        "reason": "Policy requires HumanWorker review before external source collection.",
        "created_at": "2026-07-03T09:04:00Z",
        "data_sensitivity": "public",
        "denied_grant_refs": ["grant:external-source-read"],
        "request_id": "req-native-agent-source",
    }
    request_pending = {
        "id": "req-native-agent-source",
        "protocol_version": PROTOCOL_VERSION,
        "work_session_id": WORK_SESSION_ID,
        "requester_actor_id": AGENT_ACTOR_ID,
        "requester_worker_id": AGENT_WORKER_ID,
        "target_human_worker_id": HUMAN_WORKER_ID,
        "policy_decision_id": denied_policy_decision["id"],
        "type": "permission",
        "blocking_scope": "action",
        "reason_code": "policy_denied",
        "reason_summary": "External source access is outside current Policy until HumanWorker review.",
        "requested_action": requested_action(),
        "requested_outcome": "Approve external source collection for this WorkSession only.",
        "risk_class": "medium",
        "human_decision_needed": "Approve, narrow, deny, correct, or take over the blocked action.",
        "options": [
            {
                "id": "option-approve-current-session",
                "label": "Approve current WorkSession scope",
                "effect": "AgentWorker collects the referenced source for this WorkSession only.",
                "risk_class": "medium",
                "scope_ref": "scope:external-source",
            },
            {
                "id": "option-deny",
                "label": "Deny external collection",
                "effect": "AgentWorker continues with existing evidence and records the limitation.",
                "risk_class": "low",
                "scope_ref": "scope:local-worksession",
            },
        ],
        "default_if_no_response": {
            "action": "continue_with_limited_evidence",
            "reason": "The blocked action remains stopped and the WorkSession records an evidence limitation.",
            "limitation_ref": "limitation:external-source-not-reviewed",
        },
        "status": "pending",
        "created_at": "2026-07-03T09:05:00Z",
        "expires_at": "2026-07-03T09:35:00Z",
        "missing_permission_or_context": "Policy grant for external source collection",
        "policy_refs": [POLICY_ID],
        "data_sensitivity": "public",
        "recommended_option": "option-approve-current-session",
    }
    review = {
        "id": "review-native-agent-source-approval",
        "work_session_id": WORK_SESSION_ID,
        "reviewer_actor_id": HUMAN_ACTOR_ID,
        "reviewer_worker_id": HUMAN_WORKER_ID,
        "target_ref": f"request:{request_pending['id']}",
        "decision": "approve",
        "created_at": "2026-07-03T09:08:00Z",
        "comments": "Approved for the referenced source and current WorkSession only.",
        "approval_scope": {
            "request_id": request_pending["id"],
            "review_id": "review-native-agent-source-approval",
            "policy_decision_id": denied_policy_decision["id"],
            "request_revision": 3,
            "request_event_hash": events[2]["event_hash"],
            "normalized_action_hash": action_hash(),
            "approved_action": requested_action(),
            "allowed_scope": {
                "scope_ref": "scope:external-source",
                "grant_refs": ["grant:review-approved-external-source"],
            },
            "denied_scope": {"scope_ref": "scope:all-other-external-sources"},
            "expires_at": "2026-07-03T09:35:00Z",
            "max_uses": 1,
            "applies_to_work_session_id": WORK_SESSION_ID,
            "applies_to_actor_id": AGENT_ACTOR_ID,
        },
    }
    request_approved = {
        **request_pending,
        "status": "approved",
        "resolved_at": review["created_at"],
        "resolved_by_review_id": review["id"],
    }
    allowed_policy_decision = {
        "id": "pd-native-agent-source-approved",
        "work_session_id": WORK_SESSION_ID,
        "actor_id": AGENT_ACTOR_ID,
        "policy_id": POLICY_ID,
        "requested_action": requested_action(),
        "normalized_action_hash": action_hash(),
        "risk_class": "medium",
        "result": "allow",
        "reason": "HumanWorker Review created bounded ApprovalScope for this action.",
        "created_at": "2026-07-03T09:08:30Z",
        "data_sensitivity": "public",
        "selected_grant_refs": ["grant:review-approved-external-source"],
    }
    contribution = {
        "id": "contribution-native-agent-shared-answer",
        "work_session_id": WORK_SESSION_ID,
        "contributor_refs": [
            {
                "worker_id": HUMAN_WORKER_ID,
                "actor_id": HUMAN_ACTOR_ID,
                "contribution_role": "human",
            },
            {
                "worker_id": AGENT_WORKER_ID,
                "actor_id": AGENT_ACTOR_ID,
                "contribution_role": "agent",
            },
        ],
        "contributor_type": "shared",
        "contribution_type": "artifact",
        "event_refs": ["event-evidence-captured", "event-contribution-recorded"],
        "created_at": "2026-07-03T09:16:00Z",
        "artifact_refs": ["artifact:reviewed-agent-output"],
        "review_refs": [review["id"]],
        "evidence_refs": ["evidence-source-summary"],
        "confidence": 0.92,
        "limitations": ["limitation:none-recorded"],
    }
    learning = {
        "id": "learning-native-agent-pair",
        "work_session_id": WORK_SESSION_ID,
        "created_by_actor_id": HUMAN_ACTOR_ID,
        "subject_type": "pair",
        "subject_ref": f"pair:{HUMAN_WORKER_ID}+{AGENT_WORKER_ID}",
        "lesson_type": "bounded_external_source_approval",
        "source_event_refs": [
            "event-request-created",
            "event-review-approved",
            "event-evidence-captured",
        ],
        "review_state": "accepted",
        "scope": "scope:future-source-collection",
        "created_at": "2026-07-03T09:18:00Z",
        "proposed_change": {
            "pattern": "Ask for bounded external source approval before collecting evidence outside local context.",
        },
        "memory_proposal_refs": ["memory-proposal-native-agent"],
        "skill_proposal_refs": ["skill-proposal-native-agent"],
    }
    memory_proposal = {
        "id": "memory-proposal-native-agent",
        "work_session_id": WORK_SESSION_ID,
        "proposed_by_actor_id": HUMAN_ACTOR_ID,
        "proposed_for": "pair",
        "memory_scope": "scope:future-source-collection",
        "memory_type": "collaboration_pattern",
        "content": {
            "pattern": "External source collection requires bounded approval tied to WorkSession, Actor, action hash, expiry, and max uses.",
        },
        "provenance": [
            "event-request-created",
            "event-review-approved",
            learning["id"],
        ],
        "confidence": 0.9,
        "review_required": True,
        "status": "pending_review",
        "created_at": "2026-07-03T09:19:00Z",
        "source_event_refs": ["event-review-approved", "event-learning-recorded"],
        "learning_record_refs": [learning["id"]],
    }
    skill_proposal = {
        "id": "skill-proposal-native-agent",
        "work_session_id": WORK_SESSION_ID,
        "proposed_by_actor_id": HUMAN_ACTOR_ID,
        "proposed_for": "pair",
        "skill_scope": "scope:future-source-collection",
        "skill_name": "bounded_external_source_collection",
        "trigger_conditions": [
            "AgentWorker needs evidence outside local context",
            "Policy denies or requires review for the action",
        ],
        "procedure": [
            "Record PolicyDecision before action acceptance",
            "Create scoped Request with risk, options, and fallback",
            "Wait for Review approval or narrowing",
            "Execute only inside ApprovalScope",
            "Capture evidence refs during work",
        ],
        "review_checks": [
            "Request references blocking PolicyDecision",
            "ApprovalScope binds action hash, WorkSession, Actor, expiry, and max uses",
            "EvidenceManifest excludes host-private fields",
        ],
        "failure_cases": [
            "Request resolves without Review",
            "Evidence appears after the fact",
            "Skill activates without review",
        ],
        "provenance": [
            "event-request-created",
            "event-review-approved",
            "event-evidence-captured",
            learning["id"],
        ],
        "status": "pending_review",
        "created_at": "2026-07-03T09:20:00Z",
        "required_tools": ["tool:source-reader"],
        "source_event_refs": [
            "event-request-created",
            "event-review-approved",
            "event-evidence-captured",
        ],
        "learning_record_refs": [learning["id"]],
    }
    outcome_report = {
        "id": "outcome-report-native-agent",
        "work_session_id": WORK_SESSION_ID,
        "source_ref": f"source:completed-worksession:{WORK_SESSION_ID}",
        "reporter_ref": "reporter:proof-evaluator",
        "accepted_by_actor_id": HUMAN_ACTOR_ID,
        "outcome": "accepted",
        "learning_record_refs": [learning["id"]],
        "received_at": "2026-07-03T09:30:00Z",
        "external_system_ref": "external:evaluation-system",
        "reporter_actor_id": HUMAN_ACTOR_ID,
        "reason": "Post-session feedback confirms the bounded Request and Review loop improved future source collection.",
        "reviewer_feedback_refs": ["feedback:bounded-source-loop-accepted"],
    }
    return {
        "policy_decisions": {
            "external_source_denied": denied_policy_decision,
            "external_source_allowed": allowed_policy_decision,
        },
        "requests": {
            "pending": request_pending,
            "approved": request_approved,
        },
        "reviews": {"approve_source": review},
        "contributions": {"shared_answer": contribution},
        "learning_records": {"pair": learning},
        "memory_proposals": {"source_policy_pattern": memory_proposal},
        "skill_proposals": {"bounded_source_collection": skill_proposal},
        "outcome_reports": {"post_session": outcome_report},
    }


def build_operations(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    def op(**kwargs: Any) -> dict[str, Any]:
        return jarvis_protocol.create_operation_envelope(
            authorization=AUTHORIZATION,
            **kwargs,
        )

    return [
        op(
            operation_id="registerWorker",
            actor_id=REGISTRAR_ACTOR_ID,
            worker_id=HUMAN_WORKER_ID,
            idempotency_key="idem-register-worker-human-proof",
            request_timestamp="2026-07-03T09:00:00Z",
            body_ref="records.workers.human",
        ),
        op(
            operation_id="registerWorker",
            actor_id=REGISTRAR_ACTOR_ID,
            worker_id=AGENT_WORKER_ID,
            idempotency_key="idem-register-worker-agent-proof",
            request_timestamp="2026-07-03T09:00:01Z",
            body_ref="records.workers.agent",
        ),
        op(
            operation_id="registerActor",
            actor_id=REGISTRAR_ACTOR_ID,
            target_actor_id=HUMAN_ACTOR_ID,
            idempotency_key="idem-register-actor-human-proof",
            request_timestamp="2026-07-03T09:00:02Z",
            body_ref="records.actors.human",
        ),
        op(
            operation_id="registerActor",
            actor_id=REGISTRAR_ACTOR_ID,
            target_actor_id=AGENT_ACTOR_ID,
            idempotency_key="idem-register-actor-agent-proof",
            request_timestamp="2026-07-03T09:00:03Z",
            body_ref="records.actors.agent",
        ),
        op(
            operation_id="createWorkSession",
            actor_id=HUMAN_ACTOR_ID,
            work_session_id=WORK_SESSION_ID,
            idempotency_key="idem-create-worksession-proof",
            request_timestamp="2026-07-03T09:01:00Z",
            expected_work_session_revision=0,
            previous_event_hash="hash:protocol-genesis",
            body_ref="records.work_sessions.genesis_request",
        ),
        op(
            operation_id="recordPolicyDecision",
            actor_id=AGENT_ACTOR_ID,
            work_session_id=WORK_SESSION_ID,
            idempotency_key="idem-policy-denied-proof",
            request_timestamp="2026-07-03T09:04:00Z",
            expected_work_session_revision=1,
            previous_event_hash=events[0]["event_hash"],
            body_ref="records.policy_decisions.external_source_denied",
        ),
        op(
            operation_id="createRequest",
            actor_id=AGENT_ACTOR_ID,
            work_session_id=WORK_SESSION_ID,
            idempotency_key="idem-request-source-proof",
            request_timestamp="2026-07-03T09:05:00Z",
            expected_work_session_revision=2,
            previous_event_hash=events[1]["event_hash"],
            body_ref="records.requests.pending",
        ),
        op(
            operation_id="recordReview",
            actor_id=HUMAN_ACTOR_ID,
            work_session_id=WORK_SESSION_ID,
            idempotency_key="idem-review-source-proof",
            request_timestamp="2026-07-03T09:08:00Z",
            expected_work_session_revision=3,
            previous_event_hash=events[2]["event_hash"],
            body_ref="records.reviews.approve_source",
        ),
        op(
            operation_id="recordPolicyDecision",
            actor_id=AGENT_ACTOR_ID,
            work_session_id=WORK_SESSION_ID,
            idempotency_key="idem-policy-allowed-proof",
            request_timestamp="2026-07-03T09:08:30Z",
            expected_work_session_revision=4,
            previous_event_hash=events[3]["event_hash"],
            body_ref="records.policy_decisions.external_source_allowed",
        ),
        op(
            operation_id="appendJarvisEvent",
            actor_id=AGENT_ACTOR_ID,
            work_session_id=WORK_SESSION_ID,
            idempotency_key="idem-evidence-captured-proof",
            request_timestamp="2026-07-03T09:12:00Z",
            expected_work_session_revision=5,
            previous_event_hash=events[4]["event_hash"],
            body_ref="records.jarvis_events.evidence_captured",
        ),
        op(
            operation_id="recordContribution",
            actor_id=HUMAN_ACTOR_ID,
            work_session_id=WORK_SESSION_ID,
            idempotency_key="idem-contribution-proof",
            request_timestamp="2026-07-03T09:16:00Z",
            expected_work_session_revision=6,
            previous_event_hash=events[5]["event_hash"],
            body_ref="records.contributions.shared_answer",
        ),
        op(
            operation_id="createLearningRecord",
            actor_id=HUMAN_ACTOR_ID,
            work_session_id=WORK_SESSION_ID,
            idempotency_key="idem-learning-proof",
            request_timestamp="2026-07-03T09:18:00Z",
            expected_work_session_revision=7,
            previous_event_hash=events[6]["event_hash"],
            body_ref="records.learning_records.pair",
        ),
        op(
            operation_id="createMemoryProposal",
            actor_id=HUMAN_ACTOR_ID,
            work_session_id=WORK_SESSION_ID,
            idempotency_key="idem-memory-proposal-proof",
            request_timestamp="2026-07-03T09:19:00Z",
            expected_work_session_revision=8,
            previous_event_hash=events[7]["event_hash"],
            body_ref="records.memory_proposals.source_policy_pattern",
        ),
        op(
            operation_id="createSkillProposal",
            actor_id=HUMAN_ACTOR_ID,
            work_session_id=WORK_SESSION_ID,
            idempotency_key="idem-skill-proposal-proof",
            request_timestamp="2026-07-03T09:20:00Z",
            expected_work_session_revision=9,
            previous_event_hash=events[8]["event_hash"],
            body_ref="records.skill_proposals.bounded_source_collection",
        ),
        op(
            operation_id="appendJarvisEvent",
            actor_id=HUMAN_ACTOR_ID,
            work_session_id=WORK_SESSION_ID,
            idempotency_key="idem-worksession-completed-proof",
            request_timestamp="2026-07-03T09:25:00Z",
            expected_work_session_revision=10,
            previous_event_hash=events[9]["event_hash"],
            body_ref="records.jarvis_events.worksession_completed",
        ),
        op(
            operation_id="exportEvidenceManifest",
            actor_id=HUMAN_ACTOR_ID,
            work_session_id=WORK_SESSION_ID,
        ),
        op(
            operation_id="submitOutcomeReport",
            actor_id=HUMAN_ACTOR_ID,
            idempotency_key="idem-outcome-report-proof",
            request_timestamp="2026-07-03T09:30:00Z",
            body_ref="records.outcome_reports.post_session",
        ),
    ]


def build_proof() -> dict[str, Any]:
    workers = worker_records()
    actors = actor_records()
    human_worker, agent_worker = participant_records()
    policy = policy_record()
    events = build_events()
    work_sessions = {
        "genesis_request": base_work_session(
            revision=0,
            last_event_hash="hash:protocol-genesis",
            status="active",
            updated_at="2026-07-03T09:01:00Z",
        ),
        "active": base_work_session(
            revision=1,
            last_event_hash=events[0]["event_hash"],
            status="active",
            updated_at="2026-07-03T09:01:00Z",
        ),
        "completed": base_work_session(
            revision=11,
            last_event_hash=events[-1]["event_hash"],
            status="completed",
            updated_at="2026-07-03T09:25:00Z",
        ),
    }
    collaboration_records = build_collaboration_records(events)
    evidence_manifest = jarvis_protocol.create_evidence_manifest(
        id="evidence-manifest-native-agent-proof",
        work_session=work_sessions["completed"],
        generated_by_actor_id=HUMAN_ACTOR_ID,
        generated_at="2026-07-03T09:26:00Z",
        events=events,
        evidence_item_refs=[
            {
                "id": "evidence-source-summary",
                "work_session_id": WORK_SESSION_ID,
                "source_event_refs": ["event-evidence-captured"],
                "captured_by_actor_id": AGENT_ACTOR_ID,
                "evidence_type": "source_summary",
                "artifact_ref": "artifact:source-summary",
                "content_hash": "hash:source-summary",
                "trust_label": "reviewed",
                "redaction_state": "redacted",
                "captured_at": "2026-07-03T09:12:00Z",
                "limitation_refs": ["limitation:none-recorded"],
            },
        ],
        policy_decision_refs=[
            "pd-native-agent-source-denied",
            "pd-native-agent-source-approved",
        ],
        request_refs=["req-native-agent-source"],
        review_refs=["review-native-agent-source-approval"],
        takeover_refs=[],
        contribution_refs=["contribution-native-agent-shared-answer"],
        artifact_refs=["artifact:reviewed-agent-output", "artifact:source-summary"],
        limitation_refs=["limitation:none-recorded"],
        redaction_refs=["redaction:portable-safe"],
        export_profile={
            "profile": "portable_evidence_manifest",
            "version": PROTOCOL_VERSION,
            "redaction_profile_ref": "redaction:portable-safe",
        },
    )
    records = {
        "workers": workers,
        "actors": actors,
        "human_workers": {"primary": human_worker},
        "agent_workers": {"primary": agent_worker},
        "policies": {"bounded": policy},
        "work_sessions": work_sessions,
        "jarvis_events": {
            "worksession_created": events[0],
            "policy_denied": events[1],
            "request_event": events[2],
            "review_approved": events[3],
            "policy_allowed": events[4],
            "evidence_captured": events[5],
            "contribution_recorded": events[6],
            "learning_recorded": events[7],
            "memory_proposal_created": events[8],
            "skill_proposal_created": events[9],
            "worksession_completed": events[10],
        },
        **collaboration_records,
        "evidence_manifests": {"portable_export": evidence_manifest},
    }
    return {
        "proof_id": "native-coding-agent-sdk-helper-proof-v01",
        "fixture_id": "native-coding-agent-sdk-helper-proof-v01",
        "protocol_version": PROTOCOL_VERSION,
        "kind": "valid",
        "expected_result": "accept",
        "title": "Native coding-agent SDK-helper implementation proof",
        "description": (
            "Protocol-record proof that an existing native coding agent "
            "participates in Jarvis through SDK-generated records."
        ),
        "issue_ref": "https://github.com/Flow-Research/jarvis/issues/68",
        "host_shape_ref": "command_line_host_boundary",
        "native_agent_boundary": {
            "agent_ref": "agent:native-coding-agent",
            "execution_owner": "host",
            "jarvis_scope": "protocol_records_only",
            "native_execution_preserved": True,
        },
        "sdk_helper_trace": [
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
        ],
        "source_contract_refs": [
            "docs/examples/existing-agent-compatibility.md",
            "docs/examples/protocol-records.md",
            "docs/conformance/existing-agent-proof-plan.md",
            "docs/conformance/checklist.md",
            "docs/protocol/15-openapi-communication-binding.md",
            "docs/openapi/jarvis-openapi.yaml#/components/schemas/Worker",
            "docs/openapi/jarvis-openapi.yaml#/components/schemas/Actor",
            "docs/openapi/jarvis-openapi.yaml#/components/schemas/HumanWorker",
            "docs/openapi/jarvis-openapi.yaml#/components/schemas/AgentWorker",
            "docs/openapi/jarvis-openapi.yaml#/components/schemas/WorkSession",
            "docs/openapi/jarvis-openapi.yaml#/components/schemas/JarvisEvent",
            "docs/openapi/jarvis-openapi.yaml#/components/schemas/Policy",
            "docs/openapi/jarvis-openapi.yaml#/components/schemas/PolicyDecision",
            "docs/openapi/jarvis-openapi.yaml#/components/schemas/Request",
            "docs/openapi/jarvis-openapi.yaml#/components/schemas/Review",
            "docs/openapi/jarvis-openapi.yaml#/components/schemas/Contribution",
            "docs/openapi/jarvis-openapi.yaml#/components/schemas/EvidenceManifest",
            "docs/openapi/jarvis-openapi.yaml#/components/schemas/LearningRecord",
            "docs/openapi/jarvis-openapi.yaml#/components/schemas/MemoryProposal",
            "docs/openapi/jarvis-openapi.yaml#/components/schemas/SkillProposal",
            "docs/openapi/jarvis-openapi.yaml#/components/schemas/OutcomeReport",
        ],
        "records": records,
        "operations": build_operations(events),
        "assertions": [
            "native agent execution stays outside Jarvis",
            "Jarvis records HumanWorker and AgentWorker collaboration",
            "PolicyDecision precedes accepted AgentWorker state",
            "Request resolves through HumanWorker Review",
            "EvidenceManifest exports from terminal WorkSession state",
            "OutcomeReport enters after WorkSession completion",
            "LearningRecord, MemoryProposal, and SkillProposal carry governed learning forward",
        ],
        "pack_limits": {
            "certifies_implementation": False,
            "claims_production_adoption": False,
            "defines_host_execution": False,
            "defines_runtime_behavior": False,
            "defines_agent_runtime": False,
            "defines_host_ui": False,
            "defines_storage": False,
            "defines_auth": False,
            "defines_model_calls": False,
            "defines_tool_execution": False,
            "defines_billing": False,
            "defines_scoring": False,
            "defines_payment": False,
            "defines_deployment": False,
            "defines_monitoring": False,
            "defines_host_integration": False,
            "defines_host_workflow": False,
            "defines_adapter_code": False,
            "defines_wrapper_code": False,
        },
    }


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"{json.dumps(value, indent=2, ensure_ascii=False)}\n",
        encoding="utf-8",
    )


def main() -> int:
    write_json(PROOF_PATH, build_proof())
    print(f"wrote {PROOF_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
