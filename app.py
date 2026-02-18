import streamlit as st
import pandas as pd
import re, os, base64
from io import BytesIO

# --- การตั้งค่า UI/UX สไตล์ครูตระกูล ---
st.set_page_config(page_title="ระบบครูตระกูล v11.8", layout="wide")

def get_image_base64():
    """ดึงภาพโปรไฟล์ teacher.jpg มาแสดงผล"""
    for ext in ["jpg", "jpeg", "png"]:
        path = f"teacher.{ext}"
        if os.path.exists(path):
            with open(path, "rb") as f:
                data = base64.b64encode(f.read()).decode()
                return f"data:image/{ext};base64,{data}"
    return "https://cdn-icons-png.flaticon.com/512/3429/3429433.png"

def inject_custom_css():
    st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@400;700&display=swap');
        html, body, [class*="css"] {{ font-family: 'Sarabun', sans-serif; }}
        .main-header {{ background: linear-gradient(90deg, #1b5e20, #4caf50); padding: 30px; border-radius: 15px; text-align: center; color: white; margin-bottom: 25px; border-bottom: 5px solid #2e7d32; }}
        .teacher-profile {{ display: flex; align-items: center; justify-content: center; gap: 20px; }}
        .teacher-img {{ width: 110px; height: 110px; border-radius: 50%; border: 4px solid white; object-fit: cover; box-shadow: 0 4px 10px rgba(0,0,0,0.3); }}
        .room-header {{ background-color: #f1f8e9; border-left: 12px solid #2e7d32; padding: 12px 20px; border-radius: 5px; margin: 40px 0 10px 0; color: #1b5e20; font-weight: bold; font-size: 1.7rem; }}
        .stDataFrame {{ width: 100% !important; border: 1px solid #e0e0e0; border-radius: 10px; }}
    </style>
    """, unsafe_allow_html=True)

def normalize_name(text):
    if not text or pd.isna(text): return ""
    t = str(text).replace(" ", "").replace("\xa0", "")
    t = re.sub(r'(เด็กชาย|เด็กหญิง|นาย|นางสาว|ด\.ช\.|ด\.ญ\.|น\.ส\.|นาง|ชื่อ|นามสกุล|:|：)', '', t)
    return t.strip()

# --- Logic การประมวลผลข้อมูล ---
def process_data(m_files, p_files):
    master_records = []
    for f in m_files:
        try:
            df = pd.read_excel(f) if f.name.endswith(('.xlsx', '.xls')) else pd.read_csv(f, encoding='utf-8-sig')
            c_sid = next((c for c in df.columns if "เลขที่" in str(c)), None)
            c_name = next((c for c in df.columns if any(k in str(c) for k in ["ชื่อ", "นามสกุล"])), None)
            if c_name:
                room_name = f.name.split('.')[0]
                for _, row in df.iterrows():
                    master_records.append({
                        'key': normalize_name(row[c_name]),
                        'เลขที่': str(int(row[c_sid])) if c_sid and not pd.isna(row[c_sid]) else "-",
                        'ชื่อ-นามสกุล': str(row[c_name]).strip(),
                        'ห้อง': room_name
                    })
        except: continue
    
    df_main = pd.DataFrame(master_records).drop_duplicates(subset=['key', 'ห้อง'])
    acts = [f"1.{i}" for i in range(1, 15)]
    for a in acts: df_main[a] = 0

    for f in p_files:
        try:
            df_p = pd.read_excel(f) if f.name.endswith(('.xlsx', '.xls')) else pd.read_csv(f, encoding='utf-8-sig')
            for _, row in df_p.iterrows():
                content = normalize_name(" ".join(map(str, row.values)))
                act_match = re.search(r'1\.(\d{1,2})', content)
                if act_match:
                    act_col = f"1.{act_match.group(1)}"
                    mask = df_main['key'].apply(lambda k: k in content if k != "" else False)
                    df_main.loc[mask, act_col] = 1
        except: continue
    return df_main, acts

# --- ส่วนแสดงผลหลัก ---
def main():
    inject_custom_css()
    img_base64 = get_image_base64()
    
    st.markdown(f"""
    <div class="main-header">
        <div class="teacher-profile">
            <img src="{img_base64}" class="teacher-img">
            <div style="text-align: left;">
                <h1 style="margin: 0; font-size: 2.3rem;">คุณครูตระกูล บุญชิต</h1>
                <p style="margin: 0; font-size: 1.3rem; opacity: 0.95;">ระบบรายงานผลการส่งงานแยกรายห้อง (หน้าเดียวต่อเนื่อง)</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    with st.sidebar:
        st.header("📂 จัดการไฟล์ข้อมูล")
        m_files = st.file_uploader("1. อัปโหลดรายชื่อทะเบียน (ทุกห้อง)", accept_multiple_files=True)
        p_files = st.file_uploader("2. อัปโหลดไฟล์ Padlet (ทุกไฟล์)", accept_multiple_files=True)

    if m_files and p_files:
        df_final, acts = process_data(m_files, p_files)
        df_final['รวมส่ง'] = df_final[acts].sum(axis=1)

        rooms = sorted(df_final['ห้อง'].unique())
        for room in rooms:
            st.markdown(f'<div class="room-header">🏫 ห้องเรียน: {room}</div>', unsafe_allow_html=True)
            room_df = df_final[df_final['ห้อง'] == room].copy()
            
            display_df = room_df.copy()
            for a in acts: display_df[a] = display_df[a].map({1: "✅", 0: "❌"})
            
            st.dataframe(display_df[['เลขที่', 'ชื่อ-นามสกุล'] + acts + ['รวมส่ง']], 
                         use_container_width=True, hide_index=True)
            
            buf = BytesIO()
            room_df.to_excel(buf, index=False)
            st.download_button(f"📥 โหลด Excel เฉพาะห้อง {room}", buf.getvalue(), f"Report_{room}.xlsx", key=f"dl_{room}")
    else:
        st.info("💡 กรุณาอัปโหลดไฟล์ในแถบด้านข้าง ระบบจะแสดงตารางแยกห้องต่อยาวลงไปในหน้านี้ครับ")

if __name__ == "__main__":
    main()
