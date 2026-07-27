import streamlit as st
import pandas as pd
from datetime import datetime
import re
import gspread
from google.oauth2.service_account import Credentials
import json

# --- アプリの初期設定（スマホ向けに最適化） ---
st.set_page_config(page_title="収穫量記録アプリ", layout="centered", initial_sidebar_state="collapsed")

# --- Googleスプレッドシートへの接続設定 ---
@st.cache_resource
def get_gspread_client():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    # Secretsから文字列として取得し、json.loadsで辞書型（データ）に自動変換する
    creds_json = json.loads(st.secrets["gcp_service_account"])
    
    credentials = Credentials.from_service_account_info(
        creds_json,
        scopes=scopes
    )
    return gspread.authorize(credentials)

# スプレッドシートのキー（URLの /d/〇〇〇/ の部分）を指定してください
SPREADSHEET_KEY = "/d/1ulQjYCYlhZjxGMO3iTWGPmxM7U-O-NkCs2OOm6mY1Wk/edit?gid=0#gid=0"
@st.cache_data(ttl=600) # 10分ごとにマスタデータをキャッシュ更新
def load_master_data():
    client = get_gspread_client()
    sheet = client.open_by_key(SPREADSHEET_KEY).worksheet("Master")
    data = sheet.get_all_records()
    return pd.DataFrame(data)

def load_log_data():
    client = get_gspread_client()
    sheet = client.open_by_key(SPREADSHEET_KEY).worksheet("Harvest_Log")
    data = sheet.get_all_records()
    return pd.DataFrame(data)

# --- セッションステート（状態保持）の初期化 ---
if "username" not in st.session_state:
    st.session_state.username = ""
if "search_input" not in st.session_state:
    st.session_state.search_input = ""
if "weight_input" not in st.session_state:
    st.session_state.weight_input = 0.0

# --- 1. ログイン画面 ---
if not st.session_state.username:
    st.title("🌾 収穫量記録システム")
    st.write("作業を開始するにはユーザー名を入力してください。")
    
    user_input = st.text_input("ユーザー名", placeholder="例: Yamada")
    if st.button("ログイン") or user_input:
        if user_input:
            st.session_state.username = user_input
            st.rerun()
    st.stop() # ログインするまで以降のコードは実行しない

# --- データ送信処理（エンターキーで発火） ---
def submit_harvest(line_str):
    weight = st.session_state.weight_input
    if weight > 0:
        unit = st.session_state.unit_input
        # kgの場合はgに変換
        weight_g = weight * 1000 if unit == "kg" else weight
        
        # スプレッドシートへ書き込み
        client = get_gspread_client()
        log_sheet = client.open_by_key(SPREADSHEET_KEY).worksheet("Harvest_Log")
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        new_row = [
            timestamp, 
            st.session_state.username, 
            line_str, 
            weight, 
            unit, 
            weight_g
        ]
        log_sheet.append_row(new_row)
        
        # 送信完了メッセージと入力のリセット
        st.toast(f"✅ {line_str} のデータ（{weight}{unit}）を記録しました！")
        st.session_state.weight_input = 0.0
        st.session_state.search_input = "" # 次の入力に備えて検索欄もクリア

def cancel_input():
    st.session_state.weight_input = 0.0
    st.session_state.search_input = ""

# --- 2. メイン画面（検索と入力） ---
st.title("収穫量入力")
st.caption(f"👤 担当者: {st.session_state.username}")

try:
    df_master = load_master_data()

# 変更後（エラーの正体 e を画面に出す）
except Exception as e:
    st.error(f"エラーが発生しました: {e}")
    st.stop()

# ライン番号の検索（最初の数字を入力）
search_val = st.text_input("ラインの最初の番号を入力", key="search_input", placeholder="例: 1 (L1 to L9の場合)")

if search_val:
    # Lの後の数字が検索値と一致するか判定するロジック
    matched_row = None
    for index, row in df_master.iterrows():
        line_str = str(row.get("Line Number", ""))
        match = re.search(r'L(\d+)', line_str)
        if match and match.group(1) == search_val:
            matched_row = row
            break
    
    if matched_row is not None:
        line_name = matched_row["Line Number"]
        st.success(f"📌 対象ライン: **{line_name}**")
        
        # 確認情報の表示
        cols = st.columns(4)
        cols[0].metric("Mother ID", matched_row.get("Mother Id", "-"))
        cols[1].metric("Variety", matched_row.get("Variety", "-"))
        cols[2].metric("Sack No.", matched_row.get("Sack Number", "-"))
        cols[3].metric("Total Plant", matched_row.get("Total no.of plant", "-"))
        
        st.divider()
        
        # 入力フォーム（単位と重量）
        st.radio("単位を選択", ["kg", "g"], index=0, horizontal=True, key="unit_input")
        
        # on_changeでエンターキー押下時にsubmit_harvest関数を呼び出す
        st.number_input(
            "重量を入力 (Enterで確定)", 
            min_value=0.0, 
            step=0.1, 
            format="%.2f",
            key="weight_input",
            on_change=submit_harvest,
            args=(line_name,) # コールバック関数にライン名を渡す
        )
        
        # キャンセルボタン
        if st.button("🚫 キャンセル（クリア）", on_click=cancel_input):
            pass

    else:
        st.warning("該当するライン番号が見つかりません。")

st.divider()

# --- 3. 履歴の表示と訂正機能 ---
st.subheader("📝 本日の入力履歴と訂正")
try:
    df_log = load_log_data()
    if not df_log.empty:
        # 今日の日付のデータのみ、またはユーザー自身のデータのみに絞ることも可能
        # 今回はシンプルに最新10件を降順で表示
        df_log_recent = df_log.tail(10)[::-1].reset_index(drop=True)
        
        st.write("※表のセルを直接タップ（クリック）して数値を修正できます。")
        # 編集可能なデータフレームを表示
        edited_df = st.data_editor(
            df_log_recent,
            use_container_width=True,
            num_rows="dynamic",
            key="data_editor"
        )
        
        # 訂正を保存するボタン
        if st.button("🔄 訂正をスプレッドシートに反映"):
            client = get_gspread_client()
            sheet = client.open_by_key(SPREADSHEET_KEY).worksheet("Harvest_Log")
            
            # Gspreadで全データを上書き更新（※実運用ではID等をキーにした行ごとの更新が安全です）
            # ここでは簡易的に、元のdf_logをedited_dfの内容で上書きして全更新します
            df_log.update(edited_df)
            
            # g（グラム）列の再計算（訂正漏れを防ぐため）
            df_log['Weight in Grams'] = df_log.apply(
                lambda x: float(x['Input Weight']) * 1000 if x['Unit'] == 'kg' else float(x['Input Weight']), axis=1
            )
            
            sheet.clear()
            sheet.update([df_log.columns.values.tolist()] + df_log.values.tolist())
            st.success("変更を保存しました！")
            st.rerun()
            
    else:
        st.info("まだ入力履歴がありません。")
except Exception as e:
    st.error("履歴データの取得に失敗しました。")
