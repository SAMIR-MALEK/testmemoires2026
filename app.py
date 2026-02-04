import streamlit as st
from datetime import datetime, time, date
import pandas as pd
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time
import textwrap
import base64

# ---------------- إعداد Logging ----------------
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ---------------- إعداد الصفحة ----------------
st.set_page_config(
    page_title="🎓 منصة تسجيل مذكرات الماستر",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========================
# إعداد الموعد النهائي
# ========================
REGISTRATION_DEADLINE = datetime(2027, 1, 28, 23, 59)

# ---------------- LEGENDARY CSS - تصميم أسطوري خرافي ----------------
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;600;700;900&family=Tajawal:wght@300;400;500;700;900&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
<style>
/* ═══════════════════════════════════════════════════════════════
   🎨 LEGENDARY DESIGN SYSTEM - تصميم أسطوري خرافي
   ═══════════════════════════════════════════════════════════════ */

/* 🌟 متغيرات الألوان الأسطورية */
:root {
    --primary-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    --secondary-gradient: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    --success-gradient: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
    --gold-gradient: linear-gradient(135deg, #f6d365 0%, #fda085 100%);
    --dark-bg: #0f0c29;
    --card-bg: rgba(21, 23, 35, 0.95);
    --glass-bg: rgba(255, 255, 255, 0.03);
    --neon-blue: #00f3ff;
    --neon-purple: #bc13fe;
    --neon-pink: #ff006e;
    --gold: #ffd700;
}

/* 🎭 الخلفية الأسطورية المتحركة */
html, body, [class*="css"] {
    font-family: 'Tajawal', 'Cairo', sans-serif !important;
    direction: rtl;
    text-align: right;
}

.main {
    background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
    background-size: 400% 400%;
    animation: gradientShift 15s ease infinite;
    color: #ffffff;
    position: relative;
    overflow-x: hidden;
}

/* خلفية متحركة بجزيئات */
.main::before {
    content: '';
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: 
        radial-gradient(circle at 20% 50%, rgba(102, 126, 234, 0.1) 0%, transparent 50%),
        radial-gradient(circle at 80% 80%, rgba(188, 19, 254, 0.1) 0%, transparent 50%),
        radial-gradient(circle at 40% 20%, rgba(0, 243, 255, 0.08) 0%, transparent 50%);
    pointer-events: none;
    z-index: 0;
    animation: floatingParticles 20s ease-in-out infinite;
}

@keyframes gradientShift {
    0%, 100% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
}

@keyframes floatingParticles {
    0%, 100% { transform: translate(0, 0) scale(1); }
    33% { transform: translate(30px, -30px) scale(1.1); }
    66% { transform: translate(-20px, 20px) scale(0.9); }
}

/* 🎯 Container الرئيسي */
.block-container {
    padding: 2rem 3rem;
    background: transparent;
    border-radius: 0;
    margin: auto;
    max-width: 1400px;
    position: relative;
    z-index: 1;
}

/* 🎨 العناوين الأسطورية */
h1 {
    font-family: 'Tajawal', sans-serif !important;
    font-weight: 900 !important;
    font-size: 3.5rem !important;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    text-align: center;
    margin-bottom: 1rem !important;
    animation: titleGlow 3s ease-in-out infinite;
    position: relative;
}

h1::after {
    content: '';
    position: absolute;
    bottom: -15px;
    left: 50%;
    transform: translateX(-50%);
    width: 200px;
    height: 4px;
    background: var(--primary-gradient);
    border-radius: 2px;
    box-shadow: 0 0 20px rgba(102, 126, 234, 0.6);
}

@keyframes titleGlow {
    0%, 100% { filter: brightness(1) drop-shadow(0 0 20px rgba(102, 126, 234, 0.4)); }
    50% { filter: brightness(1.2) drop-shadow(0 0 40px rgba(102, 126, 234, 0.8)); }
}

h2, h3, h4 {
    font-weight: 700 !important;
    color: #ffffff !important;
    margin-bottom: 1.5rem !important;
    text-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
}

h2 {
    font-size: 2rem !important;
    background: linear-gradient(90deg, #667eea, #f093fb);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

/* 🎴 البطاقات الزجاجية الأسطورية (Glassmorphism) */
.card {
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.05), rgba(255, 255, 255, 0.02));
    backdrop-filter: blur(20px) saturate(180%);
    -webkit-backdrop-filter: blur(20px) saturate(180%);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 24px;
    padding: 2.5rem;
    margin-bottom: 2rem;
    box-shadow: 
        0 20px 60px rgba(0, 0, 0, 0.3),
        inset 0 1px 0 rgba(255, 255, 255, 0.1),
        0 0 0 1px rgba(255, 255, 255, 0.05);
    transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;
    overflow: hidden;
}

.card::before {
    content: '';
    position: absolute;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: radial-gradient(circle, rgba(102, 126, 234, 0.1) 0%, transparent 70%);
    opacity: 0;
    transition: opacity 0.5s ease;
}

.card:hover {
    transform: translateY(-8px) scale(1.01);
    box-shadow: 
        0 30px 80px rgba(102, 126, 234, 0.25),
        inset 0 1px 0 rgba(255, 255, 255, 0.2),
        0 0 0 1px rgba(102, 126, 234, 0.3);
    border-color: rgba(102, 126, 234, 0.3);
}

.card:hover::before {
    opacity: 1;
}

/* 📊 KPI Cards - بطاقات المؤشرات الخرافية */
.kpi-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 2rem;
    margin-bottom: 3rem;
}

.kpi-card {
    background: linear-gradient(135deg, rgba(102, 126, 234, 0.1), rgba(118, 75, 162, 0.05));
    backdrop-filter: blur(15px);
    border: 2px solid rgba(255, 255, 255, 0.08);
    border-radius: 20px;
    padding: 2rem 1.5rem;
    text-align: center;
    position: relative;
    overflow: hidden;
    transition: all 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
}

.kpi-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.1), transparent);
    transition: left 0.5s ease;
}

