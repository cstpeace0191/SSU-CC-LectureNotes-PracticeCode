# Deployment의 spec 하위 모든 필드 계층 구조를 재귀적으로 조회
# (외부 spec 내부의 template, template.spec, containers 등 모든 중첩 필드 트리를 한눈에 확인할 때 사용)
```BASH
# 1. Deployment 리소스의 최상위 spec과 그 하위 모든 구조 확인 (재귀적)
$kubectl explain deployment.spec --recursive

# 2. template 필드 아래의 구조만 선택적으로 확인
$kubectl explain deployment.spec.template --recursive

# 3. template.spec 아래의 구조만 선택적으로 확인
$kubectl explain deployment.spec.template.spec --recursive

# 4. containers 배열 내부의 각 요소 필드 구조 확인
$kubectl explain deployment.spec.template.spec.containers --recursive
```

# 5. Deployment 기본 매니페스트 스캐폴딩 (YAML 템플릿 생성)
# 실제 클러스터에 배포하지 않고(--dry-run=client), Nginx 1.27 이미지를 사용하는 Deployment 기본 뼈대를 YAML로 추출하여 파일로 저장
```BASH
$kubectl create deployment web --image=nginx:1.27 --dry-run=client -o yaml > a.yaml

# --image=nginx:1.27 : 사용할 컨테이너 이미지 및 버전 태그 지정
# --dry-run=client   : API 서버에 전송하지 않고 로컬(클라이언트)에서만 객체 생성 시뮬레이션
# -o yaml > a.yaml   : 결과를 YAML 형식으로 출력하여 a.yaml 파일로 저장
```

# 6. 서버 측 Dry-run 검증 및 클러스터 실시간 Diff 점검

### [1] 서버 측 Dry-run 검증
```BASH
$kubectl apply -f a.yaml --dry-run=server
```
- **실행 결과 메시지의 의미**:
  - `deployment.apps/web configured (server dry run)`: 클러스터에 이미 `web` 리소스가 존재하며, 매니페스트 내용으로 정상 업데이트(수정) 가능함을 의미합니다. *(처음 생성 시에는 `created (server dry run)`으로 출력)*
  - `(server dry run)`: **실제 etcd 및 클러스터 상태에는 아무런 변경도 반영되지 않았음**을 뜻합니다. (동작 중인 Pod에 전혀 영향을 주지 않음)
- **기대할 수 있는 결과 (성공 vs 실패)**:
  - **성공 시 (정상 통과)**: 에러 없이 정상 종료 코드(`0`) 반환. 실제 배포 시 스키마, RBAC 권한, 클러스터 정책상 아무런 문제가 발생하지 않음을 보장.
  - **실패 시 (오류 사전 차단)**: 오타/스키마 오류, 변경 불가 필드(Immutable Field) 위반, RBAC 권한 부족, 어드미션 정책 위반 등을 실제 배포 전에 안전하게 감지.

#### 💡 `--dry-run=client` vs `--dry-run=server` 비교
| 비교 항목 | `client` (`--dry-run=client`) | `server` (`--dry-run=server`) |
| :--- | :--- | :--- |
| **실행 주체** | 로컬 PC의 `kubectl` CLI 도구 | 실제 **쿠버네티스 API 서버** |
| **API 서버 통신** | ❌ 통신하지 않음 (오프라인 실행 가능) | ✅ API 서버로 요청 전송 |
| **검증 범위** | 기본적인 YAML 문법 및 스키마 형식 체크 | **RBAC 권한, 스키마, 어드미션 정책, 기본값 병합까지 전체 검증** |
| **주요 목적** | 기본 YAML 템플릿 추출 및 스캐폴딩 (`-o yaml`) | **실제 배포(apply) 직전 완벽한 사전 안전 점검(Pre-flight Check)** |

---

### [2] 클러스터 라이브(Live) 상태와 로컬 매니페스트 간의 차이점(Diff) 비교
```BASH
$kubectl diff -f a.yaml
```
- **동작 원리**: 로컬 매니페스트 파일(`a.yaml`)과 현재 클러스터에서 실제로 실행 중인 실시간(Live) 리소스 상태를 비교하여, 추가(`+`), 수정, 삭제(`-`)될 내용을 `git diff` 스타일(Unified diff)로 출력합니다.
- **종료 코드 (Exit Code)**:
  - 변경 사항(Diff)이 **없을 때**: `0`
  - 변경 사항이 **있을 때**: `1`
  - 오류 발생 시: `> 1`
- **활용**: 실제 `apply` 전 변경 영향도를 사전에 검토하거나, CI/CD 파이프라인에서 Git 소스와 클러스터 간의 구성 불일치(Configuration Drift)를 자동 감지하는 용도로 활용됩니다.

---

# 7. Deployment 배포 이력 관리 및 롤백 (Rollout Undo)

### 💡 Rollout(롤아웃)과 Rollback(롤백)이란?

| 구분 | 개념 및 정의 | 쿠버네티스에서의 동작 방식 | 대표 명령어 |
| :--- | :--- | :--- | :--- |
| **Rollout (롤아웃)** | 새로운 버전(컨테이너 이미지, 환경변수, 리소스 설정 등)을 클러스터에 **점진적으로 배포/교체해 나가는 전체 과정** | 새로운 버전의 ReplicaSet을 생성하여 새 Pod을 순차적으로 띄우고 구버전 Pod을 점진적으로 줄여 **무중단 배포(Rolling Update)**를 수행 | `kubectl rollout status`<br>`kubectl rollout history`<br>`kubectl rollout restart` |
| **Rollback (롤백)** | 신규 버전 배포 후 버그/장애 발생 시, **정상 동작하던 이전 버전(Revision)으로 시스템을 되돌리는 복구 작업** | 과거 배포 당시 보존되어 있던 이전 ReplicaSet의 크기를 다시 늘려 구버전 Pod을 즉시 복원하고 문제 버전 Pod을 종료 | **`kubectl rollout undo`**<br>`kubectl rollout undo --to-revision=N` |

> **핵심 요약**:
> - 쿠버네티스에는 별도의 `kubectl rollback`이라는 독립 명령어가 존재하지 않으며, **`kubectl rollout undo`** 명령어가 롤백(이전 버전 복구) 기능을 수행합니다.
> - Deployment는 배포할 때마다 변경 이력을 **리비전(Revision)** 단위로 기록하므로, 원하는 과거 시점으로 안전하게 되돌릴 수 있습니다.

---

### [1] 배포 상태 확인 및 롤백 명령어
```BASH
# 1) 현재 배포(롤아웃) 진행 상태 모니터링
$kubectl rollout status deployment/web

# 2) 과거 배포 이력(Revision) 목록 조회
$kubectl rollout history deployment/web

# 3) 직전 버전(이전 Revision)으로 즉시 롤백
$kubectl rollout undo deployment/web

# 4) 특정 리비전 번호(예: revision 1)를 지정하여 롤백
$kubectl rollout undo deployment/web --to-revision=1
```

