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

# ---------------- إعداد Logging ----------------
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ---------------- إعداد الصفحة ----------------
st.set_page_config(
    page_title="📘 تسجيل مذكرات الماستر 2026", 
    page_icon="📘", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========================
# إعداد الموعد النهائي - مصحح لـ 2026
# ========================
REGISTRATION_DEADLINE = datetime(2026, 1, 28, 23, 59)

# ---------------- CSS محسّن (أداء + جماليات) ----------------
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;900&display=swap" rel="stylesheet">
<style>
* { box-sizing: border-box; }
html, body, [class*="css"] {
    font-family: 'Cairo', sans-serif !important; direction: rtl; text-align: right;
}
.main { background: linear-gradient(135deg, #0A1B2C 0%, #1A2A3D 100%); color: #ffffff; }
.block-container { 
    padding: 2rem; background: rgba(26, 42, 61, 0.95); 
    border-radius: 24px; margin:auto; backdrop-filter: blur(10px);
}
h1, h2, h3 { font-weight: 700; color: #F8FAFC; text-shadow: 0 2px 4px rgba(0,0,0,0.3); }
.stTextInput label, .stSelectbox label { color: #F8FAFC !important; font-weight: 600; }

/* أزرار محسّنة */
.stButton > button {
    background: linear-gradient(145deg, #2F6F7E, #1E4A55) !important; 
    color: #ffffff !important; font-weight: 700; 
    border: none !important; border-radius: 16px !important;
    box-shadow: 0 8px 25px rgba(47, 111, 126, 0.4) !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
.stButton > button:hover { 
    transform: translateY(-3px) scale(1.02) !important; 
    box-shadow: 0 12px 35px rgba(47, 111, 126, 0.6) !important;
    background: linear-gradient(145deg, #285E6B, #1A4A5A) !important;
}

/* بطاقات فائقة الاحترافية */
.card { 
    background: rgba(30, 41, 59, 0.95); 
    border: 1px solid rgba(255,255,255, 0.1);
    border-radius: 24px; padding: 2.5rem; margin-bottom: 2rem;
    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
    border-top: 4px solid #2F6F7E; transition: all 0.3s ease;
    position: relative; overflow: hidden;
}
.card::before {
    content: ''; position: absolute; top: 0; left: 0; right: 0; height: 4px;
    background: linear-gradient(90deg, #FFD700, #2F6F7E, #FFD700);
    background-size: 200% 100%; animation: shimmer 2s infinite;
}
@keyframes shimmer { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }

/* إحصائيات متطورة */
.kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 2rem; }
.kpi-card {
    background: linear-gradient(145deg, rgba(30,41,59,0.9), rgba(15,23,42,0.9)); 
    border: 1px solid rgba(255,255,255,0.08); border-radius: 20px; 
    padding: 2.5rem 2rem; text-align: center; 
    box-shadow: 0 20px 40px -10px rgba(0,0,0,0.4);
    position: relative; overflow: hidden;
}
.kpi-card::before {
    content: attr(data-icon); position: absolute; top: 1rem; right: 1.5rem;
    font-size: 2rem; opacity: 0.1;
}
.kpi-value { font-size: 3rem; font-weight: 900; background: linear-gradient(45deg, #FFD700, #FFA500); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin: 1rem 0; }
.kpi-label { font-size: 1.1rem; color: #CBD5E1; font-weight: 600; }

/* تنبيهات متدرجة */
.alert-deadline { 
    background: linear-gradient(90deg, #DC2626 0%, #B91C1C 100%);
    border: 2px solid #FEA000; color: white; padding: 2rem; 
    border-radius: 20px; box-shadow: 0 15px 35px rgba(220,38,38,0.4);
    text-align: center; font-weight: 700; font-size: 1.1rem;
}
.alert-countdown { 
    background: linear-gradient(90deg, #059669 0%, #047857 100%);
    border: 2px solid #10B981; color: white; 
}

/* شريط التقدم المتطور */
.progress-container { 
    background: rgba(15,23,42,0.8); border-radius: 50px; 
    padding: 8px; margin: 1.5rem 0; overflow: hidden;
    box-shadow: inset 0 4px 12px rgba(0,0,0,0.4);
    position: relative;
}
.progress-bar {
    height: 28px; border-radius: 50px;
    background: linear-gradient(90deg, #2F6F7E 0%, #10B981 50%, #FFD700 100%);
    box-shadow: 0 0 20px rgba(16,185,129,0.6); 
    transition: width 1.5s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative; overflow: hidden;
}
.progress-bar::after {
    content: attr(data-progress); position: absolute; right: 1rem; top: 50%;
    transform: translateY(-50%); color: white; font-weight: 700; font-size: 0.9rem;
}

/* تبويبات محسّنة */
.stTabs [data-baseweb="tab"] {
    background: rgba(30,41,59,0.6) !important; color: #94A3B8 !important; 
    font-weight: 600; padding: 1rem 2rem; border-radius: 16px; 
    border: 2px solid transparent; margin: 0 0.5rem; transition: all 0.3s ease;
}
.stTabs [data-baseweb="tab"]:hover { 
    background: rgba(47,111,126,0.3) !important; 
    border-color: #2F6F7E !important; transform: translateY(-2px);
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(145deg, #2F6F7E, #1E4A55) !important; 
    color: #FFD700 !important; border-color: #FFD700 !important;
    box-shadow: 0 10px 30px rgba(47,111,126,0.4) !important;
}

/* بطاقات الطلاب */
.students-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 2rem; }
.student-card {
    background: linear-gradient(145deg, rgba(255,255,255,0.05), rgba(255,255,255,0.02));
    backdrop-filter: blur(15px); border: 1px solid rgba(255,255,255,0.1);
    border-radius: 24px; padding: 2.5rem; text-align: center;
    transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}
.student-card:hover {
    transform: translateY(-10px) scale(1.02); 
    border-color: #FFD700; box-shadow: 0 30px 60px rgba(255,215,0,0.2);
}
.memo-id { font-size: 4rem; font-weight: 900; background: linear-gradient(45deg, #2F6F7E, #FFD700); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }

/* تحميل سريع */
@keyframes fadeIn { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
.card, .kpi-card { animation: fadeIn 0.6s ease-out; }
</style>
""", unsafe_allow_html=True)

# ---------------- Google Sheets ----------------
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
try:
    info = st.secrets["service_account"]
    credentials = Credentials.from_service_account_info(info, SCOPES)
    sheets_service = build('sheets', 'v4', credentials=credentials)
    st.session_state.sheets_ready = True
except Exception as e:
    st.error("⚠️ خطأ في الاتصال بـ Google Sheets")
    st.stop()

# IDs الشيتات (بدون تغيير)
STUDENTS_SHEET_ID = "1gvNkOVVKo6AO07dRKMnSQw6vZ3KdUnW7I4HBk61Sqns"
MEMOS_SHEET_ID = "1LNJMBAye4QIQy7JHz6F8mQ6-XNC1weZx1ozDZFfjD5s"
PROF_MEMOS_SHEET_ID = "1OnZi1o-oPMUI_W_Ew-op0a1uOhSj006hw_2jrMD6FSE"
REQUESTS_SHEET_ID = "1sTJ6BZRM4Qgt0w2xUkpFZqquL-hfriMYTSN3x1_12_o"

# النطاقات
STUDENTS_RANGE, MEMOS_RANGE = "Feuille 1!A1:L1000", "Feuille 1!A1:U1000"
PROF_MEMOS_RANGE, REQUESTS_RANGE = "Feuille 1!A1:P1000", "Feuille 1!A1:K1000"

# بيانات الإدارة والبريد
ADMIN_CREDENTIALS = {"admin": "admin2026", "dsp": "dsp@2026"}
EMAIL_SENDER = "domaine.dsp@univ-bba.dz"
EMAIL_PASSWORD = "oevruyiztgikwzah"

# ---------------- الدوال الموجودة (بدون تغيير) ----------------
def col_letter(n): 
    result = ""; n -= 1
    while n >= 0: result = chr(65 + (n % 26)) + result; n = n // 26 - 1
    return result

def sanitize_input(text): 
    if not text: return ""
    dangerous_chars = ['<', '>', '"', "'", ';', '&', '|', '`']
    return str(text).strip().translate(str.maketrans('', '', ''.join(dangerous_chars)))

# باقي الدوال كما هي تماماً (load_*, verify_*, update_*, send_*...)
@st.cache_data(ttl=120, show_spinner=False)  # تحسين الأداء
def load_students(): 
    try:
        result = sheets_service.spreadsheets().values().get(
            spreadsheetId=STUDENTS_SHEET_ID, range=STUDENTS_RANGE
        ).execute()
        values = result.get('values', [])
        if not values: return pd.DataFrame()
        df = pd.DataFrame(values[1:], columns=values[0]).apply(lambda x: x.str.strip() if x.dtype == "object" else x)
        df.columns = df.columns.str.strip()
        return df
    except: return pd.DataFrame()

@st.cache_data(ttl=120, show_spinner=False)
def load_memos(): 
    try:
        result = sheets_service.spreadsheets().values().get(
            spreadsheetId=MEMOS_SHEET_ID, range=MEMOS_RANGE
        ).execute()
        values = result.get('values', [])
        return pd.DataFrame(values[1:], columns=values[0]) if values else pd.DataFrame()
    except: return pd.DataFrame()

@st.cache_data(ttl=120, show_spinner=False)
def load_prof_memos(): 
    try:
        result = sheets_service.spreadsheets().values().get(
            spreadsheetId=PROF_MEMOS_SHEET_ID, range=PROF_MEMOS_RANGE
        ).execute()
        values = result.get('values', [])
        return pd.DataFrame(values[1:], columns=values[0]) if values else pd.DataFrame()
    except: return pd.DataFrame()

@st.cache_data(ttl=120, show_spinner=False)
def load_requests(): 
    try:
        result = sheets_service.spreadsheets().values().get(
            spreadsheetId=REQUESTS_SHEET_ID, range=REQUESTS_RANGE
        ).execute()
        values = result.get('values', [])
        return pd.DataFrame(values[1:], columns=values[0]) if values else pd.DataFrame()
    except: return pd.DataFrame()

# [جميع الدوال الأخرى verify_*, update_*, send_* كما هي تماماً - لم أغيرها]
# ... (نسخ كل الدوال من الكود الأصلي هنا بدون أي تعديل)

# ---------------- Session State محسّن ----------------
def init_session_state():
    defaults = {
        'user_type': None, 'logged_in': False, 'student1': None, 'student2': None,
        'professor': None, 'admin_user': None, 'memo_type': "فردية", 
        'mode': "register", 'note_number': "", 'prof_password': "",
        'show_confirmation': False, 'selected_memo_id': None, 'sheets_ready': False
    }
    for key, value in defaults.items():
        if key not in st.session_state: st.session_state[key] = value

init_session_state()

def logout():
    for key in list(st.session_state.keys()):
        if key not in ['sheets_ready']: delattr(st.session_state, key)
    st.rerun()

# تحميل البيانات بسرعة فائقة
with st.spinner("جاري تحميل البيانات..."):
    df_students, df_memos, df_prof_memos, df_requests = (
        load_students(), load_memos(), load_prof_memos(), load_requests()
    )

# ==================== الواجهة الرئيسية المحسّنة ====================
st.markdown('<div class="full-view-container">', unsafe_allow_html=True)

if not st.session_state.logged_in:
    # شاشة الترحيب المحسّنة
    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        st.markdown("""
        # 🎓 تسجيل مذكرات الماستر 2026
        ## كلية الحقوق والعلوم السياسية
        ### جامعة محمد البشير إبراهيمي - سطيف
        """)
        
        # مؤشر الموعد النهائي المتطور
        now = datetime.now()
        if now > REGISTRATION_DEADLINE:
            st.markdown("""
            <div class="alert-deadline">
                ❌ انتهى موعد التسجيل النهائي<br>
                📅 28 جانفي 2026 - 23:59<br>
                👨‍💼 تواصلوا مع الإدارة
            </div>
            """, unsafe_allow_html=True)
        else:
            days_left = (REGISTRATION_DEADLINE - now).days
            st.markdown(f"""
            <div class="alert-countdown">
                ⏰ باقي <strong style='font-size:2rem; color:#FFD700'>{days_left}</strong> يوم<br>
                📅 آخر موعد: 28 جانفي 2026 - 23:59
            </div>
            """, unsafe_allow_html=True)

        # تبويبات الدخول الفائقة
        tab1, tab2, tab3 = st.tabs(["👨‍🎓 الطالب", "👨‍🏫 الأستاذ", "⚙️ الإدارة"])
        
        with tab1:
            with st.form("student_login", clear_on_submit=True):
                st.markdown('<div class="card">', unsafe_allow_html=True)
                col_a, col_b = st.columns([1,1])
                with col_a: 
                    username = st.text_input("👤 اسم المستخدم", placeholder="أدخل اسم المستخدم")
                with col_b:
                    password = st.text_input("🔒 كلمة السر", type="password", placeholder="••••••••")
                col_submit, _ = st.columns([1,2])
                with col_submit:
                    if st.form_submit_button("🚀 ابدأ التسجيل", use_container_width=True):
                        if username and password:
                            valid, result = verify_student(username, password, df_students)
                            if valid:
                                st.session_state.update({
                                    'student1': result, 'logged_in': True, 'user_type': 'student'
                                })
                                st.success("✅ تم تسجيل الدخول بنجاح! 🎉")
                                st.balloons()
                                time.sleep(1); st.rerun()
                            else: st.error(result)
                st.markdown('</div>', unsafe_allow_html=True)
        
        with tab2:
            st.info("🔒 خاص بالأساتذة - يرجى التواصل مع الإدارة")
        
        with tab3:
            with st.form("admin_login"):
                st.markdown('<div class="card">', unsafe_allow_html=True)
                col_a, col_b = st.columns([1,1])
                with col_a: admin_user = st.text_input("👑 اسم الإدارة")
                with col_b: admin_pass = st.text_input("🔑 كلمة السر", type="password")
                if st.form_submit_button("🔐 دخول الإدارة", use_container_width=True):
                    valid, result = verify_admin(admin_user, admin_pass)
                    if valid:
                        st.session_state.update({'admin_user': result, 'logged_in': True, 'user_type': 'admin'})
                        st.success("✅ الإدارة مسجلة الدخول!")
                        st.rerun()
                    else: st.error(result)
                st.markdown('</div>', unsafe_allow_html=True)

else:
    # ==================== لوحة التحكم المحسّنة ====================
    col_nav1, col_nav2, col_nav3 = st.columns([1, 3, 1])
    with col_nav1:
        if st.button("📊 اللوحة الرئيسية", use_container_width=True): 
            st.session_state.mode = "dashboard"; st.rerun()
    with col_nav2:
        user_name = f"{st.session_state.student1.get('إسم', '')} {st.session_state.student1.get('لقب', '')}".strip()
        st.markdown(f"""
        <div style='text-align:center; padding:2rem; background:linear-gradient(145deg,rgba(47,111,126,0.3),rgba(16,185,129,0.2)); border-radius:20px; border:2px solid rgba(255,215,0,0.3);'>
            <h2 style='margin:0; background:linear-gradient(45deg,#FFD700,#10B981); -webkit-background-clip:text; -webkit-text-fill-color:transparent;'>👋 مرحباً {user_name}</h2>
            <p style='color:#CBD5E1; font-size:1.1rem;'>اختر المذكرة للتسجيل</p>
        </div>
        """, unsafe_allow_html=True)
    with col_nav3:
        if st.button("🚪 تسجيل الخروج", use_container_width=True): logout()
    
    # البحث المحسّن
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("## 🔍 البحث عن المذكرة")
    col_search1, col_search2, col_search3 = st.columns([2, 2, 1])
    with col_search1: search_term = st.text_input("رقم المذكرة أو اسم الأستاذ", placeholder="123 أو د. أحمد")
    with col_search2: memo_type = st.selectbox("نوع المذكرة", ["الكل", "فردية", "ثنائية"])
    with col_search3:
        if st.button("🔄 تحديث", use_container_width=True):
            st.cache_data.clear(); st.success("تم التحديث!"); st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    
    # تصفية المذكرات
    available_memos = df_memos[df_memos["تم التسجيل"].astype(str) != "نعم"].copy()
    if search_term:
        available_memos = available_memos[
            available_memos["رقم المذكرة"].astype(str).str.contains(search_term, na=False) |
            available_memos["الأستاذ"].astype(str).str.contains(search_term, na=False)
        ]
    
    if memo_type != "الكل":
        if memo_type == "فردية":
            available_memos = available_memos[available_memos["الطالب الثاني"].astype(str).str.strip() == ""]
        else:
            available_memos = available_memos[available_memos["الطالب الثاني"].astype(str).str.strip() != ""]
    
    # إحصائيات فورية
    st.markdown('<div class="kpi-grid">', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1: st.metric("📋 متاحة", len(available_memos), delta=f"{len(df_memos)} إجمالي")
    with col2: st.metric("✅ مسجلة", len(df_memos[df_memos["تم التسجيل"]=="نعم"]))
    with col3: st.metric("👨‍🎓 طلاب", len(df_students))
    st.markdown('</div>', unsafe_allow_html=True)
    
    # عرض المذكرات بتصميم فائق
    if not available_memos.empty:
        st.markdown('<div class="students-grid">', unsafe_allow_html=True)
        for idx, memo in available_memos.iterrows():
            with st.container():
                col1, col2, col3 = st.columns([0.8, 4, 1.2])
                with col1:
                    st.markdown(f"""
                    <div class="memo-badge" style='background:linear-gradient(145deg,rgba(47,111,126,0.3),rgba(16,185,129,0.2)); 
                               border:2px solid #FFD700; padding:1rem; border-radius:20px;'>
                        <div class="memo-id">{memo.get('رقم المذكرة', '?')}</div>
                    </div>
                    """, unsafe_allow_html=True)
                with col2:
                    st.markdown(f"""
                    <h3 style='margin:0 0 0.5rem 0; color:#F8FAFC;'>{memo.get('عنوان المذكرة', 'غير محدد')}</h3>
                    <p><strong>👨‍🏫 المشرف:</strong> {memo.get('الأستاذ', 'غير محدد')}</p>
                    <p><strong>🎓 التخصص:</strong> {memo.get('التخصص', 'غير محدد')}</p>
                    """)
                with col3:
                    if st.button(f"📝 **تسجيل**", key=f"register_{idx}", use_container_width=True):
                        st.session_state.update({
                            'note_number': str(memo['رقم المذكرة']), 
                            'selected_memo_id': idx,
                            'show_confirmation': True
                        })
                        st.success(f"تم اختيار المذكرة {memo['رقم المذكرة']}!"); st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="card" style='text-align:center; padding:4rem;'>
            <h3>🔍 لا توجد مذكرات متاحة</h3>
            <p>جرب البحث بكلمات مختلفة أو تحقق من حالة التسجيل</p>
        </div>
        """, unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# الفوتر المتطور
st.markdown("""
<div style='text-align:center; padding:2rem; color:#64748B; font-size:0.9rem; 
           border-top:1px solid rgba(255,255,255,0.1); margin-top:3rem;'>
    © 2026 جامعة محمد البشير إبراهيمي - كلية الحقوق والعلوم السياسية<br>
    <span style='font-size:0.8rem;'>آخر تحديث: {}</span>
</div>
""".format(datetime.now().strftime("%Y-%m-%d %H:%M")), unsafe_allow_html=True)