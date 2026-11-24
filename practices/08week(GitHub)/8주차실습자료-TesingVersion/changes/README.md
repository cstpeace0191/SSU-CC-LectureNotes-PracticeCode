# changes 디렉터리 가이드

`changes/` 디렉터리는 8주차 실습(Git · GitHub · PR · GitHub Actions)을 단계별로 수행하기 위해 미리 준비된 **PR 단위의 변경사항 파일 모음**입니다.

각 실습 단계에서 브랜치를 생성한 후, 해당 서브폴더의 파일들을 작업 디렉터리로 복사(`cp -r`)하여 커밋 및 PR을 작성할 수 있도록 구성되어 있습니다.

---

## 서브폴더 목록 및 요약

| 서브폴더 | 적용 실습 | 연관 Issue / PR | 주요 변경 내용 |
| :--- | :---: | :---: | :--- |
| [**`pr1-ci-setup/`**](file:///d:/Lecture%20Notes/2026-2CloudComputing/2026-2CloudComputing_LectureNotes/8thLecture/8주차실습자료/changes/pr1-ci-setup/README.md) | 실습 2 ① | Issue #1 (첫 커밋) | GitHub Actions CI 워크플로(`ci.yml`), 협업 템플릿(Issue Form, PR 템플릿, CODEOWNERS, Dependabot), 린트/테스트 설정 |
| [**`pr1-ruff-fix/`**](file:///d:/Lecture%20Notes/2026-2CloudComputing/2026-2CloudComputing_LectureNotes/8thLecture/8주차실습자료/changes/pr1-ruff-fix/README.md) | 실습 2 ① | Issue #1 (두 번째 커밋) | 백엔드 코드의 Ruff 린트 에러 6건 수정, 커버리지 제외 설정(`mysql.py`) |
| [**`pr2-docker-fix/`**](file:///d:/Lecture%20Notes/2026-2CloudComputing/2026-2CloudComputing_LectureNotes/8thLecture/8주차실습자료/changes/pr2-docker-fix/README.md) | 실습 2 ④ | Issue #2 / PR #5 | 누락되었던 `requirements-dev.txt` 추가, 운영 의존성 분리, Dockerfile 비루트(USER 10001) 실행 및 HEALTHCHECK 적용 |
| [**`pr3-filter/`**](file:///d:/Lecture%20Notes/2026-2CloudComputing/2026-2CloudComputing_LectureNotes/8thLecture/8주차실습자료/changes/pr3-filter/README.md) | 실습 3 ① | Issue #3 / PR #7 | 할 일 완료 여부 필터링(`GET /api/items?completed=true\|false`) API 구현 및 단위 테스트 4개 추가 |
| [**`pr6-bob/`**](file:///d:/Lecture%20Notes/2026-2CloudComputing/2026-2CloudComputing_LectureNotes/8thLecture/8주차실습자료/changes/pr6-bob/README.md) | 실습 3 ② | 동료 Bob 역할 | `get_items()` 함수를 "미완료 먼저 정렬"하도록 수정하여 선행 머지 $\rightarrow$ `pr3-filter`와 의도적 충돌(Merge Conflict) 유발 |
| [**`publish/`**](file:///d:/Lecture%20Notes/2026-2CloudComputing/2026-2CloudComputing_LectureNotes/8thLecture/8주차실습자료/changes/publish/README.md) | 실습 4 ③ | GHCR 이미지 게시 | `main` 브랜치 푸시 및 버전 태그(`v*.*.*`) 발생 시 GitHub Container Registry(GHCR)에 컨테이너 이미지를 자동 빌드/게시하고 출처 증명(Attestation) 생성 |

---

## 활용 방법 예시

실습 스크립트(`scripts/lab*.sh`)에서 다음과 같이 해당 폴더의 파일들을 작업 디렉터리로 복사하여 적용합니다:

```bash
# 예: 실습 2에서 Issue #1 CI 설정 반영 시
cp -r "$LAB/changes/pr1-ci-setup/." .
git add -A
git commit -m "ci: add GitHub Actions CI, issue/PR templates, CODEOWNERS (#1)"
```

