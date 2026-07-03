# @jarvis-protocol/sdk

Status: Protocol Alpha helper package.

This package provides TypeScript helpers for Jarvis v0.1 protocol records.

Accepted surfaces:

- generated OpenAPI component types
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

## Public Helpers

The package exports:

- OpenAPI-derived TypeScript declarations for every v0.1 component schema
- `createReadHeaders`
- `createMutationHeaders`
- `createNonWorkSessionMutationHeaders`
- `createWorkSessionMutationHeaders`
- `getOperationBinding`
- `createOperationPath`
- `createOperationEnvelope`
- `createJarvisEvent`
- `createNextJarvisEvent`
- `createEvidenceManifest`
- `validateMutationHeaders`
- `validateReadHeaders`
- `validateProtocolRecord`
- `validateRequest`
- `validateReview`
- `validateTakeover`
- `validateContribution`
- `validateEvidenceManifest`
- `validateLearningRecord`
- `validateMemoryProposal`
- `validateSkillProposal`
- `validateOutcomeReport`
- `validateFixture`
- `validateEventHashChain`
- `canonicalizeProtocolValue`
- `hashProtocolValue`
- `protocolError`

The package also exports `./package.json` and `./fixtures/v0.1/*` subpaths so
compatible implementations can read package metadata and v0.1 fixture snapshots
from the installed package.

## Protocol Helper Flow

```js
import {
  createEvidenceManifest,
  createNextJarvisEvent,
  createOperationEnvelope,
  createWorkSessionMutationHeaders,
  validateEventHashChain,
} from "@jarvis-protocol/sdk";

const headers = createWorkSessionMutationHeaders({
  actorId: "actor-human-1",
  authorization: "HostAuth caller",
  idempotencyKey: "idem-1",
  requestTimestamp: "2026-06-16T10:00:00Z",
  expectedWorkSessionRevision: 0,
  previousEventHash: "hash:protocol-genesis",
});

const operation = createOperationEnvelope({
  operationId: "appendJarvisEvent",
  actorId: "actor-human-1",
  headers,
  workSessionId: "ws-1",
  bodyRef: "records.jarvis_events.created",
});

const event = createNextJarvisEvent({
  id: "event-created",
  type: "work_session.created",
  workSessionId: "ws-1",
  actorId: "actor-human-1",
  timestamp: "2026-06-16T10:00:00Z",
  payload: {
    object_type: "work_session",
    object_id: "ws-1",
    action: "created",
  },
});

validateEventHashChain([event]);

createEvidenceManifest({
  id: "evidence-1",
  workSession: {
    id: "ws-1",
    objective: "Create a governed protocol record.",
    status: "completed",
    last_event_hash: event.event_hash,
  },
  events: [event],
  generatedByActorId: "actor-human-1",
  generatedAt: "2026-06-16T10:01:00Z",
  evidenceItemRefs: [
    {
      id: "evidence-item-1",
      work_session_id: "ws-1",
      source_event_refs: ["event-created"],
      captured_by_actor_id: "actor-human-1",
      evidence_type: "artifact",
      artifact_ref: "artifact:created-work",
      content_hash: "hash:created-work",
      trust_label: "verified",
      redaction_state: "none",
      captured_at: "2026-06-16T10:01:00Z",
      limitation_refs: [],
    },
  ],
});
```

These helpers create protocol records and operation envelopes only. Hosts own
transport, auth, storage, execution, and workflow.

## Local Checks

Run:

```sh
npm --workspace @jarvis-protocol/sdk test
python3 scripts/check_sdk_boundary.py
```

`validateFixture` checks the v0.1 fixture snapshots shipped with this package.
The package rejects invalid protocol records with OpenAPI `ProtocolError`
envelopes.
