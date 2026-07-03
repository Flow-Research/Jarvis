# Jarvis Roadmap

Jarvis is the open-source human-agent collaboration and learning-loop
compatibility protocol.

This roadmap records the completed v0.1.0 Protocol Alpha work and defines
next-phase protocol targets. It does not create an execution stack.

For the immediate execution plan, see
[12-30-day-roadmap.md](./12-30-day-roadmap.md).

For the OpenAPI entry gate, see
[14-protocol-lock.md](../protocol/14-protocol-lock.md).

For the post-v0.1 SDK helper tooling plan, see
[post-v0.1-sdk-helper-tooling/README.md](./post-v0.1-sdk-helper-tooling/README.md).

## Current Status

Week 1 protocol lock is complete.

Current protocol status: Jarvis v0.1.0 is released as Protocol Alpha.

Current active work: existing-agent implementation proof and public docs site
maintenance.

Release-readiness work for the v0.1.0 tag is complete:

- changelog
- contribution rules
- security policy
- citation metadata
- issue templates
- PR template
- validation CI
- release notes

Week 2 completed the OpenAPI 3.1 component syntax, path syntax, security scheme
encoding, protocol examples, and conformance entry rules from the locked Week 1
protocol decisions.

Week 3 completed protocol compatibility mapping, conformance fixtures, fixture
validation, and existing-agent compatibility proof. Jarvis does not add or own
adapters, runtimes, wrappers, host behavior, or integration code.

Week 4 completed compatible examples, public README tightening, published
conformance checklist, protocol record examples, and public story.

Post-v0.1 SDK helper tooling is implemented. TypeScript, Python, and CLI helper
surfaces stay limited to protocol implementation helpers.

The v0.1 acceptance review now includes protocol-publication discipline:
version consistency, precise conformance-claim language, release-readiness gap
logging, extension boundary checks, and governance-gap classification.

Jarvis v0.1.0 is released as Protocol Alpha. This release does not certify
Jarvis or any implementation, designate an official host, claim production
adoption, establish foundation governance, or create long-term support.

## Roadmap Contract

Jarvis owns:

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
- protocol export format
- OpenAPI 3.1 communication binding
- protocol compatibility mapping
- compatibility conformance expectations
- version negotiation rules
- capability negotiation rules
- conformance tests
- interoperability rules
- protocol implementation helper rules

Jarvis does not own:

- UI
- authentication
- host implementation details
- task/evaluation implementation details
- host/tool/environment implementation details
- model providers
- tool execution
- MCP hosting
- sandboxes
- databases
- queues
- cloud providers
- deployment
- local execution
- operational monitoring

Hosts own those responsibilities.

Jarvis SDKs are protocol implementation kits. They help compatible
implementations create, validate, export, and test Jarvis records. They do not
run agents, orchestrate models, execute tools, own memory engines, provide UI,
manage auth, store records, run sandboxes, schedule work, or become host
adapters.

## Protocol Version Targets

```txt
v0.1 accepted: Protocol Alpha
  locked vocabulary, OpenAPI 3.1 contract, event envelope, and golden-path
  conformance

v0.2 target: Evidence And Learning Beta
  stronger EvidenceManifest, Contribution, MemoryProposal, and SkillProposal
  contracts

v0.3 target: Ecosystem Conformance
  host conformance suite, examples, and compatibility-mapping records

v1.0 target: Stable Protocol
  stable public protocol, compatibility rules, export format, and migration
  policy
```

Rows after v0.1 are roadmap targets. These rows are not release, tag,
certification, long-term-support, governance, or adoption claims.

## v0.1 Protocol Alpha

Goal: prove the smallest complete human-agent collaboration loop.

The alpha proves that the loop is portable, not tied to a single host or
execution stack.

The protocol must express:

```txt
HumanWorker defines intent
Policy defines boundaries
AgentWorker acts inside policy
blocked action becomes Request
HumanWorker reviews or takes over
AgentWorker resumes when allowed
Contribution records who did what
EvidenceManifest captures proof during work
LearningRecord captures what the human, agent, and pair learned
MemoryProposal and SkillProposal remain governed
```

