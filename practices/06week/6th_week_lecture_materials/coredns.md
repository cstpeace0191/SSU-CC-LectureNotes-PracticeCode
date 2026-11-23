# 쿠버네티스 DNS(CoreDNS) 동작 원리 및 이름 해석(Name Resolution) 가이드

## 1. 개요 및 문제 현상

호스트 OS(Windows/Git Bash 등)의 터미널에서 쿠버네티스 서비스의 FQDN(전체 주소)을 `nslookup` 질의할 경우 다음과 같이 에러가 발생합니다.

### 실행 명령어 및 에러 결과
```text
$ kubectl get svc
NAME             TYPE           CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE
db               ClusterIP      None            <none>        3306/TCP       46m
kubernetes       ClusterIP      10.96.0.1       <none>        443/TCP        3h32m
mysql            ClusterIP      10.96.198.68    <none>        3306/TCP       29m
web-lb-service   LoadBalancer   10.96.119.162   172.18.0.5    80:31149/TCP   86m

$ nslookup web-lb-service.default.svc.cluster.local
Server:  kns.kornet.net
Address:  168.126.63.1

*** kns.kornet.net can't find web-lb-service.default.svc.cluster.local: Non-existent domain
```

---

## 2. 원인 분석

### 호스트 OS vs 클러스터 내부 네트워크 격리
1. **쿠버네티스 사설 도메인**:
   - `web-lb-service.default.svc.cluster.local`과 같은 `.cluster.local` 도메인은 **쿠버네티스 내부(CoreDNS)에서만 유효한 사설 가상 도메인**입니다.
2. **호스트 DNS 질의**:
   - 로컬 윈도우(호스트 OS) 터미널에서 `nslookup`을 실행하면, 윈도우 네트워크 어댑터에 설정된 인터넷 통신사 DNS(예: KT `kns.kornet.net`, `168.126.63.1`)로 패킷이 전송됩니다.
   - 외부 공인 DNS 서버는 쿠버네티스 내부 클러스터 도메인을 알지 못하므로 `Non-existent domain`을 반환합니다.

---

## 3. 올바른 확인 및 질의 방법

쿠버네티스 내부 도메인은 **쿠버네티스 클러스터 내부(Pod 안)** 에서 CoreDNS(`kube-dns`) 서버(`10.96.0.10`)를 통해 질의해야 합니다.

### 방법 1: 임시 디버깅 Pod 생성하여 질의 (`dnsutils` or `busybox`)

일회성 Pod를 클러스터 내부에 띄워 DNS 조회를 수행합니다.

```bash
# dnsutils 이미지 사용 (완전한 FQDN 조회)
kubectl run -i --tty --rm debug-dns --image=tutum/dnsutils --restart=Never -- nslookup web-lb-service.default.svc.cluster.local
```

또는 짧은 서비스 이름으로 질의:
```bash
# busybox 이미지 사용 (동일 namespace 내 짧은 서비스명 조회)
kubectl run -i --tty --rm debug-dns --image=busybox:1.28 --restart=Never -- nslookup web-lb-service
```

#### 정상 응답 예시
```text
Server:    10.96.0.10   <-- 클러스터 내부 CoreDNS 서비스 IP (kube-dns)
Address 1: 10.96.0.10 kube-dns.kube-system.svc.cluster.local

Name:      web-lb-service.default.svc.cluster.local
Address 1: 10.96.119.162 web-lb-service.default.svc.cluster.local  <-- ClusterIP 반환 확인
```

---

### 방법 2: 이미 실행 중인 Pod 내부에서 질의

클러스터에 기동 중인 기존 Pod 내부로 진입하여 DNS를 조회합니다.

```bash
# 1. 실행 중인 Pod 이름 확인
kubectl get pods

# 2. 특정 Pod 내부에서 nslookup 실행
kubectl exec -it <POD_NAME> -- nslookup web-lb-service
```

---

## 4. 쿠버네티스 서비스 DNS 이름 규칙 (FQDN)

쿠버네티스에서 서비스가 생성되면 CoreDNS는 다음 규칙으로 도메인을 자동 등록합니다:

$$\text{<서비스명>}.\text{<네임스페이스>}.\text{svc}.\text{<클러스터도메인>}$$

- **동일 네임스페이스 내 Pod 간 통신**: 서비스 이름만으로 접근 가능 (`web-lb-service`)
- **다른 네임스페이스 간 통신**: 네임스페이스까지 명시 (`web-lb-service.<namespace>`)
- **전체 정규화 도메인(FQDN)**: `web-lb-service.default.svc.cluster.local`

---

## 5. 호스트 OS(윈도우)에서 서비스에 접근하는 방법

호스트 머신은 내부 CoreDNS를 직접 바라보지 않으므로, 다음 방법 중 하나로 접근해야 합니다.

1. **포트포워딩(Port-Forward) - 권장 디버깅 방식**:
   ```bash
   kubectl port-forward svc/web-lb-service 8080:80
   ```
   - 브라우저 또는 로컬 터미널에서 `http://localhost:8080`으로 접근합니다.

2. **LoadBalancer External-IP 접근 (MetalLB 연동 환경)**:
   - `web-lb-service`의 EXTERNAL-IP가 `172.18.0.5`로 할당되어 있으므로, KinD 도커 브릿지 네트워크 라우팅이 되어 있는 경우 직접 접근 가능:
   ```bash
   curl http://172.18.0.5
   ```

