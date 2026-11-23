FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py migrate.py ./
COPY migrations ./migrations

# 비루트 사용자로 실행 (차트의 securityContext.runAsNonRoot 와 짝을 이룸)
RUN useradd -u 10001 -m appuser
USER 10001

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
