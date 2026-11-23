# GKE Gateway API 가이드 및 nip.io 실습 매뉴얼

이 문서는 쿠버네티스 **Gateway API**의 개념과 GKE에서의 동작 방식, **`nip.io` 와일드카드 DNS**를 활용한 호스트 기반 L7 라우팅, 그리고 본 프로젝트의 **Todo 웹 애플리케이션(React + Express)**을 서비스하기 위한 검증된 배포 절차와 트러블슈팅을 정리한 실습 가이드입니다.

> [!IMPORTANT]
> **본 실습의 핵심**:  
> 본 실습의 핵심은 **별도의 유료 도메인 구매나 SSL/TLS 인증서 등록 없이도, `nip.io` 와일드카드 DNS와 GKE가 자동 프로비저닝하는 동적 외부 공인 IP(Dynamic External IP)를 결합**하여 실제 프로덕션 도메인 환경과 동일한 호스트 기반 L7 라우팅 및 웹 애플리케이션 서비스를 완벽하게 검증하는 것입니다.

---

## 1. 쿠버네티스 Gateway API란?

**Gateway API**는 기존 쿠버네티스 `Ingress`의 구조적 한계를 극복하고 차세대 서비스 네트워킹을 표준화하기 위해 발전된 공식 쿠버네티스 네트워킹 사양(Specification)입니다.

### 1) Ingress 대비 주요 차이점 및 장점
* **역할 분리 (Role-oriented Architecture)**:
  * **인프라 관리자 (Platform Admin)**: 로드밸런서 인프라 스펙, 포트, 인증서(`Gateway` 리소스)를 관리.
  * **애플리케이션 개발자 (App Developer)**: 특정 서비스로의 라우팅 경로, 가상 호스트, 트래픽 정책(`HTTPRoute` 리소스)을 독립적으로 관리.
* **L7 고급 기능 표준 내장**: 복잡한 벤더 전용 Annotations 없이도 **가중치 기반 트래픽 분할(Canary 배포)**, 호스트/헤더 기반 라우팅, URL 리라이트/리다이렉트 등을 표준 문법으로 선언할 수 있습니다.
* **컨테이너 네이티브 부하 분산 (NEG 연동)**: GKE Gateway Controller는 노드의 물리 포트(NodePort)를 거치지 않고, 파드(Pod)의 내부 IP로 직접 트래픽을 전달하는 **NEG(Network Endpoint Group)**를 기본으로 사용하여 네트워크 지연을 최소화합니다.

---

## 2. GatewayClass, 로드밸런서 유형 및 Envoy 프록시 심층 이해

GKE Gateway API를 제대로 이해하고 프로덕션 환경에 적용하기 위해서는 `gatewayClassName`, GCP 로드밸런서 유형, 그리고 하위 구동 엔진인 `Envoy` 프록시의 역할을 명확히 파악해야 합니다.

### 1) `gatewayClassName`의 개념과 역할
* **개념**: 쿠버네티스의 `StorageClass`가 다양한 스토리지 백엔드(SSD, HDD, NFS 등)를 추상화하듯, **`gatewayClassName`은 `Gateway` 리소스가 실제로 어떤 하위 인프라(로드밸런서 컨트롤러)에 의해 생성되고 동작할지를 결정하는 지정자**입니다.
* **추상화의 장점**: 애플리케이션 개발자나 인프라 관리자는 동일한 Gateway API YAML 문법을 사용하면서, `gatewayClassName` 필드만 변경함으로써 GCP Cloud Load Balancing, AWS ALB, NGINX Ingress Controller, Istio, Cilium 등으로 손쉽게 백엔드 네트워킹 인프라를 교체할 수 있습니다.
* **매핑 관계**:
  ```yaml
  kind: Gateway
  spec:
    gatewayClassName: gke-l7-global-external-managed  # 클러스터에 등록된 GatewayClass 이름을 참조
  ```

### 2) GKE GatewayClass 유형 비교: `global` vs `regional`

GKE Gateway API를 활성화하면 Google Cloud가 제공하는 관리형 L7 부하 분산기 클래스들이 클러스터에 등록됩니다. 대표적인 두 유형의 차이는 다음과 같습니다:

