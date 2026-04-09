import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
import random

# 페이지 설정
st.set_page_config(page_title="모건&모하의 성장 미션", layout="centered")

# --- 모바일 최적화 CSS ---
st.markdown("""
    <style>
    .main-title { font-size: 24px !important; font-weight: bold; margin-bottom: 10px; text-align: center; }
    .medal-display { font-size: 20px !important; font-weight: bold; text-align: center; margin-bottom: 10px; }
    .msg-text { font-size: 15px !important; margin-bottom: 5px !important; }
    .stButton > button { width: 100% !important; height: 45px !important; font-size: 15px !important; margin-bottom: 5px !important; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<p class="main-title">🌱 모건&모하의 금메달 성장 미션!</p>', unsafe_allow_html=True)

# --- 응원 문구 관리 ---
if 'm_msg' not in st.session_state:
    love_msgs = ["사랑해", "너무 사랑해", "오늘도 할수 있어!", "난 멋지니깐!", "규칙을 잘지키자!", "우리집은 내가 지킨다!", "스스로 하는 멋진 나!"]
    st.session_state.m_msg = f"모건, {random.choice(love_msgs)}"
    st.session_state.h_msg = f"모하, {random.choice(love_msgs)}"

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
    
    total_rules_count = len(rules_df) # 총 규칙 개수 (10개)
    today_str = datetime.now().strftime("%Y-%m-%d")

    # 데이터 정제
    if not history_df.empty:
        history_df['이름'] = history_df['이름'].astype(str).str.replace("김", "").str.strip()
        history_df['날짜'] = history_df['일시'].str[:10]

    # [1] 금메달 계산 로직 (획득한 메달 - 사용한 메달)
    def calculate_medals(name):
        if history_df.empty: return 0
        earned = len(history_df[(history_df['이름'] == name) & (history_df['규칙/보상명'] == "🥇 금메달 획득")])
        spent = history_df[(history_df['이름'] == name) & (history_df['규칙/보상명'].str.startswith("[보상]"))]['변동 점수'].abs().sum()
        return int(earned - spent)

    m_medals = calculate_medals("모건")
    h_medals = calculate_medals("모하")

    # 상단 금메달 점수판
    col_m, col_h = st.columns(2)
    col_m.markdown(f"<div class='medal-display'>👦 모건<br>🥇 {m_medals}개</div>", unsafe_allow_html=True)
    col_h.markdown(f"<div class='medal-display'>👧 모하<br>🥇 {h_medals}개</div>", unsafe_allow_html=True)

    st.divider()

    # 기록 저장 및 금메달 판별 함수
    def save_log(name, p, r):
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        # 1. 현재 액션 기록
        history_sheet.append_row([name, now, r, int(p)])
        
        # 2. 금메달 획득 조건 체크 (성공이 10개고 실패가 0개인지)
        # 새로 고침된 데이터를 가져오기 위해 다시 읽기 (간단한 로직을 위해 append 후 즉시 체크)
        updated_history = pd.DataFrame(history_sheet.get_all_records())
        updated_history['날짜'] = updated_history['일시'].str[:10]
        
        today_actions = updated_history[(updated_history['이름'] == name) & (updated_history['날짜'] == today_str)]
        success_count = len(today_actions[today_actions['변동 점수'] > 0])
        fail_count = len(today_actions[today_actions['변동 점수'] < 0])
        
        # 이미 오늘 메달을 받았는지 확인
        already_got_medal = not today_actions[today_actions['규칙/보상명'] == "🥇 금메달 획득"].empty

        if success_count == total_rules_count and fail_count == 0 and not already_got_medal:
            # ★ 금메달 획득! ★
            history_sheet.append_row([name, now, "🥇 금메달 획득", 1])
            st.balloons()
            st.session_state[f'{name}_medal_popup'] = True
        
        st.rerun()

    # 금메달 획득 팝업 노출
    for kid in ["모건", "모하"]:
        if st.session_state.get(f'{kid}_medal_popup'):
            st.success(f"🎊 대박! {kid}이가 오늘 모든 규칙을 지켰어요! 금메달 1개 획득! 🥇")
            if st.button(f"{kid}아, 축하해! (닫기)"):
                st.session_state[f'{kid}_medal_popup'] = False
                st.rerun()

    tab1, tab2 = st.tabs(["🚀 미션", "🎁 보상"])

    with tab1:
        st.markdown(f'<p class="msg-text">💡 {st.session_state.m_msg}</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="msg-text">💡 {st.session_state.h_msg}</p>', unsafe_allow_html=True)

        for i, row in rules_df.iterrows():
            if not row.get('규칙명'): continue
            
            m_act = history_df[(history_df['이름'] == "모건") & (history_df['날짜'] == today_str) & (history_df['규칙/보상명'] == row['규칙명'])] if not history_df.empty else pd.DataFrame()
            h_act = history_df[(history_df['이름'] == "모하") & (history_df['날짜'] == today_str) & (history_df['규칙/보상명'] == row['규칙명'])] if not history_df.empty else pd.DataFrame()

            with st.expander(row['규칙명']):
                # 모건
                st.write("👦 **모건**")
                m_c1, m_c2 = st.columns(2)
                if not m_act.empty:
                    m_c1.button("완료 ✅" if m_act.iloc[0]['변동 점수'] > 0 else "실패 ❌", key=f"m_d_{i}", disabled=True)
                else:
                    if m_c1.button("성공", key=f"m_s_{i}"): save_log("모건", 1, row['규칙명'])
                    if m_c2.button("실패", key=f"m_f_{i}"): save_log("모건", -1, row['규칙명'])
                
                # 모하
                st.write("👧 **모하**")
                h_c1, h_c2 = st.columns(2)
                if not h_act.empty:
                    h_c1.button("완료 ✅" if h_act.iloc[0]['변동 점수'] > 0 else "실패 ❌", key=f"h_d_{i}", disabled=True)
                else:
                    if h_c1.button("성공", key=f"h_s_{i}"): save_log("모하", 1, row['규칙명'])
                    if h_c2.button("실패", key=f"h_f_{i}"): save_log("모하", -1, row['규칙명'])

    with tab2:
        st.subheader("🥇 금메달로 소원 빌기")
        # 요청하신 보상 리스트
        reward_items = [
            {"name": "거실에서 자기", "cost": 1},
            {"name": "주말 게임 1시간 이용권", "cost": 1},
            {"name": "주말 TV 1시간 이용권", "cost": 1},
            {"name": "원하는곳 가기(키즈카페 등)", "cost": 3},
        ]
        
        for idx, item in enumerate(reward_items):
            with st.expander(f"{item['name']} (🥇 {item['cost']}개)"):
                c1, c2 = st.columns(2)
                if c1.button(f"모건 구매", key=f"rb_m_{idx}", disabled=m_medals < item['cost']):
                    save_log("모건", -item['cost'], f"[보상] {item['name']}")
                if c2.button(f"모하 구매", key=f"rb_h_{idx}", disabled=h_medals < item['cost']):
                    save_log("모하", -item['cost'], f"[보상] {item['name']}")

except Exception as e:
    st.error(f"오류: {e}")
