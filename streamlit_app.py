import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# 한글 인코딩 문제를 피하기 위한 설정
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.detach(), encoding='utf-8')

# 페이지 설정
st.set_page_config(page_title="모건&모하 규칙 지키기", layout="centered")
st.title("🏆 우리 집 규칙 상점")

# 구글 시트 연결
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data():
    url = "https://docs.google.com/spreadsheets/d/1psSU23KIAOpxwdGaJ67Deaz5XWk3VAkFo0DXM2qsCqA/edit"
    # 영어로 바꾼 시트 이름을 사용합니다
    rules = conn.read(spreadsheet=url, worksheet="rules")
    history = conn.read(spreadsheet=url, worksheet="history")
    return rules, history

# 데이터 불러오기
try:
    rules_df, history_df = get_data()

    # 1. 점수 계산
    def get_total_score(name):
        score = history_df[history_df['이름'] == name]['변동 점수'].sum()
        return score

    morgan_score = get_total_score("김모건")
    moha_score = get_total_score("김모하")

    # 2. 메인 화면 점수판
    col1, col2 = st.columns(2)
    col1.metric("모건이 점수", f"{morgan_score}점")
    col2.metric("모하 점수", f"{moha_score}점")

    st.divider()

    # 3. 규칙 리스트 및 버튼
    st.subheader("📋 오늘의 규칙 미션")

    for index, row in rules_df.iterrows():
        with st.expander(f"{row['규칙명']} (+{row['상점']} / -{row['벌점']})"):
            c1, c2, c3, c4 = st.columns(4)
            
            def add_record(name, points, rule_name):
                new_row = pd.DataFrame([{
                    "일시": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "보상명": rule_name,
                    "변동 점수": points,
                    "이름": name
                }])
                updated_df = pd.concat([history_df, new_row], ignore_index=True)
                url = "https://docs.google.com/spreadsheets/d/1psSU23KIAOpxwdGaJ67Deaz5XWk3VAkFo0DXM2qsCqA/edit"
                conn.update(spreadsheet=url, worksheet="history", data=updated_df)
                st.success(f"{name} 기록 완료!")
                st.rerun()

            if c1.button("모건 ✅", key=f"m_s_{index}"):
                add_record("김모건", row['상점'], row['규칙명'])
            if c2.button("모건 ❌", key=f"m_f_{index}"):
                add_record("김모건", -row['벌점'], row['규칙명'])
            if c3.button("모하 ✅", key=f"h_s_{index}"):
                add_record("김모하", row['상점'], row['규칙명'])
            if c4.button("모하 ❌", key=f"h_f_{index}"):
                add_record("김모하", -row['벌점'], row['규칙명'])

    st.divider()
    st.subheader("📜 최근 기록")
    st.dataframe(history_df.tail(10), use_container_width=True)

except Exception as e:
    st.error(f"데이터를 불러오는 중 문제가 발생했습니다: {e}")
    st.info("구글 시트의 탭 이름이 'rules'와 'history'로 되어 있는지 확인해 주세요!")
