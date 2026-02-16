import streamlit as st
import pandas as pd
import re
import os
import io
from datetime import datetime

# --- 1. ตั้งค่าหน้าเว็บและสไตล์ ---
st.set_page_config(page_title="ระบบตรวจสอบงาน - ครูตระกูล", layout="centered")

# สร้างโฟลเดอร์เก็บฐานข้อมูลไฟล์
DB_DIR = "stored_db"
if not os.path.exists(DB_DIR):
    os.makedirs(DB_DIR)

st.markdown("""
    <style>
    .main-header {
        background-color:#1b5e20; padding:35px; border-radius:20px; 
        text-align:center; color:white; border: 3px solid #ffffff; 
        box-shadow: 0px 10px 20px rgba(0,0,0,0.2);
    }
    </style>
    <div class="main-header">
        <h1 style="margin:0;">📋 ระบบตรวจสอบการส่งงาน</h1>
        <p style="margin-top:10px; font-size:1.2rem; font-weight:bold;">ระบบเช็คสถานะและจัดการไฟล์ Padlet</p>
        <hr style="border: 0.5px solid #fff; width: 30%; margin: 15px auto;">
        <p style="font-size:1rem;">โดย คุณครูตระกูล บุญชิต</p>
    </div>
""", unsafe_allow_html=True)

# --- 2. รูปโปรไฟล์คุณครู (Centered) ---
st.markdown("<br>", unsafe_allow_html=True)
col_l, col_m, col_r = st.columns([1, 1, 1])
with col_m:
    if os.path.exists("teacher.jpg"):
        st.image("teacher.jpg", use_container_width=True, caption="คุณครูตระกูล บุญชิต")
    else:
        st.markdown("<h1 style='text-align:center;'>👨‍🏫</h1>", unsafe_allow_html=True)

st.divider()

# --- 3. ส่วนจัดการไฟล์ (Upload & History) ---
st.subheader("📂 จัดการไฟล์ข้อมูล")
uploaded_files = st.file_uploader("อัปโหลดไฟล์ CSV หรือ Excel จาก Padlet", type=["csv", "xlsx"], accept_multiple_files=True)

if uploaded_files:
    for f in uploaded_files:
        with open(os.path.join(DB_DIR, f.name), "wb") as file:
            file.write(f.getbuffer())
    st.success(f"✅ บันทึกไฟล์ {len(uploaded_files)} ไฟล์เรียบร้อย!")
    st.rerun()

# แสดงประวัติไฟล์ที่จัดเก็บ
history_files = sorted(os.listdir(DB_DIR))
if history_files:
    with st.expander("📜 ประวัติการอัปโหลดไฟล์ในระบบ"):
        for f_name in history_files:
            c1, c2 = st.columns([4, 1])
            c1.text(f"📄 {f_name}")
            if c2.button("ลบ", key=f"del_{f_name}"):
                os.remove(os.path.join(DB_DIR, f_name))
                st.rerun()
else:
    st.info("💡 ยังไม่มีไฟล์ในฐานข้อมูล โปรดอัปโหลดไฟล์เพื่อเริ่มต้น")

st.divider()

# --- 4. ฟังก์ชันประมวลผลข้อมูล (Data Engine) ---
def clean_student_name(text):
    text = str(text)
    # ตัดคำนำหน้า
    for p in ['นาย', 'นางสาว', 'น.ส.', 'เด็กชาย', 'เด็กหญิง', 'ด.ช.', 'ด.ญ.']:
        if p in text:
            text = text[text.find(p) + len(p):]
            break
    # ดึงเฉพาะชื่อ-นามสกุล (ก-ฮ)
    match = re.search(r'^([ก-ฮะ-์\s]+)', text.strip())
    if match:
        name = match.group(1).strip()
        # ตัดคำขยะที่มักติดมา
        for junk in ['ชั้น', 'เลขที่', 'ม.', '/', '(', 'ชื่อเล่น', 'กลุ่ม']:
            name = name.split(junk)[0].strip()
        return name if name else "ไม่ระบุชื่อ"
    return "ไม่ระบุชื่อ"

