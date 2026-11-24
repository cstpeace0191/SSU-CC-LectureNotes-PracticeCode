# pr6-bob

**적용 단계**: [실습 3] ② 동료(Bob) 역할 시뮬레이션 (`scripts/lab3_feature_conflict.sh`)  
**연관 PR**: PR #6 (동료 머지 시뮬레이션)

---

## 폴더 개요
협업 개발 환경에서 **동일한 소스 코드를 서로 다른 개발자가 동시에 수정했을 때 발생하는 충돌(Merge Conflict)을 실습**하기 위해 준비된 파일입니다.

---

## 변경 내용 및 충돌 발생 원리

| 파일 경로 | 변경 내용 |
| :--- | :--- |
| **`backend/src/routes/items.py`** | `get_items()` 함수를 "미완료 항목이 먼저 오도록 정렬"하여 반환하도록 수정:<br>`return sorted(items, key=lambda item: item["completed"])` |

### 💥 충돌 시나리오
1. **동료 Bob**(`bob/` 폴더)이 이 파일을 수정하여 PR을 올리고 `main` 브랜치에 먼저 머지합니다.
2. **Alice**(`todo-lab/` 폴더)는 동일한 `items.py`의 `get_items()` 함수에 필터링 기능(`pr3-filter`)을 작업하고 있었습니다.
3. Alice가 `git rebase origin/main`을 실행하면, 동일한 함수의 반환부에서 충돌이 발생합니다.
4. 이 충돌을 수동으로 해결하여 필터링과 정렬 두 기능을 모두 살리도록 코드를 병합하는 것이 실습 3의 핵심 과제입니다. (해결 정답: `answers/items.py`)

