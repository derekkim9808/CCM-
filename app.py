import streamlit as st
import google.generativeai as genai
import pandas as pd

st.set_page_config(page_title="고객 문의 대응 시스템", page_icon="💬", layout="wide")

# ── 사이드바 ──────────────────────────────────────────────────────
with st.sidebar:
    st.title("⚙️ 설정")

    api_key = ""
    if hasattr(st, "secrets") and "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
    if not api_key:
        api_key = st.text_input("Google Gemini API Key", type="password",
                                 help="https://aistudio.google.com 에서 무료 발급")

    st.divider()
    st.subheader("📂 과거 문의 데이터")
    uploaded = st.file_uploader("CSV 파일 업로드", type=["csv"],
                                 help="컬럼: 문의내용, 카테고리, 담당부서, 필요정보, 처리기간, 처리결과")

    if uploaded:
        try:
            df = pd.read_csv(uploaded, encoding="utf-8-sig")
            st.success(f"✅ {len(df)}건 로드됨")
            st.dataframe(df.head(3), use_container_width=True)
            st.session_state["df"] = df
        except Exception as e:
            st.error(f"파일 오류: {e}")

    if "df" not in st.session_state:
        st.session_state["df"] = pd.DataFrame([
            {"문의내용":"구매한 노트북 배터리가 3시간도 안 됩니다. 환불 받고 싶습니다.",
             "카테고리":"환불/반품","담당부서":"CS팀 > 환불처리파트",
             "필요정보":"주문번호, 구매일자, 불량 사진","처리기간":"3~5 영업일","처리결과":"환불 완료"},
            {"문의내용":"주문한 제품이 2주가 지났는데도 도착하지 않았습니다.",
             "카테고리":"배송 문의","담당부서":"물류팀 > 배송추적파트",
             "필요정보":"주문번호, 수령지 주소","처리기간":"1~2 영업일","처리결과":"택배사 분실 확인 후 재발송"},
            {"문의내용":"앱 로그인이 안 됩니다. 비밀번호 재설정도 이메일이 안 옵니다.",
             "카테고리":"계정/인증","담당부서":"기술지원팀",
             "필요정보":"가입 이메일, 가입일자","처리기간":"당일~1 영업일","처리결과":"계정 수동 복구"},
            {"문의내용":"결제했는데 주문 확인 이메일이 오지 않고 결제 내역만 있습니다.",
             "카테고리":"결제 오류","담당부서":"결제팀",
             "필요정보":"결제수단, 결제금액, 결제시각","처리기간":"1 영업일","처리결과":"주문 수동 등록 처리"},
            {"문의내용":"제품 설명과 실제 색상이 다릅니다. 교환 가능한지요?",
             "카테고리":"제품 결함","담당부서":"CS팀 > 교환처리파트",
             "필요정보":"주문번호, 제품 사진, 수령 사진","처리기간":"2~4 영업일","처리결과":"교환 완료"},
            {"문의내용":"서비스 접속이 자꾸 끊깁니다. 오늘 아침부터 계속됩니다.",
             "카테고리":"서비스 장애","담당부서":"기술팀 > 인프라파트",
             "필요정보":"오류 발생 시각, 브라우저/앱 버전, 화면 캡처","처리기간":"긴급 대응 (2시간 이내)","처리결과":"서버 이슈 패치 완료"},
            {"문의내용":"멤버십 구독 취소했는데 다음 달에도 결제가 됐습니다.",
             "카테고리":"결제 오류","담당부서":"결제팀 > 구독관리파트",
             "필요정보":"결제수단, 취소 신청 날짜, 결제 내역 캡처","처리기간":"2~3 영업일","처리결과":"환불 및 구독 완전 취소 처리"},
            {"문의내용":"구매 후 사용하지 않은 제품인데 단순 변심으로 반품 가능한가요?",
             "카테고리":"환불/반품","담당부서":"CS팀 > 환불처리파트",
             "필요정보":"주문번호, 구매일자, 미개봉 여부","처리기간":"2~5 영업일","처리결과":"정책 안내 후 반품 처리"},
        ])
        st.info("💡 샘플 데이터 8건 사용 중. CSV 업로드 시 교체됩니다.")

    st.divider()
    st.caption("⚠️ 고객 개인정보(실명·고객번호 등)는 마스킹 후 입력해 주세요.")


