import streamlit as st
import pandas as pd
import re, os, base64
from io import BytesIO

# --- 1. การตั้งค่าหน้าจอและสไตล์ (UI/UX เดิมที่คุณครูออกแบบ) ---
st.set_page_config(page_title="ระบบครูตระกูล v10.1", layout="wide")

def inject_custom_css():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@400;700&display=swap');
        html, body, [class*="css"] { font-family: 'Sarabun', sans-serif; background-color: #ffffff; }
        .main-header { background-color: #1b5e20; padding: 25px; border-radius: 15px; text-align: center; color: white; border-bottom: 5px solid #4caf50; margin-bottom: 25px;}
        .level-section { background-color: #e8f5e9; padding: 15px; border-radius: 10px; border-left: 10px solid #2e7d32; margin: 30px 0 15px 0; font-size: 1.8rem; font-weight: bold; color: #1b5e20; }
        .room-label { background-color: #f1f8e9; padding: 10px 15px; border-left: 5px solid #8bc34a; border-radius: 5px; margin: 15px 0; font-weight: bold; color: #33691e; }
    </style>
    """, unsafe_allow_html=True)

def get_image_base64():
    """ดึงภาพโปรไฟล์ครูตระกูล (คงเดิม)"""
    for ext in ["jpeg", "jpg", "png"]:
        path = f"teacher.{ext}"
        if os.path.exists(path):
            with open(path, "rb") as f:
                return f"data:image/{ext};base64," + base64.b64encode(f.read()).decode()
    return "https://cdn-icons-png.flaticon.com/512/3429/3429433.png"

def normalize_name(text):
    """ฟอกชื่อเพื่อใช้เป็นกุญแจสำคัญในการรวมรายชื่อที่ซ้ำกัน"""
    if not text or pd.isna(text): return ""
    t = str(text).replace(" ", "").replace("\xa0", "")
    t = re.sub(r'(เด็กชาย|เด็กหญิง|นาย|นางสาว|ด\.ช\.|ด\.ญ\.|น\.ส\.|นาง|ชื่อ|นามสกุล|:|：)', '', t)
    return t.strip()

# --- 2. ฟังก์ชันประมวลผลข้อมูล (ปรับปรุง Logic การรวมชื่อ) ---

def process_ultimate_sync(m_files, p_files):
    # 1. สร้างฐานข้อมูลจากรายชื่อฝ่ายทะเบียน (ยึดเป็นแม่แบบหลัก)
    master_db = []
    for f in m_files:
        df = pd.read_excel(f) if f.name.endswith(('.xlsx', '.xls')) else pd.read_csv(f, encoding='utf-8-sig')
        c_sid = next((c for c in df.columns if "เลขที่" in str(c)), None)
        c_name = next((c for c in df.columns if any(k in str(c) for k in ["ชื่อ", "นามสกุล"])), None)
        if c_name:
            room_name = f.name.split('.')[0]
            room_id = "".join(re.findall(r'\d+', room_name))
            for _, row in df.iterrows():
                master_db.append({
                    'name_key': normalize_name(row[c_name]),
                    'เลขที่_จริง': str(int(row[c_sid])) if c_sid and not pd.isna(row[c_sid]) else "-",
                    'ชื่อ_ทะเบียน': str(row[c_name]).strip(),
                    'ห้อง_ทะเบียน': room_name,
                    'room_id_จริง': room_id
                })
    df_final = pd.DataFrame(master_db).drop_duplicates(subset=['name_key'])

    # 2. จัดการข้อมูลจาก Padlet (ใช้ Logic รวมงานเข้าหาชื่อเดียว)
    acts = [f"1.{i}" for i in range(1, 15)]
    for a in acts: df_final[a] = 0

    for f in p_files:
        df_p = pd.read_excel(f) if f.name.endswith(('.xlsx', '.xls')) else pd.read_csv(f, encoding='utf-8-sig')
        col_sec = next((c for c in df_p.columns if any(k in str(c).lower() for k in ["ส่วน", "ห้อง"])), None)
        for _, row in df_p.iterrows():
            content = " ".join(map(str, row.values))
            act_match = re.search(r'1\.(\d{1,2})', content)
            if act_match:
                act_name = f"1.{act_match.group(1)}"
                sid_typed = re.search(r'(?:เลขที่|No\.|#|n)\s*(\d+)', content, re.I)
                raw_room = str(row[col_sec]) if col_sec else ""
                room_typed = "".join(re.findall(r'\d+', raw_room))
                
                # Matching & Aggregating: รวมงานเข้าสู่รายชื่อ Master
                for idx, student in df_final.iterrows():
                    if student['name_key'] != "" and student['name_key'] in normalize_name(content):
                        # ตรวจสอบข้อมูลแฝงที่อาจพิมพ์ผิด
                        is_wrong = (sid_typed and sid_typed.group(1) != student['เลขที่_จริง']) or \
                                   (room_typed and student['room_id_จริง'] not in room_typed)
                        
                        current = df_final.at[idx, act_name]
                        if is_wrong:
                            if current == 0: df_final.at[idx, act_name] = 2 # 2 คือ ⚠
                        else:
                            df_final.at[idx, act_name] = 1 # 1 คือ ✔
    return df_final, acts

# --- 3. ส่วนแสดงผลแอปพลิเคชัน (UI/UX เดิม) ---

def main():
    inject_custom_css()
    img_src = get_image_base64()
    
    st.markdown(f"""
    <div class="main-header"><h2>📋 ระบบรายงานผลแยกตามระดับชั้น (ครูตระกูล บุญชิต)</h2></div>
    <div style="display: flex; align-items: center; gap: 20px; margin-bottom: 25px;">
        <img src="{img_src}" style="width: 100px; height: 100px; border-radius: 50%; border: 3px solid #1b5e20; object-fit: cover;">
        <div>
            <h1 style="margin:0; color: #1b5e20;">คุณครูตระกูล บุญชิต (เจมส์)</h1>
            <p style="margin:0;">โรงเรียนตระกาศประชาสามัคคี | ระบบเช็คงานอัตโนมัติ v10.1</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    m_files = col1.file_uploader("📂 1. อัปโหลดรายชื่อ (ฝ่ายทะเบียน)", accept_multiple_files=True)
    p_files = col2.file_uploader("📂 2. อัปโหลดงานจาก Padlet", accept_multiple_files=True)

    if m_files and p_files:
        df_res, acts = process_ultimate_sync(m_files, p_files)
        
        # จัดกลุ่มและแสดงผลตามระดับชั้นจากชื่อห้อง
        df_res['ระดับชั้น'] = df_res['ห้อง_ทะเบียน'].apply(lambda x: re.search(r'(ม\.\d+)', x).group(1) if re.search(r'(ม\.\d+)', x) else "อื่นๆ")
        
        for level in sorted(df_res['ระดับชั้น'].unique()):
            st.markdown(f'<div class="level-section">📚 ระดับชั้น {level}</div>', unsafe_allow_html=True)
            level_df = df_res[df_res['ระดับชั้น'] == level]
            
            for room in sorted(level_df['ห้อง_ทะเบียน'].unique()):
                room_df = level_df[level_df['ห้อง_ทะเบียน'] == room].copy()
                room_df['รวม'] = room_df[acts].apply(lambda x: (x > 0).sum(), axis=1)
                
                st.markdown(f'<div class="room-label">🏫 ห้อง: {room} (นักเรียน {len(room_df)} คน)</div>', unsafe_allow_html=True)
                
                # แปลงรหัสเป็นสัญลักษณ์ (✔, ⚠, -)
                display_df = room_df.copy()
                for a in acts:
                    display_df[a] = display_df[a].map({1: "✔", 2: "⚠", 0: "-"})
                
                # แสดงตารางสรุปแบบขยายพื้นที่ (UI เดิมแต่ Logic ใหม่)
                st.dataframe(
                    display_df[['เลขที่_จริง', 'ชื่อ_ทะเบียน'] + acts + ['รวม']]
                    .rename(columns={'เลขที่_จริง': 'เลขที่', 'ชื่อ_ทะเบียน': 'ชื่อ - นามสกุล'}),
                    use_container_width=True, hide_index=True
                )
                
                # ปุ่มดาวน์โหลด Excel
                buf = BytesIO()
                room_df.to_excel(buf, index=False)
                st.download_button(f"📥 โหลดไฟล์ Excel {room}", buf.getvalue(), f"Summary_{room}.xlsx", key=f"btn_{room}")
    else:
        st.info("💡 กรุณาอัปโหลดไฟล์รายชื่อฝ่ายทะเบียนและไฟล์ Padlet เพื่อเริ่มระบบครับ")

if __name__ == "__main__":
    main()
