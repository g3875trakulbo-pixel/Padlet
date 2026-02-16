import streamlit as st
import pandas as pd
import re
import os

# --- ส่วนหัวแอป ---
st.set_page_config(page_title="ระบบสรุปงานครูตระกูล", layout="wide")
st.markdown("<h1 style='text-align: center; color: #1b5e20;'>📊 ระบบสรุปผลการส่งงาน</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>โดย คุณครูตระกูล บุญชิต</p>", unsafe_allow_html=True)

# --- ปุ่มอัปโหลด ---
uploaded_files = st.file_uploader("เลือกไฟล์จาก Padlet (CSV หรือ Excel)", type=["csv", "xlsx"], accept_multiple_files=True)

if uploaded_files:
    all_records = []
    for f in uploaded_files:
        df = pd.read_csv(f, encoding='utf-8-sig') if f.name.endswith('.csv') else pd.read_excel(f)
        
        # ค้นหาระดับจากชื่อไฟล์
        lv = "ม.3" if '3' in f.name else "ม.4" if '4' in f.name else "ม.5" if '5' in f.name else "ม.6" if '6' in f.name else "ทั่วไป"
        
        for _, row in df.iterrows():
            txt = str(row.get('เนื้อหา', '')) + str(row.get('เรื่อง', ''))
            
            # ดึงเลขที่และกิจกรรม (ใช้สูตรฉลาดขึ้น)
            sid = re.search(r'เลขที่\s*(\d+)', txt)
            act = re.search(r'กิจกรรม(?:ที่)?\s*1\.(\d+)', txt)
            
            if sid and act:
                # ดึงชื่อนักเรียนจากบรรทัดแรกของเนื้อหา
                name = str(row.get('เนื้อหา', '')).split('\n')[0].strip()
                all_records.append({
                    'ระดับ': lv, 'เลขที่': int(sid.group(1)), 
                    'ชื่อ-นามสกุล': name[:40], 'กิจกรรม': f"กิจกรรมที่ 1.{act.group(1)}"
                })

    if all_records:
        df_final = pd.DataFrame(all_records).drop_duplicates()
        # ทำตารางสรุป
        pivot = df_final.pivot_table(index=['ระดับ', 'เลขที่', 'ชื่อ-นามสกุล'], 
                                       columns='กิจกรรม', values='กิจกรรม', 
                                       aggfunc=lambda x: '✔').fillna('-').reset_index()
        
        st.subheader("✅ ตารางสรุปรายบุคคล")
        st.dataframe(pivot, use_container_width=True)
        
        # ปุ่มดาวน์โหลด Excel
        st.download_button("📥 ดาวน์โหลดรายงานสรุป (Excel)", pivot.to_csv(index=False).encode('utf-8-sig'), "Summary_Report.csv")
    else:
        st.warning("⚠️ ไม่พบข้อมูลเลขที่ในไฟล์ที่อัปโหลด")
