import streamlit as st
import pandas as pd
import re
import os

# --- 1. ตั้งค่าหน้าเว็บ ---
st.set_page_config(page_title="ระบบสรุปงานครูเจมส์", layout="wide")

# สไตล์ Dashboard
st.markdown("""
    <style>
    .header-box {
        background-color:#1b5e20; padding:30px; border-radius:20px; 
        text-align:center; color:white; border: 3px solid #ffffff; 
        box-shadow: 0px 10px 20px rgba(0,0,0,0.2);
    }
    </style>
    <div class="header-box">
        <h1 style="margin:0;">📊 ระบบสรุปผลการส่งงาน</h1>
        <p style="margin-top:10px; font-size:1.2rem;">โรงเรียนตระกาศประชาสามัคคี</p>
    </div>
""", unsafe_allow_html=True)

# --- 2. ส่วนรูปภาพโปรไฟล์ (แก้ไขจุดนี้) ---
st.markdown("<br>", unsafe_allow_html=True)
_, col_m, _ = st.columns([2, 1, 2])
with col_m:
    # ค้นหาไฟล์ภาพที่ชื่อคล้ายกัน (เผื่อคุณครูใช้ .png หรือ .jpeg)
    image_files = [f for f in os.listdir('.') if f.lower().startswith('teacher') and f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    
    if image_files:
        # ใช้ไฟล์ภาพที่เจอไฟล์แรก
        st.image(image_files[0], use_container_width=True, caption="คุณครูตระกูล บุญชิต")
    else:
        # ถ้าหาไม่เจอจริงๆ จะโชว์ไอคอนครูแทน
        st.markdown("<h1 style='text-align:center; font-size:100px;'>👨‍🏫</h1>", unsafe_allow_html=True)
        st.info("💡 ทิป: อัปโหลดรูปครูและตั้งชื่อว่า teacher.jpg ไว้ในโฟลเดอร์เดียวกับโค้ดนะครับ")

st.divider()

# --- 3. ฟังก์ชันล้างชื่อ (ตัดคำนำหน้าชื่อออก 100%) ---
def clean_student_name(name):
    if not name or pd.isna(name): return "ไม่ระบุชื่อ"
    name = str(name).split('\n')[0].strip()
    prefixes = ['นาย', 'นางสาว', 'นาง', 'เด็กชาย', 'เด็กหญิง', 'น.ส.', 'น.ส', 'ด.ช.', 'ด.ช', 'ด.ญ.', 'ด.ญ']
    for p in prefixes:
        # ใช้ regex ตัดคำนำหน้าออกจากต้นประโยคแบบเด็ดขาด
        name = re.sub(f'^{p}\s*', '', name)
    # ล้างจุดหรือขีดที่อาจหลงเหลือ
    name = re.sub(r'^[.\-\s]+', '', name)
    return name.strip()

# --- 4. ส่วนอัปโหลดและประมวลผล ---
uploaded_files = st.file_uploader("📂 เลือกไฟล์จาก Padlet (CSV หรือ Excel)", type=["csv", "xlsx"], accept_multiple_files=True)

if uploaded_files:
    all_records = []
    for f in uploaded_files:
        try:
            df = pd.read_csv(f, encoding='utf-8-sig') if f.name.endswith('.csv') else pd.read_excel(f)
        except: continue
        
        lv = "ม.3" if '3' in f.name else "ม.4" if '4' in f.name else "ม.5" if '5' in f.name else "ม.6" if '6' in f.name else "ทั่วไป"
        
        for _, row in df.iterrows():
            # รวมข้อความเพื่อหาข้อมูลเลขที่และกิจกรรม
            all_text = " ".join([str(val) for val in row.values])
            sid = re.search(r'เลขที่\s*(\d+)', all_text)
            act = re.search(r'กิจกรรม(?:ที่)?\s*1\.(\d+)', all_text)
            
            if sid and act:
                raw_name = str(row.get('เนื้อหา', row.get('เรื่อง', '')))
                all_records.append({
                    'ระดับ': lv, 
                    'เลขที่': int(sid.group(1)), 
                    'ชื่อ-นามสกุล': clean_student_name(raw_name), 
                    'กิจกรรม': f"กิจกรรมที่ 1.{act.group(1)}"
                })

    if all_records:
        df_final = pd.DataFrame(all_records).drop_duplicates()
        pivot = df_final.pivot_table(index=['ระดับ', 'เลขที่', 'ชื่อ-นามสกุล'], 
                                       columns='กิจกรรม', values='กิจกรรม', 
                                       aggfunc=lambda x: '✔').fillna('-').reset_index()
        pivot = pivot.sort_values(by=['ระดับ', 'เลขที่'])
        
        st.subheader("✅ ตารางสรุปรายบุคคล (ล้างชื่อแล้ว)")
        st.dataframe(pivot, use_container_width=True, hide_index=True)
        
        # ปุ่มดาวน์โหลด
        st.download_button("📥 ดาวน์โหลดรายงานสรุป", pivot.to_csv(index=False).encode('utf-8-sig'), "Summary_Report.csv", "text/csv")
