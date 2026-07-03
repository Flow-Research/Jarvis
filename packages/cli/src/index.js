#!/usr/bin/env node

import { readFileSync, readdirSync, realpathSync, statSync } from "node:fs";
import { dirname, relative, resolve, sep } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const CLI_PROTOCOL_VERSION = "v0.1";

const OPERATION_CONTEXT = Object.freeze({
  registerWorker: {
    method: "PUT",
    path: "/workers/{worker_id}",
    operationClass: "non_worksession_mutation",
  },
  registerActor: {
    method: "PUT",
    path: "/actors/{actor_id}",
    operationClass: "non_worksession_mutation",
  },
  createWorkSession: {
    method: "POST",
    path: "/work-sessions",
    operationClass: "worksession_genesis_mutation",
  },
  getWorkSession: {
    method: "GET",
    path: "/work-sessions/{work_session_id}",
    operationClass: "worksession_scoped_read",
  },
  appendJarvisEvent: {
    method: "POST",
    path: "/work-sessions/{work_session_id}/events",
    operationClass: "worksession_scoped_mutation",
  },
  recordPolicyDecision: {
    method: "POST",
    path: "/work-sessions/{work_session_id}/policy-decisions",
    operationClass: "worksession_scoped_mutation",
  },
  createRequest: {
    method: "POST",
    path: "/work-sessions/{work_session_id}/requests",
    operationClass: "worksession_scoped_mutation",
  },
  recordReview: {
    method: "POST",
    path: "/work-sessions/{work_session_id}/reviews",
    operationClass: "worksession_scoped_mutation",
  },
  recordTakeover: {
    method: "POST",
    path: "/work-sessions/{work_session_id}/takeovers",
    operationClass: "worksession_scoped_mutation",
  },
  recordContribution: {
    method: "POST",
    path: "/work-sessions/{work_session_id}/contributions",
    operationClass: "worksession_scoped_mutation",
  },
  createLearningRecord: {
    method: "POST",
    path: "/work-sessions/{work_session_id}/learning-records",
    operationClass: "worksession_scoped_mutation",
  },
  createMemoryProposal: {
    method: "POST",
    path: "/work-sessions/{work_session_id}/memory-proposals",
    operationClass: "worksession_scoped_mutation",
  },
  createSkillProposal: {
    method: "POST",
    path: "/work-sessions/{work_session_id}/skill-proposals",
    operationClass: "worksession_scoped_mutation",
  },
  exportEvidenceManifest: {
    method: "GET",
    path: "/work-sessions/{work_session_id}/export",
    operationClass: "export_read",
  },
  submitOutcomeReport: {
    method: "POST",
    path: "/outcome-reports",
    operationClass: "non_worksession_mutation",
  },
});

const ACCEPTED_OPERATION_CLASSES = new Set([
  "worksession_scoped_mutation",
  "worksession_genesis_mutation",
  "non_worksession_mutation",
  "worksession_scoped_read",
  "export_read",
]);

const REQUIRED_FIXTURE_PATHS = Object.freeze([
  "valid/golden-path.json",
  "valid/takeover-path.json",
  "invalid/forbidden-host-private-export-field.json",
  "invalid/invalid-approval-scope.json",
  "invalid/invalid-evidence-export-state.json",
  "invalid/invalid-previous-event-hash.json",
  "invalid/missing-actor.json",
  "invalid/missing-expected-work-session-revision.json",
  "invalid/missing-idempotency-key.json",
  "invalid/missing-policy-decision.json",
  "invalid/missing-policy.json",
  "invalid/missing-previous-event-hash.json",
  "invalid/missing-protocol-version.json",
  "invalid/missing-request-timestamp.json",
  "invalid/missing-review-resolution.json",
  "invalid/missing-takeover-resolution.json",
  "invalid/outcome-report-without-learning-record.json",
  "invalid/outcome-report-requires-terminal-source.json",
  "invalid/sealed-evidence-mutation.json",
  "invalid/sealed-work-session-mutation.json",
  "invalid/silent-memory-mutation.json",
  "invalid/silent-skill-activation.json",
  "invalid/stale-request-timestamp.json",
  "invalid/stale-takeover-continuation.json",
  "invalid/stale-work-session-revision.json",
  "invalid/unauthorized-actor.json",
  "invalid/unresolved-request.json",
]);

export async function runCli(args, io = defaultIo()) {
  let sdk;
  try {
    sdk = await loadSdk();
    const parsed = parseArgs(args);
    const outcome = await dispatch(sdk, parsed);
    writeJson(io.stdout, outcome.payload);
    return outcome.code;
  } catch (error) {
    const reason = error instanceof Error ? error.message : String(error);
    writeJson(io.stdout, {
      protocol_version: sdk?.PROTOCOL_VERSION ?? CLI_PROTOCOL_VERSION,
      command: "jarvis",
      passed: false,
      valid: false,
      errors: [cliProtocolError(sdk, "argv", reason)],
    });
    return 1;
  }
}