| 항목 | `gke-l7-global-external-managed` (본 실습 사용) | `gke-l7-regional-external-managed` |
| :--- | :--- | :--- |
| **서비스 범위** | **전 세계 글로벌 (Global)** | **특정 GCP 단일 리전 (Regional)** |
| **IP 및 네트워크 인입** | Google의 전 세계 엣지 PoP(Point of Presence)를 통한 **Anycast 단일 공인 IP** 제공 | 해당 리전 내부로 직접 인입되는 **리전 공인 IP** 제공 |
| **지연 시간 (Latency)** | 전 세계 사용자에게 가장 가까운 Google 엣지 캐시 및 네트워크를 통해 최단 지연 보장 | 해당 리전 근처 사용자에게 최적화 |
| **주요 사용 사례** | **전 세계 서비스, 글로벌 웹 애플리케이션, CDN 연동 필수 서비스** | **데이터 주권(특정 국가/리전 내 데이터 보관 규제 준수), 단일 리전 로컬 서비스** |
| **GCP Cloud Armor(WAF)** | 글로벌 보안 정책 적용 가능 | 리전 보안 정책 적용 가능 |

> [!TIP]
> **왜 `gke-l7-gxlb` 대신 `*-managed`를 사용하는가?**  
> 과거의 `gke-l7-gxlb`(Classic 글로벌 외부 부하 분산기)는 레거시 아키텍처로 최신 Gateway API의 고급 기능(가중치 분할, 헤더 기반 라우팅 등)에 제약이 있습니다. 반면 최신 **`*-managed`** 클래스는 Google의 완전 관리형 Envoy 프록시 풀을 기반으로 동작하여 Gateway API의 모든 표준 기능을 완벽하게 지원합니다.

### 3) Envoy(엔보이) 프록시란 무엇이며 왜 사용하는가?

#### ① Envoy 개요
**Envoy**는 Lyft에서 개발하여 현재 CNCF(Cloud Native Computing Foundation)의 최상위 졸업(Graduated) 프로젝트로 등록된 **초고성능 오픈소스 L7(애플리케이션 계층) 엣지 및 서비스 프록시**입니다. 모던 마이크로서비스 아키텍처의 사실상 표준(Defacto Standard) 데이터 플레인으로 널리 사용됩니다.

#### ② Envoy의 핵심 특징
* **초고성능 및 저지연**: C++11로 작성되어 뛰어난 메모리 효율성과 처리량을 자랑하며, CPU와 메모리 오버헤드가 매우 적습니다.
* **동적 설정 (xDS API)**: 프록시 서버를 재시작하지 않고도 라우팅 테이블, 백엔드 클러스터 엔드포인트, TLS 인증서를 실시간으로 무중단 갱신할 수 있습니다.
* **고급 L7 트래픽 제어**: HTTP/1.1, HTTP/2, HTTP/3(QUIC), gRPC를 완벽 지원하며, 가중치 기반 트래픽 분할(Canary), 타임아웃, 재시도(Retry), 서킷 브레이커(Circuit Breaking), 속도 제한(Rate Limiting) 등을 지원합니다.
* **강력한 관찰성(Observability)**: 풍부한 L7 메트릭 생성, 분산 추적(Distributed Tracing - Zipkin, Jaeger 등) 연동을 기본 내장합니다.

#### ③ GKE Gateway API와 Envoy의 관계
* GCP의 차세대 관리형 부하 분산기(`gke-l7-*-managed`)의 **핵심 구동 엔진(Data Plane)이 바로 Google에 의해 완전 관리되는 Envoy 프록시 풀**입니다.
* 사용자가 직접 복잡한 Envoy 설정 파일(`envoy.yaml`)을 작성하거나 Envoy 파드를 직접 배포·관리할 필요가 없습니다.
* 사용자는 표준 쿠버네티스 선언형 리소스인 **`Gateway`**와 **`HTTPRoute`**만 배포하면, **GKE Gateway Controller가 이를 자동으로 Google Cloud 인프라 레벨의 Envoy 프록시 설정으로 변환하여 실시간 적용**해 줍니다.

---

## 3. 매니페스트 구조 및 nip.io 원리 분석

본 실습에서는 별도의 공인 도메인을 구매하거나 DNS 레코드를 등록하지 않고도, 고유한 FQDN 주소로 호스트 라우팅을 검증하기 위해 **`nip.io` 와일드카드 DNS**를 적용합니다.

