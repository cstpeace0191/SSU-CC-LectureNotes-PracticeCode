# 13주차: 클라우드 컴퓨팅 보안 — 슬라이드 콘텐츠 초안 (총 47장)

> 이 문서는 `13주차_클라우드 컴퓨팅 보안.pptx` 제작을 위한 슬라이드별 콘텐츠 초안입니다. 샌드박스(파일 생성 환경) 복구 후 이 내용을 그대로 pptx로 변환합니다. 각 슬라이드 하단의 `[디자인 노트]`는 추후 pptx 제작 시 반영할 시각 요소 제안입니다.
>
> **팔레트 제안**: Midnight Executive 계열(네이비 `1E2761` 주색 + 아이스블루 `CADCFC` 보조 + 화이트 포인트) — 보안/신뢰 주제에 어울리는 톤. 타이틀·구분 슬라이드는 다크(네이비) 배경, 본문 슬라이드는 화이트 배경의 샌드위치 구조.

---

## 0부. 도입 (Slide 1~5)

### Slide 1. 표지
- 13주차: 클라우드 컴퓨팅 보안
- 부제: 경계 기반(Perimeter)에서 자격증명 기반(Identity-based) · 제로 트러스트(Zero Trust)로
- 과목명 / 주차 / 날짜
[디자인 노트] 다크 네이비 배경, 큰 타이틀(44pt), 자물쇠·클라우드 아이콘 조합 그래픽

### Slide 2. 학습목표
- 클라우드 보안의 패러다임 전환(경계 → 자격증명/제로트러스트)을 설명할 수 있다
- 책임공유모델에 따라 고객/CSP의 보안 책임 범위를 구분할 수 있다
- 인프라·컨테이너·IaC·CI/CD 각 단계별 핵심 보안 통제를 나열할 수 있다
- CSPM/CNAPP 및 주요 컴플라이언스 표준(ISMS-P, ISO27017/18, SOC2, GDPR)을 이해한다
[디자인 노트] 체크리스트 아이콘 4개, 원형 아이콘+텍스트 행 레이아웃

### Slide 3. 오늘의 목차 (5대 영역 로드맵)
1. 클라우드 보안 기본 원리 (Fundamentals)
2. 인프라 및 데이터 보안 (Infrastructure & Data)
3. 컨테이너 & 쿠버네티스 보안 (Cloud-Native)
4. DevSecOps & IaC 보안 (Security in Automation)
5. 관제·거버넌스·컴플라이언스 (Governance & Monitoring)
[디자인 노트] 5단계 가로 타임라인/로드맵 그래픽, 각 단계 아이콘

### Slide 4. 왜 지금 클라우드 보안인가 — 숫자로 보는 현실
- 데이터 유출 평균 비용(글로벌, 2025): **4.44M달러**(IBM Cost of a Data Breach 2025)
- 다중환경(멀티클라우드) 유출 평균 비용: **5.05M달러** — 단일 온프레미스(4.01M)보다 높음
- 클라우드 보안 사고의 **약 95%는 설정 오류 등 인적 요인**에서 기인(업계 조사 다수)
- Gartner 전망: 2026년까지 클라우드 보안 실패의 **99%가 고객 책임**(설정 오류 중심)
[디자인 노트] 큰 통계 콜아웃(60-72pt 숫자) 2x2 그리드, 출처 각주(작게)

### Slide 5. 패러다임 전환: 경계 기반 → 자격증명 기반/제로트러스트
- 전통 보안: 방화벽으로 둘러싼 "성(城)" — 내부는 신뢰, 외부는 차단
- 클라우드 시대: 경계가 사라짐(재택근무, API, 멀티클라우드, 컨테이너의 동적 IP)
- 새 원칙: **"아무도 믿지 않고, 항상 검증한다"** — 신원(Identity)이 새로운 경계
[디자인 노트] 좌(성벽 아이콘, 어둡게) → 우(분산 네트워크+ID뱃지 아이콘) 비교형 2단 레이아웃

---

## 1부. 클라우드 보안의 기본 원리 (Slide 6~13)

