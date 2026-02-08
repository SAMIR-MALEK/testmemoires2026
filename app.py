import streamlit as st
import pandas as pd
from datetime import datetime
import base64
import time
import logging
from google.oauth2 import service_account
from googleapiclient.discovery import build
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ============================================================
# إعدادات الصفحة
# ============================================================
st.set_page_config(page_title="نظام إدارة مذكرات التخرج", layout="wide", page_icon="📚")

# ============================================================
# إعداد نظام السجل
# ============================================================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================
# الثوابت والإعدادات
# ============================================================
ADMIN_CREDENTIALS = {
    "admin": st.secrets.get("ADMIN_PASSWORD", "admin123"),
}

# معرفات Google Sheets
try:
    MEMOS_SHEET_ID = st.secrets["MEMOS_SHEET_ID"]
    STUDENTS_SHEET_ID = st.secrets["STUDENTS_SHEET_ID"]
    PROF_MEMOS_SHEET_ID = st.secrets["PROF_MEMOS_SHEET_ID"]
    REQUESTS_SHEET_ID = st.secrets.get("REQUESTS_SHEET_ID", "")
except KeyError as e:
    st.error(f"❌ خطأ: معرف Google Sheet مفقود في secrets: {e}")
    st.stop()

# إعدادات البريد الإلكتروني
EMAIL_CONFIG = {
    "smtp_server": st.secrets.get("EMAIL_SMTP_SERVER", "smtp.gmail.com"),
    "smtp_port": st.secrets.get("EMAIL_SMTP_PORT", 587),
    "sender_email": st.secrets.get("EMAIL_SENDER", ""),
    "sender_password": st.secrets.get("EMAIL_PASSWORD", ""),
}

# ============================================================
# الاتصال بـ Google Sheets
# ============================================================
@st.cache_resource
def get_sheets_service():
    try:
        credentials_dict = dict(st.secrets["gcp_service_account"])
        credentials = service_account.Credentials.from_service_account_info(
            credentials_dict,
            scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )
        return build('sheets', 'v4', credentials=credentials)
    except Exception as e:
        st.error(f"❌ خطأ في الاتصال بـ Google Sheets: {str(e)}")
        return None

sheets_service = get_sheets_service()

# ============================================================
# دوال تحميل البيانات
# ============================================================
@st.cache_data(ttl=300)
def load_memos():
    if not sheets_service or not MEMOS_SHEET_ID:
        return pd.DataFrame()
    try:
        result = sheets_service.spreadsheets().values().get(
            spreadsheetId=MEMOS_SHEET_ID,
            range="Feuille 1!A:Z"
        ).execute()
        values = result.get('values', [])
        if not values or len(values) < 2:
            return pd.DataFrame()
        df = pd.DataFrame(values[1:], columns=values[0])
        return df
    except Exception as e:
        logger.error(f"خطأ في تحميل المذكرات: {str(e)}")
        return pd.DataFrame()

@st.cache_data(ttl=300)
def load_students():
    if not sheets_service or not STUDENTS_SHEET_ID:
        return pd.DataFrame()
    try:
        result = sheets_service.spreadsheets().values().get(
            spreadsheetId=STUDENTS_SHEET_ID,
            range="Feuille 1!A:Z"
        ).execute()
        values = result.get('values', [])
        if not values or len(values) < 2:
            return pd.DataFrame()
        df = pd.DataFrame(values[1:], columns=values[0])
        return df
    except Exception as e:
        logger.error(f"خطأ في تحميل الطلاب: {str(e)}")
        return pd.DataFrame()

@st.cache_data(ttl=300)
def load_prof_memos():
    if not sheets_service or not PROF_MEMOS_SHEET_ID:
        return pd.DataFrame()
    try:
        result = sheets_service.spreadsheets().values().get(
            spreadsheetId=PROF_MEMOS_SHEET_ID,
            range="Feuille 1!A:Z"
        ).execute()
        values = result.get('values', [])
        if not values or len(values) < 2:
            return pd.DataFrame()
        df = pd.DataFrame(values[1:], columns=values[0])
        return df
    except Exception as e:
        logger.error(f"خطأ في تحميل بيانات الأساتذة: {str(e)}")
        return pd.DataFrame()

@st.cache_data(ttl=300)
def load_requests():
    if not sheets_service or not REQUESTS_SHEET_ID:
        return pd.DataFrame()
    try:
        result = sheets_service.spreadsheets().values().get(
            spreadsheetId=REQUESTS_SHEET_ID,
            range="Feuille 1!A:Z"
        ).execute()
        values = result.get('values', [])
        if not values or len(values) < 2:
            return pd.DataFrame()
        df = pd.DataFrame(values[1:], columns=values[0])
        return df
    except Exception as e:
        logger.error(f"خطأ في تحميل الطلبات: {str(e)}")
        return pd.DataFrame()

# ============================================================
# دوال مساعدة
# ============================================================
def sanitize_input(text):
    """تنظيف النص من المسافات الزائدة"""
    if not text:
        return ""
    return str(text).strip()

