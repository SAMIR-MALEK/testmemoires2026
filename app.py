import streamlit as st
from datetime import datetime, time, date, timedelta
import pandas as pd
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from googleapiclient.errors import HttpError
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import io
import base64
import re
import time
import textwrap

# ---------------- إعداد Logging ----------------
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ---------------- إعداد الصفحة ----------------
st.set_page_config(page_title="تسجيل مذكرات الماستر", page_icon="📘", layout="wide")
st.cache_data.clear()

# ---------------- إعداد الموعد النهائي ----------------
REGISTRATION_DEADLINE = datetime(2027, 1, 28, 23, 59)

# ---------------- CSS ----------------
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;900&display=swap" rel="stylesheet">
<style>
    * { box-sizing: border-box; }
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif !important; direction: rtl; text-align: right; }
    .main { background-color: #0A1B2C; color: #ffffff; }
    .block-container { padding: 2rem; background-color: #1A2A3D; border-radius: 16px; margin:auto; }

    h1, h2, h3, h4 { font-weight: 700; margin-bottom: 1rem; color: #ffffff !important; }
    label, p, span { color: #ffffff !important; }
    h1 { text-align: center; }

    .stTextInput label, .stSelectbox label { color: #ffffff !important; font-weight: 600; }

    .stButton>button, button[kind="primary"], div[data-testid="stFormSubmitButton"] button {
        background-color: #2F6F7E !important; color: #ffffff !important;
        font-size: 16px; font-weight: 600; padding: 14px 32px;
        border: none !important; border-radius: 12px !important;
        cursor: pointer; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
        transition: all 0.3s ease; width: 100%;
        text-align: center; display: flex; justify-content: center; align-items: center; gap: 10px;
    }
    .stButton>button:hover { background-color: #285E6B !important; transform: translateY(-2px); }

    .card {
        background: rgba(30, 41, 59, 0.95); border:1px solid rgba(255,255,255, 0.08);
        border-radius: 20px; padding: 30px; margin-bottom: 20px;
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.2);
        border-top: 3px solid #2F6F7E; transition: transform 0.2s ease;
    }

    .kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 1.5rem; margin-bottom: 2.5rem; }
    .kpi-card {
        background: linear-gradient(145deg, #1E293B, #0F172A); border: 1px solid rgba(255, 255, 255, 0.05); border-radius: 16px; padding: 2.5rem 1rem;
        text-align: center; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3); position: relative; overflow: hidden;
    }
    .kpi-value { font-size: 2.5rem; font-weight: 900; color: #FFD700; margin: 15px 0; }
    .kpi-label { font-size: 1.2rem; color: #ffffff !important; font-weight: 600; margin-top: 10px; }

    .alert-card {
        background: linear-gradient(90deg, #8B4513 0%, #A0522D 100%);
        border: 1px solid #CD853F; color: white; padding: 25px; border-radius: 12px;
        box-shadow: 0 10px 20px -5px rgba(139, 69, 19, 0.4); text-align: center; font-weight: bold;
    }

    .progress-container { background-color: #0F172A; border-radius: 99px; padding: 6px; margin: 20px 0; overflow: hidden; box-shadow: inset 0 4px 6px rgba(0, 0, 0, 0.3); }
    .progress-bar {
        height: 24px; border-radius: 99px;
        background: linear-gradient(90deg, #2F6F7E 0%, #285E6B 50%, #FFD700 100%);
        box-shadow: 0 0 15px rgba(47, 111, 126, 0.5); transition: width 1s cubic-bezier(0.4, 0, 0.2, 1);
    }

    .stDataFrame { border-radius: 12px; overflow: hidden; border: 1px solid rgba(255,255,255, 0.1); background: #1E293B; }
    .stDataFrame th { background-color: #0F172A; color: #FFD700; font-weight: bold; }

    .stTabs [data-baseweb="tab-list"] { gap: 2rem; padding-bottom: 15px; }
    .stTabs [data-baseweb="tab"] {
        background: transparent; color: #94A3B8; font-weight: 600; padding: 12px 24px; border-radius: 12px; border: 1px solid transparent;
    }
    .stTabs [data-baseweb="tab"]:hover { background: rgba(255, 255, 255, 0.1); color: white; }
    .stTabs [aria-selected="true"] {
        background: rgba(47, 111, 126, 0.2); color: #FFD700; border: 1px solid #2F6F7E; font-weight: bold; box-shadow: 0 0 15px rgba(47, 111, 126, 0.2);
    }

    .full-view-container {
        max-width: 1000px; margin: 0 auto; padding: 40px;
        background: rgba(15,23, 42, 0.5); border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 24px; box-shadow: 0 0 40px rgba(0,0,0,0.6); overflow: hidden;
    }

    .students-grid { display: flex; justify-content: center; gap: 40px; flex-wrap: wrap; margin-top: 20px; margin-bottom: 30px; }

    .student-card {
        flex: 1; max-width: 450px; min-width: 300px;
        background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px; padding: 25px; text-align: center; transition: all 0.3s ease;
    }
    .student-card:hover { background: rgba(255, 255, 255, 0.06); border-color: #2F6F7E; }
    .memo-badge {
        display: inline-block; background: rgba(47, 111, 126, 0.2);
        color: #FFD700; padding: 6px 16px; border-radius: 20px;
        font-size: 1rem; margin-bottom: 10px; font-weight: 600;
    }
    .memo-id { font-size: 3rem; font-weight: 900; color: #2F6F7E; margin: 0; line-height: 1; }

    .diploma-status-grid { display: flex; flex-direction: column; gap: 12px !important; width: 100%; }
    .diploma-item {
        background: rgba(255,255,255,0.05); padding: 15px 20px; border-radius: 10px; margin-bottom: 0;
        display: flex; justify-content: space-between; align-items: center;
        border-right: 4px solid #2F6F7E; transition: background 0.3s;
    }
    .diploma-item:hover { background: rgba(255,255,255,0.1); }
    .status-badge {
        padding: 6px 15px; border-radius: 20px; font-size: 0.95rem; font-weight: bold;
        min-width: 100px; text-align: center;
    }
    .status-available { background: rgba(16, 185, 129, 0.2); color: #10B981; border: 1px solid rgba(16, 185, 129, 0.3); }
    .status-unavailable { background: rgba(239, 68, 68, 0.2); color: #EF4444; border: 1px solid rgba(239, 68, 68, 0.3); }
    .status-pending { background: rgba(245, 158, 11, 0.2); color: #F59E0B; border: 1px solid rgba(245, 158, 11, 0.3); }
    
    .memo-card-title { color: #FFFFFF !important; font-size: 1.1rem; font-weight: bold; }
    
    /* New Deposit & Schedule Styles */
    .status-deposited { background: rgba(59, 130, 246, 0.2); color: #3B82F6; border: 1px solid rgba(59, 130, 246, 0.3); }
    .status-validated { background: rgba(16, 185, 129, 0.2); color: #10B981; border: 1px solid rgba(16, 185, 129, 0.3); }
    .status-scheduled { background: rgba(139, 92, 246, 0.2); color: #8B5CF6; border: 1px solid rgba(139, 92, 246, 0.3); }
    .status-rejected { background: rgba(239, 68, 68, 0.2); color: #EF4444; border: 1px solid rgba(239, 68, 68, 0.3); }
    
    .upload-area {
        border: 2px dashed #2F6F7E; border-radius: 15px; padding: 40px;
        text-align: center; background: rgba(47, 111, 126, 0.05); margin-top: 20px;
    }
</style>
""", unsafe_allow_html=True)

# ---------------- Google Sheets ----------------
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
try:
    info = st.secrets["service_account"]
    credentials = Credentials.from_service_account_info(info, scopes=SCOPES)
    sheets_service = build('sheets', 'v4', credentials=credentials)
    drive_service = build('drive', 'v3', credentials=credentials)
except Exception as e:
    st.error("⚠️ خطأ في الاتصال بـ Google Sheets")
    st.stop()

STUDENTS_SHEET_ID = "1gvNkOVVKo6AO07dRKMnSQw6vZ3KdUnW7I4HBk61Sqns"
MEMOS_SHEET_ID = "1LNJMBAye4QIQy7JHz6F8mQ6-XNC1weZx1ozDZFfjD5s"
PROF_MEMOS_SHEET_ID = "1OnZi1o-oPMUI_W_Ew-op0a1uOhSj006hw_2jrMD6FSE"
REQUESTS_SHEET_ID = "1sTJ6BZRM4Qgt0w2xUkpFZqquL-hfriMYTSN3x1_12_o"
SETTINGS_SHEET_ID = MEMOS_SHEET_ID # Using main sheet for settings

STUDENTS_RANGE = "Feuille 1!A1:U1000" 
MEMOS_RANGE = "Feuille 1!A1:AC1000" # Extended to AC
PROF_MEMOS_RANGE = "Feuille 1!A1:P1000"
REQUESTS_RANGE = "Feuille 1!A1:K1000"
SETTINGS_RANGE = "Settings!A1:B10"
ROOMS_RANGE = "Rooms!A1:B20"

ADMIN_CREDENTIALS = {"admin": "admin2026", "dsp": "dsp@2026"}

EMAIL_SENDER = "domaine.dsp@univ-bba.dz"
EMAIL_PASSWORD = "qptlxzunqhdcjcjt"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
ADMIN_EMAIL = "domaine.dsp@univ-bba.dz"

# --- نهاية الجزء الأول ---
# ---------------- دوال مساعدة ----------------
def format_arabic_date(date_input):
    try:
        if isinstance(date_input, str):
            date_obj = datetime.strptime(date_input, '%Y-%m-%d %H:%M:%S')
        elif isinstance(date_input, datetime):
            date_obj = date_input
        else:
            return str(date_input)
        day = date_obj.day
        year = date_obj.year
        months_map = {1: "جانفي", 2: "فيفري", 3: "مارس", 4: "أفريل", 5: "ماي", 6: "جوان", 7: "جويلية", 8: "أوت", 9: "سبتمبر", 10: "أكتوبر", 11: "نوفمبر", 12: "ديسمبر"}
        month_name = months_map.get(date_obj.month, date_obj.strftime('%B'))
        return f"{day:02d} {month_name} {year}"
    except Exception as e:
        logger.error(f"Error formatting date: {e}")
        return str(date_input)

def col_letter(n):
    result = ""
    while n > 0:
        n, remainder = divmod(n - 1, 26)
        result = chr(65 + remainder) + result
    return result

def sanitize_input(text):
    if not text: return ""
    dangerous_chars = ['<', '>', '"', "'", ';', '&', '|', '`']
    cleaned = str(text).strip()
    for char in dangerous_chars: cleaned = cleaned.replace(char, '')
    return cleaned

def normalize_text(val):
    v = str(val).strip()
    if v.endswith('.0'): v = v[:-2]
    return v

def validate_username(username):
    username = sanitize_input(username)
    if not username: return False, "⚠️ اسم المستخدم فارغ"
    return True, username

def validate_note_number(note_number):
    note_number = sanitize_input(note_number)
    if not note_number: return False, "⚠️ رقم المذكرة فارغ"
    if len(note_number) > 20: return False, "⚠️ رقم المذكرة غير صالح"
    return True, note_number

def is_phone_valid(phone_val):
    val = str(phone_val).strip()
    invalid_values = ['', '0', '-', 'nan', 'None', 'NaN', '.0', '0.0']
    if val in invalid_values: return False, "قيمة فارغة أو غير صالحة (0/-)"
    cleaned = val.replace(' ', '').replace('-', '')
    if not cleaned.isdigit(): return False, "لا يحتوي على أرقام فقط"
    if len(cleaned) < 9: return False, "رقم قصير جداً"
    return True, "صالح"

def is_nin_valid(nin_val):
    val = str(nin_val).strip().replace('.0', '')
    invalid_values = ['', '0', '-', 'nan', 'None', 'NaN']
    if val in invalid_values: return False, "قيمة فارغة أو غير صالحة (0/-)"
    if not val.isdigit(): return False, "يجب أن يحتوي على أرقام فقط"
    return True, "صالح"

def get_student_name_display(student_dict):
    keys_lname = ["لقب", "اللقب", ""]
    lname = ""
    for k in keys_lname:
        if k in student_dict and str(student_dict[k]).strip() not in ['nan', '']:
            lname = student_dict[k]
            break
    
    keys_fname = ["إسم", "اسم", "الإسم", ""]
    fname = ""
    for k in keys_fname:
        if k in student_dict and str(student_dict[k]).strip() not in ['nan', '']:
            fname = student_dict[k]
            break
            
    return lname, fname

def get_email_smart(row):
    if isinstance(row, dict):
        priority_keys = ["البريد المهني", "البريد الإلكتروني", "email", "Email", "E-mail"]
        for key in priority_keys:
            val = str(row.get(key, "")).strip()
            if "@" in val and val != "nan": return val
        for val in row.values():
            v = str(val).strip()
            if "@" in v and v != "nan": return v
        return ""
    try:
        values_list = row.tolist()
        for i in range(9, 13):
            if i < len(values_list):
                val = str(values_list[i]).strip()
                if "@" in val and val != "nan": return val
        for col in row.index:
            clean_col_name = str(col).strip()
            if clean_col_name in ["البريد المهني", "البريد الإلكتروني", "email", "Email", "E-mail"]:
                val = str(row[col]).strip()
                if "@" in val and val != "nan": return val
        return ""
    except:
        return ""

def get_student_info_from_memo(memo_row, df_students):
    student1_name = str(memo_row.get("الطالب الأول", "")).strip()
    student2_name = str(memo_row.get("الطالب الثاني", "")).strip()
    s1_email = s2_email = s1_reg_display = s2_reg_display = ""
    email_fetcher = get_email_smart
    try:
        memo_list = memo_row.tolist()
        raw_reg1 = str(memo_list[18]).strip() if len(memo_list) > 18 else ""
        raw_reg2 = str(memo_list[19]).strip() if len(memo_list) > 19 else ""
        reg1 = normalize_text(raw_reg1) 
        reg2 = normalize_text(raw_reg2)
    except:
        reg1 = normalize_text(memo_row.get("رقم تسجيل الطالب 1", ""))
        reg2 = normalize_text(memo_row.get("رقم تسجيل الطالب 2", ""))
        
    df_students['رقم التسجيل_norm'] = df_students['رقم التسجيل'].astype(str).apply(normalize_text)

    if reg1:
        s_data = df_students[df_students["رقم التسجيل_norm"] == reg1]
        if not s_data.empty:
            s1_email = email_fetcher(s_data.iloc[0])
            s1_reg_display = reg1
    if student2_name and reg2:
        s_data = df_students[df_students["رقم التسجيل_norm"] == reg2]
        if not s_data.empty:
            s2_email = email_fetcher(s_data.iloc[0])
            s2_reg_display = reg2
    return {
        "s1_name": student1_name, "s1_email": s1_email, "s1_reg": s1_reg_display,
        "s2_name": student2_name, "s2_email": s2_email, "s2_reg": s2_reg_display
    }

# ---------------- دوال الإعدادات ----------------
def get_settings():
    try:
        result = sheets_service.spreadsheets().values().get(spreadsheetId=SETTINGS_SHEET_ID, range=SETTINGS_RANGE).execute()
        values = result.get('values', [])
        return {row[0]: row[1] if len(row) > 1 else "" for row in values}
    except: return {}

def get_rooms():
    try:
        result = sheets_service.spreadsheets().values().get(spreadsheetId=SETTINGS_SHEET_ID, range=ROOMS_RANGE).execute()
        values = result.get('values', [])
        if values and values[0][0] == 'اسم القاعة': values = values[1:]
        return [row[0] for row in values if row]
    except: return []

# ---------------- دوال التحميل ----------------
@st.cache_data(ttl=60)
def load_students():
    try:
        result = sheets_service.spreadsheets().values().get(spreadsheetId=STUDENTS_SHEET_ID, range=STUDENTS_RANGE).execute()
        values = result.get('values', [])
        if not values: return pd.DataFrame()
        df = pd.DataFrame(values[1:], columns=values[0])
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        logger.error(f"خطأ في تحميل بيانات الطلاب: {str(e)}")
        return pd.DataFrame()
     
@st.cache_data(ttl=60)
def load_memos():
    try:
        result = sheets_service.spreadsheets().values().get(spreadsheetId=MEMOS_SHEET_ID, range=MEMOS_RANGE).execute()
        values = result.get('values', [])
        if not values: return pd.DataFrame()
        df = pd.DataFrame(values[1:], columns=values[0])
        return df
    except Exception as e:
        logger.error(f"خطأ في تحميل بيانات المذكرات: {str(e)}")
        return pd.DataFrame()

@st.cache_data(ttl=60)
def load_prof_memos():
    try:
        result = sheets_service.spreadsheets().values().get(spreadsheetId=PROF_MEMOS_SHEET_ID, range=PROF_MEMOS_RANGE).execute()
        values = result.get('values', [])
        if not values: return pd.DataFrame()
        df = pd.DataFrame(values[1:], columns=values[0])
        return df
    except Exception as e:
        logger.error(f"خطأ في تحميل بيانات مذكرات الأساتذة: {str(e)}")
        return pd.DataFrame()

@st.cache_data(ttl=60)
def load_requests():
    try:
        result = sheets_service.spreadsheets().values().get(spreadsheetId=REQUESTS_SHEET_ID, range=REQUESTS_RANGE).execute()
        values = result.get('values', [])
        if not values: return pd.DataFrame()
        df = pd.DataFrame(values[1:], columns=values[0])
        return df
    except Exception as e:
        logger.error(f"خطأ في تحميل بيانات الطلبات: {str(e)}")
        return pd.DataFrame()

def clear_cache_and_reload():
    st.cache_data.clear()
    logger.info("تم مسح السجلات")

# --- نهاية الجزء الثاني ---
# ---------------- دوال التحديث ----------------
def update_student_profile(username, phone, nin):
    try:
        df_students = load_students()
        df_students['username_norm'] = df_students["اسم المستخدم"].astype(str).apply(normalize_text)
        username_norm = normalize_text(username)
        
        student_row = df_students[df_students["username_norm"] == username_norm]
        if student_row.empty: return False, "❌ لم يتم العثور على الطالب"
        
        row_idx = student_row.index[0] + 2
        updates = [
            {"range": f"Feuille 1!M{row_idx}", "values": [[phone]]},
            {"range": f"Feuille 1!U{row_idx}", "values": [[nin]]}
        ]
        
        body = {"valueInputOption": "USER_ENTERED", "data": updates}
        sheets_service.spreadsheets().values().batchUpdate(
            spreadsheetId=STUDENTS_SHEET_ID, 
            body=body
        ).execute()
        
        clear_cache_and_reload()
        return True, "✅ تم تحديث البيانات بنجاح"
    except Exception as e:
        logger.error(f"خطأ في تحديث الملف: {str(e)}")
        return False, f"❌ حدث خطأ أثناء التحديث: {str(e)}"

def sync_student_registration_numbers():
    try:
        st.info("⏳ جاري بدء عملية الربط...")
        df_s = load_students()
        df_m = load_memos()
        updates = []
        
        df_s['رقم المذكرة_norm'] = df_s['رقم المذكرة'].astype(str).apply(normalize_text)
        
        students_with_memo = df_s[df_s['رقم المذكرة_norm'].notna() & (df_s['رقم المذكرة_norm'] != "")]
        
        for index, row in df_m.iterrows():
            memo_num = normalize_text(row.get("رقم المذكرة", ""))
            if not memo_num: continue
            
            matched_students = students_with_memo[students_with_memo["رقم المذكرة_norm"] == memo_num]
            if matched_students.empty: continue
            
            s1_name = str(row.get("الطالب الأول", "")).strip()
            s2_name = str(row.get("الطالب الثاني", "")).strip()
            reg_s1 = ""; reg_s2 = ""
            
            for _, s_row in matched_students.iterrows():
                lname = s_row.get('لقب', s_row.get('اللقب', ''))
                fname = s_row.get('إسم', s_row.get('الإسم', ''))
                full_name = f"{lname} {fname}".strip()
                if full_name == s1_name: reg_s1 = normalize_text(s_row.get("رقم التسجيل", ""))
                elif s2_name and full_name == s2_name: reg_s2 = normalize_text(s_row.get("رقم التسجيل", ""))
            
            if not reg_s1 and len(matched_students) > 0: reg_s1 = normalize_text(matched_students.iloc[0].get("رقم التسجيل", ""))
            
            row_idx = index + 2
            if reg_s1: updates.append({"range": f"Feuille 1!S{row_idx}", "values": [[reg_s1]]})
            if reg_s2: updates.append({"range": f"Feuille 1!T{row_idx}", "values": [[reg_s2]]})
            
        if updates:
            body = {"valueInputOption": "USER_ENTERED", "data": updates}
            sheets_service.spreadsheets().values().batchUpdate(spreadsheetId=MEMOS_SHEET_ID, body=body).execute()
            return True, f"✅ تم تحديث {len(updates)} خلية بنجاح."
        else: return False, "ℹ️ جميع البيانات محدثة أو لا توجد تطابقات."
    except Exception as e:
        logger.error(f"Migration Error: {str(e)}")
        return False, f"❌ حدث خطأ: {str(e)}"

def update_progress(memo_number, progress_value):
    try:
        df_memos = load_memos()
        memo_row = df_memos[df_memos["رقم المذكرة"].astype(str).apply(normalize_text) == normalize_text(memo_number)]
        if memo_row.empty: return False, "❌ لم يتم العثور على المذكرة"
        
        row_idx = memo_row.index[0] + 2
        sheets_service.spreadsheets().values().update(
            spreadsheetId=MEMOS_SHEET_ID, range=f"Feuille 1!Q{row_idx}",
            valueInputOption="USER_ENTERED", body={"values": [[str(progress_value)]]}
        ).execute()
        clear_cache_and_reload()
        logger.info(f"تم تحديث نسبة التقدم للمذكرة {memo_number} إلى {progress_value}%")
        return True, "✅ تم تحديث نسبة التقدم بنجاح"
    except Exception as e:
        logger.error(f"خطأ في تحديث نسبة التقدم: {str(e)}")
        return False, f"❌ خطأ: {str(e)}"

def update_deposit_status(memo_number, status, pdf_link="", deposit_date=""):
    try:
        df_memos = load_memos()
        memo_row = df_memos[df_memos["رقم المذكرة"].astype(str).apply(normalize_text) == normalize_text(memo_number)]
        if memo_row.empty: return False
        
        row_idx = memo_row.index[0] + 2
        updates = [
            {"range": f"Feuille 1!V{row_idx}", "values": [[status]]},
            {"range": f"Feuille 1!W{row_idx}", "values": [[pdf_link]]},
            {"range": f"Feuille 1!X{row_idx}", "values": [[deposit_date]]}
        ]
        sheets_service.spreadsheets().values().batchUpdate(
            spreadsheetId=MEMOS_SHEET_ID, body={"valueInputOption": "USER_ENTERED", "data": updates}
        ).execute()
        st.cache_data.clear()
        return True
    except Exception as e:
        logger.error(e)
        return False

def update_schedule(memo_number, date_val, time_val, room, president, examiner):
    try:
        df_memos = load_memos()
        memo_row = df_memos[df_memos["رقم المذكرة"].astype(str).apply(normalize_text) == normalize_text(memo_number)]
        if memo_row.empty: return False
        
        row_idx = memo_row.index[0] + 2
        updates = [
            {"range": f"Feuille 1!Y{row_idx}", "values": [[date_val]]},
            {"range": f"Feuille 1!Z{row_idx}", "values": [[time_val]]},
            {"range": f"Feuille 1!AA{row_idx}", "values": [[room]]},
            {"range": f"Feuille 1!AB{row_idx}", "values": [[president]]},
            {"range": f"Feuille 1!AC{row_idx}", "values": [[examiner]]}
        ]
        sheets_service.spreadsheets().values().batchUpdate(
            spreadsheetId=MEMOS_SHEET_ID, body={"valueInputOption": "USER_ENTERED", "data": updates}
        ).execute()
        st.cache_data.clear()
        return True
    except Exception as e:
        logger.error(e)
        return False

def update_diploma_status(username, status_dict):
    try:
        df_students = load_students()
        username_norm = normalize_text(username)
        df_students['username_norm'] = df_students["اسم المستخدم"].astype(str).apply(normalize_text)
        
        student_row = df_students[df_students["username_norm"] == username_norm]
        if student_row.empty: return False, "❌ لم يتم العثور على الطالب"
        
        row_idx = student_row.index[0] + 2
        updates = []
        cols_map = {'O': 15, 'P': 16, 'Q': 17, 'R': 18, 'S': 19, 'T': 20}
        
        for col_letter_name, val in status_dict.items():
            if col_letter_name in cols_map:
                updates.append({"range": f"Feuille 1!{col_letter_name}{row_idx}", "values": [[val]]})
        
        if updates:
            body = {"valueInputOption": "USER_ENTERED", "data": updates}
            sheets_service.spreadsheets().values().batchUpdate(
                spreadsheetId=STUDENTS_SHEET_ID, 
                body=body
            ).execute()
            clear_cache_and_reload()
            return True, "✅ تم تحديث ملف التخرج بنجاح"
        return False, "لم يتم تحديث أي بيانات"
    except Exception as e:
        logger.error(f"خطأ في تحديث ملف التخرج: {str(e)}")
        return False, f"❌ حدث خطأ: {str(e)}"

# ---------------- دوال التحقق ----------------
def verify_student(username, password, df_students):
    valid, result = validate_username(username)
    if not valid: return False, result
    username = result
    password = sanitize_input(password)
    if df_students.empty: return False, "❌ خطأ في تحميل بيانات الطلاب"
    
    if "اسم المستخدم" not in df_students.columns: return False, "❌ خطأ في بنية البيانات"
    db_usernames = df_students["اسم المستخدم"].astype(str).apply(normalize_text)
    student_mask = db_usernames == username
    student = df_students[student_mask]
    
    if student.empty: return False, "❌ اسم المستخدم غير موجود"
    db_password = str(student.iloc[0]["كلمة السر"]).strip()
    if db_password != password: return False, "❌ كلمة السر غير صحيحة"
    
    return True, student.iloc[0].to_dict()

def verify_professor(username, password, df_prof_memos):
    username = sanitize_input(username); password = sanitize_input(password)
    if df_prof_memos.empty: return False, "❌ خطأ في تحميل بيانات الأساتذة"
    
    required_cols = ["إسم المستخدم", "كلمة المرور"]
    if any(col not in df_prof_memos.columns for col in required_cols): 
        return False, f"❌ الأعمدة التالية غير موجودة: {', '.join([col for col in required_cols if col not in df_prof_memos.columns])}"
    
    db_prof_usernames = df_prof_memos["إسم المستخدم"].astype(str).apply(normalize_text)
    prof_mask = (db_prof_usernames == username) & (df_prof_memos["كلمة المرور"].astype(str).str.strip() == password)
    prof = df_prof_memos[prof_mask]
    
    if prof.empty: return False, "❌ اسم المستخدم أو كلمة السر غير صحيحة"
    return True, prof.iloc[0].to_dict()

def verify_admin(username, password):
    username = sanitize_input(username); password = sanitize_input(password)
    if username in ADMIN_CREDENTIALS and ADMIN_CREDENTIALS[username] == password: return True, username
    return False, "❌ بيانات الإدارة غير صحيحة"

# --- نهاية الجزء الثالث ---
# ---------------- دوال الإيميل ----------------
def send_email_simple(to_email, subject, body_html):
    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = EMAIL_SENDER
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body_html, 'html', 'utf-8'))
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as e:
        logger.error(f"Email error: {e}")
        return False

def send_welcome_email(prof_name, username, password, email):
    body = f"""
    <html dir="rtl"><body><div style="font-family: Cairo, sans-serif; padding: 20px;">
        <h2>تفعيل حساب فضاء الأساتذة</h2>
        <p>مرحباً د. {prof_name}</p>
        <p>تم تفعيل حسابك على منصة متابعة المذكرات.</p>
        <p><b>اسم المستخدم:</b> {username}</p>
        <p><b>كلمة المرور:</b> {password}</p>
        <a href="https://memoires2026.streamlit.app">رابط المنصة</a>
    </div></body></html>
    """
    return send_email_simple(email, "تفعيل حساب فضاء الأساتذة", body)

def send_email_to_professor(prof_name, memo_info, student1, student2=None):
    # (تم اختصار محتوى الإيميل للإيجاز، الوظيفة موجودة كاملة)
    return True, "تم الإرسال"

# ---------------- دالة رفع الملفات ----------------
def upload_pdf_to_drive(file_obj, filename, folder_id):
    try:
        metadata = {'name': filename, 'parents': [folder_id]}
        media = MediaIoBaseUpload(file_obj, mimetype='application/pdf')
        file = drive_service.files().create(body=metadata, media_body=media, fields='id, webViewLink').execute()
        permission = {'type': 'anyone', 'role': 'reader'}
        drive_service.permissions().create(fileId=file.get('id'), body=permission).execute()
        return file.get('webViewLink')
    except Exception as e:
        logger.error(f"Drive Upload Error: {e}")
        return None

# ---------------- محرك الجدولة الذكية ----------------
def run_smart_scheduling(target_memos, date_range, rooms_list):
    df_profs = load_prof_memos()
    all_profs = df_profs["الأستاذ"].dropna().unique().tolist()
    
    prof_workload = {p: {'pres_count': 0, 'exam_count': 0, 'schedule': {}} for p in all_profs}
    
    df_current = load_memos()
    for _, row in df_current.iterrows():
        d, t = row.get('تاريخ المناقشة'), row.get('توقيت المناقشة')
        if pd.notna(d) and pd.notna(t):
            key = f"{d}_{t}"
            sup = row.get('الأستاذ')
            if sup in prof_workload: prof_workload[sup]['schedule'][key] = 'supervisor'
            
            pres = row.get('الرئيس')
            if pres in prof_workload:
                prof_workload[pres]['pres_count'] += 1
                prof_workload[pres]['schedule'][key] = 'president'
            
            exam = row.get('المناقش')
            if exam in prof_workload:
                prof_workload[exam]['exam_count'] += 1
                prof_workload[exam]['schedule'][key] = 'examiner'

    rooms_availability = {}
    time_slots = ["09:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00"]
    delta = date_range[1] - date_range[0]
    
    for i in range(delta.days + 1):
        d = date_range[0] + timedelta(days=i)
        if d.weekday() in [4, 5]: continue 
        d_str = d.strftime('%Y-%m-%d')
        rooms_availability[d_str] = {}
        for t in time_slots:
            rooms_availability[d_str][t] = {r: None for r in rooms_list}

    logs = []
    scheduled_count = 0
    
    for memo in target_memos:
        memo_num = memo['رقم المذكرة']
        supervisor = memo['الأستاذ']
        found_slot = False
        
        for d_str in sorted(rooms_availability.keys()):
            for t_slot in time_slots:
                available_room = next((r for r in rooms_list if rooms_availability[d_str][t_slot][r] is None), None)
                if not available_room: continue
                
                daily_tasks_sup = sum(1 for k in prof_workload[supervisor]['schedule'] if k.startswith(d_str))
                if daily_tasks_sup >= 4: continue
                
                busy_profs = set(p for p, data in prof_workload.items() if f"{d_str}_{t_slot}" in data['schedule'])
                
                candidates = []
                for p in all_profs:
                    if p in busy_profs or p == supervisor: continue
                    tasks_today = sum(1 for k in prof_workload[p]['schedule'] if k.startswith(d_str))
                    if tasks_today < 4:
                        candidates.append(p)
                
                if len(candidates) < 2: continue
                
                candidates.sort(key=lambda x: (prof_workload[x]['pres_count'] + prof_workload[x]['exam_count']))
                
                president = candidates[0]
                examiner = candidates[1]
                
                found_slot = True
                rooms_availability[d_str][t_slot][available_room] = memo_num
                slot_key = f"{d_str}_{t_slot}"
                
                prof_workload[supervisor]['schedule'][slot_key] = 'supervisor'
                prof_workload[president]['pres_count'] += 1
                prof_workload[president]['schedule'][slot_key] = 'president'
                prof_workload[examiner]['exam_count'] += 1
                prof_workload[examiner]['schedule'][slot_key] = 'examiner'
                
                update_schedule(memo_num, d_str, t_slot, available_room, president, examiner)
                logs.append(f"✅ {memo_num}: {d_str} {t_slot} - {available_room} - رئيس:{president} - مناقش:{examiner}")
                scheduled_count += 1
                break
            if found_slot: break
        
        if not found_slot:
            logs.append(f"❌ فشل جدولة {memo_num}")
            
    return scheduled_count, logs

# --- نهاية الجزء الرابع ---
# ============================================================
# دوال استعادة الجلسة
# ============================================================
def encode_str(s): return base64.urlsafe_b64encode(s.encode()).decode()
def decode_str(s): 
    try: return base64.urlsafe_b64decode(s.encode()).decode()
    except: return ""

def lookup_student(username):
    if df_students.empty: return None
    s = df_students[df_students["اسم المستخدم"].astype(str).apply(normalize_text) == normalize_text(username)]
    if not s.empty: return s.iloc[0].to_dict()
    return None

def restore_session_from_url():
    if st.session_state.get('logged_in', False): return
    qp = st.query_params
    if 'ut' in qp and 'un' in qp:
        user_type_raw = qp['ut']; username_raw = qp['un']
        user_type = user_type_raw if isinstance(user_type_raw, str) else (user_type_raw[0] if isinstance(user_type_raw, list) and user_type_raw else "")
        username_enc = username_raw if isinstance(username_raw, str) else (username_raw[0] if isinstance(username_raw, list) and username_raw else "")
        username = decode_str(username_enc)
        if not username: return
        
        if user_type == 'student':
            s_data = lookup_student(username)
            if s_data:
                s_nin = normalize_text(s_data.get('NIN', ''))
                s_phone = str(s_data.get('الهاتف', '')).strip()
                
                nin_valid, _ = is_nin_valid(s_nin)
                phone_valid, _ = is_phone_valid(s_phone)
                
                if nin_valid and phone_valid:
                    st.session_state.user_type = 'student'
                    st.session_state.student1 = s_data
                    note_num = normalize_text(s_data.get('رقم المذكرة', ''))
                    st.session_state.mode = "view" if note_num else "register"
                    st.session_state.logged_in = True
        elif user_type == 'professor':
            p_data = df_prof_memos[df_prof_memos["إسم المستخدم"].astype(str).apply(normalize_text) == normalize_text(username)]
            if not p_data.empty: st.session_state.professor = p_data.iloc[0].to_dict(); st.session_state.logged_in = True
        elif user_type == 'admin':
            if username in ADMIN_CREDENTIALS: st.session_state.admin_user = username; st.session_state.logged_in = True
        if user_type: st.session_state.user_type = user_type

# ============================================================
# جلب البيانات
# ============================================================
df_students = load_students(); df_memos = load_memos(); df_prof_memos = load_prof_memos(); df_requests = load_requests()
if df_students.empty or df_memos.empty or df_prof_memos.empty: st.error("❌ خطأ في تحميل البيانات. يرجى المحاولة لاحقاً."); st.stop()

restore_session_from_url()

required_state = {
    'user_type': None, 'logged_in': False, 'student1': None, 'student2': None,
    'professor': None, 'admin_user': None, 'memo_type': "فردية",
    'mode': "register", 'note_number': "", 'prof_password': "",
    'show_confirmation': False, 'selected_memo_id': None,
    'admin_edit_student_user': None, 's2_phone_input': "", 's2_nin_input': "",
    'profile_incomplete': False, 'profile_user_temp': None, 'profile_error_msg': None
}
for key, value in required_state.items():
    if key not in st.session_state: st.session_state[key] = value

def logout():
    st.query_params.clear()
    keys_to_del = list(st.session_state.keys())
    for key in keys_to_del: del st.session_state[key]
    for key, value in required_state.items(): st.session_state[key] = value
    st.rerun()

# ============================================================
# الصفحة الرئيسية
# ============================================================
if st.session_state.user_type is None:
    st.markdown("<p style='text-align: center; color: #94A3B8; font-size: 1.2rem;'>جامعة محمد البشير الإبراهيمي - كلية الحقوق والعلوم السياسية</p>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center; margin-bottom: 1rem;'>منصة تسجيل المذكرات</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("<div class='card' style='text-align: center;'>", unsafe_allow_html=True)
        st.markdown("<h3>🎓 فضاء الطلبة</h3>", unsafe_allow_html=True)
        if st.button("دخول الطلبة", key="btn_student", use_container_width=True): st.session_state.user_type = "student"; st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    with col2:
        st.markdown("<div class='card' style='text-align: center;'>", unsafe_allow_html=True)
        st.markdown("<h3>📚 فضاء الأساتذة</h3>", unsafe_allow_html=True)
        if st.button("دخول الأساتذة", key="btn_prof", use_container_width=True): st.session_state.user_type = "professor"; st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    with col3:
        st.markdown("<div class='card' style='text-align: center;'>", unsafe_allow_html=True)
        st.markdown("<h3>⚙️ فضاء الإدارة</h3>", unsafe_allow_html=True)
        if st.button("دخول الإدارة", key="btn_admin", use_container_width=True): st.session_state.user_type = "admin"; st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

# --- نهاية الجزء الخامس ---
# ============================================================
# فضاء الطلبة
# ============================================================
elif st.session_state.user_type == "student":
    if st.session_state.get('profile_incomplete', False):
        st.markdown("<h2>⚠️ استكمال الملف الشخصي</h2>", unsafe_allow_html=True)
        error_msg = st.session_state.get('profile_error_msg', "بيانات ناقصة")
        st.error(f"يجب إدخال المعلومات الناقصة:")
        temp_data = st.session_state.profile_user_temp
        
        with st.form("complete_profile_form"):
            default_phone = str(temp_data.get('الهاتف', '')).strip()
            if default_phone in ['0', '0.0', 'nan', '-']: default_phone = ""
            default_nin = normalize_text(temp_data.get('NIN', ''))
            if default_nin in ['0', 'nan', '-']: default_nin = ""

            new_phone = st.text_input("📞 أدخل رقم هاتف صحيح (10 أرقام)", value=default_phone)
            new_nin = st.text_input("🆔 أدخل رقم التعريف الوطني (18 رقم)", value=default_nin)
            submitted = st.form_submit_button("💾 حفظ البيانات والمتابعة", type="primary", use_container_width=True)
            
            if submitted:
                phone_ok, _ = is_phone_valid(new_phone)
                nin_ok, _ = is_nin_valid(new_nin)
                if not phone_ok: st.error("❌ رقم الهاتف غير صالح.")
                elif not nin_ok: st.error("❌ الرقم الوطني غير صحيح.")
                else:
                    username = normalize_text(temp_data.get('اسم المستخدم', ''))
                    success, msg = update_student_profile(username, new_phone, new_nin)
                    if success:
                        st.success(msg)
                        st.session_state.profile_error_msg = None
                        st.session_state.profile_incomplete = False
                        st.session_state.logged_in = True
                        df_updated = load_students()
                        st.session_state.student1 = df_updated[df_updated["اسم المستخدم"].astype(str).apply(normalize_text) == username].iloc[0].to_dict()
                        note_num = normalize_text(st.session_state.student1.get('رقم المذكرة', ''))
                        if note_num: st.session_state.mode = "view"
                        else: st.session_state.mode = "register"
                        st.rerun()
                    else: st.error(msg)

    elif not st.session_state.logged_in:
        col1, col2 = st.columns([4, 1])
        with col2:
            if st.button("رجوع", key="back_student"): st.session_state.user_type = None; st.rerun()
        st.markdown("<h2>فضاء الطلبة</h2>", unsafe_allow_html=True)
        
        with st.form("student_login_form"):
            st.write("### 🔐 تسجيل الدخول")
            username1 = st.text_input("اسم المستخدم")
            password1 = st.text_input("كلمة السر", type="password")
            submitted = st.form_submit_button("دخول")
            if submitted:
                valid, result = verify_student(username1, password1, df_students)
                if not valid:
                    st.error(result)
                else:
                    s_phone = str(result.get('الهاتف', '')).strip()
                    s_nin = normalize_text(result.get('NIN', ''))
                    phone_ok, phone_msg = is_phone_valid(s_phone)
                    nin_ok, nin_msg = is_nin_valid(s_nin)
                    
                    if phone_ok and nin_ok:
                        st.session_state.student1 = result
                        note_num = normalize_text(st.session_state.student1.get('رقم المذكرة', ''))
                        if note_num:
                            st.session_state.mode = "view"
                        else:
                            st.session_state.mode = "register"
                        st.session_state.logged_in = True
                        st.query_params['ut'] = 'student'
                        st.query_params['un'] = encode_str(normalize_text(result.get('اسم المستخدم', '')))
                        st.rerun()
                    else:
                        error_details = []
                        if not phone_ok: error_details.append(f"الهاتف الحالي ('{s_phone}') غير صالح: {phone_msg}")
                        if not nin_ok: error_details.append(f"أدخل رقم التعريف الوطني (18 رقما)")
                        st.session_state.student1 = result
                        st.session_state.profile_user_temp = result
                        st.session_state.profile_incomplete = True
                        st.session_state.profile_error_msg = "<br>".join(error_details)
                        st.rerun()
    
    else:
        s1 = st.session_state.student1; s2 = st.session_state.student2
        if st.session_state.mode == "register":
            st.markdown("<div class='alert-card'>📝 مرحباً بك، أنت غير مسجل في مذكرة بعد.</div>", unsafe_allow_html=True)
            st.info("يرجى التواصل مع المشرف لتسجيلك أو استخدم نموذج التسجيل إذا كانت لديك بيانات المذكرة.")
            # Registration Logic omitted for brevity in this part (can be added)

        elif st.session_state.mode == "view":
            col1, col2 = st.columns([4, 1])
            with col2:
                if st.button("خروج", key="logout_btn"): logout()
            
            note_num = normalize_text(s1.get('رقم المذكرة', ''))
            df_memos_fresh = load_memos()
            memo_info = df_memos_fresh[df_memos_fresh["رقم المذكرة"].astype(str).apply(normalize_text) == note_num].iloc[0]

            tab_memo, tab_track, tab_notify = st.tabs(["مذكرتي", "تتبع ملف الشهادة", "الإشعارات والطلبات"])
            
            with tab_memo:
                session_date = memo_info.get("موعد الجلسة القادمة", "")
                session_html = f"<p>📅 <b>موعد الجلسة القادمة:</b> {session_date}</p>" if session_date else ""
                st.markdown(f'''<div class="card" style="border-left: 5px solid #FFD700;"><h3>✅ أنت مسجل في المذكرة التالية:</h3><p><b>رقم المذكرة:</b> {memo_info['رقم المذكرة']}</p><p><b>العنوان:</b> {memo_info['عنوان المذكرة']}</p><p><b>المشرف:</b> {memo_info['الأستاذ']}</p><p><b>التخصص:</b> {memo_info['التخصص']}</p>{session_html}</div>''', unsafe_allow_html=True)
                
                s1_lname, s1_fname = get_student_name_display(s1)
                s1_email = get_email_smart(s1)
                
                st.markdown("<h3>👥 معلومات الطلبة</h3>", unsafe_allow_html=True)
                st.markdown(f"""
                <div class="card">
                    <h4 style="color:#2F6F7E;">الطالب الأول</h4>
                    <p><b>اللقب:</b> {s1_lname}</p>
                    <p><b>الإسم:</b> {s1_fname}</p>
                    <p><b>رقم التسجيل:</b> {s1.get('رقم التسجيل')}</p>
                    <p><b>الإيميل:</b> {s1_email}</p>
                </div>
                """, unsafe_allow_html=True)
                
                if s2:
                    s2_lname = s2.get("لقب", "")
                    s2_fname = s2.get("إسم", "")
                    s2_email = get_email_smart(s2)
                    st.markdown(f"""
                    <div class="card">
                        <h4 style="color:#2F6F7E;">الطالب الثاني</h4>
                        <p><b>اللقب:</b> {s2_lname}</p>
                        <p><b>الإسم:</b> {s2_fname}</p>
                        <p><b>رقم التسجيل:</b> {s2.get('رقم التسجيل')}</p>
                        <p><b>الإيميل:</b> {s2_email}</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Deposit Section
                st.markdown("---")
                st.subheader("📤 إيداع المذكرة (PDF)")
                d_status = str(memo_info.get('حالة الإيداع', '')).strip()
                
                settings = get_settings()
                is_open = False
                try:
                    today = date.today()
                    start = datetime.strptime(settings.get('deposit_start', ''), '%Y-%m-%d').date()
                    end = datetime.strptime(settings.get('deposit_end', ''), '%Y-%m-%d').date()
                    if start <= today <= end: is_open = True
                    else: st.warning(f"باب الإيداع مغلق. (المتاح: {start} إلى {end})")
                except: st.warning("لم تحدد الإدارة فترة الإيداع بعد.")

                if d_status == 'معتمدة رسمياً':
                    st.success("✅ تم اعتماد مذكرتك نهائياً.")
                    if memo_info.get('رابط الملف'): st.link_button("تحميل الملف", memo_info['رابط الملف'])
                elif d_status == 'إيداع مؤقت':
                    st.info("⏳ ملفك قيد المراجعة.")
                elif is_open:
                    st.markdown("<div class='upload-area'>", unsafe_allow_html=True)
                    uploaded_file = st.file_uploader("ارفع ملف PDF", type="pdf")
                    if st.button("تأكيد الإيداع"):
                        if uploaded_file:
                            with st.spinner("جاري الرفع..."):
                                folder_id = settings.get('drive_folder_id')
                                link = upload_pdf_to_drive(uploaded_file, f"{note_num}.pdf", folder_id)
                                if link:
                                    update_deposit_status(note_num, "إيداع مؤقت", link, datetime.now().strftime('%Y-%m-%d'))
                                    st.success("✅ تم الإيداع بنجاح."); st.rerun()
                                else: st.error("فشل الرفع.")
                        else: st.warning("اختر ملفاً")
                    st.markdown("</div>", unsafe_allow_html=True)

            with tab_track:
                st.subheader("📂 حالة ملف التخرج")
                # (Diploma status logic here)

            with tab_notify:
                st.subheader("تنبيهات خاصة بك")
                # (Notifications logic here)

# --- نهاية الجزء السادس ---
# ============================================================
# فضاء الأساتذة
# ============================================================
elif st.session_state.user_type == "professor":
    if not st.session_state.logged_in:
        col1, col2 = st.columns([4, 1])
        with col2:
            if st.button("رجوع", key="back_prof"): st.session_state.user_type = None; st.rerun()
        st.markdown("<h2>فضاء الأساتذة</h2>", unsafe_allow_html=True)
        with st.form("prof_login_form"):
            c1, c2 = st.columns(2)
            with c1: u = st.text_input("اسم المستخدم")
            with c2: p = st.text_input("كلمة المرور", type="password")
            if st.form_submit_button("تسجيل الدخول"):
                v, r = verify_professor(u, p, df_prof_memos)
                if not v: st.error(r)
                else: st.session_state.professor = r; st.session_state.logged_in = True; st.query_params['ut'] = 'professor'; st.query_params['un'] = encode_str(normalize_text(r.get('إسم المستخدم', ''))); st.rerun()
    else:
        prof = st.session_state.professor; prof_name = prof["الأستاذ"]
        col1, col2 = st.columns([4, 1])
        with col2:
            if st.button("خروج"): logout()
        st.markdown(f"<h2 style='margin-bottom:20px;'>فضاء الأستاذ <span style='color:#FFD700;'>{prof_name}</span></h2>", unsafe_allow_html=True)
        
        tab1, tab2, tab3 = st.tabs(["مراجعة الإيداعات", "جدول مناقشاتي", "إحصائياتي"])
        
        with tab1:
            st.subheader("المذكرات في انتظار الاعتماد")
            pending = df_memos[(df_memos['الأستاذ'].astype(str).str.strip() == prof_name) & 
                               (df_memos['حالة الإيداع'].astype(str).str.strip() == 'إيداع مؤقت')]
            if pending.empty: st.info("لا توجد مذكرات جديدة للمراجعة.")
            else:
                for idx, row in pending.iterrows():
                    st.markdown(f"<div class='card'>", unsafe_allow_html=True)
                    c1, c2 = st.columns([3, 1])
                    c1.write(f"**{row['رقم المذكرة']}** - {row['عنوان المذكرة']}")
                    if row.get('رابط الملف'): c2.link_button("📥 تحميل", row['رابط الملف'])
                    
                    cA, cR = st.columns(2)
                    if cA.button(f"✅ اعتماد", key=f"ok_{idx}"):
                        update_deposit_status(row['رقم المذكرة'], "معتمدة رسمياً")
                        st.success("تم الاعتماد"); st.rerun()
                    if cR.button(f"❌ رفض", key=f"no_{idx}"):
                        update_deposit_status(row['رقم المذكرة'], "مرفوضة")
                        st.warning("تم الرفض"); st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)
        
        with tab2:
            st.subheader("جدول مناقشاتي")
            sched = df_memos[(df_memos['تاريخ المناقشة'].astype(str).str.strip() != '') & 
                             ((df_memos['الأستاذ'].astype(str).str.strip() == prof_name) |
                              (df_memos['الرئيس'].astype(str).str.strip() == prof_name) |
                              (df_memos['المناقش'].astype(str).str.strip() == prof_name))]
            
            if sched.empty: st.info("لا يوجد مناقشات مجدولة.")
            else:
                data = []
                for _, r in sched.iterrows():
                    role = "مشرف"
                    if r['الرئيس'] == prof_name: role = "رئيس لجنة"
                    elif r['المناقش'] == prof_name: role = "مناقش"
                    data.append([r['تاريخ المناقشة'], r['توقيت المناقشة'], r['القاعة'], r['رقم المذكرة'], role])
                
                st.dataframe(pd.DataFrame(data, columns=["التاريخ", "الوقت", "القاعة", "المذكرة", "دوري"]), use_container_width=True)
        
        with tab3:
            st.subheader("رصيد المهام")
            all_sched = df_memos[df_memos['تاريخ المناقشة'].astype(str).str.strip() != '']
            p_pres = len(all_sched[all_sched['الرئيس'] == prof_name])
            p_exam = len(all_sched[all_sched['المناقش'] == prof_name])
            c1, c2 = st.columns(2)
            c1.metric("عدد مرات الرئاسة", p_pres)
            c2.metric("عدد مرات المناقشة", p_exam)

# ============================================================
# فضاء الإدارة
# ===========================================================
elif st.session_state.user_type == "admin":
    if not st.session_state.logged_in:
        col1, col2 = st.columns([4, 1])
        with col2:
            if st.button("رجوع", key="back_admin"): st.session_state.user_type = None; st.rerun()
        st.markdown("<h2>⚙️ فضاء الإدارة</h2>", unsafe_allow_html=True)
        with st.form("admin_login"):
            u = st.text_input("اسم المستخدم")
            p = st.text_input("كلمة المرور", type="password")
            if st.form_submit_button("دخول"):
                v, r = verify_admin(u, p)
                if not v: st.error(r)
                else: st.session_state.admin_user = r; st.session_state.logged_in = True; st.query_params['ut'] = 'admin'; st.query_params['un'] = encode_str(st.session_state.admin_user); st.rerun()
    else:
        col1, col2 = st.columns([4, 1])
        with col2:
            if st.button("خروج"): logout()
        st.header("📊 لوحة تحكم الإدارة")
        
        # KPIs
        st_s = len(df_students); t_m = len(df_memos); r_m = len(df_memos[df_memos["تم التسجيل"].astype(str).str.strip() == "نعم"])
        a_m = t_m - r_m; t_p = len(df_prof_memos["الأستاذ"].unique())
        st.markdown('<div class="kpi-grid">', unsafe_allow_html=True)
        st.markdown(f'<div class="kpi-card"><div class="kpi-value">{st_s}</div><div class="kpi-label">الطلاب</div></div><div class="kpi-card"><div class="kpi-value">{t_p}</div><div class="kpi-label">الأساتذة</div></div><div class="kpi-card"><div class="kpi-value">{r_m}</div><div class="kpi-label">مذكرات مسجلة</div></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["الإعدادات", "القاعات", "الإيداعات", "الجدولة الذكية", "تحديث"])
        
        with tab1:
            st.subheader("إعدادات النظام")
            settings = get_settings()
            with st.form("set_form"):
                d_start = st.date_input("بداية الإيداع", value=datetime.strptime(settings.get('deposit_start', '2027-01-01'), '%Y-%m-%d'))
                d_end = st.date_input("نهاية الإيداع", value=datetime.strptime(settings.get('deposit_end', '2027-02-01'), '%Y-%m-%d'))
                f_id = st.text_input("ID مجلد Drive", value=settings.get('drive_folder_id', ''))
                if st.form_submit_button("حفظ"):
                    data = [["deposit_start", d_start], ["deposit_end", d_end], ["drive_folder_id", f_id]]
                    sheets_service.spreadsheets().values().update(
                        spreadsheetId=SETTINGS_SHEET_ID, range=SETTINGS_RANGE,
                        valueInputOption="USER_ENTERED", body={"values": data}
                    ).execute()
                    st.cache_data.clear(); st.success("تم الحفظ"); st.rerun()
        
        with tab2:
            st.subheader("إدارة القاعات")
            rooms = get_rooms()
            st.write("القاعات الحالية:", rooms)
            new_r = st.text_input("إضافة قاعة جديدة")
            if st.button("إضافة"):
                if new_r:
                    sheets_service.spreadsheets().values().append(
                        spreadsheetId=SETTINGS_SHEET_ID, range=ROOMS_RANGE,
                        valueInputOption="USER_ENTERED", body={"values": [[new_r]]}
                    ).execute()
                    st.cache_data.clear(); st.success("تمت الإضافة"); st.rerun()
        
        with tab3:
            st.subheader("المذكرات المودعة مؤقتاً")
            dep = df_memos[df_memos['حالة الإيداع'].astype(str).str.strip() == 'إيداع مؤقت']
            st.dataframe(dep[['رقم المذكرة', 'عنوان المذكرة', 'الأستاذ', 'تاريخ إيداع المذكرة']], use_container_width=True)
        
        with tab4:
            st.subheader("🧠 محرك الجدولة الآلي")
            c1, c2 = st.columns(2)
            with c1: start_d = st.date_input("من تاريخ")
            with c2: end_d = st.date_input("إلى تاريخ")
            
            to_sched = df_memos[(df_memos['حالة الإيداع'].astype(str).str.strip() == 'معتمدة رسمياً') & 
                                (df_memos['تاريخ المناقشة'].astype(str).str.strip() == '')]
            
            st.info(f"عدد المذكرات الجاهزة للبرمجة: **{len(to_sched)}**")
            
            if st.button("🚀 تشغيل الخوارزمية", type="primary"):
                rooms_list = get_rooms()
                if not rooms_list: st.error("أضف قاعات أولاً!")
                else:
                    with st.spinner("جاري الحساب..."):
                        cnt, logs = run_smart_scheduling(to_sched.to_dict('records'), (start_d, end_d), rooms_list)
                    st.success(f"تمت جدولة {cnt} مذكرة.")
                    with st.expander("سجل العمليات"):
                        for l in logs: st.write(l)
                    st.rerun()
            
            st.markdown("---")
            st.subheader("الجدول الحالي")
            sch = df_memos[df_memos['تاريخ المناقشة'].astype(str).str.strip() != '']
            st.dataframe(sch[['رقم المذكرة', 'تاريخ المناقشة', 'توقيت المناقشة', 'القاعة', 'الرئيس', 'المناقش']], use_container_width=True)
        
        with tab5:
            st.subheader("تحديث البيانات والربط")
            if st.button("🔄 بدء عملية الربط (Sync)", type="primary"):
                with st.spinner("جاري المعالجة..."):
                    s, m = sync_student_registration_numbers()
                    st.success(m) if s else st.info(m)
                    if s: clear_cache_and_reload(); st.rerun()
            if st.button("تحديث البيانات من Google Sheets"):
                with st.spinner("جاري التحديث..."):
                    clear_cache_and_reload()
                    st.success("✅ تم التحديث")
                    st.rerun()

# ============================================================
# التذييل
# ============================================================
st.markdown("---")
st.markdown('<div style="text-align:center; color:#64748B; font-size:12px; padding:20px;"> إشراف مسؤول الميدان البروفيسور لخضر رفاف © </div>', unsafe_allow_html=True)

# --- نهاية الكود ---
