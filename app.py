import streamlit as st
import pandas as pd
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from datetime import datetime

# =========================================================
# إعداد الصفحة
# =========================================================
st.set_page_config(
    page_title="منصة تسجيل مذكرات الماستر",
    page_icon="🎓",
    layout="centered"
)

# =========================================================
# CSS
# =========================================================
st.markdown("""
<style>
.message {
    color: #FF4500;
    font-weight: bold;
    text-align: center;
}
.block-container {
    background-color: #1A2A3D;
    padding: 20px;
    border-radius: 12px;
}
</style>
""", unsafe_allow_html=True)

# =========================================================
# Session State
# =========================================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "student" not in st.session_state:
    st.session_state.student = None

if "memo_type" not in st.session_state:
    st.session_state.memo_type = None

# =========================================================
# Google Sheets
# =========================================================
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

credentials = Credentials.from_service_account_info(
    st.secrets["service_account"],
    scopes=SCOPES
)

service = build("sheets", "v4", credentials=credentials)

SPREADSHEET_ID = st.secrets["spreadsheet_id"]

# =========================================================
# دوال Google Sheets
# =========================================================
def read_sheet(sheet_name):
    result = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=sheet_name
    ).execute()

    values = result.get("values", [])
    if not values:
        return pd.DataFrame()

    return pd.DataFrame(values[1:], columns=values[0])


def append_sheet(sheet_name, row):
    service.spreadsheets().values().append(
        spreadsheetId=SPREADSHEET_ID,
        range=sheet_name,
        valueInputOption="USER_ENTERED",
        body={"values": [row]}
    ).execute()

# =========================================================
# تحميل الشيتات (لا تغيّر الأسماء)
# =========================================================
df_students = read_sheet("تجريب الطلبة")
df_memoires = read_sheet("تجريب حالة تسجيل المذكرات")
df_teachers = read_sheet("تجريب المذكرات - الأساتذة")

# =========================================================
# التحقق من الطالب
# =========================================================
def verify_student(username, password, df):
    row = df[df["اسم المستخدم"].astype(str).str.strip() == username.strip()]

    if row.empty:
        return False, "اسم المستخدم غير موجود"

    if row.iloc[0]["كلمة السر"].strip() != password.strip():
        return False, "كلمة السر غير صحيحة"

    return True, row.iloc[0].to_dict()

# =========================================================
# واجهة تسجيل الدخول (دخول حقيقي)
# =========================================================
if not st.session_state.logged_in:
    st.title("🔐 تسجيل الدخول")

    username = st.text_input("اسم المستخدم")
    password = st.text_input("كلمة السر", type="password")

    if st.button("تسجيل الدخول"):
        valid1, student1 = verify_student(username, password, df_students)

        if not valid1:
            st.markdown(
                f'<p class="message">❌ {student1}</p>',
                unsafe_allow_html=True
            )
            st.stop()

        st.session_state.logged_in = True
        st.session_state.student = student1
        st.rerun()

# =========================================================
# حماية التطبيق (مهم جدا)
# =========================================================
if not st.session_state.logged_in:
    st.stop()

student = st.session_state.student

# =========================================================
# فضاء الطالب
# =========================================================
st.title("🎓 فضاء الطالب")
st.success(f"مرحبًا {student['الاسم واللقب']}")

# =========================================================
# هل الطالب مسجل مسبقًا؟
# =========================================================
existing = df_memoires[
    df_memoires["اسم المستخدم"].astype(str).str.strip()
    == student["اسم المستخدم"].strip()
]

if not existing.empty:
    st.info("✅ أنت مسجل مسبقًا في مذكرة")

    st.write("📘 **عنوان المذكرة:**", existing.iloc[0]["عنوان المذكرة"])
    st.write("👨‍🏫 **الأستاذ:**", existing.iloc[0]["الأستاذ"])
    st.write("📅 **تاريخ التسجيل:**", existing.iloc[0]["تاريخ التسجيل"])

    st.stop()

# =========================================================
# اختيار نوع المذكرة
# =========================================================
st.subheader("📌 اختيار نوع المذكرة")

memo_type = st.radio(
    "نوع المذكرة",
    ["فردية", "ثنائية"]
)

st.session_state.memo_type = memo_type

# =========================================================
# شرط المذكرة الفردية (كما طلبت حرفيًا)
# =========================================================
if st.session_state.memo_type == "فردية":
    value = str(student.get("فردية", "")).strip().lower()

    if value not in ["1", "نعم"]:
        st.markdown(
            '<div class="block-container">'
            '<h4 style="text-align:center; color:#FF4500;">❌ لا يمكن تسجيل مذكرة فردية. يرجى الاتصال بمسؤول الميدان للحصول على الموافقة</h4>'
            '<p style="text-align:center; color:#FFD700;">📧 Email: domaie.dsp@univ-bba.dz</p>'
            '</div>',
            unsafe_allow_html=True
        )
        st.stop()

# =========================================================
# نموذج تسجيل المذكرة
# =========================================================
st.subheader("📝 تسجيل المذكرة")

title = st.text_input("عنوان المذكرة")

teacher = st.selectbox(
    "الأستاذ المشرف",
    df_teachers["اسم الأستاذ"].dropna().unique()
)

if st.button("📌 تسجيل المذكرة"):
    append_sheet(
        "تجريب حالة تسجيل المذكرات",
        [
            student["اسم المستخدم"],
            student["الاسم واللقب"],
            st.session_state.memo_type,
            title,
            teacher,
            datetime.now().strftime("%Y-%m-%d %H:%M")
        ]
    )

    st.success("✅ تم تسجيل المذكرة بنجاح")
    st.rerun()