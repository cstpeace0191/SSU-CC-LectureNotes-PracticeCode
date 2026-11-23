# Implementation Plan: Getting Started Todo Application

**Branch**: `001-getting-started-todo-app` | **Date**: 2026-11-04 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-getting-started-todo-app/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command; its definition describes the execution workflow.

## Summary

Build the full-stack **Getting Started Todo Application** (`backend/` + `client/` application code) as specified in `requirements.txt` and `spec.md`. The application provides a React 19 + React-Bootstrap web interface backed by an Express 5 REST API (`/api/greeting`, `/api/items`, `/api/items/:id`) with dual-mode persistence (MySQL via `mysql2` + `wait-port` when `MYSQL_HOST` is configured, or automatic fallback to local SQLite via `sqlite3`), graceful signal shutdown (`SIGINT`, `SIGTERM`, `SIGUSR2`), input validation (1–255 character non-whitespace task names), accessible inline error recovery (`WCAG 2.1 Level AA`), and comprehensive TDD test suites (`>= 80%` coverage).

## Technical Context

**Language/Version**: Node.js 22 (JavaScript ES6+ / CommonJS in `backend`, ES Modules + JSX in `client`)

**Primary Dependencies**:
- **Backend (`backend/package.json`)**: `express ^5.1.0`, `mysql2 ^3.14.1`, `sqlite3 ^5.1.7`, `uuid ^11.1.0`, `wait-port ^1.1.0`
- **Client (`client/package.json`)**: `react ^19.1.0`, `react-dom ^19.1.0`, `bootstrap ^5.3.6`, `react-bootstrap ^2.10.10`, `@fortawesome/fontawesome-svg-core ^6.5.1`, `@fortawesome/free-solid-svg-icons ^6.5.1`, `@fortawesome/fontawesome-free-regular ^5.0.13`, `@fortawesome/react-fontawesome ^0.2.2`, `prop-types ^15.8.1`, `vite ^6.3.5`, `@vitejs/plugin-react ^4.5.1`, `sass ^1.62.1`

**Storage**: Dual-mode relational persistence — MySQL (`mysql2` when `MYSQL_HOST` or `MYSQL_HOST_FILE` is set) and SQLite (`sqlite3` at `SQLITE_DB_LOCATION` or default `/etc/todos/todo.db` when `MYSQL_HOST` is unset)

**Testing**:
- **Backend**: `jest ^29.7.0` (`backend/spec/`) for unit and route/persistence tests, `prettier ^3.2.4`
- **Client**: `vitest`, `@testing-library/react`, `@testing-library/user-event`, `jsdom`, `vitest-axe` / `axe-core` for component TDD and automated WCAG 2.1 AA audits, plus `eslint ^8.55.0` and `prettier ^3.2.4`

**Target Platform**: Node.js 22 server (port `3000`) and modern desktop/mobile web browsers

**Project Type**: Full-stack web application (`backend` REST API + static file server, `client` React SPA)

**Performance Goals**:
- API CRUD latency: `p95 < 200ms` under expected load (`SC-001`)
- Frontend Core Web Vitals: `LCP < 2.5s`, `INP < 200ms`, `CLS < 0.1` (`SC-002`)

**Constraints**:
- Application code only (`Dockerfile`, `compose.yaml`, and Kubernetes/Helm manifests excluded per Clarification Session `2026-11-04` Q1)
- Task `name` constrained to 1–255 non-whitespace characters (`FR-004`, `FR-005`)
- Inline dismissible error alert with UI state preservation on backend request failure (`FR-015`)
- WCAG 2.1 Level AA keyboard operability and contrast compliance (`FR-014`, `SC-004`)

