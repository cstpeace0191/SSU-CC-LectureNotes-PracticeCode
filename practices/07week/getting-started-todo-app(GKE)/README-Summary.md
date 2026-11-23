# GKE Todo 애플리케이션 클라우드 네이티브 아키텍처 및 실습 총괄 요약서 (README-Summary)

본 문서는 **Todo 애플리케이션(React 프론트엔드 + Express Node.js 백엔드 + MySQL 데이터베이스)**을 Google Kubernetes Engine(GKE)에 배포하고 운영하기 위해 실습한 전체 클라우드 네이티브 기술 스택을 총괄 정리한 마스터 가이드입니다.

---

## 1. 프로젝트 아키텍처 개요

본 프로젝트는 Docker Compose 기반의 로컬 개발 환경에서 출발하여, 클라우드 환경(GKE)의 프로덕션 수준 클라우드 네이티브 서비스로 진화시키는 과정을 다룹니다.

```
                    [사용자 / 웹 브라우저]
                              │
               (인터넷 트래픽 진입점: L4 / L7)
                              │
       ┌──────────────────────┼──────────────────────┐
       ▼                      ▼                      ▼
[Service: LoadBalancer]  [GKE Ingress]       [GKE Gateway API]
  (GCP L4 Passthrough)     (GCP External ALB)  (GCP External Managed ALB)
       │                      │                      │
       │                      ├─ ManagedCertificate  ├─ HTTPRoute
       │                      ├─ FrontendConfig      └─ nip.io 와일드카드 DNS
       │                      └─ BackendConfig
       │                              │                      │
       └──────────────────────┬───────┴──────────────────────┘
                              ▼
                 [컨테이너 네이티브 부하 분산 (NEG)]
                              │
            ┌─────────────────┴─────────────────┐
            ▼                                   ▼
[Pod: todo-backend (React+Express)] ──➔ [Pod: mysql (데이터베이스)]
  (단일 컨테이너 번들, 포트 3000)          (표준 포트 3306, PVC 연동)
```

### 아키텍처 핵심 특징
1. **프론트엔드/백엔드 단일 컨테이너 통합 (프로덕션 빌드)**:
   * 로컬 개발 시에는 Vite(개발 서버)와 nodemon이 분리되어 Traefik 리버스 프록시가 필요했으나,
   * 프로덕션 GKE 환경에서는 멀티 스테이지 빌드(`Dockerfile`)를 통해 React 정적 에셋(HTML, CSS, JS)이 Express 백엔드 내부에 통합 번들링되어 포트 3000으로 직접 서빙됩니다.
2. **쿠버네티스 네이티브 서비스 디스커버리**:
   * 백엔드 파드는 `mysql:3306` 내부 도메인을 통해 CoreDNS로 MySQL 서비스에 안전하게 연결됩니다.

---

## 2. 도커 컴포즈에서 쿠버네티스로의 전환 도구 (Katenary & Helm)

