import streamlit as st
import pandas as pd
import re, os, base64
from io import BytesIO

# --- 1. การตั้งค่า UI & Print Style ---
st.set_page_config(page_title="ระบบครูตระกูล v9.7", layout="wide")

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
    
    /* ตารางสำหรับปริ้น: เส้นขอบชัดเจน พื้นขาว ตัวหนังสือดำ */
    .stDataFrame div[data-testid="stTable"] { background-color: #ffffff !important; }
    td, th { color: #000000 !important; font-weight: 400 !important; border: 1px solid #dddddd !important; }
    th { font-weight: 700 !important; background-color: #f1f3f4 !important; }
    
    .room-label { background-color: #e8f5e9; padding: 15px; border-left: 10px solid #2e7d32; border-radius: 5px; margin-top: 40px; font-size: 1.5rem; font-weight: bold; color: #1b5e20; display: flex; justify-content: space-between; align-items: center; }
</style>
""", unsafe_allow_html=True)

# ส่วนหัวโปรไฟล์
img_src = f"data:image/jpeg;base64,{img_b64}" if img_b64 else placeholder_img
st.markdown(f"""
<div class="main-header"><h2 style="margin:0; color:white; font-weight:700;">📋 ระบบรายงานผลและเตรียมใบปริ้นรายห้อง (v9.7)</h2></div>
<div class="teacher-card">
    <img src="{img_src}" class="teacher-img">
    <div>
        <h1 style="margin:0; font-size: 2.5rem; color: #1b5e20; font-weight:700;">ครูตระกูล บุญชิต</h1>
        <p style="margin:0; font-size: 1.2rem; color: #333;">แยกตารางเป็นห้อง | พร้อมปุ่มดาวน์โหลดเพื่อปริ้น A4</p>
    </div>
</div>
""", unsafe_allow_html=True)

# --- 2. ส่วนอัปโหลดไฟล์ ---
col_m, col_p = st.columns(2)
with col_m:
    st.subheader("📂 1. อัปโหลดรายชื่อห้องเรียน")
    master_files = st.file_uploader("ไฟล์รายชื่อ (ม.3-1, ม.3-2, ม.3-3...)", type=["xlsx", "csv"], accept_multiple_files=True)
with col_p:
    st.subheader("📂 2. อัปโหลดงานจาก Padlet")
    padlet_files = st.file_uploader("ไฟล์ Excel จาก Padlet", type=["xlsx", "csv"], accept_multiple_files=True)

# --- 3. ประมวลผล Master List แยกห้อง ---
rooms_db = {} 
if master_files:
    for mf in master_files:
        try:
            r_name = mf.name.replace('.xlsx', '').replace('.csv', '').split(' - ')[0]
            m_df = pd.read_csv(mf, encoding='utf-8-sig') if mf.name.endswith('.csv') else pd.read_excel(mf)
            c_sid = next((c for c in m_df.columns if "เลขที่" in str(c)), None)
            c_name = next((c for c in m_df.columns if "ชื่อ" in str(c)), None)
            if c_sid and c_name:
                students = []
                for _, r in m_df.iterrows():
                    try:
                        sid = int(float(str(r[c_sid]).split('.')[0]))
                        sname = str(r[c_name]).strip()
                        if sname and sname != "nan": students.append({'เลขที่': sid, 'ชื่อ - นามสกุล': sname})
                    except: continue
                rooms_db[r_name] = pd.DataFrame(students)
        except: continue

# --- 4. ประมวลผล Padlet & แสดงผลเพื่อการปริ้น ---
if padlet_files and rooms_db:
    all_subs = []
    full_acts = [f"1.{i}" for i in range(1, 15)]

    for f in padlet_files:
        try:
            p_df = pd.read_csv(f, encoding='utf-8-sig') if f.name.endswith('.csv') else pd.read_excel(f)
            col_sec = next((c for c in p_df.columns if any(k in str(c) for k in ["ส่วน", "Section"])), None)
            for _, row in p_df.iterrows():
                row_str = " ".join(map(str, row.values))
                sid_m = re.search(r'(?:เลขที่|No\.|#)\s*(\d+)', row_str)
                act_m = re.search(r'1\.(\d{1,2})', row_str)
                if sid_m and act_m:
                    sid = int(sid_m.group(1))
                    all_subs.append({'เลขที่': sid, 'ส่วน': str(row[col_sec]).strip() if col_sec else "", 'กิจกรรม': f"1.{act_m.group(1)}"})
        except: continue

    if all_subs:
        df_sub = pd.DataFrame(all_subs).drop_duplicates()
        pivot = df_sub.pivot_table(index='เลขที่', columns='กิจกรรม', aggfunc='size', fill_value=0)
        sec_map = df_sub.groupby('เลขที่')['ส่วน'].last()

        for room, room_list in rooms_db.items():
            # รวมข้อมูล
            final_df = room_list.merge(pivot, on='เลขที่', how='left').fillna(0)
            final_df['ส่วน'] = final_df['เลขที่'].map(sec_map).fillna("-")
            for act in full_acts:
                if act not in final_df.columns: final_df[act] = 0
            
            final_df['รวม'] = final_df[full_acts].sum(axis=1)
            final_df = final_df.sort_values('เลขที่').reset_index(drop=True)
            final_df.insert(0, 'ลำดับที่', final_df.index + 1)
            cols = ['ลำดับที่', 'เลขที่', 'ส่วน', 'ชื่อ - นามสกุล'] + full_acts + ['รวม']
            final_df = final_df[cols]

            # ส่วนแสดงผลหน้าเว็บ
            st.markdown(f'<div class="room-label"><span>🏫 ห้อง: {room}</span></div>', unsafe_allow_html=True)
            
            # ปุ่มดาวน์โหลดไฟล์สำหรับปริ้น
            towrite = BytesIO()
            final_df.to_excel(towrite, index=False, engine='xlsxwriter')
            st.download_button(label=f"📥 ดาวน์โหลดไฟล์ปริ้น {room}", data=towrite.getvalue(), file_name=f"ใบเช็คงาน_{room}.xlsx", mime="application/vnd.ms-excel")

            st.dataframe(
                final_df.style.set_properties(**{'background-color': '#ffffff', 'color': '#000000', 'text-align': 'center'})
                .set_properties(subset=['ส่วน', 'ชื่อ - นามสกุล'], **{'text-align': 'left'})
                .format({a: lambda x: '✔' if x >= 1 else '-' for a in full_acts}),
                use_container_width=True, hide_index=True
            )
else:
    st.info("💡 กรุณาอัปโหลดทั้ง 'ไฟล์รายชื่อ' และ 'ไฟล์ Padlet' เพื่อสร้างใบเช็คงานรายห้องครับ")
