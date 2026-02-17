import streamlit as st
import pandas as pd
import re, os, base64

# --- 1. การตั้งค่าหน้าตาแอป (UI & Theme) ---
st.set_page_config(page_title="ระบบครูตระกูล v9.4", layout="wide")

def get_b64(file):
    if os.path.exists(file):
        try:
            with open(file, "rb") as f:
                return base64.b64encode(f.read()).decode()
        except: return None
    return None

img_b64 = get_b64("teacher.jpeg")
placeholder_img = "https://cdn-icons-png.flaticon.com/512/3429/3429433.png"

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Sarabun', sans-serif; background-color: #ffffff; }
    .main-header { background-color: #1b5e20; padding: 25px; border-radius: 15px; text-align: center; color: white; border-bottom: 5px solid #4caf50; margin-bottom: 20px;}
    .teacher-card { background-color: #f8f9fa; border: 1px solid #dee2e6; border-radius: 15px; padding: 30px; margin-bottom: 35px; display: flex; align-items: center; gap: 30px; }
    .teacher-img { width: 130px; height: 130px; border-radius: 50%; border: 5px solid #1b5e20; object-fit: cover; }
    
    /* ตารางใหม่: พื้นขาว ตัวหนังสือปกติ (ไม่หนา) */
    .stDataFrame div[data-testid="stTable"] { background-color: #ffffff !important; }
    td, th { color: #000000 !important; font-weight: 400 !important; border: 0.5px solid #eeeeee !important; }
    th { font-weight: 700 !important; background-color: #f8f9fa !important; }
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ส่วนหัวโปรไฟล์ครูตระกูล
img_src = f"data:image/jpeg;base64,{img_b64}" if img_b64 else placeholder_img
st.markdown(f"""
<div class="main-header"><h2 style="margin:0; color:white; font-weight:700;">📋 ระบบรายงานผลคะแนน Padlet อัจฉริยะ</h2></div>
<div class="teacher-card">
    <img src="{img_src}" class="teacher-img">
    <div>
        <h1 style="margin:0; font-size: 2.5rem; color: #1b5e20; font-weight:700;">ครูตระกูล บุญชิต</h1>
        <p style="margin:0; font-size: 1.2rem; color: #333;">ลำดับที่ | เลขที่ | ส่วน | ชื่อ - นามสกุล (ตรงตามทะเบียน) | ตารางพื้นขาว</p>
    </div>
</div>
""", unsafe_allow_html=True)

# --- 2. ส่วนการอัปโหลดไฟล์ (รองรับหลายไฟล์) ---
col_m, col_p = st.columns(2)
with col_m:
    st.subheader("1️⃣ ไฟล์รายชื่อนักเรียน (Master)")
    master_files = st.file_uploader("อัปโหลดไฟล์รายชื่อ (Excel/CSV)", type=["xlsx", "csv"], accept_multiple_files=True, key="master")

with col_p:
    st.subheader("2️⃣ ไฟล์ส่งงาน (จาก Padlet)")
    padlet_files = st.file_uploader("อัปโหลดไฟล์จาก Padlet (Excel/CSV)", type=["xlsx", "csv"], accept_multiple_files=True, key="padlet")

# --- 3. ประมวลผลรายชื่อจาก Master List (ดึงชื่อพร้อมคำนำหน้า) ---
student_db = {}
if master_files:
    for mf in master_files:
        try:
            m_df = pd.read_csv(mf, encoding='utf-8-sig') if mf.name.endswith('.csv') else pd.read_excel(mf)
            # ค้นหาคอลัมน์จากไฟล์จริง (รองรับ "เลขที่" และ "ชื่อ - นามสกุล")
            c_sid = next((c for c in m_df.columns if "เลขที่" in str(c)), None)
            c_name = next((c for c in m_df.columns if "ชื่อ" in str(c)), None)
            
            if c_sid and c_name:
                for _, r in m_df.iterrows():
                    try:
                        # จัดการเลขที่ (ถ้าเป็น 1.0 ให้เป็น 1)
                        raw_sid = str(r[c_sid]).split('.')[0]
                        s_id = int(re.sub(r'\D', '', raw_sid))
                        s_full_name = str(r[c_name]).strip()
                        if s_full_name and s_full_name != "nan":
                            student_db[s_id] = s_full_name # เก็บชื่อเต็มตามต้นฉบับ
                    except: continue
        except: st.error(f"ไม่สามารถอ่านไฟล์รายชื่อ: {mf.name}")
    if student_db:
        st.success(f"✅ เชื่อมต่อฐานข้อมูลรายชื่อสำเร็จ {len(student_db)} คน")

# --- 4. ประมวลผลไฟล์ Padlet และสร้างตาราง ---
if padlet_files:
    all_data = []
    full_acts = [f"1.{i}" for i in range(1, 15)]

    for f in padlet_files:
        try:
            p_df = pd.read_csv(f, encoding='utf-8-sig') if f.name.endswith('.csv') else pd.read_excel(f)
            col_sec = next((c for c in p_df.columns if any(k in str(c) for k in ["ส่วน", "Section"])), None)
            
            for _, row in p_df.iterrows():
                row_str = " ".join(map(str, row.values))
                # ค้นหาเลขที่และเลขกิจกรรมจากข้อความในแถวนั้น
                sid_match = re.search(r'(?:เลขที่|No\.|#)\s*(\d+)', row_str)
                act_match = re.search(r'1\.(\d{1,2})', row_str)
                
                if sid_match and act_match:
                    sid = int(sid_match.group(1))
                    # ดึงชื่อจาก Master (จะได้คำนำหน้าตรงตามทะเบียน)
                    final_name = student_db.get(sid, f"⚠️ ไม่พบในรายชื่อ (เลขที่ {sid})")
                    
                    raw_section = str(row[col_sec]).strip() if col_sec else ""
                    section_display = raw_section if raw_section not in ["", "nan"] else f.name.split('.')[0]
                    
                    all_data.append({
                        'เลขที่': sid,
                        'ส่วน': section_display,
                        'ชื่อ - นามสกุล': final_name,
                        'กิจกรรม': f"1.{act_match.group(1)}"
                    })
        except: continue

    if all_data:
        df_final = pd.DataFrame(all_data).drop_duplicates()
        pivot = df_final.pivot_table(index=['เลขที่', 'ส่วน', 'ชื่อ - นามสกุล'], columns='กิจกรรม', aggfunc='size', fill_value=0)
        
        # ตรวจสอบกิจกรรมให้ครบ 1.1 - 1.14
        for act in full_acts:
            if act not in pivot.columns: pivot[act] = 0
            
        res = pivot[full_acts].copy()
        res['รวม'] = res.sum(axis=1)
        res = res.reset_index().sort_values('เลขที่').reset_index(drop=True)
        
        # เพิ่มคอลัมน์ลำดับที่ 1-N หน้าสุด
        res.insert(0, 'ลำดับที่', res.index + 1)
        
        # เรียงลำดับคอลัมน์: ลำดับที่ -> เลขที่ -> ส่วน -> ชื่อ - นามสกุล -> กิจกรรม... -> รวม
        cols_order = ['ลำดับที่', 'เลขที่', 'ส่วน', 'ชื่อ - นามสกุล'] + full_acts + ['รวม']
        
        st.dataframe(
            res[cols_order].style.set_properties(**{'background-color': '#ffffff', 'color': '#000000', 'text-align': 'center'})
            .set_properties(subset=['ส่วน', 'ชื่อ - นามสกุล'], **{'text-align': 'left'})
            .format({a: lambda x: '✔' if x >= 1 else '-' for a in full_acts}),
            use_container_width=True, hide_index=True
        )
