import streamlit as st
import pandas as pd
import re, os, base64

# --- 1. ตั้งค่าหน้าตาโปรแกรม (โทนเขียว-ขาว) ---
st.set_page_config(page_title="ระบบเช็คงานครูตระกูล", layout="wide")

def get_b64(file):
    if os.path.exists(file):
        try:
            with open(file, "rb") as f:
                return base64.b64encode(f.read()).decode()
        except: return None
    return None

# ตรวจสอบรูปภาพ teacher.jpg ในโฟลเดอร์
img_b64 = get_b64("teacher.jpg")
# ถ้าไม่มีรูปในเครื่อง ให้ใช้รูปไอคอนครูเป็นตัวสำรอง (Placeholder)
placeholder_img = "https://cdn-icons-png.flaticon.com/512/3429/3429433.png"

st.markdown(f"""
<style>
    /* พื้นหลังและ Header */
    .stApp {{ background-color: #f9fbf9; }}
    .main-header {{
        background-color: #1b5e20; /* เขียวเข้ม */
        padding: 15px;
        border-radius: 10px 10px 0 0;
        text-align: center;
        color: white;
    }}
    /* การ์ดโปรไฟล์ครูตระกูล */
    .teacher-card {{
        background-color: #ffffff;
        border: 2px solid #e0e0e0;
        border-radius: 12px;
        padding: 20px;
        margin: 15px 0;
        display: flex;
        align-items: center;
        gap: 25px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }}
    .teacher-img {{
        width: 120px; height: 120px;
        border-radius: 50%;
        border: 4px solid #4caf50;
        object-fit: cover;
    }}
</style>

<div class="main-header">
    <h2 style="margin:0; font-weight: 300; letter-spacing: 1px;">📋 ระบบเช็คงานอัจฉริยะ</h2>
</div>

<div class="teacher-card">
    <img src="{f'data:image/jpeg;base64,{img_b64}' if img_b64 else placeholder_img}" class="teacher-img">
    <div>
        <h1 style="margin:0; color: #1b5e20; font-size: 2rem;">ครูตระกูล บุญชิต</h1>
        <p style="margin:0; color: #666; font-size: 1.1rem;">โรงเรียนตระกาศประชาสามัคคี |
