import streamlit as st
import pandas as pd
from datetime import datetime, timezone, timedelta
import re
import gspread
from google.oauth2.service_account import Credentials
import unicodedata
import streamlit.components.v1 as components
import time
import html as html_lib

# ==========================================
# 1. ページ基本設定
# ==========================================
st.set_page_config(
    page_title="Reg. Colheita",
    page_icon="icon.png",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# 異常値とみなす閾値（グラム）
WEIGHT_MAX_G = 30000   # 30kg超は確認を挟む
WEIGHT_MIN_G = 5       # 5g未満は確認を挟む


# ==========================================
# 2. デザイン（計量器コンセプト）
# ==========================================
st.html("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600;700&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
:root {
  --ink:        #12261C;
  --ink-soft:   #566B5E;
  --line:       #D9E2DB;
  --bg:         #F2F4EF;
  --card:       #FFFFFF;
  --green:      #1F7A4C;
  --green-dark: #16593A;
  --green-soft: #E4F1E9;
  --amber:      #A86A12;
  --amber-soft: #FBF1DC;
  --red:        #A6231C;
  --red-soft:   #F9E6E4;
  --panel:      #16221C;
  --digit:      #9FE8BE;
  --font-ui:    'IBM Plex Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  --font-mono:  'IBM Plex Mono', ui-monospace, SFMono-Regular, Menlo, monospace;
}
/* ---- Streamlit標準UIを隠す ---- */
header[data-testid="stHeader"] { display: none !important; }
div[data-testid="stToolbar"]   { display: none !important; }
div[data-testid="stDecoration"]{ display: none !important; }
footer                         { display: none !important; }
#MainMenu                      { display: none !important; }
/* ---- 全体 ---- */
.stApp {
  background: var(--bg) !important;
  overflow-x: hidden !important;
}
html, body, [class*="css"] { font-family: var(--font-ui) !important; }
div[data-testid="stAppViewContainer"] > .main .block-container,
div[data-testid="stMainBlockContainer"] {
  padding-top: 14px !important;
  padding-bottom: 40px !important;
  max-width: 560px !important;
}
/* ================= トップバー ================= */
.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: 14px;
  padding: 12px 14px;
  margin-bottom: 14px;
}
.topbar .who {
  min-width: 0;
}
.topbar .who .name {
  font-size: 14px;
  font-weight: 600;
  color: var(--ink);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.topbar .who .month {
  font-family: var(--font-mono);
  font-size: 11px;
  letter-spacing: .08em;
  text-transform: uppercase;
  color: var(--ink-soft);
  margin-top: 2px;
}
.counter {
  flex: 0 0 auto;
  text-align: right;
  padding-left: 12px;
  border-left: 1px solid var(--line);
}
.counter .num {
  font-family: var(--font-mono);
  font-size: 26px;
  font-weight: 700;
  line-height: 1;
  color: var(--green);
  font-variant-numeric: tabular-nums;
}
.counter .lbl {
  font-size: 10px;
  letter-spacing: .1em;
  text-transform: uppercase;
  color: var(--ink-soft);
  margin-top: 4px;
}
/* ================= セクション見出し ================= */
.eyebrow {
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 600;
  letter-spacing: .14em;
  text-transform: uppercase;
  color: var(--ink-soft);
  margin: 4px 0 8px;
}
/* ================= 計量パネル（署名要素） ================= */
.readout {
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: 16px;
  padding: 14px 16px;
  margin-bottom: 10px;
}
.readout .tag {
  font-family: var(--font-mono);
  font-size: 11px;
  letter-spacing: .14em;
  text-transform: uppercase;
  color: var(--ink-soft);
  margin-bottom: 6px;
}
.readout .line-code {
  font-family: var(--font-mono);
  font-size: 32px;
  font-weight: 700;
  color: var(--green-dark);
  letter-spacing: -.01em;
  line-height: 1.1;
  word-break: break-word;
}
.readout .sub {
  font-size: 12px;
  color: var(--ink-soft);
  margin-top: 6px;
}
/* 計量パネル内の重量入力欄を「表示窓」にする */
.st-key-weightpanel div[data-testid="stTextInput"] input {
  background: var(--panel) !important;
  color: var(--digit) !important;
  border: none !important;
  border-radius: 18px !important;
  font-family: var(--font-mono) !important;
  font-size: 40px !important;
  font-weight: 700 !important;
  text-align: right !important;
  letter-spacing: -.02em !important;
  padding: 18px 20px !important;
  height: auto !important;
  box-shadow: none !important;
  caret-color: var(--digit);
}
.st-key-weightpanel div[data-testid="stTextInput"] input::placeholder {
  color: #3C5347 !important;
  font-weight: 400 !important;
}
.st-key-weightpanel div[data-testid="stTextInput"] > div {
  background: var(--panel) !important;
  border: none !important;
  border-radius: 18px !important;
  box-shadow: none !important;
}
.st-key-weightpanel div[data-baseweb="input"],
.st-key-weightpanel div[data-baseweb="base-input"] {
  background: var(--panel) !important;
  border: none !important;
  border-radius: 18px !important;
  box-shadow: none !important;
}
.st-key-weightpanel div[data-testid="stTextInput"] label { display: none !important; }
/* ================= 検索入力（大きく） ================= */
.st-key-searchpanel div[data-testid="stTextInput"] input {
  background: var(--card) !important;
  color: var(--ink) !important;
  border: 2px solid var(--line) !important;
  border-radius: 14px !important;
  font-family: var(--font-mono) !important;
  font-size: 34px !important;
  font-weight: 700 !important;
  text-align: center !important;
  padding: 16px 14px !important;
  height: auto !important;
}
.st-key-searchpanel div[data-testid="stTextInput"] input:focus {
  border-color: var(--green) !important;
  box-shadow: 0 0 0 4px var(--green-soft) !important;
}
.st-key-searchpanel div[data-testid="stTextInput"] input::placeholder {
  color: #B9C6BE !important;
  font-weight: 400 !important;
}
.st-key-searchpanel div[data-testid="stTextInput"] label { display: none !important; }
/* ログイン画面の入力欄 */
.st-key-loginpanel div[data-testid="stTextInput"] input,
.st-key-loginpanel div[data-baseweb="select"] > div {
  background: var(--card) !important;
  border: 1.5px solid var(--line) !important;
  border-radius: 12px !important;
  font-size: 16px !important;
  padding: 12px 14px !important;
  color: var(--ink) !important;
}
.st-key-loginpanel div[data-testid="stTextInput"] input:focus {
  border-color: var(--green) !important;
  box-shadow: 0 0 0 4px var(--green-soft) !important;
}
.st-key-loginpanel label {
  font-size: 12px !important;
  font-weight: 600 !important;
  letter-spacing: .06em !important;
  text-transform: uppercase !important;
  color: var(--ink-soft) !important;
}
/* ================= 単位トグル（セグメント） ================= */
/* 単位トグル（自作ボタン式） */
.st-key-unitrow div[data-testid="stHorizontalBlock"] {
  gap: 6px !important;
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: 12px;
  padding: 5px;
  margin-top: 10px;
}
.st-key-unit_kg_off div[data-testid="stButton"] > button,
.st-key-unit_g_off div[data-testid="stButton"] > button {
  background: transparent !important;
  border: none !important;
  color: var(--ink-soft) !important;
  font-family: var(--font-mono) !important;
  font-size: 15px !important;
  font-weight: 600 !important;
  min-height: 44px !important;
  border-radius: 8px !important;
}
.st-key-unit_kg_on div[data-testid="stButton"] > button,
.st-key-unit_g_on div[data-testid="stButton"] > button {
  background: var(--ink) !important;
  border: none !important;
  color: #FFFFFF !important;
  font-family: var(--font-mono) !important;
  font-size: 15px !important;
  font-weight: 700 !important;
  min-height: 44px !important;
  border-radius: 8px !important;
}
/* ================= ボタン共通 ================= */
div[data-testid="stButton"] > button {
  border-radius: 12px !important;
  font-family: var(--font-ui) !important;
  font-size: 15px !important;
  font-weight: 600 !important;
  min-height: 54px !important;
  border: 1.5px solid var(--line) !important;
  background: var(--card) !important;
  color: var(--ink) !important;
  transition: transform .08s ease, background .15s ease;
}
div[data-testid="stButton"] > button:hover { border-color: var(--ink-soft) !important; }
div[data-testid="stButton"] > button:active { transform: scale(.985); }
div[data-testid="stButton"] > button:focus-visible {
  outline: 3px solid var(--green) !important;
  outline-offset: 2px !important;
}
/* 主要アクション（緑・塗り） */
.st-key-btn_confirm div[data-testid="stButton"] > button,
.st-key-btn_login div[data-testid="stButton"] > button,
.st-key-btn_force div[data-testid="stButton"] > button {
  background: var(--green) !important;
  border-color: var(--green) !important;
  color: #FFFFFF !important;
}
.st-key-btn_confirm div[data-testid="stButton"] > button:hover,
.st-key-btn_login div[data-testid="stButton"] > button:hover,
.st-key-btn_force div[data-testid="stButton"] > button:hover {
  background: var(--green-dark) !important;
  border-color: var(--green-dark) !important;
}
/* 取り消し（赤・枠） */
.st-key-btn_cancel div[data-testid="stButton"] > button,
.st-key-btn_fix div[data-testid="stButton"] > button {
  background: var(--red-soft) !important;
  border-color: var(--red) !important;
  color: var(--red) !important;
}
.st-key-btn_cancel div[data-testid="stButton"] > button:hover,
.st-key-btn_fix div[data-testid="stButton"] > button:hover {
  background: var(--red) !important;
  color: #FFFFFF !important;
}
/* 控えめなリンク風ボタン */
.st-key-btn_logout div[data-testid="stButton"] > button,
.st-key-btn_back div[data-testid="stButton"] > button {
  background: transparent !important;
  border: none !important;
  color: var(--ink-soft) !important;
  font-size: 13px !important;
  font-weight: 500 !important;
  min-height: 38px !important;
  text-decoration: underline;
  text-underline-offset: 3px;
}
/* ================= 候補カード（袋タグ） ================= */
.st-key-candzone div[data-testid="stButton"] > button {
  min-height: 84px !important;
  padding: 14px 16px !important;
  text-align: left !important;
  justify-content: flex-start !important;
  border: 1.5px solid var(--line) !important;
  background: var(--card) !important;
  white-space: pre-line !important;
  line-height: 1.45 !important;
}
.st-key-candzone div[data-testid="stButton"] > button:hover {
  border-color: var(--green) !important;
  background: var(--green-soft) !important;
}
.st-key-candzone div[data-testid="stButton"] > button p {
  text-align: left !important;
  font-family: var(--font-mono) !important;
  font-size: 13px !important;
  white-space: pre-line !important;
  margin: 0 !important;
}
/* ================= バナー ================= */
.banner {
  border-radius: 12px;
  padding: 12px 14px;
  font-size: 13.5px;
  line-height: 1.5;
  margin-bottom: 12px;
  border: 1px solid transparent;
}
.banner b { font-family: var(--font-mono); }
.banner.warn  { background: var(--amber-soft); border-color: #E8CE9A; color: var(--amber); }
.banner.error { background: var(--red-soft);   border-color: #E9BDB9; color: var(--red); }
.banner.info  { background: var(--green-soft); border-color: #BDDCC9; color: var(--green-dark); }
/* ================= 明細（メタ情報） ================= */
.meta {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1px;
  background: var(--line);
  border: 1px solid var(--line);
  border-radius: 12px;
  overflow: hidden;
  margin-top: 14px;
}
.meta .cell { background: var(--card); padding: 11px 13px; }
.meta .k {
  font-size: 10px;
  letter-spacing: .1em;
  text-transform: uppercase;
  color: var(--ink-soft);
}
.meta .v {
  font-family: var(--font-mono);
  font-size: 16px;
  font-weight: 600;
  color: var(--ink);
  margin-top: 3px;
  word-break: break-word;
}
/* ================= 履歴 ================= */
.log { border: 1px solid var(--line); border-radius: 12px; overflow: hidden; background: var(--card); }
.log .row {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 10px;
  padding: 10px 13px;
  border-bottom: 1px solid var(--line);
}
.log .row:last-child { border-bottom: none; }
.log .row .l {
  font-family: var(--font-mono);
  font-size: 13px;
  font-weight: 600;
  color: var(--ink);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.log .row .t { font-size: 11px; color: var(--ink-soft); margin-top: 2px; }
.log .row .w {
  font-family: var(--font-mono);
  font-size: 15px;
  font-weight: 700;
  color: var(--green);
  white-space: nowrap;
  font-variant-numeric: tabular-nums;
}
.empty {
  border: 1px dashed var(--line);
  border-radius: 12px;
  padding: 22px 14px;
  text-align: center;
  color: var(--ink-soft);
  font-size: 13px;
  background: var(--card);
}
/* ログイン画面のヘッダー */
.login-head { padding: 22px 0 18px; }
.login-head .mark {
  font-family: var(--font-mono);
  font-size: 11px;
  letter-spacing: .18em;
  text-transform: uppercase;
  color: var(--green);
  font-weight: 600;
}
.login-head h1 {
  font-size: 27px;
  font-weight: 700;
  color: var(--ink);
  margin: 8px 0 6px;
  line-height: 1.22;
  letter-spacing: -.02em;
}
.login-head p { font-size: 14px; color: var(--ink-soft); margin: 0; line-height: 1.55; }
/* 横並びの列はスマホでも維持する */
div[data-testid="stHorizontalBlock"] {
  display: grid !important;
  grid-template-columns: 1fr 1fr !important;
  gap: 10px !important;
  width: 100% !important;
}
div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
  width: 100% !important;
  min-width: 0 !important;
  max-width: 100% !important;
  flex: 1 1 0 !important;
}
div[data-testid="stHorizontalBlock"] div[data-testid="stButton"] > button p {
  white-space: normal !important;
  word-break: break-word !important;
}
hr, div[data-testid="stDivider"] { border-color: var(--line) !important; }
@media (prefers-reduced-motion: reduce) {
  * { transition: none !important; animation: none !important; }
}
</style>
""")


# ==========================================
# 3. データ接続
# ==========================================
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


# ==========================================
# 4. セッションステート
# ==========================================
_defaults = {
    "username": "",
    "target_month": "",
    "step": 0,
    "form_counter": 0,
    "selected_line": None,
    "matched_row": None,
    "candidate_rows": [],
    "searched_number": "",
    "search_error": "",
    "pending_weight": None,   # 異常値の確認待ち
}
for _k, _v in _defaults.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v


# ==========================================
# 5. ヘルパー
# ==========================================
def esc(v):
    return html_lib.escape(str(v))


def get_line_numbers(line_str):
    """'L586' -> [586] / 'L586 to L593' や 'L586-L593' -> [586, 593]"""
    nums = re.findall(r'L\s*(\d+)', str(line_str), flags=re.IGNORECASE)
    return [int(n) for n in nums]


def get_first_number(line_str):
    nums = get_line_numbers(line_str)
    return nums[0] if nums else None


def describe_row(row):
    nums = get_line_numbers(row.get("Line Number", ""))
    if len(nums) >= 2:
        return f"{nums[-1] - nums[0] + 1} linhas ({nums[0]}-{nums[-1]})"
    return "Linha única"


def write_log(weight, unit):
    """スプレッドシートに1行追記する"""
    weight_g = int(round(weight * 1000)) if unit == "kg" else int(round(weight))
    client = get_gspread_client()
    log_sheet = client.open_by_key(SPREADSHEET_KEY).worksheet("Harvest_Log")
    mozambique_tz = timezone(timedelta(hours=2))
    timestamp = datetime.now(mozambique_tz).strftime("%Y-%m-%d %H:%M:%S")
    log_sheet.append_row([
        timestamp,
        st.session_state.username,
        st.session_state.target_month,
        st.session_state.selected_line,
        f"{weight:.2f}",
        unit,
        weight_g
    ])


def reset_to_search():
    st.session_state.candidate_rows = []
    st.session_state.searched_number = ""
    st.session_state.pending_weight = None
    st.session_state.selected_line = None
    st.session_state.matched_row = None
    st.session_state.form_counter += 1
    st.session_state.step = 1


def process_submission():
    """重量入力の確定。異常値なら確認待ちにする。"""
    key = f"weight_{st.session_state.form_counter}"
    raw = st.session_state.get(key, "")
    if not raw:
        return
    try:
        weight = float(unicodedata.normalize('NFKC', str(raw)).strip())
    except ValueError:
        st.session_state.search_error = "Valor inválido. Use apenas números, ex: 1.5"
        return
    if weight <= 0:
        st.session_state.search_error = "O peso deve ser maior que zero."
        return

    unit = st.session_state.get("unit_input", "kg")
    weight_g = weight * 1000 if unit == "kg" else weight

    if weight_g > WEIGHT_MAX_G or weight_g < WEIGHT_MIN_G:
        st.session_state.pending_weight = (weight, unit)
        return

    write_log(weight, unit)
    st.toast(f"{st.session_state.selected_line} registrado")
    reset_to_search()


def focus_last_input(mode="numeric"):
    attr = ("targetInput.setAttribute('inputmode', 'decimal');" if mode == "decimal"
            else "targetInput.setAttribute('inputmode', 'numeric');"
                 "targetInput.setAttribute('pattern', '[0-9]*');")
    components.html(
        f"""
        <script>
        setTimeout(function() {{
            const inputs = window.parent.document.querySelectorAll('input[type="text"]');
            if (inputs.length > 0) {{
                let targetInput = inputs[inputs.length - 1];
                targetInput.focus();
                {attr}
            }}
        }}, 400);
        </script>
        <!-- {time.time()} -->
        """, height=0
    )


def pop_error():
    if st.session_state.search_error:
        st.html(
            f'<div class="banner error">{esc(st.session_state.search_error)}</div>'
        )
        st.session_state.search_error = ""


# ==========================================
# Step 0: ログイン
# ==========================================
if st.session_state.step == 0:
    st.html("""
    <div class="login-head">
      <div class="mark">Registro de colheita</div>
      <h1>Pesagem por linha</h1>
      <p>Identifique-se e escolha o mês antes de começar.</p>
    </div>
    """)

    with st.container(key="loginpanel"):
        pop_error()
        month_options = ["Selecione o mês", "May-26", "Jun-26", "Jul-26", "Aug-26",
                         "Sep-26", "Oct-26", "Nov-26", "Dec-26", "Jan-27", "Feb-27",
                         "Mar-27", "Apr-27"]
        user_input = st.text_input("Nome de usuário", placeholder="Seu nome")
        month_input = st.selectbox("Mês de registro", month_options, index=0)

        with st.container(key="btn_login"):
            if st.button("Começar", use_container_width=True):
                if user_input and month_input != "Selecione o mês":
                    st.session_state.username = user_input
                    st.session_state.target_month = month_input
                    st.session_state.step = 1
                    st.rerun()
                else:
                    st.session_state.search_error = "Preencha o nome e selecione o mês."
                    st.rerun()

    focus_last_input("numeric")
    st.stop()


# ==========================================
# データ読み込み
# ==========================================
try:
    df_master = load_master_data()
    df_log = load_log_data()
except Exception as e:
    st.html(
        f'<div class="banner error">Não foi possível carregar os dados. {esc(e)}</div>'
    )
    st.stop()


sack_count = 0
df_month = pd.DataFrame()
if not df_log.empty and len(df_log.columns) >= 3:
    _mcol = df_log.columns[2]
    df_month = df_log[df_log[_mcol] == st.session_state.target_month]
    sack_count = len(df_month)


def already_registered(line_name):
    if df_month.empty or len(df_log.columns) < 4:
        return False
    lcol = df_log.columns[3]
    return not df_month[
        df_month[lcol].astype(str).str.strip() == str(line_name).strip()
    ].empty


# ---- トップバー ----
st.html(f"""
<div class="topbar">
  <div class="who">
    <div class="name">{esc(st.session_state.username)}</div>
    <div class="month">{esc(st.session_state.target_month)}</div>
  </div>
  <div class="counter">
    <div class="num">{sack_count}</div>
    <div class="lbl">sacos</div>
  </div>
</div>
""")


# ==========================================
# Step 1: ライン番号検索
# ==========================================
if st.session_state.step == 1:

    def process_search():
        raw = st.session_state.get(f"search_{st.session_state.form_counter}", "")
        val = unicodedata.normalize('NFKC', str(raw)).strip()
        st.session_state.search_error = ""
        if not val:
            return
        if not val.isdigit():
            st.session_state.search_error = "Digite apenas números."
            return

        target = int(val)
        matched = [row for _, row in df_master.iterrows()
                   if get_first_number(row.get("Line Number", "")) == target]

        if len(matched) == 1:
            st.session_state.selected_line = matched[0].get("Line Number", "")
            st.session_state.matched_row = matched[0]
            st.session_state.candidate_rows = []
            st.session_state.step = 2
        elif len(matched) > 1:
            st.session_state.candidate_rows = matched
            st.session_state.searched_number = val
            st.session_state.selected_line = None
            st.session_state.matched_row = None
            st.session_state.step = 15
        else:
            st.session_state.search_error = f"Linha {val} não existe no cadastro."

    pop_error()
    st.html('<div class="eyebrow">Número inicial da linha</div>')

    with st.container(key="searchpanel"):
        st.text_input(
            "Número da linha",
            placeholder="1",
            key=f"search_{st.session_state.form_counter}",
            on_change=process_search,
            label_visibility="collapsed"
        )

    st.html(
        '<div class="banner info">Digite o número e toque em Enter para avançar.</div>'
    )

    with st.container(key="btn_logout"):
        if st.button("Trocar de usuário", use_container_width=True):
            st.session_state.username = ""
            st.session_state.target_month = ""
            st.session_state.candidate_rows = []
            st.session_state.step = 0
            st.rerun()

    focus_last_input("numeric")


# ==========================================
# Step 15: 候補が複数あるとき
# ==========================================
elif st.session_state.step == 15:

    st.html(
        f'<div class="banner warn">O número <b>{esc(st.session_state.searched_number)}</b> '
        f'aparece em {len(st.session_state.candidate_rows)} registros. '
        f'Escolha em qual deles você vai lançar o peso.</div>'
    )

    with st.container(key="candzone"):
        for i, row in enumerate(st.session_state.candidate_rows):
            line_name = str(row.get("Line Number", "")).strip()
            done = "  •  JÁ REGISTRADO" if already_registered(line_name) else ""
            label = (
                f"{line_name}{done}\n"
                f"{describe_row(row)}  ·  Saco {row.get('Sack Number', '-')}\n"
                f"{row.get('Variety', '-')}  ·  {row.get('Total no.of plant', '-')} plantas"
            )
            if st.button(label, key=f"cand_{i}", use_container_width=True):
                st.session_state.selected_line = line_name
                st.session_state.matched_row = row
                st.session_state.candidate_rows = []
                st.session_state.step = 2
                st.rerun()

    with st.container(key="btn_back"):
        if st.button("Buscar outro número", use_container_width=True):
            reset_to_search()
            st.rerun()


# ==========================================
# Step 2: 重量入力
# ==========================================
elif st.session_state.step == 2:

    line_name = st.session_state.selected_line
    row_data = st.session_state.matched_row

    # --- 異常値の確認待ち ---
    if st.session_state.pending_weight is not None:
        w, u = st.session_state.pending_weight
        st.html(
            f'<div class="banner warn">O valor <b>{w:.2f} {u}</b> está fora da faixa '
            f'esperada. Confirme se está correto antes de registrar.</div>'
        )
        st.html(f"""
        <div class="readout">
          <div class="tag">Confirmar registro</div>
          <div class="line-code">{esc(line_name)}</div>
          <div class="sub">{w:.2f} {u}</div>
        </div>
        """)

        c1, c2 = st.columns(2)
        with c1:
            with st.container(key="btn_force"):
                if st.button("Registrar assim", use_container_width=True):
                    write_log(w, u)
                    st.toast(f"{line_name} registrado")
                    reset_to_search()
                    st.rerun()
        with c2:
            with st.container(key="btn_fix"):
                if st.button("Corrigir", use_container_width=True):
                    st.session_state.pending_weight = None
                    st.session_state.form_counter += 1
                    st.rerun()
        st.stop()

    pop_error()

    if already_registered(line_name):
        st.html(
            '<div class="banner warn">Esta linha já tem um registro neste mês. '
            'Um novo lançamento será somado ao histórico.</div>'
        )

    # --- 計量パネル ---
    with st.container(key="weightpanel"):
        st.html(f"""
        <div class="readout">
          <div class="tag">Pesando</div>
          <div class="line-code">{esc(line_name)}</div>
          <div class="sub">{esc(describe_row(row_data))} &nbsp;·&nbsp; Saco {esc(row_data.get('Sack Number', '-'))}</div>
        </div>
        """)

        st.text_input(
            "Peso",
            placeholder="0.00",
            key=f"weight_{st.session_state.form_counter}",
            on_change=process_submission,
            label_visibility="collapsed"
        )

    _unit = st.session_state.get("unit_input", "kg")
    with st.container(key="unitrow"):
        u1, u2 = st.columns(2)
        with u1:
            with st.container(key=f"unit_kg_{'on' if _unit == 'kg' else 'off'}"):
                if st.button("kg", use_container_width=True, key="pick_kg"):
                    st.session_state.unit_input = "kg"
                    st.rerun()
        with u2:
            with st.container(key=f"unit_g_{'on' if _unit == 'g' else 'off'}"):
                if st.button("g", use_container_width=True, key="pick_g"):
                    st.session_state.unit_input = "g"
                    st.rerun()

    c1, c2 = st.columns(2)
    with c1:
        with st.container(key="btn_confirm"):
            if st.button("Registrar", use_container_width=True):
                process_submission()
                st.rerun()
    with c2:
        with st.container(key="btn_cancel"):
            if st.button("Cancelar", use_container_width=True):
                reset_to_search()
                st.rerun()

    # --- 明細 ---
    st.html(f"""
    <div class="meta">
      <div class="cell"><div class="k">ID da mãe</div><div class="v">{esc(row_data.get('Mother Id', '-'))}</div></div>
      <div class="cell"><div class="k">Variedade</div><div class="v">{esc(row_data.get('Variety', '-'))}</div></div>
      <div class="cell"><div class="k">Saco</div><div class="v">{esc(row_data.get('Sack Number', '-'))}</div></div>
      <div class="cell"><div class="k">Plantas</div><div class="v">{esc(row_data.get('Total no.of plant', '-'))}</div></div>
    </div>
    """)

    focus_last_input("decimal")


# ==========================================
# 履歴
# ==========================================
if st.session_state.step in (1, 2, 15):
    st.html('<div class="eyebrow" style="margin-top:26px">Últimos registros</div>')

    if not df_month.empty and len(df_log.columns) >= 6:
        c_time, c_line, c_val, c_unit = (df_log.columns[0], df_log.columns[3],
                                         df_log.columns[4], df_log.columns[5])
        rows = []
        for _, r in df_month.tail(8)[::-1].iterrows():
            stamp = str(r.get(c_time, ""))[5:16]   # MM-DD HH:MM
            rows.append(
                '<div class="row">'
                f'<div><div class="l">{esc(r.get(c_line, "-"))}</div>'
                f'<div class="t">{esc(stamp)} · {esc(r.get(df_log.columns[1], ""))}</div></div>'
                f'<div class="w">{esc(r.get(c_val, "-"))} {esc(r.get(c_unit, ""))}</div>'
                '</div>'
            )
        st.html(f'<div class="log">{"".join(rows)}</div>')
    else:
        st.html(
            f'<div class="empty">Nenhum registro em {esc(st.session_state.target_month)} ainda.</div>'
        )
