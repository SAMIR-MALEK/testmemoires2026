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

# ---------------- CSS (تم دمج التصميم النهائي) ----------------
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
.stButton>button { background-color: #2F6F7E !important; color: white !important; border: none; border-radius: 12px; font-weight: bold; padding: 10px 20px; }
.stButton>button:hover { background-color: #285E6B !important; transform: translateY(-2px); }

/* البطاقات */
.card { background: rgba(30, 41, 59, 0.95); border: 1px solid rgba(255,255,255,0.08); border-radius: 20px; padding: 20px; margin-bottom: 20px; border-top: 3px solid #2F6F7E; }
.kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 2rem; }
.kpi-card { background: linear-gradient(145deg, #1E293B, #0F172A); border: 1px solid rgba(255,255,255,0.05); border-radius: 16px; padding: 1.5rem; text-align: center; }
.kpi-value { font-size: 2rem; font-weight: 900; color: #FFD700; }
.kpi-label { font-size: 0.9rem; color: #94A3B8; }

/* الإشعارات */
.alert-card { background: linear-gradient(90deg, #8B4513, #A0522D); border: 1px solid #CD853F; color: white; padding: 15px; border-radius: 12px; margin-bottom: 20px; }
.success-card { background: linear-gradient(90deg, #065f46, #047857); border: 1px solid #34d399; color: white; padding: 15px; border-radius: 12px; margin-bottom: 20px; }

/* التبويبات */
.stTabs [data-baseweb="tab-list"] { gap: 2rem; padding-bottom: 10px; }
.stTabs [aria-selected="true"] { background: rgba(47, 111, 126, 0.2); color: #FFD700; border-bottom: 2px solid #FFD700; font-weight: bold; }

/* شارات الحالة */
.status-badge { padding: 4px 10px; border-radius: 99px; font-size: 0.8em; font-weight: bold; }
.status-pending { background: #F59E0B; color: #fff; }
.status-approved { background: #10B981; color: #fff; }
.status-rejected { background: #EF4444; color: #fff; }
</style>
""", unsafe_allow_html=True)

# ================= Google Sheets Config =================
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
try:
    info = st.secrets["service_account"]
    credentials = Credentials.from_service_account_info(info, scopes=SCOPES)
    sheets_service = build('sheets', 'v4', credentials=credentials)
except Exception as e:
    st.error("⚠️ خطأ في ملف Secrets أو الاتصال بـ Google.")
    st.stop()

# --- معرفات الشيتات ---
STUDENTS_SHEET_ID = "1gvNkOVVKo6AO07dRKMnSQw6vZ3KdUnW7I4HBk61Sqns"
MEMOS_SHEET_ID = "1LNJMBAye4QIQy7JHz6F8mQ6-XNC1weZx1ozDZFfjD5s"
PROF_MEMOS_SHEET_ID = "1OnZi1o-oPMUI_W_Ew-op0a1uOhSj006hw_2jrMD6FSE"

# === ضع معرف الشيت الرابع (الطلبات) هنا ===
REQUESTS_SHEET_ID = "YOUR_REQUESTS_SHEET_ID_HERE" 

STUDENTS_RANGE = "Feuille 1!A1:L1000"
MEMOS_RANGE = "Feuille 1!A1:T1000" 
PROF_MEMOS_RANGE = "Feuille 1!A1:P1000"
REQUESTS_RANGE = "Feuille 1!A1:K1000"

ADMIN_CREDENTIALS = {"admin": "admin2026", "dsp": "dsp@2026"}

# ================= Helpers =================
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

# ================= Data Loading =================
@st.cache_data(ttl=60)
def load_students():
    try:
        result = sheets_service.spreadsheets().values().get(spreadsheetId=STUDENTS_SHEET_ID, range=STUDENTS_RANGE).execute()
        values = result.get('values', [])
        if not values: return pd.DataFrame()
        df = pd.DataFrame(values[1:], columns=values[0])
        df.columns = [c.strip() for c in df.columns]
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
        headers = values[0]
        while len(headers) < 20: headers.append(f"Col_{len(headers)}")
        df = pd.DataFrame(values[1:], columns=headers)
        df.columns = [c.strip() for c in df.columns]
        
        # Force columns S and T (Indices 18 and 19)
        if len(df.columns) > 18: df['رقم تسجيل ط1'] = df.iloc[:, 18]
        if len(df.columns) > 19: df['رقم تسجيل ط2'] = df.iloc[:, 19]
        return df
    except Exception as e:
        logger.error(f"Error loading memos: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=30)
def load_requests():
    if not REQUESTS_SHEET_ID or REQUESTS_SHEET_ID == "YOUR_REQUESTS_SHEET_ID_HERE":
        return pd.DataFrame()
    try:
        result = sheets_service.spreadsheets().values().get(spreadsheetId=REQUESTS_SHEET_ID, range=REQUESTS_RANGE).execute()
        values = result.get('values', [])
        if not values: return pd.DataFrame()
        expected_cols = ["رقم الطلب", "الوقت", "النوع", "الحالة", "الأستاذ", "رقم المذكرة", 
                         "رقم تسجيل الطالب 1", "رقم تسجيل الطالب 2", "العنوان الجديد", "المبررات", "ملاحظات الإدارة"]
        if len(values) == 1: return pd.DataFrame(columns=expected_cols)
        if len(values[0]) == len(expected_cols):
            df = pd.DataFrame(values[1:], columns=values[0])
        else:
            df = pd.DataFrame(values[1:], columns=expected_cols)
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
        df.columns = [c.strip() for c in df.columns]
        return df
    except Exception as e:
        return pd.DataFrame()

# ================= Request Logic =================
def create_request(prof_name, req_type, memo_number, s1_reg, s2_reg, new_title, justification):
    if REQUESTS_SHEET_ID == "YOUR_REQUESTS_SHEET_ID_HERE":
        return False, "يرجى ضبط معرف شيت الطلبات في الكود"
    
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
        return True, "تم إرسال الطلب"
    except Exception as e:
        logger.error(f"Error creating request: {e}")
        return False, f"فشل الإرسال: {str(e)}"

def update_request_status(req_id, new_status, admin_note=""):
    if REQUESTS_SHEET_ID == "YOUR_REQUESTS_SHEET_ID_HERE": return False
    try:
        df_req = load_requests()
        if df_req.empty: return False
        row_idx = df_req[df_req["رقم الطلب"] == req_id].index
        if len(row_idx) == 0: return False
        
        row_num = row_idx[0] + 2
        
        sheets_service.spreadsheets().values().update(
            spreadsheetId=REQUESTS_SHEET_ID, range=f"Feuille 1!D{row_num}",
            valueInputOption="USER_ENTERED", body={"values": [[new_status]]}
        ).execute()
        
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

# ================= Registration Logic =================
def update_registration(note_number, student1, student2=None):
    try:
        df_memos = load_memos()
        df_prof_memos = load_prof_memos()
        
        memo_mask = df_memos["رقم المذكرة"].astype(str).str.strip() == str(note_number).strip()
        if memo_mask.sum() == 0: return False, "المذكرة غير موجودة"
        
        prof_name = df_memos[memo_mask]["الأستاذ"].iloc[0].strip()
        used_prof_password = st.session_state.prof_password.strip()
        
        # 1. Update Prof Sheet
        prof_mask = (df_prof_memos["الأستاذ"].astype(str).str.strip() == prof_name) & \
                     (df_prof_memos["كلمة سر التسجيل"].astype(str).str.strip() == used_prof_password)
        if prof_mask.sum() == 0: return False, "بيانات المشرف غير صحيحة"
        
        prof_row_idx = prof_mask.index[0] + 2
        col_names = df_prof_memos.columns.tolist()
        
        s1_lname = student1.get('لقب', student1.get('اللقب', ''))
        s1_fname = student1.get('الإسم', student1.get('إسم', ''))
        
        updates = [
            {"range": f"Feuille 1!{col_letter(col_names.index('الطالب الأول')+1)}{prof_row_idx}", "values": [[s1_lname + ' ' + s1_fname]]},
            {"range": f"Feuille 1!{col_letter(col_names.index('تم التسجيل')+1)}{prof_row_idx}", "values": [["نعم"]]},
            {"range": f"Feuille 1!{col_letter(col_names.index('تاريخ التسجيل')+1)}{prof_row_idx}", "values": [[datetime.now().strftime('%Y-%m-%d %H:%M')]]},
            {"range": f"Feuille 1!{col_letter(col_names.index('رقم المذكرة')+1)}{prof_row_idx}", "values": [[note_number]]}
        ]
        if student2:
            s2_lname = student2.get('لقب', student2.get('اللقب', ''))
            s2_fname = student2.get('الإسم', student2.get('إسم', ''))
            updates.append({"range": f"Feuille 1!{col_letter(col_names.index('الطالب الثاني')+1)}{prof_row_idx}", "values": [[s2_lname + ' ' + s2_fname]]})
        
        sheets_service.spreadsheets().values().batchUpdate(spreadsheetId=PROF_MEMOS_SHEET_ID, body={"valueInputOption": "USER_ENTERED", "data": updates}).execute()

        # 2. Update Main Memos Sheet (S and T)
        memo_row_idx = memo_mask.index[0] + 2
        memo_cols = df_memos.columns.tolist()
        
        updates2 = [
            {"range": f"Feuille 1!S{memo_row_idx}", "values": [[student1.get('رقم التسجيل', '')]]}, # Col S
            {"range": f"Feuille 1!{col_letter(memo_cols.index('الطالب الأول')+1)}{memo_row_idx}", "values": [[s1_lname + ' ' + s1_fname]]},
            {"range": f"Feuille 1!{col_letter(memo_cols.index('تم التسجيل')+1)}{memo_row_idx}", "values": [["نعم"]]},
            {"range": f"Feuille 1!{col_letter(memo_cols.index('تاريخ التسجيل')+1)}{memo_row_idx}", "values": [[datetime.now().strftime('%Y-%m-%d %H:%M')]]}
        ]
        
        if student2:
            updates2.append({"range": f"Feuille 1!T{memo_row_idx}", "values": [[student2.get('رقم التسجيل', '')]]}) # Col T
            updates2.append({"range": f"Feuille 1!{col_letter(memo_cols.index('الطالب الثاني')+1)}{memo_row_idx}", "values": [[s2_lname + ' ' + s2_fname]]})
            
        sheets_service.spreadsheets().values().batchUpdate(spreadsheetId=MEMOS_SHEET_ID, body={"valueInputOption": "USER_ENTERED", "data": updates2}).execute()

        # 3. Update Students
        df_students = load_students()
        students_cols = df_students.columns.tolist()
        s1_idx = df_students[df_students["اسم المستخدم"].astype(str).str.strip() == student1['اسم المستخدم'].strip()].index[0] + 2
        sheets_service.spreadsheets().values().update(
            spreadsheetId=STUDENTS_SHEET_ID, 
            range=f"Feuille 1!{col_letter(students_cols.index('رقم المذكرة')+1)}{s1_idx}", 
            valueInputOption="USER_ENTERED", body={"values": [[note_number]]}
        ).execute()
        
        if student2:
            s2_idx = df_students[df_students["اسم المستخدم"].astype(str).str.strip() == student2['اسم المستخدم'].strip()].index[0] + 2
            sheets_service.spreadsheets().values().update(
                spreadsheetId=STUDENTS_SHEET_ID, 
                range=f"Feuille 1!{col_letter(students_cols.index('رقم المذكرة')+1)}{s2_idx}", 
                valueInputOption="USER_ENTERED", body={"values": [[note_number]]}
            ).execute()

        time.sleep(2); clear_cache(); time.sleep(1)
        return True, "✅ تم التسجيل"
    except Exception as e:
        logger.error(f"Error updating: {e}")
        return False, f"❌ خطأ: {str(e)}"

# ================= Auth Logic =================
def verify_student(username, password, df_students):
    if df_students.empty: return False, "❌ خطأ في البيانات"
    s = df_students[df_students["اسم المستخدم"].astype(str).str.strip() == username]
    if s.empty: return False, "❌ المستخدم غير موجود"
    if s.iloc[0]["كلمة السر"].strip() != password: return False, "❌ كلمة السر خاطئة"
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
    if prof.empty: return False, "❌ بيانات خاطئة"
    return True, prof.iloc[0]

def verify_admin(username, password):
    if username in ADMIN_CREDENTIALS and ADMIN_CREDENTIALS[username] == password: return True, username
    return False, "❌ بيانات خاطئة"

def verify_professor_password(note_number, prof_password, df_memos, df_prof_memos):
    note_number = sanitize_input(note_number); prof_password = sanitize_input(prof_password)
    memo_row = df_memos[df_memos["رقم المذكرة"].astype(str).str.strip() == note_number]
    if memo_row.empty: return False, None, "❌ المذكرة غير موجودة"
    memo_row = memo_row.iloc[0]
    if str(memo_row.get("تم التسجيل", "")).strip() == "نعم": return False, None, "❌ مسجلة مسبقاً"
    prof_row = df_prof_memos[
        (df_prof_memos["الأستاذ"].astype(str).str.strip() == memo_row["الأستاذ"].strip()) &
        (df_prof_memos["كلمة سر التسجيل"].astype(str).str.strip() == prof_password)
    ]
    if prof_row.empty: return False, None, "❌ كلمة سر المشرف خاطئة"
    return True, prof_row.iloc[0], None

# ================= Session Init =================
if 'user_type' not in st.session_state:
    st.session_state.user_type = None
    st.session_state.logged_in = False
    st.session_state.student1 = None; st.session_state.student2 = None; st.session_state.professor = None
    st.session_state.admin_user = None; st.session_state.memo_type = "فردية"
    st.session_state.mode = "register"
    st.session_state.note_number = ""; st.session_state.prof_password = ""; st.session_state.show_confirmation = False

def logout():
    for key in list(st.session_state.keys()): del st.session_state[key]
    st.session_state.user_type = None; st.session_state.logged_in = False
    st.rerun()

# ================= Main Logic =================

df_students = load_students()
df_memos = load_memos()
df_prof_memos = load_prof_memos()
df_requests = load_requests()

if df_students.empty: st.error("❌ خطأ: شيت الطلاب فارغ."); st.stop()
if df_memos.empty: st.error("❌ خطأ: شيت المذكرات فارغ."); st.stop()
if df_prof_memos.empty: st.error("❌ خطأ: شيت الأساتذة فارغ."); st.stop()

# 1. HOME
if st.session_state.user_type is None:
    st.markdown("<h1 style='text-align:center;'>نظام تسجيل المذكرات</h1>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("👨‍🎓 طلبة"): st.session_state.user_type = "student"; st.rerun()
    with c2:
        if st.button("👨‍🏫 أساتذة"): st.session_state.user_type = "professor"; st.rerun()
    with c3:
        if st.button("⚙️ إدارة"): st.session_state.user_type = "admin"; st.rerun()

# 2. STUDENTS
elif st.session_state.user_type == "student":
    if not st.session_state.logged_in:
        with st.form("s_login"):
            u = st.text_input("اسم المستخدم"); p = st.text_input("كلمة السر", type="password")
            if st.form_submit_button("دخول"):
                v, r = verify_student(u, p, df_students)
                if not v: st.error(r)
                else: st.session_state.student1 = r; st.session_state.logged_in = True; st.rerun()
    else:
        s = st.session_state.student1
        if st.button("خروج"): logout()
        st.markdown(f"<h2>مرحباً {s['لقب']} {s['الإسم']}</h2>", unsafe_allow_html=True)
        my_reg = s.get('رقم التسجيل', '')
        
        my_reqs = df_requests[
            (df_requests["رقم تسجيل الطالب 1"].astype(str).str.strip() == my_reg) | 
            (df_requests["رقم تسجيل الطالب 2"].astype(str).str.strip() == my_reg)
        ]
        if not my_reqs.empty:
            st.markdown("### 📬 تنبيهات")
            for _, r in my_reqs.iterrows():
                if r['الحالة'] == "مرفوض":
                    st.markdown(f"<div class='alert-card'>تم رفض طلب {r['نوع']}. {r['ملاحظات الإدارة']}</div>", unsafe_allow_html=True)
                elif r['الحالة'] == "موافق عليه":
                     st.markdown(f"<div class='success-card'>تم الموافقة على طلب {r['نوع']}.</div>", unsafe_allow_html=True)

        my_memo = df_memos[df_memos["رقم تسجيل ط1"].astype(str).str.strip() == my_reg]
        if my_memo.empty:
            my_memo = df_memos[df_memos["رقم تسجيل ط2"].astype(str).str.strip() == my_reg]
            
        if not my_memo.empty:
            m = my_memo.iloc[0]
            st.markdown(f"""
            <div class='card'>
                <h4>مذكرتك: {m['رقم المذكرة']}</h4>
                <p>{m['عنوان المذكرة']}</p>
                <p>المشرف: {m['الأستاذ']}</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("لا توجد مذكرة مسجلة.")

# 3. PROFESSOR
elif st.session_state.user_type == "professor":
    if not st.session_state.logged_in:
        with st.form("p_login"):
            u = st.text_input("اسم المستخدم"); p = st.text_input("كلمة المرور", type="password")
            if st.form_submit_button("دخول"):
                v, r = verify_professor(u, p, df_prof_memos)
                if not v: st.error(r)
                else: st.session_state.professor = r; st.session_state.logged_in = True; st.rerun()
    else:
        prof = st.session_state.professor
        prof_name = prof["الأستاذ"]
        if st.button("خروج"): logout()
        st.markdown(f"<h2>أ. {prof_name}</h2>", unsafe_allow_html=True)
        
        prof_memos = df_memos[df_memos["الأستاذ"].astype(str).str.strip() == prof_name.strip()]
        reg_memos = prof_memos[prof_memos["تم التسجيل"].astype(str).str.strip() == "نعم"]
        
        tab1, tab2, tab3 = st.tabs(["المذكرات", "طلباتي", "المتاحة"])
        
        with tab1:
            for _, m in reg_memos.iterrows():
                s1_reg = str(m['رقم تسجيل ط1']).strip()
                s2_reg = str(m['رقم تسجيل ط2']).strip()
                
                s1_data = df_students[df_students['رقم التسجيل'].astype(str).str.strip() == s1_reg]
                s1_name = m.get('الطالب الأول', '--')
                s1_email = ""
                if not s1_data.empty:
                    s1_email = s1_data.iloc[0].get('البريد الإلكتروني', '')
                    s1_name = s1_data.iloc[0].get('لقب', '') + ' ' + s1_data.iloc[0].get('الإسم', '')

                s2_name = ""
                s2_email = ""
                if s2_reg:
                    s2_data = df_students[df_students['رقم التسجيل'].astype(str).str.strip() == s2_reg]
                    s2_name = m.get('الطالب الثاني', '')
                    if not s2_data.empty:
                        s2_email = s2_data.iloc[0].get('البريد الإلكتروني', '')
                        s2_name = s2_data.iloc[0].get('لقب', '') + ' ' + s2_data.iloc[0].get('الإسم', '')

                st.markdown(f"""
                <div class='card'>
                    <h4>{m['رقم المذكرة']} - {m['عنوان المذكرة']}</h4>
                    <p>👤 {s1_name} 📧 {s1_email}</p>
                    {f"<p>👤 {s2_name} 📧 {s2_email}</p>" if s2_name else ""}
                </div>
                """, unsafe_allow_html=True)
        
        with tab2:
            st.subheader("إرسال طلب")
            with st.form("req"):
                r_type = st.selectbox("النوع:", ["تغيير عنوان", "التنازل", "إضافة طالب"])
                r_memo = st.selectbox("المذكرة:", [""] + sorted(reg_memos["رقم المذكرة"].astype(str).unique()))
                reason = st.text_area("المبررات")
                
                s1_reg = ""; s2_reg = ""; new_title = ""
                if r_memo:
                    m_data = df_memos[df_memos["رقم المذكرة"].astype(str).str.strip() == r_memo].iloc[0]
                    if r_type == "التنازل":
                        target = st.selectbox("الطالب:", ["الطالب الأول", "الطالب الثاني", "كلاهما"])
                        if target in ["الطالب الأول", "كلاهما"]: s1_reg = m_data['رقم تسجيل ط1']
                        if target in ["الطالب الثاني", "كلاهما"]: s2_reg = m_data['رقم تسجيل ط2']
                    elif r_type == "تغيير عنوان":
                        new_title = st.text_input("العنوان الجديد")
                
                if st.form_submit_button("إرسال"):
                    s, m = create_request(prof_name, r_type, r_memo, s1_reg, s2_reg, new_title, reason)
                    if s: st.success(m); time.sleep(1); clear_cache(); st.rerun()
                    else: st.error(m)

            my_reqs = df_requests[df_requests["الأستاذ"] == prof_name]
            if not my_reqs.empty:
                st.markdown("---")
                for _, r in my_reqs.iterrows():
                    c = "status-pending" if r['الحالة']=="قيد الانتظار" else ("status-approved" if r['الحالة']=="موافق عليه" else "status-rejected")
                    st.markdown(f"<span class='status-badge {c}'>{r['الحالة']}</span> **{r['نوع']}** ({r['رقم المذكرة']}) - {r['ملاحظات الإدارة']}", unsafe_allow_html=True)

        with tab3:
            avail = prof_memos[prof_memos["تم التسجيل"].astype(str).str.strip() != "نعم"]
            for _, m in avail.iterrows():
                st.markdown(f"**{m['رقم المذكرة']}** - {m['عنوان المذكرة']}")

# 4. ADMIN
elif st.session_state.user_type == "admin":
    if not st.session_state.logged_in:
        with st.form("a_login"):
            u = st.text_input("اسم المستخدم"); p = st.text_input("كلمة المرور", type="password")
            if st.form_submit_button("دخول"):
                v, r = verify_admin(u, p)
                if not v: st.error(r)
                else: st.session_state.admin_user = r; st.session_state.logged_in = True; st.rerun()
    else:
        if st.button("خروج"): logout()
        st.header("الإدارة")
        
        tab1, tab2 = st.tabs(["الطلبات", "البيانات"])
        
        with tab1:
            pending = df_requests[df_requests["الحالة"] == "قيد الانتظار"]
            if not pending.empty:
                for _, r in pending.iterrows():
                    with st.expander(f"طلب {r['نوع']} - {r['الأستاذ']}"):
                        st.write(f"**الوقت:** {r['الوقت']}")
                        st.write(f"**المبررات:** {r['المبررات']}")
                        note = st.text_input("ملاحظة:", key=f"n_{r['رقم الطلب']}")
                        c1, c2 = st.columns(2)
                        if c1.button("موافقة", key=f"y_{r['رقم الطلب']}"): 
                            update_request_status(r['رقم الطلب'], "موافق عليه", note); clear_cache(); st.rerun()
                        if c2.button("رفض", key=f"n_{r['رقم الطلب']}"): 
                            update_request_status(r['رقم الطلب'], "مرفوض", note); clear_cache(); st.rerun()
            else:
                st.success("لا توجد طلبات معلقة")
        
        with tab2:
            st.dataframe(df_memos)

st.markdown("---")
st.markdown('<div style="text-align:center; color:#666; font-size:12px;">© 2026 جامعة محمد البشير الإبراهيمي - كلية الحقوق</div>', unsafe_allow_html=True)
