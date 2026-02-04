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

# ---------------- إعداد Logging ----------------
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ---------------- إعداد الصفحة ----------------
st.set_page_config(page_title="تسجيل مذكرات الماستر", page_icon="📘", layout="wide")

# ========================
# إعداد الموعد النهائي
# ========================
REGISTRATION_DEADLINE = datetime(2027, 1, 28, 23, 59)

# ---------------- CSS (تصميم زرقاء بلا حدود ومثبت) ----------------
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;900&display=swap" rel="stylesheet">
<style>
* { box-sizing: border-box; }
html, body, [class*="css"] {
    font-family: 'Cairo', sans-serif !important; direction: rtl; text-align: right;
}
.main { background-color: #0A1B2C; color: #ffffff; }
.block-container { padding: 2rem; background-color: #1A2A3D; border-radius: 16px; margin:auto; }
h1, h2, h3, h4 { font-weight: 700; margin-bottom: 1rem; color: #F8FAFC; }
label, p, span { color: #E2E8F0; }
.stTextInput label, .stSelectbox label { color: #F8FAFC !important; font-weight: 600; }
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
    background: rgba(30, 41, 59, 0.95); border: 1px solid rgba(255,255,255, 0.08);
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
.kpi-label { font-size: 1.2rem; color: #94A3B8; font-weight: 600; margin-top: 10px; }
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
.stDataFrame { border-radius: 12px; overflow: hidden; border: 1px solid rgba(255,255,white, 0.1); background: #1E293B; }
.stDataFrame th { background-color: #0F172A; color: #FFD700; font-weight: bold; }

/* ==================== تحسينات الـ Tabs ==================== */
.stTabs [data-baseweb="tab-list"] {
    gap: 1rem; padding-bottom: 15px;
    display: flex; flex-wrap: wrap; justify-content: center;
}
.stTabs [data-baseweb="tab"] {
    background: rgba(30, 41, 59, 0.5); color: #94A3B8; font-weight: 600; padding: 12px 24px; border-radius: 12px; border: 1px solid #334155;
    flex: 1 0 auto; text-align: center; min-width: 120px;
}
.stTabs [data-baseweb="tab"]:hover { background: rgba(255, 255, 255, 0.1); color: white; }
.stTabs [aria-selected="true"] {
    background: rgba(47, 111, 126, 0.8); color: #FFD700; border: 1px solid #2F6F7E; font-weight: bold; box-shadow: 0 0 15px rgba(47, 111, 126, 0.2);
}

/* ==================== تحويل Sidebar Radio إلى Tabs واضحة ==================== */
div[data-testid="stSidebar"] div[data-baseweb="radio-group"] div[role="radio"] span {
    display: none !important;
}
div[data-testid="stSidebar"] div[data-baseweb="radio-group"] label {
    background-color: #1E293B;
    color: #cbd5e1;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 15px;
    margin-bottom: 10px;
    font-size: 16px;
    cursor: pointer;
    transition: all 0.2s ease;
    display: flex;
    align-items: center;
    justify-content: center;
    text-align: center;
}
div[data-testid="stSidebar"] div[data-baseweb="radio-group"] label:hover {
    background-color: #334155;
    color: #ffffff;
    transform: translateX(-5px);
    border-color: #2F6F7E;
}
div[data-testid="stSidebar"] div[data-baseweb="radio-group"] label[aria-checked="true"] {
    background-color: #2F6F7E !important;
    color: #ffffff !important;
    border-color: #FFD700;
    font-weight: bold;
    box-shadow: 0 4px 12px rgba(47, 111, 126, 0.4);
}

.full-view-container {
    max-width: 1000px;
    margin: 0 auto;
    padding: 40px;
    background: rgba(15,23, 42, 0.5);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 24px;
    box-shadow: 0 0 40px rgba(0,0,0,0.6);
    overflow: hidden;
}
.students-grid {
    display: flex;
    justify-content: center;
    gap: 40px;
    flex-wrap: wrap;
    margin-top: 20px;
    margin-bottom: 30px;
}
.student-card {
    flex: 1;
    max-width: 450px;
    min-width: 300px;
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 16px;
    padding: 25px;
    text-align: center;
    transition: all 0.3s ease;
}
.student-card:hover {
    background: rgba(255, 255, 255, 0.06);
    border-color: #2F6F7E;
}
.memo-badge {
    display: inline-block; background: rgba(47, 111, 126, 0.2);
    color: #FFD700; padding: 6px 16px; border-radius: 20px;
    font-size: 1rem; margin-bottom: 10px; font-weight: 600;
}
.memo-id { font-size: 3rem; font-weight: 900; color: #2F6F7E; margin: 0; line-height: 1; }
</style>
""", unsafe_allow_html=True)

# ---------------- Google Sheets ----------------
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
try:
    info = st.secrets["service_account"]
    credentials = Credentials.from_service_account_info(info, scopes=SCOPES)
    sheets_service = build('sheets', 'v4', credentials=credentials)
except Exception as e:
    st.error("⚠️ خطأ في الاتصال بـ Google Sheets: تأكد من ملف Secrets.")
    st.stop()

STUDENTS_SHEET_ID = "1gvNkOVVKo6AO07dRKMnSQw6vZ3KdUnW7I4HBk61Sqns"
MEMOS_SHEET_ID = "1LNJMBAye4QIQy7JHz6F8mQ6-XNC1weZx1ozDZFfjD5s"
PROF_MEMOS_SHEET_ID = "1OnZi1o-oPMUI_W_Ew-op0a1uOhSj006hw_2jrMD6FSE"
REQUESTS_SHEET_ID = "1sTJ6BZRM4Qgt0w2xUkpFZqquL-hfriMYTSN3x1_12_o"

STUDENTS_RANGE = "Feuille 1!A1:N1000"
MEMOS_RANGE = "Feuille 1!A1:U1000"
PROF_MEMOS_RANGE = "Feuille 1!A1:P1000"
REQUESTS_RANGE = "Feuille 1!A1:K1000"

ADMIN_CREDENTIALS = {"admin": "admin2026", "dsp": "dsp@2026"}

EMAIL_SENDER = "domaine.dsp@univ-bba.dz"
EMAIL_PASSWORD = "qptlxzunqhdcjcjt"
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
        months_map = {
            1: "جانفي", 2: "فيفري", 3: "مارس", 4: "أفريل",
            5: "ماي", 6: "جوان", 7: "جويلية", 8: "أوت",
            9: "سبتمبر", 10: "أكتوبر", 11: "نوفمبر", 12: "ديسمبر"
        }
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

def validate_username(username):
    username = sanitize_input(username)
    if not username: return False, "⚠️ اسم المستخدم فارغ"
    return True, username

def validate_note_number(note_number):
    note_number = sanitize_input(note_number)
    if not note_number: return False, "⚠️ رقم المذكرة فارغ"
    if len(note_number) > 20: return False, "⚠️ رقم المذكرة غير صالح"
    return True, note_number

def get_email_smart(row):
    values_list = row.tolist()
    for i in range(9, 13):
        if i < len(values_list):
            val = str(values_list[i]).strip()
            if "@" in val and val != "nan":
                return val
    for col in row.index:
        clean_col_name = str(col).strip()
        if clean_col_name in ["البريد المهني", "البريد الإلكتروني", "email", "Email", "E-mail"]:
            val = str(row[col]).strip()
            if "@" in val and val != "nan":
                return val
    return ""

# دالة محدثة لتشمل رقم الهاتف
def get_student_info_from_memo(memo_row, df_students):
    student1_name = str(memo_row.get("الطالب الأول", "")).strip()
    student2_name = str(memo_row.get("الطالب الثاني", "")).strip()
    s1_email = s2_email = s1_reg_display = s2_reg_display = s1_phone = s2_phone = ""
    
    def get_contact_data(reg_number):
        if not reg_number: return {"email": "", "phone": ""}
        s_data = df_students[df_students["رقم التسجيل"].astype(str).str.strip() == reg_number]
        if not s_data.empty:
            row = s_data.iloc[0]
            email = get_email_smart(row)
            phone = str(row.get('الهاتف', '')).strip().replace('.0', '')
            return {"email": email, "phone": phone if phone and phone != 'nan' else "غير متوفر"}
        return {"email": "", "phone": "غير متوفر"}

    try:
        memo_list = memo_row.tolist()
        raw_reg1 = str(memo_list[18]).strip() if len(memo_list) > 18 else ""
        raw_reg2 = str(memo_list[19]).strip() if len(memo_list) > 19 else ""
        reg1 = raw_reg1.replace('.0', '')
        reg2 = raw_reg2.replace('.0', '')
    except:
        reg1 = str(memo_row.get("رقم تسجيل الطالب 1", "")).replace('.0', '').strip()
        reg2 = str(memo_row.get("رقم تسجيل الطالب 2", "")).replace('.0', '').strip()
    
    # جلب بيانات الطالب 1
    data1 = get_contact_data(reg1)
    s1_email = data1['email']; s1_phone = data1['phone']; s1_reg_display = reg1 if reg1 else ""

    # جلب بيانات الطالب 2
    if student2_name and reg2:
        data2 = get_contact_data(reg2)
        s2_email = data2['email']; s2_phone = data2['phone']; s2_reg_display = reg2 if reg2 else ""

    return {
        "s1_name": student1_name, "s1_email": s1_email, "s1_phone": s1_phone, "s1_reg": s1_reg_display,
        "s2_name": student2_name, "s2_email": s2_email, "s2_phone": s2_phone, "s2_reg": s2_reg_display
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

def update_student_phone(username, new_phone):
    try:
        df_students = load_students()
        student_row = df_students[df_students["اسم المستخدم"].astype(str).str.strip() == username]
        if student_row.empty: return False, "❌ لم يتم العثور على الطالب"
        row_idx = student_row.index[0] + 2
        body = {"values": [[new_phone]]}
        sheets_service.spreadsheets().values().update(
            spreadsheetId=STUDENTS_SHEET_ID,
            range=f"Feuille 1!M{row_idx}",
            valueInputOption="USER_ENTERED",
            body=body
        ).execute()
        clear_cache_and_reload()
        return True, "✅ تم تحديث رقم الهاتف بنجاح"
    except Exception as e:
        logger.error(f"خطأ في تحديث الهاتف: {str(e)}")
        return False, f"❌ حدث خطأ أثناء التحديث: {str(e)}"

def sync_student_registration_numbers():
    try:
        st.info("⏳ جاري بدء عملية الربط...")
        df_s = load_students()
        df_m = load_memos()
        updates = []
        students_with_memo = df_s[df_s["رقم المذكرة"].notna() & (df_s["رقم المذكرة"] != "")]
        for index, row in df_m.iterrows():
            memo_num = str(row.get("رقم المذكرة", "")).strip()
            if not memo_num: continue
            matched_students = students_with_memo[students_with_memo["رقم المذكرة"].astype(str).str.strip() == memo_num]
            if matched_students.empty: continue
            s1_name = str(row.get("الطالب الأول", "")).strip()
            s2_name = str(row.get("الطالب الثاني", "")).strip()
            reg_s1 = ""; reg_s2 = ""
            for _, s_row in matched_students.iterrows():
                lname = s_row.get('لقب', s_row.get('اللقب', ''))
                fname = s_row.get('إسم', s_row.get('الإسم', ''))
                full_name = f"{lname} {fname}".strip()
                if full_name == s1_name: reg_s1 = str(s_row.get("رقم التسجيل", ""))
                elif s2_name and full_name == s2_name: reg_s2 = str(s_row.get("رقم التسجيل", ""))
            if not reg_s1 and len(matched_students) > 0: reg_s1 = str(matched_students.iloc[0].get("رقم التسجيل", ""))
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
        memo_row = df_memos[df_memos["رقم المذكرة"].astype(str).str.strip() == str(memo_number).strip()]
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
# دوال الإيميل (محسنة: إرسال واحد لكل شيء)
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
    <html dir="rtl"><head><meta charset="UTF-8"><style>body {{ font-family: 'Cairo', Arial, sans-serif; direction: rtl; text-align: right; line-height: 1.6; background-color: #f4f4f4; margin: 0; padding: 0; }} .container {{ max-width: 600px; margin: 20px auto; background-color: #ffffff; padding: 30px; border: 1px solid #dddddd; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }} .header {{ text-align: center; margin-bottom: 30px; border-bottom: 2px solid #0056b3; padding-bottom: 20px; }} .header h2 {{ color: #003366; margin: 0; font-size: 24px; }} .header h3 {{ color: #005580; margin: 5px 0 0 0; font-size: 20px; }} .content {{ margin-bottom: 30px; color: #333; }} .content ul {{ padding-right: 20px; }} .info-box {{ background-color: #eef7fb; border-right: 5px solid #005580; padding: 20px; margin: 20px 0; border-radius: 4px; }} .info-box p {{ margin: 10px 0; font-weight: bold; font-size: 1.1em; }} .footer {{ text-align: center; margin-top: 40px; font-size: 14px; color: #666; border-top: 1px solid #eee; padding-top: 20px; }} .link {{ color: #005580; text-decoration: none; font-weight: bold; }} .link:hover {{ text-decoration: underline; }}</style></head><body><div class="container"><div class="header"><h2>جامعة محمد البشير الإبراهيمي – برج بوعريريج</h2><h3>كلية الحقوق والعلوم السياسية</h3><h4 style='color:#666; margin-top:5px;'>فضاء الأساتذة</h4></div><div class="content"><p>تحية طيبة وبعد،</p><p>الأستاذ (ة) الفاضل (ة) : <strong>{prof_name}</strong></p><br><p>في إطار رقمنة متابعة مذكّرات الماستر، يشرفنا إعلامكم بأنه تم تفعيل فضاء الأساتذة على منصة متابعة مذكرات الماستر الخاصة بكلية الحقوق والعلوم السياسية، وذلك قصد تسهيل عملية المتابعة البيداغوجية وتنظيم الإشراف.</p><p>يُمكِّنكم فضاء الأستاذ من القيام بالمهام التالية:</p><ul><li>متابعة حالة تسجيل كل مذكرة (مسجلة / غير مسجلة).</li><li>الاطلاع على أسماء الطلبة المسجلين وأرقام هواتفهم وبريدهم المهني.</li><li>تحديث نسبة التقدم في إنجاز المذكرات.</li><li>تحديد موعد جلسة إشراف واحدة يتم تعميمها آليًا على جميع الطلبة المعنيين.</li><li>إرسال طلبات إدارية رقمية للإدارة.</li></ul><div class="info-box"><p>الدخول إلى حسابكم يكون عبر الرابط:</p><a href="https://memoires2026.streamlit.app" class="link">https://memoires2026.streamlit.app</a><p style="margin-top: 15px;">إسم المستخدم: <span style="background:#fff; padding:2px 8px; border:1px solid #ccc; border-radius:4px;">{username}</span></p><p>كلمة المرور: <span style="background:#fff; padding:2px 8px; border:1px solid #ccc; border-radius:4px;">{password}</span></p></div></div><div class="footer"><p>تقبلوا تحياتنا الطيبة.</p><p>مسؤول الميدان: الدكتور لخضر رفاف</p></div></div></body></html>
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

def send_session_emails(students_data, session_info, prof_name):
    try:
        df_students = load_students()
        student_emails = []
        students_list_html = "<ul style='list-style-type: square; padding-right: 20px;'>"
        for s in students_data:
            s_row = df_students[df_students["رقم التسجيل"].astype(str).str.strip() == s['reg']]
            if not s_row.empty:
                email = ""
                possible_cols = ["البريد المهني", "البريد الإلكتروني", "email", "Email"]
                for col in possible_cols:
                    if col in s_row.columns:
                        val = str(s_row.iloc[0][col]).strip()
                        if val and val != "nan" and "@" in val: email = val; break
                if email: student_emails.append(email)
            students_list_html += f"<li style='margin-bottom: 5px;'>{s['name']} (رقم تسجيل: {s['reg']})</li>"
        students_list_html += "</ul>"
        subject = f"🔔 تنبيه هام: جلسة إشراف - {prof_name}"
        email_body = f"""
        <html dir="rtl">
        <head>
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f4f4; margin: 0; padding: 20px; }}
                .container {{ max-width: 600px; margin: 0 auto; background-color: #ffffff; padding: 30px; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); border-top: 5px solid #2F6F7E; }}
                .header {{ text-align: center; margin-bottom: 25px; border-bottom: 1px solid #eee; padding-bottom: 20px; }}
                .session-box {{ background-color: #eef2f5; padding: 15px; border-radius: 8px; text-align: center; margin: 20px 0; border: 1px solid #d1d9e6; }}
                .student-list {{ background-color: #fafafa; padding: 20px; border-radius: 8px; border: 1px solid #eee; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2 style="color: #2F6F7E; margin: 0;">📅 جدولة جلسة إشراف</h2>
                </div>
                <p>السلام عليكم ورحمة الله وبركاته،</p>
                <p>يُعلن الأستاذ(ة) <b>{prof_name}</b> عن تنظيم جلسة إشراف للمذكرات.</p>
                <div class="session-box">
                    <h3 style="margin: 0 0 10px 0; color: #333;">📆 الموعد:</h3>
                    <p style="font-size: 1.2em; color: #2F6F7E; font-weight: bold;">{session_info}</p>
                </div>
                <p>يُرجى من الطلبة التاليين الحضور والتحضير للموضوعات المخصصة لهم:</p>
                <div class="student-list">{students_list_html}</div>
                <p style="margin-top: 20px; font-size: 0.9em; color: #666;"><i>* تم إرسال هذا الإشعار للأستاذ والإدارة تلقائياً.</i></p>
            </div>
        </body>
        </html>
        """
        msg = MIMEMultipart('alternative')
        msg['From'] = EMAIL_SENDER
        msg['To'] = ADMIN_EMAIL
        # إضافة الأستاذ في CC
        prof_email_row = df_prof_memos[df_prof_memos["الأستاذ"] == prof_name]
        if not prof_email_row.empty:
             prof_email = prof_email_row.iloc[0].get("البريد الإلكتروني", "")
             if prof_email: msg['Cc'] = prof_email
        # إضافة الطلاب في BCC
        if student_emails: msg['Bcc'] = ", ".join(student_emails)
        msg['Subject'] = subject
        msg.attach(MIMEText(email_body, 'html', 'utf-8'))
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)
        logger.info(f"✅ ONE Session email sent to Admin, Prof, and {len(student_emails)} students.")
        return True, "تم الإرسال بنجاح"
    except Exception as e:
        logger.error(f"Error sending session emails: {e}")
        return False, str(e)

def send_email_to_professor(prof_name, memo_info, student1, student2=None):
    # ... (كود دالة الإيميل للأستاذ كما هو، لم يتغير) ...
    # نحتفظ بالكود القديم لتقليل الحجم في الرد، لكن يفضل أن تضعه كما كان
    # للتأكد من أن كل شيء يعمل، انسخ دالة send_email_to_professor من ملفك الأصلي
    pass 

# -------------------------------------------------------------
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
        s1_reg = str(memo.get("رقم تسجيل الطالب 1", memo.get("رقم التسجيل 1", ""))).strip()
        if s1_name and s1_name != "--" and s1_reg: students_data.append({"name": s1_name, "reg": s1_reg, "memo": memo.get("رقم المذكرة")})
        s2_name = str(memo.get("الطالب الثاني", "")).strip()
        s2_reg = str(memo.get("رقم تسجيل الطالب 2", memo.get("رقم التسجيل 2", ""))).strip()
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
    # ... (تم استبدال الدالة بالكامل بالنسخة المحسنة أعلاه) ...
    # (ملاحظة: لقد وضعت النسخة المحسنة في الأعلى، تأكد من نسخها فقط)
    pass

# ================= دوال التحقق والتحديث =================
def verify_student(username, password, df_students):
    valid, result = validate_username(username)
    if not valid: return False, result
    username = result
    password = sanitize_input(password)
    if df_students.empty: return False, "❌ خطأ في تحميل بيانات الطلاب"
    student = df_students[df_students["اسم المستخدم"].astype(str).str.strip() == username]
    if student.empty: return False, "❌ اسم المستخدم غير موجود"
    if student.iloc[0]["كلمة السر"].strip() != password: return False, "❌ كلمة السر غير صحيحة"
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
    if any(col not in df_prof_memos.columns for col in required_cols): return False, f"❌ الأعمدة التالية غير موجودة: {', '.join([col for col in required_cols if col not in df_prof_memos.columns])}"
    prof = df_prof_memos[(df_prof_memos["إسم المستخدم"].astype(str).str.strip() == username) & (df_prof_memos["كلمة المرور"].astype(str).str.strip() == password)]
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
    memo_row = df_memos[df_memos["رقم المذكرة"].astype(str).str.strip() == note_number]
    if memo_row.empty: return False, None, "❌ رقم المذكرة غير موجود"
    memo_row = memo_row.iloc[0]
    if str(memo_row.get("تم التسجيل", "")).strip() == "نعم": return False, None, "❌ هذه المذكرة مسجلة مسبقاً"
    prof_row = df_prof_memos[(df_prof_memos["الأستاذ"].astype(str).str.strip() == memo_row["الأستاذ"].strip()) & (df_prof_memos["كلمة سر التسجيل"].astype(str).str.strip() == prof_password)]
    if prof_row.empty: return False, None, "❌ كلمة سر المشرف غير صحيحة"
    return True, prof_row.iloc[0].to_dict(), None

def update_registration(note_number, student1, student2=None):
    # ... (كود التسجيل كما هو، لم يتغير) ...
    # لتوفير المساحة في الرد، يرجى نسخ دالة update_registration من نسختك الأصلية
    # لأننا لم نغير فيها شيئاً
    pass

# ============================================================
# جلب البيانات
# ============================================================
df_students = load_students(); df_memos = load_memos(); df_prof_memos = load_prof_memos(); df_requests = load_requests()
if df_students.empty or df_memos.empty or df_prof_memos.empty: st.error("❌ خطأ في تحميل البيانات. يرجى المحاولة لاحقاً."); st.stop()

# ============================================================
# دوال استعادة الجلسة (Persistence Logic) - مع Base64
# ============================================================

def encode_str(s): 
    return base64.urlsafe_b64encode(s.encode()).decode()

def decode_str(s): 
    try: return base64.urlsafe_b64decode(s.encode()).decode()
    except: return ""

def lookup_student(username):
    if df_students.empty: return None
    s = df_students[df_students["اسم المستخدم"].astype(str).str.strip() == username]
    if not s.empty: return s.iloc[0].to_dict()
    return None

def lookup_professor(username):
    if df_prof_memos.empty: return None
    p = df_prof_memos[df_prof_memos["إسم المستخدم"].astype(str).str.strip() == username]
    if not p.empty: return p.iloc[0].to_dict()
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
                st.session_state.user_type = 'student'; st.session_state.logged_in = True
                st.session_state.student1 = s_data; st.session_state.student2 = None
                note_num = str(s_data.get('رقم المذكرة', '')).strip()
                st.session_state.mode = "view" if note_num else "register"
        elif user_type == 'professor':
            p_data = lookup_professor(username)
            if p_data: st.session_state.user_type = 'professor'; st.session_state.logged_in = True; st.session_state.professor = p_data
        elif user_type == 'admin':
            if username in ADMIN_CREDENTIALS:
                st.session_state.user_type = 'admin'; st.session_state.logged_in = True; st.session_state.admin_user = username

restore_session_from_url()

# ============================================================
# تهيئة Session State
# ============================================================
required_state = {
    'user_type': None, 'logged_in': False, 'student1': None, 'student2': None,
    'professor': None, 'admin_user': None, 'memo_type': "فردية", 'mode': "register",
    'note_number': "", 'prof_password': "", 'show_confirmation': False, 'selected_memo_id': None
}
for key, value in required_state.items():
    if key not in st.session_state: st.session_state[key] = value

def logout():
    st.query_params.clear()
    for key in list(st.session_state.keys()):
        if key not in ['user_type']: del st.session_state[key]
    st.session_state.update({'logged_in': False, 'student1': None, 'student2': None, 'professor': None, 'admin_user': None, 'mode': "register", 'note_number': "", 'prof_password': "", 'show_confirmation': False, 'user_type': None, 'selected_memo_id': None})
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
# فضاء الطلبة (تم اختصار الجزء المتكرر للتركيز على التحسينات)
# ============================================================
elif st.session_state.user_type == "student":
    # ... (ضع هنا الكود الخاص بفضاء الطلبة كما هو في ملفك الأصلي) ...
    # بما أن التحسينات كانت مركزة على الأستاذ والإيميلات، بقي هذا القسم على حاله
    # تأكد من نسخه من ملفك الأصلي لضمان عمل النظام
    pass

# ============================================================
# فضاء الأساتذة (مع التحسينات الجديدة)
# ============================================================
elif st.session_state.user_type == "professor":
    if not st.session_state.logged_in:
        col1, col2 = st.columns([4, 1])
        with col2:
            if st.button("رجوع", key="back_prof"):
                st.session_state.user_type = None
                st.rerun()
        st.markdown("<h2>فضاء الأساتذة</h2>", unsafe_allow_html=True)
        with st.form("prof_login_form"):
            c1, c2 = st.columns(2)
            with c1: u = st.text_input("اسم المستخدم")
            with c2: p = st.text_input("كلمة المرور", type="password")
            if st.form_submit_button("تسجيل الدخول"):
                v, r = verify_professor(u, p, df_prof_memos)
                if not v: st.error(r)
                else: 
                    st.session_state.professor = r; st.session_state.logged_in = True
                    st.query_params['ut'] = 'professor'
                    st.query_params['un'] = encode_str(st.session_state.professor['إسم المستخدم'])
                    st.rerun()
    else:
        prof = st.session_state.professor; prof_name = prof["الأستاذ"]
        
        # ==================== تنبيه: حالة عرض مذكرة واحدة ====================
        if st.session_state.get('selected_memo_id'):
            memo_id = st.session_state.selected_memo_id
            current_memo = df_memos[df_memos["رقم المذكرة"].astype(str).str.strip() == memo_id].iloc[0]
            student_info = get_student_info_from_memo(current_memo, df_students)
            col_back, _, _ = st.columns([1, 8, 1])
            with col_back:
                if st.button("⬅️ العودة للقائمة"): st.session_state.selected_memo_id = None; st.rerun()
            st.markdown("<br>", unsafe_allow_html=True)
            
            progress_val = str(current_memo.get('نسبة التقدم', '0')).strip()
            try: prog_int = int(progress_val) if progress_val else 0
            except: prog_int = 0
            
            # HTML البطاقة المحسنة (مع رقم الهاتف)
            student_cards_html = f"""
<div class="student-card">
    <h4 style="color: #FFD700; margin-top: 0; font-size: 1.1rem;">الطالب الأول</h4>
    <p style="font-size: 1.3rem; font-weight: bold; margin: 15px 0 5px 0; color: #fff;">{student_info['s1_name']}</p>
    <p style="font-size: 0.9rem; color: #94A3B8;">رقم التسجيل: {student_info['s1_reg'] or '--'}</p>
    
    <div style="margin-top: 15px; background: rgba(15, 23, 42, 0.6); border-radius: 8px; padding: 10px;">
        <div style="display: flex; align-items: center; margin-bottom: 5px;">
            <span style="font-size: 1.2em; margin-left: 8px;">📧</span>
            <span style="color: #10B981; font-size: 0.9rem;">{student_info['s1_email'] or 'غير متوفر'}</span>
        </div>
        <div style="display: flex; align-items: center; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 5px;">
            <span style="font-size: 1.2em; margin-left: 8px;">📱</span>
            <span style="color: #F59E0B; font-weight: bold; font-size: 0.95rem;">{student_info['s1_phone']}</span>
        </div>
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
                            target = df_students[df_students["رقم التسجيل"] == reg_to_add]
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

        # ==================== القائمة الرئيسية مع Sidebar Tabs ====================
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

            # === القائمة في الـ Sidebar ===
            options = [
                "📝 المذكرات المسجلة", 
                "📅 جدولة جلسة إشراف", 
                "🔑 كلمات السر", 
                "⏳ المذكرات المتاحة"
            ]
            
            with st.sidebar:
                st.markdown("### 📚 قائمة الأستاذ")
                selected_page = st.radio("تنقل:", options, label_visibility="collapsed")

            # عرض المحتوى
            if selected_page == options[0]: # المذكرات المسجلة
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

            elif selected_page == options[1]: # جدولة جلسة
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
                                        # استدعاء الدالة المحسنة (إيميل واحد للجميع)
                                        email_success, email_msg = send_session_emails(target_students, details_text, prof_name) 
                                        if email_success: st.success("📧 تم إرسال الإشعارات للطلبة والإدارة.")
                                        else: st.warning(f"⚠️ تم الحفظ لكن فشل الإرسال: {email_msg}")
                                        time.sleep(2); st.rerun()
                                    else: st.error(f"تم حفظ الطلب ولكن حدث خطأ في تحديث المذكرات: {update_msg}")
                                else: st.error(save_msg)

            elif selected_page == options[2]: # كلمات السر
                st.subheader("🔑 كلمات السر")
                pwds = df_prof_memos[df_prof_memos["الأستاذ"].astype(str).str.strip() == prof_name.strip()]
                if not pwds.empty:
                    for _, row in pwds.iterrows():
                        stat = str(row.get("تم التسجيل", "")).strip()
                        pwd = str(row.get("كلمة سر التسجيل", "")).strip()
                        if pwd:
                            color = "#10B981" if stat == "نعم" else "#F59E0B"
                            status_txt = "مستخدمة" if stat == "نعم" else "متاحة"
                            st.markdown(f'''<div class="card" style="border-right:5px solid {color}; display:flex; justify-content:space-between; align-items:center;"><div><h3 style="margin:0; font-family:monospace; font-size:1.8rem; color:#FFD700;">{pwd}</h3><p style="margin:5px 0 0 0 0; color:#94A3B8;">الحالة: {status_txt}</p></div></div>''', unsafe_allow_html=True)
                else: st.info("لا توجد كلمات سر مسندة إليك.")
            
            elif selected_page == options[3]: # المذكرات المتاحة
                st.subheader("⏳ المذكرات المتاحة للتسجيل")
                if is_exhausted: st.info("💡 لقد استنفذت العناوين الأربعة المخصصة لك.")
                else:
                    avail = prof_memos[prof_memos["تم التسجيل"].astype(str).str.strip() != "نعم"]
                    if not avail.empty:
                        for _, m in avail.iterrows():
                            st.markdown(f'''<div class="card" style="border-left:4px solid #64748B;"><h4>{m['رقم المذكرة']}</h4><p>{m['عنوان المذكرة']}</p><p style="color:#94A3B8;">تخصص: {m['التخصص']}</p></div>''', unsafe_allow_html=True)
                    else: st.success("✅ جميع المذكرات مسجلة أو مقترحة!")

# ============================================================
# فضاء الإدارة (تم الاختصار للتركيز على التحسينات)
# ============================================================
elif st.session_state.user_type == "admin":
    # ... (ضع هنا الكود الخاص بفضاء الإدارة كما هو في ملفك الأصلي) ...
    # بما أن التحسينات كانت مركزة على الأستاذ، بقي هذا القسم على حاله
    # تأكد من نسخه من ملفك الأصلي لضمان عمل النظام
    pass

st.markdown("---")
st.markdown('<div style="text-align:center; color:#64748B; font-size:12px; padding:20px;">  إشراف مسؤول الميدان الدكتور لخضر رفاف © </div>', unsafe_allow_html=True)