.kpi-card:hover {
    transform: translateY(-10px) scale(1.05);
    border-color: var(--neon-blue);
    box-shadow: 
        0 20px 60px rgba(102, 126, 234, 0.4),
        0 0 40px rgba(0, 243, 255, 0.3),
        inset 0 0 20px rgba(102, 126, 234, 0.2);
}

.kpi-card:hover::before {
    left: 100%;
}

.kpi-icon {
    font-size: 3rem;
    margin-bottom: 1rem;
    background: var(--primary-gradient);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    filter: drop-shadow(0 0 10px rgba(102, 126, 234, 0.5));
}

.kpi-value {
    font-size: 3.5rem;
    font-weight: 900;
    background: linear-gradient(135deg, #ffd700, #ffed4e, #ffd700);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 1rem 0;
    filter: drop-shadow(0 0 20px rgba(255, 215, 0, 0.6));
    animation: numberPulse 2s ease-in-out infinite;
}

@keyframes numberPulse {
    0%, 100% { transform: scale(1); }
    50% { transform: scale(1.05); }
}

.kpi-label {
    font-size: 1.1rem;
    color: #cbd5e1;
    font-weight: 600;
    letter-spacing: 0.5px;
    text-transform: uppercase;
}

/* 🚨 Alert Card - تنبيه أسطوري */
.alert-card {
    background: linear-gradient(135deg, #ff006e 0%, #8b0000 100%);
    border: 2px solid rgba(255, 0, 110, 0.5);
    color: white;
    padding: 2rem;
    border-radius: 20px;
    box-shadow: 
        0 20px 60px rgba(255, 0, 110, 0.3),
        0 0 40px rgba(255, 0, 110, 0.2),
        inset 0 1px 0 rgba(255, 255, 255, 0.2);
    text-align: center;
    font-weight: bold;
    font-size: 1.3rem;
    position: relative;
    overflow: hidden;
    animation: alertPulse 2s ease-in-out infinite;
}

@keyframes alertPulse {
    0%, 100% { box-shadow: 0 20px 60px rgba(255, 0, 110, 0.3), 0 0 40px rgba(255, 0, 110, 0.2); }
    50% { box-shadow: 0 20px 60px rgba(255, 0, 110, 0.6), 0 0 60px rgba(255, 0, 110, 0.5); }
}

.alert-card::before {
    content: '';
    position: absolute;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: linear-gradient(45deg, transparent 30%, rgba(255, 255, 255, 0.1) 50%, transparent 70%);
    animation: alertShine 3s linear infinite;
}

@keyframes alertShine {
    0% { transform: translate(-100%, -100%) rotate(45deg); }
    100% { transform: translate(100%, 100%) rotate(45deg); }
}

/* 📈 Progress Bar - شريط التقدم الأسطوري */
.progress-container {
    background: rgba(15, 23, 42, 0.6);
    border-radius: 50px;
    padding: 8px;
    margin: 2rem 0;
    overflow: hidden;
    box-shadow: 
        inset 0 4px 8px rgba(0, 0, 0, 0.4),
        0 2px 10px rgba(0, 0, 0, 0.2);
    border: 2px solid rgba(255, 255, 255, 0.05);
}

.progress-bar {
    height: 32px;
    border-radius: 50px;
    background: linear-gradient(90deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
    background-size: 200% 100%;
    box-shadow: 
        0 0 30px rgba(102, 126, 234, 0.6),
        inset 0 2px 4px rgba(255, 255, 255, 0.3);
    transition: width 1.5s cubic-bezier(0.4, 0, 0.2, 1);
    animation: progressGlow 2s ease-in-out infinite;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: bold;
    color: white;
    font-size: 1rem;
}

@keyframes progressGlow {
    0%, 100% { 
        background-position: 0% 50%;
        box-shadow: 0 0 30px rgba(102, 126, 234, 0.6);
    }
    50% { 
        background-position: 100% 50%;
        box-shadow: 0 0 50px rgba(240, 147, 251, 0.8);
    }
}

/* 🎯 الأزرار الأسطورية */
.stButton > button,
button[kind="primary"],
div[data-testid="stFormSubmitButton"] button {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    color: #ffffff !important;
    font-size: 1.1rem !important;
    font-weight: 700 !important;
    padding: 1rem 2.5rem !important;
    border: none !important;
    border-radius: 50px !important;
    cursor: pointer !important;
    box-shadow: 
        0 10px 30px rgba(102, 126, 234, 0.4),
        0 0 20px rgba(102, 126, 234, 0.2),
        inset 0 1px 0 rgba(255, 255, 255, 0.2) !important;
    transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
    position: relative !important;
    overflow: hidden !important;
    text-transform: uppercase;
    letter-spacing: 1px;
}

.stButton > button::before,
button[kind="primary"]::before {
    content: '';
    position: absolute;
    top: 50%;
    left: 50%;
    width: 0;
    height: 0;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.3);
    transform: translate(-50%, -50%);
    transition: width 0.6s ease, height 0.6s ease;
}

.stButton > button:hover,
button[kind="primary"]:hover {
    background: linear-gradient(135deg, #764ba2 0%, #667eea 100%) !important;
    transform: translateY(-5px) scale(1.02) !important;
    box-shadow: 
        0 20px 50px rgba(102, 126, 234, 0.6),
        0 0 40px rgba(102, 126, 234, 0.4),
        inset 0 1px 0 rgba(255, 255, 255, 0.3) !important;
}

.stButton > button:hover::before {
    width: 300px;
    height: 300px;
}

.stButton > button:active {
    transform: translateY(-2px) scale(0.98) !important;
}

/* 📋 الجداول الأسطورية */
.stDataFrame {
    border-radius: 16px !important;
    overflow: hidden !important;
    border: 2px solid rgba(255, 255, 255, 0.1) !important;
    background: rgba(15, 23, 42, 0.6) !important;
    backdrop-filter: blur(10px) !important;
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3) !important;
}

.stDataFrame th {
    background: linear-gradient(135deg, #667eea, #764ba2) !important;
    color: #ffffff !important;
    font-weight: bold !important;
    padding: 1rem !important;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.stDataFrame td {
    background: rgba(30, 41, 59, 0.5) !important;
    color: #e2e8f0 !important;
    padding: 0.8rem !important;
    border-bottom: 1px solid rgba(255, 255, 255, 0.05) !important;
}

.stDataFrame tr:hover td {
    background: rgba(102, 126, 234, 0.15) !important;
}

/* 🎨 التبويبات الأسطورية */
.stTabs {
    overflow-x: auto !important;
    overflow-y: visible !important;
}

.stTabs [data-baseweb="tab-list"] {
    gap: 1rem !important;
    padding-bottom: 20px !important;
    display: flex !important;
    flex-wrap: wrap !important;
    justify-content: center !important;
    background: linear-gradient(to bottom, rgba(255, 255, 255, 0.02), transparent);
    border-radius: 16px;
    padding: 1rem;
}

.stTabs [data-baseweb="tab"] {
    background: linear-gradient(135deg, rgba(102, 126, 234, 0.1), rgba(118, 75, 162, 0.05)) !important;
    backdrop-filter: blur(10px) !important;
    color: #cbd5e1 !important;
    font-weight: 600 !important;
    padding: 1rem 2rem !important;
    border-radius: 50px !important;
    border: 2px solid rgba(255, 255, 255, 0.1) !important;
    transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
    white-space: nowrap !important;
    min-width: fit-content !important;
    position: relative;
    overflow: hidden;
}

.stTabs [data-baseweb="tab"]::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.1), transparent);
    transition: left 0.5s ease;
}

.stTabs [data-baseweb="tab"]:hover {
    background: linear-gradient(135deg, rgba(102, 126, 234, 0.2), rgba(118, 75, 162, 0.15)) !important;
    color: #ffffff !important;
    border-color: var(--neon-blue) !important;
    transform: translateY(-3px) scale(1.05);
    box-shadow: 
        0 10px 30px rgba(102, 126, 234, 0.3),
        0 0 20px rgba(0, 243, 255, 0.3);
}

.stTabs [data-baseweb="tab"]:hover::before {
    left: 100%;
}

.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #667eea, #764ba2) !important;
    color: #ffffff !important;
    border: 2px solid var(--neon-blue) !important;
    font-weight: bold !important;
    box-shadow: 
        0 10px 40px rgba(102, 126, 234, 0.5),
        0 0 30px rgba(0, 243, 255, 0.4),
        inset 0 1px 0 rgba(255, 255, 255, 0.3) !important;
    transform: scale(1.05);
}

