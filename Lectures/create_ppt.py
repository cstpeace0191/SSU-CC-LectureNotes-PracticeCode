import sys
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor

def create_observability_presentation():
    prs = Presentation()
    prs.slide_width = Inches(13.333)  # 16:9 Widescreen
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    # 흰색 배경 설정
    def set_white_bg(slide):
        background = slide.background
        fill = background.fill
        fill.solid()
        fill.fore_color.rgb = RGBColor(255, 255, 255)

    # 슬라이드 헤더 추가
    def add_header(slide, title_text):
        tx_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.5), Inches(11.733), Inches(0.9))
        tf = tx_box.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
        p = tf.paragraphs[0]
        p.text = title_text
        p.font.size = Pt(26)
        p.font.bold = True
        p.font.color.rgb = RGBColor(0, 51, 102)  # 다크 네이비 포인트 컬러
        p.font.name = "Malgun Gothic"

    # 본문 텍스트 추가 (최소 18pt 이상)
    def add_bullet_content(slide, paragraphs_list, top_in=1.5, height_in=5.5):
        body_box = slide.shapes.add_textbox(Inches(0.8), Inches(top_in), Inches(11.733), Inches(height_in))
        tf = body_box.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
        
        for i, item in enumerate(paragraphs_list):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.font.name = "Malgun Gothic"
            
            if isinstance(item, tuple):
                text, size, bold, color, is_code = item
                p.text = text
                p.font.size = Pt(size)
                p.font.bold = bold
                p.font.color.rgb = color
                if is_code:
                    p.font.name = "Consolas"
            else:
                p.text = str(item)
                p.font.size = Pt(18)
                p.font.color.rgb = RGBColor(17, 17, 17) # 검정색 텍스트
            
            p.space_after = Pt(8)

    slides_spec = []

    # Slide 1: 표지
    slides_spec.append({
        "type": "title",
        "title": "분산 환경에서의 Observability\n핵심 토픽 및 기술 체계",
        "subtitle": "클라우드, 쿠버네티스, 마이크로서비스 관측성을 구성하는 7대 핵심 분야",
        "presenter": "Observability Architecture Guide"
    })

    # Slide 2: 목차
    slides_spec.append({
        "type": "standard",
        "title": "Slide 2: Observability가 다루는 7대 핵심 토픽",
        "content": [
            ("1. 텔레메트리 데이터 요소 (Telemetry Signals)", 20, True, RGBColor(0, 51, 102), False),
            ("2. 수집 및 계측 표준 (Instrumentation & Standards)", 20, True, RGBColor(0, 51, 102), False),
            ("3. 쿠버네티스 및 인프라 관측 (Infrastructure & K8s)", 20, True, RGBColor(0, 51, 102), False),
            ("4. 데이터 파이프라인 및 가공 (Pipeline & Processing)", 20, True, RGBColor(0, 51, 102), False),
            ("5. 데이터 저장 및 쿼리 시스템 (Storage & Query Engines)", 20, True, RGBColor(0, 51, 102), False),
            ("6. 시각화, 알림 및 SRE 프레임워크 (Analytics & SRE)", 20, True, RGBColor(0, 51, 102), False),
            ("7. 엔터프라이즈 및 최신 트렌드 (FinOps, Security, AI)", 20, True, RGBColor(0, 51, 102), False)
        ]
    })

    # Slide 3: Category 1
    slides_spec.append({
        "type": "standard",
        "title": "Slide 3: 1. 텔레메트리 데이터 요소 (Telemetry Signals)",
        "content": [
            ("• Metrics (지표):", 20, True, RGBColor(0, 51, 102), False),
            ("   - 수치형 시계열 데이터로 시스템 전체의 상태, 트래픽(RPS), 에러율, 자원 사용량 파악.", 18, False, RGBColor(17, 17, 17), False),
            ("• Logs (로그):", 20, True, RGBColor(0, 51, 102), False),
            ("   - 타임스탬프 기반 이벤트의 상세 텍스트 기록 (원인 파악 및 세부 맥락 분석용).", 18, False, RGBColor(17, 17, 17), False),
            ("• Traces (트레이스):", 20, True, RGBColor(0, 51, 102), False),
            ("   - 사용자 요청이 여러 마이크로서비스를 통과하는 전체 실행 경로 및 구간 지연 추적.", 18, False, RGBColor(17, 17, 17), False),
            ("• Continuous Profiling & Events:", 20, True, RGBColor(0, 51, 102), False),
            ("   - 운영 환경에서 CPU/메모리 플레임그래프 수집 및 Pod 재시작 등 상태 변화 기록.", 18, False, RGBColor(17, 17, 17), False)
        ]
    })

    # Slide 4: Category 2
    slides_spec.append({
        "type": "standard",
        "title": "Slide 4: 2. 수집 및 계측 표준 (Instrumentation & Standards)",
        "content": [
            ("• OpenTelemetry (OTel):", 20, True, RGBColor(0, 51, 102), False),
            ("   - CNCF 벤더 중립 글로벌 수집 표준 API/SDK 및 OTLP 프로토콜 체계.", 18, False, RGBColor(17, 17, 17), False),
            ("• eBPF (Extended Berkeley Packet Filter):", 20, True, RGBColor(0, 51, 102), False),
            ("   - 소스 코드 수정 없이 리눅스 커널 공간에서 수집하는 Zero-Code 관측 기술.", 18, False, RGBColor(17, 17, 17), False),
            ("• Auto vs. Manual Instrumentation:", 20, True, RGBColor(0, 51, 102), False),
            ("   - 자바 에이전트/파이썬 몽키패칭 자동 수집 + 도메인 로직 수동 계측 하이브리드.", 18, False, RGBColor(17, 17, 17), False),
            ("• K8s Operators:", 20, True, RGBColor(0, 51, 102), False),
            ("   - OpenTelemetry Operator 등을 활용한 관측 에이전트 자동 주입 및 lifecycle 관리.", 18, False, RGBColor(17, 17, 17), False)
        ]
    })

    # Slide 5: Category 3
    slides_spec.append({
        "type": "standard",
        "title": "Slide 5: 3. 쿠버네티스 및 인프라 관측 (Infrastructure & K8s)",
        "content": [
            ("• Node & OS Level:", 20, True, RGBColor(0, 51, 102), False),
            ("   - Node Exporter 기반 CPU, Memory, Disk I/O, Network 인터페이스 모니터링.", 18, False, RGBColor(17, 17, 17), False),
            ("• K8s Control Plane & Objects:", 20, True, RGBColor(0, 51, 102), False),
            ("   - kube-state-metrics, cAdvisor 활용 (Pod Restart, OOMKilled, Replica 상태 관제).", 18, False, RGBColor(17, 17, 17), False),
            ("• Service Mesh 관측성:", 20, True, RGBColor(0, 51, 102), False),
            ("   - Istio, Envoy 프록시를 통한 mTLS 통신, 트래픽 라우팅, 서킷 브레이커, 프록시 트레이스.", 18, False, RGBColor(17, 17, 17), False)
        ]
    })

    # Slide 6: Category 4
    slides_spec.append({
        "type": "standard",
        "title": "Slide 6: 4. 데이터 파이프라인 및 가공 (Pipeline & Processing)",
        "content": [
            ("• Collector Architecture:", 20, True, RGBColor(0, 51, 102), False),
            ("   - Node 단위 Agent (DaemonSet) + Central Gateway 2-Tier 파이프라인 아키텍처.", 18, False, RGBColor(17, 17, 17), False),
            ("• Sampling Strategies (샘플링 전략):", 20, True, RGBColor(0, 51, 102), False),
            ("   - Head-based (시작 시점 수집 판단) vs Tail-based (종료 후 에러/지연 100% 수집).", 18, False, RGBColor(17, 17, 17), False),
            ("• PII & Data Sanitization:", 20, True, RGBColor(0, 51, 102), False),
            ("   - Collector 레이어에서 개인정보(주민등록번호, 카드번호) 정규식 마스킹 및 보안 정제.", 18, False, RGBColor(17, 17, 17), False)
        ]
    })

    # Slide 7: Category 5
    slides_spec.append({
        "type": "standard",
        "title": "Slide 7: 5. 데이터 저장 및 쿼리 시스템 (Storage & Query Engines)",
        "content": [
            ("• Metrics Engine: Prometheus, Grafana Mimir, Thanos, VictoriaMetrics (PromQL)", 18, True, RGBColor(0, 51, 102), False),
            ("• Logs Engine: Grafana Loki, Elasticsearch, OpenSearch, Vector (LogQL)", 18, True, RGBColor(0, 51, 102), False),
            ("• Traces Engine: Grafana Tempo, Jaeger (TraceQL)", 18, True, RGBColor(0, 51, 102), False),
            ("", 12, False, RGBColor(0,0,0), False),
            ("• Object Storage 중심 아키텍처의 혁신:", 20, True, RGBColor(17, 17, 17), False),
            ("   - AWS S3, GCS 등 저렴한 오브젝트 스토리지를 활용한 대용량 보관.", 18, False, RGBColor(17, 17, 17), False),
            ("   - 무거운 풀 인덱싱 대신 Indexless / Label-based 저장 구조로 운영 비용 극대화 절감.", 18, True, RGBColor(0, 102, 51), False)
        ]
    })

    # Slide 8: Category 6
    slides_spec.append({
        "type": "standard",
        "title": "Slide 8: 6. 시각화, 알림 및 SRE 프레임워크 (Analytics & SRE)",
        "content": [
            ("• Unified Dashboards (통합 시각화):", 20, True, RGBColor(0, 51, 102), False),
            ("   - Grafana 기반 메트릭-트레이스-로그 심리스 Context Correlation (Exemplar, Derived Fields).", 18, False, RGBColor(17, 17, 17), False),
            ("• Alerting & Routing (지능형 알림):", 20, True, RGBColor(0, 51, 102), False),
            ("   - Alertmanager 알림 그룹화(Grouping), 노이즈 억제(Inhibition), Silencing 라우팅.", 18, False, RGBColor(17, 17, 17), False),
            ("• Service Level Management (SRE 프레임워크):", 20, True, RGBColor(0, 51, 102), False),
            ("   - SLI (지표), SLO (목표), SLA (합의) 및 Error Budget (에러 예산) 기반 관제 체계.", 18, False, RGBColor(17, 17, 17), False)
        ]
    })

    # Slide 9: Category 7
    slides_spec.append({
        "type": "standard",
        "title": "Slide 9: 7. 엔터프라이즈 및 최신 트렌드 (FinOps, Security, AI)",
        "content": [
            ("• FinOps (비용 최적화):", 20, True, RGBColor(0, 51, 102), False),
            ("   - High-Cardinality 메트릭 제어, 데이터 보관 주기(TTL) 분리, Downsampling 적용.", 18, False, RGBColor(17, 17, 17), False),
            ("• AI / LLM Observability (GenAI):", 20, True, RGBColor(0, 51, 102), False),
            ("   - TTFT(첫 토큰 시간), 프롬프트/완료 토큰 소비 비용, RAG 검색 품질, Agent 추론 경로.", 18, False, RGBColor(17, 17, 17), False),
            ("• AIOps & Root Cause Analysis (자동 진단):", 20, True, RGBColor(0, 51, 102), False),
            ("   - ML/LLM 알고리즘 기반 장애 원인 자동 분석 및 동적 이상 감지(Anomaly Detection).", 18, False, RGBColor(17, 17, 17), False)
        ]
    })

    # Slide 10: 결론
    slides_spec.append({
        "type": "standard",
        "title": "Slide 10: 결론 및 핵심 요약",
        "content": [
            ("1. Observability는 단순 툴 설치가 아닌 데이터 기반의 문화이자 체계입니다.", 20, True, RGBColor(0, 51, 102), False),
            ("2. OpenTelemetry 수집 표준화로 특정 APM 벤더 종속성을 탈피합니다.", 20, True, RGBColor(0, 51, 102), False),
            ("3. 메트릭, 트레이스, 로그의 심리스한 연동으로 장애 복구 시간(MTTR)을 단축합니다.", 20, True, RGBColor(0, 51, 102), False),
            ("4. S3 기반 저렴한 백엔드와 Tail-Sampling으로 FinOps 비용을 통제합니다.", 20, True, RGBColor(0, 51, 102), False),
            ("5. LLM 및 AI 워크로드 관측성까지 확장하여 차세대 통합 관제탑을 완성합니다.", 20, True, RGBColor(0, 102, 51), False)
        ]
    })

    # 슬라이드 생성 루프
    for idx, spec in enumerate(slides_spec):
        slide = prs.slides.add_slide(blank_layout)
        set_white_bg(slide)

        if spec["type"] == "title":
            title_box = slide.shapes.add_textbox(Inches(1.0), Inches(1.8), Inches(11.333), Inches(2.5))
            tf = title_box.text_frame
            tf.word_wrap = True
            p = tf.paragraphs[0]
            p.text = spec["title"]
            p.font.size = Pt(32)
            p.font.bold = True
            p.font.color.rgb = RGBColor(0, 51, 102)
            p.font.name = "Malgun Gothic"
            
            sub_box = slide.shapes.add_textbox(Inches(1.0), Inches(4.5), Inches(11.333), Inches(1.5))
            tf_sub = sub_box.text_frame
            tf_sub.word_wrap = True
            p_sub = tf_sub.paragraphs[0]
            p_sub.text = spec["subtitle"]
            p_sub.font.size = Pt(22)
            p_sub.font.color.rgb = RGBColor(17, 17, 17)
            p_sub.font.name = "Malgun Gothic"
            
            p_pres = tf_sub.add_paragraph()
            p_pres.text = "\n" + spec["presenter"]
            p_pres.font.size = Pt(18)
            p_pres.font.color.rgb = RGBColor(100, 100, 100)
            p_pres.font.name = "Malgun Gothic"
        else:
            add_header(slide, spec["title"])
            add_bullet_content(slide, spec["content"])

    filename = "Observability.pptx"
    prs.save(filename)
    print(f"성공적으로 '{filename}' (총 {len(prs.slides)}장) 슬라이드가 생성되었습니다.")

if __name__ == "__main__":
    create_observability_presentation()