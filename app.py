import streamlit as st
from datetime import datetime
import pandas as pd
# استبدال import smtplib ...
import time

# ---------------- إعداد Google Sheets (للتجربة بدون مفات خاطية) ----------------
class MockCredentials:
    def __init__(self):
        self.scopes = []
        self.info = {"username": "", "password": ""}

    def to_dict(self):
        return {"username": "admin", "password": "admin2026"}

credentials_obj = MockCredentials()

# استبدال دالة التعليق الحقيقية عندما تكون المعلومات متاحة
try:
    credentials_obj.to_dict()
    if not credentials_obj.to_dict()["username"]:
        logger.info("⚠️ لا توجد بيانات خاطية للوصول للبريد. سيتم استخدام وضع المحاكاة للنظام (بلا إرسال بريد).")
        # متغيرات الوضع هنا ستتستخدمها فقط لاستعراض الواجهة
except:
    pass

# متغيراتك السرية
STUDENTS_SHEET_ID = "1gvNkOVVKo6AO07dRKMnSQw6vZ3KdUnW7I4HBk61Sqns"
MEMOS_SHEET_ID = "1LNJMBAye4QIQy7JHz6F8mQ6-XNC1weZx1ozDZFfjD5s"
PROF_MEMOS_SHEET_ID = "1OnZi1o-oPMUI_W_Ew-op0a1uOhSj006hw_2jrMD6FSE"

ADMIN_CREDENTIALS = {"admin": "admin2026", "dsp": "dsp@2026"}
EMAIL_SENDER = "domaine.dsp@univ-bba.dz"
EMAIL_PASSWORD = "oevruyiztgikwzah"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
ADMIN_EMAIL = "domaine.dsp@univ-bba.dz"

# ---------------- دوال مساعدة ----------------
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

# ---------------- تحميل البيانات (محاكاة للعرض) ----------------
@st.cache_data(ttl=60)
def load_students():
    # في بيئة حقيقية، استبدل load_memos() بـ load_data(sheet_id, ...)
    # للتجربة الآن نرجع إطاراً:
    try:
        # محاولة قراءة البيانات المحملة
        if 'students_data' in st.session_state:
            return st.session_state.students_data
        return pd.DataFrame() # إرجاع خالية شريطة لتجنب الأخطاء
    except Exception:
        return pd.DataFrame()

def load_memos():
    if 'memos_data' in st.session_state:
        return st.session_state.memos_data
    return pd.DataFrame()

def load_prof_memos():
    if 'prof_memos_data' in st.session_state:
        return st.session_state.prof_memos_data
    return pd.DataFrame()

def clear_cache_and_reload():
    st.cache_data.clear()
    st.session_state.students_data = None; st.session_state.memos_data = None; st.session_state.prof_memos_data = None
    print("🗑️ تم مسح السجلات والمحاكاة")
    # مسح الذاكرة المحاكاة كذلك (لأن لا يبقى بيانات قديمة)
    st.rerun()

# دالة تحديث وهمي في الوضع المحاكاة
def update_progress_dummy(memo_number, progress_value):
    # في الوضع الحقيقي، استبدل .execute()
    print(f"📤 محاكاة: تحديث نسبة التقدم للمذكرة {memo_number} إلى {progress_value}%")
    return True, "✅ محاكاة: تم تحديث نسبة التقدم بنجاح"

def get_student_map():
    if 'students_map' in st.session_state:
        return st.session_state.students_map
    # إنشاء خريطة خريطة للأسماء (كامل - أسماء صغيرة للمطابعة)
    if 'students_data' in st.session_state and not st.session_state.students_data.empty:
        students_map = {}
        for index, row in st.session_state.students_data.iterrows():
            full_name = f"{row['اللقب']} {row['الإسم']}"
            email = str(row.get("البريد الإلكتروني", "")).strip()
            if email:
                students_map[full_name] = email
        st.session_state.students_map = students_map
        return st.session_state.students_map
    return {}

# دالة تحديث التسجيل في الوضع المحاكاة
def update_registration_dummy(note_number, student1, student2=None):
    print(f"📤 محاكاة: تسجيل المذكرة {note_number}")
    # هنا في الوضع الحقي: تحديث جداول Google Sheets
    return True, "✅ محاكاة: تم تسجيل المذكرة بنجاح!"

# ---------------- دالة البريد (وظيفة Mock في الوضع المحاكاة) ----------------
def send_email_to_professor(prof_email, prof_name, memo_info, student1, student2=None):
    # في الوضع الحقي: تنفيذ smtp login/send
    print(f"📤 محاكاة: إرسال بريد لـ {prof_email}")
    # دالة Mock تعيد كود HTML فقط في التمرور
    print("📤 محاكاة: تم تجهيز البريد للمشرف.")
    return True # لا نعطل التطبيق في الوضع المحاكاة

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

