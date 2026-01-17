import streamlit as st
from datetime import datetime
import pandas as pd
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time

# ---------------- إعداد Logging ----------------
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ---------------- إعداد الصفحة ----------------
st.set_page_config(
    page_title="نظام إدارة المذكرات",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ---------------- CSS الاحترافي ----------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;600;700;800;900&display=swap');

* {
    font-family: 'Cairo', sans-serif !important;
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

/* إخفاء عناصر Streamlit الافتراضية */
#MainMenu, footer, header {visibility: hidden;}
.stDeployButton {display: none;}

/* الخلفية الرئيسية */
.stApp {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    background-attachment: fixed;
}

.main > div {
    padding: 0 !important;
    max-width: 100% !important;
}

/* Container رئيسي */
.main-container {
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 2rem;
}

/* بطاقات Glassmorphism */
.glass-card {
    background: rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(20px) saturate(180%);
    border-radius: 30px;
    border: 1px solid rgba(255, 255, 255, 0.2);
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
    padding: 3rem;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.glass-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 30px 80px rgba(0, 0, 0, 0.4);
}

/* العناوين */
.hero-title {
    font-size: 4rem;
    font-weight: 900;
    background: linear-gradient(135deg, #ffffff 0%, #e0e7ff 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    text-align: center;
    margin-bottom: 1rem;
    text-shadow: 0 4px 20px rgba(255, 255, 255, 0.3);
}

.hero-subtitle {
    font-size: 1.5rem;
    color: rgba(255, 255, 255, 0.9);
    text-align: center;
    margin-bottom: 3rem;
    font-weight: 300;
}

/* بطاقات الاختيار */
.role-card {
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.15) 0%, rgba(255, 255, 255, 0.05) 100%);
    backdrop-filter: blur(20px);
    border-radius: 25px;
    border: 2px solid rgba(255, 255, 255, 0.3);
    padding: 3rem;
    text-align: center;
    transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    cursor: pointer;
    position: relative;
    overflow: hidden;
}

.role-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.1) 0%, transparent 100%);
    opacity: 0;
    transition: opacity 0.3s;
}

.role-card:hover::before {
    opacity: 1;
}

.role-card:hover {
    transform: translateY(-15px) scale(1.02);
    border-color: rgba(255, 255, 255, 0.5);
    box-shadow: 0 30px 80px rgba(0, 0, 0, 0.4);
}

.role-icon {
    width: 120px;
    height: 120px;
    margin: 0 auto 2rem;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 4rem;
    box-shadow: 0 15px 40px rgba(102, 126, 234, 0.5);
}

.role-title {
    font-size: 2.5rem;
    font-weight: 800;
    color: white;
    margin-bottom: 1rem;
}

.role-desc {
    font-size: 1.2rem;
    color: rgba(255, 255, 255, 0.8);
    font-weight: 300;
}

/* بطاقات الإحصائيات */
.stat-card {
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.15) 0%, rgba(255, 255, 255, 0.05) 100%);
    backdrop-filter: blur(20px);
    border-radius: 20px;
    border: 2px solid rgba(255, 255, 255, 0.3);
    padding: 2rem;
    text-align: center;
    transition: all 0.3s;
    height: 100%;
}

.stat-card:hover {
    transform: translateY(-10px);
    border-color: rgba(255, 255, 255, 0.5);
}

.stat-icon {
    font-size: 3.5rem;
    margin-bottom: 1rem;
}

.stat-number {
    font-size: 3.5rem;
    font-weight: 900;
    color: white;
    margin: 1rem 0;
    text-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
}

.stat-label {
    font-size: 1.2rem;
    color: rgba(255, 255, 255, 0.9);
    font-weight: 600;
}

/* حقول الإدخال */
.stTextInput > div > div > input,
.stSelectbox > div > div > select,
.stTextArea > div > div > textarea {
    background: rgba(255, 255, 255, 0.15) !important;
    backdrop-filter: blur(10px) !important;
    border: 2px solid rgba(255, 255, 255, 0.3) !important;
    border-radius: 15px !important;
    color: white !important;
    font-size: 1.1rem !important;
    padding: 1rem 1.5rem !important;
    transition: all 0.3s !important;
}

