# Public Conformance Checklist

This checklist defines what a Jarvis v0.1 compatible implementation proves.

Jarvis conformance proves protocol behavior. It does not certify host runtime,
UI, storage, auth backend, model calls, tool execution, billing, scoring,
payment, deployment, adapters, wrappers, or SDK implementation.

Compatible implementations preserve host-owned execution and record the Jarvis
human-agent collaboration and learning loop around it.

## How To Use This Checklist

Use this checklist in three passes:

```txt
1. Prove the golden path.
2. Prove every fixture-backed rejection gate.
3. Prove unsupported or non-fixture-backed protocol errors without claiming
   fixture coverage.
```

The machine-readable fixture entry is:

- [fixtures/README.md](./fixtures/README.md)

The current valid fixtures are:

- [valid/golden-path.json](./fixtures/valid/golden-path.json)
- [valid/takeover-path.json](./fixtures/valid/takeover-path.json)

The current invalid fixtures are listed in the fixture-backed rejection table
below.

## Compatibility Boundary

Compatible implementations MUST preserve these boundaries:

- Jarvis records protocol state.
- Hosts own native execution.
- Jarvis records HumanWorker and AgentWorker collaboration.
- Hosts own UI, auth, storage, model calls, tool execution, runtime behavior,
  deployment, billing, scoring, payment, adapters, wrappers, and workflow
  implementation.
- Portable protocol records MUST NOT contain credentials, secrets, host-only
  database ids, raw runtime state, deployment details, billing data, private
  scores, UI state, raw auth tokens, provider secrets, session cookies, or
  private keys.

## Golden-Path Proof

A compatible implementation MUST prove the golden path.

Fixture:

- [golden-path.json](./fixtures/valid/golden-path.json)

Golden-path conformance proves:

- HumanWorker and AgentWorker are represented by Worker records.
- HumanWorker and AgentWorker are represented by Actor records.
- WorkSession records objective, Policy, revision, and event hash state.
- WorkSession-scoped mutations include the required mutation headers.
- Accepted WorkSession-scoped state changes record the Actor.
- Actor-bearing mutation bodies match `Jarvis-Actor-Id`.
- Accepted WorkSession-scoped state changes verify Actor authority.
- Accepted WorkSession-scoped state changes check
  `Jarvis-Expected-WorkSession-Revision`.
- Accepted WorkSession-scoped state changes link
  `Jarvis-Previous-Event-Hash`.
- AgentWorker action records PolicyDecision before accepted protocol state.
- Policy-denied action creates scoped Request.
- Request resolves only through Review or Takeover.
- Review approve or narrow produces bounded ApprovalScope.
- Stale Takeover rejection is covered by
  [stale-takeover-continuation.json](./fixtures/invalid/stale-takeover-continuation.json).
- Contribution records attributable human, agent, shared, service, or tool
  work.
- EvidenceManifest exports portable proof.
- LearningRecord captures human, agent, or pair learning.
- MemoryProposal and SkillProposal keep durable learning governed.
- OutcomeReport references LearningRecord without mutating sealed records.

## Required Header Gates

WorkSession-scoped mutating operations MUST include:

```txt
host authentication
Jarvis-Protocol-Version
Jarvis-Actor-Id
Jarvis-Idempotency-Key
Jarvis-Request-Timestamp
Jarvis-Expected-WorkSession-Revision
Jarvis-Previous-Event-Hash
```

The protocol rejects missing or invalid WorkSession-scoped mutation headers
before state changes.

Non-WorkSession protocol mutations MUST include:

```txt
host authentication
Jarvis-Protocol-Version
Jarvis-Actor-Id
Jarvis-Idempotency-Key
Jarvis-Request-Timestamp
```

Worker registration, Actor registration, and OutcomeReport submission are
non-WorkSession protocol mutations. They MUST NOT require fake
`Jarvis-Expected-WorkSession-Revision` or `Jarvis-Previous-Event-Hash` values.
They MUST verify Actor authority, idempotency, protocol version, and timestamp
before state changes.

WorkSession-scoped reads and export reads MUST include:

