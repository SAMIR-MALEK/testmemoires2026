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
MEMOS_RANGE = "Feuille 1!A1:N1000"
PROF_MEMOS_RANGE = "Feuille 1!A1:L1000"

# ---------------- Email Configuration ----------------
EMAIL_SENDER = "domaine.dsp@univ-bba.dz"
EMAIL_PASSWORD = "oevruyiztgikwzah"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# كلمة سر الإدارة
ADMIN_PASSWORD = "admin2026"

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
    st.session_state.admin_mode = False

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
            spreadsheetId=STUDENTS_SHEET_ID, range=STUDENTS_RANGE
        ).execute()
        values = result.get('values', [])
        if not values:
            return pd.DataFrame()
        df = pd.DataFrame(values[1:], columns=values[0])
        logger.info(f"تم تحميل {len(df)} طالب")
        return df
    except Exception as e:
        logger.error(f"خطأ في تحميل بيانات الطلاب: {str(e)}")
        return pd.DataFrame()

@st.cache_data(ttl=60)
def load_memos():
    try:
        result = sheets_service.spreadsheets().values().get(
            spreadsheetId=MEMOS_SHEET_ID, range=MEMOS_RANGE
        ).execute()
        values = result.get('values', [])
        if not values:
            return pd.DataFrame()
        df = pd.DataFrame(values[1:], columns=values[0])
        logger.info(f"تم تحميل {len(df)} مذكرة")
        return df
    except Exception as e:
        logger.error(f"خطأ في تحميل بيانات المذكرات: {str(e)}")
        return pd.DataFrame()

@st.cache_data(ttl=60)
def load_prof_memos():
    try:
        result = sheets_service.spreadsheets().values().get(
            spreadsheetId=PROF_MEMOS_SHEET_ID, range=PROF_MEMOS_RANGE
        ).execute()
        values = result.get('values', [])
        if not values:
            return pd.DataFrame()
        df = pd.DataFrame(values[1:], columns=values[0])
        logger.info(f"تم تحميل {len(df)} مذكرة للأساتذة")
        return df
    except Exception as e:
        logger.error(f"خطأ في تحميل بيانات مذكرات الأساتذة: {str(e)}")
        return pd.DataFrame()

def clear_cache_and_reload():
    st.cache_data.clear()
    logger.info("تم مسح السجلات")

