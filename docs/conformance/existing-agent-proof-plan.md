# Existing-Agent Compatibility Proof Plan

Jarvis v0.1 compatibility proof shows that existing human-agent work maps into
Jarvis protocol records without replacing the native host.

Jarvis records the collaboration contract. Hosts own native execution.

## Boundary

This proof plan defines protocol mapping only.

It does not define adapter code, wrapper code, integration code, runtime
behavior, UI, storage, authentication backend, model calls, tool execution,
billing, scoring, payment, deployment behavior, or host-specific workflow.

Compatible implementations MUST preserve host-owned execution and record only
Jarvis protocol state.

A Jarvis SDK, when used, acts only as a protocol implementation kit. It helps
the host create, validate, export, and test Jarvis records. It does not run the
agent, replace the native agent, orchestrate models, execute tools, own memory,
provide UI, manage auth, store records, or become the host adapter.

The proof rejects compatibility claims that require rewriting an existing agent
as a Jarvis-owned agent.

## Proof Inputs

Existing-agent compatibility proof starts from these protocol records:

```txt
Worker
Actor
HumanWorker
AgentWorker
WorkSession
JarvisEvent
Policy
PolicyDecision
Request
Review
Takeover
Contribution
EvidenceManifest
LearningRecord
MemoryProposal
SkillProposal
OutcomeReport
```

Proof uses these allowed `host_shape_ref` values:

```txt
command_line_host_boundary
local_execution_host_boundary
hosted_execution_host_boundary
tool_use_protocol_boundary
```

`host_shape_ref` is fixture metadata only. It MUST NOT appear inside protocol
records, operation bodies, JarvisEvents, EvidenceManifest records, or portable
export payloads.

## Required Compatibility Claim

A public compatibility claim for this proof MUST use this format:

```txt
Implementation: <name> <implementation-version>
Protocol compatibility: Jarvis v0.1
Conformance surface: existing-agent proof plan, public conformance checklist,
and v0.1 golden-path and failure-mode fixtures
Verification date: <verification-date>
Verifier: <verifier-or-self-attested-status>
Evidence: <evidence-ref>
```

The proof behind that claim is:

```txt
Different native host shapes produce equivalent Jarvis records for the same
human-agent collaboration loop.
```

Equivalent Jarvis records preserve:

```txt
same object sequence and lifecycle state transitions
same HumanWorker role
same AgentWorker role
same WorkSession objective
same Policy boundary
same PolicyDecision before accepted AgentWorker state
same normalized_action_hash binding across affected records
same Request for blocked scope
same Review or Takeover resolution
same Contribution attribution
same EvidenceManifest proof
same LearningRecord and governed MemoryProposal or SkillProposal loop when
  learning changes future work
same forbidden host-private export boundary
```

Host-owned runtime details are outside compatibility comparison.

## Proof Pair

The compatibility proof locks this v0.1 proof pair:

```txt
command_line_host_boundary
local_execution_host_boundary
```

Both host shapes MUST map the same collaboration loop into equivalent Jarvis
records.

The command-line host shape represents a native boundary where the human and
agent coordinate through a command-line interaction.

The local execution host shape represents a native boundary where the human and
agent coordinate through a local workspace or local process.

Both shapes produce the same protocol proof. The native interface does not
change the Jarvis record.

## Proof Cases

The proof pair MUST cover Review resolution and Takeover resolution.

Jarvis publishes protocol-record evidence packs for both paths:

```txt
docs/examples/evidence-packs/existing-agent-review
docs/examples/evidence-packs/existing-agent-takeover
```

These packs prove record compatibility only. They do not certify an
implementation, define adapter code, define wrapper code, or move host-owned
execution into Jarvis.

### Review Resolution Equivalence

Review resolution proof MUST map this sequence for both host shapes:

```txt
1. Register Worker records.
2. Register Actor records.
3. Represent the human as HumanWorker.
4. Represent the agent as AgentWorker.
5. Create WorkSession with Policy, revision, and event hash state.
6. AgentWorker attempts denied or review-required work.
7. Record PolicyDecision before accepted protocol state.
8. Create scoped Request.
9. HumanWorker resolves Request through Review.
10. Review approve or narrow creates bounded ApprovalScope.
11. AgentWorker resumes only inside ApprovalScope.
12. Record Contribution.
13. Capture EvidenceItemRef records from source events.
14. Export EvidenceManifest.
15. Record LearningRecord when the session changes future work.
16. Record MemoryProposal or SkillProposal when learning changes future work.
```

The Review proof MUST preserve `resolved_by_review_id` on the resolved Request
and MUST bind ApprovalScope to request, review, PolicyDecision,
request_revision, request_event_hash, `normalized_action_hash`,
approved_action, allowed_scope, denied_scope, Actor, WorkSession, expiry, and
max uses.

### Takeover Resolution Equivalence

Takeover resolution proof MUST map this sequence for both host shapes:

