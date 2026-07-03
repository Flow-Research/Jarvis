import assert from "node:assert/strict";
import test from "node:test";

import {
  canonicalizeProtocolValue,
  createEvidenceManifest,
  createJarvisEvent,
  createNextJarvisEvent,
  createOperationEnvelope,
  createOperationPath,
  createReadHeaders,
  createWorkSessionMutationHeaders,
  findForbiddenHostPrivateField,
  getOperationBinding,
  hashProtocolValue,
  JarvisProtocolValidationError,
  protocolError,
  validateEvidenceManifest,
  validateEventHashChain,
  validateMutationHeaders,
  validateOperationHeaders,
  validateApprovalScope,
  validateOutcomeReport,
  validateProtocolRecord,
  validateReadHeaders,
} from "../src/index.js";

const AUTHORIZATION = "HostAuth test";

test("mutation headers enforce WorkSession-scoped zero-trust requirements", () => {
  const missing = validateMutationHeaders({
    Authorization: "HostAuth test",
    "Jarvis-Protocol-Version": "v0.1",
    "Jarvis-Actor-Id": "actor-test",
    "Jarvis-Idempotency-Key": "idem-test",
    "Jarvis-Request-Timestamp": "2026-06-16T10:00:00Z",
  });
  assert.equal(missing.valid, false);
  assert.equal(missing.errors[0].error_id, "missing_expected_work_session_revision");

  const accepted = validateMutationHeaders({
    Authorization: "HostAuth test",
    "Jarvis-Protocol-Version": "v0.1",
    "Jarvis-Actor-Id": "actor-test",
    "Jarvis-Idempotency-Key": "idem-test",
    "Jarvis-Request-Timestamp": "2026-06-16T10:00:00Z",
    "Jarvis-Expected-WorkSession-Revision": 0,
    "Jarvis-Previous-Event-Hash": "hash:protocol-genesis",
  });
  assert.equal(accepted.valid, true);
});

test("header helpers create valid read and WorkSession mutation headers", () => {
  const readHeaders = createReadHeaders({
    actorId: "actor-human-test",
    authorization: AUTHORIZATION,
  });
  assert.deepEqual(readHeaders, {
    Authorization: AUTHORIZATION,
    "Jarvis-Protocol-Version": "v0.1",
    "Jarvis-Actor-Id": "actor-human-test",
  });
  assert.equal(validateReadHeaders(readHeaders).valid, true);

  const mutationHeaders = createWorkSessionMutationHeaders({
    actorId: "actor-human-test",
    authorization: AUTHORIZATION,
    idempotencyKey: "idem-test",
    requestTimestamp: "2026-06-16T10:00:00Z",
    expectedWorkSessionRevision: 0,
    previousEventHash: "hash:protocol-genesis",
  });
  assert.equal(validateMutationHeaders(mutationHeaders).valid, true);
});

test("operation helper binds OpenAPI method path status headers and actor", () => {
  const binding = getOperationBinding("exportEvidenceManifest");
  assert.deepEqual(binding, {
    method: "GET",
    path: "/work-sessions/{work_session_id}/export",
    statuses: [200, 400],
  });
  assert.equal(
    createOperationPath("exportEvidenceManifest", { work_session_id: "ws-test" }),
    "/work-sessions/ws-test/export",
  );
  assert.equal(
    createOperationPath("exportEvidenceManifest", { work_session_id: "ws-!'()*" }),
    "/work-sessions/ws-%21%27%28%29%2A/export",
  );

  const operation = createOperationEnvelope({
    operationId: "exportEvidenceManifest",
    actorId: "actor-human-test",
    authorization: AUTHORIZATION,
    workSessionId: "ws-test",
  });
  assert.deepEqual(operation, {
    operation_id: "exportEvidenceManifest",
    method: "GET",
    path: "/work-sessions/ws-test/export",
    headers: {
      Authorization: AUTHORIZATION,
      "Jarvis-Protocol-Version": "v0.1",
      "Jarvis-Actor-Id": "actor-human-test",
    },
    actor_id: "actor-human-test",
    expected_status: 200,
    work_session_id: "ws-test",
  });
  assert.equal(validateOperationHeaders(operation).valid, true);
});

