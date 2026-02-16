import streamlit as st
import pandas as pd
import re, os, base64

# --- 1. การตั้งค่าหน้าตาและสไตล์ ---
st.set_page_config(page_title="ระบบครูตระกูล v2.5", layout="wide")

st.markdown("""
<style>
    /* Header & Cards */
    .main-header { background-color: #1b5e20; padding: 20px; border-radius: 12px; text-align: center; color: white; margin-bottom: 20px; }
    .teacher-card { background-color: #f8f9fa; border: 1px solid #dee2e6; border-radius: 15px; padding: 20px; display: flex; align-items: center; gap: 20px; margin-bottom: 30px; }
    .teacher-img { width: 90px; height: 90px; border-radius: 50%; border: 3px solid #4caf50; object-fit: cover; }
    
    /* Table & Headers */
    .level-header { background-color: #2e7d32; color: white; padding: 10px 20px; border-radius: 8px; margin-top: 30px; margin-bottom: 15px; font-size: 1.3rem; font-weight: bold; }
    .stDataFrame { border-radius: 10px; overflow: hidden; }
    
    /* Metrics */
    [data-testid="stMetricValue"] { color: #1b5e20; font-size: 1.8rem; }
</style>
""", unsafe_allow_html=True)

# --- 2. ฟังก์ชันช่วยประมวลผล (Utility Functions) ---

def strict_clean_name(n):
    """ฟังก์ชันล้างชื่อ-นามสกุลให้สะอาดที่สุด"""
    if pd.isna(n) or str(n).strip() == "": 
        return "ไม่ระบุชื่อ"
    
    # ล้าง HTML และขึ้นบรรทัดใหม่
    n = re.sub('<[^<]+?>', '', str(n)) 
    n = n.replace('\n', ' ').strip()
    
    # ตัดคำนำหน้าชื่อ (Prefixes)
    prefixes = [
        'นาย', 'นางสาว', 'นาง', 'เด็กชาย', 'เด็กหญิง', 
        r'น\.ส\.', r'ด\.ช\.', r'ด\.ญ\.', r'น\.ส', r'ด\.ช', r'ด\.ญ', 
        r'นส\.', r'ดช\.', r'ดญ\.', 'นส ', 'ดช ', 'ดญ '
    ]
    for p in prefixes:
        n = re.sub(f'^{p}', '', n).strip()
    
    # ตัดข้อความส่วนเกิน (กลุ่ม/เลขที่/ชั้น/สัญลักษณ์)
    keywords = [
        'กลุ่ม', 'เลขที่', 'กิจกรรม', 'ชั้น', 'ม\.', 'เลข', 
        'No\.', '#', 'ชื่อเล่น', 'สมาชิก', 'งานที่', r'\(', r'\['
    ]
    pattern = '|'.join(keywords)
    n = re.split(pattern, n, flags=re.IGNORECASE)[0]
    
    # ลบตัวเลขและสัญลักษณ์หัว-ท้าย
    n = re.sub(r'^[0-9.\-\s]+', '', n) 
    n = re.sub(r'[0-9.\-\s]+$', '', n) 
    
    # รวบช่องว่างที่เกินมา
    n = re.sub(r'\s+', ' ', n).strip()
    
    return n if n else "ไม่ระบุชื่อ"

