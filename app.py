import streamlit as st
import pandas as pd
import re
import os
import io
from datetime import datetime

# --- การตั้งค่าหน้าเว็บ (เน้นใช้งานเป็นเครื่องมือสรุปงานส่วนตัว) ---
st.set_page_config(page_title="ระบบสรุปงานครูตระกูล", layout="wide")

# โฟลเดอร์เก็บฐานข้อมูล
DB_DIR = "teacher_database"
if not os.path.exists(DB_DIR):
    os.makedirs(DB_DIR)

# --- ส่วนหัว Dashboard สีเขียวเข้ม ---
st.markdown("""
    <div style="background-color:#1b5e20; padding:30px; border-radius:15px; text-align:center; color:white; border: 2px solid #ffffff;">
        <h1 style="margin:0;">📊 ระบบสรุปผลการส่งงาน (Teacher Tools)</h1>
        <p style="margin-top:10px; font-size:1.2rem;">รวบรวมฐานข้อมูล Padlet และออกรายงาน Excel</p>
        <hr style="border: 0.5px solid #fff; width: 30%; margin: 15px auto;">
        <p style="font-size:1rem;">คุณครูตระกูล บุญชิต - โรงเรียนตระกาศประชาสามัคคี</p>
    </div>
""", unsafe_allow_html=True)

# --- รูปโปรไฟล์คุณครูตรงกลาง ---
st.markdown("<br>", unsafe_allow_html=True)
col_l, col_m, col_r = st.columns([2, 1, 2])
with col_m:
    if os.path.exists("teacher.jpg"):
        st.image("teacher.jpg", use_container_width=True)
    else:
        st.markdown("<h1 style='text-align:center;'>👨‍🏫</h1>", unsafe_allow_html=True)

st.divider()

# --- ส่วนที่ 1: การจัดการไฟล์ ---
st.subheader("📂 1. อัปโหลดและจัดการไฟล์ Padlet")
uploaded_files = st.file_uploader("เลือกไฟล์ CSV หรือ Excel จาก Padlet หลายๆ ห้องพร้อมกัน", type=["csv", "xlsx"], accept_multiple_files=True)

if uploaded_files:
    for f in uploaded_files:
        with open(os.path.join(DB_DIR, f.name), "wb") as file:
            file.write(f.getbuffer())
    st.success("✅ บันทึกไฟล์ข้อมูลเรียบร้อย!")
    st.rerun()

history_files = sorted(os.listdir(DB_DIR))
if history_files:
    with st.expander("📜 ดูรายชื่อไฟล์ที่จัดเก็บไว้ในระบบ"):
        for f_name in history_files:
            c1, c2 = st.columns([5, 1])
            c1.text(f"📄 {f_name}")
            if c2.button("ลบ", key=f"del_{f_name}"):
                os.remove(os.path.join(DB_DIR, f_name))
                st.rerun()

st.divider()

# --- ส่วนที่ 2: การประมวลผลข้อมูลสรุป ---
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
        # ตรวจสอบระดับจากชื่อไฟล์
        lv = "ม.3" if '3' in fn else "ม.4" if '4' in fn else "ม.5" if '5' in fn else "ม.6" if '6' in fn else "ทั่วไป"
        for _, r in df_t.iterrows():
            txt, subj = str(r.get('เนื้อหา','')), str(r.get('เรื่อง',''))
            sid, act = re.search(r'เลขที่\s*(\d+)', txt), re.search(r'กิจกรรม(?:ที่)?\s*1\.(\d+)', subj + txt)
            if sid and act:
                all_recs.append({'ระดับ': lv, 'เลขที่': int(sid.group(1)), 'ชื่อ-นามสกุล': clean_name(txt), 'กิจกรรม': f"กิจกรรมที่ 1.{act.group(1)}"})
    except: continue

if all_recs:
    st.subheader("📊 2. ตารางสรุปภาพรวม (Auto-Summary)")
    final_df = pd.DataFrame(all_recs).drop_duplicates()
    pivot = final_df.pivot_table(index=['ระดับ', 'เลขที่', 'ชื่อ-นามสกุล'], columns='กิจกรรม', values='กิจกรรม', aggfunc=lambda x: '✔').fillna('-').reset_index()
    pivot = pivot.sort_values(by=['ระดับ', 'เลขที่'])

    st.dataframe(pivot, use_container_width=True, hide_index=True)

    # ปุ่มดาวน์โหลด Excel
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        pivot.to_excel(writer, index=False, sheet_name='Summary_Report')
    
    st.download_button(
        label="📥 ดาวน์โหลดไฟล์สรุปเป็น Excel",
        data=output.getvalue(),
        file_name=f"รายงานสรุปงาน_ครูตระกูล_{datetime.now().strftime('%d-%m-%Y')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
else:
    st.warning("⚠️ ยังไม่มีข้อมูล โปรดอัปโหลดไฟล์ Padlet เพื่อเริ่มการสรุป")

st.markdown("<hr><center style='color:grey; font-size:0.8rem;'>© 2026 Teacher Assistant Tool by ครูตระกูล บุญชิต</center>", unsafe_allow_html=True)
