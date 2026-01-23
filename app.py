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

# ---------------- تهيئة Session State ----------------
if 'user_type' not in st.session_state:
    st.session_state.user_type = None
    st.session_state.logged_in = False
    st.session_state.student1 = None
    st.session_state.student2 = None
    st.session_state.professor = None
    st.session_state.admin_user = None
    st.session_state.memo_type = "فردية"
    st.session_state.mode = "register"
    st.session_state.note_number = ""
    st.session_state.prof_password = ""
    st.session_state.show_confirmation = False

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
    
    # استخدام selectbox بدلاً من أزرار لتجنب مشاكل CSS
    user_type = st.selectbox(
        "اختر نوع المستخدم:",
        ["", "👨‍🎓 طلبة", "👨‍🏫 أساتذة", "⚙️ إدارة"],
        index=0
    )
    
    if user_type:
        if "طلبة" in user_type:
            st.session_state.user_type = "student"
        elif "أساتذة" in user_type:
            st.session_state.user_type = "professor"
        elif "إدارة" in user_type:
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