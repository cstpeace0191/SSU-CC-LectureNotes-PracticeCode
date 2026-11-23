# Docker Getting Started App (FastAPI) — 실행방법 

### ① 사전 준비 — Python 및 VSCode 설치
윈도우즈/리눅스 환경에서 동작 시키기 위해 Python 및 VSCode(또는 선호하는 IDE) 설치
* **Python**: [Python-Download](https://www.python.org/downloads/) 에서 Python 3.9 이상 버전 설치 (설치 시 `Add Python to PATH` 체크)
* **VSCode**: [VSCode-Download](https://code.visualstudio.com/download) 에서 설치

---

### ② 가상환경 생성 및 활성화 (권장)

#### Windows (PowerShell):
```powershell
python -m venv venv
.\venv\Scripts\activate
```

#### Linux / macOS:
```bash
python3 -m venv venv
source venv/bin/activate
```

---

### ③ 패키지 설치 및 웹응용 실행

#### 1) 필요한 라이브러리 설치
```bash
pip install -r requirements.txt
```

#### 2) Uvicorn으로 FastAPI 서버 실행
```bash
uvicorn src.main:app --host 0.0.0.0 --port 3000 --reload
```
> **참고**:
> - `--reload`: 소스 코드가 수정될 때 서버가 자동으로 재시작되는 옵션입니다.
> - 또는 `python src/main.py` 로 직접 실행할 수도 있습니다.

---

### ④ 브라우저에서 접속
* **Todo 웹 앱 화면**: [http://localhost:3000](http://localhost:3000)
* **Swagger 대화형 API 문서**: [http://localhost:3000/docs](http://localhost:3000/docs)
* **ReDoc API 문서**: [http://localhost:3000/redoc](http://localhost:3000/redoc)

---

### ⑤ 할일 관리 사용
1. 입력창에 할일 텍스트 입력 → **Add Item** 버튼 클릭하여 추가 (`POST /items`)
2. 항목 왼쪽 **체크박스** 클릭 → 완료/미완료 토글 (`PUT /items/{id}`)
3. 항목 오른쪽 **휴지통 아이콘** 클릭 → 삭제 (`DELETE /items/{id}`)

---

### ⑥ 테스트 실행 (선택 사항)
```bash
pytest
```
