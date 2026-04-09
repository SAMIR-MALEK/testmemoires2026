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
import re
from googleapiclient.http import MediaIoBaseUpload
import io
st.cache_data.clear()

# ---------------- إعداد Logging ----------------
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ---------------- إعداد الصفحة ----------------
st.set_page_config(page_title="تسجيل مذكرات الماستر", page_icon="📘", layout="wide")

# ========================
# إعداد الموعد النهائي
# ========================
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

    /* إصلاح واجهة رفع الملفات */
    [data-testid="stFileUploader"] {
        background: rgba(30, 41, 59, 0.8) !important;
        border: 2px dashed #2F6F7E !important;
        border-radius: 16px !important;
        padding: 20px !important;
    }
    [data-testid="stFileUploader"] label {
        color: #ffffff !important;
        font-size: 1rem !important;
        font-weight: 600 !important;
    }
    [data-testid="stFileUploader"] section {
        background: rgba(15, 23, 42, 0.6) !important;
        border-radius: 12px !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
    }
    [data-testid="stFileUploader"] section > div {
        color: #94A3B8 !important;
    }
    [data-testid="stFileUploaderDropzone"] {
        background: rgba(47, 111, 126, 0.1) !important;
        border-radius: 12px !important;
    }
    [data-testid="stFileUploaderDropzoneInstructions"] span,
    [data-testid="stFileUploaderDropzoneInstructions"] p,
    [data-testid="stFileUploaderDropzoneInstructions"] small {
        color: #94A3B8 !important;
    }
    [data-testid="stFileUploader"] button {
        background-color: #2F6F7E !important;
        color: #ffffff !important;
        border-radius: 8px !important;
        width: auto !important;
        padding: 8px 20px !important;
    }
