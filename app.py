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
    text-align: center; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3); position: relative; overflow: hidden;
}
.kpi-value { font-size: 2.5rem; font-weight: 900; color: #FFD700; margin: 15px 0; }
.kpi-label { font-size: 1.2rem; color: #94A3B8; font-weight: 600; text-transform: uppercase; }
.alert-card {
    background: linear-gradient(90deg, #8B4513 0%, #A0522D 100%);
    border: 1px solid #CD853F; color: white; padding: 25px; border-radius: 12px; text-align: center;
}
.progress-container { background-color: #0F172A; border-radius: 99px; padding: 6px; margin: 20px 0; overflow: hidden; }
.progress-bar {
    height: 24px; border-radius: 99px;
    background: linear-gradient(90deg, #2F6F7E 0%, #285E6B 50%, #FFD700 100%);
    transition: width 1s cubic-bezier(0.4, 0, 0.2, 1);
}
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

# دالة قوية لجلب الإيميل (الحل للمشكلة 3)
def get_student_email(reg_no, full_name_fallback, df_students):
    # 1. البحث برقم التسجيل
    if reg_no:
        match = df_students[df_students["رقم التسجيل"].astype(str).str.strip() == str(reg_no).strip()]
        if not match.empty:
            # البحث في أعمدة مختلفة للإيميل
            for col in ["البريد الإلكتروني", "email", "Email"]:
                if col in match.columns:
                    email = match.iloc[0].get(col, "").strip()
                    if email and "@" in email: return email
    
    # 2. البحث بالاسم (احتياطي)
    if full_name_fallback:
        parts = full_name_fallback.strip().split(' ', 1)
        if len(parts) == 2:
            lname, fname = parts[0], parts[1]
            # التعامل مع اختلافات الأعمدة
            possible_lname = ["لقب", "اللقب"]
            possible_fname = ["إسم", "الإسم", "اسم"]
            
            for pl in possible_lname:
                for pf in possible_fname:
                    if pl in df_students.columns and pf in df_students.columns:
                        match = df_students[
                            (df_students[pl].astype(str).str.strip() == lname) & 
                            (df_students[pf].astype(str).str.strip() == fname)
                        ]
                        if not match.empty:
                            for col in ["البريد الإلكتروني", "email", "Email"]:
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

# ---------------- الجديد: ربط ذكي لـ S و T (الحل للمشكلة 1) ----------------
def sync_student_registration_numbers():
    try:
        st.info("⏳ جاري الربط الذكي للأعمدة S و T...")
        df_s = load_students()
        df_m = load_memos()
        updates = []
        
        # فلترة الطلاب الذين لديهم مذكرات
        # إنشاء قاموس: رقم المذكرة -> قائمة الطلاب (ديكشنري لسهولة الوصول)
        memo_to_students = {}
        for _, s_row in df_s[df_s["رقم المذكرة"].notna() & (df_s["رقم المذكرة"] != "")].iterrows():
            m_id = str(s_row["رقم المذكرة"]).strip()
            reg_no = str(s_row.get("رقم التسجيل", "")).strip()
            
            # بناء الاسم للتحقق
            lname = s_row.get('لقب', s_row.get('اللقب', ''))
            fname = s_row.get('إسم', s_row.get('إسم', ''))
            full_name = f"{lname} {fname}".strip()
            
            if m_id not in memo_to_students: memo_to_students[m_id] = []
            memo_to_students[m_id].append({"reg": reg_no, "name": full_name})

        for index, row in df_m.iterrows():
            memo_id = str(row.get("رقم المذكرة", "")).strip()
            if not memo_id or memo_id not in memo_to_students: continue
            
            s1_name = str(row.get("الطالب الأول", "")).strip()
            s2_name = str(row.get("الطالب الثاني", "")).strip()
            
            students_in_this_memo = memo_to_students[memo_id]
            reg_s1 = ""
            reg_s2 = ""
            
            # 1. إذا كان هناك طالب ثاني في المذكرة، حاول مطابقته أولاً (للتأكد من العمود T)
            if s2_name:
                found_s2 = next((s for s in students_in_this_memo if s["name"] == s2_name), None)
                if found_s2:
                    reg_s2 = found_s2["reg"]
                    students_in_this_memo.remove(found_s2)
            
            # 2. الطالب المتبقي هو الطالب الأول (عمود S)
            if students_in_this_memo:
                # إذا لم يتم العثور على تطابق للطالب الثاني، ناختر الأول للطالب الأول
                # ولكن إذا وجدنا الطالب الثاني، ناخذ المتبقي للطالب الأول
                candidate_s1 = students_in_this_memo[0]
                if candidate_s1["name"] == s1_name or not s1_name:
                    reg_s1 = candidate_s1["reg"]
            
            row_idx = index + 2
            if reg_s1: updates.append({"range": f"Feuille 1!S{row_idx}", "values": [[reg_s1]]})
            if reg_s2: updates.append({"range": f"Feuille 1!T{row_idx}", "values": [[reg_s2]]})
        
        if updates:
            body = {"valueInputOption": "USER_ENTERED", "data": updates}
            sheets_service.spreadsheets().values().batchUpdate(spreadsheetId=MEMOS_SHEET_ID, body=body).execute()
            return True, f"✅ تم تحديث {len(updates)} خلية (S و T)."
        return False, "لا توجد بيانات جديدة للتحديث."
    except Exception as e:
        return False, f"خطأ: {str(e)}"

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
        
        request_titles = {"تغيير عنوان المذكرة": "طلب تغيير عنوان", "حذف طالب": "طلب حذف", "إضافة طالب": "طلب إضافة", "تنازل": "طلب تنازل"}
        subject = f"{request_titles.get(req_type, 'طلب')} - {memo_id}"
        email_body = f"<html dir='rtl'><body><h2>{subject}</h2><p>من: {prof_name}</p><p>{details_text}</p></body></html>"
        msg = MIMEMultipart('alternative')
        msg['From'], msg['To'], msg['Subject'] = EMAIL_SENDER, ADMIN_EMAIL, subject
        msg.attach(MIMEText(email_body, 'html', 'utf-8'))
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls(); server.login(EMAIL_SENDER, EMAIL_PASSWORD); server.send_message(msg)
        return True, "✅ تم إرسال الطلب"
    except Exception as e:
        return False, f"خطأ: {str(e)}"

# ---------------- منطق التسجيل (مع ربط S و T) ----------------
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

        # تحديث شيت المذكرات (مع S و T)
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
            sheets_service.spreadsheets().values().update(spreadsheetId=STUDENTS_SHEET_ID, range=f"Feuille 1!{col_letter(students_cols.index('رقم المذكرة')+1)}{s2_idx}", valueInputOption="USER_ENTERED", body={"values": [[note_number]]}).execute()

        clear_cache()
        return True, "✅ تم التسجيل"
    except Exception as e:
        return False, f"❌ {str(e)}"

# ---------------- دوال التحقق ----------------
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

# ---------------- Session State ----------------
if 'user_type' not in st.session_state:
    st.session_state.user_type = None
    st.session_state.logged_in = False
    st.session_state.selected_memo = None # لحالة النافذة المنبثقة

df_students = load_students(); df_memos = load_memos(); df_prof_memos = load_prof_memos(); df_requests = load_requests()

# ---------------- الصفحة الرئيسية ----------------
if st.session_state.user_type is None:
    st.markdown("<h1 style='text-align: center;'>نظام تسجيل المذكرات</h1>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("<div class='card' style='text-align: center;'><h3>👨‍🎓 فضاء الطلبة</h3></div>", unsafe_allow_html=True)
        if st.button("دخول الطلبة", key="btn_student"): st.session_state.user_type = "student"; st.rerun()
    with c2:
        st.markdown("<div class='card' style='text-align: center;'><h3>👨‍🏫 فضاء الأساتذة</h3></div>", unsafe_allow_html=True)
        if st.button("دخول الأساتذة", key="btn_prof"): st.session_state.user_type = "professor"; st.rerun()
    with c3:
        st.markdown("<div class='card' style='text-align: center;'><h3>⚙️ فضاء الإدارة</h3></div>", unsafe_allow_html=True)
        if st.button("دخول الإدارة", key="btn_admin"): st.session_state.user_type = "admin"; st.rerun()

# ---------------- فضاء الطلبة ----------------
elif st.session_state.user_type == "student":
    if not st.session_state.logged_in:
        # (نموذج تسجيل دخول مختصر للتبسيط، نفس المنطق السابق)
        with st.form("login"):
            u = st.text_input("اسم المستخدم")
            p = st.text_input("كلمة المرور", type="password")
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
            # عرض إشعارات الطالب
            reqs = df_requests[df_requests["رقم المذكرة"].astype(str).str.strip() == note_id]
            if not reqs.empty:
                for _, r in reqs.iterrows():
                    hide = r['نوع الطلب'] in ["حذف طالب", "تنازل"]
                    det = r.get('العنوان الجديد', r.get('المبررات', ''))
                    st.markdown(f"<div class='card'><h4>{r['نوع الطلب']}</h4><p>{det if not hide else 'التفاصيل مخفية'}</p></div>", unsafe_allow_html=True)
            else: st.info("لا توجد إشعارات")

# ---------------- فضاء الأساتذة (مع التعديلات) ----------------
elif st.session_state.user_type == "professor":
    if not st.session_state.logged_in:
        with st.form("p_login"):
            u = st.text_input("اسم المستخدم")
            p = st.text_input("كلمة المرور", type="password")
            if st.form_submit_button("دخول"):
                v, r = verify_professor(u, p, df_prof_memos)
                if v: st.session_state.professor = r; st.session_state.logged_in = True; st.rerun()
                else: st.error(r)
    else:
        prof = st.session_state.professor
        p_name = prof["الأستاذ"]
        
        # التبويبات الجديدة
        t1, t2, t3, t4 = st.tabs(["المذكرات المسجلة", "كلمات السر", "الإشعارات", "المتاحة"])
        
        with t1:
            st.subheader("المذكرات المسجلة")
            memos = df_memos[(df_memos["الأستاذ"] == p_name) & (df_memos["تم التسجيل"] == "نعم")]
            
            # عرض المذكرات كبطاقات
            cols = st.columns(2)
            for i, (_, m) in enumerate(memos.iterrows()):
                with cols[i%2]:
                    mid = m['رقم المذكرة']
                    title = m['عنوان المذكرة']
                    
                    # البطاقة (تصميم بسيط للنقر)
                    st.markdown(f"""
                    <div class="card" style="cursor:pointer; border-top: 5px solid #10B981;">
                        <h4>{mid}</h4>
                        <p>{title}</p>
                        <p style="font-size:0.9em; color:#94A3B8;">انظر أدناه للتفاصيل</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # زر التفاعل (الحل لمشكلة الضغط)
                    if st.button("⚙️ إدارة وتفاصيل", key=f"mgr_{mid}"):
                        st.session_state.selected_memo = mid
                        st.rerun()
            
            # النافذة المنبثقة (Modal Logic)
            if st.session_state.selected_memo:
                sel_mid = st.session_state.selected_memo
                sel_memo = memos[memos["رقم المذكرة"] == sel_mid].iloc[0]
                
                st.markdown("---")
                st.markdown(f"<div class='card' style='border: 2px solid #2F6F7E;'><h2>🔧 تفاصيل المذكرة: {sel_mid}</h2></div>", unsafe_allow_html=True)
                
                # عرض الطلاب والإيميلات
                s1_name = sel_memo['الطالب الأول']
                s2_name = sel_memo.get('الطالب الثاني', '')
                
                # جلب الإيميلات (باستخدام الدالة المحسنة)
                s1_email = get_student_email(sel_memo.get('رقم تسجيل الطالب 1', ''), s1_name, df_students)
                s2_email = get_student_email(sel_memo.get('رقم تسجيل الطالب 2', ''), s2_name, df_students) if s2_name else ""
                
                st.markdown(f"""
                <div style='background:#1E293B; padding:15px; border-radius:10px; margin-bottom:15px;'>
                    <h4>الطالب الأول: {s1_name}</h4>
                    {f"<p>📧 {s1_email}</p>" if s1_email else "<p>لا يوجد إيميل</p>"}
                </div>
                """, unsafe_allow_html=True)
                
                if s2_name:
                    st.markdown(f"""
                    <div style='background:#1E293B; padding:15px; border-radius:10px; margin-bottom:15px;'>
                        <h4>الطالب الثاني: {s2_name}</h4>
                        {f"<p>📧 {s2_email}</p>" if s2_email else "<p>لا يوجد إيميل</p>"}
                    </div>
                    """, unsafe_allow_html=True)

                # التقدم
                prog_val = int(sel_memo.get('نسبة التقدم', 0)) if str(sel_memo.get('نسبة التقدم', 0)).isdigit() else 0
                st.markdown(f"<div class='progress-container'><div class='progress-bar' style='width:{prog_val}%;'></div></div>", unsafe_allow_html=True)
                
                new_prog = st.selectbox("تحديث التقدم:", ["0%", "30%", "60%", "100%"], key=f"np_{sel_mid}")
                if st.button("حفظ التقدم", key=f"sv_{sel_mid}"):
                    sheets_service.spreadsheets().values().update(spreadsheetId=MEMOS_SHEET_ID, range=f"Feuille 1!Q{memos.index[sel_memo]+2}", valueInputOption="USER_ENTERED", body={"values": [[int(new_prog[:-1])]]}).execute()
                    st.success("تم التحديث"); time.sleep(1); st.rerun()
                
                # الطلبات
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
                    if st.button("إرسال الطلب", key=f"send_{sel_mid}"):
                        res, msg = save_and_send_request(rtype, p_name, sel_mid, sel_memo['عنوان المذكرة'], details)
                        st.success(msg) if res else st.error(msg)

                if st.button("❌ إغلاق النافذة"):
                    del st.session_state.selected_memo
                    st.rerun()

        with t2: # كلمات السر
            pwds = df_prof_memos[df_prof_memos["الأستاذ"] == p_name]
            for _, row in pwds.iterrows():
                st.markdown(f"<h3 style='color:#FFD700'>{row['كلمة سر التسجيل']}</h3>", unsafe_allow_html=True)

        with t3: # إشعارات الأستاذ (الحل للمشكلة 4)
            st.subheader("إشعاراتي")
            my_reqs = df_requests[df_requests["الأستاذ"] == p_name]
            if not my_reqs.empty:
                for _, r in my_reqs.iterrows():
                    status_color = "#10B981" if r['الحالة'] == "مقبول" else "#F59E0B"
                    st.markdown(f"""
                    <div class="card" style="border-right: 4px solid {status_color};">
                        <h4>{r['نوع الطلب']} - {r['رقم المذكرة']}</h4>
                        <p>الحالة: <b>{r['الحالة']}</b></p>
                        <p>{r['الوقت']}</p>
                    </div>
                    """, unsafe_allow_html=True)
            else: st.info("لا توجد إشعارات")

        with t4: # المتاحة
            avail = df_memos[(df_memos["الأستاذ"] == p_name) & (df_memos["تم التسجيل"] != "نعم")]
            for _, m in avail.iterrows():
                st.markdown(f"<div class='card'><h4>{m['رقم المذكرة']}</h4><p>{m['عنوان المذكرة']}</p></div>", unsafe_allow_html=True)

# ---------------- فضاء الإدارة ----------------
elif st.session_state.user_type == "admin":
    if not st.session_state.logged_in:
        with st.form("a_login"):
            u = st.text_input("User"); p = st.text_input("Pass", type="password")
            if st.form_submit_button("Login"):
                if verify_admin(u,p)[0]: st.session_state.logged_in = True; st.rerun()
    else:
        t1, t2, t3 = st.tabs(["بيانات", "طلبات", "صيانة"])
        with t1: st.dataframe(df_memos)
        with t2: st.dataframe(df_requests)
        with t3:
            if st.button("🔄 تشغيل الربط الذكي (S & T)"):
                s, m = sync_student_registration_numbers()
                st.success(m) if s else st.info(m)
                clear_cache(); st.rerun()

st.markdown("---")
st.markdown("<div style='text-align:center; color:#64748B;'>© 2026 University</div>", unsafe_allow_html=True)
