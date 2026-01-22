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
st.set_page_config(page_title="نظام تسجيل المذكرات", page_icon="🎓", layout="wide")

# ---------------- CSS محسّن ----------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
html, body, [class*="css"] { font-family: 'Cairo', sans-serif !important; }
.main { background-color: #0A1B2C; color: #ffffff; }
.block-container { padding: 2rem; background-color: #1A2A3D; border-radius: 12px; margin:auto;}
label, h1, h2, h3, h4, h5, h6, p, span, .stTextInput label { color:#ffffff !important; }
button { background-color:#256D85 !important; color:white !important; border:none !important; padding:10px 20px !important; border-radius:6px !important; }
button:hover { background-color:#2C89A0 !important; }
.success-msg { color: #FFFFFF; padding: 15px; margin: 10px 0; background-color: #2d5a2d; border-radius: 8px; }
.error-msg { color: #FFFFFF; padding: 15px; margin: 10px 0; background-color: #5a2d2d; border-radius: 8px; }
.info-msg { color: #FFFFFF; padding: 15px; margin: 10px 0; background-color: #2d4a5a; border-radius: 8px; }
.warning-msg { color: #FFFFFF; padding: 15px; margin: 10px 0; background-color: #5a4d2d; border-radius: 8px; }

/* بطاقة المذكرة */
.memo-card { 
    background: linear-gradient(135deg, #243447 0%, #1e3a52 100%); 
    padding: 20px; 
    border-radius: 10px; 
    margin: 15px 0; 
    border-left: 5px solid #256D85;
    box-shadow: 0 3px 8px rgba(0,0,0,0.2);
}

/* بطاقة تحذير الاستنفاذ */
.alert-card {
    background: linear-gradient(135deg, #8B4513 0%, #A0522D 100%);
    padding: 20px;
    border-radius: 10px;
    margin: 15px 0;
    border-left: 5px solid #FFD700;
    box-shadow: 0 3px 8px rgba(0,0,0,0.3);
    text-align: center;
    font-size: 18px;
    font-weight: bold;
}

/* شريط التقدم */
.progress-container {
    background-color: #1A2A3D;
    border-radius: 10px;
    padding: 3px;
    margin: 10px 0;
}
.progress-bar {
    height: 25px;
    border-radius: 8px;
    background: linear-gradient(90deg, #256D85 0%, #2C89A0 50%, #FFD700 100%);
    text-align: center;
    line-height: 25px;
    color: white;
    font-weight: bold;
    transition: width 0.3s ease;
}

/* تحسينات عامة */
.stApp {
    background-color: #0A1B2C;
}
.element-container {
    background-color: transparent !important;
}
.stSelectbox, .stTextInput, .stRadio {
    margin-bottom: 10px;
}
</style>
""", unsafe_allow_html=True)

# ---------------- Google Sheets ----------------
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
info = st.secrets["service_account"]
credentials = Credentials.from_service_account_info(info, scopes=SCOPES)
sheets_service = build('sheets', 'v4', credentials=credentials)

STUDENTS_SHEET_ID = "1gvNkOVVKo6AO07dRKMnSQw6vZ3KdUnW7I4HBk61Sqns"
MEMOS_SHEET_ID = "1LNJMBAye4QIQy7JHz6F8mQ6-XNC1weZx1ozDZFfjD5s"
PROF_MEMOS_SHEET_ID = "1OnZi1o-oPMUI_W_Ew-op0a1uOhSj006hw_2jrMD6FSE"

STUDENTS_RANGE = "Feuille 1!A1:L1000"
MEMOS_RANGE = "Feuille 1!A1:Q1000"
PROF_MEMOS_RANGE = "Feuille 1!A1:P1000"

ADMIN_CREDENTIALS = {
    "admin": "admin2026",
    "dsp": "dsp@2026"
}

EMAIL_SENDER = "domaine.dsp@univ-bba.dz"
EMAIL_PASSWORD = "oevruyiztgikwzah"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
ADMIN_EMAIL = "domaine.dsp@univ-bba.dz"

# ---------------- دوال مساعدة ----------------
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

def validate_username(username):
    username = sanitize_input(username)
    if not username:
        return False, "⚠️ اسم المستخدم فارغ"
    return True, username

def validate_note_number(note_number):
    note_number = sanitize_input(note_number)
    if not note_number:
        return False, "⚠️ رقم المذكرة فارغ"
    if len(note_number) > 20:
        return False, "⚠️ رقم المذكرة غير صالح"
    return True, note_number

# ---------------- تحميل البيانات ----------------
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

def clear_cache_and_reload():
    st.cache_data.clear()
    logger.info("تم مسح السجلات")

# ---------------- تحديث نسبة التقدم ----------------
def update_progress(memo_number, progress_value):
    """تحديث نسبة التقدم في عمود Q"""
    try:
        df_memos = load_memos()
        memo_row = df_memos[df_memos["رقم المذكرة"].astype(str).str.strip() == str(memo_number).strip()]
        
        if memo_row.empty:
            return False, "❌ لم يتم العثور على المذكرة"
        
        row_idx = memo_row.index[0] + 2
        
        sheets_service.spreadsheets().values().update(
            spreadsheetId=MEMOS_SHEET_ID,
            range=f"Feuille 1!Q{row_idx}",
            valueInputOption="USER_ENTERED",
            body={"values": [[str(progress_value)]]}
        ).execute()
        
        clear_cache_and_reload()
        logger.info(f"تم تحديث نسبة التقدم للمذكرة {memo_number} إلى {progress_value}%")
        return True, "✅ تم تحديث نسبة التقدم بنجاح"
        
    except Exception as e:
        logger.error(f"خطأ في تحديث نسبة التقدم: {str(e)}")
        return False, f"❌ خطأ: {str(e)}"

# ---------------- إرسال طلب للإدارة ----------------
def send_request_to_admin(prof_name, request_type, memo_number, details):
    """إرسال طلب الأستاذ للإدارة"""
    try:
        request_types = {
            "تغيير العنوان": "🔄 طلب تغيير عنوان مذكرة",
            "إضافة طالب": "➕ طلب إضافة طالب لمذكرة فردية"
        }
        
        subject = request_types.get(request_type, "📬 طلب جديد من أستاذ")
        
        email_body = f"""
<html dir="rtl">
<head>
    <style>
        body {{ font-family: 'Arial', sans-serif; background-color: #f4f4f4; padding: 20px; }}
        .container {{ background-color: #ffffff; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); max-width: 600px; margin: auto; }}
        .header {{ background-color: #8B4513; color: white; padding: 20px; border-radius: 8px; text-align: center; margin-bottom: 20px; }}
        .content {{ line-height: 1.8; color: #333; }}
        .info-box {{ background-color: #fff8dc; padding: 15px; border-right: 4px solid #8B4513; margin: 15px 0; }}
        .footer {{ text-align: center; color: #888; font-size: 12px; margin-top: 30px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>{subject}</h2>
        </div>
        <div class="content">
            <p><strong>من:</strong> الأستاذ(ة) {prof_name}</p>
            <p><strong>نوع الطلب:</strong> {request_type}</p>
            <p><strong>رقم المذكرة:</strong> {memo_number}</p>
            
            <div class="info-box">
                <h3>📋 تفاصيل الطلب:</h3>
                <p style="white-space: pre-line;">{details}</p>
            </div>
            
            <p><strong>⏰ تاريخ الطلب:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
        </div>
        <div class="footer">
            <p>© 2026 جامعة محمد البشير الإبراهيمي</p>
            <p>نظام إدارة المذكرات</p>
        </div>
    </div>
</body>
</html>
"""
        
        msg = MIMEMultipart('alternative')
        msg['From'] = EMAIL_SENDER
        msg['To'] = ADMIN_EMAIL
        msg['Subject'] = f"{subject} - {prof_name}"
        msg.attach(MIMEText(email_body, 'html', 'utf-8'))
        
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)
        
        logger.info(f"تم إرسال طلب {request_type} من {prof_name} للإدارة")
        return True, "✅ تم تسجيل طلبك بنجاح"
        
    except Exception as e:
        logger.error(f"خطأ في إرسال الطلب: {str(e)}")
        return False, "❌ خطأ في تسجيل الطلب"

# ---------------- إرسال البريد للأستاذ ----------------
def send_email_to_professor(prof_email, prof_name, memo_info, student1, student2=None):
    try:
        df_prof_memos = load_prof_memos()
        prof_memos = df_prof_memos[df_prof_memos["الأستاذ"].astype(str).str.strip() == prof_name.strip()]
        total_memos = len(prof_memos)
        registered_memos = len(prof_memos[prof_memos["تم التسجيل"].astype(str).str.strip() == "نعم"])
        
        student2_info = ""
        if student2 is not None:
            student2_info = f"<p>👤 <strong>الطالب الثاني:</strong> {student2['اللقب']} {student2['الإسم']}</p>"
        
        email_body = f"""
<html dir="rtl">
<head>
    <style>
        body {{ font-family: 'Arial', sans-serif; background-color: #f4f4f4; padding: 20px; }}
        .container {{ background-color: #ffffff; padding: 30px; border-radius: 10px; max-width: 600px; margin: auto; }}
        .header {{ background-color: #256D85; color: white; padding: 20px; border-radius: 8px; text-align: center; }}
        .content {{ line-height: 1.8; color: #333; }}
        .info-box {{ background-color: #f8f9fa; padding: 15px; border-right: 4px solid #256D85; margin: 15px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>✅ تسجيل مذكرة جديدة</h2>
        </div>
        <div class="content">
            <p>الأستاذ(ة) الفاضل(ة) <strong>{prof_name}</strong>،</p>
            <div class="info-box">
                <p>📄 <strong>رقم المذكرة:</strong> {memo_info['رقم المذكرة']}</p>
                <p>📑 <strong>عنوان المذكرة:</strong> {memo_info['عنوان المذكرة']}</p>
                <p>👤 <strong>الطالب الأول:</strong> {student1['اللقب']} {student1['الإسم']}</p>
                {student2_info}
            </div>
            <p>📊 <strong>إحصائياتك:</strong> {registered_memos} من {total_memos} مذكرات مسجلة</p>
        </div>
    </div>
</body>
</html>
"""
        
        msg = MIMEMultipart('alternative')
        msg['From'] = EMAIL_SENDER
        msg['To'] = prof_email
        msg['Subject'] = f"✅ تسجيل مذكرة - {memo_info['رقم المذكرة']}"
        msg.attach(MIMEText(email_body, 'html', 'utf-8'))
        
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)
        
        return True, "تم إرسال البريد"
    except Exception as e:
        logger.error(f"خطأ في البريد: {str(e)}")
        return False, str(e)

# ---------------- التحقق ----------------
def verify_student(username, password, df_students):
    valid, result = validate_username(username)
    if not valid:
        return False, result
    username = result
    password = sanitize_input(password)
    if df_students.empty:
        return False, "❌ خطأ في تحميل بيانات الطلاب"
    student = df_students[df_students["اسم المستخدم"].astype(str).str.strip() == username]
    if student.empty:
        return False, "❌ اسم المستخدم غير موجود"
    if student.iloc[0]["كلمة السر"].strip() != password:
        return False, "❌ كلمة السر غير صحيحة"
    return True, student.iloc[0]

def verify_students_batch(students_data, df_students):
    verified_students = []
    for username, password in students_data:
        if not username:
            continue
        valid, student = verify_student(username, password, df_students)
        if not valid:
            return False, student
        verified_students.append(student)
    return True, verified_students

def verify_professor(username, password, df_prof_memos):
    username = sanitize_input(username)
    password = sanitize_input(password)
    if df_prof_memos.empty:
        return False, "❌ خطأ في تحميل بيانات الأساتذة"
    
    required_cols = ["إسم المستخدم", "كلمة المرور"]
    missing_cols = [col for col in required_cols if col not in df_prof_memos.columns]
    if missing_cols:
        return False, f"❌ الأعمدة التالية غير موجودة: {', '.join(missing_cols)}"
    
    prof = df_prof_memos[
        (df_prof_memos["إسم المستخدم"].astype(str).str.strip() == username) &
        (df_prof_memos["كلمة المرور"].astype(str).str.strip() == password)
    ]
    if prof.empty:
        return False, "❌ اسم المستخدم أو كلمة السر غير صحيحة"
    return True, prof.iloc[0]

def verify_admin(username, password):
    username = sanitize_input(username)
    password = sanitize_input(password)
    if username in ADMIN_CREDENTIALS and ADMIN_CREDENTIALS[username] == password:
        return True, username
    return False, "❌ بيانات الإدارة غير صحيحة"

def verify_professor_password(note_number, prof_password, df_memos, df_prof_memos):
    valid, result = validate_note_number(note_number)
    if not valid:
        return False, None, result
    note_number = result
    prof_password = sanitize_input(prof_password)
    if df_memos.empty or df_prof_memos.empty:
        return False, None, "❌ خطأ في تحميل البيانات"
    memo_row = df_memos[df_memos["رقم المذكرة"].astype(str).str.strip() == note_number]
    if memo_row.empty:
        return False, None, "❌ رقم المذكرة غير موجود"
    memo_row = memo_row.iloc[0]
    if str(memo_row.get("تم التسجيل", "")).strip() == "نعم":
        return False, None, "❌ هذه المذكرة مسجلة مسبقاً"
    prof_row = df_prof_memos[
        (df_prof_memos["الأستاذ"].astype(str).str.strip() == memo_row["الأستاذ"].strip()) &
        (df_prof_memos["كلمة سر التسجيل"].astype(str).str.strip() == prof_password)
    ]
    if prof_row.empty:
        return False, None, "❌ كلمة سر المشرف غير صحيحة"
    if str(prof_row.iloc[0].get("تم التسجيل", "")).strip() == "نعم":
        return False, None, "❌ هذه كلمة السر تم استعمالها مسبقًا"
    return True, prof_row.iloc[0], None

# ---------------- تحديث المذكرات ----------------
def update_registration(note_number, student1, student2=None):
    try:
        df_memos = load_memos()
        df_prof_memos = load_prof_memos()
        df_students = load_students()

        prof_name = df_memos[df_memos["رقم المذكرة"].astype(str).str.strip() == str(note_number).strip()]["الأستاذ"].iloc[0].strip()
        used_prof_password = st.session_state.prof_password.strip()
        
        prof_row_idx = df_prof_memos[
            (df_prof_memos["الأستاذ"].astype(str).str.strip() == prof_name) &
            (df_prof_memos["كلمة سر التسجيل"].astype(str).str.strip() == used_prof_password)
        ].index[0] + 2

        col_names = df_prof_memos.columns.tolist()
        
        updates = [
            {"range": f"Feuille 1!{col_letter(col_names.index('الطالب الأول')+1)}{prof_row_idx}",
             "values": [[student1['اللقب'] + ' ' + student1['الإسم']]]},
            {"range": f"Feuille 1!{col_letter(col_names.index('تم التسجيل')+1)}{prof_row_idx}",
             "values": [["نعم"]]},
            {"range": f"Feuille 1!{col_letter(col_names.index('تاريخ التسجيل')+1)}{prof_row_idx}",
             "values": [[datetime.now().strftime('%Y-%m-%d %H:%M')]]},
            {"range": f"Feuille 1!{col_letter(col_names.index('رقم المذكرة')+1)}{prof_row_idx}",
             "values": [[note_number]]}
        ]
        
        if student2 is not None:
            updates.append({
                "range": f"Feuille 1!{col_letter(col_names.index('الطالب الثاني')+1)}{prof_row_idx}",
                "values": [[student2['اللقب'] + ' ' + student2['الإسم']]]
            })
        
        sheets_service.spreadsheets().values().batchUpdate(
            spreadsheetId=PROF_MEMOS_SHEET_ID,
            body={"valueInputOption": "USER_ENTERED", "data": updates}
        ).execute()

        memo_row_idx = df_memos[df_memos["رقم المذكرة"].astype(str).str.strip() == str(note_number).strip()].index[0] + 2
        memo_cols = df_memos.columns.tolist()
        
        updates2 = [
            {"range": f"Feuille 1!{col_letter(memo_cols.index('الطالب الأول')+1)}{memo_row_idx}",
             "values": [[student1['اللقب'] + ' ' + student1['الإسم']]]},
            {"range": f"Feuille 1!{col_letter(memo_cols.index('تم التسجيل')+1)}{memo_row_idx}",
             "values": [["نعم"]]},
            {"range": f"Feuille 1!{col_letter(memo_cols.index('تاريخ التسجيل')+1)}{memo_row_idx}",
             "values": [[datetime.now().strftime('%Y-%m-%d %H:%M')]]}
        ]
        
        if 'كلمة سر التسجيل' in memo_cols:
            updates2.append({
                "range": f"Feuille 1!{col_letter(memo_cols.index('كلمة سر التسجيل')+1)}{memo_row_idx}",
                "values": [[used_prof_password]]
            })
        
        if student2 is not None:
            updates2.append({
                "range": f"Feuille 1!{col_letter(memo_cols.index('الطالب الثاني')+1)}{memo_row_idx}",
                "values": [[student2['اللقب'] + ' ' + student2['الإسم']]]
            })
        
        sheets_service.spreadsheets().values().batchUpdate(
            spreadsheetId=MEMOS_SHEET_ID,
            body={"valueInputOption": "USER_ENTERED", "data": updates2}
        ).execute()

        students_cols = df_students.columns.tolist()
        student1_row_idx = df_students[df_students["اسم المستخدم"].astype(str).str.strip() == student1['اسم المستخدم'].strip()].index[0] + 2
        
        sheets_service.spreadsheets().values().update(
            spreadsheetId=STUDENTS_SHEET_ID,
            range=f"Feuille 1!{col_letter(students_cols.index('رقم المذكرة')+1)}{student1_row_idx}",
            valueInputOption="USER_ENTERED",
            body={"values": [[note_number]]}
        ).execute()

        if student2 is not None:
            student2_row_idx = df_students[df_students["اسم المستخدم"].astype(str).str.strip() == student2['اسم المستخدم'].strip()].index[0] + 2
            sheets_service.spreadsheets().values().update(
                spreadsheetId=STUDENTS_SHEET_ID,
                range=f"Feuille 1!{col_letter(students_cols.index('رقم المذكرة')+1)}{student2_row_idx}",
                valueInputOption="USER_ENTERED",
                body={"values": [[note_number]]}
            ).execute()

        time.sleep(2)
        clear_cache_and_reload()
        time.sleep(1)
        
        df_students_updated = load_students()
        st.session_state.student1 = df_students_updated[
            df_students_updated["اسم المستخدم"].astype(str).str.strip() == student1['اسم المستخدم'].strip()
        ].iloc[0]
        
        if student2 is not None:
            st.session_state.student2 = df_students_updated[
                df_students_updated["اسم المستخدم"].astype(str).str.strip() == student2['اسم المستخدم'].strip()
            ].iloc[0]
        
        memo_data = df_memos[df_memos["رقم المذكرة"].astype(str).str.strip() == str(note_number).strip()].iloc[0]
        prof_name = memo_data["الأستاذ"].strip()
        
        prof_memo_data = df_prof_memos[
            (df_prof_memos["الأستاذ"].astype(str).str.strip() == prof_name)
        ].iloc[0]
        
        prof_email = str(prof_memo_data.get("الإيميل", "")).strip()
        
        if prof_email and "@" in prof_email:
            send_email_to_professor(prof_email, prof_name, memo_data, student1, student2)
        
        return True, "✅ تم تسجيل المذكرة بنجاح!"
        
    except Exception as e:
        logger.error(f"خطأ في تحديث التسجيل: {str(e)}")
        return False, f"❌ حدث خطأ أثناء التسجيل: {str(e)}"

# ---------------- Session State ----------------
if 'user_type' not in st.session_state:
    st.session_state.user_type = None

if 'logged_in' not in st.session_state:
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

def logout():
    st.session_state.logged_in = False
    st.session_state.user_type = None
    st.session_state.student1 = None
    st.session_state.student2 = None
    st.session_state.professor = None
    st.session_state.admin_user = None
    st.session_state.mode = "register"
    st.session_state.note_number = ""
    st.session_state.prof_password = ""
    st.session_state.show_confirmation = False
    st.rerun()

# تحميل البيانات
df_students = load_students()
df_memos = load_memos()
df_prof_memos = load_prof_memos()

if df_students.empty or df_memos.empty or df_prof_memos.empty:
    st.error("❌ خطأ في تحميل البيانات. يرجى المحاولة لاحقاً.")
    st.stop()

# ---------------- اختيار نوع المستخدم ----------------
if st.session_state.user_type is None:
    col_img, col_title = st.columns([1, 3])
    with col_img:
        st.image("https://raw.githubusercontent.com/SAMIR-MALEK/memoire-depot-2026/main/LOGO2.png", width=120)
    with col_title:
        st.title("🎓 نظام تسجيل المذكرات")
        st.markdown("##### جامعة محمد البشير الإبراهيمي - كلية الحقوق والعلوم السياسية")
    
    st.markdown("---")
    
    st.subheader("اختر نوع الدخول:")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("👨‍🎓 فضاء الطلبة", key="student_btn", use_container_width=True):
            st.session_state.user_type = "student"
            st.rerun()
    
    with col2:
        if st.button("👨‍🏫 فضاء الأساتذة", key="prof_btn", use_container_width=True):
            st.session_state.user_type = "professor"
            st.rerun()
    
    with col3:
        if st.button("🔐 فضاء الإدارة", key="admin_btn", use_container_width=True):
            st.session_state.user_type = "admin"
            st.rerun()

# ============================================================
# فضاء الطلبة
# ============================================================
elif st.session_state.user_type == "student":
    if not st.session_state.logged_in:
        col1, col2 = st.columns([4, 1])
        with col2:
            if st.button("🔙 رجوع", key="back_student"):
                st.session_state.user_type = None
                st.rerun()
        
        st.subheader("👨‍🎓 فضاء الطلبة")
        
        st.session_state.memo_type = st.radio("اختر نوع المذكرة:", ["فردية", "ثنائية"])
        username1 = st.text_input("اسم المستخدم الطالب الأول", max_chars=50)
        password1 = st.text_input("كلمة السر الطالب الأول", type="password", max_chars=50)
        username2 = password2 = None
        
        if st.session_state.memo_type == "ثنائية":
            username2 = st.text_input("اسم المستخدم الطالب الثاني", max_chars=50)
            password2 = st.text_input("كلمة السر الطالب الثاني", type="password", max_chars=50)

        if st.button("تسجيل الدخول"):
            if st.session_state.memo_type == "ثنائية":
                if not username2 or not password2:
                    st.error("⚠️ يرجى إدخال بيانات الطالب الثاني كاملة")
                    st.stop()
                
                if username1.strip().lower() == username2.strip().lower():
                    st.error("❌ لا يمكن أن يكون الطالب الأول والثاني نفس الشخص!")
                    st.stop()
            
            students_data = [(username1, password1)]
            if st.session_state.memo_type == "ثنائية" and username2:
                students_data.append((username2, password2))
            
            valid, result = verify_students_batch(students_data, df_students)
            
            if not valid:
                st.error(result)
            else:
                verified_students = result
                st.session_state.student1 = verified_students[0]
                st.session_state.student2 = verified_students[1] if len(verified_students) > 1 else None
                
                if st.session_state.memo_type == "ثنائية" and st.session_state.student2 is not None:
                    s1_note = str(st.session_state.student1.get('رقم المذكرة', '')).strip()
                    s2_note = str(st.session_state.student2.get('رقم المذكرة', '')).strip()
                    s1_specialty = str(st.session_state.student1.get('التخصص', '')).strip()
                    s2_specialty = str(st.session_state.student2.get('التخصص', '')).strip()
                    
                    if s1_specialty != s2_specialty:
                        st.error("❌ لا يمكن التسجيل الثنائي. الطالبان في تخصصين مختلفين")
                        st.session_state.logged_in = False
                        st.session_state.student1 = None
                        st.session_state.student2 = None
                        st.stop()
                    
                    if (s1_note and not s2_note) or (not s1_note and s2_note):
                        st.error("❌ أحد الطالبين مسجل مسبقاً")
                        st.session_state.logged_in = False
                        st.session_state.student1 = None
                        st.session_state.student2 = None
                        st.stop()
                    
                    if s1_note and s2_note and s1_note != s2_note:
                        st.error(f"❌ الطالبان مسجلان في مذكرتين مختلفتين")
                        st.session_state.logged_in = False
                        st.session_state.student1 = None
                        st.session_state.student2 = None
                        st.stop()
                    
                    if s1_note and s2_note and s1_note == s2_note:
                        st.session_state.mode = "view"
                        st.session_state.logged_in = True
                        st.rerun()
                
                if st.session_state.memo_type == "فردية":
                    fardiya_value = str(st.session_state.student1.get('فردية', '')).strip()
                    if fardiya_value not in ["1", "نعم"]:
                        st.error("❌ لا يمكنك تسجيل مذكرة فردية")
                        st.stop()
                
                note_number = str(st.session_state.student1.get('رقم المذكرة', '')).strip()
                
                if note_number:
                    st.session_state.mode = "view"
                else:
                    st.session_state.mode = "register"
                
                st.session_state.logged_in = True
                st.rerun()
    
    else:
        s1 = st.session_state.student1
        s2 = st.session_state.student2
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.header("📘 فضاء الطالب")
        with col2:
            if st.button("🚪 خروج", key="logout_btn"):
                logout()
        
        st.markdown(f"👤 الطالب الأول: **{s1['اللقب']} {s1['الإسم']}**")
        st.markdown(f"🎓 التخصص: **{s1['التخصص']}**")
        
        if s2 is not None:
            st.markdown(f"👤 الطالب الثاني: **{s2['اللقب']} {s2['الإسم']}**")

        if st.session_state.mode == "view":
            time.sleep(0.5)
            df_memos_fresh = load_memos()
            note_number = str(s1.get('رقم المذكرة', '')).strip()
            memo_info = df_memos_fresh[df_memos_fresh["رقم المذكرة"].astype(str).str.strip() == note_number]
            
            if not memo_info.empty:
                memo_info = memo_info.iloc[0]
                st.markdown('<div class="success-msg">', unsafe_allow_html=True)
                st.markdown(f"### ✅ أنت مسجل في المذكرة التالية:")
                st.markdown(f"**📄 رقم المذكرة:** {memo_info['رقم المذكرة']}")
                st.markdown(f"**📑 عنوان المذكرة:** {memo_info['عنوان المذكرة']}")
                st.markdown(f"**👨‍🏫 الأستاذ المشرف:** {memo_info['الأستاذ']}")
                st.markdown(f"**🎯 التخصص:** {memo_info['التخصص']}")
                st.markdown(f"**🕒 تاريخ التسجيل:** {memo_info.get('تاريخ التسجيل','')}")
                st.markdown('</div>', unsafe_allow_html=True)

        elif st.session_state.mode == "register":
            st.subheader("📝 تسجيل مذكرة جديدة")
            
            all_profs = sorted(df_memos["الأستاذ"].dropna().unique())
            selected_prof = st.selectbox("🧑‍🏫 اختر الأستاذ المشرف:", [""] + all_profs)
            
            if selected_prof:
                student_specialty = s1["التخصص"]
                prof_all_memos = df_memos[df_memos["الأستاذ"].astype(str).str.strip() == selected_prof.strip()]
                prof_registered_memos = prof_all_memos[prof_all_memos["تم التسجيل"].astype(str).str.strip() == "نعم"]
                total_registered = len(prof_registered_memos)
                
                if total_registered >= 4:
                    st.error(f'❌ الأستاذ {selected_prof} استنفذ كل العناوين')
                else:
                    available_memos_df = df_memos[
                        (df_memos["الأستاذ"].astype(str).str.strip() == selected_prof.strip()) &
                        (df_memos["التخصص"].astype(str).str.strip() == student_specialty.strip()) &
                        (df_memos["تم التسجيل"].astype(str).str.strip() != "نعم")
                    ][["رقم المذكرة", "عنوان المذكرة"]]
                    
                    if not available_memos_df.empty:
                        st.success(f'✅ المذكرات المتاحة في تخصصك ({student_specialty}):')
                        for idx, row in available_memos_df.iterrows():
                            st.markdown(f"**{row['رقم المذكرة']}.** {row['عنوان المذكرة']}")
                    else:
                        st.error('لا توجد مذكرات متاحة ❌')
            
            st.markdown("---")
            col1, col2 = st.columns(2)
            with col1:
                st.session_state.note_number = st.text_input("📄 رقم المذكرة", value=st.session_state.note_number, max_chars=20)
            with col2:
                st.session_state.prof_password = st.text_input("🔑 كلمة سر المشرف", type="password", max_chars=50)

            if not st.session_state.show_confirmation:
                if st.button("📝 المتابعة للتأكيد", type="primary", use_container_width=True):
                    if not st.session_state.note_number or not st.session_state.prof_password:
                        st.error("⚠️ يرجى إدخال رقم المذكرة وكلمة سر المشرف")
                    else:
                        st.session_state.show_confirmation = True
                        st.rerun()
            else:
                st.warning(f"⚠️ تأكيد التسجيل - المذكرة رقم: {st.session_state.note_number}")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ تأكيد نهائي", type="primary", use_container_width=True):
                        valid_memo, prof_row, error_msg = verify_professor_password(
                            st.session_state.note_number, 
                            st.session_state.prof_password, 
                            df_memos, 
                            df_prof_memos
                        )
                        
                        if not valid_memo:
                            st.error(error_msg)
                            st.session_state.show_confirmation = False
                        else:
                            with st.spinner('⏳ جاري تسجيل المذكرة...'):
                                success, message = update_registration(st.session_state.note_number, s1, s2)
                            
                            if success:
                                st.success(message)
                                st.balloons()
                                clear_cache_and_reload()
                                st.session_state.mode = "view"
                                st.session_state.show_confirmation = False
                                time.sleep(2)
                                st.rerun()
                            else:
                                st.error(message)
                                st.session_state.show_confirmation = False
                
                with col2:
                    if st.button("❌ إلغاء", use_container_width=True):
                        st.session_state.show_confirmation = False
                        st.rerun()

# ============================================================
# فضاء الأساتذة
# ============================================================
elif st.session_state.user_type == "professor":
    if not st.session_state.logged_in:
        col1, col2 = st.columns([4, 1])
        with col2:
            if st.button("🔙 رجوع", key="back_prof"):
                st.session_state.user_type = None
                st.rerun()
        
        st.subheader("👨‍🏫 فضاء الأساتذة")
        
        username = st.text_input("اسم المستخدم", max_chars=50)
        password = st.text_input("كلمة المرور", type="password", max_chars=50)
        
        if st.button("تسجيل الدخول"):
            valid, result = verify_professor(username, password, df_prof_memos)
            if not valid:
                st.error(result)
            else:
                st.session_state.professor = result
                st.session_state.logged_in = True
                st.rerun()
    
    else:
        prof = st.session_state.professor
        prof_name = prof["الأستاذ"]
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.header(f"👨‍🏫 فضاء الأستاذ(ة) {prof_name}")
        with col2:
            if st.button("🚪 خروج", key="logout_prof"):
                logout()
        
        # إحصائيات الأستاذ
        prof_memos = df_memos[df_memos["الأستاذ"].astype(str).str.strip() == prof_name.strip()]
        total_memos = len(prof_memos)
        registered_memos = len(prof_memos[prof_memos["تم التسجيل"].astype(str).str.strip() == "نعم"])
        available_memos = total_memos - registered_memos
        
        # تحقق من الاستنفاذ
        is_exhausted = registered_memos >= 4
        
        st.subheader("📊 لوحة التحكم")
        
        # إحصائيات بدون مستطيلات زرقاء
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"### {total_memos}")
            st.markdown("**إجمالي المذكرات**")
        
        with col2:
            st.markdown(f"### {registered_memos}")
            st.markdown("**المذكرات المسجلة**")
        
        with col3:
            st.markdown(f"### {available_memos}")
            if is_exhausted:
                st.markdown("**مذكرات مقترحة**")
            else:
                st.markdown("**المذكرات المتاحة**")
        
        # تحذير الاستنفاذ
        if is_exhausted:
            st.markdown('<div class="alert-card">⚠️ لقد استنفذت العناوين الأربعة المخصصة لك. المذكرات المتبقية تعتبر مقترحة ولا يمكن تسجيلها حالياً.</div>', unsafe_allow_html=True)
        
        st.markdown("---")
        
        # التبويبات: المذكرات المسجلة → كلمات السر → المذكرات المتاحة/المقترحة
        tab1, tab2, tab3 = st.tabs(["📝 المذكرات المسجلة", "🔑 كلمات السر", "⏳ المذكرات المتاحة/المقترحة"])
        
        # Tab 1: المذكرات المسجلة
        with tab1:
            st.subheader("✅ المذكرات المسجلة")
            registered = prof_memos[prof_memos["تم التسجيل"].astype(str).str.strip() == "نعم"]
            
            if not registered.empty:
                # إنشاء قائمة اختيار للمذكرات
                memo_options = [f"{row['رقم المذكرة']} - {row['عنوان المذكرة']}" for _, row in registered.iterrows()]
                selected_memo_option = st.selectbox("📝 اختر مذكرة لعرض التفاصيل:", memo_options, key="select_registered_memo")
                
                # الحصول على رقم المذكرة المختارة
                selected_memo_num = selected_memo_option.split(" - ")[0]
                memo = registered[registered["رقم المذكرة"].astype(str).str.strip() == selected_memo_num].iloc[0]
                
                st.markdown('<div class="memo-card">', unsafe_allow_html=True)
                st.markdown(f"**📄 رقم المذكرة:** {memo['رقم المذكرة']}")
                st.markdown(f"**📑 العنوان:** {memo['عنوان المذكرة']}")
                st.markdown(f"**🎓 التخصص:** {memo['التخصص']}")
                
                # معلومات الطلاب
                student1_name = memo.get('الطالب الأول', 'غير محدد')
                st.markdown(f"**👤 الطالب الأول:** {student1_name}")
                
                # البحث عن بريد الطالب الأول
                if student1_name != 'غير محدد':
                    student1_parts = student1_name.split()
                    if len(student1_parts) >= 2:
                        student1_data = df_students[
                            (df_students["اللقب"].astype(str).str.strip() == student1_parts[0].strip()) &
                            (df_students["الإسم"].astype(str).str.strip() == student1_parts[1].strip())
                        ]
                        if not student1_data.empty:
                            student1_email = str(student1_data.iloc[0].get("البريد الإلكتروني", "")).strip()
                            if student1_email:
                                st.markdown(f"**📧 البريد:** {student1_email}")
                
                # الطالب الثاني
                if str(memo.get('الطالب الثاني', '')).strip():
                    student2_name = memo['الطالب الثاني']
                    st.markdown(f"**👤 الطالب الثاني:** {student2_name}")
                    
                    # البحث عن بريد الطالب الثاني
                    student2_parts = student2_name.split()
                    if len(student2_parts) >= 2:
                        student2_data = df_students[
                            (df_students["اللقب"].astype(str).str.strip() == student2_parts[0].strip()) &
                            (df_students["الإسم"].astype(str).str.strip() == student2_parts[1].strip())
                        ]
                        if not student2_data.empty:
                            student2_email = str(student2_data.iloc[0].get("البريد الإلكتروني", "")).strip()
                            if student2_email:
                                st.markdown(f"**📧 البريد:** {student2_email}")
                
                st.markdown(f"**🕒 تاريخ التسجيل:** {memo.get('تاريخ التسجيل', 'غير محدد')}")
                
                # نسبة التقدم
                progress_value = str(memo.get('نسبة التقدم', '0')).strip()
                try:
                    progress_int = int(progress_value) if progress_value else 0
                except:
                    progress_int = 0
                
                st.markdown(f"**📊 نسبة التقدم الحالية:** {progress_int}%")
                st.markdown(f'<div class="progress-container"><div class="progress-bar" style="width: {progress_int}%;">{progress_int}%</div></div>', unsafe_allow_html=True)
                
                # تحديث نسبة التقدم
                st.markdown("**🔄 تحديث نسبة التقدم:**")
                
                progress_stages = {
                    "0%": 0,
                    "10% - ضبط المقدمة والإشكالية": 10,
                    "30% - المبحث الأول من الفصل الأول": 30,
                    "40% - المبحث الثاني من الفصل الأول": 40,
                    "60% - المبحث الأول من الفصل الثاني": 60,
                    "80% - المبحث الثاني من الفصل الثاني": 80,
                    "100% - الخاتمة والمذكرة مكتملة": 100
                }
                
                new_progress = st.selectbox(
                    "اختر المرحلة الحالية:",
                    options=list(progress_stages.keys()),
                    key=f"progress_{memo['رقم المذكرة']}"
                )
                
                if st.button(f"💾 حفظ التقدم", key=f"save_progress_{memo['رقم المذكرة']}"):
                    progress_val = progress_stages[new_progress]
                    success, msg = update_progress(memo['رقم المذكرة'], progress_val)
                    if success:
                        st.success(msg)
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(msg)
                
                st.markdown('</div>', unsafe_allow_html=True)
                
                st.markdown("---")
                
                # قسم الطلبات المتعلقة بهذه المذكرة
                st.subheader("📬 طلبات متعلقة بهذه المذكرة")
                
                request_type = st.selectbox(
                    "نوع الطلب:",
                    ["تغيير العنوان", "إضافة طالب"],
                    key=f"request_type_{memo['رقم المذكرة']}"
                )
                
                if request_type == "تغيير العنوان":
                    new_title = st.text_input(
                        "العنوان الجديد للمذكرة:",
                        placeholder="اكتب العنوان الجديد هنا...",
                        key=f"new_title_{memo['رقم المذكرة']}"
                    )
                    details = f"العنوان الجديد المقترح:\n{new_title}"
                    
                elif request_type == "إضافة طالب":
                    col1, col2 = st.columns(2)
                    with col1:
                        new_student_lastname = st.text_input(
                            "لقب الطالب الجديد:",
                            placeholder="اللقب",
                            key=f"new_student_ln_{memo['رقم المذكرة']}"
                        )
                    with col2:
                        new_student_firstname = st.text_input(
                            "اسم الطالب الجديد:",
                            placeholder="الاسم",
                            key=f"new_student_fn_{memo['رقم المذكرة']}"
                        )
                    details = f"الطالب المطلوب إضافته:\nاللقب: {new_student_lastname}\nالاسم: {new_student_firstname}"
                
                if st.button("📤 تسجيل الطلب", type="primary", key=f"submit_request_{memo['رقم المذكرة']}"):
                    if request_type == "تغيير العنوان" and new_title.strip():
                        success, msg = send_request_to_admin(prof_name, request_type, memo['رقم المذكرة'], details)
                        if success:
                            st.success(msg)
                            st.balloons()
                        else:
                            st.error(msg)
                    elif request_type == "إضافة طالب" and new_student_lastname.strip() and new_student_firstname.strip():
                        success, msg = send_request_to_admin(prof_name, request_type, memo['رقم المذكرة'], details)
                        if success:
                            st.success(msg)
                            st.balloons()
                        else:
                            st.error(msg)
                    else:
                        st.error("⚠️ يرجى ملء جميع الحقول المطلوبة")
            else:
                st.info("لا توجد مذكرات مسجلة بعد")
        
        # Tab 2: كلمات السر
        with tab2:
            st.subheader("🔑 كلمات السر الخاصة بك")
            prof_passwords = df_prof_memos[df_prof_memos["الأستاذ"].astype(str).str.strip() == prof_name.strip()]
            
            if not prof_passwords.empty:
                for idx, row in prof_passwords.iterrows():
                    password = str(row.get("كلمة سر التسجيل", "")).strip()
                    status = str(row.get("تم التسجيل", "")).strip()
                    memo_num = str(row.get("رقم المذكرة", "")).strip()
                    
                    if password:
                        st.markdown('<div class="memo-card">', unsafe_allow_html=True)
                        if status == "نعم":
                            st.markdown(f"**🔑 كلمة السر:** `{password}` ✅ **مستخدمة**")
                            if memo_num:
                                st.markdown(f"**📄 المذكرة:** {memo_num}")
                        else:
                            st.markdown(f"**🔑 كلمة السر:** `{password}` ⏳ **متاحة**")
                        st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.info("لا توجد كلمات سر مسجلة")
        
        # Tab 3: المذكرات المتاحة/المقترحة
        with tab3:
            if is_exhausted:
                st.subheader("💡 المذكرات المقترحة (استنفذت العناوين)")
            else:
                st.subheader("⏳ المذكرات المتاحة للتسجيل")
            
            available = prof_memos[prof_memos["تم التسجيل"].astype(str).str.strip() != "نعم"]
            
            if not available.empty:
                for idx, memo in available.iterrows():
                    st.markdown('<div class="memo-card">', unsafe_allow_html=True)
                    st.markdown(f"**📄 رقم المذكرة:** {memo['رقم المذكرة']}")
                    st.markdown(f"**📑 العنوان:** {memo['عنوان المذكرة']}")
                    st.markdown(f"**🎓 التخصص:** {memo['التخصص']}")
                    if is_exhausted:
                        st.markdown("**⚠️ حالة:** مقترحة (غير متاحة للتسجيل)")
                    st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.success("✅ جميع المذكرات مسجلة!")

# ============================================================
# فضاء الإدارة
# ============================================================
elif st.session_state.user_type == "admin":
    if not st.session_state.logged_in:
        col1, col2 = st.columns([4, 1])
        with col2:
            if st.button("🔙 رجوع", key="back_admin"):
                st.session_state.user_type = None
                st.rerun()
        
        st.subheader("🔐 فضاء الإدارة")
        
        username = st.text_input("اسم المستخدم", max_chars=50)
        password = st.text_input("كلمة المرور", type="password", max_chars=50)
        
        if st.button("تسجيل الدخول"):
            valid, result = verify_admin(username, password)
            if not valid:
                st.error(result)
            else:
                st.session_state.admin_user = result
                st.session_state.logged_in = True
                st.rerun()
    
    else:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.header("🔐 لوحة تحكم الإدارة")
        with col2:
            if st.button("🚪 خروج", key="logout_admin"):
                logout()
        
        # إحصائيات عامة
        total_students = len(df_students)
        total_memos = len(df_memos)
        registered_memos = len(df_memos[df_memos["تم التسجيل"].astype(str).str.strip() == "نعم"])
        available_memos = total_memos - registered_memos
        total_profs = len(df_prof_memos["الأستاذ"].unique())
        
        st.subheader("📊 الإحصائيات العامة")
        
        # إحصائيات بدون مستطيلات زرقاء
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.markdown(f"### {total_students}")
            st.markdown("**👨‍🎓 الطلاب**")
        
        with col2:
            st.markdown(f"### {total_profs}")
            st.markdown("**👨‍🏫 الأساتذة**")
        
        with col3:
            st.markdown(f"### {total_memos}")
            st.markdown("**📚 المذكرات**")
        
        with col4:
            st.markdown(f"### {registered_memos}")
            st.markdown("**✅ المسجلة**")
        
        with col5:
            st.markdown(f"### {available_memos}")
            st.markdown("**⏳ المتاحة**")
        
        st.markdown("---")
        
        # التبويبات
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["📝 المذكرات", "👨‍🎓 الطلاب", "👨‍🏫 الأساتذة", "📊 تقارير", "🔄 تحديث"])
        
        with tab1:
            st.subheader("📝 جميع المذكرات")
            
            filter_status = st.selectbox("تصفية حسب الحالة:", ["الكل", "مسجلة", "متاحة"])
            
            if filter_status == "مسجلة":
                display_memos = df_memos[df_memos["تم التسجيل"].astype(str).str.strip() == "نعم"]
            elif filter_status == "متاحة":
                display_memos = df_memos[df_memos["تم التسجيل"].astype(str).str.strip() != "نعم"]
            else:
                display_memos = df_memos
            
            st.dataframe(display_memos, use_container_width=True, height=400)
        
        with tab2:
            st.subheader("👨‍🎓 جميع الطلاب")
            
            search_student = st.text_input("🔍 بحث عن طالب (اللقب أو الاسم):", "")
            
            if search_student:
                filtered_students = df_students[
                    df_students["اللقب"].astype(str).str.contains(search_student, case=False, na=False) |
                    df_students["الإسم"].astype(str).str.contains(search_student, case=False, na=False)
                ]
                st.dataframe(filtered_students, use_container_width=True, height=400)
            else:
                st.dataframe(df_students, use_container_width=True, height=400)
        
        with tab3:
            st.subheader("👨‍🏫 الأساتذة والمذكرات")
            
            profs_list = sorted(df_memos["الأستاذ"].dropna().unique())
            selected_prof = st.selectbox("اختر أستاذاً:", ["الكل"] + profs_list)
            
            if selected_prof != "الكل":
                prof_data = df_memos[df_memos["الأستاذ"].astype(str).str.strip() == selected_prof.strip()]
                st.dataframe(prof_data, use_container_width=True, height=400)
            else:
                prof_summary = df_memos.groupby("الأستاذ").agg({
                    "رقم المذكرة": "count",
                    "تم التسجيل": lambda x: (x.astype(str).str.strip() == "نعم").sum()
                }).rename(columns={
                    "رقم المذكرة": "إجمالي المذكرات",
                    "تم التسجيل": "المذكرات المسجلة"
                })
                prof_summary["المذكرات المتاحة"] = prof_summary["إجمالي المذكرات"] - prof_summary["المذكرات المسجلة"]
                st.dataframe(prof_summary, use_container_width=True)
        
        with tab4:
            st.subheader("📊 تقارير مفصلة")
            
            st.markdown("#### 📈 توزيع المذكرات حسب التخصص")
            specialty_dist = df_memos.groupby("التخصص").agg({
                "رقم المذكرة": "count",
                "تم التسجيل": lambda x: (x.astype(str).str.strip() == "نعم").sum()
            }).rename(columns={
                "رقم المذكرة": "العدد الكلي",
                "تم التسجيل": "المسجلة"
            })
            specialty_dist["المتاحة"] = specialty_dist["العدد الكلي"] - specialty_dist["المسجلة"]
            st.dataframe(specialty_dist, use_container_width=True)
            
            st.markdown("---")
            st.markdown("#### 📅 آخر التسجيلات")
            recent_registrations = df_memos[df_memos["تم التسجيل"].astype(str).str.strip() == "نعم"].tail(10)
            if not recent_registrations.empty and "تاريخ التسجيل" in recent_registrations.columns:
                st.dataframe(recent_registrations[["رقم المذكرة", "عنوان المذكرة", "الأستاذ", "الطالب الأول", "تاريخ التسجيل"]], use_container_width=True)
            else:
                st.info("لا توجد تسجيلات حديثة")
            
            st.markdown("---")
            st.markdown("#### 📊 نسب التقدم")
            progress_summary = df_memos[df_memos["تم التسجيل"].astype(str).str.strip() == "نعم"].copy()
            if not progress_summary.empty and "نسبة التقدم" in progress_summary.columns:
                progress_summary["نسبة التقدم"] = progress_summary["نسبة التقدم"].apply(lambda x: int(x) if str(x).isdigit() else 0)
                avg_progress = progress_summary["نسبة التقدم"].mean()
                st.markdown(f"**📊 متوسط نسبة التقدم العامة:** {avg_progress:.1f}%")
                st.markdown(f'<div class="progress-container"><div class="progress-bar" style="width: {avg_progress}%;">{avg_progress:.1f}%</div></div>', unsafe_allow_html=True)
        
        with tab5:
            st.subheader("🔄 تحديث البيانات")
            st.info("⚠️ استخدم هذا الخيار لتحديث البيانات من Google Sheets")
            
            if st.button("🔄 تحديث البيانات الآن", type="primary"):
                with st.spinner("⏳ جاري تحديث البيانات..."):
                    clear_cache_and_reload()
                    time.sleep(2)
                    st.success("✅ تم تحديث البيانات بنجاح!")
                    st.rerun()

# ---------------- Footer ----------------
st.markdown("---")
st.markdown("""
    <div style='text-align:center; color:#888; font-size:12px; padding:20px;'>
        <p>© 2026 جامعة محمد البشير الإبراهيمي - كلية الحقوق والعلوم السياسية</p>
        <p>للاستفسار يرجى الاتصال بمكتب فريق التكوين</p>
    </div>
""", unsafe_allow_html=True)