test("operation helper preserves caller-provided headers", () => {
  const headers = createWorkSessionMutationHeaders({
    actorId: "actor-human-test",
    authorization: AUTHORIZATION,
    idempotencyKey: "idem-test",
    requestTimestamp: "2026-06-16T10:00:00Z",
    expectedWorkSessionRevision: 0,
    previousEventHash: "hash:protocol-genesis",
  });
  const operation = createOperationEnvelope({
    operationId: "appendJarvisEvent",
    actorId: "actor-human-test",
    headers,
    workSessionId: "ws-test",
    bodyRef: "records.jarvis_events.created",
  });
  assert.equal(operation.headers, headers);
  assert.equal(validateOperationHeaders(operation).valid, true);
});

test("event and EvidenceManifest helpers build records accepted by validators", () => {
  const created = createNextJarvisEvent({
    id: "event-created",
    type: "work_session.created",
    workSessionId: "ws-test",
    actorId: "actor-human-test",
    timestamp: "2026-06-16T10:00:00Z",
    payload: {
      object_type: "work_session",
      object_id: "ws-test",
      action: "created",
    },
  });
  const completed = createNextJarvisEvent({
    events: [created],
    id: "event-completed",
    type: "work_session.completed",
    workSessionId: "ws-test",
    actorId: "actor-human-test",
    timestamp: "2026-06-16T10:10:00Z",
    payload: {
      object_type: "work_session",
      object_id: "ws-test",
      action: "completed",
    },
  });
  assert.equal(created.sequence, 1);
  assert.equal(completed.sequence, 2);
  assert.equal(completed.previous_hash, created.event_hash);
  assert.equal(validateEventHashChain([created, completed]).valid, true);

  const workSession = {
    id: "ws-test",
    objective: "Prove helper-created protocol records.",
    status: "completed",
    last_event_hash: completed.event_hash,
  };
  const manifest = createEvidenceManifest({
    id: "evidence-test",
    workSession,
    events: [created, completed],
    generatedByActorId: "actor-human-test",
    generatedAt: "2026-06-16T10:11:00Z",
    evidenceItemRefs: [
      {
        id: "evidence-item-test",
        work_session_id: "ws-test",
        source_event_refs: ["event-completed"],
        captured_by_actor_id: "actor-human-test",
        evidence_type: "artifact",
        artifact_ref: "artifact:test",
        content_hash: "hash:content",
        trust_label: "verified",
        redaction_state: "none",
        captured_at: "2026-06-16T10:10:00Z",
        limitation_refs: [],
      },
    ],
  });
  assert.equal(manifest.event_chain_root, completed.event_hash);
  assert.equal(validateEvidenceManifest(manifest, { workSession }).valid, true);
});

test("event helper computes hash before optional signature metadata", () => {
  const base = {
    id: "event-signed",
    sequence: 1,
    type: "work_session.created",
    workSessionId: "ws-test",
    actorId: "actor-human-test",
    timestamp: "2026-06-16T10:00:00Z",
    payload: {
      object_type: "work_session",
      object_id: "ws-test",
      action: "created",
    },
  };
  const unsigned = createJarvisEvent(base);
  const signed = createJarvisEvent({
    ...base,
    actorSignature: "signature:test",
    signingKeyRef: "signing-key:test",
  });
  assert.equal(signed.event_hash, unsigned.event_hash);
  assert.equal(signed.actor_signature, "signature:test");
});

test("event helper rejects mismatched caller-supplied event hash", () => {
  assert.throws(
    () => createJarvisEvent({
      id: "event-bad-hash",
      sequence: 1,
      type: "work_session.created",
      workSessionId: "ws-test",
      actorId: "actor-human-test",
      timestamp: "2026-06-16T10:00:00Z",
      payload: {
        object_type: "work_session",
        object_id: "ws-test",
        action: "created",
      },
      eventHash: "hash:not-the-canonical-event",
    }),
    (error) => error instanceof JarvisProtocolValidationError
      && error.error.error_id === "invalid_event_hash",
  );
});

test("next event helper rejects cross-WorkSession event linkage", () => {
  const other = createNextJarvisEvent({
    id: "event-other",
    type: "work_session.created",
    workSessionId: "ws-other",
    actorId: "actor-human-test",
    timestamp: "2026-06-16T10:00:00Z",
    payload: {
      object_type: "work_session",
      object_id: "ws-other",
      action: "created",
    },
  });
  assert.throws(
    () => createNextJarvisEvent({
      events: [other],
      id: "event-wrong-link",
      type: "work_session.completed",
      workSessionId: "ws-test",
      actorId: "actor-human-test",
      timestamp: "2026-06-16T10:10:00Z",
      payload: {
        object_type: "work_session",
        object_id: "ws-test",
        action: "completed",
      },
    }),
    (error) => error instanceof JarvisProtocolValidationError
      && error.error.error_id === "invalid_export",
  );
});

