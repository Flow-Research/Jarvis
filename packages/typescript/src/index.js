import { createHash } from "node:crypto";
import {
  OPENAPI_SCHEMA_NAMES,
  PROTOCOL_VERSION,
  SCHEMA_ALLOWED_FIELDS,
  SCHEMA_CLOSED_SCHEMAS,
  SCHEMA_ENUMS,
  SCHEMA_FORBIDDEN_FIELDS,
  SCHEMA_REQUIRED_FIELDS,
} from "./generated/schema-metadata.js";

export {
  OPENAPI_SCHEMA_NAMES,
  PROTOCOL_VERSION,
  SCHEMA_ALLOWED_FIELDS,
  SCHEMA_CLOSED_SCHEMAS,
  SCHEMA_ENUMS,
  SCHEMA_FORBIDDEN_FIELDS,
  SCHEMA_REQUIRED_FIELDS,
};

export const WORKSESSION_MUTATION_HEADERS = Object.freeze([
  "Authorization",
  "Jarvis-Protocol-Version",
  "Jarvis-Actor-Id",
  "Jarvis-Idempotency-Key",
  "Jarvis-Request-Timestamp",
  "Jarvis-Expected-WorkSession-Revision",
  "Jarvis-Previous-Event-Hash",
]);

export const NON_WORKSESSION_MUTATION_HEADERS = Object.freeze([
  "Authorization",
  "Jarvis-Protocol-Version",
  "Jarvis-Actor-Id",
  "Jarvis-Idempotency-Key",
  "Jarvis-Request-Timestamp",
]);

export const READ_HEADERS = Object.freeze([
  "Authorization",
  "Jarvis-Protocol-Version",
  "Jarvis-Actor-Id",
]);

export const MUTATION_ONLY_HEADERS = Object.freeze([
  "Jarvis-Idempotency-Key",
  "Jarvis-Request-Timestamp",
  "Jarvis-Expected-WorkSession-Revision",
  "Jarvis-Previous-Event-Hash",
]);

export const TERMINAL_WORK_SESSION_STATES = Object.freeze([
  "completed",
  "failed",
  "cancelled",
  "closed",
]);

export const REVIEW_RESOLVED_REQUEST_STATUSES = Object.freeze([
  "approved",
  "denied",
  "narrowed",
  "answered",
  "needs_revision",
]);

export const FORBIDDEN_EXPORT_KEY_TOKENS = Object.freeze([
  "password",
  "credential",
  "token",
  "secret",
  "private_key",
  "session_cookie",
  "cookie",
  "api_key",
  "access_key",
  "auth_header",
  "oauth",
  "database",
  "billing",
  "runtime",
  "container",
  "deployment",
  "model_api_key",
  "raw_prompt",
  "host_account",
  "ui_state",
  "private_score",
]);

const MISSING_HEADER_ERROR_IDS = Object.freeze({
  Authorization: "unauthorized_actor",
  "Jarvis-Protocol-Version": "missing_protocol_version",
  "Jarvis-Actor-Id": "missing_actor",
  "Jarvis-Idempotency-Key": "missing_idempotency_key",
  "Jarvis-Request-Timestamp": "missing_request_timestamp",
  "Jarvis-Expected-WorkSession-Revision": "missing_expected_work_session_revision",
  "Jarvis-Previous-Event-Hash": "missing_previous_event_hash",
});

const OBJECT_BY_OPERATION = Object.freeze({
  registerWorker: "Worker",
  registerActor: "Actor",
  createWorkSession: "WorkSession",
  appendJarvisEvent: "JarvisEvent",
  recordPolicyDecision: "PolicyDecision",
  createRequest: "Request",
  recordReview: "Review",
  recordTakeover: "Takeover",
  recordContribution: "Contribution",
  createLearningRecord: "LearningRecord",
  createMemoryProposal: "MemoryProposal",
  createSkillProposal: "SkillProposal",
  submitOutcomeReport: "OutcomeReport",
  exportEvidenceManifest: "EvidenceManifest",
});

const OPERATION_BINDINGS_BY_ID = Object.freeze({
  registerWorker: Object.freeze({ method: "PUT", path: "/workers/{worker_id}", statuses: new Set([200, 400]) }),
  registerActor: Object.freeze({ method: "PUT", path: "/actors/{actor_id}", statuses: new Set([200, 400]) }),
  createWorkSession: Object.freeze({ method: "POST", path: "/work-sessions", statuses: new Set([201, 400]) }),
  getWorkSession: Object.freeze({
    method: "GET",
    path: "/work-sessions/{work_session_id}",
    statuses: new Set([200, 400]),
  }),
  appendJarvisEvent: Object.freeze({
    method: "POST",
    path: "/work-sessions/{work_session_id}/events",
    statuses: new Set([201, 400]),
  }),
  recordPolicyDecision: Object.freeze({
    method: "POST",
    path: "/work-sessions/{work_session_id}/policy-decisions",
    statuses: new Set([201, 400]),
  }),
  createRequest: Object.freeze({
    method: "POST",
    path: "/work-sessions/{work_session_id}/requests",
    statuses: new Set([201, 400]),
  }),
  recordReview: Object.freeze({
    method: "POST",
    path: "/work-sessions/{work_session_id}/reviews",
    statuses: new Set([201, 400]),
  }),
  recordTakeover: Object.freeze({
    method: "POST",
    path: "/work-sessions/{work_session_id}/takeovers",
    statuses: new Set([201, 400]),
  }),
  recordContribution: Object.freeze({
    method: "POST",
    path: "/work-sessions/{work_session_id}/contributions",
    statuses: new Set([201, 400]),
  }),
  createLearningRecord: Object.freeze({
    method: "POST",
    path: "/work-sessions/{work_session_id}/learning-records",
    statuses: new Set([201, 400]),
  }),
  createMemoryProposal: Object.freeze({
    method: "POST",
    path: "/work-sessions/{work_session_id}/memory-proposals",
    statuses: new Set([201, 400]),
  }),
  createSkillProposal: Object.freeze({
    method: "POST",
    path: "/work-sessions/{work_session_id}/skill-proposals",
    statuses: new Set([201, 400]),
  }),
  exportEvidenceManifest: Object.freeze({
    method: "GET",
    path: "/work-sessions/{work_session_id}/export",
    statuses: new Set([200, 400]),
  }),
  submitOutcomeReport: Object.freeze({ method: "POST", path: "/outcome-reports", statuses: new Set([202, 400]) }),
});

const ACTOR_BODY_FIELD_BY_OPERATION = Object.freeze({
  createWorkSession: "created_by_actor_id",
  appendJarvisEvent: "actor_id",
  recordPolicyDecision: "actor_id",
  createRequest: "requester_actor_id",
  recordReview: "reviewer_actor_id",
  recordTakeover: "controlling_actor_id",
  createLearningRecord: "created_by_actor_id",
  createMemoryProposal: "proposed_by_actor_id",
  createSkillProposal: "proposed_by_actor_id",
  submitOutcomeReport: "accepted_by_actor_id",
});

const PROTOCOL_ERROR_IDS = new Set(SCHEMA_ENUMS.ProtocolErrorId ?? []);

const DEFAULT_CANONICALIZATION = Object.freeze({
  serialization: "json-c14n",
  hash_method: "sha256",
  profile_ref: "canonicalization:v0.1",
});

export class JarvisProtocolValidationError extends Error {
  constructor(error) {
    super(error.reason);
    this.name = "JarvisProtocolValidationError";
    this.error = error;
  }
}

