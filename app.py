import streamlit as st
import pandas as pd
import re, os, base64
from io import BytesIO

# --- 1. CONFIG & STYLES ---
st.set_page_config(page_title="ระบบครูตระกูล v9.7", layout="wide")

def inject_custom_css():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@400;700&display=swap');
        html, body, [class*="css"] { font-family: 'Sarabun', sans-serif; background-color: #ffffff; }
        .main-header { background-color: #1b5e20; padding: 25px; border-radius: 15px; text-align: center; color: white; border-bottom: 5px solid #4caf50; margin-bottom: 20px;}
        .teacher-card { background-color: #f8f9fa; border: 1px solid #dee2e6; border-radius: 15px; padding: 30px; margin-bottom: 35px; display: flex; align-items: center; gap: 30px; }
        .teacher-img { width: 130px; height: 130px; border-radius: 50%; border: 5px solid #1b5e20; object-fit: cover; }
        .room-label { background-color: #e8f5e9; padding: 15px; border-left: 10px solid #2e7d32; border-radius: 5px; margin-top: 40px; font-size: 1.2rem; font-weight: bold; color: #1b5e20; }
    </style>
    """, unsafe_allow_html=True)

def get_image_base64():
    """ค้นหาไฟล์ภาพที่มีในระบบ (รองรับหลายนามสกุล)"""
    for ext in ["jpeg", "jpg", "png"]:
        path = f"teacher.{ext}"
        if os.path.exists(path):
            with open(path, "rb") as f:
                return f"data:image/{ext};base64," + base64.b64encode(f.read()).decode()
    return "https://cdn-icons-png.flaticon.com/512/3429/3429433.png" # ภาพสำรองกรณีไม่พบไฟล์

# --- 2. DATA PROCESSING --- (ส่วนนี้คงเดิมเพื่อความเสถียร)
def process_master_files(files):
    db = {}
    for f in files:
        name = f.name.replace('.xlsx', '').replace('.csv', '').split(' - ')[0]
        df = pd.read_csv(f, encoding='utf-8-sig') if f.name.endswith('.csv') else pd.read_excel(f)
        c_sid = next((c for c in df.columns if "เลขที่" in str(c)), None)
        c_name = next((c for c in df.columns if "ชื่อ" in str(c)), None)
        if c_sid and c_name:
            df_clean = df[[c_sid, c_name]].copy().dropna()
            df_clean.columns = ['เลขที่', 'ชื่อ - นามสกุล']
            df_clean['เลขที่'] = pd.to_numeric(df_clean['เลขที่'], errors='coerce').fillna(0).astype(int)
            db[name] = df_clean
    return db

def process_padlet_files(files):
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

# --- 3. MAIN APP ---
def main():
    inject_custom_css()
    img_src = get_image_base64() # ดึงภาพโปรไฟล์
    
    st.markdown(f"""
    <div class="main-header"><h2 style="margin:0; color:white;">📋 ระบบรายงานผลและเตรียมใบปริ้น (v9.7)</h2></div>
    <div class="teacher-card">
        <img src="{img_src}" class="teacher-img">
        <div>
            <h1 style="margin:0; color: #1b5e20;">ครูตระกูล บุญชิต</h1>
            <p style="margin:0;">โรงเรียนตระกาศประชาสามัคคี | Kantharalak District</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    m_files = col1.file_uploader("📂 1. อัปโหลดรายชื่อแยกห้อง", accept_multiple_files=True)
    p_files = col2.file_uploader("📂 2. อัปโหลดงานจาก Padlet", accept_multiple_files=True)

    if m_files and p_files:
        rooms_db = process_master_files(m_files)
        df_padlet = process_padlet_files(p_files)
        
        if not df_padlet.empty:
            full_acts = [f"1.{i}" for i in range(1, 15)]
            pivot = df_padlet.pivot_table(index=['เลขที่', 'ห้อง_padlet'], columns='กิจกรรม', aggfunc='size', fill_value=0).reset_index()

            for room, room_list in rooms_db.items():
                room_num = "".join(re.findall(r'\d+', room))
                r_pivot = pivot[pivot['ห้อง_padlet'].str.contains(room_num, na=False) | (pivot['ห้อง_padlet'] == "")]
                if r_pivot.empty: r_pivot = pivot

                final_df = room_list.merge(r_pivot, on='เลขที่', how='left').fillna(0)
                for a in full_acts: 
                    if a not in final_df.columns: final_df[a] = 0
                
                final_df['รวม'] = final_df[full_acts].sum(axis=1)
                final_df = final_df.sort_values('เลขที่').reset_index(drop=True)
                final_df.insert(0, 'ลำดับที่', final_df.index + 1)
                
                st.markdown(f'<div class="room-label">🏫 ห้อง: {room}</div>', unsafe_allow_html=True)
                
                # Excel Export logic (xlsxwriter)
                buffer = BytesIO()
                with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                    final_df.to_excel(writer, index=False, sheet_name=room)
                
                st.download_button(f"📥 ดาวน์โหลดไฟล์ปริ้น {room}", buffer.getvalue(), f"ใบเช็คงาน_{room}.xlsx", key=f"dl_{room}")
                
                st.dataframe(
                    final_df.style.set_properties(**{'background-color': '#ffffff', 'color': '#000000', 'text-align': 'center'})
                    .format({a: lambda x: '✔' if x >= 1 else '-' for a in full_acts}),
                    use_container_width=True, hide_index=True
                )

            # Summary Section
            st.divider()
            st.subheader("📈 สรุปภาพรวมทุกห้อง")
            summary = []
            for r, r_l in rooms_db.items():
                r_num = "".join(re.findall(r'\d+', r))
                res = r_l.merge(pivot[pivot['ห้อง_padlet'].str.contains(r_num, na=False) | (pivot['ห้อง_padlet'] == "")], on='เลขที่', how='left').fillna(0)
                row = res[full_acts].apply(lambda x: (x >= 1).sum()).to_dict()
                row.update({'ห้อง': r, 'นักเรียน': len(r_l)})
                summary.append(row)
            st.table(pd.DataFrame(summary)[['ห้อง', 'นักเรียน'] + full_acts])
    else:
        st.info("กรุณาอัปโหลดไฟล์ให้ครบเพื่อเริ่มการประมวลผล")

if __name__ == "__main__":
    main()
