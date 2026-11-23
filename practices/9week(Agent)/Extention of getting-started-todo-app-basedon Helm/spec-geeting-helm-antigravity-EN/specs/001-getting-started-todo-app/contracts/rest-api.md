# REST API & UI Contracts: Getting Started Todo Application

**Feature**: `001-getting-started-todo-app`
**Date**: 2026-11-04
**Base Path**: `/api` (served on port `3000` by Express; proxied in development by Vite `/api` proxy)

---

## 1. HTTP Endpoints

### 1.1 `GET /api/greeting`

Returns the static greeting message used by the frontend banner to verify backend connectivity (`FR-010`).

- **Request**: No parameters or body.
- **Response `200 OK`** (`application/json`):
  ```json
  {
    "greeting": "Hello world!"
  }
  ```

---

### 1.2 `GET /api/items`

Retrieves all stored todo items (`FR-001`).

- **Request**: No parameters or body.
- **Response `200 OK`** (`application/json`):
  ```json
  [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Buy milk",
      "completed": false
    }
  ]
  ```

---

### 1.3 `POST /api/items`

Creates a new todo item with a generated UUID v4 `id` and `completed: false` (`FR-004`, `FR-005`, `FR-006`).

- **Request Headers**: `Content-Type: application/json`
- **Request Body**:
  ```json
  {
    "name": "Buy milk"
  }
  ```
- **Validation Rules**:
  - `name` MUST be a string.
  - `name.trim().length` MUST be `>= 1` (empty or whitespace-only strings rejected).
  - `name.length` MUST be `<= 255`.
- **Response `200 OK`** (`application/json`):
  ```json
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Buy milk",
    "completed": false
  }
  ```
- **Response `400 Bad Request`** (`application/json`):
  ```json
  {
    "error": "Task name must be a non-empty string up to 255 characters."
  }
  ```

---

### 1.4 `PUT /api/items/:id`

Updates an existing todo item's `name` and `completed` state (`FR-007`, `FR-008`).

- **URL Parameters**:
  - `id` (string, UUID v4 of the target item)
- **Request Headers**: `Content-Type: application/json`
- **Request Body**:
  ```json
  {
    "name": "Buy milk",
    "completed": true
  }
  ```
- **Validation Rules**:
  - `name` MUST be a non-whitespace string of 1 to 255 characters.
  - `completed` MUST be a boolean (`true` or `false`).
- **Response `200 OK`** (`application/json`):
  ```json
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Buy milk",
    "completed": true
  }
  ```
- **Response `400 Bad Request`** (`application/json`):
  ```json
  {
    "error": "Invalid item payload: name (1-255 chars) and boolean completed are required."
  }
  ```

---

### 1.5 `DELETE /api/items/:id`

Permanently deletes an existing todo item (`FR-009`).

- **URL Parameters**:
  - `id` (string, UUID v4 of the target item)
- **Response `200 OK`**: Empty body.

---

## 2. UI Component Contracts (`client/src/components/`)

| Component | Props | Required UI States & Accessibility (`FR-014`, `FR-015`) |
| :--- | :--- | :--- |
| `Greeting` | None | Fetches `GET /api/greeting`; renders `<h1>Hello world!</h1>`; displays dismissible `<Alert variant="danger" role="alert">` if fetch fails. |
| `TodoListCard` | None | Fetches `GET /api/items`; shows `"Loading..."` while `items === null`; shows `"No items yet! Add one above!"` when `items.length === 0`; shows dismissible `<Alert variant="danger" role="alert">` on load/mutation error. |
| `AddNewItemForm` | `onNewItem: PropTypes.func.isRequired` | Controlled input (`maxLength={255}`, accessible label/placeholder); submit button disabled when `newItem.trim().length === 0` or `submitting === true`; button text shows `"Adding..."` during POST and `"Add Item"` otherwise; preserves input text and displays dismissible error alert on failure. |
| `ItemDisplay` | `item: PropTypes.shape({ id, name, completed }).isRequired`, `onItemUpdate: PropTypes.func.isRequired`, `onItemRemoval: PropTypes.func.isRequired` | Renders `.item` container with `.completed` class when `item.completed === true`; left toggle `<Button>` with accessible `aria-label` (`Mark "<name>" as complete/incomplete`); right delete `<Button>` with accessible `aria-label` (`Delete "<name>"`). |

