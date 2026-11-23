###################################################
# Stage: client-base
#
# This stage is used as the base for the client-dev and client-build stages.
###################################################
FROM node:22-alpine AS client-base
WORKDIR /app/client

COPY client/package.json client/package-lock.json ./
RUN npm ci --ignore-scripts

# TSX 전환 후: vite.config.ts + tsconfig*.json 이 필요 (vite.config.js 는 없음)
COPY client/index.html client/vite.config.ts client/copy-build.js client/tsconfig*.json ./
COPY client/public ./public
COPY client/src ./src

###################################################
# Stage: client-dev
# 
# This stage is used for development of the client application.
###################################################
FROM client-base AS client-dev
EXPOSE 5173
CMD ["npm", "run", "dev"]

###################################################
# Stage: client-build
#
# This stage builds the client application, producing static HTML, CSS, and
# JS files in the dist directory.
###################################################
FROM client-base AS client-build
RUN npm run build


###################################################
################  BACKEND STAGES  #################
###################################################

###################################################
# Stage: backend-base
#
# This stage installs Python dependencies for development and testing.
###################################################
FROM python:3.12-slim AS backend-base
WORKDIR /app/backend

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Install system dependencies if required (curl for healthchecks and utility)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

###################################################
# Stage: backend-dev
#
# This stage is used for development of the backend FastAPI application.
###################################################
FROM backend-base AS backend-dev
COPY backend/pytest.ini ./
COPY backend/main.py ./
COPY backend/src ./src
COPY backend/spec ./spec

EXPOSE 3000
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "3000", "--reload"]

###################################################
# Stage: test
#
# This stage runs the pytest suite on the backend.
# The final stage depends on this stage to guarantee tests pass before image creation.
###################################################
FROM backend-dev AS test
RUN pytest

###################################################
# Stage: final
#
# This stage is the final production image. It copies the FastAPI backend
# and the built React static assets from client-build into src/static.
###################################################
FROM python:3.12-slim AS final
WORKDIR /app/backend

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PORT=3000
ENV HOST=0.0.0.0

# Install system dependencies if required (curl for container healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements from test stage to ensure test stage is executed
COPY --from=test /app/backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source code and entrypoint
COPY backend/main.py ./
COPY backend/src ./src

# Copy built React frontend assets into static folder for FastAPI root serving
COPY --from=client-build /app/client/dist ./src/static

# 비루트 사용자로 실행 (Kubernetes runAsNonRoot 대응)
RUN useradd --uid 10001 --create-home app \
    && mkdir -p /etc/todos && chown app:app /etc/todos
USER 10001

EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=3s CMD curl -fsS http://localhost:3000/api/greeting || exit 1
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "3000"]
