import streamlit as st
import pandas as pd
import re, os, base64

# --- 1. หน้าเว็บและดีไซน์ (รูปภาพ 90px พอดีสวย) ---
st.set_page_config(page_title="ระบบครูตระกูล", layout="wide")

def get_b64(file):
    if os.path.exists(file):
        with open(file, "rb") as f: return base64.b64encode(f.read()).decode()
    return None

img = get_b64("teacher.jpg")
st.markdown(f"""
<div style="background: linear-gradient(135deg, #1b5e20, #2e7d32); padding: 25px; border-radius: 15px; text-align: center; color: white; border: 2px solid #fff;">
    {f'<img src="data:image/jpeg;base64,{img}" style="width:90px; height:90px; border-radius:50%; border:2px solid gold; object-fit:cover; margin-bottom:10px;">' if img else ''}
    <h2 style="margin:0;">📋 ระบบเช็คงานอัจฉริยะ ครูตระกูล บุญชิต</h2>
    <p style="margin:5px 0; opacity:0.9;">โรงเรียนตระกาศประชาสามัคคี | ภาคเรียนที่ 2/2568</p>
</div><br>""", unsafe_allow_html=True)

# --- 2. ฟังก์ชันตัดคำนำหน้า (ล้างกริบ) ---
def clean_n(n):
    n = str(n).split('\n')[0].strip()
    for p in ['นาย','นางสาว','นาง','เด็กชาย','เด็กหญิง','น.ส.','ด.ช.','ด.ญ.','น.ส','ด.ช','ด.ญ']:
        n = re.sub(f'^{p}\s*', '', n)
    return re.sub(r'^[.\-\s0-9]+', '', n).strip()

# --- 3. ส่วนประมวลผล (ป้องกัน Error 100%) ---
files = st.file_uploader("📂 อัปโหลดไฟล์ Padlet", type=["csv", "xlsx"], accept_multiple_files=True)

if files:
    data = []
    for f in files:
        try:
            df = pd.read_csv(f, encoding='utf-8-sig') if f.name.endswith('.csv') else pd.read_excel(f)
            lv = next((m for m in ["ม.3","ม.4","ม.5","ม.6"] if m[-1] in f.name), "ทั่วไป")
            for _, r in df.iterrows():
                # รวมข้อมูลทุกคอลัมน์เพื่อความแม่นยำในการหา
                txt = " ".join(map(str, r.values))
                sid, act = re.search(r'เลขที่\s*(\d+)', txt), re.search(r'กิจกรรม(?:ที่)?\s*1\.(\d+)', txt)
                if sid and act:
                    data.append({
                        'ระดับ': lv, 'เลขที่': int(sid.group(1)), 
                        'ชื่อ-นามสกุล': clean_n(r.get('เนื้อหา', r.get('เรื่อง', ''))),
                        'กิจกรรม': f"กิจกรรมที่ 1.{act.group(1)}"
                    })
        except: continue
    
    if data:
        df_f = pd.DataFrame(data).drop_duplicates()
        # เช็คว่ามีคอลัมน์กิจกรรมไหมก่อนทำ Pivot เพื่อเลี่ยง KeyError
        if not df_f.empty and 'กิจกรรม' in df_f.columns:
            pivot = df_f.pivot_table(index=['ระดับ','เลขที่','ชื่อ-นามสกุล'], columns='กิจกรรม', 
                                     values='กิจกรรม', aggfunc=lambda x:1).fillna(0)
            pivot['คะแนนรวม'] = pivot.sum(axis=1).astype(int)
            res = pivot.replace({1:'✔', 0:'-'}).reset_index().sort_values(['ระดับ','เลขที่'])
            
            # แยกสีระดับชั้น
            colors = {'ม.3':'#fce4ec', 'ม.4':'#fff3e0', 'ม.5':'#e3f2fd', 'ม.6':'#fffde7'}
            styled = res.style.apply(lambda r: [f'background-color: {colors.get(r["ระดับ"], "")}'] * len(r), axis=1)
            
            st.dataframe(styled, use_container_width=True, hide_index=True)
            st.download_button("📥 โหลดรายงาน (CSV)", res.to_csv(index=False).encode('utf-8-sig'), "Report_KruJames.csv")
    else: st.warning("⚠️ ไม่พบข้อมูลงานที่ส่ง (กรุณาเช็คว่าระบุ เลขที่ และ กิจกรรม 1.x ครบไหม)")
