import streamlit as st
import pandas as pd
import re
import os
import io
from datetime import datetime

# --- 1. ตั้งค่าหน้าเว็บและดีไซน์ ---
st.set_page_config(page_title="ระบบสรุปงานครูตระกูล", layout="wide")

# สร้างโฟลเดอร์เก็บฐานข้อมูล
DB_DIR = "teacher_database"
if not os.path.exists(DB_DIR):
    os.makedirs(DB_DIR)

st.markdown("""
    <style>
    .header-box {
        background-color:#1b5e20; padding:30px; border-radius:20px; 
        text-align:center; color:white; border: 3px solid #ffffff; 
        box-shadow: 0px 10px 20px rgba(0,0,0,0.2);
    }
    </style>
    <div class="header-box">
        <h1 style="margin:0;">📊 ระบบสรุปผลการส่งงานรายบุคคล</h1>
        <p style="margin-top:10px; font-size:1.2rem;">แยกตามระดับชั้น ม.3, ม.4, ม.5, ม.6</p>
        <hr style="border: 0.5px solid #fff; width: 30%; margin: 15px auto;">
        <p style="font-size:1rem;">โดย คุณครูตระกูล บุญชิต</p>
    </div>
""", unsafe_allow_html=True)

# --- 2. รูปโปรไฟล์คุณครู ---
st.markdown("<br>", unsafe_allow_html=True)
_, col_m, _ = st.columns([2, 1, 2])
with col_m:
    if os.path.exists("teacher.jpg"):
        st.image("teacher.jpg", use_container_width=True, caption="คุณครูตระกูล บุญชิต")
    else:
        st.markdown("<h1 style='text-align:center;'>👨‍🏫</h1>", unsafe_allow_html=True)

st.divider()

# --- 3. ส่วนจัดการไฟล์ (Upload) ---
st.subheader("📂 1. อัปโหลดไฟล์จาก Padlet")
uploaded_files = st.file_uploader("ลากไฟล์ CSV หรือ Excel มาวางที่นี่ (อัปโหลดพร้อมกันได้หลายไฟล์)", 
                                  type=["csv", "xlsx"], accept_multiple_files=True)

if uploaded_files:
    for f in uploaded_files:
        with open(os.path.join(DB_DIR, f.name), "wb") as file:
            file.write(f.getbuffer())
    st.success("✅ บันทึกข้อมูลสำเร็จ!")
    st.rerun()

history_files = sorted(os.listdir(DB_DIR))
if history_files:
    with st.expander("📜 รายชื่อไฟล์ในระบบ (สามารถกดลบได้)"):
        for f_name in history_files:
            c1, c2 = st.columns([5, 1])
            c1.text(f"📄 {f_name}")
            if c2.button("ลบ", key=f"del_{f_name}"):
                os.remove(os.path.join(DB_DIR, f_name))
                st.rerun()

st.divider()

# --- 4. ฟังก์ชันการดึงข้อมูล (Logic) ---
def clean_name(t):
    t = str(t)
    for p in ['นาย', 'นางสาว', 'น.ส.', 'เด็กชาย', 'เด็กหญิง', 'ด.ช.', 'ด.ญ.']:
        if p in t: t = t[t.find(p) + len(p):]; break
    m = re.search(r'^([ก-ฮะ-์\s]+)', t.strip())
    name = m.group(1).strip() if m else "ไม่ระบุชื่อ"
    for junk in ['ชั้น', 'เลขที่', 'ม.', '/', '(', 'ชื่อเล่น', 'กลุ่ม']:
        name = name.split(junk)[0].strip()
    return name

all_recs = []
for fn in history_files:
    try:
        f_path = os.path.join(DB_DIR, fn)
        df_t = pd.read_csv(f_path, encoding='utf-8-sig') if fn.endswith('.csv') else pd.read_excel(f_path)
        
        # ระบุระดับชั้นจากชื่อไฟล์
        lv = "ม.3" if '3' in fn else "ม.4" if '4' in fn else "ม.5" if '5' in fn else "ม.6" if '6' in fn else "ทั่วไป"
        
        for _, r in df_t.iterrows():
            txt, subj = str(r.get('เนื้อหา','')), str(r.get('เรื่อง',''))
            sid = re.search(r'เลขที่\s*(\d+)', txt)
            act = re