# ---------------- إرسال البريد الإلكتروني ----------------
def send_bulk_emails_to_all_professors():
    """إرسال إيميلات لجميع الأساتذة"""
    try:
        df_prof_memos = load_prof_memos()
        all_professors = df_prof_memos["الأستاذ"].dropna().unique()
        
        success_count = 0
        failed_count = 0
        results = []
        
        for prof_name in all_professors:
            prof_name = str(prof_name).strip()
            prof_memos = df_prof_memos[df_prof_memos["الأستاذ"].astype(str).str.strip() == prof_name]
            
            if prof_memos.empty:
                continue
            
            prof_email = str(prof_memos.iloc[0].get("الإيميل", "")).strip()
            
            if not prof_email or "@" not in prof_email:
                results.append(f"❌ {prof_name}: لا يوجد إيميل صالح")
                failed_count += 1
                continue
            
            total_memos = len(prof_memos)
            registered_memos = len(prof_memos[prof_memos["تم التسجيل"].astype(str).str.strip() == "نعم"])
            remaining_memos = total_memos - registered_memos
            
            used_passwords = []
            for idx, row in prof_memos.iterrows():
                password = str(row.get("كلمة سر التسجيل", "")).strip()
                memo_num = str(row.get("رقم المذكرة", "")).strip()
                if password:
                    if str(row.get("تم التسجيل", "")).strip() == "نعم":
                        used_passwords.append(f"✅ {password} - المذكرة: {memo_num}")
                    else:
                        used_passwords.append(f"⏳ {password} - متاحة")
            
            passwords_list = "\n".join(used_passwords) if used_passwords else "لا توجد كلمات سر مسجلة"
            
            email_body = f"""
<html dir="rtl">
<head>
    <style>
        body {{ font-family: 'Arial', sans-serif; background-color: #f4f4f4; padding: 20px; }}
        .container {{ background-color: #ffffff; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); max-width: 600px; margin: auto; }}
        .header {{ background-color: #256D85; color: white; padding: 20px; border-radius: 8px; text-align: center; margin-bottom: 20px; }}
        .header h2 {{ margin: 0; }}
        .content {{ line-height: 1.8; color: #333; }}
        .info-box {{ background-color: #f8f9fa; padding: 15px; border-right: 4px solid #256D85; margin: 15px 0; }}
        .stats-box {{ background-color: #e8f4f8; padding: 15px; border-radius: 8px; margin: 15px 0; }}
        .footer {{ text-align: center; color: #888; font-size: 12px; margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; }}
        .highlight {{ color: #256D85; font-weight: bold; }}
        ul {{ list-style: none; padding: 0; }}
        li {{ padding: 5px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>📊 تقرير حالة المذكرات</h2>
        </div>
        
        <div class="content">
            <p>تحية طيبة وبعد : الأستاذ(ة) الفاضل(ة) <span class="highlight">{prof_name}</span>،</p>
            
            <p>نحيطكم علماً بحالة المذكرات المسجلة تحت إشرافكم:</p>
            
            <div class="stats-box">
                <h3 style="color: #256D85; margin-top: 0;">📊 إحصائيات مذكراتك:</h3>
                <ul>
                    <li>📝 <strong>إجمالي المذكرات:</strong> {total_memos}</li>
                    <li>✅ <strong>المذكرات المسجلة:</strong> {registered_memos}</li>
                    <li>⏳ <strong>المذكرات المتبقية:</strong> {remaining_memos}</li>
                </ul>
            </div>
            
            <div class="info-box">
                <h3 style="color: #256D85; margin-top: 0;">🔑 كلمات السر:</h3>
                <ul style="white-space: pre-line;">{passwords_list}</ul>
            </div>
            
            <p style="margin-top: 20px; color: #666;">للاستفسار أو الدعم، يرجى التواصل مع السيد مسؤول الميدان الدكتور رفاف لخضر.</p>
        </div>
        
        <div class="footer">
            <p>© 2026 جامعة محمد البشير الإبراهيمي</p>
            <p>كلية الحقوق والعلوم السياسية</p>
        </div>
    </div>
</body>
</html>
"""
            
            try:
                msg = MIMEMultipart('alternative')
                msg['From'] = EMAIL_SENDER
                msg['To'] = prof_email
                msg['Subject'] = f"📊 تقرير حالة المذكرات - {prof_name}"
                
                html_part = MIMEText(email_body, 'html', 'utf-8')
                msg.attach(html_part)
                
                with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                    server.starttls()
                    server.login(EMAIL_SENDER, EMAIL_PASSWORD)
                    server.send_message(msg)
                
                results.append(f"✅ {prof_name}: تم الإرسال بنجاح")
                success_count += 1
                logger.info(f"✅ تم إرسال إيميل للأستاذ {prof_name}")
                time.sleep(1)
                
            except Exception as e:
                results.append(f"❌ {prof_name}: فشل الإرسال")
                failed_count += 1
                logger.error(f"❌ خطأ في إرسال إيميل للأستاذ {prof_name}: {str(e)}")
        
        return True, success_count, failed_count, results
        
    except Exception as e:
        logger.error(f"❌ خطأ في إرسال الإيميلات: {str(e)}")
        return False, 0, 0, [f"❌ خطأ عام: {str(e)}"]

