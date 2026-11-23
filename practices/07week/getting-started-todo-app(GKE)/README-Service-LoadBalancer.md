# 쿠버네티스 서비스와 GKE LoadBalancer 동작 원리

이 문서는 쿠버네티스 서비스(Service)의 기본 개념과 유형(ClusterIP, NodePort, LoadBalancer)을 비교하고, [`GKE-service-lb.yaml`](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/07week/getting-started-todo-app(GKE)/GKE-service-lb.yaml) 매니페스트를 적용했을 때 GKE가 클라우드 로드밸런서 및 `EXTERNAL-IP`를 프로비저닝하고 할당하는 구체적인 과정을 설명합니다.

---

## 1. 쿠버네티스 서비스(Service)란?

쿠버네티스의 파드(Pod)는 생성과 소멸이 빈번하게 일어나는 **일회성(Ephemeral) 자원**입니다. 파드가 재시작되거나 롤링 업데이트될 때마다 내부 IP 주소가 변경되므로, 파드의 IP로 직접 통신하는 것은 불가능합니다.

**서비스(Service)**는 이러한 문제를 해결하기 위해 도입된 추상화 계층입니다.
* **고정 엔드포인트 제공**: 파드가 교체되어도 변하지 않는 단일 진입점(가상 IP 및 내부 DNS 이름)을 제공합니다.
* **서비스 디스커버리 및 부하 분산**: `spec.selector`로 지정된 레이블(예: `app: todo-backend`)과 일치하는 파드들을 자동으로 추적(EndpointSlice)하여 트래픽을 균등하게 로드밸런싱합니다.

---

## 2. 쿠버네티스 서비스 유형 비교

쿠버네티스 서비스는 노출 범위와 방식에 따라 다음과 같이 계층적으로 구성됩니다.

```
+-----------------------------------------------------------+
|                      LoadBalancer                         |  <-- 외부 클라우드 LB (공인 IP)
|  +-----------------------------------------------------+  |
|  |                     NodePort                        |  |  <-- 모든 노드의 물리 포트 (30000~32767)
|  |  +-----------------------------------------------+  |  |
|  |  |                 ClusterIP                     |  |  |  <-- 클러스터 내부 가상 IP
|  |  |  +---------+   +---------+   +---------+      |  |  |
|  |  |  |  Pod 1  |   |  Pod 2  |   |  Pod 3  |      |  |  |
|  |  |  +---------+   +---------+   +---------+      |  |  |
|  |  +-----------------------------------------------+  |  |
|  +-----------------------------------------------------+  |
+-----------------------------------------------------------+
```

### 1) ClusterIP (기본값)
* **특징**: 클러스터 내부 네트워크에서만 접근 가능한 가상 IP를 할당받습니다.
* **용도**: 데이터베이스, 내부 캐시, 백엔드 마이크로서비스 등 클러스터 외부로 노출될 필요가 없는 서비스 간 통신에 사용됩니다.
* **외부 접근**: 클러스터 외부에서는 기본적으로 직접 접근할 수 없습니다.

### 2) NodePort
* **특징**: `ClusterIP`를 기본 생성한 뒤, 클러스터의 모든 워커 노드(Node)에 동일한 고유 포트(기본 범위: `30000~32767`)를 개방합니다.
* **접근 방식**: `<노드_공인또는내부_IP>:<NodePort>` 형태로 요청을 보내면 해당 노드의 `kube-proxy`가 내부 `ClusterIP` 및 파드로 트래픽을 라우팅합니다.
* **한계**: 노드 IP가 변경될 수 있고, 포트 번호가 비표준(30000번대)이며, 노드 앞단에 별도의 로드밸런서를 직접 관리해야 하는 번거로움이 있습니다.

### 3) LoadBalancer
* **특징**: `NodePort`와 `ClusterIP`를 바탕으로, 클라우드 제공업체(GCP, AWS, Azure 등)의 **외부 로드밸런서(External Load Balancer)**를 자동으로 생성하고 연동합니다.
* **접근 방식**: 클라우드 공급자가 할당한 공인 고유 IP(`EXTERNAL-IP`)의 표준 포트(80, 443 등)로 직접 접근할 수 있습니다.
* **용도**: 인터넷에서 사용자가 직접 접속해야 하는 웹 서비스, 공개 API 서버 등에 사용됩니다.

---

## 3. `GKE-service-lb.yaml` 적용 시 GKE의 EXTERNAL-IP 할당 과정

