import streamlit as st
from datetime import datetime, time, date
import pandas as pd
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time as time_module
import textwrap
import base64

# ---------------- إعداد Logging ----------------
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ---------------- إعداد الصفحة ----------------
st.set_page_config(
    page_title="منصة إدارة المذكرات",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ========================
# إعداد الموعد النهائي
# ========================
REGISTRATION_DEADLINE = datetime(2027, 1, 28, 23, 59)

# ---------------- ULTIMATE PROFESSIONAL CSS ----------------
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=IBM+Plex+Sans+Arabic:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
<style>
/* ═══════════════════════════════════════════════════════════
   🎨 ULTIMATE PROFESSIONAL DESIGN - تصميم احترافي أسطوري
   ═══════════════════════════════════════════════════════════ */

:root {
    --primary: #6366f1;
    --primary-dark: #4f46e5;
    --secondary: #8b5cf6;
    --success: #10b981;
    --warning: #f59e0b;
    --danger: #ef4444;
    --dark: #0f172a;
    --dark-light: #1e293b;
    --dark-lighter: #334155;
    --text: #f1f5f9;
    --text-muted: #94a3b8;
    --border: #334155;
    --shadow: rgba(0, 0, 0, 0.25);
}

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

/* إخفاء عناصر Streamlit الافتراضية */
#MainMenu, footer, header {
    display: none !important;
}

.stDeployButton {
    display: none !important;
}

/* الخلفية الرئيسية */
html, body, [data-testid="stAppViewContainer"], .main {
    background: var(--dark) !important;
    color: var(--text) !important;
    font-family: 'IBM Plex Sans Arabic', 'Inter', sans-serif !important;
    direction: rtl !important;
}

/* إزالة padding من الـ main */
.main > div:first-child {
    padding-top: 0 !important;
}

.block-container {
    padding: 0 !important;
    max-width: 100% !important;
}

/* ═══════════════════════════════════════════════════════════
   🎯 NAVBAR - شريط التنقل الاحترافي (ثابت في الأعلى)
   ═══════════════════════════════════════════════════════════ */

.pro-navbar {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    height: 70px;
    background: linear-gradient(135deg, var(--dark-light) 0%, var(--dark) 100%);
    border-bottom: 1px solid var(--border);
    box-shadow: 0 4px 20px var(--shadow);
    z-index: 9999;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 2rem;
    backdrop-filter: blur(10px);
}

.navbar-brand {
    display: flex;
    align-items: center;
    gap: 1rem;
}

.navbar-logo {
    width: 45px;
    height: 45px;
    background: linear-gradient(135deg, var(--primary), var(--secondary));
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.5rem;
    box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
}

.navbar-title {
    font-size: 1.3rem;
    font-weight: 700;
    background: linear-gradient(135deg, var(--primary), var(--secondary));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.navbar-user {
    display: flex;
    align-items: center;
    gap: 1.5rem;
}

.user-info {
    display: flex;
    align-items: center;
    gap: 1rem;
    background: rgba(255, 255, 255, 0.05);
    padding: 0.5rem 1.5rem;
    border-radius: 50px;
    border: 1px solid var(--border);
    transition: all 0.3s ease;
}

.user-info:hover {
    background: rgba(255, 255, 255, 0.08);
    border-color: var(--primary);
}

.user-avatar {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    background: linear-gradient(135deg, var(--primary), var(--secondary));
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.1rem;
    font-weight: 700;
    color: white;
    box-shadow: 0 0 20px rgba(99, 102, 241, 0.4);
}

.user-details {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
}

.user-name {
    font-size: 0.95rem;
    font-weight: 600;
    color: var(--text);
    line-height: 1.2;
}

.user-role {
    font-size: 0.75rem;
    color: var(--text-muted);
    line-height: 1;
}

.user-status {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    font-size: 0.8rem;
    color: var(--success);
}

.status-dot {
    width: 8px;
    height: 8px;
    background: var(--success);
    border-radius: 50%;
    animation: pulse 2s infinite;
}

@keyframes pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.6; transform: scale(1.2); }
}

