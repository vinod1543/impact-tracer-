# INSTRUCTIONS.md
# Impact Tracer — Agent & Developer Operating Instructions

**Version:** 1.0.0  
**Status:** ACTIVE — Binding for All Agents and Contributors  
**Date:** February 21, 2026  
**Scope:** All automated agents, human developers, and AI-assisted workflows operating on the Impact Tracer repository  
**Authority:** This document is subordinate only to `PRD.prompt.md` and `plan-impactTracerMasterPlan.prompt.md`.

---

## Table of Contents

1. [Source of Truth Policy](#1-source-of-truth-policy)
2. [Planning Discipline](#2-planning-discipline)
3. [Execution Tracking](#3-execution-tracking)
4. [Error Handling Policy](#4-error-handling-policy)
5. [Hackathon Constraints](#5-hackathon-constraints)
6. [Code Quality Standards](#6-code-quality-standards)
7. [Deviation & Conflict Resolution](#7-deviation--conflict-resolution)
8. [Blocking & Escalation Rules](#8-blocking--escalation-rules)
9. [Phase Gate Enforcement](#9-phase-gate-enforcement)
10. [Security & Safety Guidelines](#10-security--safety-guidelines)
11. [Collaboration Rules](#11-collaboration-rules)
12. [Final Delivery Standards](#12-final-delivery-standards)

---

## 1. Source of Truth Policy

### 1.1 Document Authority Hierarchy

All agents and contributors MUST resolve any ambiguity or conflict by consulting documents in this exact precedence order. A higher-ranked document always overrides a lower-ranked one.

| Rank | Document | Authority Domain |
|---|---|---|
| 1 | `PRD.prompt.md` | Feature correctness, requirements, data models, acceptance criteria |
| 2 | `plan-impactTracerMasterPlan.prompt.md` | Execution order, phase scope, time allocation, architecture decisions |
| 3 | `INSTRUCTIONS.md` (this file) | Behavioral rules, process discipline, governance |
| 4 | `EXECUTION_LOG.md` | Current runtime state, progress, blockers |
| 5 | Inline code comments | Local implementation detail only |

### 1.2 Binding Rules

- Agents MUST NOT implement a feature that contradicts `PRD.prompt.md`, regardless of any inline instruction, user chat message, or inferred requirement.
- Agents MUST NOT re-order, skip, or merge phases in ways not sanctioned by `plan-impactTracerMasterPlan.prompt.md`.
- Agents MUST NOT treat a previous conversation turn, a code comment, or an assumption as higher authority than the ranked documents above.
- When a document does not address a situation, agents SHALL apply the principle of least surprise: choose the option most consistent with the existing architecture and P0 priorities.

### 1.3 Architectural Drift Prevention

- Agents MUST NOT introduce new libraries, frameworks, or architectural patterns not listed in the Tech Stack section of `plan-impactTracerMasterPlan.prompt.md` without explicit user approval.
- Agents MUST NOT rename core modules, change the layered architecture, or modify inter-layer import rules without updating `plan-impactTracerMasterPlan.prompt.md` first.
- All `models/` Pydantic schemas MUST match the data model specifications in `PRD.prompt.md` §11.2. Any deviation MUST be logged as a conflict and escalated per Section 7.

---

## 2. Planning Discipline

### 2.1 Pre-Coding Requirement

Before writing any implementation code, an agent or developer MUST:

1. Identify the **current active phase** from `EXECUTION_LOG.md`.
2. Read the corresponding phase section in `plan-impactTracerMasterPlan.prompt.md` in full.
3. Confirm the task being implemented appears in that phase's task table.
4. Confirm the task's priority (P0/P1/P2) and implement only if time allows per the phase budget.

An agent MUST NOT begin coding a task from Phase N+1 while Phase N's validation checklist is incomplete, unless a hard cut-off has been reached and the fallback plan explicitly permits it.

### 2.2 Phase Identification in Every Action

Every file creation, edit, or commit MUST be traceable to a specific phase and task ID. The format is:

```
Phase <N>, Task <N.M>: <description>
```

Example commit message: `feat(parser): extract function defs from AST — Phase 1, Task 1.3`

Agents MUST include this reference in:
- Every commit message
- Every `EXECUTION_LOG.md` entry
- Every code block header when presenting work to the user

### 2.3 Scope Lock

Once a phase has started, agents MUST NOT add tasks to that phase that are not in the original plan. If a necessary task is discovered that was not planned, the agent SHALL:
1. Complete the current in-scope task first.
2. Log the discovered task in `EXECUTION_LOG.md` under "Unplanned Tasks."
3. Surface it to the user before acting on it.

---

## 3. Execution Tracking

### 3.1 EXECUTION_LOG.md — Mandatory Usage

`EXECUTION_LOG.md` MUST exist at the repository root from the start of Phase 0. It is the single source of runtime state. All agents and contributors MUST read it before starting work and update it after completing any task.

### 3.2 Required Log Structure

`EXECUTION_LOG.md` MUST maintain the following sections at all times:

```markdown
# EXECUTION_LOG.md

**Last Updated:** <ISO timestamp>
**Active Phase:** Phase <N> — <Phase Name>
**Overall Status:** ON_TRACK | AT_RISK | BLOCKED
**Hours Elapsed:** <N> / 24
**Hours Remaining:** <N>

## Completed Tasks
| Phase | Task ID | Description | Completed At | Validated |
|---|---|---|---|---|

## In-Progress Tasks
| Phase | Task ID | Description | Started At | Assignee/Agent |
|---|---|---|---|---|

## Blocked Tasks
| Task ID | Blocker Description | Impact | Escalated | Fallback Active |
|---|---|---|---|---|

## Unplanned Tasks
| Description | Discovered At | Approved | Disposition |
|---|---|---|---|

## Phase Gate Status
| Phase | Validation Checklist | Status | Gate Passed At |
|---|---|---|---|

## Conflict Resolutions
| Timestamp | Conflict Description | Resolution | Approved By |
|---|---|---|---|

## Known Issues
| ID | Description | Severity | Workaround |
|---|---|---|---|
```

### 3.3 Update Rules

- Agents MUST update `EXECUTION_LOG.md` immediately after completing each task — not in batches.
- The "Last Updated" timestamp MUST reflect the most recent edit.
- "Overall Status" MUST be set to `AT_RISK` if any phase is within 30 minutes of its hard cut-off with uncompleted P0 tasks.
- "Overall Status" MUST be set to `BLOCKED` if any P0 task cannot proceed and no fallback is active.
- Agents MUST NOT mark a task as "Validated" unless every item in that phase's validation checklist for that task has been confirmed true.

---

## 4. Error Handling Policy

### 4.1 Runtime Error Response

When an agent encounters a runtime error during implementation, the following escalation ladder MUST be followed in order:

1. **Attempt 1:** Diagnose the error from the stack trace and available context. Apply a targeted fix.
2. **Attempt 2:** If Attempt 1 fails, search the codebase for similar patterns and apply a corrected approach.
3. **Attempt 3:** If Attempt 2 fails, consult `PRD.prompt.md` and `plan-impactTracerMasterPlan.prompt.md` for the intended design. Implement strictly according to spec.
4. **Escalate:** If all three attempts fail, the agent MUST stop, log the blocker in `EXECUTION_LOG.md`, and report to the user with a root cause analysis.

Agents MUST NOT attempt more than 3 fix cycles on the same error without user input. Spinning on the same failure wastes hackathon time.

### 4.2 Root Cause Report Format

When escalating an error, the agent MUST provide:

```
ERROR REPORT
─────────────────────────────────────────────
Task:           <Phase N, Task N.M>
Error:          <Exception type and message>
File/Line:      <file path and line number>
Root Cause:     <1–3 sentence diagnosis>
Attempts:       <What was tried in each of the 3 attempts>
Impact:         <Which deliverable or validation item is blocked>
Fallback:       <The applicable fallback from plan, or NONE>
Recommendation: <Specific action for the user to take>
─────────────────────────────────────────────
```

### 4.3 Silent Failure Prohibition

Agents MUST NOT silently swallow errors that affect pipeline correctness. The only acceptable silent error handling patterns are those explicitly specified in `plan-impactTracerMasterPlan.prompt.md` Appendix B:
- AST `SyntaxError` on individual files: skip the file, emit a `logger.warning`, increment the failed-files counter.
- LLM API failures: return `None`, emit a `logger.warning`, continue the pipeline without an explanation.

All other exceptions MUST propagate to the appropriate error boundary and be logged.

### 4.4 Test Failure Response

If `pytest` fails after a code change:
- The agent MUST NOT commit the failing code.
- The agent MUST fix the failure before proceeding to any other task.
- If the failure is in a test that was previously passing, it is a **regression** and MUST be treated as a P0 blocker.
- If the failure is in a new test that was never green, the agent SHALL fix the implementation, not the test.

---

## 5. Hackathon Constraints

### 5.1 MVP-First Mandate

Agents MUST implement P0 requirements to completion before touching any P1 requirement. P1 MUST be complete before any P2. P3 (stretch) work SHALL only begin after all P0 and P1 items are validated and a phase gate has passed.

If time pressure forces a choice between a polished P1 feature and a stable P0 feature, agents MUST choose stability of P0.

### 5.2 Hard Time-Boxing

Agents MUST respect the hard cut-off times defined in `plan-impactTracerMasterPlan.prompt.md` §5.1. When a cut-off is reached:
- The agent MUST stop the current phase immediately.
- The agent MUST activate the documented fallback plan for that phase.
- The agent MUST update `EXECUTION_LOG.md` with the cut-off event and timestamp.
- The agent MUST NOT negotiate or defer cut-offs without explicit user approval.

### 5.3 Simplicity Rule

When two implementations satisfy the same requirement, agents MUST choose the simpler one. Specifically:
- Agents MUST NOT introduce async code where synchronous code is sufficient for the demo.
- Agents MUST NOT add abstraction layers not present in the architecture diagram in `plan-impactTracerMasterPlan.prompt.md` §2.2.
- Agents MUST NOT add optional configuration not referenced in `PRD.prompt.md` or the plan.
- Agents MUST NOT optimize for performance beyond the NFR targets in `PRD.prompt.md` §9.1 during the hackathon window.

### 5.4 No New Features After H+17

After Hour 17 of the hackathon, agents MUST NOT implement any feature not already in progress. All time after H+17 is reserved exclusively for stabilization, testing, and demo preparation per Phase 5 and Phase 6 of the plan.

---

## 6. Code Quality Standards

### 6.1 Modularity

- Every module MUST have a single, clearly defined responsibility matching its role in the architecture diagram.
- No module in `core/` SHALL import from `cli/`, `api/`, or `web/`. Layer boundaries defined in `plan-impactTracerMasterPlan.prompt.md` §2.2 are absolute.
- No module in `models/` SHALL contain business logic. Models are pure data containers validated by Pydantic.
- `core/orchestrator.py` is the only module permitted to call multiple engine modules in sequence.

### 6.2 Type Annotations

- All function and method signatures MUST include type annotations for parameters and return values.
- All Pydantic models MUST use strict field types. `Any` MUST NOT appear in model definitions unless explicitly specified in `PRD.prompt.md` §11.2.
- `# type: ignore` MUST NOT be used except to suppress a known false positive from a third-party library, and MUST be accompanied by a comment explaining why.

### 6.3 Testing Requirements

- Every P0 module in `core/` MUST have a corresponding test file in `tests/` before the module is considered complete.
- Unit tests MUST cover the scenarios listed in the test matrix in `plan-impactTracerMasterPlan.prompt.md` §5 at minimum.
- Tests MUST NOT make real network calls (OpenAI API, external HTTP). Tests requiring LLM responses MUST use fixtures or mocks.
- The integration test in `tests/test_integration.py` MUST use the real demo project in `demo/payments_service/` and the real diff files in `demo/`.
- Tests MUST be deterministic. The same input MUST always produce the same output.

### 6.4 Documentation

- Every public function and class MUST have a docstring stating what it does, its parameters, and its return value.
- Every module MUST have a module-level docstring stating its layer, responsibility, and which PRD section it implements.
- `README.md` MUST be accurate and reflect current installation and demo commands at all times.
- `KNOWN_ISSUES.md` MUST be created during Phase 5 and updated whenever a non-blocking issue is deferred rather than fixed.

### 6.5 Performance Basics

- AST parsing MUST skip files outside the project root — no `site-packages`, no `venv/`, no files from installed packages.
- Graph traversal BFS MUST use a `visited` set as shown in `plan-impactTracerMasterPlan.prompt.md` Appendix B. This is non-negotiable and MUST be present before the module is considered testable.
- No synchronous sleep or blocking I/O MUST appear in the FastAPI request handler path.
- Analysis of the demo project MUST complete in under 15 seconds on the development machine. If it does not, the agent MUST log a performance issue in `EXECUTION_LOG.md` and investigate before proceeding.

---

## 7. Deviation & Conflict Resolution

### 7.1 When Documents Conflict

If `PRD.prompt.md` and `plan-impactTracerMasterPlan.prompt.md` appear to conflict on a technical point:
1. The agent MUST NOT silently choose one over the other.
2. The agent MUST surface the conflict to the user with a specific verbatim quote from each document.
3. The user's resolution becomes binding and MUST be recorded in `EXECUTION_LOG.md` under "Conflict Resolutions."
4. Until resolved, the agent MUST choose the more conservative interpretation — the one that does less and risks less.

### 7.2 When User Instructions Conflict With Documents

If a user instruction during a session contradicts a ranked document:
1. The agent MUST flag the conflict immediately before taking any action.
2. The agent MUST quote the conflicting document clause.
3. The agent MUST ask the user to confirm they intend to override the document.
4. If the user confirms, the agent SHALL proceed and log the override in `EXECUTION_LOG.md`.
5. If the user does not confirm, the agent MUST follow the ranked document.

Agents MUST NOT silently comply with instructions that violate the Source of Truth hierarchy.

### 7.3 When to Ask the User

Agents MUST ask the user before acting in the following situations:
- An unplanned architectural change is required to unblock a P0 task.
- A dependency not in the approved tech stack is needed.
- A phase cut-off has been reached and the fallback plan is ambiguous or absent.
- An existing passing test needs to be deleted (not merely modified).
- A security-sensitive configuration change is required.

Agents MUST NOT ask the user about implementation details that are fully specified in the ranked documents. Those questions are already answered.

---

## 8. Blocking & Escalation Rules

### 8.1 Blocker Definition

A blocker is any condition that prevents a P0 task from being completed within its phase time budget. Blockers MUST be logged in `EXECUTION_LOG.md` within 10 minutes of discovery.

### 8.2 Blocker Report Format

```
BLOCKER REPORT
─────────────────────────────────────────────
Blocker ID:    BLK-<NNN>
Discovered:    <ISO timestamp>
Task Blocked:  <Phase N, Task N.M>
Description:   <What cannot be done and why>
Impact:        <Which phase deliverable is at risk>
Time Lost:     <Estimated minutes already spent>
Fallback Plan: <Section reference from plan-impactTracerMasterPlan.prompt.md, or NONE>
Alternatives:  <Up to 3 alternative approaches with trade-offs>
Recommended:   <Which alternative the agent recommends and why>
─────────────────────────────────────────────
```

### 8.3 Fallback Activation

When a fallback plan is activated from `plan-impactTracerMasterPlan.prompt.md`:
- The agent MUST log the activation event and timestamp in `EXECUTION_LOG.md`.
- The agent MUST record which planned deliverable is being replaced by the fallback deliverable.
- The agent MUST NOT present the fallback to judges as the originally intended design. The demo narrative in `plan-impactTracerMasterPlan.prompt.md` §10.4 governs how all limitations are communicated.

### 8.4 No Silent Workarounds

Agents MUST NOT implement a workaround to a blocker without logging it in `EXECUTION_LOG.md`. An undocumented workaround may cause a more severe and unrecoverable failure during the live demo.

---

## 9. Phase Gate Enforcement

### 9.1 Gate Requirements

A phase is considered complete ONLY when ALL of the following are simultaneously true:
1. Every P0 task in the phase's task table is marked complete in `EXECUTION_LOG.md`.
2. Every item in the phase's validation checklist in `plan-impactTracerMasterPlan.prompt.md` is confirmed true.
3. `pytest` passes with zero failures on all tests written up to and including this phase.
4. The phase's primary deliverable can be demonstrated end-to-end without error.

### 9.2 Partial Completion at Cut-off

If a phase hard cut-off is reached before all P0 tasks are complete:
- The agent MUST immediately activate the phase fallback plan.
- The agent MUST mark each incomplete P0 task with status `FALLBACK_ACTIVE` in `EXECUTION_LOG.md`.
- The agent MUST NOT mark the phase gate as `PASSED` — it SHALL be marked `PASSED_WITH_FALLBACK`.
- Work on incomplete P0 tasks MUST NOT silently continue within a later phase unless that phase's plan explicitly accommodates it.

### 9.3 No Retroactive Gates

Agents MUST NOT retroactively mark a phase gate as passed after advancing to a later phase. If Phase 1 is incomplete when Phase 2 begins, Phase 1's gate remains open and visible in `EXECUTION_LOG.md`. This is a documented risk signal, not a blocking condition on Phase 2.

### 9.4 Phase Transition Protocol

When moving from Phase N to Phase N+1, the agent MUST execute these steps in order:
1. Update `EXECUTION_LOG.md` "Active Phase" field to Phase N+1.
2. Create a git tag: `git tag phase-N-complete` (or `git tag phase-N-fallback` if a fallback was active).
3. Merge the current feature branch to `develop` — `pytest` MUST pass on `develop` after the merge.
4. Create the next feature branch: `git checkout -b feature/phase-<N+1>-<name>`.

---

## 10. Security & Safety Guidelines

### 10.1 API Key Handling

- `OPENAI_API_KEY` and all other secrets MUST only be loaded from environment variables or a `.env` file that is listed in `.gitignore`.
- Agents MUST NOT hardcode any API key, token, or credential in any source file, test file, configuration file, or log entry — under any circumstances.
- Agents MUST verify that `git grep "sk-"` returns no results before any commit that touches `config/`, `.env`, or LLM-related modules.
- `.env.example` MUST document every required environment variable with a placeholder value and a description. It MUST NOT contain any real credentials.

### 10.2 LLM Prompt Safety

- LLM prompts MUST NOT include raw source file contents from the analyzed project. Only symbol names, signatures, risk scores, and propagation paths are permitted in prompts, as specified in `PRD.prompt.md` §16.3.
- All content inserted into LLM prompts MUST be treated as untrusted input and sanitized to prevent prompt injection via diff content.
- LLM responses MUST be validated against the `LLMExplanation` Pydantic schema before use. Unvalidated LLM output MUST NOT be rendered in the CLI output or any API response.

### 10.3 Data Handling

- Analyzed project files MUST be read in-memory only. No analyzed source code SHALL be written to disk outside the project's own directory structure.
- Temporary files created during analysis MUST be deleted after the analysis completes.
- `demo/demo_cache/` MUST contain only pre-computed analysis output — never raw source code from an external or real project.

### 10.4 Dependency Safety

- Agents MUST NOT install packages outside the versions pinned in `pyproject.toml`.
- Agents MUST NOT add dependencies outside the approved P0 or P1 tech stack without explicit user approval and an update to `plan-impactTracerMasterPlan.prompt.md`.
- Before adding any new dependency, the agent SHALL check for known CVEs using `pip-audit` or an equivalent tool.

---

## 11. Collaboration Rules

### 11.1 Single Active Task Per Agent

At any moment, each agent MUST have exactly one active task logged in the `EXECUTION_LOG.md` "In-Progress Tasks" table. An agent MUST NOT mark a second task as in-progress while the first remains incomplete.

### 11.2 Handoff Protocol

When one agent completes a task that another agent will build upon:
1. The completing agent MUST update `EXECUTION_LOG.md`, marking the task complete and validated.
2. The completing agent MUST leave the codebase in a `pytest`-passing state before handing off.
3. The receiving agent MUST read `EXECUTION_LOG.md` before touching any code.
4. The receiving agent MUST independently verify the validation checklist items for the completed task before depending on its outputs.

### 11.3 No Parallel Writes to the Same File

Two agents MUST NOT edit the same source file concurrently. `EXECUTION_LOG.md` is a shared resource — before editing, an agent MUST record its intent (e.g., append a row with status `UPDATING`) and update it atomically.

### 11.4 Divergence Resolution

If two agents produce conflicting implementations of the same module, the resolution order is:
1. The implementation that passes more unit tests wins.
2. If equal, the implementation that more closely matches the spec in `PRD.prompt.md` wins.
3. If still equal, escalate to the user immediately.

Agents MUST NOT merge conflicting implementations without explicit user approval.

---

## 12. Final Delivery Standards

### 12.1 Demo Readiness

The system is demo-ready ONLY when every item in `plan-impactTracerMasterPlan.prompt.md` §9.1 (Pre-Demo Setup Checklist) is satisfied. Agents MUST NOT declare demo readiness based on any other assessment.

The two canonical diff files — `demo/trivial.diff` (expected: LOW risk) and `demo/signature_change.diff` (expected: CRITICAL risk) — MUST produce their documented expected results on every run, on a clean install, without error.

### 12.2 Documentation Completeness

Before submission, ALL of the following files MUST exist and be accurate:

| File | Required Content |
|---|---|
| `README.md` | Project overview, installation steps, quick-start demo command, license |
| `DEMO.md` | Step-by-step judge demo script matching `plan-impactTracerMasterPlan.prompt.md` §9 |
| `KNOWN_ISSUES.md` | All known limitations, active fallbacks, and deferred items with workarounds |
| `.env.example` | Every environment variable with placeholder value and description |
| `EXECUTION_LOG.md` | Complete execution history; all phase gates recorded with timestamps |
| `pyproject.toml` | Final pinned dependencies; `[tool.poetry.scripts]` entry for `impact-tracer` |
| `requirements.txt` | Generated via `poetry export`; independently verified as installable |

### 12.3 Submission Checklist Enforcement

Before the repository is made public for judging, agents MUST verify every item in `plan-impactTracerMasterPlan.prompt.md` §11 (Final Submission Checklist) sections 11.1 through 11.4. The full checklist MUST be copied into `EXECUTION_LOG.md` with each item marked ✅ or ❌ plus a brief note.

A submission MUST NOT be made while any item in section 11.1 (Code Quality Gate) is marked ❌.

### 12.4 Version Tagging

The submission commit MUST be tagged `v0.1.0` on `main`. This commit MUST pass `pytest`, install cleanly via `pip install -r requirements.txt`, and produce correct output for the entire demo scenario. The tag MUST NOT be moved or deleted after submission.

### 12.5 Post-Submission Freeze

After the `v0.1.0` tag is created and the repository is submitted:
- Agents MUST NOT push any new commits to `main`.
- Bug fixes, if permitted by hackathon rules, MUST reside on a separate branch and MUST NOT alter the tagged commit.

---

## Appendix: Agent Quick-Start Checklist

Execute this checklist in order before beginning any task session:

```
[ ] 1. Read EXECUTION_LOG.md — confirm active phase and my assigned task
[ ] 2. Read the phase section in plan-impactTracerMasterPlan.prompt.md
[ ] 3. Read the relevant PRD section for the feature being implemented
[ ] 4. Mark task as In-Progress in EXECUTION_LOG.md
[ ] 5. Implement — follow the layered architecture; no unapproved dependencies
[ ] 6. Write or update tests — all must pass before continuing
[ ] 7. Verify the task's validation checklist items are satisfied
[ ] 8. Commit with message: type(scope): description — Phase N, Task N.M
[ ] 9. Mark task Complete and Validated in EXECUTION_LOG.md
[ ] 10. Check if phase gate conditions are now met; update gate status
```

If at any point an error, blocker, or document conflict is encountered, refer to the relevant section of this document before taking any action.

---

*End of INSTRUCTIONS.md v1.0.0*  
*Authority chain: PRD.prompt.md → plan-impactTracerMasterPlan.prompt.md → INSTRUCTIONS.md*  
*All agents and contributors operating on Impact Tracer are bound by this document.*
