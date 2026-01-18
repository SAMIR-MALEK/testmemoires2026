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
import re

# ---------------- إعداد Logging ----------------
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ---------------- إعداد الصفحة ----------------
st.set_page_config(page_title="منصة تسجيل المذكرات", page_icon="🎓", layout="wide")

# ---------------- CSS عصري ----------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;900&family=Tajawal:wght@400;700;900&display=swap');

* {
    font-family: 'Cairo', sans-serif !important;
}

html, body, [class*="css"] {
    background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
    color: #F1F5F9;
}

.main {
    background: transparent;
}

.block-container {
    padding: 2rem !important;
    max-width: 1400px !important;
}

/* الصفحة الرئيسية */
.hero-section {
    text-align: center;
    padding: 3rem 1rem;
    background: linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(245, 158, 11, 0.1) 100%);
    border-radius: 24px;
    margin-bottom: 3rem;
    border: 2px solid rgba(59, 130, 246, 0.2);
}

.hero-title {
    font-size: 48px !important;
    font-weight: 900 !important;
    background: linear-gradient(135deg, #3B82F6 0%, #F59E0B 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 1rem !important;
}

.hero-subtitle {
    font-size: 28px !important;
    color: #94A3B8;
    font-weight: 600 !important;
}

/* بطاقات الاختيار */
.choice-container {
    display: flex;
    gap: 2rem;
    justify-content: center;
    flex-wrap: wrap;
    margin: 2rem 0;
}

.choice-card {
    background: linear-gradient(135deg, #1E293B 0%, #334155 100%);
    border-radius: 24px;
    padding: 3rem 2rem;
    text-align: center;
    cursor: pointer;
    transition: all 0.4s ease;
    border: 3px solid transparent;
    min-width: 280px;
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
}

.choice-card:hover {
    transform: translateY(-10px) scale(1.05);
    border-color: #3B82F6;
    box-shadow: 0 20px 60px rgba(59, 130, 246, 0.4);
}

.choice-icon {
    font-size: 80px;
    margin-bottom: 1rem;
}

.choice-title {
    font-size: 32px !important;
    font-weight: 900 !important;
    color: #F1F5F9;
    margin-bottom: 0.5rem !important;
}

.choice-desc {
    font-size: 18px !important;
    color: #94A3B8;
}

/* نماذج تسجيل الدخول */
.login-box {
    background: linear-gradient(135deg, #1E293B 0%, #334155 100%);
    border-radius: 24px;
    padding: 3rem;
    max-width: 500px;
    margin: 2rem auto;
    border: 2px solid rgba(59, 130, 246, 0.3);
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.4);
}

.login-title {
    font-size: 36px !important;
    font-weight: 900 !important;
    text-align: center;
    color: #3B82F6;
    margin-bottom: 2rem !important;
}

/* حقول الإدخال */
.stTextInput > div > div > input,
.stSelectbox > div > div > select,
.stTextArea > div > div > textarea {
    background: #0F172A !important;
    border: 2px solid #334155 !important;
    border-radius: 12px !important;
    color: #F1F5F9 !important;
    font-size: 20px !important;
    padding: 16px !important;
    font-weight: 600 !important;
}

.stTextInput > div > div > input:focus,
.stSelectbox > div > div > select:focus {
    border-color: #3B82F6 !important;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2) !important;
}

label, .stTextInput label, .stSelectbox label, .stTextArea label {
    color: #F1F5F9 !important;
    font-size: 20px !important;
    font-weight: 700 !important;
    margin-bottom: 8px !important;
}

/* الأزرار */
.stButton > button {
    background: linear-gradient(135deg, #3B82F6 0%, #2563EB 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 16px 32px !important;
    font-size: 20px !important;
    font-weight: 900 !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 8px 24px rgba(59, 130, 246, 0.4) !important;
}

.stButton > button:hover {
    transform: translateY(-3px) !important;
    box-shadow: 0 12px 32px rgba(59, 130, 246, 0.6) !important;
}

/* بطاقات المعلومات */
.info-card {
    background: linear-gradient(135deg, #1E293B 0%, #334155 100%);
    border-radius: 20px;
    padding: 2rem;
    margin: 1rem 0;
    border-left: 6px solid #3B82F6;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
}

.stat-card {
    background: linear-gradient(135deg, #3B82F6 0%, #2563EB 100%);
    border-radius: 20px;
    padding: 2rem;
    text-align: center;
    box-shadow: 0 10px 30px rgba(59, 130, 246, 0.4);
}

.stat-number {
    font-size: 56px !important;
    font-weight: 900 !important;
    font-family: 'Tajawal', sans-serif !important;
    color: #F59E0B;
    text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
}

.stat-label {
    font-size: 22px !important;
    font-weight: 700 !important;
    color: #F1F5F9;
    margin-top: 0.5rem;
}

/* الرسائل */
.success-msg {
    background: linear-gradient(135deg, #10B981 0%, #059669 100%);
    color: white;
    padding: 1.5rem;
    border-radius: 16px;
    font-size: 20px !important;
    font-weight: 700 !important;
    text-align: center;
    box-shadow: 0 8px 24px rgba(16, 185, 129, 0.4);
    margin: 1rem 0;
}

.error-msg {
    background: linear-gradient(135deg, #EF4444 0%, #DC2626 100%);
    color: white;
    padding: 1.5rem;
    border-radius: 16px;
    font-size: 20px !important;
    font-weight: 700 !important;
    text-align: center;
    box-shadow: 0 8px 24px rgba(239, 68, 68, 0.4);
    margin: 1rem 0;
}

.warning-msg {
    background: linear-gradient(135deg, #F59E0B 0%, #D97706 100%);
    color: white;
    padding: 1.5rem;
    border-radius: 16px;
    font-size: 20px !important;
    font-weight: 700 !important;
    text-align: center;
    box-shadow: 0 8px 24px rgba(245, 158, 11, 0.4);
    margin: 1rem 0;
}

.info-msg {
    background: linear-gradient(135deg, #3B82F6 0%, #2563EB 100%);
    color: white;
    padding: 1.5rem;
    border-radius: 16px;
    font-size: 20px !important;
    font-weight: 700 !important;
    box-shadow: 0 8px 24px rgba(59, 130, 246, 0.4);
    margin: 1rem 0;
}

/* جدول المذكرات */
.memo-table {
    background: #1E293B;
    border-radius: 16px;
    padding: 1.5rem;
    margin: 1rem 0;
    border: 2px solid #334155;
}

.memo-row {
    padding: 1rem;
    border-bottom: 1px solid #334155;
    font-size: 18px;
    transition: all 0.3s ease;
}

.memo-row:hover {
    background: #334155;
    border-radius: 8px;
}

/* شريط التقدم */
.progress-container {
    background: #0F172A;
    border-radius: 20px;
    padding: 1rem;
    margin: 1rem 0;
}

.progress-bar {
    height: 40px;
    border-radius: 20px;
    background: linear-gradient(90deg, #3B82F6 0%, #10B981 100%);
    transition: width 0.5s ease;
    box-shadow: 0 4px 12px rgba(59, 130, 246, 0.5);
}

.progress-text {
    font-size: 24px !important;
    font-weight: 900 !important;
    font-family: 'Tajawal', sans-serif !important;
    color: #F59E0B;
    text-align: center;
    margin-top: 0.5rem;
}

/* زر الخروج */
.logout-btn {
    background: linear-gradient(135deg, #EF4444 0%, #DC2626 100%) !important;
}

.logout-btn:hover {
    background: linear-gradient(135deg, #DC2626 0%, #B91C1C 100%) !important;
}

/* تحسينات إضافية */
h1, h2, h3, h4, h5, h6 {
    color: #F1F5F9 !important;
    font-weight: 900 !important;
}

.stRadio > div {
    gap: 1rem;
}

.stRadio label {
    font-size: 20px !important;
    font-weight: 700 !important;
}

/* الأيقونات */
.big-icon {
    font-size: 64px;
    margin: 1rem 0;
}

hr {
    border-color: #334155 !important;
    margin: 2rem 0 !important;
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

STUDENTS_RANGE = "Feuille 1!A1:M1000"
MEMOS_RANGE = "Feuille 1!A1:N1000"
PROF_MEMOS_RANGE = "Feuille 1!A1:M1000"

# ---------------- Email Configuration ----------------
EMAIL_SENDER = "domaine.dsp@univ-bba.dz"
EMAIL_PASSWORD = "oevruyiztgikwzah"
ADMIN_EMAIL = "domaine.dsp@univ-bba.dz"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# ---------------- مراحل التقدم ----------------
PROGRESS_STAGES = [
    "0% - لم يبدأ",
    "10% - ضبط الخطة",
    "20% - المقدمة",
    "30% - الفصل الأول - المبحث الأول",
    "40% - الفصل الأول - المبحث الثاني",
    "50% - الفصل الثاني - المبحث الأول",
    "60% - الفصل الثاني - المبحث الثاني",
    "70% - الخاتمة",
    "80% - المراجعة النهائية",
    "90% - التدقيق اللغوي",
    "100% - مكتملة"
]

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

def validate_phone(phone):
    """التحقق من رقم هاتف جزائري"""
    phone = sanitize_input(phone)
    pattern = r'^0[567]\d{8}$'
    if re.match(pattern, phone):
        return True, phone
    return False, "⚠️ رقم الهاتف يجب أن يبدأ بـ 05 أو 06 أو 07 ويتكون من 10 أرقام"

def is_valid_phone_in_sheet(phone):
    """التحقق من وجود رقم هاتف حقيقي في الشيت"""
    if not phone or phone in ['0', '1', '', 'nan']:
        return False
    pattern = r'^0[567]\d{8}$'
    return bool(re.match(pattern, str(phone).strip()))

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
        logger.info(f"تم تحميل {len(df)} طالب")
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
        logger.info(f"تم تحميل {len(df)} مذكرة")
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
        logger.info(f"تم تحميل {len(df)} مذكرة للأساتذة")
        return df
    except Exception as e:
        logger.error(f"خطأ في تحميل بيانات مذكرات الأساتذة: {str(e)}")
        return pd.DataFrame()

def clear_cache():
    st.cache_data.clear()
    logger.info("تم مسح السجلات")

# ---------------- إرسال البريد الإلكتروني ----------------
def send_email(to_email, subject, body_html):
    """دالة عامة لإرسال البريد الإلكتروني"""
    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = EMAIL_SENDER
        msg['To'] = to_email
        msg['Subject'] = subject
        
        html_part = MIMEText(body_html, 'html', 'utf-8')
        msg.attach(html_part)
        
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)
        
        logger.info(f"✅ تم إرسال بريد إلى {to_email}")
        return True
    except Exception as e:
        logger.error(f"❌ خطأ في إرسال البريد: {str(e)}")
        return False

def send_registration_email_to_student(student_email, student_name, memo_info, prof_name):
    """إرسال بريد للطالب عند التسجيل الناجح"""
    body = f"""
<html dir="rtl">
<head>
    <style>
        body {{ font-family: 'Cairo', sans-serif; background: #f4f4f4; padding: 20px; }}
        .container {{ background: white; padding: 40px; border-radius: 16px; max-width: 600px; margin: auto; box-shadow: 0 10px 40px rgba(0,0,0,0.1); }}
        .header {{ background: linear-gradient(135deg, #3B82F6, #2563EB); color: white; padding: 30px; border-radius: 12px; text-align: center; }}
        .content {{ padding: 30px 0; line-height: 2; }}
        .info-box {{ background: #F1F5F9; padding: 20px; border-radius: 12px; margin: 20px 0; border-right: 5px solid #3B82F6; }}
        .footer {{ text-align: center; color: #64748B; margin-top: 40px; padding-top: 20px; border-top: 2px solid #E2E8F0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎉 تهانينا!</h1>
            <h2>تم تسجيل مذكرتك بنجاح</h2>
        </div>
        <div class="content">
            <p>عزيزي الطالب <strong>{student_name}</strong>،</p>
            <p>نهنئك بتسجيل مذكرتك بنجاح في منصة التسجيل الإلكتروني.</p>
            <div class="info-box">
                <h3>📋 تفاصيل المذكرة:</h3>
                <p><strong>رقم المذكرة:</strong> {memo_info['رقم المذكرة']}</p>
                <p><strong>العنوان:</strong> {memo_info['عنوان المذكرة']}</p>
                <p><strong>الأستاذ المشرف:</strong> {prof_name}</p>
                <p><strong>التخصص:</strong> {memo_info['التخصص']}</p>
                <p><strong>تاريخ التسجيل:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
            </div>
            <p>يمكنك متابعة تقدم مذكرتك من خلال فضاءك الخاص في المنصة.</p>
            <p><strong>نتمنى لك التوفيق في رحلتك الأكاديمية! 🎓</strong></p>
        </div>
        <div class="footer">
            <p>© 2026 جامعة محمد البشير الإبراهيمي</p>
            <p>كلية الحقوق والعلوم السياسية</p>
        </div>
    </div>
</body>
</html>
"""
    return send_email(student_email, "✅ تسجيل مذكرة ناجح", body)

def send_title_change_notification(prof_name, old_title, new_title, memo_number):
    """إرسال إشعار للإدارة عند تعديل العنوان"""
    body = f"""
<html dir="rtl">
<head>
    <style>
        body {{ font-family: 'Cairo', sans-serif; background: #f4f4f4; padding: 20px; }}
        .container {{ background: white; padding: 40px; border-radius: 16px; max-width: 600px; margin: auto; }}
        .header {{ background: #F59E0B; color: white; padding: 30px; border-radius: 12px; text-align: center; }}
        .content {{ padding: 30px 0; line-height: 2; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>⚠️ تعديل عنوان مذكرة</h2>
        </div>
        <div class="content">
            <p><strong>الأستاذ:</strong> {prof_name}</p>
            <p><strong>رقم المذكرة:</strong> {memo_number}</p>
            <p><strong>العنوان القديم:</strong> {old_title}</p>
            <p><strong>العنوان الجديد:</strong> {new_title}</p>
            <p><strong>التاريخ:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
        </div>
    </div>
</body>
</html>
"""
    return send_email(ADMIN_EMAIL, f"تعديل عنوان المذكرة {memo_number}", body)

def send_message_to_student(student_email, student_name, prof_name, message):
    """إرسال رسالة من الأستاذ للطالب"""
    body = f"""
<html dir="rtl">
<head>
    <style>
        body {{ font-family: 'Cairo', sans-serif; background: #f4f4f4; padding: 20px; }}
        .container {{ background: white; padding: 40px; border-radius: 16px; max-width: 600px; margin: auto; }}
        .header {{ background: #3B82F6; color: white; padding: 30px; border-radius: 12px; text-align: center; }}
        .message-box {{ background: #F1F5F9; padding: 25px; border-radius: 12px; margin: 20px 0; font-size: 18px; line-height: 2; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>💬 رسالة من الأستاذ المشرف</h2>
        </div>
        <div style="padding: 30px 0;">
            <p>عزيزي الطالب <strong>{student_name}</strong>,</p>
            <p>تلقيت رسالة من الأستاذ المشرف <strong>{prof_name}</strong>:</p>
            <div class="message-box">
                {message}
            </div>
            <p>يرجى الاطلاع عليها والتواصل مع الأستاذ المشرف إذا لزم الأمر.</p>
        </div>
    </div>
</body>
</html>
"""
    return send_email(student_email, f"رسالة من الأستاذ {prof_name}", body)

# ---------------- تحديث الهاتف ----------------
def update_student_phone(username, phone):
    """تحديث رقم هاتف الطالب في الشيت"""
    try:
        df_students = load_students()
        student_idx = df_students[df_students["اسم المستخدم"].astype(str).str.strip() == username.strip()].index[0]
        row_number = student_idx + 2
        
        cols = df_students.columns.tolist()
        phone_col = col_letter(cols.index('الهاتف') + 1)
        
        sheets_service.spreadsheets().values().update(
            spreadsheetId=STUDENTS_SHEET_ID,
            range=f"Feuille 1!{phone_col}{row_number}",
            valueInputOption="USER_ENTERED",
            body={"values": [[phone]]}
        ).execute()
        
        clear_cache()
        logger.info(f"✅ تم تحديث رقم هاتف الطالب: {username}")
        return True
    except Exception as e:
        logger.error(f"❌ خطأ في تحديث رقم الهاتف: {str(e)}")
        return False

# ---------------- تحديث عنوان المذكرة ----------------
def update_memo_title(memo_number, new_title, prof_name):
    """تحديث عنوان المذكرة"""
    try:
        df_memos = load_memos()
        old_title = df_memos[df_memos["رقم المذكرة"].astype(str).str.strip() == str(memo_number).strip()]["عنوان المذكرة"].iloc[0]
        
        memo_idx = df_memos[df_memos["رقم المذكرة"].astype(str).str.strip() == str(memo_number).strip()].index[0]
        row_number = memo_idx + 2
        
        cols = df_memos.columns.tolist()
        title_col = col_letter(cols.index('عنوان المذكرة') + 1)
        
        sheets_service.spreadsheets().values().update(
            spreadsheetId=MEMOS_SHEET_ID,
            range=f"Feuille 1!{title_col}{row_number}",
            valueInputOption="USER_ENTERED",
            body={"values": [[new_title]]}
        ).execute()
        
        send_title_change_notification(prof_name, old_title, new_title, memo_number)
        clear_cache()
        logger.info(f"✅ تم تحديث عنوان المذكرة: {memo_number}")
        return True, "✅ تم تحديث العنوان وإرسال إشعار للإدارة"
    except Exception as e:
        logger.error(f"❌ خطأ في تحديث العنوان: {str(e)}")
        return False, f"❌ خطأ: {str(e)}"

# ---------------- تحديث نسبة التقدم ----------------
def update_progress(memo_number, progress_stage, prof_username):
    """تحديث نسبة تقدم المذكرة"""
    try:
        df_prof_memos = load_prof_memos()
        
        mask = (df_prof_memos["رقم المذكرة"].astype(str).str.strip() == str(memo_number).strip()) & \
               (df_prof_memos["إسم المستخدم"].astype(str).str.strip() == prof_username.strip())
        
        if not any(mask):
            return False, "❌ لم يتم العثور على المذكرة"
        
        memo_idx = df_prof_memos[mask].index[0]
        row_number = memo_idx + 2
        
        cols = df_prof_memos.columns.tolist()
        
        if 'نسبة التقدم' in cols:
            progress_col = col_letter(cols.index('نسبة التقدم') + 1)
            sheets_service.spreadsheets().values().update(
                spreadsheetId=PROF_MEMOS_SHEET_ID,
                range=f"Feuille 1!{progress_col}{row_number}",
                valueInputOption="USER_ENTERED",
                body={"values": [[progress_stage]]}
            ).execute()
        
        clear_cache()
        logger.info(f"✅ تم تحديث نسبة التقدم للمذكرة: {memo_number}")
        return True, "✅ تم تحديث نسبة التقدم بنجاح"
    except Exception as e:
        logger.error(f"❌ خطأ في تحديث نسبة التقدم: {str(e)}")
        return False, f"❌ خطأ: {str(e)}"

# ---------------- تحديث الملاحظات ----------------
def update_notes(memo_number, notes, prof_username):
    """تحديث ملاحظات المذكرة"""
    try:
        df_prof_memos = load_prof_memos()
        
        mask = (df_prof_memos["رقم المذكرة"].astype(str).str.strip() == str(memo_number).strip()) & \
               (df_prof_memos["إسم المستخدم"].astype(str).str.strip() == prof_username.strip())
        
        if not any(mask):
            return False, "❌ لم يتم العثور على المذكرة"
        
        memo_idx = df_prof_memos[mask].index[0]
        row_number = memo_idx + 2
        
        cols = df_prof_memos.columns.tolist()
        
        if 'ملاحظات' in cols:
            notes_col = col_letter(cols.index('ملاحظات') + 1)
            sheets_service.spreadsheets().values().update(
                spreadsheetId=PROF_MEMOS_SHEET_ID,
                range=f"Feuille 1!{notes_col}{row_number}",
                valueInputOption="USER_ENTERED",
                body={"values": [[notes]]}
            ).execute()
        
        clear_cache()
        logger.info(f"✅ تم تحديث ملاحظات المذكرة: {memo_number}")
        return True, "✅ تم حفظ الملاحظات بنجاح"
    except Exception as e:
        logger.error(f"❌ خطأ في تحديث الملاحظات: {str(e)}")
        return False, f"❌ خطأ: {str(e)}"

# ---------------- التحقق من تسجيل الدخول ----------------
def verify_professor(username, password, df_prof_memos):
    """التحقق من بيانات الأستاذ"""
    username = sanitize_input(username)
    password = sanitize_input(password)
    
    if df_prof_memos.empty:
        return False,     # جمع إحصائيات
    my_memos = df_prof_memos_fresh[df_prof_memos_fresh["الأستاذ"].astype(str).str.strip() == prof_name]
    total_memos = len(my_memos)
    registered_memos = len(my_memos[my_memos["تم التسجيل"].astype(str).str.strip() == "نعم"])
    remaining_memos = total_memos - registered_memos
    
    # عرض الإحصائيات
    st.markdown('<h2 style="font-size:32px; margin:2rem 0 1rem 0;">📊 الإحصائيات</h2>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f'''
        <div class="stat-card">
            <div class="big-icon">📚</div>
            <div class="stat-number">{total_memos}</div>
            <div class="stat-label">إجمالي المذكرات</div>
        </div>
        ''', unsafe_allow_html=True)
    
    with col2:
        st.markdown(f'''
        <div class="stat-card" style="background: linear-gradient(135deg, #10B981 0%, #059669 100%);">
            <div class="big-icon">✅</div>
            <div class="stat-number">{registered_memos}</div>
            <div class="stat-label">المذكرات المسجلة</div>
        </div>
        ''', unsafe_allow_html=True)
    
    with col3:
        st.markdown(f'''
        <div class="stat-card" style="background: linear-gradient(135deg, #F59E0B 0%, #D97706 100%);">
            <div class="big-icon">⏳</div>
            <div class="stat-number">{remaining_memos}</div>
            <div class="stat-label">المذكرات المتبقية</div>
        </div>
        ''', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # التبويبات
    tab1, tab2, tab3, tab4 = st.tabs(["📝 المذكرات المسجلة", "🔑 كلمات السر", "📋 جميع المذكرات", "💬 إرسال رسالة"])
    
    # ========== التبويب الأول: المذكرات المسجلة ==========
    with tab1:
        st.markdown('<h2 style="font-size:28px; margin:1.5rem 0;">✅ المذكرات المسجلة</h2>', unsafe_allow_html=True)
        
        registered = my_memos[my_memos["تم التسجيل"].astype(str).str.strip() == "نعم"]
        
        if registered.empty:
            st.markdown('<div class="info-msg">📝 لا توجد مذكرات مسجلة حتى الآن</div>', unsafe_allow_html=True)
        else:
            for idx, row in registered.iterrows():
                memo_number = str(row.get('رقم المذكرة', '')).strip()
                student1 = str(row.get('الطالب الأول', '')).strip()
                student2 = str(row.get('الطالب الثاني', '')).strip()
                reg_date = str(row.get('تاريخ التسجيل', '')).strip()
                progress = str(row.get('نسبة التقدم', '0% - لم يبدأ')).strip()
                notes = str(row.get('ملاحظات', '')).strip()
                
                # الحصول على العنوان من شيت المذكرات
                memo_title = ""
                memo_data = df_memos_fresh[df_memos_fresh["رقم المذكرة"].astype(str).str.strip() == memo_number]
                if not memo_data.empty:
                    memo_title = str(memo_data.iloc[0].get('عنوان المذكرة', '')).strip()
                
                with st.expander(f"📄 المذكرة رقم {memo_number} - {student1}" + (f" و {student2}" if student2 else ""), expanded=False):
                    st.markdown(f"**📑 العنوان:** {memo_title}")
                    st.markdown(f"**👤 الطالب الأول:** {student1}")
                    if student2:
                        st.markdown(f"**👤 الطالب الثاني:** {student2}")
                    st.markdown(f"**📅 تاريخ التسجيل:** {reg_date}")
                    
                    # شريط التقدم
                    progress_num = int(progress.split('%')[0]) if '%' in progress else 0
                    st.markdown(f'''
                    <div class="progress-container">
                        <div style="font-size:20px; font-weight:700; margin-bottom:0.5rem;">📊 نسبة التقدم</div>
                        <div style="background:#0F172A; border-radius:20px; height:40px; overflow:hidden;">
                            <div class="progress-bar" style="width:{progress_num}%; display:flex; align-items:center; justify-content:center;">
                                <span style="color:white; font-weight:900; font-size:18px;">{progress_num}%</span>
                            </div>
                        </div>
                        <div class="progress-text" style="margin-top:0.5rem;">{progress}</div>
                    </div>
                    ''', unsafe_allow_html=True)
                    
                    st.markdown("---")
                    
                    # تعديل العنوان
                    st.markdown("### ✏️ تعديل العنوان")
                    new_title = st.text_area("عنوان جديد:", value=memo_title, key=f"title_{idx}", height=100)
                    
                    if st.button("💾 حفظ العنوان الجديد", key=f"save_title_{idx}"):
                        if new_title.strip() and new_title.strip() != memo_title:
                            success, msg = update_memo_title(memo_number, new_title.strip(), prof_name)
                            if success:
                                st.markdown(f'<div class="success-msg">{msg}</div>', unsafe_allow_html=True)
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.markdown(f'<div class="error-msg">{msg}</div>', unsafe_allow_html=True)
                        else:
                            st.markdown('<div class="warning-msg">⚠️ لم يتم إجراء أي تغيير</div>', unsafe_allow_html=True)
                    
                    st.markdown("---")
                    
                    # تحديث نسبة التقدم
                    st.markdown("### 📊 تحديث نسبة التقدم")
                    new_progress = st.selectbox("اختر المرحلة:", PROGRESS_STAGES, key=f"progress_{idx}", index=PROGRESS_STAGES.index(progress) if progress in PROGRESS_STAGES else 0)
                    
                    if st.button("💾 حفظ نسبة التقدم", key=f"save_progress_{idx}"):
                        success, msg = update_progress(memo_number, new_progress, prof_username)
                        if success:
                            st.markdown(f'<div class="success-msg">{msg}</div>', unsafe_allow_html=True)
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.markdown(f'<div class="error-msg">{msg}</div>', unsafe_allow_html=True)
                    
                    st.markdown("---")
                    
                    # الملاحظات
                    st.markdown("### 📝 الملاحظات (خاصة بالأستاذ والإدارة)")
                    new_notes = st.text_area("الملاحظات:", value=notes, key=f"notes_{idx}", height=150)
                    
                    if st.button("💾 حفظ الملاحظات", key=f"save_notes_{idx}"):
                        success, msg = update_notes(memo_number, new_notes.strip(), prof_username)
                        if success:
                            st.markdown(f'<div class="success-msg">{msg}</div>', unsafe_allow_html=True)
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.markdown(f'<div class="error-msg">{msg}</div>', unsafe_allow_html=True)
    
    # ========== التبويب الثاني: كلمات السر ==========
    with tab2:
        st.markdown('<h2 style="font-size:28px; margin:1.5rem 0;">🔑 كلمات السر المخصصة</h2>', unsafe_allow_html=True)
        
        used_passwords = []
        available_passwords = []
        
        for idx, row in my_memos.iterrows():
            password = str(row.get("كلمة سر التسجيل", "")).strip()
            if password:
                is_used = str(row.get("تم التسجيل", "")).strip() == "نعم"
                memo_num = str(row.get("رقم المذكرة", "")).strip()
                
                if is_used:
                    used_passwords.append({
                        'password': password,
                        'memo': memo_num,
                        'student': str(row.get('الطالب الأول', '')).strip()
                    })
                else:
                    available_passwords.append(password)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown('<div class="info-card" style="border-left-color:#10B981;">', unsafe_allow_html=True)
            st.markdown('### ✅ كلمات السر المستخدمة')
            if used_passwords:
                for item in used_passwords:
                    st.markdown(f"🔒 **{item['password']}** - مذكرة {item['memo']} ({item['student']})")
            else:
                st.markdown("لا توجد كلمات سر مستخدمة")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="info-card" style="border-left-color:#F59E0B;">', unsafe_allow_html=True)
            st.markdown('### ⏳ كلمات السر المتاحة')
            if available_passwords:
                for pwd in available_passwords:
                    st.markdown(f"🔓 **{pwd}**")
            else:
                st.markdown("لا توجد كلمات سر متاحة")
            st.markdown('</div>', unsafe_allow_html=True)
    
    # ========== التبويب الثالث: جميع المذكرات ==========
    with tab3:
        st.markdown('<h2 style="font-size:28px; margin:1.5rem 0;">📋 جميع المذكرات المقترحة</h2>', unsafe_allow_html=True)
        
        for idx, row in my_memos.iterrows():
            memo_number = str(row.get('رقم المذكرة', '')).strip()
            is_registered = str(row.get("تم التسجيل", "")).strip() == "نعم"
            
            # الحصول على العنوان
            memo_title = ""
            specialty = ""
            memo_data = df_memos_fresh[df_memos_fresh["رقم المذكرة"].astype(str).str.strip() == memo_number]
            if not memo_data.empty:
                memo_title = str(memo_data.iloc[0].get('عنوان المذكرة', '')).strip()
                specialty = str(memo_data.iloc[0].get('التخصص', '')).strip()
            
            status_icon = "✅" if is_registered else "⏳"
            status_text = "مسجلة" if is_registered else "متاحة"
            
            st.markdown(f'''
            <div class="memo-row">
                {status_icon} <strong>{memo_number}.</strong> {memo_title} 
                <span style="color:#94A3B8;">({specialty})</span>
                <span style="float:left; color:{'#10B981' if is_registered else '#F59E0B'}; font-weight:700;">{status_text}</span>
            </div>
            ''', unsafe_allow_html=True)
    
    # ========== التبويب الرابع: إرسال رسالة ==========
    with tab4:
        st.markdown('<h2 style="font-size:28px; margin:1.5rem 0;">💬 إرسال رسالة للطالب</h2>', unsafe_allow_html=True)
        
        registered = my_memos[my_memos["تم التسجيل"].astype(str).str.strip() == "نعم"]
        
        if registered.empty:
            st.markdown('<div class="info-msg">📝 لا توجد مذكرات مسجلة لإرسال رسائل</div>', unsafe_allow_html=True)
        else:
            # اختيار المذكرة
            memo_options = []
            for idx, row in registered.iterrows():
                memo_num = str(row.get('رقم المذكرة', '')).strip()
                student = str(row.get('الطالب الأول', '')).strip()
                memo_options.append(f"{memo_num} - {student}")
            
            selected_memo = st.selectbox("📄 اختر المذكرة:", memo_options, key="msg_memo")
            
            message_text = st.text_area("💬 الرسالة:", height=200, key="message_content", placeholder="اكتب رسالتك هنا...")
            
            if st.button("📧 إرسال الرسالة", type="primary", use_container_width=True):
                if not message_text.strip():
                    st.markdown('<div class="error-msg">⚠️ يرجى كتابة رسالة</div>', unsafe_allow_html=True)
                else:
                    # استخراج رقم المذكرة
                    selected_memo_num = selected_memo.split(' - ')[0].strip()
                    
                    # الحصول على بيانات الطالب
                    df_students_fresh = load_students()
                    student_data = df_students_fresh[df_students_fresh["رقم المذكرة"].astype(str).str.strip() == selected_memo_num]
                    
                    if not student_data.empty:
                        emails_sent = 0
                        for idx, student in student_data.iterrows():
                            student_email = str(student.get('البريد المهني', '')).strip()
                            student_name = f"{student['اللقب']} {student['الإسم']}"
                            
                            if student_email and '@' in student_email:
                                if send_message_to_student(student_email, student_name, prof_name, message_text.strip()):
                                    emails_sent += 1
                        
                        if emails_sent > 0:
                            st.markdown(f'<div class="success-msg">✅ تم إرسال الرسالة بنجاح إلى {emails_sent} طالب/طلاب</div>', unsafe_allow_html=True)
                        else:
                            st.markdown('<div class="error-msg">❌ فشل إرسال الرسالة. تحقق من البريد الإلكتروني</div>', unsafe_allow_html=True)
                    else:
                        st.markdown('<div class="error-msg">❌ لم يتم العثور على بيانات الطالب</div>', unsafe_allow_html=True)

# ---------------- فضاء الطالب ----------------
elif st.session_state.page == "student_space" and st.session_state.logged_in:
    
    s1 = st.session_state.student1
    s2 = st.session_state.student2
    
    # رأس الصفحة
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown(f'<h1 style="font-size:42px; margin-bottom:0;">🎓 مرحباً {s1["اللقب"]} {s1["الإسم"]}</h1>', unsafe_allow_html=True)
    with col2:
        if st.button("🚪 خروج", key="logout_student", use_container_width=True):
            logout()
    
    st.markdown("---")
    
    # معلومات الطالب
    st.markdown('<div class="info-card">', unsafe_allow_html=True)
    st.markdown(f"**👤 الطالب الأول:** {s1['اللقب']} {s1['الإسم']}")
    st.markdown(f"**🎓 التخصص:** {s1['التخصص']}")
    if s2 is not None:
        st.markdown(f"**👤 الطالب الثاني:** {s2['اللقب']} {s2['الإسم']}")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # التحقق من وجود مذكرة مسجلة
    note_number = str(s1.get('رقم المذكرة', '')).strip()
    
    if note_number:
        # ========== الطالب مسجل - عرض معلومات المذكرة ==========
        df_memos_fresh = load_memos()
        df_prof_memos_fresh = load_prof_memos()
        
        memo_info = df_memos_fresh[df_memos_fresh["رقم المذكرة"].astype(str).str.strip() == note_number]
        
        if not memo_info.empty:
            memo_info = memo_info.iloc[0]
            prof_name = str(memo_info['الأستاذ']).strip()
            
            # الحصول على نسبة التقدم من شيت الأساتذة
            prof_memo_data = df_prof_memos_fresh[
                (df_prof_memos_fresh["رقم المذكرة"].astype(str).str.strip() == note_number)
            ]
            
            progress = "0% - لم يبدأ"
            if not prof_memo_data.empty:
                progress = str(prof_memo_data.iloc[0].get('نسبة التقدم', '0% - لم يبدأ')).strip()
            
            st.markdown('<h2 style="font-size:32px; margin:2rem 0 1rem 0;">✅ مذكرتك المسجلة</h2>', unsafe_allow_html=True)
            
            st.markdown('<div class="info-card" style="border-left-color:#10B981;">', unsafe_allow_html=True)
            st.markdown(f"### 📄 المذكرة رقم {memo_info['رقم المذكرة']}")
            st.markdown(f"**📑 العنوان:** {memo_info['عنوان المذكرة']}")
            st.markdown(f"**👨‍🏫 الأستاذ المشرف:** {memo_info['الأستاذ']}")
            st.markdown(f"**🎯 التخصص:** {memo_info['التخصص']}")
            st.markdown(f"**📅 تاريخ التسجيل:** {memo_info.get('تاريخ التسجيل', '')}")
            st.markdown('</div>', unsafe_allow_html=True)
            
            # شريط التقدم
            st.markdown('<h2 style="font-size:28px; margin:2rem 0 1rem 0;">📊 نسبة التقدم</h2>', unsafe_allow_html=True)
            
            progress_num = int(progress.split('%')[0]) if '%' in progress else 0
            
            st.markdown(f'''
            <div class="progress-container">
                <div style="background:#0F172A; border-radius:20px; height:50px; overflow:hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.3);">
                    <div class="progress-bar" style="width:{progress_num}%; display:flex; align-items:center; justify-content:center; height:50px;">
                        <span style="color:white; font-weight:900; font-size:22px;">{progress_num}%</span>
                    </div>
                </div>
                <div class="progress-text" style="margin-top:1rem; font-size:26px;">{progress}</div>
            </div>
            ''', unsafe_allow_html=True)
            
            st.markdown('<div class="info-msg" style="margin-top:2rem;">', unsafe_allow_html=True)
            st.markdown("### ℹ️ ملاحظات هامة")
            st.markdown("• يتم تحديث نسبة التقدم من قبل الأستاذ المشرف")
            st.markdown("• في حالة وجود أي استفسار، يرجى التواصل مباشرة مع الأستاذ المشرف")
            st.markdown("• تابع بريدك الإلكتروني لتلقي الرسائل والتحديثات")
            st.markdown('</div>', unsafe_allow_html=True)
        
        else:
            st.markdown('<div class="error-msg">⚠️ لم يتم العثور على معلومات المذكرة. يرجى تحديث الصفحة.</div>', unsafe_allow_html=True)
            if st.button("🔄 تحديث الصفحة", use_container_width=True):
                clear_cache()
                time.sleep(1)
                st.rerun()
    
    else:
        # ========== الطالب غير مسجل - نموذج التسجيل ==========
        st.markdown('<h2 style="font-size:32px; margin:2rem 0 1rem 0;">📝 تسجيل مذكرة جديدة</h2>', unsafe_allow_html=True)
        
        st.markdown('<div class="warning-msg">', unsafe_allow_html=True)
        st.markdown("### ⚠️ تنبيه هام")
        st.markdown("• اختر الأستاذ المشرف والمذكرة بعناية")
        st.markdown("• بعد التأكيد النهائي، لن تتمكن من تغيير المذكرة")
        st.markdown("• تأكد من صحة رقم المذكرة وكلمة سر المشرف")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # اختيار الأستاذ
        all_profs = sorted(df_memos["الأستاذ"].dropna().unique())
        selected_prof = st.selectbox("🧑‍🏫 اختر الأستاذ المشرف:", [""] + all_profs, key="select_prof")
        
        if selected_prof:
            student_specialty = s1["التخصص"]
            available_memos_df = df_memos[
                (df_memos["الأستاذ"].astype(str).str.strip() == selected_prof.strip()) &
                (df_memos["التخصص"].astype(str).str.strip() == student_specialty.strip()) &
                (df_memos["تم التسجيل"].astype(str).str.strip() != "نعم")
            ][["رقم المذكرة", "عنوان المذكرة"]]
            
            if not available_memos_df.empty:
                st.markdown(f'<div class="info-card" style="border-left-color:#10B981;">', unsafe_allow_html=True)
                st.markdown(f'<h3 style="color:#10B981; font-size:24px;">✅ المذكرات المتاحة في تخصصك ({student_specialty})</h3>', unsafe_allow_html=True)
                
                for idx, row in available_memos_df.iterrows():
                    st.markdown(f"**{row['رقم المذكرة']}.** {row['عنوان المذكرة']}")
                
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="error-msg">❌ لا توجد مذكرات متاحة لهذا الأستاذ في تخصصك</div>', unsafe_allow_html=True)
        
        st.markdown("---")
        
        # إدخال البيانات
        col1, col2 = st.columns(2)
        with col1:
            st.session_state.note_number = st.text_input(
                "📄 رقم المذكرة", 
                value=st.session_state.note_number,
                max_chars=20,
                key="note_num_input"
            )
        with col2:
            st.session_state.prof_password = st.text_input(
                "🔑 كلمة سر المشرف", 
                type="password",
                key="prof_pass_input",
                max_chars=50
            )
        
        # نموذج التأكيد
        if not st.session_state.show_confirmation:
            if st.button("📝 المتابعة للتأكيد", type="primary", use_container_width=True):
                if not st.session_state.note_number or not st.session_state.prof_password:
                    st.markdown('<div class="error-msg">⚠️ يرجى إدخال رقم المذكرة وكلمة سر المشرف</div>', unsafe_allow_html=True)
                else:
                    st.session_state.show_confirmation = True
                    st.rerun()
        else:
            st.markdown('<div class="warning-msg">', unsafe_allow_html=True)
            st.markdown("### ⚠️ تأكيد نهائي")
            st.markdown(f"**📄 رقم المذكرة:** {st.session_state.note_number}")
            st.markdown(f"**👤 الطالب الأول:** {s1['اللقب']} {s1['الإسم']}")
            if s2 is not None:
                st.markdown(f"**👤 الطالب الثاني:** {s2['اللقب']} {s2['الإسم']}")
            st.markdown("**🚨 تنبيه:** بعد التأكيد، لن تتمكن من تغيير المذكرة!")
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
                            
                            clear_cache()
                            st.session_state.show_confirmation = False
                            
                            # إعادة تحميل بيانات الطالب
                            time.sleep(2)
                            df_students_updated = load_students()
                            st.session_state.student1 = df_students_updated[
                                df_students_updated["اسم المستخدم"].astype(str).str.strip() == s1['اسم المستخدم'].strip()
                            ].iloc[0]
                            
                            if s2 is not None:
                                st.session_state.student2 = df_students_updated[
                                    df_students_updated["اسم المستخدم"].astype(str).str.strip() == s2['اسم المستخدم'].strip()
                                ].iloc[0]
                            
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.markdown(f'<div class="error-msg">{message}</div>', unsafe_allow_html=True)
                            st.session_state.show_confirmation = False
            
            with col2:
                if st.button("❌ إلغاء", use_container_width=True):
                    st.session_state.show_confirmation = False
                    st.rerun()

# ---------------- Footer ----------------
st.markdown("---")
st.markdown("""
    <div style='text-align:center; color:#64748B; font-size:16px; padding:30px; background:rgba(30, 41, 59, 0.5); border-radius:16px; margin-top:3rem;'>
        <p style='font-size:18px; font-weight:700; color:#F1F5F
    
    prof = df_prof_memos[
        (df_prof_memos["إسم المستخدم"].astype(str).str.strip() == username) &
        (df_prof_memos["كلمة المرور"].astype(str).str.strip() == password)
    ]
    
    if prof.empty:
        return False, None
    
    logger.info(f"✅ تسجيل دخول أستاذ: {username}")
    return True, prof.iloc[0]

def verify_student(username, password, df_students):
    """التحقق من بيانات الطالب"""
    username = sanitize_input(username)
    password = sanitize_input(password)
    
    if df_students.empty:
        return False, "❌ خطأ في تحميل البيانات"
    
    student = df_students[df_students["اسم المستخدم"].astype(str).str.strip() == username]
    
    if student.empty:
        return False, "❌ اسم المستخدم غير موجود"
    
    if student.iloc[0]["كلمة السر"].strip() != password:
        return False, "❌ كلمة السر غير صحيحة"
    
    logger.info(f"✅ تسجيل دخول طالب: {username}")
    return True, student.iloc[0]

# ---------------- تحديث التسجيل (نفس المنطق القديم) ----------------
def verify_professor_password(note_number, prof_password, df_memos, df_prof_memos):
    """التحقق من كلمة سر الأستاذ"""
    note_number = sanitize_input(note_number)
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
        return False, None, "❌ هذه كلمة السر مستخدمة مسبقاً"
    
    return True, prof_row.iloc[0], None

def update_registration(note_number, student1, student2=None):
    """تحديث تسجيل المذكرة"""
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
        clear_cache()
        time.sleep(1)
        
        # إرسال بريد للطالب
        student1_email = str(student1.get('البريد المهني', '')).strip()
        if student1_email and '@' in student1_email:
            memo_data = df_memos[df_memos["رقم المذكرة"].astype(str).str.strip() == str(note_number).strip()].iloc[0]
            send_registration_email_to_student(
                student1_email,
                f"{student1['اللقب']} {student1['الإسم']}",
                memo_data,
                prof_name
            )
        
        if student2 is not None:
            student2_email = str(student2.get('البريد المهني', '')).strip()
            if student2_email and '@' in student2_email:
                send_registration_email_to_student(
                    student2_email,
                    f"{student2['اللقب']} {student2['الإسم']}",
                    memo_data,
                    prof_name
                )
        
        return True, "✅ تم التسجيل بنجاح وإرسال البريد الإلكتروني!"
        
    except Exception as e:
        logger.error(f"❌ خطأ في التسجيل: {str(e)}")
        return False, f"❌ خطأ: {str(e)}"

# ---------------- Session State ----------------
if 'page' not in st.session_state:
    st.session_state.page = "home"
    st.session_state.user_type = None
    st.session_state.logged_in = False
    st.session_state.professor = None
    st.session_state.student1 = None
    st.session_state.student2 = None
    st.session_state.memo_type = "فردية"
    st.session_state.note_number = ""
    st.session_state.prof_password = ""
    st.session_state.show_confirmation = False
    st.session_state.phone_collected = False

def logout():
    """تسجيل الخروج"""
    st.session_state.page = "home"
    st.session_state.user_type = None
    st.session_state.logged_in = False
    st.session_state.professor = None
    st.session_state.student1 = None
    st.session_state.student2 = None
    st.session_state.note_number = ""
    st.session_state.prof_password = ""
    st.session_state.show_confirmation = False
    st.session_state.phone_collected = False
    st.rerun()

# تحميل البيانات
df_students = load_students()
df_memos = load_memos()
df_prof_memos = load_prof_memos()

# ---------------- الصفحة الرئيسية ----------------
if st.session_state.page == "home":
    st.markdown("""
        <div class="hero-section">
            <div style="text-align:center; margin-bottom:2rem;">
                <img src="https://raw.githubusercontent.com/SAMIR-MALEK/memoire-depot-2026/main/LOGO2.png" width="120">
            </div>
            <h1 class="hero-title">🎓 منصة تسجيل المذكرات</h1>
            <h2 class="hero-subtitle">جامعة محمد البشير الإبراهيمي</h2>
            <p style="font-size:22px; color:#94A3B8; margin-top:1rem;">كلية الحقوق والعلوم السياسية</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<h2 style="text-align:center; margin:3rem 0 2rem 0; font-size:36px;">اختر نوع المستخدم</h2>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        col_prof, col_student = st.columns(2)
        
        with col_prof:
            if st.button("👨‍🏫", key="prof_btn", use_container_width=True):
                st.session_state.user_type = "professor"
                st.session_state.page = "login"
                st.rerun()
            st.markdown('<div class="choice-card"><div class="choice-icon">👨‍🏫</div><h3 class="choice-title">أستاذ</h3><p class="choice-desc">فضاء الأساتذة</p></div>', unsafe_allow_html=True)
        
        with col_student:
            if st.button("🎓", key="student_btn", use_container_width=True):
                st.session_state.user_type = "student"
                st.session_state.page = "login"
                st.rerun()
            st.markdown('<div class="choice-card"><div class="choice-icon">🎓</div><h3 class="choice-title">طالب</h3><p class="choice-desc">فضاء الطلبة</p></div>', unsafe_allow_html=True)

# ---------------- صفحة تسجيل الدخول ----------------
elif st.session_state.page == "login":
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        if st.session_state.user_type == "professor":
            st.markdown('<div class="login-box">', unsafe_allow_html=True)
            st.markdown('<h2 class="login-title">👨‍🏫 تسجيل دخول الأستاذ</h2>', unsafe_allow_html=True)
            
            username = st.text_input("📧 اسم المستخدم", max_chars=100, key="prof_user")
            password = st.text_input("🔒 كلمة المرور", type="password", max_chars=100, key="prof_pass")
            
            col_login, col_back = st.columns(2)
            
            with col_login:
                if st.button("🚀 دخول", type="primary", use_container_width=True):
                    if not username or not password:
                        st.markdown('<div class="error-msg">⚠️ يرجى إدخال جميع البيانات</div>', unsafe_allow_html=True)
                    else:
                        valid, prof_data = verify_professor(username, password, df_prof_memos)
                        if valid:
                            st.session_state.logged_in = True
                            st.session_state.professor = prof_data
                            st.session_state.page = "professor_dashboard"
                            st.rerun()
                        else:
                            st.markdown('<div class="error-msg">❌ اسم المستخدم أو كلمة المرور غير صحيحة</div>', unsafe_allow_html=True)
            
            with col_back:
                if st.button("🔙 رجوع", use_container_width=True):
                    st.session_state.page = "home"
                    st.rerun()
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        else:  # student
            st.markdown('<div class="login-box">', unsafe_allow_html=True)
            st.markdown('<h2 class="login-title">🎓 تسجيل دخول الطالب</h2>', unsafe_allow_html=True)
            
            st.session_state.memo_type = st.radio("📝 نوع المذكرة:", ["فردية", "ثنائية"], horizontal=True)
            
            st.markdown("---")
            
            username1 = st.text_input("👤 اسم المستخدم (الطالب الأول)", max_chars=50)
            password1 = st.text_input("🔒 كلمة السر (الطالب الأول)", type="password", max_chars=50)
            
            username2 = password2 = None
            
            if st.session_state.memo_type == "ثنائية":
                st.markdown("---")
                username2 = st.text_input("👤 اسم المستخدم (الطالب الثاني)", max_chars=50)
                password2 = st.text_input("🔒 كلمة السر (الطالب الثاني)", type="password", max_chars=50)
            
            col_login, col_back = st.columns(2)
            
            with col_login:
                if st.button("🚀 دخول", type="primary", use_container_width=True):
                    # التحقق من الطالب الأول
                    valid1, result1 = verify_student(username1, password1, df_students)
                    
                    if not valid1:
                        st.markdown(f'<div class="error-msg">{result1}</div>', unsafe_allow_html=True)
                    else:
                        st.session_state.student1 = result1
                        
                        # إذا كانت ثنائية
                        if st.session_state.memo_type == "ثنائية":
                            if not username2 or not password2:
                                st.markdown('<div class="error-msg">⚠️ يرجى إدخال بيانات الطالب الثاني</div>', unsafe_allow_html=True)
                                st.stop()
                            
                            if username1.strip().lower() == username2.strip().lower():
                                st.markdown('<div class="error-msg">❌ لا يمكن أن يكون الطالبان نفس الشخص!</div>', unsafe_allow_html=True)
                                st.stop()
                            
                            valid2, result2 = verify_student(username2, password2, df_students)
                            
                            if not valid2:
                                st.markdown(f'<div class="error-msg">{result2}</div>', unsafe_allow_html=True)
                                st.stop()
                            
                            st.session_state.student2 = result2
                            
                            # التحقق من التخصص
                            if st.session_state.student1['التخصص'].strip() != st.session_state.student2['التخصص'].strip():
                                st.markdown('<div class="error-msg">❌ الطالبان في تخصصين مختلفين</div>', unsafe_allow_html=True)
                                st.stop()
                        
                        # التحقق من المذكرة الفردية
                        if st.session_state.memo_type == "فردية":
                            fardiya = str(st.session_state.student1.get('فردية', '')).strip()
                            if fardiya not in ["1", "نعم"]:
                                st.markdown('<div class="error-msg">❌ لا يمكنك تسجيل مذكرة فردية</div>', unsafe_allow_html=True)
                                st.stop()
                        
                        st.session_state.logged_in = True
                        st.session_state.page = "collect_phone"
                        st.rerun()
            
            with col_back:
                if st.button("🔙 رجوع", use_container_width=True):
                    st.session_state.page = "home"
                    st.rerun()
            
            st.markdown('</div>', unsafe_allow_html=True)

# ---------------- جمع رقم الهاتف ----------------
elif st.session_state.page == "collect_phone":
    
    # التحقق من رقم الهاتف للطالب الأول
    phone1 = str(st.session_state.student1.get('الهاتف', '')).strip()
    needs_phone1 = not is_valid_phone_in_sheet(phone1)
    
    phone2_needed = False
    if st.session_state.student2 is not None:
        phone2 = str(st.session_state.student2.get('الهاتف', '')).strip()
        phone2_needed = not is_valid_phone_in_sheet(phone2)
    
    # إذا كان كل الهواتف موجودة
    if not needs_phone1 and not phone2_needed:
        st.session_state.phone_collected = True
        st.session_state.page = "student_space"
        st.rerun()
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown('<div class="login-box">', unsafe_allow_html=True)
        st.markdown('<h2 class="login-title">📱 تسجيل رقم الهاتف</h2>', unsafe_allow_html=True)
        st.markdown('<div class="info-msg">⚠️ يرجى إدخال رقم هاتف جزائري صحيح (10 أرقام تبدأ بـ 05 أو 06 أو 07)</div>', unsafe_allow_html=True)
        
        phone_input1 = None
        phone_input2 = None
        
        if needs_phone1:
            st.markdown(f"<p style='font-size:20px; font-weight:700; margin-top:1.5rem;'>👤 {st.session_state.student1['اللقب']} {st.session_state.student1['الإسم']}</p>", unsafe_allow_html=True)
            phone_input1 = st.text_input("📱 رقم الهاتف", max_chars=10, key="phone1", placeholder="0612345678")
        
        if phone2_needed:
            st.markdown(f"<p style='font-size:20px; font-weight:700; margin-top:1.5rem;'>👤 {st.session_state.student2['اللقب']} {st.session_state.student2['الإسم']}</p>", unsafe_allow_html=True)
            phone_input2 = st.text_input("📱 رقم الهاتف", max_chars=10, key="phone2", placeholder="0712345678")
        
        if st.button("✅ تأكيد", type="primary", use_container_width=True):
            all_valid = True
            
            if needs_phone1:
                valid1, msg1 = validate_phone(phone_input1)
                if not valid1:
                    st.markdown(f'<div class="error-msg">{msg1}</div>', unsafe_allow_html=True)
                    all_valid = False
                else:
                    if not update_student_phone(st.session_state.student1['اسم المستخدم'], phone_input1):
                        st.markdown('<div class="error-msg">❌ خطأ في حفظ رقم الهاتف</div>', unsafe_allow_html=True)
                        all_valid = False
            
            if phone2_needed and all_valid:
                valid2, msg2 = validate_phone(phone_input2)
                if not valid2:
                    st.markdown(f'<div class="error-msg">{msg2}</div>', unsafe_allow_html=True)
                    all_valid = False
                else:
                    if not update_student_phone(st.session_state.student2['اسم المستخدم'], phone_input2):
                        st.markdown('<div class="error-msg">❌ خطأ في حفظ رقم الهاتف</div>', unsafe_allow_html=True)
                        all_valid = False
            
            if all_valid:
                st.session_state.phone_collected = True
                clear_cache()
                
                # إعادة تحميل بيانات الطلبة
                df_students_fresh = load_students()
                st.session_state.student1 = df_students_fresh[
                    df_students_fresh["اسم المستخدم"].astype(str).str.strip() == st.session_state.student1['اسم المستخدم'].strip()
                ].iloc[0]
                
                if st.session_state.student2 is not None:
                    st.session_state.student2 = df_students_fresh[
                        df_students_fresh["اسم المستخدم"].astype(str).str.strip() == st.session_state.student2['اسم المستخدم'].strip()
                    ].iloc[0]
                
                st.session_state.page = "student_space"
                st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)

# ---------------- فضاء الأستاذ ----------------
elif st.session_state.page == "professor_dashboard" and st.session_state.logged_in:
    
    prof = st.session_state.professor
    prof_name = str(prof['الأستاذ']).strip()
    prof_username = str(prof['إسم المستخدم']).strip()
    
    # رأس الصفحة
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown(f'<h1 style="font-size:42px; margin-bottom:0;">👨‍🏫 مرحباً الأستاذ(ة) {prof_name}</h1>', unsafe_allow_html=True)
    with col2:
        if st.button("🚪 خروج", key="logout_prof", use_container_width=True):
            logout()
    
    st.markdown("---")
    
    # تحميل بيانات المذكرات
    df_memos_fresh = load_memos()
    df_prof_memos_fresh = load_prof_memos()
    
    # جمع إحصائي