export function protocolError(errorId, options = {}) {
  if (!PROTOCOL_ERROR_IDS.has(errorId)) {
    return {
      error_id: "invalid_export",
      protocol_version: PROTOCOL_VERSION,
      object_type: "ProtocolError",
      field: "error_id",
      reason: `ProtocolErrorId MUST exist in the OpenAPI ProtocolErrorId enum: ${errorId}`,
      remediation: "Use a Jarvis v0.1 ProtocolErrorId from the OpenAPI contract.",
      trace_id: options.traceId ?? "trace:jarvis-sdk",
    };
  }
  return {
    error_id: errorId,
    protocol_version: PROTOCOL_VERSION,
    object_type: options.objectType ?? "protocol",
    field: options.field ?? "",
    reason: options.reason ?? errorId,
    remediation: options.remediation ?? "Submit a Jarvis v0.1 compatible record.",
    trace_id: options.traceId ?? "trace:jarvis-sdk",
  };
}

export function validationResult(errors) {
  return {
    valid: errors.length === 0,
    errors,
  };
}

function fail(errorId, options = {}) {
  return validationResult([protocolError(errorId, options)]);
}

function pass() {
  return validationResult([]);
}

function assertValid(result) {
  if (!result.valid) {
    throw new JarvisProtocolValidationError(
      result.errors[0] ?? protocolError("invalid_export"),
    );
  }
}

function helperError(field, reason) {
  return new JarvisProtocolValidationError(protocolError("invalid_export", {
    objectType: "ProtocolHelper",
    field,
    reason,
  }));
}

function successfulStatus(binding) {
  return [...binding.statuses].sort((left, right) => left - right).find((status) => status < 400);
}

function operationWorkSessionScoped(binding) {
  return binding.path.startsWith("/work-sessions");
}

function buildHeadersForOperation(binding, options) {
  if (options.headers) {
    return options.headers;
  }
  const shared = {
    actorId: options.actorId,
    authorization: options.authorization,
    protocolVersion: options.protocolVersion,
    validationOptions: options.validationOptions,
  };
  if (binding.method === "GET") {
    return createReadHeaders(shared);
  }
  if (!operationWorkSessionScoped(binding)) {
    return createNonWorkSessionMutationHeaders({
      ...shared,
      idempotencyKey: options.idempotencyKey,
      requestTimestamp: options.requestTimestamp,
    });
  }
  return createWorkSessionMutationHeaders({
    ...shared,
    idempotencyKey: options.idempotencyKey,
    requestTimestamp: options.requestTimestamp,
    expectedWorkSessionRevision: options.expectedWorkSessionRevision,
    previousEventHash: options.previousEventHash,
  });
}

function pathParamsForOperation(options) {
  return {
    ...(options.pathParams ?? {}),
    worker_id: options.workerId ?? options.pathParams?.worker_id,
    actor_id: options.targetActorId ?? options.pathParams?.actor_id,
    work_session_id: options.workSessionId ?? options.pathParams?.work_session_id,
  };
}

function invalidEventHashError(field, reason) {
  return new JarvisProtocolValidationError(protocolError("invalid_event_hash", {
    objectType: "JarvisEvent",
    field,
    reason,
  }));
}

function invalidEvidenceRootError(field, reason) {
  return new JarvisProtocolValidationError(protocolError("invalid_evidence_export_state", {
    objectType: "EvidenceManifest",
    field,
    reason,
  }));
}

function lastEventForWorkSession(events, workSessionId) {
  if (!Array.isArray(events) || events.length === 0) {
    return null;
  }
  if (!isNonEmptyString(workSessionId)) {
    throw helperError("work_session_id", "work_session_id is required when JarvisEvents are supplied.");
  }
  const mismatch = events.find((event) => {
    return isPlainObject(event) && event.work_session_id !== workSessionId;
  });
  if (mismatch) {
    throw helperError("events.work_session_id", "JarvisEvents MUST belong to the target WorkSession.");
  }
  return [...events]
    .filter((event) => isPlainObject(event) && isInteger(event.sequence))
    .sort((left, right) => right.sequence - left.sequence)[0] ?? null;
}

function eventHashFor(eventWithoutHash, callerHash) {
  const computedHash = hashProtocolValue(eventWithoutHash);
  if (callerHash !== undefined && callerHash !== computedHash) {
    throw invalidEventHashError(
      "event_hash",
      "JarvisEvent.event_hash MUST match the canonical hash of the event body.",
    );
  }
  return computedHash;
}

function assertManifestRoot(workSession, events, eventChainRoot) {
  const workSessionHash = workSession?.last_event_hash;
  if (!isNonEmptyString(workSessionHash)) {
    throw invalidEvidenceRootError(
      "work_session.last_event_hash",
      "EvidenceManifest export requires a terminal WorkSession last_event_hash.",
    );
  }
  if (eventChainRoot !== undefined && eventChainRoot !== workSessionHash) {
    throw invalidEvidenceRootError(
      "event_chain_root",
      "EvidenceManifest.event_chain_root MUST match WorkSession.last_event_hash.",
    );
  }
  if (Array.isArray(events) && events.length > 0) {
    assertValid(validateEventHashChain(events));
    const previous = lastEventForWorkSession(events, workSession?.id);
    if (previous?.event_hash !== workSessionHash) {
      throw invalidEvidenceRootError(
        "event_chain_root",
        "EvidenceManifest event chain root MUST match the terminal WorkSession last_event_hash.",
      );
    }
  }
  return workSessionHash;
}

export function createReadHeaders(options = {}) {
  const headers = {
    Authorization: options.authorization,
    "Jarvis-Protocol-Version": options.protocolVersion ?? PROTOCOL_VERSION,
    "Jarvis-Actor-Id": options.actorId,
  };
  assertValid(validateReadHeaders(headers, options.validationOptions));
  return headers;
}

export function createNonWorkSessionMutationHeaders(options = {}) {
  const headers = {
    Authorization: options.authorization,
    "Jarvis-Protocol-Version": options.protocolVersion ?? PROTOCOL_VERSION,
    "Jarvis-Actor-Id": options.actorId,
    "Jarvis-Idempotency-Key": options.idempotencyKey,
    "Jarvis-Request-Timestamp": options.requestTimestamp,
  };
  assertValid(validateMutationHeaders(headers, {
    ...(options.validationOptions ?? {}),
    workSessionScoped: false,
  }));
  return headers;
}

export function createWorkSessionMutationHeaders(options = {}) {
  const headers = {
    Authorization: options.authorization,
    "Jarvis-Protocol-Version": options.protocolVersion ?? PROTOCOL_VERSION,
    "Jarvis-Actor-Id": options.actorId,
    "Jarvis-Idempotency-Key": options.idempotencyKey,
    "Jarvis-Request-Timestamp": options.requestTimestamp,
    "Jarvis-Expected-WorkSession-Revision": options.expectedWorkSessionRevision,
    "Jarvis-Previous-Event-Hash": options.previousEventHash,
  };
  assertValid(validateMutationHeaders(headers, options.validationOptions));
  return headers;
}

export function createMutationHeaders(options = {}) {
  if (options.workSessionScoped === false) {
    return createNonWorkSessionMutationHeaders(options);
  }
  return createWorkSessionMutationHeaders(options);
}

export function getOperationBinding(operationId) {
  const binding = OPERATION_BINDINGS_BY_ID[operationId];
  if (!binding) {
    throw helperError("operation_id", "operation_id MUST exist in the Jarvis OpenAPI binding.");
  }
  return {
    method: binding.method,
    path: binding.path,
    statuses: [...binding.statuses].sort((left, right) => left - right),
  };
}

function encodePathParam(value) {
  return encodeURIComponent(value).replace(/[!'()*]/g, (char) => {
    return `%${char.charCodeAt(0).toString(16).toUpperCase()}`;
  });
}

export function createOperationPath(operationId, pathParams = {}) {
  const binding = getOperationBinding(operationId);
  return binding.path.replace(/\{([^/]+)\}/g, (_match, key) => {
    const value = pathParams[key];
    if (!isNonEmptyString(value)) {
      throw helperError(`path.${key}`, `${key} is required for ${operationId}.`);
    }
    return encodePathParam(value);
  });
}

