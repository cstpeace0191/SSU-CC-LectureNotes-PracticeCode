# Quickstart & Validation Guide: Getting Started Todo Application

**Feature**: `001-getting-started-todo-app`
**Date**: 2026-11-04
**Related Artifacts**: [spec.md](./spec.md) | [data-model.md](./data-model.md) | [contracts/rest-api.md](./contracts/rest-api.md)

---

## 1. Prerequisites

- **Node.js**: v22.x (with bundled `npm`)
- **Operating System**: Linux, macOS, or Windows (SQLite fallback path configurable via `SQLITE_DB_LOCATION`)
- *(Optional)* **MySQL 9.3** instance if validating external database persistence mode (`FR-011`)

---

## 2. Dependency Installation

Install dependencies independently for the backend and frontend packages from the repository root:

```bash
# Install backend dependencies
cd backend && npm install

# Install frontend client dependencies
cd ../client && npm install
```

---

## 3. Running Automated Tests & Quality Gates

Per the project [Constitution](../../.specify/memory/constitution.md), all unit, integration, accessibility, and formatting checks must pass:

```bash
# 1. Backend unit & route tests (with coverage >= 80%)
cd backend
npm test

# 2. Backend formatting check
npm run format-check

# 3. Frontend unit, interaction & WCAG 2.1 AA axe accessibility tests
cd ../client
npm test

# 4. Frontend ESLint & Prettier checks
npm run lint
npm run format-check
```

---

## 4. Running the Application Locally (SQLite Mode - Default)

When `MYSQL_HOST` is not set, the backend automatically persists items to a local SQLite database file (`FR-012`).

```bash
# Terminal 1: Start the backend API server on port 3000
cd backend
SQLITE_DB_LOCATION=./data/todo.db npm run dev

# Terminal 2: Start the Vite development server on port 5173 (proxies /api -> localhost:3000)
cd client
npm run dev
```

Open `http://localhost:5173` in a browser to interact with the application, or build the production frontend bundle (`cd client && npm run build`) and copy/serve it via the backend on `http://localhost:3000`.

---

## 5. Running with External MySQL Persistence (`FR-011`)

Provide the MySQL connection variables (or `*_FILE` secret paths) when starting the backend:

```bash
cd backend
MYSQL_HOST=127.0.0.1 \
MYSQL_USER=root \
MYSQL_PASSWORD=secret \
MYSQL_DB=todos \
npm start
```

The backend waits for the MySQL port (`3306`) to open, initializes the `todo_items` table if absent, and stores all items in MySQL.

---

## 6. End-to-End Validation Scenarios

1. **Greeting & Empty State (`US4`, `US1`)**:
   - Verify `GET http://localhost:3000/api/greeting` returns `{"greeting":"Hello world!"}`.
   - Open the web UI with an empty database and confirm the `"Hello world!"` heading and `"No items yet! Add one above!"` message are visible.
2. **Input Validation & Item Creation (`US1`, `FR-004`, `FR-005`)**:
   - Confirm the `"Add Item"` button is disabled when the input is empty or contains only spaces (`"   "`).
   - Enter `"Write TDD tests"` and submit; verify the item is listed as incomplete and persists across a page reload.
3. **Toggle Completion (`US2`, `FR-007`, `FR-008`)**:
   - Activate the checkbox toggle on `"Write TDD tests"`; verify the row receives the `.completed` styling and `GET /api/items` shows `"completed": true`.
4. **Delete Item (`US3`, `FR-009`)**:
   - Activate the trash icon on `"Write TDD tests"`; verify the item is removed and the empty-state message returns.
5. **Failure Recovery (`FR-015`)**:
   - Stop the backend server and attempt to add an item in the UI; verify the `"Adding..."` button resets to `"Add Item"`, the typed text remains in the input box, and a dismissible error alert is displayed.
6. **Graceful Shutdown (`US5`, `FR-013`)**:
   - Send `SIGINT` (`Ctrl+C`) or `SIGTERM` to the running backend process and verify it logs/completes clean database teardown before exiting with code `0`.
7. **Performance & Web Vitals Budgets (`SC-001`, `SC-002`)**:
   - Verify CRUD API endpoints (`GET /api/items`, `POST /api/items`, `PUT /api/items/:id`, `DELETE /api/items/:id`) complete in `< 200ms` (p95) under normal local load, and initial page load meets `LCP < 2.5s` and `CLS < 0.1`.