</style>
""", unsafe_allow_html=True)

# ---------------- Google Sheets ----------------
SCOPES_SHEETS = ['https://www.googleapis.com/auth/spreadsheets']
SCOPES_DRIVE  = ['https://www.googleapis.com/auth/drive']

try:
    info = st.secrets["service_account"]
    credentials = Credentials.from_service_account_info(info, scopes=SCOPES_SHEETS)
    sheets_service = build('sheets', 'v4', credentials=credentials)
except Exception as e:
    st.error("⚠️ خطأ في الاتصال بـ Google Sheets")
    st.stop()

# Drive للإيداع (service account منفصل)
DRIVE_UPLOAD_FOLDER_ID = "1fvckcOGegVD4Ofs-UnVZbVCbYBQlToWs"
try:
    drive_info = st.secrets["drive_service_account"]
    drive_credentials = Credentials.from_service_account_info(drive_info, scopes=SCOPES_DRIVE)
    drive_service = build('drive', 'v3', credentials=drive_credentials)
except Exception as e:
    drive_service = None
    logger.warning(f"Drive service account not configured: {e}")

STUDENTS_SHEET_ID = "1gvNkOVVKo6AO07dRKMnSQw6vZ3KdUnW7I4HBk61Sqns"
MEMOS_SHEET_ID = "1LNJMBAye4QIQy7JHz6F8mQ6-XNC1weZx1ozDZFfjD5s"
PROF_MEMOS_SHEET_ID = "1OnZi1o-oPMUI_W_Ew-op0a1uOhSj006hw_2jrMD6FSE"
REQUESTS_SHEET_ID = "1sTJ6BZRM4Qgt0w2xUkpFZqquL-hfriMYTSN3x1_12_o"

STUDENTS_RANGE = "Feuille 1!A1:U1000" 
MEMOS_RANGE = "Feuille 1!A1:U1000"
PROF_MEMOS_RANGE = "Feuille 1!A1:P1000"
REQUESTS_RANGE = "Feuille 1!A1:K1000"

ADMIN_CREDENTIALS = {"admin": "admin2026", "dsp": "dsp@2026"}

EMAIL_SENDER = "domaine.dsp@univ-bba.dz"
EMAIL_PASSWORD = "oqwejylusjllfvhc"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
ADMIN_EMAIL = "domaine.dsp@univ-bba.dz"

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

# دالة جديدة لتوحيد النصوص (إزالة .0 والمسافات)
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
    keys_lname = ["اللقب", "لقب", "Nom", "nom"]
    lname = ""
    for k in keys_lname:
        val = str(student_dict.get(k, "")).strip()
        if val and val not in ['nan', 'None', '-']:
            lname = val
            break
    
    keys_fname = ["الإسم", "إسم", "اسم", "الاسم", "Prénom", "prenom"]
    fname = ""
    for k in keys_fname:
        val = str(student_dict.get(k, "")).strip()
        if val and val not in ['nan', 'None', '-']:
            fname = val
            break
            
    return lname, fname

def load_student2_for_memo(memo_row, current_student_reg, df_students):
    """يجلب الطالب الآخر في المذكرة بغض النظر عن موضعه (S أو T)"""
    memo_list = memo_row.tolist() if hasattr(memo_row, 'tolist') else list(memo_row.values())
    reg_s = normalize_text(memo_row.get("رقم تسجيل الطالب 1", memo_list[18] if len(memo_list) > 18 else ""))
    reg_t = normalize_text(memo_row.get("رقم تسجيل الطالب 2", memo_list[19] if len(memo_list) > 19 else ""))
    
    current_reg = normalize_text(current_student_reg)
    
    # الطالب الثاني = الآخر (ليس الطالب الداخل)
    if current_reg == reg_s:
        other_reg = reg_t
    elif current_reg == reg_t:
        other_reg = reg_s
    else:
        # إن لم يُطابق شيء، نأخذ T كافتراضي
        other_reg = reg_t

    if not other_reg or other_reg in ["", "nan"]:
        return None

    df_students['رقم التسجيل_norm'] = df_students['رقم التسجيل'].astype(str).apply(normalize_text)
    s2_data = df_students[df_students["رقم التسجيل_norm"] == other_reg]
    if not s2_data.empty:
        return s2_data.iloc[0].to_dict()
    return None

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
        reg1 = normalize_text(raw_reg1) # استخدام normalize_text
        reg2 = normalize_text(raw_reg2) # استخدام normalize_text
    except:
        reg1 = normalize_text(memo_row.get("رقم تسجيل الطالب 1", ""))
        reg2 = normalize_text(memo_row.get("رقم تسجيل الطالب 2", ""))
        
    # Normalize registration numbers in the dataframe for matching
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
        result = sheets_service.spreadsheets().values().get(
            spreadsheetId=MEMOS_SHEET_ID, range="Feuille 1!A1:AI1000"
        ).execute()
        values = result.get('values', [])
        if not values: return pd.DataFrame()
        headers = values[0]
        rows = values[1:]
        # توحيد عدد الأعمدة في كل صف
        padded = [r + [''] * (len(headers) - len(r)) for r in rows]
        df = pd.DataFrame(padded, columns=headers)
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

def update_student_profile(username, phone, nin):
    try:
        df_students = load_students()
        # Use normalized matching for username lookup as well
        df_students['username_norm'] = df_students["اسم المستخدم"].astype(str).apply(normalize_text)
        username_norm = normalize_text(username)
        
        student_row = df_students[df_students["username_norm"] == username_norm]
        if student_row.empty: return False, "❌ لم يتم العثور على الطالب"
        
        # Original index for sheet update
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
        
        # Normalize for matching
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

def save_and_send_request(req_type, prof_name, memo_id, memo_title, details_text, status="قيد المراجعة"):
    try:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        new_row = ["", timestamp, req_type, status, prof_name, memo_id, "", "", details_text, "", ""]
        body_append = {"values": [new_row]}
        sheets_service.spreadsheets().values().append(
            spreadsheetId=REQUESTS_SHEET_ID, range="Feuille 1!A2",
            valueInputOption="USER_ENTERED", body=body_append, insertDataOption="INSERT_ROWS"
        ).execute()
        
        request_titles = {
            "تغيير عنوان المذكرة": "طلب تغيير عنوان مذكرة",
            "حذف طالب": "طلب حذف طالب من مذكرة ثنائية",
            "إضافة طالب": "طلب إضافة طالب لمذكرة فردية",
            "تنازل": "طلب تنازل عن الإشراف",
            "جلسة إشراف": "تنبيه: جلسة إشراف مجدولة"
        }
        subject = f"{request_titles.get(req_type, 'طلب جديد')} - {prof_name}"
        email_body = f"<html dir='rtl'><body style='font-family:sans-serif; padding:20px;'><div style='background:#f4f4f4; padding:30px; border-radius:10px; max-width:600px; margin:auto; color:#333;'><h2 style='background:#8B4513; color:white; padding:20px; border-radius:8px; text-align:center;'>{subject}</h2><p><strong>من:</strong> {prof_name}</p><p><strong>رقم/نوع:</strong> {memo_id}</p><div style='background:#fff8dc; padding:15px; border-right:4px solid #8B4513; margin:15px 0; border-radius: 8px;'><h3>التفاصيل:</h3><p>{details_text}</p></div></div></body></html>"
        
        msg = MIMEMultipart('alternative')
        msg['From'], msg['To'], msg['Subject'] = EMAIL_SENDER, ADMIN_EMAIL, subject
        msg.attach(MIMEText(email_body, 'html', 'utf-8'))
        
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls(); server.login(EMAIL_SENDER, EMAIL_PASSWORD); server.send_message(msg)
        return True, "✅ تم تسجيل الطلب في النظام وإرسال الإيميل للإدارة"
    except Exception as e:
        logger.error(f"Request Error: {str(e)}")
        return False, f"❌ حدث خطأ أثناء تسجيل الطلب: {str(e)}"

def update_progress(memo_number, progress_value):
    try:
        df_memos = load_memos()
        # Normalize for matching
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

# -------------------------------------------------------------
# دوال الإيميل
# -------------------------------------------------------------
def _send_email_to_professor_row(row):
    possible_username_keys = ["إسم المستخدم", "اسم المستخدم", "Identifiant", "Username", "user"]
    possible_password_keys = ["كلمة المرور", "كلمة السر", "Password", "pass"]
    possible_email_keys = ["البريد الإلكتروني", "الإيميل", "email", "Email", "E-mail"]
    
    prof_name = row.get("الأستاذ", "غير محدد")
    email = ""; username = ""; password = ""
    
    for col in possible_email_keys:
        if col in row.index:
            val = str(row[col]).strip()
            if "@" in val and val != "nan": email = val; break
            
    for col in possible_username_keys:
        if col in row.index:
            val = str(row[col]).strip()
            if val != "nan" and val != "": username = val; break
            
    for col in possible_password_keys:
        if col in row.index:
            val = str(row[col]).strip()
            if val != "nan" and val != "": password = val; break
            
    if not email or not username or not password: return False, "⚠️ بيانات ناقصة"
    
    email_body = f"""
    <html dir="rtl"><head><meta charset="UTF-8"><style>body {{ font-family: 'Cairo', Arial, sans-serif; direction: rtl; text-align: right; line-height: 1.6; background-color: #f4f4f4; margin: 0; padding: 0; }} .container {{ max-width: 600px; margin: 20px auto; background-color: #ffffff; padding: 30px; border: 1px solid #dddddd; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }} .header {{ text-align: center; margin-bottom: 30px; border-bottom: 2px solid #0056b3; padding-bottom: 20px; }} .header h2 {{ color: #003366; margin: 0; font-size: 24px; }} .header h3 {{ color: #005580; margin: 5px 0 0 0; font-size: 20px; }} .content {{ margin-bottom: 30px; color: #333; }} .content ul {{ padding-right: 20px; }} .info-box {{ background-color: #eef7fb; border-right: 5px solid #005580; padding: 20px; margin: 20px 0; border-radius: 4px; }} .info-box p {{ margin: 10px 0; font-weight: bold; font-size: 1.1em; }} .footer {{ text-align: center; margin-top: 40px; font-size: 14px; color: #666; border-top: 1px solid #eee; padding-top: 20px; }} .link {{ color: #005580; text-decoration: none; font-weight: bold; }} .link:hover {{ text-decoration: underline; }}</style></head><body><div class="container"><div class="header"><h2>جامعة محمد البشير الإبراهيمي – برج بوعريريج</h2><h3>كلية الحقوق والعلوم السياسية</h3><h4 style="color:#666; margin-top:5px;">فضاء الأساتذة</h4></div><div class="content"><p>تحية طيبة وبعد،</p><p>الأستاذ (ة) الفاضل (ة) : <strong>{prof_name}</strong></p><br><p>في إطار رقمنة متابعة مذكّرات الماستر، يشرفنا إعلامكم بأنه تم تفعيل فضاء الأساتذة على منصة متابعة مذكرات الماستر الخاصة بكلية الحقوق والعلوم السياسية، وذلك قصد تسهيل عملية المتابعة البيداغوجية وتنظيم الإشراف.</p><p>يُمكِّنكم فضاء الأستاذ من القيام بالمهام التالية:</p><ul><li>متابعة حالة تسجيل كل مذكرة (مسجلة / غير مسجلة).</li><li>الاطلاع على أسماء الطلبة المسجلين وأرقام هواتفهم وبريدهم المهني.</li><li>تحديث نسبة التقدم في إنجاز المذكرات.</li><li>تحديد موعد جلسة إشراف واحدة يتم تعميمها آليًا على جميع الطلبة المعنيين.</li><li>إرسال طلبات إدارية رقمية للإدارة.</li></ul><div class="info-box"><p>الدخول إلى حسابكم يكون عبر الرابط:</p><a href="https://memoires2026.streamlit.app" class="link">https://memoires2026.streamlit.app</a><p style="margin-top: 15px;">إسم المستخدم: <span style="background:#fff; padding:2px 8px; border:1px solid #ccc; border-radius:4px;">{username}</span></p><p>كلمة المرور: <span style="background:#fff; padding:2px 8px; border:1px solid #ccc; border-radius:4px;">{password}</span></p></div></div><div class="footer"><p>تقبلوا تحياتنا الطيبة.</p><p>مسؤول الميدان: البروفيسور لخضر رفاف</p></div></div></body></html>
    """
    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = EMAIL_SENDER; msg['To'] = email; msg['Subject'] = "تفعيل حساب فضاء الأساتذة - منصة المذكرات"
        msg.attach(MIMEText(email_body, 'html', 'utf-8'))
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls(); server.login(EMAIL_SENDER, EMAIL_PASSWORD); server.send_message(msg)
        return True, f"✅ تم الإرسال إلى {email}"
    except Exception as e:
        logger.error(f"Error sending email to {prof_name}: {e}")
        return False, f"❌ فشل الإرسال: {str(e)}"

def send_welcome_emails_to_all_profs():
    try:
        df_profs = load_prof_memos()
        sent_count = 0; failed_count = 0; results_log = []
        progress_bar = st.progress(0); total_profs = len(df_profs)
        with st.spinner("⏳ جاري الإرسال لجميع الأساتذة... يرجى الانتظار"):
            for index, row in df_profs.iterrows():
                success, msg = _send_email_to_professor_row(row)
                if success: sent_count += 1
                else: failed_count += 1
                results_log.append(msg)
                progress_bar.progress((index + 1) / total_profs)
                time.sleep(0.5)
        return sent_count, failed_count, results_log
    except Exception as e:
        return 0, 0, [f"خطأ عام: {str(e)}"]

def send_welcome_email_to_one(prof_name):
    try:
        df_profs = load_prof_memos()
        prof_rows = df_profs[df_profs["الأستاذ"].astype(str).str.strip() == prof_name.strip()]
        if prof_rows.empty: return False, f"❌ لم يتم العثور على الأستاذ: {prof_name}"
        row = prof_rows.iloc[0]
        with st.spinner(f"⏳ جاري الإرسال للأستاذ: {prof_name}..."):
            success, msg = _send_email_to_professor_row(row)
        if success: return True, msg
        else: return False, msg
    except Exception as e:
        logger.error(f"Error sending single email: {e}")
        return False, f"حدث خطأ: {str(e)}"

def format_datetime_ar(date_obj, time_str):
    days_ar = ["الاثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت", "الأحد"]
    day_name = days_ar[date_obj.weekday()]
    date_str = date_obj.strftime('%Y-%m-%d')
    return f"{day_name} {date_str} الساعة {time_str}"

def get_students_of_professor(prof_name, df_memos):
    prof_memos = df_memos[(df_memos["الأستاذ"].astype(str).str.strip() == prof_name.strip()) & (df_memos["تم التسجيل"].astype(str).str.strip() == "نعم")]
    students_data = []
    for _, memo in prof_memos.iterrows():
        s1_name = str(memo.get("الطالب الأول", "")).strip()
        s1_reg = normalize_text(memo.get("رقم تسجيل الطالب 1", memo.get("رقم التسجيل 1", "")))
        if s1_name and s1_name != "--" and s1_reg: students_data.append({"name": s1_name, "reg": s1_reg, "memo": memo.get("رقم المذكرة")})
        
        s2_name = str(memo.get("الطالب الثاني", "")).strip()
        s2_reg = normalize_text(memo.get("رقم تسجيل الطالب 2", memo.get("رقم التسجيل 2", "")))
        if s2_name and s2_name != "--" and s2_reg: students_data.append({"name": s2_name, "reg": s2_reg, "memo": memo.get("رقم المذكرة")})
    return students_data

def update_session_date_in_sheets(prof_name, date_str):
    try:
        df_memos = load_memos()
        masks = (df_memos["الأستاذ"].astype(str).str.strip() == prof_name) & (df_memos["تم التسجيل"].astype(str).str.strip() == "نعم")
        target_indices = df_memos[masks].index
        if target_indices.empty: return True, "لا توجد مذكرات لتحديثها"
        
        updates = []; col_names = df_memos.columns.tolist(); target_col_name = "موعد الجلسة القادمة"
        if target_col_name in col_names: col_idx = col_names.index(target_col_name) + 1
        else: col_idx = len(col_names)
        col_letter_str = col_letter(col_idx)
        
        for idx in target_indices:
            row_num = idx + 2
            updates.append({"range": f"Feuille 1!{col_letter_str}{row_num}", "values": [[date_str]]})
        
        body = {"valueInputOption": "USER_ENTERED", "data": updates}
        sheets_service.spreadsheets().values().batchUpdate(spreadsheetId=MEMOS_SHEET_ID, body=body).execute()
        return True, "تم تحديث التواريخ بنجاح"
    except Exception as e:
        logger.error(f"Update Session Error: {e}")
        return False, str(e)

def send_session_emails(students_data, session_info, prof_name):
    try:
        df_students = load_students(); student_emails = []
        
        # Create normalized column for matching
        df_students['رقم التسجيل_norm'] = df_students['رقم التسجيل'].astype(str).apply(normalize_text)
        
        for s in students_data:
            s_row = df_students[df_students["رقم التسجيل_norm"] == s['reg']]
            if not s_row.empty:
                email = ""
                possible_cols = ["البريد المهني", "البريد الإلكتروني", "email", "Email"]
                for col in possible_cols:
                    if col in s_row.columns:
                        val = str(s_row.iloc[0][col]).strip()
                        if val and val != "nan" and "@" in val: email = val; break
                if email: student_emails.append(email)
        
        subject = f"🔔 تنبيه هام: جلسة إشراف - {prof_name}"
        students_list_html = "<ul>"
        for i, s in enumerate(students_data):
            if i < 10: students_list_html += f"<li>{s['name']}</li>"
            else: students_list_html += f"<li>... و {len(students_data) - 10} طالب آخر</li>"; break
        students_list_html += "</ul>"
        
        email_body = f"""
        <html dir="rtl"><head><style>body {{ font-family: 'Arial', sans-serif; background-color: #f4f4f4; padding: 20px; }} .container {{ background-color: #ffffff; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); max-width: 600px; margin: auto; border-top: 5px solid #256D85; }} .header {{ text-align: center; margin-bottom: 20px; }} .highlight {{ background-color: #e8f4f8; padding: 15px; border-radius: 8px; margin: 15px 0; font-size: 1.1em; }} .footer {{ text-align: center; color: #777; font-size: 12px; margin-top: 30px; border-top: 1px solid #ddd; padding-top: 10px; }}</style></head><body><div class="container"><div class="header"><h2 style="color: #256D85; margin: 0;">📅 جدولة جلسة إشراف</h2></div><p>السلام عليكم ورحمة الله،</p><p>يُعلن الأستاذ(ة) <b>{prof_name}</b> عن تنظيم جلسة إشراف للمذكرات.</p><div class="highlight"><strong>📆 الموعد:</strong> {session_info}</div><p>تم توجيه هذا الإشعار إلى الطلبة المسجلين تحت إشراف الأستاذ:</p>{students_list_html}<hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;"><p style="font-size: 0.9em; color: #555;"><strong>للإدارة:</strong> يرجى نشر هذا الموعد في الفيسبوك وإعلام الطلبة غير الحاصلين على بريد إلكتروني.</p></div><div class="footer">جامعة محمد البشير الإبراهيمي - كلية الحقوق والعلوم السياسية</div></body></html>
        """
        
        msg = MIMEMultipart('alternative')
        msg['From'] = EMAIL_SENDER; msg['To'] = ADMIN_EMAIL; msg['Subject'] = subject
        if student_emails: msg['Bcc'] = ", ".join(student_emails)
        msg.attach(MIMEText(email_body, 'html', 'utf-8'))
        
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls(); server.login(EMAIL_SENDER, EMAIL_PASSWORD); server.send_message(msg)
        logger.info(f"✅ Session email sent to Admin and {len(student_emails)} students.")
        return True, "تم الإرسال"
    except Exception as e:
        logger.error(f"Error sending session emails: {e}")
        return False, str(e)

def send_email_to_professor(prof_name, memo_info, student1, student2=None):
    try:
        df_prof_memos = load_prof_memos()
        prof_row = df_prof_memos[df_prof_memos["الأستاذ"].astype(str).str.strip() == prof_name.strip()]
        if prof_row.empty:
            clean_name = prof_name.strip().replace("الأستاذ", "").replace("د.", "").replace("أ.د", "").strip()
            if clean_name: prof_row = df_prof_memos[df_prof_memos["الأستاذ"].astype(str).str.contains(clean_name, case=False, na=False)]
        
        if prof_row.empty:
            error_msg = f"فشل الإرسال: لم يتم العثور على البريد للأستاذ <b>{prof_name}</b>."
            logger.error(f"Email Error: Professor {prof_name} not found.")
            return False, error_msg
            
        prof_data = prof_row.iloc[0]; prof_email = ""
        possible_email_cols = ["البريد الإلكتروني", "الإيميل", "email", "Email"]
        for col in possible_email_cols:
            if col in prof_data.index:
                val = str(prof_data[col]).strip()
                if val and val != "nan": prof_email = val; break
        
        if "@" not in prof_email:
            error_msg = f"فشل الإرسال: الأستاذ <b>{prof_name}</b> موجود، ولكن البريد الإلكتروني فارغ."
            logger.error(f"Email Error: Invalid email for Prof {prof_name}: {prof_email}")
            return False, error_msg
            
        total_memos = len(prof_row)
        registered_memos = len(prof_row[prof_row["تم التسجيل"].astype(str).str.strip() == "نعم"])
        
        s1_lname, s1_fname = get_student_name_display(student1)
        student2_info = ""
        if student2 is not None:
            s2_lname, s2_fname = get_student_name_display(student2)
            student2_info = f"\n👤 **الطالب الثاني:** {s2_lname} {s2_fname}"
            
        email_body = f"""
<html dir="rtl"><head><style>body {{ font-family: 'Arial', sans-serif; background-color: #f4f4f4; padding: 20px; }} .container {{ background-color: #ffffff; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); max-width: 600px; margin: auto; }} .header {{ background-color: #256D85; color: white; padding: 20px; border-radius: 8px; text-align: center; margin-bottom: 20px; }} .header h2 {{ margin: 0; }} .content {{ line-height:1.8; color: #333; }} .info-box {{ background-color: #f8f9fa; padding: 15px; border-right: 4px solid #256D85; margin: 15px 0; }} .stats-box {{ background-color: #e8f4f8; padding: 15px; border-radius: 8px; margin: 15px 0; }} .footer {{ text-align: center; color: #888; font-size: 12px; margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; }} .highlight {{ color: #256D85; font-weight: bold; }} ul {{ list-style: none; padding: 0; }} li {{ padding: 5px 0; }}</style></head>
<body><div class="container"><div class="header"><h2>✅ تسجيل مذكرة جديدة</h2></div><div class="content"><p>تحية طيبة، الأستاذ(ة) <span class="highlight">{prof_name}</span>،</p><p>نحيطكم علماً بأنه تم تسجيل مذكرة جديدة تحت إشرافكم:</p><div class="info-box"><p>📄 <strong>رقم المذكرة:</strong> {memo_info['رقم المذكرة']}</p><p>📑 <strong>عنوان المذكرة:</strong> {memo_info['عنوان المذكرة']}</p><p>🎓 <strong>التخصص:</strong> {memo_info['التخصص']}</p><p>👤 <strong>الطالب الأول:</strong> {s1_lname} {s1_fname}{student2_info}</p><p>🕒 <strong>تاريخ التسجيل:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M')}</p></div><div class="stats-box"><h3 style="color: #256D85; margin-top: 0;">📊 إحصائيات مذكراتك:</h3><ul><li>📝 <strong>إجمالي المذكرات:</strong> {total_memos}</li><li>✅ <strong>المذكرات المسجلة:</strong> {registered_memos}</li><li>⏳ <strong>المذكرات المتبقية:</strong> {total_memos - registered_memos}</li></ul></div><p style="margin-top: 20px; color: #666;">للاستفسار والدعم، يرجى التواصل مع مسؤول الميدان البروفيسور رفاف لخضر.</p></div><div class="footer"><p>© 2026 جامعة محمد البشير الإبراهيمي</p></div></div></body></html>
"""
        msg = MIMEMultipart('alternative')
        msg['From'] = EMAIL_SENDER; msg['To'] = prof_email
        msg['Subject'] = f"✅ تسجيل مذكرة جديدة - رقم {memo_info['رقم المذكرة']}"
        msg.attach(MIMEText(email_body, 'html', 'utf-8'))
        
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls(); server.login(EMAIL_SENDER, EMAIL_PASSWORD); server.send_message(msg)
        logger.info(f"✅ Email sent to professor {prof_name}")
        return True, "تم إرسال البريد الإلكتروني بنجاح"
    except Exception as e:
        logger.error(f"❌ Error sending email: {str(e)}")
        return False, f"خطأ تقني أثناء الإرسال: {str(e)}"

def _email_style():
    return """<style>
body{font-family:'Arial',sans-serif;background:#f4f4f4;padding:20px;direction:rtl;text-align:right;}
.container{background:#fff;padding:30px;border-radius:10px;box-shadow:0 2px 10px rgba(0,0,0,.1);max-width:600px;margin:auto;}
.header{background:#2F6F7E;color:#fff;padding:20px;border-radius:8px;text-align:center;margin-bottom:20px;}
.header h2{margin:0;font-size:1.4rem;}
.info-box{background:#f0f9ff;padding:15px;border-right:4px solid #2F6F7E;margin:15px 0;border-radius:8px;}
.action-box{background:#fff8e1;padding:15px;border-right:4px solid #F59E0B;margin:15px 0;border-radius:8px;}
.success-box{background:#f0fdf4;padding:15px;border-right:4px solid #10B981;margin:15px 0;border-radius:8px;}
.warning-box{background:#fff1f2;padding:15px;border-right:4px solid #EF4444;margin:15px 0;border-radius:8px;}
.platform-btn{display:inline-block;background:#2F6F7E;color:#fff!important;padding:12px 28px;border-radius:8px;text-decoration:none;font-weight:bold;margin-top:10px;}
.footer{text-align:center;color:#888;font-size:12px;margin-top:30px;border-top:1px solid #eee;padding-top:15px;}
p{color:#333;line-height:1.7;}
</style>"""

def send_deposit_email_to_professor(prof_name, memo_number, memo_title, student1_name, student2_name=None):
    """إرسال إيميل للأستاذ المشرف + الإدارة عند إيداع المذكرة"""
    try:
        df_profs = load_prof_memos()
        prof_rows = df_profs[df_profs["الأستاذ"].astype(str).str.strip() == prof_name.strip()]
        if prof_rows.empty:
            logger.warning(f"لم يتم العثور على بريد الأستاذ: {prof_name}")
            return False, "لم يتم العثور على بريد الأستاذ"
        prof_email = get_email_smart(prof_rows.iloc[0])
        if not prof_email:
            return False, "البريد الإلكتروني للأستاذ غير متوفر"

        students_html = f"<p>👤 <strong>الطالب الأول:</strong> {student1_name}</p>"
        if student2_name and student2_name.strip() and student2_name != student1_name:
            students_html += f"<p>👤 <strong>الطالب الثاني:</strong> {student2_name}</p>"

        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')

        email_body = f"""<html dir="rtl">
<head>
<meta charset="UTF-8">
{_email_style()}
</head>
<body>
<div class="container">
  <div class="header">
    <h2>📥 إيداع مذكرة — بانتظار موافقتكم</h2>
    <p style="color:rgba(255,255,255,0.85); margin:5px 0 0 0; font-size:0.9rem;">جامعة محمد البشير الإبراهيمي — كلية الحقوق والعلوم السياسية</p>
  </div>

  <p>تحية طيبة، الأستاذ(ة) الفاضل(ة) <strong>{prof_name}</strong>،</p>
  <p>نحيطكم علماً بأن الطالب(ة) أودع/أودعا نسخة المذكرة النهائية عبر المنصة، وهي بانتظار مراجعتكم والموافقة عليها.</p>

  <div class="info-box">
    <p>📄 <strong>رقم المذكرة:</strong> {memo_number}</p>
    <p>📑 <strong>عنوان المذكرة:</strong> {memo_title}</p>
    {students_html}
    <p>🕒 <strong>تاريخ الإيداع:</strong> {timestamp}</p>
  </div>

  <div class="action-box">
    <p>⚠️ <strong>مطلوب منكم:</strong> الدخول إلى المنصة، مراجعة المذكرة المودعة، والموافقة عليها لتصبح <strong style="color:#10B981;">قابلة للمناقشة</strong>.</p>
    <p>🔒 يمكنكم الاطلاع على الملف حصراً من خلال <strong>فضاء الأساتذة في المنصة</strong>.</p>
    <p>📌 هذه النسخة هي التي ستُناقَش رسمياً ولا يمكن تغييرها إلا بموافقة الإدارة.</p>
  </div>

  <div style="text-align:center; margin:25px 0;">
    <a href="https://memoires2026.streamlit.app" style="
      display:inline-block;
      background:#2F6F7E;
      color:#ffffff !important;
      padding:15px 35px;
      border-radius:10px;
      text-decoration:none;
      font-size:1.1rem;
      font-weight:bold;
      letter-spacing:0.3px;
      box-shadow:0 4px 12px rgba(47,111,126,0.4);">
      🔗 الدخول إلى المنصة للمراجعة والموافقة
    </a>
  </div>

  <div class="footer">
    <p>مسؤول الميدان: البروفيسور لخضر رفاف</p>
    <p>جامعة محمد البشير الإبراهيمي - كلية الحقوق والعلوم السياسية</p>
  </div>
</div>
</body></html>"""

        # إرسال منفصل للأستاذ وللإدارة لتجنب تقسيم Gmail
        for recipient in [prof_email, ADMIN_EMAIL]:
            msg = MIMEMultipart('alternative')
            msg['From'] = EMAIL_SENDER
            msg['To'] = recipient
            msg['Subject'] = f"📥 إيداع مذكرة للمراجعة — رقم {memo_number}"
            msg.attach(MIMEText(email_body, 'html', 'utf-8'))
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(EMAIL_SENDER, EMAIL_PASSWORD)
                server.send_message(msg)

        logger.info(f"✅ تم إرسال إيميل الإيداع للأستاذ {prof_name} + الإدارة")
        return True, "✅ تم إرسال إشعار للأستاذ المشرف والإدارة"
    except Exception as e:
        logger.error(f"خطأ في إرسال إيميل الإيداع: {e}")
        return False, f"❌ فشل إرسال الإيميل: {str(e)}"


def send_approval_email_to_students(memo_number, memo_title, prof_name, student1_data, student2_data=None):
    """إرسال إيميل للطالب(ين) عند موافقة الأستاذ"""
    try:
        recipients = []
        student_names = []
        for s in [student1_data, student2_data]:
            if s is None: continue
            email = get_email_smart(s)
            if email: recipients.append(email)
            lname, fname = get_student_name_display(s)
            student_names.append(f"{lname} {fname}".strip())

        if not recipients:
            return False, "لا يوجد بريد إلكتروني للطلبة"

        students_str = " و ".join(student_names)
        email_body = f"""<html dir="rtl"><head>{_email_style()}</head>
<body><div class="container">
<div class="header"><h2>🟢 مذكرتك قابلة للمناقشة</h2></div>
<p>تحية طيبة، {students_str}،</p>
<p>يسعدنا إعلامكم بأن الأستاذ المشرف <strong>{prof_name}</strong> قد راجع مذكرتكم ووافق عليها، وأصبحت رسمياً <strong style="color:#10B981;">قابلة للمناقشة</strong>.</p>
<div class="success-box">
    <p>📄 <strong>رقم المذكرة:</strong> {memo_number}</p>
    <p>📑 <strong>عنوان المذكرة:</strong> {memo_title}</p>
    <p>👨‍🏫 <strong>المشرف:</strong> {prof_name}</p>
</div>
<div class="action-box">
    <p>📌 ستتلقون إشعاراً آخر من الإدارة بتاريخ وتوقيت ومكان المناقشة.</p>
    <p>يمكنكم متابعة حالة مذكرتكم في أي وقت عبر المنصة.</p>
</div>
<div style="text-align:center;">
    <a href="https://memoires2026.streamlit.app" class="platform-btn">🔗 متابعة على المنصة</a>
</div>
<div class="footer">
    <p>جامعة محمد البشير الإبراهيمي - كلية الحقوق والعلوم السياسية</p>
    <p>مسؤول الميدان: البروفيسور لخضر رفاف</p>
</div>
</div></body></html>"""

        msg = MIMEMultipart('alternative')
        msg['From'] = EMAIL_SENDER
        msg['To'] = recipients[0]
        if len(recipients) > 1: msg['Cc'] = ", ".join(recipients[1:])
        msg['Subject'] = f"🟢 مذكرتك قابلة للمناقشة — رقم {memo_number}"
        msg.attach(MIMEText(email_body, 'html', 'utf-8'))
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)
        return True, "✅ تم إرسال إشعار الموافقة للطلبة"
    except Exception as e:
        logger.error(f"خطأ في إرسال إيميل الموافقة: {e}")
        return False, f"❌ فشل إرسال الإيميل: {str(e)}"


def send_defense_schedule_email(memo_number, memo_title, prof_name, defense_date, defense_time, defense_room, student1_data, student2_data=None):
    """إرسال إيميل للطالب(ين) عند تحديد موعد المناقشة"""
    try:
        recipients = []
        student_names = []
        for s in [student1_data, student2_data]:
            if s is None: continue
            email = get_email_smart(s)
            if email: recipients.append(email)
            lname, fname = get_student_name_display(s)
            student_names.append(f"{lname} {fname}".strip())

        if not recipients:
            return False, "لا يوجد بريد إلكتروني للطلبة"

        students_str = " و ".join(student_names)
        email_body = f"""<html dir="rtl"><head>{_email_style()}</head>
<body><div class="container">
<div class="header"><h2>📅 موعد مناقشة مذكرتك</h2></div>
<p>تحية طيبة، {students_str}،</p>
<p>يسعدنا إعلامكم بأنه تم تحديد موعد مناقشة مذكرتكم رسمياً.</p>
<div class="info-box">
    <p>📄 <strong>رقم المذكرة:</strong> {memo_number}</p>
    <p>📑 <strong>عنوان المذكرة:</strong> {memo_title}</p>
    <p>👨‍🏫 <strong>المشرف:</strong> {prof_name}</p>
</div>
<div class="success-box">
    <p>📆 <strong>تاريخ المناقشة:</strong> <span style="font-size:1.1rem;color:#10B981;">{defense_date}</span></p>
    <p>🕐 <strong>التوقيت:</strong> <span style="font-size:1.1rem;color:#10B981;">{defense_time}</span></p>
    <p>🏛️ <strong>القاعة:</strong> <span style="font-size:1.1rem;color:#10B981;">{defense_room}</span></p>
</div>
<div class="warning-box">
    <p>⚠️ يرجى الحضور قبل الموعد بـ 15 دقيقة على الأقل مع إحضار جميع الوثائق المطلوبة.</p>
</div>
<div style="text-align:center;">
    <a href="https://memoires2026.streamlit.app" class="platform-btn">🔗 متابعة على المنصة</a>
</div>
<div class="footer">
    <p>جامعة محمد البشير الإبراهيمي - كلية الحقوق والعلوم السياسية</p>
    <p>مسؤول الميدان: البروفيسور لخضر رفاف</p>
</div>
</div></body></html>"""

        msg = MIMEMultipart('alternative')
        msg['From'] = EMAIL_SENDER
        msg['To'] = recipients[0]
        if len(recipients) > 1: msg['Cc'] = ", ".join(recipients[1:])
        msg['Bcc'] = ADMIN_EMAIL
        msg['Subject'] = f"📅 موعد مناقشة مذكرتك — رقم {memo_number}"
        msg.attach(MIMEText(email_body, 'html', 'utf-8'))
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)
        return True, "✅ تم إرسال موعد المناقشة للطلبة"
    except Exception as e:
        logger.error(f"خطأ في إرسال إيميل المناقشة: {e}")
        return False, f"❌ فشل إرسال الإيميل: {str(e)}"

def save_approval_declaration(memo_number, prof_name, signature, declaration_text):
    """حفظ تصريح الأستاذ في Sheets — عمود AB"""
    try:
        df_memos = load_memos()
        memo_row = df_memos[df_memos["رقم المذكرة"].astype(str).apply(normalize_text) == normalize_text(memo_number)]
        if memo_row.empty:
            return False, "❌ المذكرة غير موجودة"
        row_idx = memo_row.index[0] + 2
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        declaration_full = f"تصريح: {prof_name} | توقيع: {signature} | {timestamp} | {declaration_text}"
        sheets_service.spreadsheets().values().update(
            spreadsheetId=MEMOS_SHEET_ID,
            range=f"Feuille 1!AB{row_idx}",
            valueInputOption="USER_ENTERED",
            body={"values": [[declaration_full]]}
        ).execute()
        return True, "✅ تم حفظ التصريح"
    except Exception as e:
        logger.error(f"Save declaration error: {e}")
        return False, f"❌ خطأ: {str(e)}"
    """الإدارة تعيد فتح الإيداع للطالب"""
    try:
        df_memos = load_memos()
        memo_row = df_memos[df_memos["رقم المذكرة"].astype(str).apply(normalize_text) == normalize_text(memo_number)]
        if memo_row.empty:
            return False, "❌ المذكرة غير موجودة"
        row_idx = memo_row.index[0] + 2
        updates = [
            {"range": f"Feuille 1!V{row_idx}", "values": [[""]]},
            {"range": f"Feuille 1!W{row_idx}", "values": [[""]]},
            {"range": f"Feuille 1!X{row_idx}", "values": [[""]]},
        ]
        sheets_service.spreadsheets().values().batchUpdate(
            spreadsheetId=MEMOS_SHEET_ID,
            body={"valueInputOption": "USER_ENTERED", "data": updates}
        ).execute()
        clear_cache_and_reload()
        return True, "✅ تم إعادة فتح الإيداع للطالب"
    except Exception as e:
        logger.error(f"Reset deposit error: {e}")
        return False, f"❌ خطأ: {str(e)}"

# ============================================================
# دوال إيداع المذكرات
# ============================================================
def upload_memo_to_drive(pdf_bytes, memo_number, memo_title):
    """رفع PDF إلى Google Drive وإرجاع الرابط"""
    if drive_service is None:
        return False, "", "❌ خدمة Drive غير متاحة"
    try:
        # تنظيف اسم الملف
        safe_title = re.sub(r'[\\/:*?"<>|]', '', str(memo_title).strip())
        file_name = f"{memo_number}.{safe_title}.pdf"
        
        # حذف أي ملف سابق بنفس رقم المذكرة
        existing = drive_service.files().list(
            q=f"'{DRIVE_UPLOAD_FOLDER_ID}' in parents and name contains '{memo_number}.' and trashed=false",
            fields="files(id, name)"
        ).execute()
        for f in existing.get('files', []):
            drive_service.files().delete(fileId=f['id']).execute()
        
        # رفع الملف الجديد
        file_metadata = {
            'name': file_name,
            'parents': [DRIVE_UPLOAD_FOLDER_ID]
        }
        media = MediaIoBaseUpload(io.BytesIO(pdf_bytes), mimetype='application/pdf', resumable=True)
        uploaded = drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink'
        ).execute()
        
        file_id = uploaded.get('id')
        # جعل الملف قابلاً للقراءة للجميع
        drive_service.permissions().create(
            fileId=file_id,
            body={'type': 'anyone', 'role': 'reader'}
        ).execute()
        
        link = uploaded.get('webViewLink', f"https://drive.google.com/file/d/{file_id}/view")
        return True, link, "✅ تم رفع الملف بنجاح"
    except Exception as e:
        logger.error(f"Drive upload error: {e}")
        return False, "", f"❌ خطأ في رفع الملف: {str(e)}"

def save_memo_deposit(memo_number, file_link):
    """حفظ حالة الإيداع ورابط الملف في Sheets (أعمدة V و W و X)"""
    try:
        df_memos = load_memos()
        memo_row = df_memos[df_memos["رقم المذكرة"].astype(str).apply(normalize_text) == normalize_text(memo_number)]
        if memo_row.empty:
            return False, "❌ المذكرة غير موجودة"
        row_idx = memo_row.index[0] + 2
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
        updates = [
            {"range": f"Feuille 1!V{row_idx}", "values": [["مودعة"]]},
            {"range": f"Feuille 1!W{row_idx}", "values": [[file_link]]},
            {"range": f"Feuille 1!X{row_idx}", "values": [[timestamp]]},
        ]
        sheets_service.spreadsheets().values().batchUpdate(
            spreadsheetId=MEMOS_SHEET_ID,
            body={"valueInputOption": "USER_ENTERED", "data": updates}
        ).execute()
        clear_cache_and_reload()
        return True, "✅ تم حفظ الإيداع بنجاح"
    except Exception as e:
        logger.error(f"Save deposit error: {e}")
        return False, f"❌ خطأ: {str(e)}"

def approve_memo_for_defense(memo_number):
    """الأستاذ يوافق على المذكرة → قابلة للمناقشة"""
    try:
        df_memos = load_memos()
        memo_row = df_memos[df_memos["رقم المذكرة"].astype(str).apply(normalize_text) == normalize_text(memo_number)]
        if memo_row.empty:
            return False, "❌ المذكرة غير موجودة"
        row_idx = memo_row.index[0] + 2
        sheets_service.spreadsheets().values().update(
            spreadsheetId=MEMOS_SHEET_ID,
            range=f"Feuille 1!V{row_idx}",
            valueInputOption="USER_ENTERED",
            body={"values": [["قابلة للمناقشة"]]}
        ).execute()
        clear_cache_and_reload()
        return True, "✅ تمت الموافقة على المذكرة"
    except Exception as e:
        logger.error(f"Approve memo error: {e}")
        return False, f"❌ خطأ: {str(e)}"

def save_defense_schedule(memo_number, defense_date, defense_time, defense_room):
    """الإدارة تحدد موعد ومكان المناقشة (أعمدة Y و Z و AA)"""
    try:
        df_memos = load_memos()
        memo_row = df_memos[df_memos["رقم المذكرة"].astype(str).apply(normalize_text) == normalize_text(memo_number)]
        if memo_row.empty:
            return False, "❌ المذكرة غير موجودة"
        row_idx = memo_row.index[0] + 2
        updates = [
            {"range": f"Feuille 1!Y{row_idx}", "values": [[str(defense_date)]]},
            {"range": f"Feuille 1!Z{row_idx}", "values": [[str(defense_time)]]},
            {"range": f"Feuille 1!AA{row_idx}", "values": [[defense_room]]},
        ]
        sheets_service.spreadsheets().values().batchUpdate(
            spreadsheetId=MEMOS_SHEET_ID,
            body={"valueInputOption": "USER_ENTERED", "data": updates}
        ).execute()
        clear_cache_and_reload()
        return True, "✅ تم حفظ موعد المناقشة"
    except Exception as e:
        logger.error(f"Save defense schedule error: {e}")
        return False, f"❌ خطأ: {str(e)}"


# ============================================================
# دوال اللجان والبرنامج والنشر
# ============================================================

def load_rooms():
    try:
        result = sheets_service.spreadsheets().values().get(
            spreadsheetId=MEMOS_SHEET_ID, range="القاعات!A1:C100"
        ).execute()
        values = result.get('values', [])
        if not values: return pd.DataFrame(columns=["إسم القاعة","الطابق","ملاحظات"])
        headers = values[0]
        rows = values[1:]
        padded = [r + ['']*(len(headers)-len(r)) for r in rows]
        return pd.DataFrame(padded, columns=headers)
    except Exception as e:
        logger.error(f"خطأ في تحميل القاعات: {e}")
        return pd.DataFrame(columns=["إسم القاعة","الطابق","ملاحظات"])

def save_jury(memo_number, president, examiner1, examiner2):
    """حفظ أعضاء اللجنة في أعمدة AC AD AE"""
    try:
        df_memos = load_memos()
        row = df_memos[df_memos["رقم المذكرة"].astype(str).apply(normalize_text) == normalize_text(memo_number)]
        if row.empty: return False, "❌ المذكرة غير موجودة"
        row_idx = row.index[0] + 2
        updates = [
            {"range": f"Feuille 1!AC{row_idx}", "values": [[president]]},
            {"range": f"Feuille 1!AD{row_idx}", "values": [[examiner1]]},
            {"range": f"Feuille 1!AE{row_idx}", "values": [[examiner2]]},
        ]
        sheets_service.spreadsheets().values().batchUpdate(
            spreadsheetId=MEMOS_SHEET_ID,
            body={"valueInputOption": "USER_ENTERED", "data": updates}
        ).execute()
        clear_cache_and_reload()
        return True, "✅ تم حفظ اللجنة"
    except Exception as e:
        return False, f"❌ {str(e)}"

def save_notes_by_member(memo_number, member_role, notes_text):
    """حفظ ملاحظات عضو اللجنة — AG رئيس / AH مناقش1 / AI مناقش2"""
    col_map = {"رئيس": "AG", "مناقش1": "AH", "مناقش2": "AI"}
    col = col_map.get(member_role)
    if not col: return False, "دور غير معروف"
    try:
        df_memos = load_memos()
        row = df_memos[df_memos["رقم المذكرة"].astype(str).apply(normalize_text) == normalize_text(memo_number)]
        if row.empty: return False, "❌ المذكرة غير موجودة"
        row_idx = row.index[0] + 2
        sheets_service.spreadsheets().values().update(
            spreadsheetId=MEMOS_SHEET_ID,
            range=f"Feuille 1!{col}{row_idx}",
            valueInputOption="USER_ENTERED",
            body={"values": [[notes_text]]}
        ).execute()
        clear_cache_and_reload()
        return True, "✅ تم حفظ الملاحظات"
    except Exception as e:
        return False, f"❌ {str(e)}"

def publish_memos(memo_numbers=None):
    """نشر مذكرات محددة أو كل المذكرات القابلة للمناقشة — عمود AF"""
    try:
        df_memos = load_memos()
        if memo_numbers:
            targets = df_memos[df_memos["رقم المذكرة"].astype(str).apply(normalize_text).isin(
                [normalize_text(m) for m in memo_numbers]
            )]
        else:
            targets = df_memos[df_memos.get("حالة الإيداع", pd.Series(dtype=str)).astype(str).str.strip() == "قابلة للمناقشة"] if "حالة الإيداع" in df_memos.columns else pd.DataFrame()
        if targets.empty: return False, "لا توجد مذكرات للنشر"
        updates = []
        for idx in targets.index:
            row_idx = idx + 2
            updates.append({"range": f"Feuille 1!AF{row_idx}", "values": [["نعم"]]})
        sheets_service.spreadsheets().values().batchUpdate(
            spreadsheetId=MEMOS_SHEET_ID,
            body={"valueInputOption": "USER_ENTERED", "data": updates}
        ).execute()
        clear_cache_and_reload()
        return True, f"✅ تم نشر {len(updates)} مذكرة"
    except Exception as e:
        return False, f"❌ {str(e)}"

def generate_schedule(rooms_list, start_date_str="2026-05-24", end_date_str="2026-06-04"):
    """توليد برنامج المناقشات تلقائياً"""
    from datetime import date as date_type, timedelta
    import random

    df_memos = load_memos()
    # المذكرات القابلة للمناقشة ولديها لجنة كاملة
    col_deposit = "حالة الإيداع"
    if col_deposit not in df_memos.columns:
        return False, "لا توجد أعمدة إيداع", pd.DataFrame()

    ready = df_memos[
        (df_memos[col_deposit].astype(str).str.strip() == "قابلة للمناقشة") &
        (df_memos.get("AC", pd.Series(dtype=str)).astype(str).str.strip().notna()) &
        (df_memos.get("AC", pd.Series(dtype=str)).astype(str).str.strip() != "") &
        (df_memos.get("AC", pd.Series(dtype=str)).astype(str).str.strip() != "nan")
    ] if "AC" in df_memos.columns else df_memos[df_memos[col_deposit].astype(str).str.strip() == "قابلة للمناقشة"]

    if ready.empty:
        return False, "لا توجد مذكرات جاهزة (قابلة للمناقشة + لجنة مكتملة)", pd.DataFrame()

    # بناء قائمة الأيام (أحد→خميس فقط)
    start = date_type.fromisoformat(start_date_str)
    end   = date_type.fromisoformat(end_date_str)
    work_days = []
    d = start
    while d <= end:
        if d.weekday() in [0,1,2,3,6]:  # Mon-Thu + Sun
            work_days.append(d)
        d += timedelta(days=1)

    # الحصص: 9:00 → كل 90 دقيقة
    slots = ["09:00","10:30","12:00","13:30","15:00","16:30"]

    # تتبع جدول كل أستاذ: {prof: {day: [slot_indices]}}
    prof_schedule = {}  # prof -> {day_str -> [slot_idx]}
    # تتبع القاعات: {day_str -> {slot_idx -> room}}
    room_schedule = {}  # day_str -> {slot_idx -> set of used rooms}

    results = []
    unscheduled = []

    def get_prof_slots(prof, day_str):
        return prof_schedule.setdefault(prof, {}).setdefault(day_str, [])

    def is_consecutive_pair(slots_used):
        """هل يوجد اثنتان متتاليتان؟"""
        for i in range(len(slots)-1):
            if i in slots_used and (i+1) in slots_used:
                return True
        return False

    for _, memo in ready.iterrows():
        memo_num = str(memo.get("رقم المذكرة","")).strip()
        supervisor = str(memo.get("الأستاذ","")).strip()
        president  = str(memo.get("AC","")).strip() if "AC" in memo.index else ""
        exam1      = str(memo.get("AD","")).strip() if "AD" in memo.index else ""
        exam2      = str(memo.get("AE","")).strip() if "AE" in memo.index else ""
        members    = [m for m in [supervisor, president, exam1, exam2] if m and m != "nan"]

        placed = False
        for day in work_days:
            day_str = str(day)
            room_day = room_schedule.setdefault(day_str, {})

            for slot_idx, slot_time in enumerate(slots):
                # تحقق 1: لا يوجد عضو في نفس الوقت
                conflict = False
                for m in members:
                    if slot_idx in get_prof_slots(m, day_str):
                        conflict = True; break
                if conflict: continue

                # تحقق 2: لم يتجاوز أي عضو 3 مناقشات اليوم
                over_limit = False
                for m in members:
                    if len(get_prof_slots(m, day_str)) >= 3:
                        over_limit = True; break
                if over_limit: continue

                # تحقق 3: لم يكن لأي عضو مناقشتان متتاليتان قبلها مباشرة
                consec_block = False
                for m in members:
                    used = get_prof_slots(m, day_str)
                    # إضافة مؤقتة للتحقق
                    test_used = used + [slot_idx]
                    # هل ستكون 3 متتالية؟
                    sorted_used = sorted(test_used)
                    for i in range(len(sorted_used)-2):
                        if sorted_used[i+1] == sorted_used[i]+1 and sorted_used[i+2] == sorted_used[i]+2:
                            consec_block = True; break
                    if consec_block: break
                if consec_block: continue

                # تحقق 4: قاعة متاحة
                used_rooms = room_day.get(slot_idx, set())
                available_rooms = [r for r in rooms_list if r not in used_rooms]
                if not available_rooms: continue

                # تعيين أول قاعة متاحة
                chosen_room = available_rooms[0]

                # حجز
                for m in members:
                    get_prof_slots(m, day_str).append(slot_idx)
                room_day.setdefault(slot_idx, set()).add(chosen_room)

                results.append({
                    "رقم المذكرة": memo_num,
                    "عنوان المذكرة": str(memo.get("عنوان المذكرة","")),
                    "التخصص": str(memo.get("التخصص","")),
                    "المشرف": supervisor,
                    "الرئيس": president,
                    "المناقش1": exam1,
                    "المناقش2": exam2,
                    "تاريخ المناقشة": day_str,
                    "توقيت المناقشة": slot_time,
                    "القاعة": chosen_room,
                })
                placed = True
                break
            if placed: break

        if not placed:
            unscheduled.append(memo_num)

    df_result = pd.DataFrame(results)
    msg = f"✅ تم جدولة {len(results)} مذكرة"
    if unscheduled:
        msg += f"\n⚠️ لم يتم جدولة {len(unscheduled)} مذكرة: {', '.join(unscheduled)}"
    return True, msg, df_result

def save_schedule_to_sheets(df_schedule):
    """حفظ البرنامج المولّد في Sheets"""
    try:
        df_memos = load_memos()
        updates = []
        for _, row in df_schedule.iterrows():
            memo_num = normalize_text(str(row["رقم المذكرة"]))
            memo_row = df_memos[df_memos["رقم المذكرة"].astype(str).apply(normalize_text) == memo_num]
            if memo_row.empty: continue
            row_idx = memo_row.index[0] + 2
            updates += [
                {"range": f"Feuille 1!Y{row_idx}",  "values": [[str(row["تاريخ المناقشة"])]]},
                {"range": f"Feuille 1!Z{row_idx}",  "values": [[str(row["توقيت المناقشة"])]]},
                {"range": f"Feuille 1!AA{row_idx}", "values": [[str(row["القاعة"])]]},
            ]
        if updates:
            sheets_service.spreadsheets().values().batchUpdate(
                spreadsheetId=MEMOS_SHEET_ID,
                body={"valueInputOption": "USER_ENTERED", "data": updates}
            ).execute()
            clear_cache_and_reload()
            return True, f"✅ تم حفظ {len(updates)//3} موعد في Sheets"
        return False, "لا يوجد شيء للحفظ"
    except Exception as e:
        return False, f"❌ {str(e)}"

def clear_schedule_from_sheets():
    """مسح التوقيتات فقط (Y Z AA) لإعادة التوليد"""
    try:
        df_memos = load_memos()
        col_deposit = "حالة الإيداع"
        if col_deposit not in df_memos.columns: return False, "لا يوجد عمود إيداع"
        targets = df_memos[df_memos[col_deposit].astype(str).str.strip() == "قابلة للمناقشة"]
        updates = []
        for idx in targets.index:
            row_idx = idx + 2
            updates += [
                {"range": f"Feuille 1!Y{row_idx}",  "values": [[""]]},
                {"range": f"Feuille 1!Z{row_idx}",  "values": [[""]]},
                {"range": f"Feuille 1!AA{row_idx}", "values": [[""]]},
            ]
        if updates:
            sheets_service.spreadsheets().values().batchUpdate(
                spreadsheetId=MEMOS_SHEET_ID,
                body={"valueInputOption": "USER_ENTERED", "data": updates}
            ).execute()
            clear_cache_and_reload()
        return True, "✅ تم مسح البرنامج السابق"
    except Exception as e:
        return False, f"❌ {str(e)}"

# ---------------- دوال التحقق (محدثة) ----------------
def verify_student(username, password, df_students):
    valid, result = validate_username(username)
    if not valid: return False, result
    username = result
    password = sanitize_input(password)
    if df_students.empty: return False, "❌ خطأ في تحميل بيانات الطلاب"
    
    # التحقق من وجود العمود أولاً
    if "اسم المستخدم" not in df_students.columns:
        return False, "❌ خطأ في بنية البيانات: عمود اسم المستخدم غير موجود"

    # التصحيح: تطبيق normalize_text على العمود بأكمله قبل المقارنة
    # هذا يضمن إزالة .0 والمسافات الزائدة من القيم الرقمية
    db_usernames = df_students["اسم المستخدم"].astype(str).apply(normalize_text)
    
    # إنشاء قناع (mask) للمطابقة
    student_mask = db_usernames == username
    
    student = df_students[student_mask]
    
    if student.empty: return False, "❌ اسم المستخدم غير موجود"
    
    # التحقق من كلمة السر
    db_password = str(student.iloc[0]["كلمة السر"]).strip()
    if db_password != password: return False, "❌ كلمة السر غير صحيحة"
    
    return True, student.iloc[0].to_dict()

def verify_students_batch(students_data, df_students):
    verified_students = []
    for username, password in students_data:
        if not username: continue
        valid, student = verify_student(username, password, df_students)
        if not valid: return False, student
        verified_students.append(student)
    return True, verified_students

def verify_professor(username, password, df_prof_memos):
    username = sanitize_input(username); password = sanitize_input(password)
    if df_prof_memos.empty: return False, "❌ خطأ في تحميل بيانات الأساتذة"
    
    required_cols = ["إسم المستخدم", "كلمة المرور"]
    if any(col not in df_prof_memos.columns for col in required_cols): 
        return False, f"❌ الأعمدة التالية غير موجودة: {', '.join([col for col in required_cols if col not in df_prof_memos.columns])}"
    
    # التصحيح: تطبيق normalize_text هنا أيضاً
    db_prof_usernames = df_prof_memos["إسم المستخدم"].astype(str).apply(normalize_text)
    
    prof_mask = (db_prof_usernames == username) & (df_prof_memos["كلمة المرور"].astype(str).str.strip() == password)
    prof = df_prof_memos[prof_mask]
    
    if prof.empty: return False, "❌ اسم المستخدم أو كلمة السر غير صحيحة"
    return True, prof.iloc[0].to_dict()

def verify_admin(username, password):
    username = sanitize_input(username); password = sanitize_input(password)
    if username in ADMIN_CREDENTIALS and ADMIN_CREDENTIALS[username] == password: return True, username
    return False, "❌ بيانات الإدارة غير صحيحة"

def verify_professor_password(note_number, prof_password, df_memos, df_prof_memos):
    valid, result = validate_note_number(note_number)
    if not valid: return False, None, result
    note_number = result
    prof_password = sanitize_input(prof_password)
    if df_memos.empty or df_prof_memos.empty: return False, None, "❌ خطأ في تحميل البيانات"
    
    # التصحيح: normalize memo number
    memo_row = df_memos[df_memos["رقم المذكرة"].astype(str).apply(normalize_text) == note_number]
    if memo_row.empty: return False, None, "❌ رقم المذكرة غير موجود"
    
    memo_row = memo_row.iloc[0]
    if str(memo_row.get("تم التسجيل", "")).strip() == "نعم": return False, None, "❌ هذه المذكرة مسجلة مسبقاً"
    
    prof_row = df_prof_memos[(df_prof_memos["الأستاذ"].astype(str).str.strip() == memo_row["الأستاذ"].strip()) & (df_prof_memos["كلمة سر التسجيل"].astype(str).str.strip() == prof_password)]
    if prof_row.empty: return False, None, "❌ كلمة سر المشرف غير صحيحة"
    return True, prof_row.iloc[0].to_dict(), None

# ============================================================
# الدالة: تحديث التسجيل
# ============================================================
def update_registration(note_number, student1, student2=None, s2_new_phone=None, s2_new_nin=None):
    try:
        df_memos = load_memos()
        df_prof_memos = load_prof_memos()
        df_students = load_students()

        memo_data_main = df_memos[df_memos["رقم المذكرة"].astype(str).apply(normalize_text) == str(note_number).strip()]
        if memo_data_main.empty:
            return False, "❌ رقم المذكرة غير موجود في القائمة الرئيسية"
        
        prof_name = memo_data_main["الأستاذ"].iloc[0].strip()
        used_prof_password = st.session_state.prof_password.strip()
        
        potential_rows = df_prof_memos[
            (df_prof_memos["الأستاذ"].astype(str).str.strip() == prof_name) & 
            (df_prof_memos["كلمة سر التسجيل"].astype(str).str.strip() == used_prof_password)
        ]
        if potential_rows.empty: return False, "❌ بيانات الأستاذ أو كلمة السر غير متطابقة في شيت المتابعة"
        
        # Check if memo already registered in prof sheet to avoid duplicates
        target_row = potential_rows[potential_rows["رقم المذكرة"].astype(str).apply(normalize_text) == str(note_number).strip()]
        if target_row.empty:
            # If memo number not in prof sheet yet, find an empty slot (unregistered row)
            target_row = potential_rows[potential_rows["تم التسجيل"].astype(str).str.strip() != "نعم"]
            if target_row.empty: return False, "❌ خطأ: جميع المذكرات المخصصة لهذا الأستاذ مسجلة بالفعل."
            
        prof_row_idx = target_row.index[0] + 2 
        col_names = df_prof_memos.columns.tolist()
        
        s1_lname, s1_fname = get_student_name_display(student1)
        
        updates = [
            {"range": f"Feuille 1!{col_letter(col_names.index('الطالب الأول')+1)}{prof_row_idx}", "values": [[s1_lname + ' ' + s1_fname]]},
            {"range": f"Feuille 1!{col_letter(col_names.index('تم التسجيل')+1)}{prof_row_idx}", "values": [["نعم"]]},
            {"range": f"Feuille 1!{col_letter(col_names.index('تاريخ التسجيل')+1)}{prof_row_idx}", "values": [[datetime.now().strftime('%Y-%m-%d %H:%M')]]},
            {"range": f"Feuille 1!{col_letter(col_names.index('رقم المذكرة')+1)}{prof_row_idx}", "values": [[note_number]]}
        ]
        
        if student2 is not None:
            s2_lname, s2_fname = get_student_name_display(student2)
            updates.append({"range": f"Feuille 1!{col_letter(col_names.index('الطالب الثاني')+1)}{prof_row_idx}", "values": [[s2_lname + ' ' + s2_fname]]})
            
        sheets_service.spreadsheets().values().batchUpdate(spreadsheetId=PROF_MEMOS_SHEET_ID, body={"valueInputOption": "USER_ENTERED", "data": updates}).execute()
        
        # Update Main Memos Sheet
        memo_row_idx = df_memos[df_memos["رقم المذكرة"].astype(str).apply(normalize_text) == str(note_number).strip()].index[0] + 2
        memo_cols = df_memos.columns.tolist()
        
        reg1 = normalize_text(student1.get('رقم التسجيل', ''))
        reg2 = normalize_text(student2.get('رقم التسجيل', '')) if student2 else ""
        
        updates2 = [
            {"range": f"Feuille 1!{col_letter(memo_cols.index('الطالب الأول')+1)}{memo_row_idx}", "values": [[s1_lname + ' ' + s1_fname]]},
            {"range": f"Feuille 1!{col_letter(memo_cols.index('تم التسجيل')+1)}{memo_row_idx}", "values": [["نعم"]]},
            {"range": f"Feuille 1!{col_letter(memo_cols.index('تاريخ التسجيل')+1)}{memo_row_idx}", "values": [[datetime.now().strftime('%Y-%m-%d %H:%M')]]},
            {"range": f"Feuille 1!S{memo_row_idx}", "values": [[reg1]]}
        ]
        if 'كلمة سر التسجيل' in memo_cols: 
            updates2.append({"range": f"Feuille 1!{col_letter(memo_cols.index('كلمة سر التسجيل')+1)}{memo_row_idx}", "values": [[used_prof_password]]})
        if student2 is not None:
            updates2.append({"range": f"Feuille 1!{col_letter(memo_cols.index('الطالب الثاني')+1)}{memo_row_idx}", "values": [[s2_lname + ' ' + s2_fname]]})
            updates2.append({"range": f"Feuille 1!T{memo_row_idx}", "values": [[reg2]]})
            
        sheets_service.spreadsheets().values().batchUpdate(spreadsheetId=MEMOS_SHEET_ID, body={"valueInputOption": "USER_ENTERED", "data": updates2}).execute()
        
        # Update Students Sheet
        students_cols = df_students.columns.tolist()
        
        # Find student row using normalized username
        s1_user = normalize_text(student1.get('اسم المستخدم', ''))
        student1_row_idx = df_students[df_students["اسم المستخدم"].astype(str).apply(normalize_text) == s1_user].index[0] + 2
        sheets_service.spreadsheets().values().update(spreadsheetId=STUDENTS_SHEET_ID, range=f"Feuille 1!{col_letter(students_cols.index('رقم المذكرة')+1)}{student1_row_idx}", valueInputOption="USER_ENTERED", body={"values": [[note_number]]}).execute()
        
        if student2 is not None:
            s2_user = normalize_text(student2.get('اسم المستخدم', ''))
            student2_row_idx = df_students[df_students["اسم المستخدم"].astype(str).apply(normalize_text) == s2_user].index[0] + 2
            sheets_service.spreadsheets().values().update(spreadsheetId=STUDENTS_SHEET_ID, range=f"Feuille 1!{col_letter(students_cols.index('رقم المذكرة')+1)}{student2_row_idx}", valueInputOption="USER_ENTERED", body={"values": [[note_number]]}).execute()
            
            s2_updates = []
            if s2_new_phone:
                 s2_updates.append({"range": f"Feuille 1!M{student2_row_idx}", "values": [[s2_new_phone]]})
            if s2_new_nin:
                 s2_updates.append({"range": f"Feuille 1!U{student2_row_idx}", "values": [[s2_new_nin]]})
            
            if s2_updates:
                sheets_service.spreadsheets().values().batchUpdate(spreadsheetId=STUDENTS_SHEET_ID, body={"valueInputOption": "USER_ENTERED", "data": s2_updates}).execute()

        time.sleep(2)
        clear_cache_and_reload()
        time.sleep(1)
        
        df_students_updated = load_students()
        st.session_state.student1 = df_students_updated[df_students_updated["اسم المستخدم"].astype(str).apply(normalize_text) == s1_user].iloc[0].to_dict()
        if student2 is not None: 
            st.session_state.student2 = df_students_updated[df_students_updated["اسم المستخدم"].astype(str).apply(normalize_text) == s2_user].iloc[0].to_dict()
            
        memo_data = df_memos[df_memos["رقم المذكرة"].astype(str).apply(normalize_text) == str(note_number).strip()].iloc[0]
        email_sent, email_msg = send_email_to_professor(prof_name, memo_data, st.session_state.student1, st.session_state.student2 if student2 else None)
        if not email_sent: st.error(f"⚠️ {email_msg}"); st.warning("تم تسجيل المذكرة في النظام، لكن لم يتم إرسال الإيميل للأستاذ.")
        else: st.success("📧 تم إرسال إشعار بالبريد الإلكتروني للأستاذ.")
        
        return True, "✅ تم تسجيل المذكرة بنجاح!"
    except Exception as e:
        logger.error(f"خطأ في تحديث التسجيل: {str(e)}")
        return False, f"❌ حدث خطأ أثناء التسجيل: {str(e)}"

# ============================================================
# دالة تحديث ملف التخرج (للإدارة)
# ============================================================
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

# ============================================================
# جلب البيانات
# ============================================================
df_students = load_students(); df_memos = load_memos(); df_prof_memos = load_prof_memos(); df_requests = load_requests()
if df_students.empty or df_memos.empty or df_prof_memos.empty: st.error("❌ خطأ في تحميل البيانات. يرجى المحاولة لاحقاً."); st.stop()

# ============================================================
# دوال استعادة الجلسة
# ============================================================
def encode_str(s): return base64.urlsafe_b64encode(s.encode()).decode()
def decode_str(s): 
    try: return base64.urlsafe_b64decode(s.encode()).decode()
    except: return ""

def lookup_student(username):
    if df_students.empty: return None
    # Use normalized matching
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
                    if note_num:
                        memo_row = df_memos[df_memos["رقم المذكرة"].astype(str).apply(normalize_text) == note_num]
                        if not memo_row.empty:
                            memo_row = memo_row.iloc[0]
                            s2_name = str(memo_row.get("الطالب الثاني", "")).strip()
                            if s2_name and s2_name != "--":
                                current_reg = normalize_text(s_data.get('رقم التسجيل', ''))
                                s2_obj = load_student2_for_memo(memo_row, current_reg, df_students)
                                if s2_obj: st.session_state.student2 = s2_obj
                else:
                     st.session_state.user_type = 'student'
                     st.session_state.profile_incomplete = True
                     st.session_state.profile_user_temp = s_data
                     
        elif user_type == 'professor':
            # Normalize prof username check
            p_data = df_prof_memos[df_prof_memos["إسم المستخدم"].astype(str).apply(normalize_text) == normalize_text(username)]
            if not p_data.empty: st.session_state.professor = p_data.iloc[0].to_dict(); st.session_state.logged_in = True
        elif user_type == 'admin':
            if username in ADMIN_CREDENTIALS: st.session_state.admin_user = username; st.session_state.logged_in = True
        if user_type: st.session_state.user_type = user_type

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
    for key in keys_to_del:
         del st.session_state[key]
    for key, value in required_state.items():
        st.session_state[key] = value
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

# ============================================================
# فضاء الطلبة
# ============================================================
elif st.session_state.user_type == "student":
    if st.session_state.get('profile_incomplete', False):
        st.markdown("<h2>⚠️ استكمال الملف الشخصي</h2>", unsafe_allow_html=True)
        error_msg = st.session_state.get('profile_error_msg', "بيانات ناقصة")
        st.error(f"يجب إدخال المعلومات الناقصة:")
        st.markdown(f"<div style='background:rgba(255,0,0,0.1); padding:10px; border-radius:5px; color:#FF6B6B; margin-bottom:20px;'>{error_msg}</div>", unsafe_allow_html=True)
        temp_data = st.session_state.profile_user_temp
        
        with st.form("complete_profile_form"):
            st.markdown("<div class='card'>", unsafe_allow_html=True)
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
            st.markdown("</div>", unsafe_allow_html=True)

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
                            memo_row = df_memos[df_memos["رقم المذكرة"].astype(str).apply(normalize_text) == note_num]
                            if not memo_row.empty:
                                memo_row = memo_row.iloc[0]
                                s2_name = str(memo_row.get("الطالب الثاني", "")).strip()
                                if s2_name and s2_name != "--":
                                    current_reg = normalize_text(result.get('رقم التسجيل', ''))
                                    s2_obj = load_student2_for_memo(memo_row, current_reg, df_students)
                                    if s2_obj: st.session_state.student2 = s2_obj
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
            st.markdown("---")
            registration_type = st.radio("اختر نوع المذكرة:", ["فردية", "ثنائية"], horizontal=True)
            
            username2 = password2 = None
            student2_obj = None
            s2_missing_info = False
            s2_new_phone_val = ""
            s2_new_nin_val = ""

            if registration_type == "ثنائية":
                st.markdown("### 👥 بيانات الطالب الثاني")
                username2 = st.text_input("اسم المستخدم الطالب الثاني")
                password2 = st.text_input("كلمة السر الطالب الثاني", type="password")
                
                if username2 and password2:
                    v2, r2 = verify_student(username2, password2, df_students)
                    if v2:
                        student2_obj = r2
                        s2_phone = str(r2.get('الهاتف', '')).strip()
                        s2_nin = normalize_text(r2.get('NIN', ''))
                        s2_phone_ok, s2_phone_msg = is_phone_valid(s2_phone)
                        s2_nin_ok, s2_nin_msg = is_nin_valid(s2_nin)
                        if not s2_phone_ok or not s2_nin_ok:
                            s2_missing_info = True
                            st.warning(f"⚠️ الطالب الثاني ({r2.get('لقب')} {r2.get('إسم')}) لم يستكمل ملفه الشخصي. يرجى إدخال بياناته أدناه للمتابعة.")
                            s2_new_phone_val = st.text_input("📞 هاتف الطالب الثاني", value=s2_phone, key="s2_phone_input_new")
                            s2_new_nin_val = st.text_input("🆔 NIN الطالب الثاني", value=s2_nin, key="s2_nin_input_new")
                            if s2_new_phone_val and s2_new_nin_val:
                                tmp_ph_ok, _ = is_phone_valid(s2_new_phone_val)
                                tmp_nin_ok, _ = is_nin_valid(s2_new_nin_val)
                                if tmp_ph_ok and tmp_nin_ok: st.info("✅ بيانات الطالب الثاني جاهزة للحفظ عند التسجيل.")
                                else:
                                    st.error("❌ صيغة الهاتف أو NIN غير صحيحة للطالب الثاني.")
                                    student2_obj = None
                        else: st.success("✅ بيانات الطالب الثاني كاملة.")
                    else: st.error(r2)
            
            st.markdown("### 🔍 البحث عن مذكرة متاحة")
            student_specialty = str(s1.get("التخصص", "")).strip()
            
            def clean_text(val):
                v = str(val).strip()
                if v in ['', 'nan', 'None', 'NaN', '-', '0', '0.0']: return ''
                return v

            prof_counts = df_prof_memos.groupby("الأستاذ")["رقم المذكرة"].apply(
                lambda x: sum([1 for val in x if clean_text(val) != ''])
            ).to_dict()
            
            available_memos_df = df_memos[
                (df_memos["تم التسجيل"].astype(str).str.strip() != "نعم") & 
                (df_memos["التخصص"].astype(str).str.strip() == student_specialty)
            ]
            
            available_profs = []
            if not available_memos_df.empty:
                profs_in_list = available_memos_df["الأستاذ"].unique().tolist()
                for p in profs_in_list:
                    p_clean = str(p).strip()
                    count = prof_counts.get(p_clean, 0)
                    if count < 4: available_profs.append(p_clean)
            available_profs = sorted(list(set(available_profs)))
            
            if available_profs:
                selected_prof = st.selectbox("اختر الأستاذ المشرف:", [""] + available_profs)
                if selected_prof:
                    prof_specific_memos = available_memos_df[available_memos_df["الأستاذ"].astype(str).str.strip() == selected_prof.strip()]
                    if not prof_specific_memos.empty:
                        st.success(f'✅ لديك {len(prof_specific_memos)} خيار/خيارات متاحة:')
                        for _, row in prof_specific_memos.iterrows():
                            st.markdown(f"""
                            <div style="background: rgba(47, 111, 126, 0.15); border: 1px solid #2F6F7E; padding: 10px; border-radius: 8px; margin-bottom: 5px;">
                                <strong class="memo-card-title" style="color: #FFFFFF;">{row['رقم المذكرة']}</strong> - <span style="color: #FFFFFF;">{row['عنوان المذكرة']}</span>
                            </div>
                            """, unsafe_allow_html=True)
                    else: st.info("هذا الأستاذ ليس لديه عناوين متاحة حالياً في تخصصك.")
            else:
                st.warning("🔒 عذراً، لا يوجد أساتذة لديهم أماكن شاغرة (أقل من 4 مذكرات) في تخصصك حالياً.")
                st.info("يرجى التواصل مع مسؤول الميدان أو المحاولة لاحقاً.")
            
            st.markdown("---")
            st.markdown("### ✍️ تسجيل المذكرة المختارة")
            c1, c2 = st.columns([3, 1])
            with c1: st.session_state.note_number = st.text_input("رقم المذكرة", value=st.session_state.note_number)
            with c2: st.session_state.prof_password = st.text_input("كلمة سر المشرف", type="password")
            
            if not st.session_state.show_confirmation:
                if st.button("المتابعة للتأكيد"):
                    if not st.session_state.note_number or not st.session_state.prof_password: 
                        st.error("⚠️ يرجى إدخال بيانات المذكرة")
                    elif registration_type == "ثنائية" and not student2_obj:
                        st.error("❌ يرجى إدخال بيانات الطالب الثاني بشكل صحيح.")
                    elif s2_missing_info and (not s2_new_phone_val or not s2_new_nin_val):
                        st.error("❌ يرجى إدخال بيانات الطالب الثاني الناقصة (هاتف و NIN).")
                    else:
                        s1_reg_perm = str(s1.get('التسجيل', '')).strip()
                        if registration_type == "ثنائية":
                            s2 = student2_obj
                            s2_reg_perm = str(s2.get('التسجيل', '')).strip()
                            if s1_reg_perm != '1' and s2_reg_perm != '1':
                                st.error("⛔ عذراً، لم يتم السماح لك بتسجيل المذكرة في الوقت الحالي."); st.stop()
                        else:
                            fardiya_val = str(s1.get('فردية', '')).strip()
                            if fardiya_val not in ["1", "نعم"]: st.error("❌ لا يمكنك تسجيل مذكرة فردية"); st.stop()
                            if s1_reg_perm != '1': st.error("⛔ لم يتم السماح لك بتسجيل المذكرة في الوقت الحالي."); st.stop()

                        st.session_state.show_confirmation = True
                        st.session_state.s2_phone_input = s2_new_phone_val if s2_missing_info else ""
                        st.session_state.s2_nin_input = s2_new_nin_val if s2_missing_info else ""
                        st.rerun()
            else:
                st.warning(f"⚠️ تأكيد التسجيل - المذكرة رقم: {st.session_state.note_number}")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("تأكيد نهائي", type="primary"):
                        valid, prof_row, err = verify_professor_password(st.session_state.note_number, st.session_state.prof_password, df_memos, df_prof_memos)
                        if not valid: st.error(err); st.session_state.show_confirmation = False
                        else:
                            with st.spinner('⏳ جاري تسجيل...'):
                                s2_to_pass = student2_obj if registration_type == "ثنائية" else None
                                success, msg = update_registration(
                                    st.session_state.note_number, 
                                    s1, 
                                    s2_to_pass, 
                                    st.session_state.s2_phone_input, 
                                    st.session_state.s2_nin_input
                                )
                            if success: 
                                st.success(msg); st.balloons(); 
                                clear_cache_and_reload(); 
                                st.session_state.mode = "view"; 
                                st.session_state.show_confirmation = False; 
                                time.sleep(2); st.rerun()
                            else: st.error(msg); st.session_state.show_confirmation = False
                with col2:
                    if st.button("إلغاء"): st.session_state.show_confirmation = False; st.rerun()

        elif st.session_state.mode == "view":
            col1, col2 = st.columns([4, 1])
            with col2:
                if st.button("خروج", key="logout_btn"): logout()
            
            note_num = normalize_text(s1.get('رقم المذكرة', ''))
            df_memos_fresh = load_memos()
            memo_info = df_memos_fresh[df_memos_fresh["رقم المذكرة"].astype(str).apply(normalize_text) == note_num].iloc[0]

            tab_memo, tab_deposit, tab_track, tab_notify = st.tabs(["مذكرتي", "📤 إيداع المذكرة", "تتبع ملف الشهادة", "الإشعارات والطلبات"])
            
            with tab_memo:
                session_date = memo_info.get("موعد الجلسة القادمة", "")
                session_html = f"<p>📅 <b>موعد الجلسة القادمة:</b> {session_date}</p>" if session_date else ""
                st.markdown(f'''<div class="card" style="border-left: 5px solid #FFD700;"><h3>✅ أنت مسجل في المذكرة التالية:</h3><p><b>رقم المذكرة:</b> {memo_info['رقم المذكرة']}</p><p><b>العنوان:</b> {memo_info['عنوان المذكرة']}</p><p><b>المشرف:</b> {memo_info['الأستاذ']}</p><p><b>التخصص:</b> {memo_info['التخصص']}</p>{session_html}</div>''', unsafe_allow_html=True)

                # عرض موعد المناقشة ولجنة التحكيم إذا كانت منشورة
                is_published = str(memo_info.get("AF","")).strip() == "نعم" if "AF" in memo_info.index else False
                if is_published:
                    def_date_s = str(memo_info.get("تاريخ المناقشة","")).strip()
                    def_time_s = str(memo_info.get("توقيت المناقشة","")).strip()
                    def_room_s = str(memo_info.get("القاعة","")).strip()
                    president_s = str(memo_info.get("AC","")).strip() if "AC" in memo_info.index else ""
                    exam1_s = str(memo_info.get("AD","")).strip() if "AD" in memo_info.index else ""
                    exam2_s = str(memo_info.get("AE","")).strip() if "AE" in memo_info.index else ""
                    if def_date_s and def_date_s != "nan":
                        st.markdown(f"""
                        <div style="background:rgba(16,185,129,0.12); border:2px solid #10B981; border-radius:16px; padding:25px; margin-top:15px;">
                            <h4 style="color:#10B981; margin:0 0 15px 0;">🎓 برنامج المناقشة</h4>
                            <p>📆 <b>التاريخ:</b> <span style="color:#FFD700; font-size:1.1rem;">{def_date_s}</span></p>
                            <p>🕐 <b>التوقيت:</b> <span style="color:#FFD700; font-size:1.1rem;">{def_time_s}</span></p>
                            <p>🏛️ <b>القاعة:</b> <span style="color:#FFD700; font-size:1.1rem;">{def_room_s}</span></p>
                            <hr style="border-color:rgba(255,255,255,0.1); margin:15px 0;">
                            <h5 style="color:#94A3B8; margin:0 0 10px 0;">👥 أعضاء لجنة المناقشة</h5>
                            <p>🏛️ <b>الرئيس:</b> {president_s if president_s and president_s != 'nan' else '--'}</p>
                            <p>📋 <b>المناقش 1:</b> {exam1_s if exam1_s and exam1_s != 'nan' else '--'}</p>
                            <p>📋 <b>المناقش 2:</b> {exam2_s if exam2_s and exam2_s != 'nan' else '--'}</p>
                        </div>
                        """, unsafe_allow_html=True)
                
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
                    s2_lname, s2_fname = get_student_name_display(s2)
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

            with tab_track:
                st.subheader("📂 حالة ملف التخرج")
                def render_student_diploma_status(student_data, title):
                    if isinstance(student_data, dict):
                        cols = df_students.columns.tolist()
                        val_birth = student_data.get(cols[14]) if len(cols) > 14 else "غير محدد"
                        val_rel1 = student_data.get(cols[15]) if len(cols) > 15 else "غير محدد"
                        val_rel2 = student_data.get(cols[16]) if len(cols) > 16 else "غير محدد"
                        val_pv = student_data.get(cols[17]) if len(cols) > 17 else "غير محدد"
                        val_file = student_data.get(cols[18]) if len(cols) > 18 else "غير محدد"
                        val_dipl = student_data.get(cols[19]) if len(cols) > 19 else "غير محدد"
                    else:
                        vals = student_data.tolist()
                        val_birth = vals[14] if len(vals) > 14 else "غير محدد"
                        val_rel1 = vals[15] if len(vals) > 15 else "غير محدد"
                        val_rel2 = vals[16] if len(vals) > 16 else "غير محدد"
                        val_pv = vals[17] if len(vals) > 17 else "غير محدد"
                        val_file = vals[18] if len(vals) > 18 else "غير محدد"
                        val_dipl = vals[19] if len(vals) > 19 else "غير محدد"

                    def get_badge_color(val):
                        v = str(val).strip()
                        if v in ["متوفر", "مكتملة", "كامل", "كامل لحد الآن", "جاهز", "تم التسليم"]: return "status-available"
                        elif v in ["غير متوفر", "ناقص", "غير جاهز"]: return "status-unavailable"
                        else: return "status-pending"

                    html = f"""
                    <div class="card" style="border-right: 4px solid #2F6F7E;">
                        <h4 style="color:#FFD700; border-bottom:1px solid #444; padding-bottom:10px;">{title}</h4>
                        <div class="diploma-status-grid">
                            <div class="diploma-item"><span>📄 شهادة الميلاد</span><span class="status-badge {get_badge_color(val_birth)}">{val_birth}</span></div>
                            <div class="diploma-item"><span>📊 كشف نقاط (M1)</span><span class="status-badge {get_badge_color(val_rel1)}">{val_rel1}</span></div>
                            <div class="diploma-item"><span>📊 كشف نقاط (M2)</span><span class="status-badge {get_badge_color(val_rel2)}">{val_rel2}</span></div>
                            <div class="diploma-item"><span>📜 محضر المناقشة</span><span class="status-badge {get_badge_color(val_pv)}">{val_pv}</span></div>
                            <div class="diploma-item"><span>📂 حالة الملف</span><span class="status-badge {get_badge_color(val_file)}">{val_file}</span></div>
                            <div class="diploma-item"><span>🎓 حالة الشهادة</span><span class="status-badge {get_badge_color(val_dipl)}">{val_dipl}</span></div>
                        </div>
                    </div>
                    """
                    return html
                
                s1_lname, s1_fname = get_student_name_display(s1)
                st.markdown(render_student_diploma_status(s1, f"👤 {s1_lname} {s1_fname}"), unsafe_allow_html=True)
                st.info("ℹ️ ملاحظة: إذا كانت المذكرة ثنائية، سيظهر لك هنا فقط ملفك الشخصي. يتعين على الطالب الثاني الدخول بحسابه لمشاهدة ملفه.")

            with tab_deposit:
                st.subheader("📤 إيداع نسخة المذكرة")
                
                deposit_status = str(memo_info.get("حالة الإيداع", "")).strip()
                deposit_link = str(memo_info.get("رابط الملف", "")).strip()
                deposit_date = str(memo_info.get("تاريخ إيداع المذكرة", "")).strip()

                # عرض الحالة الحالية
                if deposit_status == "قابلة للمناقشة":
                    st.markdown("""
                    <div style="background: rgba(16,185,129,0.15); border: 2px solid #10B981; border-radius: 16px; padding: 25px; text-align: center; margin-bottom: 20px;">
                        <div style="font-size: 3rem;">🟢</div>
                        <h3 style="color: #10B981; margin: 10px 0;">قابلة للمناقشة</h3>
                        <p style="color: #94A3B8;">وافق المشرف على مذكرتك. بانتظار تحديد موعد المناقشة من الإدارة.</p>
                    </div>
                    """, unsafe_allow_html=True)
                    if deposit_link and deposit_link != "nan":
                        st.markdown(f"📎 [عرض الملف المودع]({deposit_link})")
                    if deposit_date and deposit_date != "nan":
                        st.caption(f"تاريخ الإيداع: {deposit_date}")
                    
                    # عرض موعد المناقشة إن وُجد
                    def_date = str(memo_info.get("تاريخ المناقشة", "")).strip()
                    def_time = str(memo_info.get("توقيت المناقشة", "")).strip()
                    def_room = str(memo_info.get("القاعة", "")).strip()
                    if def_date and def_date != "nan":
                        st.markdown(f"""
                        <div style="background: rgba(47,111,126,0.2); border: 1px solid #2F6F7E; border-radius: 12px; padding: 20px; margin-top: 15px;">
                            <h4 style="color:#FFD700;">📅 موعد المناقشة</h4>
                            <p>📆 التاريخ: <b>{def_date}</b></p>
                            <p>🕐 التوقيت: <b>{def_time if def_time and def_time != 'nan' else 'سيُحدد لاحقاً'}</b></p>
                            <p>🏛️ القاعة: <b>{def_room if def_room and def_room != 'nan' else 'سيُحدد لاحقاً'}</b></p>
                        </div>
                        """, unsafe_allow_html=True)

                elif deposit_status == "مودعة":
                    st.markdown("""
                    <div style="background: rgba(245,158,11,0.15); border: 2px solid #F59E0B; border-radius: 16px; padding: 25px; text-align: center; margin-bottom: 20px;">
                        <div style="font-size: 3rem;">🟡</div>
                        <h3 style="color: #F59E0B; margin: 10px 0;">في انتظار مراجعة المشرف</h3>
                        <p style="color: #94A3B8;">تم إيداع مذكرتك. بانتظار موافقة الأستاذ المشرف.</p>
                    </div>
                    """, unsafe_allow_html=True)
                    if deposit_date and deposit_date != "nan":
                        st.caption(f"تاريخ الإيداع: {deposit_date}")
                    st.markdown("""
                    <div style="background: rgba(239,68,68,0.1); border: 1px solid #EF4444; border-radius: 12px; padding: 20px; margin-top: 15px;">
                        <p style="color: #EF4444; font-weight: bold; margin: 0;">⛔ الإيداع نهائي ولا يمكن تعديله.</p>
                        <p style="color: #94A3B8; margin: 8px 0 0 0;">في حالة وجود خطأ، يرجى التواصل مع الإدارة مباشرة لإعادة فتح الإيداع.</p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    # لم يودع بعد
                    st.markdown("""
                    <div style="background: rgba(100,116,139,0.15); border: 1px solid #475569; border-radius: 16px; padding: 25px; text-align: center; margin-bottom: 20px;">
                        <div style="font-size: 3rem;">📄</div>
                        <h3 style="color: #94A3B8; margin: 10px 0;">لم تُودَع المذكرة بعد</h3>
                        <p style="color: #64748B;">ارفع نسخة PDF من مذكرتك النهائية لإرسالها للمشرف.</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    uploaded_pdf = st.file_uploader("📁 اختر ملف المذكرة (PDF فقط)", type=["pdf"], key="upload_pdf")
                    if uploaded_pdf:
                        file_size_mb = len(uploaded_pdf.read()) / (1024*1024)
                        uploaded_pdf.seek(0)
                        st.info(f"📊 حجم الملف: {file_size_mb:.1f} MB")
                        if file_size_mb > 50:
                            st.error("❌ حجم الملف يتجاوز 50 MB. يرجى ضغط الملف أولاً.")
                        else:
                            if st.button("📤 إيداع المذكرة", type="primary", use_container_width=True):
                                with st.spinner("⏳ جاري رفع الملف على Drive... قد يستغرق بضع ثوانٍ"):
                                    pdf_bytes = uploaded_pdf.read()
                                    ok, link, msg = upload_memo_to_drive(pdf_bytes, note_num, memo_info['عنوان المذكرة'])
                                    if ok:
                                        s, m = save_memo_deposit(note_num, link)
                                        if s:
                                            st.success("✅ تم إيداع مذكرتك بنجاح! ستُراجَع من قِبل المشرف.")
                                            # إرسال إيميل للأستاذ
                                            s1_lname, s1_fname = get_student_name_display(st.session_state.student1)
                                            student1_display = f"{s1_lname} {s1_fname}".strip()
                                            student2_display = ""
                                            # جلب الطالب الثاني بنفس منطق load_student2_for_memo
                                            current_reg_dep = normalize_text(st.session_state.student1.get('رقم التسجيل', ''))
                                            s2_obj_dep = load_student2_for_memo(memo_info, current_reg_dep, load_students())
                                            if s2_obj_dep:
                                                s2_lname, s2_fname = get_student_name_display(s2_obj_dep)
                                                student2_display = f"{s2_lname} {s2_fname}".strip()
                                            prof_name_dep = str(memo_info.get('الأستاذ','')).strip()
                                            email_ok, email_msg = send_deposit_email_to_professor(
                                                prof_name_dep, note_num, memo_info['عنوان المذكرة'],
                                                student1_display, student2_display
                                            )
                                            if email_ok:
                                                st.info("📧 تم إرسال إشعار للأستاذ المشرف والإدارة.")
                                            else:
                                                st.warning(f"⚠️ تم الإيداع لكن فشل إرسال الإيميل: {email_msg}")
                                            st.balloons()
                                            clear_cache_and_reload()
                                            time.sleep(2)
                                            st.rerun()
                                        else: st.error(m)
                                    else: st.error(msg)

            with tab_notify:
                st.subheader("تنبيهات خاصة بك")
                df_reqs = load_requests()
                my_memo_id = note_num
                if my_memo_id:
                    df_memos_fresh = load_memos()
                    my_memo_row = df_memos_fresh[df_memos_fresh["رقم المذكرة"].astype(str).apply(normalize_text) == my_memo_id]
                    if not my_memo_row.empty:
                        my_prof = str(my_memo_row.iloc[0]["الأستاذ"]).strip()
                        base_filter = df_reqs["النوع"] == "جلسة إشراف"
                        prof_filter = df_reqs["الأستاذ"].astype(str).str.strip() == my_prof
                        prof_sessions = df_reqs[base_filter & prof_filter]
                        if not prof_sessions.empty:
                            last_session = prof_sessions.iloc[-1]
                            details_display = ""; date_to_show = ""
                            try:
                                if len(last_session) > 8: 
                                    raw_val = last_session.iloc[8]
                                    if pd.notna(raw_val) and str(raw_val).strip() not in ['nan', '']:
                                        details_text = str(raw_val)
                                        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', details_text)
                                        if date_match:
                                            raw_date_str = date_match.group(0)
                                            try:
                                                dt_obj = datetime.strptime(raw_date_str, '%Y-%m-%d')
                                                formatted_arabic_date = format_arabic_date(dt_obj)
                                                details_display = details_text.replace(raw_date_str, formatted_arabic_date)
                                                date_to_show = f"<p style='font-size:1.2rem; color:#FFD700; font-weight:bold; margin-top:10px;'>📅 {formatted_arabic_date}</p>"
                                            except: details_display = details_text
                                        else: details_display = details_text
                            except Exception: pass
                            st.markdown(f"""<div class='card' style='border-right: 4px solid #3B82F6; background: rgba(59, 130, 246, 0.1);'><h4>🔔 جلسة إشراف</h4>{date_to_show}<p>{details_display}</p></div>""", unsafe_allow_html=True)
                    
                    # Filter requests by memo number (normalized)
                    reqs_mask = df_reqs["رقم المذكرة"].astype(str).apply(normalize_text) == my_memo_id
                    my_reqs = df_reqs[reqs_mask]
                    if not my_reqs.empty:
                        for _, r in my_reqs.iterrows():
                            req_type = r['النوع']; details = ""
                            if len(r) > 8:
                                val = str(r.iloc[8]).strip()
                                if val and val.lower() not in ['nan', 'none']: details = val
                            show_details = True
                            if req_type in ["حذف طالب", "تنازل"]: show_details = False
                            st.markdown(f"""<div class="card" style="border-right: 4px solid #F59E0B; padding: 20px;"><h4>{req_type}</h4><p>الحالة: <b>{r.get('الحالة', 'غير محدد')}</b></p>{'<p>التفاصيل: ' + details + '</p>' if show_details and details else '<p><i>التفاصيل مخفية</i></p>'}</div>""", unsafe_allow_html=True)
                    if prof_sessions.empty and my_reqs.empty: st.info("لا توجد إشعارات جديدة.")
                else: st.info("يجب تسجيل مذكرة أولاً.")

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
        if st.session_state.get('selected_memo_id'):
            memo_id = st.session_state.selected_memo_id
            current_memo = df_memos[df_memos["رقم المذكرة"].astype(str).apply(normalize_text) == memo_id].iloc[0]
            student_info = get_student_info_from_memo(current_memo, df_students)
            col_back, _, _ = st.columns([1, 8, 1])
            with col_back:
                if st.button("⬅️ العودة للقائمة"): st.session_state.selected_memo_id = None; st.rerun()
            st.markdown("<br>", unsafe_allow_html=True)
            progress_val = str(current_memo.get('نسبة التقدم', '0')).strip()
            try: prog_int = int(progress_val) if progress_val else 0
            except: prog_int = 0
            student_cards_html = f"""
<div class="student-card">
    <h4 style="color: #FFD700; margin-top: 0; font-size: 1.1rem;">الطالب الأول</h4>
    <p style="font-size: 1.3rem; font-weight: bold; margin: 15px 0 5px 0; color: #fff;">{student_info['s1_name']}</p>
    <p style="font-size: 0.9rem; color: #94A3B8;">رقم التسجيل: {student_info['s1_reg'] or '--'}</p>
    <div style="margin-top: 15px; padding: 8px; background: rgba(16, 185, 129, 0.1); border-radius: 8px; color: #10B981; font-size: 0.9rem;">
        📧 {student_info['s1_email'] or 'غير متوفر'}
    </div>
</div>
"""
            if student_info['s2_name']:
                student_cards_html += f"""
<div class="student-card">
    <h4 style="color: #FFD700; margin-top: 0; font-size: 1.1rem;">الطالب الثاني</h4>
    <p style="font-size: 1.3rem; font-weight: bold; margin: 15px 0 5px 0; color: #fff;">{student_info['s2_name']}</p>
    <p style="font-size: 0.9rem; color: #C0C0C0;">رقم التسجيل: {student_info['s2_reg'] or '--'}</p>
    <div style="margin-top: 15px; padding: 8px; background: rgba(16, 185, 129, 0.1); border-radius: 8px; color: #10B981; font-size: 0.9rem;">
        📧 {student_info['s2_email'] or 'غير متوفر'}
    </div>
</div>
"""
            student_cards_html += "</div>"
            full_memo_html = f"""<div class="full-view-container">
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; flex-wrap: wrap;">
    <div>
        <p class="memo-badge">{current_memo['التخصص']}</p>
        <h1 class="memo-id">{current_memo['رقم المذكرة']}</h1>
    </div>
</div>
<div style="text-align: center; border-bottom: 2px solid #2F6F7E; padding-bottom: 20px; margin-bottom: 30px;">
    <h2 style="color: #F8FAFC; font-size: 1.8rem; margin: 0; line-height: 1.6;">{current_memo['عنوان المذكرة']}</h2>
</div>
<div class="students-grid">
    {student_cards_html}
</div>
<div style="margin-bottom: 40px; text-align: center;">
    <h3 style="color: #F8FAFC; margin-bottom: 15px;">نسبة الإنجاز الحالية</h3>
    <div class="progress-container" style="height: 40px; border-radius: 20px;">
        <div class="progress-bar" style="width: """ + str(prog_int) + """%; font-size: 1.2rem; font-weight: bold; line-height: 28px;">""" + str(prog_int) + """%</div>
    </div>
</div>
</div>
"""
            st.markdown(textwrap.dedent(full_memo_html), unsafe_allow_html=True)
            st.markdown("<div class='divider' style='border-top: 1px solid #334155; margin: 30px 0;'></div>", unsafe_allow_html=True)
            st.markdown("<h3 style='text-align: center; margin-bottom: 20px;'>إدارة المذكرة</h3>", unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("<div style='background: rgba(30, 41, 59, 0.5); padding: 20px; border-radius: 10px;'>", unsafe_allow_html=True)
                st.subheader("📊 تحديث نسبة التقدم")
                new_prog = st.selectbox("اختر المرحلة:", ["0%", "10% - ضبط المقدمة", "30% - الفصل الأول", "60% - الفصل الثاني", "80% - الخاتمة", "100% - مكتملة"], key=f"prog_full_{memo_id}")
                if st.button("حفظ التحديث", key=f"save_full_{memo_id}", use_container_width=True):
                    mapping = {"0%":0, "10% - ضبط المقدمة":10, "30% - الفصل الأول":30, "60% - الفصل الثاني":60, "80% - الخاتمة":80, "100% - مكتملة":100}
                    s, m = update_progress(memo_id, mapping[new_prog])
                    st.success(m) if s else st.error(m); time.sleep(1); st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
            
            # قسم الإيداع للأستاذ
            deposit_status = str(current_memo.get("حالة الإيداع", "")).strip()
            deposit_link = str(current_memo.get("رابط الملف", "")).strip()
            deposit_date = str(current_memo.get("تاريخ إيداع المذكرة", "")).strip()
            
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("<h3 style='text-align:center; border-top:1px solid #334155; padding-top:25px;'>📥 حالة إيداع المذكرة</h3>", unsafe_allow_html=True)
            
            if not deposit_status or deposit_status in ["nan", ""]:
                st.markdown("""
                <div style="background:rgba(100,116,139,0.1); border:1px solid #475569; border-radius:16px; padding:25px; text-align:center;">
                    <div style="font-size:2.5rem;">⏳</div>
                    <p style="color:#94A3B8; font-size:1.1rem; margin:10px 0;">لم يودع الطالب المذكرة بعد.</p>
                </div>
                """, unsafe_allow_html=True)

            elif deposit_status == "مودعة":
                # عرض حالة الإيداع
                st.markdown(f"""
                <div style="background:rgba(245,158,11,0.15); border:2px solid #F59E0B; border-radius:16px; padding:25px; text-align:center; margin-bottom:20px;">
                    <div style="font-size:2.5rem;">🟡</div>
                    <h4 style="color:#F59E0B; margin:10px 0;">المذكرة مودعة — بانتظار موافقتك</h4>
                    <p style="color:#94A3B8;">تاريخ الإيداع: {deposit_date if deposit_date and deposit_date != 'nan' else 'غير محدد'}</p>
                </div>
                """, unsafe_allow_html=True)

                # زر الاطلاع على المذكرة
                if deposit_link and deposit_link != "nan":
                    st.markdown(f"""
                    <div style="text-align:center; margin-bottom:25px;">
                        <a href="{deposit_link}" target="_blank" style="
                            display:inline-block; background:linear-gradient(135deg,#1E3A5F,#2F6F7E);
                            color:#ffffff; padding:18px 40px; border-radius:14px; text-decoration:none;
                            font-size:1.2rem; font-weight:700; letter-spacing:0.5px;
                            box-shadow:0 8px 20px rgba(47,111,126,0.4);
                            border:2px solid rgba(255,255,255,0.15);">
                            📄 الاطلاع على المذكرة المودعة
                        </a>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown("---")

                # نموذج التصريح
                st.markdown("""
                <div style="background:linear-gradient(145deg,#1E293B,#0F172A); border:2px solid #2F6F7E;
                     border-radius:20px; padding:30px; margin-bottom:20px;">
                    <h3 style="color:#FFD700; text-align:center; margin-bottom:5px;">📋 نموذج التصريح الرسمي</h3>
                    <p style="color:#94A3B8; text-align:center; font-size:0.9rem;">يرجى ملء جميع الحقول للمتابعة</p>
                </div>
                """, unsafe_allow_html=True)

                # استخراج بيانات الطلبة للعرض
                memo_vals_ap = current_memo.tolist() if hasattr(current_memo, 'tolist') else list(current_memo.values())
                s1_name_ap = str(current_memo.get("الطالب الأول", "")).strip()
                s2_name_ap = str(current_memo.get("الطالب الثاني", "")).strip()
                students_str_ap = s1_name_ap
                if s2_name_ap and s2_name_ap not in ["", "nan", "--"]:
                    students_str_ap += f" و {s2_name_ap}"

                st.markdown(f"""
                <div style="background:rgba(47,111,126,0.1); border:1px solid #2F6F7E; border-radius:12px; padding:20px; margin-bottom:20px;">
                    <p style="margin:5px 0;">📄 <b>رقم المذكرة:</b> {memo_id}</p>
                    <p style="margin:5px 0;">📑 <b>العنوان:</b> {current_memo.get('عنوان المذكرة','')}</p>
                    <p style="margin:5px 0;">👤 <b>الطالب(ون):</b> {students_str_ap}</p>
                    <p style="margin:5px 0;">👨‍🏫 <b>المشرف:</b> {prof_name}</p>
                </div>
                """, unsafe_allow_html=True)

                # الخطوة 1: التحقق من رقم المذكرة
                st.markdown("**الخطوة 1 — أدخل رقم المذكرة للتأكيد:**")
                confirm_memo_num = st.text_input("رقم المذكرة", placeholder=f"اكتب: {memo_id}", key=f"confirm_num_{memo_id}")

                # الخطوة 2: خانة الإقرار
                st.markdown("**الخطوة 2 — اقرأ التصريح وضع علامة الموافقة:**")
                declaration_text = f"أنا الأستاذ {prof_name}، أصرّح بأن المذكرة رقم {memo_id} بعنوان «{current_memo.get('عنوان المذكرة','')}» للطالب(ين) {students_str_ap}، هي النسخة النهائية المودعة وهي التي ستُعرض على لجنة المناقشة ولن يُقبل أي تعديل بعد هذا التصريح."
                st.markdown(f"""
                <div style="background:rgba(16,185,129,0.08); border:1px solid rgba(16,185,129,0.3);
                     border-radius:10px; padding:15px; margin:10px 0; direction:rtl; line-height:1.9; color:#E2E8F0;">
                    {declaration_text}
                </div>
                """, unsafe_allow_html=True)
                agree_check = st.checkbox("✅ أوافق على هذا التصريح وأقرّ بصحته", key=f"agree_{memo_id}")

                # الخطوة 3: التوقيع الإلكتروني
                st.markdown("**الخطوة 3 — التوقيع الإلكتروني (اكتب اسمك الكامل بالضبط):**")
                st.markdown(f"""
                <div style="background:rgba(47,111,126,0.08); border:1px dashed #2F6F7E; border-radius:8px; padding:10px 15px; margin-bottom:8px;">
                    <p style="color:#94A3B8; font-size:0.85rem; margin:0;">📌 الاسم المسجل في المنصة: <strong style="color:#FFD700;">{prof_name}</strong></p>
                </div>
                """, unsafe_allow_html=True)
                signature = st.text_input("التوقيع", placeholder=f"اكتب: {prof_name}", key=f"sig_{memo_id}")

                st.markdown("<br>", unsafe_allow_html=True)

                # زر الموافقة الأولى
                if not st.session_state.get(f"confirm_step_{memo_id}", False):
                    if st.button("📋 متابعة للتأكيد النهائي", type="primary", use_container_width=True, key=f"pre_approve_{memo_id}"):
                        errors = []
                        if normalize_text(confirm_memo_num) != normalize_text(memo_id):
                            errors.append("❌ رقم المذكرة غير مطابق — تحقق من الرقم وأعد الكتابة")
                        if not agree_check:
                            errors.append("❌ يجب الموافقة على التصريح أولاً")
                        if not signature.strip():
                            errors.append("❌ حقل التوقيع فارغ")
                        elif signature.strip() != prof_name.strip():
                            errors.append(f"❌ التوقيع غير مطابق — يجب كتابة اسمك بالضبط: «{prof_name}»")
                        if errors:
                            for e in errors: st.error(e)
                        else:
                            st.session_state[f"confirm_step_{memo_id}"] = True
                            st.session_state[f"sig_value_{memo_id}"] = signature.strip()
                            st.rerun()
                else:
                    # تأكيد نهائي
                    st.markdown(f"""
                    <div style="background:rgba(239,68,68,0.15); border:2px solid #EF4444; border-radius:14px; padding:25px; text-align:center; margin-bottom:20px;">
                        <div style="font-size:2rem;">⚠️</div>
                        <h4 style="color:#EF4444; margin:10px 0;">تأكيد نهائي</h4>
                        <p style="color:#F8FAFC;">هل أنت متأكد تماماً؟</p>
                        <p style="color:#94A3B8; font-size:0.9rem;">هذا الإجراء <b>نهائي وغير قابل للتراجع</b>.<br>
                        المذكرة رقم <b>{memo_id}</b> ستُرسل رسمياً للجنة المناقشة.</p>
                    </div>
                    """, unsafe_allow_html=True)
                    col_yes, col_no = st.columns(2)
                    with col_yes:
                        if st.button("✅ نعم، أؤكد الموافقة النهائية", type="primary", use_container_width=True, key=f"final_approve_{memo_id}"):
                            with st.spinner("⏳ جاري حفظ التصريح..."):
                                # حفظ التصريح
                                sig_saved = st.session_state.get(f"sig_value_{memo_id}", "")
                                save_approval_declaration(memo_id, prof_name, sig_saved, declaration_text)
                                # تغيير الحالة
                                ok, msg = approve_memo_for_defense(memo_id)
                                if ok:
                                    # إرسال إيميل للطلبة
                                    df_students_fresh = load_students()
                                    df_students_fresh['رقم التسجيل_norm'] = df_students_fresh['رقم التسجيل'].astype(str).apply(normalize_text)
                                    s1_data_ap = None; s2_data_ap = None
                                    memo_vals = current_memo.tolist() if hasattr(current_memo, 'tolist') else list(current_memo.values())
                                    reg1 = normalize_text(current_memo.get("رقم تسجيل الطالب 1", memo_vals[18] if len(memo_vals) > 18 else ""))
                                    reg2 = normalize_text(current_memo.get("رقم تسجيل الطالب 2", memo_vals[19] if len(memo_vals) > 19 else ""))
                                    if reg1 and reg1 not in ["", "nan"]:
                                        r = df_students_fresh[df_students_fresh["رقم التسجيل_norm"] == reg1]
                                        if not r.empty: s1_data_ap = r.iloc[0].to_dict()
                                    if reg2 and reg2 not in ["", "nan"]:
                                        r = df_students_fresh[df_students_fresh["رقم التسجيل_norm"] == reg2]
                                        if not r.empty: s2_data_ap = r.iloc[0].to_dict()
                                    send_approval_email_to_students(
                                        memo_id, str(current_memo.get('عنوان المذكرة','')),
                                        prof_name, s1_data_ap, s2_data_ap
                                    )
                                    st.session_state.pop(f"confirm_step_{memo_id}", None)
                                    st.session_state.pop(f"sig_value_{memo_id}", None)
                                    st.success("✅ تمت الموافقة وحُفظ التصريح رسمياً")
                                    st.balloons()
                                    clear_cache_and_reload()
                                    time.sleep(2)
                                    st.rerun()
                                else:
                                    st.error(msg)
                    with col_no:
                        if st.button("❌ إلغاء — العودة للمراجعة", use_container_width=True, key=f"cancel_approve_{memo_id}"):
                            st.session_state.pop(f"confirm_step_{memo_id}", None)
                            st.rerun()

            elif deposit_status == "قابلة للمناقشة":
                st.markdown(f"""
                <div style="background:rgba(16,185,129,0.15); border:2px solid #10B981; border-radius:16px; padding:25px; text-align:center;">
                    <div style="font-size:2.5rem;">🟢</div>
                    <h4 style="color:#10B981; margin:10px 0;">المذكرة معتمدة — قابلة للمناقشة</h4>
                    <p style="color:#94A3B8;">تم التصريح رسمياً بهذه المذكرة وإرسالها للجنة.</p>
                </div>
                """, unsafe_allow_html=True)
                if deposit_link and deposit_link != "nan":
                    st.markdown(f"""
                    <div style="text-align:center; margin-top:15px;">
                        <a href="{deposit_link}" target="_blank" style="
                            display:inline-block; background:rgba(16,185,129,0.2);
                            color:#10B981; padding:12px 28px; border-radius:10px; text-decoration:none;
                            font-weight:700; border:1px solid #10B981;">
                            📄 الاطلاع على المذكرة المودعة
                        </a>
                    </div>
                    """, unsafe_allow_html=True)
            with col2:
                st.markdown("<div style='background: rgba(30, 41, 59, 0.5); padding: 20px; border-radius: 10px;'>", unsafe_allow_html=True)
                st.subheader("📨 إرسال طلب للإدارة")
                req_op = st.selectbox("نوع الطلب:", ["", "تغيير عنوان المذكرة", "حذف طالب (ثنائية)", "إضافة طالب (فردية)", "تنازل عن الإشراف"], key=f"req_full_{memo_id}")
                details_to_save = ""; validation_error = None
                if req_op == "تغيير عنوان المذكرة":
                    new_title = st.text_input("العنوان الجديد:", key=f"nt_full_{memo_id}")
                    if st.button("إرسال طلب تغيير العنوان", key=f"btn_ch_full_{memo_id}", use_container_width=True):
                        if new_title: details_to_save = f"العنوان الجديد المقترح: {new_title}"
                        else: validation_error = "الرجاء إدخال العنوان"
                elif req_op == "حذف طالب (ثنائية)":
                    if not student_info['s2_name']: st.warning("هذه مذكرة فردية!")
                    else:
                        st.write("الطالبان:"); st.write(f"1. {student_info['s1_name']}"); st.write(f"2. {student_info['s2_name']}")
                        to_del = st.selectbox("اختر الطالب للحذف:", ["", "الطالب الأول", "الطالب الثاني"], key=f"del_full_{memo_id}")
                        just = st.text_area("تبريرات الحذف:", key=f"jus_del_full_{memo_id}")
                        if st.button("إرسال طلب الحذف", key=f"btn_del_full_{memo_id}", use_container_width=True):
                            if to_del and just: details_to_save = f"حذف: {to_del}. السبب: {just}"
                            else: validation_error = "اكمل البيانات"
                elif req_op == "إضافة طالب (فردية)":
                    if student_info['s2_name']: st.warning("هذه مذكرة ثنائية بالفعل!")
                    else:
                        reg_to_add = st.text_input("رقم التسجيل:", key=f"add_full_{memo_id}")
                        if st.button("تحقق وإرسال", key=f"btn_add_full_{memo_id}", use_container_width=True):
                            df_students['رقم التسجيل_norm'] = df_students['رقم التسجيل'].astype(str).apply(normalize_text)
                            target = df_students[df_students["رقم التسجيل_norm"] == normalize_text(reg_to_add)]
                            if target.empty: validation_error = "رقم التسجيل غير موجود"
                            elif target.iloc[0].get("رقم المذكرة"): validation_error = "الطالب لديه مذكرة بالفعل"
                            elif target.iloc[0].get("التخصص") != current_memo['التخصص']: validation_error = "التخصص غير متطابق"
                            else:
                                just = st.text_area("ملاحظات (اختياري):", key=f"jus_add_full_{memo_id}")
                                details_to_save = f"إضافة الطالب المسجل: {reg_to_add}. ملاحظات: {just}"
                elif req_op == "تنازل عن الإشراف":
                    just = st.text_area("مبررات التنازل:", key=f"res_full_{memo_id}")
                    if st.button("إرسال طلب التنازل", key=f"btn_res_full_{memo_id}", use_container_width=True):
                        if just: details_to_save = f"التنازل عن الإشراف. المبررات: {just}"
                        else: validation_error = "الرجاء كتابة المبررات"
                if validation_error: st.error(validation_error)
                elif details_to_save:
                    suc, msg = save_and_send_request(req_op, prof_name, memo_id, current_memo['عنوان المذكرة'], details_to_save)
                    if suc: st.success(msg); time.sleep(1); st.rerun()
                    else: st.error(msg)
                st.markdown("</div>", unsafe_allow_html=True)

        else:
            col1, col2 = st.columns([4, 1])
            with col2:
                if st.button("خروج"): logout()
            st.markdown(f"<h2 style='margin-bottom:20px;'>فضاء الأستاذ <span style='color:#FFD700;'>{prof_name}</span></h2>", unsafe_allow_html=True)
            prof_memos = df_memos[df_memos["الأستاذ"].astype(str).str.strip() == prof_name.strip()]
            total = len(prof_memos)
            registered = len(prof_memos[prof_memos["تم التسجيل"].astype(str).str.strip() == "نعم"])
            available = total - registered
            is_exhausted = registered >= 4
            st.markdown('<div class="kpi-grid">', unsafe_allow_html=True)
            st.markdown(f'<div class="kpi-card"><div class="kpi-value">{total}</div><div class="kpi-label">إجمالي المذكرات</div></div><div class="kpi-card" style="border-color: #10B981;"><div class="kpi-value" style="color: #10B981;">{registered}</div><div class="kpi-label">المذكرات المسجلة</div></div><div class="kpi-card" style="border-color: #F59E0B;"><div class="kpi-value" style="color: #F59E0B;">{available}</div><div class="kpi-label">المذكرات المتاحة</div></div></div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            if is_exhausted: st.markdown('<div class="alert-card">لقد استنفذت العناوين الأربعة المخصصة لك.</div>', unsafe_allow_html=True)
            tab1, tab2, tab3, tab4, tab5 = st.tabs(["المذكرات المسجلة", "جدولة جلسة إشراف", "كلمات السر", "المذكرات المتاحة", "🎓 لجان المناقشة"])
            with tab1:
                st.subheader("المذكرات المسجلة")
                registered_memos = prof_memos[prof_memos["تم التسجيل"].astype(str).str.strip() == "نعم"]
                if not registered_memos.empty:
                    cols = st.columns(2)
                    for i, (_, memo) in enumerate(registered_memos.iterrows()):
                        with cols[i % 2]:
                            progress_val = str(memo.get('نسبة التقدم', '0')).strip()
                            try: prog_int = int(progress_val) if progress_val else 0
                            except: prog_int = 0
                            s_info = get_student_info_from_memo(memo, df_students)
                            st.markdown(f'''<div class="card" style="border-right:5px solid #10B981; padding-bottom: 10px;"><h4>{memo['رقم المذكرة']} - {memo['عنوان المذكرة']}</h4><p style="color:#94A3B8; font-size:0.9em;">تخصص: {memo['التخصص']}</p><p style="font-size:0.95em; margin-bottom: 5px;">{s_info['s1_name']}</p>{f"<p style='font-size:0.95em; margin-bottom: 15px;'>{s_info['s2_name']}</p>" if s_info['s2_name'] else ""}<div class="progress-container" style="margin: 10px 0;"><div class="progress-bar" style="width: {prog_int}%;"></div></div><p style="text-align:left; font-size:0.8em;">نسبة الإنجاز: {prog_int}%</p></div>''', unsafe_allow_html=True)
                            if st.button(f"👉 عرض المذكرة {memo['رقم المذكرة']}", key=f"open_{memo['رقم المذكرة']}", use_container_width=True):
                                st.session_state.selected_memo_id = memo['رقم المذكرة']; st.rerun()
                else: st.info("لا توجد مذكرات مسجلة حتى الآن.")

            with tab2:
                st.subheader("📅 جدولة جلسة إشراف")
                st.info("سيتم إرسال الإشعار لكل الطلبة المسجلين لديك في المذكرات.")
                with st.form("supervision_session_form"):
                    c1, c2 = st.columns(2)
                    with c1: selected_date = st.date_input("تاريخ الجلسة", min_value=datetime.now().date())
                    with c2:
                        time_slots = []
                        for h in range(8, 16):
                            for m in [0, 30]:
                                if h == 15 and m == 30: continue
                                time_slots.append(f"{h:02d}:{m:02d}")
                        selected_time = st.selectbox("توقيت الجلسة", time_slots)
                    submitted = st.form_submit_button("📤 نشر الجلسة وإرسال الإشعارات")
                    if submitted:
                        weekday = selected_date.weekday()
                        if weekday in [4, 5]: st.error("❌ لا يمكن جدولة جلسات في يومي الجمعة والسبت.")
                        else:
                            session_datetime_str = format_datetime_ar(selected_date, selected_time)
                            details_text = f"موعد الجلسة: {session_datetime_str}"
                            target_students = get_students_of_professor(prof_name, df_memos)
                            if not target_students: st.warning("⚠️ لا يوجد طلاب مسجلون لديك حالياً لإرسال الإشعار.")
                            else:
                                save_success, save_msg = save_and_send_request("جلسة إشراف", prof_name, "جماعي", "جلسة إشراف", details_text, status="منجز")
                                if save_success:
                                    update_success, update_msg = update_session_date_in_sheets(prof_name, details_text)
                                    if update_success:
                                        st.success(f"✅ {save_msg}")
                                        st.info(f"تم تحديث موعد الجلسة في ملفات {len(target_students)} طالب.")
                                        email_success, email_msg = send_session_emails(target_students, details_text, prof_name)
                                        if email_success: st.success("📧 تم إرسال الإشعارات للطلبة والإدارة.")
                                        else: st.warning(f"⚠️ تم الحفظ لكن فاشل الإرسال: {email_msg}")
                                        time.sleep(2); st.rerun()
                                    else: st.error(f"تم حفظ الطلب ولكن حدث خطأ في تحديث المذكرات: {update_msg}")
                                else: st.error(save_msg)

            with tab3:
                st.subheader("كلمات السر")
                pwds = df_prof_memos[df_prof_memos["الأستاذ"].astype(str).str.strip() == prof_name.strip()]
                if not pwds.empty:
                    for _, row in pwds.iterrows():
                        stat = str(row.get("تم التسجيل", "")).strip()
                        pwd = str(row.get("كلمة سر التسجيل", "")).strip()
                        if pwd:
                            color = "#10B981" if stat == "نعم" else "#F59E0B"
                            status_txt = "مستخدمة" if stat == "نعم" else "متاحة"
                            st.markdown(f'''<div class="card" style="border-right:5px solid {color}; display:flex; justify-content:space-between; align-items:center;"><div><h3 style="margin:0; font-family:monospace; font-size:1.8rem; color:#FFD700;">{pwd}</h3><p style="margin:5px 0 0 0 0 0; color:#94A3B8;">الحالة: {status_txt}</p></div></div>''', unsafe_allow_html=True)
                else: st.info("لا توجد كلمات سر مسندة إليك.")
            
            with tab4:
                if is_exhausted: st.subheader("💡 المذكرات المقترحة")
                else: st.subheader("⏳ المذكرات المتاحة للتسجيل")
                avail = prof_memos[prof_memos["تم التسجيل"].astype(str).str.strip() != "نعم"]
                if not avail.empty:
                    for _, m in avail.iterrows():
                        st.markdown(f'''<div class="card" style="border-left:4px solid #64748B;"><h4>{m['رقم المذكرة']}</h4><p>{m['عنوان المذكرة']}</p><p style="color:#94A3B8;">تخصص: {m['التخصص']}</p></div>''', unsafe_allow_html=True)
                else: st.success("✅ جميع المذكرات مسجلة أو مقترحة!")

            with tab5:
                st.subheader("🎓 لجان المناقشة")
                df_m_jury = load_memos()

                # البحث عن المذكرات التي الأستاذ عضو فيها بأي صفة + منشورة
                jury_memos = pd.DataFrame()
                if not df_m_jury.empty:
                    masks = []
                    for col_j, role_j in [("الأستاذ","مشرف"),("AC","رئيس"),("AD","مناقش1"),("AE","مناقش2")]:
                        if col_j in df_m_jury.columns:
                            m = df_m_jury[df_m_jury[col_j].astype(str).str.strip() == prof_name.strip()]
                            if not m.empty:
                                m = m.copy(); m['صفتي'] = role_j
                                masks.append(m)
                    if masks:
                        jury_memos = pd.concat(masks).drop_duplicates(subset=["رقم المذكرة"])
                        # فقط المنشورة
                        if "AF" in jury_memos.columns:
                            jury_memos = jury_memos[jury_memos["AF"].astype(str).str.strip() == "نعم"]

                if jury_memos.empty:
                    st.info("⏳ لا توجد مذكرات منشورة تخصك كعضو لجنة بعد.")
                else:
                    for _, jm in jury_memos.iterrows():
                        jmemo_id = str(jm.get("رقم المذكرة","")).strip()
                        role_display = jm.get('صفتي','')
                        dep_link_j = str(jm.get("رابط الملف","")).strip()
                        def_date_j = str(jm.get("تاريخ المناقشة","")).strip()
                        def_time_j = str(jm.get("توقيت المناقشة","")).strip()
                        def_room_j = str(jm.get("القاعة","")).strip()

                        # ملاحظات العضو
                        notes_col = {"رئيس":"AG","مناقش1":"AH","مناقش2":"AI","مشرف":"AG"}.get(role_display,"AG")
                        curr_notes = str(jm.get(notes_col,"")).strip() if notes_col in jm.index else ""
                        if curr_notes in ["nan",""]: curr_notes = ""

                        with st.expander(f"📄 {jmemo_id} — {jm.get('عنوان المذكرة','')} | صفتك: {role_display}", expanded=False):
                            st.markdown(f"""
                            <div class="card" style="border-top:3px solid #2F6F7E;">
                                <p>📄 <b>رقم المذكرة:</b> {jmemo_id}</p>
                                <p>📑 <b>العنوان:</b> {jm.get('عنوان المذكرة','')}</p>
                                <p>🎓 <b>التخصص:</b> {jm.get('التخصص','')}</p>
                                <p>👨‍🏫 <b>المشرف:</b> {jm.get('الأستاذ','')}</p>
                                <p>🏛️ <b>الرئيس:</b> {jm.get('AC','') if 'AC' in jm.index else '--'}</p>
                                <p>📋 <b>المناقش1:</b> {jm.get('AD','') if 'AD' in jm.index else '--'}</p>
                                <p>📋 <b>المناقش2:</b> {jm.get('AE','') if 'AE' in jm.index else '--'}</p>
                                <p>📆 <b>موعد المناقشة:</b> {def_date_j} {def_time_j}</p>
                                <p>🏛️ <b>القاعة:</b> {def_room_j}</p>
                            </div>
                            """, unsafe_allow_html=True)

                            if dep_link_j and dep_link_j != "nan":
                                st.markdown(f"""
                                <div style="text-align:center; margin:15px 0;">
                                    <a href="{dep_link_j}" target="_blank" style="
                                        display:inline-block; background:linear-gradient(135deg,#1E3A5F,#2F6F7E);
                                        color:#ffffff; padding:14px 32px; border-radius:12px; text-decoration:none;
                                        font-size:1.05rem; font-weight:700;
                                        box-shadow:0 6px 16px rgba(47,111,126,0.4);">
                                        📄 الاطلاع على المذكرة المودعة
                                    </a>
                                </div>
                                """, unsafe_allow_html=True)

                            st.markdown("**📝 ملاحظاتك الأولية** (تراها الإدارة فقط):")
                            new_notes = st.text_area("الملاحظات", value=curr_notes, height=120, key=f"notes_{jmemo_id}_{role_display}", placeholder="اكتب ملاحظاتك الأولية حول المذكرة...")
                            if st.button("💾 حفظ الملاحظات", key=f"save_notes_{jmemo_id}_{role_display}", use_container_width=True):
                                ok, msg = save_notes_by_member(jmemo_id, role_display, new_notes)
                                if ok: st.success(msg); clear_cache_and_reload()
                                else: st.error(msg)

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
        # وضع Wizard برنامج المناقشات
        if st.session_state.get('admin_mode') == 'defense_wizard':
            # ======================================================
            # WIZARD — برنامج المناقشات
            # ======================================================
            col_back_w, col_title_w = st.columns([1, 5])
            with col_back_w:
                if st.button("⬅️ رجوع للوحة التحكم"):
                    st.session_state['admin_mode'] = None
                    st.session_state.pop('wizard_step', None)
                    st.session_state.pop('generated_schedule', None)
                    st.rerun()
            with col_title_w:
                st.markdown("<h2 style='color:#FFD700;'>🎓 برنامج المناقشات</h2>", unsafe_allow_html=True)

            # شريط التقدم
            step = st.session_state.get('wizard_step', 1)
            steps_labels = ["1️⃣ اللجان", "2️⃣ التوليد", "3️⃣ المراجعة", "4️⃣ النشر"]
            cols_steps = st.columns(4)
            for i, (col_s, label) in enumerate(zip(cols_steps, steps_labels)):
                with col_s:
                    active = i+1 == step
                    done = i+1 < step
                    color = "#FFD700" if active else ("#10B981" if done else "#475569")
                    st.markdown(f"""
                    <div style="text-align:center; padding:10px; border-radius:10px;
                         background:{'rgba(255,215,0,0.15)' if active else ('rgba(16,185,129,0.1)' if done else 'rgba(71,85,105,0.1)')};
                         border:2px solid {color};">
                        <span style="color:{color}; font-weight:bold; font-size:0.95rem;">{label}</span>
                    </div>
                    """, unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)

            df_mw = load_memos()
            col_deposit_w = "حالة الإيداع"
            ready_w = df_mw[df_mw[col_deposit_w].astype(str).str.strip() == "قابلة للمناقشة"] if col_deposit_w in df_mw.columns else pd.DataFrame()
            all_profs_w = sorted(df_prof_memos["الأستاذ"].dropna().unique().tolist())

            # ===================== STEP 1 — اللجان =====================
            if step == 1:
                st.markdown("### 👥 تحديد لجان المناقشة")
                if ready_w.empty:
                    st.warning("⏳ لا توجد مذكرات قابلة للمناقشة بعد.")
                else:
                    st.info(f"📌 عدد المذكرات الجاهزة: **{len(ready_w)}**")
                    jury_errors = []
                    jury_data = {}

                    for _, row_w in ready_w.iterrows():
                        mnum = str(row_w.get("رقم المذكرة","")).strip()
                        supervisor_w = str(row_w.get("الأستاذ","")).strip()
                        curr_p = str(row_w.get("AC","")).strip() if "AC" in row_w.index else ""
                        curr_e1 = str(row_w.get("AD","")).strip() if "AD" in row_w.index else ""
                        curr_e2 = str(row_w.get("AE","")).strip() if "AE" in row_w.index else ""
                        if curr_p in ["nan",""]: curr_p = all_profs_w[0] if all_profs_w else ""
                        if curr_e1 in ["nan",""]: curr_e1 = all_profs_w[0] if all_profs_w else ""
                        if curr_e2 in ["nan",""]: curr_e2 = all_profs_w[0] if all_profs_w else ""

                        with st.expander(f"📄 {mnum} — {row_w.get('عنوان المذكرة','')[:50]}...", expanded=False):
                            st.markdown(f"👨‍🏫 **المشرف:** {supervisor_w}")
                            cw1, cw2, cw3 = st.columns(3)
                            with cw1:
                                p_sel = st.selectbox("🏛️ الرئيس", all_profs_w, index=all_profs_w.index(curr_p) if curr_p in all_profs_w else 0, key=f"wp_{mnum}")
                            with cw2:
                                e1_sel = st.selectbox("📋 المناقش 1", all_profs_w, index=all_profs_w.index(curr_e1) if curr_e1 in all_profs_w else 0, key=f"we1_{mnum}")
                            with cw3:
                                e2_sel = st.selectbox("📋 المناقش 2", all_profs_w, index=all_profs_w.index(curr_e2) if curr_e2 in all_profs_w else 0, key=f"we2_{mnum}")

                            members_w = [supervisor_w, p_sel, e1_sel, e2_sel]
                            if len(set(members_w)) < 4:
                                st.error("⚠️ أستاذ يشغل أكثر من صفة!")
                                jury_errors.append(mnum)
                            else:
                                jury_data[mnum] = (p_sel, e1_sel, e2_sel)

                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("💾 حفظ جميع اللجان والمتابعة ←", type="primary", use_container_width=True, key="wizard_save_jury"):
                        if jury_errors:
                            st.error(f"❌ يوجد تعارض في اللجان: {', '.join(jury_errors)}")
                        else:
                            saved_ok = True
                            for mnum, (p,e1,e2) in jury_data.items():
                                ok, msg = save_jury(mnum, p, e1, e2)
                                if not ok: st.error(f"خطأ في {mnum}: {msg}"); saved_ok = False; break
                            if saved_ok:
                                st.success(f"✅ تم حفظ {len(jury_data)} لجنة بنجاح")
                                st.session_state['wizard_step'] = 2
                                clear_cache_and_reload()
                                time.sleep(1)
                                st.rerun()

            # ===================== STEP 2 — التوليد =====================
            elif step == 2:
                st.markdown("### ⚡ توليد البرنامج التلقائي")
                df_rooms_w = load_rooms()
                rooms_list_w = df_rooms_w["إسم القاعة"].dropna().tolist() if "إسم القاعة" in df_rooms_w.columns else []

                if not rooms_list_w:
                    st.error("❌ لا توجد قاعات في شيت 'القاعات'.")
                else:
                    st.info(f"📌 القاعات المتاحة: **{', '.join(rooms_list_w)}**")
                    csd1, csd2 = st.columns(2)
                    with csd1:
                        w_start = st.date_input("📅 تاريخ البداية", value=date(2026,5,24), key="w_start")
                    with csd2:
                        w_end = st.date_input("📅 تاريخ النهاية", value=date(2026,6,4), key="w_end")

                    col_g1, col_g2 = st.columns(2)
                    with col_g1:
                        gen_btn = st.button("⚡ توليد البرنامج", type="primary", use_container_width=True, key="w_gen")
                    with col_g2:
                        regen_btn = st.button("🔄 اقتراح جديد", use_container_width=True, key="w_regen")

                    if gen_btn or regen_btn:
                        if regen_btn: clear_schedule_from_sheets()
                        with st.spinner("⏳ جاري التوليد..."):
                            ok, msg, df_sched = generate_schedule(rooms_list_w, str(w_start), str(w_end))
                            if ok:
                                st.session_state['generated_schedule'] = df_sched
                                st.session_state['schedule_msg'] = msg
                                st.rerun()
                            else:
                                st.error(msg)

                    if 'generated_schedule' in st.session_state and st.session_state['generated_schedule'] is not None:
                        df_show_w = st.session_state['generated_schedule']
                        msg_w = st.session_state.get('schedule_msg','')
                        for line in msg_w.split('\n'):
                            if "✅" in line: st.success(line)
                            elif "⚠️" in line: st.warning(line)

                        st.dataframe(df_show_w, use_container_width=True, height=350)

                        col_back2, col_next2 = st.columns(2)
                        with col_back2:
                            if st.button("⬅️ العودة للجان", use_container_width=True, key="w_back2"):
                                st.session_state['wizard_step'] = 1; st.rerun()
                        with col_next2:
                            if st.button("✅ تأكيد البرنامج والمتابعة ←", type="primary", use_container_width=True, key="w_confirm_sched"):
                                ok, msg = save_schedule_to_sheets(df_show_w)
                                if ok:
                                    st.success(msg)
                                    st.session_state['wizard_step'] = 3
                                    clear_cache_and_reload()
                                    time.sleep(1)
                                    st.rerun()
                                else:
                                    st.error(msg)
                    else:
                        col_back2b, _ = st.columns(2)
                        with col_back2b:
                            if st.button("⬅️ العودة للجان", use_container_width=True, key="w_back2b"):
                                st.session_state['wizard_step'] = 1; st.rerun()

            # ===================== STEP 3 — المراجعة =====================
            elif step == 3:
                st.markdown("### 📋 مراجعة البرنامج")
                df_mw3 = load_memos()
                col_deposit_w3 = "حالة الإيداع"
                scheduled = df_mw3[
                    (df_mw3.get(col_deposit_w3, pd.Series(dtype=str)).astype(str).str.strip() == "قابلة للمناقشة") &
                    (df_mw3.get("تاريخ المناقشة", pd.Series(dtype=str)).astype(str).str.strip().isin(["","nan"]) == False)
                ] if col_deposit_w3 in df_mw3.columns and "تاريخ المناقشة" in df_mw3.columns else pd.DataFrame()

                if scheduled.empty:
                    st.warning("لا يوجد برنامج محفوظ بعد.")
                else:
                    # عرض يومي
                    days_in_sched = sorted(scheduled["تاريخ المناقشة"].astype(str).unique().tolist())
                    today_str = str(date.today())
                    view_mode = st.radio("عرض:", ["📅 يوم بيوم", "📋 الكل"], horizontal=True, key="w_view_mode")

                    if view_mode == "📅 يوم بيوم":
                        sel_day = st.selectbox("اختر اليوم:", days_in_sched, key="w_day_sel",
                                               index=days_in_sched.index(today_str) if today_str in days_in_sched else 0)
                        day_data = scheduled[scheduled["تاريخ المناقشة"].astype(str) == sel_day].sort_values("توقيت المناقشة")
                        for _, dr in day_data.iterrows():
                            st.markdown(f"""
                            <div class="card" style="border-right:5px solid #2F6F7E; margin-bottom:10px;">
                                <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap;">
                                    <span style="color:#FFD700; font-size:1.3rem; font-weight:900;">🕐 {dr.get('توقيت المناقشة','')}</span>
                                    <span style="background:#2F6F7E; color:white; padding:4px 12px; border-radius:20px; font-size:0.9rem;">🏛️ {dr.get('القاعة','')}</span>
                                </div>
                                <p style="margin:8px 0 4px 0;"><b>📄 {dr.get('رقم المذكرة','')}</b> — {str(dr.get('عنوان المذكرة',''))[:60]}</p>
                                <p style="color:#94A3B8; font-size:0.9rem;">👤 {dr.get('الطالب الأول','')} {'| ' + str(dr.get('الطالب الثاني','')) if str(dr.get('الطالب الثاني','')).strip() not in ['','nan','--'] else ''}</p>
                                <p style="color:#64748B; font-size:0.85rem;">👨‍🏫 {dr.get('الأستاذ','')} | 🏛️ {dr.get('AC','')} | {dr.get('AD','')} | {dr.get('AE','')}</p>
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        disp_cols3 = [c for c in ["رقم المذكرة","عنوان المذكرة","تاريخ المناقشة","توقيت المناقشة","القاعة","الأستاذ","AC","AD","AE","الطالب الأول","الطالب الثاني"] if c in scheduled.columns]
                        st.dataframe(scheduled[disp_cols3].sort_values(["تاريخ المناقشة","توقيت المناقشة"]), use_container_width=True, height=400)

                    st.markdown("<br>", unsafe_allow_html=True)
                    col_back3, col_next3 = st.columns(2)
                    with col_back3:
                        if st.button("⬅️ العودة للتوليد", use_container_width=True, key="w_back3"):
                            st.session_state['wizard_step'] = 2; st.rerun()
                    with col_next3:
                        if st.button("📢 المتابعة للنشر ←", type="primary", use_container_width=True, key="w_to_publish"):
                            st.session_state['wizard_step'] = 4; st.rerun()

            # ===================== STEP 4 — النشر =====================
            elif step == 4:
                st.markdown("### 📢 نشر البرنامج")
                df_mw4 = load_memos()
                col_deposit_w4 = "حالة الإيداع"
                publishable = df_mw4[
                    df_mw4.get(col_deposit_w4, pd.Series(dtype=str)).astype(str).str.strip() == "قابلة للمناقشة"
                ] if col_deposit_w4 in df_mw4.columns else pd.DataFrame()

                published = publishable[publishable.get("AF", pd.Series(dtype=str)).astype(str).str.strip() == "نعم"] if "AF" in publishable.columns else pd.DataFrame()
                unpublished = publishable[publishable.get("AF", pd.Series(dtype=str)).astype(str).str.strip() != "نعم"] if "AF" in publishable.columns else publishable

                col_pub_s1, col_pub_s2 = st.columns(2)
                with col_pub_s1:
                    st.markdown(f'<div class="kpi-card"><div class="kpi-value" style="color:#10B981;">{len(published)}</div><div class="kpi-label">منشورة</div></div>', unsafe_allow_html=True)
                with col_pub_s2:
                    st.markdown(f'<div class="kpi-card"><div class="kpi-value" style="color:#F59E0B;">{len(unpublished)}</div><div class="kpi-label">غير منشورة</div></div>', unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)
                st.warning("⚠️ بعد النشر يرى الطالب والأستاذ موعد المناقشة وأعضاء اللجنة.")

                if st.button("🚀 نشر جميع المذكرات دفعة واحدة", type="primary", use_container_width=True, key="w_pub_all"):
                    ok, msg = publish_memos()
                    if ok:
                        st.success(msg); st.balloons()
                        clear_cache_and_reload(); time.sleep(1); st.rerun()
                    else: st.error(msg)

                st.markdown("---")
                st.markdown("**أو نشر مذكرة محددة:**")
                if not unpublished.empty:
                    pub_opts = unpublished["رقم المذكرة"].astype(str).tolist()
                    pub_single = st.selectbox("اختر المذكرة:", pub_opts, key="w_pub_single_sel")
                    if st.button("📤 نشر هذه المذكرة", use_container_width=True, key="w_pub_single_btn"):
                        ok, msg = publish_memos([pub_single])
                        if ok: st.success(msg); clear_cache_and_reload(); time.sleep(1); st.rerun()
                        else: st.error(msg)
                else:
                    st.success("✅ جميع المذكرات منشورة!")

                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("⬅️ العودة للمراجعة", use_container_width=True, key="w_back4"):
                    st.session_state['wizard_step'] = 3; st.rerun()

        else:
            # ======================================================
            # لوحة التحكم العادية
            # ======================================================
            col1, col2 = st.columns([4, 1])
            with col2:
                if st.button("خروج"): logout()
            st.header("📊 لوحة تحكم الإدارة")

            # زر الـ Wizard
            if st.button("🎓 برنامج المناقشات", use_container_width=False, key="open_wizard"):
                st.session_state['admin_mode'] = 'defense_wizard'
                st.session_state['wizard_step'] = 1
                st.rerun()

            st.markdown("<br>", unsafe_allow_html=True)
        st_s = len(df_students); t_m = len(df_memos); r_m = len(df_memos[df_memos["تم التسجيل"].astype(str).str.strip() == "نعم"])
        a_m = t_m - r_m; t_p = len(df_prof_memos["الأستاذ"].unique())
        memo_col = df_students["رقم المذكرة"].astype(str).str.strip()
        reg_st = (memo_col != "").sum()
        unreg_st = (memo_col == "").sum()
        st.markdown('<div class="kpi-grid">', unsafe_allow_html=True)
        st.markdown(f'<div class="kpi-card"><div class="kpi-value">{st_s}</div><div class="kpi-label">الطلاب</div></div><div class="kpi-card"><div class="kpi-value">{t_p}</div><div class="kpi-label">الأساتذة</div></div><div class="kpi-card"><div class="kpi-value">{t_m}</div><div class="kpi-label">إجمالي المذكرات</div></div><div class="kpi-card" style="border-color: #10B981;"><div class="kpi-value" style="color: #10B981;">{r_m}</div><div class="kpi-label">مذكرات مسجلة</div></div><div class="kpi-card" style="border-color: #F59E0B;"><div class="kpi-value" style="color: #F59E0B;">{a_m}</div><div class="kpi-label">مذكرات متاحة</div></div><div class="kpi-card" style="border-color: #10B981;"><div class="kpi-value" style="color: #10B98E;">{reg_st}</div><div class="kpi-label">طلاب مسجلين</div></div><div class="kpi-card" style="border-color: #F59E0B;"><div class="kpi-value" style="color: #F59E0B;">{unreg_st}</div><div class="kpi-label">طلاب غير مسجلين</div></div></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs(["المذكرات", "الطلاب", "الأساتذة", "تقارير", "تحديث", "إدارة الطلبات", "📧 إرسال إيميلات", "📅 جدولة المناقشات"])
        
        with tab1:
            st.subheader("جدول المذكرات")
            f_status = st.selectbox("تصفية:", ["الكل", "مسجلة", "متاحة"])
            if f_status == "الكل": d_memos = df_memos
            elif f_status == "مسجلة": d_memos = df_memos[df_memos["تم التسجيل"].astype(str).str.strip() == "نعم"]
            else: d_memos = df_memos[df_memos["تم التسجيل"].astype(str).str.strip() != "نعم"]
            st.dataframe(d_memos, use_container_width=True, height=400)
        with tab2:
            st.subheader("قائمة الطلاب")
            q = st.text_input("بحث (لقب/اسم):")
            
            if st.session_state.get('admin_edit_student_user'):
                target_user = st.session_state.admin_edit_student_user
                student_data = df_students[df_students["اسم المستخدم"] == target_user]
                if not student_data.empty:
                    s = student_data.iloc[0]
                    vals = s.tolist()
                    
                    o_curr = vals[14] if len(vals) > 14 else ""
                    p_curr = vals[15] if len(vals) > 15 else ""
                    q_curr = vals[16] if len(vals) > 16 else ""
                    r_curr = vals[17] if len(vals) > 17 else ""
                    s_curr = vals[18] if len(vals) > 18 else ""
                    t_curr = vals[19] if len(vals) > 19 else ""

                    st.markdown(f"<h3>📝 تعديل ملف التخرج: {s.get('لقب', '')} {s.get('إسم', '')}</h3>", unsafe_allow_html=True)
                    
                    with st.form("edit_diploma_form"):
                        c1, c2 = st.columns(2)
                        with c1:
                            new_o = st.selectbox("شهادة الميلاد", ["متوفر", "غير متوفر"], index=0 if o_curr=="متوفر" else 1)
                            new_p = st.selectbox("كشف1 (M1)", ["متوفر", "مدين", "محول", "خطأ في الكشف"], index=["متوفر", "مدين", "محول", "خطأ في الكشف"].index(p_curr) if p_curr in ["متوفر", "مدين", "محول", "خطأ في الكشف"] else 0)
                            new_q = st.selectbox("كشف2 (M2)", ["غير متوفر", "متوفر"], index=0 if q_curr=="غير متوفر" else 1)
                        with c2:
                            new_r = st.selectbox("محضر المناقشة", ["غير متوفر", "متوفر"], index=0 if r_curr=="غير متوفر" else 1)
                            new_s = st.selectbox("حالة الملف", ["ناقص", "كامل", "كامل لحد الآن"], index=["ناقص", "كامل", "كامل لحد الآن"].index(s_curr) if s_curr in ["ناقص", "كامل", "كامل لحد الآن"] else 0)
                            new_t = st.selectbox("حالة الشهادة", ["غير جاهز", "جاهز", "تم التسليم"], index=["غير جاهز", "جاهز", "تم التسليم"].index(t_curr) if t_curr in ["غير جاهز", "جاهز", "تم التسليم"] else 0)
                        
                        col_s, col_c = st.columns([1, 4])
                        with col_s:
                            save_btn = st.form_submit_button("💾 حفظ", use_container_width=True)
                            cancel_btn = st.form_submit_button("❌ إلغاء", use_container_width=True)
                        
                        if save_btn:
                            updates = {'O': new_o, 'P': new_p, 'Q': new_q, 'R': new_r, 'S': new_s, 'T': new_t}
                            success, msg = update_diploma_status(target_user, updates)
                            if success: 
                                st.success(msg)
                                st.session_state.admin_edit_student_user = None
                                st.rerun()
                            else: st.error(msg)
                        
                        if cancel_btn:
                            st.session_state.admin_edit_student_user = None
                            st.rerun()

            if q:
                name_cols = [c for c in df_students.columns if 'اسم' in c.lower() or 'لقب' in c.lower() or 'إسم' in c.lower()]
                if name_cols:
                    mask = df_students[name_cols].astype(str).apply(lambda x: x.str.contains(q, case=False, na=False)).any(axis=1)
                    f_st = df_students[mask]
                else: f_st = df_students
                
                for idx, row in f_st.iterrows():
                    u_name = row.get('اسم المستخدم')
                    full_name = f"{row.get('لقب', '')} {row.get('إسم', '')}"
                    st.markdown(f"""
                    <div style="background:rgba(255,255,255,0.03); padding:10px; border-radius:8px; border:1px solid #333; display:flex; justify-content:space-between; align-items:center; margin-bottom:5px;">
                        <div>
                            <b style="color:#F8FAFC;">{full_name}</b><br>
                            <small style="color:#94A3B8;">{u_name} | {row.get('رقم التسجيل')}</small>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    c_edit, c_space = st.columns([1, 4])
                    with c_edit:
                        if st.button("📝 ملف التخرج", key=f"edit_{idx}", use_container_width=True):
                            st.session_state.admin_edit_student_user = u_name
                            st.rerun()
            else: 
                st.dataframe(df_students, use_container_width=True, height=400)

        with tab3:
            st.subheader("توزيع الأساتذة")
            if df_memos.empty:
                st.warning("لا توجد بيانات مذكرات للعرض.")
            else:
                if "الأستاذ" not in df_memos.columns:
                    st.error("العمود 'الأستاذ' غير موجود في ملف المذكرات.")
                else:
                    profs_list = sorted(df_memos["الأستاذ"].dropna().unique().tolist())
                    sel_p = st.selectbox("اختر أستاذ:", ["الكل"] + profs_list)
                    
                    if sel_p != "الكل":
                        st.dataframe(df_memos[df_memos["الأستاذ"].astype(str).str.strip() == sel_p.strip()], use_container_width=True, height=400)
                    else:
                        required_cols = ["الأستاذ", "رقم المذكرة", "تم التسجيل"]
                        missing_cols = [c for c in required_cols if c not in df_memos.columns]
                        
                        if not missing_cols:
                            s_df = df_memos.groupby("الأستاذ").agg(
                                total=("رقم المذكرة", "count"), 
                                registered=("تم التسجيل", lambda x: (x.astype(str).str.strip() == "نعم").sum())
                            ).reset_index()
                            s_df["المتاحة"] = s_df["total"] - s_df["registered"]
                            s_df = s_df.rename(columns={"total": "الإجمالي", "registered": "المسجلة"})
                            st.dataframe(s_df, use_container_width=True)
                        else:
                            st.error(f"بعض الأعمدة المطلوبة مفقودة: {', '.join(missing_cols)}")

        with tab4:
            st.subheader("التحليل الإحصائي")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("##### توزيع المذكرات حسب التخصص")
                spec_dist = df_memos.groupby("التخصص").size()
                st.bar_chart(spec_dist, color="#2F6F7E")
            with col2:
                st.markdown("##### حالة التسجيل حسب التخصص")
                reg_status = df_memos.groupby("التخصص")["تم التسجيل"].apply(lambda x: (x.astype(str).str.strip() == "نعم").sum())
                st.bar_chart(reg_status, color="#FFD700")
            st.markdown("---")
            st.markdown("##### نسب التقدم العامة")
            p_df = df_memos[df_memos["تم التسجيل"].astype(str).str.strip() == "نعم"].copy()
            if not p_df.empty and "نسبة التقدم" in p_df.columns:
                p_df["نسبة التقدم"] = p_df["نسبة التقدم"].apply(lambda x: int(x) if str(x).isdigit() else 0)
                avg_prog = p_df["نسبة التقدم"].mean()
                st.metric("متوسط نسبة الإنجاز", f"{avg_prog:.1f}%", delta_color="normal")
                st.markdown(f'<div class="progress-container"><div class="progress-bar" style="width: {avg_prog}%;">{avg_prog:.1f}%</div></div>', unsafe_allow_html=True)
                st.markdown("##### آخر التسجيلات")
                recent = df_memos[df_memos["تم التسجيل"].astype(str).str.strip() == "نعم"].tail(5)[["رقم المذكرة", "عنوان المذكرة", "الأستاذ", "تاريخ التسجيل"]]
                st.dataframe(recent, use_container_width=True, hide_index=True)
        with tab5:
            st.subheader("تحديث البيانات والربط")
            st.warning("⚠️ استخدم هذا الزر لربط أرقام التسجيل (أعمدة S و T) لأول مرة أو لإصلاح الأخطاء.")
            if st.button("🔄 بدء عملية الربط (Sync)", type="primary"):
                with st.spinner("جاري المعالجة... قد يستغرق وقتاً"):
                    s, m = sync_student_registration_numbers()
                    st.success(m) if s else st.info(m)
                    if s: clear_cache_and_reload(); st.rerun()
            st.markdown("---")
            if st.button("تحديث البيانات من Google Sheets"):
                with st.spinner("جاري التحديث..."):
                    clear_cache_and_reload()
                    st.success("✅ تم التحديث")
                    st.rerun()
        with tab6:
            st.subheader("سجل الطلبات الواردة")
            st.dataframe(df_requests, use_container_width=True, height=500)
        
        with tab7:
            st.subheader("إرسال رسالة ترحيب للأساتذة")
            send_mode = st.radio("اختر نوع العملية:", ["📩 إرسال لأستاذ محدد", "🚀 إرسال لجميع الأساتذة"], horizontal=True)
            st.markdown("---")
            if send_mode == "📩 إرسال لأستاذ محدد":
                st.info("أدخل بيانات الأستاذ لإرسال رسالة التفعيل له فقط.")
                prof_list = df_prof_memos["الأستاذ"].astype(str).dropna().unique().tolist()
                prof_list = list(set([p for p in prof_list if p.strip() and p.strip().lower() != "nan"]))
                prof_list.sort()
                selected_prof = st.selectbox("اختر الأستاذ من القائمة:", prof_list, index=None)
                col_s1, col_s2 = st.columns([1, 3])
                with col_s1:
                    send_single_btn = st.button("إرسال الآن", type="secondary", use_container_width=True)
                if send_single_btn and selected_prof:
                    success, msg = send_welcome_email_to_one(selected_prof)
                    if success: st.success(msg); st.balloons()
                    else: st.error(msg)
                elif send_single_btn and not selected_prof: st.warning("⚠️ يرجى اختيار اسم أستاذ من القائمة.")
            elif send_mode == "🚀 إرسال لجميع الأساتذة":
                st.info("تقوم هذه الأداة بإرسال إيميل يحتوي على بيانات الدخول لجميع الأساتذة.")
                st.write("عدد الأساتذة المستهدفين:", len(df_prof_memos))
                with st.expander("عرض قائمة الأساتذة المستهدفين"):
                     cols_available = df_prof_memos.columns.tolist()
                     target_cols = ["الأستاذ", "الأستاذة", "إسم المستخدم", "اسم المستخدم", "كلمة المرور", "البريد الإلكتروني", "الإيميل", "email", "Email"]
                     cols_to_display = [col for col in target_cols if col in cols_available]
                     if not cols_to_display: cols_to_display = cols_available[:3]
                     st.dataframe(df_prof_memos[cols_to_display].head(20))
                col_send, col_space = st.columns([1, 3])
                with col_send:
                    if st.button("🚀 بدء عملية الإرسال للجميع", type="primary"):
                        sent, failed, logs = send_welcome_emails_to_all_profs()
                        st.markdown("---")
                        st.success(f"تم الانتهاء! تم الإرسال بنجاح لـ {sent} أستاذ.")
                        if failed > 0: st.error(f"فشل الإرسال لـ {failed} أستاذ.")
                        with st.expander("سجل العمليات (Logs)", expanded=True):
                            for log in logs: st.text(log)

        with tab8:
            st.subheader("📅 جدولة مواعيد المناقشات")
            df_memos_fresh8 = load_memos()
            col_deposit = "حالة الإيداع"

            # إحصائيات
            if col_deposit in df_memos_fresh8.columns:
                total_deposited = len(df_memos_fresh8[df_memos_fresh8[col_deposit].astype(str).str.strip().isin(["مودعة","قابلة للمناقشة"])])
                total_approved  = len(df_memos_fresh8[df_memos_fresh8[col_deposit].astype(str).str.strip() == "قابلة للمناقشة"])
                already_scheduled = len(df_memos_fresh8[
                    (df_memos_fresh8[col_deposit].astype(str).str.strip() == "قابلة للمناقشة") &
                    (df_memos_fresh8.get("تاريخ المناقشة", pd.Series(dtype=str)).astype(str).str.strip().isin(["","nan"]) == False)
                ]) if "تاريخ المناقشة" in df_memos_fresh8.columns else 0
            else:
                total_deposited = total_approved = already_scheduled = 0

            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(f'<div class="kpi-card"><div class="kpi-value" style="color:#F59E0B;">{total_deposited}</div><div class="kpi-label">📤 مذكرات مودعة</div></div>', unsafe_allow_html=True)
            with c2:
                st.markdown(f'<div class="kpi-card"><div class="kpi-value" style="color:#10B981;">{total_approved}</div><div class="kpi-label">🟢 قابلة للمناقشة</div></div>', unsafe_allow_html=True)
            with c3:
                st.markdown(f'<div class="kpi-card"><div class="kpi-value" style="color:#2F6F7E;">{already_scheduled}</div><div class="kpi-label">📅 مجدولة</div></div>', unsafe_allow_html=True)

            st.markdown("---")

            if col_deposit not in df_memos_fresh8.columns:
                st.info("ℹ️ لم يُودَع أي ملف بعد. ستظهر البيانات هنا بعد أول إيداع.")
            else:
                defense_ready = df_memos_fresh8[df_memos_fresh8[col_deposit].astype(str).str.strip() == "قابلة للمناقشة"]

                if defense_ready.empty:
                    st.info("⏳ لا توجد مذكرات معتمدة للمناقشة حالياً. يجب أن يوافق الأستاذ المشرف أولاً.")
                else:
                    st.markdown("### 🟢 تحديد موعد المناقشة")
                    memo_options = defense_ready["رقم المذكرة"].astype(str).tolist()
                    selected_memo_def = st.selectbox("اختر المذكرة:", memo_options, key="admin_defense_select")

                    if selected_memo_def:
                        sel_row = defense_ready[defense_ready["رقم المذكرة"].astype(str) == selected_memo_def].iloc[0]

                        # معلومات المذكرة
                        st.markdown(f"""
                        <div class="card" style="border-top: 3px solid #10B981;">
                            <p>📄 <b>العنوان:</b> {sel_row.get('عنوان المذكرة','')}</p>
                            <p>👨‍🏫 <b>المشرف:</b> {sel_row.get('الأستاذ','')}</p>
                            <p>🎓 <b>التخصص:</b> {sel_row.get('التخصص','')}</p>
                            <p>👤 <b>الطالب الأول:</b> {sel_row.get('الطالب الأول','')}</p>
                            <p>👤 <b>الطالب الثاني:</b> {sel_row.get('الطالب الثاني','--')}</p>
                        </div>
                        """, unsafe_allow_html=True)

                        dep_link = str(sel_row.get("رابط الملف","")).strip()
                        if dep_link and dep_link != "nan":
                            st.markdown(f"📎 [**عرض المذكرة المودعة على Drive**]({dep_link})")

                        st.markdown("#### 📅 تحديد موعد ومكان المناقشة")
                        curr_date = str(sel_row.get("تاريخ المناقشة","")).strip()
                        curr_time = str(sel_row.get("توقيت المناقشة","")).strip()
                        curr_room = str(sel_row.get("القاعة","")).strip()

                        ca, cb, cc = st.columns(3)
                        with ca:
                            try:
                                default_date = datetime.strptime(curr_date, "%Y-%m-%d").date() if curr_date not in ["","nan"] else date.today()
                            except:
                                default_date = date.today()
                            defense_date = st.date_input("📆 تاريخ المناقشة", value=default_date, key=f"def_date_{selected_memo_def}")
                        with cb:
                            try:
                                default_time = datetime.strptime(curr_time, "%H:%M").time() if curr_time not in ["","nan"] else datetime.strptime("09:00", "%H:%M").time()
                            except:
                                default_time = datetime.strptime("09:00", "%H:%M").time()
                            defense_time = st.time_input("🕐 التوقيت", value=default_time, key=f"def_time_{selected_memo_def}")
                        with cc:
                            defense_room = st.text_input("🏛️ القاعة", value=curr_room if curr_room not in ["","nan"] else "", key=f"def_room_{selected_memo_def}", placeholder="مثال: قاعة A01")

                        if st.button("💾 حفظ موعد المناقشة", type="primary", use_container_width=True, key=f"save_defense_{selected_memo_def}"):
                            if not defense_room.strip():
                                st.error("⚠️ يرجى إدخال اسم القاعة.")
                            else:
                                ok, msg = save_defense_schedule(
                                    selected_memo_def,
                                    str(defense_date),
                                    str(defense_time),
                                    defense_room.strip()
                                )
                                if ok:
                                    # إرسال إيميل للطلبة
                                    df_students_def = load_students()
                                    df_students_def['رقم التسجيل_norm'] = df_students_def['رقم التسجيل'].astype(str).apply(normalize_text)
                                    s1_def = None; s2_def = None
                                    sel_vals = sel_row.tolist() if hasattr(sel_row, 'tolist') else list(sel_row.values())
                                    reg1_def = normalize_text(sel_row.get("رقم تسجيل الطالب 1", sel_vals[18] if len(sel_vals) > 18 else ""))
                                    reg2_def = normalize_text(sel_row.get("رقم تسجيل الطالب 2", sel_vals[19] if len(sel_vals) > 19 else ""))
                                    if reg1_def and reg1_def not in ["", "nan"]:
                                        r = df_students_def[df_students_def["رقم التسجيل_norm"] == reg1_def]
                                        if not r.empty: s1_def = r.iloc[0].to_dict()
                                    if reg2_def and reg2_def not in ["", "nan"]:
                                        r = df_students_def[df_students_def["رقم التسجيل_norm"] == reg2_def]
                                        if not r.empty: s2_def = r.iloc[0].to_dict()
                                    email_ok, email_msg = send_defense_schedule_email(
                                        selected_memo_def, str(sel_row.get('عنوان المذكرة','')),
                                        str(sel_row.get('الأستاذ','')),
                                        str(defense_date), str(defense_time), defense_room.strip(),
                                        s1_def, s2_def
                                    )
                                    if email_ok: st.info("📧 تم إرسال إشعار الموعد للطلبة.")
                                    else: st.warning(f"تم الحفظ لكن فشل الإيميل: {email_msg}")
                                    st.success(msg)
                                    clear_cache_and_reload()
                                    time.sleep(1)
                                    st.rerun()
                                else:
                                    st.error(msg)

                st.markdown("---")
                st.markdown("### 🔓 إعادة فتح الإيداع (في حالة خطأ الطالب)")
                st.info("استخدم هذا الخيار فقط عند طلب الطالب تصحيح ملف خاطئ. سيُمحى الإيداع السابق.")
                all_deposited_list = df_memos_fresh8[
                    df_memos_fresh8[col_deposit].astype(str).str.strip().isin(["مودعة","قابلة للمناقشة"])
                ]["رقم المذكرة"].astype(str).tolist()
                if all_deposited_list:
                    reset_memo_sel = st.selectbox("اختر المذكرة لإعادة الفتح:", all_deposited_list, key="reset_deposit_sel")
                    if st.button("🔓 إعادة فتح الإيداع", key="reset_deposit_btn"):
                        ok, msg = reset_memo_deposit(reset_memo_sel)
                        if ok: st.success(msg); clear_cache_and_reload(); time.sleep(1); st.rerun()
                        else: st.error(msg)
                else:
                    st.caption("لا توجد مذكرات مودعة حالياً.")

                st.markdown("---")
                st.markdown("### 📋 جدول كامل بحالات الإيداع")
                display_cols = ["رقم المذكرة","عنوان المذكرة","الأستاذ","التخصص","حالة الإيداع","تاريخ إيداع المذكرة","تاريخ المناقشة","توقيت المناقشة","القاعة"]
                available_cols = [c for c in display_cols if c in df_memos_fresh8.columns]
                filter_dep = st.selectbox("تصفية حسب الحالة:", ["الكل","مودعة","قابلة للمناقشة","لم تودَع"], key="filter_deposit_admin")
                if filter_dep == "مودعة":
                    show_df = df_memos_fresh8[df_memos_fresh8[col_deposit].astype(str).str.strip() == "مودعة"]
                elif filter_dep == "قابلة للمناقشة":
                    show_df = df_memos_fresh8[df_memos_fresh8[col_deposit].astype(str).str.strip() == "قابلة للمناقشة"]
                elif filter_dep == "لم تودَع":
                    show_df = df_memos_fresh8[~df_memos_fresh8[col_deposit].astype(str).str.strip().isin(["مودعة","قابلة للمناقشة"])]
                else:
                    show_df = df_memos_fresh8
                st.dataframe(show_df[available_cols], use_container_width=True, height=400)

st.markdown("---")
st.markdown('<div style="text-align:center; color:#64748B; font-size:12px; padding:20px;"> إشراف مسؤول الميدان البروفيسور لخضر رفاف © </div>', unsafe_allow_html=True)
