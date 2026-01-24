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
st.set_page_config(page_title="تسجيل مذكرات الماستر", page_icon="📘", layout="wide")

# ---------------- CSS (تصميم زرقاء بلا حدود) ----------------
# تم استعادة التصميم الأصلي كما هو
st.markdown("""
<!-- استدعاء خط احترافي -->
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;900&display=swap" rel="stylesheet">

<style>
html, body, [class*="css"] { 
    font-family: 'Cairo', sans-serif !important; direction: rtl; text-align: right; 
}

/* الخلفية الأساسية */
.main { background-color: #0A1B2C; color: #ffffff; }
.block-container { padding: 2rem; background-color: #1A2A3D; border-radius: 16px; margin:auto; }

/* النصوص والعناوين */
h1, h2, h3, h4 { font-weight: 700; margin-bottom: 1rem; color: #F8FAFC; }
label, p, span { color: #E2E8F0; }
.stTextInput label, .stSelectbox label { color: #F8FAFC !important; font-weight: 600; }

/* =========================================
   الأزرار - تصميم موحد للجميع (أزرق، بدون حدود)
   ========================================= */
.stButton>button,
button[kind="primary"],
div[data-testid="stFormSubmitButton"] button {
    background-color: #2F6F7E !important;   /* خلفية زرقاء للجميع */
    color: #ffffff !important;              /* كتابة بيضاء للجميع */
    font-size: 16px;
    font-weight: 600;
    padding: 14px 32px;
    border: none !important;                /* بدون حدود */
    border-radius: 12px !important;        /* تدوير الزوايا */
    cursor: pointer;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
    transition: all 0.3s ease;
    width: 100%;
    text-align: center;
    display: flex; justify-content: center; align-items: center; gap: 10px;
}

/* تأثير عند مرور الماوس */
.stButton>button:hover,
button[kind="primary"]:hover,
div[data-testid="stFormSubmitButton"] button:hover {
    background-color: #285E6B !important;   /* لون أغمق عند المرور */
    transform: translateY(-2px);
    box-shadow: 0 8px 16px rgba(0, 0, 0, 0.3);
    font-weight: 700;
}

/* البطاقات الاحترافية (Glassmorphism) */
.card { 
    background: rgba(30, 41, 59, 0.95);
    border: 1px solid rgba(255,255,  white, 0.08);
    border-radius: 20px; padding: 30px; margin-bottom: 20px; 
    box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.2); 
    border-top: 3px solid #2F6F7E;
}
.card:hover {
    transform: translateY(-2px);
    box-shadow: 0 30px 40px -5px rgba(0, 0, 0, 0.4);
}

/* بطاقات الإحصائيات */
.kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 1.5rem; margin-bottom: 2.5rem; }
.kpi-card {
    background: linear-gradient(145deg, #1E293B, #0F172A);
    border: 1px solid rgba(255, 255, 255, 0.05); border-radius: 16px; padding: 2.5rem 1rem;
    text-align: center; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
    position: relative; overflow: hidden;
    transition: transform 0.3s ease;
}
.kpi-card::before {
    content: ""; position: absolute; top: 0; left: 0; right: 0; height: 5px;
    background: linear-gradient(90deg, #2F6F7E, #FFD700);
    opacity: 0.9;
}
.kpi-value { font-size: 2.5rem; font-weight: 900; color: #FFD700; margin: 15px 0; line-height: 1.2; text-shadow: 0 2px 4px rgba(0, 0, 0, 0.5); }
.kpi-label { font-size: 1.2rem; color: #94A3B8; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; margin-top: 10px; }

/* التنبيهات */
.alert-card {
    background: linear-gradient(90deg, #8B4513 0%, #A0522D 100%);
    border: 1px solid #CD853F; color: white; padding: 25px; border-radius: 12px;
    box-shadow: 0 10px 20px -5px rgba(139, 69, 19, 0.4);
    text-align: center; font-size: 16px; font-weight: bold;
}

/* شريط التقدم */
.progress-container { background-color: #0F172A; border-radius: 99px; padding: 6px; margin: 20px 0; overflow: hidden; box-shadow: inset 0 4px 6px rgba(0, 0, 0, 0.3); }
.progress-bar {
    height: 24px; border-radius: 99px;
    background: linear-gradient(90deg, #2F6F7E 0%, #285E6B 50%, #FFD700 100%);
    box-shadow: 0 0 15px rgba(47, 111, 126, 0.5);
    transition: width 1s cubic-bezier(0.4, 0, 0.2, 1);
}

/* الجداول */
.stDataFrame { border-radius: 12px; overflow: hidden; border: 1px solid rgba(255,255,  white, 0.1); background: #1E293B; }
.stDataFrame th { background-color: #0F172A; color: #FFD700; font-weight: bold; }

/* التبويبات */
.stTabs [data-baseweb="tab-list"] { gap: 2rem; padding-bottom: 15px; }
.stTabs [data-baseweb="tab"] { 
    background: transparent; color: #94A3B8; 
    font-weight: 600; padding: 12px 24px; border-radius: 12px; border: 1px solid transparent;
}
.stTabs [data-baseweb="tab"]:hover { background: rgba(255, 255, 255, 0.1); color: white; }
.stTabs [aria-selected="true"] { 
    background: rgba(47, 111, 126, 0.2); color: #FFD700; border: 1px solid #2F6F7E; font-weight: bold; box-shadow: 0 0 15px rgba(47, 111, 126, 0.2);
}
</style>
""", unsafe_allow_html=True)

# ---------------- Google Sheets ----------------
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
# تأكد من إعداد المفاتيح في إعدادات Streamlit Secrets
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
# شيت الطلبات الجديد
REQUESTS_SHEET_ID = "1sTJ6BZRM4Qgt0w2xUkpFZqquL-hfriMYTSN3x1_12_o"

STUDENTS_RANGE = "Feuille 1!A1:L1000"
# توسيع النطاق ليشمل الأعمدة S و T
MEMOS_RANGE = "Feuille 1!A1:T1000" 
PROF_MEMOS_RANGE = "Feuille 1!A1:P1000"
REQUESTS_RANGE = "Feuille 1!A1:K1000"

ADMIN_CREDENTIALS = {
    "admin": "admin2026",
    "dsp": "dsp@2026"
}

EMAIL_SENDER = "domaine.dsp@univ-bba.dz"
EMAIL_PASSWORD = "oevruyiztgikwzah"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
ADMIN_EMAIL = "domaine.dsp@univ-bba.dz"

