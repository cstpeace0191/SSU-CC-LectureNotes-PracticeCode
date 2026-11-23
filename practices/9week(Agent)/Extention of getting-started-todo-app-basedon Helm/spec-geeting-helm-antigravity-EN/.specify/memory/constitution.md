<!--
Sync Impact Report
- Version change: N/A (template) → 1.0.0
- Modified principles:
  - [PRINCIPLE_1_NAME] → I. Code Quality
  - [PRINCIPLE_2_NAME] → II. Test-First Approach (NON-NEGOTIABLE)
  - [PRINCIPLE_3_NAME] → III. Accessibility
  - [PRINCIPLE_4_NAME] → IV. Performance
  - [PRINCIPLE_5_NAME] → Removed (user specified 4 core principles)
- Added sections:
  - Quality & Performance Constraints
  - Development Workflow & Quality Gates
- Removed sections:
  - Placeholder Principle 5 ([PRINCIPLE_5_NAME])
- Templates requiring updates:
  - .specify/templates/plan-template.md (✅ compatible with Constitution Check gates)
  - .specify/templates/spec-template.md (✅ compatible with functional/non-functional requirements)
  - .specify/templates/tasks-template.md (✅ compatible with test-first task ordering)
- Follow-up TODOs: None
-->
# spec-geeting-helm-antigravity Constitution

## Core Principles

### I. Code Quality
All production and infrastructure code MUST adhere to strict modularity, single-responsibility, and clean-code standards.
- Code MUST pass automated linting, formatting, and static analysis checks with zero errors and zero unapproved warnings before merge.
- Functions, components, and Helm templates MUST remain small, composable, and free of duplicated logic (DRY).
- Magic values and environment-specific settings MUST be externalized into typed configuration or documented `values.yaml` entries; hardcoding environment parameters in source or templates is prohibited.
- Public interfaces, configuration keys, and non-trivial algorithms MUST include concise, accurate documentation.

**Rationale**: Consistent code quality reduces cognitive load, prevents configuration drift across environments, and ensures long-term maintainability.

### II. Test-First Approach (NON-NEGOTIABLE)
Test-Driven Development (TDD) is mandatory for all new features, bug fixes, and chart/deployment changes.
- Automated tests (unit, integration, and chart validation/template tests) MUST be written and verified to fail before implementation code is authored.
- The Red-Green-Refactor cycle MUST be strictly followed: write a failing test (Red), implement the minimal code to pass (Green), and clean up while keeping tests green (Refactor).
- Pull requests that introduce behavior changes without corresponding pre-written tests MUST be rejected in review.
- Every bug fix MUST begin with a regression test that reproduces the defect prior to applying the fix.

**Rationale**: Writing tests first enforces testable architecture, clarifies requirements upfront, and prevents regressions before code reaches production.

### III. Accessibility
All user-facing interfaces MUST be inclusive and accessible by default, conforming to WCAG 2.1 Level AA standards at minimum.
- UI components MUST use semantic HTML elements and valid ARIA attributes only where native semantics are insufficient.
- Every interactive workflow MUST be operable via keyboard navigation alone with visible, logical focus states and no focus traps.
- Text and interactive elements MUST meet or exceed WCAG AA color contrast ratios (4.5:1 for normal text, 3:1 for large text and UI components).
- Automated accessibility checks (e.g., axe-core or Lighthouse a11y audits) MUST run in verification workflows with zero critical or serious violations permitted.

**Rationale**: Accessibility is a baseline quality requirement ensuring every user can perceive, navigate, and interact with the application regardless of ability or assistive technology.

### IV. Performance
Application and deployment artifacts MUST meet defined responsiveness, resource efficiency, and scalability budgets.
- Web interfaces MUST target Core Web Vitals thresholds: Largest Contentful Paint (LCP) < 2.5s, Interaction to Next Paint (INP) < 200ms, and Cumulative Layout Shift (CLS) < 0.1.
- Backend API endpoints MUST maintain p95 response latency under 200ms for standard CRUD operations under expected load.
- Container images and Kubernetes/Helm workloads MUST define explicit CPU and memory `requests` and `limits`, use minimal base images, and avoid unnecessary runtime dependencies.
- Performance regressions exceeding 10% on critical paths or bundle size budgets MUST be blocked or explicitly justified and approved during review.

**Rationale**: Predictable latency and bounded resource consumption directly impact user satisfaction and cluster operational stability.

## Quality & Performance Constraints

- **Static Verification**: Source files and Helm charts (`helm lint`, `helm template`) MUST validate cleanly prior to deployment or merge.
- **Test Coverage**: Critical business logic and API routes MUST maintain at least 80% line and branch coverage.
- **Accessibility Auditing**: UI changes MUST be verified against keyboard navigation, screen reader semantics, and contrast requirements before task completion.
- **Resource Hygiene**: Unbounded queries, blocking main-thread operations, and unindexed lookups on growing datasets are prohibited.

## Development Workflow & Quality Gates

1. **Specification & Planning**: Every feature MUST start with a clear specification (`spec.md`) and implementation plan (`plan.md`) that passes the Constitution Check against all four Core Principles.
2. **Red-Green-Refactor Execution**: Tasks in `tasks.md` MUST sequence test creation before implementation tasks.
3. **Pre-Merge Quality Gates**: All unit tests, integration tests, accessibility checks, linters, and performance budget validations MUST pass before a feature is marked complete.
4. **Exception Handling**: Any temporary deviation from a principle requires documented justification in the feature plan's `Complexity Tracking` table and an explicit remediation task.

## Governance

This Constitution supersedes all other local conventions and ad-hoc practices within the repository.
- **Amendment Procedure**: Any proposed change to principles or constraints MUST be documented with rationale, reviewed by project maintainers, and accompanied by updates to affected templates or active specifications.
- **Versioning Policy**: This document follows Semantic Versioning (`MAJOR.MINOR.PATCH`):
  - `MAJOR`: Backward-incompatible removals or redefinitions of core principles or governance rules.
  - `MINOR`: Addition of new principles, sections, or materially expanded compliance requirements.
  - `PATCH`: Wording clarifications, formatting fixes, and non-semantic refinements.
- **Compliance Review**: Every specification, implementation plan, task list, and code review MUST verify compliance with these principles before approval.

**Version**: 1.0.0 | **Ratified**: 2026-11-04 | **Last Amended**: 2026-11-04
