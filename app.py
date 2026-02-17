import streamlit as st
import pandas as pd
import re, os, base64
from io import BytesIO

# --- 1. CONFIG & STYLES ---
st.set_page_config(page_title="ระบบครูตระกูล v9.7", layout="wide")

def inject_custom_css():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@400;700&display=swap');
        html, body, [class*="css"] { font-family: 'Sarabun', sans-serif; }
        .main-header { background-color: #1b5e20; padding: 20px; border-radius: 15px; text-align: center; color: white; }
        .level-header { background-color: #f0f4f1; padding: 10px 20px; border-radius: 10px; color: #1b5e20; font-size: 1.8rem; font-weight: bold; margin-top: 30px; border: 2px solid #1b5e20; }
        .room-label { background-color: #e8f5e9; padding: 10px 15px; border-left: 5px solid #2e7d32; border-radius: 5px; margin: 15px 0; font-weight: bold; color: #1b5e20; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA PROCESSING --- (คงฟังก์ชันเดิมแต่ปรับการดึงระดับชั้น)
def process_master_files(files):
    db = {}
    for f in files:
        name = f.name.replace('.xlsx', '').replace('.csv', '').split(' - ')[0]
        # ดึงระดับชั้น เช่น "ม.3" จาก "ม.3-1"
        level_match = re.search(r'(ม\.\d+)', name)
        level = level_match.group(1) if level_match else "ไม่ระบุระดับชั้น"
        
        df = pd.read_csv(f, encoding='utf-8-sig') if f.name.endswith('.csv') else pd.read_excel(f)
        c_sid = next((c for c in df.columns if "เลขที่" in str(c)), None)
        c_name = next((c for c in df.columns if "ชื่อ" in str(c)), None)
        
        if c_sid and c_name:
            df_clean = df[[c_sid, c_name]].copy().dropna()
            df_clean.columns = ['เลขที่', 'ชื่อ - นามสกุล']
            df_clean['เลขที่'] = pd.to_numeric(df_clean['เลขที่'], errors='coerce').fillna(0).astype(int)
            
            if level not in db: db[level] = {}
            db[level][name] = df_clean
    return db

# --- 3. MAIN APP ---
def main():
    inject_custom_css()
    st.markdown('<div class="main-header"><h2>📋 ระบบรายงานผลแยกตามระดับชั้น (v9.7)</h2></div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    m_files = col1.file_uploader("📂 1. อัปโหลดรายชื่อ (เช่น ม.1-1, ม.2-1, ม.3-1)", accept_multiple_files=True)
    p_files = col2.file_uploader("📂 2. อัปโหลดงานจาก Padlet", accept_multiple_files=True)

    if m_files and p_files:
        # แยกฐานข้อมูลตามระดับชั้น และตามห้อง
        levels_db = process_master_files(m_files)
        # โค้ดส่วนดึง Padlet (เรียกจากโค้ดเดิม)
        # ... (df_padlet = process_padlet_files(p_files)) ...
        
        # วนลูปตามระดับชั้น (ม.1, ม.2, ม.3)
        for level in sorted(levels_db.keys()):
            st.markdown(f'<div class="level-header">📚 ระดับชั้น {level}</div>', unsafe_allow_html=True)
            
            # วนลูปห้องเรียนในระดับชั้นนั้นๆ
            for room, room_list in levels_db[level].items():
                st.markdown(f'<div class="room-label">🏫 ห้อง: {room}</div>', unsafe_allow_html=True)
                
                # ... (ส่วนการแสดงผล Dataframe และปุ่ม Download xlsxwriter เดิม) ...
                st.write(f"แสดงข้อมูลของ {room} ตรงนี้")

    else:
        st.info("กรุณาอัปโหลดไฟล์รายชื่อที่มีการระบุระดับชั้น (เช่น ม.3-1) เพื่อให้ระบบแยกประเภทให้ครับ")

if __name__ == "__main__":
    main()