### Slide 6. 구분 슬라이드 — 1. Fundamentals
- 클라우드 보안 학습의 출발점: 온프레미스와 무엇이 다른가
[디자인 노트] 다크 배경 섹션 구분 슬라이드, 큰 번호 "01"

### Slide 7. 책임공유모델(Shared Responsibility Model) 개념
- CSP(AWS/GCP/Azure)가 책임지는 영역: **"Cloud 자체의 보안"**(물리보안, 하이퍼바이저, 글로벌 인프라)
- 고객이 책임지는 영역: **"Cloud 내부의 보안"**(데이터, IAM 설정, OS 패치, 네트워크 설정, 애플리케이션)
- 다수의 침해사고가 이 경계를 오해한 데서 발생
[디자인 노트] 저울(균형) 아이콘, 좌우 대비 카드

### Slide 8. 서비스 모델별 책임 범위 (IaaS/PaaS/SaaS)
| 영역 | IaaS | PaaS | SaaS |
|---|---|---|---|
| 데이터/접근관리 | 고객 | 고객 | 고객 |
| 애플리케이션 | 고객 | 고객 | CSP |
| 런타임/OS | 고객 | CSP | CSP |
| 가상화/서버/네트워크 | CSP | CSP | CSP |
- 고객 책임 범위는 IaaS→SaaS로 갈수록 축소되지만 "0"이 되지는 않음
[디자인 노트] 4행 비교표, 고객=네이비 셀 강조 / CSP=연한 회색

### Slide 9. 제로 트러스트(Zero Trust) 정의
- 핵심 문구: **"Never trust, always verify"**
- 사용자·기기·워크로드·API 호출·데이터 요청 **모두를 기본적으로 신뢰하지 않음**
- 매 요청마다 신원(Identity)·컨텍스트(디바이스 상태, 위치, 시간)·정책을 기준으로 검증
[디자인 노트] 중앙에 방패 아이콘, 방사형으로 User/Device/Workload/API 4개 노드 배치, 각 노드에서 방패로 화살표(검증)

### Slide 10. 제로 트러스트 5대 축(NIST/CISA 성숙도 모델 기반)
- Identity(신원) · Device(기기) · Network(네트워크, 마이크로세그멘테이션) · Application/Workload(앱) · Data(데이터)
- 5개 축을 아우르는 가시성·자동화·거버넌스 계층
[디자인 노트] 5개 세로 기둥(pillar) 아이콘 카드 + 하단 가로 바(가시성/자동화)

### Slide 11. IAM(Identity and Access Management) 개념
- User(사용자) · Role(역할) · Policy(정책)의 3요소
- Policy: 누가(Principal) 무엇을(Resource) 어떤 조건(Condition)에서 할 수 있는가(Action)를 JSON 등으로 명시
- 클라우드 보안 사고의 상당수가 과도한 IAM 권한에서 출발
[디자인 노트] User→Role→Policy→Resource 흐름 다이어그램(화살표 체인)

### Slide 12. 최소 권한 원칙 & MFA
- 최소 권한 원칙(Principle of Least Privilege): 업무 수행에 필요한 **최소한의 권한만** 부여
- "과도한 권한 조합(Toxic Combination)"이 권한 상승(Privilege Escalation) 경로가 됨 → 정기적 권한 재검토(Rightsizing) 필요
- MFA(다중요소인증): 비밀번호 유출만으로는 계정 탈취 불가하도록 2차 인증요소 추가
[디자인 노트] 자물쇠 단계별 축소 아이콘(넓은권한→좁은권한), MFA는 스마트폰+OTP 아이콘

### Slide 13. 최신 트렌드: 임시 자격증명(Temporary Credentials)
- 정적 액세스 키(장기 유효) → **임시 자격증명**으로 전환이 업계 표준화
  - AWS: STS(Security Token Service)
  - Azure: Managed Identity
  - GCP: Workload Identity Federation
- 장기 키 유출 리스크를 근본적으로 축소 — 자격증명 기반 보안의 핵심 실천
[디자인 노트] 3개 벤더 로고형 아이콘 카드 3열, 하단에 "정적 키 🚫 → 임시 토큰 ✅" 비교 바

