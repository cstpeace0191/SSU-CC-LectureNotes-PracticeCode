import pptx
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)

# Color Constants
DARK_BG = RGBColor(15, 23, 42)        # #0F172A Deep Slate / Navy
WHITE = RGBColor(255, 255, 255)
PRIMARY_BLUE = RGBColor(37, 99, 235)  # #2563EB Bright Accent Blue
DARK_TEXT = RGBColor(30, 41, 59)      # #1E293B Dark Slate
MUTED_TEXT = RGBColor(100, 116, 139) # #64748B Gray
CARD_BORDER = RGBColor(226, 232, 240) # #E2E8F0
CARD_BG = RGBColor(255, 255, 255)
LIGHT_CARD_BG = RGBColor(241, 245, 249) # #F1F5F9
CODE_BG = RGBColor(30, 30, 30)
CODE_TEXT = RGBColor(226, 232, 240)

blank_layout = prs.slide_layouts[6]

def add_header(slide, section_tag, slide_title, subtitle=""):
    tx_tag = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.733), Inches(0.35))
    tf_tag = tx_tag.text_frame
    tf_tag.word_wrap = True
    p_tag = tf_tag.paragraphs[0]
    p_tag.text = section_tag
    p_tag.font.size = Pt(11)
    p_tag.font.bold = True
    p_tag.font.color.rgb = PRIMARY_BLUE
    
    tx_title = slide.shapes.add_textbox(Inches(0.8), Inches(0.7), Inches(11.733), Inches(0.6))
    tf_title = tx_title.text_frame
    tf_title.word_wrap = True
    p_title = tf_title.paragraphs[0]
    p_title.text = slide_title
    p_title.font.size = Pt(22)
    p_title.font.bold = True
    p_title.font.color.rgb = DARK_TEXT
    
    if subtitle:
        p_sub = tf_title.add_paragraph()
        p_sub.text = subtitle
        p_sub.font.size = Pt(12)
        p_sub.font.color.rgb = MUTED_TEXT

def create_card(slide, left, top, width, height, title="", items=None, bg_color=CARD_BG, border_color=CARD_BORDER, title_color=DARK_TEXT):
    card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    card.fill.solid()
    card.fill.fore_color.rgb = bg_color
    if border_color:
        card.line.color.rgb = border_color
        card.line.width = Pt(1)
    else:
        card.line.fill.background()
        
    tf = card.text_frame
    tf.word_wrap = True
    tf.margin_left = Inches(0.2)
    tf.margin_right = Inches(0.2)
    tf.margin_top = Inches(0.2)
    tf.margin_bottom = Inches(0.2)
    
    if title:
        p_title = tf.paragraphs[0]
        p_title.text = title
        p_title.font.size = Pt(15)
        p_title.font.bold = True
        p_title.font.color.rgb = title_color
        p_title.space_after = Pt(8)
        first_item = True
    else:
        first_item = False
        
    if items:
        for idx, item in enumerate(items):
            if first_item and idx == 0:
                p = tf.add_paragraph()
            elif not first_item and idx == 0:
                p = tf.paragraphs[0]
            else:
                p = tf.add_paragraph()
                
            p.text = item
            p.font.size = Pt(12)
            p.font.color.rgb = DARK_TEXT
            p.space_after = Pt(4)

    return card

def create_code_box(slide, left, top, width, height, title, code_text):
    card = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
    card.fill.solid()
    card.fill.fore_color.rgb = CODE_BG
    card.line.fill.background()
    
    tf = card.text_frame
    tf.word_wrap = True
    tf.margin_left = Inches(0.2)
    tf.margin_right = Inches(0.2)
    tf.margin_top = Inches(0.2)
    tf.margin_bottom = Inches(0.2)
    
    p_title = tf.paragraphs[0]
    p_title.text = title
    p_title.font.size = Pt(12)
    p_title.font.bold = True
    p_title.font.color.rgb = PRIMARY_BLUE
    p_title.space_after = Pt(6)
    
    for line in code_text.split('\n'):
        p = tf.add_paragraph()
        p.text = line
        p.font.name = "Consolas"
        p.font.size = Pt(10)
        p.font.color.rgb = CODE_TEXT
        p.space_after = Pt(1)

def create_table(slide, left, top, width, height, headers, data, col_widths=None):
    rows = len(data) + 1
    cols = len(headers)
    table_shape = slide.shapes.add_table(rows, cols, left, top, width, height)
    table = table_shape.table
    
    if col_widths:
        for i, w in enumerate(col_widths):
            table.columns[i].width = w
            
    # Headers
    for c_idx, h_text in enumerate(headers):
        cell = table.cell(0, c_idx)
        cell.fill.solid()
        cell.fill.fore_color.rgb = DARK_BG
        p = cell.text_frame.paragraphs[0]
        p.text = h_text
        p.font.size = Pt(12)
        p.font.bold = True
        p.font.color.rgb = WHITE
        p.alignment = PP_ALIGN.CENTER
        
    # Data Rows
    for r_idx, row_data in enumerate(data):
        row_bg = LIGHT_CARD_BG if r_idx % 2 == 1 else CARD_BG
        for c_idx, cell_value in enumerate(row_data):
            cell = table.cell(r_idx + 1, c_idx)
            cell.fill.solid()
            cell.fill.fore_color.rgb = row_bg
            p = cell.text_frame.paragraphs[0]
            p.text = str(cell_value)
            p.font.size = Pt(11)
            p.font.color.rgb = DARK_TEXT
            if c_idx == 0:
                p.font.bold = True