test("operation helper rejects concrete path WorkSession mismatch", () => {
  assert.throws(
    () => createOperationEnvelope({
      operationId: "appendJarvisEvent",
      actorId: "actor-human-test",
      authorization: AUTHORIZATION,
      path: "/work-sessions/ws-other/events",
      workSessionId: "ws-test",
      idempotencyKey: "idem-test",
      requestTimestamp: "2026-06-16T10:00:00Z",
      expectedWorkSessionRevision: 0,
      previousEventHash: "hash:protocol-genesis",
      bodyRef: "records.jarvis_events.created",
    }),
    (error) => error instanceof JarvisProtocolValidationError
      && error.error.error_id === "path_body_id_mismatch",
  );
});

test("EvidenceManifest helper rejects empty refs and root drift", () => {
  const event = createNextJarvisEvent({
    id: "event-root",
    type: "work_session.completed",
    workSessionId: "ws-test",
    actorId: "actor-human-test",
    timestamp: "2026-06-16T10:10:00Z",
    payload: {
      object_type: "work_session",
      object_id: "ws-test",
      action: "completed",
    },
  });
  const workSession = {
    id: "ws-test",
    objective: "Reject malformed manifest helpers.",
    status: "completed",
    last_event_hash: event.event_hash,
  };
  assert.throws(
    () => createEvidenceManifest({
      id: "evidence-empty",
      workSession,
      events: [event],
      generatedByActorId: "actor-human-test",
      generatedAt: "2026-06-16T10:11:00Z",
    }),
    (error) => error instanceof JarvisProtocolValidationError
      && error.error.error_id === "invalid_export",
  );
  assert.throws(
    () => createEvidenceManifest({
      id: "evidence-root-drift",
      workSession,
      events: [event],
      eventChainRoot: "hash:wrong-root",
      generatedByActorId: "actor-human-test",
      generatedAt: "2026-06-16T10:11:00Z",
      evidenceItemRefs: [
        {
          id: "evidence-item-test",
          work_session_id: "ws-test",
          source_event_refs: ["event-root"],
          captured_by_actor_id: "actor-human-test",
          evidence_type: "artifact",
          artifact_ref: "artifact:test",
          content_hash: "hash:content",
          trust_label: "verified",
          redaction_state: "none",
          captured_at: "2026-06-16T10:10:00Z",
          limitation_refs: [],
        },
      ],
    }),
    (error) => error instanceof JarvisProtocolValidationError
      && error.error.error_id === "invalid_evidence_export_state",
  );
});

test("required identity and replay headers reject empty values", () => {
  const result = validateMutationHeaders({
    Authorization: " ",
    "Jarvis-Protocol-Version": "v0.1",
    "Jarvis-Actor-Id": "actor-test",
    "Jarvis-Idempotency-Key": "idem-test",
    "Jarvis-Request-Timestamp": "2026-06-16T10:00:00Z",
    "Jarvis-Expected-WorkSession-Revision": 0,
    "Jarvis-Previous-Event-Hash": "hash:protocol-genesis",
  });
  assert.equal(result.valid, false);
  assert.equal(result.errors[0].field, "headers.Authorization");
});

test("required mutation headers reject undefined values", () => {
  const baseHeaders = {
    Authorization: "HostAuth test",
    "Jarvis-Protocol-Version": "v0.1",
    "Jarvis-Actor-Id": "actor-test",
    "Jarvis-Idempotency-Key": "idem-test",
    "Jarvis-Request-Timestamp": "2026-06-16T10:00:00Z",
    "Jarvis-Expected-WorkSession-Revision": 0,
    "Jarvis-Previous-Event-Hash": "hash:protocol-genesis",
  };
  for (const [header, errorId] of [
    ["Jarvis-Request-Timestamp", "missing_request_timestamp"],
    ["Jarvis-Expected-WorkSession-Revision", "missing_expected_work_session_revision"],
    ["Jarvis-Previous-Event-Hash", "missing_previous_event_hash"],
  ]) {
    const headers = { ...baseHeaders, [header]: undefined };
    const result = validateMutationHeaders(headers);
    assert.equal(result.valid, false, header);
    assert.equal(result.errors[0].error_id, errorId);
  }
});

