import streamlit as st
from datetime import datetime, time, date, timedelta
import pandas as pd
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from googleapiclient.errors import HttpError
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import io
import base64
import re
import random
import time
import textwrap

# ---------------- إعداد Logging ----------------
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ---------------- إعداد الصفحة ----------------
st.set_page_config(page_title="نظام إدارة مذكرات الماستر", page_icon="📘", layout="wide")
st.cache_data.clear()

# ---------------- CSS ----------------
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;900&display=swap" rel="stylesheet">
<style>
    * { box-sizing: border-box; }
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif !important; direction: rtl; text-align: right; }
    .main { background-color: #0A1B2C; color: #ffffff; }
    .block-container { padding: 2rem; background-color: #1A2A3D; border-radius: 16px; margin:auto; }
    h1, h2, h3, h4 { font-weight: 700; margin-bottom: 1rem; color: #ffffff !important; }
    label, p, span { color: #ffffff !important; }
    
    /* Cards */
    .card {
        background: rgba(30, 41, 59, 0.95); border:1px solid rgba(255,255,255, 0.08);
        border-radius: 20px; padding: 30px; margin-bottom: 20px;
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.2);
        border-top: 3px solid #2F6F7E; transition: transform 0.2s ease;
    }
    .card:hover { transform: translateY(-2px); }
    
    /* Buttons */
    .stButton>button, button[kind="primary"] {
        background-color: #2F6F7E !important; color: #ffffff !important;
        border-radius: 12px !important; padding: 12px 28px;
        border: none !important; font-weight: 600; width: 100%;
    }
    .stButton>button:hover { background-color: #285E6B !important; }

    /* KPIs */
    .kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1.5rem; margin-bottom: 2.5rem; }
    .kpi-card { background: linear-gradient(145deg, #1E293B, #0F172A); border: 1px solid rgba(255, 255, 255, 0.05); border-radius: 16px; padding: 2rem 1rem; text-align: center; }
    .kpi-value { font-size: 2.5rem; font-weight: 900; color: #FFD700; margin: 10px 0; }
    .kpi-label { font-size: 1.1rem; color: #ffffff; }

    /* Status Badges */
    .status-badge { padding: 8px 16px; border-radius: 20px; font-size: 0.95rem; font-weight: bold; text-align: center; display: inline-block; margin: 5px; }
    .status-deposited { background: rgba(59, 130, 246, 0.2); color: #3B82F6; }
    .status-validated { background: rgba(16, 185, 129, 0.2); color: #10B981; }
    .status-scheduled { background: rgba(139, 92, 246, 0.2); color: #8B5CF6; }
    .status-rejected { background: rgba(239, 68, 68, 0.2); color: #EF4444; }
    
    /* Upload Area */
    .upload-area { border: 2px dashed #2F6F7E; border-radius: 15px; padding: 40px; text-align: center; background: rgba(47, 111, 126, 0.05); margin-top: 20px; }
    
    /* Progress Bar */
    .progress-container { background-color: #0F172A; border-radius: 99px; padding: 6px; margin: 20px 0; overflow: hidden; }
    .progress-bar { height: 24px; border-radius: 99px; background: linear-gradient(90deg, #2F6F7E 0%, #FFD700 100%); box-shadow: 0 0 15px rgba(47, 111, 126, 0.5); }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] { gap: 2rem; }
    .stTabs [data-baseweb="tab"] { color: #94A3B8; font-weight: 600; padding: 10px 20px; border-radius: 10px; }
    .stTabs [aria-selected="true"] { background: rgba(47, 111, 126, 0.2); color: #FFD700; }
    
    /* DataFrames */
    .stDataFrame { border-radius: 12px; overflow: hidden; border: 1px solid rgba(255,255,255, 0.1); background: #1E293B; }
</style>
""", unsafe_allow_html=True)

# ---------------- Google APIs ----------------
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
try:
    info = st.secrets["service_account"]
    credentials = Credentials.from_service_account_info(info, scopes=SCOPES)
    sheets_service = build('sheets', 'v4', credentials=credentials)
    drive_service = build('drive', 'v3', credentials=credentials)
except Exception as e:
    st.error("⚠️ خطأ في الاتصال بـ Google APIs"); st.stop()

# ---------------- IDs ----------------
STUDENTS_SHEET_ID = "1gvNkOVVKo6AO07dRKMnSQw6vZ3KdUnW7I4HBk61Sqns"
MEMOS_SHEET_ID = "1LNJMBAye4QIQy7JHz6F8mQ6-XNC1weZx1ozDZFfjD5s"
PROF_MEMOS_SHEET_ID = "1OnZi1o-oPMUI_W_Ew-op0a1uOhSj006hw_2jrMD6FSE"
SETTINGS_SHEET_ID = MEMOS_SHEET_ID 

# Ranges
STUDENTS_RANGE = "Feuille 1!A1:U1000" 
MEMOS_RANGE = "Feuille 1!A1:AC1000" 
PROF_MEMOS_RANGE = "Feuille 1!A1:P1000"
REQUESTS_RANGE = "Feuille 1!A1:K1000"
SETTINGS_RANGE = "Settings!A1:B10"
ROOMS_RANGE = "Rooms!A1:B20"

ADMIN_CREDENTIALS = {"admin": "admin2026"}
EMAIL_SENDER = "domaine.dsp@univ-bba.dz"
EMAIL_PASSWORD = "qptlxzunqhdcjcjt"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# ---------------- دوال مساعدة ----------------
def col_letter(n):
    result = ""
    while n > 0:
        n, remainder = divmod(n - 1, 26)
        result = chr(65 + remainder) + result
    return result

def normalize_text(val):
    v = str(val).strip()
    if v.endswith('.0'): v = v[:-2]
    return v

def sanitize_input(text):
    if not text: return ""
    return str(text).strip()

# --- نهاية الجزء الأول ---