사용자가 다음 명령어를 실행하면:
```bash
kubectl apply -f GKE-service-lb.yaml
```

GKE와 Google Cloud(GCP) 인프라는 백그라운드에서 아래의 단계로 **EXTERNAL-IP**를 프로비저닝하고 할당합니다.

```
[1. kubectl apply]
       │
       ▼
[2. k8s API Server] (Service 리소스 등록: type=LoadBalancer)
       │
       ▼
[3. GKE Cloud Controller Manager (CCM)] (신규 LB 서비스 감지)
       │
       ▼ (GCP Compute Engine API 호출)
[4. Google Cloud Networking 인프라 생성]
       ├─ 외부 공인 IP (External IPv4) 자동 예약/할당
       ├─ 전달 규칙 (Forwarding Rule: 0.0.0.0/0:80 -> Target Pool / Backend Service)
       ├─ 백엔드 대상 (GKE 노드 인스턴스 풀 / NEG 등록)
       ├─ 상태 확인 (Health Check 생성)
       └─ GCP 방화벽 규칙 (Firewall Rule 생성: 외부 트래픽 허용)
       │
       ▼ (프로비저닝 완료 및 할당된 IP 반환)
[5. Service status 업데이트]
       status.loadBalancer.ingress[0].ip = <GCP_공인_IP>
       │
       ▼
[6. 사용자 확인 (EXTERNAL-IP 표시)]
       kubectl get svc todo-backend-lb
       NAME               TYPE           CLUSTER-IP     EXTERNAL-IP      PORT(S)
       todo-backend-lb    LoadBalancer   10.96.12.34    34.120.xxx.xxx   80:3xxxx/TCP
```

### 상세 단계 설명

1. **서비스 스펙 등록**:
   * 쿠버네티스 API Server가 `type: LoadBalancer`, `port: 80`, `targetPort: 3000` 설정이 담긴 매니페스트를 저장합니다.
   * 이 시점에서는 외부 IP가 아직 없으므로 `kubectl get svc` 시 `EXTERNAL-IP: <pending>` 상태로 표시됩니다.

2. **GKE Cloud Controller Manager(CCM)의 감지**:
   * GKE 컨트롤 플레인 내부의 클라우드 컨트롤러 매니저가 신규 `LoadBalancer` 타입 서비스를 감지하고, 연동된 GCP 프로젝트의 Compute Engine API를 호출합니다.

3. **GCP L4 외부 패스스루 네트워크 부하 분산기 프로비저닝**:
   * **외부 정적/동적 IP 할당**: Google Cloud의 글로벌/리전 IP 풀에서 고유한 공인 IPv4 주소를 1개 할당합니다.
   * **전달 규칙(Forwarding Rule)**: 할당된 공인 IP의 80번 포트(TCP)로 들어오는 패킷을 백엔드로 넘겨주는 포워딩 룰을 생성합니다.
   * **상태 확인(Health Check)**: 노드/파드의 생존 여부를 모니터링하는 GCP Health Check를 구성합니다.
   * **VPC 방화벽 자동 구성**: 외부 클라이언트가 해당 포트로 접근할 수 있도록 GCP VPC 방화벽에 허용 규칙을 자동 등록합니다.

4. **Service 상태(status) 업데이트 및 완료**:
   * 로드밸런서 구축이 완료되면 컨트롤러는 할당받은 공인 IP를 쿠버네티스 Service 객체의 `.status.loadBalancer.ingress[0].ip` 필드에 기록합니다.
   * `kubectl get svc --watch`로 모니터링하던 사용자는 `<pending>`이 실제 공인 IP(예: `34.120.xxx.xxx`)로 변경되는 것을 확인하고 `http://<EXTERNAL-IP>/`로 접속할 수 있게 됩니다.

---

## 4. `GKE-service-lb.yaml`의 핵심 설정: `externalTrafficPolicy: Local`

[`GKE-service-lb.yaml`](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/07week/getting-started-todo-app(GKE)/GKE-service-lb.yaml) 18번 라인에 선언된 `externalTrafficPolicy: Local`의 의미와 동작 차이입니다.