**Scale/Scope**: Single shared workspace todo list (5 REST endpoints, 2 persistence adapters, 4 primary React components)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle / Gate | Pre-Phase 0 Status | Post-Phase 1 Status | Verification & Design Alignment |
| :--- | :--- | :--- | :--- |
| **I. Code Quality** (Modularity, DRY, zero lint/format errors, externalized config, `prop-types` declared) | ✅ PASS | ✅ PASS | Routes and persistence adapters follow single-responsibility; environment variables (`PORT`, `SQLITE_DB_LOCATION`, `MYSQL_*`, `MYSQL_*_FILE`) externalize all runtime settings; `prop-types` explicitly declared in `client/package.json`; ESLint + Prettier configured. |
| **II. Test-First Approach (NON-NEGOTIABLE)** (Red-Green-Refactor TDD, >=80% line & branch coverage) | ✅ PASS | ✅ PASS | Backend Jest specs (`backend/spec/`) and frontend Vitest + Testing Library specs (`client/src/__tests__/`) will be authored and verified to fail before implementing each module/component. |
| **III. Accessibility** (WCAG 2.1 Level AA, keyboard navigation, semantic HTML/ARIA, `axe-core` checks) | ✅ PASS | ✅ PASS | Icon buttons in `ItemDisplay.jsx` and form controls in `AddNewItemForm.jsx` include explicit `aria-label`s and keyboard operability; error alerts use `role="alert"`; automated `axe-core` assertions included in component tests. |
| **IV. Performance** (`LCP < 2.5s`, `INP < 200ms`, `CLS < 0.1`, API `p95 < 200ms`) | ✅ PASS | ✅ PASS | Lightweight Express 5 handlers and minimal React 19 bundle with no blocking main-thread operations or unbounded queries. *(Container/Helm resource limit gates are scoped out per Clarification Q1; documented in Complexity Tracking below.)* |

## Project Structure

### Documentation (this feature)

```text
specs/001-getting-started-todo-app/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
│   └── rest-api.md      # HTTP endpoints & UI component contracts
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
.prettierrc                      # Shared Prettier formatting rules

backend/
├── package.json
├── src/
│   ├── index.js                 # Express app setup, static serving, DB init, signal shutdown
│   ├── persistence/
│   │   ├── index.js             # Exports mysql.js if MYSQL_HOST is set, else sqlite.js
│   │   ├── mysql.js             # MySQL persistence adapter (mysql2 + wait-port + *_FILE support)
│   │   └── sqlite.js            # SQLite persistence adapter (sqlite3 + auto mkdir)
│   └── routes/
│       ├── getGreeting.js       # GET /api/greeting
│       ├── getItems.js          # GET /api/items
│       ├── addItem.js           # POST /api/items (UUID v4 + 1-255 char validation)
│       ├── updateItem.js        # PUT /api/items/:id (1-255 char + boolean validation)
│       └── deleteItem.js        # DELETE /api/items/:id
└── spec/
    ├── persistence/
    │   ├── index.spec.js        # Persistence selector & signal shutdown tests
    │   ├── sqlite.spec.js       # SQLite adapter CRUD & lifecycle tests
    │   └── mysql.spec.js        # MySQL adapter unit tests (mocked mysql2/wait-port)
    └── routes/
        ├── getGreeting.spec.js  # Greeting route tests
        ├── getItems.spec.js     # List items route tests
        ├── addItem.spec.js      # Add item & validation tests
        ├── updateItem.spec.js   # Update item & validation tests
        └── deleteItem.spec.js   # Delete item route tests

client/
├── package.json
├── index.html
├── vite.config.js               # Vite bundler, /api dev proxy, and Vitest config
├── .eslintrc.cjs                # ESLint configuration (react, react-hooks, react-refresh)
├── src/
│   ├── main.jsx                 # React 19 root mount
│   ├── App.jsx                  # Top-level layout (Container, Row, Col, Greeting, TodoListCard)
│   ├── index.scss               # Bootstrap & custom styles (.item, .completed, AA contrast)
│   ├── components/
│   │   ├── Greeting.jsx         # Fetches and displays "Hello world!" banner + error alert
│   │   ├── TodoListCard.jsx     # Manages items state, loading, empty state, and error alert
│   │   ├── AddNewItemForm.jsx   # Controlled task input (1-255 chars), Add/Adding button
│   │   └── ItemDisplay.jsx      # Accessible toggle completion & delete item controls
│   └── __tests__/
│       ├── setup.js             # Vitest + @testing-library/jest-dom + fetch test setup
│       ├── Greeting.test.jsx
│       ├── AddNewItemForm.test.jsx
│       ├── ItemDisplay.test.jsx
│       ├── TodoListCard.test.jsx
│       └── a11y.test.jsx        # Automated axe-core WCAG 2.1 Level AA verification
```

**Structure Decision**: Two-package web application layout (`backend/` and `client/`) matching the exact directory and file paths specified in `requirements.txt`.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation / Exemption | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| Omission of Helm chart / container manifests (`helm lint`, K8s CPU/memory limits in Principles I & IV) | User explicitly clarified in `/speckit-clarify` (Session `2026-11-04`, Q1 → Option C) that this feature's scope is **Application code only** (`backend/` and `client/`). | Generating Helm charts or Dockerfiles in this feature would violate the user's explicit scope boundary; container and Helm manifests can be tracked in a dedicated deployment feature track. |
