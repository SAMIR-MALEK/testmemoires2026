import streamlit as st
from datetime import datetime
import pandas as pd
# تم محاكاة تعليق المتغيرات لمنع توقف التطبيق في حالات عدم إعداداتك (للتشغيل، قم بتعليق المتغيرات الفارغة بالكامل)

# محاكاة Google Sheets (استبدل القيم الحقي ببيانات فارغة أو مفاتحة إذا لم توجد اتصالات معينة)
# قم بتعديل البيانات الحقيق (st.secrets["service_account"]) هنا
# وإلاحظظ أن المتغيرات الأساسية التالية تعمل بشكل صحيح

class Credentials:
    def __init__(self):
        self.scopes = ['https://www.googleapis.com/auth/spreadsheets']
        self.info = {}
    
    def to_dict(self):
        return {
            "username": "", "password": ""
        }

credentials = Credentials()

class GoogleSheetsHelper:
    def __init__(self):
        self.service = None

    def load_data(self, spreadsheet_id, range_str):
        try:
            if not credentials.to_dict()["username"]:
                print("⚠️ لا توجد بيانات صحيحة للاتصال بالبريد")
                return pd.DataFrame()
            
            credentials_obj = Credentials()
            credentials_obj.to_dict()
            service = build('sheets', 'v4', credentials=credentials_obj)
            
            result = service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=range_str).execute()
            values = result.get('values', [])
            if not values: return pd.DataFrame()
            df = pd.DataFrame(values[1:], columns=values[0])
            return df
        except Exception as e:
            print(f"خطأ في تحميل البيانات: {str(e)}")
            return pd.DataFrame()

sheets_helper = GoogleSheetsHelper()

# المتغيرات الأساسية (استبدلها ببياناتك الحقيق)
# ADMIN_CREDENTIALS = {"admin": "admin2026", "dsp": "dsp@2026"}
EMAIL_SENDER = "domaine.dsp@univ-bba.dz"
EMAIL_PASSWORD = "oevruyiztgikwzah"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465 # تغيير المنفذ إلى منفذ 587 ليتوافق مع معظم خوادم الجامعة
ADMIN_EMAIL = "domaine.dsp@univ-bba.dz"

# محاكاة البيانات للعمل (لتجعل الكود يعمل خارج بيئة الجامعة)
# df_students = pd.DataFrame() # قم بملء بيانات الطلاب هنا
# df_memos = pd.DataFrame() # قم بملء بيانات المذكرات هنا
# df_prof_memos = pd.DataFrame() # قم بملء بيانات مذكرات الأساتذة هنا

# دالة مساعدة للحروف الأعمدة (لمنع الأخطاء المتعلقات)
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
    if len(note_number) > 20: return False, "⚠️ رقم المذنقرة غير صالح"
    return True, note_number