def create_section_slide(prs, sec_num, sec_title, topics):
    slide = prs.slides.add_slide(blank_layout)
    bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
    bg.fill.solid()
    bg.fill.fore_color.rgb = DARK_BG
    bg.line.fill.background()
    
    tb_num = slide.shapes.add_textbox(Inches(1.0), Inches(1.8), Inches(3.0), Inches(1.2))
    p_num = tb_num.text_frame.paragraphs[0]
    p_num.text = f"{sec_num:02d}" if isinstance(sec_num, int) else str(sec_num)
    p_num.font.size = Pt(64)
    p_num.font.bold = True
    p_num.font.color.rgb = PRIMARY_BLUE
    
    tb_title = slide.shapes.add_textbox(Inches(1.0), Inches(3.2), Inches(11.333), Inches(1.0))
    p_title = tb_title.text_frame.paragraphs[0]
    p_title.text = sec_title
    p_title.font.size = Pt(32)
    p_title.font.bold = True
    p_title.font.color.rgb = WHITE
    
    tb_topics = slide.shapes.add_textbox(Inches(1.0), Inches(4.5), Inches(11.333), Inches(1.5))
    p_topics = tb_topics.text_frame.paragraphs[0]
    p_topics.text = topics
    p_topics.font.size = Pt(16)
    p_topics.font.color.rgb = RGBColor(148, 163, 184)
    return slide

# ------------------- Slide 1: Title Slide -------------------
s1 = prs.slides.add_slide(blank_layout)
bg1 = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
bg1.fill.solid()
bg1.fill.fore_color.rgb = DARK_BG
bg1.line.fill.background()

tb = s1.shapes.add_textbox(Inches(1.0), Inches(1.5), Inches(11.333), Inches(0.5))
p = tb.text_frame.paragraphs[0]
p.text = "CLOUD COMPUTING · WEEK 05"
p.font.size = Pt(14)
p.font.bold = True
p.font.color.rgb = PRIMARY_BLUE

tb_t = s1.shapes.add_textbox(Inches(1.0), Inches(2.2), Inches(11.333), Inches(1.6))
p_t = tb_t.text_frame.paragraphs[0]
p_t.text = "쿠버네티스 리소스 모델\n(Kubernetes Resource Model, KRM)"
p_t.font.size = Pt(36)
p_t.font.bold = True
p_t.font.color.rgb = WHITE

tb_sub = s1.shapes.add_textbox(Inches(1.0), Inches(4.2), Inches(11.333), Inches(0.8))
p_sub = tb_sub.text_frame.paragraphs[0]
p_sub.text = "K8s API · Resource · Object · Manifest 구조 및 자원 관리 실습"
p_sub.font.size = Pt(18)
p_sub.font.color.rgb = RGBColor(148, 163, 184)

line = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(1.0), Inches(5.3), Inches(11.333), Inches(0.03))
line.fill.solid()
line.fill.fore_color.rgb = PRIMARY_BLUE
line.line.fill.background()

tb_meta = s1.shapes.add_textbox(Inches(1.0), Inches(5.6), Inches(11.333), Inches(1.0))
p_meta = tb_meta.text_frame.paragraphs[0]
p_meta.text = "2026학년도 2학기 · AI융합학부   |   담당교수: 정선태 (cst@ssu.ac.kr, 형암공학관 1310호)   |   통합 강의노트 v.2026.07.03"
p_meta.font.size = Pt(13)
p_meta.font.color.rgb = RGBColor(203, 213, 225)


# ------------------- Slide 2: LEARNING OBJECTIVES -------------------
s2 = prs.slides.add_slide(blank_layout)
add_header(s2, "LEARNING OBJECTIVES", "학습 목표", "본 강의를 통해 습득할 핵심 지식 및 실무 역량입니다.")

objectives = [
    ("1. K8s 개요 및 생태계 표준", ["• Borg/Omega 유래 및 K8s 핵심 이점(인프라 독립성) 이해", "• CNI, CSI, CRI, CPI 등 플러그인 인터페이스 표준 및 CNCF 생태계 동향 습득"]),
    ("2. KRM 4대 요소 체계", ["• Manifest, API, Resource, Object의 정의 및 유기적 연동 관계 명확 구분", "• OOP 객체지향 및 REST API 관점에서의 다각도 모델 분석"]),
    ("3. Reconciliation Loop", ["• Spec(원하는 상태)과 Status(현재 상태) 간의 지속적 자동 조율 메커니즘 이해", "• 장애 발생 시 Self-healing(자가 복구) 동작 원리 체득"]),
    ("4. 7대 리소스 카테고리", ["• Workload, Network, Storage, Config, Security, Scheduling 등 분류별 역학 이해", "• 주요 K8s 오브젝트의 용도 및 특성 파악"]),
    ("5. 자원 제한 및 배포 실습", ["• Requests(스케줄링)와 Limits(상한선)의 동작 차이(Throttling vs OOMKilled)", "• Deployment 매니페스트 작성 및 자원 제한 실전 운용"])
]

for i, (title, items) in enumerate(objectives):
    top_pos = Inches(1.5 + i * 1.1)
    create_card(s2, Inches(0.8), top_pos, Inches(11.733), Inches(0.95), title=title, items=items, title_color=PRIMARY_BLUE)


# ------------------- Slide 3: AGENDA -------------------
s3 = prs.slides.add_slide(blank_layout)
add_header(s3, "AGENDA", "강의 목차")

