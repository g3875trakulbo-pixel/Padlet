import streamlit as st
import pandas as pd
import re, os, base64

# --- 1. การตั้งค่าหน้าตา ---
st.set_page_config(page_title="ระบบครูตระกูล", layout="wide")

def get_b64(file):
    if os.path.exists(file):
        try:
            with open(file, "rb") as f:
                return base64.b64encode(f.read()).decode()
        except: return None
    return None

img_b64 = get_b64("teacher.jpg")
placeholder_img = "https://cdn-icons-png.flaticon.com/512/3429/3429433.png"

# --- 2. แยก CSS เพื่อป้องกัน Syntax Error ---
st.markdown("""
<style>
    .main-header { background-color: #1b5e20; padding: 15px; border-radius: 10px 10px 0 0; text-align: center; color: white; }
    .teacher-card { background-color: #ffffff; border: 2px solid #e0e0e0; border-radius: 12px; padding: 20px; margin: 15px 0; display: flex; align-items: center; gap: 25px; }
    .teacher-img { width: 110px; height: 110px; border-radius: 50%; border: 4px solid #4caf50; object-fit: cover; }
    .level-header { background-color: #4caf50; color: white; padding: 10px 20px; border-radius: 8px; margin-top: 30px; margin-bottom: 10px; font-size: 1.5rem; }
</style>
""", unsafe_allow_html=True)

# ส่วนโปรไฟล์
img_src = f"data:image/jpeg;base64,{img_b64}" if img_b64 else placeholder_img
st.markdown(f"""
<div class="main-header"><h2 style="margin:0;">📋 ระบบเช็คงานอัจฉริยะ</h2></div>
<div class="teacher-card">
    <img src="{img_src}" class="teacher-img">
    <div>
        <h1 style="margin:0; color: #1b5e20;">ครูตระกูล บุญชิต</h1>
        <p style="margin:0; color: #666;">โรงเรียนตระกาศประชาสามัคคี | ภาคเรียนที่ 2/2568</p>
    </div>
</div>
""", unsafe_allow_html=True)

# --- 3. ฟังก์ชันล้างชื่อแบบเข้มงวดที่สุด ---
def strict_clean_name(n):
    if pd.isna(n): return "ไม่ระบุชื่อ"
    n = str(n).replace('\n', ' ').strip()
    
    # [1] ตัดคำนำหน้าชื่อ
    prefixes = ['นาย', 'นางสาว', 'นาง', 'เด็กชาย', 'เด็กหญิง', r'น\.ส\.', r'ด\.ช\.', r'ด\.ญ\.', r'น\.ส', r'ด\.ช', r'ด\.ญ', 'นส ', 'ดช ', 'ดญ ']
    for p in prefixes:
        n = re.sub(f'^{p}\s*', '', n)
    
    # [2] ตัดข้อความหลังนามสกุล (กลุ่ม/เลขที่/ชั้น/สมาชิก/ชื่อเล่น)
    n = re.split(r'กลุ่ม|เลขที่|กิจกรรม|ชั้น|ม\.|เลข|No\.|#|ชื่อเล่น|สมาชิก', n)[0]
    
    # [3] ล้างสัญลักษณ์และตัวเลขหัว-ท้าย
    n = re.sub(r'^[.\-\s0-9]+', '', n)
    n = re.sub(r'[.\-\s0-9]+$', '', n)
    
    return n.strip()

# --- 4. ประมวลผลและสร้างตาราง ---
uploaded_files = st.file_uploader("📂 อัปโหลดไฟล์จาก Padlet", type=["csv", "xlsx"], accept_multiple_files=True)

if uploaded_files:
    all_rows = []
    # รายชื่อกิจกรรม 1.1 - 1.14
    full_acts = [f"กิจกรรมที่ 1.{i}" for i in range(1, 15)]

    for f in uploaded_files:
        try:
            if f.name.endswith('.csv'):
                df = pd.read_csv(f, encoding='utf-8-sig')
            else:
                df = pd.read_excel(f)
            
            lv_m = re.search(r'([3-6])', f.name)
            level = f"ม.{lv_m.group(1)}" if lv_m else "ทั่วไป"
            file_name = f.name.split('.')[0]
            
            for _, row in df.iterrows():
                # รวมข้อมูลทุกช่องเพื่อค้นหา เลขที่ และ กิจกรรม
                txt = " ".join(map(str, row.values))
                sid = re.search(r'เลขที่\s*(\d+)', txt)
                act = re.search(r'กิจกรรม(?:ที่)?\s*1\.(\d+)', txt)
                grp = re.search(r'กลุ่มที่\s*(\d+)', txt)
                
                if sid and act:
                    grp_info = f"กลุ่มที่ {grp.group(1)} {file_name}" if grp else file_name
                    # ดึงเนื้อหามาล้างชื่อ
                    raw_name = row.get('เนื้อหา', row.get('เรื่อง', 'ไม่ระบุชื่อ'))
                    all_rows.append({
                        'เลขที่': int(sid.group(1)),
                        'ระดับ': level,
                        'ชื่อ-นามสกุล': strict_clean_name(raw_name),
                        'ชื่อกลุ่ม': grp_info.strip(),
                        'กิจกรรม': f"กิจกรรมที่ 1.{act.group(1)}"
                    })
        except: continue

    if all_rows:
        df_all = pd.DataFrame(all_rows).drop_duplicates()
        for lv in ["ม.3", "ม.4", "ม.5", "ม.6"]:
            df_lv = df_all[df_all['ระดับ'] == lv]
            if not df_lv.empty:
                st.markdown(f'<div class="level-header">🟢 ชั้น {lv}</div>', unsafe_allow_html=True)
                
                # ทำ Pivot และเติมกิจกรรมให้ครบ
                pivot = df_lv.pivot_table(index=['เลขที่', 'ระดับ', 'ชื่อ-นามสกุล', 'ชื่อกลุ่ม'], 
                                          columns='กิจกรรม', values='กิจกรรม', aggfunc=lambda x: 1).fillna(0)
                
                for a in full_acts:
                    if a not in pivot.columns: pivot[a] = 0
                
                pivot = pivot[full_acts]
                pivot['คะแนนรวม'] = pivot.sum(axis=1).astype(int)
                res = pivot.replace({1:'✔', 0:'-'}).reset_index().sort_values('เลขที่')
                
                # จัดลำดับคอลัมน์
                cols = ['เลขที่', 'ระดับ', 'ชื่อ-นามสกุล', 'ชื่อกลุ่ม'] + full_acts + ['คะแนนรวม']
                res = res[cols]
                
                # แสดงตาราง (พื้นขาว ตัวหนังสือดำ)
                st.dataframe(
                    res.style.set_properties(**{'background-color': 'white', 'color': 'black', 'text-align': 'center'})
                    .set_properties(subset=['ชื่อ-นามสกุล', 'ชื่อกลุ่ม'], **{'text-align': 'left'})
                    .set_properties(subset=['คะแนนรวม'], **{'background-color': '#e8f5e9', 'font-weight': 'bold'})
                    .set_table_styles([{'selector': 'th', 'props': [('background-color', '#1b5e20'), ('color', 'white')]}])
                , use_container_width=True, hide_index=True)
                
                st.download_button(f"📥 โหลดไฟล์ {lv}", res.to_csv(index=False).encode('utf-8-sig'), f"Report_{lv}.csv")
    else:
        st.info("💡 กรุณาอัปโหลดไฟล์ที่มีข้อมูลนักเรียนครับ")
