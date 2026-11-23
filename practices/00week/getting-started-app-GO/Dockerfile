# syntax=docker/dockerfile:1

# 1단계: 빌드 환경
FROM golang:1.24-alpine AS builder

WORKDIR /app

# 의존성 정의 파일 복사 및 다운로드
COPY go.mod ./
COPY go.sum* ./
RUN go mod download || true

# 전체 소스 복사 및 정적 바이너리 컴파일 (CGO_ENABLED=0)
COPY . .
RUN go mod tidy
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o getting-started-app .

# 2단계: 실행 환경 (경량화 Alpine)
FROM alpine:latest

WORKDIR /app

# 빌드된 Go 바이너리 및 프론트엔드 정적 파일 복사
COPY --from=builder /app/getting-started-app .
COPY --from=builder /app/src/static ./src/static

EXPOSE 3000

CMD ["./getting-started-app"]