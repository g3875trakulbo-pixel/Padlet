import streamlit as st
import pandas as pd
import re, os, base64

# --- 1. การตั้งค่าหน้าตา ---
st.set_page_config(page_title="ระบบครูตระกูล v5.2", layout="wide")

# ฟังก์ชันดึงรูปภาพครู
def get_b64(file):
    if os.path.exists(file):
        try:
            with open(file, "rb") as f:
                return base64.b64encode(f.read()).decode()
        except: return None
    return None

img_b64 = get_b64("teacher.jpg")
placeholder_img = "https://cdn-icons-png.flaticon.com/512/3429/3429433.png"

# --- 2. CSS สำหรับ Header และ UI ---
st.markdown("""
<style>
    .main-header { background-color: #1b5e20; padding: 15px; border-radius: 10px 10px 0 0; text-align: center; color: white; }
    .teacher-card { background-color: #ffffff; border: 2px solid #e0e0e0; border-radius: 0 0 12px 12px; padding: 20px; margin-bottom: 25px; display: flex; align-items: center; gap: 25px; }
    .teacher-img { width: 110px; height: 110px; border-radius: 50%; border: 4px solid #4caf50; object-fit: cover; }
    .level-header { background-color: #4caf50; color: white; padding: 10px 20px; border-radius: 8px; margin-top: 30px; margin-bottom: 15px; font-size: 1.5rem; font-weight: bold; }
    .stDataFrame { border: 1px solid #e0e0e0; border-radius: 10px; }
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ส่วนโปรไฟล์ Header
img_src = f"data:image/jpeg;base64,{img_b64}" if img_b64 else placeholder_img
st.markdown(f"""
<div class="main-header"><h2 style="margin:0;">📋 ระบบเช็คงานอัจฉริยะ (Padlet Summary)</h2></div>
<div class="teacher-card">
    <img src="{img_src}" class="teacher-img">
    <div>
        <h1 style="margin:0; color: #1b5e20;">ครูตระกูล บุญชิต</h1>
        <p style="margin:0; color: #666;">โรงเรียนตระกาศประชาสามัคคี | ภาคเรียนที่ 2/2568</p>
    </div>
</div>
""", unsafe_allow_html=True)

# --- 3. ฟังก์ชันล้างชื่อ (ตัดคำนำหน้าออก 100%) ---
def strict_clean_name(n, sid):
    if pd.isna(n) or str(n).strip() == "" or str(n).lower() == "nan": 
        return f"⚠️ ไม่ระบุชื่อ (เลขที่ {sid})"
    
    n = re.sub('<[^<]+?>', '', str(n)).replace('\n', ' ').strip()
    
    # ตัดคำนำหน้าออก
    prefixes = ['เด็กชาย', 'เด็กหญิง', 'นางสาว', 'นาย', 'นาง', r'ด\.ช\.', r'ด\.ญ\.', r'น\.ส\.', r'น\.ส', r'ด\.ช', r'ด\.ญ', 'นส.', 'ดช.', 'ดญ.', 'นส ', 'ดช ', 'ดญ ']
    for p in prefixes:
        n = re.sub(f'^{p}', '', n).strip()
    
    n = re.split(r'กลุ่ม|เลขที่|กิจกรรม|ชั้น|ม\.|เลข|No\.|#|ชื่อเล่น|\(|\[', n, flags=re.IGNORECASE)[0]
    n = re.sub(r'^[0-9.\-\s]+', '', n)
    n = re.sub(r'[0-9.\-\s]+$', '', n)
    
    final_name = re.sub(r'\s+', ' ', n).strip()
    return final_name if final_name else f"⚠️ ไม่ระบุชื่อ (เลขที่ {sid})"

# --- 4. ส่วนประมวลผลไฟล์ ---
uploaded_files = st.file_uploader("📂 อัปโหลดไฟล์ Excel/CSV จาก Padlet", type=["csv", "xlsx"], accept_multiple_files=True)

if uploaded_files:
    all_data = []
    full_acts = [f"กิจกรรมที่ 1.{i}" for i in range(1, 15)]

    for f in uploaded_files:
        try:
            df = pd.read_csv(f, encoding='utf-8-sig') if f.name.endswith('.csv') else pd.read_excel(f)
            lv_match = re.search(r'([3-6])', f.name)
            level = f"ม.{lv_match.group(1)}" if lv_match else "ทั่วไป"
            file_label = f.name.split('.')[0] 
            
            for _, row in df.iterrows():
                combined_text = " ".join(map(str, row.values))
                sid_match = re.search(r'(?:เลขที่|No\.|#)\s*(\d+)', combined_text)
                act_match = re.search(r'1\.(\d{1,2})', combined_text)
                
                if sid_match and act_match:
                    sid = sid_match.group(1)
                    
                    # --- ดึงข้อมูลกลุ่มจาก Excel ---
                    group_info = ""
                    for col in df.columns:
                        if any(k in str(col) for k in ["กลุ่ม", "Group"]):
                            val = str(row[col]).strip()
                            if val != "nan" and val != "":
                                group_info = val
                                break
                    
                    if group_info:
                        group_display = group_info if "กลุ่ม" in group_info else f"กลุ่มที่ {group_info}"
                        if "ที่" not in group_display and "กลุ่ม" in group_display:
                            group_display = group_display.replace("กลุ่ม", "กลุ่มที่ ")
                    else:
                        group_display = f"กลุ่มที่ {file_label}"

                    # ดึงชื่อนักเรียน
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
            st.markdown(f'<div class="level-header">📍 ระดับชั้น {lv}</div>', unsafe_allow_html=True)
            df_lv = df_master[df_master['ระดับ'] == lv]
            
            pivot = df_lv.pivot_table(
                index=['เลขที่', 'ชื่อ-นามสกุล', 'ชื่อกลุ่ม'],
                columns='กิจกรรม',
                values='ระดับ',
                aggfunc='count'
            ).fillna(0).astype(int)

            for act in full_acts:
                if act not in pivot.columns: pivot[act] = 0
            
            res = pivot[full_acts].copy()
            res['คะแนนรวม'] = res.sum(axis=1)
            res['สถานะ'] = res['คะแนนรวม'].apply(lambda s: "🟢 ส่งครบ" if s == 14 else ("🟡 ยังไม่ครบ" if s >= 7 else "🔴 ตามงาน"))
            res = res.reset_index()

            # แยกคนไม่มีชื่อ (มี ⚠️) ไปไว้ท้ายตาราง
            res['is_missing'] = res['ชื่อ-นามสกุล'].apply(lambda x: 1 if "⚠️" in str(x) else 0)
            res = res.sort_values(by=['is_missing', 'เลขที่']).drop(columns=['is_missing'])

            cols = ['เลขที่', 'ชื่อ-นามสกุล', 'ชื่อกลุ่ม'] + full_acts + ['คะแนนรวม', 'สถานะ']
            res = res[cols]

            st.dataframe(
                res.style.set_properties(**{'text-align': 'center'})
                .set_properties(subset=['ชื่อ-นามสกุล', 'ชื่อกลุ่ม'], **{'text-align': 'left'})
                .apply(lambda x: ['background-color: #fff3f3; color: #d32f2f;' if "⚠️" in str(x['ชื่อ-นามสกุล']) else '' for _ in x], axis=1)
                .format({a: lambda x: '✔' if x >= 1 else '-' for a in full_acts}),
                use_container_width=True, hide_index=True
            )
            
            st.download_button(f"📥 โหลดไฟล์คะแนน {lv}", res.to_csv(index=False).encode('utf-8-sig'), f"Report_{lv}.csv")
    else:
        st.info("💡 กรุณาอัปโหลดไฟล์ที่มีข้อมูลครบถ้วนครับ")
