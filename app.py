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
    border: 1px solid rgba(255, 255, 255, 0.08);
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
.stDataFrame { border-radius: 12px; overflow: hidden; border: 1px solid rgba(255, 255, 255, 0.1); background: #1E293B; }
.stDataFrame th { background-color: #0F172A; color: #FFD700; font-weight: bold; }

/* التبويبات - بدون فواصل زرقاء */
.stTabs [data-baseweb="tab-list"] { gap: 2rem; padding-bottom: 15px; border-bottom: none; }
.stTabs [data-baseweb="tab"] { 
    background: transparent; color: #94A3B8; 
    font-weight: 600; padding: 12px 24px; border-radius: 12px; border: 1px solid transparent;
}
.stTabs [data-baseweb="tab"]:hover { background: rgba(255, 255, 255, 0.1); color: white; }
.stTabs [aria-selected="true"] { 
    background: rgba(47, 111, 126, 0.2); color: #FFD700; border: 1px solid #2F6F7E; font-weight: bold; box-shadow: 0 0 15px rgba(47, 111, 126, 0.2);
}

/* إزالة الفواصل الزرقاء */
.stDivider { display: none !important; }
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
# إضافة شيت الطلبات الجديد
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

def validate_username(username):
    username = sanitize_input(username)
    if not username: return False, "⚠️ اسم المستخدم فارغ"
    return True, username

def validate_note_number(note_number):
    note_number = sanitize_input(note_number)
    if not note_number: return False, "⚠️ رقم المذكرة فارغ"
    if len(note_number) > 20: return False, "⚠️ رقم المذكرة غير صالح"
    return True, note_number

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

# ============================================================
# دالة إضافة طلب جديد
# ============================================================
def add_request(memo_number, request_type, request_content, student_email):
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        new_request = [[timestamp, memo_number, request_type, request_content, student_email, ""]]
        
        sheets_service.spreadsheets().values().append(
            spreadsheetId=REQUESTS_SHEET_ID,
            range=REQUESTS_RANGE,
            valueInputOption="USER_ENTERED",
            body={"values": new_request}
        ).execute()
        
        time.sleep(1)
        clear_cache_and_reload()
        return True, "✅ تم إرسال الطلب بنجاح"
    except Exception as e:
        logger.error(f"خطأ في إضافة الطلب: {str(e)}")
        return False, f"❌ حدث خطأ: {str(e)}"

# ============================================================
# دالة التحقق من الطلاب
# ============================================================
def verify_students_batch(students_data, df_students):
    verified = []
    for username, password in students_data:
        student = df_students[df_students["اسم المستخدم"].astype(str).str.strip() == username.strip()]
        if student.empty:
            return False, f"❌ الطالب '{username}' غير موجود"
        
        student_row = student.iloc[0]
        stored_password = str(student_row.get("كلمة السر", "")).strip()
        if stored_password != password.strip():
            return False, f"❌ كلمة السر غير صحيحة للطالب '{username}'"
        
        verified.append(student_row)
    
    return True, verified

def verify_admin(username, password):
    if username in ADMIN_CREDENTIALS and ADMIN_CREDENTIALS[username] == password:
        return True, username
    return False, "❌ بيانات الدخول غير صحيحة"

# ============================================================
# دالة إرسال البريد الإلكتروني
# ============================================================
def send_email_to_professor(prof_email, prof_name, memo_data, student1, student2=None):
    try:
        subject = f"تسجيل جديد للمذكرة: {memo_data.get('رقم المذكرة', '')}"
        
        s1_name = f"{student1.get('لقب', student1.get('اللقب', ''))} {student1.get('الإسم', student1.get('إسم', ''))}"
        s2_name = f"{student2.get('لقب', student2.get('اللقب', ''))} {student2.get('الإسم', student2.get('إسم', ''))}" if student2 is not None else ""
        
        body = f"""
        السلام عليكم ورحمة الله وبركاته
        
        تم تسجيل مذكرة جديدة على اسمك:
        
        رقم المذكرة: {memo_data.get('رقم المذكرة', '')}
        العنوان: {memo_data.get('عنوان المذكرة', '')}
        الطالب الأول: {s1_name}
        الطالب الثاني: {s2_name if s2_name else 'لا يوجد'}
        
        يرجى متابعة تقدم المذكرة من خلال النظام.
        """
        
        msg = MIMEMultipart()
        msg['From'] = EMAIL_SENDER
        msg['To'] = prof_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        
        logger.info(f"تم إرسال بريد إلى {prof_email}")
    except Exception as e:
        logger.error(f"خطأ في إرسال البريد: {str(e)}")

# ============================================================
# Session State
# ============================================================
if 'user_type' not in st.session_state:
    st.session_state.user_type = None
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
    st.session_state.selected_memo = None

def logout():
    for key in st.session_state.keys():
        if key not in ['user_type']: del st.session_state[key]
    st.session_state.update({
        'logged_in': False, 'student1': None, 'student2': None, 'professor': None,
        'admin_user': None, 'mode': "register", 'note_number': "", 'prof_password': "", 'show_confirmation': False,
        'user_type': None, 'selected_memo': None
    })
    st.rerun()

df_students = load_students()
df_memos = load_memos()
df_prof_memos = load_prof_memos()
df_requests = load_requests()

if df_students.empty or df_memos.empty or df_prof_memos.empty:
    st.error("❌ خطأ في تحميل البيانات. يرجى المحاولة لاحقاً.")
    st.stop()

# ============================================================
# الصفحة الرئيسية (اختيار الفضاء)
# ============================================================
if st.session_state.user_type is None:
    st.markdown("<h1 style='text-align: center; margin-bottom: 1rem;'>نظام تسجيل المذكرات</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #94A3B8; font-size: 1.2rem; margin-bottom: 2rem;'>جامعة محمد البشير الإبراهيمي - كلية الحقوق والعلوم السياسية</p>", unsafe_allow_html=True)

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
                        
                        if s1_spec != s2_spec: 
                            st.error("❌ لا يمكن التسجيل الثنائي. الطالبان في تخصصين مختلفين")
                            st.session_state.logged_in = False
                            st.stop()
                        if (s1_note and not s2_note) or (not s1_note and s2_note): 
                            st.error("❌ أحد الطالبين مسجل مسبقاً")
                            st.session_state.logged_in = False
                            st.stop()
                        if s1_note and s2_note and s1_note != s2_note: 
                            st.error(f"❌ الطالبان مسجلان في مذكرتين مختلفتين")
                            st.session_state.logged_in = False
                            st.stop()
                        if s1_note and s2_note and s1_note == s2_note: 
                            st.session_state.mode = "view"
                            st.session_state.logged_in = True
                            st.rerun()
                    
                    if st.session_state.memo_type == "فردية":
                        fardiya_val = str(st.session_state.student1.get('فردية', '')).strip()
                        if fardiya_val not in ["1", "نعم"]: 
                            st.error("❌ لا يمكنك تسجيل مذكرة فردية")
                            st.stop()
                    
                    note_num = str(st.session_state.student1.get('رقم المذكرة', '')).strip()
                    st.session_state.mode = "view" if note_num else "register"
                    st.session_state.logged_in = True
                    st.rerun()
    
    else:
        s1 = st.session_state.student1
        s2 = st.session_state.student2
        col1, col2 = st.columns([4, 1])
        with col2:
            if st.button("خروج", key="logout_btn"):
                logout()
        
        st.markdown(f'<div class="card"><h3>ملف الطالب</h3><p>الطالب الأول: <b style="color:#2F6F7E;">{s1["لقب"] if "لقب" in s1 else s1["اللقب"]} {s1["الإسم"] if "الإسم" in s1 else s1["إسم"]}</b></p><p>التخصص: <b>{s1["التخصص"]}</b></p></div>', unsafe_allow_html=True)
        
        if s2 is not None:
            st.markdown(f'<p style="color:#94A3B8;">الطالب الثاني: <b style="color:#2F6F7E;">{s2["لقب"] if "لقب" in s2 else s2["اللقب"]} {s2["الإسم"] if "الإسم" in s2 else s2["إسم"]}</b></p>', unsafe_allow_html=True)
        
        if st.session_state.mode == "register":
            st.markdown("<h3>تسجيل مذكرة جديدة</h3>", unsafe_allow_html=True)
            # سيتم إضافة نموذج التسجيل هنا
        else:
            st.markdown("<h3>عرض المذكرة المسجلة</h3>", unsafe_allow_html=True)
            note_num = str(s1.get('رقم المذكرة', '')).strip()
            if note_num:
                memo = df_memos[df_memos["رقم المذكرة"].astype(str).str.strip() == note_num]
                if not memo.empty:
                    m = memo.iloc[0]
                    st.markdown(f'<div class="card"><h4>{m["رقم المذكرة"]}</h4><p><b>العنوان:</b> {m["عنوان المذكرة"]}</p><p><b>الأستاذ:</b> {m["الأستاذ"]}</p></div>', unsafe_allow_html=True)

# ============================================================
# فضاء الأساتذة - محدث
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
            prof_name = st.text_input("اسم الأستاذ")
            prof_password = st.text_input("كلمة السر", type="password")
            submitted = st.form_submit_button("تسجيل الدخول")
            
            if submitted:
                prof_data = df_prof_memos[df_prof_memos["الأستاذ"].astype(str).str.strip() == prof_name.strip()]
                if prof_data.empty:
                    st.error("❌ الأستاذ غير موجود")
                else:
                    stored_password = str(prof_data.iloc[0].get("كلمة السر", "")).strip()
                    if stored_password != prof_password.strip():
                        st.error("❌ كلمة السر غير صحيحة")
                    else:
                        st.session_state.professor = prof_data.iloc[0]
                        st.session_state.logged_in = True
                        st.rerun()
    
    else:
        prof = st.session_state.professor
        col1, col2 = st.columns([4, 1])
        with col2:
            if st.button("خروج", key="logout_prof"):
                logout()
        
        st.markdown(f"<h2>مرحباً بك، أ.د {prof['الأستاذ']}</h2>", unsafe_allow_html=True)
        
        # التبويبات الجديدة بالترتيب المطلوب
        tab1, tab2, tab3 = st.tabs(["المذكرات المسجلة", "كلمات السر", "المذكرات المتاحة"])
        
        with tab1:
            st.subheader("المذكرات المسجلة")
            prof_memos = df_memos[df_memos["الأستاذ"].astype(str).str.strip() == prof['الأستاذ'].strip()]
            registered_memos = prof_memos[prof_memos["تم التسجيل"].astype(str).str.strip() == "نعم"]
            
            if not registered_memos.empty:
                # قائمة اختيار (Combo Box) للمذكرات المسجلة
                memo_options = [f"{m['رقم المذكرة']} - {m['عنوان المذكرة']}" for _, m in registered_memos.iterrows()]
                selected_memo_display = st.selectbox("اختر المذكرة:", memo_options, key="registered_memo_select")
                
                if selected_memo_display:
                    # استخراج رقم المذكرة من الخيار المختار
                    memo_num = selected_memo_display.split(" - ")[0]
                    selected_memo = registered_memos[registered_memos["رقم المذكرة"].astype(str).str.strip() == memo_num].iloc[0]
                    st.session_state.selected_memo = selected_memo
                    
                    # عرض تفاصيل المذكرة بملء الشاشة
                    st.markdown(f'''
                    <div class="card">
                        <h3>{selected_memo["رقم المذكرة"]}</h3>
                        <p><b>العنوان:</b> {selected_memo["عنوان المذكرة"]}</p>
                        <p><b>الطالب الأول:</b> {selected_memo["الطالب الأول"]}</p>
                        <p><b>البريد الإلكتروني:</b> {selected_memo.get("البريد الإلكتروني للطالب الأول", "غير متوفر")}</p>
                    ''', unsafe_allow_html=True)
                    
                    if str(selected_memo.get("الطالب الثاني", "")).strip():
                        st.markdown(f'<p><b>الطالب الثاني:</b> {selected_memo["الطالب الثاني"]}</p>', unsafe_allow_html=True)
                        st.markdown(f'<p><b>البريد الإلكتروني:</b> {selected_memo.get("البريد الإلكتروني للطالب الثاني", "غير متوفر")}</p>', unsafe_allow_html=True)
                    
                    st.markdown(f'<p><b>التخصص:</b> {selected_memo["التخصص"]}</p>', unsafe_allow_html=True)
                    st.markdown(f'<p><b>نسبة التقدم:</b> {selected_memo.get("نسبة التقدم", "0")}%</p>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    # الطلبات المرتبطة بهذه المذكرة
                    st.markdown("<h4>الطلبات المتعلقة بهذه المذكرة</h4>", unsafe_allow_html=True)
                    
                    memo_requests = df_requests[df_requests["رقم المذكرة"].astype(str).str.strip() == memo_num]
                    
                    if not memo_requests.empty:
                        for _, req in memo_requests.iterrows():
                            st.markdown(f'''
                            <div class="card" style="border-left: 4px solid #FFD700;">
                                <p><b>نوع الطلب:</b> {req.get("نوع الطلب", "")}</p>
                                <p><b>التفاصيل:</b> {req.get("تفاصيل الطلب", "")}</p>
                                <p style="color:#94A3B8; font-size:0.9rem;">التاريخ: {req.get("التاريخ", "")}</p>
                            </div>
                            ''', unsafe_allow_html=True)
                    else:
                        st.info("لا توجد طلبات لهذه المذكرة حالياً")
                    
                    # إضافة طلب جديد
                    st.markdown("<h4>إضافة طلب جديد</h4>", unsafe_allow_html=True)
                    
                    request_type = st.selectbox("نوع الطلب:", ["تغيير العنوان", "إضافة طالب", "تعديل آخر"], key=f"request_type_{memo_num}")
                    
                    if request_type == "تغيير العنوان":
                        new_title = st.text_input("العنوان الجديد:", key=f"new_title_{memo_num}")
                        if st.button("إرسال الطلب", key=f"submit_title_{memo_num}"):
                            if new_title:
                                success, msg = add_request(memo_num, "تغيير العنوان", new_title, prof['البريد الإلكتروني'])
                                st.success(msg) if success else st.error(msg)
                            else:
                                st.error("يرجى إدخال العنوان الجديد")
                    
                    elif request_type == "إضافة طالب":
                        student_name = st.text_input("لقب واسم الطالب الجديد:", key=f"new_student_{memo_num}")
                        if st.button("إرسال الطلب", key=f"submit_student_{memo_num}"):
                            if student_name:
                                success, msg = add_request(memo_num, "إضافة طالب", student_name, prof['البريد الإلكتروني'])
                                st.success(msg) if success else st.error(msg)
                            else:
                                st.error("يرجى إدخال اسم الطالب")
                    
                    else:
                        request_content = st.text_area("تفاصيل الطلب:", key=f"request_content_{memo_num}")
                        if st.button("إرسال الطلب", key=f"submit_request_{memo_num}"):
                            if request_content:
                                success, msg = add_request(memo_num, "تعديل آخر", request_content, prof['البريد الإلكتروني'])
                                st.success(msg) if success else st.error(msg)
                            else:
                                st.error("يرجى إدخال تفاصيل الطلب")
            else:
                st.info("لا توجد مذكرات مسجلة لك حالياً")
        
        with tab2:
            st.subheader("كلمات السر")
            st.info("يمكنك عرض كلمات السر الخاصة بمذكراتك هنا")
            # سيتم إضافة محتوى كلمات السر
        
        with tab3:
            st.subheader("المذكرات المتاحة للتسجيل")
            prof_memos = df_memos[df_memos["الأستاذ"].astype(str).str.strip() == prof['الأستاذ'].strip()]
            available_memos = prof_memos[prof_memos["تم التسجيل"].astype(str).str.strip() != "نعم"]
            
            if not available_memos.empty:
                for _, m in available_memos.iterrows():
                    st.markdown(f'''
                    <div class="card" style="border-left: 4px solid #64748B;">
                        <h4>{m['رقم المذكرة']}</h4>
                        <p>{m['عنوان المذكرة']}</p>
                        <p style="color:#94A3B8;">تخصص: {m['التخصص']}</p>
                    </div>
                    ''', unsafe_allow_html=True)
            else:
                st.success("✅ جميع المذكرات مسجلة!")

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
                if not v:
                    st.error(r)
                else:
                    st.session_state.admin_user = r
                    st.session_state.logged_in = True
                    st.rerun()
    else:
        col1, col2 = st.columns([4, 1])
        with col2:
            if st.button("خروج"):
                logout()
        st.header("📊 لوحة تحكم الإدارة")
        
        # --- Stats ---
        st_s = len(df_students)
        t_m = len(df_memos)
        r_m = len(df_memos[df_memos["تم التسجيل"].astype(str).str.strip() == "نعم"])
        a_m = t_m - r_m
        t_p = len(df_prof_memos["الأستاذ"].unique())
        reg_st = df_students["رقم المذكرة"].notna().sum()
        unreg_st = st_s - reg_st
        
        st.markdown('<div class="kpi-grid">', unsafe_allow_html=True)
        st.markdown(f'''
            <div class="kpi-card">
                <div class="kpi-value">{st_s}</div>
                <div class="kpi-label">الطلاب</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-value">{t_p}</div>
                <div class="kpi-label">الأساتذة</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-value">{t_m}</div>
                <div class="kpi-label">إجمالي المذكرات</div>
            </div>
            <div class="kpi-card" style="border-color: #10B981;">
                <div class="kpi-value" style="color: #10B981;">{r_m}</div>
                <div class="kpi-label">مذكرات مسجلة</div>
            </div>
            <div class="kpi-card" style="border-color: #F59E0B;">
                <div class="kpi-value" style="color: #F59E0B;">{a_m}</div>
                <div class="kpi-label">مذكرات متاحة</div>
            </div>
            <div class="kpi-card" style="border-color: #10B981;">
                <div class="kpi-value" style="color: #10B981;">{reg_st}</div>
                <div class="kpi-label">طلاب مسجلين</div>
            </div>
            <div class="kpi-card" style="border-color: #F59E0B;">
                <div class="kpi-value" style="color: #F59E0B;">{unreg_st}</div>
                <div class="kpi-label">طلاب غير مسجلين</div>
            </div>
        ''', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # التبويبات الجديدة
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["المذكرات", "الطلاب", "الأساتذة", "تقارير", "تحديث", "إدارة الطلبات"])
        
        with tab1:
            st.subheader("جدول المذكرات")
            f_status = st.selectbox("تصفية:", ["الكل", "مسجلة", "متاحة"])
            if f_status == "الكل":
                d_memos = df_memos
            elif f_status == "مسجلة":
                d_memos = df_memos[df_memos["تم التسجيل"].astype(str).str.strip() == "نعم"]
            else:
                d_memos = df_memos[df_memos["تم التسجيل"].astype(str).str.strip() != "نعم"]
            
            st.dataframe(d_memos, use_container_width=True, height=400)

        with tab2:
            st.subheader("قائمة الطلاب")
            q = st.text_input("بحث (لقب/الاسم):")
            if q:
                f_st = df_students[df_students["لقب"].astype(str).str.contains(q, case=False, na=False) | df_students["الإسم"].astype(str).str.contains(q, case=False, na=False)]
                if "اللقب" in df_students.columns:
                     f_st = df_students[df_students["اللقب"].astype(str).str.contains(q, case=False, na=False) | df_students["الإسم"].astype(str).str.contains(q, case=False, na=False)]
                st.dataframe(f_st, use_container_width=True, height=400)
            else:
                st.dataframe(df_students, use_container_width=True, height=400)

        with tab3:
            st.subheader("توزيع الأساتذة")
            profs_list = sorted(df_memos["الأستاذ"].dropna().unique())
            sel_p = st.selectbox("اختر أستاذ:", ["الكل"] + profs_list)
            if sel_p != "الكل":
                if sel_p not in df_memos["الأستاذ"].values:
                    st.error("بيانات الأساتذة غير متاحة")
                else:
                    st.dataframe(df_memos[df_memos["الأستاذ"].astype(str).str.strip() == sel_p.strip()], use_container_width=True, height=400)
            else:
                s_df = df_memos.groupby("الأستاذ").agg({"رقم المذكرة":"count", "تم التسجيل": lambda x: (x.astype(str).str.strip() == "نعم").sum()}).rename(columns={"رقم المذكرة":"الإجمالي", "تم التسجيل":"المسجلة"})
                s_df["المتاحة"] = s_df["الإجمالي"] - s_df["المسجلة"]
                st.dataframe(s_df, use_container_width=True)

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
            st.subheader("تحديث البيانات")
            st.warning("⚠️ استخدم هذا الزر لتحديث البيانات من Google Sheets.")
            if st.button("تحديث البيانات من Google Sheets"):
                with st.spinner("جاري التحديث..."):
                    clear_cache_and_reload()
                    st.success("✅ تم التحديث")
                    st.rerun()
        
        with tab6:
            st.subheader("سجل الطلبات الواردة")
            st.dataframe(df_requests, use_container_width=True, height=500)
st.markdown("---")
st.markdown('<div style="text-align:center; color:#64748B; font-size:12px; padding:20px;">© 2026 جامعة محمد البشير الإبراهيمي - كلية الحقوق</div>', unsafe_allow_html=True)