def validate_username(username):
    """التحقق من صحة اسم المستخدم"""
    username = sanitize_input(username)
    if not username:
        return False, "❌ اسم المستخدم فارغ"
    if len(username) < 3:
        return False, "❌ اسم المستخدم قصير جداً"
    return True, username

def validate_note_number(note_number):
    """التحقق من صحة رقم المذكرة"""
    note_number = sanitize_input(note_number)
    if not note_number:
        return False, "❌ رقم المذكرة فارغ"
    return True, note_number

def col_letter(col_num):
    """تحويل رقم العمود إلى حرف (1=A, 2=B, ...، 27=AA)"""
    string = ""
    while col_num > 0:
        col_num, remainder = divmod(col_num - 1, 26)
        string = chr(65 + remainder) + string
    return string

def clear_cache_and_reload():
    """مسح الذاكرة المؤقتة وإعادة تحميل البيانات"""
    st.cache_data.clear()


# ---------------- دوال التحقق ----------------
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

# ============================================================
# الدالة المعدلة: تحديث التسجيل (مع تصحيح البحث في شيت الأساتذة)
# ============================================================
def update_registration(note_number, student1, student2=None):
    try:
        df_memos = load_memos()
        df_prof_memos = load_prof_memos()
        df_students = load_students()

        memo_data_main = df_memos[df_memos["رقم المذكرة"].astype(str).str.strip() == str(note_number).strip()]
        if memo_data_main.empty: return False, "❌ رقم المذكرة غير موجود في القائمة الرئيسية"
        
        prof_name = memo_data_main["الأستاذ"].iloc[0].strip()
        used_prof_password = st.session_state.prof_password.strip()

        potential_rows = df_prof_memos[
            (df_prof_memos["الأستاذ"].astype(str).str.strip() == prof_name) & 
            (df_prof_memos["كلمة سر التسجيل"].astype(str).str.strip() == used_prof_password)
        ]
        if potential_rows.empty: return False, "❌ بيانات الأستاذ أو كلمة السر غير متطابقة في شيت المتابعة"

        target_row = potential_rows[potential_rows["رقم المذكرة"].astype(str).str.strip() == str(note_number).strip()]
        if target_row.empty:
            target_row = potential_rows[potential_rows["تم التسجيل"].astype(str).str.strip() != "نعم"]
            if target_row.empty: return False, "❌ خطأ: جميع المذكرات المخصصة لهذا الأستاذ مسجلة بالفعل. لا يوجد مكان للتسجيل."

        prof_row_idx = target_row.index[0] + 2

        col_names = df_prof_memos.columns.tolist()
        s1_lname = student1.get('لقب', student1.get('اللقب', ''))
        s1_fname = student1.get('إسم', student1.get('الإسم', ''))
        
        updates = [
            {"range": f"Feuille 1!{col_letter(col_names.index('الطالب الأول')+1)}{prof_row_idx}", "values": [[s1_lname + ' ' + s1_fname]]},
            {"range": f"Feuille 1!{col_letter(col_names.index('تم التسجيل')+1)}{prof_row_idx}", "values": [["نعم"]]},
            {"range": f"Feuille 1!{col_letter(col_names.index('تاريخ التسجيل')+1)}{prof_row_idx}", "values": [[datetime.now().strftime('%Y-%m-%d %H:%M')]]},
            {"range": f"Feuille 1!{col_letter(col_names.index('رقم المذكرة')+1)}{prof_row_idx}", "values": [[note_number]]}
        ]
        if student2 is not None:
            s2_lname = student2.get('لقب', student2.get('اللقب', ''))
            s2_fname = student2.get('إسم', student2.get('الإسم', ''))
            updates.append({"range": f"Feuille 1!{col_letter(col_names.index('الطالب الثاني')+1)}{prof_row_idx}", "values": [[s2_lname + ' ' + s2_fname]]})

        sheets_service.spreadsheets().values().batchUpdate(
            spreadsheetId=PROF_MEMOS_SHEET_ID, 
            body={"valueInputOption": "USER_ENTERED", "data": updates}
        ).execute()

        memo_row_idx = df_memos[df_memos["رقم المذكرة"].astype(str).str.strip() == str(note_number).strip()].index[0] + 2
        memo_cols = df_memos.columns.tolist()
        reg1 = str(student1.get('رقم التسجيل', ''))
        reg2 = str(student2.get('رقم التسجيل', '')) if student2 else ""
        
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
        st.session_state.student1 = df_students_updated[df_students_updated["اسم المستخدم"].astype(str).str.strip() == student1['اسم المستخدم'].strip()].iloc[0].to_dict()
        if student2 is not None: 
            st.session_state.student2 = df_students_updated[df_students_updated["اسم المستخدم"].astype(str).str.strip() == student2['اسم المستخدم'].strip()].iloc[0].to_dict()
        
        memo_data = df_memos[df_memos["رقم المذكرة"].astype(str).str.strip() == str(note_number).strip()].iloc[0]
        email_sent, email_msg = send_email_to_professor(prof_name, memo_data, st.session_state.student1, st.session_state.student2 if student2 else None)
        
        if not email_sent:
            st.error(f"⚠️ {email_msg}")
            st.warning("تم تسجيل المذكرة في النظام، ولكن لم يتم إرسال الإيميل للأستاذ.")
        else: 
            st.success("📧 تم إرسال إشعار بالبريد الإلكتروني للأستاذ.")
            
        return True, "✅ تم تسجيل المذكرة بنجاح!"

    except Exception as e:
        logger.error(f"خطأ في تحديث التسجيل: {str(e)}")
        return False, f"❌ حدث خطأ أثناء التسجيل: {str(e)}"