function cliProtocolError(sdk, field, reason) {
  if (sdk?.protocolError) {
    return sdk.protocolError("invalid_export", {
      objectType: "CLI",
      field,
      reason,
      remediation: "Run a supported Jarvis CLI command with the required input file.",
      traceId: "trace:jarvis-cli",
    });
  }
  return {
    error_id: "invalid_export",
    protocol_version: CLI_PROTOCOL_VERSION,
    object_type: "CLI",
    field,
    reason,
    remediation: "Run a supported Jarvis CLI command with the required input file.",
    trace_id: "trace:jarvis-cli",
  };
}

async function loadSdk() {
  try {
    return await import("@jarvis-protocol/sdk");
  } catch (error) {
    if (
      error?.code !== "ERR_MODULE_NOT_FOUND"
      || !String(error?.message ?? "").includes("@jarvis-protocol/sdk")
    ) {
      throw error;
    }
    const here = dirname(fileURLToPath(import.meta.url));
    const localSdk = resolve(here, "../../typescript/src/index.js");
    return import(pathToFileURL(localSdk).href);
  }
}

function defaultIo() {
  return {
    stdout: process.stdout,
    stderr: process.stderr,
  };
}

function parseArgs(args) {
  const positionals = [];
  const flags = {};
  for (let index = 0; index < args.length; index += 1) {
    const arg = args[index];
    if (arg.startsWith("--")) {
      const key = arg.slice(2);
      const value = args[index + 1];
      if (!value || value.startsWith("--")) {
        throw new Error(`--${key} requires a value.`);
      }
      flags[key] = value;
      index += 1;
    } else {
      positionals.push(arg);
    }
  }
  return { positionals, flags };
}

async function dispatch(sdk, parsed) {
  const [group, action, target] = parsed.positionals;
  if (group === "validate" && action === "fixture") {
    return validateFixtureCommand(sdk, requiredPath(target));
  }
  if (group === "validate" && action === "fixtures") {
    return validateFixturesCommand(sdk, requiredPath(target));
  }
  if (group === "validate" && action === "record") {
    return validateRecordCommand(sdk, requiredPath(target));
  }
  if (group === "validate" && action === "evidence-manifest") {
    return validateEvidenceManifestCommand(sdk, requiredPath(target));
  }
  if (group === "check" && action === "headers") {
    return checkHeadersCommand(sdk, requiredPath(target), parsed.flags);
  }
  if (group === "check" && action === "hash-chain") {
    return checkHashChainCommand(sdk, requiredPath(target));
  }
  if (group === "list" && action === "rejection-ids") {
    return listRejectionIdsCommand(sdk);
  }
  if (group === "print" && action === "compatibility-claim") {
    return compatibilityClaimCommand(sdk);
  }
  throw new Error(`Unsupported command: ${parsed.positionals.join(" ")}`);
}

function requiredPath(value) {
  if (!value) {
    throw new Error("Input path is required.");
  }
  return value;
}

function validateFixtureCommand(sdk, file) {
  const fixture = readJsonFile(file);
  const result = fixtureRunResult(sdk, fixture, file);
  return {
    code: result.passed ? 0 : 1,
    payload: result,
  };
}

function validateFixturesCommand(sdk, directory) {
  const root = resolve(directory);
  const files = collectJsonFiles(root);
  const results = files.map((file) => fixtureRunResult(sdk, readJsonFile(file), file));
  const fixtureSetError = fixtureSetCompletenessError(sdk, root, files);
  const passed = !fixtureSetError && results.every((result) => result.passed);
  return {
    code: passed ? 0 : 1,
    payload: {
      protocol_version: sdk.PROTOCOL_VERSION,
      command: "validate fixtures",
      directory,
      passed,
      fixture_count: results.length,
      errors: fixtureSetError ? [fixtureSetError] : [],
      results,
    },
  };
}

function validateRecordCommand(sdk, file) {
  const input = readJsonFile(file);
  const objectType = input.object_type ?? input.objectType;
  if (!objectType) {
    return failureOutcome(sdk, "validate record", "record.object_type", "Record input MUST include object_type.");
  }
  const record = input.record ?? input.body;
  if (record === undefined) {
    return failureOutcome(sdk, "validate record", "record", "Record input MUST include record.");
  }
  const result = sdk.validateProtocolRecord(objectType, record, input.context ?? input.options ?? {});
  return validationOutcome(sdk, "validate record", result, { file, object_type: objectType });
}

