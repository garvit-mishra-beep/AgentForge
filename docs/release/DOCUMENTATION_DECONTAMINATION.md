# Documentation Decontamination

`Version: 1.0` · `Audit Focus: Technical Accuracy & Claims Verification`

This document details the comparison of claims made in AgentForge documentation (readmes, roadmaps, architecture guides) against actual code reality.

---

## 1. Claims Verification Log

| Doc Pathway | Claimed Feature / State | Code Verification Status | Verdict | Reality & Code Evidence |
| :--- | :--- | :--- | :--- | :--- |
| `README.md` (root) | **Tree-Sitter Intelligence**: Live symbol index, dependency graphs, and call-scope awareness (Status: Active). | **FALSE** | **DECONTAMINATE** | The static analysis directory `app/repository_intelligence/` contains parsers and indexers, but it is completely unreferenced by the `apps/api` backend server and agents runtime. The `pyproject.toml` dependency file does not include tree-sitter packages. |
| `README.md` (root) | **Evidence Validation Gate**: Each agent output validated for confidence, completeness, and correctness. | **PARTIALLY_TRUE** | **MISLEADING** | The LangGraph `evidence_validator_node.py` exists but populates mock local validations with hardcoded values instead of invoking verification models. |
| `README.md` (root) | **Real-time Streaming**: WebSocket-based live agent output delivery. | **PARTIALLY_TRUE** | **MISLEADING** | WebSockets are active and broadcast JSON payloads when a node completes a step or updates its message logs. It does not stream tokens character-by-character in real-time. |
| `docs/release/ROADMAP.md` | Milestone 3: Local Code Indexing via Tree-Sitter daemon scheduled for Q3 2026. | **OUTDATED** | **RECONSTRUCT** | Pre-existing experimental parser files exist in root `app/repository_intelligence/`, indicating prototype leakage. |

---

## 2. Decontamination Tasks

1.  **Decontaminate Root README**: Remove "Tree-Sitter Intelligence" from active features list (move to planned/experimental), and clarify the behavior of "Evidence Validation Gate" (automated local schema validation) and "Real-time Streaming" (WebSocket events update).
2.  **Update Roadmap Timeline**: Align roadmap milestones with actual code state.
