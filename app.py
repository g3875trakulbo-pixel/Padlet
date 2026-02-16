import streamlit as st
import pandas as pd
import re, os, base64

# --- 1. ตั้งค่าหน้าตาและโทนสีเขียว-ขาว ---
st.set_page_config(page_title="ระบบครูตระกูล", layout="wide")

def get_b64(file):
    if os.path.exists(file):
        try:
            with open(file, "rb") as f: return base64.b64encode(f.read()).decode()
        except: return None
    return None

img = get_b64("teacher.jpg")

# CSS สำหรับ Layout โทนสีเขียว (จัดระเบียบใหม่ให้เหมือนภาพตัวอย่าง)
st.markdown(f"""
<style>
    .main-header {{
        background-color: #1b5e20;
        padding: 15px;
        border-radius: 10px 10px 0 0;
        text-align: center;
        color: white;
    }}
    .teacher-card {{
        background-color: #ffffff;
        border: 2px solid #e0e0e0;
        border-radius: 12px;
        padding: 20px;
        margin: 15px 0;
        display: flex;
        align-items: center;
        gap: 25px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }}
    .teacher-img {{
        width: 100px; height: 100px;
        border-radius: 50%;
        border: 3px solid #4caf50;
        object-fit: cover;
    }}
    .stTabs [data-baseweb="tab-list"] {{ gap: 8px; }}
    .stTabs [data-baseweb="tab"] {{
        background-color: #f1f8e9;
        border-radius: 8px 8px 0 0;
        color: #2e7d32;
    }}
</style>

<div class="main-header">
    <h2 style="margin:0; font-weight: 300; letter-spacing: 1px;">ระบบเช็คงานอัจฉริยะ</h2>
</div>

<div class="teacher-card">
    {f'<img src="data:image/jpeg;base64,{img}" class="teacher-img">' if img else '<div style="width:100px;height:100px;background:#eee;border-radius:50%;display:flex;align-items:center;justify-content:center;color:#999;">No Img</div>'}
    <div>
        <h2 style="margin:0; color: #1b5e20;">ครูตระกูล บุญชิต (ครูเจมส์)</h2>
        <p style="margin:0; color: #666; font-size: 1rem;">โรงเรียนตระกาศประชาสามัคคี | ภาคเรียนที่ 2/2568</p>
    </div>
</div>
""", unsafe_allow_html=True)

# --- 2. ฟังก์ชันจัดการชื่อและสไตล์ ---
def clean_n(n):
    n = str(n).split('\n')[0].strip()
    prefixes = ['นาย','นางสาว','นาง','เด็กชาย','เด็กหญิง','น.ส.','ด.ช.','ด.ญ.']
    for p in prefixes: n = re.sub(f'^{p}\s*', '', n)
    return re.sub(r'^[.\-\s0-9]+', '', n).strip()

def apply_style(row):
    return ['background-color: white; color: #1b5e20; border: 0.5px solid #eee;'] * len(row)

# --- 3. ส่วนประมวลผล (เพิ่มระบบเช็ค Error) ---
files = st.file_uploader("📂 อัปโหลดไฟล์จาก Padlet (CSV/Excel)", type=["csv", "xlsx"], accept_multiple_files=True)

if files:
    all_data = []
    for f in files:
        try:
            # ตรวจสอบนามสกุลไฟล์และอ่านข้อมูล
            if f.name.endswith('.csv'):
                df = pd.read_csv(f, encoding='utf-8-sig')
            else:
                df = pd.read_excel(f)
            
            # หาระดับชั้นจากชื่อไฟล์
            lv_m = re.search(r'([3-6])', f.name)
            lv = f"ม.{lv_m.group(1)}" if lv_m else "ทั่วไป"
            group_name = f.name.split('.')[0]
            
            for _, r in df.iterrows():
                # รวมข้อมูลทุก Column เป็น String เพื่อใช้ Regex ค้นหา
                txt = " ".join(map(str, r.values))
                sid = re.search(r'เลขที่\s*(\d+)', txt)
                act = re.search(r'กิจกรรม(?:ที่)?\s*1\.(\d+)', txt)
                grp_match = re.search(r'กลุ่มที่\s*(\d+)', txt)
                group_no = f"กลุ่มที่ {grp_match.group(1)}" if grp_match else ""
                
                if sid and act:
                    all_data.append({
                        'เลขที่': int(sid.group(1)),
                        'ระดับ': lv,
                        'ชื่อ-นามสกุล': clean_n(r.get('เนื้อหา', r.get('เรื่อง', 'ไม่ระบุชื่อ'))),
                        'ชื่อกลุ่ม': f"{group_no} {group_name}".strip(),
                        'กิจกรรม': f"กิจกรรมที่ 1.{act.group(1)}"
                    })
        except Exception as e:
            st.error(f"❌ ไฟล์ {f.name} มีปัญหา: {e}")

    if all_data:
        df_final = pd.DataFrame(all_data).drop_duplicates()
        tab_list = ["ม.3", "ม.4", "ม.5", "ม.6"]
        tabs = st.tabs(tab_list)

        for i, level in enumerate(tab_list):
            with tabs[i]:
                df_lv = df_final[df_final['ระดับ'] == level]
                if not df_lv.empty:
                    try:
                        # สร้าง Pivot Table
                        pivot = df_lv.pivot_table(index=['เลขที่','ระดับ','ชื่อ-นามสกุล','ชื่อกลุ่ม'], 
                                                   columns='กิจกรรม', values='กิจกรรม', aggfunc=lambda x:1).fillna(0)
                        
                        # คำนวณคะแนนรวม
                        pivot['คะแนนรวม'] = pivot.sum(axis=1).astype(int)
                        res = pivot.replace({1:'✔', 0:'-'}).reset_index().sort_values('เลขที่')
                        
                        st.markdown(f"#### 🟢 ผลการเช็คงานชั้น {level}")
                        st.dataframe(res.style.apply(apply_style, axis=1), use_container_width=True, hide_index=True)
                        st.download_button(f"📥 ดาวน์โหลดไฟล์ {level}", res.to_csv(index=False).encode('utf-8-sig'), f"Report_{level}.csv")
                    except Exception as e:
                        st.warning(f"⚠️ ไม่สามารถสร้างตารางของ {level} ได้: ข้อมูลไม่ครบถ้วน")
                else:
                    st.info(f"🍃 ยังไม่มีข้อมูลการส่งงานของ {level}")
    else:
        st.warning("🔎 ไม่พบข้อมูล 'เลขที่' หรือ 'กิจกรรม' ในไฟล์ที่อัปโหลด กรุณาตรวจสอบการตั้งชื่อโพสต์ของนักเรียน")