# ============================================================
# جلب البيانات
# ============================================================

# تحميل البيانات الأولي
df_students = load_students()
df_memos = load_memos()
df_prof_memos = load_prof_memos()
df_requests = load_requests()
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
                st.session_state.user_type = 'student'
                st.session_state.logged_in = True
                st.session_state.student1 = s_data
                st.session_state.student2 = None
                note_num = str(s_data.get('رقم المذكرة', '')).strip()
                st.session_state.mode = "view" if note_num else "register"
        elif user_type == 'professor':
            p_data = lookup_professor(username)
            if p_data:
                st.session_state.user_type = 'professor'
                st.session_state.logged_in = True
                st.session_state.professor = p_data
        elif user_type == 'admin':
            if username in ADMIN_CREDENTIALS:
                st.session_state.user_type = 'admin'
                st.session_state.logged_in = True
                st.session_state.admin_user = username

restore_session_from_url()

# ============================================================
# تهيئة Session State (Robust Initialization)
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
    for key in st.session_state.keys():
        if key not in ['user_type']: del st.session_state[key]
    st.session_state.update({'logged_in': False, 'student1': None, 'student2': None, 'professor': None, 'admin_user': None, 'mode': "register", 'note_number': "", 'prof_password': "", 'show_confirmation': False, 'user_type': None, 'selected_memo_id': None})
    st.rerun()

