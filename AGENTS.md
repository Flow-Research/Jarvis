# AGENTS.md

This repo is for Jarvis.

Jarvis is the human-agent collaboration and learning-loop protocol.

Jarvis defines how HumanWorkers and AgentWorkers coordinate inside
WorkSessions under shared goals and human-defined policy, create Requests when
blocked, capture Reviews and Takeovers from human judgment, record attributable
Contributions, export portable EvidenceManifest records, and carry governed
LearningRecords, MemoryProposals, and SkillProposals into future work.

This thesis is the source of truth for every agent, contributor, and maintainer
working in this repository.

## Non-Negotiable Boundary

Jarvis is a protocol.

Jarvis defines portable contracts for governed collaboration between
HumanWorkers and AgentWorkers.

Jarvis does not own host implementation.

Hosts implement Jarvis. Hosts own execution, storage, identity, UI, deployment,
runtime behavior, model calls, tool execution, billing, monitoring, and
host-specific workflow.

## What Jarvis Owns

Jarvis owns the protocol contracts for:

- Worker
- Actor
- HumanWorker
- AgentWorker
- WorkSession
- JarvisEvent
- Policy
- PolicyDecision
- Request
- Review
- Takeover
- Contribution
- EvidenceManifest
- LearningRecord
- MemoryProposal
- SkillProposal
- OutcomeReport
- protocol event envelope
- portable export format
- OpenAPI 3.1 communication binding
- version negotiation
- capability negotiation
- extension rules
- protocol errors
- conformance expectations

## What Hosts Own

Hosts own implementation details:

- UI
- identity provider
- authentication
- authorization backend
- storage
- queues
- cloud provider
- local execution
- isolation mechanism
- model provider
- tool execution
- billing
- deployment
- monitoring
- host-specific workflow

A host implements Jarvis. A host is not Jarvis.

## The Decision Test

Every change must pass this test:

```txt
Does this define how a human and an agent collaborate, request help, review
work, take over, record contribution, produce evidence, or learn together?
```

If yes, the change belongs in Jarvis.

If the change defines host execution, UI, auth, storage, billing, cloud,
runtime, model calls, or host workflow, it belongs outside Jarvis.

## Core Thesis

The valuable unit is the human-agent team.

Not the human alone.
Not the agent alone.
Not the model.
Not the runtime.
Not the host.

The HumanWorker improves.
The AgentWorker improves.
The pair improves.
The next WorkSession carries confirmed learning forward.

## Protocol Shape

Jarvis v0.1 has four protocol layers and one explicit outside-Jarvis boundary:

```txt
Layer 1: Protocol semantics
  HumanWorker + AgentWorker collaboration and learning loop

Layer 2: Protocol objects
  Worker, Actor, HumanWorker, AgentWorker, WorkSession, JarvisEvent,
  Policy, PolicyDecision, Request, Review, Takeover, Contribution,
  EvidenceManifest, LearningRecord, MemoryProposal, SkillProposal,
  OutcomeReport

Layer 3: Protocol operations
  register Worker, register Actor, create WorkSession, read WorkSession,
  append event, record PolicyDecision, create Request, record Review,
  record Takeover, record Contribution, create LearningRecord,
  create MemoryProposal, create SkillProposal, export EvidenceManifest,
  submit OutcomeReport

Layer 4: OpenAPI 3.1 communication binding
  HTTP paths, operations, parameters, request bodies, response bodies,
  component schemas, security scheme, header parameters, errors, examples

Outside Jarvis: Host implementation
  UI, auth, storage, execution, deployment, model calls, and tool execution
```

OpenAPI 3.1 is the primary machine-readable communication contract. Separate
schema-file packages are not the primary contract.

## SDK Boundary

A Jarvis SDK is a protocol implementation kit.

A Jarvis SDK provides protocol helpers for compatible implementations to create,
validate, sign, hash, export, and test Jarvis protocol records.

A Jarvis SDK does not run agents. A Jarvis SDK does not orchestrate models. A
Jarvis SDK does not execute tools. A Jarvis SDK does not own memory engines,
planning loops, UI, auth, storage, sandboxing, queues, billing, deployment, or
host workflow.

Jarvis SDK work is accepted only when it strengthens protocol implementation:

- generated OpenAPI clients
- protocol types
- event envelope helpers
- event hash-chain helpers
- idempotency helpers
- mutation-header helpers
- EvidenceManifest helpers
- Request, Review, and Takeover validators
- conformance fixture runners
- protocol error helpers
- example record mappers

Jarvis SDK work is rejected when it becomes an agent framework, runtime,
planner, model router, tool executor, memory engine, host adapter, wrapper, UI
kit, auth provider, storage backend, sandbox, or workflow engine.

The protocol compatibility test is strict: an existing agent participates in
Jarvis through protocol records without being rewritten as a Jarvis agent.

## Zero-Trust Requirement

Jarvis starts from zero trust.

Every WorkSession-scoped mutating operation requires:

```txt
Jarvis-Protocol-Version
Jarvis-Actor-Id
Jarvis-Idempotency-Key
Jarvis-Request-Timestamp
Jarvis-Expected-WorkSession-Revision
Jarvis-Previous-Event-Hash
```

Every non-WorkSession protocol mutation requires:

```txt
Jarvis-Protocol-Version
Jarvis-Actor-Id
Jarvis-Idempotency-Key
Jarvis-Request-Timestamp
```

Worker registration, Actor registration, and OutcomeReport submission are
non-WorkSession protocol mutations. They verify Actor authority, idempotency,
protocol version, and timestamp. They do not require fake WorkSession revision
or previous event hash values.

