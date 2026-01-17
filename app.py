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
import plotly.express as px
import plotly.graph_objects as go

# ---------------- إعداد Logging ----------------
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ---------------- إعداد الصفحة ----------------
st.set_page_config(page_title="نظام إدارة مذكرات الماستر", page_icon="🎓", layout="wide")

# ---------------- CSS المحسّن ----------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800&display=swap');

* {
    font-family: 'Cairo', sans-serif !important;
}

.main {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 0;
}

.stApp {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

/* بطاقة رئيسية */
.main-card {
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(10px);
    border-radius: 20px;
    padding: 40px;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
    margin: 20px auto;
    max-width: 1400px;
}

/* عنوان */
.hero-title {
    font-size: 3rem;
    font-weight: 800;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    text-align: center;
    margin-bottom: 10px;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
}

.hero-subtitle {
    text-align: center;
    color: #666;
    font-size: 1.2rem;
    margin-bottom: 30px;
}

/* أزرار الاختيار */
.role-selector {
    display: flex;
    gap: 30px;
    justify-content: center;
    margin: 40px 0;
}

.role-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 20px;
    padding: 40px;
    text-align: center;
    cursor: pointer;
    transition: all 0.3s ease;
    min-width: 250px;
    box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
}

.role-card:hover {
    transform: translateY(-10px);
    box-shadow: 0 20px 40px rgba(102, 126, 234, 0.5);
}

/* بطاقات الإحصائيات */
.stat-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 15px;
    padding: 25px;
    color: white;
    text-align: center;
    box-shadow: 0 8px 20px rgba(0, 0, 0, 0.2);
    transition: all 0.3s ease;
}

.stat-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 12px 30px rgba(0, 0, 0, 0.3);
}

.stat-number {
    font-size: 3rem;
    font-weight: 800;
    margin: 10px 0;
}

.stat-label {
    font-size: 1.1rem;
    opacity: 0.9;
}

/* أزرار */
.stButton > button {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    border-radius: 12px;
    padding: 15px 35px;
    font-size: 1.1rem;
    font-weight: 600;
    transition: all 0.3s ease;
    box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
}

.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(102, 126, 234, 0.6);
}

/* حقول الإدخال */
.stTextInput > div > div > input,
.stSelectbox > div > div > select {
    border-radius: 12px;
    border: 2px solid #e0e0e0;
    padding: 12px;
    font-size: 1rem;
    transition: all 0.3s ease;
}