.logout-btn {
    background: rgba(239, 68, 68, 0.1);
    border: 1px solid rgba(239, 68, 68, 0.3);
    color: var(--danger);
    padding: 0.6rem 1.5rem;
    border-radius: 10px;
    font-size: 0.9rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s ease;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.logout-btn:hover {
    background: rgba(239, 68, 68, 0.2);
    border-color: var(--danger);
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(239, 68, 68, 0.3);
}

/* ═══════════════════════════════════════════════════════════
   📦 MAIN CONTENT - المحتوى الرئيسي
   ═══════════════════════════════════════════════════════════ */

.main-content {
    margin-top: 90px;
    padding: 2rem;
    min-height: calc(100vh - 90px);
}

/* ═══════════════════════════════════════════════════════════
   🎴 CARDS - البطاقات الاحترافية
   ═══════════════════════════════════════════════════════════ */

.pro-card {
    background: var(--dark-light);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 2rem;
    margin-bottom: 2rem;
    box-shadow: 0 8px 24px var(--shadow);
    transition: all 0.3s ease;
}

.pro-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 12px 32px var(--shadow);
    border-color: var(--primary);
}

.card-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 1.5rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid var(--border);
}

.card-title {
    font-size: 1.4rem;
    font-weight: 700;
    color: var(--text);
    display: flex;
    align-items: center;
    gap: 0.8rem;
}

.card-icon {
    width: 40px;
    height: 40px;
    background: linear-gradient(135deg, var(--primary), var(--secondary));
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.2rem;
}

/* ═══════════════════════════════════════════════════════════
   📊 STATS CARDS - بطاقات الإحصائيات
   ═══════════════════════════════════════════════════════════ */

.stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 1.5rem;
    margin-bottom: 2rem;
}

.stat-card {
    background: var(--dark-light);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 1.5rem;
    display: flex;
    align-items: center;
    gap: 1.5rem;
    transition: all 0.3s ease;
    position: relative;
    overflow: hidden;
}

.stat-card::before {
    content: '';
    position: absolute;
    top: 0;
    right: 0;
    width: 100%;
    height: 100%;
    background: linear-gradient(135deg, transparent, rgba(99, 102, 241, 0.1));
    opacity: 0;
    transition: opacity 0.3s ease;
}

.stat-card:hover {
    transform: translateY(-4px);
    border-color: var(--primary);
    box-shadow: 0 8px 24px var(--shadow);
}

.stat-card:hover::before {
    opacity: 1;
}

.stat-icon {
    width: 60px;
    height: 60px;
    border-radius: 14px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.8rem;
    flex-shrink: 0;
}

.stat-icon.primary {
    background: linear-gradient(135deg, rgba(99, 102, 241, 0.2), rgba(139, 92, 246, 0.2));
    color: var(--primary);
}

.stat-icon.success {
    background: linear-gradient(135deg, rgba(16, 185, 129, 0.2), rgba(5, 150, 105, 0.2));
    color: var(--success);
}

.stat-icon.warning {
    background: linear-gradient(135deg, rgba(245, 158, 11, 0.2), rgba(217, 119, 6, 0.2));
    color: var(--warning);
}

.stat-icon.danger {
    background: linear-gradient(135deg, rgba(239, 68, 68, 0.2), rgba(220, 38, 38, 0.2));
    color: var(--danger);
}

.stat-content {
    flex: 1;
}

.stat-value {
    font-size: 2rem;
    font-weight: 800;
    color: var(--text);
    line-height: 1;
    margin-bottom: 0.3rem;
}

.stat-label {
    font-size: 0.9rem;
    color: var(--text-muted);
    font-weight: 500;
}

/* ═══════════════════════════════════════════════════════════
   🎯 BUTTONS - الأزرار الاحترافية
   ═══════════════════════════════════════════════════════════ */

.stButton > button {
    background: linear-gradient(135deg, var(--primary), var(--secondary)) !important;
    color: white !important;
    border: none !important;
    padding: 0.8rem 2rem !important;
    border-radius: 12px !important;
    font-size: 1rem !important;
    font-weight: 600 !important;
    cursor: pointer !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3) !important;
}

.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 20px rgba(99, 102, 241, 0.4) !important;
}