.stTextInput > div > div > input:focus,
.stSelectbox > div > div > select:focus,
.stTextArea > div > div > textarea:focus {
    border-color: rgba(255, 255, 255, 0.6) !important;
    box-shadow: 0 0 0 3px rgba(255, 255, 255, 0.1) !important;
    background: rgba(255, 255, 255, 0.2) !important;
}

.stTextInput > div > div > input::placeholder {
    color: rgba(255, 255, 255, 0.6) !important;
}

/* Labels */
.stTextInput > label,
.stSelectbox > label,
.stTextArea > label {
    color: white !important;
    font-size: 1.1rem !important;
    font-weight: 600 !important;
    margin-bottom: 0.5rem !important;
}

/* الأزرار */
.stButton > button {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 15px !important;
    padding: 1.2rem 3rem !important;
    font-size: 1.3rem !important;
    font-weight: 700 !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    box-shadow: 0 10px 30px rgba(102, 126, 234, 0.4) !important;
    width: 100%;
}

.stButton > button:hover {
    transform: translateY(-3px) !important;
    box-shadow: 0 15px 40px rgba(102, 126, 234, 0.6) !important;
}

.stButton > button:active {
    transform: translateY(-1px) !important;
}

/* رسائل النجاح والخطأ */
.success-msg {
    background: linear-gradient(135deg, rgba(16, 185, 129, 0.2) 0%, rgba(5, 150, 105, 0.2) 100%);
    backdrop-filter: blur(10px);
    border: 2px solid rgba(16, 185, 129, 0.5);
    border-radius: 15px;
    padding: 1.5rem;
    color: white;
    font-size: 1.1rem;
    margin: 1rem 0;
    text-align: center;
}

.error-msg {
    background: linear-gradient(135deg, rgba(239, 68, 68, 0.2) 0%, rgba(220, 38, 38, 0.2) 100%);
    backdrop-filter: blur(10px);
    border: 2px solid rgba(239, 68, 68, 0.5);
    border-radius: 15px;
    padding: 1.5rem;
    color: white;
    font-size: 1.1rem;
    margin: 1rem 0;
    text-align: center;
}

.info-msg {
    background: linear-gradient(135deg, rgba(59, 130, 246, 0.2) 0%, rgba(37, 99, 235, 0.2) 100%);
    backdrop-filter: blur(10px);
    border: 2px solid rgba(59, 130, 246, 0.5);
    border-radius: 15px;
    padding: 1.5rem;
    color: white;
    font-size: 1.1rem;
    margin: 1rem 0;
}

/* جدول المذكرات */
.dataframe {
    background: rgba(255, 255, 255, 0.1) !important;
    backdrop-filter: blur(10px);
    border-radius: 15px !important;
    overflow: hidden;
    border: 2px solid rgba(255, 255, 255, 0.2) !important;
}

.dataframe thead tr th {
    background: rgba(255, 255, 255, 0.15) !important;
    color: white !important;
    font-weight: 700 !important;
    font-size: 1.1rem !important;
    padding: 1.5rem !important;
    border: none !important;
}

.dataframe tbody tr td {
    color: white !important;
    padding: 1.2rem !important;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1) !important;
    font-size: 1rem !important;
}

.dataframe tbody tr:hover {
    background: rgba(255, 255, 255, 0.1) !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 1rem;
    background: rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(10px);
    border-radius: 15px;
    padding: 0.5rem;
    border: 2px solid rgba(255, 255, 255, 0.2);
}

.stTabs [data-baseweb="tab"] {
    border-radius: 10px;
    padding: 1rem 2rem;
    font-weight: 600;
    font-size: 1.1rem;
    color: rgba(255, 255, 255, 0.7);
    transition: all 0.3s;
}