function validateEvidenceManifestCommand(sdk, file) {
  const input = readJsonFile(file);
  const manifest = input.evidence_manifest ?? input.evidenceManifest ?? input.record;
  if (manifest === undefined) {
    return failureOutcome(
      sdk,
      "validate evidence-manifest",
      "evidence_manifest",
      "EvidenceManifest input MUST include evidence_manifest, evidenceManifest, or record.",
    );
  }
  const workSession = input.work_session ?? input.workSession;
  const result = sdk.validateEvidenceManifest(manifest, { workSession });
  return validationOutcome(sdk, "validate evidence-manifest", result, { file });
}

function checkHeadersCommand(sdk, file, flags) {
  const input = readJsonFile(file);
  const headers = input.headers ?? input;
  const operationId = flags["operation-id"] ?? input.operation_id;
  const operationClass = flags["operation-class"] ?? input.operation_class;
  if (operationId) {
    const context = OPERATION_CONTEXT[operationId];
    if (!context) {
      return failureOutcome(sdk, "check headers", "operation_id", `Unsupported operation_id: ${operationId}`);
    }
    const operation = {
      ...input,
      operation_id: operationId,
      method: context.method,
      path: context.path,
      actor_id: input.actor_id ?? input.actorId ?? headers["Jarvis-Actor-Id"],
      expected_status: input.expected_status ?? 200,
      headers,
    };
    const result = sdk.validateOperationHeaders(operation);
    return validationOutcome(sdk, "check headers", result, {
      file,
      operation_id: operationId,
      operation_class: context.operationClass,
    });
  }
  if (!operationClass) {
    return failureOutcome(
      sdk,
      "check headers",
      "operation_class",
      "Header checks MUST include --operation-id or --operation-class.",
    );
  }
  if (!ACCEPTED_OPERATION_CLASSES.has(operationClass)) {
    return failureOutcome(sdk, "check headers", "operation_class", `Unsupported operation_class: ${operationClass}`);
  }
  const result = validateHeadersByOperationClass(sdk, headers, operationClass);
  return validationOutcome(sdk, "check headers", result, {
    file,
    operation_class: operationClass,
  });
}

function validateHeadersByOperationClass(sdk, headers, operationClass) {
  if (operationClass === "worksession_scoped_mutation") {
    return sdk.validateMutationHeaders(headers, { workSessionScoped: true });
  }
  if (operationClass === "non_worksession_mutation") {
    return sdk.validateMutationHeaders(headers, { workSessionScoped: false });
  }
  if (operationClass === "worksession_scoped_read" || operationClass === "export_read") {
    return sdk.validateReadHeaders(headers);
  }
  const mutationResult = sdk.validateMutationHeaders(headers, { workSessionScoped: true });
  if (!mutationResult.valid) {
    return mutationResult;
  }
  if (headers["Jarvis-Expected-WorkSession-Revision"] !== 0) {
    return {
      valid: false,
      errors: [
        sdk.protocolError("stale_work_session_revision", {
          objectType: "headers",
          field: "headers.Jarvis-Expected-WorkSession-Revision",
          reason: "WorkSession genesis mutation MUST use expected revision 0.",
          traceId: "trace:jarvis-cli",
        }),
      ],
    };
  }
  if (headers["Jarvis-Previous-Event-Hash"] !== "hash:protocol-genesis") {
    return {
      valid: false,
      errors: [
        sdk.protocolError("invalid_previous_event_hash", {
          objectType: "headers",
          field: "headers.Jarvis-Previous-Event-Hash",
          reason: "WorkSession genesis mutation MUST use hash:protocol-genesis.",
          traceId: "trace:jarvis-cli",
        }),
      ],
    };
  }
  return mutationResult;
}

function checkHashChainCommand(sdk, file) {
  const input = readJsonFile(file);
  const events = extractEvents(input);
  const result = sdk.validateEventHashChain(events);
  return validationOutcome(sdk, "check hash-chain", result, { file });
}

function listRejectionIdsCommand(sdk) {
  return {
    code: 0,
    payload: {
      protocol_version: sdk.PROTOCOL_VERSION,
      command: "list rejection-ids",
      passed: true,
      rejection_ids: sdk.SCHEMA_ENUMS.ProtocolErrorId ?? [],
    },
  };
}