```txt
host authentication
Jarvis-Protocol-Version
Jarvis-Actor-Id
```

Read operations MUST NOT require mutation-only idempotency, request timestamp,
expected revision, or previous event hash headers.
Read operations MUST verify that `Jarvis-Actor-Id` has authority to read the
requested WorkSession-scoped record or export.

## Required Compatibility Gates

### Participant Gate

Compatible implementations MUST prove:

- Worker records identify protocol-visible participants.
- Actor records bind protocol-visible events to authorized acting identities.
- HumanWorker has policy, review, correction, and takeover authority.
- AgentWorker acts autonomously only inside Policy.
- Worker and Actor registration does not create accounts, authenticate
  callers, issue credentials, or own identity storage.

The protocol rejects:

- missing Actor header as `missing_actor`
- unauthorized Actor authority as `unauthorized_actor`
- missing protocol version as `missing_protocol_version`
- unsupported protocol version as `unsupported_protocol_version`

### WorkSession Gate

Compatible implementations MUST prove:

- WorkSession is the source of truth.
- WorkSession starts with objective, HumanWorker, AgentWorker, and Policy.
- WorkSession records revision and event hash state.
- Accepted WorkSession-scoped mutations increment revision.
- Accepted WorkSession-scoped mutations link to the previous event hash.
- Closed or sealed WorkSession records reject further mutation except
  idempotent replay of the same accepted request.

The protocol rejects:

- missing objective as `missing_objective`
- missing Policy as `missing_policy`
- stale WorkSession revision as `stale_work_session_revision`
- missing expected WorkSession revision as
  `missing_expected_work_session_revision`
- missing previous event hash as `missing_previous_event_hash`
- invalid previous event hash as `invalid_previous_event_hash`
- sealed WorkSession mutation as `sealed_work_session_mutation`
- mutation after closed WorkSession as `mutation_after_closed`

### PolicyDecision Gate

Compatible implementations MUST prove:

- Every AgentWorker action that affects a WorkSession records PolicyDecision
  before accepted protocol state.
- `allow` creates no authority outside selected grants.
- `deny` creates or references Request.
- `review_required` creates or references Request.
- `narrow` creates or references Review or Request before narrowed execution.

The protocol rejects:

- missing PolicyDecision as `missing_policy_decision`
- AgentWorker state mutation without PolicyDecision as
  `missing_policy_decision`
- policy-denied action without valid blocked handling as `policy_denied`

### Request Gate

Compatible implementations MUST prove:

- Request is structured, scoped deferral.
- Request is not chat, notification, or authority.
- Request blocks only its declared scope.
- Request records reason, risk, options, requested action, and safe fallback.
- Duplicate or unchanged rejected Requests do not create livelock.
- Expired Request applies safe fallback without granting new authority.

The protocol rejects:

- unresolved Request in terminal WorkSession state as `request_unresolved`
- invalid Request transitions as `invalid_request_transition`
- Request resolution without Review as `missing_review_resolution`
- Request resolution without Takeover as `missing_takeover_resolution`
- missing blocked scope resolution refs as
  `missing_blocked_scope_resolution_refs`
- repeated unchanged Request livelock as `request_livelock`
- duplicate Request mismatch as `duplicate_request_mismatch`

### Review And ApprovalScope Gate

Compatible implementations MUST prove:

- Review records HumanWorker judgment over a Request or protocol target.
- Review resolves Request only when it carries valid human judgment.
- Review approve or narrow creates bounded ApprovalScope.
- ApprovalScope binds request id, review id, PolicyDecision, action hash,
  allowed scope, denied scope, expiry, max uses, WorkSession, and Actor.
- Narrowed approval prevents execution outside approved scope.

The protocol rejects:

- missing Review resolution as `missing_review_resolution`
- invalid ApprovalScope as `invalid_approval_scope`
- expired ApprovalScope as `approval_scope_expired`
- mismatched ApprovalScope as `approval_scope_mismatch`

### Takeover Gate

Compatible implementations MUST prove:

