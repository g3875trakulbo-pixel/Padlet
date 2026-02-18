import streamlit as st
import pandas as pd
import re
from io import BytesIO

# --- 1. ตั้งค่าหน้าจอ (Full Width & Expanded Space) ---
st.set_page_config(page_title="ระบบครูตระกูล v10.0", layout="wide")

def inject_custom_css():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@400;700&display=swap');
        html, body, [class*="css"] { font-family: 'Sarabun', sans-serif; }
        .main-header { background: linear-gradient(90deg, #0d47a1, #42a5f5); padding: 20px; border-radius: 10px; text-align: center; color: white; margin-bottom: 20px; }
        .stDataFrame { width: 100% !important; }
    </style>
    """, unsafe_allow_html=True)

def normalize_name(text):
    """ฟอกชื่อให้สะอาดที่สุดเพื่อใช้เป็นกุญแจหลักในการรวมข้อมูล"""
    if not text or pd.isna(text): return ""
    t = str(text).replace(" ", "").replace("\xa0", "")
    t = re.sub(r'(เด็กชาย|เด็กหญิง|นาย|นางสาว|ด\.ช\.|ด\.ญ\.|น\.ส\.|นาง|ชื่อ|นามสกุล|:|：)', '', t)
    return t.strip()

# --- 2. ฟังก์ชันประมวลผล (The Final Merge Logic) ---

def process_ultimate_merge(m_files, p_files):
    # 1. ดึงรายชื่อจากฝ่ายทะเบียนเป็นตัวตั้งต้น (Master Template)
    master_db = []
    for f in m_files:
        try:
            df = pd.read_excel(f) if f.name.endswith(('.xlsx', '.xls')) else pd.read_csv(f, encoding='utf-8-sig')
            c_sid = next((c for c in df.columns if "เลขที่" in str(c)), None)
            c_name = next((c for c in df.columns if any(k in str(c) for k in ["ชื่อ", "นามสกุล"])), None)
            
            if c_name:
                room_label = f.name.split('.')[0]
                room_id = "".join(re.findall(r'\d+', room_label)) # รหัสห้องจริง
                for _, row in df.iterrows():
                    master_db.append({
                        'name_key': normalize_name(row[c_name]),
                        'เลขที่_ทะเบียน': str(int(row[c_sid])) if c_sid and not pd.isna(row[c_sid]) else "-",
                        'ชื่อ_ทะเบียน': str(row[c_name]).strip(),
                        'ห้อง_ทะเบียน': room_label,
                        'room_id_จริง': room_id
                    })
        except: continue
    
    # 🌟 บังคับให้ Master มี 1 ชื่อต่อ 1 แถวเท่านั้น
    df_final = pd.DataFrame(master_db).drop_duplicates(subset=['name_key'])

    # 2. รวบรวมงานจาก Padlet และทำเครื่องหมายความถูกต้อง
    acts = [f"1.{i}" for i in range(1, 15)]
    for a in acts: df_final[a] = 0

    for f in p_files:
        try:
            df = pd.read_excel(f) if f.name.endswith(('.xlsx', '.xls')) else pd.read_csv(f, encoding='utf-8-sig')
            col_sec = next((c for c in df.columns if any(k in str(c).lower() for k in ["ส่วน", "ห้อง"])), None)
            for _, row in df.iterrows():
                content = " ".join(map(str, row.values))
                act_match = re.search(r'1\.(\d{1,2})', content)
                sid_match = re.search(r'(?:เลขที่|No\.|#|n)\s*(\d+)', content, re.I)
                
                if act_match:
                    act_name = f"1.{act_match.group(1)}"
                    raw_room = str(row[col_sec]) if col_sec else ""
                    room_typed = "".join(re.findall(r'\d+', raw_room))
                    sid_typed = sid_match.group(1) if sid_match else None
                    
                    # 🚀 ขั้นตอนการ Match และ Aggregate (รวมงานเข้าหาชื่อเดิม)
                    for idx, student in df_final.iterrows():
                        if student['name_key'] != "" and student['name_key'] in normalize_name(content):
                            # เช็คข้อมูลแฝง (เลขที่/ห้อง)
                            is_wrong = False
                            if sid_typed and sid_typed != student['เลขที่_ทะเบียน']: is_wrong = True
                            if room_typed and student['room_id_จริง'] not in room_typed: is_wrong = True
                            
                            # อัปเดตสถานะ (ถ้าเคยเป็น 1 (ตรง) แล้ว ไม่ต้องเปลี่ยนเป็น 2 (เตือน))
                            current = df_final.at[idx, act_name]
                            if is_wrong:
                                if current == 0: df_final.at[idx, act_name] = 2
                            else:
                                df_final.at[idx, act_name] = 1
        except: continue
                    
    return df_final, acts

# --- 3. ส่วนแสดงผล ---

def main():
    inject_custom_css()
    st.markdown('<div class="main-header"><h3>📋 ระบบเช็คงานอัตโนมัติครูตระกูล v10.0 (Ultimate Merge)</h3></div>', unsafe_allow_html=True)

    with st.sidebar:
        st.header("⚙️ การจัดการไฟล์")
        m_files = st.file_uploader("1. ไฟล์รายชื่อฝ่ายทะเบียน", accept_multiple_files=True)
        p_files = st.file_uploader("2. ไฟล์ส่งออกจาก Padlet", accept_multiple_files=True)

    if m_files and p_files:
        df_res, acts = process_ultimate_merge(m_files, p_files)
        
        for room in sorted(df_res['ห้อง_ทะเบียน'].unique()):
            st.markdown(f"#### 🏫 ห้อง: {room}")
            room_df = df_res[df_res['ห้อง_ทะเบียน'] == room].copy()
            room_df['สรุปส่ง'] = room_df[acts].apply(lambda x: (x > 0).sum(), axis=1)
            
            # แปลงรหัสเป็นสัญลักษณ์เพื่อความสวยงาม
            display_df = room_df.copy()
            for a in acts:
                display_df[a] = display_df[a].map({1: "✅", 2: "⚠️", 0: "-"})
            
            # ขยายพื้นที่ตารางสรุปตามความต้องการ
            st.dataframe(
                display_df[['เลขที่_ทะเบียน', 'ชื่อ_ทะเบียน'] + acts + ['สรุปส่ง']]
                .rename(columns={'เลขที่_ทะเบียน': 'เลขที่', 'ชื่อ_ทะเบียน': 'ชื่อ-นามสกุล'}),
                use_container_width=True, 
                hide_index=True,
                height=800 # ปรับความสูงให้พอดีกับพื้นที่หน้าจอ
            )
            
            # ปุ่มดาวน์โหลด Excel ที่สมบูรณ์
            buf = BytesIO()
            room_df.to_excel(buf, index=False)
            st.download_button(f"📥 ดาวน์โหลดสรุป Excel {room}", buf.getvalue(), f"Official_Report_{room}.xlsx")
    else:
        st.info("👋 คุณครูตระกูลครับ กรุณาอัปโหลดไฟล์รายชื่อและไฟล์งานเพื่อเริ่มระบบ 'รวมชื่ออัตโนมัติ' ครับ")

if __name__ == "__main__":
    main()
