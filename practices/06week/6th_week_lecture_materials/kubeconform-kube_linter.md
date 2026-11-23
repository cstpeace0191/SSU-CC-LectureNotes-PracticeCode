# Kubernetes 매니페스트 검증 도구 가이드: Kubeconform & Kube-linter

쿠버네티스(Kubernetes) 환경에서 YAML 매니페스트를 작성하고 배포할 때, 배포 전 단계(Pre-deployment / CI/CD)에서 오류와 보안 취약점을 사전에 차단하기 위해 사용하는 대표적인 두 도구의 사용법과 비교 가이드입니다.

---

## 1. Kubeconform vs Kube-linter 핵심 비교

| 구분 | Kubeconform | Kube-linter |
| :--- | :--- | :--- |
| **주요 역할** | **스키마 유효성 검증 (Schema Validation)** | **보안 및 모범 사례 검사 (Linting & Best Practices)** |
| **주요 질문** | "문법이 올바르고 K8s 공식 API 스키마 규격에 부합하는가?" | "루트 권한 차단, 리소스 제한 등 안전하게 작성되었는가?" |
| **비유** | 컴파일 에러 / 타입 체커 (TypeScript, Compiler) | 정적 분석 / 린터 (ESLint, SonarQube) |
| **개발 주체** | 오픈소스 (kubeval 후속/대안) | Red Hat (StackRox 팀) |
| **검사 대상** | Kubernetes YAML/JSON 매니페스트 | Kubernetes YAML 매니페스트, Helm 차트 |

---

## 2. Kubeconform (스키마 유효성 검증 도구)

Kubeconform은 쿠버네티스 리소스 명세가 공식 OpenAPI/JSONSchema 규격에 부합하는지 고속으로 검증해 주는 오픈소스 도구입니다.

### 2.1 설치 방법

