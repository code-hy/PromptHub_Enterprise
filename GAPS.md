# GAPS.md — RFQ REQ-20260819 Compliance Gap Analysis

**RFQ Reference:** REQ-20260819 — AI prompt engineering in Microsoft Copilot for ATO priority AI use cases  
**Application:** PromptHub Enterprise (self-hosted prompt library/engineering/testing/governance platform)  
**Date:** 19 August 2026

---

## Legend

| Symbol | Meaning |
|--------|---------|
| ✅ | Fully implemented and functional |
| ⚠️ | Partially implemented — exists in code but missing formal documentation or ATO-specific detail |
| ❌ | Not implemented — gap requiring work |

---

## 1. Prompt Development and Testing

| Requirement | Status | Evidence / Notes |
|-------------|--------|------------------|
| Development of 20–30 production-ready prompts | ✅ | 68 seeded enterprise prompts across 10+ business functions (`prompts_catalog.py`) |
| Coverage of ~10–15 priority business tasks | ✅ | `BusinessFunction` enum covers EXECUTIVE, PROJECT_MANAGEMENT, DATA_ANALYTICS, OPERATIONS, RISK, FINANCE, HR, MARKETING, SALES, LEGAL, CUSTOMER_SERVICE, IT |
| Testing and refinement of prompts | ✅ | Quality engine 9-component rubric (`quality/engine.py`), execution with eval metrics, assistant analyse/improve modes |
| Sample outputs and expected outcomes | ✅ | Execution results stored with output text, eval scores (instruction, grounding, completeness, etc.), mock provider gives deterministic sample outputs |
| User input parameters and configurable variables | ✅ | `PromptInput` model with name/type/required/description/sample_value; workflow `input_mapping` for inter-step variables |
| Exception handling guidance where output quality may vary | ⚠️ | Error handling exists in execution service and workflow service (`continue_on_failure`), but no **formal document** describing when/why output quality varies and how to handle it |
| Practical recommendations for achieving greater output consistency | ⚠️ | Quality engine scores and assistant explanations give per-prompt guidance, but no **standalone recommendations document** |
| Identification of prompts suitable for future Copilot Skills implementation | ❌ | No feature flags, tags, or metadata field to mark a prompt as "Copilot Skills candidate" |

---

## 2. Prompt Design and Governance

| Requirement | Status | Evidence / Notes |
|-------------|--------|------------------|
| Standard prompt architecture and templates | ✅ | Quality engine defines 9-component architecture (goal, context, source, expectations, specificity, constraints, audience, output format, examples). Prompt builder enforces structured fields. `is_template` flag on prompts |
| Prompt engineering methodology | ✅ | Quality scoring rubric with 100-point scale, 30+ action verbs, 16 context markers, 17 source markers, 19 expectation markers. Assistant provides educational explanations |
| Prompt design principles and guidance | ✅ | Quality engine scoring + assistant `explain` mode teaches users why a prompt scored as it did |
| Prompt quality assurance approach | ✅ | Quality engine (`analyse_prompt_fields`), governance policy evaluation, security scan (injection + sensitive data), approval workflow |
| Documentation of limitations, assumptions and usage considerations | ⚠️ | Each prompt has `description`, `context`, `expectations`, `source` fields, but no **formal limitations/assumptions report** as a deliverable |
| Reusable prompt patterns | ✅ | Templates (`is_template`), cloning, prompt inputs, workflow step reuse |
| Guidance on designing prompts for Copilot Skills extension | ❌ | No Copilot Skills-related documentation, tagging, or guidance |

---

## 3. Prompt Library Design

| Requirement | Status | Evidence / Notes |
|-------------|--------|------------------|
| Library structure and organisation | ✅ | Frontend Library page with card grid, filter sidebar, pagination. Backend supports search, multi-filter, sort |
| Taxonomy and metadata design | ✅ | 19 StrEnum taxonomies: BusinessFunction, Application, Task, Audience, Tone, OutputFormat, DataClassification, RiskLevel, etc. JSON tags field on prompts |
| Search and navigation approach | ✅ | Full-text search across name/description/template/goal/task, filter by business_function/application/task/status/risk_level/classification/tag, sort by name/quality_score/created_at/executions |
| Reusable prompt categorisation model | ✅ | Business function + task + application triple categorisation, plus tags for custom taxonomy |
| Consideration of future scalability and maintainability | ⚠️ | SQLite default with PostgreSQL support in config, Docker Compose stack, but no **scalability architecture document** |
| Categorisation of prompts suitable for Copilot Skills | ❌ | No Copilot Skills readiness metadata |

---

## 4. Governance and Sustainability

| Requirement | Status | Evidence / Notes |
|-------------|--------|------------------|
| Ownership and accountability model | ✅ | `owner_id` on prompts, `owner_id` on workflows, USER/AUTHOR/REVIEWER/ADMIN/GOVERNANCE role hierarchy |
| Prompt review and approval processes | ✅ | Lifecycle state machine: DRAFT → SUBMITTED → UNDER_REVIEW → APPROVED → PUBLISHED → DEPRECATED → RETIRED. Approval requests table. Review decisions |
| Version control approach | ✅ | `PromptVersion` table with JSON snapshots, version comparison endpoint, auto-versioning on edit of published prompts |
| Quality assurance processes | ✅ | Quality engine scoring, governance policy evaluation, compliance violation tracking, security scanning |
| Governance responsibilities | ✅ | Role-based access control: ADMIN manages users, GOVERNANCE manages policies, REVIEWER approves, AUTHOR creates, USER executes |
| Maintenance and lifecycle management recommendations | ⚠️ | Lifecycle state machine exists in code, but no **formal maintenance/lifecycle recommendations document** |
| Governance considerations for Copilot Skills | ❌ | No Copilot Skills governance model |