# ============================================================
# منطق تطبيق الطالب (محاكاة البيانات)
# ============================================================

# تحميل البيانات (إظهار قائمة وهمي للتجربة)
print("⏳️ جاري تحميل البيانات (وضع المحاكاة)...")
try:
    # هنا يمكنك تعريف بيانات وهمي للاختبار الواجهة
    st.session_state.students_data = pd.DataFrame([
        {"اسم المستخدم":"s1", "كلمة السر":"123", "اللقب":"البشير", "الإسم":"محمد", "التخصص":"قانون عام", "فردية":"نعم", "رقم المذكرة":""},
        {"اسم المستخدم":"s2", "كلمة السر":"123", "لقب":"محمد", "الإسم":"خالد", "التخصص":"قانون عام", "فردية":"لا", "رقم المذكرة":""},
        {"اسم المستخدم":"admin", "كلمة السر":"admin", "لقب":"الإدارة", "الإسم":"الإدارة", "التخصص":"إدارة", "فردية":"--", "رقم المذكرة":""} # للاختبار الإدارة
    ])
    st.session_state.memos_data = pd.DataFrame({
        "رقم المذكرة":["101", "102", "103", "104"], 
                       "201", "202"],
        "عنوان المذكرة":["نظام تشغيل المذكرات", "القانون المدني", "قانون عام", "عقوبة مالية", "تسجيل مذكرة", "مذكرة مزدوجة"],
        "الأستاذ":["أ. أحمد", "ب. فاطمة", "أ. أحمد", "أ. أحمد"],
        "التخصص":["قانون عام", "قانون عام", "قانون عام", "عقوبة مالية", "قانون عام", "عقوبة مالية"],
        "تم التسجيل":["نعم", "نعم", "نعم", "نعم", "نعم", "نعم", "نعم"]
    })
    
    st.session_state.prof_memos_data = pd.DataFrame({
        "الأستاذ":["أ. أحمد", "ب. فاطمة", "أ. أحمد", "أ. أحمد", "أ. أحمد", "أ. أحمد"],
        "إسم المستخدم":["p1", "p2", "p1", "p2", "p1", "p1", "p1"],
        "كلمة المرور":["pass1", "pass2", "pass1", "pass2", "pass1", "pass1", "pass1"],
        "كلمة سر التسجيل":["k1", "k2", "k1", "k2", "k1", "k1", "k1"],
        "الإيميل": ["p1@univ-bba.dz", "p2@univ-bba.dz", "p1@univ-bba.dz", "p2@univ-bba.dz", "p1@univ-bba.dz", "p1@univ-bba.dz", "p2@univ-bba.dz"],
        "تم التسجيل":["لا", "لا", "نعم", "نعم", "لا", "لا", "لا", "لا"]
    })
    
    # إنشاء خريطة الأسماء
    get_student_map()
    
    print("✅ تم تحميل البيانات بنجاح")

except Exception as e:
    st.error("❌ خطأ في تحميل البيانات في الوضع المحاكاة.")
    st.stop()

