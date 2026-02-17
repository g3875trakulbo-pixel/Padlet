import streamlit as st
import pandas as pd
import re, os, base64
from difflib import SequenceMatcher

# --- 1. การตั้งค่าหน้าตาแอปและ UI ---
st.set_page_config(page_title="ระบบครูตระกูล v8.3", layout="wide")

def get_b64(file):
    if os.path.exists(file):
        try:
            with open(file, "rb") as f:
                return base64.b64encode(f.read()).decode()
        except: return None
    return None

img_b64 = get_b64("teacher.jpg")
placeholder_img = "https://cdn-icons-png.flaticon.com/512/3429/3429433.png"

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Sarabun', sans-serif; background-color: #ffffff; }
    .main-header { background-color: #1b5e20; padding: 25px; border-radius: 15px 15px 0 0; text-align: center; color: white; border-bottom: 5px solid #4caf50; }
    .teacher-card { background-color: #f8f9fa; border: 1px solid #dee2e6; border-radius: 0 0 15px 15px; padding: 30px; margin-bottom: 35px; display: flex; align-items: center; gap: 30px; }
    .teacher-img { width: 130px; height: 130px; border-radius: 50%; border: 5px solid #1b5e20; object-fit: cover; }
    
    /* ตารางพื้นขาว ตัวหนังสือปกติ ไม่หนา */
    .stDataFrame div[data-testid="stTable"] { background-color: #ffffff !important; }
    td, th { color: #000000 !important; font-weight: 400 !important; border: 0.5px solid #eeeeee !important; }
    th { font-weight: 700 !important; background-color: #f8f9fa !important; }
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ส่วนโปรไฟล์เจ้าของแอป
img_src = f"data:image/jpeg;base64,{img_b64}" if img_b64 else placeholder_img
st.markdown(f"""
<div class="main-header"><h2 style="margin:0; color:white; font-weight:700;">📋 ระบบรายงานผลคะแนน Padlet อัจฉริยะ</h2></div>
<div class="teacher-card">
    <img src="{img_src}" class="teacher-img">
    <div>
        <h1 style="margin:0; font-size: 2.5rem; color: #1b5e20; font-weight:700;">ครูตระกูล บุญชิต</h1>
        <p style="margin:0; font-size: 1.2rem; color: #333 !important;">ดึงข้อมูลจากคอลัมน์ "ส่วน" | ลำดับที่ 1-N | ชื่อ 2 คำ</p>
    </div>
</div>
""", unsafe_allow_html=True)

# --- 2. ฟังก์ชันการดึงข้อมูลและกรองชื่อ ---
def strict_clean_name(n, sid):
    if pd.isna(n) or str(n).strip() == "": return f"⚠️ ไม่ระบุชื่อ (เลขที่ {sid})"
    n = re.sub('<[^<]+?>', '', str(n)).replace('\n', ' ').strip()
    prefixes = ['เด็กชาย', 'เด็กหญิง', 'นางสาว', 'นาย', 'นาง', r'ด\.ช\.', r'ด\.ญ\.', r'น\.ส\.']
    for p in prefixes: n = re.sub(f'^{p}', '', n).strip()
    n = re.sub(r'[0-9๐-๙]', '', n)
    n = re.sub(r'[^\u0E01-\u0E3A\u0E40-\u0E4E A-Za-z\s]', '', n)
    words = n.split()
    return f"{words[0]} {words[1]}" if len(words) >= 2 else (words[0] if len(words)==1 else f"⚠️ ไม่ระบุชื่อ (เลขที่ {sid})")

# --- 3. ส่วนประมวลผลไฟล์ ---
uploaded_files = st.file_uploader("📂 อัปโหลดไฟล์ Excel/CSV จาก Padlet", type=["csv", "xlsx"], accept_multiple_files=True)

if uploaded_files:
    all_raw_data = []
    full_acts = [f"1.{i}" for i in range(1, 15)]

    for f in uploaded_files:
        try:
            df = pd.read_csv(f, encoding='utf-8-sig') if f.name.endswith('.csv') else pd.read_excel(f)
            # ค้นหาคอลัมน์ "ส่วน"
            col_section = next((c for c in df.columns if "ส่วน" in str(c)), None)
            
            for _, row in df.iterrows():
                row_text = " ".join(map(str, row.values))
                sid_match = re.search(r'(?:เลขที่|No\.|#)\s*(\d+)', row_text)
                act_match = re.search(r'1\.(\d{1,2})', row_text)
                
                if sid_match and act_match:
                    sid = int(sid_match.group(1))
                    # ดึงค่าจาก "ส่วน" โดยตรง
                    raw_sec = str(row[col_section]).strip() if col_section else ""
                    section_display = raw_sec if raw_sec not in ["", "nan"] else f.name.split('.')[0]
                    # หาชื่อนักเรียน
                    name_cand = [row.get('Subject'), row.get('Body'), row.get('เนื้อหา')]
                    raw_name = next((str(x) for x in name_cand if pd.notna(x) and str(x).strip() != ""), "")
                    
                    all_raw_data.append({
                        'sid_key': sid, 'ส่วน': section_display,
                        'ชื่อ-นามสกุล': strict_clean_name(raw_name, sid),
                        'กิจกรรม': f"1.{act_match.group(1)}"
                    })
        except: continue

    if all_raw_data:
        df_master = pd.DataFrame(all_raw_data).drop_duplicates()
        pivot = df_master.pivot_table(index=['sid_key', 'ส่วน', 'ชื่อ-นามสกุล'], columns='กิจกรรม', aggfunc='size', fill_value=0)
        for act in full_acts: 
            if act not in pivot.columns: pivot[act] = 0
            
        res = pivot[full_acts].copy()
        res['รวม'] = res.sum(axis=1)
        res = res.reset_index().sort_values('sid_key').reset_index(drop=True)
        
        # ใส่ลำดับที่ 1-N
        res.insert(0, 'ลำดับที่', res.index + 1)
        
        # แสดงตาราง (เอาคอลัมน์เลขที่ sid_key ออก)
        cols_final = ['ลำดับที่', 'ส่วน', 'ชื่อ-นามสกุล'] + full_acts + ['รวม']
        
        st.dataframe(
            res[cols_final].style.set_properties(**{'background-color': '#ffffff', 'color': '#000000', 'text-align': 'center'})
            .set_properties(subset=['ส่วน', 'ชื่อ-นามสกุล'], **{'text-align': 'left'})
            .format({a: lambda x: '✔' if x >= 1 else '-' for a in full_acts}),
            use_container_width=True, hide_index=True
        )
