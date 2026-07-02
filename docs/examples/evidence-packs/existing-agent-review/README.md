# Existing-Agent Review Evidence Pack

This evidence pack shows one existing-agent collaboration loop as Jarvis v0.1
protocol records.

Jarvis records protocol state. Hosts own native execution.

## Boundary

This pack does not define adapter code, wrapper code, host runtime behavior,
host UI, model calls, tool execution, storage, auth, billing, scoring, payment,
deployment, monitoring, host integration, or host workflow.

The pack uses
[docs/conformance/fixtures/valid/golden-path.json](../../../conformance/fixtures/valid/golden-path.json)
as its source fixture and extracts a public record bundle from it. The records
show:

- HumanWorker and AgentWorker participant records
- WorkSession and Policy records
- PolicyDecision before accepted AgentWorker state
- scoped Request
- HumanWorker Review with bounded ApprovalScope
- Contribution attribution
- EvidenceManifest export from a terminal WorkSession
- governed LearningRecord, MemoryProposal, and SkillProposal
- OutcomeReport from a terminal source WorkSession
- operation headers for mutation and read surfaces
- JarvisEvent hash-chain validation

## Files

```txt
manifest.json
records/
evidence/evidence-manifest.json
events/event-chain.json
headers/
```

`manifest.json` defines the source fixture refs, record files, context refs,
EvidenceManifest source, event chain, and operation header checks.

Record files use the helper-compatible envelope:

```json
{
  "object_type": "Request",
  "record": {}
}
```

Records that require protocol context include only the minimum protocol context
needed for validation. Context does not add host runtime state.

## Validation

Validate all evidence packs from the repository root:

```bash
python3 scripts/check_example_evidence_packs.py
```

Validate one record with the CLI:

```bash
node packages/cli/src/index.js validate record docs/examples/evidence-packs/existing-agent-review/records/request-approved.json
```

Validate the EvidenceManifest export:

```bash
node packages/cli/src/index.js validate evidence-manifest docs/examples/evidence-packs/existing-agent-review/evidence/evidence-manifest.json
```

Validate the event hash chain:

```bash
node packages/cli/src/index.js check hash-chain docs/examples/evidence-packs/existing-agent-review/events/event-chain.json
```

The evidence pack proves record compatibility only. It does not certify an
implementation, does not claim production adoption, and does not define host
execution.
