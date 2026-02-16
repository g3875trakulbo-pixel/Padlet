import streamlit as st
import pandas as pd
import re, os, base64
from difflib import SequenceMatcher

# --- 1. ตั้งค่าหน้าตา App ---
st.set_page_config(page_title="ระบบครูตระกูล v7.7", layout="wide")

# ฟังก์ชันดึงรูปโปรไฟล์
def get_b64(file):
    if os.path.exists(file):
        try:
            with open(file, "rb") as f:
                return base64.b64encode(f.read()).decode()
        except: return None
    return None

img_b64 = get_b64("teacher.jpeg")
placeholder_img = "https://cdn-icons-png.flaticon.com/512/3429/3429433.png"

# CSS ปรับแต่งตาราง (พื้นขาว, ตัวหนังสือปกติ)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Sarabun', sans-serif; background-color: #ffffff; }
    .main-header { background-color: #1b5e20; padding: 25px; border-radius: 15px 15px 0 0; text-align: center; color: white; border-bottom: 5px solid #4caf50; }
    .teacher-card { background-color: #f8f9fa; border: 1px solid #dee2e6; border-radius: 0 0 15px 15px; padding: 30px; margin-bottom: 35px; display: flex; align-items: center; gap: 30px; }
    .teacher-img { width: 130px; height: 130px; border-radius: 50%; border: 5px solid #1b5e20; object-fit: cover; }
    .level-header { background-color: #e8f5e9; color: #1b5e20; padding: 15px 25px; border-left: 10px solid #1b5e20; border-radius: 4px; margin-top: 40px; font-weight: 700; font-size: 1.5rem; }
    .stDataFrame div[data-testid="stTable"] { font-size: 1.1rem; background-color: #ffffff !important; }
    td, th { color: #000000 !important; font-weight: 400 !important; border: 0.5px solid #eeeeee !important; }
    th { font-weight: 700 !important; background-color: #f8f9fa !important; } 
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ส่วนโปรไฟล์ครู
img_src = f"data:image/jpeg;base64,{img_b64}" if img_b64 else placeholder_img
st.markdown(f"""
<div class="main-header"><h2 style="margin:0; color:white; font-weight:700;">📋 ระบบรายงานผลคะแนน Padlet อัจฉริยะ</h2></div>
<div class="teacher-card">
    <img src="{img_src}" class="teacher-img">
    <div>
        <h1 style="margin:0; font-size: 2.5rem; color: #1b5e20; font-weight:700;">ครูตระกูล บุญชิต</h1>
        <p style="margin:0; font-size: 1.2rem; color: #333 !important;">ลำดับที่ | ชื่อกลุ่ม | ชื่อ-นามสกุล 2 คำ | ตารางขาว</p>
    </div>
</div>
""", unsafe_allow_html=True)

# ฟังก์ชันกรองชื่อ
def strict_clean_name(n, sid):
    if pd.isna(n) or str(n).strip() == "" or str(n).lower() == "nan": 
        return f"⚠️ ไม่ระบุชื่อ (เลขที่ {sid})"
    n = re.sub('<[^<]+?>', '', str(n)).replace('\n', ' ').strip()
    prefixes = ['เด็กชาย', 'เด็กหญิง', 'นางสาว', 'นาย', 'นาง', r'ด\.ช\.', r'ด\.ญ\.', r'น\.ส\.', r'น\.ส', r'ด\.ช', r'ด\.ญ', 'นส.', 'ดช.', 'ดญ.']
    junk_words = ['มีชีวิต', 'มี', 'จาก', 'เล่น', 'งาน', 'ส่งงาน']
    for p in prefixes: n = re.sub(f'^{p}', '', n).strip()
    for j in junk_words: n = re.sub(f'^{j}', '', n).strip(); n = re.sub(f' {j} ', ' ', n).strip()
    n = re.split(r'กลุ่ม|เลขที่|กิจกรรม|ชั้น|ม\.|เลข|No\.|#|ชื่อเล่น|\(|\[', n, flags=re.IGNORECASE)[0]
    n = re.sub(r'[0-9๐-๙]', '', n)
    n = re.sub(r'[^\u0E01-\u0E3A\u0E40-\u0E4E A-Za-z\s]', '', n)
    words = n.split()
    if len(words) >= 2: return f"{words[0]} {words[1]}"
    elif len(words) == 1: return words[0]
    return f"⚠️ ไม่ระบุชื่อ (เลขที่ {sid})"

def merge_similar_names(data_list):
    best_names = {}
    for item in data_list:
        sid = item['เลขที่']; name = item['ชื่อ-นามสกุล']
        if "⚠️" in name: continue
        if sid not in best_names: best_names[sid] = name
        else:
            if SequenceMatcher(None, name, best_names[sid]).ratio() > 0.75:
                if len(name) > len(best_names[sid]): best_names[sid] = name
    for item in data_list:
        sid = item['เลขที่']
        if sid in best_names and "⚠️" not in item['ชื่อ-นามสกุล']:
            item['ชื่อ-นามสกุล'] = best_names[sid]
    return data_list

# --- ส่วนที่ครูต้องระวัง (ห้ามลบบรรทัดนี้เด็ดขาด) ---
uploaded_files = st.file_uploader("📂 อัปโหลดไฟล์ Excel/CSV จาก Padlet", type=["csv", "xlsx"], accept_multiple_files=True)

if uploaded_files:
    all_raw_data = []
    full_acts = [f"1.{i}" for i in range(1, 15)]

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
                    raw_grp = str(row[col_group]).strip() if col_group else ""
                    group_display = f"กลุ่มที่ {raw_grp}" if raw_grp and raw_grp != "nan" else f"กลุ่มที่ {f.name.split('.')[0]}"
                    if "กลุ่มที่" not in group_display: group_display = f"กลุ่มที่ {group_display}"
                    name_candidates = [row.get('Subject'), row.get('เนื้อหา'), row.get('Body')]
                    raw_name = next((str(x) for x in name_candidates if pd.notna(x) and str(x).strip() != ""), "")
                    all_raw_data.append({
                        'เลขที่': sid, 'ระดับ': level, 'ชื่อ-นามสกุล': strict_clean_name(raw_name, sid),
                        'ชื่อกลุ่ม': group_display, 'กิจกรรม': f"1.{act_match.group(1)}"
                    })
        except: continue

    if all_raw_data:
        final_data = merge_similar_names(all_raw_data)
        df_master = pd.DataFrame(final_data).drop_duplicates()
        for lv in sorted(df_master['ระดับ'].unique()):
            st.markdown(f'<div class="level-header">📍 ระดับชั้น {lv}</div>', unsafe_allow_html=True)
            df_lv = df_master[df_master['ระดับ'] == lv]
            pivot = df_lv.pivot_table(index=['เลขที่', 'ชื่อ-นามสกุล', 'ชื่อกลุ่ม'], columns='กิจกรรม', values='ระดับ', aggfunc='count').fillna(0).astype(int)
            for act in full_acts: 
                if act not in pivot.columns: pivot[act] = 0
            res = pivot[full_acts].copy(); res['รวม'] = res.sum(axis=1); res = res.reset_index()
            res['is_missing'] = res['ชื่อ-นามสกุล'].apply(lambda x: 1 if "⚠️" in str(x) else 0)
            res = res.sort_values(by=['is_missing', 'เลขที่']).drop(columns=['is_missing']).reset_index(drop=True)
            res.insert(0, 'ลำดับที่', res.index + 1)
            cols_final = ['ลำดับที่', 'ชื่อกลุ่ม', 'ชื่อ-นามสกุล'] + full_acts + ['รวม']
            st.dataframe(
                res[cols_final].style.set_properties(**{'background-color': '#ffffff', 'color': '#000000', 'text-align': 'center'})
                .set_properties(subset=['ชื่อ-นามสกุล', 'ชื่อกลุ่ม'], **{'text-align': 'left'})
                .apply(lambda x: ['background-color: #fff0f0; color: #d32f2f;' if "⚠️" in str(x['ชื่อ-นามสกุล']) else 'background-color: #ffffff;' for _ in x], axis=1)
                .format({a: lambda x: '✔' if x >= 1 else '-' for a in full_acts}),
                use_container_width=True, hide_index=True
            )
            st.download_button(f"📥 โหลดไฟล์ {lv}", res[cols_final].to_csv(index=False).encode('utf-8-sig'), f"Summary_{lv}.csv")
