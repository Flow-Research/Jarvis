## Summary

-

## Protocol Surface

-

## Boundary Check

- [ ] This change keeps Jarvis protocol-only.
- [ ] This change does not add host runtime, UI, auth, storage, billing, model orchestration, tool execution, scoring, payment, deployment, monitoring, host integration, host workflow, adapter, or wrapper code.

## Compatibility Impact

-

## Conformance Impact

-

## Validation

- [ ] `python3 scripts/check_conformance_fixtures.py`
- [ ] `python3 scripts/check_openapi_contract.py`
- [ ] `python3 scripts/check_markdown_links.py`
- [ ] `python3 scripts/check_docs_site.py`
- [ ] `python3 scripts/check_example_evidence_packs.py`
- [ ] `python3 scripts/check_protocol_wording.py`
- [ ] `python3 scripts/check_sdk_boundary.py`
- [ ] `npm --workspace @jarvis-protocol/sdk test` if TypeScript helper paths changed
- [ ] `npm run test:python` if Python helper paths changed
- [ ] `git diff --check`
- [ ] `node --check demo/assets/app.js` if docs site JavaScript changed