# ---------------- إعدادات الـ CSS (تصميم احترافي) ----------------
st.markdown("""
<!-- استدعاء خط احترافي -->
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;900&display=swap" rel="stylesheet">

<style>
html, body, [class*="css"] { 
    font-family: 'Cairo', sans-serif !important; direction: rtl; text-align: right; 
}

/* الخلفية الأساسية */
.main { background-color: #0F172A; color: #ffffff; }
.block-container { padding: 2rem; background-color: #1E293B; border-radius: 16px; margin:auto;}

/* النصوص والعناوين */
h1, h2, h3, h4 { font-weight: 700; margin-bottom: 1rem; color: #F8FAFC; }
label, p, span { color: #E2E8F0; }
.stTextInput label, .stSelectbox label { color: #F8FAFC !important; font-weight: 600; }

/* الأزرار - تصميم موحد (أزرق للجميع) */
.stButton>button,
button[kind="primary"],
button[kind="secondary"],
div[data-testid="stFormSubmitButton"] button {
    background-color: #2F6F7E !important;   /* خلفية زرقاء للجميع */
    color: #ffffff !important;              /* كتابة بيضاء للجميع */
    font-size: 16px;
    font-weight: 600;
    padding: 12px 28px;
    border: none !important;                /* بدون حدود */
    border-radius: 12px !important;        /* تدوير الزوايا */
    cursor: pointer;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2); /* ظل خفيف أكبر */
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    width: 100%;
    text-align: center;
    display: flex; justify-content: center; align-items: center;
    gap: 10px;
}

/* تأثير عند مرور الماوس */
.stButton>button:hover,
button[kind="primary"]:hover,
button[kind="secondary"]:hover,
div[data-testid="stFormSubmitButton"] button:hover {
    background-color: #285E6B !important;   /* لون أغمق عند المرور */
    transform: translateY(-2px); /* حركة خفيفة للأعلى */
    box-shadow: 0 6px 16px rgba(0, 0, 0, 0.3);
}

/* البطاقات الاحترافية (Glassmorphism) */
.card { 
    background: rgba(30, 41, 59, 0.95);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 20px; padding: 25px; margin: 15px 0; 
    box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.2); 
    border-top: 3px solid #2F6F7E;
}
.card:hover {
    transform: translateY(-2px);
    box-shadow: 0 30px 40px -5px rgba(0, 0, 0, 0.4);
    border-color: rgba(255, 255, 255, 0.2);
}

/* بطاقات الإحصائيات */
.kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 1.5rem; margin-bottom: 2.5rem; }
.kpi-card {
    background: linear-gradient(145deg, #1E293B, #0F172A);
    border: 1px solid rgba(255, 255, 255, 0.05); border-radius: 16px; padding: 2.5rem 1rem;
    text-align: center; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
    position: relative; overflow: hidden;
    transition: transform 0.3s ease;
}
.kpi-card:hover { transform: translateY(-3px); }

.kpi-card::before {
    content: ""; position: absolute; top: 0; left: 0; right: 0; height: 5px;
    background: linear-gradient(90deg, #2F6F7E, #FFD700);
    opacity: 0.9;
}
.kpi-value { font-size: 3.5rem; font-weight: 900; color: #FFD700; margin: 15px 0; line-height: 1.2; text-shadow: 0 2px 4px rgba(0,0,0,0.5); }
.kpi-label { font-size: 1.2rem; color: #94A3B8; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; }

/* التنبيهات */
.alert-card {
    background: linear-gradient(90deg, #8B4513 0%, #A0522D 100%);
    border: 1px solid #CD853F; color: white; padding: 25px; border-radius: 16px;
    box-shadow: 0 15px 25px -5px rgba(139, 69, 19, 0.4);
    text-align: center; font-size: 16px; font-weight: bold;
}

/* شريط التقدم */
.progress-container { background-color: #0F172A; border-radius: 99px; padding: 4px; margin: 15px 0; overflow: hidden; box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.3); }
.progress-bar {
    height: 28px; border-radius: 99px;
    background: linear-gradient(90deg, #2F6F7E 0%, #285E6B 50%, #FFD700 100%);
    box-shadow: 0 0 15px rgba(47, 111, 126, 0.5);
    transition: width 1s cubic-bezier(0.4, 0, 0.2, 1);
}

/* الجداول */
.stDataFrame { border-radius: 16px; overflow: hidden; border: 1px solid rgba(255,255, 255, 0.1); background: #1E293B; }
.stDataFrame th { background-color: #0F172A; color: #FFD700; font-weight: bold; font-size: 16px; }
.stDataFrame td { color: #F8FAFC; font-size: 14px; }

/* التبويبات */
.stTabs [data-baseweb="tab-list"] { gap: 1.5rem; padding-bottom: 10px; }
.stTabs [data-baseweb="tab"] { 
    background: rgba(255, 255, 255, 0.05); color: #94A3B8; 
    font-weight: 600; padding: 12px 24px; border-radius: 10px; border: 1px solid transparent;
}
.stTabs [data-baseweb="tab"]:hover { background: rgba(255, 255, 255, 0.1); color: white; }
.stTabs [aria-selected="true"] { 
    background: rgba(47, 111, 126, 0.2); color: #FFD700; border: 1px solid #2F6F7E; font-weight: bold; box-shadow: 0 0 15px rgba(47, 111, 126, 0.2);
}
</style>
""", unsafe_allow_html=True)


# ---------------- دالة التسجيل (المن الكود الأصلي للعرض التقدم) ----------------
def update_progress_real(memo_number, progress_value):
    try:
        # محاكاة التحميل (في الواقع ستحمل من جوجل شيت)
        # df_memos = load_memos() 
        
        # محاكاة التحديث
        # sheets_service.spreadsheets().values().update(...) .execute()
        print(f"محاكاة: تم تحديث التقدم للمذكرة {memo_number} إلى {progress_value}%")
        return True, "✅ تم تحديث نسبة التقدم بنجاح"
    except Exception as e:
        print(f"محاكاة: خطأ في تحديث نسبة التقدم: {str(e)}")
        return False, f"Error: {str(e)}"

def get_student_by_name(full_name):
    try:
        # محاكاة البحث في جدول الطلاب (في الواقع ستحميل من جوجل شيت)
        # df_students = load_students()
        # محاكاة منطق البحث - تأكد أن 'لقب' و 'الإسم' أعمدة صحيحة
        return {}
        # return None
    except:
        return {}

