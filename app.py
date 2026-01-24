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
.block-container { padding: 2rem; background-color: #1A2A3D; border-radius: 16px; margin:auto; }
h1, h2, h3, h4 { font-weight: 700; margin-bottom: 1rem; color: #F8FAFC; }
label, p, span { color: #E2E8F0; }
.stTextInput label, .stSelectbox label { color: #F8FAFC !important; font-weight: 600; }

.stButton>button, button[kind="primary"], div[data-testid="stFormSubmitButton"] button {
    background-color: #2F6F7E !important; color: #ffffff !important; font-size: 16px;
    font-weight: 600; padding: 14px 32px; border: none !important; border-radius: 12px !important;
    cursor: pointer; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2); transition: all 0.3s ease;
    width: 100%; text-align: center; display: flex; justify-content: center; align-items: center; gap: 10px;
}
.stButton>button:hover { background-color: #285E6B !important; transform: translateY(-2px); }

.card { 
    background: rgba(30, 41, 59, 0.95); border: 1px solid rgba(255,255, 255, 0.08);
    border-radius: 20px; padding: 30px; margin-bottom: 20px; 
    box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.2); border-top: 3px solid #2F6F7E;
}
.kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 1.5rem; margin-bottom: 2.5rem; }
.kpi-card {
    background: linear-gradient(145deg, #1E293B, #0F172A); border: 1px solid rgba(255, 255, 255, 0.05); border-radius: 16px; padding: 2.5rem 1rem;
    text-align: center; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
}
.kpi-value { font-size: 2.5rem; font-weight: 900; color: #FFD700; margin: 15px 0; }
.kpi-label { font-size: 1.2rem; color: #94A3B8; font-weight: 600; text-transform: uppercase; }
.alert-card { background: linear-gradient(90deg, #8B4513 0%, #A0522D 100%); border: 1px solid #CD853F; color: white; padding: 25px; border-radius: 12px; text-align: center; }
.progress-container { background-color: #0F172A; border-radius: 99px; padding: 6px; margin: 20px 0; overflow: hidden; }
.progress-bar { height: 24px; border-radius: 99px; background: linear-gradient(90deg, #2F6F7E 0%, #285E6B 50%, #FFD700 100%); transition: width 1s cubic-bezier(0.4, 0, 0.2, 1); }
.stDataFrame { border-radius: 12px; overflow: hidden; border: 1px solid rgba(255,255,  white, 0.1); background: #1E293B; }
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

# ---------------- Helpers & Init ----------------
def col_letter(n):
    result = ""
    while n > 0:
        n, remainder = divmod(n - 1, 26)
        result = chr(65 + remainder) + result
    return result

def normalize_name(name):
    if pd.isna(name): return ""
    return " ".join(str(name).strip().split())

def get_student_email(reg_no, full_name, df_students):
    # البحث في عدة أعمدة محتملة
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
        clean_name = normalize_name(full_name)
        for col_l in ["لقب", "اللقب"]:
            for col_f in ["إسم", "إسم", "اسم"]:
                if col_l in df_students.columns and col_f in df_students.columns:
                    match = df_students[(df_students[col_l].astype(str).str.strip() == clean_name.split()[0]) & (df_students[col_f].astype(str).str.strip() == " ".join(clean_name.split()[1:]))]
                    if not match.empty:
                        for col in email_cols:
                            if col in match.columns:
                                email = match.iloc[0].get(col, "").strip()
                                if email and "@" in email: return email
    return ""

# ================= تحديد حالة Session State بأمان =================
# نقوم بتعريف المتغيرات هنا لتجنب الخطأ عند إعادة التشغيل
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
    
    # المتغيرات الجديدة للأمن
    if 'selected_memo' not in st.session_state:
        st.session_state.selected_memo = None
    if 'admin_edit_req' not in st.session_state:
        st.session_state.admin_edit_req = None

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

# ---------------- ربط ذكي مع تقرير تفصيلي (يحل مشكلة الربط) ----------------
def sync_student_registration_numbers():
    try:
        st.info("⏳ جاري بدء الربط الذكي...")
        df_s = load_students()
        df_m = load_memos()
        
        updates = []
        col_s_idx = 19 # S
        col_t_idx = 20 # T
        
        # تنظيف أسماء الطلبة في الشيت المصدر
        for col in ["لقب", "اللقب", "إسم", "إسم", "اسم"]:
            if col in df_s.columns: df_s[col] = df_s[col].astype(str).str.strip()
        
        # إنشاء عمود مؤقت للاسم الموحد
        lname_col = "لقب" if "لقب" in df_s.columns else ("اللقب" if "اللقب" in df_s.columns else None)
        fname_col = "إسم" if "إسم" in df_s.columns else ("إسم" if "إسم" in df_s.columns else None)
        
        if not lname_col or not fname_col:
            return False, "❌ تعذر العثور على أعمدة الاسماء في شيت الطلبة."

        df_s["full_name_clean"] = df_s[lname_col] + " " + df_s[fname_col]
        students_with_memo = df_s[df_s["رقم المذكرة"].notna() & (df_s["رقم المذكرة"] != "")]
        
        # القاموس: رقم المذكرة -> قائمة الطلاب
        memo_to_students = {}
        for _, s_row in students_with_memo.iterrows():
            m_id = str(s_row["رقم المذكرة"]).strip()
            reg_no = str(s_row.get("رقم التسجيل", "")).strip()
            full_name = s_row["full_name_clean"]
            if m_id not in memo_to_students: memo_to_students[m_id] = []
            memo_to_students[m_id].append({"reg": reg_no, "name": full_name})

        report_log = [] # تقرير للعرض

        for index, row in df_m.iterrows():
            memo_id = str(row.get("رقم المذكرة", "")).strip()
            if not memo_id or memo_id not in memo_to_students: continue
            
            # تنظيف أسماء المذكرات
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
                    report_log.append(f"✅ تم ربط الطالب الثاني (T): {s2_name}")
                else:
                    report_log.append(f"⚠️ لم يتم العثور على الطالب الثاني في شيت الطلبة: {s2_name}")
            
            # منطق الطالب الأول
            if students_in_this_memo:
                candidate_s1 = students_in_this_memo[0]
                if candidate_s1["name"] == s1_name or not s1_name:
                    reg_s1 = candidate_s1["reg"]
                    report_log.append(f"✅ تم ربط الطالب الأول (S): {candidate_s1['name']}")
                else:
                    report_log.append(f"⚠️ تضارض في اسم الطالب الأول.")
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
            return True, f"✅ تم تحديث {len(updates)} خلية.\n\nتفاصيل العملية:\n" + "\n".join(report_log)
        else:
            return False, "ℹ️ جميع البيانات محدثة أو لا توجد تطابقات.\n\n" + "\n".join(report_log)
            
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

        students_cols = df_students.columns.tolist()
        s1_idx = df_students[df_students["اسم المستخدم"].astype(str).str.strip() == student1['اسم المستخدم'].strip()].index[0] + 2
        sheets_service.spreadsheets().values().update(spreadsheetId=STUDENTS_SHEET_ID, range=f"Feuille 1!{col_letter(students_cols.index('رقم المذكرة')+1)}{s1_idx}", valueInputOption="USER_ENTERED", body={"values": [[note_number]]}).execute()
        
        if student2 is not None:
            s2_idx = df_students[df_students["اسم المستخدم"].astype(str).str.strip() == student2['اسم المستخدم'].strip()].index[0] + 2
            sheets_service.spreadsheets().values().update(spreadsheetId=STUDENTS_SHEET_ID, range=f"Feuille 1!{col_letter(students_cols.index('رقم المذكرة')+1)}{s2_idx}", valueInputOption="USER_ENTERED", body={"values": [[note_number]]}).execute()

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
df_students = load_students(); df_memos = load_memos(); df_prof_memos = load_prof_memos(); df_requests = load_requests()

if df_students.empty or df_memos.empty or df_prof_memos.empty:
    st.error("❌ خطأ في تحميل البيانات."); st.stop()

# الصفحة الرئيسية
if st.session_state.user_type is None:
    st.markdown("<h1 style='text-align: center;'>نظام تسجيل المذكرات</h1>", unsafe_allow_html=True)
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
        with st.form("login"):
            u = st.text_input("اسم المستخدم"); p = st.text_input("كلمة المرور", type="password")
            if st.form_submit_button("دخول"):
                v, r = verify_student(u, p, df_students)
                if v: st.session_state.student1 = r; st.session_state.logged_in = True; st.rerun()
                else: st.error(r)
    else:
        s1 = st.session_state.student1
        tab1, tab2 = st.tabs(["مذكرتي", "إشعاراتي"])
        with tab1:
            note_id = s1.get('رقم المذكرة', '').strip()
            if note_id:
                info = df_memos[df_memos["رقم المذكرة"] == note_id].iloc[0]
                st.markdown(f"<div class='card'><h3>{info['عنوان المذكرة']}</h3><p>المشرف: {info['الأستاذ']}</p></div>", unsafe_allow_html=True)
            else: st.info("لم تسجل مذكرة")
        with tab2:
            reqs = df_requests[df_requests["رقم المذكرة"].astype(str).str.strip() == note_id]
            if not reqs.empty:
                for _, r in reqs.iterrows():
                    hide = r['نوع الطلب'] in ["حذف طالب", "تنازل"]
                    det = r.get('العنوان الجديد', r.get('المبررات', ''))
                    st.markdown(f"<div class='card'><h4>{r['نوع الطلب']}</h4><p>{det if not hide else 'مخفي'}</p></div>", unsafe_allow_html=True)
            else: st.info("لا توجد إشعارات")

# فضاء الأساتذة (التصميم الجديد)
elif st.session_state.user_type == "professor":
    if not st.session_state.logged_in:
        with st.form("p_login"):
            u = st.text_input("اسم المستخدم"); p = st.text_input("كلمة المرور", type="password")
            if st.form_submit_button("دخول"):
                v, r = verify_professor(u, p, df_prof_memos)
                if v: st.session_state.professor = r; st.session_state.logged_in = True; st.rerun()
                else: st.error(r)
    else:
        prof = st.session_state.professor
        p_name = prof["الأستاذ"]
        
        t1, t2, t3, t4 = st.tabs(["المذكرات المسجلة", "كلمات السر", "الإشعارات", "المتاحة"])
        
        with t1:
            # التحقق الآمن باستخدام .get()
            if st.session_state.get('selected_memo'):
                # صفحة التفاصيل (Modal)
                sel_mid = st.session_state.selected_memo
                sel_memo = df_memos[(df_memos["الأستاذ"] == p_name) & (df_memos["رقم المذكرة"] == sel_mid)].iloc[0]
                
                st.empty() # إخفاء القائمة
                
                col1, col2, col3 = st.columns([1, 6, 1])
                with col1: 
                    if st.button("⬅ عودة"):
                        del st.session_state.selected_memo
                        st.rerun()
                
                st.markdown(f"<div class='card' style='border: 2px solid #2F6F7E;'><h2>🔧 تفاصيل المذكرة: {sel_mid}</h2></div>", unsafe_allow_html=True)
                
                s1_name = sel_memo['الطالب الأول']
                s2_name = sel_memo.get('الطالب الثاني', '')
                s1_email = get_student_email(sel_memo.get('رقم تسجيل الطالب 1', ''), s1_name, df_students)
                s2_email = get_student_email(sel_memo.get('رقم تسجيل الطالب 2', ''), s2_name, df_students) if s2_name else ""
                
                st.markdown(f"<div style='background:#1E293B; padding:15px; border-radius:10px; margin-bottom:15px;'><h4>الطالب الأول: {s1_name}</h4><p>📧 {s1_email if s1_email else 'لا يوجد'}</p></div>", unsafe_allow_html=True)
                if s2_name:
                    st.markdown(f"<div style='background:#1E293B; padding:15px; border-radius:10px; margin-bottom:15px;'><h4>الطالب الثاني: {s2_name}</h4><p>📧 {s2_email if s2_email else 'لا يوجد'}</p></div>", unsafe_allow_html=True)

                # التحكم
                prog_val = int(sel_memo.get('نسبة التقدم', 0)) if str(sel_memo.get('نسبة التقدم', 0)).isdigit() else 0
                st.markdown(f"<div class='progress-container'><div class='progress-bar' style='width:{prog_val}%;'></div></div>", unsafe_allow_html=True)
                
                new_prog = st.selectbox("تحديث التقدم:", ["0%", "30%", "60%", "100%"], key=f"np_{sel_mid}")
                if st.button("حفظ", key=f"sv_{sel_mid}"):
                    sheets_service.spreadsheets().values().update(spreadsheetId=MEMOS_SHEET_ID, range=f"Feuille 1!Q{df_memos[df_memos['رقم المذكرة']==sel_mid].index[0]+2}", valueInputOption="USER_ENTERED", body={"values": [[int(new_prog[:-1])]]}).execute()
                    st.success("تم"); clear_cache(); st.rerun()

                st.markdown("---")
                st.markdown("### 📨 تقديم طلب")
                rtype = st.selectbox("نوع الطلب:", ["", "تغيير عنوان", "حذف طالب", "إضافة طالب", "تنازل"], key=f"rt_{sel_mid}")
                details = ""
                if rtype == "تغيير عنوان": details = st.text_input("العنوان الجديد:", key=f"ch_{sel_mid}")
                elif rtype == "تنازل": details = st.text_area("المبررات:", key=f"re_{sel_mid}")
                elif rtype == "حذف طالب":
                    to_del = st.selectbox("اختر:", ["", s1_name, s2_name], key=f"del_{sel_mid}")
                    details = st.text_area("السبب:", key=f"jus_del_{sel_mid}")
                    if to_del and details: details = f"حذف {to_del}: {details}"
                elif rtype == "إضافة طالب":
                    r_add = st.text_input("رقم التسجيل:", key=f"add_{sel_mid}")
                    details = st.text_area("ملاحظات:", key=f"jus_add_{sel_mid}")
                    if r_add and details: details = f"إضافة {r_add}: {details}"
                
                if details and rtype != "":
                    if st.button("إرسال", key=f"send_{sel_mid}"):
                        res, msg = save_and_send_request(rtype, p_name, sel_mid, sel_memo['عنوان المذكرة'], details)
                        st.success(msg) if res else st.error(msg)
            else:
                # القائمة (List View)
                memos = df_memos[(df_memos["الأستاذ"] == p_name) & (df_memos["تم التسجيل"] == "نعم")]
                if not memos.empty:
                    cols = st.columns(2)
                    for i, (_, m) in enumerate(memos.iterrows()):
                        with cols[i%2]:
                            st.markdown(f"""
                            <div class="card" style="cursor:pointer; border-top:5px solid #10B981;">
                                <h4>{m['رقم المذكرة']} - {m['عنوان المذكرة']}</h4>
                                <p style="font-size:0.8em; color:#94A3B8;">انقر على الزر بالأسفل للتفاصيل</p>
                            </div>
                            """, unsafe_allow_html=True)
                            if st.button("⚙️ إدارة وتفاصيل", key=f"mgr_{m['رقم المذكرة']}"):
                                st.session_state.selected_memo = m['رقم المذكرة']
                                st.rerun()

        with t2: # كلمات السر
            pwds = df_prof_memos[df_prof_memos["الأستاذ"] == p_name]
            for _, r in pwds.iterrows():
                st.markdown(f"<h3 style='color:#FFD700'>{r['كلمة سر التسجيل']}</h3>", unsafe_allow_html=True)

        with t3: # إشعارات
            my_reqs = df_requests[df_requests["الأستاذ"] == p_name]
            if not my_reqs.empty:
                for _, r in my_reqs.iterrows():
                    c = "#10B981" if r['الحالة'] == "مقبول" else "#F59E0B"
                    st.markdown(f"<div class='card' style='border-right:4px solid {c};'><h4>{r['نوع الطلب']} - {r['رقم المذكرة']}</h4><p>الحالة: <b>{r['الحالة']}</b></p></div>", unsafe_allow_html=True)
            else: st.info("لا توجد إشعارات")

        with t4: # المتاحة
            avail = df_memos[(df_memos["الأستاذ"] == p_name) & (df_memos["تم التسجيل"] != "نعم")]
            for _, m in avail.iterrows():
                st.markdown(f"<div class='card'><h4>{m['رقم المذكرة']}</h4><p>{m['عنوان المذكرة']}</p></div>", unsafe_allow_html=True)

# فضاء الإدارة
elif st.session_state.user_type == "admin":
    if not st.session_state.logged_in:
        with st.form("a_login"):
            u = st.text_input("User"); p = st.text_input("Pass", type="password")
            if st.form_submit_button("Login"):
                if verify_admin(u,p)[0]: st.session_state.logged_in = True; st.rerun()
    else:
        t1, t2, t3 = st.tabs(["بيانات", "إدارة الطلبات", "صيانة"])
        with t1: st.dataframe(df_memos)
        
        with t2:
            if not st.session_state.get('admin_edit_req'):
                # عرض الجدول
                st.subheader("سجل الطلبات الواردة")
                for idx, row in df_requests.iterrows():
                    c = "#10B981" if row['الحالة'] == "مقبول" else "#F59E0B"
                    c1, c2, c3 = st.columns([4, 1, 1])
                    with c1:
                        st.markdown(f"<div style='background:#1E293B; padding:10px; border-radius:5px; margin-bottom:5px; border-right:3px solid {c};'><b>{row['نوع الطلب']}</b> - {row['رقم المذكرة']} <br> {row['الحالة']}</div>", unsafe_allow_html=True)
                    with c3:
                        if st.button("⚙️", key=f"edit_{idx}"):
                            st.session_state.admin_edit_req = idx
                            st.rerun()
            else:
                # صفحة التعديل
                idx = st.session_state.admin_edit_req
                req_row = df_requests.iloc[idx]
                
                st.empty()
                st.markdown("<div class='card'><h2>⚖️ إدارة الطلب</h2></div>", unsafe_allow_html=True)
                
                c1, c2 = st.columns(2)
                with c1:
                    st.write(f"**النوع:** {req_row['نوع الطلب']}")
                    st.write(f"**الأستاذ:** {req_row['الأستاذ']}")
                    st.write(f"**المذكرة:** {req_row['رقم المذكرة']}")
                    st.info(f"**التفاصيل:** {req_row['العنوان الجديد']}")
                
                with c2:
                    new_status = st.selectbox("القرار:", ["قيد المراجعة", "مقبول", "مرفوض"], index=["قيد المراجعة", "مقبول", "مرفوض"].index(req_row['الحالة']))
                    admin_notes = st.text_area("ملاحظاتك:", value=req_row.get('ملاحظات الإدارة', ''))
                
                c_b1, c_b2 = st.columns(2)
                with c_b1:
                    if st.button("💾 حفظ", type="primary"):
                        # تحديث الشيت
                        sheet_idx = idx + 2
                        body = {
                            "valueInputOption": "USER_ENTERED",
                            "data": [
                                {"range": f"Feuille 1!D{sheet_idx}", "values": [[new_status]]},
                                {"range": f"Feuille 1!J{sheet_idx}", "values": [[admin_notes]]}
                            ]
                        }
                        sheets_service.spreadsheets().values().batchUpdate(spreadsheetId=REQUESTS_SHEET_ID, body=body).execute()
                        st.success("تم الحفظ"); clear_cache()
                        del st.session_state.admin_edit_req
                        st.rerun()
                with c_b2:
                    if st.button("إلغاء"):
                        del st.session_state.admin_edit_req
                        st.rerun()

        with t3:
            st.subheader("الربط والصيانة")
            if st.button("🔄 بدء عملية الربط (مع تقرير)", type="primary"):
                with st.spinner("جاري..."):
                    s, m = sync_student_registration_numbers()
                    st.success(m) if s else st.info(m)
                    if s: clear_cache(); st.rerun()

st.markdown("<div style='text-align:center; color:#64748B;'>© 2026 جامعة محمد البشير الإبراهيمي</div>", unsafe_allow_html=True)