.stButton > button:active {
    transform: translateY(0) !important;
}

/* ═══════════════════════════════════════════════════════════
   📋 TABLES - الجداول الاحترافية
   ═══════════════════════════════════════════════════════════ */

.stDataFrame {
    border-radius: 12px !important;
    overflow: hidden !important;
    border: 1px solid var(--border) !important;
}

.stDataFrame table {
    background: var(--dark-light) !important;
}

.stDataFrame th {
    background: var(--dark) !important;
    color: var(--text) !important;
    font-weight: 700 !important;
    padding: 1rem !important;
    border-bottom: 2px solid var(--primary) !important;
}

.stDataFrame td {
    background: var(--dark-light) !important;
    color: var(--text) !important;
    padding: 0.8rem !important;
    border-bottom: 1px solid var(--border) !important;
}

.stDataFrame tr:hover td {
    background: rgba(99, 102, 241, 0.1) !important;
}

/* ═══════════════════════════════════════════════════════════
   📑 TABS - التبويبات الاحترافية
   ═══════════════════════════════════════════════════════════ */

.stTabs [data-baseweb="tab-list"] {
    gap: 0.5rem !important;
    background: var(--dark-light);
    padding: 0.5rem;
    border-radius: 12px;
    border: 1px solid var(--border);
}

.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: var(--text-muted) !important;
    border: none !important;
    padding: 0.8rem 1.5rem !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    transition: all 0.3s ease !important;
}

.stTabs [data-baseweb="tab"]:hover {
    background: rgba(99, 102, 241, 0.1) !important;
    color: var(--text) !important;
}

.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, var(--primary), var(--secondary)) !important;
    color: white !important;
    box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3) !important;
}

/* ═══════════════════════════════════════════════════════════
   🎨 INPUTS - حقول الإدخال
   ═══════════════════════════════════════════════════════════ */

.stTextInput input,
.stSelectbox select,
.stTextArea textarea {
    background: var(--dark) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    color: var(--text) !important;
    padding: 0.8rem !important;
    font-size: 0.95rem !important;
    transition: all 0.3s ease !important;
}

.stTextInput input:focus,
.stSelectbox select:focus,
.stTextArea textarea:focus {
    border-color: var(--primary) !important;
    box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1) !important;
}

label {
    color: var(--text) !important;
    font-weight: 600 !important;
    font-size: 0.95rem !important;
    margin-bottom: 0.5rem !important;
}

/* ═══════════════════════════════════════════════════════════
   ⚠️ ALERTS - التنبيهات
   ═══════════════════════════════════════════════════════════ */

.stAlert {
    border-radius: 12px !important;
    border: 1px solid var(--border) !important;
    background: var(--dark-light) !important;
    padding: 1rem !important;
}

.stSuccess {
    border-left: 4px solid var(--success) !important;
}

.stWarning {
    border-left: 4px solid var(--warning) !important;
}

.stError {
    border-left: 4px solid var(--danger) !important;
}

.stInfo {
    border-left: 4px solid var(--primary) !important;
}

/* ═══════════════════════════════════════════════════════════
   📱 RESPONSIVE
   ═══════════════════════════════════════════════════════════ */

@media (max-width: 768px) {
    .pro-navbar {
        padding: 0 1rem;
    }
    
    .navbar-title {
        font-size: 1rem;
    }
    
    .user-info {
        padding: 0.4rem 1rem;
    }
    
    .user-name {
        display: none;
    }
    
    .stats-grid {
        grid-template-columns: 1fr;
    }
    
    .main-content {
        padding: 1rem;
    }
}

/* ═══════════════════════════════════════════════════════════
   🎭 ANIMATIONS
   ═══════════════════════════════════════════════════════════ */

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}

.pro-card, .stat-card {
    animation: fadeIn 0.5s ease;
}

/* Scrollbar */
::-webkit-scrollbar {
    width: 10px;
    height: 10px;
}

::-webkit-scrollbar-track {
    background: var(--dark);
}

::-webkit-scrollbar-thumb {
    background: var(--dark-lighter);
    border-radius: 5px;
}

