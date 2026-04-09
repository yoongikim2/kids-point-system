import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# 페이지 설정
st.set_page_config(page_title="모건&모하 규칙 지키기", layout="centered")
st.title("🏆 우리 집 규칙 상점")

# 구글 시트 연결
conn = st.connection("gsheets", type=GSheetsConnection)

# 데이터 불러오기
def get_data():
    # 아빠의 실제 시트 주소입니다!
    url = "https://docs.google.com/spreadsheets/d/1psSU23KIAOpxwdGaJ67Deaz5XWk3VAkFo0DXM2qsCqA/edit"
    
    # 주소와 시트 이름을 정확히 연결합니다.
    rules = conn.read(spreadsheet=url, worksheet="규칙")
    history = conn.read(spreadsheet=url, worksheet="기록")
    return rules, history
rules_df, history_df = get_data()

# 1. 점수 계산 (글라이드 롤업 기능)
def get_total_score(name):
    # '이름' 컬럼에서 해당 이름만 필터링해서 '변동 점수' 합계
    score = history_df[history_df['이름'] == name]['변동 점수'].sum()
    return score

morgan_score = get_total_score("김모건")
moha_score = get_total_score("김모하")

# 2. 메인 화면 점수판 (Big Numbers)
col1, col2 = st.columns(2)
col1.metric("모건이 점수", f"{morgan_score}점")
col2.metric("모하 점수", f"{moha_score}점")

st.divider()

# 3. 규칙 리스트 및 버튼 (글라이드 액션 기능)
st.subheader("📋 오늘의 규칙 미션")

for index, row in rules_df.iterrows():
    with st.expander(f"{row['규칙명']} (+{row['상점']} / -{row['벌점']})"):
        c1, c2, c3, c4 = st.columns(4)
        
        # 버튼 클릭 시 데이터 추가 로직
        def add_record(name, points, rule_name):
            new_row = pd.DataFrame([{
                "일시": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "보상명": rule_name,
                "변동 점수": points,
                "이름": name
            }])
            updated_df = pd.concat([history_df, new_row], ignore_index=True)
            conn.update(worksheet="기록", data=updated_df)
            st.success(f"{name} {points}점 기록 완료!")
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
