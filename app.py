import streamlit as st
import pandas as pd
import re, os, base64

# --- 1. การตั้งค่าหน้าตา App ---
st.set_page_config(page_title="ระบบครูตระกูล v5.9", layout="wide")

def get_b64(file):
    if os.path.exists(file):
        try:
            with open(file, "rb") as f:
                return base64.b64encode(f.read()).decode()
        except: return None
    return None

img_b64 = get_b64("teacher.jpg")
placeholder_img = "https://cdn-icons-png.flaticon.com/512/3429/3429433.png"

# --- 2. CSS ดีไซน์เขียว-ขาว (ตัวหนังสือปกติ อ่านง่าย) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Sarabun', sans-serif; background-color: #ffffff; }
    
    .main-header { background-color: #1b5e20; padding: 25px; border-radius: 15px 15px 0 0; text-align: center; color: #ffffff; border-bottom: 6px solid #4caf50; }
    
    .teacher-card { background-color: #f8f9fa; border: 1px solid #dee2e6; border-radius: 0 0 15px 15px; padding: 30px; margin-bottom: 35px; display: flex; align-items: center; gap: 30px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
    .teacher-img { width: 130px; height: 130px; border-radius: 50%; border: 5px solid #1b5e20; object-fit: cover; }
    
    .level-header { background-color: #e8f5e9; color: #1b5e20; padding: 15px 25px; border-left: 10px solid #1b5e20; border-radius: 5px; margin-top: 45px; margin-bottom: 20px; font-weight: 700; font-size: 1.6rem; }
    
    /* ปรับแต่งตาราง: ใช้ตัวหนังสือปกติ (Normal Weight) */
    .stDataFrame div[data-testid="stTable"] { font-size: 1.1rem; }
    td, th { color: #000000 !important; font-weight: 400 !important; }
    th { font-weight: 700 !important; } /* หัวตารางยังคงหนาเพื่อให้แยกแยะง่าย */
    
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ส่วน Header และโปรไฟล์
img_src = f"data:image/jpeg;base64,{img_b64}" if img_b64 else placeholder_img
st.markdown(f"""
<div class="main-header"><h2 style="margin:0; color:white; font-weight:700;">📋 ระบบรายงานผลคะแนน Padlet อัจฉริยะ</h2></div>
<div class="teacher-card">
    <img src="{img_src}" class="teacher-img">
    <div>
        <h1 style="margin:0; font-size: 2.5rem; color: #1b5e20; font-weight:700;">ครูตระกูล บุญชิต</h1>
        <p style="margin:0; font-size: 1.3rem; color: #333 !important;">สรุปข้อมูลรายห้องและคะแนนกิจกรรมรายบุคคล</p>
    </div>
</div>
""", unsafe_allow_html=True)

# --- 3. ฟังก์ชันล้างชื่อ (พยัญชนะ สระ วรรณยุกต์ เท่านั้น) ---
def strict_clean_name(n, sid):
    if pd.isna(n) or str(n).strip() == "" or str(n).lower() == "nan": 
        return f"⚠️ ไม่ระบุชื่อ (เลขที่ {sid})"
    
    n = re.sub('<[^<]+?>', '', str(n)).replace('\n', ' ').strip()
    
    prefixes = ['เด็กชาย', 'เด็กหญิง', 'นางสาว', 'นาย', 'นาง', r'ด\.ช\.', r'ด\.ญ\.', r'น\.ส\.', r'น\.ส', r'ด\.ช', r'ด\.ญ', 'นส.', 'ดช.', 'ดญ.', 'นส ', 'ดช ', 'ดญ ']
    for p in prefixes: n = re.sub(f'^{p}', '', n).strip()
    
    n = re.split(r'กลุ่ม|เลขที่|กิจกรรม|ชั้น|ม\.|เลข|No\.|#|ชื่อเล่น|\(|\[', n, flags=re.IGNORECASE)[0]
    
    # ลบตัวเลขและสัญลักษณ์พิเศษ
    n = re.sub(r'[0-9๐-๙]', '', n)
    n = re.sub(r'[^\u0E01-\u0E3A\u0E40-\u0E4E A-Za-z\s]', '', n)
    
    final_name = re.sub(r'\s+', ' ', n).strip()
    return final_name if final_name else f"⚠️ ไม่ระบุชื่อ (เลขที่ {sid})"

# --- 4. การประมวลผลไฟล์ ---
uploaded_files = st.file_uploader("📂 อัปโหลดไฟล์ Excel/CSV จาก Padlet", type=["csv", "xlsx"], accept_multiple_files=True)

if uploaded_files:
    all_data = []
    full_acts = [f"กิจกรรมที่ 1.{i}" for i in range(1, 15)]

    for f in uploaded_files:
        try:
            df = pd.read_csv(f, encoding='utf-8-sig') if f.name.endswith('.csv') else pd.read_excel(f)
            lv_match = re.search(r'([3-6])', f.name)
            level = f"ม.{lv_match.group(1)}" if lv_match else "ทั่วไป"
            
            for _, row in df.iterrows():
                combined_text = " ".join(map(str, row.values))
                sid_match = re.search(r'(?:เลขที่|No\.|#)\s*(\d+)', combined_text)
                act_match = re.search(r'1\.(\d{1,2})', combined_text)
                
                if sid_match and act_match:
                    sid = sid_match.group(1)
                    
                    # --- ดึงกลุ่มและชื่อกลุ่มมาพิมพ์ต่อกัน ---
                    g_no = ""
                    g_name = ""
                    for col in df.columns:
                        col_lower = str(col).lower()
                        if any(k in col_lower for k in ["กลุ่ม", "group"]):
                            val = str(row[col]).strip()
                            if val != "nan" and val != "":
                                if any(char.isdigit() for char in val): g_no = val
                                else: g_name = val
                    
                    if g_no and g_name: group_display = f"กลุ่มที่ {g_no} {g_name}"
                    elif g_no: group_display = f"กลุ่มที่ {g_no}"
                    elif g_name: group_display = f"กลุ่มที่ {g_name}"
                    else: group_display = f"กลุ่มที่ {f.name.split('.')[0]}"

                    # หาชื่อนักเรียน
                    name_candidates = [row.get('Subject'), row.get('เนื้อหา'), row.get('Body')]
                    raw_name = next((str(x) for x in name_candidates if pd.notna(x) and str(x).strip() != ""), "")
                    
                    all_data.append({
                        'เลขที่': int(sid),
                        'ระดับ': level,
                        'ชื่อ-นามสกุล': strict_clean_name(raw_name, sid),
                        'ชื่อกลุ่ม': group_display,
                        'กิจกรรม': f"กิจกรรมที่ 1.{act_match.group(1)}"
                    })
        except: continue

    if all_data:
        df_master = pd.DataFrame(all_data).drop_duplicates()
        for lv in sorted(df_master['ระดับ'].unique()):
            st.markdown(f'<div class="level-header">📍 ผลการเช็คงานระดับชั้น {lv}</div>', unsafe_allow_html=True)
            df_lv = df_master[df_master['ระดับ'] == lv]
            
            pivot = df_lv.pivot_table(index=['เลขที่', 'ชื่อ-นามสกุล', 'ชื่อกลุ่ม'], columns='กิจกรรม', values='ระดับ', aggfunc='count').fillna(0).astype(int)
            for act in full_acts: 
                if act not in pivot.columns: pivot[act] = 0
            
            res = pivot[full_acts].copy()
            res['รวม'] = res.sum(axis=1)
            res = res.reset_index()

            # เรียงลำดับ: มีชื่อ (บน) / ไม่มีชื่อ (ล่าง)
            res['is_missing'] = res['ชื่อ-นามสกุล'].apply(lambda x: 1 if "⚠️" in str(x) else 0)
            res = res.sort_values(by=['is_missing', 'เลขที่']).drop(columns=['is_missing'])

            # แสดงตาราง (ตัวหนังสือปกติ)
            st.dataframe(
                res.style.set_properties(**{'text-align': 'center', 'border': '1px solid #dee2e6'})
                .set_properties(subset=['ชื่อ-นามสกุล', 'ชื่อกลุ่ม'], **{'text-align': 'left'})
                .apply(lambda x: ['background-color: #fffafa; color: #d32f2f;' if "⚠️" in str(x['ชื่อ-นามสกุล']) else '' for _ in x], axis=1)
                .format({a: lambda x: '✔' if x >= 1 else '-' for a in full_acts}),
                use_container_width=True, hide_index=True
            )
            st.download_button(f"📥 โหลดไฟล์สรุป {lv}", res.to_csv(index=False).encode('utf-8-sig'), f"Report_{lv}.csv")
    else:
        st.info("💡 กรุณาอัปโหลดไฟล์ที่มีข้อมูลครบถ้วน")
