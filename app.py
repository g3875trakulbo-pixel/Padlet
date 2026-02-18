import streamlit as st
import pandas as pd
import re
from io import BytesIO

# --- 1. UI/UX และการตั้งค่าหน้าจอ (คงเอกลักษณ์เดิม) ---
st.set_page_config(page_title="ระบบครูตระกูล v10.5", layout="wide")

def inject_custom_css():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@400;700&display=swap');
        html, body, [class*="css"] { font-family: 'Sarabun', sans-serif; }
        .main-header { background: linear-gradient(90deg, #1b5e20, #4caf50); padding: 20px; border-radius: 10px; text-align: center; color: white; margin-bottom: 25px; }
        .room-header { background-color: #e8f5e9; border-left: 10px solid #2e7d32; padding: 10px 20px; border-radius: 5px; margin: 30px 0 10px 0; color: #1b5e20; font-weight: bold; font-size: 1.5rem; }
    </style>
    """, unsafe_allow_html=True)

def normalize_name(text):
    """ฟอกชื่อเพื่อใช้เป็น Key ในการดึงงานจากกองกลางไปใส่รายห้อง"""
    if not text or pd.isna(text): return ""
    t = str(text).replace(" ", "").replace("\xa0", "")
    t = re.sub(r'(เด็กชาย|เด็กหญิง|นาย|นางสาว|ด\.ช\.|ด\.ญ\.|น\.ส\.|นาง|ชื่อ|นามสกุล|:|：)', '', t)
    return t.strip()

# --- 2. ฟังก์ชันประมวลผล (Core Logic: Merge & Partition) ---

def process_vertical_sync(m_files, p_files):
    # 1. รวบรวมรายชื่อ Master (แม่แบบทะเบียน)
    master_db = []
    for f in m_files:
        try:
            df = pd.read_excel(f) if f.name.endswith(('.xlsx', '.xls')) else pd.read_csv(f, encoding='utf-8-sig')
            c_sid = next((c for c in df.columns if "เลขที่" in str(c)), None)
            c_name = next((c for c in df.columns if any(k in str(c) for k in ["ชื่อ", "นามสกุล"])), None)
            
            if c_name:
                room_name = f.name.split('.')[0] # ชื่อห้องจากชื่อไฟล์
                for _, row in df.iterrows():
                    master_db.append({
                        'name_key': normalize_name(row[c_name]),
                        'เลขที่_จริง': str(int(row[c_sid])) if c_sid and not pd.isna(row[c_sid]) else "-",
                        'ชื่อ_ทะเบียน': str(row[c_name]).strip(),
                        'ห้อง_จริง': room_name
                    })
        except: continue
    
    df_all = pd.DataFrame(master_db).drop_duplicates(subset=['name_key'])

    # 2. รวบรวมงานจาก Padlet ทุกไฟล์ (กองกลาง)
    acts = [f"1.{i}" for i in range(1, 15)]
    for a in acts: df_all[a] = 0

    works_pool = []
    for f in p_files:
        try:
            df_p = pd.read_excel(f) if f.name.endswith(('.xlsx', '.xls')) else pd.read_csv(f, encoding='utf-8-sig')
            for _, row in df_p.iterrows():
                content = " ".join(map(str, row.values))
                act_match = re.search(r'1\.(\d{1,2})', content)
                if act_match:
                    works_pool.append({
                        'content_key': normalize_name(content),
                        'act_name': f"1.{act_match.group(1)}"
                    })
        except: continue

    # 3. กระจายงานจากกองกลางเข้าสู่รายชื่อในแต่ละห้อง
    for work in works_pool:
        mask = df_all['name_key'].apply(lambda k: k in work['content_key'] if k != "" else False)
        df_all.loc[mask, work['act_name']] = 1
        
    return df_all, acts

# --- 3. ส่วนการแสดงผลแบบยาวต่อเนื่อง ---

def main():
    inject_custom_css()
    st.markdown('<div class="main-header"><h3>📋 ระบบสรุปผลการส่งงานครูตระกูล v10.5</h3></div>', unsafe_allow_html=True)

    with st.sidebar:
        st.header("📂 อัปโหลดไฟล์")
        m_files = st.file_uploader("1. รายชื่อฝ่ายทะเบียน (แยกห้อง)", accept_multiple_files=True)
        p_files = st.file_uploader("2. ข้อมูลส่งงานจาก Padlet", accept_multiple_files=True)

    if m_files and p_files:
        df_res, acts = process_vertical_sync(m_files, p_files)
        
        # ค้นหาห้องทั้งหมดที่มีในระบบ
        rooms = sorted(df_res['ห้อง_จริง'].unique())
        
        for room in rooms:
            # สร้างส่วนหัวของแต่ละห้อง
            st.markdown(f'<div class="room-header">🏫 ห้อง: {room}</div>', unsafe_allow_html=True)
            
            # กรองข้อมูลและคำนวณสรุป
            room_df = df_res[df_res['ห้อง_จริง'] == room].copy()
            room_df['สรุปส่ง'] = room_df[acts].sum(axis=1)
            
            # ตกแต่งสัญลักษณ์สรุป
            display_df = room_df.copy()
            for a in acts:
                display_df[a] = display_df[a].map({1: "✅", 0: "❌"})
            
            # แสดงตารางแบบขยายพื้นที่ (UI เต็มความกว้าง)
            st.dataframe(
                display_df[['เลขที่_จริง', 'ชื่อ_ทะเบียน'] + acts + ['สรุปส่ง']]
                .rename(columns={'เลขที่_จริง': 'เลขที่', 'ชื่อ_ทะเบียน': 'ชื่อ-นามสกุล'}),
                use_container_width=True, 
                hide_index=True,
                height=500 # ปรับความสูงต่อตารางได้ตามเหมาะสม
            )
            
            # ปุ่มดาวน์โหลด Excel แยกห้อง
            buf = BytesIO()
            room_df.to_excel(buf, index=False)
            st.download_button(f"📥 ดาวน์โหลดไฟล์ Excel (ห้อง {room})", buf.getvalue(), f"Report_{room}.xlsx", key=f"dl_{room}")
            
    else:
        st.info("💡 คำแนะนำ: ระบบจะรวบรวมงานจาก Padlet และส่งงานเหล่านั้นกลับไปที่ห้องเรียนที่ถูกต้องตามรายชื่อฝ่ายทะเบียนครับ")

if __name__ == "__main__":
    main()