test("ApprovalScope requires review timestamp when review context is present", () => {
  const approvalScope = {
    id: "approval-test",
    request_id: "request-test",
    review_id: "review-test",
    policy_decision_id: "policy-decision-test",
    approved_action: { action: "fetch", target: "registry.npmjs.org" },
    allowed_scope: { domain: "registry.npmjs.org" },
    denied_scope: {},
    expires_at: "2026-06-16T10:30:00Z",
    max_uses: 3,
    applies_to_work_session_id: "ws-test",
    applies_to_actor_id: "actor-agent-test",
    normalized_action_hash: "hash:approval-test",
  };
  const result = validateApprovalScope(approvalScope, {
    request: {
      id: "request-test",
      policy_decision_id: "policy-decision-test",
      requester_actor_id: "actor-agent-test",
    },
    review: {
      id: "review-test",
      work_session_id: "ws-test",
    },
  });
  assert.equal(result.valid, false);
  assert.equal(result.errors[0].error_id, "invalid_approval_scope");
});

test("timestamp skew rejects future requests beyond one minute", () => {
  const result = validateMutationHeaders(
    {
      Authorization: "HostAuth test",
      "Jarvis-Protocol-Version": "v0.1",
      "Jarvis-Actor-Id": "actor-test",
      "Jarvis-Idempotency-Key": "idem-test",
      "Jarvis-Request-Timestamp": "2026-06-16T10:04:00Z",
      "Jarvis-Expected-WorkSession-Revision": 0,
      "Jarvis-Previous-Event-Hash": "hash:protocol-genesis",
    },
    { now: new Date("2026-06-16T10:00:00Z") },
  );
  assert.equal(result.valid, false);
  assert.equal(result.errors[0].error_id, "stale_request_timestamp");
});

test("previous hash header requires protocol hash prefix", () => {
  const result = validateMutationHeaders({
    Authorization: "HostAuth test",
    "Jarvis-Protocol-Version": "v0.1",
    "Jarvis-Actor-Id": "actor-test",
    "Jarvis-Idempotency-Key": "idem-test",
    "Jarvis-Request-Timestamp": "2026-06-16T10:00:00Z",
    "Jarvis-Expected-WorkSession-Revision": 0,
    "Jarvis-Previous-Event-Hash": "not-a-protocol-hash",
  });
  assert.equal(result.valid, false);
  assert.equal(result.errors[0].error_id, "invalid_previous_event_hash");
});

test("read operations still bind operation actor to Actor header", () => {
  const result = validateOperationHeaders({
    operation_id: "exportEvidenceManifest",
    method: "GET",
    path: "/work-sessions/ws-test/export",
    actor_id: "actor-body",
    expected_status: 200,
    headers: {
      Authorization: "HostAuth test",
      "Jarvis-Protocol-Version": "v0.1",
      "Jarvis-Actor-Id": "actor-header",
    },
  });
  assert.equal(result.valid, false);
  assert.equal(result.errors[0].error_id, "actor_body_id_mismatch");
});

test("read headers reject mutation-only requirements", () => {
  const accepted = validateReadHeaders({
    Authorization: "HostAuth test",
    "Jarvis-Protocol-Version": "v0.1",
    "Jarvis-Actor-Id": "actor-test",
  });
  assert.equal(accepted.valid, true);

  const extraMutationHeader = validateReadHeaders({
    Authorization: "HostAuth test",
    "Jarvis-Protocol-Version": "v0.1",
    "Jarvis-Actor-Id": "actor-test",
    "Jarvis-Idempotency-Key": "idem-test",
  });
  assert.equal(extraMutationHeader.valid, false);
  assert.equal(extraMutationHeader.errors[0].error_id, "invalid_export");
});

test("OutcomeReport requires a terminal WorkSession source", () => {
  const report = {
    id: "outcome-test",
    work_session_id: "ws-test",
    source_ref: "source:ws-test",
    reporter_ref: "reporter:test",
    accepted_by_actor_id: "actor-human-test",
    outcome: "accepted",
    learning_record_refs: ["learning-test"],
    received_at: "2026-06-16T10:00:00Z",
  };
  const missingSource = validateOutcomeReport(report);
  assert.equal(missingSource.valid, false);
  assert.equal(missingSource.errors[0].error_id, "outcome_report_requires_terminal_source");

  const activeSource = validateOutcomeReport(report, {
    workSession: { id: "ws-test", status: "active" },
  });
  assert.equal(activeSource.valid, false);
  assert.equal(activeSource.errors[0].error_id, "outcome_report_requires_terminal_source");

  const completedSource = validateOutcomeReport(report, {
    workSession: { id: "ws-test", status: "completed" },
  });
  assert.equal(completedSource.valid, true);

  const wrongSource = validateOutcomeReport(report, {
    workSession: { id: "ws-other", status: "completed" },
  });
  assert.equal(wrongSource.valid, false);
  assert.equal(wrongSource.errors[0].error_id, "outcome_report_requires_terminal_source");
});