### v0.1 Must-Have Slice

- OpenAPI 3.1 contract for all core contracts
- event envelope
- WorkSession status transitions
- Policy decision model
- Request and Review lifecycle
- Takeover lifecycle
- Contribution ledger shape
- EvidenceManifest shape
- LearningRecord shape
- MemoryProposal shape
- SkillProposal shape
- portable export profile
- conformance tests for the golden path
- interoperability checklist
- protocol compatibility mapping
- one real existing-agent compatibility proof
- valid and invalid conformance fixtures
- version and capability negotiation
- non-normative public simulation boundary
- compatible implementation guide
- protocol implementation helper boundary
- protocol-publication discipline gate

### v0.1 Excludes

- execution packages
- agent framework packages
- cloud implementation
- local execution implementation
- model calls
- sandbox execution
- persistent storage implementation
- queues and scheduling
- hosted UI
- auth
- billing
- task routing
- host implementation

## Milestone 0: Protocol Lock

Status: complete.

Owner: Architecture

Output:

- official definition is frozen
- core terms are frozen
- system boundaries are frozen
- non-goals are frozen

Done when:

- README, Principles, Architecture, Package Contracts, Protocol v0.1, and
  Acceptance Criteria all agree.
- no Jarvis document assigns execution, cloud, database, sandbox, or deployment
  ownership to Jarvis.

## Milestone 1: OpenAPI Contract

Status: complete.

Owner: Protocol

Output:

- OpenAPI 3.1 document
- component schemas for Worker, Actor, HumanWorker, AgentWorker, WorkSession,
  JarvisEvent, Policy, PolicyDecision, Request, Review, Takeover,
  Contribution, EvidenceManifest, LearningRecord, MemoryProposal,
  SkillProposal, and OutcomeReport
- paths for core protocol operations
- security scheme and required protocol headers
- protocol error responses
- examples for WorkSession, Request, Review, and export

Done when:

- every component matches `11-core-protocol-objects.md`
- OpenAPI describes the HTTP communication binding
- required fields are explicit
- status values are enumerated
- references are typed
- no component or path requires implementation-private fields

## Milestone 2: WorkSession Lifecycle

Status: complete.

Owner: Protocol

Output:

- WorkSession status transition table
- event ordering rules
- event hash-chain rules
- objective recording rules
- completion rules
- failure and close rules

Done when:

- invalid transitions fail conformance tests
- every WorkSession has HumanWorker, AgentWorker, Policy, and objective
- events remain attributable to an Actor

## Milestone 3: Policy, Request, Review, Takeover

Status: complete.

Owner: Safety

Output:

- policy decision shape
- grant and denial shape
- Request creation rules
- Review decision rules
- approval narrowing rules
- takeover lock rules
- reconciliation rules

Done when:

- policy-denied action creates Request
- Request cannot reach human-resolved state without Review or Takeover
- Request blocks only its declared scope
- Review approves, denies, narrows, corrects, takes over, or requests revision
- takeover rejects stale autonomous continuation

## Milestone 4: Contribution And Evidence

Status: complete.

Owner: Evidence

Output:

- Contribution record
- EvidenceItem record
- EvidenceManifest record
- artifact reference shape
- limitation shape
- export profile

Done when:

- human, agent, service, and shared contributions are distinguishable
- EvidenceManifest references policy decisions, requests, reviews,
  contributions, artifacts, and limitations
- evidence is captured during work, not reconstructed after completion

## Milestone 5: Governed Learning

Status: complete.

Owner: Learning

Output:

- LearningRecord
- MemoryProposal
- SkillProposal
- provenance rules
- review-state rules
- scope rules

Done when:

- learning is attributed to human, agent, or pair
- HumanWorker and AgentWorker both improve from the same WorkSession
- memory changes require proposal and review state
- skill changes require proposal and review state
- unreviewed learning cannot become durable protocol memory

## Milestone 6: Conformance Suite

Status: complete.

Owner: Developer Experience

Output:

- golden-path conformance tests
- failure-mode conformance tests
- export conformance tests
- integration checklist

Done when a host proves:

