import streamlit as st
import pandas as pd
import re
import os

# --- ส่วนหัวแอป ---
st.set_page_config(page_title="ระบบสรุปงานครูเจมส์", layout="wide")
st.markdown("<h1 style='text-align: center; color: #1b5e20;'>📊 ระบบสรุปผลการส่งงาน</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>โดย คุณครูตระกูล บุญชิต</p>", unsafe_allow_html=True)

# --- ฟังก์ชันตัดคำนำหน้าชื่อ ---
def remove_prefix(name):
    name = str(name).strip()
    # รายการคำนำหน้าที่ต้องการตัดออก
    prefixes = ['นาย', 'นางสาว', 'น.ส.', 'นาง', 'เด็กชาย', 'เด็กหญิง', 'ด.ช.', 'ด.ญ.']
    for p in prefixes:
        if name.startswith(p):
            name = name[len(p):].strip() # ตัดคำนำหน้าออกแล้วลบช่องว่าง
            break
    return name

# --- ปุ่มอัปโหลด ---
uploaded_files = st.file_uploader("เลือกไฟล์จาก Padlet (CSV หรือ Excel)", type=["csv", "xlsx"], accept_multiple_files=True)

if uploaded_files:
    all_records = []
    for f in uploaded_files:
        df = pd.read_csv(f, encoding='utf-8-sig') if f.name.endswith('.csv') else pd.read_excel(f)
        
        # ค้นหาระดับจากชื่อไฟล์
        lv = "ม.3" if '3' in f.name else "ม.4" if '4' in f.name else "ม.5" if '5' in f.name else "ม.6" if '6' in f.name else "ทั่วไป"
        
        for _, row in df.iterrows():
            txt = str(row.get('เนื้อหา', '')) + " " + str(row.get('เรื่อง', ''))
            
            # ดึงเลขที่และกิจกรรม
            sid = re.search(r'เลขที่\s*(\d+)', txt)
            act = re.search(r'กิจกรรม(?:ที่)?\s*1\.(\d+)', txt)
            
            if sid and act:
                # ดึงชื่อจากบรรทัดแรก และส่งไปตัดคำนำหน้า
                raw_name = str(row.get('เนื้อหา', '')).split('\n')[0].strip()
                clean_name = remove_prefix(raw_name)
                
                all_records.append({
                    'ระดับ': lv, 
                    'เลข
