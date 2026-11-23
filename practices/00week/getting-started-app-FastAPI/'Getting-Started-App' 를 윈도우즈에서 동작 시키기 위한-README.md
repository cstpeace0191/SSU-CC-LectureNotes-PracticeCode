# Getting Started Todo App (FastAPI 버전)
윈도우즈 환경에서 동작 시키기 위해 **Python** 설치가 필요합니다.

---

## 1. Python 및 가상환경 설정 (Windows)

### 1) Python 설치 확인
명령 프롬프트(CMD) 또는 PowerShell에서 확인:
```powershell
python --version
# 또는
py --version
```

### 2) 가상환경 생성 및 활성화 (권장)
```powershell
python -m venv venv
.\venv\Scripts\activate
```

---

## 2. Backend (FastAPI + Uvicorn) 패키지 설치 및 실행

### 1) 필요한 패키지 설치
```powershell
pip install -r requirements.txt
```

### 2) Uvicorn 서버 실행
```powershell
uvicorn src.main:app --host 0.0.0.0 --port 3000 --reload
```
> 또는 직접 실행:
> ```powershell
> python src/main.py
> ```

---

## 3. 웹 브라우저에서 접속
- **Todo App 화면**: [http://localhost:3000/](http://localhost:3000/)
- **Swagger API 자동 문서**: [http://localhost:3000/docs](http://localhost:3000/docs)