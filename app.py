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
import shutil

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
# 2. PWA（スマホアプリ化）のための設定
# ==========================================
APP_NAME = "Reg. Colheita"
APP_FULL_NAME = "Sistema de Registro de Colheita"
THEME_COLOR = "#28a745"


def _patch_streamlit_pwa():
    """
    Streamlit本体が配布している静的ファイル
    (index.html / manifest.json / favicon.png) を直接書き換えてPWA化する。
    各ステップの結果を辞書で返し、?debug=1 で確認できるようにする。
    """
    log = {}
    try:
        st_static_dir = os.path.join(os.path.dirname(st.__file__), "static")
        index_path = os.path.join(st_static_dir, "index.html")
        manifest_path = os.path.join(st_static_dir, "manifest.json")
        favicon_path = os.path.join(st_static_dir, "favicon.png")
        apple_icon_path = os.path.join(st_static_dir, "apple-touch-icon.png")

        log["streamlit_version"] = st.__version__
        log["static_dir"] = st_static_dir
        log["static_dir_exists"] = os.path.isdir(st_static_dir)
        log["index_exists"] = os.path.exists(index_path)
        log["writable"] = os.access(st_static_dir, os.W_OK)

        if not log["static_dir_exists"] or not log["index_exists"]:
            log["result"] = "NG: Streamlitのstaticフォルダが見つからない"
            return log

        with open(index_path, "r", encoding="utf-8") as f:
            html = f.read()

        log["index_size"] = len(html)
        log["has_title_tag"] = "<title>Streamlit</title>" in html
        log["has_shortcut_icon"] = '<link rel="shortcut icon" href="/favicon.png" />' in html
        log["has_manifest_link"] = 'rel="manifest"' in html
        log["head_snippet"] = html[:800]

        if "<!-- pwa-patched -->" in html:
            log["result"] = "OK: 既にパッチ適用済み"
            return log

        # 1. manifest.json を自分のアプリ用に上書き
        pwa_manifest = {
            "name": APP_FULL_NAME,
            "short_name": APP_NAME,
            "start_url": "/",
            "scope": "/",
            "display": "standalone",
            "theme_color": THEME_COLOR,
            "background_color": "#ffffff",
            "icons": [
                {"src": "/favicon.png", "sizes": "192x192", "type": "image/png"},
                {"src": "/apple-touch-icon.png", "sizes": "512x512", "type": "image/png"}
            ]
        }
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(pwa_manifest, f, ensure_ascii=False)
        log["manifest_written"] = True

        # 2. favicon.png / apple-touch-icon.png を自前のアイコンで上書き
        repo_dir = os.path.dirname(os.path.abspath(__file__))
        source_icon = os.path.join(repo_dir, "static", "icon-512.png")
        if not os.path.exists(source_icon):
            source_icon = os.path.join(repo_dir, "icon.png")
        log["source_icon"] = source_icon
        log["source_icon_exists"] = os.path.exists(source_icon)
        if log["source_icon_exists"]:
            shutil.copyfile(source_icon, favicon_path)
            shutil.copyfile(source_icon, apple_icon_path)
            log["icons_copied"] = True

        # 3. index.html にタイトルとメタタグを追記
        html = html.replace("<title>Streamlit</title>", f"<title>{APP_NAME}</title>")
        injected_tags = (
            f'<link rel="manifest" href="/manifest.json">'
            f'<meta name="theme-color" content="{THEME_COLOR}">'
            f'<meta name="apple-mobile-web-app-capable" content="yes">'
            f'<meta name="mobile-web-app-capable" content="yes">'
            f'<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">'
            f'<meta name="apple-mobile-web-app-title" content="{APP_NAME}">'
            f'<link rel="apple-touch-icon" href="/apple-touch-icon.png">'
            f'<!-- pwa-patched -->'
        )
        # 既存のmanifestリンクがあれば先に除去（重複防止）
        html = re.sub(r'<link[^>]*rel="manifest"[^>]*>', '', html)

        if "</head>" in html:
            html = html.replace("</head>", injected_tags + "</head>", 1)
            log["injection_point"] = "</head>"
        else:
            log["result"] = "NG: </head>が見つからない"
            return log

        with open(index_path, "w", encoding="utf-8") as f:
            f.write(html)
        log["index_written"] = True
        log["result"] = "OK: パッチを新規適用した"

    except Exception as e:
        log["result"] = f"NG: 例外発生 → {type(e).__name__}: {e}"
    return log


