import streamlit as st
import pandas as pd
import re, os, base64

# --- 1. หน้าเว็บและดีไซน์ Header (โทนสีม่วง-ชมพู-ส้ม) ---
st.set_page_config(page_title="ระบบครูตระกูล", layout="wide")

def get_b64(file):
    if os.path.exists(file):
        with open(file, "rb") as f: return base64.b64encode(f.read()).decode()
    return None

img = get_b64("teacher.jpg")

# Layout: ชื่อระบบบนสุด -> รูปครูตรงกลาง -> ชื่อครูล่างรูป
st.markdown(f"""
<style>
    .main-header {{
        background: linear-gradient(90deg, #9c27b0, #e91e63, #ff9800);
        padding: 40px 20px;
        border-radius: 0 0 30px 30px;
        text-align: center;
        color: white;
        box-shadow: 0 10px 20px rgba(0,0,0,0.2);
        margin-top: -60px;
    }}
    .teacher-img {{
        width: 130px; height: 130px;
        border-radius: 50%;
        border: 5px solid rgba(255,255,255,0.8);
        box-shadow: 0 0 20px rgba(0,0,0,0.3);
        object-fit: cover;
        margin: 20px 0;
    }}
</style>
<div class="main-header">
    <h1 style="font-size: 3rem; font-weight: 800; margin:0; text-shadow: 3px 3px 6px rgba(0,0,0,0.3);">
        📋 ระบบเช็คงานอัจฉริยะ
    </h1>
    <p style="font-size: 1.2rem; opacity: 0.9;">โรงเรียนตระกาศประชาสามัคคี | ภาคเรียนที่ 2/2568</p>
    
    {f'<img src="data:image/jpeg;base64,{img}" class="teacher-img">' if img else '<div style="height:20px;"></div>'}
    
    <h2 style="margin:0; font-size: 2rem; font-weight: bold;">ครูตระกูล บุญชิต</h2>
    <div style="background: rgba(255,255,255,0.2); display: inline-block; padding: 5px 25px; border-radius: 50px; margin-top: 10px; border: 1px solid white;">
        PROFESSIONAL TEACHER
    </div>
</div><br>""", unsafe_allow_html=True)

# --- 2. ฟังก์ชันจัดการสีตัวหนังสือและสีพื้นในตาราง (High Contrast) ---
def apply_style(row):
    color_map = {
        'ม.3': ['#f3e5f5', '#7b1fa2'], # ม่วงอ่อน - ตัวหนังสือม่วงเข้ม
        'ม.4': ['#e3f2fd', '#1565c0'], # ฟ้าอ่อน - ตัวหนังสือน้ำเงินเข้ม
        'ม.5': ['#e8f5e9', '#2e7d32'], # เขียวอ่อน - ตัวหนังสือเขียวเข้ม
        'ม.6': ['#fff3e0', '#e65100'], # ส้มอ่อน - ตัวหนังสือส้มเข้ม
    }
    bg, fg = color_map.get(row['ระดับ'], ['#ffffff', '#000000'])
    return [f'background-color: {bg}; color: {fg}; font-weight: bold; border: 0.5px solid #eee;'] * len(row)

# --- 3. ฟังก์ชันล้างชื่อ (คงชื่อคุณครูไว้) ---
def clean_n(n):
    n = str(n).split('\n')[0].strip()
    prefixes = ['นาย','นางสาว','นาง','เด็กชาย','เด็กหญิง','น.ส.','ด.ช.','ด.ญ.','น.ส','ด.ช','ด.ญ']
    for p in prefixes:
        n = re.sub(f'^{p}\s*', '', n)
    return re.sub(r'^[.\-\s0-9]+', '', n).strip()

# --- 4. การประมวลผล ---
files = st.file_uploader("📂 อัปโหลดไฟล์จาก Padlet (CSV/Excel)", type=["csv", "xlsx"], accept_multiple_files=True)

if files:
    data = []
    for f in files:
        try:
            df = pd.read_csv(f, encoding='utf-8-sig') if f.name.endswith('.csv') else pd.read_excel(f)
            lv = next((m for m in ["ม.3","ม.4","ม.5","ม.6"] if m[-1] in f.name), "ทั่วไป")
            for _, r in