---

## 2부. 인프라 및 데이터 보안 (Slide 14~21)

### Slide 14. 구분 슬라이드 — 2. Infrastructure & Data
- 가상 네트워크, 서버, 데이터 저장소를 보호하는 기술 체계
[디자인 노트] 다크 배경, 큰 번호 "02", 서버랙+자물쇠 아이콘

### Slide 15. 네트워크 보안 기본 구조 — VPC와 Subnet
- VPC(Virtual Private Cloud): 클라우드 내 논리적으로 격리된 사설 네트워크 공간
- Subnet 분리: Public Subnet(외부노출 필요 자원) vs Private Subnet(DB 등 내부자원) 분리 배치
- 원칙: 외부에 노출될 필요가 없는 자원은 Private Subnet에 배치
[디자인 노트] VPC 박스 안에 Public/Private Subnet 2개 구획, 서버 아이콘 배치도

### Slide 16. Security Group vs NACL
| 구분 | Security Group | NACL |
|---|---|---|
| 적용 단위 | 인스턴스(ENI) | 서브넷 |
| 상태(State) | Stateful(응답 트래픽 자동 허용) | Stateless(양방향 규칙 필요) |
| 규칙 | Allow만 가능 | Allow/Deny 모두 가능 |
- Security Group이 1차 방어선, NACL은 서브넷 단위 2차 방어선
[디자인 노트] 좌우 비교 카드, 방화벽 아이콘

### Slide 17. WAF와 DDoS 방어
- WAF(Web Application Firewall): SQL Injection, XSS 등 애플리케이션 계층(L7) 공격 차단
- DDoS 방어: 대용량 트래픽 공격으로부터 가용성 보호(예: AWS Shield, Azure DDoS Protection, Cloud Armor)
- 두 방어체계는 네트워크 경계에서 애플리케이션을 보호하는 상호 보완적 계층
[디자인 노트] 방패 아이콘 앞에서 화살(공격) 튕겨내는 이미지 모티프

### Slide 18. 안전한 접속 경로 — Bastion / VPN / Private Link
- Bastion Host: Private Subnet 자원 접속을 위한 단일 경유 서버(SSH/RDP 진입점 최소화)
- VPN: 온프레미스-클라우드 간 암호화 터널
- Private Link(Private Endpoint): 공인 인터넷을 거치지 않고 클라우드 서비스 간 사설 연결
[디자인 노트] 3개 접속경로 아이콘을 하나의 네트워크 다이어그램에 통합 표시

### Slide 19. 데이터 보호 — 암호화의 두 축
- 전송 중 암호화(In-Transit): TLS/SSL, HTTPS로 네트워크 구간 데이터 보호
- 저장 시 암호화(At-Rest): 디스크·DB·오브젝트 스토리지에 저장된 데이터 보호
- 두 축이 모두 갖춰져야 "End-to-End" 데이터 보호가 완성됨
[디자인 노트] 데이터가 이동(전송)하는 화살표 + 저장(디스크 아이콘) 두 지점에 자물쇠 표시

### Slide 20. 키 관리 — KMS(Key Management Service)
- 대칭키(Symmetric Key): 암/복호화에 동일 키 사용 — 속도가 빠름(대용량 데이터에 적합)
- 비대칭키(Asymmetric Key): 공개키/개인키 쌍 — 키 배포·전자서명에 유리
- KMS: 암호화 키의 생성·순환(Rotation)·접근권한·감사로그를 중앙관리하는 서비스
[디자인 노트] 열쇠 2종(같은모양=대칭 / 자물쇠+열쇠 다른모양=비대칭) 아이콘 비교

### Slide 21. 실습 체크리스트 — 인프라·데이터 보안 자가점검
- [ ] Private Subnet에 있어야 할 자원이 실수로 Public에 노출되어 있지 않은가?
- [ ] Security Group에 0.0.0.0/0(전체허용) 규칙이 불필요하게 남아있지 않은가?
- [ ] 스토리지/DB의 저장 시 암호화가 기본 활성화되어 있는가?
- [ ] KMS 키의 순환 주기가 설정되어 있는가?
[디자인 노트] 체크박스 리스트 카드, 우측에 "Quick Win" 뱃지