- Takeover records HumanWorker direct control over a declared work scope.
- Takeover creates lock epoch.
- Takeover blocks stale AgentWorker continuation.
- Takeover resume requires reconciliation refs.
- Takeover resolution does not erase the Request, Review, or Contribution
  record.

The protocol rejects:

- missing Takeover resolution as `missing_takeover_resolution`
- stale Takeover epoch as `stale_takeover_epoch`
- missing reconciliation refs as `missing_reconciliation_refs`
- stale AgentWorker continuation after Takeover as `stale_takeover_epoch`

### Contribution Gate

Compatible implementations MUST prove:

- Contribution records who did what.
- Human, agent, shared, service, and tool contributions remain
  distinguishable.
- Shared Contribution preserves individual contributor refs.
- Contribution references WorkSession events or artifacts.
- Contribution does not contain payment, compensation, private score, or
  settlement fields.

The protocol rejects:

- missing Contribution actor as `missing_contribution_actor`
- invalid contributor refs as `invalid_contributor_refs`
- shared Contribution without individual contributor refs as
  `shared_contribution_without_individual_refs`
- duplicate contributor refs as `duplicate_contributor_ref`

### EvidenceManifest Gate

Compatible implementations MUST prove:

- Evidence is captured during work.
- Evidence item refs link to source JarvisEvents.
- Evidence item refs record who captured evidence and when.
- EvidenceManifest references the WorkSession event chain.
- EvidenceManifest references policy decisions, requests, reviews, takeovers,
  contributions, artifacts, evidence items, limitations, and export profile
  when present.
- EvidenceManifest export is valid only from completed, failed, cancelled, or
  closed WorkSession state.
- Redacted exports remain derived artifacts.
- Redaction never replaces the source evidence record.
- Portable exports exclude host-private fields.

The protocol rejects:

- invalid export as `invalid_export`
- invalid export state as `invalid_export_state`
- EvidenceManifest export from invalid WorkSession state as
  `invalid_evidence_export_state`
- sealed EvidenceManifest mutation as `sealed_evidence_mutation`
- evidence after the fact presented as during-work evidence as
  `evidence_after_the_fact`
- missing evidence event refs as `missing_evidence_event_refs`
- duplicate evidence item refs as `duplicate_evidence_item_ref`
- forbidden host-private export field as `forbidden_host_private_field`
- forbidden export field as `forbidden_export_field`

### Learning Gate

Compatible implementations MUST prove:

- LearningRecord records human, agent, or pair learning.
- LearningRecord references source events.
- LearningRecord does not directly create durable memory or active skill
  behavior.
- LearningRecord referenced by OutcomeReport records `outcome_report_refs` and
  WorkSession source events that support the learning.

The protocol rejects:

- learning mutation without governed source refs as `silent_memory_mutation` or
  `silent_skill_activation`
- OutcomeReport without LearningRecord as
  `outcome_report_without_learning_record`

### MemoryProposal Gate

Compatible implementations MUST prove:

- MemoryProposal records a proposed durable memory change.
- Durable memory does not silently mutate.
- Model-derived memory cannot confirm itself.
- Tool-derived memory cannot confirm itself.
- Accepted MemoryProposal requires review refs.
- Rejected, superseded, or expired MemoryProposal does not affect retrieval.

The protocol rejects:

- silent memory mutation as `silent_memory_mutation`
- model self-confirmed memory as `model_self_confirmed_memory`
- tool self-confirmed memory as `tool_self_confirmed_memory`

### SkillProposal Gate

Compatible implementations MUST prove:

- SkillProposal records a proposed reusable way of working.
- SkillProposal does not activate without review.
- SkillProposal does not expand tool access without policy review.
- Rejected, superseded, or archived SkillProposal does not affect future work.

The protocol rejects:

- silent skill activation as `silent_skill_activation`
- skill expansion without policy review as
  `skill_expands_tool_access_without_policy_review`

### OutcomeReport Gate

Compatible implementations MUST prove:

- OutcomeReport arrives after WorkSession completion.
- OutcomeReport does not mutate sealed WorkSession or sealed
  EvidenceManifest.