```txt
1. AgentWorker reaches blocked scope.
2. Record PolicyDecision before accepted protocol state.
3. Create scoped Request.
4. HumanWorker resolves Request through Takeover.
5. Takeover records lock_epoch.
6. Stale AgentWorker continuation rejects.
7. Resume requires reconciliation_refs.
8. Record human, agent, or shared Contribution.
9. Capture EvidenceItemRef records from source events.
10. Export EvidenceManifest.
```

The Takeover proof MUST preserve `resolved_by_takeover_id` on the resolved
Request, reject stale `lock_epoch` continuation, and require
`reconciliation_refs` before AgentWorker continuation resumes. It MUST bind
Takeover.request_id to the resolved Request and bind affected_scope to
blocking_scope, scope_ref, and `normalized_action_hash`.

## Universal Collaboration Loop

The proof pair uses this loop:

```txt
1. HumanWorker defines the work objective.
2. Host registers Worker and Actor records.
3. Host represents the human as HumanWorker.
4. Host represents the agent as AgentWorker.
5. Host starts a WorkSession with Policy.
6. AgentWorker attempts work that affects WorkSession state.
7. PolicyDecision records the policy result before accepted protocol state.
8. Allowed action records JarvisEvent.
9. Denied, blocked, or review-required action creates Request.
10. HumanWorker resolves the Request through Review or Takeover.
11. Work resumes inside approved or narrowed scope.
12. Contribution records who performed the work.
13. EvidenceManifest records portable proof from source events.
14. LearningRecord captures human, agent, or pair learning.
15. MemoryProposal or SkillProposal records governed future-work change.
16. OutcomeReport records post-session feedback without mutating sealed records.
```

The proof rejects any later record that backfills a missing PolicyDecision,
Request resolution, Contribution actor, evidence event ref, or governed
learning review.

## Equivalence Matrix

| Native surface | Command-line host proof | Local execution host proof | Required Jarvis equivalence |
| --- | --- | --- | --- |
| human participant | maps to Worker, HumanWorker, Actor | maps to Worker, HumanWorker, Actor | same human protocol role and authority |
| agent participant | maps to Worker, AgentWorker, Actor | maps to Worker, AgentWorker, Actor | same agent protocol role and authority |
| work objective | maps to WorkSession.objective | maps to WorkSession.objective | same WorkSession.objective |
| policy boundary | maps to Policy | maps to Policy | same allowed, denied, review-required, and request-limit rules |
| agent action | maps to PolicyDecision and JarvisEvent | maps to PolicyDecision and JarvisEvent | PolicyDecision exists before accepted state |
| blocked scope | maps to Request | maps to Request | same Request type, blocking_scope, reason, risk, options, fallback, expiry |
| human judgment | maps to Review or Takeover | maps to Review or Takeover | same resolution authority and target refs |
| narrowed authority | maps to ApprovalScope | maps to ApprovalScope | same bounded action, scope, expiry, max uses, Actor, and WorkSession |
| performed work | maps to Contribution | maps to Contribution | same contributor refs and contribution type |
| artifacts and sources | maps to EvidenceManifest evidence refs | maps to EvidenceManifest evidence refs | source_event_refs exist and export excludes host-private fields |
| confirmed improvement | maps to LearningRecord, MemoryProposal, or SkillProposal | maps to LearningRecord, MemoryProposal, or SkillProposal | learning subject is human, agent, or pair and future-work change stays governed |
| unsupported native concept | maps to limitations or rejects as unsupported_capability | maps to limitations or rejects as unsupported_capability | missing native proof never weakens required protocol gates |

## Normalized Record Graph

Compatibility compares the normalized Jarvis record graph.

It does not compare native host behavior.

Equivalent record graphs MUST preserve:

```txt
object sequence
lifecycle state transitions
WorkSession revision state
WorkSession event hash state
JarvisEvent chain
PolicyDecision before accepted AgentWorker state
normalized_action_hash across PolicyDecision, Request, Review, ApprovalScope,
  Contribution, and evidence refs
Request type, blocking_scope, risk_class, status, and resolver refs
resolved_by_review_id or resolved_by_takeover_id
ApprovalScope bounds for approve or narrow Review decisions
Takeover lock_epoch and reconciliation_refs when Takeover resolves the Request
contributor refs through valid Worker and Actor records
EvidenceManifest refs, event_chain_root, limitations, and export_profile
LearningRecord, MemoryProposal, and SkillProposal review state
```

## Host-Private Exclusion

The proof MUST exclude these host-owned fields from portable records:

```txt
credentials
secrets
raw runtime state
host-only database ids
deployment details
billing data
private scores
UI state
raw auth tokens
provider secrets
provider keys
session cookies
private keys
```

Host-private fields remain outside Worker, Actor, HumanWorker, AgentWorker,
WorkSession, Policy, JarvisEvent, PolicyDecision, Request, Review, Takeover,
Contribution, EvidenceManifest, LearningRecord, MemoryProposal, SkillProposal,
and OutcomeReport records.

## Zero-Trust Gates

