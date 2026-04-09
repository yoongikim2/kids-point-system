import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
import random

# 페이지 설정
st.set_page_config(page_title="모건&모하의 성장 미션", layout="centered")

# --- [디자인 수정] 모바일 가로 정렬 및 글자 크기 최적화 ---
st.markdown("""
    <style>
    /* 메인 제목 크기 */
    .main-title {
        font-size: 24px !important;
        font-weight: bold;
        margin-bottom: 10px;
    }
    /* 응원 문구 크기 */
    .msg-text {
        font-size: 16px !important;
        margin-bottom: 5px !important;
    }
    /* [핵심] 모바일에서도 버튼을 가로로 강제 정렬 */
    [data-testid="stHorizontalBlock"] {
        flex-direction: row !important;
        display: flex !important;
        flex-wrap: nowrap !important;
        gap: 5px !important;
    }
    [data-testid="column"] {
        min-width: 0px !important;
        flex: 1 1 auto !important;
    }
    /* 버튼 내부 텍스트와 여백 조정 */
    .stButton > button {
        font-size: 13px !important;
        padding: 0px !important;
        height: 38px !important;
        width: 100% !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 제목 표시
st.markdown('<p class="main-title">🌱 모건&모하의 규칙 성장 미션!</p>', unsafe_allow_html=True)

# --- 응원 문구 리스트 ---
if 'm_msg' not in st.session_state:
    love_msgs = ["사랑해", "너무 사랑해", "오늘도 할수 있어!", "난 멋지니깐!", "규칙을 잘지키자!", "우리집은 내가 지킨다!", "스스로 하는 멋진 나!"]
    m_list = [f"모건, {msg}" for msg in love_msgs] + ["모건, 멋지게 성장 중!", "모건, 넌 정말 훌륭해!", "모건, 오늘도 미션 클리어!"]
    h_list = [f"모하, {msg}" for msg in love_msgs] + ["모하, 한 걸음씩 쑥쑥!", "모하, 오늘도 빛나는 하루!", "모하, 미션을 즐겁게 해보자!"]
    st.session_state.m_msg = random.choice(m_list)
    st.session_state.h_msg = random.choice(h_list)

def get_gspread_client():
    creds_info = st.secrets["gspread_service_account"]
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
    return gspread.authorize(creds)

try:
    client = get_gspread_client()
    sheet_id = "1psSU23KIAOpxwdGaJ67Deaz5XWk3VAkFo0DXM2qsCqA"
    sh = client.open_by_key(sheet_id)
    
    rules_sheet = sh.worksheet("rules")
    history_sheet = sh.worksheet("history")
    rewards_sheet = sh.worksheet("rewards")

    rules_df = pd.DataFrame(rules_sheet.get_all_records())
    history_df = pd.DataFrame(history_sheet.get_all_records())
    rewards_df = pd.DataFrame(rewards_sheet.get_all_records())

    # 데이터 정제
    today_str = datetime.now().strftime("%Y-%m-%d")
    if not history_df.empty:
        history_df['이름'] = history_df['이름'].astype(str).str.replace("김", "").str.strip()
        history_df['변동 점수'] = pd.to_numeric(history_df['변동 점수'], errors='coerce').fillna(0)
        history_df['날짜'] = history_df['일시'].str[:10]

    def calculate_score(name):
        if not history_df.empty:
            return int(history_df[history_df['이름'] == name]['변동 점수'].sum())
        return 0

    m_score = calculate_score("모건")
    h_score = calculate_score("모하")

    # 상단 점수판
    col_score1, col_score2 = st.columns(2)
    col_score1.metric("모건", f"{m_score}점")
    col_score2.metric("모하", f"{h_score}점")

    st.divider()

    def save_log(name, p, r):
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        history_sheet.append_row([name, now, r, int(p)])
        st.success(f"기록 완료!")
        st.rerun()

    def check_today_complete(name):
        if history_df.empty: return False
        today_done = history_df[(history_df['이름'] == name) & (history_df['날짜'] == today_str) & (~history_df['규칙/보상명'].str.startswith("[보상]"))]
        return len(today_done) >= 10

    tab1, tab2 = st.tabs(["🚀 미션", "🎁 상점"])

    with tab1:
        # 모건&모하 응원 문구 나란히 표시
        if check_today_complete("모건"): st.success("✨ 모건 성장 완료! ✨")
        else: st.markdown(f'<p class="msg-text">💡 {st.session_state.m_msg}</p>', unsafe_allow_html=True)

        if check_today_complete("모하"): st.success("✨ 모하 성장 완료! ✨")
        else: st.markdown(f'<p class="msg-text">💡 {st.session_state.h_msg}</p>', unsafe_allow_html=True)

        for i, row in rules_df.iterrows():
            if not row.get('규칙명'): continue
            
            def get_status_label(name, rule_name):
                if history_df.empty: return None
                record = history_df[(history_df['이름'] == name) & (history_df['날짜'] == today_str) & (history_df['규칙/보상명'] == rule_name)]
                if not record.empty:
                    return "멋져!" if record.iloc[0]['변동 점수'] > 0 else "다음엔!"
                return None

            m_status = get_status_label("모건", row['규칙명'])
            h_status = get_status_label("모하", row['규칙명'])

            with st.expander(row['규칙명']):
                # 가로로 4칸을 무조건 유지하도록 설정
                c1, c2, c3, c4 = st.columns(4)
                
                # 모건 버튼 구역
                if m_status:
                    c1.button(m_status, key=f"m_r_{i}", disabled=True)
                    # 옆 칸을 비워두지 않기 위해 투명 버튼 처리 (가로 비율 유지용)
                else:
                    if c1.button("모건✅", key=f"m_r_{i}"): save_log("모건", row['상점'], row['규칙명'])
                    if c2.button("모건❌", key=f"m_f_{i}"): save_log("모건", -row['벌점'], row['규칙명'])
                
                # 모하 버튼 구역
                if h_status:
                    c3.button(h_status, key=f"h_r_{i}", disabled=True)
                else:
                    if c3.button("모하✅", key=f"h_r_{i}"): save_log("모하", row['상점'], row['규칙명'])
                    if c4.button("모하❌", key=f"h_f_{i}"): save_log("모하", -row['벌점'], row['규칙명'])

    with tab2:
        st.subheader("🎁 포인트 사용")
        for i, row in rewards_df.iterrows():
            if not row.get('보상명'): continue
            needed = abs(int(row['필요점수']))
            with st.expander(row['보상명']):
                col_m, col_h = st.columns(2)
                with col_m:
                    m_can_buy = m_score >= needed
                    st.write(f"모건:{m_score}/{needed}")
                    if st.button(f"구매", key=f"m_p_{i}", disabled=not m_can_buy, use_container_width=True):
                        save_log("모건", -needed, f"[보상] {row['보상명']}")
                with col_h:
                    h_can_buy = h_score >= needed
                    st.write(f"모하:{h_score}/{needed}")
                    if st.button(f"구매", key=f"h_p_{i}", disabled=not h_can_buy, use_container_width=True):
                        save_log("모하", -needed, f"[보상] {row['보상명']}")

    st.divider()
    if not history_df.empty:
        display_df = history_df[history_df['날짜'] == today_str][['이름', '일시', '규칙/보상명', '변동 점수']].iloc[::-1]
        st.dataframe(display_df.head(5), use_container_width=True)

except Exception as e:
    st.error(f"오류: {e}")
