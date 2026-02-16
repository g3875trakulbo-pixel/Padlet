import streamlit as st
import pandas as pd
import re, os, base64

# --- 1. การตั้งค่าหน้าตา ---
st.set_page_config(page_title="ระบบครูตระกูล v5.0", layout="wide")

st.markdown("""
<style>
    .main-header { background-color: #1b5e20; padding: 20px; border-radius: 12px; text-align: center; color: white; }
    .level-header { background-color: #2e7d32; color: white; padding: 10px 20px; border-radius: 8px; margin-top: 30px; font-weight: bold; }
    .stDataFrame { border: 1px solid #e0e0e0; border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

# --- 2. ฟังก์ชันล้างชื่อ (ตัดคำนำหน้าออก) ---
def strict_clean_name(n, sid):
    if pd.isna(n) or str(n).strip() == "" or str(n).lower() == "nan": 
        return f"⚠️ ไม่ระบุชื่อ (เลขที่ {sid})"
    
    n = re.sub('<[^<]+?>', '', str(n)).replace('\n', ' ').strip()
    
    # ลบคำนำหน้าชื่อทุกรูปแบบ
    prefixes = ['เด็กชาย', 'เด็กหญิง', 'นางสาว', 'นาย', 'นาง', r'ด\.ช\.', r'ด\.ญ\.', r'น\.ส\.', r'น\.ส', r'ด\.ช', r'ด\.ญ', 'นส.', 'ดช.', 'ดญ.', 'นส ', 'ดช ', 'ดญ ']
    for p in prefixes:
        n = re.sub(f'^{p}', '', n).strip()
    
    # ตัดขยะหลังชื่อ (กลุ่ม/เลขที่/ฯลฯ)
    n = re.split(r'กลุ่ม|เลขที่|กิจกรรม|ชั้น|ม\.|เลข|No\.|#|ชื่อเล่น|\(|\[', n, flags=re.IGNORECASE)[0]
    n = re.sub(r'^[0-9.\-\s]+', '', n)
    n = re.sub(r'[0-9.\-\s]+$', '', n)
    
    final_name = re.sub(r'\s+', ' ', n).strip()
    return final_name if final_name else f"⚠️ ไม่ระบุชื่อ (เลขที่ {sid})"

# --- 3. ส่วนประมวลผลไฟล์ ---
uploaded_files = st.file_uploader("📂 อัปโหลดไฟล์ Excel หรือ CSV จาก Padlet", type=["csv", "xlsx"], accept_multiple_files=True)

if uploaded_files:
    all_data = []
    full_acts = [f"กิจกรรมที่ 1.{i}" for i in range(1, 15)]

    for f in uploaded_files:
        try:
            df = pd.read_csv(f, encoding='utf-8-sig') if f.name.endswith('.csv') else pd.read_excel(f)
            
            # ค้นหาระดับชั้นจากชื่อไฟล์
            lv_match = re.search(r'([3-6])', f.name)
            level = f"ม.{lv_match.group(1)}" if lv_match else "ทั่วไป"
            file_label = f.name.split('.')[0] 
            
            for _, row in df.iterrows():
                combined_text = " ".join(map(str, row.values))
                sid_match = re.search(r'(?:เลขที่|No\.|#)\s*(\d+)', combined_text)
                act_match = re.search(r'1\.(\d{1,2})', combined_text)
                
                if sid_match and act_match:
                    sid = sid_match.group(1)
                    
                    # --- [ดึงข้อมูลกลุ่มจาก Excel โดยตรง] ---
                    group_info = ""
                    for col in df.columns:
                        if any(k in str(col) for k in ["กลุ่ม", "Group"]):
                            val = str(row[col]).strip()
                            if val != "nan" and val != "":
                                group_info = val
                                break
                    
                    if group_info:
                        # เติม "กลุ่มที่ " นำหน้าให้สวยงาม
                        if "กลุ่ม" in group_info:
                            group_display = group_info.replace("กลุ่ม", "กลุ่มที่ ").replace("ที่ ที่", "ที่")
                        else:
                            group_display = f"กลุ่มที่ {group_info}"
                    else:
                        # กรณีหาในคอลัมน์ไม่เจอ ให้ลองหาในเนื้อหาโพสต์
                        grp_text_match = re.search(r'กลุ่มที่\s*(\d+)', combined_text)
                        group_display = f"กลุ่มที่ {grp_text_match.group(1)}" if grp_text_match else f"กลุ่มที่ {file_label}"

                    # ดึงชื่อนักเรียนจาก Subject หรือเนื้อหา
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
            st.markdown(f'<div class="level-header">📊 รายงานสรุปผลชั้น {lv}</div>', unsafe_allow_html=True)
            df_lv = df_master[df_master['ระดับ'] == lv]
            
            # สร้าง Pivot Table
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

            # --- การเรียงลำดับ: เอาคนไม่มีชื่อ (มีไอคอน ⚠️) ไปไว้ท้ายตาราง ---
            res['is_missing'] = res['ชื่อ-นามสกุล'].apply(lambda x: 1 if "⚠️" in str(x) else 0)
            res = res.sort_values(by=['is_missing', 'เลขที่']).drop(columns=['is_missing'])

            # แสดงตาราง
            st.dataframe(
                res.style.set_properties(**{'text-align': 'center'})
                .set_properties(subset=['ชื่อ-นามสกุล', 'ชื่อกลุ่ม'], **{'text-align': 'left'})
                .apply(lambda x: ['background-color: #fff3f3; color: #d32f2f;' if "⚠️" in str(x['ชื่อ-นามสกุล']) else '' for _ in x], axis=1)
                .format({a: lambda x: '✔' if x >= 1 else '-' for a in full_acts}),
                use_container_width=True, hide_index=True
            )
            
            st.download_button(f"📥 โหลดไฟล์คะแนน {lv}", res.to_csv(index=False).encode('utf-8-sig'), f"Report_{lv}.csv")
    else:
        st.info("💡 กรุณาอัปโหลดไฟล์ที่มีข้อมูลเลขที่และกิจกรรมครับ")