all_records = []
for fn in history_files:
    try:
        f_path = os.path.join(DB_DIR, fn)
        # ลองอ่านหลาย Encoding ป้องกันภาษาไทยเพี้ยน
        try:
            df_t = pd.read_csv(f_path, encoding='utf-8-sig') if fn.endswith('.csv') else pd.read_excel(f_path)
        except:
            df_t = pd.read_csv(f_path, encoding='tis-620')
            
        # กำหนดระดับชั้นจากชื่อไฟล์
        lv = "ม.3" if '3' in fn else "ม.4" if '4' in fn else "ม.5" if '5' in fn else "ม.6" if '6' in fn else "ทั่วไป"
        
        for _, r in df_t.iterrows():
            content = str(r.get('เนื้อหา',''))
            subject = str(r.get('เรื่อง',''))
            sid = re.search(r'เลขที่\s*(\d+)', content)
            act = re.search(r'กิจกรรม(?:ที่)?\s*1\.(\d+)', subject + content)
            
            if sid and act:
                all_records.append({
                    'ระดับ': lv,
                    'เลขที่': int(sid.group(1)),
                    'ชื่อ-นามสกุล': clean_student_name(content),
                    'กิจกรรม': f"กิจกรรมที่ 1.{act.group(1)}"
                })
    except: continue

# --- 5. แสดงตารางสรุปข้อมูล (ถัดมาแสดงข้อมูล) ---
if all_records:
    final_df = pd.DataFrame(all_records).drop_duplicates()
    pivot = final_df.pivot_table(index=['ระดับ', 'เลขที่', 'ชื่อ-นามสกุล'], 
                                   columns='กิจกรรม', values='กิจกรรม', 
                                   aggfunc=lambda x: '✔').fillna('-').reset_index()
    pivot = pivot.sort_values(by=['ระดับ', 'เลขที่'])

    st.subheader("📊 ตารางสรุปภาพรวม")
    st.dataframe(pivot, use_container_width=True, hide_index=True)

    # ปุ่มดาวน์โหลด Excel
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        pivot.to_excel(writer, index=False, sheet_name='Summary')
    
    st.download_button(
        label="📥 ดาวน์โหลดตารางนี้เป็นไฟล์ Excel",
        data=output.getvalue(),
        file_name=f"รายงานการส่งงาน_{datetime.now().strftime('%d-%m-%Y')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    st.divider()

    # --- 6. ส่วนค้นหารายบุคคลสำหรับนักเรียน ---
    st.subheader("🔍 ค้นหาประวัติส่วนตัว")
    query = st.text_input("กรอกเลขที่ หรือ ชื่อเพื่อเช็คงาน:", placeholder="เช่น 7")
    if query:
        res = pivot[pivot.apply(lambda x: x.astype(str).str.contains(query, case=False)).any(axis=1)]
        if not res.empty:
            for _, r in res.iterrows():
                with st.container(border=True):
                    st.markdown(f"### 👤 {r['ระดับ']} เลขที่ {r['เลขที่']} - {r['ชื่อ-นามสกุล']}")
                    done = [c for c in pivot.columns if r[c] == '✔' and 'กิจกรรม' in c]
                    st.write(f"**ส่งงานแล้ว:** :green[{len(done)}] รายการ")
                    st.info(", ".join(done) if done else "ยังไม่มีข้อมูล")
        else: st.error("❌ ไม่พบข้อมูลที่ต้องการ")
else:
    st.warning("⚠️ โปรดอัปโหลดไฟล์ข้อมูลก่อนเพื่อเริ่มต้นระบบ")

st.markdown("<hr><center style='color:grey; font-size:0.8rem;'>© 2026 Tracking System by ครูตระกูล บุญชิต</center>", unsafe_allow_html=True)