.stTabs [data-baseweb="tab"]:hover {
    background: rgba(255, 255, 255, 0.1);
    color: white;
}

.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    color: white !important;
    box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4);
}

/* الـ Expander */
.streamlit-expanderHeader {
    background: rgba(255, 255, 255, 0.1) !important;
    backdrop-filter: blur(10px);
    border-radius: 12px !important;
    border: 2px solid rgba(255, 255, 255, 0.2) !important;
    color: white !important;
    font-weight: 600 !important;
    font-size: 1.1rem !important;
    padding: 1rem !important;
}

.streamlit-expanderHeader:hover {
    background: rgba(255, 255, 255, 0.15) !important;
    border-color: rgba(255, 255, 255, 0.3) !important;
}

.streamlit-expanderContent {
    background: rgba(255, 255, 255, 0.05) !important;
    backdrop-filter: blur(10px);
    border: 2px solid rgba(255, 255, 255, 0.2) !important;
    border-radius: 12px !important;
    padding: 1.5rem !important;
}

/* Progress bar */
.stProgress > div > div > div {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    border-radius: 10px;
    height: 12px !important;
}

.stProgress > div > div {
    background: rgba(255, 255, 255, 0.2) !important;
    border-radius: 10px;
    height: 12px !important;
}

/* Selectbox options */
option {
    background: #764ba2 !important;
    color: white !important;
    padding: 10px !important;
}

/* Footer */
.footer {
    text-align: center;
    padding: 2rem;
    color: rgba(255, 255, 255, 0.8);
    background: rgba(255, 255, 255, 0.05);
    backdrop-filter: blur(10px);
    border-radius: 15px;
    border: 2px solid rgba(255, 255, 255, 0.1);
    margin-top: 3rem;
}

/* شعار */
.logo {
    width: 150px;
    height: 150px;
    margin: 0 auto 2rem;
    display: block;
    filter: drop-shadow(0 10px 30px rgba(0, 0, 0, 0.3));
    animation: float 3s ease-in-out infinite;
}

@keyframes float {
    0%, 100% { transform: translateY(0px); }
    50% { transform: translateY(-10px); }
}

/* تحسين المسافات */
.block-container {
    padding: 0 !important;
    max-width: none !important;
}

/* Radio buttons */
.stRadio > div {
    background: rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(10px);
    border-radius: 15px;
    border: 2px solid rgba(255, 255, 255, 0.2);
    padding: 1rem;
}

.stRadio > div > label {
    color: white !important;
    font-size: 1.1rem !important;
    font-weight: 600 !important;
}

