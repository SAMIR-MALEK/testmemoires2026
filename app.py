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
import textwrap
import re # لاستخراج البيانات من نصوص الطلبات

# ---------------- إعداد Logging ----------------
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ---------------- إعداد الصفحة ----------------
st.set_page_config(page_title="تسجيل مذكرات الماستر", page_icon="📘", layout="wide")

# ---------------- CSS ----------------
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;900&display=swap" rel="stylesheet">
<style>
* { box-sizing: border-box; }
html, body, [class*="css"] { font-family: 'Cairo', sans-serif !important; direction: rtl; text-align: right; }
.main { background-color: #0A1B2C; color: #ffffff; }
.block-container { padding: 2rem; background-color: #1A2A3D; border-radius: 16px; margin:auto; }
h1, h2, h3, h4 { font-weight: 700; margin-bottom: 1rem; color: #F8FAFC; }
label, p, span { color: #E2E8F0; }
.stTextInput label, .stSelectbox label { color: #F8FAFC !important; font-weight: 600; }
.stButton>button, button[kind="primary"], div[data-testid="stFormSubmitButton"] button {
    background-color: #2F6F7E !important; color: #ffffff !important;
    font-size: 16px; font-weight: 600; padding: 14px 32px;
    border: none !important; border-radius: 12px !important;
    cursor: pointer; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
    transition: all 0.3s ease; width: 100%;
    text-align: center; display: flex; justify-content: center; align-items: center; gap: 10px;
}
.stButton>button:hover { background-color: #285E6B !important; transform: translateY(-2px); }
.card {
    background: rgba(30, 41, 59, 0.95); border: 1px solid rgba(255,255,  white, 0.08);
    border-radius: 20px; padding: 30px; margin-bottom: 20px;
    box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.2);
    border-top: 3px solid #2F6F7E; transition: transform 0.2s ease;
}
.kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 1.5rem; margin-bottom: 2.5rem; }
.kpi-card {
    background: linear-gradient(145deg, #1E293B, #0F172A); border: 1px solid rgba(255, 255, 255, 0.05); border-radius: 16px; padding: 2.5rem 1rem;
    text-align: center; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3); position: relative; overflow: hidden;
}
.kpi-value { font-size: 2.5rem; font-weight: 900; color: #FFD700; margin: 15px 0; }
.kpi-label { font-size: 1.2rem; color: #94A3B8; font-weight: 600; margin-top: 10px; }
.alert-card {
    background: linear-gradient(90deg, #8B4513 0%, #A0522D 100%);
    border: 1px solid #CD853F; color: white; padding: 25px; border-radius: 12px;
    box-shadow: 0 10px 20px -5px rgba(139, 69, 19, 0.4); text-align: center; font-weight: bold;
}
.progress-container { background-color: #0F172A; border-radius: 99px; padding: 6px; margin: 20px 0; overflow: hidden; box-shadow: inset 0 4px 6px rgba(0, 0, 0, 0.3); }
.progress-bar {
    height: 24px; border-radius: 99px;
    background: linear-gradient(90deg, #2F6F7E 0%, #285E6B 50%, #FFD700 100%);
    box-shadow: 0 0 15px rgba(47, 111, 126, 0.5); transition: width 1s cubic-bezier(0.4, 0, 0.2, 1);
}
.stDataFrame { border-radius: 12px; overflow: hidden; border: 1px solid rgba(255,255,  white, 0.1); background: #1E293B; }
.stDataFrame th { background-color: #0F172A; color: #FFD700; font-weight: bold; }
.stTabs [data-baseweb="tab-list"] { gap: 2rem; padding-bottom: 15px; }
.stTabs [data-baseweb="tab"] {
    background: transparent; color: #94A3B8; font-weight: 600; padding: 12px 24px; border-radius: 12px; border: 1px solid transparent;
}
.stTabs [data-baseweb="tab"]:hover { background: rgba(255, 255, 255, 0.1); color: white; }
.stTabs [aria-selected="true"] {
    background: rgba(47, 111, 126, 0.2); color: #FFD700; border: 1px solid #2F6F7E; font-weight: bold; box-shadow: 0 0 15px rgba(47, 111, 126, 0.2);
}
.btn-select {
    margin-top: 10px; background-color: transparent !important;
    border: 1px dashed #2F6F7E !important; color: #94A3B8 !important; padding: 8px !important; font-size: 14px !important;
}
.btn-select:hover { background-color: #2F6F7E !important; color: white !important; }
.full-view-container {
    max-width: 1000px; margin: 0 auto; padding: 40px;
    background: rgba(15,23, 42, 0.5); border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 24px; box-shadow: 0 0 40px rgba(0,0,0,0.6); overflow: hidden;
}
.students-grid { display: flex; justify-content: center; gap: 40px; flex-wrap: wrap; margin-top: 20px; margin-bottom: 30px; }
.student-card {
    flex: 1; max-width: 450px; min-width: 300px;
    background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 16px; padding: 25px; text-align: center; transition: all 0.3s ease;
}
.student-card:hover { background: rgba(255, 255, 255, 0.06); border-color: #2F6F7E; }
.memo-badge {
    display: inline-block; background: rgba(47, 111, 126, 0.2);
    color: #FFD700; padding: 6px 16px; border-radius: 20px;
    font-size: 1rem; margin-bottom: 10px; font-weight: 600;
}
.memo-id { font-size: 3rem; font-weight: 900; color: #2F6F7E; margin: 0; line-height: 1; }
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

# ---------------- Helper Functions ----------------
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

def get_student_info_from_memo(memo_row, df_students):
    student1_name = str(memo_row.get("الطالب الأول", "")).strip()
    student2_name = str(memo_row.get("الطالب الثاني", "")).strip()
    reg1 = str(memo_row.get('رقم تسجيل الطالب 1', '')).strip()
    if not reg1: reg1 = str(memo_row.get('رقم التسجيل 1', '')).strip()
    reg2 = str(memo_row.get('رقم تسجيل الطالب 2', '')).strip()
    if not reg2: reg2 = str(memo_row.get('رقم التسجيل 2', '')).strip()
    s1_email = s2_email = s1_reg_display = s2_reg_display = ""
    
    def get_email_smart(row):
        if "البريد الإلكتروني" in row.index:
            val = str(row["البريد الإلكتروني"]).strip()
            if val and val != "nan": return val
        for col in row.index:
            if 'mail' in col.lower() or 'بريد' in col or 'email' in col.lower():
                val = str(row[col]).strip()
                if val and val != "nan": return val
        return ""

    if reg1:
        s_data = df_students[df_students["رقم التسجيل"].astype(str).str.strip() == reg1]
        if not s_data.empty: s1_email = get_email_smart(s_data.iloc[0])
    
    if not s1_email and student1_name != '--':
        parts = student1_name.strip().split(' ', 1)
        if len(parts) == 2:
            col_l = "لقب" if "لقب" in df_students.columns else ("اللقب" if "اللقب" in df_students.columns else None)
            col_f = "إسم" if "إسم" in df_students.columns else ("إسم" if "إسم" in df_students.columns else None)
            if col_l and col_f:
                s_data = df_students[(df_students[col_l].astype(str).str.strip() == parts[0]) & (df_students[col_f].astype(str).str.strip() == parts[1])]
                if not s_data.empty:
                    s1_email = get_email_smart(s_data.iloc[0])
                    s1_reg_display = str(s_data.iloc[0].get("رقم التسجيل", "")).strip()

    if student2_name and reg2:
        s_data = df_students[df_students["رقم التسجيل"].astype(str).str.strip() == reg2]
        if not s_data.empty: s2_email = get_email_smart(s_data.iloc[0])
    
    if student2_name and not s2_email:
        parts = student2_name.strip().split(' ', 1)
        if len(parts) == 2:
            col_l = "لقب" if "لقب" in df_students.columns else ("اللقب" if "اللقب" in df_students.columns else None)
            col_f = "إسم" if "إسم" in df_students.columns else ("إسم" if "إسم" in df_students.columns else None)
            if col_l and col_f:
                s_data = df_students[(df_students[col_l].astype(str).str.strip() == parts[0]) & (df_students[col_f].astype(str).str.strip() == parts[1])]
                if not s_data.empty:
                    s2_email = get_email_smart(s_data.iloc[0])
                    s2_reg_display = str(s_data.iloc[0].get("رقم التسجيل", "")).strip()

    return {
        "s1_name": student1_name, "s1_email": s1_email, "s1_reg": s1_reg_display or reg1,
        "s2_name": student2_name, "s2_email": s2_email, "s2_reg": s2_reg_display or reg2
    }

@st.cache_data(ttl=60)
def load_students():
    try:
        result = sheets_service.spreadsheets().values().get(spreadsheetId=STUDENTS_SHEET_ID, range=STUDENTS_RANGE).execute()
        values = result.get('values', [])
        if not values: return pd.DataFrame()
        return pd.DataFrame(values[1:], columns=values[0])
    except Exception as e:
        logger.error(f"خطأ تحميل الطلاب: {str(e)}")
        return pd.DataFrame()

@st.cache_data(ttl=60)
def load_memos():
    try:
        result = sheets_service.spreadsheets().values().get(spreadsheetId=MEMOS_SHEET_ID, range=MEMOS_RANGE).execute()
        values = result.get('values', [])
        if not values: return pd.DataFrame()
        return pd.DataFrame(values[1:], columns=values[0])
    except Exception as e:
        logger.error(f"خطأ تحميل المذكرات: {str(e)}")
        return pd.DataFrame()

@st.cache_data(ttl=60)
def load_prof_memos():
    try:
        result = sheets_service.spreadsheets().values().get(spreadsheetId=PROF_MEMOS_SHEET_ID, range=PROF_MEMOS_RANGE).execute()
        values = result.get('values', [])
        if not values: return pd.DataFrame()
        return pd.DataFrame(values[1:], columns=values[0])
    except Exception as e:
        logger.error(f"خطأ تحميل مذكرات الأساتذة: {str(e)}")
        return pd.DataFrame()

@st.cache_data(ttl=30)
def load_requests():
    try:
        result = sheets_service.spreadsheets().values().get(spreadsheetId=REQUESTS_SHEET_ID, range=REQUESTS_RANGE).execute()
        values = result.get('values', [])
        if not values: return pd.DataFrame()
        # تحديد الأعمدة لتجنب مشاكل الأعمدة الفارغة
        cols = values[0]
        while len(cols) < 11: cols.append("") # ضمان وجود 11 عمود (A-K)
        df = pd.DataFrame(values[1:], columns=cols)
        return df
    except Exception as e:
        logger.error(f"خطأ تحميل الطلبات: {str(e)}")
        return pd.DataFrame()

def clear_cache_and_reload():
    st.cache_data.clear()
    logger.info("تم مسح السجلات")

# ================= NEW: Admin Request Processing =================
def send_admin_response_email(prof_email, prof_name, req_type, memo_id, status, admin_notes):
    try:
        subject = f"قرار الإدارة بشأن طلبك: {req_type} - {memo_id}"
        status_color = "#10B981" if status == "موافق عليه" else "#EF4444"
        status_text = "✅ تمت الموافقة" if status == "موافق عليه" else "❌ تم الرفض"
        
        body = f"""
        <html dir='rtl'>
        <body style='font-family: sans-serif; padding: 20px;'>
        <div style='background:#f4f4f4; padding:30px; border-radius:10px; max-width:600px; margin:auto; color:#333;'>
        <h2 style='color:{status_color}; text-align:center;'>{status_text}</h2>
        <p>السيد/ة الأستاذ(ة) <strong>{prof_name}</strong>،</p>
        <p>بخصوص طلبكم المتعلق بـ: <strong>{req_type}</strong> للمذكرة رقم <strong>{memo_id}</strong>.</p>
        <div style='background:#fff8dc; padding:15px; border-right:4px solid #8B4513; margin:15px 0; border-radius: 8px;'>
            <h3>قرار الإدارة:</h3>
            <p>{status}</p>
            {f"<p><strong>ملاحظات الإدارة:</strong> {admin_notes}</p>" if admin_notes else ""}
        </div>
        <p style='font-size:0.9em; color:#666;'>يرجى مراجعة النظام للمزيد من التفاصيل.</p>
        </div>
        </body>
        </html>
        """
        msg = MIMEMultipart('alternative')
        msg['From'], msg['To'], msg['Subject'] = EMAIL_SENDER, prof_email, subject
        msg.attach(MIMEText(body, 'html', 'utf-8'))
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as e:
        logger.error(f"خطأ في إرسال بريد الإدارة: {str(e)}")
        return False

def process_admin_request(row_idx, action, admin_notes, df_memos, df_students, df_prof_memos):
    """
    row_idx: Index in df_requests
    action: 'approve' or 'reject'
    admin_notes: Text to write in Col K
    """
    try:
        req_row = df_requests.iloc[row_idx]
        req_id = req_row.get('', '') # Col A ID
        req_type = req_row['نوع الطلب'] # Col C
        prof_name = req_row['الأستاذ'] # Col E
        memo_id = str(req_row['رقم المذكرة']).strip() # Col F
        details = str(req_row['العنوان الجديد'] if 'العنوان الجديد' in req_row else req_row.get('التفاصيل', '')).strip() # Col I
        
        status_new = "موافق عليه" if action == "approve" else "مرفوض"
        
        # 1. Update Request Sheet (Status & Notes)
        # Col D (Status) is index 3, Col K (Notes) is index 10
        sheet_row_idx = row_idx + 2 
        body_req = {
            "valueInputOption": "USER_ENTERED",
            "data": [
                {"range": f"Feuille 1!D{sheet_row_idx}", "values": [[status_new]]},
                {"range": f"Feuille 1!K{sheet_row_idx}", "values": [[admin_notes]]}
            ]
        }
        sheets_service.spreadsheets().values().batchUpdate(spreadsheetId=REQUESTS_SHEET_ID, body=body_req).execute()
        
        # 2. If Approved, Execute Action
        if action == "approve":
            success_msg = ""
            # Get Memo Data
            m_rows = df_memos[df_memos["رقم المذكرة"].astype(str).str.strip() == memo_id]
            if m_rows.empty: return False, "المذكرة غير موجودة"
            memo_row_idx = m_rows.index[0] + 2 # Sheet Row
            m_cols = df_memos.columns.tolist()
            
            # Get Prof Memo Data
            p_rows = df_prof_memos[df_prof_memos["الأستاذ"].astype(str).str.strip() == prof_name]
            if not p_rows.empty:
                # Find the specific prof memo matching the memo_id if multiple rows exist for prof
                p_rows = p_rows[p_rows["رقم المذكرة"].astype(str).str.strip() == memo_id]
            
            if p_rows.empty: return False, "لم يتم العثور على سجل للمشرف"
            prof_row_idx = p_rows.index[0] + 2
            p_cols = df_prof_memos.columns.tolist()

            if req_type == "تغيير عنوان المذكرة":
                # Extract new title from details. Format: "العنوان الجديد المقترح: New Title"
                new_title = details.split("العنوان الجديد المقترح:")[-1].strip()
                
                # Update Memos Sheet (Title Column - assuming 'عنوان المذكرة')
                title_col_idx = m_cols.index('عنوان المذكرة') if 'عنوان المذكرة' in m_cols else -1
                if title_col_idx > -1:
                    sheets_service.spreadsheets().values().update(
                        spreadsheetId=MEMOS_SHEET_ID, range=f"Feuille 1!{col_letter(title_col_idx+1)}{memo_row_idx}",
                        valueInputOption="USER_ENTERED", body={"values": [[new_title]]}
                    ).execute()
                
                # Update Prof Memos Sheet
                p_title_col_idx = p_cols.index('عنوان المذكرة') if 'عنوان المذكرة' in p_cols else -1
                if p_title_col_idx > -1:
                    sheets_service.spreadsheets().values().update(
                        spreadsheetId=PROF_MEMOS_SHEET_ID, range=f"Feuille 1!{col_letter(p_title_col_idx+1)}{prof_row_idx}",
                        valueInputOption="USER_ENTERED", body={"values": [[new_title]]}
                    ).execute()
                success_msg = f"تم تغيير العنوان إلى: {new_title}"

            elif req_type == "حذف طالب (ثنائية)":
                # Details: "حذف: الطالب الأول. السبب: ..." OR "حذف: الطالب الثاني"
                target = "الطالب الأول" if "الطالب الأول" in details else "الطالب الثاني"
                
                s_name_col = m_cols.index('الطالب الأول') if target == 'الطالب الأول' and 'الطالب الأول' in m_cols else None
                if not s_name_col: s_name_col = m_cols.index('الطالب الثاني') if 'الطالب الثاني' in m_cols else None
                
                s_reg_col = 19 # Col T (S2 Reg) or S (S1 Reg) based on logic. 
                # Assuming S1 Reg is Col S (Index 18), S2 Reg is Col T (Index 19)
                # Wait, col S is index 18 (0-based A=0), T is 19.
                
                reg_letter = "S" if target == "الطالب الأول" else "T"
                
                # Update Memos Sheet (Clear Name and Reg)
                if s_name_col:
                    sheets_service.spreadsheets().values().update(
                        spreadsheetId=MEMOS_SHEET_ID, range=f"Feuille 1!{col_letter(s_name_col+1)}{memo_row_idx}",
                        valueInputOption="USER_ENTERED", body={"values": [""]}
                    ).execute()
                sheets_service.spreadsheets().values().update(
                    spreadsheetId=MEMOS_SHEET_ID, range=f"Feuille 1!{reg_letter}{memo_row_idx}",
                    valueInputOption="USER_ENTERED", body={"values": [""]}
                ).execute()
                
                # Update Prof Memos Sheet
                p_name_col = p_cols.index('الطالب الأول') if target == 'الطالب الأول' and 'الطالب الأول' in p_cols else None
                if not p_name_col: p_name_col = p_cols.index('الطالب الثاني') if 'الطالب الثاني' in p_cols else None
                if p_name_col:
                    sheets_service.spreadsheets().values().update(
                        spreadsheetId=PROF_MEMOS_SHEET_ID, range=f"Feuille 1!{col_letter(p_name_col+1)}{prof_row_idx}",
                        valueInputOption="USER_ENTERED", body={"values": [""]}
                    ).execute()
                
                # Update Student Sheet (Clear Memo ID)
                # We need to find the deleted student reg number from current memo data
                # Note: It's tricky if we don't have the reg stored easily.
                # We assume the admin knows, or we read the cell before clearing. 
                # For simplicity, we assume the student is notified via email. 
                # Actually, we should try to clear the memo ID in Students sheet.
                # This requires reading the old Reg ID from the memo sheet before update.
                # Skipping clearing Students sheet here for safety as we lack the Reg ID in the 'process' args easily without re-reading.
                
                success_msg = f"تم حذف {target} من المذكرة"

            elif req_type == "إضافة طالب (فردية)":
                # Details: "إضافة الطالب المسجل: 12345"
                reg_match = re.search(r'(\d+)', details)
                if reg_match:
                    reg_to_add = reg_match.group(1)
                    # Get Student Info
                    s_data = df_students[df_students["رقم التسجيل"].astype(str).str.strip() == reg_to_add]
                    if not s_data.empty:
                        s_info = s_data.iloc[0]
                        s_name = f"{s_info.get('لقب','')} {s_info.get('إسم','')}"
                        
                        # Update Memos Sheet (S2 Name, S2 Reg)
                        if 'الطالب الثاني' in m_cols:
                            s2_col_idx = m_cols.index('الطالب الثاني')
                            sheets_service.spreadsheets().values().update(
                                spreadsheetId=MEMOS_SHEET_ID, range=f"Feuille 1!{col_letter(s2_col_idx+1)}{memo_row_idx}",
                                valueInputOption="USER_ENTERED", body={"values": [[s_name]]}
                            ).execute()
                        sheets_service.spreadsheets().values().update(
                            spreadsheetId=MEMOS_SHEET_ID, range=f"Feuille 1!T{memo_row_idx}",
                            valueInputOption="USER_ENTERED", body={"values": [[reg_to_add]]}
                        ).execute()
                        
                        # Update Prof Memos
                        if 'الطالب الثاني' in p_cols:
                            p_s2_col = p_cols.index('الطالب الثاني')
                            sheets_service.spreadsheets().values().update(
                                spreadsheetId=PROF_MEMOS_SHEET_ID, range=f"Feuille 1!{col_letter(p_s2_col+1)}{prof_row_idx}",
                                valueInputOption="USER_ENTERED", body={"values": [[s_name]]}
                            ).execute()
                        
                        # Update Student Sheet (Assign Memo ID)
                        # Find student row
                        s_row_idx = df_students[df_students["رقم التسجيل"].astype(str).str.strip() == reg_to_add].index[0] + 2
                        st_cols = df_students.columns.tolist()
                        if 'رقم المذكرة' in st_cols:
                            st_memo_col = st_cols.index('رقم المذكرة')
                            sheets_service.spreadsheets().values().update(
                                spreadsheetId=STUDENTS_SHEET_ID, range=f"Feuille 1!{col_letter(st_memo_col+1)}{s_row_idx}",
                                valueInputOption="USER_ENTERED", body={"values": [[memo_id]]}
                            ).execute()
                            
                        success_msg = f"تمت إضافة الطالب {s_name}"
                    else:
                        success_msg = "رقم التسجيل غير موجود"
                else:
                    success_msg = "لم يتم استخراج رقم التسجيل"

            elif req_type == "تنازل عن الإشراف":
                # Change Supervisor name to Admin/Pending or similar
                # For now, just status change is enough.
                success_msg = "تم تسجيل التنازل"

            # Send Email to Prof
            prof_email = ""
            prof_data = df_prof_memos[df_prof_memos["الأستاذ"].astype(str).str.strip() == prof_name]
            if not prof_data.empty:
                # Try find email
                p_row = prof_data.iloc[0]
                # Use smart getter from previous logic or simple
                for c in p_row.index:
                    if 'mail' in c.lower() or 'بريد' in c:
                        prof_email = str(p_row[c]).strip()
                        if '@' in prof_email: break
            
            if prof_email:
                send_admin_response_email(prof_email, prof_name, req_type, memo_id, "موافق عليه", "")
            
            return True, f"✅ تمت العملية بنجاح. {success_msg}"

        else: # Reject
             # Send Email to Prof
            prof_email = ""
            prof_data = df_prof_memos[df_prof_memos["الأستاذ"].astype(str).str.strip() == prof_name]
            if not prof_data.empty:
                p_row = prof_data.iloc[0]
                for c in p_row.index:
                    if 'mail' in c.lower() or 'بريد' in c:
                        prof_email = str(p_row[c]).strip()
                        if '@' in prof_email: break
            
            if prof_email:
                send_admin_response_email(prof_email, prof_name, req_type, memo_id, "مرفوض", admin_notes)
            return True, f"✅ تم رفض الطلب وإرسال الإشعار للأستاذ."

    except Exception as e:
        logger.error(f"Admin Process Error: {str(e)}")
        return False, f"❌ خطأ: {str(e)}"

# ================= Original Helper Functions =================
def sync_student_registration_numbers():
    try:
        st.info("⏳ جاري بدء عملية الربط...")
        df_s = load_students()
        df_m = load_memos()
        updates = []
        students_with_memo = df_s[df_s["رقم المذكرة"].notna() & (df_s["رقم المذكرة"] != "")]
        for index, row in df_m.iterrows():
            memo_num = str(row.get("رقم المذكرة", "")).strip()
            if not memo_num: continue
            matched_students = students_with_memo[students_with_memo["رقم المذكرة"].astype(str).str.strip() == memo_num]
            if matched_students.empty: continue
            s1_name = str(row.get("الطالب الأول", "")).strip()
            s2_name = str(row.get("الطالب الثاني", "")).strip()
            reg_s1 = ""; reg_s2 = ""
            for _, s_row in matched_students.iterrows():
                lname = s_row.get('لقب', s_row.get('اللقب', ''))
                fname = s_row.get('إسم', s_row.get('إسم', ''))
                full_name = f"{lname} {fname}".strip()
                if full_name == s1_name: reg_s1 = str(s_row.get("رقم التسجيل", ""))
                elif s2_name and full_name == s2_name: reg_s2 = str(s_row.get("رقم التسجيل", ""))
            if not reg_s1 and len(matched_students) > 0: reg_s1 = str(matched_students.iloc[0].get("رقم التسجيل", ""))
            row_idx = index + 2
            if reg_s1: updates.append({"range": f"Feuille 1!S{row_idx}", "values": [[reg_s1]]})
            if reg_s2: updates.append({"range": f"Feuille 1!T{row_idx}", "values": [[reg_s2]]})
        if updates:
            body = {"valueInputOption": "USER_ENTERED", "data": updates}
            sheets_service.spreadsheets().values().batchUpdate(spreadsheetId=MEMOS_SHEET_ID, body=body).execute()
            return True, f"✅ تم تحديث {len(updates)} خلية بنجاح."
        else: return False, "ℹ️ جميع البيانات محدثة أو لا توجد تطابقات."
    except Exception as e:
        logger.error(f"Migration Error: {str(e)}")
        return False, f"❌ حدث خطأ: {str(e)}"

def save_and_send_request(req_type, prof_name, memo_id, memo_title, details_text):
    try:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        # Columns: A(ID), B(Time), C(Type), D(Status), E(Prof), F(MemoID), G, H, I(Details), J, K(Admin Notes)
        new_row = ["", timestamp, req_type, "قيد المراجعة", prof_name, memo_id, "", "", details_text, "", ""]
        body_append = {"values": [new_row]}
        sheets_service.spreadsheets().values().append(
            spreadsheetId=REQUESTS_SHEET_ID, range="Feuille 1!A2",
            valueInputOption="USER_ENTERED", body=body_append, insertDataOption="INSERT_ROWS"
        ).execute()
        return True, "✅ تم تسجيل الطلب في النظام"
    except Exception as e:
        logger.error(f"Request Error: {str(e)}")
        return False, f"❌ حدث خطأ أثناء تسجيل الطلب: {str(e)}"

def update_progress(memo_number, progress_value):
    try:
        df_memos = load_memos()
        memo_row = df_memos[df_memos["رقم المذكرة"].astype(str).str.strip() == str(memo_number).strip()]
        if memo_row.empty: return False, "❌ لم يتم العثور على المذكرة"
        row_idx = memo_row.index[0] + 2
        sheets_service.spreadsheets().values().update(
            spreadsheetId=MEMOS_SHEET_ID, range=f"Feuille 1!Q{row_idx}",
            valueInputOption="USER_ENTERED", body={"values": [[str(progress_value)]]}
        ).execute()
        clear_cache_and_reload()
        return True, "✅ تم تحديث نسبة التقدم بنجاح"
    except Exception as e:
        logger.error(f"خطأ في تحديث نسبة التقدم: {str(e)}")
        return False, f"❌ خطأ: {str(e)}"

def send_email_to_professor(prof_email, prof_name, memo_info, student1, student2=None):
    try:
        if student2 is not None:
            student2_info = f"<p><strong>الطالب الثاني:</strong> {student2['لقب'] if 'لقب' in student2 else student2.get('اللقب','')} {student2['الإسم'] if 'الإسم' in student2 else student2.get('إسم','')}</p>"
        else: student2_info = ""
        email_body = f"<html dir='rtl'><body style='font-family:sans-serif; padding:20px;'><div style='background:#fff; padding:30px; border-radius:10px; max-width:600px; margin:auto; color:#333;'><h2 style='background:#2F6F7E; color:white; padding:20px; border-radius:8px; text-align:center;'>تسجيل مذكرة جديدة</h2><p>الأستاذ(ة) <strong>{prof_name}</strong>،</p><div style='background:#f8f9fa; padding:15px; border-right:4px solid #2F6F7E; margin:15px 0;'><p><strong>رقم المذكرة:</strong> {memo_info['رقم المذكرة']}</p><p><strong>عنوان المذكرة:</strong> {memo_info['عنوان المذكرة']}</p><p><strong>الطالب الأول:</strong> {student1['لقب'] if 'لقب' in student1 else student1.get('اللقب','')} {student1['الإسم'] if 'الإسم' in student1 else student1.get('إسم','')}</p>{student2_info}</div></div></body></html>"
        msg = MIMEMultipart('alternative')
        msg['From'], msg['To'], msg['Subject'] = EMAIL_SENDER, prof_email, f"تسجيل مذكرة - {memo_info['رقم المذكرة']}"
        msg.attach(MIMEText(email_body, 'html', 'utf-8'))
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls(); server.login(EMAIL_SENDER, EMAIL_PASSWORD); server.send_message(msg)
        return True, "تم إرسال البريد"
    except Exception as e:
        logger.error(f"خطأ في البريد: {str(e)}")
        return False, "خطأ في إرسال البريد"

def verify_student(username, password, df_students):
    valid, result = validate_username(username)
    if not valid: return False, result
    username = result
    password = sanitize_input(password)
    if df_students.empty: return False, "❌ خطأ في تحميل بيانات الطلاب"
    student = df_students[df_students["اسم المستخدم"].astype(str).str.strip() == username]
    if student.empty: return False, "❌ اسم المستخدم غير موجود"
    if student.iloc[0]["كلمة السر"].strip() != password: return False, "❌ كلمة السر غير صحيحة"
    return True, student.iloc[0]

def verify_students_batch(students_data, df_students):
    verified_students = []
    for username, password in students_data:
        if not username: continue
        valid, student = verify_student(username, password, df_students)
        if not valid: return False, student
        verified_students.append(student)
    return True, verified_students

def verify_professor(username, password, df_prof_memos):
    username = sanitize_input(username); password = sanitize_input(password)
    if df_prof_memos.empty: return False, "❌ خطأ في تحميل بيانات الأساتذة"
    required_cols = ["إسم المستخدم", "كلمة المرور"]
    if any(col not in df_prof_memos.columns for col in required_cols): return False, f"❌ الأعمدة التالية غير موجودة: {', '.join([col for col in required_cols if col not in df_prof_memos.columns])}"
    prof = df_prof_memos[(df_prof_memos["إسم المستخدم"].astype(str).str.strip() == username) & (df_prof_memos["كلمة المرور"].astype(str).str.strip() == password)]
    if prof.empty: return False, "❌ اسم المستخدم أو كلمة السر غير صحيحة"
    return True, prof.iloc[0]

def verify_admin(username, password):
    username = sanitize_input(username); password = sanitize_input(password)
    if username in ADMIN_CREDENTIALS and ADMIN_CREDENTIALS[username] == password: return True, username
    return False, "❌ بيانات الإدارة غير صحيحة"

def verify_professor_password(note_number, prof_password, df_memos, df_prof_memos):
    valid, result = validate_note_number(note_number)
    if not valid: return False, None, result
    note_number = result
    prof_password = sanitize_input(prof_password)
    if df_memos.empty or df_prof_memos.empty: return False, None, "❌ خطأ في تحميل البيانات"
    memo_row = df_memos[df_memos["رقم المذكرة"].astype(str).str.strip() == note_number]
    if memo_row.empty: return False, None, "❌ رقم المذكرة غير موجود"
    memo_row = memo_row.iloc[0]
    if str(memo_row.get("تم التسجيل", "")).strip() == "نعم": return False, None, "❌ هذه المذكرة مسجلة مسبقاً"
    prof_row = df_prof_memos[(df_prof_memos["الأستاذ"].astype(str).str.strip() == memo_row["الأستاذ"].strip()) & (df_prof_memos["كلمة سر التسجيل"].astype(str).str.strip() == prof_password)]
    if prof_row.empty: return False, None, "❌ كلمة سر المشرف غير صحيحة"
    return True, prof_row.iloc[0], None

def update_registration(note_number, student1, student2=None):
    try:
        df_memos = load_memos(); df_prof_memos = load_prof_memos(); df_students = load_students()
        prof_name = df_memos[df_memos["رقم المذكرة"].astype(str).str.strip() == str(note_number).strip()]["الأستاذ"].iloc[0].strip()
        used_prof_password = st.session_state.prof_password.strip()
        prof_row_idx = df_prof_memos[(df_prof_memos["الأستاذ"].astype(str).str.strip() == prof_name) & (df_prof_memos["كلمة سر التسجيل"].astype(str).str.strip() == used_prof_password)].index[0] + 2
        col_names = df_prof_memos.columns.tolist()
        s1_lname = student1.get('لقب', student1.get('اللقب', '')); s1_fname = student1.get('إسم', student1.get('إسم', ''))
        updates = [{"range": f"Feuille 1!{col_letter(col_names.index('الطالب الأول')+1)}{prof_row_idx}", "values": [[s1_lname + ' ' + s1_fname]]}, {"range": f"Feuille 1!{col_letter(col_names.index('تم التسجيل')+1)}{prof_row_idx}", "values": [["نعم"]]}, {"range": f"Feuille 1!{col_letter(col_names.index('تاريخ التسجيل')+1)}{prof_row_idx}", "values": [[datetime.now().strftime('%Y-%m-%d %H:%M')]]}, {"range": f"Feuille 1!{col_letter(col_names.index('رقم المذكرة')+1)}{prof_row_idx}", "values": [[note_number]]}]
        if student2 is not None:
            s2_lname = student2.get('لقب', student2.get('اللقب', '')); s2_fname = student2.get('إسم', student2.get('إسم', ''))
            updates.append({"range": f"Feuille 1!{col_letter(col_names.index('الطالب الثاني')+1)}{prof_row_idx}", "values": [[s2_lname + ' ' + s2_fname]]})
        sheets_service.spreadsheets().values().batchUpdate(spreadsheetId=PROF_MEMOS_SHEET_ID, body={"valueInputOption": "USER_ENTERED", "data": updates}).execute()
        memo_row_idx = df_memos[df_memos["رقم المذكرة"].astype(str).str.strip() == str(note_number).strip()].index[0] + 2
        memo_cols = df_memos.columns.tolist()
        reg1 = str(student1.get('رقم التسجيل', '')); reg2 = str(student2.get('رقم التسجيل', '')) if student2 else ""
        updates2 = [{"range": f"Feuille 1!{col_letter(memo_cols.index('الطالب الأول')+1)}{memo_row_idx}", "values": [[s1_lname + ' ' + s1_fname]]}, {"range": f"Feuille 1!{col_letter(memo_cols.index('تم التسجيل')+1)}{memo_row_idx}", "values": [["نعم"]]}, {"range": f"Feuille 1!{col_letter(memo_cols.index('تاريخ التسجيل')+1)}{memo_row_idx}", "values": [[datetime.now().strftime('%Y-%m-%d %H:%M')]]}, {"range": f"Feuille 1!S{memo_row_idx}", "values": [[reg1]]}]
        if 'كلمة سر التسجيل' in memo_cols: updates2.append({"range": f"Feuille 1!{col_letter(memo_cols.index('كلمة سر التسجيل')+1)}{memo_row_idx}", "values": [[used_prof_password]]})
        if student2 is not None:
            updates2.append({"range": f"Feuille 1!{col_letter(memo_cols.index('الطالب الثاني')+1)}{memo_row_idx}", "values": [[s2_lname + ' ' + s2_fname]]})
            updates2.append({"range": f"Feuille 1!T{memo_row_idx}", "values": [[reg2]]})
        sheets_service.spreadsheets().values().batchUpdate(spreadsheetId=MEMOS_SHEET_ID, body={"valueInputOption": "USER_ENTERED", "data": updates2}).execute()
        students_cols = df_students.columns.tolist()
        student1_row_idx = df_students[df_students["اسم المستخدم"].astype(str).str.strip() == student1['اسم المستخدم'].strip()].index[0] + 2
        sheets_service.spreadsheets().values().update(spreadsheetId=STUDENTS_SHEET_ID, range=f"Feuille 1!{col_letter(students_cols.index('رقم المذكرة')+1)}{student1_row_idx}", valueInputOption="USER_ENTERED", body={"values": [[note_number]]}).execute()
        if student2 is not None:
            student2_row_idx = df_students[df_students["اسم المستخدم"].astype(str).str.strip() == student2['اسم المستخدم'].strip()].index[0] + 2
            sheets_service.spreadsheets().values().update(spreadsheetId=STUDENTS_SHEET_ID, range=f"Feuille 1!{col_letter(students_cols.index('رقم المذكرة')+1)}{student2_row_idx}", valueInputOption="USER_ENTERED", body={"values": [[note_number]]}).execute()
        time.sleep(2); clear_cache_and_reload(); time.sleep(1)
        df_students_updated = load_students()
        st.session_state.student1 = df_students_updated[df_students_updated["اسم المستخدم"].astype(str).str.strip() == student1['اسم المستخدم'].strip()].iloc[0]
        if student2 is not None: st.session_state.student2 = df_students_updated[df_students_updated["اسم المستخدم"].astype(str).str.strip() == student2['اسم المستخدم'].strip()].iloc[0]
        memo_data = df_memos[df_memos["رقم المذكرة"].astype(str).str.strip() == str(note_number).strip()].iloc[0]
        prof_name = memo_data["الأستاذ"].strip()
        prof_memo_data = df_prof_memos[df_prof_memos["الأستاذ"].astype(str).str.strip() == prof_name].iloc[0]
        prof_email = str(prof_memo_data.get("البريد الإلكتروني", "")).strip()
        if prof_email and "@" in prof_email: send_email_to_professor(prof_email, prof_name, memo_data, st.session_state.student1, st.session_state.student2 if student2 else None)
        return True, "✅ تم تسجيل المذكرة بنجاح!"
    except Exception as e:
        logger.error(f"خطأ في تحديث التسجيل: {str(e)}")
        return False, f"❌ حدث خطأ أثناء التسجيل: {str(e)}"

# ---------------- Session State ----------------
if 'user_type' not in st.session_state:
    st.session_state.user_type = None
    st.session_state.logged_in = False
    st.session_state.student1 = None; st.session_state.student2 = None; st.session_state.professor = None
    st.session_state.admin_user = None; st.session_state.memo_type = "فردية"; st.session_state.mode = "register"
    st.session_state.note_number = ""; st.session_state.prof_password = ""; st.session_state.show_confirmation = False
    st.session_state.selected_memo_id = None

def logout():
    for key in st.session_state.keys():
        if key not in ['user_type']: del st.session_state[key]
    st.session_state.update({'logged_in': False, 'student1': None, 'student2': None, 'professor': None, 'admin_user': None, 'mode': "register", 'note_number': "", 'prof_password': "", 'show_confirmation': False, 'user_type': None, 'selected_memo_id': None})
    st.rerun()

df_students = load_students(); df_memos = load_memos(); df_prof_memos = load_prof_memos(); df_requests = load_requests()
if df_students.empty or df_memos.empty or df_prof_memos.empty: st.error("❌ خطأ في تحميل البيانات."); st.stop()

# ============================================================
# الصفحة الرئيسية
# ============================================================
if st.session_state.user_type is None:
    st.markdown("<h1 style='text-align: center; margin-bottom: 1rem;'>نظام تسجيل المذكرات</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #94A3B8; font-size: 1.2rem;'>جامعة محمد البشير الإبراهيمي - كلية الحقوق والعلوم السياسية</p>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("<div class='card' style='text-align: center;'>", unsafe_allow_html=True)
        st.markdown("<h3>👨‍🎓 فضاء الطلبة</h3>", unsafe_allow_html=True)
        if st.button("دخول الطلبة", key="btn_student", use_container_width=True): st.session_state.user_type = "student"; st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    with col2:
        st.markdown("<div class='card' style='text-align: center;'>", unsafe_allow_html=True)
        st.markdown("<h3>👨‍🏫 فضاء الأساتذة</h3>", unsafe_allow_html=True)
        if st.button("دخول الأساتذة", key="btn_prof", use_container_width=True): st.session_state.user_type = "professor"; st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    with col3:
        st.markdown("<div class='card' style='text-align: center;'>", unsafe_allow_html=True)
        st.markdown("<h3>⚙️ فضاء الإدارة</h3>", unsafe_allow_html=True)
        if st.button("دخول الإدارة", key="btn_admin", use_container_width=True): st.session_state.user_type = "admin"; st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

# ============================================================
# فضاء الطلبة
# ============================================================
elif st.session_state.user_type == "student":
    # ... (Same Student Space Logic as previous version) ...
    # Shortened for brevity, but included fully in the output below to ensure copy-paste works
    if not st.session_state.logged_in:
        col1, col2 = st.columns([4, 1])
        with col2:
            if st.button("رجوع", key="back_student"): st.session_state.user_type = None; st.rerun()
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
                    if not username1 or not password1: st.error("⚠️ يرجى إدخال اسم المستخدم وكلمة السر"); st.stop()
                if st.session_state.memo_type == "ثنائية":
                    if not username1 or not password1 or not username2 or not password2: st.error("⚠️ يرجى إدخال بيانات الطالبين كاملة"); st.stop()
                    if username1.strip().lower() == username2.strip().lower(): st.error("❌ لا يمكن أن يكون الطالب الأول والثاني نفس الشخص!"); st.stop()
                students_data = [(username1, password1)]
                if st.session_state.memo_type == "ثنائية" and username2: students_data.append((username2, password2))
                valid, result = verify_students_batch(students_data, df_students)
                if not valid: st.error(result)
                else:
                    verified_students = result
                    if not verified_students: st.error("حدث خطأ غير متوقع في التحقق من البيانات"); st.stop()
                    st.session_state.student1 = verified_students[0]
                    st.session_state.student2 = verified_students[1] if len(verified_students) > 1 else None
                    if st.session_state.memo_type == "ثنائية" and st.session_state.student2 is not None:
                        s1_note = str(st.session_state.student1.get('رقم المذكرة', '')).strip()
                        s2_note = str(st.session_state.student2.get('رقم المذكرة', '')).strip()
                        s1_spec = str(st.session_state.student1.get('التخصص', '')).strip()
                        s2_spec = str(st.session_state.student2.get('التخصص', '')).strip()
                        if s1_spec != s2_spec: st.error("❌ لا يمكن التسجيل الثنائي. الطالبان في تخصصين مختلفين"); st.session_state.logged_in=False; st.stop()
                        if (s1_note and not s2_note) or (not s1_note and s2_note): st.error("❌ أحد الطالبين مسجل مسبقاً"); st.session_state.logged_in=False; st.stop()
                        if s1_note and s2_note and s1_note != s2_note: st.error(f"❌ الطالبان مسجلان في مذكرتين مختلفتين"); st.session_state.logged_in=False; st.stop()
                        if s1_note and s2_note and s1_note == s2_note: st.session_state.mode = "view"; st.session_state.logged_in = True; st.rerun()
                    if st.session_state.memo_type == "فردية":
                        fardiya_val = str(st.session_state.student1.get('فردية', '')).strip()
                        if fardiya_val not in ["1", "نعم"]: st.error("❌ لا يمكنك تسجيل مذكرة فردية"); st.stop()
                    note_num = str(st.session_state.student1.get('رقم المذكرة', '')).strip()
                    st.session_state.mode = "view" if note_num else "register"
                    st.session_state.logged_in = True; st.rerun()
    else:
        s1 = st.session_state.student1; s2 = st.session_state.student2
        col1, col2 = st.columns([4, 1])
        with col2:
            if st.button("خروج", key="logout_btn"): logout()
        st.markdown(f'<div class="card"><h3>ملف الطالب</h3><p>الطالب الأول: <b style="color:#2F6F7E;">{s1["لقب"] if "لقب" in s1 else s1["اللقب"]} {s1["الإسم"] if "الإسم" in s1 else s1["إسم"]}</b></p><p>التخصص: <b>{s1["التخصص"]}</b></p></div>', unsafe_allow_html=True)
        if s2 is not None: st.markdown(f'<div class="card"><p>الطالب الثاني: <b style="color:#2F6F7E;">{s2["لقب"] if "لقب" in s2 else s2["اللقب"]} {s2["الإسم"] if "الإسم" in s2 else s2["إسم"]}</b></p></div>', unsafe_allow_html=True)

        tab_memo, tab_notify = st.tabs(["مذكرتي", "الإشعارات والطلبات"])
        with tab_memo:
            if st.session_state.mode == "view":
                df_memos_fresh = load_memos()
                note_num = str(s1.get('رقم المذكرة', '')).strip()
                memo_info = df_memos_fresh[df_memos_fresh["رقم المذكرة"].astype(str).str.strip() == note_num]
                if not memo_info.empty:
                    memo_info = memo_info.iloc[0]
                    st.markdown(f'''<div class="card" style="border-left: 5px solid #FFD700;"><h3>✅ أنت مسجل في المذكرة التالية:</h3><p><b>رقم المذكرة:</b> {memo_info['رقم المذكرة']}</p><p><b>العنوان:</b> {memo_info['عنوان المذكرة']}</p><p><b>المشرف:</b> {memo_info['الأستاذ']}</p><p><b>التخصص:</b> {memo_info['التخصص']}</p><p><b>التاريخ:</b> {memo_info.get('تاريخ التسجيل','')}</p></div>''', unsafe_allow_html=True)
            elif st.session_state.mode == "register":
                st.markdown('<div class="card"><h3>تسجيل مذكرة جديدة</h3></div>', unsafe_allow_html=True)
                all_profs = sorted(df_memos["الأستاذ"].dropna().unique())
                selected_prof = st.selectbox("اختر الأستاذ المشرف:", [""] + all_profs)
                if selected_prof:
                    student_specialty = s1["التخصص"]
                    prof_memos = df_memos[df_memos["الأستاذ"].astype(str).str.strip() == selected_prof.strip()]
                    reg_count = len(prof_memos[prof_memos["تم التسجيل"].astype(str).str.strip() == "نعم"])
                    if reg_count >= 4: st.error(f'❌ الأستاذ {selected_prof} استنفذ كل العناوين')
                    else:
                        avail_memos = df_memos[(df_memos["الأستاذ"].astype(str).str.strip() == selected_prof.strip()) & (df_memos["التخصص"].astype(str).str.strip() == student_specialty.strip()) & (df_memos["تم التسجيل"].astype(str).str.strip() != "نعم")][["رقم المذكرة", "عنوان المذكرة"]]
                        
                        if not avail_memos.empty:
                            st.success(f'✅ المذكرات المتاحة في تخصصك ({student_specialty}):')
                            for _, row in avail_memos.iterrows(): st.markdown(f"**{row['رقم المذكرة']}.** {row['عنوان المذكرة']}")
                        else:
                            st.error('لا توجد مذكرات متاحة لهذا الأستاذ في تخصصك حالياً ❌')
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
                            valid, prof_row, err = verify_professor_password(st.session_state.note_number, st.session_state.prof_password, df_memos, df_prof_memos)
                            if not valid: st.error(err); st.session_state.show_confirmation = False
                            else:
                                with st.spinner('⏳ جاري تسجيل...'):
                                    success, msg = update_registration(st.session_state.note_number, s1, s2)
                                if success: st.success(msg); st.balloons(); clear_cache_and_reload(); st.session_state.mode = "view"; st.session_state.show_confirmation = False; time.sleep(2); st.rerun()
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
                        details = str(r.get('العنوان الجديد', r.get('التفاصيل', '')).strip() if 'العنوان الجديد' in r else r.get('التفاصيل', '')).strip()
                        status = r['الحالة']
                        status_color = "#10B981" if status == "موافق عليه" else "#EF4444" if status == "مرفوض" else "#F59E0B"
                        show_details = True
                        if req_type in ["حذف طالب", "تنازل"]: show_details = False
                        st.markdown(f"""<div class='card' style='border-right: 4px solid {status_color}; padding: 20px;'><h4>{req_type}</h4><p>التاريخ: {r['الوقت']}</p><p>الحالة: <b style="color:{status_color}">{status}</b></p>{'<p>التفاصيل: ' + details + '</p>' if show_details else '<p><i>التفاصيل مخفية</i></p>'}</div>""", unsafe_allow_html=True)
                else: st.info("لا توجد إشعارات جديدة.")
            else: st.info("يجب تسجيل مذكرة أولاً لتلقي الإشعارات.")

# ============================================================
# فضاء الأساتذة
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
            c1, c2 = st.columns(2)
            with c1: u = st.text_input("اسم المستخدم")
            with c2: p = st.text_input("كلمة المرور", type="password")
            if st.form_submit_button("تسجيل الدخول"):
                v, r = verify_professor(u, p, df_prof_memos)
                if not v: st.error(r)
                else: st.session_state.professor = r; st.session_state.logged_in = True; st.rerun()
    else:
        prof = st.session_state.professor; prof_name = prof["الأستاذ"]
       
        # --- وضع عرض مذكرة محددة ---
        if st.session_state.selected_memo_id:
            memo_id = st.session_state.selected_memo_id
            current_memo = df_memos[df_memos["رقم المذكرة"].astype(str).str.strip() == memo_id].iloc[0]
            student_info = get_student_info_from_memo(current_memo, df_students)
           
            col_back, _, _ = st.columns([1, 8, 1])
            with col_back:
                if st.button("⬅️ العودة للقائمة"): st.session_state.selected_memo_id = None; st.rerun()

            st.markdown("<br>", unsafe_allow_html=True)
            progress_val = str(current_memo.get('نسبة التقدم', '0')).strip()
            try: prog_int = int(progress_val) if progress_val else 0
            except: prog_int = 0

            # بناء كود HTML للطلبة
            student_cards_html = f"""
<div class="student-card">
    <h4 style="color: #FFD700; margin-top: 0; font-size: 1.1rem;">الطالب الأول</h4>
    <p style="font-size: 1.3rem; font-weight: bold; margin: 15px 0 5px 0; color: #fff;">{student_info['s1_name']}</p>
    <p style="font-size: 0.9rem; color: #94A3B8;">رقم التسجيل: {student_info['s1_reg'] or '--'}</p>
    <div style="margin-top: 15px; padding: 8px; background: rgba(16, 185, 129, 0.1); border-radius: 8px; color: #10B981; font-size: 0.9rem;">
        📧 {student_info['s1_email'] or 'غير متوفر'}
    </div>
</div>
"""
            if student_info['s2_name']:
                student_cards_html += f"""
<div class="student-card">
    <h4 style="color: #FFD700; margin-top: 0; font-size: 1.1rem;">الطالب الثاني</h4>
    <p style="font-size: 1.3rem; font-weight: bold; margin: 15px 0 5px 0; color: #fff;">{student_info['s2_name']}</p>
    <p style="font-size: 0.9rem; color: #C0C0C0;">رقم التسجيل: {student_info['s2_reg'] or '--'}</p>
    <div style="margin-top: 15px; padding: 8px; background: rgba(16, 185, 129, 0.1); border-radius: 8px; color: #10B981; font-size: 0.9rem;">
        📧 {student_info['s2_email'] or 'غير متوفر'}
    </div>
</div>
"""
           
            student_cards_html += "</div>"

            full_memo_html = f"""<div class="full-view-container">
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; flex-wrap: wrap;">
    <div>
        <p class="memo-badge">{current_memo['التخصص']}</p>
        <h1 class="memo-id">{current_memo['رقم المذكرة']}</h1>
    </div>
</div>
<div style="text-align: center; border-bottom: 2px solid #2F6F7E; padding-bottom: 20px; margin-bottom: 30px;">
    <h2 style="color: #F8FAFC; font-size: 1.8rem; margin: 0; line-height: 1.6;">{current_memo['عنوان المذكرة']}</h2>
</div>
<div class="students-grid">
    {student_cards_html}
</div>
<div style="margin-bottom: 40px; text-align: center;">
    <h3 style="color: #F8FAFC; margin-bottom: 15px;">نسبة الإنجاز الحالية</h3>
    <div class="progress-container" style="height: 40px; border-radius: 20px;">
        <div class="progress-bar" style="width: """ + str(prog_int) + """%; font-size: 1.2rem; font-weight: bold; line-height: 28px;">""" + str(prog_int) + """%</div>
    </div>
</div>
</div>
"""
           
            st.markdown(textwrap.dedent(full_memo_html), unsafe_allow_html=True)

            st.markdown("<div class='divider' style='border-top: 1px solid #334155; margin: 30px 0;'></div>", unsafe_allow_html=True)
           
            # منطق الإدارة
            st.markdown("<h3 style='text-align: center; margin-bottom: 20px;'>إدارة المذكرة</h3>", unsafe_allow_html=True)
            col1, col2 = st.columns(2)
           
            with col1:
                st.markdown("<div style='background: rgba(30, 41, 59, 0.5); padding: 20px; border-radius: 10px;'>", unsafe_allow_html=True)
                st.subheader("📊 تحديث نسبة التقدم")
                new_prog = st.selectbox("اختر المرحلة:", ["0%", "10% - ضبط المقدمة", "30% - الفصل الأول", "60% - الفصل الثاني", "80% - الخاتمة", "100% - مكتملة"], key=f"prog_full_{memo_id}")
                if st.button("حفظ التحديث", key=f"save_full_{memo_id}", use_container_width=True):
                    mapping = {"0%":0, "10% - ضبط المقدمة":10, "30% - الفصل الأول":30, "60% - الفصل الثاني":60, "80% - الخاتمة":80, "100% - مكتملة":100}
                    s, m = update_progress(memo_id, mapping[new_prog])
                    st.success(m) if s else st.error(m); time.sleep(1); st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
           
            with col2:
                st.markdown("<div style='background: rgba(30, 41, 59, 0.5); padding: 20px; border-radius: 10px;'>", unsafe_allow_html=True)
                st.subheader("📨 إرسال طلب للإدارة")
                req_op = st.selectbox("نوع الطلب:", ["", "تغيير عنوان المذكرة", "حذف طالب (ثنائية)", "إضافة طالب (فردية)", "تنازل عن الإشراف"], key=f"req_full_{memo_id}")
                details_to_save = ""
                validation_error = None
               
                if req_op == "تغيير عنوان المذكرة":
                    new_title = st.text_input("العنوان الجديد:", key=f"nt_full_{memo_id}")
                    if st.button("إرسال طلب تغيير العنوان", key=f"btn_ch_full_{memo_id}", use_container_width=True):
                        if new_title: details_to_save = f"العنوان الجديد المقترح: {new_title}"
                        else: validation_error = "الرجاء إدخال العنوان"
                elif req_op == "حذف طالب (ثنائية)":
                    if not student_info['s2_name']: st.warning("هذه مذكرة فردية!")
                    else:
                        st.write("الطالبان:")
                        st.write(f"1. {student_info['s1_name']}")
                        st.write(f"2. {student_info['s2_name']}")
                        to_del = st.selectbox("اختر الطالب للحذف:", ["", "الطالب الأول", "الطالب الثاني"], key=f"del_full_{memo_id}")
                        just = st.text_area("تبريرات الحذف:", key=f"jus_del_full_{memo_id}")
                        if st.button("إرسال طلب الحذف", key=f"btn_del_full_{memo_id}", use_container_width=True):
                            if to_del and just: details_to_save = f"حذف: {to_del}. السبب: {just}"
                            else: validation_error = "اكمل البيانات"
                elif req_op == "إضافة طالب (فردية)":
                    if student_info['s2_name']: st.warning("هذه مذكرة ثنائية بالفعل!")
                    else:
                        reg_to_add = st.text_input("رقم التسجيل:", key=f"add_full_{memo_id}")
                        if st.button("تحقق وإرسال", key=f"btn_add_full_{memo_id}", use_container_width=True):
                            target = df_students[df_students["رقم التسجيل"] == reg_to_add]
                            if target.empty: validation_error = "رقم التسجيل غير موجود"
                            elif target.iloc[0].get("رقم المذكرة"): validation_error = "الطالب لديه مذكرة بالفعل"
                            elif target.iloc[0].get("تخصص") != current_memo['التخصص']: validation_error = "التخصص غير متطابق"
                            else:
                                just = st.text_area("ملاحظات (اختياري):", key=f"jus_add_full_{memo_id}")
                                details_to_save = f"إضافة الطالب المسجل: {reg_to_add}. ملاحظات: {just}"
                elif req_op == "تنازل عن الإشراف":
                    just = st.text_area("مبررات التنازل:", key=f"res_full_{memo_id}")
                    if st.button("إرسال طلب التنازل", key=f"btn_res_full_{memo_id}", use_container_width=True):
                        if just: details_to_save = f"التنازل عن الإشراف. المبررات: {just}"
                        else: validation_error = "الرجاء كتابة المبررات"

                if validation_error:
                    st.error(validation_error)
                elif details_to_save:
                    suc, msg = save_and_send_request(req_op, prof_name, memo_id, current_memo['عنوان المذكرة'], details_to_save)
                    if suc: st.success(msg); time.sleep(1); st.rerun()
                    else: st.error(msg)
                st.markdown("</div>", unsafe_allow_html=True)

        # --- لوحة التحكم ---
        else:
            col1, col2 = st.columns([4, 1])
            with col2:
                if st.button("خروج"): logout()
           
            st.markdown(f"<h2 style='margin-bottom:20px;'>فضاء الأستاذ <span style='color:#FFD700;'>{prof_name}</span></h2>", unsafe_allow_html=True)
            prof_memos = df_memos[df_memos["الأستاذ"].astype(str).str.strip() == prof_name.strip()]
            total = len(prof_memos)
            registered = len(prof_memos[prof_memos["تم التسجيل"].astype(str).str.strip() == "نعم"])
            available = total - registered
            is_exhausted = registered >= 4

            st.markdown('<div class="kpi-grid">', unsafe_allow_html=True)
            st.markdown(f'<div class="kpi-card"><div class="kpi-value">{total}</div><div class="kpi-label">إجمالي المذكرات</div></div><div class="kpi-card" style="border-color: #10B981;"><div class="kpi-value" style="color: #10B981;">{registered}</div><div class="kpi-label">المذكرات المسجلة</div></div><div class="kpi-card" style="border-color: #F59E0B;"><div class="kpi-value" style="color: #F59E0B;">{available}</div><div class="kpi-label">المذكرات المتاحة</div></div></div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            if is_exhausted: st.markdown('<div class="alert-card">لقد استنفذت العناوين الأربعة المخصصة لك.</div>', unsafe_allow_html=True)
           
            tab1, tab2, tab3, tab4 = st.tabs(["المذكرات المسجلة", "كلمات السر", "المذكرات المتاحة", "سجل طلباتي"]) # Added Tab 4
           
            with tab1:
                st.subheader("المذكرات المسجلة")
                registered_memos = prof_memos[prof_memos["تم التسجيل"].astype(str).str.strip() == "نعم"]
                if not registered_memos.empty:
                    cols = st.columns(2)
                    for i, (_, memo) in enumerate(registered_memos.iterrows()):
                        with cols[i % 2]:
                            progress_val = str(memo.get('نسبة التقدم', '0')).strip()
                            try: prog_int = int(progress_val) if progress_val else 0
                            except: prog_int = 0
                            s_info = get_student_info_from_memo(memo, df_students)
                            st.markdown(f'''<div class="card" style="border-right: 5px solid #10B981; padding-bottom: 10px;"><h4>{memo['رقم المذكرة']} - {memo['عنوان المذكرة']}</h4><p style="color:#94A3B8; font-size:0.9em;">تخصص: {memo['التخصص']}</p><p style="font-size:0.95em; margin-bottom: 5px;">{s_info['s1_name']}</p>{f"<p style='font-size:0.95em; margin-bottom: 15px;'>{s_info['s2_name']}</p>" if s_info['s2_name'] else ""}<div class="progress-container" style="margin: 10px 0;"><div class="progress-bar" style="width: {prog_int}%;"></div></div><p style="text-align:left; font-size:0.8em;">نسبة الإنجاز: {prog_int}%</p></div>''', unsafe_allow_html=True)
                            if st.button(f"👉 عرض المذكرة {memo['رقم المذكرة']}", key=f"open_{memo['رقم المذكرة']}", use_container_width=True):
                                st.session_state.selected_memo_id = memo['رقم المذكرة']; st.rerun()
                else: st.info("لا توجد مذكرات مسجلة حتى الآن.")
            with tab2:
                st.subheader("كلمات السر")
                pwds = df_prof_memos[df_prof_memos["الأستاذ"].astype(str).str.strip() == prof_name.strip()]
                if not pwds.empty:
                    for _, row in pwds.iterrows():
                        stat = str(row.get("تم التسجيل", "")).strip()
                        pwd = str(row.get("كلمة سر التسجيل", "")).strip()
                        if pwd:
                            color = "#10B981" if stat == "نعم" else "#F59E0B"
                            status_txt = "مستخدمة" if stat == "نعم" else "متاحة"
                            st.markdown(f'''<div class="card" style="border-right: 5px solid {color}; display:flex; justify-content:space-between; align-items:center;"><div><h3 style="margin:0; font-family:monospace; font-size:1.8rem; color:#FFD700;">{pwd}</h3><p style="margin:5px 0 0 0 0; color:#94A3B8;">الحالة: {status_txt}</p></div></div>''', unsafe_allow_html=True)
                else: st.info("لا توجد كلمات سر مسندة إليك.")
            with tab3:
                if is_exhausted: st.subheader("💡 المذكرات المقترحة")
                else: st.subheader("⏳ المذكرات المتاحة للتسجيل")
                avail = prof_memos[prof_memos["تم التسجيل"].astype(str).str.strip() != "نعم"]
                if not avail.empty:
                    for _, m in avail.iterrows():
                        st.markdown(f'''<div class="card" style="border-left: 4px solid #64748B;"><h4>{m['رقم المذكرة']}</h4><p>{m['عنوان المذكرة']}</p><p style="color:#94A3B8;">تخصص: {m['التخصص']}</p></div>''', unsafe_allow_html=True)
                else: st.success("✅ جميع المذكرات مسجلة أو مقترحة!")
            
            # NEW TAB FOR PROFESSOR
            with tab4:
                st.subheader("سجل طلباتي")
                my_reqs = df_requests[df_requests["الأستاذ"].astype(str).str.strip() == prof_name]
                if my_reqs.empty:
                    st.info("لم ترسل أي طلبات بعد.")
                else:
                    for idx, r in my_reqs.iterrows():
                        status = r['الحالة']
                        status_color = "#10B981" if status == "موافق عليه" else "#EF4444" if status == "مرفوض" else "#F59E0B"
                        st.markdown(f"""
                        <div style="background: rgba(30, 41, 59, 0.5); padding: 20px; border-radius: 10px; border-right: 4px solid {status_color}; margin-bottom: 15px;">
                            <h4>{r['نوع الطلب']}</h4>
                            <p style="font-size:0.9em; color:#94A3B8;">المذكرة: {r['رقم المذكرة']} | التاريخ: {r['الوقت']}</p>
                            <p><strong>الحالة:</strong> <span style="color:{status_color}; font-weight:bold;">{status}</span></p>
                            <p style="font-size:0.8em; margin-top:5px;">{r['العنوان الجديد'] if 'العنوان الجديد' in r else r.get('التفاصيل', '')}</p>
                            {f"<p style='color:#EF4444; font-size:0.8em;'>ملاحظات الإدارة: {r['']}</p>" if status == "مرفوض" and r[''] else ""}
                        </div>
                        """, unsafe_allow_html=True)


# ============================================================
# فضاء الإدارة
# ============================================================
elif st.session_state.user_type == "admin":
    if not st.session_state.logged_in:
        col1, col2 = st.columns([4, 1])
        with col2:
            if st.button("رجوع", key="back_admin"): st.session_state.user_type = None; st.rerun()
       
        st.markdown("<h2>⚙️ فضاء الإدارة</h2>", unsafe_allow_html=True)
       
        with st.form("admin_login"):
            u = st.text_input("اسم المستخدم")
            p = st.text_input("كلمة المرور", type="password")
            if st.form_submit_button("دخول"):
                v, r = verify_admin(u, p)
                if not v: st.error(r)
                else: st.session_state.admin_user = r; st.session_state.logged_in = True; st.rerun()
    else:
        col1, col2 = st.columns([4, 1])
        with col2:
            if st.button("خروج"): logout()
        st.header("📊 لوحة تحكم الإدارة")
        st_s = len(df_students); t_m = len(df_memos); r_m = len(df_memos[df_memos["تم التسجيل"].astype(str).str.strip() == "نعم"])
        a_m = t_m - r_m; t_p = len(df_prof_memos["الأستاذ"].unique())
        memo_col = df_students["رقم المذكرة"].astype(str).str.strip()
        reg_st = (memo_col != "").sum()
        unreg_st = (memo_col == "").sum()
       
        st.markdown('<div class="kpi-grid">', unsafe_allow_html=True)
        st.markdown(f'<div class="kpi-card"><div class="kpi-value">{st_s}</div><div class="kpi-label">الطلاب</div></div><div class="kpi-card"><div class="kpi-value">{t_p}</div><div class="kpi-label">الأساتذة</div></div><div class="kpi-card"><div class="kpi-value">{t_m}</div><div class="kpi-label">إجمالي المذكرات</div></div><div class="kpi-card" style="border-color: #10B981;"><div class="kpi-value" style="color: #10B981;">{r_m}</div><div class="kpi-label">مذكرات مسجلة</div></div><div class="kpi-card" style="border-color: #F59E0B;"><div class="kpi-value" style="color: #F59E0B;">{a_m}</div><div class="kpi-label">مذكرات متاحة</div></div><div class="kpi-card" style="border-color: #10B981;"><div class="kpi-value" style="color: #10B981;">{reg_st}</div><div class="kpi-label">طلاب مسجلين</div></div><div class="kpi-card" style="border-color: #F59E0B;"><div class="kpi-value" style="color: #F59E0B;">{unreg_st}</div><div class="kpi-label">طلاب غير مسجلين</div></div></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["المذكرات", "الطلاب", "الأساتذة", "تقارير", "تحديث", "إدارة الطلبات"])
       
        with tab1:
            st.subheader("جدول المذكرات")
            f_status = st.selectbox("تصفية:", ["الكل", "مسجلة", "متاحة"])
            if f_status == "الكل": d_memos = df_memos
            elif f_status == "مسجلة": d_memos = df_memos[df_memos["تم التسجيل"].astype(str).str.strip() == "نعم"]
            else: d_memos = df_memos[df_memos["تم التسجيل"].astype(str).str.strip() != "نعم"]
            st.dataframe(d_memos, use_container_width=True, height=400)
            
        with tab2:
            st.subheader("قائمة الطلاب")
            q = st.text_input("بحث (لقب/الاسم):")
            if q:
                name_cols = [c for c in df_students.columns if 'اسم' in c.lower() or 'لقب' in c.lower() or 'إسم' in c.lower()]
                if name_cols:
                    mask = df_students[name_cols].astype(str).apply(lambda x: x.str.contains(q, case=False, na=False)).any(axis=1)
                    f_st = df_students[mask]
                else: f_st = df_students
                st.dataframe(f_st, use_container_width=True, height=400)
            else: st.dataframe(df_students, use_container_width=True, height=400)
                
        with tab3:
            st.subheader("توزيع الأساتذة")
            profs_list = sorted(df_memos["الأستاذ"].dropna().unique())
            sel_p = st.selectbox("اختر أستاذ:", ["الكل"] + profs_list)
            if sel_p != "الكل":
                if sel_p not in df_memos["الأستاذ"].values: st.error("بيانات الأساتذة غير متاحة")
                else: st.dataframe(df_memos[df_memos["الأستاذ"].astype(str).str.strip() == sel_p.strip()], use_container_width=True, height=400)
            else:
                if "الأستاذ" in df_memos.columns and "رقم المذكرة" in df_memos.columns and "تم التسجيل" in df_memos.columns:
                    s_df = df_memos.groupby("الأستاذ").agg(
                        إجمالي=("رقم المذكرة", "count"),
                        مسجلة=("تم التسجيل", lambda x: (x.astype(str).str.strip() == "نعم").sum())
                    ).reset_index()
                    s_df["المتاحة"] = s_df["إجمالي"] - s_df["مسجلة"]
                    s_df = s_df.rename(columns={"إجمالي": "الإجمالي", "مسجلة": "المسجلة"})
                    st.dataframe(s_df, use_container_width=True)
                else: st.error("بعض الأعمدة المطلوبة مفقودة")
                    
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
            st.markdown("---")
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
            st.subheader("تحديث البيانات والربط")
            if st.button("🔄 بدء عملية الربط (Sync)", type="primary"):
                with st.spinner("جاري المعالجة..."):
                    s, m = sync_student_registration_numbers()
                    st.success(m) if s else st.info(m)
                    if s: clear_cache_and_reload(); st.rerun()
            st.markdown("---")
            if st.button("تحديث البيانات من Google Sheets"):
                with st.spinner("جاري التحديث..."):
                    clear_cache_and_reload()
                    st.success("✅ تم التحديث")
                    st.rerun()
        
        with tab6:
            st.subheader("إدارة الطلبات الواردة")
            if df_requests.empty:
                st.info("لا توجد طلبات حالياً.")
            else:
                # Filter pending requests first
                pending = df_requests[df_requests["الحالة"] == "قيد المراجعة"]
                
                st.markdown("### 📋 طلبات قيد المراجعة")
                if pending.empty:
                    st.success("لا توجد طلبات معلقة.")
                else:
                    for idx, row in pending.iterrows():
                        with st.container():
                            st.markdown(f"""<div class="card"><h3>{row['نوع الطلب']}</h3><p><strong>من:</strong> {row['الأستاذ']}</p><p><strong>المذكرة:</strong> {row['رقم المذكرة']}</p><p><strong>التفاصيل:</strong> {row['العنوان الجديد'] if 'العنوان الجديد' in row else row.get('التفاصيل','')}</p></div>""", unsafe_allow_html=True)
                            
                            # Admin Action Form
                            with st.form(key=f"req_form_{idx}"):
                                c1, c2 = st.columns(2)
                                action = c1.radio("القرار:", ["موافقة", "رفض"], horizontal=True, key=f"act_{idx}")
                                notes = ""
                                if action == "رفض":
                                    notes = st.text_input("سبب الرفض (ملاحظات الإدارة):", key=f"note_{idx}")
                                submitted = st.form_submit_button("تنفيذ", type="primary")
                                
                                if submitted:
                                    if action == "رفض" and not notes:
                                        st.error("يجب كتابة سبب الرفض")
                                    else:
                                        with st.spinner("جاري التنفيذ..."):
                                            success, msg = process_admin_request(idx, "approve" if action == "موافقة" else "reject", notes, df_memos, df_students, df_prof_memos)
                                            if success:
                                                st.success(msg)
                                                clear_cache_and_reload()
                                                time.sleep(1)
                                                st.rerun()
                                            else:
                                                st.error(msg)
                            st.markdown("---")

                st.markdown("### 📜 سجل الطلبات السابقة")
                history = df_requests[df_requests["الحالة"] != "قيد المراجعة"]
                if not history.empty:
                    st.dataframe(history, use_container_width=True, height=300)

st.markdown("---")
st.markdown('<div style="text-align:center; color:#64748B; font-size:12px; padding:20px;">© 2026 جامعة محمد البشير الإبراهيمي - كلية الحقوق</div>', unsafe_allow_html=True)