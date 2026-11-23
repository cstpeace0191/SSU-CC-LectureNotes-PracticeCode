# Gemini AI Chat System - Architecture & Workflow Specification

This document provides a comprehensive technical overview of the conversational AI web service based on **Google Gemini 3.7 Flash**, detailing system architecture, project directory structure, backend/frontend operational workflows, and Mermaid diagrams.

---

## 1. Key Features

| Category | Feature | Description |
| :--- | :--- | :--- |
| **AI Model & Chat** | **Gemini 3.7 Flash** | High-performance multi-turn general Q&A powered by the official `google-genai` SDK |
| **Realtime Tools** | **Function Calling** | Automated retrieval of **real-time weather** (`Open-Meteo API`) and **local time** (`ZoneInfo`) for cities worldwide |
| **Language Consistency** | **Language Matching** | Automatically detects user input language (Korean, English, Japanese, French, etc.) and generates responses in the exact same language |
| **Session State** | **Multi-turn Sessions** | In-memory conversation context management keyed by `session_id`, with one-click reset (`New Chat / Reset`) |
| **UI/UX** | **Timeline Interface** | Gemini.ai-style clean white theme, sequential question-and-answer accumulation, markdown parser, code block syntax highlighting, and one-click copy |
| **Network & Deployment** | **Traefik Reverse Proxy** | Unified routing via port `3000` for both frontend static assets and backend API endpoints in a fully containerized `Docker Compose` environment |

---

## 2. Directory and File Structure

```plaintext
geminiAI-Sever/
├── compose.yaml                      # Docker Compose orchestration (Traefik, Backend, Frontend)
├── Architecture_Workflow-KR.md       # Architecture & Workflow documentation (Korean)
├── Architecture_Workflow-EN.md       # Architecture & Workflow documentation (English)
├── How-to-Execute(KR).md             # 3 execution workflows guide (Korean)
├── How-to-Execute(EN).md             # 3 execution workflows guide (English)
│
├── backend/                          # FastAPI backend application
│   ├── gemini-chat-server.py         # FastAPI main server (Uvicorn, Gemini SDK, Function Calling, Static routing)
│   ├── Dockerfile                    # Container build configuration (Python 3.11-slim + uv)
│   ├── .dockerignore                 # Docker build exclusions
│   ├── pyproject.toml                # uv package manager dependency manifest
│   ├── .python-version               # Python runtime version pin (3.11)
│   ├── .env                          # GEMINI_API_KEY environment variable file
│   ├── README.md                     # Backend setup and endpoint specifications
│   └── static/                       # Production frontend build distribution folder (optional serving)
│
└── frontend/                         # React + TypeScript + Vite web client
    ├── Dockerfile                    # Multi-stage container build (Node.js build -> Nginx serving)
    ├── .dockerignore                 # Docker build exclusions
    ├── nginx.conf                    # Nginx web server configuration (SPA routing & asset caching)
    ├── package.json                  # Frontend dependencies and npm build scripts
    ├── tsconfig.json                 # TypeScript base configuration
    ├── tsconfig.app.json             # Application TypeScript configuration
    ├── tsconfig.node.json            # Node/Vite TypeScript configuration
    ├── vite.config.ts                # Vite bundler & backend proxy configuration
    ├── index.html                    # Web application HTML entrypoint
    ├── src/
    │   ├── App.tsx                   # Main chat timeline component (state, API client, markdown renderer)
    │   ├── App.css                   # Gemini-inspired clean white theme and animations
    │   ├── main.tsx                  # React 18 DOM mount entrypoint
    │   ├── index.css                 # Global typography and CSS reset
    │   └── vite-env.d.ts             # Vite environment TypeScript declarations
    └── scripts/
        └── copy-to-backend.js        # Build script that automatically copies dist/ to backend/static/
```

---

## 3. Backend Architecture (`gemini-chat-server.py`)

### 3.1 Core Architecture Components

1. **Uvicorn (ASGI Web Server)**
   - Operates on an asynchronous event loop to handle concurrent client connections with high throughput.
   - Reads host environment variables (`HOST=0.0.0.0`, `PORT=8000`) for flexible deployment across bare-metal and container environments.

2. **FastAPI (Web Application Framework)**
   - **CORS Middleware**: Allows cross-origin requests from development servers (e.g. `http://localhost:5173`).
   - **Pydantic Validation**: Enforces strict request/response contracts via `ChatRequest`, `ChatResponse`, and `ResetRequest` schemas.
   - **Static Routing Handlers**: Serves frontend static assets (HTML, JS, CSS) with exact MIME types (`application/javascript`, `text/css`) through `@app.get("/")` and `@app.get("/{full_path:path}")` route handlers.

