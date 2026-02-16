import streamlit as st
import pandas as pd
import re, os, base64

# --- 1. ตั้งค่าหน้าตาและโทนสีเขียว-ขาว ---
st.set_page_config(page_title="ระบบครูตระกูล", layout="wide")

def get_b64(file):
    if os.path.exists(file):
        try:
            with open(file, "rb") as f: return base64.b64encode(f.read()).decode()
        except: return None
    return None

img_b64 = get_b64("teacher.jpg")
placeholder_img = "https://cdn-icons-png.flaticon.com/512/3429/3429433.png"

st.markdown(f"""
<style>
    .main-header {{ background-color: #1b5e20; padding: 15px; border-radius: 10px 10px 0 0; text-align: center; color: white; }}
    .teacher-card {{ background-color: #ffffff; border: 2px solid #e0e0e0; border-radius: 12px; padding: 20px; margin: 15px 0; display: flex; align-items: center; gap: 25px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }}
    .teacher-img {{ width: 110px; height: 110px; border-radius: 50%; border: 4px solid #4caf50; object-fit: cover; }}
    .level-header {{ background-color: #4caf50; color: white; padding: 10px 20px; border-radius: 8px; margin-top: 30px; margin-bottom: 10px; font-size: 1.5rem; }}
</style>
<div class="main-header"><h2 style="margin:0;">📋 ระบบเช็คงานอัจฉริยะ</h2></div>
<div class="teacher-card">
    <img src="{f'data:image/jpeg;base64,{img_b64}' if img_b64 else placeholder_img}" class="teacher-img">
    <div>
        <h1 style="margin:0; color: #1b5e20;">ครูตระกูล บุญชิต</h1>
        <p style="margin:0; color: #666;">โรงเรียนตระกาศประชาสามัคคี | ภาคเรียนที่ 2/2568</p>
    </div>
</div>
""", unsafe_allow_html=True)

# --- 2. ฟังก์ชันจัดการความสะอาดของชื่อ ---
def clean_full_name(n):
    if pd.isna(n): return "ไม่ระบุชื่อ"
    n = str(n).split('\n')[0].strip()
    prefixes = ['นาย', 'นางสาว', 'นาง', 'เด็กชาย', 'เด็กหญิง', r'น\.ส\.', r'ด\.ช\.', r'ด\.ญ\.', r'น\.ส', r'ด\.ช', r'ด\.ญ']
    for p in
