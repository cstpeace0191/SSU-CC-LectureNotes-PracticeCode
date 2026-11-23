# kube-prometheus-stack

[kube-prometheus stack](https://github.com/prometheus-operator/kube-prometheus)의 핵심 컴포넌트를 설치합니다. 이는 [Prometheus Operator](https://github.com/prometheus-operator/prometheus-operator)를 사용하여 [Prometheus](https://prometheus.io/) 기반의 운영이 간편한 엔드투엔드 쿠버네티스 클러스터 모니터링 환경을 제공하기 위해 쿠버네티스 매니페스트, [Grafana](http://grafana.com/) 대시보드, [Prometheus 규칙(rules)](https://prometheus.io/docs/prometheus/latest/configuration/recording_rules/)을 문서 및 스크립트와 함께 결합한 모음집입니다.

컴포넌트, 대시보드 및 알림에 대한 자세한 내용은 [kube-prometheus](https://github.com/prometheus-operator/kube-prometheus) 리드미(readme)를 참조하세요.

_참고: 이 차트의 이전 이름은 `prometheus-operator` 차트였으나, Prometheus Operator가 단지 하나의 컴포넌트로 포함된 `kube-prometheus` 프로젝트 스택을 설치한다는 점을 더 명확히 나타내기 위해 이름이 변경되었습니다. 이 차트는 `kube-prometheus`의 모든 컴포넌트를 설치하지는 않으며, 특히 Prometheus Adapter와 Prometheus black-box exporter는 제외되어 있습니다._

## 사전 요구사항 (Prerequisites)

- Kubernetes 1.19+
- Helm 3+

## 사용법 (Usage)

이 차트는 [OCI 아티팩트(Artifact)](https://helm.sh/docs/topics/registries/) 및 전통적인 [Helm 리포지토리(Repository)](https://helm.sh/docs/topics/chart_repository/)를 통해 배포됩니다.

- OCI 아티팩트: `oci://ghcr.io/prometheus-community/charts/kube-prometheus-stack`
- Helm 리포지토리: `kube-prometheus-stack` 차트가 포함된 `https://prometheus-community.github.io/helm-charts`

설치 안내는 OCI 레지스트리를 기준으로 설명합니다. 전통적인 리포지토리를 통한 차트 설치에 대한 정보는 [`helm repo`](https://helm.sh/docs/helm/helm_repo/) 명령어 문서를 참조하세요.

### Helm 차트 설치

```console
helm install [RELEASE_NAME] oci://ghcr.io/prometheus-community/charts/kube-prometheus-stack
```

_아래의 [설정](#설정-configuration)을 참조하세요._

_명령어에 대한 자세한 내용은 [helm install](https://helm.sh/docs/helm/helm_install/) 문서를 참조하세요._

### 의존성 (Dependencies)

기본적으로 이 차트는 다음과 같은 추가 종속성 차트들을 함께 설치합니다:

- [prometheus-community/kube-state-metrics](https://github.com/prometheus-community/helm-charts/tree/main/charts/kube-state-metrics)
- [prometheus-community/prometheus-node-exporter](https://github.com/prometheus-community/helm-charts/tree/main/charts/prometheus-node-exporter)
- [grafana/grafana](https://github.com/grafana/helm-charts/tree/main/charts/grafana)

설치 시 이러한 의존성을 비활성화하려면 아래의 [다중 릴리스](#다중-릴리스-multiple-releases) 섹션을 참조하세요.

_명령어 문서는 [helm dependency](https://helm.sh/docs/helm/helm_dependency/)를 참조하세요._

#### Grafana 대시보드

이 차트는 ConfigMap을 통해 Grafana에 자동으로 로드되는 선별된 Grafana 대시보드 모음을 프로비저닝합니다. 이러한 대시보드들은 Helm 차트의 [`templates/grafana/`](https://github.com/prometheus-community/helm-charts/tree/main/charts/kube-prometheus-stack/templates/grafana/) 아래에 렌더링되지만, **이곳이 원본 소스(source of truth)는 아닙니다**.

대시보드들은 다양한 업스트림 프로젝트에서 유래되었으며, [`hack/`](https://github.com/prometheus-community/helm-charts/tree/main/charts/kube-prometheus-stack/hack) 디렉터리에 있는 스크립트를 사용하여 수집 및 처리됩니다. 대시보드가 수집되고 최신 상태로 유지되는 방식에 대한 자세한 내용은 [hack/README.md](https://github.com/prometheus-community/helm-charts/blob/main/charts/kube-prometheus-stack/hack/README.md)를 참조하세요.

> **참고:** `hack` 스크립트에서 참조하는 대시보드 역시 대개 **최초 원본 소스가 아닙니다**. 대부분은 별도의 **Prometheus 믹스인(mixin) 저장소**(예: [kubernetes-mixin](https://github.com/kubernetes-monitoring/kubernetes-mixin))에서 비롯되며, 여기에 포함되기 전에 `jsonnet` 도구를 통해 처리됩니다. 대시보드를 수정하기 위해 원본 소스를 찾으려면 업스트림을 더 추적해야 할 수 있습니다.

대시보드에 기여하거나 수정하려는 경우 일관성과 재현성을 보장하기 위해 `hack/README.md`의 안내를 따라주세요.

### Helm 차트 삭제 (Uninstall)

```console
helm uninstall [RELEASE_NAME]
```

이 명령은 차트와 관련된 모든 쿠버네티스 컴포넌트를 제거하고 릴리스를 삭제합니다.

_명령어 문서는 [helm uninstall](https://helm.sh/docs/helm/helm_uninstall/)을 참조하세요._

이 차트에 의해 생성된 CRD는 기본적으로 삭제되지 않으므로 수동으로 정리해야 합니다:

```console
kubectl delete crd alertmanagerconfigs.monitoring.coreos.com
kubectl delete crd alertmanagers.monitoring.coreos.com
kubectl delete crd podmonitors.monitoring.coreos.com
kubectl delete crd probes.monitoring.coreos.com
kubectl delete crd prometheusagents.monitoring.coreos.com
kubectl delete crd prometheuses.monitoring.coreos.com
kubectl delete crd prometheusrules.monitoring.coreos.com
kubectl delete crd scrapeconfigs.monitoring.coreos.com
kubectl delete crd servicemonitors.monitoring.coreos.com
kubectl delete crd thanosrulers.monitoring.coreos.com
```

### 차트 업그레이드 (Upgrading Chart)

```console
helm upgrade [RELEASE_NAME] [CHART]
```

Helm v3에서는 이 차트에 의해 생성된 CRD가 기본적으로 업데이트되지 않으므로 수동으로 업데이트해야 합니다.
[CRD에 관한 Helm 문서](https://helm.sh/docs/chart_best_practices/custom_resource_definitions)도 참조하세요.

CRD 업데이트는 메이저 버전 업데이트로 이어집니다.
차트의 [appVersion](https://github.com/prometheus-community/helm-charts/blob/13ed7098db2f78c2bbcdab6c1c3c7a95b4b94574/charts/kube-prometheus-stack/Chart.yaml#L36)은 일치하는 CRD를 가진 [`prometheus-operator`](https://github.com/prometheus-operator/prometheus-operator/tree/main)의 버전을 참조합니다.

_명령어 문서는 [helm upgrade](https://helm.sh/docs/helm/helm_upgrade/)를 참조하세요._

#### 기존 릴리스를 새 메이저 버전으로 업그레이드

메이저 차트 버전 변경(예: v1.2.3 -> v2.0.0)은 수동 조치가 필요한 호환되지 않는 변경 사항(Breaking Change)이 있음을 의미합니다.

버전 간 주요 변경 사항은 [UPGRADE.md](https://github.com/prometheus-community/helm-charts/blob/main/charts/kube-prometheus-stack/UPGRADE.md)를 참조하세요.

## 설정 (Configuration)

[설치 전 차트 사용자 정의(Customizing the Chart Before Installing)](https://helm.sh/docs/intro/using_helm/#customizing-the-chart-before-installing)를 참조하세요. 상세한 주석과 함께 구성 가능한 모든 옵션을 확인하려면 다음 명령을 실행합니다:

```console
helm show values oci://ghcr.io/prometheus-community/charts/kube-prometheus-stack
```

추가 옵션을 확인하기 위해 이 차트의 [종속성](#의존성-dependencies)에 대해서도 `helm show values`를 실행할 수 있습니다.

템플릿화된 Grafana 데이터 소스 정의(예: Helm 흐름 제어 사용 시)의 경우 `tpl`을 통해 렌더링되는 `grafana.additionalDataSourcesString`을 사용하세요.

### HTTPRoute 타임아웃

라우트에 `timeouts`를 설정하여 생성된 HTTPRoute 규칙에 대한 요청(request) 및 백엔드 요청(backend request) 타임아웃을 구성할 수 있습니다:

```yaml
prometheus:
  route:
    main:
      enabled: true
      parentRefs:
        - name: gateway
      timeouts:
        request: 120s
        backendRequest: 60s
```

동일한 설정이 `alertmanager.route`, `thanosRuler.route`, 그리고 Prometheus 및 Alertmanager의 `routePerReplica` 설정에서도 사용 가능합니다.

타임아웃은 `kind: HTTPRoute`에 대해서만 렌더링됩니다. 생성된 HTTPS 리디렉션 규칙에는 적용되지 않으며 `additionalRules`로 전파되지 않습니다. 필요한 경우 추가 규칙에 직접 타임아웃을 구성하세요. `timeouts`를 비워 두면 Gateway 컨트롤러의 기본값이 유지됩니다.

이를 사용하려면 HTTPRoute 타임아웃을 지원하는 Gateway API CRD(v1.2.0부터 표준 채널에서 제공됨)와 해당 타임아웃 기능을 지원하는 Gateway 컨트롤러가 필요합니다. 두 값을 모두 설정할 때 `request`가 `"0s"`가 아닌 이상 `backendRequest`는 `request`를 초과할 수 없습니다. 시간 지속성 의미 체계 및 컨트롤러 지원 요구 사항은 [Gateway API 타임아웃 문서](https://gateway-api.sigs.k8s.io/reference/api-types/httproute/#timeouts-optional)를 참조하세요.

### 컨트롤 플레인 ServiceMonitor 인증

kubelet, kube-apiserver, kube-controller-manager, kube-scheduler, kube-etcd, kube-proxy, coredns 및 kube-dns를 위한 기본 제공 ServiceMonitor는 스크레이퍼의 파일시스템에 있는 파일 대신 쿠버네티스 객체를 통해 인증합니다. 베어러 토큰(bearer token)은 `authorization`에서 참조하는 Secret에서 가져오며, CA는 쿠버네티스가 모든 네임스페이스에서 유지 관리하는 `kube-root-ca.crt` ConfigMap에서 가져옵니다. 이를 통해 `prometheus.prometheusSpec.arbitraryFSAccessThroughSMs.deny`가 `true`일 때나, v1.19.0부터 기본적으로 파일시스템 참조를 거부하는 Grafana Alloy의 `prometheus.operator.servicemonitors` 컴포넌트가 스크레이프할 때도 ServiceMonitor가 유효하게 유지됩니다.

차트 자체에서 자격 증명을 생성합니다: `prometheus.serviceAccount.createTokenSecret`(기본 활성화됨)은 `<prometheus service account>-token`이라는 이름의 `kubernetes.io/service-account-token` Secret을 렌더링하며, 모든 컴포넌트가 기본적으로 이를 참조합니다:

```yaml
kubelet:
  serviceMonitor:
    authorization:
      type: Bearer
      credentials:
        name: '{{ include "kube-prometheus-stack.prometheus.tokenSecretName" . }}'
        key: token
    tlsConfig:
      insecureSkipVerify: true
      ca:
        configMap:
          name: kube-root-ca.crt
          key: ca.crt
```

`authorization`과 `tlsConfig`는 모두 있는 그대로 렌더링되므로, Prometheus Operator의 [SafeAuthorization](https://github.com/prometheus-operator/prometheus-operator/blob/main/Documentation/api-reference/api.md#monitoring.coreos.com/v1.SafeAuthorization) 및 [SafeTLSConfig](https://github.com/prometheus-operator/prometheus-operator/blob/main/Documentation/api-reference/api.md#monitoring.coreos.com/v1.SafeTLSConfig) 타입의 모든 필드를 설정할 수 있습니다. 인증 없이 컴포넌트를 스크레이프하려면 `authorization`을 `null`로 설정하세요. `kubeApiServer`는 TLS 설정을 `kubeApiServer.tlsConfig` 아래에 유지합니다. `coreDns`와 `kubeDns`는 해당 엔드포인트가 HTTP를 통해 스크레이프되므로 `tlsConfig`가 없습니다.

해당 Secret은 Prometheus 서비스 계정과 함께만 렌더링되므로 `prometheus.enabled` 및 `prometheus.serviceAccount.create`도 필요합니다. Secret이 렌더링되지 않은 상태에서 컴포넌트를 기본 `authorization` 설정으로 두면 절대 존재하지 않을 Secret을 참조하는 ServiceMonitor가 생성되는 대신 설명 메시지와 함께 릴리스가 실패합니다. 컨트롤 플레인이 이 차트에서 배포하지 않는 외부 Prometheus에 의해 스크레이프될 때는 활성화된 각 컴포넌트가 스크레이퍼 자체 자격 증명을 가리키도록 설정하세요. `ci/08-external-scraper-values.yaml`에서 완전한 예제를 확인할 수 있습니다.

자체 자격 증명을 사용하려면 `prometheus.serviceAccount.createTokenSecret`을 비활성화하고 컴포넌트가 사용자 지정 Secret을 가리키도록 설정하세요. 해당 Secret은 ServiceMonitor와 동일한 네임스페이스에 있어야 하며, 이는 `prometheus.prometheusSpec.ignoreNamespaceSelectors`가 활성화되지 않은 한 릴리스 네임스페이스입니다. Helm은 값을 딥 머지(deep-merge)하므로 CA 참조를 대체하려면 기본값을 명시적으로 지워야 합니다:

```yaml
kubelet:
  serviceMonitor:
    tlsConfig:
      ca:
        configMap: null
        secret:
          name: kubelet-scrape-auth
          key: ca.crt
```

`kubeEtcd`는 클라이언트 인증서를 사용하여 스크레이프하는 유일한 컴포넌트입니다:

```yaml
kubeEtcd:
  serviceMonitor:
    scheme: https
    tlsConfig:
      insecureSkipVerify: false
      ca:
        secret:
          name: etcd-client-cert
          key: etcd-ca
      cert:
        secret:
          name: etcd-client-cert
          key: etcd-client
      keySecret:
        name: etcd-client-cert
        key: etcd-client-key
```

### 프로메테우스 고가용성 (Prometheus High Availability, HA)

기본적인 HA 구성을 위해 여러 개의 Prometheus 복제본(replica)을 실행합니다:

```yaml
prometheus:
  prometheusSpec:
    replicas: 2
    podAntiAffinity: "hard"
    externalLabels:
      cluster: prod-eu1
```

중요 참고 사항:

1. `replicas`는 각 샤드에 배포되는 Prometheus 파드 수를 제어합니다.
2. 모든 복제본이 단일 노드에 스케줄링되지 않도록 anti-affinity를 활성화(또는 hard로 설정) 상태로 유지하세요.
3. HA 설정에서는 복제본/인스턴스 외부 라벨(`replicaExternalLabelNameClear` / `prometheusExternalLabelNameClear`)을 삭제하지 마세요. 그렇지 않으면 중복 제거 및 알림/소스 식별이 어려워집니다.
4. 쿠버네티스 서비스를 통해 복제본을 쿼리하면 가용성은 확보되지만, 그 자체로 복제본 간의 샘플 중복 제거가 제공되지는 않습니다. 글로벌/중복 제거 쿼리를 위해서는 Thanos Query 계층(또는 중복 제거를 수행하는 다른 백엔드)을 사용하세요.

Prometheus Operator HA 지침도 참조하세요:

- [Prometheus Operator HA 문서](https://github.com/prometheus-operator/prometheus-operator/blob/main/Documentation/platform/high-availability.md#prometheus)

### 다중 릴리스 (Multiple releases)

필요한 경우 동일한 클러스터 내에서 여러 Prometheus 인스턴스를 실행하는 데 동일한 차트를 사용할 수 있습니다. 이를 달성하려면 prometheus-operator 인스턴스 하나와 HA 구성을 위한 alertmanager 파드 쌍만 실행하고, 다른 모든 컴포넌트는 비활성화해야 합니다. 설치 중 의존성을 비활성화하려면 `kubeStateMetrics.enabled`, `nodeExporter.enabled`, `grafana.enabled`를 `false`로 설정하세요.

## 알려진 문제에 대한 해결 방법 (Work-Arounds for Known Issues)

### 프라이빗 GKE 클러스터에서 실행하기

Google이 프라이빗 클러스터의 컨트롤 플레인을 구성할 때, 쿠버네티스 클러스터 네트워크와 별도의 Google 관리 프로젝트 간에 VPC 피어링을 자동으로 구성합니다. Google이 클러스터 내에서 액세스할 수 있는 대상을 제한하기 위해 설정된 방화벽 규칙은 쿠버네티스 파드에 대한 액세스를 제한합니다. 즉, GKE 프라이빗 클러스터에서 웹훅 컴포넌트를 사용하려면 GKE 컨트롤 플레인이 웹훅 파드에 액세스할 수 있도록 허용하는 추가 방화벽 규칙을 구성해야 합니다.

GKE 컨트롤 플레인 노드에 대한 방화벽 규칙을 추가하는 방법에 대한 자세한 내용은 [GKE 문서](https://cloud.google.com/kubernetes-engine/docs/how-to/private-clusters#add_firewall_rules)에서 확인할 수 있습니다.

또는 `prometheusOperator.admissionWebhooks.enabled=false`를 설정하여 훅을 비활성화할 수도 있습니다.

### Argo CD

오퍼레이터 CRD의 크기는 `kubectl.kubernetes.io/last-applied-configuration` 어노테이션의 262,144바이트 한도를 초과합니다(`crd-prometheuses.yaml` 단독으로도 약 840KiB에 달함). 따라서 클라이언트 측 apply를 수행하면 `metadata.annotations: Too long` 오류로 실패합니다. 애플리케이션을 `ServerSideApply=true`로 동기화하세요.

## PrometheusRules 어드미션 웹훅 (Admission Webhooks)

Prometheus Operator 버전 0.30 이상에서는 핵심 Prometheus Operator 파드가 잘못된 형식의 규칙이 클러스터에 추가되는 것을 방지하기 위해 쿠버네티스의 `validatingwebhookconfiguration` 기능과 통합되는 엔드포인트를 노출합니다.

### 차트가 웹훅을 구성하는 방식

Validating 및 Mutating 웹훅 구성은 요청이 전송되는 엔드포인트에서 TLS를 사용해야 합니다. 이를 위해 사용자 정의 인증서를 설정할 수도 있지만, 대부분의 경우 자체 서명 인증서(Self-signed certificate)로 충분합니다. Helm을 사용할 때 이 컴포넌트의 설정에는 다소 복잡한 오케스트레이션이 필요합니다. 각 단계는 멱등성을 유지하며 Helm의 예기치 않은 동작을 겪지 않고 기능을 켜고 끌 수 있도록 구성되었습니다.

1. 사전 설치 훅(pre-install hook)이 최종 사용자 인증서를 사용하는 프로비저닝과 호환되는 형식을 사용하여 동일한 네임스페이스에 인증서를 프로비저닝합니다. 인증서가 이미 존재하는 경우 훅은 종료됩니다.
2. Prometheus Operator 파드는 해당 인증서를 로드하는 TLS 프록시 컨테이너를 사용하도록 구성됩니다.
3. 클러스터에 Validating 및 Mutating 웹훅 구성이 생성되며, 장애 모드(failure mode)는 Ignore로 설정됩니다. 이를 통해 웹훅이 아직 완전히 설정되지 않았더라도(올바른 CA 필드가 설정되지 않음) 동일한 차트에 의해 규칙이 동시에 생성될 수 있습니다.
4. 사후 설치 훅(post-install hook)이 1단계에서 생성된 시크릿에서 CA를 읽어 Validating 및 Mutating 웹훅 구성을 패치합니다. 이 프로세스를 통해 다른 프로세스에서 프로비저닝된 사용자 지정 CA도 웹훅 구성에 패치될 수 있습니다. 선택한 장애 정책(failure policy) 또한 웹훅 구성에 패치됩니다.

### 대안 (Alternatives)

보다 완전한 솔루션이 필요한 경우 [jetstack/cert-manager](https://github.com/jetstack/cert-manager)를 사용할 수도 있으나, 이는 테스트되지 않았습니다.

`prometheusOperator.admissionWebhooks.certManager.enabled` 값을 true로 설정하여 cert-manager를 통한 자동 자체 서명 TLS 인증서 프로비저닝을 활성화할 수 있습니다.

### 제약 사항 (Limitations)

오퍼레이터는 단일 파드로만 실행될 수 있기 때문에 이 컴포넌트에 장애가 발생하면 규칙 배포가 실패할 가능성이 있습니다. 그러나 검증(validation) 기능을 통해 얻는 이점이 이러한 위험보다 크기 때문에 이 기능은 기본적으로 활성화되어 있습니다.

## Prometheus 규칙 및 Grafana 대시보드 개발

이 차트의 Grafana 대시보드 및 Prometheus 규칙은 [prometheus-operator/prometheus-operator](https://github.com/prometheus-operator/prometheus-operator) 및 기타 소스에서 복사된 것이며, [hack](hack) 폴더의 스크립트를 통해 (일부 수정되어) 동기화됩니다. 변경 사항을 적용하려면 먼저 [원본 리포지토리에 추가](https://github.com/prometheus-operator/kube-prometheus/blob/main/docs/customizations/developing-prometheus-rules-and-grafana-dashboards.md)한 다음 스크립트를 통해 동기화해야 합니다.

## 추가 정보 (Further Information)

설정 옵션의 의미에 대한 더 자세한 문서는 다음을 참조하세요:

- [Prometheus Operator](https://github.com/prometheus-operator/prometheus-operator)
- [Prometheus](https://prometheus.io/docs/introduction/overview/)
- [Grafana](https://github.com/grafana/helm-charts/tree/main/charts/grafana#grafana-helm-chart)

## prometheus.io/scrape

Prometheus Operator는 어노테이션 기반의 서비스 디스커버리를 지원하지 않으며, 훨씬 더 많은 설정 옵션을 제공하는 `PodMonitor` 또는 `ServiceMonitor` CRD를 대신 사용합니다.
PodMonitor/ServiceMonitor 사용 방법에 대한 정보는 `prometheus-operator/prometheus-operator` 문서를 참조하세요:

- [ServiceMonitors](https://github.com/prometheus-operator/prometheus-operator/blob/main/Documentation/developer/getting-started.md#using-servicemonitors)
- [PodMonitors](https://github.com/prometheus-operator/prometheus-operator/blob/main/Documentation/developer/getting-started.md#using-podmonitors)
- [Running Exporters](https://github.com/prometheus-operator/prometheus-operator/blob/main/Documentation/user-guides/running-exporters.md)

기본적으로 Prometheus는 해당 네임스페이스 내에서 prometheus-operator 릴리스와 동일한 릴리스 태그로 라벨이 지정된 PodMonitor 및 ServiceMonitor를 검색(디스커버리)합니다.
때로는 타사 애플리케이션에서 데이터를 스크레이프하는 등의 목적으로 사용자 정의 PodMonitor/ServiceMonitor를 검색해야 할 수 있습니다.
기본 PodMonitor/ServiceMonitor 검색을 해치지 않고 이를 수행하는 쉬운 방법은 Prometheus가 라벨 필터링을 적용하지 않고 해당 네임스페이스 내의 모든 PodMonitor/ServiceMonitor를 검색하도록 허용하는 것입니다.
이를 위해 `prometheus.prometheusSpec.podMonitorSelectorNilUsesHelmValues` 및 `prometheus.prometheusSpec.serviceMonitorSelectorNilUsesHelmValues`를 `false`로 설정할 수 있습니다.

## stable/prometheus-operator 차트에서 마이그레이션

### 무중단 마이그레이션 (Zero downtime)

`kube-prometheus-stack`은 `stable/prometheus-operator` 차트와 완벽하게 호환되므로 중단 없이 마이그레이션할 수 있습니다.
단, 이전 이름 접두사(prefix)를 유지해야 합니다. 새 이름을 사용하려면 아래의 단계별 가이드(다운타임 발생)를 따르세요.

다음과 같이 이름을 재정의하여 이를 달성할 수 있습니다:

```console
helm upgrade prometheus-operator prometheus-community/kube-prometheus-stack -n monitoring --reuse-values --set nameOverride=prometheus-operator
```

**참고**: 먼저 `--dry-run --debug` 플래그를 사용하여 실행해 보는 것을 권장합니다.

### 새 이름으로 재배포 (다운타임 발생)

**prometheus-operator** values 설정이 새 **kube-prometheus-stack** 차트와 호환되는 경우, 다음 단계에 따라 마이그레이션을 진행하세요:

> 이 가이드는 차트가 `monitoring` 네임스페이스에 배포되어 있고 해당 위치에서 실행 중임을 전제로 합니다. 다른 네임스페이스인 경우 `monitoring`을 배포된 네임스페이스로 변경하세요.

1. prometheus-operator 차트에서 생성/사용한 PersistentVolume의 반환 정책(reclaim policy)을 `Retain`으로 패치합니다:

    ```console
    kubectl patch pv/<PersistentVolume name> -p '{"spec":{"persistentVolumeReclaimPolicy":"Retain"}}'
    ```

    **참고:** 위 명령을 실행하려면 클러스터 전체 권한이 있어야 합니다. [Kubernetes RBAC](https://kubernetes.io/docs/reference/access-authn-authz/rbac/)을 참조하세요.

2. **prometheus-operator** 릴리스를 제거하고 기존 PersistentVolumeClaim을 삭제한 후, PV 상태가 `Released`가 되었는지 확인합니다.

    ```console
    helm uninstall prometheus-operator -n monitoring
    kubectl delete pvc/<PersistenceVolumeClaim name> -n monitoring
    ```

    추가로 남아 있는 `prometheus-operator-kubelet` 서비스를 수동으로 제거해야 합니다.

    ```console
    kubectl delete service/prometheus-operator-kubelet -n kube-system
    ```

    원하는 경우 기존의 모든 CRD(ServiceMonitor, PodMonitor 등)를 제거하도록 선택할 수도 있습니다.

3. 현재의 `spec.claimRef` 값을 제거하여 PV 상태를 Released에서 Available로 변경합니다.

    ```console
    kubectl patch pv/<PersistentVolume name> --type json -p='[{"op": "remove", "path": "/spec/claimRef"}]' -n monitoring
    ```

**참고:** 위 명령을 실행하려면 클러스터 전체 권한이 있어야 합니다. [Kubernetes RBAC](https://kubernetes.io/docs/reference/access-authn-authz/rbac/)을 참조하세요.

이 단계들을 완료한 후 **kube-prometheus-stack**을 새로 설치하고, 현재 **kube-prometheus-stack** 릴리스가 `values.yaml`의 `volumeClaimTemplate` 값과 일치하는지 확인합니다.

바인딩은 요청된 특정 스토리지 용량과 특정 액세스 모드를 일치시키는 방식으로 이루어집니다.

예를 들어, **prometheus-operator**에서 스토리지를 다음과 같이 지정했었다면:

```yaml
volumeClaimTemplate:
  spec:
    storageClassName: gp2
    accessModes: ["ReadWriteOnce"]
    resources:
     requests:
       storage: 50Gi
```

50Gi 스토리지와 `ReadWriteOnce` 액세스 모드를 갖는 일치하는 `volumeClaimTemplate`을 지정해야 합니다.

또한 기존 설치의 PV가 위치한 현재 가용 영역(AZ)을 확인하고, 새 릴리스가 이전과 동일한 AZ를 사용하도록 구성해야 합니다. 파드가 PV와 다른 AZ에 있는 경우 릴리스에서 기존 볼륨을 바인딩하지 못해 새 PV를 생성하게 됩니다.

이는 `values.yaml`을 통해 라벨을 지정하거나(예: `prometheus.prometheusSpec.nodeSelector`를 다음과 같이 설정):

```yaml
nodeSelector:
  failure-domain.beta.kubernetes.io/zone: east-west-1a
```

설치 시 `--set` 재정의 옵션으로 이 값들을 전달하여 수행할 수 있습니다.

이제 새 릴리스가 이전에 릴리스되었던 PV를 해당 내용과 함께 다시 연결합니다.

## coreos/prometheus-operator 차트에서 마이그레이션

여러 차트가 결합되어 prometheus-operator, prometheus, alertmanager, grafana 및 클러스터 모니터링에 필요한 다양한 exporter들을 설치하는 단일 차트로 통합되었습니다.

변경 사항이 광범위하고 차트 유지 관리를 더 용이하게 하기 위한 목적이므로 두 차트 간에 단순하고 직접적인 마이그레이션 경로는 없습니다.

단일 클러스터에서 여러 프로메테우스 인스턴스를 실행하는 기능을 포함하여 이전 차트의 모든 기능을 새 차트에서도 사용할 수 있습니다. 단, 배포하지 않으려는 차트 부분은 비활성화해야 합니다.

이 변경 사항에 대한 티켓은 [prometheus-operator/prometheus-operator #592](https://github.com/prometheus-operator/prometheus-operator/issues/592) 및 [helm/charts #6765](https://github.com/helm/charts/pull/6765)에서 확인할 수 있습니다.

### 주요 변경 사항 개요

#### 추가된 의존성

차트에 3가지 [의존성](#의존성-dependencies)이 추가되었습니다.

- Node-Exporter, Kube-State-Metrics: 이 컴포넌트들은 차트의 의존성으로 로드되며 비교적 단순한 컴포넌트들입니다.
- Grafana: Grafana 차트는 이 차트보다 기능이 더 풍부합니다. 동일한 클러스터에 배포된 configmap에서 데이터 소스와 대시보드를 로드할 수 있는 사이드카(sidecar)가 포함되어 있습니다. 자세한 내용은 [차트 문서](https://github.com/grafana/helm-charts/blob/main/charts/grafana/README.md)를 확인하세요.

#### Kubelet 서비스

차트에서 kubelet 서비스의 새 이름이 지정되었으므로, 컨테이너 메트릭이 두 번 카운트되는 것을 방지하기 위해 `kube-system` 네임스페이스에 있는 이전 kubelet 서비스를 정리해야 합니다.

#### 영구 볼륨 (Persistent Volumes)

현재 영구 볼륨의 데이터를 유지하려면 새 차트의 명명 규칙을 사용하여 생성된 새 PVC 및 PV에 기존 볼륨을 연결할 수 있습니다. 예를 들어 `prometheus-migration`이라는 Helm 릴리스에 기존 Azure 디스크를 사용하려면 다음과 같은 리소스를 생성할 수 있습니다:

```yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: pvc-prometheus-migration-prometheus-0
spec:
  accessModes:
  - ReadWriteOnce
  azureDisk:
    cachingMode: None
    diskName: pvc-prometheus-migration-prometheus-0
    diskURI: /subscriptions/f5125d82-2622-4c50-8d25-3f7ba3e9ac4b/resourceGroups/sample-migration-resource-group/providers/Microsoft.Compute/disks/pvc-prometheus-migration-prometheus-0
    fsType: ""
    kind: Managed
    readOnly: false
  capacity:
    storage: 1Gi
  persistentVolumeReclaimPolicy: Delete
  storageClassName: prometheus
  volumeMode: Filesystem
```

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  labels:
    app.kubernetes.io/name: prometheus
    prometheus: prometheus-migration-prometheus
  name: prometheus-prometheus-migration-prometheus-db-prometheus-prometheus-migration-prometheus-0
  namespace: monitoring
spec:
  accessModes:
  - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
  storageClassName: prometheus
  volumeMode: Filesystem
  volumeName: pvc-prometheus-migration-prometheus-0
```

PVC는 PV의 소유권을 가지며, persistent volume claim template을 사용하여 릴리스를 생성할 때 차트에서 사용되는 명명 규칙과 일치하므로 기존 PVC를 사용하게 됩니다. 다른 클라우드 공급자의 경우에도 유사한 접근 방식을 사용할 수 있습니다.

#### KubeProxy

kube-proxy의 메트릭 바인드 주소는 기본값이 `127.0.0.1:10249`로 설정되어 있어 Prometheus 인스턴스가 **접근할 수 없습니다**. 메트릭을 수집하려면 `metricsBindAddress` 필드 값을 `0.0.0.0:10249`로 변경하여 노출해야 합니다.

클러스터에 따라 관련 `config.conf` 부분은 ConfigMap `kube-system/kube-proxy` 또는 `kube-system/kube-proxy-config`에 위치합니다. 예:

```console
kubectl -n kube-system edit cm kube-proxy
```

```yaml
apiVersion: v1
data:
  config.conf: |-
    apiVersion: kubeproxy.config.k8s.io/v1alpha1
    kind: KubeProxyConfiguration
    # ...
    # metricsBindAddress: 127.0.0.1:10249
    metricsBindAddress: 0.0.0.0:10249
    # ...
  kubeconfig.conf: |-
    # ...
kind: ConfigMap
metadata:
  labels:
    app: kube-proxy
  name: kube-proxy
  namespace: kube-system
```

