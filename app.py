import streamlit as st
import pandas as pd
import re, os, base64

# --- 1. ตั้งค่าหน้าตาและโทนสีเขียว-ขาว ---
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

# ใช้ f-string แยกกันเพื่อป้องกัน Syntax Error ใน CSS
header_style = """
<style>
    .main-header { background-color: #1b5e20; padding: 15px; border-radius: 10px 10px 0 0; text-align: center; color: white; }
    .teacher-card { background-color: #ffffff; border: 2px solid #e0e0e0; border-radius: 12px; padding: 20px; margin: 15px 0; display: flex; align-items: center; gap: 25px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    .teacher-img { width: 110px; height: 110px; border-radius: 50%; border: 4px solid #4caf50; object-fit: cover; }
    .level-header { background-color: #4caf50; color: white; padding: 10px 20px; border-radius: 8px; margin-top: 30px; margin-bottom: 10px; font-size: 1.5rem; }
</style>
"""
st.markdown(header_style, unsafe_allow_html=True)

# ส่วนแสดงโปรไฟล์
img_src = f"data:image/jpeg;base64,{img_b64}" if img_b64 else placeholder_img
profile_html = f"""
<div class="main-header"><h2 style="margin:0;">📋 ระบบเช็คงานอัจฉริยะ</h2></div>
<div class="teacher-card">
    <img src="{img_src}" class="teacher-img">
    <div>
        <h1 style="margin:0; color: #1b5e20;">ครูตระกูล บุญชิต</h1>
        <p style="margin:0; color: #666;">โรงเรียนตระกาศประชาสามัคคี | ภาคเรียนที่ 2/2568</p>
    </div>
</div>
"""
st.markdown(profile_html, unsafe_allow_html=True)

# --- 2. ฟังก์ชันจัดการความสะอาดของข้อมูล ---
def clean_full_name(n):
    if pd.isna(n): return "ไม่ระบุชื่อ"
    n = str(n).split('\n')[0].strip()
    prefixes = ['นาย', 'นางสาว', 'นาง', 'เด็กชาย', 'เด็กหญิง', r'น\.ส\.', r'ด\.ช\.', r'ด\.ญ\.', r'น\.ส', r'ด\.ช', r'ด\.ญ']
    for p in prefixes:
        n = re.sub(f'^{p}\s*', '', n)
    # ตัดชื่อกลุ่ม/เลขที่/กิจกรรม ที่อาจพิมพ์ปนมาหลังนามสกุล
    n = re.split(r'กลุ่ม|เลขที่|กิจกรรม|ชั้น|ม\.', n)[0]
    return re.sub(r'^[.\-\s0-9]+', '', n).strip()

# --- 3. ส่วนประมวลผล ---
uploaded_files = st.file_uploader("📂 อัปโหลดไฟล์จาก Padlet", type=["csv", "xlsx"], accept_multiple_files=True)

if uploaded_files:
    all_rows = []
    # สร้างคอลัมน์กิจกรรม 1.1 ถึง 1.14
    full_activity_list = [f"กิจกรรมที่ 1.{i}" for i in range(1, 15)]

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
                full_text = " ".join(map(str, row.values))
                sid = re.search(r'เลขที่\s*(\d+)', full_text)
                act = re.search(r'กิจกรรม(?:ที่)?\s*1\.(\d+)', full_text)
                grp = re.search(r'กลุ่มที่\s*(\d+)', full_text)
                
                if sid and act:
                    group_info = f"กลุ่มที่ {grp.group(1)} {file_name}" if grp else file_name
                    raw_content = row.get('เนื้อหา', row.get('เรื่อง', 'ไม่ระบุชื่อ'))
                    all_rows.append({
                        'เลขที่': int(sid.group(1)),
                        'ระดับ': level,
                        'ชื่อ-นามสกุล': clean_full_name(raw_content),
                        'ชื่อกลุ่ม': group_info.strip(),
                        'กิจกรรม': f"กิจกรรมที่ 1.{act.group(1)}"
                    })
        except Exception as e:
            st.error(f"⚠️ ไฟล์ {f.name} มีปัญหา: {e}")

    if all_rows:
        df_all = pd.DataFrame(all_rows).drop_duplicates()
        
        st.markdown("### 🔍 ค้นหาข้อมูล (ค้นหาได้ทั้งระดับชั้นและชื่อ)")
        search_query = st.text_input("พิมพ์ชื่อนักเรียนเพื่อค้นหา...", "")

        for level in ["ม.3", "ม.4", "ม.5", "ม.6"]:
            df_lv = df_all[df_all['ระดับ'] == level]
            if search_query:
                df_lv = df_lv[df_lv['ชื่อ-นามสกุล'].str.contains(search_query, case=False, na=False)]

            if not df_lv.empty:
                st.markdown(f'<div class="level-header">🟢 สรุปผลการส่งงานชั้น {level}</div>', unsafe_allow_html=True)
                
                # ทำ Pivot Table และเติมกิจกรรมให้ครบ 14 คอลัมน์
                pivot = df_lv.pivot_table(index=['เลขที่', 'ระดับ', 'ชื่อ-นามสกุล', 'ชื่อกลุ่ม'], 
                                          columns='กิจกรรม', values='กิจกรรม', aggfunc=lambda x: 1).fillna(0)
                
                for act in full_activity_list:
                    if act not in pivot.columns: pivot[act] = 0
                
                # เรียงคอลัมน์และรวมคะแนน
                pivot = pivot[full_activity_list]
                pivot['คะแนนรวม'] = pivot.sum(axis=1).astype(int)
                res = pivot.replace({1:'✔', 0:'-'}).reset_index().sort_values('เลขที่')
                
                # แสดงตาราง
                st.dataframe(
                    res.style.set_properties(**{'text-align': 'center'})
                    .set_properties(subset=['ชื่อ-นามสกุล', 'ชื่อกลุ่ม'], **{'text-align': 'left'})
                    .set_properties(subset=['คะแนนรวม'], **{'background-color': '#e8f5e9', 'font-weight': 'bold'})
                    .set_table_styles([{'selector': 'th', 'props': [('background-color', '#1b5e20'), ('color', 'white')]}])
                , use_container_width=True, hide_index=True)
                
                st.download_button(f"📥 โหลดไฟล์ {level}", res.to_csv(index=False).encode('utf-8-sig'), f"Report_{level}.csv")
            else:
                st.write(f"🍃 ไม่พบข้อมูลของชั้น {level}")
else:
    st.info("💡 กรุณาอัปโหลดไฟล์จาก Padlet เพื่อแสดงตารางสรุปข้อมูลครับ")
