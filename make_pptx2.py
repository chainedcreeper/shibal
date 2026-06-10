"""
LLM 소개 세미나 PPT — 8장
python make_pptx2.py
"""
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

BG_DARK  = RGBColor(0x0f, 0x0f, 0x1a)
BG_SLIDE = RGBColor(0x11, 0x11, 0x22)
BLUE     = RGBColor(0x7e, 0xb8, 0xff)
BLUE_MID = RGBColor(0x3a, 0x7a, 0xff)
TEXT     = RGBColor(0xe8, 0xe8, 0xf0)
TEXT_SUB = RGBColor(0xc8, 0xd8, 0xf0)
DIM      = RGBColor(0x70, 0x80, 0xa0)
GREEN    = RGBColor(0x5d, 0xdf, 0x5d)
ORANGE   = RGBColor(0xff, 0xaa, 0x40)
PURPLE   = RGBColor(0xd2, 0xa8, 0xff)
TEAL     = RGBColor(0x4a, 0xd4, 0xc0)
YELLOW   = RGBColor(0xff, 0xd0, 0x50)
RED      = RGBColor(0xff, 0x70, 0x70)
CARD     = RGBColor(0x1a, 0x1e, 0x30)
BORDER   = RGBColor(0x2a, 0x35, 0x60)

W = Inches(13.33)
H = Inches(7.5)