/* 🎯 حقول الإدخال الأسطورية */
.stTextInput > div > div > input,
.stSelectbox > div > div > select,
.stTextArea > div > div > textarea {
    background: rgba(15, 23, 42, 0.6) !important;
    backdrop-filter: blur(10px) !important;
    border: 2px solid rgba(255, 255, 255, 0.1) !important;
    border-radius: 12px !important;
    color: #ffffff !important;
    padding: 0.8rem !important;
    transition: all 0.3s ease !important;
}

.stTextInput > div > div > input:focus,
.stSelectbox > div > div > select:focus,
.stTextArea > div > div > textarea:focus {
    border-color: var(--neon-blue) !important;
    box-shadow: 
        0 0 20px rgba(0, 243, 255, 0.3),
        inset 0 1px 0 rgba(255, 255, 255, 0.1) !important;
    transform: translateY(-2px);
}

label {
    color: #f8fafc !important;
    font-weight: 600 !important;
    font-size: 1rem !important;
    margin-bottom: 0.5rem !important;
}

/* 🎪 الرسائل والإشعارات */
.stAlert {
    border-radius: 16px !important;
    border: 2px solid rgba(255, 255, 255, 0.1) !important;
    backdrop-filter: blur(10px) !important;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2) !important;
}

/* 📱 Responsive Design */
@media (max-width: 768px) {
    h1 { font-size: 2.5rem !important; }
    .kpi-grid { grid-template-columns: 1fr; gap: 1rem; }
    .kpi-value { font-size: 2.5rem; }
    .block-container { padding: 1rem; }
    .card { padding: 1.5rem; }
    .stTabs [data-baseweb="tab-list"] {
        flex-direction: column !important;
        align-items: stretch !important;
    }
    .stTabs [data-baseweb="tab"] {
        width: 100% !important;
        margin-bottom: 8px !important;
    }
}