test("EvidenceManifest export requires terminal WorkSession source", () => {
  const manifest = {
    id: "evidence-test",
    work_session_id: "ws-test",
    generated_by_actor_id: "actor-human-test",
    objective: "test",
    event_chain_root: "hash:root",
    evidence_item_refs: [
      {
        id: "evidence-item-test",
        work_session_id: "ws-test",
        source_event_refs: ["event-test"],
        captured_by_actor_id: "actor-agent-test",
        evidence_type: "artifact",
        artifact_ref: "artifact:test",
        content_hash: "hash:content",
        trust_label: "verified",
        redaction_state: "none",
        captured_at: "2026-06-16T10:00:00Z",
        limitation_refs: [],
      },
    ],
    policy_decision_refs: [],
    request_refs: [],
    review_refs: [],
    takeover_refs: [],
    contribution_refs: [],
    export_profile: {
      profile: "portable",
    },
    generated_at: "2026-06-16T10:00:00Z",
  };

  const missingSource = validateEvidenceManifest(manifest);
  assert.equal(missingSource.valid, false);
  assert.equal(missingSource.errors[0].error_id, "invalid_evidence_export_state");

  const activeSource = validateEvidenceManifest(manifest, {
    workSession: { id: "ws-test", status: "active" },
  });
  assert.equal(activeSource.valid, false);
  assert.equal(activeSource.errors[0].error_id, "invalid_evidence_export_state");

  const completedSource = validateEvidenceManifest(manifest, {
    workSession: { id: "ws-test", status: "completed" },
  });
  assert.equal(completedSource.valid, true);

  const wrongSource = validateEvidenceManifest(manifest, {
    workSession: { id: "ws-other", status: "completed" },
  });
  assert.equal(wrongSource.valid, false);
  assert.equal(wrongSource.errors[0].error_id, "invalid_evidence_export_state");
  assert.equal(wrongSource.errors[0].field, "work_session_id");

  const rootDrift = validateEvidenceManifest(
    { ...manifest, event_chain_root: "hash:wrong-root" },
    {
      workSession: { id: "ws-test", status: "completed", last_event_hash: "hash:root" },
    },
  );
  assert.equal(rootDrift.valid, false);
  assert.equal(rootDrift.errors[0].error_id, "invalid_evidence_export_state");
  assert.equal(rootDrift.errors[0].field, "event_chain_root");
});

test("protocol error helper emits the OpenAPI error envelope", () => {
  const error = protocolError("missing_actor", {
    objectType: "headers",
    field: "Jarvis-Actor-Id",
    reason: "actor missing",
    remediation: "send actor header",
    traceId: "trace:test",
  });
  assert.deepEqual(error, {
    error_id: "missing_actor",
    protocol_version: "v0.1",
    object_type: "headers",
    field: "Jarvis-Actor-Id",
    reason: "actor missing",
    remediation: "send actor header",
    trace_id: "trace:test",
  });
});

test("protocol error helper rejects ids outside the OpenAPI enum", () => {
  const error = protocolError("not_in_openapi");
  assert.equal(error.error_id, "invalid_export");
  assert.equal(error.field, "error_id");
});

test("closed schema validation rejects unknown protocol fields", () => {
  const result = validateProtocolRecord("OutcomeReport", {
    id: "outcome-test",
    work_session_id: "ws-test",
    source_ref: "source:ws-test",
    reporter_ref: "reporter:test",
    accepted_by_actor_id: "actor-human-test",
    outcome: "accepted",
    learning_record_refs: ["learning-test"],
    received_at: "2026-06-16T10:00:00Z",
    unexpected_host_field: "host-only",
  });
  assert.equal(result.valid, false);
  assert.equal(result.errors[0].error_id, "invalid_export");
});

test("generic schema validation rejects unknown protocol object type", () => {
  const result = validateProtocolRecord("NotAProtocolObject", {});
  assert.equal(result.valid, false);
  assert.equal(result.errors[0].error_id, "invalid_export");
  assert.equal(result.errors[0].field, "object_type");
});