- OutcomeReport identifies the report source.
- OutcomeReport records the accepting Actor.
- OutcomeReport references at least one LearningRecord.
- OutcomeReport submission uses the non-WorkSession mutation header set.

The protocol rejects:

- OutcomeReport without LearningRecord as
  `outcome_report_without_learning_record`
- OutcomeReport without terminal WorkSession source as
  `outcome_report_requires_terminal_source`
- sealed WorkSession mutation from OutcomeReport as
  `sealed_work_session_mutation`
- sealed EvidenceManifest mutation from OutcomeReport as
  `sealed_evidence_mutation`

### Capability And Extension Gate

Compatible implementations MUST prove:

- Unsupported required capabilities reject as `unsupported_capability`.
- Extension fields are namespaced.
- Extension fields do not override core field names.
- Extension fields do not contain credentials, secrets, host database ids,
  runtime state, deployment details, billing data, private scores, or UI
  state.

The protocol rejects:

- unsupported capability as `unsupported_capability`
- invalid extension namespace as `invalid_extension_namespace`
- extension core field override as `extension_core_field_override`

## Fixture-Backed Rejection Gates

These rejection gates have current invalid fixtures.

| Gate | Error id | Fixture |
| --- | --- | --- |
| protocol version header is missing | `missing_protocol_version` | [missing-protocol-version.json](./fixtures/invalid/missing-protocol-version.json) |
| Actor header is missing | `missing_actor` | [missing-actor.json](./fixtures/invalid/missing-actor.json) |
| Actor lacks authority | `unauthorized_actor` | [unauthorized-actor.json](./fixtures/invalid/unauthorized-actor.json) |
| idempotency key is missing | `missing_idempotency_key` | [missing-idempotency-key.json](./fixtures/invalid/missing-idempotency-key.json) |
| request timestamp is missing | `missing_request_timestamp` | [missing-request-timestamp.json](./fixtures/invalid/missing-request-timestamp.json) |
| request timestamp is stale | `stale_request_timestamp` | [stale-request-timestamp.json](./fixtures/invalid/stale-request-timestamp.json) |
| expected WorkSession revision is missing | `missing_expected_work_session_revision` | [missing-expected-work-session-revision.json](./fixtures/invalid/missing-expected-work-session-revision.json) |
| WorkSession revision is stale | `stale_work_session_revision` | [stale-work-session-revision.json](./fixtures/invalid/stale-work-session-revision.json) |
| previous event hash is missing | `missing_previous_event_hash` | [missing-previous-event-hash.json](./fixtures/invalid/missing-previous-event-hash.json) |
| previous event hash is invalid | `invalid_previous_event_hash` | [invalid-previous-event-hash.json](./fixtures/invalid/invalid-previous-event-hash.json) |
| Policy is missing | `missing_policy` | [missing-policy.json](./fixtures/invalid/missing-policy.json) |
| PolicyDecision is missing | `missing_policy_decision` | [missing-policy-decision.json](./fixtures/invalid/missing-policy-decision.json) |
| Request is unresolved | `request_unresolved` | [unresolved-request.json](./fixtures/invalid/unresolved-request.json) |
| Review resolution is missing | `missing_review_resolution` | [missing-review-resolution.json](./fixtures/invalid/missing-review-resolution.json) |
| Takeover resolution is missing | `missing_takeover_resolution` | [missing-takeover-resolution.json](./fixtures/invalid/missing-takeover-resolution.json) |
| ApprovalScope is invalid | `invalid_approval_scope` | [invalid-approval-scope.json](./fixtures/invalid/invalid-approval-scope.json) |
| Takeover epoch is stale | `stale_takeover_epoch` | [stale-takeover-continuation.json](./fixtures/invalid/stale-takeover-continuation.json) |
| EvidenceManifest export state is invalid | `invalid_evidence_export_state` | [invalid-evidence-export-state.json](./fixtures/invalid/invalid-evidence-export-state.json) |
| WorkSession is sealed | `sealed_work_session_mutation` | [sealed-work-session-mutation.json](./fixtures/invalid/sealed-work-session-mutation.json) |
| EvidenceManifest is sealed | `sealed_evidence_mutation` | [sealed-evidence-mutation.json](./fixtures/invalid/sealed-evidence-mutation.json) |
| export contains host-private field | `forbidden_host_private_field` | [forbidden-host-private-export-field.json](./fixtures/invalid/forbidden-host-private-export-field.json) |
| memory mutates silently | `silent_memory_mutation` | [silent-memory-mutation.json](./fixtures/invalid/silent-memory-mutation.json) |
| skill activates silently | `silent_skill_activation` | [silent-skill-activation.json](./fixtures/invalid/silent-skill-activation.json) |
| OutcomeReport lacks LearningRecord | `outcome_report_without_learning_record` | [outcome-report-without-learning-record.json](./fixtures/invalid/outcome-report-without-learning-record.json) |
| OutcomeReport source is not terminal | `outcome_report_requires_terminal_source` | [outcome-report-requires-terminal-source.json](./fixtures/invalid/outcome-report-requires-terminal-source.json) |