### 1) nip.io 와일드카드 DNS 동작 원리
`nip.io`는 `<어떤서브도메인>.<IP주소>.nip.io` 형식의 요청이 들어오면, 중간에 포함된 `<IP주소>`를 DNS 응답(A 레코드)으로 즉시 반환해 주는 무료 공개 DNS 서비스입니다.
* 예: `www.ssu-cloud-computing-gke.34.160.156.124.nip.io` ➔ DNS 질의 시 **`34.160.156.124`**로 자동 해석됨.
* 별도의 `/etc/hosts` 설정이나 유료 도메인 구매 없이 웹 브라우저 주소창에 바로 입력하여 테스트할 수 있습니다.

### 2) 핵심 매니페스트 구성

#### ① Gateway 매니페스트 ([`GKE-gateway-nip.yaml`](...//getting-started-todo-app(GKE)/GKE-gateway-nip.yaml))
인프라 관리 영역(`infra-team` 네임스페이스)에 GCP 글로벌 외부 L7 로드밸런서를 생성합니다.
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: infra-team
---
apiVersion: gateway.networking.k8s.io/v1
kind: Gateway
metadata:
  name: external-gateway
  namespace: infra-team
spec:
  gatewayClassName: gke-l7-global-external-managed
  listeners:
  - name: http
    protocol: HTTP
    port: 80
    allowedRoutes:
      namespaces:
        from: All       # default 등 타 네임스페이스의 HTTPRoute 연결 허용
```

#### ② HTTPRoute 매니페스트 ([`GKE-httproutes-nip.yaml`](...//getting-started-todo-app(GKE)/GKE-httproutes-nip.yaml))
애플리케이션 영역(`default` 네임스페이스)에서 `nip.io` 주소로 들어온 요청을 Todo 웹 애플리케이션 서비스(`app-service`) 및 API 테스트 서비스(`api-service`)로 연결합니다.
```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: web-app-route
  namespace: default
spec:
  parentRefs:
  - name: external-gateway
    namespace: infra-team
    sectionName: http # Gateway 리스너 이름 매핑
  hostnames:
  - "www.ssu-cloud-computing-gke.34.160.156.124.nip.io"
  - "app.ssu-cloud-computing-gke.34.160.156.124.nip.io"
  rules:
  - matches:
    - path:
        type: PathPrefix
        value: /
    backendRefs:
    - name: app-service         # 실제 Todo 웹 인터페이스(React + Express) 서비스 (10.104.0.15:3000)
      port: 80
---
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: api-route
  namespace: default
spec:
  parentRefs:
  - name: external-gateway
    namespace: infra-team
    sectionName: http # Gateway 리스너 이름 매핑
  hostnames:
  - "api.ssu-cloud-computing-gke.34.160.156.124.nip.io"
  rules:
  - matches:
    - path:
        type: PathPrefix
        value: /
    backendRefs:
    - name: api-service         # API 테스트용 서비스 (whereami)
      port: 80