---

## 5. Knowledge Transfer and Capability Uplift

| Requirement | Status | Evidence / Notes |
|-------------|--------|------------------|
| User guidance and instruction materials | ✅ | USERGUIDE.md (end-user guide), WALKTHROUGH.md (detailed non-technical explainer), DEMO.md (guided demo runbook) |
| Reusable templates and artefacts | ✅ | Prompt templates, clone feature, workflow templates, quality engine rubric |
| Recommendations to support sustainable capability development | ⚠️ | Documentation exists but no **formal capability uplift plan** tailored to ATO |
| Guidance materials for maintaining prompts and converting to Copilot Skills | ❌ | No Copilot Skills conversion guidance |

---

## 6. Security, Confidentiality and Information Management

| Requirement | Status | Evidence / Notes |
|-------------|--------|------------------|
| Secure handling of ATO information | ⚠️ | PBKDF2 password hashing, HMAC bearer tokens, role-based access, audit trail. But **not ATO-specific** — no PEIC integration, no ATO security documentation framework |
| Compliance with Australian Government security and privacy expectations | ❌ | No PSPF (Protective Security Policy Framework) alignment, no ISM documentation, no data sovereignty controls |
| Clear arrangements regarding data storage, access, and retention | ❌ | No data retention policy, no data residency enforcement (Australia-only), no access review cadence |
| Ability to work with sensitive or protected information | ⚠️ | `DataClassification` enum (PUBLIC/INTERNAL/CONFIDENTIAL/RESTRICTED), `contains_pii`/`contains_financial_data`/`contains_customer_data` flags, but no actual data handling controls enforced |

---

## 7. Intellectual Property and Reuse

| Requirement | Status | Evidence / Notes |
|-------------|--------|------------------|
| ATO sole ownership and reuse rights to all prompts, libraries, Skills, artefacts, documentation | ❌ | No IP management, licensing, or export feature. Prompts are stored in DB with no IP metadata |

---

## 8. Deliverables Checklist

| Deliverable | Status | Evidence / Notes |
|-------------|--------|------------------|
| **Copilot Prompt Library** | ✅ | The PromptHub Enterprise application itself — full library with 68 prompts, search, filter, version control |
| **Copilot Prompt Development Framework and Methodology** | ⚠️ | Quality engine + assistant embody the methodology, but no **standalone framework document** (methodology is embedded in code) |
| **Prompt Testing, Assumptions, Limitations and Exception Report** | ❌ | No formal testing report document. Tests exist in pytest but are internal, not a deliverable report |
| **User Guides and Usage Instructions** | ✅ | USERGUIDE.md, WALKTHROUGH.md, DEMO.md, PROGRAM_DOCUMENTATION.md |
| **Risk Assessment and Mitigation Recommendations** | ⚠️ | Risk levels (LOW/MEDIUM/HIGH/CRITICAL) and data classification exist on prompts, governance evaluates risk, but no **formal risk assessment and mitigation report** |
| **Copilot Skills Readiness Guidance** | ❌ | No Copilot Skills readiness guidance, recommendations on which prompts are suitable, or future adoption considerations |

---

## Summary of Gaps

### Fully Implemented (✅) — 28 requirements
Core platform is solid: prompt library, quality engine, versioning, governance, analytics, audit, workflows, execution, RAG, RBAC, demo data, testing, documentation.

### Partially Implemented (⚠️) — 10 requirements
Exist in code but need formal deliverable documents or ATO-specific tailoring:
1. Exception handling guidance document
2. Output consistency recommendations document
3. Limitations/assumptions report
4. Scalability architecture document
5. Maintenance/lifecycle recommendations
6. Capability uplift plan
7. ATO-specific security handling
8. Data classification enforcement
9. Prompt development framework document (standalone)
10. Risk assessment and mitigation report

### Not Implemented (❌) — 12 requirements
These are the critical gaps:
1. **Copilot Skills identification** — no metadata/tags to mark prompts as Copilot Skills candidates
2. **Copilot Skills guidance** — no documentation on designing prompts for Skills extension
3. **Copilot Skills governance** — no ownership/maintenance/approval model for Skills
4. **Copilot Skills conversion guidance** — no materials on converting prompts to Skills
5. **Australian Government PSPF compliance** — no protective security policy framework alignment
6. **ISM documentation** — no Information Security Manual documentation structure
7. **Data sovereignty controls** — no Australia-only data residency enforcement
8. **Data retention policy** — no retention/deletion schedule
9. **ATO PEIC integration** — no pre-engagement integrity check support
10. **IP management** — no licensing/IP metadata on prompts
11. **Export/import** — no prompt library export for ATO ownership
12. **Prompt testing report** — no formal deliverable testing report

---

## Priority Recommendations

### High Priority (RFQ Core Deliverables)
1. Add a `copilot_skills_candidate` boolean field to prompts + a `copilot_skills_notes` text field
2. Create `COPILOT_SKILLS_GUIDANCE.md` — how to design prompts suitable for Copilot Skills
3. Create `PROMPT_TESTING_REPORT.md` — formal testing report with sample prompts, test results, limitations
4. Create `RISK_ASSESSMENT.md` — risk assessment and mitigation recommendations
5. Add prompt export endpoint (JSON) so ATO can own all assets

### Medium Priority (Security & Compliance)
6. Create `SECURITY_FRAMEWORK.md` — align with PSPF, document ISM structure
7. Add data residency configuration (enforce Australia-only)
8. Add data retention policy configuration
9. Create `PROMPT_DEV_FRAMEWORK.md` — standalone methodology document

### Lower Priority (Nice-to-Have)
10. Add Copilot Skills governance policies
11. Add capability uplift plan document
12. Add exception handling guidance document