/* Columns */
[data-testid="column"] {
    padding: 0.5rem !important;
}
</style>
""", unsafe_allow_html=True)

# ---------------- باقي الكود من النسخة السابقة مع تعديلات بسيطة ----------------

# [باقي imports و Google Sheets configuration كما هو]

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
info = st.secrets["service_account"]
credentials = Credentials.from_service_account_info(info, scopes=SCOPES)
sheets_service = build('sheets', 'v4', credentials=credentials)

STUDENTS_SHEET_ID = "1CHQyE1GJHlmynvaj2ez89Lf_S7Y3GU8T9rrl75rnF5c"
MEMOS_SHEET_ID = "1oV2RYEWejDaRpTrKhecB230SgEo6dDwwLzUjW6VPw6o"
PROF_MEMOS_SHEET_ID = "15u6N7XLFUKvTEmNtUNKVytpqVAQLaL19cAM8xZB_u3A"

STUDENTS_RANGE = "Feuille 1!A1:M1000"
MEMOS_RANGE = "Feuille 1!A1:O1000"
PROF_MEMOS_RANGE = "Feuille 1!A1:N1000"

EMAIL_SENDER = "domaine.dsp@univ-bba.dz"
EMAIL_PASSWORD = "oevruyiztgikwzah"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# دوال مساعدة
def col_letter(n):
    result = ""
    while n > 0:
        n, remainder = divmod(n - 1, 26)
        result = chr(65 + remainder) + result
    return result

def sanitize_input(text):
    if not text:
        return ""
    dangerous_chars = ['<', '>', '"', "'", ';', '&', '|', '`']
    cleaned = str(text).strip()
    for char in dangerous_chars:
        cleaned = cleaned.replace(char, '')
    return cleaned

@st.cache_data(ttl=60)
def load_students():
    try:
        result = sheets_service.spreadsheets().values().get(
            spreadsheetId=STUDENTS_SHEET_ID, 
            range=STUDENTS_RANGE
        ).execute()
        values = result.get('values', [])
        if not values:
            return pd.DataFrame()
        df = pd.DataFrame(values[1:], columns=values[0])
        return df
    except Exception as e:
        logger.error(f"خطأ في تحميل بيانات الطلاب: {str(e)}")
        return pd.DataFrame()

@st.cache_data(ttl=60)
def load_memos():
    try:
        result = sheets_service.spreadsheets().values().get(
            spreadsheetId=MEMOS_SHEET_ID, 
            range=MEMOS_RANGE
        ).execute()
        values = result.get('values', [])
        if not values:
            return pd.DataFrame()
        df = pd.DataFrame(values[1:], columns=values[0])
        return df
    except Exception as e:
        logger.error(f"خطأ في تحميل بيانات المذكرات: {str(e)}")
        return pd.DataFrame()

@st.cache_data(ttl=60)
def load_prof_memos():
    try:
        result = sheets_service.spreadsheets().values().get(
            spreadsheetId=PROF_MEMOS_SHEET_ID, 
            range=PROF_MEMOS_RANGE
        ).execute()
        values = result.get('values', [])
        if not values:
            return pd.DataFrame()
        df = pd.DataFrame(values[1:], columns=values[0])
        return df
    except Exception as e:
        logger.error(f"خطأ في تحميل بيانات مذكرات الأساتذة: {str(e)}")
        return pd.DataFrame()

def clear_cache():
    st.cache_data.clear()

def verify_professor(username, password, df_prof_memos):
    username = sanitize_input(username)
    password = sanitize_input(password)
    
    if df_prof_memos.empty:
        return False, "❌ خطأ في تحميل البيانات"
    
    prof = df_prof_memos[
        (df_prof_memos.get("اسم المستخدم", pd.Series()).astype(str).str.strip() == username) &
        (df_prof_memos.get("كلمة المرور", pd.Series()).astype(str).str.strip() == password)
    ]
    
    if prof.empty:
        logger.warning(f"محاولة دخول أستاذ فاشلة: {username}")
        return False, "❌ اسم المستخدم أو كلمة المرور غير صحيحة"
    
    logger.info(f"تسجيل دخول أستاذ ناجح: {username}")
    return True, prof.iloc[0]

# Session State
if 'page' not in st.session_state:
    st.session_state.page = "home"
if 'user_type' not in st.session_state:
    st.session_state.user_type = None
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_data' not in st.session_state:
    st.session_state.user_data = None

def logout():
    st.session_state.page = "home"
    st.session_state.user_type = None
    st.session_state.logged_in = False
    st.session_state.user_data = None
    st.rerun()

# الصفحة الرئيسية
def show_home_page():
    st.markdown("""
        <div class="main-container">
            <div style="max-width: 1400px; width: 100%;">
                <div style="text-align: center; margin-bottom: 4rem;">
                    <img src="https://raw.githubusercontent.com/SAMIR-MALEK/memoire-depot-2026/main/LOGO2.png" class="logo">
                    <h1 class="hero-title">🎓 نظام إدارة المذكرات</h1>
                    <p class="hero-subtitle">جامعة محمد البشير الإبراهيمي - كلية الحقوق والعلوم السياسية</p>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        col_student, col_prof = st.columns(2)
        
        with col_student:
            st.markdown("""
                <div class="role-card">
                    <div class="role-icon">👨‍🎓</div>
                    <h2 class="role-title">طالب</h2>
                    <p class="role-desc">تسجيل ومتابعة المذكرات</p>
                </div>
            """, unsafe_allow_html=True)
            
            if st.button("الدخول كطالب", key="btn_student", use_container_width=True):
                st.session_state.user_type = "student"
                st.session_state.page = "student_login"
                st.rerun()
        
        with col_prof:
            st.markdown("""
                <div class="role-card">
                    <div class="role-icon">👨‍🏫</div>
                    <h2 class="role-title">أستاذ</h2>
                    <p class="role-desc">لوحة التحكم والإدارة</p>
                </div>
            """, unsafe_allow_html=True)
            
            if st.button("الدخول كأستاذ", key="btn_prof", use_container_width=True):
                st.session_state.user_type = "professor"
                st.session_state.page = "prof_login"
                st.rerun()
        
        st.markdown("<br><br>", unsafe_allow_html=True)
        
        st.markdown("""
            <div class="footer">
                <p style="font-size: 1.2rem; font-weight: 600;">© 2026 جامعة محمد البشير الإبراهيمي</p>
                <p style="opacity: 0.8; margin-top: 0.5rem;">كلية الحقوق والعلوم السياسية - جميع الحقوق محفوظة</p>
            </div>
        """, unsafe_allow_html=True)