# ---------------- دالة مساعدة ----------------
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

# دالة قوية لجلب الإيميل (الحل لمشكلة الإيميلات)
def get_student_email(reg_no, full_name_fallback, df_students):
    # 1. البحث برقم التسجيل (الأولوية)
    if reg_no:
        match = df_students[df_students["رقم التسجيل"].astype(str).str.strip() == str(reg_no).strip()]
        if not match.empty:
            for col in ["البريد الإلكتروني", "email", "Email"]:
                if col in match.columns:
                    email = match.iloc[0].get(col, "").strip()
                    if email and "@" in email: return email
    
    # 2. البحث بالاسم (احتياطي)
    if full_name_fallback:
        parts = full_name_fallback.strip().split(' ', 1)
        if len(parts) == 2:
            lname, fname = parts[0], parts[1]
            possible_lname = ["لقب", "اللقب"]
            possible_fname = ["إسم", "إسم", "اسم"]
            
            for pl in possible_lname:
                for pf in possible_fname:
                    if pl in df_students.columns and pf in df_students.columns:
                        match = df_students[
                            (df_students[pl].astype(str).str.strip() == lname) & 
                            (df_students[pf].astype(str).str.strip() == fname)
                        ]
                        if not match.empty:
                            for col in ["البريد الإلكتروني", "email", "Email"]:
                                if col in match.columns:
                                    email = match.iloc[0].get(col, "").strip()
                                    if email and "@" in email: return email
    return ""

# ---------------- تحميل البيانات ----------------
@st.cache_data(ttl=60)
def load_students():
    try:
        result = sheets_service.spreadsheets().values().get(spreadsheetId=STUDENTS_SHEET_ID, range=STUDENTS_RANGE).execute()
        values = result.get('values', [])
        if not values: return pd.DataFrame()
        df = pd.DataFrame(values[1:], columns=values[0])
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

# ---------------- الجديد: عملية الربط الذكي لـ S و T (الحل للمشكلة 1) ----------------
def sync_student_registration_numbers():
    try:
        st.info("⏳ جاري بدء عملية الربط...")
        df_s = load_students()
        df_m = load_memos()
        
        updates = []
        # الأعمدة 19 و 20 هي S و T
        col_s_idx = 19
        col_t_idx = 20
        
        students_with_memo = df_s[df_s["رقم المذكرة"].notna() & (df_s["رقم المذكرة"] != "")]
        
        # إنشاء قاموس: رقم المذكرة -> قائمة الطلاب
        memo_to_students = {}
        for _, s_row in students_with_memo.iterrows():
            m_id = str(s_row["رقم المذكرة"]).strip()
            reg_no = str(s_row.get("رقم التسجيل", "")).strip()
            
            # بناء الاسم للتحقق
            lname = s_row.get('لقب', s_row.get('اللقب', ''))
            fname = s_row.get('إسم', s_row.get('إسم', ''))
            full_name = f"{lname} {fname}".strip()
            
            if m_id not in memo_to_students: memo_to_students[m_id] = []
            memo_to_students[m_id].append({"reg": reg_no, "name": full_name})

        for index, row in df_m.iterrows():
            memo_id = str(row.get("رقم المذكرة", "")).strip()
            if not memo_id or memo_id not in memo_to_students: continue
            
            s1_name = str(row.get("الطالب الأول", "")).strip()
            s2_name = str(row.get("الطالب الثاني", "")).strip()
            
            students_in_this_memo = memo_to_students[memo_id]
            reg_s1 = ""
            reg_s2 = ""
            
            # 1. إذا كان هناك طالب ثاني في المذكرة، حاول مطابقته أولاً (للتأكد من العمود T)
            if s2_name:
                found_s2 = next((s for s in students_in_this_memo if s["name"] == s2_name), None)
                if found_s2:
                    reg_s2 = found_s2["reg"]
                    students_in_this_memo.remove(found_s2)
            
            # 2. الطالب المتبقي هو الطالب الأول (عمود S)
            if students_in_this_memo:
                candidate_s1 = students_in_this_memo[0]
                if candidate_s1["name"] == s1_name or not s1_name:
                    reg_s1 = candidate_s1["reg"]

            row_idx = index + 2 
            if reg_s1:
                updates.append({"range": f"Feuille 1!S{row_idx}", "values": [[reg_s1]]})
            if reg_s2:
                updates.append({"range": f"Feuille 1!T{row_idx}", "values": [[reg_s2]]})
        
        if updates:
            body = {"valueInputOption": "USER_ENTERED", "data": updates}
            sheets_service.spreadsheets().values().batchUpdate(spreadsheetId=MEMOS_SHEET_ID, body=body).execute()
            return True, f"✅ تم تحديث {len(updates)} خلية بنجاح."
        else:
            return False, "ℹ️ جميع البيانات محدثة أو لا توجد تطابقات."
            
    except Exception as e:
        logger.error(f"Migration Error: {str(e)}")
        return False, f"❌ حدث خطأ: {str(e)}"

# ---------------- الجديد: نظام الطلبات والشيت والايميل ----------------
def save_and_send_request(req_type, prof_name, memo_id, memo_title, details_text):
    try:
        # 1. الحفظ في شيت الطلبات
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        new_row = [
            "", timestamp, req_type, "قيد المراجعة", prof_name, memo_id, "", "", details_text, "", ""
        ]
        body_append = {"values": [new_row]}
        sheets_service.spreadsheets().values().append(
            spreadsheetId=REQUESTS_SHEET_ID, range="Feuille 1!A2",
            valueInputOption="USER_ENTERED", body=body_append, insertDataOption="INSERT_ROWS"
        ).execute()
        
        # 2. إرسال الإيميل
        request_titles = {
            "تغيير عنوان المذكرة": "طلب تغيير عنوان مذكرة",
            "حذف طالب": "طلب حذف طالب من مذكرة ثنائية",
            "إضافة طالب": "طلب إضافة طالب لمذكرة فردية",
            "تنازل": "طلب تنازل عن الإشراف"
        }
        subject = f"{request_titles.get(req_type, 'طلب جديد')} - {memo_id}"
        email_body = f"""
<html dir="rtl"><body style="font-family:sans-serif; padding:20px;">
    <div style="background:#f4f4f4; padding:30px; border-radius:10px; max-width:600px; margin:auto; color:#333;">
        <h2 style="background:#8B4513; color:white; padding:20px; border-radius:8px; text-align:center;">{subject}</h2>
        <p><strong>من:</strong> {prof_name}</p>
        <p><strong>رقم المذكرة:</strong> {memo_id}</p>
        <div style="background:#fff8dc; padding:15px; border-right:4px solid #8B4513; margin:15px 0; border-radius: 8px;">
            <h3>التفاصيل/المبررات:</h3>
            <p>{details_text}</p>
        </div>
    </div>
</body></html>"""
        msg = MIMEMultipart('alternative')
        msg['From'], msg['To'], msg['Subject'] = EMAIL_SENDER, ADMIN_EMAIL, subject
        msg.attach(MIMEText(email_body, 'html', 'utf-8'))
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls(); server.login(EMAIL_SENDER, EMAIL_PASSWORD); server.send_message(msg)
            
        return True, "✅ تم تسجيل الطلب في النظام وإرسال الإيميل للإدارة"
    except Exception as e:
        logger.error(f"Request Error: {str(e)}")
        return False, f"❌ حدث خطأ أثناء تسجيل الطلب: {str(e)}"