Every accepted WorkSession-scoped state change records the Actor, verifies
authority, checks the current WorkSession revision, and links to the previous
event hash.

Every AgentWorker action that affects a WorkSession records a PolicyDecision
before the action is accepted as protocol state.

Every export excludes host-private fields, credentials, secrets, raw runtime
state, host-only database ids, deployment details, billing data, private scores,
UI state, raw auth tokens, provider secrets, session cookies, and private keys.

## Protocol Drift Guard

Every contributor must hold the protocol boundary.

Jarvis records the collaboration contract. Hosts provide the implementation.

When a proposed change adds host execution, UI, auth, storage, billing, model
calls, isolation behavior, host workflow, scoring, or payment mechanics,
move it outside Jarvis. Keep only the protocol record, lifecycle rule, security
rule, error rule, or conformance rule that protects human-agent collaboration
and shared learning.

## Current Execution Focus

The active focus is post-v0.1 SDK helper tooling planning and public docs site
work.

Protocol lock is complete. Week 2 OpenAPI contract and conformance entry work
is complete. Week 3 protocol compatibility mapping and conformance fixtures
are complete. Week 4 compatible examples and public story are complete.
The v0.1 acceptance review is complete. Jarvis v0.1.0 is released as Protocol
Alpha.

The release does not certify Jarvis or any implementation, designate an
official host, claim production adoption, establish foundation governance, or
create long-term support.

Work on:

- next-phase protocol specification
- post-v0.1 SDK helper tooling plan
- SDK helper boundary and package plan
- TypeScript protocol types and validators
- Python protocol types and validators
- conformance runner and protocol helper CLI
- additional conformance evidence only when it preserves the protocol boundary

The v0.1 acceptance review record starts from
[docs/planning/v0.1-acceptance-review/README.md](./docs/planning/v0.1-acceptance-review/README.md)
and
[docs/planning/v0.1-acceptance-review/acceptance-spec.md](./docs/planning/v0.1-acceptance-review/acceptance-spec.md).

The post-v0.1 SDK helper tooling plan starts from
[docs/planning/post-v0.1-sdk-helper-tooling/README.md](./docs/planning/post-v0.1-sdk-helper-tooling/README.md).

Do not build host implementations in this repo.
Do not build runtime features in this repo.
Do not add or own adapters, wrappers, host behavior, or integration code in this
repo.
Do not add host-specific assumptions to protocol records.
Do not reopen locked protocol decisions unless a concrete contradiction blocks
v0.1.0 release integrity or next-phase specification.

## Wording Rules

Use direct protocol language.

Write:

```txt
Jarvis defines...
Jarvis owns...
Hosts own...
Compatible implementations MUST...
The protocol rejects...
```

Soft protocol wording is a defect.

Do not write protocol rules with soft modal verbs, speculative phrases,
advisory phrases, or generic implementation-concern phrasing. The wording
guard in [scripts/check_protocol_wording.py](./scripts/check_protocol_wording.py)
rejects the blocked terms.

Use direct ownership and state language instead:

```txt
Hosts own storage, streaming, execution, auth, deployment, and UI.
Jarvis records governed learning when protocol behavior changes future work.
Review resolves a Request when human judgment resolves the blocked scope.
Takeover resolves a Request when the human assumes direct control.
The protocol rejects missing or invalid required state.
```

Every PR MUST run the wording guard before push. Every CodeRabbit wording
comment MUST be checked and fixed when valid before the PR is treated as done.

Do not write this repo as a third-party review of Jarvis. Write it as the
source of truth for Jarvis.

## Local Check Commands

Every protocol PR MUST run:

```txt
python3 scripts/check_conformance_fixtures.py
python3 scripts/check_openapi_contract.py
python3 scripts/check_markdown_links.py
python3 scripts/check_docs_site.py
python3 scripts/check_example_evidence_packs.py
python3 scripts/check_protocol_wording.py
python3 scripts/check_sdk_boundary.py
git diff --check
```

Fixture changes MUST run `python3 scripts/check_conformance_fixtures.py`.

Example evidence pack changes MUST run
`python3 scripts/check_example_evidence_packs.py`.

SDK boundary, package, helper, and fixture-snapshot changes MUST still treat
`python3 scripts/check_sdk_boundary.py` as a blocking gate.

TypeScript helper changes MUST run
`npm --workspace @jarvis-protocol/sdk test`.

Python helper changes MUST run `npm run test:python`.

CLI helper changes MUST run `npm run test:cli`.

## Required References

Before changing protocol direction, read:

- [README.md](./README.md)
- [docs/protocol/14-protocol-lock.md](./docs/protocol/14-protocol-lock.md)
- [docs/protocol/15-openapi-communication-binding.md](./docs/protocol/15-openapi-communication-binding.md)
- [docs/protocol/11-core-protocol-objects.md](./docs/protocol/11-core-protocol-objects.md)
- [docs/protocol/12-request-protocol.md](./docs/protocol/12-request-protocol.md)
- [docs/protocol/13-contribution-evidence-learning.md](./docs/protocol/13-contribution-evidence-learning.md)
- [docs/protocol/16-positioning-adoption-lock.md](./docs/protocol/16-positioning-adoption-lock.md)
- [docs/planning/12-30-day-roadmap.md](./docs/planning/12-30-day-roadmap.md)

## Change Discipline

Keep changes scoped.

Do not rename core objects without updating every protocol doc and roadmap
reference.

Do not add a new protocol object until its reason to exist is clear.

Do not add host-private fields to portable protocol records.

Do not weaken the boundary between Jarvis and host implementation.

Do not describe Jarvis as a harness, runtime, framework, or host
implementation.

Jarvis is the protocol for governed human-agent collaboration and shared
learning.
