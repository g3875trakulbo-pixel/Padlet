import streamlit as st
import pandas as pd
import re

# --- 1. การตั้งค่าหน้าเว็บ (Page Config) ---
st.set_page_config(
    page_title="Biology Tracking App - ครูตระกูล",
    page_icon="🧬",
    layout="centered"  # ใช้แบบ centered เพื่อให้ดูดีบนมือถือ
)

# --- 2. ฟังก์ชันช่วยประมวลผลข้อมูล (Helper Functions) ---
def extract_student_id(text):
    """ดึงเลขที่จากข้อความ เช่น 'เลขที่ 7' หรือ 'เลขที่7'"""
    if pd.isna(text): return None
    match = re.search(r'เลขที่\s*(\d+)', str(text))
    return match.group(1) if match else None

@st.cache_data
def load_and_process_data(file):
    """โหลดไฟล์ CSV และเตรียมคอลัมน์สำหรับการค้นหา"""
    try:
        df = pd.read_csv(file)
        # ตรวจสอบว่ามีคอลัมน์ที่จำเป็นไหม
        required_cols = ['เรื่อง', 'เนื้อหา', 'ส่วน']
        for col in required_cols:
            if col not in df.columns:
                st.error(f"ไฟล์ที่อัปโหลดไม่มีคอลัมน์: {col}")
                return None
        
        # สร้างคอลัมน์เลขที่เพื่อช่วยในการค้นหา
        df['student_id_search'] = df['เนื้อหา'].apply(extract_student_id)
        return df
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดในการอ่านไฟล์: {e}")
        return None

# --- 3. ส่วนหัวของแอป (Header) ---
st.markdown("""
    <div style="background-color:#1b5e20; padding:25px; border-radius:15px; text-align:center; margin-bottom:10px; color:white;">
        <h1 style="margin:0;">🧬 Biology Submission Tracking</h1>
        <p style="font-size:1.2rem; margin-top:10px; opacity:0.9;">ระบบตรวจสอบการส่งกิจกรรมออนไลน์</p>
    </div>
""", unsafe_allow_html=True)

# --- 4. ส่วนเจ้าของแอป (Profile) ---
st.markdown("<h3 style='text-align:center;'>ผู้พัฒนาแอป: คุณครูตระกูล บุญชิต</h3>", unsafe_allow_html=True)

col1, col2,