def new_slide(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    for ph in slide.placeholders:
        ph._element.getparent().remove(ph._element)
    return slide

def bg(slide, color=BG_SLIDE):
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = color

def box(slide, l, t, w, h, fill=None, line=None, lw=Pt(1)):
    s = slide.shapes.add_shape(1, l, t, w, h)
    s.fill.solid() if fill else s.fill.background()
    if fill: s.fill.fore_color.rgb = fill
    if line: s.line.color.rgb = line; s.line.width = lw
    else: s.line.fill.background()
    return s

def T(slide, t, l, top, w, h,
      size=Pt(18), bold=False, color=TEXT, align=PP_ALIGN.LEFT):
    tb = slide.shapes.add_textbox(l, top, w, h)
    tb.word_wrap = True
    tf = tb.text_frame; tf.word_wrap = True
    p = tf.paragraphs[0]; p.alignment = align
    r = p.add_run()
    r.text = t; r.font.size = size
    r.font.bold = bold; r.font.color.rgb = color
    return tb

def ML(slide, items, l, top, w, h, size=Pt(16), color=TEXT_SUB):
    tb = slide.shapes.add_textbox(l, top, w, h)
    tb.word_wrap = True
    tf = tb.text_frame; tf.word_wrap = True
    first = True
    for item in items:
        if isinstance(item, str):
            t, b, c = item, False, color
        else:
            t = item[0]
            b = item[1] if len(item) > 1 else False
            c = item[2] if len(item) > 2 else color
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False; p.space_after = Pt(6)
        r = p.add_run()
        r.text = t; r.font.size = size
        r.font.bold = b; r.font.color.rgb = c

def hdr(slide, title, subtitle=None):
    bg(slide)
    box(slide, 0, 0, W, Inches(0.1), fill=BLUE_MID)
    T(slide, title,
      Inches(0.7), Inches(0.22), Inches(11.9), Inches(0.52),
      size=Pt(28), bold=True, color=TEXT)
    if subtitle:
        T(slide, subtitle,
          Inches(0.7), Inches(0.76), Inches(11.9), Inches(0.3),
          size=Pt(14), color=DIM)
        box(slide, Inches(0.7), Inches(1.1), Inches(12.0), Pt(1.2), fill=BLUE_MID)
        return Inches(1.28)
    box(slide, Inches(0.7), Inches(0.78), Inches(12.0), Pt(1.2), fill=BLUE_MID)
    return Inches(0.96)


# ════════════════════════════════════════════════════
# S1 — 타이틀
# ════════════════════════════════════════════════════
def s1(prs):
    slide = new_slide(prs)
    bg(slide, BG_DARK)
    box(slide, 0, 0, W, Inches(0.18), fill=BLUE_MID)
    box(slide, 0, Inches(7.32), W, Inches(0.18), fill=BLUE_MID)

    T(slide, "LLM, 어떻게 활용할 수 있을까",
      Inches(1.4), Inches(1.7), Inches(10.5), Inches(0.7),
      size=Pt(28), color=DIM)
    T(slide, "개념부터 생태계까지",
      Inches(1.4), Inches(2.35), Inches(10.5), Inches(1.1),
      size=Pt(56), bold=True, color=BLUE)
    T(slide, "2026. 06. 11",
      Inches(1.4), Inches(6.88), Inches(4), Inches(0.35),
      size=Pt(14), color=DIM)


# ════════════════════════════════════════════════════
# S2 — 머신러닝 / LLM 이란?
# ════════════════════════════════════════════════════
def s2(prs):
    slide = new_slide(prs)
    y0 = hdr(slide, "머신러닝과 LLM")

    # 왼쪽: ML 개념
    box(slide, Inches(0.7), y0+Inches(0.15),
        Inches(5.7), Inches(5.6),
        fill=CARD, line=BORDER)
    T(slide, "머신러닝",
      Inches(1.0), y0+Inches(0.38),
      Inches(5.1), Inches(0.5),
      size=Pt(26), bold=True, color=BLUE)
    ML(slide, [
        "데이터로부터 규칙을 스스로 학습",
        "",
        ("지도학습", True, BLUE),
        "  정답 레이블로 학습  →  분류, 예측",
        ("비지도학습", True, BLUE),
        "  레이블 없이 패턴 발견  →  클러스터링",
        ("강화학습", True, BLUE),
        "  보상 신호로 행동 최적화",
        "",
        ("딥러닝", True, ORANGE),
        "  신경망 기반 머신러닝",
        "  이미지·음성·텍스트 처리에 강함",
    ], Inches(1.0), y0+Inches(0.98),
       Inches(5.1), Inches(4.3),
       size=Pt(15), color=TEXT_SUB)

    # 오른쪽: LLM 개념
    box(slide, Inches(6.73), y0+Inches(0.15),
        Inches(5.93), Inches(5.6),
        fill=RGBColor(0x0f,0x1a,0x30), line=BLUE_MID)
    T(slide, "LLM",
      Inches(7.03), y0+Inches(0.38),
      Inches(5.3), Inches(0.5),
      size=Pt(26), bold=True, color=BLUE)
    T(slide, "Large Language Model",
      Inches(7.03), y0+Inches(0.88),
      Inches(5.3), Inches(0.3),
      size=Pt(14), color=DIM)
    ML(slide, [
        "수천억 개 텍스트로 사전학습된",
        "초거대 언어 모델",
        "",
        ("대표 모델", True, BLUE),
        "  GPT-4, Claude, Gemini  (클로즈드)",
        "  LLaMA, Qwen, Mistral   (오픈소스)",
        "",
        ("핵심 능력", True, BLUE),
        "  자연어 이해 & 생성",
        "  지식 내재화",
        "  다양한 태스크 범용 처리",
        "",
        "학습 데이터: 인터넷 텍스트 수조 토큰",
        "파라미터:   수십억 ~ 수천억 개",
    ], Inches(7.03), y0+Inches(1.22),
       Inches(5.3), Inches(4.2),
       size=Pt(15), color=TEXT_SUB)


# ════════════════════════════════════════════════════
# S3 — LLM 동작 구조
# ════════════════════════════════════════════════════
def s3(prs):
    slide = new_slide(prs)
    y0 = hdr(slide, "LLM 동작 구조", "Transformer 기반 언어 모델")

    # Transformer 구조 개념
    box(slide, Inches(0.7), y0+Inches(0.15),
        Inches(5.7), Inches(5.45),
        fill=CARD, line=BORDER)
    T(slide, "Transformer",
      Inches(1.0), y0+Inches(0.35),
      Inches(5.1), Inches(0.48),
      size=Pt(24), bold=True, color=PURPLE)
    ML(slide, [
        "LLM의 핵심 구조 (2017, Google)",
        "",
        ("Self-Attention", True, PURPLE),
        "  입력 토큰들 간 관계를 학습",
        "  멀리 떨어진 단어도 연결 가능",
        "",
        ("Feed-Forward Network", True, PURPLE),
        "  각 토큰의 표현을 변환",
        "",
        ("레이어를 쌓을수록", True, PURPLE),
        "  추상적인 개념 표현 가능",
        "  7B = 약 32개 레이어",
    ], Inches(1.0), y0+Inches(0.93),
       Inches(5.1), Inches(4.2),
       size=Pt(15), color=TEXT_SUB)

    # 학습 과정
    box(slide, Inches(6.73), y0+Inches(0.15),
        Inches(5.93), Inches(2.55),
        fill=RGBColor(0x11,0x1e,0x11), line=RGBColor(0x2a,0x5c,0x2a))
    T(slide, "사전학습 (Pre-training)",
      Inches(7.03), y0+Inches(0.35),
      Inches(5.3), Inches(0.4),
      size=Pt(18), bold=True, color=GREEN)
    ML(slide, [
        "다음 토큰 예측을 반복하며 언어 습득",
        "수천억 토큰  ·  수백만 달러  ·  수 개월",
        "→  GPT, LLaMA 등 베이스 모델 탄생",
    ], Inches(7.03), y0+Inches(0.85),
       Inches(5.3), Inches(1.6),
       size=Pt(14.5), color=TEXT_SUB)

    box(slide, Inches(6.73), y0+Inches(2.85),
        Inches(5.93), Inches(2.75),
        fill=RGBColor(0x0f,0x1a,0x30), line=BORDER)
    T(slide, "토큰화 & 추론",
      Inches(7.03), y0+Inches(3.05),
      Inches(5.3), Inches(0.4),
      size=Pt(18), bold=True, color=BLUE)
    ML(slide, [
        "텍스트  →  토큰(숫자) 변환",
        "한국어 1글자  ≈  1~3 토큰",
        "",
        "토큰을 하나씩 순서대로 생성",
        "Greedy / Sampling / Beam Search",
        "temperature로 창의성 조절",
    ], Inches(7.03), y0+Inches(3.55),
       Inches(5.3), Inches(1.9),
       size=Pt(14.5), color=TEXT_SUB)


# ════════════════════════════════════════════════════
# S4 — LLM 성능 향상 방법들
# ════════════════════════════════════════════════════
def s4(prs):
    slide = new_slide(prs)
    y0 = hdr(slide, "LLM 활용 & 성능 향상 방법")

    methods = [
        ("프롬프트\n엔지니어링", TEAL, RGBColor(0x0f,0x1e,0x1e), RGBColor(0x2a,0x5c,0x5c),
         [
             "비용  없음",
             "난이도  낮음",
             "",
             "시스템 프롬프트",
             "Few-shot 예시",
             "Chain-of-Thought",
             "Role prompting",
             "",
             "한계: 모델 능력",
             "자체는 그대로",
         ]),
        ("RAG", BLUE, RGBColor(0x0f,0x1a,0x30), BORDER,
         [
             "비용  서버",
             "난이도  중간",
             "",
             "외부 문서 검색",
             "→ 컨텍스트로 주입",
             "",
             "최신 정보 반영",
             "할루시네이션 감소",
             "",
             "한계: 검색 실패 시",
             "여전히 취약",
         ]),
        ("파인튜닝", GREEN, RGBColor(0x11,0x1e,0x11), RGBColor(0x2a,0x5c,0x2a),
         [
             "비용  GPU",
             "난이도  중간",
             "",
             "LoRA / QLoRA",
             "도메인 특화 학습",
             "포맷·스타일 고정",
             "",
             "모델 능력 자체",
             "향상 가능",
             "",
             "데이터 품질이 전부",
         ]),
        ("에이전트\n/ 툴 사용", ORANGE, RGBColor(0x1e,0x14,0x08), RGBColor(0x5c,0x3a,0x0d),
         [
             "비용  API",
             "난이도  중간~높음",
             "",
             "웹 검색, 코드 실행",
             "DB 조회, API 호출",
             "",
             "LangChain",
             "LlamaIndex",
             "AutoGen",
             "",
             "복잡한 태스크 처리",
         ]),
        ("지식 증류\n(KD)", PURPLE, RGBColor(0x1a,0x11,0x2a), RGBColor(0x5a,0x2a,0x8a),
         [
             "비용  Teacher GPU",
             "난이도  높음",
             "",
             "큰 모델 → 작은 모델",
             "추론 능력 이식",
             "",
             "CoT Distillation",
             "<think> 포함 학습",
             "",
             "DeepSeek-R1",
             "Qwen3 distill",
         ]),
    ]

    cw = Inches(2.3); ch = Inches(5.45)
    cx = Inches(0.7)
    for name, acc, bg_c, bd, bullets in methods:
        box(slide, cx, y0+Inches(0.12), cw, ch, fill=bg_c, line=bd, lw=Pt(1.5))
        T(slide, name,
          cx+Inches(0.15), y0+Inches(0.28),
          cw-Inches(0.3), Inches(0.75),
          size=Pt(17), bold=True, color=acc, align=PP_ALIGN.CENTER)
        box(slide, cx+Inches(0.15), y0+Inches(1.08),
            cw-Inches(0.3), Pt(1), fill=acc)
        ML(slide, bullets,
           cx+Inches(0.15), y0+Inches(1.22),
           cw-Inches(0.3), ch-Inches(1.35),
           size=Pt(13), color=TEXT_SUB)
        cx += cw + Inches(0.2)


# ════════════════════════════════════════════════════
# S5 — 라이브러리 & 도구
# ════════════════════════════════════════════════════
def s5(prs):
    slide = new_slide(prs)
    y0 = hdr(slide, "라이브러리 & 도구 생태계")

    # 학습 도구
    box(slide, Inches(0.7), y0+Inches(0.15),
        Inches(5.8), Inches(2.55),
        fill=CARD, line=BORDER)
    T(slide, "학습",
      Inches(1.0), y0+Inches(0.3),
      Inches(5.2), Inches(0.38),
      size=Pt(18), bold=True, color=BLUE)
    train_libs = [
        ("PEFT",    "HuggingFace 공식  LoRA 구현 표준",           BLUE),
        ("TRL",     "SFT · DPO · RLHF 통합 학습",                PURPLE),
        ("Unsloth", "LoRA 2~5배 가속  Flash Attention 내장",       GREEN),
        ("Axolotl", "YAML 설정만으로 파인튜닝  멀티GPU 지원",      TEAL),
    ]
    for i, (name, desc, acc) in enumerate(train_libs):
        ry = y0+Inches(0.78)+Inches(0.42)*i
        T(slide, name, Inches(1.0), ry, Inches(1.3), Inches(0.38),
          size=Pt(14), bold=True, color=acc)
        T(slide, desc, Inches(2.4), ry, Inches(3.8), Inches(0.38),
          size=Pt(13), color=DIM)

    # 서빙 도구
    box(slide, Inches(0.7), y0+Inches(2.85),
        Inches(5.8), Inches(2.75),
        fill=CARD, line=BORDER)
    T(slide, "서빙",
      Inches(1.0), y0+Inches(3.0),
      Inches(5.2), Inches(0.38),
      size=Pt(18), bold=True, color=ORANGE)
    serve_libs = [
        ("llama.cpp", "C++ 추론 엔진  GGUF 양자화 포맷",          ORANGE),
        ("Ollama",    "로컬 LLM 서버  설치 1분  REST API",         YELLOW),
        ("vLLM",      "고성능 서버  PagedAttention  OpenAI 호환",  RED),
        ("LM Studio", "GUI 기반 로컬 실행  프로토타이핑용",         DIM),
    ]
    for i, (name, desc, acc) in enumerate(serve_libs):
        ry = y0+Inches(3.52)+Inches(0.42)*i
        T(slide, name, Inches(1.0), ry, Inches(1.5), Inches(0.38),
          size=Pt(14), bold=True, color=acc)
        T(slide, desc, Inches(2.6), ry, Inches(3.6), Inches(0.38),
          size=Pt(13), color=DIM)

    # 오른쪽: 프레임워크 & 데이터
    box(slide, Inches(6.73), y0+Inches(0.15),
        Inches(5.93), Inches(2.55),
        fill=CARD, line=BORDER)
    T(slide, "에이전트 프레임워크",
      Inches(7.03), y0+Inches(0.3),
      Inches(5.3), Inches(0.38),
      size=Pt(18), bold=True, color=TEAL)
    agent_libs = [
        ("LangChain",   "LLM 앱 구축 표준  RAG·에이전트·툴",    TEAL),
        ("LlamaIndex",  "문서 기반 RAG 특화",                    TEAL),
        ("AutoGen",     "멀티 에이전트 자동화  Microsoft",        TEAL),
    ]
    for i, (name, desc, acc) in enumerate(agent_libs):
        ry = y0+Inches(0.78)+Inches(0.52)*i
        T(slide, name, Inches(7.03), ry, Inches(1.6), Inches(0.45),
          size=Pt(14), bold=True, color=acc)
        T(slide, desc, Inches(8.73), ry, Inches(3.8), Inches(0.45),
          size=Pt(13), color=DIM)

    box(slide, Inches(6.73), y0+Inches(2.85),
        Inches(5.93), Inches(2.75),
        fill=CARD, line=BORDER)
    T(slide, "평가 & 데이터",
      Inches(7.03), y0+Inches(3.0),
      Inches(5.3), Inches(0.38),
      size=Pt(18), bold=True, color=PURPLE)
    eval_libs = [
        ("HuggingFace Hub",  "모델·데이터셋 허브  가장 큰 공개 저장소", PURPLE),
        ("ROUGE / BERTScore","텍스트 생성 품질 평가 지표",               PURPLE),
        ("Weights & Biases", "학습 과정 시각화  실험 관리",               PURPLE),
    ]
    for i, (name, desc, acc) in enumerate(eval_libs):
        ry = y0+Inches(3.52)+Inches(0.52)*i
        T(slide, name, Inches(7.03), ry, Inches(2.0), Inches(0.45),
          size=Pt(13), bold=True, color=acc)
        T(slide, desc, Inches(9.13), ry, Inches(3.3), Inches(0.45),
          size=Pt(12.5), color=DIM)


# ════════════════════════════════════════════════════
# S6 — 우리 프로젝트 (키워드 위주)
# ════════════════════════════════════════════════════
def s6(prs):
    slide = new_slide(prs)
    y0 = hdr(slide, "AI Tutor", "강의자료 기반 질의응답 시스템")

    # 왼쪽: 구성
    box(slide, Inches(0.7), y0+Inches(0.15),
        Inches(7.5), Inches(5.5),
        fill=CARD, line=BORDER)

    components = [
        ("FastAPI",          "백엔드 서버",                    BLUE),
        ("FAISS",            "벡터 DB  ·  유사도 검색",        TEAL),
        ("BGE Reranker",     "검색 결과 재순위",               PURPLE),
        ("Parent-Child 청킹", "문서 구조 보존 청킹",           DIM),
        ("Qwen3-8B / Ollama","로컬 LLM 추론",                 GREEN),
        ("JWT 인증",          "학생 개인화",                   ORANGE),
    ]
    T(slide, "구성 요소",
      Inches(1.0), y0+Inches(0.3),
      Inches(6.8), Inches(0.4),
      size=Pt(17), bold=True, color=BLUE)
    for i, (name, desc, acc) in enumerate(components):
        ry = y0+Inches(0.85)+Inches(0.78)*i
        box(slide, Inches(1.0), ry, Inches(2.2), Inches(0.55),
            fill=RGBColor(0x0f,0x1a,0x30), line=acc, lw=Pt(1.2))
        T(slide, name, Inches(1.0), ry+Inches(0.08),
          Inches(2.2), Inches(0.38),
          size=Pt(13), bold=True, color=acc, align=PP_ALIGN.CENTER)
        T(slide, desc, Inches(3.35), ry+Inches(0.1),
          Inches(4.6), Inches(0.38),
          size=Pt(14), color=TEXT_SUB)

    # 오른쪽: 문제 키워드
    box(slide, Inches(8.43), y0+Inches(0.15),
        Inches(4.23), Inches(2.5),
        fill=RGBColor(0x25,0x10,0x10), line=RED, lw=Pt(2))
    T(slide, "한계",
      Inches(8.73), y0+Inches(0.3),
      Inches(3.63), Inches(0.42),
      size=Pt(20), bold=True, color=RED)
    ML(slide, [
        "Hallucination",
        "단답  ·  추론 부재",
        "도메인 맥락 부족",
    ], Inches(8.73), y0+Inches(0.82),
       Inches(3.63), Inches(1.5),
       size=Pt(17), color=TEXT_SUB)

    box(slide, Inches(8.43), y0+Inches(2.8),
        Inches(4.23), Inches(2.85),
        fill=RGBColor(0x11,0x1e,0x11), line=GREEN, lw=Pt(2))
    T(slide, "목표",
      Inches(8.73), y0+Inches(2.95),
      Inches(3.63), Inches(0.42),
      size=Pt(20), bold=True, color=GREEN)
    ML(slide, [
        "Faithfulness ↑",
        "CoT 설명",
        "Hallucination ↓",
    ], Inches(8.73), y0+Inches(3.47),
       Inches(3.63), Inches(1.8),
       size=Pt(17), color=TEXT_SUB)


# ════════════════════════════════════════════════════
# S7 — 접근 방식 (키워드 위주)
# ════════════════════════════════════════════════════
def s7(prs):
    slide = new_slide(prs)
    y0 = hdr(slide, "Reasoning Distillation", "Qwen3-14B  →  Qwen3-8B  ·  LoRA r=32")

    # 플로우
    steps = [
        ("Wikipedia\n한국어",    BLUE,   RGBColor(0x1a,0x1a,0x3a)),
        ("Teacher\nQwen3-14B",  ORANGE, RGBColor(0x2a,0x18,0x08)),
        ("CoT QA\n~50,000개",   GREEN,  RGBColor(0x11,0x1e,0x11)),
        ("Student\nQwen3-8B",   PURPLE, RGBColor(0x1a,0x11,0x2a)),
        ("GGUF\nOllama",        TEAL,   RGBColor(0x0f,0x1e,0x1e)),
    ]
    sw = Inches(2.1); sh = Inches(1.4)
    sx = Inches(0.7)
    for i, (label, acc, bg_c) in enumerate(steps):
        box(slide, sx, y0+Inches(0.18), sw, sh, fill=bg_c, line=acc, lw=Pt(2))
        T(slide, label, sx, y0+Inches(0.35), sw, sh-Inches(0.1),
          size=Pt(15), bold=True, color=acc, align=PP_ALIGN.CENTER)
        sx += sw
        if i < len(steps)-1:
            T(slide, "→", sx, y0+Inches(0.45), Inches(0.27), Inches(0.5),
              size=Pt(22), color=DIM, align=PP_ALIGN.CENTER)
            sx += Inches(0.27)

    # 키워드 블록들
    y1 = y0+Inches(1.82)
    kw_blocks = [
        ("데이터", BLUE,
         ["Wikipedia  ·  KLUE/MRC  ·  OpenThoughts",
          "CoT  ·  <think> 태그  ·  ChatML 포맷",
          "Faithfulness 필터  ·  체크포인트"]),
        ("학습", GREEN,
         ["LoRA  r=32  ·  fp16  ·  alpha=64",
          "Sequence Packing  ·  Grad Checkpointing",
          "Kubeflow  ·  L40S 44GB  ·  Watchdog"]),
        ("평가", ORANGE,
         ["ROUGE-L  ≥ 0.35",
          "BERTScore  ≥ 0.80",
          "Faithfulness  ≥ 0.70  ·  Hallucination  ≤ 0.10"]),
    ]
    cw = Inches(3.93); ch = Inches(3.75)
    cx = Inches(0.7)
    for title, acc, kws in kw_blocks:
        box(slide, cx, y1, cw, ch, fill=CARD, line=acc, lw=Pt(1.5))
        T(slide, title,
          cx+Inches(0.2), y1+Inches(0.15),
          cw-Inches(0.4), Inches(0.42),
          size=Pt(20), bold=True, color=acc)
        box(slide, cx+Inches(0.2), y1+Inches(0.62),
            cw-Inches(0.4), Pt(1), fill=acc)
        for i, kw in enumerate(kws):
            T(slide, kw,
              cx+Inches(0.2), y1+Inches(0.82)+Inches(0.88)*i,
              cw-Inches(0.4), Inches(0.75),
              size=Pt(14.5), color=TEXT_SUB)
        cx += cw + Inches(0.17)


# ════════════════════════════════════════════════════
# S8 — 진행 현황 & 마무리
# ════════════════════════════════════════════════════
def s8(prs):
    slide = new_slide(prs)
    bg(slide, BG_DARK)
    box(slide, 0, 0, W, Inches(0.18), fill=BLUE_MID)
    box(slide, 0, Inches(7.32), W, Inches(0.18), fill=BLUE_MID)

    T(slide, "현재",
      Inches(1.4), Inches(0.38),
      Inches(5), Inches(0.52),
      size=Pt(26), bold=True, color=BLUE)

    status = [
        ("✅", "파이프라인 구성",   "데이터 생성  ·  학습  ·  평가 스크립트", GREEN),
        ("✅", "데이터셋",         "~50,000개 병합 완료",                     GREEN),
        ("⏳", "학습 진행 중",     "Kubeflow L40S  ·  결과 대기",             ORANGE),
        ("□",  "서빙",            "GGUF 변환  →  Ollama  ·  Tailscale",      DIM),
        ("□",  "DPO 정렬",        "학습 결과 확인 후 진행",                   DIM),
    ]
    for i, (icon, title, desc, acc) in enumerate(status):
        ry = Inches(1.05) + Inches(0.9)*i
        T(slide, icon,
          Inches(1.4), ry, Inches(0.5), Inches(0.65),
          size=Pt(22), color=acc, align=PP_ALIGN.CENTER)
        T(slide, title,
          Inches(2.05), ry+Inches(0.05), Inches(2.5), Inches(0.45),
          size=Pt(17), bold=True, color=acc)
        T(slide, desc,
          Inches(4.65), ry+Inches(0.1), Inches(7.5), Inches(0.4),
          size=Pt(15), color=DIM)

    box(slide, Inches(1.4), Inches(5.7),
        Inches(10.5), Pt(1), fill=BORDER)

    T(slide, "Q & A",
      Inches(1.4), Inches(5.95),
      Inches(10.5), Inches(0.85),
      size=Pt(48), bold=True, color=BLUE,
      align=PP_ALIGN.CENTER)


# ════════════════════════════════════════════════════
def main():
    prs = Presentation()
    prs.slide_width  = W
    prs.slide_height = H

    print("생성 중...")
    s1(prs); print("  1/8 타이틀")
    s2(prs); print("  2/8 머신러닝 / LLM")
    s3(prs); print("  3/8 동작 구조")
    s4(prs); print("  4/8 활용 방법들")
    s5(prs); print("  5/8 라이브러리 생태계")
    s6(prs); print("  6/8 AI Tutor")
    s7(prs); print("  7/8 Reasoning Distillation")
    s8(prs); print("  8/8 현재 & Q&A")

    prs.save("finetune_seminar_v2.pptx")
    print("\n완료: finetune_seminar_v2.pptx")

if __name__ == "__main__":
    main()