## Non-Fixture-Backed Protocol Error Ids

These `ProtocolErrorId` values exist in the OpenAPI contract but do not have
dedicated invalid fixtures in the current v0.1 fixture set.

Compatible implementations MUST still reject these errors when the relevant
condition appears. Public conformance reports MUST NOT claim fixture coverage
for these ids unless fixtures are added.

```txt
invalid_transition
unknown_state
unsupported_protocol_version
path_body_id_mismatch
actor_body_id_mismatch
missing_objective
policy_denied
review_required
invalid_request_transition
missing_superseding_request
approval_scope_expired
approval_scope_mismatch
invalid_event_hash
duplicate_idempotency_key_mismatch
request_livelock
duplicate_request_mismatch
missing_jarvis_event
missing_blocked_scope_resolution_refs
missing_reconciliation_refs
mutation_after_closed
invalid_export
invalid_export_state
missing_contribution_actor
invalid_contributor_refs
shared_contribution_without_individual_refs
duplicate_contributor_ref
evidence_after_the_fact
missing_evidence_event_refs
duplicate_evidence_item_ref
forbidden_export_field
model_self_confirmed_memory
tool_self_confirmed_memory
skill_expands_tool_access_without_policy_review
unsupported_capability
invalid_extension_namespace
extension_core_field_override
```

## Required Error Envelope

Compatible implementations MUST return protocol errors with:

```txt
error_id
protocol_version
object_type
field
reason
remediation
trace_id
```

Protocol error responses MUST exclude host-private fields.

## Public Compatibility Claim

A product, host, SDK helper, or external system MUST NOT claim Jarvis
compatibility because it has chat, approval buttons, logs, agent runs, or
memory.

Public compatibility claims MUST use this exact structure:

```txt
Implementation: <name> <implementation-version>
Protocol compatibility: Jarvis <protocol-version>
Conformance surface: <conformance-surface>
Verification date: <date>
Verifier: <verifier-or-self-attested-status>
Evidence: <evidence-ref>
```

The claim MUST name:

- protocol version
- conformance surface
- fixture or checklist basis
- verification date
- retained evidence reference or artifact hash
- implementation version
- verifier identity or explicit self-attested status

Claims without independent verification MUST say `self-attested`.

Jarvis compatibility requires this proof:

```txt
PolicyDecision before accepted AgentWorker protocol state.
Request for blocked scope.
Review or Takeover resolution.
Takeover stale-continuation rejection.
Contribution attribution.
EvidenceManifest portable export boundary.
LearningRecord for human, agent, or pair learning.
Governed MemoryProposal and SkillProposal.
OutcomeReport references governed LearningRecord records.
Actor/body binding.
Required mutation headers.
Event hash chain.
Event hash chain conformance verifies previous-hash linkage with symbolic
`hash:` fixture values. It does not claim digest recomputation for fixture
examples.
Protocol error envelope.
Forbidden host-private export rejection.
```

Jarvis conformance protects the protocol record that makes human-agent work
governed, reviewable, attributable, evidence-backed, portable, and able to
improve across WorkSessions.
