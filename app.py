import streamlit as st
from datetime import datetime, time, date, timedelta
import pandas as pd
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from googleapiclient.errors import HttpError
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import io
import base64
import re
import random
import time
import textwrap

# ---------------- إعداد Logging ----------------
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ---------------- إعداد الصفحة ----------------
st.set_page_config(page_title="نظام إدارة مذكرات الماستر", page_icon="📘", layout="wide")
st.cache_data.clear()

# ---------------- CSS ----------------
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;900&display=swap" rel="stylesheet">
<style>
    * { box-sizing: border-box; }
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif !important; direction: rtl; text-align: right; }
    .main { background-color: #0A1B2C; color: #ffffff; }
    .block-container { padding: 2rem; background-color: #1A2A3D; border-radius: 16px; margin:auto; }
    h1, h2, h3, h4 { font-weight: 700; margin-bottom: 1rem; color: #ffffff !important; }
    label, p, span { color: #ffffff !important; }
    
    /* Cards */
    .card {
        background: rgba(30, 41, 59, 0.95); border:1px solid rgba(255,255,255, 0.08);
        border-radius: 20px; padding: 30px; margin-bottom: 20px;
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.2);
        border-top: 3px solid #2F6F7E; transition: transform 0.2s ease;
    }
    .card:hover { transform: translateY(-2px); }
    
    /* Buttons */
    .stButton>button, button[kind="primary"] {
        background-color: #2F6F7E !important; color: #ffffff !important;
        border-radius: 12px !important; padding: 12px 28px;
        border: none !important; font-weight: 600; width: 100%;
    }
    .stButton>button:hover { background-color: #285E6B !important; }

    /* KPIs */
    .kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1.5rem; margin-bottom: 2.5rem; }
    .kpi-card { background: linear-gradient(145deg, #1E293B, #0F172A); border: 1px solid rgba(255, 255, 255, 0.05); border-radius: 16px; padding: 2rem 1rem; text-align: center; }
    .kpi-value { font-size: 2.5rem; font-weight: 900; color: #FFD700; margin: 10px 0; }
    .kpi-label { font-size: 1.1rem; color: #ffffff; }

    /* Status Badges */
    .status-badge { padding: 8px 16px; border-radius: 20px; font-size: 0.95rem; font-weight: bold; text-align: center; display: inline-block; margin: 5px; }
    .status-deposited { background: rgba(59, 130, 246, 0.2); color: #3B82F6; }
    .status-validated { background: rgba(16, 185, 129, 0.2); color: #10B981; }
    .status-scheduled { background: rgba(139, 92, 246, 0.2); color: #8B5CF6; }
    .status-rejected { background: rgba(239, 68, 68, 0.2); color: #EF4444; }
    
    /* Upload Area */
    .upload-area { border: 2px dashed #2F6F7E; border-radius: 15px; padding: 40px; text-align: center; background: rgba(47, 111, 126, 0.05); margin-top: 20px; }
    
    /* Progress Bar */
    .progress-container { background-color: #0F172A; border-radius: 99px; padding: 6px; margin: 20px 0; overflow: hidden; }
    .progress-bar { height: 24px; border-radius: 99px; background: linear-gradient(90deg, #2F6F7E 0%, #FFD700 100%); box-shadow: 0 0 15px rgba(47, 111, 126, 0.5); }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] { gap: 2rem; }
    .stTabs [data-baseweb="tab"] { color: #94A3B8; font-weight: 600; padding: 10px 20px; border-radius: 10px; }
    .stTabs [aria-selected="true"] { background: rgba(47, 111, 126, 0.2); color: #FFD700; }
    
    /* DataFrames */
    .stDataFrame { border-radius: 12px; overflow: hidden; border: 1px solid rgba(255,255,255, 0.1); background: #1E293B; }
</style>
""", unsafe_allow_html=True)

# ---------------- Google APIs ----------------
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
try:
    info = st.secrets["service_account"]
    credentials = Credentials.from_service_account_info(info, scopes=SCOPES)
    sheets_service = build('sheets', 'v4', credentials=credentials)
    drive_service = build('drive', 'v3', credentials=credentials)
except Exception as e:
    st.error("⚠️ خطأ في الاتصال بـ Google APIs"); st.stop()

# ---------------- IDs ----------------
STUDENTS_SHEET_ID = "1gvNkOVVKo6AO07dRKMnSQw6vZ3KdUnW7I4HBk61Sqns"
MEMOS_SHEET_ID = "1LNJMBAye4QIQy7JHz6F8mQ6-XNC1weZx1ozDZFfjD5s"
PROF_MEMOS_SHEET_ID = "1OnZi1o-oPMUI_W_Ew-op0a1uOhSj006hw_2jrMD6FSE"
SETTINGS_SHEET_ID = MEMOS_SHEET_ID 

# Ranges
STUDENTS_RANGE = "Feuille 1!A1:U1000" 
MEMOS_RANGE = "Feuille 1!A1:AC1000" 
PROF_MEMOS_RANGE = "Feuille 1!A1:P1000"
REQUESTS_RANGE = "Feuille 1!A1:K1000"
SETTINGS_RANGE = "Settings!A1:B10"
ROOMS_RANGE = "Rooms!A1:B20"

ADMIN_CREDENTIALS = {"admin": "admin2026"}
EMAIL_SENDER = "domaine.dsp@univ-bba.dz"
EMAIL_PASSWORD = "qptlxzunqhdcjcjt"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# ---------------- دوال مساعدة ----------------
def col_letter(n):
    result = ""
    while n > 0:
        n, remainder = divmod(n - 1, 26)
        result = chr(65 + remainder) + result
    return result

def normalize_text(val):
    v = str(val).strip()
    if v.endswith('.0'): v = v[:-2]
    return v

def sanitize_input(text):
    if not text: return ""
    return str(text).strip()

# --- نهاية الجزء الأول ---
# ---------------- دوال الإعدادات ----------------
def get_settings():
    try:
        result = sheets_service.spreadsheets().values().get(spreadsheetId=SETTINGS_SHEET_ID, range=SETTINGS_RANGE).execute()
        values = result.get('values', [])
        return {row[0]: row[1] if len(row) > 1 else "" for row in values}
    except: return {}

def get_rooms():
    try:
        result = sheets_service.spreadsheets().values().get(spreadsheetId=SETTINGS_SHEET_ID, range=ROOMS_RANGE).execute()
        values = result.get('values', [])
        if values and values[0][0] == 'اسم القاعة': values = values[1:]
        return [row[0] for row in values if row]
    except: return []

# ---------------- دوال التحميل ----------------
@st.cache_data(ttl=60)
def load_students():
    try:
        result = sheets_service.spreadsheets().values().get(spreadsheetId=STUDENTS_SHEET_ID, range=STUDENTS_RANGE).execute()
        values = result.get('values', [])
        if not values: return pd.DataFrame()
        df = pd.DataFrame(values[1:], columns=values[0])
        df.columns = df.columns.str.strip()
        return df
    except Exception as e: logger.error(f"Load Students Error: {e}"); return pd.DataFrame()

@st.cache_data(ttl=60)
def load_memos():
    try:
        result = sheets_service.spreadsheets().values().get(spreadsheetId=MEMOS_SHEET_ID, range=MEMOS_RANGE).execute()
        values = result.get('values', [])
        if not values: return pd.DataFrame()
        df = pd.DataFrame(values[1:], columns=values[0])
        df.columns = df.columns.str.strip()
        return df
    except Exception as e: logger.error(f"Load Memos Error: {e}"); return pd.DataFrame()

@st.cache_data(ttl=60)
def load_prof_memos():
    try:
        result = sheets_service.spreadsheets().values().get(spreadsheetId=PROF_MEMOS_SHEET_ID, range=PROF_MEMOS_RANGE).execute()
        values = result.get('values', [])
        if not values: return pd.DataFrame()
        df = pd.DataFrame(values[1:], columns=values[0])
        return df
    except Exception as e: return pd.DataFrame()

@st.cache_data(ttl=60)
def load_requests():
    try:
        result = sheets_service.spreadsheets().values().get(spreadsheetId=MEMOS_SHEET_ID, range=REQUESTS_RANGE).execute()
        values = result.get('values', [])
        if not values: return pd.DataFrame()
        df = pd.DataFrame(values[1:], columns=values[0])
        return df
    except: return pd.DataFrame()

# ---------------- دوال التحقق ----------------
def verify_student(username, password, df_students):
    username = normalize_text(username)
    password = str(password).strip()
    if df_students.empty: return False, "خطأ في البيانات"
    
    df_students['username_norm'] = df_students["اسم المستخدم"].astype(str).apply(normalize_text)
    student = df_students[df_students["username_norm"] == username]
    
    if student.empty: return False, "اسم المستخدم غير موجود"
    if str(student.iloc[0]["كلمة السر"]).strip() != password: return False, "كلمة السر غير صحيحة"
    return True, student.iloc[0].to_dict()

def verify_professor(username, password, df_prof_memos):
    username = normalize_text(username)
    password = str(password).strip()
    if df_prof_memos.empty: return False, "خطأ في البيانات"
    
    prof = df_prof_memos[(df_prof_memos["إسم المستخدم"].astype(str).apply(normalize_text) == username) & 
                         (df_prof_memos["كلمة المرور"].astype(str).str.strip() == password)]
    if prof.empty: return False, "بيانات الدخول غير صحيحة"
    return True, prof.iloc[0].to_dict()

def verify_admin(username, password):
    if username in ADMIN_CREDENTIALS and ADMIN_CREDENTIALS[username] == password:
        return True, username
    return False, "بيانات خاطئة"

# ---------------- دوال الإيميل ----------------
def send_email(to_email, subject, body_html):
    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = EMAIL_SENDER
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body_html, 'html', 'utf-8'))
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as e:
        logger.error(f"Email error: {e}")
        return False

def send_welcome_email(prof_name, username, password, email):
    body = f"""
    <html dir="rtl"><body><div style="font-family: Cairo, sans-serif; padding: 20px;">
        <h2>تفعيل حساب فضاء الأساتذة</h2>
        <p>مرحباً د. {prof_name}</p>
        <p>تم تفعيل حسابك على منصة متابعة المذكرات.</p>
        <p><b>اسم المستخدم:</b> {username}</p>
        <p><b>كلمة المرور:</b> {password}</p>
        <a href="https://memoires2026.streamlit.app">رابط المنصة</a>
    </div></body></html>
    """
    return send_email(email, "تفعيل حساب فضاء الأساتذة", body)

# ---------------- دوال رفع الملفات ----------------
def upload_pdf_to_drive(file_obj, filename, folder_id):
    try:
        metadata = {'name': filename, 'parents': [folder_id]}
        media = MediaIoBaseUpload(file_obj, mimetype='application/pdf')
        file = drive_service.files().create(body=metadata, media_body=media, fields='id, webViewLink').execute()
        permission = {'type': 'anyone', 'role': 'reader'}
        drive_service.permissions().create(fileId=file.get('id'), body=permission).execute()
        return file.get('webViewLink')
    except Exception as e:
        logger.error(f"Drive Upload Error: {e}")
        return None

# ---------------- دوال التحديث ----------------
def update_deposit_status(memo_number, status, pdf_link="", deposit_date=""):
    try:
        df_memos = load_memos()
        memo_row = df_memos[df_memos["رقم المذكرة"].astype(str).apply(normalize_text) == normalize_text(memo_number)]
        if memo_row.empty: return False
        
        row_idx = memo_row.index[0] + 2
        updates = [
            {"range": f"Feuille 1!V{row_idx}", "values": [[status]]},
            {"range": f"Feuille 1!W{row_idx}", "values": [[pdf_link]]},
            {"range": f"Feuille 1!X{row_idx}", "values": [[deposit_date]]}
        ]
        sheets_service.spreadsheets().values().batchUpdate(
            spreadsheetId=MEMOS_SHEET_ID, body={"valueInputOption": "USER_ENTERED", "data": updates}
        ).execute()
        st.cache_data.clear()
        return True
    except Exception as e:
        logger.error(e)
        return False

def update_schedule(memo_number, date_val, time_val, room, president, examiner):
    try:
        df_memos = load_memos()
        memo_row = df_memos[df_memos["رقم المذكرة"].astype(str).apply(normalize_text) == normalize_text(memo_number)]
        if memo_row.empty: return False
        
        row_idx = memo_row.index[0] + 2
        updates = [
            {"range": f"Feuille 1!Y{row_idx}", "values": [[date_val]]},
            {"range": f"Feuille 1!Z{row_idx}", "values": [[time_val]]},
            {"range": f"Feuille 1!AA{row_idx}", "values": [[room]]},
            {"range": f"Feuille 1!AB{row_idx}", "values": [[president]]},
            {"range": f"Feuille 1!AC{row_idx}", "values": [[examiner]]}
        ]
        sheets_service.spreadsheets().values().batchUpdate(
            spreadsheetId=MEMOS_SHEET_ID, body={"valueInputOption": "USER_ENTERED", "data": updates}
        ).execute()
        st.cache_data.clear()
        return True
    except Exception as e:
        logger.error(e)
        return False

def update_progress(memo_number, progress_value):
    try:
        df_memos = load_memos()
        memo_row = df_memos[df_memos["رقم المذكرة"].astype(str).apply(normalize_text) == normalize_text(memo_number)]
        if memo_row.empty: return False
        row_idx = memo_row.index[0] + 2
        sheets_service.spreadsheets().values().update(
            spreadsheetId=MEMOS_SHEET_ID, range=f"Feuille 1!Q{row_idx}",
            valueInputOption="USER_ENTERED", body={"values": [[str(progress_value)]]}
        ).execute()
        st.cache_data.clear()
        return True
    except: return False

# --- نهاية الجزء الثاني ---
# ---------------- محرك الجدولة الذكية ----------------
def run_smart_scheduling(target_memos, date_range, rooms_list):
    df_profs = load_prof_memos()
    all_profs = df_profs["الأستاذ"].dropna().unique().tolist()
    
    # تهيئة أعباء الأساتذة
    prof_workload = {p: {'pres_count': 0, 'exam_count': 0, 'schedule': {}} for p in all_profs}
    
    # تحميل الجدول الحالي لحساب الأعباء المسبقة
    df_current = load_memos()
    for _, row in df_current.iterrows():
        d, t = row.get('تاريخ المناقشة'), row.get('توقيت المناقشة')
        if pd.notna(d) and pd.notna(t):
            key = f"{d}_{t}"
            sup = row.get('الأستاذ')
            if sup in prof_workload: prof_workload[sup]['schedule'][key] = 'supervisor'
            
            pres = row.get('الرئيس')
            if pres in prof_workload:
                prof_workload[pres]['pres_count'] += 1
                prof_workload[pres]['schedule'][key] = 'president'
            
            exam = row.get('المناقش')
            if exam in prof_workload:
                prof_workload[exam]['exam_count'] += 1
                prof_workload[exam]['schedule'][key] = 'examiner'

    # تهيئة القاعات
    rooms_availability = {}
    time_slots = ["09:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00"]
    delta = date_range[1] - date_range[0]
    
    for i in range(delta.days + 1):
        d = date_range[0] + timedelta(days=i)
        if d.weekday() in [4, 5]: continue # استبعاد الجمعة والسبت
        d_str = d.strftime('%Y-%m-%d')
        rooms_availability[d_str] = {}
        for t in time_slots:
            rooms_availability[d_str][t] = {r: None for r in rooms_list}

    # حلقة البرمجة
    logs = []
    scheduled_count = 0
    
    for memo in target_memos:
        memo_num = memo['رقم المذكرة']
        supervisor = memo['الأستاذ']
        found_slot = False
        
        for d_str in sorted(rooms_availability.keys()):
            for t_slot in time_slots:
                # البحث عن قاعة
                available_room = next((r for r in rooms_list if rooms_availability[d_str][t_slot][r] is None), None)
                if not available_room: continue
                
                # تقييد عدد المهام اليومية للمشرف (4 مهام)
                daily_tasks_sup = sum(1 for k in prof_workload[supervisor]['schedule'] if k.startswith(d_str))
                if daily_tasks_sup >= 4: continue
                
                # البحث عن مرشحين (رئيس ومناقش)
                busy_profs = set(p for p, data in prof_workload.items() if f"{d_str}_{t_slot}" in data['schedule'])
                
                candidates = []
                for p in all_profs:
                    if p in busy_profs or p == supervisor: continue
                    # التحقق من الحد الأقصى للمهام اليومية (4)
                    tasks_today = sum(1 for k in prof_workload[p]['schedule'] if k.startswith(d_str))
                    if tasks_today < 4:
                        candidates.append(p)
                
                if len(candidates) < 2: continue
                
                # ترتيب للعدالة (أقل أدوار)
                candidates.sort(key=lambda x: (prof_workload[x]['pres_count'] + prof_workload[x]['exam_count']))
                
                president = candidates[0]
                examiner = candidates[1]
                
                # --- نجاح ---
                found_slot = True
                rooms_availability[d_str][t_slot][available_room] = memo_num
                slot_key = f"{d_str}_{t_slot}"
                
                prof_workload[supervisor]['schedule'][slot_key] = 'supervisor'
                prof_workload[president]['pres_count'] += 1
                prof_workload[president]['schedule'][slot_key] = 'president'
                prof_workload[examiner]['exam_count'] += 1
                prof_workload[examiner]['schedule'][slot_key] = 'examiner'
                
                update_schedule(memo_num, d_str, t_slot, available_room, president, examiner)
                logs.append(f"✅ {memo_num}: {d_str} {t_slot} - {available_room} - رئيس:{president} - مناقش:{examiner}")
                scheduled_count += 1
                break
            if found_slot: break
        
        if not found_slot:
            logs.append(f"❌ فشل جدولة {memo_num}")
            
    return scheduled_count, logs

# ============================================================
# التطبيق الرئيسي
# ============================================================
st.session_state.setdefault('user_type', None)

# --- 1. الصفحة الرئيسية (اختيار الدور) ---
if not st.session_state.user_type:
    st.title("نظام إدارة مذكرات الماستر")
    st.markdown("<p style='text-align: center;'>جامعة محمد البشير الإبراهيمي - كلية الحقوق والعلوم السياسية</p>", unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns(3)
    with c1: 
        st.markdown("<div class='card' style='text-align:center;'><h3>🎓 فضاء الطالب</h3>", unsafe_allow_html=True)
        if st.button("دخول", key="std_btn"): st.session_state.user_type = "student"; st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    with c2: 
        st.markdown("<div class='card' style='text-align:center;'><h3>📚 فضاء الأستاذ</h3>", unsafe_allow_html=True)
        if st.button("دخول", key="prof_btn"): st.session_state.user_type = "prof"; st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    with c3: 
        st.markdown("<div class='card' style='text-align:center;'><h3>⚙️ فضاء الإدارة</h3>", unsafe_allow_html=True)
        if st.button("دخول", key="adm_btn"): st.session_state.user_type = "admin"; st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

# --- 2. فضاء الطالب ---
elif st.session_state.user_type == "student":
    # شاشة تسجيل الدخول
    if 'student_data' not in st.session_state:
        st.subheader("🔐 تسجيل الدخول")
        with st.form("std_login"):
            u = st.text_input("اسم المستخدم")
            p = st.text_input("كلمة السر", type="password")
            if st.form_submit_button("دخول"):
                df_s = load_students()
                ok, res = verify_student(u, p, df_s)
                if ok: st.session_state.student_data = res; st.rerun()
                else: st.error(res)
    
    # بعد تسجيل الدخول
    else:
        s_data = st.session_state.student_data
        st.sidebar.success(f"مرحباً {s_data.get('إسم', 'طالب')}")
        if st.sidebar.button("خروج"): st.session_state.clear(); st.rerun()
        
        memo_num = normalize_text(s_data.get('رقم المذكرة', ''))
        
        # حالة: غير مسجل في مذكرة بعد
        if not memo_num:
            st.warning("⚠️ أنت غير مسجل في مذكرة بعد.")
            st.info("في حال كنت مذكرة فردية أو ثنائية، يرجى التواصل مع المشرف لتسجيلك.")
            st.stop()

        # حالة: طالب مسجل له مذكرة
        else:
            df_memos = load_memos()
            m_info = df_memos[df_memos["رقم المذكرة"].astype(str).apply(normalize_text) == memo_num]
            
            if m_info.empty: st.error("خطأ في جلب بيانات المذكرة")
            else:
                m_row = m_info.iloc[0]
                d_status = str(m_row.get('حالة الإيداع', '')).strip()
                
                tab1, tab2 = st.tabs(["📄 مذكرتي", "📤 إيداع المذكرة"])
                
                # --- تبويب مذكرتي ---
                with tab1:
                    st.markdown(f"<div class='card'>", unsafe_allow_html=True)
                    st.write(f"**رقم المذكرة:** {m_row['رقم المذكرة']}")
                    st.write(f"**العنوان:** {m_row['عنوان المذكرة']}")
                    st.write(f"**المشرف:** {m_row['الأستاذ']}")
                    
                    # نسبة التقدم
                    prog = str(m_row.get('نسبة التقدم', '0')).strip()
                    try: p_int = int(prog)
                    except: p_int = 0
                    st.markdown(f"<div class='progress-container'><div class='progress-bar' style='width:{p_int}%;'>{p_int}%</div></div>", unsafe_allow_html=True)
                    
                    # حالة الإيداع
                    badge_class = ""
                    status_text = "قيد الإنجاز"
                    if d_status == 'إيداع مؤقت': badge_class="status-deposited"; status_text = "إيداع مؤقت"
                    elif d_status == 'معتمدة رسمياً': badge_class="status-validated"; status_text = "معتمدة رسمياً"
                    elif d_status == 'مرفوضة': badge_class="status-rejected"; status_text = "مرفوضة"
                    st.markdown(f"<br><span class='status-badge {badge_class}'>{status_text}</span>", unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)
                    
                    # موعد المناقشة
                    if pd.notna(m_row.get('تاريخ المناقشة')) and str(m_row['تاريخ المناقشة']).strip() != '':
                        st.markdown("<div class='card' style='border-color: #8B5CF6;'>", unsafe_allow_html=True)
                        st.subheader("📅 موعد المناقشة")
                        st.write(f"**التاريخ:** {m_row['تاريخ المناقشة']}")
                        st.write(f"**الساعة:** {m_row['توقيت المناقشة']}")
                        st.write(f"**القاعة:** {m_row['القاعة']}")
                        st.write(f"**رئيس اللجنة:** {m_row['الرئيس']}")
                        st.write(f"**المناقش:** {m_row['المناقش']}")
                        st.markdown("</div>", unsafe_allow_html=True)

                # --- تبويب الإيداع ---
                with tab2:
                    settings = get_settings()
                    is_open = False
                    try:
                        today = date.today()
                        start = datetime.strptime(settings.get('deposit_start', ''), '%Y-%m-%d').date()
                        end = datetime.strptime(settings.get('deposit_end', ''), '%Y-%m-%d').date()
                        if start <= today <= end: is_open = True
                        else: st.warning(f"باب الإيداع مغلق حالياً. (المتاح: {start} إلى {end})")
                    except: st.warning("لم تحدد الإدارة فترة الإيداع بعد.")
                    
                    if is_open:
                        if d_status == 'معتمدة رسمياً':
                            st.success("✅ تم اعتماد مذكرتك نهائياً.")
                            if m_row.get('رابط الملف'): st.link_button("تحميل الملف", m_row['رابط الملف'])
                        elif d_status == 'إيداع مؤقت':
                            st.info("⏳ ملفك قيد المراجعة.")
                            if m_row.get('رابط الملف'): st.link_button("تحميل الملف", m_row['رابط الملف'])
                        else:
                            st.markdown("<div class='upload-area'>", unsafe_allow_html=True)
                            st.write("### 📤 رفع ملف المذكرة (PDF)")
                            uploaded_file = st.file_uploader("اختر الملف", type="pdf")
                            if st.button("تأكيد الإيداع"):
                                if uploaded_file:
                                    with st.spinner("جاري الرفع..."):
                                        folder_id = settings.get('drive_folder_id')
                                        link = upload_pdf_to_drive(uploaded_file, f"{memo_num}.pdf", folder_id)
                                        if link:
                                            update_deposit_status(memo_num, "إيداع مؤقت", link, datetime.now().strftime('%Y-%m-%d'))
                                            st.success("✅ تم الإيداع بنجاح."); st.rerun()
                                        else: st.error("فشل الرفع.")
                                else: st.warning("اختر ملفاً")
                            st.markdown("</div>", unsafe_allow_html=True)

# --- نهاية الجزء الثالث ---
# --- 3. فضاء الأستاذ ---
elif st.session_state.user_type == "prof":
    if 'prof_data' not in st.session_state:
        st.subheader("🔐 تسجيل الدخول")
        with st.form("prof_login"):
            u = st.text_input("اسم المستخدم")
            p = st.text_input("كلمة المرور", type="password")
            if st.form_submit_button("دخول"):
                df_p = load_prof_memos()
                ok, res = verify_professor(u, p, df_p)
                if ok: st.session_state.prof_data = res; st.rerun()
                else: st.error(res)
    
    else:
        p_data = st.session_state.prof_data
        p_name = p_data['الأستاذ']
        st.sidebar.success(f"د. {p_name}")
        if st.sidebar.button("خروج"): st.session_state.clear(); st.rerun()
        
        df_memos = load_memos()
        
        tab1, tab2, tab3 = st.tabs(["📝 مراجعة الإيداعات", "🗓️ جدول مناقشاتي", "📊 إحصائياتي"])
        
        with tab1:
            st.subheader("المذكرات في انتظار الاعتماد")
            pending = df_memos[(df_memos['الأستاذ'].astype(str).str.strip() == p_name) & 
                               (df_memos['حالة الإيداع'].astype(str).str.strip() == 'إيداع مؤقت')]
            if pending.empty: st.info("لا توجد مذكرات جديدة للمراجعة.")
            else:
                for idx, row in pending.iterrows():
                    st.markdown(f"<div class='card'>", unsafe_allow_html=True)
                    c1, c2 = st.columns([3, 1])
                    c1.write(f"**{row['رقم المذكرة']}** - {row['عنوان المذكرة']}")
                    if row.get('رابط الملف'): c2.link_button("📥 تحميل", row['رابط الملف'])
                    
                    cA, cR = st.columns(2)
                    if cA.button(f"✅ اعتماد", key=f"ok_{idx}"):
                        update_deposit_status(row['رقم المذكرة'], "معتمدة رسمياً")
                        st.success("تم الاعتماد"); st.rerun()
                    if cR.button(f"❌ رفض", key=f"no_{idx}"):
                        update_deposit_status(row['رقم المذكرة'], "مرفوضة")
                        st.warning("تم الرفض"); st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)
        
        with tab2:
            st.subheader("جدول مناقشاتي")
            sched = df_memos[(df_memos['تاريخ المناقشة'].astype(str).str.strip() != '') & 
                             ((df_memos['الأستاذ'].astype(str).str.strip() == p_name) |
                              (df_memos['الرئيس'].astype(str).str.strip() == p_name) |
                              (df_memos['المناقش'].astype(str).str.strip() == p_name))]
            
            if sched.empty: st.info("لا يوجد مناقشات مجدولة.")
            else:
                data = []
                for _, r in sched.iterrows():
                    role = "مشرف"
                    if r['الرئيس'] == p_name: role = "رئيس لجنة"
                    elif r['المناقش'] == p_name: role = "مناقش"
                    data.append([r['تاريخ المناقشة'], r['توقيت المناقشة'], r['القاعة'], r['رقم المذكرة'], role])
                
                st.dataframe(pd.DataFrame(data, columns=["التاريخ", "الوقت", "القاعة", "المذكرة", "دوري"]), use_container_width=True)
        
        with tab3:
            st.subheader("رصيد المهام")
            all_sched = df_memos[df_memos['تاريخ المناقشة'].astype(str).str.strip() != '']
            p_pres = len(all_sched[all_sched['الرئيس'] == p_name])
            p_exam = len(all_sched[all_sched['المناقش'] == p_name])
            c1, c2 = st.columns(2)
            c1.metric("عدد مرات الرئاسة", p_pres)
            c2.metric("عدد مرات المناقشة", p_exam)

# --- 4. فضاء الإدارة ---
elif st.session_state.user_type == "admin":
    if 'admin_logged' not in st.session_state:
        st.subheader("🔐 دخول الإدارة")
        u = st.text_input("المستخدم")
        p = st.text_input("السر", type="password")
        if st.button("دخول"):
            ok, res = verify_admin(u, p)
            if ok: st.session_state.admin_logged = True; st.rerun()
            else: st.error(res)
    
    else:
        st.sidebar.title("لوحة التحكم")
        if st.sidebar.button("خروج"): st.session_state.clear(); st.rerun()
        
        df_memos = load_memos()
        df_students = load_students()
        settings = get_settings()
        
        # KPIs
        st.markdown('<div class="kpi-grid">', unsafe_allow_html=True)
        st.markdown(f'<div class="kpi-card"><div class="kpi-value">{len(df_students)}</div><div class="kpi-label">طلاب</div></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="kpi-card"><div class="kpi-value">{len(df_memos)}</div><div class="kpi-label">مذكرات</div></div>', unsafe_allow_html=True)
        valid_count = len(df_memos[df_memos['حالة الإيداع'] == 'معتمدة رسمياً'])
        st.markdown(f'<div class="kpi-card"><div class="kpi-value">{valid_count}</div><div class="kpi-label">جاهزة للبرمجة</div></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        tab1, tab2, tab3, tab4, tab5 = st.tabs(["⚙️ الإعدادات", "🏫 القاعات", "📥 الإيداعات", "🧠 الجدولة الذكية", "📧 رسائل الأساتذة"])
        
        # --- الإعدادات ---
        with tab1:
            st.subheader("إعدادات النظام")
            with st.form("set_form"):
                d_start = st.date_input("بداية الإيداع", value=datetime.strptime(settings.get('deposit_start', '2027-01-01'), '%Y-%m-%d'))
                d_end = st.date_input("نهاية الإيداع", value=datetime.strptime(settings.get('deposit_end', '2027-02-01'), '%Y-%m-%d'))
                f_id = st.text_input("ID مجلد Drive", value=settings.get('drive_folder_id', ''))
                if st.form_submit_button("حفظ"):
                    data = [["deposit_start", d_start], ["deposit_end", d_end], ["drive_folder_id", f_id]]
                    sheets_service.spreadsheets().values().update(
                        spreadsheetId=SETTINGS_SHEET_ID, range=SETTINGS_RANGE,
                        valueInputOption="USER_ENTERED", body={"values": data}
                    ).execute()
                    st.cache_data.clear(); st.success("تم الحفظ"); st.rerun()
        
        # --- القاعات ---
        with tab2:
            st.subheader("إدارة القاعات")
            rooms = get_rooms()
            st.write("القاعات الحالية:", rooms)
            new_r = st.text_input("إضافة قاعة جديدة")
            if st.button("إضافة"):
                if new_r:
                    sheets_service.spreadsheets().values().append(
                        spreadsheetId=SETTINGS_SHEET_ID, range=ROOMS_RANGE,
                        valueInputOption="USER_ENTERED", body={"values": [[new_r]]}
                    ).execute()
                    st.cache_data.clear(); st.success("تمت الإضافة"); st.rerun()
        
        # --- الإيداعات ---
        with tab3:
            st.subheader("المذكرات المودعة مؤقتاً")
            dep = df_memos[df_memos['حالة الإيداع'].astype(str).str.strip() == 'إيداع مؤقت']
            st.dataframe(dep[['رقم المذكرة', 'عنوان المذكرة', 'الأستاذ', 'تاريخ إيداع المذكرة']], use_container_width=True)
        
        # --- الجدولة ---
        with tab4:
            st.subheader("🧠 محرك الجدولة الآلي")
            c1, c2 = st.columns(2)
            with c1: start_d = st.date_input("من تاريخ")
            with c2: end_d = st.date_input("إلى تاريخ")
            
            to_sched = df_memos[(df_memos['حالة الإيداع'].astype(str).str.strip() == 'معتمدة رسمياً') & 
                                (df_memos['تاريخ المناقشة'].astype(str).str.strip() == '')]
            
            st.info(f"عدد المذكرات الجاهزة للبرمجة: **{len(to_sched)}**")
            
            if st.button("🚀 تشغيل الخوارزمية", type="primary"):
                rooms_list = get_rooms()
                if not rooms_list: st.error("أضف قاعات أولاً!")
                else:
                    with st.spinner("جاري الحساب..."):
                        cnt, logs = run_smart_scheduling(to_sched.to_dict('records'), (start_d, end_d), rooms_list)
                    st.success(f"تمت جدولة {cnt} مذكرة.")
                    with st.expander("سجل العمليات"):
                        for l in logs: st.write(l)
                    st.rerun()
            
            st.markdown("---")
            st.subheader("الجدول الحالي")
            sch = df_memos[df_memos['تاريخ المناقشة'].astype(str).str.strip() != '']
            st.dataframe(sch[['رقم المذكرة', 'تاريخ المناقشة', 'توقيت المناقشة', 'القاعة', 'الرئيس', 'المناقش']], use_container_width=True)
        
        # --- رسائل الأساتذة ---
        with tab5:
            st.subheader("إرسال بيانات الدخول للأساتذة")
            df_profs = load_prof_memos()
            if st.button("إرسال للكل"):
                prog = st.progress(0, text="جاري الإرسال...")
                success_count = 0
                for i, row in df_profs.iterrows():
                    # محاكاة الإرسال - تأكد من وجود أعمدة البريد الإلكتروني في بياناتك
                    # email = row.get('البريد الإلكتروني')
                    # if email:
                    #     sent = send_welcome_email(row['الأستاذ'], row['إسم المستخدم'], row['كلمة المرور'], email)
                    #     if sent: success_count += 1
                    time.sleep(0.05) # محاكاة زمن الإرسال
                    prog.progress((i+1)/len(df_profs), text=f"جاري إرسال للبريد...")
                prog.empty()
                st.success(f"تم إرسال الإيميلات بنجاح (محاكاة).")

# --- نهاية الكود ---