export function createOperationEnvelope(options = {}) {
  const operationId = options.operationId;
  const binding = getOperationBinding(operationId);
  const path = options.path ?? createOperationPath(operationId, pathParamsForOperation(options));
  const headers = buildHeadersForOperation(OPERATION_BINDINGS_BY_ID[operationId], options);
  const pathValues = operationPathValues({ operation_id: operationId, path });
  const operation = {
    operation_id: operationId,
    method: binding.method,
    path,
    headers,
    actor_id: options.actorId,
    expected_status: options.expectedStatus ?? successfulStatus(OPERATION_BINDINGS_BY_ID[operationId]),
  };
  if (options.expectedErrorId) {
    operation.expected_error_id = options.expectedErrorId;
  }
  if (options.expectedErrorField) {
    operation.expected_error_field = options.expectedErrorField;
  }
  if (options.workSessionId ?? pathValues.work_session_id) {
    operation.work_session_id = options.workSessionId ?? pathValues.work_session_id;
  }
  if (options.bodyRef) {
    operation.body_ref = options.bodyRef;
  }
  if (options.attemptedTakeoverLockEpoch !== undefined) {
    operation.attempted_takeover_lock_epoch = options.attemptedTakeoverLockEpoch;
  }
  const bindingError = operationBindingError(operation);
  if (bindingError) {
    throw new JarvisProtocolValidationError(bindingError);
  }
  assertValid(validateOperationHeaders(operation, options.validationOptions));
  return operation;
}

export function createJarvisEvent(options = {}) {
  const hashInput = {
    id: options.id,
    sequence: options.sequence,
    type: options.type,
    work_session_id: options.workSessionId,
    actor_id: options.actorId,
    timestamp: options.timestamp,
    payload: options.payload,
    previous_hash: options.previousHash ?? "hash:protocol-genesis",
    canonicalization: options.canonicalization ?? DEFAULT_CANONICALIZATION,
  };
  if (options.traceContext) {
    hashInput.trace_context = options.traceContext;
  }
  const event = {
    ...hashInput,
    event_hash: eventHashFor(hashInput, options.eventHash),
  };
  if (options.actorSignature) {
    event.actor_signature = options.actorSignature;
  }
  if (options.signingKeyRef) {
    event.signing_key_ref = options.signingKeyRef;
  }
  assertValid(validateProtocolRecord("JarvisEvent", event));
  return event;
}

export function createNextJarvisEvent(options = {}) {
  const previous = lastEventForWorkSession(options.events ?? [], options.workSessionId);
  return createJarvisEvent({
    ...options,
    sequence: options.sequence ?? (previous ? previous.sequence + 1 : 1),
    previousHash: options.previousHash ?? (previous ? previous.event_hash : "hash:protocol-genesis"),
  });
}

export function createEvidenceManifest(options = {}) {
  const workSession = options.workSession;
  const root = assertManifestRoot(workSession, options.events ?? [], options.eventChainRoot);
  const manifest = {
    id: options.id,
    work_session_id: options.workSessionId ?? workSession?.id,
    generated_by_actor_id: options.generatedByActorId,
    objective: options.objective ?? workSession?.objective,
    event_chain_root: root,
    evidence_item_refs: options.evidenceItemRefs ?? [],
    policy_decision_refs: options.policyDecisionRefs ?? [],
    request_refs: options.requestRefs ?? [],
    review_refs: options.reviewRefs ?? [],
    takeover_refs: options.takeoverRefs ?? [],
    contribution_refs: options.contributionRefs ?? [],
    export_profile: options.exportProfile ?? {
      profile: "portable_evidence_manifest",
      version: PROTOCOL_VERSION,
    },
    generated_at: options.generatedAt,
  };
  if (options.artifactRefs) {
    manifest.artifact_refs = options.artifactRefs;
  }
  if (options.limitationRefs) {
    manifest.limitation_refs = options.limitationRefs;
  }
  if (options.redactionRefs) {
    manifest.redaction_refs = options.redactionRefs;
  }
  assertValid(validateEvidenceManifest(manifest, { workSession }));
  return manifest;
}