---

## 3부. 컨테이너 & 쿠버네티스 보안 (Slide 22~30)

### Slide 22. 구분 슬라이드 — 3. Cloud-Native Security
- 도커 컨테이너와 쿠버네티스 환경에 특화된 보안
[디자인 노트] 다크 배경, 큰 번호 "03", 고래(Docker)+조타륜(K8s) 아이콘

### Slide 23. 컨테이너 이미지 보안 — 취약점 스캐닝
- 컨테이너 이미지는 OS 패키지·라이브러리의 집합 — 알려진 취약점(CVE)을 내포할 수 있음
- 대표 도구: **Trivy**, **Grype** — 이미지 레이어를 스캔해 CVE·설정오류를 탐지
- CI 파이프라인에 통합해 "취약한 이미지는 빌드 단계에서 차단"하는 것이 핵심
[디자인 노트] 컨테이너 박스를 레이어별로 분해한 그림 + 돋보기(스캔) 아이콘

### Slide 24. 이미지 무결성 검증 — 디지털 서명(Cosign)
- 문제의식: 스캔을 통과한 이미지가 배포 전에 변조되지 않았음을 어떻게 보장할까?
- **Cosign(Sigstore 프로젝트)**: 컨테이너 이미지에 디지털 서명을 부여하고 배포 시 서명을 검증
- 소프트웨어 공급망 보안(Supply Chain Security)의 핵심 실천
[디자인 노트] 이미지 박스에 인장(도장/서명) 아이콘 부착, 검증 화살표

### Slide 25. 쿠버네티스 보안 아키텍처 개요
- 클러스터 계층에서 지켜야 할 요소: API Server, etcd, RBAC, 감사로그, Admission Controller
- 컨테이너 보안이 "이미지"를 지킨다면, 쿠버네티스 보안은 "이미지가 실행되는 운영체계 전체"를 지킴
[디자인 노트] 쿠버네티스 클러스터 구조도(Control Plane + Node) 단순화 다이어그램

### Slide 26. RBAC (Role-Based Access Control)
- 클러스터 리소스(Pod, Secret, Deployment 등)에 대한 접근 권한을 역할 기반으로 제어
- 원칙: 사용자·서비스어카운트에 **필요한 리소스·동작(verb)만** 허용하는 세밀한(Granular) 권한 설계
- 과도하게 넓은 RBAC 권한은 OWASP Kubernetes Top 10의 주요 리스크(추후 슬라이드 참고)
[디자인 노트] Role→RoleBinding→User/ServiceAccount 관계도

### Slide 27. Network Policy
- 기본값: 쿠버네티스 Pod는 별도 설정이 없으면 **서로 자유롭게 통신 가능**(과도하게 개방적)
- Network Policy로 Pod 간 통신을 화이트리스트 방식으로 제한 → 마이크로세그멘테이션 구현
- 예: 프론트엔드 Pod는 백엔드 Pod의 특정 포트만 호출 가능하도록 제한
[디자인 노트] Pod들을 점선 박스로 그룹화하고 허용된 통신만 실선 화살표로 표시

### Slide 28. Pod Security Standards (PSS)
- Pod가 지켜야 할 실행 보안 규칙의 표준(Privileged / Baseline / Restricted 3단계)
- 대표 규칙: **root 권한으로 컨테이너 실행 금지**, 호스트 네임스페이스 접근 제한, 권한 상승(privilege escalation) 금지
- Namespace 단위로 Restricted 레벨을 강제하는 것이 권장 기본값
[디자인 노트] 3단계 레벨 게이지(Privileged→Baseline→Restricted), root 사용자 아이콘에 금지 표시

### Slide 29. 런타임 보안 — Falco
- 스캐닝·정책은 "배포 전" 통제 — 그렇다면 "실행 중" 이상행동은 누가 잡는가?
- **Falco**: 커널 이벤트를 관찰해 컨테이너 내부의 이상행동(예상 밖 명령 실행, 민감 파일 변경, 권한 상승 시도)을 실시간 탐지
- 다른 도구(Cilium, Prometheus, Grafana)와 결합해 통합 클라우드 네이티브 보안 스택 구성
[디자인 노트] 레이더/모니터 화면 아이콘, 이상행동 알림 팝업 그래픽

