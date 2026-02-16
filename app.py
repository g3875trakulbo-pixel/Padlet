import streamlit as st
import pandas as pd
import re, os, base64

# --- 1. การตั้งค่าหน้าตาและโทนสี ---
st.set_page_config(page_title="ระบบครูตระกูล", layout="wide")

def get_b64(file):
    if os.path.exists(file):
        try:
            with open(file, "rb") as f: return base64.b64encode(f.read()).decode()
        except: return None
    return None

img_b64 = get_b64("teacher.jpg")
placeholder_img = "https://cdn-icons-png.flaticon.com/512/3429/3429433.png"

# ปรับ CSS ให้ตัวหนังสือเป็นสีดำเข้มและพื้นหลังสีขาว
st.markdown("""
<style>
    .main-header { background-color: #1b5e20; padding: 15px; border-radius: 10px 10px 0 0; text-align: center; color: white; }
    .teacher-card { background-color: #ffffff; border: 2px solid #e0e0e0; border-radius: 12px; padding: 20px; margin: 15px 0; display: flex; align-items: center; gap: 25px; }
    .teacher-img { width: 110px; height: 110px; border-radius: 50%; border: 4px solid #4caf50; object-fit: cover; }
    .level-header { background-color: #4caf50; color: white; padding: 10px 20px; border-radius: 8px; margin-top: 30px; margin-bottom: 10px; font-size: 1.5rem; }
    
    /* บังคับตัวหนังสือในตารางให้เป็นสีดำเข้มทั้งหมด */
    [data-testid="stTable"] td, [data-testid="stDataFrame"] td {
        color: #000000 !important;
        font