3. **Google GenAI SDK & Function Calling Engine**
   - **`client.chats.create`**: Maintains multi-turn conversation memory within an in-memory session pool (`sessions: dict[str, chats.Chat]`).
   - **Realtime Tool Functions**:
     - `get_weather_info(city)`: Calls Open-Meteo Geocoding and Weather Forecast APIs to fetch real-time temperature, humidity, wind speed, and meteorological condition.
     - `get_current_time(city)`: Resolves IANA timezone identifiers via geocoding and computes exact local time using Python's standard `ZoneInfo`.
   - **Automatic Tool Execution Loop**: When Gemini determines that external information is necessary to satisfy the prompt, the server executes the tool locally, feeds the result back to Gemini, and delivers the synthesized natural language response.

---

### 3.2 Backend System Architecture Diagram

```mermaid
graph TB
    subgraph "External Clients"
        User["User Web Browser (Port 3000)"]
    end

    subgraph "Reverse Proxy Layer"
        Traefik["Traefik v3.x Reverse Proxy\n(:3000 -> :80)"]
    end

    subgraph "Backend Container (FastAPI + Uvicorn :8000)"
        Uvicorn["Uvicorn ASGI Server"]
        FastAPIApp["FastAPI Application"]
        Router["API & Static Router\n(/chat, /reset, /health, /)"]
        SessionStore[("In-Memory Session Store\n(sessions: dict)")]
        ToolEngine["Function Calling Tools Engine"]
        WeatherTool["get_weather_info()"]
        TimeTool["get_current_time()"]
    end

    subgraph "External APIs & Cloud Services"
        GeminiAPI["Google Gemini 3.7 Flash API\n(google.genai SDK)"]
        OpenMeteoGeo["Open-Meteo Geocoding API"]
        OpenMeteoWeather["Open-Meteo Forecast API"]
    end

    User --> Traefik
    Traefik -- "/chat, /reset, /health, /docs" --> Uvicorn
    Uvicorn --> FastAPIApp
    FastAPIApp --> Router
    Router -- "Get / Create Session" --> SessionStore
    SessionStore -- "Chat Session" --> GeminiAPI
    GeminiAPI -- "Request Tool Execution" --> ToolEngine
    ToolEngine --> WeatherTool
    ToolEngine --> TimeTool
    WeatherTool --> OpenMeteoGeo
    WeatherTool --> OpenMeteoWeather
    ToolEngine -- "Return Tool Results" --> GeminiAPI
    GeminiAPI -- "Final Natural Language Response" --> FastAPIApp
    FastAPIApp --> Traefik
    Traefik --> User
```

---

### 3.3 Chat Request & Function Calling Sequence Diagram

```mermaid
sequenceDiagram
    autonumber
    actor User as User (Web Client)
    participant Traefik as Traefik (:3000)
    participant FastAPI as FastAPI (/chat)
    participant Session as Session Manager
    participant Gemini as Gemini 3.7 Flash
    participant Tool as Tool Engine (Weather/Time)
    participant OpenMeteo as Open-Meteo API

    User->>Traefik: POST /chat { message: "What is the weather in Paris and what time is it now?", session_id: "default" }
    Traefik->>FastAPI: Forward to Backend (:8000)
    FastAPI->>Session: get_or_create_chat("default")
    Session-->>FastAPI: Return Chat Session instance
    
    FastAPI->>Gemini: chat.send_message("What is the weather in Paris...")
    
    Note over Gemini: Analyzes prompt -> Determines weather & time tools are required
    Gemini-->>FastAPI: Tool Call Request (get_weather_info, get_current_time: city="Paris")
    
    FastAPI->>Tool: get_weather_info("Paris")
    Tool->>OpenMeteo: Geocoding & Weather Forecast API call
    OpenMeteo-->>Tool: Return 18°C, Clear Sky data
    Tool-->>FastAPI: Return weather data dictionary

    FastAPI->>Tool: get_current_time("Paris")
    Tool-->>FastAPI: Return local time via ZoneInfo("Europe/Paris")
    
    FastAPI->>Gemini: Send tool execution results (FunctionResponse)
    
    Note over Gemini: Synthesizes final response matching the query language
    Gemini-->>FastAPI: "The current weather in Paris is clear at 18°C, and the local time is 14:30."
    
    FastAPI-->>Traefik: 200 OK { response: "...", session_id: "default" }
    Traefik-->>User: Deliver JSON payload & render in timeline
```

---

## 4. Frontend Architecture (`frontend`)

### 4.1 Technology Stack & Structure

- **React 18 & TypeScript**: Component-driven UI architecture with complete compile-time type safety.
- **Vite Bundler**: Sub-second Hot Module Replacement (HMR) and optimized production rollup builds.
- **Nginx Web Server**: Serves production static files with gzip compression and client-side SPA routing fallback.
- **CSS Architecture (`App.css`)**:
  - Gemini.ai-inspired modern clean white theme.
  - Pulsing status indicators and typing animations.
  - Custom markdown parser (headings, bold, lists, backtick code blocks with one-click clipboard copy).
  - Smooth auto-scrolling to latest messages (`chatEndRef`).

