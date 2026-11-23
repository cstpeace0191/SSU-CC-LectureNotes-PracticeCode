# Getting Started Todo App (FastAPI Backend)

This application is a Todo application built with **FastAPI** + **Uvicorn** on the backend and **React** on the frontend.

## 1. Requirements
- Python 3.9+ (or Docker)

## 2. Installation
```bash
pip install -r requirements.txt
```

## 3. Running with Uvicorn (Local Host)
```bash
uvicorn src.main:app --host 0.0.0.0 --port 3000 --reload
```
or run directly via Python:
```bash
python src/main.py
```

## 4. Accessing the App
- **Web App**: [http://localhost:3000](http://localhost:3000)
- **FastAPI Interactive Docs (Swagger UI)**: [http://localhost:3000/docs](http://localhost:3000/docs)
- **Alternative Docs (ReDoc)**: [http://localhost:3000/redoc](http://localhost:3000/redoc)

## 5. Database Options
- **SQLite (Default)**: Automatically creates a `todo.db` file (or uses path from `SQLITE_DB_LOCATION`).
- **MySQL**: Set environment variable `MYSQL_HOST` to connect to MySQL database.

## 6. Automated Testing with `pytest`

`pytest` is the automated test runner for the Python backend. It performs unit and integration tests defined under the `spec/` directory to verify the application's correctness.

### What `pytest` Does in this Project:
1. **Persistence Layer Testing (`spec/persistence/test_sqlite.py`)**:
   - Tests asynchronous SQLite database initialization, table creation (`todo_items`), and teardown.
   - Verifies CRUD operations: adding items, fetching the entire list, single item lookup, updating item status/name, and deletion.
2. **REST API Route Testing (`spec/routes/`)**:
   - **`test_getItems.py`**: Validates `GET /items` response structure and DB interaction.
   - **`test_addItem.py`**: Verifies `POST /items` creates a unique UUID v4 and stores the new task with `completed: False`.
   - **`test_updateItem.py`**: Verifies `PUT /items/{id}` updates task completion/name and returns the updated item.
   - **`test_deleteItem.py`**: Verifies `DELETE /items/{id}` removes the specified item from the DB.
3. **Async / Mock Testing**:
   - Uses `pytest-asyncio` to execute non-blocking coroutines and `unittest.mock.AsyncMock` to isolate route tests from the physical database.

### Running the Test Suite:
```bash
# Run all tests
pytest

# Run with verbose output (shows each test case status)
pytest -v
```

## 7. Docker Build and Run

You can containerize and run the entire FastAPI + React Todo application using Docker.

### 1) Build the Docker Image
Build the container image using the project's `Dockerfile`:
```bash
docker build -t getting-started-fastapi .
```

### 2) Run the Docker Container

#### Basic Run (Ephemeral storage):
```bash
docker run -dp 3000:3000 --name todo-app getting-started-fastapi
```

#### Persistent Run with Named Volume (Recommended for SQLite):
Mount a Docker volume (`todo-db`) to preserve todo items across container restarts and updates:
```bash
docker run -dp 3000:3000 --name todo-app -v todo-db:/etc/todos getting-started-fastapi
```

#### Run with External MySQL Database:
```bash
docker run -dp 3000:3000 --name todo-app \
  -e MYSQL_HOST=mysql-server \
  -e MYSQL_USER=root \
  -e MYSQL_PASSWORD=secret \
  -e MYSQL_DB=todos \
  getting-started-fastapi
```

### 3) Useful Container Management Commands
```bash
# View live container logs
docker logs -f todo-app

# Stop the container
docker stop todo-app

# Restart the container
docker start todo-app

# Remove the container
docker rm -f todo-app
```