# ---------------- دالة البريد - الكود النظيف ---------------
def send_email_to_professor_real(prof_email, prof_name, memo_info, student1, student2=None):
    try:
        student2_info = f"<p><strong>Student 2:</strong> {student2['اللقب']} {student2['الإسم']}</p>" if student2 else ""
        email_body = f"""
<html dir="rtl"><body style="font-family:sans-serif; padding:20px;">
    <div style="background:#fff; padding:30px; border-radius:15px; max-width:600px; margin:auto; color:#333;">
        <h2 style="background:#2F6F7E; color:white; padding:20px; border-radius:8px; text-align:center;">New Memo Registration</h2>
        <p>Dear Professor <strong>{prof_name}</strong>,</p>
        <div style="background:#f8f9fa; padding:15px; border-right:4px solid #2F6F7E; margin:15px 0;">
            <p><strong>Memo No:</strong> {memo_info['رقم المذكرة']}</p>
            <p><strong>Topic:</strong> {memo_info['عنوان المذكرة']}</p>
            <p><strong>Student 1:</strong> {student1['اللقب']} {student1['الإسم']}</p>
            {student2_info}
        </div>
    </div>
</body></html>"""
        msg = MIMEMultipart('alternative')
        msg['From'], msg['To'], msg['Subject'] = EMAIL_SENDER, prof_email, f"Registration - {memo_info['رقم المذكرة']}"
        msg.attach(MIMEText(email_body, 'html', 'utf-8'))
        
        print(f"محاكاة: جاري إرسال بريد إلى {prof_email}")
        # محاكاة SMTP ...
        return True, "Success"
    except Exception as e:
        print(f"محاكاة: خطأ في البريد: {str(e)}")
        return False, "Error in Email"

