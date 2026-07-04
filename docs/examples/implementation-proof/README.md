# Existing-Agent Implementation Proof

This directory contains Jarvis implementation-proof records.

Jarvis records protocol state. Hosts own native execution.

## Proofs

- [native-coding-agent/README.md](./native-coding-agent/README.md) - SDK-helper
  generated proof for one LangGraph StateGraph coding-agent collaboration loop.
- [live-agent-frameworks/README.md](./live-agent-frameworks/README.md) -
  live external-host proof for LangGraph, DeepAgents, and AgentScope with
  OpenAI model execution mapped into Jarvis protocol records.

## Boundary

Implementation proof records do not define runtime behavior, host UI, storage,
auth, model calls, tool execution, billing, scoring, payment, deployment,
monitoring, host integration, adapters, wrappers, or host workflow.

The proofs validate protocol records, committed native framework traces,
trace-to-record mappings, hash linkage, operation ordering, fixture shape, and
live framework evidence exports.

## Validation

Validate the proof from the repository root:

```bash
python3 scripts/check_implementation_proof.py
```

Regenerate the proof from SDK helpers:

```bash
python3 scripts/generate_implementation_proof.py
```

The checker rejects stale proof output.