- WorkSession is the source of truth
- Policy gates autonomous action
- blocked action creates Request
- Review or Takeover resolves Request
- Takeover prevents stale continuation
- Contributions are attributable
- EvidenceManifest is portable
- learning is governed

## Milestone 7: Examples And Public Docs

Status: complete.

Owner: Developer Experience

Output:

- protocol README
- glossary
- protocol diagrams
- OpenAPI examples
- compatible implementation guide
- EvidenceManifest consumption rules
- compatible host boundary note
- non-normative public simulation boundary

Done when:

- a team understands Jarvis without knowing any specific host
- a host implements Jarvis without inheriting execution assumptions
- the public simulation, when present, stays non-normative and protocol-aligned

## v0.1 Acceptance

Status: complete.

v0.1 is accepted because:

- OpenAPI contract passes the v0.1 acceptance review
- conformance tests cover the golden path
- no protocol contract names a cloud, database, sandbox, or deployment
  platform
- public docs describe Jarvis as protocol only
- live simulation, when present, describes Jarvis as protocol only
- any Jarvis SDK surface is limited to protocol implementation helpers
- public version labels, conformance claims, release-readiness gaps, and
  extension rules pass protocol-publication discipline review

## Post-v0.1 SDK Helper Tooling

Status: implemented.

Owner: Developer Experience

Issue scope:

- #64 SDK boundary and package plan
- #65 TypeScript protocol types and validators
- #66 Python protocol types and validators
- #67 conformance runner and protocol helper CLI

Output:

- SDK boundary document
- package plan
- TypeScript helper package plan
- Python helper package plan
- conformance runner and CLI plan
- conformance runner and protocol helper CLI package
- validator and fixture reuse plan

Done when:

- SDK helper surfaces stay limited to protocol implementation helpers
- TypeScript and Python helper scopes match the OpenAPI contract
- conformance runner scope matches the fixture contract
- package plans reject runtime, adapter, wrapper, model orchestration, tool
  execution, auth, storage, UI, billing, scoring, payment, and deployment
  behavior, monitoring, observability, host integration, and host workflow
- local validation passes

## Public Documentation Site Foundation

Status: complete.

Owner: Documentation

Output:

- public documentation entry point
- protocol overview
- OpenAPI and specification links
- conformance entry links
- SDK helper tooling links
- non-normative interactive walkthrough

Done when:

- public site introduces Jarvis as protocol-only
- public site links to the OpenAPI contract, conformance docs, examples,
  package docs, and release notes
- walkthrough stays non-normative and does not claim host UI implementation or
  protocol proof
- GitHub Pages workflow validates docs-site JavaScript
- local validation passes

## Protocol Record Compatibility Evidence Packs

Status: implemented.

Owner: Developer Experience

Output:

- machine-checkable existing-agent evidence pack
- Review-resolution proof pack
- Takeover-resolution proof pack
- protocol record envelopes
- EvidenceManifest export envelope
- JarvisEvent hash-chain envelope
- operation header envelopes
- evidence-pack validator

Done when:

- Review evidence pack derives from the canonical v0.1 golden-path fixture
- Takeover evidence pack derives from the valid v0.1 Takeover fixture
- evidence packs link to the existing-agent proof plan, protocol record
  examples, conformance checklist, OpenAPI binding, and OpenAPI schemas
- record files validate through protocol helper validators
- EvidenceManifest export validates only from a terminal WorkSession source
- OutcomeReport validates only from a terminal WorkSession source
- event hash chain validates through JarvisEvent previous-hash and event-hash
  rules
- operation headers validate through the v0.1 header gate
- evidence packs do not define adapter code, wrapper code, runtime behavior,
  host UI, model calls, tool execution, storage, auth, billing, scoring,
  payment, deployment, monitoring, host integration, or host workflow
  behavior
- local validation passes

## Existing-Agent Implementation Proof

Status: implemented.

Owner: Developer Experience

Output:

- SDK-helper generated native coding-agent proof
- proof generator
- proof validator
- protocol record fixture-shaped proof envelope
- EvidenceManifest export record
- OutcomeReport terminal-source record

Done when:

