# Phase 0 Research: Getting Started Todo Application

**Feature**: `001-getting-started-todo-app`
**Date**: 2026-11-04
**Inputs**: `requirements.txt`, `specs/001-getting-started-todo-app/spec.md`, `.specify/memory/constitution.md`

---

## 1. Backend Framework & Runtime Stack

- **Decision**: Use **Node.js 22** with **Express `^5.1.0`** (`backend/package.json`), **UUID `^11.1.0`** (UUID v4 generation), **Jest `^29.7.0`** for unit and route testing, **nodemon `^3.0.3`** for local development, and **Prettier `^3.2.4`** for code formatting.
- **Rationale**: Directly aligns with `requirements.txt`. Express 5 provides native promise rejection forwarding in async route handlers, simplifying error propagation when persistence calls fail.
- **Alternatives Considered**:
  - *Fastify or Koa*: Rejected because `requirements.txt` explicitly specifies Express `^5.1.0` and the route layout (`backend/src/routes/*.js`).
  - *Express 4.x*: Rejected because `requirements.txt` pins `^5.1.0` (resolved `5.1.0`).

---

## 2. Dual-Mode Persistence Strategy (`sqlite3` vs. `mysql2`)

- **Decision**: Implement a unified persistence interface (`init()`, `teardown()`, `getItems()`, `getItem(id)`, `storeItem(item)`, `updateItem(id, item)`, `removeItem(id)`) in `backend/src/persistence/index.js` that dynamically exports `backend/src/persistence/mysql.js` when `process.env.MYSQL_HOST` is defined, and `backend/src/persistence/sqlite.js` otherwise.
  - **SQLite (`sqlite3 ^5.1.7`)**: Uses `process.env.SQLITE_DB_LOCATION || '/etc/todos/todo.db'`, recursively creating missing parent directories (`fs.mkdirSync(dir, { recursive: true })`) before opening the database and creating `todo_items (id varchar(36), name varchar(255), completed boolean)`.
  - **MySQL (`mysql2 ^3.14.1` + `wait-port ^1.1.0`)**: Supports direct environment variables (`MYSQL_HOST`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DB`) and Docker secret file variants (`MYSQL_HOST_FILE`, `MYSQL_USER_FILE`, `MYSQL_PASSWORD_FILE`, `MYSQL_DB_FILE`), waits for the MySQL port via `wait-port` before initializing the connection pool, and creates the `todo_items` table with `DEFAULT CHARSET utf8mb4`.
- **Rationale**: Satisfies `FR-011`, `FR-012`, `FR-013`, and `requirements.txt` while keeping route handlers completely agnostic of the underlying database engine.
- **Alternatives Considered**:
  - *ORM (Prisma / Sequelize / Knex)*: Rejected because `requirements.txt` specifies direct `mysql2` and `sqlite3` drivers with zero ORM overhead.

---

## 3. Frontend Framework, Styling & Prop Validation

- **Decision**: Use **React `^19.1.0`** with **Vite `^6.3.5`** (`@vitejs/plugin-react ^4.5.1`), **Bootstrap `^5.3.6`**, **React-Bootstrap `^2.10.10`**, **SCSS (`sass ^1.62.1`)**, **FontAwesome (`@fortawesome/react-fontawesome ^0.2.2`, `@fortawesome/free-solid-svg-icons ^6.5.1`, `@fortawesome/fontawesome-free-regular ^5.0.13`)**, and explicitly declare **`prop-types ^15.8.1`** in `client/package.json`.
- **Rationale**: Matches `requirements.txt` component structure (`Greeting.jsx`, `TodoListCard.jsx`, `AddNewItemForm.jsx`, `ItemDisplay.jsx`) and resolves the undeclared transitive dependency warning noted in `requirements.txt` lines 66–70 by declaring `prop-types` explicitly.
- **Alternatives Considered**:
  - *Tailwind CSS or Material UI*: Rejected because `requirements.txt` specifies `bootstrap` and `react-bootstrap`.

---

## 4. Input Validation & Error Recovery (Clarifications Integration)

- **Decision**:
  - **Task Name Validation (`FR-004`, `FR-005`)**: Trim input on validation; disable the `"Add Item"` submit button in `AddNewItemForm.jsx` when `newItem.trim().length === 0` or `newItem.length > 255` (and enforce `maxLength={255}` on the form control). Enforce matching validation in `POST /api/items` and `PUT /api/items/:id` on the backend (returning HTTP `400 Bad Request` if `name` is missing, non-string, whitespace-only, or exceeds 255 characters).
  - **Failure Recovery (`FR-015`)**: Wrap `fetch` calls in `Greeting.jsx`, `TodoListCard.jsx`, `AddNewItemForm.jsx`, and `ItemDisplay.jsx` with `try/catch` and `response.ok` checks. On failure, reset in-progress states (`submitting = false`, `loading = false`), preserve current input text and list state, and render a dismissible React-Bootstrap `<Alert variant="danger">` with `role="alert"` so assistive technologies announce the error immediately.
- **Rationale**: Directly implements the three Session `2026-11-04` clarifications in `spec.md` while maintaining WCAG 2.1 Level AA accessibility compliance.
- **Alternatives Considered**:
  - *Silent console logging on error*: Rejected by user clarification in favor of Option A (inline dismissible error alert + state preservation).

---

## 5. Accessibility (WCAG 2.1 AA) & Frontend Testing Strategy

- **Decision**:
  - Ensure all interactive controls use accessible `<button>` elements (or proper ARIA roles/labels), explicit `aria-label` attributes on icon-only controls (completion toggle checkbox button and delete trash button in `ItemDisplay.jsx`), associated `<Form.Label>` or `aria-label` on the task input in `AddNewItemForm.jsx`, and WCAG AA compliant color contrast (`>= 4.5:1`).
  - Use **Vitest**, **React Testing Library (`@testing-library/react`, `@testing-library/user-event`)**, **`jsdom`**, and **`vitest-axe` / `axe-core`** in `client/` alongside **Jest** in `backend/` to satisfy Constitution Principle II (Test-First TDD) and Principle III (Automated Accessibility Auditing).
- **Rationale**: Constitution Principle II requires automated unit/integration tests written before implementation, and Principle III mandates automated accessibility checks (`axe-core`) with zero critical or serious violations.
- **Alternatives Considered**:
  - *Backend-only testing*: Rejected because Constitution Principle II & III require test-first verification and automated accessibility checks for UI components.

---

## 6. Scope Boundary: Application Code Only vs. Constitution Helm Gates

- **Decision**: Scope this feature strictly to the `backend/` and `client/` application code as clarified in `spec.md` (`Application code only; container and Kubernetes/Helm deployment manifests are excluded from scope`). Record the omission of `Dockerfile`, `compose.yaml`, and Helm charts in the `plan.md` `Constitution Check` / `Complexity Tracking` table as an explicit user-directed scope boundary rather than a code quality violation.
- **Rationale**: User explicitly selected Option C (`Application code only`) during `/speckit-clarify`.
- **Alternatives Considered**:
  - *Generating Helm charts in this feature*: Rejected per user clarification `Q1 -> C`.