# ── 메인 화면 ────────────────────────────────────────────────────
st.title("💬 고객 문의 대응 프로세스 안내")
st.caption("문의 내용을 입력하면 AI가 담당 부서·대응 절차·필요 정보를 안내합니다.")

col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.subheader("📝 문의 등록")
    inquiry = st.text_area("문의 내용", height=160,
                            placeholder="예) 지난달 구매한 제품의 환불을 요청드립니다.\n\n⚠️ 고객 실명·고객번호 등 개인정보는 마스킹 처리 후 입력해 주세요.")
    c1, c2 = st.columns(2)
    with c1:
        category = st.selectbox("카테고리 (선택)", ["", "환불/반품", "배송 문의", "제품 결함",
                                                      "서비스 장애", "계정/인증", "결제 오류", "기타"])
    with c2:
        urgency = st.selectbox("긴급도 (선택)", ["", "높음", "보통", "낮음"])

    analyze = st.button("🔍 AI 대응 프로세스 분석", type="primary", use_container_width=True)

with col2:
    st.subheader("📋 참고 데이터 현황")
    df = st.session_state["df"]
    st.caption(f"총 {len(df)}건 로드됨")
    st.dataframe(df[["문의내용","카테고리","담당부서"]].head(5), use_container_width=True, hide_index=True)


# ── 분석 실행 ────────────────────────────────────────────────────
if analyze:
    if not api_key:
        st.error("사이드바에서 Gemini API Key를 입력해 주세요.")
        st.stop()
    if not inquiry.strip():
        st.warning("문의 내용을 입력해 주세요.")
        st.stop()

    context = "\n".join(
        f"[{r.get('카테고리','')}] {r.get('문의내용','')} → 담당: {r.get('담당부서','')}, "
        f"필요정보: {r.get('필요정보','')}, 처리기간: {r.get('처리기간','')}"
        for _, r in df.iterrows()
    )

    prompt = f"""당신은 고객 문의 대응 전문가입니다. 과거 사례를 참고해 새 문의의 대응 프로세스를 분석하세요.

과거 사례:
{context}

새 문의:
- 문의내용: {inquiry}
{"- 카테고리: " + category if category else ""}
{"- 긴급도: " + urgency if urgency else ""}

다음 항목을 명확하게 분석해 주세요:
1. 문의 카테고리 및 긴급도 (높음/보통/낮음)
2. 담당 부서 및 에스컬레이션 경로
3. 단계별 대응 절차 (번호 목록)
4. 고객에게 추가로 받아야 할 정보 목록
5. 고객 초기 응답 메시지 템플릿
6. 유사 사례 요약 및 주의사항"""

    with st.spinner("AI 분석 중..."):
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("models/gemini-1.5-flash")
            resp = model.generate_content(prompt)
            result = resp.text
            st.session_state["result"] = result
        except Exception as e:
            st.error(f"API 오류: {e}")
            st.stop()

if "result" in st.session_state:
    st.divider()
    st.subheader("✅ 대응 프로세스 분석 결과")
    st.markdown(st.session_state["result"])

    col_a, col_b = st.columns(2)
    with col_a:
        st.download_button(
            "📥 결과 다운로드 (.txt)",
            data=st.session_state["result"].encode("utf-8"),
            file_name="대응프로세스.txt",
            mime="text/plain",
            use_container_width=True
        )
    with col_b:
        if st.button("🔄 초기화", use_container_width=True):
            del st.session_state["result"]
            st.rerun()
