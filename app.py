import streamlit as st
import pandas as pd
import re, os, base64

# --- 1. หน้าเว็บและดีไซน์ Header ---
st.set_page_config(page_title="ระบบครูตระกูล", layout="wide")

def get_b64(file):
    if os.path.exists(file):
        with open(file, "rb") as f: return base64.b64encode(f.read()).decode()
    return None

img = get_b64("teacher.jpg")

# Layout: ชื่อระบบบนสุด -> รูปครูตรงกลาง -> ชื่อครูล่างรูป (โทนม่วง-ชมพู-ส้ม)
st.markdown(f"""
<style>
    .main-header {{
        background: linear-gradient(90deg, #9c27b0, #e91e63, #ff9800);
        padding: 40px 20px;
        border-radius: 0 0 30px 30px;
        text-align: center;
        color: white;
        margin-top: -60px;
        box-shadow: 0 10px 20px rgba(0,0,0,0.2);
    }}
    .teacher-img {{
        width: 120px; height: 120px;
        border-radius: 50%;
        border: 4px solid white;
        object-fit: cover;
        margin: 20px 0;
        box-shadow: 0 4px 10px rgba(0,0,0,0.3);
    }}
</style>
<div class="main-header">
    <h1 style="font-size: 2.8rem; font-weight: 800; margin:0;">📋 ระบบเช็คงานอัจฉริยะ</h1>
    <p style="font-size: 1.1rem; opacity: 0.9;">โรงเรียนตระกาศประชาสามัคคี | ภาคเรียนที่ 2/2568</p>
    {f'<img src="data:image/jpeg;base64,{img}" class="teacher-img">' if img else '<div style="height:20px;"></div>'}
    <h2 style="margin:0; font-size: 1.8rem;">ครูตระกูล บุญชิต</h2>
    <div style="background: rgba(255,255,255,0.2); display: inline-block; padding: 3px 20px; border-radius: 50px; margin-top: 10px; border: 1px solid white; font-size: 0.8rem;">
        PROFESSIONAL TEACHER
    </div>
</div><br>""", unsafe_allow_html=True)

# --- 2. ฟังก์ชันจัดการชื่อและสไตล์ตาราง ---
def clean_n(n):
    n = str(n).split('\n')[0].strip()
    for p in ['นาย','นางสาว','นาง','เด็กชาย','เด็กหญิง','น.ส.','ด.ช.','ด.ญ.','น.ส','ด.ช','ด.ญ']:
        n = re.sub(f'^{p}\s*', '', n)
    return re.sub(r'^[.\-\s0-9]+', '', n).strip()

def apply_style(row):
    color_map = {
        'ม.3': ['#f3e5f5', '#7b1fa2'], # ม่วง
        'ม.4': ['#e3f2fd', '#1565c0'], # ฟ้า
        'ม.5': ['#e8f5e9', '#2e7d32'], # เขียว
        'ม.6': ['#fff3e0', '#e65100'], # ส้ม
    }
    bg, fg = color_map.get(row['ระดับ'], ['#ffffff', '#000000'])
    return [f'background-color: {bg}; color: {fg}; font-weight: bold; border: 0.5px solid #eee;'] * len(row)

# --- 3. ส่วนประมวลผล (แก้ไขให้ทำงานได้จริง) ---
files = st.file_uploader("📂 อัปโหลดไฟล์ Padlet (CSV/Excel)", type=["csv", "xlsx"], accept_multiple_files=True)

if files:
    all_data = []
    for f in files:
        try:
            df = pd.read_csv(f, encoding='utf-8-sig') if f.name.endswith('.csv') else pd.read_excel(f)
            # พยายามหาระดับชั้นจากชื่อไฟล์
            lv_match = re.search(r'([3-6])', f.name)
            lv = f"ม.{lv_match.group(1)}" if lv_match else "ทั่วไป"
            
            for _, r in df.iterrows():
                # รวมข้อมูลทุกคอลัมน์เพื่อหา เลขที่ และ กิจกรรม
                full_text = " ".join(map(str, r.values))
                sid = re.search(r'เลขที่\s*(\d+)', full_text)
                act = re.search(r'กิจกรรม(?:ที่)?\s*1\.(\d+)', full_text)
                
                if sid and act:
                    name_raw = r.get('เนื้อหา', r.get('เรื่อง', 'ไม่ระบุชื่อ'))
                    all_data.append({
                        'ระดับ': lv, 'เลขที่': int(sid.group(1)), 
                        'ชื่อ-นามสกุล': clean_n(name_raw), 
                        'กิจกรรม': f"กิจกรรมที่ 1.{act.group(1)}"
                    })
        except Exception as e:
            st.error(f"เกิดข้อผิดพลาดกับไฟล์ {f.name}: {e}")

    if all_data:
        df_final = pd.DataFrame(all_data).drop_duplicates()
        
        # จุดสำคัญ: เช็คก่อนว่ามีข้อมูลกิจกรรมไหม
        if not df_final.empty:
            # สร้างตาราง Pivot
            pivot = df_final.pivot_table(index=['ระดับ','เลขที่','ชื่อ-นามสกุล'], 
                                           columns='กิจกรรม', 
                                           values='กิจกรรม', 
                                           aggfunc=lambda x: 1).fillna(0)
            
            # คำนวณคะแนนรวม
            pivot['คะแนนรวม'] = pivot.sum(axis=1).astype(int)
            res = pivot.replace({1:'✔', 0:'-'}).reset_index().sort_values(['ระดับ','เลขที่'])
            
            # แสดงตาราง
            st.dataframe(res.style.apply(apply_style, axis=1), use_container_width=True, hide_index=True)
            
            # ปุ่มดาวน์โหลด
            st.download_button("📥 โหลดรายงาน (CSV)", res.to_csv(index=False).encode('utf-8-sig'), "Report_KruJames.csv", "text/csv")
    else:
        st.info("💡 คำแนะนำ: โปรดอัปโหลดไฟล์ และตรวจสอบว่าใน Padlet นักเรียนพิมพ์คำว่า 'เลขที่' และ 'กิจกรรม 1.x' ถูกต้องหรือไม่")