### 1) Katenary
* **정의**: Docker Compose 파일(`compose.yaml`)을 분석하여 쿠버네티스 표준 매니페스트 및 Helm Chart로 자동 변환해 주는 CLI 오픈소스 도구입니다.
* **주요 역할**: Compose의 서비스, 볼륨, 환경 변수, 포트 매핑을 쿠버네티스의 `Deployment`, `Service`, `PersistentVolumeClaim(PVC)`, `ConfigMap`, `Secret`으로 자동 매핑합니다.
* 👉 **상세 가이드**: [`Katenary-README-KR.md`](...//getting-started-todo-app(GKE)/Katenary-README-KR.md)

### 2) Helm (쿠버네티스 패키지 매니저)
* **정의**: 복잡한 쿠버네티스 매니페스트들을 템플릿화하여 하나의 패키지(Chart) 단위로 관리, 배포, 버전 롤백을 수행하는 도구입니다.
* **주요 활용**: `values.yaml` 설정을 통해 개발/스테이징/운영 환경별로 파라미터를 유연하게 주입하여 일관된 릴리스를 배포합니다.
* 👉 **상세 가이드**: [`README(HelmChart).md`](...//getting-started-todo-app(GKE)/README(HelmChart).md)

---

## 3. 쿠버네티스 매니페스트 정적 분석 및 보안 감사 (KubeLinter)

### 1) KubeLinter 개요
* Red Hat(구 StackRox)에서 오픈소스로 개발한 **쿠버네티스 매니페스트 정적 분석(Linter) 도구**입니다.
* 클러스터에 배포하기 전에 보안 모범 사례(Security Best Practices)와 운영 안정성 모범 사례(Production Readiness)를 사전 점검하는 **Shift-Left 보안**을 제공합니다.

### 2) 주요 서브커맨드 요약
| 서브커맨드 | 설명 |
| :--- | :--- |
| **`lint`** | 쿠버네티스 YAML 매니페스트 파일, 디렉터리, Helm 차트를 정적 검사합니다. |
| **`checks`** | 기본 내장된 50여 개 이상의 보안/안정성 검사 규칙(`checks list`)을 조회합니다. |
| **`templates`** | 사용자 정의 검사 룰을 작성하기 위한 템플릿 목록(`templates list`)을 확인합니다. |
| **`version`** | 설치된 바이너리의 버전 정보를 출력합니다. |

* 👉 **상세 가이드**: [`kubelinter-README-KR.md`](...//getting-started-todo-app(GKE)/kubelinter-README-KR.md)

---

## 4. 쿠버네티스 서비스(Service) 모델 분석

파드(Pod)는 동적으로 생성·소멸되는 일회성 자원이므로 고정된 진입점이 필요합니다. 쿠버네티스 서비스는 이러한 파드 집합에 고정 IP와 로드밸런싱을 제공합니다.

### 1) 서비스 3대 유형 비교

| 서비스 유형 | 접근 범위 | 주요 특징 및 역할 |
| :--- | :--- | :--- |
| **`ClusterIP`** (기본값) | 클러스터 내부 전용 | 클러스터 내부 가상 IP 할당, 백엔드 마이크로서비스 및 DB 통신에 사용 |
| **`NodePort`** | 노드 IP + 물리 포트 | 모든 워커 노드의 물리 포트(30000~32767)를 개방하여 외부 트래픽 수신 |
| **`LoadBalancer`** | 인터넷 공인 IP 노출 | 클라우드 공급자(GCP)의 외부 L4 로드밸런서를 자동 프로비저닝하여 공인 IP 할당 |

### 2) GKE LoadBalancer 동작 원리 및 설정
* **공인 IP 자동 프로비저닝**: `kubectl apply -f GKE-service-lb.yaml` 실행 시 GKE Cloud Controller Manager(CCM)가 GCP Compute Engine API를 호출하여 외부 고유 공인 IP(`EXTERNAL-IP`), 포워딩 룰(포트 80 TCP), 방화벽 규칙을 자동 생성합니다.
* **`externalTrafficPolicy: Local` 설정의 중요성**:
  * 클라이언트의 실제 IP(Client Source IP)를 보존(SNAT 방지)합니다.
  * 노드 간 불필요한 2차 네트워크 홉을 제거하여 지연 시간을 줄입니다.
  * 실제 해당 파드가 실행 중인 워커 노드로만 GCP 로드밸런서 헬스체크를 통과시켜 트래픽을 분산합니다.
* **서비스 배포 의존성**: `GKE-service-lb.yaml`은 독립된 객체이므로 사전에 `ClusterIP`나 `NodePort` 파일을 먼저 배포할 필요가 없습니다. (LoadBalancer 자체에 ClusterIP와 NodePort가 자동 내장됨).
* 👉 **상세 가이드**: [`README-Service-LoadBalancer.md`](...//getting-started-todo-app(GKE)/README-Service-LoadBalancer.md)

---

## 5. L7 애플리케이션 부하 분산 (GKE Ingress)

L4 로드밸런서(Service)가 단순 IP/포트 기반 포워딩만 수행하는 반면, **Ingress**는 HTTP/HTTPS 프로토콜의 URL 경로 및 호스트 헤더를 분석하는 **L7 글로벌 외부 애플리케이션 부하 분산기(External Application Load Balancer)**입니다.

### 핵심 구성 요소
1. **`Ingress` 리소스 ([`GKE-ingress.yaml`](...//getting-started-todo-app(GKE)/GKE-ingress.yaml))**:
   * 단일 공인 IP로 도메인 기반 가상 호스팅 및 경로(`/`, `/api`) 라우팅 수행
2. **`ManagedCertificate` ([`managed-cert-fc.yaml`](...//getting-started-todo-app(GKE)/managed-cert-fc.yaml))**:
   * Google이 관리하는 무료 SSL/TLS 인증서를 자동 발급·갱신 (인증서 시크릿 수동 관리 불필요)
3. **`FrontendConfig`**:
   * HTTP(포트 80) 요청을 안전한 HTTPS(포트 443)로 강제 301 영구 리다이렉트
4. **`BackendConfig`**:
   * GCP 부하 분산기가 백엔드 파드의 생존 여부를 판단할 수 있도록 커스텀 헬스체크 경로(`/api/items`) 연동
* 👉 **상세 가이드**: [`README-Ingress.md`](...//getting-started-todo-app(GKE)/README-Ingress.md)

---

## 6. 차세대 네트워킹 표준: GKE Gateway API

**Gateway API**는 기존 Ingress의 한계를 극복하고 멀티 테넌시 및 고급 L7 트래픽 제어를 위해 표준화된 최신 쿠버네티스 네트워킹 사양입니다.

### 1) 핵심 아키텍처 및 역할 분리
* **인프라 관리자 (`Gateway`)**: 포트, 프로토콜, 인증서, 공인 IP 바인딩 관리 (`GKE-gateway-nip.yaml`)
* **애플리케이션 개발자 (`HTTPRoute`)**: 호스트네임, URL 경로 매칭, 가중치 기반 분기 정책 관리 (`GKE-httproutes-nip.yaml`)

### 2) GKE 컨테이너 네이티브 부하 분산 (NEG)
* GKE Gateway Controller는 노드 포트(NodePort)를 완전히 우회하고 파드의 IP로 직접 패킷을 전송하는 **NEG(Network Endpoint Group)** 방식을 기본 사용합니다.
* 복잡한 주석 없이 표준 문법으로 **카나리(Canary) 트래픽 분할(예: 90% vs 10%)**을 지원합니다.
* 👉 **상세 가이드**: [`README-Gateway.md`](...//getting-started-todo-app(GKE)/README-Gateway.md)

---

## 7. [핵심 실습 검증] nip.io 와일드카드 DNS와 GKE Gateway 연동 실습

> [!IMPORTANT]
> **본 실습의 핵심 목적**:  
> 본 실습의 핵심은 **별도의 유료 도메인 구매나 SSL/TLS 인증서 등록 없이도, `nip.io` 와일드카드 DNS와 GKE가 자동 프로비저닝하는 동적 외부 공인 IP(Dynamic External IP)를 결합**하여 실제 프로덕션 도메인 환경과 동일한 호스트 기반 L7 라우팅 및 웹 애플리케이션 서비스를 완벽하게 검증하는 것입니다.

### 1) nip.io 와일드카드 DNS 원리
* `nip.io`는 `<어떤이름>.<IP주소>.nip.io` 형식의 질의가 들어오면, 주소 중간의 `<IP주소>`를 DNS A 레코드로 즉시 반환합니다.
* 예: `www.ssu-cloud-computing-gke.34.160.156.124.nip.io` ➔ DNS 질의 시 **`34.160.156.124`**로 자동 매핑되어 전 세계 어디서든 즉시 접속 가능.

### 2) 전체 실습 실행 명령어 요약 (Command Cheatsheet)

```bash
# 1. GKE 클러스터에 Gateway API 활성화 (클러스터당 최초 1회)
gcloud container clusters update my-gke-cluster --gateway-api=standard --zone=asia-northeast3-a

# 2. Gateway API 컨트롤러 및 클래스 등록 확인
kubectl get gatewayclass

# 3. Gateway 리소스 배포 (GCP L7 글로벌 외부 로드밸런서 자동 프로비저닝)
kubectl apply -f GKE-gateway-nip.yaml

# 4. 할당된 동적 외부 공인 IP(ADDRESS) 확인 (<IP> 확보, 예: 34.160.156.124)
kubectl get gateway external-gateway -n infra-team --watch

# 5. 백엔드 워크로드 및 NEG 활성화 서비스 배포 (실제 Todo 웹 UI 파드와 연결)
kubectl apply -f sample-workloads.yaml
kubectl get endpoints app-service

# 6. nip.io 기반 HTTPRoute 매니페스트 배포 (GKE-httproutes-nip.yaml)
#    (hostnames 에 4단계에서 확보한 공인 IP가 적용되어 있는지 확인)
kubectl apply -f GKE-httproutes-nip.yaml

# 7. HTTPRoute 바인딩 및 라우팅 상태 확인 (Accepted: True 확인)
kubectl describe httproute web-app-route -n default

# 8. nip.io 도메인 이름 자동 해석 검증
nslookup www.ssu-cloud-computing-gke.34.160.156.124.nip.io

# 9. curl 을 통한 Todo 웹 인터페이스(HTML) 응답 검증 (초기 전파 1~2분 후 수행)
curl -i http://www.ssu-cloud-computing-gke.34.160.156.124.nip.io/

# 10. 웹 브라우저 최종 접속 확인
#     http://www.ssu-cloud-computing-gke.34.160.156.124.nip.io/
```

### 3) 검증 결과 확인
* **테스트 컨테이너(`whereami`) vs 실제 웹앱(`todo-backend`)**:
  * 구글 샘플 컨테이너인 `whereami`는 디버깅용 JSON 메타데이터만 반환합니다.
  * 서비스의 `selector`를 `app: todo-backend`(포트 3000)로 연결하여, 브라우저 접속 시 실제 **Todo App React UI**가 정상 렌더링됨을 최종 확인했습니다.

---

## 8. 프로젝트 매니페스트 및 참조 문서 맵

| 파일명 | 종류 | 주요 역할 및 설명 | 세부 가이드 링크 |
| :--- | :--- | :--- | :--- |
| **`GKE-gateway-nip.yaml`** | 쿠버네티스 매니페스트 | L7 글로벌 관리형 로드밸런서(`external-gateway`, HTTP 80) 선언 | [`README-Gateway.md`](...//getting-started-todo-app(GKE)/README-Gateway.md) |
| **`GKE-httproutes-nip.yaml`** | 쿠버네티스 매니페스트 | nip.io 기반 웹앱(`web-app-route`) 및 API(`api-route`) 멀티 호스트 분기 라우팅 | [`README-Gateway.md`](...//getting-started-todo-app(GKE)/README-Gateway.md) |
| **`sample-workloads.yaml`** | 쿠버네티스 매니페스트 | NEG 활성화 서비스(`app-service`, `api-service`) 및 테스트 파드 정의 | [`README-Gateway.md`](...//getting-started-todo-app(GKE)/README-Gateway.md) |
| **`GKE-service-lb.yaml`** | 쿠버네티스 매니페스트 | GCP L4 외부 패스스루 네트워크 부하 분산기 서비스 선언 | [`README-Service-LoadBalancer.md`](...//getting-started-todo-app(GKE)/README-Service-LoadBalancer.md) |
| **`GKE-service-np.yaml`** | 쿠버네티스 매니페스트 | 노드 포트(30080) 서비스 및 Ingress 백엔드용 매니페스트 | [`README-Ingress.md`](...//getting-started-todo-app(GKE)/README-Ingress.md) |
| **`GKE-service-cip.yaml`** | 쿠버네티스 매니페스트 | 클러스터 내부 전용 가상 IP 서비스 선언 | [`README-Service-LoadBalancer.md`](...//getting-started-todo-app(GKE)/README-Service-LoadBalancer.md) |
| **`GKE-ingress.yaml`** | 쿠버네티스 매니페스트 | GCE Ingress + 관리형 인증서 + HTTPS 리다이렉트 통합 선언 | [`README-Ingress.md`](...//getting-started-todo-app(GKE)/README-Ingress.md) |
| **`managed-cert-fc.yaml`** | 쿠버네티스 매니페스트 | Google 관리형 인증서(`ManagedCertificate`) 및 `FrontendConfig` | [`README-Ingress.md`](...//getting-started-todo-app(GKE)/README-Ingress.md) |
| **`GKE-deployment-GCP.yaml`**| 쿠버네티스 매니페스트 | Todo 백엔드 및 MySQL 9.3 GKE 단독 배포용 통합 매니페스트 | [`README.md`](...//getting-started-todo-app(GKE)/README.md) |
| **`kube-linter`** | 실행 바이너리 | 쿠버네티스 YAML 정적 분석 및 보안 취약점 사전 진단 CLI | [`kubelinter-README-KR.md`](...//getting-started-todo-app(GKE)/kubelinter-README-KR.md) |
| **`charts/`** | Helm 차트 디렉터리 | Katenary를 통해 생성된 Todo 애플리케이션 Helm 패키징 차트 | [`README(HelmChart).md`](...//getting-started-todo-app(GKE)/README(HelmChart).md) |