function compatibilityClaimCommand(sdk) {
  return {
    code: 0,
    payload: {
      protocol_version: sdk.PROTOCOL_VERSION,
      command: "print compatibility-claim",
      passed: true,
      compatibility_claim: {
        implementation: "<name> <implementation-version>",
        "protocol compatibility": `Jarvis ${sdk.PROTOCOL_VERSION}`,
        "conformance surface": "<conformance-surface>",
        "verification date": "<YYYY-MM-DD>",
        verifier: "self-attested",
        evidence: "<evidence-ref-or-artifact-hash>",
        "fixture or checklist basis": "Jarvis v0.1 conformance fixtures and checklist",
        implementation_version: "<implementation-version>",
        status: "implementation claim, not certification",
        statement: "This implementation claims Jarvis v0.1 compatibility for the listed protocol surfaces.",
        required_evidence: [
          "valid fixture run",
          "invalid fixture run with expected rejection ids",
          "mutation-header validation",
          "read-header validation",
          "event hash-chain validation",
          "EvidenceManifest export validation",
        ],
        boundary: "Jarvis compatibility does not certify host runtime, storage, auth, UI, model, tool, billing, deployment, or workflow behavior.",
      },
    },
  };
}

function validationOutcome(sdk, command, result, extra = {}) {
  return {
    code: result.valid ? 0 : 1,
    payload: {
      protocol_version: sdk.PROTOCOL_VERSION,
      command,
      passed: result.valid,
      valid: result.valid,
      errors: result.errors,
      ...extra,
    },
  };
}

function failureOutcome(sdk, command, field, reason) {
  return {
    code: 1,
    payload: {
      protocol_version: sdk.PROTOCOL_VERSION,
      command,
      passed: false,
      valid: false,
      errors: [
        sdk.protocolError("invalid_export", {
          objectType: "CLI",
          field,
          reason,
          traceId: "trace:jarvis-cli",
        }),
      ],
    },
  };
}

function fixtureRunResult(sdk, fixture, file) {
  const result = sdk.validateFixture(fixture);
  const expectedResult = fixture.expected_result;
  const expectedErrorId = fixture.expected_error_id;
  const errorId = result.errors[0]?.error_id;
  const rejectedExpected = expectedResult === "reject";
  const acceptedExpected = expectedResult === "pass";
  const passed = rejectedExpected
    ? Boolean(expectedErrorId) && result.valid === false && errorId === expectedErrorId
    : acceptedExpected && result.valid === true;
  return {
    protocol_version: sdk.PROTOCOL_VERSION,
    command: "validate fixture",
    file,
    fixture_id: fixture.fixture_id,
    expected_result: expectedResult,
    expected_error_id: expectedErrorId,
    passed,
    valid: result.valid,
    errors: result.errors,
  };
}

function fixtureSetCompletenessError(sdk, root, files) {
  const observed = new Set(files.map((file) => relative(root, file).split(sep).join("/")));
  const required = new Set(REQUIRED_FIXTURE_PATHS);
  const missing = REQUIRED_FIXTURE_PATHS.filter((path) => !observed.has(path));
  const extra = [...observed].filter((path) => !required.has(path)).sort();
  if (missing.length === 0 && extra.length === 0) {
    return null;
  }
  return sdk.protocolError("invalid_export", {
    objectType: "FixtureSet",
    field: "fixtures",
    reason: "Fixture directory MUST contain the complete Jarvis v0.1 fixture snapshot.",
    remediation: `Missing: ${missing.join(", ") || "none"}. Extra: ${extra.join(", ") || "none"}.`,
    traceId: "trace:jarvis-cli",
  });
}

function readJsonFile(path) {
  const text = readFileSync(resolve(path), "utf8");
  return JSON.parse(text);
}

function collectJsonFiles(directory) {
  const root = resolve(directory);
  const entries = [];
  function visit(path) {
    const stat = statSync(path);
    if (stat.isDirectory()) {
      for (const entry of readdirSync(path).sort()) {
        visit(resolve(path, entry));
      }
      return;
    }
    if (path.endsWith(".json")) {
      entries.push(path);
    }
  }
  visit(root);
  return entries;
}

function extractEvents(input) {
  if (Array.isArray(input)) {
    return input;
  }
  if (Array.isArray(input.events)) {
    return input.events;
  }
  if (input.records?.jarvis_events && typeof input.records.jarvis_events === "object") {
    return Object.values(input.records.jarvis_events);
  }
  if (input.jarvis_events && typeof input.jarvis_events === "object") {
    return Object.values(input.jarvis_events);
  }
  throw new Error("Hash-chain input MUST be an event array or contain events.");
}

function writeJson(stream, value) {
  stream.write(`${JSON.stringify(value, null, 2)}\n`);
}

function isDirectRun() {
  return process.argv[1]
    && realpathSync(resolve(process.argv[1])) === realpathSync(fileURLToPath(import.meta.url));
}

if (isDirectRun()) {
  runCli(process.argv.slice(2)).then((code) => {
    process.exitCode = code;
  });
}
