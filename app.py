import streamlit as st
import pandas as pd
import re
import os

# --- ส่วนหัวแอป ---
st.set_page_config(page_title="ระบบสรุปงานครูเจมส์", layout="wide")
st.markdown("<h1 style='text-align: center; color: #1b5e20;'>📊 ระบบสรุปผลการส่งงาน</h1>", unsafe_allow_html=True)

# --- ฟังก์ชันตัดคำนำหน้าชื่อ ---
def remove_prefix(name):
    name = str(name).strip()
    prefixes = ['นาย', 'นางสาว', 'น.ส.', 'นาง', 'เด็กชาย', 'เด็กหญิง', 'ด.ช.', 'ด.ญ.']
    for p in prefixes:
        if name.startswith(p):
            name = name[len(p):].strip()
            break
    return name

# --- ปุ่มอัปโหลด ---
uploaded_files = st.file_uploader("เลือกไฟล์จาก Padlet (CSV หรือ Excel)", type=["csv", "xlsx"], accept_multiple_files=True)

if uploaded_files:
    all_records = []
    for f in uploaded_files:
        # อ่านไฟล์รองรับทั้ง Excel และ CSV (ภาษาไทย)
        try:
            if f.name.endswith('.csv'):
                df = pd.read_csv(f, encoding='utf-8-sig')
            else:
                df = pd.read_excel(f)
        except:
            st.error(f"ไม่สามารถอ่านไฟล์ {f.name} ได้")
            continue
        
        # ค้นหาระดับจากชื่อไฟล์
        lv = "ม.3" if '3' in f.name else "ม.4" if '4' in f.name else "ม.5" if '5' in f.name else "ม.6" if '6' in f.name else "ทั่วไป"
        
        for _, row in df.iterrows():
            # รวมข้อมูลจากทุกคอลัมน์เพื่อค้นหา
            txt = " ".join([str(val) for val in row.values])
            
            # ดึงเลขที่และกิจกรรม
            sid = re.search(r'เลขที่\s*(\d+)', txt)
            act = re.search(r'กิจกรรม(?:ที่)?\s*1\.(\d+)', txt)
            
            if sid and act:
                # ดึงชื่อจากคอลัมน์ "เนื้อหา" หรือบรรทัดแรก
                raw_name = str(row.get('เนื้อหา', '')).split('\n')[0].strip()
                if not raw_name or raw_name == 'nan':
                    raw_name = "ไม่ระบุชื่อ"
                
                clean_name = remove_prefix(raw_name)
                
                all_records.append({
                    'ระดับ': lv, 
                    'เลขที่': int(sid.group(1)), 
                    'ชื่อ-นามสกุล': clean_name, 
                    'กิจกรรม': f"กิจกรรมที่ 1.{act.group(1)}"
                })

    if len(all_records) > 0:
        df_final = pd.DataFrame(all_records).drop_duplicates()
        
        # ตรวจสอบว่ามีคอลัมน์ 'กิจกรรม' หรือไม่ก่อนทำ Pivot
        if 'กิจกรรม' in df_final.columns:
            pivot = df_final.pivot_table(index=['ระดับ', 'เลขที่', 'ชื่อ-นามสกุล'], 
                                           columns='กิจกรรม', values='กิจกรรม', 
                                           aggfunc=lambda x: '✔').fillna('-').reset_index()
            
            st.subheader("✅ ตารางสรุปรายบุคคล")
            st.dataframe(pivot, use_container_width=True)
            
            # ปุ่มดาวน์โหลด Excel
            csv = pivot.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 ดาวน์โหลดรายงานสรุป (CSV/Excel)", csv, "Summary_Report.csv", "text/csv")
    else:
        st.warning("⚠️ ไม่พบข้อมูลที่ตรงตามเงื่อนไข (ต้องมีคำว่า 'เลขที่' และ 'กิจกรรม 1.x')")
