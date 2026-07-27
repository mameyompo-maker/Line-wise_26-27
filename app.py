import streamlit as st
import pandas as pd
from datetime import datetime
import re
import gspread
from google.oauth2.service_account import Credentials
import unicodedata
import streamlit.components.v1 as components
import time
import json
import base64
import os

# ==========================================
# 1. ページ全体の基本設定
# ==========================================
# page_icon="icon.png" とすることで、PC等のブラウザのタブに画像が表示されます
st.set_page_config(
    page_title="収穫量記録アプリ", 
    page_icon="icon.png", 
    layout="centered", 
    initial_sidebar_state="collapsed"
)

# ==========================================
# 2. PWA（スマホアプリ化）のための設定注入
# ==========================================
# ローカル画像をスマホのホーム画面アイコンとして認識させるため、画像データを文字列に変換します
def get_base64_image(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            encoded_string = base64.b64encode(img_file.read()).decode()
            return f"data:image/png;base64,{encoded_string}"
    return ""

# GitHubの同じ階層に置いた "icon.png" を読み込む
ICON_DATA_URI = get_base64_image("icon.png")

APP_NAME = "収穫量記録"
THEME_COLOR = "#28a745" # 時計部分の緑色

# 画像が正しく読み込めた場合のみ、スマホ用設定を注入
if ICON_DATA_URI:
    pwa_manifest = {
        "name": "収穫量記録システム",
        "short_name": APP_NAME,
        "start_url": ".",
        "display": "standalone",
        "theme_color": THEME_COLOR,
        "background_color": "#ffffff",
        "icons": [
            {"src": ICON_DATA_URI, "sizes": "192x192", "type": "image/png"},
            {"src": ICON_DATA_URI, "sizes": "512x512", "type": "image/png"}
        ]
    }

    components.html(
        f"""
        <script>
        const head = window.parent.document.getElementsByTagName('head')[0];
        
        // 重複してタグを追加しないためのチェック
        if (!window.parent.document.getElementById('pwa-injected')) {{
            
            // 1. Android/iOS向け テーマカラー（時計部分の色）
            let metaTheme = window.parent.document.createElement('meta');
            metaTheme.name = "theme-color";
            metaTheme.content = "{THEME_COLOR}";
            head.appendChild(metaTheme);

            // 2. iOS向け フルスクリーン表示設定（URLバー非表示）
            let metaAppleCapable = window.parent.document.createElement('meta');
            metaAppleCapable.name = "apple-mobile-web-app-capable";
            metaAppleCapable.content = "yes";
            head.appendChild(metaAppleCapable);

            // 3. iOS向け ステータスバースタイル
            let metaAppleStatus = window.parent.document.createElement('meta');
            metaAppleStatus.name = "apple-mobile-web-app-status-bar-style";
            metaAppleStatus.content = "black-translucent"; 
            head.appendChild(metaAppleStatus);

            // 4. iOS向け アプリ名
            let metaAppleTitle = window.parent.document.createElement('meta');
            metaAppleTitle.name = "apple-mobile-web-app-title";
            metaAppleTitle.content = "{APP_NAME}";
            head.appendChild(metaAppleTitle);

            // 5. iOS向け ホーム画面アイコン
            let linkAppleIcon = window.parent.document.createElement('link');
            linkAppleIcon.rel = "apple-touch-icon";
            linkAppleIcon.href = "{ICON_DATA_URI}";
            head.appendChild(linkAppleIcon);

            // 6. Android向け マニフェスト設定
            const manifestJSON = {json.dumps(pwa_manifest)};
            const manifestString = JSON.stringify(manifestJSON);
            const manifestBlob = new Blob([manifestString], {{type: 'application/json'}});
            const manifestURL = URL.createObjectURL(manifestBlob);

            let linkManifest = window.parent.document.createElement('link');
            linkManifest.rel = "manifest";
            linkManifest.href = manifestURL;
            head.appendChild(linkManifest);

            // 注入完了フラグ
            let marker = window.parent.document.createElement('meta');
            marker.id = 'pwa-injected';
            head.appendChild(marker);
        }}
        </script>
        """,
        height=0
    )


# ==========================================
# 3. CSS設定
# ==========================================
st.markdown("""
    <style>
    /* 全体の横スクロールを強制的にオフ */
    .stApp {
        overflow-x: hidden !important;
    }

    @media (max-width: 640px) {
        /* 1. Flexboxをやめ、厳格に2分割するGridレイアウトを採用 */
        div[data-testid="stHorizontalBlock"] {
            display: grid !important;
            grid-template-columns: 1fr 1fr !important;
            gap: 10px !important;
            width: 100% !important;
        }
        
        /* 2. カラムをGridのマス目に強制的に従わせる */
        div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
            width: 100% !important;
            min-width: 0px !important;
            max-width: 100% !important;
            padding: 0 !important;
        }
        
        /* 3. ボタン本体がマス目をはみ出さないように設定 */
        div[data-testid="stHorizontalBlock"] button {
            width: 100% !important;
            min-width: 0px !important;
            height: auto !important;
            min-height: 65px !important;
            padding: 4px !important;
            margin: 0 !important;
        }
        
        /* 4. ボタン内部のテキストを強制的に折り返させる */
        div[data-testid="stHorizontalBlock"] button p,
        div[data-testid="stHorizontalBlock"] button div,
        div[data-testid="stHorizontalBlock"] button span {
            white-space: normal !important; 
            word-wrap: break-word !important; 
            text-align: center !important;
            font-size: 0.8rem !important;
            line-height: 1.2 !important;
        }
    }
    
    /* 左側のカラム(1つ目)のボタンを緑色に */
    div[data-testid="column"]:nth-of-type(1) button {
        background-color: #28a745 !important;
        color: white !important;
        border-color: #28a745 !important;
    }
    
    /* 右側のカラム(2つ目)のボタンを赤色に */
    div[data-testid="column"]:nth-of-type(2) button {
        background-color: #dc3545 !important;
        color: white !important;
        border-color: #dc3545 !important;
    }
    </style>
""", unsafe_allow_html=True)


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
        df.columns = df.columns.astype(str).str.strip()
        return df
    return pd.DataFrame()

# --- セッションステートの初期化 ---
if "username" not in st.session_state:
    st.session_state.username = ""
if "target_month" not in st.session_state:
    st.session_state.target_month = ""
if "step" not in st.session_state:
    st.session_state.step = 0
if "form_counter" not in st.session_state:
    st.session_state.form_counter = 0
if "selected_line" not in st.session_state:
    st.session_state.selected_line = None
if "matched_row" not in st.session_state:
    st.session_state.matched_row = None
if "weight_input_val" not in st.session_state:
    st.session_state.weight_input_val = ""


# ==========================================
# 共通送信関数（Enterでもボタンでも呼ばれる）
# ==========================================
def process_submission():
    weight_val = st.session_state.get("weight_input_val", "")
    if weight_val:
        try:
            weight_str = unicodedata.normalize('NFKC', weight_val)
            weight = float(weight_str)
            
            if weight > 0:
                unit = st.session_state.get("unit_input", "kg")
                weight_g = int(weight * 1000) if unit == "kg" else int(weight)
                
                client = get_gspread_client()
                log_sheet = client.open_by_key(SPREADSHEET_KEY).worksheet("Harvest_Log")
                
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                new_row = [
                    timestamp, 
                    st.session_state.username, 
                    st.session_state.target_month, 
                    st.session_state.selected_line, 
                    f"{weight:.2f}",
                    unit, 
                    weight_g
                ]
                log_sheet.append_row(new_row)
                
                st.toast(f"✅ {st.session_state.selected_line} のデータを記録しました！")
                
                # 送信成功したらStep1(検索画面)に戻り、カウンターを進めて入力欄をリフレッシュする
                st.session_state.weight_input_val = ""
                st.session_state.form_counter += 1
                st.session_state.step = 1
        except ValueError:
            st.error("⚠️ 数値を正しく入力してください。")


# ==========================================
# Step 0: ログイン＆月選択画面
# ==========================================
if st.session_state.step == 0:
    st.title("収穫量記録システム")
    st.write("作業を開始する前に、ユーザー名と対象月を選択してください。")
    
    month_options = ["月を選択", "May-26", "Jun-26", "Jul-26", "Aug-26", "Sep-26", "Oct-26", 
                     "Nov-26", "Dec-26", "Jan-27", "Feb-27", "Mar-27", "Apr-27"]
    
    user_input = st.text_input("ユーザー名", placeholder="名前を入力")
    month_input = st.selectbox("記録する対象月", month_options, index=0)
    
    if st.button("ログインして開始", use_container_width=True):
        if user_input and month_input != "月を選択":
            st.session_state.username = user_input
            st.session_state.target_month = month_input
            st.session_state.step = 1
            st.rerun()
        else:
            st.warning("⚠️ ユーザー名を入力し、対象月を正しく選択してください。")
            
    components.html(
        f"""
        <script>
        setTimeout(function() {{
            const inputs = window.parent.document.querySelectorAll('input[type="text"]');
            if (inputs.length > 0) {{ inputs[0].focus(); }}
        }}, 400);
        </script>
        """, height=0
    )
    st.stop()


# --- メイン画面共通 ---
st.title("収穫量入力")
st.caption(f"👤 担当者: {st.session_state.username} | 📅 対象月: {st.session_state.target_month}")

try:
    df_master = load_master_data()
    df_log = load_log_data()
except Exception as e:
    st.error(f"データ読み込みエラー: {e}")
    st.stop()

# 袋数の表示
sack_count = 0
if not df_log.empty and len(df_log.columns) >= 3:
    target_col = df_log.columns[2]
    df_month = df_log[df_log[target_col] == st.session_state.target_month]
    sack_count = len(df_month)
st.info(f" **{st.session_state.target_month} の完了した袋数: {sack_count} 袋**")


# ==========================================
# Step 1: ライン番号検索画面
# ==========================================
if st.session_state.step == 1:
    
    if st.button("ログイン画面に戻る"):
        st.session_state.username = ""
        st.session_state.target_month = ""
        st.session_state.step = 0
        st.rerun()

    # 検索の処理関数（Enter押下時に自動で実行される）
    def process_search():
        search_val = st.session_state[f"search_{st.session_state.form_counter}"]
        if search_val:
            matched_row = None
            for index, row in df_master.iterrows():
                line_str = str(row.get("Line Number", ""))
                match = re.search(r'L(\d+)', line_str)
                if match and match.group(1) == search_val:
                    matched_row = row
                    break
            
            if matched_row is not None:
                st.session_state.selected_line = matched_row.get("Line Number", "")
                st.session_state.matched_row = matched_row
                st.session_state.step = 2
            else:
                st.warning("該当するライン番号が見つかりません。")

    # Enterキーで自動検索されるように on_change を設定
    st.text_input(
        "ラインの最初の番号を入力 (Enterで次へ)", 
        placeholder="例: 1",
        key=f"search_{st.session_state.form_counter}",
        on_change=process_search
    )
    
    components.html(
        f"""
        <script>
        setTimeout(function() {{
            const inputs = window.parent.document.querySelectorAll('input[type="text"]');
            if (inputs.length > 0) {{ inputs[inputs.length - 1].focus(); }}
        }}, 400);
        </script>
        <!-- timestamp: {time.time()} -->
        """, height=0
    )


# ==========================================
# Step 2: 重量入力＆送信画面
# ==========================================
elif st.session_state.step == 2:
    
    line_name = st.session_state.selected_line
    st.success(f"📌 対象ライン: **{line_name}**")
    
    st.radio("単位を選択", ["kg", "g"], index=0, horizontal=True, key="unit_input")
    
    st.text_input(
        "重量を入力 (Enterで確定して送信)", 
        value="",
        placeholder="例: 1.5",
        key="weight_input_val",
        on_change=process_submission
    )

    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("✅ 完了", use_container_width=True):
            process_submission()
            if st.session_state.step == 1: 
                st.rerun()
                
    with col2:
        if st.button("🚫 キャンセル", use_container_width=True):
            st.session_state.weight_input_val = ""
            st.session_state.form_counter += 1
            st.session_state.step = 1
            st.rerun()

    st.divider()

    st.write("▼ ライン詳細情報")
    row_data = st.session_state.matched_row
    cols = st.columns(4)
    cols[0].metric("Mother ID", row_data.get("Mother Id", "-"))
    cols[1].metric("Variety", row_data.get("Variety", "-"))
    cols[2].metric("Sack No.", row_data.get("Sack Number", "-"))
    cols[3].metric("Total Plant", row_data.get("Total no.of plant", "-"))

    components.html(
        f"""
        <script>
        setTimeout(function() {{
            const inputs = window.parent.document.querySelectorAll('input[type="text"]');
            if (inputs.length > 0) {{ inputs[inputs.length - 1].focus(); }}
        }}, 400);
        </script>
        <!-- timestamp: {time.time()} -->
        """, height=0
    )


st.divider()

# --- 共通フッター：履歴表示 ---
if st.session_state.step in [1, 2]:
    st.subheader(f" {st.session_state.target_month} の入力履歴")
    if not df_log.empty and len(df_log.columns) >= 3:
        target_col = df_log.columns[2]
        df_filtered = df_log[df_log[target_col] == st.session_state.target_month]
        
        if not df_filtered.empty:
            df_display = df_filtered.tail(10)[::-1].reset_index(drop=True)
            st.dataframe(df_display, use_container_width=True)
        else:
             st.info(f"{st.session_state.target_month} の履歴はまだありません。")
    else:
        st.info("まだ入力履歴がありません。")
