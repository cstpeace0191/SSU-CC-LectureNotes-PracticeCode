## 무엇이 문제인가요?
`docker build --target final .` (또는 `docker compose -f compose-prod-build.yml up --build`) 가 실패합니다.

## 재현 절차
1. 저장소를 새로 clone
2. `docker build --target final -t todo-app:ci .`

## 실제 출력
```
#11 [backend-dev 1/5] COPY backend/requirements-dev.txt ./
#11 ERROR: ... "/backend/requirements-dev.txt": not found
```

## 기대 동작
새로 clone 한 저장소에서도 이미지가 빌드된다. (작성자 PC 에는 커밋되지 않은 requirements-dev.txt 가 있어 성공했던 것)

## 제안
- `backend/requirements-dev.txt` 를 커밋하고 `requirements.txt` 는 운영 의존성만 남기기
- 운영 이미지는 비루트(USER 10001)로 실행하고 HEALTHCHECK 추가