# تسجيل دخول الأستاذ
def show_prof_login():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        
        st.markdown("""
            <div class="glass-card">
                <div style="text-align: center; margin-bottom: 3rem;">
                    <div class="role-icon" style="width: 100px; height: 100px; font-size: 3rem; margin: 0 auto 1.5rem;">👨‍🏫</div>
                    <h1 class="hero-title" style="font-size: 2.5rem;">فضاء الأستاذ</h1>
                    <p class="hero-subtitle" style="font-size: 1.2rem; margin-bottom: 0;">تسجيل الدخول</p>
                </div>
        """, unsafe_allow_html=True)
        
        username = st.text_input("📧 اسم المستخدم", key="prof_username")
        password = st.text_input("🔑 كلمة المرور", type="password", key="prof_password")
        
        if st.button("🚀 تسجيل الدخول", use_container_width=True):
            if not username or not password:
                st.markdown('<div class="error-msg">⚠️ يرجى إدخال جميع البيانات</div>', unsafe_allow_html=True)
            else:
                df_prof_memos = load_prof_memos()
                valid, result = verify_professor(username, password, df_prof_memos)
                
                if valid:
                    st.session_state.logged_in = True
                    st.session_state.user_data = result
                    st.session_state.page = "prof_dashboard"
                    st.rerun()
                else:
                    st.markdown(f'<div class="error-msg">{result}</div>', unsafe_allow_html=True)
        
        if st.button("◀️ رجوع للرئيسية", use_container_width=True):
            st.session_state.page = "home"
            st.rerun()
        
        st.markdown("</div>", unsafe_allow_html=True)

# لوحة تحكم الأستاذ
def show_prof_dashboard():
    prof_data = st.session_state.user_data
    prof_name = prof_data.get("الأستاذ", "").strip()
    
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown(f'<h1 class="hero-title" style="text-align: right; font-size: 2.5rem;">مرحباً أ. {prof_name} 👋</h1>', unsafe_allow_html=True)
    with col2:
        if st.button("🚪 خروج", use_container_width=True):
            logout()
    
    clear_cache()
    df_prof_memos = load_prof_memos()
    
    prof_memos = df_prof_memos[df_prof_memos["الأستاذ"].astype(str).str.strip() == prof_name]
    
    total = len(prof_memos)
    registered = len(prof_memos[prof_memos["تم التسجيل"].astype(str).str.strip() == "نعم"])
    remaining = total - registered
    percentage = (registered / total * 100) if total > 0 else 0
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
            <div class="stat-card">
                <div class="stat-icon">📚</div>
                <div class="stat-number"