agenda_items = [
    ("01", "쿠버네티스 개요 및 생태계 표준", "K8s 정의, Borg/Omega 유래, CNI/CSI/CRI/CPI 표준 및 CNCF 동향"),
    ("02", "쿠버네티스 리소스 모델 (KRM) 및 API 체계", "KRM 개념, API Endpoint, Resource vs Object, Spec vs Status"),
    ("03", "쿠버네티스 주요 리소스 상세 분류", "Workload, Network, Storage, Config, Security, Scheduling 7대 리소스"),
    ("04", "리소스 제어 및 자원 제한 (Requests & Limits)", "Requests/Limits, CPU Throttling, Memory OOMKilled 메커니즘"),
    ("05", "실전 Deployment Manifest 작성 및 배포 실습", "Deployment YAML 스펙 작성, 자원 제한 적용 및 kubectl 배포 실습"),
    ("06", "WRAP-UP (핵심 요약 & 학습 로드맵)", "주차별 학습 로드맵 점검 및 Week 05 핵심 요약 정리")
]

for i, (num, title, desc) in enumerate(agenda_items):
    col = i % 2
    row = i // 2
    left = Inches(0.8 + col * 5.97)
    top = Inches(1.6 + row * 1.8)
    
    card = s3.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, Inches(5.76), Inches(1.6))
    card.fill.solid()
    card.fill.fore_color.rgb = CARD_BG
    card.line.color.rgb = CARD_BORDER
    
    tf = card.text_frame
    tf.word_wrap = True
    tf.margin_left = Inches(0.2)
    tf.margin_top = Inches(0.2)
    
    p0 = tf.paragraphs[0]
    p0.text = num
    p0.font.size = Pt(20)
    p0.font.bold = True
    p0.font.color.rgb = PRIMARY_BLUE
    
    p1 = tf.add_paragraph()
    p1.text = title
    p1.font.size = Pt(14)
    p1.font.bold = True
    p1.font.color.rgb = DARK_TEXT
    
    p2 = tf.add_paragraph()
    p2.text = desc
    p2.font.size = Pt(11)
    p2.font.color.rgb = MUTED_TEXT


# ------------------- Slide 4: Section 01 Divider -------------------
create_section_slide(prs, 1, "쿠버네티스 개요 및 생태계 표준", "정의 · 역사 (Borg/Omega) · 표준 플러그인 (CNI/CSI/CRI/CPI) · CNCF 생태계 동향")


# ------------------- Slide 5: 1-1. 쿠버네티스(K8s) 개요 및 탄생 배경 -------------------
s5 = prs.slides.add_slide(blank_layout)
add_header(s5, "SECTION 01", "1-1. 쿠버네티스(K8s) 개요 및 탄생 배경")

c1_items = [
    "• 컨테이너화된 애플리케이션(containerized applications)의 자동 배포, 스케일링, 관리를 제공하는 오픈소스 컨테이너 오케스트레이션 플랫폼",
    "• 약어 'K8s': 'K'와 's' 사이에 8개의 철자가 들어가는 데서 유래",
    "• 클러스터 자원을 하나의 거대한 가상 컴퓨팅 자원으로 추상화하여 제공"
]
create_card(s5, Inches(0.8), Inches(1.6), Inches(3.7), Inches(5.2), title="📌 쿠버네티스 정의", items=c1_items, title_color=PRIMARY_BLUE)

c2_items = [
    "• Google이 10년 이상 구동한 대규모 분산 관리 시스템 Borg 및 Omega의 경험과 노하우를 바탕으로 2014년 개발",
    "• 2015년 CNCF(Cloud Native Computing Foundation) 설립과 함께 오픈소스로 기증됨",
    "• 커뮤니티 중심으로 지속 발전하여 클라우드 네이티브의 디팩토(De facto) 표준 확립"
]
create_card(s5, Inches(4.8), Inches(1.6), Inches(3.7), Inches(5.2), title="📜 역사적 유래 (Borg/Omega)", items=c2_items, title_color=PRIMARY_BLUE)

c3_items = [
    "• 온프레미스 베어메탈 서버, 가상 머신(VM), 퍼블릭 클라우드(GCP, AWS, Azure), 프라이빗/하이브리드 환경 등 모든 곳에서 구동 가능",
    "• 특정 인프라 벤더 종속(Vendor Lock-in) 방지",
    "• 개발-검증-운영 환경 간 완벽한 환경 일관성 및 이식성 보장"
]
create_card(s5, Inches(8.8), Inches(1.6), Inches(3.7), Inches(5.2), title="🌍 인프라 독립성 (핵심 이점)", items=c3_items, title_color=PRIMARY_BLUE)


# ------------------- Slide 6: 1-2. 쿠버네티스 표준의 핵심 구성 요소 -------------------
s6 = prs.slides.add_slide(blank_layout)
add_header(s6, "SECTION 01", "1-2. 쿠버네티스 표준의 핵심 구성 요소")

k8s_api_items = [
    "• 모든 리소스 정의 및 관리는 쿠버네티스 RESTful API(kube-apiserver)를 통해 수행",
    "• Pod, Service, Deployment 등의 객체를 YAML/JSON 표준 형식으로 선언적(Declarative) 관리",
    "• 클러스터 종류(Vanilla K8s, EKS, GKE, AKS)에 관계없이 동일한 관리 인터페이스 제공"
]
create_card(s6, Inches(0.8), Inches(1.5), Inches(11.733), Inches(1.6), title="⚡ 쿠버네티스 API (표준 인터페이스)", items=k8s_api_items, title_color=PRIMARY_BLUE)