.stTextInput > div > div > input:focus,
.stSelectbox > div > div > select:focus {
    border-color: #667eea;
    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

/* رسائل */
.success-box {
    background: linear-gradient(135deg, #84fab0 0%, #8fd3f4 100%);
    border-radius: 12px;
    padding: 20px;
    color: #065f46;
    margin: 20px 0;
    box-shadow: 0 5px 15px rgba(132, 250, 176, 0.3);
}

.error-box {
    background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
    border-radius: 12px;
    padding: 20px;
    color: #7f1d1d;
    margin: 20px 0;
    box-shadow: 0 5px 15px rgba(250, 112, 154, 0.3);
}

.info-box {
    background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
    border-radius: 12px;
    padding: 20px;
    color: #1e40af;
    margin: 20px 0;
    box-shadow: 0 5px 15px rgba(168, 237, 234, 0.3);
}

/* جدول المذكرات */
.dataframe {
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
}

/* شعار */
.logo-container {
    text-align: center;
    margin: 20px 0;
}

.university-name {
    font-size: 1.5rem;
    font-weight: 700;
    color: #667eea;
    margin: 10px 0;
}

/* Dashboard Cards */
.dashboard-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 20px;
    margin: 30px 0;
}

/* تحسين الـ tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 10px;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 12px;
    padding: 5px;
}

.stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    padding: 10px 20px;
    font-weight: 600;
}

.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
}

/* Footer */
.footer {
    text-align: center;
    padding: 20px;
    color: white;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 12px;
    margin-top: 40px;
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

STUDENTS_RANGE = "Feuille 1!A1:M1000"  # تم إضافة عمود M لرقم الهاتف
MEMOS_RANGE = "Feuille 1!A1:O1000"  # تم إضافة عمود O لنسبة التقدم
PROF_MEMOS_RANGE = "Feuille 1!A1:N1000"  # M: username, N: password

# ---------------- Email Configuration ----------------
EMAIL_SENDER = "domaine.dsp@univ-bba.dz"
EMAIL_PASSWORD = "oevruyiztgikwzah"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# ---------------- دوال مساعدة ----------------
def col_letter(n):
    """تحويل رقم العمود إلى حرف"""
    result = ""
    while n > 0:
        n, remainder = divmod(n - 1, 26)
        result = chr(65 + remainder) + result
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

def validate_phone(phone):
    """التحقق من صحة رقم الهاتف"""
    phone = sanitize_input(phone)
    if not phone:
        return False, "⚠️ رقم الهاتف مطلوب"
    if len(phone) < 10:
        return False, "⚠️ رقم الهاتف غير صالح"
    return True, phone

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
    """مسح الكاش"""
    st.cache_data.clear()
    logger.info("تم مسح الكاش")

# ---------------- التحقق من الأستاذ ----------------
def verify_professor(username, password, df_prof_memos):
    """التحقق من بيانات الأستاذ"""
    username = sanitize_input(username)
    password = sanitize_input(password)
    
    if df_prof_memos.empty:
        return False, "❌ خطأ في تحميل البيانات"
    
    # البحث في العمودين M و N
    prof = df_prof_memos[
        (df_prof_memos.get("اسم المستخدم", pd.Series()).astype(str).str.strip() == username) &
        (df_prof_memos.get("كلمة المرور", pd.Series()).astype(str).str.strip() == password)
    ]
    
    if prof.empty:
        logger.warning(f"محاولة دخول أستاذ فاشلة: {username}")
        return False, "❌ اسم المستخدم أو كلمة المرور غير صحيحة"
    
    logger.info(f"تسجيل دخول أستاذ ناجح: {username}")
    return True, prof.iloc[0]

# ---------------- Session State ----------------
if 'page' not in st.session_state:
    st.session_state.page = "home"
if 'user_type' not in st.session_state:
    st.session_state.user_type = None
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_data' not in st.session_state:
    st.session_state.user_data = None
if 'student1' not in st.session_state:
    st.session_state.student1 = None
if 'student2' not in st.session_state:
    st.session_state.student2 = None

def logout():
    """تسجيل الخروج"""
    st.session_state.page = "home"
    st.session_state.user_type = None
    st.session_state.logged_in = False
    st.session_state.user_data = None
    st.session_state.student1 = None
    st.session_state.student2 = None
    st.rerun()

# ---------------- الصفحة الرئيسية ----------------
def show_home_page():
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    
    # الشعار والعنوان
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
            <div class="logo-container">
                <img src="https://raw.githubusercontent.com/SAMIR-MALEK/memoire-depot-2026/main/LOGO2.png" width="120">
                <div class="university-name">جامعة محمد البشير الإبراهيمي</div>
                <div style="color: #666; font-size: 1.1rem;">كلية الحقوق والعلوم السياسية</div>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown('<h1 class="hero-title">🎓 نظام إدارة مذكرات الماستر</h1>', unsafe_allow_html=True)
        st.markdown('<p class="hero-subtitle">منصة متكاملة لتسجيل ومتابعة مذكرات التخرج</p>', unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # اختيار نوع المستخدم
    st.markdown('<h2 style="text-align: center; color: #667eea; margin: 40px 0;">اختر نوع حسابك</h2>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        col_student, col_prof = st.columns(2)
        
        with col_student:
            if st.button("👨‍🎓 طالب", use_container_width=True, key="btn_student"):
                st.session_state.user_type = "student"
                st.session_state.page = "student_login"
                st.rerun()
        
        with col_prof:
            if st.button("👨‍🏫 أستاذ", use_container_width=True, key="btn_prof"):
                st.session_state.user_type = "professor"
                st.session_state.page = "prof_login"
                st.rerun()
    
    # معلومات إضافية
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("""
        <div class="info-box">
            <h3 style="margin-top: 0;">📌 معلومات هامة:</h3>
            <ul style="text-align: right;">
                <li>🔹 الطلاب: يمكنكم تسجيل مذكراتكم ومتابعة تقدمكم</li>
                <li>🔹 الأساتذة: لوحة تحكم شاملة لإدارة ومتابعة المذكرات</li>
                <li>🔹 للدعم الفني: يرجى التواصل مع إدارة الكلية</li>
            </ul>
        </div>
    """, unsafe_allow_html=True)
    
    # Footer
    st.markdown("""
        <div class="footer">
            <p>© 2026 جامعة محمد البشير الإبراهيمي - كلية الحقوق والعلوم السياسية</p>
            <p style="font-size: 0.9rem; opacity: 0.8;">جميع الحقوق محفوظة</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# ---------------- تسجيل دخول الأستاذ ----------------
def show_prof_login():
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<h1 class="hero-title">👨‍🏫 فضاء الأستاذ</h1>', unsafe_allow_html=True)
        st.markdown('<p class="hero-subtitle">تسجيل الدخول</p>', unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        username = st.text_input("📧 اسم المستخدم", max_chars=50)
        password = st.text_input("🔑 كلمة المرور", type="password", max_chars=50)
        
        col_login, col_back = st.columns(2)
        
        with col_login:
            if st.button("🚀 تسجيل الدخول", use_container_width=True):
                if not username or not password:
                    st.markdown('<div class="error-box">⚠️ يرجى إدخال جميع البيانات</div>', unsafe_allow_html=True)
                else:
                    df_prof_memos = load_prof_memos()
                    valid, result = verify_professor(username, password, df_prof_memos)
                    
                    if valid:
                        st.session_state.logged_in = True
                        st.session_state.user_data = result
                        st.session_state.page = "prof_dashboard"
                        st.rerun()
                    else:
                        st.markdown(f'<div class="error-box">{result}</div>', unsafe_allow_html=True)
        
        with col_back:
            if st.button("◀️ رجوع", use_container_width=True):
                st.session_state.page = "home"
                st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

# ---------------- لوحة تحكم الأستاذ ----------------
def show_prof_dashboard():
    prof_data = st.session_state.user_data
    prof_name = prof_data.get("الأستاذ", "").strip()
    
    # Header
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f'<h1 class="hero-title">مرحباً أ. {prof_name} 👋</h1>', unsafe_allow_html=True)
    with col2:
        if st.button("🚪 خروج", use_container_width=True):
            logout()
    
    # تحميل البيانات
    clear_cache()
    df_prof_memos = load_prof_memos()
    df_memos = load_memos()
    
    # فلترة مذكرات الأستاذ
    prof_memos = df_prof_memos[df_prof_memos["الأستاذ"].astype(str).str.strip() == prof_name]
    
    # حساب الإحصائيات
    total = len(prof_memos)
    registered = len(prof_memos[prof_memos["تم التسجيل"].astype(str).str.strip() == "نعم"])
    remaining = total - registered
    percentage = (registered / total * 100) if total > 0 else 0
    
    # بطاقات الإحصائيات
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
            <div class="stat-card" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
                <div style="font-size: 2.5rem;">📚</div>
                <div class="stat-number">{total}</div>
                <div class="stat-label">إجمالي المذكرات</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
            <div class="stat-card" style="background: linear-gradient(135deg, #84fab0 0%, #8fd3f4 100%);">
                <div style="font-size: 2.5rem;">✅</div>
                <div class="stat-number">{registered}</div>
                <div class="stat-label">مذكرات مسجلة</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
            <div class="stat-card" style="background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);">
                <div style="font-size: 2.5rem;">⏳</div>
                <div class="stat-number">{remaining}</div>
                <div class="stat-label">مذكرات متبقية</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
            <div class="stat-card" style="background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);">
                <div style="font-size: 2.5rem;">📊</div>
                <div class="stat-number">{percentage:.0f}%</div>
                <div class="stat-label">نسبة الإنجاز</div>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📋 المذكرات المسجلة", "🔑 كلمات السر", "📊 الإحصائيات", "⚙️ الإعدادات"])
    
    with tab1:
        st.markdown("### 📋 قائمة المذكرات المسجلة")
        
        registered_memos = prof_memos[prof_memos["تم التسجيل"].astype(str).str.strip() == "نعم"]
        
        if not registered_memos.empty:
            for idx, memo in registered_memos.iterrows():
                with st.expander(f"📄 {memo.get('رقم المذكرة', '')} - {memo.get('عنوان المذكرة', '')[:50]}..."):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown(f"**👤 الطالب الأول:** {memo.get('الطالب الأول', '')}")
                        st.markdown(f"**👤 الطالب الثاني:** {memo.get('الطالب الثاني', 'لا يوجد')}")
                        st.markdown(f"**📅 تاريخ التسجيل:** {memo.get('تاريخ التسجيل', '')}")
                    
                    with col2:
                        # هنا يمكن إضافة أرقام الهواتف عندما يتم حفظها
                        st.markdown(f"**🎯 التخصص:** {memo.get('التخصص', '')}")
                        
                        # نسبة التقدم (قابلة للتعديل لاحقاً)
                        progress = st.slider(
                            "نسبة التقدم",
                            0, 100,
                            int(memo.get('نسبة التقدم', 0)) if memo.get('نسبة التقدم', '').isdigit() else 0,
                            key=f"progress_{idx}"
                        )
        else:
            st.info("لا توجد مذكرات مسجلة بعد")
    
    with tab2:
        st.markdown("### 🔑 كلمات السر")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### ✅ كلمات السر المستخدمة")
            used = prof_memos[prof_memos["تم التسجيل"].astype(str).str.strip() == "نعم"]
            for idx, row in used.iterrows():
                password = row.get("كلمة سر التسجيل", "")
                if password:
                    st.success(f"✅ {password}")
            
            if used.empty:
                st.info("لا توجد كلمات سر مستخدمة")
        
        with col2:
            st.markdown("#### ⏳ كلمات السر المتاحة")
            available = prof_memos[prof_memos["تم التسجيل"].astype(str).str.strip() != "نعم"]
            for idx, row in available.iterrows():
                password = row.get("كلمة سر التسجيل", "")
                if password:
                    st.warning(f"⏳ {password}")
            
            if available.empty:
                st.info("لا توجد كلمات سر متاحة")
    
    with tab3:
        st.markdown("### 📊 الإحصائيات التفصيلية")
        
        # رسم بياني دائري
        fig = go.Figure(data=[go.Pie(
            labels=['مسجلة', 'متبقية'],
            values=[registered, remaining],
            hole=.4,
            marker_colors=['#84fab0', '#fa709a']
        )])
        
        fig.update_layout(
            title_text="توزيع المذكرات",
            font=dict(family="Cairo, sans-serif", size=14)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with tab4:
        st.markdown("### ⚙️ الإعدادات")
        st.info("🚧 قيد التطوير - قريباً")

# ---------------- Main App ----------------
if st.session_state.page == "home":
    show_home_page()

elif st.session_state.page == "prof_login":
    show_prof_login
