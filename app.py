import streamlit as st
import pandas as pd
import re, os, base64
from difflib import SequenceMatcher

# --- 1. การตั้งค่าหน้าตา App (เขียว-ขาว) ---
st.set_page_config(page_title="ระบบครูตระกูล v7.5", layout="wide")

# ... (ส่วน CSS และ Header คงเดิมเหมือน v7.4) ...

# --- [ส่วนประมวลผลตารางที่แก้ไขใหม่] ---
if uploaded_files:
    # ... (ส่วนการอ่านไฟล์และรวมชื่อยังคงเดิม) ...
    
    if all_raw_data:
        final_data = merge_similar_names(all_raw_data)
        df_master = pd.DataFrame(final_data).drop_duplicates()
        
        for lv in sorted(df_master['ระดับ'].unique()):
            st.markdown(f'<div class="level-header">📍 ระดับชั้น {lv}</div>', unsafe_allow_html=True)
            df_lv = df_master[df_master['ระดับ'] == lv]
            pivot = df_lv.pivot_table(index=['เลขที่', 'ชื่อ-นามสกุล', 'ชื่อกลุ่ม'], columns='กิจกรรม', values='ระดับ', aggfunc='count').fillna(0).astype(int)
            for act in full_acts: 
                if act not in pivot.columns: pivot[act] = 0
            
            res = pivot[full_acts].copy()
            res['รวม'] = res.sum(axis=1)
            res = res.reset_index()
            
            # จัดการลำดับคนลืมชื่อไว้ท้าย
            res['is_missing'] = res['ชื่อ-นามสกุล'].apply(lambda x: 1 if "⚠️" in str(x) else 0)
            res = res.sort_values(by=['is_missing', 'เลขที่']).drop(columns=['is_missing'])

            # --- ✨ แก้ไขจุดสำคัญ: สร้างคอลัมน์ 'ลำดับที่' ใหม่ ---
            res = res.reset_index(drop=True)
            res.insert(0, 'ลำดับที่', res.index + 1) # ใส่ลำดับ 1, 2, 3... ไว้คอลัมน์แรกสุด

            # --- เลือกคอลัมน์ที่จะแสดง: ลำดับที่ -> ชื่อกลุ่ม -> ชื่อ-นามสกุล ---
            cols_final = ['ลำดับที่', 'ชื่อกลุ่ม', 'ชื่อ-นามสกุล'] + full_acts + ['รวม']
            
            st.dataframe(
                res[cols_final].style.set_properties(**{
                    'background-color': '#ffffff', 
                    'color': '#000000', 
                    'text-align': 'center'
                })
                .set_properties(subset=['ชื่อ-นามสกุล', 'ชื่อกลุ่ม'], **{'text-align': 'left'})
                .apply(lambda x: ['background-color: #fff0f0; color: #d32f2f;' if "⚠️" in str(x['ชื่อ-นามสกุล']) else 'background-color: #ffffff;' for _ in x], axis=1)
                .format({a: lambda x: '✔' if x >= 1 else '-' for a in full_acts}),
                use_container_width=True, hide_index=True
            )
            st.download_button(f"📥 โหลดไฟล์ {lv}", res[cols_final].to_csv(index=False).encode('utf-8-sig'), f"Report_{lv}.csv")