# ---------------- تحديث نسبة التقدم ----------------
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
        return True, "✅ تم تحديث نسبة التقدم بنجاح"
    except Exception as e:
        logger.error(f"خطأ في تحديث نسبة التقدم: {str(e)}")
        return False, f"❌ خطأ: {str(e)}"

# ---------------- التحقق ----------------
def verify_student(username, password, df_students):
    username = sanitize_input(username)
    password = sanitize_input(password)
    if df_students.empty: return False, "❌ خطأ في تحميل بيانات الطلاب"
    student = df_students[df_students["اسم المستخدم"].astype(str).str.strip() == username]
    if student.empty: return False, "❌ اسم المستخدم غير موجود"
    if student.iloc[0]["كلمة السر"].strip() != password: return False, "❌ كلمة السر غير صحيحة"
    return True, student.iloc[0]

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
    prof = df_prof_memos[
        (df_prof_memos["إسم المستخدم"].astype(str).str.strip() == username) &
        (df_prof_memos["كلمة المرور"].astype(str).str.strip() == password)
    ]
    if prof.empty: return False, "❌ اسم المستخدم أو كلمة السر غير صحيحة"
    return True, prof.iloc[0]

def verify_admin(username, password):
    username = sanitize_input(username); password = sanitize_input(password)
    if username in ADMIN_CREDENTIALS and ADMIN_CREDENTIALS[username] == password:
        return True, username
    return False, "❌ بيانات الإدارة غير صحيحة"

def verify_professor_password(note_number, prof_password, df_memos, df_prof_memos):
    note_number = sanitize_input(note_number)
    prof_password = sanitize_input(prof_password)
    if df_memos.empty or df_prof_memos.empty: return False, None, "❌ خطأ في تحميل البيانات"
    memo_row = df_memos[df_memos["رقم المذكرة"].astype(str).str.strip() == note_number]
    if memo_row.empty: return False, None, "❌ رقم المذكرة غير موجود"
    memo_row = memo_row.iloc[0]
    if str(memo_row.get("تم التسجيل", "")).strip() == "نعم": return False, None, "❌ هذه المذكرة مسجلة مسبقاً"
    prof_row = df_prof_memos[
        (df_prof_memos["الأستاذ"].astype(str).str.strip() == memo_row["الأستاذ"].strip()) &
        (df_prof_memos["كلمة سر التسجيل"].astype(str).str.strip() == prof_password)
    ]
    if prof_row.empty: return False, None, "❌ كلمة سر المشرف غير صحيحة"
    return True, prof_row.iloc[0], None

