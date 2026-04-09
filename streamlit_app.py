import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
import random

# 페이지 설정
st.set_page_config(page_title="Family Rules & Shop", layout="centered")
st.title("🏆 우리 집 규칙 상점")

# --- 응원 문구 리스트 (사이트 접속 시마다 랜덤 선택) ---
if 'm_msg' not in st.session_state:
    m_list = ["모건, 오늘도 멋지게 지켜보자!", "모건, 넌 할 수 있어!", "오늘도 차곡차곡 점수를 쌓아볼까?", "모건의 멋진 하루를 응원해!", "모건, 규칙 지키기 대장!"]
    h_list = ["모하, 즐겁게 시작해볼까?", "모하, 오늘도 화이팅!", "웃음 가득한 모하의 하루!", "작은 규칙부터 하나씩 지켜보자!", "모하, 오늘도 응원해!"]
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

    # 누적 점수 계산
    def calculate_score(name):
        if not history_df.empty:
            return int(history_df[history_df['이름'] == name]['변동 점수'].sum())
        return 0

    m_score = calculate_score("모건")
    h_score = calculate_score("모하")

    # 상단 점수판
    col_score1, col_score2 = st.columns(2)
    col_score1.metric("모건 누적 점수", f"{m_score}점")
    col_score2.metric("모하 누적 점수", f"{h_score}점")

    st.divider()

    # 기록 저장 함수
    def save_log(name, p, r):
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        history_sheet.append_row([name, now, r, int(p)])
        st.success(f"기록 완료!")
        st.rerun()

    # 오늘 미션 10개 완료 체크
    def check_today_complete(name):
        if history_df.empty: return False
        today_done = history_df[
            (history_df['이름'] == name) & 
            (history_df['날짜'] == today_str) & 
            (~history_df['규칙/보상명'].str.startswith("[보상]"))
        ]
        return len(today_done) >= 10

    tab1, tab2 = st.tabs(["📋 규칙 지키기", "🎁 보상 마켓"])

    # [TAB 1: 규칙 지키기]
    with tab1:
        # 랜덤 문구 표시
        if check_today_complete("모건"): st.success("✨ 모건 오늘 미션 10개 완료! 대단해! ✨")
        else: st.subheader(st.session_state.m_msg)

        if check_today_complete("모하"): st.success("✨ 모하 오늘 미션 10개 완료! 최고야! ✨")
        else: st.subheader(st.session_state.h_msg)

        for i, row in rules_df.iterrows():
            if not row.get('규칙명'): continue
            
            # --- 오늘 이미 이 규칙을 수행했는지 체크 ---
            m_already_done = False
            h_already_done = False
            if not history_df.empty:
                m_already_done = not history_df[(history_df['이름'] == "모건") & (history_df['날짜'] == today_str) & (history_df['규칙/보상명'] == row['규칙명'])].empty
                h_already_done = not history_df[(history_df['이름'] == "모하") & (history_df['날짜'] == today_str) & (history_df['규칙/보상명'] == row['규칙명'])].empty

            with st.expander(row['규칙명']):
                c1, c2, c3, c4 = st.columns(4)
                
                # 모건 버튼 (오늘 완료했으면 disabled)
                if c1.button("모건✅" if not m_already_done else "모건 완료", key=f"m_r_{i}", disabled=m_already_done):
                    save_log("모건", row['상점'], row['규칙명'])
                if c2.button("모건❌" if not m_already_done else "모건 완료", key=f"m_f_{i}", disabled=m_already_done):
                    save_log("모건", -row['벌점'], row['규칙명'])
                
                # 모하 버튼 (오늘 완료했으면 disabled)
                if c3.button("모하✅" if not h_already_done else "모하 완료", key=f"h_r_{i}", disabled=h_already_done):
                    save_log("모하", row['상점'], row['규칙명'])
                if c4.button("모하❌" if not h_already_done else "모하 완료", key=f"h_f_{i}", disabled=h_already_done):
                    save_log("모하", -row['벌점'], row['규칙명'])

    # [TAB 2: 보상 마켓]
    with tab2:
        st.subheader("🎁 점수로 소원 구매하기")
        for i, row in rewards_df.iterrows():
            if not row.get('보상명'): continue
            needed = abs(int(row['필요점수']))
            with st.expander(row['보상명']):
                col_m, col_h = st.columns(2)
                with col_m:
                    m_can_buy = m_score >= needed
                    st.write(f"모건 필요: **{needed}점**")
                    if st.button(f"모건 구매", key=f"m_p_{i}", disabled=not m_can_buy, use_container_width=True):
                        save_log("모건", -needed, f"[보상] {row['보상명']}")
                with col_h:
                    h_can_buy = h_score >= needed
                    st.write(f"모하 필요: **{needed}점**")
                    if st.button(f"모하 구매", key=f"h_p_{i}", disabled=not h_can_buy, use_container_width=True):
                        save_log("모하", -needed, f"[보상] {row['보상명']}")

    st.divider()
    st.subheader("📜 최근 기록")
    if not history_df.empty:
        display_df = history_df[['이름', '일시', '규칙/보상명', '변동 점수']].iloc[::-1]
        st.dataframe(display_df.head(10), use_container_width=True)

except Exception as e:
    st.error(f"오류가 발생했어요: {e}")