### Slide 30. OWASP Kubernetes Top 10 (요약)
- K01 안전하지 않은 워크로드 설정 · K02 공급망 취약점 · K03 과도한 RBAC 권한
- K04 중앙화된 정책 부재 · K05 부실한 로깅/모니터링 · K06 취약한 인증
- K07 네트워크 세그먼트 미흡 · K08 시크릿 관리 실패 · K09 클러스터 구성요소 설정오류 · K10 오래된 취약 컴포넌트
[디자인 노트] 10개 항목을 2열×5행 아이콘+짧은 텍스트 카드 그리드로 배치(작은 폰트, 밀도 높은 요약 슬라이드)

---

## 4부. DevSecOps & IaC 보안 (Slide 31~37)

### Slide 31. 구분 슬라이드 — 4. DevSecOps & IaC Security
- 보안을 파이프라인과 코드 작성 단계로 끌어올리는 "Shift-Left Security"
[디자인 노트] 다크 배경, 큰 번호 "04", 인프라 코드(</>)+방패 결합 아이콘

### Slide 32. Shift-Left Security란
- 기존: 보안 점검은 배포 "이후"(운영 단계)에 집중 → 사고 발생 시 수습 비용 큼
- Shift-Left: 설계·코드 작성·CI 단계로 보안 점검을 앞당김
- "IaC 설정 오류는 배포 전에 고치면 공짜, 침해사고 이후에 고치면 매우 비싸다"
[디자인 노트] SDLC 타임라인 위에 화살표로 보안 점검 지점을 왼쪽(초기 단계)으로 이동시키는 그래픽

### Slide 33. 시크릿(Secret) 관리
- 위험: API Key, DB 비밀번호 등을 소스코드에 하드코딩 → 저장소 유출 시 즉시 노출
- 해결: 전용 시크릿 관리 도구에 암호화 저장 후 런타임에 동적으로 주입
  - **HashiCorp Vault**, **AWS Secrets Manager**
- 원칙: 코드에는 "시크릿을 어디서 가져올지"만 남기고, 값 자체는 남기지 않는다
[디자인 노트] 소스코드 파일 아이콘에 금고(Vault) 아이콘을 연결하는 흐름도

### Slide 34. IaC 정적 분석 도구 비교
| 도구 | 주요 특징 |
|---|---|
| Checkov | Terraform/K8s/CloudFormation 등 광범위 지원, 1,000개+ 정책(그래프 기반 교차분석 포함) |
| Trivy | 컨테이너·오픈소스 의존성·IaC 설정을 하나의 도구로 통합 스캔 (구 tfsec 기능 통합) |
| KICS | 22개+ IaC 플랫폼, 2,400개+ 규칙(Rego 쿼리) 지원 |
- 공통 목표: Terraform/CloudFormation 코드의 CIS 벤치마크 위반·설정오류를 배포 전에 탐지
[디자인 노트] 3개 도구 로고형 카드 + 표, 하단에 "Pull Request마다 자동 실행" 캡션

### Slide 35. 파이프라인 보안 — SAST / SCA
- SAST(정적 애플리케이션 보안 테스트): 소스코드 자체의 보안 취약점 분석 (예: SonarQube)
- SCA(소프트웨어 구성요소 분석): 오픈소스 라이브러리·의존성의 알려진 취약점 점검 (예: Snyk)
- CI 단계에 두 검사를 통합해 "취약한 코드/의존성은 병합 전 자동 차단"
[디자인 노트] CI 파이프라인 흐름(커밋→빌드→테스트→배포) 위에 SAST/SCA 체크포인트 배지 삽입