Every WorkSession-scoped mutation in the proof MUST require the `HostAuth`
security scheme and these Jarvis protocol headers:

```txt
Jarvis-Protocol-Version
Jarvis-Actor-Id
Jarvis-Idempotency-Key
Jarvis-Request-Timestamp
Jarvis-Expected-WorkSession-Revision
Jarvis-Previous-Event-Hash
```

The genesis WorkSession mutation MUST set `Jarvis-Expected-WorkSession-Revision`
to `0` and `Jarvis-Previous-Event-Hash` to the protocol genesis hash.

Every non-WorkSession protocol mutation in the proof MUST require the
`HostAuth` security scheme and these Jarvis protocol headers:

```txt
Jarvis-Protocol-Version
Jarvis-Actor-Id
Jarvis-Idempotency-Key
Jarvis-Request-Timestamp
```

Worker registration, Actor registration, and OutcomeReport submission are
non-WorkSession protocol mutations. They MUST NOT use fake WorkSession revision
or previous event hash values.

WorkSession-scoped reads and export reads MUST require the `HostAuth` security
scheme and these Jarvis protocol headers:

```txt
Jarvis-Protocol-Version
Jarvis-Actor-Id
```

WorkSession-scoped reads and export reads MUST NOT require mutation-only
idempotency, expected revision, or previous event hash headers.

Every accepted WorkSession-scoped state change MUST:

```txt
record the Actor
verify Actor authority
validate Jarvis-Expected-WorkSession-Revision
validate Jarvis-Previous-Event-Hash
append or reference the resulting JarvisEvent
advance WorkSession revision and event hash state
```

## Evidence And Learning Gates

Evidence proof MUST include:

```txt
event_chain_root
evidence item refs
source_event_refs
PolicyDecision refs
Request refs
Review refs
Takeover refs when takeover happens
Contribution refs
limitations
export_profile
terminal export state
```

Evidence proof MUST come from source events captured during the WorkSession.
The protocol rejects evidence reconstructed without source event refs.

Learning proof MUST include:

```txt
LearningRecord subject_type as human, agent, or pair
source_event_refs
review_state
scope
MemoryProposal when durable memory changes future work
SkillProposal when reusable procedure changes future work
```

MemoryProposal and SkillProposal MUST stay proposed until governed review
accepts them.

## Rejection Gates

The existing-agent proof MUST reject these compatibility failures:

```txt
missing_protocol_version
unsupported_protocol_version
missing_actor
unauthorized_actor
missing_idempotency_key
duplicate_idempotency_key_mismatch
missing_request_timestamp
stale_request_timestamp
missing_expected_work_session_revision
missing_previous_event_hash
missing_objective
missing_policy
missing_policy_decision
request_unresolved
missing_review_resolution
missing_takeover_resolution
invalid_approval_scope
stale_work_session_revision
invalid_previous_event_hash
invalid_event_hash
stale_takeover_epoch
missing_reconciliation_refs
invalid_evidence_export_state
sealed_work_session_mutation
sealed_evidence_mutation
missing_contribution_actor
invalid_contributor_refs
shared_contribution_without_individual_refs
duplicate_contributor_ref
evidence_after_the_fact
missing_evidence_event_refs
duplicate_evidence_item_ref
forbidden_host_private_field
silent_memory_mutation
silent_skill_activation
outcome_report_without_learning_record
unsupported_capability
```

Unsupported native concepts MUST record `limitations` or reject as
`unsupported_capability`. They MUST NOT remove required PolicyDecision,
Request, Review, Takeover, Contribution, EvidenceManifest, or LearningRecord
gates.

## Compatible Examples Entry Gate

Compatible examples MUST start from this proof plan and the conformance
fixtures.

Compatible examples MUST NOT start from adapter behavior, host runtime behavior,
UI behavior, model behavior, tool execution, storage behavior, authentication
backend behavior, billing, scoring, payment, or deployment behavior.

Before a compatible example starts, the example MUST identify:

```txt
host_shape_ref
WorkSession objective
HumanWorker mapping
AgentWorker mapping
Policy mapping
Request/Review/Takeover mapping
Contribution mapping
EvidenceManifest mapping
LearningRecord mapping
unsupported native concepts
forbidden host-private fields
required rejection gates
```

## Compatibility Conditions

Existing-agent compatibility proof requires:

- two allowed host shapes map the same collaboration loop into equivalent
  Jarvis records
- host-owned execution stays outside portable protocol records
- the proof preserves zero-trust mutation headers and event hash linkage
- the proof preserves PolicyDecision before accepted AgentWorker state
- blocked or review-required scope creates Request
- Request resolves only through Review or Takeover
- Contribution preserves actor attribution
- EvidenceManifest exports portable proof without host-private fields
- LearningRecord captures human, agent, or pair learning
- MemoryProposal and SkillProposal stay governed until review
- unsupported native concepts record `limitations` or reject as
  `unsupported_capability`
- compatible examples remain behind the conformance gate
