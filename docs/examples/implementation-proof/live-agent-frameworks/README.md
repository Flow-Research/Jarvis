# Live Agent Framework Proof

This proof records live framework runs from external host code.

Jarvis records protocol state. Hosts own framework execution and model calls.

## What This Proves

The proof records three external host runs:

- LangGraph `StateGraph.compile.invoke`
- DeepAgents `create_deep_agent.invoke`
- AgentScope `OpenAIChatModel.__call__`

Each run used OpenAI `gpt-5.5`, produced a native framework trace, produced a
Jarvis protocol export, and passed Jarvis validation for:

- JarvisEvent hash chain
- EvidenceManifest export
- trace hash linkage
- live model-call marker
- host boundary flags
- secret-free committed artifacts

Each run keeps a distinct WorkSession, JarvisEvent, EvidenceManifest, and trace
hash namespace. The committed traces remove raw provider response metadata and
keep only portable proof evidence.

## Files

- [langgraph_trace.json](./langgraph_trace.json)
- [langgraph_protocol_export.json](./langgraph_protocol_export.json)
- [deepagents_trace.json](./deepagents_trace.json)
- [deepagents_protocol_export.json](./deepagents_protocol_export.json)
- [agentscope_trace.json](./agentscope_trace.json)
- [agentscope_protocol_export.json](./agentscope_protocol_export.json)

## Boundary

This proof does not add runtime behavior to Jarvis.

This proof does not add adapters, wrappers, host UI, storage, auth, model
execution, tool execution, billing, scoring, payment, deployment, monitoring,
host integration, or host workflow to Jarvis.

The live harness stays outside this repository. The committed artifacts contain
only sanitized traces and Jarvis protocol exports.

## Validation

Validate this proof from the repository root:

```bash
python3 scripts/check_implementation_proof.py
```

Run the full protocol check:

```bash
npm run check:protocol
```
