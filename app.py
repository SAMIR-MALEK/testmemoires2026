import streamlit as st
from datetime import datetime
import pandas as pd
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ---------------- إعداد Logging ----------------
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ---------------- إعداد الصفحة ----------------
st.set_page_config(page_title="تسجيل مذكرة ماستر", page_icon="🎓", layout="centered")

# ---------------- CSS ----------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
html, body, [class*="css"] { font-family: 'Cairo', sans-serif !important; }
.main { background-color: #0A1B2C; color: #ffffff; }
.block-container { padding: 2rem; background-color: #1A2A3D; border-radius: 12px; max-width: 750px; margin:auto;}
label, h1, h2, h3, h4, h5, h6, p, span, .stTextInput label { color:#ffffff !important; }
button { background-color:#256D85 !important; color:white !important; border:none !important; padding:10px 20px !important; border-radius:6px !important; }
button:hover { background-color:#2C89A0 !important; }
.message { font-size:18px; font-weight:bold; text-align:center; margin:10px 0; color:#FFFFFF;}
.logout-btn { background-color:#8B0000 !important; }
.logout-btn:hover { background-color:#A52A2A !important; }
.success-msg { color: #FFFFFF; padding: 15px; margin: 10px 0; }
.error-msg { color: #FFFFFF; padding: 15px; margin: 10px 0; }
.info-msg { color: #FFFFFF; padding: 15px; margin: 10px 0; }
.memo-item { 
    background-color: #2C3E50; 
    padding: 15px; 
    margin: 10px 0; 
    border-radius: 8px; 
    border-left: 4px solid #256D85;
}
.memo-number { 
    color: #FFD700; 
    font-size: 20px; 
    font-weight: bold; 
    margin-bottom: 5px;
}
.memo-title { 
    color: #FFFFFF; 
    font-size: 16px; 
    line-height: 1.5;
}
</style>
""", unsafe_allow_html=True)

# ---------------- Google Sheets ----------------
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
info = st.secrets["service_account"]
credentials = Credentials.from_service_account_info(info, scopes=SCOPES)
sheets_service = build('sheets', 'v4', credentials=credentials)

STUDENTS_SHEET_ID = "1CHQyE1GJHlmynvaj2ez89Lf_S7Y3GU8T9rrl75rnF5c"
MEMOS_SHEET_ID = "1oV2RYEWejDaRpTrKhecB230SgEo6dDwwLzUjW6VPw6o"
PROF_MEMOS_SHEET_ID = "15u6N7XLFUKvTEmNtUNKVytpqVAQLaL19cAM8xZB_u3A"

STUDENTS_RANGE = "Feuille 1!A1:L1000"
MEMOS_RANGE = "Feuille 1!A1:N1000"
PROF_MEMOS_RANGE = "Feuille 1!A1:L1000"

# ---------------- إعداد البريد الإلكتروني ----------------
# استخدم secrets لتخزين بيانات الإيميل
try:
    EMAIL_ADDRESS = st.secrets.get("email_address", "")
    EMAIL_PASSWORD = st.secrets.get("email_password", "")
    EMAIL_ENABLED = bool(EMAIL_ADDRESS and EMAIL_PASSWORD)
except:
    EMAIL_ENABLED = False
    logger.warning("البريد الإلكتروني غير مفعّل - تأكد من إضافة email_address و email_password في secrets")

# ---------------- دوال مساعدة ----------------
def col_letter(n):
    """تحويل رقم العمود إلى حرف (محسّن)"""
    result = ""
    while n > 0:
        n -= 1
        result = chr(65 + (n % 26)) + result
        n //= 26
    return result

def sanitize_input(text):
    """تنقية المدخلات من الأحرف الخطرة"""
    if not text:
        return ""
    dangerous_chars = ['<', '>', '"', "'", ';', '&', '|', '`']
    cleaned = str(text).strip()
    for char in dangerous_chars:
        cleaned = cleaned.replace(char, '')
    return cleaned

def validate_username(username):
    """التحقق من صحة اسم المستخدم"""
    username = sanitize_input(username)
    if not username:
        return False, "⚠️ اسم المستخدم فارغ"
    return True, username

def validate_note_number(note_number):
    """التحقق من صحة رقم المذكرة"""
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
            logger.error("لا توجد بيانات في صفحة الطلاب")
            return pd.DataFrame()
        df = pd.DataFrame(values[1:], columns=values[0])
        logger.info(f"تم تحميل {len(df)} طالب")
        return df
    except Exception as e:
        logger.error(f"خطأ في تحميل بيانات الطلاب: {str(e)}")
        st.error(f"❌ خطأ في تحميل بيانات الطلاب: {str(e)}")
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
            logger.error("لا توجد بيانات في صفحة المذكرات")
            return pd.DataFrame()
        df = pd.DataFrame(values[1:], columns=values[0])
        logger.info(f"تم تحميل {len(df)} مذكرة")
        return df
    except Exception as e:
        logger.error(f"خطأ في تحميل بيانات المذكرات: {str(e)}")
        st.error(f"❌ خطأ في تحميل بيانات المذكرات: {str(e)}")
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
            logger.error("لا توجد بيانات في صفحة المذكرات - الأساتذة")
            return pd.DataFrame()
        df = pd.DataFrame(values[1:], columns=values[0])
        logger.info(f"تم تحميل {len(df)} مذكرة للأساتذة")
        return df
    except Exception as e:
        logger.error(f"خطأ في تحميل بيانات مذكرات الأساتذة: {str(e)}")
        st.error(f"❌ خطأ في تحميل بيانات مذكرات الأساتذة: {str(e)}")
        return pd.DataFrame()

def clear_cache_and_reload():
    """مسح الكاش وإعادة تحميل البيانات"""
    try:
        st.cache_data.clear()
        logger.info("تم مسح الكاش بنجاح")
        return True
    except Exception as e:
        logger.error(f"خطأ في مسح الكاش: {str(e)}")
        return False

# ---------------- دالة إرسال البريد الإلكتروني ----------------


def send_email_to_professor(prof_email, prof_name, memo_number, memo_title, 
                            student1_name, student2_name, used_password, 
                            remaining_passwords):
    """
    إرسال بريد إلكتروني للأستاذ مع تفاصيل المذكرة وكلمات السر.
    يدعم Gmail / GSuite باستخدام App Password.
    """
    if not EMAIL_ENABLED:
        logger.warning("البريد الإلكتروني غير مفعل")
        return False, "البريد الإلكتروني غير مفعل"
    
    if not prof_email or '@' not in prof_email:
        logger.warning(f"بريد إلكتروني غير صالح للأستاذ: {prof_name}")
        return False, "البريد الإلكتروني غير صالح"
    
    try:
        # إعداد الرسالة بصيغة HTML
        students_info = f"<li>{student1_name}</li>"
        if student2_name:
            students_info += f"<li>{student2_name}</li>"

        remaining_pass_html = ""
        if remaining_passwords:
            remaining_pass_html = "".join([f"<li>{pwd}</li>" for pwd in remaining_passwords])
        else:
            remaining_pass_html = "<li>لا توجد كلمات سر متبقية</li>"

        html_content = f"""
        <html dir="rtl">
        <body>
            <h2>🎓 تأكيد تسجيل مذكرة ماستر</h2>
            <p>السلام عليكم الأستاذ(ة) <strong>{prof_name}</strong></p>
            <p>تم تسجيل مذكرة جديدة تحت إشرافكم:</p>
            <ul>
                <li><strong>رقم المذكرة:</strong> {memo_number}</li>
                <li><strong>عنوان المذكرة:</strong> {memo_title}</li>
                {students_info}
                <li><strong>كلمة السر المستخدمة:</strong> {used_password}</li>
            </ul>
            <h3>🔐 كلمات السر المتبقية:</h3>
            <ul>{remaining_pass_html}</ul>
        </body>
        </html>
        """

        # إنشاء الرسالة
        msg = MIMEMultipart("alternative")
        msg['Subject'] = f"تأكيد تسجيل مذكرة - {memo_number}"
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = prof_email
        msg.attach(MIMEText(html_content, "html", "utf-8"))

        # إرسال البريد عبر Gmail SMTP
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)

        logger.info(f"تم إرسال البريد للأستاذ {prof_name} على {prof_email}")
        return True, "تم إرسال البريد الإلكتروني بنجاح"

    except Exception as e:
        logger.error(f"خطأ في إرسال البريد الإلكتروني: {str(e)}")
        return False, f"فشل إرسال البريد: {str(e)}"





# ---------------- التحقق ----------------
def verify_student(username, password, df_students):
    """التحقق من بيانات الطالب"""
    valid, result = validate_username(username)
    if not valid:
        logger.warning(f"محاولة دخول بـ username غير صالح: {username}")
        return False, result
    
    username = result
    password = sanitize_input(password)
    
    if df_students.empty:
        return False, "❌ خطأ في تحميل بيانات الطلاب"
    
    student = df_students[df_students["اسم المستخدم"].astype(str).str.strip() == username]
    
    if student.empty:
        logger.warning(f"محاولة دخول بـ username غير موجود: {username}")
        return False, "❌ اسم المستخدم غير موجود"
    
    if student.iloc[0]["كلمة السر"].strip() != password:
        logger.warning(f"محاولة دخول بكلمة سر خاطئة لـ: {username}")
        return False, "❌ كلمة السر غير صحيحة"
    
    logger.info(f"تسجيل دخول ناجح: {username}")
    return True, student.iloc[0]

def verify_students_batch(students_data, df_students):
    """التحقق من بيانات عدة طلاب دفعة واحدة"""
    verified_students = []
    
    if df_students.empty:
        return False, "❌ خطأ في تحميل بيانات الطلاب"
    
    for username, password in students_data:
        if not username or not username.strip():
            continue
            
        valid, student = verify_student(username, password, df_students)
        if not valid:
            return False, student
        verified_students.append(student)
    
    if not verified_students:
        return False, "❌ لم يتم إدخال بيانات صحيحة"
    
    return True, verified_students

def verify_professor_password(note_number, prof_password, df_memos, df_prof_memos):
    """التحقق من كلمة سر الأستاذ (محسّن)"""
    valid, result = validate_note_number(note_number)
    if not valid:
        return False, None, result
    
    note_number = result
    prof_password = sanitize_input(prof_password)
    
    if df_memos.empty or df_prof_memos.empty:
        return False, None, "❌ خطأ في تحميل البيانات"
    
    df_memos['رقم المذكرة'] = df_memos['رقم المذكرة'].astype(str).str.strip()
    memo_row = df_memos[df_memos['رقم المذكرة'] == note_number]
    
    if memo_row.empty:
        logger.warning(f"محاولة تسجيل برقم مذكرة غير موجود: {note_number}")
        return False, None, "❌ رقم المذكرة غير موجود"
    
    memo_row = memo_row.iloc[0]
    
    registered_status = str(memo_row.get("تم التسجيل", "")).strip()
    if registered_status == "نعم":
        logger.warning(f"محاولة تسجيل مذكرة مسجلة مسبقاً: {note_number}")
        return False, None, "❌ هذه المذكرة مسجلة مسبقاً لطالب آخر"
    
    prof_name = str(memo_row.get("الأستاذ", "")).strip()
    if not prof_name:
        return False, None, "❌ خطأ في بيانات المذكرة"
    
    df_prof_memos['الأستاذ'] = df_prof_memos['الأستاذ'].astype(str).str.strip()
    df_prof_memos['كلمة سر التسجيل'] = df_prof_memos['كلمة سر التسجيل'].astype(str).str.strip()
    
    prof_row = df_prof_memos[
        (df_prof_memos['الأستاذ'] == prof_name) &
        (df_prof_memos['كلمة سر التسجيل'] == prof_password)
    ]
    
    if prof_row.empty:
        logger.warning(f"كلمة سر مشرف خاطئة للمذكرة: {note_number}")
        return False, None, "❌ كلمة سر المشرف غير صحيحة"
    
    prof_registered = str(prof_row.iloc[0].get("تم التسجيل", "")).strip()
    if prof_registered == "نعم":
        logger.warning(f"محاولة استخدام كلمة سر مستخدمة مسبقاً")
        return False, None, "❌ هذه كلمة السر تم استعمالها مسبقًا"
    
    logger.info(f"تحقق ناجح من كلمة سر المشرف للمذكرة: {note_number}")
    return True, prof_row.iloc[0], None

# ---------------- تحديث المذكرات ----------------
def update_registration(note_number, student1, student2=None):
    """تحديث تسجيل المذكرة في جميع الجداول (محسّن)"""
    try:
        st.cache_data.clear()
        
        df_memos = load_memos()
        df_prof_memos = load_prof_memos()
        df_students = load_students()
        
        if df_memos.empty or df_prof_memos.empty or df_students.empty:
            raise Exception("فشل تحميل البيانات")
        
        note_number_clean = str(note_number).strip()
        df_memos['رقم المذكرة'] = df_memos['رقم المذكرة'].astype(str).str.strip()
        
        memo_match = df_memos[df_memos['رقم المذكرة'] == note_number_clean]
        if memo_match.empty:
            raise Exception("لم يتم العثور على المذكرة")
        
        memo_info = memo_match.iloc[0]
        prof_name = str(memo_info['الأستاذ']).strip()
        memo_title = str(memo_info.get('عنوان المذكرة', '')).strip()
        
        df_prof_memos['الأستاذ'] = df_prof_memos['الأستاذ'].astype(str).str.strip()
        df_prof_memos['تم التسجيل'] = df_prof_memos['تم التسجيل'].astype(str).str.strip()
        
        prof_match = df_prof_memos[
            (df_prof_memos['الأستاذ'] == prof_name) &
            (df_prof_memos['تم التسجيل'] != "نعم")
        ]
        
        if prof_match.empty:
            raise Exception("لم يتم العثور على بيانات الأستاذ")
        
        # الحصول على كلمة السر المستخدمة
        used_password = str(st.session_state.prof_password).strip()
        
        # الحصول على كلمات السر المتبقية للأستاذ
        remaining_passwords_df = df_prof_memos[
            (df_prof_memos['الأستاذ'] == prof_name) &
            (df_prof_memos['تم التسجيل'] != "نعم") &
            (df_prof_memos['كلمة سر التسجيل'].astype(str).str.strip() != used_password)
        ]
        remaining_passwords = remaining_passwords_df['كلمة سر التسجيل'].astype(str).str.strip().tolist()
        
        # الحصول على الإيميل
        prof_email = str(prof_match.iloc[0].get('الإيميل', '')).strip()
        
        prof_row_idx = prof_match.index[0] + 2
        col_names = df_prof_memos.columns.tolist()
        
        student1_name = f"{student1['اللقب']} {student1['الإسم']}"
        
        updates = []
        for col_name, value in [
            ('الطالب الأول', student1_name),
            ('تم التسجيل', 'نعم'),
            ('تاريخ التسجيل', datetime.now().strftime('%Y-%m-%d %H:%M')),
            ('رقم المذكرة', note_number_clean)
        ]:
            if col_name in col_names:
                col_idx = col_names.index(col_name) + 1
                updates.append({
                    "range": f"Feuille 1!{col_letter(col_idx)}{prof_row_idx}",
                    "values": [[value]]
                })
        
        student2_name = None
        if student2 is not None and 'الطالب الثاني' in col_names:
            student2_name = f"{student2['اللقب']} {student2['الإسم']}"
            col_idx = col_names.index('الطالب الثاني') + 1
            updates.append({
                "range": f"Feuille 1!{col_letter(col_idx)}{prof_row_idx}",
                "values": [[student2_name]]
            })
        
        if updates:
            sheets_service.spreadsheets().values().batchUpdate(
                spreadsheetId=PROF_MEMOS_SHEET_ID,
                body={"valueInputOption": "USER_ENTERED", "data": updates}
            ).execute()
            logger.info(f"تم تحديث شيت الأساتذة للمذكرة: {note_number}")
        
        memo_row_idx = df_memos[df_memos['رقم المذكرة'] == note_number_clean].index[0] + 2
        memo_cols = df_memos.columns.tolist()
        
        updates2 = []
        for col_name, value in [
            ('الطالب الأول', student1_name),
            ('تم التسجيل', 'نعم'),
            ('تاريخ التسجيل', datetime.now().strftime('%Y-%m-%d %H:%M'))
        ]:
            if col_name in memo_cols:
                col_idx = memo_cols.index(col_name) + 1
                updates2.append({
                    "range": f"Feuille 1!{col_letter(col_idx)}{memo_row_idx}",
                    "values": [[value]]
                })
        
        if student2 is not None and 'الطالب الثاني' in memo_cols:
            col_idx = memo_cols.index('الطالب الثاني') + 1
            updates2.append({
                "range": f"Feuille 1!{col_letter(col_idx)}{memo_row_idx}",
                "values": [[student2_name]]
            })
        
        if updates2:
            sheets_service.spreadsheets().values().batchUpdate(
                spreadsheetId=MEMOS_SHEET_ID,
                body={"valueInputOption": "USER_ENTERED", "data": updates2}
            ).execute()
            logger.info(f"تم تحديث شيت المذكرات للمذكرة: {note_number}")
        
        students_cols = df_students.columns.tolist()
        if 'رقم المذكرة' not in students_cols:
            raise Exception("عمود 'رقم المذكرة' غير موجود")
        
        df_students['اسم المستخدم'] = df_students['اسم المستخدم'].astype(str).str.strip()
        
        student1_match = df_students[df_students['اسم المستخدم'] == student1['اسم المستخدم'].strip()]
        if not student1_match.empty:
            student1_row_idx = student1_match.index[0] + 2
            col_idx = students_cols.index('رقم المذكرة') + 1
            
            sheets_service.spreadsheets().values().update(
                spreadsheetId=STUDENTS_SHEET_ID,
                range=f"Feuille 1!{col_letter(col_idx)}{student1_row_idx}",
                valueInputOption="USER_ENTERED",
                body={"values": [[note_number_clean]]}
            ).execute()
            logger.info(f"تم تحديث بيانات الطالب الأول")
        
        if student2 is not None:
            student2_match = df_students[df_students['اسم المستخدم'] == student2['اسم المستخدم'].strip()]
            if not student2_match.empty:
                student2_row_idx = student2_match.index[0] + 2
                
                sheets_service.spreadsheets().values().update(
                    spreadsheetId=STUDENTS_SHEET_ID,
                    range=f"Feuille 1!{col_letter(col_idx)}{student2_row_idx}",
                    valueInputOption="USER_ENTERED",
                    body={"values": [[note_number_clean]]}
                ).execute()
                logger.info(f"تم تحديث بيانات الطالب الثاني")
        
        st.cache_data.clear()
        
        # إرسال البريد الإلكتروني للأستاذ


# إرسال البريد الإلكتروني للأستاذ
if prof_email and EMAIL_ENABLED:
    email_success, email_msg = send_email_to_professor(
        prof_email=prof_email,
        prof_name=prof_name,
        memo_number=note_number_clean,
        memo_title=memo_title,
        student1_name=student1_name,
        student2_name=student2_name,
        used_password=used_password,
        remaining_passwords=remaining_passwords
    )
    if email_success:
        logger.info(f"تم إرسال إيميل للأستاذ {prof_name}")
    else:
        logger.warning(f"فشل إرسال الإيميل: {email_msg}")



# ---------------- Session State ----------------
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.student1 = None
    st.session_state.student2 = None
    st.session_state.memo_type = "فردية"
    st.session_state.mode = "register"
    st.session_state.note_number = ""
    st.session_state.prof_password = ""
    st.session_state.show_confirmation = False

def logout():
    """تسجيل الخروج"""
    username1 = 'unknown'
    username2 = None
    
    if st.session_state.student1 is not None:
        username1 = st.session_state.student1.get('اسم المستخدم', 'unknown')
    
    if st.session_state.student2 is not None:
        username2 = st.session_state.student2.get('اسم المستخدم', 'unknown')
    
    if username2:
        logger.info(f"تسجيل خروج: {username1} و {username2}")
    else:
        logger.info(f"تسجيل خروج: {username1}")
    
    st.session_state.logged_in = False
    st.session_state.student1 = None
    st.session_state.student2 = None
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

# ---------------- واجهة الدخول ----------------
st.markdown('<div class="block-container">', unsafe_allow_html=True)
st.markdown("<h5 style='text-align:center;'>جامعة محمد البشير الإبراهيمي</h5>", unsafe_allow_html=True)
st.markdown("<h6 style='text-align:center;'>كلية الحقوق والعلوم السياسية</h6>", unsafe_allow_html=True)
st.markdown("""
    <div style="text-align:center; margin:20px 0;">
        <img src="https://raw.githubusercontent.com/SAMIR-MALEK/memoire-depot-2026/main/LOGO2.png" width="100">
    </div>
""", unsafe_allow_html=True)
st.markdown("<h4 style='text-align:center; color:#FFD700;'>منصة تسجيل مذكرة الماستر</h4>", unsafe_allow_html=True)

# ---------------- عملية تسجيل الدخول ----------------
if not st.session_state.logged_in:
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
                st.markdown('<div class="error-msg">⚠️ يرجى إدخال بيانات الطالب الثاني كاملة</div>', unsafe_allow_html=True)
                logger.warning("محاولة تسجيل ثنائي بدون بيانات الطالب الثاني")
                st.stop()
            
            if username1.strip().lower() == username2.strip().lower():
                st.markdown('<div class="error-msg">❌ لا يمكن أن يكون الطالب الأول والثاني نفس الشخص!</div>', unsafe_allow_html=True)
                logger.warning(f"محاولة تسجيل ثنائي بنفس اسم المستخدم: {username1}")
                st.stop()
        
        students_data = [(username1, password1)]
        if st.session_state.memo_type == "ثنائية" and username2:
            students_data.append((username2, password2))
        
        valid, result = verify_students_batch(students_data, df_students)
        
        if not valid:
            st.markdown(f'<div class="error-msg">{result}</div>', unsafe_allow_html=True)
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
                    st.markdown('<div class="error-msg">❌ لا يمكن التسجيل الثنائي. الطالبان في تخصصين مختلفين</div>', unsafe_allow_html=True)
                    logger.warning(f"محاولة تسجيل ثنائي بتخصصات مختلفة")
                    st.session_state.logged_in = False
                    st.session_state.student1 = None
                    st.session_state.student2 = None
                    st.stop()
                
                if (s1_note and not s2_note) or (not s1_note and s2_note):
                    registered_student = None
                    if s1_note:
                        registered_student = f"{st.session_state.student1['اللقب']} {st.session_state.student1['الإسم']}"
                    else:
                        registered_student = f"{st.session_state.student2['اللقب']} {st.session_state.student2['الإسم']}"
                    
                    st.markdown(f'<div class="error-msg">❌ أحد الطالبين مسجل مسبقاً: {registered_student}<br>لا يمكن المتابعة</div>', unsafe_allow_html=True)
                    logger.warning(f"محاولة تسجيل ثنائي مع طالب مسجل")
                    st.session_state.logged_in = False
                    st.session_state.student1 = None
                    st.session_state.student2 = None
                    st.stop()
                
                if s1_note and s2_note and s1_note != s2_note:
                    st.markdown(f'<div class="error-msg">❌ الطالبان مسجلان في مذكرتين مختلفتين</div>', unsafe_allow_html=True)
                    logger.warning(f"محاولة دخول ثنائي بمذكرتين مختلفتين")
                    st.session_state.logged_in = False
                    st.session_state.student1 = None
                    st.session_state.student2 = None
                    st.stop()
                
                if s1_note and s2_note and s1_note == s2_note:
                    st.session_state.mode = "view"
                    logger.info(f"دخول ثنائي لمذكرة مسجلة")
                    st.session_state.logged_in = True
                    st.rerun()
            
            if st.session_state.memo_type == "فردية":
                fardiya_value = str(st.session_state.student1.get('فردية', '')).strip()
                if fardiya_value not in ["1", "نعم"]:
                    st.markdown('<div class="error-msg">❌ لا يمكنك تسجيل مذكرة فردية</div>', unsafe_allow_html=True)
                    logger.warning(f"محاولة تسجيل فردي ممنوع")
                    st.stop()
            
            note_number = str(st.session_state.student1.get('رقم المذكرة', '')).strip()
            
            if note_number:
                st.session_state.mode = "view"
                logger.info(f"الطالب مسجل مسبقاً")
            else:
                st.session_state.mode = "register"
            
            st.session_state.logged_in = True
            st.rerun()

st.markdown('</div>', unsafe_allow_html=True)

# ---------------- فضاء الطالب ----------------
if st.session_state.logged_in:
    s1 = st.session_state.student1
    s2 = st.session_state.student2
    
    st.markdown('<div class="block-container">', unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("<h2 style='text-align:center;'>📘 فضاء الطالب</h2>", unsafe_allow_html=True)
    with col2:
        if st.button("🚪 خروج", key="logout_btn"):
            logout()
    
    st.markdown(f"👤 الطالب الأول: **{s1['اللقب']} {s1['الإسم']}**")
    st.markdown(f"🎓 التخصص: **{s1['التخصص']}**")
    
    if s2 is not None:
        st.markdown(f"👤 الطالب الثاني: **{s2['اللقب']} {s2['الإسم']}**")

    if st.session_state.mode == "view":
        note_number = str(s1.get('رقم المذكرة', '')).strip()
        memo_info = df_memos[df_memos["رقم المذكرة"].astype(str).str.strip() == note_number]
        
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
            
            st.markdown('<div class="info-msg">', unsafe_allow_html=True)
            st.markdown("ℹ️ **ملاحظة:** لا يمكن تسجيل مذكرة أخرى.")
            st.markdown('</div>', unsafe_allow_html=True)

    elif st.session_state.mode == "register":
        st.markdown('<div class="info-msg">', unsafe_allow_html=True)
        st.markdown("### 📝 تسجيل مذكرة جديدة")
        st.markdown("⚠️ اختر الأستاذ المشرف والمذكرة التي ترغب في تسجيلها")
        st.markdown('</div>', unsafe_allow_html=True)
        
        all_profs = sorted(df_memos["الأستاذ"].dropna().unique())
        selected_prof = st.selectbox("🧑‍🏫 اختر الأستاذ المشرف:", [""] + all_profs)
        
        if selected_prof:
            student_specialty = s1["التخصص"]
            available_memos_df = df_memos[
                (df_memos["الأستاذ"].astype(str).str.strip() == selected_prof.strip()) &
                (df_memos["التخصص"].astype(str).str.strip() == student_specialty.strip()) &
                (df_memos["تم التسجيل"].astype(str).str.strip() != "نعم")
            ][["رقم المذكرة", "عنوان المذكرة"]]
            
       

    



#بداية    

            if not available_memos_df.empty:
                st.markdown(f'<p style="color:#4CAF50; font-weight:bold;">✅ المذكرات المتاحة في تخصصك ({student_specialty}):</p>', unsafe_allow_html=True)
                
                # عرض المذكرات بتنسيق محسّن مع أرقامها الفعلية
                for idx, row in available_memos_df.iterrows():
                    st.markdown(f"""
                        <div class="memo-item">
                            <div class="memo-number">{row['رقم المذكرة']}. {row['عنوان المذكرة']}</div>
                        </div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown('<div class="error-msg">❌ لا توجد مذكرات متاحة لهذا الأستاذ في تخصصك.</div>', unsafe_allow_html=True)



#نهاية
        

        
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        with col1:
            st.session_state.note_number = st.text_input(
                "📄 رقم المذكرة", 
                value=st.session_state.note_number,
                max_chars=20
            )
        with col2:
            st.session_state.prof_password = st.text_input(
                "🔑 كلمة سر المشرف", 
                type="password",
                max_chars=50
            )

        if not st.session_state.show_confirmation:
            if st.button("📝 المتابعة للتأكيد", type="primary", use_container_width=True):
                if not st.session_state.note_number or not st.session_state.prof_password:
                    st.markdown('<div class="error-msg">⚠️ يرجى إدخال رقم المذكرة وكلمة سر المشرف</div>', unsafe_allow_html=True)
                else:
                    st.session_state.show_confirmation = True
                    st.rerun()
        else:
            st.markdown('<div class="info-msg">', unsafe_allow_html=True)
            st.markdown("### ⚠️ تأكيد التسجيل")
            st.markdown(f"**رقم المذكرة:** {st.session_state.note_number}")
            st.markdown(f"**الطالب الأول:** {s1['اللقب']} {s1['الإسم']}")
            if s2 is not None:
                st.markdown(f"**الطالب الثاني:** {s2['اللقب']} {s2['الإسم']}")
            st.markdown("**⚠️ تنبيه:** بعد التأكيد، لن تتمكن من تغيير المذكرة!")
            st.markdown('</div>', unsafe_allow_html=True)
            
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
                        st.markdown(f'<div class="error-msg">{error_msg}</div>', unsafe_allow_html=True)
                        st.session_state.show_confirmation = False
                    else:
                        with st.spinner('⏳ جاري تسجيل المذكرة...'):
                            success, message = update_registration(
                                st.session_state.note_number, 
                                s1, 
                                s2
                            )
                        
                        if success:
                            st.markdown(f'<div class="success-msg">{message}</div>', unsafe_allow_html=True)
                            st.balloons()
                            st.session_state.mode = "view"
                            st.session_state.show_confirmation = False
                            
                            import time
                            time.sleep(2)
                            st.rerun()
                        else:
                            st.markdown(f'<div class="error-msg">{message}</div>', unsafe_allow_html=True)
                            st.session_state.show_confirmation = False
            
            with col2:
                if st.button("❌ إلغاء", use_container_width=True):
                    st.session_state.show_confirmation = False
                    st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("---")
st.markdown("""
    <div style='text-align:center; color:#888; font-size:12px; padding:20px;'>
        <p>© 2026 جامعة محمد البشير الإبراهيمي - كلية الحقوق والعلوم السياسية</p>
        <p>للدعم الفني، يرجى الاتصال بالإدارة</p>
    </div>
""", unsafe_allow_html=True)