# ============================================================
# الصفحة الرئيسية
# ============================================================
if st.session_state.user_type is None:
    st.markdown("<p style='text-align: center; color: #94A3B8; font-size: 1.2rem;'>جامعة محمد البشير الإبراهيمي - برج بوعريريج</p>", unsafe_allow_html=True)
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
    if not st.session_state.logged_in:
        col1, col2 = st.columns([4, 1])
        with col2:
            if st.button("رجوع", key="back_student"): st.session_state.user_type = None; st.rerun()
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
                    if not username1 or not password1: st.error("⚠️ يرجى إدخال اسم المستخدم وكلمة السر"); st.stop()
                if st.session_state.memo_type == "ثنائية":
                    if not username1 or not password1 or not username2 or not password2: st.error("⚠️ يرجى إدخال بيانات الطالبين كاملة"); st.stop()
                    if username1.strip().lower() == username2.strip().lower(): st.error("❌ لا يمكن أن يكون الطالب الأول والثاني نفس الشخص!"); st.stop()
                students_data = [(username1, password1)]
                if st.session_state.memo_type == "ثنائية" and username2: students_data.append((username2, password2))
                valid, result = verify_students_batch(students_data, df_students)
                if not valid: st.error(result)
                else:
                    verified_students = result
                    if not verified_students: st.error("حدث خطأ غير متوقع في التحقق من البيانات"); st.stop()
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
                    st.session_state.logged_in = True
                    st.query_params['ut'] = 'student'
                    st.query_params['un'] = encode_str(st.session_state.student1['اسم المستخدم'])
                    st.rerun()
    else:
        # ================= بداية التحقق الإلزامي من الهاتف =================
        s1 = st.session_state.student1; s2 = st.session_state.student2
        def is_phone_valid(phone_val):
            if not phone_val: return False
            return str(phone_val).strip() not in ['0', 'nan', '']
        s1_phone_ok = is_phone_valid(s1.get('الهاتف'))
        s2_phone_ok = is_phone_valid(s2.get('الهاتف')) if s2 else True
        if not s1_phone_ok or not s2_phone_ok:
            st.markdown(f"<div style='text-align: center; margin-top: 50px; margin-bottom: 30px;'><h1 style='color: #EF4444; font-size: 2.5rem;'>🚫 الوصول محظور</h1><p style='font-size: 1.2rem; color: #cbd5e1;'>نظام التسجيل يفرض وجود رقم هاتف صحيح لجميع الطلبة قبل الدخول.</p></div>", unsafe_allow_html=True)
            if not s1_phone_ok:
                st.markdown(f"<div class='card' style='border-right:5px solid #EF4444; background: rgba(239, 68, 68, 0.1);'><h3>❌ بيانات الطالب الأول: {s1.get('لقب', '')} {s1.get('إسم', '')}</h3><p>رقم الهاتف الحالي: <span style='color: #EF4444; font-weight: bold;'>غير مدخل</span></p></div>", unsafe_allow_html=True)
                with st.form(f"mandatory_update_s1"):
                    new_s1_phone = st.text_input("أدخل رقم هاتف الطالب الأول (إجباري):", placeholder="0550...")
                    if st.form_submit_button("✅ حفظ وفتح النظام", use_container_width=True):
                        if new_s1_phone and len(new_s1_phone) >= 10:
                            success, msg = update_student_phone(s1['اسم المستخدم'], new_s1_phone)
                            if success:
                                st.success(msg)
                                st.session_state.student1['الهاتف'] = new_s1_phone
                                time.sleep(1); st.rerun()
                            else: st.error(msg)
                        else: st.error("⚠️ يرجى إدخال رقم هاتف صحيح")
            if s2 and not s2_phone_ok:
                st.markdown("---")
                st.markdown(f"<div class='card' style='border-right:5px solid #EF4444; background: rgba(239, 68, 68, 0.1);'><h3>❌ بيانات الطالب الثاني: {s2.get('لقب', '')} {s2.get('إسم', '')}</h3><p>رقم الهاتف الحالي: <span style='color: #EF4444; font-weight: bold;'>غير مدخل</span></p></div>", unsafe_allow_html=True)
                with st.form(f"mandatory_update_s2"):
                    new_s2_phone = st.text_input("أدخل رقم هاتف الطالب الثاني (إجباري):", placeholder="0660...")
                    if st.form_submit_button("✅ حفظ وفتح النظام", use_container_width=True):
                        if new_s2_phone and len(new_s2_phone) >= 10:
                            success, msg = update_student_phone(s2['اسم المستخدم'], new_s2_phone)
                            if success:
                                st.success(msg)
                                st.session_state.student2['الهاتف'] = new_s2_phone
                                time.sleep(1); st.rerun()
                            else: st.error(msg)
                        else: st.error("⚠️ يرجى إدخال رقم هاتف صحيح")
            st.stop()
        # ================= نهاية التحقق الإلزامي من الهاتف =================
        col1, col2 = st.columns([4, 1])
        with col2:
            if st.button("خروج", key="logout_btn"): logout()
        st.markdown(f'<div class="card"><h3>ملف الطالب</h3><p>الطالب الأول: <b style="color:#2F6F7E;">{s1.get("لقب", s1.get("اللقب"))} {s1.get("إسم", s1.get("الإسم"))}</b></p><p>التخصص: <b>{s1.get("التخصص")}</b></p></div>', unsafe_allow_html=True)
        if s2 is not None: st.markdown(f'<div class="card"><p>الطالب الثاني: <b style="color:#2F6F7E;">{s2.get("لقب", s2.get("اللقب"))} {s2.get("إسم", s2.get("الإسم"))}</b></p></div>', unsafe_allow_html=True)

        # ============================================================
        # التعديل الجديد: إضافة التبويب الثالث لتتبع الملف
        # ============================================================
        tab_memo, tab_notify, tab_file_track = st.tabs(["مذكرتي", "الإشعارات والطلبات", "📂 تتبع ملف التخرج"])
        
        with tab_memo:
            if st.session_state.mode == "view":
                df_memos_fresh = load_memos()
                note_num = str(s1.get('رقم المذكرة', '')).strip()
                memo_info = df_memos_fresh[df_memos_fresh["رقم المذكرة"].astype(str).str.strip() == note_num]
                if not memo_info.empty:
                    memo_info = memo_info.iloc[0]
                    session_date = memo_info.get("موعد الجلسة القادمة", "")
                    session_html = f"<p>📅 <b>موعد الجلسة القادمة:</b> {session_date}</p>" if session_date else ""
                    st.markdown(f'''<div class="card" style="border-left: 5px solid #FFD700;"><h3>✅ أنت مسجل في المذكرة التالية:</h3><p><b>رقم المذكرة:</b> {memo_info['رقم المذكرة']}</p><p><b>العنوان:</b> {memo_info['عنوان المذكرة']}</p><p><b>المشرف:</b> {memo_info['الأستاذ']}</p><p><b>التخصص:</b> {memo_info['التخصص']}</p><p><b>التاريخ:</b> {memo_info.get('تاريخ التسجيل','')}</p>{session_html}</div>''', unsafe_allow_html=True)
            elif st.session_state.mode == "register":
                if datetime.now() > REGISTRATION_DEADLINE:
                    st.markdown("<div class='alert-card' style='text-align:center; padding:40px; border: 2px solid #EF4444; background: linear-gradient(135deg, #450a0a 0%, #7f1d1d 100%);'><h2 style='font-size:2.5rem; margin-bottom:20px;'>⛔ انتهت مهلة التسجيل</h2><p style='font-size:1.3rem; margin:20px 0; line-height:1.6;'>تم إيقاف خاصية التسجيل</p><div style='background: rgba(255,255,255,0.1); padding:15px; border-radius:10px; margin-top:20px;'><p style='font-size:1.2rem; color:#FFD700; margin:0; font-weight:bold;'>⚠️ يرجى الاتصال بمكتب فريق التكوين في الكلية يوم الأحد 01 فيفري 2025 </p></div></div>", unsafe_allow_html=True)
                else:
                    st.markdown('<div class="card"><h3>تسجيل مذكرة جديدة</h3></div>', unsafe_allow_html=True)
                    all_profs = sorted(df_memos["الأستاذ"].dropna().unique())
                    selected_prof = st.selectbox("اختر الأستاذ المشرف:", [""] + all_profs)
                    if selected_prof:
                        student_specialty = s1.get("التخصص")
                        prof_memos = df_memos[df_memos["الأستاذ"].astype(str).str.strip() == selected_prof.strip()]
                        reg_count = len(prof_memos[prof_memos["تم التسجيل"].astype(str).str.strip() == "نعم"])
                        if reg_count >= 4: st.error(f'❌ الأستاذ {selected_prof} استنفذ كل العناوين')
                        else:
                            avail_memos = df_memos[(df_memos["الأستاذ"].astype(str).str.strip() == selected_prof.strip()) & (df_memos["التخصص"].astype(str).str.strip() == student_specialty.strip()) & (df_memos["تم التسجيل"].astype(str).str.strip() != "نعم")][["رقم المذكرة", "عنوان المذكرة"]]
                            if not avail_memos.empty:
                                st.success(f'✅ المذكرات المتاحة في تخصصك ({student_specialty}):')
                                for _, row in avail_memos.iterrows(): st.markdown(f"**{row['رقم المذكرة']}.** {row['عنوان المذكرة']}")
                            else: st.error('لا توجد مذكرات متاحة لهذا الأستاذ في تخصصك حالياً ❌')
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
                                s1_reg_perm = str(s1.get('التسجيل', '')).strip()
                                s2_reg_perm = str(s2.get('التسجيل', '')).strip() if s2 else ''
                                if s1_reg_perm != '1' and s2_reg_perm != '1':
                                    st.error("⛔ عذراً، لم يتم السماح لك بتسجيل المذكرة في الوقت الحالي.")
                                    st.info("يرجى التواصل مع مسؤول الميدان: **البروفيسور لخضر رفاف**", icon="ℹ️")
                                    st.stop()
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
                df_memos_fresh = load_memos()
                my_memo_row = df_memos_fresh[df_memos_fresh["رقم المذكرة"] == my_memo_id]
                if not my_memo_row.empty:
                    my_prof = str(my_memo_row.iloc[0]["الأستاذ"]).strip()
                    base_filter = df_requests["النوع"] == "جلسة إشراف"
                    prof_filter = df_requests["الأستاذ"].astype(str).str.strip() == my_prof
                    prof_sessions = df_requests[base_filter & prof_filter]
                    if not prof_sessions.empty:
                        last_session = prof_sessions.iloc[-1]
                        details_display = ""; date_to_show = ""
                        try:
                            if len(last_session) > 8: 
                                raw_val = last_session.iloc[8]
                                if pd.notna(raw_val) and str(raw_val).strip() not in ['nan', '']:
                                    details_text = str(raw_val)
                                    import re
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
                                else: details_display = "لم يتم العثور على تفاصيل الموعد."
                        except Exception as e: details_display = "خطأ في قراءة البيانات."
                        st.markdown(f"<div class='card' style='border-right: 4px solid #3B82F6; background: rgba(59, 130, 246, 0.1);'><h4>🔔 جلسة إشراف</h4>{date_to_show}<p>{details_display}</p><small style='color: #666;'>تمت الجدولة: {last_session['الوقت']}</small></div>", unsafe_allow_html=True)
                my_reqs = df_requests[df_requests["رقم المذكرة"].astype(str).str.strip() == my_memo_id]
                if not my_reqs.empty:
                    for _, r in my_reqs.iterrows():
                        req_type = r['النوع']; details = ""
                        if len(r) > 8:
                            val = str(r.iloc[8]).strip()
                            if val and val.lower() not in ['nan', 'none']: details = val
                        show_details = True
                        if req_type in ["حذف طالب", "تنازل"]: show_details = False
                        st.markdown(f"""<div class="card" style="border-right: 4px solid #F59E0B; padding: 20px;"><h4>{req_type}</h4><p>التاريخ: {r['الوقت']}</p><p>الحالة: <b>{r.get('الحالة', 'غير محدد')}</b></p>{'<p>التفاصيل: ' + details + '</p>' if show_details and details else '<p><i>التفاصيل مخفية</i></p>'}</div>""", unsafe_allow_html=True)
                if prof_sessions.empty and my_reqs.empty: st.info("لا توجد إشعارات جديدة.")
            else: st.info("يجب تسجيل مذكرة أولاً لتلقي الإشعارات.")

        # ============================================================
        # --- التبويب الجديد: تتبع ملف التخرج (Student File Tracking) ---
        # ============================================================
        with tab_file_track:
            st.markdown("<h2 style='color: #F8FAFC; margin-bottom: 20px;'>📂 حالة ملف التخرج الإداري</h2>", unsafe_allow_html=True)
            st.info("يرجى التأكد من أن ملفك كامل ومتوفر في مصلحة التدريس لتجنب التأخير في إصدار الشهادة.")
            
            # جلب بيانات طازجة من df_students لضمان قراءة الأعمدة الجديدة
            s1_fresh = df_students[df_students["اسم المستخدم"] == s1['اسم المستخدم']]
            if not s1_fresh.empty:
                s1_data = s1_fresh.iloc[0].to_dict()
            else:
                s1_data = s1 # Fallback

            # دالة مساعدة لتحديد اللون
            def get_status_color(val):
                val_str = str(val).strip()
                if val_str in ["موجودة", "موجود", "كامل", "جاهزة", "تم تسليمها للطالب", "قيد الانجاز"]: return "status-ok"
                elif val_str in ["غير موجودة", "غير موجود", "غير كامل", "الملف غير كامل", "مدين", "خطأ في الكشف"]: return "status-err"
                else: return "status-neutral"

            docs_list = [
                {"title": "📄 شهادة الميلاد", "desc": "على الطالب إحضارها لمصلحة التدريس", "value": s1_data.get("شهادة الميلاد", "غير محدد").strip() if "شهادة الميلاد" in s1_data else "غير محدد"},
                {"title": "📊 كشف النقاط - السنة أولى ماستر", "desc": "يجب أن تكون غير مدين", "value": s1_data.get("كشف1", "غير محدد").strip() if "كشف1" in s1_data else "غير محدد"},
                {"title": "📊 كشف النقاط - السنة ثانية ماستر", "desc": "إلى غاية إجراء المداولات", "value": s1_data.get("كشف2", "غير محدد").strip() if "كشف2" in s1_data else "غير محدد"},
                {"title": "🎓 محضر المناقشة", "desc": "يتوفر بعد المناقشة", "value": s1_data.get("محضر المناقشة", "غير محدد").strip() if "محضر المناقشة" in s1_data else "غير محدد"}
            ]

            st.markdown("<div class='file-track-grid'>", unsafe_allow_html=True)
            for doc in docs_list:
                color_class = get_status_color(doc["value"])
                if doc["value"].lower() in ["nan", "", "none"]:
                    display_value = "لم يُحدد بعد"; color_class = "status-neutral"
                else: display_value = doc["value"]
                st.markdown(f"<div class='file-track-card'><div class='doc-title'>{doc['title']}</div><div class='doc-status {color_class}'>{display_value}</div><small style='color: #64748B; font-size: 0.85rem;'>{doc['desc']}</small></div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("<hr style='border-color: #334155; margin: 30px 0;'>", unsafe_allow_html=True)
            col_file, col_cert = st.columns(2)
            with col_file:
                file_status = s1_data.get("حالة الملف", "غير محدد").strip() if "حالة الملف" in s1_data else "غير محدد"
                file_color = get_status_color(file_status)
                st.markdown(f"<div class='card' style='text-align:center; border-top: 4px solid #64748B;'><h3 style='color: #94A3B8; font-size: 1rem; margin-bottom: 10px;'>📁 حالة الملف الإداري</h3><div style='font-size: 1.5rem; font-weight: bold; color: #F8FAFC;' class='{file_color}'>{file_status}</div><p style='font-size:0.8rem; color:#64748B; margin-top:10px;'>مكان الملف: <span style='color:#fff; font-weight:600;'>{s1_data.get('مكان الملف', 'غير محدد') if 'مكان الملف' in s1_data else 'غير محدد'}</span></p></div>", unsafe_allow_html=True)
            with col_cert:
                cert_status = s1_data.get("حالة الشهادة", "غير محدد").strip() if "حالة الشهادة" in s1_data else "غير محدد"
                cert_color = get_status_color(cert_status)
                st.markdown(f"<div class='card' style='text-align:center; border-top: 4px solid #FFD700;'><h3 style='color: #94A3B8; font-size: 1rem; margin-bottom: 10px;'>🎓 حالة الشهادة</h3><div style='font-size: 1.5rem; font-weight: bold; color: #F8FAFC;' class='{cert_color}'>{cert_status}</div></div>", unsafe_allow_html=True)

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
                else: 
                    st.session_state.professor = r; st.session_state.logged_in = True
                    st.query_params['ut'] = 'professor'
                    st.query_params['un'] = encode_str(st.session_state.professor['إسم المستخدم'])
                    st.rerun()
    else:
        prof = st.session_state.professor; prof_name = prof["الأستاذ"]
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
            student_cards_html = f"<div class='student-card'><h4 style='color: #FFD700; margin-top: 0; font-size: 1.1rem;'>الطالب الأول</h4><p style='font-size: 1.3rem; font-weight: bold; margin: 15px 0 5px 0; color: #fff;'>{student_info['s1_name']}</p><p style='font-size: 0.9rem; color: #94A3B8;'>رقم التسجيل: {student_info['s1_reg'] or '--'}</p><div style='margin-top: 15px; padding: 8px; background: rgba(16, 185, 129, 0.1); border-radius: 8px; color: #10B981; font-size: 0.9rem;'>📧 {student_info['s1_email'] or 'غير متوفر'}</div></div>"
            if student_info['s2_name']:
                student_cards_html += f"<div class='student-card'><h4 style='color: #FFD700; margin-top: 0; font-size: 1.1rem;'>الطالب الثاني</h4><p style='font-size: 1.3rem; font-weight: bold; margin: 15px 0 5px 0; color: #fff;'>{student_info['s2_name']}</p><p style='font-size: 0.9rem; color: #C0C0C0;'>رقم التسجيل: {student_info['s2_reg'] or '--'}</p><div style='margin-top: 15px; padding: 8px; background: rgba(16, 185, 129, 0.1); border-radius: 8px; color: #10B981; font-size: 0.9rem;'>📧 {student_info['s2_email'] or 'غير متوفر'}</div></div>"
            student_cards_html += "</div>"
            full_memo_html = f"""<div class="full-view-container"><div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; flex-wrap: wrap;"><div><p class="memo-badge">{current_memo['التخصص']}</p><h1 class="memo-id">{current_memo['رقم المذكرة']}</h1></div></div><div style="text-align: center; border-bottom: 2px solid #2F6F7E; padding-bottom: 20px; margin-bottom: 30px;"><h2 style="color: #F8FAFC; font-size: 1.8rem; margin: 0; line-height: 1.6;">{current_memo['عنوان المذكرة']}</h2></div><div class="students-grid">{student_cards_html}</div><div style="margin-bottom: 40px; text-align: center;"><h3 style="color: #F8FAFC; margin-bottom: 15px;">نسبة الإنجاز الحالية</h3><div class="progress-container" style="height: 40px; border-radius: 20px;"><div class="progress-bar" style="width: {prog_int}%; font-size: 1.2rem; font-weight: bold; line-height: 28px;">{prog_int}%</div></div></div></div>"""
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
            st.markdown(f'<div class="kpi-card"><div class="kpi-value">{total}</div><div class="kpi-label">إجمالي المكرات</div></div><div class="kpi-card" style="border-color: #10B981;"><div class="kpi-value" style="color: #10B981;">{registered}</div><div class="kpi-label">المذكرات المسجلة</div></div><div class="kpi-card" style="border-color: #F59E0B;"><div class="kpi-value" style="color: #F59E0B;">{available}</div><div class="kpi-label">المذكرات المتاحة</div></div></div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            if is_exhausted: st.markdown('<div class="alert-card">لقد استنفذت العناوين الأربعة المخصصة لك.</div>', unsafe_allow_html=True)
            tab1, tab2, tab3, tab4 = st.tabs(["المذكرات المسجلة", "جدولة جلسة إشراف", "كلمات السر", "المذكرات المتاحة"])
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
                                        else: st.warning(f"⚠️ تم الحفظ لكن فشل الإرسال: {email_msg}")
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
                            st.markdown(f'''<div class="card" style="border-right:5px solid {color}; display:flex; justify-content:space-between; align-items:center;"><div><h3 style="margin:0; font-family:monospace; font-size:1.8rem; color:#FFD700;">{pwd}</h3><p style="margin:5px 0 0 0 0; color:#94A3B8;">الحالة: {status_txt}</p></div>''', unsafe_allow_html=True)
                else: st.info("لا توجد كلمات سر مسندة إليك.")
            
            with tab4:
                if is_exhausted: st.subheader("💡 المذكرات المقترحة")
                else: st.subheader("⏳ المذكرات المتاحة للتسجيل")
                avail = prof_memos[prof_memos["تم التسجيل"].astype(str).str.strip() != "نعم"]
                if not avail.empty:
                    for _, m in avail.iterrows():
                        st.markdown(f'''<div class="card" style="border-left:4px solid #64748B;"><h4>{m['رقم المذكرة']}</h4><p>{m['عنوان المذكرة']}</p><p style="color:#94A3B8;">تخصص: {m['التخصص']}</p></div>''', unsafe_allow_html=True)
                else: st.success("✅ جميع المذكرات مسجلة أو مقترحة!")

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
                else: 
                    st.session_state.admin_user = r; st.session_state.logged_in = True
                    st.query_params['ut'] = 'admin'
                    st.query_params['un'] = encode_str(st.session_state.admin_user)
                    st.rerun()
    else:
        col1, col2 = st.columns([4, 1])
        with col2:
            if st.button("خروج"): logout()
        st.header("📊 لوحة تحكم الإدارة")
        st_s = len(df_students); t_m = len(df_memos); r_m = len(df_memos[df_memos["تم التسجيل"].astype(str).str.strip() == "نعم"])
        a_m = t_m - r_m; t_p = len(df_prof_memos["الأستاذ"].unique())
        memo_col = df_students["رقم المذكرة"].astype(str).str.strip()
        reg_st = (memo_col != "").sum()
        unreg_st = (memo_col == "").sum()
        st.markdown('<div class="kpi-grid">', unsafe_allow_html=True)
        st.markdown(f'<div class="kpi-card"><div class="kpi-value">{st_s}</div><div class="kpi-label">الطلاب</div></div><div class="kpi-card"><div class="kpi-value">{t_p}</div><div class="kpi-label">الأساتذة</div></div><div class="kpi-card"><div class="kpi-value">{t_m}</div><div class="kpi-label">إجمالي المذكرات</div></div><div class="kpi-card" style="border-color: #10B981;"><div class="kpi-value" style="color: #10B981;">{r_m}</div><div class="kpi-label">مذكرات مسجلة</div></div><div class="kpi-card" style="border-color: #F59E0B;"><div class="kpi-value" style="color: #F59E0B;">{a_m}</div><div class="kpi-label">مذكرات متاحة</div></div><div class="kpi-card" style="border-color: #10B981;"><div class="kpi-value" style="color: #10B981;">{reg_st}</div><div class="kpi-label">طلاب مسجلين</div></div><div class="kpi-card" style="border-color: #F59E0B;"><div class="kpi-value" style="color: #F59E0B;">{unreg_st}</div><div class="kpi-label">طلاب غير مسجلين</div></div></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(["المذكرات", "الطلاب", "الأساتذة", "تقارير", "تحديث", "إدارة الطلبات", "📧 إرسال إيميلات"])
        
        with tab1:
            st.subheader("جدول المذكرات")
            f_status = st.selectbox("تصفية:", ["الكل", "مسجلة", "متاحة"])
            if f_status == "الكل": d_memos = df_memos
            elif f_status == "مسجلة": d_memos = df_memos[df_memos["تم التسجيل"].astype(str).str.strip() == "نعم"]
            else: d_memos = df_memos[df_memos["تم التسجيل"].astype(str).str.strip() != "نعم"]
            st.dataframe(d_memos, use_container_width=True, height=400)
        with tab2:
            st.subheader("قائمة الطلاب")
            q = st.text_input("بحث (لقب/الاسم):")
            if q:
                name_cols = [c for c in df_students.columns if 'اسم' in c.lower() or 'لقب' in c.lower() or 'إسم' in c.lower()]
                if name_cols:
                    mask = df_students[name_cols].astype(str).apply(lambda x: x.str.contains(q, case=False, na=False)).any(axis=1)
                    f_st = df_students[mask]
                else: f_st = df_students
                st.dataframe(f_st, use_container_width=True, height=400)
            else: st.dataframe(df_students, use_container_width=True, height=400)
        with tab3:
            st.subheader("توزيع الأساتذة")
            profs_list = sorted(df_memos["الأستاذ"].dropna().unique())
            sel_p = st.selectbox("اختر أستاذ:", ["الكل"] + profs_list)
            if sel_p != "الكل":
                if sel_p not in df_memos["الأستاذ"].values: st.error("بيانات الأساتذة غير متاحة")
                else: st.dataframe(df_memos[df_memos["الأستاذ"].astype(str).str.strip() == sel_p.strip()], use_container_width=True, height=400)
            else:
                if "الأستاذ" in df_memos.columns and "رقم المذكرة" in df_memos.columns and "تم التسجيل" in df_memos.columns:
                    s_df = df_memos.groupby("الأستاذ").agg(
                        total=("رقم المذكرة", "count"), 
                        registered=("تم التسجيل", lambda x: (x.astype(str).str.strip() == "نعم").sum())
                    ).reset_index()
                    s_df["المتاحة"] = s_df["total"] - s_df["registered"]
                    s_df = s_df.rename(columns={"total": "الإجمالي", "registered": "المسجلة"})
                    st.dataframe(s_df, use_container_width=True)
                else: st.error("بعض الأعمدة المطلوبة مفقودة في شيت المذكرات")
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
                if "الأستاذة" in df_prof_memos.columns:
                     prof_list.extend(df_prof_memos["الأستاذة"].astype(str).dropna().unique().tolist())
                prof_list = list(set([p for p in prof_list if p.strip() and p.strip().lower() != "nan"]))
                prof_list.sort()
                selected_prof = st.selectbox("اختر الأستاذ من القائمة:", prof_list, index=None)
                col_s1, col_s2 = st.columns([1, 3])
                with col_s1:
                    send_single_btn = st.button("إرسال الآن", type="secondary", use_container_width=True)
                if send_single_btn and selected_prof:
                    success, msg = send_welcome_email_to_one(selected_prof)
                    if success:
                        st.success(msg); st.balloons()
                    else: st.error(msg)
                elif send_single_btn and not selected_prof:
                    st.warning("⚠️ يرجى اختيار اسم أستاذ من القائمة.")
            elif send_mode == "🚀 إرسال لجميع الأساتذة":
                st.info("تقوم هذه الأداة بإرسال إيميل يحتوي على بيانات الدخول لجميع الأساتذة المسجلين في ملف 'PROF_MEMOS'.")
                st.write("عدد الأساتذة المستهدفين:", len(df_prof_memos))
                with st.expander("عرض قائمة الأساتذة المستهدفين"):
                     cols_available = df_prof_memos.columns.tolist()
                     target_cols = ["الأستاذ", "الأستاذة", "إسم المستخدم", "اسم المستخدم", "كلمة المرور", "البريد الإلكتروني", "الإيميل", "email", "Email"]
                     cols_to_display = [col for col in target_cols if col in cols_available]
                     if not cols_to_display: cols_to_display = cols_available[:3]
                     st.dataframe(df_prof_memos[cols_to_display].head(20))
                col_send, col_space = st.columns([1, 3])
                with col_send:
                    if st.button("🚀 بدء عملية الإلحاق للجميع", type="primary"):
                        sent, failed, logs = send_welcome_emails_to_all_profs()
                        st.markdown("---")
                        st.success(f"تم الانتهاء! تم الإلف لجائزال {sent} أستاذ.")
                        if failed >0: st.error(f"فشل الإرسال لـ {failed} أستاذ.")
                        with st.expander("سجل العمليات (Logs)", expanded=True):
                            for log in logs: st.text(log)

st.markdown("---")
st.markdown('<div style="text-align:center; color:#64748B; font-size:12px; padding:20px;">  إشراف مسؤول الميدان البروفيسور لخضر رفاف © </div>', unsafe_allow_html=True)