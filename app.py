import streamlit as st
import pandas as pd
import re, os, base64

# --- 1. การตั้งค่าหน้าเว็บและเฮดเดอร์ ---
st.set_page_config(page_title="ระบบครูตระกูล", layout="wide")

def get_img(file):
    if os.path.exists(file):
        with open(file, "rb") as f: return base64.b64encode(f.read()).decode()
    return None

img_data = get_img("teacher.jpg")
head = f"""
<div style="background: linear-gradient(135deg, #1b5e20, #2e7d32); padding: 25px; border-radius: 15px; text-align: center; color: white; border: 2px solid #fff; box-shadow: 0 4px 10px rgba(0,0,0,0.2);">
    {f'<img src="data:image/jpeg;base64,{img_data}" style="width:90px; height:90px; border-radius:50%; border:2px solid gold; object-fit:cover; margin-bottom:10px;">' if img_data else ''}
    <h2 style="margin:0;">📋 ระบบเช็คงานอัจฉริยะ ครูตระกูล บุญชิต</h2>
    <p style="margin:5px 0; opacity:0.9;">โรงเรียนตระกาศประชาสามัคคี | ภาคเรียนที่ 2/2568</p>
    <div style="background:#689f38; display:inline-block; padding:2px 15px; border-radius:20px; font-size:0.8rem;">BY KRU JAMES</div>
</div><br>"""
st.markdown(head, unsafe_allow_html=True)

# --- 2. ฟังก์ชันจัดการชื่อและสี (ตัดคำนำหน้าออกหมดจด) ---
def clean_name(n):
    n = str(n).split('\n')[0].strip()
    for p in ['นาย','นางสาว','นาง','เด็กชาย','เด็กหญิง','น.ส.','ด.ช.','ด.ญ.','น.ส','ด.ช','ด.ญ']:
        n = re.sub(f'^{p}\s*', '', n)
    return re.sub(r'^[.\-\s0-9]+', '', n).strip()

def row_color(row):
    colors = {'ม.3':'#fce4ec', 'ม.4':'#fff3e0', 'ม.5':'#e3f2fd', 'ม.6':'#fffde7'}
    return [f'background-color: {colors.get(row["ระดับ"], "")}'] * len(row)

# --- 3. ส่วนประมวลผลไฟล์ ---
files = st.file_uploader("📂 อัปโหลดไฟล์จาก Padlet", type=["csv", "xlsx"], accept_multiple_files=True)

if files:
    data = []
    for f in files:
        df = pd.read_csv(f, encoding='utf-8-sig') if f.name.endswith('.csv') else pd.read_excel(f)
        lv = next((m for m in ["ม.3","ม.4","ม.5","ม.6"] if m[-1] in f.name), "ทั่วไป")
        for _, r in df.iterrows():
            txt = " ".join(map(str, r.values))
            sid, act = re.search(r'เลขที่\s*(\d+)', txt), re.search(r'กิจกรรม(?:ที่)?\s*1\.(\d+)', txt)
            if sid and act:
                data.append({'ระดับ': lv, 'เลขที่': int(sid.group(1)), 
                             'ชื่อ-นามสกุล': clean_name(r.get('เนื้อหา', r.get('เรื่อง', ''))),
                             'กิจกรรม': f"กิจกรรมที่ 1.{act.group(1)}"})
    
    if data:
        df_f = pd.DataFrame(data).drop_duplicates()
        pivot = df_f.pivot_table(index=['ระดับ','เลขที่','ชื่อ-นามสกุล'], columns='กิจกรรม', 
                                 values='กิจกรรม', aggfunc=lambda x:1).fillna(0)
        pivot['คะแนนรวม'] = pivot.sum(axis=1).astype(int)
        res = pivot.replace({1:'✔', 0:'-'}).reset_index().sort_values(['ระดับ','เลขที่'])
        
        st.dataframe(res.style.apply(row_color, axis=1), use_container_width=True, hide_index=True)
        st.download_button("📥 โหลดรายงาน (CSV)", res.to_csv(index=False).encode('utf-8-sig'), "Report_KruJames.csv")
    else: st.warning("ไม่พบข้อมูลเลขที่และกิจกรรม")
