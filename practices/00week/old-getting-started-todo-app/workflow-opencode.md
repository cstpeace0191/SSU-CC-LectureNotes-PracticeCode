# Getting Started Todo App — 동작 구조

## 개요

React + Vite 프론트엔드, Node.js/Express 백엔드, MySQL 데이터베이스로 구성된 간단한 Todo 애플리케이션.
Docker 모범 사례를 시연하기 위한 샘플 프로젝트.

---

## 1. 개발 모드 (compose.yml / compose-dev-build.yml)

```mermaid
graph TB
    Browser["브라우저<br/>http://localhost:80"]

    subgraph "Docker Compose Network"
        Traefik["Traefik (proxy)<br/>포트 80 → 라우팅"]

        subgraph "Frontend Layer"
            Client["client:5173<br/>Vite Dev Server<br/>React SPA"]
        end

        subgraph "Backend Layer"
            Backend["backend:3000<br/>Express API (nodemon)"]
            MySQL["mysql:3306<br/>MySQL 8.0<br/>볼륨: todo-mysql-data"]
            SQLite["SQLite Fallback<br/>(MYSQL_HOST 미설정 시)"]
        end

        subgraph "Admin Layer"
            PhpMyAdmin["phpmyadmin:80<br/>DB 관리 UI<br/>http://db.localhost"]
        end
    end

    Browser --> Traefik

    Traefik -- "Host(localhost) && PathPrefix(/api)" --> Backend
    Traefik -- "Host(localhost)" --> Client
    Traefik -- "Host(db.localhost)" --> PhpMyAdmin

    Client -- "/api 프록시 (Vite config)" --> Backend

    Backend --> MySQL
    Backend -.-> SQLite
    PhpMyAdmin --> MySQL

    style Browser fill:#e1f5fe
    style Traefik fill:#fff3e0
    style Client fill:#e8f5e9
    style Backend fill:#e8f5e9
    style MySQL fill:#fce4ec
    style PhpMyAdmin fill:#f3e5f5
```

---

## 2. 프로덕션 모드 (compose-prod-build.yml)

```mermaid
graph TB
    Browser["브라우저<br/>http://localhost:80"]

    subgraph "Docker Compose Network"
        Traefik["Traefik (proxy)<br/>포트 80 → 라우팅"]

        subgraph "Backend (단일 서비스)"
            Backend["backend:3000<br/>Express (final stage)<br/>- 정적 파일: /src/static/<br/>- API: /api/*"]
            MySQL["mysql:3306<br/>MySQL 8.0"]
        end
    end

    Browser --> Traefik
    Traefik -- "Host(localhost)" --> Backend
    Backend --> MySQL

    style Browser fill:#e1f5fe
    style Traefik fill:#fff3e0
    style Backend fill:#e8f5e9
    style MySQL fill:#fce4ec
```

> **프로덕션**에서는 프론트엔드가 정적 파일로 빌드되어 백엔드 이미지에 포함됨 (`client` 서비스 없음, phpMyAdmin 제거)

---

## 3. Dockerfile 멀티-스테이지 빌드

```mermaid
graph LR
    subgraph "Build Stages"
        Base["base<br/>node:20<br/>WORKDIR /usr/local/app"]

        ClientBase["client-base<br/>COPY client/ + yarn install"]

        ClientDev["client-dev<br/>CMD yarn dev<br/>→ Vite:5173"]

        ClientBuild["client-build<br/>yarn build<br/>→ /usr/local/app/dist"]

        BackendDev["backend-dev<br/>COPY backend/ + yarn install<br/>CMD yarn dev (nodemon)<br/>→ Express:3000"]

        Test["test<br/>yarn test<br/>(Jest)"]

        Final["final<br/>yarn install --production<br/>+ dist/ → ./src/static/<br/>CMD node src/index.js<br/>→ Express:3000"]
    end

    Base --> ClientBase
    ClientBase --> ClientDev
    ClientBase --> ClientBuild
    Base --> BackendDev
    BackendDev --> Test
    Test --> Final
    ClientBuild --> Final

    style Base fill:#e0e0e0
    style ClientDev fill:#e8f5e9
    style ClientBuild fill:#a5d6a7
    style BackendDev fill:#fff9c4
    style Test fill:#ffcc80
    style Final fill:#ef9a9a
```