# ---------------- دالة التسجيل (المن الكود الأصلي للتجنب الأخطاء المتعلقات ----------------
def update_registration_real(note_number, student1, student2=None):
    try:
        # محاكاة التحميل والتحديث
        # df_memos = load_memos(); df_prof_memos = load_prof_memos(); df_students = load_students()
        prof_name = df_memos[df_memos["رقم المذكرة"].astype(str).str.strip() == str(note_number).strip()]["الأستاذ"].iloc[0].strip()
        used_prof_password = st.session_state.prof_password.strip()
        
        prof_row_idx = df_prof_memos[
            (df_prof_memos["الأستاذ"].astype(str).str.strip() == prof_name) &
            (df_prof_memos["كلمة سر التسجيل"].astype(str).str.strip() == used_prof_password)
        ].index[0] + 2
        col_names = df_prof_memos.columns.tolist()
        
        updates = [
            {"range": f"Feuille 1!{col_letter(col_names.index('الطالب الأول')+1)}{prof_row_idx}", "values": [[student1['اللقب'] + ' ' + student1['الإسم']]]},
            {"range": f"Feuille 1!{col_letter(col_names.index('تم التسجيل')+1)}{prof_row_idx}", "values": [["نعم"]]},
            {"range": f"Feuille 1!{col_letter(col_names.index('تاريخ التسجيل')+1)}{prof_row_idx}", "values": [[datetime.now().strftime('%Y-%m-%d %H:%M')]]},
            {"range": f"Feuille 1!{col_letter(col_names.index('رقم المذكرة')+1)}{prof_row_idx}", "values": [[note_number]]}
        ]
        if student2 is not None:
            updates.append({"range": f"Feuille 1!{col_letter(col_names.index('الطالب الثاني')+1)}{prof_row_idx}", "values": [[student2['اللقب'] + ' ' + student2['الإسم']]]})
        
        # محاكاة التحديث
        # sheets_service.spreadsheets().values().batchUpdate(spreadsheetId=PROF_MEMOS_SHEET_ID, body={"valueInputOption": "USER_ENTERED", "data": updates}).execute()

        memo_row_idx = df_memos[df_memos["رقم المذكرة"].astype(str).str.strip() == str(note_number).strip()].index[0] + 2
        memo_cols = df_memos.columns.tolist()
        
        updates2 = [
            {"range": f"Feuille 1!{col_letter(memo_cols.index('الطالب الأول')+1)}{memo_row_idx}", "values": [[student1['اللقب'] + ' ' + student1['الإسم']]]},
            {"range": f"Feuille 1!{col_letter(memo_cols.index('تم التسجيل')+1)}{memo_row_idx}", "values": [["نعم"]]},
            {"range": f"Feuille 1!{col_letter(memo_cols.index('تاريخ التسجيل')+1)}{memo_row_idx}", "values": [[datetime.now().strftime('%Y-%m-%d %H:%M')]]}
        ]
        if 'كلمة سر التسجيل' in memo_cols:
            updates2.append({"range": f"Feuille 1!{col_letter(memo_cols.index('كلمة سر التسجيل')+1)}{memo_row_idx}", "values": [[used_prof_password]]})
        if student2 is not None:
            updates2.append({"range": f"Feuille 1!{col_letter(memo_cols.index('الطالب الثاني')+1)}{memo_row_idx}", "values": [[student2['اللقب'] + ' ' + student2['الإسم']]]})
            
        # محاكاة التحديث
        # sheets_service.spreadsheets().values().batchUpdate(spreadsheetId=MEMOS_SHEET_ID, body={"valueInputOption": "USER_ENTERED", "data": updates2}).execute()

        # محاكاة تحديث طلاب
        students_cols = df_students.columns.tolist()
        student1_row_idx = df_students[df_students["اسم المستخدم"].astype(str).str.strip() == student1['اسم المستخدم'].strip()].index[0] + 2
        # محاكاة التحديث
        # sheets_service.spreadsheets().values().update(spreadsheetId=STUDENTS_SHEET_ID, range=f"Feuille 1!{col_letter(students_cols.index('رقم المذكرة')+1)}{student1_row_idx}", valueInputOption="USER_ENTERED", body={"values": [[note_number]]}).execute()
        
        if student2 is not None:
            student2_row_idx = df_students[df_students["اسم المستخدم"].astype(str).str.strip() == student2['اسم المستخدم'].strip()].index[0] + 2
            # محاكاة التحديث
            # sheets_service.spreadsheets().values().update(spreadsheetId=STUDENTS_SHEET_ID, range=f"Feuille 1!{col_letter(students_cols.index('رقم المذكرة')+1)}{student2_row_idx}", valueInputOption="USER_ENTERED", body={"values": [[note_number]]}).execute()

        # محاكاة إعادة التحميل
        # df_students_updated = load_students()
        st.session_state.student1 = df_students_updated[df_students_updated["اسم المستخدم"].astype(str).str.strip() == student1['اسم المستخدم'].strip()].iloc[0]
        if student2 is not None:
            st.session_state.student2 = df_students_updated[df_students_updated["اسم المستخدم"].astype(str).str.strip() == student2['اسم المستخدم'].strip()].iloc[0]
        
        # محاكاة إرسال البريد
        memo_data = df_memos[df_memos["رقم المذكرة"].astype(str).str.strip() == str(note_number).strip()].iloc[0]
        prof_name = memo_data["الأستاذ"].strip()
        prof_memo_data = df_prof_memos[df_prof_memos["الأستاذ"].astype(str).str.strip() == prof_name].iloc[0]
        prof_email = str(prof_memo_data.get("الإيميل", "")).strip()
        if prof_email and "@" in prof_email: send_email_to_professor_real(prof_email, prof_name, memo_data, student1, student2)
        
        return True, "✅ تم تسجيل المذكرة بنجاح!"
    except Exception as e:
        print(f"Error in update_registration: {str(e)}")
        return False, f"Error in update_registration: {str(e)}"

# ---------------- Session State ----------------
if 'user_type' not in st.session_state:
    st.session_state.user_type = None
    st.session_state.logged_in = False
    st.session_state.student1 = None; st.session_state.student2 = None; st.session_state.professor = None
    st.session_state.admin_user = None; st.session_state.memo_type = "فردية"; st.session_state.mode = "register"
    st.session_state.note_number = ""; st.session_state.prof_password = ""; st.session_state.show_confirmation = False

def logout():
    for key in st.session_state.keys():
        if key not in ['user_type']: del st.session_state[key]
    st.session_state.update({
        'logged_in': False, 'student1': None, 'student2': None, 'professor': None,
        'admin_user': None, 'mode': "register", 'note_number': "", 'prof_password': "", 'show_confirmation': False
    })
    st.rerun()

# ---------------- تحميل البيانات (محاكاة للعرض) ----------------
@st.cache_data(ttl=60)
def load_students():
    return df_students

@st.cache_data(ttl=60)
def load_memos():
    return df_memos

@st.cache_data(ttl=60)
def load_prof_memos():
    return df_prof_memos

if df_students.empty or df_memos.empty or df_prof_memos.empty:
    st.error("❌ خطأ في تحميل البيانات. يرجى المحاولة لاحقاً."); st.stop()

