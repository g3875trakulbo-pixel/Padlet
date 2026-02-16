import streamlit as st
import pandas as pd
import re
import os
import base64

# --- 1. การตั้งค่าหน้าเว็บ ---
st.set_page_config(page_title="ระบบสรุปงานครูเจมส์", layout="wide")

# ฟังก์ชันดึงรูปภาพ teacher.jpg มาแสดง
def get_image_base64(path):
    if os.path.exists(path):
        with open(path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return None

img_base64 = get_image_base64("teacher.jpg")

# --- 2. ส่วนเฮดเดอร์พรีเมียม (ดีไซน์เน้นสวยงามและภาพขนาดพอดี) ---
if img_base64:
    header_html = f"""
    <div style="background: linear-gradient(135deg, #1b5e20 0%, #2e7d32 100%); padding: 30px; border-radius: 20px; text-align: center; color: white; border: 3px solid #ffffff; box-shadow: 0px 10px 20px rgba(0,0,0,0.2); margin-bottom: 30px;">
        <img src="data:image/jpeg;base64,{img_base64}" style="width: 100px; height: 100px; border-radius: 50%; border: 3px solid gold; object-fit: cover; margin-bottom: 10px; box-shadow: 0px 4px 10px rgba(0,0,0,0.3);">
        <p style="letter-spacing: 2px; font-size: 0.9rem; margin-bottom: 0; opacity: 0.9;">ASSIGNMENT TRACKING SYSTEM</p>
        <h1 style="font-size: 2.2rem; margin: 5px 0; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);">📋 ระบบเช็คงานอัจฉริยะ ครูตระกูล บุญชิต</h1>
        <p style="font-size: 1.1rem; opacity: 0.9;">โรงเรียนตระกาศประชาสามัคคี | ภาคเรียนที่ 2/2568</p>
        <div style="display: inline-block; background-color: #689f38; color: white; padding: 5px 20px; border-radius: 50px; font-weight: bold; margin-top: 10px; border: 1px solid rgba(255,255,255,0.3);">👨‍🏫 BY TEACHER TARKUL (KRU JAMES)</div>
    </div>
    """
else:
    header_html
