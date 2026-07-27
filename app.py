import streamlit as st
import pandas as pd
from datetime import datetime
import re
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="収穫量記録アプリ", layout="centered", initial_sidebar_state="collapsed")

@st.cache_resource
def get_gspread_client():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    credentials = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=scopes
    )
    return gspread.authorize(credentials)

SPREADSHEET_KEY = "1ulQjYCYlhZjxGMO3iTWGPmxM7U-O-NkCs2OOm6mY1Wk"

@st.cache_data(ttl=600)
def load_master_data():
    client = get_gspread_client()
    sheet = client.open_by_key(SPREADSHEET_KEY).worksheet("Master")
    data = sheet.get_all_values()
    if len(data) > 0:
        df = pd.DataFrame(data[1:], columns=data[0])
        return df
    return pd.DataFrame()

def load_log_data():
    client = get_gspread_client()
    sheet = client.open_by_key(SPREADSHEET_KEY).worksheet("Harvest_Log")
    data = sheet.get_all_values()
    if len(data) > 0:
        df = pd.DataFrame(data[1:], columns=data[0])
        return df
    return pd.DataFrame()

if "username" not in st.session_state:
    st.session_state.username = ""
if "target_month" not in st.session_state:
    st.session_state.target_month = ""
if "search_input" not in st.session_state:
    st.session_state.search_input = ""
if "weight_input" not in st.session_state:
    st.session_state.weight_input = None

# --- ログイン＆月選択画面 ---
if not st.session_state.username or not st.session_state.target_month:
    st.title("🌾 収穫量記録システム")
    st.write("作業を開始する前に、ユーザー名と対象月を選択してください。")
    
    month_options = ["May-26", "Jun-26", "Jul-26", "Aug-26", "Sep-26", "Oct-26", 
                     "Nov-26", "Dec-26", "Jan-27", "Feb-27", "Mar-27", "Apr-27"]
    
    user_input = st.text_input("ユーザー名", placeholder="例: Ze Maria")
    month_input = st.selectbox("記録する対象月", month_options, index=2)
    
    if st.button("ログインして開始"):
        if user_input:
            st.session_state.username = user_input
            st.session_state.target_month = month_input
            st.rerun()
        else:
            st.warning("ユーザー名を入力してください。")
    st.stop()

# --- データ送信処理 ---
def submit_harvest(line_str=None):
    weight = st.session_state.weight_input
    if weight is not None and weight > 0:
        unit = st.session_state.unit_input
        weight_g = int(weight * 1000) if unit == "kg" else int(weight)
        
        client = get_gspread_client()
        log_sheet = client.open_by_key(SPREADSHEET_KEY).worksheet("Harvest_Log")
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        new_row = [
            timestamp, 
            st.session_state.username, 
            st.session_state.target_month, 
            line_str, 
            f"{weight:.2f}",
            unit, 
            weight_g
        ]
        log_sheet.append_row(new_row)
        
        st.toast(f"✅ {line_str} のデータ（{weight:.2f}{unit}）を記録しました！")
        # 💡 ここで入力値をリセットすることで、自動的に「ライン検索画面」に戻る仕組みになっています
        st.session_state.weight_input = None
        st.session_state.search_input = ""

def cancel_input():
    st.session_state.weight_input = None
    st.session_state.search_input = ""


# --- メイン画面 ---
st.title("収穫量入力")
st.caption(f"👤 担当者: {st.session_state.username} | 📅 対象月: {st.session_state.target_month}")

try:
    df_master = load_master_data()
    df_log = load_log_data()
except Exception as e:
    st.error(f"データ読み込みエラー: {e}")
    st.stop()

# --- 月間合計の計算と表示 ---
total_kg = 0.0
if not df_log.empty and 'Target Month' in df_log.columns and 'Weight in Grams' in df_log.columns:
    df_month = df_log[df_log['Target Month'] == st.session_state.target_month]
    if not df_month.empty:
        # スプレッドシート上の文字列データを数値に変換して合計する
        total_g = pd.to_numeric(df_month['Weight in Grams'], errors='coerce').sum()
        total_kg = total_g / 1000

st.info(f"📊 **{st.session_state.target_month} の合計収穫量: {total_kg:,.2f} kg**")


# --- ライン検索（完了ボタン付き横並びレイアウト） ---
col_s1, col_s2 = st.columns([3, 1])
with col_s1:
    search_val = st.text_input("ラインの最初の番号を入力", key="search_input", placeholder="例: 1")
with col_s2:
    # 検索ボタンの位置をテキスト入力欄と合わせるための空白設定
    st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
    st.button("🔍 完了", key="search_btn", use_container_width=True)

# 検索値が入った瞬間に「重量入力」画面が自動で開く
if search_val:
    matched_row = None
    for index, row in df_master.iterrows():
        line_str = str(row.get("Line Number", ""))
        match = re.search(r'L(\d+)', line_str)
        if match and match.group(1) == search_val:
            matched_row = row
            break
    
    if matched_row is not None:
        line_name = matched_row.get("Line Number", "")
        st.success(f"📌 対象ライン: **{line_name}**")
        
        st.radio("単位を選択", ["kg", "g"], index=0, horizontal=True, key="unit_input")
        
        st.number_input(
            "重量を入力 (Enterで確定)", 
            min_value=0.0, 
            step=0.1, 
            format="%.2f",
            value=None,
            placeholder="例: 1.00",
            key="weight_input",
            on_change=submit_harvest,
            args=(line_name,)
        )
        
        btn_col1, btn_col2 = st.columns(2)
        with btn_col1:
            if st.button("✅ 完了", key="submit_btn", use_container_width=True):
                if st.session_state.weight_input is not None:
                    submit_harvest(line_name)
                    st.rerun()
        with btn_col2:
            if st.button("🚫 キャンセル", on_click=cancel_input, use_container_width=True):
                pass
        
        st.divider()

        st.write("▼ ライン詳細情報")
        cols = st.columns(4)
        cols[0].metric("Mother ID", matched_row.get("Mother Id", "-"))
        cols[1].metric("Variety", matched_row.get("Variety", "-"))
        cols[2].metric("Sack No.", matched_row.get("Sack Number", "-"))
        cols[3].metric("Total Plant", matched_row.get("Total no.of plant", "-"))
        
    else:
        st.warning("該当するライン番号が見つかりません。")

st.divider()

# --- 履歴表示 ---
st.subheader(f"📝 {st.session_state.target_month} の入力履歴")
if not df_log.empty and 'Target Month' in df_log.columns:
    df_filtered = df_log[df_log['Target Month'] == st.session_state.target_month]
    
    if not df_filtered.empty:
        df_display = df_filtered.tail(10)[::-1].reset_index(drop=True)
        st.dataframe(df_display, use_container_width=True)
    else:
         st.info(f"{st.session_state.target_month} の履歴はまだありません。")
else:
    st.info("まだ入力履歴がありません。")