```

#### ③ 백엔드 워크로드 매니페스트 ([`sample-workloads.yaml`](...//getting-started-todo-app(GKE)/sample-workloads.yaml))
Gateway 및 HTTPRoute가 전달한 트래픽을 최종 수신하는 백엔드 파드와 서비스(NEG 활성화)를 정의합니다.
* **`whereami` 배포(Deployment)**:
  * Google Cloud 공식 팀이 네트워크 라우팅 및 부하 분산 진단용으로 제공하는 **경량 진단용 컨테이너**(`google-samples/containers/gke/whereami`)입니다.
  * 요청을 받으면 자신이 실행 중인 파드 이름, GCP 존(Zone), 클러스터 이름, 요청 헤더 등을 JSON으로 반환하여 L7 라우팅 정상 여부를 즉각 검증할 수 있습니다.
* **본 프로젝트 `todo-backend`와의 연결 구조**:
  * 원본 구글 샘플에서는 `app-service`와 `api-service` 모두 `whereami` 컨테이너를 가리키게 되어 있었습니다.
  * 하지만 본 실습에서는 브라우저 접속 시 **실제 Todo 웹 애플리케이션 화면(React UI)**이 렌더링되도록 만들기 위해, `app-service`의 `selector`를 **`app: todo-backend` (포트 3000)**로 지정했습니다.
  * 즉, **`app-service`가 실제 Todo 파드를 GKE Gateway와 이어주는 핵심 다리(Bridge)** 역할을 수행합니다.
  * 반면 `api-service`는 멀티 호스트 분기 라우팅을 함께 증명하기 위해 `whereami` 진단 컨테이너를 그대로 활용합니다.

---

## 4. 핵심 질의응답 (FAQ)

### Q1. Gateway를 적용하기 전에 LoadBalancer 서비스(`GKE-service-lb.yaml`)를 먼저 적용해야 하나요?
> **답변: 전혀 필요 없으며, 적용하면 안 됩니다.**
* `Gateway`(`gke-l7-global-external-managed`) 자체가 GCP에 **독립적인 L7 글로벌 외부 로드밸런서**를 직접 프로비저닝하고 공인 IP를 할당받습니다.
* [`GKE-service-lb.yaml`](...//getting-started-todo-app(GKE)/GKE-service-lb.yaml)은 **별개의 L4 네트워크 부하 분산기**를 생성하므로, 둘 다 배포하면 게이트웨이와 상관없는 L4 로드밸런서가 하나 더 생성되어 **GCP 클라우드 비용이 중복 발생**합니다.

### Q2. Gateway를 적용하기 전에 반드시 NodePort 서비스를 먼저 적용해야 하나요?
> **답변: 반드시 NodePort일 필요는 없으며, ClusterIP여도 완벽하게 동작합니다.**
* GKE Gateway API는 컨테이너 네이티브 LB(NEG) 방식을 사용하므로 파드의 IP로 직접 패킷을 전송합니다.
* 따라서 서비스 타입이 `ClusterIP`이든 `NodePort`이든 상관없이 **`cloud.google.com/neg: '{"ingress": true}'`** 어노테이션이 붙어 있으면 정상 라우팅됩니다.

### Q3. sample-workloads.yaml은 무얼 테스트하며, whereami와 todo-backend는 어떤 관계인가요?
> **답변: Gateway API의 호스트 기반 멀티 라우팅을 테스트하기 위한 백엔드들이며, `app-service`가 우리 프로젝트의 `todo-backend`를 게이트웨이에 연결합니다.**

```text
[ 브라우저 요청 ]
       │
       ▼
[ GKE Gateway (34.160.156.124) ]
       │
       ├─ (Host: www...nip.io) ──> [ app-service ] ──(NEG)──> [ ★ todo-backend 파드 (포트 3000) ]
       │                                                         ➔ 실제 Todo App React 웹 UI 렌더링!
       │
       └─ (Host: api...nip.io) ──> [ api-service ] ──(NEG)──> [ whereami 파드 (포트 8080) ]
                                                                 ➔ JSON 진단 메타데이터 반환!
```

* **`whereami` Deployment**: Google의 공식 진단용 컨테이너로, 호출 시 요청을 처리한 파드 이름(`api-v1-...`)과 GCP 존 정보를 JSON으로 반환하여 라우팅이 정상 작동함을 증명합니다.
* **`todo-backend` 연계**: `sample-workloads.yaml`의 `app-service`는 `selector: { app: todo-backend }`, `targetPort: 3000`으로 설정되어 있어, 웹 브라우저로 `www...nip.io`에 접속하면 `whereami` 대신 **실제 Todo 백엔드 파드가 서빙하는 React HTML/CSS/JS 화면**이 정상 로딩됩니다.

---

## 5. [검증 완료] nip.io 기반 GCP Gateway 올바른 실습 배포 절차

실제 GKE 클러스터 상에서 최종 검증된 5단계 배포 절차입니다.

```
[1단계: Gateway API 활성화] ──➔ [2단계: Gateway 배포 & 공인 IP 획득]
                                                 │
                                                 ▼
[5단계: 최종 접속 검증]   ◀── [4단계: nip.io HTTPRoute 배포] ◀── [3단계: 백엔드 워크로드 & NEG 배포]
(브라우저 Todo App UI 확인)       (호스트 기반 라우팅 연결)               (Todo 파드와 Service 연결)
```

### 1단계: GKE 클러스터 Gateway API 활성화 (최초 1회)
클러스터에 Gateway API 컨트롤러가 활성화되어 있지 않다면 먼저 활성화합니다.
```bash
gcloud container clusters update my-gke-cluster --gateway-api=standard --zone=asia-northeast3-a

