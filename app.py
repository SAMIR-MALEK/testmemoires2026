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
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;900&display=swap" rel="stylesheet">
<style>
html, body, [class*="css"] { font-family: 'Cairo', sans-serif !important; direction: rtl; text-align: right; }
.main { background-color: #0A1B2C; color: #ffffff; }
.block-container { padding: 2rem; background-color: #1A2A3D; border-radius: 16px; margin: auto; }
h1, h2, h3, h4 { font-weight: 700; margin-bottom: 1rem; color: #F8FAFC; }
label, p, span { color: #E2E8F0; }
.stTextInput label, .stSelectbox label { color: #F8FAFC !important; font-weight: 600; }

/* الأزرار */
.stButton>button,
button[kind="primary"],
div[data-testid="stFormSubmitButton"] button {
    background-color: #2F6F7E !important; color: #ffffff !important; font-size: 16px;
    font-weight: 600; padding: 14px 32px; border: none !important; border-radius: 12px !important;
    cursor: pointer; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2); transition: all 0.3s ease;
    width: 100%; text-align: center; display: flex; justify-content: center; align-items: center; gap: 10px;
}
.stButton>button:hover { background-color: #285E6B !important; transform: translateY(-2px); }

/* البطاقات */
.card { 
    background: rgba(30, 41, 59, 0.95); border: 1px solid rgba(255,255, 255, 0.08);
    border-radius: 20px; padding: 30px; margin-bottom: 20px; box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.2); 
    border-top: 3px solid #2F6F7E;
}
.card:hover { transform: translateY(-2px); box-shadow: 0 30px 40px -5px rgba(0, 0, 0, 0.4); }

.kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 1.5rem; margin-bottom: 2.5rem; }
.kpi-card {
    background: linear-gradient(145deg, #1E293B, #0F172A); border: 1px solid rgba(255, 255, 255, 0.05); border-radius: 16px; padding: 2.5rem 1rem;
    text-align: center; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3); position: relative; overflow: hidden;
}
.kpi-value { font-size: 2.5rem; font-weight: 900; color: #FFD700; margin: 15px 0; }
.kpi-label { font-size: 1.2rem; color: #94A3B8; font-weight: 600; text-transform: uppercase; }

.alert-card {
    background: linear-gradient(90deg, #8B4513 0%, #A0522D 100%); border: 1px solid #CD853F; color: white; padding: 25px; border-radius: 12px;
    text-align: center; font-size: 16px; font-weight: bold;
}

.progress-container { background-color: #0F172A; border-radius: 99px; padding: 6px; margin: 20px 0; overflow: hidden; }
.progress-bar {
    height: 24px; border-radius: 99px; background: linear-gradient(90deg, #2F6F7E 0%, #285E6B 50%, #FFD700 100%);
    transition: width 1s cubic-bezier(0.4, 0, 0.2, 1);
}

.stDataFrame { border-radius: 12px; overflow: hidden; border: 1px solid rgba(255,255, 255, 0.1); background: #1E293B; }
.stDataFrame th { background-color: #0F172A; color: #FFD700; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# ---------------- Google Sheets ----------------
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
try:
    info = st.secrets["service_account"]
    credentials = Credentials.from_service_account_info(info, scopes=SCOPES)
    sheets_service = build('sheets', 'v4', credentials=credentials)
except Exception as e:
    st.error("⚠️ خطأ في الاتصال بـ Google Sheets")
    st.stop()

STUDENTS_SHEET_ID = "1gvNkOVVKo6AO07dRKMnSQw6vZ3KdUnW7I4HBk61Sqns"
MEMOS_SHEET_ID = "1LNJMBAye4QIQy7JHz6F8mQ6-XNC1weZx1ozDZFfjD5s"
PROF_MEMOS_SHEET_ID = "1OnZi1o-oPMUI_W_Ew-op0a1uOhSj006hw_2jrMD6FSE"
REQUESTS_SHEET_ID = "1sTJ6BZRM4Qgt0w2xUkpFZqquL-hfriMYTSN3x1_12_o"

STUDENTS_RANGE = "Feuille 1!A1:L1000"
MEMOS_RANGE = "Feuille 1!A1:T1000" 
PROF_MEMOS_RANGE = "Feuille 1!A1:P1000"
REQUESTS_RANGE = "Feuille 1!A1:K1000"

ADMIN_CREDENTIALS = {"admin": "admin2026", "dsp": "dsp@2026"}
EMAIL_SENDER = "domaine.dsp@univ-bba.dz"
EMAIL_PASSWORD = "oevruyiztgikwzah"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
ADMIN_EMAIL = "domaine.dsp@univ-bba.dz"

# ---------------- Helpers ----------------
def col_letter(n):
    result = ""
    while n > 0:
        n, remainder = divmod(n - 1, 26)
        result = chr(65 + remainder) + result
    return result

def sanitize_input(text):
    if not text: return ""
    return str(text).strip()

def normalize_name(name):
    if pd.isna(name): return ""
    return " ".join(str(name).strip().split())

def get_student_email(reg_no, full_name, df_students):
    # البحث في عدة أعمدة محتملة للإيميل
    email_cols = ["البريد الإلكتروني", "البريد المهني", "email", "Email"]
    
    if reg_no:
        match = df_students[df_students["رقم التسجيل"].astype(str).str.strip() == str(reg_no).strip()]
        if not match.empty:
            for col in email_cols:
                if col in match.columns:
                    email = match.iloc[0].get(col, "").strip()
                    if email and "@" in email: return email
    
    # الاحتياطي بالاسم
    if full_name:
        parts = full_name.strip().split(' ', 1)
        if len(parts) == 2:
            lname, fname = parts[0], parts[1]
            possible_lname = ["لقب", "اللقب"]
            possible_fname = ["إسم", "إسم", "اسم"]
            
            for pl in possible_lname:
                for pf in possible_fname:
                    if pl in df_students.columns and pf in df_students.columns:
                        match = df_students[
                            (df_students[pl].astype(str).str.strip() == lname) & 
                            (df_students[pf].astype(str).str.strip() == fname)
                        ]
                        if not match.empty:
                            for col in email_cols:
                                if col in match.columns:
                                    email = match.iloc[0].get(col, "").strip()
                                    if email and "@" in email: return email
    return ""

# ---------------- تحميل البيانات ----------------
@st.cache_data(ttl=60)
def load_students():
    try:
        result = sheets_service.spreadsheets().values().get(spreadsheetId=STUDENTS_SHEET_ID, range=STUDENTS_RANGE).execute()
        values = result.get('values', [])
        if not values: return pd.DataFrame()
        df = pd.DataFrame(values[1:], columns=values[0])
        return df
    except: return pd.DataFrame()

@st.cache_data(ttl=60)
def load_memos():
    try:
        result = sheets_service.spreadsheets().values().get(spreadsheetId=MEMOS_SHEET_ID, range=MEMOS_RANGE).execute()
        values = result.get('values', [])
        if not values: return pd.DataFrame()
        df = pd.DataFrame(values[1:], columns=values[0])
        return df
    except: return pd.DataFrame()

@st.cache_data(ttl=60)
def load_prof_memos():
    try:
        result = sheets_service.spreadsheets().values().get(spreadsheetId=PROF_MEMOS_SHEET_ID, range=PROF_MEMOS_RANGE).execute()
        values = result.get('values', [])
        if not values: return pd.DataFrame()
        df = pd.DataFrame(values[1:], columns=values[0])
        return df
    except: return pd.DataFrame()

@st.cache_data(ttl=60)
def load_requests():
    try:
        result = sheets_service.spreadsheets().values().get(spreadsheetId=REQUESTS_SHEET_ID, range=REQUESTS_RANGE).execute()
        values = result.get('values', [])
        if not values: return pd.DataFrame()
        df = pd.DataFrame(values[1:], columns=values[0])
        return df
    except: return pd.DataFrame()

def clear_cache():
    st.cache_data.clear()

# ---------------- ربط ذكي مع تقرير تفصيلي ----------------
def sync_student_registration_numbers():
    try:
        st.info("⏳ جاري بدء الربط الذكي...")
        df_s = load_students()
        df_m = load_memos()
        
        updates = []
        # الأعمدة 19 و 20 هي S و T
        col_s_idx = 19
        col_t_idx = 20
        
        # تنظيف الأسماء في شيت الطلبة
        for col in ["لقب", "اللقب", "إسم", "إسم", "اسم"]:
            if col in df_s.columns: df_s[col] = df_s[col].astype(str).str.strip()
        
        # إنشاء عمود مؤقت للاسم الموحد
        lname_col = "لقب" if "لقب" in df_s.columns else ("اللقب" if "اللقب" in df_s.columns else None)
        fname_col = "إسم" if "إسم" in df_s.columns else ("إسم" if "إسم" in df_s.columns else None)
        
        if lname_col and fname_col:
            df_s["full_name_clean"] = df_s[lname_col] + " " + df_s[fname_col]
            df_s["full_name_clean"] = df_s["full_name_clean"].str.strip()
        else:
            return False, "❌ تعذر العثور على أعمدة الأسماء في شيت الطلبة"

        students_with_memo = df_s[df_s["رقم المذكرة"].notna() & (df_s["رقم المذكرة"] != "")]
        
        # القاموس: رقم المذكرة -> قائمة الطلاب
        memo_to_students = {}
        for _, s_row in students_with_memo.iterrows():
            m_id = str(s_row["رقم المذكرة"]).strip()
            reg_no = str(s_row.get("رقم التسجيل", "")).strip()
            full_name = s_row["full_name_clean"]
            if m_id not in memo_to_students: memo_to_students[m_id] = []
            memo_to_students[m_id].append({"reg": reg_no, "name": full_name})

        report_log = []

        for index, row in df_m.iterrows():
            memo_id = str(row.get("رقم المذكرة", "")).strip()
            if not memo_id or memo_id not in memo_to_students: continue
            
            s1_name = normalize_name(row.get("الطالب الأول", ""))
            s2_name = normalize_name(row.get("الطالب الثاني", ""))
            
            students_in_this_memo = memo_to_students[memo_id]
            reg_s1 = ""
            reg_s2 = ""
            
            # منطق الطالب الثاني
            if s2_name:
                found_s2 = next((s for s in students_in_this_memo if s["name"] == s2_name), None)
                if found_s2:
                    reg_s2 = found_s2["reg"]
                    students_in_this_memo.remove(found_s2)
                    report_log.append(f"✅ طالب 2 تم ربطه: {s2_name}")
                else:
                    report_log.append(f"⚠️ لم يتم العثور على الطالب 2 في شيت الطلبة: {s2_name}")
            
            # منطق الطالب الأول
            if students_in_this_memo:
                candidate_s1 = students_in_this_memo[0]
                if candidate_s1["name"] == s1_name or not s1_name:
                    reg_s1 = candidate_s1["reg"]
                    report_log.append(f"✅ طالب 1 تم ربطه: {candidate_s1['name']}")
                else:
                    report_log.append(f"⚠️ تعارض في اسم الطالب 1.")
            else:
                 report_log.append(f"⚠️ لم يتم العثور على طالب لهذه المذكرة.")

            row_idx = index + 2 
            if reg_s1:
                updates.append({"range": f"Feuille 1!S{row_idx}", "values": [[reg_s1]]})
            if reg_s2:
                updates.append({"range": f"Feuille 1!T{row_idx}", "values": [[reg_s2]]})
        
        if updates:
            body = {"valueInputOption": "USER_ENTERED", "data": updates}
            sheets_service.spreadsheets().values().batchUpdate(spreadsheetId=MEMOS_SHEET_ID, body=body).execute()
            return True, f"✅ تم تحديث {len(updates)} خلية.\nتقرير العملية:\n" + "\n".join(report_log)
        else:
            return False, "ℹ️ جميع البيانات محدثة أو لا توجد تطابقات.\n" + "\n".join(report_log)
            
    except Exception as e:
        return False, f"❌ حدث خطأ: {str(e)}"

# ---------------- نظام الطلبات ----------------
def save_and_send_request(req_type, prof_name, memo_id, memo_title, details_text):
    try:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        new_row = ["", timestamp, req_type, "قيد المراجعة", prof_name, memo_id, "", "", details_text, "", ""]
        body_append = {"values": [new_row]}
        sheets_service.spreadsheets().values().append(
            spreadsheetId=REQUESTS_SHEET_ID, range="Feuille 1!A2",
            valueInputOption="USER_ENTERED", body=body_append, insertDataOption="INSERT_ROWS"
        ).execute()
        
        # إرسال إيميل مبسط
        subject = f"طلب {req_type} - {memo_id}"
        msg = MIMEMultipart('alternative')
        msg['From'], msg['To'], msg['Subject'] = EMAIL_SENDER, ADMIN_EMAIL, subject
        msg.attach(MIMEText(f"{details_text}", 'plain', 'utf-8'))
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls(); server.login(EMAIL_SENDER, EMAIL_PASSWORD); server.send_message(msg)
        return True, "✅ تم الإرسال"
    except Exception as e:
        return False, f"❌ خطأ: {str(e)}"

# ---------------- منطق التسجيل ----------------
def update_registration(note_number, student1, student2=None):
    try:
        df_memos = load_memos(); df_prof_memos = load_prof_memos(); df_students = load_students()
        prof_name = df_memos[df_memos["رقم المذكرة"].astype(str).str.strip() == str(note_number).strip()]["الأستاذ"].iloc[0].strip()
        used_prof_password = st.session_state.prof_password.strip()
        
        # تحديث شيت الأساتذة
        prof_row_idx = df_prof_memos[
            (df_prof_memos["الأستاذ"].astype(str).str.strip() == prof_name) &
            (df_prof_memos["كلمة سر التسجيل"].astype(str).str.strip() == used_prof_password)
        ].index[0] + 2
        col_names = df_prof_memos.columns.tolist()
        
        s1_lname = student1.get('لقب', student1.get('اللقب', ''))
        s1_fname = student1.get('إسم', student1.get('إسم', ''))
        
        updates = [
            {"range": f"Feuille 1!{col_letter(col_names.index('الطالب الأول')+1)}{prof_row_idx}", "values": [[s1_lname + ' ' + s1_fname]]},
            {"range": f"Feuille 1!{col_letter(col_names.index('تم التسجيل')+1)}{prof_row_idx}", "values": [["نعم"]]},
            {"range": f"Feuille 1!{col_letter(col_names.index('تاريخ التسجيل')+1)}{prof_row_idx}", "values": [[datetime.now().strftime('%Y-%m-%d %H:%M')]]},
            {"range": f"Feuille 1!{col_letter(col_names.index('رقم المذكرة')+1)}{prof_row_idx}", "values": [[note_number]]}
        ]
        if student2 is not None:
            s2_lname = student2.get('لقب', student2.get('اللقب', ''))
            s2_fname = student2.get('إسم', student2.get('إسم', ''))
            updates.append({"range": f"Feuille 1!{col_letter(col_names.index('الطالب الثاني')+1)}{prof_row_idx}", "values": [[s2_lname + ' ' + s2_fname]]})
        
        sheets_service.spreadsheets().values().batchUpdate(spreadsheetId=PROF_MEMOS_SHEET_ID, body={"valueInputOption": "USER_ENTERED", "data": updates}).execute()

        # تحديث شيت المذكرات
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
            
        sheets_service.spreadsheets().values().batchUpdate(spreadsheetId=MEMOS_SHEET_ID, body={"valueInputOption": "USER_ENTERED", "data": updates2}).execute()

        # تحديث شيت الطلبة
        students_cols = df_students.columns.tolist()
        s1_idx = df_students[df_students["اسم المستخدم"].astype(str).str.strip() == student1['اسم المستخدم'].strip()].index[0] + 2
        sheets_service.spreadsheets().values().update(spreadsheetId=STUDENTS_SHEET_ID, range=f"Feuille 1!{col_letter(students_cols.index('رقم المذكرة')+1)}{s1_idx}", valueInputOption="USER_ENTERED", body={"values": [[note_number]]}).execute()
        
        if student2 is not None:
            s2_idx = df_students[df_students["اسم المستخدم"].astype(str).str.strip() == student2['اسم المستخدم'].strip()].index[0] + 2
            sheets_service.spreadsheets().values().update(spreadsheetId=STUDENTS_SHEET_ID, range=f"Feuille 1!{col_letter(students_cols.index('رقم الم2026')}{s2_idx}", valueInputOption="USER_ENDERED", body={"values": [[note_number]]}).execute()

        clear_cache()
        return True, "✅ تم التسجيل"
    except Exception as e:
        return False, f"❌ {str(e)}"

# ---------------- التحقق ----------------
def verify_student(username, password, df_students):
    student = df_students[df_students["اسم المستخدم"].astype(str).str.strip() == username]
    if student.empty: return False, "❌ غير موجود"
    if student.iloc[0]["كلمة السر"].strip() != password: return False, "❌ كلمة سر خطأ"
    return True, student.iloc[0]

def verify_professor(username, password, df_prof_memos):
    prof = df_prof_memos[
        (df_prof_memos["إسم المستخدم"].astype(str).str.strip() == username) &
        (df_prof_memos["كلمة المرور"].astype(str).str.strip() == password)
    ]
    if prof.empty: return False, "❌ بيانات خاطئة"
    return True, prof.iloc[0]

def verify_admin(username, password):
    if username in ADMIN_CREDENTIALS and ADMIN_CREDENTIALS[username] == password: return True, username
    return False, False

# ================= MAIN APP LOGIC =================
# تعريف متغيرات Session State قبل الاستخدام لتجنب المشاكل
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
    
    # تعريف المتغيرات الجديدة المهمة
    if 'selected_memo' not in st.session_state:
        st.session_state.selected_memo = None
    if 'admin_edit_req' not in st.system_state:
        st.session_state.admin_edit_req = None

df_students = load_students(); df_memos = load_memos(); df_prof_memos = load_prof_memos(); df_requests = load_requests()

if df_students.empty or df_memos.empty or df_prof_memos.empty:
    st.error("❌ خطأ في تحميل البيانات."); st.stop()

# الصفحة الرئيسية
if st.session_state.user_type is None:
    st.markdown("<h1 style='text-align: center; margin-bottom: 1rem;'>نظام تسجيل المذكرات</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #94A3B8; font-size: 1.2rem; margin-bottom: 2rem;'>جامعة محمد البشير الإبراهيمي - كلية الحقوق</p>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("<div class='card' style='text-align: center;'><h3>👨‍🎓 فضاء الطلبة</h3></div>", unsafe_allow_html=True)
        if st.button("دخول الطلبة"): st.session_state.user_type = "student"; st.rerun()
    with c2:
        st.markdown("<div class='card' style='text-align: center;'><h3>👨‍🏫 فضاء الأساتذة</h3></div>", unsafe_allow_html=True)
        if st.button("دخول الأساتذة"): st.session_state.user_type = "professor"; st.rerun()
    with c3:
        st.markdown("<div class='card' style='text-align: center;'><h3>⚙️ فضاء الإدارة</h3></div>", unsafe_allow_html=True)
        if st.button("دخول الإدارة"): st.session_state.user_type = "admin"; st.rerun()

# فضاء الطلبة
elif st.session_state.user_type == "student":
    if not st.session_state.logged_in:
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
                    if not username1 or not password1: st.error("⚠️ يرجى إدخال اسم المستخدم وكلمة السر")
                else:
                    v, r = verify_student(username1, password1, df_students)
                    if v: st.session_state.student1 = r; st.session_state.logged_in = True; st.rerun()
                    else: st.error(r)
                    
                if st.session_state.memo_type == "ثنائية":
                    if not username1 or not password1 or not username2 or not password2: st.error("⚠️ يرجى إدخال بيانات الطالبين كاملة")
                    elif username1.strip().lower() == username2.strip().lower(): st.error("❌ لا يمكن أن يكون الطالب الأول والثاني نفس الشخص!")
                    else:
                        v1, r1 = verify_student(username1, password1, df_students)
                        if not v1: st.error(r1); st.stop()
                        v2, r2 = verify_student(username2, password2, df_students)
                        if not v2: st.error(r2); st.stop()
                        
                        st.session_state.student1 = r1; st.session_state.student2 = r2
                        st.session_state.logged_in = True
                        # (منطق التسجيل الثنائي مختصر للتبسيط هنا)
                        s1_note = str(r1.get('رقم المذكرة', '')).strip()
                        s2_note = str(r2.get('رقم المذكرة', '')).strip()
                        s1_spec = str(r1.get('التخصص', '')).strip()
                        s2_spec = str(r2.get('التخصص', '')).strip()
                        
                        if s1_spec != s2_spec: st.error("❌ لا يمكن التسجيل الثنائي.")
                        elif (s1_note and not s2_note) or (not s1_note and s2_note): st.error("❌ أحد الطالبين مسجل مسبقاً")
                        elif s1_note and s2_note and s1_note != s2_note: st.error(f"❌ الطلاب مسجلان في مذكرتين مختلفتين")
                        elif s1_note and s2_note and s1_note == s2_note: 
                            st.session_state.mode = "view"; st.rerun()
                        
                        if not s1_note:
                            st.session_state.mode = "register"; st.rerun()
                        else: # فردية
                            fardiya_val = str(r1.get('فردية', '')).strip()
                            if fardiya_val not in ["1", "نعم"]: st.error("❌ لا يمكنك تسجيل مذكرة فردية"); st.stop()
                            st.session_state.mode = "register" # لم يكن لديه مذكرة
                            st.rerun()
    else:
        s1 = st.session_state.student1; s2 = st.session_state.student2
        
        col1, col2 = st.columns([4, 1])
        with col2:
            if st.button("خروج", key="logout_btn"):
                logout()
        
        st.markdown(f'<div class="card"><h3>ملف الطالب</h3><p>الطالب الأول: <b style="color:#2F6F7E;">{s1["لقب"] if "لقب" in s1 else s1["اللقب"]} {s1["إسم"] if "الإسم" in s1 else s1["إسم"]}</b></p><p>التخصص: <b>{s1["التخصص"]}</b></p></div>', unsafe_allow_html=True)
        if s2 is not None: st.markdown(f'<div class="card"><p>الطالب الثاني: <b style="color:#2F6F7E;">{s2["لقب"] if "لقب" in s2 else s2["لقب"]} {s2["إسم"] if "إسم" in s2 else s2["إسم"]}</b></p></div>', unsafe_allow_html=True)

        # تبويبات الطالب
        tab_memo, tab_notify = st.tabs(["مذكرتي", "الإشعارات والطلبات"])
        
        with tab_memo:
            if st.session_state.mode == "view":
                note_num = str(s1.get('رقم المذكرة', '')).strip()
                if note_num:
                    info = df_memos[df_memos["رقم المذكرة"] == note_num].iloc[0]
                    st.markdown(f'''
                    <div class="card" style="border-left: 5px solid #FFD700;">
                        <h3>✅ أنت مسجل في المذكرة التالية:</h3>
                        <p><b>رقم المذkinsa:</b> {info['رقم المذكرة']}</p>
                        <p><b>العنوان:</b> {info['عنوان المذكرة']}</p>
                        <p><b>المشرف:</b> {info['الأستاذ']}</p>
                        <p><b>التخصص:</b> {info['التخصص']}</p>
                    </div>''', unsafe_allow_html=True)
                else:
                    st.info("لم تسجل مذكرة")

            elif st.session_state.mode == "register":
                st.markdown('<div class="card"><h3>تسجيل مذكرة جديدة</h3></div>', unsafe_allow_html=True)
                all_profs = sorted(df_memos["الأستاذ"].dropna().unique())
                selected_prof = st.selectbox("اختر الأستاذ المشرف:", [""] + all_profs)
                
                if selected_prof:
                    student_specialty = s1["التخصص"]
                    prof_memos = df_memos[df_memos["الأستاذ"].astype(str).str.strip() == selected_prof.strip()]
                    reg_count = len(prof_memos[prof_memos["تم التسجيل"].astype(str).str.strip() == "نعم"])
                    
                    if reg_count >= 4:
                        st.error(f'❌ الأستاذ {selected_prof} استنفذ كل العناوين')
                    else:
                        avail_memos = df_memos[
                            (df_memos["الأستاذ"].astype(str).str.strip() == selected_prof.strip()) &
                            (df_memos["التخصص"].astype(str).str.strip() == student_specialty.strip()) &
                            (df_memos["تم التسجيل"].astype(str).str.strip() != "نعم")
                        ][["رقم المذكرة", "عنوان المذكرة"]]
                        
                        if not avail_memos.empty:
                            st.success(f'✅ المذكرات المتاحة في تخصصك ({student_specialty}):')
                            for _, row in avail_memos.iterrows():
                                st.markdown(f"**{row['رقم المذكرة']}.** {row['عنوان المذكرة']}")
                        else:
                            st.error('لا توجد مذكرات متاحة ❌')
                
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
                            # منطق التحقق المبسط للمختصر الرسالة
                            v, _, _ = verify_professor_password(st.session_state.note_number, st.session_state.prof_password, df_memos, df_prof_memos)
                            if v:
                                # (تبسيط للعرض فقط - في كود التحديث السابق كان منطق معقدً)
                                with st.spinner('⏳ جاري تسجيل...'):
                                    success, msg = update_registration(st.session_state.note_number, s1, s2)
                                if success: 
                                    st.success(msg); st.balloons(); clear_cache_and_reload()
                                    st.session_state.mode = "view"; st.session_state.show_confirmation = False; time.sleep(2); st.rerun()
                                else: st.error(msg); st.session_state.show_confirmation = False
                    with col2:
                        if st.button("إلغاء"): st.session_state.show_confirmation = False; st.rerun()

        with tab_notify:
            st.subheader("تنبيهات خاصة بك")
            my_memo_id = str(s1.get('رقم المذكرة', '')).strip()
            if my_memo_id:
                my_reqs = df_requests[df_requests["رقم المذكرة"].astype(str).str.strip() == my_memo_id]
                if not my_reqs.empty:
                    for _, r in my_reqs.iterrows():
                        req_type = r['نوع الطلب']
                        details = str(r.get('العنوان الجديد', r.get('المبررات', '')).strip())
                        
                        # القواعد: إخفاء المبررات في حذف طالب والتنازل
                        show_details = True
                        if req_type in ["حذف طالب", "تنازل"]:
                            show_details = False

                        st.markdown(f"""
                        <div class='card' style='border-right: 4px solid #F59E0B; padding: 20px;'>
                            <h4>{req_type}</h4>
                            <p>التاريخ: {r['الوقت']}</p>
                            <p>الحالة: <b>{r['الحالة']}</b></p>
                            {'<p>التفاصيل: ' + details + '</p>' if show_details else '<p><i>التفاصيل مخفية</i></p>'}
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("لا توجد إشعارات جديدة.")
            else:
                st.info("يجب تسجيل مذكرة أولاً لتلقي التنبيهات.")

# فضاء الأساتذة
elif st.session_state.user_type == "professor":
    if not st.session_state.logged_in:
        st.markdown("<h2>فضاء الأساتذة</h2>", unsafe_allow_html=True)
        with st.form("prof_login_form"):
            c1, c2 = st.columns(2)
            with c1: u = st.text_input("اسم المستخدم")
            with c2: p = st.text_input("كلمة المرور", type="password")
            if st.form_submit_button("تسجيل الدخول"):
                v, r = verify_professor(u, p, df_prof_memos)
                if not v: st.error(r)
                else: st.session_state.professor = r; st.session_state.logged_in = True; st.rerun()
    else:
        prof = st.session_state.professor
        prof_name = prof["الأستاذ"]
        
        col1, col2 = st.columns([4, 1])
        with col2:
            if st.button("خروج"):
                logout()
        
        st.markdown(f"<h2 style='margin-bottom:20px;'>فضاء الأستاذ <span style='color:#FFD700;'>{prof_name}</span></h2>", unsafe_allow_html=True)

        prof_memos = df_memos[df_memos["الأستاذ"].astype(str).str.strip() == prof_name.strip()]
        total = len(prof_memos)
        registered = len(prof_memos[prof_memos["تم التسجيل"].astype(str).str.strip() == "نعم"])
        available = total - registered
        is_exhausted = registered >= 4

        st.markdown('<div class="kpi-grid">', unsafe_allow_html=True)
        st.markdown(f'''
            <div class="kpi-card"><div class="kpi-value">{total}</div><div class="kpi-label">إجمالي المذكرات</div></div>
            <div class="kpi-card" style="border-color: #10B981;"><div class="kpi-value" style="color: #10B981;">{registered}</div><div class="kpi-label">المذكرات المسجلة</div></div>
            <div class="kpi-card" style="border-color: #F59E0B;"><div class="kpi-value" style="color: #F59E0B;">{available}</div><div class="kpi-label">المذكرات المتاحة</div></div>
        ''', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        if is_exhausted:
            st.markdown('<div class="alert-card">لقد استنفذت العناوين الأربعة المخصصة لك.</div>', unsafe_allow_html=True)
        
        tab1, tab2, tab3, tab4 = st.tabs(["المذكرات المسجلة", "كلمات السر", "الإشعارات", "المتاحة"])
        
        with tab1:
            st.subheader("المذكرات المسجلة")
            # استخدام .get() بدلاً من الوصول المباشر لتجنب الخطأ
            if st.session_state.get('selected_memo'):
                # صفحة التفاصيل (Modal)
                sel_mid = st.session_state.selected_memo
                sel_memo = prof_memos[prof_memos["رقم المذكرة"] == sel_mid].iloc[0]
                
                st.empty() # إخفاء القائمة
                
                col1, col2, col3 = st.columns([1, 6, 1])
                with col1: 
                    if st.button("⬅ عودة للقائمة"):
                        del st.session_state.selected_memo
                        st.rerun()
                
                st.markdown(f"<div class='card' style='border: 2px solid #2F6F7E;'><h2>🔧 تفاصيل المذكرة: {sel_mid}</h2></div>", unsafe_allow_html=True)
                
                s1_name = sel_memo['الطالب الأول']
                s2_name = sel_memo.get('الطالب الثاني', '')
                
                s1_email = get_student_email(sel_memo.get('رقم تسجيل الطالب 1', ''), s1_name, df_students)
                s2_email = get_student_email(sel_memo.get('رقم تسجيل الطالب 2', ''), s2_name, df_students) if s2_name else ""
                
                st.markdown(f"""
                <div style='background:#1E293B; padding:15px; border-radius:10px; margin-bottom:15px;'>
                    <h4>الطالب الأول: {s1_name}</h4>
                    {f"<p style='color:#10B981;'>📧 {s1_email if s1_email else 'لا يوجد'}</p>" if s1_email else "<p style='color:#EF4444;'>لا يوجد إيميل</p>"}
                </div>
                """, unsafe_allow_html=True)
                if s2_name:
                    st.markdown(f"""
                    <div style='background:#1E293B; padding:15px; border-radius:10px; بعرض: 20px; margin-bottom:15px;'>
                        <h4>الطالب الثاني: {s2_name}</h4>
                        {f"<p style='color:#10B981;'>📧 {s2_email if s2_email else 'لا يوجد'}</p>" if s2_email else "<p style='color:#EF4444;'>لا يوجد إيميل</p>"}
                    </div>
                    """, unsafe_allow_html=True)

                # شريط التقدم
                prog_val = int(sel_memo.get('نسبة التقدم', 0)) if str(sel_memo.get('نسبة التقدم', 0)).isdigit() else 0
                st.markdown(f"<div class='progress-container'><div class='progress-bar' style='width:{prog_int}%;'></div></div>", unsafe_allow_html=True)
                
                new_prog = st.selectbox("تحديث نسبة التقدم:", [
                    "0%", "30%", "60%", "100%"], key=f"np_{sel_mid}")
                if st.button("حفظ التقدم", key=f"sv_{sel_mid}"):
                    mapping = {"0%":0, "30%":30, "60%":60, "100%":100}
                    s, m = update_progress(sel_mid, mapping[new_prog])
                    st.success(m) if s else st.error(m); time.sleep(1); st.rerun()

                st.markdown("---")
                st.markdown("### 📨 تقديم طلب جديد")
                rtype = st.selectbox("نوع الطلب:", ["", "تغيير عنوان المذكرة", "حذف طالب (ثنائية)", "إضافة طالب (فردية)", "تنازل"], key=f"rt_{sel_mid}")
                details = ""
                if rtype == "تغيير عنوان المذكرة":
                    details = st.text_input("العنوان الجديد:", key=f"nt_{sel_mid}")
                    if st.button("إرسال طلب تغيير العنوان", key=f"send_{sel_mid}"):
                        if details: res, msg = save_and_send_request(prof_name, sel_mid, sel_memo['عنوان المذكرة'], rtype, details)
                        st.success(msg) if res else st.error(msg)
                elif rtype == "تنازل":
                    details = st.text_area("مبررات التنازل:", key=f"res_{sel_mid}")
                    if st.button("إرسال طلب التنازل", key=f"send_res_{sel_mid}"):
                        if details: res, msg = save_and_send_request(prof_name, sel_mid, sel_memo['عنوان المذكرة'], rtype, details)
                        st.success(msg) if res else st.error(msg)
                elif rtype in ["حذف طالب (ثنائية)", "إضافة طالب (فردية)"]:
                    is_binary = (rtype == "حذف طالب (ثنائية)")
                    
                    if is_binary:
                        if not s2_name: st.warning("هذه مذكرة فردية!")
                    else:
                        st.write("الطالبان:")
                        st.write(f"1. {s1_name}")
                        st.write(f"2. {s2_name}")
                        to_del = st.selectbox("اختر الطالب للحذف:", ["", "الطالب الأول", "الطالب الثاني"], key=f"del_{sel_mid}")
                        just = st.text_area("تبريرات الحذف:", key=f"jus_del_{sel_mid}")
                        if to_del and just: details = f"حذف {to_del}: {just}"
                        else: validation_error = "اكمل البيانات"
                elif rtype == "إضافة طالب (فردية)":
                    if s2_name: st.warning("هذه مذكرة ثنائية بالفعل!")
                    else:
                        r_add = st.text_input("رقم التسجيل:", key=f"add_{sel_mid}")
                        if st.button("تحقق وإرسال", key=f"btn_add_{sel_mid}"):
                            target = df_students[df_students["رقم التسجيل"] == r_add]
                            if target.empty: validation_error = "رقم التسجيل غير موجود"
                            elif target.iloc[0].get("رقم المذكرة"): validation_error = "الطالب لديه مذكرة بالفعل"
                            elif target.iloc[0].get("التخصص") != sel_memo['التخصص']: validation_error = "التخصص غير متطابق"
                            else:
                                just = st.text_area("ملاحظات:", key=f"jus_add_{sel_mid}")
                                details = f"إضافة الطالب المسجل: {r_add}. ملاحظات: {just}"
                if validation_error:
                    st.error(validation_error)
                elif details:
                    res, msg = save_and_send_request(prof_name, sel_mid, sel_memo['عنوان المذكرة'], rtype, details)
                    st.success(msg) if res else st.error(msg)
            
            # تنفيذ الطلب
            if details:
                res, msg = save_and_send_request(prof_name, sel_mid, sel_memo['عنوان المذكرة'], rtype, details)
                if res: st.success(msg); time.sleep(1); st.rerun()
                else: st.error(msg)
            
            if st.button("❌ إغلاق"):
                del st.session_state.selected_memo
                st.rerun()

            else:
                # القائمة (List View)
                memos = prof_memos[prof_memos["تم التسجيل"] == "نعم"]
                if not memos.empty:
                    cols = st.columns(2)
                    for i, (_, m) in enumerate(memos.iterrows()):
                        with cols[i % 2]:
                            st.markdown(f"""
                            <div class="card" style="cursor:pointer; border-top: 5px solid #10B981;">
                                <h4>{m['رقم المذكرة']} - {m['عنوان المذكرة']}</h4>
                                <p style="font-size:0.8em; color:#2F6F7E;">انقر على الزر بالأسفل للتفاصيل</p>
                            </div>
                            """, unsafe_allow_html=True)
                            if st.button("⚙️ إدارة وتفاصيل", key=f"mgr_{m['رقم المذكرة']}"):
                                st.session_state.selected_memo = m['رقم المذكرة']
                                st.rerun()
                else:
                    st.info("لا توجد مذكرات مسجلة حتى الآن.")

        with tab2: # كلمات السر
            pwds = df_prof_memos[df_prof_memos["الأستاذ"].astype(str).str.strip() == prof_name.strip()]
            if not pwds.empty:
                for _, row in pwds.iterrows():
                    stat = str(row.get("تم التسجيل", "")).strip()
                    pwd = str(row.get("كلمة سر التسجيل", "")).strip()
                    if pwd:
                        color = "#10B981" if stat == "نعم" else "#F59E0B"
                        status_txt = "مستخدمة" if stat == "نعم" else "متاحة"
                        st.markdown(f"""
                        <div class="card" style="border-right: 5px solid {color}; display:flex; justify-content:space-between; align-items:center;">
                            <div>
                                <h3 style="margin:0; font-family:monospace; font-size:1.8rem; color:#FFD700;">{pwd}</h3>
                                <p style="margin:5px 0 0 0 0 0; color:#94A3B8;">الحالة: {status_txt}</p>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
            else: st.info("لا توجد كلمات سر مسندة إليك.")

        with tab3: # إشعارات الأساتذة
            my_reqs = df_requests[df_requests["الأستاذ"] == prof_name]
            if not my_reqs.empty:
                for _, r in my_reqs.iterrows():
                    c = "#10B981" if r['الحالة'] == "مقبول" else "#F59E0B"
                    st.markdown(f"""
                    <div class="card" style="border-right: 4px solid {c};">
                        <h4>{r['نوع الطلب']} - {r['رقم المذكرة']}</h4>
                        <p>التاريخ: {r['الوقت']}</p>
                        <p>الحالة: <b>{r['الحالة']}</b></p>
                    </div>
                    """, unsafe_allow_html=True)
            else: st.info("لا توجد إشعارات")

        with tab4: # المتاحة
            if is_exhausted: st.subheader("💡 المذكرات المقترحة")
            else: st.subheader("⏳ المذكرات المتاحة للتسجيل")
            avail = prof_memos[prof_memos["تم التسجيل"].astype(str).str.strip() != "نعم"]
            if not avail.empty:
                for _, m in avail.iterrows():
                    st.markdown(f"""
                    <div class="card" style="border-left: 4px solid #64748B;">
                        <h4>{m['رقم المذكرة']}</h4>
                        <p>{m['عنوان المذكرة']}</p>
                        <p style="color:#94A3B8;">تخصص: {m['التخصص']}</p>
                    </div>
                    """, unsafe_allow_html=True)
            else: st.success("✅ جميع المذكرات مسجلة أو مقترحة!")

# فضاء الإدارة
elif st.session_state.user_type == "admin":
    if not st.session_state.logged_in:
        st.markdown("<h2>⚙️ فضاء الإدارة</h2>", unsafe_allow_html=True)
        with st.form("admin_login"):
            u = st.text_input("User")
            p = st.text_input("Pass", type="password")
            if st.form_submit_button("دخول"):
                v, r = verify_admin(u, p)
                if not v: st.error(r)
                else: st.session_state.admin_user = r; st.session_state.logged_in = True; st.rerun()
    else:
        col1, col2 = st.columns([4, 1])
        with col2:
            if st.button("خروج"):
                logout()
        
        st.header("📊 لوحة تحكم الإدارة")
        
        # --- Stats ---
        st_s = len(df_students); t_m = len(df_memos); r_m = len(df_memos[df_memos["تم التسجيل"].astype(str).str.strip() == "نعم"])
        a_m = t_m - r_m; t_p = len(df_prof_memos["الأستاذ"].unique())
        reg_st = df_students["رقم المذكرة"].notna().sum()
        unreg_st = st_s - reg_st
        
        st.markdown('<div class="kpi-grid">', unsafe_allow_html=True)
        st.markdown(f'''
            <div class="kpi-card"><div class="kpi-value">{st_s}</div><div class="kpi-label">الطلاب</div></div>
            <div class="kpi-card"><div class="kpi-value">{t_p}</div><div class="kpi-label">الأساتذة</div></div>
            <div class="kpi-card"><div class="kpi-value">{t_m}</div><div class="kpi-label">إجمالي المذكرات</div></div>
            <div class="kpi-card" style="border-color: #10B981;"><div class="kpi-value" style="color: #10B981;">{r_m}</div><div class="kpi-label">مذكرات مسجلة</div></div>
            <div class="kpi-card" style="border-color: #F59E0B;"><div class="kpi-value" style="color: #F59E0B;">{a_m}</div><div class="kpi-label">مذكرات متاحة</div></div>
        ''', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        tab1, tab2, tab3, tab4, tab5 = st.tabs(["بيانات", "إدارة الطلبات", "الصيانة", "خروج"])
        
        with tab1:
            st.subheader("جدول المذكرات")
            st.dataframe(df_memos, use_container_width=True, height=400)

        with tab2:
            # إدارة الطلبات (نظام الصفحات: List -> Modal)
            
            if not st.session_state.get('admin_edit_req'):
                # عرض الجدول
                st.subheader("سجل الطلبات الواردة")
                for index, row in df_requests.iterrows():
                    c = "#10B981" if row['الحالة'] == "مقبول" else "#F59E0B"
                    # عرض مختصر + زر تعديل
                    col1, col2, col3 = st.columns([4, 1, 1])
                    with col1:
                        st.markdown(f"<div style='background:#1E293B; padding:10px; border-radius:5px; margin-bottom:5px; border-right:3px solid {c};'><b>{row['نوع الطلب']}</b> - {row['رقم المذكرة']} <br> {row['الحالة']}</div>", unsafe_allow_html=True)
                    with col3:
                        if st.button("⚙️ قرار", key=f"edit_{index}"):
                            st.session_state.admin_edit_req = index
                            st.rerun()
            else:
                # صفحة التعديل (Modal)
                idx = st.session_state.admin_edit_req
                req_row = df_requests.iloc[idx]
                
                st.empty() # إخفاء الجدول
                st.markdown("<div class='card'><h2>⚖️ اتخاذ قرار للطلب</h2></div>", unsafe_allow_html=True)
                
                # واجهة التعديل
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**نوع الطلب:** {req_row['نوع الطلب']}")
                    st.write(f"**الأستاذ:** {req_row['الأستاذ']}")
                    st.write(f"**رقم المذكرة:** {req_row['رقم المذكرة']}")
                    st.info(f"**تفاصيل الطلب:** {req_row['عنوان الجديد']}")
                
                with col2:
                    new_status = st.selectbox("قرار الإدارة:", ["قيد المراجعة", "مقبول", "مرفوض"])
                    admin_notes = st.text_area("ملاحظات الإدارة:", value=req_row.get('ملاحظات الإدارة', ''))
                
                col_b1, col_b2 = st.columns(2)
                with col_b1:
                    if st.button("💾 حفظ القرار", type="primary"):
                        # تحديث الشيت (مباشرة لتفادي الحالة)
                        sheet_idx = idx + 2 # A=0... J=9. D=الحالة (رقم 3), J=ملاحظات (رقم 9)
                        
                        body = {
                            "valueInputOption": "USER_ENTERED",
                            "data": [
                                {"range": f"Feuille 1!D{sheet_idx}", "values": [[new_status]]},
                                {"range": f"Feuille 1!J{sheet_idx}", "values": [[admin_notes]]}
                            ]
                        }
                        sheets_service.spreadsheets().values().batchUpdate(spreadsheetId=REQUESTS_SHEET_ID, body=body).execute()
                        st.success("تم حفظ القرار")
                        clear_cache()
                        del st.session_state.admin_edit_req
                        st.rerun()
                
                with col_b2:
                    if st.button("إلغاء"):
                        del st.session_state.admin_edit_req
                        st.rerun()

        with tab3:
            st.subheader("الصيانة والربط الذكي")
            st.warning("⚠️ استخدم هذا الزر لربط أرقام التسجيل (أعمدة S و T) لأول مرة.")
            if st.button("🔄 تشغيل عملية الربط (مع تقرير)", type="primary"):
                with st.spinner("جاري المعالجة..."):
                    s, m = sync_student_registration_numbers()
                    st.success(m) if s else st.info(m)
                    if s: clear_cache(); st.rerun()

        with tab5:
            if st.button("تسجيل خروج"):
                logout()

st.markdown("---")
st.markdown('<div style="text-align:center; color:#64748B; font-size:12px; padding:20px;">© 2026 جامعة محمد البشير الإبراهيمي</div>', unsafe_allow_html=True)
