import streamlit as st
import pandas as pd
import re, os, base64
from io import BytesIO

# --- 1. การตั้งค่าหน้าจอและสไตล์ (UI/UX) ---
st.set_page_config(page_title="ระบบครูตระกูล v9.8", layout="wide")

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
    """ดึงภาพโปรไฟล์ครูตระกูล (รองรับ jpeg, jpg, png)"""
    for ext in ["jpeg", "jpg", "png"]:
        path = f"teacher.{ext}"
        if os.path.exists(path):
            with open(path, "rb") as f:
                return f"data:image/{ext};base64," + base64.b64encode(f.read()).decode()
    return "https://cdn-icons-png.flaticon.com/512/3429/3429433.png"

# --- 2. ฟังก์ชันประมวลผลข้อมูล (Data Processing) ---

def process_master_files(files):
    """แยกกลุ่มไฟล์รายชื่อตามระดับชั้น"""
    levels_db = {}
    for f in files:
        name = f.name.replace('.xlsx', '').replace('.csv', '').split(' - ')[0]
        # ดึงระดับชั้นจากชื่อไฟล์ เช่น "ม.3"
        level_match = re.search(r'(ม\.\d+)', name)
        level = level_match.group(1) if level_match else "ระดับชั้นอื่น ๆ"
        
        df = pd.read_csv(f, encoding='utf-8-sig') if f.name.endswith('.csv') else pd.read_excel(f)
        c_sid = next((c for c in df.columns if "เลขที่" in str(c)), None)
        c_name = next((c for c in df.columns if "ชื่อ" in str(c)), None)
        
        if c_sid and c_name:
            df_clean = df[[c_sid, c_name]].copy().dropna()
            df_clean.columns = ['เลขที่', 'ชื่อ - นามสกุล']
            df_clean['เลขที่'] = pd.to_numeric(df_clean['เลขที่'], errors='coerce').fillna(0).astype(int)
            
            if level not in levels_db: levels_db[level] = {}
            levels_db[level][name] = df_clean
    return levels_db

def process_padlet_files(files):
    """ดึงข้อมูลกิจกรรมจากไฟล์ Padlet"""
    data = []
    for f in files:
        df = pd.read_csv(f, encoding='utf-8-sig') if f.name.endswith('.csv') else pd.read_excel(f)
        col_sec = next((c for c in df.columns if any(k in str(c) for k in ["ส่วน", "Section", "ห้อง"])), None)
        for _, row in df.iterrows():
            txt = " ".join(map(str, row.values))
            sid = re.search(r'(?:เลขที่|No\.|#)\s*(\d+)', txt)
            act = re.search(r'1\.(\d{1,2})', txt)
            if sid and act:
                data.append({
                    'เลขที่': int(sid.group(1)),
                    'กิจกรรม': f"1.{act.group(1)}",
                    'ห้อง_padlet': str(row[col_sec]).strip() if col_sec else ""
                })
    return pd.DataFrame(data).drop_duplicates() if data else pd.DataFrame()

# --- 3. ส่วนแสดงผลแอปพลิเคชัน (Main App) ---

def main():
    inject_custom_css()
    img_src = get_image_base64()
    
    st.markdown(f"""
    <div class="main-header"><h2>📋 ระบบรายงานผลแยกตามระดับชั้น (ครูตระกูล บุญชิต)</h2></div>
    <div style="display: flex; align-items: center; gap: 20px; margin-bottom: 25px;">
        <img src="{img_src}" style="width: 100px; height: 100px; border-radius: 50%; border: 3px solid #1b5e20; object-fit: cover;">
        <div>
            <h1 style="margin:0; color: #1b5e20;">คุณครูตระกูล บุญชิต (เจมส์)</h1>
            <p style="margin:0;">โรงเรียนตระกาศประชาสามัคคี | ระบบเช็คงานอัตโนมัติ v9.8</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ส่วนอัปโหลดไฟล์
    col1, col2 = st.columns(2)
    m_files = col1.file_uploader("📂 1. อัปโหลดรายชื่อ (ระบุชั้นในชื่อไฟล์ เช่น ม.3-1)", accept_multiple_files=True)
    p_files = col2.file_uploader("📂 2. อัปโหลดงานจาก Padlet", accept_multiple_files=True)

    if m_files and p_files:
        levels_db = process_master_files(m_files)
        df_padlet = process_padlet_files(p_files)
        
        if not df_padlet.empty:
            full_acts = [f"1.{i}" for i in range(1, 15)]
            pivot = df_padlet.pivot_table(index=['เลขที่', 'ห้อง_padlet'], columns='กิจกรรม', aggfunc='size', fill_value=0).reset_index()

            # แสดงผลตารางแยกตามระดับชั้น
            for level in sorted(levels_db.keys()):
                st.markdown(f'<div class="level-section">📚 ระดับชั้น {level}</div>', unsafe_allow_html=True)
                
                for room, room_list in levels_db[level].items():
                    # Logic Matching ห้องเรียน
                    room_num = "".join(re.findall(r'\d+', room))
                    r_pivot = pivot[pivot['ห้อง_padlet'].str.contains(room_num, na=False) | (pivot['ห้อง_padlet'] == "")]
                    if r_pivot.empty: r_pivot = pivot

                    # รวมข้อมูลและเพิ่มคอลัมน์ "ชั้น"
                    final_df = room_list.merge(r_pivot, on='เลขที่', how='left').fillna(0)
                    final_df['ชั้น'] = level
                    
                    for a in full_acts: 
                        if a not in final_df.columns: final_df[a] = 0
                    
                    final_df['รวม'] = final_df[full_acts].sum(axis=1)
                    final_df = final_df.sort_values('เลขที่').reset_index(drop=True)
                    final_df.insert(0, 'ลำดับ', final_df.index + 1)
                    
                    # จัดเรียงคอลัมน์ใหม่
                    cols = ['ลำดับ', 'เลขที่', 'ชั้น', 'ชื่อ - นามสกุล'] + full_acts + ['รวม']
                    final_df = final_df[cols]

                    # ส่วนแสดงผลแต่ละห้อง
                    st.markdown(f'<div class="room-label">🏫 ห้อง: {room} (นักเรียน {len(room_list)} คน)</div>', unsafe_allow_html=True)
                    
                    # ปุ่มดาวน์โหลด Excel (ใช้ xlsxwriter)
                    buf = BytesIO()
                    with pd.ExcelWriter(buf, engine='xlsxwriter') as writer:
                        final_df.to_excel(writer, index=False, sheet_name=room)
                    st.download_button(f"📥 โหลดไฟล์ Excel {room}", buf.getvalue(), f"Check_{room}.xlsx", key=f"btn_{room}")

                    # แสดงตารางบนหน้าเว็บ
                    st.dataframe(
                        final_df.style.format({a: lambda x: '✔' if x >= 1 else '-' for a in full_acts})
                        .set_properties(**{'text-align': 'center'})
                        .set_properties(subset=['ชื่อ - นามสกุล'], **{'text-align': 'left'}),
                        use_container_width=True, hide_index=True
                    )
    else:
        st.info("💡 กรุณาอัปโหลดไฟล์รายชื่อ (ม.1, ม.2, ม.3) และไฟล์ Padlet เพื่อเริ่มระบบครับ")

if __name__ == "__main__":
    main()