# ---------------- اختر نوع المستخدم ----------------
if st.session_state.user_type is None:
    col_img, col_title = st.columns([1, 4])
    with col_img: 
        st.image("https://raw.githubusercontent.com/SAMIR-MALEK/memoire-depot-2026/main/LOGO2.png", width=140)
    with col_title:
        st.markdown("<h1 style='font-size: 3rem; color: #FFD700;'>نظام تسجيل المذكرات</h1>", unsafe_allow_html=True)
        st.markdown("<h4 style='color: #94A3B8; font-weight: 300;'>جامعة محمد البشير الإبراهيمي - كلية الحقوق والعلوم السياسية</h4>", unsafe_allow_html=True)
    
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🎓 فضاء الطلبة", key="student_btn", use_container_width=True): st.session_state.user_type = "student"; st.rerun()
    with col2:
        if st.button("📚 فضاء الأساتذة", key="prof_btn", use_container_width=True): st.session_state.user_type = "professor"; st.rerun()
    with col3:
        if st.button("🔇 فضاء الإدارة", key="admin_btn", use_container_width=True): st.session_state.user_type = "admin"; st.rerun()

# ============================================================
# فضاء الطلبة
# ============================================================
elif st.session_state.user_type == "student":
    if not st.session_state.logged_in:
        col1, col2 = st.columns([4, 1])
        with col2:
            if st.button("🔙 رجوع", key="back_student"):
                st.session_state.user_type = None
                st.rerun()
        
        st.markdown("<h2>🎓 فضاء الطلبة</h2>", unsafe_allow_html=True)
        st.session_state.memo_type = st.radio("اختر نوع المذكرة:", ["فردية", "ثنائية"], horizontal=True)
        
        with st.form("student_login_form"):
            username1 = st.text_input("اسم المستخدم الطالب الأول")
            password1 = st.text_input("كلمة السر الطالب الأول", type="password")
            
            username2 = password2 = None
            if st.session_state.memo_type == "ثنائية":
                st.markdown("---")
                username2 = st.text_input("اسم المستخدم الطالب الثاني")
                password2 = st.text_input("كلمة السر الطالب الثاني", type="password")
            
            submitted = st.form_submit_button("➡️ تسجيل الدخول")
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
                        st.error("❌ لا يمكن أن يكون الطالب الأول والثاني نفس الشخص!"); st.stop()

                students_data = [(username1, password1)]
                if st.session_state.memo_type == "ثنائية" and username2: students_data.append((username2, password2))
                
                # محاكاة التحقق من البيانات
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
            if st.button("🚪 خروج", key="logout_btn"):
                logout()
        
        st.markdown(f'<div class="card"><h3>ملف الطالب</h3><p>الطالب الأول: <b style="color:#2F6F7E;">{s1["اللقب"]} {s1["الإسم"]}</b></p><p>التخصص: <b>{s1["التخصص"]}</b></p></div>', unsafe_allow_html=True)
        if s2 is not None: st.markdown(f'<div class="card"><p>الطالب الثاني: <b style="color:#2F6F7E;">{s2["اللقب"]} {s2["الإسم"]}</b></p></div>', unsafe_allow_html=True)

        if st.session_state.mode == "view":
            df_memos_fresh = load_memos()
            note_num = str(s1.get('رقم المذكرة', '')).strip()
            memo_info = df_memos_fresh[df_memos_fresh["رقم المذكرة"].astype(str).str.strip() == note_num]
            if not memo_info.empty:
                memo_info = memo_info.iloc[0]
                st.markdown(f'''<div class="card" style="border-left: 5px solid #FFD700;">
                    <h3>✅ أنت مسجل في المذكرة التالية:</h3>
                    <p><b>رقم المذكرة:</b> {memo_info['رقم المذكرة']}</p>
                    <p><b>العنوان:</b> {memo_info['عنوان المذكرة']}</p>
                    <p><b>المشرف:</b> {memo_info['الأستاذ']}</p>
                    <p><b>التخصص:</b> {memo_info['التخصص']}</p>
                    <p><b>التاريخ:</b> {memo_info.get('تاريخ التسجيل','')}</p>
                </div>''', unsafe_allow_html=True)

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
                        # تحقق من صحة الاسم
                        valid, prof_row, err = verify_professor_password(st.session_state.note_number, st.session_state.prof_password, df_memos, df_prof_memos)
                        if not valid: st.error(err); st.session_state.show_confirmation = False
                        else:
                            with st.spinner('⏳ جاري تسجيل...'):
                                success, msg = update_registration_real(st.session_state.note_number, s1, s2)
                            if success: st.success(msg); st.balloons(); clear_cache_and_reload(); st.session_state.mode = "view"; st.session_state.show_confirmation = False; time.sleep(2); st.rerun()
                            else: st.error(msg); st.session_state.show_confirmation = False
                with col2:
                    if st.button("إلغاء"): st.session_state.show_confirmation = False; st.rerun()

