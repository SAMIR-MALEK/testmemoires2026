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

# ═══════════════════════════════════════════════════════════════════════════
# 1. الإعدادات الأساسية - BASIC CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
st.set_page_config(page_title="تسجيل مذكرة ماستر", page_icon="🎓", layout="centered")

# ═══════════════════════════════════════════════════════════════════════════
# 2. التصميم والأنماط - STYLES & CSS
# ═══════════════════════════════════════════════════════════════════════════

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
html, body, [class*="css"] { font-family: 'Cairo', sans-serif !important; }
.main { background-color: #0A1B2C; color: #ffffff; }
.block-container { padding: 2rem; background-color: #1A2A3D; border-radius: 12px; max-width: 750px; margin:auto;}
label, h1, h2, h3, h4, h5, h6, p, span, .stTextInput label { color:#ffffff !important; }
button { background-color:#256D85 !important; color:white !important; border:none !important; padding:10px 20px !important; border-radius:6px !important; }
button:hover { background-color:#2C89A0 !important; }
.success-msg, .error-msg, .info-msg { color: #FFFFFF; padding: 15px; margin: 10px 0; }
.stat-card { background: rgba(255,255,255,0.1); padding: 15px; border-radius: 8px; margin: 10px 0; }
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════
# 3. إعدادات Google Sheets - GOOGLE SHEETS CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
info = st.secrets["service_account"]
credentials = Credentials.from_service_account_info(info, scopes=SCOPES)
sheets_service = build('sheets', 'v4', credentials=credentials)

STUDENTS_SHEET_ID = "1gvNkOVVKo6AO07dRKMnSQw6vZ3KdUnW7I4HBk61Sqns"
MEMOS_SHEET_ID = "1LNJMBAye4QIQy7JHz6F8mQ6-XNC1weZx1ozDZFfjD5s"
PROF_MEMOS_SHEET_ID = "1OnZi1o-oPMUI_W_Ew-op0a1uOhSj006hw_2jrMD6FSE"

STUDENTS_RANGE = "Feuille 1!A1:L1000"
MEMOS_RANGE = "Feuille 1!A1:N1000"
PROF_MEMOS_RANGE = "Feuille 1!A1:L1000"

# ═══════════════════════════════════════════════════════════════════════════
# 4. إعدادات البريد الإلكتروني - EMAIL CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

EMAIL_SENDER = "domaine.dsp@univ-bba.dz"
EMAIL_PASSWORD = "oevruyiztgikwzah"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# ═══════════════════════════════════════════════════════════════════════════
# 5. الثوابت - CONSTANTS (يمكن تعديلها حسب الحاجة)
# ═══════════════════════════════════════════════════════════════════════════

USER_TYPE_STUDENT = "student"
USER_TYPE_PROFESSOR = "professor"
USER_TYPE_ADMIN = "admin"
MEMO_REGISTERED = "نعم"
ADMIN_USERNAME = "admin"  # غيّر هنا
ADMIN_PASSWORD = "admin2026"  # غيّر هنا

# ═══════════════════════════════════════════════════════════════════════════
# 6. دوال مساعدة - UTILITY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

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

def clear_cache_and_reload():
    st.cache_data.clear()
    logger.info("تم مسح السجلات")

# ═══════════════════════════════════════════════════════════════════════════
# 7. تحميل البيانات - DATA LOADING
# ═══════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=60)
def load_students():
    try:
        result = sheets_service.spreadsheets().values().get(spreadsheetId=STUDENTS_SHEET_ID, range=STUDENTS_RANGE).execute()
        values = result.get('values', [])
        if not values:
            return pd.DataFrame()
        return pd.DataFrame(values[1:], columns=values[0])
    except Exception as e:
        logger.error(f"خطأ تحميل الطلاب: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=60)
def load_memos():
    try:
        result = sheets_service.spreadsheets().values().get(spreadsheetId=MEMOS_SHEET_ID, range=MEMOS_RANGE).execute()
        values = result.get('values', [])
        if not values:
            return pd.DataFrame()
        return pd.DataFrame(values[1:], columns=values[0])
    except Exception as e:
        logger.error(f"خطأ تحميل المذكرات: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=60)
def load_prof_memos():
    try:
        result = sheets_service.spreadsheets().values().get(spreadsheetId=PROF_MEMOS_SHEET_ID, range=PROF_MEMOS_RANGE).execute()
        values = result.get('values', [])
        if not values:
            return pd.DataFrame()
        return pd.DataFrame(values[1:], columns=values[0])
    except Exception as e:
        logger.error(f"خطأ تحميل مذكرات الأساتذة: {e}")
        return pd.DataFrame()

# ═══════════════════════════════════════════════════════════════════════════
# 8. البريد الإلكتروني - EMAIL
# ═══════════════════════════════════════════════════════════════════════════

def send_email_to_professor(prof_email, prof_name, memo_info, student1, student2=None):
    try:
        df_prof_memos = load_prof_memos()
        prof_memos = df_prof_memos[df_prof_memos["الأستاذ"].astype(str).str.strip() == prof_name.strip()]
        total = len(prof_memos)
        registered = len(prof_memos[prof_memos["تم التسجيل"].astype(str).str.strip() == MEMO_REGISTERED])
        
        student2_info = f"\n👤 الطالب الثاني: {student2['اللقب']} {student2['الإسم']}" if student2 else ""
        
        email_body = f"""<html dir="rtl"><body>
        <h2>✅ تسجيل مذكرة جديدة</h2>
        <p>الأستاذ(ة) {prof_name}،</p>
        <p>تم تسجيل مذكرة جديدة:</p>
        <p>📄 رقم المذكرة: {memo_info['رقم المذكرة']}</p>
        <p>📑 العنوان: {memo_info['عنوان المذكرة']}</p>
        <p>👤 الطالب الأول: {student1['اللقب']} {student1['الإسم']}{student2_info}</p>
        <p>📊 المسجلة: {registered} من {total}</p>
        </body></html>"""
        
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
        return False, f"فشل: {e}"

# ═══════════════════════════════════════════════════════════════════════════
# 9. التحقق - VERIFICATION
# ═══════════════════════════════════════════════════════════════════════════

def verify_student(username, password, df_students):
    valid, result = validate_username(username)
    if not valid:
        return False, result
    username = result
    password = sanitize_input(password)
    if df_students.empty:
        return False, "❌ خطأ تحميل البيانات"
    student = df_students[df_students["اسم المستخدم"].astype(str).str.strip() == username]
    if student.empty:
        return False, "❌ اسم المستخدم غير موجود"
    if student.iloc[0]["كلمة السر"].strip() != password:
        return False, "❌ كلمة السر خاطئة"
    return True, student.iloc[0]

def verify_students_batch(students_data, df_students):
    verified = []
    for username, password in students_data:
        if not username:
            continue
        valid, student = verify_student(username, password, df_students)
        if not valid:
            return False, student
        verified.append(student)
    return True, verified

def verify_professor(username, password, df_prof_memos):
    valid, result = validate_username(username)
    if not valid:
        return False, result
    username = result
    password = sanitize_input(password)
    if df_prof_memos.empty:
        return False, "❌ خطأ تحميل البيانات"
    prof = df_prof_memos[
        (df_prof_memos["إسم المستخدم"].astype(str).str.strip() == username) &
        (df_prof_memos["كلمة المرور"].astype(str).str.strip() == password)
    ]
    if prof.empty:
        return False, "❌ بيانات خاطئة"
    return True, prof.iloc[0]

def verify_admin(username, password):
    username = sanitize_input(username)
    password = sanitize_input(password)
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        return True, None
    return False, "❌ بيانات الإدارة خاطئة"

def verify_professor_password(note_number, prof_password, df_memos, df_prof_memos):
    valid, result = validate_note_number(note_number)
    if not valid:
        return False, None, result
    note_number = result
    prof_password = sanitize_input(prof_password)
    if df_memos.empty or df_prof_memos.empty:
        return False, None, "❌ خطأ تحميل البيانات"
    memo_row = df_memos[df_memos["رقم المذكرة"].astype(str).str.strip() == note_number]
    if memo_row.empty:
        return False, None, "❌ رقم المذكرة غير موجود"
    memo_row = memo_row.iloc[0]
    if str(memo_row.get("تم التسجيل", "")).strip() == MEMO_REGISTERED:
        return False, None, "❌ المذكرة مسجلة مسبقاً"
    prof_row = df_prof_memos[
        (df_prof_memos["الأستاذ"].astype(str).str.strip() == memo_row["الأستاذ"].strip()) &
        (df_prof_memos["كلمة سر التسجيل"].astype(str).str.strip() == prof_password)
    ]
    if prof_row.empty:
        return False, None, "❌ كلمة السر خاطئة"
    if str(prof_row.iloc[0].get("تم التسجيل", "")).strip() == MEMO_REGISTERED:
        return False, None, "❌ كلمة السر مستخدمة"
    return True, prof_row.iloc[0], None

# ═══════════════════════════════════════════════════════════════════════════
# 10. تحديث البيانات - DATA UPDATE
# ═══════════════════════════════════════════════════════════════════════════

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
             "values": [[MEMO_REGISTERED]]},
            {"range": f"Feuille 1!{col_letter(col_names.index('تاريخ التسجيل')+1)}{prof_row_idx}",
             "values": [[datetime.now().strftime('%Y-%m-%d %H:%M')]]},
            {"range": f"Feuille 1!{col_letter(col_names.index('رقم المذكرة')+1)}{prof_row_idx}",
             "values": [[note_number]]}
        ]
        
        if student2:
            updates.append({"range": f"Feuille 1!{col_letter(col_names.index('الطالب الثاني')+1)}{prof_row_idx}",
                          "values": [[student2['اللقب'] + ' ' + student2['الإسم']]]})
        
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
             "values": [[MEMO_REGISTERED]]},
            {"range": f"Feuille 1!{col_letter(memo_cols.index('تاريخ التسجيل')+1)}{memo_row_idx}",
             "values": [[datetime.now().strftime('%Y-%m-%d %H:%M')]]}
        ]
        
        if 'كلمة سر التسجيل' in memo_cols:
            updates2.append({"range": f"Feuille 1!{col_letter(memo_cols.index('كلمة سر التسجيل')+1)}{memo_row_idx}",
                           "values": [[used_prof_password]]})
        
        if student2:
            updates2.append({"range": f"Feuille 1!{col_letter(memo_cols.index('الطالب الثاني')+1)}{memo_row_idx}",
                           "values": [[student2['اللقب'] + ' ' + student2['الإسم']]]})
        
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

        if student2:
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
        
        if student2:
            st.session_state.student2 = df_students_updated[
                df_students_updated["اسم المستخدم"].astype(str).str.strip() == student2['اسم المستخدم'].strip()
            ].iloc[0]

        memo_data = df_memos[df_memos["رقم المذكرة"].astype(str).str.strip() == str(note_number).strip()].iloc[0]
        prof_memo_data = df_prof_memos[(df_prof_memos["الأستاذ"].astype(str).str.strip() == prof_name)].iloc[0]
        prof_email = str(prof_memo_data.get("الإيميل", "")).strip()
        
        if prof_email and "@" in prof_email:
            send_email_to_professor(prof_email, prof_name, memo_data, student1, student2)
        
        return True, "✅ تم التسجيل بنجاح!"
    except Exception as e:
        logger.error(f"خطأ التحديث: {e}")
        return False, f"❌ خطأ: {e}"

# ═══════════════════════════════════════════════════════════════════════════
# 11. إدارة الجلسة - SESSION MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════

def initialize_session_state():
    defaults = {
        'logged_in': False, 'user_type': None, 'student1': None, 'student2': None,
        'professor_data': None, 'memo_type': "فردية", 'mode': "register",
        'note_number': "", 'prof_password': "", 'show_confirmation': False
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def logout():
    st.session_state.clear()
    initialize_session_state()
    st.rerun()

# ═══════════════════════════════════════════════════════════════════════════
# 12. واجهات المستخدم - USER INTERFACES
# ═══════════════════════════════════════════════════════════════════════════

def show_header():
    st.markdown("<h5 style='text-align:center;'>جامعة محمد البشير الإبراهيمي</h5>", unsafe_allow_html=True)
    st.markdown("<h6 style='text-align:center;'>كلية الحقوق والعلوم السياسية</h6>", unsafe_allow_html=True)
    st.markdown("<div style='text-align:center; margin:20px 0;'><img src='https://raw.githubusercontent.com/SAMIR-MALEK/memoire-depot-2026/main/LOGO2.png' width='100'></div>", unsafe_allow_html=True)
    st.markdown("<h4 style='text-align:center; color:#FFD700;'>منصة تسجيل مذكرة الماستر</h4>", unsafe_allow_html=True)

def show_login_selection():
    st.markdown('<div class="block-container">', unsafe_allow_html=True)
    show_header()
    st.markdown("---")
    st.markdown("### 🔐 اختر نوع الدخول")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("👨‍🎓 الطلاب", use_container_width=True):
            st.session_state.user_type = USER_TYPE_STUDENT
            st.rerun()
    with col2:
        if st.button("👨‍🏫 الأساتذة", use_container_width=True):
            st.session_state.user_type = USER_TYPE_PROFESSOR
            st.rerun()
    with col3:
        if st.button("👔 الإدارة", use_container_width=True):
            st.session_state.user_type = USER_TYPE_ADMIN
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

def show_student_login(df_students):
    st.markdown('<div class="block-container">', unsafe_allow_html=True)
    show_header()
    if st.button("⬅️ رجوع"):
        st.session_state.user_type = None
        st.rerun()
    st.markdown("### 👨‍🎓 دخول الطلاب")
    st.session_state.memo_type = st.radio("نوع المذكرة:", ["فردية", "ثنائية"])
    username1 = st.text_input("اسم المستخدم الأول", max_chars=50)
    password1 = st.text_input("كلمة السر الأول", type="password", max_chars=50)
    username2 = password2 = None
    if st.session_state.memo_type == "ثنائية":
        username2 = st.text_input("اسم المستخدم الثاني", max_chars=50)
        password2 = st.text_input("كلمة السر الثاني", type="password", max_chars=50)
    if st.button("دخول", type="primary"):
        if st.session_state.memo_type == "ثنائية" and (not username2 or not password2):
            st.markdown('<div class="error-msg">⚠️ أدخل بيانات الثاني</div>', unsafe_allow_html=True)
            st.stop()
        if st.session_state.memo_type == "ثنائية" and username1.strip().lower() == username2.strip().lower():
            st.markdown('<div class="error-msg">❌ نفس الشخص!</div>', unsafe_allow_html=True)
            st.stop()
        students_data = [(username1, password1)]
        if st.session_state.memo_type == "ثنائية" and username2:
            students_data.append((username2, password2))
        valid, result = verify_students_batch(students_data, df_students)
        if not valid:
            st.markdown(f'<div class="error-msg">{result}</div>', unsafe_allow_html=True)
        else:
            verified = result
            st.session_state.student1 = verified[0]
            st.session_state.student2 = verified[1] if len(verified) > 1 else None
            if st.session_state.memo_type == "ثنائية" and st.session_state.student2:
                s1_note = str(st.session_state.student1.get('رقم المذكرة', '')).strip()
                s2_note = str(st.session_state.student2.get('رقم المذكرة', '')).strip()
                s1_spec = str(st.session_state.student1.get('التخصص', '')).strip()
                s2_spec = str(st.session_state.student2.get('التخصص', '')).strip()
                if s1_spec != s2_spec:
                    st.markdown('<div class="error-msg">❌ تخصصات مختلفة</div>', unsafe_allow_html=True)
                    st.stop()
                if (s1_note and not s2_note) or (not s1_note and s2_note):
                    st.markdown('<div class="error-msg">❌ أحدهما مسجل</div>', unsafe_allow_html=True)
                    st.stop()
                if s1_note and s2_note and s1_note != s2_note:
                    st.markdown('<div class="error-msg">❌ مذكرتان مختلفتان</div>', unsafe_allow_html=True)
                    st.stop()
                if s1_note and s2_note:
                    st.session_state.mode = "view"
            if st.session_state.memo_type == "فردية":
                fardiya = str(st.session_state.student1.get('فردية', '')).strip()
                if fardiya not in ["1", "نعم"]:
                    st.markdown('<div class="error-msg">❌ غير مسموح فردي</div>', unsafe_allow_html=True)
                    st.stop()
            note = str(st.session_state.student1.get('رقم المذكرة', '')).strip()
            st.session_state.mode = "view" if note else "register"
            st.session_state.logged_in = True
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

def show_professor_login(df_prof_memos):
    st.markdown('<div class="block-container">', unsafe_allow_html=True)
    show_header()
    if st.button("⬅️ رجوع"):
        st.session_state.user_type = None
        st.rerun()
    st.markdown("### 👨‍🏫 دخول الأساتذة")
    username = st.text_input("اسم المستخدم", max_chars=50)
    password = st.text_input("كلم