# ---------------- اختيار نوع المستخدم ----------------
if st.session_state.user_type is None:
    col_img, col_title = st.columns([1, 4])
    with col_img: st.image("https://raw.githubusercontent.com/SAMIR-MALEK/memoire-depot-2026/main/LOGO2.png", width=140)
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
        if st.button("🛠️ فضاء الإدارة", key="admin_btn", use_container_width=True): st.session_state.user_type = "admin"; st.rerun()

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
                
                # في الوضع الحقي: verify_students_batch
                valid, result = True, [] # نعتبر الدالة لتجنب الأخطاء هنا
                if valid:
                    verified_students = result
                    # هنا في الكود الحقي تقوم بحفظ البيانات من جول البيانات
                    for s in verified_students:
                        st.session_state.student1 = s # حفظ الكائن في ذاكرة الطالب الأول
                        if s.get("المذكرة"): # افترض وجود العمود
                            st.session_state.mode = "view"
                            st.session_state.logged_in = True
                            st.rerun()
                    st.session_state.mode = "view" if len(verified_students) > 0 else "register"
                    st.session_state.logged_in = True; st.rerun()
                else:
                    st.error("❌ خطأ في التحقق من البيانات")
                    st.stop()

    else:
        s1 = st.session_state.student1; s2 = st.session_state.student2
        col1, col2 = st.columns([4, 1])
        with col2:
            if st.button("🔙 خروج", key="logout_btn"):
                logout()
        
        st.markdown(f'<div class="card"><h3>ملف الطالب</h3><p>الطالب الأول: <b style="color:#2F6F7E;">{s1["اللقب"]} {s1["الإسم"]}</b></p><p>التخصص: <b>{s1["التخصص"]}</b></p></div>', unsafe_allow_html=True)
        if s2 is not None: st.markdown(f'<div class="card"><p>الطالب الثاني: <b style="color:#2F6F7E;">{s2["اللقب"]} {s2["الإسم"]}</b></p></div>', unsafe_allow_html=True)

        if st.session_state.mode == "view":
            # عرض وهمي للتجربة
            # في الوضع الحقي: استدع df_memos[...]
            note_num = str(s1.get("رقم المذكرة", "")).strip()
            st.markdown(f'''<div class="card" style="border-left: 5px solid #FFD700;">
                    <h3>✅ أنت مسجل في المذكرة التالية:</h3>
                    <p><b>رقم المذكرة:</b> {note_num}</p>
                    <p><b>العنوان:</b> 'محاكاة العنوان'</p>
                    <p><b>المشرف:</b> 'محاكاة الأستاذ'</p>
                    <p><b>التخصص:</b> 'محاكاة التخصص'</p>
                    <p><b>التاريخ:</b> '2026-05-22 14:30' # محاكاة تاريخ
                </div>''', unsafe_allow_html=True)

        elif st.session_state.mode == "register":
            st.markdown('<div class="card"><h3>تسجيل مذكرة جديدة</h3></div>', unsafe_allow_html=True)
            all_profs = sorted(["أ. أحمد", "ب. فاطمة"]) # وهمي محاكاة
            selected_prof = st.selectbox("اختر الأستاذ المشرف:", [""] + all_profs)
            
            if selected_prof:
                student_specialty = s1["التخصص"]
                # محاكاة البيانات
                prof_memos = st.session_state.memos_data[st.session_state.memos_data["الأستاذ"] == selected_prof.strip()]
                reg_count = len(prof_memos[prof_memos["تم التسجيل"] == "نعم"])
                
                if reg_count >= 4:
                    st.error(f'❌ الأستاذ {selected_prof} استنفذ كل العناوين')
                else:
                    st.success(f'✅ المذكرات المتاحة في تخصصك ({student_specialty}):')
                    for i, row in enumerate(prof_memos.iterrows()):
                        st.markdown(f"**{i+1}. {row['رقم المذكرة']}.** {row['عنوان المذكرة']}")
            st.markdown("---")
            c1, c2 = st.columns(2)
            with c1: st.session_state.note_number = st.text_input("رقم المذكرة", value=st.session_state.note_number)
            with c2: st.session_state.prof_password = st.text_input("كلمة سر المشرف", type="password")

            if not st.session_state.show_confirmation:
                if st.button("المتابعة للتأكيد"):
                    if not st.session_state.note_number or not st.session_state.prof_password: st.error("⚠️ يرجى إدخال البيانات"); st.session_state.show_confirmation = False
                    else: st.session_state.show_confirmation = True; st.rerun()
            else:
                st.warning(f"⚠️ تأكيد التسجيل - المذكرة رقم: {st.session_state.note_number}")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("تأكيد نهائي", type="primary"):
                        # استدع update_registration_dummy بدلاً
                        success, msg = update_registration_dummy(st.session_state.note_number, s1, s2)
                        if success:
                            st.success(msg); st.balloons()
                            # محاكاة تحديث البيانات
                            df_memos_fresh = load_memos()
                            if not df_memos_fresh.empty:
                                # محاكاة تحديث الذاكرة الطالب
                                st.session_state.students_data.loc[st.session_state.students_data["اسم المستخدم"] == s1["اسم المستخدم"], "رقم المذكرة"] = st.session_state.note_number
            else:
                st.error("❌ تحميل البيانات للعرض تفاصيل أخرى")

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
                # استدع verify_professor
                if u == "p1" and p == "pass1":
                    st.session_state.professor = {"الأستاذ": "أ. أحمد", "إسم المستخدم": "p1", "كلمة المرور": "pass1"}
                    st.session_state.logged_in = True; st.rerun()
                else:
                    st.error("❌ بيانات الدخول غير صحيحة في الوضع المحاكاة (جرب p1 / pass1)")

    else:
        prof = st.session_state.professor; prof_name = prof["الأستاذ"]
        col1, col2 = st.columns([4, 1])
        with col2:
            if st.button("🔙 خروج"):
                logout()
        
        st.markdown(f"<h2 style='margin-bottom:20px;'>فضاء الأستاذ <span style='color:#FFD700;'>{prof_name}</span></h2>", unsafe_allow_html=True)

        # --- Stats (محاكاة) ---
        prof_memos = st.session_state.memos_data[st.session_state.memos_data["الأستاذ"] == prof_name]
        total = len(prof_memos)
        registered = len(prof_memos[prof_memos["تم التسجيل"] == "نعم"])
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
            registered = prof_memos[prof_memos["تم التسجيل"] == "نعم"]
            
            if not registered.empty:
                cols = st.columns(2)
                for i, (_, memo) in enumerate(registered.iterrows()):
                    with cols[i % 2]:
                        progress_val = str(memo.get('نسبة التقدم', '0')).strip()
                        try: prog_int = int(progress_val) if progress_val else 0
                        except: prog_int = 0
                        
                        student1_name = memo.get('الطالب الأول', '--')
                        student2_name = memo.get('الطالب الثاني', '')
                        
                        # استخدام دالة get_student_map لاستخراج الإيميل (وهمي محاكاة فقط)
                        students_map = get_student_map()
                        if student1_name != '--':
                            s1_parts = student1_name.split(' ', 1)
                            if len(s1_parts) == 2:
                                s1_lname, s1_fname = s1_parts[0], s1_parts[1]
                                s1_data = st.session_state.students_data[
                                    (st.session_state.students_data["لقب"].astype(str).str.strip() == s1_lname) & 
                                    (st.session_state.students_data["الإسم"].astype(str).str.strip() == s1_fname)
                                ]
                                if not s1_data.empty:
                                    student1_email = s1_data.iloc[0].get("بريد الإلكتروني", "").strip()
                        else:
                            student1_email = "غير معروف"
                        
                        students_display = f"<p><b>الطالب الأول:</b> {student1_name}</p>"
                        if student2_name and str(student2_name).strip():
                            students_display += f"<p><b>الطالب الثاني:</b> {student2_name}</p>"
                        
                        # عرض الإيميل
                        if student1_email != "غير معروف":
                            students_display += f"<p style='color:#94A3B8; font-size:0.9em;'>📧 {student1_email}</p>"
                        
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
            else:
                st.info("لا توجد مذكرات مسجلة حتى الآن.")

        with tab2:
            st.subheader("كلمات السر")
            pwds = st.session_state.prof_memos[st.session_state.prof_memos["الأستاذ"] == prof_name]
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
                                <p style="margin:5px 0 0 0; color:#94A3B8;">الحالة: {status_txt}</p>
                            </div>
                        </div>
                        ''', unsafe_allow_html=True)
            else: st.info("لا توجد كلمات سر مسندة إليك.")

        with tab3:
            if is_exhausted: st.subheader("المذكرات المقترحة")
            else: st.subheader("المذكرات المتاحة للتسجيل")
            
            avail = prof_memos[prof_memos["تم التسجيل"] != "نعم"]
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
# فضاء الإدارة (محاكاة)
# ============================================================
elif st.session_state.user_type == "admin":
    if not st.session_state.logged_in:
        col1, col2 = st.columns([4, 1])
        with col2:
            if st.button("🔙 رجوع", key="back_admin"):
                st.session_state.user_type = None
                st.rerun()
        
        st.markdown("<h2>🛠️ فضاء الإدارة</h2>", unsafe_allow_html=True)
        
        with st.form("admin_login"):
            u = st.text_input("اسم المستخدم"); p = st.text_input("كلمة المرور", type="password")
            if st.form_submit_button("➡️ دخول"):
                v, r = u == "admin" and p == "admin2026"
                if v: st.session_state.admin_user = r; st.session_state.logged_in = True; st.rerun()
                else: st.error("❌ بيانات الإدارة غير صحيحة")
    else:
        col1, col2 = st.columns([4, 1])
        with col2:
            if st.button("🚪 خروج"):
                logout()
        st.header("لوحة تحكم الإدارة")
        
        # --- Stats (محاكاة) ---
        st_s = len(st.session_state.students_data)
        t_m = len(st.session_state.memos_data)
        r_m = len(st.session_state.memos_data[st.session_state.memos_data["تم التسجيل"] == "نعم"])
        a_m = t_m - r_m; t_p = len(st.session_state.prof_memos_data["الأستاذ"].unique())
        
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
            <div class="kpi-card" style="border-color: #10B981;">
                <div class="kpi-value" style="color: #10B981;">{len(st.session_state.students_data)} - len(st.session_state.students_data[st.session_state.students_data["رقم المذكرة"].notna()])}</div>
                <div class="kpi-label">مسجلين</div>
            </div>
            <div class="kpi-card" style="border-color: #F59E0B;">
                <div class="kpi-value" style="color: #F59E0B;">{len(st.session_state.students_data) - len(st.session_state.students_data[st.session_state.students_data["رقم المذكرة"].notna()])}</div>
                <div class="kpi-label">غير مسجلين</div>
            </div>
        ''', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        tab1, tab2, tab3, tab4, tab5 = st.tabs(["المذكرات", "الطلاب", "الأساتذة", "تقارير", "تحديث"])
        
        with tab1:
            st.subheader("جدول المذكرات")
            f_status = st.selectbox("تصفية:", ["الكل", "مسجلة", "متاحة"])
            if f_status == "الكل":
                d_memos = st.session_state.memos_data
            elif f_status == "مسجلة":
                d_memos = st.session_state.memos_data[st.session_state.memos_data["تم التسجيل"] == "نعم"]
            else:
                d_memos = st.session_state.memos_data[st.session_state.memos_data["تم التسجيل"] != "نعم"]
            
            st.dataframe(d_memos, use_container_width=True, height=400)

        with tab2:
            st.subheader("قائمة الطلاب")
            q = st.text_input("بحث (اللقب/الاسم):")
            if q:
                f_st = st.session_state.students_data[st.session_state.students_data["لقب"].astype(str).str.contains(q, case=False, na=False) | st.session_state.students_data["الإسم"].astype(str).str.contains(q, case=False, na=False)]
                st.dataframe(f_st, use_container_width=True, height=400)
            else: st.dataframe(st.session_state.students_data, use_container_width=True, height=400)

        with tab3:
            st.subheader("توزيع الأساتذة")
            profs_list = sorted(st.session_state.memos_data["الأستاذ"].unique())
            sel_p = st.selectbox("اختر أستاذ:", ["الكل"] + profs_list)
            if sel_p != "الكل":
                st.dataframe(st.session_state.memos_data[st.session_state.memos_data["الأستاذ"] == sel_p.strip()], use_container_width=True, height=400)
            else:
                s_df = st.session_state.memos_data.groupby("الأستاذ").agg({"رقم المذكرة":"count", "تم التسجيل": lambda x: (x == "نعم").sum()}).rename(columns={"رقم المذكرة":"الإجمالي", "تم التسجيل":"المسجلة"})
                s_df["المتاحة"] = s_df["الإجمالي"] - s_df["المسجلة"]
                st.dataframe(s_df, use_container_width=True)

        with tab4:
            st.subheader("التحليل الإحصائي")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("##### توزيع المذكرات حسب التخصص")
                spec_dist = st.session_state.memos_data.groupby("التخصص").size()
                st.bar_chart(spec_dist, color="#2F6F7E")
            
            with col2:
                st.markdown("##### حالة التسجيل حسب التخصص")
                reg_status = st.session_state.memos_data.groupby("التخصص")["تم التسجيل"].apply(lambda x: (x == "نعم").sum())
                st.bar_chart(reg_status, color="#FFD700")

            st.markdown("---")
            st.markdown("##### نسب التقدم العامة")
            p_df = st.session_state.memos_data[st.session_state.memos_data["تم التسجيل"] == "نعم"].copy()
            if not p_df.empty and "نسبة التقدم" in p_df.columns:
                p_df["نسبة التقدم"] = p_df["نسبة التقدم"].apply(lambda x: int(x) if str(x).isdigit() else 0)
                avg_prog = p_df["نسبة التقدم"].mean()
                st.metric("متوسط نسبة الإنجاز", f"{avg_prog:.1f}%", delta_color="normal")
                st.markdown(f'<div class="progress-container"><div class="progress-bar" style="width: {avg_prog}%;">{avg_prog:.1f}%</div></div>', unsafe_allow_html=True)
                
                st.markdown("##### آخر التسجيلات")
                recent = st.session_state.memos_data[st.session_state.memos_data["تم التسجيل"] == "نعم"].tail(5)[["رقم المذكرة", "عنوان المذكرة", "الأستاذ", "تاريخ التسجيل"]]
                st.dataframe(recent, use_container_width=True, hide_index=True)

        with tab5:
            if st.button("تحديث البيانات من Google Sheets"):
                st.spinner("جاري التحديث...")
                st.success("✅ تم التحديث")
                clear_cache_and_reload()
                st.rerun()

st.markdown("---")
st.markdown('<div style="text-align:center; color:#64748B; font-size:12px; padding:20px;">© 2026 جامعة محمد البشير الإبراهيمي - كلية الحقوق</div>', unsafe_allow_html=True)