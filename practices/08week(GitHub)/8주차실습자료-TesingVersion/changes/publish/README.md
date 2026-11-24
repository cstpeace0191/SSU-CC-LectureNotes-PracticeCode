# publish

**적용 단계**: [실습 4] ③ 이미지 게시 워크플로 (`scripts/lab4_actions_security.sh`)  
**연관 주제**: GitHub Container Registry (GHCR) 게시 및 출처 증명 (Attestation)

---

## 폴더 개요
소프트웨어 공급망 보안을 고려하여, 빌드된 컨테이너 이미지를 **GitHub Container Registry(GHCR)**에 안전하게 배포하고 암호학적 출처 증명(Artifact Attestation)을 첨부하는 워크플로 파일입니다.

---

## 포함된 파일 및 역할

| 파일 경로 | 설명 |
| :--- | :--- |
| **`.github/workflows/publish.yml`** | GitHub Actions 이미지 배포 워크플로:<br>1. **트리거**: `main` 브랜치로의 푸시 또는 버전 태그(`v*.*.*`) 푸시 시 실행<br>2. **이미지 빌드 및 푸시**: `ghcr.io/<사용자>/todo-lab:<태그>` 형태로 컨테이너 이미지를 빌드하여 GHCR에 자동 게시<br>3. **출처 증명(Attestation)**: `actions/attest-build-provenance` 액션을 사용하여 이미지가 변조되지 않았음을 보증하는 암호학적 빌드 증명서 생성<br>4. **검증 지원**: `gh attestation verify` 명령어로 배포된 이미지의 무결성을 검증 가능 |