| 항목 | `Cluster` (기본값) | `Local` (GKE 권장 설정) |
| :--- | :--- | :--- |
| **트래픽 전달 방식** | 로드밸런서가 아무 노드로 트래픽을 보내면, 해당 노드에 파드가 없더라도 노드 간 내부 통신(2차 홉)을 통해 파드가 있는 노드로 전달 | 로드밸런서가 **실제 해당 파드가 실행 중인 노드로만** 트래픽을 직접 전달 |
| **클라이언트 원본 IP** | 노드 간 프록시 과정(SNAT)으로 인해 **클라이언트 실제 IP가 손실**되고 노드 IP로 변경됨 | SNAT이 발생하지 않아 **클라이언트의 실제 공인 IP가 보존**됨 (로그 분석, 보안 감사에 필수) |
| **네트워크 홉(Hop)** | 노드 간 불필요한 2차 네트워크 홉이 발생할 수 있음 | 2차 홉이 없어 **네트워크 지연 시간(Latency) 감소** |
| **헬스체크 동작** | 모든 워커 노드가 정상으로 응답 | **대상 파드가 떠 있는 노드만 헬스체크를 통과**하고, 파드가 없는 노드는 로드밸런서 분산 대상에서 자동 제외 |

---

## 5. 자주 묻는 질문: LoadBalancer 적용 전 ClusterIP / NodePort를 먼저 배포해야 하는가?

> **결론: 전혀 먼저 적용할 필요가 없습니다.**  
> [`GKE-service-lb.yaml`](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/07week/getting-started-todo-app(GKE)/GKE-service-lb.yaml) 단독으로 바로 배포(`kubectl apply`)하시면 정상 동작합니다.

### 1) 왜 먼저 적용할 필요가 없을까요?
* **완전히 독립된 쿠버네티스 리소스 객체**:
  * [`GKE-service-cip.yaml`](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/07week/getting-started-todo-app(GKE)/GKE-service-cip.yaml) ➔ `metadata.name: todo-backend-cip`
  * [`GKE-service-np.yaml`](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/07week/getting-started-todo-app(GKE)/GKE-service-np.yaml) ➔ `metadata.name: todo-backend-np`
  * [`GKE-service-lb.yaml`](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/07week/getting-started-todo-app(GKE)/GKE-service-lb.yaml) ➔ `metadata.name: todo-backend-lb`
  위 세 파일은 서로 의존하는 관계가 아니라, **동일한 백엔드 파드를 다양한 방식(내부 전용, 노드 포트, 외부 로드밸런서)으로 노출하기 위해 각각 작성된 독립적인 실습 파일**입니다.

* **"LoadBalancer는 ClusterIP와 NodePort를 포함한다"는 개념의 의미**:
  * 이는 별도의 Service 파일을 먼저 만들어야 한다는 뜻이 아닙니다.
  * **`GKE-service-lb.yaml` 단 하나의 서비스 안에서** 쿠버네티스가 내부적으로:
    1. 가상 클러스터 IP(`ClusterIP`)를 자동 부여하고,
    2. 워커 노드들의 포트(`NodePort`)를 자동으로 개방한 뒤,
    3. 그 앞단에 GCP 외부 로드밸런서(`EXTERNAL-IP`)를 연결한다는 뜻입니다.
  * 따라서 `GKE-service-lb.yaml` 하나만 실행해도 필요한 하위 네트워크 계층이 모두 자동 생성됩니다.

### 2) 세 파일을 모두 apply하면 어떻게 되나요?
세 파일을 모두 실행해도 충돌이나 오류가 발생하지 않습니다. 동일한 파드 레이블(`app: todo-backend`)을 대상으로 서로 다른 3개의 진입로(Doorway)가 동시에 열리게 됩니다.

```bash
$ kubectl get svc
NAME                TYPE           CLUSTER-IP     EXTERNAL-IP      PORT(S)
todo-backend-cip    ClusterIP      10.96.10.11    <none>           80/TCP
todo-backend-np     NodePort       10.96.20.22    <none>           80:30080/TCP
todo-backend-lb     LoadBalancer   10.96.30.33    34.120.xxx.xxx   80:3xxxx/TCP
```

---

## 6. 실습 명령어 가이드

```bash
# 1. 로드밸런서 서비스 배포
kubectl apply -f GKE-service-lb.yaml

# 2. EXTERNAL-IP 할당 실시간 모니터링 (<pending> -> 공인 IP)
kubectl get svc todo-backend-lb --watch

# 3. 서비스 세부 정보 및 GCP 로드밸런서 연동 확인
kubectl describe svc todo-backend-lb

# 4. 외부 브라우저 또는 curl 로 접속 테스트
curl http://<EXTERNAL-IP>/
```