# GatewayClass 등록 확인
kubectl get gatewayclass
# NAME                             CONTROLLER                  ACCEPTED   AGE
# gke-l7-global-external-managed   networking.gke.io/gateway   True       ...
```

### 2단계: Gateway 배포 및 공인 IP 확보
인프라 전용 네임스페이스(`infra-team`)에 Gateway를 배포하고, GCP 로드밸런서의 외부 공인 IP를 확인합니다.
```bash
# 1. Gateway 매니페스트 적용
kubectl apply -f GKE-gateway-nip.yaml

# 2. 할당된 ADDRESS 공인 IP 확인 (약 1~2분 대기)
kubectl get gateway external-gateway -n infra-team --watch
# NAME               CLASS                            ADDRESS          PROGRAMMED   AGE
# external-gateway   gke-l7-global-external-managed   34.160.156.124   True         2m
```
> **확인된 공인 IP 예시**: `34.160.156.124`

### 3단계: 백엔드 워크로드 및 NEG 활성화 서비스 배포
Todo 애플리케이션 파드가 배포되어 있는지 확인하고, 파드와 연결되는 NEG 활성화 서비스를 배포합니다.
```bash
# 1. 백엔드 워크로드 및 서비스 배포
kubectl apply -f sample-workloads.yaml

# 2. 서비스 엔드포인트에 실제 Todo 백엔드 파드가 연결되었는지 확인
kubectl get endpoints app-service
# NAME          ENDPOINTS          AGE
# app-service   10.104.0.15:3000   ...
```

### 4단계: nip.io 기반 가상 호스트 HTTPRoute 배포
2단계에서 확보한 공인 IP(`34.160.156.124`)가 포함된 HTTPRoute 매니페스트를 적용합니다.
```bash
# HTTPRoute 배포 (웹앱 및 API 라우트 동시 배포)
kubectl apply -f GKE-httproutes-nip.yaml
```

### 5단계: 바인딩 상태 확인 및 접속 테스트
```bash
# 1. HTTPRoute 바인딩 상태 확인 (Accepted: True, ReconciliationSucceeded 확인)
kubectl describe httproute web-app-route -n default
kubectl describe httproute api-route -n default

# 2. DNS 자동 해석 확인
nslookup www.ssu-cloud-computing-gke.34.160.156.124.nip.io
# Address: 34.160.156.124 반환 확인

# 3. curl 을 통한 Todo 웹 인터페이스(HTML) 응답 검증
curl -i http://www.ssu-cloud-computing-gke.34.160.156.124.nip.io/