# ============================================================
# فضاء الأساتذة
# ============================================================
elif st.session_state.user_type == "professor":
    if not st.session_state.logged_in:
        col1, col2 = st.columns([4, 1])
        with col2:
            if st.button("🔙 رجوع", key="back_prof"):
                st.session_state.user_type = None
                st.rerun()
        st.markdown("<h2>📚 فضاء الأساتذة</h2>", unsafe_allow_html=True)
        
        with st.form("prof_login_form"):
            c1, c2 = st.columns(2)
            with c1: u = st.text_input("اسم المستخدم")
            with c2: p = st.text_input("كلمة المرور", type="password")
            if st.form_submit_button("➡️ تسجيل الدخول"):
                v, r = verify_professor(u, p, df_prof_memos)
                if not v: st.error(r)
                else: st.session_state.professor = r; st.session_state.logged_in = True; st.rerun()
    else:
        prof = st.session_state.professor; prof_name = prof["الأستاذ"]
        col1, col2 = st.columns([4, 1])
        with col2:
            if st.button("🚪 خروج"):
                logout()
        
        st.markdown(f"<h2 style='margin-bottom:20px;'>فضاء الأستاذ <span style='color:#FFD700;'>{prof_name}</span></h2>", unsafe_allow_html=True)

        # --- Stats ---
        prof_memos = df_memos[df_memos["الأستاذ"].astype(str).str.strip() == prof_name.strip()]
        total = len(prof_memos)
        registered = len(prof_memos[prof_memos["تم التسجيل"].astype(str).str.strip() == "نعم"])
        available = total - registered
        is_exhausted = registered >= 4

        st.markdown('<div class="kpi-grid">', unsafe_allow_html=True)
        st.markdown(f'''
            <div class="kpi-card">
                <div class="kpi-value">{total}</div>
                <div class="kpi-label">إجمالي المذكرات</div>
            </div>
            <div class="kpi-card" style="border-color: #10B981;">
                <div class="kpi-value" style="color: #10B981;">{registered}</div>
                <div class="kpi-label">المذكرات المسجلة</div>
            </div>
            <div class="kpi-card" style="border-color: #F59E0B;">
                <div class="kpi-value" style="color: #F59E0B;">{available}</div>
                <div class="kpi-label">المذكرات المتاحة</div>
            </div>
        ''', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        if is_exhausted:
            st.markdown('<div class="alert-card">لقد استنفذت العناوين الأربعة المخصصة لك.</div>', unsafe_allow_html=True)
        
        # --- Tabs ---
        tab1, tab2, tab3 = st.tabs(["المذكرات المسجلة", "كلمات السر", "المذكرات المتاحة/المقترحة"])
        
        with tab1:
            st.subheader("المذكرات المسجلة")
            registered = prof_memos[prof_memos["تم التسجيل"].astype(str).str.strip() == "نعم"]
            
            if not registered.empty:
                cols = st.columns(2)
                for i, (_, memo) in enumerate(registered.iterrows()):
                    with cols[i % 2]:
                        progress_val = str(memo.get('نسبة التقدم', '0')).strip()
                        try: prog_int = int(progress_val) if progress_val else 0
                        except: prog_int = 0
                        
                        student1_name = memo.get('الطالب الأول', '--')
                        student2_name = memo.get('طالب الثاني', '')
                        
                        # عرض الإيميل الطالب الأول
                        student1_email = ""
                        if student1_name != '--':
                            # محاكاة البحث عن الإيميلات
                            email_match = df_students[df_students["اللقب"].astype(str).str.strip() == student1_name.split(' ', 1)[0]] | df_students["الإسم"].astype(str).str.strip() == student1_name.split(' ', 1)[0]]
                            if not email_match:
                                student1_email = "غير معروف"
                            else:
                                student1_email = email_match.iloc[0].get("بريد الإلكتروني", "").strip()
                        else:
                            student1_email = "غير معروف"

                        students_display = f"<p><b>الطالب الأول:</b> {student1_name}</p>"
                        if student2_name and str(student2_name).strip():
                            students_display += f"<p><b>الطالب الثاني:</b> {student2_name}</p>"
                        
                        if student1_email:
                            students_display += f"<p style='color:#94A3B8; font-size:0.9em;'>📧 {student1_email}</p>"

                        # عرض الإيميل الطالب الثاني
                        if student2_name and str(student2_name).strip():
                            # محاكاة البحث عن الإيميلات
                            email_match_2 = df_students[df_students["اللقب"].astype(str).str.strip() == student2_name.split(' ', 1)[0]] | df_students["الإسم"].astype(str).str.strip() == student2_name.split(' ', 1)[0]]
                            if not email_match_2:
                                student2_email = "غير معروف"
                            else:
                                student2_email = email_match_2.iloc[0].get("بريد الإلكتروني", "").strip()
                                if student2_email:
                                    students_display += f"<p style='color:#94A3B8; font-size:0.9em;'>📧 {student2_email}</p>"
                        
                        st.markdown(f'''
                        <div class="card" style="border-right: 5px solid #10B981;">
                            <h4>{memo['رقم المذكرة']} - {memo['عنوان المذكرة']}</h4>
                            <p style="color:#94A3B8; font-size:0.9em;">تخصص: {memo['التخصص']}</p>
                            {students_display}
                            <div class="progress-container">
                                <div class="progress-bar" style="width: {prog_int}%;"></div>
                            </div>
                            <p style="text-align:left; font-size:0.8em;">نسبة الإنجاز: {prog_int}%</p>
                        </div>
                        ''', unsafe_allow_html=True)
                        
                        with st.expander("إدارة وتفاصيل", expanded=False):
                            new_prog = st.selectbox("تحديث نسبة التقدم:", [
                                "0%", "10% - ضبط المقدمة", "30% - الفصل الأول", 
                                "60% - الفصل الثاني", "80% - الخاتمة", "100% - مكتملة"
                            ], key=f"prog_{memo['رقم المذكرة']}")
                            if st.button("حفظ التقدم", key=f"save_{memo['رقم المذكرة']}"):
                                mapping = {"0%":0, "10% - ضبط المقدمة":10, "30% - الفصل الأول":30, "60% - الفصل الثاني":60, "80% - الخاتمة":80, "100% - مكتملة":100}
                                s, m = update_progress_real(memo['رقم المذكرة'], mapping[new_prog])
                                st.success(m) if s else st.error(m); time.sleep(1); st.rerun()
                            
                            st.markdown("---")
                            st.markdown("**📨 إرسال طلب للإدارة**")
                            req_type = st.selectbox("نوع الطلب:", ["تغيير العنوان", "إضافة طالب"], key=f"req_{memo['رقم المذكرة']}")
                            det = ""
                            if req_type == "تغيير العنوان":
                                det = st.text_input("العنوان الجديد:", key=f"tit_{memo['رقم المذكرة']}")
                                if st.button("إرسال طلب التغيير", key=f"send_chg_{memo['رقم المذكرة']}"):
                                    if det: 
                                        r, m = send_request_to_admin(prof_name, req_type, memo['رقم المذكرة'], f"العنوان: {det}")
                                        st.success(m) if r else st.error(m)
                            else:
                                st.markdown("❌ الرجاء بإدخال العنوان الجديد")
                                
                            else:
                                c1, c2 = st.columns(2)
                                ln = c1.text_input("لقب الطالب", key=f"ln_{memo['رقم المذكرة']}")
                                fn = c2.text_input("اسم الطالب", key=f"fn_{memo['رقم المذكرة']}")
                                if st.button("إرسال طلب الإضافة", key=f"send_add_{memo['رقم المذكرة']}"):
                                    if ln and fn:
                                        r, m = send_request_to_admin(prof_name, req_type, memo['رقم المذكرة'], f"الطالب: {ln} {fn}")
                                        st.success(m) if r else st.error(m)
                                    else:
                                        st.markdown("❌ الرجاء بإدخال بيانات الطالب")
            else:
                st.markdown("❌ الرجوع إلى تعب الإنجاز التقدم")
            else:
                st.info("لا توجد مذكرات مسجلة حتى الآن.")

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
                        st.markdown(f'''
                        <div class="card" style="border-right: 5px solid {color}; display:flex; justify-content:space-between; align-items:center;">
                            <div>
                                <h3 style="margin:0; font-family:monospace; font-size:1.8rem; color:#FFD700;">{pwd}</h3>
                                <p style="margin:5px 0 0 0 0; color:#94A3B8;">الحالة: {status_txt}</p>
                            </div>
                        </div>
                        ''', unsafe_allow_html=True)
            else: st.info("لا توجد كلمات سر مسندة إليك.")

        with tab3:
            if is_exhausted: st.subheader("💡 المذكرات المقترحة")
            else: st.subheader("⏳ المذكرات المتاحة للتسجيل")
            
            avail = prof_memos[prof_memos["تم التسجيل"].astype(str).str.strip() != "نعم"]
            if not avail.empty:
                for _, m in avail.iterrows():
                    st.markdown(f'''
                    <div class="card" style="border-left: 4px solid #64748B;">
                        <h4>{m['رقم المذكرة']}</h4>
                        <p>{m['عنوان المذكرة']}</p>
                        <p style="color:#94A3B8;">تخصص: {m['التخصص']}</p>
                    </div>
                    ''', unsafe_allow_html=True)
            else: st.success("✅ جميع المذكرات مسجلة أو مقترحة!")