def send_email_to_professor(prof_email, prof_name, memo_info, student1, student2=None):
    """إرسال بريد إلكتروني للأستاذ عند تسجيل مذكرة"""
    try:
        df_prof_memos = load_prof_memos()
        prof_memos = df_prof_memos[df_prof_memos["الأستاذ"].astype(str).str.strip() == prof_name.strip()]
        total_memos = len(prof_memos)
        registered_memos = len(prof_memos[prof_memos["تم التسجيل"].astype(str).str.strip() == "نعم"])
        remaining_memos = total_memos - registered_memos
        
        used_passwords = []
        available_passwords = []
        
        for idx, row in prof_memos.iterrows():
            password = str(row.get("كلمة سر التسجيل", "")).strip()
            if password:
                if str(row.get("تم التسجيل", "")).strip() == "نعم":
                    used_passwords.append(f"✅ {password}")
                else:
                    available_passwords.append(f"⏳ {password}")
        
        student2_info = ""
        if student2 is not None:
            student2_info = f"\n👤 **الطالب الثاني:** {student2['اللقب']} {student2['الإسم']}"
        
        passwords_list = "\n".join(used_passwords + available_passwords) if (used_passwords or available_passwords) else "لا توجد كلمات سر مسجلة"
        
        email_body = f"""
<html dir="rtl">
<head>
    <style>
        body {{ font-family: 'Arial', sans-serif; background-color: #f4f4f4; padding: 20px; }}
        .container {{ background-color: #ffffff; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); max-width: 600px; margin: auto; }}
        .header {{ background-color: #256D85; color: white; padding: 20px; border-radius: 8px; text-align: center; margin-bottom: 20px; }}
        .header h2 {{ margin: 0; }}
        .content {{ line-height: 1.8; color: #333; }}
        .info-box {{ background-color: #f8f9fa; padding: 15px; border-right: 4px solid #256D85; margin: 15px 0; }}
        .stats-box {{ background-color: #e8f4f8; padding: 15px; border-radius: 8px; margin: 15px 0; }}
        .footer {{ text-align: center; color: #888; font-size: 12px; margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; }}
        .highlight {{ color: #256D85; font-weight: bold; }}
        ul {{ list-style: none; padding: 0; }}
        li {{ padding: 5px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>✅ تسجيل مذكرة جديدة</h2>
        </div>
        
        <div class="content">
            <p>تحية طيبة وبعد : الأستاذ(ة) الفاضل(ة) <span class="highlight">{prof_name}</span>،</p>
            
            <p>نحيطكم علماً بأنه تم تسجيل مذكرة جديدة تحت إشرافكم:</p>
            
            <div class="info-box">
                <p>📄 <strong>رقم المذكرة:</strong> {memo_info['رقم المذكرة']}</p>
                <p>📑 <strong>عنوان المذكرة:</strong> {memo_info['عنوان المذكرة']}</p>
                <p>🎓 <strong>التخصص:</strong> {memo_info['التخصص']}</p>
                <p>👤 <strong>الطالب الأول:</strong> {student1['اللقب']} {student1['الإسم']}{student2_info}</p>
                <p>🕒 <strong>تاريخ التسجيل:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
            </div>
            
            <div class="stats-box">
                <h3 style="color: #256D85; margin-top: 0;">📊 إحصائيات مذكراتك:</h3>
                <ul>
                    <li>📝 <strong>إجمالي المذكرات:</strong> {total_memos}</li>
                    <li>✅ <strong>المذكرات المسجلة:</strong> {registered_memos}</li>
                    <li>⏳ <strong>المذكرات المتبقية:</strong> {remaining_memos}</li>
                </ul>
            </div>
            
            <div class="info-box">
                <h3 style="color: #256D85; margin-top: 0;">🔑 كلمات السر:</h3>
                <ul style="white-space: pre-line;">{passwords_list}</ul>
            </div>
            
            <p style="margin-top: 20px; color: #666;">للاستفسار أو الدعم، يرجى التواصل مع السيد مسؤول الميدان الدكتور رفاف لخضر.</p>
        </div>
        
        <div class="footer">
            <p>© 2026 جامعة محمد البشير الإبراهيمي</p>
            <p>كلية الحقوق والعلوم السياسية</p>
        </div>
    </div>
</body>
</html>
"""
        
        msg = MIMEMultipart('alternative')
        msg['From'] = EMAIL_SENDER
        msg['To'] = prof_email
        msg['Subject'] = f"✅ تسجيل مذكرة جديدة - رقم {memo_info['رقم المذكرة']}"
        
        html_part = MIMEText(email_body, 'html', 'utf-8')
        msg.attach(html_part)
        
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)
        
        logger.info(f"✅ تم إرسال بريد إلكتروني للأستاذ {prof_name}")
        return True, "تم إرسال البريد الإلكتروني بنجاح"
        
    except Exception as e:
        logger.error(f"❌ خطأ في إرسال البريد الإلكتروني: {str(e)}")
        return False, f"فشل إرسال البريد: {str(e)}"

# بقية الكود كما هو (verify_student, verify_students_batch, verify_professor_password, update_registration, logout)
# ... (أضف هنا بقية الدوال من الكود الأصلي)

# تحميل البيانات
df_students = load_students()
df_memos = load_memos()
df_prof_memos = load_prof_memos()

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

# ---------------- لوحة تحكم الإدارة ----------------
with st.expander("🔐 لوحة تحكم الإدارة"):
    if not st.session_state.admin_mode:
        admin_pass_input = st.text_input("كلمة سر الإدارة", type="password", key="admin_login")
        if st.button("دخول الإدارة"):
            if admin_pass_input == ADMIN_PASSWORD:
                st.session_state.admin_mode = True
                st.success("✅ تم الدخول بنجاح")
                st.rerun()
            else:
                st.error("❌ كلمة سر خاطئة")
    else:
        st.success("✅ أنت في وضع الإدارة")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📧 إرسال إيميلات لجميع الأساتذة", type="primary", use_container_width=True):
                with st.spinner("⏳ جاري إرسال الإيميلات..."):
                    success, success_count, failed_count, results = send_bulk_emails_to_all_professors()
                
                if success:
                    st.success(f"✅ تم إرسال {success_count} إيميل بنجاح")
                    if failed_count > 0:
                        st.warning(f"⚠️ فشل إرسال {failed_count} إيميل")
                    
                    with st.expander("📋 تفاصيل الإرسال"):
                        for result in results:
                            st.text(result)
                else:
                    st.error("❌ فشل إرسال الإيميلات")
                    for result in results:
                        st.text(result)
        
        with col2:
            if st.button("🚪 خروج من الإدارة", use_container_width=True):
                st.session_state.admin_mode = False
                st.rerun()
