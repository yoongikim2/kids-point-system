import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime, timedelta, timezone
import random

# 페이지 설정
st.set_page_config(page_title="모건&모하의 성장 미션", layout="centered")

# --- 모바일 최적화 CSS ---
st.markdown("""
    <style>
    .main-title { font-size: 24px !important; font-weight: bold; margin-bottom: 10px; text-align: center; }
    .medal-display { font-size: 18px !important; font-weight: bold; text-align: center; margin-bottom: 10px; background-color: #1E1E1E; padding: 10px; border-radius: 10px; }
    .msg-text { font-size: 15px !important; margin-bottom: 5px !important; }
    .stButton > button { width: 100% !important; height: 45px !important; font-size: 15px !important; margin-bottom: 5px !important; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<p class="main-title">🌱 모건&모하의 성장 미션!</p>', unsafe_allow_html=True)

# --- 한국 시간(KST) 설정 ---
KST = timezone(timedelta(hours=9))

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
    rewards_df = pd.DataFrame(rewards_sheet.get_all_records())

    # 보상 시트에 '메달종류' 컬럼이 없으면 기본 생성
    if '메달종류' not in rewards_df.columns:
        rewards_df['메달종류'] = '금메달'

    total_rules_count = len(rules_df)
    today_str = datetime.now(KST).strftime("%Y-%m-%d")

    # 데이터 정제
    if not history_df.empty:
        history_df['이름'] = history_df['이름'].astype(str).str.replace("김", "").str.strip()
        history_df['날짜'] = history_df['일시'].str[:10]

    # [업데이트] 금메달, 도장, 다이아몬드 계산 로직
    def calculate_assets(name):
        if history_df.empty: return 0, 0, 0
        df = history_df[history_df['이름'] == name]
        
        # 금메달 계산
        gold_earned = len(df[df['규칙/보상명'] == "🥇 금메달 획득"])
        gold_spent = df[(df['규칙/보상명'].str.startswith("[보상]")) & (~df['규칙/보상명'].str.contains("다이아"))]['변동 점수'].abs().sum()
        current_gold = int(gold_earned - gold_spent)

        # 칭찬도장 & 다이아몬드 계산
        total_stamps = df[df['규칙/보상명'] == "🌟 칭찬도장"]['변동 점수'].sum()
        dia_spent = df[(df['규칙/보상명'].str.startswith("[보상]")) & (df['규칙/보상명'].str.contains("다이아"))]['변동 점수'].abs().sum()
        
        current_dia = int((total_stamps // 30) - dia_spent)
        current_stamps = int(total_stamps % 30)
        
        return current_gold, current_dia, current_stamps

    m_gold, m_dia, m_stamps = calculate_assets("모건")
    h_gold, h_dia, h_stamps = calculate_assets("모하")

    # 상단 자산 현황판
    col_m, col_h = st.columns(2)
    col_m.markdown(f"<div class='medal-display'>👦 모건<br>🥇 {m_gold}개 &nbsp;|&nbsp; 💎 {m_dia}개</div>", unsafe_allow_html=True)
    col_h.markdown(f"<div class='medal-display'>🧒 모하<br>🥇 {h_gold}개 &nbsp;|&nbsp; 💎 {h_dia}개</div>", unsafe_allow_html=True)

    st.divider()

    def save_log(name, p, r):
        now = datetime.now(KST).strftime("%Y-%m-%d %H:%M")
        history_sheet.append_row([name, now, r, int(p)])
        
        # 금메달 & 칭찬도장 획득 체크
        updated_history = pd.DataFrame(history_sheet.get_all_records())
        updated_history['날짜'] = updated_history['일시'].str[:10]
        today_actions = updated_history[(updated_history['이름'] == name) & (updated_history['날짜'] == today_str)]
        
        success_count = len(today_actions[today_actions['변동 점수'] > 0])
        fail_count = len(today_actions[today_actions['변동 점수'] < 0])
        already_got_medal = not today_actions[today_actions['규칙/보상명'] == "🥇 금메달 획득"].empty

        # 모든 규칙 달성 && 실패 0개 && 오늘 메달 안 받았을 때
        if success_count == total_rules_count and fail_count == 0 and not already_got_medal:
            # 🥇 금메달 1개, 🌟 칭찬도장 3개 동시 지급!
            history_sheet.append_rows([
                [name, now, "🥇 금메달 획득", 1],
                [name, now, "🌟 칭찬도장", 3]
            ])
            st.balloons()
            st.session_state[f'{name}_medal_popup'] = True
        
        st.rerun()

    # 금메달 획득 팝업 노출
    for kid in ["모건", "모하"]:
        if st.session_state.get(f'{kid}_medal_popup'):
            st.success(f"🎊 대박! {kid}이가 오늘 모든 미션을 성공했어요!\n\n**🥇 금메달 1개 + 🌟 칭찬도장 3개 획득!**")
            if st.button(f"{kid}아, 축하해! (닫기)"):
                st.session_state[f'{kid}_medal_popup'] = False
                st.rerun()

    def get_emoji_for_rule(rule_name):
        name = str(rule_name)
        if "기상" in name or "아침" in name: return "⏰"
        if "씻고" in name or "옷" in name: return "👕"
        if "갈 준비" in name: return "🏃‍♂️"
        if "시계" in name or "물통" in name or "물건" in name: return "🎒"
        if "태권도" in name and "시간" in name: return "🥋"
        if "귀가" in name or "끝나고" in name: return "🏠"
        if "식사" in name or "밥" in name: return "🍽️"
        if "예쁜 말" in name or "이야기" in name: return "💖"
        if "숙제" in name or "공부" in name: return "📚"
        if "잠자기" in name or "밤" in name: return "🌙"
        return "⭐"

    # [업데이트] 탭 4개로 확장
    tab1, tab2, tab3, tab4 = st.tabs(["🚀 미션", "🎁 보상", "💮 도장판", "⚙️ 설정"])

    with tab1:
        st.markdown(f'<p class="msg-text">💡 {st.session_state.m_msg}</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="msg-text">💡 {st.session_state.h_msg}</p>', unsafe_allow_html=True)

        for i, row in rules_df.iterrows():
            if not row.get('규칙명'): continue
            m_act = history_df[(history_df['이름'] == "모건") & (history_df['날짜'] == today_str) & (history_df['규칙/보상명'] == row['규칙명'])] if not history_df.empty else pd.DataFrame()
            h_act = history_df[(history_df['이름'] == "모하") & (history_df['날짜'] == today_str) & (history_df['규칙/보상명'] == row['규칙명'])] if not history_df.empty else pd.DataFrame()
            
            with st.expander(f"{get_emoji_for_rule(row['규칙명'])} {row['규칙명']}"):
                st.write("👦 **모건**")
                m_c1, m_c2 = st.columns(2)
                if not m_act.empty:
                    m_c1.button("완료 ✅" if m_act.iloc[0]['변동 점수'] > 0 else "실패 ❌", key=f"m_d_{i}", disabled=True)
                else:
                    if m_c1.button("성공", key=f"m_s_{i}"): save_log("모건", 1, row['규칙명'])
                    if m_c2.button("실패", key=f"m_f_{i}"): save_log("모건", -1, row['규칙명'])
                
                st.write("🧒 **모하**")
                h_c1, h_c2 = st.columns(2)
                if not h_act.empty:
                    h_c1.button("완료 ✅" if h_act.iloc[0]['변동 점수'] > 0 else "실패 ❌", key=f"h_d_{i}", disabled=True)
                else:
                    if h_c1.button("성공", key=f"h_s_{i}"): save_log("모하", 1, row['규칙명'])
                    if h_c2.button("실패", key=f"h_f_{i}"): save_log("모하", -1, row['규칙명'])

    with tab2:
        st.subheader("🛒 금메달 & 다이아몬드 샵")
        for i, row in rewards_df.iterrows():
            if not row.get('보상명'): continue
            needed = abs(int(row['필요점수']))
            currency = str(row.get('메달종류', '금메달')).strip()
            
            is_diamond = (currency == '다이아')
            icon = "💎" if is_diamond else "🥇"
            
            with st.expander(f"🎁 {row['보상명']} ({icon} {needed}개)"):
                c1, c2 = st.columns(2)
                
                # 모건 구매
                m_can = (m_dia >= needed) if is_diamond else (m_gold >= needed)
                if c1.button(f"모건 구매", key=f"rb_m_{i}", disabled=not m_can):
                    suffix = " (다이아)" if is_diamond else " (금메달)"
                    save_log("모건", -needed, f"[보상] {row['보상명']}{suffix}")
                
                # 모하 구매
                h_can = (h_dia >= needed) if is_diamond else (h_gold >= needed)
                if c2.button(f"모하 구매", key=f"rb_h_{i}", disabled=not h_can):
                    suffix = " (다이아)" if is_diamond else " (금메달)"
                    save_log("모하", -needed, f"[보상] {row['보상명']}{suffix}")

    # [신규] 칭찬도장판 탭
    with tab3:
        def draw_stamp_board(name, current_stamps):
            st.markdown(f"#### {'👦' if name=='모건' else '🧒'} {name}의 칭찬도장판 ({current_stamps}/30)")
            st.progress(current_stamps / 30)
            
            grid_html = "<div style='display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px; text-align: center; margin-top: 10px; margin-bottom: 30px;'>"
            for idx in range(30):
                if idx < current_stamps:
                    grid_html += "<div style='font-size: 35px;'>💮</div>"
                else:
                    grid_html += "<div style='font-size: 35px; opacity: 0.1;'>⚪</div>"
            grid_html += "</div>"
            st.markdown(grid_html, unsafe_allow_html=True)

        st.info("💡 10개 미션을 모두 완료하면 도장 3개를 받아요! 30개를 모으면 💎 다이아몬드로 자동 변환됩니다.")
        draw_stamp_board("모건", m_stamps)
        st.divider()
        draw_stamp_board("모하", h_stamps)

    # [신규] 설정 (관리자) 탭
    with tab4:
        st.subheader("⚙️ 미션 및 보상 관리")
        st.write("표를 클릭해서 내용을 바로 수정하거나, 맨 아래 빈 줄에 새로 추가할 수 있습니다.")
        
        st.markdown("##### 📝 오늘의 규칙(미션) 수정")
        edited_rules = st.data_editor(rules_df, num_rows="dynamic", use_container_width=True, key="rule_editor")
        if st.button("미션 저장하기", type="primary"):
            rules_sheet.clear()
            rules_sheet.append_rows([edited_rules.columns.values.tolist()] + edited_rules.values.tolist())
            st.success("✅ 미션이 성공적으로 업데이트되었습니다!")
            st.rerun()

        st.divider()
        st.markdown("##### 🎁 보상 상점 수정")
        st.caption("※ '메달종류' 칸에는 **금메달** 또는 **다이아** 라고 정확히 적어주세요.")
        edited_rewards = st.data_editor(rewards_df, num_rows="dynamic", use_container_width=True, key="reward_editor")
        if st.button("보상 저장하기", type="primary"):
            rewards_sheet.clear()
            rewards_sheet.append_rows([edited_rewards.columns.values.tolist()] + edited_rewards.values.tolist())
            st.success("✅ 보상이 성공적으로 업데이트되었습니다!")
            st.rerun()

    st.divider()
    st.subheader("📜 오늘 기록")
    if not history_df.empty:
        today_logs = history_df[history_df['날짜'] == today_str][['이름', '일시', '규칙/보상명', '변동 점수']].iloc[::-1]
        if not today_logs.empty:
            st.dataframe(today_logs.head(10), use_container_width=True)
        else:
            st.info("오늘 아직 기록된 미션이 없어요. 화이팅!")

except Exception as e:
    st.error(f"오류: {e}")
