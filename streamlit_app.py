import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime

# 페이지 설정
st.set_page_config(page_title="Family Rules & Shop", layout="centered")
st.title("🏆 우리 집 규칙 상점")

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
    if not history_df.empty:
        history_df['이름'] = history_df['이름'].astype(str).str.strip()
        history_df['변동 점수'] = pd.to_numeric(history_df['변동 점수'], errors='coerce').fillna(0)
        history_df['날짜'] = history_df['일시'].str[:10]

    # [1] 무한 누적 점수 계산 (모든 기록 합산)
    def calculate_score(name):
        if not history_df.empty:
            return int(history_df[history_df['이름'] == name]['변동 점수'].sum())
        return 0

    m_score = calculate_score("김모건")
    h_score = calculate_score("김모하")

    # 상단 점수판
    col1, col2 = st.columns(2)
    col1.metric("모건이 누적 점수", f"{m_score}점")
    col2.metric("모하 누적 점수", f"{h_score}점")

    st.divider()

    # 기록 저장 함수
    def save_log(name, p, r):
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        # 숫자로 확실히 변환해서 저장
        history_sheet.append_row([name, now, r, int(p)])
        st.success(f"기록 완료!")
        st.rerun()

    # [2] 오늘 미션 10개 완료 체크 함수
    def check_today_complete(name):
        if history_df.empty: return False
        today = datetime.now().strftime("%Y-%m-%d")
        # 오늘 수행한 규칙(보상 제외) 개수 파악
        today_done = history_df[
            (history_df['이름'] == name) & 
            (history_df['날짜'] == today) & 
            (~history_df['규칙/보상명'].str.startswith("[보상]"))
        ]
        return len(today_done) >= 10

    tab1, tab2 = st.tabs(["📋 규칙 지키기", "🎁 보상 마켓"])

    # [TAB 1: 규칙 지키기]
    with tab1:
        # 모건이 상태 메시지
        if check_today_complete("김모건"):
            st.success("✨ 모건이 오늘의 미션 10개 완료! 대단해요! ✨")
        else:
            st.subheader("모건아, 오늘도 멋지게 규칙을 지켜보자!")

        # 모하 상태 메시지
        if check_today_complete("김모하"):
            st.success("✨ 모하 오늘의 미션 10개 완료! 최고예요! ✨")
        else:
            st.subheader("모하야, 한 걸음씩 규칙을 지켜보자!")

        for i, row in rules_df.iterrows():
            if not row.get('규칙명'): continue
            with st.expander(f"{row['규칙명']} (+{row['상점']}/-{row['벌점']})"):
                c1, c2, c3, c4 = st.columns(4)
                if c1.button("모건✅", key=f"m_r_{i}"): save_log("김모건", row['상점'], row['규칙명'])
                if c2.button("모건❌", key=f"m_f_{i}"): save_log("김모건", -row['벌점'], row['규칙명'])
                if c3.button("모하✅", key=f"h_r_{i}"): save_log("김모하", row['상점'], row['규칙명'])
                if c4.button("모하❌", key=f"h_f_{i}"): save_log("김모하", -row['벌점'], row['규칙명'])

    # [TAB 2: 보상 마켓]
    with tab2:
        st.subheader("🎁 점수를 사용해서 소원을 빌어보세요!")
        for i, row in rewards_df.iterrows():
            if not row.get('보상명'): continue
            with st.expander(f"{row['보상명']} ({row['필요점수']}점 차감)"):
                c1, c2 = st.columns(2)
                
                # [중요] 점수 차감 시 마이너스(-)를 강제로 붙임
                m_can_buy = m_score >= row['필요점수']
                if c1.button(f"모건 구매", key=f"m_p_{i}", disabled=not m_can_buy):
                    # -1을 곱해서 마이너스로 만듭니다.
                    save_log("김모건", -1 * abs(int(row['필요점수'])), f"[보상] {row['보상명']}")
                
                h_can_buy = h_score >= row['필요점수']
                if c2.button(f"모하 구매", key=f"h_p_{i}", disabled=not h_can_buy):
                    save_log("김모하", -1 * abs(int(row['필요점수'])), f"[보상] {row['보상명']}")

    st.divider()
    st.subheader("📜 최근 기록")
    if not history_df.empty:
        display_df = history_df[['이름', '일시', '규칙/보상명', '변동 점수']].iloc[::-1]
        st.dataframe(display_df.head(10), use_container_width=True)

except Exception as e:
    st.error(f"오류가 발생했어요: {e}")