# ---------------- تحديث المذكرات ----------------
def update_registration(note_number, student1, student2=None):
    try:
        df_memos = load_memos(); df_prof_memos = load_prof_memos(); df_students = load_students()
        prof_name = df_memos[df_memos["رقم المذكرة"].astype(str).str.strip() == str(note_number).strip()]["الأستاذ"].iloc[0].strip()
        used_prof_password = st.session_state.prof_password.strip()
        
        prof_row_idx = df_prof_memos[
            (df_prof_memos["الأستاذ"].astype(str).str.strip() == prof_name) &
            (df_prof_memos["كلمة سر التسجيل"].astype(str).str.strip() == used_prof_password)
        ].index[0] + 2
        col_names = df_prof_memos.columns.tolist()
        
        s1_lname = student1.get('لقب', student1.get('اللقب', ''))
        s1_fname = student1.get('إسم', student1.get('إسم', ''))
        
        updates = [
            {"range": f"Feuille 1!{col_letter(col_names.index('الطالب الأول')+1)}{prof_row_idx}", "values": [[s1_lname + ' ' + s1_fname]]},
            {"range": f"Feuille 1!{col_letter(col_names.index('تم التسجيل')+1)}{prof_row_idx}", "values": [["نعم"]]},
            {"range": f"Feuille 1!{col_letter(col_names.index('تاريخ التسجيل')+1)}{prof_row_idx}", "values": [[datetime.now().strftime('%Y-%m-%d %H:%M')]]},
            {"range": f"Feuille 1!{col_letter(col_names.index('رقم المذكرة')+1)}{prof_row_idx}", "values": [[note_number]]}
        ]
        if student2 is not None:
            s2_lname = student2.get('لقب', student2.get('اللقب', ''))
            s2_fname = student2.get('إسم', student2.get('إسم', ''))
            updates.append({"range": f"Feuille 1!{col_letter(col_names.index('الطالب الثاني')+1)}{prof_row_idx}", "values": [[s2_lname + ' ' + s2_fname]]})
        
        sheets_service.spreadsheets().values().batchUpdate(spreadsheetId=PROF_MEMOS_SHEET_ID, body={"valueInputOption": "USER_ENTERED", "data": updates}).execute()

        memo_row_idx = df_memos[df_memos["رقم المذكرة"].astype(str).str.strip() == str(note_number).strip()].index[0] + 2
        memo_cols = df_memos.columns.tolist()
        
        reg1 = str(student1.get('رقم التسجيل', ''))
        reg2 = str(student2.get('رقم التسجيل', '')) if student2 else ""
        
        updates2 = [
            {"range": f"Feuille 1!{col_letter(memo_cols.index('الطالب الأول')+1)}{memo_row_idx}", "values": [[s1_lname + ' ' + s1_fname]]},
            {"range": f"Feuille 1!{col_letter(memo_cols.index('تم التسجيل')+1)}{memo_row_idx}", "values": [["نعم"]]},
            {"range": f"Feuille 1!{col_letter(memo_cols.index('تاريخ التسجيل')+1)}{memo_row_idx}", "values": [[datetime.now().strftime('%Y-%m-%d %H:%M')]]},
            {"range": f"Feuille 1!S{memo_row_idx}", "values": [[reg1]]} # العمود S
        ]
        if 'كلمة سر التسجيل' in memo_cols:
            updates2.append({"range": f"Feuille 1!{col_letter(memo_cols.index('كلمة سر التسجيل')+1)}{memo_row_idx}", "values": [[used_prof_password]]})
        if student2 is not None:
            updates2.append({"range": f"Feuille 1!{col_letter(memo_cols.index('الطالب الثاني')+1)}{memo_row_idx}", "values": [[s2_lname + ' ' + s2_fname]]})
            updates2.append({"range": f"Feuille 1!T{memo_row_idx}", "values": [[reg2]]}) # العمود T
            
        sheets_service.spreadsheets().values().batchUpdate(spreadsheetId=MEMOS_SHEET_ID, body={"valueInputOption": "USER_ENTERED", "data": updates2}).execute()

        students_cols = df_students.columns.tolist()
        student1_row_idx = df_students[df_students["اسم المستخدم"].astype(str).str.strip() == student1['اسم المستخدم'].strip()].index[0] + 2
        sheets_service.spreadsheets().values().update(spreadsheetId=STUDENTS_SHEET_ID, range=f"Feuille 1!{col_letter(students_cols.index('رقم المذكرة')+1)}{student1_row_idx}", valueInputOption="USER_ENTERED", body={"values": [[note_number]]}).execute()
        
        if student2 is not None:
            student2_row_idx = df_students[df_students["اسم المستخدم"].astype(str).str.strip() == student2['اسم المستخدم'].strip()].index[0] + 2
            sheets_service.spreadsheets().values().update(spreadsheetId=STUDENTS_SHEET_ID, range=f"Feuille 1!{col_letter(students_cols.index('رقم المذكرة')+1)}{student2_row_idx}", valueInputOption="USER_ENTERED", body={"values": [[note_number]]}).execute()

        time.sleep(2); clear_cache_and_reload(); time.sleep(1)
        
        df_students_updated = load_students()
        st.session_state.student1 = df_students_updated[df_students_updated["اسم المستخدم"].astype(str).str.strip() == student1['اسم المستخدم'].strip()].iloc[0]
        if student2 is not None:
            st.session_state.student2 = df_students_updated[df_students_updated["اسم المستخدم"].astype(str).str.strip() == student2['اسم المستخدم'].strip()].iloc[0]
        
        return True, "✅ تم تسجيل المذكرة بنجاح!"
    except Exception as e:
        logger.error(f"خطأ في تحديث التسجيل: {str(e)}")
        return False, f"❌ حدث خطأ أثناء التسجيل: {str(e)}"

# ---------------- Session State ----------------
if 'user_type' not in st.session_state:
    st.session_state.user_type = None
    st.session_state.logged_in = False
    st.session_state.student1 = None; st.session_state.student2 = None; st.session_state.professor = None
    st.session_state.admin_user = None; st.session_state.memo_type = "فردية"; st.session_state.mode = "register"
    st.session_state.note_number = ""; st.session_state.prof_password = ""; st.session_state.show_confirmation = False
    st.session_state.selected_memo = None # جديد: لتخزين المذكرة المختارة للنافذة المنبثقة

def logout():
    for key in st.session_state.keys():
        if key not in ['user_type']: del st.session_state[key]
    st.session_state.update({
        'logged_in': False, 'student1': None, 'student2': None, 'professor': None,
        'admin_user': None, 'mode': "register", 'note_number': "", 'prof_password': "", 'show_confirmation': False,
        'user_type': None, 'selected_memo': None
    })
    st.rerun()

df_students = load_students(); df_memos = load_memos(); df_prof_memos = load_prof_memos(); df_requests = load_requests()

if df_students.empty or df_memos.empty or df_prof_memos.empty:
    st.error("❌ خطأ في تحميل البيانات. يرجى المحاولة لاحقاً."); st.stop()