tbl_headers = ["인터페이스", "풀네임", "역할 및 주요 기능", "대표 기술 / 도구"]
tbl_data = [
    ["CNI", "Container Network Interface", "Pod 네트워킹 표준, IP 할당 및 Pod 간 통신 라우팅", "Calico, Flannel, Cilium, Kindnetd"],
    ["CSI", "Container Storage Interface", "외부 스토리지 연동 표준, 영속성 볼륨 프로비저닝", "EBS CSI Driver, GCS Fuse, Rook-Ceph"],
    ["CRI", "Container Runtime Interface", "컨테이너 생성/실행 런타임 표준, Kubelet 통신", "containerd, CRI-O"],
    ["CPI", "Cloud Provider Interface", "퍼블릭 클라우드 자원(LB, Route, Storage) 연동", "AWS CPI, GCP CPI, Azure CPI"]
]
create_table(s6, Inches(0.8), Inches(3.3), Inches(11.733), Inches(3.5), tbl_headers, tbl_data, [Inches(1.5), Inches(2.8), Inches(4.6), Inches(2.833)])


# ------------------- Slide 7: 1-3. CNCF 생태계 표준 및 2026년 최근 동향 -------------------
s7 = prs.slides.add_slide(blank_layout)
add_header(s7, "SECTION 01", "1-3. CNCF 생태계 표준 및 2026년 최근 동향")

cncf_items = [
    "• Prometheus: 클러스터 메트릭 수집 및 모니터링 표준",
    "• Helm: 쿠버네티스 애플리케이션 패키징(Chart) 관리 표준",
    "• Envoy: L7 프록시 및 서비스 메시(Service Mesh) 통신 표준",
    "• Open Policy Agent (OPA): 클러스터 보안 및 정책 관리 표준",
    "• ArgoCD: GitOps 기반 선언적 지속적 배포(CD) 파이프라인 표준"
]
create_card(s7, Inches(0.8), Inches(1.6), Inches(5.7), Inches(5.2), title="🌐 CNCF 생태계 표준 프로젝트", items=cncf_items, title_color=PRIMARY_BLUE)

trend_items = [
    "• 운영성 고도화: Ingress에서 Gateway API로의 전환, Fine-grained RBAC 및 NetworkPolicy 기반 Zero-Trust 보안 적용",
    "• 멀티/하이브리드 클라우드: Anthos, Rancher, ACM 등을 활용한 멀티클러스터 중앙 통합 관리 보편화",
    "• 오퍼레이터 패턴 (Operator): Custom Resource Definition (CRD) 기반 DB 및 미들웨어 자동 운영 보편화",
    "• AI/ML 워크로드 확산: GPU 스케줄링 및 Kueue, Ray-on-K8s 오케스트레이션 활성화"
]
create_card(s7, Inches(6.833), Inches(1.6), Inches(5.7), Inches(5.2), title="🚀 2026년 운영 및 아키텍처 트렌드", items=trend_items, title_color=PRIMARY_BLUE)


# ------------------- Slide 8: Section 02 Divider -------------------
create_section_slide(prs, 2, "쿠버네티스 리소스 모델 (KRM) 및 API 체계", "KRM 개념 · API Endpoint · Resource vs Object · Spec vs Status")


# ------------------- Slide 9: 2-1. 쿠버네티스 리소스 모델 (KRM) 개요 -------------------
s9 = prs.slides.add_slide(blank_layout)
add_header(s9, "SECTION 02", "2-1. 쿠버네티스 리소스 모델 (KRM) 개요")

krm_def = [
    "• 쿠버네티스가 클러스터의 원하는 상태(Desired State)를 선언하고, 검증하며, 저장 및 유지하기 위해 채택한 통합 상태 관리 체계",
    "• 모든 클러스터 구성 요소를 일관된 API 스키마와 데이터 모델로 추상화하여 처리"
]
create_card(s9, Inches(0.8), Inches(1.5), Inches(11.733), Inches(1.4), title="🎯 쿠버네티스 리소스 모델 (KRM, Kubernetes Resource Model) 정의", items=krm_def, title_color=PRIMARY_BLUE)

krm_steps = [
    ("1. Manifest (선언서)", ["• 개발자가 작성한 정적 .yaml 파일", "• 원하는 상태(Desired State) 기술"]),
    ("2. API (접수처)", ["• kube-apiserver 엔드포인트", "• 인증, 인가 및 스키마 검증"]),
    ("3. Resource (클래스)", ["• 리소스 종류/타입 스키마", "• API 엔드포인트 수신 규격"]),
    ("4. Object (실체)", ["• etcd에 보존되는 실행 실체", "• 실제 노드에 배포 및 관동"])
]

for i, (st_title, st_items) in enumerate(krm_steps):
    left = Inches(0.8 + i * 2.98)
    create_card(s9, left, Inches(3.1), Inches(2.8), Inches(3.8), title=st_title, items=st_items, title_color=PRIMARY_BLUE)


# ------------------- Slide 10: 2-2. Resource vs Object 개념 비교 -------------------
s10 = prs.slides.add_slide(blank_layout)
add_header(s10, "SECTION 02", "2-2. Resource vs Object 개념 비교")

