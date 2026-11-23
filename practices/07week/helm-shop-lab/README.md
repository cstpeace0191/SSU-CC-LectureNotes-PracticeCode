# helm-shop-lab — Helm 기반 Kubernetes 응용 개발 실습

> **실습 원문 출처 (Source)**: [https://github.com/cstpeace0191/helm-shop-lab](https://github.com/cstpeace0191/helm-shop-lab)

## 1. 응용 프로그램 개요 (What is helm-shop-lab?)

**`helm-shop-lab`**은 Kubernetes 환경에서 클라우드 네이티브 애플리케이션의 패키징, 배포, 롤백, DB 스키마 마이그레이션(Helm Hook), CI/CD 및 GitOps 파이프라인 전체 라이프사이클을 실습하기 위해 제작된 **온라인 굿즈 쇼핑몰 백엔드 REST API 서비스**입니다.

### 아키텍처 및 구성 요소
* **API 서버 (`shop-api`)**: Python 3.12와 **FastAPI** 기반의 RESTful 웹 서비스 (상품 조회/등록, 상태 확인)
* **데이터베이스 (`shop-db`)**: 상품 데이터와 마이그레이션 이력을 영속 저장하는 **PostgreSQL**
* **마이그레이션 러너 (`migrate.py`)**: 애플리케이션 파드가 배포되기 전 DB 스키마를 순차적으로 최신화하는 경량 SQL 마이그레이터 (Helm `pre-install` / `pre-upgrade` Hook Job)

### 주요 API 엔드포인트
| 메서드 | 엔드포인트 | 설명 | 실습 목적 |
|---|---|---|---|
| `GET` | `/items` | 등록된 상품 목록 조회 (예: 쿠버네티스 머그컵, 스티커 등) | DB 연결 및 데이터 조회 검증 (`helm test`) |
| `POST` | `/items` | 신규 상품 추가 (`{"name": "...", "price": ...}`) | 데이터베이스 트랜잭션 및 쓰기 기능 검증 |
| `GET` | `/version` | 현재 배포된 앱 버전(`APP_VERSION`) 및 인사말 반환 | 롤링 업데이트 및 `helm rollback` 결과 확인 |
| `GET` | `/healthz` | DB 연결 상태 확인 (Health Check) | Kubernetes Liveness / Readiness 프로브 |

### Helm 실습 관점의 핵심 설계
1. **2-Tier 아키텍처 모듈화**: 비즈니스 로직 계층(`charts/shop-api`)과 데이터 계층(`charts/shop-db`)을 독립된 Helm 차트로 분리하여 관리
2. **안전한 DB 마이그레이션 (Helm Hook)**: 새 코드 배포 전 `migration-job` Hook을 통해 스키마를 먼저 업그레이드하여 버전 불일치 방지
3. **선언적 환경 분리 (Dev vs Prod)**: 하나의 차트 템플릿으로 `values-dev.yaml`(단일 복제본, 경량)과 `values-prod.yaml`(다중 복제본, HPA, PDB, Ingress)을 분기 적용

---

## 2. 프로젝트 수행 개요 및 전체 흐름

이 프로젝트는 **Kubernetes 로컬 개발부터 GitOps 기반 운영 배포까지 이어지는 클라우드 네이티브 개발 파이프라인의 전체 라이프사이클**을 4단계(Lab 1 ~ Lab 4)로 나누어 직접 실습합니다.

```
[개발 단계]                                [CI 단계]                            [CD / GitOps 단계]
로컬 코드 수정                              GitHub Actions                       Argo CD (GitOps)
(main.py, SQL)                            자동 Lint & Build                    클러스터 상태 감지
     │                                           │                                       │
     ├──▶ ./make.sh build (도커 빌드)              ├──▶ GHCR 이미지/차트 푸시               ├──▶ PreSync: 마이그레이션 Job 실행
     ├──▶ ./make.sh deploy-dev (로컬 Helm 배포)    └──▶ values-prod.yaml 태그 커밋 ────────▶└──▶ 롤링 업데이트 (무중단 운영 배포)
     └──▶ /docs, /items 로컬 검증
```

### 단계별 핵심 학습 목표
| Lab | 사례 | 핵심 질문 | 수행 내용 및 결과물 |
|---|---|---|---|
| **Lab 0** | **환경 준비** | 로컬 쿠버네티스 환경을 어떻게 구성하는가? | kind 클러스터 + metrics-server + Argo CD 설치, 계정명 치환 |
| **Lab 1** | **자체 차트 배포** | 단일 템플릿으로 dev/prod 환경을 어떻게 나누는가? | `charts/shop-api`, `values-*.yaml`, 롤링 배포 및 `helm rollback` |
| **Lab 2** | **Helm Hook 마이그레이션** | 파드 교체 전 DB 스키마를 어떻게 안전하게 변경하는가? | `pre-install/pre-upgrade` Hook Job, 실패 시 구버전 파드 보호 |
| **Lab 3** | **GitHub Actions CI** | 컨테이너 이미지와 Helm 차트를 어떻게 자동 게시하는가? | `.github/workflows/ci.yaml`, GHCR OCI 차트 레지스트리 게시 |
| **Lab 4** | **Argo CD GitOps** | 수동 배포 명령 없이 Git 커밋만으로 어떻게 배포하는가? | `argocd/shop-prod.yaml`, 선언적 배포, Self-heal, Git 기반 롤백 |

---

## 3. 저장소 구조 및 파일 역할

```
helm-shop-lab/
├── app/                      # FastAPI 애플리케이션 소스 코드
│   ├── main.py               # REST API 엔드포인트 (/items, /version, /healthz, /docs)
│   ├── migrate.py            # DB 스키마 마이그레이션 실행기 (Hook Job에서 실행)
│   ├── Dockerfile            # shop-api 컨테이너 빌드 정의
│   └── migrations/           # 순차 적용될 SQL 파일들 (001_*.sql, 002_*.sql.example)
├── charts/
│   ├── shop-api/             # 실습 대상 메인 애플리케이션 차트
│   │   ├── values.yaml       # 공통 기본 설정값 (이미지, DB 연결 정보, 훅 설정 등)
│   │   ├── values-dev.yaml   # 개발 환경 오버라이드 (1개 복제본, 로컬 kind 환경용)
│   │   ├── values-prod.yaml  # 운영 환경 오버라이드 (HPA 자동확장, Ingress, PDB 활성화)
│   │   ├── values.schema.json# Helm 입력값 유효성 검증 스키마
│   │   └── templates/        # Kubernetes 매니페스트 템플릿 (Deployment, Service, Hook Job 등)
│   └── shop-db/              # 개발/실습용 PostgreSQL 차트 (Secret 생성 및 DB 기동)
├── .github/workflows/
│   ├── ci.yaml               # PR 및 main 브랜치 푸시 시 자동 실행되는 CI 파이프라인
│   └── deploy-helm-push.yaml # (참고용) 전통적인 Push 방식 Helm 배포 워크플로우
├── argocd/
│   └── shop-prod.yaml        # 운영 환경 배포를 위한 Argo CD Application 매니페스트
├── scripts/
│   └── kind-setup.sh         # kind 클러스터, metrics-server, Argo CD 원클릭 설치 스크립트
├── make.sh                   # Windows Git Bash 및 Make 미설치 환경을 위한 단축 실행 스크립트
└── Makefile                  # 전체 실습 단축 명령어 정의
```

---

## 4. 실습 단계별 상세 수행 가이드

### Lab 0. 사전 준비 (Prerequisites)

필요 도구: Docker, [kind](https://kind.sigs.k8s.io/), kubectl, Helm 3.x/4.x, bash (또는 make)

#### 0-1. 본인 GitHub 계정으로 설정 치환 (필수)
실습을 진행하기 전, 템플릿 기본 계정(`cstpeace0191`)을 **본인의 GitHub 계정명**(예: `cstpeace0191`)으로 일괄 치환합니다:
```bash
grep -rl cstpeace0191 . | xargs sed -i 's/cstpeace0191/<내_깃허브_계정>/g'
```
*주요 변경 파일: `Makefile`, `charts/shop-api/values.yaml`, `charts/shop-api/Chart.yaml`, `argocd/shop-prod.yaml`*

#### 0-2. 실행 도구 선택 (`./make.sh` vs `make`)
* **Windows (Git Bash 환경)**: `make`가 기본 설치되어 있지 않으므로 제공된 **`./make.sh <타깃>`** 스크립트를 사용합니다. (권장)
* **Linux / macOS / Make 설치 환경**: `make <타깃>` 명령을 직접 사용할 수 있습니다.

> [!TIP]
> **Windows에서 `make` 명령어를 직접 사용하고 싶은 경우**
> PowerShell(관리자 권한)에서 패키지 관리자로 설치 후 새 Git Bash 창을 열면 됩니다:
> * Winget: `winget install ezwinports.make`
> * Chocolatey: `choco install make`
> * Scoop: `scoop install make`

#### 0-3. 로컬 Kubernetes 클러스터 기동
kind 클러스터와 metrics-server, Argo CD 플랫폼 컴포넌트를 한 번에 설치합니다:
```bash
./make.sh cluster
```
*설치 완료 후 `kubectl get nodes` 명령으로 노드가 `Ready` 상태인지 확인합니다.*

---

### Lab 1. 자체 애플리케이션 차트 개발 및 로컬 배포

#### 1-1. 차트 린트 및 템플릿 렌더링 확인 (dev vs prod 환경 분기)
클러스터에 적용하기 전, 템플릿 문법과 환경별 렌더링 결과 YAML을 확인합니다:
```bash
./make.sh lint                                                      # 차트 문법 및 구조 검사
./make.sh template ENV=dev                                          # dev 환경 매니페스트 확인 (1개 복제본)
./make.sh template ENV=prod | grep -A5 "kind: HorizontalPodAutoscaler" # prod 환경 HPA 확인
```
> **관찰 포인트**: 동일한 차트 템플릿이지만 `values-prod.yaml`의 `autoscaling.enabled: true` 설정에 의해 prod 환경에서는 Deployment의 `replicas` 필드가 생략되고 HPA 리소스가 동적으로 생성됩니다.

#### 1-2. 데이터베이스 및 애플리케이션 설치
```bash
./make.sh db-dev       # 1) PostgreSQL DB 릴리스 설치 (Secret: shop-db-credentials 자동 생성)
./make.sh build        # 2) FastAPI 앱 컨테이너 빌드 후 kind 노드에 로컬 로드
./make.sh deploy-dev   # 3) shop-api 배포 (사전 마이그레이션 Hook Job 실행 후 Deployment 배포)
./make.sh status       # 4) 배포된 파드 및 서비스 상태 확인
```

#### 1-3. 서비스 동작 검증 (API & Swagger UI)
포트 포워딩을 통해 로컬 머신에서 서비스에 접근합니다:
```bash
kubectl -n shop-dev port-forward svc/shop-api 5678:80
```
* **Swagger 대화형 API 문서**: 브라우저에서 [http://localhost:5678/docs](http://localhost:5678/docs) 접속 (모든 API 시각적 테스트)
* **상품 목록 조회 (DB 연동)**: 브라우저에서 [http://localhost:5678/items](http://localhost:5678/items) 접속 (기본 상품 2건 확인)
* **버전 및 인사말 확인**: 브라우저에서 [http://localhost:5678/version](http://localhost:5678/version) 접속 (`Hello from DEV`)
* **루트 경로 안내**: 브라우저에서 [http://localhost:5678/](http://localhost:5678/) 접속 시 엔드포인트 목록 확인

#### 1-4. 설정 변경 → 자동 롤링 업데이트 → 롤백 실습
ConfigMap 값이 변경되었을 때 파드가 자동으로 재시작되는 원리를 체험합니다:
```bash
# 1) 인사말 변경 (ConfigMap 갱신)
helm upgrade shop-api charts/shop-api -n shop-dev --reuse-values --set config.greeting="안녕하세요"

# 2) 파드 롤링 교체 실시간 확인
kubectl -n shop-dev get po -w   # checksum/config 어노테이션 변경으로 인해 새 파드가 뜨고 구버전 종료

# 3) 배포 히스토리 확인 및 이전 버전 롤백
./make.sh history               # 리비전 목록 확인
./make.sh rollback 1            # 1번 리비전으로 즉시 롤백 (REV=1)
```

#### 1-5. 스키마 유효성 검증 (`values.schema.json`)
Helm의 JSON Schema 검증 기능이 잘못된 설정을 사전 차단하는 것을 확인합니다:
```bash
helm template x charts/shop-api --set replicaCount=0              # 최소 복제본(1 이상) 규칙 위반 → 즉시 에러 차단
helm template x charts/shop-api --set database.existingSecret=""         # 필수 시크릿 지정 함수(required) 위반 → 에러 차단
```

---

### Lab 2. Helm Hook 으로 DB 마이그레이션 무중단 처리

애플리케이션 신규 배포 시 파드가 교체되기 전에 DB 스키마가 먼저 최신화되어야 데이터 불일치가 발생하지 않습니다.

#### 2-1. 정상 마이그레이션 (스키마 확장)
상품 테이블에 `stock`(재고) 컬럼을 추가하는 실습용 마이그레이션 SQL을 활성화합니다:
```bash
# 1) 실습용 마이그레이션 파일 확장자 변경 (.example 제거)
mv app/migrations/002_add_stock.sql.example app/migrations/002_add_stock.sql

# 2) 이미지 재빌드 및 재배포
./make.sh build
./make.sh deploy-dev

# 3) 마이그레이션 훅 Job 로그 확인
kubectl -n shop-dev logs job/shop-api-migrate
```
* **결과 확인**: `[migrate] skip 001_create_items.sql` 후 `[migrate] apply 002_add_stock.sql`이 차례로 출력되고, 포트포워딩 상태에서 `/items` 조회 시 `stock` 필드가 포함된 것을 확인할 수 있습니다.

#### 2-2. 마이그레이션 실패 시나리오 — 무중단 서비스 보호 검증
만약 SQL 스키마 마이그레이션 중 문법 오류나 문제가 발생하면 어떤 일이 일어나는지 검증합니다:
```bash
# 1) 일부러 문법 오류가 있는 SQL 생성
echo "ALTER TABLE no_such_table ADD COLUMN x INTEGER;" > app/migrations/003_broken.sql

# 2) 빌드 및 배포 시도
./make.sh build
./make.sh deploy-dev            # pre-upgrade 훅 실패로 인해 Helm upgrade가 즉시 중단됨

# 3) 클러스터 상태 확인
./make.sh history               # 최신 리비전 STATUS = failed 로 기록됨
kubectl -n shop-dev get po      # 중요한 점: 기존에 동작 중이던 정상 파드는 종료되지 않고 그대로 Running 유지!
```
* **정리**: 깨진 파일 삭제 후 재배포:
  ```bash
  rm -f app/migrations/003_broken.sql
  ./make.sh build && ./make.sh deploy-dev
  ```
> 🔎 **토론**: 훅 Job은 `helm uninstall`이나 롤백 때 되돌려지지 않습니다. **스키마 변경은 항상 하위 호환(expand → contract)**으로 설계해야 하는 이유를 생각해 보세요.

---

### Lab 3. GitHub Actions CI 파이프라인

개발자가 코드를 푸시하면 자동으로 컨테이너 이미지와 Helm OCI 차트 패키지를 빌드하고 레지스트리에 게시합니다.

#### 3-1. GitHub 저장소 권한 설정
1. 이 저장소를 본인 GitHub 계정으로 `push`합니다.
2. 저장소의 **Settings → Actions → General → Workflow permissions**에서 **"Read and write permissions"**를 선택하고 저장합니다.

#### 3-2. PR을 통한 린트(Lint) 검증
1. 새 브랜치를 만들어 `app/main.py`의 인사말이나 주석을 약간 수정한 뒤 PR을 생성합니다.
2. PR 단계에서는 테스트 및 정적 검사를 위한 **`lint` 잡**만 가볍게 실행되는 것을 확인합니다.

#### 3-3. PR 병합 및 자동 릴리스 (4개 Job)
PR을 `main` 브랜치에 병합(Merge)하면 아래 4개의 CI 잡이 순차 실행됩니다:
1. `lint`: 차트 문법 및 유효성 검사
2. `build-image`: 컨테이너 이미지를 빌드하여 `ghcr.io/<내계정>/shop-api:<커밋SHA>`로 푸시
3. `publish-chart`: Helm 차트를 OCI 형식으로 패키징하여 `oci://ghcr.io/<내계정>/charts/shop-api:0.1.0`에 게시
4. `update-manifest`: 빌드된 새 이미지 태그를 `charts/shop-api/values-prod.yaml`의 `image.tag`에 자동 반영하여 커밋

#### 3-4. Helm 차트 OCI 레지스트리(GHCR) Push & Pull 완벽 가이드

Helm 3.8+ 부터 OCI(Open Container Initiative) 표준을 기본 지원하므로, Docker 이미지를 저장하는 **GitHub Container Registry (GHCR)**에 Helm 차트도 독립된 OCI 아티팩트로 저장·관리할 수 있습니다.

> 📌 **저장소 경로 구분**:
> * **Docker 컨테이너 이미지**: `ghcr.io/<내_깃허브_계정>/shop-api:<태그>`
> * **Helm 차트 OCI 아티팩트**: `oci://ghcr.io/<내_깃허브_계정>/charts/shop-api:<버전>` *(OCI 프로토콜 사용 시 `oci://` 접두사 필수)*

---

##### (1) 사전 준비: GitHub Personal Access Token (PAT) 발급 및 Helm 로그인
로컬 터미널에서 GHCR에 차트를 푸시하려면 패키지 쓰기 권한이 있는 Personal Access Token(PAT)이 필요합니다:
1. GitHub 웹사이트 > 우측 상단 프로필 > **Settings** > 좌측 맨 아래 **Developer Settings** 클릭
2. **Personal access tokens** > **Tokens (classic)** > **Generate new token (classic)** 선택
3. 토큰 권한(Scopes)에서 **`write:packages`** (자동으로 `read:packages` 포함), **`delete:packages`**(선택) 체크 후 발급
4. 터미널에서 토큰으로 Helm 레지스트리 로그인:
   ```bash
   # 토큰을 환경변수로 설정
   export CR_PAT="<발급받은_GitHub_PAT_토큰>"

   # Helm OCI 레지스트리 로그인
   echo $CR_PAT | helm registry login ghcr.io -u <내_깃허브_계정> --password-stdin
   ```
   *로그인 성공 시 `Login Succeeded` 메시지가 출력됩니다.*

---

##### (2) Helm 차트 패키징 (`helm package`)
`charts/shop-api/Chart.yaml`에 정의된 `version`(예: `0.1.0`)을 기준으로 차트를 압축 아카이브(`.tgz`)로 생성합니다:
```bash
helm package charts/shop-api
```
*실행 결과: 현재 디렉토리에 `shop-api-0.1.0.tgz` 파일이 생성됩니다.*

---

##### (3) Helm 차트 OCI 레지스트리에 푸시 (`helm push`)
생성된 `.tgz` 아카이브를 본인의 GHCR OCI 저장소로 푸시합니다:
```bash
helm push shop-api-0.1.0.tgz oci://ghcr.io/<내_깃허브_계정>/charts
```
*성공 출력 예시*:
```text
Pushed: ghcr.io/<내_깃허브_계정>/charts/shop-api:0.1.0
Digest: sha256:xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

> ⚠️ **차트 버전 불변성(Immutability) 주의**:  
> OCI 차트 레지스트리는 동일한 버전을 덮어쓸 수 없습니다. 차트를 수정하여 다시 푸시할 때는 반드시 [charts/shop-api/Chart.yaml](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/07week/helm-shop-lab/charts/shop-api/Chart.yaml)의 `version`을 `0.1.1` 등으로 올린 후 패키징하여 푸시해야 합니다.

---

##### (4) GHCR 패키지 Public 전환 (필수)
기본적으로 GHCR에 새로 푸시된 패키지는 비공개(Private) 상태입니다. kind 클러스터나 팀원이 인증 없이 다운로드할 수 있도록 공개로 전환합니다:
1. GitHub 본인 프로필 > **Packages** 탭으로 이동
2. 방금 푸시된 `charts/shop-api` 패키지 클릭
3. 우측 하단의 **Package settings** 클릭
4. 페이지 맨 아래 **Danger Zone**의 **Change package visibility**를 **Public**으로 변경

---

##### (5) 원격 OCI 차트 조회 및 다운로드 (`helm show` & `helm pull`)
푸시된 원격 차트를 로컬에서 조회하고 다운로드(pull)합니다:

```bash
# 1) 차트 메타데이터(Chart.yaml 내용) 확인
helm show chart oci://ghcr.io/<내_깃허브_계정>/charts/shop-api --version 0.1.0

# 2) 차트의 기본 설정값(values.yaml 내용) 확인
helm show values oci://ghcr.io/<내_깃허브_계정>/charts/shop-api --version 0.1.0

# 3) 차트 아카이브(.tgz) 다운로드 (Pull)
helm pull oci://ghcr.io/<내_깃허브_계정>/charts/shop-api --version 0.1.0

# 4) 차트 압축을 바로 풀며 디렉토리 형태로 다운로드
helm pull oci://ghcr.io/<내_깃허브_계정>/charts/shop-api --version 0.1.0 --untar
```

---

##### (6) 원격 OCI 차트에서 클러스터로 직접 배포
로컬 차트 폴더 없이도 GHCR의 OCI 차트 주소만으로 쿠버네티스 클러스터에 바로 설치할 수 있습니다:
```bash
helm upgrade --install shop-api oci://ghcr.io/<내_깃허브_계정>/charts/shop-api \
  --version 0.1.0 \
  -n shop-dev \
  -f charts/shop-api/values-dev.yaml
```

---

### Lab 4. Argo CD GitOps 운영 배포

운영 환경에서는 사람이 직접 `helm` 배포 명령을 실행하지 않고, **Git 커밋을 단일 진실 공급원(Single Source of Truth)으로 삼아 Argo CD가 선언적으로 클러스터를 동기화**합니다.

#### 4-1. 운영 네임스페이스 및 시크릿 준비
```bash
kubectl create ns shop-prod
kubectl -n shop-prod create secret generic shop-db-credentials \
  --from-literal=username=shop --from-literal=password='S3cure-Pass'
```

#### 4-2. Argo CD Application 등록 및 웹 UI 접속
```bash
./make.sh argocd                                                  # argocd/shop-prod.yaml 매니페스트 적용
kubectl -n argocd port-forward svc/argocd-server 8443:80          # Argo CD UI 포트 포워딩
```
* 브라우저에서 [http://localhost:8443](http://localhost:8443) 접속
* **로그인**: 아이디 `admin`, 초기 비밀번호는 아래 명령으로 확인:
  ```bash
  kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath='{.data.password}' | base64 -d; echo
  ```

#### 4-3. Git 커밋 기반 자동 배포 (GitOps 배포 흐름)
1. `app/main.py`의 코드를 수정하여 GitHub `main`에 push합니다.
2. GitHub Actions CI가 새 이미지를 빌드하고 `values-prod.yaml`의 태그를 변경하는 커밋을 생성합니다.
3. Argo CD가 Git의 변경(OutOfSync)을 자동 감지하고, **PreSync 훅(DB 마이그레이션)**을 먼저 실행한 후 **롤링 업데이트**를 완료합니다.

#### 4-4. Self-heal (자가 치유) 체험
누군가 클러스터의 ConfigMap을 수동으로 변조하더라도 Argo CD가 Git 형상으로 되돌리는 것을 확인합니다:
```bash
# ConfigMap 값을 임의로 변조
kubectl -n shop-prod patch cm shop-api-config -p '{"data":{"GREETING":"hacked"}}'

# 잠시 후 확인하면 Argo CD에 의해 Git에 선언된 원래 값("Hello from PROD")으로 자동 복원됨!
kubectl -n shop-prod get cm shop-api-config -o yaml | grep GREETING
```

#### 4-5. Git 기반 선언적 롤백
GitOps 환경에서는 클러스터에서 `helm rollback`을 실행하지 않고(실행하더라도 Argo CD가 Git 상태로 다시 덮어씀), **Git 커밋을 되돌려 롤백**합니다:
```bash
git revert <이전_배포_커밋_SHA>
git push origin main
```
*Argo CD가 revert된 커밋을 감지하고 이전 안정 버전으로 안전하게 복귀합니다.*

#### 4-6. argocd CLI 로 관찰하기 (선택 사항)
CLI가 설치되어 있는 경우 포트 포워딩 상태에서 다음 명령으로 상태를 조회할 수 있습니다:
```bash
argocd login localhost:8443 --plaintext --username admin
argocd app list                      # Sync / Health 상태
argocd app get shop-api-prod         # 리소스 트리 (Deployment·HPA·PDB·PreSync Job)
argocd app diff shop-api-prod        # Git 렌더링 결과 vs 클러스터 차이
argocd app sync shop-api-prod        # 즉시 동기화
```

---

## 5. 자주 겪는 문제 및 트러블슈팅

| 증상 | 원인 | 해결 방법 |
|---|---|---|
| `bash: make: command not found` | Windows Git Bash에 `make` 부재 | `./make.sh <타깃>` 스크립트를 사용하거나 `winget install ezwinports.make` 설치 |
| `{"detail":"Not Found"}` | 루트(`/`) 경로에 라우트 없음 | 브라우저에서 `/docs`, `/items`, `/version` 경로로 접속 |
| `failed pre-install ... context deadline exceeded` | 마이그레이션 Job 파드가 이미지를 찾지 못함 | `values.yaml`의 `image.repository`가 본인 빌드 이미지와 일치하는지 확인 |
| `ErrImagePull` (dev) | kind 클러스터 노드에 이미지가 없음 | `./make.sh build`로 kind 노드에 로컬 로드되었는지 확인 |
| `ImagePullBackOff` (prod) | GHCR 패키지 비공개(Private) 상태 | GitHub 프로필 > Packages > `shop-api` 패키지 설정을 **Public**으로 변경 |
| 마이그레이션 Job이 계속 `DB 대기 중` | PostgreSQL DB 파드 미기동 또는 Secret 불일치 | `kubectl -n shop-dev get po`로 `shop-db-0` 상태 및 Secret(`shop-db-credentials`) 확인 |
| `UPGRADE FAILED: pre-upgrade hooks failed` | 마이그레이션 SQL 실행 오류 | `kubectl logs job/shop-api-migrate -n shop-dev`로 오류 로그 확인 후 SQL 수정 |
| HPA `TARGETS <unknown>` | metrics-server가 설치되지 않음 | `./make.sh cluster` 재실행하여 metrics-server 정상 배포 |

## 6. 참고 및 출처 (References)

* **실습 원문 저장소 (Upstream Source)**: [cstpeace0191/helm-shop-lab](https://github.com/cstpeace0191/helm-shop-lab)
* **개인 실습 포크 저장소 (Personal Repo)**: [cstpeace0191/helm-shop-lab](https://github.com/cstpeace0191/helm-shop-lab)
* **Helm 공식 문서**:
  * [Chart Template Guide](https://helm.sh/docs/chart_template_guide/)
  * [Chart Hooks](https://helm.sh/docs/topics/charts_hooks/)
  * [Helm OCI Registries](https://helm.sh/docs/topics/registries/)
* **Argo CD 공식 문서**:
  * [Argo CD Helm Integration](https://argo-cd.readthedocs.io/en/stable/user-guide/helm/)
  * [Resource Hooks & Sync Waves](https://argo-cd.readthedocs.io/en/stable/user-guide/resource_hooks/)
* **참고 사항**:
  * 이 저장소의 `shop-db`는 로컬 실습 전용입니다. 운영 환경에서는 클라우드 관리형 DB(RDS, Cloud SQL 등) 또는 CloudNativePG 같은 Kubernetes 오퍼레이터 사용을 권장합니다.
