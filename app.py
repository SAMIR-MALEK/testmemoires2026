import streamlit as st
from datetime import datetime
import pandas as pd
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# ---------------- إعداد الصفحة ----------------
st.set_page_config(page_title="تسجيل مذكرة ماستر", page_icon="🎓", layout="centered")

# ---------------- CSS للواجهة ----------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
html, body, [class*="css"]  { font-family: 'Cairo', sans-serif !important; }
.main { background-color: #0A1B2C; color: #ffffff; }
.block-container { padding: 2rem; background-color: #1A2A3D; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.5); max-width: 750px; margin: auto; }
label, h1, h2, h3, h4, h5, h6, p, span, .stTextInput label { color: #ffffff !important; }
input, button, select { font-size: 16px !important; }
button { background-color: #256D85 !important; color: white !important; border: none !important; padding: 10px 20px !important; border-radius: 6px !important; transition: background-color 0.3s ease; }
button:hover { background-color: #2C89A0 !important; }
hr { border: 1px solid #00CED1; margin: 20px 0; }
.message { font-size: 18px; font-weight: bold; text-align: center; margin: 10px 0; color: #FFFFFF; }
</style>
""", unsafe_allow_html=True)

# ---------------- اتصال Google Sheets ----------------
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
info = st.secrets["service_account"]
credentials = Credentials.from_service_account_info(info, scopes=SCOPES)
sheets_service = build('sheets', 'v4', credentials=credentials)

# ---------------- معرفات الشيتات ----------------
STUDENTS_SHEET_ID = "1CHQyE1GJHlmynvaj2ez89Lf_S7Y3GU8T9rrl75rnF5c"
MEMOS_SHEET_ID = "1oV2RYEWejDaRpTrKhecB230SgEo6dDwwLzUjW6VPw6o"
PROF_MEMOS_SHEET_ID = "15u6N7XLFUKvTEmNtUNKVytpqVAQLaL19cAM8xZB_u3A"

STUDENTS_RANGE = "Feuille 1!A1:L1000"
MEMOS_RANGE = "Feuille 1!A1:N1000"
PROF_MEMOS_RANGE = "Feuille 1!A1:L1000"

# ---------------- تحميل البيانات ----------------
@st.cache_data(ttl=300)
def load_students():
    result = sheets_service.spreadsheets().values().get(spreadsheetId=STUDENTS_SHEET_ID, range=STUDENTS_RANGE).execute()
    values = result.get('values', [])
    if not values: st.error("❌ لا توجد بيانات في صفحة الطلاب."); st.stop()
    df = pd.DataFrame(values[1:], columns=values[0])
    return df

@st.cache_data(ttl=300)
def load_memos():
    result = sheets_service.spreadsheets().values().get(spreadsheetId=MEMOS_SHEET_ID, range=MEMOS_RANGE).execute()
    values = result.get('values', [])
    if not values: st.error("❌ لا توجد بيانات في صفحة المذكرات.");