r_vs_o_headers = ["비교 항목", "Kubernetes Resource (리소스)", "Kubernetes Object (오브젝트)"]
r_vs_o_data = [
    ["핵심 정의", "API에서 다룰 수 있는 '리소스 유형 (Type / Class)'", "리소스를 기반으로 실제 클러스터에 생성된 '구체적 인스턴스 (Instance)'"],
    ["쉬운 비유", "프로그래밍의 클래스 (Class) / 메뉴판 카테고리", "메모리에 할당된 인스턴스 (Instance) / 주문하여 나온 실제 음식"],
    ["역할 및 위치", "API 서버가 제공하는 REST 엔드포인트 (/api/v1/pods 등)", "etcd 분산 저장소에 보존되는 실제 클러스터 상태 및 기록 그 자체"],
    ["구성 및 형태", "스키마 정의 (kubectl api-resources 로 목록 확인)", "Spec(원하는 상태)과 Status(현재 상태) 데이터를 포함하는 실체"],
    ["대표 예시", "Pod, Service, Deployment, ConfigMap, Secret, Node", "myapp-pod-a1b2, main-db-service, web-deployment-7f9b"]
]
create_table(s10, Inches(0.8), Inches(1.6), Inches(11.733), Inches(5.2), r_vs_o_headers, r_vs_o_data, [Inches(2.0), Inches(4.866), Inches(4.866)])


# ------------------- Slide 11: 2-3. Object의 내부 구조 및 Reconciliation Loop -------------------
s11 = prs.slides.add_slide(blank_layout)
add_header(s11, "SECTION 02", "2-3. Object의 내부 구조 및 Reconciliation Loop")

spec_items = [
    "• 사용자가 Manifest 파일에 정의한 의도 (Intention)",
    "• 예: 'nginx 컨테이너 3개를 항상 실행해줘'",
    "• 사용자가 수정하지 않는 한 변하지 않는 고정 목표값"
]
create_card(s11, Inches(0.8), Inches(1.6), Inches(5.7), Inches(2.4), title="📋 Spec (원하는 상태 - Desired State)", items=spec_items, title_color=PRIMARY_BLUE)

status_items = [
    "• 쿠버네티스 시스템이 실시간으로 관찰하고 수집한 실제 상태",
    "• 예: '현재 동작 중인 nginx 파드는 2개임'",
    "• 컨트롤러 및 Kubelet에 의해 실시간 갱신되는 동적 데이터"
]
create_card(s11, Inches(6.833), Inches(1.6), Inches(5.7), Inches(2.4), title="🔍 Status (현재 상태 - Current State)", items=status_items, title_color=PRIMARY_BLUE)

loop_items = [
    "• 컨트롤러 루프 (Controller Loop): 쿠버네티스는 Spec과 Status를 끊임없이 비교 (Observation)",
    "• 차이 발생 감지 (Drift Detection): 파드 사망, 노드 장애 등으로 Spec ≠ Status 상황 발생 시",
    "• 자가 복구 (Self-Healing): 쿠버네티스가 자동으로 신규 파드를 생성/재시작하여 Spec = Status 상태로 보정",
    "• 선언적 관리의 핵심: 사용자는 '복구 과정'을 명령하지 않고, 오직 '원하는 최종 상태(Spec)'만 선언"
]
create_card(s11, Inches(0.8), Inches(4.2), Inches(11.733), Inches(2.7), title="🔄 조율 루프 (Reconciliation Loop) & Self-Healing 동작 원리", items=loop_items, title_color=PRIMARY_BLUE)


# ------------------- Slide 12: 2-4. Manifest 파일의 4대 기본 필드 및 YAML 구조 -------------------
s12 = prs.slides.add_slide(blank_layout)
add_header(s12, "SECTION 02", "2-4. Manifest 파일의 4대 기본 필드 및 YAML 구조")

m_items = [
    "1. apiVersion: <API 그룹/버전>",
    "   • 이 리소스를 생성하기 위한 API 스키마 버전 지정",
    "   • 예: v1 (Pod), apps/v1 (Deployment)",
    "2. kind: <리소스 종류>",
    "   • 생성하고자 하는 리소스의 타입 명시 (Pod, Service 등)",
    "3. metadata: <메타데이터>",
    "   • 리소스를 식별하기 위한 이름(name), 라벨(labels), 네임스페이스 지정",
    "4. spec: <상세 스펙>",
    "   • 리소스별 원하는 상태(Desired State) 및 사양 작성"
]
create_card(s12, Inches(0.8), Inches(1.6), Inches(5.7), Inches(5.2), title="📝 4대 필수 기본 필드", items=m_items, title_color=PRIMARY_BLUE)

yaml_code = """apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp-deployment
  labels:
    app: myapp
spec:
  replicas: 3
  selector:
    matchLabels:
      app: myapp
  template:
    metadata:
      labels:
        app: myapp
    spec:
      containers:
      - name: myapp-container
        image: myapp:latest
        imagePullPolicy: IfNotPresent"""
create_code_box(s12, Inches(6.833), Inches(1.6), Inches(5.7), Inches(5.2), "📄 Deployment Manifest 예시 (YAML)", yaml_code)


# ------------------- Slide 13: Section 03 Divider -------------------
create_section_slide(prs, 3, "쿠버네티스 주요 리소스 상세 분류", "Workload · Network · Storage · Config · Security · Scheduling · Monitoring")


# ------------------- Slide 14: 3-1. 리소스 분류 (1/3) — 워크로드 & 네트워크 -------------------
s14 = prs.slides.add_slide(blank_layout)
add_header(s14, "SECTION 03", "3-1. 리소스 분류 (1/3) — 워크로드 & 네트워크")