#### Windows
```powershell
# Scoop 사용 시
scoop install kubeconform

# Chocolatey 사용 시
choco install kubeconform
```
*또는 [Kubeconform GitHub Releases](https://github.com/yannh/kubeconform/releases)에서 Windows용 바이너리(`kubeconform-windows-amd64.zip`)를 다운로드하여 PATH에 등록합니다.*

#### macOS / Linux / Docker
```bash
# macOS (Homebrew)
brew install kubeconform

# Go CLI
go install github.com/yannh/kubeconform/cmd/kubeconform@latest

# Docker 사용 시
docker run --rm -v ${PWD}:/manifests ghcr.io/yannh/kubeconform:latest /manifests
```

### 2.2 기본 및 실전 사용법

#### 1) 단일 파일 검증
```powershell
kubeconform kind-deployment-only-Local.yaml
```

#### 2) 디렉토리 내 전체 파일 검증
```powershell
kubeconform .
```

#### 3) 실무 추천 옵션 조합 (엄격한 검사 + 요약 출력 + 특정 K8s 버전)
```powershell
kubeconform -strict -summary -kubernetes-version 1.30.0 kind-deployment-only-Local.yaml
```

#### 4) Helm / Kustomize 파이프라인 검증 (stdin 파이프)
```powershell
# Kustomize 빌드 결과 검증
kubectl kustomize ./overlays/prod | kubeconform -summary

# Helm 템플릿 렌더링 결과 검증
helm template my-release ./charts/my-chart | kubeconform -summary
```

#### 5) CRD(Custom Resource Definition) 검증 (외부 스키마 카탈로그 연동)
```powershell
kubeconform -strict -summary \
  -schema-location default \
  -schema-location 'https://raw.githubusercontent.com/datreeio/CRDs-catalog/main/{{.ResourceKind}}_{{.ResourceAPIVersion}}.json' \
  .
```

### 2.3 주요 옵션 요약
- `-strict`: 스키마에 정의되지 않은 잘못된 필드(오타 등)를 에러로 처리 (**강력 권장**)
- `-summary`: 성공, 실패, 스킵된 리소스 수 요약 출력
- `-kubernetes-version <버전>`: 특정 쿠버네티스 버전의 스키마 기준으로 검증 (예: `1.30.0`)
- `-output <format>`: 출력 형식 지정 (`text`, `json`, `tap`)
- `-ignore-missing-schemas`: 스키마를 찾을 수 없는 리소스를 에러 대신 건너뜀

---

## 3. Kube-linter (보안 및 모범 사례 린팅 도구)

Kube-linter는 쿠버네티스 매니페스트와 Helm 차트가 보안 취약점을 포함하고 있거나 프로덕션 권장 모범 사례를 위반했는지 사전에 분석하는 도구입니다.

### 3.1 주요 검출 항목
- **보안 (Security)**:
  - 컨테이너의 root 권한 실행 여부 (`run-as-non-root`)
  - 호스트 특권 모드 실행 여부 (`privileged-container`)
  - 읽기 전용 루트 파일시스템 미적용 (`read-only-root-filesystem`)
  - 민감한 호스트 볼륨 마운트 여부 (`host-mounts`)
- **신뢰성 및 운영 (Reliability & Operations)**:
  - CPU/메모리 요청(Request) 및 제한(Limit) 누락 (`unset-cpu-requirements`, `unset-memory-requirements`)
  - `latest` 이미지 태그 사용 여부 (`latest-tag`)
  - 헬스체크 프로브 누락 (`no-readiness-probe`, `no-liveness-probe`)

### 3.2 설치 방법

#### Windows
```powershell
# Chocolatey 사용 시
choco install kube-linter

# Scoop 사용 시
scoop install kube-linter
```
*또는 [Kube-linter GitHub Releases](https://github.com/stackrox/kube-linter/releases)에서 Windows용 바이너리를 다운로드하여 PATH에 등록합니다.*

#### macOS / Linux / Docker
```bash
# macOS (Homebrew)
brew install kube-linter

# Go CLI
go install golang.stackrox.io/kube-linter/cmd/kube-linter@latest

# Docker 사용 시
docker run --rm -v ${PWD}:/workspace -w /workspace stackrox/kube-linter:latest lint .
```

### 3.3 기본 및 실전 사용법

#### 1) 단일 파일 검사
```powershell
kube-linter lint kind-deployment-only-Local.yaml
```

#### 2) 디렉토리 전체 검사
```powershell
kube-linter lint .
```

#### 3) Helm 차트 검사
```powershell
kube-linter lint ./helm-chart-directory/
```

#### 4) CI/CD 연동용 포맷 출력
```powershell
kube-linter lint . --format json
kube-linter lint . --format sarif
```

### 3.4 설정 파일(`.kube-linter.yaml`)을 통한 규칙 커스터마이징
실습 환경이나 개발 환경에서 지나치게 엄격한 규칙(예: 필수 리소스 제한)을 제외할 때 프로젝트 루트에 설정 파일을 생성합니다.

```yaml
# .kube-linter.yaml
customChecks: []
checks:
  # 기본 내장 룰 전체 활성화
  addAllBuiltIn: true
  
  # 제외할 룰 목록
  exclude:
    - "unset-cpu-requirements"       # CPU request/limit 미지정 허용
    - "unset-memory-requirements"    # Memory request/limit 미지정 허용
    - "no-readiness-probe"           # readinessProbe 생략 허용
```

설정 파일을 적용하여 실행:
```powershell
kube-linter lint --config .kube-linter.yaml .
```

### 3.5 매니페스트 내 어노테이션(Annotation)으로 개별 리소스 룰 예외 처리
특정 리소스에만 검사를 건너뛰게 하려면 YAML의 `metadata.annotations`에 아래와 같이 추가합니다.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: todo-app
  annotations:
    ignore-check.kube-linter.io/unset-cpu-requirements: "실습 환경이므로 리소스 제한 생략"
spec:
  # ...
```

---

## 4. CI/CD 파이프라인 연계 베스트 프랙티스

실제 프로덕션 배포 파이프라인(GitHub Actions, GitLab CI 등)에서는 두 도구를 단계별로 연결하여 사용하는 것이 표준입니다.

```mermaid
flowchart LR
    A[K8s YAML 매니페스트 / Helm] --> B[1단계: Kubeconform]
    B -- 스키마 규격 통과 --> C[2단계: Kube-linter]
    B -- 스키마 오류/오타 --> F[배포 차단 (Fix Syntax)]
    C -- 보안/모범사례 통과 --> D[클러스터 배포 (ArgoCD / Kubectl)]
    C -- 보안 위반/누락 --> E[배포 차단 (Fix Security/Policy)]
```

1. **1단계 (Kubeconform)**: 문법 오타, 잘못된 API 필드, 지원되지 않는 K8s 버전 규격을 빠르게 걸러냅니다.
2. **2단계 (Kube-linter)**: 보안 정책(Root 실행 방지), 리소스 Limit/Request, 프로브 설정 등 운영 모범 사례를 검증합니다.
