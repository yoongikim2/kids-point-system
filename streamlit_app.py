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
    rewards_sheet = sh.worksheet("rewards") # 보상 시트 추가

    # 데이터 불러오기
    rules_df = pd.DataFrame(rules_sheet.get_all_records())
    history_df = pd.DataFrame(history_sheet.get_all_records())
    rewards_df = pd.DataFrame(rewards_sheet.get_all_records())

    # 점수 계산 함수
    def calculate_score(name):
        if not history_df.empty and '이름' in history_df.columns:
            tmp_df = history_df.copy()
            tmp_df['이름'] = tmp_df['이름'].astype(str).str.strip()
            tmp_df['변동 점수'] = pd.to_numeric(tmp_df['변동 점수'], errors='coerce').fillna(0)
            return int(tmp_df[tmp_df['이름'] == name]['변동 점수'].sum())
        return 0

    m_score = calculate_score("김모건")
    h_score = calculate_score("김모하")

    # 상단 점수판
    col1, col2 = st.columns(2)
    col1.metric("모건이 현재 점수", f"{m_score}점")
    col2.metric("모하 현재 점수", f"{h_score}점")

    # 데이터 저장 공통 함수
    def save_log(name, p, r):
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        history_sheet.append_row([name, now, r, int(p)])
        st.success(f"'{r}' 완료! ({name}: {p}점)")
        st.rerun()

    # --- 탭으로 메뉴 나누기 ---
    tab1, tab2 = st.tabs(["📋 규칙 지키기", "🎁 보상 마켓"])

    # [TAB 1: 규칙 지키기]
    with tab1:
        st.subheader("오늘의 미션 완료!")
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
        st.subheader("모은 점수로 소원 사기")
        for i, row in rewards_df.iterrows():
            if not row.get('보상명'): continue
            with st.expander(f"{row['보상명']} ({row['필요점수']}점 필요)"):
                c1, c2 = st.columns(2)
                
                # 모건이 구매 버튼 (점수 부족하면 비활성화)
                m_disabled = m_score < row['필요점수']
                if c1.button(f"모건 구매 {'(부족)' if m_disabled else ''}", key=f"m_p_{i}", disabled=m_disabled):
                    save_log("김모건", -row['필요점수'], f"[보상] {row['보상명']}")
                
                # 모하 구매 버튼
                h_disabled = h_score < row['필요점수']
                if c2.button(f"모하 구매 {'(부족)' if h_disabled else ''}", key=f"h_p_{i}", disabled=h_disabled):
                    save_log("김모하", -row['필요점수'], f"[보상] {row['보상명']}")

    st.divider()
    st.subheader("📜 최근 5개 기록")
    if not history_df.empty:
        st.dataframe(history_df.iloc[::-1].head(5), use_container_width=True)

except Exception as e:
    st.error(f"오류가 발생했어요: {e}")
