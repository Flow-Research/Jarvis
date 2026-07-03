import assert from "node:assert/strict";
import { readdirSync, readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";

import { validateFixture } from "../src/index.js";

const packageRoot = dirname(dirname(fileURLToPath(import.meta.url)));
const fixtureRoot = join(packageRoot, "fixtures/v0.1");

function readJson(path) {
  return JSON.parse(readFileSync(path, "utf8"));
}

test("valid golden-path fixture is accepted", () => {
  const fixture = readJson(join(fixtureRoot, "valid/golden-path.json"));
  const result = validateFixture(fixture);
  assert.equal(result.valid, true, JSON.stringify(result.errors, null, 2));
});

test("valid takeover-path fixture is accepted", () => {
  const fixture = readJson(join(fixtureRoot, "valid/takeover-path.json"));
  const result = validateFixture(fixture);
  assert.equal(result.valid, true, JSON.stringify(result.errors, null, 2));
});

test("takeover-path fixture requires reconciliation before resume", () => {
  const fixture = readJson(join(fixtureRoot, "valid/takeover-path.json"));
  fixture.records.takeovers.reconciliation_required.state = "resumed";
  const result = validateFixture(fixture);
  assert.equal(result.valid, false);
  assert.equal(result.errors[0]?.error_id, "invalid_transition");
});

test("takeover-path fixture requires resumed reconciliation refs", () => {
  const fixture = readJson(join(fixtureRoot, "valid/takeover-path.json"));
  fixture.records.takeovers.resumed.reconciliation_refs = [];
  const result = validateFixture(fixture);
  assert.equal(result.valid, false);
  assert.equal(result.errors[0]?.error_id, "missing_reconciliation_refs");
});

test("golden-path OutcomeReport requires a terminal WorkSession source", () => {
  const fixture = readJson(join(fixtureRoot, "valid/golden-path.json"));
  fixture.records.work_sessions.outcome_active = {
    ...fixture.records.work_sessions.active,
    id: "ws-outcome-active",
  };
  fixture.records.outcome_reports.post_session.work_session_id = "ws-outcome-active";
  const result = validateFixture(fixture);
  assert.equal(result.valid, false);
  assert.equal(result.errors[0]?.error_id, "outcome_report_requires_terminal_source");
});

test("fixture validation binds operation body Actor fields to Actor header", () => {
  const fixture = readJson(join(fixtureRoot, "valid/golden-path.json"));
  fixture.records.reviews.approve_source.reviewer_actor_id = "actor-agent-golden";
  const result = validateFixture(fixture);
  assert.equal(result.valid, false);
  assert.equal(result.errors[0]?.error_id, "actor_body_id_mismatch");
});

test("fixture validation enforces WorkSession genesis headers", () => {
  const fixture = readJson(join(fixtureRoot, "valid/golden-path.json"));
  const operation = fixture.operations.find((op) => op.operation_id === "createWorkSession");
  operation.headers["Jarvis-Expected-WorkSession-Revision"] = 1;
  const result = validateFixture(fixture);
  assert.equal(result.valid, false);
  assert.equal(result.errors[0]?.error_id, "stale_work_session_revision");
});

test("fixture validation rejects unrepresented WorkSession previous hash", () => {
  const fixture = readJson(join(fixtureRoot, "valid/golden-path.json"));
  const operation = fixture.operations.find((op) => op.operation_id === "recordReview");
  operation.headers["Jarvis-Expected-WorkSession-Revision"] = 999;
  operation.headers["Jarvis-Previous-Event-Hash"] = "hash:unrepresented";
  const result = validateFixture(fixture);
  assert.equal(result.valid, false);
  assert.equal(result.errors[0]?.error_id, "invalid_previous_event_hash");
});

test("fixture validation rejects operation-id read downgrade", () => {
  const fixture = readJson(join(fixtureRoot, "valid/golden-path.json"));
  const operation = fixture.operations.find((op) => op.operation_id === "createRequest");
  operation.method = "GET";
  operation.path = "/work-sessions/ws-golden-001/export";
  operation.headers = {
    Authorization: "HostAuth fixture",
    "Jarvis-Protocol-Version": "v0.1",
    "Jarvis-Actor-Id": operation.actor_id,
  };
  const result = validateFixture(fixture);
  assert.equal(result.valid, false);
  assert.equal(result.errors[0]?.error_id, "invalid_export");
  assert.equal(result.errors[0]?.field, "method");
});

test("fixture validation rejects operation path and status drift", () => {
  const pathFixture = readJson(join(fixtureRoot, "valid/golden-path.json"));
  const pathOperation = pathFixture.operations.find((op) => op.operation_id === "createRequest");
  pathOperation.path = "/work-sessions/ws-golden-001/export";
  const pathResult = validateFixture(pathFixture);
  assert.equal(pathResult.valid, false);
  assert.equal(pathResult.errors[0]?.error_id, "invalid_export");
  assert.equal(pathResult.errors[0]?.field, "path");

  const statusFixture = readJson(join(fixtureRoot, "valid/golden-path.json"));
  const statusOperation = statusFixture.operations.find((op) => op.operation_id === "createRequest");
  statusOperation.expected_status = 418;
  const statusResult = validateFixture(statusFixture);
  assert.equal(statusResult.valid, false);
  assert.equal(statusResult.errors[0]?.error_id, "invalid_export");
  assert.equal(statusResult.errors[0]?.field, "expected_status");
});

test("fixture validation rejects host-private cookie fields in exports", () => {
  const fixture = readJson(join(fixtureRoot, "valid/golden-path.json"));
  fixture.records.evidence_manifests.portable_export.evidence_item_refs[0].cookie = "secret";
  const result = validateFixture(fixture);
  assert.equal(result.valid, false);
  assert.equal(result.errors[0]?.error_id, "forbidden_host_private_field");
});

test("fixture validation rejects unknown nested EvidenceItemRef fields", () => {
  const fixture = readJson(join(fixtureRoot, "valid/golden-path.json"));
  fixture.records.evidence_manifests.portable_export.evidence_item_refs[0].unexpected_extra = "host";
  const result = validateFixture(fixture);
  assert.equal(result.valid, false);
  assert.equal(result.errors[0]?.error_id, "invalid_export");
});

test("fixture validation allows read-only fetch from terminal WorkSession state", () => {
  const fixture = readJson(join(fixtureRoot, "valid/golden-path.json"));
  fixture.records.work_sessions = {
    completed: fixture.records.work_sessions.completed,
    genesis_request: fixture.records.work_sessions.genesis_request,
    active: fixture.records.work_sessions.active,
  };
  fixture.operations.unshift({
    operation_id: "getWorkSession",
    method: "GET",
    path: "/work-sessions/ws-golden-001",
    headers: {
      Authorization: "HostAuth fixture",
      "Jarvis-Protocol-Version": "v0.1",
      "Jarvis-Actor-Id": "actor-human-golden",
    },
    actor_id: "actor-human-golden",
    work_session_id: "ws-golden-001",
    expected_status: 200,
  });
  const result = validateFixture(fixture);
  assert.equal(result.valid, true, JSON.stringify(result.errors, null, 2));
});

test("invalid fixture set is rejected with expected protocol errors", () => {
  const invalidRoot = join(fixtureRoot, "invalid");
  for (const fileName of readdirSync(invalidRoot).filter((name) => name.endsWith(".json"))) {
    const fixture = readJson(join(invalidRoot, fileName));
    const result = validateFixture(fixture);
    assert.equal(result.valid, false, `${fileName} should be rejected`);
    assert.equal(
      result.errors[0]?.error_id,
      fixture.expected_error_id,
      `${fileName} should reject as ${fixture.expected_error_id}`,
    );
  }
});
