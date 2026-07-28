import streamlit as st
import pandas as pd
from datetime import datetime, timezone, timedelta
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
st.set_page_config(
    page_title="App Registro de Colheita", 
    page_icon="icon.png", 
    layout="centered", 
    initial_sidebar_state="collapsed"
)

# ==========================================
# 2. PWA（スマホアプリ化）のための設定注入
# ==========================================
def get_base64_image(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            encoded_string = base64.b64encode(img_file.read()).decode()
            return f"data:image/png;base64,{encoded_string}"
    return ""

ICON_DATA_URI = get_base64_image("icon.png")

APP_NAME = "Reg. Colheita"
THEME_COLOR = "#28a745"

if ICON_DATA_URI:
    pwa_manifest = {
        "name": "Sistema de Registro de Colheita",
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
        
        if (!window.parent.document.getElementById('pwa-injected')) {{
            
            let metaTheme = window.parent.document.createElement('meta');
            metaTheme.name = "theme-color";
            metaTheme.content = "{THEME_COLOR}";
            head.appendChild(metaTheme);

            let metaAppleCapable = window.parent.document.createElement('meta');
            metaAppleCapable.name = "apple-mobile-web-app-capable";
            metaAppleCapable.content = "yes";
            head.appendChild(metaAppleCapable);

            let metaAppleStatus = window.parent.document.createElement('meta');
            metaAppleStatus.name = "apple-mobile-web-app-status-bar-style";
            metaAppleStatus.content = "black-translucent"; 
            head.appendChild(metaAppleStatus);

            let metaAppleTitle = window.parent.document.createElement('meta');
            metaAppleTitle.name = "apple-mobile-web-app-title";
            metaAppleTitle.content = "{APP_NAME}";
            head.appendChild(metaAppleTitle);

            let linkAppleIcon = window.parent.document.createElement('link');
            linkAppleIcon.rel = "apple-touch-icon";
            linkAppleIcon.href = "{ICON_DATA_URI}";
            head.appendChild(linkAppleIcon);

            const manifestJSON = {json.dumps(pwa_manifest)};
            const manifestString = JSON.stringify(manifestJSON);
            const manifestBlob = new Blob([manifestString], {{type: 'application/json'}});
            const manifestURL = URL.createObjectURL(manifestBlob);

            let linkManifest = window.parent.document.createElement('link');
            linkManifest.rel = "manifest";
            linkManifest.href = manifestURL;
            head.appendChild(linkManifest);

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
    .stApp {
        overflow-x: hidden !important;
    }

    @media (max-width: 640px) {
        div[data-testid="stHorizontalBlock"] {
            display: grid !important;
            grid-template-columns: 1fr 1fr !important;
            gap: 10px !important;
            width: 100% !important;
        }
        
        div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
            width: 100% !important;
            min-width: 0px !important;
            max-width: 100% !important;
            padding: 0 !important;
        }
        
        div[data-testid="stHorizontalBlock"] button {
            width: 100% !important;
            min-width: 0px !important;
            height: auto !important;
            min-height: 65px !important;
            padding: 4px !important;
            margin: 0 !important;
        }
        
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
    
    div[data-testid="column"]:nth-of-type(1) button {
        background-color: #28a745 !important;
        color: white !important;
        border-color: #28a745 !important;
    }
    
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
# 共通送信関数
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
                
                # モザンビーク時間 (UTC+2) を設定してタイムスタンプを取得
                mozambique_tz = timezone(timedelta(hours=2))
                timestamp = datetime.now(mozambique_tz).strftime("%Y-%m-%d %H:%M:%S")
                
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
                
                st.toast(f"Dados da linha {st.session_state.selected_line} registrados!")
                
                st.session_state.weight_input_val = ""
                st.session_state.form_counter += 1
                st.session_state.step = 1
        except ValueError:
            st.error("⚠️ Por favor, insira um valor numérico válido.")


# ==========================================
# Step 0: ログイン＆月選択画面
# ==========================================
if st.session_state.step == 0:
    st.title("Sistema de Registro de Colheita")
    st.write("Antes de iniciar o trabalho, selecione o nome de usuário e o mês alvo.")
    
    month_options = ["Selecione o mês", "May-26", "Jun-26", "Jul-26", "Aug-26", "Sep-26", "Oct-26", 
                     "Nov-26", "Dec-26", "Jan-27", "Feb-27", "Mar-27", "Apr-27"]
    
    user_input = st.text_input("Nome de usuário", placeholder="Insira seu nome")
    month_input = st.selectbox("Mês de registro", month_options, index=0)
    
    if st.button("Fazer login e começar", use_container_width=True):
        if user_input and month_input != "Selecione o mês":
            st.session_state.username = user_input
            st.session_state.target_month = month_input
            st.session_state.step = 1
            st.rerun()
        else:
            st.warning("⚠️ Por favor, insira o nome de usuário e selecione o mês corretamente.")
            
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
st.title("Inserir Colheita")
st.caption(f"👤 Responsável: {st.session_state.username} | 📅 Mês Alvo: {st.session_state.target_month}")

try:
    df_master = load_master_data()
    df_log = load_log_data()
except Exception as e:
    st.error(f"Erro ao carregar dados: {e}")
    st.stop()

# 袋数の表示
sack_count = 0
if not df_log.empty and len(df_log.columns) >= 3:
    target_col = df_log.columns[2]
    df_month = df_log[df_log[target_col] == st.session_state.target_month]
    sack_count = len(df_month)
st.info(f"**Quantidade de sacos concluídos em {st.session_state.target_month}: {sack_count} sacos**")


# ==========================================
# Step 1: ライン番号検索画面
# ==========================================
if st.session_state.step == 1:
    
    if st.button("Voltar à tela de login"):
        st.session_state.username = ""
        st.session_state.target_month = ""
        st.session_state.step = 0
        st.rerun()

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
                st.warning("Número da linha correspondente não encontrado.")

    st.text_input(
        "Insira o primeiro número da linha (Enter para avançar)", 
        placeholder="Ex: 1",
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
    st.success(f"Linha selecionada: **{line_name}**")
    
    st.radio("Selecione a unidade", ["kg", "g"], index=0, horizontal=True, key="unit_input")
    
    st.text_input(
        "Insira o peso (Enter para confirmar e enviar)", 
        value="",
        placeholder="Ex: 1.5",
        key="weight_input_val",
        on_change=process_submission
    )

    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Concluir", use_container_width=True):
            process_submission()
            if st.session_state.step == 1: 
                st.rerun()
                
    with col2:
        if st.button("Cancelar", use_container_width=True):
            st.session_state.weight_input_val = ""
            st.session_state.form_counter += 1
            st.session_state.step = 1
            st.rerun()

    st.divider()

    st.write("▼ Detalhes da Linha")
    row_data = st.session_state.matched_row
    cols = st.columns(4)
    cols[0].metric("ID da Mãe", row_data.get("Mother Id", "-"))
    cols[1].metric("Variedade", row_data.get("Variety", "-"))
    cols[2].metric("Nº do Saco", row_data.get("Sack Number", "-"))
    cols[3].metric("Total de Plantas", row_data.get("Total no.of plant", "-"))

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
    st.subheader(f"Histórico de entradas de {st.session_state.target_month}")
    if not df_log.empty and len(df_log.columns) >= 3:
        target_col = df_log.columns[2]
        df_filtered = df_log[df_log[target_col] == st.session_state.target_month]
        
        if not df_filtered.empty:
            df_display = df_filtered.tail(10)[::-1].reset_index(drop=True)
            st.dataframe(df_display, use_container_width=True)
        else:
             st.info(f"Ainda não há histórico para {st.session_state.target_month}.")
    else:
        st.info("Ainda não há histórico de entradas.")
