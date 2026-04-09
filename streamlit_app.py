import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime

# 페이지 설정
st.set_page_config(page_title="Family Rules", layout="centered")
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

    rules_df = pd.DataFrame(rules_sheet.get_all_records())
    history_df = pd.DataFrame(history_sheet.get_all_records())

    # 데이터 정제 (이름 앞뒤 공백 제거 및 숫자 변환)
    if not history_df.empty:
        history_df['이름'] = history_df['이름'].astype(str).str.strip()
        history_df['변동 점수'] = pd.to_numeric(history_df['변동 점수'], errors='coerce').fillna(0)

    # 1. 점수 계산 (이름이 정확히 일치해야 함)
    m_score = history_df[history_df['이름'] == "김모건"]['변동 점수'].sum()
    h_score = history_df[history_df['이름'] == "김모하"]['변동 점수'].sum()

    col1, col2 = st.columns(2)
    col1.metric("모건이", f"{int(m_score)}점")
    col2.metric("모하", f"{int(h_score)}점")

    st.divider()

    st.subheader("📋 오늘의 규칙 미션")
    for i, row in rules_df.iterrows():
        if not row['규칙명']: continue
        
        with st.expander(f"{row['규칙명']} (+{row['상점']} / -{row['벌점']})"):
            b1, b2, b3, b4 = st.columns(4)
            
            # 데이터를 넣는 순서를 시트 제목(이름, 일시, 보상명, 변동 점수)에 맞춤
            def save_data(name, p, r):
                now = datetime.now().strftime("%Y-%m-%d %H:%M")
                # ★ 중요: 시트의 컬럼 순서대로 데이터를 넣습니다.
                history_sheet.append_row([name, now, r, int(p)])
                st.success(f"{name} 기록 완료!")
                st.rerun()

            if b1.button("모건✅", key=f"m1_{i}"): save_data("김모건", row['상점'], row['규칙명'])
            if b2.button("모건❌", key=f"m2_{i}"): save_data("김모건", -row['벌점'], row['규칙명'])
            if b3.button("모하✅", key=f"h1_{i}"): save_data("김모하", row['상점'], row['규칙명'])
            if b4.button("모하❌", key=f"h2_{i}"): save_data("김모하", -row['벌점'], row['규칙명'])

    st.divider()
    st.subheader("📜 최근 기록")
    if not history_df.empty:
        # 보기 편하게 최신순으로 정렬해서 보여줌
        st.dataframe(history_df.iloc[::-1].head(10), use_container_width=True)

except Exception as e:
    st.error(f"오류 발생: {e}")