# ============================================================
# فضاء الإدارة
# ============================================================
elif st.session_state.user_type == "admin":
    if not st.session_state.logged_in:
        col1, col2 = st.columns([4, 1])
        with col2:
            if st.button("🔙 رجوع", key="back_admin"):
                st.session_state.user_type = None
                st.rerun()
        
        st.markdown("<h2>🔇 فضاء الإدارة</h2>", unsafe_allow_html=True)
        
        with st.form("admin_login"):
            u = st.text_input("اسم المستخدم"); p = st.text_input("كلمة المرور", type="password")
            if st.form_submit_button("➡️ دخول"):
                v, r = verify_admin(u, p)
                if not v: st.error(r)
                else: st.session_state.admin_user = r; st.session_state.logged_in = True; st.rerun()
    else:
        col1, col2 = st.columns([4, 1])
        with col2:
            if st.button("🚪 خروج"):
                logout()
        
        st.header("🔐 لوحة تحكم الإدارة")
        
        # --- Stats ---
        st_s = len(df_students); t_m = len(df_memos); r_m = len(df_memos[df_memos["تم التسجيل"].astype(str).str.strip() == "نعم"])
        a_m = t_m - r_m; t_p = len(df_prof_memos["الأستاذ"].unique())
        
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
                <div class="kpi-label">مسجلة</div>
            </div>
            <div class="kpi-card" style="border-color: #F59E0B;">
                <div class="kpi-value" style="color: #F59E0B;">{a_m}</div>
                <div class="kpi-label">متاحة</div>
            </div>
        ''', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        tab1, tab2, tab3, tab4, tab5 = st.tabs(["المذكرات", "الطلاب", "الأساتذة", "تقارير", "تحديث"])
        
        with tab1:
            st.subheader("جدول المذكرات")
            f_status = st.selectbox("تصفية:", ["الكل", "مسجلة", "متاحة"])
            if f_status == "الكل":
                d_memos = df_memos
            elif f_status == "مسجلة":
                d_memos = df_memos[df_memos["تم التسجيل"].astype(str).str.strip() == "نعم"]
            else:
                d_memos = df_memos[df_memos["تم التسجيل"].astype(str).str.strip() != "نعم"]
            
            st.dataframe(d_memos, use_container_width=True, height=500)

        with tab2:
            st.subheader("قائمة الطلاب")
            q = st.text_input("بحث (اللقب/الاسم):")
            if q:
                f_st = df_students[df_students["لقب"].astype(str).str.contains(q, case=False, na=False) | df_students["الإسم"].astype(str).str.contains(q, case=False, na=False)]
                st.dataframe(f_st, use_container_width=True, height=500)
            else: st.dataframe(df_students, use_container_width=True, height=500)

        with tab3:
            st.subheader("توزيع الأساتذة")
            profs_list = sorted(df_memos["الأستاذ"].dropna().unique())
            sel_p = st.selectbox("اختر أستاذ:", ["الكل"] + profs_list)
            if sel_p != "الكل":
                # إصلاح خطأ اختيار الأستاذ
                if sel_p in df_memos["الأستاذ"].astype(str).values:
                    st.dataframe(df_memos[df_memos["الأستاذ"].astype(str).str.strip() == sel_p.strip()], use_container_width=True, height=500)
                else:
                    st.error("بيانات الأساتذة غير متاحة حالياً.")
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
                st.bar_chart(spec_dist, color="#2F6F7E", height=400)
            
            with col2:
                st.markdown("##### حالة التسجيل حسب التخصص")
                reg_status = df_memos.groupby("التخصص")["تم التسجيل"].apply(lambda x: (x.astype(str).str.strip() == "نعم").sum())
                st.bar_chart(reg_status, color="#FFD700", height=400)

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
            if st.button("🔄 تحديث البيانات من Google Sheets"):
                with st.spinner("جاري التحديث..."):
                    st.cache_data.clear()
                    # Reload data logic here
                    st.success("✅ تم تحديث البيانات")
                    st.rerun()

st.markdown("---")
st.markdown('<div style="text-align:center; color:#64748B; font-size:12px; padding:20px;">© 2026 جامعة محمد البشير الإبراهيمي - كلية الحقوق</div>', unsafe_allow_html=True)