# 4. curl 을 통한 API 진단(JSON) 응답 검증 (whereami)
curl -i http://api.ssu-cloud-computing-gke.34.160.156.124.nip.io/
```

웹 브라우저를 열고 다음 URL에 접속하여 실제 서비스들이 정상 분기되는지 확인합니다:
* 🌐 **[http://www.ssu-cloud-computing-gke.34.160.156.124.nip.io/](http://www.ssu-cloud-computing-gke.34.160.156.124.nip.io/)** (실제 **Todo App React UI** 렌더링)
* 🌐 **[http://app.ssu-cloud-computing-gke.34.160.156.124.nip.io/](http://app.ssu-cloud-computing-gke.34.160.156.124.nip.io/)** (실제 **Todo App React UI** 렌더링)
* 🌐 **[http://api.ssu-cloud-computing-gke.34.160.156.124.nip.io/](http://api.ssu-cloud-computing-gke.34.160.156.124.nip.io/)** (진단용 **whereami JSON** 메타데이터 반환)

---

## 6. 트러블슈팅 및 실습 주의사항

### 1) 왜 웹 인터페이스 대신 JSON 응답이 나타났을까요?
* 초기 테스트에서 사용된 `whereami` 이미지는 네트워크 라우팅 디버깅을 위해 제작된 구글 공식 샘플 컨테이너로, 웹 UI가 없이 클러스터 및 파드 정보(`{"cluster_name":"...", "pod_name":"..."}`)만 반환합니다.
* 실제 Todo 웹 인터페이스(React + Express)를 서빙하려면 서비스의 `selector`를 `app: todo-backend`로 지정하고, 대상 포트를 Express 웹 서버 포트인 **`3000`**으로 연결해야 합니다.

### 2) 배포 직후 `fault filter abort` 또는 `404 Not Found`가 발생하는 이유
* Google Cloud의 글로벌 외부 애플리케이션 부하 분산기는 전 세계 수백 개의 엣지 프록시(GFE)로 URL 맵과 라우팅 정책을 전파합니다.
* 매니페스트가 성공적으로 적용되었더라도 전 세계 프록시에 완전히 동기화되기까지 **약 1~3분의 지연 시간(Propagation Delay)**이 소요되며, 동기화가 완료되면 정상적으로 `200 OK` 응답이 반환됩니다.

### 3) `www.ssu-cloud-computing-gke.com` 단독 사용 시 문제점
* 실제 도메인 등록 사이트에서 해당 도메인을 구매하고 DNS A 레코드를 로드밸런서 IP로 지정하지 않은 상태에서 `hostnames: [www.ssu-cloud-computing-gke.com]`만 사용하면, 일반 웹 브라우저나 외부 클라이언트에서는 IP를 찾지 못해 접속할 수 없습니다.
* 따라서 실습 환경에서는 반드시 **`www.ssu-cloud-computing-gke.<IP>.nip.io`** 형식으로 작성해야만 별도의 도메인 구매 없이도 정상적인 테스트가 가능합니다.

---

## 7. 실습정리 요약 (Command Cheatsheet)

본 실습의 핵심은 **별도의 유료 도메인 구매나 SSL/TLS 인증서 등록 없이도, `nip.io` 와일드카드 DNS와 GKE가 자동 프로비저닝하는 동적 외부 공인 IP(Dynamic External IP)를 결합**하여 실제 프로덕션 도메인 환경과 동일한 호스트 기반 L7 라우팅 및 웹 애플리케이션 서비스를 완벽하게 검증하는 것입니다. 전체 실습 절차를 실행 명령어 리스트로 요약합니다:

```bash
# 1. GKE 클러스터에 Gateway API 활성화 (클러스터당 1회)
gcloud container clusters update my-gke-cluster --gateway-api=standard --zone=asia-northeast3-a

# 2. Gateway API 클래스 등록 확인 (gke-l7-global-external-managed 확인)
kubectl get gatewayclass

# 3. Gateway 리소스 배포 (GCP L7 글로벌 외부 로드밸런서 생성)
kubectl apply -f GKE-gateway-nip.yaml

# 4. 프로비저닝된 동적 외부 공인 IP(ADDRESS) 확인 (<IP> 확보, 예: 34.160.156.124)
kubectl get gateway external-gateway -n infra-team --watch

# 5. 백엔드 워크로드 및 NEG 활성화 서비스 배포 (실제 Todo 웹 UI 파드와 연결)
kubectl apply -f sample-workloads.yaml
kubectl get endpoints app-service

# 6. nip.io 기반 HTTPRoute 매니페스트 배포
#    (매니페스트 내 hostnames 에 4단계에서 확보한 <IP> 가 적용되어 있는지 확인)
kubectl apply -f GKE-httproutes-nip.yaml

# 7. HTTPRoute 바인딩 및 라우팅 상태 확인 (Accepted: True 확인)
kubectl describe httproute web-app-route -n default

# 8. nip.io 도메인 이름 자동 해석 검증
nslookup www.ssu-cloud-computing-gke.34.160.156.124.nip.io

# 9. curl 을 통한 응답 검증 (엣지 전파 1~2분 후 수행)
curl -i http://www.ssu-cloud-computing-gke.34.160.156.124.nip.io/  # Todo 웹 UI (HTML)
curl -i http://api.ssu-cloud-computing-gke.34.160.156.124.nip.io/  # whereami 진단 API (JSON)

# 10. 웹 브라우저 최종 접속 확인
#     웹앱: http://www.ssu-cloud-computing-gke.34.160.156.124.nip.io/
#     API : http://api.ssu-cloud-computing-gke.34.160.156.124.nip.io/
```