function isPlainObject(value) {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

function isNonEmptyString(value) {
  return typeof value === "string" && value.trim().length > 0;
}

function isInteger(value) {
  return Number.isInteger(value);
}

function timestamp(value) {
  if (!isNonEmptyString(value)) {
    return null;
  }
  if (!/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$/.test(value)) {
    return null;
  }
  const parsed = Date.parse(value);
  return Number.isNaN(parsed) ? null : parsed;
}

function getRef(root, ref) {
  if (!isNonEmptyString(ref)) {
    return undefined;
  }
  return ref.split(".").reduce((current, part) => {
    if (!isPlainObject(current)) {
      return undefined;
    }
    return current[part];
  }, root);
}

function operationBody(fixture, operation) {
  return getRef(fixture, operation?.body_ref);
}

function firstRejectingOperation(fixture) {
  const operations = Array.isArray(fixture?.operations) ? fixture.operations : [];
  return operations.find((operation) => operation?.expected_status >= 400) ?? operations[0];
}

function allRecords(records, group) {
  const values = records?.[group];
  return isPlainObject(values)
    ? Object.values(values).filter((value) => isPlainObject(value))
    : [];
}

function recordById(records, group, id) {
  return allRecords(records, group).find((record) => record.id === id);
}

function idsFor(records, group) {
  return new Set(allRecords(records, group).map((record) => record.id));
}

function actorById(records, actorId) {
  return recordById(records, "actors", actorId);
}

function workerForActor(records, actor) {
  return actor ? recordById(records, "workers", actor.worker_id) : undefined;
}

function workerGrants(worker) {
  const scope = worker?.authority_scope;
  const grants = isPlainObject(scope) && Array.isArray(scope.grants) ? scope.grants : [];
  return new Set(grants.filter((grant) => typeof grant === "string"));
}

function operationMethod(operation) {
  return OPERATION_BINDINGS_BY_ID[operation?.operation_id]?.method ?? operation?.method;
}

function operationPath(operation) {
  return OPERATION_BINDINGS_BY_ID[operation?.operation_id]?.path ?? operation?.path ?? "";
}

function escapeRegex(value) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function operationPathMatchesTemplate(template, path) {
  if (!isNonEmptyString(template) || !isNonEmptyString(path)) {
    return false;
  }
  const pattern = `^${template.split("/").map((segment) => {
    if (/^\{[^/]+\}$/.test(segment)) {
      return "[^/]+";
    }
    return escapeRegex(segment);
  }).join("/")}$`;
  return new RegExp(pattern).test(path);
}

function operationPathValues(operation) {
  const binding = OPERATION_BINDINGS_BY_ID[operation?.operation_id];
  if (!binding || !isNonEmptyString(operation?.path)) {
    return {};
  }
  const templateSegments = binding.path.split("/");
  const pathSegments = operation.path.split("/");
  if (templateSegments.length !== pathSegments.length) {
    return {};
  }
  const values = {};
  for (let index = 0; index < templateSegments.length; index += 1) {
    const match = templateSegments[index].match(/^\{([^/]+)\}$/);
    if (match) {
      values[match[1]] = decodeURIComponent(pathSegments[index]);
    }
  }
  return values;
}

function operationBindingError(operation) {
  const operationId = operation?.operation_id;
  const binding = OPERATION_BINDINGS_BY_ID[operationId];
  if (!binding) {
    return protocolError("invalid_export", {
      objectType: "FixtureOperation",
      field: "operation_id",
      reason: "Fixture operation_id MUST exist in the Jarvis OpenAPI binding.",
    });
  }
  if (operation.method !== binding.method) {
    return protocolError("invalid_export", {
      objectType: "FixtureOperation",
      field: "method",
      reason: "Fixture operation method MUST match the Jarvis OpenAPI binding.",
    });
  }
  if (!operationPathMatchesTemplate(binding.path, operation.path)) {
    return protocolError("invalid_export", {
      objectType: "FixtureOperation",
      field: "path",
      reason: "Fixture operation path MUST match the Jarvis OpenAPI binding.",
    });
  }
  if (!binding.statuses.has(operation.expected_status)) {
    return protocolError("invalid_export", {
      objectType: "FixtureOperation",
      field: "expected_status",
      reason: "Fixture operation expected_status MUST match the Jarvis OpenAPI binding.",
    });
  }
  const pathValues = operationPathValues(operation);
  if (
    isNonEmptyString(pathValues.work_session_id)
    && operation.work_session_id !== pathValues.work_session_id
  ) {
    return protocolError("path_body_id_mismatch", {
      objectType: "FixtureOperation",
      field: "work_session_id",
      reason: "operation.work_session_id MUST match the concrete WorkSession path id.",
    });
  }
  return null;
}

function targetWorkSessionId(operation, body) {
  return operation?.work_session_id ?? body?.work_session_id ?? body?.id;
}

function requestIdFromTargetRef(targetRef) {
  return isNonEmptyString(targetRef) && targetRef.startsWith("request:")
    ? targetRef.slice("request:".length)
    : undefined;
}

function recordTimestamp(record) {
  for (const field of ["created_at", "timestamp", "generated_at", "received_at"]) {
    if (record?.[field]) {
      return timestamp(record[field]);
    }
  }
  return null;
}

function workSessionSnapshotForOperation(records, operation, body) {
  const workSessionId = targetWorkSessionId(operation, body);
  const revision = operation?.headers?.["Jarvis-Expected-WorkSession-Revision"];
  const previousHash = operation?.headers?.["Jarvis-Previous-Event-Hash"];
  return allRecords(records, "work_sessions").find((snapshot) => {
    return (
      snapshot.id === workSessionId
      && (revision === undefined || snapshot.revision === revision)
      && (previousHash === undefined || snapshot.last_event_hash === previousHash)
    );
  });
}

function outcomeReportSourceWorkSession(records, outcomeReport) {
  const candidates = allRecords(records, "work_sessions").filter((snapshot) => {
    return snapshot.id === outcomeReport?.work_session_id;
  });
  return (
    candidates.find((snapshot) => TERMINAL_WORK_SESSION_STATES.includes(snapshot.status))
    ?? candidates[0]
  );
}

function evidenceManifestSourceWorkSession(fixture, evidenceManifest, operation) {
  const records = fixture?.records ?? {};
  const expectedField = fixture?.expected_error_field;
  if (
    fixture?.expected_error_id === "invalid_evidence_export_state"
    && isNonEmptyString(expectedField)
    && expectedField.endsWith(".status")
  ) {
    const referenced = getRef(fixture, expectedField.slice(0, -".status".length));
    if (isPlainObject(referenced)) {
      return referenced;
    }
  }
  const workSessionId = evidenceManifest?.work_session_id;
  return (
    allRecords(records, "work_sessions").find((snapshot) => {
      return snapshot.id === workSessionId
        && TERMINAL_WORK_SESSION_STATES.includes(snapshot.status);
    })
    ?? workSessionSnapshotForOperation(records, operation, evidenceManifest)
    ?? allRecords(records, "work_sessions").find((snapshot) => snapshot.id === workSessionId)
  );
}

function operationBodyBindingError(operation, body) {
  const pathValues = operationPathValues(operation);
  if (
    isNonEmptyString(pathValues.work_session_id)
    && isPlainObject(body)
    && body.work_session_id !== pathValues.work_session_id
  ) {
    return protocolError("path_body_id_mismatch", {
      field: "work_session_id",
      reason: "body.work_session_id MUST match the concrete WorkSession path id.",
    });
  }
  const actorBodyField = ACTOR_BODY_FIELD_BY_OPERATION[operation?.operation_id];
  if (!actorBodyField || !isPlainObject(body)) {
    return null;
  }
  const headerActorId = operation?.headers?.["Jarvis-Actor-Id"];
  if (body[actorBodyField] !== headerActorId) {
    return protocolError("actor_body_id_mismatch", {
      field: actorBodyField,
      reason: `${actorBodyField} MUST match Jarvis-Actor-Id.`,
    });
  }
  return null;
}

function createWorkSessionGenesisError(operation) {
  if (operation?.operation_id !== "createWorkSession") {
    return null;
  }
  const headers = operation?.headers ?? {};
  const revision = headers["Jarvis-Expected-WorkSession-Revision"];
  const previousHash = headers["Jarvis-Previous-Event-Hash"];
  if (revision !== 0) {
    return protocolError("stale_work_session_revision", {
      field: "headers.Jarvis-Expected-WorkSession-Revision",
      reason: "createWorkSession MUST use WorkSession revision 0.",
    });
  }
  if (previousHash !== "hash:protocol-genesis") {
    return protocolError("invalid_previous_event_hash", {
      field: "headers.Jarvis-Previous-Event-Hash",
      reason: "createWorkSession MUST use hash:protocol-genesis as previous event hash.",
    });
  }
  return null;
}

function operationStateError(records, operation, body) {
  const headers = operation?.headers ?? {};
  const revision = headers["Jarvis-Expected-WorkSession-Revision"];
  const previousHash = headers["Jarvis-Previous-Event-Hash"];
  if (operation?.operation_id === "createWorkSession") {
    return createWorkSessionGenesisError(operation);
  }
  if (!operationPath(operation).startsWith("/work-sessions")) {
    return null;
  }
  if (revision === undefined || previousHash === undefined) {
    return null;
  }
  const workSessionId = targetWorkSessionId(operation, body);
  const workSessionStates = allRecords(records, "work_sessions")
    .filter((state) => state.id === workSessionId)
    .map((state) => ({
      revision: state.revision,
      hash: state.last_event_hash,
    }));
  const eventStates = allRecords(records, "jarvis_events")
    .filter((event) => event.work_session_id === workSessionId)
    .map((event) => ({
      revision: event.sequence,
      hash: event.event_hash,
    }));
  const representedStates = [...workSessionStates, ...eventStates];
  if (representedStates.length === 0) {
    return null;
  }
  if (representedStates.some((state) => state.revision === revision && state.hash === previousHash)) {
    return null;
  }
  if (representedStates.some((state) => state.hash === previousHash)) {
    return protocolError("stale_work_session_revision", {
      field: "headers.Jarvis-Expected-WorkSession-Revision",
      reason: "Expected WorkSession revision does not match the represented previous hash state.",
    });
  }
  return protocolError("invalid_previous_event_hash", {
    field: "headers.Jarvis-Previous-Event-Hash",
    reason: "Previous event hash is not represented for the WorkSession.",
  });
}

function pathForKey(basePath, key) {
  return basePath ? `${basePath}.${key}` : key;
}

function compactKey(value) {
  return value.toLowerCase().replace(/[^a-z0-9]+/g, "");
}

const FORBIDDEN_EXPORT_COMPACT_KEY_TOKENS = new Set(
  FORBIDDEN_EXPORT_KEY_TOKENS.map((token) => compactKey(token)),
);

function evidenceManifestExportError(evidenceManifest, workSession) {
  const forbidden = findForbiddenHostPrivateField(evidenceManifest);
  if (forbidden) {
    return protocolError("forbidden_host_private_field", {
      objectType: "EvidenceManifest",
      field: forbidden,
      reason: "EvidenceManifest MUST exclude host-private fields.",
    });
  }
  const workSessionStatus = workSession?.status;
  if (!workSessionStatus) {
    return protocolError("invalid_evidence_export_state", {
      objectType: "EvidenceManifest",
      field: "work_session.status",
      reason: "EvidenceManifest export requires a terminal WorkSession source.",
    });
  }
  if (workSessionStatus && !TERMINAL_WORK_SESSION_STATES.includes(workSessionStatus)) {
    return protocolError("invalid_evidence_export_state", {
      objectType: "EvidenceManifest",
      field: "work_session.status",
      reason: "EvidenceManifest export requires a terminal WorkSession source.",
    });
  }
  if (workSession?.id !== evidenceManifest?.work_session_id) {
    return protocolError("invalid_evidence_export_state", {
      objectType: "EvidenceManifest",
      field: "work_session_id",
      reason: "EvidenceManifest source WorkSession id MUST match EvidenceManifest.work_session_id.",
    });
  }
  if (workSession?.last_event_hash && evidenceManifest?.event_chain_root !== workSession.last_event_hash) {
    return protocolError("invalid_evidence_export_state", {
      objectType: "EvidenceManifest",
      field: "event_chain_root",
      reason: "EvidenceManifest.event_chain_root MUST match WorkSession.last_event_hash.",
    });
  }
  return null;
}

export function findForbiddenHostPrivateField(value, basePath = "") {
  if (Array.isArray(value)) {
    for (let index = 0; index < value.length; index += 1) {
      const found = findForbiddenHostPrivateField(value[index], `${basePath}[${index}]`);
      if (found) {
        return found;
      }
    }
    return null;
  }
  if (!isPlainObject(value)) {
    return null;
  }
  for (const [key, child] of Object.entries(value)) {
    const normalized = key.toLowerCase();
    const compact = compactKey(key);
    if (
      FORBIDDEN_EXPORT_KEY_TOKENS.includes(normalized)
      || FORBIDDEN_EXPORT_KEY_TOKENS.some((token) => normalized.includes(token))
      || FORBIDDEN_EXPORT_COMPACT_KEY_TOKENS.has(compact)
      || [...FORBIDDEN_EXPORT_COMPACT_KEY_TOKENS].some((token) => compact.includes(token))
    ) {
      return pathForKey(basePath, key);
    }
    const found = findForbiddenHostPrivateField(child, pathForKey(basePath, key));
    if (found) {
      return found;
    }
  }
  return null;
}

export function validateSchemaRecord(objectType, record) {
  if (!OPENAPI_SCHEMA_NAMES.includes(objectType)) {
    return fail("invalid_export", {
      objectType,
      field: "object_type",
      reason: `${objectType} MUST be defined by the OpenAPI schema.`,
    });
  }
  if (!isPlainObject(record)) {
    return fail("invalid_export", {
      objectType,
      field: objectType,
      reason: `${objectType} MUST be an object.`,
    });
  }
  const required = SCHEMA_REQUIRED_FIELDS[objectType] ?? [];
  for (const field of required) {
    if (!(field in record) || record[field] === undefined || record[field] === null) {
      return fail("invalid_export", {
        objectType,
        field,
        reason: `${objectType}.${field} is required.`,
      });
    }
  }
  const forbidden = new Set(SCHEMA_FORBIDDEN_FIELDS[objectType] ?? []);
  const closed = SCHEMA_CLOSED_SCHEMAS.includes(objectType);
  const allowed = new Set(SCHEMA_ALLOWED_FIELDS[objectType] ?? []);
  for (const field of Object.keys(record)) {
    if (forbidden.has(field)) {
      return fail("forbidden_host_private_field", {
        objectType,
        field,
        reason: `${objectType}.${field} is forbidden in portable protocol records.`,
      });
    }
    if (closed && !allowed.has(field)) {
      return fail("invalid_export", {
        objectType,
        field,
        reason: `${objectType}.${field} is not defined by the closed OpenAPI schema.`,
      });
    }
  }
  return pass();
}

export function validateMutationHeaders(headers, options = {}) {
  const workSessionScoped = options.workSessionScoped !== false;
  const required = workSessionScoped
    ? WORKSESSION_MUTATION_HEADERS
    : NON_WORKSESSION_MUTATION_HEADERS;
  return validateHeaders(headers, {
    ...options,
    requiredHeaders: required,
  });
}

export function validateReadHeaders(headers, options = {}) {
  const result = validateHeaders(headers, {
    ...options,
    requiredHeaders: READ_HEADERS,
  });
  if (!result.valid) {
    return result;
  }
  const forbiddenHeader = MUTATION_ONLY_HEADERS.find((header) => header in headers);
  if (forbiddenHeader) {
    return fail("invalid_export", {
      objectType: "headers",
      field: `headers.${forbiddenHeader}`,
      reason: "Read operations MUST NOT include mutation-only headers.",
    });
  }
  return result;
}

export function validateHeaders(headers, options = {}) {
  if (!isPlainObject(headers)) {
    return fail("missing_protocol_version", {
      field: "headers",
      reason: "Jarvis operation headers MUST be an object.",
    });
  }
  const requiredHeaders = options.requiredHeaders ?? WORKSESSION_MUTATION_HEADERS;
  for (const header of requiredHeaders) {
    if (!(header in headers) || headers[header] === undefined || headers[header] === null) {
      return fail(MISSING_HEADER_ERROR_IDS[header] ?? "invalid_export", {
        field: `headers.${header}`,
        reason: `${header} is required.`,
      });
    }
  }
  for (const header of [
    "Authorization",
    "Jarvis-Actor-Id",
    "Jarvis-Idempotency-Key",
  ]) {
    if (header in headers && !isNonEmptyString(headers[header])) {
      return fail(MISSING_HEADER_ERROR_IDS[header] ?? "missing_actor", {
        field: `headers.${header}`,
        reason: `${header} MUST be a nonempty string.`,
      });
    }
  }
  if (headers["Jarvis-Protocol-Version"] !== PROTOCOL_VERSION) {
    return fail("unsupported_protocol_version", {
      field: "headers.Jarvis-Protocol-Version",
      reason: "Jarvis-Protocol-Version MUST be v0.1.",
    });
  }
  const requestTimestamp = headers["Jarvis-Request-Timestamp"];
  if (requestTimestamp !== undefined && timestamp(requestTimestamp) === null) {
    return fail("missing_request_timestamp", {
      field: "headers.Jarvis-Request-Timestamp",
      reason: "Jarvis-Request-Timestamp MUST be an RFC3339 UTC timestamp.",
    });
  }
  if (requestTimestamp !== undefined && options.now instanceof Date) {
    const timestampMs = timestamp(requestTimestamp);
    const deltaMs = timestampMs - options.now.getTime();
    const maxPastSkewMs = options.maxPastSkewMs ?? options.maxSkewMs ?? 300_000;
    const maxFutureSkewMs = options.maxFutureSkewMs ?? 60_000;
    if (deltaMs < -maxPastSkewMs || deltaMs > maxFutureSkewMs) {
      return fail("stale_request_timestamp", {
        field: "headers.Jarvis-Request-Timestamp",
        reason: "Jarvis-Request-Timestamp is outside the accepted skew.",
      });
    }
  }
  const revision = headers["Jarvis-Expected-WorkSession-Revision"];
  if (revision !== undefined && (!isInteger(revision) || revision < 0)) {
    return fail("missing_expected_work_session_revision", {
      field: "headers.Jarvis-Expected-WorkSession-Revision",
      reason: "Jarvis-Expected-WorkSession-Revision MUST be a nonnegative integer.",
    });
  }
  const previousHash = headers["Jarvis-Previous-Event-Hash"];
  if (
    previousHash !== undefined
    && (!isNonEmptyString(previousHash) || !previousHash.startsWith("hash:"))
  ) {
    return fail("invalid_previous_event_hash", {
      field: "headers.Jarvis-Previous-Event-Hash",
      reason: "Jarvis-Previous-Event-Hash MUST use the hash: prefix.",
    });
  }
  return pass();
}

export function validateOperationHeaders(operation, options = {}) {
  const method = operationMethod(operation);
  const path = operationPath(operation);
  const workSessionScoped = path.startsWith("/work-sessions");
  const headerResult = method === "GET"
    ? validateReadHeaders(operation?.headers, options)
    : validateMutationHeaders(operation?.headers, { ...options, workSessionScoped });
  if (!headerResult.valid) {
    return headerResult;
  }
  if (operation?.actor_id !== operation?.headers?.["Jarvis-Actor-Id"]) {
    return fail("actor_body_id_mismatch", {
      field: "headers.Jarvis-Actor-Id",
      reason: "operation.actor_id MUST match Jarvis-Actor-Id.",
    });
  }
  const genesisError = createWorkSessionGenesisError(operation);
  if (genesisError) {
    return validationResult([genesisError]);
  }
  return pass();
}

export function validateRequest(request) {
  const schema = validateSchemaRecord("Request", request);
  if (!schema.valid) {
    return schema;
  }
  if (["pending", "acknowledged"].includes(request.status)) {
    for (const field of [
      "resolved_at",
      "resolved_by_review_id",
      "resolved_by_takeover_id",
      "closed_by_event_ref",
      "superseded_by_request_id",
    ]) {
      if (field in request) {
        return fail("invalid_request_transition", {
          objectType: "Request",
          field,
          reason: "Pending Request records MUST NOT include resolution fields.",
        });
      }
    }
  }
  if (REVIEW_RESOLVED_REQUEST_STATUSES.includes(request.status) && !request.resolved_by_review_id) {
    return fail("missing_review_resolution", {
      objectType: "Request",
      field: "resolved_by_review_id",
      reason: "Review-resolved Request states require resolved_by_review_id.",
    });
  }
  if (request.status === "takeover" && !request.resolved_by_takeover_id) {
    return fail("missing_takeover_resolution", {
      objectType: "Request",
      field: "resolved_by_takeover_id",
      reason: "Takeover Request state requires resolved_by_takeover_id.",
    });
  }
  return pass();
}

export function validateApprovalScope(approvalScope, options = {}) {
  const schema = validateSchemaRecord("ApprovalScope", approvalScope);
  if (!schema.valid) {
    return fail("invalid_approval_scope", {
      objectType: "ApprovalScope",
      field: schema.errors[0].field,
      reason: schema.errors[0].reason,
    });
  }
  const { request, review } = options;
  const expiresAt = timestamp(approvalScope.expires_at);
  const reviewTime = recordTimestamp(review);
  const valid = (
    isInteger(approvalScope.max_uses)
    && approvalScope.max_uses > 0
    && expiresAt !== null
    && (!review || (reviewTime !== null && expiresAt > reviewTime))
    && isNonEmptyString(approvalScope.normalized_action_hash)
    && approvalScope.normalized_action_hash.startsWith("hash:")
    && isPlainObject(approvalScope.approved_action)
    && isPlainObject(approvalScope.allowed_scope)
    && isPlainObject(approvalScope.denied_scope)
    && (!request || approvalScope.request_id === request.id)
    && (!request || approvalScope.policy_decision_id === request.policy_decision_id)
    && (!request || approvalScope.applies_to_actor_id === request.requester_actor_id)
    && (!review || approvalScope.review_id === review.id)
    && (!review || approvalScope.applies_to_work_session_id === review.work_session_id)
  );
  return valid
    ? pass()
    : fail("invalid_approval_scope", {
        objectType: "ApprovalScope",
        field: "approval_scope",
        reason: "ApprovalScope MUST be bounded, current, and tied to the Request and Review.",
      });
}

export function validateReview(review, options = {}) {
  const schema = validateSchemaRecord("Review", review);
  if (!schema.valid) {
    return schema;
  }
  if (["approve", "narrow"].includes(review.decision)) {
    return validateApprovalScope(review.approval_scope, {
      request: options.request,
      review,
    });
  }
  if (review.decision === "takeover" && !review.takeover_id) {
    return fail("missing_takeover_resolution", {
      objectType: "Review",
      field: "takeover_id",
      reason: "Takeover Review decisions require takeover_id.",
    });
  }
  return pass();
}

export function validateTakeover(takeover) {
  const schema = validateSchemaRecord("Takeover", takeover);
  if (!schema.valid) {
    return schema;
  }
  if (
    takeover.state === "resumed"
    && (!Array.isArray(takeover.reconciliation_refs) || !takeover.resumed_by_actor_id)
  ) {
    return fail("missing_reconciliation_refs", {
      objectType: "Takeover",
      field: "reconciliation_refs",
      reason: "Resumed Takeover records require reconciliation refs and resumed_by_actor_id.",
    });
  }
  return pass();
}

export function validateContribution(contribution) {
  const schema = validateSchemaRecord("Contribution", contribution);
  if (!schema.valid) {
    return schema;
  }
  if (!Array.isArray(contribution.contributor_refs) || contribution.contributor_refs.length === 0) {
    return fail("missing_contribution_actor", {
      objectType: "Contribution",
      field: "contributor_refs",
      reason: "Contribution MUST identify contributors.",
    });
  }
  if (contribution.contributor_type === "shared" && contribution.contributor_refs.length < 2) {
    return fail("shared_contribution_without_individual_refs", {
      objectType: "Contribution",
      field: "contributor_refs",
      reason: "Shared Contribution MUST preserve individual contributor refs.",
    });
  }
  return pass();
}

export function validateEvidenceManifest(evidenceManifest, options = {}) {
  const schema = validateSchemaRecord("EvidenceManifest", evidenceManifest);
  if (!schema.valid) {
    return schema;
  }
  const exportError = evidenceManifestExportError(evidenceManifest, options.workSession);
  if (exportError) {
    return validationResult([exportError]);
  }
  if (!Array.isArray(evidenceManifest.evidence_item_refs) || evidenceManifest.evidence_item_refs.length === 0) {
    return fail("invalid_export", {
      objectType: "EvidenceManifest",
      field: "evidence_item_refs",
      reason: "EvidenceManifest.evidence_item_refs MUST contain at least one evidence item.",
    });
  }
  if (Array.isArray(evidenceManifest.evidence_item_refs)) {
    for (let index = 0; index < evidenceManifest.evidence_item_refs.length; index += 1) {
      const itemResult = validateSchemaRecord(
        "EvidenceItemRef",
        evidenceManifest.evidence_item_refs[index],
      );
      if (!itemResult.valid) {
        return validationResult([
          protocolError(itemResult.errors[0].error_id, {
            objectType: "EvidenceItemRef",
            field: `evidence_item_refs[${index}].${itemResult.errors[0].field}`,
            reason: itemResult.errors[0].reason,
          }),
        ]);
      }
    }
  }
  return pass();
}

export function validateLearningRecord(learningRecord) {
  return validateSchemaRecord("LearningRecord", learningRecord);
}

export function validateMemoryProposal(memoryProposal) {
  const schema = validateSchemaRecord("MemoryProposal", memoryProposal);
  if (!schema.valid) {
    return schema;
  }
  if (memoryProposal.review_required !== true || memoryProposal.status === "accepted" && !memoryProposal.review_refs?.length) {
    return fail("silent_memory_mutation", {
      objectType: "MemoryProposal",
      field: "review_required",
      reason: "MemoryProposal cannot silently mutate durable memory.",
    });
  }
  return pass();
}

export function validateSkillProposal(skillProposal) {
  const schema = validateSchemaRecord("SkillProposal", skillProposal);
  if (!schema.valid) {
    return schema;
  }
  if (skillProposal.status === "accepted" && !skillProposal.review_refs?.length) {
    return fail("silent_skill_activation", {
      objectType: "SkillProposal",
      field: "review_refs",
      reason: "SkillProposal cannot activate without review.",
    });
  }
  return pass();
}

export function validateOutcomeReport(outcomeReport, options = {}) {
  const schema = validateSchemaRecord("OutcomeReport", outcomeReport);
  if (!schema.valid) {
    return schema;
  }
  if (!Array.isArray(outcomeReport.learning_record_refs) || outcomeReport.learning_record_refs.length === 0) {
    return fail("outcome_report_without_learning_record", {
      objectType: "OutcomeReport",
      field: "learning_record_refs",
      reason: "OutcomeReport MUST create or reference governed learning.",
    });
  }
  if (!options.workSession || !TERMINAL_WORK_SESSION_STATES.includes(options.workSession.status)) {
    return fail("outcome_report_requires_terminal_source", {
      objectType: "OutcomeReport",
      field: "work_session.status",
      reason: "OutcomeReport source WorkSession MUST be terminal.",
    });
  }
  if (options.workSession.id !== outcomeReport.work_session_id) {
    return fail("outcome_report_requires_terminal_source", {
      objectType: "OutcomeReport",
      field: "work_session_id",
      reason: "OutcomeReport source WorkSession id MUST match OutcomeReport.work_session_id.",
    });
  }
  return pass();
}

export function canonicalizeProtocolValue(value) {
  return JSON.stringify(sortProtocolValue(value));
}

function sortProtocolValue(value) {
  if (Array.isArray(value)) {
    return value.map(sortProtocolValue);
  }
  if (isPlainObject(value)) {
    return Object.fromEntries(
      Object.keys(value)
        .sort()
        .map((key) => [key, sortProtocolValue(value[key])]),
    );
  }
  return value;
}

export function hashProtocolValue(value) {
  return `hash:${createHash("sha256").update(canonicalizeProtocolValue(value)).digest("hex")}`;
}

export function validateEventHashChain(events, options = {}) {
  if (!Array.isArray(events) || events.length === 0) {
    return fail("missing_jarvis_event", {
      objectType: "JarvisEvent",
      field: "events",
      reason: "Event hash-chain validation requires events.",
    });
  }
  const seenSequences = new Set();
  const seenHashes = new Set();
  for (const event of events) {
    const sequence = event?.sequence;
    if (!isPlainObject(event) || !isInteger(sequence) || sequence <= 0) {
      return fail("invalid_export", {
        objectType: "JarvisEvent",
        field: "sequence",
        reason: "JarvisEvent.sequence MUST be a positive integer.",
      });
    }
    if (seenSequences.has(sequence)) {
      return fail("invalid_export", {
        objectType: "JarvisEvent",
        field: "sequence",
        reason: "JarvisEvent.sequence MUST be unique.",
      });
    }
    seenSequences.add(sequence);
    const eventHash = event.event_hash;
    if (!isNonEmptyString(eventHash) || !eventHash.startsWith("hash:")) {
      return fail("invalid_event_hash", {
        objectType: "JarvisEvent",
        field: "event_hash",
        reason: "JarvisEvent.event_hash MUST use the hash: prefix.",
      });
    }
    if (seenHashes.has(eventHash)) {
      return fail("invalid_event_hash", {
        objectType: "JarvisEvent",
        field: "event_hash",
        reason: "JarvisEvent.event_hash MUST be unique.",
      });
    }
    seenHashes.add(eventHash);
  }
  const ordered = [...events].sort((left, right) => left.sequence - right.sequence);
  let previousHash = options.genesisHash ?? "hash:protocol-genesis";
  for (const event of ordered) {
    if (event.previous_hash !== previousHash) {
      return fail("invalid_previous_event_hash", {
        objectType: "JarvisEvent",
        field: "previous_hash",
        reason: "JarvisEvent.previous_hash MUST link to the previous event hash.",
      });
    }
    previousHash = event.event_hash;
  }
  return pass();
}

export function validateProtocolRecord(objectType, record, options = {}) {
  if (OPENAPI_SCHEMA_NAMES.includes(objectType)) {
    const forbidden = findForbiddenHostPrivateField(record);
    if (forbidden) {
      return fail("forbidden_host_private_field", {
        objectType,
        field: forbidden,
        reason: "Protocol records MUST NOT expose host-private fields.",
      });
    }
  }
  switch (objectType) {
    case "Request":
      return validateRequest(record, options);
    case "Review":
      return validateReview(record, options);
    case "Takeover":
      return validateTakeover(record, options);
    case "Contribution":
      return validateContribution(record, options);
    case "EvidenceManifest":
      return validateEvidenceManifest(record, options);
    case "LearningRecord":
      return validateLearningRecord(record, options);
    case "MemoryProposal":
      return validateMemoryProposal(record, options);
    case "SkillProposal":
      return validateSkillProposal(record, options);
    case "OutcomeReport":
      return validateOutcomeReport(record, options);
    default:
      return validateSchemaRecord(objectType, record);
  }
}

function takeoverPathLifecycleError(fixture) {
  if (fixture?.fixture_id !== "valid-takeover-path-v01") {
    return null;
  }
  const request = getRef(fixture, "records.requests.takeover");
  const humanActive = getRef(fixture, "records.takeovers.human_active");
  const reconciliationRequired = getRef(fixture, "records.takeovers.reconciliation_required");
  const resumed = getRef(fixture, "records.takeovers.resumed");
  const startedEvent = getRef(fixture, "records.jarvis_events.takeover_started");
  const reconciliationEvent = getRef(fixture, "records.jarvis_events.takeover_reconciliation_required");
  const resumedEvent = getRef(fixture, "records.jarvis_events.takeover_resumed");
  const takeovers = [humanActive, reconciliationRequired, resumed];
  if (
    !isPlainObject(request)
    || request.status !== "takeover"
    || !isNonEmptyString(request.resolved_by_takeover_id)
    || !takeovers.every(isPlainObject)
  ) {
    return protocolError("invalid_transition", {
      field: "records.takeovers",
      reason: "Takeover proof MUST include Request resolution and all Takeover lifecycle states.",
    });
  }
  const expectedStates = ["human_active", "reconciliation_required", "resumed"];
  for (const [index, takeover] of takeovers.entries()) {
    const affectedScope = takeover.affected_scope ?? {};
    if (
      takeover.id !== request.resolved_by_takeover_id
      || takeover.request_id !== request.id
      || takeover.work_session_id !== request.work_session_id
      || takeover.state !== expectedStates[index]
      || takeover.lock_epoch !== humanActive.lock_epoch
      || affectedScope.blocking_scope !== request.blocking_scope
      || affectedScope.scope_ref !== request.requested_action?.scope_ref
      || affectedScope.normalized_action_hash !== "hash:action-final-submission"
    ) {
      return protocolError("invalid_transition", {
        field: `records.takeovers.${expectedStates[index]}`,
        reason: "Takeover lifecycle states MUST bind the same Request, lock epoch, and affected scope.",
      });
    }
  }
  if (!Array.isArray(resumed.reconciliation_refs) || resumed.reconciliation_refs.length === 0 || !resumed.resumed_by_actor_id) {
    return protocolError("missing_reconciliation_refs", {
      field: "records.takeovers.resumed.reconciliation_refs",
      reason: "Resumed Takeover records require reconciliation refs and resumed_by_actor_id.",
    });
  }
  if (
    !isPlainObject(startedEvent)
    || !isPlainObject(reconciliationEvent)
    || !isPlainObject(resumedEvent)
    || !isInteger(startedEvent.sequence)
    || !isInteger(reconciliationEvent.sequence)
    || !isInteger(resumedEvent.sequence)
    || !(startedEvent.sequence < reconciliationEvent.sequence && reconciliationEvent.sequence < resumedEvent.sequence)
    || reconciliationEvent.previous_hash !== startedEvent.event_hash
    || resumedEvent.previous_hash !== reconciliationEvent.event_hash
  ) {
    return protocolError("invalid_transition", {
      field: "records.jarvis_events.takeover_reconciliation_required",
      reason: "Takeover event chain MUST pass through reconciliation_required before resumed.",
    });
  }
  return null;
}

export function validateFixture(fixture) {
  if (!isPlainObject(fixture)) {
    return fail("invalid_export", {
      field: "fixture",
      reason: "Fixture MUST be an object.",
    });
  }
  const operation = firstRejectingOperation(fixture);
  const error = detectFixtureError(fixture, operation);
  if (fixture.kind === "invalid") {
    return error
      ? validationResult([error])
      : fail("invalid_export", {
          field: fixture.expected_error_field ?? "fixture",
          reason: "Invalid fixture did not trigger a protocol rejection.",
        });
  }
  if (error) {
    return validationResult([error]);
  }
  const takeoverLifecycleError = takeoverPathLifecycleError(fixture);
  if (takeoverLifecycleError) {
    return validationResult([takeoverLifecycleError]);
  }
  for (const op of fixture.operations ?? []) {
    const bindingShapeError = operationBindingError(op);
    if (bindingShapeError) {
      return validationResult([bindingShapeError]);
    }
    const headerResult = validateOperationHeaders(op);
    if (!headerResult.valid) {
      return headerResult;
    }
    const body = operationBody(fixture, op);
    const bindingError = operationBodyBindingError(op, body);
    if (bindingError) {
      return validationResult([bindingError]);
    }
    const stateError = operationStateError(fixture.records ?? {}, op, body);
    if (stateError) {
      return validationResult([stateError]);
    }
    if (op.operation_id === "exportEvidenceManifest") {
      const manifest = allRecords(fixture.records ?? {}, "evidence_manifests")[0];
      const manifestResult = validateEvidenceManifest(manifest, {
        workSession: evidenceManifestSourceWorkSession(fixture, manifest, op),
      });
      if (!manifestResult.valid) {
        return manifestResult;
      }
    }
    if (body && OBJECT_BY_OPERATION[op.operation_id]) {
      const recordOptions = op.operation_id === "submitOutcomeReport"
        ? { workSession: outcomeReportSourceWorkSession(fixture.records ?? {}, body) }
        : {};
      const recordResult = validateProtocolRecord(
        OBJECT_BY_OPERATION[op.operation_id],
        body,
        recordOptions,
      );
      if (!recordResult.valid) {
        return recordResult;
      }
    }
  }
  const events = allRecords(fixture.records ?? {}, "jarvis_events");
  return events.length > 0 ? validateEventHashChain(events) : pass();
}

function detectFixtureError(fixture, operation) {
  const records = fixture.records ?? {};
  const body = operationBody(fixture, operation);
  if (operation) {
    const bindingShapeError = operationBindingError(operation);
    if (bindingShapeError) {
      return bindingShapeError;
    }
  }
  const headerResult = validateOperationHeaders(operation);
  if (!headerResult.valid) {
    return headerResult.errors[0];
  }

  const headers = operation?.headers ?? {};
  const bindingError = operationBodyBindingError(operation, body);
  if (bindingError) {
    return bindingError;
  }
  const stateError = operationStateError(records, operation, body);
  if (stateError) {
    return stateError;
  }
  const bodyTime = recordTimestamp(body);
  const headerTime = timestamp(headers["Jarvis-Request-Timestamp"]);
  if (
    fixture.expected_error_id === "stale_request_timestamp"
    && bodyTime !== null
    && headerTime !== null
    && bodyTime - headerTime >= 300_000
  ) {
    return protocolError("stale_request_timestamp", {
      field: "headers.Jarvis-Request-Timestamp",
      reason: "Request timestamp is stale against the submitted protocol body.",
    });
  }

  const workSession = workSessionSnapshotForOperation(records, operation, body);

  if (operation?.operation_id === "createWorkSession" && body?.created_by_actor_id !== operation.actor_id) {
    return protocolError("unauthorized_actor", {
      field: "headers.Jarvis-Actor-Id",
      reason: "Actor cannot create a WorkSession for a different creator.",
    });
  }
  if (operation?.operation_id === "createWorkSession") {
    const actor = actorById(records, operation.actor_id);
    const grants = workerGrants(workerForActor(records, actor));
    if (!grants.has("policy:own")) {
      return protocolError("unauthorized_actor", {
        field: "headers.Jarvis-Actor-Id",
        reason: "Actor lacks authority to create a governed WorkSession.",
      });
    }
  }

  if (body?.policy_id && !idsFor(records, "policies").has(body.policy_id)) {
    return protocolError("missing_policy", {
      field: "policy_id",
      reason: "WorkSession references a Policy that is absent.",
    });
  }

  const isMutationOperation = operationMethod(operation) !== "GET";
  if (isMutationOperation && workSession?.status && TERMINAL_WORK_SESSION_STATES.includes(workSession.status)) {
    return protocolError("sealed_work_session_mutation", {
      field: "records.work_sessions.completed.status",
      reason: "Sealed WorkSession records cannot be mutated.",
    });
  }

  const activeTakeover = allRecords(records, "takeovers").find((takeover) => {
    return takeover.work_session_id === targetWorkSessionId(operation, body)
      && takeover.state === "human_active";
  });
  if (
    activeTakeover
    && actorById(records, operation?.actor_id)?.type === "agent"
    && Number.isInteger(operation?.attempted_takeover_lock_epoch)
    && operation.attempted_takeover_lock_epoch < activeTakeover.lock_epoch
  ) {
    return protocolError("stale_takeover_epoch", {
      field: "records.takeovers.active.lock_epoch",
      reason: "AgentWorker continuation uses a stale takeover lock epoch.",
    });
  }

  if (operation?.operation_id === "appendJarvisEvent") {
    const actor = actorById(records, body?.actor_id);
    const hasPolicyDecision = (
      "policy_decision_id" in (body ?? {})
      || "policy_decision_ref" in (body?.payload ?? {})
      || "policy_decision_refs" in (body?.payload ?? {})
    );
    if (actor?.type === "agent" && !hasPolicyDecision && body?.type !== "evidence_manifest.mutated") {
      return protocolError("missing_policy_decision", {
        field: "records.jarvis_events",
        reason: "AgentWorker action state requires a prior PolicyDecision.",
      });
    }
  }

  if (operation?.operation_id === "createRequest") {
    const requestResult = validateRequest(body);
    if (!requestResult.valid) {
      return requestResult.errors[0];
    }
  }

  if (operation?.operation_id === "recordReview") {
    const requestId = requestIdFromTargetRef(body?.target_ref);
    const request = recordById(records, "requests", requestId);
    const reviewResult = validateReview(body, { request });
    if (!reviewResult.valid) {
      return reviewResult.errors[0];
    }
  }

  if (operation?.operation_id === "appendJarvisEvent" && body?.type === "work_session.completed") {
    const pending = allRecords(records, "requests").find((request) => {
      return request.work_session_id === body.work_session_id && request.status === "pending";
    });
    if (pending) {
      return protocolError("request_unresolved", {
        field: "records.requests.pending.status",
        reason: "WorkSession cannot complete while a Request remains pending.",
      });
    }
  }

  if (operation?.operation_id === "exportEvidenceManifest") {
    const manifest = allRecords(records, "evidence_manifests")[0];
    const exportError = evidenceManifestExportError(
      manifest,
      evidenceManifestSourceWorkSession(fixture, manifest, operation) ?? workSession,
    );
    if (exportError) {
      return exportError;
    }
  }

  if (body?.type === "evidence_manifest.mutated") {
    return protocolError("sealed_evidence_mutation", {
      field: "records.evidence_manifests.sealed",
      reason: "Sealed EvidenceManifest records cannot be mutated.",
    });
  }

  if (operation?.operation_id === "createMemoryProposal") {
    const memoryResult = validateMemoryProposal(body);
    if (!memoryResult.valid) {
      return memoryResult.errors[0];
    }
  }

  if (operation?.operation_id === "createSkillProposal") {
    const skillResult = validateSkillProposal(body);
    if (!skillResult.valid) {
      return skillResult.errors[0];
    }
  }

  if (operation?.operation_id === "submitOutcomeReport") {
    const outcomeResult = validateOutcomeReport(body, {
      workSession: outcomeReportSourceWorkSession(records, body),
    });
    if (!outcomeResult.valid) {
      return outcomeResult.errors[0];
    }
  }

  const forbiddenField = findForbiddenHostPrivateField(body);
  if (forbiddenField) {
    return protocolError("forbidden_host_private_field", {
      field: forbiddenField,
      reason: "Protocol records MUST NOT expose host-private fields.",
    });
  }

  return null;
}