def get_image_base64(path):
    if os.path.exists(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

# --- 3. ส่วนแสดงผล Profile ครู ---
img_b64 = get_image_base64("teacher.jpg")
img_src = f"data:image/jpeg;base64,{img_b64}" if img_b64 else "https://cdn-icons-png.flaticon.com/512/3429/3429433.png"

st.markdown(f"""
<div class="main-header"><h2>📋 ระบบเช็คงานอัจฉริยะ (Padlet Parser)</h2></div>
<div class="teacher-card">
    <img src="{img_src}" class="teacher-img">
    <div>
        <h2 style="margin:0; color: #1b5e20;">ครูตระกูล บุญชิต</h2>
        <p style="margin:0; color: #666;">โรงเรียนตระกาศประชาสามัคคี | ภาคเรียนที่ 2/2568</p>
    </div>
</div>
""", unsafe_allow_html=True)

# --- 4. การจัดการไฟล์และการดึงข้อมูล ---
uploaded_files = st.file_uploader("📂 อัปโหลดไฟล์ CSV/XLSX จาก Padlet", type=["csv", "xlsx"], accept_multiple_files=True)

if uploaded_files:
    all_data = []
    full_acts = [f"กิจกรรมที่ 1.{i}" for i in range(1, 15)]

    for f in uploaded_files:
        try:
            df = pd.read_csv(f, encoding='utf-8-sig') if f.name.endswith('.csv') else pd.read_excel(f)
            
            # ค้นหาระดับชั้นจากชื่อไฟล์
            lv_match = re.search(r'([3-6])', f.name)
            level = f"ม.{lv_match.group(1)}" if lv_match else "ทั่วไป"
            
            for _, row in df.iterrows():
                # รวมข้อมูลทุกช่องเพื่อค้นหา Pattern
                combined_text = " ".join(map(str, row.values))
                
                # ค้นหาเลขที่ และ กิจกรรม 1.1 - 1.14
                sid_match = re.search(r'(?:เลขที่|No\.|#)\s*(\d+)', combined_text)
                act_match = re.search(r'1\.(\d{1,2})', combined_text)
                
                if sid_match and act_match:
                    act_num = int(act_match.group(1))
                    if 1 <= act_num <= 14:
                        # ดึงชื่อจาก Subject (หัวข้อ) หรือ Body (เนื้อหา)
                        raw_name = row.get('Subject', row.get('เนื้อหา', row.get('Body', 'ไม่ระบุชื่อ')))
                        
                        all_data.append({
                            'เลขที่': int(sid_match.group(1)),
                            'ระดับ': level,
                            'ชื่อ-นามสกุล': strict_clean_name(raw_name),
                            'กิจกรรม': f"กิจกรรมที่ 1.{act_num}"
                        })
        except Exception as e:
            st.error(f"ผิดพลาดที่ไฟล์ {f.name}: {e}")

    # --- 5. การแสดงผลตารางคะแนนสรุป ---
    if all_data:
        df_master = pd.DataFrame(all_data).drop_duplicates()
        
        for lv in sorted(df_master['ระดับ'].unique()):
            st.markdown(f'<div class="level-header">📍 ระดับชั้น {lv}</div>', unsafe_allow_html=True)
            df_lv = df_master[df_master['ระดับ'] == lv]
            
            # สร้าง Pivot Table (1 = ส่งแล้ว, 0 = ยังไม่ส่ง)
            pivot = df_lv.pivot_table(
                index=['เลขที่', 'ชื่อ-นามสกุล'],
                columns='กิจกรรม',
                values='ระดับ',
                aggfunc='count'
            ).fillna(0)

            # เติมคอลัมน์กิจกรรมให้ครบ 1.1 - 1.14
            for act in full_acts:
                if act not in pivot.columns:
                    pivot[act] = 0
            
            # จัดเรียงและคำนวณคะแนน
            pivot = pivot[full_acts].astype(int)
            pivot['คะแนนรวม'] = pivot.sum(axis=1)
            res = pivot.reset_index().sort_values('เลขที่')

            # ฟังก์ชันตกแต่งสีคอลัมน์คะแนนรวม
            def color_total(val):
                if val >= 14: color = '#c8e6c9' # เขียว
                elif val >= 7: color = '#fff9c4' # เหลือง
                else: color = '#ffecb3'          # ส้ม
                return f'background-color: {color}; font-weight: bold; color: black;'

            # แสดงตาราง
            st.dataframe(
                res.style.set_properties(**{'text-align': 'center'})
                .applymap(color_total, subset=['คะแนนรวม'])
                .set_properties(subset=['ชื่อ-นามสกุล'], **{'text-align': 'left'})
                .format({act: lambda x: '1' if x >= 1 else '0' for act in full_acts})
                .set_table_styles([
                    {'selector': 'th', 'props': [('background-color', '#1b5e20'), ('color', 'white'), ('text-align', 'center')]}
                ]),
                use_container_width=True, 
                hide_index=True
            )

            # ส่วนสรุป Metrics
            m1, m2, m3 = st.columns(3)
            with m1: st.metric("นักเรียนที่ส่งงาน", f"{len(res)} คน")
            with m2: st.metric("คะแนนเฉลี่ย", f"{res['คะแนนรวม'].mean():.1f} / 14")
            with m3: st.metric("ส่งครบ 100%", f"{len(res[res['คะแนนรวม'] == 14])} คน")
            
            # ปุ่มโหลดไฟล์เฉพาะชั้น
            csv_data = res.to_csv(index=False).encode('utf-8-sig')
            st.download_button(f"📥 ดาวน์โหลดไฟล์ Excel ({lv})", csv_data, f"คะแนน_{lv}.csv", "text/csv")
            st.divider()

    else:
        st.info("💡 ระบบพร้อมใช้งาน! กรุณาอัปโหลดไฟล์ CSV หรือ XLSX จาก Padlet ครับ")
else:
    st.warning("👈 เริ่มต้นโดยการอัปโหลดไฟล์ที่แถบด้านข้าง (หรือคลิกปุ่ม Browse files ด้านบน)")

# --- 6. Footer ---
st.markdown("<p style='text-align: center; color: #999;'>พัฒนาโดย Gemini AI สำหรับครูตระกูล บุญชิต</p>", unsafe_allow_html=True)
