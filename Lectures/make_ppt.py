from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

# 1. 프레젠테이션 생성 (16:9 비율)
prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)

slide_layout = prs.slide_layouts[6] # Blank 레이아웃
slide = prs.slides.add_slide(slide_layout)

# Color Palette
DARK_BLUE = RGBColor(15, 23, 42)
LIGHT_BG = RGBColor(241, 245, 249)
BORDER_BLUE = RGBColor(59, 130, 246)
TEXT_MAIN = RGBColor(30, 41, 59)
TEXT_MUTED = RGBColor(100, 116, 139)

# --- Title ---
title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.6), Inches(11.7), Inches(1.0))
tf = title_box.text_frame
tf.word_wrap = True

p1 = tf.paragraphs[0]
p1.text = "쿠버네티스 리소스 모델 (Kubernetes Resource Model)"
p1.font.bold = True
p1.font.size = Pt(28)
p1.font.color.rgb = DARK_BLUE

p2 = tf.add_paragraph()
p2.text = "모든 인프라를 표준 객체로 선언하고, 컴퓨팅 자원을 효율적으로 배분하는 메커니즘"
p2.font.size = Pt(14)
p2.font.color.rgb = TEXT_MUTED
p2.space_before = Pt(4)

# --- Left Card (KRM API) ---
left_card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.8), Inches(5.6), Inches(4.3))
left_card.fill.solid()
left_card.fill.fore_color.rgb = LIGHT_BG
left_card.line.color.rgb = BORDER_BLUE
left_card.line.width = Pt(1.5)

tf_left = left_card.text_frame
tf_left.word_wrap = True
tf_left.margin_left = Inches(0.3)
tf_left.margin_top = Inches(0.3)

p = tf_left.paragraphs[0]
p.text = "1. API 및 객체 모델 (KRM)"
p.font.bold = True
p.font.size = Pt(18)
p.font.color.rgb = DARK_BLUE

items_left = [
    ("선언형 제어 구조 (Spec vs Status)", True),
    (" • spec : 엔지니어가 정의한 '원하는 상태'", False),
    (" • status : 시스템이 감시하는 '현재 상태'", False),
    ("조정 루프 (Reconciliation Loop)", True),
    (" • spec과 status를 지속 비교하여 자동 복구 (Self-Healing)", False),
    ("표준 객체 구조", True),
    (" • apiVersion, kind, metadata, spec, status 5개 필드 통일", False),
]

for text, is_bold in items_left:
    p = tf_left.add_paragraph()
    p.text = text
    p.font.size = Pt(12)
    p.font.bold = is_bold
    p.font.color.rgb = TEXT_MAIN
    p.space_before = Pt(6 if is_bold else 2)

# --- Right Card (Compute Resource) ---
right_card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.9), Inches(1.8), Inches(5.6), Inches(4.3))
right_card.fill.solid()
right_card.fill.fore_color.rgb = LIGHT_BG
right_card.line.color.rgb = BORDER_BLUE
right_card.line.width = Pt(1.5)

tf_right = right_card.text_frame
tf_right.word_wrap = True
tf_right.margin_left = Inches(0.3)
tf_right.margin_top = Inches(0.3)

p = tf_right.paragraphs[0]
p.text = "2. 컴퓨팅 자원 관리 (Compute Resource)"
p.font.bold = True
p.font.size = Pt(18)
p.font.color.rgb = DARK_BLUE

items_right = [
    ("Requests vs Limits", True),
    (" • Requests (최소 보장) : 노드 스케줄링 배치 기준", False),
    (" • Limits (최대 한도) : 자원 사용 한계선", False),
    ("   - CPU 초과 시 : Throttling (속도 제한)", False),
    ("   - Memory 초과 시 : OOM Kill (강제 재부팅)", False),
    ("QoS (Quality of Service) 우선순위", True),
    (" • Guaranteed (1순위) > Burstable > BestEffort (강제종료 1순위)", False),
]

for text, is_bold in items_right:
    p = tf_right.add_paragraph()
    p.text = text
    p.font.size = Pt(12)
    p.font.bold = is_bold
    p.font.color.rgb = TEXT_MAIN
    p.space_before = Pt(6 if is_bold else 2)

# --- Bottom Key Takeaway ---
bottom_card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(6.25), Inches(11.7), Inches(0.7))
bottom_card.fill.solid()
bottom_card.fill.fore_color.rgb = DARK_BLUE
bottom_card.line.fill.background()

tf_bottom = bottom_card.text_frame
tf_bottom.word_wrap = True
tf_bottom.margin_left = Inches(0.3)
tf_bottom.margin_top = Inches(0.15)

p = tf_bottom.paragraphs[0]
p.text = "💡 Key Takeaway : 모든 인프라 객체를 선언형 표준 규격(Spec/Status)으로 통합 관리하고, Requests/Limits 기반으로 자원을 안정적으로 제어함."
p.font.size = Pt(11)
p.font.bold = True
p.font.color.rgb = RGBColor(255, 255, 255)

# 저장
prs.save("k8s_resource_model.pptx")
print("k8s_resource_model.pptx 파일 생성 완료!")