### Slide 36. DevSecOps 파이프라인 통합 흐름
- 코드 작성(시크릿 스캔) → PR 생성(SAST/SCA, IaC 정적분석) → 빌드(이미지 스캔 Trivy) → 배포 전 서명검증(Cosign) → 운영(런타임 모니터링 Falco, CSPM)
- 보안이 파이프라인 "전 구간"에 촘촘히 내재화된 형태가 이상적인 DevSecOps
[디자인 노트] 좌→우 6단계 파이프라인 다이어그램, 각 단계 아래 대응 도구 아이콘 배치 (본 강의 핵심 요약 슬라이드)

### Slide 37. 사례로 보는 교훈 — IaC 설정 오류의 대가
- 흔한 실수 예: Terraform으로 생성한 S3/스토리지 버킷의 접근범위를 실수로 "전체 공개"로 설정
- 정적분석 도구가 PR 단계에서 규칙 위반을 탐지했다면 배포 자체가 차단되었을 사안
- 교훈: 사람의 리뷰만으로는 반복되는 설정 실수를 막기 어렵다 → 자동화된 게이트가 필수
[디자인 노트] "Before/After" 2단 비교(수동리뷰만 있는 파이프라인 vs 자동 게이트가 있는 파이프라인)

---

## 5부. 관제·거버넌스·컴플라이언스 (Slide 38~44)

### Slide 38. 구분 슬라이드 — 5. Governance & Monitoring
- 기업 전체 클라우드 자산의 위협 감지와 법적 규제 준수
[디자인 노트] 다크 배경, 큰 번호 "05", 대시보드/레이더 아이콘

### Slide 39. CSPM (Cloud Security Posture Management)
- 클라우드에 이미 배포된 자산의 **설정 오류(Misconfiguration)를 지속적으로 스캔·탐지**
- IaC 정적분석이 "배포 전" 점검이라면, CSPM은 "배포 후 현재 상태"를 계속 추적하는 상시 감시
- 시장 성장세: CSPM 시장은 2025년 약 28.2억 달러 → 2030년 약 69.6억 달러 전망(연평균 19.8% 성장) — 그만큼 중요도가 커지는 영역
[디자인 노트] 클라우드 자산 아이콘들 위에 지속적으로 움직이는 스캔 레이더 그래픽

### Slide 40. CNAPP — CSPM의 확장판
- CNAPP(Cloud-Native Application Protection Platform): CSPM + 워크로드 보호 + 취약점관리 + IaC스캔 등을 하나의 플랫폼으로 통합
- 최근 흐름: CSPM은 독립도구에서 **CNAPP의 통합 제어판(Control Plane)** 역할로 진화 중
- "코드에서 클라우드까지(Code-to-Cloud)" 가시성 확보가 핵심 트렌드
[디자인 노트] 우산형 다이어그램 — CNAPP 큰 우산 아래 CSPM/이미지스캔/IaC스캔/런타임보호 하위 요소 배치

### Slide 41. 위협 감지 — 로그 수집과 SIEM/SOAR
- 클라우드 감사로그: AWS CloudTrail(API 호출 기록), VPC Flow Logs(네트워크 트래픽 기록) 등
- SIEM(보안정보이벤트관리): 각종 로그를 중앙 수집·상관분석하여 위협 징후 탐지
- SOAR(보안오케스트레이션·자동화·대응): 탐지된 위협에 대한 대응을 자동화(예: 의심 계정 자동 격리)
[디자인 노트] 여러 로그 소스 → SIEM(깔때기) → SOAR(자동 대응 로봇 아이콘) 흐름도

### Slide 42. 관리형 위협 탐지 서비스 — GuardDuty 등
- AWS GuardDuty와 같은 관리형 위협탐지 서비스: 로그 기반으로 이상행동을 자동 탐지(비정상 API 호출, 알려진 악성 IP 통신 등)
- CSPM(설정오류 탐지) + 위협탐지 서비스(행위기반 탐지)가 상호보완적으로 결합되어야 완전한 관제 체계
[디자인 노트] 레이더 화면에 이상 신호 포인트 표시, 경고 아이콘