w_headers = ["구분", "리소스 이름", "설명 / 역할", "주요 특징"]
w_data = [
    ["워크로드", "Pod", "컨테이너 실행의 최소 단위", "하나 이상의 컨테이너, IP 공유, 볼륨 공유"],
    ["워크로드", "ReplicaSet", "지정한 수의 Pod 복제 유지", "Pod 개수 자동 관리, Deployment에 의해 관리됨"],
    ["워크로드", "Deployment", "파드 배포와 롤링 업데이트 관리", "ReplicaSet 생성/관리, 무중단 배포 및 버전 롤백"],
    ["워크로드", "StatefulSet", "상태를 가지는 Pod 관리", "고정 네트워크 ID, 안정된 스토리지, 순차 배포"],
    ["워크로드", "DaemonSet", "모든 노드에 1개의 Pod 실행", "로그 수집기, 모니터링 에이전트 배포에 사용"],
    ["워크로드", "Job / CronJob", "일회성 및 주기적 작업 수행", "배치 작업, 완료 시 종료, 크론 스케줄 기반"],
    ["네트워크", "Service", "Pod 집합에 네트워크 접근 제공", "ClusterIP, NodePort, LoadBalancer 모드 제공"],
    ["네트워크", "Ingress", "외부 요청을 클러스터 내부로 라우팅", "HTTP/HTTPS 라우팅, L7 도메인 기반 접근 제어"]
]
create_table(s14, Inches(0.8), Inches(1.6), Inches(11.733), Inches(5.2), w_headers, w_data, [Inches(1.5), Inches(1.8), Inches(4.2), Inches(4.233)])


# ------------------- Slide 15: 3-2. 리소스 분류 (2/3) — 스토리지 & 구성 -------------------
s15 = prs.slides.add_slide(blank_layout)
add_header(s15, "SECTION 03", "3-2. 리소스 분류 (2/3) — 스토리지 & 구성")

s_headers = ["구분", "리소스 이름", "설명 / 역할", "주요 특징"]
s_data = [
    ["스토리지", "Volume", "Pod 내 컨테이너 간 데이터 공유", "emptyDir, hostPath 등 다양한 타입 제공"],
    ["스토리지", "PersistentVolume (PV)", "클러스터에 프로비저닝된 스토리지", "관리자가 생성, 영속적 데이터 보존"],
    ["스토리지", "PersistentVolumeClaim (PVC)", "Pod에서 PV를 사용하기 위한 요청", "PV와 동적/정적 바인딩 지원"],
    ["스토리지", "StorageClass", "스토리지 프로비저닝 방식 정의", "PVC 요청 시 외부 스토리지 동적 생성"],
    ["구성", "ConfigMap", "환경 변수, 설정 파일 등 저장", "일반 설정값 주입, 코드와 설정 분리"],
    ["구성", "Secret", "민감한 데이터 저장 (비밀번호, 토큰 등)", "Base64 인코딩, 보안 접근 제어 적용"]
]
create_table(s15, Inches(0.8), Inches(1.6), Inches(11.733), Inches(5.2), s_headers, s_data, [Inches(1.5), Inches(2.2), Inches(4.0), Inches(4.033)])


# ------------------- Slide 16: 3-3. 리소스 분류 (3/3) — 스케줄링, 보안 및 관리 -------------------
s16 = prs.slides.add_slide(blank_layout)
add_header(s16, "SECTION 03", "3-3. 리소스 분류 (3/3) — 스케줄링, 보안 및 관리")

m_headers = ["구분", "리소스 이름", "설명 / 역할", "주요 특징"]
m_data = [
    ["스케줄링", "Node", "클러스터를 구성하는 물리/가상 머신", "Pod가 실제로 실행되는 컴퓨팅 서버"],
    ["스케줄링", "Namespace", "리소스 격리 및 관리 논리 단위", "팀/프로젝트/환경 별 자원 격리 및 권한 분리"],
    ["보안", "ServiceAccount", "Pod가 API 서버와 통신 시 사용하는 계정", "Pod 전용 RBAC 권한 부여 계정"],
    ["보안", "Role / ClusterRole", "리소스 접근 권한 규칙 정의", "Namespace 제한(Role) vs 클러스터 전역(ClusterRole)"],
    ["보안", "RoleBinding / ClusterRoleBinding", "계정(SA)에 Role 부여하여 권한 연결", "RBAC 권한 연결 핵심 오브젝트"],
    ["관리", "ResourceQuota", "네임스페이스 단위 리소스 사용 총량 제한", "CPU, 메모리, 스토리지 총용량 제한"],
    ["관리", "LimitRange", "Pod/컨테이너 자원 요청 기본값 정의", "자원 최소/최대 범위를 사전 규정"],
    ["관리", "HorizontalPodAutoscaler (HPA)", "부하에 따라 Pod 개수 자동 확장", "CPU/메모리/커스텀 메트릭 기반 오토스케일링"]
]
create_table(s16, Inches(0.8), Inches(1.6), Inches(11.733), Inches(5.2), m_headers, m_data, [Inches(1.5), Inches(2.5), Inches(3.8), Inches(3.933)])


# ------------------- Slide 17: Section 04 Divider -------------------
create_section_slide(prs, 4, "리소스 제어 및 자원 제한 (Requests & Limits)", "Requests vs Limits · CPU Throttling · Memory OOMKilled · Manifest 실습")


# ------------------- Slide 18: 4-1. 컨테이너 자원 제한 메커니즘 (Requests vs Limits) -------------------
s18 = prs.slides.add_slide(blank_layout)
add_header(s18, "SECTION 04", "4-1. 컨테이너 자원 제한 메커니즘 (Requests vs Limits)")

