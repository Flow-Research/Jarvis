# Conformance Fixtures

This directory contains Jarvis v0.1 conformance fixtures.

Fixtures are protocol proof records. They do not execute host behavior,
runtime behavior, model calls, tool calls, UI, storage, auth backend, billing,
scoring, payment, or deployment behavior.

## Layout

```txt
valid/
  golden-path.json
  takeover-path.json

invalid/
  forbidden-host-private-export-field.json
  invalid-approval-scope.json
  invalid-evidence-export-state.json
  invalid-previous-event-hash.json
  missing-actor.json
  missing-expected-work-session-revision.json
  missing-idempotency-key.json
  missing-policy-decision.json
  missing-policy.json
  missing-previous-event-hash.json
  missing-protocol-version.json
  missing-request-timestamp.json
  missing-review-resolution.json
  missing-takeover-resolution.json
  outcome-report-requires-terminal-source.json
  outcome-report-without-learning-record.json
  sealed-evidence-mutation.json
  sealed-work-session-mutation.json
  silent-memory-mutation.json
  silent-skill-activation.json
  stale-request-timestamp.json
  stale-takeover-continuation.json
  stale-work-session-revision.json
  unauthorized-actor.json
  unresolved-request.json
```

## Fixture Envelope

Every fixture uses this envelope:

```txt
fixture_id
protocol_version
kind
title
description
source_contract_refs
host_shape_ref
records
operations
assertions
expected_result
expected_error_id
expected_error_field
```

Valid fixtures omit `expected_error_id` and `expected_error_field`.
Invalid fixtures include one primary `expected_error_id`.

`host_shape_ref` is fixture metadata only. It MUST NOT appear inside records,
operation bodies, JarvisEvents, EvidenceManifest, or portable export payloads.

## Records

`records` contains protocol records only.

Fixture precondition records represent protocol authority that exists before
the operation sequence starts. They remain protocol records and do not define
host setup.

When a protocol object changes state during the fixture, records use named
snapshots:

```txt
genesis_request
active
pending
approved
completed
```

Named snapshots do not create host state. They preserve the protocol state that
operations and assertions reference.

## Operations

`operations` use OpenAPI operation ids from
`docs/openapi/jarvis-openapi.yaml`.

Operation entries record the OpenAPI `HostAuth` placeholder, Jarvis protocol
headers, and expected protocol outcomes. They do not define auth backend
behavior and do not execute host code.

Accepted mutation operations that produce a JarvisEvent record use
`expected_event_ref` with the produced JarvisEvent id. Fixtures MUST NOT
duplicate that produced event with a separate `appendJarvisEvent` operation.
`appendJarvisEvent` appears only when the operation under test directly appends
a JarvisEvent request body.

## Assertions

`assertions` record the protocol gates that a compatible implementation proves
or rejects.

Assertion classes come from the public conformance gates in
`docs/conformance/checklist.md` and the allowed validator set in
`scripts/check_conformance_fixtures.py`.

## Validator

Jarvis defines this validator command for conformance fixtures:

```txt
python3 scripts/check_conformance_fixtures.py
```

Conformance fixture records MUST satisfy fixture envelope fields, operation
binding, required headers, assertion refs, source_contract_refs, OpenAPI
component refs, required invalid-fixture coverage, global assertion-class
coverage, golden-path semantic coverage, invalid rejection semantics,
WorkSession revision and previous-hash binding, host-private export boundaries,
and expected protocol outcomes.

The validator MUST NOT execute host behavior. It validates only Jarvis protocol
fixture records.
