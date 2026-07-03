# Jarvis Examples

Jarvis examples show protocol records only.

They do not define runtime behavior, host UI, storage, auth, model calls, tool
execution, billing, scoring, payment, deployment, monitoring, host integration,
adapters, wrappers, SDK implementation, or host workflow.

## Public Examples

- [protocol-records.md](./protocol-records.md) - concrete v0.1 protocol record
  examples for one human-agent collaboration loop.
- [existing-agent-compatibility.md](./existing-agent-compatibility.md) - how an
  existing native agent participates through Jarvis records without being
  rewritten as a Jarvis-owned agent.
- [compatible-host-mapping.md](./compatible-host-mapping.md) - how hosts map
  native collaboration events into Jarvis protocol records while keeping
  implementation private.
- [evidence-packs/existing-agent-review/README.md](./evidence-packs/existing-agent-review/README.md)
  machine-checkable protocol-record evidence pack for the existing-agent
  review-resolution loop.
- [evidence-packs/existing-agent-takeover/README.md](./evidence-packs/existing-agent-takeover/README.md)
  machine-checkable protocol-record evidence pack for the existing-agent
  takeover-resolution loop.
- [implementation-proof/native-coding-agent/README.md](./implementation-proof/native-coding-agent/README.md)
  SDK-helper generated implementation proof for one native coding-agent
  collaboration loop.

## Validation

Validate evidence packs from the repository root:

```bash
python3 scripts/check_example_evidence_packs.py
```

Validate the implementation proof from the repository root:

```bash
python3 scripts/check_implementation_proof.py
```

Evidence packs and implementation proofs validate protocol records only. They
do not certify an implementation and do not claim production adoption.