req_items = [
    "• 스케줄러(kube-scheduler)가 Pod를 배정할 노드를 선택하는 기준 자원",
    "• 노드의 남은 배정 가능 자원이 Requests보다 작으면 해당 노드에 배치 불가",
    "• 컨테이너에 최소한 보장되는 기본 자원 영역"
]
create_card(s18, Inches(0.8), Inches(1.6), Inches(5.7), Inches(2.5), title="📌 Requests (자원 요청량)", items=req_items, title_color=PRIMARY_BLUE)

lim_items = [
    "• 컨테이너가 노드 상에서 초과 사용할 수 없는 최대 자원 상한선",
    "• 노드에 여유 자원이 있더라도 Limits 설정값을 넘어서 사용할 수 없음",
    "• 자원 남용 방지 및 타 컨테이너의 자원 고갈 방지"
]
create_card(s18, Inches(6.833), Inches(1.6), Inches(5.7), Inches(2.5), title="🛑 Limits (자원 상한선)", items=lim_items, title_color=PRIMARY_BLUE)

cap_items = [
    "• Allocatable Space = Requests (배정 보장) + Burst Space (Limits 상한선까지 추가 사용 공간)",
    "• 스케줄러 판단: sum(Pod Requests) <= Node Allocatable Capacity 기준 배정",
    "• 런타임 제어: Limits를 기준으로 cgroups가 CPU 스로틀링 및 메모리 OOM 제어"
]
create_card(s18, Inches(0.8), Inches(4.3), Inches(11.733), Inches(2.6), title="📐 노드 자원 용량 구조 (Node Capacity Structure)", items=cap_items, title_color=PRIMARY_BLUE)


# ------------------- Slide 19: 4-2. CPU 제한 vs 메모리 제한 동작 차이 -------------------
s19 = prs.slides.add_slide(blank_layout)
add_header(s19, "SECTION 04", "4-2. CPU 제한 vs 메모리 제한 동작 차이")

cpu_mem_headers = ["구분", "자원 특성", "Requests 역할", "Limits 초과 시 동작 메커니즘"]
cpu_mem_data = [
    ["CPU", "압축 가능 (Compressible) 자원", "스케줄러가 노드의 CPU 여유분 판단", "Throttling (속도 제한):\n프로세스를 강제 종료하지 않고, CPU CFS quota를 제어하여 연산 처리 속도만 둔화시킴"],
    ["Memory", "압축 불가능 (Uncompressible) 자원", "스케줄러가 노드의 메모리 여유분 판단", "OOMKilled (Out of Memory Kill):\nOS 커널의 OOM Killer가 해당 컨테이너 프로세스를 즉시 강제 종료하고 파드 재시작"]
]
create_table(s19, Inches(0.8), Inches(1.6), Inches(11.733), Inches(5.2), cpu_mem_headers, cpu_mem_data, [Inches(1.5), Inches(2.5), Inches(3.2), Inches(4.533)])


# ------------------- Slide 20: 4-3. 실전 Deployment Manifest 작성 및 자원 제한 예시 -------------------
s20 = prs.slides.add_slide(blank_layout)
add_header(s20, "SECTION 04", "4-3. 실전 Deployment Manifest 작성 및 자원 제한 예시")

res_expl = [
    "1. resources.requests 설정:",
    "   • memory: '512Mi' (최소 512MB 메모리 보장)",
    "   • cpu: '500m' (0.5 vCPU = 500 millicores 보장)",
    "2. resources.limits 설정:",
    "   • memory: '1Gi' (최대 1GB 메모리 제한, 초과 시 OOMKilled)",
    "   • cpu: '1' (최대 1 vCPU 제한, 초과 시 Throttling)",
    "3. 프로덕션 환경 권장사항:",
    "   • Memory Limit과 Request를 유사하게 맞춰 OOM 예측 가능성 확보"
]
create_card(s20, Inches(0.8), Inches(1.6), Inches(5.7), Inches(5.2), title="⚙️ 자원 제한 설정 가이드", items=res_expl, title_color=PRIMARY_BLUE)

res_yaml = """apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
spec:
  replicas: 3
  selector:
    matchLabels:
      app: myapp
  template:
    metadata:
      labels:
        app: myapp
    spec:
      containers:
      - name: myapp-container
        image: myapp:latest
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1" """
create_code_box(s20, Inches(6.833), Inches(1.6), Inches(5.7), Inches(5.2), "📄 deployment.yaml (Resources 적용)", res_yaml)


# ------------------- Slide 21: Section 05 / WRAP-UP Divider -------------------
create_section_slide(prs, "WRAP-UP", "핵심 내용 요약 및 학습 로드맵", "주차별 강의 로드맵 · Week 05 핵심 요약 · Q & A")


# ------------------- Slide 22: WRAP-UP — 강좌의 학습 로드맵 -------------------
s22 = prs.slides.add_slide(blank_layout)
add_header(s22, "WRAP-UP", "강좌의 학습 로드맵 (Course Roadmap)")

roadmap_steps = [
    ("W1-2 (기초)", "클라우드 개요, 가상화 기술 이해", "NIST 5대 특성, IaaS/PaaS/SaaS, Hypervisor"),
    ("W3-4 (컨테이너화)", "Docker 컨테이너 이미지 제작 & 배포", "Dockerfile, Docker CLI, Container Runtime"),
    ("W5-7 (오케스트레이션)", "Kubernetes 운영, 관리 & KRM 실습", "[현재] KRM, Pod, Deployment, Service, Requests/Limits"),
    ("W8-11 (DevOps/CI-CD)", "GitHub Actions, GitOps, IaC, 보안", "CI/CD 파이프라인, Terraform, DevSecOps"),
    ("W12-13 (AI/ML)", "AI/ML 클라우드: MLOps, LLMOps", "Vertex AI, LLM 서빙, Kubeflow, Model Pipeline"),
    ("W14-15 (운영 고도화)", "모니터링·관측성·FinOps & 종합 평가", "Prometheus, Grafana, Cost Optimization, GCP 실습")
]