/* 🌟 Scrollbar مخصص */
::-webkit-scrollbar {
    width: 12px;
    height: 12px;
}

::-webkit-scrollbar-track {
    background: rgba(15, 23, 42, 0.5);
    border-radius: 10px;
}

::-webkit-scrollbar-thumb {
    background: linear-gradient(135deg, #667eea, #764ba2);
    border-radius: 10px;
    border: 2px solid rgba(15, 23, 42, 0.5);
}

::-webkit-scrollbar-thumb:hover {
    background: linear-gradient(135deg, #764ba2, #f093fb);
}

/* 🎯 Footer الأسطوري */
.legendary-footer {
    text-align: center;
    padding: 3rem 1rem;
    margin-top: 4rem;
    background: linear-gradient(to top, rgba(15, 23, 42, 0.8), transparent);
    border-top: 2px solid rgba(255, 255, 255, 0.05);
}

.legendary-footer p {
    color: #94a3b8;
    font-size: 0.95rem;
    margin: 0.5rem 0;
}

.legendary-footer .signature {
    background: linear-gradient(135deg, #667eea, #f093fb);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-weight: bold;
    font-size: 1.1rem;
}
</style>
""", unsafe_allow_html=True)

# ============================================================
# دوال Google Sheets
# ============================================================

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SPREADSHEET_ID = "1fPaOpL_vQw5q3H1tVKUKYN76sXjIqxjqhcF3DslLBNA"

def get_google_sheets_client():
    """إنشاء اتصال بـ Google Sheets"""
    try:
        creds_dict = st.secrets["gcp_service_account"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
        service = build('sheets', 'v4', credentials=creds)
        return service.spreadsheets()
    except Exception as e:
        logger.error(f"خطأ في الاتصال بـ Google Sheets: {e}")
        return None

@st.cache_data(ttl=60)
def load_sheet_data(sheet_name):
    """تحميل البيانات من Google Sheets"""
    try:
        sheets = get_google_sheets_client()
        if not sheets:
            return pd.DataFrame()
        
        result = sheets.values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{sheet_name}!A:Z"
        ).execute()
        
        values = result.get('values', [])
        
        if not values or len(values) < 2:
            logger.warning(f"لا توجد بيانات في شيت {sheet_name}")
            return pd.DataFrame()
        
        df = pd.DataFrame(values[1:], columns=values[0])
        logger.info(f"تم تحميل {len(df)} صف من {sheet_name}")
        return df
        
    except Exception as e:
        logger.error(f"خطأ في تحميل شيت {sheet_name}: {e}")
        return pd.DataFrame()

def clear_cache_and_reload():
    """مسح الذاكرة المؤقتة"""
    st.cache_data.clear()
    logger.info("تم مسح الذاكرة المؤقتة")

def update_cell(sheet_name, cell_range, value):
    """تحديث خلية في Google Sheets"""
    try:
        sheets = get_google_sheets_client()
        if not sheets:
            return False
        
        body = {'values': [[value]]}
        sheets.values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{sheet_name}!{cell_range}",
            valueInputOption='USER_ENTERED',
            body=body
        ).execute()
        
        logger.info(f"تم تحديث {cell_range} في {sheet_name} بالقيمة: {value}")
        return True
        
    except Exception as e:
        logger.error(f"خطأ في تحديث الخلية {cell_range}: {e}")
        return False

def append_row_to_sheet(sheet_name, row_data):
    """إضافة صف جديد إلى Google Sheets"""
    try:
        sheets = get_google_sheets_client()
        if not sheets:
            return False
        
        body = {'values': [row_data]}
        sheets.values().append(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{sheet_name}!A:Z",
            valueInputOption='USER_ENTERED',
            body=body
        ).execute()
        
        logger.info(f"تم إضافة صف جديد في {sheet_name}")
        return True
        
    except Exception as e:
        logger.error(f"خطأ في إضافة صف في {sheet_name}: {e}")
        return False

def sync_student_registration_numbers():
    """ربط أرقام تسجيل الطلاب"""
    try:
        df_students = load_sheet_data("STUDENTS")
        df_memos = load_sheet_data("MEMOS")
        
        if df_students.empty or df_memos.empty:
            return False, "لا توجد بيانات في أحد الشيتات"
        
        if "الإيميل" not in df_students.columns or "البريد الإلكتروني للطالب 1" not in df_memos.columns:
            return False, "الأعمدة المطلوبة غير موجودة"
        
        if "تم التسجيل" not in df_memos.columns:
            return False, "عمود 'تم التسجيل' غير موجود في المذكرات"
        
        updates_count = 0
        
        for idx, st_row in df_students.iterrows():
            st_email = str(st_row.get("الإيميل", "")).strip().lower()
            if not st_email or st_email == "nan":
                continue
            
            memo_match = df_memos[
                (df_memos["البريد الإلكتروني للطالب 1"].astype(str).str.strip().str.lower() == st_email) &
                (df_memos["تم التسجيل"].astype(str).str.strip() == "نعم")
            ]
            
            if not memo_match.empty:
                memo_num = memo_match.iloc[0]["رقم المذكرة"]
                excel_row = idx + 2
                
                if update_cell("STUDENTS", f"S{excel_row}", memo_num):
                    if update_cell("STUDENTS", f"T{excel_row}", memo_num):
                        updates_count += 1
        
        clear_cache_and_reload()
        return True, f"تم ربط {updates_count} طالب بنجاح"
        
    except Exception as e:
        logger.error(f"خطأ في sync: {e}")
        return False, f"حدث خطأ: {str(e)}"

def send_welcome_email_to_one(prof_name):
    """إرسال إيميل ترحيب لأستاذ واحد"""
    try:
        df_prof = load_sheet_data("PROF_MEMOS")
        if df_prof.empty:
            return False, "لا توجد بيانات في PROF_MEMOS"
        
        prof_name = prof_name.strip()
        matched = df_prof[
            (df_prof["الأستاذ"].astype(str).str.strip() == prof_name) |
            (df_prof.get("الأستاذة", pd.Series()).astype(str).str.strip() == prof_name)
        ]
        
        if matched.empty:
            return False, f"لم يتم العثور على الأستاذ: {prof_name}"
        
        row = matched.iloc[0]
        email = str(row.get("البريد الإلكتروني", row.get("الإيميل", row.get("email", "")))).strip()
        username = str(row.get("إسم المستخدم", row.get("اسم المستخدم", ""))).strip()
        password = str(row.get("كلمة المرور", "")).strip()
        
        if not email or email.lower() == "nan":
            return False, f"لا يوجد إيميل للأستاذ: {prof_name}"
        
        smtp_server = st.secrets.get("smtp_server", "smtp.gmail.com")
        smtp_port = int(st.secrets.get("smtp_port", 587))
        sender_email = st.secrets.get("sender_email", "")
        sender_password = st.secrets.get("sender_password", "")
        
        if not sender_email or not sender_password:
            return False, "بيانات SMTP غير متوفرة في الإعدادات"
        
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "🎓 تفعيل حسابك في منصة المذكرات"
        msg["From"] = sender_email
        msg["To"] = email
        
        html_body = f"""
        <html dir="rtl">
        <head>
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f0f2f5; padding: 20px; }}
                .container {{ max-width: 600px; margin: auto; background: white; border-radius: 15px; overflow: hidden; box-shadow: 0 10px 40px rgba(0,0,0,0.1); }}
                .header {{ background: linear-gradient(135deg, #667eea, #764ba2); padding: 40px 20px; text-align: center; color: white; }}
                .header h1 {{ margin: 0; font-size: 28px; }}
                .content {{ padding: 40px 30px; }}
                .credentials {{ background: #f8f9fa; border-radius: 10px; padding: 20px; margin: 20px 0; border-right: 4px solid #667eea; }}
                .credentials p {{ margin: 10px 0; font-size: 16px; }}
                .credentials strong {{ color: #667eea; }}
                .button {{ display: inline-block; background: linear-gradient(135deg, #667eea, #764ba2); color: white; padding: 15px 40px; text-decoration: none; border-radius: 50px; margin: 20px 0; font-weight: bold; }}
                .footer {{ text-align: center; padding: 20px; background: #f8f9fa; color: #6c757d; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎓 مرحباً بك في منصة المذكرات</h1>
                </div>
                <div class="content">
                    <p>عزيزي/عزيزتي الأستاذ(ة) <strong>{prof_name}</strong>،</p>
                    <p>تم تفعيل حسابك بنجاح في منصة إدارة مذكرات الماستر.</p>
                    <div class="credentials">
                        <p><strong>اسم المستخدم:</strong> {username if username and username != 'nan' else 'غير متوفر'}</p>
                        <p><strong>كلمة المرور:</strong> {password if password and password != 'nan' else 'غير متوفر'}</p>
                    </div>
                    <p>يمكنك الآن الدخول إلى المنصة وإدارة المذكرات الخاصة بك.</p>
                    <center>
                        <a href="#" class="button">الدخول إلى المنصة</a>
                    </center>
                </div>
                <div class="footer">
                    <p>© 2025 منصة المذكرات - إشراف د. لخضر رفاف</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(html_body, "html"))
        
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
        
        logger.info(f"تم إرسال إيميل ترحيب إلى {prof_name} ({email})")
        return True, f"✅ تم إرسال الإيميل بنجاح إلى {prof_name}"
        
    except Exception as e:
        logger.error(f"خطأ في إرسال الإيميل: {e}")
        return False, f"❌ فشل الإرسال: {str(e)}"

def send_welcome_emails_to_all_profs():
    """إرسال إيميلات لجميع الأساتذة"""
    try:
        df_prof = load_sheet_data("PROF_MEMOS")
        if df_prof.empty:
            return 0, 0, ["لا توجد بيانات في PROF_MEMOS"]
        
        sent_count = 0
        failed_count = 0
        logs = []
        
        for idx, row in df_prof.iterrows():
            prof_name = str(row.get("الأستاذ", row.get("الأستاذة", ""))).strip()
            if not prof_name or prof_name.lower() == "nan":
                continue
            
            success, msg = send_welcome_email_to_one(prof_name)
            if success:
                sent_count += 1
                logs.append(f"✅ {prof_name}: تم الإرسال")
            else:
                failed_count += 1
                logs.append(f"❌ {prof_name}: {msg}")
            
            time.sleep(2)
        
        return sent_count, failed_count, logs
        
    except Exception as e:
        logger.error(f"خطأ في الإرسال الجماعي: {e}")
        return 0, 0, [f"خطأ: {str(e)}"]

# ============================================================
# تحميل البيانات
# ============================================================

try:
    df_memos = load_sheet_data("MEMOS")
    df_students = load_sheet_data("STUDENTS")
    df_requests = load_sheet_data("REQUESTS")
    df_prof_memos = load_sheet_data("PROF_MEMOS")
except Exception as e:
    logger.error(f"خطأ في تحميل البيانات: {e}")
    df_memos = pd.DataFrame()
    df_students = pd.DataFrame()
    df_requests = pd.DataFrame()
    df_prof_memos = pd.DataFrame()

# ============================================================
# الواجهة الرئيسية - LEGENDARY UI
# ============================================================

# 🎨 العنوان الأسطوري
st.markdown("""
<div style="text-align: center; margin-bottom: 3rem;">
    <h1 style="margin-bottom: 0.5rem;">
        🎓 منصة إدارة مذكرات الماستر
    </h1>
    <p style="color: #94a3b8; font-size: 1.2rem; margin-top: 1rem;">
        نظام إدارة متطور وشامل لتسجيل ومتابعة مذكرات التخرج
    </p>
</div>
""", unsafe_allow_html=True)

# ============================================================
# حساب الإحصائيات مع معالجة الأخطاء
# ============================================================

total_students = len(df_students) if not df_students.empty else 0
total_profs = len(df_prof_memos) if not df_prof_memos.empty else 0
total_memos = len(df_memos) if not df_memos.empty else 0

# معالجة آمنة للأعمدة
registered_memos = 0
available_memos = 0
registered_students = 0
unregistered_students = 0

if not df_memos.empty and "تم التسجيل" in df_memos.columns:
    try:
        registered_memos = (df_memos["تم التسجيل"].astype(str).str.strip() == "نعم").sum()
        available_memos = total_memos - registered_memos
    except:
        pass

if not df_students.empty and "رقم المذكرة" in df_students.columns:
    try:
        memo_col = df_students["رقم المذكرة"].astype(str).str.strip()
        registered_students = (memo_col != "").sum()
        unregistered_students = (memo_col == "").sum()
    except:
        pass

# 🎴 KPI Cards الأسطورية
st.markdown('<div class="kpi-grid">', unsafe_allow_html=True)

kpi_data = [
    {"icon": "fas fa-users", "value": total_students, "label": "إجمالي الطلاب"},
    {"icon": "fas fa-chalkboard-teacher", "value": total_profs, "label": "عدد الأساتذة"},
    {"icon": "fas fa-book", "value": total_memos, "label": "إجمالي المذكرات"},
    {"icon": "fas fa-check-circle", "value": registered_memos, "label": "مذكرات مسجلة"},
    {"icon": "fas fa-hourglass-half", "value": available_memos, "label": "مذكرات متاحة"},
    {"icon": "fas fa-user-check", "value": registered_students, "label": "طلاب مسجلين"},
    {"icon": "fas fa-user-clock", "value": unregistered_students, "label": "طلاب غير مسجلين"},
]

for kpi in kpi_data:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-icon">
            <i class="{kpi['icon']}"></i>
        </div>
        <div class="kpi-value">{kpi['value']}</div>
        <div class="kpi-label">{kpi['label']}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# 🚨 تنبيه الموعد النهائي
now = datetime.now()
if now < REGISTRATION_DEADLINE:
    days_left = (REGISTRATION_DEADLINE - now).days
    st.markdown(f"""
    <div class="alert-card">
        <i class="fas fa-exclamation-triangle" style="font-size: 2rem; margin-bottom: 1rem;"></i>
        <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">⏰ الموعد النهائي للتسجيل</div>
        <div style="font-size: 1.2rem;">متبقي {days_left} يوم</div>
        <div style="font-size: 1rem; margin-top: 1rem; opacity: 0.9;">
            {REGISTRATION_DEADLINE.strftime("%Y/%m/%d - %H:%M")}
        </div>
    </div>
    """, unsafe_allow_html=True)

# 📈 شريط التقدم الأسطوري
if total_memos > 0:
    progress = (registered_memos / total_memos) * 100
    st.markdown(f"""
    <div style="margin: 3rem 0;">
        <h3 style="text-align: center; margin-bottom: 1.5rem;">
            <i class="fas fa-chart-line"></i> نسبة إنجاز التسجيلات
        </h3>
        <div class="progress-container">
            <div class="progress-bar" style="width: {progress}%;">
                {progress:.1f}%
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ============================================================
# 📑 التبويبات الأسطورية
# ============================================================

tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "📚 المذكرات",
    "👥 الطلاب",
    "👨‍🏫 الأساتذة",
    "📊 التقارير",
    "🔄 التحديث",
    "📝 الطلبات",
    "📧 الإيميلات"
])

# ============================================================
# TAB 1: المذكرات
# ============================================================
with tab1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### 📚 جدول المذكرات")
    
    if not df_memos.empty:
        filter_status = st.selectbox(
            "🔍 تصفية حسب الحالة:",
            ["الكل", "مسجلة", "متاحة"],
            key="memo_filter"
        )
        
        display_memos = df_memos.copy()
        
        if "تم التسجيل" in df_memos.columns:
            if filter_status == "مسجلة":
                display_memos = df_memos[df_memos["تم التسجيل"].astype(str).str.strip() == "نعم"]
            elif filter_status == "متاحة":
                display_memos = df_memos[df_memos["تم التسجيل"].astype(str).str.strip() != "نعم"]
        
        st.dataframe(display_memos, use_container_width=True, height=500)
    else:
        st.info("لا توجد بيانات متاحة")
    
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# TAB 2: الطلاب
# ============================================================
with tab2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### 👥 قائمة الطلاب")
    
    if not df_students.empty:
        search_query = st.text_input("🔍 البحث عن طالب (الاسم أو اللقب):", key="student_search")
        
        if search_query:
            name_columns = [col for col in df_students.columns if any(term in col.lower() for term in ['اسم', 'لقب', 'إسم'])]
            if name_columns:
                mask = df_students[name_columns].astype(str).apply(
                    lambda x: x.str.contains(search_query, case=False, na=False)
                ).any(axis=1)
                filtered_students = df_students[mask]
            else:
                filtered_students = df_students
            st.dataframe(filtered_students, use_container_width=True, height=500)
        else:
            st.dataframe(df_students, use_container_width=True, height=500)
    else:
        st.info("لا توجد بيانات متاحة")
    
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# TAB 3: الأساتذة
# ============================================================
with tab3:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### 👨‍🏫 توزيع الأساتذة")
    
    if not df_memos.empty and "الأستاذ" in df_memos.columns:
        profs_list = sorted(df_memos["الأستاذ"].dropna().unique())
        selected_prof = st.selectbox("اختر أستاذاً:", ["الكل"] + profs_list, key="prof_select")
        
        if selected_prof != "الكل":
            prof_memos = df_memos[df_memos["الأستاذ"].astype(str).str.strip() == selected_prof.strip()]
            st.dataframe(prof_memos, use_container_width=True, height=400)
        else:
            if all(col in df_memos.columns for col in ["الأستاذ", "رقم المذكرة", "تم التسجيل"]):
                summary_df = df_memos.groupby("الأستاذ").agg(
                    total=("رقم المذكرة", "count"),
                    registered=("تم التسجيل", lambda x: (x.astype(str).str.strip() == "نعم").sum())
                ).reset_index()
                summary_df["المتاحة"] = summary_df["total"] - summary_df["registered"]
                summary_df = summary_df.rename(columns={"total": "الإجمالي", "registered": "المسجلة"})
                st.dataframe(summary_df, use_container_width=True)
    else:
        st.info("لا توجد بيانات متاحة")
    
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# TAB 4: التقارير
# ============================================================
with tab4:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### 📊 التحليل الإحصائي")
    
    if not df_memos.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("##### 📈 توزيع المذكرات حسب التخصص")
            if "التخصص" in df_memos.columns:
                spec_dist = df_memos.groupby("التخصص").size()
                st.bar_chart(spec_dist)
        
        with col2:
            st.markdown("##### ✅ حالة التسجيل حسب التخصص")
            if "التخصص" in df_memos.columns and "تم التسجيل" in df_memos.columns:
                reg_status = df_memos.groupby("التخصص")["تم التسجيل"].apply(
                    lambda x: (x.astype(str).str.strip() == "نعم").sum()
                )
                st.bar_chart(reg_status)
        
        st.markdown("---")
        
        st.markdown("##### 🎯 نسب التقدم العامة")
        
        if "تم التسجيل" in df_memos.columns:
            progress_df = df_memos[df_memos["تم التسجيل"].astype(str).str.strip() == "نعم"].copy()
            
            if not progress_df.empty and "نسبة التقدم" in progress_df.columns:
                progress_df["نسبة التقدم"] = progress_df["نسبة التقدم"].apply(
                    lambda x: int(x) if str(x).isdigit() else 0
                )
                avg_progress = progress_df["نسبة التقدم"].mean()
                
                st.metric("📊 متوسط نسبة الإنجاز", f"{avg_progress:.1f}%")
                
                st.markdown(f"""
                <div class="progress-container">
                    <div class="progress-bar" style="width: {avg_progress}%;">
                        {avg_progress:.1f}%
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("##### 🆕 آخر التسجيلات")
            recent_registrations = progress_df.tail(5)
            display_cols = ["رقم المذكرة", "عنوان المذكرة", "الأستاذ", "تاريخ التسجيل"]
            display_cols = [col for col in display_cols if col in recent_registrations.columns]
            if display_cols:
                st.dataframe(recent_registrations[display_cols], use_container_width=True, hide_index=True)
    else:
        st.info("لا توجد بيانات متاحة")
    
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# TAB 5: التحديث
# ============================================================
with tab5:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### 🔄 تحديث البيانات والربط")
    
    st.warning("⚠️ استخدم هذا الزر لربط أرقام التسجيل (أعمدة S و T) لأول مرة أو لإصلاح الأخطاء.")
    
    if st.button("🔄 بدء عملية الربط (Sync)", type="primary", key="sync_btn"):
        with st.spinner("⏳ جاري المعالجة... قد يستغرق وقتاً"):
            success, message = sync_student_registration_numbers()
            if success:
                st.success(message)
                clear_cache_and_reload()
                st.rerun()
            else:
                st.info(message)
    
    st.markdown("---")
    
    if st.button("♻️ تحديث البيانات من Google Sheets", key="refresh_btn"):
        with st.spinner("⏳ جاري التحديث..."):
            clear_cache_and_reload()
            st.success("✅ تم التحديث بنجاح!")
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# TAB 6: الطلبات
# ============================================================
with tab6:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### 📝 سجل الطلبات الواردة")
    
    if not df_requests.empty:
        st.dataframe(df_requests, use_container_width=True, height=500)
    else:
        st.info("لا توجد طلبات متاحة")
    
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# TAB 7: الإيميلات
# ============================================================
with tab7:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### 📧 إرسال رسائل الترحيب للأساتذة")
    
    if not df_prof_memos.empty:
        send_mode = st.radio(
            "اختر نوع العملية:",
            ["📩 إرسال لأستاذ محدد", "🚀 إرسال لجميع الأساتذة"],
            horizontal=True,
            key="send_mode"
        )
        
        st.markdown("---")
        
        # إرسال فردي
        if send_mode == "📩 إرسال لأستاذ محدد":
            st.info("📝 أدخل بيانات الأستاذ لإرسال رسالة التفعيل له فقط.")
            
            prof_list = df_prof_memos["الأستاذ"].astype(str).dropna().unique().tolist()
            if "الأستاذة" in df_prof_memos.columns:
                prof_list.extend(df_prof_memos["الأستاذة"].astype(str).dropna().unique().tolist())
            
            prof_list = list(set([p for p in prof_list if p.strip() and p.strip().lower() != "nan"]))
            prof_list.sort()
            
            selected_prof = st.selectbox("اختر الأستاذ من القائمة:", prof_list, index=None, key="single_prof_select")
            
            col_s1, col_s2 = st.columns([1, 3])
            with col_s1:
                send_single_btn = st.button("📤 إرسال الآن", type="secondary", use_container_width=True, key="send_single")
            
            if send_single_btn and selected_prof:
                with st.spinner("⏳ جاري الإرسال..."):
                    success, msg = send_welcome_email_to_one(selected_prof)
                    if success:
                        st.success(msg)
                        st.balloons()
                    else:
                        st.error(msg)
            elif send_single_btn and not selected_prof:
                st.warning("⚠️ يرجى اختيار اسم أستاذ من القائمة.")
        
        # إرسال جماعي
        elif send_mode == "🚀 إرسال لجميع الأساتذة":
            st.info("📢 تقوم هذه الأداة بإرسال إيميل يحتوي على بيانات الدخول لجميع الأساتذة المسجلين.")
            st.write(f"**عدد الأساتذة المستهدفين:** {len(df_prof_memos)}")
            
            with st.expander("👁️ عرض قائمة الأساتذة المستهدفين"):
                cols_available = df_prof_memos.columns.tolist()
                target_cols = ["الأستاذ", "الأستاذة", "إسم المستخدم", "اسم المستخدم", "كلمة المرور", "البريد الإلكتروني"]
                cols_to_display = [col for col in target_cols if col in cols_available]
                if not cols_to_display:
                    cols_to_display = cols_available[:3]
                st.dataframe(df_prof_memos[cols_to_display].head(20))
            
            col_send, col_space = st.columns([1, 3])
            with col_send:
                if st.button("🚀 بدء عملية الإرسال للجميع", type="primary", key="send_all"):
                    with st.spinner("⏳ جاري الإرسال... يرجى الانتظار"):
                        sent, failed, logs = send_welcome_emails_to_all_profs()
                        
                        st.markdown("---")
                        st.success(f"✅ تم الانتهاء! تم الإرسال بنجاح لـ **{sent}** أستاذ.")
                        if failed > 0:
                            st.error(f"❌ فشل الإرسال لـ **{failed}** أستاذ.")
                        
                        with st.expander("📋 سجل العمليات (Logs)", expanded=True):
                            for log in logs:
                                st.text(log)
    else:
        st.info("لا توجد بيانات أساتذة متاحة")
    
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# 🎭 Footer الأسطوري
# ============================================================
st.markdown("""
<div class="legendary-footer">
    <p style="font-size: 1.1rem; margin-bottom: 1rem;">
        <i class="fas fa-graduation-cap"></i> منصة إدارة مذكرات الماستر
    </p>
    <p class="signature">
        إشراف: الدكتور لخضر رفاف
    </p>
    <p style="margin-top: 1.5rem; font-size: 0.9rem;">
        © 2025 جميع الحقوق محفوظة
    </p>
</div>
""", unsafe_allow_html=True)