- proof records are generated through SDK helper surfaces
- checker rejects stale generated proof output
- HumanWorker and AgentWorker records are present
- WorkSession, Policy, PolicyDecision, Request, Review, Contribution,
  EvidenceManifest, LearningRecord, MemoryProposal, SkillProposal, and
  OutcomeReport records validate
- JarvisEvent hash chain validates
- operation headers validate through the v0.1 header gate
- EvidenceManifest validates only from a terminal WorkSession source
- OutcomeReport validates only from a terminal WorkSession source
- proof records do not define runtime behavior, host UI, model calls, tool
  execution, storage, auth, billing, scoring, payment, deployment, monitoring,
  host integration, adapters, wrappers, or host workflow
- local validation passes

## v0.2 Evidence And Learning Beta

Goal: strengthen the compounding loop.

Output:

- richer contribution taxonomy
- stronger evidence export profiles
- limitation and uncertainty records
- LearningRecord, MemoryProposal, and SkillProposal review-state rules
- memory scope compatibility rules
- skill proposal compatibility rules

Done when:

- external reviewers and systems consume Jarvis EvidenceManifest records
- implementations expose review, learning, and contribution history without
  changing protocol semantics
- external systems export compatible EvidenceManifest records

## v0.3 Ecosystem Conformance

Goal: make Jarvis implementable across independent hosts.

Output:

- host conformance suite
- compatibility evidence labels
- version negotiation rules
- migration examples
- public implementation checklist

Done when:

- two independent host shapes pass the same protocol conformance tests
- protocol records remain portable across compatible hosts
- implementation-private fields stay outside portable Jarvis records
- compatible hosts exchange WorkSession evidence without sharing
  infrastructure

## v1.0 Target: Stable Protocol

Goal: freeze the protocol surface.

Output:

- stable OpenAPI contract
- stable event envelope
- stable EvidenceManifest export format
- stable conformance suite
- compatibility policy
- migration policy

Done when:

- future compatible implementations read v1.0 records
- host implementations do not need to adopt any Jarvis-owned execution stack
- Jarvis remains protocol-only

## Risk Register

### Execution Creep

Risk: Jarvis starts defining how agents run.

Control: every execution, cloud, isolation, storage, queue, and deployment
choice belongs to hosts.

### Host Implementation Creep

Risk: Jarvis becomes a host workspace.

Control: hosts implement Jarvis; Jarvis does not inherit UI,
identity, operations, or enterprise controls.

### Task-System Creep

Risk: Jarvis becomes a task or evaluation system.

Control: task systems own tasks, rubrics, evaluation, and settlement. Jarvis
owns the collaboration record that external reviewers and systems evaluate.

### Weak Evidence

Risk: Evidence is reconstructed after work and loses trust.

Control: EvidenceManifest entries are captured during the WorkSession.

### Silent Learning

Risk: agent memory mutates without human review.

Control: learning becomes MemoryProposal or SkillProposal until reviewed.

### SDK Creep

Risk: Jarvis SDK work becomes an agent framework, runtime, planner, model
orchestrator, tool executor, memory engine, host adapter, UI kit, auth
provider, storage backend, sandbox, or workflow engine.

Control: Jarvis SDK work stays limited to protocol types, OpenAPI clients,
event helpers, hash-chain helpers, header helpers, validation helpers,
EvidenceManifest helpers, conformance fixture runners, protocol error helpers,
and example record mappers.

## Immediate Next Actions

1. Keep the repository protocol-only.
2. Keep execution and cloud ownership outside the protocol.
3. Use `11-core-protocol-objects.md`, `jarvis-openapi.yaml`, and
   `docs/conformance/` with the accepted v0.1 decision record.
4. Keep v0.1.0 release materials aligned with the tag.
5. Run local validation and GitHub validation CI before every protocol change.
6. Keep adapter code, wrappers, host behavior, and integration code outside
   Jarvis.
7. Keep every Jarvis SDK discussion limited to protocol implementation helpers.
8. Continue public documentation site work inside protocol-owned scope.
9. Start compatibility evidence only through Jarvis protocol records, not host
   runtime ownership.
