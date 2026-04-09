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

    # 데이터 가져오기
    rules_df = pd.DataFrame(rules_sheet.get_all_records())
    history_df = pd.DataFrame(history_sheet.get_all_records())

    # 1. 점수 계산 (데이터가 없을 때를 대비해 안전하게 처리)
    m_score = 0
    h_score = 0
    
    # '이름' 칸이 있고 데이터가 있을 때만 계산합니다.
    if not history_df.empty and '이름' in history_df.columns:
        history_df['이름'] = history_df['이름'].astype(str).str.strip()
        history_df['변동 점수'] = pd.to_numeric(history_df['변동 점수'], errors='coerce').fillna(0)
        
        m_score = history_df[history_df['이름'] == "김모건"]['변동 점수'].sum()
        h_score = history_df[history_df['이름'] == "김모하"]['변동 점수'].sum()

    col1, col2 = st.columns(2)
    col1.metric("모건이", f"{int(m_score)}점")
    col2.metric("모하", f"{int(h_score)}점")

    st.divider()

    st.subheader("📋 오늘의 규칙 미션")
    
    if not rules_df.empty:
        for i, row in rules_df.iterrows():
            if '규칙명' not in row or not row['규칙명']: continue
            
            with st.expander(f"{row['규칙명']} (+{row.get('상점', 0)} / -{row.get('벌점', 0)})"):
                b1, b2, b3, b4 = st.columns(4)
                
                def save_data(name, p, r):
                    now = datetime.now().strftime("%Y-%m-%d %H:%M")
                    # [이름, 일시, 규칙/보상명, 변동 점수] 순서로 추가
                    history_sheet.append_row([name, now, r, int(p)])
                    st.success(f"{name} 기록 완료!")
                    st.rerun()

                if b1.button("모건✅", key=f"m1_{i}"): save_data("김모건", row.get('상점', 0), row['규칙명'])
                if b2.button("모건❌", key=f"m2_{i}"): save_data("김모건", -row.get('벌점', 0), row['규칙명'])
                if b3.button("모하✅", key=f"h1_{i}"): save_data("김모하", row.get('상점', 0), row['규칙명'])
                if b4.button("모하❌", key=f"h2_{i}"): save_data("김모하", -row.get('벌점', 0), row['규칙명'])
    else:
        st.info("rules 시트에 규칙을 입력해 주세요!")

    st.divider()
    st.subheader("📜 최근 기록")
    if not history_df.empty and '이름' in history_df.columns:
        st.dataframe(history_df.iloc[::-1].head(10), use_container_width=True)
    else:
        st.write("아직 기록이 없습니다. 첫 점수를 눌러보세요!")

except Exception as e:
    st.error(f"오류 발생: {e}")