test("generic schema validation rejects non-object records as invalid export", () => {
  const result = validateProtocolRecord("Request", null);
  assert.equal(result.valid, false);
  assert.equal(result.errors[0].error_id, "invalid_export");
});

test("protocol record validation rejects nested host-private fields", () => {
  const result = validateProtocolRecord("JarvisEvent", {
    id: "event-test",
    sequence: 1,
    type: "work_session.created",
    work_session_id: "ws-test",
    actor_id: "actor-test",
    timestamp: "2026-06-16T10:00:00Z",
    payload: {
      object_type: "work_session",
      object_id: "ws-test",
      action: "created",
      raw_runtime_state: "host-only",
    },
    previous_hash: "hash:protocol-genesis",
    event_hash: "hash:event-test",
    canonicalization: {
      serialization: "json-c14n",
      hash_method: "sha256",
      profile_ref: "canonicalization:v0.1",
    },
  });
  assert.equal(result.valid, false);
  assert.equal(result.errors[0].error_id, "forbidden_host_private_field");
  assert.equal(result.errors[0].field, "payload.raw_runtime_state");
});

test("canonicalization and hashing are stable across object key order", () => {
  const left = { b: 2, a: { y: true, x: "yes" } };
  const right = { a: { x: "yes", y: true }, b: 2 };
  assert.equal(canonicalizeProtocolValue(left), canonicalizeProtocolValue(right));
  assert.equal(hashProtocolValue(left), hashProtocolValue(right));
});

test("event hash-chain helper rejects broken previous hashes", () => {
  const valid = validateEventHashChain([
    {
      sequence: 1,
      previous_hash: "hash:protocol-genesis",
      event_hash: "hash:first",
    },
    {
      sequence: 2,
      previous_hash: "hash:first",
      event_hash: "hash:second",
    },
  ]);
  assert.equal(valid.valid, true);

  const invalid = validateEventHashChain([
    {
      sequence: 1,
      previous_hash: "hash:protocol-genesis",
      event_hash: "hash:first",
    },
    {
      sequence: 2,
      previous_hash: "hash:wrong",
      event_hash: "hash:second",
    },
  ]);
  assert.equal(invalid.valid, false);
  assert.equal(invalid.errors[0].error_id, "invalid_previous_event_hash");
});

test("event hash-chain helper rejects malformed sequence and duplicate event hash", () => {
  const malformedSequence = validateEventHashChain([
    {
      sequence: 0,
      previous_hash: "hash:protocol-genesis",
      event_hash: "hash:first",
    },
  ]);
  assert.equal(malformedSequence.valid, false);
  assert.equal(malformedSequence.errors[0].error_id, "invalid_export");
  assert.equal(malformedSequence.errors[0].field, "sequence");

  const duplicateSequence = validateEventHashChain([
    {
      sequence: 1,
      previous_hash: "hash:protocol-genesis",
      event_hash: "hash:first",
    },
    {
      sequence: 1,
      previous_hash: "hash:first",
      event_hash: "hash:second",
    },
  ]);
  assert.equal(duplicateSequence.valid, false);
  assert.equal(duplicateSequence.errors[0].error_id, "invalid_export");
  assert.equal(duplicateSequence.errors[0].field, "sequence");

  const missingHash = validateEventHashChain([
    {
      sequence: 1,
      previous_hash: "hash:protocol-genesis",
    },
  ]);
  assert.equal(missingHash.valid, false);
  assert.equal(missingHash.errors[0].error_id, "invalid_event_hash");
  assert.equal(missingHash.errors[0].field, "event_hash");

  const duplicateHash = validateEventHashChain([
    {
      sequence: 1,
      previous_hash: "hash:protocol-genesis",
      event_hash: "hash:same",
    },
    {
      sequence: 2,
      previous_hash: "hash:same",
      event_hash: "hash:same",
    },
  ]);
  assert.equal(duplicateHash.valid, false);
  assert.equal(duplicateHash.errors[0].error_id, "invalid_event_hash");
  assert.equal(duplicateHash.errors[0].field, "event_hash");
});

test("host-private field scanner returns the forbidden path", () => {
  assert.equal(
    findForbiddenHostPrivateField({ export_profile: {}, session_cookie: "secret" }),
    "session_cookie",
  );
  assert.equal(
    findForbiddenHostPrivateField({ export_profile: {}, "private-key": "secret" }),
    "private-key",
  );
  assert.equal(
    findForbiddenHostPrivateField({ export_profile: {}, rawPrompt: "secret" }),
    "rawPrompt",
  );
});
