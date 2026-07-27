import streamlit as st
import pandas as pd
from datetime import datetime
import re
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="収穫量記録アプリ", layout="centered", initial_sidebar_state="collapsed")

# --- 1. TOML形式での認証情報読み込みに戻す ---
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

# セッションステートの初期化
if "username" not in st.session_state:
    st.session_state.username = ""
if "target_month" not in st.session_state:
    st.session_state.target_month = ""
if "search_input" not in st.session_state:
    st.session_state.search_input = ""
# プレースホルダーを機能させるため、初期値をNoneに設定
if "weight_input" not in st.session_state:
    st.session_state.weight_input = None

# --- ログイン＆月選択画面 ---
if not st.session_state.username or not st.session_state.target_month:
    st.title("🌾 収穫量記録システム")
    st.write("作業を開始する前に、ユーザー名と対象月を選択してください。")
    
    month_options = ["May-26", "Jun-26", "Jul-26", "Aug-26", "Sep-26", "Oct-26", 
                     "Nov-26", "Dec-26", "Jan-27", "Feb-27", "Mar-27", "Apr-27"]
    
    user_input = st.text_input("ユーザー名", placeholder="例: Yamada")
    month_input = st.selectbox("記録する対象月", month_options, index=2)
    
    if st.button("ログインして開始"):
        if user_input:
            st.session_state.username = user_input
            st.session_state.target_month = month_input
            st.rerun()
        else:
            st.warning("ユーザー名を入力してください。")
    st.stop()

# --- 4. データ送信処理（小数点2桁・整数変換） ---
def submit_harvest(line_str=None):
    weight = st.session_state.weight_input
    if weight is not None and weight > 0:
        unit = st.session_state.unit_input
        
        # kgの場合は1000倍して整数(int)にする（1.00kg -> 1000）
        weight_g = int(weight * 1000) if unit == "kg" else int(weight)
        
        client = get_gspread_client()
        log_sheet = client.open_by_key(SPREADSHEET_KEY).worksheet("Harvest_Log")
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        new_row = [
            timestamp, 
            st.session_state.username, 
            st.session_state.target_month, 
            line_str, 
            f"{weight:.2f}", # スプレッドシートには「1.00」の形で記録
            unit, 
            weight_g
        ]
        log_sheet.append_row(new_row)
        
        st.toast(f"✅ {line_str} のデータ（{weight:.2f}{unit}）を {st.session_state.target_month}分 として記録しました！")
        # 次の入力のためにリセット
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
except Exception as e:
    st.error(f"マスタ読み込みエラー: {e}")
    st.stop()

search_val = st.text_input("ラインの最初の番号を入力", key="search_input", placeholder="例: 1 (L1 to L9の場合)")

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
        
        cols = st.columns(4)
        cols[0].metric("Mother ID", matched_row.get("Mother Id", "-"))
        cols[1].metric("Variety", matched_row.get("Variety", "-"))
        cols[2].metric("Sack No.", matched_row.get("Sack Number", "-"))
        cols[3].metric("Total Plant", matched_row.get("Total no.of plant", "-"))
        
        st.divider()
        
        st.radio("単位を選択", ["kg", "g"], index=0, horizontal=True, key="unit_input")
        
        # --- 3. プレースホルダーと自動小数点表示の設定 ---
        st.number_input(
            "重量を入力 (Enterで確定)", 
            min_value=0.0, 
            step=0.1, 
            format="%.2f",
            value=None,  # これをNoneにすることで、最初から数字が入っていない状態になります
            placeholder="例: 1.00", # 消す必要のない薄い文字
            key="weight_input",
            on_change=submit_harvest,
            args=(line_name,)
        )
        
        # --- 2. 完了ボタンとキャンセルボタンを横並びで配置 ---
        btn_col1, btn_col2 = st.columns(2)
        with btn_col1:
            # 完了ボタン（押されたらsubmit_harvestを実行）
            if st.button("✅ 完了", use_container_width=True):
                # 重量に値が入っている場合のみ送信処理を行う
                if st.session_state.weight_input is not None:
                    submit_harvest(line_name)
                    st.rerun() # 画面をリフレッシュ
        with btn_col2:
            # キャンセルボタン
            if st.button("🚫 キャンセル", on_click=cancel_input, use_container_width=True):
                pass
    else:
        st.warning("該当するライン番号が見つかりません。")

st.divider()

# --- 履歴表示 ---
st.subheader(f"📝 {st.session_state.target_month} の入力履歴")
try:
    df_log = load_log_data()
    if not df_log.empty and 'Target Month' in df_log.columns:
        df_filtered = df_log[df_log['Target Month'] == st.session_state.target_month]
        
        if not df_filtered.empty:
            df_display = df_filtered.tail(10)[::-1].reset_index(drop=True)
            st.dataframe(df_display, use_container_width=True)
        else:
             st.info(f"{st.session_state.target_month} の履歴はまだありません。")
    else:
        st.info("まだ入力履歴がありません。")
except Exception as e:
    st.error(f"履歴取得エラー: {e}")
