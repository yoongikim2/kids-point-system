import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime

# 페이지 설정
st.set_page_config(page_title="Family Rules", layout="centered")
st.title("🏆 우리 집 규칙 상점")

# 1. 구글 시트 연결 (gspread 방식)
def get_gspread_client():
    # Streamlit Secrets에서 JSON 키를 읽어옵니다.
    creds_info = st.secrets["gspread_service_account"]
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
    return gspread.authorize(creds)

try:
    client = get_gspread_client()
    # 아빠의 시트 ID (주소창에서 가져옴)
    sheet_id = "1psSU23KIAOpxwdGaJ67Deaz5XWk3VAkFo0DXM2qsCqA"
    sh = client.open_by_key(sheet_id)
    
    # 탭 이름 (반드시 영어 rules, history여야 함)
    rules_sheet = sh.worksheet("rules")
    history_sheet = sh.worksheet("history")

    # 데이터 가져오기
    rules_df = pd.DataFrame(rules_sheet.get_all_records())
    history_df = pd.DataFrame(history_sheet.get_all_records())

    # 2. 점수 계산
    m_score = history_df[history_df['이름'] == "김모건"]['변동 점수'].sum() if not history_df.empty else 0
    h_score = history_df[history_df['이름'] == "김모하"]['변동 점수'].sum() if not history_df.empty else 0

    col1, col2 = st.columns(2)
    col1.metric("모건이", f"{int(m_score)}점")
    col2.metric("모하", f"{int(h_score)}점")

    st.divider()

    # 3. 규칙 버튼들
    st.subheader("📋 오늘의 규칙 미션")
    for i, row in rules_df.iterrows():
        with st.expander(f"{row['규칙명']} (+{row['상점']}/-{row['벌점']})"):
            b1, b2, b3, b4 = st.columns(4)
            
            def save_data(name, p, r):
                now = datetime.now().strftime("%Y-%m-%d %H:%M")
                history_sheet.append_row([now, r, p, name])
                st.success(f"{name} 기록 완료!")
                st.rerun()

            if b1.button("모건✅", key=f"m1_{i}"): save_data("김모건", row['상점'], row['규칙명'])
            if b2.button("모건❌", key=f"m2_{i}"): save_data("김모건", -row['벌점'], row['규칙명'])
            if b3.button("모하✅", key=f"h1_{i}"): save_data("김모하", row['상점'], row['규칙명'])
            if b4.button("모하❌", key=f"h2_{i}"): save_data("김모하", -row['벌점'], row['규칙명'])

    st.divider()
    st.subheader("📜 최근 기록")
    st.dataframe(history_df.tail(10), use_container_width=True)

except Exception as e:
    st.error(f"연결 실패: {e}")
    st.info("시트 공유 주소: mgmh-519@morganmohagoodrules.iam.gserviceaccount.com")