::-webkit-scrollbar-thumb:hover {
    background: var(--primary);
}
</style>
""", unsafe_allow_html=True)

# ============================================================
# دالة إنشاء NAVBAR الاحترافي
# ============================================================
def render_professional_navbar(username="مستخدم", role="طالب"):
    """إنشاء شريط تنقل احترافي مع معلومات المستخدم"""
    
    # الحصول على الحرف الأول من الاسم
    first_letter = username[0] if username else "م"
    
    navbar_html = f"""
    <div class="pro-navbar">
        <div class="navbar-brand">
            <div class="navbar-logo">
                <i class="fas fa-graduation-cap"></i>
            </div>
            <div class="navbar-title">منصة إدارة المذكرات</div>
        </div>
        
        <div class="navbar-user">
            <div class="user-info">
                <div class="user-avatar">{first_letter}</div>
                <div class="user-details">
                    <div class="user-name">{username}</div>
                    <div class="user-status">
                        <span class="status-dot"></span>
                        <span>متصل</span>
                    </div>
                </div>
            </div>
            <button class="logout-btn" onclick="window.location.reload()">
                <i class="fas fa-sign-out-alt"></i>
                <span>خروج</span>
            </button>
        </div>
    </div>
    """
    
    st.markdown(navbar_html, unsafe_allow_html=True)

# ============================================================
# دالة إنشاء بطاقات الإحصائيات
# ============================================================
def render_stats_cards(stats_data):
    """إنشاء بطاقات الإحصائيات الاحترافية"""
    
    stats_html = '<div class="stats-grid">'
    
    for stat in stats_data:
        icon_class = stat.get('icon_class', 'primary')
        stats_html += f"""
        <div class="stat-card">
            <div class="stat-icon {icon_class}">
                <i class="{stat['icon']}"></i>
            </div>
            <div class="stat-content">
                <div class="stat-value">{stat['value']}</div>
                <div class="stat-label">{stat['label']}</div>
            </div>
        </div>
        """
    
    stats_html += '</div>'
    st.markdown(stats_html, unsafe_allow_html=True)

# ============================================================
# PLACEHOLDER للدوال الأصلية (ضع دوالك الأصلية هنا)
# ============================================================

# مثال بسيط لعرض التصميم
def main():
    # عرض الـ Navbar
    render_professional_navbar(username="أحمد محمد", role="طالب")
    
    # المحتوى الرئيسي
    st.markdown('<div class="main-content">', unsafe_allow_html=True)
    
    # بطاقات الإحصائيات
    stats_data = [
        {'icon': 'fas fa-users', 'value': '150', 'label': 'إجمالي الطلاب', 'icon_class': 'primary'},
        {'icon': 'fas fa-chalkboard-teacher', 'value': '45', 'label': 'عدد الأساتذة', 'icon_class': 'success'},
        {'icon': 'fas fa-book', 'value': '120', 'label': 'إجمالي المذكرات', 'icon_class': 'warning'},
        {'icon': 'fas fa-check-circle', 'value': '85', 'label': 'مذكرات مسجلة', 'icon_class': 'success'},
    ]
    
    render_stats_cards(stats_data)
    
    # بطاقة محتوى
    st.markdown("""
    <div class="pro-card">
        <div class="card-header">
            <div class="card-title">
                <div class="card-icon">
                    <i class="fas fa-clipboard-list"></i>
                </div>
                <span>قائمة المذكرات</span>
            </div>
        </div>
        <p style="color: var(--text-muted);">هنا يمكنك عرض وإدارة جميع المذكرات المسجلة في النظام.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # تبويبات
    tab1, tab2, tab3 = st.tabs(["المذكرات", "الطلاب", "الإحصائيات"])
    
    with tab1:
        st.markdown('<div class="pro-card">', unsafe_allow_html=True)
        st.write("محتوى تبويب المذكرات")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with tab2:
        st.markdown('<div class="pro-card">', unsafe_allow_html=True)
        st.write("محتوى تبويب الطلاب")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with tab3:
        st.markdown('<div class="pro-card">', unsafe_allow_html=True)
        st.write("محتوى تبويب الإحصائيات")
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
