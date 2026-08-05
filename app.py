import streamlit as st
import pandas as pd
from datetime import datetime, timezone, timedelta
import re
import threading
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
    page_title="JatLog",
    page_icon="icon.png",
    layout="centered",
    initial_sidebar_state="collapsed"
)

APP_VERSION = "2.0"

# 異常値とみなす閾値（グラム）
WEIGHT_MAX_G = 30000   # 30kg超は確認を挟む
WEIGHT_MIN_G = 5       # 5g未満は確認を挟む

TZ_MZ = timezone(timedelta(hours=2))  # モザンビーク時間

# 監査ログ・バックアップのタブ名（各スプレッドシート内に自動作成される）
AUDIT_TAB = "Audit_Log"
BACKUP_TAB = "Backup_Snapshot"
AUDIT_HEADERS = ("Timestamp", "Action", "By User", "Role", "Record Owner",
                 "Month", "Line/Block", "Old Value", "Old Unit", "New Value", "New Unit")

GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# 管理者パスワード。Streamlit Cloud の Secrets に admin_password を
# 設定すればそちらが優先される（未設定時は下のデフォルト）。
ADMIN_PASSWORD = str(st.secrets.get("admin_password", "JatRD2026"))


# ==========================================
# 2. デザイン（計量器コンセプト v2）
# ==========================================
st.html("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600;700&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
:root {
  --ink:        #12261C;
  --ink-soft:   #5B6F63;
  --line:       #DCE4DC;
  --bg:         #EFF3EC;
  --card:       #FFFFFF;
  --green:      #1F7A4C;
  --green-dark: #16593A;
  --green-soft: #E4F1E9;
  --amber:      #8C560D;
  --amber-soft: #FBF1DC;
  --red:        #A6231C;
  --red-soft:   #F9E6E4;
  --panel:      #16221C;
  --digit:      #9FE8BE;
  --shadow:     0 1px 2px rgba(18,38,28,.05), 0 6px 20px rgba(18,38,28,.05);
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
  background: linear-gradient(180deg, #E9EFE6 0%, var(--bg) 260px) fixed !important;
  overflow-x: hidden !important;
}
html, body, [class*="css"] { font-family: var(--font-ui) !important; }
div[data-testid="stAppViewContainer"] > .main .block-container,
div[data-testid="stMainBlockContainer"] {
  padding-top: 14px !important;
  padding-bottom: 40px !important;
  max-width: 560px !important;
}
@keyframes rise {
  from { opacity: 0; transform: translateY(6px); }
  to   { opacity: 1; transform: none; }
}
div[data-testid="stMainBlockContainer"] { animation: rise .18s ease-out; }
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
  margin-bottom: 12px;
  box-shadow: var(--shadow);
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
  margin-top: 3px;
}
.badge-adm {
  display: inline-block;
  font-family: var(--font-mono);
  font-size: 9px;
  font-weight: 700;
  letter-spacing: .12em;
  background: var(--panel);
  color: var(--digit);
  border-radius: 5px;
  padding: 2px 6px;
  margin-left: 6px;
  vertical-align: 2px;
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
  box-shadow: var(--shadow);
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
/* 「Press Enter to apply」の案内文が大きな入力欄と被らないよう、下・左に離す */
.st-key-searchpanel div[data-testid="InputInstructions"],
.st-key-weightpanel div[data-testid="InputInstructions"],
.st-key-loginpanel div[data-testid="InputInstructions"] {
  position: static !important;
  display: flex !important;
  justify-content: flex-start !important;
  text-align: left !important;
  margin-top: 6px !important;
  padding-left: 2px !important;
}
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
/* 管理者ログインの折りたたみ */
div[data-testid="stExpander"] {
  border: 1px solid var(--line) !important;
  border-radius: 12px !important;
  background: var(--card) !important;
  overflow: hidden;
}
div[data-testid="stExpander"] summary {
  font-size: 13px !important;
  color: var(--ink-soft) !important;
}
/* ================= 単位トグル（セグメント） ================= */
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
/* ================= 拠点切り替え ================= */
.st-key-siterow div[data-testid="stHorizontalBlock"] {
  gap: 6px !important;
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: 12px;
  padding: 5px;
  margin-bottom: 14px;
}
.st-key-site_lines_off div[data-testid="stButton"] > button,
.st-key-site_blocks_off div[data-testid="stButton"] > button {
  background: transparent !important;
  border: none !important;
  color: var(--ink-soft) !important;
  font-family: var(--font-mono) !important;
  font-size: 13px !important;
  font-weight: 600 !important;
  min-height: 40px !important;
  border-radius: 8px !important;
}
.st-key-site_lines_on div[data-testid="stButton"] > button,
.st-key-site_blocks_on div[data-testid="stButton"] > button {
  background: var(--ink) !important;
  border: none !important;
  color: #FFFFFF !important;
  font-family: var(--font-mono) !important;
  font-size: 13px !important;
  font-weight: 700 !important;
  min-height: 40px !important;
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
/* 管理者の月切替（コンパクト） */
.st-key-adminmonthrow label {
  font-size: 11px !important;
  font-weight: 600 !important;
  letter-spacing: .1em !important;
  text-transform: uppercase !important;
  color: var(--ink-soft) !important;
}
.st-key-adminmonthrow input {
  font-family: var(--font-mono) !important;
  font-weight: 600 !important;
}
/* 控えめなリンク風ボタン */
.st-key-btn_logout div[data-testid="stButton"] > button,
.st-key-btn_back div[data-testid="stButton"] > button,
.st-key-btn_month div[data-testid="stButton"] > button,
.st-key-btn_exit_admin div[data-testid="stButton"] > button {
  background: transparent !important;
  border: none !important;
  color: var(--ink-soft) !important;
  font-size: 13px !important;
  font-weight: 500 !important;
  min-height: 38px !important;
  text-decoration: underline;
  text-underline-offset: 3px;
}
/* 削除リンク（控えめ・赤） */
.st-key-btn_delete div[data-testid="stButton"] > button {
  background: transparent !important;
  border: none !important;
  color: var(--red) !important;
  font-size: 13px !important;
  font-weight: 500 !important;
  min-height: 38px !important;
  text-decoration: underline;
  text-underline-offset: 3px;
}
/* 削除の確定（赤・塗り） */
.st-key-btn_danger div[data-testid="stButton"] > button {
  background: var(--red) !important;
  border-color: var(--red) !important;
  color: #FFFFFF !important;
}
.st-key-btn_danger div[data-testid="stButton"] > button:hover {
  background: #7C1912 !important;
  border-color: #7C1912 !important;
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
.st-key-candzone div[data-testid="stButton"] > button > div {
  justify-content: flex-start !important;
  width: 100% !important;
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
.banner.ok {
  background: var(--green-soft);
  border-color: #9ED0B4;
  color: var(--green-dark);
  font-weight: 600;
}
.banner.ok .tick {
  display: inline-block;
  font-family: var(--font-mono);
  font-weight: 700;
  margin-right: 6px;
}
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
/* ================= 履歴（タップで編集） ================= */
.st-key-histzone div[data-testid="stButton"] > button {
  min-height: 58px !important;
  padding: 10px 14px !important;
  margin-bottom: 6px !important;
  text-align: left !important;
  justify-content: flex-start !important;
  border: 1.5px solid var(--line) !important;
  background: var(--card) !important;
  white-space: pre-line !important;
  line-height: 1.4 !important;
}
.st-key-histzone div[data-testid="stButton"] > button:hover {
  border-color: var(--green) !important;
  background: var(--green-soft) !important;
}
.st-key-histzone div[data-testid="stButton"] > button p {
  text-align: left !important;
  font-family: var(--font-mono) !important;
  font-size: 13px !important;
  white-space: pre-line !important;
  margin: 0 !important;
}
.st-key-histzone div[data-testid="stButton"] > button > div {
  justify-content: flex-start !important;
  width: 100% !important;
}
/* 履歴：他人の記録（編集不可の静的カード） */
.histrow {
  border: 1.5px solid var(--line);
  border-radius: 12px;
  background: #FAFBF9;
  padding: 10px 14px;
  margin-bottom: 6px;
  font-family: var(--font-mono);
  font-size: 13px;
  line-height: 1.4;
  color: var(--ink);
}
.histrow .hs {
  color: var(--ink-soft);
  font-size: 12px;
  margin-top: 2px;
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
.appfoot {
  margin-top: 26px;
  text-align: center;
  font-family: var(--font-mono);
  font-size: 10px;
  letter-spacing: .1em;
  text-transform: uppercase;
  color: #9AA99F;
}
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
/* ================= 処理中インジケータ（通信待ちのフィードバック） ================= */
div[data-testid="stSpinner"] {
  color: var(--ink-soft) !important;
  font-family: var(--font-ui) !important;
  font-size: 13.5px !important;
}
@media (prefers-reduced-motion: reduce) {
  * { transition: none !important; animation: none !important; }
}
</style>
""")


# ==========================================
# 3. 通信状態ウォッチャー（オフライン警告バー）
# ==========================================
def ensure_offline_watch():
    """親ページに一度だけスクリプトを注入し、電波が切れたら赤い帯を表示する。"""
    components.html("""
    <script>
    (function() {
      const pd = window.parent.document;
      if (pd.getElementById('jatrd-offline-watch')) return;
      const s = pd.createElement('script');
      s.id = 'jatrd-offline-watch';
      s.textContent = "(function(){" +
        "var b = document.createElement('div');" +
        "b.id = 'jatrd-offline-banner';" +
        "b.textContent = 'SEM CONEX\\u00c3O \\u2014 aguarde o sinal voltar antes de registrar';" +
        "b.style.cssText = 'display:none;position:fixed;top:0;left:0;right:0;z-index:999999;" +
        "background:#A6231C;color:#fff;font:600 13px/1.4 sans-serif;text-align:center;" +
        "padding:9px 12px;letter-spacing:.04em;';" +
        "document.body.appendChild(b);" +
        "function u(){ b.style.display = navigator.onLine ? 'none' : 'block'; }" +
        "window.addEventListener('online', u);" +
        "window.addEventListener('offline', u);" +
        "u();" +
        "})();";
      pd.body.appendChild(s);
    })();
    </script>
    """, height=0)


ensure_offline_watch()


# ==========================================
# 4. データ接続
# ==========================================
@st.cache_resource
def get_gspread_client():
    credentials = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=GOOGLE_SCOPES
    )
    return gspread.authorize(credentials)


@st.cache_resource(show_spinner=False)
def get_spreadsheet(spreadsheet_key):
    return get_gspread_client().open_by_key(spreadsheet_key)


@st.cache_resource(show_spinner=False)
def get_or_create_ws(spreadsheet_key, tab_name, headers):
    """ワークシートを取得。無ければヘッダー付きで自動作成する。
    （タブ名の食い違いによる WorksheetNotFound クラッシュを恒久的に防ぐ）"""
    ss = get_spreadsheet(spreadsheet_key)
    try:
        return ss.worksheet(tab_name)
    except gspread.exceptions.WorksheetNotFound:
        try:
            ws = ss.add_worksheet(title=tab_name, rows=2000, cols=max(12, len(headers)))
            ws.append_row(list(headers))
            return ws
        except gspread.exceptions.APIError:
            # 別の端末が同時に作成した場合など
            return ss.worksheet(tab_name)


class StaleRowError(Exception):
    """編集・削除しようとした行が、シート上で既に変わっていた（他端末の操作など）"""
    pass


def with_retries(fn, attempts=3, wait=1.2):
    """一時的な通信エラーに対して再試行する。恒久エラーはそのまま上げる。"""
    for i in range(attempts):
        try:
            return fn()
        except StaleRowError:
            raise
        except Exception:
            if i == attempts - 1:
                raise
            # キャッシュ済みハンドルが腐っている可能性があるので作り直す
            get_or_create_ws.clear()
            get_spreadsheet.clear()
            time.sleep(wait)


# 圃場ごとの設定（ログイン前後の切り替えボタンで選ぶ）
SITES = {
    "lines": {
        "label": "Linhas",
        "spreadsheet_key": "1ulQjYCYlhZjxGMO3iTWGPmxM7U-O-NkCs2OOm6mY1Wk",
        "field_col": "Line Number",
        "prefix": "L",
        "unit_pl": "linhas",
        "single_label": "Linha única",
        "search_label": "Número inicial da linha",
        "search_input_label": "Número da linha",
        "not_found": "Linha {val} não existe no cadastro.",
        "already_registered_msg": "Esta linha já tem um registro neste mês. Um novo lançamento será somado ao histórico.",
        "app_title": "Pesagem por linha",
        "log_tab": "Harvest_Log",
    },
    "blocks": {
        "label": "Blocos",
        "spreadsheet_key": "1lm78EHRxKQRevTTN6NqBTMY4H8-qJuPRPpjEUoy0ses",
        "field_col": "Block",
        "prefix": "",
        "unit_pl": "blocos",
        "single_label": "Bloco único",
        "search_label": "Número inicial do bloco",
        "search_input_label": "Número do bloco",
        "not_found": "Bloco {val} não existe no cadastro.",
        "already_registered_msg": "Este bloco já tem um registro neste mês. Um novo lançamento será somado ao histórico.",
        "app_title": "Pesagem por bloco",
        "log_tab": "Harvest_Log",
    },
}


def current_site():
    return SITES[st.session_state.get("site", "lines")]


def log_headers(site):
    return ("Timestamp", "Username", "Month", site["field_col"], "Weight", "Unit", "Weight_g")


def get_log_ws(site):
    return get_or_create_ws(site["spreadsheet_key"], site["log_tab"], log_headers(site))


@st.cache_data(ttl=600, show_spinner=False)
def load_master_data(spreadsheet_key):
    client = get_gspread_client()
    sheet = client.open_by_key(spreadsheet_key).worksheet("Master")
    data = sheet.get_all_values()
    if len(data) > 0:
        df = pd.DataFrame(data[1:], columns=data[0])
        df.columns = df.columns.astype(str).str.strip()
        return df
    return pd.DataFrame()


@st.cache_data(ttl=60, show_spinner=False)
def load_log_data(spreadsheet_key, worksheet_name):
    client = get_gspread_client()
    try:
        sheet = client.open_by_key(spreadsheet_key).worksheet(worksheet_name)
    except gspread.exceptions.WorksheetNotFound:
        return pd.DataFrame()
    data = sheet.get_all_values()
    if len(data) > 0:
        df = pd.DataFrame(data[1:], columns=data[0])
        df.columns = df.columns.astype(str).str.strip()
        return df
    return pd.DataFrame()


# ==========================================
# 5. セッションステート
# ==========================================
_defaults = {
    "site": "lines",
    "username": "",
    "role": "worker",         # worker / admin
    "target_month": "",
    "step": 0,
    "form_counter": 0,
    "selected_line": None,
    "matched_row": None,
    "candidate_rows": [],
    "searched_number": "",
    "search_error": "",
    "pending_weight": None,   # 異常値の確認待ち
    "edit_target": None,      # 履歴編集中のレコード
    "return_step": None,      # 編集後に戻るステップ
    "confirm_delete": False,  # 削除確認待ち
    "last_saved": None,       # 直近の保存成功（明示フィードバック用）
}
for _k, _v in _defaults.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v


# ==========================================
# 6. ヘルパー
# ==========================================
def esc(v):
    return html_lib.escape(str(v))


def getv(row, *names, default="-"):
    """列名の表記ゆれ（Mother Id / Mother ID など）を吸収して値を取る"""
    for n in names:
        try:
            v = row.get(n)
        except AttributeError:
            v = None
        if v is not None and str(v).strip() != "":
            return v
    return default


def get_line_numbers(line_str, prefix="L"):
    """'L586' -> [586] / 'L586 to L593' や 'L586-L593' -> [586, 593]
    prefixが空文字の場合は接頭辞なしの素の数字にマッチする（ブロック番号など）"""
    pattern = re.escape(prefix) + r'\s*(\d+)' if prefix else r'(\d+)'
    nums = re.findall(pattern, str(line_str), flags=re.IGNORECASE)
    return [int(n) for n in nums]


def get_first_number(line_str, prefix="L"):
    nums = get_line_numbers(line_str, prefix)
    return nums[0] if nums else None


def describe_row(row):
    site = current_site()
    nums = get_line_numbers(row.get(site["field_col"], ""), site["prefix"])
    if len(nums) >= 2:
        return f"{nums[-1] - nums[0] + 1} {site['unit_pl']} ({nums[0]}-{nums[-1]})"
    return site["single_label"]


MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def now_stamp():
    return datetime.now(TZ_MZ).strftime("%Y-%m-%d %H:%M:%S")


def can_modify(record_owner):
    """自分の記録は本人が、それ以外は管理者だけが編集・削除できる"""
    if st.session_state.role == "admin":
        return True
    return str(record_owner).strip().casefold() == str(st.session_state.username).strip().casefold()


# ---- 監査ログ（誰が・いつ・何を・どう変えたか。失敗しても本処理は止めない） ----
def write_audit(action, owner, line, month, old=("", ""), new=("", "")):
    try:
        site = current_site()
        ws = get_or_create_ws(site["spreadsheet_key"], AUDIT_TAB, AUDIT_HEADERS)
        ws.append_row([
            now_stamp(), action,
            st.session_state.username, st.session_state.role,
            owner, month, line,
            old[0], old[1], new[0], new[1],
        ])
    except Exception:
        pass


# ---- 日次自動バックアップ（Harvest_Log を Backup_Snapshot に丸ごと複製） ----
def _backup_worker(sa_info, spreadsheet_key, log_tab, today):
    try:
        creds = Credentials.from_service_account_info(sa_info, scopes=GOOGLE_SCOPES)
        gc = gspread.authorize(creds)
        ss = gc.open_by_key(spreadsheet_key)
        try:
            bws = ss.worksheet(BACKUP_TAB)
        except gspread.exceptions.WorksheetNotFound:
            bws = ss.add_worksheet(title=BACKUP_TAB, rows=2000, cols=12)
        marker = bws.acell("A1").value or ""
        if today in str(marker):
            return  # 今日の分は取得済み
        data = ss.worksheet(log_tab).get_all_values()
        bws.clear()
        bws.update([[f"AUTO BACKUP de {log_tab} — {today} — não editar"]], "A1")
        if data:
            bws.update(data, "A2")
    except Exception:
        pass  # バックアップ失敗は本処理に影響させない


def kick_daily_backup():
    """保存成功後に呼ぶ。セッション×拠点ごとに1回だけ、別スレッドで実行。"""
    site = current_site()
    guard = f"backup_kicked_{site['spreadsheet_key']}"
    if st.session_state.get(guard):
        return
    st.session_state[guard] = True
    try:
        sa_info = dict(st.secrets["gcp_service_account"])
    except Exception:
        return
    today = datetime.now(TZ_MZ).strftime("%Y-%m-%d")
    threading.Thread(
        target=_backup_worker,
        args=(sa_info, site["spreadsheet_key"], site["log_tab"], today),
        daemon=True,
    ).start()


# ---- 書き込み・修正・削除 ----
def write_log(weight, unit):
    """スプレッドシートに1行追記する（通信エラー時は自動リトライ）"""
    weight_g = int(round(weight * 1000)) if unit == "kg" else int(round(weight))
    site = current_site()
    ts = now_stamp()
    row = [
        ts,
        st.session_state.username,
        st.session_state.target_month,
        st.session_state.selected_line,
        f"{weight:.2f}",
        unit,
        weight_g,
    ]
    with_retries(lambda: get_log_ws(site).append_row(row))
    write_audit("CREATE", st.session_state.username, st.session_state.selected_line,
                st.session_state.target_month, new=(f"{weight:.2f}", unit))
    load_log_data.clear()
    st.session_state.last_saved = {
        "line": st.session_state.selected_line,
        "val": f"{weight:.2f}",
        "unit": unit,
        "time": ts[11:16],
    }
    kick_daily_backup()


def _verify_row(ws, target):
    """編集・削除の対象行が、キャッシュ時点から変わっていないか確認する"""
    vals = ws.row_values(target["row"])
    if (len(vals) < 4
            or str(vals[0]).strip() != str(target.get("ts_full", "")).strip()
            or str(vals[3]).strip() != str(target["line"]).strip()):
        raise StaleRowError()


def update_log_row(target, weight, unit):
    """既存の記録（履歴）を修正する。修正前に行の一致を検証する。"""
    weight_g = int(round(weight * 1000)) if unit == "kg" else int(round(weight))
    site = current_site()

    def _do():
        ws = get_log_ws(site)
        _verify_row(ws, target)
        ws.update([[f"{weight:.2f}", unit, weight_g]], f"E{target['row']}:G{target['row']}")

    with_retries(_do, attempts=2)
    write_audit("EDIT", target.get("author", ""), target["line"], target.get("month", ""),
                old=(target["val"], target["unit"]), new=(f"{weight:.2f}", unit))
    load_log_data.clear()


def delete_log_row(target):
    """履歴の記録を完全に取り消す（該当行を削除）。削除前に行の一致を検証する。"""
    site = current_site()

    def _do():
        ws = get_log_ws(site)
        _verify_row(ws, target)
        ws.delete_rows(target["row"])

    with_retries(_do, attempts=2)
    write_audit("DELETE", target.get("author", ""), target["line"], target.get("month", ""),
                old=(target["val"], target["unit"]))
    load_log_data.clear()


SAVE_FAIL_MSG = ("Falha de conexão — o registro NÃO foi salvo. "
                 "Verifique o sinal e toque em Registrar novamente.")
STALE_MSG = ("Este registro mudou ou foi excluído em outro aparelho. "
             "A lista foi atualizada — confira antes de tentar de novo.")
NO_PERMISSION_MSG = "Somente o autor do registro ou o administrador pode alterá-lo."


def process_edit_save():
    """履歴編集フォームの保存処理"""
    target = st.session_state.edit_target
    key = f"editweight_{st.session_state.form_counter}"
    raw = st.session_state.get(key, "")
    if not raw:
        st.session_state.search_error = "Informe o novo peso."
        return
    try:
        weight = float(unicodedata.normalize('NFKC', str(raw)).strip())
    except ValueError:
        st.session_state.search_error = "Valor inválido. Use apenas números, ex: 1.5"
        return
    if weight <= 0:
        st.session_state.search_error = "O peso deve ser maior que zero."
        return

    if not can_modify(target.get("author", "")):
        st.session_state.search_error = NO_PERMISSION_MSG
        return

    unit = st.session_state.get("unit_edit", target["unit"])
    try:
        with st.spinner("Salvando…"):
            update_log_row(target, weight, unit)
    except StaleRowError:
        load_log_data.clear()
        st.session_state.search_error = STALE_MSG
        st.session_state.edit_target = None
        st.session_state.step = st.session_state.return_step or 1
        return
    except Exception:
        st.session_state.search_error = SAVE_FAIL_MSG
        return
    st.toast(f"{target['line']} atualizado")
    st.session_state.edit_target = None
    st.session_state.step = st.session_state.return_step or 1


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

    try:
        with st.spinner("Registrando…"):
            write_log(weight, unit)
    except Exception:
        # 入力値は消さない（form_counterを進めない）ので、そのまま再送できる
        st.session_state.search_error = SAVE_FAIL_MSG
        return
    st.toast(f"{st.session_state.selected_line} registrado")
    reset_to_search()


def focus_last_input(mode="numeric"):
    if mode == "decimal":
        attr = "targetInput.setAttribute('inputmode', 'decimal');"
    elif mode == "text":
        attr = ""
    else:
        attr = ("targetInput.setAttribute('inputmode', 'numeric');"
                 "targetInput.setAttribute('pattern', '[0-9]*');")
    components.html(
        f"""
        <script>
        setTimeout(function() {{
            const inputs = window.parent.document.querySelectorAll('input[type="text"]:not([role="combobox"])');
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


def _switch_site(new_site):
    if st.session_state.site == new_site:
        return
    st.session_state.site = new_site
    if st.session_state.step != 0:
        # ログイン情報（名前・月）は保持したまま、検索状態だけリセット
        st.session_state.last_saved = None
        st.session_state.edit_target = None
        st.session_state.confirm_delete = False
        reset_to_search()


def render_site_toggle():
    with st.container(key="siterow"):
        sa, sb = st.columns(2)
        with sa:
            with st.container(key=f"site_lines_{'on' if st.session_state.site == 'lines' else 'off'}"):
                if st.button(SITES["lines"]["label"], use_container_width=True, key="pick_site_lines"):
                    _switch_site("lines")
                    st.rerun()
        with sb:
            with st.container(key=f"site_blocks_{'on' if st.session_state.site == 'blocks' else 'off'}"):
                if st.button(SITES["blocks"]["label"], use_container_width=True, key="pick_site_blocks"):
                    _switch_site("blocks")
                    st.rerun()


# ==========================================
# Step 0: ログイン（名前だけ。月・年は次の画面で選ぶ）
# ==========================================
if st.session_state.step == 0:
    site = current_site()

    render_site_toggle()

    st.html(f"""
    <div class="login-head">
      <div class="mark">JatLog</div>
      <h1>{esc(site['app_title'])}</h1>
      <p>Identifique-se para começar. O nome fica guardado até você trocar de usuário.</p>
    </div>
    """)

    with st.container(key="loginpanel"):
        pop_error()

        user_input = st.text_input("Nome de usuário", placeholder="Seu nome")

        # 一度管理者になったら、ユーザー交代しても管理者のまま（明示的に抜けるまで）
        if st.session_state.role == "admin":
            st.html('<div class="banner info">Modo administrador ativo — '
                    'você continuará como administrador.</div>')
            with st.container(key="btn_exit_admin"):
                if st.button("Sair do modo administrador", use_container_width=True):
                    st.session_state.role = "worker"
                    st.session_state.pop("admin_pw_input", None)
                    st.rerun()
        else:
            with st.expander("Administrador"):
                st.text_input("Senha do administrador", type="password",
                              key="admin_pw_input", placeholder="Somente para o gestor")

        with st.container(key="btn_login"):
            if st.button("Começar", use_container_width=True):
                pw = str(st.session_state.get("admin_pw_input", "") or "").strip()
                already_admin = st.session_state.role == "admin"
                if not already_admin and pw and pw != ADMIN_PASSWORD:
                    st.session_state.search_error = "Senha do administrador incorreta."
                    st.rerun()
                elif not user_input or not user_input.strip():
                    st.session_state.search_error = "Informe seu nome."
                    st.rerun()
                else:
                    st.session_state.username = user_input.strip()
                    st.session_state.role = "admin" if (already_admin or pw) else "worker"
                    st.session_state.step = 8
                    st.rerun()

    st.html(f'<div class="appfoot">JatLog · v{APP_VERSION} · Google Sheets sync</div>')
    focus_last_input("text")
    st.stop()


# ==========================================
# Step 8: 月・年の選択（名前は保持したまま何度でも戻れる）
# ==========================================
if st.session_state.step == 8:
    site = current_site()

    st.html(f"""
    <div class="login-head">
      <div class="mark">JatLog</div>
      <h1>Escolha o mês</h1>
      <p>Usuário: <b>{esc(st.session_state.username)}</b>{' · administrador' if st.session_state.role == 'admin' else ''}</p>
    </div>
    """)

    with st.container(key="loginpanel"):
        pop_error()
        _now = datetime.now(TZ_MZ)
        current_year = _now.year
        year_options = [str(current_year - 1), str(current_year), str(current_year + 1)]

        # 既に選んでいた月・年があればそれを、無ければ今月を初期値にする
        def_m_idx = _now.month - 1
        def_y_idx = 1
        try:
            _pm, _py = st.session_state.target_month.split("-")
            def_m_idx = MONTHS.index(_pm)
            def_y_idx = year_options.index(f"20{_py}")
        except (ValueError, AttributeError):
            pass

        col_month, col_year = st.columns(2)
        with col_month:
            month_input = st.selectbox("Mês", MONTHS, index=def_m_idx)
        with col_year:
            year_input = st.selectbox("Ano", year_options, index=def_y_idx)

        with st.container(key="btn_login"):
            if st.button("Continuar", use_container_width=True):
                st.session_state.target_month = f"{month_input}-{year_input[-2:]}"
                st.session_state.admin_month_pick = st.session_state.target_month
                st.session_state.last_saved = None
                st.session_state.edit_target = None
                st.session_state.confirm_delete = False
                reset_to_search()
                st.rerun()

    with st.container(key="btn_logout"):
        if st.button("Trocar de usuário", use_container_width=True):
            st.session_state.username = ""
            st.session_state.target_month = ""
            st.session_state.pop("admin_pw_input", None)
            st.session_state.step = 0
            st.rerun()

    st.html(f'<div class="appfoot">JatLog · v{APP_VERSION} · Google Sheets sync</div>')
    st.stop()


# ==========================================
# データ読み込み
# ==========================================
try:
    _site_cfg = current_site()
    df_master = load_master_data(_site_cfg["spreadsheet_key"])
    df_log = load_log_data(_site_cfg["spreadsheet_key"], _site_cfg["log_tab"])
except Exception as e:
    st.html(
        f'<div class="banner error">Não foi possível carregar os dados. {esc(e)}</div>'
    )
    if st.button("Tentar novamente", use_container_width=True, key="retry_load"):
        load_master_data.clear()
        load_log_data.clear()
        get_or_create_ws.clear()
        get_spreadsheet.clear()
        st.rerun()
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
_adm_badge = '<span class="badge-adm">ADMIN</span>' if st.session_state.role == "admin" else ""
st.html(f"""
<div class="topbar">
  <div class="who">
    <div class="name">{esc(st.session_state.username)}{_adm_badge}</div>
    <div class="month">{esc(st.session_state.target_month)} · {esc(_site_cfg['label'])}</div>
  </div>
  <div class="counter">
    <div class="num">{sack_count}</div>
    <div class="lbl">registros</div>
  </div>
</div>
""")


# ==========================================
# Step 1: ライン番号検索
# ==========================================
if st.session_state.step == 1:
    site = current_site()

    render_site_toggle()

    # 管理者はログインし直さずに任意の月へ移動できる
    if st.session_state.role == "admin":
        def _admin_pick_month():
            pick = st.session_state.get("admin_month_pick")
            if pick and pick != st.session_state.target_month:
                st.session_state.target_month = pick
                st.session_state.last_saved = None
                reset_to_search()

        _cy = datetime.now(TZ_MZ).year
        _mopts = [f"{m}-{str(y)[-2:]}" for y in (_cy - 1, _cy, _cy + 1) for m in MONTHS]
        _cur = st.session_state.target_month
        if _cur not in _mopts:
            _mopts = [_cur] + _mopts
        with st.container(key="adminmonthrow"):
            st.selectbox("Mês (administrador)", _mopts, index=_mopts.index(_cur),
                         key="admin_month_pick", on_change=_admin_pick_month)

    def process_search():
        site = current_site()
        raw = st.session_state.get(f"search_{st.session_state.form_counter}", "")
        val = unicodedata.normalize('NFKC', str(raw)).strip()
        st.session_state.search_error = ""
        if not val:
            return
        st.session_state.last_saved = None
        if not val.isdigit():
            st.session_state.search_error = "Digite apenas números."
            return

        target = int(val)
        matched = [row for _, row in df_master.iterrows()
                   if get_first_number(row.get(site["field_col"], ""), site["prefix"]) == target]

        if len(matched) == 1:
            st.session_state.selected_line = matched[0].get(site["field_col"], "")
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
            st.session_state.search_error = site["not_found"].format(val=val)

    pop_error()

    # 直近の保存成功を明示（「本当に保存されたか」への確実なフィードバック）
    if st.session_state.last_saved:
        _ls = st.session_state.last_saved
        st.html(
            f'<div class="banner ok"><span class="tick">✓</span>'
            f'<b>{esc(_ls["line"])}</b> — {esc(_ls["val"])} {esc(_ls["unit"])} '
            f'salvo às {esc(_ls["time"])}</div>'
        )

    st.html(f'<div class="eyebrow">{esc(site["search_label"])}</div>')

    with st.container(key="searchpanel"):
        st.text_input(
            site["search_input_label"],
            placeholder="1",
            key=f"search_{st.session_state.form_counter}",
            on_change=process_search,
            label_visibility="collapsed"
        )

    st.html(
        '<div class="banner info">Digite o número e toque em Enter para avançar.</div>'
    )

    l1, l2 = st.columns(2)
    with l1:
        with st.container(key="btn_month"):
            # 名前はそのままに、月・年の選択画面へ戻る
            if st.button("Mudar mês", use_container_width=True):
                st.session_state.candidate_rows = []
                st.session_state.last_saved = None
                st.session_state.step = 8
                st.rerun()
    with l2:
        with st.container(key="btn_logout"):
            # 管理者権限は保持したまま名前だけ入れ直せる（抜けるのはログイン画面から）
            if st.button("Trocar de usuário", use_container_width=True):
                st.session_state.username = ""
                st.session_state.target_month = ""
                st.session_state.candidate_rows = []
                st.session_state.last_saved = None
                st.session_state.pop("admin_pw_input", None)
                st.session_state.step = 0
                st.rerun()

    focus_last_input("numeric")


# ==========================================
# Step 15: 候補が複数あるとき
# ==========================================
elif st.session_state.step == 15:
    site = current_site()

    st.html(
        f'<div class="banner warn">O número <b>{esc(st.session_state.searched_number)}</b> '
        f'aparece em {len(st.session_state.candidate_rows)} registros. '
        f'Escolha em qual deles você vai lançar o peso.</div>'
    )

    with st.container(key="candzone"):
        for i, row in enumerate(st.session_state.candidate_rows):
            line_name = str(row.get(site["field_col"], "")).strip()
            done = "  •  JÁ REGISTRADO" if already_registered(line_name) else ""
            label = (
                f"{line_name}{done}\n"
                f"{describe_row(row)}  ·  Saco {getv(row, 'Sack Number')}\n"
                f"{getv(row, 'Variety')}  ·  {getv(row, 'Total no.of plant', 'No.of plant available')} plantas"
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
    site = current_site()

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
                    try:
                        with st.spinner("Registrando…"):
                            write_log(w, u)
                        st.toast(f"{line_name} registrado")
                        reset_to_search()
                    except Exception:
                        st.session_state.search_error = SAVE_FAIL_MSG
                        st.session_state.pending_weight = None
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
            f'<div class="banner warn">{esc(site["already_registered_msg"])}</div>'
        )

    # --- 計量パネル ---
    with st.container(key="weightpanel"):
        st.html(f"""
        <div class="readout">
          <div class="tag">Pesando</div>
          <div class="line-code">{esc(line_name)}</div>
          <div class="sub">{esc(describe_row(row_data))} &nbsp;·&nbsp; Saco {esc(getv(row_data, 'Sack Number'))}</div>
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
      <div class="cell"><div class="k">ID da mãe</div><div class="v">{esc(getv(row_data, 'Mother Id', 'Mother ID'))}</div></div>
      <div class="cell"><div class="k">Variedade</div><div class="v">{esc(getv(row_data, 'Variety'))}</div></div>
      <div class="cell"><div class="k">Saco</div><div class="v">{esc(getv(row_data, 'Sack Number'))}</div></div>
      <div class="cell"><div class="k">Plantas</div><div class="v">{esc(getv(row_data, 'Total no.of plant', 'No.of plant available'))}</div></div>
    </div>
    """)

    focus_last_input("decimal")


# ==========================================
# Step 3: 履歴の編集（入力ミスの修正）
# ==========================================
elif st.session_state.step == 3:

    target = st.session_state.edit_target
    pop_error()

    if target is None:
        st.session_state.step = 1
        st.rerun()

    if st.session_state.confirm_delete:
        st.html(
            f'<div class="banner error">Excluir definitivamente o registro de <b>{esc(target["line"])}</b> '
            f'({esc(target["val"])} {esc(target["unit"])})? Esta ação não pode ser desfeita.</div>'
        )
        st.html(f"""
        <div class="readout">
          <div class="tag">Registro a excluir</div>
          <div class="line-code">{esc(target['line'])}</div>
          <div class="sub">Lançado em {esc(target['stamp'])} por {esc(target.get('author', '-'))}</div>
        </div>
        """)

        d1, d2 = st.columns(2)
        with d1:
            with st.container(key="btn_danger"):
                if st.button("Sim, excluir", use_container_width=True):
                    if not can_modify(target.get("author", "")):
                        st.session_state.search_error = NO_PERMISSION_MSG
                        st.session_state.confirm_delete = False
                        st.rerun()
                    try:
                        with st.spinner("Excluindo…"):
                            delete_log_row(target)
                        st.toast(f"{target['line']} excluído")
                    except StaleRowError:
                        load_log_data.clear()
                        st.session_state.search_error = STALE_MSG
                    except Exception:
                        st.session_state.search_error = SAVE_FAIL_MSG
                    st.session_state.edit_target = None
                    st.session_state.confirm_delete = False
                    st.session_state.step = st.session_state.return_step or 1
                    st.rerun()
        with d2:
            with st.container(key="btn_cancel"):
                if st.button("Não, voltar", use_container_width=True):
                    st.session_state.confirm_delete = False
                    st.rerun()

    else:
        st.html(
            f'<div class="banner warn">Corrigindo o peso registrado para <b>{esc(target["line"])}</b>. '
            f'Ajuste o valor e salve.</div>'
        )

        with st.container(key="weightpanel"):
            st.html(f"""
            <div class="readout">
              <div class="tag">Editando registro</div>
              <div class="line-code">{esc(target['line'])}</div>
              <div class="sub">Lançado em {esc(target['stamp'])} por {esc(target.get('author', '-'))}</div>
            </div>
            """)

            edit_key = f"editweight_{st.session_state.form_counter}"
            if edit_key not in st.session_state:
                st.session_state[edit_key] = target["val"]
            st.text_input(
                "Novo peso",
                key=edit_key,
                label_visibility="collapsed"
            )

        _unit_e = st.session_state.get("unit_edit", target["unit"])
        with st.container(key="unitrow"):
            u1, u2 = st.columns(2)
            with u1:
                with st.container(key=f"unit_kg_{'on' if _unit_e == 'kg' else 'off'}"):
                    if st.button("kg", use_container_width=True, key="pick_kg_edit"):
                        st.session_state.unit_edit = "kg"
                        st.rerun()
            with u2:
                with st.container(key=f"unit_g_{'on' if _unit_e == 'g' else 'off'}"):
                    if st.button("g", use_container_width=True, key="pick_g_edit"):
                        st.session_state.unit_edit = "g"
                        st.rerun()

        c1, c2 = st.columns(2)
        with c1:
            with st.container(key="btn_confirm"):
                if st.button("Salvar", use_container_width=True):
                    process_edit_save()
                    st.rerun()
        with c2:
            with st.container(key="btn_cancel"):
                if st.button("Cancelar", use_container_width=True):
                    st.session_state.edit_target = None
                    st.session_state.step = st.session_state.return_step or 1
                    st.rerun()

        with st.container(key="btn_delete"):
            if st.button("Excluir este registro", use_container_width=True):
                st.session_state.confirm_delete = True
                st.rerun()

        focus_last_input("decimal")


# ==========================================
# 履歴
# ==========================================
if st.session_state.step in (1, 2, 15):
    st.html('<div class="eyebrow" style="margin-top:26px">Últimos registros</div>')

    if not df_month.empty and len(df_log.columns) >= 6:
        c_time, c_user, c_month, c_line, c_val, c_unit = (
            df_log.columns[0], df_log.columns[1], df_log.columns[2],
            df_log.columns[3], df_log.columns[4], df_log.columns[5])
        with st.container(key="histzone"):
            for idx, r in df_month.tail(8)[::-1].iterrows():
                ts_full = str(r.get(c_time, ""))
                stamp = ts_full[5:16]   # MM-DD HH:MM
                author = str(r.get(c_user, "")).strip()
                line_val = str(r.get(c_line, "-")).strip()
                val = str(r.get(c_val, "-")).strip()
                unit_val = str(r.get(c_unit, "")).strip()

                if can_modify(author):
                    who = "você" if author.casefold() == st.session_state.username.strip().casefold() else author
                    label = f"{line_val}    {val} {unit_val}\n{stamp} · {who} · toque para corrigir"
                    if st.button(label, key=f"hist_{idx}", use_container_width=True):
                        st.session_state.edit_target = {
                            "row": int(idx) + 2,
                            "line": line_val,
                            "val": val,
                            "unit": unit_val if unit_val in ("kg", "g") else "kg",
                            "stamp": stamp,
                            "ts_full": ts_full,
                            "author": author,
                            "month": str(r.get(c_month, "")).strip(),
                        }
                        st.session_state.unit_edit = st.session_state.edit_target["unit"]
                        st.session_state.return_step = st.session_state.step
                        st.session_state.form_counter += 1
                        st.session_state.step = 3
                        st.rerun()
                else:
                    st.html(
                        f'<div class="histrow">{esc(line_val)} &nbsp;&nbsp; {esc(val)} {esc(unit_val)}'
                        f'<div class="hs">{esc(stamp)} · {esc(author)} · 🔒 só o autor ou o admin</div></div>'
                    )
    else:
        st.html(
            f'<div class="empty">Nenhum registro em {esc(st.session_state.target_month)} ainda.</div>'
        )
