import streamlit as st
from datetime import datetime
import pandas as pd
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import logging
import time
import uuid

# ---------------- إعداد Logging ----------------
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ---------------- إعداد الصفحة ----------------
st.set_page_config(page_title="نظام تسجيل المذكرات", page_icon="📘", layout="wide")

# ---------------- CSS (تصميم زرقاء بلا حدود) ----------------
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;900&display=swap" rel="stylesheet">
<style>
html, body, [class*="css"] { font-family: 'Cairo', sans-serif !important; direction: rtl; text-align: right; }
.main { background-color: #0A1B2C; color: #ffffff; }
.block-container { padding: 2rem; background-color: #1A2A3D; border-radius: 16px; margin:auto; }
h1, h2, h3, h4 { font-weight: 700; margin-bottom: 1rem; color: #F8FAFC; }
label, p, span { color: #E2E8F0; }
.stTextInput label, .stSelectbox label { color: #F8FAFC !important; font-weight: 600; }

/* الأزرار */
.stButton>button, button[kind="primary"], div[data-testid="stFormSubmitButton"] button {
    background-color: #2F6F7E !important; color: #ffffff !important; border: none !important;
    border-radius: 12px !important; font-weight: 600; padding: 10px 20px;
    transition: 0.3s;
}
.stButton>button:hover { background-color: #285E6B !important; transform: translateY(-2px); }

/* البطاقات */
.card { 
    background: rgba(30, 41, 59, 0.95); border: 1px solid rgba(255,255, 255, 0.08);
    border-radius: 20px; padding: 20px; margin-bottom: 20px; 
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3); border-top: 3px solid #2F6F7E;
}
.kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 2rem; }
.kpi-card {
    background: linear-gradient(145deg, #1E293B, #0F172A); border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 16px; padding: 1.5rem; text-align: center; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
}
.kpi-value { font-size: 2rem; font-weight: 900; color: #FFD700; margin: 10px 0; }
.kpi-label { font-size: 0.9rem; color: #94A3B8; font-weight: 600; text-transform: uppercase; }

/* الإشعارات */
.alert-card { background: linear-gradient(90deg, #8B4513 0%, #A0522D 100%); border: 1px solid #CD853F; color: white; padding: 15px; border-radius: 12px; text-align: center; font-weight: bold; margin-bottom: 20px; }
.success-card { background: linear-gradient(90deg, #065f46 0%, #047857 100%); border: 1px solid #34d399; color: white; padding: 15px; border-radius: 12px; text-align: center; margin-bottom: 20px; }

/* التبويبات */
.stTabs [data-baseweb="tab-list"] { gap: 2rem; padding-bottom: 10px; }
.stTabs [data-baseweb="tab"] { background: transparent; color: #94A3B8; font-weight: 600; padding: 10px 20px; }
.stTabs [aria-selected="true"] { background: rgba(47, 111, 126, 0.2); color: #FFD700; border-bottom: 2px solid #FFD700; }

/* شارات الحالة */
.status-badge { padding: 4px 10px; border-radius: 99px; font-size: 0.8em; font-weight: bold; }
.status-pending { background: #F59E0B; color: #fff; }
.status-approved { background: #10B981; color: #fff; }
.status-rejected { background: #EF4444; color: #fff; }
</style>
""", unsafe_allow_html=True)

# ---------------- Google Sheets Configuration ----------------
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
try:
    info = st.secrets["service_account"]
    credentials = Credentials.from_service_account_info(info, scopes=SCOPES)
    sheets_service = build('sheets', 'v4', credentials=credentials)
except Exception as e:
    st.error("⚠️ خطأ في الاتصال بـ Google Sheets. تأكد من ملف Secrets.")
    st.stop()

# --- معرفات الشيتات (يرجى التحقق منها) ---
STUDENTS_SHEET_ID = "1gvNkOVVKo6AO07dRKMnSQw6vZ3KdUnW7I4HBk61Sqns"
MEMOS_SHEET_ID = "1LNJMBAye4QIQy7JHz6F8mQ6-XNC1weZx1ozDZFfjD5s"
PROF_MEMOS_SHEET_ID = "1OnZi1o-oPMUI_W_Ew-op0a1uOhSj006hw_2jrMD6FSE"

# ضع هنا معرف الشيت الجديد "الطلبات" الذي أنشأته
REQUESTS_SHEET_ID = "YOUR_REQUESTS_SHEET_ID_HERE" 

# --- النطاقات (RANGES) ---
# تم توسيع نطاق المذكرات ليشمل الأعمدة S و T
STUDENTS_RANGE = "Feuille 1!A1:L1000"
MEMOS_RANGE = "Feuille 1!A1:T1000" 
PROF_MEMOS_RANGE = "Feuille 1!A1:P1000"
REQUESTS_RANGE = "Feuille 1!A1:K1000"

ADMIN_CREDENTIALS = {"admin": "admin2026", "dsp": "dsp@2026"}

# ---------------- Helper Functions ----------------
def col_letter(n):
    result = ""
    while n > 0:
        n, remainder = divmod(n - 1, 26)
        result = chr(65 + remainder) + result
    return result

def sanitize_input(text):
    if not text: return ""
    return str(text).strip()

def clear_cache():
    st.cache_data.clear()
    time.sleep(0.5)

# ---------------- Data Loading Functions ----------------
@st.cache_data(ttl=60)
def load_students():
    try:
        result = sheets_service.spreadsheets().values().get(spreadsheetId=STUDENTS_SHEET_ID, range=STUDENTS_RANGE).execute()
        values = result.get('values', [])
        if not values: return pd.DataFrame()
        df = pd.DataFrame(values[1:], columns=values[0])
        # توحيد أسماء الأعمدة
        if 'رقم تسجيل' in df.columns: df = df.rename(columns={'رقم تسجيل': 'رقم التسجيل'})
        return df
    except Exception as e:
        logger.error(f"Error loading students: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=60)
def load_memos():
    try:
        result = sheets_service.spreadsheets().values().get(spreadsheetId=MEMOS_SHEET_ID, range=MEMOS_RANGE).execute()
        values = result.get('values', [])
        if not values: return pd.DataFrame()
        
        # التعامل مع الأعمدة S (Index 18) و T (Index 19)
        cols = values[0]
        while len(cols) < 20: cols.append(f"Col_{len(cols)+1}") # ضمان عدد الأعمدة
        
        df = pd.DataFrame(values[1:], columns=cols)
        
        # تسمية الأعمدة الجديدة بشكل صريح
        if len(df.columns) >= 19: df.columns.values[18] = 'رقم تسجيل ط1' # العمود S
        if len(df.columns) >= 20: df.columns.values[19] = 'رقم تسجيل ط2' # العمود T
            
        return df
    except Exception as e:
        logger.error(f"Error loading memos: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=30) # تحديث أسرع للطلبات
def load_requests():
    if REQUESTS_SHEET_ID == "YOUR_REQUESTS_SHEET_ID_HERE" or REQUESTS_SHEET_ID == "":
        return pd.DataFrame()
    try:
        result = sheets_service.spreadsheets().values().get(spreadsheetId=REQUESTS_SHEET_ID, range=REQUESTS_RANGE).execute()
        values = result.get('values', [])
        if not values: return pd.DataFrame()
        
        expected_cols = ["رقم الطلب", "الوقت", "النوع", "الحالة", "الأستاذ", "رقم المذكرة", 
                         "رقم تسجيل الطالب 1", "رقم تسجيل الطالب 2", "العنوان الجديد", "المبررات", "ملاحظات الإدارة"]
        
        # إذا كان الشيت فارغ أو الرأس غير مطابق، نستخدم الأعمدة الافتراضية
        if len(values[0]) != len(expected_cols):
             df = pd.DataFrame(values[1:], columns=expected_cols if len(values)>1 else expected_cols)
        else:
             df = pd.DataFrame(values[1:], columns=values[0])
             
        return df
    except Exception as e:
        logger.error(f"Error loading requests: {e}")
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
        return pd.DataFrame()

# ---------------- Requests System Logic ----------------
def create_request(prof_name, req_type, memo_number, s1_reg, s2_reg, new_title, justification):
    if REQUESTS_SHEET_ID == "YOUR_REQUESTS_SHEET_ID_HERE":
        return False, "يرجى ضبط معرف شيت الطلبات في الكود (REQUESTS_SHEET_ID)"
    
    req_id = str(uuid.uuid4())[:8]
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    status = "قيد الانتظار"
    
    row_data = [[
        req_id, timestamp, req_type, status, prof_name, 
        str(memo_number), str(s1_reg) if s1_reg else "", 
        str(s2_reg) if s2_reg else "", 
        str(new_title) if new_title else "", justification, ""
    ]]
    
    try:
        sheets_service.spreadsheets().values().append(
            spreadsheetId=REQUESTS_SHEET_ID, range="Feuille 1!A1",
            valueInputOption="USER_ENTERED", body={"values": row_data}
        ).execute()
        clear_cache()
        return True, "تم إرسال الطلب بنجاح"
    except Exception as e:
        logger.error(f"Error creating request: {e}")
        return False, f"فشل إرسال الطلب: {str(e)}"

def update_request_status(req_id, new_status, admin_note=""):
    if REQUESTS_SHEET_ID == "YOUR_REQUESTS_SHEET_ID_HERE": return False
    
    try:
        df_req = load_requests()
        if df_req.empty: return False
        
        req_row_idx = df_req[df_req["رقم الطلب"] == req_id].index
        if len(req_row_idx) == 0: return False
        
        row_num = req_row_idx[0] + 2 # +2 for header and 1-based index
        
        # تحديث الحالة (العمود D -> 4)
        sheets_service.spreadsheets().values().update(
            spreadsheetId=REQUESTS_SHEET_ID, range=f"Feuille 1!D{row_num}",
            valueInputOption="USER_ENTERED", body={"values": [[new_status]]}
        ).execute()
        
        # تحديث ملاحظات الإدارة (العمود K -> 11)
        if admin_note:
            sheets_service.spreadsheets().values().update(
                spreadsheetId=REQUESTS_SHEET_ID, range=f"Feuille 1!K{row_num}",
                valueInputOption="USER_ENTERED", body={"values": [[admin_note]]}
            ).execute()
            
        clear_cache()
        return True
    except Exception as e:
        logger.error(f"Error updating request: {e}")
        return False

# ---------------- Registration Logic ----------------
def update_registration(note_number, student1, student2=None):
    try:
        df_memos = load_memos()
        df_prof_memos = load_prof_memos()
        
        prof_name = df_memos[df_memos["رقم المذكرة"].astype(str).str.strip() == str(note_number).strip()]["الأستاذ"].iloc[0].strip()
        used_prof_password = st.session_state.prof_password.strip()
        
        # 1. تحديث شيت الأساتذة (PROF_MEMOS_SHEET_ID)
        prof_row_idx = df_prof_memos[
            (df_prof_memos["الأستاذ"].astype(str).str.strip() == prof_name) &
            (df_prof_memos["كلمة سر التسجيل"].astype(str).str.strip() == used_prof_password)
        ].index[0] + 2
        col_names = df_prof_memos.columns.tolist()
        
        s1_lname = student1.get('لقب', student1.get('اللقب', ''))
        s1_fname = student1.get('الإسم', student1.get('إسم', ''))
        
        updates = [
            {"range": f"Feuille 1!{col_letter(col_names.index('الطالب الأول')+1)}{prof_row_idx}", "values": [[s1_lname + ' ' + s1_fname]]},
            {"range": f"Feuille 1!{col_letter(col_names.index('تم التسجيل')+1)}{prof_row_idx}", "values": [["نعم"]]},
            {"range": f"Feuille 1!{col_letter(col_names.index('تاريخ التسجيل')+1)}{prof_row_idx}", "values": [[datetime.now().strftime('%Y-%m-%d %H:%M')]]},
            {"range": f"Feuille 1!{col_letter(col_names.index('رقم المذكرة')+1)}{prof_row_idx}", "values": [[note_number]]}
        ]
        if student2 is not None:
            s2_lname = student2.get('لقب', student2.get('اللقب', ''))
            s2_fname = student2.get('الإسم', student2.get('إسم', ''))
            updates.append({"range": f"Feuille 1!{col_letter(col_names.index('الطالب الثاني')+1)}{prof_row_idx}", "values": [[s2_lname + ' ' + s2_fname]]})
        
        sheets_service.spreadsheets().values().batchUpdate(spreadsheetId=PROF_MEMOS_SHEET_ID, body={"valueInputOption": "USER_ENTERED", "data": updates}).execute()

        # 2. تحديث الشيت الرئيسي للمذكرات (MEMOS_SHEET_ID) مع حفظ أرقام التسجيل S و T
        memo_row_idx = df_memos[df_memos["رقم المذكرة"].astype(str).str.strip() == str(note_number).strip()].index[0] + 2
        memo_cols = df_memos.columns.tolist()
        
        # تحديد فهرس الأعمدة S و T (19 و 20)
        try:
            idx_s1 = memo_cols.index('رقم تسجيل ط1') + 1
            idx_s2 = memo_cols.index('رقم تسجيل ط2') + 1
        except:
            idx_s1 = 19 # Fallback to S
            idx_s2 = 20 # Fallback to T

        updates2 = [
            {"range": f"Feuille 1!{col_letter(memo_cols.index('الطالب الأول')+1)}{memo_row_idx}", "values": [[s1_lname + ' ' + s1_fname]]},
            {"range": f"Feuille 1!{col_letter(memo_cols.index('تم التسجيل')+1)}{memo_row_idx}", "values": [["نعم"]]},
            {"range": f"Feuille 1!{col_letter(memo_cols.index('تاريخ التسجيل')+1)}{memo_row_idx}", "values": [[datetime.now().strftime('%Y-%m-%d %H:%M')]]},
            {"range": f"Feuille 1!{col_letter(idx_s1)}{memo_row_idx}", "values": [[student1.get('رقم التسجيل', '')]]}
        ]
        
        if 'كلمة سر التسجيل' in memo_cols:
            updates2.append({"range": f"Feuille 1!{col_letter(memo_cols.index('كلمة سر التسجيل')+1)}{memo_row_idx}", "values": [[used_prof_password]]})
            
        if student2 is not None:
            updates2.append({"range": f"Feuille 1!{col_letter(memo_cols.index('الطالب الثاني')+1)}{memo_row_idx}", "values": [[s2_lname + ' ' + s2_fname]]})
            updates2.append({"range": f"Feuille 1!{col_letter(idx_s2)}{memo_row_idx}", "values": [[student2.get('رقم التسجيل', '')]]})
            
        sheets_service.spreadsheets().values().batchUpdate(spreadsheetId=MEMOS_SHEET_ID, body={"valueInputOption": "USER_ENTERED", "data": updates2}).execute()

        # 3. تحديث شيت الطلبة
        df_students = load_students()
        students_cols = df_students.columns.tolist()
        
        student1_row_idx = df_students[df_students["اسم المستخدم"].astype(str).str.strip() == student1['اسم المستخدم'].strip()].index[0] + 2
        sheets_service.spreadsheets().values().update(
            spreadsheetId=STUDENTS_SHEET_ID, 
            range=f"Feuille 1!{col_letter(students_cols.index('رقم المذكرة')+1)}{student1_row_idx}", 
            valueInputOption="USER_ENTERED", body={"values": [[note_number]]}
        ).execute()
        
        if student2 is not None:
            student2_row_idx = df_students[df_students["اسم المستخدم"].astype(str).str.strip() == student2['اسم المستخدم'].strip()].index[0] + 2
            sheets_service.spreadsheets().values().update(
                spreadsheetId=STUDENTS_SHEET_ID, 
                range=f"Feuille 1!{col_letter(students_cols.index('رقم المذكرة')+1)}{student2_row_idx}", 
                valueInputOption="USER_ENTERED", body={"values": [[note_number]]}
            ).execute()

        time.sleep(2); clear_cache(); time.sleep(1)
        return True, "✅ تم تسجيل المذكرة بنجاح!"
    except Exception as e:
        logger.error(f"Error updating registration: {e}")
        return False, f"❌ خطأ: {str(e)}"

# ---------------- Auth & Verification ----------------
def verify_student(username, password, df_students):
    if df_students.empty: return False, "❌ خطأ في البيانات"
    s = df_students[df_students["اسم المستخدم"].astype(str).str.strip() == username]
    if s.empty: return False, "❌ اسم المستخدم غير موجود"
    if s.iloc[0]["كلمة السر"].strip() != password: return False, "❌ كلمة السر غير صحيحة"
    return True, s.iloc[0]

def verify_students_batch(students_data, df_students):
    verified = []
    for u, p in students_data:
        v, r = verify_student(u, p, df_students)
        if not v: return False, r
        verified.append(r)
    return True, verified

def verify_professor(username, password, df_prof_memos):
    username = sanitize_input(username); password = sanitize_input(password)
    if df_prof_memos.empty: return False, "❌ خطأ في البيانات"
    prof = df_prof_memos[
        (df_prof_memos["إسم المستخدم"].astype(str).str.strip() == username) &
        (df_prof_memos["كلمة المرور"].astype(str).str.strip() == password)
    ]
    if prof.empty: return False, "❌ بيانات الدخول غير صحيحة"
    return True, prof.iloc[0]

def verify_admin(username, password):
    if username in ADMIN_CREDENTIALS and ADMIN_CREDENTIALS[username] == password: return True, username
    return False, "❌ بيانات الدخول غير صحيحة"

def verify_professor_password(note_number, prof_password, df_memos, df_prof_memos):
    note_number = sanitize_input(note_number); prof_password = sanitize_input(prof_password)
    memo_row = df_memos[df_memos["رقم المذكرة"].astype(str).str.strip() == note_number]
    if memo_row.empty: return False, None, "❌ رقم المذكرة غير موجود"
    memo_row = memo_row.iloc[0]
    if str(memo_row.get("تم التسجيل", "")).strip() == "نعم": return False, None, "❌ هذه المذكرة مسجلة مسبقاً"
    prof_row = df_prof_memos[
        (df_prof_memos["الأستاذ"].astype(str).str.strip() == memo_row["الأستاذ"].strip()) &
        (df_prof_memos["كلمة سر التسجيل"].astype(str).str.strip() == prof_password)
    ]
    if prof_row.empty: return False, None, "❌ كلمة سر المشرف غير صحيحة"
    return True, prof_row.iloc[0], None

# ---------------- Session State Initialization ----------------
if 'user_type' not in st.session_state:
    st.session_state.user_type = None
    st.session_state.logged_in = False
    st.session_state.student1 = None; st.session_state.student2 = None; st.session_state.professor = None
    st.session_state.admin_user = None; st.session_state.memo_type = "فردية"
    st.session_state.mode = "register"
    st.session_state.note_number = ""; st.session_state.prof_password = ""; st.session_state.show_confirmation = False

def logout():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.session_state.user_type = None; st.session_state.logged_in = False
    st.rerun()

# Load Initial Data
df_students = load_students()
df_memos = load_memos()
df_prof_memos = load_prof_memos()
df_requests = load_requests()

if df_students.empty or df_memos.empty or df_prof_memos.empty:
    st.error("❌ خطأ في تحميل البيانات الأساسية. يرجى المحاولة لاحقاً.")
    st.stop()

# ============================================================
# Main Application Logic
# ============================================================

# 1. HOME PAGE
if st.session_state.user_type is None:
    st.markdown("<h1 style='text-align: center; margin-bottom: 1rem;'>نظام تسجيل المذكرات</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #94A3B8; font-size: 1.2rem; margin-bottom: 3rem;'>الجامعة محمد البشير الإبراهيمي - كلية الحقوق</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("<div class='card' style='text-align: center;'>", unsafe_allow_html=True)
        st.markdown("<h3>👨‍🎓 فضاء الطلبة</h3>", unsafe_allow_html=True)
        if st.button("دخول الطلبة", key="btn_student", use_container_width=True):
            st.session_state.user_type = "student"; st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    with col2:
        st.markdown("<div class='card' style='text-align: center;'>", unsafe_allow_html=True)
        st.markdown("<h3>👨‍🏫 فضاء الأساتذة</h3>", unsafe_allow_html=True)
        if st.button("دخول الأساتذة", key="btn_prof", use_container_width=True):
            st.session_state.user_type = "professor"; st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    with col3:
        st.markdown("<div class='card' style='text-align: center;'>", unsafe_allow_html=True)
        st.markdown("<h3>⚙️ فضاء الإدارة</h3>", unsafe_allow_html=True)
        if st.button("دخول الإدارة", key="btn_admin", use_container_width=True):
            st.session_state.user_type = "admin"; st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

# 2. STUDENT SPACE
elif st.session_state.user_type == "student":
    if not st.session_state.logged_in:
        st.markdown("<h2>فضاء الطلبة</h2>", unsafe_allow_html=True)
        with st.form("student_login_form"):
            username1 = st.text_input("اسم المستخدم")
            password1 = st.text_input("كلمة السر", type="password")
            if st.form_submit_button("تسجيل الدخول"):
                v, r = verify_student(username1, password1, df_students)
                if not v: st.error(r)
                else: st.session_state.student1 = r; st.session_state.logged_in = True; st.rerun()
    else:
        s = st.session_state.student1
        if st.button("خروج"): logout()
        st.markdown(f"<h2>مرحباً {s['لقب']} {s['الإسم']}</h2>", unsafe_allow_html=True)
        
        my_reg = s.get('رقم التسجيل', '')
        
        # Show Notifications (Requests affecting student)
        my_reqs = df_requests[
            (df_requests["رقم تسجيل الطالب 1"].astype(str).str.strip() == my_reg) | 
            (df_requests["رقم تسجيل الطالب 2"].astype(str).str.strip() == my_reg)
        ]
        if not my_reqs.empty:
            st.markdown("### 📬 تنبيهات هامة")
            for _, r in my_reqs.iterrows():
                if r['الحالة'] == "مرفوض":
                    st.markdown(f"<div class='alert-card'>تم رفض طلب {r['النوع']} المتعلق بك. {r['ملاحظات الإدارة']}</div>", unsafe_allow_html=True)
                elif r['الحالة'] == "موافق عليه":
                     st.markdown(f"<div class='success-card'>تمت الموافقة على طلب {r['النوع']}. يرجى مراجعة أستاذك.</div>", unsafe_allow_html=True)

        # Show Memo Details
        my_memo = df_memos[df_memos["رقم التسجيل"].astype(str).str.strip() == my_reg]
        if not my_memo.empty:
            m = my_memo.iloc[0]
            st.markdown(f"""
            <div class='card'>
                <h4>مذكرتك المسجلة: {m['رقم المذكرة']}</h4>
                <p><b>العنوان:</b> {m['عنوان المذكرة']}</p>
                <p><b>المشرف:</b> {m['الأستاذ']}</p>
                <p><b>تاريخ التسجيل:</b> {m['تاريخ التسجيل']}</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("لم يتم تسجيل مذكرة بعد.")

# 3. PROFESSOR SPACE
elif st.session_state.user_type == "professor":
    if not st.session_state.logged_in:
        st.markdown("<h2>فضاء الأساتذة</h2>", unsafe_allow_html=True)
        with st.form("prof_login_form"):
            u = st.text_input("اسم المستخدم"); p = st.text_input("كلمة المرور", type="password")
            if st.form_submit_button("تسجيل الدخول"):
                v, r = verify_professor(u, p, df_prof_memos)
                if not v: st.error(r)
                else: st.session_state.professor = r; st.session_state.logged_in = True; st.rerun()
    else:
        prof = st.session_state.professor
        prof_name = prof["الأستاذ"]
        if st.button("خروج"): logout()
        
        st.markdown(f"<h2>مرحباً أ. {prof_name}</h2>", unsafe_allow_html=True)
        
        # Stats
        prof_memos = df_memos[df_memos["الأستاذ"].astype(str).str.strip() == prof_name.strip()]
        total = len(prof_memos)
        registered = len(prof_memos[prof_memos["تم التسجيل"].astype(str).str.strip() == "نعم"])
        is_exhausted = registered >= 4
        
        st.markdown(f"<div class='kpi-grid'><div class='kpi-card'><div class='kpi-value'>{total}</div><div class='kpi-label'>إجمالي المذكرات</div></div>"
                    f"<div class='kpi-card'><div class='kpi-value' style='color:#10B981'>{registered}</div><div class='kpi-label'>مسجلة</div></div></div>", unsafe_allow_html=True)
        
        if is_exhausted: st.markdown('<div class="alert-card">لقد استنفذت الحد الأقصى للمذكرات.</div>', unsafe_allow_html=True)

        tab1, tab2, tab3, tab4 = st.tabs(["المذكرات المسجلة", "إرسال طلب", "تنبيهاتي", "المذكرات المتاحة"])
        
        # Tab 1: Registered Memos (With Email Fix)
        with tab1:
            registered_memos = prof_memos[prof_memos["تم التسجيل"].astype(str).str.strip() == "نعم"]
            if not registered_memos.empty:
                for _, m in registered_memos.iterrows():
                    s1_reg = str(m.get('رقم تسجيل ط1', '')).strip()
                    s2_reg = str(m.get('رقم تسجيل ط2', '')).strip()
                    
                    # Accurate Email Lookup via Registration ID
                    s1_name = m.get('الطالب الأول', '--')
                    s1_email = ""
                    if s1_reg:
                        s1_data = df_students[df_students['رقم التسجيل'].astype(str).str.strip() == s1_reg]
                        if not s1_data.empty:
                            s1_email = s1_data.iloc[0].get('البريد الإلكتروني', '')
                            s1_name = s1_data.iloc[0].get('لقب', '') + ' ' + s1_data.iloc[0].get('الإسم', '')

                    s2_name = m.get('الطالب الثاني', '')
                    s2_email = ""
                    if s2_reg:
                        s2_data = df_students[df_students['رقم التسجيل'].astype(str).str.strip() == s2_reg]
                        if not s2_data.empty:
                            s2_email = s2_data.iloc[0].get('البريد الإلكتروني', '')
                            s2_name = s2_data.iloc[0].get('لقب', '') + ' ' + s2_data.iloc[0].get('الإسم', '')

                    st.markdown(f"""
                    <div class='card'>
                        <h4>{m['رقم المذكرة']} - {m['عنوان المذكرة']}</h4>
                        <p><b>الطالب 1:</b> {s1_name} <br> <b>📧 Email:</b> {s1_email if s1_email else 'غير متوفر'}</p>
                        {f"<p><b>الطالب 2:</b> {s2_name} <br> <b>📧 Email:</b> {s2_email if s2_email else 'غير متوفر'}</p>" if s2_name else ""}
                    </div>
                    """, unsafe_allow_html=True)
            else: st.info("لا توجد مذكرات مسجلة.")

        # Tab 2: Create Request
        with tab2:
            st.subheader("تقديم طلب جديد")
            with st.form("req_form"):
                req_type = st.selectbox("نوع الطلب:", ["تغيير عنوان", "التنازل عن طالب", "إضافة طالب لمذكرة فردية"])
                memo_num = st.selectbox("رقم المذكرة:", [""] + sorted(registered_memos["رقم المذكرة"].astype(str).unique()))
                
                # Context Display
                s1_reg_disp = ""; s2_reg_disp = ""
                if memo_num:
                    m_data = df_memos[df_memos["رقم المذكرة"].astype(str).str.strip() == memo_num].iloc[0]
                    s1_reg_disp = m_data.get('رقم تسجيل ط1', '')
                    s2_reg_disp = m_data.get('رقم تسجيل ط2', '')
                    st.info(f"بيانات الحالية: ط1 ({s1_reg_disp}) - ط2 ({s2_reg_disp})")

                justification = st.text_area("المبررات والتفاصيل", height=100)
                new_title = ""; target_student = ""
                
                if req_type == "تغيير عنوان":
                    new_title = st.text_input("العنوان الجديد:")
                elif req_type == "التنازل عن طالب":
                    target_student = st.selectbox("اختر الطالب:", ["الطالب الأول", "الطالب الثاني", "الطالبين معاً"])
                elif req_type == "إضافة طالب لمذكرة فردية":
                    # في هذا النوع، المبررات يجب أن تحتوي على معلومات الطالب الجديد
                    pass 

                if st.form_submit_button("إرسال الطلب"):
                    if not justification: st.error("يرجى كتابة المبررات")
                    else:
                        # Logic for Request Payload
                        req_s1 = ""
                        req_s2 = ""
                        
                        if req_type == "التنازل عن طالب":
                            if target_student == "الطالب الأول" or target_student == "الطالبين معاً": req_s1 = s1_reg_disp
                            if target_student == "الطالب الثاني" or target_student == "الطالبين معاً": req_s2 = s2_reg_disp
                        
                        s, m = create_request(prof_name, req_type, memo_num, req_s1, req_s2, new_title, justification)
                        if s: st.success(m); time.sleep(1); clear_cache(); st.rerun()
                        else: st.error(m)

        # Tab 3: My Notifications
        with tab3:
            st.subheader("حالة طلباتي")
            my_reqs = df_requests[df_requests["الأستاذ"].astype(str).str.strip() == prof_name.strip()]
            if not my_reqs.empty:
                for _, r in my_reqs.iterrows():
                    status_color = "status-pending" if r['الحالة']=="قيد الانتظار" else ("status-approved" if r['الحالة']=="موافق عليه" else "status-rejected")
                    st.markdown(f"""
                    <div class='card' style='border-right: 4px solid #aaa;'>
                        <div style='display:flex; justify-content:space-between;'>
                            <b>{r['النوع']} - {r['رقم المذكرة']}</b>
                            <span class='status-badge {status_color}'>{r['الحالة']}</span>
                        </div>
                        <p style='font-size:0.9em; color:#ccc;'>{r['الوقت']}</p>
                        <p>{r['المبررات']}</p>
                        {f"<p style='color:#fbbf24; font-weight:bold;'>رد الإدارة: {r['ملاحظات الإدارة']}</p>" if r['ملاحظات الإدارة'] else ""}
                    </div>
                    """, unsafe_allow_html=True)
            else: st.info("لا توجد طلبات.")

        # Tab 4: Available Memos (Simple View)
        with tab4:
             if not is_exhausted:
                 avail = prof_memos[prof_memos["تم التسجيل"].astype(str).str.strip() != "نعم"]
                 if not avail.empty:
                     for _, m in avail.iterrows():
                         st.markdown(f"**{m['رقم المذكرة']}** - {m['عنوان المذكرة']} ({m['التخصص']})")
                 else: st.success("جميع العناوين مسجلة.")
             else:
                 st.info("لا يوجد عناوين متاحة (تم استنفاذ الحد).")

# 4. ADMIN SPACE
elif st.session_state.user_type == "admin":
    if not st.session_state.logged_in:
        st.markdown("<h2>فضاء الإدارة</h2>", unsafe_allow_html=True)
        with st.form("admin_login"):
            u = st.text_input("اسم المستخدم"); p = st.text_input("كلمة المرور", type="password")
            if st.form_submit_button("دخول"):
                v, r = verify_admin(u, p)
                if not v: st.error(r)
                else: st.session_state.admin_user = r; st.session_state.logged_in = True; st.rerun()
    else:
        if st.button("خروج"): logout()
        st.header("لوحة تحكم الإدارة")
        
        tab1, tab2 = st.tabs(["صندوق الطلبات", "سجل المذكرات"])
        
        with tab1:
            st.subheader("الطلبات الواردة (قيد الانتظار)")
            pending_reqs = df_requests[df_requests["الحالة"] == "قيد الانتظار"]
            
            if not pending_reqs.empty:
                for _, r in pending_reqs.iterrows():
                    with st.expander(f"طلب {r['النوع']} - {r['الأستاذ']} ({r['رقم المذكرة']})", expanded=True):
                        st.markdown(f"**الوقت:** {r['الوقت']}")
                        st.markdown(f"**المبررات:** {r['المبررات']}")
                        if r['العنوان الجديد']: st.markdown(f"**العنوان الجديد:** {r['العنوان الجديد']}")
                        
                        # Check if it's a waiver request to show who is being dropped
                        if r['رقم تسجيل الطالب 1']: st.markdown(f"⚠️ طلب تنازل/تغيير يشمل: الطالب 1 ({r['رقم تسجيل الطالب 1']})")
                        if r['رقم تسجيل الطالب 2']: st.markdown(f"⚠️ طلب تنازل/تغيير يشمل: الطالب 2 ({r['رقم تسجيل الطالب 2']})")
                        
                        admin_note = st.text_input("ملاحظات للإدارة:", key=f"note_{r['رقم الطلب']}")
                        c1, c2 = st.columns(2)
                        
                        with c1:
                            if st.button("✅ موافقة", key=f"app_{r['رقم الطلب']}"):
                                update_request_status(r['رقم الطلب'], "موافق عليه", admin_note)
                                st.success("تمت الموافقة"); clear_cache(); st.rerun()
                        with c2:
                            if st.button("❌ رفض", key=f"rej_{r['رقم الطلب']}"):
                                update_request_status(r['رقم الطلب'], "مرفوض", admin_note)
                                st.warning("تم الرفض"); clear_cache(); st.rerun()
            else:
                st.success("لا توجد طلبات معلقة.")

            st.markdown("---")
            st.subheader("أرشيف الطلبات")
            hist_reqs = df_requests[df_requests["الحالة"] != "قيد الانتظار"]
            if not hist_reqs.empty:
                st.dataframe(hist_reqs[['الوقت', 'النوع', 'الأستاذ', 'الحالة', 'رقم المذكرة', 'ملاحظات الإدارة']], use_container_width=True)

        with tab2:
            st.dataframe(df_memos, use_container_width=True)

st.markdown("---")
st.markdown('<div style="text-align:center; color:#64748B; font-size:12px; padding:20px;">© 2026 جامعة محمد البشير الإبراهيمي - كلية الحقوق</div>', unsafe_allow_html=True)