# ============================================================
# الصفحة الرئيسية (اختيار الفضاء)
# ============================================================
if st.session_state.user_type is None:
    st.markdown("<h1 style='text-align: center; margin-bottom: 1rem;'>نظام تسجيل المذكرات</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #94A3B8; font-size: 1.2rem; margin-bottom: جامعة محمد البشير الإبراهيمي - كلية الحقوق والعلوم السياسية</p>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("<div class='card' style='text-align: center;'>", unsafe_allow_html=True)
        st.markdown("<h3>👨‍🎓 فضاء الطلبة</h3>", unsafe_allow_html=True)
        st.markdown("<p style='color:#94A3B8'>تسجيل وعرض المذكرات</p>", unsafe_allow_html=True)
        if st.button("دخول الطلبة", key="btn_student", use_container_width=True):
            st.session_state.user_type = "student"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
            
    with col2:
        st.markdown("<div class='card' style='text-align: center;'>", unsafe_allow_html=True)
        st.markdown("<h3>👨‍🏫 فضاء الأساتذة</h3>", unsafe_allow_html=True)
        st.markdown("<p style='color:#94A3B8'>متابعة التقدم والطلبات</p>", unsafe_allow_html=True)
        if st.button("دخول الأساتذة", key="btn_prof", use_container_width=True):
            st.session_state.user_type = "professor"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
            
    with col3:
        st.markdown("<div class='card' style='text-align: center;'>", unsafe_allow_html=True)
        st.markdown("<h3>⚙️ فضاء الإدارة</h3>", unsafe_allow_html=True)
        st.markdown("<p style='color:#94A3B8'>إدارة النظام والتقارير</p>", unsafe_allow_html=True)
        if st.button("دخول الإدارة", key="btn_admin", use_container_width=True):
            st.session_state.user_type = "admin"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

# ============================================================
# فضاء الطلبة
# ============================================================
elif st.session_state.user_type == "student":
    if not st.session_state.logged_in:
        col1, col2 = st.columns([4, 1])
        with col2:
            if st.button("رجوع", key="back_student"):
                st.session_state.user_type = None
                st.rerun()
        
        st.markdown("<h2>فضاء الطلبة</h2>", unsafe_allow_html=True)
        st.session_state.memo_type = st.radio("اختر نوع المذكرة:", ["فردية", "ثنائية"], horizontal=True)
        
        with st.form("student_login_form"):
            username1 = st.text_input("اسم المستخدم الطالب الأول")
            password1 = st.text_input("كلمة السر الطالب الأول", type="password")
            
            username2 = password2 = None
            if st.session_state.memo_type == "ثنائية":
                st.markdown("---")
                username2 = st.text_input("اسم المستخدم الطالب الثاني")
                password2 = st.text_input("كلمة السر الطالب الثاني", type="password")
            
            submitted = st.form_submit_button("تسجيل الدخول")
            if submitted:
                if st.session_state.memo_type == "فردية":
                    if not username1 or not password1:
                        st.error("⚠️ يرجى إدخال اسم المستخدم وكلمة السر")
                        st.stop()
                
                if st.session_state.memo_type == "ثنائية":
                    if not username1 or not password1 or not username2 or not password2:
                        st.error("⚠️ يرجى إدخال بيانات الطالبين كاملة")
                        st.stop()
                    if username1.strip().lower() == username2.strip().lower(): 
                        st.error("❌ لا يمكن أن يكون الطالب الأول والثاني نفس الشخص!"); st.stop()

                students_data = [(username1, password1)]
                if st.session_state.memo_type == "ثنائية" and username2: students_data.append((username2, password2))
                
                valid, result = verify_students_batch(students_data, df_students)
                if not valid: 
                    st.error(result)
                else:
                    verified_students = result
                    if not verified_students:
                        st.error("حدث خطأ غير متوقع في التحقق من البيانات")
                        st.stop()

                    st.session_state.student1 = verified_students[0]
                    st.session_state.student2 = verified_students[1] if len(verified_students) > 1 else None
                    
                    if st.session_state.memo_type == "ثنائية" and st.session_state.student2 is not None:
                        s1_note = str(st.session_state.student1.get('رقم المذكرة', '')).strip()
                        s2_note = str(st.session_state.student2.get('رقم المذكرة', '')).strip()
                        s1_spec = str(st.session_state.student1.get('التخصص', '')).strip()
                        s2_spec = str(st.session_state.student2.get('التخصص', '')).strip()
                        
                        if s1_spec != s2_spec: st.error("❌ لا يمكن التسجيل الثنائي. الطالبان في تخصصين مختلفين"); st.session_state.logged_in=False; st.stop()
                        if (s1_note and not s2_note) or (not s1_note and s2_note): st.error("❌ أحد الطالبين مسجل مسبقاً"); st.session_state.logged_in=False; st.stop()
                        if s1_note and s2_note and s1_note != s2_note: st.error(f"❌ الطالبان مسجلان في مذكرتين مختلفتين"); st.session_state.logged_in=False; st.stop()
                        if s1_note and s2_note and s1_note == s2_note: st.session_state.mode = "view"; st.session_state.logged_in = True; st.rerun()
                    
                    if st.session_state.memo_type == "فردية":
                        fardiya_val = str(st.session_state.student1.get('فردية', '')).strip()
                        if fardiya_val not in ["1", "نعم"]: st.error("❌ لا يمكنك تسجيل مذكرة فردية"); st.stop()
                    
                    note_num = str(st.session_state.student1.get('رقم المذكرة', '')).strip()
                    st.session_state.mode = "view" if note_num else "register"
                    st.session_state.logged_in = True; st.rerun()
    
    else:
        s1 = st.session_state.student1; s2 = st.session_state.student2
        col1, col2 = st.columns([4, 1])
        with col2:
            if st.button("خروج", key="logout_btn"):
                logout()
        
        st.markdown(f'<div class="card"><h3>ملف الطالب</h3><p>الطالب الأول: <b style="color:#2F6F7E;">{s1["لقب"] if "لقب" in s1 else s1["اللقب"]} {s1["الإسم"] if "الإسم" in s1 else s1["إسم"]}</b></p><p>التخصص: <b>{s1["التخصص"]}</b></p></div>', unsafe_allow_html=True)
        if s2 is not None: st.markdown(f'<div class="card"><p>الطالب الثاني: <b style="color:#2F6F7E;">{s2["لقب"] if "لقب" in s2 else s2["اللقب"]} {s2["الإسم"] if "الإسم" in s2 else s2["إسم"]}</b></p></div>', unsafe_allow_html=True)

        # تبويبات الطالب (جديد)
        tab_memo, tab_notify = st.tabs(["مذكرتي", "الإشعارات والطلبات"])

        with tab_memo:
            if st.session_state.mode == "view":
                df_memos_fresh = load_memos()
                note_num = str(s1.get('رقم المذكرة', '')).strip()
                memo_info = df_memos_fresh[df_memos_fresh["رقم المذكرة"].astype(str).str.strip() == note_num]
                if not memo_info.empty:
                    memo_info = memo_info.iloc[0]
                    st.markdown(f'''<div class="card" style="border-left: 5px solid #FFD700;">
                        <h3>✅ أنت مسجل في المذكرة التالية:</h3>
                        <p><b>رقم المذكرة:</b> {memo_info['رقم المذكرة']}</p>
                        <p><b>العنوان:</b> {memo_info['عنوان المذكرة']}</p>
                        <p><b>المشرف:</b> {memo_info['الأستاذ']}</p>
                        <p><b>التخصص:</b> {memo_info['التخصص']}</p>
                        <p><b>التاريخ:</b> {memo_info.get('تاريخ التسجيل','')}</p>
                    </div>''', unsafe_allow_html=True)

            elif st.session_state.mode == "register":
                st.markdown('<div class="card"><h3>تسجيل مذكرة جديدة</h3></div>', unsafe_allow_html=True)
                all_profs = sorted(df_memos["الأستاذ"].dropna().unique())
                selected_prof = st.selectbox("اختر الأستاذ المشرف:", [""] + all_profs)
                
                if selected_prof:
                    student_specialty = s1["التخصص"]
                    prof_memos = df_memos[df_memos["الأستاذ"].astype(str).str.strip() == selected_prof.strip()]
                    reg_count = len(prof_memos[prof_memos["تم التسجيل"].astype(str).str.strip() == "نعم"])
                    
                    if reg_count >= 4:
                        st.error(f'❌ الأستاذ {selected_prof} استنفذ كل العناوين')
                    else:
                        avail_memos = df_memos[
                            (df_memos["الأستاذ"].astype(str).str.strip() == selected_prof.strip()) &
                            (df_memos["التخصص"].astype(str).str.strip() == student_specialty.strip()) &
                            (df_memos["تم التسجيل"].astype(str).str.strip() != "نعم")
                        ][["رقم المذكرة", "عنوان المذكرة"]]
                        
                        if not avail_memos.empty:
                            st.success(f'✅ المذكرات المتاحة في تخصصك ({student_specialty}):')
                            for _, row in avail_memos.iterrows():
                                st.markdown(f"**{row['رقم المذكرة']}.** {row['عنوان المذكرة']}")
                        else:
                            st.error('لا توجد مذكرات متاحة ❌')
                
                st.markdown("---")
                c1, c2 = st.columns(2)
                with c1: st.session_state.note_number = st.text_input("رقم المذكرة", value=st.session_state.note_number)
                with c2: st.session_state.prof_password = st.text_input("كلمة سر المشرف", type="password")

                if not st.session_state.show_confirmation:
                    if st.button("المتابعة للتأكيد"):
                        if not st.session_state.note_number or not st.session_state.prof_password: st.error("⚠️ يرجى إدخال البيانات")
                        else: st.session_state.show_confirmation = True; st.rerun()
                else:
                    st.warning(f"⚠️ تأكيد التسجيل - المذكرة رقم: {st.session_state.note_number}")
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("تأكيد نهائي", type="primary"):
                            valid, prof_row, err = verify_professor_password(st.session_state.note_number, st.session_state.prof_password, df_memos, df_prof_memos)
                            if not valid: st.error(err); st.session_state.show_confirmation = False
                            else:
                                with st.spinner('⏳ جاري تسجيل...'):
                                    success, msg = update_registration(st.session_state.note_number, s1, s2)
                                if success: st.success(msg); st.balloons(); clear_cache_and_reload(); st.session_state.mode = "view"; st.session_state.show_confirmation = False; time.sleep(2); st.rerun()
                                else: st.error(msg); st.session_state.show_confirmation = False
                    with col2:
                        if st.button("إلغاء"): st.session_state.show_confirmation = False; st.rerun()

        with tab_notify:
            st.subheader("تنبيهات خاصة بك")
            my_memo_id = str(s1.get('رقم المذكرة', '')).strip()
            if my_memo_id:
                my_reqs = df_requests[df_requests["رقم المذكرة"].astype(str).str.strip() == my_memo_id]
                if not my_reqs.empty:
                    for _, r in my_reqs.iterrows():
                        req_type = r['نوع الطلب']
                        details = str(r.get('العنوان الجديد', r.get('المبررات', ''))).strip()
                        
                        # القواعد: إخفاء المبررات في حذف طالب والتنازل
                        show_details = True
                        if req_type in ["حذف طالب", "تنازل"]:
                            show_details = False

                        st.markdown(f"""
                        <div class='card' style='border-right: 4px solid #F59E0B; padding: 20px;'>
                            <h4>{req_type}</h4>
                            <p>التاريخ: {r['الوقت']}</p>
                            <p>الحالة: <b>{r['الحالة']}</b></p>
                            {'<p>التفاصيل: ' + details + '</p>' if show_details else '<p><i>التفاصيل مخفية</i></p>'}
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("لا توجد إشعارات جديدة.")
            else:
                st.info("يجب تسجيل مذكرة أولاً لتلقي الإشعارات.")

# ============================================================
# فضاء الأساتذة (تم التعديل لإصلاح الخطأ وإضافة المميزات)
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
                else: st.session_state.professor = r; st.session_state.logged_in = True; st.rerun()
    else:
        prof = st.session_state.professor; prof_name = prof["الأستاذ"]
        col1, col2 = st.columns([4, 1])
        with col2:
            if st.button("خروج"):
                logout()
        
        st.markdown(f"<h2 style='margin-bottom:20px;'>فضاء الأستاذ <span style='color:#FFD700;'>{prof_name}</span></h2>", unsafe_allow_html=True)

        prof_memos = df_memos[df_memos["الأستاذ"].astype(str).str.strip() == prof_name.strip()]
        total = len(prof_memos)
        registered = len(prof_memos[prof_memos["تم التسجيل"].astype(str).str.strip() == "نعم"])
        available = total - registered
        is_exhausted = registered >= 4

        st.markdown('<div class="kpi-grid">', unsafe_allow_html=True)
        st.markdown(f'''
            <div class="kpi-card">
                <div class="kpi-value">{total}</div>
                <div class="kpi-label">إجمالي المذكرات</div>
            </div>
            <div class="kpi-card" style="border-color: #10B981;">
                <div class="kpi-value" style="color: #10B981;">{registered}</div>
                <div class="kpi-label">المذكرات المسجلة</div>
            </div>
            <div class="kpi-card" style="border-color: #F59E0B;">
                <div class="kpi-value" style="color: #F59E0B;">{available}</div>
                <div class="kpi-label">المذكرات المتاحة</div>
            </div>
        ''', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        if is_exhausted:
            st.markdown('<div class="alert-card">لقد استنفذت العناوين الأربعة المخصصة لك.</div>', unsafe_allow_html=True)
        
        # --- Tabs (تم التعديل لإضافة الإشعارات) ---
        tab1, tab2, tab3, tab4 = st.tabs(["المذكرات المسجلة", "كلمات السر", "الإشعارات", "المذكرات المتاحة/المقترحة"])
        
        with tab1:
            st.subheader("المذكرات المسجلة")
            registered_memos = prof_memos[prof_memos["تم التسجيل"].astype(str).str.strip() == "نعم"]
            
            if not registered_memos.empty:
                cols = st.columns(2)
                for i, (_, memo) in enumerate(registered_memos.iterrows()):
                    with cols[i % 2]:
                        mid = memo['رقم المذكرة']
                        title = memo['عنوان المذكرة']
                        progress_val = str(memo.get('نسبة التقدم', '0')).strip()
                        try: prog_int = int(progress_val) if progress_val else 0
                        except: prog_int = 0
                        
                        # عرض البطاقة
                        st.markdown(f'''
                        <div class="card" style="border-right: 5px solid #10B981;">
                            <h4>{mid} - {title}</h4>
                            <p style="color:#94A3B8; font-size:0.9em;">تخصص: {memo['التخصص']}</p>
                            <p style="font-size:0.8em; color:#2F6F7E;">انقر على الزر بالأسفل للتفاصيل</p>
                            <div class="progress-container">
                                <div class="progress-bar" style="width: {prog_int}%;"></div>
                            </div>
                            <p style="text-align:left; font-size:0.8em;">نسبة الإنجاز: {prog_int}%</p>
                        </div>
                        ''', unsafe_allow_html=True)
                        
                        # زر التفاعل (يفتح النافذة المنبثقة)
                        if st.button("⚙️ إدارة وتفاصيل", key=f"mgr_{mid}"):
                            st.session_state.selected_memo = mid
                            st.rerun()
            
            # النافذة المنبثقة (Modal)
            if st.session_state.selected_memo:
                sel_mid = st.session_state.selected_memo
                sel_memo = registered_memos[registered_memos["رقم المذكرة"] == sel_mid].iloc[0]
                
                st.markdown("---")
                st.markdown(f"<div class='card' style='border: 2px solid #2F6F7E;'><h2>🔧 إدارة المذكرة: {sel_mid}</h2></div>", unsafe_allow_html=True)
                
                # معلومات الطلاب والإيميلات
                s1_name = sel_memo['الطالب الأول']
                s2_name = sel_memo.get('الطالب الثاني', '')
                
                s1_email = get_student_email(sel_memo.get('رقم تسجيل الطالب 1', ''), s1_name, df_students)
                s2_email = get_student_email(sel_memo.get('رقم تسجيل الطالب 2', ''), s2_name, df_students) if s2_name else ""
                
                st.markdown(f"""
                <div style='background:#1E293B; padding:15px; border-radius:10px; margin-bottom:15px;'>
                    <h4>الطالب الأول: {s1_name}</h4>
                    {f"<p style='color:#10B981;'>📧 {s1_email}</p>" if s1_email else "<p style='color:#EF4444;'>لا يوجد إيميل</p>"}
                </div>
                """, unsafe_allow_html=True)
                
                if s2_name:
                    st.markdown(f"""
                    <div style='background:#1E293B; padding:15px; border-radius:10px; margin-bottom:15px;'>
                        <h4>الطالب الثاني: {s2_name}</h4>
                        {f"<p style='color:#10B981;'>📧 {s2_email}</p>" if s2_email else "<p style='color:#EF4444;'>لا يوجد إيميل</p>"}
                    </div>
                    """, unsafe_allow_html=True)

                # التقدم
                new_prog = st.selectbox("تحديث نسبة التقدم:", [
                    "0%", "10% - ضبط المقدمة", "30% - الفصل الأول", 
                    "60% - الفصل الثاني", "80% - الخاتمة", "100% - مكتملة"
                ], key=f"np_{sel_mid}")
                if st.button("حفظ التقدم", key=f"sv_{sel_mid}"):
                    mapping = {"0%":0, "10% - ضبط المقدمة":10, "30% - الفصل الأول":30, "60% - الفصل الثاني":60, "80% - الخاتمة":80, "100% - مكتملة":100}
                    s, m = update_progress(sel_mid, mapping[new_prog])
                    st.success(m) if s else st.error(m); time.sleep(1); st.rerun()
                
                st.markdown("---")
                st.markdown("### 📨 تقديم طلب جديد")
                
                req_op = st.selectbox("نوع الطلب:", ["", "تغيير عنوان المذكرة", "حذف طالب (ثنائية)", "إضافة طالب (فردية)", "تنازل عن الإشراف"], key=f"req_{sel_mid}")
                
                details_to_save = ""
                validation_error = None
                
                if req_op == "تغيير عنوان المذكرة":
                    new_title = st.text_input("العنوان الجديد:", key=f"nt_{sel_mid}")
                    if st.button("إرسال طلب تغيير العنوان", key=f"btn_ch_{sel_mid}"):
                        if new_title: details_to_save = f"العنوان الجديد المقترح: {new_title}"
                        else: validation_error = "الرجاء إدخال العنوان"
                            
                elif req_op == "حذف طالب (ثنائية)":
                    if not s2_name: st.warning("هذه مذكرة فردية!")
                    else:
                        st.write("الطالبان:")
                        st.write(f"1. {s1_name}")
                        st.write(f"2. {s2_name}")
                        to_del = st.selectbox("اختر الطالب للحذف:", ["", "الطالب الأول", "الطالب الثاني"], key=f"del_{sel_mid}")
                        just = st.text_area("تبريرات الحذف:", key=f"jus_del_{sel_mid}")
                        if st.button("إرسال طلب الحذف", key=f"btn_del_{sel_mid}"):
                            if to_del and just: details_to_save = f"حذف: {to_del}. السبب: {just}"
                            else: validation_error = "اكمل البيانات"
                            
                elif req_op == "إضافة طالب (فردية)":
                    if s2_name: st.warning("هذه مذكرة ثنائية بالفعل!")
                    else:
                        reg_to_add = st.text_input("رقم التسجيل:", key=f"add_{sel_mid}")
                        if st.button("تحقق وإرسال", key=f"btn_add_{sel_mid}"):
                            target = df_students[df_students["رقم التسجيل"] == reg_to_add]
                            if target.empty: validation_error = "رقم التسجيل غير موجود"
                            elif target.iloc[0].get("رقم المذكرة"): validation_error = "الطالب لديه مذكرة بالفعل"
                            elif target.iloc[0].get("التخصص") != sel_memo['التخصص']: validation_error = "التخصص غير متطابق"
                            else:
                                just = st.text_area("ملاحظات (اختياري):", key=f"jus_add_{sel_mid}")
                                details_to_save = f"إضافة الطالب المسجل: {reg_to_add}. ملاحظات: {just}"
                                
                elif req_op == "تنازل عن الإشراف":
                    just = st.text_area("مبررات التنازل:", key=f"res_{sel_mid}")
                    if st.button("إرسال طلب التنازل", key=f"btn_res_{sel_mid}"):
                        if just: details_to_save = f"التنازل عن الإشراف. المبررات: {just}"
                        else: validation_error = "الرجاء كتابة المبررات"

                if validation_error:
                    st.error(validation_error)
                elif details_to_save:
                    suc, msg = save_and_send_request(prof_name, sel_mid, sel_memo['عنوان المذكرة'], req_op, details_to_save)
                    if suc: st.success(msg); time.sleep(1); st.rerun()
                    else: st.error(msg)

                if st.button("❌ إغلاق"):
                    del st.session_state.selected_memo
                    st.rerun()

            else:
                st.info("لا توجد مذكرات مسجلة حتى الآن.")

        with tab2:
            st.subheader("كلمات السر")
            pwds = df_prof_memos[df_prof_memos["الأستاذ"].astype(str).str.strip() == prof_name.strip()]
            if not pwds.empty:
                for _, row in pwds.iterrows():
                    stat = str(row.get("تم التسجيل", "")).strip()
                    pwd = str(row.get("كلمة سر التسجيل", "")).strip()
                    if pwd:
                        color = "#10B981" if stat == "نعم" else "#F59E0B"
                        status_txt = "مستخدمة" if stat == "نعم" else "متاحة"
                        st.markdown(f'''
                        <div class="card" style="border-right: 5px solid {color}; display:flex; justify-content:space-between; align-items:center;">
                            <div>
                                <h3 style="margin:0; font-family:monospace; font-size:1.8rem; color:#FFD700;">{pwd}</h3>
                                <p style="margin:5px 0 0 0 0; color:#94A3B8;">الحالة: {status_txt}</p>
                            </div>
                        </div>
                        ''', unsafe_allow_html=True)
            else: st.info("لا توجد كلمات سر مسندة إليك.")
        
        with tab3: # إضافة تبويب الإشعارات للأستاذ
            st.subheader("إشعاراتي")
            my_reqs = df_requests[df_requests["الأستاذ"] == prof_name]
            if not my_reqs.empty:
                for _, r in my_reqs.iterrows():
                    status_color = "#10B981" if r['الحالة'] == "مقبول" else "#F59E0B"
                    st.markdown(f"""
                    <div class="card" style="border-right: 4px solid {status_color};">
                        <h4>{r['نوع الطلب']} - {r['رقم المذكرة']}</h4>
                        <p>التاريخ: {r['الوقت']}</p>
                        <p>الحالة: <b>{r['الحالة']}</b></p>
                    </div>
                    """, unsafe_allow_html=True)
            else: st.info("لا توجد إشعارات")

        with tab4:
            if is_exhausted: st.subheader("💡 المذكرات المقترحة")
            else: st.subheader("⏳ المذكرات المتاحة للتسجيل")
            
            avail = prof_memos[prof_memos["تم التسجيل"].astype(str).str.strip() != "نعم"]
            if not avail.empty:
                for _, m in avail.iterrows():
                    st.markdown(f'''
                    <div class="card" style="border-left: 4px solid #64748B;">
                        <h4>{m['رقم المذكرة']}</h4>
                        <p>{m['عنوان المذكرة']}</p>
                        <p style="color:#94A3B8;">تخصص: {m['التخصص']}</p>
                    </div>
                    ''', unsafe_allow_html=True)
            else: st.success("✅ جميع المذكرات مسجلة أو مقترحة!")

# ============================================================
# فضاء الإدارة
# ============================================================
elif st.session_state.user_type == "admin":
    if not st.session_state.logged_in:
        col1, col2 = st.columns([4, 1])
        with col2:
            if st.button("رجوع", key="back_admin"):
                st.session_state.user_type = None
                st.rerun()
        
        st.markdown("<h2>⚙️ فضاء الإدارة</h2>", unsafe_allow_html=True)
        
        with st.form("admin_login"):
            u = st.text_input("اسم المستخدم")
            p = st.text_input("كلمة المرور", type="password")
            if st.form_submit_button("دخول"):
                v, r = verify_admin(u, p)
                if not v: st.error(r)
                else: st.session_state.admin_user = r; st.session_state.logged_in = True; st.rerun()
    else:
        col1, col2 = st.columns([4, 1])
        with col2:
            if st.button("خروج"):
                logout()
        st.header("📊 لوحة تحكم الإدارة")
        
        st_s = len(df_students); t_m = len(df_memos); r_m = len(df_memos[df_memos["تم التسجيل"].astype(str).str.strip() == "نعم"])
        a_m = t_m - r_m; t_p = len(df_prof_memos["الأستاذ"].unique())
        reg_st = df_students["رقم المذكرة"].notna().sum()
        unreg_st = st_s - reg_st
        
        st.markdown('<div class="kpi-grid">', unsafe_allow_html=True)
        st.markdown(f'''
            <div class="kpi-card"><div class="kpi-value">{st_s}</div><div class="kpi-label">الطلاب</div></div>
            <div class="kpi-card"><div class="kpi-value">{t_p}</div><div class="kpi-label">الأساتذة</div></div>
            <div class="kpi-card"><div class="kpi-value">{t_m}</div><div class="kpi-label">إجمالي المذكرات</div></div>
            <div class="kpi-card" style="border-color: #10B981;"><div class="kpi-value" style="color: #10B981;">{r_m}</div><div class="kpi-label">مذكرات مسجلة</div></div>
            <div class="kpi-card" style="border-color: #F59E0B;"><div class="kpi-value" style="color: #F59E0B;">{a_m}</div><div class="kpi-label">مذكرات متاحة</div></div>
        ''', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        tab1, tab2, tab3, tab4, tab5 = st.tabs(["المذكرات", "الطلاب", "الأساتذة", "إدارة الطلبات", "الصيانة"])
        
        with tab1:
            st.subheader("جدول المذكرات")
            st.dataframe(df_memos, use_container_width=True, height=400)

        with tab2:
            st.subheader("قائمة الطلاب")
            st.dataframe(df_students, use_container_width=True, height=400)

        with tab3:
            st.subheader("توزيع الأساتذة")
            st.dataframe(df_memos.groupby("الأستاذ").size(), use_container_width=True)

        with tab4:
            st.subheader("سجل الطلبات الواردة")
            st.dataframe(df_requests, use_container_width=True, height=500)

        with tab5:
            st.subheader("الصيانة والربط")
            st.warning("⚠️ استخدم هذا الزر لربط أرقام التسجيل (أعمدة S و T) لأول مرة.")
            if st.button("🔄 بدء عملية الربط (Sync)", type="primary"):
                with st.spinner("جاري المعالجة..."):
                    s, m = sync_student_registration_numbers()
                    st.success(m) if s else st.info(m)
                    if s: clear_cache_and_reload(); st.rerun()

st.markdown("---")
st.markdown('<div style="text-align:center; color:#64748B; font-size:12px; padding:20px;">© 2026 جامعة محمد البشير الإبراهيمي - كلية الحقوق</div>', unsafe_allow_html=True)