### Slide 43. 컴플라이언스 표준 한눈에 보기
| 표준 | 성격 | 주요 대상 |
|---|---|---|
| ISMS-P | 한국 정보보호·개인정보보호 관리체계 인증 | 국내 사업자 |
| ISO/IEC 27017 | 클라우드 특화 보안 통제 가이드(ISO27002 확장) | 글로벌 CSP/이용기업 |
| ISO/IEC 27018 | 퍼블릭 클라우드 내 개인식별정보(PII) 보호 가이드 | PII 처리 CSP |
| SOC 2 (Type II) | 북미 중심 신뢰서비스기준 감사 보고서 | 글로벌 SaaS/CSP |
| GDPR | EU 개인정보보호 규정(법적 구속력) | EU 시민 데이터 처리 전체 |
[디자인 노트] 5행 비교표, 국기/지역 아이콘으로 지역성 표시

### Slide 44. 컴플라이언스 실무 포인트
- 인증/표준 준수는 "한 번 취득으로 끝"이 아니라 **지속적 증적 수집**의 문제(Continuous Compliance)
- ISO 27018 인증이 GDPR 준수를 자동으로 보장하지는 않음 — 표준 간 범위 차이를 이해해야 함
- CSPM 도구들이 컴플라이언스 프레임워크별 체크리스트를 자동 매핑해주는 기능을 제공하는 추세
[디자인 노트] "인증서 아이콘 + 지속적 갱신 화살표(원형)" 그래픽

---

## 마무리 (Slide 45~47)

### Slide 45. 전체 로드맵 총정리
- ① Fundamentals(책임공유·제로트러스트·IAM) → ② Infra&Data(네트워크·암호화) → ③ Container/K8s(이미지·RBAC·런타임) → ④ DevSecOps/IaC(시크릿·정적분석·파이프라인) → ⑤ Governance(CSPM·SIEM·컴플라이언스)
- 다섯 영역은 순차적 학습 단계이자, 실제 조직에서는 **동시에 운영되어야 하는 통합 보안 체계**
[디자인 노트] Slide 3의 로드맵 그래픽을 재사용하되 각 단계에 체크마크 추가(학습완료 느낌)

### Slide 46. 더 나아가기 — 관련 자격증 & 학습 경로 (심화 학습용)
- 클라우드 보안 전문 자격: CCSP(Certified Cloud Security Professional), AWS Certified Security – Specialty
- 쿠버네티스 보안 전문 자격: CKS(Certified Kubernetes Security Specialist)
- 실습 권장: 개인 실습 계정에서 Trivy/Checkov/Falco를 직접 설치해보는 것을 권장
[디자인 노트] 자격증 뱃지 아이콘 3~4개 가로 배열

### Slide 47. 참고자료 및 출처
- IBM, *Cost of a Data Breach Report 2025*
- OWASP, *Kubernetes Top 10* (owasp.org/www-project-kubernetes-top-ten)
- NIST/CISA, *Zero Trust Maturity Model*
- Wiz Academy, *Zero Trust Architecture / Cloud Security Standards*
- Aqua Security(Trivy), HashiCorp(Vault), Sigstore(Cosign), Falco(CNCF) 공식 문서
- ISO/IEC 27017, ISO/IEC 27018 공식 표준 개요(iso.org)
- 각 슬라이드 통계·수치는 작성 시점 공개된 업계 조사자료를 인용하였으며, 실제 강의 시 최신 수치로 갱신 권장
[디자인 노트] 심플한 텍스트 슬라이드, 화이트 배경, 좌측 정렬 출처 리스트(9-10pt)

---

## 제작 메모 (pptx 변환 시 참고)
- 총 슬라이드 수: **47장** (요청 기준 40장 이상 충족)
- 구분 슬라이드(다크 배경) 6장 + 표지/마무리 4장 + 본문 슬라이드 37장
- 표가 포함된 슬라이드(8, 16, 34, 43)는 pptxgenjs의 표 개체 또는 카드형 레이아웃으로 변환
- 모든 본문 슬라이드에 최소 1개 이상의 아이콘/도형/다이어그램 배치 원칙 준수(텍스트만 있는 슬라이드 지양)
- 팔레트: 주색 네이비(1E2761), 보조 아이스블루(CADCFC), 포인트 화이트(FFFFFF) — 필요 시 경고/위험 강조색으로 코랄(F96167) 소량 사용 가능