for i, (w_title, w_main, w_sub) in enumerate(roadmap_steps):
    col = i % 2
    row = i // 2
    left = Inches(0.8 + col * 5.97)
    top = Inches(1.6 + row * 1.8)
    
    card = s22.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, Inches(5.76), Inches(1.6))
    card.fill.solid()
    card.fill.fore_color.rgb = LIGHT_CARD_BG if row == 1 and col == 0 else CARD_BG
    card.line.color.rgb = PRIMARY_BLUE if row == 1 and col == 0 else CARD_BORDER
    card.line.width = Pt(2) if row == 1 and col == 0 else Pt(1)
    
    tf = card.text_frame
    tf.word_wrap = True
    tf.margin_left = Inches(0.2)
    tf.margin_top = Inches(0.15)
    
    p0 = tf.paragraphs[0]
    p0.text = w_title
    p0.font.size = Pt(13)
    p0.font.bold = True
    p0.font.color.rgb = PRIMARY_BLUE
    
    p1 = tf.add_paragraph()
    p1.text = w_main
    p1.font.size = Pt(13)
    p1.font.bold = True
    p1.font.color.rgb = DARK_TEXT
    
    p2 = tf.add_paragraph()
    p2.text = w_sub
    p2.font.size = Pt(11)
    p2.font.color.rgb = MUTED_TEXT


# ------------------- Slide 23: WRAP-UP — Week 05 핵심 내용 요약 -------------------
s23 = prs.slides.add_slide(blank_layout)
add_header(s23, "WRAP-UP", "Week 05 핵심 내용 요약")

s_items1 = [
    "• Manifest(선언) → API(수신) → Resource(타입) → Object(실체)로 연동되는 선언적 상태 관리 메커니즘",
    "• RESTful API 스펙 및 플러그인 인터페이스(CNI, CSI, CRI, CPI) 표준화로 인프라 독립성 확보"
]
create_card(s23, Inches(0.8), Inches(1.6), Inches(5.7), Inches(2.5), title="✓ KRM (Kubernetes Resource Model)", items=s_items1, title_color=PRIMARY_BLUE)

s_items2 = [
    "• Spec(원하는 상태)과 Status(현재 상태)를 지속적 비교 및 감시 (Observation Loop)",
    "• 차이(Drift) 발생 시 쿠버네티스가 자동으로 자가 복구(Self-healing)하여 Spec = Status 유지"
]
create_card(s23, Inches(6.833), Inches(1.6), Inches(5.7), Inches(2.5), title="✓ Spec vs Status & Reconciliation Loop", items=s_items2, title_color=PRIMARY_BLUE)

s_items3 = [
    "• Workload(Pod, Deployment, StatefulSet, DaemonSet, Job)",
    "• Network(Service, Ingress), Storage(PV, PVC, StorageClass), Config(ConfigMap, Secret), Security(RBAC)"
]
create_card(s23, Inches(0.8), Inches(4.3), Inches(5.7), Inches(2.6), title="✓ 7대 주요 리소스 분류", items=s_items3, title_color=PRIMARY_BLUE)

s_items4 = [
    "• Requests: 스케줄러가 노드 배치를 결정하는 최소 자원 보장 영역",
    "• Limits: 컨테이너 최대 상한선. 초과 시 CPU는 Throttling, Memory는 OOMKilled 발생"
]
create_card(s23, Inches(6.833), Inches(4.3), Inches(5.7), Inches(2.6), title="✓ 자원 제한 (Requests vs Limits)", items=s_items4, title_color=PRIMARY_BLUE)


# ------------------- Slide 24: Q & A -------------------
s24 = prs.slides.add_slide(blank_layout)
bg24 = s24.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
bg24.fill.solid()
bg24.fill.fore_color.rgb = DARK_BG
bg24.line.fill.background()

tb_q = s24.shapes.add_textbox(Inches(1.0), Inches(2.2), Inches(11.333), Inches(1.2))
p_q = tb_q.text_frame.paragraphs[0]
p_q.text = "Q & A"
p_q.font.size = Pt(54)
p_q.font.bold = True
p_q.font.color.rgb = PRIMARY_BLUE

tb_qt = s24.shapes.add_textbox(Inches(1.0), Inches(3.6), Inches(11.333), Inches(1.0))
p_qt = tb_qt.text_frame.paragraphs[0]
p_qt.text = "질문 및 토론 시간"
p_qt.font.size = Pt(28)
p_qt.font.bold = True
p_qt.font.color.rgb = WHITE

tb_qc = s24.shapes.add_textbox(Inches(1.0), Inches(4.8), Inches(11.333), Inches(1.5))
p_qc = tb_qc.text_frame.paragraphs[0]
p_qc.text = "강의 내용 중 궁금한 점이나 의견이 있으시면 편하게 질문해 주세요.\n\n담당교수: 정선태 (cst@ssu.ac.kr | 형암공학관 1310호)"
p_qc.font.size = Pt(16)
p_qc.font.color.rgb = RGBColor(148, 163, 184)


# Save Presentation
output_filename = "쿠버네티스_리소스모델_mod.pptx"
prs.save(output_filename)
print(f"Presentation saved successfully as {output_filename}")