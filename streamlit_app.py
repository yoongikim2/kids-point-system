import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
import random

# 페이지 설정
st.set_page_config(page_title="모건&모하의 성장 미션", layout="centered")

# --- [디자인 수정] 모바일에서 버튼이 안 잘리게 레이아웃 조정 ---
st.markdown("""
    <style>
    .main-title {
        font-size: 22px !important;
        font-weight: bold;
        margin-bottom: 10px;
    }
    .msg-text {
        font-size: 15px !important;
        margin-bottom: 3px !important;
    }
    /* 버튼 간격 및 크기 최적화 */
    .stButton > button {
        width: 100% !important;
        height: 45px !important;
        font-size: 15px !important;
        margin-bottom: 5px !important;
    }
    /* 여백 줄이기 */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 1rem !important;
    }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<p class="main-title">🌱 모건&모하의 규칙 성장 미션!</p>', unsafe_allow_html=True)

# --- 응원 문구 세션 관리 ---
if 'm_msg' not in st.session_state:
    love_msgs = ["사랑해", "너무 사랑해", "오늘도 할수 있어!", "난 멋지니깐!", "규칙을 잘지키자!", "우리집은 내가 지킨다!", "스스로 하는 멋진 나!"]
    m_list = [f"모건, {msg}" for msg in love_msgs] + ["모건, 멋지게 성장 중!", "모건, 넌 정말 훌륭해!"]
    h_list = [f"모하, {msg}" for msg in love_msgs] + ["모하, 한 걸음씩 쑥쑥!", "모하, 오늘도 빛나는 하루!"]
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

    today_str = datetime.now().strftime("%Y-%m-%d")
    if not history_df.empty:
        history_df['이름'] = history_df['이름'].astype(str).str.replace("김", "").str.strip()
        history_df['변동 점수'] = pd.to_numeric(history_df['변동 점수'], errors='coerce').fillna(0)
        history_df['날짜'] = history_df['일시'].str[:10]

    m_score = int(history_df[history_df['이름'] == "모건"]['변동 점수'].sum()) if not history_df.empty else 0
    h_score = int(history_df[history_df['이름'] == "모하"]['변동 점수'].sum()) if not history_df.empty else 0

    col_score1, col_score2 = st.columns(2)
    col_score1.metric("모건", f"{m_score}점")
    col_score2.metric("모하", f"{h_score}점")

    def save_log(name, p, r):
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        history_sheet.append_row([name, now, r, int(p)])
        st.success(f"기록 완료!")
        st.rerun()

    tab1, tab2 = st.tabs(["🚀 미션", "🎁 상점"])

    with tab1:
        st.markdown(f'<p class="msg-text">💡 {st.session_state.m_msg}</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="msg-text">💡 {st.session_state.h_msg}</p>', unsafe_allow_html=True)

        for i, row in rules_df.iterrows():
            if not row.get('규칙명'): continue
            
            # 오늘 수행 여부 체크
            m_rec = history_df[(history_df['이름'] == "모건") & (history_df['날짜'] == today_str) & (history_df['규칙/보상명'] == row['규칙명'])] if not history_df.empty else pd.DataFrame()
            h_rec = history_df[(history_df['이름'] == "모하") & (history_df['날짜'] == today_str) & (history_df['규칙/보상명'] == row['규칙명'])] if not history_df.empty else pd.DataFrame()

            with st.expander(row['규칙명']):
                # --- [수정 핵심] 모건/모하 구역을 상하로 나누고, 가로로 2개씩 배치 ---
                # 1층: 모건
                st.write("👦 **모건**")
                m_c1, m_c2 = st.columns(2)
                if not m_rec.empty:
                    label = "역시 멋져! ✅" if m_rec.iloc[0]['변동 점수'] > 0 else "다음엔 잘하자! ❌"
                    m_c1.button(label, key=f"m_done_{i}", disabled=True, use_container_width=True)
                else:
                    if m_c1.button("성공 ✅", key=f"m_s_{i}", use_container_width=True): save_log("모건", row['상점'], row['규칙명'])
                    if m_c2.button("실패 ❌", key=f"m_f_{i}", use_container_width=True): save_log("모건", -row['벌점'], row['규칙명'])
                
                st.write("👧 **모하**")
                h_c1, h_c2 = st.columns(2)
                if not h_rec.empty:
                    label = "역시 멋져! ✅" if h_rec.iloc[0]['변동 점수'] > 0 else "다음엔 잘하자! ❌"
                    h_c1.button(label, key=f"h_done_{i}", disabled=True, use_container_width=True)
                else:
                    if h_c1.button("성공 ✅", key=f"h_s_{i}", use_container_width=True): save_log("모하", row['상점'], row['규칙명'])
                    if h_c2.button("실패 ❌", key=f"h_f_{i}", use_container_width=True): save_log("모하", -row['벌점'], row['규칙명'])

    with tab2:
        st.subheader("🎁 포인트 사용")
        for i, row in rewards_df.iterrows():
            if not row.get('보상명'): continue
            needed = abs(int(row['필요점수']))
            with st.expander(row['보상명']):
                c1, c2 = st.columns(2)
                m_can = m_score >= needed
                if c1.button(f"모건({needed}p)", key=f"m_p_{i}", disabled=not m_can, use_container_width=True):
                    save_log("모건", -needed, f"[보상] {row['보상명']}")
                h_can = h_score >= needed
                if c2.button(f"모하({needed}p)", key=f"h_p_{i}", disabled=not h_can, use_container_width=True):
                    save_log("모하", -needed, f"[보상] {row['보상명']}")

except Exception as e:
    st.error(f"오류: {e}")