PWA_LOG = _patch_streamlit_pwa()

# ?debug=1 を付けてアクセスすると診断結果を表示
try:
    _qp = dict(st.query_params)
except Exception:
    _qp = st.experimental_get_query_params()
if _qp.get("debug"):
    st.warning("🔧 PWA診断モード")
    st.json(PWA_LOG)
    st.stop()


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
            font-weight: bold !important;
        }
    }

    /* 完了ボタン（緑の枠） */
    div[data-testid="column"]:nth-of-type(1) button {
        background-color: transparent !important;
        color: #28a745 !important;
        border: 2px solid #28a745 !important;
    }

    /* キャンセルボタン（赤の枠） */
    div[data-testid="column"]:nth-of-type(2) button {
        background-color: transparent !important;
        color: #dc3545 !important;
        border: 2px solid #dc3545 !important;
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
        df.columns = df.columns.astype(str).str.strip()
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
if "candidate_rows" not in st.session_state:
    st.session_state.candidate_rows = []
if "searched_number" not in st.session_state:
    st.session_state.searched_number = ""
if "search_error" not in st.session_state:
    st.session_state.search_error = ""


# ==========================================
# ライン番号のパース用ヘルパー
# ==========================================
def get_line_numbers(line_str):
    """'L586' -> [586] / 'L586 to L593' や 'L586-L593' -> [586, 593]"""
    nums = re.findall(r'L\s*(\d+)', str(line_str), flags=re.IGNORECASE)
    return [int(n) for n in nums]


def get_first_number(line_str):
    nums = get_line_numbers(line_str)
    return nums[0] if nums else None


def describe_row(row):
    """選択ボタンに出す説明文"""
    nums = get_line_numbers(row.get("Line Number", ""))
    if len(nums) >= 2:
        span = nums[-1] - nums[0] + 1
        return f"Faixa de {span} linhas ({nums[0]}-{nums[-1]})"
    return "Linha unica"


# ==========================================
# 共通送信関数
# ==========================================
def process_submission():
    weight_key = f"weight_{st.session_state.form_counter}"
    weight_val = st.session_state.get(weight_key, "")
    if weight_val:
        try:
            weight_str = unicodedata.normalize('NFKC', weight_val)
            weight = float(weight_str)

            if weight > 0:
                unit = st.session_state.get("unit_input", "kg")
                weight_g = int(weight * 1000) if unit == "kg" else int(weight)

                client = get_gspread_client()
                log_sheet = client.open_by_key(SPREADSHEET_KEY).worksheet("Harvest_Log")

                # モザンビーク時間 (UTC+2)
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

                st.session_state.candidate_rows = []
                st.session_state.searched_number = ""
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
        """
        <script>
        setTimeout(function() {
            const inputs = window.parent.document.querySelectorAll('input[type="text"]');
            if (inputs.length > 0) { inputs[0].focus(); }
        }, 400);
        </script>
        """,
        height=0
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


def already_registered(line_name):
    """その月に同じ Line Number が既に登録済みか"""
    if df_log.empty or len(df_log.columns) < 4:
        return False
    month_col = df_log.columns[2]
    line_col = df_log.columns[3]
    hit = df_log[
        (df_log[month_col] == st.session_state.target_month)
        & (df_log[line_col].astype(str).str.strip() == str(line_name).strip())
    ]
    return not hit.empty


# ==========================================
# Step 1: ライン番号検索画面
# ==========================================
if st.session_state.step == 1:

    if st.button("Voltar à tela de login"):
        st.session_state.username = ""
        st.session_state.target_month = ""
        st.session_state.candidate_rows = []
        st.session_state.step = 0
        st.rerun()

    def process_search():
        raw = st.session_state.get(f"search_{st.session_state.form_counter}", "")
        search_val = unicodedata.normalize('NFKC', str(raw)).strip()
        st.session_state.search_error = ""

        if not search_val:
            return

        if not search_val.isdigit():
            st.session_state.search_error = "Insira apenas números."
            return

        target_num = int(search_val)

        matched_rows = []
        for _, row in df_master.iterrows():
            first_num = get_first_number(row.get("Line Number", ""))
            if first_num is not None and first_num == target_num:
                matched_rows.append(row)

        if len(matched_rows) == 1:
            st.session_state.selected_line = matched_rows[0].get("Line Number", "")
            st.session_state.matched_row = matched_rows[0]
            st.session_state.candidate_rows = []
            st.session_state.step = 2
        elif len(matched_rows) > 1:
            # 候補が複数 → 必ず選択させる
            st.session_state.candidate_rows = matched_rows
            st.session_state.searched_number = search_val
            st.session_state.selected_line = None
            st.session_state.matched_row = None
            st.session_state.step = 15
        else:
            st.session_state.search_error = "Número da linha correspondente não encontrado."

    if st.session_state.search_error:
        st.warning(f"⚠️ {st.session_state.search_error}")
        st.session_state.search_error = ""

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
            if (inputs.length > 0) {{
                let targetInput = inputs[inputs.length - 1];
                targetInput.focus();
                targetInput.setAttribute('inputmode', 'numeric');
                targetInput.setAttribute('pattern', '[0-9]*');
            }}
        }}, 400);
        </script>
        <!-- timestamp: {time.time()} -->
        """,
        height=0
    )


# ==========================================
# Step 15: 候補が複数ある場合の選択画面（必須）
# ==========================================
elif st.session_state.step == 15:

    st.warning(
        f"⚠️ Existem {len(st.session_state.candidate_rows)} registros que começam com "
        f"**{st.session_state.searched_number}**. Selecione qual deseja usar."
    )

    for i, row in enumerate(st.session_state.candidate_rows):
        line_name = str(row.get("Line Number", "")).strip()
        kind = describe_row(row)
        mark = "  ✅ já registrado" if already_registered(line_name) else ""

        label = (
            f"{line_name}  |  {kind}  |  "
            f"Saco: {row.get('Sack Number', '-')}  |  "
            f"Var.: {row.get('Variety', '-')}  |  "
            f"Plantas: {row.get('Total no.of plant', '-')}{mark}"
        )

        if st.button(label, key=f"cand_{i}", use_container_width=True):
            st.session_state.selected_line = line_name
            st.session_state.matched_row = row
            st.session_state.candidate_rows = []
            st.session_state.step = 2
            st.rerun()

    st.divider()
    if st.button("↩ Voltar (buscar outro número)", key="cand_cancel", use_container_width=True):
        st.session_state.candidate_rows = []
        st.session_state.searched_number = ""
        st.session_state.form_counter += 1
        st.session_state.step = 1
        st.rerun()


# ==========================================
# Step 2: 重量入力＆送信画面
# ==========================================
elif st.session_state.step == 2:

    line_name = st.session_state.selected_line
    st.success(f"Linha selecionada: **{line_name}**")

    st.radio("Selecione a unidade", ["kg", "g"], index=0, horizontal=True, key="unit_input")

    st.text_input(
        "Insira o peso (Enter para confirmar e enviar)",
        placeholder="Ex: 1.5",
        key=f"weight_{st.session_state.form_counter}",
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
            st.session_state.candidate_rows = []
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
            if (inputs.length > 0) {{
                let targetInput = inputs[inputs.length - 1];
                targetInput.focus();
                targetInput.setAttribute('inputmode', 'decimal');
            }}
        }}, 400);
        </script>
        <!-- timestamp: {time.time()} -->
        """,
        height=0
    )


st.divider()

# --- 共通フッター：履歴表示 ---
if st.session_state.step in [1, 2, 15]:
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
