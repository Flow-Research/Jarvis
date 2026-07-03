# jarvis-protocol

Status: Protocol Alpha helper tooling.

This package provides Python helpers for Jarvis v0.1 protocol records. It
implements the protocol-helper surface for compatible implementations that need
OpenAPI-derived models, validation helpers, event hashing, EvidenceManifest
checks, and conformance fixture checks.

Accepted surfaces:

- protocol models generated from the OpenAPI contract
- protocol record validators
- mutation-header helpers
- read-header helpers
- event envelope helpers
- event hash-chain helpers
- EvidenceManifest helpers
- Request, Review, and Takeover validators
- LearningRecord, MemoryProposal, and SkillProposal validators
- protocol error helpers
- example record mappers

Rejected surfaces:

- agent runtime
- model router
- tool executor
- host adapter
- wrapper
- UI kit
- auth provider
- storage backend
- memory engine
- sandbox
- billing system
- scoring system
- payment system
- deployment system
- host workflow engine

## Public Surface

The package root exports:

- generated OpenAPI schema metadata
- generated `TypedDict` and `Literal` model names under
  `jarvis_protocol.generated.openapi_types`
- `protocol_error`
- `create_read_headers`
- `create_mutation_headers`
- `create_non_work_session_mutation_headers`
- `create_work_session_mutation_headers`
- `get_operation_binding`
- `create_operation_path`
- `create_operation_envelope`
- `create_jarvis_event`
- `create_next_jarvis_event`
- `create_evidence_manifest`
- `validate_mutation_headers`
- `validate_read_headers`
- `validate_operation_headers`
- `validate_protocol_record`
- `validate_fixture`
- `validate_event_hash_chain`
- `canonicalize_protocol_value`
- `hash_protocol_value`
- `find_forbidden_host_private_field`

## Protocol Helper Flow

```python
from jarvis_protocol import (
    create_evidence_manifest,
    create_next_jarvis_event,
    create_operation_envelope,
    create_work_session_mutation_headers,
    validate_event_hash_chain,
)

headers = create_work_session_mutation_headers(
    actor_id="actor-human-1",
    authorization="HostAuth caller",
    idempotency_key="idem-1",
    request_timestamp="2026-06-16T10:00:00Z",
    expected_work_session_revision=0,
    previous_event_hash="hash:protocol-genesis",
)

operation = create_operation_envelope(
    operation_id="appendJarvisEvent",
    actor_id="actor-human-1",
    headers=headers,
    work_session_id="ws-1",
    body_ref="records.jarvis_events.created",
)

event = create_next_jarvis_event(
    id="event-created",
    event_type="work_session.created",
    work_session_id="ws-1",
    actor_id="actor-human-1",
    timestamp="2026-06-16T10:00:00Z",
    payload={
        "object_type": "work_session",
        "object_id": "ws-1",
        "action": "created",
    },
)

validate_event_hash_chain([event])

create_evidence_manifest(
    id="evidence-1",
    work_session={
        "id": "ws-1",
        "objective": "Create a governed protocol record.",
        "status": "completed",
        "last_event_hash": event["event_hash"],
    },
    events=[event],
    generated_by_actor_id="actor-human-1",
    generated_at="2026-06-16T10:01:00Z",
    evidence_item_refs=[
        {
            "id": "evidence-item-1",
            "work_session_id": "ws-1",
            "source_event_refs": ["event-created"],
            "captured_by_actor_id": "actor-human-1",
            "evidence_type": "artifact",
            "artifact_ref": "artifact:created-work",
            "content_hash": "hash:created-work",
            "trust_label": "verified",
            "redaction_state": "none",
            "captured_at": "2026-06-16T10:01:00Z",
            "limitation_refs": [],
        }
    ],
)
```

These helpers create protocol records and operation envelopes only. Hosts own
transport, auth, storage, execution, and workflow.

## Local Validation

Run Python package tests from the repository root:

```bash
npm run test:python
```

The package tests load the v0.1 fixture snapshots under `fixtures/v0.1` and
verify that the Python validators accept the golden path and reject every
invalid fixture with the expected protocol error id. The test command also
builds the wheel and sdist, installs the wheel into a temporary target, and
verifies importable package resources through `importlib.resources`.
