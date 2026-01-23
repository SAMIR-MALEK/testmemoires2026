import streamlit as st
from datetime import datetime
import pandas as pd
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import logging
import time
import uuid

# ---------------- إعداد Logging ----------------
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ---------------- إعداد الصفحة ----------------
st.set_page_config(page_title="نظام تسجيل المذكرات", page_icon="📘", layout="wide")

# ---------------- CSS بسيط ----------------
st.markdown("""
<style>
body {
    font-family: 'Cairo', sans-serif;
    direction: rtl;
    text-align: right;
    background-color: #0A1B2C;
    color: white;
}
.main {
    background-color: #0A1B2C;
}
.block-container {
    background-color: #1A2A3D;
    border-radius: 16px;
    padding: 2rem;
}
h1, h2, h3 {
    color: #F8FAFC;
}
.stButton>button {
    background-color: #2F6F7E;
    color: white;
    border-radius: 12px;
    padding: 10px 20px;
}
.stButton>button:hover {
    background-color: #285E6B;
}
</style>
""", unsafe_allow_html=True)

# ================= Google Sheets Config =================
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
try:
    info = st.secrets["service_account"]
    credentials = Credentials.from_service_account_info(info, scopes=SCOPES)
    sheets_service = build('sheets', 'v4', credentials=credentials)
except Exception as e:
    st.error("⚠️ خطأ في ملف Secrets أو الاتصال بـ Google.")
    st.stop()

# --- معرفات الشيتات ---
STUDENTS_SHEET_ID = "1gvNkOVVKo6AO07dRKMnSQw6vZ3KdUnW7I4HBk61Sqns"
MEMOS_SHEET_ID = "1LNJMBAye4QIQy7JHz6F8mQ6-XNC1weZx1ozDZFfjD5s"
PROF_MEMOS_SHEET_ID = "1OnZi1o-oPMUI_W_Ew-op0a1uOhSj006hw_2jrMD6FSE"
REQUESTS_SHEET_ID = "1sTJ6BZRM4Qgt0w2xUkpFZqquL-hfriMYTSN3x1_12_o"

# ================= Data Loading =================
@st.cache_data(ttl=60)
def load_students():
    try:
        result = sheets_service.spreadsheets().values().get(spreadsheetId=STUDENTS_SHEET_ID, range="Feuille 1!A1:L1000").execute()
        values = result.get('values', [])
        if not values: return pd.DataFrame()
        df = pd.DataFrame(values[1:], columns=values[0])
        return df
    except Exception as e:
        logger.error(f"Error loading students: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=60)
def load_memos():
    try:
        result = sheets_service.spreadsheets().values().get(spreadsheetId=MEMOS_SHEET_ID, range="Feuille 1!A1:T1000").execute()
        values = result.get('values', [])
        if not values: return pd.DataFrame()
        df = pd.DataFrame(values[1:], columns=values[0])
        return df
    except Exception as e:
        logger.error(f"Error loading memos: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=30)
def load_requests():
    try:
        result = sheets_service.spreadsheets().values().get(spreadsheetId=REQUESTS_SHEET_ID, range="Feuille 1!A1:K1000").execute()
        values = result.get('values', [])
        if not values: return pd.DataFrame()
        df = pd.DataFrame(values[1:], columns=values[0])
        return df
    except Exception as e:
        logger.error(f"Error loading requests: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=60)
def load_prof_memos():
    try:
        result = sheets_service.spreadsheets().values().get(spreadsheetId=PROF_MEMOS_SHEET_ID, range="Feuille 1!A1:P1000").execute()
        values = result.get('values', [])
        if not values: return pd.DataFrame()
        df = pd.DataFrame(values[1:], columns=values[0])
        return df
    except Exception as e:
        logger.error(f"Error loading prof memos: {e}")
        return pd.DataFrame()

# ================= Main Logic =================

# تحميل البيانات
st.info("🔄 جاري تحميل البيانات...")
df_students = load_students()
df_memos = load_memos()
df_prof_memos = load_prof_memos()
df_requests = load_requests()

st.info("✅ انتهى تحميل البيانات")

# 1. HOME
if st.session_state.user_type is None:
    st.markdown("<h1 style='text-align:center;'>نظام تسجيل المذكرات</h1>", unsafe_allow_html=True)
    st.info("🔄 جاري عرض واجهة الدخول...")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("👨‍🎓 طلبة"): 
            st.session_state.user_type = "student"
            st.rerun()
    with col2:
        if st.button("👨‍🏫 أساتذة"): 
            st.session_state.user_type = "professor"
            st.rerun()
    with col3:
        if st.button("⚙️ إدارة"): 
            st.session_state.user_type = "admin"
            st.rerun()

# 2. STUDENTS
elif st.session_state.user_type == "student":
    st.write("صفحة طلاب")

# 3. PROFESSOR
elif st.session_state.user_type == "professor":
    st.write("صفحة أساتذة")

# 4. ADMIN
elif st.session_state.user_type == "admin":
    st.write("صفحة إدارة")

# السطر الأخير
st.markdown('<div style="text-align:center; color:#666; font-size:12px;">© 2026 جامعة محمد البشير الإبراهيمي - كلية الحقوق</div>', unsafe_allow_html=True)