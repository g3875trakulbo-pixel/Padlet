import streamlit as st
import pandas as pd
import re, os, base64
from difflib import SequenceMatcher

# --- 1. การตั้งค่าหน้าตา App (เขียว-ขาว) ---
st.set_page_config(page_title="ระบบครูตระกูล v6.8", layout="wide")

def get_b64(file):
    if os.path.exists(file):
        try:
            with open(file, "rb") as f:
                return base64.b64encode(f.read()).decode()
        except: return None
    return None

img_b64 = get_b64("teacher.jpeg")
placeholder_img = "https://cdn-icons-png.flaticon.com/512/3429/3429433.png"

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Sarabun', sans-serif; background-color: #ffffff; }
    
    .main-header { background-color: #1b5e20; padding: 25px; border-radius: 15px 15px 0 0; text-align: center; color: white; border-bottom: 5px solid #4caf50; }
    
    .teacher-card { background-color: #f8f9fa; border: 1px solid #dee2e6; border-radius: 0 0 15px 15px; padding: 30px; margin-bottom: 35px; display: flex; align-items: center; gap: 30px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); }
    .teacher-img { width: 130px; height: 130px; border-radius: 50%; border: 5px solid #1b5e20; object-fit: cover; }
    
    .level-header { background-color: #e8f5e9; color: #1b5e20; padding: 15px 25px; border-left: 10px solid #1b5e20; border-radius: 5px; margin-top: 40px; font-weight: 700; font-size: 1.5rem; }
    
    /* ตารางพื้นหลังขาว ตัวหนังสือปกติ ไม่หนา */
    .stDataFrame div[data-testid="stTable"] { font-size: 1.1rem; background-color: #ffffff !important; }
    td, th { color: #000000 !important; font-weight: 400 !important; border: 1px solid #dee2e6 !important; }
    th { font-weight: 700 !important; background-color: #f1f3f1 !important; } 
    
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ส่วนหัวและโปรไฟล์ครู
img_src = f"data:image/jpeg;base64,{img_b64}" if img_b64 else placeholder_img
st.markdown(f"""
<div class="main-header"><h2 style="margin:0; color:white; font-weight:700;">📋 ระบบรายงานผลคะแนน Padlet อัจฉริยะ</h2></div>
<div class="teacher-card">
    <img src="{img_src}" class="teacher-img">
    <div>
        <h1 style="margin:0; font-size: 2.5rem; color: #1b5e20; font-weight:700;">ครูตระกูล บุญชิต</h1>
        <p style="margin:0; font-size: 1.2rem; color: #333 !important;">คัดกรองชื่อ 2 คำ | ตารางขาว | ตัวหนังสือปกติ</p>
    </div>
</div>
""", unsafe_allow_html=True)

# --- 2. ฟังก์ชันล้างชื่อ (เอาแค่ 2 คำแรก) ---
def strict_clean_name(n, sid):
    if pd.isna(n) or str(n).strip() == "" or str(n).lower() == "nan": 
        return f"⚠️ ไม่ระบุชื่อ (เลขที่ {sid})"
    
    n = re.sub('<[^<]+?>', '', str(n)).replace('\n', ' ').strip()
    
    # 1. ตัดคำนำหน้าชื่อ
    prefixes = ['เด็กชาย', 'เด็กหญิง', 'นางสาว', 'นาย', 'นาง', r'ด\.ช\.', r'ด\.ญ\.', r'น\.ส\.', r'น\.ส', r'ด\.ช', r'ด\.ญ', 'นส.', 'ดช.', 'ดญ.']
    for p in prefixes: n = re.sub(f'^{p}', '', n).strip()
    
    # 2. ตัดคำขยะ (มีชีวิต, จาก, เล่น, งาน)
    junk_words = ['มีชีวิต', 'มี', 'จาก', 'เล่น', 'งาน', 'ส่งงาน']
    for j in junk_words:
        n = re.sub(f'^{j}', '', n).strip()
        n = re.sub(f' {j} ', ' ', n).strip()

    # 3. ตัดส่วนขยาย (กลุ่ม, กิจกรรม, เลขที่)
    n = re.split(r'กลุ่ม|เลขที่|กิจกรรม|ชั้น|ม\.|เลข|No\.|#|ชื่อเล่น|\(|\[', n, flags=re.IGNORECASE)[0]
    
    # 4. กรองเหลือแค่ พยัญชนะ สระ วรรณยุกต์
    n = re.sub(r'[0-9๐-๙]', '', n)
    n = re.sub(r'[^\u0E01-\u0E3A\u0E40-\u0E4E A-Za-z\s]', '', n)
    
    # 5. บังคับเอาแค่ 2 คำแรก (ชื่อ-นามสกุล)
    words = n.split()
    if len(words) >= 2:
        return f"{words[0]} {words[1]}"
    elif len(words) == 1:
        return words[0]
    return f"⚠️ ไม่ระบุชื่อ (เลขที่ {sid})"

# --- 3. ระบบรวมชื่อที่สะกดใกล้เคียง (Fuzzy Merge) ---
def merge_similar_names(data_list):
    best_names = {}
    for item in data_list:
        sid = item['เลขที่']
        name = item['ชื่อ-นามสกุล']
        if "⚠️" in name: continue
        if sid not in best_names:
            best_names[sid] = name
        else:
            if SequenceMatcher(None, name, best_names[sid]).ratio() > 0.75:
                if len(name) > len(best_names[sid]): best_names[sid] = name
    for item in data_list:
        sid = item['เลขที่']
        if sid in best_names and "⚠️" not in item['ชื่อ-นามสกุล']:
            item['ชื่อ-นามสกุล'] = best_names[sid]
    return data_list

# --- 4. การประมวลผลไฟล์ ---
uploaded_files = st.file_uploader("📂 อัปโหลดไฟล์ Padlet (Excel/CSV)", type=["csv", "xlsx"], accept_multiple_files=True)

if uploaded_files:
    all_raw_data = []
    full_acts = [f"กิจกรรมที่ 1.{i}" for i in range(1, 15)]

    for f in uploaded_files:
        try:
            df = pd.read_csv(f, encoding='utf-8-sig') if f.name.endswith('.csv') else pd.read_excel(f)
            lv_match = re.search(r'([3-6])', f.name)
            level = f"ม.{lv_match.group(1)}" if lv_match else "ทั่วไป"
            col_group = next((c for c in df.columns if any(k in str(c) for k in ["กลุ่ม", "Group"])), None)

            for _, row in df.iterrows():
                combined_text = " ".join(map(str, row.values))
                sid_match = re.search(r'(?:เลขที่|No\.|#)\s*(\d+)', combined_text)
                act_match = re.search(r'1\.(\d{1,2})', combined_text)
                
                if sid_match and act_match:
                    sid = int(sid_match.group(1))
                    
                    # ดึงข้อมูลกลุ่มมาต่อกัน
                    raw_grp = str(row[col_group]).strip() if col_group else ""
                    if raw_grp == "nan" or raw_grp == "":
                        group_display = f"กลุ่มที่ {f.name.split('.')[0]}"
                    else:
                        group_display = raw_grp if "กลุ่ม" in raw_grp else f"กลุ่มที่ {raw_grp}"
                        group_display = group_display.replace("กลุ่ม", "กลุ่มที่ ").replace("ที่ ที่", "ที่")

                    name_candidates = [row.get('Subject'), row.get('เนื้อหา'), row.get('Body')]
                    raw_name = next((str(x) for x in name_candidates if pd.notna(x) and str(x).strip() != ""), "")
                    
                    all_raw_data.append({
                        'เลขที่': sid,
                        'ระดับ': level,
                        'ชื่อ-นามสกุล': strict_clean_name(raw_name, sid),
                        'ชื่อกลุ่ม': group_display,
                        'กิจกรรม': f"กิจกรรมที่ 1.{act_match.group(1)}"
                    })
        except: continue

    if all_raw_data:
        final_data = merge_similar_names(all_raw_data)
        df_master = pd.DataFrame(final_data).drop_duplicates()
        
        for lv in sorted(df_master['ระดับ'].unique()):
            st.markdown(f'<div class="level-header">📍 รายงานผลระดับชั้น {lv}</div>', unsafe_allow_html=True)
            df_lv = df_master[df_master['ระดับ'] == lv]
            pivot = df_lv.pivot_table(index=['เลขที่', 'ชื่อ-นามสกุล', 'ชื่อกลุ่ม'], columns='กิจกรรม', values='ระดับ', aggfunc='count').fillna(0).astype(int)
            for act in full_acts: 
                if act not in pivot.columns: pivot[act] = 0
            res = pivot[full_acts].copy()
            res['รวม'] = res.sum(axis=1)
            res = res.reset_index()
            res['is_missing'] = res['ชื่อ-นามสกุล'].apply(lambda x: 1 if "⚠️" in str(x) else 0)
            res = res.sort_values(by=['is_missing', 'เลขที่']).drop(columns=['is_missing'])

            # --- ตารางพื้นขาว ตัวหนังสือปกติ ---
            st.dataframe(
                res.style.set_properties(**{
                    'background-color': '#ffffff',
                    'color': '#000000',
                    'text-align': 'center'
                })
                .set_properties(subset=['ชื่อ-นามสกุล', 'ชื่อกลุ่ม'], **{'text-align': 'left'})
                .apply(lambda x: ['background-color: #fffafa; color: #d32f2f;' if "⚠️" in str(x['ชื่อ-นามสกุล']) else 'background-color: #ffffff;' for _ in x], axis=1)
                .format({a: lambda x: '✔' if x >= 1 else '-' for a in full_acts}),
                use_container_width=True, hide_index=True
            )
            st.download_button(f"📥 โหลดไฟล์สรุป {lv}", res.to_csv(index=False).encode('utf-8-sig'), f"Summary_{lv}.csv")
