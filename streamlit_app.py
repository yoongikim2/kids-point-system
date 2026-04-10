import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime, timedelta, timezone
import random

# 페이지 설정
st.set_page_config(page_title="모건&모하의 성장 미션", layout="centered")

# 모바일 최적화 CSS
st.markdown("""
    <style>
    .main-title { font-size: 24px !important; font-weight: bold; margin-bottom: 10px; text-align: center; }
    .medal-display { font-size: 18px !important; font-weight: bold; text-align: center; margin-bottom: 10px; background-color: #1E1E1E; padding: 10px; border-radius: 10px; }
    .msg-text { font-size: 15px !important; margin-bottom: 5px !important; }
    .stButton > button { width: 100% !important; height: 45px !important; font-size: 15px !important; margin-bottom: 5px !important; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<p class="main-title">🌱 모건&모하의 성장 미션!</p>', unsafe_allow_html=True)

KST = timezone(timedelta(hours=9))

if 'm_msg' not in st.session_state:
    love_msgs = ["사랑해", "너무 사랑해", "오늘도 할수 있어!", "난 멋지니깐!", "규칙을 잘지키자!", "우리집은 내가 지킨다!", "스스로 하는 멋진 나!"]
    st.session_state.m_msg = f"모건, {random.choice(love_msgs)}"
    st.session_state.h_msg = f"모하, {random.choice(love_msgs)}"

@st.cache_resource
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

    @st.cache_data(ttl=600)
    def load_base_data():
        return pd.DataFrame(rules_sheet.get_all_records()), pd.DataFrame(rewards_sheet.get_all_records())

    @st.cache_data(ttl=600)
    def load_history_data():
        return pd.DataFrame(history_sheet.get_all_records())

    rules_df, rewards_df = load_base_data()
    history_df = load_history_data()

    if '이모티콘' not in rules_df.columns:
        rules_df.insert(0, '이모티콘', '⭐')

    if '메달종류' not in rewards_df.columns:
        rewards_df['메달종류'] = '금메달'

    total_rules_count = len(rules_df)
    today_str = datetime.now(KST).strftime("%Y-%m-%d")

    if not history_df.empty:
        history_df['이름'] = history_df['이름'].astype(str).str.replace("김", "").str.strip()
        history_df['날짜'] = history_df['일시'].str[:10]

    def calculate_assets(name):
        if history_df.empty: return 0, 0, 0
        df = history_df[history_df['이름'] == name]
        
        gold_earned = len(df[df['규칙/보상명'] == "🥇 금메달 획득"])
        gold_spent = df[(df['규칙/보상명'].str.startswith("[보상]")) & (~df['규칙/보상명'].str.contains("다이아"))]['변동 점수'].abs().sum()
        current_gold = int(gold_earned - gold_spent)

        total_stamps = df[df['규칙/보상명'] == "🌟 칭찬도장"]['변동 점수'].sum()
        dia_spent = df[(df['규칙/보상명'].str.startswith("[보상]")) & (df['규칙/보상명'].str.contains("다이아"))]['변동 점수'].abs().sum()
        
        current_dia = int((total_stamps // 30) - dia_spent)
        current_stamps = int(total_stamps % 30)
        
        return current_gold, current_dia, current_stamps

    m_gold, m_dia, m_stamps = calculate_assets("모건")
    h_gold, h_dia, h_stamps = calculate_assets("모하")

    col_m, col_h = st.columns(2)
    col_m.markdown(f"<div class='medal-display'>👦 모건<br>🥇 {m_gold}개 &nbsp;|&nbsp; 💎 {m_dia}개</div>", unsafe_allow_html=True)
    col_h.markdown(f"<div class='medal-display'>🧒 모하<br>🥇 {h_gold}개 &nbsp;|&nbsp; 💎 {h_dia}개</div>", unsafe_allow_html=True)

    st.divider()

    def save_log(name, p, r):
        now = datetime.now(KST).strftime("%Y-%m-%d %H:%M")
        history_sheet.append_row([name, now, r, int(p)])
        
        new_row = pd.DataFrame([[name, now, r, int(p), today_str]], columns=['이름', '일시', '규칙/보상명', '변동 점수', '날짜'])
        updated_history = pd.concat([history_df, new_row], ignore_index=True)
        
        today_actions = updated_history[(updated_history['이름'] == name) & (updated_history['날짜'] == today_str)]
        success_count = len(today_actions[today_actions['변동 점수'] > 0])
        already_got_medal = not today_actions[today_actions['규칙/보상명'] == "🥇 금메달 획득"].empty

        if success_count == total_rules_count and not already_got_medal:
            history_sheet.append_rows([
                [name, now, "🥇 금메달 획득", 1],
                [name, now, "🌟 칭찬도장", 3]
            ])
            st.balloons()
            st.session_state[f'{name}_medal_popup'] = True
        
        load_history_data.clear()
        st.rerun()

    for kid in ["모건", "모하"]:
        if st.session_state.get(f'{kid}_medal_popup'):
            # [자연스러운 호칭 패치 적용 완료!]
            josa_ga = "이가" if kid == "모건" else "가"
            josa_ya = "아" if kid == "모건" else "야"
            
            st.success(f"🎊 대박! {kid}{josa_ga} 오늘 모든 미션을 성공했어요!\n\n**🥇 금메달 1개 + 🌟 칭찬도장 3개 획득!**")
            if st.button(f"{kid}{josa_ya}, 축하해! (닫기)"):
                st.session_state[f'{kid}_medal_popup'] = False
                st.rerun()

    tab1, tab2, tab3, tab4 = st.tabs(["🚀 미션", "🎁 보상", "💮 도장판", "⚙️ 설정"])

    with tab1:
        st.markdown(f'<p class="msg-text">💡 {st.session_state.m_msg}</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="msg-text">💡 {st.session_state.h_msg}</p>', unsafe_allow_html=True)

        for i, row in rules_df.iterrows():
            if not row.get('규칙명'): continue
            m_act = history_df[(history_df['이름'] == "모건") & (history_df['날짜'] == today_str) & (history_df['규칙/보상명'] == row['규칙명'])] if not history_df.empty else pd.DataFrame()
            h_act = history_df[(history_df['이름'] == "모하") & (history_df['날짜'] == today_str) & (history_df['규칙/보상명'] == row['규칙명'])] if not history_df.empty else pd.DataFrame()
            
            emoji = str(row.get('이모티콘', '⭐')).strip()
            if not emoji: emoji = '⭐'
            
            with st.expander(f"{emoji} {row['규칙명']}"):
                st.write("👦 **모건**")
                if not m_act.empty:
                    st.button("✨ 참 잘했어요! (완료)", key=f"m_d_{i}", disabled=True, use_container_width=True)
                else:
                    if st.button("🟢 미션 성공!", key=f"m_s_{i}", use_container_width=True): 
                        save_log("모건", 1, row['규칙명'])
                
                st.write("🧒 **모하**")
                if not h_act.empty:
                    st.button("✨ 참 잘했어요! (완료)", key=f"h_d_{i}", disabled=True, use_container_width=True)
                else:
                    if st.button("🟢 미션 성공!", key=f"h_s_{i}", use_container_width=True): 
                        save_log("모하", 1, row['규칙명'])

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
                m_can = (m_dia >= needed) if is_diamond else (m_gold >= needed)
                if c1.button(f"모건 구매", key=f"rb_m_{i}", disabled=not m_can):
                    suffix = " (다이아)" if is_diamond else " (금메달)"
                    save_log("모건", -needed, f"[보상] {row['보상명']}{suffix}")
                
                h_can = (h_dia >= needed) if is_diamond else (h_gold >= needed)
                if c2.button(f"모하 구매", key=f"rb_h_{i}", disabled=not h_can):
                    suffix = " (다이아)" if is_diamond else " (금메달)"
                    save_log("모하", -needed, f"[보상] {row['보상명']}{suffix}")

    with tab3:
        if 'admin_mode' not in st.session_state:
            st.session_state.admin_mode = False

        def draw_stamp_board(name, current_stamps):
            st.markdown(f"#### {'👦' if name=='모건' else '🧒'} {name}의 칭찬도장판 ({current_stamps}/30)")
            st.progress(current_stamps / 30)
            
            grid_html = "<div style='display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px; text-align: center; margin-top: 10px; margin-bottom: 30px;'>"
            for idx in range(30):
                if idx < current_stamps:
                    grid_html += "<div style='font-size: 35px;'>💮</div>"
                else:
                    grid_html += "<div style='font-size: 35px; opacity: 0.4;'>⚫</div>"
            grid_html += "</div>"
            st.markdown(grid_html, unsafe_allow_html=True)

        def draw_interactive_stamp_board(name, current_edit_stamps):
            st.markdown(f"#### 🛠️ {'👦' if name=='모건' else '🧒'} {name}의 칭찬도장판 ({current_edit_stamps}/30) - 수정 모드")
            st.progress(current_edit_stamps / 30)
            
            for r in range(6):
                cols = st.columns(5)
                for c in range(5):
                    idx = r * 5 + c
                    with cols[c]:
                        if idx < current_edit_stamps:
                            if st.button("💮", key=f"rm_{name}_{idx}"):
                                st.session_state[f'edit_{"m" if name=="모건" else "h"}_stamps'] -= 1
                                st.rerun()
                        else:
                            if st.button("⚫", key=f"add_{name}_{idx}"):
                                st.session_state[f'edit_{"m" if name=="모건" else "h"}_stamps'] += 1
                                st.rerun()

        st.info("💡 10개 미션을 모두 완료하면 도장 3개를 받아요! 30개를 모으면 💎 다이아몬드로 자동 변환됩니다.")

        if not st.session_state.admin_mode:
            with st.expander("🔒 도장 수동 관리 (부모님 전용)"):
                pwd = st.text_input("비밀번호 입력", type="password")
                if st.button("확인"):
                    if pwd == "0507":
                        st.session_state.admin_mode = True
                        st.session_state.edit_m_stamps = m_stamps
                        st.session_state.edit_h_stamps = h_stamps
                        st.rerun()
                    else:
                        st.error("비밀번호가 틀렸습니다.")
            
            draw_stamp_board("모건", m_stamps)
            st.divider()
            draw_stamp_board("모하", h_stamps)
        
        else:
            st.success("🔓 도장 관리 모드가 활성화되었습니다. 동그라미를 마구 클릭해도 로딩이 걸리지 않습니다!")
            
            draw_interactive_stamp_board("모건", st.session_state.edit_m_stamps)
            st.divider()
            draw_interactive_stamp_board("모하", st.session_state.edit_h_stamps)
            
            st.divider()
            col_save, col_exit = st.columns(2)
            
            with col_save:
                if st.button("💾 변경된 도장 저장하기", type="primary", use_container_width=True):
                    diff_m = st.session_state.edit_m_stamps - m_stamps
                    diff_h = st.session_state.edit_h_stamps - h_stamps
                    
                    rows_to_add = []
                    now = datetime.now(KST).strftime("%Y-%m-%d %H:%M")
                    if diff_m != 0:
                        rows_to_add.append(["모건", now, "🌟 칭찬도장", diff_m])
                    if diff_h != 0:
                        rows_to_add.append(["모하", now, "🌟 칭찬도장", diff_h])
                    
                    if rows_to_add:
                        history_sheet.append_rows(rows_to_add)
                        load_history_data.clear()
                    
                    st.session_state.admin_mode = False
                    st.success("✅ 구글 시트에 안전하게 저장되었습니다!")
                    st.rerun()
            
            with col_exit:
                if st.button("🚪 일반 모드로 나가기", use_container_width=True):
                    st.session_state.admin_mode = False
                    st.rerun()

    with tab4:
        st.subheader("⚙️ 미션 및 보상 관리")
        st.write("표를 수정하고 반드시 **[저장하기]** 버튼을 눌러야 반영됩니다.")
        
        with st.form("rule_form"):
            st.markdown("##### 📝 오늘의 규칙(미션) 수정")
            st.caption("💡 '이모티콘' 칸에 원하는 이모티콘을 넣으세요. 비워두면 ⭐로 표시됩니다.")
            edited_rules = st.data_editor(rules_df, num_rows="dynamic", use_container_width=True)
            if st.form_submit_button("미션 저장하기", type="primary"):
                rules_sheet.clear()
                rules_sheet.append_rows([edited_rules.columns.values.tolist()] + edited_rules.values.tolist())
                load_base_data.clear() 
                st.success("✅ 미션이 성공적으로 업데이트되었습니다!")
                st.rerun()

        st.divider()
        
        with st.form("reward_form"):
            st.markdown("##### 🎁 보상 상점 수정")
            st.caption("※ '메달종류' 칸에는 **금메달** 또는 **다이아** 라고 정확히 적어주세요.")
            edited_rewards = st.data_editor(rewards_df, num_rows="dynamic", use_container_width=True)
            if st.form_submit_button("보상 저장하기", type="primary"):
                rewards_sheet.clear()
                rewards_sheet.append_rows([edited_rewards.columns.values.tolist()] + edited_rewards.values.tolist())
                load_base_data.clear()
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