---

### 4.2 Frontend State Management & Lifecycle Flow

```mermaid
graph TD
    subgraph "React App Component Lifecycle (App.tsx)"
        InitState["Initialize State\n- messages: []\n- input: ''\n- isLoading: false\n- serverStatus: 'checking'"]
        
        HealthCheck["useEffect (Server Health Check)\nGET /health -> online/offline"]
        
        UserInput["User Input\n- Text input (Enter / Shift+Enter)\n- Click sample question chips"]
        
        AddUserMsg["Append user message to timeline\nmessages.push({ sender: 'user', text })"]
        
        SendAPI["Async API Request\nPOST /chat { message, session_id }"]
        
        ShowLoading["Display Loading State\n(Gemini Sparkle + Pulsing dots)"]
        
        ReceiveRes["Receive Response (200 OK)\nmessages.push({ sender: 'ai', text, time })"]
        
        MarkdownRender["Render Custom Markdown\n- Code block styling\n- Copy button binding\n- List & paragraph formatting"]
        
        AutoScroll["chatEndRef.scrollIntoView({ behavior: 'smooth' })"]
    end

    InitState --> HealthCheck
    InitState --> UserInput
    UserInput --> AddUserMsg
    AddUserMsg --> ShowLoading
    AddUserMsg --> SendAPI
    SendAPI --> ReceiveRes
    ReceiveRes --> MarkdownRender
    MarkdownRender --> AutoScroll
```

---

### 4.3 UI Layout Component Hierarchy

```mermaid
classDiagram
    class AppContainer {
        +Header
        +TimelineContainer
        +InputDockArea
    }

    class Header {
        +Logo ("Gemini AI")
        +ServerStatusBadge ("online / offline")
        +ResetChatButton ("New Chat")
    }

    class TimelineContainer {
        +WelcomeHero (Sample question prompt chips)
        +MessageList (User & AI message timeline)
        +LoadingIndicator (Realtime response generator)
        +ScrollAnchor (Auto-scroll anchor point)
    }

    class MessageItem {
        +Avatar (User / Gemini Sparkle)
        +SenderLabel ("User" / "Gemini AI")
        +Timestamp (Generated time)
        +BubbleContent (Markdown rendered body)
        +CopyButton (One-click response copy)
    }

    class InputDockArea {
        +Textarea ("Ask a question... / Enter to send")
        +CharCounter (Character counter)
        +SendButton (Send icon button)
    }

    AppContainer *-- Header
    AppContainer *-- TimelineContainer
    AppContainer *-- InputDockArea
    TimelineContainer *-- MessageItem
```

---

## 5. Docker Compose & Routing Specification (`compose.yaml`)

```mermaid
flowchart LR
    Client(["🌐 Client Browser<br/>http://localhost:3000"])

    subgraph DockerHost["Docker Compose Environment (gemini-net)"]
        subgraph TraefikContainer["gemini-traefik (Traefik v3 Reverse Proxy)"]
            Port3000["External Port 3000<br/>(Entrypoint :80)"]
            Dashboard["Dashboard :8080"]
            RouterRule{"Traefik Dynamic Routing<br/>(PathPrefix Evaluation)"}
        end

        subgraph BackendContainer["gemini-backend (FastAPI Backend)"]
            BackendApp["FastAPI + Uvicorn :8000<br/>• /chat (AI Chat)<br/>• /reset (Session Reset)<br/>• /health (Health Check)<br/>• /docs (Swagger UI)"]
        end

        subgraph FrontendContainer["gemini-frontend (React Web Client)"]
            FrontendApp["React SPA Web Service :80<br/>• index.html (Timeline UI)<br/>• assets/* (JS/CSS Bundles)"]
        end
    end

    Client -->|"HTTP Request (Port 3000)"| Port3000
    Port3000 --> RouterRule

    RouterRule -->|"PathPrefix: /chat, /reset, /health, /docs<br/>(Priority 100)"| BackendApp
    RouterRule -->|"PathPrefix: /<br/>(Priority 1)"| FrontendApp
```

### 5.1 Ports & Network Summary

- **Host Entrypoint Port**: `3000` (Handled by Traefik and dynamically routed)
- **Traefik Monitoring Dashboard**: `http://localhost:8080`
- **Internal Bridge Network**: `gemini-net`
- **Environment Ingestion**: Automatically passes `GEMINI_API_KEY` from `backend/.env` to the backend container

---

## 6. Service Management Commands

```bash
# 1. Build and start containers in the background
docker compose up --build -d

# 2. Check running container status
docker compose ps

# 3. View live aggregate logs
docker compose logs -f

# 4. Stop and remove containers and network
docker compose down
```