---

## 4. API 요청 생명주기

```mermaid
sequenceDiagram
    participant User as 사용자
    participant Browser as 브라우저 (React)
    participant Proxy as Traefik
    participant API as Express API
    participant DB as MySQL

    Note over User,DB: 인사말 조회
    User->>Browser: 페이지 접속
    Browser->>Proxy: GET /
    Proxy->>Browser: index.html + React 번들
    Browser->>Proxy: GET /api/greeting
    Proxy->>API: GET /api/greeting
    API-->>Proxy: {"greeting": "Hello world!"}
    Proxy-->>Browser: JSON 응답
    Browser->>User: "Hello world!" 표시

    Note over User,DB: Todo 목록 조회
    Browser->>Proxy: GET /api/items
    Proxy->>API: GET /api/items
    API->>DB: SELECT * FROM todo_items
    DB-->>API: [{id, name, completed}, ...]
    API-->>Proxy: JSON 배열
    Proxy-->>Browser: 목록 표시

    Note over User,DB: Todo 항목 추가
    User->>Browser: 할 일 입력 + Add Item
    Browser->>Proxy: POST /api/items {name: "..."}
    Proxy->>API: POST /api/items
    API->>API: UUID 생성, completed=false
    API->>DB: INSERT INTO todo_items
    DB-->>API: OK
    API-->>Proxy: 생성된 항목
    Proxy-->>Browser: 목록 갱신

    Note over User,DB: 완료 토글
    User->>Browser: 체크박스 클릭
    Browser->>Proxy: PUT /api/items/:id {completed: true}
    Proxy->>API: UPDATE todo_items
    API->>DB: UPDATE SET completed=true
    DB-->>API: OK
    API-->>Proxy: 갱신된 항목
    Proxy-->>Browser: UI 갱신

    Note over User,DB: 항목 삭제
    User->>Browser: 삭제 버튼 클릭
    Browser->>Proxy: DELETE /api/items/:id
    Proxy->>API: DELETE FROM todo_items
    API->>DB: DELETE WHERE id=?
    DB-->>API: OK
    API-->>Proxy: 200 OK
    Proxy-->>Browser: 목록 갱신
```

---

## 5. 전체 서비스 관계 및 포트

```mermaid
graph TB
    subgraph "External"
        Browser["브라우저"]
    end

    subgraph "Docker Network"
        Traefik["Traefik<br/>80:80"]

        subgraph "Dev Services"
            Client["Client<br/>5173"]
            PhpMyAdmin["phpMyAdmin<br/>80"]
        end

        subgraph "Core Services"
            Backend["Backend<br/>3000"]
            MySQL["MySQL<br/>3306"]
            Volume["볼륨<br/>todo-mysql-data"]
        end
    end

    Browser -- "localhost:80" --> Traefik
    Traefik -- "/api/*" --> Backend
    Traefik -- "/*" --> Client
    Traefik -- "db.localhost" --> PhpMyAdmin
    Backend -- "mysql:3306" --> MySQL
    MySQL --> Volume

    linkStyle default stroke-width:2px
```

---

## 환경 변수

| 변수 | 용도 | 기본값 |
|------|------|--------|
| `MYSQL_HOST` | MySQL 호스트명 | `mysql` |
| `MYSQL_USER` | MySQL 사용자명 | `root` |
| `MYSQL_PASSWORD` | MySQL 비밀번호 | `secret` |
| `MYSQL_DB` | MySQL 데이터베이스명 | `todos` |
| `SQLITE_DB_LOCATION` | SQLite 파일 경로 | `/etc/todos/todo.db` |
| `MYSQL_ROOT_PASSWORD` | MySQL root 비밀번호 | `secret` |
| `PMA_HOST` | phpMyAdmin 연결 대상 | `mysql` |

> `MYSQL_HOST` 환경 변수가 설정되면 MySQL, 없으면 SQLite를 사용합니다.
> 모든 `*_FILE` 접미사 변수는 Docker Secret을 지원합니다.
