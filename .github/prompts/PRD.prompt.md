# Product Requirements Document (PRD)
# Impact Tracer — Intelligent Code Change Impact Analysis System

**Version:** 1.0.0  
**Status:** Draft — Hackathon MVP  
**Date:** February 21, 2026  
**Author:** Impact Tracer Core Team  
**Audience:** Engineering Judges, Technical Reviewers, Stakeholders  

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Problem Statement](#2-problem-statement)
3. [Target Users](#3-target-users)
4. [User Personas](#4-user-personas)
5. [Use Cases](#5-use-cases)
6. [Goals & Success Metrics](#6-goals--success-metrics)
7. [In-Scope and Out-of-Scope](#7-in-scope-and-out-of-scope)
8. [Functional Requirements](#8-functional-requirements)
9. [Non-Functional Requirements](#9-non-functional-requirements)
10. [Technical Architecture Overview](#10-technical-architecture-overview)
11. [Data Flow](#11-data-flow)
12. [Dependency Graph Design](#12-dependency-graph-design)
13. [Change Analysis Workflow](#13-change-analysis-workflow)
14. [Risk & Confidence Model](#14-risk--confidence-model)
15. [UI/UX Requirements](#15-uiux-requirements)
16. [Security & Privacy](#16-security--privacy)
17. [Assumptions & Constraints](#17-assumptions--constraints)
18. [Risks & Mitigation](#18-risks--mitigation)
19. [Future Roadmap (Multi-language Support)](#19-future-roadmap-multi-language-support)
20. [Appendix](#20-appendix)

---

## 1. Executive Summary

**Impact Tracer** is an intelligent developer tooling system that answers a question every engineering team faces daily: *"If I change this code, what else will break?"*

By combining static program analysis, infrastructure configuration parsing, runtime trace mining, graph-based dependency modeling, change propagation algorithms, risk scoring, and Large Language Model (LLM) generated natural-language explanations, Impact Tracer transforms opaque code changes into auditable, explainable impact reports — before a single line is merged.

The MVP targets Python microservice systems and is designed as a **developer-first AI terminal tool**. The primary interface is a **natural language CLI** — users type plain English queries and the system understands intent, runs the appropriate analysis, and replies in the terminal with a rich formatted report. A **Model Context Protocol (MCP) server** is the secondary interface, enabling AI assistants and autonomous agents to call Impact Tracer as a tool. There is no web dashboard and no REST API server — the product is entirely terminal and AI-agent native.

**Value proposition:**  
- Reduces code review time by surfacing hidden blast radius before review.  
- Reduces production incidents caused by unexpected side effects.  
- Provides a confidence layer for autonomous agents and AI-assisted coding tools.  
- Accelerates onboarding by making code relationships visible.

**Hackathon demo scope:** A fully functional end-to-end pipeline — from a Git diff input to an interactive impact report — running against a sample Python microservice monorepo.

---

## 2. Problem Statement

### 2.1 The Core Problem

Modern software systems are deeply interconnected. A change to a single utility function — say, a JSON serialization helper — may be called by a data model, which is used by three API endpoints, which are consumed by two frontend services and a background worker. The actual blast radius of even a "small" change is often invisible to the engineer making the change and the reviewer approving it.

Current tooling does not adequately solve this:

| Tool Category | What It Does | What It Misses |
|---|---|---|
| Unit Tests | Catches regressions in tested code paths | Doesn't show *what* will be affected before tests run |
| Linters / Type Checkers | Finds syntax/type errors | No cross-module impact reasoning |
| Code Search | Finds references manually | No propagation, no risk scoring |
| Coverage Reports | Shows what was tested | Backward-looking; no predictive impact |
| LLMs (raw) | Explains code in context window | No whole-codebase graph awareness |

### 2.2 Consequences of the Gap

- **Production incidents** traced to unexpected function signature changes or changed return types in shared utilities.
- **Slow code reviews** where reviewers manually trace dependencies without tooling.
- **Risky refactors** that get deferred because impact is unknown — accumulating technical debt.
- **Onboarding friction** for new engineers who lack the mental model of the system.
- **AI coding agents** (e.g., Copilot, Devin) that make changes in isolation without understanding systemic impact.

### 2.3 The Opportunity

Combining static analysis, graph theory, and LLMs creates a system that can:
1. Map the full structural dependency graph of a Python codebase.
2. Receive a code diff as input.
3. Trace change propagation through the graph.
4. Produce a risk-ranked impact report with natural language explanation.

This is not a linter. It is not a test runner. It is an **impact intelligence layer** for software development.

---

## 3. Target Users

Impact Tracer targets three primary user segments and one emerging segment:

### 3.1 Primary Segments

| Segment | Description | Entry Point |
|---|---|---|
| **Backend Engineers** | Python developers making changes to shared services, APIs, or libraries | CLI, IDE plugin, PR check |
| **Engineering Leads / Tech Leads** | Engineers responsible for code quality who review PRs and assess risk | CI/CD dashboard, PR annotations |
| **DevOps / Platform Engineers** | Teams managing CI/CD pipelines who want automated risk gates | Pipeline step, API |

### 3.2 Secondary Segments

| Segment | Description |
|---|---|
| **QA Engineers** | Use impact reports to prioritize test coverage for high-risk changes |
| **Engineering Managers** | Use aggregate risk data for release readiness decisions |
| **AI Agent Operators** | Teams using autonomous coding agents (Copilot Workspace, Devin, etc.) who need an impact validation layer |

### 3.3 Organizational Context

- **Team size:** 3–500+ engineers
- **Codebase size:** 5,000–500,000 lines of Python
- **Deployment:** Python monorepo, modular monolith, or microservices
- **Maturity:** Teams that have outgrown "just run the tests and see" but haven't invested in custom impact tooling

---

## 4. User Personas

### Persona 1 — Aditya, Senior Backend Engineer

> *"I know what my change does. I don't always know what it touches."*

- **Age:** 29 | **Experience:** 5 years Python
- **Role:** Backend engineer on a payments microservice
- **Stack:** Python 3.11 + FastAPI + PostgreSQL
- **Pain:** His team has 40+ internal modules. He modifies a `BasePaymentValidator` class and spends 45 minutes manually checking what might break before opening a PR.
- **Goal:** Get an automated blast-radius report in seconds, ranked by risk.
- **How Impact Tracer helps:** Runs `impact-tracer analyze --diff HEAD~1` before pushing. Gets a ranked list of affected modules, functions, and endpoints with a risk score and LLM summary.

---

### Persona 2 — Priya, Engineering Lead

> *"I review 10 PRs a day. I can't trace every dependency manually."*

- **Age:** 34 | **Experience:** 9 years engineering, 3 years as lead
- **Role:** Tech lead for a platform team managing shared Python libraries used by 6 other teams
- **Pain:** PRs come in that change core utilities. She has no automated way to know if the change affects downstream teams without reading every piece of code.
- **Goal:** See a PR-level impact report automatically posted as a CI check.
- **How Impact Tracer helps:** Impact Tracer runs in CI on every PR. A report is posted as a PR comment and a CI status check. High-risk PRs require an additional approval.

---

### Persona 3 — Marcus, Platform/DevOps Engineer

> *"I need a risk gate in the pipeline, not a post-mortem."*

- **Age:** 31 | **Experience:** 6 years DevOps/SRE
- **Role:** Responsible for the deployment pipeline for a Python-heavy microservices org
- **Pain:** Deployments sometimes fail or cause cascading issues because a change's blast radius wasn't understood at merge time.
- **Goal:** Automated pipeline gate that blocks or flags high-risk changes.
- **How Impact Tracer helps:** Impact Tracer integrates as a pipeline step. Changes with a risk score above a configurable threshold require manual approval or are blocked.

---

### Persona 4 — Lena, AI Agent Operator

> *"Our AI agent writes code autonomously. I need to trust its changes."*

- **Age:** 27 | **Experience:** 2 years AI/ML ops
- **Role:** Operates autonomous coding agents in a startup engineering workflow
- **Pain:** AI agents change shared utilities without knowing the downstream impact. Production bugs are introduced because agents lack systemic awareness.
- **Goal:** Wrap every AI PR with an impact validation step that the agent or a human can review.
- **How Impact Tracer helps:** Impact Tracer's REST API is called post-generation. The impact report is injected into the agent's context or surfaced to a human reviewer.

---

## 5. Use Cases

### UC-01: Pre-Push Impact Check (Developer CLI)

**Actor:** Backend Engineer (Aditya)  
**Trigger:** Developer has staged changes and wants to verify impact before pushing  
**Flow:**
1. Developer runs `impact-tracer analyze --diff HEAD~1 --project ./src`
2. System parses the Git diff, extracts changed symbols (functions, classes, modules)
3. System loads the precomputed dependency graph or builds it on-the-fly
4. System traces change propagation from changed nodes
5. System computes risk score for each affected node
6. System invokes LLM with graph context to generate plain-English summary
7. CLI outputs ranked impact report with risk levels and affected files

**Postcondition:** Developer has a clear blast-radius report before the PR is opened.

---

### UC-02: CI/CD Pipeline Risk Gate

**Actor:** CI/CD System (GitHub Actions, GitLab CI)  
**Trigger:** Pull request opened or updated  
**Flow:**
1. CI pipeline fetches the PR diff
2. Impact Tracer CLI/API step is invoked
3. Impact report is generated
4. If risk score ≥ configured threshold: pipeline posts warning or fails the check
5. Report is posted as PR comment (GitHub/GitLab annotation)
6. High-risk label is applied to the PR

**Postcondition:** Every PR has an attached impact report; high-risk PRs are flagged.

---

### UC-03: Interactive Impact Dashboard

**Actor:** Engineering Lead, Engineering Manager  
**Trigger:** User opens Impact Tracer web UI  
**Flow:**
1. User inputs a GitHub repository URL or uploads a project ZIP
2. System analyzes the codebase and builds the dependency graph
3. User browses the interactive dependency graph visualization
4. User selects a branch/PR diff or inputs a custom diff
5. System highlights affected nodes in the graph with risk colors
6. User reviews the impact report, LLM summary, and affected paths

**Postcondition:** Stakeholder has a visual, explorable view of change impact.

---

### UC-04: API-Driven Integration (AI Agent Use Case)

**Actor:** AI Agent Operator / External System  
**Trigger:** POST request to Impact Tracer API with code diff and project context  
**Flow:**
1. External system sends diff and project metadata to `/api/v1/analyze`
2. System returns structured JSON impact report
3. Calling system (agent, IDE plugin, custom tool) consumes the report

**Postcondition:** Third-party systems can consume impact intelligence programmatically.

---

### UC-05: Dependency Graph Exploration (Onboarding)

**Actor:** New Engineer  
**Trigger:** User wants to understand the codebase structure  
**Flow:**
1. User runs `impact-tracer graph --project ./src --output graph.html`
2. System generates an interactive HTML dependency graph
3. User explores module-to-module and function-to-function relationships

**Postcondition:** New engineer understands codebase topology without reading every file.

---

## 6. Goals & Success Metrics

### 6.1 Product Goals

| # | Goal | Description |
|---|---|---|
| G1 | **Correctness** | Impact reports accurately reflect the true blast radius of a change |
| G2 | **Speed** | Analysis completes in under 30 seconds for codebases up to 50K LOC |
| G3 | **Actionability** | Reports provide ranked, prioritized, human-readable impact data |
| G4 | **Integrability** | Works in CLI, CI/CD, and API-driven modes without code changes |
| G5 | **Explainability** | LLM summaries are accurate, concise, and non-hallucinated |

### 6.2 Hackathon Demo Success Metrics

| Metric | Target | Measurement |
|---|---|---|
| End-to-end analysis latency | < 15 seconds (demo codebase) | Stopwatch during demo |
| Dependency graph accuracy | ≥ 95% of real imports captured | Manual audit vs. AST output |
| Risk score relevance | Judges agree high-risk items are critical | Live demo review |
| LLM explanation quality | Judges rate explanation as "useful" | Verbal feedback |
| Zero false critical alerts on trivial changes | No critical flag for docstring-only edits | Demo test case |

### 6.3 Production Success Metrics (Post-Hackathon)

| Metric | 30-Day Target | 90-Day Target |
|---|---|---|
| Analysis runs per day (active team) | 50 | 500 |
| PR coverage rate | 80% of PRs analyzed | 95% of PRs analyzed |
| Time spent on manual impact tracing (self-reported) | -40% | -70% |
| Production incidents from undetected side effects | -25% | -50% |
| Developer NPS for the tool | > 30 | > 50 |

---

## 7. In-Scope and Out-of-Scope

### 7.1 In-Scope (MVP)

| Category | Feature |
|---|---|
| **Languages** | Python 3.8+ |
| **Frameworks** | FastAPI, Flask, standalone scripts, Python services/workers |
| **Analysis** | AST-based static analysis, import graph, call graph, class hierarchy |
| **Infrastructure Parsing** | Docker Compose YAML (services, depends_on, networks, environment), Kubernetes manifests (Service, Deployment, Ingress, ConfigMap), Terraform HCL (resource dependencies, interpolation references) |
| **Runtime Trace Mining** | OpenTelemetry JSON trace exports, Nginx/Envoy API gateway access logs, PostgreSQL query logs (pg_stat_statements / slow query log) |
| **Unified Graph** | All three signal sources merged into a single `networkx.DiGraph`; cross-layer blast radius spanning code → services → infrastructure → database tables |
| **Change Input** | Git diff (unified diff format), file path list |
| **Propagation** | BFS/DFS over dependency graph from changed nodes |
| **Risk Scoring** | Configurable, multi-factor risk model (fan-out, depth, type of change, test coverage presence) |
| **LLM Explanation** | OpenAI GPT-4o / local open-source model via structured prompt |
| **Output** | CLI report (text), JSON API response, HTML interactive graph |
| **Interfaces** | Natural language CLI (conversational, opencode-style interactive REPL + single-shot query mode), MCP server (stdio + SSE transports) |
| **Deployment** | Local installation, Docker container, CI/CD step |

### 7.2 Out-of-Scope (MVP)

| Category | Justification |
|---|---|
| JavaScript / TypeScript | Post-MVP: requires separate AST toolchain |
| Java / Go / Rust | Planned for v2+ |
| Live runtime instrumentation (active profiling) | Requires agent injection into running process; out of scope. Offline log/trace file parsing IS in scope. |
| REST API server | Removed as a user-facing interface. No `fastapi` server, no HTTP endpoints. The MCP server IS the programmatic interface. |
| Web dashboard | No browser UI. Terminal is the only visual surface. Graph visualization is exported as a static `graph.html` file opened by the user locally. |
| IDE plugin (VS Code, JetBrains) | Post-MVP |
| Auto-fix suggestions | Beyond analysis scope for MVP |
| Historical trend dashboards | Requires data persistence layer; post-MVP |
| Security vulnerability scanning | Separate concern; out of scope |
| Semantic code diffing (beyond AST) | Post-MVP enhancement |

---

## 8. Functional Requirements

### 8.1 Static Analysis Engine

| ID | Requirement | Priority |
|---|---|---|
| FR-SA-01 | Parse Python source files into ASTs using Python's `ast` module | P0 |
| FR-SA-02 | Extract all top-level and nested function/method definitions with line ranges | P0 |
| FR-SA-03 | Extract all class definitions and their method members | P0 |
| FR-SA-04 | Extract all import statements: `import`, `from ... import`, `import ... as` | P0 |
| FR-SA-05 | Resolve relative imports to absolute module paths within the project | P0 |
| FR-SA-06 | Identify all function call sites and map caller → callee relationships | P0 |
| FR-SA-07 | Detect class inheritance relationships | P1 |
| FR-SA-08 | Extract type annotations and return types for function signatures | P1 |
| FR-SA-09 | Identify decorator usage (e.g., `@router.get`, `@property`, `@staticmethod`) | P1 |
| FR-SA-10 | Handle `__init__.py` re-exports when resolving module symbols | P1 |
| FR-SA-11 | Gracefully handle syntax errors in individual files without crashing the analysis | P0 |

### 8.2 Infrastructure Configuration Parsing

| ID | Requirement | Priority |
|---|---|---|
| FR-IC-01 | Parse `docker-compose.yml` using `pyyaml`; extract services, `depends_on`, `links`, `networks`, and `environment` blocks | P1 |
| FR-IC-02 | Create `ServiceNode` graph nodes for each Docker Compose service; create `ConfigEdge` for each `depends_on` and link relationship | P1 |
| FR-IC-03 | Parse Kubernetes manifests (Service, Deployment, Ingress, ConfigMap kinds); map selectors to deployments; extract ingress routing rules | P1 |
| FR-IC-04 | Create `ServiceNode` nodes for K8s services; create `NetworkNode` for network segments; create `IngressEdge` for externally-exposed services | P1 |
| FR-IC-05 | Parse Terraform HCL using `python-hcl2`; extract resource blocks and interpolation references (e.g., `aws_rds_instance.payments_db.endpoint`) | P1 |
| FR-IC-06 | Create `InfraNode` nodes for Terraform resources (RDS, SQS, Lambda, API Gateway); create `InfraEdge` for interpolation-based dependencies | P1 |
| FR-IC-07 | Validate parsed config schemas using `jsonschema`; skip invalid config files with a warning, never crash | P1 |
| FR-IC-08 | Link `ServiceNode` (from config) to `CodeNode` (from AST) by matching service names to Python module/package names | P1 |

### 8.3 Runtime Trace Mining

| ID | Requirement | Priority |
|---|---|---|
| FR-RT-01 | Parse OpenTelemetry JSON trace exports; extract span parent-child relationships to identify service-to-service call chains | P1 |
| FR-RT-02 | Aggregate OTEL traces over a configurable time window (default: 7 days) using `pandas`; compute per-pair call_count, avg_latency_ms, last_seen | P1 |
| FR-RT-03 | Apply confidence boost based on call frequency: ≥1000 calls → +0.20; 100–999 → +0.10; <100 → +0.05 | P1 |
| FR-RT-04 | Parse Nginx/Envoy access logs using regex; extract source service (from `X-Source-Service` header or source IP), target path, and HTTP status | P1 |
| FR-RT-05 | Parse PostgreSQL query logs (slow query log or `pg_stat_statements` export); extract application_name, tables touched, and query type (READ/WRITE) | P1 |
| FR-RT-06 | Create `RuntimeEdge` in the unified graph for each observed service-to-service call with metadata: call_count, avg_latency_ms, last_seen, confidence | P1 |
| FR-RT-07 | Create `DataAccessEdge` for each service-to-database-table relationship observed in Postgres logs; distinguish READ vs WRITE | P1 |
| FR-RT-08 | Flag "undeclared runtime dependencies": RuntimeEdges with no corresponding ConfigEdge — these are ghost couplings and are elevated in risk | P1 |
| FR-RT-09 | Gracefully handle missing or malformed log/trace files; log a warning and continue analysis with reduced confidence | P0 |

### 8.4 Unified Dependency Graph Construction

| ID | Requirement | Priority |
|---|---|---|
| FR-DG-01 | Build a directed module-level dependency graph (node = module, edge = import relationship) from AST analysis | P0 |
| FR-DG-02 | Build a directed symbol-level dependency graph (node = function/class, edge = call/inheritance) from AST analysis | P0 |
| FR-DG-03 | Merge CodeNodes (AST), ServiceNodes (config), InfraNodes (Terraform), TableNodes (DB logs) into a single `networkx.DiGraph` (the Unified Graph) | P1 |
| FR-DG-04 | Attach `source` metadata to every edge: `"ast"` / `"config"` / `"runtime"`; attach `confidence` float (0.0–1.0) to every edge | P1 |
| FR-DG-05 | Support incremental graph updates when only a subset of files change | P1 |
| FR-DG-06 | Persist the unified graph to disk in a serializable format (JSON, NetworkX pickle) | P1 |
| FR-DG-07 | Support graph queries: neighbors, transitive dependencies, ancestors, descendants — across all node and edge types | P0 |
| FR-DG-08 | Detect and report circular dependency chains | P1 |
| FR-DG-09 | When all three sources (AST + config + runtime) agree on an edge, elevate that edge's confidence to HIGH (≥ 0.80) | P1 |

### 8.5 Diff Parsing & Change Detection

| ID | Requirement | Priority |
|---|---|---|
| FR-DP-01 | Accept unified Git diff format as input | P0 |
| FR-DP-02 | Parse diff to extract changed files, changed line ranges, added symbols, removed symbols, modified symbols | P0 |
| FR-DP-03 | Classify change types: addition, deletion, modification, rename | P0 |
| FR-DP-04 | Map changed line ranges to affected symbols using the AST | P0 |
| FR-DP-05 | Accept a direct file path list as an alternative to diff input | P1 |

### 8.6 Change Propagation Engine

| ID | Requirement | Priority |
|---|---|---|
| FR-CP-01 | Starting from changed symbols, perform BFS traversal over the dependency graph | P0 |
| FR-CP-02 | Collect all transitively affected symbols up to a configurable depth (default: unlimited) | P0 |
| FR-CP-03 | Track the propagation path (chain) from changed node to each affected node | P0 |
| FR-CP-04 | Distinguish between direct dependents (depth 1) and transitive dependents (depth 2+) | P0 |
| FR-CP-05 | Support configurable maximum traversal depth to limit scope for large codebases | P1 |

### 8.7 Risk Scoring Model

| ID | Requirement | Priority |
|---|---|---|
| FR-RS-01 | Assign a risk score (0.0–1.0) to each affected symbol | P0 |
| FR-RS-02 | Risk score factors: fan-in degree, propagation depth, change type, symbol type, test file presence | P0 |
| FR-RS-03 | Assign an overall change risk score aggregated from all affected symbols | P0 |
| FR-RS-04 | Assign a confidence level (HIGH/MEDIUM/LOW) alongside the risk score | P0 |
| FR-RS-05 | Risk levels: CRITICAL (0.8–1.0), HIGH (0.6–0.8), MEDIUM (0.4–0.6), LOW (0.0–0.4) | P0 |
| FR-RS-06 | Support configurable risk factor weights via a config file | P1 |
| FR-RS-07 | Flag changes to public API surfaces (exported symbols) as higher risk | P1 |

### 8.8 LLM Explanation Engine

| ID | Requirement | Priority |
|---|---|---|
| FR-LLM-01 | Generate a plain-English summary of the change and its impact | P0 |
| FR-LLM-02 | Include structured context in the LLM prompt: changed symbols, affected graph, risk score, propagation paths | P0 |
| FR-LLM-03 | Support OpenAI GPT-4o as the primary LLM backend | P0 |
| FR-LLM-04 | Support a local model (Ollama + Code Llama / Mistral) as a fallback | P1 |
| FR-LLM-05 | Explanation must include: change summary, blast radius description, highest-risk items, recommended actions | P0 |
| FR-LLM-06 | Implement prompt guarding to prevent hallucination of non-existent modules or symbols | P1 |
| FR-LLM-07 | Allow explanation to be regenerated independently without rerunning full analysis | P1 |

### 8.9 Output & Reporting

| ID | Requirement | Priority |
|---|---|---|
| FR-OUT-01 | CLI output: color-coded impact report with risk-ranked table | P0 |
| FR-OUT-02 | JSON output: structured impact report for API/CI consumption | P0 |
| FR-OUT-03 | HTML output: interactive dependency graph with highlighted affected nodes | P1 |
| FR-OUT-04 | Markdown output: suitable for GitHub PR comments | P1 |
| FR-OUT-05 | Exit code semantics: 0 = low risk, 1 = medium/high risk, 2 = critical risk (for CI gating) | P0 |

### 8.10 Interfaces

#### Natural Language CLI

| ID | Requirement | Priority |
|---|---|---|
| FR-IF-01 | `impact-tracer` (no args) launches an interactive REPL session with a Rich-styled prompt: `❯ ` | P0 |
| FR-IF-02 | `impact-tracer "<query>"` accepts a single natural language query, runs analysis, prints the report, and exits | P0 |
| FR-IF-03 | A LLM-powered **Intent Parser** (GPT-4o) maps the user's NL query to one or more analysis operations: `analyze_diff`, `show_graph`, `get_risk`, `explain_symbol`, `query_dependencies` | P0 |
| FR-IF-04 | The CLI maintains **session context** within a REPL session: current project path, last diff, last `ImpactReport` — enabling follow-up queries without re-specifying context | P0 |
| FR-IF-05 | If the intent is ambiguous or required inputs (project path, diff) are missing, the CLI asks a clarifying question before proceeding | P0 |
| FR-IF-06 | All analysis output is rendered in the terminal using `Rich`: risk-coloured tables, propagation path trees, panels with LLM explanation, and progress spinners during analysis | P0 |
| FR-IF-07 | `--format json` flag produces machine-readable `ImpactReport` JSON on stdout for CI/CD scriptability | P0 |
| FR-IF-08 | `--project <path>` and `--diff <file>` flags pre-load context before the REPL or single-shot query | P1 |
| FR-IF-09 | The REPL supports multi-turn conversation: "what else is affected?" correctly continues from the last report without restarting analysis | P1 |
| FR-IF-10 | `impact-tracer version` prints version; `impact-tracer --help` prints usage with NL query examples | P0 |

**Example NL queries the CLI MUST handle:**

```
> what breaks if I change validate() in payments/validator.py?
> analyze my latest git diff against ./src
> show me the dependency graph for the payments module
> what's the risk score for removing process_payment?
> which symbols have fan-in greater than 5?
> give me the blast radius as JSON
> what services depend on the payments database table at runtime?
```

#### MCP Server

| ID | Requirement | Priority |
|---|---|---|
| FR-IF-11 | MCP server exposes 4 tools: `analyze_change`, `get_impact_report`, `query_dependency_graph`, `get_risk_score` | P1 |
| FR-IF-12 | MCP server supports stdio transport (primary) for Claude Desktop and VS Code MCP extension | P1 |
| FR-IF-13 | MCP server supports SSE transport (opt-in) for HTTP-capable AI clients on port 8001 | P2 |
| FR-IF-14 | `impact-tracer-mcp` script starts the MCP server process | P1 |

---

## 9. Non-Functional Requirements

### 9.1 Performance

| ID | Requirement | Target |
|---|---|---|
| NFR-PERF-01 | Full analysis latency for a 10K LOC project | < 5 seconds |
| NFR-PERF-02 | Full analysis latency for a 50K LOC project | < 30 seconds |
| NFR-PERF-03 | Graph build time for a 50K LOC project (first run) | < 60 seconds |
| NFR-PERF-04 | Incremental analysis latency (graph cached) | < 3 seconds |
| NFR-PERF-05 | API P95 response time under load | < 10 seconds |
| NFR-PERF-06 | Memory footprint for a 50K LOC project | < 512 MB |

### 9.2 Reliability

| ID | Requirement |
|---|---|
| NFR-REL-01 | System must not crash on partial project directories (missing `__init__.py`, syntax errors in target files) |
| NFR-REL-02 | LLM unavailability must degrade gracefully: report is generated without the explanation |
| NFR-REL-03 | Analysis is deterministic: same diff + same project = same report |

### 9.3 Maintainability

| ID | Requirement |
|---|---|
| NFR-MNT-01 | Core engine has > 80% unit test coverage |
| NFR-MNT-02 | All modules follow a clean layered architecture (see section 10) |
| NFR-MNT-03 | New language analyzers can be added by implementing a single `LanguageAnalyzer` interface |
| NFR-MNT-04 | Risk model weights are externalized to a YAML config file |

### 9.4 Scalability

| ID | Requirement |
|---|---|
| NFR-SCALE-01 | API can handle ≥ 10 concurrent analysis requests |
| NFR-SCALE-02 | Graph store is replaceable (default: in-memory NetworkX; option: Redis/Neo4j for production) |

### 9.5 Usability

| ID | Requirement |
|---|---|
| NFR-UX-01 | CLI help output is self-documenting |
| NFR-UX-02 | Error messages clearly identify the failing component and suggest remediation |
| NFR-UX-03 | First run (no config file) requires only a path argument |

---

## 10. Technical Architecture Overview

### 10.1 System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        Impact Tracer                            │
│                                                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐                  │
│  │   CLI    │  │ REST API │  │  Web Dashboard│                  │
│  │ (Typer)  │  │(FastAPI) │  │  (React/HTML) │                  │
│  └────┬─────┘  └────┬─────┘  └──────┬───────┘                  │
│       │             │               │                           │
│       └─────────────┴───────────────┘                           │
│                           │                                     │
│                    ┌──────▼──────┐                              │
│                    │  Core API   │                              │
│                    │  (Orchestr) │                              │
│                    └──────┬──────┘                              │
│          ┌────────────────┼────────────────┐                   │
│          │                │                │                    │
│   ┌──────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐           │
│   │  Static     │  │  Dependency │  │   Change    │           │
│   │  Analysis   │  │  Graph      │  │  Propagation│           │
│   │  Engine     │  │  Engine     │  │  Engine     │           │
│   │  (AST/AST)  │  │  (NetworkX) │  │  (BFS/DFS)  │           │
│   └──────┬──────┘  └──────┬──────┘  └──────┬──────┘           │
│          │                │                │                    │
│          └────────────────┼────────────────┘                   │
│                           │                                     │
│                    ┌──────▼──────┐                              │
│                    │  Risk Score │                              │
│                    │  Engine     │                              │
│                    └──────┬──────┘                              │
│                           │                                     │
│                    ┌──────▼──────┐                              │
│                    │  LLM Engine │                              │
│                    │  (OpenAI /  │                              │
│                    │   Ollama)   │                              │
│                    └──────┬──────┘                              │
│                           │                                     │
│                    ┌──────▼──────┐                              │
│                    │  Report     │                              │
│                    │  Generator  │                              │
│                    │(CLI/JSON/MD)│                              │
│                    └─────────────┘                              │
└─────────────────────────────────────────────────────────────────┘
```

### 10.2 Module Structure

```
impact_tracer/
├── cli/                    # Natural language CLI
│   ├── main.py             # Entry point: REPL loop + single-shot mode
│   ├── repl.py             # Interactive REPL (prompt_toolkit)
│   ├── intent_parser.py    # LLM-powered NL → analysis operation mapper
│   └── session.py          # Session context (current project, last report)
├── mcp/                    # MCP server interface
│   ├── __init__.py
│   ├── server.py
│   └── tool_handlers.py
├── core/                   # Core business logic
│   ├── orchestrator.py     # Coordinates all engines
│   ├── analyzer/           # Static analysis engine
│   │   ├── base.py         # LanguageAnalyzer interface
│   │   └── python/
│   │       ├── ast_parser.py
│   │       ├── import_resolver.py
│   │       └── call_graph_builder.py
│   ├── infra/              # Infrastructure configuration parsers
│   │   ├── base.py         # InfraParser interface
│   │   ├── docker_compose.py
│   │   ├── kubernetes.py
│   │   └── terraform.py
│   ├── runtime/            # Runtime trace and log miners
│   │   ├── base.py         # RuntimeMiner interface
│   │   ├── otel_parser.py
│   │   ├── nginx_parser.py
│   │   └── postgres_parser.py
│   ├── graph/              # Unified dependency graph engine
│   │   ├── graph_builder.py   # Merges AST + infra + runtime into one DiGraph
│   │   ├── graph_store.py
│   │   └── graph_query.py
│   ├── diff/               # Diff parsing
│   │   └── diff_parser.py
│   ├── propagation/        # Change propagation engine
│   │   └── propagator.py
│   ├── risk/               # Risk scoring engine
│   │   ├── scorer.py
│   │   └── config.py
│   └── llm/                # LLM explanation engine
│       ├── client.py
│       ├── prompt_builder.py
│       └── explainer.py
├── output/                 # Report generators
│   ├── cli_reporter.py
│   ├── json_reporter.py
│   ├── markdown_reporter.py
│   └── graph_visualizer.py
├── models/                 # Pydantic data models
│   ├── symbol.py
│   ├── graph.py
│   ├── diff.py
│   ├── impact.py
│   └── report.py
├── config/
│   ├── settings.py
│   └── risk_weights.yaml
└── tests/
```

### 10.3 Technology Stack

| Layer | Technology | Justification |
|---|---|---|
| Language | Python 3.11 | Target language; full ecosystem access |
| CLI framework | `prompt_toolkit` | Interactive REPL with history, multiline input, syntax highlighting |
| CLI rendering | `rich` | All terminal output: tables, panels, trees, spinners, colours |
| Intent parsing | OpenAI GPT-4o (function calling) | Maps NL queries to analysis operations; same LLM backend as explanation |
| API framework | ~~FastAPI~~ _(removed)_ | No REST server. MCP is the programmatic interface. |
| ASGI | ~~uvicorn~~ _(removed)_ | Not needed without HTTP server. |
| AST parsing | `ast` (stdlib) | Zero dependencies; comprehensive Python AST |
| Infra config parsing | `pyyaml` | YAML parsing for Docker Compose + K8s manifests |
| Terraform parsing | `python-hcl2` | Parse HashiCorp Configuration Language (HCL) |
| Config validation | `jsonschema` | Validate parsed config schemas |
| Runtime aggregation | `pandas` | Aggregate OTEL spans and log entries by service pair |
| Graph engine | NetworkX | Unified dependency graph algorithms |
| Graph visualization | `pyvis` | Static `graph.html` export; no web server needed |
| LLM client | OpenAI SDK + httpx | Async; GPT-4o for intent parsing + explanation; Ollama fallback |
| MCP server | `mcp` SDK | Model Context Protocol; stdio + optional SSE transport |
| Data models | Pydantic v2 | Fast, strict models |
| Configuration | Pydantic Settings + YAML | Environment + file config |
| Testing | pytest + pytest-cov | Standard Python testing |
| Packaging | Poetry | Reproducible dependency management |

---

## 11. Data Flow

### 11.1 Primary Analysis Flow

```
[Input A: Git Diff + Project Path]   [Input B: Infra Config Files]   [Input C: OTEL Traces + Logs]
            │                                    │                              │
            ▼                                    ▼                              ▼
┌──────────────────────┐          ┌──────────────────────┐   ┌───────────────────────────┐
│   Diff Parser        │          │  Infra Config Parser  │   │  Runtime Trace/Log Miner  │
│   DiffResult model   │          │  (pyyaml, hcl2,       │   │  (OTEL JSON, Nginx logs,  │
│                      │          │   jsonschema)         │   │   Postgres query logs)    │
│                      │          │  ServiceNode, InfraNode│  │  RuntimeEdge, DataAccess  │
└──────────┬───────────┘          └──────────┬────────────┘   └──────────────┬────────────┘
           │                                 │                               │
           ▼                                 │                               │
┌──────────────────────┐                     │                               │
│   Static Analysis    │                     │                               │
│   Engine (AST)       │  ← Walk project files, extract functions/classes     │
│   CodeNode, Symbol   │                     │                               │
└──────────┬───────────┘                     │                               │
           │                                 │                               │
           └─────────────────────────────────┴───────────────────────────────┘
                                             │
                                             ▼
┌────────────────────────────────────────────────────────────┐
│   Unified Graph Builder                                    │
│   networkx.DiGraph                                         │
│   Merges: CodeNodes + ServiceNodes + InfraNodes + TableNodes
│   Edges: CodeEdge + ConfigEdge + InfraEdge + RuntimeEdge   │
│   Each edge carries: source, confidence, call_count        │
└──────────┬─────────────────────────────────────────────────┘
           │
           ▼
┌──────────────────────┐
│   Graph Builder       │  (legacy name retained for MDG/SDG sub-layers)
│   Module Graph        │  ← Node: module, Edge: import
│   Symbol Graph        │  ← Node: symbol, Edge: call/inherit
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│   Diff → Symbol Map   │  ← Map changed lines → symbols
│   ChangedSymbols[]    │  ← Root nodes for traversal
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│   Propagation Engine  │  ← BFS from changed nodes
│   AffectedGraph       │  ← Collect all reachable nodes
│                       │  ← Track depth + propagation path
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│   Risk Scorer         │  ← Score each affected node
│   RiskReport          │  ← Aggregate overall risk
│                       │  ← Compute confidence level
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│   LLM Explainer       │  ← Build structured prompt
│   Explanation         │  ← Call GPT-4o/Ollama
│                       │  ← Parse + validate response
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│   Report Generator    │  ← Format: CLI / JSON / Markdown
│   ImpactReport        │
└──────────────────────┘
            │
            ▼
[Output: Ranked Impact Report]
```

### 11.2 Data Models

```
ImpactReport {
  project_path: str
  diff_summary: DiffSummary
  changed_symbols: List[Symbol]
  affected_symbols: List[AffectedSymbol]
  propagation_paths: List[PropagationPath]
  overall_risk: RiskScore
  confidence: ConfidenceLevel
  explanation: LLMExplanation
  metadata: AnalysisMetadata
}

Symbol {
  id: str                    # module.ClassName.method_name
  name: str
  type: SymbolType           # FUNCTION | CLASS | METHOD | MODULE
  module: str
  file_path: str
  line_start: int
  line_end: int
  is_public: bool
  fan_in: int                # number of callers
  fan_out: int               # number of callees
}

AffectedSymbol {
  symbol: Symbol
  propagation_depth: int
  risk_score: float          # 0.0 - 1.0
  risk_level: RiskLevel      # CRITICAL | HIGH | MEDIUM | LOW
  propagation_path: List[str]
  change_type: ChangeType    # DIRECT | TRANSITIVE
}

RiskScore {
  value: float               # 0.0 - 1.0
  level: RiskLevel
  confidence: ConfidenceLevel
  factors: Dict[str, float]  # Breakdown of contributing factors
}

ServiceNode {
  id: str                    # "service:<name>"
  name: str
  image: Optional[str]
  ports: List[str]
  env_vars: Dict[str, str]
  network_segments: List[str]
  source: str                # "docker-compose" | "kubernetes" | "terraform"
}

InfraNode {
  id: str                    # "infra:<resource_type>:<name>"
  resource_type: str         # "RDS" | "SQS" | "Lambda" | "Redis" | "APIGateway"
  name: str
  source: str                # "terraform"
}

TableNode {
  id: str                    # "table:<schema>.<name>"
  table_name: str
  schema: str
  database_name: str
  source: str                # "runtime"
}

RuntimeEdge {
  source_id: str
  target_id: str
  call_count: int
  avg_latency_ms: float
  last_seen: datetime
  confidence: float          # 0.0 - 1.0, boosted by frequency
  edge_source: str           # "otel" | "nginx" | "postgres"
  is_ghost: bool             # True if no ConfigEdge exists for same pair
}
```

---

## 12. Dependency Graph Design

### 12.1 Graph Model

Impact Tracer constructs a **Unified Dependency Graph** — a single `networkx.DiGraph` that merges four interlocked layers. Each layer adds its own node types and edge types on top of the same graph instance.

**Layer 1 — Module Dependency Graph (MDG)** — source: AST
```
Node type: CodeNode (module layer)
  - module_path: str
  - file_path: str
  - lines_of_code: int
  - symbol_count: int
  - test_module: bool

Edge type: ImportEdge
  - import_type: DIRECT | STAR | ALIAS
  - symbols_imported: List[str]
  - source: "ast"
  - confidence: 1.0   # AST is ground truth
```

**Layer 2 — Symbol Dependency Graph (SDG)** — source: AST
```
Node type: CodeNode (symbol layer)
  - symbol_id: str
  - symbol_type: FUNCTION | CLASS | METHOD
  - module: str
  - signature: str
  - decorators: List[str]
  - fan_in: int
  - fan_out: int

Edge type: CodeEdge
  - edge_type: CALL | INHERITANCE | OVERRIDE | DECORATOR
  - call_site_line: int
  - source: "ast"
  - confidence: 1.0
```

**Layer 3 — Infrastructure Graph** — source: Docker Compose, Kubernetes, Terraform
```
Node types:
  ServiceNode   - name, image, port, network_segments, env_vars
  InfraNode     - resource_type (RDS|SQS|Lambda|Redis), name, arn
  NetworkNode   - name, cidr, vpc_id

Edge types:
  ConfigEdge    - service A depends_on service B (from docker-compose)
                  source: "config" | confidence: 0.60 (declared, not proven)
  InfraEdge     - lambda reads from RDS via HCL interpolation
                  source: "config" | confidence: 0.75
  NetworkEdge   - service in network segment X can reach segment Y
                  source: "config" | confidence: 0.50
```

**Layer 4 — Runtime Behavior Graph** — source: OTEL traces, API logs, DB logs
```
Node types:
  ServiceNode   - same as Layer 3 (merged by name match)
  TableNode     - table_name, schema, database_name

Edge types:
  RuntimeEdge   - service A called service B N times in 7 days
                  source: "runtime"
                  call_count: int
                  avg_latency_ms: float
                  last_seen: datetime
                  confidence: 0.40 + frequency_boost
                    (>= 1000 calls → +0.20 | 100-999 → +0.10 | <100 → +0.05)

  DataAccessEdge - service A READ/WRITE table T
                  source: "runtime"
                  access_type: READ | WRITE
                  query_count: int
                  confidence: 0.50 + frequency_boost
```

**Corroboration Rule:** When a `ConfigEdge` AND a `RuntimeEdge` both exist between the same pair of nodes, the combined confidence is elevated to `max(config_conf, runtime_conf) + 0.20`, capped at 1.0. This is the triple-corroborated "ground truth" edge.

### 12.2 Graph Construction Algorithm

```
FOR each .py file in project:
  1. Parse into AST
  2. Extract module-level imports → MDG edges
  3. Extract function/class definitions → SDG nodes
  4. Walk AST for Call nodes → SDG edges (caller → callee)
  5. Walk ClassDef bases → SDG inheritance edges
  6. Resolve relative imports using package __init__.py chain
  7. Handle star imports: expand to all public symbols in target module
```

### 12.3 Graph Visualization Schema

The interactive visualization uses a layered force-directed layout:

```
Color coding — Nodes:
  ● Blue       — Unchanged code modules / symbols
  ● Purple     — Infrastructure nodes (ServiceNode, InfraNode)
  ● Cyan       — Database table nodes (TableNode)
  ● Orange     — Directly changed symbols
  ● Red        — High-risk affected symbols (risk > 0.6)
  ● Yellow     — Medium-risk affected symbols
  ● Green      — Low-risk affected symbols
  ● Grey       — Unaffected, out of traversal scope

Color coding — Edges:
  ─── Dark grey  — Code edges (AST, confidence = 1.0)
  ─── Blue       — Config edges (docker-compose/K8s/Terraform)
  ─── Green      — Runtime edges (OTEL / logs)
  ─── Dashed red — Ghost dependency (runtime edge without config edge)

Node size: proportional to fan-in (number of dependents)
Edge thickness: proportional to call_count (runtime edges) or coupling strength (code edges)
Edge tooltip: shows source, confidence, call_count, last_seen
```

### 12.4 Graph Storage

| Mode | Backend | Use Case |
|---|---|---|
| Default | In-memory NetworkX | Single analysis run, CI |
| Persistent | NetworkX + pickle/JSON cache | CLI with `--cache` flag |
| Production (future) | Neo4j / Redis graph | Large monorepos, multi-user |

---

## 13. Change Analysis Workflow

### 13.1 Step-by-Step Workflow

**Step 1: Diff Ingestion**
```
Input: git diff --unified=0 HEAD~1 HEAD
Output: DiffResult {
  files_changed: ["src/payments/validator.py"],
  hunks: [Hunk{file, old_start, old_end, new_start, new_end, content}],
  change_type: MODIFIED
}
```

**Step 2: Symbol Extraction from Diff**
```
For each changed hunk:
  - Map line range to enclosing AST nodes
  - Identify: function signature changed? class body changed? new method added?
  - Classify change type:
    SIGNATURE_CHANGE  → highest risk (breaks all callers)
    BODY_CHANGE       → medium risk (logic change, callers still compile)
    DOCSTRING_CHANGE  → low risk
    ADDITION          → medium risk (new surface area)
    DELETION          → highest risk (breaks all callers)
```

**Step 3: Propagation Traversal**
```
BFS from each ChangedSymbol:
  queue = [changed_symbol]
  visited = set()
  WHILE queue not empty:
    node = queue.pop()
    IF node in visited: continue
    visited.add(node)
    FOR dependent IN graph.predecessors(node):  # Who depends on this?
      affected_symbols.add(AffectedSymbol(
        symbol=dependent,
        depth=current_depth + 1,
        path=current_path + [node]
      ))
      queue.push(dependent)
```

**Step 4: Risk Computation**
```
FOR each affected_symbol:
  risk = weighted_sum(
    fan_in_score      * w_fan_in,       # More callers = higher risk
    depth_score       * w_depth,        # Direct deps > transitive
    change_type_score * w_change_type,  # Signature > body > docstring
    symbol_type_score * w_symbol_type,  # Public API > internal
    test_coverage_score * w_coverage    # No tests = higher risk
  )
  confidence = f(graph_completeness, import_resolution_rate)
```

**Step 5: LLM Explanation**
```
Prompt structure:
  [SYSTEM]: You are a senior software architect analyzing Python code impact.
             Only reference symbols that exist in the provided context.
             Be precise and actionable.
  
  [USER]:   CHANGED: {changed_symbols with signatures}
            AFFECTED: {top 10 affected symbols, ranked by risk}
            PROPAGATION: {highest-risk paths}
            RISK SCORE: {overall_risk} ({confidence} confidence)
            
            Generate:
            1. A 2-sentence change summary
            2. A 3-sentence blast radius description
            3. Top 3 risk items with one-line explanations
            4. Recommended reviewer actions
```

---

## 14. Risk & Confidence Model

### 14.1 Risk Factor Definitions

| Factor | Symbol | Range | Description |
|---|---|---|---|
| Fan-in Score | `F_in` | 0–1 | Normalized: `min(fan_in / MAX_FAN_IN, 1.0)` |
| Propagation Depth Penalty | `F_depth` | 0–1 | `1.0 / (depth + 1)` — direct = 1.0, depth 2 = 0.5 |
| Change Type Score | `F_type` | 0–1 | DELETION=1.0, SIGNATURE=0.9, BODY=0.5, DOCSTRING=0.05 |
| Symbol Type Score | `F_symbol` | 0–1 | PUBLIC_API=1.0, CLASS=0.7, INTERNAL_FUNC=0.4 |
| Test Coverage Penalty | `F_test` | 0–1 | No tests=1.0, Tests present=0.3 |

### 14.2 Risk Score Formula

$$
R = w_1 \cdot F_{in} + w_2 \cdot F_{depth} + w_3 \cdot F_{type} + w_4 \cdot F_{symbol} + w_5 \cdot F_{test}
$$

**Default weights (configurable in `risk_weights.yaml`):**

| Weight | Default |
|---|---|
| $w_1$ (Fan-in) | 0.30 |
| $w_2$ (Depth) | 0.20 |
| $w_3$ (Change type) | 0.25 |
| $w_4$ (Symbol type) | 0.15 |
| $w_5$ (Test coverage) | 0.10 |

**Risk Levels:**

| Level | Score Range | Action |
|---|---|---|
| CRITICAL | 0.8 – 1.0 | Block CI; require senior review |
| HIGH | 0.6 – 0.8 | Flag PR; attach impact report |
| MEDIUM | 0.4 – 0.6 | Annotate PR; suggest test coverage |
| LOW | 0.0 – 0.4 | Pass; informational only |

### 14.3 Confidence Model

Confidence reflects how complete and reliable the graph analysis is. The model now incorporates three signal sources:

```
# Base confidence — static analysis quality
static_confidence = (
    import_resolution_rate   * 0.40  +  # % of imports fully resolved
    ast_parse_success_rate   * 0.30  +  # % of files parsed without error
    call_resolution_rate     * 0.30     # % of call sites resolved to symbols
)

# Runtime corroboration boost — per-edge adjustment
runtime_boost = 0.0
IF runtime_edge exists for this dependency pair:
    IF call_count >= 1000: runtime_boost = +0.20
    IF call_count 100-999: runtime_boost = +0.10
    IF call_count < 100:   runtime_boost = +0.05

# Ghost penalty — undeclared runtime dependency
IF runtime_edge exists AND config_edge does NOT exist:
    ghost_penalty = -0.10   # penalize unreliable ghost coupling

# Final edge confidence
edge_confidence = min(1.0, base_edge_confidence + runtime_boost + ghost_penalty)

# Overall analysis confidence
confidence_score = static_confidence

HIGH:   confidence_score >= 0.85
MEDIUM: confidence_score >= 0.60
LOW:    confidence_score <  0.60
```

**Confidence is surfaced alongside the risk score.** A CRITICAL risk with LOW confidence means the analysis is incomplete and should trigger human review regardless.

### 14.4 Special Risk Rules

| Rule | Condition | Action |
|---|---|---|
| Public API Change | Changed symbol is in `__all__` or has no leading underscore and is in a package | Auto-elevate to CRITICAL |
| Mass Deletion | > 20% of a module's symbols deleted | Auto-elevate overall risk to CRITICAL |
| Circular Dep in Path | Propagation path includes a cycle | Flag cycle, cap depth at 5 |
| No Tests Found | No `test_*.py` referencing the changed module | Penalty applied |
| Framework Decorator | `@router.get`, `@app.route` on changed function | Elevate: API endpoint changed |

---

## 15. UI/UX Requirements

### 15.1 Natural Language CLI — Interaction Specification

**REPL mode** (`impact-tracer` with no args):

```
$ impact-tracer

  ███ Impact Tracer v0.1.0
  Type a question in plain English. Type 'exit' to quit.
  Project: not set  │  Last diff: none

❯ what breaks if I change validate() in payments/validator.py?

⠿ Parsing intent...
⠿ No project loaded. Which project should I analyze? (path or '.' for current dir)

❯ .

⠿ Building unified dependency graph for ./  (AST + infra config)
⠿ Running impact analysis...
⠿ Generating explanation...

┏━━━━━━━━━━━━━━━━━━━━━ IMPACT REPORT ━━━━━━━━━━━━━━━━━━━━┓
┃ Changed:  BasePaymentValidator.validate()  SIGNATURE (hypothetical) ┃
┃ Risk:     ██████████ CRITICAL (0.87)   Confidence: HIGH  ┃
┃ Affected: 14 symbols across 3 services                             ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

  AFFECTED SYMBOLS
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ❗ CRITICAL  process_payment()          risk 0.92  depth 1
             └─ calls validate() directly │ 0 tests

  ❗ CRITICAL  refund_payment()            risk 0.88  depth 1
             └─ calls validate() directly │ 0 tests

  ⚠️  HIGH      settlement_worker.run()    risk 0.74  depth 2
             └─ via SettlementProcessor.process()

  [ ... 11 more symbols ... type 'show all' to expand ]

  LLM EXPLANATION
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Two production API endpoints call validate() directly and will fail
  at runtime if not updated. A background settlement worker is
  transitively affected. Update callers and add integration tests
  before merging.

  ✔ Update all direct callers before merging
  ✔ Add integration tests for process_payment and refund_payment
  ✔ Notify the settlements team of the transitive risk

❯ what services depend on the payments database at runtime?

⠿ Querying runtime edges for TableNode:payments_db...

  2 services observed accessing payments_db in the last 7 days:
  • payment-service  →  payments_db  WRITE  (1847 queries)  last: 2h ago
  • reporting-service → payments_db  READ   (312 queries)   last: 5h ago
  ⚠️  reporting-service has NO config edge — ghost dependency

❯ give me the blast radius as JSON

  (outputs ImpactReport JSON to stdout)

❯ exit
```

**Single-shot mode** (`impact-tracer "<query>"`):
```bash
# Works for CI/CD pipelines
impact-tracer "analyze my latest git diff" --project . --format json | jq .overall_risk
```

**Intent → Operation Mapping (handled by GPT-4o function calling):**

| User query pattern | Mapped operation |
|---|---|
| "what breaks if I change X" | `analyze_change` with synthesized diff for X |
| "analyze [this/my/latest] diff" | `analyze_change` with diff from context/file/`git diff HEAD~1` |
| "show [the] graph [for X]" | `build_graph` + open `graph.html` in browser |
| "what depends on X" / "who calls X" | `query_dependencies(node=X)` |
| "what's the risk score for X" | `get_risk_score(symbol=X)` |
| "what services use table T at runtime" | `query_runtime_edges(table=T)` |
| "show all" / "expand" | re-render last report with full symbol list |
| "give me JSON" / "export as JSON" | re-render last report as JSON |

### 15.2 Design Principles

1. **Conversation over commands** — the user should never need to remember flags or syntax
2. **Clarify before failing** — if context is missing, ask one focused question
3. **Progressive disclosure** — summary first, truncated lists, expand on request
4. **Risk = colour** — red CRITICAL / yellow HIGH / blue MEDIUM / green LOW; consistent everywhere
5. **Zero noise for low-risk** — a LOW result is shown in green with one line, never a wall of text
6. **Session memory** — follow-up questions work without re-specifying the project or diff

---

## 16. Security & Privacy

### 16.1 Source Code Handling

| Risk | Mitigation |
|---|---|
| Code uploaded to external LLM API | Only symbol names, signatures, and propagation structure are sent — never raw source file contents |
| API key exposure | Keys loaded from environment variables only; never logged or included in reports |
| Temporary file storage | Project files analyzed in-memory or in temp directories cleaned up post-analysis |

### 16.2 Security

| Control | Implementation |
|---|---|
| API key exposure | Keys loaded from environment variables only; never logged or printed to terminal |
| Input validation | Pydantic models on all internal inputs; max diff size enforced (10MB) |

### 16.3 LLM Prompt Security

- Prompt injection guarding: sanitize all code content inserted into prompts
- Structured output mode (JSON schema enforcement) to prevent prompt manipulation via diff content
- No sensitive PII or secrets extracted from code and sent to LLM

### 16.4 Local-First Option

For organizations with strict data policies, Impact Tracer supports a fully local mode:
- Static analysis: fully local (Python stdlib only)
- LLM: Ollama with local model (no external API calls)
- No data leaves the user's machine

---

## 17. Assumptions & Constraints

### 17.1 Assumptions

| # | Assumption |
|---|---|
| A1 | The Python project follows standard packaging conventions (`__init__.py`, relative imports) |
| A2 | Git is available in the analysis environment for diff generation |
| A3 | The codebase does not rely exclusively on dynamic imports (`importlib.import_module`) for core business logic |
| A4 | An OpenAI API key is available for LLM explanation (or Ollama is configured locally) |
| A5 | Analyzed projects are under 200K LOC for the MVP performance targets |
| A6 | Python 3.8+ is required (f-strings, walrus operator, typed AST nodes) |

### 17.2 Constraints

| # | Constraint | Impact |
|---|---|---|
| C1 | 24-hour hackathon development window | Scope is tightly controlled; P0 requirements only for demo |
| C2 | Python AST cannot fully resolve dynamic dispatch, monkey-patching, or metaclass magic | Confidence penalty applied; noted in output |
| C3 | Star imports (`from module import *`) resolved heuristically | May over- or under-count dependencies; flagged in confidence |
| C4 | LLM context window limits (GPT-4o: 128K tokens) | Graphs with > 500 affected nodes truncated to top 50 by risk |
| C5 | No runtime execution of code | Dynamic behavior invisible to static analysis |

---

## 18. Risks & Mitigation

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R1 | False negatives: dynamic imports not captured | High (Python is dynamic) | Medium | Document limitation; penalize confidence; suggest test run |
| R2 | LLM API unavailable or rate-limited during demo | Medium | High | Pre-cache LLM response for demo scenario; local Ollama fallback |
| R3 | Graph build time exceeds demo threshold for large target repo | Medium | High | Pre-build graph for demo repo; ship with cached graph artifact |
| R4 | Circular dependencies cause infinite traversal loop | Low | High | Cycle detection in BFS with visited set |
| R5 | Over-engineered architecture unfinished in 24 hours | Medium | High | Hard P0/P1 prioritization; stub P1 components with mock data for demo |
| R6 | LLM hallucinating non-existent module names in explanation | Medium | Medium | Constrain prompt to only reference symbols in the analysis context; validate output |
| R7 | Risk score miscalibrated (trivial changes flagged as critical) | Medium | Medium | Calibrate weights on demo project; test with docstring-only diff edge case |
| R8 | AST parsing fails on third-party library code in venv | Low | Low | Skip files outside project root; only analyze first-party code |

---

## 19. Future Roadmap (Multi-language Support)

### 19.1 Architecture for Language Extensibility

The analyzer layer is designed around a `LanguageAnalyzer` abstract interface:

```python
class LanguageAnalyzer(ABC):
    @abstractmethod
    def parse_file(self, file_path: Path) -> SymbolTable: ...
    
    @abstractmethod
    def extract_dependencies(self, symbol_table: SymbolTable) -> DependencySet: ...
    
    @abstractmethod
    def resolve_imports(self, project_root: Path) -> ImportMap: ...
```

Adding a new language requires only implementing this interface. The propagation, risk scoring, LLM, and output layers are language-agnostic.

### 19.2 Roadmap Timeline

```
Q2 2026 — v1.1: TypeScript/JavaScript Support
  ├── ESTree-based AST parser
  ├── CommonJS + ESM import resolution
  ├── tsconfig.json path aliases support
  └── React component dependency graph

Q3 2026 — v1.2: Java Support
  ├── JavaParser / tree-sitter JVM AST
  ├── Maven/Gradle dependency mapping
  ├── Spring annotation awareness (@Autowired, @Component)
  └── Interface → implementation resolution

Q3 2026 — v1.3: IDE Integration
  ├── VS Code extension: inline risk indicators
  ├── JetBrains plugin
  └── Real-time analysis on file save

Q4 2026 — v2.0: Go + Rust Support
  ├── Go: go/ast parser, module system
  ├── Rust: syn crate AST, cargo workspace
  └── Cross-language impact for polyglot services

Q1 2027 — v2.1: Dynamic Analysis Integration
  ├── Python runtime trace collector (sys.settrace)
  ├── Merge static + dynamic graphs for higher confidence
  └── CI test execution impact mapping

Q2 2027 — v2.2: Multi-Service / Microservice Graph
  ├── OpenAPI spec → service endpoint dependency graph
  ├── gRPC proto → service call graph
  ├── Cross-service impact propagation
  └── Service mesh integration (Istio, Linkerd telemetry)

Q3 2027 — v3.0: Intelligent Agent Mode
  ├── MCP (Model Context Protocol) server for AI agent integration
  ├── Real-time impact feedback loop for autonomous coding agents
  ├── Change proposal scoring before execution
  └── Multi-agent change coordination
```

### 19.3 Multi-Language Graph Unification

Long-term, Impact Tracer will maintain a unified **Polyglot Dependency Graph** where:
- Nodes represent symbols across any language
- Edges carry a `language` property
- Cross-language call relationships (Python → JS via API, Java → Python via subprocess) are modeled via service-level connectors

---

## 20. Appendix

### A. Glossary

| Term | Definition |
|---|---|
| **AST** | Abstract Syntax Tree — the structured tree representation of parsed source code |
| **Call Graph** | A directed graph where nodes are functions/methods and edges represent "A calls B" |
| **MDG** | Module Dependency Graph — module-level import graph |
| **SDG** | Symbol Dependency Graph — function/class level call/inheritance graph |
| **Fan-in** | Number of symbols that depend on (call or import) the given symbol |
| **Fan-out** | Number of symbols that the given symbol depends on |
| **Blast Radius** | The total set of code symbols affected by a given change |
| **Propagation Depth** | How many hops through the dependency graph a change travels |
| **Confidence Level** | How reliably the static analysis captured the true dependency graph |
| **Change Propagation** | The process of tracing how a change ripples through dependent code |
| **Risk Score** | A computed 0–1 value representing the potential danger of a code change |
| **LLM** | Large Language Model — AI model used to generate natural-language explanations |

### B. Sample JSON Impact Report

```json
{
  "version": "1.0.0",
  "timestamp": "2026-02-21T10:23:45Z",
  "project_path": "/workspace/payments-service",
  "overall_risk": {
    "value": 0.87,
    "level": "CRITICAL",
    "confidence": "HIGH"
  },
  "changed_symbols": [
    {
      "id": "payments.validator.BasePaymentValidator.validate",
      "type": "METHOD",
      "change_type": "SIGNATURE_CHANGE",
      "file": "payments/validator.py",
      "line_start": 42
    }
  ],
  "affected_symbols": [
    {
      "id": "payments.api.routes.process_payment",
      "risk_score": 0.92,
      "risk_level": "CRITICAL",
      "propagation_depth": 1,
      "propagation_path": [
        "payments.validator.BasePaymentValidator.validate",
        "payments.api.routes.process_payment"
      ]
    }
  ],
  "explanation": {
    "summary": "Signature change to BasePaymentValidator.validate() affects 14 symbols across 6 modules.",
    "blast_radius": "Two production API endpoints are directly impacted...",
    "top_risks": [],
    "recommended_actions": []
  }
}
```

### C. Configuration File Schema (`risk_weights.yaml`)

```yaml
risk_weights:
  fan_in: 0.30
  depth: 0.20
  change_type: 0.25
  symbol_type: 0.15
  test_coverage: 0.10

change_type_scores:
  DELETION: 1.0
  SIGNATURE_CHANGE: 0.9
  BODY_CHANGE: 0.5
  ADDITION: 0.4
  DOCSTRING_CHANGE: 0.05

propagation:
  max_depth: null  # null = unlimited
  
thresholds:
  ci_block: 0.8    # Block CI at this risk level
  ci_warn: 0.5     # Warn at this risk level
```

### D. CI/CD Integration Example (GitHub Actions)

```yaml
name: Impact Analysis

on: [pull_request]

jobs:
  impact-tracer:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 2

      - name: Run Impact Tracer
        uses: impact-tracer/action@v1
        with:
          project-path: ./src
          diff-from: ${{ github.event.pull_request.base.sha }}
          diff-to: ${{ github.sha }}
          format: markdown
          ci-block-threshold: critical
          openai-api-key: ${{ secrets.OPENAI_API_KEY }}
        
      - name: Post Report to PR
        uses: impact-tracer/comment-action@v1
        with:
          report-path: impact-report.md
```

### E. Hackathon Demo Script

**Demo scenario:** A Python FastAPI payments microservice with 15 modules.

1. **Setup (30s):** Show the project structure and dependency graph in the dashboard
2. **Trivial change (30s):** Edit a docstring → run analysis → show LOW risk → explain confidence
3. **Risky change (90s):** Change the signature of `BasePaymentValidator.validate()` → run analysis → watch CRITICAL report populate → walk through propagation paths → show LLM explanation
4. **CI Gate demo (30s):** Show that a GitHub Actions run would have blocked the PR
5. **QA (30s):** Demonstrate JSON output for AI agent consumption

**Total demo time: ~4 minutes**

---

*Document ends. Version 1.0.0 — Impact Tracer Hackathon MVP PRD*
